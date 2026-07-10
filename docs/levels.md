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
import numpy as np
from phonometry import leq, laeq

# recording: a calibrated microphone capture (Pa) — recorded through your measurement chain. Synthesized here so the guide runs standalone.
fs = 48000
recording = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)
sensitivity = 1.0                                    # calibration_factor (see Calibration)

# Equivalent continuous level of the whole recording
level = leq(recording, calibration_factor=sensitivity)

# A-weighted Leq (the standard environmental noise metric)
la = laeq(recording, fs, calibration_factor=sensitivity)
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
| `calibration_factor` | float | Pa per digital unit | default `1.0` | From `sensitivity()` |
| `dbfs` | bool | — | default `False` | `True`: 0 dBFS = full-scale RMS sine; ignores calibration |

## Percentile levels (LN)

`ln_levels` computes statistical levels from the time-weighted envelope:
**L10** is the level exceeded 10 % of the time (event peaks), **L50** the median,
**L90** the background level.

```python
import numpy as np
from phonometry import ln_levels

# A steady tone gives L10 = L50 = L90; percentiles only tell a story for a
# *fluctuating* level. Synthesize 3 s alternating between a quiet and a
# ~10 dB louder half-second so the statistics separate.
fs = 48000
rng = np.random.default_rng(0)
segment = fs // 2                                  # 0.5 s per level
quiet = 0.02 * rng.standard_normal(segment)        # background
loud = 0.06 * rng.standard_normal(segment)         # ~10 dB louder events
varying = np.tile(np.concatenate([quiet, loud]), 3)

stats = ln_levels(varying, fs, n=(10, 50, 90), weighting="A")
print(f"LA10={stats[10]:.1f}  LA50={stats[50]:.1f}  LA90={stats[90]:.1f} dB")
# LA10=66.6  LA50=65.2  LA90=58.5 dB  -> L10 (events) > L50 (median) > L90 (background)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ln_levels_example_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/ln_levels_example.svg" alt="Fast level history of fluctuating noise with the L10, L50 and L90 statistical levels marked" width="80%"></picture>

*L10 tracks the event peaks, L50 the median level and L90 the background.*

Options: `mode` selects the envelope ballistics (`'fast'`, `'slow'`,
`'impulse'`), `weighting` applies A/C weighting first, and
`calibration_factor`/`dbfs` behave as in `leq`. The integrator attack transient
(~5τ) is discarded before taking percentiles, so the leading settling ramp is
not counted in the low percentiles.

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

# Uses `recording`, `fs` and `sensitivity` from the Leq snippet above.

# C-weighted peak (IEC 61672-1 §5.13) - occupational action limits use this
peak = lc_peak(recording, fs, calibration_factor=sensitivity)

# A single noise event and a work-shift sample (slices of a real recording)
event = recording
shift_sample = recording

# Sound exposure level: single-event level normalized to 1 s (LAE)
lae = sel(event, fs, weighting="A", calibration_factor=sensitivity)

# Daily noise dose (IEC 61252): exposure in Pa²·h and LEX,8h / LEP,d
E = sound_exposure(shift_sample, fs, duration_hours=8, calibration_factor=sensitivity)
lex = lex_8h(shift_sample, fs, duration_hours=8, calibration_factor=sensitivity)
```

`lc_peak` is verified against the one-cycle/half-cycle reference responses of
IEC 61672-1:2013 Table 5, `sel` against the Table 4 LAE toneburst column, and
the dose functions against the IEC 61252 anchors (3.2 Pa²h ↔ exactly 90 dB).
`lc_peak` polyphase-oversamples the C-weighted signal by `oversample` (default
`8`) before taking the maximum, recovering the true inter-sample peak: a raw
on-grid maximum under-reads sustained HF tones by up to ~1.15 dB (an 8 kHz tone
at 48 kHz is only 6 samples/cycle). Set `oversample=1` to detect the peak on the
original sample grid. With `duration_hours`, the input is treated as a
representative sample of that exposure period; without it, the input is the
whole event.

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

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_concept_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_concept.svg" alt="A vehicle pass-by level history with its Leq over the whole event and the equal-energy one-second SEL block" width="80%"></picture>

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

