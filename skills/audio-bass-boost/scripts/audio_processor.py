#!/usr/bin/env python3
"""
Audio processing: Pitch shift +8 degrees (one octave) with bass boost EQ
High-quality phase vocoder algorithm to minimize quality loss
"""

import sys
import os
import numpy as np
import librosa
import soundfile as sf
from scipy import signal
from pathlib import Path


def apply_eq_low_boost(y, sr):
    """
    Apply EQ: Boost lows, cut mids and highs
    Using FFT-based equalization
    """
    # EQ Parameters
    low_freq = 200      # Low freq cutoff
    mid_low = 400       # Low-mid range
    mid_high = 2000     # Mid-high range
    high_freq = 6000    # High freq cutoff
    
    # FFT-based EQ
    freqs = np.fft.rfftfreq(len(y), d=1/sr)
    
    # Design EQ curve (in dB)
    eq_db = np.zeros_like(freqs, dtype=np.float64)
    
    for i, f in enumerate(freqs):
        if f < low_freq:
            # Low freq: +6dB boost
            eq_db[i] = 6.0
        elif f < mid_low:
            # Low-mid: +3dB taper
            eq_db[i] = 3.0 * (1 - (f - low_freq) / (mid_low - low_freq))
        elif f < mid_high:
            # Mid: -6dB cut
            eq_db[i] = -6.0
        elif f < high_freq:
            # High: taper to -12dB
            ratio = (f - mid_high) / (high_freq - mid_high)
            eq_db[i] = -6.0 - 6.0 * ratio
        else:
            # Very high: -12dB
            eq_db[i] = -12.0
    
    # Convert to linear gain
    eq_gain = 10 ** (eq_db / 20)
    
    # Apply FFT EQ
    y_fft = np.fft.rfft(y)
    y_fft *= eq_gain
    y_eq = np.fft.irfft(y_fft, n=len(y))
    
    # Additional lowpass filter for smoothness
    sos = signal.butter(2, 8000, 'low', fs=sr, output='sos')
    y_eq = signal.sosfiltfilt(sos, y_eq)
    
    # Soft limiting to prevent clipping
    max_val = np.max(np.abs(y_eq))
    if max_val > 0.95:
        y_eq = y_eq * 0.95 / max_val
    
    return y_eq.astype(np.float32)


def pitch_shift_octave(y, sr):
    """
    Use phase vocoder to shift pitch up by one octave (12 semitones)
    librosa uses high-quality phase vocoder algorithm
    """
    print(f"  Original: {len(y)} samples, {sr} Hz")
    
    # Use librosa's phase vocoder for pitch shift
    # n_steps=12 means one octave up
    y_shifted = librosa.effects.pitch_shift(
        y=y,
        sr=sr,
        n_steps=12,  # 12 semitones = 1 octave
        bins_per_octave=12,
        res_type='kaiser_best'  # Highest quality resampling
    )
    
    print(f"  After pitch shift: {len(y_shifted)} samples")
    return y_shifted


def process_audio(input_path, output_path):
    """
    Main processing pipeline
    """
    print(f"\n{'='*60}")
    print(f"Processing: {input_path}")
    print(f"{'='*60}")
    
    # Check input file
    if not os.path.exists(input_path):
        print(f"Error: File not found - {input_path}")
        return False
    
    # Load audio - use original sample rate for quality
    print("\n[1/4] Loading audio...")
    try:
        y, sr = librosa.load(input_path, sr=None, mono=False)
        print(f"  Sample rate: {sr} Hz")
        print(f"  Channels: {'Stereo' if y.ndim > 1 else 'Mono'}")
    except Exception as e:
        print(f"Error loading audio: {e}")
        return False
    
    # Process stereo channels separately
    if y.ndim > 1:
        print("\n[2/4] Processing left channel...")
        left_eq = apply_eq_low_boost(y[0], sr)
        left_shifted = pitch_shift_octave(left_eq, sr)
        
        print("\n[3/4] Processing right channel...")
        right_eq = apply_eq_low_boost(y[1], sr)
        right_shifted = pitch_shift_octave(right_eq, sr)
        
        # Merge channels
        y_processed = np.array([left_shifted, right_shifted])
    else:
        print("\n[2/4] Applying EQ...")
        y_eq = apply_eq_low_boost(y, sr)
        
        print("\n[3/4] Pitch shifting +8 degrees...")
        y_processed = pitch_shift_octave(y_eq, sr)
    
    # Ensure data is in [-1, 1] range
    print("\n[4/4] Finalizing...")
    if y_processed.ndim > 1:
        for ch in range(y_processed.shape[0]):
            max_val = np.max(np.abs(y_processed[ch]))
            if max_val > 1.0:
                y_processed[ch] = y_processed[ch] / max_val * 0.98
                print(f"  Channel {ch+1}: normalized (peak: {max_val:.3f})")
    else:
        max_val = np.max(np.abs(y_processed))
        if max_val > 1.0:
            y_processed = y_processed / max_val * 0.98
            print(f"  Normalized (peak: {max_val:.3f})")
    
    # Transpose for soundfile format (samples, channels)
    if y_processed.ndim > 1:
        y_processed = y_processed.T
    
    # Save output
    output_ext = Path(output_path).suffix.lower()
    
    if output_ext == '.wav':
        subtype = 'PCM_24'
        print(f"  Output: WAV 24-bit")
    elif output_ext in ['.mp3', '.m4a', '.aac']:
        temp_wav = output_path + '.temp.wav'
        sf.write(temp_wav, y_processed, sr, subtype='PCM_24')
        
        cmd = None
        if output_ext == '.mp3':
            cmd = f'ffmpeg -y -i "{temp_wav}" -codec:a libmp3lame -q:a 0 "{output_path}"'
            print(f"  Output: MP3 V0 (highest quality)")
        elif output_ext in ['.m4a', '.aac']:
            cmd = f'ffmpeg -y -i "{temp_wav}" -codec:a aac -b:a 320k "{output_path}"'
            print(f"  Output: AAC 320kbps")
        
        if cmd:
            os.system(cmd)
        os.remove(temp_wav)
        
        print(f"\n✓ Done! Output: {output_path}")
        return True
    else:
        subtype = 'PCM_24'
        print(f"  Output: WAV 24-bit (default)")
    
    # Write file
    sf.write(output_path, y_processed, sr, subtype=subtype)
    
    print(f"\n✓ Done! Output: {output_path}")
    
    # Show file info
    input_size = os.path.getsize(input_path) / (1024*1024)
    output_size = os.path.getsize(output_path) / (1024*1024)
    print(f"  Input size: {input_size:.2f} MB")
    print(f"  Output size: {output_size:.2f} MB")
    
    return True


def main():
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        print("Usage: python audio_processor.py <input_audio_file>")
        print("\nExample:")
        print("  python audio_processor.py song.mp3")
        sys.exit(1)
    
    # Generate output filename
    input_path = Path(input_file)
    output_file = input_path.parent / f"{input_path.stem}_processed{input_path.suffix}"
    
    # Run processing
    success = process_audio(str(input_file), str(output_file))
    
    if success:
        print(f"\n{'='*60}")
        print("Success!")
        print(f"{'='*60}")
    else:
        print(f"\n{'='*60}")
        print("Failed!")
        print(f"{'='*60}")
        sys.exit(1)


if __name__ == "__main__":
    main()
