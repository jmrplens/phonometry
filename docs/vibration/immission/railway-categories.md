← [Documentation index](../../README.md)

# Railway vibration by category of train (E DIN 4150-2)

The [1999 edition of DIN 4150-2](people-in-buildings.md)
treats a railway as a set of classes of train, each occupying the clock
intervals its trains ran through, and lifts the guide values by 1,5 for an
urban line. The draft that is to replace it, published for comment in
August 2023, rewrites that part from the ground up and touches little else:
one cell of Table 1, one worked example, two new sources, and the days two
to six of a construction site printed instead of read off a curve. This
page is the railway; the rest of the draft is the last section, and the
library reads either edition with one argument.

## 1. One interval per passage, and a KB_Fmax that is not a maximum

The draft's first decision is that every train passage counts as one clock
interval, however long it lasts (6.5.3.2). So the clock maximum r.m.s. of a
**category** of train, a kind of vehicle on a track in a direction, is the
r.m.s. of one clock maximum per passage over the passages measured (Formula
(5)), and, unlike the 1999 edition's (A.1) and the meter's own Formula (1),
nothing below 0,1 is set to zero on the way, because the next number is
built on it: the `KB_Fmax` of the category is not the largest clock maximum
anyone observed but **1,5 times** its r.m.s. (Formula (7)), since a single
passage with a flat spot on a wheel says nothing about the line. The
`KB_Fmax` of the railway is the largest over the categories (Formula (8)).

Example 8 of Annex B measures 2,5 h in a new residential building next to a
tram and a metro: 14 metro passages each way underground and 9 and 10 tram
passages each way on the surface.

```python
from phonometry import vibration

# Annex B, Table B.1: the clock maximum of every passage, by category.
metro_north = [0.017, 0.036, 0.024, 0.035, 0.025, 0.036, 0.035, 0.037, 0.041, 0.042,
               0.068, 0.040, 0.022, 0.025]
metro_south = [0.076, 0.034, 0.025, 0.054, 0.033, 0.018, 0.033, 0.060, 0.019, 0.092,
               0.030, 0.019, 0.024, 0.058]
tram_east = [0.379, 0.369, 0.348, 0.288, 0.270, 0.549, 0.320, 0.290, 0.663]
tram_west = [0.649, 0.717, 0.658, 0.508, 0.423, 0.332, 0.735, 0.363, 0.441, 0.663]

kb_ftm = [vibration.train_category_rms(c) for c in (metro_north, metro_south, tram_east, tram_west)]
print([round(v, 3) for v in kb_ftm])  # [0.037, 0.047, 0.406, 0.568]
print(vibration.train_kb_fmax(kb_ftm).round(3))  # [0.055 0.07  0.609 0.851]
print(round(vibration.railway_kb_fmax(kb_ftm), 3))  # 0.851
```

## 2. A weighting factor for the kind of train

The assessment vibration severity of a railway is Formula (6): each
category weighted by the number of its trains in the period, out of the
1920 clock intervals of the day or the 960 of the night, and by a
**weighting factor** `α_Zug` of Table 2 for the kind of train and whether
the line runs on the surface or underground. A tram, light rail or metro on
the surface is 0,7, an S-Bahn 0,8, another passenger train 0,9, a freight
train up to 600 m 1,0, and a freight train over 600 m 1,3 wherever it runs;
underground everything but the long freight train is 1,0. A category whose
r.m.s. is at or below 0,1 enters the sum as zero, which is where the
suppression the passages were spared is applied. The rest hours of the day
are not applied to a railway, as they were not in 1999.

```python
from phonometry import vibration

print(vibration.train_weighting_factor("freight_long"))  # 1.3
print(vibration.train_weighting_factor("s_bahn", alignment="underground"))  # 1.0

# Example 8: 144 metros a track a day at 1,0, whose r.m.s. is below 0,1 and
# counts as zero, and 80 trams a track at 0,7.
kb_ftm = [0.03654, 0.04676, 0.40606, 0.56758]
day = vibration.train_assessment_severity(kb_ftm, [144, 144, 80, 80], alpha=[1.0, 1.0, 0.7, 0.7])
print(f"KB_FTr = {day:.4f}")  # 0.0997, printed 0,099 8

guide = vibration.guide_values("residential", edition="2023")
verdict = vibration.assess_people_in_buildings(
    vibration.railway_kb_fmax(kb_ftm), guide, kb_ftr=day, source="railway", edition="2023"
)
print(verdict.complies, verdict.criterion)  # False A_r
```

