← [Documentation index](README.md)

# Filter Banks

PyOctaveBand supports several filter types, each with its own transfer function
characteristic. All banks place their **−3 dB points on the ANSI S1.11 band
edges**, so band levels are comparable across architectures.

## Filter Comparison and Zoom

We use Second-Order Sections (SOS) for all filters to ensure numerical stability.
The following plot compares the architectures focusing on the -3 dB crossover point.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_type_comparison_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_type_comparison.png" width="80%"></picture>

| Type | Name | Usage Example | Best For |
| :--- | :--- | :--- | :--- |
| `butter` | **Butterworth** | `octavefilter(x, fs, filter_type='butter')` | General acoustic measurement. |
| `cheby1` | **Chebyshev I** | `octavefilter(x, fs, filter_type='cheby1', ripple=0.1)` | Sharper roll-off at the cost of ripple. |
| `cheby2` | **Chebyshev II** | `octavefilter(x, fs, filter_type='cheby2', attenuation=60)` | Flat passband with stopband zeros. |
| `ellip` | **Elliptic** | `octavefilter(x, fs, filter_type='ellip', ripple=0.1, attenuation=60)` | Maximum selectivity. |
| `bessel` | **Bessel** | `octavefilter(x, fs, filter_type='bessel')` | Preserving transient waveform shapes. |

## Gallery of Filter Bank Responses

Full spectral view of the filter banks for Octave (1/1) and 1/3-Octave fractions.

| Architecture | 1/1 Octave (Fraction=1) | 1/3 Octave (Fraction=3) |
| :--- | :--- | :--- |
| **Butterworth** | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_butter_fraction_1_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_butter_fraction_1_order_6.png" width="100%"></picture> | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_butter_fraction_3_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_butter_fraction_3_order_6.png" width="100%"></picture> |
| **Chebyshev I** | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby1_fraction_1_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby1_fraction_1_order_6.png" width="100%"></picture> | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby1_fraction_3_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby1_fraction_3_order_6.png" width="100%"></picture> |
| **Chebyshev II** | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby2_fraction_1_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby2_fraction_1_order_6.png" width="100%"></picture> | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby2_fraction_3_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby2_fraction_3_order_6.png" width="100%"></picture> |
| **Elliptic** | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_ellip_fraction_1_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_ellip_fraction_1_order_6.png" width="100%"></picture> | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_ellip_fraction_3_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_ellip_fraction_3_order_6.png" width="100%"></picture> |
| **Bessel** | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_bessel_fraction_1_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_bessel_fraction_1_order_6.png" width="100%"></picture> | <picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_bessel_fraction_3_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_bessel_fraction_3_order_6.png" width="100%"></picture> |

## Filter Usage and Examples

### 1. Butterworth (`butter`)

The Butterworth filter is known for its **maximally flat passband**. It is the
standard choice for acoustic measurements where no ripple is allowed within the
frequency bands.

```python
from pyoctaveband import octavefilter
# Default standard measurement
spl, freq = octavefilter(x, fs, filter_type='butter')
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_butter_fraction_3_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_butter_fraction_3_order_6.png" width="60%"></picture>

### 2. Chebyshev I (`cheby1`)

Chebyshev Type I filters provide a **steeper roll-off** than Butterworth at the
expense of ripples in the passband. Useful when high selectivity is needed near
the cut-off frequencies.

```python
# Selectivity with 0.1 dB passband ripple
spl, freq = octavefilter(x, fs, filter_type='cheby1', ripple=0.1)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby1_fraction_3_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby1_fraction_3_order_6.png" width="60%"></picture>

### 3. Chebyshev II (`cheby2`)

Also known as Inverse Chebyshev, it has a **flat passband** and ripples in the
stopband. It provides faster roll-off than Butterworth without affecting the
signal in the passband. The stopband edges are placed automatically so that the
−3 dB points land on the band edges (`attenuation` must be > 3.01 dB).

```python
# Flat passband with 60 dB stopband attenuation
spl, freq = octavefilter(x, fs, filter_type='cheby2', attenuation=60)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby2_fraction_3_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_cheby2_fraction_3_order_6.png" width="60%"></picture>

### 4. Elliptic (`ellip`)

Elliptic (Cauer) filters have the **shortest transition width** (steepest
roll-off) for a given order. They feature ripples in both the passband and stopband.

```python
# Maximum selectivity for extreme band isolation
spl, freq = octavefilter(x, fs, filter_type='ellip', ripple=0.1, attenuation=60)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_ellip_fraction_3_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_ellip_fraction_3_order_6.png" width="60%"></picture>

