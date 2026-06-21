# MishMash-web

[![Web Quality Checks](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml)
[![Deploy Jekyll site to Pages](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml)

Source for [mishmash.no](https://mishmash.no) — the website of **MishMash Centre for AI and Creativity**, a Norwegian research consortium funded by the Research Council of Norway.

The site is a [Jekyll](https://jekyllrb.com/) static site (Cayman theme + custom CSS) published on GitHub Pages. Jekyll source lives in [`site/`](site/); tooling and config live at the repo root.

## About the site

English is the default language. Norwegian pages mirror key sections under `/no/…` with `lang: nb` and `translation_url` links.

| Area | Location | Notes |
| --- | --- | --- |
| People directory | `site/_directory/people/` | 117 profiles; many fields sync nightly from NVA |
| Institutions | `site/_directory/institutions/` | 36 entries |
| Projects | `site/_directory/projects/` | 22 entries |
| Research results | `site/_data/mishmash_results.yml` | MishMash NVA project publications |
| People network | `/people/network/` | Interactive graph with governance filters |
| Work packages | `site/wp1/` … `site/wp7/` | Public pages + internal password-gated copies |

- [CONTRIBUTING.md](CONTRIBUTING.md) — what to edit, generated files, PR workflow
- [scripts/README.md](scripts/README.md) — Python automation (NVA sync, events, tags, images)
- [config/README.md](config/README.md) — local NVA credentials and tag merge map
- [GitHub Wiki](https://github.com/MishMash-Norway/mishmash-web/wiki) — detailed maintenance guides

## Local setup

### Jekyll

```bash
bundle install
bundle exec jekyll serve --livereload
```

Site: `http://127.0.0.1:4000`

### Python scripts (optional)

For NVA/ORCID sync, directory validation, tag merging, and event helpers:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

NVA credentials: see [config/README.md](config/README.md). Never commit credential files.

## Where to edit content

All published content is under `site/`:

- **Hand-edited:** about pages, news, events, vacancies, work packages, institution entries, layouts/CSS
- **People profiles:** `site/_directory/people/<slug>/index.md` — many fields sync nightly from [NVA](https://nva.sikt.no/) when `urls.nva` is set
- **Machine-updated:** `site/_data/mishmash_results.yml`, person portraits, synced person fields (see CONTRIBUTING.md)

Copy `site/_directory/people/_template/` to add a new person. Set `slug`, `name`, and at least `urls.nva` or `urls.orcid`.

### Governance roles

Person `roles` are curated manually and drive filters on `/people/network/`. Use these canonical labels:

- `Member` — consortium members (not WP leaders)
- `Work package leader` — all 21 WP leaders listed in `site/_data/work_packages.yml`
- `Council member`, `Board member`, `Board Leader`, `Director`, `Deputy director`, `Research advisor`, `Administrative coordinator`
- `Associate member`, `Affiliate member` — external stakeholders

Run `python3 scripts/validate_directory.py` to catch deprecated role spellings (e.g. `Full member`, `Board Member`).

### Cross-links

List related people, institutions, and projects by **slug** only (e.g. `university-of-oslo`), not as `/people/…` paths. The reciprocity sync and validator enforce bidirectional links.

## Validation before push

```bash
bundle exec jekyll build --trace
bundle exec htmlproofer ./_site --disable-external --no-enforce-https
python3 scripts/validate_directory.py
```

The directory validator reports **errors** (broken links, missing fields) and **warnings** (deprecated roles, missing NVA/ORCID, WP leader role mismatches). Fix errors before merging; warnings are informational.

Optional accessibility scan (same as CI):

```bash
python3 -m http.server 4000 --directory _site &
npx --yes wait-on@7 http://127.0.0.1:4000/
npx --yes pa11y-ci@3 --config .pa11yci.json
```

## Automation

| What | How |
| --- | --- |
| Deploy to mishmash.no | Push/merge to `main` → `.github/workflows/pages.yml` |
| Quality checks on PRs | `.github/workflows/web-tests.yml` |
| Nightly directory sync | `.github/workflows/enrich-directory-people.yml` — NVA enrich, results sync, reciprocity fix, tag merge, validation |
| Merge similar tags | `python3 scripts/merge_tags.py` (see `config/tag_merge_map.yml`; also runs nightly in CI) |

The nightly workflow may push directly to `main` when NVA data or tag normalisation changes profiles or `site/_data/mishmash_results.yml`.

## Publish flow

1. Branch from `main`, commit changes.
2. Open a pull request.
3. Wait for **Web Quality Checks** to pass.
4. Merge to `main` — GitHub Pages deploys automatically.

## Questions

Write to contact@mishmash.no if you have any questions or comments.
