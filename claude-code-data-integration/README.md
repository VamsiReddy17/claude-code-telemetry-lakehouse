# Claude Code Data Integration Pipeline

End-to-end skeleton: **Claude Code prompts, replies, tool activity → ADLS Gen2 → Databricks → Snowflake**.

Designed for org-scale (~1000 users) with managed settings, OpenTelemetry, medallion layers, and dual warehouse sinks.

```
Claude Code (1000 clients)
        │  OTLP (gRPC/HTTP)
        ▼
OpenTelemetry Collector
        │  Azure Blob exporter (JSONL)
        ▼
ADLS Gen2  (bronze landing)
        │  Autoloader / COPY
        ▼
Databricks  (bronze → silver → gold)
        │  Snowflake connector / external stage
        ▼
Snowflake  (serving / BI / compliance)
```

## Quick start (local skeleton)

```bash
cd claude-code-data-integration
cp .env.example .env          # fill Azure / Databricks / Snowflake values
docker compose up -d          # OTel collector + local Azurite (ADLS emulator)
python3 scripts/emit_sample_events.py
python3 scripts/validate_pipeline.py
```

Production: point collector at real ADLS, deploy Databricks Asset Bundle, run Snowflake DDL.

## Folder map

| Path | Role |
|------|------|
| `managed-settings/` | Org-locked Claude Code OTel env (MDM / server-managed) |
| `otel-collector/` | Collector config → ADLS Gen2 JSONL |
| `schemas/` | Event contracts (bronze / silver) |
| `adls/` | Container + path conventions |
| `databricks/` | Autoloader jobs, silver/gold transforms, DAB |
| `snowflake/` | DB/schema/stage/pipe/views |
| `scripts/` | Sample emitter, validators |
| `infra/terraform/` | Optional Azure storage + RBAC skeleton |
| `samples/` | Example OTel log payloads |
| `config/` | Shared pipeline config |

## What gets captured

From Claude Code OpenTelemetry (see `../knowledge-base/docs/en/monitoring-usage.md`):

| Event | Content flags required |
|-------|------------------------|
| `claude_code.user_prompt` | `OTEL_LOG_USER_PROMPTS=1` |
| `claude_code.assistant_response` | `OTEL_LOG_ASSISTANT_RESPONSES=1` (or inherits prompts flag) |
| `claude_code.tool_result` / `tool_decision` | `OTEL_LOG_TOOL_DETAILS=1` |
| Tool I/O in traces | `OTEL_LOG_TOOL_CONTENT=1` + enhanced telemetry |
| Full API bodies | `OTEL_LOG_RAW_API_BODIES=1` or `file:<dir>` |

Default Claude Code redacts prompt/response text until these flags are set in **managed** settings.

## Medallion layers

| Layer | Store | Contents |
|-------|-------|----------|
| **Bronze** | ADLS + Databricks Delta | Raw OTLP log records as JSONL / VARIANT |
| **Silver** | Databricks Delta | Normalized tables: prompts, responses, tools, sessions, users |
| **Gold** | Databricks + Snowflake | Daily usage, cost, compliance extracts, PII-masked views |

## Security notes

- Prompt/code content is sensitive. Encrypt ADLS, restrict Unity Catalog + Snowflake roles.
- Prefer managed identity / workload identity; never commit `.env`.
- Truncation default in Claude Code is ~60 KB per attribute; raise `CLAUDE_CODE_OTEL_CONTENT_MAX_LENGTH` only if your backends allow it.
- Inform employees that prompts and code may be logged for compliance.

## Next steps after filling credentials

1. Deploy `managed-settings/settings.json` via MDM or claude.ai server-managed settings.
2. Run collector on AKS / Container Apps / VMs with `AZURE_STORAGE_*`.
3. `databricks bundle deploy && databricks bundle run bronze_ingest`.
4. Apply `snowflake/ddl/*.sql`, enable Snowpipe or scheduled Databricks→Snowflake sync.
5. Point BI at Snowflake gold views.
