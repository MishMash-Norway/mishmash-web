// Page weight and a carbon estimate, measured in a browser (issue #67).
//
// The earlier version of this measurement read the HTML and added up the
// assets it could see in the markup. That was wrong in both directions: it
// counted every photo of a carousel although a reader is sent one, and it
// missed what a stylesheet or a script asks for. This version serves the
// built site the way GitHub Pages serves it, with text compressed, drives a
// headless browser with an empty cache, and counts the bytes the server
// actually sends for a first visit.
//
// The carbon figure uses the Sustainable Web Design model as implemented in
// CO2.js (version 3): 0.81 kWh per GB transferred at 442 g CO2 per kWh. It is
// an estimate for comparing builds, not a measurement of a reader's device or
// network.
//
// The build also weighs one reference page, the news post from the opening
// conference, as it would be with four common choices this site does not make:
// photos as JPEG rather than AVIF, the web fonts at full size rather than cut
// down, every carousel photo sent on arrival, and the YouTube players loaded
// with the page rather than on a press. Beside them it records the median
// desktop page of the web from the HTTP Archive. The lab page
// /lab/footprint/ draws and plays the result.
//
// Usage: node scripts/measure_page_weight.mjs [--site _site]

import { createServer } from 'node:http';
import { gzipSync } from 'node:zlib';
import { readFile, stat, mkdir, writeFile } from 'node:fs/promises';
import { join, extname, resolve } from 'node:path';
import { chromium } from '@playwright/test';

const PAGES = ['/', '/about/description/', '/results/', '/events/', '/news/opening-conference/',
  '/people/alexander-refsum-jensenius/', '/lab/heritage/', '/no/'];
const KWH_PER_GB = 0.81;
const G_CO2_PER_KWH = 442;
const IDLE_TIMEOUT_MS = 15000;   // give up waiting for quiet after this
const REFERENCE_PAGE = '/news/opening-conference/';
const SOURCE_ROOT = resolve('site');   // the fonts before scripts/subset_fonts.py cut them down
const HTTP_ARCHIVE = 'https://cdn.httparchive.org/reports/bytesTotal.json';

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
  '.mjs': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml',
  '.txt': 'text/plain', '.xml': 'application/xml', '.woff2': 'font/woff2', '.woff': 'font/woff',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.avif': 'image/avif', '.gif': 'image/gif', '.ico': 'image/x-icon', '.webmanifest': 'application/manifest+json',
};
const COMPRESSED = new Set(['.html', '.css', '.js', '.mjs', '.json', '.svg', '.txt', '.xml', '.webmanifest']);
const KIND = {
  '.css': 'styles', '.js': 'scripts', '.mjs': 'scripts', '.json': 'data', '.woff2': 'fonts', '.woff': 'fonts',
  '.png': 'images', '.jpg': 'images', '.jpeg': 'images', '.webp': 'images', '.avif': 'images',
  '.svg': 'images', '.gif': 'images', '.ico': 'images', '.html': 'html', '.webmanifest': 'data',
};

function startServer(root) {
  const counters = { bytes: 0, requests: 0, byKind: {}, htmlBytes: 0, files: [] };
  const server = createServer(async (req, res) => {
    const path = decodeURIComponent(req.url.split('?')[0]);
    let file = join(root, path);
    try {
      if ((await stat(file)).isDirectory()) file = join(file, 'index.html');
    } catch { /* fall through to the 404 below */ }
    if (!resolve(file).startsWith(resolve(root))) { res.writeHead(403).end(); return; }
    let body;
    try {
      body = await readFile(file);
    } catch {
      res.writeHead(404, { 'content-type': 'text/plain' }).end('not found');
      return;
    }
    const ext = extname(file).toLowerCase();
    const headers = { 'content-type': TYPES[ext] || 'application/octet-stream' };
    if (COMPRESSED.has(ext) && /\bgzip\b/.test(req.headers['accept-encoding'] || '')) {
      body = gzipSync(body, { level: 6 });
      headers['content-encoding'] = 'gzip';
    }
    headers['content-length'] = String(body.length);
    counters.bytes += body.length;
    counters.requests += 1;
    counters.files.push({ file, ext, bytes: body.length });
    const kind = KIND[ext] || 'other';
    if (kind === 'html') counters.htmlBytes += body.length;
    else counters.byKind[kind] = (counters.byKind[kind] || 0) + body.length;
    res.writeHead(200, headers).end(body);
  });
  return { server, counters };
}

