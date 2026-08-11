"""Silver: explode / normalize Claude Code OTel raw logs into typed tables."""

from __future__ import annotations

import argparse
import hashlib

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    return p.parse_args()


def sk(*parts: str) -> str:
    raw = "|".join("" if p is None else str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def attr(col_name: str, key: str):
    """Pull attribute from common OTLP JSON shapes (body / attributes map)."""
    return F.coalesce(
        F.get_json_object(F.col(col_name), f"$.attributes.{key}"),
        F.get_json_object(F.col(col_name), f"$.{key}"),
        F.col(key) if False else F.lit(None),
    )


def build_base(raw: DataFrame) -> DataFrame:
    # Skeleton assumes collector wrote OTLP JSON; adapt selectors to your exporter encoding.
    return (
        raw.withColumn("event_name", F.coalesce(F.col("event_name"), F.col("attributes.event.name"), F.lit("other")))
        .withColumn("session_id", F.coalesce(F.col("session_id"), F.col("attributes.session.id"), F.lit("unknown")))
        .withColumn("prompt_id", F.coalesce(F.col("prompt_id"), F.col("attributes.prompt.id")))
        .withColumn("event_sequence", F.coalesce(F.col("event_sequence"), F.col("attributes.event.sequence")))
        .withColumn("event_timestamp", F.coalesce(F.col("event_timestamp"), F.col("attributes.event.timestamp"), F.col("ingest_ts")))
        .withColumn("user_account_uuid", F.coalesce(F.col("user_account_uuid"), F.col("attributes.user.account_uuid")))
        .withColumn("org_id", F.coalesce(F.col("org_id"), F.col("attributes.org.id"), F.lit("unknown")))
        .withColumn("prompt_text", F.coalesce(F.col("prompt_text"), F.col("attributes.user_prompt"), F.col("attributes.prompt")))
        .withColumn("response_text", F.coalesce(F.col("response_text"), F.col("attributes.response"), F.col("attributes.assistant_response")))
        .withColumn("tool_name", F.coalesce(F.col("tool_name"), F.col("attributes.tool_name")))
        .withColumn("model", F.coalesce(F.col("model"), F.col("attributes.model")))
        .withColumn("input_tokens", F.coalesce(F.col("input_tokens"), F.col("attributes.input_tokens")))
        .withColumn("output_tokens", F.coalesce(F.col("output_tokens"), F.col("attributes.output_tokens")))
        .withColumn("cost_usd", F.coalesce(F.col("cost_usd"), F.col("attributes.cost_usd")))
    )


def main() -> None:
    args = parse_args()
    spark = SparkSession.builder.getOrCreate()
    spark.udf.register("make_sk", sk, StringType())

    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {args.catalog}.silver")

    raw = spark.table(f"{args.catalog}.bronze.claude_code_otel_raw")
    base = build_base(raw).filter(F.col("session_id").isNotNull())

    prompts = (
        base.filter(F.lower(F.col("event_name")).contains("user_prompt"))
        .select(
            F.expr("make_sk(session_id, prompt_id, cast(event_sequence as string), 'prompt')").alias("prompt_sk"),
            "session_id",
            "prompt_id",
            "event_sequence",
            F.to_timestamp("event_timestamp").alias("event_timestamp"),
            "user_account_uuid",
            "prompt_text",
            F.length("prompt_text").alias("prompt_length"),
            "org_id",
        )
        .dropDuplicates(["prompt_sk"])
    )

    responses = (
        base.filter(F.lower(F.col("event_name")).contains("assistant_response"))
        .select(
            F.expr("make_sk(session_id, prompt_id, cast(event_sequence as string), 'response')").alias("response_sk"),
            "session_id",
            "prompt_id",
            F.col("attributes.message.uuid").alias("message_uuid") if False else F.lit(None).alias("message_uuid"),
            "event_sequence",
            F.to_timestamp("event_timestamp").alias("event_timestamp"),
            "response_text",
            F.length("response_text").alias("response_length"),
            "model",
            "org_id",
        )
        .dropDuplicates(["response_sk"])
    )

    tools = (
        base.filter(
            F.lower(F.col("event_name")).contains("tool")
        )
        .select(
            F.expr("make_sk(session_id, cast(event_sequence as string), tool_name, 'tool')").alias("tool_event_sk"),
            "session_id",
            "prompt_id",
            "event_name",
            "tool_name",
            F.col("attributes.tool_input").alias("tool_input") if False else F.lit(None).alias("tool_input"),
            F.lit(None).cast("string").alias("tool_output"),
            F.lit(None).cast("string").alias("decision"),
            F.to_timestamp("event_timestamp").alias("event_timestamp"),
            "org_id",
        )
        .dropDuplicates(["tool_event_sk"])
    )

    sessions = (
        base.groupBy("session_id", "org_id", "user_account_uuid")
        .agg(
            F.min(F.to_timestamp("event_timestamp")).alias("started_at"),
            F.max(F.to_timestamp("event_timestamp")).alias("last_event_at"),
            F.sum(F.when(F.lower(F.col("event_name")).contains("user_prompt"), 1).otherwise(0)).alias("prompt_count"),
            F.sum(F.when(F.lower(F.col("event_name")).contains("assistant_response"), 1).otherwise(0)).alias("response_count"),
            F.sum(F.when(F.lower(F.col("event_name")).contains("tool"), 1).otherwise(0)).alias("tool_call_count"),
            F.sum(F.coalesce(F.col("input_tokens").cast("long"), F.lit(0))).alias("total_input_tokens"),
            F.sum(F.coalesce(F.col("output_tokens").cast("long"), F.lit(0))).alias("total_output_tokens"),
            F.sum(F.coalesce(F.col("cost_usd").cast("double"), F.lit(0.0))).alias("total_cost_usd"),
        )
    )

    (
        prompts.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{args.catalog}.silver.prompts")
    )
    (
        responses.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{args.catalog}.silver.responses")
    )
    (
        tools.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{args.catalog}.silver.tool_events")
    )
    (
        sessions.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{args.catalog}.silver.sessions")
    )

    print("Silver normalize complete")


if __name__ == "__main__":
    main()
