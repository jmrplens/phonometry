---
title: "vibration.immission.people"
description: "Vibration and the people in a building (DIN 4150-2:1999-06)."
sidebar:
  label: "people"
---

Vibration and the people in a building (DIN 4150-2:1999-06).

DIN 4150-2 is the assessment the DIN 45669-1 meter exists for. The meter
produces two numbers for a record, the maximum weighted vibration severity
$KB_{F\mathrm{max}}$ and the clock maximum r.m.s. $KB_{FTm}$, and
this standard says what they may be for the people who live or work where the
vibration arrives: a table of guide values by kind of area and time of day,
a procedure that reads them in a fixed order, and the special rules for the
sources that most often bring vibration into a house.

**The two assessment quantities** (Clause 6.1). $KB_{F\mathrm{max}}$ is
what the vibration felt like at its worst. The **assessment vibration
severity** $KB_{FTr}$ of Formulae (4a), (4b) and (5) is what it added
up to over the whole assessment period, 16 h by day and 8 h by night: the
clock maximum r.m.s. of each stretch of exposure, weighted by its share of the
period, and doubled in weight where the stretch falls in the rest hours of the
day. The largest of the three directions is the one assessed.

**The procedure** (Clause 6.2, Figure 2). If $KB_{F\mathrm{max}}$ is at
or below the lower guide value $A_u$, the requirement is met and the
question is over. If it is above the upper guide value $A_o$, it is not
met. In between, rare and short events are accepted as they are, and
everything else is decided by $KB_{FTr}$ against $A_r$. The guide
values of Table 1 are not to be applied mechanically, the standard says, and
Example 3 of its Annex C shows what it means: 0,17 against an $A_u$ of
0,15 is inside the 15 % a measurement of $KB_F$ is uncertain by, and
the requirement "can as a rule still be regarded as met".

**The sources** (Clause 6.5). Up to three short events a day, blasting among
them, are judged on $A_o$ alone, and quarry blasting by day in a mixed
or residential area, under the conditions of 6.5.1, on the $A_o$ of an
industrial one. Road traffic uses the procedure without the rest-time factor.
A railway is judged on $A_u$ and $A_r$ only, with the factor 1,5
on both for an urban surface line; $A_o$ is not a verdict for it, and
6.5.3.5 sets its own night-time thresholds, 0,6 on a surface line and 0,3
underground, above which a single clock maximum is a reason to look into the
cause. A construction site has its own Table 2, by how many working days it
shakes the neighbours and how far the operator is prepared to go, with the
values for two to six days interpolated as Figure 3 draws them.

**A railway, in detail** (Annex A). The trains of one class occupy a few
clock intervals each, so their $KB_{FTm}$ is formed over the occupied
intervals alone (Formula (A.1)), a standard deviation is put on its square
(Formula (A.2)), and the assessment severity weights each class by the
intervals it occupies in the period, 1920 by day and 960 by night (Formula
(A.3)). Figure D.1 turns that around: how many trains an hour a class may run
before $KB_{FTr}$ reaches $A_r$.

**From a velocity record** (Clause 7). Where only an unweighted record
exists, Formula (6) turns its peak and its frequency into a KB value and
Formula (7) scales that by an empirical factor of Table 3 to an estimate of
$KB_{F\mathrm{max}}$, marked with an asterisk in the standard because
it is one.

**A formula printed wrong.** Formula (A.1b) equates $KB_{FTm,j}$ to a
mean of squares with no root over it; Formula (A.1a) beside it, Formula (A.2)
and the worked Example 8 all take the root. Registered in `docs/ERRATA.md`.

