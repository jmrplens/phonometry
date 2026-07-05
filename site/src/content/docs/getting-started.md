---
title: "Getting Started"
description: "Install PyOctaveBand and run your first fractional octave analysis."
---

## Installation

**Option 1: From PyPI (Recommended)**

```bash
pip install PyOctaveBand
```

Optional extras:

```bash
pip install PyOctaveBand[plot]   # matplotlib, for filter response plots
pip install PyOctaveBand[perf]  # numba, faster 'impulse' time weighting
pip install PyOctaveBand[full]  # both
```

**Option 2: Cloning and Installing**

```bash
git clone https://github.com/jmrplens/PyOctaveBand.git
cd PyOctaveBand
pip install .
```

**Option 3: Git Submodule**

```bash
git submodule add https://github.com/jmrplens/PyOctaveBand.git
# Then install in editable mode to use it from your project
pip install -e ./PyOctaveBand
```

## Basic Usage: 1/3 Octave Analysis

Analyze a signal and get the Sound Pressure Level (SPL) per frequency band.

```python
import numpy as np
from pyoctaveband import octavefilter

fs = 48000
t = np.linspace(0, 1, fs, endpoint=False)
# Composite signal: 100Hz + 1000Hz
signal = np.sin(2 * np.pi * 100 * t) + np.sin(2 * np.pi * 1000 * t)

# Apply 1/3 octave filter bank
spl, freq = octavefilter(signal, fs=fs, fraction=3)

print(f"Bands: {freq}")
print(f"SPL [dB]: {spl}")
```

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/signal_response_fraction_3.png" width="80%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/signal_response_fraction_3_dark.png" width="80%">

*Example of a 1/3 Octave Band spectrum analysis of a complex signal.*

## Analyzing an audio file

```python
from scipy.io import wavfile
from pyoctaveband import octavefilter

# Load standard WAV file
fs, signal = wavfile.read("measurement.wav")

# Analyze
# Note: To obtain real-world SPL values, you must calibrate the input.
# See the Calibration guide.
spl, freq = octavefilter(signal, fs=fs, fraction=3)
```

Integer audio (e.g. int16 WAV data) is converted to float64 internally, so it is
safe to pass `wavfile.read` output directly.

## Where to go next

- [Filter Banks](/PyOctaveBand/guides/filter-banks/) — choose an architecture and inspect responses
- [Calibration and dBFS](/PyOctaveBand/guides/calibration/) — get real-world SPL values
- [API Reference](/PyOctaveBand/reference/api/) — every parameter of every function
