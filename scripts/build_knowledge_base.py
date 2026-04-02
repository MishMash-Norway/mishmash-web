#!/usr/bin/env python3
"""
Build the MishMash chatbot knowledge base from site content.

Usage (from repo root):
    python3 scripts/build_knowledge_base.py

Output: chat/knowledge.json

To add your own documents:
    1. Place .md or .txt files in the chat/docs/ directory.
    2. Re-run this script.

Supported file types:
    .md   Markdown (front matter stripped automatically)
    .txt  Plain text
    .pdf  PDF (requires: pip install pypdf)
"""

import json
import math
import os
import re

# ── Site pages to always include ────────────────────────────────────────────
SITE_SOURCES = [
    ("about/index.md",   "About MishMash"),
    ("wp1/index.md",     "WP1: AI for Artistic Performances"),
    ("wp2/index.md",     "WP2: AI for Creative Processes"),
    ("wp3/index.md",     "WP3: AI for Well-being"),
    ("wp4/index.md",     "WP4: AI in Education"),
    ("wp5/index.md",     "WP5: AI in Creative Industries"),
    ("wp6/index.md",     "WP6: AI for Cultural Heritage"),
    ("wp7/index.md",     "WP7: AI for Problem-solving"),
    ("people/index.md",  "People"),
]

# Extra documents directory (relative to repo root)
DOCS_DIR = "chat/docs"

# News directory
NEWS_DIR = "_news"

STOP_WORDS = {
    'a','an','the','and','or','but','if','in','on','at','to','for','of','with',
    'by','from','is','it','be','as','so','we','he','she','they','you','i',
    'this','that','these','those','are','was','were','been','have','has','had',
    'do','does','did','will','would','could','should','may','might','can','not',
    'no','nor','yet','both','either','neither','also','than','then','when','where',
    'which','who','what','how','all','each','every','any','some','its','their',
    'our','your','his','her','more','into','through','about','such','only','very',
    'just','over','after','before','up','out','there','here','being','having',
}


# ── Text extraction ──────────────────────────────────────────────────────────

def strip_front_matter(text):
    """Remove YAML front matter delimited by ---."""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].strip()
    return text.strip()


