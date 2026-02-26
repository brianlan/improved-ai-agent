---
name: epub-to-markdown
description: Extract EPUB HTML files to a single concatenated markdown document. Use when working with extracted EPUB directories to convert HTML chapter files into a readable markdown format with proper formatting, reading order preservation, and clean text extraction.
---

# EPUB to Markdown

Extract EPUB HTML files to a single markdown document with proper formatting and reading order preservation.

## Quick Start

Run the extraction script on an EPUB extraction directory:

```bash
python3 scripts/extract_epub.py /path/to/epub_extracted -o output.md
```

## How It Works

1. **Parse OPF file**: Reads the EPUB package file to determine the correct reading order of HTML documents
2. **Extract text**: Converts HTML content to markdown format with proper handling of:
   - Headings (h1-h6)
   - Paragraphs and emphasis (bold, italic)
   - Lists (ordered and unordered)
   - Links
   - Blockquotes
   - Tables (basic conversion)
3. **Concatenate**: Joins all documents with separators in reading order
4. **Clean up**: Removes scripts, styles, and navigation elements

## Supported Input

The skill works with EPUB extraction directories that contain:
- An `.opf` package file (typically in `ops/`, `OEBPS/`, or root directory)
- HTML/XHTML chapter files
- Standard EPUB directory structure

## Usage

### Basic Extraction

```python
from scripts.extract_epub import extract_epub_to_markdown

extract_epub_to_markdown(
    epub_dir='/path/to/epub_extracted',
    output_file='book.md'
)
```

### Command Line

```bash
# Basic usage
python3 scripts/extract_epub.py /path/to/epub_extracted

# Custom output file
python3 scripts/extract_epub.py /path/to/epub_extracted -o my_book.md

# Include all files (including cover, copyright pages, etc.)
python3 scripts/extract_epub.py /path/to/epub_extracted --include-all
```

## Output Format

The generated markdown includes:
- Chapter headings preserved from HTML h1-h6 tags
- Paragraphs separated by blank lines
- Emphasis converted to markdown bold/italic syntax
- Lists converted to markdown list syntax
- Page markers removed for cleaner text
- File separators (---) between documents

## Scripts

- `scripts/extract_epub.py` - Main extraction script that handles OPF parsing and HTML-to-markdown conversion

## Limitations

- Complex HTML tables may not convert perfectly
- CSS-styled content relies on semantic HTML structure
- Some decorative elements may be included in output
