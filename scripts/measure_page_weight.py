#!/usr/bin/env python3
"""Page weight and a carbon estimate for a set of pages, measured on the built site (issue #67).

For each page the script sums the bytes a first visit transfers: the HTML and
every local stylesheet, script, image and preloaded font the page links, text
assets counted gzip-compressed as the server sends them. Fonts that a browser
discovers inside a stylesheet are not counted, since which of them it fetches
depends on the characters on the page; `scripts/subset_fonts.py` keeps them
small. The carbon figure
uses the Sustainable Web Design model as implemented in CO2.js (version 3):
0.81 kWh per GB transferred, at 442 g CO2 per kWh, for a first visit. It is an
estimate for comparison between builds, not a measurement of any reader's
device or network.

Runs after jekyll build and writes _site/data/page-weight.json, which the AI
colophon shows.

Usage:
  python3 scripts/measure_page_weight.py [--site _site]
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import re
import sys
from pathlib import Path

PAGES = ["/", "/about/description/", "/results/", "/events/", "/news/opening-conference/", "/people/alexander-refsum-jensenius/", "/lab/heritage/", "/no/"]
TEXT = {".html", ".css", ".js", ".json", ".svg", ".txt", ".xml"}
KWH_PER_GB = 0.81
G_CO2_PER_KWH = 442
ASSET_RE = re.compile(r'(?:src|href|srcset)="(/[^"#?]+\.(?:css|js|woff2?|png|jpe?g|webp|avif|svg|ico|gif|json))(?:\?[^"]*)?"', re.I)


def transfer_bytes(path: Path) -> int:
    data = path.read_bytes()
    return len(gzip.compress(data, 6)) if path.suffix.lower() in TEXT else len(data)


def weigh(site: Path, page: str) -> dict:
    html = site / page.strip("/") / "index.html" if page != "/" else site / "index.html"
    text = html.read_text(encoding="utf-8", errors="ignore")
    assets: dict[str, int] = {}
    for m in ASSET_RE.finditer(text):
        rel = m.group(1)
        f = site / rel.lstrip("/")
        if f.is_file() and rel not in assets:
            assets[rel] = transfer_bytes(f)
    # A browser that takes AVIF fetches only the AVIF of a <picture>, not the JPEG fallback.
    for rel in [r for r in assets if r.endswith(".avif")]:
        assets.pop(rel[: -len(".avif")], None)
    html_bytes = transfer_bytes(html)
    total = html_bytes + sum(assets.values())
    by_kind: dict[str, int] = {}
    for rel, n in assets.items():
        kind = rel.rsplit(".", 1)[-1].lower()
        kind = {"jpg": "images", "jpeg": "images", "png": "images", "webp": "images", "avif": "images", "svg": "images", "gif": "images", "ico": "images",
                "woff": "fonts", "woff2": "fonts", "css": "styles", "js": "scripts", "json": "data"}.get(kind, kind)
        by_kind[kind] = by_kind.get(kind, 0) + n
    return {"page": page, "bytes": total, "html_bytes": html_bytes, "by_kind": by_kind, "requests": 1 + len(assets),
            "g_co2_first_visit": round(total / 1e9 * KWH_PER_GB * G_CO2_PER_KWH, 4)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", type=Path, default=Path(__file__).resolve().parents[1] / "_site")
    args = ap.parse_args()
    rows = [weigh(args.site, p) for p in PAGES if ((args.site / p.strip("/") / "index.html").exists() or p == "/")]
    out = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": "Sustainable Web Design model v3 (CO2.js): 0.81 kWh/GB, 442 g CO2/kWh, first visit; text assets counted gzip-compressed; counts the HTML and the assets the page links, including preloaded fonts, not fonts a browser finds inside a stylesheet",
        "pages": rows,
        "median_bytes": sorted(r["bytes"] for r in rows)[len(rows) // 2] if rows else 0,
    }
    (args.site / "data").mkdir(exist_ok=True)
    (args.site / "data" / "page-weight.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for r in rows:
        print(f"{r['page']:45s} {r['bytes']/1024:7.0f} KB  {r['requests']:3d} requests  {r['g_co2_first_visit']:.3f} g CO2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
