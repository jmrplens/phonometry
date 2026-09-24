← [Documentation index](../../README.md)

# Soundscape analysis (ISO/TS 12913)

A sound level tells how much sound arrives at a place, not whether the people
there find it pleasant, busy, calming or annoying. A **soundscape** is the
acoustic environment as a person perceives it, in context (ISO 12913-1), and
this is the first page of the library whose input is a **questionnaire**
rather than a signal. ISO/TS 12913-2:2018 prints the questionnaires and the
minimum a study reports; ISO/TS 12913-3 turns the answers into numbers, places
each site on a two-dimensional model of how pleasant and how eventful it
sounds, correlates the answers with the acoustic data, and analyses a binaural
recording of the same place.

This page implements the **2019 edition of ISO/TS 12913-3**. A 2025 edition
exists that revises Annex A, where the pleasantness and eventfulness formulas
are; it has not been read for this implementation, so a study citing it should
check those formulas against it.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/soundscape_pleasantness_eventfulness_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/soundscape_pleasantness_eventfulness.svg" alt="Eleven London sites on the two-dimensional model of ISO/TS 12913-3 Figure A.1, pleasantness against eventfulness with the eight attribute axes, and the rank of each site's pleasantness against the rank of its LAeq, r spearman = minus 0.638, p = 0.035" width="100%"></picture>

## The questionnaire and its scale values

Method A of ISO/TS 12913-2 (C.3.1) has four parts on five boxes each: the
sources heard (Figure C.2, or the three-source Figure C.3), eight attributes of
the perceived affective quality (Figure C.4), the overall quality (Figure C.5)
and the appropriateness (Figure C.6). They are published as read-only tables,
text as printed, with the scale values of ISO/TS 12913-3 Table A.1: parts 1
and 4 run 1 to 5 from the left-hand box, parts 2 and 3 run **5 to 1**.

```python
from phonometry import environment

part2 = environment.METHOD_A_SCALES[2]
print(part2.figure, part2.categories[0], part2.scale_values)  # C.4 Strongly agree (5, 4, 3, 2, 1)
print(environment.method_a_scale_values([1, 2, 5], part=2))  # [5. 4. 1.]

answers = {"pleasant": [5, 4, 4, 2, 5], "annoying": [1, 2, 1, 4, 1]}
summary = environment.method_a_summary(
    answers, part=2, sites=["park", "park", "park", "road", "road"]
)
print(summary.medians.tolist())   # [[4.0, 1.0], [3.5, 2.5]]
print(summary.ranges.tolist())    # [[1.0, 1.0], [3.0, 3.0]]
```

Every Method A scale is ordinal, so A.2 reports the median per site and item
and the range. The questions of Figures C.2 to C.4 print "to what extend" and
"reponse alternative"; the tables keep them, and the
[errata register](../../ERRATA.md) has the entry.

## Pleasantness and eventfulness

Formulas (A.1) and (A.2) project the eight attributes onto two axes, with
`cos 45°` weighting the two rotated ones:
`P = (p - a) + cos 45° (ca - ch) + cos 45° (v - m)` and
`E = (e - u) + cos 45° (ch - ca) + cos 45° (v - m)`. Equal answers sit at the
origin and the extremes are `±(4 + √32) = ±9.66`; dividing by `4 + √32` maps
the coordinates to ±1. The site point is the formulas applied to the site
median of each attribute (A.2), or to its mean with `central_tendency="mean"`,
which is the mean of the respondents' coordinates only when nobody left an
attribute blank. The eleven London sites below were surveyed almost entirely
with the English questionnaire; ten answers at four sites came from the
database's Spanish version and are counted too.

```python
sites = ["Camden Town", "Euston Tap", "Marchmont Garden", "Pancras Lock",
         "Regent's Park Fields", "Regent's Park Japan", "Russell Square",
         "St Paul's Cross", "St Paul's Row", "Tate Modern", "Torrington Square"]
# Site medians of the eight attributes (International Soundscape Database v1.0,
# CC BY 4.0), in the order of Figure C.4: pleasant, chaotic, vibrant,
# uneventful, calm, annoying, eventful, monotonous.
medians = [
    [3, 4, 4, 2, 2, 3, 4, 3], [2, 4, 3, 3, 2, 3, 3, 3], [4, 2, 3, 3, 4, 2, 3, 2],
    [4, 3, 3, 2, 4, 2, 3, 2], [5, 2, 3, 3, 4, 1, 3, 2], [5, 1, 4, 3, 5, 1, 3, 2],
    [4, 2, 4, 2, 4, 1, 3, 2], [4, 2.5, 4, 2, 4, 2, 3, 2], [4, 3, 4, 2, 3, 2, 3, 3],
    [4, 3, 4, 2, 4, 2, 4, 2], [3, 4, 4, 3, 2, 3, 3, 2],
]
laeq_db = [69.96, 69.45, 55.14, 59.02, 53.12, 59.74, 66.12, 61.83, 63.34, 63.00, 63.51]

pe = environment.pleasantness_eventfulness(medians, sites=sites)
print(round(pe.normalized_pleasantness[5], 2), round(pe.normalized_eventfulness[5], 2))  # 0.85 -0.15
pe.plot()  # the model of Figure A.1
```

A.3 says the formulas process "the results from part 3"; the attributes they
read are part 2, which is what the library uses (see the
[errata register](../../ERRATA.md)).

## Linking the ratings to the acoustic data

For ordinal data A.4 prescribes Spearman's coefficient, Formula (A.3) without
ties and (A.4) with them; for interval data B.3 prescribes Pearson's, Formulas
(B.1) and (B.2), whose covariance divides by `n`. Both come with the
probability value of the Student statistic with `n - 2` degrees of freedom.

