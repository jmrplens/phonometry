---
title: "Multichannel and Performance"
description: "Vectorized multichannel analysis and performance notes."
---

## Multichannel Support

phonometry natively supports multichannel signals (e.g., Stereo, 5.1,
Microphone Arrays) using **fully vectorized operations**. Input arrays of shape
`(N_channels, N_samples)` are processed in parallel, offering significant
performance gains over iterative loops.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_response_multichannel.svg" alt="Stereo analysis: pink noise and logarithmic sweep resolved per channel in one-third-octave bands" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_response_multichannel_dark.svg" alt="Stereo analysis: pink noise and logarithmic sweep resolved per channel in one-third-octave bands" style="width:80%">

*Simultaneous analysis of a Stereo signal: Left Channel (Pink Noise) vs Right
Channel (Log Sine Sweep).*

The convention is consistent across the whole library: time is always the
**last axis**. This applies to `octave_filter`, `OctaveFilterBank`,
`weighting_filter`, `time_weighting`, `leq`, `laeq`, `ln_levels` and
`spectrogram`.

```python
import numpy as np
from phonometry import octave_filter

# Two calibrated channels in Pa so the guide runs standalone
fs = 48000
t = np.arange(fs) / fs
left = 0.2 * np.sin(2 * np.pi * 1000 * t)
right = 0.1 * np.sin(2 * np.pi * 500 * t)

stereo = np.stack([left, right])          # (2, n_samples)
spl, freq = octave_filter(stereo, fs, fraction=3)
# spl has shape (2, n_bands): one row per channel
```

## Accepted shapes, at a glance

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_multichannel.svg" alt="Array-shape flow: a 1-D (samples,) input reduces to a scalar and a 2-D (channels, samples) input reduces to (channels,), because the operation runs along the last axis while the channel axis is preserved" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_multichannel_dark.svg" alt="Array-shape flow: a 1-D (samples,) input reduces to a scalar and a 2-D (channels, samples) input reduces to (channels,), because the operation runs along the last axis while the channel axis is preserved" style="width:80%">

| Input | Interpreted as | Typical output |
| :--- | :--- | :--- |
| `(n,)` 1D array | one channel | scalar level / `(bands,)` |
| `(ch, n)` 2D array | `ch` channels, `n` samples each | `(ch,)` levels / `(ch, bands)` |
| list of floats | one channel (converted) | as 1D |
| `(ch, n)` into `spectrogram` | multichannel STFT-style | `(ch, bands, frames)` |

Everything vectorizes across the leading channel axis — one filter design is
applied to all channels in a single SciPy call, so 8 channels cost far less
than 8 separate runs. Convention: **channels first**, like most DSP code
(`soundfile` returns `(n, ch)`: transpose with `x.T`).

## Performance: Vectorization and caching

The `OctaveFilterBank` class is highly optimized for real-time and batch
processing. It uses NumPy vectorization to handle multichannel audio arrays
(e.g., 64-channel microphone arrays) without explicit Python loops, ensuring
maximum throughput.

```python
from phonometry import OctaveFilterBank

bank = OctaveFilterBank(fs=48000, fraction=3, filter_type='butter')

# Access computed properties
# bank.freq (center), bank.freq_d (lower), bank.freq_u (upper), bank.sos (coefficients)

# Process multiple signals efficiently
stream = [stereo]                 # your sequence of multichannel frames
for frame in stream:
    # detrend=True (default) removes DC offset to improve low-freq accuracy
    spl, freq = bank.filter(frame, detrend=True)
```

Additional performance notes:

- **Design cache**: `octave_filter()` reuses filter bank designs across calls
  with identical parameters (LRU cache, 32 entries), so calling it in a loop
  does not redesign the bank each time. `OctaveFilterBank` gives you explicit
  control over the design lifetime.
- **Multirate decimation**: low-frequency bands are filtered at a decimated
  rate, which is both faster and numerically more stable (see
  [Theory](/phonometry/reference/theory/)).
- **Optional numba**: the `impulse` time weighting kernel is JIT-compiled when
  numba is installed (`pip install phonometry[perf]`).

## See also

- API reference: [`phonometry`](/phonometry/reference/api/filters/phonometry/) and [`metrology.core`](/phonometry/reference/api/filters/core/).
