# MishMash visual identity: guide for developers and automated tools

This is the reference for anyone (person or agent) styling something for
MishMash: the website, a slide deck, a poster, a generated image. It records
the identity designed by the design agency and used on mishmash.no. The
public version of this page is <https://mishmash.no/internal/brand/>. The
`bubbles` UI theme (`themes/bubbles/`, <https://mishmash.no/ui/bubbles/>) is
an alternative look.

Machine-readable tokens: `site/assets/css/brand.css`. Use the custom
properties from that file instead of hard-coding values. The styling built
from them is `site/assets/css/identity.css`; site-wide components are in
`site/assets/css/custom.css`.

## Wordmark

The logo is a wordmark: MISH stacked over MASH in a condensed bold face, with
the S and H columns cut off top and bottom as if rolling through a window.
Files (all in `site/assets/images/logo/`):

| File | Use |
| --- | --- |
| `mishmash-wordmark-black.svg` / `.png` | The mark on white or light backgrounds |
| `mishmash-wordmark-white.svg` / `.png` | The mark on dark backgrounds or photographs |
| `mishmash-wordmark-animated.svg` | Looping split-flap animation; works as an `<img>`; static under reduced motion |
| `mishmash-tile-{green,purple,blue,pink}.svg` / `.png` | The mark on each surface colour, square |
| `mishmash-og.png` | 1200 × 630 social media image |
| `favicon.svg`, `favicon.ico`, `apple-touch-icon.png`, `icon-512.png` | Icons |

Rules: use the files as delivered. Do not retype the name in a font, stretch,
outline, rotate, add shadows or gradients, or change the letter offsets. Clear
space around the mark is at least a quarter of the M's height. Minimum size is
24 px tall on screen, 8 mm in print. The SVG paths are outlines, so no font is
needed to display the mark.

## Colours

| Token | Hex | Role |
| --- | --- | --- |
| `--mm-green` | `#b3e297` | Surface. Default for the front page and general pages |
| `--mm-purple` | `#9a90cf` | Surface for decoration only: the wordmark, artwork, the event badge's rule. No section and no text |
| `--mm-blue` | `#a5cbed` | Surface. News, events and work packages |
| `--mm-pink` | `#efadb2` | Surface. Directory: people, institutions, projects, results |
| `--mm-ink` | `#231f20` | Text, the wordmark on green, rules, outlines |
| `--mm-yellow` | `#d1e422` | Accent. The wordmark on blue; small highlights |
| `--mm-red` | `#ee5648` | Accent. The wordmark on pink; small highlights |
| `--mm-white` | `#ffffff` | Page background; the wordmark on dark photos |
| `--mm-purple-text`, `--mm-purple-dark` | `#594aab` | The purple for text on white, and the purple surface that carries white text; 7.02:1 either way |
| `--mm-on-green`, `--mm-on-purple`, `--mm-on-blue`, `--mm-on-pink` | | The wordmark colour paired with each surface |
| `--mm-rule` | | Hairlines |
| `--mm-display-weight`, `--mm-display-leading`, `--mm-display-tracking` | | The display face's settings |

Pairings are fixed. The wordmark is black on green, green on purple, yellow
on blue, red on pink, and black or white on anything else. Never green on
blue, purple on pink, and so on.

Text on any surface colour is ink. Ink reaches 11.05:1 on green, 9.60:1 on
blue and 8.76:1 on pink; on the purple it reaches 5.64:1 and white 2.89:1,
so no text sits on the purple. The pastels do not have enough contrast to
carry text on white, so never use them as a text colour; text that has to be
purple uses `--mm-purple-text`. Use the pastels as backgrounds, underlines or
highlights behind ink text. Text is held to 4.5:1 against whatever is painted
behind it (3:1 when large), measured in the states a page scan cannot reach by
`scripts/check_contrast.mjs`; `scripts/measure_aaa.mjs` reports the distance
to 7:1. Light tints for cards
and callouts (about 15 % colour on white) are in `brand.css` as
`--mm-*-tint`.

Greys are derived from ink: `--mm-ink-70` for secondary text, `--mm-ink-40`
for placeholders, `--mm-ink-15` for hairlines, `--mm-ink-5` for code and
input backgrounds.

`#A7A1F4`, `#C1F7AE` and `#363644` are not part of the identity; replace
them with the tokens above wherever they turn up. The bubble illustrations in
`site/assets/images/bubbles/` use this palette and serve as news and event
thumbnails and as placeholder portraits.

## Type

- **Display** (headings, tagline, navigation, signage): Acumin Variable
  Concept Condensed Bold. Set tight: the identity sheet uses 44 pt on a 33 pt
  line. Acumin is an Adobe font under licence and is used in print and in the
  agency's files.
- **Display on the web**: Roboto Condensed 700, self-hosted from
  `site/assets/fonts/`. The site serves all fonts itself and loads
  nothing from third parties; do not add Adobe Fonts, Google Fonts or any
  other remote font service. Token: `--mm-font-display`.
- **Body**: Inter 400/700, already self-hosted by the site. Token:
  `--mm-font-body`.

Headings are bold, tight (line-height about 0.9), slightly negative tracking,
sentence case. Small labels and navigation may be uppercase with a little
positive tracking.

## Shape and layout

Flat surfaces, hard edges. No gradients, no drop shadows, no rounded corners
(`--mm-radius: 0`). Rules and outlines are 2 px ink. Buttons are ink outlines
on the surface colour, inverting to ink fill with the surface colour as text
on hover. Links in running text are ink with a purple underline; on hover the
purple becomes a highlight behind the text.

The arrow (→) is the secondary motif: it precedes "more" links and is used
large on signage. Token: `--mm-arrow`.

## Icons

Social and contact icons are square tiles in the identity style: green
surface, ink outline, ink glyph, no rounding. The glyphs are Tabler Icons
(MIT) at the same stroke weight as the tile border, so the set reads as one
family; ORCID, Wikidata and NVA are drawn in the same weight. Files:
`site/assets/images/icons/catalogue/` (person pages, front page), built by
`scripts/build_icons.py`. Add an icon by adding a row to that script and
running it; do not hand-draw one-offs.

## Website sections

| Section | Surface | Wordmark colour |
| --- | --- | --- |
| Front page, about, FAQ, search, everything else | green | ink |
| `/news/`, `/events/`, `/wp1/` … `/wp7/` | blue | yellow |
| `/people/`, `/institutions/`, `/projects/`, `/results/` | pink | red |

The section is chosen in `site/_layouts/default.html` and set as a
class on `<body>` (`mm-section-green` etc.), so a stylesheet can respond to it.

## Tagline

English: *Centre for AI and Creativity*. Norwegian: *Senter for KI og
kreativitet*. The site name in running text remains "MishMash Centre for AI
and Creativity" / "MishMash senter for KI og kreativitet".

## Checklist for a new page or asset

1. Surface colour from the section table; text in ink.
2. Wordmark in the paired colour, unaltered, with clear space.
3. Headings in the display face, body in Inter; fonts self-hosted.
4. No gradients, shadows or rounded corners.
5. All three languages, if it is a web page; a new abbreviation or glossary entry carries its English, Bokmål and Nynorsk form.

## How this document has developed

- August 2026: the agency delivered the identity.
- 13 September 2026: mishmash.no adopted it; the earlier bubbles look became the `bubbles` theme, and the bubble illustrations were recoloured from the old palette (`#A7A1F4`, `#C1F7AE`, `#363644`).
- 25 September 2026: the work packages moved from the purple surface to the blue one, since ink on the purple falls short of 7:1; the purple carries no text since.
