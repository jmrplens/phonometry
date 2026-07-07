← [Documentation index](README.md)

# Integrated and Statistical Levels

Environmental noise metrics computed directly from the raw (calibrated) signal.

## Leq and LAeq

The equivalent continuous level integrates the squared pressure over the
measurement time:

$$
L_{eq} = 10\log_{10}\left(\frac{1}{T}\int_0^T \frac{p^2(t)}{p_0^2}\ dt\right) \text{ dB}, \qquad p_0 = 20\ \mu\text{Pa}
$$

and $L_{Aeq}$ is the same integral after A-weighting the signal. $L_N$ is the
level exceeded $N\ \%$ of the time — the $(100-N)$-th percentile of the
time-weighted level distribution.

```python
from phonometry import leq, laeq

# Equivalent continuous level of the whole recording
level = leq(signal, calibration_factor=sensitivity)

# A-weighted Leq (the standard environmental noise metric)
la = laeq(signal, fs, calibration_factor=sensitivity)
```

Both accept 1D signals (returning a scalar) or 2D `[channels, samples]` arrays
(returning one level per channel), and support `dbfs=True` for digital
full-scale analysis (calibration does not apply in dBFS mode).

Why the *energy* mean and not the arithmetic mean of dB values? Because sound
doses add as energy: two periods at 60 dB and 80 dB do not average to 70 dB —
the 80 dB half dominates and $L_{eq}$ = 77 dB. Averaging decibels directly
underestimates every fluctuating noise. $L_{eq}$ is the level of the *steady*
sound carrying the same energy as the real, fluctuating one, which is why
regulations are written in terms of it.

### `leq()` / `laeq()` parameters

| Parameter | Type / shape | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `x` | 1D or 2D array | digital units (or Pa if calibrated) | non-empty | 2D is `[channels, samples]`; returns one level per channel |
| `fs` | int | Hz | > 0 (`laeq` only) | `leq` needs no sample rate (pure RMS integral) |
| `calibration_factor` | float | Pa per digital unit | default `1.0` | From `calculate_sensitivity()` |
| `dbfs` | bool | — | default `False` | `True`: 0 dBFS = full-scale RMS sine; ignores calibration |

## Percentile levels (LN)

`ln_levels` computes statistical levels from the time-weighted envelope:
**L10** is the level exceeded 10 % of the time (event peaks), **L50** the median,
**L90** the background level.

```python
from phonometry import ln_levels

stats = ln_levels(signal, fs, n=(10, 50, 90), weighting="A")
print(f"LA10={stats[10]:.1f}  LA50={stats[50]:.1f}  LA90={stats[90]:.1f} dB")
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ln_levels_example_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ln_levels_example.png" alt="Fast level history of fluctuating noise with the L10, L50 and L90 statistical levels marked" width="80%"></picture>

*L10 tracks the event peaks, L50 the median level and L90 the background.*

Options: `mode` selects the envelope ballistics (`'fast'`, `'slow'`,
`'impulse'`), `weighting` applies A/C weighting first, and
`calibration_factor`/`dbfs` behave as in `leq`. The integrator attack transient
(~2τ) is discarded before taking percentiles.

Formally, $L_N$ is the $(100-N)$-th percentile of the distribution of the
time-weighted level: the recording is first turned into a level-vs-time
envelope (Fast by default), and $L_{10}$ is the envelope value exceeded 10 %
of the time. That makes the *ballistics choice part of the metric*: an
$L_{10}$ from a Slow envelope is systematically lower than from a Fast one on
impulsive noise, so regulations always name the time weighting.

### `ln_levels()` parameters

| Parameter | Type / shape | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `x` | 1D or 2D array | digital units | non-empty | 2D returns per-channel dicts |
| `fs` | int | Hz | > 0 | Needed by the envelope detector |
| `n` | tuple of ints | % | default `(10, 50, 90)` | Any exceedance percentages, e.g. `(1, 5, 95)` |
| `mode` | str | — | `'fast'` (default), `'slow'`, `'impulse'` | IEC 61672-1 ballistics of the envelope |
| `weighting` | str or None | — | `'A'`, `'C'`, `'G'`, `'Z'`, `None` (default) | Frequency weighting before the envelope |
| `calibration_factor` / `dbfs` | float / bool | — | as `leq` | Same semantics as in `leq()` |

## Peak, event and occupational metrics

```python
from phonometry import lc_peak, sel, sound_exposure, lex_8h

# C-weighted peak (IEC 61672-1 §5.13) - occupational action limits use this
peak = lc_peak(signal, fs, calibration_factor=sensitivity)

# Sound exposure level: single-event level normalized to 1 s (LAE)
lae = sel(event, fs, weighting="A", calibration_factor=sensitivity)