```python
rho = environment.spearman_rank_correlation(pe.pleasantness, laeq_db)
print(rho.formula, round(rho.coefficient, 3), round(rho.p_value, 3))  # (A.4) -0.638 0.035
r = environment.pearson_correlation(pe.pleasantness, laeq_db)
print(r.formula, round(r.coefficient, 3), round(r.p_value, 3))  # (B.1) -0.66 0.027
```

Formula (A.3) is printed with a stray factor 1 before its fraction, read as the
typesetting remnant it is; the where-list of (A.4) garbles the definitions of
the tie counts `t_j` and `k(x)`, read as the size and the number of the groups
of tied values; and the where-list of (B.2) prints `x_I` for `x_i`.

## Method B

The continuous-category scales of Figure C.7 take a value from 1 to 5 with one
decimal; B.2 reports their mean, standard deviation and 95 % confidence
interval per site, and the median and range of the rank of each recognised
source. The text of C.3.2.3 speaks of three scales where the figure prints
four; `METHOD_B_SCALES` holds all four.

```python
print(environment.method_b_scale_values([0.0, 0.37, 1.0]))  # [1.  2.5 5. ]
ratings = {"How loud is it here?": [3.9, 4.2, 3.1, 4.4, 3.6, 4.0]}
b = environment.method_b_summary(ratings)
print(round(b.confidence_lower[0, 0], 2), round(b.confidence_upper[0, 0], 2))  # 3.38 4.35
```

## The binaural analysis

Every metric of ISO/TS 12913-3 Table D.1 is determined at each ear of an
equalized, calibrated two-channel recording, and the higher of the two is the
representative value (D.2): the levels `LAeq,T`, `LCeq,T`, `LAF5,T`,
`LAF95,T`; the ISO 532-1 loudness `N5`, `Naverage`, `Nrmc`, `N95` and the ratio
`N5/N95` (`Nrmc` by the formula of the NOTE under ISO/TS 12913-2 A.3 f), whose
text says "the exponent 3" where the formula applies 1/3); and the ECMA-418-2
tonality, roughness `R10`, `R50` and fluctuation
strength `F10`, `F50`. The time-varying sharpness `S5`, `Saverage`, `S95` is
reported as not implemented, because the library's DIN 45692 sharpness is
stationary. A recording under 3 min or sampled below 44.1 kHz raises a
`SoundscapeWarning` (ISO/TS 12913-2 D.3, D.6).

```python
import warnings

import numpy as np

fs = 48_000
rng = np.random.default_rng(12913)
t = np.arange(8 * fs) / fs
background = 0.02 * rng.standard_normal(t.size)
swell = np.exp(-0.5 * ((t - 4.0) / 0.9) ** 2)
vehicle = 0.08 * rng.standard_normal(t.size)
left = background + swell * vehicle
right = 0.9 * background + 10 ** (-3 / 20) * np.roll(swell, int(0.3 * fs)) * vehicle
with warnings.catch_warnings():
    warnings.simplefilter("ignore", environment.SoundscapeWarning)
    bi = environment.binaural_indicators(
        np.vstack([left, right]), fs, parameters=("sound_pressure_level", "loudness", "sharpness")
    )
print(round(bi.representative("LAeq,T"), 1), round(bi.representative("N5"), 1))  # 63.5 22.2
print(sorted(bi.not_implemented))  # ['S5', 'S95', 'Saverage']
bi.plot(parameter="loudness")
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/soundscape_binaural_indicators_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/soundscape_binaural_indicators.svg" alt="The sound pressure levels and the loudness of Table D.1 at the left and right ears of a synthetic street recording, with the higher ear marked as the representative value and N5/N95 of 2.27 and 2.01" width="100%"></picture>

## The report

`SoundscapeReport` holds the minimum reporting requirements of ISO/TS 12913-2
Annex A (normative): the participants (A.2), the acoustic environment with the
seven results of A.3 f), which `bi.reporting_results()` provides, and the data
collection (A.4). A record with a required item missing is refused, and the
error names its clause.

## What this guide covers

Implemented: the scale values and ordinal statistics of ISO/TS 12913-3 Annex
A, Formulas (A.1) to (A.4) with probability values, the Method B statistics and
Formulas (B.1) and (B.2) of Annex B, the binaural metrics of Table D.1 the
library implements with the representative values of D.2, the questionnaires
of ISO/TS 12913-2 Annex C, its Annex D recording checks and its Annex A
reporting record. Not implemented: the 2025 edition of ISO/TS 12913-3, the
time-varying sharpness of Table D.1, the qualitative analyses, triangulation,
laboratory studies, clustering and psychoacoustic maps, and the binaural
measurement protocol of ISO/TS 12913-2 D.7.

## See also

- [Environmental levels](environmental-levels.md): the ISO 1996-1 framework
  the levels of Table D.1 are defined in.
- [Integrated and statistical levels](../../signals/levels/levels.md): the
  level and percentile functions the binaural analysis reads at each ear.
- [Errata in published sources](../../ERRATA.md): part 3 for part 2, the stray
  factor of Formula (A.3), the where-lists of (A.4) and (B.2), the exponent of
  the Nrmc NOTE, three scales for four, and the questionnaire misspellings.
- API reference: [`environment.assessment.soundscape`](https://jmrplens.github.io/phonometry/reference/api/environment/soundscape/)
  and [`environment.assessment.soundscape_binaural`](https://jmrplens.github.io/phonometry/reference/api/environment/soundscape-binaural/).
