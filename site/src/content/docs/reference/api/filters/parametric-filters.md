---
title: "metrology.parametric_filters"
description: "Public API of phonometry.metrology.parametric_filters (auto-generated)."
sidebar:
  label: "parametric_filters"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Weighting filters (A, C, G, Z) and time weighting utilities for audio analysis.
A/C/Z per IEC 61672-1:2013; G (infrasound) per ISO 7196:1995.

## linkwitz_riley

```python
linkwitz_riley(
    x: List[float] | np.ndarray,
    fs: int,
    freq: float,
    order: int = 4,
) -> Tuple[np.ndarray, np.ndarray]
```

Linkwitz-Riley crossover filter (Butterworth squared).
Splits signal into low and high bands with flat sum response.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | Input signal. |
| `fs` | Sample rate. |
| `freq` | Crossover frequency. |
| `order` | Total order (must be even, typically 2 or 4). |

**Returns:** (low_pass_signal, high_pass_signal)

## time_weighting

```python
time_weighting(
    x: List[float] | np.ndarray,
    fs: int,
    mode: str = 'fast',
    initial_state: str | float | np.ndarray | None = None,
) -> np.ndarray
```

Apply time weighting to a signal (Exponential averaging).

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | Input signal (raw pressure/voltage). The function squares it internally. |
| `fs` | Sample rate. |
| `mode` | 'fast' (125ms), 'slow' (1000ms), 'impulse' (35ms rise, 1500ms fall). |
| `initial_state` | Previous mean-square output state `y[-1]`. Use None/'zero' for zero initialization (default), 'first' to initialize from the first input energy, or a scalar/array broadcastable to the input shape without the time axis. |

**Returns:** Time-weighted squared signal (sound pressure level envelope).

## TimeWeighting

```python
TimeWeighting(fs: int, mode: str = 'fast')
```

Stateful time weighting for block processing.

Wraps [`time_weighting`](/phonometry/reference/api/filters/parametric-filters/#time_weighting) carrying the exponential integrator state
across blocks, so concatenated block outputs equal a single continuous call.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sample rate in Hz. |
| `mode` | 'fast' (125 ms), 'slow' (1000 ms) or 'impulse' (35 ms / 1.5 s). |

### TimeWeighting.process()

```python
TimeWeighting.process(x: List[float] | np.ndarray) -> np.ndarray
```

Apply time weighting to a block, continuing from the previous block.

### TimeWeighting.reset()

```python
TimeWeighting.reset() -> None
```

Forget the carried state (the next block starts from rest).

## weighting_filter

```python
weighting_filter(
    x: List[float] | np.ndarray,
    fs: int,
    curve: str = 'A',
    high_accuracy: bool = True,
) -> np.ndarray
```

Apply frequency weighting (A or C) to a signal.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | Input signal. |
| `fs` | Sample rate. |
| `curve` | 'A', 'C', 'G' (ISO 7196 infrasound) or 'Z' (bypass). |
| `high_accuracy` | Use internal oversampling for IEC 61672-1 class 1 accuracy at high frequencies (default True). |

**Returns:** Weighted signal.

## WeightingFilter

```python
WeightingFilter(
    fs: int,
    curve: str = 'A',
    stateful: bool = False,
    steady_ic: bool = False,
    high_accuracy: bool | None = None,
)
```

Class-based frequency weighting filter (A, C, G, Z).
Allows pre-calculating and reusing filter coefficients.

Initialize the weighting filter.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sample rate in Hz. |
| `curve` | 'A', 'C', 'G' (ISO 7196 infrasound) or 'Z'. |
| `stateful` | If True, the weighting filter is stateful. Useful for block processing. |
| `steady_ic` | If True, calculate steady state initial conditions for filter. |
| `high_accuracy` | If True, design and run the filter at an internal oversampled rate (target >= 144 kHz) so the response stays within IEC 61672-1 class 1 tolerances up to 16 kHz. At 48 kHz this oversamples x3, keeping the deviation from the analytic curve to about -0.44 dB @16k / -0.85 dB @20k. The plain bilinear design still holds class 1 at fs = 44.1/48 kHz (about -2.7 dB at 12.5 kHz, inside the +2.0/-5.0 class 1 limits) but degrades to class 2 for fs \<= 32 kHz. Defaults to True except in stateful mode (the internal FIR resampling is incompatible with block processing). |

### WeightingFilter.filter()

```python
WeightingFilter.filter(x: List[float] | np.ndarray) -> np.ndarray
```

Apply the weighting filter to a signal.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | Input signal (1D or 2D [channels, samples]). |

**Returns:** Weighted signal.
