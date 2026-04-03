# Output Format Specification

This document defines the standard output format for the video understanding skill.

Default principle: **First produce text results directly readable by end users, then output structured JSON / files.**

## Standard JSON Output Format

### Top-level Structure

```json
{
  "metadata": {
    "video_url": "https://www.bilibili.com/video/BV1W2wtzkEBR",
    "video_title": "Claude Code + Autoresearch = self-evolving AI",
    "duration_seconds": 1482,
    "duration_minutes": 24.7,
    "processed_at": "2026-03-18T08:00:00Z",
    "processor": "video-understanding-skill",
    "version": "1.0"
  },
  "asr": {
    "success": true,
    "error": null,
    "service_url": "http://192.168.71.57:8002",
    "model": "qwen3asr",
    "audio_file": "audio.mp3",
    "audio_size_mb": 5.8,
    "processing_time_seconds": 72,
    "text": "Full ASR transcription text...",
    "word_count": 3521,
    "duration_seconds": 1482
  },
  "ocr": {
    "success": false,
    "error": "OCR was not performed",
    "service_url": null,
    "frames_extracted": 0,
    "frames_processed": 0,
    "results": []
  },
  "summary": {
    "key_topics": [
      "Auto Research project introduction",
      "Claude Code integration",
      "Cold email optimization application example",
      "General application scenarios",
      "Self-evolving AI concept"
    ],
    "main_points": [
      "Andrej Karpathy released the Auto Research project, enabling AI autonomous experimentation",
      "Core paradigm: AI agent modifies code → trains → evaluates → keeps/discards → repeats",
      "Can be applied to any scenario with objective metrics and API access",
      "AI is not as smart as humans, but works 24/7 without rest, iterates faster"
    ],
    "timestamps": [
      {
        "time": "00:00",
        "time_seconds": 0,
        "topic": "Project introduction"
      },
      {
        "time": "05:30",
        "time_seconds": 330,
        "topic": "Cold email optimization example"
      },
      {
        "time": "15:00",
        "time_seconds": 900,
        "topic": "General application scenarios"
      }
    ],
    "speaker_opinions": {
      "project_evaluation": "very_positive",
      "generality": "highly_general",
      "future_outlook": "very_optimistic"
    }
  },
  "files": {
    "asr_result": "asr_result.json",
    "transcript": "transcript.txt",
    "video_analysis": "video_analysis.json"
  }
}
```

### ASR Success Format

```json
{
  "asr": {
    "success": true,
    "error": null,
    "service_url": "http://192.168.71.57:8002",
    "model": "qwen3asr",
    "audio_file": "audio.mp3",
    "audio_size_mb": 5.8,
    "processing_time_seconds": 72,
    "text": "Full ASR transcription text...",
    "word_count": 3521,
    "duration_seconds": 1482
  }
}
```

### ASR Failure Format

```json
{
  "asr": {
    "success": false,
    "error": "Maximum file size exceeded (parameter=audio_filesize_mb, value=45.2)",
    "error_code": "BadRequestError",
    "service_url": "http://192.168.71.57:8002",
    "model": "qwen3asr",
    "audio_file": "audio.wav",
    "audio_size_mb": 45.2,
    "suggestion": "Compress audio to MP3 32kbps or split into smaller chunks"
  }
}
```

### OCR Format

```json
{
  "ocr": {
    "success": true,
    "error": null,
    "service_url": "http://192.168.71.57:8001",
    "frames_extracted": 25,
    "frames_processed": 25,
    "processing_time_seconds": 45,
    "results": [
      {
        "frame": "frame_001.jpg",
        "frame_index": 1,
        "timestamp_seconds": 0,
        "timestamp": "00:00",
        "text": "Text recognized in this frame...",
        "confidence": 0.92
      }
    ]
  }
}
```

## Simplified Output (Optional)

For scenarios that only require ASR, you can use the simplified format:

```json
{
  "success": true,
  "text": "ASR transcription text...",
  "duration_seconds": 1482,
  "model": "qwen3asr"
}
```

## User Visible Text Templates

### Template A: ASR-only

```markdown
## Video Content Summary
- Topic: ...
- Core points: ...
- Conclusion / Recommendations: ...

## Key Takeaways
- ...
- ...
- ...

## Organized Transcript
...
```

Usage Guidelines:
- Provide summary first, then transcript
- Provide "easy-to-read transcript" by default, not raw unprocessed ASR text
- Provide a more complete version only when the user explicitly requests full/verbatim transcript

### Template B: ASR + OCR

```markdown
## Video Content Summary
- Topic: ...
- Audio content: ...
- On-screen text supplements: ...

## Integrated Key Information
- From audio: ...
- From on-screen text: ...
- Comprehensive assessment: ...

## Organized Transcript
### Audio Content
...

### On-screen Text
...
```

Usage Guidelines:
- Clearly distinguish between audio information and on-screen information sources
- If OCR does not provide significant new information, state this explicitly
- Do not just mechanically append OCR results at the end

### Transcript Quality Requirements

- Remove obviously repeated modal particles and verbal fillers
- Add basic punctuation and paragraph breaks
- Keep original meaning, do not over-polish into a different article
- Mark uncertain words with "[Uncertain]" or note them in the description

## File Output

### Required Files

1. `asr_result.json` - Raw ASR API response
2. `transcript.txt` - Plain text ASR transcription (easy to read)
3. `video_analysis.json` - Complete structured analysis result (format defined above)

### Optional Files

1. `ocr_results/` directory - OCR results for each frame (if OCR was performed)
2. `frames/` directory - Extracted video frames (if OCR was performed)
3. `summary.md` - Markdown format summary (optional)

## Summary Markdown Format (Optional)

```markdown
# Video Analysis Summary

## Basic Information

- **Video Title**: Claude Code + Autoresearch = self-evolving AI
- **Video URL**: https://www.bilibili.com/video/BV1W2wtzkEBR
- **Duration**: 24:42 (1482 seconds)
- **Processing Time**: 2026-03-18 08:00:00 UTC

## Core Topics

1. Auto Research project introduction
2. Claude Code integration
3. Cold email optimization application example
4. General application scenarios
5. Self-evolving AI concept

## Main Points

- Andrej Karpathy released the Auto Research project, enabling AI autonomous experimentation
- Core paradigm: AI agent modifies code → trains → evaluates → keeps/discards → repeats
- Can be applied to any scenario with objective metrics and API access
- AI is not as smart as humans, but works 24/7 without rest, iterates faster

## Timeline

| Time | Topic |
|------|-------|
| 00:00 | Project introduction |
| 05:30 | Cold email optimization example |
| 15:00 | General application scenarios |

## ASR Information

- **Model**: qwen3asr
- **Processing Time**: 72 seconds
- **Word Count**: 3,521 words
```
