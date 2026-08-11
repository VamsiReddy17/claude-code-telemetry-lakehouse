# Architecture

## Data flow

```mermaid
flowchart LR
  subgraph clients [Developer machines / VDI]
    CC[Claude Code CLI / Desktop / VS Code]
  end

  subgraph edge [Org edge]
    MS[Managed settings]
    OTC[OpenTelemetry Collector]
  end

  subgraph azure [Azure]
    ADLS[(ADLS Gen2<br/>bronze/otel/...]
  end

  subgraph dbx [Databricks]
    BRZ[bronze.claude_code_otel_raw]
    SLV[silver.prompts / responses / tools / sessions]
    GLD[gold.daily_usage / compliance]
  end

  subgraph sf [Snowflake]
    STG[STAGE + PIPE]
    RAW[BRONZE.OTEL_RAW]
    CUR[SILVER / GOLD views]
  end

  MS --> CC
  CC -->|OTLP gRPC :4317| OTC
  OTC -->|JSONL blobs| ADLS
  ADLS -->|Autoloader| BRZ
  BRZ --> SLV --> GLD
  ADLS -->|external stage / Snowpipe| STG --> RAW --> CUR
  GLD -->|Snowflake connector optional| CUR
```

## Design choices

1. **ADLS Gen2 is the system of record for raw events** — both Databricks and Snowflake can read the same bronze landing without coupling.
2. **Databricks owns transforms** — Autoloader + Delta for schema evolution and streaming.
3. **Snowflake owns serving** — BI, compliance exports, cross-domain joins.
4. **Collector is the only OTLP sink** — managed settings lock `OTEL_EXPORTER_OTLP_ENDPOINT` so users cannot redirect telemetry.
5. **Idempotent keys** — `session.id` + `event.sequence` / `prompt.id` / `message.uuid` for dedupe.

## Partitioning (ADLS)

```
abfss://claude-telemetry@<account>.dfs.core.windows.net/
  bronze/otel/logs/year=YYYY/month=MM/day=DD/hour=HH/<collector>-<uuid>.jsonl
  bronze/otel/metrics/...
  quarantine/bad_records/...
```

## Latency targets (skeleton defaults)

| Path | Cadence |
|------|---------|
| OTel export | logs every 5s (Claude Code default interval) |
| Collector → ADLS | batch flush 10–30s |
| Databricks Autoloader | continuous / 1–5 min trigger |
| Snowflake pipe | near-real-time after ADLS PUT, or hourly TASK |

## Failure modes

| Failure | Mitigation |
|---------|------------|
| Collector down | Clients buffer briefly; deploy HA replicas + PDB |
| Bad JSON | Quarantine path + `badRecordsPath` |
| Schema drift | Bronze VARIANT/JSON; silver evolved with `mergeSchema` |
| PII leak to gold | Masking UDFs + separate `gold_compliance` schema with tight RBAC |