Under the draft a railway is compared with `A_o` like any other source,
which the 1999 edition did not do; the trams of Example 8 exceed the night
`A_o` of 0,2 of a new residential building and the requirement is not met
by night before `KB_FTr` is even formed.

```python
from phonometry import vibration

night = vibration.guide_values("residential", time_of_day="night", edition="2023")
verdict = vibration.assess_people_in_buildings(0.851, night, source="railway", edition="2023")
print(verdict.complies, verdict.criterion)  # False A_o
```

## 3. A new line, and an old one made bigger

A line to be built new is held at night to an upper value of its own
(6.5.3.5): 0,6 on the surface whatever the area, and underground the
Table 1 value in an industrial or commercial area and 0,3 elsewhere. By day
Table 1 applies as it stands.

```python
from phonometry import vibration

print(vibration.railway_guide_values("mixed", time_of_day="night"))
# GuideValues(a_u=0.1, a_o=0.6, a_r=0.07, time_of_day='night', edition='2023')
print(vibration.railway_guide_values("residential", time_of_day="night", alignment="underground"))
# GuideValues(a_u=0.1, a_o=0.3, a_r=0.05, time_of_day='night', edition='2023')
```

An existing line that is altered or extended is judged by the **change** it
brings (6.5.3.6). The case without the project, with the present or the
forecast timetable, is set against the planned case; the planned case is
first held to the guide values like any immission, a `KB_Fmax` at or below
`A_u` settling it on its own, and where `KB_Fmax` exceeds `A_o` or `KB_FTr`
exceeds `A_r` the requirement still counts as met if the quantity grows by
less than 25 %, the least increase a laboratory study found people to
notice. The clause says the requirements are met if one of its conditions
holds; its own Example 9, whose `KB_Fmax` does not change at all, goes to
mitigation because `KB_FTr` grows by more, so every condition that applies
has to hold, and the library reads it that way. Example 9 adds a second
track to a single-track line
past a house in a mixed area: 28 regional and 8 freight trains a day become
34 and 12, and a third of the freight trains grow past 600 m.

```python
from phonometry import vibration

# Annex B, Example 9. Existing track: regional 0,24, freight 0,44; new track:
# 0,22 and 0,40; the long freight trains at 1,3.
nullfall_day = vibration.train_assessment_severity([0.24, 0.44], [28, 8], alpha=[0.9, 1.0])
nullfall_night = vibration.train_assessment_severity(
    [0.24, 0.44], [12, 18], alpha=[0.9, 1.0], time_of_day="night"
)
kb_ftm = [0.24, 0.22, 0.44, 0.40, 0.44, 0.40]
alpha = [0.9, 0.9, 1.0, 1.0, 1.3, 1.3]
planfall_day = vibration.train_assessment_severity(kb_ftm, [17, 17, 4, 4, 2, 2], alpha=alpha)
planfall_night = vibration.train_assessment_severity(
    kb_ftm, [7, 7, 12, 12, 6, 6], alpha=alpha, time_of_day="night"
)
print(f"{nullfall_day:.3f} {nullfall_night:.3f} {planfall_day:.3f} {planfall_night:.3f}")
# 0.039 0.065 0.046 0.094

change = vibration.assess_railway_change(
    kb_fmax_before=0.66,
    kb_fmax_after=0.66,
    kb_ftr_before=nullfall_night,
    kb_ftr_after=planfall_night,
    guide=vibration.railway_guide_values("mixed", time_of_day="night"),
    time_of_day="night",
)
print(change.complies, change.kb_fmax_met, change.kb_ftr_met)  # False True False
print(f"{change.kb_ftr_increase_percent:.0f} %")  # 44 %
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/railway_change_example_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/railway_change_example.svg" alt="A bar chart of the assessment vibration severity by day and by night, on an axis from 0 to 0.13. In each group a green bar is the case without the project and a blue bar the case with the second track: 0.039 and 0.046 by day, 0.065 and 0.094 by night. A red line marks A r, 0.1 by day and 0.07 by night, and a grey dashed line 25 percent above the green bar, at 0.048 by day and 0.081 by night. By day both bars stay under both lines; by night the blue bar rises above the 25 percent line and above A r, and a note says mitigation" width="96%"></picture>

<details>
<summary>Figure code</summary>

```python
import matplotlib.pyplot as plt
import numpy as np

