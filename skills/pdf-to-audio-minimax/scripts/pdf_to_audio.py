#!/usr/bin/env python3
"""Convert a scanned/text PDF to one cleaned MiniMax MP3 via local GLM-OCR."""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


OCR_PROMPT_TEMPLATE = """Read this document page in its original language and perform OCR. The document language is {language}.

Return only the main body text in normal reading order. Preserve paragraphs, section headings, and meaningful table text, but join visual line wraps inside a paragraph.

Exclude page numbers, running headers and footers, repeated chapter titles, marginal/decorative text, footnotes, endnotes, bibliographic references, in-text citation markers, source attributions, figure/diagram captions, illustrations, and other non-narrative graphics. Do not describe images or add text that is not visible. If a character is genuinely unreadable, write [unclear]. Do not wrap the result in a code block or add an OCR explanation.
{extra}"""

NOTE_MARKER_RE = re.compile(
    r"(?:translator(?:'s)?\s+note|footnotes?|endnotes?|bibliograph(?:y|ies)|references?|"
    r"source\s*:|image\s+source|译者注|脚注|尾注|参考文献|资料来源|出处)",
    re.IGNORECASE,
)
FIGURE_MARKER_RE = re.compile(
    r"(?:figure|fig\.?|diagram|illustration|plate|图|图表)\s*(?:no\.?|#)?\s*\d+",
    re.IGNORECASE,
)
TERMINAL_CHARS = "。！？；：.!?;:)]}」』】”’\"'"


def build_ocr_prompt(language: str, extra: str = "") -> str:
    language = language.strip() or "auto-detect"
    extra_text = extra.strip()
    if extra_text:
        extra_text = "Additional user instructions:\n" + extra_text
    return OCR_PROMPT_TEMPLATE.format(language=language, extra=extra_text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Input PDF path")
    parser.add_argument("--ocr-base-url", default=os.getenv("PDF_OCR_BASE_URL", "http://10.243.80.19:8001/v1"))
    parser.add_argument("--ocr-model", default="glmocr")
    parser.add_argument("--document-language", default="auto", help="Language hint for OCR; default: auto")
    parser.add_argument("--ocr-extra-instructions", default="", help="Extra OCR instructions")
    parser.add_argument("--minimax-api-endpoint", default=os.getenv("MINIMAX_API_ENDPOINT", "https://api.minimaxi.com/v1"))
    parser.add_argument("--minimax-ws-url", default=None)
    parser.add_argument("--tts-model", default=os.getenv("MINIMAX_TTS_MODEL", "speech-2.8-hd"))
    parser.add_argument("--voice-id", default=os.getenv("MINIMAX_VOICE_ID", "male-qn-qingse"))
    parser.add_argument("--start-page", type=int, default=1)
    parser.add_argument("--end-page", type=int, default=None)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--jpeg-quality", type=int, default=72)
    parser.add_argument("--max-tts-chars", type=int, default=8500)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--force", action="store_true", help="Regenerate audio chunks and final audio")
    return parser.parse_args()


def require_runtime() -> None:
    missing = [name for name in ("ffmpeg",) if shutil.which(name) is None]
    if missing:
        raise SystemExit("Missing command(s): " + ", ".join(missing))
    try:
        import fitz  # noqa: F401
        import PIL  # noqa: F401
        import websockets  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "Install dependencies first: python -m pip install pymupdf pillow websockets"
        ) from exc


def extract_pages(pdf: Path, page_dir: Path, start: int, end: int, dpi: int) -> None:
    import fitz

    page_dir.mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf) as document:
        if start < 1 or end < start:
            raise ValueError(f"invalid page range: {start}-{end}")
        if end > len(document):
            raise ValueError(f"end page {end} exceeds PDF page count {len(document)}")
        scale = dpi / 72
        matrix = fitz.Matrix(scale, scale)
        for page_no in range(start, end + 1):
            output = page_dir / f"page_{page_no:03d}.png"
            if output.exists() and output.stat().st_size:
                continue
            pixmap = document[page_no - 1].get_pixmap(matrix=matrix, alpha=False)
            pixmap.save(output)
            print(f"extracted page {page_no}/{end}", flush=True)


def make_jpegs(page_dir: Path, jpg_dir: Path, quality: int) -> None:
    from PIL import Image

    jpg_dir.mkdir(parents=True, exist_ok=True)
    for png in sorted(page_dir.glob("page_*.png")):
        output = jpg_dir / f"{png.stem}.jpg"
        if output.exists() and output.stat().st_size:
            continue
        with Image.open(png) as image:
            image.convert("RGB").save(output, "JPEG", quality=quality, optimize=True)


def chat_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    return base if base.endswith("/chat/completions") else base + "/chat/completions"


def check_ocr_endpoint(base_url: str, model: str) -> None:
    models_url = base_url.rstrip("/") + "/models"
    request = urllib.request.Request(models_url)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=20) as response:
        result = json.load(response)
    available = {item.get("id") for item in result.get("data", [])}
    if model not in available:
        raise RuntimeError(f"OCR model {model!r} not found at {models_url}; available={sorted(available)}")


