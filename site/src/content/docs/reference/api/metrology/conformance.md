---
title: "metrology.conformance"
description: "The conformance rule of IEC TC 29: a deviation, its limits and its uncertainty."
sidebar:
  label: "conformance"
---

The conformance rule of IEC TC 29: a deviation, its limits and its uncertainty.

The instrument standards IEC technical committee 29 has written since 2013
decide conformance the same way, and say so in the same sentence. IEC
60942:2017 (sound calibrators) prints it in 5.1.15, A.1.2 and B.1.3, IEC
61672-1:2013 (sound level meters) in 5.1.21, IEC 61672-3:2013 in 4.1 and IEC
61260-2 and -3:2016 (band filters) in their introductions: conformance to a
performance specification is demonstrated when **both** of the following hold,

(a) the measured deviation from the design goal does not exceed the applicable
    acceptance limits, **and**
(b) the actual expanded uncertainty of the measurement, for a coverage
    probability of 95 %, does not exceed the maximum-permitted uncertainty
    the standard prints for that test.

Two things set this rule apart from the older one, which ISO 8041-1:2017 still
uses (13.1 and 14.1) and [`phonometry.vibration.verify_weighting`](/phonometry/reference/api/vibration/instrumentation/#verify_weighting)
implements: the uncertainty is not added to the deviation, and the limits are
inclusive. Annex D of IEC 60942 (Figure D.1) says why the first is safe: the
acceptance interval already sits inside the tolerance interval by a guard band
equal to the maximum-permitted uncertainty, so a laboratory whose uncertainty
is no larger than that maximum cannot pass an instrument that is outside its
tolerance. The same annex settles the second in so many words: "a measured
deviation equal to a limit of an acceptance interval demonstrates conformance
to a specification, providing also that the uncertainty of the measurement
from the laboratory performing a test does not exceed the specified
maximum-permitted uncertainty". The uncertainty criterion is inclusive too:
example 7 of IEC 60942 Table E.1 has an actual uncertainty of 0,15 dB against
a maximum of 0,15 dB and conforms.

With two criteria there are four outcomes, and the standards number them the
same way (IEC 60942 E.2.2, IEC 61672-1 C.2.2):

1. deviation within the limits and uncertainty within the maximum: conformance;
2. deviation within the limits but uncertainty above the maximum:
   non-conformance, because the measurement cannot demonstrate anything;
3. deviation outside the limits with an acceptable uncertainty:
   non-conformance;
4. both criteria failed.

[`ConformanceVerification.outcome`](/phonometry/reference/api/metrology/conformance/#conformanceverificationoutcome) is that number and
[`ConformanceVerification.reason`](/phonometry/reference/api/metrology/conformance/#conformanceverificationreason) the wording the "Reasons" column of
Table E.1 and Table C.1 gives it, so the eighteen printed examples of the two
tables are reproduced to the letter as well as to the verdict.

The limits may be symmetric, as IEC 60942 writes them (an acceptance limit on
the *absolute* deviation), or asymmetric, as IEC 61672-1 writes most of its own
(+1,0 dB; -1,2 dB in Table C.1). A symmetric limit is given as one number and
an asymmetric pair as `(lower, upper)`.

A deviation that reaches a limit through floating-point arithmetic, such as a
measured 0,2 dB plus a correction of 0,1 dB against a limit of 0,3 dB, sums
to 0,300 000 000 000 000 04 and would be turned away by its last bit. Both
comparisons therefore accept a value within one part in $10^9$ of its
bound, which is nine orders of magnitude below any resolution these standards
report a deviation at.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## ConformanceVerification

```python
ConformanceVerification(
    deviation: float,
    uncertainty: float,
    lower_limit: float,
    upper_limit: float,
    max_uncertainty: float,
    unit: str = 'dB',
)
```

One measured deviation judged by the conformance rule of IEC TC 29.

The verdict is derived from the fields rather than stored beside them, so
a result cannot say it conforms over numbers that do not. All five
numbers are in the one unit the specification is written in, which
`unit` names for the figure.

**Attributes**

| Name | Description |
| :--- | :--- |
| `deviation` | The measured deviation from the design goal, signed. |
| `uncertainty` | The actual expanded uncertainty of that measurement, for a coverage probability of 95 %, as the testing laboratory calculated it. |
| `lower_limit` | The lower acceptance limit, inclusive. |
| `upper_limit` | The upper acceptance limit, inclusive. |
| `max_uncertainty` | The maximum-permitted expanded uncertainty the standard prints for the test, inclusive. |
| `unit` | The unit of the five numbers, a label for the figure (`"dB"` by default, `"%"` for a frequency or a distortion). |

### ConformanceVerification.deviation_within_limits

*property*

Criterion (a): the deviation lies inside the acceptance limits.

Both limits belong to the acceptance interval (IEC 60942:2017 Annex D).

### ConformanceVerification.outcome

*property*

The outcome number of IEC 60942:2017 E.2.2 and IEC 61672-1:2013 C.2.2.

`1` conforms; `2` the uncertainty exceeds its maximum; `3` the
deviation exceeds its limits; `4` both.

### ConformanceVerification.passes

*property*

Whether the measurement demonstrates conformance: (a) AND (b).

A deviation inside its limits measured with too large an uncertainty
does not pass. It is not a failure of the instrument; it is a
measurement that "shall not be used to demonstrate conformance"
(IEC 60942:2017 5.1.16), which `outcome` tells apart.

### ConformanceVerification.plot()

```python
ConformanceVerification.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Draw the deviation, its uncertainty and the limits, as Figure E.1 does.

The acceptance limits are the two horizontal lines, the measured
deviation the marker (a diamond when it conforms, a cross when it does
not), the actual uncertainty the error bar and the maximum-permitted
one the shaded band behind it.

Requires matplotlib (`pip install phonometry[plot]`); returns the
`Axes`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to `phonometry._plot.metrology.plot_conformance_verification`. |

### ConformanceVerification.reason

*property*

Why the measurement does or does not conform, as Table E.1 words it.

### ConformanceVerification.share_of_acceptance_limit

*property*

How much of its acceptance limit the deviation uses, as a fraction.

Read on the side the deviation lies: a deviation of -0,6 dB against
limits of +1,0 dB and -1,2 dB uses 0,5 of the lower one. Above 1 the
deviation is outside the limits. A deviation on the far side of a
limit of zero (a negative distortion against `(0, 3)`) has no finite
share and reads as infinity.

### ConformanceVerification.share_of_max_uncertainty

*property*

The actual uncertainty over the maximum permitted. Above 1 it fails.

### ConformanceVerification.uncertainty_within_maximum

*property*

Criterion (b): the uncertainty does not exceed the maximum permitted.

## verify_conformance

```python
verify_conformance(
    deviation: float,
    *,
    uncertainty: float,
    acceptance_limits: float | tuple[float, float],
    max_uncertainty: float,
    unit: str = 'dB',
) -> ConformanceVerification
```

Verify one measured deviation by the conformance rule of IEC TC 29.

Conformance to a performance specification is demonstrated when the
measured deviation from the design goal does not exceed the acceptance
limits AND the actual expanded uncertainty does not exceed the
maximum-permitted uncertainty, both limits inclusive (IEC 60942:2017
5.1.15 and Annex D; IEC 61672-1:2013 5.1.21). The rule reproduces every
verdict of IEC 60942:2017 Table E.1 and IEC 61672-1:2013 Table C.1.

It is the rule, not a standard: the limits and the maximum uncertainty are
what the standard prints for the test at hand, read off its own tables.
[`phonometry.metrology.verify_sound_calibrator`](/phonometry/reference/api/metrology/sound-calibrator/#verify_sound_calibrator) does that for IEC
60942.

**Parameters**

| Name | Description |
| :--- | :--- |
| `deviation` | The measured deviation from the design goal, signed, in the unit of the specification. A standard that grades the absolute deviation, as IEC 60942 does, is served by passing the deviation as measured and a symmetric limit. |
| `uncertainty` | The actual expanded uncertainty of the measurement for a coverage probability of 95 %, in the same unit. |
| `acceptance_limits` | One non-negative number for symmetric limits (`0.25` is +/-0,25), or a `(lower, upper)` pair such as `(-1.2, 1.0)`. Both limits belong to the acceptance interval. |
| `max_uncertainty` | The maximum-permitted expanded uncertainty for a coverage probability of 95 %, in the same unit. |
| `unit` | The unit of the numbers, used to label the figure (default `"dB"`). |

**Returns:** The [`ConformanceVerification`](/phonometry/reference/api/metrology/conformance/#conformanceverification), whose `passes` is the verdict and whose `outcome` and `reason` say which of the four outcomes it is.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a non-finite number, a negative symmetric limit, a lower limit above the upper one, a negative uncertainty or a maximum-permitted uncertainty that is not positive. |
