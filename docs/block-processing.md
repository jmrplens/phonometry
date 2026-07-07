← [Documentation index](README.md)

# Block Processing

The `OctaveFilterBank`, `WeightingFilter` (for A, C, or Z-weighting) and
`TimeWeighting` classes support block (streaming) processing: the internal
filter state is carried between calls, so concatenated block outputs match a
single full-signal pass.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/block_processing_continuity_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/block_processing_continuity.png" alt="Stateful block processing matching the continuous result versus independent blocks restarting the filter transient at each boundary" width="80%"></picture>

*With `stateful=True` the concatenated block outputs match the continuous
result exactly; without state, every block boundary restarts the filter
transient.*

Create a stateful filter bank with `stateful=True`. The internal state is
zero-initialized by default but may be initialized for step-response
steady-state (like `scipy.signal.sosfilt_zi`) with `steady_ic=True`.

Notes when using a stateful `OctaveFilterBank`:

- Detrending should be disabled during block processing (`detrend=False`), as it
  can introduce discontinuities between blocks.
- Resampling is not supported for block processing, so you need to set
  `resample=False`.
- `zero_phase=True` is incompatible with stateful mode (forward-backward
  filtering needs the whole signal).
- Stateful `WeightingFilter` uses the legacy bilinear design
  (`high_accuracy=False`); see [Frequency Weighting](weighting.md).

## Example

This example streams a WAV file with [`soundfile`](https://pysoundfile.readthedocs.io/),
an optional dependency (`pip install soundfile`). Any block source works just as
well — `scipy.io.wavfile` plus manual slicing, or a live capture callback.

```python
import soundfile as sf
from phonometry import OctaveFilterBank, WeightingFilter

fs = 48000
octavefilter = OctaveFilterBank(fs, 1, stateful=True, resample=False)
afilter = WeightingFilter(fs, "A", stateful=True)

for block in sf.blocks("measurement.wav", blocksize=256, overlap=0):

    # Apply A-filter
    weighted = afilter.filter(block)

    # Split into octave bands
    block_spl, _, block_output = octavefilter.filter(weighted, sigbands=True, detrend=False)

    # further signal processing
    ...
```

## Time weighting across blocks

Use the `TimeWeighting` class (state carried automatically):

```python
from phonometry import TimeWeighting

tw = TimeWeighting(fs, mode="fast")
# audio_blocks: successive frames of your microphone recording (Pa),
#   e.g. from sf.blocks("measurement.wav", ...) as in the block above.
for block in audio_blocks:
    envelope = tw.process(block)
```

Or manage the state yourself with the functional API — see
[Time Weighting](time-weighting.md#block-processing).

## Multichannel state

All stateful classes handle multichannel input `(channels, samples)`: the state
is allocated lazily on the first call to match the channel count, and reallocated
if the channel count changes (e.g. switching from stereo to mono resets the state).

## Real-time level meter pattern

The canonical streaming loop — weight, envelope and report block by block
with all state carried across calls:

```python
import numpy as np
from phonometry import TimeWeighting, WeightingFilter

fs, block = 48000, 4800  # 100 ms blocks
aw = WeightingFilter(fs, "A", stateful=True)
env = TimeWeighting(fs, mode="fast")  # the class is inherently stateful

for x in audio_stream(block):            # your capture callback
    y = env.process(aw.filter(x))
    spl = 10 * np.log10(y[..., -1] / (2e-5) ** 2)  # instantaneous LAF
    display(spl)
```

### Stateful-mode constraints

| Option | Stateful behavior | Why |
| :--- | :--- | :--- |
| `detrend` | must be `False` | Per-block detrending creates boundary discontinuities |
| `resample` | must be `False` | The resampler is not stateful |
| `zero_phase` | unsupported | Forward-backward filtering needs the whole signal |
| `high_accuracy` (weighting) | resolves to `False` by default; explicitly passing `True` raises `ValueError` | The polyphase resampling inside is block-incompatible |
| `steady_ic` | optional | Starts the filters in step-response steady state |
