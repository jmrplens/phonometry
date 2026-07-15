---
title: "phonometry"
description: "Top-level convenience API of the phonometry package (auto-generated)."
sidebar:
  label: "phonometry"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Convenience wrappers defined at the package top level (`phonometry/__init__.py`). Every public name in the library can be imported directly from `phonometry`; this page documents the objects that live at the top level itself.

## \_\_version\_\_

*Constant* (`str`).

## octave_filter

```python
octave_filter(
    x: List[float] | np.ndarray,
    fs: int,
    fraction: float = 1,
    order: int = 6,
    limits: List[float] | None = None,
    show: bool = False,
    sigbands: bool = False,
    plot_file: str | None = None,
    detrend: bool = True,
    filter_type: str = 'butter',
    ripple: float = 0.1,
    attenuation: float = 72.0,
    calibration_factor: float = 1.0,
    dbfs: bool = False,
    mode: str = 'rms',
    nominal: bool = False,
) -> Tuple[np.ndarray, List[float]] | Tuple[np.ndarray, List[str]] | Tuple[np.ndarray, List[float], List[np.ndarray]] | Tuple[np.ndarray, List[str], List[np.ndarray]]
```

Filter a signal with octave or fractional octave filter bank.

This method uses a filter bank with Second-Order Sections (SOS) coefficients.
To obtain the correct coefficients, automatic subsampling is applied to the
signal in each filtered band.

Multichannel support: If x is 2D (channels, samples), each channel is filtered.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | (*Union[List[float], np.ndarray]*) Input signal (1D array or 2D array [channels, samples]). |
| `fs` | (*int*) Sample rate in Hz. |
| `fraction` | (*float*) Bandwidth 'b'. Examples: 1/3-octave b=3, 1-octave b=1, 2/3-octave b=1.5. Default: 1. |
| `order` | (*int*) Order of the filter. Default: 6. |
| `limits` | (*Optional[List[float]]*) Minimum and maximum limit frequencies [f_min, f_max]. Default [12, 20000]. |
| `show` | (*bool*) If True, plot and show the filter response. |
| `sigbands` | (*bool*) If True, also return the signal in the time domain divided into bands. |
| `plot_file` | (*Optional[str]*) Path to save the filter response plot. |
| `detrend` | (*bool*) If True, remove DC offset before filtering. Default: True. |
| `filter_type` | Type of filter ('butter', 'cheby1', 'cheby2', 'ellip', 'bessel'). Default: 'butter' (the only type that meets IEC 61260-1 class 1 with the default parameters). |
| `ripple` | Passband ripple in dB (for cheby1, ellip). Default: 0.1. |
| `attenuation` | Stopband attenuation in dB (for cheby2, ellip). Default: 72.0. For `cheby2` scipy pins the deep-stopband floor at exactly this value, so it must be >= 70 dB to clear the IEC 61260-1 class 1 limit (matches [`OctaveFilterBank`](/phonometry/reference/api/filters/core/#octavefilterbank)). |
| `calibration_factor` | Calibration factor for SPL calculation. Default: 1.0. |
| `dbfs` | If True, return results in dBFS. Default: False. |
| `mode` | 'rms' or 'peak'. Default: 'rms'. |
| `nominal` | If True, return IEC 61260-1 nominal frequency labels (List[str]) instead of exact floats. |

**Returns:** A tuple containing (SPL_array, Frequencies_list) or (SPL_array, Frequencies_list, signals). When *nominal=True*, the frequency list contains `List[str]` labels instead of floats. (*Union[Tuple[np.ndarray, List[float]], Tuple[np.ndarray, List[str]], Tuple[np.ndarray, List[float], List[np.ndarray]], Tuple[np.ndarray, List[str], List[np.ndarray]]]*)

## octavefilter

```python
octavefilter(*args: Any, **kwargs: Any) -> Any
```

Deprecated alias of [`octave_filter`](/phonometry/reference/api/filters/phonometry/#octave_filter).

## PhonometryWarning

Base class for all phonometry warnings.
