← [Documentation index](README.md)

# Psychoacoustics and Speech Intelligibility

Level metrics tell you how much *sound pressure* there is; psychoacoustic
metrics tell you what a listener actually *perceives*. This page covers
loudness (ISO 532-1), sharpness (DIN 45692) and the speech transmission
index (IEC 60268-16), then the advanced Moore-Glasberg (ISO 532-2/3) and
Sottek Hearing Model (ECMA-418-2) loudness, tonality and roughness models.

## Loudness in sones (ISO 532-1, Zwicker)

Decibels compress perception: 10 dB more reads as *twice as loud*, and two
sounds with the same dB(A) can differ audibly depending on how their energy
spreads over the ear's **critical bands**. The Zwicker method models the
hearing chain explicitly — outer/middle-ear transmission, critical-band
analysis on the 24 Bark scale, level-dependent masking slopes — and outputs
**loudness N in sones**, a ratio scale: 4 sones is twice as loud as 2 sones.
By definition a 1 kHz tone at 40 dB SPL is 1 sone, and every +10 phon
doubles the sone value.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/loudness_pattern_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/loudness_pattern.png" alt="Specific loudness patterns over the Bark scale for a 1 kHz narrowband sound and a broadband sound of equal band level" width="80%"></picture>

*Same band level, very different loudness: energy spread over many critical
bands (red) sums to far more sones than the same level concentrated in one
band (blue). The area under N'(z) is the total loudness.*

```python
import numpy as np
from phonometry import loudness_zwicker, loudness_zwicker_from_spectrum

# A raw recording plus its calibration so the guide runs standalone
fs = 48000
x = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)   # any recording (digital units)
sens = 1.0                                                # calibration_factor to pascals
levels_28 = np.full(28, 60.0)                             # 28 one-third-octave band levels (dB)

# From a raw recording: calibration_factor scales digital units to Pa
res = loudness_zwicker(x, fs, field="free", calibration_factor=sens)
print(f"N = {res.loudness:.1f} sone  ({res.loudness_level:.0f} phon)")

# Time-varying signals: percentile loudness N5 is the reporting standard
res = loudness_zwicker(x, fs)          # stationary=False (default)
print(res.n5, res.n10, res.loudness)   # N5, N10, Nmax

# From 28 one-third-octave band levels (25 Hz .. 12.5 kHz)
res = loudness_zwicker_from_spectrum(levels_28, field="diffuse")

res.plot()   # N'(z) over the Bark scale — the specific-loudness pattern (needs matplotlib)
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# One line — the specific-loudness pattern N'(z) straight from the result:
res.plot()
plt.show()

# Or reproduce the figure by hand — two patterns of equal band level (60 dB),
# energy spread over many critical bands vs concentrated in the 1 kHz band:
narrow = loudness_zwicker_from_spectrum(np.r_[np.full(16, -60.0), 60.0, np.full(11, -60.0)])
broad = loudness_zwicker_from_spectrum(np.full(28, 60.0))
z = np.arange(1, narrow.specific.size + 1) * 0.1          # Bark axis
fig, ax = plt.subplots()
for r, color, label in [
    (broad, "#ff7f0e", f"Broadband  N = {broad.loudness:.1f} sone"),
    (narrow, "#1f77b4", f"1 kHz narrowband  N = {narrow.loudness:.1f} sone"),
]:
    ax.fill_between(z, r.specific, color=color, alpha=0.3)
    ax.plot(z, r.specific, color=color, label=label)
ax.set_xlabel("Critical-band rate z [Bark]")
ax.set_ylabel("Specific loudness N' [sone/Bark]")
ax.legend()
plt.show()
```

</details>

The implementation is a clean-room port of the standard's **normative
reference program** (Annex A.4): all twelve data tables are digit-exact and
the full Annex B validation set runs in CI — the stationary test case
reproduces the published value to every printed digit, and the tone-pulse
N(t) traces stay inside the standard's per-sample 5 % tolerance band.

### `loudness_zwicker()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `x` | 1D array | Pa (after calibration) | ≥ 8 ms at 48 kHz | Resampled internally to 48 kHz if needed |
| `fs` | int | Hz | > 0 | |
| `field` | str | — | `'free'` (default) / `'diffuse'` | Sound-field correction (Table A.5) |
| `stationary` | bool | — | default `False` | `True`: single N from the averaged spectrum |
| `calibration_factor` | float | Pa per digital unit | default `1.0` | From `calculate_sensitivity()` |

