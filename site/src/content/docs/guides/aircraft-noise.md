---
title: "Aircraft noise: Effective Perceived Noise Level"
description: "The ICAO Annex 16 Vol. I Appendix 2 Effective Perceived Noise Level (EPNL): perceived noisiness and PNL, the tone correction by the slope method, the 10 dB-down duration correction, and the IEC 61265 measurement-system verifier."
---

The **Effective Perceived Noise Level (EPNL)** is the noise-certification metric
for transport-category aircraft. It condenses a half-second one-third-octave
spectral time history of a flyover into a single number, in EPNdB, through five
steps of **ICAO Annex 16, Vol. I, Appendix 2**. This page covers the four
primitives that build the metric and the IEC 61265 measurement-system verifier.
Each quantity is validated against the worked examples of the ICAO Doc 9501
Environmental Technical Manual (ETM) Vol. I.

## Perceived noisiness and PNL

Each of the 24 one-third-octave-band levels (50 Hz–10 kHz) is converted to a
perceived **noisiness** in noys by the analytic piecewise law of Table A2-3,
then combined into the total noisiness `N = 0.85·n_max + 0.15·Σn` and the
perceived noise level `PNL = 40 + (10/lg2)·lg N`.

```python
import phonometry as ph

noys = ph.perceived_noisiness(spl)      # per-band noys (spl = 24 band levels, dB)
pnl = ph.perceived_noise_level(spl)      # PNdB
```

## Tone correction

Spectral irregularities (fan/turbine tones) are penalised by a **tone
correction** `C`, found with the slope ("encircling") method: slopes are
smoothed to a background spectrum `SPL''`, the tone excess `F = SPL − SPL''`
above 1.5 dB is mapped to a correction factor (frequency-split at 500 Hz /
5000 Hz, capped at 6⅔ dB), and the maximum over bands is taken. The
implementation reproduces the ICAO Doc 9501 ETM Vol. I Table 3-7 turbofan
example exactly (`C = 2.0 dB` at 2500 Hz).

```python
c = ph.tone_correction(spl)              # dB; added to PNL to give PNLT
```

## EPNL

Over the flyover, `PNLT = PNL + C`, its maximum is `PNLTM`, and the metric
integrates `PNLT` over the 10 dB-down window (the records nearest to
`PNLTM − 10` on each side) normalised to 10 s, so `EPNL = PNLTM + D` with the
duration correction `D`.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/epnl.svg" alt="Aircraft-flyover perceived-noise-level time history: PNL and the tone-corrected PNLT versus time, with the maximum PNLTM marked and the 10 dB-down integration window shaded, annotated with the resulting EPNL and duration correction" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/epnl_dark.svg" alt="Aircraft-flyover perceived-noise-level time history: PNL and the tone-corrected PNLT versus time, with the maximum PNLTM marked and the 10 dB-down integration window shaded, annotated with the resulting EPNL and duration correction" style="width:82%">

```python
import phonometry as ph

# spectra: a (K, 24) array of one-third-octave band levels sampled every dt s
res = ph.effective_perceived_noise_level(spectra, dt=0.5)
print(res.epnl, res.pnltm, res.duration_correction, res.band_limits)
res.plot()   # PNL/PNLT time history (needs matplotlib)
```

`effective_perceived_noise_level` returns an `EPNLResult` bundling the per-record
`pnl`, `tone_correction`, `pnlt`, the peak `pnltm`, the `duration_correction`,
the `epnl` and the 10 dB-down `band_limits`. The reference-condition
integrated-method example of ETM Vol. I Table 4-4 is reproduced as
`EPNL = 92.6 EPNdB`.

<details>
<summary>Show the code for this figure</summary>

```python
import numpy as np
import phonometry as ph

k, dt = 41, 0.5
idx = np.arange(k)
shape = 15.0 * np.exp(-((np.log10(ph.NOY_BANDS) - np.log10(400.0)) ** 2) / 0.5)
gain = 30.0 * np.exp(-((idx - 20.0) ** 2) / (2 * 5.0**2)) - 5.0
spectra = (55.0 + shape)[None, :] + gain[:, None]
spectra[:, 17] += 12.0 * np.exp(-((idx - 20.0) ** 2) / (2 * 6.0**2))  # 2500 Hz fan tone
ph.effective_perceived_noise_level(spectra, dt).plot()
```

</details>

## Measurement-system verification (IEC 61265)

`verify_aircraft_noise_system` checks measured performance against the
IEC 61265:1995 tolerances: the microphone directional-response limits (Table 1)
and the scalar frequency-response, linearity and resolution limits. The
one-third-octave filtering is covered by the library's IEC 61260 class-2 filter
verification.

```python
import phonometry as ph

report = ph.verify_aircraft_noise_system(
    directional={4000.0: {30: 0.4, 60: 0.9, 90: 1.9, 120: 2.4, 150: 2.4}},
    frequency_response={1000.0: 1.2},
)
print(report["passed"], report["checks"])
```

## Atmospheric absorption (SAE ARP 5534)

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/aircraft_atmospheric_absorption.svg" alt="Aircraft atmospheric absorption versus frequency for two path lengths; the SAE-Method band attenuation stays below the pure-tone mid-band value at high absorption" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/aircraft_atmospheric_absorption_dark.svg" alt="Aircraft atmospheric absorption versus frequency for two path lengths; the SAE-Method band attenuation stays below the pure-tone mid-band value at high absorption" style="width:82%">

Correcting a measured flyover to reference atmospheric conditions needs the
one-third-octave-band attenuation over the path. The pure-tone coefficient is
the ISO 9613-1 one (identical, per ARP 5534 §3.1) provided by `air_attenuation`;
`sae_band_attenuation` adds the **SAE Method** (ARP 5534 §3.2.2) mapping the
pure-tone mid-band path attenuation `δ_t = α·s` to the band attenuation `δ_B`,
consistent with the Exact Method well beyond the 50 dB Approximate-Method limit.

```python
import numpy as np
import phonometry as ph

freqs = 1000.0 * 10.0 ** (np.arange(-13, 11) / 10.0)   # 50 Hz–10 kHz thirds
att = ph.sae_band_attenuation(freqs, path_length=7620.0,
                              temperature=25.0, relative_humidity=70.0)
att.plot()   # band vs pure-tone mid-band (needs matplotlib)
```

Valid roughly 6–32 °C, 20–95 % RH (14 CFR Part 36 window), to 7620 m, reciprocal.

---

**Standards.** ICAO Annex 16 Vol. I Appendix 2 (EPNL procedure), ICAO Doc 9501
ETM Vol. I (worked-example oracles), IEC 61265:1995 (measurement-system
tolerances), SAE ARP 5534:2021 (SAE-Method band absorption; pure-tone coefficient
from ISO 9613-1). Airport noise contours (ECAC Doc 29) remain out of scope here.
