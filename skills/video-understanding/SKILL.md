---
name: video-understanding
description: Automatically analyze, transcribe, and summarize video content from Bilibili, YouTube, and other platforms. Converts video to text using ASR (speech-to-text) with LAN/Bailian fallback, and extracts text from video frames via OCR when requested. Trigger phrases: video analysis, video transcription, video summary, extract text from video, video OCR, Bilibili, YouTube, video to text, speech to text, ASR, transcribe video, understand video content, video frame text extraction
---

# Video Understanding Skill
A complete pipeline for extracting text and understanding content from online and local videos.

## Overview
This skill processes video content to produce human-readable text transcripts and summaries:
- Downloads videos from 1000+ platforms via yt-dlp
- Converts speech to text with multi-layer ASR fallback
- Extracts on-screen text, subtitles, and PPT content via OCR when requested
- Combines and formats results for direct user consumption
- Automatically cleans up intermediate files after processing

## Modes
Two processing modes are available:
1. **ASR-only (Default)**: Fastest mode, transcribes only audio content. Use for standard requests like "summarize this video", "transcribe this speech", or "get the text from this video".
2. **ASR + OCR**: Extracts both audio speech and text from video frames. Use only when the user explicitly asks for screen text, hardcoded subtitles, presentation content, or any text visible in the video itself.

## Quick Start

All scripts accept `--workdir <path>` (default: `/tmp/video-understanding/`) to control where intermediate files are written. Pass `--help` to any script for full usage details.

1. **ASR-only mode (default)** — transcribe audio only:
```bash
python SCRIPTS/full_pipeline.py "<VIDEO_URL>" http://192.168.71.57:8002
```

2. **ASR + OCR mode** — also extract on-screen text from frames:
```bash
python SCRIPTS/full_pipeline.py "<VIDEO_URL>" http://192.168.71.57:8002 --ocr-url http://192.168.71.57:8001
```

3. **Custom frame interval** (default: 15 seconds):
```bash
python SCRIPTS/full_pipeline.py "<VIDEO_URL>" http://192.168.71.57:8002 --ocr-url http://192.168.71.57:8001 --ocr-interval 10
```

Where `SCRIPTS` = `/home/rlan/.openclaw/skills/video-understanding/scripts`.

## Working Directory

All scripts default to `/tmp/video-understanding/` as their working directory (configurable via `--workdir`). This keeps the skill installation directory clean — intermediate files (video.mp4, audio.mp3, frames/) are written to the workdir, not alongside the scripts.

To use a unique directory per run:
```bash
python SCRIPTS/full_pipeline.py "<VIDEO_URL>" http://192.168.71.57:8002 --workdir /tmp/vu-$(date +%s)
```

Clean up when done:
```bash
python SCRIPTS/clean_cache.py --workdir /tmp/vu-<id>
```

## Step-by-Step Workflow

For debugging or when you need control over individual steps. All scripts accept `--workdir` to specify output location.

### ASR-only Workflow
1. Download the video:
```bash
python SCRIPTS/download_video.py "<VIDEO_URL>"
```
2. Extract and compress audio to MP3:
```bash
python SCRIPTS/prepare_audio.py <video-file>
```
3. Run ASR transcription (auto-detects model, with Bailian fallback):
```bash
python SCRIPTS/call_asr.py audio.mp3 http://192.168.71.57:8002
```
4. Read `transcript.txt` and present results to the user

### ASR + OCR Workflow
1. Download and prepare audio (steps 1-2 above)
2. Run ASR (step 3 above)
3. Extract frames from video:
```bash
python SCRIPTS/extract_frames.py <video-file> 15
```
4. Run OCR on the frames:
```bash
python SCRIPTS/call_ocr.py frames http://192.168.71.57:8001
```
5. Read `transcript.txt` and `frames/ocr_text.txt`, merge results, present to the user

### Using the Full Pipeline (recommended)
The `full_pipeline.py` script runs all steps automatically (download → audio → ASR, and optionally OCR in parallel):
```bash
# ASR-only
python SCRIPTS/full_pipeline.py "<VIDEO_URL>" http://192.168.71.57:8002

# ASR + OCR
python SCRIPTS/full_pipeline.py "<VIDEO_URL>" http://192.168.71.57:8002 --ocr-url http://192.168.71.57:8001
```

Where `SCRIPTS` = `/home/rlan/.openclaw/skills/video-understanding/scripts`.

## Service Configuration
Default service endpoints (adapt to your environment if these are not available):
- **ASR Service**: `http://192.168.71.57:8002` (LAN first, with automatic fallback to Bailian API Qwen3-ASR-Flash if the LAN service is unreachable)
- **OCR Service**: `http://192.168.71.57:8001` (LAN first, with automatic fallback to VLM multimodal subagent if the LAN service is unreachable)

The ASR script automatically splits long audio files into chunks for reliable processing, and retries failed requests up to 3 times before falling back to the secondary service.

## Dependencies
Ensure these are available in your environment:
1. `yt-dlp`: For downloading videos from 1000+ platforms (keep updated for new site support)
2. `ffmpeg`: For audio extraction, compression, and video frame extraction
3. Python 3.8+ with the `requests` library installed
4. Network access to either the LAN ASR/OCR services or their respective fallbacks

## Output Presentation
Always present results directly to the user, not just file paths:
1. Start with a concise summary of the video content (1-3 paragraphs) if the user requested a summary
2. For transcription requests, provide the full, formatted transcript with timestamps if available
3. If using OCR mode, group frame text by timestamp and insert it into the transcript at the appropriate positions, or clearly mark OCR content as separate sections
4. Do not include raw JSON outputs or technical metadata in user-facing responses

## Troubleshooting
For common issues:
- **Video download failures**: Update yt-dlp to the latest version, or check if the URL is accessible in your network environment
- **ASR errors**: Verify connectivity to the LAN ASR service, or manually use the Bailian API fallback if needed
- **OCR errors**: Ensure frames are extracted correctly, or use the VLM subagent directly for low-quality frame text
- **Permission errors**: Confirm you have write access to the temporary working directory you created

All scripts support `--help` flag for additional usage details and parameter options.

