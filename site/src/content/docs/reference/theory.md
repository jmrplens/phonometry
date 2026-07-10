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

`octave_filter` is a **time-domain fractional-octave filter bank**, not an FFT or
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
from phonometry import nominal_frequencies

fc, fl, fu, labels = nominal_frequencies(fraction=3, limits=[12, 20000])
for label, center, lower, upper in zip(labels, fc, fl, fu):
    print(label, center, lower, upper, upper - lower)
```

If you need narrowband FFT bins for tonal inspection, run Welch/FFT on the
original signal and use the phonometry band edges as masks:

```python
import numpy as np
from scipy import signal
from phonometry import octave_filter, nominal_frequencies

fs = 100_000
# any 1D pressure signal in Pa (synthesized here so the example runs)
pressure_signal_pa = 0.02 * np.random.default_rng(0).standard_normal(fs)
x = pressure_signal_pa

# Standardized third-octave levels from phonometry.
levels, centers = octave_filter(
    x,
    fs=fs,
    fraction=3,
    limits=[12, 20_000],
)

# Same standardized band definitions, including lower/upper edges.
fc, fl, fu, labels = nominal_frequencies(fraction=3, limits=[12, 20_000])

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

When `sigbands=True`, `octave_filter` can also return the time-domain waveform
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
oversampled rate (≥ 144 kHz) — see [Frequency Weighting](/phonometry/guides/weighting/).

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
p = 2\pi \left\lbrace -0.707 \pm j0.707,\  -19.27 \pm j5.16,\  -14.11 \pm j14.11,\  -5.16 \pm j19.27 \right\rbrace \ \text{Hz}
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
L_f = \frac{10}{\alpha_f} \log_{10}\left[ \left(4 \cdot 10^{-10}\right)^{0.3 - \alpha_f} \left( 10^{\ 0.03 L_N} - 10^{\ 0.072} \right) + 10^{\ \alpha_f (T_f + L_U)/10} \right] - L_U
$$

Formula (2) (clause 4.2) inverts it, returning the loudness level of a tone at SPL $L_f$:

$$
L_N = \frac{100}{3} \log_{10}\left[ \frac{10^{\ \alpha_f (L_f + L_U)/10} - 10^{\ \alpha_f (T_f + L_U)/10}}{\left(4 \cdot 10^{-10}\right)^{0.3 - \alpha_f}} + 10^{\ 0.072} \right]
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

**TNR** (clause 11). The tone band spans the spectral minima on both sides of the peak within 15 % of $\Delta f_c$ (clause 11.2). The tone power subtracts the straight line connecting the band-edge bins (Formula 9): over $N$ tone-band bins, $P_t = \sum_k P_k - (P_{\text{lo}} + P_{\text{hi}})\ N/2$. The masking-noise power is the remaining critical-band power rescaled to the full critical bandwidth (Formula 10): $P_n = (P_{\text{band}} - P_t) \cdot \Delta f_c / \Delta f_{\text{band}}$, and $\mathrm{TNR} = 10\log_{10}(P_t/P_n)$ (Formula 11). The prominence criterion (Formulae 12–13) is

$$
\mathrm{TNR}_{\text{crit}} = \begin{cases} 8.0 + 8.33 \log_{10}(1000/f_t) \ \text{dB} & f_t < 1\ \text{kHz} \\ 8.0 \ \text{dB} & f_t \ge 1\ \text{kHz} \end{cases}
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
E = \int_0^T p_A^2(t)\ dt = \overline{p_A^2} \cdot T \quad [\text{Pa}^2\text{h}]
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
L_{den} = 10 \log_{10}\left\lbrace\frac{1}{24}\left[ t_d\ 10^{0.1 L_{day}} + t_e\ 10^{0.1 (L_{evening} + 5)} + t_n\ 10^{0.1 (L_{night} + 10)} \right]\right\rbrace
$$

with default period durations $(t_d, t_e, t_n) = (12, 4, 8)$ h — countries may define the periods differently (3.6.4 Note 1). The **day-night level** $L_{dn}$ (3.6.5) drops the evening period:

$$
L_{dn} = 10 \log_{10}\left\lbrace\frac{1}{24}\left[ t_d\ 10^{0.1 L_{day}} + t_n\ 10^{0.1 (L_{night} + 10)} \right]\right\rbrace, \qquad (t_d, t_n) = (15, 9)\ \text{h}
$$

Both are special cases of the **composite whole-day rating level** (6.5, generalizing Formulae 5–6), where each period $i$ contributes its rating level $L_i$ plus an adjustment $K_i$, weighted by its share of the day:

$$
L_R = 10 \log_{10}\left[ \sum_i \frac{h_i}{24}\ 10^{0.1 (L_i + K_i)} \right], \qquad \sum_i h_i = 24\ \text{h}
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