Returns a `ZwickerLoudness` dataclass: `loudness` (N, sones), `loudness_level`
(phon), `specific` (N′(z), 240 bins of 0.1 Bark), and for time-varying runs
`n5`, `n10`, `time`, `loudness_vs_time` (500 Hz trace).

## Sharpness in acum (DIN 45692)

Two sounds can be equally loud yet one feels "sharper" — hissy, metallic —
because its loudness sits higher on the Bark scale. Sharpness is the
g(z)-weighted first moment of the specific loudness pattern:

$$
S = k\ \frac{\int_0^{24} N'(z)\ g(z)\ z\ dz}{\int_0^{24} N'(z)\ dz}\ \text{acum}
$$

with $g(z) = 1$ up to 15.8 Bark and rising exponentially beyond, and $k$
normalized so the reference sound — critical-band-wide noise at 1 kHz,
60 dB — is exactly **1.00 acum** (DIN 45692 clause 6; the derived
$k = 0.108$ sits inside the normative window 0.105–0.115).

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sharpness_weighting_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sharpness_weighting.png" alt="DIN 45692 sharpness weighting g(z) against critical-band rate on a log axis, comparing the DIN, von Bismarck and Aures curves with the 15.8 and 15 Bark knees marked" width="80%"></picture>

```python
from phonometry import sharpness_din

s = sharpness_din(x, fs, calibration_factor=sens)      # acum
s_aures = sharpness_din(x, fs, method="aures")          # Annex B variant
```

CI verifies the Table A.2 target values (0.38 acum at 250 Hz up to
2.82 acum at 4 kHz) within the standard's 5 % / 0.05 acum tolerance.

## Speech Transmission Index (IEC 60268-16)

Reverberation and noise do not muffle speech uniformly — they blur its
*envelope*: the slow (0.63–12.5 Hz) intensity modulations that carry
syllables. STI quantifies how much of that modulation survives from mouth
to ear, per octave band, as the **modulation transfer function** m(F). A
delta-like channel keeps m = 1 (STI = 1); reverberation low-passes the
envelope following Schroeder's closed form, and steady noise scales it:

$$
m(F) = \frac{1}{\sqrt{1 + \left(2\pi F\ \frac{T_{60}}{13.8}\right)^2}}
\cdot \frac{1}{1 + 10^{-\mathrm{SNR}/10}}
$$

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sti_vs_t60_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sti_vs_t60.png" alt="STI versus reverberation time with the IEC 60268-16 Annex F rating bands shaded" width="80%"></picture>

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sti_chain_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_sti_chain.svg" alt="STI measurement chain: STIPA source signal through the room to the microphone and the MTF analysis" width="92%"></picture>

```python
import numpy as np
from phonometry import sti_from_impulse_response, stipa, stipa_signal

fs = 48000
# A measured room impulse response (synthesized decay so the example runs)
ir = np.random.default_rng(0).standard_normal(fs) * np.exp(-6.9 * np.arange(fs) / fs / 0.5)

# Indirect method: from a measured room impulse response
res = sti_from_impulse_response(ir, fs, snr=25.0)
print(f"STI = {res.sti:.2f}  ({res.rating})")   # e.g. 0.62 (D)

# Direct STIPA measurement: play stipa_signal() in the room, record it
test = stipa_signal(fs, seconds=18.0, level_db=80.0)
recording = test                       # in practice, the microphone signal after playback
res = stipa(recording, fs)
res.plot()   # per-band modulation transfer index (MTI) bars, STI + rating in the title
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# STI vs reverberation time: sweep sti_from_impulse_response over synthetic
# exponential decays (white noise x exp(-6.9077 t / T60)) at a T60 grid —
# exactly the physics behind the curve above:
rng = np.random.default_rng(0)
t60_grid = np.array([0.3, 0.5, 0.8, 1.2, 1.6, 2.0, 2.5, 3.0, 4.0, 5.0])
sti_values = []
for t60 in t60_grid:
    t = np.arange(int(2 * t60 * fs)) / fs
    ir = rng.standard_normal(t.size) * np.exp(-6.9077 * t / t60)
    sti_values.append(sti_from_impulse_response(ir, fs).sti)

fig, ax = plt.subplots()
ax.semilogx(t60_grid, sti_values, "o-")
ax.set_xlabel("Reverberation time T60 [s]")
ax.set_ylabel("STI")
ax.set_ylim(0.0, 1.0)
ax.grid(True, which="both", alpha=0.3)
plt.show()
```

