---
name: pdf-to-audio-minimax
description: Convert a scanned or image-heavy PDF book/chapter into one continuous, playable MiniMax MP3. Use this skill whenever the user asks to read a PDF aloud, turn a PDF/book/chapter into an audiobook, OCR PDF pages before speech synthesis, or combine local OCR with MiniMax TTS. The workflow uses the local OpenAI-compatible GLM-OCR service, removes page numbers, headers/footers, footnotes, citations, figure captions, and decorative image content, repairs cross-page sentence breaks, then generates and validates the final audio.
compatibility: Requires Python 3.10+, ffmpeg, PyMuPDF, Pillow, websockets, a reachable local GLM-OCR OpenAI-compatible endpoint, and MINIMAX_API_KEY for MiniMax TTS.
---

# PDF to continuous audio with local OCR and MiniMax

Use the bundled `scripts/pdf_to_audio.py` for the deterministic parts of this workflow. It preserves the source document's language and is not tied to a particular book genre; the OCR model still needs to support the document's language.

## When to use

Use this skill when the user wants the textual contents of a PDF spoken aloud or asks for an audiobook/audio file from a PDF. It is especially appropriate when the PDF is scanned, when the user requests page-by-page OCR, or when the user specifically names a local OCR endpoint and MiniMax.

Do not use it for extracting audio already embedded in a PDF, summarizing a PDF into a short narration, or creating an audiobook from an already-clean text file.

## Defaults

- Local OCR REST base: `http://10.243.80.19:8001/v1`
- OCR model: `glmocr`
- MiniMax REST base: `https://api.minimaxi.com/v1`
- MiniMax WebSocket: derived as `wss://<host>/ws/v1/t2a_v2`
- TTS model: `speech-2.8-hd`
- Voice: `male-qn-qingse`
- OCR language hint: `auto` (preserve the original language)
- PDF rendering: 150 DPI, JPEG quality 72
- TTS chunk size: 8,500 characters, split at paragraph/sentence boundaries

The MiniMax API key must already be available as `MINIMAX_API_KEY`. The OCR and MiniMax endpoint defaults can be overridden with `--ocr-base-url`, `--minimax-api-endpoint`, or the environment variables `PDF_OCR_BASE_URL` and `MINIMAX_API_ENDPOINT`; the TTS model and voice can likewise be set with `MINIMAX_TTS_MODEL` and `MINIMAX_VOICE_ID`. For a language other than the default voice's strongest language, choose a suitable voice with `--voice-id`. Never print, write, or include the key in prompts, logs, or output files.

## Workflow

1. Identify the input PDF. If the user did not provide a path, inspect the current working directory for a likely PDF and state which one will be used.
2. Check that `ffmpeg`, Python dependencies, the OCR endpoint, the OCR model, and `MINIMAX_API_KEY` are available. A lightweight check of `/v1/models` is appropriate before spending TTS credits.
3. Run the bundled script. It renders pages to PNG, creates smaller JPEG transport images, OCRs pages sequentially, and saves each page result. Existing page results are reused so interrupted runs can resume.
4. Merge and clean the OCR text:
   - remove page numbers, repeated headers/footers, footnotes, notes, bibliographic citations, and figure/diagram captions;
   - ignore illustrations and decorative elements rather than describing them;
   - preserve body paragraphs, section headings, and meaningful table text in a speakable form;
   - remove OCR footnote markers and repair obvious cross-page sentence joins;
   - make only conservative OCR cleanup corrections; do not invent missing content.
5. Split the cleaned text below the MiniMax per-request limit. Keep paragraph boundaries whenever possible.
6. Synthesize each chunk through the MiniMax WebSocket API. Each returned MP3 chunk is decoded/re-encoded before concatenation because raw streamed MP3 chunks may contain metadata/junk that some players reject.
7. Concatenate the cleaned chunks, re-encode the final MP3 once, and run `ffmpeg -v error` against it. Report the final path, size, duration if available, and the cleaned text path.

## Command

From the user's working directory, run:

```bash
python3 <skill-directory>/scripts/pdf_to_audio.py "input.pdf"
```

Useful overrides:

```bash
python3 <skill-directory>/scripts/pdf_to_audio.py "input.pdf" \
  --ocr-base-url http://10.243.80.19:8001/v1 \
  --document-language auto \
  --ocr-extra-instructions "Preserve mathematical notation in readable form." \
  --minimax-api-endpoint https://api.minimaxi.com/v1 \
  --tts-model speech-2.8-hd \
  --voice-id male-qn-qingse \
  --output-dir ./audio-output
```

For a page range, use `--start-page N --end-page M`. Use `--force` only when the user explicitly wants audio chunks regenerated; normal reruns reuse completed OCR and TTS chunks.

## Outputs

For `book.pdf`, the default outputs are placed beside the input:

- `book_minimax.mp3` — final validated, playable audio;
- `book_clean.txt` — continuous cleaned text used for TTS;
- `.book.pdf_to_audio/` — resumable intermediate pages, OCR results, TTS chunks, and concat metadata.

Link the final audio file using an absolute local markdown link. If the user reports a player compatibility problem, provide the cleaned MP3 produced after re-encoding; do not hand off the raw streamed chunk file. A WAV fallback can be created with `ffmpeg` if needed.

## Failure handling

- If `MINIMAX_API_KEY` is missing, stop before any TTS call and ask the user to set it.
- If OCR `/v1/models` is unreachable, report the endpoint failure and do not fabricate text.
- If Python sends requests through a proxy and the private OCR host returns Tinyproxy errors, force a direct `ProxyHandler({})` connection as the bundled script does.
- Retry each OCR page up to three times, saving successful pages immediately.
- If MiniMax fails for a chunk, preserve completed chunks and report the failing chunk; rerunning should resume after the failure.
- If the final `ffmpeg` validation fails, do not claim success. Inspect the chunk files and regenerate the affected audio rather than returning an unverified file.

## User-facing handoff

Lead with the result. State how many pages were OCR'd, what was excluded, that the audio was validated, and provide the final audio link. Mention the text file only as an optional inspection artifact. Do not expose API keys or raw service responses.
