-- ============================================================================
-- executive_kpi_queries.sql
-- ----------------------------------------------------------------------------
-- Executive Leadership Dashboard Queries for CEO & Engineering Executives
-- Designed for 2,500 Claude Code Developers in Enterprise Data Warehouse
-- ============================================================================

USE DATABASE CLAUDE_CODE_ANALYTICS;
USE SCHEMA GOLD;

-- ============================================================================
-- QUERY 1: Executive Overview Scorecard (Last 30 Days)
-- Provides CEO with overall active users, prompt volume, tool velocity & cost.
-- ============================================================================
SELECT
  COUNT(DISTINCT USER_EMAIL)                          AS TOTAL_ACTIVE_DEVELOPERS_WAU,
  SUM(TOTAL_SESSIONS)                                 AS TOTAL_CODING_SESSIONS,
  SUM(TOTAL_TOKENS_CONSUMED)                          AS TOTAL_TOKENS_USED,
  ROUND(SUM(TOTAL_SPEND_USD), 2)                      AS TOTAL_LLM_INVESTMENT_USD,
  ROUND(SUM(TOTAL_SPEND_USD) / COUNT(DISTINCT USER_EMAIL), 2) AS AVG_MONTHLY_COST_PER_DEV_USD
FROM GOLD.V_EXECUTIVE_DAILY_KPIS
WHERE METRIC_DATE >= DATEADD('day', -30, CURRENT_DATE());


-- ============================================================================
-- QUERY 2: Developer Tool Adoption & Usage Frequency Matrix
-- Shows what tools developers are using (Bash commands, File View/Edit, Search, Git)
-- ============================================================================
SELECT
  TOOL_NAME,
  SUM(TOTAL_EXECUTIONS)                               AS TOTAL_EXECUTIONS_30D,
  COUNT(DISTINCT UNIQUE_USERS)                        AS ACTIVE_DEVELOPERS_USING_TOOL,
  ROUND(AVG(ERROR_RATE_PCT), 2)                       AS AVG_FAILURE_RATE_PCT,
  ROUND(AVG(AVG_DURATION_MS), 0)                      AS AVG_EXECUTION_TIME_MS
FROM GOLD.V_TOOL_ADOPTION_MATRIX
WHERE METRIC_DATE >= DATEADD('day', -30, CURRENT_DATE())
GROUP BY TOOL_NAME
ORDER BY TOTAL_EXECUTIONS_30D DESC;


-- ============================================================================
-- QUERY 3: Departmental Cost Attribution & Token Cache Efficiency
-- Breakdown of LLM spend by engineering department and token caching savings.
-- ============================================================================
SELECT
  DEPARTMENT,
  COUNT(DISTINCT ACTIVE_USERS)                        AS DEV_COUNT,
  SUM(TOTAL_INPUT_TOKENS)                             AS INPUT_TOKENS,
  SUM(TOTAL_OUTPUT_TOKENS)                            AS OUTPUT_TOKENS,
  SUM(TOTAL_CACHE_READ_TOKENS)                        AS CACHED_TOKENS,
  ROUND((SUM(TOTAL_CACHE_READ_TOKENS) / NULLIF(SUM(TOTAL_INPUT_TOKENS + TOTAL_CACHE_READ_TOKENS), 0)) * 100, 1) AS CACHE_HIT_RATIO_PCT,
  ROUND(SUM(TOTAL_COST_USD), 2)                       AS TOTAL_DEPARTMENT_COST_USD
FROM GOLD.V_DEPARTMENT_COST_ATTRIBUTION
WHERE METRIC_DATE >= DATEADD('day', -30, CURRENT_DATE())
GROUP BY DEPARTMENT
ORDER BY TOTAL_DEPARTMENT_COST_USD DESC;


-- ============================================================================
-- QUERY 4: Daily Active User (DAU) Trend & Engagement Cadence
-- Tracks daily adoption rate across 2,500 active developers over time.
-- ============================================================================
SELECT
  METRIC_DATE,
  ACTIVE_DEVELOPERS_DAU,
  TOTAL_SESSIONS,
  ROUND(TOTAL_SPEND_USD, 2) AS DAILY_SPEND_USD
FROM GOLD.V_EXECUTIVE_DAILY_KPIS
ORDER BY METRIC_DATE DESC;


-- ============================================================================
-- QUERY 5: Security & Compliance Secret Interception Audit
-- Summarizes secret credentials intercepted and redacted before data storage.
-- ============================================================================
SELECT
  AUDIT_DATE,
  DEPARTMENT,
  COUNT(*) AS TOTAL_CREDENTIALS_REDACTED,
  COUNT(DISTINCT USER_EMAIL) AS IMPACTED_DEVELOPERS
FROM GOLD.V_SECURITY_LEAK_AUDIT
WHERE AUDIT_DATE >= DATEADD('day', -30, CURRENT_DATE())
GROUP BY AUDIT_DATE, DEPARTMENT
ORDER BY AUDIT_DATE DESC;
