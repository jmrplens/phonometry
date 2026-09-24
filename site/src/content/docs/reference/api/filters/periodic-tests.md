---
title: "filters.periodic_tests"
description: "Periodic tests of band filters (IEC 61260-3:2016): test frequencies and verdict."
sidebar:
  label: "periodic_tests"
---

Periodic tests of band filters (IEC 61260-3:2016): test frequencies and verdict.

IEC 61260-3:2016 is the short list of tests a laboratory runs on a working
octave-band or fractional-octave-band filter every year or two, to show that
it still meets the class it was built to under IEC 61260-1:2014. This module
gives two things for it.

**The test frequencies of Clause 13.** The relative attenuation of three
filters of the set is measured at 15 normalized frequencies, an abbreviation
of the Table 1 mask of IEC 61260-1 (13.3, NOTE 1). Formula (1) carries the
octave-band frequency parameters $R_k$ of its Table 1 ($G^0$,
$G^{1/8}$, $G^{1/4}$, $G^{3/8}$, $G$, $G^2$,
$G^3$, $G^4$) to a bandwidth designator $1/b$,

$$
\Omega_k = 1 + \frac{G^{1/(2b)} - 1}{G^{1/2} - 1}\,(R_k - 1), \qquad k = 0, 1, \ldots, 7,
$$

