#!/usr/bin/env python3
"""Assign Work Package (WP) tags to directory people from sympa mailing list dumps.

Reads sympa member-list exports named `wp{N}@mishmash.no.txt` (one member per
line, tab-separated `email<TAB>Name`) and adds the matching `WPN` tag to each
matched person's `wps` front matter list in site/_directory/people.

Matching order per entry: normalised full-name match, slugified-name folder
match, then slugified email local-part folder match. Entries that cannot be
matched are left untouched and reported so they can be followed up manually
(e.g. contacted to fill in the directory survey).

Usage:
  python3 scripts/assign_wps_from_mailing_lists.py --dumps-dir temp --dry-run
  python3 scripts/assign_wps_from_mailing_lists.py --dumps-dir temp
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

from directory_io import load_entry, save_entry
from import_directory_survey_csv import merge_wps, slugify
from repo_paths import SITE_ROOT

PEOPLE_ROOT = SITE_ROOT / "_directory" / "people"
DUMP_NAME_RE = re.compile(r"^wp([1-7])@mishmash\.no\.txt$", re.IGNORECASE)


def normalized_name_key(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name or "")
    ascii_name = "".join(ch for ch in ascii_name if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", ascii_name.casefold()).strip()


def build_name_index(people_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for index_md in people_root.glob("*/index.md"):
        if index_md.parent.name == "_template":
            continue
        data, _ = load_entry(index_md)
        key = normalized_name_key(str(data.get("name") or ""))
        if key:
            index[key] = index_md
    return index


def find_match(name: str, email: str, people_root: Path, name_index: dict[str, Path]) -> Path | None:
    key = normalized_name_key(name)
    if key and key in name_index:
        return name_index[key]

    slug = slugify(name)
    if slug and (people_root / slug / "index.md").exists():
        return people_root / slug / "index.md"

    email = (email or "").strip().lower()
    if "@" in email:
        local = email.split("@", 1)[0]
        local_slug = slugify(local.replace(".", " ").replace("_", " "))
        if local_slug and (people_root / local_slug / "index.md").exists():
            return people_root / local_slug / "index.md"
    return None


def parse_dump(path: Path) -> list[tuple[str, str]]:
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        email = parts[0].strip()
        name = parts[1].strip() if len(parts) > 1 else ""
        entries.append((email, name))
    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dumps-dir", default="temp", help="Directory containing wp{N}@mishmash.no.txt dumps")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files")
    args = parser.parse_args()

    dumps_dir = Path(args.dumps_dir)
    dump_paths = sorted(p for p in dumps_dir.glob("wp*@mishmash.no.txt") if DUMP_NAME_RE.match(p.name))
    if not dump_paths:
        raise SystemExit(f"No wp{{N}}@mishmash.no.txt dumps found in {dumps_dir}")

    name_index = build_name_index(PEOPLE_ROOT)
    unmatched: dict[str, list[tuple[str, str]]] = {}
    updated = 0

    for dump_path in dump_paths:
        wp_label = f"WP{DUMP_NAME_RE.match(dump_path.name).group(1)}"
        for email, name in parse_dump(dump_path):
            match = find_match(name, email, PEOPLE_ROOT, name_index) if name else None
            if not match and email:
                match = find_match(email.split("@", 1)[0], email, PEOPLE_ROOT, name_index)
            if match:
                data, body = load_entry(match)
                wps = merge_wps(data.get("wps"), [wp_label])
                if wps != (data.get("wps") or []):
                    if not args.dry_run:
                        data["wps"] = wps
                        save_entry(match, data, body)
                    updated += 1
                    print(f"{match.parent.name}: +{wp_label}")
            else:
                unmatched.setdefault(wp_label, []).append((email, name))

    verb = "Would update" if args.dry_run else "Updated"
    print(f"\n{verb} {updated} person entries with new WP tags.\n")
    print("=== Unmatched mailing list entries (not found in directory) ===")
    for wp_label in sorted(unmatched, key=lambda w: int(w[2:])):
        entries = unmatched[wp_label]
        print(f"\n{wp_label}: {len(entries)} unmatched")
        for email, name in entries:
            print(f"  {name or '(no name)'} <{email}>")


if __name__ == "__main__":
    main()
