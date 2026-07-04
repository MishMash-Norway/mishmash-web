# MishMash-web

[![Web Quality Checks](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml)
[![Deploy Jekyll site to Pages](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml)

Source for [mishmash.no](https://mishmash.no) — the website of **MishMash Centre for AI and Creativity**, a Norwegian research consortium funded by the Research Council of Norway.

The site is a [Jekyll](https://jekyllrb.com/) static site published on GitHub Pages. It is also a research and teaching project in itself: content is pulled from authoritative sources (NVA, ORCID, Wikipedia), pages experiment with [adaptive content and stretchtext](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy), and students build alternative frontends and backend automation. **The [wiki](https://github.com/MishMash-Norway/mishmash-web/wiki) is the main documentation** — this README only covers getting started.

## Quick start

```bash
bundle install
bundle exec jekyll serve --livereload   # → http://127.0.0.1:4000
```

Python automation (NVA/ORCID sync, validation, tags — optional):

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r scripts/requirements.txt
```

## What's where

| Path | Contents |
| --- | --- |
| `site/` | All published content: pages, collections (`_directory`, `_news`, `_events`), layouts, CSS/JS |
| `themes/` | Alternative student UI themes ([guide](themes/README.md)); switch with `./scripts/ui serve <name>` |
| `scripts/` | Python/Ruby automation ([overview](scripts/README.md)) and the `ui` theme switcher |
| `config/` | Local credentials (never committed) and tag merge map ([readme](config/README.md)) |

## Contributing

Branch from `main`, open a pull request, and merge when **Web Quality Checks** pass — GitHub Pages deploys `main` automatically. Before pushing:

```bash
bundle exec jekyll build --trace
bundle exec htmlproofer ./_site --disable-external --no-enforce-https
python3 scripts/validate_directory.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for what to edit (and what is machine-generated), and the wiki for guides:

- [Web Philosophy](https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy) — why the site works the way it does
- [Adaptive Content](https://github.com/MishMash-Norway/mishmash-web/wiki/Adaptive-Content) — authoring reading levels and stretchtext
- [Student Development](https://github.com/MishMash-Norway/mishmash-web/wiki/Student-Development) — frontend themes and backend work
- [Directory](https://github.com/MishMash-Norway/mishmash-web/wiki/Directory) — people/institutions/projects, NVA sync, roles
- [Site Architecture](https://github.com/MishMash-Norway/mishmash-web/wiki/Site-Architecture), [Deployment](https://github.com/MishMash-Norway/mishmash-web/wiki/Deployment), [Maintaining the Page](https://github.com/MishMash-Norway/mishmash-web/wiki/Maintaining-the-Page)

## Questions

Write to contact@mishmash.no if you have any questions or comments.
