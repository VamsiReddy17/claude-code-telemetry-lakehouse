# Claude Code Knowledge Base

Offline mirror of Anthropic's Claude Code documentation.

## Source

- Docs home: https://code.claude.com/docs/en/
- Index: https://code.claude.com/docs/llms.txt
- Full dump: https://code.claude.com/docs/llms-full.txt

## Contents

| Asset | Description |
|-------|-------------|
| [`INDEX.md`](INDEX.md) | Categorized navigation of every page |
| [`docs/en/`](docs/en/) | Full markdown for each documentation page |
| [`guides/`](guides/) | Curated supplements (e.g. Enterprise Inference Hooks) not in the Code docs mirror |
| [`llms.txt`](llms.txt) | Official page index |
| [`llms-full.txt`](llms-full.txt) | Official concatenated corpus |
| [`manifest.json`](manifest.json) | Machine-readable map of fetched pages |
| [`scripts/`](scripts/) | Re-download and rebuild tools |

## Refresh

```bash
python3 scripts/fetch_docs.py
python3 scripts/build_index.py
```

Documentation content © Anthropic. Local mirror for knowledge-base use.
