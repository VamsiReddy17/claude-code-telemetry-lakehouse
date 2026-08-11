"""Validate local skeleton: samples exist, collector config parses, paths present."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ok(msg: str) -> None:
    print(f"  OK  {msg}")


def fail(msg: str) -> None:
    print(f" FAIL {msg}")


def main() -> int:
    print("Claude Code data-integration skeleton checks\n")
    errors = 0

    required = [
        "managed-settings/settings.json",
        "otel-collector/config.yaml",
        "otel-collector/Dockerfile",
        "docker-compose.yml",
        ".env.example",
        "schemas/bronze_event.schema.json",
        "databricks/databricks.yml",
        "databricks/src/bronze/autoloader_ingest.py",
        "databricks/src/silver/normalize_events.py",
        "databricks/src/gold/daily_usage.py",
        "databricks/src/gold/sync_to_snowflake.py",
        "snowflake/ddl/01_database.sql",
        "snowflake/ddl/02_stage_and_pipe.sql",
        "snowflake/ddl/03_tables_views.sql",
        "ARCHITECTURE.md",
        "README.md",
    ]
    for rel in required:
        path = ROOT / rel
        if path.exists():
            ok(rel)
        else:
            fail(f"missing {rel}")
            errors += 1

    settings = json.loads((ROOT / "managed-settings/settings.json").read_text())
    env = settings.get("env", {})
    for key in [
        "CLAUDE_CODE_ENABLE_TELEMETRY",
        "OTEL_LOG_USER_PROMPTS",
        "OTEL_LOG_ASSISTANT_RESPONSES",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
    ]:
        if key in env:
            ok(f"managed-settings has {key}={env[key]}")
        else:
            fail(f"managed-settings missing {key}")
            errors += 1

    schema = json.loads((ROOT / "schemas/bronze_event.schema.json").read_text())
    ok(f"bronze schema title={schema.get('title')}")

    samples = ROOT / "samples" / "otel_events.jsonl"
    if samples.exists():
        lines = [json.loads(l) for l in samples.read_text().splitlines() if l.strip()]
        ok(f"samples/otel_events.jsonl ({len(lines)} events)")
    else:
        print("  WARN samples/otel_events.jsonl not found — run emit_sample_events.py")

    fallback = ROOT / "otel-collector" / "local-file-fallback"
    fallback.mkdir(parents=True, exist_ok=True)
    ok(f"fallback dir ready: {fallback}")

    print("\n" + ("PASS" if errors == 0 else f"FAILED ({errors} errors)"))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
