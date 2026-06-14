import argparse
import os

from PIL import Image

from repo_paths import SITE_ROOT

MAX_SIZE = 300


def process_portrait(img_path: str, out_path: str, max_size: int) -> None:
    with Image.open(img_path) as opened:
        img = opened.convert("RGB")
        size = min(img.size)

        left = (img.width - size) // 2
        top = (img.height - size) // 2
        img = img.crop((left, top, left + size, top + size))

        if size > max_size:
            img = img.resize((max_size, max_size), Image.Resampling.LANCZOS)

        img.save(out_path, "JPEG", quality=90)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resize portraits to a square max size in site/assets/images/portraits/.")
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

    portrait_folder = os.path.join(SITE_ROOT, "assets/images/portraits")
    os.makedirs(portrait_folder, exist_ok=True)

    filenames = sorted(
        name
        for name in os.listdir(portrait_folder)
        if name.lower().endswith((".png", ".jpg", ".jpeg"))
    )

    processed = 0
    skipped = 0
    failed = 0
    total = len(filenames)

    try:
        for index, filename in enumerate(filenames, start=1):
            img_path = os.path.join(portrait_folder, filename)
            out_path = os.path.join(portrait_folder, os.path.splitext(filename)[0] + ".jpg")

            if not args.force and os.path.exists(out_path) and out_path != img_path:
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
