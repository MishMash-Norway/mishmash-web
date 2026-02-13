#!/usr/bin/env python3
"""Retry downloading logos for partner sites that don't yet have saved logos.

This script checks `index.md` for partner URLs, skips domains with existing
logo files in `assets/images/logos/partners/`, and applies extra heuristics to
fetch logos for the remaining domains.

Usage: python3 scripts/retry_failed_logos.py
"""
import os
import re
import time
from urllib import request, parse

ROOT = os.path.dirname(os.path.dirname(__file__))
INDEX = os.path.join(ROOT, 'index.md')
OUTDIR = os.path.join(ROOT, 'assets', 'images', 'logos', 'partners')

os.makedirs(OUTDIR, exist_ok=True)

def read_index_urls(path):
    text = open(path, 'r', encoding='utf-8').read()
    urls = re.findall(r'href=["\'](https?://[^"\']+)["\']', text)
    urls = [u for u in urls if not u.startswith('mailto:')]
    seen = []
    for u in urls:
        if u not in seen:
            seen.append(u)
    return seen

def domain_from_url(u):
    p = parse.urlparse(u)
    return p.netloc.replace(':', '_')

def saved_exists(domain):
    # check for any file starting with domain.* in OUTDIR
    for fn in os.listdir(OUTDIR):
        if fn.startswith(domain + '.'):
            return True
    return False

def try_fetch(url, timeout=12):
    try:
        req = request.Request(url, headers={'User-Agent': 'mishmash-logo-retry/1.0'})
        with request.urlopen(req, timeout=timeout) as r:
            return r.read(), r.headers.get('Content-Type', '')
    except Exception:
        return None, None

def save(data, content_type, domain, candidate_url):
    if not data:
        return False
    ext = 'png'
    ct = (content_type or '').lower()
    if 'svg' in ct or candidate_url.endswith('.svg'):
        ext = 'svg'
    elif 'png' in ct or candidate_url.endswith('.png'):
        ext = 'png'
    elif 'jpeg' in ct or 'jpg' in ct or candidate_url.endswith('.jpg') or candidate_url.endswith('.jpeg'):
        ext = 'jpg'
    else:
        # fallback from path
        p = parse.urlparse(candidate_url).path
        if '.' in p:
            ext = p.rsplit('.', 1)[1]
    fname = f"{domain}.{ext}"
    out = os.path.join(OUTDIR, fname)
    with open(out, 'wb') as f:
        f.write(data)
    return True

COMMON_PATHS = [
    '/favicon.ico', '/favicon.png', '/favicon.svg', '/logo.svg', '/logo.png',
    '/assets/logo.svg', '/assets/logo.png', '/images/logo.svg', '/images/logo.png',
    '/img/logo.svg', '/img/logo.png', '/static/logo.svg', '/static/logo.png'
]

def retry_domain(url):
    print('Retrying', url)
    p = parse.urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    domain = domain_from_url(url)

    # try homepage https first (already tried once probably)
    candidates = []
    candidates.append(base)
    candidates.append(base + '/')
    # try http if https may have blocked
    other_scheme = 'http' if p.scheme == 'https' else 'https'
    candidates.append(f"{other_scheme}://{p.netloc}")
    # common paths
    for path in COMMON_PATHS:
        candidates.append(base + path)

    # small crawl: fetch homepage and look for <link rel="icon"> or og:image
    data, ct = try_fetch(base)
    if data:
        html = data.decode('utf-8', errors='replace')
        m = re.search(r'content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']', html, re.I)
        if m:
            candidates.append(parse.urljoin(base, m.group(1)))
        m2 = re.search(r'href=["\']([^"\']+)["\'][^>]*rel=["\'](?:shortcut icon|icon)["\']', html, re.I)
        if m2:
            candidates.append(parse.urljoin(base, m2.group(1)))

    # dedupe preserve order
    seen = set()
    dedup = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            dedup.append(c)

    for cand in dedup:
        data, ct = try_fetch(cand)
        if data:
            if save(data, ct, domain, cand):
                print('  saved', domain, 'from', cand)
                return True
        time.sleep(0.3)
    print('  still failed for', domain)
    return False

def main():
    urls = read_index_urls(INDEX)
    to_retry = []
    for u in urls:
        d = domain_from_url(u)
        if not saved_exists(d):
            to_retry.append(u)

    print('Domains to retry:', len(to_retry))
    succ = 0
    for u in to_retry:
        try:
            if retry_domain(u):
                succ += 1
        except Exception as e:
            print(' error', e)
        time.sleep(0.5)
    print('Retry done. new logos saved:', succ)

if __name__ == '__main__':
    main()
