#!/usr/bin/env python3
"""Make the work package leaders local managers of the MishMash project in NVA.

The project record at https://nva.sikt.no/projects/2744839 carries its
contributors with roles: ProjectManager, LocalProjectManager and
ProjectParticipant. The 21 work package leaders in site/_data/work_packages.yml
should hold LocalProjectManager, each with the active affiliation their NVA
person record gives.

The NVA API replaces the whole contributor list on an update, so this reads
the current list, keeps every existing contributor and role, adds the leaders
who are not yet local managers, and sends the union. Nothing is removed. The
API allows the update only for the project's creator or manager, so the token
must belong to one of them; a 403 means it does not.

Usage:
  python3 scripts/nva_project_managers.py            # show what would change
  python3 scripts/nva_project_managers.py --write    # send the update
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from enrich_directory_from_nva import resolve_nva_access_token
from repo_paths import SITE_ROOT

PROJECT = "https://api.nva.unit.no/cristin/project/2744839"
ROLE = "LocalProjectManager"


def leaders() -> list[tuple[str, str]]:
    wp = yaml.safe_load((SITE_ROOT / "_data" / "work_packages.yml").read_text(encoding="utf-8"))
    out = []
    for w in (wp if isinstance(wp, list) else wp.get("work_packages", wp)):
        for key in ("leaders", "leads", "members", "people"):
            if key in w:
                out += [(w.get("id") or w.get("key"), l if isinstance(l, str) else l.get("slug")) for l in w[key]]
                break
    return out


def people_by_slug() -> dict:
    people = {}
    for f in glob.glob(str(SITE_ROOT / "_directory" / "people" / "*" / "index.md")):
        d = yaml.safe_load(Path(f).read_text(encoding="utf-8").split("---")[1]) or {}
        people[d.get("slug")] = d
    return people


def active_affiliation(person_url: str) -> str:
    r = requests.get(person_url, headers={"Accept": "application/json"}, timeout=30)
    r.raise_for_status()
    affs = r.json().get("affiliations") or []
    active = [a for a in affs if a.get("active")] or affs
    return (active[0].get("organization") or "") if active else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="send the update; without it, only report")
    args = ap.parse_args()

    current = requests.get(PROJECT, headers={"Accept": "application/json"}, timeout=30).json()
    contributors = []
    for c in current["contributors"]:
        contributors.append({
            "identity": {"type": "Person", "id": c["identity"]["id"]},
            "roles": [{"type": r["type"], **({"affiliation": {"type": "Organization", "id": r["affiliation"]["id"]}} if r.get("affiliation") else {})}
                      for r in c["roles"]],
        })
    by_id = {c["identity"]["id"]: c for c in contributors}
    print(f"project has {len(contributors)} contributors")

    people = people_by_slug()
    added, kept = [], []
    for wp, slug in leaders():
        d = people.get(slug) or {}
        nva = ((d.get("urls") or {}).get("nva") or "").rstrip("/")
        if not nva:
            print(f"  {wp} {slug}: no NVA id, skipped")
            continue
        person_url = "https://api.nva.unit.no/cristin/person/" + nva.split("/")[-1]
        existing = by_id.get(person_url)
        if existing and any(r["type"] == ROLE for r in existing["roles"]):
            kept.append((wp, d.get("name")))
            continue
        org = active_affiliation(person_url)
        role = {"type": ROLE, **({"affiliation": {"type": "Organization", "id": org}} if org else {})}
        if existing:
            existing["roles"].append(role)
        else:
            contributors.append({"identity": {"type": "Person", "id": person_url}, "roles": [role]})
        added.append((wp, d.get("name"), org.split("/")[-1] if org else "no affiliation"))

    for wp, name, org in added:
        print(f"  add  {wp} {name} ({org})")
    for wp, name in kept:
        print(f"  keep {wp} {name}: already {ROLE}")
    print(f"{len(added)} to add, {len(kept)} already there, {len(contributors)} contributors after")
    Path("temp").mkdir(exist_ok=True)
    Path("temp/nva-project-2744839-contributors.json").write_text(json.dumps({"contributors": contributors}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("payload written to temp/nva-project-2744839-contributors.json")

    if not args.write:
        print("dry run; add --write to send")
        return 0
    token = resolve_nva_access_token()
    r = requests.patch(PROJECT, headers={"Authorization": f"Bearer {token}", "Accept": "application/json",
                                         "Content-Type": "application/json"},
                       json={"contributors": contributors}, timeout=60)
    print(f"PATCH {PROJECT} -> {r.status_code} {r.text[:300]}")
    return 0 if r.status_code == 204 else 1


if __name__ == "__main__":
    raise SystemExit(main())
