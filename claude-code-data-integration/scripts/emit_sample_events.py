"""Emit sample Claude Code–shaped OTLP logs to the local collector.

Usage:
  docker compose up -d
  pip install -r requirements.txt
  python3 scripts/emit_sample_events.py
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LogRecord
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor, SimpleLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.util.instrumentation import InstrumentationScope
from opentelemetry._logs.severity import SeverityNumber


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples" / "otel_events.jsonl"
FALLBACK = ROOT / "otel-collector" / "local-file-fallback"


def build_events(session_id: str, prompt_id: str) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()
    return [
        {
            "event.name": "user_prompt",
            "event.timestamp": now,
            "event.sequence": 1,
            "session.id": session_id,
            "prompt.id": prompt_id,
            "user.account_uuid": "user-001",
            "user_prompt": "Refactor the auth module and add tests",
            "prompt_length": 42,
            "org.id": "acme-corp",
        },
        {
            "event.name": "assistant_response",
            "event.timestamp": now,
            "event.sequence": 2,
            "session.id": session_id,
            "prompt.id": prompt_id,
            "user.account_uuid": "user-001",
            "response": "I'll refactor auth and add unit tests for login/logout.",
            "response_length": 58,
            "model": "claude-opus-4-6",
            "input_tokens": 1200,
            "output_tokens": 800,
            "cost_usd": 0.042,
            "org.id": "acme-corp",
        },
        {
            "event.name": "tool_result",
            "event.timestamp": now,
            "event.sequence": 3,
            "session.id": session_id,
            "prompt.id": prompt_id,
            "tool_name": "Edit",
            "tool_input": json.dumps({"file_path": "src/auth.py"}),
            "org.id": "acme-corp",
        },
    ]


def main() -> None:
    FALLBACK.mkdir(parents=True, exist_ok=True)
    SAMPLES.parent.mkdir(parents=True, exist_ok=True)

    session_id = str(uuid.uuid4())
    prompt_id = str(uuid.uuid4())
    events = build_events(session_id, prompt_id)

    with SAMPLES.open("w", encoding="utf-8") as fh:
        for e in events:
            fh.write(json.dumps(e) + "\n")

    resource = Resource.create(
        {
            "service.name": "claude-code",
            "service.version": "2.1.223",
            "organization.id": "acme-corp",
        }
    )
    provider = LoggerProvider(resource=resource)
    exporter = OTLPLogExporter(endpoint="localhost:4317", insecure=True)
    provider.add_log_record_processor(SimpleLogRecordProcessor(exporter))
    logger = provider.get_logger("claude-code-sample", "1.0.0")
    scope = InstrumentationScope("claude-code-sample", "1.0.0")

    for attrs in events:
        record = LogRecord(
            timestamp=time.time_ns(),
            observed_timestamp=time.time_ns(),
            severity_number=SeverityNumber.INFO,
            severity_text="INFO",
            body=attrs["event.name"],
            resource=resource,
            attributes=attrs,
        )
        # sdk logger.emit expects LogRecord in recent versions
        try:
            logger.emit(record)
        except TypeError:
            # Fallback for API variants
            provider.get_logger("claude-code-sample").emit(record)  # type: ignore[arg-type]
        print(f"emitted {attrs['event.name']}")
        time.sleep(0.05)

    provider.force_flush(timeout_millis=10000)
    print(f"\nSession {session_id}")
    print(f"Sample JSONL → {SAMPLES}")
    print(f"Collector fallback dir → {FALLBACK}")
    print("Next: python3 scripts/validate_pipeline.py")


if __name__ == "__main__":
    main()
