#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_cmd(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "Unknown error"
        raise RuntimeError(f"Command failed ({' '.join(command)}): {message}")
    return result.stdout.strip()


def count_files(path: Path, suffix: str) -> int:
    return len([p for p in path.glob(f"*{suffix}") if p.is_file()])


def verify_split_pairs(images_dir: Path, split_dir: Path) -> tuple[int, int]:
    sources = sorted([p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() == ".png"])
    missing = 0
    for src in sources:
        a = split_dir / f"{src.stem}A.PNG"
        b = split_dir / f"{src.stem}B.PNG"
        if not a.exists():
            missing += 1
        if not b.exists():
            missing += 1
    return len(sources), missing


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Capture EPUB pages from Books and split images into A/B halves."
    )
    parser.add_argument("--epub", required=True, help="Path to EPUB file")
    parser.add_argument("--images-dir", required=True, help="Output directory for captured PNG files")
    parser.add_argument("--split-dir", required=True, help="Output directory for split PNG files")

    parser.add_argument("--capture-only", action="store_true", help="Run capture stage only")
    parser.add_argument("--split-only", action="store_true", help="Run split stage only")

    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--max-pages", type=int, default=5000)
    parser.add_argument("--duplicate-stop-threshold", type=int, default=2)

    parser.add_argument("--luma-threshold", type=int, default=40)
    parser.add_argument("--min-non-black-ratio", type=float, default=0.10)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--overwrite-split", action="store_true")
    parser.add_argument("--recursive", action="store_true")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.capture_only and args.split_only:
        raise SystemExit("Cannot combine --capture-only and --split-only")

    epub_path = Path(args.epub).expanduser()
    images_dir = Path(args.images_dir).expanduser()
    split_dir = Path(args.split_dir).expanduser()
    script_dir = Path(__file__).resolve().parent

    if not epub_path.exists() and not args.split_only:
        raise SystemExit(f"EPUB not found: {epub_path}")

    images_dir.mkdir(parents=True, exist_ok=True)
    split_dir.mkdir(parents=True, exist_ok=True)

    if not args.split_only:
        capture_script = script_dir / "capture_books_png.scpt"
        capture_cmd = [
            "osascript",
            str(capture_script),
            str(epub_path),
            str(images_dir),
            str(args.start_index),
            str(args.max_pages),
            str(args.duplicate_stop_threshold),
        ]
        print("Running capture stage...")
        capture_output = run_cmd(capture_cmd)
        if capture_output:
            print(capture_output)

    if not args.capture_only:
        split_script = script_dir / "split_trimmed_images.py"
        split_cmd = [
            sys.executable,
            str(split_script),
            "--src",
            str(images_dir),
            "--out",
            str(split_dir),
            "--luma-threshold",
            str(args.luma_threshold),
            "--min-non-black-ratio",
            str(args.min_non_black_ratio),
            "--workers",
            str(args.workers),
        ]
        if args.overwrite_split:
            split_cmd.append("--overwrite")
        if args.recursive:
            split_cmd.append("--recursive")

        print("Running split stage...")
        split_output = run_cmd(split_cmd)
        if split_output:
            print(split_output)

        source_count, missing = verify_split_pairs(images_dir, split_dir)
        split_count = count_files(split_dir, ".PNG")
        expected = source_count * 2

        print(f"Source screenshots: {source_count}")
        print(f"Split images: {split_count}")
        print(f"Expected split images: {expected}")
        print(f"Missing split pair files: {missing}")

        if missing > 0 or split_count < expected:
            raise SystemExit("Verification failed: split outputs are incomplete")


if __name__ == "__main__":
    main()
