#!/usr/bin/env python3
"""Fetch Open Graph metadata for partner events and enrich _data/partner_events.yml.

For each event that has a URL, fetches og:title, og:description, and og:image
and writes them back into the YAML (preserving all existing fields and ordering).
Re-running is safe: entries that already have og_* fields are skipped unless
--force is passed.

Usage:
  python3 scripts/fetch_partner_og_data.py
  python3 scripts/fetch_partner_og_data.py --force
"""
import argparse
import os
import sys
import re

import requests
from bs4 import BeautifulSoup

YAML_PATH = os.path.join(os.path.dirname(__file__), "..", "_data", "partner_events.yml")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; mishmash-web-bot/1.0)"}
TIMEOUT = 15


def fetch_og(url: str) -> dict:
    """Return a dict with og_title, og_description, og_image (any may be None)."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"  WARNING: could not fetch {url}: {e}", file=sys.stderr)
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")

    def og(prop):
        tag = soup.find("meta", property=f"og:{prop}") or soup.find("meta", attrs={"name": f"og:{prop}"})
        if tag:
            return tag.get("content", "").strip() or None
        return None

    title = og("title") or og("site_name")
    description = og("description")
    image = og("image")

    # fallback title to <title> tag
    if not title:
        t = soup.find("title")
        if t:
            title = t.get_text(strip=True) or None

    # fallback description to <meta name="description">
    if not description:
        m = soup.find("meta", attrs={"name": "description"})
        if m:
            description = m.get("content", "").strip() or None

    result = {}
    if title:
        result["og_title"] = title
    if description:
        result["og_description"] = description
    if image:
        result["og_image"] = image
    return result


def load_raw_yaml(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_raw_yaml(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def inject_og_fields(entry_block: str, og: dict) -> str:
    """Insert og_* fields into a YAML entry block (raw string), after the 'url:' line."""
    if not og:
        return entry_block

    og_lines = ""
    for key in ("og_title", "og_description", "og_image"):
        if key in og:
            val = og[key]
            # Escape double quotes in the value
            val_escaped = val.replace("\\", "\\\\").replace('"', '\\"')
            og_lines += f'  {key}: "{val_escaped}"\n'

    # Insert after the url: line
    return re.sub(r"(  url:.*\n)", r"\1" + og_lines, entry_block, count=1)


def has_og_fields(entry_block: str) -> bool:
    return bool(re.search(r"  og_title:", entry_block))


def split_entries(raw: str):
    """Split raw YAML into (preamble, list_of_entry_strings)."""
    # Entries start with a line beginning with '- '
    parts = re.split(r"(?=^- )", raw, flags=re.MULTILINE)
    preamble = ""
    entries = []
    for p in parts:
        if p.startswith("- "):
            entries.append(p)
        else:
            preamble += p
    return preamble, entries


def get_url(entry_block: str):
    m = re.search(r"  url:\s*(\S+)", entry_block)
    return m.group(1) if m else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="Re-fetch even if og_* fields already exist")
    args = parser.parse_args()

    raw = load_raw_yaml(YAML_PATH)
    preamble, entries = split_entries(raw)

    updated_entries = []
    changed = False

    for entry in entries:
        url = get_url(entry)
        if not url:
            updated_entries.append(entry)
            continue

        if has_og_fields(entry) and not args.force:
            print(f"  skipping (already enriched): {url}")
            updated_entries.append(entry)
            continue

        print(f"  fetching OG data: {url}")
        og = fetch_og(url)
        if og:
            # Remove stale og_ lines first if --force
            if args.force:
                entry = re.sub(r"  og_(?:title|description|image):.*\n", "", entry)
            new_entry = inject_og_fields(entry, og)
            if new_entry != entry:
                changed = True
            updated_entries.append(new_entry)
        else:
            updated_entries.append(entry)

    if changed:
        new_raw = preamble + "".join(updated_entries)
        save_raw_yaml(YAML_PATH, new_raw)
        print("_data/partner_events.yml updated.")
    else:
        print("No changes.")


if __name__ == "__main__":
    main()
