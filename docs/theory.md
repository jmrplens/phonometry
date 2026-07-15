← [Documentation index](README.md)

# Theoretical Background

The theory reference explains the standards, the mathematics and the design decisions behind every phonometry module. It is split into five domain pages, listed below with the sections each one hosts. Theory for the underwater modules lives with its guides: [Underwater Acoustics](underwater-acoustics.md) and [Underwater Propagation](underwater-propagation.md).

## [Signal Analysis](theory-signal-analysis.md)

- [Octave Band Frequencies (ANSI S1.11 / IEC 61260)](theory-signal-analysis.md#octave-band-frequencies-ansi-s111--iec-61260)
- [Frequency Resolution vs FFT Bin Spacing](theory-signal-analysis.md#frequency-resolution-vs-fft-bin-spacing)
- [Magnitude Responses |H(jw)|](theory-signal-analysis.md#magnitude-responses-hjw)
- [Filter Bank Design & Numerical Stability](theory-signal-analysis.md#filter-bank-design--numerical-stability)
- [Weighting Curves (IEC 61672-1)](theory-signal-analysis.md#weighting-curves-iec-61672-1)
- [Time Integration](theory-signal-analysis.md#time-integration)
- [G-weighting (ISO 7196)](theory-signal-analysis.md#g-weighting-iso-7196)
- [Event and dose metrics](theory-signal-analysis.md#event-and-dose-metrics)
- [Sound intensity (IEC 61043)](theory-signal-analysis.md#sound-intensity-iec-61043)
- [Measurement uncertainty (ISO/IEC Guide 98-3 — GUM and Supplement 1)](theory-signal-analysis.md#measurement-uncertainty-isoiec-guide-98-3--gum-and-supplement-1)

## [Perception and Hearing](theory-perception.md)

- [Equal-loudness contours (ISO 226:2023)](theory-perception.md#equal-loudness-contours-iso-2262023)
- [Tone prominence: TNR and PR (ECMA-418-1)](theory-perception.md#tone-prominence-tnr-and-pr-ecma-418-1)
- [Zwicker loudness (ISO 532-1)](theory-perception.md#zwicker-loudness-iso-532-1)
- [Advanced loudness models & sound quality](theory-perception.md#advanced-loudness-models--sound-quality)
- [Modulation transfer and STI (IEC 60268-16)](theory-perception.md#modulation-transfer-and-sti-iec-60268-16)
- [Speech Intelligibility Index (ANSI S3.5)](theory-perception.md#speech-intelligibility-index-ansi-s35)
- [Hearing thresholds and presbycusis (ISO 389-7, ISO 7029)](theory-perception.md#hearing-thresholds-and-presbycusis-iso-389-7-iso-7029)
- [Noise-induced hearing loss (ISO 1999)](theory-perception.md#noise-induced-hearing-loss-iso-1999)

## [Rooms and Buildings](theory-rooms-buildings.md)

- [Room noise criteria (ANSI S12.2)](theory-rooms-buildings.md#room-noise-criteria-ansi-s122)
- [Room and building acoustics (ISO 18233, ISO 3382, ISO 16283, ISO 10140, EN 12354, ISO 12999, ISO 717, ISO 354)](theory-rooms-buildings.md#room-and-building-acoustics-iso-18233-iso-3382-iso-16283-iso-10140-en-12354-iso-12999-iso-717-iso-354)
- [Surface scattering and diffusion (ISO 17497-1, ISO 17497-2)](theory-rooms-buildings.md#surface-scattering-and-diffusion-iso-17497-1-iso-17497-2)
- [In-situ road surface absorption (ISO 13472-1, ISO 13472-2)](theory-rooms-buildings.md#in-situ-road-surface-absorption-iso-13472-1-iso-13472-2)
- [Acoustic material characterisation (ISO 11654, ISO 9053-1/2, ISO 10534-1/2, ASTM E2611)](theory-rooms-buildings.md#acoustic-material-characterisation-iso-11654-iso-9053-12-iso-10534-12-astm-e2611)

## [Environment and Transport](theory-environment-transport.md)

- [Environmental descriptors (ISO 1996-1)](theory-environment-transport.md#environmental-descriptors-iso-1996-1)
- [Impulsive-sound prominence (NT ACOU 112)](theory-environment-transport.md#impulsive-sound-prominence-nt-acou-112)
- [Outdoor propagation and occupational exposure (ISO 9613-1/2, ISO 9612)](theory-environment-transport.md#outdoor-propagation-and-occupational-exposure-iso-9613-12-iso-9612)
- [Sound power determination (ISO 3744/3745/3746, ISO 3741, ISO 9614-2/3)](theory-environment-transport.md#sound-power-determination-iso-374437453746-iso-3741-iso-9614-23)

## [Vibration](theory-vibration.md)

- [Human vibration (ISO 8041-1, ISO 2631-1/2, ISO 5349-1/2, Directive 2002/44/EC)](theory-vibration.md#human-vibration-iso-8041-1-iso-2631-12-iso-5349-12-directive-200244ec)

## Anchor map

This page used to host every section. Deep links into the old single page can be re-found here: each old anchor maps to the page that now hosts the section.

| Old anchor | Section | New page |
| :--- | :--- | :--- |
| `#octave-band-frequencies-ansi-s111--iec-61260` | Octave Band Frequencies (ANSI S1.11 / IEC 61260) | [Signal Analysis](theory-signal-analysis.md#octave-band-frequencies-ansi-s111--iec-61260) |
| `#frequency-resolution-vs-fft-bin-spacing` | Frequency Resolution vs FFT Bin Spacing | [Signal Analysis](theory-signal-analysis.md#frequency-resolution-vs-fft-bin-spacing) |
| `#magnitude-responses-hjw` | Magnitude Responses \|H(jw)\| | [Signal Analysis](theory-signal-analysis.md#magnitude-responses-hjw) |
| `#band-edge-placement` | Band-edge placement | [Signal Analysis](theory-signal-analysis.md#band-edge-placement) |
| `#filter-bank-design--numerical-stability` | Filter Bank Design & Numerical Stability | [Signal Analysis](theory-signal-analysis.md#filter-bank-design--numerical-stability) |
| `#weighting-curves-iec-61672-1` | Weighting Curves (IEC 61672-1) | [Signal Analysis](theory-signal-analysis.md#weighting-curves-iec-61672-1) |
| `#time-integration` | Time Integration | [Signal Analysis](theory-signal-analysis.md#time-integration) |
| `#g-weighting-iso-7196` | G-weighting (ISO 7196) | [Signal Analysis](theory-signal-analysis.md#g-weighting-iso-7196) |
| `#equal-loudness-contours-iso-2262023` | Equal-loudness contours (ISO 226:2023) | [Perception and Hearing](theory-perception.md#equal-loudness-contours-iso-2262023) |
| `#tone-prominence-tnr-and-pr-ecma-418-1` | Tone prominence: TNR and PR (ECMA-418-1) | [Perception and Hearing](theory-perception.md#tone-prominence-tnr-and-pr-ecma-418-1) |
| `#event-and-dose-metrics` | Event and dose metrics | [Signal Analysis](theory-signal-analysis.md#event-and-dose-metrics) |
| `#environmental-descriptors-iso-1996-1` | Environmental descriptors (ISO 1996-1) | [Environment and Transport](theory-environment-transport.md#environmental-descriptors-iso-1996-1) |
| `#impulsive-sound-prominence-nt-acou-112` | Impulsive-sound prominence (NT ACOU 112) | [Environment and Transport](theory-environment-transport.md#impulsive-sound-prominence-nt-acou-112) |
| `#zwicker-loudness-iso-532-1` | Zwicker loudness (ISO 532-1) | [Perception and Hearing](theory-perception.md#zwicker-loudness-iso-532-1) |
| `#advanced-loudness-models--sound-quality` | Advanced loudness models & sound quality | [Perception and Hearing](theory-perception.md#advanced-loudness-models--sound-quality) |
| `#moore-glasberg-loudness-iso-532-22017-iso-532-32023` | Moore-Glasberg loudness (ISO 532-2:2017, ISO 532-3:2023) | [Perception and Hearing](theory-perception.md#moore-glasberg-loudness-iso-532-22017-iso-532-32023) |
| `#sottek-hearing-model-ecma-418-22025` | Sottek Hearing Model (ECMA-418-2:2025) | [Perception and Hearing](theory-perception.md#sottek-hearing-model-ecma-418-22025) |
| `#tonality--autocorrelation-of-the-band-signal-ecma-418-2` | Tonality — autocorrelation of the band signal (ECMA-418-2) | [Perception and Hearing](theory-perception.md#tonality--autocorrelation-of-the-band-signal-ecma-418-2) |
| `#roughness--envelope-modulation-ecma-418-2` | Roughness — envelope modulation (ECMA-418-2) | [Perception and Hearing](theory-perception.md#roughness--envelope-modulation-ecma-418-2) |
| `#sharpness-din-45692` | Sharpness (DIN 45692) | [Perception and Hearing](theory-perception.md#sharpness-din-45692) |
| `#modulation-transfer-and-sti-iec-60268-16` | Modulation transfer and STI (IEC 60268-16) | [Perception and Hearing](theory-perception.md#modulation-transfer-and-sti-iec-60268-16) |
| `#speech-intelligibility-index-ansi-s35` | Speech Intelligibility Index (ANSI S3.5) | [Perception and Hearing](theory-perception.md#speech-intelligibility-index-ansi-s35) |
| `#hearing-thresholds-and-presbycusis-iso-389-7-iso-7029` | Hearing thresholds and presbycusis (ISO 389-7, ISO 7029) | [Perception and Hearing](theory-perception.md#hearing-thresholds-and-presbycusis-iso-389-7-iso-7029) |
| `#noise-induced-hearing-loss-iso-1999` | Noise-induced hearing loss (ISO 1999) | [Perception and Hearing](theory-perception.md#noise-induced-hearing-loss-iso-1999) |
| `#sound-intensity-iec-61043` | Sound intensity (IEC 61043) | [Signal Analysis](theory-signal-analysis.md#sound-intensity-iec-61043) |
| `#room-noise-criteria-ansi-s122` | Room noise criteria (ANSI S12.2) | [Rooms and Buildings](theory-rooms-buildings.md#room-noise-criteria-ansi-s122) |
| `#room-and-building-acoustics-iso-18233-iso-3382-iso-16283-iso-10140-en-12354-iso-12999-iso-717-iso-354` | Room and building acoustics (ISO 18233, ISO 3382, ISO 16283, ISO 10140, EN 12354, ISO 12999, ISO 717, ISO 354) | [Rooms and Buildings](theory-rooms-buildings.md#room-and-building-acoustics-iso-18233-iso-3382-iso-16283-iso-10140-en-12354-iso-12999-iso-717-iso-354) |
| `#deterministic-excitation-impulse-response-iso-18233` | Deterministic-excitation impulse response (ISO 18233) | [Rooms and Buildings](theory-rooms-buildings.md#deterministic-excitation-impulse-response-iso-18233) |
| `#schroeder-backward-integration-iso-3382-1-533` | Schroeder backward integration (ISO 3382-1, 5.3.3) | [Rooms and Buildings](theory-rooms-buildings.md#schroeder-backward-integration-iso-3382-1-533) |
| `#regression-windows-and-validity-iso-3382-2-clause-6-annex-bc` | Regression windows and validity (ISO 3382-2, Clause 6, Annex B/C) | [Rooms and Buildings](theory-rooms-buildings.md#regression-windows-and-validity-iso-3382-2-clause-6-annex-bc) |
| `#clarity-definition-and-centre-time-iso-3382-1-annex-a` | Clarity, definition and centre time (ISO 3382-1, Annex A) | [Rooms and Buildings](theory-rooms-buildings.md#clarity-definition-and-centre-time-iso-3382-1-annex-a) |
| `#open-plan-spatial-decay-iso-3382-3-clause-6` | Open-plan spatial decay (ISO 3382-3, Clause 6) | [Rooms and Buildings](theory-rooms-buildings.md#open-plan-spatial-decay-iso-3382-3-clause-6) |
| `#field-insulation-and-weighted-rating-iso-16283-1-iso-717-1` | Field insulation and weighted rating (ISO 16283-1, ISO 717-1) | [Rooms and Buildings](theory-rooms-buildings.md#field-insulation-and-weighted-rating-iso-16283-1-iso-717-1) |
| `#impact-insulation-and-absorption-iso-16283-2-iso-717-2-iso-354` | Impact insulation and absorption (ISO 16283-2, ISO 717-2, ISO 354) | [Rooms and Buildings](theory-rooms-buildings.md#impact-insulation-and-absorption-iso-16283-2-iso-717-2-iso-354) |
| `#laboratory-vs-field-normalization-iso-10140-iso-16283` | Laboratory vs field normalization (ISO 10140, ISO 16283) | [Rooms and Buildings](theory-rooms-buildings.md#laboratory-vs-field-normalization-iso-10140-iso-16283) |
| `#flanking-transmission-prediction-en-12354-12` | Flanking transmission prediction (EN 12354-1/2) | [Rooms and Buildings](theory-rooms-buildings.md#flanking-transmission-prediction-en-12354-12) |
| `#absorption-in-enclosed-spaces-en-12354-6` | Absorption in enclosed spaces (EN 12354-6) | [Rooms and Buildings](theory-rooms-buildings.md#absorption-in-enclosed-spaces-en-12354-6) |
| `#measurement-uncertainty-iso-12999-1` | Measurement uncertainty (ISO 12999-1) | [Rooms and Buildings](theory-rooms-buildings.md#measurement-uncertainty-iso-12999-1) |
| `#outdoor-propagation-and-occupational-exposure-iso-9613-12-iso-9612` | Outdoor propagation and occupational exposure (ISO 9613-1/2, ISO 9612) | [Environment and Transport](theory-environment-transport.md#outdoor-propagation-and-occupational-exposure-iso-9613-12-iso-9612) |
| `#atmospheric-absorption-iso-9613-1` | Atmospheric absorption (ISO 9613-1) | [Environment and Transport](theory-environment-transport.md#atmospheric-absorption-iso-9613-1) |
| `#outdoor-propagation-general-method-iso-9613-2` | Outdoor propagation, general method (ISO 9613-2) | [Environment and Transport](theory-environment-transport.md#outdoor-propagation-general-method-iso-9613-2) |
| `#occupational-noise-exposure-and-uncertainty-iso-9612` | Occupational noise exposure and uncertainty (ISO 9612) | [Environment and Transport](theory-environment-transport.md#occupational-noise-exposure-and-uncertainty-iso-9612) |
| `#sound-power-determination-iso-374437453746-iso-3741-iso-9614-23` | Sound power determination (ISO 3744/3745/3746, ISO 3741, ISO 9614-2/3) | [Environment and Transport](theory-environment-transport.md#sound-power-determination-iso-374437453746-iso-3741-iso-9614-23) |
| `#enveloping-surface-pressure-iso-37443746` | Enveloping-surface pressure (ISO 3744/3746) | [Environment and Transport](theory-environment-transport.md#enveloping-surface-pressure-iso-37443746) |
| `#precision-grade-in-anechoic-rooms-iso-3745` | Precision grade in anechoic rooms (ISO 3745) | [Environment and Transport](theory-environment-transport.md#precision-grade-in-anechoic-rooms-iso-3745) |
| `#reverberation-room-iso-3741` | Reverberation room (ISO 3741) | [Environment and Transport](theory-environment-transport.md#reverberation-room-iso-3741) |
| `#intensity-scanning-iso-9614-2` | Intensity scanning (ISO 9614-2) | [Environment and Transport](theory-environment-transport.md#intensity-scanning-iso-9614-2) |
| `#precision-intensity-scanning-iso-9614-3` | Precision intensity scanning (ISO 9614-3) | [Environment and Transport](theory-environment-transport.md#precision-intensity-scanning-iso-9614-3) |
| `#surface-scattering-and-diffusion-iso-17497-1-iso-17497-2` | Surface scattering and diffusion (ISO 17497-1, ISO 17497-2) | [Rooms and Buildings](theory-rooms-buildings.md#surface-scattering-and-diffusion-iso-17497-1-iso-17497-2) |
| `#random-incidence-scattering-coefficient-iso-17497-1` | Random-incidence scattering coefficient (ISO 17497-1) | [Rooms and Buildings](theory-rooms-buildings.md#random-incidence-scattering-coefficient-iso-17497-1) |
| `#directional-diffusion-coefficient-iso-17497-2` | Directional diffusion coefficient (ISO 17497-2) | [Rooms and Buildings](theory-rooms-buildings.md#directional-diffusion-coefficient-iso-17497-2) |
| `#in-situ-road-surface-absorption-iso-13472-1-iso-13472-2` | In-situ road surface absorption (ISO 13472-1, ISO 13472-2) | [Rooms and Buildings](theory-rooms-buildings.md#in-situ-road-surface-absorption-iso-13472-1-iso-13472-2) |
| `#acoustic-material-characterisation-iso-11654-iso-9053-12-iso-10534-12-astm-e2611` | Acoustic material characterisation (ISO 11654, ISO 9053-1/2, ISO 10534-1/2, ASTM E2611) | [Rooms and Buildings](theory-rooms-buildings.md#acoustic-material-characterisation-iso-11654-iso-9053-12-iso-10534-12-astm-e2611) |
| `#weighted-sound-absorption-iso-11654` | Weighted sound absorption (ISO 11654) | [Rooms and Buildings](theory-rooms-buildings.md#weighted-sound-absorption-iso-11654) |
| `#airflow-resistance-iso-9053-12` | Airflow resistance (ISO 9053-1/2) | [Rooms and Buildings](theory-rooms-buildings.md#airflow-resistance-iso-9053-12) |
| `#impedance-tube-iso-10534-1-iso-10534-2-astm-e2611` | Impedance tube (ISO 10534-1, ISO 10534-2, ASTM E2611) | [Rooms and Buildings](theory-rooms-buildings.md#impedance-tube-iso-10534-1-iso-10534-2-astm-e2611) |
| `#human-vibration-iso-8041-1-iso-2631-12-iso-5349-12-directive-200244ec` | Human vibration (ISO 8041-1, ISO 2631-1/2, ISO 5349-1/2, Directive 2002/44/EC) | [Vibration](theory-vibration.md#human-vibration-iso-8041-1-iso-2631-12-iso-5349-12-directive-200244ec) |
| `#multiple-shocks-iso-2631-5` | Multiple shocks (ISO 2631-5) | [Vibration](theory-vibration.md#multiple-shocks-iso-2631-5) |
| `#measurement-uncertainty-isoiec-guide-98-3--gum-and-supplement-1` | Measurement uncertainty (ISO/IEC Guide 98-3 — GUM and Supplement 1) | [Signal Analysis](theory-signal-analysis.md#measurement-uncertainty-isoiec-guide-98-3--gum-and-supplement-1) |
