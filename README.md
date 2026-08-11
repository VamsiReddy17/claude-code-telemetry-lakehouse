# Claude Code Telemetry Lakehouse

[![Claude Code](https://img.shields.io/badge/Claude%20Code-Anthropic-191919?style=for-the-badge&logo=anthropic&logoColor=white)](https://code.claude.com/docs/en/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-OTLP-000000?style=for-the-badge&logo=opentelemetry&logoColor=white)](https://opentelemetry.io/)
[![Azure ADLS Gen2](https://img.shields.io/badge/Azure-ADLS%20Gen2-0078D4?style=for-the-badge&logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/products/storage/data-lake-storage/)
[![Databricks](https://img.shields.io/badge/Databricks-FF3621?style=for-the-badge&logo=databricks&logoColor=white)](https://www.databricks.com/)
[![Snowflake](https://img.shields.io/badge/Snowflake-29B5E8?style=for-the-badge&logo=snowflake&logoColor=white)](https://www.snowflake.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Terraform](https://img.shields.io/badge/Terraform-844FBA?style=for-the-badge&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![SQL](https://img.shields.io/badge/SQL-4479A1?style=for-the-badge&logo=postgresql&logoColor=white)](https://en.wikipedia.org/wiki/SQL)
[![YAML](https://img.shields.io/badge/YAML-CB171E?style=for-the-badge&logo=yaml&logoColor=white)](https://yaml.org/)
[![Delta Lake](https://img.shields.io/badge/Delta%20Lake-00ADD8?style=for-the-badge&logo=delta&logoColor=white)](https://delta.io/)

Capture Claude Code prompts, replies, and tool activity at org scale — **OpenTelemetry → ADLS Gen2 → Databricks (medallion) → Snowflake**, plus an offline Claude Code docs knowledge base.

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

## Stack

| Layer | Tools |
|-------|--------|
| Capture | Claude Code, OpenTelemetry (OTLP), managed settings |
| Landing | Azure Data Lake Storage Gen2, Docker Collector |
| Transform | Databricks, Apache Spark, Delta Lake, Python |
| Serve | Snowflake (Snowpipe / views), SQL |
| Infra | Terraform, YAML (Asset Bundles) |

## Topics

`claude-code` · `opentelemetry` · `adls-gen2` · `databricks` · `snowflake` · `lakehouse` · `medallion-architecture` · `observability` · `enterprise` · `data-engineering`
