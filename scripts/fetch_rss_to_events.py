#!/usr/bin/env python3
"""
Fetch RSS/Atom feeds and create Jekyll `_events/` markdown files for new items.

Usage:
  pip install -r scripts/requirements.txt
  python3 scripts/fetch_rss_to_events.py --feeds scripts/rss_feeds.txt

The feeds file should list one feed URL per line. Blank lines and lines
starting with # are ignored. Optionally a label can follow the URL after a
space and will be recorded as `source` in the front matter.
"""
from __future__ import annotations

import argparse
import os
import re
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

import feedparser
import requests


BASE_DIR = Path(__file__).resolve().parents[1]
EVENTS_DIR = BASE_DIR / "_events"


def slugify(value: str) -> str:
    value = unescape(value)
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"[\s-]+", "-", value).strip("-")
    return value[:80]


def existing_links() -> set[str]:
    links = set()
    if not EVENTS_DIR.exists():
        return links
    for p in EVENTS_DIR.glob("*.md"):
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        m = re.search(r"^original_link:\s*(.+)$", text, re.MULTILINE)
        if m:
            links.add(m.group(1).strip())
    return links


def ensure_events_dir() -> None:
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)


def parse_date(entry) -> datetime:
    # Try common properties
    for key in ("published", "updated", "created"):
        if key in entry:
            try:
                return parsedate_to_datetime(entry[key])
            except Exception:
                pass
    # feedparser provides published_parsed as struct_time sometimes
    if getattr(entry, "published_parsed", None):
        return datetime.fromtimestamp(time.mktime(entry.published_parsed))
    return datetime.utcnow()


def write_event(entry, source_label: str | None) -> Path:
    title = entry.get("title", "(no title)")
    link = entry.get("link", "")
    date = parse_date(entry)
    slug = slugify(title)
    filename = f"{date.strftime('%Y-%m-%d')}-{slug}.md"
    dest = EVENTS_DIR / filename

    front = ["---"]
    front.append(f"title: \"{title.replace('"', '\\"')}\"")
    front.append(f"date: {date.isoformat()}")
    if source_label:
        front.append(f"source: \"{source_label.replace('"', '\\"')}\"")
    if link:
        front.append(f"original_link: {link}")
    front.append("external: true")
    front.append("---")

    content = entry.get("summary", entry.get("content", ""))
    if isinstance(content, list):
        content = content[0].get("value", "")
    body = "\n\n" + (content or "")

    dest.write_text("\n".join(front) + body, encoding="utf-8")
    return dest


def fetch_feed(url: str) -> feedparser.FeedParserDict:
    resp = requests.get(url, timeout=20, headers={"User-Agent": "mishmash-rss-fetcher/1.0"})
    resp.raise_for_status()
    return feedparser.parse(resp.content)


def load_feeds_file(path: Path) -> list[tuple[str, str | None]]:
    feeds: list[tuple[str, str | None]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        url = parts[0]
        label = parts[1].strip() if len(parts) > 1 else None
        feeds.append((url, label))
    return feeds


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch RSS feeds into _events/")
    parser.add_argument("--feeds", type=Path, default=Path("scripts/rss_feeds.txt"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    feeds_file = args.feeds
    if not feeds_file.exists():
        print(f"Feeds file not found: {feeds_file}")
        return

    feeds = load_feeds_file(feeds_file)
    if not feeds:
        print("No feeds configured in", feeds_file)
        return

    ensure_events_dir()
    seen = existing_links()
    added = 0

    for url, label in feeds:
        print("Fetching", url)
        try:
            parsed = fetch_feed(url)
        except Exception as e:
            print("  Failed to fetch:", e)
            continue

        feed_title = parsed.feed.get("title") if parsed.feed else None
        source_label = label or feed_title

        for entry in parsed.entries:
            link = entry.get("link", "")
            if not link:
                continue
            if link in seen:
                # skip already imported entry
                continue
            if args.dry_run:
                print(f"  Would add: {entry.get('title','(no title)')} - {link}")
                added += 1
                seen.add(link)
                continue
            try:
                path = write_event(entry, source_label)
                print("  Added:", path.name)
                added += 1
                seen.add(link)
            except Exception as e:
                print("  Failed to write entry:", e)

    print(f"Done. Added {added} new event(s).")


if __name__ == "__main__":
    main()
