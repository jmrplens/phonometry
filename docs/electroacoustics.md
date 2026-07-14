← [Documentation index](README.md)

# Electroacoustics: distortion and frequency response (IEC 60268-3 / Bendat & Piersol)

Two staples of audio-equipment characterisation, from a captured signal: how much
an amplifier or transducer **distorts** a test tone, and what **frequency
response** an input/output measurement reveals. This page covers the IEC 60268-3
distortion set — total and nth-order harmonic distortion, THD+N and SINAD
through the AES17 measurement bandwidth, the per-order modulation and
difference-frequency intermodulation, dynamic intermodulation (DIM) and the
ITU-R 468 weighted THD — and the Bendat & Piersol frequency-response estimators
`H1`/`H2` with the ordinary coherence `γ²`. Every quantity has an exact analytic
oracle, so the numbers are verifiable rather than tuned.

## 1. Harmonic distortion (IEC 60268-3 14.12.2–5)

A non-linear device fed a pure sine at `f₁` returns the fundamental plus
harmonics at `2f₁, 3f₁, …`. The **total harmonic distortion** combines the
harmonic amplitudes `aₙ`, either relative to the fundamental (`kind='F'`) or to
the total RMS (`kind='R'`):

$$
\mathrm{THD}_F = \frac{\sqrt{\sum_{n\ge 2} a_n^2}}{a_1}, \qquad
\mathrm{THD}_R = \frac{\sqrt{\sum_{n\ge 2} a_n^2}}{\sqrt{\sum_{n\ge 1} a_n^2}},
\qquad
d_n = \frac{a_n}{\sqrt{\sum_{k\ge 1} a_k^2}}.
$$

`dₙ` is the nth-order harmonic distortion (the nth harmonic relative to the
total). The tones should fall on FFT bins — use coherent sampling (an integer
number of periods) or a low-leakage window — so the amplitudes are read without
spectral leakage.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/distortion_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/distortion.svg" alt="Magnitude spectrum of a 1 kHz single-tone test in dB relative to the fundamental, with the first five harmonics marked above a broadband noise floor, annotated with THD (F), THD (R), THD+N and SINAD" width="82%"></picture>

```python
import phonometry as ph

thd_f = ph.thd(signal, fs, 1000.0, kind="F")          # relative to fundamental
thd_r = ph.thd(signal, fs, 1000.0, kind="R")          # relative to total RMS
d2 = ph.harmonic_distortion(signal, fs, 1000.0, 2)    # 2nd-order harmonic
```

`harmonic_analysis` bundles the fundamental, the harmonic amplitudes and the THD
(both conventions), THD+N and SINAD into one plottable result:

```python
res = ph.harmonic_analysis(signal, fs, 1000.0)
print(res.thd_f, res.thd_r, res.thd_plus_noise, res.sinad_db)
res.plot()   # annotated harmonic spectrum (needs matplotlib)
```

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
import phonometry as ph

fs = 48000
n = fs                     # 1 s -> 1 Hz bins; harmonics land on bins
t = np.arange(n) / fs
f0 = 1000.0
amps = {1: 1.0, 2: 0.02, 3: 0.012, 4: 0.006, 5: 0.003}
sig = sum(a * np.sin(2 * np.pi * k * f0 * t) for k, a in amps.items())
sig = sig + np.random.default_rng(2026).standard_normal(n) * 1.2e-2

res = ph.harmonic_analysis(sig, fs, f0, n_harmonics=len(amps))
res.plot()
plt.show()
```

</details>

## 2. THD+N and SINAD (AES17-2015 6.3)

Where THD counts only the harmonics, **THD+N** compares *everything but the
fundamental* — harmonics **and** noise — with the total signal. AES17 removes the
fundamental with a standard notch filter (`1.2 ≤ Q ≤ 3`, validated on the
*applied* zero-phase response per clause 5.2.8) and takes the ratio of the
residual to the total RMS; **SINAD** is its reciprocal in dB:

$$
\mathrm{THD{+}N} = \frac{V_\text{residual}}{V_\text{total}}, \qquad
\mathrm{SINAD} = -20\lg(\mathrm{THD{+}N})\ \mathrm{dB}.
$$

Both voltages are measured through the AES17 measurement bandwidth — a 20 Hz
high-pass plus the standard low-pass at 20 kHz (clauses 5.2.5 and 6.3.1) — so a
DC offset or ultrasonic noise at a high sample rate does not count as "noise".
The band edge is configurable, and `bandwidth=None` disables the chain and
measures the full Nyquist band.

```python
import phonometry as ph

