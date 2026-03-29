#!/usr/bin/env python3
"""
Extract pages from a PDF as PNG images for OCR processing.

Usage:
    python3 extract_pages.py <pdf_path> <start_page> <end_page> <output_dir>

Example:
    python3 extract_pages.py book.pdf 1 10 /tmp/pages
"""

import sys
import os
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF not installed. Run: pip install pymupdf")
    sys.exit(1)


def extract_pages(pdf_path: str, start_page: int, end_page: int, output_dir: str) -> list[str]:
    """
    Extract pages from a PDF as PNG images.
    
    Args:
        pdf_path: Path to the PDF file
        start_page: Starting page number (1-indexed)
        end_page: Ending page number (1-indexed, inclusive)
        output_dir: Directory to save PNG files
        
    Returns:
        List of saved PNG file paths
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    
    if start_page < 1 or end_page > len(doc):
        print(f"Error: Page range {start_page}-{end_page} out of bounds (PDF has {len(doc)} pages)")
        doc.close()
        sys.exit(1)
    
    saved_files = []
    
    for page_num in range(start_page, end_page + 1):
        page = doc[page_num - 1]  # 0-indexed
        mat = fitz.Matrix(150/72, 150/72)  # 150 DPI
        pix = page.get_pixmap(matrix=mat)
        
        output_path = output_dir / f"page_{page_num:03d}.png"
        pix.save(str(output_path))
        saved_files.append(str(output_path))
        print(f"Extracted page {page_num}: {pix.width}x{pix.height}")
    
    doc.close()
    return saved_files


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    start_page = int(sys.argv[2])
    end_page = int(sys.argv[3])
    output_dir = sys.argv[4]
    
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)
    
    extract_pages(pdf_path, start_page, end_page, output_dir)
    print(f"\nExtracted {end_page - start_page + 1} pages to {output_dir}")
