---
title: "Theory"
description: "Standards, math and design decisions behind phonometry."
---

## Octave Band Frequencies (ANSI S1.11 / IEC 61260)

The mid-band frequencies (fm) and edges (f1, f2) use a base-10 ratio:

$$
G = 10^{0.3}
$$

**Mid-band:**

$$
f_m = 1000 \cdot G^{x/b}
$$

(for odd b)

**Band edges:**

$$
f_1 = f_m \cdot G^{-1/2b}, \quad f_2 = f_m \cdot G^{1/2b}
$$

## Frequency Resolution vs FFT Bin Spacing

`octavefilter` is a **time-domain fractional-octave filter bank**, not an FFT or
Welch spectrum estimator. Therefore, its result does not have a frequency
resolution in the `fs / nfft` sense.

For `fraction=3`, the output contains one scalar level per third-octave band.
The relevant frequency granularity is the standardized band definition: center
frequency, lower edge, and upper edge. Because fractional-octave bands are
logarithmically spaced, their absolute bandwidth in Hz grows with frequency
while their relative bandwidth remains approximately constant.

For example, with `fraction=3` and `limits=[12, 20000]`, the exact third-octave
band around 1 kHz is approximately:

| Nominal band | Lower edge | Center | Upper edge | Bandwidth |
| :--- | ---: | ---: | ---: | ---: |
| 1 kHz | 891.25 Hz | 1000.00 Hz | 1122.02 Hz | 230.77 Hz |

You can inspect the exact bands with:

```python
from phonometry import getansifrequencies

fc, fl, fu, labels = getansifrequencies(fraction=3, limits=[12, 20000])
for label, center, lower, upper in zip(labels, fc, fl, fu):
    print(label, center, lower, upper, upper - lower)
```

If you need narrowband FFT bins for tonal inspection, run Welch/FFT on the
original signal and use the phonometry band edges as masks:

```python
import numpy as np
from scipy import signal
from phonometry import octavefilter, getansifrequencies

fs = 100_000
x = pressure_signal_pa  # 1D pressure signal in Pa

# Standardized third-octave levels from phonometry.
levels, centers = octavefilter(
    x,
    fs=fs,
    fraction=3,
    limits=[12, 20_000],
)

# Same standardized band definitions, including lower/upper edges.
fc, fl, fu, labels = getansifrequencies(fraction=3, limits=[12, 20_000])

# Narrowband Welch estimate on the original signal.
nperseg = min(2**15, len(x))
freq_bins, psd = signal.welch(
    x,
    fs=fs,
    window="hann",
    nperseg=nperseg,
    noverlap=nperseg // 2,
    scaling="density",
)

# Example: list the Welch bins inside the third-octave band closest to 1 kHz.
band_index = int(np.argmin(np.abs(np.asarray(fc) - 1000.0)))
in_band = (freq_bins >= fl[band_index]) & (freq_bins <= fu[band_index])

print("Selected third-octave band:", labels[band_index])
print("Welch bin spacing:", freq_bins[1] - freq_bins[0], "Hz")
for f, pxx in zip(freq_bins[in_band], psd[in_band]):
    print(f, pxx)
```

This keeps the two concepts separate: phonometry gives standardized
fractional-octave levels, while Welch gives narrowband FFT bins. With
`fs=100000` and `nperseg=2**15`, the Welch bin spacing is about `3.05 Hz`.
Window choice and overlap affect leakage and averaging variance, but they do not
change the bin spacing of each FFT segment.

When `sigbands=True`, `octavefilter` can also return the time-domain waveform
filtered by each band. Applying Welch/FFT to one selected filtered waveform can
be useful as a diagnostic view of the content inside that filtered band, but it
does not recover FFT bins from the scalar band levels.

## Magnitude Responses |H(jw)|

The library implements standard classical filter prototypes:

**1. Butterworth:** Maximally flat passband.

$$
|H(j\omega)| = \frac{1}{\sqrt{1 + (\omega/\omega_c)^{2n}}}
$$

**2. Chebyshev I:** Equiripple in passband, steeper roll-off.

$$
|H(j\omega)| = \frac{1}{\sqrt{1 + \epsilon^2 T_n^2(\omega/\omega_c)}}
$$

**3. Chebyshev II:** Inverse Chebyshev, equiripple in stopband, flat passband.

$$
|H(j\omega)| = \frac{1}{\sqrt{1 + \frac{1}{\epsilon^2 T_n^2(\omega_{stop}/\omega)}}}
$$

