← [Documentation index](README.md)

# Objective audibility of tones in noise (ISO/PAS 20065)

A steady tone embedded in broadband noise stands out when it rises audibly above
the noise that would otherwise mask it — the objective precondition for the tonal
penalties applied in noise assessment. **ISO/PAS 20065:2016** is the *engineering
method* that quantifies this audibility: from a narrow-band FFT spectrum it
derives, for every prominent tone, the **audibility** `ΔL` — how many decibels
the tone level exceeds the masking threshold of the surrounding noise. (Whether a
tone is *annoying* is a separate, downstream rating judgement.) It is the
detailed method that **ISO 1996-2:2017** defers to (the simpler Annex C route
lives in [environmental measurement](building-acoustics.md)); the mean audibility
`ΔL` it produces feeds the ISO 1996-2 tonal adjustment `Kt`.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tone_audibility_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tone_audibility.svg" alt="Per-tone audibility ΔL of the nine tones of the ISO/PAS 20065 Annex E combustion-engine spectrum, with the decisive tone at 137.3 Hz highlighted and the ΔL = 0 dB audibility threshold marked" width="82%"></picture>

## 1. The critical band about the tone

Each tone of frequency `fT` is evaluated inside a critical band whose width is
(Formula 2)

$$
\Delta f_c = 25.0 + 75.0\left(1.0 + 1.4\left(\tfrac{f_T}{1000}\right)^{2}\right)^{0.69}\ \mathrm{Hz}.
$$

With a geometric placement of the corner frequencies about the tone
(Formulae 3–5), `√(f₁·f₂) = fT` and `f₂ − f₁ = Δfc`, so
`f₁ = −Δfc/2 + √(Δfc² + 4·fT²)/2` and `f₂ = f₁ + Δfc`.

```python
import phonometry as ph

print(round(ph.critical_bandwidth_engineering(137.3), 2))   # 101.36 Hz
f1, f2 = ph.critical_band_corners(137.3)
print(round(f1, 2), round(f2, 2))                            # 95.67 197.04
```

## 2. Audibility of a tone

The mean narrow-band level `LS` of the masking noise (Formula 6, an iterative
energy average of the lines in the critical band) and the tone level `LT`
(Formula 8, the energy sum of the tonal lines) are derived from the narrow-band
spectrum — `mean_narrowband_level` and `tone_level` do this directly (see §4).
The critical-band level of the masking noise spreads `LS` over the critical
bandwidth (Formula 12), the masking index accounts for the ear (Formula 13) and
the audibility is their difference (Formula 14):

$$
L_G = L_S + 10\lg\!\frac{\Delta f_c}{\Delta f}, \qquad
a_v = -2 - \lg\!\Big[1 + \big(\tfrac{f}{502}\big)^{2.5}\Big], \qquad
\Delta L = L_T - L_G - a_v .
$$

A supplied tone is *audible* when `ΔL > 0`. `Δf` is the line spacing (frequency
resolution); the energy sums carry a window correction of `10·lg(Δf/Δfe)`
(`−1.76 dB` for the recommended Hanning window, `Δfe = 1.5·Δf`).

```python
import phonometry as ph

# ISO/PAS 20065 Annex E, tone at 137.3 Hz (Δf = 2.7 Hz):
#   LS = 49.22 dB (Formula 6), LT = 67.96 dB (Formula 8).
print(round(ph.tone_audibility(67.96, 49.22, 137.3, 2.7), 2))   # 5.01 dB
print(round(ph.masking_index(137.3), 2))                        # -2.02 dB
```

## 3. Decisive and mean audibility

The **decisive** audibility of one narrow-band spectrum is the largest tone
audibility in it (clause 5.3.8). Over `J` staggered spectra the **mean
audibility** is their energy mean (Formula 20); a spectrum in which no tone is
found contributes `ΔLj = −10 dB` (Formula 21). `assess_tones` applies the whole
chain to a spectrum's tones and reports the decisive tone.

