// How far the site is from WCAG AAA, measured rather than guessed (issue #76).
//
// The AAA criteria that a stylesheet decides are three: contrast at 7:1
// (1.4.6), pointer targets of 44 by 44 CSS pixels (2.5.5), and visual
// presentation (1.4.8), of which the measurable part is a line of text no
// longer than 80 characters. WCAG 2.2 adds a minimum target of 24 by 24 at
// level AA (2.5.8), which is reported alongside. Everything else at AAA is
// content: transcripts, sign language, reading level, abbreviations.
//
// This drives a browser over a set of pages and measures what it paints:
// the contrast of body text, headings and links at the AAA threshold, the size
// of every element a reader can press, and the width of every paragraph in
// characters of its own font. Contrast in the states a page scan cannot reach
// (the skip link, the menus, the search results) comes from check_contrast.mjs
// at the same threshold.
//
// Usage: node scripts/measure_aaa.mjs [--site _site] [--base https://mishmash.no]
//                                    [--prefix /ui/<theme>] [--fail]
//
// --prefix measures a theme preview built under that path. --fail exits 1 when
// anything is below the AAA thresholds, which is how a theme that declares
// wcag_target: AAA in its _config.yml is held to it in CI; without it the
// script only reports, which is what the main site gets.

import { resolve } from 'node:path';
import { chromium } from '@playwright/test';
import { server, measure, TARGETS, LEVELS } from './check_contrast.mjs';

const PAGES = ['/', '/about/', '/about/description/', '/wp1/', '/events/', '/news/', '/search/',
  '/people/alexander-refsum-jensenius/', '/about/glossary/', '/no/', '/results/'];
const TEXT = '.main-content p, .main-content li, .main-content h1, .main-content h2, .main-content h3, '
  + '.main-content a, .main-content td, .main-content th, footer a, footer p, .page-header a, .page-header p, '
  + '.event-meta, .event-desc, .result-date, .search-status';
const TARGET_MIN = { AAA: 44, AA22: 24 };
const LINE_MAX_CH = 80;

// Runs in the page: the box of every element a reader can press. An inline
// link inside a sentence is exempt in both 2.5.5 and 2.5.8, so it is skipped;
// a link that stands on its own is measured.
function targets() {
  const rows = [];
  const sel = 'a[href], button, input:not([type=hidden]), select, textarea, summary, [role=button], [tabindex="0"]';
  for (const el of document.querySelectorAll(sel)) {
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') continue;
    if (el.getAttribute('tabindex') === '-1' || el.getAttribute('aria-hidden') === 'true') continue;
    const box = el.getBoundingClientRect();
    if (box.width < 2 || box.height < 2) continue;   // clipped away until focused, like the skip link
    const inline = style.display === 'inline' && el.parentElement
      && (el.parentElement.textContent || '').trim().length > (el.textContent || '').trim().length + 2;
    if (inline) continue;
    rows.push({
      selector: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(/\s+/)[0] : ''),
      text: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 30).replace(/\s+/g, ' '),
      w: Math.round(box.width), h: Math.round(box.height),
    });
  }
  return rows;
}

// Runs in the page: the width of each paragraph in characters of its own font,
// using the width of a run of zeros the way the CSS unit ch does.
function lineLengths() {
  const rows = [];
  const probe = document.createElement('span');
  probe.textContent = '0000000000';
  probe.style.cssText = 'position:absolute;visibility:hidden;white-space:nowrap';
  for (const p of document.querySelectorAll('.main-content p, .main-content li')) {
    const text = (p.textContent || '').trim();
    if (text.length < 120) continue;                 // too short to wrap into a long line
    const style = getComputedStyle(p);
    probe.style.font = style.font;
    p.appendChild(probe);
    const ch = probe.getBoundingClientRect().width / 10;
    p.removeChild(probe);
    const width = p.getBoundingClientRect().width - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
    rows.push({ chars: Math.round(width / ch), text: text.slice(0, 40) });
  }
  return rows;
}

function distinct(rows, keyOf) {
  const map = new Map();
  for (const row of rows) {
    const k = keyOf(row);
    const seen = map.get(k);
    if (seen) seen.count += 1; else map.set(k, { ...row, count: 1 });
  }
  return [...map.values()];
}

