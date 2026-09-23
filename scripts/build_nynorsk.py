#!/usr/bin/env python3
"""Generate the Nynorsk mirror (/nn/) from the Bokmål pages under site/no/.

Every Bokmål page is translated with Apertium's nob-nno pair and its e-infinitive
variant (moderate Nynorsk, "vi"), unless a reviewed Nynorsk page exists at the
same path under site/nn/, in which case the reviewed page wins and the
generated one is skipped. Generated pages go to site/nn-auto/ (ignored by git)
with permalinks under /nn/, carry the site's automatic-translation mark in the
footer and the experiment notice at the top (_includes/nynorsk-note.html,
rendered by the default layout for pages with translation.automatic), and link
to the Bokmål page they come from. The UI strings for Nynorsk
are generated the same way into site/_data/translations_nn.yml.

Liquid tags, code, link targets, HTML tags, Markdown emphasis markers, acronyms
and the glossary's protected names are cut out before translation and put back
afterwards, so the translator never sees them; the glossary's replacements are
applied to the output.

Translation runs locally when the apertium command is installed (the CI
runners install it), and otherwise through the public APy service at
apertium.org with a local cache, so a laptop without Apertium can still build.

Usage:
  python3 scripts/build_nynorsk.py            # generate
  python3 scripts/build_nynorsk.py --status   # only report what is reviewed and what is automatic
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

SRC = SITE_ROOT / "no"
REVIEWED = SITE_ROOT / "nn"
OUT = SITE_ROOT / "nn-auto"
CACHE = SITE_ROOT.parent / ".nynorsk-cache"
GLOSSARY = SITE_ROOT / "_data" / "nynorsk_glossary.yml"
TRANSLATIONS = SITE_ROOT / "_data" / "translations.yml"
TRANSLATIONS_NN = SITE_ROOT / "_data" / "translations_nn.yml"
STATUS = SITE_ROOT / "_data" / "nynorsk_status.yml"
APY = "https://apertium.org/apy/translate"
MODEL = "Apertium nob-nno (e-infinitiv)"
SKIP_DIRS = {"internal"}

# Things that must not be translated, in the order they are shielded.
PROTECT = [
    re.compile(r"```.*?```", re.S),                  # fenced code
    re.compile(r"\{%-?.*?-?%\}", re.S),               # Liquid tags
    re.compile(r"\{\{.*?\}\}", re.S),                 # Liquid output
    re.compile(r"<[^>]+>", re.S),                     # HTML tags
    re.compile(r"`[^`\n]+`"),                         # inline code
    re.compile(r"\]\([^)\s]+\)"),                     # link targets
    re.compile(r"https?://\S+"),                      # bare URLs
    re.compile(r"\*\*|__"),                           # strong emphasis markers
    # single-asterisk italics: shield the delimiters, translate what is between
    re.compile(r"(?<![\*\w])\*(?=[^\s*])|(?<=[^\s*])\*(?![\*\w])"),
    re.compile(r"\{:[^}]*\}"),                        # kramdown attributes
    re.compile(r"#[0-9a-fA-F]{3,8}(?![\w-])"),          # hex colour codes
    re.compile(r"(?<![\w-])[A-ZÆØÅ][A-ZÆØÅ0-9]{1,}(?![\w-])"),  # acronyms such as NVA, WCAG, RSS
]
SEP = "XQSEPX"
SEP_RE = re.compile(r"\s*XQSEPX\s*")
HEADING_RE = re.compile(r"^#{1,6}\s")


def strip_marks(text: str) -> str:
    """Remove the translator's generation-failure marks (#) from translated text.
    A Markdown heading marker at the start of a line is kept."""
    out = []
    for line in text.split("\n"):
        m = HEADING_RE.match(line)
        if m:
            out.append(m.group(0) + line[m.end():].replace("#", ""))
        else:
            out.append(line.replace("#", ""))
    return "\n".join(out)


LIST_MARKER_RE = re.compile(r"^(\s*)(\d+) \.(\s)", re.M)


def fix_list_markers(text: str) -> str:
    """Put back the space the translator inserts before the dot of an ordered
    list marker, which otherwise stops Markdown seeing a list at all."""
    return LIST_MARKER_RE.sub(r"\1\2.\3", text)


def load_glossary() -> dict:
    if not GLOSSARY.exists():
        return {"keep": [], "replace": {}}
    data = yaml.safe_load(GLOSSARY.read_text(encoding="utf-8")) or {}
    return {
        "keep": data.get("keep") or [],
        "replace": data.get("replace") or {},
        "expected_unused": data.get("expected_unused") or [],
    }


def segment(text: str, keep: list[str]) -> list[tuple[bool, str]]:
    """Split text into (protected, chunk) pairs; protected chunks are never translated."""
    spans: list[tuple[int, int]] = []
    for rx in PROTECT:
        spans += [(m.start(), m.end()) for m in rx.finditer(text)]
    for word in keep:
        spans += [(m.start(), m.end()) for m in re.finditer(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text)]
    spans.sort()
    merged: list[list[int]] = []
    for x, y in spans:
        if merged and x <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], y)
        else:
            merged.append([x, y])
    out: list[tuple[bool, str]] = []
    pos = 0
    for x, y in merged:
        if x > pos:
            out.append((False, text[pos:x]))
        out.append((True, text[x:y]))
        pos = y
    if pos < len(text):
        out.append((False, text[pos:]))
    return out


REPLACEMENTS_USED: dict[str, int] = {}


def apply_replacements(text: str, replace: dict[str, str]) -> str:
    for a, b in replace.items():
        n = text.count(a)
        if n:
            REPLACEMENTS_USED[a] = REPLACEMENTS_USED.get(a, 0) + n
            text = text.replace(a, b)
    return text


class Translator:
    """Bokmål to moderate Nynorsk, locally with apertium or through APy."""

    def __init__(self, use_local: bool | None = None) -> None:
        self.local = shutil.which("apertium") is not None if use_local is None else use_local
        CACHE.mkdir(exist_ok=True)

    def _apertium(self, text: str, mode: str) -> str:
        r = subprocess.run(["apertium", "-u", "-f", "txt", mode], input=text, capture_output=True, text=True, check=True)
        return r.stdout

    def _apy(self, text: str, pair: str) -> str:
        """The public service answers 500 now and then; retry with a pause before giving up."""
        import time
        import requests
        last = None
        for attempt in range(4):
            try:
                r = requests.post(APY, data={"langpair": pair, "q": text, "markUnknown": "no", "format": "txt"}, timeout=120)
                if r.status_code == 200:
                    return r.json()["responseData"]["translatedText"]
                last = RuntimeError(f"APy {r.status_code}")
            except requests.RequestException as exc:
                last = exc
            time.sleep(2 * (attempt + 1))
        raise last

    def translate(self, text: str) -> str:
        if not text.strip():
            return text
        key = hashlib.sha256(("v1|" + text).encode("utf-8")).hexdigest()
        cached = CACHE / (key + ".txt")
        if cached.exists():
            return cached.read_text(encoding="utf-8")
        if self.local:
            try:
                out = self._apertium(self._apertium(text, "nob-nno"), "nno-nno_e")
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                print(f"local apertium failed ({exc}); using the public service", file=sys.stderr)
                self.local = False
                out = self._apy(self._apy(text, "nob|nno"), "nno|nno_e")
        else:
            out = self._apy(self._apy(text, "nob|nno"), "nno|nno_e")
        cached.write_text(out, encoding="utf-8")
        return out


def translate_text(text: str, tr: Translator, glossary: dict) -> str:
    """Translate Markdown or plain text; protected spans pass through untouched.

    The translatable chunks are stripped of surrounding whitespace, joined with a
    separator line the translator leaves alone, translated in one call, and put
    back between the protected spans with their whitespace restored."""
    parts = segment(text, glossary["keep"])
    todo = [(i, c) for i, (prot, c) in enumerate(parts) if not prot and c.strip()]
    if not todo:
        return text
    stripped = [c.strip() for _, c in todo]
    try:
        translated = tr.translate(("\n\n" + SEP + "\n\n").join(stripped))
        pieces = SEP_RE.split(translated)
    except Exception as exc:  # a failed call must not abort the build
        print(f"translation of a block failed ({exc}); translating chunk by chunk", file=sys.stderr)
        pieces = []
    if len(pieces) != len(stripped):          # the translator ate a separator, or the block failed
        pieces = []
        for c in stripped:
            try:
                pieces.append(tr.translate(c))
            except Exception as exc:
                print(f"chunk left in Bokmål ({exc}): {c[:60]!r}", file=sys.stderr)
                pieces.append(c)
    result = [c for _, c in parts]
    for (i, original), piece in zip(todo, pieces):
        lead = original[: len(original) - len(original.lstrip())]
        trail = original[len(original.rstrip()):]
        result[i] = lead + strip_marks(piece.strip()) + trail
    return apply_replacements(fix_list_markers("".join(result)), glossary["replace"])


def split_front_matter(text: str) -> tuple[dict, str, str]:
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, "", text
    return yaml.safe_load(m.group(1)) or {}, m.group(1), m.group(2)


def nn_permalink(nb_permalink: str) -> str:
    assert nb_permalink.startswith("/no/"), nb_permalink
    return "/nn/" + nb_permalink[len("/no/"):]


def transform_page(text: str, rel: Path, tr: Translator, glossary: dict) -> str:
    data, _, body = split_front_matter(text)
    nb_permalink = data.get("permalink") or ("/no/" + rel.parent.as_posix().rstrip(".") + "/").replace("//", "/")
    if rel.name != "index.md" and rel.name != "index.html" and "permalink" not in data:
        nb_permalink = "/no/" + rel.with_suffix("").as_posix() + "/"
    data["lang"] = "nn"
    data["permalink"] = nn_permalink(nb_permalink)
    for key in ("title", "description"):
        if isinstance(data.get(key), str) and data[key].strip():
            data[key] = translate_text(data[key], tr, glossary).strip()
    data["translation"] = {
        "automatic": True,
        "source_url": nb_permalink,
        "model": MODEL,
        "original_label": "bokmålsoriginalen",
    }
    data["nynorsk_source"] = rel.as_posix()
    if "redirect_from" in data:
        del data["redirect_from"]
    front = yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000).rstrip("\n")
    return f"---\n{front}\n---\n{translate_text(body, tr, glossary)}"


def translate_ui_strings(tr: Translator, glossary: dict) -> dict:
    nb = yaml.safe_load(TRANSLATIONS.read_text(encoding="utf-8"))["nb"]
    nn: dict = {}
    for k, v in nb.items():
        if k == "lang_name":
            nn[k] = "Nynorsk"
        elif k == "lang_code":
            nn[k] = "nn"
        elif isinstance(v, str) and k.endswith("_url"):
            nn[k] = v.replace("/no/", "/nn/", 1) if v.startswith("/no/") else v
        elif isinstance(v, str) and v.strip():
            nn[k] = translate_text(v, tr, glossary).strip()
        else:
            nn[k] = v
    return nn


def iter_sources():
    for f in sorted(SRC.rglob("*")):
        if not f.is_file() or f.suffix not in (".md", ".html"):
            continue
        rel = f.relative_to(SRC)
        if rel.parts and rel.parts[0] in SKIP_DIRS:
            continue
        if not f.read_text(encoding="utf-8").startswith("---"):
            continue
        yield f, rel


def report_glossary_use(glossary: dict, expected_unused: set[str], engine: str, fail: bool) -> int:
    """Say which replacement rules did no work, so a dead one can be deleted.

    A rule listed under `expected_unused` in the glossary may legitimately match
    nothing: it repairs what only the other back end gets wrong, or it is a
    safety net for a term the translator currently handles by itself. Those are
    reported but never fail the run. Every other rule is expected to fire."""
    unused = [k for k in glossary["replace"] if k not in REPLACEMENTS_USED]
    dead = [k for k in unused if k not in expected_unused]
    allowed = [k for k in unused if k in expected_unused]
    fired = len(glossary["replace"]) - len(unused)
    print(f"glossary: {fired} of {len(glossary['replace'])} replacement rules fired via {engine}")
    for k in allowed:
        print(f"  unused here, kept on purpose: {k!r}")
    for k in dead:
        print(f"  MATCHED NOTHING: {k!r}")
    if dead and fail:
        print("A rule that matches nothing is either fixed upstream, aimed at the other back end,\n"
              "or written for a sentence that has since been rewritten. Delete it, or list it under\n"
              "expected_unused in site/_data/nynorsk_glossary.yml with a comment saying why.",
              file=sys.stderr)
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--status", action="store_true", help="report only; generate nothing")
    ap.add_argument("--apy", action="store_true", help="use the public APy service even if apertium is installed")
    ap.add_argument("--check-glossary", action="store_true",
                    help="fail if a replacement rule matched nothing in this run")
    args = ap.parse_args()

    glossary = load_glossary()
    expected_unused = set(glossary["expected_unused"])
    reviewed, automatic = [], []
    for f, rel in iter_sources():
        (reviewed if (REVIEWED / rel).exists() else automatic).append(rel.as_posix())
    if args.status:
        print(f"reviewed {len(reviewed)}, automatic {len(automatic)}")
        for r in automatic:
            print("  automatic:", r)
        return 0

    tr = Translator(use_local=False if args.apy else None)
    work = OUT.with_name(OUT.name + ".tmp")
    if work.exists():
        shutil.rmtree(work)
    n = 0
    for f, rel in iter_sources():
        if (REVIEWED / rel).exists():
            continue
        target = work / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(transform_page(f.read_text(encoding="utf-8"), rel, tr, glossary), encoding="utf-8")
        n += 1
    if OUT.exists():                          # swap in the finished mirror only when every page is done
        shutil.rmtree(OUT)
    work.rename(OUT)
    TRANSLATIONS_NN.write_text(
        "# Generated by scripts/build_nynorsk.py from the nb section of translations.yml. Do not edit.\n"
        + yaml.safe_dump(translate_ui_strings(tr, glossary), allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )
    STATUS.write_text(
        "# Generated by scripts/build_nynorsk.py. Do not edit.\n"
        + yaml.safe_dump({"reviewed": reviewed, "automatic": automatic}, allow_unicode=True),
        encoding="utf-8",
    )
    engine = "apertium" if tr.local else "apy"
    print(f"nynorsk: {n} pages generated, {len(reviewed)} reviewed, via {engine}")
    return report_glossary_use(glossary, expected_unused, engine, fail=args.check_glossary)


if __name__ == "__main__":
    sys.exit(main())
