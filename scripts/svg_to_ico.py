#!/usr/bin/env python3
"""Convert an SVG to a multi-size ICO using Inkscape + Pillow.

Usage: python3 scripts/svg_to_ico.py <source.svg> <output.ico>
"""
import os
import sys
import subprocess
from PIL import Image

SIZES = [16, 32, 48, 64, 128, 256]

def render_png(svg_path, size, out_png):
    # Use inkscape to render PNG at specified width (maintain aspect)
    cmd = [
        'inkscape', svg_path,
        '--export-type=png',
        f'--export-filename={out_png}',
        f'-w', str(size)
    ]
    subprocess.check_call(cmd)

def make_ico(svg_path, ico_path):
    base = os.path.splitext(os.path.basename(ico_path))[0]
    tmp_dir = os.path.join('/tmp', f'svg2ico_{base}')
    os.makedirs(tmp_dir, exist_ok=True)
    png_files = []
    try:
        for s in SIZES:
            out_png = os.path.join(tmp_dir, f'{s}.png')
            render_png(svg_path, s, out_png)
            png_files.append(out_png)

        # Open images and save as ICO
        imgs = [Image.open(p).convert('RGBA') for p in png_files]
        # Pillow requires largest first
        imgs_sorted = sorted(imgs, key=lambda im: im.width, reverse=True)
        imgs_sorted[0].save(ico_path, format='ICO', sizes=[(i.width, i.height) for i in imgs_sorted])
        print('Created', ico_path)
    finally:
        for p in png_files:
            try:
                os.remove(p)
            except Exception:
                pass
        try:
            os.rmdir(tmp_dir)
        except Exception:
            pass

def main():
    if len(sys.argv) != 3:
        print('Usage: svg_to_ico.py <source.svg> <output.ico>')
        sys.exit(1)
    svg = sys.argv[1]
    ico = sys.argv[2]
    make_ico(svg, ico)

if __name__ == '__main__':
    main()
