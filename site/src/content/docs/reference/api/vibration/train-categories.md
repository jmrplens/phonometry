---
title: "vibration.immission.train_categories"
description: "Railway vibration by category of train (E DIN 4150-2:2023-08, 6.5.3)."
sidebar:
  label: "train_categories"
---

Railway vibration by category of train (E DIN 4150-2:2023-08, 6.5.3).

The draft of August 2023 that is to replace DIN 4150-2:1999-06 rewrites how a
railway is assessed for the people in a building. The 1999 edition formed the
clock maximum r.m.s. over the intervals a class of train occupied, raised the
guide values by 1,5 for an urban line and left the upper value out of the
railway's verdict altogether. The draft keeps the two assessment quantities
and changes what feeds them:

- every train passage counts as **one** clock interval, however long it
  lasts (6.5.3.2), so $KB_{FTm,Zug}$ of Formula (5) is the r.m.s. of one
  clock maximum per passage, with nothing set to zero below 0,1;
- $KB_{F\mathrm{max}}$ of a railway is not the largest clock maximum
  observed but **1,5 times** $KB_{FTm,Zug}$ of each category and the
  largest of those (Formulae (7) and (8)), because a single passage with a
  flat spot on a wheel is not what the line is like;
- the assessment vibration severity of Formula (6) weights each category by
  the number of its trains in the period, out of the 1920 or 960 clock
  intervals of the day or the night, and by a **weighting factor**
  $\alpha_{Zug}$ of Table 2 for the kind of train and whether the line
  runs on the surface or underground: 0,7 for a tram on the surface, 1,3 for
  a freight train over 600 m anywhere. A category whose r.m.s. is at or below
  0,1 enters Formula (6) as zero;
- a line to be built new is held at night to an upper value of its own
  (6.5.3.5): 0,6 on the surface in any area, and underground the Table 1
  value in an industrial or commercial area and 0,3 elsewhere;
- an existing line that is altered or extended is judged by the **change**
  it brings (6.5.3.6): the planned case is first held to the guide values as
  any immission is, and where $A_o$ or $A_r$ is exceeded the
  requirement still counts as met if $KB_{F\mathrm{max}}$ or
  $KB_{FTr}$ grows by less than 25 % against the case without the
  project, which is the least increase a laboratory study found people to
  notice. The clause says the requirements are met if *one* of its
  conditions holds, and its own Example 9 sends a line whose
  $KB_{F\mathrm{max}}$ does not change at all to mitigation because
  $KB_{FTr}$ grows by more; every condition that applies has to hold
  here, as in the example, and the sentence is in `docs/ERRATA.md`.

E DIN 45672-3:2023-02, the draft prediction method for railways, takes the
sum of Formula (6) as its Formula (11) and the same factors as its Annex E,
though it prints the sum without the sentence that zeroes a category at or
below 0,1, so the functions here serve both; the prediction chain that leads
up to them is in [`phonometry.vibration.immission.railway_prediction`](/phonometry/reference/api/vibration/railway-prediction/).

Every example of Annex B that the draft works with these formulae is a
conformance row: the 47 passages of Table B.1 and their eight derived values,
and the four assessment severities of Example 9. The two night-time
severities of those four are printed over 920 intervals where 6.5.3.2 fixes
960, and the day-time one of Example 8 is printed as 0,099 8 where its own
four-decimal inputs give 0,099 7; both are registered in `docs/ERRATA.md`,
and the rows run the standard's own 960 and its own inputs.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## assess_railway_change

```python
assess_railway_change(
    *,
    kb_fmax_before: float,
    kb_fmax_after: float,
    kb_ftr_before: float,
    kb_ftr_after: float,
    guide: GuideValues,
    time_of_day: str = 'day',
) -> RailwayChange
```

Judge an altered or extended line by the change it brings (6.5.3.6).

