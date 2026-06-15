#!/usr/bin/env python3
"""Set urls.website on institution entries from DEFAULT_INSTITUTION_WEBSITES."""

from __future__ import annotations

import argparse
from pathlib import Path

from directory_io import load_entry, save_entry
from institution_short_names import DEFAULT_INSTITUTION_WEBSITES
from repo_paths import SITE_ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync institution website URLs into front matter.")
    parser.add_argument("--root", default=str(SITE_ROOT), help="Jekyll site source directory")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    institutions_dir = Path(args.root).resolve() / "_directory" / "institutions"
    updated = 0

    for slug, website in sorted(DEFAULT_INSTITUTION_WEBSITES.items()):
        index_md = institutions_dir / slug / "index.md"
        if not index_md.exists():
            print(f"missing entry: {slug}")
            continue

        data, body = load_entry(index_md)
        urls = data.setdefault("urls", {})
        current = urls.get("website")
        if current == website:
            continue
        if current and current not in ("", "null", None):
            print(f"skip {slug}: already has {current}")
            continue

        urls["website"] = website
        if not args.dry_run:
            save_entry(index_md, data, body)
        print(f"{'would set' if args.dry_run else 'set'} {slug} -> {website}")
        updated += 1

    print(f"\nUpdated: {updated}")


if __name__ == "__main__":
    main()