</details>

`stipa` emits a `UserWarning` when the recording is shorter than the
recommended 15 s (IEC 60268-16 STIPA practice, 15 s to 25 s): below that the
slow modulation components are averaged over too few periods and the STI is
biased low (an ideal loopback gives STI ≈ 0.944 at 5 s vs ≈ 0.998 at 18 s).

The implementation follows **Edition 5 (2020)**: Edition 4's normative PDF
is the base and every Ed. 5 change is source-attributed in the code — the
only numeric delta is the revised male speech spectrum of clause A.6.1.
CI checks the standard's own verification vectors: the six weighting-factor
band pairs to ±0.001 STI, the m ↔ STI mapping table, the level-dependent
masking control points, and Schroeder-form decays at four T₆₀ values.

### `sti_from_impulse_response()` / `stipa()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `ir` / `x` | 1D array | any / Pa | non-empty | IR (indirect) or STIPA recording (direct) |
| `fs` | int | Hz | > 0 | |
| `snr` | float or 7-vector, optional | dB | default `None` | Adds steady-noise degradation |
| `level` | 7-vector, optional | dB SPL | default `None` | Enables auditory masking + reception threshold (Tables A.2/A.3) |
| `ambient` | 7-vector, optional | dB SPL | needs `level` | Ambient noise band levels |
| `reference` | 1D array, optional (`stipa`) | — | default `None` | Measured source signal instead of the nominal m = 0.55 |

Both return `STIResult`: `sti`, `mti` (7 bands), `mtf` (7×14 or 7×2),
`band_levels`, `rating` (Annex F letter `A+`…`U`).

## Advanced loudness & sound-quality models

ISO 532-1 above is one of **three** loudness models phonometry ships, and
loudness is only half of the sound-quality story: two sounds of equal loudness
can still differ in how *tonal* or how *rough* they are. This section adds the
**Moore-Glasberg** loudness of ISO 532-2/532-3 and the **Sottek Hearing Model**
loudness, tonality and roughness of ECMA-418-2:2025.

### Choosing a loudness model

| Model | Standard | Stationary / time-varying | Output | When to use |
| :--- | :--- | :--- | :--- | :--- |
| Zwicker | ISO 532-1:2017 | both | sone | Reference method; one-third-octave input; fast and widely cited |
| Moore-Glasberg | ISO 532-2:2017 | stationary | sone | roex excitation pattern; better for tones and explicit binaural summation |
| Moore-Glasberg-Schlittenlacher | ISO 532-3:2023 | time-varying | sone (STL/LTL) | Time-varying loudness with short-/long-term traces and the peak N_max |
| Sottek (Hearing Model) | ECMA-418-2:2025 | time-varying | sone_HMS | Shares one auditory front-end with the ECMA tonality and roughness metrics |

All three are anchored so a **1 kHz tone at 40 dB SPL is ≈ 1 sone**; the values
are not interchangeable digit-for-digit because the models differ in their
auditory filters and their loudness summation.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/loudness_models_comparison_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/loudness_models_comparison.png" alt="Loudness of a 1 kHz tone as a function of level for the Zwicker, Moore-Glasberg and Sottek models, all passing through 1 sone at 40 dB SPL" width="80%"></picture>

*The three models agree at the 1 sone / 40 dB anchor and diverge with level:
Zwicker doubles the sone value every +10 phon, while the Sottek model grows
more slowly (about 1.65× per 10 dB), an intrinsic difference between the
auditory summations, not a calibration error.*

### Moore-Glasberg loudness (ISO 532-2)

Where Zwicker uses fixed critical bands on the Bark scale, Moore-Glasberg builds
an **excitation pattern** with level-dependent rounded-exponential (roex)
auditory filters on the ERB-number ("Cam") scale, then applies a compressive
excitation → specific-loudness transform with C = 0.0617 sone/Cam
(ISO 532-2:2017, Formula 7) and a binaural-inhibition stage. It reproduces the
tone and broadband cases of Annex B to a percent or two and, unlike ISO 532-1,
models binaural summation explicitly.