def clean_text(text):
    """Strip HTML tags, markdown syntax, and excessive whitespace."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Remove markdown images
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    # Keep link text, drop URL
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove bold/italic markers
    text = re.sub(r'\*{1,3}([^*\n]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,3}([^_\n]+)_{1,3}', r'\1', text)
    # Remove fenced code blocks
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`[^`\n]+`', '', text)
    # Remove horizontal rules
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)
    # Collapse excess whitespace
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def read_markdown(path):
    with open(path, encoding='utf-8') as f:
        return clean_text(strip_front_matter(f.read()))


def read_text(path):
    with open(path, encoding='utf-8') as f:
        return clean_text(f.read())


def read_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        print(f"  Skipping {path} — install pypdf: pip install pypdf")
        return ""
    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return clean_text("\n\n".join(pages))


# ── Chunking ─────────────────────────────────────────────────────────────────

def split_into_chunks(text, source_label, max_words=350):
    """Split text at headings; further split oversized sections by paragraph."""
    # Split on header lines (## or ###)
    parts = re.split(r'\n(#{1,4} .+)', text)

    sections = []
    current_header = source_label
    current_body = []

    for part in parts:
        if re.match(r'^#{1,4} ', part):
            if current_body:
                sections.append((current_header, '\n'.join(current_body).strip()))
            current_header = re.sub(r'^#+\s*', '', part).strip()
            current_body = []
        else:
            current_body.append(part)

    if current_body:
        sections.append((current_header, '\n'.join(current_body).strip()))

    # Further split long sections by paragraph
    chunks = []
    for header, body in sections:
        words = body.split()
        if len(words) <= max_words:
            if len(words) >= 15:
                chunks.append({"source": header, "text": body})
        else:
            paras = [p.strip() for p in body.split('\n\n') if p.strip()]
            buf_words, buf_paras, part_num = [], [], 1
            for para in paras:
                pw = para.split()
                if buf_words and len(buf_words) + len(pw) > max_words:
                    if len(buf_words) >= 15:
                        label = f"{header} ({part_num})" if part_num > 1 else header
                        chunks.append({"source": label, "text": '\n\n'.join(buf_paras)})
                    buf_words, buf_paras, part_num = [], [], part_num + 1
                buf_words.extend(pw)
                buf_paras.append(para)
            if buf_words and len(buf_words) >= 15:
                label = f"{header} ({part_num})" if part_num > 1 else header
                chunks.append({"source": label, "text": '\n\n'.join(buf_paras)})

    return chunks


# ── TF-IDF ───────────────────────────────────────────────────────────────────

def tokenize(text):
    tokens = re.findall(r'\b[a-z][a-z0-9]*\b', text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 2]


def compute_tf(tokens):
    tf = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1
    total = len(tokens) or 1
    return {t: count / total for t, count in tf.items()}


def build_tfidf(chunks):
    # Compute TF per chunk
    for chunk in chunks:
        tokens = tokenize(chunk['text'])
        chunk['_tf'] = compute_tf(tokens)

    # Compute IDF
    N = len(chunks)
    doc_freq = {}
    for chunk in chunks:
        for term in chunk['_tf']:
            doc_freq[term] = doc_freq.get(term, 0) + 1

    # Exclude terms in > 75% of documents (too generic)
    threshold = 0.75 * N
    idf = {
        t: math.log(N / count + 1)
        for t, count in doc_freq.items()
        if count < threshold
    }

    # Compute final TF-IDF per chunk, drop raw TF
    for chunk in chunks:
        chunk['tfidf'] = {
            t: chunk['_tf'][t] * idf[t]
            for t in chunk['_tf'] if t in idf
        }
        del chunk['_tf']

    return idf


# ── Main ─────────────────────────────────────────────────────────────────────

def build(root_dir='.'):
    all_chunks = []

    # 1. Site pages
    print("Processing site pages…")
    for rel_path, label in SITE_SOURCES:
        full = os.path.join(root_dir, rel_path)
        if not os.path.exists(full):
            print(f"  not found: {rel_path}")
            continue
        text = read_markdown(full)
        chunks = split_into_chunks(text, label)
        print(f"  {rel_path}: {len(chunks)} chunks")
        all_chunks.extend(chunks)

    # 2. News items
    news_path = os.path.join(root_dir, NEWS_DIR)
    if os.path.isdir(news_path):
        news_chunks = []
        for fname in sorted(os.listdir(news_path)):
            if not fname.endswith('.md'):
                continue
            text = read_markdown(os.path.join(news_path, fname))
            label = "News: " + re.sub(r'^\d{4}-\d{2}-\d{2}-', '', fname[:-3]).replace('-', ' ').title()
            news_chunks.extend(split_into_chunks(text, label))
        print(f"  _news/: {len(news_chunks)} chunks")
        all_chunks.extend(news_chunks)

    # 3. Extra documents in chat/docs/
    docs_path = os.path.join(root_dir, DOCS_DIR)
    if os.path.isdir(docs_path):
        print(f"\nProcessing extra documents in {DOCS_DIR}/…")
        for fname in sorted(os.listdir(docs_path)):
            fpath = os.path.join(docs_path, fname)
            ext = os.path.splitext(fname)[1].lower()
            label = os.path.splitext(fname)[0].replace('-', ' ').replace('_', ' ').title()
            if ext == '.md':
                text = read_markdown(fpath)
            elif ext == '.txt':
                text = read_text(fpath)
            elif ext == '.pdf':
                text = read_pdf(fpath)
            else:
                continue
            chunks = split_into_chunks(text, label)
            print(f"  {fname}: {len(chunks)} chunks")
            all_chunks.extend(chunks)

    # Filter empty / trivial chunks
    all_chunks = [c for c in all_chunks if len(c['text'].split()) >= 15]

    print(f"\nTotal chunks before TF-IDF: {len(all_chunks)}")
    idf = build_tfidf(all_chunks)
    print(f"Vocabulary size: {len(idf)} terms")

    return {"chunks": all_chunks, "idf": idf}


if __name__ == '__main__':
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"Root: {root}\n")

    kb = build(root)

    out = os.path.join(root, 'chat', 'knowledge.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(kb, f, separators=(',', ':'), ensure_ascii=False)

    size = os.path.getsize(out) // 1024
    print(f"\nWritten: {out} ({size} KB, {len(kb['chunks'])} chunks)")
    print("\nTo add your own documents:")
    print(f"  1. Place .md / .txt / .pdf files in  {os.path.join(root, 'chat', 'docs')}/")
    print(f"  2. Re-run:  python3 scripts/build_knowledge_base.py")
