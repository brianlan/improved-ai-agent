# EQ Curve Documentation

## Default EQ Curve for Bass Boost

This skill applies a specific EQ curve designed to emphasize low frequencies while reducing mid and high frequencies.

### Frequency Response

```
Frequency (Hz)    |    Gain (dB)    |    Description
------------------|-----------------|------------------
0 - 200           |    +6.0         |    Strong bass boost
200 - 400         |    +3.0 to 0    |    Low-mid taper
400 - 2000        |    -6.0         |    Mid cut
2000 - 6000       |    -6 to -12    |    High-mid taper
6000+             |    -12.0        |    High cut
```

### Visual Representation

```
Gain (dB)
   +
 6 |        ____
   |       /    \
 3 |      /      \
   |     /        \
 0 |____/          \____
   |                     \
-6 |      ____________    \
   |     /            \\    \
-12|____/              \\____\____
   |
   +----+----+----+----+----+----+----> Frequency (Hz)
        200  400  1k   2k   4k   6k   10k
```

### Use Cases

1. **Guitar Processing**: Makes guitar sound fuller and warmer
2. **Voice Recording**: Reduces harshness, adds warmth
3. **Music Remix**: Creates "telephone" or "lo-fi" effect with bass emphasis
4. **Sample Preparation**: Pre-processing for specific genres (lo-fi, ambient)

### Technical Implementation

The EQ is implemented using FFT-based filtering:

1. **FFT Transform**: Convert signal to frequency domain
2. **Gain Application**: Multiply each frequency bin by calculated gain
3. **IFFT Transform**: Convert back to time domain
4. **Butterworth Filter**: Additional 8kHz lowpass for smoothness

### Customization

To modify the EQ curve, edit the `apply_eq_low_boost()` function in `audio_processor.py`:

```python
# Adjust these values for different curves
low_freq = 200      # Bass boost cutoff
mid_low = 400       # Low-mid range end
mid_high = 2000     # Mid cut range end
high_freq = 6000    # High cut range end

# Adjust dB values
eq_db[i] = 6.0      # Bass boost amount
eq_db[i] = -6.0     # Mid cut amount
eq_db[i] = -12.0    # High cut amount
```