# Daily noise dose (IEC 61252): exposure in Pa²·h and LEX,8h / LEP,d
E = sound_exposure(shift_sample, fs, duration_hours=8, calibration_factor=sensitivity)
lex = lex_8h(shift_sample, fs, duration_hours=8, calibration_factor=sensitivity)
```

`lc_peak` is verified against the one-cycle/half-cycle reference responses of
IEC 61672-1:2013 Table 5, `sel` against the Table 4 LAE toneburst column, and
the dose functions against the IEC 61252 anchors (3.2 Pa²h ↔ exactly 90 dB).
With `duration_hours`, the input is treated as a representative sample of that
exposure period; without it, the input is the whole event.

### SEL: comparing events of different duration

A 4 s train pass-by and a 30 s one cannot be compared by their $L_{Aeq}$
alone — the longer event delivers more energy at the same level. The **sound
exposure level** compresses the *whole* event energy into exactly one second:

$$
L_E = L_{eq,T} + 10\log_{10}\frac{T}{T_0}, \qquad T_0 = 1\ \text{s}
$$

so events of any duration become directly comparable, and $N$ identical
events sum as $+10\log_{10}N$. This is the building block of airport and
railway noise models.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_concept_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_concept.png" alt="A vehicle pass-by level history with its Leq over the whole event and the equal-energy one-second SEL block" width="80%"></picture>

### Noise dose: sound exposure and LEX,8h

Occupational regulations limit the daily *dose*, not the level. IEC 61252
expresses it as **sound exposure** $E$ in pascal-squared-hours — the time
integral of the squared A-weighted pressure — and the equivalent
**normalized 8 h level**:

$$
E = \int_0^T p_A^2(t)\ dt \quad [\text{Pa}^2\text{h}], \qquad
L_{EX,8h} = 10\log_{10}\frac{E}{8\ \text{h} \cdot p_0^2}
$$

The anchor worth memorizing: **3.2 Pa²h ⇔ exactly 90 dB over 8 h** (the CI
suite enforces it). Half the dose is −3 dB; double duration at the same level
is +3 dB.

### Peak / event / dose parameters

| Function | Key parameters | Returns | Standard anchor |
| :--- | :--- | :--- | :--- |
| `lc_peak(x, fs, calibration_factor=1.0, dbfs=False)` | `dbfs=True` references full-scale *peak* (1.0), not RMS | LCpeak [dB] | IEC 61672-1 §5.13, Table 5 tone bursts |
| `sel(x, fs, weighting=None, ...)` | `weighting='A'` gives LAE | SEL [dB] | IEC 61672-1 Table 4 (LAE column) |
| `sound_exposure(x, fs, duration_hours=None, ...)` | `duration_hours` treats `x` as a sample of that period | E [Pa²h] | IEC 61252 |
| `lex_8h(x, fs, duration_hours=None, ...)` | same sampling semantics | LEX,8h [dB] | IEC 61252 (≡ LEP,d) |

## Loudness level of pure tones (ISO 226:2023)

The normal equal-loudness-level contours relate the SPL of a pure tone to its
perceived *loudness level* in phons (the SPL of an equally loud 1 kHz tone).
`equal_loudness_contour(phon)` evaluates ISO 226:2023 Formula (1) at the 29
preferred third-octave frequencies of Table 1, `loudness_level(spl, frequency)`
is the exact inverse (Formula 2), and `hearing_threshold()` returns the
threshold-of-hearing column:

```python
from phonometry import equal_loudness_contour, loudness_level

freqs, spl = equal_loudness_contour(40.0)   # the classic 40-phon contour
phon = loudness_level(73.0, 63.0)           # 73 dB @ 63 Hz -> 40 phon
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/equal_loudness_contours_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/equal_loudness_contours.png" alt="ISO 226:2023 normal equal-loudness-level contours from 20 to 90 phon with the hearing threshold curve" width="80%"></picture>

Validity per clause 4.1: 20-90 phon (80 phon above 4 kHz); the implementation
is verified against the Annex B tables in CI. Note this is the loudness of
*pure tones* - loudness of arbitrary signals (ISO 532 sones) is a different,
upcoming feature.

## Prominent discrete tones (ECMA-418-1)

Tonal components in machinery noise are far more annoying than their level
suggests. ECMA-418-1:2024 (referenced by ECMA-74 Annex D) gives two FFT-based
methods to decide whether a discrete tone is *prominent*:
`tone_to_noise_ratio()` compares the tone level with the masking noise in its
critical band (clause 11), and `prominence_ratio()` compares the critical band
centred on the tone with the two contiguous bands (clause 12). Both return a
structured verdict against the frequency-dependent prominence criteria:

```python
from phonometry import tone_to_noise_ratio, prominence_ratio

tnr = tone_to_noise_ratio(x, fs)            # highest peak, or tone_freq=...
pr = prominence_ratio(x, fs, tone_freq=1000.0)
print(tnr.ratio_db, tnr.criterion_db, tnr.prominent)
```


