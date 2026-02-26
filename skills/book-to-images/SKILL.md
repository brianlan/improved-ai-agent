---
name: book-to-images
description: Automate EPUB-to-image extraction on macOS Books, then trim side black bars and split each screenshot into A/B page images. Use when asked to open an EPUB in Books, capture all pages as lossless PNG files, and generate split page images for OCR, indexing, or dataset prep. Supports one-shot pipeline run, capture-only reruns, split-only reruns, and configurable split thresholds/workers.
---

# Book To Images

## Overview

Run this skill to convert a Books-readable EPUB into reusable page images in two stages: capture screenshots from Books, then trim side black UI bars and split each image at midpoint.

## Inputs

- `epub_path`: Absolute path to the EPUB file.
- `images_dir`: Output directory for screenshot PNGs.
- `split_dir`: Output directory for split PNGs (`NNNA.PNG`, `NNNB.PNG`).
- Optional tuning:
  - `--luma-threshold` (default `40`)
  - `--min-non-black-ratio` (default `0.10`)
  - `--workers` (default `1`)

## Workflow

1. Run capture script with `osascript` to create sequential PNG files (`001.png`, `002.png`, ...).
2. Run split script to trim side black regions and split each trimmed image into A/B halves.
3. Verify outputs (`N` source screenshots and `2N` split images, with paired `A/B` names).

## Commands

Full pipeline:

```bash
python3 scripts/book_to_images.py \
  --epub "/path/to/book.epub" \
  --images-dir "/path/to/images" \
  --split-dir "/path/to/split-images" \
  --overwrite-split \
  --workers 4
```

Capture only:

```bash
python3 scripts/book_to_images.py \
  --epub "/path/to/book.epub" \
  --images-dir "/path/to/images" \
  --split-dir "/path/to/split-images" \
  --capture-only
```

Split only (reuse existing screenshots):

```bash
python3 scripts/book_to_images.py \
  --epub "/path/to/book.epub" \
  --images-dir "/path/to/images" \
  --split-dir "/path/to/split-images" \
  --split-only \
  --overwrite-split \
  --workers 4
```

## Script Reference

- `scripts/book_to_images.py`
  - Orchestrates capture and split pipeline.
  - Performs output count checks.
- `scripts/capture_books_png.scpt`
  - AppleScript capture engine for Books.
  - Accepts args: `epubPath outputDir [startIndex maxPages duplicateStopThreshold minDelay pollInterval timeout minTotalWait stablePolls postChangeSettle]`.
- `scripts/split_trimmed_images.py`
  - Trims side black bars and splits each image into `A/B` outputs.
  - Supports recursive scan, suffix filters, thresholds, workers.

## Environment Requirements

- macOS with Books app.
- `python3` and Pillow (`PIL`).
- Accessibility + Screen Recording permissions for script host.
- Keep Books window visible and unobstructed while capturing.

## Notes

- Prefer `--split-only` for threshold tuning reruns.
- Use `--overwrite-split` when regenerating split outputs.
- If capture races page rendering, increase AppleScript timeout/stability args.