## Advanced loudness models & sound quality

ISO 532-1 is one of three loudness models; two newer families refine the auditory front-end and add the sound-quality metrics tonality and roughness.

### Moore-Glasberg loudness (ISO 532-2:2017, ISO 532-3:2023)

Instead of Zwicker's fixed critical bands, the Moore-Glasberg model forms a continuous **excitation pattern** on the ERB-number ("Cam") scale using level-dependent **rounded-exponential (roex)** auditory filters. As a function of the normalized frequency deviation $g = |f - f_c| / f_c$ from a filter centred at $f_c$, the filter weighting is

$$
W(g) = (1 + p\ g)\ e^{-p\ g}
$$

where the slope $p$ grows with the source level, broadening the lower skirt as level rises (ISO 532-2, Formulae 2–5); this reproduces the upward spread of masking. Passing the stimulus intensity through every filter gives the excitation $E(i)$, and a compressive law maps it to the **specific loudness** $N'(i)$ in sone/Cam (Formulae 7–9), of the mid-level form

$$
N'(i) = C \left[ \left( G\ \frac{E(i)}{E_0} + A \right)^{\alpha} - A^{\alpha} \right]
$$

with the calibration constant $C = 0.0617$ sone/Cam (ISO 532-2; $0.063$ in ISO 532-3). The total loudness is the area under the pattern,

$$
N = \int N'(i)\ di \ \ \text{sone}
$$

and a binaural-inhibition stage (Formulae 10–13) combines the ears so a diotic sound is louder than the same sound at one ear. The 1 kHz / 40 dB SPL anchor gives exactly 1 sone.

**ISO 532-3** makes this time-varying. A running spectrum from six parallel Hann-windowed FFTs (segment lengths 2–64 ms, each contributing its own frequency range, updated every $T_0 = 1$ ms) drives the same excitation and specific-loudness chain, integrated by two cascaded first-order smoothers with $\alpha = 1 - e^{-T_0 / \tau}$,

$$
S(t) = \alpha\ x(t) + (1 - \alpha)\ S(t - 1)
$$

using a fast time constant on the attack and a slower one on the release. This yields the **short-term loudness** $S'(t)$ (attack/release near 20–30 ms) and the **long-term loudness** $S''(t)$ (near 0.1–0.75 s); the peak long-term loudness $N_{\max} = \max_t S''(t)$ predicts the loudness of sounds up to about 5 s.

### Sottek Hearing Model (ECMA-418-2:2025)

ECMA-418-2 builds all three of its metrics on one auditory front-end (Clause 5): an outer/middle-ear filter, a bank of 53 overlapping gammatone-like band-pass filters spaced on the Bark_HMS scale ($z = 0.5$ to $26.5$), half-wave rectification, and a short-block RMS $\tilde{p}(l, z)$ per band $z$ and time block $l$. A compressive nonlinearity (Formula 23) turns the band RMS into the **specific basis loudness** $N'_{\mathrm{basis}}(l, z)$, whose calibration constant $c_N$ fixes a 1 kHz / 40 dB SPL tone at 1 sone_HMS. The loudness assembles the tonal and noise loudness (below) over bands and time (Formulae 113–117); it grows about $1.65\times$ per 10 dB, more slowly than Zwicker's factor of 2 — an intrinsic property of the Sottek summation.

### Tonality — autocorrelation of the band signal (ECMA-418-2)

A tonal component is periodic, so it survives in the **autocorrelation function** (ACF) of a band's rectified signal while broadband noise decorrelates. For each band the unbiased ACF of the block is

$$
\phi_z(m) = \frac{1}{M - m} \sum_{n=0}^{M - 1 - m} p_z(n)\ p_z(n + m)
$$

A windowed spectral estimate of $\phi_z$ separates a **tonal loudness** $N'_{\mathrm{tonal}}(l, z)$ from the **noise loudness** $N'_{\mathrm{noise}}(l, z)$ (Formulae 36–48). The specific tonality is the tonal loudness scaled by a smooth signal-to-noise gate $q(l)$ (Formulae 49–51),

$$
T'(l, z) = c_T\ q(l)\ N'_{\mathrm{tonal}}(l, z)
$$

and the single value $T$ (tu_HMS) is the gated time-average of the per-block maximum over bands (Formulae 61–64). The constant $c_T$ fixes the 1 kHz / 40 dB tone at 1 tu_HMS, and the band of the ACF peak gives the tonal frequency $f_{\mathrm{ton}}$.

### Roughness — envelope modulation (ECMA-418-2)

