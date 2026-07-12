---
title: "Wind-turbine noise: apparent sound power and tonal audibility"
description: "The IEC 61400-11 wind-turbine acoustic emission: the apparent sound power level referred to the rotor centre, and the tonal-audibility chain (Zwicker critical band, masking-noise level and the audibility criterion) that decides whether a discrete tone is audible."
---

IEC 61400-11 measures the acoustic emission of a wind turbine. This page covers
its two closed-form quantities: the **apparent sound power level** referred to
an equivalent point source at the rotor centre, and the **tonal audibility**
that decides whether a discrete tone (blade-passing, gearbox, generator) is
audible above the masking noise.

## Apparent sound power level

With the reference microphone on a ground board at the horizontal distance
`R0 = H + D/2` (hub height `H`, rotor diameter `D`), the slant distance to the
rotor centre is `R1 = √(H² + R0²)` and the apparent sound power level is
`L_WA,i = L_p,i − 6 + 10·lg(4π R1²/S0)` per band (`S0 = 1 m²`), energy-summed
over bands. The `−6 dB` accounts for the ground-board pressure doubling.

```python
import phonometry as ph

r1 = ph.slant_distance(hub_height=80.0, rotor_diameter=100.0)
lwa = ph.apparent_sound_power_level(band_levels, r1)   # dB re 1 pW
```

## Tonal audibility

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_tonality.svg" alt="A wind-turbine narrowband spectrum with a discrete tone near 200 Hz standing above a shaped broadband floor, the critical band about the tone shaded, the masking-noise level drawn as a horizontal line, and the tonal audibility annotated" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/wind_turbine_tonality_dark.svg" alt="A wind-turbine narrowband spectrum with a discrete tone near 200 Hz standing above a shaped broadband floor, the critical band about the tone shaded, the masking-noise level drawn as a horizontal line, and the tonal audibility annotated" style="width:82%">

From a narrowband spectrum (1–2 Hz resolution), the lines in the **critical
band** about the tone, `CBW = 25 + 75·[1 + 1.4·(fc/1000)²]^0.69` Hz, are
classified into masking noise and tone lines (the 70 %-lowest energy mean, the
`+6 dB` criteria). The masking-noise level `L_pn` follows Formula 31, the
tonality is `ΔL_tn = L_pt − L_pn`, and the tonal audibility is
`ΔL_a = ΔL_tn − L_a` with `L_a = −2 − lg[1 + (f/502)^2.5]`, reported when
`ΔL_a ≥ −3 dB` and audible when `ΔL_a > 0`.

```python
import phonometry as ph

res = ph.wind_turbine_tonality(levels, frequencies)   # narrowband spectrum
print(res.tone_frequency, res.tonality, res.tonal_audibility, res.is_audible)
res.plot()   # spectrum + critical band + masking level (needs matplotlib)
```

`wind_turbine_tonality` returns a `WindTurbineTonalityResult` with the
`critical_bandwidth`, `tone_level`, `masking_level`, `tonality`,
`audibility_criterion`, `tonal_audibility` and `is_audible`. The audibility
formula coincides with ISO 1996-2 Annex C; what is specific to IEC 61400-11 is
the determination of the tone and masking levels and the Zwicker critical band
from the spectrum. For a rating adjustment `K_T`, pass the mean audibility to
the ISO 1996-2 `tonal_adjustment`.

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

**Standards.** IEC 61400-11:2012+A1:2018 (apparent sound power Formula 26,
critical bandwidth Formula 30, masking level Formula 31, tonality/audibility
Formulae 32–34). The full measurement pipeline is out of scope here.
