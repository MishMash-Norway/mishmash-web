#!/usr/bin/env python3
"""Give each institution the register identifiers that already exist for it (issue #75).

Read-mostly. An institution page can say very little when the organisation has no
Wikipedia article, but that is only the prose. The structured facts are usually
recorded somewhere authoritative already, and the directory simply does not hold
the pointer.

Two sources, in this order:

  Wikidata    for every entry that has an item: the Norwegian organisation number
              (P2333), the ROR identifier (P6782), and the country (P17).
  Enhetsregisteret  to check the organisation number resolves, and to read the
              registered name, the website and the size.

Nothing is written on a name match alone. An organisation number is accepted only
when the website the register holds matches the website the directory holds, or
when the entry has no website to compare. That rule matters: Wikidata records the
number of the legal entity, and a research centre inside a university or a
foundation is not one. Two entries here point at their parent, and the check
catches both rather than quietly filing a centre under its owner.

Whatever cannot be settled that way is printed for a person to look at.

Usage:
  python3 scripts/sync_institution_registers.py --dry-run
  python3 scripts/sync_institution_registers.py
  python3 scripts/sync_institution_registers.py --slug notam-norwegian-centre-for-technology-art-and-music
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from directory_io import load_entry, save_entry
from repo_paths import SITE_ROOT

AGENT = {"User-Agent": "mishmash-web/1.0 (+https://mishmash.no; contact@mishmash.no)",
         "Accept": "application/json"}
SPARQL = "https://query.wikidata.org/sparql"
BRREG = "https://data.brreg.no/enhetsregisteret/api/enheter"
BRREG_PAGE = "https://virksomhet.brreg.no/nb/oppslag/enheter/"


def fetch(url: str, tries: int = 3) -> dict | None:
    for attempt in range(tries):
        try:
            request = urllib.request.Request(url, headers=AGENT)
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except Exception:
            if attempt == tries - 1:
                return None
            time.sleep(2)
    return None


def domain(url: str | None) -> str:
    """A website reduced to something two sources can be compared on."""
    if not url:
        return ""
    text = url.strip().lower()
    if "//" not in text:
        text = "//" + text
    host = urllib.parse.urlsplit(text).netloc
    return re.sub(r"^www\.", "", host)


def site_name(url: str | None) -> str:
    """The organisation's own label in its address, without language or country.

    A university writes its Norwegian pages at ntnu.no and its English ones at
    ntnu.edu, and UiT puts English on en.uit.no. Those are the same body. What
    tells two bodies apart is the label itself, which is why simula.no and
    simulamet.no must not compare equal.
    """
    host = domain(url)
    if not host:
        return ""
    parts = [p for p in host.split(".") if p not in ("www", "en", "no", "nb", "nn")]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    # drop the suffix: ntnu.edu and ntnu.no both reduce to ntnu
    return parts[-2] if parts[-1] in ("no", "com", "org", "net", "edu", "io", "de", "dk", "se") else parts[0]


def from_wikidata(qids: list[str]) -> dict[str, dict]:
    """One query for the lot: organisation number, ROR and country."""
    values = " ".join(f"wd:{q}" for q in qids)
    query = f"""SELECT ?item ?countryLabel ?orgnr ?ror WHERE {{
      VALUES ?item {{ {values} }}
      OPTIONAL {{ ?item wdt:P17 ?country. }}
      OPTIONAL {{ ?item wdt:P2333 ?orgnr. }}
      OPTIONAL {{ ?item wdt:P6782 ?ror. }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,no". }}
    }}"""
    data = fetch(f"{SPARQL}?{urllib.parse.urlencode({'query': query, 'format': 'json'})}")
    if not data:
        return {}
    out: dict[str, dict] = {}
    for row in data["results"]["bindings"]:
        qid = row["item"]["value"].rsplit("/", 1)[-1]
        entry = out.setdefault(qid, {})
        for key in ("countryLabel", "orgnr", "ror"):
            if key in row:
                entry[key] = row[key]["value"]
    return out


def registered(number: str) -> dict | None:
    return fetch(f"{BRREG}/{number}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(SITE_ROOT))
    parser.add_argument("--slug", action="append")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    folder = Path(args.root).resolve() / "_directory" / "institutions"
    slugs = sorted(args.slug) if args.slug else sorted(
        child.name for child in folder.iterdir()
        if child.is_dir() and not child.name.startswith("_") and (child / "index.md").exists()
    )

    entries = {}
    for slug in slugs:
        data, body = load_entry(folder / slug / "index.md")
        entries[slug] = (data, body)

    qids = {}
    for slug, (data, _) in entries.items():
        url = (data.get("urls") or {}).get("wikidata") or ""
        qid = url.rstrip("/").rsplit("/", 1)[-1]
        if qid.startswith("Q"):
            qids[slug] = qid
    print(f"{len(entries)} institutions, {len(qids)} with a Wikidata item")

    facts = from_wikidata(sorted(set(qids.values())))
    print(f"Wikidata answered for {len(facts)} items\n")

    written = checked = flagged = 0
    for slug, (data, body) in entries.items():
        qid = qids.get(slug)
        fact = facts.get(qid, {}) if qid else {}
        urls = data.setdefault("urls", {})
        changes = []

        if fact.get("countryLabel") and not data.get("country"):
            data["country"] = fact["countryLabel"]
            changes.append("country")

        if fact.get("ror") and not urls.get("ror"):
            urls["ror"] = f"https://ror.org/{fact['ror']}"
            changes.append("ror")

        number = fact.get("orgnr")
        if number and not urls.get("brreg"):
            checked += 1
            entity = registered(number)
            time.sleep(0.2)
            if not entity or entity.get("error"):
                print(f"  {slug}: {number} does not resolve in the register")
                flagged += 1
            else:
                ours = site_name((data.get("urls") or {}).get("website"))
                theirs = site_name(entity.get("hjemmeside"))
                if not theirs:
                    print(f"  {slug}: the register holds no website for {number} "
                          f"({entity.get('navn')}), so nothing confirms it is this body "
                          f"rather than its parent. Left for a person.")
                    flagged += 1
                elif ours and theirs != ours:
                    print(f"  {slug}: the register has {number} as {entity.get('navn')} "
                          f"at {theirs}, but the directory says {ours}. Left alone.")
                    flagged += 1
                else:
                    urls["brreg"] = BRREG_PAGE + number
                    changes.append("brreg")

        if changes:
            if not args.dry_run:
                save_entry(folder / slug / "index.md", data, body)
            written += 1
            print(f"{'would set' if args.dry_run else 'set'} {slug}: {', '.join(changes)}")

    print(f"\n{written} entries updated, {checked} organisation numbers checked, {flagged} left for a person")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
