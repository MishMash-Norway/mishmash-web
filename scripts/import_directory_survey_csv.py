#!/usr/bin/env python3
"""Import or update directory people from a MishMash survey CSV export."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

from enrich_directory_from_nva import ORCID_PROFILE_RE, build_institution_lookup, orcid_primary_employment
from directory_io import load_entry, save_entry
from repo_paths import SITE_ROOT
from sync_directory_reciprocity import sync_directory

EMAIL_DOMAIN_TO_INSTITUTION = {
    "ntnu.no": "norwegian-university-of-science-and-technology",
    "uio.no": "university-of-oslo",
    "nla.no": "nla-university-college",
    "nb.no": "national-library-of-norway",
    "nmh.no": "norwegian-academy-of-music",
    "bi.no": "bi-norwegian-business-school",
    "kristiania.no": "kristiania-university-college",
    "uia.no": "university-of-agder",
    "uib.no": "university-of-bergen",
    "inn.no": "inland-norway-university-of-applied-sciences",
}

HOST_TO_INSTITUTION = {
    "ntnu.no": "norwegian-university-of-science-and-technology",
    "uio.no": "university-of-oslo",
    "people.uio.no": "university-of-oslo",
    "nla.no": "nla-university-college",
    "nb.no": "national-library-of-norway",
    "nmh.no": "norwegian-academy-of-music",
    "bi.no": "bi-norwegian-business-school",
    "kristiania.no": "kristiania-university-college",
    "uia.no": "university-of-agder",
    "uib.no": "university-of-bergen",
    "inn.no": "inland-norway-university-of-applied-sciences",
}

INVALID_NVA_RE = re.compile(r"/my-page/|/profile/research-profile/?$")
ORCID_ID_RE = re.compile(r"^(\d{4}-\d{4}-\d{4}-\d{3}[\dX])$", re.I)
WP_TAG_RE = re.compile(r"^WP[1-7]$", re.I)
URL_FIELDS = (
    "personal_website",
    "institutional_website",
    "github",
    "linkedin",
    "youtube",
    "facebook",
    "mastodon",
    "instagram",
)
CSV_URL_COLUMNS = {
    "website (institution)": "institutional_website",
    "website (personal)": "personal_website",
    "github": "github",
    "linkedin": "linkedin",
    "youtube": "youtube",
    "facebook": "facebook",
    "mastodon": "mastodon",
    "instagram": "instagram",
    "orcid": "orcid",
    "nva": "nva",
}


def slugify(value: str) -> str:
    value = value.lower()
    for src, dst in {"æ": "ae", "ø": "o", "å": "a"}.items():
        value = value.replace(src, dst)
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value).strip("-")
    return value[:80]


def normalize_url(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if ORCID_ID_RE.match(value):
        return f"https://orcid.org/{value}"
    if value.startswith("orcid.org/"):
        return f"https://{value}"
    if "orcid.org/my-orcid" in value:
        match = re.search(r"orcid=((?:\d{4}-){3}[\dX]{4})", value, re.I)
        if match:
            return f"https://orcid.org/{match.group(1)}"
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", value):
        value = f"https://{value.lstrip('/')}"
    return value


def valid_nva_url(value: str) -> str:
    value = normalize_url(value)
    if not value or INVALID_NVA_RE.search(value):
        return ""
    if "nva.sikt.no/research-profile/" in value:
        return value
    return ""


def host_from_url(value: str) -> str:
    value = normalize_url(value)
    if not value:
        return ""
    host = urlparse(value).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def institution_from_orcid(orcid_url: str) -> tuple[str, str, str]:
    match = ORCID_PROFILE_RE.search(orcid_url or "")
    if not match:
        return "", "", ""
    lookup, _ = build_institution_lookup(SITE_ROOT)
    return orcid_primary_employment(match.group(1), lookup)


def institution_from_row(row: dict) -> str:
    email = (row.get("Email address") or "").strip().lower()
    if "@" in email:
        domain = email.split("@", 1)[1]
        if domain in EMAIL_DOMAIN_TO_INSTITUTION:
            return EMAIL_DOMAIN_TO_INSTITUTION[domain]

    for column in ("website (institution)", "website (personal)"):
        host = host_from_url(row.get(column, ""))
        if host in HOST_TO_INSTITUTION:
            return HOST_TO_INSTITUTION[host]
        for known_host, slug in HOST_TO_INSTITUTION.items():
            if host.endswith(known_host):
                return slug
    return ""


def parse_tags(raw: str) -> list[str]:
    if not raw or not raw.strip():
        return []
    tags: list[str] = []
    seen: set[str] = set()
    for part in re.split(r",\s*", raw.strip()):
        tag = part.strip().lstrip("#").strip()
        if not tag:
            continue
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            tags.append(tag)
    return tags


def parse_work_packages(row: dict) -> list[str]:
    wps: list[str] = []
    for n in range(1, 8):
        value = (row.get(f"Work package(s).WP{n}") or "").strip()
        if value:
            wps.append(value.upper())
    return sorted(wps, key=lambda item: int(item[2:]))


def strip_wp_tags(items: list | None) -> list[str]:
    return [item for item in (items or []) if isinstance(item, str) and not WP_TAG_RE.match(item.strip())]


def merge_wps(existing: list | None, new_items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in list(existing or []) + list(new_items or []):
        if not isinstance(item, str):
            continue
        value = item.strip().upper()
        if not WP_TAG_RE.match(value):
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return sorted(out, key=lambda item: int(item[2:]))


def merge_unique(existing: list | None, new_items: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in list(existing or []) + new_items:
        if not isinstance(item, str):
            continue
        value = item.strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def merge_urls(existing: dict | None, incoming: dict[str, str]) -> dict[str, str]:
    merged = {key: "" for key in URL_FIELDS + ("orcid", "nva")}
    for key, value in (existing or {}).items():
        if isinstance(value, str):
            merged[key] = value.strip()
    for key, value in incoming.items():
        if value and not merged.get(key):
            merged[key] = value
    return merged


def build_person_data(row: dict, existing: dict | None) -> tuple[dict, str]:
    name = (row.get("Name") or "").strip()
    slug = (existing or {}).get("slug") or slugify(name)
    institution = institution_from_row(row)
    wp_tags = parse_work_packages(row)
    csv_tags = parse_tags(row.get("Tags", ""))
    comments = (row.get("Comments") or "").strip()

    incoming_urls: dict[str, str] = {}
    for csv_col, url_key in CSV_URL_COLUMNS.items():
        raw = (row.get(csv_col) or "").strip()
        if not raw:
            continue
        if url_key == "nva":
            normalized = valid_nva_url(raw)
        elif url_key == "orcid":
            normalized = normalize_url(raw)
            if "orcid.org" not in normalized:
                normalized = ""
        else:
            normalized = normalize_url(raw)
        if normalized:
            incoming_urls[url_key] = normalized

    if not institution:
        orcid_url = incoming_urls.get("orcid") or normalize_url((existing or {}).get("urls", {}).get("orcid", ""))
        if orcid_url:
            position, inst_slug, department = institution_from_orcid(orcid_url)
            institution = inst_slug
            if institution and not (existing or {}).get("position") and position:
                existing = dict(existing or {})
                existing.setdefault("position", position)
            if institution and not (existing or {}).get("department") and department and department != institution:
                existing = dict(existing or {})
                existing.setdefault("department", department)

    existing = existing or {}
    institutions = merge_unique(existing.get("institutions"), [institution] if institution else [])
    primary_institution = existing.get("institution") or institution or (institutions[0] if institutions else "")
    if primary_institution:
        institutions = merge_unique(institutions, [primary_institution])

    wps = merge_wps(existing.get("wps"), wp_tags)
    tags = merge_unique(strip_wp_tags(existing.get("tags")), csv_tags)
    search_keywords = merge_unique(strip_wp_tags(existing.get("search_keywords")), tags)

    data = {
        "type": "person",
        "slug": slug,
        "name": name,
        "title": name,
        "position": existing.get("position") or "",
        "department": existing.get("department") or "",
        "institution": primary_institution,
        "institutions": institutions,
        "wps": wps,
        "projects": existing.get("projects") or [],
        "roles": existing.get("roles") or ["Member"],
        "urls": merge_urls(existing.get("urls"), incoming_urls),
        "aliases": existing.get("aliases") or [],
        "tags": tags,
        "search_keywords": search_keywords,
        "selected_works": existing.get("selected_works") or [],
        "source_mentions": existing.get("source_mentions") or [],
        "summary": existing.get("summary") or (comments if comments and not comments.lower().startswith("more sites:") else None),
        "permalink": existing.get("permalink") or f"/people/{slug}/",
        "redirect_from": existing.get("redirect_from") or [f"/directory/people/{slug}/"],
    }

    for optional in ("layout", "image", "nva_affiliations", "affiliation_units", "published"):
        if optional in existing and existing[optional] not in (None, "", []):
            data[optional] = existing[optional]

    if not data.get("summary"):
        data.pop("summary", None)

    if existing and existing.get("_body"):
        body = existing["_body"]
        if comments and comments not in body and not comments.lower().startswith("more sites:"):
            body = f"{body.rstrip()}\n\n{comments}\n"
    elif comments and not comments.lower().startswith("more sites:"):
        body = f"{comments}\n"
    else:
        body = "Bio coming soon.\n"

    return data, body


def find_existing_slug(people_root: Path, name: str) -> Path | None:
    slug = slugify(name)
    candidate = people_root / slug / "index.md"
    if candidate.exists():
        return candidate

    target = name.strip().lower()
    for index_md in people_root.glob("*/index.md"):
        if index_md.parent.name in {"_template"}:
            continue
        data, _ = load_entry(index_md)
        if str(data.get("name", "")).strip().lower() == target:
            return index_md
    return None


def import_csv(csv_path: Path, dry_run: bool = False) -> dict[str, int]:
    people_root = SITE_ROOT / "_directory" / "people"
    stats = {"created": 0, "updated": 0, "skipped": 0}

    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for row in reader:
            name = (row.get("Name") or "").strip()
            if not name:
                stats["skipped"] += 1
                continue

            existing_path = find_existing_slug(people_root, name)
            existing_data: dict | None = None
            existing_body = ""
            if existing_path:
                existing_data, existing_body = load_entry(existing_path)
                existing_data["_body"] = existing_body

            data, body = build_person_data(row, existing_data)
            slug = data["slug"]
            target = people_root / slug / "index.md"

            if dry_run:
                action = "update" if existing_path else "create"
                print(f"{action}: {name} -> {target.relative_to(SITE_ROOT)}")
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            save_entry(target, data, body)
            if existing_path:
                stats["updated"] += 1
                print(f"Updated {name}")
            else:
                stats["created"] += 1
                print(f"Created {name}")

    if not dry_run:
        sync_directory(SITE_ROOT, dry_run=False)

    return stats


def fill_missing_institutions(dry_run: bool = False) -> int:
    """Add institution affiliations from ORCID for people missing them."""
    people_root = SITE_ROOT / "_directory" / "people"
    updated = 0
    for index_md in sorted(people_root.glob("*/index.md")):
        if index_md.parent.name.startswith("_"):
            continue
        data, body = load_entry(index_md)
        insts = [i for i in (data.get("institutions") or []) if isinstance(i, str) and i.strip()]
        primary = str(data.get("institution") or "").strip()
        if insts or primary:
            continue
        orcid_url = normalize_url((data.get("urls") or {}).get("orcid", ""))
        if not orcid_url:
            continue
        position, institution, department = institution_from_orcid(orcid_url)
        if not institution:
            continue
        data["institution"] = institution
        data["institutions"] = [institution]
        if position and not data.get("position"):
            data["position"] = position
        if department and department != institution and not data.get("department"):
            data["department"] = department
        if dry_run:
            print(f"would update {data.get('name')} -> {institution}")
        else:
            save_entry(index_md, data, body)
            print(f"Updated {data.get('name')} -> {institution}")
        updated += 1
    if updated and not dry_run:
        sync_directory(SITE_ROOT, dry_run=False)
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", nargs="?", type=Path, help="Path to survey CSV export")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--fill-missing-institutions",
        action="store_true",
        help="Fill missing affiliations from ORCID for all directory people",
    )
    args = parser.parse_args()

    if args.fill_missing_institutions:
        count = fill_missing_institutions(dry_run=args.dry_run)
        if not args.dry_run:
            print(f"Filled institutions for {count} people.")
        return

    if not args.csv_path:
        parser.error("csv_path is required unless --fill-missing-institutions is used")

    stats = import_csv(args.csv_path.resolve(), dry_run=args.dry_run)
    if not args.dry_run:
        print(
            f"Done: {stats['created']} created, {stats['updated']} updated, {stats['skipped']} skipped."
        )


if __name__ == "__main__":
    main()
