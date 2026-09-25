#!/usr/bin/env python3
"""Build the text alternative for the opening ceremony recording (WCAG 1.2.8).

The recording on YouTube has two caption tracks made by hand from the
automatic captions: a full Norwegian track, and a full English track that is
a translation where Norwegian was spoken. A transcript that stands in for the
recording has to carry each part in the language it was spoken in, so this
takes the edited Norwegian track for the Norwegian parts and the original
captions for the two parts spoken in English, where the English track is a
translation of a translation.

The programme comes from the event page, with the time each part begins.
Cues are joined into paragraphs, a line that repeats the end of the previous
cue is dropped, and the names the programme gives are put back where the
captions misheard them. Nothing else in the text is changed.

The pages are written with published: false. They go live when someone has
read them against the recording and removes that line.

Usage:
  python3 scripts/build_opening_transcript.py /path/to/video/export
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

NB_TRACK = "captions_first_panel_translated_no_complete.vtt"
ORIGINAL = "2026-04-08-MishMash_Aulaen.vtt"
VIDEO_ID = "rq8UnZlzYk4"

# The programme as it happened, from the event page. Source names the caption
# track a part is read from: the edited Norwegian track, or the original
# captions where English was spoken.
PROGRAMME = [
    (0,    "Flytpunkt 1 (extract)", "Flytpunkt 1 (utdrag)", "Victoria Johnson, Barratt Due and University of Oslo; Anders Tveit, Norwegian Academy of Music", "nb"),
    (610,  "Welcome", "Velkommen", "Rector Ragnhild Hennum, University of Oslo", "nb"),
    (900,  "Address", "Hilsen", "Minister of Research and Higher Education Sigrun Aasland", "nb"),
    (1090, "Dancing Embryo", "Dancing Embryo", "Diego Marin, University of Oslo; Benedikte Wallace, University of Oslo", "orig"),
    (1540, "Panel: Bransje i bekymring, Industry in Concern", "Panel: Bransje i bekymring", "Øystein Strand, Arts and Culture Norway; Nina Frederikke Grünfeld, Inland Norway University of Applied Sciences; Andrew Melchior; chaired by Daniel Nordgård, University of Agder", "orig"),
    (2860, "Rhythm and AI", "Rytme og KI", "Daniel Formo, Norwegian University of Science and Technology", "nb"),
    (3245, "Artistic Intelligence", "Kunstnerisk intelligens", "Synne Tollerud Bull, Kristiania", "nb"),
    (3650, "The centre's Artistic Readiness Level", "Senterets Artistic Readiness Level", "MishMash", "nb"),
    (3810, "Skurdalsbruri", "Skurdalsbruri", "Joan Gatti, Norwegian Academy of Music; Olivier Lartillot, University of Oslo; Lars Monstad, University of Oslo", "nb"),
    (4230, "Panel: Kunnskaping, kultur og KI, Knowledge, Culture and AI", "Panel: Kunnskaping, kultur og KI", "Åse Wetås, National Library of Norway; Helge Jordheim, University of Oslo; Anne Kjersti Fahlvik, The Research Council of Norway; chaired by Ida Jahr, Inland Norway University of Applied Sciences", "nb"),
    (5590, "Video Percussion", "Video Percussion", "Koka Nikoladze, Norwegian Academy of Music", "nb"),
]
END = 6136

# What the captions made of a name, and what the programme calls the person.
NAMES = {
    "Ida Jar ": "Ida Jahr ",
    "Koka Nikolas ": "Koka Nikoladze ",
    "Koka Nikolas.": "Koka Nikoladze.",
    "Nikolatse": "Nikoladze",
    "Benedikte Walles": "Benedikte Wallace",
    "Anders Treit": "Anders Tveit",
    "Nordgaard": "Nordgård",
    "Norgård": "Nordgård",
    "Jorheim": "Jordheim",
    "i Auland": "i Aulaen",
    "Irkan": "IRCAM",
}

# The Norwegian captions write a lone "K" where "KI" was said, in dozens of
# places ("senter for K og kreativitet", "snakker om K"). No Norwegian sentence
# has a bare capital K as a word, so the token is restored throughout.
LONE_K = re.compile(r"(?<![\w-])K(?![\w-])")

TIME_RE = re.compile(r"(?:(\d+):)?(\d+):(\d+)\.(\d+) --> (?:(\d+):)?(\d+):(\d+)\.(\d+)")


def read_cues(path: Path) -> list[tuple[float, float, list[str]]]:
    cues: list = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = TIME_RE.match(line)
        if m:
            g = [int(x) if x else 0 for x in m.groups()]
            cues.append((g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000,
                         g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, []))
        elif cues and line.strip() and not line.startswith(("WEBVTT", "Kind:", "Language:")):
            cues[-1][2].append(line.strip())
    return cues


def is_placeholder(text: str) -> bool:
    return "..." in text or text.startswith("[") or not re.search(r"[A-Za-zÆØÅæøå]", text)


def paragraphs(cues, start: float, end: float) -> list[str]:
    """Join the cues of one part into paragraphs.

    A new paragraph starts after a pause of more than four seconds, or when a
    sentence has just ended and the paragraph is already long."""
    out: list[str] = []
    current: list[str] = []
    last_end = None
    last_line = None
    for c_start, c_end, lines in cues:
        if c_start < start or c_start >= end:
            continue
        text = " ".join(lines)
        if is_placeholder(text):
            continue
        # a cue whose first line repeats the previous cue's last line
        if last_line and lines and lines[0] == last_line:
            lines = lines[1:]
            text = " ".join(lines)
            if not text:
                continue
        gap = (c_start - last_end) if last_end is not None else 0
        joined = " ".join(current)
        if current and (gap > 4 or (len(joined) > 700 and joined.rstrip().endswith((".", "?", "!")))):
            out.append(joined)
            current = []
        current.append(text)
        last_end = c_end
        last_line = lines[-1] if lines else None
    if current:
        out.append(" ".join(current))
    cleaned = []
    for p in out:
        p = re.sub(r"\s+", " ", p).strip()
        for wrong, right in NAMES.items():
            p = p.replace(wrong, right)
        p = LONE_K.sub("KI", p)
        cleaned.append(p)
    return cleaned


def clock(seconds: float) -> str:
    s = int(seconds)
    h, rest = divmod(s, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02}:{s:02}" if h else f"{m}:{s:02}"


def render(lang: str, parts: list[tuple]) -> str:
    en = lang == "en"
    title = "Opening ceremony: transcript" if en else "Åpningsseremonien: utskrift"
    intro = (
        "This is the text alternative to the [recording of the opening ceremony](/events/aulaen2026/) on 8 April 2026, "
        "for anyone who cannot watch or hear it. Each part is given in the language it was spoken in: Norwegian for most of the evening, "
        "English for the dance introduction and the first panel. The text comes from the captions of the recording, joined into paragraphs, "
        "with the names of the programme put back where the captions misheard them. The music is not described; the "
        "[lab page](/lab/opening-ceremony/) plays the recording from the start of any part."
        if en else
        "Dette er tekstalternativet til [opptaket av åpningsseremonien](/events/aulaen2026/) 8. april 2026, for den som ikke kan se eller høre det. "
        "Hver del gjengis på språket den ble holdt på: norsk det meste av kvelden, engelsk for danseintroduksjonen og den første panelsamtalen. "
        "Teksten kommer fra tekstingen av opptaket, satt sammen til avsnitt, med navnene fra programmet satt inn der tekstingen hørte feil. "
        "Musikken er ikke beskrevet; [lab-siden](/lab/opening-ceremony/) spiller opptaket fra starten av hver del."
    )
    out = [
        "---",
        "layout: page",
        f"title: \"{title}\"",
        f"permalink: {'/events/aulaen2026/transcript/' if en else '/no/events/aulaen2026/transcript/'}",
        f"translation_url: {'/no/events/aulaen2026/transcript/' if en else '/events/aulaen2026/transcript/'}",
        *([] if en else ["lang: nb"]),
        ("description: \"The opening ceremony of 8 April 2026 as text, part by part, in the language each part was spoken in.\""
         if en else
         "description: \"Åpningsseremonien 8. april 2026 som tekst, del for del, på språket hver del ble holdt på.\""),
        "published: false",
        "---",
        "",
        intro,
        "",
    ]
    for start, name_en, name_nb, who, source, paras, lang_of_part in parts:
        out.append(f"## {clock(start)} {name_en if en else name_nb}")
        out.append("")
        out.append(f"*{who}*")
        out.append("")
        if not paras:
            out.append("[Music, no speech]" if en else "[Musikk, ingen tale]")
            out.append("")
            continue
        out.append(f'<div lang="{lang_of_part}" markdown="1">')
        for p in paras:
            out.append(p)
            out.append("")
        out.append("</div>")
        out.append("")
    return "\n".join(out).replace("\n\n\n", "\n\n").rstrip() + "\n"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    folder = Path(sys.argv[1])
    nb = read_cues(folder / NB_TRACK)
    orig = read_cues(folder / ORIGINAL)
    parts = []
    for i, (start, name_en, name_nb, who, source) in enumerate(PROGRAMME):
        end = PROGRAMME[i + 1][0] if i + 1 < len(PROGRAMME) else END
        cues = orig if source == "orig" else nb
        paras = paragraphs(cues, start, end)
        parts.append((start, name_en, name_nb, who, source, paras, "en" if source == "orig" else "nb"))
    targets = {
        "en": SITE_ROOT / "events" / "aulaen2026-transcript" / "index.md",
        "nb": SITE_ROOT / "no" / "events" / "aulaen2026-transcript" / "index.md",
    }
    for lang, path in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(lang, parts), encoding="utf-8")
    words = sum(len(p.split()) for part in parts for p in part[5])
    print(f"transcript: {len(parts)} parts, {words} words, written to {targets['en']} and {targets['nb']} (published: false)")
    for part in parts:
        print(f"  {clock(part[0]):>8} {part[1][:44]:46} {part[4]:5} {sum(len(p.split()) for p in part[5]):5} words")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
