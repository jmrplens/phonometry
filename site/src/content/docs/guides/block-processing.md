---
title: "Block Processing"
description: "Stateful streaming workflows with carried filter state."
---

The `OctaveFilterBank`, `WeightingFilter` (for A, C, or Z-weighting) and
`TimeWeighting` classes support block (streaming) processing: the internal
filter state is carried between calls, so concatenated block outputs match a
single full-signal pass.

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
  (`high_accuracy=False`); see [Frequency Weighting](/PyOctaveBand/guides/weighting/).

## Example

```python
import soundfile as sf
from pyoctaveband import OctaveFilterBank, WeightingFilter

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
from pyoctaveband import TimeWeighting

tw = TimeWeighting(fs, mode="fast")
for block in audio_blocks:
    envelope = tw.process(block)
```

Or manage the state yourself with the functional API — see
[Time Weighting](/PyOctaveBand/guides/time-weighting/#block-processing).

## Multichannel state

All stateful classes handle multichannel input `(channels, samples)`: the state
is allocated lazily on the first call to match the channel count, and reallocated
if the channel count changes (e.g. switching from stereo to mono resets the state).