async function main() {
  const siteArg = process.argv.indexOf('--site');
  const root = resolve(siteArg > -1 ? process.argv[siteArg + 1] : '_site');
  const { server, counters } = startServer(root);
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const base = `http://127.0.0.1:${server.address().port}`;

  const browser = await chromium.launch();
  const rows = [];
  let reference = null;
  for (const page of PAGES) {
    try {
      await stat(join(root, page === '/' ? '' : page, 'index.html'));
    } catch { continue; }
    counters.bytes = 0; counters.requests = 0; counters.htmlBytes = 0; counters.files = [];
    for (const k of Object.keys(counters.byKind)) delete counters.byKind[k];
    // An empty cache is a first visit. Reduced motion stops the slideshows
    // from turning, so a gallery is counted as the one photo a reader is
    // shown on arrival rather than as however many turn up while the
    // measurement watches.
    const context = await browser.newContext({ reducedMotion: 'reduce' });
    // Only what this site serves is counted. Pictures hotlinked from partner
    // sites are refused, so that a slow or fast answer from someone else's
    // server does not move the figure between builds.
    await context.route('**', (route) => (route.request().url().startsWith(base) ? route.continue() : route.abort()));
    const tab = await context.newPage();
    await tab.setViewportSize({ width: 1280, height: 900 });
    await tab.goto(base + page, { waitUntil: 'load' });
    // Let the fonts arrive and the text settle before judging what is in
    // view, so that a lazy image just below the fold does not come and go
    // between runs.
    await tab.evaluate(() => document.fonts.ready);
    // Fetch the pictures a reader who reads the whole page would see: every
    // lazy image that is part of the layout, but not the slides a carousel
    // keeps hidden until asked. Scrolling to trigger them is unreliable in a
    // headless browser, and the figure has to mean the same thing at every
    // build.
    await tab.evaluate(() => {
      document.querySelectorAll('img[loading="lazy"]').forEach((img) => {
        if (img.offsetParent !== null || img.getClientRects().length > 0) img.loading = 'eager';
      });
    });
    // Wait for the network to fall quiet rather than for a fixed time, so the
    // figure does not depend on how fast this machine happens to be. A
    // carousel that turns every six seconds never starts before that.
    try {
      await tab.waitForLoadState('networkidle', { timeout: IDLE_TIMEOUT_MS });
    } catch { /* a page that never falls quiet is counted as it stands */ }
    // A font is asked for only once the text that needs it is laid out, which
    // can land just after the first quiet moment, so wait for a second one.
    await tab.waitForTimeout(500);
    try {
      await tab.waitForLoadState('networkidle', { timeout: IDLE_TIMEOUT_MS });
    } catch { /* as above */ }
    if (page === REFERENCE_PAGE) {
      reference = {
        files: [...counters.files],
        carousel: await tab.evaluate(() => [...document.querySelectorAll('.mm-carousel img')].map((i) => i.getAttribute('src'))),
        videos: await tab.evaluate(() => [...document.querySelectorAll('[data-youtube]')].map((b) => b.dataset.youtube)),
      };
    }
    await context.close();
    rows.push({
      page,
      bytes: counters.bytes,
      html_bytes: counters.htmlBytes,
      by_kind: { ...counters.byKind },
      requests: counters.requests,
      g_co2_first_visit: Math.round((counters.bytes / 1e9) * KWH_PER_GB * G_CO2_PER_KWH * 1e4) / 1e4,
    });
  }
  const alternatives = reference ? await weighAlternatives(browser, base, root, reference, rows) : null;
  await browser.close();
  await new Promise((r) => server.close(r));

  const out = {
    generated_at: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
    model: 'Sustainable Web Design model v3 (CO2.js): 0.81 kWh/GB, 442 g CO2/kWh, first visit. '
      + 'Measured in a headless browser with an empty cache and reduced motion, against a server that compresses text as GitHub Pages does. '
      + 'Counts everything a reader of the whole page is sent, but not the slides a carousel keeps hidden and not pictures hotlinked from other sites.',
    pages: rows,
    kwh_per_gb: KWH_PER_GB,
    g_co2_per_kwh: G_CO2_PER_KWH,
    alternatives,
    median_bytes: rows.length ? [...rows].map((r) => r.bytes).sort((a, b) => a - b)[Math.floor(rows.length / 2)] : 0,
  };
  const empty = rows.filter((r) => r.bytes < 10000);
  if (!rows.length || empty.length) {
    console.error(`measure_page_weight: ${empty.length || 'all'} page(s) transferred almost nothing; the server or the browser is wrong`);
    process.exit(1);
  }
  await mkdir(join(root, 'data'), { recursive: true });
  await writeFile(join(root, 'data', 'page-weight.json'), JSON.stringify(out, null, 1), 'utf8');
  for (const r of rows) {
    const kinds = Object.entries(r.by_kind).map(([k, v]) => `${k} ${Math.round(v / 1024)}`).join(', ');
    console.log(`${r.page.padEnd(45)} ${String(Math.round(r.bytes / 1024)).padStart(6)} KB ${String(r.requests).padStart(3)} requests  ${r.g_co2_first_visit.toFixed(3)} g CO2  | ${kinds}`);
  }
}