### 5. Bessel (`bessel`)

Bessel filters are optimized for **linear phase response** and minimal group
delay. They preserve the shape of filtered waveforms (transients) better than
any other type, but have the slowest roll-off.

```python
# Best for pulse analysis and transient preservation
spl, freq = octavefilter(x, fs, filter_type='bessel')
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_bessel_fraction_3_order_6_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/filter_bessel_fraction_3_order_6.png" width="60%"></picture>

### 6. Linkwitz-Riley (`linkwitz_riley`)

Specifically designed for **audio crossovers**. Linkwitz-Riley filters (typically
4th order, but any even order is supported) allow splitting a signal into bands
that, when summed, result in a perfectly flat magnitude response and zero phase
difference between bands at the crossover.

```python
from pyoctaveband import linkwitz_riley
# Split signal into Low and High bands at 1000 Hz
low, high = linkwitz_riley(signal, fs, freq=1000, order=4)
# Reconstruction: low + high == signal (flat response)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/crossover_lr4_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/crossover_lr4.png" width="60%"></picture>

## Verifying the IEC 61260-1 class

`verify_filter_class` checks every band of a bank against the acceptance
limits of **IEC 61260-1:2014** (Table 1, with the fractional-octave breakpoint
mapping and log-frequency interpolation from the standard) and reports the
performance class per band with its margin in dB:

```python
from pyoctaveband import OctaveFilterBank, verify_filter_class

bank = OctaveFilterBank(fs=48000, fraction=3, order=6)
result = verify_filter_class(bank)
print(result["overall_class"])          # 1, 2 or None
print(result["bands"][0])               # {'freq': ..., 'class': 1, 'margin_class1_db': ...}
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/class_mask_overlay_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/class_mask_overlay.png" width="80%"></picture>

*The order-6 Butterworth response (blue) threads between the forbidden
regions: it must attenuate at least the red mask outside the band and no more
than the purple mask inside it.*

With default parameters (order 6), **Butterworth meets class 1**. Chebyshev II
lands in class 2 — capped exactly by its `attenuation=60` versus the 70 dB
far-stopband requirement (raise `attenuation` to reach class 1). Chebyshev I,
Elliptic and Bessel do not meet class limits at order 6: passband ripple
(cheby1/ellip) and slow roll-off (bessel) violate the mask.

## Signal Decomposition and Stability

By setting `sigbands=True`, you can retrieve the time-domain components of each
band. This allows for advanced analysis or comparing how different architectures
(e.g., Butterworth vs Chebyshev) affect the signal phase and transient response.

```python
import numpy as np
from pyoctaveband import octavefilter

# 1. Generate a signal (Sum of 250Hz and 1000Hz)
fs = 48000
t = np.linspace(0, 0.5, int(fs * 0.5), endpoint=False)
y = np.sin(2 * np.pi * 250 * t) + np.sin(2 * np.pi * 1000 * t)

# 2. Compare architectures (Butterworth vs Chebyshev II)
spl_b, freq, xb_butter = octavefilter(y, fs=fs, fraction=1, sigbands=True, filter_type='butter')
spl_c2, _, xb_cheby2 = octavefilter(y, fs=fs, fraction=1, sigbands=True, filter_type='cheby2')

# 'xb_butter' and 'xb_cheby2' contain the time-domain signals per band
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/signal_decomposition_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/signal_decomposition.png" width="80%"></picture>

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

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/group_delay_comparison_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/group_delay_comparison.png" width="80%"></picture>

## Zero-phase filtering

For offline analysis you can eliminate group delay entirely: `zero_phase=True`
filters each band forward-backward (`scipy.signal.sosfiltfilt`), keeping band
signals time-aligned with the input. The effective attenuation doubles, and the
option is incompatible with stateful (block) processing.

```python
from pyoctaveband import OctaveFilterBank

bank = OctaveFilterBank(fs=48000, fraction=3)
spl, freq, xb = bank.filter(y, sigbands=True, zero_phase=True)
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/zero_phase_comparison_dark.png"><img src="https://raw.githubusercontent.com/jmrplens/PyOctaveBand/main/.github/images/zero_phase_comparison.png" width="80%"></picture>

*Causal filtering delays the burst by the filter's group delay; zero-phase
filtering keeps it aligned with the input.*
