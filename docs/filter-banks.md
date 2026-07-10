← [Documentation index](README.md)

# Filter Banks

phonometry supports several filter types, each with its own transfer function
characteristic. All banks place their **−3 dB points on the ANSI S1.11 band
edges**, so band levels are comparable across architectures.

## 1. Fractional octave bands: the math

IEC 61260-1:2014 builds every band from the base-10 octave ratio
$G = 10^{3/10} \approx 1.99526$ (so "one octave" is *not* exactly 2). For
band fraction $1/b$, the mid frequencies and band edges follow (5.2-5.5):

$$
f_m = 1000 \cdot G^{x/b} \quad (b\ \text{odd}), \qquad
f_1 = f_m G^{-1/2b}, \quad f_2 = f_m G^{+1/2b}
$$

so every 1/3-octave band spans $G^{1/3} \approx 1.2589 \approx 10^{1/10}$ —
ten bands per decade, which is why the nominal frequencies (25, 31.5, 40 …)
repeat scaled by 10. phonometry designs each band as an SOS cascade whose
−3 dB points land exactly on $f_1$ and $f_2$ for every architecture — for
Chebyshev II, Elliptic and Bessel that requires pre-warping the analytic
band-edge mapping rather than trusting SciPy's default parametrization.

### Multirate decimation

A 25 Hz one-third-octave band at 48 kHz spans about 5.8 Hz — 0.024 %
of Nyquist — coefficients so stiff they go numerically unstable. The bank
avoids that by filtering low bands at a decimated rate:

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_multirate_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/diagram_multirate.svg" alt="Multirate decimation: high bands filtered at the input rate, low bands after anti-alias low-pass and decimation so the SOS sections stay numerically healthy" width="92%"></picture>

## 2. Filter Comparison and Zoom

We use Second-Order Sections (SOS) for all filters to ensure numerical stability.
The following plot compares the architectures focusing on the -3 dB crossover point.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_type_comparison_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_type_comparison.svg" alt="Magnitude response comparison of the five filter architectures for the 1 kHz octave band, with a zoom at the -3 dB crossover" width="80%"></picture>

| Type | Name | Usage Example | Best For |
| :--- | :--- | :--- | :--- |
| `butter` | **Butterworth** | `octave_filter(x, fs, filter_type='butter')` | General acoustic measurement. |
| `cheby1` | **Chebyshev I** | `octave_filter(x, fs, filter_type='cheby1', ripple=0.1)` | Sharper roll-off at the cost of ripple. |
| `cheby2` | **Chebyshev II** | `octave_filter(x, fs, filter_type='cheby2')` | Flat passband with stopband zeros. |
| `ellip` | **Elliptic** | `octave_filter(x, fs, filter_type='ellip', ripple=0.1)` | Maximum selectivity. |
| `bessel` | **Bessel** | `octave_filter(x, fs, filter_type='bessel')` | Preserving transient waveform shapes. |

## 3. `octave_filter()` / `OctaveFilterBank` parameters

| Parameter | Type | Units | Range / default | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `x` | 1D or 2D array | digital units | non-empty | 2D is `[channels, samples]` |
| `fs` | int | Hz | > 0 | |
| `fraction` | int | — | default `1`; common `3`; any `b ≥ 1` | Bands per octave = `b` |
| `order` | int | — | default `6` | SOS order per band |
| `limits` | list `[lo, hi]` | Hz | default `[12, 20000]` | Analysis range |
| `filter_type` | str | — | `'butter'` (default), `'cheby1'`, `'cheby2'`, `'ellip'`, `'bessel'` | See comparison above |
| `ripple` / `attenuation` | float | dB | `ripple` default `0.1`; `attenuation` default `72.0` | Passband ripple / stopband attenuation (cheby/ellip); `cheby2` needs `attenuation ≥ 70` for class 1, since scipy pins its equiripple floor at exactly this value |
| `show` | bool | — | default `False` | Plot the bank response (needs matplotlib) |
| `sigbands` | bool | — | default `False` | Also return the per-band time signals |
| `mode` | str | — | `'rms'` (default), `'peak'`, `'sum'` | Per-band statistic returned |
| `nominal` | bool | — | default `False` | Return nominal band labels (e.g. `1000`) instead of exact centre frequencies |
| `detrend` | bool | — | default `True` | Remove each band's DC offset before the level (improves low-frequency accuracy) |
| `calibration_factor` | float | — | default `1.0` | Scales the input to pascals (see the Calibration guide) |
| `dbfs` | bool | — | default `False` | Reference levels to digital full scale instead of 20 µPa |
| `plot_file` | str or `None` | — | default `None` | Save the bank-response plot to this path |
| `zero_phase` | bool | — | default `False` | Forward-backward filtering (offline) |
| `stateful` / `steady_ic` (class) | bool | — | default `False` | Streaming state; see [Block Processing](block-processing.md) |

