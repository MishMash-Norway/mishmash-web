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
  const counters = { bytes: 0, requests: 0, byKind: {}, htmlBytes: 0 };
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
  for (const page of PAGES) {
    try {
      await stat(join(root, page === '/' ? '' : page, 'index.html'));
    } catch { continue; }
    counters.bytes = 0; counters.requests = 0; counters.htmlBytes = 0;
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
  await browser.close();
  await new Promise((r) => server.close(r));

  const out = {
    generated_at: new Date().toISOString().replace(/\.\d+Z$/, 'Z'),
    model: 'Sustainable Web Design model v3 (CO2.js): 0.81 kWh/GB, 442 g CO2/kWh, first visit. '
      + 'Measured in a headless browser with an empty cache and reduced motion, against a server that compresses text as GitHub Pages does. '
      + 'Counts everything a reader of the whole page is sent, but not the slides a carousel keeps hidden and not pictures hotlinked from other sites.',
    pages: rows,
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

main().catch((e) => { console.error(e); process.exit(1); });
