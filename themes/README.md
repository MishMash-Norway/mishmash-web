# Alternative UI themes

This folder holds **alternative frontends (UI themes)** for mishmash.no, made by
student groups. Each theme is a folder — `themes/<group-name>/` — whose files
*shadow* files in [`site/`](../site/) at the same relative path when the site is
built with that theme. Anything a theme does not override falls back to the
regular site, so a theme can be as small as one CSS file or as large as a full
redesign of every layout.

Nothing in this folder affects the live website: production builds only use
`site/`. Themes are built and viewed locally with the switcher script.

## Quick start

```bash
# one-time setup (repo root)
bundle install

# create your group's theme (copies the main layout as a starting point)
./scripts/ui new group-a

# run the site with your theme — edits reload automatically
./scripts/ui serve group-a
```

Then open <http://127.0.0.1:4000>. Edit files under `themes/group-a/` and the
browser reloads on save.

## Switching between UIs

```bash
./scripts/ui list                       # what themes exist
./scripts/ui serve group-b              # try another group's UI
./scripts/ui serve default --port 4001  # the unmodified site, e.g. side by side
./scripts/ui build group-a              # one-off build into .ui-work/_site/
```

## How the overlay works

`scripts/ui serve <name>` copies `site/` into a staging folder (`.ui-work/`,
git-ignored), copies your theme folder on top, and runs Jekyll on the result.
So this file in your theme:

```
themes/group-a/_layouts/default.html
```

replaces

```
site/_layouts/default.html
```

and new files (e.g. `themes/group-a/assets/css/theme.css`) are simply added.
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

**Gotcha:** `site/assets/css/custom.css` sets some rules (notably the header
gradient and header link colours) with `!important`. If you layer an extra
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

Work on a branch, keep everything inside `themes/<your-group>/`, and open a
pull request. Check that `./scripts/ui build <your-group>` completes without
errors before submitting.
