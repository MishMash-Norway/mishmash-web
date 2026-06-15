#!/usr/bin/env python3
"""Compress large portrait images in assets/images/portraits."""

from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path

from PIL import Image

from repo_paths import SITE_ROOT

PORTRAITS_DIR = SITE_ROOT / "assets" / "images" / "portraits"
DEFAULT_MAX_BYTES = 500_000
DEFAULT_MAX_DIMENSION = 1200
DEFAULT_JPEG_QUALITY = 85


def compress_image(path: Path, max_bytes: int, max_dimension: int, quality: int) -> bool:
    original_size = path.stat().st_size
    if original_size <= max_bytes:
        return False

    with Image.open(path) as opened:
        image = opened.convert("RGB")
        width, height = image.size
        longest = max(width, height)
        if longest > max_dimension:
            scale = max_dimension / longest
            image = image.resize(
                (max(1, int(width * scale)), max(1, int(height * scale))),
                Image.Resampling.LANCZOS,
            )

        if path.suffix.lower() in {".jpg", ".jpeg"}:
            image.save(path, format="JPEG", quality=quality, optimize=True, progressive=True)
            if path.stat().st_size <= max_bytes:
                return True

        buffer = BytesIO()
        current_quality = quality
        while current_quality >= 60:
            buffer.seek(0)
            buffer.truncate(0)
            image.save(buffer, format="JPEG", quality=current_quality, optimize=True, progressive=True)
            if buffer.tell() <= max_bytes:
                path.write_bytes(buffer.getvalue())
                return True
            current_quality -= 5

        path.write_bytes(buffer.getvalue())
        return True


def main():
    parser = argparse.ArgumentParser(description="Compress large portrait images.")
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument("--max-dimension", type=int, default=DEFAULT_MAX_DIMENSION)
    parser.add_argument("--quality", type=int, default=DEFAULT_JPEG_QUALITY)
    args = parser.parse_args()

    if not PORTRAITS_DIR.exists():
        raise SystemExit(f"Missing portraits directory: {PORTRAITS_DIR}")

    compressed = 0
    for path in sorted(PORTRAITS_DIR.iterdir()):
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        before = path.stat().st_size
        if before <= args.max_bytes:
            continue
        if compress_image(path, args.max_bytes, args.max_dimension, args.quality):
            after = path.stat().st_size
            print(f"{path.name}: {before // 1024} KB -> {after // 1024} KB")
            compressed += 1

    print(f"Compressed {compressed} portrait(s).")


if __name__ == "__main__":
    main()
