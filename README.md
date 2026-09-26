# MishMash-web

[![Web Quality Checks](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml)
[![Deploy Jekyll site to Pages](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml)

Source for [mishmash.no](https://mishmash.no), the website of the MishMash Centre for AI and Creativity, a Norwegian research consortium funded by the Research Council of Norway. The site is published in English, Bokmål and Nynorsk; the Nynorsk pages are generated from the Bokmål ones at every build.

## Want to change something on the website?

The site is a [Jekyll](https://jekyllrb.com/) static site published on GitHub Pages. There is no content management system: every page is a text file in this repository. Committing a change kicks off the build process automatically and publishes a new version of the page in a few minutes. 

Check the [wiki](https://github.com/MishMash-Norway/mishmash-web/wiki) for documentation about how the page works. Start with [Start Here][start], then [Your First Edit][first]. Then you can explore [Adding News][news], [Adding Events][events], [Markdown Basics][md], [When Things Go Wrong][wrong].

To get started with agentic coding, sign up for [GitHub Education](https://github.com/education). It is free for academic staff and students, and it includes Copilot.

Check our [web Philosophy][why] for an explanation of why the site is built this way. 

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

Install Ruby and run the checks before pushing: [Running the Site Locally][local].

## Where to find things

| Path | Contents |
| --- | --- |
| `site/` | All published content: pages, collections (`_directory`, `_news`, `_events`), layouts, CSS and JS |
| `themes/` | Student UI themes ([guide](themes/README.md)), published at `/ui/<name>/` |
| `scripts/` | Python and Node automation ([overview](scripts/README.md)) and the `ui` theme switcher |
| `tests/visual/` | Playwright specs: screenshots of the main look and the themes with their baselines, and the behaviour of the header menus and the abbreviation toggles (`npm run visual`, `visual:themes`, `visual:update`) |
| `tests/chat/` | The question set the Ask MishMash retrieval is scored against |
| `CONTENT_HANDOVER.yml` | The brief for agents and automated tools: what may be edited, the rules, the runbooks |
| `config/` | Local credentials (never committed) and the tag merge map ([readme](config/README.md)) |
| `BRAND.md` | The visual identity: wordmark, colours, type, and the rules for using them |

More detail: [Site Architecture][arch] and [Deployment][deploy].

## Contributing

If you want to change something, create a branch and open a pull request so the quality checks run before publication — see [Branches and Pull Requests][pr].

[CONTRIBUTING.md](CONTRIBUTING.md) covers what is safe to edit and what is machine-generated. Much of the [directory][dir] is refreshed nightly from NVA and ORCID, so some fields are overwritten if you edit them by hand.

## Look and feel

The visual identity (wordmark, colours, type) is documented in [BRAND.md](BRAND.md) and shown at [mishmash.no/internal/brand/](https://mishmash.no/internal/brand/); stylesheets use the tokens in `site/assets/css/brand.css`. The look can be swapped: any theme in `themes/` can be promoted to become the main site with `./scripts/ui promote <name>`, and the outgoing look is kept as a theme. The `bubbles` theme at [mishmash.no/ui/bubbles/](https://mishmash.no/ui/bubbles/) keeps the earlier bubbles look as an alternative. Details: [Visual Identity and Theming][brand] and [themes/README.md](themes/README.md).

## Licences

The code in this repository (scripts, layouts, includes, stylesheets, JavaScript and themes) is under the [MIT licence](LICENSE). The text of the website is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), the site's own data files are [CC0](https://creativecommons.org/publicdomain/zero/1.0/), and images carry their own terms. Personal data in the directory is published under the site's privacy notice, not a licence. The full terms are in the communication strategy on the site.

## Questions and comments

If you have questions or comments about the code, please use the [issues tracker](https://github.com/MishMash-Norway/mishmash-web/issues). For general things, write to contact@mishmash.no.

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
[brand]: https://github.com/MishMash-Norway/mishmash-web/wiki/Visual-Identity-and-Theming

## How this document has developed

- Until 13 September 2026 the main site used the bubbles look, kept since as the `bubbles` theme.