def ocr_page(image: Path, endpoint: str, model: str, prompt: str) -> str:
    encoded = base64.b64encode(image.read_bytes()).decode("ascii")
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {
                    "url": "data:image/jpeg;base64," + encoded,
                    "detail": "high",
                }},
            ],
        }],
        "temperature": 0,
        "max_tokens": 4096,
    }
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    # The private OCR host is on an internal network. Bypass the shell's HTTP proxy;
    # Python's urllib does not consistently interpret CIDR entries in no_proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=180) as response:
        result = json.load(response)
    choices = result.get("choices") or []
    content = choices[0].get("message", {}).get("content") if choices else None
    if not content:
        raise RuntimeError(f"OCR returned no text for {image.name}")
    return content.strip()


def run_ocr(jpg_dir: Path, result_dir: Path, endpoint: str, model: str, prompt: str) -> None:
    result_dir.mkdir(parents=True, exist_ok=True)
    pages = sorted(jpg_dir.glob("page_*.jpg"))
    for index, image in enumerate(pages, 1):
        output = result_dir / f"{image.stem}.md"
        if output.exists() and output.stat().st_size:
            print(f"OCR reuse {index}/{len(pages)} {image.name}", flush=True)
            continue
        for attempt in range(1, 4):
            try:
                text = ocr_page(image, endpoint, model, prompt)
                output.write_text(text + "\n", encoding="utf-8")
                print(f"OCR done {index}/{len(pages)} chars={len(text)}", flush=True)
                break
            except Exception as exc:
                if attempt == 3:
                    raise
                print(f"OCR retry {image.name} attempt={attempt}: {exc}", flush=True)
                time.sleep(2)


def clean_page(text: str) -> str:
    kept: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or NOTE_MARKER_RE.search(line):
            if not line:
                kept.append("")
            continue
        figure = FIGURE_MARKER_RE.search(line)
        if figure:
            line = line[:figure.start()].rstrip()
            if not line:
                continue
        line = re.sub(r"\$\^\d+\$|\[\^\d+\]", "", line)
        if "|" in line:
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if cells and all(re.fullmatch(r":?-{2,}:?", cell) for cell in cells):
                continue
            line = "；".join(cell for cell in cells if cell)
        line = re.sub(r"^\s*[-*+•●◦▪‣⁃]\s+", "", line)
        line = re.sub(r"(?<=[\u3400-\u9fff])\s+(?=[\u3400-\u9fff])", "", line)
        line = re.sub(r"\s+([，。！？；：、）》】”’])", r"\1", line)
        line = re.sub(r"([（《【“‘])\s+", r"\1", line)
        if line:
            kept.append(line)
    result: list[str] = []
    blank = False
    for line in kept:
        if not line:
            if not blank:
                result.append("")
            blank = True
        else:
            result.append(line)
            blank = False
    return "\n".join(result).strip()


def merge_text(result_dir: Path, output: Path) -> str:
    files = sorted(result_dir.glob("page_*.md"))
    if not files:
        raise RuntimeError("No OCR result files found")
    pages = [clean_page(path.read_text(encoding="utf-8")) for path in files]
    merged = pages[0]
    for page in pages[1:]:
        if not page:
            continue
        left = merged.rstrip()
        right = page.lstrip()
        last = left[-1:] if left else ""
        first = right[:1]
        if last == "-":
            merged = left[:-1] + right
        elif last and last not in TERMINAL_CHARS:
            separator = " " if last.isalnum() and first.isalnum() else ""
            merged = left + separator + right
        else:
            merged = left + "\n\n" + right
    merged = re.sub(r"\n{3,}", "\n\n", merged).strip()
    output.write_text(merged + "\n", encoding="utf-8")
    return merged


def split_text(text: str, limit: int) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else current + "\n\n" + paragraph
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        while len(paragraph) > limit:
            positions = [paragraph.rfind(mark, 0, limit) for mark in "。！？；"]
            cut = max(positions)
            if cut < limit // 2:
                cut = limit
            chunks.append(paragraph[:cut])
            paragraph = paragraph[cut:]
        current = paragraph
    if current:
        chunks.append(current)
    return chunks