`verify_filter_class(bank)` checks the designed bank against the IEC 61260-1
Table 1 acceptance limits and reports the class (`1`, `2` or `None` if outside both) with per-band
margins.

## 4. Gallery of Filter Bank Responses

Full spectral view of the filter banks for Octave (1/1) and 1/3-Octave fractions.

| Architecture | 1/1 Octave (Fraction=1) | 1/3 Octave (Fraction=3) |
| :--- | :--- | :--- |
| **Butterworth** | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_1_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_1_order_6.svg" alt="Butterworth octave-band filter bank frequency response" width="100%"></picture> | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6.svg" alt="Butterworth one-third-octave filter bank frequency response" width="100%"></picture> |
| **Chebyshev I** | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_1_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_1_order_6.svg" alt="Chebyshev I octave-band filter bank frequency response" width="100%"></picture> | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6.svg" alt="Chebyshev I one-third-octave filter bank frequency response" width="100%"></picture> |
| **Chebyshev II** | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_1_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_1_order_6.svg" alt="Chebyshev II octave-band filter bank frequency response" width="100%"></picture> | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6.svg" alt="Chebyshev II one-third-octave filter bank frequency response" width="100%"></picture> |
| **Elliptic** | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_1_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_1_order_6.svg" alt="Elliptic octave-band filter bank frequency response" width="100%"></picture> | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6.svg" alt="Elliptic one-third-octave filter bank frequency response" width="100%"></picture> |
| **Bessel** | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_1_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_1_order_6.svg" alt="Bessel octave-band filter bank frequency response" width="100%"></picture> | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6.svg" alt="Bessel one-third-octave filter bank frequency response" width="100%"></picture> |

## 5. Filter Usage and Examples

### 1. Butterworth (`butter`)

The Butterworth filter is known for its **maximally flat passband**. It is the
standard choice for acoustic measurements where no ripple is allowed within the
frequency bands.

```python
import numpy as np
from phonometry import octave_filter

# A calibrated signal in Pa so the guide runs standalone
fs = 48000
x = 0.2 * np.sin(2 * np.pi * 1000 * np.arange(fs) / fs)

# Default standard measurement
spl, freq = octave_filter(x, fs, filter_type='butter')
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_butter_fraction_3_order_6.svg" alt="Butterworth one-third-octave filter bank frequency response" width="60%"></picture>

### 2. Chebyshev I (`cheby1`)

Chebyshev Type I filters provide a **steeper roll-off** than Butterworth at the
expense of ripples in the passband. Useful when high selectivity is needed near
the cut-off frequencies.

```python
# Uses `x` and `fs` from the snippet above.
# Selectivity with 0.1 dB passband ripple
spl, freq = octave_filter(x, fs, filter_type='cheby1', ripple=0.1)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby1_fraction_3_order_6.svg" alt="Chebyshev I one-third-octave filter bank frequency response" width="60%"></picture>

### 3. Chebyshev II (`cheby2`)

Also known as Inverse Chebyshev, it has a **flat passband** and ripples in the
stopband. It provides faster roll-off than Butterworth without affecting the
signal in the passband. The stopband edges are placed automatically so that the
−3 dB points land on the band edges (`attenuation` must be > 3.01 dB).

```python
# Uses `x` and `fs` from the snippet above.
# Flat passband, class-1 default 72 dB stopband attenuation
spl, freq = octave_filter(x, fs, filter_type='cheby2')
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_cheby2_fraction_3_order_6.svg" alt="Chebyshev II one-third-octave filter bank frequency response" width="60%"></picture>

### 4. Elliptic (`ellip`)

Elliptic (Cauer) filters have the **shortest transition width** (steepest
roll-off) for a given order. They feature ripples in both the passband and stopband.

```python
# Uses `x` and `fs` from the snippet above.
# Maximum selectivity for extreme band isolation
spl, freq = octave_filter(x, fs, filter_type='ellip', ripple=0.1)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_ellip_fraction_3_order_6.svg" alt="Elliptic one-third-octave filter bank frequency response" width="60%"></picture>

### 5. Bessel (`bessel`)

Bessel filters are optimized for **linear phase response** and minimal group
delay. They preserve the shape of filtered waveforms (transients) better than
any other type, but have the slowest roll-off.

