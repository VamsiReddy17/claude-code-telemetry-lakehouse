"""
04_snowflake_delta_sync.py
--------------------------
Azure Databricks to Snowflake Data Warehouse Synchronizer.

Syncs Gold & Silver Delta tables directly into Snowflake `CLAUDE_CODE_ANALYTICS` database
using Snowflake Spark Connector.
"""

import os
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("ClaudeCodeTelemetry_SnowflakeSync") \
    .getOrCreate()

# Snowflake Connection Options from Environment / KeyVault Secrets
SNOWFLAKE_URL = os.getenv("SNOWFLAKE_URL", "enterprise.snowflakecomputing.com")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER", "DATABRICKS_SYNC_SVC")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD", "")
SNOWFLAKE_DB = "CLAUDE_CODE_ANALYTICS"
SNOWFLAKE_WAREHOUSE = "DATABRICKS_SYNC_WH"

sf_options = {
    "sfUrl": SNOWFLAKE_URL,
    "sfUser": SNOWFLAKE_USER,
    "sfPassword": SNOWFLAKE_PASSWORD,
    "sfDatabase": SNOWFLAKE_DB,
    "sfWarehouse": SNOWFLAKE_WAREHOUSE,
    "sfRole": "DATA_ENGINEERING_ROLE"
}

TABLES_TO_SYNC = [
    ("gold.daily_user_metrics", "GOLD", "DAILY_USER_METRICS"),
    ("gold.tool_adoption_summary", "GOLD", "TOOL_ADOPTION_SUMMARY"),
    ("gold.department_cost_attribution", "GOLD", "DEPARTMENT_COST_ATTRIBUTION"),
    ("gold.security_leak_alerts", "GOLD", "SECURITY_LEAK_ALERTS"),
    ("silver.sessions", "SILVER", "SESSIONS"),
    ("silver.token_costs", "SILVER", "TOKEN_COSTS")
]

print("Starting Snowflake Delta Sync...")

for source_delta, sf_schema, sf_table in TABLES_TO_SYNC:
    print(f"Syncing {source_delta} → Snowflake {sf_schema}.{sf_table}...")
    
    df = spark.read.table(source_delta)
    
    sf_table_options = sf_options.copy()
    sf_table_options["sfSchema"] = sf_schema
    sf_table_options["dbtable"] = sf_table
    
    df.write \
        .format("snowflake") \
        .options(**sf_table_options) \
        .mode("overwrite") \
        .save()

print("Snowflake Delta Sync completed successfully.")
