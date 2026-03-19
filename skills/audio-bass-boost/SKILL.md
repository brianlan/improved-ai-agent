---
name: audio-bass-boost
description: |
  Audio processing skill that enhances bass frequencies, reduces mid/high frequencies, and shifts pitch up by one octave (8 semitones). 
  
  Use when users need to:
  1. Process audio files (MP3, M4A, WAV) to boost low frequencies and cut mids/highs
  2. Shift audio pitch up by 8 degrees (one octave) for higher pitch effect
  3. Apply EQ adjustments to emphasize bass while maintaining audio quality
  4. Process guitar tracks, music, or voice recordings for specific tonal characteristics
  
  Triggers: "提高音频8度", "boost bass", "EQ adjustment", "pitch shift", "音频处理", "增强低音", "削弱中高频"
---

# Audio Bass Boost Skill

Process audio files with pitch shifting and EQ adjustments.

## Quick Start

Process an audio file with default settings:

```bash
python scripts/audio_processor.py "/path/to/audio.mp3"
```

The output will be saved as `{original_name}_processed.{ext}` in the same directory.

## Features

### 1. Pitch Shift (+8 Degrees / One Octave)
Uses librosa's high-quality phase vocoder to shift pitch up by 12 semitones:
- `kaiser_best` resampling for minimal quality loss
- Preserves tempo while changing pitch
- Suitable for guitar tracks, vocals, or any audio

### 2. EQ Adjustments
Frequency response curve applied:

| Frequency Range | Adjustment | Effect |
|----------------|------------|--------|
| < 200Hz | +6dB | Strong bass boost |
| 200-400Hz | +3dB to 0dB | Low-mid enhancement |
| 400-2000Hz | -6dB | Mid frequency cut |
| 2000-6000Hz | -6dB to -12dB | High-mid reduction |
| > 6000Hz | -12dB | High frequency cut |

### 3. Quality Preservation
- 24-bit internal processing
- Maintains original sample rate
- Soft limiting to prevent clipping
- Stereo channel processing (preserves spatial imaging)

## Supported Formats

**Input:** MP3, M4A, AAC, WAV, FLAC, OGG
**Output:** Same format as input (MP3 uses V0 quality, M4A uses 320kbps AAC)

## Requirements

Install dependencies before first use:

```bash
pip install librosa soundfile scipy numpy audioread resampy
```

Or use the provided conda environment:
```bash
conda activate cqgui_py312  # or your preferred environment
pip install -r scripts/requirements.txt
```

## Usage Examples

### Basic Usage
```bash
python scripts/audio_processor.py "song.mp3"
# Output: song_processed.mp3
```

### Custom Output Path
```python
from scripts.audio_processor import process_audio

process_audio("input.mp3", "output.mp3")
```

### Batch Processing
```bash
for file in *.mp3; do
    python scripts/audio_processor.py "$file"
done
```

## Technical Details

### Algorithm
1. **FFT-based EQ**: Applies frequency-domain equalization using numpy FFT
2. **Phase Vocoder**: librosa's time-stretch + resample pitch shift
3. **Butterworth Filter**: 2nd-order lowpass at 8kHz for smoothness
4. **Normalization**: Prevents clipping with 0.98 headroom

### Performance
- Processing speed: ~1-2x real-time on modern CPUs
- Memory usage: ~500MB for 5-minute stereo track
- Temporary files: Created during MP3/M4A encoding, auto-deleted

## Troubleshooting

**Import Error: No module named 'librosa'**
```bash
pip install librosa soundfile scipy numpy audioread resampy
```

**FFmpeg not found (for MP3/M4A output)**
Install FFmpeg: `brew install ffmpeg` (macOS) or `apt-get install ffmpeg` (Linux)

**Memory Error with large files**
Process in chunks or convert to WAV first

## File Structure

```
audio-bass-boost/
├── SKILL.md                    # This file
├── scripts/
│   ├── audio_processor.py      # Main processing script
│   └── requirements.txt        # Python dependencies
└── references/
    └── eq_curves.md           # Detailed EQ curve documentation
```
