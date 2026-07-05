# UI theme: techy

A dark, terminal-inspired UI with a page-wide two-column layout: a sticky
sidebar on the left (the `$`-prompt title with a blinking cursor and the
nav as `~/` directories that expand in place), and content filling the
rest of the viewport. Monospace type (JetBrains Mono), near-black panels,
neon green/cyan accents. Collapses to a single column on small screens.

- `_layouts/default.html` — copy of the site layout with the nav's inline
  styles removed (so the dropdowns can be themed), a swapped Google Fonts
  link, and the theme stylesheet + badge added.
- `assets/css/techy-theme.css` — the dark styling, layered on top of the
  regular site CSS.

Run it with:

```bash
./scripts/ui serve techy
```

Full guide: [themes/README.md](../README.md).
