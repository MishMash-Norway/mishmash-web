/**
 * Can a page on another site play sound and film from the National Library?
 *
 * The catalogue already answers the metadata half of the question: a public
 * radio programme carries a IIIF v3 manifest whose body is a Sound pointing at
 * a stream, and a public film carries a Video body the same way. See
 * scripts/report_nb_media_access.py for those counts.
 *
 * This test answers the other half, which only a browser can answer: whether
 * the stream server serves a page that is not nb.no. It loads the library's
 * own item page and records what plays there, then asks the same addresses
 * from a page served on localhost, which stands in for any other site.
 *
 * Run: node tests/nb-media-access.mjs
 */
import { chromium } from 'playwright';
import http from 'http';

// A radio programme and a film, both public; the film is marked Public Domain
// Mark 1.0, so a block that catches it as well is not a rights decision.
const CASES = [
  {
    kind: 'radio',
    item: 'ff6aa81025b6c5d8d40a4ac5687ec011',
    stream: 'https://wow.nb.no/vod/URN:NBN:no-nb_dra_2002-06441D/playlist.m3u8',
  },
  {
    kind: 'film (public domain)',
    item: 'c76533127bb8519ab43c458cbe569d9b',
    stream: 'https://wow.nb.no/vod/URN:NBN:no-nb_digifilm_800916_20211123/playlist.m3u8',
  },
];

const browser = await chromium.launch();
const server = http
  .createServer((req, res) => {
    res.writeHead(200, { 'content-type': 'text/html' });
    res.end('<!doctype html><title>other site</title>');
  })
  .listen(8734);

const results = [];

for (const testCase of CASES) {
  // 1. The library's own page: does the stream answer there?
  const onTheirPage = await browser.newPage();
  const served = [];
  onTheirPage.on('response', (response) => {
    if (/wow\.nb\.no/.test(response.url())) served.push(response.status());
  });
  await onTheirPage.goto(`https://www.nb.no/items/${testCase.item}`, {
    waitUntil: 'domcontentloaded',
    timeout: 60000,
  });
  await onTheirPage.waitForTimeout(6000);
  // A film starts on its own; a radio programme waits for the play control.
  for (const selector of [
    'button[aria-label*="Spill"]',
    'button[title*="Spill"]',
    '.vjs-big-play-button',
    'button:has-text("Spill")',
  ]) {
    const control = await onTheirPage.$(selector);
    if (control) {
      await control.click().catch(() => {});
      break;
    }
  }
  await onTheirPage.waitForTimeout(8000);
  await onTheirPage.close();

  // 2. A page on another origin: the same address, fetched and in an element.
  const elsewhere = await browser.newPage();
  await elsewhere.goto('http://localhost:8734/');
  const fetched = await elsewhere.evaluate(async (url) => {
    try {
      const response = await fetch(url);
      return { status: response.status, acao: response.headers.get('access-control-allow-origin') };
    } catch (error) {
      return { error: String(error) };
    }
  }, testCase.stream);
  const element = await elsewhere.evaluate(
    (url) =>
      new Promise((resolve) => {
        const media = new Audio();
        media.preload = 'auto';
        media.src = url;
        media.onloadedmetadata = () => resolve({ loaded: true });
        media.onerror = () => resolve({ loaded: false, code: media.error && media.error.code });
        setTimeout(() => resolve({ loaded: false, code: 'timeout' }), 15000);
      }),
    testCase.stream
  );
  await elsewhere.close();

  results.push({ kind: testCase.kind, served, fetched, element });
  console.log(`\n${testCase.kind}`);
  console.log(`  on nb.no          ${served.length} stream responses, statuses ${[...new Set(served)].join(',') || 'none'}`);
  console.log(`  fetch from other  ${JSON.stringify(fetched)}`);
  console.log(`  media element     ${JSON.stringify(element)}`);
}

// 3. Could the library's own player be framed instead?
const headerPage = await browser.newPage();
const response = await headerPage.goto(`https://www.nb.no/items/${CASES[0].item}`, {
  waitUntil: 'domcontentloaded',
  timeout: 60000,
});
const headers = response.headers();
console.log('\nframing the library player');
console.log(`  x-frame-options          ${headers['x-frame-options'] || '(none)'}`);
console.log(`  content-security-policy  ${headers['content-security-policy'] || '(none)'}`);
await headerPage.close();

server.close();
await browser.close();

const blocked = results.filter((r) => !r.element.loaded).length;
console.log(`\n${blocked} of ${results.length} cases could not be played from another site.`);
