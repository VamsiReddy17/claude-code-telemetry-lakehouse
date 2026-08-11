"""
03_gold_aggregations.py
-----------------------
Azure Databricks PySpark Gold Business Aggregations & Analytics Engine.

Materializes curated business intelligence Delta tables from Silver layer:
  1. gold.daily_user_metrics
  2. gold.tool_adoption_summary
  3. gold.department_cost_attribution
  4. gold.security_leak_alerts
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    to_date,
    current_timestamp,
    countDistinct,
    count,
    sum as _sum,
    avg as _avg,
    when
)

spark = SparkSession.builder \
    .appName("ClaudeCodeTelemetry_GoldAggregations") \
    .getOrCreate()

STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "stclaudetelemetryprod")
CONTAINER_NAME = "claude-telemetry"
ADLS_BASE_PATH = f"abfss://{CONTAINER_NAME}@{STORAGE_ACCOUNT}.dfs.core.windows.net"

# Create Gold Database Schema
spark.sql("CREATE DATABASE IF NOT EXISTS gold")

# -------------------------------------------------------------------------
# 1. Gold Daily User Metrics
# -------------------------------------------------------------------------
print("Processing gold.daily_user_metrics...")
sessions_df = spark.read.table("silver.sessions")

daily_user_metrics_df = sessions_df \
    .withColumn("usage_date", to_date("session_start")) \
    .groupBy("usage_date", "user_email", "department") \
    .agg(
        countDistinct("session_id").alias("total_sessions"),
        _sum("total_prompts").alias("total_prompts"),
        _sum("total_tool_calls").alias("total_tool_calls"),
        _sum("session_duration_sec").alias("total_duration_sec"),
        _avg("session_duration_sec").alias("avg_session_duration_sec")
    ) \
    .withColumn("processed_at", current_timestamp())

daily_user_path = f"{ADLS_BASE_PATH}/delta-lake/gold/daily_user_metrics"
daily_user_metrics_df.write.format("delta").mode("overwrite").save(daily_user_path)
spark.sql(f"CREATE TABLE IF NOT EXISTS gold.daily_user_metrics USING DELTA LOCATION '{daily_user_path}'")

# -------------------------------------------------------------------------
# 2. Gold Tool Adoption Summary
# -------------------------------------------------------------------------
print("Processing gold.tool_adoption_summary...")
tools_df = spark.read.table("silver.tool_executions")

tool_adoption_df = tools_df \
    .withColumn("execution_date", to_date("event_timestamp")) \
    .groupBy("execution_date", "tool_name") \
    .agg(
        count("*").alias("total_executions"),
        countDistinct("user_email").alias("unique_users"),
        _sum(when(col("exit_code") != 0, 1).otherwise(0)).alias("failed_executions"),
        _avg("duration_ms").alias("avg_duration_ms")
    ) \
    .withColumn("error_rate_pct", (col("failed_executions") / col("total_executions")) * 100) \
    .withColumn("processed_at", current_timestamp())

tool_path = f"{ADLS_BASE_PATH}/delta-lake/gold/tool_adoption_summary"
tool_adoption_df.write.format("delta").mode("overwrite").save(tool_path)
spark.sql(f"CREATE TABLE IF NOT EXISTS gold.tool_adoption_summary USING DELTA LOCATION '{tool_path}'")

# -------------------------------------------------------------------------
# 3. Gold Department Cost Attribution
# -------------------------------------------------------------------------
print("Processing gold.department_cost_attribution...")
costs_df = spark.read.table("silver.token_costs")

cost_attribution_df = costs_df \
    .withColumn("cost_date", to_date("event_timestamp")) \
    .groupBy("cost_date", "department", "model_name") \
    .agg(
        countDistinct("user_email").alias("active_users"),
        _sum("input_tokens").alias("total_input_tokens"),
        _sum("output_tokens").alias("total_output_tokens"),
        _sum("cache_creation_tokens").alias("total_cache_creation_tokens"),
        _sum("cache_read_tokens").alias("total_cache_read_tokens"),
        _sum("estimated_cost_usd").alias("total_cost_usd")
    ) \
    .withColumn("processed_at", current_timestamp())

cost_path = f"{ADLS_BASE_PATH}/delta-lake/gold/department_cost_attribution"
cost_attribution_df.write.format("delta").mode("overwrite").save(cost_path)
spark.sql(f"CREATE TABLE IF NOT EXISTS gold.department_cost_attribution USING DELTA LOCATION '{cost_path}'")

# -------------------------------------------------------------------------
# 4. Gold Security Leak Alerts Audit
# -------------------------------------------------------------------------
print("Processing gold.security_leak_alerts...")
prompts_df = spark.read.table("silver.prompts")

security_alerts_df = prompts_df \
    .filter(col("prompt_text").contains("[REDACTED_")) \
    .select(
        to_date("event_timestamp").alias("alert_date"),
        col("event_timestamp"),
        col("user_email"),
        col("department"),
        col("session_id"),
        col("prompt_text").alias("flagged_prompt_snippet"),
        current_timestamp().alias("processed_at")
    )

alerts_path = f"{ADLS_BASE_PATH}/delta-lake/gold/security_leak_alerts"
security_alerts_df.write.format("delta").mode("overwrite").save(alerts_path)
spark.sql(f"CREATE TABLE IF NOT EXISTS gold.security_leak_alerts USING DELTA LOCATION '{alerts_path}'")

print("Gold Aggregations completed successfully.")
