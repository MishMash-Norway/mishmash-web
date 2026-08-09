# UI theme: sfa

Files in this folder replace files in `site/` at the same relative path.

`sfa` adds a light Game of Life animated background using p5.js and styles
the page with high-contrast translucent content panels for readability.
It also includes an experimental WebAudio granular engine controlled by
Game of Life metrics and Freesound preview samples.

Main files:

- `_layouts/default.html` loads the theme CSS, p5.js, and the sketch script.
- `assets/css/theme.css` defines the visual language and content layering.
- `assets/js/sfa-gol.js` implements the Game of Life animation.
- `assets/js/sfa-sonic.js` handles sound toggle, Freesound loading, and audio synthesis.

Full guide: [themes/README.md](../README.md).

Run it with:

```bash
./scripts/ui serve sfa
```
