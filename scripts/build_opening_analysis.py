#!/usr/bin/env python3
"""Put the opening ceremony analysis on the web page (/lab/opening-ceremony/).

Read-only on the analysis folder, which lives outside this repository because the
recording and its caches are several gigabytes. This script takes what the page
needs and leaves the rest where it is.

It does two things:

  curves    Every measured track in the analysis is sampled at 1 Hz, which is
            6,136 points for this recording and far more than a strip 1,400
            pixels wide can show. Each one is reduced to one value per 10
            seconds, the same hop the level curve already uses, so that every
            lane on the page shares one time axis. The reduction is the mean,
            except for the tracks that are events rather than states, where the
            maximum is what a reader wants to see.

  strips    The videogram, motiongram and colourgram are written at one common
            height. Their source images have three different heights, because
            each comes from a different tool and means something different
            vertically, and a page that shows them at their own heights makes
            that difference look like information. It is not: the vertical axis
            of a strip is a drawing choice, and the three are comparable only
            when they are the same size.

The page's own JSON is edited in place rather than rewritten, since parts of it
were set by hand: the rights statement, the privacy note and the programme.

Usage:
  python3 scripts/build_opening_analysis.py
  python3 scripts/build_opening_analysis.py --analysis /path/to/analysis --hop 10
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from repo_paths import SITE_ROOT

ANALYSIS = Path.home() / "UiO Dropbox/alexanje@uio.no/arkiv/2026/2026-04-08-MishMash-apning/analysis"
DATA = SITE_ROOT / "assets" / "data" / "opening-ceremony-segments.json"
IMAGES = SITE_ROOT / "assets" / "images" / "lab"
STRIP_WIDTH = 1400
STRIP_HEIGHT = 110

# file, key in that file, id, label, unit, and whether a window is summed up by its peak
CURVES = [
    ("audio_features.json", "centroid_hz", "centroid_hz", "Spectral centroid", "Hz", False),
    ("audio_features.json", "bandwidth_hz", "bandwidth_hz", "Spectral bandwidth", "Hz", False),
    ("audio_features.json", "rolloff_hz", "rolloff_hz", "Spectral rolloff", "Hz", False),
    ("audio_features.json", "flatness", "flatness", "Spectral flatness", "", False),
    ("audio_features.json", "zcr", "zcr", "Zero-crossing rate", "", False),
    ("audio_features.json", "onset_rate", "onset_rate", "Onset rate", "onsets/s", True),
    ("loudness.json", "momentary_lufs_1hz", "loudness_m", "Momentary loudness", "LUFS", False),
    ("picture_colour.json", "brightness", "brightness", "Picture brightness", "0..1", False),
    ("picture_colour.json", "saturation", "saturation", "Picture saturation", "0..1", False),
    ("motion_vectors.json", "magnitude", "mv_qom", "Motion from the codec vectors", "px", True),
    ("motion_vectors.json", "global_motion", "mv_global", "Camera motion from the vectors", "px", True),
    # avsegmenter labels this one "share of concert max", but the values run past 1
    # on this recording, so the plot carries no unit until that is settled.
    ("segments.json", "qom", "qom", "Quantity of motion", "", False),
]

FLAT_NOTE = (
    "These came back empty. The reader takes motion vectors from P-frames, and this "
    "recording is AV1, which it cannot read. The frame-based quantity of motion is "
    "plotted instead, and measures the same thing a different way."
)

STRIPS = [
    ("videogram.png", "opening-videogram.webp"),
    ("motiongram.png", "opening-motiongram.webp"),
    ("colourgram.png", "opening-colourgram.webp"),
]


def values_of(blob: dict, key: str) -> list:
    """The track may sit at the top level or inside a 'tracks' map."""
    if key in blob and isinstance(blob[key], list):
        return blob[key]
    return (blob.get("tracks") or {}).get(key, [])


def hop_of(blob: dict, filename: str) -> float:
    """segments.json keeps the hop beside the tracks rather than at the top."""
    if filename == "segments.json":
        return (blob.get("tracks") or {}).get("hop_s", 1.0)
    return blob.get("hop_s", 1.0)


def reduce_curve(values: list, hop_in: float, hop_out: float, peak: bool) -> list:
    """One value per hop_out seconds, dropping the gaps the feature run left behind."""
    per = max(1, round(hop_out / hop_in))
    out = []
    for i in range(0, len(values), per):
        window = [v for v in values[i:i + per] if isinstance(v, (int, float))]
        if not window:
            out.append(None)
            continue
        out.append(max(window) if peak else sum(window) / len(window))
    return out


def tidy(values: list) -> tuple[list, list]:
    """Round to what a 1,400 pixel strip can show, and report the range."""
    real = [v for v in values if v is not None]
    if not real:
        return values, [0, 0]
    span = max(real) - min(real)
    places = 0 if span > 100 else (2 if span > 1 else 4)
    rounded = [None if v is None else round(v, places) for v in values]
    return rounded, [round(min(real), places), round(max(real), places)]


def build_curves(analysis: Path, hop_out: float) -> tuple[list[dict], list[dict]]:
    cache: dict[str, dict] = {}
    curves: list[dict] = []
    skipped: list[dict] = []
    for filename, key, cid, label, unit, peak in CURVES:
        path = analysis / filename
        if not path.exists():
            print(f"  {filename} is missing, {cid} left out")
            continue
        blob = cache.setdefault(filename, json.loads(path.read_text()))
        raw = values_of(blob, key)
        if not raw:
            print(f"  {filename} holds no {key}, left out")
            continue
        reduced = reduce_curve(raw, hop_of(blob, filename), hop_out, peak)
        values, span = tidy(reduced)
        if span[0] == span[1]:
            # A track that never moves measured nothing. Drawing it would show a
            # straight line where a reader expects a measurement.
            skipped.append({"label": label, "value": span[0]})
            print(f"  {cid:<14} is flat at {span[0]}, left out of the plots")
            continue
        curves.append({
            "id": cid, "label": label, "unit": unit,
            "reduced_by": "peak" if peak else "mean",
            "range": span, "values": values,
        })
        print(f"  {cid:<14} {len(raw):>6} points at {hop_of(blob, filename)} s -> {len(values)} at {hop_out} s")
    return curves, skipped


def build_strips(analysis: Path) -> int:
    from PIL import Image

    written = 0
    for source, target in STRIPS:
        path = analysis / source
        if not path.exists():
            print(f"  {source} is missing, {target} left alone")
            continue
        image = Image.open(path).convert("RGB")
        image = image.resize((STRIP_WIDTH, STRIP_HEIGHT), Image.LANCZOS)
        out = IMAGES / target
        image.save(out, "WEBP", quality=82, method=6)
        print(f"  {source:<18} {Image.open(path).size} -> {target} {image.size}, {out.stat().st_size:,} bytes")
        written += 1
    return written


def report(page: dict) -> None:
    """Print what the curves say per part and per kind of sound.

    The page's prose makes claims about these curves, and a claim about a number
    belongs to a script that can be run again rather than to a sentence someone
    typed once.
    """
    hop = page.get("curve_hop_s", 10.0)
    curves = {c["id"]: c["values"] for c in page.get("curves", [])}
    if not curves:
        print("no curves in the page file yet")
        return

    def mean_over(cid: str, spans) -> float | None:
        values = []
        for start, end in spans:
            lo, hi = int(start // hop), int(end // hop) + 1
            values += [v for v in curves.get(cid, [])[lo:hi] if v is not None]
        return sum(values) / len(values) if values else None

    kinds: dict[str, list] = {}
    for seg in page.get("segments", []):
        kinds.setdefault(seg["kind"], []).append((seg["start"], seg["end"]))
    print("by kind of sound:")
    for cid in ("flatness", "zcr", "centroid_hz"):
        row = "  ".join(f"{k} {mean_over(cid, spans):.4g}" for k, spans in sorted(kinds.items()) if mean_over(cid, spans) is not None)
        print(f"  {cid:<12} {row}")

    print("\nby part:")
    for part in page.get("parts", []):
        span = [(part["start"], part["end"])]
        bits = []
        for cid in ("qom", "saturation", "brightness"):
            value = mean_over(cid, span)
            if value is not None:
                bits.append(f"{cid} {value:.3f}")
        print(f"  {part['title'][:46]:<48} " + "  ".join(bits))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--analysis", type=Path, default=ANALYSIS)
    ap.add_argument("--hop", type=float, default=10.0, help="seconds per point on the page")
    ap.add_argument("--curves-only", action="store_true")
    ap.add_argument("--strips-only", action="store_true")
    ap.add_argument("--report", action="store_true", help="print what the curves say, and change nothing")
    args = ap.parse_args()

    if not args.analysis.exists():
        print(f"no analysis folder at {args.analysis}", file=sys.stderr)
        return 1

    page = json.loads(DATA.read_text())

    if args.report:
        report(page)
        return 0

    if not args.strips_only:
        print("curves:")
        curves, skipped = build_curves(args.analysis, args.hop)
        page["curves"] = curves
        page["curve_hop_s"] = args.hop
        page.pop("curves_not_plotted", None)
        page.pop("curves_not_plotted_why", None)
        if skipped:
            page["curves_empty"] = {
                "labels": [s["label"] for s in skipped],
                "why": FLAT_NOTE,
            }
        else:
            page.pop("curves_empty", None)

    if not args.curves_only:
        print("strips:")
        build_strips(args.analysis)
        page["picture_height"] = STRIP_HEIGHT

    DATA.write_text(json.dumps(page, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"\n{DATA.relative_to(SITE_ROOT.parent)}: {DATA.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