from phonometry import vibration

before = [
    vibration.train_assessment_severity([0.24, 0.44], [28, 8], alpha=[0.9, 1.0]),
    vibration.train_assessment_severity([0.24, 0.44], [12, 18], alpha=[0.9, 1.0], time_of_day="night"),
]
kb_ftm = [0.24, 0.22, 0.44, 0.40, 0.44, 0.40]
alpha = [0.9, 0.9, 1.0, 1.0, 1.3, 1.3]
after = [
    vibration.train_assessment_severity(kb_ftm, [17, 17, 4, 4, 2, 2], alpha=alpha),
    vibration.train_assessment_severity(kb_ftm, [7, 7, 12, 12, 6, 6], alpha=alpha, time_of_day="night"),
]
x = np.arange(2)
fig, ax = plt.subplots(figsize=(10, 6.2))
ax.bar(x - 0.19, before, 0.38, label="without the project")
ax.bar(x + 0.19, after, 0.38, label="with the second track")
for i, which in enumerate(("day", "night")):
    a_r = vibration.railway_guide_values("mixed", time_of_day=which).a_r
    ax.hlines(a_r, x[i] - 0.45, x[i] + 0.45, color="red")
    ax.hlines(before[i] * 1.25, x[i] - 0.45, x[i] + 0.45, color="grey", linestyle="--")
ax.set_xticks(x, ["by day", "by night"])
ax.legend()
```

</details>

The night of Example 9 is printed over 920 clock intervals, which gives the
0,066 and 0,096 on the page; 6.5.3.2 fixes the night at 960, which gives
0,065 and 0,094, and the conclusion is the same. The
[errata page](../../ERRATA.md) has it, with the one condition
of 6.5.3.6, a result of Example 8 that its own four-decimal inputs do not
give, a decision in the construction flowchart drawn the wrong way round,
ten clock maxima printed on Figure B.2 that do not give the 0,39 the text
uses, an example that cites the clause for a new line while applying the one
for an extension, two cross-references that name the wrong formula and the
wrong clause, and a rare event met below `A_o` in one sentence and at it in
the next clause and the flowchart.

## 4. What else the draft changes

The guide values carry the edition and the period they were read for, so
the verdict knows which rules to apply without being told, and asking for
the values of one edition under the rules of the other is refused.
Everything below is what `edition="2023"` reads differently from the
[1999 edition](people-in-buildings.md); the
numbers not named here are the same in both.

- **Table 1** changes one cell: the night `A_u` of a mixed area, now with
  urban areas in the row, goes from 0,15 to 0,1.
- **The 15 %** a measurement of `KB_F` is uncertain by no longer excuses a
  `KB_Fmax` above `A_u`. The 1999 Example 3 read 0,17 against 0,15 as met on
  that ground; the draft's Example 3 reads 0,114 against 0,10, goes on to
  `KB_FTr`, finds 0,075 against an `A_r` of 0,07, and fails it.
- **A road by night** is not judged on `A_o`: 6.5.2 says a rare exceedance
  of the night-time upper value does not fail the requirement, and puts a
  single clock maximum above 0,6, in any area, down as a reason to look into
  the cause and put it right, which is what the 1999 edition said of a
  railway. **An existing road** by an existing building: the neighbours must
  put up with `A_u` and `A_r` exceeded by up to 50 %, by day and by night
  (6.5.2), which `source="road_existing"` gives as guide values 1,5 times
  over.
- **An induced seismic event**, a few seconds with its energy below 15 Hz,
  years after the intervention that causes it (6.5.1.3): `KB_Fmax` is about
  0,44 times the peak velocity, and it is held by day and by night to the
  daytime `A_o`, with no `KB_FTr`.
- **A construction site**: the draft's Table 3 prints the days two to six
  that the 1999 Figure 3 made one read off a curve, cell for cell what the
  interpolation gives, and says that `D` counts only the days on which
  Table 1 is exceeded.
- The **urban railway** of 1999, with its factor 1,5 on `A_u` and `A_r`, is
  gone; its place is the factor 0,7 of Table 2 on the r.m.s.

```python
from phonometry import vibration

