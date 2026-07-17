---
title: "Calibrated spectral analysis"
description: "The Bendat & Piersol Welch estimators with their statistical quality: power and cross-spectral density with the effective number of averages, normalized random errors and chi-square confidence intervals, the coherent output spectrum with the spectral signal-to-noise ratio, constant-power fractional-octave smoothing, and colored-noise generators with an exact power-law slope."
---

A spectrum without its uncertainty is half a measurement. This page covers the
Welch spectral estimators of `phonometry.metrology` that report, next to the
spectrum itself, the statistical quality of the estimate following Bendat &
Piersol, *Random Data: Analysis and Measurement Procedures* (4th ed., 2010):
the **power spectral density** and **cross-spectral density** with the
effective number of averages, the normalized random error and chi-square
confidence intervals; the **coherent output spectrum** that splits a measured
output into the part linearly explained by the input and the noise remainder,
with the spectral signal-to-noise ratio; a **fractional-octave smoother** with
a constant-power kernel; and **colored-noise generators** with an exact
power-law slope for exercising all of the above. Every error formula is a
closed form from the book, verified by seeded Monte Carlo in the test suite.

## 1. Power spectral density with its statistical error

`power_spectral_density` estimates the one-sided autospectral density
`Gxx(f)` by Welch's method: the record is split into tapered (Hann by
default), 50 %-overlapped segments whose periodograms are averaged. No
detrending is applied, so absolute calibration is preserved — a signal in
pascals yields `Pa²/Hz`. Two scalings are available: `'density'` (units²/Hz,
integrates to the signal power) and `'spectrum'` (units², reads the power of
discrete tones directly).

Averaging `nd` independent segments gives the estimate `2·nd` chi-square
degrees of freedom (Eq. 8.162), from which everything else follows:

$$
\varepsilon_r[\hat{G}_{xx}] = \frac{1}{\sqrt{n_d}}, \qquad
\frac{n\,\hat{G}_{xx}}{\chi^2_{n;\,\alpha/2}} \le G_{xx} \le
\frac{n\,\hat{G}_{xx}}{\chi^2_{n;\,1-\alpha/2}}, \quad n = 2 n_d .
$$

With overlapped, tapered segments the averages are correlated, so the result
reports both the raw segment count (`n_segments`) and the **effective**
number of independent averages (`n_averages`), computed with the
window-correlation formula of Welch (1967) that Bendat & Piersol reference in
Section 11.5.2.2 — for a Hann taper at 50 % overlap roughly 0.95 of the raw
count. The random error and the confidence interval use the effective value.

```python
from phonometry import power_spectral_density

res = power_spectral_density(signal, fs)          # Hann, 50 % overlap, 95 % CI
print(res.n_averages, res.random_error)           # nd and 1/sqrt(nd)
print(res.ci_lower[10], res.psd[10], res.ci_upper[10])
res.plot()                                        # PSD in dB with the CI band
```

The **resolution bias** is the other half of the error budget: a finite
analysis bandwidth `Be` (reported as `resolution_bandwidth`, the effective
noise bandwidth of the taper) smooths sharp spectral features, always in the
direction of reduced dynamic range (Eq. 8.139). For a resonance peak of
half-power bandwidth `Br`, the first-order normalized bias is the closed form
of Eq. 8.141, exposed as `resolution_bias_error`:

$$
\varepsilon_b[\hat{G}_{xx}(f_r)] \approx -\frac{1}{3}\left(\frac{B_e}{B_r}\right)^2 .
$$

```python
from phonometry import resolution_bias_error

eps_b = resolution_bias_error(res.resolution_bandwidth, 25.0)  # Br = 25 Hz peak
```

Narrow `Be` (long segments) suppresses the bias but leaves fewer averages and
a larger random error; the two requirements on segment length pull in
opposite directions, which is exactly the trade-off the reported numbers make
visible.

<img class="light-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/psd_confidence_smoothing.svg" alt="Welch power spectral density of pink noise in dB per Hz over 20 Hz to 20 kHz, with the 95 percent chi-square confidence band shaded around the estimate, the 1/3-octave smoothed curve on top and the exact -3.01 dB per octave power law as a dashed reference line" style="width:82%"><img class="dark-only" src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/psd_confidence_smoothing_dark.svg" alt="Welch power spectral density of pink noise in dB per Hz over 20 Hz to 20 kHz, with the 95 percent chi-square confidence band shaded around the estimate, the 1/3-octave smoothed curve on top and the exact -3.01 dB per octave power law as a dashed reference line" style="width:82%">

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from phonometry import (
    fractional_octave_smoothing,
    noise_signal,
    power_spectral_density,
)

