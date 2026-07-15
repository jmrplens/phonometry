← [Documentation index](README.md)

# Sound Quality Metrics

Two sounds of equal loudness can still differ in how *sharp*, how *tonal* or
how *rough* they are. This page covers the sound-quality metrics that
complement loudness: sharpness (DIN 45692) and the ECMA-418-2 tonality and
roughness of the Sottek Hearing Model. Loudness itself, including the
ECMA-418-2 loudness that shares the same auditory front-end, lives in
[Loudness](loudness.md).

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

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sharpness_weighting_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sharpness_weighting.svg" alt="DIN 45692 sharpness weighting g(z) against critical-band rate on a log axis, comparing the DIN, von Bismarck and Aures curves with the 15.8 and 15 Bark knees marked" width="80%"></picture>

```python
import numpy as np
from phonometry import sharpness_din

# A raw recording plus its calibration so the guide runs standalone
fs = 48000
x = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)   # any recording (digital units)
sens = 1.0                                                # calibration_factor to pascals

s = sharpness_din(x, fs, calibration_factor=sens)      # acum
s_aures = sharpness_din(x, fs, method="aures")          # Annex B variant
```

CI verifies the Table A.2 target values (0.38 acum at 250 Hz up to
2.82 acum at 4 kHz) within the standard's 5 % / 0.05 acum tolerance.

## Tonality (ECMA-418-2)

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

### `tonality_ecma()` parameters

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

## Roughness (ECMA-418-2) — new capability

Roughness is the harsh, buzzing sensation of fast amplitude modulation
(roughly 20–300 Hz, peaking near 70 Hz) — the quality of a diesel idle or a
distorted loudspeaker. It is a **new metric** for phonometry. ECMA-418-2
extracts each band's envelope, weights its modulation spectrum by modulation
rate and depth, and correlates the modulation across bands; the result R is in
**asper**. The reference sound (1 kHz carrier, 100 % amplitude-modulated at
70 Hz, overall level 60 dB SPL) is defined as 1 asper — this clean-room
implementation returns 0.9999 asper with the tabulated calibration constant
c_R (Formula 104) used **without** reverse-fitting to the target.

```python
import numpy as np
from phonometry import roughness_ecma

fs = 48000
t = np.arange(int(2.0 * fs)) / fs
x = (1.0 + np.cos(2 * np.pi * 70 * t)) * np.sin(2 * np.pi * 1000 * t)
x *= 2e-5 * 10 ** (60 / 20) / np.sqrt(np.mean(x**2))   # overall 60 dB SPL

res = roughness_ecma(x, fs, field="free")
print(f"R = {res.roughness:.4f} asper")   # 0.9999 asper (reference: 1 asper)

res.plot()   # time-dependent roughness R(l50) + specific-roughness heatmap
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_roughness_demo_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/tonality_roughness_demo.svg" alt="ECMA-418-2 sound-quality demo: a tonal sound scores high tonality and near-zero roughness, while a 70 Hz amplitude-modulated sound scores high roughness and low tonality" width="80%"></picture>

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import tonality_ecma, roughness_ecma

fs = 48000
t = np.arange(int(2.0 * fs)) / fs
amp = np.sqrt(2) * 2e-5 * 10 ** (60 / 20)

# A pure tone (tonal, smooth) vs a 70 Hz amplitude-modulated tone (rough),
# both normalized to an overall level of 60 dB SPL:
tone = amp * np.sin(2 * np.pi * 1000 * t)
rough = (1.0 + np.cos(2 * np.pi * 70 * t)) * np.sin(2 * np.pi * 1000 * t)
rough *= 2e-5 * 10 ** (60 / 20) / np.sqrt(np.mean(rough**2))

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

### `roughness_ecma()` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `signal_in` | 1D array | Pa | non-empty | Calibrated pressure signal |
| `fs` | float | Hz | > 0 | Resampled to 48 kHz internally if needed |
| `field` | str | — | `'free'` (default) / `'diffuse'` | Outer/middle-ear filter |

Returns an `EcmaRoughness`: `roughness` (R, asper, the 90th percentile of
R(l50)), `specific_roughness` (R′(z), 53 bands), `bark`, `centre_frequencies`,
`time`, `roughness_vs_time` (R(l50)), `specific_roughness_vs_time`
((n_times, 53) array), `field`.

See [Prominent Discrete Tones](tone-prominence.md) for the ECMA-418-1 TNR/PR
prominence verdicts, [Speech Transmission Index](speech-transmission.md) for
STI/STIPA, and [Theory](theory.md) for the underlying math.

---

**Standards.** DIN 45692:2009, *Messtechnische Simulation der Hörempfindung
Schärfe* — sharpness in acum (clause 6 weighting, Annex B von Bismarck and
Aures variants, Table A.2 targets). ECMA-418-2:2025, *Psychoacoustic metrics
for ITT equipment — Part 2 (methods for describing human perception based on
the Sottek Hearing Model)* — the Sottek Hearing Model tonality (tu_HMS) and
roughness (asper).
