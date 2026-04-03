# SLA (Service Level Agreement) Details

This document details the expected performance metrics for ASR and OCR services.

## ASR Performance Metrics

### Expected Time Based on Audio Size

| Audio Size (MP3, 32kbps) | Audio Duration | Expected Processing Time | Confidence |
|---------------------------|----------------|---------------------------|------------|
| < 5 MB | < 5 minutes | 15-60 seconds | High |
| 5-10 MB | 5-10 minutes | 30-90 seconds | High |
| 10-20 MB | 10-20 minutes | 1-3 minutes | Medium |
| 20-30 MB | 20-30 minutes | 3-6 minutes | Medium |
| 30-50 MB | 30-60 minutes | 5-10 minutes | Low |
| > 50 MB | > 60 minutes | May timeout | Not recommended |

### Optimization Recommendations Based on Audio Format

| Format | Sample Rate | Channels | Bitrate | Relative Size | Recommended Scenario |
|--------|-------------|----------|---------|---------------|----------------------|
| WAV (PCM16) | 16kHz | 1 | N/A | 100% | Short audio (<5 minutes) |
| MP3 | 16kHz | 1 | 32kbps | ~15% | Most scenarios |
| MP3 | 16kHz | 1 | 16kbps | ~8% | Long audio (>30 minutes) |
| MP3 | 8kHz | 1 | 16kbps | ~4% | Speech only, low quality requirements |

## OCR Performance Metrics

| Processing Strategy | Number of Frames | Expected Processing Time | Notes |
|----------------------|-------------------|---------------------------|-------|
| Sparse sampling (1/60fps) | ~1 frame/minute | 10-60 seconds/10 frames | Recommended for long videos |
| Keyframe extraction | Variable (usually <10% of total frames) | Depends on number of keyframes | Best balance |
| Full frame sampling | All | May be very long | Not recommended unless necessary |

## Video Download Performance

| Video Duration | Expected Download Time (10Mbps) | Expected Download Time (50Mbps) |
|----------------|----------------------------------|----------------------------------|
| 5 minutes | 10-30 seconds | 5-15 seconds |
| 10 minutes | 20-60 seconds | 10-30 seconds |
| 30 minutes | 1-3 minutes | 30-90 seconds |
| 60 minutes | 2-6 minutes | 1-3 minutes |

## Timeout Recommendations

| Task Type | Recommended Timeout |
|-----------|----------------------|
| Video download | Video duration × 3 |
| Audio extraction | Video duration × 2 |
| ASR (short audio <10 minutes) | 5 minutes |
| ASR (medium 10-30 minutes) | 15 minutes |
| ASR (long audio >30 minutes) | 30 minutes |
| OCR (10 frames) | 5 minutes |

## Error Handling Strategies

### ASR File Too Large

1. First try compression: reduce bitrate to 16kbps or 8kbps
2. If still too large, split audio: 10-15 minutes per file
3. Process each segment separately, then merge results

### ASR Timeout

1. Check file size, consider compression or splitting
2. Increase timeout (maximum 30 minutes)
3. If timeouts persist, try smaller audio segments

### OCR Performance Issues

1. Reduce number of frames processed: use 1/60fps or keyframes
2. Only perform OCR when truly needed
3. Process multiple frames in parallel (if service supports)

## Quality vs Speed Tradeoffs

| Priority | Strategy | Expected Result |
|----------|----------|------------------|
| Quality priority | Use WAV 16kHz mono | Large file, slow processing, highest quality |
| Balanced | Use MP3 32kbps 16kHz | Recommended default choice |
| Speed priority | Use MP3 16kbps 8kHz | Fastest, but may affect ASR quality |
