#!/usr/bin/env python3
"""Extract JPG frames from videos at a fixed time interval.

Features:
- Input: directory path containing video files
- Output: one subfolder per video using the video stem
- Extraction interval defaults to 30 seconds
- First frame and last frame are always included
- Multi-video parallel processing
- Post-run random sampling + validation of generated JPGs
"""

from __future__ import annotations

import argparse
import concurrent.futures
import math
import os
import random
import shutil
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import cast


VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".webm",
    ".flv",
    ".m4v",
    ".mpg",
    ".mpeg",
    ".ts",
}


@dataclass
class VideoResult:
    video_path: Path
    output_dir: Path
    requested_frames: int
    written_frames: int
    errors: list[str]


def run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def require_binary(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required binary not found in PATH: {name}")


def probe_duration_seconds(video_path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    result = run_command(command)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffprobe failed while probing duration")
    value = result.stdout.strip()
    try:
        duration = float(value)
    except ValueError as exc:
        raise RuntimeError(f"Unexpected ffprobe duration output: {value}") from exc
    if not math.isfinite(duration) or duration < 0:
        raise RuntimeError(f"Invalid duration detected: {duration}")
    return duration


def build_timestamps(duration_seconds: float, interval_seconds: float) -> list[float]:
    if interval_seconds <= 0:
        raise ValueError("time_interval must be greater than 0")

    if duration_seconds <= 0:
        return [0.0]

    timestamps = {0.0}
    cursor = interval_seconds
    while cursor < duration_seconds:
        timestamps.add(cursor)
        cursor += interval_seconds

    return sorted(timestamps)


def output_frame_name(index: int, timestamp: float) -> str:
    ts = f"{timestamp:.3f}".replace(".", "p")
    return f"frame_{index:06d}_t{ts}.jpg"


def extract_one_frame(video_path: Path, timestamp: float, output_path: Path) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-ss",
        f"{timestamp:.3f}",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(output_path),
    ]
    result = run_command(command)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg frame extraction failed")


def extract_last_frame(video_path: Path, output_path: Path) -> None:
    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-sseof",
        "-3",
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        "-update",
        "1",
        str(output_path),
    ]
    result = run_command(command)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "ffmpeg last-frame extraction failed")


def discover_videos(input_dir: Path, recursive: bool) -> list[Path]:
    iterator: Iterable[Path] = input_dir.rglob("*") if recursive else input_dir.glob("*")
    videos = [p for p in iterator if p.is_file() and p.suffix.lower() in VIDEO_EXTENSIONS]
    return sorted(videos)


def convert_video(
    video_path: Path, interval_seconds: float, output_root: Path | None
) -> VideoResult:
    output_dir = (
        (output_root / video_path.stem)
        if output_root is not None
        else (video_path.parent / video_path.stem)
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    written = 0

    try:
        duration = probe_duration_seconds(video_path)
        timestamps = build_timestamps(duration, interval_seconds)
    except Exception as exc:  # noqa: BLE001
        return VideoResult(video_path, output_dir, 0, 0, [str(exc)])

    for index, timestamp in enumerate(timestamps, start=1):
        frame_path = output_dir / output_frame_name(index, timestamp)
        try:
            extract_one_frame(video_path, timestamp, frame_path)
            if frame_path.exists() and frame_path.stat().st_size > 0:
                written += 1
            else:
                errors.append(f"Empty frame output: {frame_path}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{frame_path.name}: {exc}")

    last_frame_path = output_dir / output_frame_name(len(timestamps) + 1, duration)
    try:
        extract_last_frame(video_path, last_frame_path)
        if last_frame_path.exists() and last_frame_path.stat().st_size > 0:
            written += 1
        else:
            errors.append(f"Empty frame output: {last_frame_path}")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{last_frame_path.name}: {exc}")

    return VideoResult(video_path, output_dir, len(timestamps) + 1, written, errors)


def validate_jpg(image_path: Path) -> tuple[bool, str]:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=codec_name,width,height",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(image_path),
    ]
    result = run_command(command)
    if result.returncode != 0:
        return False, result.stderr.strip() or "ffprobe failed on image"

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) < 3:
        return False, f"Unexpected ffprobe output: {lines}"

    codec = lines[0].lower()
    try:
        width = int(lines[1])
        height = int(lines[2])
    except ValueError:
        return False, f"Non-integer dimensions from ffprobe: {lines[1:3]}"

    if codec not in {"mjpeg", "jpeg"}:
        return False, f"Unexpected codec {codec}"
    if width <= 0 or height <= 0:
        return False, f"Invalid dimensions {width}x{height}"
    return True, f"{width}x{height}, codec={codec}"


