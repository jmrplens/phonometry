---
title: "metrology.core"
description: "Public API of phonometry.metrology.core (auto-generated)."
sidebar:
  label: "core"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Core processing logic and FilterBank class for phonometry.

## FilterBankWarning

Warns about fractional-octave filter-bank processing pitfalls.

## OctaveFilterBank

```python
OctaveFilterBank(
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    filter_type: str = 'butter',
    ripple: float = 0.1,
    attenuation: float = 72.0,
    show: bool = False,
    plot_file: str | None = None,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    stateful: bool = False,
    steady_ic: bool = False,
    resample: bool = True,
)
```

A class-based representation of an Octave Filter Bank.
Allows for pre-calculating and reusing filter coefficients.

Initialize the Octave Filter Bank.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sample rate in Hz. |
| `fraction` | Bandwidth fraction (e.g., 1 for octave, 3 for 1/3 octave). |
| `order` | Filter order. |
| `limits` | Frequency limits [f_min, f_max]. |
| `filter_type` | Type of filter ('butter', 'cheby1', 'cheby2', 'ellip', 'bessel'). Only `butter` meets IEC 61260-1:2014 class 1 with the default parameters (`cheby2` also does once `attenuation` >= 70 dB, see below); `cheby1`/`ellip`/`bessel` fail on passband ripple or roll-off regardless of parameters. |
| `ripple` | Passband ripple in dB. |
| `attenuation` | Stopband attenuation in dB. Default 72.0. For the `cheby2` filter scipy pins the equiripple deep-stopband floor at exactly this value, so it must be >= 70 dB for the bank to meet the IEC 61260-1:2014 class 1 deep-stopband limit (Omega >= G^4). The 72 dB default clears class 1 with the same +0.400 dB passband margin as `butter`. |
| `show` | If True, show the filter response plot. |
| `plot_file` | Path to save the filter response plot. |
| `calibration_factor` | Calibration factor for SPL calculation. |
| `dbfs` | If True, calculate SPL in dBFS. |
| `stateful` | If True, carry filter state between calls. Useful for block processing. |
| `steady_ic` | If True, calculate steady state initial conditions for filter. |
| `resample` | If True, resampling is performed. |

### OctaveFilterBank.filter()

```python
OctaveFilterBank.filter(
    x: List[float] | np.ndarray,
    sigbands: bool = False,
    mode: str = 'rms',
    detrend: bool = True,
    calculate_level: bool = True,
    nominal: bool = False,
    zero_phase: bool = False,
) -> Tuple[np.ndarray | None, List[float] | List[str]] | Tuple[np.ndarray | None, List[float] | List[str], List[np.ndarray]]
```

Apply the pre-designed filter bank to a signal.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | Input signal (1D array or 2D array [channels, samples]). |
| `sigbands` | If True, also return the signal in the time domain divided into bands. |
| `mode` | 'rms' for energy-based level, 'peak' for peak-holding level. Note: 'peak' includes the filter's onset transient; a tone that starts abruptly can overshoot by ~1 dB. For steady signals, discard the first ~5/f_low seconds or use longer signals. |
| `detrend` | If True, remove DC offset from signal before filtering (Default: True). |
| `calculate_level` | If True, calculate SPL. |
| `nominal` | If True, return IEC 61260-1 nominal frequency labels (List[str]) instead of exact floats. |
| `zero_phase` | If True, filter with `sosfiltfilt` (forward-backward): no group delay, but the effective stopband attenuation doubles and the effective passband narrows. The narrowing lowers the measured broadband band level by about 0.2 to 0.3 dB per band relative to forward filtering (a pure in-band tone is unaffected, since it sits where both passes are ~0 dB). Prefer forward filtering when the absolute band SPL must match single-pass conventions; use zero-phase when preserving the temporal envelope matters (e.g. reverberation decay, ISO 3382-2 Clause 7.3). Offline analysis only; incompatible with stateful mode. |

**Returns:** A tuple containing (SPL_array, Frequencies_list) or (SPL_array, Frequencies_list, signals).

### OctaveFilterBank.spectrogram()

```python
OctaveFilterBank.spectrogram(
    x: List[float] | np.ndarray,
    window_time: float = 0.125,
    overlap: float = 0.5,
    mode: str = 'rms',
    detrend: bool = True,
    zero_phase: bool = False,
) -> Tuple[np.ndarray, List[float], np.ndarray]
```

Short-time fractional-octave analysis: level per band over time.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | Input signal (1D array or 2D array [channels, samples]). |
| `window_time` | Analysis window length in seconds. |
| `overlap` | Window overlap fraction in [0, 1). |
| `mode` | 'rms' or 'peak' (per window). |
| `detrend` | If True, remove DC offset before filtering. |
| `zero_phase` | If True, filter bands forward-backward so their group delays don't skew the frames (offline analysis only). |

**Returns:** Tuple (levels, freq, times). `levels` has shape (num_bands, num_frames) for 1D input and (channels, num_bands, num_frames) for 2D input; `times` holds each window's center in seconds.