The case without the project, the Prognosenullfall, is the existing
line with its present or its forecast timetable; the planned case, the
Prognoseplanfall, is the line with the project. The planned case is
first held to the guide values in the order of 6.3: a
$KB_{F\mathrm{max}}$ at or below $A_u$ meets the
requirements on its own, and so does one at or below $A_o$ with a
$KB_{FTr}$ at or below $A_r$, and then the change is beside
the point. Where $KB_{F\mathrm{max}}$ exceeds $A_o$, or
$KB_{FTr}$ exceeds $A_r$, the requirements still count as
met if the quantity grows by less than 25 % against the case without the
project; otherwise mitigation is to be looked into. Example 9 of Annex B
finds a night-time $KB_{FTr}$ of 0,096 against 0,066 before, an
increase of over 25 % above an $A_r$ of 0,07, and sends the
project to mitigation although its $KB_{F\mathrm{max}}$ does not
change, which is why every condition that applies has to hold here and
not one of them, as the clause is printed.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_fmax_before` | $KB_{F\mathrm{max}}$ of Formula (8) without the project. |
| `kb_fmax_after` | The same with the project. |
| `kb_ftr_before` | $KB_{FTr}$ of Formula (6) without the project. |
| `kb_ftr_after` | The same with the project. |
| `guide` | The guide values of the planned case, from [`railway_guide_values`](/phonometry/reference/api/vibration/train-categories/#railway_guide_values) for the night-time $A_o$ of 6.5.3.6 b); they must be of the 2023 edition and of the same period. |
| `time_of_day` | `"day"` (default) or `"night"`. |

**Returns:** The verdict, as a [`RailwayChange`](/phonometry/reference/api/vibration/train-categories/#railwaychange).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For a negative quantity, an unknown time of day, or guide values of the 1999 edition or of the other period. |

## RAILWAY_CHANGE_TOLERANCE_PERCENT

*Constant* (`float`).

```python
RAILWAY_CHANGE_TOLERANCE_PERCENT = 25.0
```

## railway_guide_values

```python
railway_guide_values(
    area: str,
    *,
    time_of_day: str = 'day',
    alignment: str = 'surface',
) -> GuideValues
```

The guide values a line to be built new is held to (6.5.3.5).

$A_u$ and $A_r$ are Table 1 of the draft, by day and by
night, and $A_o$ is Table 1 by day. At night the upper value is the
line's own: 0,6 on the surface whatever the area; underground, the
Table 1 value in an industrial or commercial area and 0,3 in a mixed,
residential or sensitive one. The same values bound the planned case of
an altered or extended line (6.5.3.6 b)).

**Parameters**

| Name | Description |
| :--- | :--- |
| `area` | The row of Table 1, as [`GUIDE_VALUES`](/phonometry/reference/api/vibration/people/#guide_values) keys it. |
| `time_of_day` | `"day"` (default) or `"night"`. |
| `alignment` | `"surface"` (default) or `"underground"`. |

**Returns:** The three values, as a [`GuideValues`](/phonometry/reference/api/vibration/people/#guidevalues) of the 2023 edition.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown area, time of day or alignment. |

## railway_kb_fmax

```python
railway_kb_fmax(kb_ftm_zug: ArrayLike) -> float
```

The $KB_{F\mathrm{max}}$ of a railway, Formula (8).

The largest $KB_{F\mathrm{max},Zug}$ of Formula (7) over the
categories, which is what the draft compares with $A_u$ and
$A_o$.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_ftm_zug` | $KB_{FTm,Zug}$ of each category. |

**Returns:** $KB_{F\mathrm{max}}$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an empty, non-finite or negative input. |

## RAILWAY_NEW_LINE_NIGHT_A_O

*Constant* (`dict`).

```python
RAILWAY_NEW_LINE_NIGHT_A_O = {'surface': 0.6, 'underground': 0.3}
```

## RailwayChange

```python
RailwayChange(
    complies: bool,
    kb_fmax_met: bool,
    kb_ftr_met: bool,
    kb_fmax_increase_percent: float,
    kb_ftr_increase_percent: float,
    guide: GuideValues,
    time_of_day: str,
)
```

The verdict of 6.5.3.6 on an altered or extended line.

**Attributes**

| Name | Description |
| :--- | :--- |
| `complies` | Whether the requirements count as met for the planned case: $KB_{F\mathrm{max}}$ keeps to $A_u$, or both the $KB_{F\mathrm{max}}$ and the $KB_{FTr}$ condition hold. |
| `kb_fmax_met` | Whether $KB_{F\mathrm{max}}$ of the planned case keeps to $A_u$ or $A_o$, or exceeds $A_o$ by an increase under 25 % against the case without the project. |
| `kb_ftr_met` | Whether $KB_{FTr}$ of the planned case keeps to $A_r$, or exceeds it by an increase under 25 %; true without looking when $KB_{F\mathrm{max}}$ keeps to $A_u$, which settles the verdict on its own. |
| `kb_fmax_increase_percent` | The increase of $KB_{F\mathrm{max}}$, planned against existing, in per cent. |
| `kb_ftr_increase_percent` | The same for $KB_{FTr}$. |
| `guide` | The guide values the planned case was held to. |
| `time_of_day` | `"day"` or `"night"`. |

## train_assessment_severity

