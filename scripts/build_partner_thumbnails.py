#!/usr/bin/env python3
"""Keep a small copy of each partner picture, served from this site (issue #73).

The partner news and partner events listings show the picture a partner's own
page names in its open-graph tags. Fetched from the partner at page view, that
was two costs at once: the partner saw every reader's address, and the reader
was sent the partner's full-size image at thumbnail size, 17 MB for the events
page measured on 26 September 2026. The decision on 26 September 2026 was to
copy each picture once, at harvest, as a 240 px square WebP, and serve that.

For every record in site/_data/partner_events.yml and partner_news.yml with an
og_image, this fetches the picture, fits it to the square, writes it to
site/assets/images/partner-thumbs/<hash of the address>.webp, and records on
the entry:

  thumb          the path served
  thumb_source   the address the copy was made from
  thumb_fetched  the date

The source and the partner beside it are the attribution; the listing card
names the partner. A picture that cannot be fetched or read leaves the record
as it was, and the listing falls back to the partner's address for that one.
Re-running is safe: a record whose og_image has not changed is skipped, and a
copy whose record is gone is removed.

Usage:
  python3 scripts/build_partner_thumbnails.py            # fetch what is missing
  python3 scripts/build_partner_thumbnails.py --force    # fetch everything again
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import sys
from io import BytesIO
from pathlib import Path

import requests
import yaml
from PIL import Image, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

FILES = [SITE_ROOT / "_data" / "partner_events.yml", SITE_ROOT / "_data" / "partner_news.yml"]
OUT = SITE_ROOT / "assets" / "images" / "partner-thumbs"
SIZE = 240
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; mishmash-web-bot/1.0; +https://mishmash.no/)"}


def thumb_path(source: str) -> Path:
    return OUT / (hashlib.sha1(source.encode("utf-8")).hexdigest()[:16] + ".webp")


def make(source: str, dst: Path) -> bool:
    try:
        r = requests.get(source, headers=HEADERS, timeout=30)
        r.raise_for_status()
        with Image.open(BytesIO(r.content)) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA" if "transparency" in im.info else "RGB")
            im = ImageOps.fit(im, (SIZE, SIZE), method=Image.LANCZOS)
            im.save(dst, "WEBP", quality=80, method=6)
        return True
    except Exception as exc:  # a partner's server or picture is theirs to fix
        print(f"  could not copy {source[:80]}: {exc}", file=sys.stderr)
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true", help="fetch every picture again")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    wanted: set[Path] = set()
    made = kept = failed = 0
    for path in FILES:
        if not path.exists():
            continue
        records = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        changed = False
        for rec in records:
            source = (rec.get("og_image") or "").strip()
            if not source.startswith("http"):
                continue
            dst = thumb_path(source)
            wanted.add(dst)
            if not args.force and rec.get("thumb_source") == source and dst.exists():
                kept += 1
                continue
            if make(source, dst):
                rec["thumb"] = "/assets/images/partner-thumbs/" + dst.name
                rec["thumb_source"] = source
                rec["thumb_fetched"] = today
                made += 1
                changed = True
            else:
                failed += 1
        if changed:
            path.write_text(yaml.safe_dump(records, allow_unicode=True, sort_keys=True, width=100), encoding="utf-8")
    removed = 0
    for old in OUT.glob("*.webp"):
        if old not in wanted:
            old.unlink()
            removed += 1
    total_kb = sum(p.stat().st_size for p in OUT.glob("*.webp")) // 1024
    print(f"partner thumbnails: {made} copied, {kept} kept, {failed} failed, {removed} removed; {total_kb} KB in {OUT.relative_to(SITE_ROOT.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
