#!/usr/bin/env python3

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, cast

from PIL import Image


DEFAULT_LUMA_THRESHOLD = 40
DEFAULT_MIN_NON_BLACK_RATIO = 0.10


@dataclass
class JobConfig:
    out_dir: Path
    luma_threshold: int
    min_non_black_ratio: float
    output_format: str
    compress_level: int
    overwrite: bool
    workers: int


@dataclass
class ProcessResult:
    stem: str
    original_size: tuple[int, int]
    trimmed_size: tuple[int, int]
    left: int
    right: int
    skipped: bool


def parse_suffixes(raw: str) -> set[str]:
    values = {s.strip().lower() for s in raw.split(",") if s.strip()}
    if not values:
        raise ValueError("At least one suffix is required.")
    normalized = set()
    for value in values:
        normalized.add(value if value.startswith(".") else f".{value}")
    return normalized


def iter_source_files(src_dir: Path, recursive: bool, suffixes: set[str]) -> list[Path]:
    walker: Iterable[Path]
    walker = src_dir.rglob("*") if recursive else src_dir.glob("*")
    files = [p for p in walker if p.is_file() and p.suffix.lower() in suffixes]
    return sorted(files)


def column_non_black_ratio(img: Image.Image, x: int, luma_threshold: int) -> float:
    _, h = img.size
    non_black = 0
    for y in range(h):
        r, g, b = cast(tuple[int, int, int], img.getpixel((x, y)))
        luma = (299 * r + 587 * g + 114 * b) / 1000
        if luma > luma_threshold:
            non_black += 1
    return non_black / h


def detect_side_bounds(img: Image.Image, luma_threshold: int, min_non_black_ratio: float) -> tuple[int, int]:
    w, _ = img.size
    ratios = [column_non_black_ratio(img, x, luma_threshold) for x in range(w)]

    left = next((i for i, v in enumerate(ratios) if v >= min_non_black_ratio), 0)
    right = w - 1 - next((i for i, v in enumerate(reversed(ratios)) if v >= min_non_black_ratio), 0)

    if right <= left:
        return 0, w - 1
    return left, right


def process_image(src: Path, cfg: JobConfig) -> ProcessResult:
    out_a = cfg.out_dir / f"{src.stem}A.png"
    out_b = cfg.out_dir / f"{src.stem}B.png"
    if not cfg.overwrite and out_a.exists() and out_b.exists():
        with Image.open(src) as source_img:
            return ProcessResult(
                stem=src.stem,
                original_size=source_img.size,
                trimmed_size=source_img.size,
                left=0,
                right=source_img.size[0] - 1,
                skipped=True,
            )

    with Image.open(src) as opened:
        img = opened.convert("RGB")

    w, h = img.size
    left, right = detect_side_bounds(img, cfg.luma_threshold, cfg.min_non_black_ratio)
    trimmed = img.crop((left, 0, right + 1, h))

    tw, th = trimmed.size
    mid = tw // 2
    part_a = trimmed.crop((0, 0, mid, th))
    part_b = trimmed.crop((mid, 0, tw, th))

    part_a.save(out_a, format=cfg.output_format, compress_level=cfg.compress_level)
    part_b.save(out_b, format=cfg.output_format, compress_level=cfg.compress_level)

    return ProcessResult(
        stem=src.stem,
        original_size=(w, h),
        trimmed_size=(tw, th),
        left=left,
        right=right,
        skipped=False,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Trim black side regions and split each image into A/B halves."
    )
    parser.add_argument("--src", required=True, help="Source image directory")
    parser.add_argument("--out", required=True, help="Output directory for split images")
    parser.add_argument(
        "--suffixes",
        default=".png,.jpg,.jpeg,.tif,.tiff,.webp",
        help="Comma-separated source suffixes",
    )
    parser.add_argument("--recursive", action="store_true", help="Scan source directory recursively")
    parser.add_argument(
        "--luma-threshold",
        type=int,
        default=DEFAULT_LUMA_THRESHOLD,
        help="Pixel luminance threshold for black detection",
    )
    parser.add_argument(
        "--min-non-black-ratio",
        type=float,
        default=DEFAULT_MIN_NON_BLACK_RATIO,
        help="Minimum non-black pixel ratio for a column to be considered content",
    )
    parser.add_argument(
        "--output-format",
        choices=["png"],
        default="png",
        help="Output image format",
    )
    parser.add_argument(
        "--compress-level",
        type=int,
        default=0,
        help="PNG compression level (0-9)",
    )
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files")
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Parallel worker threads for processing",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    src_dir = Path(args.src).expanduser()
    out_dir = Path(args.out).expanduser()

    if not src_dir.exists() or not src_dir.is_dir():
        raise SystemExit(f"Source directory not found: {src_dir}")
    if args.compress_level < 0 or args.compress_level > 9:
        raise SystemExit("--compress-level must be between 0 and 9")
    if args.workers < 1:
        raise SystemExit("--workers must be >= 1")
    if args.min_non_black_ratio <= 0 or args.min_non_black_ratio > 1:
        raise SystemExit("--min-non-black-ratio must be in (0, 1]")

    suffixes = parse_suffixes(args.suffixes)
    files = iter_source_files(src_dir, args.recursive, suffixes)

    if not files:
        print("No matching image files found.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    cfg = JobConfig(
        out_dir=out_dir,
        luma_threshold=args.luma_threshold,
        min_non_black_ratio=args.min_non_black_ratio,
        output_format=args.output_format,
        compress_level=args.compress_level,
        overwrite=args.overwrite,
        workers=args.workers,
    )

    if cfg.workers == 1:
        results = [process_image(path, cfg) for path in files]
    else:
        with ThreadPoolExecutor(max_workers=cfg.workers) as pool:
            results = list(pool.map(lambda p: process_image(p, cfg), files))

    processed = sum(1 for r in results if not r.skipped)
    skipped = sum(1 for r in results if r.skipped)
    widths = [r.trimmed_size[0] for r in results]

    print(f"Found: {len(files)}")
    print(f"Processed: {processed}")
    print(f"Skipped: {skipped}")
    print(f"Outputs expected: {processed * 2}")
    print(f"Trimmed width min/max: {min(widths)}/{max(widths)}")


if __name__ == "__main__":
    main()
