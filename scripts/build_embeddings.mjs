// Build-time embeddings for the on-device semantic search (issue #57).
// Reads the built search index (_site/search.json), embeds title, description
// and the start of each item's text with a small multilingual sentence model,
// and writes _site/data/embeddings.bin (float32, L2-normalised, row per item)
// plus _site/data/embeddings.json (the items and the model name). The same
// model runs in the reader's browser to embed the query, so nothing about the
// query leaves the device.
//
//   node scripts/build_embeddings.mjs [--site _site]
import { pipeline, env } from '@xenova/transformers';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const MODEL = 'Xenova/paraphrase-multilingual-MiniLM-L12-v2';
const site = process.argv.includes('--site') ? process.argv[process.argv.indexOf('--site') + 1] : '_site';
env.allowLocalModels = false;

const raw = JSON.parse(readFileSync(join(site, 'search.json'), 'utf8'));
const items = raw
  .filter((it) => it.url && it.url !== '/404.html' && !it.url.startsWith('/internal') && !it.url.startsWith('/nn/'))
  .map((it) => ({
    url: it.url,
    title: it.title,
    type: it.type,
    text: [it.title, it.description, (it.content || '').replace(/\s+/g, ' ').slice(0, 400)].filter(Boolean).join('. '),
  }));

const extractor = await pipeline('feature-extraction', MODEL, { quantized: true });
const dim = 384;
const out = new Float32Array(items.length * dim);
const t0 = Date.now();
for (let i = 0; i < items.length; i += 16) {
  const batch = items.slice(i, i + 16).map((it) => it.text);
  const res = await extractor(batch, { pooling: 'mean', normalize: true });
  out.set(res.data, i * dim);
}
mkdirSync(join(site, 'data'), { recursive: true });
writeFileSync(join(site, 'data', 'embeddings.bin'), Buffer.from(out.buffer));
writeFileSync(join(site, 'data', 'embeddings.json'), JSON.stringify({
  model: MODEL, dim, count: items.length, generated_at: new Date().toISOString(),
  items: items.map(({ url, title, type }) => ({ url, title, type })),
}));
console.log(`embeddings: ${items.length} items, ${dim} dims, ${((Date.now() - t0) / 1000).toFixed(0)}s`);
