---
name: extract-audio-from-video
description: "Extract audio from video files and save as MP3. Use when the user wants to convert video files (MP4) to audio (MP3) in batch. Triggers on requests like: extract audio from videos, convert videos to mp3, save audio from video files, or any task involving batch audio extraction from video files in a directory."
---

# Extract Audio from Video

## Overview

Extracts audio tracks from MP4 video files and saves them as MP3 files in a separate output directory. Handles all files automatically in one command - no manual re-runs needed.

## One-Command Usage

When the user requests audio extraction, run this SINGLE command:

```bash
nohup bash /home/rlan/projects/improved-ai-agent/skills/extract_audio_from_video/scripts/extract.sh "/path/to/videos" "/path/to/audios" > /tmp/audio_extraction.log 2>&1 &
```

Replace `/path/to/videos` and `/path/to/audios` with actual paths. The script runs in background and processes ALL files automatically.

## Parameters

| Parameter | Value |
|-----------|-------|
| Input format | MP4 only |
| Output format | MP3 (libmp3lame) |
| Quality | VBR ~190kbps (`-q:a 2`) |
| Skip behavior | Skip if MP3 exists |

## How It Works

1. **nohup + &** - Runs script in background, survives tool timeout
2. **Automatic loop** - Script loops until all files processed
3. **Skip existing** - Already-processed files are skipped on re-run
4. **Progress** - Check with `tail /tmp/audio_extraction.log`

## Verification

After completion (or during), check:
```bash
echo "Videos: $(ls /path/to/videos/*.mp4 | wc -l)"
echo "Audios: $(ls /path/to/audios/*.mp3 | wc -l)"
du -sh /path/to/audios
```

Or monitor progress:
```bash
tail -f /tmp/audio_extraction.log
```
