---
title: "environment.propagation.barrier_in_situ"
description: "What a barrier by the road is worth, measured (ISO 10847:1997)."
sidebar:
  label: "barrier_in_situ"
---

What a barrier by the road is worth, measured (ISO 10847:1997).

[`phonometry.environment.propagation.ground_barriers`](/phonometry/reference/api/environment/ground-barriers/) predicts what a
barrier will do from its geometry. This is the measurement, and its scope
paragraph is worth reading before the equations:

    It does not make it possible to compare insertion loss values of an
    equivalent barrier on a different site.

An insertion loss measured here belongs to that barrier, on that site, under
those meteorological conditions. What it may be used for is comparing
different barriers on the **same** site by the direct method, and what it is
not for is a product specification. The intrinsic quantities, the sound
reduction index and the absorption coefficient, are outside the scope
altogether.

Two methods, one subtraction
----------------------------

The quantity is the level at a receiver position before the barrier existed
less the level after, with everything else unchanged. Nothing else is
unchanged, of course, so the standard puts a second microphone at a
**reference position** where the barrier does not reach, and normalises by
what it heard:

$$
D_{IL} = \left(L_{\text{ref},A} - L_{\text{ref},B}\right) - \left(L_{r,A} - L_{r,B}\right)
$$

That is the **direct method**, 8.2.1, and it needs a barrier that has not been
built yet or can be taken down. Where it cannot, the **indirect method** of
8.2.2 measures the "before" pair at a substitute site judged equivalent, and
adds a correction for the kind of receiver position: 0 dB in a hemi free
field, 6 dB against a facade, which is the pressure doubling at a large hard
surface.