ratio = ph.thd_plus_noise(signal, fs, 1000.0)          # ratio (0..)
db = ph.thd_plus_noise(signal, fs, 1000.0, as_db=True)  # 20·lg(ratio) dB
sinad_db = ph.sinad(signal, fs, 1000.0)                 # = -db
wide = ph.thd_plus_noise(signal, fs, 1000.0, bandwidth=None)  # full Nyquist
```

Because THD+N counts the in-band noise floor, it is at or above the
harmonic-only THD; `SINAD` is the corresponding signal-to-noise-and-distortion
headroom in dB (a quantity derived from the AES17 THD+N — AES17 itself does not
define SINAD). The notch discards a start/stop transient internally, so the
measurement wants a steady, sufficiently long capture.

### 2.1 Weighted THD (IEC 60268-3 14.12.11)

`weighted_thd` frequency-weights the notched residual before taking the ratio,
so the perceptual emphasis of the distortion products is accounted for. The
default weighting is the network the clause requires — the IEC 60268-1
Appendix A curve, i.e. ITU-R BS.468-4, which peaks at +12.2 dB near 6.3 kHz
(exposed as `itu_r_468_weighting`); `'A'` and `'C'` remain as labelled options.
Per the clause, the weighted measurement is valid for fundamental frequencies
between 31.5 Hz and 400 Hz:

```python
import phonometry as ph

print(ph.weighted_thd(signal, fs, 100.0))                  # ITU-R 468 network
print(ph.weighted_thd(signal, fs, 100.0, weighting="A"))   # A-weighted variant
print(ph.itu_r_468_weighting([6300.0]))                    # [+12.2] dB
```

## 3. Intermodulation distortion (IEC 60268-3 14.12.7–10)

When two tones pass through a non-linearity they beat against each other,
producing sum and difference products. IEC 60268-3 standardises three tests,
each with its own per-order definition:

- **Modulation distortion** (14.12.7): a large low tone `f_low` and a small
  high tone `f_high` (preferably 4:1). The per-order values are *arithmetic*
  sums of the sideband amplitudes relative to the `f_high` output:
  `d_m,2 = (a_{f₂+f₁} + a_{f₂−f₁})/a_{f₂}` and
  `d_m,3 = (a_{f₂+2f₁} + a_{f₂−2f₁})/a_{f₂}`. The result also carries the
  combined-RMS `smpte` value that SMPTE-type analyzers report (not an IEC
  quantity).
- **Difference-frequency distortion** (14.12.8): two equal high tones
  `f₁ < f₂`, referenced to `U_{2,ref} = 2·U_{2,f₂}` (the sum of both tone
  amplitudes): `d_d,2 = a_{f₂−f₁}/(a_{f₁}+a_{f₂})` and the arithmetic
  `d_d,3 = (a_{2f₂−f₁} + a_{2f₁−f₂})/(a_{f₁}+a_{f₂})`.
- **Total difference-frequency distortion** (14.12.10): a specific two-tone
  test (`f₁ = 2f₀`, `f₂ = 3f₀ − δ`; the standard tones 8 kHz and 11.95 kHz
  are the defaults) where only the two in-band products at `f₀ ∓ δ` count:
  `d_TDFD = √(a²_{f₂−f₁} + a²_{2f₁−f₂}) / (a_{f₁} + a_{f₂})`.
- **Dynamic intermodulation** (DIM, 14.12.9): a 15 kHz sine plus a
  low-pass-filtered 3.15 kHz square wave (1:4 peak-to-peak). The DIM is the
  RMS of the intermodulation products `|k·f_square ± f_sine|` that fall below
  `f_sine` (IEC 60268-3 Table 2), relative to the 15 kHz sine amplitude
  (the 14.12.9.1 definition; the 14.12.9.2 f) print of the denominator is an
  editorial defect, see [ERRATA](ERRATA.md)).

```python
import phonometry as ph

