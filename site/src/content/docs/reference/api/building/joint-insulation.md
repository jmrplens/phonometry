---
title: "building.measurement.joint_insulation"
description: "Sound reduction index of joints filled with fillers or seals (ISO 10140-1:2021 Annex J)."
sidebar:
  label: "joint_insulation"
---

Sound reduction index of joints filled with fillers or seals (ISO 10140-1:2021 Annex J).

A joint is a line, not an area: a slit with or without a filler, a foam or
sealing tape, a gasket on the rebate of a door or window. Annex J therefore
normalizes the sound it lets through to a **metre** of joint rather than to a
square metre of element. With the joint mounted in a highly insulating
element, the level difference measured to ISO 10140-2 gives the sound
reduction index of joints per metre,

$$
R_\mathrm{s} = L_1 - L_2 + 10 \lg \frac{S_\mathrm{n} l}{A l_\mathrm{n}} \tag{J.1}
$$

with $S_\mathrm{n} = 1$ m², $l_\mathrm{n} = 1$ m, the joint length
$l$ and the equivalent absorption area $A$ of the receiving room
([`joint_sound_reduction_index`](/phonometry/reference/api/building/joint-insulation/#joint_sound_reduction_index)).

**Flanking through the test element.** The element the joint sits in is part
of every measurement, so J.1 asks for the maximum the arrangement can show,
$R_\mathrm{s,max}$, measured with the joint sealed on both sides. Unless
it lies 10 dB or more above the measured $R_\mathrm{s}'$, the result is
corrected by the rules of ISO 10140-2:2021 A.3 ([`lab_joint_insulation`](/phonometry/reference/api/building/joint-insulation/#lab_joint_insulation)):

* a difference of 6 dB up to 10 dB: Formula (J.2),
  $R_\mathrm{s} = -10 \lg(10^{-R_\mathrm{s}'/10} - 10^{-R_\mathrm{s,max}/10})$;
* less than 6 dB: a fixed correction of 1,3 dB, which is what Formula (J.2)
  gives at 6 dB, and the value is a minimum;
* $R_\mathrm{s}'$ above $R_\mathrm{s,max} - 3$ dB: the lower limit
  of $R_\mathrm{s}$ may be set to $R_\mathrm{s,max}$ itself,
  presented in brackets as a minimum value, e.g. $(R_\mathrm{s} \ge 50{,}4$ dB).

**Single numbers.** $R_\mathrm{s,w}$ ($C$; $C_\mathrm{tr}$)
of ISO 717-1:2020 on the 16 bands 100 Hz to 3 150 Hz, with
$C_{100\text{-}5000}$ and $C_\mathrm{tr,100\text{-}5000}$ when the
bands reach 5 000 Hz, as the form of Figure J.7 prints them. Where a band is
above $R_\mathrm{s,max} - 3$ dB, J.1 rates the curve a second time with
those indicative bands taken as infinitely high; a difference of more than
1 dB between the two puts the single numbers in brackets too.

**The arrangement.** J.2.1 asks for a joint longer than 1 m and no wider
than 50 mm, J.2.2 for at least 5,0 m of a gap between the parts of a window or
door ([`check_joint_test_element`](/phonometry/reference/api/building/joint-insulation/#check_joint_test_element)), whose width is read at four positions
or more that may not differ by more than 0,3 mm ([`check_gap_width`](/phonometry/reference/api/building/joint-insulation/#check_gap_width)). A
variable slit is measured at its nominal gap width $b_\mathrm{n}$ (5 mm
when the manufacturer gives none), at the minimum width under a force of
normally 100 N/m, and at $b_\mathrm{n} + 3$ mm (J.4,
[`check_joint_gap_series`](/phonometry/reference/api/building/joint-insulation/#check_joint_gap_series)), and reported as single numbers against the
gap width ([`joint_gap_series`](/phonometry/reference/api/building/joint-insulation/#joint_gap_series), Figures J.8 and J.9).

Citations are to ISO 10140-1:2021 (third edition) Annex J and, for the
flanking rules it calls in, to ISO 10140-2:2021 A.3.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## check_gap_width

```python
check_gap_width(readings_mm: ArrayLike) -> GapWidthCheck
```

Check the gap width read along the joint and average it (J.2.2).

"Determine the gap width at a minimum of four positions, evenly
distributed over the total length of sealing. The results shall not
deviate by more than 0,3 mm, otherwise readjust the mounting. The average
value is denoted as gap width, b." The deviation is read between the
readings, the largest minus the smallest, which is the stricter of the
two ways the sentence can be read: a deviation of each reading from the
average would allow twice the spread. Whether the positions are evenly
distributed is not judged, since only the widths are given.

**Parameters**

| Name | Description |
| :--- | :--- |
| `readings_mm` | The gap widths read, in mm, in any order. |

**Returns:** A [`GapWidthCheck`](/phonometry/reference/api/building/joint-insulation/#gapwidthcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If there is no reading, or a reading is negative or not finite. |

## check_joint_gap_series

```python
check_joint_gap_series(series: JointGapSeries) -> JointGapSeriesCheck
```

Check that a variable slit was measured at the three gap widths of J.4.

"For variable slits, as with openable windows or doors, the test shall be
repeated for the following gap width": a) the nominal gap width
$b_\mathrm{n}$, b) the minimal gap width $b_\mathrm{min}$ at
maximal pressure, and c) $b_\mathrm{n} + 3$, "a gap width 3 mm more
than nominal". Each has to be among the widths of the series.

J.4 gives no tolerance on how close a measured width must come. The gap
width of a result is the average of readings that J.2.2 lets spread over
0,3 mm, so a measured width within 0,3 mm of a required one counts as
that width. A series that does not name $b_\mathrm{min}$ fails
J.4 b), because nothing then shows which width it was; pass
`minimum_gap_mm` to [`joint_gap_series`](/phonometry/reference/api/building/joint-insulation/#joint_gap_series).

**Parameters**

| Name | Description |
| :--- | :--- |
| `series` | The [`JointGapSeries`](/phonometry/reference/api/building/joint-insulation/#jointgapseries) of the slit. |

**Returns:** A [`JointGapSeriesCheck`](/phonometry/reference/api/building/joint-insulation/#jointgapseriescheck).

## check_joint_test_element

```python
check_joint_test_element(
    joint_length_m: float,
    joint_width_mm: float,
    *,
    window_or_door_gap: bool = False,
) -> JointTestElementCheck
```

Check the length and width of a joint before it is tested (J.2.1, J.2.2).

J.2.1: "The length of the joint shall be greater than 1 m and the width of
the joint shall be no greater than 50 mm." J.2.2 adds, for gaps between
the parts of windows and doors, that the gap under test "shall have a
length of at least 5,0 m with a uniform cross-section", which may be the
sum of several gaps. The 1 m bound is exclusive, the others inclusive.

The uniform cross-section, the shape of Figure J.1 and the design of the
environment around the joint (J.2.1 "can only give advice") carry no
number and are not judged here.

**Parameters**

| Name | Description |
| :--- | :--- |
| `joint_length_m` | Total length of the joint under test, in m. |
| `joint_width_mm` | Width of the joint, in mm (the gap width `b`). |
| `window_or_door_gap` | `True` for a gap between the parts of a window or door (J.2.2). |

**Returns:** A [`JointTestElementCheck`](/phonometry/reference/api/building/joint-insulation/#jointtestelementcheck).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the length is not positive or the width is negative or not finite. |

## GapWidthCheck

```python
GapWidthCheck(
    readings_mm: tuple[float, ...],
    gap_width_mm: float,
    spread_mm: float,
    enough_positions: bool,
    uniform: bool,
    passes: bool,
)
```

The gap width read along the joint, and whether the readings agree (J.2.2).

**Attributes**

| Name | Description |
| :--- | :--- |
| `readings_mm` | The gap widths read along the joint, in mm. |
| `gap_width_mm` | Their average, the gap width `b`, in mm. |
| `spread_mm` | The largest difference between two readings, in mm. |
| `enough_positions` | Whether there are at least four readings. |
| `uniform` | Whether no two readings differ by more than 0,3 mm. |
| `passes` | Whether both hold; otherwise J.2.2 says to readjust the mounting. |

### GapWidthCheck.plot()

```python
GapWidthCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the readings with their average and the 0,3 mm band.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## joint_gap_series

```python
joint_gap_series(
    gap_widths_mm: ArrayLike,
    results: tuple[LabJointInsulationResult, ...] | list[LabJointInsulationResult],
    *,
    nominal_gap_mm: float = 5.0,
    minimum_gap_mm: float | None = None,
) -> JointGapSeries
```

Collect the results of a variable slit at several gap widths (J.4, J.5).

"For variable slits, as with openable windows or doors, the test shall be
repeated" at the nominal gap width $b_\mathrm{n}$ given by the
manufacturer ("if unknown $b_\mathrm{n}$ = 5 mm is to be taken"),
at the minimal gap width $b_\mathrm{min}$ under the maximal
pressure (normally a force of 100 N per metre of sealing) and at
$b_\mathrm{n} + 3$ mm (J.4); NOTE 1 suggests steps of 1 mm from
maximum compression until a gap is present. The report gives each of
$R_\mathrm{s,w}$, $R_\mathrm{s,w} + C$ and
$R_\mathrm{s,w} + C_\mathrm{tr}$ as a function of the gap width with
the nominal width marked (J.5.2 i)), and the results at
$b_\mathrm{n}$ and $b_\mathrm{n} + 3$ are the ones products are
compared by (J.5.2 h)). Any set of widths is collected;
[`check_joint_gap_series`](/phonometry/reference/api/building/joint-insulation/#check_joint_gap_series) judges whether the three of J.4 are among
them.

**Parameters**

| Name | Description |
| :--- | :--- |
| `gap_widths_mm` | The gap width `b` of each result, in mm (the average of [`check_gap_width`](/phonometry/reference/api/building/joint-insulation/#check_gap_width)). |
| `results` | The [`LabJointInsulationResult`](/phonometry/reference/api/building/joint-insulation/#labjointinsulationresult) at each width, each with its ISO 717-1 rating. |
| `nominal_gap_mm` | $b_\mathrm{n}$, in mm (default 5 mm). |
| `minimum_gap_mm` | $b_\mathrm{min}$, in mm, marked on the plot when given. |

**Returns:** A [`JointGapSeries`](/phonometry/reference/api/building/joint-insulation/#jointgapseries), sorted by gap width.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the widths and results disagree in number, two widths coincide, a width is negative, or a result carries no rating. |

## joint_sound_reduction_index

```python
joint_sound_reduction_index(
    l1_db: ArrayLike,
    l2_db: ArrayLike,
    absorption_m2: ArrayLike,
    *,
    joint_length_m: float,
) -> np.ndarray
```

Sound reduction index of joints per metre, Formula (J.1).

$$
R_\mathrm{s} = L_1 - L_2 + 10 \lg \frac{S_\mathrm{n} l}{A l_\mathrm{n}}
$$

with $S_\mathrm{n} = 1$ m² and $l_\mathrm{n} = 1$ m. A joint
twice as long lets twice the power through, so the index of a metre is
3 dB above the one a 2 m joint gives without the normalization.

The same formula, with the joint sealed on both sides, gives the maximum
of the test arrangement $R_\mathrm{s,max}$ that
[`lab_joint_insulation`](/phonometry/reference/api/building/joint-insulation/#lab_joint_insulation) corrects against (J.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `l1_db` | Energy average sound pressure level in the source room, in dB, one value per band, or a `(positions, bands)` array that is energy-averaged over the positions (ISO 10140-2). |
| `l2_db` | The same in the receiving room, in dB. |
| `absorption_m2` | Equivalent absorption area $A$ of the receiving room per band, in m². |
| `joint_length_m` | Length $l$ of the joint under test, in m. |

**Returns:** $R_\mathrm{s}$ per band, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the inputs disagree in band count, a level is not finite, an area is not positive, or the length is not positive. |

## JointGapSeries

```python
JointGapSeries(
    gap_widths_mm: np.ndarray,
    results: tuple[LabJointInsulationResult, ...],
    nominal_gap_mm: float,
    minimum_gap_mm: float | None,
    r_s_w_db: np.ndarray,
    r_s_w_c_db: np.ndarray,
    r_s_w_ctr_db: np.ndarray,
)
```

Single numbers of a variable slit against its gap width (J.4, J.5.2 h), i)).

**Attributes**

| Name | Description |
| :--- | :--- |
| `gap_widths_mm` | The gap widths measured, ascending, in mm. |
| `results` | The [`LabJointInsulationResult`](/phonometry/reference/api/building/joint-insulation/#labjointinsulationresult) at each width. |
| `nominal_gap_mm` | The nominal gap width $b_\mathrm{n}$, in mm. |
| `minimum_gap_mm` | The minimal gap width $b_\mathrm{min}$ at the maximal pressure, in mm, or `None` when not given. |
| `r_s_w_db` | $R_\mathrm{s,w}$ at each width, in dB. |
| `r_s_w_c_db` | $R_\mathrm{s,w} + C$ at each width, in dB. |
| `r_s_w_ctr_db` | $R_\mathrm{s,Atr} = R_\mathrm{s,w} + C_\mathrm{tr}$ at each width, in dB. |

### JointGapSeries.at_gap()

```python
JointGapSeries.at_gap(
    gap_mm: float,
    quantity: Literal['r_s_w', 'r_s_w_c', 'r_s_w_ctr'] = 'r_s_w_ctr',
) -> float
```

The single number at a gap width, on the lines through the measurements.

Figure J.8 plots "measurement results (open circles) and
interpolations (lines plotted through measurement results)"; this
reads the straight line between the two widths either side.

**Parameters**

| Name | Description |
| :--- | :--- |
| `gap_mm` | The gap width, in mm, within the measured range. |
| `quantity` | `"r_s_w"`, `"r_s_w_c"` or `"r_s_w_ctr"` (default). |

**Returns:** The single number, in dB.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the width lies outside the measured widths. |

### JointGapSeries.plot()

```python
JointGapSeries.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    quantity: Literal['r_s_w', 'r_s_w_c', 'r_s_w_ctr'] = 'r_s_w_ctr',
    **kwargs: Any,
) -> Axes
```

Plot a single number against the gap width, as Figure J.8.

The measured widths as open circles on the line through them, with
$b_\mathrm{min}$, $b_\mathrm{n}$ and
$b_\mathrm{n} + 3$ marked. Requires matplotlib
(`pip install phonometry[plot]`); returns the
`Axes`.

### JointGapSeries.plot_octave_bands()

```python
JointGapSeries.plot_octave_bands(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot $R_\mathrm{s}$ in octave bands at every gap width, as Figure J.9.

Every result must hold whole octaves of one-third-octave bands.
Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

### JointGapSeries.single_number()

```python
JointGapSeries.single_number(
    quantity: Literal['r_s_w', 'r_s_w_c', 'r_s_w_ctr'] = 'r_s_w_ctr',
) -> np.ndarray
```

The single number at each width: `"r_s_w"`, `"r_s_w_c"` or `"r_s_w_ctr"`.

### JointGapSeries.working_range_mm

*property*

`(bn, bn + 3)`: the working range of Figure J.8, in mm.

The figure draws it as $\Delta b$ and its key names it
$\Delta b_\mathrm{n}$ (recorded in the errata registry); the plot
uses the symbol of the drawing. The 3 mm is the one J.4 c) measures
at; where J.5.2 h) lets "a gap range other than 3 mm" apply,
`at_gap` reads the single numbers at any other measured width.

## JointGapSeriesCheck

```python
JointGapSeriesCheck(
    gap_widths_mm: tuple[float, ...],
    nominal_gap_mm: float,
    minimum_gap_mm: float | None,
    nominal_measured: bool,
    minimum_measured: bool,
    working_range_measured: bool,
    passes: bool,
)
```

Whether a variable slit was measured at the three gap widths of J.4.

**Attributes**

| Name | Description |
| :--- | :--- |
| `gap_widths_mm` | The gap widths measured, ascending, in mm. |
| `nominal_gap_mm` | The nominal gap width $b_\mathrm{n}$, in mm. |
| `minimum_gap_mm` | The minimal gap width $b_\mathrm{min}$, in mm, or `None` when the series does not name it. |
| `nominal_measured` | Whether a measured width is $b_\mathrm{n}$ (J.4 a)). |
| `minimum_measured` | Whether a measured width is $b_\mathrm{min}$ (J.4 b)); `False` when the series names no $b_\mathrm{min}$, since nothing then shows it was measured. |
| `working_range_measured` | Whether a measured width is $b_\mathrm{n} + 3$ mm (J.4 c)). |
| `passes` | Whether all three were measured. |

### JointGapSeriesCheck.plot()

```python
JointGapSeriesCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the measured gap widths against the three widths J.4 asks for.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

### JointGapSeriesCheck.tolerance_mm

*property*

How far a measured width may lie from a required one, in mm (0,3 mm, J.2.2).

## JointOpenBandRating

```python
JointOpenBandRating(
    open_frequencies_hz: tuple[float, ...],
    r_s_w_db: int | None,
    c_db: int | None,
    ctr_db: int | None,
    c_100_5000_db: int | None,
    ctr_100_5000_db: int | None,
)
```

The single numbers with the indicative bands taken as infinitely high (J.1).

Where $R_\mathrm{s}'$ is above $R_\mathrm{s,max} - 3$ dB the
band says only that the joint is better than the arrangement can show.
J.1 rates the curve a second time with an infinitely high sound reduction
index in those bands: they then add no unfavourable deviation and no
transmitted energy. A term is `None` when it is unbounded, which happens
when every band it sums is indicative, or when the bands do not reach its
range.

**Attributes**

| Name | Description |
| :--- | :--- |
| `open_frequencies_hz` | The indicative bands, in Hz. |
| `r_s_w_db` | $R_\mathrm{s,w}$, in dB, or `None`. |
| `c_db` | $C$, in dB, or `None`. |
| `ctr_db` | $C_\mathrm{tr}$, in dB, or `None`. |
| `c_100_5000_db` | $C_{100\text{-}5000}$, in dB, or `None`. |
| `ctr_100_5000_db` | $C_\mathrm{tr,100\text{-}5000}$, in dB, or `None`. |

### JointOpenBandRating.plot()

```python
JointOpenBandRating.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the open-band single numbers beside the bands taken as open.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## JointTestElementCheck

```python
JointTestElementCheck(
    joint_length_m: float,
    joint_width_mm: float,
    window_or_door_gap: bool,
    length_ok: bool,
    width_ok: bool,
    passes: bool,
)
```

Whether a joint is long and narrow enough to be tested (J.2.1, J.2.2).

**Attributes**

| Name | Description |
| :--- | :--- |
| `joint_length_m` | Length of the joint, in m. |
| `joint_width_mm` | Width of the joint, in mm. |
| `window_or_door_gap` | Whether the joint is a gap between the parts of a window or door, which J.2.2 asks to be at least 5,0 m long. |
| `length_ok` | Whether the length is greater than 1 m and, for a window or door gap, at least 5,0 m. |
| `width_ok` | Whether the width is no greater than 50 mm. |
| `passes` | Whether both hold. |

### JointTestElementCheck.plot()

```python
JointTestElementCheck.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the length and width of the joint against their bounds.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

## lab_joint_insulation

```python
lab_joint_insulation(
    r_s_measured_db: ArrayLike,
    r_s_max_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    joint_length_m: float | None = None,
    limit_at_maximum: bool = True,
) -> LabJointInsulationResult
```

Sound reduction index of a joint, corrected for the test arrangement (J.1).

$R_\mathrm{s}'$ and $R_\mathrm{s,max}$ are both Formula (J.1)
([`joint_sound_reduction_index`](/phonometry/reference/api/building/joint-insulation/#joint_sound_reduction_index)): the first with the joint as it is
tested, the second with it sealed on both sides, "e.g. with elastic
sealant". Band by band, with the difference
$d = R_\mathrm{s,max} - R_\mathrm{s}'$:

* $d \ge 10$ dB: no correction, $R_\mathrm{s} = R_\mathrm{s}'$;
* $6 \le d < 10$ dB: Formula (J.2),
  $R_\mathrm{s} = -10 \lg(10^{-R_\mathrm{s}'/10} - 10^{-R_\mathrm{s,max}/10})$;
* $d < 6$ dB: $R_\mathrm{s} = R_\mathrm{s}' + 1{,}3$ dB, the
  correction Formula (J.2) gives at 6 dB, a minimum value
  (ISO 10140-2:2021 A.3);
* $d < 3$ dB, with `limit_at_maximum` (the default): the lower
  limit set to $R_\mathrm{s} = R_\mathrm{s,max}$, which J.1 allows
  ("may") and presents in brackets as a minimum value.

The last rule is exact rather than conservative: the arrangement passes
$\tau_\mathrm{s,max}$ alone and $\tau_\mathrm{s} + \tau_\mathrm{s,max}$ with the joint, so a measured index within 3 dB of
the maximum means $\tau_\mathrm{s} < \tau_\mathrm{s,max}$.

With the 16 bands 100 Hz to 3 150 Hz the result carries
$R_\mathrm{s,w}$ ($C$; $C_\mathrm{tr}$) of ISO 717-1, and
with the 18 bands to 5 000 Hz $C_{100\text{-}5000}$ and
$C_\mathrm{tr,100\text{-}5000}$, the evaluation of Figure J.7. Bands
with $d < 3$ dB are indicative: J.1 rates the curve again with them
taken as infinitely high, and a change of more than 1 dB puts the single
numbers in brackets ([`LabJointInsulationResult.bracketed`](/phonometry/reference/api/building/joint-insulation/#labjointinsulationresultbracketed)). The
indicative bands are read on $R_\mathrm{s}'$, the same condition as
the bracketed lower limit, whichever rule corrected them.

**Parameters**

| Name | Description |
| :--- | :--- |
| `r_s_measured_db` | $R_\mathrm{s}'$ per one-third-octave band, in dB. |
| `r_s_max_db` | $R_\mathrm{s,max}$ per band, in dB. |
| `frequencies_hz` | Band centre frequencies, in Hz. |
| `joint_length_m` | Length of the joint under test, in m, kept for the form of Figure J.7; `None` leaves that row empty. |
| `limit_at_maximum` | Set the bands within 3 dB of the maximum to $R_\mathrm{s,max}$ (default), or give them the 1,3 dB correction like the other bands below 6 dB. |

**Returns:** A [`LabJointInsulationResult`](/phonometry/reference/api/building/joint-insulation/#labjointinsulationresult).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If the three inputs disagree in length, a value is not finite, a frequency or the joint length is not positive. |

## LabJointInsulationResult

```python
LabJointInsulationResult(
    frequencies_hz: np.ndarray,
    r_s_measured_db: np.ndarray,
    r_s_max_db: np.ndarray,
    r_s_db: np.ndarray,
    regime: tuple[str, ...],
    joint_length_m: float | None,
    rating: WeightedRatingResult | None,
    c_100_5000_db: int | None,
    ctr_100_5000_db: int | None,
    max_rating: WeightedRatingResult | None,
    open_band_rating: JointOpenBandRating | None,
)
```

Sound reduction index of a joint per metre (ISO 10140-1:2021 Annex J).

**Attributes**

| Name | Description |
| :--- | :--- |
| `frequencies_hz` | One-third-octave band centre frequencies, in Hz. |
| `r_s_measured_db` | $R_\mathrm{s}'$, the index measured with the test element in the test opening, per band, in dB. |
| `r_s_max_db` | $R_\mathrm{s,max}$, the maximum of the test arrangement with the joint sealed on both sides, in dB. |
| `r_s_db` | $R_\mathrm{s}$, corrected for the flanking through the arrangement, in dB. In the `"limit"` and `"maximum"` bands it is a minimum value. |
| `regime` | How each band was corrected: `"uncorrected"` ($R_\mathrm{s,max}$ at least 10 dB above), `"corrected"` (Formula (J.2), 6 dB to 10 dB), `"limit"` (the fixed 1,3 dB below 6 dB) or `"maximum"` (above $R_\mathrm{s,max} - 3$ dB, set to $R_\mathrm{s,max}$). |
| `joint_length_m` | Length $l$ of the joint, in m, or `None` when not given; the form of Figure J.7 prints it as the test length. |
| `rating` | $R_\mathrm{s,w}$ ($C$; $C_\mathrm{tr}$) of ISO 717-1:2020, or `None` without the 16 bands 100 Hz to 3 150 Hz. |
| `c_100_5000_db` | $C_{100\text{-}5000}$, in dB, or `None` without the bands 100 Hz to 5 000 Hz. |
| `ctr_100_5000_db` | $C_\mathrm{tr,100\text{-}5000}$, in dB, or `None`. |
| `max_rating` | The ISO 717-1 rating of $R_\mathrm{s,max}$, the maximum sound insulation of the arrangement J.5.2 a) asks the report to state, or `None`. |
| `open_band_rating` | The single numbers with the indicative bands taken as infinitely high, or `None` when no band is indicative or there is no rating. |

### LabJointInsulationResult.bracketed

*property*

Whether the single numbers are presented in brackets (J.1).

They are when rating the indicative bands as infinitely high moves any
of $R_\mathrm{s,w}$, $R_\mathrm{s,w} + C$,
$R_\mathrm{s,w} + C_\mathrm{tr}$ or their enlarged-range sums
by more than 1 dB, or leaves one of them unbounded.

### LabJointInsulationResult.indicative

*property*

Bands where $R_\mathrm{s}' > R_\mathrm{s,max} - 3$ dB (J.1).

### LabJointInsulationResult.minimum_value

*property*

Bands whose $R_\mathrm{s}$ is a minimum value (`"limit"` or `"maximum"`).

### LabJointInsulationResult.octave_bands()

```python
LabJointInsulationResult.octave_bands() -> tuple[np.ndarray, np.ndarray]
```

`(octave centres in Hz, Rs,oct in dB)` from the three thirds of each octave.

$R_\mathrm{oct} = -10 \lg[(1/3) \sum 10^{-R_j/10}]$: the
transmitted power of the three thirds averaged, as Figure J.9 plots
a joint at several gap widths in octave bands.

### LabJointInsulationResult.plot()

```python
LabJointInsulationResult.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot $R_\mathrm{s}$ per band with the maximum of the arrangement.

The test curve with its minimum values marked, $R_\mathrm{s}'$
and $R_\mathrm{s,max}$, and the shifted ISO 717-1 reference
curve over the rating range, as the diagram of Figure J.7. Requires
matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

### LabJointInsulationResult.r_s_w_c_db

*property*

$R_\mathrm{s,w} + C$, in dB, or `None` without a rating.

### LabJointInsulationResult.r_s_w_ctr_db

*property*

$R_\mathrm{s,Atr} = R_\mathrm{s,w} + C_\mathrm{tr}$, in dB, or `None`.

### LabJointInsulationResult.r_s_w_db

*property*

$R_\mathrm{s,w}$, in dB, or `None` without a rating.

### LabJointInsulationResult.report()

```python
LabJointInsulationResult.report(
    path: str,
    *,
    metadata: ReportMetadata | None = None,
    engine: str = 'reportlab',
    verbose: bool = False,
    language: str = 'en',
) -> str
```

Render the form of Figure J.7 to a one-page PDF.

The header of the form (client, specimen, date, test length,
separation wall, test noise, room volumes, maximum joint sound
reduction index, mounting and climate), the table of
$R_\mathrm{s}$ from 100 Hz to 5 000 Hz beside its diagram, and
the evaluation according to ISO 717-1:
$R_\mathrm{s,w}$ ($C$; $C_\mathrm{tr}$),
$C_{100\text{-}5000}$ and
$C_\mathrm{tr,100\text{-}5000}$, in brackets when J.1 puts
them there. Minimum values are printed with `≥`, those set to
$R_\mathrm{s,max}$ in brackets.

**Parameters**

| Name | Description |
| :--- | :--- |
| `path` | Destination path of the PDF file. |
| `metadata` | Optional [`ReportMetadata`](/phonometry/reference/api/building/insulation/#reportmetadata); its `separating_element` and `test_signal` fill the separation wall and test noise rows of the form. |
| `engine` | Rendering back end; only `"reportlab"` is supported. |
| `verbose` | When `True`, the table also shows $R_\mathrm{s}'$ and $R_\mathrm{s,max}$. |
| `language` | `"en"` (default) or `"es"`. |

**Returns:** The written `path` as a `str`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | If `engine` or `language` is unknown, or the result carries no rating (the 16 bands 100 Hz to 3 150 Hz are missing). |
| ImportError | If reportlab or matplotlib is not installed. |
