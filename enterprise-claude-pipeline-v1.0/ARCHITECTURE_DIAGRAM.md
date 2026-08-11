# Enterprise Claude Code Telemetry Architecture (v1.0)

**Target Scale**: 2,500 Active Developers  
**Ingestion Capacity**: 500,000 – 1,500,000 events / day (~10–50 GB raw compressed / day)  
**System Version**: `v1.0`

---

## 1. High-Resolution Architecture Diagram

![Enterprise Claude Code Telemetry Architecture Diagram (2,500 Users)](/Users/vamsireddy/.gemini/antigravity-ide/brain/608ee790-1e72-4122-a4b3-eb6975aad040/enterprise_claude_telemetry_architecture_1786470689364.png)

---

## 2. Interactive Flowchart (Mermaid)

```mermaid
flowchart TD
    subgraph Clients["1. Client Tier (2,500 Active Developers)"]
        CC1["Claude Code CLI"]
        CC2["Claude Code VS Code Extension"]
        CC3["Claude Code Desktop App"]
        MS["MDM Managed Settings (enterprise_settings.json)"]
        MS -->|Enforces OTLP & Logging Flags| CC1
        MS -->|Enforces OTLP & Logging Flags| CC2
        MS -->|Enforces OTLP & Logging Flags| CC3
    end

    subgraph Edge["2. Ingestion & Edge Tier"]
        OTC["High-Availability OTel Collector Pool (AKS / ACA)"]
        CC1 -->|"OTLP gRPC (Port 4317) / HTTP (Port 4318)"| OTC
        CC2 -->|"OTLP gRPC (Port 4317)"| OTC
        CC3 -->|"OTLP gRPC (Port 4317)"| OTC
    end

    subgraph Storage["3. Azure Storage Tier (ADLS Gen2)"]
        ADLS_RAW["ADLS Gen2: raw/logs/year=YYYY/month=MM/day=DD/hour=HH/"]
        ADLS_QUAR["ADLS Gen2: raw/quarantine/"]
        OTC -->|"JSONL Gzip Batches"| ADLS_RAW
        OTC -.->"Bad JSON Records"| ADLS_QUAR
    end

    subgraph Compute["4. Azure Databricks Compute Tier (Medallion ETL)"]
        BRZ["Bronze Delta: bronze.claude_code_raw_events"]
        SLV["Silver Delta: prompts, responses, tool_executions, sessions, token_costs"]
        GLD["Gold Delta: daily_user_metrics, tool_adoption_summary, department_cost_attribution"]
        
        ADLS_RAW -->|"PySpark Auto Loader (cloudFiles)"| BRZ
        BRZ -->|"PySpark ETL + Secret Scanning Redactor"| SLV
        SLV -->|"PySpark Aggregations"| GLD
    end

    subgraph Warehouse["5. Snowflake Data Warehouse Tier"]
        SF_STAGE["External Stage (ADLS Integration)"]
        SF_BRZ["BRONZE.RAW_TELEMETRY"]
        SF_SLV["SILVER Relational Tables"]
        SF_GLD["GOLD Executive Views"]

        ADLS_RAW -->|"Snowpipe Auto-Ingest"| SF_STAGE
        SF_STAGE --> SF_BRZ
        SF_BRZ -->|"Streams & Tasks (5-min batch)"| SF_SLV
        SF_SLV --> SF_GLD
        
        GLD -->|"Databricks Spark Snowflake Connector (Sync)"| SF_GLD
    end

    subgraph Serving["6. Enterprise Serving & BI Tier"]
        CEO_DASH["Executive / CEO Dashboard (PowerBI / Tableau)"]
        CISO_AUDIT["CISO / Security Compliance Audit"]
        
        SF_GLD -->|"EXECUTIVE_BI_ROLE (Aggregated Metrics)"| CEO_DASH
        SF_SLV -->|"SECURITY_AUDIT_ROLE (Flagged Credential Leaks)"| CISO_AUDIT
    end
```

---

## 3. Layer-by-Layer Architectural Breakdown

### Layer 1: Client Edge & Managed Settings (`v1.0`)
* **Deployment**: Managed settings pushed to 2,500 developer machines via Enterprise MDM.
* **File Location**: [enterprise_settings.json](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/managed-settings/enterprise_settings.json)
* **Function**: Locks OTLP endpoint to `http://claude-telemetry-collector.enterprise.internal:4317` and forces `OTEL_LOG_USER_PROMPTS=1`, `OTEL_LOG_ASSISTANT_RESPONSES=1`, `OTEL_LOG_TOOL_DETAILS=1`, `OTEL_LOG_TOOL_CONTENT=1`.

### Layer 2: High-Availability Ingestion Collector (`v1.0`)
* **Deployment**: Multi-node Azure Container Apps (ACA) or Azure Kubernetes Service (AKS) pool behind an internal Load Balancer.
* **File Location**: [collector_config_ha.yaml](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/otel-collector/collector_config_ha.yaml)
* **Function**: Ingests OTLP logs/metrics over gRPC port 4317, batches payloads (5s flush / 1000 items), and writes compressed Gzip JSONL files into ADLS Gen2.

### Layer 3: System-of-Record Landing (ADLS Gen2 Storage) (`v1.0`)
* **Deployment**: Azure ADLS Gen2 storage account (`stclaudetelemetryprod`).
* **File Location**: [container_architecture.md](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/adls/container_architecture.md)
* **Function**: Immutable system of record partitioned as `abfss://claude-telemetry/raw/logs/year=YYYY/month=MM/day=DD/hour=HH/`.

### Layer 4: Azure Databricks Medallion Engine (`v1.0`)
* **Deployment**: Azure Databricks Workflows managed by Databricks Asset Bundles ([databricks.yml](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/databricks/databricks.yml)).
* **ETL Scripts**:
  1. [01_bronze_autoloader.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/databricks/src/01_bronze_autoloader.py): Continuous streaming Auto Loader into Delta Lake `bronze.claude_code_raw_events`.
  2. [02_silver_transformation_pii_redact.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/databricks/src/02_silver_transformation_pii_redact.py): PySpark transformation scanning and redacting secrets/credentials (AWS keys, Azure keys, JWTs, passwords) into Silver Delta tables.
  3. [03_gold_aggregations.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/databricks/src/03_gold_aggregations.py): Materializes Gold metrics (`daily_user_metrics`, `tool_adoption_summary`, `department_cost_attribution`, `security_leak_alerts`).
  4. [04_snowflake_delta_sync.py](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/databricks/src/04_snowflake_delta_sync.py): Pushes Gold & Silver tables directly into Snowflake.

### Layer 5: Snowflake Serving Warehouse & Security RBAC (`v1.0`)
* **Deployment**: Snowflake `CLAUDE_CODE_ANALYTICS` database.
* **SQL Scripts**:
  1. [01_storage_integration.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/snowflake/01_storage_integration.sql): Storage Integration & Snowpipe setup.
  2. [02_tables_and_silver_transform.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/snowflake/02_tables_and_silver_transform.sql): Silver tables, streams, and automated tasks.
  3. [03_gold_views_and_rbac.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/snowflake/03_gold_views_and_rbac.sql): Gold views & role-based access control.

### Layer 6: Executive BI Dashboards (`v1.0`)
* **Deployment**: PowerBI / Tableau dashboards connected to Snowflake `CLAUDE_CODE_ANALYTICS.GOLD`.
* **Queries**: [executive_kpi_queries.sql](file:///Users/vamsireddy/Desktop/Agents%20Dev/claude-code-knowledge-base/enterprise-claude-pipeline-v1.0/dashboards/executive_kpi_queries.sql)