```python
train_assessment_severity(
    kb_ftm_zug: ArrayLike,
    trains: ArrayLike,
    *,
    alpha: ArrayLike,
    time_of_day: str = 'day',
) -> float
```

The assessment vibration severity of a railway, Formula (6).

$KB_{FTr} = \sqrt{\sum_{Zug} \frac{n_{Zug}}{N_r} (\alpha_{Zug} KB_{FTm,Zug})^2}$: each category weighted by the trains it runs in the
period, out of the $N_r$ = 1920 clock intervals of the day or 960
of the night, and by its factor of Table 2. A category whose r.m.s. is
at or below 0,1 enters as zero. The rest hours of the day are not
applied to a railway (6.5.3.2). E DIN 45672-3:2023-02 Formula (11) is
the same sum, printed without the sentence on 0,1. The categories are at
least one per track or direction and kind of train, and their trains are
counted apart, so nothing bounds their sum by the intervals of the
period: two tracks can each carry a train in the same interval.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_ftm_zug` | $KB_{FTm,Zug}$ of each category, as [`train_category_rms`](/phonometry/reference/api/vibration/train-categories/#train_category_rms) gives them. |
| `trains` | $n_{Zug}$, the trains of each category in the period, from the timetable. |
| `alpha` | $\alpha_{Zug}$ of each category, from [`train_weighting_factor`](/phonometry/reference/api/vibration/train-categories/#train_weighting_factor), or one value for all. |
| `time_of_day` | `"day"` (default) or `"night"`. |

**Returns:** $KB_{FTr}$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For mismatched, negative or non-finite inputs, a count that is not whole, or an unknown time of day. |

## train_category_rms

```python
train_category_rms(kb_fti_zug: ArrayLike) -> float
```

The clock maximum r.m.s. of one category of train, Formula (5).

$KB_{FTm,Zug} = \sqrt{\frac{1}{Z}\sum_{i=1}^{Z} KB^2_{FTi,Zug}}$ over
the $Z$ passages measured, one clock maximum per passage whatever
the passage lasted. Unlike Formula (1) and the 1999 edition's (A.1), a
maximum at or below 0,1 enters as it is: the suppression is applied to
the category's r.m.s. in Formula (6), not to the passages (C.2), because
$KB_{F\mathrm{max}}$ of Formula (7) is formed from this value.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_fti_zug` | $KB_{FTi,Zug}$ of each passage, dimensionless. |

**Returns:** $KB_{FTm,Zug}$.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an empty, non-finite or negative input. |

## train_kb_fmax

```python
train_kb_fmax(kb_ftm_zug: ArrayLike) -> NDArray[np.float64]
```

The $KB_{F\mathrm{max},Zug}$ of each category, Formula (7).

$KB_{F\mathrm{max},Zug} = 1{,}5 \cdot KB_{FTm,Zug}$, the estimate the
draft uses instead of the largest clock maximum observed, which a single
passage with an out-of-round wheel would decide. Formed from the value
before rounding: Table B.1 prints 0,851 for a category whose r.m.s. it
prints as 0,568.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kb_ftm_zug` | $KB_{FTm,Zug}$ of each category. |

**Returns:** $KB_{F\mathrm{max},Zug}$ of each, in the same order.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an empty, non-finite or negative input. |

## TRAIN_KB_FMAX_FACTOR

*Constant* (`float`).

```python
TRAIN_KB_FMAX_FACTOR = 1.5
```

## TRAIN_KINDS

*Constant* (`tuple`).

```python
TRAIN_KINDS = ('tram_metro', 's_bahn', 'passenger', 'freight', 'freight_long')
```

## train_weighting_factor

```python
train_weighting_factor(kind: str, *, alignment: str = 'surface') -> float
```

The weighting factor $\alpha_{Zug}$ of Table 2 for one category.

**Parameters**

| Name | Description |
| :--- | :--- |
| `kind` | The kind of train, as [`TRAIN_KINDS`](/phonometry/reference/api/vibration/train-categories/#train_kinds) lists them. |
| `alignment` | `"surface"` (default) or `"underground"`. |

**Returns:** $\alpha_{Zug}$, dimensionless.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | For an unknown kind or alignment. |

## TRAIN_WEIGHTING_FACTORS

*Constant* (`dict`).

```python
TRAIN_WEIGHTING_FACTORS = {'tram_metro': {'surface': 0.7, 'underground': 1.0}, 's_bahn': {'surface': 0.8, 'underground': 1.0}, 'passenger': {'surface': 0.9, 'underground': 1.0}, 'freight': {'surface': 1.0, 'underground': 1.0}, 'freight_long': {'surface': 1.3, 'underground': 1.3}}
```
