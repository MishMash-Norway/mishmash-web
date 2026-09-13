# UI theme: identity

A preview of the 2026 MishMash visual identity (wordmark, colours and type
delivered by the design agency in August 2026) applied to the whole site. It
is published at <https://mishmash.no/ui/identity/> so the consortium can look
at it before deciding whether to switch the main site over. Nothing here
changes the regular site.

Run it locally:

```bash
./scripts/ui serve identity
```

## Design

- **Wordmark.** The stacked MISH/MASH mark sits in the header on every page.
  `_includes/mm-wordmark.svg` is an inline version of the delivered SVG in
  which the I/A, S and H columns are vertical strips of repeated glyphs behind
  a clip, so they can roll like a split-flap board. It rolls once on load and
  again when the pointer enters it; users who prefer reduced motion see the
  static mark. `assets/images/logo/mishmash-wordmark-animated.svg` is the
  same animation as a standalone file that loops (usable as an `<img>`).
- **One surface per section.** The header is flat green on the front page and
  general pages, purple on work-package pages, blue on news and events, pink
  on the directory (people, institutions, projects, results). The wordmark
  takes the colour paired with that surface: black, green, yellow, red.
- **Type.** Headings, tagline and navigation use Roboto Condensed 700
  (self-hosted, open licence) as the web stand-in for the identity's Acumin
  Condensed Bold. Body text stays Inter.
- **Bubbles.** The old bubble illustrations stay as thumbnails for news and
  events and as the person/event fallback image, recoloured to the new
  palette (`assets/images/bubbles/`). The front page no longer shows them; the
  wordmark is the hero there.
- **Brand page.** `/about/brand/` (and `/no/about/brand/`) shows the rules,
  the palette and the downloadable files. `BRAND.md` in the repository root
  is the same guide written for developers and automated tools.

## Files

| Path | Purpose |
| --- | --- |
| `_layouts/default.html` | Header with wordmark, tagline, section colour, favicon and social image |
| `_includes/mm-wordmark.svg` | Inline animated wordmark (generated) |
| `assets/css/brand.css` | Design tokens only: colours, pairings, tints, fonts |
| `assets/css/theme.css` | The restyle, built entirely from the tokens |
| `assets/css/wordmark-animation.css` | Keyframes for the inline wordmark (generated) |
| `assets/css/fonts-display.css` | `@font-face` for the self-hosted Roboto Condensed |
| `assets/fonts/` | Roboto Condensed 700 woff2, latin and latin-ext |
| `assets/images/logo/` | Delivered wordmarks, animated SVG, colourway tiles, favicon, social image |
| `assets/images/bubbles/` | Recoloured copies of the bubble files the site uses for news, events and people |
| `about/brand/`, `no/about/brand/` | The public brand page in English and Norwegian |

The generated files (inline wordmark, keyframes, tiles, favicon, social image)
come from `scripts/build_identity_logo.py`, which reads the delivered SVG. Run
it only if the wordmark itself changes (needs Inkscape and ImageMagick). The
letter geometry it relies on: viewBox 347.29 × 243.91, vertical pitch between
repeated S and H glyphs 129.66 units, I→A step 127.10 and A→I step 132.22.

## Switching the main site to this identity

If the consortium adopts the theme, the move is: copy `assets/` and
`_includes/mm-wordmark.svg` into `site/`, merge `_layouts/default.html` into
`site/_layouts/default.html`, replace the bubble files under
`site/assets/images/bubbles/` with the recoloured ones, fold `theme.css` into
`custom.css` (replacing the old purple/green values with the tokens), move the
brand pages, and update `logo:` in `_config.yml`.
