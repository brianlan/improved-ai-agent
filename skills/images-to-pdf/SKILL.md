---
name: images-to-pdf
description: Convert a directory of images to a PDF file with A4 pages. Use when user provides an input directory containing images and wants them converted to a single PDF file. Supports PNG, JPG, JPEG, GIF, BMP, TIFF, and WebP formats. Images are scaled to fill entire pages without borders or margins, sorted by filename to preserve order.
---

# Images To PDF

## Quick Start

Run the conversion script with input directory and output PDF path:

```bash
python3 /Users/rlan/.claude/skills/images-to-pdf/scripts/convert_images_to_pdf.py <input_dir> <output_pdf> [--paper-size A4|Letter]
```

## Parameters

- `input_dir`: Directory containing images to convert
- `output_pdf`: Path where the PDF will be saved
- `--paper-size`: Optional. Paper size - A4 (default) or Letter

## Usage Examples

**Basic usage:**
```
input: /path/to/images
output: /path/to/book.pdf
→ python3 /Users/rlan/.claude/skills/images-to-pdf/scripts/convert_images_to_pdf.py /path/to/images /path/to/book.pdf
```

**With Letter paper size:**
```
→ python3 /Users/rlan/.claude/skills/images-to-pdf/scripts/convert_images_to_pdf.py /path/to/images /path/to/book.pdf --paper-size Letter
```

## Features

- Images sorted by filename to preserve order
- Scaled to fill A4 pages completely (no borders, no margins)
- Supports PNG, JPG, JPEG, GIF, BMP, TIFF, WebP
- Creates output directory if it doesn't exist
