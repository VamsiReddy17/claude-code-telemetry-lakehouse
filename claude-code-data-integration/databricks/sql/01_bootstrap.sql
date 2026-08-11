-- Databricks SQL bootstrap (Unity Catalog)
-- Run in SQL warehouse after external location is registered.

CREATE CATALOG IF NOT EXISTS claude_telemetry;
CREATE SCHEMA IF NOT EXISTS claude_telemetry.bronze;
CREATE SCHEMA IF NOT EXISTS claude_telemetry.silver;
CREATE SCHEMA IF NOT EXISTS claude_telemetry.gold;

-- Example external location (adjust storage credential name)
-- CREATE EXTERNAL LOCATION IF NOT EXISTS claude_telem_bronze
-- URL 'abfss://claude-telemetry@stgclaudetelemdev.dfs.core.windows.net/bronze'
-- WITH (STORAGE CREDENTIAL `claude-telem-cred`);

CREATE TABLE IF NOT EXISTS claude_telemetry.bronze.claude_code_otel_raw (
  ingest_ts STRING,
  source_file STRING
) USING DELTA;

-- Silver / gold are created by Spark jobs with overwriteSchema.
