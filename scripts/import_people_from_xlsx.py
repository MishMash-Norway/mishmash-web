#!/usr/bin/env python3
"""Import MishMash people data from XLSX files.

The importer auto-detects two sheet layouts:

- intake sheets with an include column only import rows marked for inclusion
- existing-member sheets update matching directory entries with URL fields

Place an XLSX in temp/ or pass --xlsx explicitly.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from import_people_xlsx_common import import_people, read_people


DEFAULT_XLSX = None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xlsx", type=Path, default=DEFAULT_XLSX, help="XLSX file to import. Defaults to the newest XLSX in temp/.")
    parser.add_argument("--template", type=Path, default=None, help="Directory template to copy for each imported person")
    parser.add_argument("--out-base", type=Path, default=None, help="Output directory for people entries")
    return parser.parse_args(argv)


def resolve_xlsx_path(path: Path | None) -> Path | None:
    if path is not None:
        return path
    temp_dir = Path("temp")
    xlsx_files = sorted(temp_dir.glob("*.xlsx"), key=lambda candidate: candidate.stat().st_mtime, reverse=True)
    if xlsx_files:
        return xlsx_files[0]
    return None


def main(argv=None):
    args = parse_args(argv)
    xlsx = resolve_xlsx_path(args.xlsx)
    if xlsx is None:
        print("No XLSX files found in temp/", file=sys.stderr)
        return 2
    if not xlsx.exists():
        print(f"XLSX not found: {xlsx}", file=sys.stderr)
        return 2

    people, sheet_kind = read_people(xlsx)
    if not people:
        print("No people found in XLSX")
        return 0

    repo_root = Path(__file__).resolve().parents[1]
    template = args.template or (repo_root / "site" / "_directory" / "people" / "_template" / "index.md")
    if not template.exists():
        print(f"Template not found: {template}", file=sys.stderr)
        return 3

    out_base = args.out_base or (repo_root / "site" / "_directory" / "people")
    created, updated, skipped_missing = import_people(people, template, out_base)

    print(f"Done. Created: {created}, updated: {updated}, missing existing entries skipped: {skipped_missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