fs = 48000.0
x = noise_signal(fs, 20.0, color="pink", seed=11)
res = power_spectral_density(x, fs, nperseg=4096)
band = (res.frequencies >= 20.0) & (res.frequencies <= 20000.0)
freqs = res.frequencies[band]
smooth = fractional_octave_smoothing(res.frequencies, res.psd, 3.0)[band]

fig, ax = plt.subplots(figsize=(10, 6))
ax.fill_between(freqs, 10 * np.log10(res.ci_lower[band]),
                10 * np.log10(res.ci_upper[band]), alpha=0.3,
                label="95 % chi-square confidence interval")
ax.semilogx(freqs, 10 * np.log10(res.psd[band]), lw=1.0,
            label="Welch PSD estimate")
ax.semilogx(freqs, 10 * np.log10(smooth), lw=2.2,
            label="1/3-octave smoothed")
ax.set_xlabel("Frequency [Hz]")
ax.set_ylabel("PSD [dB re 1/Hz]")
ax.legend()
plt.show()
```

</details>

## 2. Cross-spectral density

`cross_spectral_density` estimates the complex `Gxy(f)` between two channels
with the same Welch core, and reports the ordinary coherence
`γ²xy = |Gxy|²/(Gxx·Gyy)` together with the Bendat & Piersol random errors of
the magnitude and phase (Eqs. 9.33 and 9.52, with the measured coherence in
place of the unknown true value, as the book recommends for measured data):

$$
\varepsilon_r[|\hat{G}_{xy}|] = \frac{1}{|\gamma_{xy}|\sqrt{n_d}}, \qquad
\mathrm{s.d.}[\hat{\theta}_{xy}] =
\frac{\left(1-\gamma^2_{xy}\right)^{1/2}}{|\gamma_{xy}|\sqrt{2 n_d}} .
$$

Both shrink as the coherence approaches one: a strongly coherent pair needs
far fewer averages for the same confidence. The phase is unwrapped, so the
slope of `phase` against frequency measures a propagation delay directly
(`τ = -slope/2π`).

```python
from phonometry import cross_spectral_density

res = cross_spectral_density(x, y, fs)
print(res.magnitude_random_error[k], res.phase_std[k])  # per-bin errors
res.plot()   # magnitude, phase with ±sigma band, coherence
```

## 3. Coherent output spectrum and spectral SNR

In the single-input/single-output model the measured output autospectrum
splits exactly into the part linearly explained by the input and the
uncorrelated remainder (Eqs. 9.55–9.57):

$$
G_{vv} = \gamma^2_{xy}\,G_{yy}, \qquad
G_{nn} = \left(1-\gamma^2_{xy}\right) G_{yy}, \qquad
\mathrm{SNR}(f) = \frac{\gamma^2_{xy}}{1-\gamma^2_{xy}} .
$$

`coherent_output_spectrum` returns all three spectra, the spectral
signal-to-noise ratio (linear and in dB) and the random error of the coherent
output estimate (Eq. 9.73), plus the first-order propagation of the coherence
error through the SNR:

$$
\varepsilon_r[\hat{G}_{vv}] =
\frac{\left(2-\gamma^2_{xy}\right)^{1/2}}{|\gamma_{xy}|\sqrt{n_d}}, \qquad
\varepsilon_r[\widehat{\mathrm{SNR}}] = \frac{\sqrt{2}}{|\gamma_{xy}|\sqrt{n_d}} .
$$

For additive uncorrelated output noise of known level the coherence has the
closed form `γ² = SNR/(1+SNR)`, which makes the whole chain verifiable with a
synthetic signal:

```python
import numpy as np
from phonometry import coherent_output_spectrum, noise_signal

fs = 48000.0
x = noise_signal(fs, 8.0, color="white", seed=1)
noise = noise_signal(fs, 8.0, color="white", rms=0.5, seed=2)
y = 0.8 * x + noise                      # SNR = 0.64/0.25 at every frequency

