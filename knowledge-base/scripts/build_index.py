#!/usr/bin/env python3
"""Generate INDEX.md and README.md for the Claude Code knowledge base."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"

# Ordered category taxonomy for navigation
TAXONOMY: list[tuple[str, str, list[str]]] = [
    (
        "Getting started",
        "Core concepts, first runs, and everyday usage",
        [
            "overview",
            "quickstart",
            "how-claude-code-works",
            "features-overview",
            "claude-directory",
            "context-window",
            "prompt-caching",
            "memory",
            "permission-modes",
            "sessions",
            "common-workflows",
            "prompt-library",
            "best-practices",
            "changelog",
            "whats-new/index",
            "large-codebases",
            "headless",
            "deep-links",
            "goal",
            "scheduled-tasks",
            "ultrareview",
            "routines",
        ],
    ),
    (
        "Surfaces & platforms",
        "Where Claude Code runs: CLI, Desktop, IDE, web, mobile",
        [
            "platforms",
            "desktop-quickstart",
            "desktop",
            "desktop-linux",
            "desktop-wsl",
            "desktop-scheduled-tasks",
            "desktop-ios-simulator",
            "vs-code",
            "jetbrains",
            "web-quickstart",
            "claude-code-on-the-web",
            "remote-control",
            "mobile",
        ],
    ),
    (
        "Agents & parallel work",
        "Subagents, teams, worktrees, and multi-session orchestration",
        [
            "agents",
            "sub-agents",
            "agent-view",
            "agent-teams",
            "cross-session-messaging",
            "workflows",
            "worktrees",
        ],
    ),
    (
        "Extensibility",
        "Skills, plugins, MCP, hooks, channels, artifacts",
        [
            "skills",
            "discover-plugins",
            "plugins",
            "plugin-marketplaces",
            "plugin-dependencies",
            "plugin-hints",
            "plugin-relevance",
            "mcp-quickstart",
            "mcp",
            "hooks-guide",
            "channels",
            "artifacts",
            "slash-commands",
        ],
    ),
    (
        "Integrations",
        "GitHub, GitLab, Slack, Chrome, computer use, security plugins",
        [
            "github-actions",
            "github-actions-cloud-providers",
            "github-enterprise-server",
            "gitlab-ci-cd",
            "code-review",
            "slack",
            "claude-tag",
            "chrome",
            "computer-use",
            "security-guidance",
            "claude-security",
        ],
    ),
    (
        "Configuration & permissions",
        "Settings, auth, models, terminal UX, and policy controls",
        [
            "setup",
            "authentication",
            "settings",
            "permissions",
            "env-vars",
            "model-config",
            "fast-mode",
            "advisor",
            "output-styles",
            "terminal-config",
            "fullscreen",
            "accessibility",
            "voice-dictation",
            "statusline",
            "keybindings",
            "admin-setup",
            "server-managed-settings",
            "managed-mcp",
            "auto-mode-config",
        ],
    ),
    (
        "Environments & isolation",
        "Sandboxes, cloud environments, self-hosted runners, containers",
        [
            "sandbox-environments",
            "sandboxing",
            "devcontainer",
            "cloud-environments",
            "self-hosted-environments",
            "self-hosted-environments-quickstart",
            "self-hosted-environments-deploy",
            "self-hosted-environments-configuration",
            "self-hosted-environments-testing",
            "self-hosted-environments-reference",
            "self-hosted-environments-identity",
        ],
    ),
    (
        "Enterprise & cloud providers",
        "Bedrock, Vertex/Agent Platform, Foundry, gateways, network",
        [
            "third-party-integrations",
            "feature-availability",
            "amazon-bedrock",
            "claude-platform-on-aws",
            "google-vertex-ai",
            "microsoft-foundry",
            "azure-ai-foundry",
            "network-config",
            "corporate-launcher",
            "gateways",
            "claude-apps-gateway",
            "claude-apps-gateway-config",
            "claude-apps-gateway-spend-limits",
            "claude-apps-gateway-deploy",
            "claude-apps-gateway-on-aws",
            "claude-apps-gateway-on-gcp",
            "llm-gateway",
            "llm-gateway-connect",
            "llm-gateway-rollout",
            "llm-gateway-protocol",
        ],
    ),
    (
        "Operations, security & cost",
        "Monitoring, costs, security, troubleshooting, legal",
        [
            "monitoring-usage",
            "costs",
            "analytics",
            "security",
            "data-usage",
            "zero-data-retention",
            "troubleshoot-install",
            "troubleshooting",
            "debug-your-config",
            "errors",
            "legal-and-compliance",
            "communications-kit",
            "champion-kit",
        ],
    ),
    (
        "Reference",
        "CLI, commands, tools, hooks, plugins, channels, glossary",
        [
            "cli-reference",
            "commands",
            "tools-reference",
            "interactive-mode",
            "checkpointing",
            "hooks",
            "plugins-reference",
            "channels-reference",
            "glossary",
        ],
    ),
    (
        "Agent SDK",
        "Build production agents with Claude Code as a library",
        [
            "agent-sdk/overview",
            "agent-sdk/quickstart",
            "agent-sdk/examples",
            "agent-sdk/troubleshooting",
            "agent-sdk/agent-loop",
            "agent-sdk/claude-code-features",
            "agent-sdk/sessions",
            "agent-sdk/session-storage",
            "agent-sdk/streaming-vs-single-mode",
            "agent-sdk/user-input",
            "agent-sdk/streaming-output",
            "agent-sdk/structured-outputs",
            "agent-sdk/custom-tools",
            "agent-sdk/mcp",
            "agent-sdk/tool-search",
            "agent-sdk/subagents",
            "agent-sdk/modifying-system-prompts",
            "agent-sdk/slash-commands",
            "agent-sdk/skills",
            "agent-sdk/plugins",
            "agent-sdk/permissions",
            "agent-sdk/hooks",
            "agent-sdk/file-checkpointing",
            "agent-sdk/cost-tracking",
            "agent-sdk/observability",
            "agent-sdk/todo-tracking",
            "agent-sdk/hosting",
            "agent-sdk/secure-deployment",
            "agent-sdk/typescript",
            "agent-sdk/typescript-v2-preview",
            "agent-sdk/python",
            "agent-sdk/migration-guide",
        ],
    ),
    (
        "What's new",
        "Weekly digests of notable Claude Code features",
        [
            "whats-new/index",
            "whats-new/2026-w32",
            "whats-new/2026-w30",
            "whats-new/2026-w29",
            "whats-new/2026-w28",
            "whats-new/2026-w27",
            "whats-new/2026-w26",
            "whats-new/2026-w25",
            "whats-new/2026-w24",
            "whats-new/2026-w23",
            "whats-new/2026-w22",
            "whats-new/2026-w21",
            "whats-new/2026-w20",
            "whats-new/2026-w19",
            "whats-new/2026-w18",
            "whats-new/2026-w17",
            "whats-new/2026-w16",
            "whats-new/2026-w15",
            "whats-new/2026-w14",
            "whats-new/2026-w13",
        ],
    ),
]


def slug_key(rel: str) -> str:
    # en/foo.md -> foo ; en/agent-sdk/bar.md -> agent-sdk/bar
    p = rel
    if p.startswith("en/"):
        p = p[3:]
    if p.endswith(".md"):
        p = p[:-3]
    return p


def main() -> None:
    # Rebuild manifest from disk to include extras
    pages: list[dict] = []
    for path in sorted((ROOT / "docs").rglob("*.md")):
        rel = str(path.relative_to(ROOT / "docs"))
        text = path.read_text(encoding="utf-8", errors="replace")
        title = slug_key(rel)
        summary = ""
        source = f"https://code.claude.com/docs/{rel}"
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                fm = text[3:end]
                for line in fm.splitlines():
                    if line.startswith("title:"):
                        title = line.split(":", 1)[1].strip().strip('"')
                    elif line.startswith("summary:"):
                        summary = line.split(":", 1)[1].strip().strip('"')
                    elif line.startswith("source:"):
                        source = line.split(":", 1)[1].strip().strip('"')
        pages.append(
            {
                "title": title,
                "summary": summary,
                "rel": rel,
                "path": f"docs/{rel}",
                "source": source,
                "html": source.replace(".md", ""),
                "bytes": path.stat().st_size,
                "slug": slug_key(rel),
            }
        )

    MANIFEST.write_text(json.dumps(pages, indent=2), encoding="utf-8")
    by_slug = {p["slug"]: p for p in pages}

    used: set[str] = set()
    sections: list[str] = []
    for section, blurb, slugs in TAXONOMY:
        lines = [f"## {section}", "", f"_{blurb}_", ""]
        for slug in slugs:
            page = by_slug.get(slug)
            if not page:
                continue
            used.add(slug)
            lines.append(
                f"- [{page['title']}]({page['path']}) — {page['summary'] or 'See page'}  \n"
                f"  Source: [{page['html']}]({page['html']})"
            )
        lines.append("")
        sections.append("\n".join(lines))

    leftover = [p for p in pages if p["slug"] not in used]
    if leftover:
        lines = ["## Other / uncategorized", ""]
        for page in leftover:
            lines.append(
                f"- [{page['title']}]({page['path']}) — {page['summary'] or 'See page'}  \n"
                f"  Source: [{page['html']}]({page['html']})"
            )
        lines.append("")
        sections.append("\n".join(lines))

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total_bytes = sum(p["bytes"] for p in pages)

    index = f"""# Claude Code Knowledge Base

