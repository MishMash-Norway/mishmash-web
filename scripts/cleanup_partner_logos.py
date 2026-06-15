#!/usr/bin/env python3
"""Normalize partner logo filenames: remove duplicates and use web-safe names."""

from __future__ import annotations

import argparse
import hashlib
import re
import unicodedata
from pathlib import Path

from repo_paths import SITE_ROOT

PARTNERS_DIR = SITE_ROOT / "assets" / "images" / "logos" / "partners"

EXT_RANK = {
    ".svg": 0,
    ".webp": 1,
    ".avif": 2,
    ".png": 3,
    ".jpg": 4,
    ".jpeg": 4,
    ".ico": 5,
}

JUNK_EXTENSIONS = {".docx", ".doc", ".tmp"}

# Inferior alternates when a better file for the same organisation already exists.
REMOVE_NAMES = {
  # exact / case duplicates (inferior copy)
  "Gramo.svg",
  "teks.jpg",
  "borealisfestival.ico",
  "innlandetfylke.ico",
  "nmh.ico",
  "storyphone.ico",
  "nmh.svg",  # favicon-sized duplicate of nmh.ico; NMH.svg is the real logo
  "OsloMet.svg",  # oversized auto-download
  "Storyphone.png",
  "Polyfon.jpg",
  "akks.png",  # large banner; AKKS.png is the logo
  "kulturskoleradet.png",  # duplicate fetch; keep Kulturskolerådet.png
  # junk
  "LES - logoer.docx",
  # .ico when a vector/raster logo exists
  "akks.ico",
  "ateliernord.ico",
  "borealisfestival.ico",
  "fyndreality.com.ico",
  "gramart.ico",
  "helseinn.ico",
  "hvl.ico",
  "innlandetfylke.ico",
  "jmn.ico",
  "kristiania.ico",
  "kunstkultursenteret.ico",
  "nasjonalmuseet.ico",
  "nb.ico",
  "nmh.ico",
  "nord.ico",
  "norsus.ico",
  "notam.ico",
  "nrk.ico",
  "ntnu.edu.ico",
  "oslomet.ico",
  "sintef.ico",
  "storyphone.ico",
  "teks.ico",
  "uib.ico",
  "uio.ico",
  "uit.ico",
  # inferior format / duplicate fetch for same org
  "BEK.jpg",
  "sintef.png",
  "ntnu.edu.svg",
  "nilu.com.png",
  "sareptastudio.com.png",
  "bi.edu.svg",
  "cultiva.png",
  "Australian National University.png",
  "nla.svg",
  "nrk.jpg",
  "nb.svg",
  "kunstkultursenteret.jpg",
  "simulamet.png",  # favicon stub; Simula.png is the logo
}


def web_safe_name(filename: str) -> str:
    stem, ext = Path(filename).stem, Path(filename).suffix
    stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    stem = re.sub(r"[^a-z0-9]+", "-", stem.lower())
    stem = re.sub(r"-+", "-", stem).strip("-")
    return f"{stem}{ext.lower()}"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_exact_duplicates(files: list[Path]) -> set[Path]:
    by_hash: dict[str, list[Path]] = {}
    for path in files:
        by_hash.setdefault(file_hash(path), []).append(path)

    remove: set[Path] = set()
    for group in by_hash.values():
        if len(group) < 2:
            continue
        group = sorted(
            group,
            key=lambda p: (EXT_RANK.get(p.suffix.lower(), 9), p.name.lower()),
        )
        remove.update(group[1:])
    return remove


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean up partner logo filenames.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not PARTNERS_DIR.exists():
        raise SystemExit(f"Missing directory: {PARTNERS_DIR}")

    files = [p for p in PARTNERS_DIR.iterdir() if p.is_file()]
    remove: set[Path] = set()

    for path in files:
        if path.name in REMOVE_NAMES or path.suffix.lower() in JUNK_EXTENSIONS:
            remove.add(path)

    remove.update(collect_exact_duplicates([p for p in files if p not in remove]))

    remaining = [p for p in files if p not in remove]
    rename_map: dict[Path, str] = {}
    used_names: set[str] = set()

    for path in sorted(remaining, key=lambda p: p.name.lower()):
        target = web_safe_name(path.name)
        if target in used_names:
            stem, ext = Path(target).stem, Path(target).suffix
            n = 2
            while f"{stem}-{n}{ext}" in used_names:
                n += 1
            target = f"{stem}-{n}{ext}"
        used_names.add(target)
        if path.name != target:
            rename_map[path] = target

    print(f"Remove: {len(remove)}")
    for path in sorted(remove, key=lambda p: p.name.lower()):
        print(f"  - {path.name}")

    print(f"\nRename: {len(rename_map)}")
    for src, dest in sorted(rename_map.items(), key=lambda item: item[0].name.lower()):
        print(f"  {src.name} -> {dest}")

    print(f"\nFinal count: {len(remaining)} files")

    if args.dry_run:
        return

    for path in remove:
        path.unlink()

    # Two-phase rename to avoid collisions.
    temp_map: dict[Path, Path] = {}
    for i, (src, dest) in enumerate(rename_map.items()):
        temp = PARTNERS_DIR / f".__rename_{i}{src.suffix.lower()}"
        src.rename(temp)
        temp_map[temp] = PARTNERS_DIR / dest

    for temp, final in temp_map.items():
        final.parent.mkdir(parents=True, exist_ok=True)
        temp.rename(final)

    print("Done.")


if __name__ == "__main__":
    main()
