← [Documentation index](README.md)

# Integrated and Statistical Levels

Environmental noise metrics computed directly from the raw (calibrated) signal.

## Leq and LAeq

The equivalent continuous level integrates the squared pressure over the
measurement time:

$$
L_{eq} = 10\log_{10}\!\left(\frac{1}{T}\int_0^T \frac{p^2(t)}{p_0^2}\,dt\right) \text{ dB}, \qquad p_0 = 20\ \mu\text{Pa}
$$

and $L_{Aeq}$ is the same integral after A-weighting the signal. $L_N$ is the
level exceeded $N\,\%$ of the time — the $(100-N)$-th percentile of the
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
