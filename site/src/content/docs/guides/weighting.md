---
title: "Frequency Weighting (A, C, Z)"
description: "IEC 61672-1 frequency weighting curves with class 1 high-frequency accuracy."
---

Frequency weighting curves simulate the human ear's sensitivity, as specified by
**IEC 61672-1:2013**.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_responses.png" alt="A, C and Z frequency weighting curves with a zoom showing the positive region of the A curve (+1.27 dB at 2.5 kHz)" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_responses_dark.png" alt="A, C and Z frequency weighting curves with a zoom showing the positive region of the A curve (+1.27 dB at 2.5 kHz)" style="width:80%">

* **A-Weighting (`A`):** Standard for environmental noise (IEC 61672-1).
* **C-Weighting (`C`):** Used for peak sound pressure and high-level noise.
* **Z-Weighting (`Z`):** Zero weighting, completely flat response.

```python
from phonometry import weighting_filter

# Apply A-weighting to the raw signal
weighted_signal = weighting_filter(signal, fs, curve='A')

# Apply C-weighting for peak analysis
c_weighted_signal = weighting_filter(signal, fs, curve='C')
```

## Reusable filter object

If you weight many signals with the same parameters, design the filter once:

```python
from phonometry import WeightingFilter

wf = WeightingFilter(fs, "A")
for signal in signals:
    weighted = wf.filter(signal)
```

## High-frequency accuracy (`high_accuracy`)

A plain bilinear-transform design compresses the response near Nyquist: at
fs = 48 kHz the A-curve error at 12.5 kHz reaches −2.7 dB, outside the IEC
61672-1 **class 1** tolerance (+2.0/−2.5 dB).

By default (`high_accuracy=True`), phonometry designs and runs the weighting
filter at an internally oversampled rate (≥ 96 kHz) and decimates back, keeping
the response within class 1 tolerances up to 16 kHz (error ≈ −0.5 dB at
12.5 kHz for fs = 48 kHz).

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_accuracy_hf.png" alt="A-weighting high-frequency accuracy at 48 kHz: analytic curve versus plain bilinear versus oversampled design, with error subplot" style="width:80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/weighting_accuracy_hf_dark.png" alt="A-weighting high-frequency accuracy at 48 kHz: analytic curve versus plain bilinear versus oversampled design, with error subplot" style="width:80%">

*The plain bilinear design (red) crosses the class 1 tolerance near 12.5 kHz;
the oversampled design (blue) stays close to the analytic curve.*

- `high_accuracy=False` restores the legacy plain-bilinear behavior.
- **Stateful (block) processing** always uses the legacy design: the internal
  FIR resampling is incompatible with block continuity. Passing
  `high_accuracy=True` together with `stateful=True` raises a `ValueError`.

```python
# Explicit legacy behavior
y = weighting_filter(signal, fs, curve="A", high_accuracy=False)

# Stateful block processing (legacy design, state carried between blocks)
wf = WeightingFilter(fs, "A", stateful=True)
for block in blocks:
    weighted = wf.filter(block)
```

See [Block Processing](/phonometry/guides/block-processing/) for the streaming workflow and
[Theory](/phonometry/reference/theory/) for the analytic curve definitions.
