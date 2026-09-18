// Score the retrieval behind Ask MishMash against a set of questions (issue #26).
//
// An assistant that answers from the site is only as good as the passages it
// is given, and that part can be measured without a model. Each question in
// tests/chat/questions.json names the page that should answer it; this script
// runs the same retrieval the chat page uses and reports how often that page
// is among the passages retrieved. It fails when the share falls below the
// threshold, so a change to the chunking or the knowledge base cannot quietly
// make the assistant worse.
//
// Usage: node scripts/eval_chat_retrieval.mjs [--min 0.8] [--verbose]

import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { retrieve, tokenize } from '../site/assets/js/chat-retrieval.js';

const here = dirname(fileURLToPath(import.meta.url));
const repo = join(here, '..');

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i > -1 ? process.argv[i + 1] : fallback;
}

const minimum = Number(arg('--min', '0.8'));
const verbose = process.argv.includes('--verbose');

// The index is tokenized in Python and a question in JavaScript; if the two
// disagree, a reader's words stop matching what was indexed.
const cases = JSON.parse(await readFile(join(repo, 'tests', 'chat', 'tokenizer-cases.json'), 'utf8'));
let drift = 0;
for (const c of cases.cases) {
  const got = tokenize(c.in);
  if (JSON.stringify(got) !== JSON.stringify(c.out)) {
    drift += 1;
    console.error(`tokenizer differs: ${JSON.stringify(c.in)} gave ${JSON.stringify(got)}, expected ${JSON.stringify(c.out)}`);
  }
}
if (drift) {
  console.error('eval_chat_retrieval: the JavaScript tokenizer no longer matches the shared cases');
  process.exit(1);
}

const kb = JSON.parse(await readFile(join(repo, 'site', 'chat', 'knowledge.json'), 'utf8'));

// Every passage has to come from a page a reader can open. A passage without
// one means a document was put into site/chat/docs/ and is being served, and
// quoted in answers, without anything linking to it.
const unlinked = kb.chunks.filter((c) => !c.url);
if (unlinked.length) {
  const names = [...new Set(unlinked.map((c) => c.source))].slice(0, 10);
  console.error(`eval_chat_retrieval: ${unlinked.length} passages have no page behind them: ${names.join(', ')}`);
  console.error('Put such a document on a page of its own, or keep it out of site/chat/docs/.');
  process.exit(1);
}
const set = JSON.parse(await readFile(join(repo, 'tests', 'chat', 'questions.json'), 'utf8'));
const topK = set.top_k || 4;

let hits = 0;
const misses = [];
for (const { q, expect } of set.questions) {
  const chunks = retrieve(kb, q, topK);
  const urls = chunks.map((c) => c.url || '');
  const wanted = Array.isArray(expect) ? expect : [expect];
  const found = urls.some((u) => wanted.some((w) => u === w || u.startsWith(w)));
  if (found) hits += 1;
  else misses.push({ q, expect: wanted.join(' or '), got: urls });
  if (verbose) console.log(`${found ? 'hit ' : 'miss'}  ${q}\n        expected ${wanted.join(' or ')}, got ${urls.join(', ') || 'nothing'}`);
}

const share = hits / set.questions.length;
console.log(`eval_chat_retrieval: ${hits} of ${set.questions.length} questions find their page in the top ${topK} (${(share * 100).toFixed(0)}%)`);
for (const m of misses) console.log(`  miss: ${m.q}\n        expected ${m.expect}, got ${m.got.join(', ') || 'nothing'}`);

if (share < minimum) {
  console.error(`eval_chat_retrieval: below the threshold of ${(minimum * 100).toFixed(0)}%`);
  process.exit(1);
}
