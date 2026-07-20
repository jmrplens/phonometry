---
title: "building.intensity_insulation"
description: "Public API of phonometry.building.intensity_insulation (auto-generated)."
sidebar:
  label: "intensity_insulation"
---

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

Sound insulation measured with sound intensity (ISO 15186).

This is the sound-**intensity** counterpart of the sound-pressure methods in
[`phonometry.lab_insulation`](/phonometry/reference/api/building/lab-insulation/) (ISO 10140) and [`phonometry.insulation`](/phonometry/reference/api/building/insulation/)
(ISO 16283). Instead of an equivalent absorption area in the receiving room,
the transmitted sound power is measured directly by scanning an intensity
probe over a measurement surface enclosing the specimen. The main use is when
the traditional pressure method fails because of high flanking transmission
(ISO 15186-1:2000, Clause 1): the intensity method only captures the power
radiated by the element itself.

**Intensity sound reduction index (ISO 15186-1:2000, Clause 3.8, Formula
(7)).** From the average source-room sound pressure level `Lp1` and the
average normal sound intensity level `LIn` over the measurement surface,

`RI = Lp1 - 6 - [LIn + 10 lg(Sm / S)]` dB

with the measurement-surface area `Sm` and the specimen area `S`. The
constant `6` dB is the diffuse-field relationship between the sound pressure
level and the sound intensity level incident on the specimen. The same formula
yields the *apparent* index `R'I` in the field (ISO 15186-2), the only
difference being the measurement condition (flanking is not suppressed), not
the arithmetic.

**Modified intensity sound reduction index (Clause 3.10, Formula (9)).**
`RI,M = RI + Kc` corrects `RI` so that it reproduces the ISO 140-3 (now
ISO 10140-2) pressure result, which slightly overestimates `R` because the
power radiated into the receiving room is underestimated. The adaptation term
`Kc` (Annex B) is `10 lg(1 + Sb2 lambda / (8 V2))` (Formula (B.1)) for a
well-defined receiving room of boundary area `Sb2` and volume `V2`, or the
room-independent approximation `10 lg(1 + 61,4 / f)` (Formula (B.2)); both
use the speed of sound `c = 340 m/s` so that (B.1) with the reference room
`Sb2 = 117 m²`, `V2 = 81 m³` reduces to (B.2).

**Intensity element normalized level difference (Clause 3.9, Formula (8)).**
For small building elements, `DI,n,e = Lp1 - 6 - (LIn + 10 lg(Sm / A0) +
10 lg N)` dB with the reference absorption area `A0 = 10 m²` and the number
`N` of element units in the measurement surface.

**Surface pressure-intensity indicator (Clause 3.6 / 6.4.2, Formula (10)).**
`FpI = Lp - LIn` qualifies the measurement surface: it must stay below
10 dB for a sound-reflecting specimen (below 6 dB when the receiving side is
sound absorbing), and the probe's pressure-residual intensity index must
exceed `FpI + 10` dB (Clause 4.1) for the dynamic capability to be adequate.

