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

Update directory people from NVA and ORCID
------------------------------------------

This script refreshes `_directory/people/*/index.md` from [NVA](https://nva.sikt.no/) and [ORCID](https://orcid.org/). NVA data is preferred; ORCID is used as fallback when NVA data is missing.

Updated fields:

- Affiliation (`position`, `institution`, `institutions`)
- Tags (`tags` and `search_keywords`, from research topics)
- Bio (`summary`)
- Portrait (`image`, downloaded from NVA when available)
- Recent publications (`selected_works`, up to 10)

A GitHub Actions workflow runs this once per day (`.github/workflows/enrich-directory-people.yml`). Optional repository secret `NVA_API_TOKEN` enables authenticated portrait downloads from the NVA API.

```bash
pip install -r scripts/requirements.txt
python3 scripts/enrich_directory_from_nva.py --discover-nva --discover-nva-loose --max-works 10
```

Useful flags:

- `--slug <slug>` process one person (repeatable)
- `--dry-run` report changes without writing files
- `--no-download-images` skip portrait downloads

Combine image slices
--------------------

This script reads two images and creates one combined image where:

- the left side comes from the first image
- the right side comes from the second image

Quick start:

```bash
python3 scripts/combine_image_slices.py first.png second.png combined.png
```

Optional flags:

- `--left-ratio 0.5` keeps 50% of the first image width from the left edge.
- `--right-ratio 0.5` keeps 50% of the second image width from the right edge.

Example:

```bash
python3 scripts/combine_image_slices.py first.jpg second.jpg output.jpg --left-ratio 0.4 --right-ratio 0.6
```