**The draft of 2023.** E DIN 4150-2:2023-08 is to replace the 1999 edition,
and `edition="2023"` reads it: Table 1 with one cell changed, the night
$A_u$ of a mixed area down from 0,15 to 0,1; no shortcut for a
$KB_{F\mathrm{max}}$ within the 15 % above $A_u$, which its
Example 3 sends on to $A_r$ and fails; a railway compared with
$A_o$ like any other source, its $KB_{F\mathrm{max}}$ and
$KB_{FTr}$ formed by category of train in
[`phonometry.vibration.immission.train_categories`](/phonometry/reference/api/vibration/train-categories/); an existing road
whose neighbours must put up with $A_u$ and $A_r$ exceeded by up
to 50 % (6.5.2); and an induced seismic event, held by day and by night to
the daytime $A_o$ (6.5.1.3). The rest of the numbers are the same, and
the draft's Table 3 prints the days two to six that the 1999 Figure 3 made
one read off a curve, cell for cell what the interpolation gives.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## admissible_exposure_s

```python
admissible_exposure_s(
    kb_ftm: float,
    a_r: float,
    *,
    time_of_day: str = 'day',
) -> float
```

How long a source may act before $KB_{FTr}$ reaches $A_r$.

Formula (4b) turned around, as Example 2 of Annex C does it:
$T_e = (A_r / KB_{FTm})^2 \, T_r$. Longer than the period means
the source may run all day and still keep to $A_r$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_ftm` | $KB_{FTm}$ of the source, positive. |
| `a_r` | $A_r$, the guide value it is held to. |
| `time_of_day` | `"day"` (default) or `"night"`. |

**Returns:** The exposure, in seconds.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive severity or guide value, or an unknown time of day. |

## admissible_trains_per_hour

```python
admissible_trains_per_hour(kb_ftm: float, a_r: float) -> float
```

How many trains an hour keep $KB_{FTr}$ at $A_r$ (Figure D.1).

With one class of train and each train occupying one clock interval,
Formula (A.4) reads $KB_{FTr} = KB_{FTm}\sqrt{n / 120}$ for
$n$ trains an hour, so the most an hour may carry is
$120 (A_r / KB_{FTm})^2$. Annex D reads the figure at 7 trains for
an $A_r$ of 0,05 and 14 for 0,07, both at a $KB_{FTm}$ of 0,2.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_ftm` | $KB_{FTm}$ of one passage, positive. |
| `a_r` | $A_r$. |

**Returns:** Trains per hour, not rounded; the standard rounds down.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a non-positive severity or guide value. |

## assess_people_in_buildings

```python
assess_people_in_buildings(
    kb_fmax: float,
    guide: GuideValues,
    *,
    kb_ftr: float | None = None,
    source: str = 'general',
    rare_short_events: bool = False,
    edition: str | None = None,
) -> PeopleAssessment
```

Read the guide values in the order of Clause 6.2 (Figure 2).

