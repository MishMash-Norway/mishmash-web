import argparse
import os

from PIL import Image, ImageDraw

MAX_SIZE = 300


def process_portrait(img_path: str, out_path: str, max_size: int) -> None:
    with Image.open(img_path) as opened:
        img = opened.convert("RGBA")
        size = min(img.size)

        # Center crop to square
        left = (img.width - size) // 2
        top = (img.height - size) // 2
        right = left + size
        bottom = top + size
        img = img.crop((left, top, right, bottom))

        # Resize if necessary
        if size > max_size:
            img = img.resize((max_size, max_size), Image.LANCZOS)
            size = max_size

        # Create circular alpha mask
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)

        result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        result.paste(img, (0, 0), mask)
        result.save(out_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create circular transparent portraits.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate portraits even when output files already exist.",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=MAX_SIZE,
        help=f"Maximum output width and height (default: {MAX_SIZE}).",
    )
    args = parser.parse_args()

    input_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../assets/images/portraits/square")
    )
    output_folder = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../assets/images/portraits/circle")
    )
    os.makedirs(output_folder, exist_ok=True)

    filenames = sorted(
        name
        for name in os.listdir(input_folder)
        if name.lower().endswith((".png", ".jpg", ".jpeg"))
    )

    processed = 0
    skipped = 0
    failed = 0
    total = len(filenames)

    try:
        for index, filename in enumerate(filenames, start=1):
            img_path = os.path.join(input_folder, filename)
            out_path = os.path.join(output_folder, os.path.splitext(filename)[0] + ".png")

            if not args.force and os.path.exists(out_path):
                skipped += 1
                print(f"[{index}/{total}] Skipped existing: {out_path}")
                continue

            try:
                process_portrait(img_path, out_path, args.max_size)
                processed += 1
                print(f"[{index}/{total}] Saved: {out_path}")
            except Exception as exc:
                failed += 1
                print(f"[{index}/{total}] Failed: {img_path} ({exc})")

    except KeyboardInterrupt:
        print("\nInterrupted by user. Partial output has been kept.")

    print(
        f"Done. processed={processed}, skipped={skipped}, failed={failed}, total={total}"
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())