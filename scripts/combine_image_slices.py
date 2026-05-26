#!/usr/bin/env python3
"""Combine one vertical slice from each of two images into a single image.

The output image is built as:
- left side: a slice from the left edge of the first image
- right side: a slice from the right edge of the second image
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def parse_fraction(value: str) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Expected a number, got: {value}") from exc

    if not 0 < number <= 1:
        raise argparse.ArgumentTypeError("Value must be in the range (0, 1].")
    return number


def resize_to_height(image: Image.Image, target_height: int) -> Image.Image:
    if image.height == target_height:
        return image

    new_width = max(1, round(image.width * (target_height / image.height)))
    return image.resize((new_width, target_height), Image.Resampling.LANCZOS)


def combine_slices(
    image1_path: Path,
    image2_path: Path,
    output_path: Path,
    left_ratio: float,
    right_ratio: float,
) -> None:
    with Image.open(image1_path) as first, Image.open(image2_path) as second:
        first = first.convert("RGBA")
        second = second.convert("RGBA")

        target_height = min(first.height, second.height)
        first = resize_to_height(first, target_height)
        second = resize_to_height(second, target_height)

        left_width = max(1, round(first.width * left_ratio))
        right_width = max(1, round(second.width * right_ratio))

        left_slice = first.crop((0, 0, left_width, target_height))
        right_slice = second.crop((second.width - right_width, 0, second.width, target_height))

        combined = Image.new("RGBA", (left_width + right_width, target_height))
        combined.paste(left_slice, (0, 0))
        combined.paste(right_slice, (left_width, 0))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix.lower() in {".jpg", ".jpeg"}:
            combined.convert("RGB").save(output_path)
        else:
            combined.save(output_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read two images and create a combined image with a left slice from the "
            "first image and a right slice from the second image."
        )
    )
    parser.add_argument("image1", type=Path, help="Path to the first input image (left slice source).")
    parser.add_argument("image2", type=Path, help="Path to the second input image (right slice source).")
    parser.add_argument("output", type=Path, help="Path to the output image.")
    parser.add_argument(
        "--left-ratio",
        type=parse_fraction,
        default=0.5,
        help="Fraction of the first image width to keep from the left side (default: 0.5).",
    )
    parser.add_argument(
        "--right-ratio",
        type=parse_fraction,
        default=0.5,
        help="Fraction of the second image width to keep from the right side (default: 0.5).",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    combine_slices(
        image1_path=args.image1,
        image2_path=args.image2,
        output_path=args.output,
        left_ratio=args.left_ratio,
        right_ratio=args.right_ratio,
    )

    print(f"Created combined image: {args.output}")


if __name__ == "__main__":
    main()