$KB_{F\mathrm{max}}$ at or below $A_u$ meets the requirement,
and so, as a rule, does one above it by less than the 15 % of 5.4 that a
measurement of $KB_F$ is uncertain by, which is how the standard's
own Example 3 concludes on 0,17 against an $A_u$ of 0,15; the
verdict says so in `within_uncertainty`. Above $A_o$ it is not
met, unless the source is a railway, which 6.5.3.1 judges on $A_u$
and $A_r$ alone. Between the two, up to three short events a day
are met as they are (6.5.1), and anything else is decided by
$KB_{FTr}$ against $A_r$, which has to be supplied then: it is
formed from the record by [`assessment_vibration_severity`](/phonometry/reference/api/vibration/people/#assessment_vibration_severity) or, for a
railway, by [`railway_assessment_severity`](/phonometry/reference/api/vibration/people/#railway_assessment_severity). The note to 6.2 says when
that is not worth doing: a steady vibration acting for much longer than
4 h by day or 2 h by night keeps to $A_r$ only if it keeps to
$A_u$.

Each comparison is made at the decimals the guide value is printed with,
which is how Example 4 reads a $KB_{FTr}$ of 0,154 as meeting an
$A_r$ of 0,15; and the standard says the values are not to be
applied mechanically in any case.

The draft of 2023 reads the same order (its 6.3 and Figure 2) with three
differences: a $KB_{F\mathrm{max}}$ within the 15 % above
$A_u$ goes on to $A_r$ like any other, which is how its
Example 3 fails 0,114 against 0,10; a railway is compared with
$A_o$ as well, its $KB_{F\mathrm{max}}$ being the 1,5 times
$KB_{FTm,Zug}$ of [`railway_kb_fmax`](/phonometry/reference/api/vibration/train-categories/#railway_kb_fmax) and
its $KB_{FTr}$ that of
[`train_assessment_severity`](/phonometry/reference/api/vibration/train-categories/#train_assessment_severity); and a road is
not, by night, its 6.5.2 saying that a rare exceedance of the night-time
$A_o$ does not fail the requirement, with
[`ROAD_NIGHT_INVESTIGATION_KB`](/phonometry/reference/api/vibration/people/#road_night_investigation_kb) in its place as a reason to look
into the cause. An induced seismic event is a rare short event by
definition (6.5.1.3). The edition is the one the guide values were read
from, and asking for the other is refused: the values of one edition
under the rules of the other is not an assessment of either.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_fmax` | $KB_{F\mathrm{max}}$, the largest of the three directions. |
| `guide` | The guide values, from [`guide_values`](/phonometry/reference/api/vibration/people/#guide_values-1), [`construction_guide_values`](/phonometry/reference/api/vibration/people/#construction_guide_values-1) or, for a railway under the draft, [`railway_guide_values`](/phonometry/reference/api/vibration/train-categories/#railway_guide_values). |
| `kb_ftr` | $KB_{FTr}$, needed only when the verdict comes down to it. |
| `source` | `"general"` (default), `"road"`, `"railway"`, `"urban_railway"` or `"quarry_blasting"`, which is a rare short event by definition; under the draft, `"road_existing"` and `"induced_seismic"` in place of `"urban_railway"`. |
| `rare_short_events` | Whether the immission is at most three short events a day, such as blasting, which 6.5.1 judges on $A_o$ alone. |
| `edition` | `"1999"` or `"2023"`, the draft; `None` (default) takes the edition of the guide values. |

**Returns:** The verdict, as a [`PeopleAssessment`](/phonometry/reference/api/vibration/people/#peopleassessment).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative severity, an unknown source or edition, an edition other than the guide values are of, or a verdict that needs $KB_{FTr}$ without one given. |

## ASSESSMENT_PERIOD_S

*Constant* (`dict`).

```python
ASSESSMENT_PERIOD_S = {'day': 57600.0, 'night': 28800.0}
```

## ASSESSMENT_TAKT_COUNT

*Constant* (`dict`).

```python
ASSESSMENT_TAKT_COUNT = {'day': 1920, 'night': 960}
```

## assessment_vibration_severity

```python
assessment_vibration_severity(
    kb_ftm: ArrayLike,
    exposure_s: ArrayLike,
    *,
    time_of_day: str = 'day',
    in_rest_time: ArrayLike | None = None,
) -> float
```

The assessment vibration severity $KB_{FTr}$, Formulae (4) and (5).

$KB_{FTr} = \sqrt{\frac{1}{T_r} \sum_j w_j T_{e,j} KB_{FTm,j}^2}$:
the clock maximum r.m.s. of each stretch of exposure, weighted by the
share of the assessment period it lasts for. One stretch is Formula
(4b), several are Formula (4a), and a stretch in the rest hours of the
day carries the weight 2 of Formula (5), which 6.5.2 and 6.5.3.1 say is
not applied to road or rail traffic.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_ftm` | $KB_{FTm}$ of each stretch, dimensionless, as [`takt_maximum_rms`](/phonometry/reference/api/vibration/vibration-meter/#takt_maximum_rms) gives it. |
| `exposure_s` | $T_{e,j}$, how long each stretch lasts within the period, in seconds. |
| `time_of_day` | `"day"` (default, $T_r$ = 16 h) or `"night"` (8 h). |
| `in_rest_time` | Whether each stretch falls in the rest hours of the day, one flag per stretch; `None` (default) for none. Rest hours exist by day only. |

**Returns:** $KB_{FTr}$, dimensionless.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For mismatched or negative inputs, an unknown time of day, an exposure longer than the period, or a rest-time flag by night. |

## BLASTING_EXCEPTION_KB_FMAX

*Constant* (`float`).

```python
BLASTING_EXCEPTION_KB_FMAX = 8.0
```

## BLASTING_MAX_PER_WEEK

*Constant* (`int`).

```python
BLASTING_MAX_PER_WEEK = 15
```

## CONSTRUCTION_BLASTING_A_O

*Constant* (`float`).

```python
CONSTRUCTION_BLASTING_A_O = 8.0
```

## CONSTRUCTION_GUIDE_VALUES

*Constant* (`dict`).

```python
CONSTRUCTION_GUIDE_VALUES = {'I': {1: GuideValues(a_u=0.8, a_o=5.0, a_r=0.4, time_of_day='day', edition='1999'), 26: GuideValues(a_u=0.4, a_o=5.0, a_r=0.3, time_of_day='day', edition='1999'), 78: GuideValues(a_u=0.3, a_o=5.0, a_r=0.2, time_of_day='day', edition='1999')}, 'II': {1: GuideValues(a_u=1.2, a_o=5.0, a_r=0.8, time_of_day='day', edition='1999'), 26: GuideValues(a_u=0.8, a_o=5.0, a_r=0.6, time_of_day='day', edition='1999'), 78: GuideValues(a_u=0.6, a_o=5.0, a_r=0.4, time_of_day='day', edition='1999')}, 'III': {1: GuideValues(a_u=1.6, a_o=5.0, a_r=1.2, time_of_day='day', edition='1999'), 26: GuideValues(a_u=1.2, a_o=5.0, a_r=1.0, time_of_day='day', edition='1999'), 78: GuideValues(a_u=0.8, a_o=5.0, a_r=0.6, time_of_day='day', edition='1999')}}
```

## construction_guide_values

```python
construction_guide_values(
    duration_days: int,
    *,
    stage: str = 'I',
    area: str = 'residential',
) -> GuideValues
```

The daytime guide values of Table 2 for a construction site (6.5.4.2).

The duration is the number of working days on which the site actually
shakes the neighbours, not how long it stands. A duration of two to six
days takes the values Figure 3 interpolates between the one-day column
and the column that starts at seven days, and a duration over 78 days is
outside the table. Vibration at night is judged by Table 1 instead, and
the site's blasting by [`CONSTRUCTION_BLASTING_A_O`](/phonometry/reference/api/vibration/people/#construction_blasting_a_o) alone. Table 2
is not applicable to an especially sensitive area, a hospital for one;
6.5.4.2 sends those to their own investigation and agreement.

**Parameters**

| Name | Description |
| :--- | :--- |
| `duration_days` | $D$, a whole number of working days from 1 to 78. |
| `stage` | `"I"` (default), `"II"` or `"III"`. |
| `area` | The area the site is in; a commercial or industrial one has an $A_o$ of 6 rather than 5, and `"sensitive"` is refused. |

**Returns:** The three values, as a [`GuideValues`](/phonometry/reference/api/vibration/people/#guidevalues).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a duration that is not a whole number of days from 1 to 78, an unknown stage, an unknown area or a sensitive one. |

## CONSTRUCTION_STAGES

*Constant* (`tuple`).

```python
CONSTRUCTION_STAGES = ('I', 'II', 'III')
```

## DAY_REST_TIME_S

*Constant* (`float`).

```python
DAY_REST_TIME_S = 14400.0
```

## GUIDE_VALUES

*Constant* (`dict`).

```python
GUIDE_VALUES = {'industrial': {'day': GuideValues(a_u=0.4, a_o=6.0, a_r=0.2, time_of_day='day', edition='1999'), 'night': GuideValues(a_u=0.3, a_o=0.6, a_r=0.15, time_of_day='night', edition='1999')}, 'commercial': {'day': GuideValues(a_u=0.3, a_o=6.0, a_r=0.15, time_of_day='day', edition='1999'), 'night': GuideValues(a_u=0.2, a_o=0.4, a_r=0.1, time_of_day='night', edition='1999')}, 'mixed': {'day': GuideValues(a_u=0.2, a_o=5.0, a_r=0.1, time_of_day='day', edition='1999'), 'night': GuideValues(a_u=0.15, a_o=0.3, a_r=0.07, time_of_day='night', edition='1999')}, 'residential': {'day': GuideValues(a_u=0.15, a_o=3.0, a_r=0.07, time_of_day='day', edition='1999'), 'night': GuideValues(a_u=0.1, a_o=0.2, a_r=0.05, time_of_day='night', edition='1999')}, 'sensitive': {'day': GuideValues(a_u=0.1, a_o=3.0, a_r=0.05, time_of_day='day', edition='1999'), 'night': GuideValues(a_u=0.1, a_o=0.15, a_r=0.05, time_of_day='night', edition='1999')}}
```

## guide_values

```python
guide_values(
    area: str,
    *,
    time_of_day: str = 'day',
    source: str = 'general',
    edition: str = '1999',
) -> GuideValues
```

The guide values of Table 1 for one area, time of day and kind of source.

**Parameters**

| Name | Description |
| :--- | :--- |
| `area` | The row of Table 1, as [`GUIDE_VALUES`](/phonometry/reference/api/vibration/people/#guide_values) keys it. |
| `time_of_day` | `"day"` (default) or `"night"`. |
| `source` | `"general"` (default), `"road"` or `"railway"`, for which Table 1 applies as printed; `"urban_railway"`, the surface line of a public transport system, for which 6.5.3.3 raises $A_u$ and $A_r$ by the factor 1,5; or `"quarry_blasting"`, blasts on working days with the neighbours warned, between 7:00 and 13:00 or 15:00 and 19:00, one event a day, for which 6.5.1 lets a mixed or residential area take the daytime $A_o$ of row 1, which is 6. The draft of 2023 has no `"urban_railway"` and adds `"road_existing"`, an existing road by an existing building, whose $A_u$ and $A_r$ its neighbours must put up with exceeded by up to 50 % (6.5.2), and `"induced_seismic"`, which the daytime $A_o$ bounds by night as well (6.5.1.3). |
| `edition` | `"1999"` (default), DIN 4150-2:1999-06, or `"2023"`, E DIN 4150-2:2023-08, whose Table 1 has the night $A_u$ of a mixed area at 0,1. |

**Returns:** The three values, as a [`GuideValues`](/phonometry/reference/api/vibration/people/#guidevalues).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown area, time of day, source or edition, or a source the edition does not have. |

## GUIDE_VALUES_2023

*Constant* (`dict`).

```python
GUIDE_VALUES_2023 = {'industrial': {'day': GuideValues(a_u=0.4, a_o=6.0, a_r=0.2, time_of_day='day', edition='2023'), 'night': GuideValues(a_u=0.3, a_o=0.6, a_r=0.15, time_of_day='night', edition='2023')}, 'commercial': {'day': GuideValues(a_u=0.3, a_o=6.0, a_r=0.15, time_of_day='day', edition='2023'), 'night': GuideValues(a_u=0.2, a_o=0.4, a_r=0.1, time_of_day='night', edition='2023')}, 'mixed': {'day': GuideValues(a_u=0.2, a_o=5.0, a_r=0.1, time_of_day='day', edition='2023'), 'night': GuideValues(a_u=0.1, a_o=0.3, a_r=0.07, time_of_day='night', edition='2023')}, 'residential': {'day': GuideValues(a_u=0.15, a_o=3.0, a_r=0.07, time_of_day='day', edition='2023'), 'night': GuideValues(a_u=0.1, a_o=0.2, a_r=0.05, time_of_day='night', edition='2023')}, 'sensitive': {'day': GuideValues(a_u=0.1, a_o=3.0, a_r=0.05, time_of_day='day', edition='2023'), 'night': GuideValues(a_u=0.1, a_o=0.15, a_r=0.05, time_of_day='night', edition='2023')}}
```

## GuideValues

```python
GuideValues(
    a_u: float,
    a_o: float,
    a_r: float,
    time_of_day: str = 'day',
    edition: str = '1999',
)
```

One row of Table 1 or Table 2 for one period: the three guide values.

**Attributes**

| Name | Description |
| :--- | :--- |
| `a_u` | $A_u$, the lower value, which $KB_{F\mathrm{max}}$ is compared with first. |
| `a_o` | $A_o$, the upper value, above which the requirement is not met however short the exposure. |
| `a_r` | $A_r$, the value the assessment vibration severity $KB_{FTr}$ is compared with. |
| `time_of_day` | The period the row is for, `"day"` or `"night"`; Table 2 is daytime only. |
| `edition` | The edition the values are read from, `"1999"` or `"2023"`, which is the edition [`assess_people_in_buildings`](/phonometry/reference/api/vibration/people/#assess_people_in_buildings) judges them under unless told otherwise. |

## induced_seismic_kb_fmax

```python
induced_seismic_kb_fmax(peak_velocity_mm_s: float) -> float
```

The $KB_{F\mathrm{max}}$ of an induced seismic event, E DIN 4150-2:2023-08 6.5.1.3.

$KB_{F\mathrm{max}} = 0{,}44 \, v_{\max}$, the simplified estimate
the draft gives for an event of a few seconds with its energy below
15 Hz, which is held by day and by night to the daytime $A_o$
alone; $KB_{FTr}$ is not formed for it.

**Parameters**

| Name | Description |
| :--- | :--- |
| `peak_velocity_mm_s` | $v_{\max}$, in millimetres per second. |

**Returns:** $KB_{F\mathrm{max}}$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative velocity. |

## INDUCED_SEISMIC_PEAK_FACTOR

*Constant* (`float`).

```python
INDUCED_SEISMIC_PEAK_FACTOR = 0.44
```

## kb_fmax_from_peak_velocity

```python
kb_fmax_from_peak_velocity(
    peak_velocity_mm_s: float,
    frequency_hz: float,
    *,
    kind: str,
) -> float
```

An estimate of $KB_{F\mathrm{max}}$ from an unweighted record, Formula (7).

$KB^*_{F\mathrm{max}} = KB \cdot c_F$, Formula (6) scaled by the
factor of Table 3 for the kind of vibration. An estimate, which is what
the asterisk marks: Table 3 puts its factors at about 15 % either way.

**Parameters**

| Name | Description |
| :--- | :--- |
| `peak_velocity_mm_s` | $v_\mathrm{max}$, in millimetres per second. |
| `frequency_hz` | $f$, in hertz. |
| `kind` | The row of Table 3, as [`PEAK_TO_KB_FACTORS`](/phonometry/reference/api/vibration/people/#peak_to_kb_factors) keys it: `"harmonic"` (little distortion, a sawmill at a distance), `"harmonic_distorted"` (more than about 20 %), `"stochastic_resonant"` and `"stochastic"` (looms, pile driving, with and without a resonating floor), `"single_event_resonant"` and `"single_event"`. |

**Returns:** $KB^*_{F\mathrm{max}}$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a bad velocity or frequency, or an unknown kind. |

## kb_from_peak_velocity

```python
kb_from_peak_velocity(
    peak_velocity_mm_s: float,
    frequency_hz: float,
) -> float
```

The KB value of a peak velocity at a frequency, Formula (6).

$KB = \frac{1}{\sqrt 2}\, \frac{v_\mathrm{max}}{\sqrt{1 + (f_o/f)^2}}$
with $f_o$ = 5,6 Hz, the corner of the KB weighting: the value the
weighted severity settles at for a sine of that peak and frequency, which
the note under the formula says is the KB of the 1975 edition.

**Parameters**

| Name | Description |
| :--- | :--- |
| `peak_velocity_mm_s` | $v_\mathrm{max}$, in millimetres per second. |
| `frequency_hz` | $f$, the frequency of the record, in hertz. |

**Returns:** $KB$, dimensionless.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative velocity or a non-positive frequency. |

## KB_UNCERTAINTY_PERCENT

*Constant* (`float`).

```python
KB_UNCERTAINTY_PERCENT = 15.0
```

## PEAK_TO_KB_FACTORS

*Constant* (`dict`).

```python
PEAK_TO_KB_FACTORS = {'harmonic': 0.9, 'harmonic_distorted': 0.8, 'stochastic_resonant': 0.8, 'stochastic': 0.7, 'single_event_resonant': 0.8, 'single_event': 0.6}
```

## PeopleAssessment

```python
PeopleAssessment(
    complies: bool,
    criterion: str,
    kb_fmax: float,
    kb_ftr: float | None,
    guide: GuideValues,
    source: str,
    within_uncertainty: bool,
)
```

The verdict of Clause 6.2 on one immission, and how it was reached.

**Attributes**

| Name | Description |
| :--- | :--- |
| `complies` | Whether the requirement of the standard is met. |
| `criterion` | The comparison that decided it: `"A_u"` when $KB_{F\mathrm{max}}$ kept to the lower value, or exceeded it by less than the measurement is uncertain by; `"A_o"` when it exceeded the upper one or, for a rare short event, kept to it; and `"A_r"` when $KB_{FTr}$ decided. |
| `kb_fmax` | $KB_{F\mathrm{max}}$ as assessed. |
| `kb_ftr` | $KB_{FTr}$, or `None` when it was not needed. |
| `guide` | The three guide values it was held to. |
| `source` | The kind of source the rules were read for. |
| `within_uncertainty` | Whether the verdict rests on the 15 % of 5.4: $KB_{F\mathrm{max}}$ above $A_u$ but by less than a measurement of $KB_F$ is uncertain by, which Annex C Example 3 concludes "can as a rule still be regarded as met". A stricter reading treats such a verdict as open. |

### PeopleAssessment.plot()

```python
PeopleAssessment.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the two assessment quantities against the three guide values.

Requires matplotlib (`pip install phonometry[plot]`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.vibration.plot_people_assessment`. |

**Returns:** The `Axes`.

## railway_assessment_severity

```python
railway_assessment_severity(
    kb_ftm: ArrayLike,
    occupied_takte: ArrayLike,
    *,
    time_of_day: str = 'day',
    spread: ArrayLike | None = None,
) -> RailwayAssessment
```

The assessment vibration severity of a railway, Formulae (A.3) and (A.4).

$KB_{FTr} = \sqrt{\frac{1}{N_r} \sum_j M_j KB^2_{FTm,j}}$: each class
of train weighted by the clock intervals it occupies in the period, out
of the 1920 of a day or the 960 of a night. With one class that is
Formula (A.4). Given the spread of Formula (A.2) for each class, the same
sum is formed with each mean square one spread up and one down, which is
how Example 8 reports $0{,}325^{+0{,}059}_{-0{,}073}$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_ftm` | $KB_{FTm,j}$, one per class, as [`railway_takt_maximum_rms`](/phonometry/reference/api/vibration/people/#railway_takt_maximum_rms) gives them. |
| `occupied_takte` | $M_j$, the clock intervals each class occupies in the period, one per class, which is about the number of its trains in the period when a train occupies one interval. |
| `time_of_day` | `"day"` (default) or `"night"`. |
| `spread` | $s(KB^2_{FTm,j})$ of each class, or `None`. |

**Returns:** The severity and, with a spread, its interval, as a [`RailwayAssessment`](/phonometry/reference/api/vibration/people/#railwayassessment).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For mismatched or negative inputs, more occupied intervals than the period holds, or an unknown time of day. |

## RAILWAY_NIGHT_INVESTIGATION_KB

*Constant* (`dict`).

```python
RAILWAY_NIGHT_INVESTIGATION_KB = {'surface': 0.6, 'underground': 0.3}
```

## railway_takt_maximum_rms

```python
railway_takt_maximum_rms(kb_fti: ArrayLike) -> float
```

The clock maximum r.m.s. of one class of train, Formula (A.1).

The root of the mean square of the clock maxima the trains of the class
occupied, $Z_j$ of them, with nothing counted for the intervals
between trains: Formula (A.1b), with the root Formula (A.1a) and the
worked Example 8 carry and the print of (A.1b) lost. The rule of Formula
(3) that a maximum at or below 0,1 enters as zero applies here as well.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_fti` | The clock maxima the class occupied, dimensionless. |

**Returns:** $KB_{FTm,j}$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an empty, non-finite or negative input. |

## railway_takt_spread

```python
railway_takt_spread(kb_fti: ArrayLike) -> float
```

The standard deviation of the square of the clock maxima, Formula (A.2).

$s(KB^2_{FTm,j}) = \sqrt{\frac{1}{Z_j - 1} \sum_i (KB^2_{FTi,j} - KB^2_{FTm,j})^2}$, on the square because it is the square that Formula
(A.3) averages, so the spread of $KB_{FTr}$ follows from it by
adding and subtracting it there. The maxima enter as they enter
[`railway_takt_maximum_rms`](/phonometry/reference/api/vibration/people/#railway_takt_maximum_rms), a value at or below 0,1 as zero, so the
spread is about the mean square that function returns.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_fti` | The clock maxima the class occupied, at least two. |

**Returns:** $s(KB^2_{FTm,j})$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For fewer than two maxima, or a bad input. |

## RailwayAssessment

```python
RailwayAssessment(
    kb_ftr: float,
    kb_ftm: NDArray[np.float64],
    occupied_takte: NDArray[np.int64],
    lower: float | None,
    upper: float | None,
    time_of_day: str,
)
```

The assessment vibration severity of a railway, Formula (A.3).

**Attributes**

| Name | Description |
| :--- | :--- |
| `kb_ftr` | $KB_{FTr}$ over the assessment period. |
| `kb_ftm` | $KB_{FTm,j}$ of each class of train. |
| `occupied_takte` | $M_j$, the clock intervals each class occupies in the period. |
| `lower` | $KB_{FTr}$ with every class's mean square one spread below its value, or `None` when no spread was given. |
| `upper` | The same, one spread above. |
| `time_of_day` | `"day"` or `"night"`. |

## RARE_EVENTS_PER_DAY

*Constant* (`int`).

```python
RARE_EVENTS_PER_DAY = 3
```

## REST_TIME_WEIGHT

*Constant* (`float`).

```python
REST_TIME_WEIGHT = 2.0
```

## ROAD_EXISTING_TOLERANCE_FACTOR

*Constant* (`float`).

```python
ROAD_EXISTING_TOLERANCE_FACTOR = 1.5
```

## ROAD_NIGHT_INVESTIGATION_KB

*Constant* (`float`).

```python
ROAD_NIGHT_INVESTIGATION_KB = 0.6
```

## URBAN_RAILWAY_FACTOR

*Constant* (`float`).

```python
URBAN_RAILWAY_FACTOR = 1.5
```
