---
name: video-frame-extractor
description: "Extract JPG frames from every video in a directory at fixed time intervals using ffmpeg, with first and last frame always included and per-video output subfolders. Use when asked to convert many videos into image datasets, run extraction in parallel, and perform random quality checks on sampled output images. Inputs: directory path and optional time interval (default 30 seconds)."
---

# Video Frame Extractor

Run this skill to convert videos into JPG frames for downstream inspection or dataset preparation.

## Inputs

- `input_dir`: Directory containing videos to process.
- `time_interval`: Seconds between frame timestamps. Default: `30`.

## Behavior

1. Discover video files in `input_dir` (optionally recursive).
2. For each video, create output folder `<video_parent>/<video_filestem>/`.
3. Extract frames as JPG at timestamps `0, interval, 2*interval, ...`.
4. Always include first frame and last frame.
5. Keep original video resolution (no scaling filter).
6. Process multiple videos in parallel with configurable workers.
7. Randomly sample output directories/images and validate sample images with `ffprobe`.

## Commands

Basic run:

```bash
python3 scripts/extract_video_frames.py /path/to/videos
```

Custom interval and workers:

```bash
python3 scripts/extract_video_frames.py /path/to/videos --time-interval 15 --workers 8
```

Recursive search + deterministic QA sampling:

```bash
python3 scripts/extract_video_frames.py /path/to/videos --recursive --sample-dirs 5 --sample-images 4 --seed 123
```

## Rehearsal Command

Use the user-provided rehearsal input:

```bash
python3 scripts/extract_video_frames.py /ssd5/downloaded-video-playlist/mibao/downloads --time-interval 30 --recursive
```

## Script Reference

- `scripts/extract_video_frames.py`
  - Requires `ffmpeg` and `ffprobe` in `PATH`
  - Supported video extensions: `.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.flv`, `.m4v`, `.mpg`, `.mpeg`, `.ts`
  - Exit code `0` when all processed videos succeed
  - Exit code `1` when one or more videos have extraction issues
  - Exit code `2` for invalid inputs or missing binaries

## Notes

- The script writes JPG files directly under each per-video folder.
- Filename pattern encodes frame order and timestamp.
- Random QA sampling validates JPEG codec and dimensions on sampled files.
