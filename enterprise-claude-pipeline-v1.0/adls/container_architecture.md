# ADLS Gen2 Container Architecture & Storage Governance

**Container Name**: `claude-telemetry`  
**Storage Account**: `stclaudetelemetryprod.dfs.core.windows.net` (Azure ADLS Gen2)  
**Access Control**: Azure Managed Identity + RBAC (`Storage Blob Data Contributor` for OTel Collector & Databricks)

---

## 1. Directory & Partition Layout

```
abfss://claude-telemetry@stclaudetelemetryprod.dfs.core.windows.net/
│
├── raw/                                     # System of Record Landing Layer (Immutable)
│   ├── logs/
│   │   └── year=YYYY/month=MM/day=DD/hour=HH/
│   │       ├── collector-pod-01_a1b2c3d4.jsonl.gz
│   │       └── collector-pod-02_e5f6g7h8.jsonl.gz
│   └── quarantine/                          # Bad JSONL records & unparseable payloads
│       └── year=YYYY/month=MM/day=DD/
│           └── bad_records_uuid.jsonl
│
├── delta-lake/                              # Managed Delta Lake Storage (Databricks Unity Catalog)
│   ├── bronze/
│   │   └── claude_code_raw_events/          # Delta tables ingested via Auto Loader
│   ├── silver/
│   │   ├── prompts/                         # Normalized & PII redacted prompts
│   │   ├── responses/                       # Normalized responses
│   │   ├── tool_executions/                 # Tool usage events (bash, view, edit)
│   │   ├── sessions/                        # Session duration & turn metrics
│   │   └── token_costs/                     # Granular token & spend metrics
│   └── gold/
│       ├── daily_user_metrics/              # Daily aggregated developer KPIs
│       ├── tool_adoption_summary/           # Tool distribution metrics
│       ├── department_cost_attribution/     # Cost per department / cost center
│       └── security_leak_alerts/            # Flagged secret leaks & audit logs
│
└── exports/
    └── snowflake_stage/                     # Formatted CSV/Parquet extracts for Snowflake import
        └── year=YYYY/month=MM/day=DD/
```

---

## 2. Lifecycle & Data Retention Policies

| Path | Lifecycle Rule | Action | Retention Period |
|------|----------------|--------|------------------|
| `raw/logs/` | Move to Cool Tier | Automate after 7 days | 7 days Hot → Cool |
| `raw/logs/` | Move to Archive Tier | Automate after 90 days | 90 days Cool → Archive |
| `raw/quarantine/` | Delete Quarantine | Purge bad payloads | 30 days |
| `delta-lake/bronze/` | Delta Vacuum | Retain Delta history | `VACUUM RETAIN 168 HOURS` (7 days) |
| `delta-lake/silver/` | Delta Vacuum | Retain Delta history | `VACUUM RETAIN 720 HOURS` (30 days) |
| `exports/snowflake_stage/` | Auto Purge | Delete stage files post Snowflake COPY | 3 days |

---

## 3. Storage Security & Encryption

1. **Encryption at Rest**: Customer-Managed Key (CMK) via Azure Key Vault (RSA 4096-bit).
2. **Encryption in Transit**: TLS 1.3 enforced for all gRPC, HTTP, and ABFSS endpoints (`secure_transfer_required = true`).
3. **Private Endpoint Networking**: Public IP access blocked. All data flows over Azure Private Link VNet endpoints.
4. **RBAC Control**:
   - `OTel Collector Managed Identity`: `Storage Blob Data Contributor` (Scoped to `raw/logs/`)
   - `Databricks Cluster Managed Identity`: `Storage Blob Data Contributor` (Scoped to `raw/` and `delta-lake/`)
   - `Snowflake Storage Integration App`: `Storage Blob Data Reader` (Scoped to `raw/` and `exports/`)
