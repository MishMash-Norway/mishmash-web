#!/usr/bin/env python3
"""Provenance markers for images the site generates (issue #55).

Every generated image carries an IPTC digital source type in its XMP metadata,
so that readers, tools and crawlers can tell how it was made:
  algorithmicMedia         drawn by a script without a trained model (the bubbles)
  trainedAlgorithmicMedia  made by an AI model
plus the creator, the licence and the terms page. SVG files get a <metadata>
block written by the generator or by this script; raster files are marked with
exiftool where it is installed.

The files to mark are listed in site/_data/generated_images.yml. CI runs
--check and fails when a listed file lacks the marker.

Usage:
  python3 scripts/image_provenance.py --mark    # add or refresh markers on listed files
  python3 scripts/image_provenance.py --check   # exit 1 if a listed file has no marker
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

LIST = SITE_ROOT / "_data" / "generated_images.yml"
CV = "http://cv.iptc.org/newscodes/digitalsourcetype/"
SOURCE_TYPES = {"algorithmicMedia", "trainedAlgorithmicMedia", "compositeSynthetic", "digitalCapture"}
CREATOR = "MishMash Centre for AI and Creativity"
RIGHTS = "CC BY 4.0"
TERMS = "https://mishmash.no/about/terms/"


def xmp_block(source_type: str, description: str, creator: str = CREATOR, rights: str = RIGHTS, terms: str = TERMS) -> str:
    assert source_type in SOURCE_TYPES, source_type
    return f"""<metadata>
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" xmlns:xmpRights="http://ns.adobe.com/xap/1.0/rights/">
    <rdf:Description rdf:about="">
      <dc:creator><rdf:Seq><rdf:li>{creator}</rdf:li></rdf:Seq></dc:creator>
      <dc:description><rdf:Alt><rdf:li xml:lang="x-default">{description}</rdf:li></rdf:Alt></dc:description>
      <dc:rights><rdf:Alt><rdf:li xml:lang="x-default">{rights}</rdf:li></rdf:Alt></dc:rights>
      <xmpRights:WebStatement>{terms}</xmpRights:WebStatement>
      <Iptc4xmpExt:DigitalSourceType>{CV}{source_type}</Iptc4xmpExt:DigitalSourceType>
    </rdf:Description>
  </rdf:RDF>
</metadata>"""


def add_svg_metadata(svg: str, xmp: str) -> str:
    """Insert the metadata block after the opening <svg> tag, replacing any existing one."""
    svg = re.sub(r"\s*<metadata>.*?</metadata>", "", svg, flags=re.S)
    m = re.search(r"<svg\b[^>]*>", svg)
    if not m:
        raise ValueError("no <svg> tag")
    return svg[: m.end()] + "\n" + xmp + svg[m.end():]


def svg_source_type(svg: str) -> str | None:
    m = re.search(r"DigitalSourceType>\s*" + re.escape(CV) + r"(\w+)", svg)
    return m.group(1) if m else None


def raster_source_type(path: Path) -> str | None:
    if not shutil.which("exiftool"):
        return None
    out = subprocess.run(["exiftool", "-s3", "-XMP-iptcExt:DigitalSourceType", str(path)], capture_output=True, text=True).stdout.strip()
    return out.rsplit("/", 1)[-1] if out else None


def mark_raster(path: Path, source_type: str, description: str) -> bool:
    if not shutil.which("exiftool"):
        print(f"exiftool not installed; cannot mark {path}", file=sys.stderr)
        return False
    subprocess.run(["exiftool", "-overwrite_original", "-q",
                    f"-XMP-iptcExt:DigitalSourceType={CV}{source_type}",
                    f"-XMP-dc:Creator={CREATOR}", f"-XMP-dc:Description={description}",
                    f"-XMP-dc:Rights={RIGHTS}", f"-XMP-xmpRights:WebStatement={TERMS}", str(path)], check=True)
    return True


def load_list() -> list[dict]:
    return (yaml.safe_load(LIST.read_text(encoding="utf-8")) or {}).get("images") or []


def mark(entries: list[dict]) -> int:
    n = 0
    for e in entries:
        path = SITE_ROOT / e["path"].lstrip("/")
        if not path.exists():
            print(f"missing: {path}", file=sys.stderr)
            continue
        if path.suffix == ".svg":
            path.write_text(add_svg_metadata(path.read_text(encoding="utf-8"), xmp_block(e["source_type"], e["description"])), encoding="utf-8")
            n += 1
        elif mark_raster(path, e["source_type"], e["description"]):
            n += 1
    return n


def check(entries: list[dict]) -> list[str]:
    problems = []
    for e in entries:
        path = SITE_ROOT / e["path"].lstrip("/")
        if not path.exists():
            problems.append(f"{e['path']}: file missing")
            continue
        found = svg_source_type(path.read_text(encoding="utf-8")) if path.suffix == ".svg" else raster_source_type(path)
        if found != e["source_type"]:
            problems.append(f"{e['path']}: expected {e['source_type']}, found {found}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mark", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    entries = load_list()
    if args.mark:
        print(f"provenance: marked {mark(entries)} of {len(entries)} listed images")
    if args.check:
        problems = check(entries)
        for p in problems:
            print("provenance:", p, file=sys.stderr)
        print(f"provenance: {len(entries) - len(problems)} of {len(entries)} listed images carry their marker")
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
