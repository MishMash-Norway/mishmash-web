#!/usr/bin/env python3
"""Write AVIF variants beside the large photographs (issue #67).

For every JPEG or PNG under the news and events image folders above a size
threshold, an .avif file is written next to it when missing or older than the
source. The photo galleries serve the AVIF to browsers that accept it and the
original to the rest. The .avif files are ignored by git and built at deploy.

Usage:
  python3 scripts/build_avif.py [--min-kb 120]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps, features

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

FOLDERS = ["news", "events", "illustrations"]
EXTS = {".jpg", ".jpeg", ".png"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-kb", type=int, default=120)
    args = ap.parse_args()
    if not features.check("avif"):
        print("avif: this Pillow has no AVIF support; nothing written", file=sys.stderr)
        return 0
    built = skipped = 0
    for folder in FOLDERS:
        for src in sorted((SITE_ROOT / "assets" / "images" / folder).rglob("*")):
            if not src.is_file() or src.suffix.lower() not in EXTS or src.stat().st_size < args.min_kb * 1024:
                continue
            dst = src.with_suffix(src.suffix + ".avif")
            if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
                skipped += 1
                continue
            try:
                with Image.open(src) as im:
                    im = ImageOps.exif_transpose(im)
                    if im.mode not in ("RGB", "RGBA"):
                        im = im.convert("RGB")
                    im.save(dst, "AVIF", quality=55, speed=6)
                built += 1
            except Exception as exc:
                print(f"avif: skip {src.name}: {exc}", file=sys.stderr)
    print(f"avif: {built} written, {skipped} up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
