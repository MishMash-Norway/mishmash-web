// Text contrast in the states a page scan never reaches.
//
// The pa11y run in CI loads a page and looks at it as it arrives. That misses
// anything a reader has to do something to see: the skip link, which exists
// only while focused, the language menu, which has to be opened, and the search
// results, which are drawn by JavaScript after a query. The UiO web team found
// three failures of 1.4.3 in exactly those places on 24 September 2026.
//
// This script opens each state in a headless browser, reads the colour the
// browser actually paints, and works out the ratio. A target may carry a
// `prepare` step: focus an element, open a <details>, or type a search.
//
// The threshold is the WCAG 2.1 AA one: 4.5:1 for text, and 3:1 for large text,
// which means 24px, or 18.66px when bold. An element whose background is
// transparent takes the first painted background above it, which is what the
// browser composites against.
//
// Usage: node scripts/check_contrast.mjs [--site _site] [--base https://mishmash.no] [--level AA|AAA] [--list]
//
// --base measures a site that is already served, such as production after a
// deploy, instead of the local build.

import { createServer } from 'node:http';
import { readFile, stat } from 'node:fs/promises';
import { join, extname, resolve } from 'node:path';
import { chromium } from '@playwright/test';

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript',
  '.mjs': 'text/javascript', '.json': 'application/json', '.svg': 'image/svg+xml',
  '.txt': 'text/plain', '.xml': 'application/xml', '.woff2': 'font/woff2', '.woff': 'font/woff',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp',
  '.avif': 'image/avif', '.gif': 'image/gif', '.ico': 'image/x-icon',
  '.webmanifest': 'application/manifest+json',
};

// WCAG 1.4.3 (AA) asks 4.5:1 for text and 3:1 for large text; 1.4.6 (AAA)
// asks 7:1 and 4.5:1. The level is chosen on the command line.
export const LEVELS = { AA: { text: 4.5, large: 3 }, AAA: { text: 7, large: 4.5 } };

// Each target names a page, what to do to bring the text into view, and the
// elements to measure once it is there.
export const TARGETS = [
  {
    page: '/',
    label: 'skip link, focused',
    prepare: { kind: 'focus', selector: '#skip-to-content' },
    selector: '#skip-to-content',
  },
  {
    page: '/',
    label: 'language menu, open',
    prepare: { kind: 'open-details', selector: '.lang-switcher' },
    selector: '.lang-switcher summary, .lang-switcher .lang-active, .lang-switcher .wp-list a',
  },
  {
    page: '/',
    label: 'work package menu, open',
    prepare: { kind: 'open-details', selector: 'header .wp-dropdown:not(.lang-switcher)' },
    selector: 'header .wp-dropdown:not(.lang-switcher) .wp-list a',
  },
  {
    page: '/about/',
    label: 'body link, focused',
    prepare: { kind: 'focus', selector: '.main-content a[href]' },
    selector: '.main-content a[href]:focus',
  },
  {
    page: '/about/',
    label: 'footer link, focused',
    prepare: { kind: 'focus', selector: 'footer a[href]' },
    selector: 'footer a[href]:focus',
  },
  {
    page: '/search/',
    label: 'search results and filters',
    prepare: { kind: 'search', selector: '#search-input', text: 'a' },
    selector: '.result-type-badge, .filter-chip, .result-date, .search-status',
  },
];

export const server = (root) => createServer(async (req, res) => {
  const path = decodeURIComponent(req.url.split('?')[0]);
  let file = join(root, path);
  try {
    if ((await stat(file)).isDirectory()) file = join(file, 'index.html');
  } catch { /* fall through to the 404 below */ }
  if (!resolve(file).startsWith(resolve(root))) { res.writeHead(403).end(); return; }
  try {
    const body = await readFile(file);
    res.writeHead(200, { 'content-type': TYPES[extname(file).toLowerCase()] || 'application/octet-stream' });
    res.end(body);
  } catch {
    res.writeHead(404, { 'content-type': 'text/plain' }).end('not found');
  }
});