Roughness is the sensation of fast (roughly 20–300 Hz) amplitude modulation, strongest near 70 Hz. From each band's envelope $p_E(n)$ (Hilbert magnitude), a modulation spectrum is formed and weighted by a modulation-rate function peaking near 70 Hz and by the modulation depth; correlating the modulation across neighbouring bands and applying the specified temporal filtering yields the **specific roughness** $R'(l_{50}, z)$ and the time-dependent roughness

$$
R(l_{50}) = \sum_z R'(l_{50}, z) \ \ \text{asper}
$$

(Formulae 65–111). The single value $R$ is the 90th percentile of $R(l_{50})$ over time (Clause 7.1.10); the constant $c_R$ (Formula 104) calibrates the reference sound — a 1 kHz carrier 100 % amplitude-modulated at 70 Hz at 60 dB SPL — to 1 asper.

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


## Room and building acoustics (ISO 18233, ISO 3382, ISO 16283, ISO 10140, EN 12354, ISO 12999, ISO 717, ISO 354)

### Deterministic-excitation impulse response (ISO 18233)

A room/transmission path is modelled as **linear time-invariant**, so its impulse response $h(t)$ carries everything. ISO 18233 replaces the classical noise-burst decay with a deterministic excitation that is **deconvolved** into $h(t)$, gaining 20–30 dB of effective signal-to-noise ratio. The exponential sine sweep (ESS, Annex B) has instantaneous frequency $f(t) = f_1 (f_2/f_1)^{t/T}$, so its phase is the closed-form integral of $2 \pi f(t)$:

$$
\varphi(t) = \frac{2 \pi f_1 T}{\ln(f_2/f_1)} \left[ \left( \frac{f_2}{f_1} \right)^{t/T} - 1 \right] .
$$

A constant time-per-octave makes the ESS spectrum pink (−3 dB/octave). Deconvolution is done by **linear** (non-circular, zero-padded) spectral division $H = Y\ \overline{X} / (|X|^2 + \varepsilon)$, the Tikhonov term $\varepsilon$ (a fraction of $\max |X|^2$) preventing noise blow-up at the band edges. Since a low-to-high sweep places harmonic-distortion products at negative arrival times, they fall in the wrapped tail and are removed by keeping the causal part (Farina). The MLS method (Annex A) instead exploits that the circular autocorrelation of a maximum-length sequence of length $2^N-1$ is a periodic delta, so $h = \operatorname{xcorr}_{\text{circ}}(\text{recorded}, \text{mls}) / 2^N$; synchronous averaging of $n$ periods adds $10 \log_{10} n$ dB.

### Schroeder backward integration (ISO 3382-1, 5.3.3)

The band decay curve is the **backward-integrated** squared IR (Schroeder):

$$
E(t) = \int_t^{\infty} p^2(\tau)\ d\tau = \int_0^{\infty} p^2\ d\tau - \int_0^t p^2\ d\tau , \qquad L(t) = 10 \log_{10} \frac{E(t)}{E(0)}\ \text{dB},
$$

i.e. a reversed cumulative sum in discrete time. Backward integration cancels the random fluctuation of a single squared IR: for a purely exponential energy decay $p^2(t) = e^{-a t}$ it gives $E(t) = e^{-a t}/a$, an exactly straight line $L(t) = -(10 a / \ln 10)\ t$. Background noise flattens $E(t)$, so integration is truncated at the crossing $t_1$ of the fitted decay line with the noise level and the missing tail is compensated by an exponential with the fitted rate; without that term the finite integral systematically **underestimates** $T$.

### Regression windows and validity (ISO 3382-2, Clause 6, Annex B/C)

Reverberation time is a least-squares fit $L = a + b t$ over a window, extrapolated to 60 dB via $T = -60/b$ (Annex C): **EDT** on 0 to −10 dB, **T20** on −5 to −25 dB, **T30** on −5 to −35 dB. A single-slope decay gives EDT = T20 = T30; a fast early / slow late double slope gives EDT < T30. Validity uses the dynamic-range rule of 5.3.3 — the noise must sit at least 25 dB below the IR peak for EDT (evaluation span + 15 dB), tightened to 46 dB for T20 and 54 dB for T30 so the tail-compensation bias of a flagged-valid value stays within the 5 % JND — and the **curvature** $C = 100\ (T_{30}/T_{20} - 1)$ % (Annex B) flags a non-straight decay above 10 %.

### Clarity, definition and centre time (ISO 3382-1, Annex A)

Splitting the energy at an early/late boundary $t_e$ gives the early-to-late index and the definition ratio:

$$
C_{te} = 10 \log_{10} \frac{\int_0^{t_e} p^2\ dt}{\int_{t_e}^{\infty} p^2\ dt}\ \text{dB}, \qquad D_{50} = \frac{\int_0^{0.05} p^2\ dt}{\int_0^{\infty} p^2\ dt}, \qquad C_{50} = 10 \log_{10} \frac{D_{50}}{1 - D_{50}},
$$

