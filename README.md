# MishMash-web

[![Web Quality Checks](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml)
[![Deploy Jekyll site to Pages](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml)

Source for [mishmash.no](https://mishmash.no) — the website of the **MishMash Centre for AI and Creativity**, a Norwegian research centre funded by the Research Council of Norway (2025–2030).

The site is a [Jekyll](https://jekyllrb.com/) static site (Cayman theme + custom CSS) published on GitHub Pages. Jekyll source lives in [`site/`](site/); tooling and config live at the repo root. Public URLs are unchanged.

## About the site

| Area | URL | Source |
| --- | --- | --- |
| Front page | [/](https://mishmash.no/) | `site/index.md`, `site/no/index.md` |
| About & organisation | [/about/](https://mishmash.no/about/) | `site/about/`, `site/no/about/` |
| Work packages | [/wp1/](https://mishmash.no/wp1/) … [/wp7/](https://mishmash.no/wp7/) | `site/wp1/` … `site/wp7/` |
| Events & calendar | [/events/](https://mishmash.no/events/) | `site/_events/` |
| News | [/news/](https://mishmash.no/news/) | `site/_news/` |
| People | [/people/{slug}/](https://mishmash.no/people/) | `site/_directory/people/` |
| Institutions | [/institutions/{slug}/](https://mishmash.no/institutions/) | `site/_directory/institutions/` |
| Projects | [/projects/{slug}/](https://mishmash.no/projects/) | `site/_directory/projects/` |
| People network | [/people/network/](https://mishmash.no/people/network/) | `site/people/network/index.html` |
| Research results | [/results/](https://mishmash.no/results/) | NVA sync → `site/_data/mishmash_results.yml` |
| Vacancies | [/vacancies/](https://mishmash.no/vacancies/) | `site/vacancies/index.md` |
| Search | [/search/](https://mishmash.no/search/) | `site/search/` + `site/search.json` |
| Norwegian (Bokmål) | [/no/…](https://mishmash.no/no/) | `site/no/` |

English is the default language. Norwegian pages mirror key sections under `/no/…` with `lang: nb` and `translation_url` links.

## Documentation

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

## Validation before push

```bash
bundle exec jekyll build --trace
bundle exec htmlproofer ./_site --disable-external --no-enforce-https
python3 scripts/validate_directory.py
```

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
| Nightly people + results sync | `.github/workflows/enrich-directory-people.yml` |
| Merge similar tags | `python3 scripts/merge_tags.py` (see `config/tag_merge_map.yml`) |

## Publish flow

1. Branch from `main`, commit changes.
2. Open a pull request.
3. Wait for **Web Quality Checks** to pass.
4. Merge to `main` — GitHub Pages deploys automatically.

## Wiki

Extended documentation lives in the [GitHub Wiki](https://github.com/MishMash-Norway/mishmash-web/wiki):

- [Home](https://github.com/MishMash-Norway/mishmash-web/wiki)
- [Site Architecture](https://github.com/MishMash-Norway/mishmash-web/wiki/Site-Architecture)
- [Directory](https://github.com/MishMash-Norway/mishmash-web/wiki/Directory)
- [Scripts and Automation](https://github.com/MishMash-Norway/mishmash-web/wiki/Scripts-and-Automation)
- [Maintaining the Page](https://github.com/MishMash-Norway/mishmash-web/wiki/Maintaining-the-Page)