**4. Elliptic:** Equiripple in both, maximum selectivity.

$$
|H(j\omega)| = \frac{1}{\sqrt{1 + \epsilon^2 R_n^2(\omega/\omega_c, L)}}
$$

**5. Bessel:** Maximally flat group delay (linear phase).

$$
H(s) = \frac{\theta_n(0)}{\theta_n(s/\omega_0)}
$$

(Where $\theta_n$ is the reverse Bessel polynomial)

### Band-edge placement

For every architecture the bank places the **−3 dB points on the band edges**.
Two cases need special handling:

- **Chebyshev II**: scipy's `Wn` is the *stopband* edge. phonometry maps the
  desired −3 dB edges to stopband edges analytically — the prototype transition
  ratio is $\cosh(\operatorname{acosh}(\sqrt{10^{A/10}-1})/N)$ — applying the
  lowpass→bandpass transform in the pre-warped bilinear domain so the mapping
  stays exact for decimated bands close to Nyquist.
- **Bessel**: designed with `norm="mag"`, which defines the −3 dB point exactly
  at `Wn` (the `phase` norm would shift the edges to roughly −10 dB).

## Filter Bank Design & Numerical Stability

To ensure **100% stability** across the entire audible spectrum (even at low
frequencies like 16 Hz with high sample rates), phonometry employs two
critical strategies:

```mermaid
flowchart LR
    X["Input signal\nfs"] --> D{"Low band?"}
    D -- "yes" --> R["Decimate\nresample_poly (1/M)"] --> S1["SOS band filter\nat fs/M"]
    D -- "no" --> S2["SOS band filter\nat fs"]
    S1 --> L["Band level (RMS/peak)"]
    S2 --> L
    S1 -- "sigbands=True" --> U["Interpolate back\nresample_poly (M/1)"] --> Y["Band signal\nat fs"]
    S2 -- "sigbands=True" --> Y
```

1. **Second-Order Sections (SOS):** All filters are implemented as a series of
   cascaded biquads. This avoids the catastrophic numerical precision loss
   associated with high-order transfer functions (coefficients a, b).
2. **Multi-rate Decimation:** For low-frequency bands, the signal is
   automatically downsampled (decimated) before filtering and upsampled
   afterwards. This keeps the digital pole locations far from the unit circle
   boundary, preventing oscillation and noise. Chebyshev II banks reserve extra
   decimation headroom so their stopband edges stay below the decimated Nyquist.

## Weighting Curves (IEC 61672-1)

The A-weighting transfer function:

$$
R_A(f) = \frac{12194^2 \cdot f^4}{(f^2 + 20.6^2)\sqrt{(f^2 + 107.7^2)(f^2 + 737.9^2)}(f^2 + 12194^2)}
$$

$$
A(f) = 20 \log_{10}(R_A(f)) + 2.00
$$

The digital filter is obtained from the analog poles/zeros via the bilinear
transform. Because the bilinear transform compresses frequencies near Nyquist,
the default `high_accuracy` mode designs and runs the filter at an internally
oversampled rate (≥ 96 kHz) — see [Frequency Weighting](/phonometry/guides/weighting/).

## Time Integration

Implemented as a first-order IIR exponential integrator:

$$
y[n] = \alpha \cdot x^2[n] + (1 - \alpha) \cdot y[n-1]
$$

$$
\alpha = 1 - e^{-1 / (f_s \cdot \tau)}
$$

Where `tau` is the time constant (e.g., 125 ms for Fast).

The default initial condition is `y[-1] = 0`. Use `initial_state='first'` to
start from the first input energy, or pass a scalar/array with the previous
mean-square output state. See [Why phonometry](/phonometry/reference/why-phonometry/) for the
IEC 61672-1 tone-burst verification of this implementation.

## G-weighting (ISO 7196)

The G curve extends frequency weighting into the infrasound range. ISO 7196:1995 Table 1 (p. 2) defines it by four zeros at the origin and four complex-conjugate pole pairs, given as coordinates in Hz (multiplied by $2\pi$ to obtain rad/s):

$$
z_{1..4} = 0, \qquad
p = 2\pi \left\lbrace -0.707 \pm j0.707,\; -19.27 \pm j5.16,\; -14.11 \pm j14.11,\; -5.16 \pm j19.27 \right\rbrace \ \text{Hz}
$$

The gain $k$ is chosen so that the response is exactly **0 dB at 10 Hz** (clause 4):