**Frequency range (Clause 6.6).** Quantities are measured over the mandatory
one-third-octave range 100 Hz to 5000 Hz (18 bands), optionally extended down
to 50 Hz. The single-number weighted rating uses the ISO 717-1 core range, so
the automatic rating (`RI,w`, `RI,M,w`, `DI,n,e,w`) is formed via the
verified [`phonometry.weighted_rating`](/phonometry/reference/api/building/insulation/#weighted_rating) engine only when exactly 16
one-third-octave (100-3150 Hz) or 5 octave (125-2000 Hz) values are supplied.

## adaptation_term_kc

```python
adaptation_term_kc(
    freq: Sequence[float] | np.ndarray,
    *,
    boundary_area: float | None = None,
    volume: float | None = None,
) -> np.ndarray
```

Adaptation term `Kc` per ISO 15186-1:2000, Annex B.

Returns, per one-third-octave midband frequency, the term `Kc` that
turns the intensity sound reduction index `RI` into the modified index
`RI,M = RI + Kc` (Clause 3.10). Two forms are available:

- **Well-defined receiving room (Formula (B.1)):** when both
  `boundary_area` (`Sb2`) and `volume` (`V2`) are supplied,
  `Kc = 10 lg(1 + Sb2 lambda / (8 V2))` with the midband wavelength
  `lambda = c / f` and `c = 340 m/s`.
- **Room-independent approximation (Formula (B.2)):** when neither is
  supplied, `Kc = 10 lg(1 + 61,4 / f)`, the exact reduction of (B.1)
  for the reference room `Sb2 = 117 m²`, `V2 = 81 m³`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `freq` | One-third-octave midband frequencies, in Hz. |
| `boundary_area` | Total boundary-surface area `Sb2` of the receiving room, in m². Supply together with `volume` for (B.1). |
| `volume` | Receiving-room volume `V2`, in m³. |

**Returns:** The adaptation term `Kc` per band, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `freq` is not positive/finite, if only one of `boundary_area` / `volume` is supplied, or if either is not positive. |

## combine_subareas

```python
combine_subareas(
    l_in: Sequence[Sequence[float]] | np.ndarray,
    measurement_area: Sequence[float] | np.ndarray,
) -> tuple[np.ndarray, float]
```

Combine per-subarea intensity levels (ISO 15186-1, Formulas (11)-(12)).

When the measurement surface is divided into subareas `Smi` each scanned
individually, the normal sound intensity level over the whole surface is
the area-weighted energy average

`LIn = 10 lg[ (1/Sm) sum_i Smi 10^(0,1 LIni) ]` dB

with the total measured area `Sm = sum_i |Smi|` (Formula (12)).

**Negative-direction subareas (Clause 6.4.6).** When the sound intensity
of a subarea has a negative direction (net energy flowing back towards
the specimen), the standard requires a minus sign before that `Smi` in
Formula (11). Express this by passing the subarea's area as a *negative*
number: its energy is subtracted in the numerator while `Sm` keeps the
unsigned area sum.

**Parameters**

| Name | Description |
| :--- | :--- |
| `l_in` | Per-subarea intensity levels as a `(subareas, bands)` array (one row per subarea), in dB (magnitude of the intensity). |
| `measurement_area` | Subarea areas `Smi`, in m² (one per row). Negative values mark reverse-flow subareas per Clause 6.4.6; zero is invalid. |

**Returns:** A tuple `(LIn, Sm)` with the combined level per band, in dB, and the total measured area `Sm = sum |Smi|`, in m².

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the shapes are inconsistent or values non-finite, if any subarea area is zero, or if the signed energy sum of Formula (11) is not positive in some band (the reverse flows cancel or exceed the forward flow, so no level exists). |

## intensity_element_normalized_difference

```python
intensity_element_normalized_difference(
    lp1: Sequence[float] | np.ndarray,
    l_in: Sequence[float] | np.ndarray,
    *,
    measurement_area: float,
    n: int = 1,
) -> IntensityElementNormalizedResult
```

Intensity element normalized level difference per ISO 15186-1 (Formula (8)).

Computes, per frequency band, the intensity element normalized level
difference for small building elements

`DI,n,e = Lp1 - 6 - (LIn + 10 lg(Sm / A0) + 10 lg N)` dB

from the average source-room sound pressure level `Lp1`, the average
normal sound intensity level `LIn` over the measurement surface of area
`Sm` (`measurement_area`), the reference absorption area `A0 = 10
m²` and the number `N` of element units installed within the surface.
The weighted rating `DI,n,e,w` is computed via
[`phonometry.weighted_rating`](/phonometry/reference/api/building/insulation/#weighted_rating) (ISO 717-1) when exactly 16 or 5 values
are supplied.

**Parameters**

| Name | Description |
| :--- | :--- |
| `lp1` | Source-room sound pressure levels, in dB. |
| `l_in` | Normal sound intensity levels over the measurement surface, in dB. |
| `measurement_area` | Measurement-surface area `Sm`, in m². |
| `n` | Number `N` of small element units in the surface (Default: 1). |

**Returns:** [`IntensityElementNormalizedResult`](/phonometry/reference/api/building/intensity-insulation/#intensityelementnormalizedresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the band counts differ, if `measurement_area` is not positive, if `n` is not a positive integer, or if inputs are non-finite. |

## intensity_sound_reduction

```python
intensity_sound_reduction(
    lp1: Sequence[float] | np.ndarray,
    l_in: Sequence[float] | np.ndarray,
    *,
    measurement_area: float,
    area: float,
    kc: Sequence[float] | np.ndarray | None = None,
) -> IntensityReductionResult
```

Intensity sound reduction index per ISO 15186-1:2000 (Formula (7)).

Computes, per frequency band, the intensity sound reduction index

`RI = Lp1 - 6 - [LIn + 10 lg(Sm / S)]` dB

from the average source-room sound pressure level `Lp1` and the average
normal sound intensity level `LIn` over the measurement surface of area
`Sm` (`measurement_area`), for a specimen of area `S` (`area`).
The same formula gives the apparent index `R'I` in the field
(ISO 15186-2). When an adaptation term `kc` is supplied (see
[`adaptation_term_kc`](/phonometry/reference/api/building/intensity-insulation/#adaptation_term_kc)), the modified index `RI,M = RI + Kc`
(Formula (9)) is also formed. Weighted ratings `RI,w` (and `RI,M,w`)
are computed via [`phonometry.weighted_rating`](/phonometry/reference/api/building/insulation/#weighted_rating) (ISO 717-1) when
exactly 16 one-third-octave (100-3150 Hz) or 5 octave (125-2000 Hz)
values are supplied.

`lp1` and `l_in` may be one value per band (already averaged) or a
two-dimensional `(positions, bands)` array, in which case the positions
are energy-averaged. Subareas scanned separately should first be combined
with [`combine_subareas`](/phonometry/reference/api/building/intensity-insulation/#combine_subareas).

**Parameters**

| Name | Description |
| :--- | :--- |
| `lp1` | Source-room sound pressure levels, in dB. |
| `l_in` | Normal sound intensity levels over the measurement surface, in dB. |
| `measurement_area` | Measurement-surface area `Sm`, in m². |
| `area` | Specimen area `S`, in m². |
| `kc` | Adaptation term `Kc` per band (dB) for the modified index, or `None` to skip it. |

**Returns:** [`IntensityReductionResult`](/phonometry/reference/api/building/intensity-insulation/#intensityreductionresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the band counts differ, if `measurement_area` / `area` are not positive, or if inputs are non-finite. |

## IntensityElementNormalizedResult

```python
IntensityElementNormalizedResult(
    d_i_n_e: np.ndarray,
    rating: WeightedRatingResult | None,
)
```

Per-band intensity element normalized level difference (ISO 15186-1).

**Attributes**

| Name | Description |
| :--- | :--- |
| `d_i_n_e` | Intensity element normalized level difference `DI,n,e = Lp1 - 6 - (LIn + 10 lg(Sm/A0) + 10 lg N)` per band, in dB (Clause 3.9, Formula (8)). |
| `rating` | Single-number weighted rating `DI,n,e,w` with `C` / `Ctr` (ISO 717-1), or `None` when the band count is neither 16 (one-third octave) nor 5 (octave). |

### IntensityElementNormalizedResult.plot()

```python
IntensityElementNormalizedResult.plot(
    ax: Axes | None = None,
    **kwargs: Any,
) -> Axes
```

Plot `DI,n,e` against the shifted ISO 717-1 reference curve.

Delegates to the weighted-rating plot. Requires the automatic rating
to be available (16 or 5 bands) and matplotlib
(`pip install phonometry[plot]`); returns the
`Axes`.

## IntensityReductionResult

```python
IntensityReductionResult(
    r_i: np.ndarray,
    r_i_modified: np.ndarray | None,
    rating: WeightedRatingResult | None,
    rating_modified: WeightedRatingResult | None,
)
```

Per-band intensity sound reduction index (ISO 15186-1:2000).

**Attributes**

| Name | Description |
| :--- | :--- |
| `r_i` | Intensity sound reduction index `RI = Lp1 - 6 - [LIn + 10 lg(Sm/S)]` per band, in dB (Clause 3.8, Formula (7)). In the field (ISO 15186-2) this is the apparent index `R'I`. |
| `r_i_modified` | Modified index `RI,M = RI + Kc` per band, in dB (Clause 3.10, Formula (9)), or `None` when no adaptation term was supplied. |
| `rating` | Single-number weighted rating `RI,w` with `C` / `Ctr` (ISO 717-1), or `None` when the band count is neither 16 (one-third octave) nor 5 (octave). |
| `rating_modified` | Weighted rating `RI,M,w` of the modified index, or `None` when unavailable. |

### IntensityReductionResult.plot()

```python
IntensityReductionResult.plot(ax: Axes | None = None, **kwargs: Any) -> Axes
```

Plot `RI` against the shifted ISO 717-1 reference curve.

Delegates to the weighted-rating plot (measured `RI` versus the
shifted reference, unfavourable deviations shaded). Requires the
automatic rating to be available (16 or 5 bands) and matplotlib
(`pip install phonometry[plot]`); returns the
`Axes`.

## surface_pressure_intensity_indicator

```python
surface_pressure_intensity_indicator(
    lp: Sequence[float] | np.ndarray,
    l_in: Sequence[float] | np.ndarray,
) -> np.ndarray
```

Surface pressure-intensity indicator `FpI` (ISO 15186-1, Formula (10)).

Returns `FpI = Lp - LIn` per band from the surface- and time-averaged
sound pressure level `Lp` and normal sound intensity level `LIn` on
the measurement surface (Clause 3.6 / 6.4.2). The measurement surface is
adequately qualified when `FpI` stays below 10 dB for a sound-reflecting
specimen, or below 6 dB when the receiving side is sound absorbing; in
addition the probe's pressure-residual intensity index must exceed
`FpI + 10` dB (Clause 4.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `lp` | Surface-averaged sound pressure levels, in dB. |
| `l_in` | Normal sound intensity levels on the surface, in dB. |

**Returns:** The indicator `FpI` per band, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the shapes differ or contain non-finite values. |
