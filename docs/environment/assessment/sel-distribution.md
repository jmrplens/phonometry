← [Documentation index](../../README.md)

# Impulsive sound exposure statistics (ISO 13474)

A blast, a shot or a detonation a few kilometres away is not heard at one
level: the same charge fired twice reaches the same receiver ten decibels apart
and more, because the wind, the temperature profile and the ground between
them change, and at long range they decide more of the level than the distance
does. ISO 13474:2009 therefore describes the weather as a set of **replica
atmospheres**, each a combination of an atmospheric-absorption class and an
excess-attenuation class with its probability of occurrence, computes the
single-event sound exposure level for each, and turns the list into a
distribution spread for turbulence, from which the long-term level and the
level exceeded by any percentage of the events are read. This page is that
statistical core, run on the example of Annex A: a TOW anti-tank missile
launcher heard at 3 020 m under 27 excess-attenuation classes.

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_distribution_density_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_distribution_density.svg" alt="The step density of the 27 classes of the Annex A example before the turbulent spread, and the smooth density after a 5 dB Gaussian spread, peaking near 30,5 dB with the long-term level LT2 of 37,0 dB marked" width="88%"></picture>

## One number per replica atmosphere

What the statistics work on is one frequency-weighted level per replica, the
energy sum over the bands of Equation (5),
`L_E,w = 10 lg sum_j 10^(0,1 [L_E(j) + w(j)])`, with whatever weighting the
assessment uses. The probability of a replica is the product of the
probabilities of its two classes (Equation (14)).

```python
import numpy as np

from phonometry import environment

source_db = [115.0, 119.0, 134.0, 135.0, 134.0, 136.0, 133.0, 126.0]  # Table A.1
a_weighting_db = [-39.4, -26.2, -16.1, -8.6, -3.2, 0.0, 1.2, 1.0]
print(round(environment.frequency_weighted_sel(source_db, a_weighting_db), 1))  # 139.5

# Table A.3: the A-weighted level of each excess-attenuation class at the
# receiver, and its probability by day and by night; 07:00 to 19:00 is 80 %
# day and 20 % night.
levels_db = [30.5, 31.2, 31.3, 36.1, 38.3, 38.8, 39.2,
             30.8, 31.8, 31.8, 33.7, 40.2, 41.0, 41.6, 42.2, 42.4, 42.7, 43.1,
             28.4, 30.8, 32.2, 42.3, 43.6, 44.5, 45.2, 45.5, 46.1]
day = [0.0360, 0.0053, 0.0003, 0.0731, 0.0951, 0.0634, 0.0,
       0.2037, 0.1087, 0.0184, 0.0279, 0.0001, 0.0, 0.0549, 0.0482, 0.0209, 0.0039, 0.0003,
       0.0, 0.0356, 0.2042, 0.0001, 0.0, 0.0, 0.0, 0.0, 0.0]
night = [0.0, 0.0, 0.0, 0.0664, 0.0966, 0.0962, 0.0,
         0.1151, 0.0295, 0.0, 0.0268, 0.0084, 0.0, 0.0665, 0.0445, 0.0172, 0.0033, 0.0003,
         0.0069, 0.0798, 0.2310, 0.0215, 0.0260, 0.0263, 0.0194, 0.0153, 0.0030]
probabilities = 0.8 * np.asarray(day) + 0.2 * np.asarray(night)
```

## The long-term level, and the rating level with K

Equation (7) is the energy mean over the replicas, and Equation (8) the same
with the ISO 1996-1 adjustment `K` for highly impulsive sound inside the sum:
the rating level the standard hands on to an ISO 1996-1 assessment.

```python
print(round(environment.long_term_sel(levels_db, probabilities), 1))  # 37.0
print(round(environment.long_term_sel(levels_db, probabilities, rating_adjustment_db=12.0), 1))  # 49.0
```

## Classes, subclasses and the spread for turbulence

The levels sorted in increasing order are `M` classes whose boundaries lie
half-way between consecutive levels, the two outer ones mirrored about the end
level (Equations (10) to (13)); each class spreads its probability evenly over
its width (Equation (15)). Each class is then split into `N_sub` subclasses and
each subclass replaced by a Gaussian of standard deviation `sigma` (typically
5 dB), centred `delta_mu = sigma^2 ln 10 / 20` below the subclass so that its
energetic mean stays where it was (Equations (17) to (23)).

