---
title: "building.measurement.lab_improvement"
description: "Improvement of sound insulation measured in the laboratory: a lining on a basic element and a floor covering on a reference floor (ISO 10140-1:2021 Annexes G and H)."
sidebar:
  label: "lab_improvement"
---

Improvement of sound insulation measured in the laboratory: a lining on a
basic element and a floor covering on a reference floor (ISO 10140-1:2021
Annexes G and H).

A lining and a floor covering are products that are never sold alone: each is
added to a wall or a floor, and what the laboratory measures is how much it
adds. ISO 10140-1 therefore measures the element twice, without and with the
product, and reports the difference band by band; the single number that
describes the product is then read on a *standard* element rather than on the
laboratory's own, so that two laboratories with different walls report the
same lining the same way.

**Linings, Annex G.** The sound reduction improvement index is
$\Delta R = R_\mathrm{with} - R_\mathrm{without}$ per one-third-octave
band (G.1). On one of the standard basic elements of ISO 10140-5:2021 Annex B
(the heavy wall of about 350 kg/m², the heavy concrete floor, the lightweight
wall of about 70 kg/m²), the single numbers are `ΔRw`, `Δ(Rw + C)` and
`Δ(Rw + Ctr)` of ISO 717-1:2020 Annex D, read on the element's reference curve
(G.5 c), [`weighted_reduction_improvement`](/phonometry/reference/api/building/ratings/#weighted_reduction_improvement)). On any
other basic element they are the direct differences `ΔRw,direct`,
`Δ(Rw + C)direct` and `Δ(Rw + Ctr)direct` of Formula (D.2), which describe
the lining only on that element. G.4 adds one numeric condition, on the curing
of the basic element ([`check_lining_curing`](/phonometry/reference/api/building/lab-improvement/#check_lining_curing)).

**Floor coverings, Annex H.** The improvement of impact sound insulation is
$\Delta L = L_\mathrm{n0} - L_\mathrm{n}$ per band (Formula (H.1)), on the
heavyweight reference floor or on one of the three lightweight (timber)
reference floors of ISO 10140-5:2021 Annex C. The octave values follow from
Formula (H.2),
$\Delta L_\mathrm{oct} = -10 \log_{10}[(1/3) \sum 10^{-\Delta L_j/10}]$,
and the single numbers `ΔLw` (heavyweight) or `ΔLt,1,w`, `ΔLt,2,w`,
`ΔLt,3,w` (lightweight) with their adaptation terms from ISO 717-2:2020
Clauses 5 and 6 ([`weighted_impact_improvement`](/phonometry/reference/api/building/ratings/#weighted_impact_improvement)),
on the reference curves of its Table 4. H.6.1 adds the improvement for the
heavy/soft (rubber ball) source, $\Delta L_\mathrm{r} = L_\mathrm{i,Fmax,0} - L_\mathrm{i,Fmax}$ (Formula (H.3)).

Citations are to ISO 10140-1:2021 (third edition) and, for the reference
curves, to ISO 717-1:2020 and ISO 717-2:2020, which since the 2021 edition of
ISO 10140-5 are where those curves are printed.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## check_lining_curing

```python
check_lining_curing(
    curing_time_days: float,
    time_lag_days: float,
    *,
    required_curing_days: float = 14.0,
) -> LiningCuringCheck
```

Is the basic element settled enough for the two measurements (G.4)?

`ΔR` is the difference of two measurements of the same element, so the
element must not change between them: "it shall either be at its final
condition or the two measurements shall be carried out within a
sufficiently short time interval". For masonry and concrete G.4 puts
numbers on both ways out, and either one suffices:

* a curing period of not less than two weeks (`required_curing_days`,
  unless the product specification sets another); or
* a time lag between the two measurements of at most one third of the
  curing time elapsed before the first one. G.4's example: measurements
  carried out within 1 d can start 3 d after the end of construction.

G.4 also asks the lining and its fixing to have reached their final
condition before the second measurement, which has no number and is not
judged here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `curing_time_days` | Days from the end of construction of the basic element to the first measurement. |
| `time_lag_days` | Days between the two measurements (zero or more). |
| `required_curing_days` | The curing period that settles the element without further condition, in days (default 14). |

**Returns:** A [`LiningCuringCheck`](/phonometry/reference/api/building/lab-improvement/#liningcuringcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If a time is negative or not finite, or the required curing period is not positive. |

## heavy_impact_improvement

```python
heavy_impact_improvement(
    l_i_fmax_0_db: ArrayLike,
    l_i_fmax_db: ArrayLike,
    frequencies_hz: ArrayLike,
) -> HeavyImpactImprovementResult
```

Improvement of a floor covering under the rubber ball (H.6.1).

The floor covering is laid on a reference floor of ISO 10140-5:2021
Annex C and the maximum impact sound pressure level `Li,Fmax` of the
heavy/soft impact source (ISO 10140-3:2021 Annex A, the rubber ball of
ISO 10140-5:2021 Annex F) is measured without and with it; the improvement
is $\Delta L_\mathrm{r} = L_\mathrm{i,Fmax,0} - L_\mathrm{i,Fmax}$
in each band (Formula (H.3)). The source is characterised in octave
bands from 31,5 Hz to 500 Hz, and the levels are usually taken in the
octaves 63 Hz to 500 Hz or the matching one-third octaves
([`heavy_impact_octave_levels`](/phonometry/reference/api/building/heavy-impact/#heavy_impact_octave_levels)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `l_i_fmax_0_db` | `Li,Fmax,0` per band, in dB. |
| `l_i_fmax_db` | `Li,Fmax` per band, in dB. |
| `frequencies_hz` | Band centre frequencies, in Hz. |

**Returns:** A [`HeavyImpactImprovementResult`](/phonometry/reference/api/building/lab-improvement/#heavyimpactimprovementresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs disagree in length, a value is not finite or a frequency is not positive. |

## HeavyImpactImprovementResult

```python
HeavyImpactImprovementResult(
    frequencies_hz: np.ndarray,
    l_i_fmax_0_db: np.ndarray,
    l_i_fmax_db: np.ndarray,
    improvement_db: np.ndarray,
)
```

Improvement for the heavy/soft impact source (ISO 10140-1:2021 H.6.1).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | Band centre frequencies, in Hz. |
| `l_i_fmax_0_db` | Maximum impact sound pressure level of the reference floor without the covering, `Li,Fmax,0`, in dB. |
| `l_i_fmax_db` | The same with the covering, `Li,Fmax`, in dB. |
| `improvement_db` | $\Delta L_\mathrm{r} = L_\mathrm{i,Fmax,0} - L_\mathrm{i,Fmax}$ per band, in dB (Formula (H.3)). |

### HeavyImpactImprovementResult.plot()

```python
HeavyImpactImprovementResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the improvement `ΔLr` per band.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## lab_floor_covering_improvement

```python
lab_floor_covering_improvement(
    l_n0_db: ArrayLike,
    l_n_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    reference_floor: ReferenceFloor = 'heavyweight',
) -> LabFloorCoveringImprovementResult
```

Improvement of impact sound insulation by a floor covering (ISO 10140-1 H).

The reference floor is measured to ISO 10140-3 with the tapping machine,
without and then with the covering at the same positions, and the
improvement is $\Delta L = L_\mathrm{n0} - L_\mathrm{n}$ in each
one-third-octave band (Formula (H.1)). The weighted reduction is read on
the reference curve of the floor it was measured on, ISO 717-2:2020
Table 4: `ΔLw` on the heavyweight concrete floor (Clause 5) and
`ΔLt,1,w`, `ΔLt,2,w` or `ΔLt,3,w` on the lightweight floors of type
No 1, 2 and 3 (Clause 6), each with its adaptation term (Formulas (A.4)
and (A.6)). The result also carries the two ratings H.5 i) asks the report
to state beside them: the reference floor with the covering (`Ln,r,w`,
`CI,r`) and the measured bare floor (`Ln,0,w`, `CI,0`).

ISO 717-2:2020 5.4 confines a `ΔLw` measured on the concrete slab to
"similar types of massive floors"; a covering meant for a timber floor is
measured on a lightweight reference floor. The wooden mock-up of
ISO 10140-5:2021 Annex G is the alternative for a laboratory that cannot
build one (H.6.2): Annex H names no reference curve for it, so its `ΔL`
describes the covering on a similar board and the rating it is given here
is the one of the `reference_floor` the caller names.

**Parameters**

| Name | Description |
| :--- | :--- |
| `l_n0_db` | `Ln0` per one-third-octave band, in dB: the energy-averaged normalized level of the bare floor (e.g. `lab_impact_insulation(...).l_n`). For small category I specimens measured with the tapping machine beside each specimen, it is the arithmetic mean of the two positions either side (H.4.6.1.1). |
| `l_n_db` | `Ln` with the covering, per band, in dB. |
| `frequencies_hz` | Band centre frequencies, in Hz; the ratings are formed on the 16 bands 100 Hz to 3 150 Hz when all are present. |
| `reference_floor` | `"heavyweight"` (default), `"lightweight_1"`, `"lightweight_2"` or `"lightweight_3"`. |

**Returns:** A [`LabFloorCoveringImprovementResult`](/phonometry/reference/api/building/lab-improvement/#labfloorcoveringimprovementresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the three inputs disagree in length, a value is not finite, a frequency is not positive, or `reference_floor` is not one of the four floors. |

## lab_lining_improvement

```python
lab_lining_improvement(
    r_without_db: ArrayLike,
    r_with_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    basic_element: BasicElement | None = 'heavy_wall',
) -> LabLiningImprovementResult
```

Improvement of airborne sound insulation by a lining (ISO 10140-1:2021 G).

The basic element is measured to ISO 10140-2 without and then with the
lining, and the improvement is
$\Delta R = R_\mathrm{with} - R_\mathrm{without}$ in each
one-third-octave band (G.1). What it says about the lining depends on the
element it was measured on (G.2):

* on a standard basic element of ISO 10140-5:2021 Annex B the single
  numbers `ΔRw`, `Δ(Rw + C)` and `Δ(Rw + Ctr)` are read on that
  element's reference curve, which generalises them beyond the
  laboratory (ISO 717-1:2020 Annex D; G.5 c));
* on any other element (`basic_element=None`) only the direct
  differences of the measured single numbers are defined,
  `ΔRw,direct = Rw,with - Rw,without` (ISO 717-1:2020 Formula (D.2)),
  which "include the particular features of the laboratory and the basic
  element" (G.2 c)).

The direct differences are returned in both cases, since they need only
the two measured curves. The single numbers need the 16 rating bands
100 Hz to 3 150 Hz; a spectrum without them keeps its per-band `ΔR` and
reports no rating.

NOTE 2 of G.1 leaves linings on flexible lightweight structures (timber
frame floors, double-leaf gypsum board walls) outside the annex, and
NOTE 1 limits the result to direct airborne transmission; neither can be
read off the numbers, so neither is refused here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `r_without_db` | `Rwithout` per one-third-octave band, in dB (e.g. `lab_airborne_insulation(...).r`). |
| `r_with_db` | `Rwith` per band, in dB. |
| `frequencies_hz` | Band centre frequencies, in Hz. |
| `basic_element` | `"heavy_wall"` (default), `"heavy_floor"`, `"lightweight_wall"` or `None` for a basic element that is not one of the three standard ones. |

**Returns:** A [`LabLiningImprovementResult`](/phonometry/reference/api/building/lab-improvement/#labliningimprovementresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the three inputs disagree in length, a value is not finite, a frequency is not positive, or `basic_element` is unknown. |

## LabFloorCoveringImprovementResult

```python
LabFloorCoveringImprovementResult(
    frequencies_hz: np.ndarray,
    l_n0_db: np.ndarray,
    l_n_db: np.ndarray,
    improvement_db: np.ndarray,
    reference_floor: str,
    delta_lw_db: int | None,
    ci_delta_db: int | None,
    reference_rating: ImpactRatingResult | None,
    bare_rating: ImpactRatingResult | None,
)
```

Improvement of impact sound insulation by a floor covering (Annex H).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | One-third-octave band centre frequencies, in Hz. |
| `l_n0_db` | Normalized impact sound pressure level of the reference floor without the covering, `Ln0`, in dB. |
| `l_n_db` | Normalized impact sound pressure level with the covering, `Ln`, in dB. |
| `improvement_db` | $\Delta L = L_\mathrm{n0} - L_\mathrm{n}$ per band, in dB (Formula (H.1)). |
| `reference_floor` | `"heavyweight"`, `"lightweight_1"`, `"lightweight_2"` or `"lightweight_3"`. |
| `delta_lw_db` | The weighted reduction on the reference curve of that floor (`ΔLw` or `ΔLt,n,w`, ISO 717-2:2020 Clauses 5 and 6), in dB, or `None` without the 16 rating bands 100 Hz to 3 150 Hz. |
| `ci_delta_db` | Its spectrum adaptation term, `CI,Δ` on the heavyweight floor (Formula (A.4)) or `CIΔ,t` on a lightweight one (Formula (A.6)), designated `CIΔ,t1` to `CIΔ,t3` by floor type (ISO 717-2:2020 A.2.3), in dB, or `None`. |
| `reference_rating` | The ISO 717-2 rating of the reference curve with the covering, $L_\mathrm{n,r} = L_\mathrm{n,r,0} - \Delta L$: `Ln,r,w` and `CI,r` of H.5 i), or `None`. |
| `bare_rating` | The ISO 717-2 rating of the measured bare floor, `Ln,0,w` and `CI,0` of H.5 i), or `None`. |

### LabFloorCoveringImprovementResult.designation

*property*

`"ΔLw"` on the heavyweight floor, `"ΔLt,n,w"` on floor No n (H.1).

### LabFloorCoveringImprovementResult.octave_bands()

```python
LabFloorCoveringImprovementResult.octave_bands() -> tuple[np.ndarray, np.ndarray]
```

`(octave centres in Hz, ΔLoct in dB)` by Formula (H.2).

$\Delta L_\mathrm{oct} = -10 \log_{10}[(1/3) \sum 10^{-\Delta L_j/10}]$
over the three one-third-octave bands of each octave present.

### LabFloorCoveringImprovementResult.plot()

```python
LabFloorCoveringImprovementResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    rating_range: bool = False,
    **kwargs: Any,
) -> Axes
```

Plot the improvement `ΔL` per band with its weighted reduction.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `rating_range` | Mark the frequency range of the ISO 717-2 rating, 100 Hz to 3 150 Hz, with two dashed lines, as the diagram of the form of Figure H.4 does (its key 1). |
| `kwargs` | Forwarded to the `ΔL` curve. |

### LabFloorCoveringImprovementResult.report()

```python
LabFloorCoveringImprovementResult.report(
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    engine: str = 'reportlab',
    verbose: bool = False,
    language: str = 'en',
) -> str
```

Render the form of ISO 10140-1:2021 Figure H.4 to a one-page PDF.

"An example of the form for the expression of results ... is given in
Figure H.4. The user is allowed to copy this form" (H.6.3). The sheet
carries its fields: manufacturer and product, client, test room,
who mounted the specimen, the date, the description of the facility
and specimen, the type of reference floor, the mass per unit area,
the curing time, the air temperature and humidity in the source room
and the receiving room volume; the one-third-octave table of
$L_\mathrm{n,0}$ and $\Delta L$ beside the $\Delta L$
diagram with the frequency range of the ISO 717-2 rating marked; the
rating $\Delta L_\mathrm{w}$ (or $\Delta L_\mathrm{t,n,w}$)
and $C_{\mathrm{I}\Delta}$ with the two floor ratings of
H.5 i); and the statement that the result comes from an artificial
source on a specified reference floor. The form also asks for
$C_\mathrm{I,r,50\text{-}2500}$, which the reference floors of
ISO 717-2:2020 Table 4 cannot give below 100 Hz; the sheet says so in
its place.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Destination path of the PDF file. |
| `metadata` | Optional [`ReportMetadata`](/phonometry/reference/api/building/insulation/#reportmetadata); its `product` and `curing_time_h` fill the product identification and curing time rows, `source_temperature_c` and `source_relative_humidity_percent` (or the single `temperature_c` and `relative_humidity_percent`) the climate of the source room, and `requirement` a verdict on the weighted reduction (passing at or above it). |
| `engine` | Rendering back end; only `"reportlab"` is supported. |
| `verbose` | When `True`, the table also shows $L_\mathrm{n}$ with the covering. |
| `language` | `"en"` (default) or `"es"`. |

**Returns:** The written `path` as a `str`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `engine` or `language` is unknown, or the result carries no weighted reduction (the 16 bands 100 Hz to 3 150 Hz are missing). |
| ImportError | If reportlab or matplotlib is not installed. |

## LabLiningImprovementResult

```python
LabLiningImprovementResult(
    frequencies_hz: np.ndarray,
    r_without_db: np.ndarray,
    r_with_db: np.ndarray,
    delta_r_db: np.ndarray,
    basic_element: str | None,
    rating: ReductionImprovementRating | None,
    delta_rw_direct_db: int | None,
    delta_rw_c_direct_db: int | None,
    delta_rw_ctr_direct_db: int | None,
)
```

Improvement of airborne sound insulation by a lining (ISO 10140-1 Annex G).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | One-third-octave band centre frequencies, in Hz. |
| `r_without_db` | Sound reduction index of the basic element without the lining, `Rwithout`, in dB. |
| `r_with_db` | Sound reduction index with the lining, `Rwith`, in dB. |
| `delta_r_db` | Sound reduction improvement index $\Delta R = R_\mathrm{with} - R_\mathrm{without}$, in dB (G.1). |
| `basic_element` | The standard basic element the lining was measured on (`"heavy_wall"`, `"heavy_floor"`, `"lightweight_wall"`), or `None` for another basic element. |
| `rating` | The ISO 717-1:2020 Annex D rating on the reference curve of that element, or `None` for another basic element or a spectrum without the 16 rating bands 100 Hz to 3 150 Hz. |
| `delta_rw_direct_db` | `ΔRw,direct = Rw,with - Rw,without` (ISO 717-1:2020 Formula (D.2)), in dB, or `None` without the 16 rating bands. |
| `delta_rw_c_direct_db` | `Δ(Rw + C)direct`, in dB, or `None`. |
| `delta_rw_ctr_direct_db` | `Δ(Rw + Ctr)direct`, in dB, or `None`. |

### LabLiningImprovementResult.octave_bands()

```python
LabLiningImprovementResult.octave_bands() -> tuple[np.ndarray, np.ndarray]
```

`(octave centres in Hz, ΔRoct in dB)` (ISO 717-1:2020 Formula (D.1)).

$\Delta R_\mathrm{oct} = -10 \log_{10}[(1/3) \sum 10^{-\Delta R_j/10}]$
over the three one-third-octave bands of each octave, for every octave
whose three bands are present.

### LabLiningImprovementResult.plot()

```python
LabLiningImprovementResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the improvement `ΔR` per band with its single numbers.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## LiningCuringCheck

```python
LiningCuringCheck(
    curing_time_days: float,
    time_lag_days: float,
    required_curing_days: float,
)
```

Whether the basic element was stable across the two measurements (G.4).

The verdicts are read from the three times and the third G.4 prints, so
they are not fields: a check cannot be built to pass times the clause
fails.

**Attributes**

| Name | Description |
| :--- | :--- |
| `curing_time_days` | Time from the end of construction of the basic element to the first sound reduction measurement, in days. |
| `time_lag_days` | Time between the measurement without and the measurement with the lining, in days. |
| `required_curing_days` | The curing period that settles the element, 14 days unless the product specification sets another. |

### LiningCuringCheck.cured

*property*

Whether the curing time reaches `required_curing_days`.

Inclusive, and compared with a relative slack so that a time on the
bound is not failed by the binary rounding of the product.

### LiningCuringCheck.earliest_start_days

*property*

The curing time at which the lag condition is first met, in days.

Three times the time lag: the G.4 example reads it the other way
round, two measurements carried out within 1 d "can be started not
less than 3 d after the end of construction".

### LiningCuringCheck.lag_within_third

*property*

Whether the time lag is at most a third of the curing time, the alternative G.4 allows.

Inclusive, with the same slack: the printed 1 d and 3 d, or 2,1 d and
6,3 d, are on the bound.

### LiningCuringCheck.passes

*property*

Whether either condition holds.

### LiningCuringCheck.plot()

```python
LiningCuringCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the admissible curing time and time lag with this measurement.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.
