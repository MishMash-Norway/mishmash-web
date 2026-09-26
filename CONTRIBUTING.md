# Contributing to mishmash-web

This repository is the [MishMash](https://mishmash.no) website: a Jekyll site published on GitHub Pages, with Python scripts for syncing directory and research data from NVA and ORCID.

Layout: the published site is built from [`site/`](site/). Tooling, config, and docs live at the repo root. The brief for agents and automated tools is [`CONTENT_HANDOVER.yml`](CONTENT_HANDOVER.yml).

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
| Legal / info pages | `site/privacy/`, `site/accessibility/`, `site/about/terms/`, and their Norwegian mirrors under `site/no/` |
| Results page intro | `site/results/index.md`, `site/no/results/index.md` |
| UI strings (EN/NB) | `site/_data/translations.yml`; the Nynorsk strings are generated |
| Languages | `site/_data/languages.yml` (the switch order); see the wiki page Nynorsk |
| Lab experiments | `site/lab/<slug>/` from `site/lab/_template/`; see the wiki page Lab |
| Reviewed Nynorsk pages | `site/nn/<path>` overrides the generated page at the same path |
| Layouts, includes, CSS | `site/_layouts/`, `site/_includes/`, `site/assets/css/` |
| Visual identity: tokens, identity styling, logo files | `site/assets/css/brand.css`, `site/assets/css/identity.css`, `site/assets/images/logo/`; rules in [BRAND.md](BRAND.md) |
| Alternative looks (UI themes) | `themes/<name>/`; swap the main look with `./scripts/ui promote <name>` ([guide](themes/README.md)) |
| Institutions | `site/_directory/institutions/` |
| New people (structure) | `site/_directory/people/<slug>/index.md` from `site/_directory/people/_template/` |

### Generated or machine-updated (do not edit by hand unless you know why)

| File / field | Updated by |
| --- | --- |
| `site/_data/mishmash_results.yml` | `scripts/sync_results_from_nva.py` (daily CI + manual) |
| Person portraits in `site/assets/images/portraits/` | NVA enrich script (daily CI) |
| Many person front-matter fields | `scripts/enrich_directory_from_nva.py` (daily CI) |
| `site/chat/knowledge.json` | `scripts/build_knowledge_base.py` (rebuilt at every deploy) |
| `site/_data/wikidata_institutions.yml`, `urls.ror` | `scripts/sync_wikidata.py` (daily CI) |
| `site/nn-auto/`, `site/_data/translations_nn.yml` | `scripts/build_nynorsk.py` (every build; ignored by git) |
| `site/data/*.json`, `*.csv` | `scripts/build_open_data.py` (every deploy; ignored by git) |
| `site/assets/images/thumbs/`, `site/assets/images/partner-thumbs/` | `scripts/build_thumbnails.py`, `scripts/build_partner_thumbnails.py` (daily CI, committed) |
| `*.avif` under `news`, `events` and `illustrations` | `scripts/build_avif.py` (every deploy; ignored by git) |
| `site/_data/results_openalex.yml`, `research_catalogue.yml`, `member_posts.yml` | `scripts/enrich_results_from_openalex.py`, `sync_research_catalogue.py`, `fetch_member_feeds.py` (daily CI) |
| `site/_data/page_git_meta.yml`, `ai_colophon.yml` | `scripts/generate_page_git_meta.py`, `generate_ai_colophon_stats.py` (every deploy) |
| `site/assets/images/bubbles/daily/` | `scripts/generate_daily_bubbles.py` (daily CI) |
| `site/_data/language_share.yml`, `nynorsk_status.yml` | `scripts/measure_languages.py`, `build_nynorsk.py` (ignored by git) |

### Person profiles: what you can edit

When a person has `urls.nva`, the **daily sync overwrites** these fields from NVA:

- `position`, `department`, `institution`, `institutions`, `nva_affiliations`
  (guest and visiting affiliations are ignored; a person whose only NVA
  affiliation is a guest role ends up with no position or institution, so add
  the real employer by hand if it is known)
- `tags`, `search_keywords`, `summary`, `selected_works`
- `urls.institutional_website`, `urls.nva`, `urls.orcid` (canonical URLs)
- `image` (when a portrait is downloaded)

These are **preserved** and intended for manual curation:

- `name`, `title`, `slug`
- `roles`, `projects`, `source_mentions`
- Other social URLs (`personal_website`, `github`, `linkedin`, `youtube`, etc.)
- Markdown body below the front matter (if present)

To add a person: copy `site/_directory/people/_template/`, set `slug`, `name`, and at least `urls.nva` or `urls.orcid`. Run enrich locally or wait for the nightly workflow.

### Tags

Tags appear on person pages, events, and the [people network](https://mishmash.no/lab/people-network/). The conventions:

- **Form:** short, human-readable phrases in title case, `Music Technology`, not `music-technology` or `MUSIC TECH`; connector words such as `and`, `of` and `to` stay lower case inside a tag. Acronyms keep their casing (`AI`, `3D`). No abbreviations otherwise. The nightly merge applies this casing, so a tag written otherwise is rewritten.
- **Count:** 2–6 tags per entry. `validate_directory.py` warns above 6.
- **Reuse before inventing:** check whether an existing tag fits before adding a new spelling; the network view only connects people whose tags match.
- **Source of truth for people:** profiles with `urls.nva` get tags from NVA on the nightly sync — lasting fixes belong in NVA or in the merge map, not in the profile file.
- **Cleanup routine:** near-duplicate spellings are merged nightly by `scripts/merge_tags.py` using [`config/tag_merge_map.yml`](config/tag_merge_map.yml); add mappings there to fold variants together. `python3 scripts/merge_tags.py --report` suggests candidates. Groupings for the network view live in `site/_data/tag_groups.yml`.

## Languages

English pages live at the site root (`/about/`, `/results/`, …). Norwegian mirrors use `/no/…`.

- Set `lang: nb` in Norwegian page front matter.
- Link the English and Bokmål pages with `translation_url` (see `site/about/description/index.md`).
- Nynorsk is generated from the Bokmål pages by `scripts/build_nynorsk.py` into `site/nn-auto/` at build time; a reviewed page at `site/nn/<path>` takes precedence. Terms live in `site/_data/glossary.yml` (en, nb, nn; exported as `/data/terminology.json`), abbreviations in `site/_data/abbreviations.yml`, and the generator's word list in `site/_data/nynorsk_glossary.yml`.
- Shared labels use `site/_data/translations.yml` via `t.*` in layouts.

Prefer absolute asset paths (`/assets/...`) in shared includes so both languages work.

Colours and fonts come from the `--mm-*` custom properties in `site/assets/css/brand.css`; do not hard-code hex values, and do not use `#A7A1F4`, `#C1F7AE` or `#363644`; they are not part of the identity. Fonts are self-hosted; do not add a remote font service. See [BRAND.md](BRAND.md).

## Reading levels and breadcrumbs

A page with `adaptive: true` carries its text at three reading levels in `div.adaptive` blocks (`data-for="simple|standard|advanced"`); the default level is `advanced`, set in `site/_data/audiences.yml`, and `python3 scripts/check_readability.py --strict` checks the levels. Every page opens with a breadcrumb trail from `site/_includes/breadcrumbs.html`; `breadcrumbs: false` in the front matter switches it off.

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
npx --yes pa11y-ci@4 --config .pa11yci.json
```

Directory sanity check and the prose checks CI blocks on:

```bash
python3 scripts/validate_directory.py
python3 scripts/check_dashes.py
python3 scripts/check_liquid_conditions.py
python3 scripts/check_terminology.py
python3 scripts/check_event_alt.py
python3 scripts/image_provenance.py --check
python3 scripts/build_nynorsk.py --check-glossary
```

The states a page scan cannot reach, after serving `_site` as above:

```bash
npx playwright test -c tests/visual/playwright.config.js tests/visual/menus.spec.js
npx playwright test -c tests/visual/playwright.config.js tests/visual/abbreviations.spec.js
node scripts/check_contrast.mjs
```

## Pull request and deploy flow

1. Branch from `main`.
2. Commit changes (only commit generated NVA data if you ran sync intentionally).
3. Open a pull request.
4. Wait for [Web Quality Checks](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml): directory validation with the prose and script checks, the build, links, HTML validation, Pa11y, the menu and contrast tests and the Ask MishMash retrieval score block; external links, Lighthouse, visual regression and the student themes report without blocking.
5. Merge to `main`.
6. [**Deploy Jekyll site to Pages**](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml) publishes to mishmash.no.

A separate scheduled workflow (`.github/workflows/enrich-directory-people.yml`) refreshes people and results from NVA and ORCID, adds open-access status, expositions and members' posts, resolves Wikidata, repairs cross-links, merges tags, regenerates the daily bubbles, marks provenance, builds the thumbnails, validates, and may push directly to `main`.

## Secrets and files to never commit

- `config/nva-credentials*.json` (except `*.example.json`) and `config/nettskjema-credentials.json`
- `venv/`, `vendor/`, `_site/`
- Passwords or API keys in source files

GitHub Actions uses repository secrets `NVA_CLIENT_ID` and `NVA_CLIENT_SECRET` for automated sync.

## Getting help

- Site content questions: [contact@mishmash.no](mailto:contact@mishmash.no)
- Repo maintenance: open an issue or ask in the MishMash web channel
- NVA API access: [Sikt NVA documentation](https://sikt.no/tjenester/nasjonalt-vitenarkiv-nva/hjelpeside-nva/teknisk-dokumentasjon-nva)

## How this document has developed

- The site source moved into `site/`; public URLs did not change.
- The tag conventions were decided in issue #13.
- September 2026: the purple/green palette (`#A7A1F4`, `#C1F7AE`, `#363644`) was replaced by the 2026 identity.
