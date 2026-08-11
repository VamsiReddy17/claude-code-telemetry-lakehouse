# Claude Code Org Workspace

Offline Claude Code docs + enterprise telemetry lakehouse pipeline.

## Architecture

![Architecture](./architecture-diagram.png)

Full diagrams (Mermaid + detail): [`ARCHITECTURE.md`](./ARCHITECTURE.md)

```
Claude Code (×1000) → OTel Collector → ADLS Gen2 (Bronze)
        → Databricks (Bronze → Silver → Gold)
        → Snowflake (serving / compliance / BI)
```

## Repository layout

| Folder | Purpose |
|--------|---------|
| [`knowledge-base/`](knowledge-base/) | Offline mirror of official Claude Code docs |
| [`claude-code-data-integration/`](claude-code-data-integration/) | Pipeline: managed settings, collector, ADLS, Databricks, Snowflake |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System architecture |
| [`architecture-diagram.png`](architecture-diagram.png) | Architecture poster |

## Topics

`claude-code` · `opentelemetry` · `adls-gen2` · `databricks` · `snowflake` · `lakehouse` · `medallion-architecture` · `observability` · `enterprise` · `data-engineering`

## Remote

```bash
git remote add origin https://github.com/VamsiReddy17/claude-code-telemetry-lakehouse.git
git push -u origin main
```
