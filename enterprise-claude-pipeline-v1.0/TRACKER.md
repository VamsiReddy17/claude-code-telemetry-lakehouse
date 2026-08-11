# Enterprise Claude Code Telemetry Pipeline Tracker & Architecture Journal

**Organization Scale**: 2,500 Active Developers  
**Target Ingestion Capacity**: 500,000 – 1,500,000 events / day (~10–50 GB raw compressed / day)  
**Primary Processing Order**: Client Telemetry → OpenTelemetry Collector → ADLS Gen2 → Azure Databricks (Medallion) → Snowflake Data Warehouse  
**Pipeline Version**: `enterprise-claude-pipeline-v1.0`  
**Status**: Active / Production Setup  
**Last Updated**: 2026-08-11

---

## 1. Executive Summary & Objectives

This repository contains the architecture, pipelines, configurations, and analytical serving layer for analyzing work patterns, productivity velocity, tool adoption, cost distribution, and security compliance across 2,500 Claude Code active users in the enterprise.

### Key Objectives
1. **Developer Work & Usage Intelligence**: Understand top workflows, tools used (Bash, View/Edit, Search, Git, custom tools), programming languages, and multi-turn agent conversation depth.
2. **Cost & Token Economics**: Track token consumption (Input, Output, Cache Creation, Cache Read) across departments, teams, and cost centers.
3. **Security & Secrets Governance**: Automatically detect and redact passwords, API keys, JWTs, and proprietary tokens from telemetry before serving to executive BI layers.
4. **Reliability & Scalability**: Multi-layer decoupled architecture ensuring zero data loss during traffic spikes or downstream maintenance.

---

## 2. Architecture & Data Flow

For full architectural diagrams and detailed component specifications, see [ARCHITECTURE_DIAGRAM.md](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/ARCHITECTURE_DIAGRAM.md).

```
┌────────────────────────────────────────────────────────┐
│             2,500 Claude Code Clients                  │
│       (CLI / VS Code / Desktop / Custom Extensions)    │
└──────────────────────────┬─────────────────────────────┘
                           │ OTLP / gRPC (Port 4317)
                           ▼
┌────────────────────────────────────────────────────────┐
│        High-Availability OpenTelemetry Collector       │
│           (Azure Container Apps / AKS Pool)            │
└──────────────────────────┬─────────────────────────────┘
                           │ JSONL Gzip Batches
                           ▼
┌────────────────────────────────────────────────────────┐
│                  ADLS Gen2 Storage                     │
│         abfss://claude-telemetry/raw/logs/             │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
  Autoloader   │                          │ Snowpipe / Stage
  (Continuous) │                          │ (Near-real-time)
               ▼                          ▼
┌─────────────────────────────┐ ┌─────────────────────────┐
│     Azure Databricks        │ │  Snowflake Warehouse    │
│                             │ │                         │
│  [Bronze] Raw Delta Lake    │ │  [BRONZE] Raw Table     │
│       │                     │ │       │                 │
│  [Silver] Cleansed & PII    │ │  [SILVER] Normalized    │
│           Redacted Tables   │ │           Tables        │
│       │                     │ │       │                 │
│  [Gold]   Aggregations &    │ │  [GOLD]   Executive &   │
│           Metrics           │ │           BI Views      │
└──────────────┬──────────────┘ └───────────┬─────────────┘
               │                            │
               └──── Delta Sync / Connector ┘
```

---

## 3. Architectural Decision Records (ADRs)

### ADR-001: ADLS Gen2 as System of Record Landing Layer
- **Status**: Accepted
- **Context**: 2,500 active developers emit continuous telemetry streams. We need an immutable, low-cost system-of-record storage layer that decouples ingestion from compute processing engines.
- **Decision**: Export telemetry from OTel Collectors as Gzip-compressed JSONL files to Azure ADLS Gen2 partitioned by `year/month/day/hour`.
- **Consequences**: Enables both Databricks (Auto Loader) and Snowflake (Snowpipe/External Stage) to read the same underlying files independently without contention.

### ADR-002: Azure Databricks Medallion Processing Engine (Bronze → Silver → Gold)
- **Status**: Accepted
- **Context**: Raw telemetry payloads contain complex JSON schemas with nested tool inputs, attributes, token metrics, and unredacted prompt strings.
- **Decision**: Implement PySpark Delta Lake Medallion pipelines:
  - **Bronze**: Auto Loader (`cloudFiles`) raw ingestion into Delta Lake with schema evolution.
  - **Silver**: Normalized relational schemas (`prompts`, `responses`, `tool_executions`, `sessions`, `token_costs`) with automated PII & secret redaction.
  - **Gold**: Aggregated business metrics (`daily_user_metrics`, `tool_adoption_summary`, `department_cost_attribution`, `security_leak_alerts`).
- **Consequences**: Near-real-time streaming capability, ACID transactions, data versioning (Time Travel), and automated schema enforcement.