```python
import phonometry as ph

# Annex E combustion-engine spectrum 1: nine tones (fT, LT, LS), Δf = 2.7 Hz.
fT = [118.4, 137.3, 158.8, 314.9, 433.4, 592.2, 629.8, 643.3, 1582.7]
LT = [64.56, 67.96, 68.63, 68.50, 73.17, 78.31, 75.00, 79.75, 71.07]
LS = [48.91, 49.22, 50.50, 52.85, 58.29, 59.53, 59.71, 61.98, 54.16]
res = ph.assess_tones(fT, LT, LS, 2.7)
print(round(res.decisive_audibility, 2), res.decisive_frequency)  # 5.01 137.3

# Mean audibility of the five measured spectra (Table E.3 decisive values):
print(round(ph.mean_audibility([9.18, 6.04, 7.46, 2.67, 7.17]), 2))  # 6.98 dB
```

## 4. From the narrow-band spectrum

Given the FFT lines of the critical band about a tone, `mean_narrowband_level`
runs the iterative Formula 6 procedure (energy average, dropping any line more
than 6 dB above the running `LS`, until stable within ±0.005 dB or fewer than
five lines remain each side — Annex D) and `tone_level` sums the tonal lines
contiguous with the peak (above both `LS + 6 dB` and `L_peak − 10 dB`). Both
carry the −1.76 dB Hanning bandwidth correction.

```python
import phonometry as ph

# Annex E Table E.1: the 38 lines of the 137.3 Hz critical band (Δf = 2.7 Hz).
freqs = [96.9, 99.6, 102.3, 105.0, 107.7, 110.4, 113.0, 115.7, 118.4, 121.1,
         123.8, 126.5, 129.2, 131.9, 134.6, 137.3, 140.0, 142.7, 145.3, 148.0,
         150.7, 153.4, 156.1, 158.8, 161.5, 164.2, 166.9, 169.6, 172.3, 175.0,
         177.6, 180.3, 183.0, 185.7, 188.4, 191.1, 193.8, 196.5]
levels = [49.40, 50.68, 50.09, 53.37, 44.47, 50.91, 51.41, 59.40, 64.54, 57.57,
          51.02, 50.76, 59.93, 62.94, 58.49, 65.87, 62.66, 50.25, 51.32, 52.30,
          52.58, 53.15, 67.04, 67.27, 57.40, 57.17, 52.56, 51.39, 52.49, 47.68,
          51.26, 49.03, 61.42, 59.52, 48.43, 50.84, 48.20, 55.95]

ls = ph.mean_narrowband_level(levels, freqs, 137.3)
lt = ph.tone_level(levels, freqs, 137.3, ls)
print(round(ls, 2), round(lt, 2))                  # 49.22 67.96
print(round(ph.tone_audibility(lt, ls, 137.3, 2.7), 2))   # 5.01 dB
```

## 5. Whole-spectrum detection

`analyze_spectrum` runs the full front-end over a spectrum — mean narrow-band
level per line, peak detection (Clause 5.3.8 Step 1, a tone cannot sit on a
slope), tone level, the distinctness test (Clause 5.3.4: bandwidth
`≤ 26·(1 + 0.001·fT)` Hz and edge steepness `≥ 24 dB`) and audibility — and
returns the distinct, audible tones. `combined_tone_level` performs the
multi-tone "FG" combination (Formula 17) for tones sharing a critical band.

```python
import phonometry as ph

# Same Table E.1 spectrum as above.
res = ph.analyze_spectrum(levels, freqs, 2.7)
print([round(f, 1) for f in res.tone_frequencies])   # [118.4, 137.3, 158.8]

# FG combination of the three tones (LS from the standard's Table E.2):
lt_fg = ph.combined_tone_level(levels, freqs, [118.4, 137.3, 158.8],
                               [48.91, 49.22, 50.50])
print(round(lt_fg, 2))                                # 72.15
```

