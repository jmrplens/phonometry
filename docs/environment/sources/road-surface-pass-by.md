← [Documentation index](../../README.md)

# Road-surface noise: the statistical pass-by method (ISO 11819-1)

A road surface makes no noise of its own, yet the same traffic can be up to
15 dB louder on one surface than on another (the Introduction of ISO 11819-1).
The Statistical Pass-By method measures that influence without choosing any
vehicles: it records the traffic that uses the road, one isolated vehicle at a
time, and lets a regression take the vehicles out. The implemented text is ISO
11819-1:1997, read from BS EN ISO 11819-1:2001, which is identical to it.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/statistical_pass_by_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/statistical_pass_by.svg" alt="Maximum A-weighted level against vehicle speed on a logarithmic axis for a medium-speed site: a cloud of 120 cars, 40 dual-axle and 50 multi-axle heavy vehicles, each cloud with its least-squares line, and a diamond on each line at the reference speed, 80 km/h for the cars and 70 km/h for both heavy categories; the legend gives the vehicle sound levels 78.9, 81.0 and 83.7 dB and the title the Statistical Pass-By Index of 80.2 dB" width="92%"></picture>

## 1. What is measured, and on which vehicles

Each vehicle is put in one of three categories (3.4): **cars (1)**,
**dual-axle heavy vehicles (2a)** and **multi-axle heavy vehicles (2b)**. Vans,
cars with trailers and motorcycles are not used (clause 4). The road is put in
one of three speed categories by the average speed of its traffic (3.3): low
(45 km/h to 64 km/h), medium (65 km/h to 99 km/h) and high (cars at 100 km/h or
more). Table 1 gives, for each, the reference speed every level is brought to
and the weighting factor $W_x$ each category gets in the index:

| Vehicle category | Low: speed | Low: $W_x$ | Medium: speed | Medium: $W_x$ | High: speed | High: $W_x$ |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cars (1) | 50 km/h | 0,900 | 80 km/h | 0,800 | 110 km/h | 0,700 |
| Dual-axle heavy (2a) | 50 km/h | 0,075 | 70 km/h | 0,100 | 85 km/h | 0,075 |
| Multi-axle heavy (2b) | 50 km/h | 0,025 | 70 km/h | 0,100 | 85 km/h | 0,225 |

## How the measurement goes

| Requirement | Value | Clause |
| :--- | :--- | :--- |
| Microphone | 7,5 m ± 0,1 m from the centre of the test lane, 1,2 m ± 0,1 m above it | 8.1 |
| Level | Maximum A-weighted level, time weighting F; type 1 meter; calibration drift over 0,5 dB invalidates the series | 5.1, 5.3, 8.2 |
| Speed | As the vehicle midpoint passes the microphone, standard uncertainty under 3 % | 5.4, 8.4 |
| Which pass-bys | The level at least 6 dB lower just before and after; no overtaking or opposing traffic at the peak; constant speed | 7.2 |
| How many | 100 cars, 30 dual-axle, 30 multi-axle and 80 heavy vehicles together, for classification | 7.3 |
| Site and weather | Level and straight over 30 m each side (50 m on a high-speed road); wind at most 5 m/s; air 5 °C to 30 °C; road 5 °C to 50 °C; dry | 6, 11 |
| Background | At least 10 dB under the quietest pass-by | 12 |

## 2. The vehicle sound level

For each category the pass-bys are fitted by least squares with
$L_{\mathrm{AFmax}} = a + b \lg(v / 1\ \mathrm{km/h})$ (9.1), and the line read
at the reference speed is the **vehicle sound level** $L_\mathrm{veh}$ (9.2).

```python
import numpy as np
from phonometry import environment

rng = np.random.default_rng(11819)
site = {  # pass-bys, mean speed (km/h), spread of lg v, line and scatter (dB)
    "1": (120, 88.0, 0.055, 16.6, 32.6, 1.4),
    "2a": (40, 76.0, 0.050, 46.5, 18.8, 2.0),
    "2b": (50, 74.0, 0.045, 34.5, 26.7, 2.0),
}
categories, speeds, levels = [], [], []
for category, (n, mean_kmh, spread, a, b, scatter) in site.items():
    lg_v = np.log10(mean_kmh) + spread * rng.standard_normal(n)
    categories += [category] * n
    speeds += (10.0**lg_v).tolist()
    levels += (a + b * lg_v + scatter * rng.standard_normal(n)).tolist()

result = environment.statistical_pass_by(
    categories,
    speeds,
    levels,
    road_speed_category="medium",
    reference_db=environment.SPB_NORMALIZED_REFERENCE_DB,
)
print(dict(result.reported_vehicle_sound_levels_db))  # {'1': 78.9, '2a': 81.0, '2b': 83.7}
print(result.reported_index_db)                       # 80.2 dB
print(round(result.difference_db, 2))                 # 1.23 dB above Annex D
```

