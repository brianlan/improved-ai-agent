#!/usr/bin/env python3
"""
Merge individual OCR markdown pages into one combined document.

Usage:
    python3 merge_markdown.py <input_dir> <output_file> [--start <start_page>] [--end <end_page>]

Example:
    python3 merge_markdown.py /home/node/.openclaw/workspace/ocr_results_vlm merged.md
    python3 merge_markdown.py /home/node/.openclaw/workspace/ocr_results_vlm merged.md --start 15 --end 21
"""

import sys
import os
import re
from pathlib import Path
from typing import Optional


def natural_sort_key(s: str) -> list:
    """Sort strings with numbers naturally (e.g., page_2, page_10 instead of page_10, page_2)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r'(\d+)', s)]


def merge_markdown_pages(input_dir: str, output_file: str, start_page: Optional[int] = None, end_page: Optional[int] = None) -> None:
    """
    Merge individual markdown pages into one document.
    
    Args:
        input_dir: Directory containing page_XXX.md files
        output_file: Path to output merged markdown file
        start_page: Optional start page number
        end_page: Optional end page number
    """
    input_dir = Path(input_dir)
    
    # Find all page_XXX.md files
    page_files = sorted(
        [f for f in input_dir.glob("page_*.md")],
        key=lambda f: natural_sort_key(f.name)
    )
    
    if not page_files:
        print(f"Error: No page_*.md files found in {input_dir}")
        sys.exit(1)
    
    # Filter by page range if specified
    if start_page is not None or end_page is not None:
        filtered_files = []
        for f in page_files:
            # Extract page number from filename like "page_015.md"
            match = re.search(r'page_(\d+)', f.name)
            if match:
                page_num = int(match.group(1))
                if (start_page is None or page_num >= start_page) and \
                   (end_page is None or page_num <= end_page):
                    filtered_files.append(f)
        page_files = filtered_files
    
    print(f"Found {len(page_files)} pages to merge")
    
    # Merge all pages
    merged_content = []
    
    for i, page_file in enumerate(page_files):
        print(f"  Merging {page_file.name} ({i+1}/{len(page_files)})")
        
        with open(page_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add page separator if not first page
        if i > 0:
            merged_content.append("")
            merged_content.append("")
        
        merged_content.append(content)
    
    # Write merged file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(merged_content))
    
    print(f"\nMerged {len(page_files)} pages -> {output_file}")
    print(f"Total size: {output_path.stat().st_size:,} bytes")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Merge OCR markdown pages into one document")
    parser.add_argument("input_dir", help="Directory containing page_XXX.md files")
    parser.add_argument("output_file", help="Path to output merged markdown file")
    parser.add_argument("--start", type=int, help="Start page number (inclusive)")
    parser.add_argument("--end", type=int, help="End page number (inclusive)")
    
    args = parser.parse_args()
    
    merge_markdown_pages(args.input_dir, args.output_file, args.start, args.end)