```python
dist = environment.sel_distribution(levels_db, probabilities, sigma_db=5.0, subclasses=10)
print(dist.lower_bounds_db[:4].round(2))                              # [27.35 29.45 30.65 30.8 ]
print([round(float(r), 4) for r in dist.class_densities_per_db[:4]])  # [0.0007, 0.024, 1.2399, 0.2222]
print(round(dist.level_shift_db, 3))                                  # 2.878
```

That is Table A.4 of the standard, all 27 rows digit for digit. Two pairs of
classes share a level, 30,8 dB and 31,8 dB; Equation (11) puts their common
boundary at that level and both classes are kept, as the table keeps them.
Only a run of equal levels that would leave a class of no width (three in a
row, or two at an end of the list) is combined into one class.

## Exceedance levels

The probability that an event exceeds `x` is the upper tail of the spread
density (Equation (24)), and the `n`-percent exceedance level is its root
(Equation (25)). The long-term level taken again over the continuous density is
Equation (A.4), Annex A's LT2.

```python
print(dist.exceedance_level([95.0, 50.0, 10.0, 5.0, 1.0]).round(1))  # [21.6 31.5 40.5 43.  47.5]
print(round(dist.distribution_long_term_level_db, 2))                 # 36.96
dist.plot(view="exceedance")
```

<picture><source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_distribution_exceedance_dark.svg"><img src="https://raw.githubusercontent.com/jmrplens/phonometry/main/.github/images/sel_distribution_exceedance.svg" alt="The probability that the single-event level exceeds x, with L95, L50, L10, L5 and L1 marked as Equation (25) gives them and the long-term level LT2 of 37,0 dB" width="88%"></picture>

Two things in Annex A do not follow from its own equations, and both are in
the [errata register](../../ERRATA.md). The running text gives the shift of
Equation (22) as 1,04 dB with a standard deviation of 5 dB; the equation gives
2,878 dB there, 1,04 dB is its value at 3 dB, and the printed LT2 of 37,0 dB and
the curve of Figure A.2 were computed with 2,878 dB. And Figure A.3 prints
21,7; 31,5; 40,6; 43,2 and 48,0 dB for the five exceedance levels, where
Equation (25) gives 21,6; 31,5; 40,5; 43,0 and 47,5 dB. The printed values are
consistent with a curve accumulated from 15 dB, where the drawn curve begins
(the axis starts at 10 dB), when it is fed the 07:00 to 19:00 column of
Table A.3 as printed; fed the full-precision probabilities that reproduce
Table A.4, that reading gives 48,05 dB for `L_1`, which would print 48,1 dB, so
it stays a hypothesis. The library evaluates Equations (22), (24) and (25) as
written.

## What this guide covers

Implemented: the statistical core of ISO 13474:2009, Equations (5), (7), (8),
(10) to (25) and (A.4), with `.plot()` views of the class density, the spread
density and the exceedance curve; Table A.4 of Annex A is reproduced digit for
digit and LT1, LT2 and `L_50` match Figure A.3. Not implemented: the
propagation that produces the level of each replica (clause 6), the
classification of the atmosphere (clause 7), the class probabilities from
meteorological data (clause 8), the ground impedances of Table 1, the source
descriptors of clause 9, the equivalent level over a period of Equation (9)
and the uncertainty budget of Annex B.

## See also

- [Impulsive-sound prominence (NT ACOU 112)](impulsive-sound.md): the other
  assessment of impulsive sound, the prominence of an impulse at a receiver.
- [Environmental levels](environmental-levels.md): the ISO 1996-1 rating
  framework the long-term rating level is offered to.
- [Atmospheric refraction](../propagation/atmospheric-refraction.md): the
  excess attenuation of one sound speed profile, where a replica level starts.
- [Errata in published sources](../../ERRATA.md): the shift printed as 1,04 dB
  and the exceedance levels of Figure A.3.
- API reference: [`environment.assessment.exposure_distribution`](https://jmrplens.github.io/phonometry/reference/api/environment/exposure-distribution/).