def ws_url(rest_endpoint: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    parsed = urlparse(rest_endpoint)
    return f"wss://{parsed.netloc}/ws/v1/t2a_v2"


async def receive_json(ws: object) -> dict:
    raw = await asyncio.wait_for(ws.recv(), timeout=180)
    if isinstance(raw, bytes):
        raise RuntimeError("unexpected binary WebSocket frame")
    return json.loads(raw)


async def synthesize(text: str, output: Path, endpoint: str, model: str, voice_id: str) -> None:
    import websockets

    key = os.getenv("MINIMAX_API_KEY")
    if not key:
        raise RuntimeError("MINIMAX_API_KEY is not set")
    audio = bytearray()
    async with websockets.connect(
        endpoint,
        additional_headers={"Authorization": f"Bearer {key}"},
        open_timeout=20,
        close_timeout=10,
    ) as ws:
        connected = await receive_json(ws)
        if connected.get("event") != "connected_success":
            raise RuntimeError(f"MiniMax connection failed: {connected}")
        await ws.send(json.dumps({
            "event": "task_start",
            "model": model,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": 1,
                "vol": 1,
                "pitch": 0,
                "english_normalization": False,
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1,
            },
        }))
        started = await receive_json(ws)
        if started.get("event") != "task_started":
            raise RuntimeError(f"MiniMax task start failed: {started}")
        await ws.send(json.dumps({"event": "task_continue", "text": text}, ensure_ascii=False))
        while True:
            response = await receive_json(ws)
            base = response.get("base_resp") or {}
            status = response.get("status_code", base.get("status_code"))
            if status not in (None, 0):
                raise RuntimeError(f"MiniMax synthesis failed: {response}")
            data = response.get("data") or {}
            if isinstance(data, dict) and data.get("audio"):
                audio.extend(bytes.fromhex(data["audio"]))
            if response.get("is_final") is True or data.get("is_final") is True or response.get("event") in {"task_finished", "task_finish"}:
                break
        await ws.send(json.dumps({"event": "task_finish"}))
    if not audio:
        raise RuntimeError("MiniMax returned no audio")
    output.write_bytes(audio)


def clean_mp3(raw: Path, output: Path) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(raw),
        "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "32000", "-ac", "1", str(output),
    ], check=True)


def combine_mp3(files: list[Path], output: Path, work: Path) -> None:
    concat = work / "concat.txt"
    entries = []
    for path in files:
        escaped = str(path.resolve()).replace("'", "'\\''")
        entries.append(f"file '{escaped}'")
    concat.write_text("\n".join(entries) + "\n", encoding="utf-8")
    joined = work / "joined.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
        "-i", str(concat), "-c:a", "copy", str(joined),
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(joined),
        "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "32000", "-ac", "1", str(output),
    ], check=True)


async def run(args: argparse.Namespace) -> None:
    require_runtime()
    if not os.getenv("MINIMAX_API_KEY"):
        raise SystemExit("MINIMAX_API_KEY is not set; refusing to start the workflow")
    pdf = args.pdf.resolve()
    if not pdf.exists():
        raise SystemExit(f"PDF not found: {pdf}")
    import fitz

    with fitz.open(pdf) as document:
        last_page = len(document)
    end_page = args.end_page or last_page
    output_dir = (args.output_dir or pdf.parent).resolve()
    work = output_dir / f".{pdf.stem}.pdf_to_audio"
    page_dir = work / "pages_png"
    jpg_dir = work / "pages_jpg"
    result_dir = work / "ocr_results"
    audio_dir = work / "tts_audio"
    clean_text = output_dir / f"{pdf.stem}_clean.txt"
    final_audio = output_dir / f"{pdf.stem}_minimax.mp3"
    work.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    if args.force and final_audio.exists():
        final_audio.unlink()

    extract_pages(pdf, page_dir, args.start_page, end_page, args.dpi)
    make_jpegs(page_dir, jpg_dir, args.jpeg_quality)
    check_ocr_endpoint(args.ocr_base_url, args.ocr_model)
    prompt = build_ocr_prompt(args.document_language, args.ocr_extra_instructions)
    run_ocr(jpg_dir, result_dir, chat_url(args.ocr_base_url), args.ocr_model, prompt)
    text = merge_text(result_dir, clean_text)
    chunks = split_text(text, args.max_tts_chars)
    print(f"clean text chars={len(text)} chunks={len(chunks)}", flush=True)

    ws_endpoint = ws_url(args.minimax_api_endpoint, args.minimax_ws_url)
    clean_chunks: list[Path] = []
    for index, chunk in enumerate(chunks, 1):
        raw = audio_dir / f"chunk_{index:03d}_raw.mp3"
        clean = audio_dir / f"chunk_{index:03d}.mp3"
        if args.force and clean.exists():
            clean.unlink()
        if not clean.exists():
            print(f"TTS {index}/{len(chunks)} chars={len(chunk)}", flush=True)
            await synthesize(chunk, raw, ws_endpoint, args.tts_model, args.voice_id)
            clean_mp3(raw, clean)
        else:
            print(f"TTS reuse {index}/{len(chunks)}", flush=True)
        clean_chunks.append(clean)
    combine_mp3(clean_chunks, final_audio, work)
    print(f"audio={final_audio} bytes={final_audio.stat().st_size}", flush=True)
    subprocess.run(["ffmpeg", "-v", "error", "-i", str(final_audio), "-f", "null", "-"], check=True)
    print("audio validation: passed", flush=True)


def main() -> None:
    try:
        asyncio.run(run(parse_args()))
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        raise SystemExit(130)


if __name__ == "__main__":
    main()
