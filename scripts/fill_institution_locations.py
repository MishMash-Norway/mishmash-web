"""Fill the empty city and country fields of institutions from ROR.

Reads every site/_directory/institutions/*/index.md, and for an entry whose `city` or `country` is
empty or null and which has `urls.ror`, takes the first location in the ROR record (v2 API) and
writes its city and country. Values already set are never overwritten, so a hand correction stays.
The search page uses these fields for its location filter, and people inherit them from their
institution.

Run: python3 scripts/fill_institution_locations.py [--dry-run]
"""
import argparse
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "site" / "_directory" / "institutions"
EMPTY = {"", "null", "~", "''", '""'}


def field(text, name):
    m = re.search(rf"^{name}:[ \t]*(.*)$", text, flags=re.M)
    return None if m is None else m.group(1).strip()


def set_field(text, name, value):
    line = f"{name}: {json.dumps(value, ensure_ascii=False) if ':' in value else value}"
    if re.search(rf"^{name}:", text, flags=re.M):
        return re.sub(rf"^{name}:.*$", line, text, count=1, flags=re.M)
    head, sep, rest = text.partition("\n---")
    return head + "\n" + line + sep + rest


def ror_location(ror_url):
    rid = ror_url.rstrip("/").rsplit("/", 1)[-1]
    req = urllib.request.Request(f"https://api.ror.org/v2/organizations/{rid}",
                                 headers={"User-Agent": "mishmash-web location fill"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    locs = data.get("locations") or []
    if not locs:
        return None, None
    g = locs[0].get("geonames_details") or {}
    return g.get("name"), g.get("country_name")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    filled, missing = 0, []
    for md in sorted(ROOT.glob("*/index.md")):
        if md.parent.name.startswith("_"):
            continue
        text = md.read_text()
        city, country = field(text, "city"), field(text, "country")
        need_city = city is None or city in EMPTY
        need_country = country is None or country in EMPTY
        if not (need_city or need_country):
            continue
        ror = re.search(r"^\s+ror:\s*(\S+)", text, flags=re.M)
        if not ror or ror.group(1) in EMPTY:
            missing.append(md.parent.name)
            continue
        try:
            rc, rn = ror_location(ror.group(1))
        except Exception as e:  # network or API error: report and go on
            print(f"{md.parent.name}: ROR failed ({e})", file=sys.stderr)
            continue
        new = text
        if need_city and rc:
            new = set_field(new, "city", rc)
        if need_country and rn:
            new = set_field(new, "country", rn)
        if new != text:
            filled += 1
            print(f"{md.parent.name}: city={rc if need_city else city}, country={rn if need_country else country}")
            if not args.dry_run:
                md.write_text(new)
        time.sleep(0.2)
    print(f"filled {filled}; without ROR and still missing a location: {len(missing)}")
    for s in missing:
        print(f"  {s}")


if __name__ == "__main__":
    main()
