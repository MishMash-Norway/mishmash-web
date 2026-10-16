#!/usr/bin/env python3
"""Write the QuickStatements batch that creates MishMash's Wikidata item.

Builds the statements from site/_data/centre.yml and the directory, so the
item says what the facts page says, each statement with a reference to its
source. The batch is printed (or written with --out) for a person to paste
into QuickStatements (https://quickstatements.toolforge.org/) while logged in;
nothing is sent to Wikidata from here. A person in a role is added only when
their directory entry has a Wikidata item.

When the item exists, put its address in centre.yml under
identifiers.wikidata, and the site links to it.

    python3 scripts/wikidata_centre_statements.py
    python3 scripts/wikidata_centre_statements.py --out temp/mishmash-wikidata.qs
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from directory_io import iter_directory_entries
from repo_paths import SITE_ROOT

QID = re.compile(r"(Q\d+)$")
# Classes and places the item points to.
RESEARCH_CENTER, NORWAY, OSLO = "Q7315155", "Q20", "Q585"
# Wikidata properties, by name.
P = {"instance_of": "P31", "country": "P17", "headquarters": "P159", "parent": "P749",
     "short_name": "P1813", "official_name": "P1448", "inception": "P571", "website": "P856",
     "funder": "P8324", "director": "P1037", "chair": "P488", "start": "P580", "end": "P582",
     "described_at": "P973", "reference_url": "S854", "retrieved": "S813"}
ROLE_PROPERTY = {"Director": "director", "Board Leader": "chair"}


def qid(url: str) -> str | None:
    match = QID.search((url or "").rstrip("/"))
    return match.group(1) if match else None


def day(value) -> str:
    return f"+{value}T00:00:00Z/11"


def statements(centre: dict, people: list[dict], institutions: dict[str, dict], today: str) -> list[str]:
    dates = {d["key"]: d for d in centre["dates"]}
    site = centre["url"]
    facts_page = site + "about/facts/"

    def ref(url: str) -> str:
        return f'\t{P["reference_url"]}\t"{url}"\t{P["retrieved"]}\t{day(today)}'

    host = qid((institutions.get(centre["host"]["slug"]) or {}).get("urls", {}).get("wikidata", ""))
    funder = qid(centre["funder"]["wikidata"])
    lines = [
        "CREATE",
        f'LAST\tLen\t"{centre["name"]["en"]}"',
        f'LAST\tLnb\t"{centre["name"]["nb"]}"',
        f'LAST\tLnn\t"{centre["name"]["nb"]}"',
        f'LAST\tAen\t"{centre["short_name"]}"',
        f'LAST\tAnb\t"{centre["short_name"]}"',
        'LAST\tDen\t"Norwegian research centre for AI and creativity"',
        'LAST\tDnb\t"norsk forskningssenter for KI og kreativitet"',
        f'LAST\t{P["instance_of"]}\t{RESEARCH_CENTER}',
        f'LAST\t{P["country"]}\t{NORWAY}',
        f'LAST\t{P["headquarters"]}\t{OSLO}',
        f'LAST\t{P["official_name"]}\ten:"{centre["name"]["en"]}"',
        f'LAST\t{P["official_name"]}\tnb:"{centre["name"]["nb"]}"',
        f'LAST\t{P["short_name"]}\ten:"{centre["short_name"]}"',
        f'LAST\t{P["website"]}\t"{site}"',
        f'LAST\t{P["inception"]}\t{day(dates["started"]["date"])}' + ref(facts_page),
    ]
    if host:
        lines.append(f'LAST\t{P["parent"]}\t{host}' + ref(centre["identifiers"]["nva_project"]))   # NVA names the coordinating institution
    if funder:
        lines.append(f'LAST\t{P["funder"]}\t{funder}\t{P["start"]}\t{day(dates["started"]["date"])}'
                     f'\t{P["end"]}\t{day(dates["ends"]["date"])}' + ref(centre["funder"]["url"]))
    for role in centre.get("roles") or []:
        prop = ROLE_PROPERTY.get(role["role"])
        if not prop:
            continue
        for person in people:
            person_qid = qid((person.get("urls") or {}).get("wikidata", ""))
            if role["role"] in (person.get("roles") or []) and person_qid:
                since = f'\t{P["start"]}\t{day(role["since"])}' if role.get("since") else ""
                lines.append(f'LAST\t{P[prop]}\t{person_qid}{since}' + ref(facts_page))
    for url in (centre["identifiers"]["nva_project"], centre["identifiers"]["rcn_project"]):
        lines.append(f'LAST\t{P["described_at"]}\t"{url}"')
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    centre = yaml.safe_load((SITE_ROOT / "_data" / "centre.yml").read_text(encoding="utf-8"))
    if centre["identifiers"].get("wikidata"):
        print(f"MishMash already has a Wikidata item: {centre['identifiers']['wikidata']}", file=sys.stderr)
        return 1
    entries = list(iter_directory_entries(SITE_ROOT))
    people = [data for section, _, _, data, _ in entries if section == "people"]
    institutions = {data.get("slug"): data for section, _, _, data, _ in entries if section == "institutions"}
    text = "\n".join(statements(centre, people, institutions, dt.date.today().isoformat())) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(f"{text.count(chr(10))} lines -> {args.out}")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