$$
k = \left| \frac{\prod_i (j\omega_{10} - p_i)}{\prod_i (j\omega_{10} - z_i)} \right|, \qquad \omega_{10} = 2\pi \cdot 10 \ \text{rad/s}
$$

The four zeros against eight poles shape the characteristic response: a rise of approximately **+12 dB/octave between 1 Hz and 20 Hz**, with roll-offs of approximately **24 dB/octave** below 1 Hz and above 20 Hz. Infrasound needs its own curve because near the hearing threshold the perceived loudness of very-low-frequency tones grows much more steeply with sound pressure level than at mid frequencies — a small dB increase above threshold produces a large loudness jump — so the A curve (anchored at 1 kHz) grossly misrepresents infrasonic annoyance.

Since G acts on 0.25 Hz – 315 Hz, the plain bilinear transform is already exact there and the internal oversampling used for the A/C designs (whose action extends to 16 kHz) is not applied.

See the [Frequency Weighting guide](/phonometry/guides/weighting/) for usage.

## Equal-loudness contours (ISO 226:2023)

A tone has a *loudness level* of $L_N$ phon when it is judged equally loud as a 1 kHz pure tone at $L_N$ dB SPL. ISO 226:2023 Formula (1) (clause 4.1, p. 2) gives the SPL of a pure tone at frequency $f$ that reaches loudness level $L_N$:

$$
L_f = \frac{10}{\alpha_f} \log_{10}\left[ \left(4 \cdot 10^{-10}\right)^{0.3 - \alpha_f} \left( 10^{\,0.03 L_N} - 10^{\,0.072} \right) + 10^{\,\alpha_f (T_f + L_U)/10} \right] - L_U
$$

Formula (2) (clause 4.2) inverts it, returning the loudness level of a tone at SPL $L_f$:

$$
L_N = \frac{100}{3} \log_{10}\left[ \frac{10^{\,\alpha_f (L_f + L_U)/10} - 10^{\,\alpha_f (T_f + L_U)/10}}{\left(4 \cdot 10^{-10}\right)^{0.3 - \alpha_f}} + 10^{\,0.072} \right]
$$

The three parameters come from Table 1 (p. 4), tabulated at the 29 preferred third-octave frequencies of ISO 266 from 20 Hz to 12.5 kHz:

- $\alpha_f$ — exponent for loudness perception at frequency $f$,
- $L_U$ — magnitude of the linear transfer function, normalized at 1 kHz ($L_U = 0$ at 1 kHz),
- $T_f$ — threshold of hearing at $f$, in dB.

The standard specifies **no interpolation** between the tabulated frequencies. Formula (1) is specified for **20 phon to 90 phon** between 20 Hz and 4 kHz, and only up to **80 phon between 5 kHz and 12.5 kHz** — above 80 phon the contour therefore stops at 4 kHz. Values outside these limits from Formula (2) are extrapolations the standard labels as informative only.

See the [Levels guide](/phonometry/guides/levels/) for usage.

## Tone prominence: TNR and PR (ECMA-418-1)

Both methods operate on a Hann-windowed, RMS-averaged power spectrum (clauses 11.1 / 12.1) and use the clause 10 critical-band model. The critical bandwidth centred on a tone at $f$ is (Formula 2):

$$
\Delta f_c = 25.0 + 75.0 \left(1.0 + 1.4 \left(\tfrac{f}{1000}\right)^2\right)^{0.69} \ \text{Hz}
$$

Band edges are placed **arithmetically** for $f \le 500$ Hz (Formulae 4–5): $f_{1,2} = f \mp \Delta f_c / 2$, and **geometrically** above (Formulae 7–8): $f_1 = -\Delta f_c/2 + \sqrt{\Delta f_c^2 + 4 f^2}/2$, $f_2 = f_1 + \Delta f_c$.

**TNR** (clause 11). The tone band spans the spectral minima on both sides of the peak within 15 % of $\Delta f_c$ (clause 11.2). The tone power subtracts the straight line connecting the band-edge bins (Formula 9): over $N$ tone-band bins, $P_t = \sum_k P_k - (P_{\text{lo}} + P_{\text{hi}})\,N/2$. The masking-noise power is the remaining critical-band power rescaled to the full critical bandwidth (Formula 10): $P_n = (P_{\text{band}} - P_t) \cdot \Delta f_c / \Delta f_{\text{band}}$, and $\mathrm{TNR} = 10\log_{10}(P_t/P_n)$ (Formula 11). The prominence criterion (Formulae 12–13) is

