#!/usr/bin/env python3
"""
Crop the martyr's face out of a finished memorial poster.

Why this exists: FaceFusion builds the source identity with get_average_face()
(face_swapper/core.py:757), which averages EVERY face it detects across the source
images. Handing it a full poster that contains a second photo - even a partial one
at the edge - silently blends two people into one identity. That is the same
"looks like a relative" failure we are trying to avoid, introduced before the
swapper even runs.

So: crop to exactly one face, once, and point the sweep at the crop.

Usage:
    python ff_prep_source.py                          # default box, writes Source_face.jpg
    python ff_prep_source.py --box 600,150,1060,800   # left,top,right,bottom
    python ff_prep_source.py --in Other.jpg --out Other_face.jpg --box ...
    python ff_prep_source.py --grid                   # overlay a coordinate grid to pick a box
"""

import argparse
import pathlib
import sys

from PIL import Image, ImageDraw

SWEEP = pathlib.Path(r"D:\01-AI\002-MertydomPosters\sweep")

# Tuned for this poster (1280x1280): the portrait's head with margin, stopping
# well short of the partial second photo at the right edge (~x 1150).
DEFAULT_BOX = (600, 150, 1060, 800)


def draw_grid(im, step=100):
    """Overlay labelled gridlines so you can read a crop box straight off the image."""
    g = im.copy().convert("RGB")
    d = ImageDraw.Draw(g)
    for x in range(0, g.width, step):
        d.line([(x, 0), (x, g.height)], fill=(255, 0, 0), width=1)
        d.text((x + 2, 2), str(x), fill=(255, 255, 0))
    for y in range(0, g.height, step):
        d.line([(0, y), (g.width, y)], fill=(255, 0, 0), width=1)
        d.text((2, y + 2), str(y), fill=(255, 255, 0))
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", default=str(SWEEP / "Source.jpg"))
    ap.add_argument("--out", dest="dst", default=str(SWEEP / "Source_face.jpg"))
    ap.add_argument("--box", default=",".join(map(str, DEFAULT_BOX)),
                    help="left,top,right,bottom")
    ap.add_argument("--grid", action="store_true",
                    help="write a grid overlay next to the source and exit")
    ap.add_argument("--quality", type=int, default=98)
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    if not src.exists():
        sys.exit(f"ERROR: {src} not found")

    im = Image.open(src)
    print(f"input : {src.name}  {im.width}x{im.height}")

    if args.grid:
        out = src.with_name(src.stem + "_grid.png")
        draw_grid(im).save(out)
        print(f"grid  : {out}   # read a box off this, then pass --box l,t,r,b")
        return

    box = tuple(int(v) for v in args.box.split(","))
    if len(box) != 4:
        sys.exit("ERROR: --box needs 4 values: left,top,right,bottom")
    l, t, r, b = box
    if not (0 <= l < r <= im.width and 0 <= t < b <= im.height):
        sys.exit(f"ERROR: box {box} outside image bounds {im.width}x{im.height}")

    crop = im.convert("RGB").crop(box)
    dst = pathlib.Path(args.dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    crop.save(dst, quality=args.quality, subsampling=0)
    print(f"output: {dst.name}  {crop.width}x{crop.height}  box={box}")
    print("\nCheck the crop contains exactly ONE face before sweeping.")


if __name__ == "__main__":
    main()
