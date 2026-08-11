# Managed settings for Claude Code org telemetry
#
# Deploy via:
#   1) MDM / device management to the managed settings file path, OR
#   2) claude.ai Admin > Claude Code > Managed settings (server-managed)
#
# Per docs (monitoring-usage.md):
# - OTEL_EXPORTER_OTLP_* in managed settings locks the destination
# - Users cannot override the collector endpoint when locked
# - Prompt/response content is REDACTED unless OTEL_LOG_USER_PROMPTS /
#   OTEL_LOG_ASSISTANT_RESPONSES are enabled
#
# Local docker compose testing: point endpoint at localhost:
#   OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317
# and remove Authorization header or use a dummy token the collector ignores.