```python
import numpy as np
from phonometry import (
    loudness_moore_glasberg,
    loudness_moore_glasberg_from_spectrum,
)

# The definitional anchor: one 1 kHz sinusoidal component at 40 dB SPL,
# free field, binaural -> 1 sone / 40 phon by construction of the sone.
res = loudness_moore_glasberg_from_spectrum([(1000.0, 40.0)], field="free")
print(f"N = {res.loudness:.3f} sone  ({res.loudness_level:.1f} phon)")   # 1.000 sone (40.0 phon)

# From a calibrated recording: the one-third-octave levels are derived from
# the signal spectrum and the exact Clause 5.5 method is applied.
fs = 48000
x = np.sqrt(2) * 2e-5 * 10 ** (40 / 20) * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)
res = loudness_moore_glasberg(x, fs, field="free", presentation="binaural")

res.plot()   # specific loudness N'(i) over the ERB-number (Cam) scale
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# One line — the specific-loudness pattern N'(i) straight from the result:
res.plot()
plt.show()

# Or draw it by hand from the ERB-number grid the result already carries:
fig, ax = plt.subplots()
ax.fill_between(res.erb_number, res.specific, alpha=0.3)
ax.plot(res.erb_number, res.specific)
ax.set_xlabel("ERB number [Cam]")
ax.set_ylabel("Specific loudness N' [sone/Cam]")
plt.show()
```

</details>

#### `loudness_moore_glasberg()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `x` | 1D array | Pa | non-empty | Calibrated pressure signal (signal wrapper) |
| `components` | list of `(f, L)` | Hz, dB SPL | — | `_from_spectrum`: discrete sinusoidal components |
| `band_levels` | 29-vector | dB SPL | 25 Hz .. 16 kHz | `_from_third_octave` input (IEC 61260-1 bands) |
| `fs` | int | Hz | > 0 | Signal wrapper only |
| `field` | str | — | `'free'` (default) / `'diffuse'` / `'eardrum'` | Outer-ear transfer |
| `presentation` | str | — | `'binaural'`/`'diotic'` (default) / `'monaural'` | Binaural summation |

Returns a `MooreGlasbergLoudness`: `loudness` (N, sone), `loudness_level`
(phon), `specific` (N′(i), 372 bins of 0.1 Cam), `erb_number`,
`centre_frequencies`, `field`, `presentation`.

### Time-varying loudness (ISO 532-3)

ISO 532-3 wraps the same excitation / specific-loudness model in a running
multi-resolution spectral analysis (six parallel FFTs, updated every 1 ms) and
two cascaded temporal integrators: the fast **short-term loudness** S′(t) and
the slower **long-term loudness** S″(t). The peak long-term loudness N_max
predicts the loudness of sounds up to about 5 s.

```python
import numpy as np
from phonometry import loudness_moore_glasberg_time

fs = 32000
t = np.arange(int(1.3 * fs)) / fs
x = np.sqrt(2) * 2e-5 * 10 ** (40 / 20) * np.sin(2 * np.pi * 1000 * t)

res = loudness_moore_glasberg_time(x, fs, field="free")
print(f"N_max = {res.n_max:.3f} sone  ({res.loudness_level_max:.0f} phon)")   # 1.000 sone (40 phon)
print(f"long-term loudness exceeded 5% of the time: {res.percentiles[5.0]:.3f} sone")

res.plot()   # short-term S'(t) and long-term S''(t) loudness vs time
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/moore_glasberg_time_loudness_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/moore_glasberg_time_loudness.png" alt="Short-term and long-term Moore-Glasberg loudness traces for a tone burst, showing the fast attack of the short-term loudness and the slower release of the long-term loudness" width="80%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# The result carries both traces on a 1 ms time axis:
res.plot()
plt.show()

# Or plot them directly to see the fast STL vs the slow LTL:
fig, ax = plt.subplots()
ax.plot(res.time, res.short_term_loudness, label="Short-term S'(t)")
ax.plot(res.time, res.long_term_loudness, label="Long-term S''(t)")
ax.set_xlabel("Time [s]")
ax.set_ylabel("Loudness [sone]")
ax.legend()
plt.show()
```

</details>

