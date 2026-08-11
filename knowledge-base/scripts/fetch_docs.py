#!/usr/bin/env python3
"""Fetch all Claude Code docs from llms.txt into a local knowledge base."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
INDEX_SRC = ROOT / "llms.txt"
MANIFEST = ROOT / "manifest.json"
FAILED = ROOT / "failed.json"

BASE = "https://code.claude.com/docs"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/plain,text/markdown,text/html,*/*",
}


def fetch(url: str, retries: int = 4) -> str:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def parse_index(text: str) -> list[dict]:
    entries: list[dict] = []
    pattern = re.compile(r"^- \[([^\]]+)\]\((https://code\.claude\.com/docs/[^)]+)\):\s*(.*)$", re.M)
    for m in pattern.finditer(text):
        title, url, summary = m.group(1), m.group(2), m.group(3).strip()
        # Prefer .md source URLs
        if not url.endswith(".md"):
            url = url.rstrip("/") + ".md"
        rel = url.replace("https://code.claude.com/docs/", "")
        entries.append({"title": title, "url": url, "summary": summary, "rel": rel})
    return entries


def category_for(rel: str) -> str:
    parts = Path(rel).parts
    if len(parts) >= 2 and parts[0] == "en":
        if len(parts) == 2:
            return "core"
        return parts[1]  # agent-sdk, whats-new, etc.
    return "other"


def save_page(entry: dict, content: str) -> Path:
    # rel like en/overview.md or en/agent-sdk/overview.md
    out = DOCS_DIR / entry["rel"]
    out.parent.mkdir(parents=True, exist_ok=True)
    header = (
        f"---\n"
        f'title: "{entry["title"].replace(chr(34), chr(39))}"\n'
        f'source: "{entry["url"]}"\n'
        f'html: "{entry["url"].replace(".md", "")}"\n'
        f'summary: "{entry["summary"].replace(chr(34), chr(39))}"\n'
        f"fetched: true\n"
        f"---\n\n"
    )
    out.write_text(header + content, encoding="utf-8")
    return out


def download_one(entry: dict) -> dict:
    content = fetch(entry["url"])
    path = save_page(entry, content)
    return {
        **entry,
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "category": category_for(entry["rel"]),
        "ok": True,
    }


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching llms.txt index...")
    index_text = fetch(f"{BASE}/llms.txt")
    INDEX_SRC.write_text(index_text, encoding="utf-8")

    # Also try llms-full.txt if available
    try:
        full = fetch(f"{BASE}/llms-full.txt")
        (ROOT / "llms-full.txt").write_text(full, encoding="utf-8")
        print(f"Saved llms-full.txt ({len(full):,} chars)")
    except Exception as exc:  # noqa: BLE001
        print(f"llms-full.txt not available: {exc}")

    entries = parse_index(index_text)

    # Alias / redirected pages linked from docs but not always in llms.txt
    extras = [
        {
            "title": "Claude Code on Azure AI Foundry",
            "url": "https://code.claude.com/docs/en/azure-ai-foundry.md",
            "summary": "Azure AI Foundry configuration (alias/legacy path).",
            "rel": "en/azure-ai-foundry.md",
        },
        {
            "title": "Slash commands",
            "url": "https://code.claude.com/docs/en/slash-commands.md",
            "summary": "Alias of the skills page (custom commands / skills).",
            "rel": "en/slash-commands.md",
        },
    ]
    seen = {e["rel"] for e in entries}
    for extra in extras:
        if extra["rel"] not in seen:
            entries.append(extra)

    print(f"Found {len(entries)} documentation pages")

    results: list[dict] = []
    failures: list[dict] = []

    # Concurrent but polite
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(download_one, e): e for e in entries}
        done = 0
        for fut in as_completed(futures):
            entry = futures[fut]
            done += 1
            try:
                result = fut.result()
                results.append(result)
                print(f"[{done}/{len(entries)}] OK  {entry['rel']} ({result['bytes']:,} bytes)")
            except Exception as exc:  # noqa: BLE001
                failures.append({**entry, "error": str(exc), "ok": False})
                print(f"[{done}/{len(entries)}] FAIL {entry['rel']}: {exc}")

    # Retry failures once serially
    if failures:
        print(f"\nRetrying {len(failures)} failures...")
        still_fail: list[dict] = []
        for entry in failures:
            try:
                result = download_one(entry)
                results.append(result)
                print(f"RETRY OK  {entry['rel']}")
            except Exception as exc:  # noqa: BLE001
                still_fail.append({**entry, "error": str(exc), "ok": False})
                print(f"RETRY FAIL {entry['rel']}: {exc}")
        failures = still_fail

    results.sort(key=lambda r: r["rel"])
    MANIFEST.write_text(json.dumps(results, indent=2), encoding="utf-8")
    FAILED.write_text(json.dumps(failures, indent=2), encoding="utf-8")

    print(f"\nDone. {len(results)} saved, {len(failures)} failed.")
    print(f"Manifest: {MANIFEST}")
    if failures:
        print(f"Failures: {FAILED}")


if __name__ == "__main__":
    main()
