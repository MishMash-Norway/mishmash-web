# Instructions for coding agents

This file is for any agent working on mishmash.no: GitHub Copilot (chat, agent mode or the coding agent), Codex, Claude Code or another. Read it first, then [CONTENT_HANDOVER.yml](CONTENT_HANDOVER.yml), which holds the content types, the routing, the runbooks and the full list of checks. [CONTRIBUTING.md](CONTRIBUTING.md) and the [wiki](https://github.com/MishMash-Norway/mishmash-web/wiki) are the human guides to the same rules.

## What the repository is

mishmash.no is a Jekyll 3 site on GitHub Pages, built from `site/` with the config at the repository root. It is published in three languages: English under `site/` is the source, Bokmål under `site/no/` is a mix of machine translations of the English and pages written or reviewed by a person, and Nynorsk under `/nn/` is generated from the Bokmål pages at every build by `scripts/build_nynorsk.py`. People, institutions and projects live in `site/_directory/`; most listings are driven by YAML in `site/_data/`. A nightly workflow refreshes people and results from NVA and ORCID and pushes to `main` by itself.

## How to work

1. Classify the request with `routing` in `CONTENT_HANDOVER.yml` and open one existing file of the same kind before writing a new one. Copy its front matter rather than inventing fields.
2. Make the smallest change that does the job, in the source files only.
3. Keep the languages in step (see below).
4. Run the checks for what you touched, from the repository root (see below).
5. For anything larger than a small text or data fix, work on a branch and open a pull request, so the quality checks run before publication. Small fixes go straight to `main`. Either way, pull first: other people and the nightly sync push to `main` too.
6. After a push, watch the two workflows, Web Quality Checks and Deploy Jekyll site to Pages. `main` has no required checks, so a red cross is the only signal that something broke.
7. Report which files changed, which checks ran and what was left undone.

Ask the person you work for before anything that cannot be undone or that reaches outside the repository: deleting pages or people, publishing a draft, sending email, posting to an external service, or rewriting a file someone has edited by hand. Everything else in git is reversible; proceed.

## Languages

- An edit to a page under `site/` is made to its mirror under `site/no/` in the same change, and the other way round, with the same headings in the same order.
- Never edit `site/nn-auto/`; it is generated and ignored by git. Fix the Bokmål page, or add a rule to `site/_data/nynorsk_glossary.yml`. A page reviewed by a person lives under `site/nn/` and is no longer generated.
- The Nynorsk build holds the output to the term list `site/_data/terms.yml`; `--check-terms` fails when a listed term does not come out as listed.
- Two exceptions to the mirror rule: internal pages (`site/internal/`) are in English only, and board meeting documents (`site/no/about/organisation/board/meetings/`) are in Bokmål only; the board page lists them in every language.
- A Bokmål page counts as an automatic translation (`translation.automatic: true`, the default in `_config.yml`) until a person has written or reviewed it; that page sets `translation:` `automatic: false` in its front matter. Never set it to false on a page you drafted yourself.
- In Norwegian, write KI for artificial intelligence, never AI, and use conservative Bokmål.

## Writing rules

- British English in English prose.
- No em dash (U+2014) and no spaced dash as a sentence break: use a comma, a colon, a full stop or brackets. An unspaced en dash between bounds is fine (`13–14 April`). `scripts/check_dashes.py` enforces this.
- No bold inside a sentence. No exclamation marks or contractions in the site's own prose.
- Proper Markdown links, never bare URLs.
- Public text, including issues and commit messages, names no person as the author of a decision: write the centre, the board, the site maintainer.
- Present tense in documentation; a dated account goes in the closing section "How this page has developed".
- Numbers in the site's prose come from data or a script, not from memory.

## Files you must not hand-edit

`site/nn-auto/`, `site/_data/nynorsk_status.yml`, `site/_data/translations_nn.yml`, `site/_data/mishmash_results.yml`, `site/_data/page_git_meta.yml`, `site/chat/knowledge.json`, `_site/`, and the fields of a person entry that the nightly sync overwrites (`content_types.directory_person.fields_overwritten_when_urls_nva_is_set` in `CONTENT_HANDOVER.yml`). Never commit anything in `config/` except the `*.example.json` files, and never commit credentials.

## Common patterns

- A partner event or partner news item is a record in `site/_data/partner_events.yml` or `partner_news.yml`, not a page. Then run `python3 scripts/fetch_partner_og_data.py` and `python3 scripts/build_partner_thumbnails.py`, and commit the new thumbnail.
- A centre event or MeshUp is a file in `site/_events/`; a MeshUp has `MeshUp` and its work package in `categories`, and a speaker portrait goes in `site/assets/images/portraits/` at 600 by 600 pixels.
- A page that should be built but not announced (a draft call, a placeholder) sets `sitemap: false` and `noindex: true`, is linked from nowhere, and opens with a bracketed note saying what is missing.
- Open questions for the person go in square brackets inside the document, with a recommendation first.
- New people from the participation form follow the runbook `automation.people_import_from_the_form`; the scripts exist, do not write new ones. Every member needs an ORCID (board and council members are exempt), and `validate_directory.py` fails on a new member without one: ask for the ORCID, or keep the entry `published: false` until it comes. Never add a name to `site/_data/orcid_pending.yml`; that list only shrinks.

## Checks

The full local sequence, mirroring CI, is `build_and_ci.local_ci_sequence` in `CONTENT_HANDOVER.yml`. The ones to run for most edits:

```bash
git diff --check
python3 scripts/validate_directory.py          # if site/_directory/ was touched
python3 scripts/check_dashes.py
python3 scripts/check_liquid_conditions.py     # if Liquid was touched
python3 scripts/build_nynorsk.py --check-glossary --check-terms   # if Bokmål was touched
bundle exec jekyll build --trace
```

Python scripts run from a virtual environment in the repository (`python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt`), never the system Python with packages installed globally. Without Apertium installed, the Nynorsk build uses the public service at apertium.org, which can differ from the CI result; read the published page.

Jekyll 3 Liquid has no brackets and reads a chain mixing `and` and `or` from the right; assign each test to a variable instead. `where_exp` takes no `and` or `or`.
