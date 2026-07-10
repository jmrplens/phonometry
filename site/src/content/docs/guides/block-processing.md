---
title: "Block Processing"
description: "Stateful streaming workflows with carried filter state."
---

Some measurements never fit in memory: an hour-long environmental recording,
a live monitor that must report levels while the microphone is still
capturing, or an embedded logger that only ever sees one buffer at a time. In
all of these the signal has to be processed block by block — and the filters
must behave exactly as if they had seen the whole signal at once.

The `OctaveFilterBank`, `WeightingFilter` (for A, C, or Z-weighting) and
`TimeWeighting` classes support block (streaming) processing: the internal
filter state is carried between calls, so concatenated block outputs match a
single full-signal pass.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_block_processing.svg" alt="Two lanes comparing block processing with the filter state carried across blocks, giving one continuous envelope, versus reset each block, where the envelope restarts from zero at every seam" style="width:86%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_block_processing_dark.svg" alt="Two lanes comparing block processing with the filter state carried across blocks, giving one continuous envelope, versus reset each block, where the envelope restarts from zero at every seam" style="width:86%">

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/block_processing_continuity.png" alt="Stateful block processing matching the continuous result versus independent blocks restarting the filter transient at each boundary" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/block_processing_continuity_dark.png" alt="Stateful block processing matching the continuous result versus independent blocks restarting the filter transient at each boundary" style="width:80%">

*With `stateful=True` the concatenated block outputs match the continuous
result exactly; without state, every block boundary restarts the filter
transient.*

Create a stateful filter bank with `stateful=True`. The internal state is
zero-initialized by default but may be initialized for step-response
steady-state (like `scipy.signal.sosfilt_zi`) with `steady_ic=True`. The
options that must be disabled in stateful mode are summarized in the
[constraints table](#stateful-mode-constraints) at the end of this guide.

## Example

This example streams a WAV file with [`soundfile`](https://pysoundfile.readthedocs.io/),
an optional dependency (`pip install soundfile`). Any block source works just as
well — `scipy.io.wavfile` plus manual slicing, or a live capture callback.

```python
import soundfile as sf
from phonometry import OctaveFilterBank, WeightingFilter

fs = 48000
octave_filter = OctaveFilterBank(fs, 1, stateful=True, resample=False)
afilter = WeightingFilter(fs, "A", stateful=True)

for block in sf.blocks("measurement.wav", blocksize=256, overlap=0):

    # Apply A-filter
    weighted = afilter.filter(block)

    # Split into octave bands
    block_spl, _, block_output = octave_filter.filter(weighted, sigbands=True, detrend=False)

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
[Time Weighting](/phonometry/guides/time-weighting/#6-block-processing).

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
| `high_accuracy` (weighting) | resolves to `False` by default — the legacy bilinear design, see [Frequency Weighting](/phonometry/guides/weighting/); explicitly passing `True` raises `ValueError` | The polyphase resampling inside is block-incompatible |
| `steady_ic` | optional | Starts the filters in step-response steady state |
