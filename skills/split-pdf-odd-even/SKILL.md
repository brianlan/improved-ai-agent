---
name: split-pdf-odd-even
description: Trim a raw PDF to an optional 1-based page range, then split the selected pages into two sibling PDFs containing odd and even pages. Use when the user provides a PDF path, with or without a page range, and wants outputs saved next to the input file with `_odd` and `_even` suffixes, such as splitting scanned book pages, duplex scans, or page-range excerpts. If no page range is provided, preserve all pages before splitting.
---

# Split PDF Odd/Even

Use the bundled script for deterministic PDF page extraction and splitting.

## Workflow

1. Confirm the input PDF path if it is missing. Treat the page range as optional; omit it to split the full PDF.
2. Run one of:

```bash
python3 ./skills/split-pdf-odd-even/scripts/trim_split_odd_even.py "/path/to/input.pdf"
python3 ./skills/split-pdf-odd-even/scripts/trim_split_odd_even.py "/path/to/input.pdf" "START-END"
```

3. Report the generated files:
   - `/path/to/input_odd.pdf`
   - `/path/to/input_even.pdf`

The script saves outputs in the same directory as the input PDF and refuses to overwrite existing files unless `--overwrite` is passed. It automatically prefers the Python `pypdf` package for speed and falls back to Poppler tools when `pypdf` is unavailable.

## Page range syntax

Use 1-based inclusive ranges when a range is provided. If omitted, the script uses all pages:

- omitted page range: pages 1 through the final page
- `1-20` or `1:20`: pages 1 through 20
- `5-`: page 5 through the final page
- `-10`: pages 1 through 10
- `7`: page 7 only

By default, odd/even means odd/even positions within the trimmed range. For example, range `10-15` maps source pages `10,12,14` to `_odd.pdf` because they are positions 1, 3, 5 after trimming. If the user explicitly asks for original PDF page-number parity, add `--parity-basis source`.

## Requirements

Prefer running with Python package `pypdf` installed because it is faster for large PDFs. If `pypdf` is unavailable, the script falls back to Poppler command-line tools on PATH: `pdfinfo`, `pdfseparate`, and `pdfunite`.

If neither backend is available, create an isolated temporary virtual environment, install `pypdf` there, and run the script with that interpreter. Do not install packages globally without user approval.
