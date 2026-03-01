#!/usr/bin/env python3
"""Fetch and parse event pages (UIO / Ritmo style) and emit event metadata or Jekyll markdown files.

Usage examples:
  python3 scripts/fetch_uio_events.py "https://.../deichman/index.html" --out-dir _events
  python3 scripts/fetch_uio_events.py urls.txt --from-file --out-dir scripts/output

The parser uses heuristics: `og:` meta tags, <h1>, <time> tags, common date strings and article/body text.
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def fetch(url: str, timeout=15):
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def text_or_none(node):
    if not node:
        return None
    return node.get_text(separator=" ", strip=True)


def find_date_strings(soup: BeautifulSoup):
    # Collect candidate date strings from <time>, meta, and visible text
    candidates = []
    for t in soup.find_all("time"):
        txt = t.get_text(separator=" ", strip=True)
        if txt:
            candidates.append(txt)
    for meta in (soup.find_all("meta") or []):
        if meta.get("property") in ("article:published_time", "og:published_time") or meta.get("name") in (
            "date",
            "dc.date",
        ):
            if meta.get("content"):
                candidates.append(meta["content"]) 
    # also search for common date patterns in headings/paragraphs
    body_text = text_or_none(soup.body) or ""
    # simple pattern to pick up '12 March 2025' or 'March 12, 2025' etc
    date_pattern = r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b|\b[A-Za-z]+\s+\d{1,2},?\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b"
    matches = re.findall(date_pattern, body_text)
    candidates.extend(matches)
    return candidates


def parse_date(candidates):
    for c in candidates:
        try:
            dt = dateparser.parse(c, fuzzy=True, dayfirst=True)
            return dt
        except Exception:
            continue
    return None


def parse_event(html: str, url: str):
    soup = BeautifulSoup(html, "html.parser")
    data = {"source_url": url}

    # Title: try og:title, then h1
    title = None
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        title = og["content"].strip()
    if not title:
        h1 = soup.find("h1")
        title = text_or_none(h1)
    data["title"] = title

    # Image
    ogimg = soup.find("meta", property="og:image")
    if ogimg and ogimg.get("content"):
        data["image"] = ogimg["content"]

    # Description / excerpt
    desc = None
    ogd = soup.find("meta", property="og:description")
    if ogd and ogd.get("content"):
        desc = ogd["content"].strip()
    if not desc:
        # first paragraph inside article or main
        article = soup.find("article") or soup.find("main")
        if article:
            p = article.find("p")
            desc = text_or_none(p)
    data["description"] = desc

    # Date/time
    candidates = find_date_strings(soup)
    dt = parse_date(candidates)
    if dt:
        data["start"] = dt.isoformat()

    # Location heuristics: look for elements with class/name 'location', 'venue', or <address>
    loc = None
    loc_candidates = soup.select(".location, .venue, .place, address")
    if loc_candidates:
        loc = text_or_none(loc_candidates[0])
    else:
        # fallback: see if the first paragraph contains 'at' or 'in' followed by capitalized words
        body = text_or_none(soup.body) or ""
        m = re.search(r"(at|in)\s+([A-Z][\w\-\s,]+)", body)
        if m:
            loc = m.group(2).strip()
    data["location"] = loc

    return data


def to_markdown(event: dict, out_dir: str = "_events") -> str:
    title = event.get("title") or "event"
    start = event.get("start")
    date_line = start.split("T")[0] if start else datetime.utcnow().date().isoformat()
    slug = slugify(title or date_line)
    filename = f"{date_line}-{slug}.md"
    lines = []
    lines.append("---")
    lines.append(f"title: \"{title}\"")
    lines.append(f"date: {date_line}")
    if event.get("location"):
        lines.append(f"location: \"{event.get('location')}\"")
    if event.get("image"):
        lines.append(f"image: \"{event.get('image')}\"")
    lines.append("layout: event")
    lines.append("---\n")
    if event.get("description"):
        lines.append(event.get("description"))
    content = "\n".join(lines)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def main():
    ap = argparse.ArgumentParser(description="Fetch and parse UIO event pages")
    ap.add_argument("urls", nargs="+", help="One or more URLs or a single filename when --from-file is set")
    ap.add_argument("--from-file", action="store_true", help="Treat the single positional arg as a file with URLs, one per line")
    ap.add_argument("--out-dir", default="scripts/output", help="Directory to write markdown files")
    ap.add_argument("--json", action="store_true", help="Print JSON output to stdout instead of writing files")
    args = ap.parse_args()

    url_list = []
    if args.from_file:
        fname = args.urls[0]
        with open(fname, "r", encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if ln:
                    url_list.append(ln)
    else:
        url_list = args.urls

    results = []
    for u in url_list:
        try:
            html = fetch(u)
            ev = parse_event(html, u)
            results.append(ev)
            if args.json:
                print(json.dumps(ev, ensure_ascii=False, indent=2))
            else:
                mdpath = to_markdown(ev, out_dir=args.out_dir)
                print(f"Wrote {mdpath}")
        except Exception as e:
            print(f"Error fetching {u}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
