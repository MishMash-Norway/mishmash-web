#!/usr/bin/env python3
"""Find and download .svg and .ico files for partner domains listed in index.md.

Saves files into `assets/images/logos/partners/` as `domain.svg` and/or
`domain.ico` when found.

Usage: python3 scripts/find_svg_ico.py
"""
import os
import re
import time
from urllib import request, parse

ROOT = os.path.dirname(os.path.dirname(__file__))
INDEX = os.path.join(ROOT, 'index.md')
OUTDIR = os.path.join(ROOT, 'assets', 'images', 'logos', 'partners')
os.makedirs(OUTDIR, exist_ok=True)

COMMON_SVG_ICO = [
    '/favicon.svg', '/favicon.ico', '/favicon.png',
    '/logo.svg', '/logo.png', '/assets/logo.svg', '/assets/logo.png',
    '/images/logo.svg', '/images/logo.png', '/img/logo.svg', '/img/logo.png'
]

def read_index_urls(path):
    text = open(path, 'r', encoding='utf-8').read()
    urls = re.findall(r'href=["\'](https?://[^"\']+)["\']', text)
    urls = [u for u in urls if not u.startswith('mailto:')]
    seen = []
    for u in urls:
        if u not in seen:
            seen.append(u)
    return seen

def domain_name(url):
    return parse.urlparse(url).netloc.replace(':', '_')

def try_fetch(url, timeout=12):
    try:
        req = request.Request(url, headers={'User-Agent': 'mishmash-find-svg-ico/1.0'})
        with request.urlopen(req, timeout=timeout) as r:
            return r.read(), r.headers.get('Content-Type', '')
    except Exception:
        return None, None

def save_file(data, domain, ext):
    fname = f"{domain}.{ext}"
    out = os.path.join(OUTDIR, fname)
    with open(out, 'wb') as f:
        f.write(data)
    return out

def find_in_homepage(base, html):
    # look for link rel icons
    m = re.search(r'<link[^>]+rel=["\'][^"\']*(?:icon|shortcut icon)[^"\']*["\'][^>]*href=["\']([^"\']+)["\']', html, re.I)
    if m:
        return parse.urljoin(base, m.group(1))
    # og:image
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if m:
        return parse.urljoin(base, m.group(1))
    return None

def process(url):
    d = domain_name(url)
    base = f"{parse.urlparse(url).scheme}://{parse.urlparse(url).netloc}"
    found = {'svg': False, 'ico': False}

    # fetch homepage and inspect
    data, ct = try_fetch(base)
    html = ''
    if data:
        try:
            html = data.decode('utf-8', errors='replace')
        except Exception:
            html = ''
        cand = find_in_homepage(base, html)
        if cand:
            lower = cand.lower()
            if lower.endswith('.svg') and not found['svg']:
                d2, c2 = try_fetch(cand)
                if d2:
                    save_file(d2, d, 'svg')
                    found['svg'] = True
            if lower.endswith('.ico') and not found['ico']:
                d2, c2 = try_fetch(cand)
                if d2:
                    save_file(d2, d, 'ico')
                    found['ico'] = True

    # try common paths
    for p in COMMON_SVG_ICO:
        if found['svg'] and found['ico']:
            break
        cand = base + p
        data, ct = try_fetch(cand)
        if not data:
            continue
        ct = (ct or '').lower()
        if ('.svg' in p or 'svg' in ct) and not found['svg']:
            save_file(data, d, 'svg')
            found['svg'] = True
        if ('.ico' in p or 'ico' in ct) and not found['ico']:
            save_file(data, d, 'ico')
            found['ico'] = True

    # try favicon.ico specifically
    if not found['ico']:
        cand = base + '/favicon.ico'
        data, ct = try_fetch(cand)
        if data:
            save_file(data, d, 'ico')
            found['ico'] = True

    # try og:image if svg
    if not found['svg'] and html:
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if m:
            cand = parse.urljoin(base, m.group(1))
            if cand.lower().endswith('.svg'):
                data, ct = try_fetch(cand)
                if data:
                    save_file(data, d, 'svg')
                    found['svg'] = True

    return found

def main():
    urls = read_index_urls(INDEX)
    results = {}
    for u in urls:
        try:
            res = process(u)
            results[u] = res
        except Exception as e:
            results[u] = {'svg': False, 'ico': False, 'error': str(e)}
        time.sleep(0.4)

    # report
    svgs = sum(1 for r in results.values() if r.get('svg'))
    icos = sum(1 for r in results.values() if r.get('ico'))
    print(f'Found {svgs} svgs and {icos} icos for {len(results)} domains. Files saved to {OUTDIR}')

if __name__ == '__main__':
    main()