and Formula (2) mirrors them below the mid-band, $\Omega_{-k} = 1/\Omega_k$, with the same acceptance limits. For octave bands
$\Omega_k = R_k$ (NOTE 2). [`periodic_test_frequencies`](/phonometry/reference/api/filters/periodic-tests/#periodic_test_frequencies) returns
the 15, for any $b$; Annex C prints them for one-third-octave filters
to five decimals, and they are reproduced there to the last digit. It is the
same mapping as Formula (9) of IEC 61260-1 that
[`phonometry.filters.class_limits`](/phonometry/reference/api/filters/compliance/#class_limits) uses for its breakpoints.

**The verdict on a laboratory's results.** [`verify_filter_periodic`](/phonometry/reference/api/filters/periodic-tests/#verify_filter_periodic)
grades what a laboratory measured, clause by clause, by the conformance rule
of IEC TC 29 that IEC 61260-3 5.1 states
([`phonometry.metrology.verify_conformance`](/phonometry/reference/api/metrology/conformance/#verify_conformance)): the measured deviation
within the acceptance limit **and** the actual expanded uncertainty within the
maximum permitted by Annex B of IEC 61260-1:2014, both inclusive. The clauses
it grades are the ones that are a measured deviation with such a pair:

* **10.2**, the relative attenuation at the exact mid-band frequency of every
  filter of the set: $\pm 0.4$ dB (class 1) or $\pm 0.6$ dB
  (class 2), with the Annex B maximum for a relative attenuation of 2 dB or
  less, 0.20 dB;
* **10.3**, the alternative for time-invariant filters: the deviation of the
  time-averaged output of an exponential sweep from Formula (17) of
  IEC 61260-1, within the same limits (10.3.6), with the Annex B maximum for
  time-invariant operation, 0.20 dB (9.2.3);
* **11.7**, the level linearity deviation of three filters over the linear
  operating range: the limits of IEC 61260-1 5.13.3 ($\pm 0.5$ dB or
  $\pm 0.6$ dB) down to 40 dB below the upper boundary and of 5.13.4
  ($\pm 0.7$ dB or $\pm 0.9$ dB) further down, with the Annex B
  maxima 0.20 dB and 0.35 dB on either side of those 40 dB;
* **11.9**, the level linearity on every other level range, 30 dB below its
  upper boundary: 5.13.3, 0.20 dB;
* **13**, the relative attenuation of the same three filters at the 15 test
  frequencies against Table 1 of IEC 61260-3, with the Annex B maxima 0.20 dB,
  0.30 dB and 0.50 dB for a relative attenuation up to 2 dB, up to 40 dB and
  above 40 dB.

A stop-band row of Table 1 prints a minimum and $+\infty$ ("+70; +∞"),
an acceptance interval with no upper limit, which is how it is judged.

**What 5.3 makes unusable.** A result whose actual uncertainty exceeds the
maximum permitted "shall not be used to evaluate conformance to this standard
for periodic testing" (5.3). Such a result is neither a pass nor, by itself, a
failure of the filter; [`FilterPeriodicVerification.unusable`](/phonometry/reference/api/filters/periodic-tests/#filterperiodicverificationunusable) lists them
and the verdict does not pass while any is left.

**What a pass here is, and is not.** It is a verdict on the numbers put in.
The checks that are not a deviation with a maximum-permitted uncertainty are
the laboratory's own record: the instruction manual and markings of Clause 4,
the preliminary inspection of Clause 6, the power supply of Clause 7, the
environmental conditions of Clause 8, the overload indications of 11.5 and
11.8, and the self-generated noise of Clause 12, which compares the output
with the input short-circuited against the lower limit the manual states and
has no maximum-permitted uncertainty in Annex B. And even a filter that
passes every periodic test supports no general conclusion about the
specifications of IEC 61260-1 unless the model's pattern approval under
IEC 61260-2 is publicly available (1.5): the statement the verdict writes is
the one Clause 14 k) or l) prescribes for the case at hand.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## FilterPeriodicMeasurements

```python
FilterPeriodicMeasurements(
    midband_attenuations_db: Sequence[float] | None = None,
    midband_uncertainties_db: Sequence[float] | None = None,
    bandwidth_deviations_db: Sequence[float] | None = None,
    bandwidth_uncertainties_db: Sequence[float] | None = None,
    set_midband_frequencies_hz: Sequence[float] | None = None,
    linearity_deviations_db: Sequence[float] | None = None,
    linearity_levels_below_upper_db: Sequence[float] | None = None,
    linearity_uncertainties_db: Sequence[float] | None = None,
    range_linearity_deviations_db: Sequence[float] | None = None,
    range_linearity_uncertainties_db: Sequence[float] | None = None,
    relative_attenuations_db: Sequence[Sequence[float]] | None = None,
    relative_attenuation_uncertainties_db: Sequence[Sequence[float]] | None = None,
    tested_midband_frequencies_hz: Sequence[float] | None = None,
)
```

What a laboratory measured in the periodic tests of IEC 61260-3:2016.

Every result comes with the actual expanded uncertainty the laboratory
calculated for it, for a coverage probability of 95 % (5.2), in the same
position of a sequence of the same length. A clause left at `None` was
not measured. Everything is in decibels.

**Attributes**

| Name | Description |
| :--- | :--- |
| `midband_attenuations_db` | 10.2: the relative attenuation at the exact mid-band frequency of every filter of the set. |
| `midband_uncertainties_db` | Their uncertainties. |
| `bandwidth_deviations_db` | 10.3: for a time-invariant filter, the deviation of every filter's time-averaged output of an exponential sweep from $L_\mathrm{c}$ of IEC 61260-1 Formula (17). |
| `bandwidth_uncertainties_db` | Their uncertainties. |
| `set_midband_frequencies_hz` | Optional labels for the 10.2 and 10.3 results: the exact mid-band frequency of each filter, in order. |
| `linearity_deviations_db` | 11.7: the level linearity deviations of the three selected filters on the reference level range, at every level measured. |
| `linearity_levels_below_upper_db` | For each of them, how far below the upper boundary of the linear operating range the input level was ($L_\mathrm{u} - L$, negative above it), which decides between the limits of 5.13.3 and 5.13.4 and the maxima of Annex B. |
| `linearity_uncertainties_db` | Their uncertainties. |
| `range_linearity_deviations_db` | 11.9: the level linearity deviation 30 dB below the upper boundary of every other level range. |
| `range_linearity_uncertainties_db` | Their uncertainties. |
| `relative_attenuations_db` | 13: for each of the three selected filters, a row of 15 relative attenuations at the test frequencies of [`periodic_test_frequencies`](/phonometry/reference/api/filters/periodic-tests/#periodic_test_frequencies), `k = -7 .. 7`, NaN where 13.4 drops the frequency. |
| `relative_attenuation_uncertainties_db` | The same shape, NaN in the same places. |
| `tested_midband_frequencies_hz` | Optional labels for the 11.7 and 13 results: the exact mid-band frequency of each selected filter. |

## FilterPeriodicVerification

```python
FilterPeriodicVerification(
    filter_class: int,
    pattern_approval_public: bool,
    measurements: FilterPeriodicMeasurements,
    clauses: tuple[PeriodicTestClause, ...],
)
```

The IEC 61260-3:2016 verdict on the periodic tests of a band filter.

**Attributes**

| Name | Description |
| :--- | :--- |
| `filter_class` | The class the filter was tested as, 1 or 2. |
| `pattern_approval_public` | Whether evidence is publicly available that the model passed the pattern evaluation of IEC 61260-2 (14 c). |
| `measurements` | The record the verdict was reached on. |
| `clauses` | One [`PeriodicTestClause`](/phonometry/reference/api/filters/periodic-tests/#periodictestclause) per clause measured, in the order of the standard. |

### FilterPeriodicVerification.clause()

```python
FilterPeriodicVerification.clause(clause: str) -> PeriodicTestClause
```

The verdict on one clause.

**Parameters**

| Name | Description |
| :--- | :--- |
| `clause` | `"10.2"`, `"10.3"`, `"11.7"`, `"11.9"` or `"13"`. |

**Returns:** Its [`PeriodicTestClause`](/phonometry/reference/api/filters/periodic-tests/#periodictestclause).

**Raises**

| Exception | When |
| :--- | :--- |
| KeyError | when that clause was not measured. |

### FilterPeriodicVerification.failed

*property*

`(clause, result)` for every result outside its acceptance limits.

### FilterPeriodicVerification.missing

*property*

The clauses a complete periodic test grades that were not measured.

`"10"` (10.2 or 10.3), `"11.7"` and `"13"`; 11.9 applies only to
a filter with more than one level range and is never missing.

### FilterPeriodicVerification.passes

*property*

Whether the filter completed the periodic tests successfully.

Every clause a complete test grades was measured, and every result
demonstrates conformance: no deviation outside its limits and no
uncertainty above its maximum.

### FilterPeriodicVerification.plot()

```python
FilterPeriodicVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw every result's margin to its acceptance limits, clause by clause.

One marker per result, grouped by clause: the distance from the
deviation to its nearer acceptance limit, with the actual uncertainty
as its error bar; a result at or above zero lies within its limits.
A result drawn hollow is one 5.3 forbids using.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the verdict markers. |

### FilterPeriodicVerification.statement

*property*

The statement IEC 61260-3:2016 Clause 14 prescribes for the result.

14 m) when a result exceeds its acceptance limits, followed by the
tests that did not complete and why; the 5.3 notice when results
cannot be used; a notice naming the clauses not measured; and
otherwise 14 k) with a public pattern approval or 14 l) without one,
which carries the caveat of 1.5: without it no general conclusion
about IEC 61260-1 can be drawn.

### FilterPeriodicVerification.unusable

*property*

`(clause, result)` for every result 5.3 forbids using.

## PERIODIC_TEST_ATTENUATION_LIMITS_DB

*Constant* (`mapping`).

```python
PERIODIC_TEST_ATTENUATION_LIMITS_DB = {1: ((-0.4, 0.4), (-0.4, 0.5), (-0.4, 0.7), (-0.4, 1.4), (16.6, inf), (40.5, inf), (60.0, inf), (70.0, inf)), 2: ((-0.6, 0.6), (-0.6, 0.7), (-0.6, 0.9), (-0.6, 1.7), (15.6, inf), (39.5, inf), (54.0, inf), (60.0, inf))}
```

## periodic_test_frequencies

```python
periodic_test_frequencies(fraction: float) -> np.ndarray
```

The 15 normalized test frequencies of IEC 61260-3:2016 Clause 13.

$\Omega_k$ for `k = -7, -6, ..., 7`, by Formula (1) for
$k \ge 0$ and Formula (2), $\Omega_{-k} = 1/\Omega_k$, below
the mid-band. Multiply by a filter's exact mid-band frequency for the
test frequencies in hertz (C.2). 13.4 drops the ones below 0.5 times the
lowest mid-band frequency of the set or above 1.5 times the highest.

**Parameters**

| Name | Description |
| :--- | :--- |
| `fraction` | The bandwidth designator denominator `b` (1 for octave, 3 for one-third-octave bands, any positive value). |

**Returns:** A read-only array of the 15 normalized frequencies, ascending, index `k + 7`; `PERIODIC_TEST_ATTENUATION_LIMITS_DB[c][abs(k)]` are their acceptance limits.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a `fraction` that is not positive. |

## PeriodicTestClause

```python
PeriodicTestClause(
    clause: str,
    title: str,
    labels: tuple[str, ...],
    verifications: tuple[ConformanceVerification, ...],
    normalized_frequencies: tuple[float, ...] | None = None,
)
```

The verdict on one clause of IEC 61260-3:2016.

**Attributes**

| Name | Description |
| :--- | :--- |
| `clause` | The clause, `"10.2"`, `"10.3"`, `"11.7"`, `"11.9"` or `"13"`. |
| `title` | What the clause tests. |
| `labels` | What each result is (the filter, the level or the test frequency it belongs to), in the order given. |
| `verifications` | One [`ConformanceVerification`](/phonometry/reference/api/metrology/conformance/#conformanceverification) per result. |
| `normalized_frequencies` | Clause 13 only: the $\Omega_k$ of each result, which its figure is drawn against; `None` otherwise. |

### PeriodicTestClause.failed

*property*

The results whose deviation exceeds its acceptance limits.

Only those measured with an acceptable uncertainty: a result that is
also `unusable` shows nothing about the filter (5.3).

### PeriodicTestClause.passes

*property*

Whether every result of the clause demonstrates conformance (5.1).

### PeriodicTestClause.plot()

```python
PeriodicTestClause.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw every result of the clause against its limits.

Clauses 10 and 11 are drawn as IEC 61260-1:2014 Figure C.1 draws its
examples: the limits, the deviation, its uncertainty and the
maximum-permitted band. Clause 13, whose limits run from a few tenths
of a decibel to 70 dB, is drawn as each result's margin to its nearer
limit against the test frequency: at or above zero it conforms.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the verdict markers. |

### PeriodicTestClause.unusable

*property*

The results whose uncertainty exceeds the maximum permitted (5.3).

## verify_filter_periodic

```python
verify_filter_periodic(
    filter_class: int,
    measurements: FilterPeriodicMeasurements,
    *,
    fraction: float,
    pattern_approval_public: bool = False,
) -> FilterPeriodicVerification
```

Grade the periodic tests of a band filter, IEC 61260-3:2016.

Each clause measured is judged result by result by the conformance rule
of IEC TC 29 (5.1), with the acceptance limits the clause sets and the
maximum-permitted uncertainties of IEC 61260-1:2014 Annex B; see the
module docstring for which clause reads which. The verdict passes when
every clause a complete test grades was measured (10.2 or 10.3, 11.7 and
13) and every result conforms, and its [`statement`](/phonometry/reference/api/filters/periodic-tests/#filterperiodicverificationstatement)
is the text Clause 14 prescribes for the case.

**Parameters**

| Name | Description |
| :--- | :--- |
| `filter_class` | The class the filter is tested as, 1 or 2. |
| `measurements` | The laboratory's results and uncertainties. |
| `fraction` | The bandwidth designator denominator `b` of the filters of Clause 13 (1 for octave, 3 for one-third-octave bands), which places their test frequencies. |
| `pattern_approval_public` | Whether evidence is publicly available, from an independent testing organization, that the model passed the pattern evaluation of IEC 61260-2. Without it a passing filter still supports no general conclusion about IEC 61260-1 (1.5), and the statement says so. |

**Returns:** A [`FilterPeriodicVerification`](/phonometry/reference/api/filters/periodic-tests/#filterperiodicverification).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a class other than 1 or 2, a `fraction` that is not positive, or a record with nothing measured. |
