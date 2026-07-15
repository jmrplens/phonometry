---
title: "hearing.sii"
description: "Public API of phonometry.hearing.sii (auto-generated)."
sidebar:
  label: "sii"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Speech Intelligibility Index (SII) per ANSI S3.5-1997 (R2017).

Implements the one-third-octave-band method (18 bands, 160 Hz - 8000 Hz) of
ANSI S3.5-1997, *American National Standard Methods for the Calculation of the
Speech Intelligibility Index*. From an equivalent speech spectrum level, an
equivalent noise spectrum level and an equivalent hearing threshold, the
procedure forms the self-speech masking, the upward spread of masking, the
equivalent internal noise and disturbance, the level-distortion factor and the
band-audibility function, and weights the latter by the band-importance function
of Table 3 to give the index `SII` in [0, 1] (clause 6).

The band-importance function (Table 3, average speech material), the standard
speech spectrum levels by vocal effort (Table 3) and the reference internal
noise spectrum level (Table 3) are the standard's own tabulated constants.
Spectrum levels are as defined in clauses 3.11 and 3.55.

## SIIResult

```python
SIIResult(
    sii: float,
    band_audibility: np.ndarray,
    band_importance: np.ndarray,
    frequencies: np.ndarray,
    speech_spectrum: np.ndarray,
    disturbance: np.ndarray,
    masking: np.ndarray,
)
```

Result of a Speech Intelligibility Index computation (ANSI S3.5-1997).

**Attributes**

| Name | Description |
| :--- | :--- |
| `sii` | The overall Speech Intelligibility Index in [0, 1] (clause 6). |
| `band_audibility` | Per-band audibility function `Ai` (clause 5.8). |
| `band_importance` | Per-band importance function `Ii` used (Table 3). |
| `frequencies` | One-third-octave band centre frequencies, in hertz. |
| `speech_spectrum` | Equivalent speech spectrum level `Ei'` per band. |
| `disturbance` | Equivalent disturbance spectrum level `Di` (clause 5.6). |
| `masking` | Equivalent masking spectrum level `Zi` (clause 5.4). |

Initialize self.  See help(type(self)) for accurate signature.

### SIIResult.plot()

```python
SIIResult.plot(ax: Axes | None = None, **kwargs: Any) -> Axes
```

Plot the per-band audibility weighted by importance, with the SII.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## speech_intelligibility_index

```python
speech_intelligibility_index(
    speech_spectrum: ArrayLike,
    noise_spectrum: ArrayLike | None = None,
    *,
    threshold: ArrayLike | None = None,
) -> SIIResult
```

Speech Intelligibility Index (ANSI S3.5-1997, one-third-octave method).

All spectra are equivalent spectrum levels (clauses 3.11/3.55) sampled at
the 18 one-third-octave band centres from 160 Hz to 8000 Hz.

**Parameters**

| Name | Description |
| :--- | :--- |
| `speech_spectrum` | Equivalent speech spectrum level `Ei'`, in dB SPL. A vocal-effort name (`"normal"`, `"raised"`, `"loud"` or `"shout"`) selects the corresponding standard speech spectrum (Table 3). |
| `noise_spectrum` | Equivalent noise spectrum level `Ni'`, in dB SPL; `None` uses a quiet field (`-80` dB in every band). |
| `threshold` | Equivalent hearing threshold `Ti'`, in dB HL; `None` uses normal hearing (`0` in every band). |

**Returns:** An [`SIIResult`](/phonometry/reference/api/speech/sii/#siiresult) with the overall index and its `.plot()`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if a spectrum has the wrong length or effort name. |

## standard_speech_spectrum

```python
standard_speech_spectrum(vocal_effort: str = 'normal') -> np.ndarray
```

Standard speech spectrum level by vocal effort (ANSI S3.5-1997 Table 3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `vocal_effort` | One of `"normal"`, `"raised"`, `"loud"`, `"shout"`. |

**Returns:** The 18-band equivalent speech spectrum level `Ui`, in dB SPL.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for an unknown vocal effort. |
