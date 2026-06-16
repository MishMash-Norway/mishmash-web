#!/usr/bin/env python3
"""Fill and refresh urls.nva and urls.orcid in directory people entries.

This script updates `urls.nva` and `urls.orcid` in `site/_directory/people/*/index.md`:
canonicalizes URLs, discovers missing NVA profiles, and syncs ORCID from NVA when available.
"""

import argparse
from pathlib import Path

import yaml

from enrich_directory_from_nva import (  # noqa: E402
    NoAliasDumper,
    build_institution_lookup,
    configure_nva_auth,
    discover_profile_id_by_name,
    extract_orcid_id,
    extract_profile_id,
    find_orcid,
    get_json,
    nva_api_url,
    ordered_person,
    split_frontmatter,
)
from repo_paths import SITE_ROOT


def canonical_orcid_url(value: str) -> str:
    orcid_id = extract_orcid_id((value or "").strip())
    return f"https://orcid.org/{orcid_id}" if orcid_id else ""


def canonical_nva_url(value: str) -> str:
    profile_id = extract_profile_id((value or "").strip())
    return f"https://nva.sikt.no/research-profile/{profile_id}" if profile_id else ""


def normalize_institution_slug(data: dict) -> str:
    slug = (data.get("institution") or "").strip()
    if slug:
        return slug.replace("/institutions/", "").replace("/", "")

    institutions = data.get("institutions") or []
    if isinstance(institutions, list) and institutions:
        first = str(institutions[0]).strip()
        return first.replace("/institutions/", "").replace("/", "")
    return ""


def update_person_file(
    index_md: Path,
    root: Path,
    institution_lookup: dict[str, str],
    slug_to_institution_name: dict[str, str],
    org_cache: dict,
    discover_nva_loose: bool,
    dry_run: bool,
) -> tuple[bool, str]:
    text = index_md.read_text(encoding="utf-8")
    front, body = split_frontmatter(text)
    data = yaml.safe_load(front) or {}

    slug = (data.get("slug") or index_md.parent.name).strip()
    name = (data.get("name") or data.get("title") or "").strip()
    urls = data.get("urls") or {}
    if not isinstance(urls, dict):
        urls = {}

    changed = False
    notes = []

    nva_url = canonical_nva_url(urls.get("nva") or "")
    if nva_url and urls.get("nva") != nva_url:
        urls["nva"] = nva_url
        changed = True
        notes.append("normalized nva")

    orcid_url = canonical_orcid_url(urls.get("orcid") or "")
    if orcid_url and urls.get("orcid") != orcid_url:
        urls["orcid"] = orcid_url
        changed = True
        notes.append("normalized orcid")

    if not nva_url:
        institution_slug = normalize_institution_slug(data)
        if name and institution_slug:
            profile_id, reason = discover_profile_id_by_name(
                name=name,
                institution_slug=institution_slug,
                slug_to_institution_name=slug_to_institution_name,
                org_cache=org_cache,
                allow_loose=discover_nva_loose,
            )
            if profile_id:
                nva_url = f"https://nva.sikt.no/research-profile/{profile_id}"
                urls["nva"] = nva_url
                changed = True
                notes.append(reason)
            else:
                notes.append(reason)
        else:
            notes.append("skip: missing name or institution")

    profile_id = extract_profile_id(nva_url)
    if profile_id:
        try:
            profile = get_json(nva_api_url(f"/cristin/person/{profile_id}"))
            nva_orcid = find_orcid(profile.get("identifiers") or [])
            if nva_orcid and urls.get("orcid") != nva_orcid:
                urls["orcid"] = nva_orcid
                changed = True
                notes.append("synced orcid from nva")
            elif not nva_orcid and not orcid_url:
                notes.append("orcid not found in nva")
        except Exception as exc:
            notes.append(f"orcid lookup failed: {exc}")
    elif orcid_url and not nva_url:
        notes.append("skip: orcid without nva")

    if not changed:
        return False, ", ".join(dict.fromkeys(notes)) if notes else "unchanged"

    if dry_run:
        return True, "would update: " + ", ".join(dict.fromkeys(notes))

    data["urls"] = urls
    dumped = yaml.dump(ordered_person(data), allow_unicode=True, sort_keys=False, Dumper=NoAliasDumper).strip()
    index_md.write_text(f"---\n{dumped}\n---\n\n{body.lstrip()}", encoding="utf-8")
    return True, "updated: " + ", ".join(dict.fromkeys(notes))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find missing NVA profile pages and fill ORCID links for directory people entries."
    )
    parser.add_argument("--root", default=str(SITE_ROOT), help="Jekyll site source directory")
    parser.add_argument("--slug", action="append", help="Only process specific person slug (repeatable)")
    parser.add_argument("--discover-nva-loose", action="store_true", help="Allow looser name matching for NVA discovery")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    people_base = root / "_directory" / "people"
    if not people_base.exists():
        raise SystemExit(f"Missing directory: {people_base}")

    configure_nva_auth()
    institution_lookup, slug_to_institution_name = build_institution_lookup(root)
    org_cache = {}

    selected = set(args.slug or [])
    updated = 0
    skipped = 0

    for person_dir in sorted(people_base.iterdir()):
        if not person_dir.is_dir() or person_dir.name.startswith("_"):
            continue
        if selected and person_dir.name not in selected:
            continue

        index_md = person_dir / "index.md"
        if not index_md.exists():
            continue

        try:
            changed, msg = update_person_file(
                index_md=index_md,
                root=root,
                institution_lookup=institution_lookup,
                slug_to_institution_name=slug_to_institution_name,
                org_cache=org_cache,
                discover_nva_loose=args.discover_nva_loose,
                dry_run=args.dry_run,
            )
            if changed:
                updated += 1
            else:
                skipped += 1
            print(f"{person_dir.name}: {msg}")
        except Exception as exc:
            skipped += 1
            print(f"{person_dir.name}: error: {exc}")

    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
