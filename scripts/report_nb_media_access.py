#!/usr/bin/env python3
"""What can a page on another site actually play from the National Library? (issue #74)

Read-only. The heritage lab shows pictures from collections by fetching the
record in the reader's browser and letting the collection's own server deliver
the file. Sound and film from Norwegian collections do not work that way yet,
and this script measures why, so that the conversation with a collection can
start from what is served rather than from an assumption.

For each media type it reports:

  total        items in the catalogue
  public       items in contentClasses:public, which is what the search
               interface calls viewability=ALL
  digital      how many of a sample of public items carry digital content
               rather than a catalogue record alone
  licences     what accessInfo.license says across that sample

It then takes one public item per media type, reads the IIIF presentation
manifest, and reports the type and address of the content body. A Sound or
Video body means the metadata side is solved: the manifest already says where
the file is and what the rights statement is.

Whether the file can be played from another site is a separate question, and
this script does not answer it from Python, since the answer depends on the
browser. Run tests/nb-media-access.mjs for that.

Usage:
  python3 scripts/report_nb_media_access.py [--out report.json] [--sample 60]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from urllib.request import urlopen

API = "https://api.nb.no/catalog/v1/items"
MEDIA_TYPES = ["radio", "musikk", "lydopptak", "noter", "film", "fjernsyn", "bilder"]


def get(url: str, tries: int = 3) -> dict | None:
    for attempt in range(tries):
        try:
            with urlopen(url, timeout=60) as response:
                return json.load(response)
        except Exception:
            if attempt == tries - 1:
                return None
            time.sleep(2)
    return None


def count(**filters: str) -> int | None:
    query = "&".join(f"filter={key}:{value}" for key, value in filters.items())
    data = get(f"{API}?{query}&size=0")
    if data is None:
        return None
    return data.get("page", {}).get("totalElements")


def sample_public(media_type: str, wanted: int) -> tuple[int, int, Counter, list[dict]]:
    """Walk public items in pages of 20 and report how many carry content."""
    seen = digital = 0
    licences: Counter = Counter()
    items: list[dict] = []
    page = 0
    while seen < wanted:
        data = get(
            f"{API}?filter=mediatype:{media_type}&filter=contentClasses:public"
            f"&size=20&page={page}"
        )
        if data is None:
            break
        batch = data.get("_embedded", {}).get("items", [])
        if not batch:
            break
        for item in batch:
            access = item.get("accessInfo", {})
            seen += 1
            if access.get("isDigital"):
                digital += 1
                items.append(item)
            licences[access.get("license")] += 1
        page += 1
    return seen, digital, licences, items


def manifest_bodies(item: dict) -> list[dict]:
    """The content resources a IIIF v3 manifest points at, if there are any."""
    href = item.get("_links", {}).get("presentation", {}).get("href")
    if not href:
        return []
    manifest = get(href.replace(":443", ""))
    if manifest is None:
        return []
    out = []
    for canvas in manifest.get("items", []):
        for page in canvas.get("items", []):
            for annotation in page.get("items", []):
                body = annotation.get("body", {})
                out.append(
                    {
                        "type": body.get("type"),
                        "id": body.get("id"),
                        "duration": canvas.get("duration"),
                        "rights": manifest.get("rights"),
                    }
                )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="write the report as JSON to this path")
    parser.add_argument("--sample", type=int, default=60, help="public items to sample")
    args = parser.parse_args()

    report = {"api": API, "media_types": {}}
    for media_type in MEDIA_TYPES:
        total = count(mediatype=media_type)
        public = count(mediatype=media_type, contentClasses="public")
        seen, digital, licences, with_content = sample_public(media_type, args.sample)
        entry = {
            "total": total,
            "public": public,
            "sampled": seen,
            "digital_in_sample": digital,
            "licences_in_sample": dict(licences),
            "bodies": [],
        }
        if with_content:
            entry["bodies"] = manifest_bodies(with_content[0])[:1]
            entry["example_id"] = with_content[0].get("id")
            entry["example_title"] = with_content[0].get("metadata", {}).get("title")
        report["media_types"][media_type] = entry

        share = f"{digital}/{seen}" if seen else "no sample"
        body = entry["bodies"][0]["type"] if entry["bodies"] else "-"
        print(
            f"{media_type:<18} total {total:>9}  public {public:>8}  "
            f"digital in sample {share:>7}  body {body}"
        )

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
        print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