```python
# Uses `x` and `fs` from the snippet above.
# Best for pulse analysis and transient preservation
spl, freq = octave_filter(x, fs, filter_type='bessel')
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_bessel_fraction_3_order_6.svg" alt="Bessel one-third-octave filter bank frequency response" width="60%"></picture>

### 6. Linkwitz-Riley (`linkwitz_riley`)

Specifically designed for **audio crossovers**. Linkwitz-Riley filters (typically
4th order, but any even order is supported) allow splitting a signal into bands
that, when summed, result in a perfectly flat magnitude response and zero phase
difference between bands at the crossover.

```python
from phonometry import linkwitz_riley

# Uses `x` and `fs` from the snippet above.
signal = x
# Split signal into Low and High bands at 1000 Hz
low, high = linkwitz_riley(signal, fs, freq=1000, order=4)
# Reconstruction: low + high == signal (flat response)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/crossover_lr4_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/crossover_lr4.svg" alt="Linkwitz-Riley 4th-order crossover: low-pass, high-pass and their flat sum" width="60%"></picture>

## 6. Verifying the IEC 61260-1 class

`verify_filter_class` checks every band of a bank against the acceptance
limits of **IEC 61260-1:2014** (Table 1, with the fractional-octave breakpoint
mapping and log-frequency interpolation from the standard) and reports the
performance class per band with its margin in dB:

```python
from phonometry import OctaveFilterBank, verify_filter_class

bank = OctaveFilterBank(fs=48000, fraction=3, order=6)
result = verify_filter_class(bank)
print(result["overall_class"])          # 1
print(result["bands"][0])
# {'freq': 12.589254117941678, 'class': 1, 'margin_class1_db': 0.39999999999997266, 'margin_class2_db': 0.5999999999999727}
```

The Table 1 acceptance mask itself is public too: `class_limits(fraction,
filter_class, omega)` returns the minimum/maximum relative-attenuation
limits at normalized frequencies Ω = f/fm — the same limits the verifier
and the figure below use.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/class_mask_overlay_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/class_mask_overlay.svg" alt="Butterworth band response threading between the forbidden regions of the IEC 61260-1 class 1 acceptance mask" width="80%"></picture>

*The order-6 Butterworth response (blue) threads between the forbidden
regions: it must attenuate at least the red mask outside the band and no more
than the purple mask inside it.*

With default parameters (order 6), **Butterworth meets class 1**, and so does
**Chebyshev II**: its `attenuation` default is now `72` dB, clearing the 70 dB
far-stopband class 1 limit (scipy pins the cheby2 equiripple floor at exactly
`attenuation`, so any value ≥ 70 dB qualifies; the 72 dB default keeps the same
+0.400 dB passband margin as Butterworth). Chebyshev I, Elliptic and Bessel do
not meet class limits at order 6: passband ripple (cheby1/ellip) and slow
roll-off (bessel) violate the mask.

### Class 0 (IEC 61260:1995 / ANSI S1.11-2004)

The tightest performance class, **class 0**, was defined by the earlier
**IEC 61260:1995** and its US twin **ANSI S1.11-2004** (both withdrawn/superseded
but still referenced for laboratory-grade instruments); IEC 61260-1:2014 dropped
it. Its class 1/2 masks differ slightly from the 2014 edition, so it lives behind
an `edition` switch rather than being mixed into the 2014 mask:

```python
result = verify_filter_class(bank, edition="1995")   # classes 0, 1, 2
print(result["overall_class"])          # 0  (the default Butterworth clears it)
print(result["bands"][0]["margin_class0_db"])
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_class0_mask_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/filter_class0_mask.svg" alt="Nested pass-band acceptance corridors for class 0, 1 and 2 of IEC 61260:1995 with the order-6 Butterworth response sitting inside the tightest class 0 corridor" width="80%"></picture>

*The class 0 corridor (±0.15 dB at mid-band) is the tightest; class 1 (±0.3 dB)
and class 2 (±0.5 dB) are progressively wider. The order-6 Butterworth threads
inside class 0 across the whole pass-band.*

**Which architecture reaches which class?** The library's **default — Butterworth
order 6 — meets class 0** in the configurations the conformance suite verifies
(octave and third-octave banks at 48 kHz), so no special setup is needed for
laboratory-grade banks in that range. The table below reports the best class
each architecture reaches under that same order-6 / 48 kHz setup; the other
architectures fall short of class 0 because they trade the IEC mask for a
different property *by construction*:

| Architecture | Best class (order 6, fs 48 kHz) | Why |
| :--- | :---: | :--- |
| `butter` (default) | **0** | Maximally-flat pass-band, monotone roll-off — fits the mask |
| `cheby2` | 1 | Flat pass-band but the mask relationship binds at class 1 |
| `cheby1` | — | Pass-band ripple violates the flatness limit |
| `ellip` | — | Pass- and stop-band ripple |
| `bessel` | — | Flat group delay bought with a slow roll-off |

So the sensible default is the common one (Butterworth order 6): it clears
class 0 in the verified configurations, while the alternative architectures are
deliberate opt-ins whose purpose (steeper roll-off, linear phase) works against
the class mask. Away from these settings — very high `fraction` or near-Nyquist
bands — always re-run `verify_filter_class` to confirm the class you need, and
raise the order if a band needs more margin.

## 7. Signal Decomposition and Stability

By setting `sigbands=True`, you can retrieve the time-domain components of each
band. This allows for advanced analysis or comparing how different architectures
(e.g., Butterworth vs Chebyshev) affect the signal phase and transient response.

```python
import numpy as np
from phonometry import octave_filter