async function sizeOf(path) {
  try { return (await stat(path)).size; } catch { return null; }
}

// The reference page as it would be with the choices this site does not make.
// Each variant is the bytes it would add to a first visit; the lab page sums
// them into a conventional build.
async function weighAlternatives(browser, base, root, reference, rows) {
  const served = rows.find((r) => r.page === REFERENCE_PAGE);
  const sent = new Set(reference.files.map((f) => f.file));
  const variants = [];

  // Photos as JPEG: every AVIF the browser was sent, replaced by the JPEG
  // beside it, which is what a browser without the AVIF source would get.
  let jpeg = 0;
  for (const f of reference.files.filter((f) => f.ext === '.avif')) {
    const size = await sizeOf(f.file.slice(0, -'.avif'.length));
    if (size) jpeg += size - f.bytes;
  }
  variants.push({ key: 'jpeg', kind: 'images', extra_bytes: jpeg });

  // Fonts at full size: the font files as they are in the repository, before
  // the build cut them down to the characters the site uses.
  let fonts = 0;
  for (const f of reference.files.filter((f) => f.ext === '.woff2' || f.ext === '.woff')) {
    const size = await sizeOf(join(SOURCE_ROOT, f.file.slice(root.length)));
    if (size) fonts += Math.max(0, size - f.bytes);
  }
  variants.push({ key: 'fonts', kind: 'fonts', extra_bytes: fonts });

  // Every carousel photo on arrival: the slides a reader has not asked for,
  // in the format the browser would have been sent.
  let carousel = 0;
  for (const src of reference.carousel) {
    const local = join(root, decodeURIComponent(src));
    if (sent.has(local) || sent.has(local + '.avif')) continue;
    carousel += (await sizeOf(local + '.avif')) ?? (await sizeOf(local)) ?? 0;
  }
  variants.push({ key: 'carousel', kind: 'images', extra_bytes: carousel });

  // The YouTube players loaded with the page, as an ordinary embed does,
  // without playing anything. This reaches YouTube, so it is the one figure
  // that depends on someone else's server; it is left out when that fails.
  let video = null;
  if (reference.videos.length) {
    const context = await browser.newContext({ reducedMotion: 'reduce' });
    let third = 0;
    const tab = await context.newPage();
    tab.on('requestfinished', async (req) => {
      if (req.url().startsWith(base)) return;
      try { third += (await req.sizes()).responseBodySize; } catch { /* ignore */ }
    });
    try {
      await tab.goto(base + REFERENCE_PAGE, { waitUntil: 'load' });
      await tab.evaluate(() => {
        document.querySelectorAll('[data-youtube]').forEach((b) => {
          const f = document.createElement('iframe');
          f.src = 'https://www.youtube-nocookie.com/embed/' + b.dataset.youtube;
          f.width = 560; f.height = 315;
          b.replaceWith(f);
        });
      });
      for (let i = 0; i < 2; i += 1) {
        try { await tab.waitForLoadState('networkidle', { timeout: IDLE_TIMEOUT_MS }); } catch { /* counted as it stands */ }
        await tab.waitForTimeout(1000);
      }
      if (third > 0) video = third;
    } catch (e) {
      console.error('measure_page_weight: the embedded players could not be weighed:', e.message);
    }
    await context.close();
  }
  variants.push({ key: 'video', kind: 'video', extra_bytes: video, players: reference.videos.length });

  // The median desktop page of the web, from the HTTP Archive's monthly crawl.
  let web = null;
  try {
    const res = await fetch(HTTP_ARCHIVE);
    const rowsHA = (await res.json()).filter((r) => r.client === 'desktop');
    const last = rowsHA[rowsHA.length - 1];
    web = { bytes: Math.round(last.p50 * 1024), date: last.date.replace(/_/g, '-'), source: HTTP_ARCHIVE };
  } catch (e) {
    console.error('measure_page_weight: the HTTP Archive median could not be fetched:', e.message);
  }

  for (const v of variants) console.log(`alternative ${v.key.padEnd(9)} +${v.extra_bytes === null ? 'n/a' : Math.round(v.extra_bytes / 1024) + ' KB'}`);
  if (web) console.log(`web median ${Math.round(web.bytes / 1024)} KB (${web.date})`);
  return { reference_page: REFERENCE_PAGE, served_bytes: served.bytes, served_by_kind: { html: served.html_bytes, ...served.by_kind }, variants, web_median: web };
}

main().catch((e) => { console.error(e); process.exit(1); });