Reproducing a *decisive* audibility exactly needs the **complete** narrow-band
spectrum: Table E.1 is truncated to the 137.3 Hz critical band, so the 158.8 Hz
tone's mean narrow-band level is under-estimated from it (the algorithm itself
matches the parent standard DIN 45681:2005-03 reference program). The peak
detection and FG combination above are verified against the Annex E worked
example (the three tone frequencies and `LT = 72.15 dB`).

### 5.1 Two tones below 1000 Hz

When **exactly two** tones share a critical band and both lie below 1000 Hz, the
ear can still tell them apart — so they are rated *separately* rather than
FG-combined — if their frequency difference `|fT1 − fT2|` (Formula 18) exceeds

```text
fD = 21·10^(1.2·|lg(fT/212)|^1.8)  Hz     (Formula 19, 88 Hz < fT < 1000 Hz)
```

evaluated at the more prominent tone `fT` (the larger audibility `ΔL`). The
threshold bottoms out at `21 Hz` at `fT = 212 Hz` and grows on either side.
`two_tone_separation_frequency` gives `fD`; `resolve_tones_separately` applies
the decision.

```python
import phonometry as ph

ph.two_tone_separation_frequency(212.0)             # 21.0 Hz (minimum)
ph.resolve_tones_separately(200.0, 260.0, 3.0, 2.0) # True  → rate separately
ph.resolve_tones_separately(118.4, 137.3, 4.0, 5.0) # False → combine (Δf < fD)
```

> **No numeric oracle.** No ISO/PAS 20065 worked example exercises this branch —
> the Annex E band groups *three* tones, so the "exactly two tones" rule never
> fires there. The formula and decision are implemented clean-room from the text
> and verified against the **DIN 45681:2005-03** Annex J reference program
> (`fD = 21 * 10 ^ (1.2 * Abs(Log(fT / 212) / Log(10)) ^ 1.8)`). Reassuringly,
> evaluated at the Annex E tones the threshold (`≈ 24 Hz` at 137.3 Hz) keeps
> them combined, consistent with that example's FG grouping.

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import phonometry as ph

fT = [118.4, 137.3, 158.8, 314.9, 433.4, 592.2, 629.8, 643.3, 1582.7]
LT = [64.56, 67.96, 68.63, 68.50, 73.17, 78.31, 75.00, 79.75, 71.07]
LS = [48.91, 49.22, 50.50, 52.85, 58.29, 59.53, 59.71, 61.98, 54.16]
res = ph.assess_tones(fT, LT, LS, 2.7)
res.plot()
plt.tight_layout(); plt.show()
```

</details>

---

**Standards.** ISO/PAS 20065:2016, *Acoustics — Objective method for assessing
the audibility of tones in noise — Engineering method*: the critical bandwidth
`Δfc` (Formula 2) and its corner frequencies (Formulae 3–5), the critical-band
level `LG` (Formula 12), the masking index `av` (Formula 13), the audibility
`ΔL = LT − LG − av` (Formula 14) and the energy-mean mean audibility
(Formula 20). The mean narrow-band level `LS` (Formula 6, iterative Annex D) and
tone level `LT` (Formula 8) are computed from the critical-band spectrum, and
`analyze_spectrum` adds peak detection (Clause 5.3.8) with the distinctness
criteria (Clause 5.3.4) and the multi-tone `FG` combination (Formula 17), plus
the separate evaluation of two tones below 1000 Hz (Formulae 18/19). The
−1.76 dB Hanning bandwidth correction, the iterative masking-level procedure and
the detection/combination logic are confirmed against the parent standard
**DIN 45681:2005-03** (its Annex J reference program). Conformance is anchored on
the Annex E combustion-engine worked example (Tables E.1/E.2/E.3): `LS` and `LT`
from the spectrum, tone detection and the `FG` combined level, the per-tone
audibility, the masking index and the mean audibility of the five spectra.
