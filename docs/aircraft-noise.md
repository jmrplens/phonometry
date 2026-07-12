← [Documentation index](README.md)

# Aircraft noise: Effective Perceived Noise Level (ICAO Annex 16 / IEC 61265)

The **Effective Perceived Noise Level (EPNL)** is the noise-certification metric
for transport-category aircraft. It condenses a half-second one-third-octave
spectral time history of a flyover into a single number, in EPNdB, through five
steps of **ICAO Annex 16, Vol. I, Appendix 2**. This page covers the four
primitives that build the metric and the IEC 61265 measurement-system verifier.
Each quantity is validated against the worked examples of the ICAO Doc 9501
Environmental Technical Manual (ETM) Vol. I.

## 1. Perceived noisiness and PNL

Each of the 24 one-third-octave-band levels (50 Hz–10 kHz) is converted to a
perceived **noisiness** in noys by the analytic piecewise law of Table A2-3,
then combined into the total noisiness and the perceived noise level:

$$
N = 0.85\,n_{\max} + 0.15\sum_i n_i, \qquad
\mathrm{PNL} = 40 + \frac{10}{\lg 2}\,\lg N .
$$

```python
import phonometry as ph

noys = ph.perceived_noisiness(spl)      # per-band noys (spl = 24 band levels, dB)
pnl = ph.perceived_noise_level(spl)      # PNdB
```

## 2. Tone correction

Spectral irregularities (fan/turbine tones) are penalised by a **tone
correction** `C`, found with the slope ("encircling") method: slopes are
smoothed to a background spectrum `SPL''`, the tone excess `F = SPL − SPL''`
above 1.5 dB is mapped to a correction factor (frequency-split at 500 Hz /
5000 Hz, capped at 6⅔ dB), and the maximum over bands is taken.

```python
c = ph.tone_correction(spl)              # dB; added to PNL to give PNLT
```

The implementation reproduces the ICAO Doc 9501 ETM Vol. I **Table 3-7**
turbofan example exactly, including its `SPL''` background column and the
resulting `C = 2.0 dB` at 2500 Hz.

## 3. EPNL

Over the flyover, the tone-corrected level is `PNLT = PNL + C`; its maximum is
`PNLTM`. The metric integrates `PNLT` over the **10 dB-down** window (the
records nearest to `PNLTM − 10` on each side) and normalises to 10 s:

$$
\mathrm{EPNL} = 10\lg\!\Big(\sum_{k=k_F}^{k_L} 10^{\mathrm{PNLT}(k)/10}\,\Delta t(k)\Big)
- 10\lg T_0, \qquad T_0 = 10\ \mathrm{s},
$$

so `EPNL = PNLTM + D` with the duration correction `D`.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/epnl_dark.svg">
  <img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/epnl.svg" alt="Aircraft-flyover perceived-noise-level time history: PNL and the tone-corrected PNLT versus time, with the maximum PNLTM marked and the 10 dB-down integration window shaded, annotated with the resulting EPNL and duration correction" width="82%">
</picture>

```python
import numpy as np
import phonometry as ph

# spectra: a (K, 24) array of one-third-octave band levels sampled every dt s
res = ph.effective_perceived_noise_level(spectra, dt=0.5)
print(res.epnl, res.pnltm, res.duration_correction, res.band_limits)
res.plot()   # PNL/PNLT time history (needs matplotlib)
```

`effective_perceived_noise_level` returns an `EPNLResult` bundling the per-record
`pnl`, `tone_correction`, `pnlt`, the peak `pnltm`, the `duration_correction`,
the `epnl` and the 10 dB-down `band_limits`. The reference-condition
integrated-method example of ETM Vol. I **Table 4-4** (a 31-record `PNLT`
history with non-uniform durations) is reproduced as `EPNL = 92.6 EPNdB`.
`epnl_from_pnlt` exposes the duration/limit machinery directly from a `PNLT`
series.

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

## 4. Measurement-system verification (IEC 61265)

`verify_aircraft_noise_system` checks a supplied set of measured performance
values against the IEC 61265:1995 tolerances for aircraft-noise measurement
systems: the microphone directional-response limits (Table 1, with the
"intermediate angle uses the greater angle's limit" rule) and the scalar
frequency-response, linearity and resolution limits. The one-third-octave
filtering itself is covered by the library's IEC 61260 class-2 filter
verification (`verify_filter_class`).

```python
import phonometry as ph

report = ph.verify_aircraft_noise_system(
    directional={4000.0: {30: 0.4, 60: 0.9, 90: 1.9, 120: 2.4, 150: 2.4}},
    frequency_response={1000.0: 1.2},
)
print(report["passed"], report["checks"])
```

---

**Standards.** ICAO Annex 16, *Environmental Protection*, Vol. I, *Aircraft
Noise*, Appendix 2: the analytic EPNL procedure (perceived noisiness Table A2-3,
tone correction Table A2-2, duration correction). ICAO Doc 9501, *Environmental
Technical Manual*, Vol. I: the worked examples (Table 3-7 tone correction,
Table 4-4 integrated-method EPNL) used as numeric oracles. IEC 61265:1995,
*Instruments for the measurement of aircraft noise*: the measurement-system
performance tolerances. The full certification correction chain (atmospheric
absorption, reference-condition corrections) and airport noise contours are out
of scope here.
