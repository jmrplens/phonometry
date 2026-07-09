# phonometry Documentation

Full documentation for phonometry. Also available as a website:
**https://jmrplens.github.io/phonometry/**

## Guides

- [Getting Started](getting-started.md) — installation and first analysis
- [Filter Banks](filter-banks.md) — architectures, responses, band decomposition
- [Frequency Weighting](weighting.md) — A, C, Z curves
- [Time Weighting](time-weighting.md) — Fast, Slow, Impulse ballistics
- [Integrated & Statistical Levels](levels.md) — Leq, LAeq, L10/L50/L90, noise dose and occupational exposure (ISO 9612), octave spectrogram
- [Psychoacoustics and Speech Intelligibility](psychoacoustics.md) — Zwicker loudness, sharpness, STI/STIPA
- [Speech Intelligibility Index](speech-intelligibility.md) — the ANSI S3.5-1997 one-third-octave-band SII: band-importance weighting (Table 3), self-speech and upward spread of masking, band audibility, and the index in noise and hearing loss
- [Room-noise criteria](room-noise.md) — the ANSI/ASA S12.2-2019 room-noise ratings: the NC tangency method (Table 1) and the RC Mark II rating with its rumble/hiss/neutral spectral tag (Annex D)
- [Hearing threshold](hearing-threshold.md) — the age-related hearing threshold distribution (ISO 7029:2017) and the free-field/diffuse-field reference threshold of hearing (ISO 389-7:2006)
- [Noise-induced hearing loss](noise-induced-hearing-loss.md) — the ISO 1999:2013 noise-induced permanent threshold shift (NIPTS) and its population distribution, and the combination with age into the hearing threshold level associated with age and noise (HTLAN)
- [Impulsive-sound prominence](impulse-prominence.md) — the NT ACOU 112:2002 predicted prominence of impulsive sounds (onset rate and level difference) and the graduated adjustment KI added to LAeq
- [Measurement uncertainty](gum-uncertainty.md) — the GUM law of propagation of uncertainty and the Monte Carlo method (ISO/IEC Guide 98-3:2008 and Supplement 1): combined and expanded uncertainty, Welch–Satterthwaite effective degrees of freedom, and probabilistically symmetric coverage intervals
- [Sound Intensity (p-p)](intensity.md) — two-microphone intensity and field indicators
- [Room and Building Acoustics](room-acoustics.md) — impulse-response acquisition, reverberation and room parameters, open-plan speech metrics, field airborne/impact/façade sound insulation (ISO 16283-1/2/3), laboratory characterisation (ISO 10140), flanking-transmission prediction (EN 12354-1/2), measurement uncertainty (ISO 12999-1), sound absorption (ISO 354)
- [Outdoor Sound Propagation](outdoor-propagation.md) — atmospheric absorption α(f) (ISO 9613-1) and the ISO 9613-2 general method: divergence, atmospheric absorption, ground effect and barrier screening (occupational exposure ISO 9612 lives in [Levels](levels.md))
- [Sound Power](sound-power.md) — sound power level by enveloping surface (ISO 3744/3746), reverberation room (ISO 3741), intensity scanning (ISO 9614-2), and the precision grades in an anechoic room (ISO 3745) and by precision intensity scanning (ISO 9614-3)
- [Acoustic Materials](materials.md) — sound-absorption rating α_w and classes (ISO 11654), airflow resistance static and alternating methods (ISO 9053-1/-2), and impedance-tube measurement of absorption, surface impedance and transmission loss (ISO 10534-1/-2, ASTM E2611)
- [Surface Scattering, Diffusion and In-situ Absorption](surface-scattering.md) — random-incidence scattering (ISO 17497-1), free-field diffusion coefficient (ISO 17497-2), and in-situ road-surface absorption by the extended-surface subtraction technique (ISO 13472-1) and the spot method (ISO 13472-2)
- [Human Vibration](human-vibration.md) — whole-body and hand-arm frequency weightings (ISO 8041-1), weighted r.m.s. acceleration, running r.m.s./MTVV/VDV and crest factor (ISO 2631-1), vibration in buildings (ISO 2631-2), vibration total value and daily exposure A(8) (ISO 5349-1/-2), and the exposure action/limit values of Directive 2002/44/EC
- [Multiple-shock whole-body vibration](multiple-shock-vibration.md) — the ISO 2631-5:2018 spinal-response model: the seat-to-spine transfer function, the acceleration and daily dose from the response peaks (Clause 5), and the compressive stress, stress variable R and Weibull probability of lumbar injury (Annex C)
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