`lex_8h` rates *one* recording; assembling a full working day from task or
job samples — with the normative ISO 9612 uncertainty budget — continues in
[Occupational Noise Exposure](occupational-exposure.md).

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

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/lden_profile_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/lden_profile.svg" alt="Synthetic 24-hour urban LAeq profile with day, evening and night bands, the +5 and +10 dB weighted period levels and the resulting Lden" width="80%"></picture>

### `lden()` / `ldn()` / `composite_rating_level()` parameters

| Function | Key parameters | Notes |
| :--- | :--- | :--- |
| `lden(lday, levening, lnight, hours=(12, 4, 8))` | period LAeq values [dB]; `hours` must sum to 24 | +5 dB evening, +10 dB night (3.6.4) |
| `ldn(lday, lnight, hours=(15, 9))` | | +10 dB night (3.6.5) |
| `composite_rating_level(periods)` | iterable of `(level_db, hours, adjustment_db)`; hours positive, finite and summing to 24 | General Formulae (5)-(6); adjustments per Table A.1 |

Where you put the microphone changes the number: ISO 1996-2 fixes the receiver positions and their façade corrections. phonometry does not implement ISO 1996-2 — the diagram is measurement context; apply the corrections to your levels before analysis:

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_env_measurement_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_env_measurement.svg" alt="Environmental noise measurement positions per ISO 1996-2: free field, 2 m from the facade and flush-mounted, with their corrections" width="92%"></picture>

Combine with `laeq()` per time period to go from recordings to Lden, and with
the `tone_to_noise_ratio()` / `prominence_ratio()` verdicts of
[Prominent Discrete Tones](tone-prominence.md) to justify tonal adjustments.

## Octave Spectrogram (levels over time)

Short-time fractional-octave analysis: one level per band per window,
time-aligned across bands.

```python
from phonometry import OctaveFilterBank

# Uses `recording` from the Leq snippet above.
bank = OctaveFilterBank(fs=48000, fraction=3)
levels, freq, times = bank.spectrogram(recording, window_time=0.125, overlap=0.5)
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
| `detrend` | bool | — | default `True` | Remove each band's DC offset before the level (improves low-frequency accuracy) |
| `zero_phase` | bool | — | default `False` | Forward-backward filtering (offline only) |
| `calibration_factor` / `dbfs` | — | — | constructor-only | Set on `OctaveFilterBank(...)`, not per call |

```python
import matplotlib.pyplot as plt

# Uses `levels`, `freq` and `times` from the spectrogram snippet above.
fig, ax = plt.subplots()
mesh = ax.pcolormesh(times, freq, levels, shading="auto")
ax.set_yscale("log")
ax.set_xlabel("Time [s]")
ax.set_ylabel("Frequency [Hz]")
fig.colorbar(mesh, label="Level [dB]")
```

See [Calibration and dBFS](calibration.md) to convert digital units to physical
SPL, and [Time Weighting](time-weighting.md) for the envelope details. The
ISO 9612 occupational strategies continue in
[Occupational Noise Exposure](occupational-exposure.md), the ECMA-418-1
tonal-prominence verdicts in [Prominent Discrete Tones](tone-prominence.md),
and the ISO 226 equal-loudness contours live with the perception metrics in
[Psychoacoustics](psychoacoustics.md).

---

**Standards.** IEC 61672-1:2013, *Electroacoustics — Sound level meters —
Part 1: Specifications* — the Fast/Slow/Impulse envelope ballistics behind
`ln_levels`, the C-weighted peak of §5.13 (verified against the Table 5 tone
bursts) and the sound exposure level verified against the Table 4 LAE column.
IEC 61252, *Electroacoustics — Specifications for personal sound exposure
meters* — the sound exposure E in Pa²h and the normalized 8 h level LEX,8h
(≡ LEP,d), anchored at 3.2 Pa²h ⇔ exactly 90 dB. ISO 1996-1:2016, *Acoustics —
Description, measurement and assessment of environmental noise — Part 1:
Basic quantities and assessment procedures* — Lden (3.6.4), Ldn (3.6.5) and
the composite whole-day rating level of clause 6.5 (Formulae 5-6, Table A.1
adjustments).
