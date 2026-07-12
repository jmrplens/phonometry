← [Documentation index](README.md)

# Wind-turbine noise: apparent sound power and tonal audibility (IEC 61400-11)

IEC 61400-11 measures the acoustic emission of a wind turbine. This page covers
its two closed-form quantities: the **apparent sound power level** referred to
an equivalent point source at the rotor centre, and the **tonal audibility**
that decides whether a discrete tone (blade-passing, gearbox, generator) is
audible above the masking noise. Each is validated against the standard's
formulas and a hand-derived synthetic-tone oracle.

## 1. Apparent sound power level

With the reference microphone on a ground board at the horizontal distance
`R0 = H + D/2` (hub height `H`, rotor diameter `D`), the slant distance to the
rotor centre is `R1 = √(H² + R0²)` and the per-band apparent sound power level is

$$
L_{WA,i} = L_{p,i} - 6 + 10\lg\frac{4\pi R_1^2}{S_0}, \qquad S_0 = 1\ \mathrm{m}^2,
$$

energy-summed over bands (Formula 27). The `−6 dB` accounts for the ground-board
pressure doubling.

```python
import phonometry as ph

# Background-corrected A-weighted one-third-octave band levels L_p,i (dB).
band_levels = [55.0, 58.0, 60.0, 57.0, 54.0]
r1 = ph.slant_distance(hub_height=80.0, rotor_diameter=100.0)
lwa = ph.apparent_sound_power_level(band_levels, r1)   # dB re 1 pW
```

## 2. Tonal audibility

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_tonality_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_tonality.svg" alt="A wind-turbine narrowband spectrum with a discrete tone near 200 Hz standing above a shaped broadband floor, the critical band about the tone shaded, the masking-noise level drawn as a horizontal line, and the tonal audibility annotated" width="82%">
</picture>

From a narrowband spectrum (1–2 Hz resolution), the lines in the **critical
band** about the tone,

$$
\mathrm{CBW} = 25 + 75\,[\,1 + 1.4\,(f_c/1000)^2\,]^{0.69}\ \mathrm{Hz},
$$

are classified into masking noise and tone lines (the 70 %-lowest energy mean,
the `+6 dB` criteria). The masking-noise level `L_pn` follows Formula 31, the
tonality is `ΔL_tn = L_pt − L_pn`, and the tonal audibility is

$$
\Delta L_a = \Delta L_{tn} - L_a, \qquad L_a = -2 - \lg\!\big[1 + (f/502)^{2.5}\big],
$$

reported when `ΔL_a ≥ −3 dB`; a tone is audible when `ΔL_a > 0`.

```python
import numpy as np
import phonometry as ph

# A uniformly-spaced narrowband spectrum (2 Hz resolution): a flat 30 dB floor
# with a discrete 60 dB tone at 500 Hz.
frequencies = np.arange(440.0, 562.0, 2.0)
levels = np.full(frequencies.size, 30.0)
levels[np.argmin(np.abs(frequencies - 500.0))] = 60.0

res = ph.wind_turbine_tonality(levels, frequencies)
print(res.tone_frequency, res.tonality, res.tonal_audibility, res.is_audible)
res.plot()   # spectrum + critical band + masking level (needs matplotlib)
```

`wind_turbine_tonality` returns a `WindTurbineTonalityResult` with the
`critical_bandwidth`, `tone_level`, `masking_level`, `tonality`,
`audibility_criterion`, `tonal_audibility` and `is_audible`. The audibility
formula is the ISO 1996-2 Annex C one; what is specific to IEC 61400-11 is the
determination of the tone and masking levels and the Zwicker critical band from
the spectrum. For a rating adjustment `K_T`, pass the mean audibility to the
ISO 1996-2 `tonal_adjustment`.

<details>
<summary>Show the code for this figure</summary>

```python
import numpy as np
import phonometry as ph

df = 2.0
freqs = np.arange(50.0, 400.0 + df, df)
levels = 42.0 - 6.0 * np.log10(freqs / 100.0)
levels[int(np.argmin(np.abs(freqs - 200.0)))] += 22.0   # blade-passing-style tone
ph.wind_turbine_tonality(levels, freqs, tone_frequency=200.0).plot()
```

</details>

---

**Standards.** IEC 61400-11:2012+A1:2018, *Wind turbines — Part 11: Acoustic
noise measurement techniques*: the apparent sound power level (Formula 26), the
critical bandwidth (Formula 30), the masking-noise level (Formula 31) and the
tonality/audibility (Formulae 32–34). The tonal-audibility formula coincides
with ISO 1996-2 Annex C. The full measurement pipeline (wind-speed binning,
regression to standardised speeds and the uncertainty budgets) is out of scope
here; these are the underlying closed forms.
