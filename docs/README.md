# phonometry Documentation

Full documentation for phonometry. Also available as a website:
**https://jmrplens.github.io/phonometry/**

## Guides

- [Getting Started](getting-started.md) — installation and first analysis
- [Filter Banks](filter-banks.md) — architectures, responses, band decomposition
- [Block Processing](block-processing.md) — stateful real-time workflows
- [Multichannel](multichannel.md) — vectorized multichannel analysis
- [Calibration and dBFS](calibration.md) — physical SPL and digital analysis
- [Integrated & Statistical Levels](levels.md) — Leq, LAeq, L10/L50/L90, LCpeak/SEL, noise dose (IEC 61252), Lden and rating levels (ISO 1996-1), octave spectrogram
- [Frequency Weighting](weighting.md) — A, C, Z curves
- [Time Weighting](time-weighting.md) — Fast, Slow, Impulse ballistics
- [Psychoacoustics](psychoacoustics.md) — Zwicker, Moore-Glasberg and Sottek loudness, sharpness, equal-loudness contours (ISO 226), tonality and roughness
- [Prominent discrete tones](tone-prominence.md) — the ECMA-418-1 tone-to-noise and prominence ratios that decide whether a discrete tone is prominent and justify tonal rating adjustments
- [Tonal audibility of tones in noise](tone-audibility.md) — the ISO/PAS 20065 engineering method for the audibility ΔL of a tone above the masking threshold: the critical band about the tone, the critical-band masking level, the masking index, and the decisive and mean audibility
- [Psychoacoustic annoyance & fluctuation strength](psychoacoustic-annoyance.md) — the Fastl & Zwicker annoyance PA = N5·√(1 + wS² + wFR²) from loudness, sharpness, roughness and fluctuation strength (Eqs 16.2–16.4), the closed form for AM broadband noise (Eq. 10.2) and the Osses 2016 fluctuation-strength signal model
- [Speech Transmission Index](speech-transmission.md) — how much of the speech envelope a room or sound system preserves: the IEC 60268-16 modulation transfer function, indirect method and direct STIPA measurement
- [Speech Intelligibility Index](speech-intelligibility.md) — the ANSI S3.5-1997 one-third-octave-band SII: band-importance weighting (Table 3), self-speech and upward spread of masking, band audibility, and the index in noise and hearing loss
- [Electroacoustics: distortion & frequency response](electroacoustics.md) — the IEC 60268-3 distortion set (THD, nth-order harmonic, THD+N and SINAD via AES17, SMPTE and CCIF intermodulation, dynamic intermodulation and weighted THD) and the Bendat & Piersol H1/H2 frequency-response estimators with the ordinary coherence γ²
- [Underwater acoustics: radiated noise & pile driving](underwater-acoustics.md) — the ISO 18405 reference levels (SPL, SEL, peak re 1 µPa), the ISO 17208 ship radiated noise level and equivalent monopole source level via the Lloyd's-mirror correction, and the ISO 18406 single-strike, peak and cumulative pile-driving sound exposure
- [Hearing threshold](hearing-threshold.md) — the age-related hearing threshold distribution (ISO 7029:2017) and the free-field/diffuse-field reference threshold of hearing (ISO 389-7:2006)
- [Noise-induced hearing loss](noise-induced-hearing-loss.md) — the ISO 1999:2013 noise-induced permanent threshold shift (NIPTS) and its population distribution, and the combination with age into the hearing threshold level associated with age and noise (HTLAN)
- [Occupational noise exposure](occupational-exposure.md) — the ISO 9612 task-based, job-based and full-day measurement strategies and the Annex C uncertainty budget behind every LEX,8h report
- [Sound Intensity (p-p)](intensity.md) — two-microphone intensity and field indicators
- [Sound Power](sound-power.md) — sound power level by enveloping surface (ISO 3744/3746), reverberation room (ISO 3741), intensity scanning (ISO 9614-2), and the precision grades in an anechoic room (ISO 3745) and by precision intensity scanning (ISO 9614-3)
- [Room Acoustics](room-acoustics.md) — impulse-response acquisition (ISO 18233), reverberation and room parameters (ISO 3382-1/2), open-plan speech metrics (ISO 3382-3), reverberation-room sound absorption (ISO 354)
- [Sound absorption in enclosed spaces](enclosed-space-absorption.md) — the EN 12354-6:2003 prediction of a room's total equivalent absorption area and reverberation time from its surfaces and objects (Clause 4)
- [Reverberation-time prediction](reverberation-prediction.md) — the reverberation time from a room's volume and surface absorption by five statistical models (Sabine, Eyring, Millington-Sette, Fitzroy, Arau-Puchades), with the air-absorption term
- [Dynamic stiffness of resilient materials](dynamic-stiffness.md) — the EN 29052-1:1992 dynamic stiffness per unit area of floating-floor resilient layers from the load-plate resonance, and the floating-floor natural frequency
- [Mechanical mobility and the FRF family](mechanical-mobility.md) — the ISO 7626-1:2011 family of motion-per-force frequency-response functions (receptance, mobility, accelerance and their reciprocals, Table 1), conversion through the receptance pivot, and the single-degree-of-freedom reference resonator (Annex A)
- [Dynamic transfer stiffness of resilient elements](transfer-stiffness.md) — the ISO 10846 dynamic transfer stiffness k₂₁ of vibration isolators: the level Lₖ re 1 N/m and loss factor, the direct and indirect (transmissibility) determination methods, and the Annex-A relation to mechanical impedance and effective mass
- [Sound power from surface vibration](vibration-sound-power.md) — the ISO/TS 7849 estimation of a machine's radiated airborne sound power from its surface vibratory velocity and a radiation factor: the velocity level and calibration, the surface mean, and the Part 1 upper limit (ε=1) versus the Part 2 engineering value
- [Structure-borne sound power of building equipment](structure-borne-power.md) — the EN 15657 reception-plate method for a source's characteristic structure-borne sound power level Lₛ: the spatial mean plate velocity, the loss factor from the structural reverberation time, and the low- and high-mobility plates
- [Installed structure-borne sound from equipment](installed-structure-borne.md) — the EN 12354-5 prediction of the receiving-room sound pressure level from service equipment: the coupling term from source and receiver mobilities, the installed structure-borne power, and the per-path transmission with its energetic total
- [Room-noise criteria](room-noise.md) — the ANSI/ASA S12.2-2019 room-noise ratings: the NC tangency method (Table 1) and the RC Mark II rating with its rumble/hiss/neutral spectral tag (Annex D)
- [Acoustic Materials](materials.md) — sound-absorption rating α_w and classes (ISO 11654), airflow resistance static and alternating methods (ISO 9053-1/-2), and impedance-tube measurement of absorption, surface impedance and transmission loss (ISO 10534-1/-2, ASTM E2611)
- [Surface Scattering, Diffusion and In-situ Absorption](surface-scattering.md) — random-incidence scattering (ISO 17497-1), free-field diffusion coefficient (ISO 17497-2), and in-situ road-surface absorption by the extended-surface subtraction technique (ISO 13472-1) and the spot method (ISO 13472-2)
- [Building Acoustics](building-acoustics.md) — field airborne/impact/façade insulation and weighted ratings (ISO 16283-1/2/3, ISO 717-1/2), laboratory characterisation (ISO 10140), flanking-transmission prediction (EN 12354-1/2), measurement uncertainty (ISO 12999-1)
- [Outdoor Sound Propagation](outdoor-propagation.md) — atmospheric absorption α(f) (ISO 9613-1) and the ISO 9613-2 general method: divergence, atmospheric absorption, ground effect and barrier screening
- [Impulsive-sound prominence](impulse-prominence.md) — the NT ACOU 112:2002 predicted prominence of impulsive sounds (onset rate and level difference) and the graduated adjustment KI added to LAeq
- [Human Vibration](human-vibration.md) — whole-body and hand-arm frequency weightings (ISO 8041-1), weighted r.m.s. acceleration, running r.m.s./MTVV/VDV and crest factor (ISO 2631-1), vibration in buildings (ISO 2631-2), vibration total value and daily exposure A(8) (ISO 5349-1/-2), and the exposure action/limit values of Directive 2002/44/EC
- [Multiple-shock whole-body vibration](multiple-shock-vibration.md) — the ISO 2631-5:2018 spinal-response model: the seat-to-spine transfer function, the acceleration and daily dose from the response peaks (Clause 5), and the compressive stress, stress variable R and Weibull probability of lumbar injury (Annex C)
- [Measurement uncertainty](gum-uncertainty.md) — the GUM law of propagation of uncertainty and the Monte Carlo method (ISO/IEC Guide 98-3:2008 and Supplement 1): combined and expanded uncertainty, Welch–Satterthwaite effective degrees of freedom, and probabilistically symmetric coverage intervals

## Reference

- [API Reference](api-reference.md) — every public function and class
- [Theory](theory.md) — standards, math and design decisions
- [Why phonometry](why-phonometry.md) — IEC compliance vs other libraries
- [Conformance report](CONFORMANCE.md) — auto-generated numerical validation: every check pins a standard clause's expected value against the library's computed value, regenerated in CI

## Development

Run the test suite with `pytest tests/`, the full quality gate with `make check`
(ruff + mypy + bandit + tests), and regenerate the documentation images with
`make graphs`. See [CONTRIBUTING.md](../CONTRIBUTING.md).
