#!/usr/bin/env python3
"""Cut the web fonts down to the characters the built site actually uses (issue #67).

The fonts under site/assets/fonts/ are the Google subsets of Inter, Raleway and
Roboto Condensed, split into latin and latin-ext by the unicode-range rules in
site/assets/css/fonts.css. Those files carry thousands of glyphs; the built site
uses a couple of hundred characters. This script reads the characters out of the
built HTML, the search index and the open data, adds a safety set that covers
Norwegian, Sami and Kven letters plus common punctuation, and rewrites the font
files inside _site with only those glyphs. The sources in site/ are never
touched, and the CSS needs no change: a browser still picks a file by its
declared unicode-range, and a character missing from the subset falls back to a
system font, as it already does for anything outside the two ranges.

Run after `jekyll build` and before the page-weight measurement.

Usage:
  python3 scripts/subset_fonts.py [--site _site] [--dry-run]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import REPO_ROOT

SCRIPT_OR_STYLE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.S | re.I)
TAG = re.compile(r"<[^>]+>")

# Characters that may arrive after the build: names typed into the directory,
# text fetched by the lab pages, interface strings in another language. The
# Sami and Kven letters are here because the centre may publish them before any
# page contains them (issue #71).
SAFETY = set(
    "".join(chr(c) for c in range(0x20, 0x7F))
    + "".join(chr(c) for c in range(0xA0, 0x100))
    + "æøåÆØÅäöÄÖüÜßéèêëáàâçñóòôúùûíìî"
    + "áčđŋšŧžÁČĐŊŠŦŽǤǥǦǧǨǩȞȟ"          # North, Lule and South Sami
    + "‐‑–—‘’‚“”„†‡•…‰′″‹›€№™←↑→↓−×÷≈≤≥"
)


def text_of_html(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    return html.unescape(TAG.sub(" ", SCRIPT_OR_STYLE.sub(" ", raw)))


def used_characters(site_dir: Path) -> set[str]:
    """Every character that can end up on screen, from the built output."""
    chars: set[str] = set(SAFETY)
    for path in sorted(site_dir.rglob("*.html")):
        chars.update(text_of_html(path))
    for path in sorted(site_dir.rglob("*.json")):
        if path.stat().st_size > 20_000_000:
            continue
        try:
            chars.update(json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False))
        except (ValueError, OSError):
            continue
    chars.discard("\n")
    chars.discard("\r")
    chars.discard("\t")
    return chars


def subset_file(src: Path, dst: Path, chars: set[str]) -> tuple[int, int]:
    """Write src to dst keeping only chars. Returns (bytes before, bytes after)."""
    from fontTools import subset

    before = src.stat().st_size
    options = subset.Options()
    options.flavor = "woff2"
    options.desubroutinize = True
    options.layout_features = ["ccmp", "liga", "locl", "kern", "mark", "mkmk"]
    options.drop_tables += ["DSIG"]
    options.notdef_outline = True
    font = subset.load_font(str(src), options)
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(unicodes=[ord(c) for c in chars])
    subsetter.subset(font)
    subset.save_font(font, str(dst), options)
    font.close()
    return before, dst.stat().st_size


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default=str(REPO_ROOT / "_site"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    site_dir = Path(args.site)
    fonts_dir = site_dir / "assets" / "fonts"
    if not fonts_dir.is_dir():
        print(f"subset_fonts: no fonts in {fonts_dir}; build the site first", file=sys.stderr)
        return 1

    chars = used_characters(site_dir)
    files = sorted(fonts_dir.glob("*.woff2"))
    print(f"subset_fonts: {len(chars)} characters in the built site, {len(files)} font files")
    if args.dry_run:
        return 0

    total_before = total_after = 0
    for src in files:
        tmp = src.with_suffix(".woff2.tmp")
        try:
            before, after = subset_file(src, tmp, chars)
        except Exception as exc:  # a font that cannot be subset is left as it was
            print(f"  {src.name}: left unchanged ({exc})", file=sys.stderr)
            tmp.unlink(missing_ok=True)
            continue
        tmp.replace(src)
        total_before += before
        total_after += after
        print(f"  {src.name}: {before // 1024} kB to {after // 1024} kB")
    if total_before:
        saved = 100 * (total_before - total_after) / total_before
        print(f"subset_fonts: {total_before // 1024} kB to {total_after // 1024} kB, {saved:.0f}% smaller")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
