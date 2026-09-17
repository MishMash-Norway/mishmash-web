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
const LIB = 'https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2';

let index = null, vectors = null, extractor = null;

async function loadIndex() {
  if (index) return;
  status.textContent = 'Loading the index…';
  const [meta, bin] = await Promise.all([
    fetch(box.dataset.index).then((r) => r.json()),
    fetch(box.dataset.vectors).then((r) => r.arrayBuffer()),
  ]);
  index = meta; vectors = new Float32Array(bin);
}

async function loadModel() {
  if (extractor) return;
  status.textContent = 'Loading the model (about 30 MB, once)…';
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
    list.textContent = '';
    hits.forEach(([score, i]) => {
      const it = index.items[i];
      const li = document.createElement('li');
      const a = document.createElement('a'); a.href = it.url; a.textContent = it.title;
      const meta = document.createElement('span'); meta.className = 'small muted';
      meta.textContent = ` ${it.type} · ${score.toFixed(2)}`;
      li.appendChild(a); li.appendChild(meta); list.appendChild(li);
    });
    status.textContent = `${hits.length} closest of ${index.count} items, in ${Math.round(performance.now() - t0)} ms on your device.`;
  } catch (err) {
    status.textContent = 'The model could not be loaded. The keyword search still works.';
    console.error(err);
  }
});
