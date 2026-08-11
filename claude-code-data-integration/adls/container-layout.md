# ADLS Gen2 layout for Claude Code telemetry

## Storage account

- Account: `stgclaudetelem{env}` (HNS enabled — Gen2)
- Container: `claude-telemetry`
- Redundancy: ZRS or GRS per compliance
- Soft delete + versioning: ON
- Encryption: Microsoft-managed or CMK

## Paths

```
claude-telemetry/
├── bronze/
│   ├── otel/
│   │   ├── logs/year=.../month=.../day=.../hour=.../*.jsonl
│   │   ├── metrics/...
│   │   └── traces/...
│   └── api_bodies/          # optional: OTEL_LOG_RAW_API_BODIES=file:<dir> sync
├── quarantine/
│   └── bad_records/
└── _checkpoints/            # Databricks Autoloader / RocksDB checkpoints (if using volume)
```

## RBAC

| Principal | Role |
|-----------|------|
| OTel collector MI | Storage Blob Data Contributor (container) |
| Databricks access connector | Storage Blob Data Contributor |
| Snowflake storage integration | Storage Blob Data Reader |
| Data engineers | Reader via UC external location |

## Networking

- Prefer private endpoint to `dfs` + `blob` endpoints
- Collector egress only to ADLS private IP / PE
- Deny public blob access
