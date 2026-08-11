-- Optional: transform bronze VARIANT → silver inside Snowflake
-- Use when you want Snowflake-native parsing instead of Databricks silver sync.

USE DATABASE CLAUDE_TELEMETRY;

CREATE OR REPLACE TASK BRONZE.TASK_PARSE_PROMPTS
  WAREHOUSE = CLAUDE_TELEM_WH
  SCHEDULE = '15 MINUTE'
AS
MERGE INTO SILVER.PROMPTS t
USING (
  SELECT
    MD5(COALESCE(RAW:attributes:"session.id"::STRING, '') || '|' ||
        COALESCE(RAW:attributes:"prompt.id"::STRING, '') || '|' ||
        COALESCE(RAW:attributes:"event.sequence"::STRING, '') || '|prompt') AS PROMPT_SK,
    RAW:attributes:"session.id"::STRING AS SESSION_ID,
    RAW:attributes:"prompt.id"::STRING AS PROMPT_ID,
    RAW:attributes:"event.sequence"::NUMBER AS EVENT_SEQUENCE,
    TRY_TO_TIMESTAMP_NTZ(RAW:attributes:"event.timestamp"::STRING) AS EVENT_TIMESTAMP,
    RAW:attributes:"user.account_uuid"::STRING AS USER_ACCOUNT_UUID,
    COALESCE(RAW:attributes:user_prompt::STRING, RAW:attributes:prompt::STRING) AS PROMPT_TEXT,
    LENGTH(COALESCE(RAW:attributes:user_prompt::STRING, RAW:attributes:prompt::STRING)) AS PROMPT_LENGTH,
    COALESCE(RAW:attributes:"org.id"::STRING, 'unknown') AS ORG_ID
  FROM BRONZE.OTEL_RAW
  WHERE LOWER(COALESCE(RAW:attributes:"event.name"::STRING, '')) LIKE '%user_prompt%'
) s
ON t.PROMPT_SK = s.PROMPT_SK
WHEN NOT MATCHED THEN INSERT *;

-- ALTER TASK BRONZE.TASK_PARSE_PROMPTS RESUME;
