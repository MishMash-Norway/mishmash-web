#!/usr/bin/env python3
"""Collect posts from the feeds members and projects have opted into (issue #59).

A person or project entry may carry a `feeds` list in its front matter:

    feeds:
      - https://example.org/blog/feed.xml

The feeds are fetched, and the newest posts from each are written to
site/_data/member_posts.yml, which the person's or the project's own page
reads: a member who has given a feed gets their latest posts on their
directory page, and nowhere else. Only title, date, link and a short summary
are stored; the reader goes to the source. A feed that fails is skipped and named, and the previous
entries for it are kept, so one broken site does not empty the page.

Two helpers for finding candidates, which change nothing:
  --discover        report which personal websites in the directory expose a feed
  --check URL       report whether one address has a feed

Usage:
  python3 scripts/fetch_member_feeds.py
  python3 scripts/fetch_member_feeds.py --discover --out candidates.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from directory_io import iter_directory_entries
from repo_paths import SITE_ROOT

OUT = SITE_ROOT / "_data" / "member_posts.yml"
UA = {"User-Agent": "MishMash-web-planet/1.0 (https://mishmash.no; contact@mishmash.no)"}
PER_FEED = 5
TIMEOUT = 20
NS = {"atom": "http://www.w3.org/2005/Atom"}
FEED_LINK_RE = re.compile(
    r'<link[^>]+type=["\'](?:application/(?:rss|atom)\+xml)["\'][^>]*>', re.I)
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']', re.I)
COMMON = ["feed.xml", "atom.xml", "rss.xml", "index.xml", "feed/", "feed"]


def text_of(el) -> str:
    return html.unescape("".join(el.itertext())).strip() if el is not None else ""


def parse_date(s: str) -> str | None:
    s = (s or "").strip()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", s)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else None


def parse_feed(xml_text: str) -> list[dict]:
    """Return [{title, url, date, summary}] from an RSS or Atom document."""
    try:
        root = ET.fromstring(xml_text.encode("utf-8", "ignore"))
    except ET.ParseError:
        return []
    posts = []
    for item in root.iter():
        tag = item.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        title = text_of(item.find("title")) or text_of(item.find("atom:title", NS))
        link = text_of(item.find("link"))
        if not link:
            el = item.find("atom:link", NS)
            link = el.get("href") if el is not None else ""
        date = parse_date(text_of(item.find("pubDate")) or text_of(item.find("atom:updated", NS))
                          or text_of(item.find("atom:published", NS)) or text_of(item.find("{http://purl.org/dc/elements/1.1/}date")))
        summary = text_of(item.find("description")) or text_of(item.find("atom:summary", NS))
        summary = re.sub(r"<[^>]+>", " ", summary)
        summary = re.sub(r"\s+", " ", summary).strip()
        if title and link:
            posts.append({"title": title, "url": link, "date": date, "summary": summary[:300] or None})
    return posts


def fetch(url: str) -> str | None:
    try:
        r = requests.get(url, headers=UA, timeout=TIMEOUT)
        return r.text if r.status_code == 200 else None
    except requests.RequestException:
        return None


def discover_feed(site_url: str) -> str | None:
    """Find a feed for a site: the declared one, else a common address."""
    page = fetch(site_url)
    if page:
        m = FEED_LINK_RE.search(page)
        if m:
            href = HREF_RE.search(m.group(0))
            if href:
                return urljoin(site_url, href.group(1))
    for suffix in COMMON:
        candidate = urljoin(site_url.rstrip("/") + "/", suffix)
        body = fetch(candidate)
        if body and ("<rss" in body[:400].lower() or "<feed" in body[:400].lower()):
            return candidate
    return None


def entries_with_feeds(root: Path):
    for section, folder, _index, data, _body in iter_directory_entries(root):
        for feed in data.get("feeds") or []:
            yield section, data.get("slug"), data.get("name") or data.get("title"), feed


def collect(root: Path) -> dict:
    previous = {}
    if OUT.exists():
        for p in (yaml.safe_load(OUT.read_text(encoding="utf-8")) or {}).get("posts") or []:
            previous.setdefault(p.get("feed"), []).append(p)
    posts, failed, sources = [], [], 0
    for section, slug, name, feed in entries_with_feeds(root):
        sources += 1
        body = fetch(feed)
        items = parse_feed(body) if body else []
        if not items:
            failed.append(feed)
            posts += previous.get(feed, [])
            continue
        for it in items[:PER_FEED]:
            posts.append({**it, "feed": feed, "author": name, "author_slug": slug, "section": section,
                          "author_url": f"/{'people' if section == 'people' else 'projects'}/{slug}/"})
    posts.sort(key=lambda p: (p.get("date") or "", p.get("title") or ""), reverse=True)
    return {
        "synced_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "sources": sources,
        "failed": failed,
        "posts": posts[:60],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--discover", action="store_true", help="report which personal websites expose a feed")
    ap.add_argument("--check", metavar="URL")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    if args.check:
        print(discover_feed(args.check) or "no feed found")
        return 0

    if args.discover:
        rows = []
        for section, folder, _i, data, _b in iter_directory_entries(SITE_ROOT):
            if section != "people":
                continue
            site = (data.get("urls") or {}).get("personal_website")
            if not site or not site.strip() or "linkedin.com" in site:
                continue
            feed = discover_feed(site.strip())
            if feed:
                rows.append((data.get("name"), data.get("slug"), site.strip(), feed))
        lines = ["# Members whose personal website exposes a feed", "",
                 f"Found {len(rows)} on {dt.date.today().isoformat()}. Nothing is added to the site: a member opts in by having `feeds` added to their directory entry.", "",
                 "| Person | Website | Feed |", "| --- | --- | --- |"]
        lines += [f"| [{n}](https://mishmash.no/people/{s}/) | [{w.split('//')[-1].split('/')[0]}]({w}) | [{f.split('//')[-1][:60]}]({f}) |" for n, s, w, f in rows]
        text = "\n".join(lines) + "\n"
        (args.out.write_text(text, encoding="utf-8") if args.out else print(text))
        print(f"discover: {len(rows)} feeds found", file=sys.stderr)
        return 0

    result = collect(SITE_ROOT)
    OUT.write_text("# Generated by scripts/fetch_member_feeds.py. Do not edit.\n"
                   + yaml.safe_dump(result, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"member feeds: {len(result['posts'])} posts from {result['sources']} feeds, {len(result['failed'])} failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