The algebra of the two is the same whenever the receiver is of the same kind
in both campaigns, which is what the NOTE to 8.2.2 recommends, and
[`measured_insertion_loss_indirect`](/phonometry/reference/api/environment/barrier-in-situ/#measured_insertion_loss_indirect) reduces to
[`measured_insertion_loss_direct`](/phonometry/reference/api/environment/barrier-in-situ/#measured_insertion_loss_direct) exactly there.

What the standard will not let you correct
------------------------------------------

Three times over. 6.3.2: "no attempt shall be made to adjust measured sound
pressure levels based on the temperature data". 6.3.3: the same for humidity.
The remedy for both is equivalence rather than arithmetic, and the clauses
say what equivalence means: the same wind class and vector components within
2 m/s, average temperatures within 10 °C, the same cloud cover class, and no
measurement at all above 5 m/s of wind.

The background is the one correction it does allow, from a **stepped table**
of two rows, and the table is not the one ISO 11820 prints and not the formula
ISO 11821 prints. Three standards on the same subject, three different rules;
they are three separate implementations here and share nothing.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## barrier_background_correction_db

```python
barrier_background_correction_db(
    level_difference_db: ArrayLike,
) -> NDArray[np.float64]
```

The background correction of Table 3, in decibels to add.

The table has two rows and no formula: 2 dB comes off at a margin of 4 or
5 dB, 1 dB at 6, 7, 8 or 9, and nothing at 10 or more, which is the margin
6.4 asks for in the first place. Under 4 dB "the measurement results are
not valid", and that is a refusal.

The sign is the trap. This column reads "correction to be **made to** the
measured sound pressure level", so its values are printed negative and are
**added**; Table 1 of ISO 11820 reads "correction to be **subtracted**"
and prints the same physical thing positive. The two tables also disagree
numerically at a margin of 9 dB, where ISO 11820 takes off 0,5 dB and this
one takes off 1. They are two tables and they stay two tables.

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_difference_db` | The difference between the level measured with the source and the level without it, in decibels. |

**Returns:** The correction to add, in decibels, which is zero or negative.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a margin under [`ISO10847_MINIMUM_BACKGROUND_MARGIN_DB`](/phonometry/reference/api/environment/barrier-in-situ/#iso10847_minimum_background_margin_db), which 6.4 calls invalid. |

## BarrierInSituWarning

The measurement is outside a condition ISO 10847 states.

## CLOSE_SOURCE_DISTANCE_M

*Constant* (`float`).

```python
CLOSE_SOURCE_DISTANCE_M = 15.0
```

## CLOUD_COVER_CLASSES

*Constant* (`dict`).

```python
CLOUD_COVER_CLASSES = {1: 'heavily overcast day or night, 80 % cloud cover or more for 100 % of the measurement time', 2: 'moderately overcast day or night, 50 % to 80 % cloud cover for at least 80 % of the measurement time', 3: 'lightly overcast or sunny day or night, either continuous sun or less than 50 % cloud cover for at least 80 % of the measurement time', 4: 'clear night'}
```

## EQUIVALENT_SECTOR_DEG

*Constant* (`float`).

```python
EQUIVALENT_SECTOR_DEG = 60.0
```

## EQUIVALENT_SURROUNDINGS_RADIUS_M

*Constant* (`float`).

```python
EQUIVALENT_SURROUNDINGS_RADIUS_M = 30.0
```

## HEMI_FREE_FIELD_DISTANCE_FACTOR

*Constant* (`float`).

```python
HEMI_FREE_FIELD_DISTANCE_FACTOR = 2.0
```

## HEMI_FREE_FIELD_DISTANCE_M

*Constant* (`float`).

```python
HEMI_FREE_FIELD_DISTANCE_M = 30.0
```

## hemi_free_field_distance_m

```python
hemi_free_field_distance_m(barrier_to_receiver_m: float) -> float
```

How far a receiver stands from a reflecting surface, 8.1.2 a).

$\min(30\ \text{m}, 2 d)$ with $d$ the distance from the
barrier to the receiver: the clause says 30 m "or twice the
barrier-receiver distance, **whichever is shorter**", so a receiver close
behind the barrier needs less clearance rather than more. The two rules
cross at 15 m.

**Parameters**

| Name | Description |
| :--- | :--- |
| `barrier_to_receiver_m` | $d$, in metres. |

**Returns:** The least distance to any vertical reflecting surface, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive distance. |

## is_short_distance

```python
is_short_distance(
    *,
    source_height_m: float,
    receiver_height_m: float,
    barrier_height_m: float,
    source_to_barrier_m: float,
    barrier_to_receiver_m: float,
) -> tuple[bool, bool]
```

Whether the geometry counts as a short distance, 6.3.1.

The clause prints one condition for the "before" campaign and two for the
"after" one, all against the same ratio of 0,1:

$$
\frac{H_s + H_R}{d_1 + d_2} > 0,1, \qquad \frac{H_s + H}{d_1} > 0,1, \qquad \frac{H + H_R}{d_2} > 0,1
$$

The "after" pair must both hold. What hangs on the answer is Table 1: the
upwind class exists only over short distances, so a long-distance
measurement may be made downwind or calm and not into the wind at all.

The inequalities are strict, so a ratio of exactly 0,1 is not a short
distance.

**Parameters**

| Name | Description |
| :--- | :--- |
| `source_height_m` | $H_s$, in metres. |
| `receiver_height_m` | $H_R$, in metres. |
| `barrier_height_m` | $H$, in metres. |
| `source_to_barrier_m` | $d_1$, in metres. |
| `barrier_to_receiver_m` | $d_2$, in metres. |

**Returns:** Whether the "before" and the "after" geometry each count as a short distance.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive height or distance. |

## ISO10847_BACKGROUND_CORRECTIONS_DB

*Constant* (`dict`).

```python
ISO10847_BACKGROUND_CORRECTIONS_DB = {4: -2.0, 5: -2.0, 6: -1.0, 7: -1.0, 8: -1.0, 9: -1.0}
```

## ISO10847_MINIMUM_BACKGROUND_MARGIN_DB

*Constant* (`float`).

```python
ISO10847_MINIMUM_BACKGROUND_MARGIN_DB = 4.0
```

## ISO10847_OCTAVE_BAND_EXTENDED_RANGE_HZ

*Constant* (`tuple`).

```python
ISO10847_OCTAVE_BAND_EXTENDED_RANGE_HZ = (63.0, 8000.0)
```

## ISO10847_OCTAVE_BAND_RANGE_HZ

*Constant* (`tuple`).

```python
ISO10847_OCTAVE_BAND_RANGE_HZ = (63.0, 4000.0)
```

## ISO10847_PREFERRED_BACKGROUND_MARGIN_DB

*Constant* (`float`).

```python
ISO10847_PREFERRED_BACKGROUND_MARGIN_DB = 10.0
```

## ISO10847_THIRD_OCTAVE_BAND_EXTENDED_RANGE_HZ

*Constant* (`tuple`).

```python
ISO10847_THIRD_OCTAVE_BAND_EXTENDED_RANGE_HZ = (50.0, 10000.0)
```

## ISO10847_THIRD_OCTAVE_BAND_RANGE_HZ

*Constant* (`tuple`).

```python
ISO10847_THIRD_OCTAVE_BAND_RANGE_HZ = (50.0, 5000.0)
```

## LINE_SOURCE_DIVERGENCE_DB

*Constant* (`float`).

```python
LINE_SOURCE_DIVERGENCE_DB = 3.0
```

## LONG_DISTANCE_M

*Constant* (`float`).

```python
LONG_DISTANCE_M = 250.0
```

## MAXIMUM_WIND_SPEED_M_S

*Constant* (`float`).

```python
MAXIMUM_WIND_SPEED_M_S = 5.0
```

## measured_insertion_loss_direct

```python
measured_insertion_loss_direct(
    reference_before_db: ArrayLike,
    reference_after_db: ArrayLike,
    receiver_before_db: ArrayLike,
    receiver_after_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
) -> MeasuredBarrierInsertionLoss
```

The insertion loss by the direct method, 8.2.1.

$$
D_{IL} = \left(L_{\text{ref},A} - L_{\text{ref},B}\right) - \left(L_{r,A} - L_{r,B}\right)
$$

The reference term is the source normalisation: whatever the source did
differently between the two campaigns, the reference microphone heard it
too, and subtracting it leaves the barrier. A uniform change of source
output therefore leaves the answer alone, which is the property the whole
arrangement exists for.

The method holds only where the barrier had not been built yet or could be
taken down, and 4.1 adds the condition that makes the subtraction mean
anything: **the same reference and receiver positions in both campaigns**.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_before_db` | $L_{\text{ref},B}$ per band, in decibels. |
| `reference_after_db` | $L_{\text{ref},A}$ per band, in decibels. |
| `receiver_before_db` | $L_{r,B}$ per band, in decibels. |
| `receiver_after_db` | $L_{r,A}$ per band, in decibels. |
| `frequencies` | Nominal band centres, in hertz. |

**Returns:** The insertion loss, as a [`MeasuredBarrierInsertionLoss`](/phonometry/reference/api/environment/barrier-in-situ/#measuredbarrierinsertionloss).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For levels that do not match band for band, or a band centre that is not strictly positive. |

## measured_insertion_loss_indirect

```python
measured_insertion_loss_indirect(
    reference_before_db: ArrayLike,
    reference_after_db: ArrayLike,
    receiver_before_db: ArrayLike,
    receiver_after_db: ArrayLike,
    *,
    frequencies: ArrayLike | None = None,
    receiver_type_before: ReceiverType = 'hemi_free_field',
    receiver_type_after: ReceiverType = 'hemi_free_field',
) -> MeasuredBarrierInsertionLoss
```

The insertion loss by the indirect method, 8.2.2.

$$
\Delta L_B = L_{\text{ref},B} - \left(L_{r,B} - C_r\right), \qquad \Delta L_A = L_{\text{ref},A} - \left(L_{r,A} - C'_r\right), \qquad D'_{IL} = \Delta L_A - \Delta L_B
$$

The "before" pair comes from a substitute site judged equivalent in
terrain, ground and source, which is what makes this an estimate rather
than a determination: 8.2.2 says so itself.

$C_r$ and $C'_r$ correct for the kind of receiver position:
0 dB in a hemi free field, 6 dB for a microphone against a facade, where
the pressure doubles. The clause attaches the unprimed symbol to the
"before" equation and the primed one to the "after", and then defines the
two by receiver type rather than by campaign, which taken literally would
force one type on each campaign. The NOTE settles it, by preferring
receiver positions "where corrections $C_r$ and $C'_r$ are
essentially the same", so the type is asked for once per campaign here
(see the errata).

Where the two types agree, the correction cancels and this returns exactly
what [`measured_insertion_loss_direct`](/phonometry/reference/api/environment/barrier-in-situ/#measured_insertion_loss_direct) returns on the same four
levels. Where they differ, the answer moves by 6 dB, which is why the NOTE
exists.

**Parameters**

| Name | Description |
| :--- | :--- |
| `reference_before_db` | $L_{\text{ref},B}$ per band, at the substitute site, in decibels. |
| `reference_after_db` | $L_{\text{ref},A}$ per band, in decibels. |
| `receiver_before_db` | $L_{r,B}$ per band, at the substitute site, in decibels. |
| `receiver_after_db` | $L_{r,A}$ per band, in decibels. |
| `frequencies` | Nominal band centres, in hertz. |
| `receiver_type_before` | `"hemi_free_field"` (default) or `"reflecting_surface"`, for the substitute site. |
| `receiver_type_after` | The same for the barrier site. |

**Returns:** The insertion loss, as a [`MeasuredBarrierInsertionLoss`](/phonometry/reference/api/environment/barrier-in-situ/#measuredbarrierinsertionloss).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For levels that do not match band for band, a band centre that is not strictly positive, or an unknown receiver type. |

## MeasuredBarrierInsertionLoss

```python
MeasuredBarrierInsertionLoss(
    frequencies: NDArray[np.float64] | None,
    reference_before_db: NDArray[np.float64],
    reference_after_db: NDArray[np.float64],
    receiver_before_db: NDArray[np.float64],
    receiver_after_db: NDArray[np.float64],
    insertion_loss_db: NDArray[np.float64],
    method: str,
    receiver_correction_before_db: float,
    receiver_correction_after_db: float,
)
```

The insertion loss of a barrier as measured, ISO 10847 clause 8.2.

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies` | Nominal band centres, in hertz, or `None` where the measurement is an A-weighted level. |
| `reference_before_db` | $L_{\text{ref},B}$ per band. |
| `reference_after_db` | $L_{\text{ref},A}$ per band. |
| `receiver_before_db` | $L_{r,B}$ per band. |
| `receiver_after_db` | $L_{r,A}$ per band. |
| `insertion_loss_db` | $D_{IL}$ or $D'_{IL}$ per band, in decibels. |
| `method` | `"direct"` or `"indirect"`. |
| `receiver_correction_before_db` | $C_r$, in decibels, zero for the direct method. |
| `receiver_correction_after_db` | $C'_r$, in decibels, zero for the direct method. |

### MeasuredBarrierInsertionLoss.plot()

```python
MeasuredBarrierInsertionLoss.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the four levels and the insertion loss they give.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.environment.plot_barrier_in_situ`. |

**Returns:** The `Axes`.

### MeasuredBarrierInsertionLoss.rounded()

```python
MeasuredBarrierInsertionLoss.rounded() -> NDArray[np.int_]
```

The values as clause 10 c) reports them, to the nearest decibel.

### MeasuredBarrierInsertionLoss.symbol

*property*

The symbol clause 8.2 reports this as, `"D_IL"` or `"D'_IL"`.

## MINIMUM_RECEIVER_HEIGHT_M

*Constant* (`float`).

```python
MINIMUM_RECEIVER_HEIGHT_M = 1.2
```

## MINIMUM_REPETITIONS

*Constant* (`int`).

```python
MINIMUM_REPETITIONS = 3
```

## POINT_SOURCE_DIVERGENCE_DB

*Constant* (`float`).

```python
POINT_SOURCE_DIVERGENCE_DB = 6.0
```

## RECEIVER_CORRECTIONS_DB

*Constant* (`dict`).

```python
RECEIVER_CORRECTIONS_DB = {'hemi_free_field': 0.0, 'reflecting_surface': 6.0}
```

## REFERENCE_ELEVATION_INCREMENT_DEG

*Constant* (`float`).

```python
REFERENCE_ELEVATION_INCREMENT_DEG = 10.0
```

## REFERENCE_MICROPHONE_CLEARANCE_M

*Constant* (`float`).

```python
REFERENCE_MICROPHONE_CLEARANCE_M = 1.5
```

## reference_microphone_height_m

```python
reference_microphone_height_m(
    barrier_height_m: float,
    *,
    source_to_barrier_m: float | None = None,
) -> float
```

How high the reference microphone stands, 7.2.2.

At least [`REFERENCE_MICROPHONE_CLEARANCE_M`](/phonometry/reference/api/environment/barrier-in-situ/#reference_microphone_clearance_m) above the top edge of
the barrier, on a vertical plane through it, so that what it hears is the
source and not the barrier. For a barrier whose top is not a straight
edge, a berm or a cupped profile, the clearance is measured from its
highest point. The clause words the clearance with "shall" (printed folio
9, PDF page 13), and no geometry takes the microphone under it.

The NOTE adds a preference for a source that stands close. Where the near
end of the source region is under [`CLOSE_SOURCE_DISTANCE_M`](/phonometry/reference/api/environment/barrier-in-situ/#close_source_distance_m) from
the barrier, the microphone "may be raised as high as possible" until the
elevation angle from that end exceeds the angle to the barrier top by
[`REFERENCE_ELEVATION_INCREMENT_DEG`](/phonometry/reference/api/environment/barrier-in-situ/#reference_elevation_increment_deg):

$$
h = \max\left(H + 1{,}5\ \mathrm{m},\; d \tan\left(\arctan\frac{H}{d} + 10^\circ\right)\right)
$$

The NOTE only ever raises the microphone, so the height is the higher of
the two. Which one governs depends on the geometry: a 4 m barrier 10 m
from the source takes the angle, 6,20 m against 5,5 m, while a 3 m barrier
5 m from the source takes the clearance, because its 10 degrees are
reached at 4,34 m and the clause asks for 4,5 m. The angle form is the
NOTE's own words; the height it implies is derived here rather than
printed.

Once the barrier top stands 80 degrees or more above the near end of the
source region, no height reaches the increment at all, and the tangent
would turn negative. The microphone then keeps the clearance and a
[`BarrierInSituWarning`](/phonometry/reference/api/environment/barrier-in-situ/#barrierinsituwarning) says that the NOTE could not be followed.
That is how this module treats a NOTE, as with the one to 8.2.2: a
preference it cannot meet is reported, and the clause it hangs from is
enforced.

**Parameters**

| Name | Description |
| :--- | :--- |
| `barrier_height_m` | $H$, the barrier height above the ground at the microphone, in metres. |
| `source_to_barrier_m` | $d$, the distance from the near end of the source region to the barrier, in metres. Omit it for the plain clearance rule. |

**Returns:** The microphone height above the ground, in metres.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive height or distance. |

## SHORT_DISTANCE_RATIO

*Constant* (`float`).

```python
SHORT_DISTANCE_RATIO = 0.1
```

## TEMPERATURE_TOLERANCE_C

*Constant* (`float`).

```python
TEMPERATURE_TOLERANCE_C = 10.0
```

## wind_class

```python
wind_class(
    vector_component_m_s: float,
    *,
    short_distance: bool = False,
) -> str | None
```

The wind class of Table 1, from the vector component of the velocity.

The component is the projection of the average wind velocity on the line
from the source to the receiver, in metres per second: positive downwind,
negative upwind. Over all distances the table has a downwind class and a
calm one; over short distances it adds an upwind class, whose interval is
printed "+ 1 to - 5" and read here as -1 to -5 (see the errata).

The calm class carries a footnote of its own over all distances: it counts
"only with the case of temperature inversion".

Above [`MAXIMUM_WIND_SPEED_M_S`](/phonometry/reference/api/environment/barrier-in-situ/#maximum_wind_speed_m_s) in absolute value no measurement is
made at all, which is a refusal rather than a class.

**Parameters**

| Name | Description |
| :--- | :--- |
| `vector_component_m_s` | The vector component, in metres per second. |
| `short_distance` | Whether the geometry is a short distance in the sense of [`is_short_distance`](/phonometry/reference/api/environment/barrier-in-situ/#is_short_distance). |

**Returns:** The class name, or `None` where the component falls in no class the table prints, which over long distances is any upwind component.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a component that is not finite, or past [`MAXIMUM_WIND_SPEED_M_S`](/phonometry/reference/api/environment/barrier-in-situ/#maximum_wind_speed_m_s) in absolute value. |

## WIND_CLASSES

*Constant* (`dict`).

```python
WIND_CLASSES = {'all': {'downwind': (1.0, 5.0), 'calm': (-1.0, 1.0)}, 'short': {'downwind': (1.0, 5.0), 'calm': (-1.0, 1.0), 'upwind': (-5.0, -1.0)}}
```

## WIND_VECTOR_TOLERANCE_M_S

*Constant* (`float`).

```python
WIND_VECTOR_TOLERANCE_M_S = 2.0
```
