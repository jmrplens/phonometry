# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- One-line canonical `.plot()` method on every public result object —
  `ZwickerLoudness`, `STIResult`, `RoomAcousticsResult`, `DecayCurve`,
  `WeightedRatingResult`, `ImpactRatingResult`, `SoundPowerResult`,
  `ReverberationSoundPowerResult`, `SoundPowerIntensityResult` and
  `IntensityResult` — reproducing each result's documentation figure in a
  single call (`res.plot()`). matplotlib stays a soft dependency: importing
  and computing work without it, and `.plot()` raises a clear `ImportError`
  with `pip install phonometry[plot]` guidance when it is missing. The
  renderers create their own figure when `ax` is `None`, always return the
  Matplotlib `Axes` (an array for multi-panel figures) and never call
  `plt.show()`, so they compose into larger layouts. To feed those
  figures, `WeightedRatingResult` and `ImpactRatingResult` now also carry
  `band_centers`, `measured` and `shifted_reference`, exposing the ISO 717
  measured curve and shifted reference behind each single-number rating.
- `sweep_signal()`, `inverse_filter()`, `impulse_response()`, `mls_signal()`
  and `mls_impulse_response()` — deterministic-excitation impulse-response
  acquisition per ISO 18233:2006 (exponential sine sweep with spectral and
  Farina deconvolution, maximum-length sequences), verified by recovering
  known impulse responses at the correct sample lags.
- `decay_curve()`, `room_parameters()` and `RoomAcousticsResult` — room
  acoustic parameters per ISO 3382-1:2009 / 3382-2:2008 (Schroeder backward
  integration with noise truncation and tail compensation; EDT/T20/T30,
  C50/C80, D50, Ts with dynamic-range validity flags and curvature),
  verified against the exponential-decay closed forms within their JNDs.
- `open_plan_metrics()` and `OpenPlanResult` — open-plan-office spatial
  speech metrics per ISO 3382-3:2012 (spatial decay rate D2,S and Lp,A,S,4m
  from the log-distance regression, distraction distance rD and privacy
  distance rP from the STI-vs-distance line).
