#!/usr/bin/env python3
"""An affiliation is only shown when its organisation resolves to a directory entry.

ORCID and NVA write an organisation's name however the person typed it, so the
matcher has to cope with a short form, a long form, both joined by a dash, a
company suffix, and a centre named after its university. It also has to refuse,
because a name that resolves to the wrong body is worse than one that resolves to
nothing: two entries here are a parent and a child, and they are not the same
organisation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import enrich_directory_from_nva as enrich
from repo_paths import SITE_ROOT

RESOLVES = [
    ("Oslo Metropolitan University", "oslo-metropolitan-university"),
    ("OsloMet – Oslo Metropolitan University", "oslo-metropolitan-university"),
    ("NTNU", "norwegian-university-of-science-and-technology"),
    ("NTNU Norwegian University of Science and Technology", "norwegian-university-of-science-and-technology"),
    ("NTNU ARTEC", "norwegian-university-of-science-and-technology"),
    ("Simula Metropolitan Center for Digital Engineering AS", "simula-metropolitan-center-for-digital-engineering"),
    ("NORSUS", "norsus-norwegian-institute-for-sustainability-research"),
    ("SINTEF Oslo", "sintef"),
    ("SINTEF Digital", "sintef"),
    ("Stiftelsen Skapia", "skapia"),
    ("Nasjonalmuseet", "national-museum-of-norway"),
    ("Ultima Oslo Contemporary Music Festival", "ultima-festival"),
]

# Nothing in the directory stands for these, and inventing a match would put a
# person at an organisation they do not work for.
REFUSES = [
    "Freelance pianist/harpsichordist",
    "Frank Ekeberg",
    "Aenima Studios",
    "Government of India",
    "Teleperformance",
    "Koninklijk Conservatorium",
    "",
]


def main() -> int:
    lookup, _ = enrich.build_institution_lookup(SITE_ROOT)
    failures = []

    for name, expected in RESOLVES:
        got = enrich.lookup_institution_slug(name, lookup)
        if got != expected:
            failures.append(f"{name!r} resolved to {got or 'nothing'}, expected {expected}")

    for name in REFUSES:
        got = enrich.lookup_institution_slug(name, lookup)
        if got:
            failures.append(f"{name!r} resolved to {got}, and should resolve to nothing")

    for line in failures:
        print(f"  {line}")
    total = len(RESOLVES) + len(REFUSES)
    print(f"institution matching: {total - len(failures)} of {total} cases pass")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