res = coherent_output_spectrum(x, y, fs)
print(np.median(res.coherence))          # -> SNR/(1+SNR) = 0.719
print(np.median(res.snr_db))             # -> 10·lg(2.56) = 4.1 dB
res.plot()                               # Gyy, Gvv, Gnn and the SNR panel
```

The `coherence_bias` field reports the small positive bias of the coherence
estimate, `b[γ̂²] ≈ (1-γ²)²/nd` (Eq. 9.75) — negligible once `nd` reaches a
few hundred, and another reason to average generously before trusting a low
coherence.

## 4. Fractional-octave smoothing

`fractional_octave_smoothing` averages a spectrum over a rectangular window
of constant relative width — 1/n octave, `[f·2^(-1/2n), f·2^(+1/2n)]` around
each frequency. This is the constant-percentage resolution bandwidth that
Bendat & Piersol recommend for the spectra of resonant systems
(Section 8.5.3), and the de facto standard for presenting loudspeaker and
room responses. The average is always computed on **power** (amplitudes are
squared first, dB levels converted and back), so band power is conserved
rather than amplitude, and a flat spectrum passes through exactly unchanged.

```python
from phonometry import fractional_octave_smoothing

smooth_psd = fractional_octave_smoothing(res.frequencies, res.psd, 3.0)
smooth_mag = fractional_octave_smoothing(freqs, np.abs(H), 6.0, domain="amplitude")
smooth_db = fractional_octave_smoothing(freqs, level_db, 3.0, domain="db")
```

A single spectral line of power `P` in a bin of width `Δf` smooths to the
closed-form level `P·Δf / (f₀·(2^{1/2n} - 2^{-1/2n}))` over one kernel width —
the oracle pinned in the tests.

## 5. Colored-noise generators

`noise_signal` produces Gaussian noise whose PSD follows `Gxx(f) ∝ f^α`
exactly: seeded white noise is shaped in the frequency domain by the exact
magnitude response `(f/f_ref)^{α/2}` bin by bin (a zero-phase filter applied
circularly), so the slope holds to machine precision on the analysis grid —
not the piecewise or few-pole pink approximations whose slope ripples by
fractions of a dB. The record is zero-mean and rescaled to the requested RMS
exactly, and the same seed reproduces the same record bit for bit.

| color | α | PSD slope |
|---|---|---|
| `white` | 0 | 0 dB/octave |
| `pink` | -1 | -3.01 dB/octave |
| `red` (Brownian) | -2 | -6.02 dB/octave |
| `blue` | +1 | +3.01 dB/octave |
| `violet` | +2 | +6.02 dB/octave |

```python
from phonometry import noise_signal

pink = noise_signal(48000, 10.0, color="pink", seed=7)     # deterministic
white = noise_signal(48000, 10.0, color="white", rms=0.5, seed=7)
```

Measured over three decades (20 Hz – 20 kHz) with the estimator of section 1,
the regression slope of each color lands within a few thousandths of a
dB/octave of the exact value — the conformance suite pins the pink slope at
-3.0116 against the exact -3.0103.

## Relation to the H1/H2 estimators

The [frequency-response estimators](/phonometry/guides/electroacoustics/)
`transfer_function` and `coherence`, the two-microphone
[sound intensity](/phonometry/guides/intensity/) probe and these estimators
all share one Welch core (same taper, overlap policy and detrend-off
calibration), so a PSD, a coherence and an H1 computed with the same segment
length are mutually consistent bin by bin.

## References

- Bendat, J. S., & Piersol, A. G. (2010). *Random Data: Analysis and
  Measurement Procedures* (4th ed.). Wiley. ISBN 978-0-470-24877-5.
  [doi:10.1002/9781118032428](https://doi.org/10.1002/9781118032428).
  Sections 5.2 and 8.5 (autospectra and their random/bias errors,
  chi-square intervals), 9.1–9.2 (cross-spectra, coherent output spectrum
  and their errors) and 11.5 (Welch processing, tapering and overlap).
- Welch, P. D. (1967). The use of fast Fourier transform for the estimation
  of power spectra: A method based on time averaging over short, modified
  periodograms. *IEEE Transactions on Audio and Electroacoustics*, 15(2),
  70–73. [doi:10.1109/TAU.1967.1161901](https://doi.org/10.1109/TAU.1967.1161901).
  The overlapped-segment variance formula behind the effective number of
  averages (Bendat & Piersol Section 11.5.2.2, Ref. 11).