print(vibration.guide_values("mixed", time_of_day="night", edition="2023"))
# GuideValues(a_u=0.1, a_o=0.3, a_r=0.07, time_of_day='night', edition='2023')

# The draft's Example 3: inside the 15 % and no longer excused by it.
guide = vibration.guide_values("mixed", time_of_day="night", edition="2023")
verdict = vibration.assess_people_in_buildings(0.114, guide, kb_ftr=0.075, edition="2023")
print(verdict.complies, verdict.criterion)  # False A_r

print(vibration.guide_values("residential", source="road_existing", edition="2023"))
# GuideValues(a_u=0.225, a_o=3.0, a_r=0.105, time_of_day='day', edition='2023')
print(vibration.induced_seismic_kb_fmax(5.0))  # 2.2
print(vibration.guide_values("residential", time_of_day="night", source="induced_seismic", edition="2023"))
# GuideValues(a_u=0.1, a_o=3.0, a_r=0.05, time_of_day='night', edition='2023')
```

## What this guide covers

**The railway of 6.5.3**: the r.m.s. of a category of train over its
passages (Formula (5)), 1,5 times it and the largest of those (Formulae (7)
and (8)), the assessment vibration severity with the factors of Table 2
(Formula (6)), the night-time upper value of a new line (6.5.3.5) and the
25 % rule of an altered one (6.5.3.6).

**The rest of the draft** behind `edition="2023"`: the one cell of Table 1,
the procedure without the 15 % shortcut, a railway compared with `A_o`, the
existing road of 6.5.2 and the induced seismic event of 6.5.1.3, and Table 3
as printed.

**No decision the draft leaves open.** An existing line that is not being
altered (6.5.3.4) has no numeric rule and none is invented; the concession
of 6.5.3.7 to a new building, an `A_o` of 0,6 for a category with rare
passages, is a judgement and stays one.

**No measurement and no monitoring.** Clause 5, the substitute measuring
points and transfer functions of a long-term monitoring included, and
Clause 8, the report, are text.

## See also

- [Vibration and people in buildings (DIN 4150-2)](people-in-buildings.md):
  the 1999 edition, the procedure and the guide values both editions share.
- [Predicting railway vibration (E DIN 45672-3)](railway-prediction.md):
  where the r.m.s. of a category comes from when there is nothing to
  measure yet.
- [Measuring vibration immission (DIN 45669-1)](vibration-meter.md):
  the clock maxima the categories are formed from.
- API reference:
  [`vibration.immission.train_categories`](https://jmrplens.github.io/phonometry/reference/api/vibration/train-categories/)
  and [`vibration.immission.people`](https://jmrplens.github.io/phonometry/reference/api/vibration/people/).
## References

- Deutsches Institut für Normung. (2023). *Erschütterungen im Bauwesen —
  Teil 2: Einwirkungen auf Menschen in Gebäuden* (E DIN 4150-2:2023-08). A
  draft, intended to replace DIN 4150-2:1999-06. Table 1 with its one changed
  cell, Formulae (5) to (8) and Table 2 of 6.5.3, the night-time upper value
  of 6.5.3.5, the 25 % rule of 6.5.3.6, the existing-road tolerance of 6.5.2,
  the induced seismic event of 6.5.1.3, and Table 3 as printed. Annex B,
  Examples 8 and 9, is the oracle of the conformance rows; Examples 1, 2
  and 4 to 7 are those of the 1999 edition, and Example 3 is reworked
  without the 15 % argument.
- Deutsches Institut für Normung. (1999). *Erschütterungen im Bauwesen —
  Teil 2: Einwirkungen auf Menschen in Gebäuden* (DIN 4150-2:1999-06). The
  edition in force, which the library reads by default.