> Offline mirror of the official Claude Code documentation from [code.claude.com/docs](https://code.claude.com/docs/en/).
>
> **Fetched:** {now}  
> **Pages:** {len(pages)}  
> **Size:** {total_bytes:,} bytes  
> **Full corpus dump:** [`llms-full.txt`](llms-full.txt) (~all pages concatenated)  
> **Index source:** [`llms.txt`](llms.txt)

## How to use this knowledge base

1. Browse by category below, or open files under [`docs/en/`](docs/en/).
2. For LLM ingestion / RAG, prefer `llms-full.txt` or individual `docs/en/**/*.md` files.
3. Re-fetch everything with: `python3 scripts/fetch_docs.py` then `python3 scripts/build_index.py`.
4. Each page has YAML frontmatter with `title`, `source`, `html`, and `summary`.

## Table of contents

"""
    for section, _, _ in TAXONOMY:
        anchor = re.sub(r"[^a-z0-9]+", "-", section.lower()).strip("-")
        index += f"- [{section}](#{anchor})\n"
    if leftover:
        index += "- [Other / uncategorized](#other--uncategorized)\n"
    index += "\n---\n\n" + "\n".join(sections)

    (ROOT / "INDEX.md").write_text(index, encoding="utf-8")

    readme = f"""# Claude Code Knowledge Base

Complete offline knowledge base of Anthropic's **Claude Code** documentation.

## Source

- Docs home: https://code.claude.com/docs/en/
- Machine-readable index: https://code.claude.com/docs/llms.txt
- Full dump: https://code.claude.com/docs/llms-full.txt

## Contents

| Asset | Description |
|-------|-------------|
| [`INDEX.md`](INDEX.md) | Categorized navigation of every page |
| [`docs/en/`](docs/en/) | Full markdown for each documentation page ({len(pages)} files) |
| [`llms.txt`](llms.txt) | Official page index |
| [`llms-full.txt`](llms-full.txt) | Official concatenated corpus |
| [`manifest.json`](manifest.json) | Machine-readable map of all fetched pages |
| [`scripts/fetch_docs.py`](scripts/fetch_docs.py) | Re-download all pages |
| [`scripts/build_index.py`](scripts/build_index.py) | Rebuild INDEX.md / manifest |

## Stats

- **Pages:** {len(pages)}
- **Fetched:** {now}
- **Total size:** {total_bytes:,} bytes

## Refresh

```bash
python3 scripts/fetch_docs.py
python3 scripts/build_index.py
```

## License / attribution

Documentation content © Anthropic. This folder is a local mirror for personal/knowledge-base use. Always prefer the live docs for the latest truth.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")
    print(f"INDEX.md written ({len(pages)} pages, {len(leftover)} uncategorized)")
    print(f"README.md written")


if __name__ == "__main__":
    main()
