# UI theme: artsy

A warm exhibition-catalogue UI: cream paper with a subtle grain, Playfair
Display serif in italic, and a terracotta/plum/ochre palette. Its signature
is a hand-painted ochre stroke — under the site title, behind every h2, and
as dividers — joined by drop caps, a slowly drifting painterly header, and
photos hung like tilted, matted canvases that straighten on hover.

- `_layouts/default.html` — copy of the site layout with the nav's inline
  styles removed (so the dropdowns can be themed), a swapped Google Fonts
  link, and the theme stylesheet + badge added.
- `assets/css/artsy-theme.css` — the editorial styling, layered on top of
  the regular site CSS.

Run it with:

```bash
./scripts/ui serve artsy
```

Full guide: [themes/README.md](../README.md).
