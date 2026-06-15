#!/usr/bin/env python3
"""Copy partner logos into site/images/institutions/ and update institution front matter."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from directory_io import load_entry, save_entry
from repo_paths import SITE_ROOT

PARTNERS_DIR = SITE_ROOT / "assets" / "images" / "logos" / "partners"
INSTITUTION_IMAGES_DIR = SITE_ROOT / "images" / "institutions"

# Institution slug -> partner logo filename in assets/images/logos/partners/
INSTITUTION_LOGO_SOURCES: dict[str, str] = {
    "arctic-university-of-norway": "uit.png",
    "australian-national-university": "australian-national-university.svg",
    "barratt-due-institute-of-music": "barratt-due.svg",
    "bergen-center-for-electronic-arts": "bek.png",
    "bi-norwegian-business-school": "bi.svg",
    "inland-norway-university-of-applied-sciences": "inn.png",
    "kristiania-university-college": "kristiania.svg",
    "kulturtanken": "kulturtanken.png",
    "motioncomposer-gmbh": "motioncomposer.png",
    "national-library-of-norway": "nasjonalbiblioteket.png",
    "nla-university-college": "nla.png",
    "nord-university": "nord.png",
    "norsus-norwegian-institute-for-sustainability-research": "norsus.png",
    "norwegian-academy-of-music": "nmh.svg",
    "norwegian-university-of-science-and-technology": "ntnu.png",
    "notam-norwegian-centre-for-technology-art-and-music": "notam.png",
    "oslo-national-academy-of-the-arts": "khio.png",
    "oslo-school-of-architecture-and-design": "aho.png",
    "ostfold-university-college": "hiof.png",
    "reimagine": "reimagine.png",
    "screenstory": "screenstory.png",
    "simula-metropolitan-center-for-digital-engineering": "simula.png",
    "sintef-digital": "sintef.svg",
    "super-ponni": "super-ponni.svg",
    "ultima-festival": "ultima.svg",
    "uniarts-helsinki": "uniarts-helsinki.svg",
    "university-of-agder": "uia.svg",
    "university-of-bergen": "uib.png",
    "university-of-cambridge": "university-of-cambridge.svg",
    "university-of-iceland": "university-of-iceland.svg",
    "university-of-manchester": "university-of-manchester.png",
    "university-of-melbourne": "university-of-melbourne.svg",
    "university-of-oslo": "uio.svg",
    "university-of-stavanger": "uis.png",
    "western-norway-university-of-applied-sciences": "hvl.svg",
}


def update_image_field(data: dict, image_path: str) -> None:
    data["image"] = image_path


def remove_image_field(data: dict) -> None:
    data.pop("image", None)


def main():
    parser = argparse.ArgumentParser(description="Link partner logos to institution directory entries.")
    parser.add_argument("--root", default=str(SITE_ROOT), help="Jekyll site source directory")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    partners_dir = root / "assets" / "images" / "logos" / "partners"
    images_dir = root / "images" / "institutions"
    institutions_dir = root / "_directory" / "institutions"

    if not partners_dir.exists():
        raise SystemExit(f"Missing partner logos directory: {partners_dir}")

    if not args.dry_run:
        images_dir.mkdir(parents=True, exist_ok=True)

    linked = 0
    missing = []
    skipped = []

    for slug, source_name in sorted(INSTITUTION_LOGO_SOURCES.items()):
        source = partners_dir / source_name
        index_md = institutions_dir / slug / "index.md"
        if not index_md.exists():
            missing.append(f"{slug}: institution entry not found")
            continue
        if not source.exists():
            missing.append(f"{slug}: partner logo not found ({source_name})")
            continue

        ext = source.suffix.lower()
        dest = images_dir / f"{slug}{ext}"
        image_path = f"/images/institutions/{slug}{ext}"

        data, body = load_entry(index_md)
        if not args.dry_run:
            shutil.copy2(source, dest)
            update_image_field(data, image_path)
            save_entry(index_md, data, body)
        linked += 1
        print(f"{'would link' if args.dry_run else 'linked'} {slug} <- {source_name}")

    for child in sorted(institutions_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("_"):
            continue
        slug = child.name
        if slug in INSTITUTION_LOGO_SOURCES:
            continue
        index_md = child / "index.md"
        if not index_md.exists():
            continue
        data, body = load_entry(index_md)
        if "image" not in data:
            continue
        if not args.dry_run:
            remove_image_field(data)
            save_entry(index_md, data, body)
        skipped.append(slug)
        print(f"{'would remove' if args.dry_run else 'removed'} image field for {slug} (no partner logo mapped)")

    print(f"\nLinked: {linked}")
    if skipped:
        print(f"Without mapped logo: {len(skipped)}")
    if missing:
        print("Missing:")
        for item in missing:
            print(f"  - {item}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