// Runs in the page. Reads the painted colours and returns one row per element.
export function measure([selector, level]) {
  const parse = (value) => {
    const m = String(value).match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[,\s/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const over = (top, bottom) => ({
    r: top.r * top.a + bottom.r * (1 - top.a),
    g: top.g * top.a + bottom.g * (1 - top.a),
    b: top.b * top.a + bottom.b * (1 - top.a),
    a: 1,
  });
  const luminance = ({ r, g, b }) => {
    const f = (v) => {
      const x = v / 255;
      return x <= 0.04045 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  };
  const hex = ({ r, g, b }) => '#' + [r, g, b]
    .map((v) => Math.round(v).toString(16).padStart(2, '0')).join('');

  const backdrop = (el) => {
    let colour = { r: 255, g: 255, b: 255, a: 1 };
    const stack = [];
    for (let node = el; node && node !== document.documentElement.parentNode; node = node.parentElement) {
      const bg = parse(getComputedStyle(node).backgroundColor);
      if (bg && bg.a > 0) stack.push(bg);
      if (bg && bg.a === 1) break;
    }
    for (const bg of stack.reverse()) colour = over(bg, colour);
    return colour;
  };

  const rows = [];
  for (const el of document.querySelectorAll(selector)) {
    const text = (el.textContent || '').trim();
    if (!text) continue;
    const style = getComputedStyle(el);
    if (style.visibility === 'hidden' || style.display === 'none') continue;
    const box = el.getBoundingClientRect();
    if (box.width === 0 || box.height === 0) continue;
    const fg = parse(style.color);
    if (!fg) continue;
    const bg = backdrop(el);
    const front = fg.a < 1 ? over(fg, bg) : fg;
    const l1 = luminance(front);
    const l2 = luminance(bg);
    const ratio = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
    const size = parseFloat(style.fontSize);
    const weight = parseInt(style.fontWeight, 10) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    rows.push({
      text: text.slice(0, 40).replace(/\s+/g, ' '),
      selector: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(/\s+/)[0] : ''),
      fg: hex(front), bg: hex(bg), ratio: Math.round(ratio * 100) / 100, large,
      required: large ? level.large : level.text,
    });
  }
  return rows;
}

async function main() {
  const args = process.argv.slice(2);
  const root = resolve(args.includes('--site') ? args[args.indexOf('--site') + 1] : '_site');
  const listOnly = args.includes('--list');
  const levelName = args.includes('--level') ? args[args.indexOf('--level') + 1].toUpperCase() : 'AA';
  const level = LEVELS[levelName];
  if (!level) { console.error(`--level takes AA or AAA, not ${levelName}`); return 2; }

  const remote = args.includes('--base') ? args[args.indexOf('--base') + 1].replace(/\/$/, '') : null;
  const app = remote ? null : server(root);
  if (app) await new Promise((r) => app.listen(0, '127.0.0.1', r));
  const base = remote || `http://127.0.0.1:${app.address().port}`;
  console.log(`measuring ${base}`);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  const failures = [];
  let measured = 0;
  for (const target of TARGETS) {
    await page.goto(base + target.page, { waitUntil: 'networkidle' });
    const p = target.prepare;
    if (p?.kind === 'focus') await page.locator(p.selector).first().focus();
    if (p?.kind === 'open-details') {
      await page.locator(p.selector).first().evaluate((el) => { el.open = true; });
    }
    if (p?.kind === 'search') {
      const input = page.locator(p.selector).first();
      if (await input.count()) {
        await input.fill(p.text);
        await page.waitForTimeout(1200);
      }
    }
    await page.waitForTimeout(150);
    const rows = await page.evaluate(measure, [target.selector, level]);
    measured += rows.length;
    if (!rows.length) {
      console.log(`  ${target.label}: nothing matched ${target.selector}`);
      continue;
    }
    // One line per distinct combination: the same chip drawn forty times is one
    // problem, not forty.
    const distinct = new Map();
    for (const row of rows) {
      const id = `${row.selector}|${row.fg}|${row.bg}|${row.required}`;
      const seen = distinct.get(id);
      if (seen) seen.count += 1;
      else distinct.set(id, { ...row, count: 1 });
    }
    console.log(`\n${target.label} (${target.page})`);
    for (const row of [...distinct.values()].sort((a, b) => a.ratio - b.ratio)) {
      const bad = row.ratio < row.required;
      if (bad) failures.push({ ...row, label: target.label });
      const mark = bad ? 'FAILS' : '  ok ';
      const times = row.count > 1 ? ` (${row.count}\u00d7)` : '';
      console.log(`  ${mark} ${row.ratio.toFixed(2).padStart(5)}:1 need ${row.required}  ${row.fg} on ${row.bg}  ${row.selector}${times}  ${row.text}`);
    }
  }

  await browser.close();
  if (app) app.close();

  console.log(`\ncontrast at ${levelName}: ${measured} pieces of text measured, ${failures.length} distinct combination(s) below the threshold`);
  if (failures.length && !listOnly) {
    console.error(`\nWCAG 2.1 ${levelName} asks for ${level.text}:1, or ${level.large}:1 for large text. Raise the\n`
      + 'contrast in assets/css/, using the tokens in brand.css, and run this again.');
    return 1;
  }
  return 0;
}

import { pathToFileURL } from 'node:url';
if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  process.exit(await main());
}
