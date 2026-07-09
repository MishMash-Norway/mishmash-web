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

# ── Site walking configuration ───────────────────────────────────────────────
# All published English markdown pages are included. These directories are
# skipped when walking the site root (collections with dedicated handling,
# build output, assets, and the Norwegian mirror, which duplicates content).
SKIP_DIRS = {
    "_site", "_layouts", "_includes", "_data", "assets", "images",
    "chat", "no", "ui", "_directory", "_news", "_events",
}

# Extra documents directory (relative to repo root)
DOCS_DIR = "chat/docs"

# Collections with dedicated labels
NEWS_DIR = "_news"
EVENTS_DIR = "_events"
DIRECTORY_DIR = "_directory"

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


def parse_front_matter(path):
    """Return (front matter dict, body) for a markdown file."""
    import yaml
    with open(path, encoding='utf-8') as f:
        raw = f.read()
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            try:
                fm = yaml.safe_load(raw[3:end]) or {}
            except yaml.YAMLError:
                fm = {}
            return fm, raw[end + 4:]
    return {}, raw


def clean_text(text):
    """Strip HTML tags, markdown syntax, and excessive whitespace."""
    # Remove Liquid tags and expressions
    text = re.sub(r'{%.*?%}', ' ', text, flags=re.DOTALL)
    text = re.sub(r'{{.*?}}', ' ', text, flags=re.DOTALL)
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

def page_label(fm, rel_path):
    title = str(fm.get('title') or '').strip()
    if title:
        return title
    label = os.path.dirname(rel_path) or rel_path
    return label.replace('/', ' / ').replace('-', ' ').title() or 'Home'


def walk_site_pages(root_dir):
    """Yield (rel_path, label, body) for every published English page."""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        rel_dir = os.path.relpath(dirpath, root_dir)
        top = rel_dir.split(os.sep)[0]
        if top in SKIP_DIRS:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in sorted(dirnames) if not (rel_dir == '.' and d in SKIP_DIRS)]
        for fname in sorted(filenames):
            if not fname.endswith('.md'):
                continue
            full = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(full, root_dir)
            fm, body = parse_front_matter(full)
            if fm.get('published') is False or fm.get('sitemap') is False:
                continue
            yield rel_path, page_label(fm, rel_path), clean_text(body)


def directory_entry_chunks(root_dir):
    """One compact chunk per published person/project/institution entry."""
    chunks = []
    sections = [
        ('people', 'Person'),
        ('projects', 'Project'),
        ('institutions', 'Institution'),
    ]
    for section, kind in sections:
        base = os.path.join(root_dir, DIRECTORY_DIR, section)
        if not os.path.isdir(base):
            continue
        count = 0
        for slug in sorted(os.listdir(base)):
            if slug.startswith('_'):
                continue
            index_md = os.path.join(base, slug, 'index.md')
            if not os.path.exists(index_md):
                continue
            fm, body = parse_front_matter(index_md)
            if fm.get('published') is False:
                continue
            name = str(fm.get('name') or slug).strip()
            facts = []
            if kind == 'Person':
                position = str(fm.get('position') or '').strip()
                department = str(fm.get('department') or '').strip()
                if position:
                    facts.append(f"{name} is {position}" + (f" at {department}" if department else "") + ".")
                wps = fm.get('wps') or []
                if wps:
                    facts.append(f"Work packages: {', '.join(map(str, wps))}.")
            summary = str(fm.get('summary') or '').strip()
            text_parts = facts + ([summary] if summary else [])
            body_text = clean_text(body)
            if body_text and body_text.lower() not in ('bio.', 'bio coming soon.'):
                text_parts.append(body_text)
            text = '\n\n'.join(dict.fromkeys(text_parts))
            if len(text.split()) < 10:
                continue
            for chunk in split_into_chunks(text, f"{kind}: {name}"):
                chunk['source'] = f"{kind}: {name}"
                chunks.append(chunk)
            count += 1
        print(f"  _directory/{section}: {count} entries")
    return chunks


def build(root_dir='.'):
    all_chunks = []

    # 1. Site pages (all published English markdown)
    print("Processing site pages…")
    page_count = 0
    for rel_path, label, text in walk_site_pages(root_dir):
        chunks = split_into_chunks(text, label)
        for chunk in chunks:
            if chunk['source'] != label:
                chunk['source'] = f"{label} — {chunk['source']}"
        if chunks:
            page_count += 1
            all_chunks.extend(chunks)
    print(f"  {page_count} pages")

    # 2. Directory entries (people, projects, institutions)
    print("Processing directory…")
    all_chunks.extend(directory_entry_chunks(root_dir))

    # 3. News and events
    for coll_dir, prefix in ((NEWS_DIR, 'News'), (EVENTS_DIR, 'Event')):
        coll_path = os.path.join(root_dir, coll_dir)
        if not os.path.isdir(coll_path):
            continue
        coll_chunks = []
        for fname in sorted(os.listdir(coll_path)):
            if not fname.endswith('.md'):
                continue
            full = os.path.join(coll_path, fname)
            fm, body = parse_front_matter(full)
            if fm.get('published') is False:
                continue
            title = str(fm.get('title') or '').strip() or re.sub(
                r'^\d{4}-\d{2}-\d{2}-', '', fname[:-3]).replace('-', ' ').title()
            date = re.match(r'^(\d{4}-\d{2}-\d{2})-', fname)
            label = f"{prefix}: {title}" + (f" ({date.group(1)})" if date else "")
            text = clean_text(body)
            for chunk in split_into_chunks(text, label):
                chunk['source'] = label
                coll_chunks.append(chunk)
        print(f"  {coll_dir}/: {len(coll_chunks)} chunks")
        all_chunks.extend(coll_chunks)

    # 4. Extra documents in chat/docs/
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
    import os

    from repo_paths import SITE_ROOT

    root = str(SITE_ROOT)
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