with $t_e = 50$ ms (C50, speech) or 80 ms (C80, music), and the **centre time** $T_s = \int_0^{\infty} t\ p^2\ dt / \int_0^{\infty} p^2\ dt$. For a pure exponential decay these have closed forms $C_{te} = 10 \log_{10}(e^{a t_e} - 1)$ and $T_s = 1/a$; at $T = 1$ s ($a = 13.8155$) they evaluate to C80 = 3.05 dB, C50 = −0.02 dB, D50 = 0.499 and Ts = 72.4 ms — the values the implementation reproduces. Table A.1 JNDs (EDT 5 %, C80 1 dB, D50 0.05, Ts 10 ms) bound how finely each is worth reporting.

### Open-plan spatial decay (ISO 3382-3, Clause 6)

The spatial decay rate of A-weighted speech is the ordinary least-squares slope of $L_{p,A,S}$ against $\lg(r/r_0)$ ($r_0 = 1$ m) over the 2–16 m positions, rescaled to a per-doubling figure, and the nominal level is read off the same line at 4 m:

$$
L = a + b\ \lg(r/r_0), \qquad D_{2,S} = -\lg(2)\ b, \qquad L_{p,A,S,4\text{m}} = a + b\ \lg(4/r_0).
$$

The distraction distance rD and privacy distance rP are the distances where a **linear** (not logarithmic) regression of STI against distance crosses 0.50 and 0.20; a non-negative fitted slope (STI not falling with distance) makes them undefined, realising the standard's "can prove impossible to determine" note.

### Field insulation and weighted rating (ISO 16283-1, ISO 717-1)

Per one-third-octave band the level difference $D = L_1 - L_2$ (energy-averaged over microphone positions, $L = 10 \log_{10}[(1/n) \sum_i 10^{L_i/10}]$) is normalised two ways: the standardized level difference $D_{nT} = D + 10 \log_{10}(T/T_0)$ with $T_0 = 0.5$ s (so $D_{nT} = D$ when $T = T_0$), and the apparent sound reduction index $R' = D + 10 \log_{10}(S/A)$ with the Sabine absorption area $A = 0.16\ V / T$, hence $R' = D + 10 \log_{10}[S T / (0.16\ V)]$.

The single-number rating (ISO 717-1, Clause 4.4) shifts the Table 3 **reference curve** in 1 dB steps toward the measured curve until the sum of *unfavourable* deviations $\sum_i \max(0, \text{ref}_i + k - \text{meas}_i)$ is maximal but $\le$ 32.0 dB (16 thirds) or 10.0 dB (5 octaves); the rating $R_w$ is the shifted reference at 500 Hz. The **spectrum adaptation terms** are $C = X_{A1} - X_w$ and $C_{tr} = X_{A2} - X_w$ with $X_{Aj} = -10 \log_{10} \sum_i 10^{(L_{ij} - X_i)/10}$ (Table 4 spectra No. 1 pink noise, No. 2 urban traffic), each rounded to an integer. The ISO 717-1 Annex C worked example ($R_w = 30$, $C = -2$, $C_{tr} = -3$, unfavourable sum 31.8 dB) is reproduced exactly.

### Impact insulation and absorption (ISO 16283-2, ISO 717-2, ISO 354)

Impact insulation swaps the airborne source for a standardized **tapping
machine** and rates the receiving-room level, so the sign conventions flip. The
standardized and normalized impact levels are $L'_{nT} = L_i - 10 \log_{10}(T/T_0)$
(the reverberation term is *subtracted*, opposite to $D_{nT}$) and
$L'_n = L_i + 10 \log_{10}(A/A_0)$ with $A_0 = 10$ m² and $A = 0.16\ V/T$. The
ISO 717-2 rating shifts the Table 3 reference curve until $\sum_i \max(0, \text{meas}_i - (\text{ref}_i + k))$
is maximal but $\le$ 32.0 dB (16 thirds) or 10.0 dB (5 octaves) — the
*unfavourable* deviation now counts where the **measurement exceeds** the
reference (impact noise is worse when louder), the mirror image of ISO 717-1.
The rating is the shifted reference at 500 Hz, reduced by a further 5 dB for
octave bands, and the adaptation term is $C_I = L_{n,\text{sum}} - 15 - L_{n,w}$
with the energetic sum $L_{n,\text{sum}} = 10 \log_{10} \sum_i 10^{L_i/10}$ over
100–2500 Hz (thirds) or 125–2000 Hz (octaves). The ISO 717-2 Annex C examples
are reproduced exactly (thirds $L_{n,w} = 79$, $C_I = -11$; octaves $54$, $0$),
via the same monotone shift search as ISO 717-1 run on the negated curves.

