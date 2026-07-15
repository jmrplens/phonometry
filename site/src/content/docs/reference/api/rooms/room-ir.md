---
title: "room.room_ir"
description: "Public API of phonometry.room.room_ir (auto-generated)."
sidebar:
  label: "room_ir"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Impulse-response acquisition per BS EN ISO 18233:2006.

This module provides the deterministic-excitation front end for the "new
measurement methods" of ISO 18233: generate an excitation signal, play it
through the system under test, and recover the broadband impulse response
(IR) by deconvolution. Later processing (fractional-octave filtering,
Schroeder backward integration, reverberation time) consumes this IR.

Two excitation families are implemented:

* **Swept-sine (Annex B)** -- an exponential sine sweep (ESS). The frequency
  rises exponentially with time, which mimics a pink-noise source
  (ISO 18233:2006, B.3.2) and is the recommended broadband excitation. The
  IR is recovered by linear (zero-padded, non-circular) spectral
  deconvolution (B.5, Figure B.3): `H = Y * conj(X) / (|X|^2 + reg)`. A
  Farina inverse-filter variant (`method="farina"`) convolves the
  recording with the time-reversed, amplitude-compensated sweep (B.5,
  Figure B.2). Because a low-to-high sweep places distortion products at
  negative arrival times, harmonic distortion is separated from the linear
  IR and discarded by keeping only the causal part (B.5).

* **Maximum-length sequence (Annex A)** -- an order-`N` binary sequence of
  length `2**N - 1` generated with a linear-feedback shift register
  (LFSR). Its circular autocorrelation is a near-perfect delta (A.1), so the
  IR of a periodically excited linear system is recovered by circular
  cross-correlation of the recorded period with the sequence
  (equivalent to the Hadamard-transform recovery of A.1).

The recovered IR is broadband; ISO 18233 6.3.2 requires subsequent
fractional-octave-band weighting (IEC 61260) before computing levels or
decay curves -- that step belongs to downstream room-acoustics modules.

## impulse_response

```python
impulse_response(
    recorded: List[float] | np.ndarray,
    reference: List[float] | np.ndarray,
    fs: int,
    *,
    method: str = 'spectral',
    f_range: Tuple[float, float] | None = None,
    regularization: float = 1e-06,
    length: int | None = None,
    return_full: bool = False,
) -> ImpulseResponseResult
```

Recover the broadband impulse response by sweep deconvolution.

Implements the linear (non-circular) deconvolution of ISO 18233:2006,
B.5. Both signals are zero-padded to `len(recorded)+len(reference)-1`
to avoid circular convolution (B.5). The causal IR occupies the start of
the result; distortion products from a low-to-high sweep fall at negative
arrival times (the wrapped tail) and are discarded by returning only the
causal part (B.5).

**Parameters**