def run_quality_sampling(
    results: list[VideoResult],
    sample_dirs: int,
    sample_images_per_dir: int,
    seed: int,
) -> tuple[int, int, list[str]]:
    rng = random.Random(seed)
    candidate_dirs = [
        res.output_dir for res in results if res.written_frames > 0 and res.output_dir.exists()
    ]
    if not candidate_dirs:
        return 0, 0, ["No converted directories available for sampling."]

    chosen_dirs = rng.sample(candidate_dirs, k=min(sample_dirs, len(candidate_dirs)))
    checked = 0
    passed = 0
    messages: list[str] = []

    for folder in chosen_dirs:
        images = sorted(folder.glob("*.jpg"))
        if not images:
            messages.append(f"[WARN] No JPG images found in sampled folder: {folder}")
            continue

        chosen_images = rng.sample(images, k=min(sample_images_per_dir, len(images)))
        for image_path in chosen_images:
            checked += 1
            ok, detail = validate_jpg(image_path)
            if ok:
                passed += 1
                messages.append(f"[OK] {image_path} -> {detail}")
            else:
                messages.append(f"[FAIL] {image_path} -> {detail}")

    return checked, passed, messages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract JPG frames from videos in a directory")
    _ = parser.add_argument("input_dir", type=Path, help="Directory containing video files")
    _ = parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional output root directory (default: each video's parent directory)",
    )
    _ = parser.add_argument(
        "--time-interval",
        type=float,
        default=30.0,
        help="Seconds between extracted frames (default: 30)",
    )
    _ = parser.add_argument(
        "--workers",
        type=int,
        default=max(1, (os.cpu_count() or 1)),
        help="Parallel workers for processing videos (default: CPU count)",
    )
    _ = parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search for videos recursively under input_dir",
    )
    _ = parser.add_argument(
        "--sample-dirs",
        type=int,
        default=3,
        help="Number of output directories to sample for QA (default: 3)",
    )
    _ = parser.add_argument(
        "--sample-images",
        type=int,
        default=3,
        help="Number of images per sampled directory for QA (default: 3)",
    )
    _ = parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic QA sampling (default: 42)",
    )
    _ = parser.add_argument(
        "--max-videos",
        type=int,
        default=0,
        help="Optional cap for number of videos to process (0 = no limit)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    input_dir_arg = cast(Path, args.input_dir)
    time_interval = cast(float, args.time_interval)
    workers = cast(int, args.workers)
    recursive = cast(bool, args.recursive)
    sample_dirs = cast(int, args.sample_dirs)
    sample_images = cast(int, args.sample_images)
    seed = cast(int, args.seed)
    max_videos = cast(int, args.max_videos)
    output_dir_arg = cast(Path | None, args.output_dir)

    try:
        require_binary("ffmpeg")
        require_binary("ffprobe")
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        return 2

    input_dir = input_dir_arg.expanduser().resolve()
    output_root = output_dir_arg.expanduser().resolve() if output_dir_arg is not None else None
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"[ERROR] input_dir is not a directory: {input_dir}")
        return 2

    if time_interval <= 0:
        print("[ERROR] --time-interval must be greater than 0")
        return 2
    if workers <= 0:
        print("[ERROR] --workers must be greater than 0")
        return 2

    videos = discover_videos(input_dir, recursive=recursive)
    if max_videos > 0:
        videos = videos[:max_videos]

    if not videos:
        print(f"[INFO] No supported videos found under {input_dir}")
        return 0

    if output_root is not None:
        output_root.mkdir(parents=True, exist_ok=True)

    output_label = str(output_root) if output_root is not None else "video parent dirs"
    print(
        f"[INFO] Found {len(videos)} video(s). Workers={workers}, interval={time_interval}s, output_root={output_label}"
    )

    results: list[VideoResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_map = {
            executor.submit(convert_video, video, time_interval, output_root): video
            for video in videos
        }
        for future in concurrent.futures.as_completed(future_map):
            video_path = future_map[future]
            try:
                result = future.result()
            except Exception as exc:  # noqa: BLE001
                print(f"[FAIL] {video_path}: {exc}")
                continue
            results.append(result)
            status = (
                "OK"
                if not result.errors and result.written_frames == result.requested_frames
                else "WARN"
            )
            print(
                f"[{status}] {result.video_path} -> {result.output_dir} ({result.written_frames}/{result.requested_frames} frames)"
            )
            for error in result.errors:
                print(f"  [ERR] {error}")

    total_requested = sum(res.requested_frames for res in results)
    total_written = sum(res.written_frames for res in results)
    failed_videos = [res for res in results if res.written_frames == 0 or res.errors]

    print("\n[SUMMARY]")
    print(f"- Videos processed: {len(results)}")
    print(f"- Frames requested: {total_requested}")
    print(f"- Frames written:   {total_written}")
    print(f"- Videos with issues: {len(failed_videos)}")

    checked, passed, qa_messages = run_quality_sampling(
        results=results,
        sample_dirs=sample_dirs,
        sample_images_per_dir=sample_images,
        seed=seed,
    )
    print("\n[QA SAMPLING]")
    print(f"- Images checked: {checked}")
    print(f"- Images passed:  {passed}")
    for message in qa_messages:
        print(message)

    return 1 if failed_videos else 0


if __name__ == "__main__":
    sys.exit(main())
