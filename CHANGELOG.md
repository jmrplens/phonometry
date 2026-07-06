# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### ⚠️ Numerical behavior changes

Results differ from 1.2.x for the following cases — all of them bring the
output in line with the governing standards:

- **Chebyshev II banks** now place their −3 dB points on the ANSI S1.11 band
  edges. Previously the band edges received the full stopband `attenuation`
  (−60 dB by default), underestimating broadband band levels by ~2.8 dB
  vs Butterworth. ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))
- **Bessel banks** are designed with `norm="mag"`: −3 dB lands on the band
  edges (previously ~−10 dB, a ~2.2 dB broadband error). ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))
- **A/C frequency weighting** defaults to `high_accuracy=True`: the filter is
  designed and run at an internally oversampled rate (≥ 96 kHz), keeping the
  response within IEC 61672-1 class 1 tolerances up to 16 kHz at common audio
  rates (previously −2.67 dB at 12.5 kHz for fs = 48 kHz, outside class 1).
  Stateful weighting keeps the legacy design; `high_accuracy=True` with
  `stateful=True` raises. ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))

### Added

- `leq()`, `laeq()` and `ln_levels()` (L10/L50/L90 statistical levels from the
  Fast/Slow/Impulse envelope, with optional A/C weighting). ([#60](https://github.com/jmrplens/PyOctaveBand/pull/60))
- `OctaveFilterBank.spectrogram()`: short-time band levels (bands × frames),
  multichannel-aware, with bounded-memory windowing. ([#60](https://github.com/jmrplens/PyOctaveBand/pull/60))
- `zero_phase=True` option in `OctaveFilterBank.filter()` and `spectrogram()`:
  forward-backward filtering (no group delay) for offline analysis. ([#60](https://github.com/jmrplens/PyOctaveBand/pull/60))
- `TimeWeighting` stateful class for block processing (block outputs match a
  single continuous call exactly). ([#60](https://github.com/jmrplens/PyOctaveBand/pull/60))
- `weighting_filter(..., high_accuracy=...)` and
  `WeightingFilter(..., high_accuracy=...)` parameter. ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))
- PEP 561 `py.typed` marker: downstream type checkers now receive the
  library's strict annotations.
- Documentation website (English/Español) at
  https://jmrplens.github.io/PyOctaveBand/ with theme-aware auto-generated
  figures, plus topic pages under `docs/`. ([#61](https://github.com/jmrplens/PyOctaveBand/pull/61))

### Fixed

- Integer input (e.g. int16 audio from `scipy.io.wavfile.read`) no longer
  overflows silently: `time_weighting` returned negative energies and
  `calculate_sensitivity` produced factors ~315× off. All inputs are converted
  to float64. ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))
- `cheby2` with `attenuation <= 3.01 dB` now raises instead of silently
  producing NaN coefficients. ([#58](https://github.com/jmrplens/PyOctaveBand/pull/58))
- `zero_phase` no longer crashes on heavily decimated bands shorter than the
  default `sosfiltfilt` padding. ([#60](https://github.com/jmrplens/PyOctaveBand/pull/60))
- The weighting-curves documentation figure measured a truncated impulse
  response through the resampling path (~2.4 dB low); the measurement is now
  guarded by tests. ([#63](https://github.com/jmrplens/PyOctaveBand/pull/63))

### Performance

- `octavefilter()` reuses cached filter-bank designs across calls (~3.3×
  faster in loops). ([#59](https://github.com/jmrplens/PyOctaveBand/pull/59))
- `numba` and `matplotlib` are optional extras (`[perf]`, `[plot]`, `[full]`);
  a pure-Python impulse kernel and lazy plotting imports keep full
  functionality without them. ([#59](https://github.com/jmrplens/PyOctaveBand/pull/59))

## [1.2.3] - 2026-05-30

### Fixed

- Importing the package no longer forces the matplotlib Agg backend. ([#53](https://github.com/jmrplens/PyOctaveBand/pull/53))

## [1.2.2] - 2026-05-09

### Added

- Configurable time weighting initial state (`initial_state`: `'zero'`,
  `'first'`, scalar or per-channel array). ([#49](https://github.com/jmrplens/PyOctaveBand/pull/49))

## [1.2.1] - 2026-03-08

### Added

- IEC 61260-1 nominal frequency labels (`nominal=True`). ([#46](https://github.com/jmrplens/PyOctaveBand/pull/46))

## [1.1.5] - 2026-03-08

### Fixed

- Overloads, `WeightingFilter` multichannel state, version sync and SonarCloud
  CI. ([#45](https://github.com/jmrplens/PyOctaveBand/pull/45))

## [1.1.4] - 2026-03-08

### Added

- Stateful block-wise processing for `OctaveFilterBank` and
  `WeightingFilter`. ([#42](https://github.com/jmrplens/PyOctaveBand/pull/42))
- macOS and Windows in the CI test matrix. ([#40](https://github.com/jmrplens/PyOctaveBand/pull/40))

## [1.1.1] - 2026-01-07

### Changed

- DSP core enhancements: vectorization, IEC standards alignment and
  precision. ([#35](https://github.com/jmrplens/PyOctaveBand/pull/35))

## [1.0.0] - 2026-01-06

Initial PyPI release: fractional octave filter banks (Butterworth,
Chebyshev I/II, Elliptic, Bessel), A/C/Z weighting, Fast/Slow/Impulse time
weighting, Linkwitz-Riley crossover, calibration and dBFS modes,
multichannel support.

[Unreleased]: https://github.com/jmrplens/PyOctaveBand/compare/v1.2.3...HEAD
[1.2.3]: https://github.com/jmrplens/PyOctaveBand/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/jmrplens/PyOctaveBand/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/jmrplens/PyOctaveBand/compare/v1.1.5...v1.2.1
[1.1.5]: https://github.com/jmrplens/PyOctaveBand/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/jmrplens/PyOctaveBand/compare/v1.1.1...v1.1.4
[1.1.1]: https://github.com/jmrplens/PyOctaveBand/compare/v1.0.0...v1.1.1
[1.0.0]: https://github.com/jmrplens/PyOctaveBand/releases/tag/v1.0.0
