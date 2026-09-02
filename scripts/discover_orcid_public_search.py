#!/usr/bin/env python3
"""Discover ORCID iDs for directory people via the public ORCID search API.

Complements scripts/fill_missing_nva_orcid.py: that script only finds ORCID
already linked from an NVA profile, which misses people without an NVA
profile or whose NVA profile lacks an ORCID identifier. This script queries
the public ORCID registry (https://pub.orcid.org, no auth required) by
given/family name and only fills `urls.orcid` when a candidate's ORCID
employment history overlaps with the person's known institution/department,
to avoid attaching the wrong identifier. Ambiguous or unverifiable candidates
are printed for manual review instead of being applied.

Usage:
  python3 scripts/discover_orcid_public_search.py --dry-run
  python3 scripts/discover_orcid_public_search.py --slug some-person --dry-run
  python3 scripts/discover_orcid_public_search.py
"""
from __future__ import annotations

import argparse
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote

import requests

from directory_io import load_entry, save_entry
from enrich_directory_from_nva import build_institution_lookup
from repo_paths import SITE_ROOT

PEOPLE_ROOT = SITE_ROOT / "_directory" / "people"
ORCID_SEARCH_URL = "https://pub.orcid.org/v3.0/expanded-search/"
REQUEST_DELAY_SECONDS = 0.3


def ascii_fold(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value or "")
    return "".join(ch for ch in ascii_value if not unicodedata.combining(ch))


def norm(value: str) -> str:
    return ascii_fold(value or "").casefold().strip()


def search_orcid(given: str, family: str) -> list[dict]:
    query = f'given-names:"{given}" AND family-name:"{family}"'
    url = ORCID_SEARCH_URL + "?q=" + quote(query) + "&rows=10"
    resp = requests.get(url, headers={"Accept": "application/json"}, timeout=30)
    resp.raise_for_status()
    return resp.json().get("expanded-result") or []


def institution_names_for(data: dict, slug_to_name: dict[str, str]) -> list[str]:
    names = []
    for slug in [data.get("institution")] + list(data.get("institutions") or []):
        slug = (slug or "").strip()
        if slug and slug in slug_to_name:
            names.append(slug_to_name[slug])
    department = (data.get("department") or "").strip()
    if department:
        names.append(department)
    return names


def institution_overlap(candidate_institutions: list[str], known_names: list[str]) -> bool:
    cand_norm = [norm(n) for n in candidate_institutions if n]
    for known in known_names:
        kn = norm(known)
        if not kn:
            continue
        for cn in cand_norm:
            if kn in cn or cn in kn:
                return True
            if len(set(kn.split()) & set(cn.split())) >= 2:
                return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--slug", action="append", help="Only process specific person slug (repeatable)")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing files")
    args = parser.parse_args()

    _, slug_to_name = build_institution_lookup(SITE_ROOT)
    selected = set(args.slug or [])

    applied, suggestions, not_found = [], [], []

    for index_md in sorted(PEOPLE_ROOT.glob("*/index.md")):
        if index_md.parent.name == "_template":
            continue
        if selected and index_md.parent.name not in selected:
            continue

        data, body = load_entry(index_md)
        urls = data.get("urls") or {}
        if (urls.get("orcid") or "").strip():
            continue

        name = str(data.get("name") or "").strip()
        parts = name.split()
        if len(parts) < 2:
            not_found.append((name, index_md.parent.name, "name too short"))
            continue
        given, family = parts[0], parts[-1]

        try:
            results = search_orcid(given, family)
        except Exception as exc:
            not_found.append((name, index_md.parent.name, f"search error: {exc}"))
            time.sleep(REQUEST_DELAY_SECONDS)
            continue
        time.sleep(REQUEST_DELAY_SECONDS)

        if not results:
            not_found.append((name, index_md.parent.name, "no orcid search results"))
            continue

        known_names = institution_names_for(data, slug_to_name)
        matches = [
            (r.get("orcid-id"), r.get("institution-name") or [])
            for r in results
            if institution_overlap(r.get("institution-name") or [], known_names)
        ]

        if len(matches) == 1:
            orcid_id, insts = matches[0]
            if not args.dry_run:
                urls["orcid"] = f"https://orcid.org/{orcid_id}"
                data["urls"] = urls
                save_entry(index_md, data, body)
            applied.append((name, index_md.parent.name, orcid_id, insts))
        elif len(matches) > 1:
            suggestions.append((name, index_md.parent.name, "ambiguous", matches))
        elif len(results) == 1:
            r = results[0]
            suggestions.append((name, index_md.parent.name, "unverified", [(r.get("orcid-id"), r.get("institution-name") or [])]))
        else:
            not_found.append((name, index_md.parent.name, f"{len(results)} candidates, none matched institution"))

    verb = "Would apply" if args.dry_run else "Applied"
    print(f"=== {verb} {len(applied)} high-confidence ORCID matches ===")
    for name, slug, orcid_id, insts in applied:
        print(f"  {name} ({slug}) -> {orcid_id}  [{', '.join(insts)}]")

    print(f"\n=== {len(suggestions)} suggestions needing manual review ===")
    for name, slug, reason, matches in suggestions:
        print(f"  {name} ({slug}) [{reason}]")
        for orcid_id, insts in matches:
            print(f"    - https://orcid.org/{orcid_id}  [{', '.join(insts)}]")

    print(f"\n=== {len(not_found)} people with no usable ORCID match ===")
    for name, slug, reason in not_found:
        print(f"  {name} ({slug}): {reason}")


if __name__ == "__main__":
    main()