async function main() {
  const args = process.argv.slice(2);
  const root = resolve(args.includes('--site') ? args[args.indexOf('--site') + 1] : '_site');
  const remote = args.includes('--base') ? args[args.indexOf('--base') + 1].replace(/\/$/, '') : null;
  const prefix = args.includes('--prefix') ? args[args.indexOf('--prefix') + 1].replace(/\/$/, '') : '';
  const fail = args.includes('--fail');
  const app = remote ? null : server(root);
  if (app) await new Promise((r) => app.listen(0, '127.0.0.1', r));
  const base = remote || `http://127.0.0.1:${app.address().port}`;
  console.log(`measuring ${base}${prefix} against WCAG AAA\n`);

  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const level = LEVELS.AAA;

  const contrast = [];
  const small = [];
  const lines = [];
  let textCount = 0, targetCount = 0, lineCount = 0;

  for (const path of PAGES) {
    await page.goto(base + prefix + path, { waitUntil: 'networkidle' });
    const rows = await page.evaluate(measure, [TEXT, level]);
    textCount += rows.length;
    for (const row of rows) if (row.ratio < row.required) contrast.push({ ...row, page: path });
    const t = await page.evaluate(targets);
    targetCount += t.length;
    for (const row of t) if (Math.min(row.w, row.h) < TARGET_MIN.AAA) small.push({ ...row, page: path });
    const l = await page.evaluate(lineLengths);
    lineCount += l.length;
    for (const row of l) if (row.chars > LINE_MAX_CH) lines.push({ ...row, page: path });
  }

  // The states a page scan cannot reach, at the AAA threshold.
  for (const target of TARGETS) {
    await page.goto(base + prefix + target.page, { waitUntil: 'networkidle' });
    const p = target.prepare;
    if (p?.kind === 'focus') await page.locator(p.selector).first().focus();
    if (p?.kind === 'open-details') await page.locator(p.selector).first().evaluate((el) => { el.open = true; });
    if (p?.kind === 'search') {
      const input = page.locator(p.selector).first();
      if (await input.count()) { await input.fill(p.text); await page.waitForTimeout(1200); }
    }
    await page.waitForTimeout(150);
    const rows = await page.evaluate(measure, [target.selector, level]);
    textCount += rows.length;
    for (const row of rows) if (row.ratio < row.required) contrast.push({ ...row, page: `${target.page} (${target.label})` });
  }
  await browser.close();
  if (app) app.close();

  console.log(`1.4.6 Contrast (Enhanced), 7:1 for text and 4.5:1 for large text`);
  const c = distinct(contrast, (r) => `${r.selector}|${r.fg}|${r.bg}`).sort((a, b) => a.ratio - b.ratio);
  console.log(`  ${textCount} pieces of text measured, ${contrast.length} below the threshold, ${c.length} distinct combinations`);
  for (const r of c) console.log(`    ${r.ratio.toFixed(2).padStart(5)}:1  ${r.fg} on ${r.bg}  ${r.selector} (${r.count}×)  ${r.text}`);

  console.log(`\n2.5.5 Target Size (Enhanced), 44 by 44 CSS pixels; 2.2's 2.5.8 asks 24 by 24`);
  const s = distinct(small, (r) => `${r.selector}|${r.w}x${r.h}`).sort((a, b) => Math.min(a.w, a.h) - Math.min(b.w, b.h));
  const under24 = small.filter((r) => Math.min(r.w, r.h) < TARGET_MIN.AA22);
  console.log(`  ${targetCount} targets measured, ${small.length} under 44 (${s.length} distinct), ${under24.length} of them under 24`);
  for (const r of s) console.log(`    ${String(r.w).padStart(4)}×${String(r.h).padEnd(4)} ${r.selector} (${r.count}×)  ${r.text}`);

  console.log(`\n1.4.8 Visual Presentation, lines no longer than ${LINE_MAX_CH} characters`);
  const longest = lines.sort((a, b) => b.chars - a.chars);
  console.log(`  ${lineCount} paragraphs measured, ${lines.length} wider than ${LINE_MAX_CH} characters`);
  for (const r of longest.slice(0, 8)) console.log(`    ${String(r.chars).padStart(4)} ch  ${r.page}  ${r.text}`);

  const short = [contrast.length && `${c.length} contrast combinations under 7:1`,
    small.length && `${s.length} target sizes under 44px`,
    lines.length && `${lines.length} lines over ${LINE_MAX_CH} characters`].filter(Boolean);
  console.log(`\nAAA: ${short.length ? short.join(', ') : 'nothing below the thresholds'}`);
  if (fail && short.length) {
    console.error('This build declares WCAG AAA as its target and does not reach it.');
    return 1;
  }
  return 0;
}

process.exit(await main());
