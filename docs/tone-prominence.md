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
tone is masked only by the noise *inside* its critical band, so both methods
focus on that band rather than the whole spectrum, but they use it
differently. The tone-to-noise ratio works within the band, separating its
spectral lines into tone and noise and subtracting their levels (clause 11,
Formulae 9–11); the prominence ratio instead compares the *whole* band centred
on the tone with the mean of its two contiguous critical bands (clause 12,
Formula 23):

$$
\mathrm{TNR} = L_t - L_n, \qquad
\mathrm{PR} = 10\,\lg\!\frac{W_M}{\tfrac{1}{2}(W_L + W_U)}\ \text{dB},
$$

where $L_t$ is the tone level (the energy sum of the tonal lines above the
band-edge baseline, Formula 9), $L_n$ the level of the masking noise that
remains in the critical band, rescaled to the full critical bandwidth
(Formulae 10–11), and $W_M$, $W_L$, $W_U$ the powers in the middle, lower and
upper critical bands (below $f_t = 171.4$ Hz the truncated lower band is
rescaled to a 100 Hz bandwidth, Formula 24).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum.svg" alt="Averaged spectrum of a tone in noise with the critical band shaded and the tone-to-noise ratio annotated against its prominence criterion" width="80%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch
from phonometry import tone_to_noise_ratio

fs = 48000
rng = np.random.default_rng(21)
t = np.arange(30 * fs) / fs
x = (np.sqrt(2) * 0.1 * np.sin(2 * np.pi * 1000 * t)
     + 0.05 * rng.standard_normal(t.size))
res = tone_to_noise_ratio(x, fs)

# Averaged 1 Hz Hann spectrum (the clause 11.1 front end) and the
# critical band about the detected tone (edges approximated as +/- dfc/2):
f, p = welch(x, fs, window="hann", nperseg=fs, scaling="spectrum")
dfc = 25 + 75 * (1 + 1.4 * (res.frequency / 1000) ** 2) ** 0.69
sel = (f > 700) & (f < 1400)
plt.plot(f[sel], 10 * np.log10(p[sel]))
plt.axvspan(res.frequency - dfc / 2, res.frequency + dfc / 2, alpha=0.15)
plt.title(f"TNR = {res.ratio_db:.1f} dB (criterion {res.criterion_db:.1f} dB)")
plt.xlabel("Frequency [Hz]"); plt.ylabel("Bin power [dB]")
plt.show()
```

</details>

A TNR at or above $8 + 8.33\log_{10}(1000/f_t)$ dB below 1 kHz (a flat 8 dB for
$f_t \ge 1$ kHz) classifies the tone as *prominent*; the PR criterion is
$9 + 10\log_{10}(1000/f_t)$ dB below 1 kHz and 9 dB from there up, likewise
applied with $\ge$. Low frequencies get higher thresholds because wider
relative bands mask more.

**When the two ratios disagree.** Near the criteria the verdicts can differ,
because each ratio is fragile in a different situation. TNR has to *split*
the critical band into tonal and noise lines first, so it degrades when that
separation is ambiguous — a tone riding a steep noise slope, or closely
spaced components whose skirts overlap. PR needs no separation, which makes
it the robust, automatable choice when **several tones share the critical
band** (they all land in $W_M$); in exchange it reads low when a
*neighbouring* band also carries a tone (the flanking bands are then not
noise) and is biased on sharply sloping spectra, where the two flanking
bands no longer estimate the masking at the tone. In practice: prefer TNR
for a clean, isolated tone, prefer PR for multi-tone complexes sharing a
band, and report both when they straddle their criteria.

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
- [Sound Quality Metrics](sound-quality.md) — the ECMA-418-2 psychoacoustic
  tonality T in tu_HMS, the hearing-model counterpart of these FFT ratios.
- [Impulsive-sound prominence](impulse-prominence.md) — the NT ACOU 112
  counterpart for impulsive (rather than tonal) character.
- [Theory](theory-perception.md) — the critical-band model and criteria derivation.
- API reference: [`psychoacoustics.tonality`](https://jmrplens.github.io/phonometry/reference/api/psychoacoustics/tonality/).

## References

- Ecma International. (2024). *ECMA-418-1: Psychoacoustic metrics for ITT
  equipment — Part 1: Prominent discrete tones* (3rd ed.).
  [Free PDF](https://ecma-international.org/wp-content/uploads/ECMA-418-1_3rd_edition_december_2024.pdf).
  The implemented standard, freely downloadable: the TNR (clause 11) and PR
  (clause 12) methods, the critical-band model and the prominence criteria of
  section 1.
- Ecma International. (2025). *ECMA-74: Measurement of airborne noise emitted
  by information technology and telecommunications equipment* (22nd ed.).
  [Free PDF](https://ecma-international.org/wp-content/uploads/ECMA-74_22nd_edition_december_2025.pdf).
  The parent emission standard, freely downloadable: the operator/bystander
  measurement positions of section 2, with Annex D delegating the tone
  assessments to ECMA-418-1.

---

**Standards.** ECMA-418-1:2024 (3rd edition), *Psychoacoustic metrics for ITT
equipment — Part 1: Prominent discrete tones* — the tone-to-noise ratio
(clause 11), the prominence ratio (clause 12), the critical-band model and the
frequency-dependent prominence criteria.
