"""Gold: daily usage aggregates for BI / Snowflake sync."""

from __future__ import annotations

import argparse

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", required=True)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    spark = SparkSession.builder.getOrCreate()
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {args.catalog}.gold")

    prompts = spark.table(f"{args.catalog}.silver.prompts")
    responses = spark.table(f"{args.catalog}.silver.responses")
    tools = spark.table(f"{args.catalog}.silver.tool_events")
    sessions = spark.table(f"{args.catalog}.silver.sessions")

    p = prompts.groupBy(F.to_date("event_timestamp").alias("usage_date"), "org_id", "user_account_uuid").agg(
        F.count("*").alias("prompts")
    )
    r = responses.groupBy(F.to_date("event_timestamp").alias("usage_date"), "org_id").agg(
        F.count("*").alias("responses")
    )
    # responses may lack user — join via session
    sess_user = sessions.select("session_id", "user_account_uuid", "org_id")
    r_user = (
        responses.join(sess_user, ["session_id", "org_id"], "left")
        .groupBy(F.to_date("event_timestamp").alias("usage_date"), "org_id", "user_account_uuid")
        .agg(F.count("*").alias("responses"))
    )
    t = (
        tools.join(sess_user, ["session_id", "org_id"], "left")
        .groupBy(F.to_date("event_timestamp").alias("usage_date"), "org_id", "user_account_uuid")
        .agg(F.count("*").alias("tool_events"))
    )
    s = sessions.groupBy(F.to_date("started_at").alias("usage_date"), "org_id", "user_account_uuid").agg(
        F.countDistinct("session_id").alias("sessions"),
        F.sum("total_input_tokens").alias("input_tokens"),
        F.sum("total_output_tokens").alias("output_tokens"),
        F.sum("total_cost_usd").alias("cost_usd"),
    )

    daily = (
        s.join(p, ["usage_date", "org_id", "user_account_uuid"], "full")
        .join(r_user, ["usage_date", "org_id", "user_account_uuid"], "full")
        .join(t, ["usage_date", "org_id", "user_account_uuid"], "full")
        .na.fill(0)
    )

    # Compliance transcript lines (prompt + nearest response)
    transcripts = (
        prompts.alias("p")
        .join(
            responses.alias("r"),
            on=[
                F.col("p.session_id") == F.col("r.session_id"),
                F.col("p.prompt_id").eqNullSafe(F.col("r.prompt_id")),
            ],
            how="left",
        )
        .select(
            F.col("p.org_id").alias("org_id"),
            F.col("p.session_id").alias("session_id"),
            F.col("p.user_account_uuid").alias("user_account_uuid"),
            F.col("p.event_timestamp").alias("prompt_ts"),
            F.col("p.prompt_text").alias("prompt_text"),
            F.col("r.event_timestamp").alias("response_ts"),
            F.col("r.response_text").alias("response_text"),
            F.col("r.model").alias("model"),
        )
    )

    (
        daily.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{args.catalog}.gold.daily_user_usage")
    )
    (
        transcripts.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(f"{args.catalog}.gold.compliance_transcript_lines")
    )

    print("Gold aggregates complete")


if __name__ == "__main__":
    main()
