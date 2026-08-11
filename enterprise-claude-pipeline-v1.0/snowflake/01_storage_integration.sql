-- ============================================================================
-- 01_storage_integration.sql
-- ----------------------------------------------------------------------------
-- Snowflake Infrastructure DDL for Claude Code Enterprise Telemetry
-- Storage Integration, External Stage, File Formats, and Snowpipe Setup.
-- ============================================================================

USE ROLE ACCOUNTADMIN;

-- 1. Create Database & Schemas
CREATE DATABASE IF NOT EXISTS CLAUDE_CODE_ANALYTICS
  COMMENT = 'Data Warehouse for 2,500 Claude Code Enterprise Developers';

USE DATABASE CLAUDE_CODE_ANALYTICS;

CREATE SCHEMA IF NOT EXISTS BRONZE COMMENT = 'Raw OTLP JSONL telemetry landing from ADLS';
CREATE SCHEMA IF NOT EXISTS SILVER COMMENT = 'Normalized relational tables & PII redacted views';
CREATE SCHEMA IF NOT EXISTS GOLD   COMMENT = 'Executive BI views & aggregated departmental metrics';

-- 2. Create Storage Integration with Azure ADLS Gen2
CREATE STORAGE INTEGRATION IF NOT EXISTS ADLS_CLAUDE_TELEMETRY_INT
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'AZURE'
  ENABLED = TRUE
  AZURE_TENANT_ID = '<YOUR_AZURE_TENANT_ID>'
  STORAGE_ALLOWED_LOCATIONS = (
    'azure://stclaudetelemetryprod.blob.core.windows.net/claude-telemetry/raw/',
    'azure://stclaudetelemetryprod.blob.core.windows.net/claude-telemetry/delta-lake/'
  )
  COMMENT = 'Storage Integration for Claude Code ADLS Gen2 Telemetry';

-- DESCRIBE STORAGE INTEGRATION ADLS_CLAUDE_TELEMETRY_INT;
-- Grant AZURE_CONSENT_URL to Azure AD Admin to authorize Snowflake Service Principal.

-- 3. File Formats
CREATE OR REPLACE FILE FORMAT BRONZE.JSONL_GZIP_FORMAT
  TYPE = 'JSON'
  COMPRESSION = 'GZIP'
  ENABLE_OCTAL = FALSE
  ALLOW_DUPLICATE = TRUE
  STRIP_OUTER_ARRAY = FALSE
  IGNORE_UTF8_ERRORS = TRUE;

-- 4. External Stage Pointing to ADLS Gen2 Raw Landing
CREATE OR REPLACE STAGE BRONZE.ADLS_RAW_STAGE
  STORAGE_INTEGRATION = ADLS_CLAUDE_TELEMETRY_INT
  URL = 'azure://stclaudetelemetryprod.blob.core.windows.net/claude-telemetry/raw/logs/'
  FILE_FORMAT = BRONZE.JSONL_GZIP_FORMAT;

-- 5. Bronze Raw Telemetry Storage Table
CREATE TABLE IF NOT EXISTS BRONZE.RAW_TELEMETRY (
  RAW_PAYLOAD VARIANT,
  INGESTED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  FILE_NAME VARCHAR(512)
);

-- 6. Snowpipe for Near-Real-Time Auto-Ingestion
CREATE OR REPLACE PIPE BRONZE.PIPE_OTEL_RAW_INGEST
  AUTO_INGEST = TRUE
  INTEGRATION = 'AZURE_EVENT_GRID_INT' -- Event Grid Notification Subscription
  AS
  COPY INTO BRONZE.RAW_TELEMETRY (RAW_PAYLOAD, INGESTED_AT, FILE_NAME)
  FROM (
    SELECT 
      $1,
      CURRENT_TIMESTAMP(),
      METADATA$FILENAME
    FROM @BRONZE.ADLS_RAW_STAGE
  );

-- Verify Pipe Status
-- SELECT SYSTEM$PIPE_STATUS('BRONZE.PIPE_OTEL_RAW_INGEST');
