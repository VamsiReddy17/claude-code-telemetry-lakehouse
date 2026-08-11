-- External stage over ADLS Gen2 bronze landing
-- Prefer STORAGE INTEGRATION over SAS in production.

-- CREATE STORAGE INTEGRATION IF NOT EXISTS CLAUDE_TELEM_AZURE_INT
--   TYPE = EXTERNAL_STAGE
--   STORAGE_PROVIDER = AZURE
--   ENABLED = TRUE
--   AZURE_TENANT_ID = '<tenant-id>'
--   STORAGE_ALLOWED_LOCATIONS = ('azure://stgclaudetelemdev.blob.core.windows.net/claude-telemetry/bronze/otel/logs/');

-- DESC STORAGE INTEGRATION CLAUDE_TELEM_AZURE_INT;
-- -- Complete Azure consent URL, then:

USE DATABASE CLAUDE_TELEMETRY;
USE SCHEMA BRONZE;

CREATE OR REPLACE FILE FORMAT CLAUDE_OTEL_JSONL
  TYPE = JSON
  STRIP_OUTER_ARRAY = FALSE
  COMPRESSION = AUTO;

CREATE OR REPLACE STAGE CLAUDE_OTEL_BRONZE_STAGE
  -- STORAGE_INTEGRATION = CLAUDE_TELEM_AZURE_INT
  URL = 'azure://stgclaudetelemdev.blob.core.windows.net/claude-telemetry/bronze/otel/logs/'
  -- CREDENTIALS = (AZURE_SAS_TOKEN = '...')  -- only for bootstrap; remove in prod
  FILE_FORMAT = CLAUDE_OTEL_JSONL;

CREATE OR REPLACE TABLE OTEL_RAW (
  RAW VARIANT,
  INGEST_TS TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
  SOURCE_FILE STRING METADATA$FILENAME
);

-- Snowpipe (auto-ingest) — requires Azure Event Grid notification setup
CREATE OR REPLACE PIPE OTEL_RAW_PIPE
  AUTO_INGEST = TRUE
  AS
  COPY INTO OTEL_RAW (RAW, SOURCE_FILE)
  FROM (
    SELECT $1, METADATA$FILENAME
    FROM @CLAUDE_OTEL_BRONZE_STAGE
  )
  FILE_FORMAT = (FORMAT_NAME = CLAUDE_OTEL_JSONL)
  ON_ERROR = 'CONTINUE';

-- SHOW PIPES;
-- Select notification_channel and wire to Event Grid on the storage account.
