# MishMash-web

[![Web Quality Checks](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/web-tests.yml)
[![Deploy Jekyll site to Pages](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml/badge.svg)](https://github.com/MishMash-Norway/mishmash-web/actions/workflows/pages.yml)

This is the source code for the web page of [MishMash Centre for AI and Creativity](https://mishmash.no). The page is built with Jekyll and published on GitHub Pages.

See [CONTRIBUTING.md](CONTRIBUTING.md) for what to edit, generated files, sync scripts, and the PR/deploy workflow.

The Jekyll site source lives in [`site/`](site/). URLs are unchanged.

## Maintain The Website

### 1) Local setup

Install Ruby gems (Jekyll and tooling):

```bash
bundle install
```

Optional Python helper scripts setup:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

Run locally:

```bash
bundle exec jekyll serve --livereload
```

Site will be available at `http://127.0.0.1:4000`.

### 2) Where to edit content

All site content is under `site/`:

- Front page content: `site/index.md`
- About pages: `site/about/` and `site/no/about/`
- News posts: `site/_news/`
- Events: `site/_events/`
- Directory entries:
  - people: `site/_directory/people/`
  - institutions: `site/_directory/institutions/`
  - projects: `site/_directory/projects/`
- Shared translations and event data: `site/_data/`

### 3) Validation before push

Build:

```bash
bundle exec jekyll build --trace
```

Check internal links (same check as CI):

```bash
bundle exec htmlproofer ./_site --disable-external --no-enforce-https
```

Accessibility scan (same URLs as CI):

```bash
python3 -m http.server 4000 --directory _site &
npx --yes wait-on@7 http://127.0.0.1:4000/
npx --yes pa11y-ci@3 --config .pa11yci.json
```

### 4) Publish flow

1. Create a branch and commit changes.
1. Open a pull request.
1. Ensure "Web Quality Checks" passes.
1. Merge to `main`.
1. GitHub Pages deployment runs automatically via `.github/workflows/pages.yml`.

### 5) Important maintenance notes

- Internal pages use a password hash in `_config.yml` (`internal_password_hash`).
  - To rotate password: `echo -n 'newpassword' | sha256sum`
  - Replace hash value and redeploy.
- Prefer absolute asset paths (`/assets/...`) in shared pages/includes to avoid language-path breakage.
- Keep event/news dates accurate and watch `future: true` behavior for future-dated entries.

## Wiki

Maintenance documentation is also available in the GitHub Wiki:

- [Wiki Home](https://github.com/MishMash-Norway/mishmash-web/wiki)
- [Maintaining the Page](https://github.com/MishMash-Norway/mishmash-web/wiki/Maintaining-the-Page)
