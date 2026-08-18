# MishMash-web

[![Web Quality Checks](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml)
[![Deploy Jekyll site to Pages](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml)

Source for [mishmash.no](https://mishmash.no), the website of the MishMash Centre for AI and Creativity — a Norwegian research consortium funded by the Research Council of Norway.

The site is a [Jekyll](https://jekyllrb.com/) static site published on GitHub Pages. There is no content management system: every page is a text file in this repository, and committing a change publishes it.

The [wiki](https://github.com/MishMash-Norway/mishmash-web/wiki) is the documentation. This README points you at the right part of it.

## Want to change something on the website?

You do not need to install anything, and you do not need to know Git, Markdown or Jekyll.

Start with [Start Here][start], then [Your First Edit][first]. Half an hour, entirely in your browser, and at the end you will have changed the live site. From there: [Adding News][news], [Adding Events][events], [Markdown Basics][md], [When Things Go Wrong][wrong], and — once the browser is no longer enough — [Editing in VS Code][vscode] and [Using GitHub Copilot][copilot].

Everyone working on the site should sign up for [GitHub Education](https://github.com/education). It is free for academic staff and students, and it includes Copilot.

## Running the site locally

```bash
bundle install
bundle exec jekyll serve --livereload   # → http://127.0.0.1:4000
```

Python automation for the NVA and ORCID sync, validation and tags is optional:

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r scripts/requirements.txt
```

Installing Ruby, and the checks to run before pushing: [Running the Site Locally][local].

## What's where

| Path | Contents |
| --- | --- |
| `site/` | All published content: pages, collections (`_directory`, `_news`, `_events`), layouts, CSS and JS |
| `themes/` | Student UI themes ([guide](themes/README.md)), published at `/ui/<name>/` |
| `scripts/` | Python automation ([overview](scripts/README.md)) and the `ui` theme switcher |
| `config/` | Local credentials (never committed) and the tag merge map ([readme](config/README.md)) |

More detail: [Site Architecture][arch] and [Deployment][deploy].

## Contributing

Small text fixes can go straight to `main` and publish within a couple of minutes. For anything larger, branch and open a pull request so the quality checks run before publication — see [Branches and Pull Requests][pr].

[CONTRIBUTING.md](CONTRIBUTING.md) covers what is safe to edit and what is machine-generated. Much of the [directory][dir] is refreshed nightly from NVA and ORCID, so some fields are overwritten if you edit them by hand.

Why the site is built this way, and what it is experimenting with: [Web Philosophy][why]. Student projects: [Student Development][students].

Questions to contact@mishmash.no.

[start]: https://github.com/MishMash-Norway/mishmash-web/wiki/Start-Here
[first]: https://github.com/MishMash-Norway/mishmash-web/wiki/Your-First-Edit
[news]: https://github.com/MishMash-Norway/mishmash-web/wiki/Adding-News
[events]: https://github.com/MishMash-Norway/mishmash-web/wiki/Adding-Events
[md]: https://github.com/MishMash-Norway/mishmash-web/wiki/Markdown-Basics
[wrong]: https://github.com/MishMash-Norway/mishmash-web/wiki/When-Things-Go-Wrong
[vscode]: https://github.com/MishMash-Norway/mishmash-web/wiki/Editing-in-VS-Code
[copilot]: https://github.com/MishMash-Norway/mishmash-web/wiki/Using-GitHub-Copilot
[local]: https://github.com/MishMash-Norway/mishmash-web/wiki/Running-the-Site-Locally
[pr]: https://github.com/MishMash-Norway/mishmash-web/wiki/Branches-and-Pull-Requests
[arch]: https://github.com/MishMash-Norway/mishmash-web/wiki/Site-Architecture
[deploy]: https://github.com/MishMash-Norway/mishmash-web/wiki/Deployment
[dir]: https://github.com/MishMash-Norway/mishmash-web/wiki/Directory
[why]: https://github.com/MishMash-Norway/mishmash-web/wiki/Web-Philosophy
[students]: https://github.com/MishMash-Norway/mishmash-web/wiki/Student-Development
