---
title: "Multichannel and Performance"
description: "Vectorized multichannel analysis and performance notes."
---

## Multichannel Support

PyOctaveBand natively supports multichannel signals (e.g., Stereo, 5.1,
Microphone Arrays) using **fully vectorized operations**. Input arrays of shape
`(N_channels, N_samples)` are processed in parallel, offering significant
performance gains over iterative loops.

<img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/signal_response_multichannel.png" width="80%">

*Simultaneous analysis of a Stereo signal: Left Channel (Pink Noise) vs Right
Channel (Log Sine Sweep).*

The convention is consistent across the whole library: time is always the
**last axis**. This applies to `octavefilter`, `OctaveFilterBank`,
`weighting_filter`, `time_weighting`, `leq`, `laeq`, `ln_levels` and
`spectrogram`.

```python
import numpy as np
from pyoctaveband import octavefilter

stereo = np.stack([left, right])          # (2, n_samples)
spl, freq = octavefilter(stereo, fs, fraction=3)
# spl has shape (2, n_bands): one row per channel
```

## Performance: Vectorization and caching

The `OctaveFilterBank` class is highly optimized for real-time and batch
processing. It uses NumPy vectorization to handle multichannel audio arrays
(e.g., 64-channel microphone arrays) without explicit Python loops, ensuring
maximum throughput.

```python
from pyoctaveband import OctaveFilterBank

bank = OctaveFilterBank(fs=48000, fraction=3, filter_type='butter')

# Access computed properties
# bank.freq (center), bank.freq_d (lower), bank.freq_u (upper), bank.sos (coefficients)

# Process multiple signals efficiently
for frame in stream:
    # detrend=True (default) removes DC offset to improve low-freq accuracy
    spl, freq = bank.filter(frame, detrend=True)
```

Additional performance notes:

- **Design cache**: `octavefilter()` reuses filter bank designs across calls
  with identical parameters (LRU cache, 32 entries), so calling it in a loop
  does not redesign the bank each time. `OctaveFilterBank` gives you explicit
  control over the design lifetime.
- **Multirate decimation**: low-frequency bands are filtered at a decimated
  rate, which is both faster and numerically more stable (see
  [Theory](/PyOctaveBand/reference/theory/)).
- **Optional numba**: the `impulse` time weighting kernel is JIT-compiled when
  numba is installed (`pip install PyOctaveBand[perf]`).
