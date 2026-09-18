#!/usr/bin/env python3
"""Collect MishMash members' expositions from the Research Catalogue (issue #28, #49).

The Research Catalogue is where artistic research is published as expositions:
media-rich works with an abstract, a licence, a DOI and a cover image. Two
public interfaces are used, neither needing a key:

  OAI-PMH (/oai)         harvest whole institutional portals, for completeness
  search JSON (/search)  the cover image, licence and abstract for one work

Portals belonging to MishMash partner institutions are harvested, every
creator is matched against the directory (name and aliases), and the matches
are written to site/_data/research_catalogue.yml for the gallery.

Cover images: the thumbnail links the Research Catalogue gives are signed and
expire within about a day, so they are downloaded here instead, but only for
expositions whose licence allows it. An all-rights-reserved exposition is
listed with its title, authors and abstract and a link to the work, without a
copy of its image.

Usage:
  python3 scripts/sync_research_catalogue.py
  python3 scripts/sync_research_catalogue.py --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from directory_io import iter_directory_entries
from repo_paths import SITE_ROOT

OAI = "https://www.researchcatalogue.net/oai"
SEARCH = "https://www.researchcatalogue.net/search"
UA = {"User-Agent": "MishMash-web-sync/1.0 (https://mishmash.no; contact@mishmash.no)"}
OUT = SITE_ROOT / "_data" / "research_catalogue.yml"
IMAGES = SITE_ROOT / "assets" / "images" / "expositions"
TIMEOUT = 60

# Portals of MishMash partner institutions, and the Norwegian artistic research
# venues where members publish. Add a portal by adding a line; the set names come
# from the OAI ListSets response.
PORTALS = {
    "17": "Faculty of Fine Art, Music and Design, University of Bergen",
    "368753": "University of Agder, Faculty of Fine Arts",
    "371609": "Norwegian Academy of Music",
    "541100": "NMH Student Portal",
    "576472": "Norwegian University of Science and Technology",
    "1249785": "University of Inland Norway",
    "589160": "Aalto University",
    "2210882": "KTH Royal Institute of Technology",
    "7": "Norwegian Artistic Research Programme",
    "426674": "VIS - Nordic Journal for Artistic Research",
    "2": "Journal for Artistic Research",
    "10": "RUUKKU - Studies in Artistic Research",
}

# Cover images are copied and shown for works under a Creative Commons licence:
# the thumbnail is redistributed unmodified, the author is named, the licence is
# stated and the work is linked, which is what those licences ask, including the
# non-commercial and no-derivatives ones. Works that reserve all rights, or whose
# licence is not stated, are listed without an image.
IMAGE_OK = {"cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa", "cc-by-nc-nd", "cc-by-nd", "cc0", "public-domain"}
LICENCE_LABEL = {
    "cc-by": "CC BY", "cc-by-sa": "CC BY-SA", "cc-by-nc": "CC BY-NC",
    "cc-by-nc-sa": "CC BY-NC-SA", "cc-by-nc-nd": "CC BY-NC-ND", "cc-by-nd": "CC BY-ND",
    "cc0": "CC0", "public-domain": "public domain", "all-rights-reserved": "all rights reserved",
}


NORDIC = {"ø": "o", "æ": "ae", "å": "a", "ö": "o", "ä": "a", "ü": "u", "ß": "ss", "đ": "d", "ŋ": "ng"}


def norm(name: str) -> str:
    """A name reduced to plain letters, so that spelling and accents do not
    decide whether a creator matches a member. The Nordic letters are
    transliterated first, since they do not decompose."""
    s = (name or "").strip().lower()
    for a, b in NORDIC.items():
        s = s.replace(a, b)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z ]", "", s).strip()


def directory_people(root: Path) -> dict[str, dict]:
    """Every member by normalised name and alias."""
    people: dict[str, dict] = {}
    for section, folder, _i, data, _b in iter_directory_entries(root):
        if section != "people" or data.get("published") is False:
            continue
        entry = {"slug": data["slug"], "name": data.get("name") or data.get("title"), "url": f"/people/{data['slug']}/"}
        for n in [entry["name"], *(data.get("aliases") or [])]:
            if n:
                people[norm(n)] = entry
    return people


def harvest_portal(pid: str) -> list[dict]:
    """Every exposition in one portal, through OAI-PMH."""
    out, token, pages = [], None, 0
    while pages < 20:
        params = {"verb": "ListRecords", "resumptionToken": token} if token else {"verb": "ListRecords", "metadataPrefix": "oai_dc", "set": f"portal-{pid}"}
        r = requests.get(OAI, params=params, headers=UA, timeout=TIMEOUT)
        if r.status_code != 200:
            break
        body = r.text
        for rec in re.findall(r"<record>(.*?)</record>", body, re.S):
            def dc(tag: str) -> list[str]:
                return [html.unescape(x).strip() for x in re.findall(rf"<dc:{tag}>(.*?)</dc:{tag}>", rec, re.S)]
            identifiers = dc("identifier")
            view = next((i for i in identifiers if "/view/" in i), identifiers[0] if identifiers else "")
            doi = next((i for i in identifiers if "doi.org" in i), None)
            title = (dc("title") or [""])[0]
            if not title or not view:
                continue
            out.append({
                "title": title,
                "creators": dc("creator"),
                "abstract": (dc("description") or [""])[0],
                "date": (dc("date") or [""])[0][:10] or None,
                "url": view,
                "doi": doi,
                "rights": (dc("rights") or [None])[0],
                "portal_id": pid,
            })
        m = re.search(r"<resumptionToken[^>]*>([^<]+)</resumptionToken>", body)
        token = m.group(1) if m else None
        pages += 1
        if not token:
            break
        time.sleep(0.4)
    return out


def enrich(exposition: dict) -> dict:
    """Cover image and licence from the search interface, matched on the title."""
    try:
        r = requests.get(SEARCH, params={"format": "json", "fulltext": exposition["title"]}, headers=UA, timeout=TIMEOUT)
        rows = r.json() if r.status_code == 200 else []
    except (requests.RequestException, ValueError):
        return exposition
    want = norm(exposition["title"])[:40]
    for row in rows:
        if norm(row.get("title", ""))[:40] == want:
            exposition["rc_id"] = row.get("id")
            exposition["licence"] = row.get("license") or exposition.get("rights")
            exposition["thumb_url"] = row.get("thumb")
            exposition["keywords"] = row.get("keywords") or []
            if row.get("abstract"):
                exposition["abstract"] = row["abstract"]
            break
    return exposition


def fetch_image(exposition: dict, dry_run: bool) -> str | None:
    """Copy the cover image when the licence allows it; return the site path."""
    licence = (exposition.get("licence") or "").lower()
    if licence not in IMAGE_OK or not exposition.get("thumb_url") or not exposition.get("rc_id"):
        return None
    target = IMAGES / f"rc-{exposition['rc_id']}.jpg"
    if target.exists():
        return f"/assets/images/expositions/{target.name}"
    if dry_run:
        return f"/assets/images/expositions/{target.name}"
    try:
        r = requests.get(exposition["thumb_url"], headers=UA, timeout=TIMEOUT)
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/"):
            return None
        IMAGES.mkdir(parents=True, exist_ok=True)
        target.write_bytes(r.content)
        return f"/assets/images/expositions/{target.name}"
    except requests.RequestException:
        return None


# The gallery shows the centre's own period. An exposition published before
# this year belongs to the author's earlier work, not to MishMash.
MIN_YEAR = 2025


def recent_enough(exp: dict, min_year: int = MIN_YEAR) -> bool:
    """True when the exposition is from the centre's period, or carries no date."""
    date = (exp.get("date") or "").strip()
    if not date:
        return False
    try:
        return int(date[:4]) >= min_year
    except ValueError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    people = directory_people(SITE_ROOT)
    found: dict[str, dict] = {}
    for pid, label in PORTALS.items():
        for exp in harvest_portal(pid):
            members = []
            for creator in exp["creators"]:
                person = people.get(norm(creator))
                if person and person["slug"] not in [m["slug"] for m in members]:
                    members.append(person)
            if not members:
                continue
            exp["members"] = members
            exp["portal"] = label
            found.setdefault(exp["url"], exp)
        time.sleep(0.4)

    expositions = []
    skipped_old = 0
    for exp in sorted(found.values(), key=lambda e: e.get("date") or "", reverse=True):
        if not recent_enough(exp):
            skipped_old += 1
            continue
        exp = enrich(exp)
        image = fetch_image(exp, args.dry_run)
        # The OAI rights field sometimes holds a rights holder's name rather than
        # a licence, so only a known licence code counts as one.
        licence = (exp.get("licence") or exp.get("rights") or "").lower().strip()
        if licence not in LICENCE_LABEL:
            licence = ""
        expositions.append({
            "title": exp["title"],
            "url": exp["url"],
            "doi": exp.get("doi"),
            "date": exp.get("date"),
            "creators": exp["creators"],
            "members": exp["members"],
            "abstract": re.sub(r"\s+", " ", exp.get("abstract") or "")[:400] or None,
            "keywords": (exp.get("keywords") or [])[:6],
            "portal": exp["portal"],
            "licence": licence or None,
            "licence_label": LICENCE_LABEL.get(licence, licence or None),
            "image": image,
        })
        time.sleep(0.3)

    print(f"sync_research_catalogue: {skipped_old} expositions from before {MIN_YEAR} left out")
    payload = {
        "synced_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "https://www.researchcatalogue.net/",
        "portals": list(PORTALS.values()),
        "count": len(expositions),
        "from_year": MIN_YEAR,
        "expositions": expositions,
    }
    text = "# Generated by scripts/sync_research_catalogue.py. Do not edit.\n" + yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    if args.dry_run:
        print(text[:3000])
    else:
        OUT.write_text(text, encoding="utf-8")
    with_image = sum(1 for e in expositions if e["image"])
    print(f"research catalogue: {len(expositions)} expositions by members, {with_image} with a cover image we may show")
    return 0


if __name__ == "__main__":
    sys.exit(main())