$$
\mathrm{TNR}_{\text{crit}} = \begin{cases} 8.0 + 8.33 \log_{10}(1000/f_t) \ \text{dB} & f_t < 1\,\text{kHz} \\ 8.0 \ \text{dB} & f_t \ge 1\,\text{kHz} \end{cases}
$$

**PR** (clause 12) compares the level of the critical band centred on the tone, $L_M$, with the mean power of the two **contiguous** critical bands $L_L$, $L_U$ (edges from the fitted Formulae 21–22 with Tables 2–3): $\mathrm{PR} = 10\log_{10} P_M - 10\log_{10}\left[(P_L + P_U)/2\right]$ (Formula 23). For $f_t \le 171.4$ Hz the lower band is truncated at 20 Hz and its power rescaled to a **100 Hz bandwidth** (Formula 24). The criterion (Formulae 25–26) is 9.0 dB at $f_t \ge 1$ kHz, rising as $9.0 + 10.0\log_{10}(1000/f_t)$ below. Tones are assessed within the 89.1 Hz – 11.2 kHz range of interest (clauses 11.5 / 12.6).

See the [Levels guide](/phonometry/guides/levels/) for usage.

## Event and dose metrics

**Sound exposure level** (SEL; LAE with A-weighting, IEC 61672-1:2013) normalizes the energy of a discrete event (aircraft flyover, train pass) to a 1 s reference duration:

$$
\mathrm{SEL} = L_{eq,T} + 10 \log_{10}\left(\frac{T}{T_0}\right), \qquad T_0 = 1\ \text{s}
$$

**Sound exposure** $E$ (IEC 61252, 3.1) is the time integral of the squared A-weighted sound pressure, expressed in pascal-squared hours:

$$
E = \int_0^T p_A^2(t)\, dt = \overline{p_A^2} \cdot T \quad [\text{Pa}^2\text{h}]
$$

When the recording is a representative sample of a longer shift, $E$ scales the measured mean square by the actual exposure duration. The **normalized 8 h level** (IEC 61252, 3.3) converts exposure to the steady level that carries the same energy over a nominal working day:

$$
L_{EX,8h} = 10 \log_{10}\left(\frac{E}{8\ \text{h} \cdot p_0^2}\right), \qquad p_0 = 20\ \mu\text{Pa}
$$

It is identical to $L_{EP,d}$ of Directive 86/188/EEC and $L_{EX,8h}$ of ISO 1999 (BS EN 61252:1995, 3.3 NOTES 5–6). The anchor of BS EN 61252:1995 (3.3 NOTE 4): an exposure of **3.2 Pa²h corresponds to $L_{EX,8h}$ of exactly 90 dB**.

**LCpeak** (IEC 61672-1:2013, subclause 5.13) is the absolute maximum of the C-weighted sound pressure expressed in dB, $L_{Cpeak} = 20\log_{10}(\max|p_C(t)|/p_0)$ — the quantity behind the 135/137/140 dB(C) occupational action limits. The implementation is verified against the one-cycle and half-cycle reference responses of Table 5.

See the [Levels guide](/phonometry/guides/levels/) for usage and the [Calibration guide](/phonometry/guides/calibration/) for absolute-scale setup.

## Environmental descriptors (ISO 1996-1)

The **day-evening-night level** $L_{den}$ (ISO 1996-1:2016, 3.6.4) is an energy average over the 24 h day with penalty weightings of **+5 dB for the evening** and **+10 dB for the night**:

$$
L_{den} = 10 \log_{10}\left\lbrace\frac{1}{24}\left[ t_d\, 10^{0.1 L_{day}} + t_e\, 10^{0.1 (L_{evening} + 5)} + t_n\, 10^{0.1 (L_{night} + 10)} \right]\right\rbrace
$$

with default period durations $(t_d, t_e, t_n) = (12, 4, 8)$ h — countries may define the periods differently (3.6.4 Note 1). The **day-night level** $L_{dn}$ (3.6.5) drops the evening period:

$$
L_{dn} = 10 \log_{10}\left\lbrace\frac{1}{24}\left[ t_d\, 10^{0.1 L_{day}} + t_n\, 10^{0.1 (L_{night} + 10)} \right]\right\rbrace, \qquad (t_d, t_n) = (15, 9)\ \text{h}
$$

Both are special cases of the **composite whole-day rating level** (6.5, generalizing Formulae 5–6), where each period $i$ contributes its rating level $L_i$ plus an adjustment $K_i$, weighted by its share of the day:

