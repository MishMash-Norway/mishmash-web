#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

from directory_io import (
    apply_jekyll_defaults,
    as_slug_list,
    iter_directory_entries,
    load_entry,
)
from repo_paths import SITE_ROOT

SECTIONS = ("people", "institutions", "projects")
TYPE_BY_SECTION = {
    "people": "person",
    "institutions": "institution",
    "projects": "project",
}

REQUIRED_FIELDS = {
    "person": ("type", "slug", "name", "institutions", "projects"),
    "institution": ("type", "slug", "name", "short_name", "people", "projects"),
    "project": ("type", "slug", "name", "people", "institutions"),
}


def main():
    parser = argparse.ArgumentParser(description="Validate directory people/institutions/projects entries.")
    parser.add_argument("--root", default=str(SITE_ROOT), help="Jekyll site source directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    directory_root = root / "_directory"

    errors = []
    warnings = []

    if not directory_root.exists():
        print(f"ERROR: Missing {directory_root}")
        sys.exit(1)

    entries = {
        "person": {},
        "institution": {},
        "project": {},
    }

    for section in SECTIONS:
        section_dir = directory_root / section
        expected_type = TYPE_BY_SECTION[section]
        if not section_dir.exists():
            warnings.append(f"Missing section directory: directory/{section}")
            continue

        for child in sorted(section_dir.iterdir()):
            if not child.is_dir() or child.name.startswith("_"):
                continue

            index_md = child / "index.md"
            if not index_md.exists():
                errors.append(f"Missing file: {index_md.relative_to(root)}")
                continue

            try:
                fm, _ = load_entry(index_md)
            except ValueError as exc:
                errors.append(f"{index_md.relative_to(root)}: {exc}")
                continue

            fm = apply_jekyll_defaults(fm, section, child.name)

            for req in REQUIRED_FIELDS[expected_type]:
                if req not in fm:
                    errors.append(f"{index_md.relative_to(root)} missing required field '{req}'")

            if expected_type == "institution":
                short_name = str(fm.get("short_name", "")).strip()
                if not short_name:
                    errors.append(f"{index_md.relative_to(root)} missing or empty short_name")

            actual_type = str(fm.get("type", "")).strip()
            if actual_type != expected_type:
                errors.append(
                    f"{index_md.relative_to(root)} has type '{actual_type}', expected '{expected_type}'"
                )

            slug = str(fm.get("slug", "")).strip()
            if not slug:
                errors.append(f"{index_md.relative_to(root)} has empty slug")
                continue

            if slug != child.name:
                errors.append(
                    f"{index_md.relative_to(root)} slug '{slug}' does not match folder '{child.name}'"
                )

            if slug in entries[expected_type]:
                other = entries[expected_type][slug]["path"]
                errors.append(
                    f"Duplicate slug '{slug}' in {index_md.relative_to(root)} and {other.relative_to(root)}"
                )
                continue

            entries[expected_type][slug] = {
                "path": index_md,
                "name": str(fm.get("name", "")).strip(),
                "institutions": as_slug_list(fm.get("institutions", [])),
                "projects": as_slug_list(fm.get("projects", [])),
                "people": as_slug_list(fm.get("people", [])),
            }

    people = entries["person"]
    institutions = entries["institution"]
    projects = entries["project"]

    for pslug, p in people.items():
        ppath = p["path"].relative_to(root)
        for islug in p["institutions"]:
            if islug not in institutions:
                errors.append(f"{ppath}: unknown institution reference '{islug}'")
        for prslug in p["projects"]:
            if prslug not in projects:
                errors.append(f"{ppath}: unknown project reference '{prslug}'")

    for islug, inst in institutions.items():
        ipath = inst["path"].relative_to(root)
        for pslug in inst["people"]:
            if pslug not in people:
                errors.append(f"{ipath}: unknown person reference '{pslug}'")
        for prslug in inst["projects"]:
            if prslug not in projects:
                errors.append(f"{ipath}: unknown project reference '{prslug}'")

    for prslug, proj in projects.items():
        prpath = proj["path"].relative_to(root)
        for pslug in proj["people"]:
            if pslug not in people:
                errors.append(f"{prpath}: unknown person reference '{pslug}'")
        for islug in proj["institutions"]:
            if islug not in institutions:
                errors.append(f"{prpath}: unknown institution reference '{islug}'")

    for pslug, p in people.items():
        ppath = p["path"].relative_to(root)

        for islug in p["institutions"]:
            if islug in institutions and pslug not in institutions[islug]["people"]:
                errors.append(
                    f"{ppath}: person->institution '{islug}' not reciprocated in institution.people"
                )

        for prslug in p["projects"]:
            if prslug in projects and pslug not in projects[prslug]["people"]:
                errors.append(
                    f"{ppath}: person->project '{prslug}' not reciprocated in project.people"
                )

    for islug, inst in institutions.items():
        ipath = inst["path"].relative_to(root)
        for prslug in inst["projects"]:
            if prslug in projects and islug not in projects[prslug]["institutions"]:
                errors.append(
                    f"{ipath}: institution->project '{prslug}' not reciprocated in project.institutions"
                )

    for islug, inst in institutions.items():
        ipath = inst["path"].relative_to(root)
        for pslug in inst["people"]:
            if pslug in people and islug not in people[pslug]["institutions"]:
                errors.append(
                    f"{ipath}: institution.people '{pslug}' not reciprocated in person.institutions"
                )

    for prslug, proj in projects.items():
        prpath = proj["path"].relative_to(root)
        for pslug in proj["people"]:
            if pslug in people and prslug not in people[pslug]["projects"]:
                errors.append(
                    f"{prpath}: project.people '{pslug}' not reciprocated in person.projects"
                )
        for islug in proj["institutions"]:
            if islug in institutions and prslug not in institutions[islug]["projects"]:
                errors.append(
                    f"{prpath}: project.institutions '{islug}' not reciprocated in institution.projects"
                )

    print("Directory validation report")
    print("---------------------------")
    print(f"People:        {len(people)}")
    print(f"Institutions:  {len(institutions)}")
    print(f"Projects:      {len(projects)}")
    print(f"Warnings:      {len(warnings)}")
    print(f"Errors:        {len(errors)}")

    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")

    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("\nOK: all checks passed.")


if __name__ == "__main__":
    main()
