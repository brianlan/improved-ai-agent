#!/usr/bin/env python3
"""Trim a PDF to a page range, then split selected pages into odd/even PDFs."""

from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def die(message: str, code: int = 1) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        die(f"Required tool not found: {name}. Install Poppler utilities (pdfinfo, pdfseparate, pdfunite).")
    return path


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        joined = " ".join(cmd)
        detail = (result.stderr or result.stdout).strip()
        die(f"Command failed: {joined}\n{detail}")
    return result


def page_count_with_pdfinfo(pdf_path: Path) -> int:
    result = run([require_tool("pdfinfo"), str(pdf_path)])
    match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    if not match:
        die(f"Could not determine page count for {pdf_path}")
    return int(match.group(1))


def parse_page_range(value: str | None, total_pages: int) -> tuple[int, int]:
    if value is None:
        return 1, total_pages

    text = value.strip()
    if not text:
        return 1, total_pages

    if re.fullmatch(r"\d+", text):
        start = end = int(text)
    else:
        match = re.fullmatch(r"(\d*)\s*[-:]\s*(\d*)", text)
        if not match:
            die("Page range must look like '1-10', '1:10', '5-', '-20', or '7'")
        start_text, end_text = match.groups()
        start = int(start_text) if start_text else 1
        end = int(end_text) if end_text else total_pages

    if start < 1 or end < 1:
        die("Page numbers are 1-based and must be positive")
    if start > end:
        die(f"Invalid page range: start page {start} is after end page {end}")
    if end > total_pages:
        die(f"Page range ends at {end}, but PDF has only {total_pages} pages")
    return start, end


def output_path(input_pdf: Path, suffix: str, overwrite: bool) -> Path:
    path = input_pdf.with_name(f"{input_pdf.stem}_{suffix}{input_pdf.suffix}")
    if path.exists() and not overwrite:
        die(f"Output already exists: {path}. Re-run with --overwrite to replace it.")
    return path


def validate_input(input_pdf: Path) -> None:
    if not input_pdf.exists():
        die(f"Input PDF does not exist: {input_pdf}")
    if not input_pdf.is_file():
        die(f"Input path is not a file: {input_pdf}")
    if input_pdf.suffix.lower() != ".pdf":
        die(f"Input file must be a PDF: {input_pdf}")


def pypdf_available() -> bool:
    return importlib.util.find_spec("pypdf") is not None


def split_with_pypdf(input_pdf: Path, page_range: str | None, parity_basis: str, overwrite: bool) -> tuple[Path | None, Path | None]:
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(input_pdf)
    total_pages = len(reader.pages)
    start, end = parse_page_range(page_range, total_pages)
    odd_output = output_path(input_pdf, "odd", overwrite)
    even_output = output_path(input_pdf, "even", overwrite)

    odd_writer = PdfWriter()
    even_writer = PdfWriter()
    for source_page in range(start, end + 1):
        parity_number = source_page if parity_basis == "source" else source_page - start + 1
        writer = odd_writer if parity_number % 2 == 1 else even_writer
        writer.add_page(reader.pages[source_page - 1])

    written: list[Path | None] = []
    for output, writer in ((odd_output, odd_writer), (even_output, even_writer)):
        if len(writer.pages) == 0:
            print(f"No pages for {output.name}; not creating an empty PDF.")
            written.append(None)
            continue
        if output.exists() and overwrite:
            output.unlink()
        with output.open("wb") as handle:
            writer.write(handle)
        print(f"Wrote {output} ({len(writer.pages)} pages)")
        written.append(output)

    return written[0], written[1]


def unite_or_report(pdfunite: str, pages: list[Path], output: Path, overwrite: bool) -> bool:
    if not pages:
        print(f"No pages for {output.name}; not creating an empty PDF.")
        return False
    if output.exists() and overwrite:
        output.unlink()
    run([pdfunite, *[str(page) for page in pages], str(output)])
    print(f"Wrote {output} ({len(pages)} pages)")
    return True


def split_with_poppler(input_pdf: Path, page_range: str | None, parity_basis: str, overwrite: bool) -> tuple[Path | None, Path | None]:
    pdfseparate = require_tool("pdfseparate")
    pdfunite = require_tool("pdfunite")

    total_pages = page_count_with_pdfinfo(input_pdf)
    start, end = parse_page_range(page_range, total_pages)
    odd_output = output_path(input_pdf, "odd", overwrite)
    even_output = output_path(input_pdf, "even", overwrite)

    with tempfile.TemporaryDirectory(prefix="trim_split_odd_even_") as tmp:
        tmpdir = Path(tmp)
        page_pattern = tmpdir / "page-%06d.pdf"
        run([pdfseparate, "-f", str(start), "-l", str(end), str(input_pdf), str(page_pattern)])

        odd_pages: list[Path] = []
        even_pages: list[Path] = []
        for source_page in range(start, end + 1):
            page_file = tmpdir / f"page-{source_page:06d}.pdf"
            if not page_file.exists():
                die(f"Expected extracted page is missing: {page_file}")
            parity_number = source_page if parity_basis == "source" else source_page - start + 1
            if parity_number % 2 == 1:
                odd_pages.append(page_file)
            else:
                even_pages.append(page_file)

        wrote_odd = unite_or_report(pdfunite, odd_pages, odd_output, overwrite)
        wrote_even = unite_or_report(pdfunite, even_pages, even_output, overwrite)

    return odd_output if wrote_odd else None, even_output if wrote_even else None


def split_pdf(input_pdf: Path, page_range: str | None, parity_basis: str, overwrite: bool, backend: str) -> tuple[Path | None, Path | None]:
    validate_input(input_pdf)

    has_pypdf = pypdf_available()
    if backend == "pypdf" and not has_pypdf:
        die("Python package 'pypdf' is not installed. Install it or use --backend poppler.")
    if backend == "pypdf" or (backend == "auto" and has_pypdf):
        return split_with_pypdf(input_pdf, page_range, parity_basis, overwrite)

    if backend == "auto":
        print("Python package 'pypdf' is not installed; falling back to Poppler tools.", file=sys.stderr)
    return split_with_poppler(input_pdf, page_range, parity_basis, overwrite)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trim a PDF by page range, then save odd/even pages as sibling PDFs."
    )
    parser.add_argument("pdf", type=Path, help="Path to the input PDF")
    parser.add_argument(
        "page_range",
        nargs="?",
        default=None,
        help="Optional 1-based page range, e.g. 1-20, 1:20, 5-, -10, or 7. Defaults to all pages.",
    )
    parser.add_argument(
        "--parity-basis",
        choices=("trimmed", "source"),
        default="trimmed",
        help="Use odd/even positions after trimming, or original source page numbers (default: trimmed)",
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "pypdf", "poppler"),
        default="auto",
        help="PDF processing backend. auto prefers pypdf and falls back to Poppler tools.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Replace existing *_odd.pdf and *_even.pdf files")
    args = parser.parse_args()

    split_pdf(args.pdf.expanduser().resolve(), args.page_range, args.parity_basis, args.overwrite, args.backend)


if __name__ == "__main__":
    main()