$$
L_R = 10 \log_{10}\left[ \sum_i \frac{h_i}{24}\, 10^{0.1 (L_i + K_i)} \right], \qquad \sum_i h_i = 24\ \text{h}
$$

The adjustments $K_i$ cover time-of-day penalties (ISO 1996-1 Table A.1: evening 5 dB, night 10 dB) as well as source-character adjustments — e.g. tonal penalties, which the ECMA-418-1 TNR/PR assessments can justify objectively.

See the [Levels guide](/phonometry/guides/levels/) for usage.

## Zwicker loudness (ISO 532-1)

The ear analyzes sound in **critical bands**: frequency regions within which energy is summed before loudness is formed. The **Bark scale** maps frequency to critical-band rate $z$, 0 to 24 Bark, and ISO 532-1:2017 samples the specific loudness $N'(z)$ at 0.1-Bark steps (240 values). The implementation is a clean-room port of the standard's normative reference program (Annex A.4) and proceeds in stages:

1. **One-third-octave levels** — 28 bands, 25 Hz to 12.5 kHz (the Annex A filterbank at 48 kHz, Tables A.1/A.2). For time-varying sounds the squared band outputs are smoothed by three cascaded low-passes with $\tau = 2/(3 f_c)$ ($f_c$ capped at 1 kHz) and sampled every 2 ms.
2. **Low-frequency grouping** — the 11 bands up to 250 Hz receive the equal-loudness corrections of Table A.3 and are summed into the first three critical bands (25–80, 100–160, 200–250 Hz).
3. **a0 transmission** — the outer/middle-ear transfer correction of Table A.4 (plus the diffuse-field difference of Table A.5 when `field='diffuse'`) yields the critical-band levels $L_E$.
4. **Core loudness** — each of the 20 critical bands is transformed with the threshold-in-quiet levels $L_{TQ}$ of Table A.6 (after the bandwidth adaptation DCB of Table A.7):

$$
N_c = 0.0635 \cdot 10^{0.025 L_{TQ}} \left[ \left( 1 - s + s \cdot 10^{(L_E - L_{TQ})/10} \right)^{0.25} - 1 \right] \ \text{sone/Bark}, \qquad s = 0.25
$$

(the reference program's form of Zwicker's loudness transformation; bands below threshold contribute zero).

5. **Slopes** — level-dependent upper masking slopes (steepness per specific-loudness range and critical band, Tables A.8/A.9) attach decaying flanks toward higher $z$; the total loudness is the area under the pattern:

$$
N = \int_0^{24} N'(z)\ dz \ \ \text{sone}
$$

For time-varying sounds a nonlinear temporal decay (time constants 5/15/75 ms, clause 6.3) and the duration-dependent weighting of the total loudness (3.5 ms and 70 ms low-passes weighted 0.47/0.53, clause 6.4) precede the 500 Hz loudness-vs-time output and the percentile values N5/N10 (clause 6.5).

**Sone and phon** are tied together by the 1 kHz anchor (1 sone = 40 phon; clause 5.6):

$$
N = 2^{(L_N - 40)/10} \ \text{sone} \qquad \Longleftrightarrow \qquad L_N = 40 + 10 \log_2 N \ \text{phon} \qquad (N \ge 1)
$$

below 1 sone the reference program uses $L_N = 40 (N + 0.0005)^{0.35}$, floored at 3 phon.

See the [Psychoacoustics guide](/phonometry/guides/psychoacoustics/) for usage.

## Modulation transfer and STI (IEC 60268-16)

Speech intelligibility rides on the slow intensity modulations of the speech envelope. The **modulation transfer function** $m(F)$ of a transmission channel is the ratio of received to emitted modulation depth of the octave-band intensity envelope at modulation frequency $F$; the full STI evaluates it at the 14 one-third-octave modulation frequencies 0.63–12.5 Hz in the seven octave bands 125 Hz – 8 kHz (A.2.2). From a measured impulse response the **Schroeder closed form** gives it directly (indirect method):

$$
m_k(f_m) = \frac{\left| \int_0^{\infty} h_k^2(t)\ e^{-j 2 \pi f_m t}\ dt \right|}{\int_0^{\infty} h_k^2(t)\ dt}
$$

Steady background noise multiplies each band's $m$ by the intensity ratio (the noise term):

