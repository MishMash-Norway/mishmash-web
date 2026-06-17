#!/usr/bin/env python3
"""Merge similar tags across the MishMash site using config/tag_merge_map.yml."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from repo_paths import SITE_ROOT
from tag_merge import (
    DEFAULT_MAP_PATH,
    DEFAULT_TAG_GROUPS_PATH,
    apply_all,
    build_lookup,
    collect_tag_counts,
    configured_fields,
    find_unmapped_duplicate_groups,
    load_merge_config,
    suggest_merge_yaml,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Merge similar tags site-wide using config/tag_merge_map.yml."
    )
    parser.add_argument("--root", default=str(SITE_ROOT), help="Jekyll site source directory")
    parser.add_argument(
        "--map",
        default=str(DEFAULT_MAP_PATH),
        help="Path to tag merge map YAML",
    )
    parser.add_argument(
        "--tag-groups",
        default=str(DEFAULT_TAG_GROUPS_PATH),
        help="Path to tag_groups.yml for network display",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="List tag usage and unmapped duplicate groups",
    )
    parser.add_argument(
        "--suggest",
        action="store_true",
        help="With --report, print YAML for unmapped duplicate groups",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show changes without writing files",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    map_path = Path(args.map).resolve()
    tag_groups_path = Path(args.tag_groups).resolve()

    if not map_path.exists():
        print(f"ERROR: Missing merge map: {map_path}")
        return 1

    try:
        config = load_merge_config(map_path)
        lookup = build_lookup(config)
        fields = configured_fields(config)
    except ValueError as exc:
        print(f"ERROR: {exc}")
        return 1

    if args.report:
        counts = collect_tag_counts(root, fields)
        print("Tag audit")
        print("-----------")
        print(f"Unique tags:   {len(counts)}")
        print(f"Mapped tags:   {sum(1 for tag in counts if lookup.get(tag, tag) != tag)}")
        print(f"Fields:        {', '.join(fields)}")
        print()
        print("Most common tags:")
        for tag, count in counts.most_common(25):
            canonical = lookup.get(tag, tag)
            suffix = f" -> {canonical}" if canonical != tag else ""
            print(f"  {count:3}  {tag}{suffix}")

        duplicates = find_unmapped_duplicate_groups(counts, lookup)
        print()
        if duplicates:
            print(f"Unmapped duplicate groups: {len(duplicates)}")
            for variants in duplicates.values():
                canonical, count = variants[0]
                others = ", ".join(f"{tag} ({c})" for tag, c in variants[1:])
                print(f"  {canonical} ({count}) | also: {others}")
            if args.suggest:
                print()
                print(suggest_merge_yaml(duplicates))
        else:
            print("Unmapped duplicate groups: 0")

        if not args.dry_run:
            return 0

    write = not args.dry_run

    file_changes, group_changes = apply_all(
        root=root,
        map_path=map_path,
        tag_groups_path=tag_groups_path,
        write=write,
    )

    if args.report and args.dry_run:
        print()

    mode = "Would update" if args.dry_run else "Updated"
    print(f"{mode} {len(file_changes)} front-matter field(s)")
    for change in file_changes:
        print(f"  - {change}")
    if group_changes:
        print(f"{mode} {len(group_changes)} tag group list(s)")
        for change in group_changes:
            print(f"  - {change}")

    if args.dry_run and not file_changes and not group_changes:
        print("No changes needed.")
    elif write and not file_changes and not group_changes:
        print("No changes needed.")
    elif args.dry_run:
        print()
        print("Re-run without --dry-run to apply.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