Sound absorption (ISO 354) measures the equivalent absorption area from
Sabine's relation applied to a reverberation room empty and with the specimen:
$A = 55.3\ V/(c\ T) - 4 V m$ (the $4 V m$ term is the air absorption, $m$ the
power attenuation coefficient in 1/m), so the specimen area is
$A_T = A_2 - A_1$ and its coefficient $\alpha_s = A_T/S$. With the speed of
sound from Eq. (6), $c = 331 + 0.6\ t$ (°C), and $m$ converted from an
ISO 9613-1 attenuation coefficient by $m = \alpha / (10 \lg e)$. Because
diffraction and edge scattering intercept more than the flat sample area,
$\alpha_s$ is left unclamped and may exceed 1.0 (Clause 3.7 NOTE 2).

### Laboratory vs field normalization (ISO 10140, ISO 16283)

The field indices carry a prime because they include flanking transmission
around the partition; the laboratory indices do not, because a qualified
facility suppresses it. The algebra is otherwise identical, differing only in
which quantity is normalised. The airborne pair is the direct laboratory sound
reduction index $R = L_1 - L_2 + 10 \log_{10}(S/A)$ (ISO 10140-2) versus the
apparent field index $R' = L_1 - L_2 + 10 \log_{10}(S/A)$ (ISO 16283-1), the
same closed form evaluated with the facility's known $A$ or the room's measured
$A = 0.16\ V/T$. The impact pair is the normalized laboratory level
$L_n = L_i + 10 \log_{10}(A/A_0)$ (ISO 10140-3) versus the field $L'_n$
(ISO 16283-2), both referenced to $A_0 = 10$ m². Before either is formed the
receiving-room level is corrected for background noise by the energy
subtraction $L = 10 \log_{10}(10^{L_{sb}/10} - 10^{L_b/10})$ for a 6–15 dB
signal-to-background margin, capped at a fixed $1.3$ dB (the limit of
measurement) at or below 6 dB and omitted at or above 15 dB (ISO 10140-4,
Clause 4.3) — the laboratory analogue of the 6/10 dB rule of ISO 16283-1. The
façade extension (ISO 16283-3) replaces the source-room level by the level 2 m
in front of the façade, $D_{2m} = L_{1,2m} - L_2$, and adds a fixed
angle-of-incidence correction to the element sound reduction index, $-1.5$ dB
for the 45° loudspeaker method ($R'_{45°}$) and $-3$ dB for the all-angle
road-traffic method ($R'_{tr,s}$); all three carry the ISO 717-1 airborne
single number.

### Flanking transmission prediction (EN 12354-1/2)

The apparent field index is the energetic sum of the direct path $Dd$ and, for
each flanking element $F=f$ across its junction with the separating element, the
three paths $Ff$, $Df$ and $Fd$ (EN 12354-1, simplified single-number model,
Formula 26):

$$
R'_w = -10 \log_{10}\Big[ 10^{-R_{Dd,w}/10}
       + \sum 10^{-R_{Ff,w}/10} + \sum 10^{-R_{Df,w}/10}
       + \sum 10^{-R_{Fd,w}/10} \Big].
$$

The direct path is $R_{Dd,w} = R_{s,w} + \Delta R_{Dd,w}$ (Formula 27), the
separating-element laboratory index plus any lining improvement. Each flanking
path (Formula 28a) is

$$
R_{ij,w} = \frac{R_{i,w} + R_{j,w}}{2} + \Delta R_{ij,w} + K_{ij}
         + 10 \log_{10}\frac{S_s}{l_0\ l_f},
$$

with $R_{i,w}$, $R_{j,w}$ the laboratory indices of the two elements meeting at
the junction ($i$ source side, $j$ receiving side), $\Delta R_{ij,w}$ the
combined lining improvement, $S_s$ the separating-element area, $l_f$ the
junction coupling length and $l_0 = 1$ m the reference coupling length. $K_{ij}$
is the junction **vibration reduction index** (Annex E), an empirical function of
the mass ratio $M = \log_{10}(m'_{\perp,i}/m'_i)$ — for a rigid cross-junction
$K_{13} = 8.7 + 17.1 M + 5.7 M^2$ (through) and $K_{12} = 8.7 + 5.7 M^2$
(corner), read at 500 Hz — floored at $K_{ij,\min} = 10 \log_{10}[l_f\ l_0
(1/S_i + 1/S_j)]$ (Formula 29). Two linings combine as $\max(a,b) + \min(a,b)/2$
(Formulas 30/31). The impact counterpart (EN 12354-2, Formula 21) is the direct
subtraction $L'_{n,w} = L_{n,w,eq} - \Delta L_w + K$, with the bare-floor
equivalent level $L_{n,w,eq} = 164 - 35 \log_{10}(m'/m'_0)$ (Annex B), the
covering improvement $\Delta L_w$ (ISO 717-2) and the flanking correction $K$
from Table 1. The EN 12354-1 Annex H.3 ($R'_w = 52$ dB) and EN 12354-2 Annex E.3
($L'_{n,w} = 45$ dB) worked examples are reproduced exactly; the simplified
model is stated to have about a 2 dB standard deviation (Clause 5).

### Measurement uncertainty (ISO 12999-1)

ISO 12999-1 supplies the uncertainty of the quantities above from
inter-laboratory (ISO 5725) reproducibility and repeatability rather than a
GUM functional model. Three **measurement situations** fix the standard
uncertainty $u$: situation **A** (laboratory characterisation) uses the
reproducibility standard deviation $\sigma_R$; situation **B** (same location,
different teams) the in-situ $\sigma_{situ}$; situation **C** (same location,
operator and equipment, repeated) the repeatability $\sigma_r$. The per-band and
single-number values are tabulated for airborne $R$/$R'$/$D_n$/$D_{nT}$
(Tables 2/3), impact $L_n$/$L'_n$ (Table 4 bands, situations B/C only; Table 5
ratings adding a situation-A estimate) and the
covering reduction $\Delta L$ (Tables 6/7, situation A only). The expanded
uncertainty is $U = k\ u$ (Formula 2) with the coverage factor $k$ of Table 8
(at 95 %, $k = 1.96$ two-sided, $k = 1.65$ one-sided; a minimum $k = 1$ is
enforced). A two-sided interval $Y = y \pm U$ reports a value (Formula 3); a
one-sided factor declares conformity, $y - U > $ requirement for a lower limit
(Formula 5) or $y + U <$ requirement for an upper limit (Formula 4).
Uncorrelated components combine in quadrature $u_c = \sqrt{\sum u_i^2}$
(Formula C.2), $m$ independent measurements reduce $u$ to $u/\sqrt{m}$
(Formula A.7), and the uncorrelated single-number uncertainty is the
energy-weighted quadrature sum of the band uncertainties (Formula B.2).

See the [Room and Building Acoustics guide](/phonometry/guides/room-acoustics/) for usage.

## Outdoor propagation and occupational exposure (ISO 9613-1/2, ISO 9612)

### Atmospheric absorption (ISO 9613-1)

Air is a lossy medium: a propagating tone loses energy to shear viscosity and
heat conduction (classical and rotational losses, growing as $f^2$) and to the
**vibrational relaxation** of the oxygen and nitrogen molecules, each an energy
reservoir that resonates near a humidity- and temperature-dependent relaxation
frequency. ISO 9613-1:1993, Eq. (5) gives the pure-tone attenuation coefficient
$\alpha$ in decibels per metre:

$$
\alpha = 8.686\ f^2 \Big[ 1.84\times10^{-11} \big(p_a/p_r\big)^{-1} \big(T/T_0\big)^{1/2}
       + \big(T/T_0\big)^{-5/2} \big( 0.01275\ \tfrac{e^{-2239.1/T}}{f_{rO} + f^2/f_{rO}}
       + 0.1068\ \tfrac{e^{-3352.0/T}}{f_{rN} + f^2/f_{rN}} \big) \Big],
$$

with the oxygen and nitrogen relaxation frequencies $f_{rO}$, $f_{rN}$ of
Eq. (3)/(4), the reference conditions $T_0 = 293.15$ K, $p_r = 101.325$ kPa
(Clause 4.2) and the molar water-vapour concentration $h$ from the relative
humidity (Annex B). At low frequency $\alpha \propto f^2$; near each relaxation
frequency the corresponding term peaks and rolls off, which is why $\alpha$ rises
by two decades from 50 Hz to 10 kHz and why raising the humidity sweeps a peak
across the band. The library reproduces Table 1 to under 0.4 % (the standard's
own printed precision), well inside its stated $\pm 10$ %; passing
`exact_midband=True` snaps each frequency onto the exact midbands
$f_m = 1000 \cdot 10^{k/10}$ (Note 5) used to compute that table. The same
$\alpha$ is the only route to the ISO 354 power attenuation coefficient
$m = \alpha/(10 \lg e)$, exposed as `air_attenuation_m`.

### Outdoor propagation, general method (ISO 9613-2)

ISO 9613-2:1996 predicts the octave-band level at a receiver **downwind** of a
point source (or the equivalent moderate temperature inversion) as
$L_{fT}(DW) = L_W + D_c - A$ (Eq. (3)), where $D_c$ is the directivity correction
and $A$ is the octave-band attenuation, a sum of independent physical mechanisms
(Eq. (4)):

$$
A = A_{div} + A_{atm} + A_{gr} + A_{bar} + A_{misc}.
$$

The library implements the four general terms of Clause 7; the informative
$A_{misc}$ (foliage, industrial sites, housing) and reflections are left to the
caller. **Geometrical divergence** is spherical spreading from a point source,
$A_{div} = 20 \log_{10}(d/d_0) + 11$ dB with $d_0 = 1$ m (Eq. (7)) — exactly
51 dB at 100 m, +6 dB per distance doubling. **Atmospheric absorption** is
$A_{atm} = \alpha\ d$ (Eq. (8)) with $\alpha$ the ISO 9613-1 coefficient above.
**Ground effect** $A_{gr} = A_s + A_r + A_m$ (Eq. (9)) sums a source, receiver and
middle region, each evaluated from the Table 3 functions $a'/b'/c'/d'$ and its
ground factor $G$ (0 hard, 1 porous); a negative $A_{gr}$ denotes a net gain from
the ground reflection. An alternative A-weighted-only form
$A_{gr} = 4.8 - (2 h_m/d)[17 + 300/d] \ge 0$ (Eq. (10)) is offered for porous
ground when only the A-weighted level matters, paired with the solid-angle index
$D_\Omega$ (Eq. (11)). **Screening** by a barrier is the diffraction insertion
loss

$$
D_z = 10 \log_{10}\big[ 3 + (C_2/\lambda)\ C_3\ z\ K_{met} \big] \quad\text{dB},
$$

(Eq. (14)) with $C_2 = 20$ (or 40 when ground reflections are handled by image
sources), $C_3 = 1$ for a single edge or Eq. (15) for a double edge, the
path-length difference $z = d_{ss} + d_{sr} - d$ (Eq. (16)/(17)), wavelength
$\lambda = 340/f$ and the meteorological factor $K_{met}$ (Eq. (18)); $D_z$ is
capped at 20 dB (single) or 25 dB (double). For a top-edge barrier the ground
effect of the screened path is folded into the screening term,
$A_{bar} = D_z - A_{gr} \ge 0$ (Eq. (12), Note 13); for a lateral (vertical-edge)
barrier $A_{bar} = D_z$ and the ground term is kept (Eq. (13)). The long-term
average level subtracts the meteorological correction $C_{met}$ (Eq. (6),
(21)/(22)). The method's stated accuracy is $\pm 1$ to $\pm 3$ dB for broadband
noise up to 1000 m (Table 5).

### Occupational noise exposure and uncertainty (ISO 9612)

ISO 9612:2009 is the engineering method (accuracy grade 2) for a worker's daily
noise exposure level $L_{EX,8h}$, normalised to a nominal 8 h day. Three
**measurement strategies** trade effort for representativeness. The *task-based*
method (Clause 9) splits the day into tasks, energy-averages $I \ge 3$ samples
per task (Eq. 7) and sums the task contributions
$L_{EX,8h,m} = L_{p,A,eqT,m} + 10 \log_{10}(T_m/T_0)$ energetically (Eq. 9/10).
The *job-based* method (Clause 10) energy-averages $N \ge 5$ random samples over a
homogeneous exposure group (Eq. 11) and normalises the effective-day duration
(Eq. 12); the *full-day* method (Clause 11) does the same arithmetic on whole-day
measurements (Eq. 13).

The **Annex C** uncertainty budget is normative. The combined standard
uncertainty is $u^2 = \sum c_i^2 u_i^2$ (C.1) and the expanded uncertainty is
$U = k\ u$ with $k = 1.65$ for a **one-sided** 95 % interval (Clause 14), so the
reported upper limit is $L_{EX,8h} + U$. The task and job methods differ in an
instructive way: the task noise-sampling uncertainty $u_{1a}$ divides the summed
squared deviations by $I(I-1)$ — the standard error of the mean (Eq. C.6) —
whereas the job/full-day sampling uncertainty $u_1$ is the plain sample standard
deviation with denominator $N-1$ (Eq. C.12), so the same spread contributes more
in the job method (fewer, coarser samples). The task budget (Eq. C.3) adds the
sensitivity coefficients $c_{1a}$ (Eq. C.4) and $c_{1b}$ (Eq. C.5) and an optional
task-duration uncertainty $u_{1b}$ (Eq. C.7); the job/full-day budget (Eq. C.9)
reads $c_1 u_1$ from Table C.4 as a function of $(N, u_1)$ and adds the instrument
uncertainty $u_2$ (Table C.5) and microphone-position uncertainty $u_3 = 1.0$ dB
in quadrature. Peak levels $L_{p,Cpeak}$ are reported without an uncertainty:
Annex C provides no method for them (Table C.5, Note 1). The three worked
examples of Annexes D (task, $L_{EX,8h} = 84.3$ dB, $U = 2.7$ dB), E (job,
$88.1$ dB, $3.8$ dB) and F (full-day, $90.1$ dB, $3.4$ dB) are reproduced to
the standard's printed precision — every intermediate of Annex E is digit-exact,
and its final level differs only by the standard's own pre-rounding of the
effective-day level (see the [Levels guide](/phonometry/guides/levels/)).

See the [Outdoor Propagation guide](/phonometry/guides/outdoor-propagation/) and the
[Levels guide](/phonometry/guides/levels/) for usage.

## Sound power determination (ISO 3744/3746, ISO 3741, ISO 9614-2)

The sound power level $L_W = 10 \log_{10}(P/P_0)$ ($P_0 = 1$ pW) is an
*emission* quantity: unlike a pressure level it does not depend on the receiver
distance or the room. Three families of methods recover it.

### Enveloping-surface pressure (ISO 3744/3746)

Over a reflecting plane the free-field relation is simply
$L_W = \bar{L}_p + 10 \log_{10}(S/S_0)$: the mean-square pressure averaged over
an enveloping surface of area $S$, multiplied by $S$, is the radiated power.
Two corrections restore that idealisation. Uncorrelated **background noise**
adds its mean square to the source's, so with the margin
$\Delta L_p = L_{ST} - L_{bg}$ the source-only level is recovered by subtracting
$K_1 = -10 \log_{10}(1 - 10^{-\Delta L_p/10})$ (from $p_{src}^2 = p_{ST}^2 (1 - 10^{-\Delta L_p/10})$).
The **reverberant field** of a non-anechoic room adds a near-uniform energy
density $4P/(A c)$ to the direct $P/(S c)$, so the surface level exceeds the
free-field value by their ratio, $K_2 = 10 \log_{10}(1 + 4 S/A)$, with $A$ the
room's equivalent absorption area. The surface area is the closed form of the
geometry: a hemisphere $S = 2 \pi r^2$ over one reflecting plane (halved and
quartered for two and three planes), a one-plane box $S = 4(ab + bc + ca)$ with
$a = 0.5\ l_1 + d$, $b = 0.5\ l_2 + d$, $c = l_3 + d$. ISO 3746 (survey) shares
the maths with looser criteria. The expanded uncertainty is
$U = 2 \sqrt{\sigma_{R0}^2 + \sigma_{omc}^2}$.

### Reverberation room (ISO 3741)

In a qualified diffuse field the steady energy density $w = 4P/(A c)$ ties the
power to the room absorption, giving $L_W = \bar{L}_p + 10 \log_{10}(A/A_0) - 6$
plus higher-order corrections, with $A = (55.26/c)(V/T_{60})$ and
$c = 20.05 \sqrt{273 + \theta}$. The **Waterhouse correction**
$10 \log_{10}(1 + S c/(8 V f))$ compensates the extra energy stored in the
boundary layer that interior microphones miss ($S c/(8 V f) = S \lambda/(8 V)$,
so it fades as frequency rises); the $4.34\ A/S$ term is the mean-free-path air
correction, and $C_1$, $C_2$ carry the result to the reference meteorological
conditions (23 °C, 101.325 kPa). The **comparison method** subtracts a
reference source of known power measured in the same room,
$L_W = L_{W(\text{RSS})} + (\bar{L}_p - \bar{L}_{p,\text{RSS}} + C_2)$, so the
absorption-area, Waterhouse and $C_1$ terms cancel and the room need not be
characterised.

### Intensity scanning (ISO 9614-2)

Sound intensity is the net energy flux $\vec{I} = \overline{p\ \vec{u}}$, so by
the divergence theorem the power through a closed surface is
$P = \sum_i \langle I_{n,i} \rangle\ S_i$. A steady source *outside* the surface
contributes zero net flux (its energy enters and leaves), which is why
intensity rejects stationary background noise — but it can still drive a band's
$P$ negative, in which case that band is not determinable. Two normative field
indicators gate validity: the surface pressure-intensity indicator
$F_{pI} = [L_p] - L_W + 10 \log_{10}(S/S_0)$ (reactivity) and the
negative-partial-power indicator
$F_{+/-} = 10 \log_{10}(\sum_i \lvert P_i \rvert / \lvert \sum_i P_i \rvert)$
(recirculation), together with the probe's dynamic capability
$L_d = \delta_{pI0} - K$ ($K = 10$ dB grade 2, 7 dB grade 3), which must exceed
$F_{pI}$. A band earns the engineering grade when $L_d > F_{pI}$, $F_{+/-} \le 3$ dB
and the two repeated sweeps agree within the Table 2 limit.

See the [Sound Power guide](/phonometry/guides/sound-power/) for usage.
