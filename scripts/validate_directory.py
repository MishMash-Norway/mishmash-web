#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

SECTIONS = ("people", "institutions", "projects")
TYPE_BY_SECTION = {
    "people": "person",
    "institutions": "institution",
    "projects": "project",
}

REQUIRED_FIELDS = {
    "person": ("type", "slug", "name", "institutions", "projects"),
    "institution": ("type", "slug", "name", "people", "projects"),
    "project": ("type", "slug", "name", "people", "institutions"),
}


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, flags=re.S)
    if not m:
        return {}

    lines = m.group(1).splitlines()
    data = {}
    i = 0

    while i < len(lines):
        line = lines[i]
        kv = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
        if not kv:
            i += 1
            continue

        key = kv.group(1).strip()
        raw_val = kv.group(2).strip()

        if raw_val.startswith("[") and raw_val.endswith("]"):
            inner = raw_val[1:-1].strip()
            if inner:
                data[key] = [x.strip().strip("'\"") for x in inner.split(",")]
            else:
                data[key] = []
            i += 1
            continue

        if raw_val:
            data[key] = raw_val.strip().strip("'\"")
            i += 1
            continue

        i += 1
        arr = []
        while i < len(lines):
            li = re.match(r"^\s*-\s+(.+?)\s*$", lines[i])
            if not li:
                break
            arr.append(li.group(1).strip().strip("'\""))
            i += 1

        data[key] = arr if arr else ""

    return data


def read_entry(index_file: Path):
    text = index_file.read_text(encoding="utf-8", errors="ignore")
    fm = parse_frontmatter(text)
    return fm


def normalize_list(v):
    if isinstance(v, list):
        return [x for x in v if isinstance(x, str) and x.strip()]
    if isinstance(v, str):
        s = v.strip()
        return [s] if s else []
    return []


def main():
    parser = argparse.ArgumentParser(description="Validate directory people/institutions/projects entries.")
    parser.add_argument("--root", default=".", help="Repository root")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    directory_root = root / "directory"

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

            fm = read_entry(index_md)
            if not fm:
                errors.append(f"No/invalid frontmatter: {index_md.relative_to(root)}")
                continue

            for req in REQUIRED_FIELDS[expected_type]:
                if req not in fm:
                    errors.append(f"{index_md.relative_to(root)} missing required field '{req}'")

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
                "institutions": normalize_list(fm.get("institutions", [])),
                "projects": normalize_list(fm.get("projects", [])),
                "people": normalize_list(fm.get("people", [])),
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
