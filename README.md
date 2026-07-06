<!-- Package -->
[![PyPI version](https://img.shields.io/pypi/v/PyOctaveBand?logo=pypi&logoColor=white)](https://pypi.org/project/PyOctaveBand/)
[![Python versions](https://img.shields.io/pypi/pyversions/PyOctaveBand?logo=python&logoColor=white)](https://pypi.org/project/PyOctaveBand/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/jmrplens/PyOctaveBand/blob/main/LICENSE)

<!-- Quality -->
[![CI](https://github.com/jmrplens/PyOctaveBand/actions/workflows/python-app.yml/badge.svg)](https://github.com/jmrplens/PyOctaveBand/actions/workflows/python-app.yml)
[![Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=jmrplens_PyOctaveBand&metric=alert_status)](https://sonarcloud.io/summary/overall?id=jmrplens_PyOctaveBand)
[![codecov](https://codecov.io/gh/jmrplens/PyOctaveBand/branch/main/graph/badge.svg)](https://codecov.io/gh/jmrplens/PyOctaveBand)

<!-- Citation & support -->
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.21215280-blue?logo=doi&logoColor=white)](https://doi.org/10.5281/zenodo.21215280)

# PyOctaveBand

Advanced Octave-Band and Fractional Octave-Band filter bank for signals in the time domain. Fully compliant with **ANSI S1.11-2004** (Filters) and **IEC 61672-1:2013** (Weighting).

<img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_type_comparison.png" alt="Magnitude response comparison of the five filter architectures for the 1 kHz octave band, with a zoom at the -3 dB crossover" width="80%">

## ✨ Highlights

- 🎛️ 1/1, 1/3 and arbitrary fractional octave filter banks (stable SOS + multirate decimation)
- 🏗️ Five architectures: Butterworth, Chebyshev I/II, Elliptic, Bessel — all with −3 dB points on the ANSI band edges
- 🔊 A/C/Z frequency weighting within IEC 61672-1 class 1 tolerances
- ⏱️ Fast/Slow/Impulse time ballistics, `Leq`, `LAeq` and `L10/L50/L90` statistical levels
- 🗺️ Octave spectrogram (band levels over time) and zero-phase offline filtering
- 📏 Physical SPL calibration and dBFS modes
- ⚡ Vectorized multichannel processing and stateful block (real-time) workflows

## 🚀 Installation

```bash
pip install PyOctaveBand
```

Optional extras: `PyOctaveBand[plot]` (matplotlib for response plots), `PyOctaveBand[perf]` (numba for faster impulse ballistics), `PyOctaveBand[full]` (both).

## 📚 Documentation

**Full documentation website: https://jmrplens.github.io/PyOctaveBand/** (English / Español)

Or browse the Markdown docs on GitHub:

| Page | Contents |
| :--- | :--- |
| [Getting Started](https://github.com/jmrplens/PyOctaveBand/blob/main/docs/getting-started.md) | Installation, first analysis, WAV files |
| [Filter Banks](https://github.com/jmrplens/PyOctaveBand/blob/main/docs/filter-banks.md) | Architectures, response gallery, band decomposition, zero-phase |
| [Frequency Weighting](https://github.com/jmrplens/PyOctaveBand/blob/main/docs/weighting.md) | A/C/Z curves, class 1 high-accuracy mode |
| [Time Weighting](https://github.com/jmrplens/PyOctaveBand/blob/main/docs/time-weighting.md) | Fast/Slow/Impulse ballistics, initial state |
| [Levels](https://github.com/jmrplens/PyOctaveBand/blob/main/docs/levels.md) | Leq, LAeq, L10/L50/L90, octave spectrogram |
| [Calibration and dBFS](https://github.com/jmrplens/PyOctaveBand/blob/main/docs/calibration.md) | Physical SPL, digital full-scale, RMS vs peak |
| [Block Processing](https://github.com/jmrplens/PyOctaveBand/blob/main/docs/block-processing.md) | Stateful streaming workflows |
| [Multichannel](https://github.com/jmrplens/PyOctaveBand/blob/main/docs/multichannel.md) | Vectorized multichannel analysis, performance |
| [API Reference](https://github.com/jmrplens/PyOctaveBand/blob/main/docs/api-reference.md) | Every public function and class |
| [Theory](https://github.com/jmrplens/PyOctaveBand/blob/main/docs/theory.md) | Standards, math, design decisions |
| [Why PyOctaveBand](https://github.com/jmrplens/PyOctaveBand/blob/main/docs/why-pyoctaveband.md) | IEC compliance verification vs other libraries |

## ⚡ Quick start

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

<img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/signal_response_fraction_3.png" alt="One-third-octave spectrum analysis of a multi-tone signal with the raw PSD in the background" width="80%">

*1/3 Octave Band spectrum analysis of a complex signal. More examples in the
[documentation](https://jmrplens.github.io/PyOctaveBand/).*

## 🧪 Development

```bash
make install   # dependencies + editable install
make check     # ruff + mypy + bandit + tests
make graphs    # regenerate documentation images
```

See https://github.com/jmrplens/PyOctaveBand/blob/main/CONTRIBUTING.md and the
https://github.com/jmrplens/PyOctaveBand/blob/main/CHANGELOG.md

## 📄 License

[MIT](https://github.com/jmrplens/PyOctaveBand/blob/main/LICENSE)
