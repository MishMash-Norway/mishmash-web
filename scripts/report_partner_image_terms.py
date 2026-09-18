#!/usr/bin/env python3
"""Do the partners say anything about reusing their pictures? (issue #73)

Read-only. The site shows a thumbnail beside every partner news item and
event, fetched from the partner's own server. Whether a copy could be kept
here instead is a copyright question, and the answer starts with what each
partner actually publishes about reuse.

For every partner page behind a thumbnail this script fetches the page and
looks for four signals, then reports them per host:

  licence      a link to a Creative Commons licence, or a rights field in the
               page metadata
  credit       a photo credit line ("Foto:", "Photo:", "Photographer")
  terms page   a link whose text or address suggests copyright or terms of use
  nothing      none of the above found

A signal is not permission. A credit line tells a reader who took the
photograph, not what may be done with it, and a terms page may forbid reuse.
The report says what is stated, so that a conversation with the partners can
start from facts rather than from an assumption.

Usage:
  python3 scripts/report_partner_image_terms.py [--out report.md] [--delay 1.0]
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

UA = {"User-Agent": "Mozilla/5.0 (compatible; MishMash-web/1.0; +https://mishmash.no)",
      "Accept": "text/html,application/xhtml+xml"}

CC_RE = re.compile(r"creativecommons\.org/(licenses|publicdomain)/([a-z0-9-]+)", re.I)
RIGHTS_META_RE = re.compile(
    r"<meta[^>]+(?:name|property)=[\"'](?:dcterms\.rights|dc\.rights|rights|copyright)[\"'][^>]*content=[\"']([^\"']{3,120})", re.I)
CREDIT_RE = re.compile(r"\b(foto|photo|fotograf|photographer|bilde|image credit)\s*[:：]", re.I)
TERMS_LINK_RE = re.compile(
    r"<a[^>]+href=[\"']([^\"']*(?:copyright|opphavsrett|terms|vilkar|vilk%C3%A5r|vilkår|bruksvilkar|personvern/?bruk|rettigheter)[^\"']*)[\"'][^>]*>([^<]{0,80})", re.I)


def pages_with_thumbnails(site_root: Path) -> list[tuple[str, str]]:
    """(host, page url) for every partner item whose card shows a picture."""
    out = []
    for name in ("partner_news.yml", "partner_events.yml"):
        data = yaml.safe_load((site_root / "_data" / name).read_text(encoding="utf-8")) or []
        for entry in data:
            if entry.get("og_image") and entry.get("url"):
                out.append((urlparse(entry["url"]).netloc, entry["url"]))
    return out


def signals(html: str) -> dict:
    cc = CC_RE.search(html)
    rights = RIGHTS_META_RE.search(html)
    credit = CREDIT_RE.search(html)
    terms = TERMS_LINK_RE.search(html)
    return {
        "licence": (cc.group(0) if cc else None) or (rights.group(1).strip() if rights else None),
        "credit": bool(credit),
        "terms": terms.group(1) if terms else None,
    }


def host_terms(host: str, session: requests.Session, delay: float) -> str | None:
    """A link to a copyright or terms page from the host's front page, if any."""
    for scheme in ("https://",):
        try:
            r = session.get(scheme + host, headers=UA, timeout=30)
        except requests.RequestException:
            return None
        time.sleep(delay)
        if r.status_code != 200:
            return None
        m = TERMS_LINK_RE.search(r.text)
        return m.group(1) if m else None
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()

    pages = pages_with_thumbnails(SITE_ROOT)
    by_host: dict[str, list[dict]] = defaultdict(list)
    session = requests.Session()
    for host, url in pages:
        try:
            r = session.get(url, headers=UA, timeout=30)
            if r.status_code != 200:
                by_host[host].append({"url": url, "error": f"HTTP {r.status_code}"})
            else:
                by_host[host].append({"url": url, **signals(r.text)})
        except requests.RequestException as exc:
            by_host[host].append({"url": url, "error": type(exc).__name__})
        time.sleep(args.delay)

    front_page_terms = {h: host_terms(h, session, args.delay) for h in sorted(by_host)}

    checked = [p for ps in by_host.values() for p in ps if "error" not in p]
    unreachable = [p for ps in by_host.values() for p in ps if "error" in p]
    with_licence = [p for p in checked if p.get("licence")]
    with_credit = [p for p in checked if p.get("credit")]
    with_terms = [p for p in checked if p.get("terms")]
    silent = [p for p in checked if not (p.get("licence") or p.get("credit") or p.get("terms"))]

    hosts_with_licence = {urlparse(p["url"]).netloc for p in with_licence}

    lines = [
        "# What partners say about reusing their pictures", "",
        f"Pages behind a thumbnail: {len(pages)} across {len(by_host)} hosts. "
        f"Read: {len(checked)}. Could not be read: {len(unreachable)}.", "",
        "| Signal | Pages | Hosts |", "| --- | --- | --- |",
        f"| A licence, stated on the page | {len(with_licence)} | {len(hosts_with_licence)} |",
        f"| A photo credit, but no licence | {len([p for p in with_credit if not p.get('licence')])} | "
        f"{len({urlparse(p['url']).netloc for p in with_credit if not p.get('licence')})} |",
        f"| A link to terms or copyright | {len(with_terms)} | {len({urlparse(p['url']).netloc for p in with_terms})} |",
        f"| Nothing found | {len(silent)} | {len({urlparse(p['url']).netloc for p in silent})} |",
        f"| A copyright or terms page linked from the host's front page | | {sum(1 for v in front_page_terms.values() if v)} of {len(front_page_terms)} |", "",
        "A credit line is not permission, and a terms page may forbid reuse. "
        "This is what is stated, not what is allowed.", "",
        "## By host", "",
        "| Host | Pages | Licence | Credit | Terms link | Unreadable |", "| --- | --- | --- | --- | --- | --- |",
    ]
    for host in sorted(by_host, key=lambda h: -len(by_host[h])):
        ps = by_host[host]
        ok = [p for p in ps if "error" not in p]
        lines.append(
            f"| {host} | {len(ps)} | {sum(1 for p in ok if p.get('licence'))} | "
            f"{sum(1 for p in ok if p.get('credit'))} | {sum(1 for p in ok if p.get('terms'))} | "
            f"{len(ps) - len(ok)} |")
    lines += ["", "## A copyright or terms page on the host's front page", ""]
    for host in sorted(front_page_terms):
        link = front_page_terms[host]
        lines.append(f"- {host}: {link if link else 'none found'}")
    if with_licence:
        lines += ["", "## Licences found", ""]
        for p in with_licence:
            lines.append(f"- {urlparse(p['url']).netloc}: {p['licence']}")

    report = "\n".join(lines) + "\n"
    if args.out:
        args.out.write_text(report, encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
