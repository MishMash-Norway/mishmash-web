/* Retrieval for the Ask MishMash assistant (site/chat/index.html).
   The passages come from /chat/knowledge.json, built by
   scripts/build_knowledge_base.py, and are ranked by cosine similarity over
   TF-IDF. The module is separate from the page so that the same code can be
   scored against a set of questions by scripts/eval_chat_retrieval.mjs. */

export const STOP_WORDS = new Set([
  'a', 'an', 'the', 'and', 'or', 'but', 'if', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
  'by', 'from', 'is', 'it', 'be', 'as', 'so', 'we', 'he', 'she', 'they', 'you', 'i',
  'this', 'that', 'these', 'those', 'are', 'was', 'were', 'been', 'have', 'has', 'had',
  'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'not',
  'no', 'nor', 'yet', 'both', 'either', 'neither', 'also', 'than', 'then', 'when', 'where',
  'which', 'who', 'what', 'how', 'all', 'each', 'every', 'any', 'some', 'its', 'their',
  'our', 'your', 'his', 'her', 'more', 'into', 'through', 'about', 'such', 'only', 'very',
  'just', 'over', 'after', 'before', 'up', 'out', 'there', 'here', 'being', 'having',
]);

const WP_RE = /\b(?:work[\s-]*package|arbeidspakke|wp)[\s.-]*([1-7])\b/gi;
const AI_RE = /\bkunstig[\s-]*intelligens\w*\b|\bki\b/gi;
const AI_EN_RE = /\bartificial[\s-]*intelligence\b|\bai\b/gi;

/** Write the centre's own shorthand the same way everywhere: work package 3 is WP3.
    Kept identical to normalise() in scripts/build_knowledge_base.py; the two are
    compared by tests/chat/tokenizer-cases.json. */
export function normalise(text) {
  return text
    .toLowerCase()
    .replace(WP_RE, (_, n) => `wp${n}`)
    .replace(AI_RE, 'kix')
    .replace(AI_EN_RE, 'aix');
}

export function tokenize(text) {
  // A letter followed by letters or digits, in any alphabet, so that bokmål,
  // Bærekraft and Kunstsilo are words rather than fragments. Kept identical to
  // tokenize() in scripts/build_knowledge_base.py.
  return (normalise(text).match(/[\p{L}][\p{L}\p{N}]*/gu) || [])
    .filter((t) => !STOP_WORDS.has(t) && t.length > 2);
}

/** The passages that answer a question best, most relevant first.
    At most `perPage` passages come from any one page. One is the default and
    the measured best: four passages from the same page tell the model the same
    thing four times and crowd out the page that holds the rest of the answer.
    Scored against tests/chat/questions.json, one per page finds every
    question's page where two finds 30 of 31. */
export function retrieve(knowledgeBase, query, topK = 4, floor = 0.05, perPage = 1) {
  if (!knowledgeBase) return [];
  const queryTokens = tokenize(query);
  if (queryTokens.length === 0) return [];

  const tf = {};
  for (const t of queryTokens) tf[t] = (tf[t] || 0) + 1;
  const total = queryTokens.length;

  const queryVec = {};
  for (const t in tf) {
    if (knowledgeBase.idf[t]) queryVec[t] = (tf[t] / total) * knowledgeBase.idf[t];
  }
  const queryNorm = Math.sqrt(Object.values(queryVec).reduce((s, v) => s + v * v, 0));
  if (queryNorm === 0) return [];

  const scored = knowledgeBase.chunks.map((chunk) => {
    let dot = 0;
    for (const t in queryVec) {
      if (chunk.tfidf[t]) dot += queryVec[t] * chunk.tfidf[t];
    }
    const chunkNorm = Math.sqrt(Object.values(chunk.tfidf).reduce((s, v) => s + v * v, 0));
    return { chunk, score: chunkNorm > 0 ? dot / (queryNorm * chunkNorm) : 0 };
  });

  const ranked = scored
    .filter((s) => s.score > floor)
    .sort((a, b) => b.score - a.score);

  const taken = new Map();
  const chosen = [];
  for (const s of ranked) {
    if (chosen.length >= topK) break;
    const key = s.chunk.url || s.chunk.source;
    const n = taken.get(key) || 0;
    if (n >= perPage) continue;
    taken.set(key, n + 1);
    chosen.push(s.chunk);
  }
  return chosen;
}

/** The passages, laid out for the model, with the page each one comes from. */
export function buildAugmentedContent(userText, chunks) {
  if (chunks.length === 0) return userText;
  const context = chunks
    .map((c) => `[${c.source}${c.url ? ' — ' + c.url : ''}]\n${c.text}`)
    .join('\n\n---\n\n');
  return `Passages from the MishMash website:\n\n${context}\n\n---\n\nQuestion: ${userText}`;
}

/** One entry per page behind the answer, in the order the passages were ranked. */
export function sourcesOf(chunks) {
  const seen = new Map();
  for (const c of chunks) {
    const key = c.url || c.source;
    if (!seen.has(key)) seen.set(key, { label: c.source, url: c.url || null });
  }
  return [...seen.values()];
}