| Name | Description |
| :--- | :--- |
| `recorded` | Recorded system response to the sweep. |
| `reference` | The emitted sweep (excitation signal). |
| `fs` | Sampling frequency in Hz (kept for API symmetry; the deconvolution itself is sample-rate agnostic). |
| `method` | `"spectral"` for spectral division `H = Y*conj(X)/(\|X\|^2+reg)` (Figure B.3, default) or `"farina"` for convolution with the analytic inverse filter (Figure B.2). The Farina method requires `f_range` and the **exact-length, unpadded** excitation sweep as `reference` (it rebuilds the inverse filter from `reference.size/fs` as the sweep duration); a reference zero-padded to the recording length - the correct input for the spectral method - is rejected with a `ValueError` because it would silently produce a wrong inverse filter. It also assumes the reference sweep was generated with the default `amplitude`/`fade` of [`sweep_signal`](/phonometry/reference/api/rooms/room-ir/#sweep_signal); a non-unit amplitude or custom fade yields a scaled IR, so use the spectral method in that case. |
| `f_range` | `(f1, f2)` of the sweep, required for `method="farina"` to rebuild the inverse filter; ignored for the spectral method. |
| `regularization` | Tikhonov term added to the denominator, expressed as a fraction of the peak spectral energy `max(\|X\|^2)` (spectral method only). Guards against amplifying noise where the sweep has little energy, e.g. outside its frequency range (B.5). Default 1e-6. |
| `length` | Number of samples of the causal IR to return. Defaults to `len(recorded)`. Ignored when `return_full` is True. |
| `return_full` | If True, return the full deconvolution sequence (causal IR at index 0, negative-time distortion products in the tail) instead of the trimmed causal IR. Default False. |

**Returns:** An [`ImpulseResponseResult`](/phonometry/reference/api/rooms/room-ir/#impulseresponseresult) wrapping the recovered impulse response. It behaves like the raw IR array (`np.asarray(result)`, indexing, `.size`) for every downstream consumer and adds [`ImpulseResponseResult.plot`](/phonometry/reference/api/rooms/room-ir/#impulseresponseresultplot).

## ImpulseResponseResult

```python
ImpulseResponseResult(ir: np.ndarray, fs: int | None, method: str)
```

Recovered broadband impulse response with its acquisition metadata.

Returned by [`impulse_response`](/phonometry/reference/api/rooms/room-ir/#impulse_response) and [`mls_impulse_response`](/phonometry/reference/api/rooms/room-ir/#mls_impulse_response).
The impulse response samples live in `ir`; `fs` is the sample rate in
Hz (or `None` when unknown, e.g. an MLS recovery called without one) and
`method` records how the IR was obtained (`"spectral"`, `"farina"`
or `"mls"`).

The object is a drop-in replacement for the raw array it used to be: it
implements `__array__`, so `np.asarray(result)` yields the IR and
the result can be passed straight to array consumers such as
[`phonometry.room_parameters`](/phonometry/reference/api/rooms/room-acoustics/#room_parameters), [`phonometry.decay_curve`](/phonometry/reference/api/rooms/room-acoustics/#decay_curve) and
[`phonometry.sti_from_impulse_response`](/phonometry/reference/api/speech/sti/#sti_from_impulse_response). Indexing, `len(result)`
and the `size`/`ndim`/`shape`/`dtype` attributes forward to `ir`.

Initialize self.  See help(type(self)) for accurate signature.

### ImpulseResponseResult.dtype

*property*

### ImpulseResponseResult.ndim

*property*

### ImpulseResponseResult.plot()

```python
ImpulseResponseResult.plot(
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes | np.ndarray
```

Plot the impulse response: waveform and log-magnitude decay.

Draws the (normalised) time-domain waveform and, below it, the
log-magnitude envelope in dB with a Schroeder energy-decay overlay.
With `ax` given, only the decay panel is drawn on it. Requires
matplotlib (`pip install phonometry[plot]`); returns the
`Axes` (or an array of two axes).

### ImpulseResponseResult.shape

*property*

### ImpulseResponseResult.size

*property*

Number of samples in the impulse response.

## ImpulseResponseWarning

Warns about suspect recovered impulse responses (e.g. MLS aliasing).

## inverse_filter

```python
inverse_filter(
    fs: int,
    f1: float,
    f2: float,
    seconds: float,
    *,
    amplitude: float = 1.0,
    fade: float = 0.01,
) -> np.ndarray
```

Build the Farina inverse filter for an exponential sine sweep.

The inverse filter is the time-reversed sweep multiplied by an amplitude
envelope that rises by 6 dB/octave (`prop. to the instantaneous
frequency`), which whitens the ESS's pink (-3 dB/octave) spectrum so
that convolving the sweep with its inverse yields an impulse
(ISO 18233:2006, B.5, Figure B.2; Farina 2000, Bibliography [14]). The
filter is scaled to unit in-band magnitude: it is normalised by the
median in-band magnitude of the compressed pulse `sweep * inverse` so
that the deconvolution reproduces a system's true in-band level, matching
the spectral-division convention (rather than a unit pulse peak).

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sampling frequency in Hz. |
| `f1` | Sweep start frequency in Hz (same value used for the sweep). |
| `f2` | Sweep stop frequency in Hz. |
| `seconds` | Sweep duration in seconds. |
| `amplitude` | Peak amplitude used for the source sweep. Default 1.0. |
| `fade` | Fade fraction used for the source sweep. Default 0.01. |

**Returns:** The inverse-filter samples (same length as the sweep).

## mls_impulse_response

```python
mls_impulse_response(
    recorded: List[float] | np.ndarray,
    mls: List[float] | np.ndarray,
    *,
    length: int | None = None,
    fs: int | None = None,
) -> ImpulseResponseResult
```

Recover an impulse response from a periodic MLS excitation.

The recording must span an integer number of MLS periods; the periods
are averaged (raising the effective signal-to-noise ratio by 3 dB per
doubling, ISO 18233:2006, 6.3.6) and the IR is obtained by circular
cross-correlation of the averaged period with the sequence, normalised by
`2**N` (A.1). Because the sequence is periodic, the recovery is a
circular deconvolution: a system IR longer than one period aliases back
into the record (A.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `recorded` | Recorded response, length a multiple of `2**N - 1`. |
| `mls` | The excitation sequence returned by [`mls_signal`](/phonometry/reference/api/rooms/room-ir/#mls_signal). |
| `length` | Number of IR samples to return. Defaults to the sequence length `2**N - 1`. |
| `fs` | Optional sample rate in Hz, stored on the result so that [`ImpulseResponseResult.plot`](/phonometry/reference/api/rooms/room-ir/#impulseresponseresultplot) can label a time axis in seconds (the recovery itself is sample-rate agnostic). Default `None`. |

**Returns:** An [`ImpulseResponseResult`](/phonometry/reference/api/rooms/room-ir/#impulseresponseresult) wrapping the recovered impulse response. It behaves like the raw IR array for every downstream consumer and adds [`ImpulseResponseResult.plot`](/phonometry/reference/api/rooms/room-ir/#impulseresponseresultplot).

:::note
An [`ImpulseResponseWarning`](/phonometry/reference/api/rooms/room-ir/#impulseresponsewarning) is emitted when the recovered IR retains significant
energy at the end of the period (a circular-aliasing symptom). The
tail-RMS heuristic is advisory: a high ambient noise floor in the
recording raises the tail RMS on its own and can trigger a
false positive even when the IR fits within one period, so treat the
warning as a prompt to check the noise floor and MLS order rather than
a definitive aliasing diagnosis.
:::

## mls_signal

```python
mls_signal(order: int) -> np.ndarray
```

Generate a maximum-length sequence (MLS) of the given order.

A Fibonacci LFSR with primitive-polynomial feedback taps produces a
binary sequence of length `2**order - 1` whose circular
autocorrelation is a near-perfect periodic delta
(ISO 18233:2006, A.1). The binary values are mapped to `+1`/`-1`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `order` | Register length `N` (2 to 20). The sequence length is `2**order - 1`. |

**Returns:** The bipolar MLS samples (values in `{-1.0, +1.0}`).

## plot_excitation

```python
plot_excitation(
    signal: np.ndarray | Any,
    fs: int,
    *,
    kind: str = 'sweep',
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes | np.ndarray
```

Plot an ISO 18233 excitation signal (sweep or MLS).

A documented helper for the raw arrays returned by
[`sweep_signal`](/phonometry/reference/api/rooms/room-ir/#sweep_signal) and [`mls_signal`](/phonometry/reference/api/rooms/room-ir/#mls_signal), which
stay plain `numpy.ndarray` (they are meant for playback). For a
swept sine the waveform and its spectrogram are drawn; for an MLS the first
samples of the bipolar sequence and its (flat) magnitude spectrum.

**Parameters**

| Name | Description |
| :--- | :--- |
| `signal` | The excitation samples (1D array-like). |
| `fs` | Sample rate in Hz (for the time and frequency axes). |
| `kind` | `"sweep"` (default) or `"mls"`. |
| `ax` | Existing axes for the top (time-domain) panel, or `None` for a fresh two-panel figure. |
| `kwargs` | Forwarded to the time-domain `plot` call. |

**Returns:** The time-domain axes (`ax` given) or the array of two axes.

## sweep_signal

```python
sweep_signal(
    fs: int,
    f1: float,
    f2: float,
    seconds: float,
    *,
    amplitude: float = 1.0,
    fade: float = 0.01,
) -> np.ndarray
```

Generate an exponential sine sweep (ESS) with exact analytic phase.

The instantaneous frequency rises exponentially from `f1` to `f2`,
`f(t) = f1 * (f2/f1) ** (t/T)`, so the time spent per octave is
constant and the sweep mimics a pink-noise excitation
(ISO 18233:2006, B.3.2). The phase is the closed-form integral of
`2*pi*f(t)` (Farina, AES 108th Conv., 2000; ISO 18233 Bibliography
[14]), avoiding numerical phase accumulation.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fs` | Sampling frequency in Hz. |
| `f1` | Start frequency in Hz (at or below the lowest band edge to be measured, ISO 18233 B.3.1). Must be > 0. |
| `f2` | Stop frequency in Hz (at or above the highest band edge). Must satisfy `f1 < f2 <= fs/2`. |
| `seconds` | Sweep duration in seconds. Any duration may be used; a longer sweep raises the effective signal-to-noise ratio (B.2, B.6). |
| `amplitude` | Peak amplitude of the sweep. Default 1.0. |
| `fade` | Half-Hann fade-in/out length as a fraction of the sweep duration, applied to suppress start/stop transients (B.3.3). Default 0.01. Set to 0.0 to disable. Because the sweep frequency is logarithmic in time, the fades consume roughly `fade*log2(f2/f1)` octaves at each band edge (the fade-out lands on the highest frequencies): with the default 0.01 the top ~29 dB of the highest band is unusable, so choose `f1`/`f2` with margin beyond the analysis range (ISO 18233 B.3.1) rather than relying on a smaller fade. |

**Returns:** The sweep samples, length `round(seconds*fs)`.
