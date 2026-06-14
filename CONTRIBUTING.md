# Contributing to mishmash-web

This repository is the [MishMash](https://mishmash.no) website: a Jekyll site published on GitHub Pages, with Python scripts for syncing directory and research data from NVA and ORCID.

**Layout:** the published site is built from [`site/`](site/). Tooling, config, and docs live at the repo root. Public URLs are unchanged.

For day-to-day editing, see also the [README](README.md) and [scripts/README.md](scripts/README.md). Maintenance notes live in the [GitHub Wiki](https://github.com/MishMash-Norway/mishmash-web/wiki).

## Local setup

### Jekyll (required)

```bash
bundle install
bundle exec jekyll serve --livereload
```

Site: `http://127.0.0.1:4000`

### Python scripts (optional)

Needed for NVA/ORCID sync and some content helpers:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

NVA credentials: see [config/README.md](config/README.md). **Never commit credential files.**

## What to edit

### Hand-edited content (safe to change in git)

| Area | Location |
| --- | --- |
| Front page | `site/index.md`, `site/no/index.md` |
| About pages | `site/about/`, `site/no/about/` |
| Work packages | `site/wp1/` … `site/wp7/` |
| News | `site/_news/` |
| Events | `site/_events/` |
| Partner events listing | `site/_data/partner_events.yml` |
| Legal / info pages | `site/privacy/`, `site/accessibility/`, `site/no/privacy/`, `site/no/accessibility/` |
| Results page intro | `site/results/index.md`, `site/no/results/index.md` |
| UI strings (EN/NO) | `site/_data/translations.yml` |
| Layouts, includes, CSS | `site/_layouts/`, `site/_includes/`, `site/assets/css/` |
| Institutions | `site/_directory/institutions/` |
| New people (structure) | `site/_directory/people/<slug>/index.md` from `site/_directory/people/_template/` |

### Generated or machine-updated (do not edit by hand unless you know why)

| File / field | Updated by |
| --- | --- |
| `site/_data/mishmash_results.yml` | `scripts/sync_results_from_nva.py` (daily CI + manual) |
| Person portraits in `site/assets/images/portraits/` | NVA enrich script (daily CI) |
| Many person front-matter fields | `scripts/enrich_directory_from_nva.py` (daily CI) |

### Person profiles: what you can edit

When a person has `urls.nva`, the **daily sync overwrites** these fields from NVA:

- `position`, `department`, `institution`, `institutions`, `nva_affiliations`
- `tags`, `search_keywords`, `summary`, `selected_works`
- `urls.website`, `urls.nva`, `urls.orcid` (canonical URLs)
- `image` (when a portrait is downloaded)

These are **preserved** and intended for manual curation:

- `name`, `title`, `slug`
- `roles`, `projects`, `source_mentions`
- Other social URLs (`github`, `linkedin`, `youtube`, etc.)
- Markdown body below the front matter (if present)

To add a person: copy `site/_directory/people/_template/`, set `slug`, `name`, and at least `urls.nva` or `urls.orcid`. Run enrich locally or wait for the nightly workflow.

## Languages

English pages live at the site root (`/about/`, `/results/`, …). Norwegian mirrors use `/no/…`.

- Set `lang: nb` in Norwegian page front matter.
- Link EN ↔ NO with `translation_url` (see `site/about/description/index.md`).
- Shared labels use `site/_data/translations.yml` via `t.*` in layouts.

Prefer absolute asset paths (`/assets/...`) in shared includes so both languages work.

## Common tasks

### Add a news post or event

Create a new file in `site/_news/` or `site/_events/` with YAML front matter (`title`, `date`, etc.). Use existing entries as examples.

### Update research results

Results on `/results/` come from NVA project `2744839`. They refresh automatically each night. To run locally:

```bash
python3 scripts/sync_results_from_nva.py
```

Card layout and filters: `site/_includes/nva-results-list.html`, `site/assets/css/custom.css`.

### Refresh people from NVA/ORCID

```bash
python3 scripts/enrich_directory_from_nva.py --discover-nva --discover-nva-loose --max-works 10
```

Useful flags: `--slug <slug>`, `--dry-run`, `--no-download-images`. See [scripts/README.md](scripts/README.md) for partner events, RSS, and other helpers.

### Internal (password-protected) pages

Pages under `site/internal/` use layout `internal` and the hash in `_config.yml` (`internal_password_hash`). They are built with the public site but gated in the browser.

## Validation before opening a PR

Build:

```bash
bundle exec jekyll build --trace
```

Internal links (same as CI):

```bash
bundle exec htmlproofer ./_site --disable-external --no-enforce-https
```

Accessibility scan (optional, same as CI):

```bash
python3 -m http.server 4000 --directory _site &
npx --yes wait-on@7 http://127.0.0.1:4000/
npx --yes pa11y-ci@3 --config .pa11yci.json
```

Directory sanity check:

```bash
python3 scripts/validate_directory.py
```

## Pull request and deploy flow

1. Branch from `main`.
2. Commit changes (only commit generated NVA data if you ran sync intentionally).
3. Open a pull request.
4. Wait for [**Web Quality Checks**](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml) (build, links, HTML validation, Pa11y).
5. Merge to `main`.
6. [**Deploy Jekyll site to Pages**](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml) publishes to mishmash.no.

A separate scheduled workflow updates people and `site/_data/mishmash_results.yml` from NVA and may push directly to `main` (`.github/workflows/enrich-directory-people.yml`).

## Secrets and files to never commit

- `config/nva-credentials*.json` (except `*.example.json`)
- `venv/`, `vendor/`, `_site/`
- Passwords or API keys in source files

GitHub Actions uses repository secrets `NVA_CLIENT_ID` and `NVA_CLIENT_SECRET` for automated sync.

## Getting help

- Site content questions: [contact@mishmash.no](mailto:contact@mishmash.no)
- Repo maintenance: open an issue or ask in the MishMash web channel
- NVA API access: [Sikt NVA documentation](https://sikt.no/tjenester/nasjonalt-vitenarkiv-nva/hjelpeside-nva/teknisk-dokumentasjon-nva)