- `airborne_insulation()`, `weighted_rating()`, `energy_average_level()`
  and the `AirborneInsulationResult` / `WeightedRatingResult` dataclasses —
  field airborne sound insulation per ISO 16283-1:2014 (D, DnT, R') and
  single-number weighted ratings with C/Ctr per ISO 717-1 (reference-curve
  method), verified against the ISO 717-1 Annex C worked example.
- `impact_insulation()`, `weighted_impact_rating()` and the
  `ImpactInsulationResult` / `ImpactRatingResult` dataclasses — field impact
  sound insulation per ISO 16283-2 (standardized L'nT and normalized L'n from
  the tapping-machine impact level) and single-number weighted impact ratings
  with the CI adaptation term per ISO 717-2 (reference-curve method, octave
  −5 dB rule), verified against the ISO 717-2 Annex C examples (Ln,w = 79,
  CI = −11; octave 54, CI = 0).
- `absorption_area()`, `absorption_coefficient()`, `attenuation_from_alpha()`
  and `AbsorptionWarning` — sound absorption in a reverberation room per
  ISO 354:2003 (equivalent absorption area from the empty and with-specimen
  reverberation times via Sabine's equation with the air-attenuation term, and
  the plane-absorber coefficient αs, left unclamped per Clause 3.7), with
  room-volume and sample-area qualification advisories.
- `sound_power_pressure()`, `measurement_positions()`,
  `background_noise_correction()`, `environmental_correction()` and
  `SoundPowerResult` / `SoundPowerWarning` — sound power level from surface
  sound pressure per ISO 3744:2010 (engineering) and ISO 3746:2010 (survey):
  hemisphere and box measurement surfaces, background (K1) and environmental
  (K2) corrections, A-weighted total, directivity index and expanded
  uncertainty.
- `sound_power_reverberation()`, `sound_power_comparison()` and
  `ReverberationSoundPowerResult` — precision-grade sound power in a
  reverberation room per ISO 3741:2010 (direct method with Sabine absorption
  area, Waterhouse boundary correction and C1/C2 meteorological corrections;
  comparison method against a reference sound source), with room-qualification
  advisories.
- `sound_power_intensity()` and `SoundPowerIntensityResult` — sound power by
  sound-intensity scanning per ISO 9614-2:1996 (partial powers over the
  measurement surface, FpI and F+/− field indicators, per-segment
  repeatability and the per-band achieved engineering/survey grade).
- `loudness_zwicker()` / `loudness_zwicker_from_spectrum()` — Zwicker
  loudness per ISO 532-1:2017 (stationary and time-varying), a clean-room
  port of the normative reference program with the full Annex B validation
  set in CI (25 test cases, per-sample tolerance bands).
- `sharpness_din()` — sharpness in acum per DIN 45692:2009 with the Aures
  and von Bismarck variants, verified against the Table A.2 targets.
- `sti_from_impulse_response()`, `stipa()` and `stipa_signal()` — Speech
  Transmission Index per IEC 60268-16 Ed. 5 (indirect and direct STIPA
  methods, Ed. 5 male spectrum, Annex F ratings), verified against the
  standard's weighting-pair and m-mapping vectors and the Schroeder
  closed form.
- `sound_intensity()`, `field_indicators()`, `dynamic_capability_index()` —
  two-microphone p-p sound intensity per IEC 61043 (cross-spectral
  estimator, finite-difference bias correction validated against Table 3)
  with the ISO 9614-1 Annex A field indicators.
- `weighting_filter(..., curve="G")` — G frequency weighting for infrasound
  (ISO 7196:1995), verified against every Table 2 nominal response value.
- `equal_loudness_contour()`, `loudness_level()`, `hearing_threshold()` —
  ISO 226:2023 normal equal-loudness-level contours (Formulae 1-2, Table 1),
  verified against the Annex B tables.
- `tone_to_noise_ratio()` and `prominence_ratio()` — prominent discrete tone
  assessment per ECMA-418-1:2024 (clauses 10-12), including proximate-tone
  combination and the low-frequency truncated band.
- `lden()`, `ldn()`, `composite_rating_level()` — environmental noise
  descriptors per ISO 1996-1:2016 (3.6.4/3.6.5 and clause 6.5).
- `calculate_sensitivity(..., narrowband=True)` — opt-in coherent
  single-frequency (Goertzel) tone estimator that locks to the calibrator
  tone near `frequency` and rejects broadband hum/noise in the reference
  take, which otherwise inflates the RMS and biases the sensitivity by
  `-10*lg(1 + 1/SNR)` (about -0.42 dB at 10 dB SNR). The default keeps the
  legacy broadband-RMS behaviour.
- `decay_curve(..., zero_phase=...)` and `room_parameters(..., zero_phase=...)`
  — optional forward-backward (time-reversed) octave filtering permitted by
  ISO 3382-2:2008 Clause 7.3 NOTE (relaxing B*T > 16 to B*T > 4). It removes
  the octave filter's group delay before the backward integration, roughly
  halving the 125 Hz short-decay T30 bias. Default off (causal).
- `sound_intensity(..., bias_correct=True)` — optional per-bin
  finite-difference correction `(k*dr)/sin(k*dr)` (IEC 61043:1994, 7.3)
  applied to the band and broadband intensity totals so they no longer
  under-read toward `max_valid_frequency`. Default off (legacy totals).
- **STIPA (IEC 60268-16):** `stipa()` now emits a `UserWarning` for
  recordings shorter than the recommended 15 s, where the recovered
  modulation depths (and STI) are biased low.
- `tone_to_noise_ratio()` / `prominence_ratio()` (ECMA-418-1) now warn when
  the FFT resolution is too coarse to resolve the tone band (fewer than
  ~3 bins across the 15 % tone half-width), which biases TNR/PR at low
  frequencies.
- `mls_impulse_response()` (ISO 18233) now warns when the recovered impulse
  response still carries energy at the end of the MLS period, the symptom of
  an impulse response longer than one period aliasing circularly (choose a
  higher MLS order).

### Changed

- `decay_curve()` now returns a `DecayCurve` dataclass (`time`, `level`,
  `band`) with a `.plot()` method instead of a bare `(time, level)` tuple.
  Backward compatible: `time, level = decay_curve(ir, fs)` still unpacks
  because `DecayCurve` iterates as `(time, level)`.
- `lc_peak()` now polyphase-oversamples the C-weighted signal (new
  `oversample` parameter, default 8) before peak detection, recovering the
  true inter-sample peak. Sustained high-frequency tones previously
  under-read by up to ~1.15 dB at fs = 48 kHz (e.g. an 8 kHz tone, 6.0
  samples/cycle); LCpeak now tracks the analytic peak within about +/-0.5 dB.
  Reported LCpeak values shift upward for HF-rich signals; pass
  `oversample=1` for the legacy on-grid behaviour.
- `OctaveFilterBank` / `octavefilter` default `attenuation` raised from 60 to
  72 dB. scipy's `cheby2` pins the equiripple deep-stopband floor at exactly
  `attenuation`, so the former 60 dB default sat 10 dB inside the IEC
  61260-1:2014 class 1 deep-stopband limit; 72 dB makes the default cheby2
  bank class 1 (same +0.400 dB passband margin as `butter`). Numerical
  outputs change for cheby2 users — and for elliptic (`ellip`) banks, which
  consume `attenuation` as their stopband attenuation `rs` — who relied on
  the previous default.
- Weighting-filter `high_accuracy` internal oversample target raised from
  96 to 144 kHz, so fs = 48 kHz now oversamples x3 (was x2). This halves the
  high-frequency residual vs the analytic A/C curves (48 kHz: -1.11 -> -0.44
  dB @16k, -2.10 -> -0.85 dB @20k) and removes the 48k-worse-than-44.1k
  asymmetry. High-accuracy weighting outputs shift for all rates below
  144 kHz (48/96/128 kHz included) — e.g. 96 kHz by +0.86 dB @16k / +1.63 dB
  @20k — always toward the analytic curve.
- Calibrator stability validation updated from IEC 60942:2003 to
  IEC 60942:2017 (Ed. 4): the deviations |max − mean| and |min − mean| are
  each compared against the limit, using the
  frequency-dependent Table 2 class 1 limits (0.07 dB in 160 Hz - 1.25 kHz);
  `calculate_sensitivity()` gains a `frequency` parameter.
- `ln_levels()` now discards 5*tau (was 2*tau) of the time-weighting
  integrator attack before computing the percentiles. At 2*tau the F
  integrator is only 86 % settled, so the leading ramp dragged the low
  percentiles down (~0.15 dB L10-L90 spread on a steady 2 s tone); 5*tau
  cuts that ~12x and matches the skip already used by the calibration
  stability check. Percentile values on short records shift slightly.

### Fixed

- **Sharpness (DIN 45692):** the informative Aures and von Bismarck variants
  are now anchored to exactly 1.00 acum on the clause 6 reference sound via
  per-variant normalization constants (previously 0.959 / 1.019 from a
  shared hard-coded factor).
- **Loudness (ISO 532-1):** N5/N10 percentiles are now computed on the
  full-rate 2000 Hz weighted-loudness series instead of the 4x-decimated
  500 Hz trace, removing an up-to-3% decimation-phase ambiguity. The
  500 Hz `time`/`loudness_vs_time` output and Nmax are unchanged.
- **Room acoustics (ISO 3382):** T20/T30 reverberation-time validity flags
  now require 46 dB / 54 dB of dynamic range (was 35 dB / 45 dB) to
  absorb the positive bias of the tail compensation and keep a flagged-valid
  decay time within the 5% JND (ISO 3382-2 Table A.1).
- **Impulse-response (ISO 18233):** `impulse_response(method="farina")` now
  raises `ValueError` when handed a zero-padded reference sweep (which
  silently produced a wrong inverse filter) instead of returning garbage;
  pass the unpadded sweep or use `method="spectral"`.

## [3.0.0] - 2026-07-06

### ⚠️ Breaking changes

- **The library is now `phonometry`** (formerly `PyOctaveBand`). Install with
  `pip install phonometry` and `import phonometry`. The API is unchanged — a
  plain rename of the import is a complete migration. The final
  `PyOctaveBand 2.1.0` release on PyPI is a transition stub that depends on
  `phonometry` and re-exports it under the old `pyoctaveband` module name with
  a `DeprecationWarning`, so `pip install -U PyOctaveBand` keeps existing code
  working. The last state under the old name is preserved in the locked
  [`pyoctaveband-v2`](https://github.com/jmrplens/phonometry/tree/pyoctaveband-v2) branch.
- **Python >= 3.13 required** (was >= 3.11). CI now tests 3.13 and 3.14
  (3.15 will be added once it reaches a stable release).

### Added

- `lc_peak()` — C-weighted peak level (IEC 61672-1 §5.13), verified against
  the Table 5 one-cycle/half-cycle tone-burst responses.
- `sel()` — sound exposure level (SEL/LAE), with class 1 conformance tests for
  the Table 4 LAE tone-burst column.
- `sound_exposure()` and `lex_8h()` — occupational noise dose (Pa²·h and
  normalized 8 h exposure level, IEC 61252).
- `calculate_sensitivity(..., validate=True)` — calibration-tone stability
  validation per IEC 60942 (short-term level fluctuation, class 1 limit),
  emitting `CalibrationWarning` on unstable or too-short recordings.

## [2.0.0] - 2026-07-06

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

- `verify_filter_class()`: verify a bank against the IEC 61260-1:2014
  class 1/2 acceptance limits (Table 1, transcribed from the official text)
  with per-band margins; `class_limits()` exposes the limit curves. ([#64](https://github.com/jmrplens/PyOctaveBand/pull/64))
- Standards-compliance test layer transcribed from the official texts:
  IEC 61672-1:2013 Table 4 tone-burst suite (F/S, 1 s to 1 ms) and Table 3
  full 34-frequency A/C weighting sweep within class 1 limits. ([#64](https://github.com/jmrplens/PyOctaveBand/pull/64))
- `CITATION.cff` and `.zenodo.json` metadata; Codecov coverage upload and
  quality badges. ([#64](https://github.com/jmrplens/PyOctaveBand/pull/64))
- Documentation: four new auto-generated figures (group delay, IEC
  toneburst, block continuity, IEC class mask), Mermaid diagrams, more
  equations, and a full SEO/GEO layer for the docs site (JSON-LD,
  llms.txt, AI-crawler opt-in, WCAG2AA gates). ([#66](https://github.com/jmrplens/PyOctaveBand/pull/66))
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

[Unreleased]: https://github.com/jmrplens/phonometry/compare/v3.0.0...HEAD
[3.0.0]: https://github.com/jmrplens/phonometry/compare/v2.0.0...v3.0.0
[2.0.0]: https://github.com/jmrplens/phonometry/compare/v1.2.3...v2.0.0
[1.2.3]: https://github.com/jmrplens/PyOctaveBand/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/jmrplens/PyOctaveBand/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/jmrplens/PyOctaveBand/compare/v1.1.5...v1.2.1
[1.1.5]: https://github.com/jmrplens/PyOctaveBand/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/jmrplens/PyOctaveBand/compare/v1.1.1...v1.1.4
[1.1.1]: https://github.com/jmrplens/PyOctaveBand/compare/v1.0.0...v1.1.1
[1.0.0]: https://github.com/jmrplens/PyOctaveBand/releases/tag/v1.0.0
