#!/usr/bin/env python3
"""Build square WebP thumbnails for the images used in listings.

Listings (front page, /news/, /events/) show a 120 px square thumbnail, but
until now they loaded the full photograph or portrait for it. This script
writes a 240 px square WebP for every image under the news, events and
portraits folders into site/assets/images/thumbs/, named after the source
path with slashes replaced by "__". The pick-thumb include uses the
thumbnail when it exists and the original otherwise, so the script may run
at any time (it runs nightly in CI) and a missing thumbnail is never an
error. Re-running only rebuilds thumbnails whose source is newer.

Usage:
  python3 scripts/build_thumbnails.py [--force]
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

from repo_paths import SITE_ROOT

IMAGES = SITE_ROOT / "assets" / "images"
SOURCES = ["news", "events", "portraits"]
OUT = IMAGES / "thumbs"
SIZE = 240
EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def thumb_name(src: Path) -> str:
    rel = src.relative_to(IMAGES)
    return "__".join(rel.parts) + ".webp"


def build(src: Path, dst: Path) -> None:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode not in ("RGB", "RGBA"):
            im = im.convert("RGBA" if "transparency" in im.info else "RGB")
        im = ImageOps.fit(im, (SIZE, SIZE), method=Image.LANCZOS)
        im.save(dst, "WEBP", quality=80, method=6)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="rebuild every thumbnail")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    built = skipped = 0
    wanted = set()
    for folder in SOURCES:
        for src in sorted((IMAGES / folder).rglob("*")):
            if not src.is_file() or src.suffix.lower() not in EXTS or "thumbs" in src.parts:
                continue
            dst = OUT / thumb_name(src)
            wanted.add(dst.name)
            if not args.force and dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
                skipped += 1
                continue
            try:
                build(src, dst)
                built += 1
            except Exception as exc:  # a broken image must not stop the run
                print(f"skip {src.relative_to(SITE_ROOT)}: {exc}", file=sys.stderr)
    removed = 0
    for old in OUT.glob("*.webp"):
        if old.name not in wanted:
            old.unlink()
            removed += 1
    print(f"thumbnails: {built} built, {skipped} up to date, {removed} removed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