# 1. Generate a signal (Sum of 250Hz and 1000Hz)
fs = 48000
t = np.linspace(0, 0.5, int(fs * 0.5), endpoint=False)
y = np.sin(2 * np.pi * 250 * t) + np.sin(2 * np.pi * 1000 * t)

# 2. Compare architectures (Butterworth vs Chebyshev II)
spl_b, freq, xb_butter = octave_filter(y, fs=fs, fraction=1, sigbands=True, filter_type='butter')
spl_c2, _, xb_cheby2 = octave_filter(y, fs=fs, fraction=1, sigbands=True, filter_type='cheby2')

# 'xb_butter' and 'xb_cheby2' contain the time-domain signals per band
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_decomposition_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/signal_decomposition.svg" alt="Time-domain band decomposition comparing Butterworth and Chebyshev II, including the impulse response" width="80%"></picture>

*The plot compares the **Butterworth** (solid blue) and **Chebyshev II** (dashed
red) responses. The bottom plot shows the **Impulse Response**, highlighting the
differences in stability and transient decay.*

> [!NOTE]
> **Why do the signals look shifted in time?**
> Digital IIR filters (like Butterworth or Chebyshev) have **non-linear phase
> responses**, which results in frequency-dependent **Group Delay**. In the 250 Hz
> band, you can see that the Chebyshev II filter has a different propagation delay
> compared to the Butterworth filter. This is a normal physical property of these
> architectures: more aggressive frequency roll-offs usually come at the cost of
> higher group delay and phase distortion.

### Group delay, quantified

The group delay $\tau_g(\omega) = -\frac{d\phi(\omega)}{d\omega}$ of the
1 kHz octave band shows the trade-off directly: Bessel stays nearly flat across
the passband (transient shapes survive), while Chebyshev I and Elliptic pay for
their steep roll-off with strong delay peaks at the band edges.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/group_delay_comparison_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/group_delay_comparison.svg" alt="Group delay of the 1 kHz octave band for the five architectures: Bessel nearly flat, Chebyshev and Elliptic peaking at the band edges" width="80%"></picture>

## 8. Zero-phase filtering

For offline analysis you can eliminate group delay entirely: `zero_phase=True`
filters each band forward-backward (`scipy.signal.sosfiltfilt`), keeping band
signals time-aligned with the input. The effective attenuation doubles and the
effective passband narrows, lowering the measured broadband band level by
~0.2 to 0.3 dB per band (a pure in-band tone is unaffected); prefer forward
filtering when the absolute band SPL must match single-pass conventions, and
reserve zero-phase for when the temporal envelope matters (e.g. reverberation
decay). The option is incompatible with stateful (block) processing.

```python
from phonometry import OctaveFilterBank

# Uses `y` from the snippet above.
bank = OctaveFilterBank(fs=48000, fraction=3)
spl, freq, xb = bank.filter(y, sigbands=True, zero_phase=True)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/zero_phase_comparison_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/zero_phase_comparison.svg" alt="Causal versus zero-phase filtering of a tone burst: the zero-phase output stays time-aligned with the input" width="80%"></picture>

*Causal filtering delays the burst by the filter's group delay; zero-phase
filtering keeps it aligned with the input.*

---

**Standards.** IEC 61260-1:2014, *Electroacoustics — Octave-band and
fractional-octave-band filters — Part 1: Specifications* — the base-10 mid
frequencies and band edges of §1 (5.2-5.5), the nominal band labels, and the
Table 1 class 1 / class 2 acceptance limits (with the fractional-octave
breakpoint mapping and log-frequency interpolation) verified in §6.
IEC 61260:1995 and ANSI S1.11-2004, *Octave-Band and Fractional-Octave-Band …
Filters* — the withdrawn edition's Table 1 (identical between the two) supplies
the stricter class 0 mask offered by ``edition="1995"``, and the band-edge
convention on which every bank places its −3 dB
points. ISO 266 — the preferred-frequency series behind the nominal band
labels reported by `nominal_frequencies`.