$$
m'_k = m_k \cdot \frac{I_k}{I_k + I_{n,k}} = \frac{m_k}{1 + 10^{-\mathrm{SNR}_k/10}}
$$

and when absolute band levels are known the full correction $m'_k = m_k I_k / (I_k + I_{am,k} + I_{rt,k} + I_{n,k})$ adds the auditory masking intensity $I_{am,k}$ (from the next lower octave band, Table A.2) and the absolute reception threshold $I_{rt,k}$ (Table A.3). Each corrected $m$ maps to an **effective SNR**, clipped to the ±15 dB range where intelligibility actually varies, then to a transmission index (A.5.4/A.5.5):

$$
\mathrm{SNR}_{\mathrm{eff}} = 10 \log_{10} \frac{m}{1 - m}\ \text{dB}, \qquad \mathrm{TI} = \frac{\mathrm{SNR}_{\mathrm{eff}} + 15}{30}
$$

The band MTI is the mean TI over the modulation frequencies, and the STI weights the bands with the male factors $\alpha_k$, $\beta_k$ of Ed. 5 Table A.1 (A.5.6):

$$
\mathrm{STI} = \sum_{k=1}^{7} \alpha_k\ \mathrm{MTI}_k - \sum_{k=1}^{6} \beta_k \sqrt{\mathrm{MTI}_k\ \mathrm{MTI}_{k+1}}
$$

truncated to 1.0. STIPA (Annex B) samples the same physics with just two modulation frequencies per band (Table B.1) on a test signal with source modulation index 0.55; the received depths are measured by sine/cosine correlation of the ~100 Hz low-passed intensity envelopes $I_k(t)$ over an integer number of modulation periods:

$$
m_{dr} = \frac{2 \sqrt{\left( \sum_t I_k(t) \sin 2 \pi f_m t \right)^2 + \left( \sum_t I_k(t) \cos 2 \pi f_m t \right)^2}}{\sum_t I_k(t)}, \qquad m = \frac{m_{dr}}{0.55}
$$

See the [Psychoacoustics guide](/phonometry/guides/psychoacoustics/) for usage.

## Sound intensity (IEC 61043)

Sound intensity is the time-averaged acoustic power flux $I = \overline{p u}$. The particle velocity follows from **Euler's equation** (linearized conservation of momentum):

$$
\rho_0 \frac{\partial u}{\partial t} = -\frac{\partial p}{\partial r}
$$

A p-p probe approximates the pressure gradient by the **finite difference** of two microphones a spacer distance $\Delta r$ apart (IEC 61043:1994, definition 3.2):

$$
p = \frac{p_1 + p_2}{2}, \qquad u = -\frac{1}{\rho_0 \Delta r} \int (p_2 - p_1)\ dt, \qquad I = \overline{p\ u}
$$

For stationary signals the same estimator has an exact frequency-domain form through the imaginary part of the one-sided **cross spectrum** $G_{12}$ of the two pressures — the implementation estimates it with Welch-averaged, Hann-windowed segments:

$$
I(f) = -\ \frac{\mathrm{Im}\lbrace G_{12}(f)\rbrace}{2 \pi f\ \rho_0\ \Delta r}
$$

The finite difference underestimates the true plane-wave intensity by the factor

$$
\frac{\sin(k \Delta r)}{k \Delta r}, \qquad k = \frac{2 \pi f}{c}
$$

— IEC 61043 clause 7.3 specifies the probe intensity response with exactly this argument and Table 3 tabulates it (e.g. −10.5 dB at 6.3 kHz for a 25 mm spacer). Below $f = 0.1 c / \Delta r$ (i.e. $k \Delta r$ under 0.63) the bias stays within about 0.3 dB; `bias_correction` provides the reciprocal factor per band and `max_valid_frequency` the bound.

The **pressure-intensity index** $\delta_{pI} = L_p - L_I$ measures how reactive the field is: in a free plane progressive wave it equals $10 \log_{10}(\rho_0 c / 400) = 0.14$ dB, while large values flag reactive or noisy fields in which the inter-channel phase error dominates. ISO 9614-1:1993 Annex A generalizes it over a measurement surface as the indicator F2 (with F3 for negative partial power and F4 for field non-uniformity), and the instrument's **dynamic capability** $L_d = \delta_{pI0} - K$ (pressure-residual intensity index minus the bias error factor: 10 dB for grades 1/2, 7 dB for grade 3) must exceed F2 for the measurement to be valid (criterion 1).

See the [Sound Intensity guide](/phonometry/guides/intensity/) for usage.
