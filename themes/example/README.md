# UI theme: example

A minimal demonstration theme showing the two basic moves:

- `_layouts/default.html` — a copy of the site's main layout with two changes:
  it links an extra stylesheet and adds a badge showing which theme is active.
- `assets/css/example-theme.css` — a new file layered on top of the regular
  site CSS (different header colours, fonts, rounded buttons).

Run it with:

```bash
./scripts/ui serve example
```

Full guide: [themes/README.md](../README.md).
