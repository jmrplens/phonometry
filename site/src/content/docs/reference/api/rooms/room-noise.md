---
title: "room.room_noise"
description: "Public API of phonometry.room.room_noise (auto-generated)."
sidebar:
  label: "room_noise"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Room-noise rating curves per ANSI/ASA S12.2-2019.

Implements the two spectrum-in rating methods of ANSI/ASA S12.2-2019, *Criteria
for Evaluating Room Noise*:

* **Noise Criteria (NC)** by the tangency method (Table 1). The NC rating is the
  value of the highest NC curve touched by the measured octave-band spectrum,
  reported together with the governing band.
* **Room Criteria Mark II (RC)** (Annex D, Table D.1). The numerical rating is
  the mid-frequency average `LMF` (500/1000/2000 Hz) rounded to the nearest
  decibel (clause D.4); the spectral tag `N`/`R`/`H` follows the
  deviation rules of clause D.3.

Both methods evaluate octave-band sound pressure levels over the 16 Hz to
8000 Hz bands tabulated by the standard. The RC Mark II curves are generated
from the -5 dB/octave rule of Annex D (16 Hz equal to 31.5 Hz, with the low
frequencies not dropping below 55 dB), which reproduces Table D.1 exactly.

The balanced noise criteria (NCB), the room noise criterion for fluctuating
low-frequency noise (RNC, Annex A) and the numeric quality-assessment index
(QAI, clause D.5 - deferred by the standard to external references) are not
implemented here.

## nc_curve

```python
nc_curve(index: float) -> np.ndarray
```

Octave-band levels of a Noise Criteria curve (ANSI/ASA S12.2-2019 Table 1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `index` | The NC designation. Integer designations from 15 to 70 in steps of five return the tabulated curve; intermediate values are linearly interpolated band by band. |

**Returns:** The 10-band curve levels, in dB, aligned with [`OCTAVE_BANDS`](/phonometry/reference/api/materials/absorption-rating/#octave_bands).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if `index` is outside the tabulated range. |

## NCResult

```python
NCResult(
    rating: float,
    governing_frequency: float,
    frequencies: np.ndarray,
    levels: np.ndarray,
)
```

Result of a Noise Criteria (NC) rating (ANSI/ASA S12.2-2019, tangency).

**Attributes**

| Name | Description |
| :--- | :--- |
| `rating` | The NC rating (value of the highest NC curve touched). |
| `governing_frequency` | Band, in hertz, where the touch occurs. |
| `frequencies` | Octave-band centre frequencies evaluated, in hertz. |
| `levels` | Measured octave-band sound pressure levels, in dB. |

### NCResult.plot()

```python
NCResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the measured spectrum against the NC curves.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## noise_criterion

```python
noise_criterion(
    levels: ArrayLike,
    frequencies: ArrayLike | None = None,
) -> NCResult
```

Noise Criteria (NC) rating by the tangency method (ANSI/ASA S12.2-2019).

The NC rating is the value of the highest NC curve touched by the measured
octave-band spectrum. For each band the NC index whose curve passes through
the measured level is found by interpolation; the rating is the maximum
over bands and the governing band is where that maximum occurs.

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Octave-band sound pressure levels, in dB. Without `frequencies` this must be the 10 bands from 16 Hz to 8000 Hz. |
| `frequencies` | Optional band centre frequencies, in hertz, matching `levels`; a subset of the ANSI S12.2 octave bands may be supplied. |

**Returns:** An [`NCResult`](/phonometry/reference/api/rooms/room-noise/#ncresult) with the rating and its `.plot()`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for malformed inputs or unknown band frequencies. |

## rc_curve

```python
rc_curve(index: float) -> np.ndarray
```

Octave-band levels of a Room Criteria Mark II curve (Annex D, Table D.1).

The curve has a constant slope of -5 dB/octave keyed to its value at
1000 Hz; the 31.5 Hz level does not drop below 55 dB and the 16 Hz level
equals the 31.5 Hz level.

**Parameters**

| Name | Description |
| :--- | :--- |
| `index` | The RC designation (value at 1000 Hz). |

**Returns:** The 10-band curve levels, in dB, aligned with [`OCTAVE_BANDS`](/phonometry/reference/api/materials/absorption-rating/#octave_bands).

## RCResult

```python
RCResult(
    rating: int,
    lmf: float,
    classification: str,
    reference_curve: np.ndarray,
    frequencies: np.ndarray,
    levels: np.ndarray,
)
```

Result of a Room Criteria Mark II rating (ANSI/ASA S12.2-2019, Annex D).

**Attributes**

| Name | Description |
| :--- | :--- |
| `rating` | Numerical RC designation `LMF` rounded to the nearest dB. |
| `lmf` | Mid-frequency average (500/1000/2000 Hz), in dB (clause D.4). |
| `classification` | Spectral tag, `"N"` (neutral), `"R"` (rumble), `"H"` (hiss) or `"RH"` (both) (clause D.3). |
| `reference_curve` | The RC Mark II curve used for classification, in dB. |
| `frequencies` | Octave-band centre frequencies evaluated, in hertz. |
| `levels` | Measured octave-band sound pressure levels, in dB. |

### RCResult.label

*property*

The room-criterion label in the `RC-NN(A)` form (clause D.3.5).

### RCResult.plot()

```python
RCResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the measured spectrum against the reference RC Mark II curve.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## room_criterion

```python
room_criterion(
    levels: ArrayLike,
    frequencies: ArrayLike | None = None,
) -> RCResult
```

Room Criteria Mark II rating (ANSI/ASA S12.2-2019, Annex D).

The numerical rating is the mid-frequency average `LMF` of the 500,
1000 and 2000 Hz levels rounded to the nearest decibel (clause D.4). The
spectral tag is neutral (`"N"`) when the levels at and below 500 Hz do
not exceed the reference RC curve by more than 5 dB and the levels at and
above 1000 Hz do not exceed it by more than 3 dB; rumble (`"R"`) when a
low band exceeds by more than 5 dB; hiss (`"H"`) when a high band
exceeds by more than 3 dB (clause D.3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels` | Octave-band sound pressure levels, in dB. Without `frequencies` this must be the 10 bands from 16 Hz to 8000 Hz. |
| `frequencies` | Optional band centre frequencies, in hertz, matching `levels`. |

**Returns:** An [`RCResult`](/phonometry/reference/api/rooms/room-noise/#rcresult) with the rating, tag and its `.plot()`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | if the 500/1000/2000 Hz mid-frequency bands are absent. |
