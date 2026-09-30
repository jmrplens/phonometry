---
title: "environment.propagation.software_quality"
description: "Quality assurance of software for outdoor sound: a program's results against the certified ones, and the spread of level differences (ISO 17534-1:2015)."
sidebar:
  label: "software_quality"
---

Quality assurance of software for outdoor sound: a program's results
against the certified ones, and the spread of level differences
(ISO 17534-1:2015).

ISO 17534-1 does not predict a level. It says how a program that implements
an outdoor calculation method (ISO 9613-2, CNOSSOS-EU, a national method)
shows that it implements it correctly, and how its user finds out what the
program's shortcuts cost. Four things in it are arithmetic, and this module
is those four:

* **The test-case comparison** of clause 7.1 and Annex B. A method's test
  cases print, for every band and for the total, a correct result and the
  limits a program's result has to fall inside; Table A.5 puts them at
  +/-0,05 dB round the result given to two decimals. The Test Case Results
  Comparison form (TRC form, Tables B.1 and B.2) lists each result beside its
  limits and answers "Result inside tolerances: yes/no".
  [`verify_calculation_results`](/phonometry/reference/api/environment/software-quality/#verify_calculation_results) fills that column and returns the
  verdict, [`CalculationVerification`](/phonometry/reference/api/environment/software-quality/#calculationverification).
* **The characteristic values of a set of level differences**, Annex C.
  Levels calculated twice at the same receiver points (in the reference
  configuration and in the faster "modified configuration" a noise map is
  actually computed with, 5.2.3 and 7.2) differ, and the standard describes
  the differences by two order statistics of a random sample of them: the
  0,1-quantile $q_{0,1}$ and the 0,9-quantile $q_{0,9}$, so that
  80 % of the differences are expected between the two.
  [`level_difference_quantiles`](/phonometry/reference/api/environment/software-quality/#level_difference_quantiles) sorts the sample, takes the ranking
  positions of [`ranking_positions`](/phonometry/reference/api/environment/software-quality/#ranking_positions-1) and returns
  [`LevelDifferenceQuantiles`](/phonometry/reference/api/environment/software-quality/#leveldifferencequantiles), with the mean and the estimated standard
  deviation C.5 asks for beside them.
* **Where the sample is taken**, C.2 and C.3: a uniform sample of `M` of
  the `N` single points by the ordinal numbers
  $\mathrm{IP}((i - 0{,}5) N / M)$ ([`uniform_sample_indices`](/phonometry/reference/api/environment/software-quality/#uniform_sample_indices)), or
  of points along sound contours of total length `L` at the chainages
  $\mathrm{IP}((i - 0{,}5) L / M)$ ([`contour_sample_chainages_m`](/phonometry/reference/api/environment/software-quality/#contour_sample_chainages_m)),
  with the points closer than 2 m to a source or an obstacle left out first.
* **The precision of a method across programs**, 4.5.2 and A.3: with `M`
  participants of a round robin calculating the same `N` receivers, the
  0,9-quantile of the `N` largest absolute deviations from the mean level
  at each receiver ([`round_robin_precision`](/phonometry/reference/api/environment/software-quality/#round_robin_precision),
  [`RoundRobinPrecision`](/phonometry/reference/api/environment/software-quality/#roundrobinprecision)).

The rest of the standard (the documentation a method has to have, the
declaration of conformity, the QA data format of Annex D) is a set of
requirements on documents, not a calculation, and is not attempted here.

Table C.1 and Formulas (C.1), (C.2): a table, two formulas and a seam
---------------------------------------------------------------------

Table C.1 prints the ranking positions for samples of 20 to 50 values, and in
every one of its 31 rows $R(q_{0,9}) = N + 1 - R(q_{0,1})$: the table
leaves as many values below $q_{0,1}$ as above $q_{0,9}$. For
$N > 50$ the standard gives two formulas instead,

$$
R(q_{0,1}) = \mathrm{IP}\!\left(\frac{N + 4}{10}\right) \tag{C.1}
$$

$$
R(q_{0,9}) = \mathrm{IP}\!\left(\frac{9 N}{10}\right) + 1 \tag{C.2}
$$

The two formulas do not treat the table alike. Formula (C.1) continues its
first column exactly: it reproduces all 31 rows, and it is not the rank
$\mathrm{IP}(0{,}1 N) + 1$ of the empirical 0,1-quantile, from which it
differs at 570 of the 950 sizes from 51 to 1000 (at `N` = 51 that rank is 6,
(C.1) gives 5). Formula (C.2) does not continue the second column: it
reproduces 16 of the 31 rows and gives one rank less for `N` = 21 to 25, 31
to 35 and 41 to 45, and at `N` = 51 it gives 46 where the symmetry of the
table would give 47. Written in the shape of (C.2), the symmetric rule would
read $\mathrm{IP}((9N + 5)/10) + 1$. The break is in (C.2) alone, and
the pair is not one quantile rule: (C.1) is the table's rule and (C.2) is the
rank $\mathrm{IP}(pN) + 1$ of the empirical $p$-quantile.

The standard states the formulas for $N > 50$ only, so nothing it prints
contradicts itself, and none of the pages read here says whether the seam is
deliberate or a slip. Annex C is taken from DIN 45687:2006-05, Annex F,
which prints the same table (Tables F.1 and F.2), the same two formulas ((F.1)
and (F.2)) and the same worked example. Its F.4 bases the ranks of the table on
VDI 3723 Blatt 1 (Table 6, column $L_{x,90}$, for $q_{0,1}$;
Table 5, column $L_{x,10}$, for $q_{0,9}$), and introduces the
formulas with "Falls die Anzahl der Stichproben N > 50 ist, gilt ergänzend zu
VDI 3723 Blatt 1 [15] mit ausreichender Übereinstimmung zu E VDI 2450 Blatt 5
[17]:" (printed folio 35): the formulas supplement VDI 3723 Blatt 1, the source
of the table, in sufficient agreement with E VDI 2450 Blatt 5, a draft on the
quantiles of air-pollutant measurements (item [17] of the bibliography,
folio 38). ISO 17534-1 drops both citations: its C.4 keeps only "based on
$L_{x,90}$ ... and $L_{x,10}$", and the formulas are introduced by
"If the number of random samples N is >50, the following applies".

VDI 3723 Blatt 1:1993-05 bears the table out and stops where it stops. Its
Tables 5 and 6 (printed pages 7 and 8) give the ranking position `k` of the
10 % and the 90 % exceedance levels, $L_{x,10}$ and $L_{x,90}$,
for samples of up to 50 values. From 20 to 50 values the column `k` of Table
6 is the first column of Table C.1 and the column `k` of Table 5 is its
second, row for row, so the symmetry of Table C.1 is already the guideline's.
The guideline gives no formula beyond them: "Die Werte in den Tabellen 4 bis 6
sind auf n = 50 begrenzt", since measurements with a larger sample are hardly
ever made, and for more than 50 values it points to VDI 2450 Blatt 5, a draft
(item [9] of its bibliography, printed page 13), rather than extend its own
rule (page 7). So Formulas (C.1) and (C.2) do not come from VDI 3723 Blatt 1:
DIN 45687 brings them in, in sufficient agreement with E VDI 2450 Blatt 5, and
only that draft could say whether (C.2) was meant to follow it rather than the
symmetry of the table; it has not been read here. A (C.2) that slipped from
the symmetric rule in the national standard and was carried into the
international one, and a (C.2) chosen to agree with E VDI 2450 Blatt 5 while
(C.1) kept the table's rule, both fit the pages that have been read. The seam
is therefore not recorded as an erratum, which needs a defect whose intended
reading the documents establish, and it is not corrected either.

What decides the behaviour is that both standards print (C.2) the same way.
[`ranking_positions`](/phonometry/reference/api/environment/software-quality/#ranking_positions-1) applies what they print: Table C.1 from 20 to 50
values, Formulas (C.1) and (C.2) above. A program that extended the symmetric
rule past 50 would report $q_{0,9}$ one rank higher than this one for
half of all sample sizes, which is exactly the disagreement between two
quality-assured implementations that ISO 17534-1 is written to prevent.

Three readings the text leaves to the implementer
-------------------------------------------------

**Ordinal numbers from zero.** C.2 numbers the `N` remaining single points
consecutively and takes the ordinal numbers
$\mathrm{IP}((i - 0{,}5) N / M)$, `i` from 1 to `M`. Counted from
zero, the ordinals run from $\mathrm{IP}(N / 2M)$ to at most `N - 1`
for every `N` at least `M`, and each sample point sits at the middle of
its `M`-th of the list. Counted from one, the formula would ask for the
ordinal 0, which does not exist, whenever `N` is less than `2M`. This
module counts from zero, which is also the index a Python array uses.

**Chainages in metres.** C.3 lays the contours out "by consecutive
kilometerage" and places the sample points "at the kilometerages"
$\mathrm{IP}((i - 0{,}5) L / M)$ (DIN 45687, F.3: "an den
Kilometrierungen"). A kilometerage is a chainage, a position counted along a
route, and the word names that position, not the unit it is counted in. Taken
in kilometres, the integer part would put every point of a contour shorter
than a kilometre at its start, so the chainage is read in metres, and each
point falls on a whole metre. Two points can share a metre only on contours
shorter than `M` metres, though not on all of them (19,5 m of contour still
give 20 points the metres 0 to 19), and a sample in which two do is refused
rather than returned with repeats.

**The sign and the spread of a difference.** A level difference is the
modified configuration's level minus the reference configuration's (the
level of the contour minus the single-point level, for C.3), so a positive
$q_{0,9}$ is a shortcut that overestimates. The "estimated standard
deviation" of C.5 is the sample standard deviation, with one degree of freedom
fewer than the sample has values.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## CalculationVerification

```python
CalculationVerification(
    results_db: NDArray[np.float64],
    lower_limits_db: NDArray[np.float64],
    upper_limits_db: NDArray[np.float64],
    labels: tuple[str, ...],
)
```

A program's results against the limits of the certified results: the
TRC form of ISO 17534-1:2015 (clause 7.1, Tables B.1 and B.2).

One row per result (a band or a total of a test case): the program's
result, the lower and upper limits of the certified result, and whether
the result is inside them, the "Result inside tolerances yes/no" column.
A limit is included: a deviation that reaches the tolerance "does not
exceed" it.

**Attributes**

| Name | Description |
| :--- | :--- |
| `results_db` | The program's results, in dB, in the reference configuration. |
| `lower_limits_db` | The lower limit of each certified result, in dB. |
| `upper_limits_db` | The upper limit of each certified result, in dB. |
| `labels` | A name for each row (`"63 Hz"`, `"Total"`, `"T03 500 Hz"`). |

### CalculationVerification.deviations_db

*property*

Each result minus the centre of its certified interval, in dB.

### CalculationVerification.failing_labels

*property*

The rows whose result is outside its limits, in order.

### CalculationVerification.inside

*property*

For each row, whether the result is inside its limits (yes/no).

### CalculationVerification.margins_db

*property*

How far each result is from the nearer limit, in dB.

Positive inside the interval, zero on a limit, negative by the amount
a result is outside.

### CalculationVerification.passes

*property*

Whether every result is inside its limits: the verdict of the form.

### CalculationVerification.plot()

```python
CalculationVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw each result against its certified interval, row by row.

Every row is centred on its certified interval, so intervals a
tenth of a decibel wide on levels tens of decibels apart can be read
side by side: the shaded bar is the interval and the marker the
program's deviation from its centre, a dot inside and a cross outside.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the line of result markers. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

## CERTIFIED_RESULT_TOLERANCE_DB

*Constant* (`float`).

```python
CERTIFIED_RESULT_TOLERANCE_DB = 0.05
```

## contour_sample_chainages_m

```python
contour_sample_chainages_m(
    total_length_m: float,
    sample_size: int,
) -> NDArray[np.float64]
```

Where the sample points sit on the sound contours (ISO 17534-1:2015, C.3).

With the contours to be designated laid end to end (their sections within
[`SAMPLE_CLEARANCE_M`](/phonometry/reference/api/environment/software-quality/#sample_clearance_m) of a source or an obstacle left out) to a total
length `L`, the `M` sample points sit at the chainages

$$
\mathrm{IP}\!\left((i - 0{,}5)\,\frac{L}{M}\right), \qquad i = 1, \ldots, M,
$$

read in metres, so that each point falls on a whole metre (the module
docstring says why). The formula is evaluated exactly, in integer
arithmetic on the decimal value of the length, as
$\lfloor (2i - 1) L / 2M \rfloor$: through a rounded quotient
`L/M`, a chainage that is a whole number of metres can come out a metre
short (115 m for `L` = 184 m and `M` = 20, where `L/M` is 9,2), and
through the binary fraction nearest a decimal length such as 22,4 m, so
can one that the decimal length puts on a whole metre. The level of the
contour there is compared with a single-point calculation at the same
place, and the differences go to [`level_difference_quantiles`](/phonometry/reference/api/environment/software-quality/#level_difference_quantiles).

**Parameters**

| Name | Description |
| :--- | :--- |
| `total_length_m` | `L`, the length of the contours that remain, in metres, long enough that no two points share a whole metre, which is always so from `sample_size` metres on. |
| `sample_size` | `M`, at least [`MINIMUM_SAMPLE_SIZE`](/phonometry/reference/api/environment/software-quality/#minimum_sample_size). |

**Returns:** The `M` chainages, in metres, in increasing order.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a sample smaller than 20, a length that is not a finite, positive number (a string or a bool included), or contours so short that two points would fall on the same whole metre, which happens only below `M` metres. |

## level_difference_quantiles

```python
level_difference_quantiles(
    level_differences_db: ArrayLike,
) -> LevelDifferenceQuantiles
```

The 0,1- and 0,9-quantiles of a sample of level differences
(ISO 17534-1:2015, C.4).

The sample is sorted in ascending order and the values at the ranking
positions of [`ranking_positions`](/phonometry/reference/api/environment/software-quality/#ranking_positions-1) are the two characteristic values:
it "shall be expected that 10 % of all level differences in the
calculation area are each below" $q_{0,1}$ "and above"
$q_{0,9}$. For a modified configuration judged against the
reference configuration (5.2.3, 7.2), pass the modified configuration's
levels minus the reference configuration's at the same sample points
([`uniform_sample_indices`](/phonometry/reference/api/environment/software-quality/#uniform_sample_indices) chooses them).

The worked example that follows Table C.1: the 25 differences it prints
give $R(q_{0,1}) = 2$, $R(q_{0,9}) = 24$,
$q_{0,1} = -1$ dB and $q_{0,9} = 3$ dB.

**Parameters**

| Name | Description |
| :--- | :--- |
| `level_differences_db` | The sample of level differences, in dB, in any order; at least [`MINIMUM_SAMPLE_SIZE`](/phonometry/reference/api/environment/software-quality/#minimum_sample_size) values. |

**Returns:** A [`LevelDifferenceQuantiles`](/phonometry/reference/api/environment/software-quality/#leveldifferencequantiles).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for fewer than 20 values, a non-finite value or an input that is not one-dimensional. |

## LevelDifferenceQuantiles

```python
LevelDifferenceQuantiles(sorted_differences_db: NDArray[np.float64])
```

The characteristic values of a sample of level differences
(ISO 17534-1:2015, C.4 and C.5).

Built by [`level_difference_quantiles`](/phonometry/reference/api/environment/software-quality/#level_difference_quantiles). Only the sorted sample is
stored; the ranking positions, the two quantiles, the mean and the
standard deviation are read from it, so they cannot disagree with it.

**Attributes**

| Name | Description |
| :--- | :--- |
| `sorted_differences_db` | The sample of level differences, sorted in ascending order as C.4 sorts it, in dB. At least [`MINIMUM_SAMPLE_SIZE`](/phonometry/reference/api/environment/software-quality/#minimum_sample_size) values. |

### LevelDifferenceQuantiles.from_table

*property*

Whether the ranks were read from Table C.1 rather than (C.1), (C.2).

### LevelDifferenceQuantiles.mean_db

*property*

The average of the difference group, in dB.

C.5: the value "specified for considering a systematic deviation".

### LevelDifferenceQuantiles.plot()

```python
LevelDifferenceQuantiles.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the sorted sample by rank, with the two quantiles marked.

Each difference is a point at its ranking position; the two ranks
of C.4 and the values they pick are marked, and the band between
$q_{0,1}$ and $q_{0,9}$ that holds the central 80 % is
shaded.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the line of sample points. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### LevelDifferenceQuantiles.q01_db

*property*

$q_{0,1}$, the value at rank $R(q_{0,1})$, in dB.

C.2, NOTE 2: 10 % of all the differences are expected below it.

### LevelDifferenceQuantiles.q09_db

*property*

$q_{0,9}$, the value at rank $R(q_{0,9})$, in dB.

C.2, NOTE 2: 10 % of all the differences are expected above it.

### LevelDifferenceQuantiles.rank_q01

*property*

$R(q_{0,1})$, the ranking position of the 0,1-quantile.

### LevelDifferenceQuantiles.rank_q09

*property*

$R(q_{0,9})$, the ranking position of the 0,9-quantile.

### LevelDifferenceQuantiles.sample_size

*property*

`N`, the number of level differences in the sample.

### LevelDifferenceQuantiles.standard_deviation_db

*property*

The estimated standard deviation of the difference group, in dB.

C.5: the uncertainty to carry into an error-propagation calculation
by ISO/IEC Guide 98-3. The sample standard deviation, with `N - 1`
degrees of freedom.

## MINIMUM_SAMPLE_SIZE

*Constant* (`int`).

```python
MINIMUM_SAMPLE_SIZE = 20
```

## RANKING_POSITIONS

*Constant* (`mapping`).

```python
RANKING_POSITIONS = {20: (2, 19), 21: (2, 20), 22: (2, 21), 23: (2, 22), 24: (2, 23), 25: (2, 24), 26: (3, 24), 27: (3, 25), 28: (3, 26), 29: (3, 27), 30: (3, 28), 31: (3, 29), 32: (3, 30), 33: (3, 31), 34: (3, 32), 35: (3, 33), 36: (4, 33), 37: (4, 34), 38: (4, 35), 39: (4, 36), 40: (4, 37), 41: (4, 38), 42: (4, 39), 43: (4, 40), 44: (4, 41), 45: (4, 42), 46: (5, 42), 47: (5, 43), 48: (5, 44), 49: (5, 45), 50: (5, 46)}
```

## ranking_positions

```python
ranking_positions(sample_size: int) -> tuple[int, int]
```

Ranking positions of the 0,1- and 0,9-quantiles (ISO 17534-1 C.4).

For a sample of `N` values sorted in ascending order, the positions,
counted from 1, of the value taken as the 0,1-quantile and of the value
taken as the 0,9-quantile. Table C.1 ([`RANKING_POSITIONS`](/phonometry/reference/api/environment/software-quality/#ranking_positions)) from 20 to
50 values; above 50, Formulas (C.1) and (C.2),

$$
R(q_{0,1}) = \mathrm{IP}\!\left(\frac{N + 4}{10}\right), \qquad R(q_{0,9}) = \mathrm{IP}\!\left(\frac{9 N}{10}\right) + 1,
$$

with IP the integer part, evaluated here in integer arithmetic so that no
rounding of `9N/10` can move a rank. The table leaves as many values
below the one quantile as above the other. Formula (C.1) continues the
table's first column, but Formula (C.2) does not continue its second: it
leaves one more value above $q_{0,9}$ whenever the last digit of
`N` is 1 to 5. ISO 17534-1 and DIN 45687, from which Annex C was taken,
both print (C.2) this way, and neither says whether the seam is deliberate;
the module docstring gives what the two documents do say, and why the
function applies the print.

**Parameters**

| Name | Description |
| :--- | :--- |
| `sample_size` | `N`, the number of values in the sample, at least [`MINIMUM_SAMPLE_SIZE`](/phonometry/reference/api/environment/software-quality/#minimum_sample_size). |

**Returns:** `(R(q0,1), R(q0,9))`.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a sample smaller than 20, which C.2 does not allow and Table C.1 does not cover, or a count that is not a whole number. |

## RECOMMENDED_SAMPLE_RATIO

*Constant* (`float`).

```python
RECOMMENDED_SAMPLE_RATIO = 0.01
```

## round_robin_precision

```python
round_robin_precision(levels_db: ArrayLike) -> RoundRobinPrecision
```

The precision of a method from a round robin of programs
(ISO 17534-1:2015, 4.5.2 and A.3).

**Parameters**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L_{n,m}$, the level each of `M` participants calculated at each of `N` receivers, in dB: shape `(N, M)`, at least 20 receivers and two participants. |

**Returns:** A [`RoundRobinPrecision`](/phonometry/reference/api/environment/software-quality/#roundrobinprecision); its `q09_db` is the result of the round robin.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a matrix of the wrong shape, one that is not numeric, or one with a complex or a non-finite level. |

## RoundRobinPrecision

```python
RoundRobinPrecision(levels_db: NDArray[np.float64])
```

The precision of a method in a round robin of programs
(ISO 17534-1:2015, 4.5.2 and A.3, Example 1).

`M` participants calculate the same `N` receivers with the same
method. At receiver `n` the mean $\bar L_n$ is the arithmetic mean
of the `M` levels, each participant deviates from it by
$dL_{n,m} = L_{n,m} - \bar L_n$, and $|dL_n|_{\max}$ is the
largest of the `M` absolute deviations. "The result of such a round
robin test is the quantile $q_{0,9}$ according to C.4 of the `N`
maximal absolute differences."

Built by [`round_robin_precision`](/phonometry/reference/api/environment/software-quality/#round_robin_precision). Only the levels are stored;
everything else is read from them.

**Attributes**

| Name | Description |
| :--- | :--- |
| `levels_db` | $L_{n,m}$, shape `(N, M)`: one row per receiver, one column per participant, in dB. |

### RoundRobinPrecision.deviations_db

*property*

$dL_{n,m} = L_{n,m} - \bar L_n$, shape `(N, M)`, in dB.

### RoundRobinPrecision.max_abs_deviations_db

*property*

$|dL_n|_{\max}$, the largest absolute deviation at each receiver, in dB.

### RoundRobinPrecision.mean_levels_db

*property*

$\bar L_n$, the arithmetic mean at each receiver, in dB.

### RoundRobinPrecision.participants

*property*

`M`, the number of participants.

### RoundRobinPrecision.plot()

```python
RoundRobinPrecision.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the distribution of $|dL_n|_{\max}$, as Figure A.3 does.

A histogram of the largest absolute deviations with $q_{0,9}$
marked. Figure A.3 counts them in classes 0,1 dB wide; here the
class width is the narrowest round one (0,05 dB, 0,1 dB, 0,2 dB and
so on) that draws the widest deviation in at most 25 classes.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the histogram bars. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

### RoundRobinPrecision.q09_db

*property*

$q_{0,9}$ of the `N` values of $|dL_n|_{\max}$, in dB.

"A value showing up the precision of the calculation method applied
with the different software applied" (A.3, Example 1).

### RoundRobinPrecision.rank_q09

*property*

$R(q_{0,9})$ for `N` receivers ([`ranking_positions`](/phonometry/reference/api/environment/software-quality/#ranking_positions-1)).

### RoundRobinPrecision.receivers

*property*

`N`, the number of receiver positions.

## SAMPLE_CLEARANCE_M

*Constant* (`float`).

```python
SAMPLE_CLEARANCE_M = 2.0
```

## SoftwareQualityWarning

A sample for Annex C of ISO 17534-1 is thinner than C.2 recommends.

Emitted by [`uniform_sample_indices`](/phonometry/reference/api/environment/software-quality/#uniform_sample_indices) when fewer than one point in a
hundred is drawn ([`RECOMMENDED_SAMPLE_RATIO`](/phonometry/reference/api/environment/software-quality/#recommended_sample_ratio)). The sample is still
returned: the ratio is a recommendation, and the quantiles of a thinner
sample are defined, only less representative of the map.

## uniform_sample_indices

```python
uniform_sample_indices(
    point_count: int,
    sample_size: int,
    *,
    horizontal_clearances_m: ArrayLike | None = None,
) -> NDArray[np.intp]
```

The single points of a uniform random sample (ISO 17534-1:2015, C.2).

Of the `N` single points that remain once those closer than
[`SAMPLE_CLEARANCE_M`](/phonometry/reference/api/environment/software-quality/#sample_clearance_m) to a source or an obstacle are left out, the
sample of size `M` takes the points of ordinal number

$$
\mathrm{IP}\!\left((i - 0{,}5)\,\frac{N}{M}\right), \qquad i = 1, \ldots, M,
$$

counted from zero (the module docstring says why), evaluated in integer
arithmetic as $\lfloor (2i - 1) N / 2M \rfloor$. A sample of fewer
than one point in a hundred is returned with a
[`SoftwareQualityWarning`](/phonometry/reference/api/environment/software-quality/#softwarequalitywarning), the ratio C.2 recommends.

**Parameters**

| Name | Description |
| :--- | :--- |
| `point_count` | How many single points there are (grid receivers, points along a street), before any is left out. |
| `sample_size` | `M`, the random sample size, at least [`MINIMUM_SAMPLE_SIZE`](/phonometry/reference/api/environment/software-quality/#minimum_sample_size) and at most the number of points that remain. |
| `horizontal_clearances_m` | Optional, one value per point: its horizontal distance to the nearest source or obstacle, in metres. The points at less than 2 m are left out before numbering; without it, every point takes part. |

**Returns:** The indices of the sampled points among the `point_count` points, in increasing order.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a sample smaller than 20 or larger than the points that remain, or clearances that are not one finite, non-negative value per point. |

## verify_calculation_results

```python
verify_calculation_results(
    results_db: ArrayLike,
    lower_limits_db: ArrayLike,
    upper_limits_db: ArrayLike,
    *,
    labels: Sequence[str] | None = None,
) -> CalculationVerification
```

Is a program's result inside the limits of every certified result?
(ISO 17534-1:2015, clause 7.1 and Annex B)

The comparison a user makes with each new installation or update, and a
producer declares in the TRC form of the declaration of conformity:
every result a test case certifies, calculated by the program in its
reference configuration, against the upper and lower limits the test case
prints. A test case of ISO/TR 17534-3 prints a correct result to two
decimals and, by Table A.5, a result is correct within
[`CERTIFIED_RESULT_TOLERANCE_DB`](/phonometry/reference/api/environment/software-quality/#certified_result_tolerance_db) of it, so its limits are the
certified result minus and plus 0,05 dB. Table B.2 is the worked form:
eight octave bands and a total of the test case "T XX", every result
inside.

**Parameters**

| Name | Description |
| :--- | :--- |
| `results_db` | The program's results, in dB, one per row. |
| `lower_limits_db` | The lower limit of each certified result, in dB. |
| `upper_limits_db` | The upper limit of each certified result, in dB. |
| `labels` | A name for each row; by default `"1"`, `"2"`, and so on. |

**Returns:** A [`CalculationVerification`](/phonometry/reference/api/environment/software-quality/#calculationverification), whose `passes` is the verdict and `inside` the column of the form.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for columns of different lengths, a non-finite value or a lower limit above its upper limit. |