Each regression reports the slope, the intercept, the correlation, the spread
of the residuals and of the speeds, and the mean speed $10^{\overline{\lg v}}$
(clause 13, item 29). Clause 9.3 asks the reference speed to lie within one
standard deviation of the mean speed for heavy vehicles and one and a half for
cars; the window is judged in $\lg v$, the variable of the fit. The 9.3 window
and the 7.3 counts are kept on the result and, when they fail, emitted as
`StatisticalPassByWarning` rather than raised.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/pass_by_regression_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/pass_by_regression.svg" alt="The 120 cars of the site alone, maximum level against speed on a logarithmic axis, with their regression line, a shaded band from about 72 to 105 km/h marking the window of clause 9.3, and a diamond on the line at the 80 km/h reference speed giving a vehicle sound level of 78.9 dB" width="88%"></picture>

## 3. The index and the reference surface

The **Statistical Pass-By Index** adds the three levels on an energy basis
(9.5):

$$
\mathrm{SPBI} = 10 \lg \left[ W_1 \, 10^{L_1/10}
  + W_{2a} \frac{v_1}{v_{2a}} 10^{L_{2a}/10}
  + W_{2b} \frac{v_1}{v_{2b}} 10^{L_{2b}/10} \right] \ \mathrm{dB}.
$$

It compares surfaces under a standard mix and is not an equivalent level of
any traffic (9.5 NOTE). It is usually quoted as a difference from a reference
surface (clause 10): a real dense asphalt concrete (10.1), a normalized case
set by convention (10.2, with the seven-surface example of Annex D as
`SPB_ANNEX_D_SURFACES_DB` and its average `SPB_NORMALIZED_REFERENCE_DB`), the
same surface at the same age (10.3) or any surface chosen (10.4). The standard
gives no temperature correction (9.4): corrected levels are an input,
`corrected_vehicle_sound_levels_db`, and the index is computed for them too.

## 4. How precise it is

Table 2 expects individual vehicles to scatter by 1,5 dB (cars) and 2,0 dB
(heavy) about $L_\mathrm{veh}$, which leaves 0,3 dB and 0,7 dB of 95 %
confidence interval for 100 cars and 40 heavy vehicles of each type. Each
regression also gives its own interval at the reference speed
(`confidence_interval_db`, Student $t$ with $n - 2$ degrees of freedom), and
the result combines the three into an interval on the index through the
sensitivity of the index to each level, taking the categories as independent.

## 5. The example of Annex E, and its rounding

9.2 asks for all levels to be "calculated to two decimal places and rounded to
one decimal place". The printed regression lines of Annex E give
$L_\mathrm{veh}$ = 78,546, 81,114 and 83,838 dB; carried unrounded, as this
library does, the index is 79,985 dB, reported as 80,0. The example prints
79,9: the index of the three levels as its own report prints them, 78,5, 81,1
and 83,8 dB, which is 79,946 dB, rounded once. The difference is 0,04 dB and
only moves the last digit; the conformance row that pins 79,9 dB runs the
example's own chain through `statistical_pass_by_index`, and the corrected
index (80,1 dB) and the 2,8 dB difference from the 77,3 dB reference are pinned
the same way.

The 77,3 dB reference is described as seven surfaces of the same composition as
Annex D, whose levels index to 78,92 dB with the same weights; the standard does
not say they are one database. The speed spreads of Annex E do not fit its own
regression; see the [errata registry](../../ERRATA.md).

## What this page does not cover

The measurement itself (classifying vehicles, screening pass-bys for the 6 dB
dips of 7.2, the site and weather checks), a temperature correction the
standard does not give, and the Close-Proximity method of ISO 11819-2. Later
editions of ISO 11819-1 were not consulted.

## See also

- [CNOSSOS-EU road traffic source emission](cnossos-road-emission.md): the
  prediction side, where a surface is a correction per vehicle category.
- [In-situ road-surface absorption](../../materials/surfaces/road-absorption.md):
  the ISO 13472 absorption of the surface itself.
- [Errata in published sources](../../ERRATA.md): the two ISO 11819-1 entries.
- API reference: [`environment.sources.statistical_pass_by`](https://jmrplens.github.io/phonometry/reference/api/environment/statistical-pass-by/).
