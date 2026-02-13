#!/usr/bin/env python3
"""Download partner logos referenced in index.md into assets/images/logos/partners/.

Usage: python3 scripts/download_partner_logos.py
"""
import os
import re
import sys
import time
from urllib import request, parse, error

ROOT = os.path.dirname(os.path.dirname(__file__))
INDEX = os.path.join(ROOT, 'index.md')
OUTDIR = os.path.join(ROOT, 'assets', 'images', 'logos', 'partners')

os.makedirs(OUTDIR, exist_ok=True)

def read_index_urls(path):
    text = open(path, 'r', encoding='utf-8').read()
    urls = re.findall(r'href=["\'](https?://[^"\']+)["\']', text)
    # filter plausible partner domains (simple heuristic)
    urls = [u for u in urls if not u.startswith('mailto:')]
    seen = []
    for u in urls:
        d = parse.urlparse(u).netloc
        if d and u not in seen:
            seen.append(u)
    return seen

def absolute(base, url):
    return parse.urljoin(base, url)

def find_logo_from_html(base_url, html):
    # try og:image
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if m:
        return absolute(base_url, m.group(1))
    m = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
    if m:
        return absolute(base_url, m.group(1))
    # link rel icons
    m = re.search(r'<link[^>]+rel=["\'](?:shortcut icon|icon)["\'][^>]+href=["\']([^"\']+)["\']', html, re.I)
    if m:
        return absolute(base_url, m.group(1))
    # <img ... logo ...>
    m = re.search(r'<img[^>]+(?:alt=["\'][^"\']*logo[^"\']*["\']|class=["\'][^"\']*logo[^"\']*["\'])[^>]*src=["\']([^"\']+)["\']', html, re.I)
    if m:
        return absolute(base_url, m.group(1))
    # fallback any image
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
    if m:
        return absolute(base_url, m.group(1))
    return None

def try_fetch(url, timeout=15):
    try:
        req = request.Request(url, headers={'User-Agent': 'mishmash-logo-downloader/1.0'})
        with request.urlopen(req, timeout=timeout) as r:
            data = r.read()
            ct = r.headers.get('Content-Type', '')
            return data, ct
    except Exception as e:
        return None, None

def save_logo(data, content_type, domain, candidate_url):
    if not data:
        return False
    ext = 'png'
    if 'svg' in content_type:
        ext = 'svg'
    elif 'png' in content_type:
        ext = 'png'
    elif 'jpeg' in content_type or 'jpg' in content_type:
        ext = 'jpg'
    else:
        # try to infer from url
        p = parse.urlparse(candidate_url).path
        if '.' in p:
            ext = p.split('.')[-1]
    fname = f"{domain}.{ext}"
    out = os.path.join(OUTDIR, fname)
    with open(out, 'wb') as f:
        f.write(data)
    return True

def process_site(url):
    print('->', url)
    parsed = parse.urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    domain = parsed.netloc.replace(':', '_')

    # fetch homepage
    data, ct = try_fetch(url)
    html = ''
    if data:
        try:
            html = data.decode('utf-8', errors='replace')
        except Exception:
            html = ''

    candidate = None
    if html:
        candidate = find_logo_from_html(base, html)

    if not candidate:
        candidate = base + '/favicon.ico'

    data2, ct2 = try_fetch(candidate)
    if data2:
        ok = save_logo(data2, ct2 or '', domain, candidate)
        if ok:
            print('   saved', domain)
            return True

    # last resort: try base + '/logo.png' or '/logo.svg'
    for p in ['/logo.svg', '/logo.png', '/assets/logo.svg', '/assets/logo.png']:
        cand = base + p
        d, c = try_fetch(cand)
        if d:
            if save_logo(d, c or '', domain, cand):
                print('   saved', domain)
                return True

    print('   failed for', domain)
    return False

def main():
    urls = read_index_urls(INDEX)
    print('Found', len(urls), 'unique urls; attempting to fetch logos...')
    success = 0
    for u in urls:
        try:
            if process_site(u):
                success += 1
        except Exception as e:
            print('   error', e)
        time.sleep(0.5)
    print(f'Done. {success}/{len(urls)} logos saved to {OUTDIR}')

if __name__ == '__main__':
    main()
