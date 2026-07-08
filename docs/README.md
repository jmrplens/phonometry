# phonometry Documentation

Full documentation for phonometry. Also available as a website:
**https://jmrplens.github.io/phonometry/**

## Guides

- [Getting Started](getting-started.md) — installation and first analysis
- [Filter Banks](filter-banks.md) — architectures, responses, band decomposition
- [Frequency Weighting](weighting.md) — A, C, Z curves
- [Time Weighting](time-weighting.md) — Fast, Slow, Impulse ballistics
- [Integrated & Statistical Levels](levels.md) — Leq, LAeq, L10/L50/L90, octave spectrogram
- [Psychoacoustics and Speech Intelligibility](psychoacoustics.md) — Zwicker loudness, sharpness, STI/STIPA
- [Sound Intensity (p-p)](intensity.md) — two-microphone intensity and field indicators
- [Room and Building Acoustics](room-acoustics.md) — impulse-response acquisition, reverberation and room parameters, open-plan speech metrics, field airborne/impact/façade sound insulation (ISO 16283-1/2/3), laboratory characterisation (ISO 10140), flanking-transmission prediction (EN 12354-1/2), measurement uncertainty (ISO 12999-1), sound absorption (ISO 354)
- [Sound Power](sound-power.md) — sound power level by enveloping surface (ISO 3744/3746), reverberation room (ISO 3741) and intensity scanning (ISO 9614-2)
- [Calibration and dBFS](calibration.md) — physical SPL and digital analysis
- [Block Processing](block-processing.md) — stateful real-time workflows
- [Multichannel](multichannel.md) — vectorized multichannel analysis

## Reference

- [API Reference](api-reference.md) — every public function and class
- [Theory](theory.md) — standards, math and design decisions
- [Why phonometry](why-phonometry.md) — IEC compliance vs other libraries

## Development

Run the test suite with `pytest tests/`, the full quality gate with `make check`
(ruff + mypy + bandit + tests), and regenerate the documentation images with
`make graphs`. See [CONTRIBUTING.md](../CONTRIBUTING.md).
