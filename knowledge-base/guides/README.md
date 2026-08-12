# Curated guides (supplements official docs)

Official Claude Code documentation lives under [`docs/en/`](../docs/en/). This folder holds **guides that are not in the Code docs mirror** (or synthesize multiple sources).

| Guide | Why it is here |
|-------|----------------|
| [`enterprise-inference-hooks/`](enterprise-inference-hooks/) | Claude Enterprise **Inference Hooks** (pre-inference DLP webhooks) — not covered in `docs/en/` |
| [`governance-defense-in-depth.md`](governance-defense-in-depth.md) | 3-layer matrix: SDK permissions × Inference Hooks × OTel |

## Already covered by official docs (do not duplicate)

| Topic | Use instead |
|-------|-------------|
| OpenTelemetry metrics/logs/traces | [`docs/en/monitoring-usage.md`](../docs/en/monitoring-usage.md) |
| Agent SDK observability | [`docs/en/agent-sdk/observability.md`](../docs/en/agent-sdk/observability.md) |
| Permissions & modes | [`docs/en/permissions.md`](../docs/en/permissions.md), [`permission-modes.md`](../docs/en/permission-modes.md) |
| Agent SDK permissions / `canUseTool` | [`docs/en/agent-sdk/permissions.md`](../docs/en/agent-sdk/permissions.md) |
| Claude Code hooks (local) | [`docs/en/hooks.md`](../docs/en/hooks.md), [`hooks-guide.md`](../docs/en/hooks-guide.md) |