The methods hinge on the **critical band** — the ear's analysis bandwidth,
$\Delta f_c = 25 + 75\ [1 + 1.4(f/1000)^2]^{0.69}$ Hz (162 Hz at 1 kHz): a
tone is masked only by the noise *inside* its critical band, so both ratios
compare the tone against exactly that noise, not the whole spectrum.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_spectrum.png" alt="Averaged spectrum of a tone in noise with the critical band shaded and the tone-to-noise ratio annotated against its prominence criterion" width="80%"></picture>

A TNR above $8 + 8.33\log_{10}(1000/f_t)$ dB (8 dB from 1 kHz up) classifies
the tone as *prominent*; the PR criterion is $9 + 10\log_{10}(1000/f_t)$ dB.
Low frequencies get higher thresholds because wider relative bands mask more.

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

## Environmental noise: Lden, Ldn and rating levels (ISO 1996-1)

Regulatory noise assessment weights evenings and nights more heavily.
`lden()` implements the day-evening-night level of ISO 1996-1:2016 (3.6.4:
+5 dB evening, +10 dB night, default 12/4/8 h periods — adjustable, since
countries define them differently), `ldn()` the day-night variant (3.6.5),
and `composite_rating_level()` the general whole-day composite of clause 6.5
(Formulae 5-6) for arbitrary periods with source or character adjustments
(Table A.1: e.g. +5 dB regular impulsive, +12 dB highly impulsive, +3 to
+6 dB prominent tones):

```python
from phonometry import lden, composite_rating_level

l = lden(63.2, 58.1, 51.4)                      # from LAeq per period
r = composite_rating_level([(63.2, 12, 0.0),    # day
                            (58.1, 4, 5.0),     # evening (+5)
                            (51.4, 8, 10.0)])   # night  (+10) == lden
```


<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/lden_profile_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/lden_profile.png" alt="Synthetic 24-hour urban LAeq profile with day, evening and night bands, the +5 and +10 dB weighted period levels and the resulting Lden" width="80%"></picture>

### `lden()` / `ldn()` / `composite_rating_level()` parameters

| Function | Key parameters | Notes |
| :--- | :--- | :--- |
| `lden(lday, levening, lnight, hours=(12, 4, 8))` | period LAeq values [dB]; `hours` must sum to 24 | +5 dB evening, +10 dB night (3.6.4) |
| `ldn(lday, lnight, hours=(15, 9))` | | +10 dB night (3.6.5) |
| `composite_rating_level(periods)` | iterable of `(level_db, hours, adjustment_db)`; hours positive, finite and summing to 24 | General Formulae (5)-(6); adjustments per Table A.1 |

Combine with `laeq()` per time period to go from recordings to Lden, and with
`tone_to_noise_ratio()` / `prominence_ratio()` to justify tonal adjustments.

## Octave Spectrogram (levels over time)

Short-time fractional-octave analysis: one level per band per window,
time-aligned across bands.

```python
from phonometry import OctaveFilterBank

bank = OctaveFilterBank(fs=48000, fraction=3)
levels, freq, times = bank.spectrogram(signal, window_time=0.125, overlap=0.5)
# levels: (bands, frames) — ready for pcolormesh(times, freq, levels)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/spectrogram_example_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/spectrogram_example.png" alt="One-third-octave spectrogram of a logarithmic sweep with two tone bursts" width="80%"></picture>

*A logarithmic sweep plus two tone bursts, resolved in time and in standardized
1/3-octave bands.*

- Multichannel input `(channels, samples)` returns `(channels, bands, frames)`.
- `times` holds each window's center in seconds.
- `mode='peak'` gives per-window peak-holding levels instead of RMS.
- `zero_phase=True` filters bands forward-backward so per-band group delay does
  not skew the frames (offline analysis only).

### `OctaveFilterBank.spectrogram()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `x` | 1D or 2D array | digital units | non-empty | 2D returns `(channels, bands, frames)` |
| `window_time` | float | s | > 0; default `0.125` | Frame length (0.125 s mirrors Fast) |
| `overlap` | float | — | 0 ≤ overlap < 1; default `0.5` | Fraction of window overlap (0 = none) |
| `mode` | str | — | `'rms'` (default) or `'peak'` | Per-window detector |
| `zero_phase` | bool | — | default `False` | Forward-backward filtering (offline only) |
| `calibration_factor` / `dbfs` | — | — | constructor-only | Set on `OctaveFilterBank(...)`, not per call |

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
mesh = ax.pcolormesh(times, freq, levels, shading="auto")
ax.set_yscale("log")
ax.set_xlabel("Time [s]")
ax.set_ylabel("Frequency [Hz]")
fig.colorbar(mesh, label="Level [dB]")
```

See [Calibration and dBFS](calibration.md) to convert digital units to physical
SPL, and [Time Weighting](time-weighting.md) for the envelope details.
