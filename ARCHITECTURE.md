# Architecture

![Claude Code Telemetry Lakehouse](./architecture-diagram.png)

End-to-end design for this repository: capture Claude Code prompts, replies, and tool activity at org scale, land them on **ADLS Gen2**, transform in **Databricks**, and serve from **Snowflake**.

---

## 1. System context

```mermaid
flowchart TB
  subgraph org [Organization ~1000 users]
    U[Developers]
    CC[Claude Code<br/>CLI · Desktop · VS Code · JetBrains]
    U --> CC
  end

  subgraph control [Control plane]
    MS[Managed settings / MDM<br/>OTel flags + locked collector URL]
    ADM[claude.ai Admin / Compliance]
  end

  subgraph data [Data plane]
    OTC[OpenTelemetry Collector HA]
    ADLS[(ADLS Gen2 Bronze)]
    DBX[Databricks Medallion]
    SF[Snowflake Serving]
  end

  MS -.->|locks env| CC
  CC -->|OTLP gRPC/HTTP| OTC
  OTC -->|JSONL blobs| ADLS
  ADLS --> DBX
  ADLS --> SF
  DBX -->|optional gold sync| SF
  ADM -.->|policies / Compliance API| org
```

---

## 2. Data flow (runtime)

```mermaid
flowchart LR
  subgraph clients [Clients]
    CC[Claude Code]
  end

  subgraph edge [Org edge]
    MS[Managed settings]
    OTC[OTel Collector]
  end

  subgraph azure [Azure]
    ADLS[(ADLS Gen2<br/>bronze/otel/logs)]
  end

  subgraph dbx [Databricks]
    BRZ[bronze.claude_code_otel_raw]
    SLV[silver.prompts<br/>responses · tools · sessions]
    GLD[gold.daily_user_usage<br/>compliance_transcript_lines]
  end

  subgraph sf [Snowflake]
    PIPE[STAGE + Snowpipe]
    RAW[BRONZE.OTEL_RAW]
    CUR[SILVER / GOLD]
  end

  MS --> CC
  CC -->|OTLP :4317| OTC
  OTC -->|JSONL| ADLS
  ADLS -->|Autoloader| BRZ --> SLV --> GLD
  ADLS --> PIPE --> RAW --> CUR
  GLD -->|Spark connector| CUR
```

---

## 3. Medallion layers

```mermaid
flowchart TB
  subgraph bronze [Bronze — raw]
    B1[OTLP JSONL on ADLS]
    B2[Delta: claude_code_otel_raw]
    B3[Snowflake VARIANT: OTEL_RAW]
    B1 --> B2
    B1 --> B3
  end

  subgraph silver [Silver — normalized]
    S1[prompts]
    S2[responses]
    S3[tool_events]
    S4[sessions]
  end

  subgraph gold [Gold — products]
    G1[daily_user_usage]
    G2[compliance_transcript_lines]
    G3[BI / audit views]
  end

  B2 --> S1 & S2 & S3 & S4
  S1 & S2 & S3 & S4 --> G1 & G2 --> G3
```

| Layer | Store | Contents |
|-------|-------|----------|
| **Bronze** | ADLS + Databricks Delta + Snowflake VARIANT | Raw OTel log records |
| **Silver** | Databricks Delta (+ optional Snowflake) | Typed prompts, responses, tools, sessions |
| **Gold** | Databricks + Snowflake | Daily usage, compliance transcript lines, BI views |

---

## 4. What is captured

```mermaid
flowchart LR
  P[user_prompt] --> R[assistant_response]
  P --> T[tool_result / tool_decision]
  P --> A[api_request / api_error]
  R --> G[gold transcript pair]
  T --> G
```

| Event | Managed setting |
|-------|-----------------|
| Prompt text | `OTEL_LOG_USER_PROMPTS=1` |
| Reply text | `OTEL_LOG_ASSISTANT_RESPONSES=1` |
| Tool names / inputs | `OTEL_LOG_TOOL_DETAILS=1` |
| Tool I/O content | `OTEL_LOG_TOOL_CONTENT=1` |
| Full API bodies | `OTEL_LOG_RAW_API_BODIES` (optional) |

---

## 5. Repo layout

```mermaid
flowchart TB
  ROOT[claude-code-knowledge-base / repo root]
  ROOT --> KB[knowledge-base/<br/>offline Claude Code docs]
  ROOT --> DI[claude-code-data-integration/<br/>pipeline code]
  DI --> MS[managed-settings]
  DI --> OC[otel-collector]
  DI --> AD[adls]
  DI --> DB[databricks]
  DI --> SF[snowflake]
  DI --> SC[schemas · scripts · infra]
```

| Path | Role |
|------|------|
| [`architecture-diagram.png`](./architecture-diagram.png) | Visual architecture poster |
| [`knowledge-base/`](./knowledge-base/) | Official docs mirror |
| [`claude-code-data-integration/`](./claude-code-data-integration/) | Pipeline skeleton |

---

## 6. Sequence (one prompt)

```mermaid
sequenceDiagram
  actor Dev as Developer
  participant CC as Claude Code
  participant OTC as OTel Collector
  participant ADLS as ADLS Gen2
  participant DBX as Databricks
  participant SF as Snowflake

  Dev->>CC: prompt
  CC->>CC: model + tools
  CC-->>Dev: reply / code edits
  CC->>OTC: OTLP user_prompt + assistant_response + tool_*
  OTC->>ADLS: append JSONL (partitioned by hour)
  ADLS->>DBX: Autoloader → bronze → silver → gold
  ADLS->>SF: Snowpipe → BRONZE → SILVER/GOLD
  DBX->>SF: optional gold table sync
```

---

## 7. Design principles

1. **ADLS Gen2 is the raw system of record** — Databricks and Snowflake both consume bronze independently.
2. **Collector is the only OTLP sink** — managed settings lock the endpoint.
3. **Medallion separation** — raw forever in bronze; PII controls on gold/compliance.
4. **Idempotent keys** — `session.id` + `event.sequence` / `prompt.id` / `message.uuid`.
5. **Fail closed on destination** — users cannot redirect telemetry when settings are managed.

Detailed pipeline notes: [`claude-code-data-integration/ARCHITECTURE.md`](./claude-code-data-integration/ARCHITECTURE.md).
