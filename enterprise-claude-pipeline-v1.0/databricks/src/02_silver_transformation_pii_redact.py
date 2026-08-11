"""
02_silver_transformation_pii_redact.py
---------------------------------------
Azure Databricks PySpark Silver ETL Pipeline with Real-Time PII & Secret Redaction Engine.

Transforms raw JSONL telemetry from bronze.claude_code_raw_events into normalized
Silver Delta Lake tables:
  1. silver.prompts
  2. silver.responses
  3. silver.tool_executions
  4. silver.sessions
  5. silver.token_costs
"""

import os
import re
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    udf,
    current_timestamp,
    to_timestamp,
    coalesce,
    lit,
    sum as _sum,
    count as _count,
    min as _min,
    max as _max,
    get_json_object,
    when
)
from pyspark.sql.types import StringType

spark = SparkSession.builder \
    .appName("ClaudeCodeTelemetry_SilverTransformRedact") \
    .getOrCreate()

# Storage Configuration
STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "stclaudetelemetryprod")
CONTAINER_NAME = "claude-telemetry"
ADLS_BASE_PATH = f"abfss://{CONTAINER_NAME}@{STORAGE_ACCOUNT}.dfs.core.windows.net"

# Create Silver Database Schema
spark.sql("CREATE DATABASE IF NOT EXISTS silver")

# Secret & PII Redaction Regex Rules
SECRET_PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "[REDACTED_AWS_KEY]"),
    (r"ASIA[0-9A-Z]{16}", "[REDACTED_AWS_TEMP_KEY]"),
    (r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+", "[REDACTED_JWT_TOKEN]"),
    (r"(?:api[_-]?key|secret|password|auth_token)\s*[:=]\s*['\"]([^'\"]+)['\"]", r"\1:[REDACTED_CREDENTIAL]"),
    (r"https?://[^:]+:[^@]+@[^\s]+", "[REDACTED_URL_CREDS]"),
    (r"-----BEGIN (?:RSA |EC |PGP )?PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]")
]

def redact_text(text: str) -> str:
    """Scans input text against sensitive credential regexes and masks matches."""
    if not text:
        return text
    redacted = text
    for pattern, replacement in SECRET_PATTERNS:
        redacted = re.sub(pattern, replacement, redacted, flags=re.IGNORECASE)
    return redacted

redact_udf = udf(redact_text, StringType())

print("Reading raw events from bronze layer...")
bronze_df = spark.read.table("bronze.claude_code_raw_events")

# -------------------------------------------------------------------------
# 1. Silver Prompts Table
# -------------------------------------------------------------------------
print("Processing silver.prompts...")
prompts_df = bronze_df \
    .filter(col("body.name") == "claude_code.user_prompt") \
    .select(
        col("body.attributes.session.id").alias("session_id"),
        col("body.attributes.user.email").alias("user_email"),
        col("body.attributes.org.department").alias("department"),
        to_timestamp(col("body.timestamp")).alias("event_timestamp"),
        col("body.attributes.model.name").alias("model_name"),
        redact_udf(col("body.attributes.prompt.text")).alias("prompt_text"),
        col("body.attributes.prompt.token_count").cast("long").alias("prompt_tokens"),
        current_timestamp().alias("processed_at")
    ) \
    .dropDuplicates(["session_id", "event_timestamp"])

prompts_path = f"{ADLS_BASE_PATH}/delta-lake/silver/prompts"
prompts_df.write.format("delta").mode("overwrite").save(prompts_path)
spark.sql(f"CREATE TABLE IF NOT EXISTS silver.prompts USING DELTA LOCATION '{prompts_path}'")

# -------------------------------------------------------------------------
# 2. Silver Responses Table
# -------------------------------------------------------------------------
print("Processing silver.responses...")
responses_df = bronze_df \
    .filter(col("body.name") == "claude_code.assistant_response") \
    .select(
        col("body.attributes.session.id").alias("session_id"),
        col("body.attributes.user.email").alias("user_email"),
        to_timestamp(col("body.timestamp")).alias("event_timestamp"),
        col("body.attributes.model.name").alias("model_name"),
        redact_udf(col("body.attributes.response.text")).alias("response_text"),
        col("body.attributes.response.token_count").cast("long").alias("completion_tokens"),
        col("body.attributes.response.latency_ms").cast("long").alias("latency_ms"),
        current_timestamp().alias("processed_at")
    ) \
    .dropDuplicates(["session_id", "event_timestamp"])

responses_path = f"{ADLS_BASE_PATH}/delta-lake/silver/responses"
responses_df.write.format("delta").mode("overwrite").save(responses_path)
spark.sql(f"CREATE TABLE IF NOT EXISTS silver.responses USING DELTA LOCATION '{responses_path}'")

