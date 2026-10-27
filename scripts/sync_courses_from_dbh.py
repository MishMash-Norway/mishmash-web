#!/usr/bin/env python3
"""Candidate courses for the course directory, from DBH (issue #77, phase 1).

DBH, the national database for higher education statistics, publishes every
course at Norwegian universities and colleges in its open table 208 (Emner):
code, name, institution, faculty, level, credits, language and status. This
script fetches one year (spring and autumn) for the partner institutions in
site/_data/partners.yml, proposes the courses whose names match the keywords
below, and writes the candidates to temp/ for review. It changes nothing on
the site.

The keywords only propose. Many relevant courses do not say what they are in
their name, so the list is a starting point for the education work package,
not the directory itself.

    python3 scripts/sync_courses_from_dbh.py                 # last complete year
    python3 scripts/sync_courses_from_dbh.py --year 2025
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
PARTNERS = ROOT / "site" / "_data" / "partners.yml"
TEMP = ROOT / "temp"
API = "https://dbh-data.dataporten-api.no/Tabeller/hentJSONTabellData"
SEMESTERS = {"1": "spring", "3": "autumn"}
LEVELS = {"LN": "bachelor", "HN": "master", "FU": "phd"}

# A partner whose name in partners.yml differs from DBH's institution name.
DBH_NAME = {
    "Oslo Metropolitan University": "OsloMet – storbyuniversitetet",
    "Universitetet i Tromsø": "Universitetet i Tromsø - Norges arktiske universitet",
}

# Why a course is proposed. The first group is AI by name; the second is
# fields where creative work and computing meet, which rarely say AI.
KEYWORDS = {
    "ai": r"\b(KI|AI)\b|kunstig intelligens|artificial intelligence|maskinlæring|machine learning|"
          r"generativ|deep learning|dyp læring|språkmodell|language model|nevrale nett|neural network",
    "creative-tech": r"musikkteknologi|music technology|lydteknologi|sound technology|kreativ koding|creative coding|"
                     r"interaksjonsdesign|interaction design|digital humaniora|digital humanities|"
                     r"digital kunst|digital art|spillutvikling|game development",
}
PATTERNS = {k: re.compile(v, re.I) for k, v in KEYWORDS.items()}


def partner_names() -> list[str]:
    """Norwegian names of the partners, without the abbreviation in brackets."""
    data = yaml.safe_load(PARTNERS.read_text(encoding="utf-8")) or []
    names = []
    for group in data:
        for e in group.get("entries") or []:
            name = (e.get("name_nb") or e.get("name") or "").strip()
            name = re.sub(r"\s*\([^)]*\)\s*$", "", name)
            if name:
                names.append(DBH_NAME.get(name, name))
    return names


def fetch(year: int, semester: str) -> list[dict]:
    body = {
        "tabell_id": 208, "api_versjon": 1, "statuslinje": "N", "begrensning": "300000",
        "kodetekst": "J", "desimal_separator": ".", "variabler": ["*"], "sortBy": [],
        "filter": [
            {"variabel": "Årstall", "selection": {"filter": "item", "values": [str(year)]}},
            {"variabel": "Semester", "selection": {"filter": "item", "values": [semester]}},
        ],
    }
    r = requests.post(API, json=body, timeout=300)
    r.raise_for_status()
    return r.json()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--year", type=int, default=date.today().year - 1, help="Year to fetch (default: last complete year)")
    args = ap.parse_args()

    rows = []
    for sem in SEMESTERS:
        rows += fetch(args.year, sem)
    if not rows:
        sys.exit(f"DBH returned no courses for {args.year}")

    dbh_names = {r["Institusjonsnavn"] for r in rows}
    partners = partner_names()
    matched = [p for p in partners if p in dbh_names]
    missing = [p for p in partners if p not in dbh_names]

    # One row per course, with the semesters it is taught in.
    courses: dict[tuple[str, str], dict] = {}
    for r in rows:
        if r["Institusjonsnavn"] not in matched:
            continue
        key = (r["Institusjonskode"], r["Emnekode"])
        c = courses.setdefault(key, {
            "institution": r["Institusjonsnavn"], "institution_code": r["Institusjonskode"],
            "code": r["Emnekode"], "title": r["Emnenavn"], "faculty": r.get("Avdelingsnavn") or "",
            "level": LEVELS.get(r.get("Nivåkode"), r.get("Nivånavn") or ""), "credits": r.get("Studiepoeng") or "",
            "language": r.get("Underv.språk") or "", "status": r.get("Statusnavn") or "", "semesters": set(),
        })
        c["semesters"].add(SEMESTERS[r["Semester"]])

    candidates = []
    for c in courses.values():
        reasons = [k for k, p in PATTERNS.items() if p.search(c["title"])]
        if reasons:
            candidates.append({**c, "semesters": " ".join(sorted(c["semesters"])), "match": " ".join(reasons)})
    candidates.sort(key=lambda c: (c["institution"], c["level"], c["code"]))

    TEMP.mkdir(exist_ok=True)
    out = TEMP / f"course-candidates-{args.year}.csv"
    fields = ["institution", "code", "title", "level", "credits", "language", "semesters", "faculty", "match", "status", "institution_code"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(candidates)

    print(f"DBH {args.year}: {len(rows)} course rows, {len(dbh_names)} institutions")
    print(f"Partners matched in DBH: {len(matched)} of {len(partners)} (DBH covers Norwegian universities and colleges only)")
    for p in missing:
        print(f"  not in DBH: {p}")
    print(f"Courses at the matched partners: {len(courses)}; candidates: {len(candidates)}")
    for k, v in sorted(Counter(c["level"] for c in candidates).items()):
        print(f"  {k}: {v}")
    for k, v in Counter(c["match"] for c in candidates).most_common():
        print(f"  match {k}: {v}")
    for k, v in Counter(c["institution"] for c in candidates).most_common():
        print(f"  {k}: {v}")
    print(f"Written: {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
