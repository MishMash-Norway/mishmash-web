# Alternative UI themes

This folder holds **alternative frontends (UI themes)** for mishmash.no —
anyone is welcome to contribute one. Each theme is a folder —
`themes/<theme-name>/` — whose files
*shadow* files in [`site/`](../site/) at the same relative path when the site is
built with that theme. Anything a theme does not override falls back to the
regular site, so a theme can be as small as one CSS file or as large as a full
redesign of every layout.

Nothing in this folder affects the regular website, whose production builds
only use `site/` — until a theme is *promoted* to become the main look (see
[Swapping the main look](#swapping-the-main-look) below). The look the site
had before the 2026 visual identity is kept here as the `bubbles` theme. Themes are built and viewed locally with the switcher
script — and every theme is also published automatically as a **live preview**
at `https://mishmash.no/ui/<name>/`, listed in the gallery at
[mishmash.no/ui/](https://mishmash.no/ui/). To appear in the gallery with a
title and description, add your theme to
[`site/_data/ui_themes.yml`](../site/_data/ui_themes.yml).

## Quick start

```bash
# one-time setup (repo root)
bundle install

# create your theme (copies the main layout as a starting point)
./scripts/ui new my-theme

# run the site with your theme — edits reload automatically
./scripts/ui serve my-theme
```

Then open <http://127.0.0.1:4000>. Edit files under `themes/my-theme/` and the
browser reloads on save.

## Switching between UIs

```bash
./scripts/ui list                       # what themes exist
./scripts/ui serve artsy                # try another theme
./scripts/ui serve default --port 4001  # the unmodified site, e.g. side by side
./scripts/ui build my-theme             # one-off build into .ui-work/_site/
```

## How the overlay works

`scripts/ui serve <name>` copies `site/` into a staging folder (`.ui-work/`,
git-ignored), copies your theme folder on top, and runs Jekyll on the result.
So this file in your theme:

```
themes/my-theme/_layouts/default.html
```

replaces

```
site/_layouts/default.html
```

and new files (e.g. `themes/my-theme/assets/css/theme.css`) are simply added.
Two files are special and **not** copied into the site: your theme's
`README.md`, and `_config.yml` (which is instead merged into the Jekyll
configuration, so you can override config values if you need to).

## What to override

| Path in your theme | What it controls |
| --- | --- |
| `_layouts/default.html` | The outer frame of every page: `<head>`, header, navigation, footer. **Start here.** |
| `_layouts/page.html`, `person.html`, `event.html`, `meeting.html`, `internal.html` | Page-type specific templates (all wrap into `default`). |
| `_includes/*.html` | Reusable fragments (news/event lists, result cards, language switcher, …). |
| `assets/css/custom.css` | The site's main custom stylesheet — override it to replace the current styling. |
| `assets/css/style.scss` | The base Cayman theme CSS. Create this file with empty front matter (`---`/`---`) to take over completely, or `@import "jekyll-theme-cayman";` and add overrides. |
| `assets/js/…`, images, fonts | Add anything you need and reference it from your layouts. |

Don't edit files in `site/` itself — keep all your work inside your theme
folder so UIs stay switchable.

**Gotcha:** `site/assets/css/custom.css` and `site/assets/css/identity.css` set
some rules (notably the header colours and link colours) with `!important`. If you layer an extra
stylesheet on top instead of replacing `custom.css`, you need `!important` on
those properties to win — see the bundled themes for examples.

## The content you can build on

All content is available to your Liquid templates exactly as on the real site:

- `site.directory` — people, institutions and projects (117 people profiles)
- `site.news`, `site.events` — news posts and events
- `site.data.mishmash_results` — publications synced from NVA
- `site.data.translations` — English/Norwegian UI strings (pages set `page.lang`)

Browse `site/_layouts/` and `site/_includes/` to see how the current UI uses
them, and copy anything you want as a starting point.

## Submitting your work

Work on a branch, keep everything inside `themes/<your-theme>/` (plus your
gallery entry in `site/_data/ui_themes.yml`), and open a pull request. Check
that `./scripts/ui build <your-theme>` completes without errors before
submitting. Once merged, your theme goes live at
`https://mishmash.no/ui/<your-theme>/` on the next deployment.

## Swapping the main look

The look of the main site is whatever is in `site/`; a theme is a candidate
look. When the consortium decides to adopt one, promote it:

```bash
./scripts/ui promote my-theme --keep-as look-2025
```

This does five things, in order: it saves the current `site/` versions of every
file the theme overrides as a new theme (`themes/look-2025/`, listed on `/ui/`
so the outgoing look stays browsable); copies the theme's files into `site/`;
removes `themes/my-theme/`, because `site/` is the single source of truth and a
copy left behind would drift from it; strips the theme badge from the promoted
layout and adds one to the snapshot; and swaps the two entries in
`site/_data/ui_themes.yml`. Keys in the theme's `_config.yml` are printed for
you to merge into the main `_config.yml` by hand, and the theme's README is
copied to `.ui-work/` so you can fold anything still relevant into the docs.
The command refuses to run with uncommitted changes under `site/` or `themes/`,
so that the swap is one clean commit. Afterwards: `bundle exec jekyll build`,
check the result, and commit `site/`, `themes/` and `_config.yml` together.

Files a theme adds that `site/` never had are copied in but are not part of the
snapshot, since there is nothing to save. Promotion copies files; it does not
edit content or recolour images. The switch of 2026-09-13 from the bubbles look
to the 2026 identity also recoloured the bubble, icon and cube images in
`site/assets/images/` to the new palette, keeping the originals in
`themes/bubbles/`; that was a one-off step outside the command.

The identity itself (wordmark, colours, type) is documented in
[BRAND.md](../BRAND.md), and its tokens live in `site/assets/css/brand.css`. A
theme that wants to keep the identity but change the layout should use those
tokens; a theme that proposes a different identity should ship its own.
