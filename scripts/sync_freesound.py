#!/usr/bin/env python3
"""Collect the facts about a set of Freesound sounds, without an API key (issue #47).

Freesound's API needs a token, which the centre does not have yet, but every sound has a public
page and an oEmbed record. This reads those for the sounds of one user or a given list of ids, and
writes site/_data/freesound.yml: id, title, author, licence, tags, the address of the preview file
and the page it came from. The preview address is served by Freesound when a reader presses play.

Each sound also gets a shape: 128 peak values and a duration, measured here once by decoding the
preview with ffmpeg. The page draws the waveform from those numbers, so a reader sees what a sound
looks like before deciding to fetch it, and Freesound learns nothing about a reader who only looks.
Pass --no-peaks to skip the decoding.

Only sounds under a Creative Commons licence are kept, since the site plays them.

Usage:
  python3 scripts/sync_freesound.py --user alexarje
  python3 scripts/sync_freesound.py --ids 863344,863343
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import struct
import subprocess
import sys
import time
from pathlib import Path
from xml.etree import ElementTree

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

UA = {"User-Agent": "MishMash-web/1.0 (+https://mishmash.no; contact@mishmash.no)"}
OUT = SITE_ROOT / "_data" / "freesound.yml"
LICENCE_LABEL = {
    "by": "CC BY", "by-sa": "CC BY-SA", "by-nc": "CC BY-NC", "by-nc-sa": "CC BY-NC-SA",
    "by-nd": "CC BY-ND", "by-nc-nd": "CC BY-NC-ND", "zero": "CC0", "mark": "public domain",
}


def sound_ids_of_user(user: str, session: requests.Session) -> list[str]:
    r = session.get(f"https://freesound.org/people/{user}/sounds/", headers=UA, timeout=40)
    r.raise_for_status()
    return sorted(set(re.findall(rf"/people/{user}/sounds/(\d+)/", r.text)), key=int)


def licence_of(html: str) -> tuple[str | None, str | None]:
    m = re.search(r"creativecommons\.org/(licenses|publicdomain)/([a-z-]+)/([\d.]+)", html)
    if not m:
        return None, None
    code = m.group(2)
    return LICENCE_LABEL.get(code, code), f"https://{m.group(0)}"


def sound_facts(sid: str, session: requests.Session) -> dict | None:
    page = f"https://freesound.org/people/_/sounds/{sid}/"
    r = session.get(f"https://freesound.org/s/{sid}/", headers=UA, timeout=40, allow_redirects=True)
    if r.status_code != 200:
        return None
    html, page = r.text, r.url
    preview = re.search(r"(https://cdn\.freesound\.org/previews/[^\"'\\ ]+?-hq\.mp3)", html) or \
              re.search(r"(https://cdn\.freesound\.org/previews/[^\"'\\ ]+?-lq\.mp3)", html)
    label, url = licence_of(html)
    if not preview or not label:
        return None
    oe = session.get("https://freesound.org/oembed/", params={"url": page}, headers=UA, timeout=40)
    title, author, description = sid, None, None
    if oe.status_code == 200:
        try:
            root = ElementTree.fromstring(oe.text)
            title = (root.findtext("title") or sid).strip()
            author = (root.findtext("author-name") or "").strip() or None
            description = re.sub(r"\s+", " ", (root.findtext("description") or "")).strip() or None
        except ElementTree.ParseError:
            pass
    return {
        "id": sid, "title": title, "author": author,
        "description": (description or "")[:300] or None,
        "licence": label, "licence_url": url,
        "preview": preview.group(1).replace("-lq.mp3", "-hq.mp3"),
        "page": page,
        "tags": sorted(set(re.findall(r"/browse/tags/([a-z0-9-]+)/", html)))[:8],
    }


PEAKS = 128
RATE = 8000


def shape_of(preview: str, session: requests.Session, count: int = PEAKS) -> tuple[list[int], float] | None:
    """Decode the preview once and reduce it to `count` peaks and a duration.

    A peak rather than a mean, because a sound action is a transient: the interesting
    part of a cork leaving a bottle is 20 ms long and a mean would hide it.
    """
    try:
        audio = session.get(preview, headers=UA, timeout=120)
        audio.raise_for_status()
    except requests.RequestException as err:
        print(f"    could not fetch the preview: {err}", file=sys.stderr)
        return None
    try:
        out = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", "pipe:0",
             "-ac", "1", "-ar", str(RATE), "-f", "f32le", "pipe:1"],
            input=audio.content, capture_output=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as err:
        print(f"    ffmpeg could not decode it: {err}", file=sys.stderr)
        return None
    samples = struct.unpack(f"<{len(out) // 4}f", out[: len(out) // 4 * 4])
    if not samples:
        return None
    duration = len(samples) / RATE
    step = max(1, len(samples) // count)
    peaks = []
    for i in range(count):
        window = samples[i * step:(i + 1) * step] or (0.0,)
        peaks.append(max(abs(v) for v in window))
    loudest = max(peaks) or 1.0
    return [min(255, round(p / loudest * 255)) for p in peaks], round(duration, 2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--user")
    ap.add_argument("--ids", help="comma-separated sound ids")
    ap.add_argument("--delay", type=float, default=0.5)
    ap.add_argument("--no-peaks", action="store_true", help="skip decoding, leave the shapes out")
    args = ap.parse_args()
    session = requests.Session()
    ids = [i.strip() for i in (args.ids or "").split(",") if i.strip()]
    if args.user:
        ids += sound_ids_of_user(args.user, session)
    if not ids:
        print("nothing to fetch: give --user or --ids", file=sys.stderr)
        return 1
    sounds = []
    for sid in ids:
        facts = sound_facts(sid, session)
        if facts:
            if not args.no_peaks:
                shape = shape_of(facts["preview"], session)
                if shape:
                    facts["peaks"], facts["duration"] = shape
            sounds.append(facts)
        else:
            print(f"  {sid}: no preview or no Creative Commons licence, left out")
        time.sleep(args.delay)
    payload = {
        "synced_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "https://freesound.org/ (public sound pages and oEmbed; no API key)",
        "count": len(sounds), "sounds": sounds,
    }
    OUT.write_text("# Generated by scripts/sync_freesound.py. Do not edit.\n" +
                   yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    shaped = sum(1 for s in sounds if s.get("peaks"))
    print(f"freesound: {len(sounds)} sounds, {shaped} with a shape -> {OUT.relative_to(SITE_ROOT.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
