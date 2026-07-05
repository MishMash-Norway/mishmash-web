#!/usr/bin/env python3
"""Generate the daily variation of the MishMash bubble artwork.

Draws the canonical two-circle mark with subtle, deterministic variations
seeded by the date and the day's site activity: geometry and hue drift
within tight bounds, and one small satellite bubble per upcoming event.
Same date + same data = same artwork, so the nightly commit is stable.

Transparency: the SVG carries a <desc> stating that it is generated and
from what, and it is shown on the AI colophon page with a caption.

Usage: generate_daily_bubbles.py [--date YYYY-MM-DD] [--out PATH]
"""

import argparse
import colorsys
import hashlib
import math
import random
import re
from datetime import date, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RESULTS_FILE = ROOT / "site" / "_data" / "mishmash_results.yml"
EVENTS_DIR = ROOT / "site" / "_events"
DEFAULT_OUT = ROOT / "site" / "assets" / "images" / "bubbles" / "daily" / "mishmash_bubbles_daily.svg"

PURPLE = "#A7A1F4"
GREEN = "#C1F7AE"
DARK = "#363644"
UPCOMING_WINDOW_DAYS = 90
MAX_SATELLITES = 12


def shift_hue(hex_color, degrees):
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb((h + degrees / 360) % 1, l, s)
    return "#{:02X}{:02X}{:02X}".format(round(r * 255), round(g * 255), round(b * 255))


def count_upcoming_events(today):
    horizon = today + timedelta(days=UPCOMING_WINDOW_DAYS)
    n = 0
    for f in EVENTS_DIR.glob("*.md"):
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})-", f.name)
        if not m:
            continue
        d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if today <= d <= horizon:
            n += 1
    return n


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", help="Seed date (YYYY-MM-DD, default today UTC)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    today = date.fromisoformat(args.date) if args.date else date.today()
    results = yaml.safe_load(RESULTS_FILE.open())["results"]
    n_results = len(results)
    n_upcoming = count_upcoming_events(today)

    seed = hashlib.sha256(f"{today}:{n_results}:{n_upcoming}".encode()).hexdigest()
    rng = random.Random(seed)

    # Geometry: the canonical mark, gently perturbed.
    lx = 150 + rng.uniform(-10, 10)
    ly = 160 + rng.uniform(-8, 8)
    rx = 270 + rng.uniform(-10, 10)
    ry = 160 + rng.uniform(-8, 8)
    lr = 110 * rng.uniform(0.94, 1.05)
    rr = 110 * rng.uniform(0.94, 1.05)

    # Hue: the pair drifts together so it stays harmonious.
    drift = rng.uniform(-14, 14)
    purple = shift_hue(PURPLE, drift)
    green = shift_hue(GREEN, drift)
    dark = shift_hue(DARK, drift / 2)

    # One satellite per upcoming event, kept clear of the text areas.
    satellites = []
    n_sats = min(n_upcoming, MAX_SATELLITES)
    for i in range(n_sats):
        # Angle bands that avoid the Science (top) and Art (bottom) labels.
        band = rng.choice([(-65, 65), (115, 245)])
        angle = rng.uniform(*band)
        a = math.radians(angle)
        cx = 210 + math.cos(a) * rng.uniform(165, 195)
        cy = 160 + math.sin(a) * rng.uniform(115, 140)
        r = rng.uniform(4, 11)
        cx = min(max(cx, r + 2), 420 - r - 2)
        cy = min(max(cy, max(60, r + 2)), 260)
        fill = purple if rng.random() < 0.5 else green
        satellites.append(
            f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" '
            f'fill="{fill}" fill-opacity="0.55" stroke="#777" stroke-width="0.5"/>'
        )

    sat_block = "\n".join(satellites)
    base_attrs = 'text-anchor="middle" font-family="Helvetica, Arial, sans-serif"'
    label_attrs = f'{base_attrs} font-size="20" fill="#333"'
    small_attrs = f'{base_attrs} font-size="18" fill="#333"'
    svg = f"""<svg width="420" height="320" viewBox="0 0 420 320" xmlns="http://www.w3.org/2000/svg">
  <title>MishMash bubbles, {today} edition</title>
  <desc>Generated automatically on {today} from site activity: {n_results} research results registered and {n_upcoming} events in the next {UPCOMING_WINDOW_DAYS} days (one small bubble each). See mishmash.no/about/ai-colophon/ for how this site uses generative tools.</desc>

{sat_block}

  <!-- Left circle: Humans -->
  <circle cx="{lx:.1f}" cy="{ly:.1f}" r="{lr:.1f}" fill="{purple}" stroke="#777" stroke-width="1"/>
  <!-- Right circle: Machines -->
  <circle cx="{rx:.1f}" cy="{ry:.1f}" r="{rr:.1f}" fill="{green}" stroke="#777" stroke-width="1"/>
  <!-- Overlap -->
  <defs>
    <clipPath id="clip-left" clipPathUnits="userSpaceOnUse">
      <circle cx="{lx:.1f}" cy="{ly:.1f}" r="{lr:.1f}"/>
    </clipPath>
  </defs>
  <circle cx="{rx:.1f}" cy="{ry:.1f}" r="{rr:.1f}" fill="{dark}" clip-path="url(#clip-left)"/>

  <text x="210" y="35" {label_attrs}>Science</text>
  <text x="210" y="305" {label_attrs}>Art</text>
  <text x="{(lx - lr * 0.35):.0f}" y="{(ly + 7):.0f}" {small_attrs}>Humans</text>
  <text x="{(rx + rr * 0.35):.0f}" y="{(ry + 7):.0f}" {small_attrs}>Machines</text>
  <text x="{(lx + (rx - lx) / 2):.0f}" y="{((ly + ry) / 2 + 7):.0f}" {base_attrs} font-size="18" fill="#fff">MishMash</text>
</svg>
"""

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(svg)
    try:
        shown = args.out.relative_to(ROOT)
    except ValueError:
        shown = args.out
    print(f"Wrote {shown} "
          f"(date={today}, results={n_results}, upcoming events={n_upcoming}, satellites={n_sats})")


if __name__ == "__main__":
    main()
