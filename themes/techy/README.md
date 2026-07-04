# UI theme: techy

A dark, terminal-inspired UI: monospace type (JetBrains Mono), near-black
panels, neon green/cyan accents, `$`-prompt header with a blinking cursor,
and `>`-prefixed dropdown menus.

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
