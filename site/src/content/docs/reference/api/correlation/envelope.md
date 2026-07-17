---
title: "metrology.envelope"
description: "Public API of phonometry.metrology.envelope (auto-generated)."
sidebar:
  label: "envelope"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Envelope and instantaneous phase via the Hilbert transform.

Signal-envelope analysis following Bendat & Piersol, *Random Data:
Analysis and Measurement Procedures* (4th ed., 2010), Chapter 13. The
analytic signal `z(t) = x(t) + j·x̃(t)` (Eq. 13.15, with `x̃` the
Hilbert transform of `x`) yields

* the **envelope** `A(t) = [x²(t) + x̃²(t)]^½` (Eq. 13.17),
* the **instantaneous phase** `θ(t) = arctan[x̃(t)/x(t)]`, unwrapped
  (Eq. 13.18), and
* the **instantaneous frequency** `f(t) = (1/2π)·dθ/dt` (Eq. 13.19).

The analytic signal is computed the way the book recommends
(Section 13.1.1): the one-sided spectrum construction
`Z(f) = 2·X(f)` for `f > 0`, `X(0)` at DC and `0` for `f < 0`
(Eq. 13.25) - which is exactly what `scipy.signal.hilbert`
implements, and the same construction the ECMA-418-2 psychoacoustic chain
of `phonometry.psychoacoustics` applies per auditory band (its
Formulae 65/119 take `|hilbert|` and subsample by 32; the standard can
subsample directly because each band is narrow). Closed-form pairs from
Table 13.1 (`cos → sin`, an AM envelope recovered exactly) anchor the
tests.

The envelope of a band-limited signal is itself low-frequency, so the
result offers optional **decimation**: an anti-aliased zero-phase FIR
decimator for general records, or plain subsampling (`antialias=False`)
matching the ECMA-internal convention when the input is already
narrowband.

## envelope

```python
envelope(
    x: NDArray[np.float64] | list[float],
    fs: float,
    *,
    decimation_factor: int = 1,
    antialias: bool = True,
) -> EnvelopeResult
```

Envelope, instantaneous phase and frequency via Hilbert transform.

Builds the analytic signal by the one-sided spectrum construction of
Bendat & Piersol Eq. 13.25 (`scipy.signal.hilbert`) and returns the
envelope `|z(t)|`, the unwrapped instantaneous phase and the
instantaneous frequency (Eqs. 13.17-13.19). For an amplitude-modulated
carrier `u(t)·cos(2πf0t)` with `u` low-frequency and non-negative
the envelope recovers `u(t)` exactly in the ideal continuous case
(Eq. 13.27); a discrete record shows small edge effects at the record
boundaries.

The optional decimation reduces the output rate by an integer factor:
the envelope is anti-alias filtered with a zero-phase FIR decimator
by default, or plainly subsampled with `antialias=False` - the
convention the ECMA-418-2 loudness/roughness chain applies internally
after its auditory bandpass, appropriate when the input is already
narrowband. The phase and instantaneous frequency, smooth after
unwrapping and differentiated at full rate, are subsampled onto the
same time axis.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | Signal, 1-D. |
| `fs` | Sample rate, in Hz. |
| `decimation_factor` | Integer output decimation (default 1: off). |
| `antialias` | Anti-alias filter the decimated envelope (default `True`). |

**Returns:** An [`EnvelopeResult`](/phonometry/reference/api/correlation/envelope/#enveloperesult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs or parameters are invalid. |

## EnvelopeResult

```python
EnvelopeResult(
    times: NDArray[np.float64],
    envelope: NDArray[np.float64],
    phase: NDArray[np.float64],
    instantaneous_frequency: NDArray[np.float64],
    fs: float,
    signal: NDArray[np.float64],
    signal_fs: float,
    decimation_factor: int,
    antialias: bool,
)
```

Envelope and instantaneous phase of a signal (B&P Chapter 13).

All output arrays share the (possibly decimated) time axis
`times`; the original record is kept at full rate for plotting.

**Attributes**

| Name | Description |
| :--- | :--- |
| `times` | Time axis of the outputs, in seconds. |
| `envelope` | Envelope `A(t) = \|z(t)\|` (Eq. 13.17). |
| `phase` | Unwrapped instantaneous phase `θ(t)`, in radians (Eq. 13.18). |
| `instantaneous_frequency` | `f(t) = (1/2π)·dθ/dt`, in Hz (Eq. 13.19), differentiated at full rate before any decimation. |
| `fs` | Sample rate of the outputs, in Hz (`signal_fs` divided by `decimation_factor`). |
| `signal` | The analysed record, at full rate. |
| `signal_fs` | Sample rate of `signal`, in Hz. |
| `decimation_factor` | Integer decimation applied to the outputs (1: none). |
| `antialias` | Whether the decimation was anti-alias filtered. |

### EnvelopeResult.plot()

```python
EnvelopeResult.plot(
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes | NDArray[Any]
```

Plot the signal with its envelope and the instantaneous frequency.
