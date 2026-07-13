<!-- Package -->
[![PyPI version](https://img.shields.io/pypi/v/phonometry?logo=pypi&logoColor=white)](https://pypi.org/project/phonometry/)
[![Python versions](https://img.shields.io/pypi/pyversions/phonometry?logo=python&logoColor=white)](https://pypi.org/project/phonometry/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/jmrplens/phonometry/blob/main/LICENSE)

<!-- Quality -->
[![CI](https://github.com/jmrplens/phonometry/actions/workflows/python-app.yml/badge.svg)](https://github.com/jmrplens/phonometry/actions/workflows/python-app.yml)
[![Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=jmrplens_phonometry&metric=alert_status)](https://sonarcloud.io/summary/overall?id=jmrplens_phonometry)
[![codecov](https://codecov.io/gh/jmrplens/phonometry/branch/main/graph/badge.svg)](https://codecov.io/gh/jmrplens/phonometry)

<!-- Citation & support -->
[![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.21215280-blue?logo=doi&logoColor=white)](https://doi.org/10.5281/zenodo.21215280)

# phonometry

> *phonometry* — the measurement of sound. Formerly published as **PyOctaveBand**.

Acoustic measurement toolkit for Python: fractional octave-band filter banks, frequency and time weighting, and sound level metrology — conformance-tested against **IEC 61260-1:2014 / ANSI S1.11-2004** (filters) and **IEC 61672-1:2013** (weighting and levels) class 1 tolerance limits.

<img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_type_comparison.svg" alt="Magnitude response comparison of the five filter architectures for the 1 kHz octave band, with a zoom at the -3 dB crossover" width="80%">

## ✨ Highlights

- 🎛️ 1/1, 1/3 and arbitrary fractional octave filter banks (stable SOS + multirate decimation)
- 🏗️ Five architectures: Butterworth, Chebyshev I/II, Elliptic, Bessel — all with −3 dB points on the ANSI band edges
- 🔊 A/C/Z frequency weighting within IEC 61672-1 class 1 tolerances
- ⏱️ Fast/Slow/Impulse time ballistics, `Leq`, `LAeq` and `L10/L50/L90` statistical levels
- 🗺️ Octave spectrogram (band levels over time) and zero-phase offline filtering
- 🧠 Loudness in sones three ways: Zwicker (ISO 532-1 Annex B validated), Moore-Glasberg stationary & time-varying (ISO 532-2/3) and Sottek Hearing Model (ECMA-418-2); DIN 45692 sharpness, ISO 226:2023 contours
- 🎻 Sound-quality metrics: ECMA-418-2 tonality (tu_HMS) and roughness (asper)
- 🗣️ Speech Transmission Index: STI and STIPA per IEC 60268-16 Ed. 5, with signal generator
- 🎯 Tone prominence (TNR/PR, ECMA-418-1), environmental Lden/Ldn (ISO 1996-1), IEC 61252 noise dose
- ↗️ Two-microphone sound intensity (IEC 61043) with ISO 9614-1 field indicators
- 🏛️ Room & building acoustics: swept-sine/MLS impulse responses (ISO 18233), EDT/T20/T30/C50/C80/Ts (ISO 3382-1/2), open-plan speech metrics (ISO 3382-3), field airborne + impact + façade insulation with R′w/DnT,w/L′nT,w/D2m,nT,w and C/Ctr/CI (ISO 16283-1/2/3, ISO 717-1/2), laboratory R/Ln (ISO 10140), flanking-transmission prediction of R′w/L′n,w (EN 12354-1/2), measurement uncertainty (ISO 12999-1), sound absorption (ISO 354)
- 🌬️ Outdoor propagation & occupational exposure: atmospheric absorption α(f) (ISO 9613-1), the ISO 9613-2 general method (divergence + atmospheric + ground + barrier terms) with a per-term octave-band breakdown, and daily noise exposure LEX,8h with task/job/full-day strategies and Annex C uncertainty (ISO 9612)
- 🔊 Sound power LW three ways: enveloping-surface pressure (ISO 3744/3746), reverberation-room precision with Waterhouse/C1/C2 (ISO 3741), intensity scanning with field indicators and grade (ISO 9614-2)
- 📏 Physical SPL calibration with IEC 60942:2017 stability validation, and dBFS modes
- ⚡ Vectorized multichannel processing and stateful block (real-time) workflows

## 🚀 Installation

```bash
pip install phonometry
```

Optional extras: `phonometry[plot]` (matplotlib for response plots and result `.plot()` methods), `phonometry[perf]` (numba for faster impulse ballistics), `phonometry[full]` (both).

## 📚 Documentation

**Full documentation website: https://jmrplens.github.io/phonometry/** (English / Español)

Or browse the Markdown docs on GitHub:

| Page | Contents |
| :--- | :--- |
| [Getting Started](https://github.com/jmrplens/phonometry/blob/main/docs/getting-started.md) | Installation, first analysis, WAV files |
| [Filter Banks](https://github.com/jmrplens/phonometry/blob/main/docs/filter-banks.md) | Architectures, response gallery, band decomposition, zero-phase |
| [Frequency Weighting](https://github.com/jmrplens/phonometry/blob/main/docs/weighting.md) | A/C/Z curves, class 1 high-accuracy mode |
| [Time Weighting](https://github.com/jmrplens/phonometry/blob/main/docs/time-weighting.md) | Fast/Slow/Impulse ballistics, initial state |
| [Levels](https://github.com/jmrplens/phonometry/blob/main/docs/levels.md) | Leq, LAeq, percentiles, LCpeak, SEL, noise dose (IEC 61252), Lden and rating levels (ISO 1996-1), octave spectrogram |
| [Occupational Exposure](https://github.com/jmrplens/phonometry/blob/main/docs/occupational-exposure.md) | ISO 9612 task-based, job-based and full-day strategies with the Annex C uncertainty budget (LEX,8h + U) |
| [Tone Prominence](https://github.com/jmrplens/phonometry/blob/main/docs/tone-prominence.md) | ECMA-418-1 tone-to-noise ratio and prominence ratio with frequency-dependent prominence criteria |
| [Psychoacoustics](https://github.com/jmrplens/phonometry/blob/main/docs/psychoacoustics.md) | Zwicker (ISO 532-1), Moore-Glasberg (ISO 532-2/3) and Sottek (ECMA-418-2) loudness, sharpness (DIN 45692), equal-loudness contours (ISO 226), tonality & roughness (ECMA-418-2) |
| [Speech Transmission](https://github.com/jmrplens/phonometry/blob/main/docs/speech-transmission.md) | STI/STIPA (IEC 60268-16): modulation transfer function, indirect method from impulse responses and direct STIPA measurement |
| [Speech Intelligibility Index](https://github.com/jmrplens/phonometry/blob/main/docs/speech-intelligibility.md) | SII (ANSI S3.5-1997): band importance, masking and audibility, the index in noise and hearing loss, standard vocal-effort spectra |
| [Electroacoustics](https://github.com/jmrplens/phonometry/blob/main/docs/electroacoustics.md) | Distortion (IEC 60268-3): THD, nth-order harmonic, THD+N & SINAD (AES17), SMPTE & CCIF intermodulation, DIM and weighted THD; frequency response & coherence (Bendat & Piersol H1/H2) |
| [Underwater Acoustics](https://github.com/jmrplens/phonometry/blob/main/docs/underwater-acoustics.md) | Reference levels re 1 µPa (SPL, SEL, peak; ISO 18405); ship radiated noise & equivalent monopole source level (ISO 17208); pile-driving single-strike, peak & cumulative SEL (ISO 18406) |
| [Underwater Sound Propagation](https://github.com/jmrplens/phonometry/blob/main/docs/underwater-propagation.md) | Transmission loss (geometrical spreading + volume absorption: Francois-Garrison, Ainslie-McColm, Thorp); speed of sound in sea water (UNESCO/Chen-Millero, Del Grosso, Mackenzie); passive & active sonar equation; seabed reflection loss (Rayleigh); ocean ambient noise (Wenz wind/thermal + JOMOPANS-ECHO ship traffic); numerical solvers (normal modes, ray tracing, parabolic equation) |
| [Aircraft Noise](https://github.com/jmrplens/phonometry/blob/main/docs/aircraft-noise.md) | Effective Perceived Noise Level (ICAO Annex 16): perceived noisiness & PNL, tone correction, 10 dB-down duration correction (EPNL); IEC 61265 measurement-system verification; SAE ARP 5534 one-third-octave-band atmospheric absorption |
| [Wind-Turbine Noise](https://github.com/jmrplens/phonometry/blob/main/docs/wind-turbine-noise.md) | Apparent sound power level referred to the rotor centre and tonal audibility (Zwicker critical band, masking-noise level, audibility criterion) — IEC 61400-11 |
| [Sound Intensity](https://github.com/jmrplens/phonometry/blob/main/docs/intensity.md) | Two-microphone p-p intensity (IEC 61043), ISO 9614-1 field indicators |
| [Room Acoustics](https://github.com/jmrplens/phonometry/blob/main/docs/room-acoustics.md) | Impulse responses (ISO 18233), room parameters (ISO 3382-1/2), open-plan metrics (ISO 3382-3), sound absorption (ISO 354) |
| [Building Acoustics](https://github.com/jmrplens/phonometry/blob/main/docs/building-acoustics.md) | Field airborne + impact + façade insulation and weighted ratings (ISO 16283-1/2/3, ISO 717-1/2), laboratory characterisation (ISO 10140), flanking-transmission prediction (EN 12354-1/2), measurement uncertainty (ISO 12999-1) |
| [Outdoor Sound Propagation](https://github.com/jmrplens/phonometry/blob/main/docs/outdoor-propagation.md) | Atmospheric absorption α(f) (ISO 9613-1) and the ISO 9613-2 general method: geometrical divergence, atmospheric absorption, ground effect, barrier screening and meteorological correction |
| [Sound Power](https://github.com/jmrplens/phonometry/blob/main/docs/sound-power.md) | Sound power level LW by enveloping surface (ISO 3744/3746), reverberation room (ISO 3741) and intensity scanning (ISO 9614-2) |
| [Calibration and dBFS](https://github.com/jmrplens/phonometry/blob/main/docs/calibration.md) | Physical SPL, digital full-scale, RMS vs peak |
| [Block Processing](https://github.com/jmrplens/phonometry/blob/main/docs/block-processing.md) | Stateful streaming workflows |
| [Multichannel](https://github.com/jmrplens/phonometry/blob/main/docs/multichannel.md) | Vectorized multichannel analysis, performance |
| [API Reference](https://github.com/jmrplens/phonometry/blob/main/docs/api-reference.md) | Every public function and class |
| [Theory](https://github.com/jmrplens/phonometry/blob/main/docs/theory.md) | Standards, math, design decisions |
| [Why phonometry](https://github.com/jmrplens/phonometry/blob/main/docs/why-phonometry.md) | IEC compliance verification vs other libraries |
| [Conformance report](https://github.com/jmrplens/phonometry/blob/main/docs/CONFORMANCE.md) | Live per-standard numerical validation (expected vs computed) regenerated by `make conformance` |

## ⚡ Quick start

```python
import numpy as np
from phonometry import octave_filter

fs = 48000
t = np.linspace(0, 1, fs, endpoint=False)
# Composite signal: 100Hz + 1000Hz
signal = np.sin(2 * np.pi * 100 * t) + np.sin(2 * np.pi * 1000 * t)

# Apply 1/3 octave filter bank
spl, freq = octave_filter(signal, fs=fs, fraction=3)

print(f"Bands: {freq}")
print(f"SPL [dB]: {spl}")
```

<img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_response_fraction_3.svg" alt="One-third-octave spectrum analysis of a multi-tone signal with the raw PSD in the background" width="80%">

*1/3 Octave Band spectrum analysis of a complex signal. More examples in the
[documentation](https://jmrplens.github.io/phonometry/).*

## 🧪 Development

```bash
make install   # dependencies + editable install
make check     # ruff + mypy + bandit + tests
make graphs    # regenerate documentation images
```

See https://github.com/jmrplens/phonometry/blob/main/CONTRIBUTING.md and the
https://github.com/jmrplens/phonometry/blob/main/CHANGELOG.md

## 📄 License

[MIT](https://github.com/jmrplens/phonometry/blob/main/LICENSE)