# -------------------------------------------------------------------------
# 3. Silver Tool Executions Table
# -------------------------------------------------------------------------
print("Processing silver.tool_executions...")
tools_df = bronze_df \
    .filter(col("body.name").isin("claude_code.tool_decision", "claude_code.tool_result")) \
    .select(
        col("body.attributes.session.id").alias("session_id"),
        col("body.attributes.user.email").alias("user_email"),
        to_timestamp(col("body.timestamp")).alias("event_timestamp"),
        col("body.attributes.tool.name").alias("tool_name"),
        redact_udf(col("body.attributes.tool.input")).alias("tool_input"),
        redact_udf(col("body.attributes.tool.output")).alias("tool_output"),
        col("body.attributes.tool.duration_ms").cast("long").alias("duration_ms"),
        col("body.attributes.tool.exit_code").cast("integer").alias("exit_code"),
        current_timestamp().alias("processed_at")
    ) \
    .dropDuplicates(["session_id", "event_timestamp", "tool_name"])

tools_path = f"{ADLS_BASE_PATH}/delta-lake/silver/tool_executions"
tools_df.write.format("delta").mode("overwrite").save(tools_path)
spark.sql(f"CREATE TABLE IF NOT EXISTS silver.tool_executions USING DELTA LOCATION '{tools_path}'")

# -------------------------------------------------------------------------
# 4. Silver Sessions Aggregations
# -------------------------------------------------------------------------
print("Processing silver.sessions...")
sessions_df = bronze_df \
    .groupBy(col("body.attributes.session.id").alias("session_id")) \
    .agg(
        _min(col("body.attributes.user.email")).alias("user_email"),
        _min(col("body.attributes.org.department")).alias("department"),
        _min(to_timestamp(col("body.timestamp"))).alias("session_start"),
        _max(to_timestamp(col("body.timestamp"))).alias("session_end"),
        _count(when(col("body.name") == "claude_code.user_prompt", 1)).alias("total_prompts"),
        _count(when(col("body.name").isin("claude_code.tool_decision", "claude_code.tool_result"), 1)).alias("total_tool_calls")
    ) \
    .withColumn("session_duration_sec", (col("session_end").cast("long") - col("session_start").cast("long"))) \
    .withColumn("processed_at", current_timestamp())

sessions_path = f"{ADLS_BASE_PATH}/delta-lake/silver/sessions"
sessions_df.write.format("delta").mode("overwrite").save(sessions_path)
spark.sql(f"CREATE TABLE IF NOT EXISTS silver.sessions USING DELTA LOCATION '{sessions_path}'")

# -------------------------------------------------------------------------
# 5. Silver Token Costs
# -------------------------------------------------------------------------
print("Processing silver.token_costs...")
token_costs_df = bronze_df \
    .filter(col("body.name") == "claude_code.assistant_response") \
    .select(
        col("body.attributes.session.id").alias("session_id"),
        col("body.attributes.user.email").alias("user_email"),
        col("body.attributes.org.department").alias("department"),
        to_timestamp(col("body.timestamp")).alias("event_timestamp"),
        col("body.attributes.model.name").alias("model_name"),
        coalesce(col("body.attributes.tokens.input").cast("long"), lit(0)).alias("input_tokens"),
        coalesce(col("body.attributes.tokens.output").cast("long"), lit(0)).alias("output_tokens"),
        coalesce(col("body.attributes.tokens.cache_creation").cast("long"), lit(0)).alias("cache_creation_tokens"),
        coalesce(col("body.attributes.tokens.cache_read").cast("long"), lit(0)).alias("cache_read_tokens")
    ) \
    .withColumn(
        "estimated_cost_usd",
        # Claude 3.7 / 3.5 Sonnet pricing model rules: $3/M input, $15/M output, $3.75/M cache write, $0.30/M cache read
        (col("input_tokens") * 0.000003) +
        (col("output_tokens") * 0.000015) +
        (col("cache_creation_tokens") * 0.00000375) +
        (col("cache_read_tokens") * 0.00000030)
    ) \
    .withColumn("processed_at", current_timestamp())

token_costs_path = f"{ADLS_BASE_PATH}/delta-lake/silver/token_costs"
token_costs_df.write.format("delta").mode("overwrite").save(token_costs_path)
spark.sql(f"CREATE TABLE IF NOT EXISTS silver.token_costs USING DELTA LOCATION '{token_costs_path}'")

print("Silver Transformation & Secret Redaction completed successfully.")
