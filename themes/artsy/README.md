# UI theme: artsy

A warm, editorial/gallery-inspired UI: cream paper background, Playfair
Display serif headings in italic, terracotta/plum/ochre palette, painterly
gradient header, pill buttons, and offset "print" shadows on images and
dropdowns.

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
