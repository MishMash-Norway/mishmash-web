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
python3 scripts/fetch_uio_events.py "https://www.uio.no/.../deichman/index.html"
```

Paths default to `site/` (see `scripts/repo_paths.py`). To write elsewhere:

```bash
python3 scripts/fetch_uio_events.py "https://www.uio.no/.../deichman/index.html" --out-dir site/_events
```

1. Or provide a file with one URL per line:

```bash
python3 scripts/fetch_uio_events.py urls.txt --from-file --out-dir scripts/output
```

The script emits either JSON to stdout (`--json`) or writes Jekyll-style markdown files with front-matter into `--out-dir`.

Fetch AI-focused partner events
-------------------------------

This script scans partner links listed in `site/index.md`, discovers likely event pages,
extracts event candidates, filters for AI-focused events, and appends new items to
`site/_data/partner_events.yml`.

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
- `--output site/_data/partner_events.yml` writes to a custom destination file.

Update directory people from NVA and ORCID
------------------------------------------

This script refreshes `site/_directory/people/*/index.md` from [NVA](https://nva.sikt.no/) and [ORCID](https://orcid.org/). When a person has `urls.nva`, **NVA overwrites** synced fields: affiliation (`institution`, `institutions` from **active** affiliations only, `department` for the primary unit), tags, bio, publications, website, and portrait. Inactive NVA affiliations are ignored. `name` and `title` are never changed.

Updated fields:

- Affiliation (`position`, `institution`, `institutions`)
- Tags (`tags` and `search_keywords`, from research topics)
- Bio (`summary`)
- Portrait (`image`, downloaded from NVA when available)
- Recent publications (`selected_works`, up to 10)

A GitHub Actions workflow runs this once per day (`.github/workflows/enrich-directory-people.yml`), including a sync of MishMash project results to `site/_data/mishmash_results.yml` for `/results/`.

### NVA API access (UiO / MishMash)

Request credentials from Sikt using the [NVA API access form](https://sikt.no/tjenester/nasjonalt-vitenarkiv-nva/hjelpeside-nva/teknisk-dokumentasjon-nva) (customer institution, contact person, purpose, Test/Prod). Sikt returns a **client ID** and **client secret** for OAuth2 client credentials ([authentication docs](https://github.com/BIBSYSDEV/nva-api-documentation/blob/main/scenarios/authenticating/index.md)).

Suggested form values for MishMash:

| Field | Value |
| --- | --- |
| Kundeinstitusjon | UiO |
| Kontaktperson | Alexander Refsum Jensenius |
| E-post | a.r.jensenius@imv.uio.no |
| Bruksområde | MishMash-nettsider (directory people profiles) |
| Tilgang | **Prod** for the live site; **Test** optional for local experiments |

After you receive credentials from Sikt (JSON files with `clientId` and `clientSecret`):

1. **Local config folder** (recommended, gitignored):

```bash
cp /path/to/uio-web-credentials\ 1.json config/nva-credentials.prod.json
cp /path/to/uio-web-credentials.json config/nva-credentials.test.json
```

See `config/README.md`. The SMS password is not the OAuth client secret.

2. **Or environment variables** (never commit):

```bash
export NVA_API_ENV=prod
export NVA_CLIENT_ID='…'
export NVA_CLIENT_SECRET='…'
```

3. **Verify**:

```bash
pip install -r scripts/requirements.txt
python3 scripts/test_nva_api_auth.py
```

4. **GitHub Actions** — in the MishMash repo go to **Settings → Secrets and variables → Actions → New repository secret**:

| Secret | Value |
| --- | --- |
| `NVA_CLIENT_ID` | client ID from Sikt |
| `NVA_CLIENT_SECRET` | client secret from Sikt |

The workflow sets `NVA_API_ENV=prod` automatically. Tokens expire after 15 minutes; the script fetches a fresh token on each run.

API hosts ([nva-api-documentation](https://github.com/BIBSYSDEV/nva-api-documentation)): production `https://api.nva.unit.no`, test `https://api.test.nva.aws.unit.no`. Swagger UI: [swagger-ui.nva.unit.no](https://swagger-ui.nva.unit.no/#/).

```bash
pip install -r scripts/requirements.txt
python3 scripts/enrich_directory_from_nva.py --discover-nva --discover-nva-loose --max-works 10
python3 scripts/sync_results_from_nva.py
```

Useful flags:

- `--slug <slug>` process one person (repeatable)
- `--dry-run` report changes without writing files
- `--no-download-images` skip portrait downloads

Fill Missing NVA and ORCID Links Only
-------------------------------------

This script only updates missing `urls.nva` and `urls.orcid` in
`site/_directory/people/*/index.md`, without changing other profile fields.

Quick start:

```bash
python3 scripts/fill_missing_nva_orcid.py --dry-run
python3 scripts/fill_missing_nva_orcid.py --discover-nva-loose
```

Useful flags:

- `--slug <slug>` process one person (repeatable)
- `--discover-nva-loose` allow looser name matching
- `--dry-run` report changes without writing files

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
