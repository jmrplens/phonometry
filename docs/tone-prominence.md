← [Documentation index](README.md)

# Prominent Discrete Tones (ECMA-418-1)

Tonal components in machinery noise are far more annoying than their level
suggests. ECMA-418-1:2024 (referenced by ECMA-74 Annex D) gives two FFT-based
methods to decide whether a discrete tone is *prominent*:
`tone_to_noise_ratio()` compares the tone level with the masking noise in its
critical band (clause 11), and `prominence_ratio()` compares the critical band
centred on the tone with the two contiguous bands (clause 12). Both return a
structured verdict against the frequency-dependent prominence criteria.

## 1. Tone-to-noise ratio and prominence ratio

```python
import numpy as np
from phonometry import tone_to_noise_ratio, prominence_ratio

fs = 48000
rng = np.random.default_rng(0)
t = np.arange(fs) / fs
x = np.sin(2 * np.pi * 1000 * t) + 0.05 * rng.standard_normal(fs)  # 1 kHz tone in noise
tnr = tone_to_noise_ratio(x, fs)            # highest peak, or tone_freq=...
pr = prominence_ratio(x, fs, tone_freq=1000.0)
print(tnr.ratio_db, tnr.criterion_db, tnr.prominent)
```

The methods hinge on the **critical band** — the ear's analysis bandwidth,
$\Delta f_c = 25 + 75\ [1 + 1.4(f/1000)^2]^{0.69}$ Hz (162 Hz at 1 kHz): a
tone is masked only by the noise *inside* its critical band, so both ratios
compare the tone against exactly that noise, not the whole spectrum.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum.svg" alt="Averaged spectrum of a tone in noise with the critical band shaded and the tone-to-noise ratio annotated against its prominence criterion" width="80%"></picture>

A TNR above $8 + 8.33\log_{10}(1000/f_t)$ dB (8 dB from 1 kHz up) classifies
the tone as *prominent*; the PR criterion is $9 + 10\log_{10}(1000/f_t)$ dB.
Low frequencies get higher thresholds because wider relative bands mask more.

## 2. Where to measure (ECMA-74) and practice

ECMA-74 (which delegates its tone assessments to ECMA-418-1) also fixes where to measure around a device — context only: phonometry implements the ECMA-418-1 assessments, not the ECMA-74 Annex D measurement procedure:

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_tonality_positions_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_tonality_positions.svg" alt="ECMA-74 emission measurement positions: seated operator microphone at 0.25 m and 1.20 m, and the four bystander positions at 1 m" width="92%"></picture>

Proximate secondary tones in the same critical band are combined per
clause 11.6; for harmonic complexes assess each component (`tone_freq=`).
Both methods work on Hann-windowed, RMS-averaged spectra and need no absolute
calibration (the ratios are level differences).

### `tone_to_noise_ratio()` / `prominence_ratio()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `x` | 1D array | any (uncalibrated OK) | ≥ `fs/resolution_hz` samples | Ratios are level differences: calibration cancels out |
| `fs` | int | Hz | > 0 | |
| `tone_freq` | float, optional | Hz | 89.1–11 200; default `None` | `None` assesses the highest peak in the range of interest |
| `resolution_hz` | float | Hz | > 0; default `1.0` | Tone band must stay within 15 % of the critical band (clause 11.2) |

Both return a `ToneAssessment(frequency, ratio_db, criterion_db, prominent)`.

## See also

- [Levels](levels.md) — the ISO 1996-1 rating levels whose tonal adjustments
  (Table A.1) these prominence verdicts justify objectively.
- [Psychoacoustics](psychoacoustics.md) — the ECMA-418-2 psychoacoustic
  tonality T in tu_HMS, the hearing-model counterpart of these FFT ratios.
- [Impulsive-sound prominence](impulse-prominence.md) — the NT ACOU 112
  counterpart for impulsive (rather than tonal) character.
- [Theory](theory.md) — the critical-band model and criteria derivation.

---

**Standards.** ECMA-418-1:2024 (3rd edition), *Psychoacoustic metrics for ITT
equipment — Part 1: Prominent discrete tones* — the tone-to-noise ratio
(clause 11), the prominence ratio (clause 12), the critical-band model and the
frequency-dependent prominence criteria.
