"""
01_bronze_autoloader.py
-----------------------
Azure Databricks PySpark Auto Loader Streaming Ingestion Pipeline.
Reads raw JSONL Gzip OpenTelemetry log events from ADLS Gen2 landing bucket
and streams them continuously into Delta Lake Bronze layer.

Designed for 2,500 Claude Code active users (~1.5M daily events).
"""

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    current_timestamp,
    input_file_name,
    col,
    year,
    month,
    dayofmonth,
    expr
)

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("ClaudeCodeTelemetry_BronzeAutoLoader") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
    .getOrCreate()

# Storage Configuration
STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT", "stclaudetelemetryprod")
CONTAINER_NAME = "claude-telemetry"
ADLS_BASE_PATH = f"abfss://{CONTAINER_NAME}@{STORAGE_ACCOUNT}.dfs.core.windows.net"

RAW_LANDING_PATH = f"{ADLS_BASE_PATH}/raw/logs/*/*/*/*/*.jsonl.gz"
BRONZE_DELTA_TABLE_PATH = f"{ADLS_BASE_PATH}/delta-lake/bronze/claude_code_raw_events"
CHECKPOINT_PATH = f"{ADLS_BASE_PATH}/delta-lake/checkpoints/bronze_autoloader"
QUARANTINE_PATH = f"{ADLS_BASE_PATH}/raw/quarantine"

# Create Bronze Database & Table Schema if not exists
spark.sql("CREATE DATABASE IF NOT EXISTS bronze")

print(f"Starting Auto Loader from: {RAW_LANDING_PATH}")

# Read Stream via Spark Auto Loader (cloudFiles)
raw_stream_df = spark.readStream \
    .format("cloudFiles") \
    .option("cloudFiles.format", "json") \
    .option("cloudFiles.schemaLocation", f"{CHECKPOINT_PATH}_schema") \
    .option("cloudFiles.schemaEvolutionMode", "addNewColumns") \
    .option("cloudFiles.badRecordsPath", QUARANTINE_PATH) \
    .option("cloudFiles.maxFilesPerTrigger", "1000") \
    .load(RAW_LANDING_PATH)

# Add Audit & Partitioning Metadata
bronze_df = raw_stream_df \
    .withColumn("ingested_at", current_timestamp()) \
    .withColumn("source_file", input_file_name()) \
    .withColumn("ingest_year", year(col("ingested_at"))) \
    .withColumn("ingest_month", month(col("ingested_at"))) \
    .withColumn("ingest_day", dayofmonth(col("ingested_at")))

# Write Stream to Delta Lake Bronze Layer
query = bronze_df.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", CHECKPOINT_PATH) \
    .option("mergeSchema", "true") \
    .partitionBy("ingest_year", "ingest_month", "ingest_day") \
    .trigger(availableNow=True) \
    .start(BRONZE_DELTA_TABLE_PATH)

query.awaitTermination()

# Register Table in Databricks Catalog
spark.sql(f"""
CREATE TABLE IF NOT EXISTS bronze.claude_code_raw_events
USING DELTA
LOCATION '{BRONZE_DELTA_TABLE_PATH}'
""")

print("Bronze Auto Loader Ingestion completed successfully.")
