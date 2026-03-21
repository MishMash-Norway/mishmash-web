Fetch UIO / Ritmo event pages
=================================

This script fetches event pages (e.g. from the UIO / Ritmo site) and extracts basic metadata.

Quick start:

1. Install deps (recommended in a venv):

```bash
pip install -r scripts/requirements.txt
```

1. Run against a single page:

```bash
python3 scripts/fetch_uio_events.py "https://www.uio.no/.../deichman/index.html" --out-dir _events
```

1. Or provide a file with one URL per line:

```bash
python3 scripts/fetch_uio_events.py urls.txt --from-file --out-dir scripts/output
```

The script emits either JSON to stdout (`--json`) or writes Jekyll-style markdown files with front-matter into `--out-dir`.

Fetch AI-focused partner events
-------------------------------

This script scans partner links listed in `index.md`, discovers likely event pages,
extracts event candidates, filters for AI-focused events, and appends new items to
`_data/partner_events.yml`.

Quick start:

1. Install deps (same as above):

```bash
pip install -r scripts/requirements.txt
```

1. Preview what would be added:

```bash
python3 scripts/fetch_partner_ai_events.py --dry-run
```

1. Append new events to partner listing:

```bash
python3 scripts/fetch_partner_ai_events.py
```

Useful flags:

- `--max-pages-per-partner 4` limits crawl depth per partner site.
- `--max-partners 40` limits total partners scanned.
- `--output _data/partner_events.yml` writes to a custom destination file.