### ADR-003: Enterprise Real-Time Secret Redaction Engine
- **Status**: Accepted
- **Context**: Telemetry from developer machines may contain secrets (AWS/Azure keys, JWTs, password strings, connection URLs) in prompt text or bash command arguments.
- **Decision**: Build regex-based token scanning and masking logic into the Silver PySpark transformation layer. Any detected secret is replaced with `[REDACTED_SECRET:<TYPE>]` before persisting to Silver/Gold layers.
- **Consequences**: Eliminates risk of exposing sensitive infrastructure credentials in data warehouse BI dashboards.

### ADR-004: Snowflake as Primary Executive Serving & BI Warehouse
- **Status**: Accepted
- **Context**: CEO and enterprise stakeholders require sub-second dashboard performance, role-based governance, and seamless integration with corporate BI tools (PowerBI, Tableau, ThoughtSpot).
- **Decision**: Materialize Gold analytics and Silver curated views directly into Snowflake `CLAUDE_CODE_ANALYTICS` warehouse using Storage Integrations and Delta sync.
- **Consequences**: Provides high-concurrency access for executives while keeping heavy transformation compute isolated in Databricks.

### ADR-005: Strict Role-Based Access Control (RBAC)
- **Status**: Accepted
- **Context**: Prompt content contains IP and code logic. Executive reports only need aggregated KPIs.
- **Decision**: Enforce two primary roles in Snowflake:
  - `EXECUTIVE_BI_ROLE`: Access to Gold aggregated views only (DAU/WAU, cost per team, top tools). No raw prompt/response text.
  - `SECURITY_AUDIT_ROLE`: Restricted access to security leak audit tables and raw telemetry for compliance investigation.

---

## 4. Pipeline Component & Implementation Status Tracker

| Component | Location | Description | Status |
|-----------|----------|-------------|--------|
| **Architecture Diagram** | [ARCHITECTURE_DIAGRAM.md](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/ARCHITECTURE_DIAGRAM.md) | Comprehensive Mermaid diagram & specs | ✅ Completed |
| **Managed Settings** | [enterprise_settings.json](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/managed-settings/enterprise_settings.json) | MDM telemetry config for 2,500 clients | ✅ Completed |
| **OTel Collector HA** | [collector_config_ha.yaml](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/otel-collector/collector_config_ha.yaml) | Production OTel configuration with ADLS sink | ✅ Completed |
| **ADLS Storage** | [container_architecture.md](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/adls/container_architecture.md) | ADLS Gen2 pathing & retention policy | ✅ Completed |
| **DAB Package** | [databricks.yml](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/databricks/databricks.yml) | Databricks Asset Bundle configuration | ✅ Completed |
| **Bronze Ingestion** | [01_bronze_autoloader.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/databricks/src/01_bronze_autoloader.py) | PySpark Auto Loader streaming ingestion | ✅ Completed |
| **Silver ETL & Redact** | [02_silver_transformation_pii_redact.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/databricks/src/02_silver_transformation_pii_redact.py) | Silver schema normalization & secret masking | ✅ Completed |
| **Gold Aggregations** | [03_gold_aggregations.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/databricks/src/03_gold_aggregations.py) | Gold business metrics calculation | ✅ Completed |
| **Snowflake Sync** | [04_snowflake_delta_sync.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/databricks/src/04_snowflake_delta_sync.py) | Spark-to-Snowflake Delta table sync | ✅ Completed |
| **Snowflake Integration**| [01_storage_integration.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/snowflake/01_storage_integration.sql) | Storage Integration & Snowpipe DDL | ✅ Completed |
| **Snowflake Silver** | [02_tables_and_silver_transform.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/snowflake/02_tables_and_silver_transform.sql) | Snowflake tables, tasks & streams | ✅ Completed |
| **Snowflake Gold/RBAC**| [03_gold_views_and_rbac.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/snowflake/03_gold_views_and_rbac.sql) | Executive views & role security | ✅ Completed |
| **Executive Queries** | [executive_kpi_queries.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/dashboards/executive_kpi_queries.sql) | Ready-to-use CEO / Exec SQL dashboards | ✅ Completed |

---

## 5. Service Level Agreements (SLAs) & Benchmarks

| Metric | Target | Disaster / Breach Threshold |
|--------|--------|----------------------------|
| **Telemetry Ingestion Lag** | < 1 minute (OTel → ADLS) | > 5 minutes |
| **Databricks Silver Freshness** | < 5 minutes (Bronze → Silver) | > 15 minutes |
| **Snowflake BI View Freshness**| < 15 minutes | > 1 hour |
| **PII/Secret Detection Accuracy** | > 99.9% secret catch rate | Any unmasked credential in BI |
| **OTel Collector Availability** | 99.95% uptime | Collector pod failure without failover |

---

## 6. Predictive Future Use Cases & Roadmap

1. **Automated Prompt Quality & Complexity Scoring**: Predict developer prompt effectiveness and suggest prompt engineering optimization tips.
2. **AI-Driven Code Safety & Vulnerability Audit**: Analyze tool execution parameters (e.g. bash execution of `curl`, `pip install`, `eval`) for potential security vulnerabilities before deployment.
3. **Developer Velocity Impact Analysis**: Correlate Claude Code session frequency with git commit volume and pull request lead times across engineering teams.
4. **Predictive Cost Management & Quota Alerts**: Machine learning model forecasting monthly LLM spend per cost center and auto-alerting management when spend exceeds projections.