#### `loudness_moore_glasberg_time()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `signal` | 1D or `(n, 2)` array | Pa | non-empty | Mono = diotic; two columns = left/right ears |
| `fs` | int | Hz | > 0 | |
| `field` | str | — | `'free'` (default) / `'diffuse'` / `'eardrum'` | Outer-ear transfer |
| `presentation` | str | — | `'binaural'`/`'diotic'` (default) / `'monaural'` | Binaural summation |
| `percentiles` | sequence | percent | default `(1, 5, 10, 50, 90, 95)` | Exceeded long-term loudness levels |

Returns a `MooreGlasbergTimeVaryingLoudness`: `time` (1 ms grid),
`short_term_loudness` / `long_term_loudness` (sone), their `_level` in phon,
`n_max`, `loudness_level_max`, a `percentiles` dict, `field`, `presentation`.

### Sottek Hearing Model loudness (ECMA-418-2)

ECMA-418-2:2025 specifies a single auditory front-end — outer/middle-ear
filtering, a 53-band gammatone-like filter bank on the Bark_HMS scale
(z = 0.5 .. 26.5), half-wave rectification, block RMS and a compressive
nonlinearity (Formula 23) — that is **shared** by its loudness, tonality and
roughness metrics. The loudness N is reported in **sone_HMS**, and the same
1 kHz/40 dB anchor calibrates the front-end (our clean-room value 0.996).

```python
import numpy as np
from phonometry import loudness_ecma

fs = 48000
t = np.arange(int(1.2 * fs)) / fs
x = np.sqrt(2) * 2e-5 * 10 ** (40 / 20) * np.sin(2 * np.pi * 1000 * t)

res = loudness_ecma(x, fs, field="free")
print(f"N = {res.loudness:.3f} sone_HMS")   # 0.996 sone_HMS
print(res.specific_loudness.shape)          # (53,) average specific loudness N'(z)

res.plot()   # average specific loudness N'(z) + time-dependent N(l) at 187.5 Hz
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sottek_specific_loudness_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sottek_specific_loudness.png" alt="Sottek Hearing Model average specific loudness N'(z) over the 53 Bark_HMS bands for a 1 kHz tone, peaking at the tone's critical band" width="80%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt

# The result carries the average specific loudness over the 53 Bark_HMS bands:
res.plot()
plt.show()

# Or draw N'(z) by hand against the critical-band-rate scale:
fig, ax = plt.subplots()
ax.fill_between(res.bark, res.specific_loudness, alpha=0.3)
ax.plot(res.bark, res.specific_loudness)
ax.set_xlabel("Critical-band rate z [Bark_HMS]")
ax.set_ylabel("Specific loudness N' [sone_HMS/Bark_HMS]")
plt.show()
```

</details>

#### `loudness_ecma()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `signal_in` | 1D array | Pa | non-empty | Calibrated pressure signal |
| `fs` | float | Hz | > 0 | Resampled to 48 kHz internally if needed (Clause 5.1.1) |
| `field` | str | — | `'free'` (default) / `'diffuse'` | Outer/middle-ear filter (Clause 5.1.3) |

Returns an `EcmaLoudness`: `loudness` (N, sone_HMS), `specific_loudness`
(N′(z), 53 bands), `bark`, `centre_frequencies`, `time`, `loudness_vs_time`
(N(l) at 187.5 Hz), `field`.

### Tonality (ECMA-418-2)

A tonal component — a whistle, a fan's blade-passing tone — stands out even at
low level. ECMA-418-2 quantifies it from the **autocorrelation function** (ACF)
of each band's rectified signal: a periodic (tonal) component keeps a high ACF
at nonzero lag, and the tonal-to-noise loudness ratio drives the specific
tonality T′(z). The single value T is in **tu_HMS**, calibrated so a 1 kHz/40 dB
tone is ≈ 1 tu_HMS; the result also tracks the tonal frequency f_ton per band.

```python
import numpy as np
from phonometry import tonality_ecma

fs = 48000
t = np.arange(int(1.2 * fs)) / fs
x = np.sqrt(2) * 2e-5 * 10 ** (40 / 20) * np.sin(2 * np.pi * 1000 * t)

res = tonality_ecma(x, fs, field="free")
peak = int(np.argmax(res.specific_tonality))
print(f"T = {res.tonality:.3f} tu_HMS")                    # 1.000 tu_HMS
print(f"f_ton = {res.tonal_frequencies[peak]:.0f} Hz")     # 999 Hz

res.plot()   # average specific tonality T'(z) + time-dependent T(l)
```