md = ph.modulation_distortion(signal, fs, 60.0, 7000.0)
print(md.d2, md.d3, md.smpte)                                       # 14.12.7
dfd2 = ph.difference_frequency_distortion(signal, fs, 13e3, 14e3, order=2)
tdfd = ph.total_difference_frequency_distortion(signal, fs)         # 8/11.95 kHz
dim = ph.dynamic_intermodulation_distortion(signal, fs)             # DIM (15k/3.15k)
```

## 4. Frequency response and coherence (Bendat & Piersol)

Given an input `x` and the output `y` of a device, the **frequency response**
`H(f)` is estimated from the Welch-averaged cross- and auto-spectra. Bendat &
Piersol (*Random Data*, 4th ed.) give two estimators, differing in which channel
carries the noise, plus the **ordinary coherence** `γ²` — the fraction of the
output power linearly explained by the input:

$$
H_1 = \frac{G_{xy}}{G_{xx}}, \qquad H_2 = \frac{G_{yy}}{G_{yx}}, \qquad
\gamma^2 = \frac{|G_{xy}|^2}{G_{xx}\,G_{yy}} \in [0, 1].
$$

`H1` is unbiased when the noise is on the output, `H2` when it is on the input;
for a noiseless linear path both recover the true response and `γ² = 1`. Additive
output noise biases `H2` upward and pulls the coherence down to `SNR/(1+SNR)`.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/frequency_response_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/frequency_response.svg" alt="Bode magnitude of an estimated H1 frequency response tracking the true response of a band-pass system, with the ordinary coherence below dropping towards the band edges where the output signal is weak relative to noise" width="82%"></picture>

```python
import phonometry as ph

res = ph.transfer_function(x, y, fs, estimator="H1")
print(res.magnitude_db, res.phase, res.coherence)
res.plot()   # Bode magnitude/phase + coherence (needs matplotlib)

freqs, gamma2 = ph.coherence(x, y, fs)
```

Coherence needs averaging over several Welch segments to be meaningful — a single
segment gives `γ² ≡ 1` by construction.

<details>
<summary>Show the code for this figure</summary>

```python
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal as sp
import phonometry as ph

fs = 48000
n = 400000
rng = np.random.default_rng(7)
x = rng.standard_normal(n)
b, a = sp.butter(2, [400.0, 4000.0], btype="band", fs=fs)   # device under test
y = sp.lfilter(b, a, x)
y = y + rng.standard_normal(n) * np.sqrt(np.mean(y ** 2)) * 0.05   # output noise

res = ph.transfer_function(x, y, fs, estimator="H1")
res.plot()
plt.show()
```

</details>

---

**Standards.** IEC 60268-3:2013, *Sound system equipment – Part 3: Amplifiers*
(clauses 14.12.2–14.12.11): total harmonic distortion `THD_F`/`THD_R` (the
14.12.3.2 formula defines the R form), nth-order harmonic distortion `dₙ`, the
per-order modulation (`d_m,n`) and difference-frequency (`d_d,n`)
intermodulation, total difference-frequency distortion, dynamic intermodulation
(DIM) and the ITU-R BS.468-4 / IEC 60268-1 weighted THD. AES17-2015,
*Measurement of digital audio equipment* (clauses 5.2.5, 5.2.8 and 6.3.1): the
THD+N ratio via the standard notch filter and the standard measurement
bandwidth; SINAD is derived from it. ITU-R BS.468-4: the weighting-network
nominal response. Bendat & Piersol (2010), *Random Data: Analysis and
Measurement Procedures* (4th ed., Wiley): the `H1` and `H2` frequency-response
estimators and the ordinary coherence `γ²`. All quantities are verified against
exact analytic oracles (synthetic signals with known harmonic/intermodulation
amplitudes, a clipped-sine Fourier oracle, a full DIM test-signal synthesis,
and a known LTI path).
