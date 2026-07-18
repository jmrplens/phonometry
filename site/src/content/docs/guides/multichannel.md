---
title: "Multichannel and Performance"
description: "Vectorized multichannel analysis and performance notes."
references:
  - type: standard
    organization: "International Electrotechnical Commission"
    year: 2014
    title: "Electroacoustics — Octave-band and fractional-octave-band filters — Part 1: Specifications"
    designation: "IEC 61260-1:2014"
    url: "https://webstore.iec.ch/en/publication/5063"
    note: "The band definitions each channel is filtered with; the multichannel path batches them unchanged. Multichannel support adds no normative content of its own: each channel is filtered exactly as the single-channel standard prescribes, and the vectorization only batches the computation across the channel axis."
  - type: standard
    organization: "International Electrotechnical Commission"
    year: 2013
    title: "Electroacoustics — Sound level meters — Part 1: Specifications"
    designation: "IEC 61672-1:2013"
    url: "https://webstore.iec.ch/en/publication/5708"
    note: "The weighting and time-integration semantics applied per channel, exactly as the single-channel standard prescribes."
---

## Multichannel Support

phonometry natively supports multichannel signals (e.g., Stereo, 5.1,
Microphone Arrays) using **fully vectorized operations**. Input arrays of shape
`(N_channels, N_samples)` are processed in parallel, offering significant
performance gains over iterative loops.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_response_multichannel.svg" alt="Stereo analysis: pink noise and logarithmic sweep resolved per channel in one-third-octave bands" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_response_multichannel_dark.svg" alt="Stereo analysis: pink noise and logarithmic sweep resolved per channel in one-third-octave bands" style="width:80%">

*Simultaneous analysis of a Stereo signal: Left Channel (Pink Noise) vs Right
Channel (Log Sine Sweep).*

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import chirp
from phonometry import metrology

# Stereo test signal: pink noise left, logarithmic sine sweep right
fs, duration = 48000, 5
t = np.linspace(0, duration, fs * duration, endpoint=False)
rng = np.random.default_rng(42)
spec = np.fft.rfft(rng.standard_normal(t.size))
spec[1:] /= np.sqrt(np.arange(1, spec.size))   # 1/f shaping: pink noise
left = np.fft.irfft(spec, t.size)
right = chirp(t, f0=50, t1=duration, f1=10000, method="logarithmic")

x = np.stack([left, right])                    # (2, n_samples)
spl, freq = metrology.octave_filter(x, fs, fraction=3, limits=[20, 20000])

fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
for ax, levels, name in zip(axes, spl, ["Left: pink noise", "Right: log sweep"]):
    ax.semilogx(freq, levels, marker="o", label=name)
    ax.set_ylabel("Level [dB]")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
axes[-1].set_xlabel("Frequency [Hz]")
plt.show()
```

</details>

The convention is consistent across the whole library: time is always the
**last axis**. This applies to `octave_filter`, `OctaveFilterBank`,
`weighting_filter`, `time_weighting`, `leq`, `laeq`, `ln_levels` and
`spectrogram`.

```python
import numpy as np
from phonometry import metrology

# Two calibrated channels in Pa so the guide runs standalone
fs = 48000
t = np.arange(fs) / fs
left = 0.2 * np.sin(2 * np.pi * 1000 * t)
right = 0.1 * np.sin(2 * np.pi * 500 * t)

stereo = np.stack([left, right])          # (2, n_samples)
spl, freq = metrology.octave_filter(stereo, fs, fraction=3)
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

## Per-channel semantics

Multichannel processing is strictly per channel: nothing is ever mixed,
summed or averaged across the channel axis. Three consequences worth
spelling out:

- **Combining channels is your decision.** Levels come back one per
  channel. If you need an array-average level (for instance the
  position-averaged levels of the room-acoustics standards), combine
  energies yourself: `10 * np.log10(np.mean(10 ** (spl / 10), axis=0))`,
  never the arithmetic mean of the dB values (see
  [Levels](/phonometry/guides/levels/) for why).
- **One `calibration_factor` means one sensitivity.** The scalar factor
  multiplies every channel, which is correct only if all channels share the
  same sensitivity. For an array of microphones with individual
  calibrations, scale the rows first, `x * factors[:, None]`, and leave
  `calibration_factor` at 1.
- **Stateful classes keep one state per channel.** In block processing the
  state array matches the channel count and a change of channel count
  resets it; see [Block Processing](/phonometry/guides/block-processing/).

## Performance: Vectorization and caching

The `OctaveFilterBank` class is highly optimized for real-time and batch
processing. It uses NumPy vectorization to handle multichannel audio arrays
(e.g., 64-channel microphone arrays) without explicit Python loops, ensuring
maximum throughput.

```python
import numpy as np
from phonometry import metrology

# Two calibrated channels in Pa so the guide runs standalone
fs = 48000
t = np.arange(fs) / fs
left = 0.2 * np.sin(2 * np.pi * 1000 * t)
right = 0.1 * np.sin(2 * np.pi * 500 * t)
stereo = np.stack([left, right])          # (2, n_samples)

bank = metrology.OctaveFilterBank(fs=48000, fraction=3, filter_type='butter')

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
  [Theory](/phonometry/reference/theory/signal-analysis/)).
- **Optional numba**: the `impulse` time weighting kernel is JIT-compiled when
  numba is installed (`pip install phonometry[perf]`).

## See also

- API reference: [`phonometry`](/phonometry/reference/api/filters/phonometry/) and [`metrology.core`](/phonometry/reference/api/filters/core/).