#### `tonality_ecma()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `signal_in` | 1D array | Pa | non-empty | Calibrated pressure signal |
| `fs` | float | Hz | > 0 | Resampled to 48 kHz internally if needed |
| `field` | str | — | `'free'` (default) / `'diffuse'` | Outer/middle-ear filter |
| `f_low` | float, optional | Hz | default `None` | Lower edge of a user band for the T(l) search |
| `f_high` | float, optional | Hz | default `None` | Upper edge of the user band |

Returns an `EcmaTonality`: `tonality` (T, tu_HMS), `specific_tonality`
(T′(z), 53 bands), `bark`, `centre_frequencies`, `tonal_frequencies`
(f_ton,z), `time`, `tonality_vs_time` (T(l)), `tonal_frequency_vs_time`,
`field`.

### Roughness (ECMA-418-2) — new capability

Roughness is the harsh, buzzing sensation of fast amplitude modulation
(roughly 20–300 Hz, peaking near 70 Hz) — the quality of a diesel idle or a
distorted loudspeaker. It is a **new metric** for phonometry. ECMA-418-2
extracts each band's envelope, weights its modulation spectrum by modulation
rate and depth, and correlates the modulation across bands; the result R is in
**asper**. The reference sound (1 kHz carrier, 100 % amplitude-modulated at
70 Hz, 60 dB SPL) is defined as 1 asper — this clean-room implementation
returns 1.0735 asper (about +7 %), an honest variance: the tabulated
calibration constant c_R (Formula 104) is used **without** reverse-fitting to
the target.

```python
import numpy as np
from phonometry import roughness_ecma

fs = 48000
t = np.arange(int(2.0 * fs)) / fs
carrier = np.sin(2 * np.pi * 1000 * t)
amp = np.sqrt(2) * 2e-5 * 10 ** (60 / 20)                  # 60 dB SPL carrier
x = amp * (1.0 + np.cos(2 * np.pi * 70 * t)) * carrier      # 100 % AM at 70 Hz

res = roughness_ecma(x, fs, field="free")
print(f"R = {res.roughness:.4f} asper")   # 1.0735 asper (reference target 1.0)

res.plot()   # time-dependent roughness R(l50) + specific-roughness heatmap
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_roughness_demo_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_roughness_demo.png" alt="ECMA-418-2 sound-quality demo: a tonal sound scores high tonality and near-zero roughness, while a 70 Hz amplitude-modulated sound scores high roughness and low tonality" width="80%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import tonality_ecma, roughness_ecma

fs = 48000
t = np.arange(int(2.0 * fs)) / fs
amp = np.sqrt(2) * 2e-5 * 10 ** (60 / 20)

# A pure tone (tonal, smooth) vs a 70 Hz amplitude-modulated tone (rough):
tone = amp * np.sin(2 * np.pi * 1000 * t)
rough = amp * (1.0 + np.cos(2 * np.pi * 70 * t)) * np.sin(2 * np.pi * 1000 * t)

scores = {
    "Pure tone": (tonality_ecma(tone, fs).tonality, roughness_ecma(tone, fs).roughness),
    "70 Hz AM tone": (tonality_ecma(rough, fs).tonality, roughness_ecma(rough, fs).roughness),
}
labels = list(scores)
tonal = [scores[k][0] for k in labels]
rough_v = [scores[k][1] for k in labels]
xpos = np.arange(len(labels))
fig, ax = plt.subplots()
ax.bar(xpos - 0.2, tonal, 0.4, label="Tonality [tu_HMS]")
ax.bar(xpos + 0.2, rough_v, 0.4, label="Roughness [asper]")
ax.set_xticks(xpos)
ax.set_xticklabels(labels)
ax.legend()
plt.show()
```

</details>

#### `roughness_ecma()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `signal_in` | 1D array | Pa | non-empty | Calibrated pressure signal |
| `fs` | float | Hz | > 0 | Resampled to 48 kHz internally if needed |
| `field` | str | — | `'free'` (default) / `'diffuse'` | Outer/middle-ear filter |

Returns an `EcmaRoughness`: `roughness` (R, asper, the 90th percentile of
R(l50)), `specific_roughness` (R′(z), 53 bands), `bark`, `centre_frequencies`,
`time`, `roughness_vs_time` (R(l50)), `specific_roughness_vs_time`
((n_times, 53) array), `field`.

See [Levels](levels.md) for tonality metrics and [Theory](theory.md) for the
underlying math.
