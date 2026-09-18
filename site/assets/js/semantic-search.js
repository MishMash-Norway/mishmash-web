/* Semantic search on the reader's device (see /lab/semantic-search/, issue #57).
   The site's items were embedded at build time (scripts/build_embeddings.mjs).
   Here the same model embeds the query in the browser and the closest items
   are listed. The model library and weights come from a public content
   network on first use; the query itself never leaves the device. */
const box = document.getElementById('semantic-search');
const form = document.getElementById('semantic-form');
const input = document.getElementById('semantic-query');
const status = document.getElementById('semantic-status');
const list = document.getElementById('semantic-results');
const keywordList = document.getElementById('keyword-results');
let searchIndex = null;
const LIB = 'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2';

let index = null, vectors = null, extractor = null;
/* The keyword index is small and needed for the right-hand column, so it is
   fetched while the reader is still typing rather than after the first query. */
let searchIndexPromise = fetch('/search.json').then((r) => r.json()).catch(() => []);

async function loadIndex() {
  if (index) return;
  status.textContent = 'Loading the index…';
  const [meta, bin] = await Promise.all([
    fetch(box.dataset.index).then((r) => r.json()),
    fetch(box.dataset.vectors).then((r) => r.arrayBuffer()),
  ]);
  index = meta; vectors = new Float32Array(bin);
}

/* The same query against the site's own keyword index, matched the way the
   search page matches: every word must appear in the title, description or
   text of an item. */
async function keywordMatches(query, n) {
  if (!searchIndex) searchIndex = await searchIndexPromise;
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  const hits = [];
  for (const it of searchIndex) {
    if (!it.url || it.url === '/404.html' || it.url.startsWith('/internal')) continue;
    const hay = `${it.title || ''} ${it.description || ''} ${it.content || ''}`.toLowerCase();
    if (words.every((w) => hay.includes(w))) hits.push(it);
    if (hits.length >= n) break;
  }
  return hits;
}

function renderInto(target, rows) {
  target.textContent = '';
  if (!rows.length) {
    const li = document.createElement('li');
    li.className = 'small muted';
    li.textContent = 'Nothing contains all of those words.';
    target.appendChild(li);
    return;
  }
  rows.forEach(({ url, title, type, score }) => {
    const li = document.createElement('li');
    const a = document.createElement('a'); a.href = url; a.textContent = title;
    const meta = document.createElement('span'); meta.className = 'small muted';
    meta.textContent = score === undefined ? ` ${type}` : ` ${type} · ${score.toFixed(2)}`;
    li.appendChild(a); li.appendChild(meta); target.appendChild(li);
  });
}

async function loadModel() {
  if (extractor) return;
  status.textContent = 'Loading the model (about 130 MB, once)…';
  const { pipeline, env } = await import(LIB);
  env.allowLocalModels = false;
  extractor = await pipeline('feature-extraction', index.model, {
    quantized: true,
    progress_callback: (p) => { if (p.status === 'progress' && p.file && p.file.endsWith('.onnx')) status.textContent = `Loading the model… ${Math.round(p.progress || 0)} %`; },
  });
}

function topMatches(q, n) {
  const dim = index.dim, scores = [];
  for (let i = 0; i < index.count; i++) {
    let s = 0; const off = i * dim;
    for (let j = 0; j < dim; j++) s += q[j] * vectors[off + j];
    scores.push([s, i]);
  }
  scores.sort((a, b) => b[0] - a[0]);
  return scores.slice(0, n);
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (!q) return;
  try {
    await loadIndex(); await loadModel();
    status.textContent = 'Searching…';
    const t0 = performance.now();
    const out = await extractor(q, { pooling: 'mean', normalize: true });
    const hits = topMatches(out.data, 12);
    renderInto(list, hits.map(([score, i]) => ({ ...index.items[i], score })));
    const elapsed = Math.round(performance.now() - t0);
    renderInto(keywordList, await keywordMatches(q, 12));
    status.textContent = `${hits.length} closest of ${index.count} items, in ${elapsed} ms on your device.`;
  } catch (err) {
    status.textContent = 'The model could not be loaded. The keyword search still works.';
    console.error(err);
  }
});
