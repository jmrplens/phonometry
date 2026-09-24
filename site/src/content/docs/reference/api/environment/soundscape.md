---
title: "environment.assessment.soundscape"
description: "How people hear a place: the soundscape questionnaire and its analysis (ISO/TS 12913-2:2018 Annexes A and C, ISO/TS 12913-3:2019 Annexes A and B)."
sidebar:
  label: "soundscape"
---

How people hear a place: the soundscape questionnaire and its analysis
(ISO/TS 12913-2:2018 Annexes A and C, ISO/TS 12913-3:2019 Annexes A and B).

A soundscape is the acoustic environment as a person perceives it in context
(ISO 12913-1). Its study "relies primarily upon human perception and only
then turns to physical measurement" (ISO/TS 12913-2, Introduction), which
makes this the first module of the library whose input is not a signal but a
**questionnaire**: the boxes people ticked on a soundwalk, turned into
numbers and statistics the way ISO/TS 12913-3 prescribes.

What is implemented, in the order a study runs:

* the **questionnaires** of ISO/TS 12913-2 Annex C as read-only tables:
  Method A (clause C.3.1, Figures C.2 to C.6), four parts on five-category
  scales, and the continuous-category scales of Method B (clause C.3.2,
  Figure C.7), with every question, item and response category as printed,
  in [`METHOD_A_SCALES`](/phonometry/reference/api/environment/soundscape/#method_a_scales), [`METHOD_A_ALTERNATIVE_PART_1`](/phonometry/reference/api/environment/soundscape/#method_a_alternative_part_1) and
  [`METHOD_B_SCALES`](/phonometry/reference/api/environment/soundscape/#method_b_scales); the eight attributes of the perceived affective
  quality in [`PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES`](/phonometry/reference/api/environment/soundscape/#perceived_affective_quality_attributes);
* the **scale values** of Method A (ISO/TS 12913-3 A.2, Table A.1): parts 1
  and 4 run 1 to 5 from the left-hand box to the right-hand one, parts 2 and 3
  run 5 to 1, [`method_a_scale_values`](/phonometry/reference/api/environment/soundscape/#method_a_scale_values); and their median and range per
  site and item, [`method_a_summary`](/phonometry/reference/api/environment/soundscape/#method_a_summary);
* the **pleasantness and eventfulness** coordinates of Formulas (A.1) and
  (A.2), per respondent and per site, raw and normalised to $\pm 1$,
  with the two-dimensional model of Figure A.1 as the plot,
  [`pleasantness_eventfulness`](/phonometry/reference/api/environment/soundscape/#pleasantness_eventfulness);
* the **correlations** that link ratings to acoustic data: Spearman's rank
  correlation with the untied Formula (A.3) and the tied Formula (A.4),
  [`spearman_rank_correlation`](/phonometry/reference/api/environment/soundscape/#spearman_rank_correlation), and Pearson's of Formulas (B.1) and
  (B.2), [`pearson_correlation`](/phonometry/reference/api/environment/soundscape/#pearson_correlation), each with its probability value;
* **Method B** (Annex B): the scale value of a mark on a continuous-category
  scale with one decimal, [`method_b_scale_values`](/phonometry/reference/api/environment/soundscape/#method_b_scale_values); the arithmetic mean,
  standard deviation and 95 % confidence interval per site,
  [`method_b_summary`](/phonometry/reference/api/environment/soundscape/#method_b_summary); and the median and range of the rank each
  recognised sound source was given, [`method_b_source_ranking`](/phonometry/reference/api/environment/soundscape/#method_b_source_ranking);
* the **minimum reporting requirements** of ISO/TS 12913-2 Annex A
  (normative), as a record that checks itself when it is built,
  [`SoundscapeReport`](/phonometry/reference/api/environment/soundscape/#soundscapereport).

The binaural analysis of ISO/TS 12913-3 Annex D is
[`phonometry.environment.assessment.soundscape_binaural`](/phonometry/reference/api/environment/soundscape-binaural/).

Edition
-------

This module implements the **first edition of ISO/TS 12913-3, published in
2019**. ISO has since published ISO/TS 12913-3:2025, which revises Annex A;
that edition has not been read for this implementation, so nothing here
claims to follow it, and a study that cites the 2025 edition should check
Formulas (A.1) and (A.2) against it.

Readings the text leaves to the implementer
-------------------------------------------

**Which part feeds Formulas (A.1) and (A.2).** Clause A.3 says "the results
from part 3 (see A.1) are further processed", but the eight attributes the
formulas use are the perceived affective quality, which is part 2 of the
questionnaire everywhere else: in Table A.1, in the paragraph of A.2 that
assigns its scale values, and in ISO/TS 12913-2 C.3.1.3 and Figure C.4. Part 3
is the single overall rating of Figure C.5, which has no attributes. The
formulas are applied to part 2, and the slip is in `docs/ERRATA.md`.

**Per site.** A.3 derives "the values on two dimensions (pleasantness and
eventfulness) for each site" from the results of the questionnaire, and A.2
makes the median the central tendency of every Method A scale. The site
coordinates are therefore Formulas (A.1) and (A.2) applied to the site medians
of the eight attributes. When every respondent answered all eight attributes,
the formulas being linear, the alternative `central_tendency="mean"` gives
the same point as the mean of the respondents' own coordinates. A blank
answer breaks that equality: each attribute mean is then taken over the
respondents who answered that attribute, while a respondent with a blank in a
formula has no coordinate of it. The median of the respondents' coordinates is
a third reading, which the per-respondent values let a caller form.

**Formula (A.3).** The page prints $r = 1 - 1\,\frac{6\sum d_i^2}{n(n^2 - 1)}$, with a stray factor 1; read as a product it is the usual
coefficient for untied ranks, which is what is implemented.

**Formulas (B.1) and (B.2).** (B.2) divides the covariance by `n`, so the
standard deviations of (B.1) are taken with `n` as well; with the `n - 1`
of a sample standard deviation the coefficient would shrink by
$(n - 1)/n$.

**Probability values.** A.4 and B.3 ask for the significance of each
coefficient and its probability value without naming a test. Both use the
Student $t$ statistic $t = r\sqrt{(n - 2)/(1 - r^2)}$ with
$n - 2$ degrees of freedom, which is exact for Pearson's coefficient of
bivariate normal data and the usual large-sample approximation for Spearman's.
The 95 % confidence interval of Method B uses the Student distribution with
$n - 1$ degrees of freedom about the mean, with the sample standard
deviation.

**The where-lists of Formulas (A.4) and (B.2).** The page defines
$t_j$ as "the number of in $t_j$ tied ranks" and $k(x)$ as
"the numbers of tied ranks"; the formula needs the size of the $j$-th
group of tied values and the number of such groups, which is what is
implemented. Under (B.2) the mean is "of the array $x_I$", for
$x_i$. Both slips are in `docs/ERRATA.md`.

> Auto-generated from the source docstrings by `scripts/generate_api_docs.py` (`make api-docs`). Do not edit by hand.

## METHOD_A_ALTERNATIVE_PART_1

*Constant* (`phonometry.environment.assessment.soundscape.QuestionnaireScale`).

## method_a_scale_values

```python
method_a_scale_values(
    positions: ArrayLike,
    *,
    part: int,
) -> float | NDArray[np.float64]
```

The scale value of a ticked box of Method A (ISO/TS 12913-3 Table A.1).

A box is counted from the left-hand end of its scale, 1 to 5, as the
questionnaire of ISO/TS 12913-2 prints it. Parts 1 and 4 assign the scale
values 1 to 5 from left to right, so the value is the position; parts 2
and 3 assign 5 to 1, so "strongly agree" (part 2) and "very good" (part 3)
are 5 and the value is `6 - position`.

**Parameters**

| Name | Description |
| :--- | :--- |
| `positions` | The position of each ticked box, 1 (left) to 5 (right); `NaN` for a question left blank. |
| `part` | The part of the questionnaire, 1 to 4. |

**Returns:** The scale values, a float for a scalar input; an array is always a new one, never a view of *positions*.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a part other than 1 to 4 or a position that is not a whole number from 1 to 5. |

## METHOD_A_SCALES

*Constant* (`mapping`).

## method_a_summary

```python
method_a_summary(
    scale_values: Mapping[str, ArrayLike] | ArrayLike,
    *,
    part: int,
    sites: ArrayLike | Sequence[object] | None = None,
) -> MethodASummary
```

Median and range of the Method A scale values per site and item
(ISO/TS 12913-3 A.2, Table A.1).

**Parameters**

| Name | Description |
| :--- | :--- |
| `scale_values` | The scale values of Table A.1, 1 to 5, `NaN` for a blank answer: a mapping from item name to one value per response; or, for a part with a single scale (3, 4), a 1-D array; or a 2-D array `(responses, items)` in the order of the part's figure (part 1: four columns for Figure C.2 or three for Figure C.3; part 2: the eight attributes of Figure C.4). Box positions are converted with [`method_a_scale_values`](/phonometry/reference/api/environment/soundscape/#method_a_scale_values) first. |
| `part` | The part of the questionnaire, 1 to 4. |
| `sites` | The site of each response, any labels; `None` puts every response at one site named `"all"`. |

**Returns:** A [`MethodASummary`](/phonometry/reference/api/environment/soundscape/#methodasummary).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a part other than 1 to 4, a scale value that is not a whole number from 1 to 5, or sites that do not match the responses. |

## METHOD_B_MAXIMUM_SOURCES

*Constant* (`int`).

```python
METHOD_B_MAXIMUM_SOURCES = 8
```

## method_b_scale_values

```python
method_b_scale_values(
    marked_fraction: ArrayLike,
) -> float | NDArray[np.float64]
```

The scale value of a mark on a Method B scale (ISO/TS 12913-3 B.2).

A continuous-category scale of Figure C.7 runs from its left-hand tick
("not at all", or "never" on the fourth scale), scale value 1, to its
right-hand one ("extremely", or "very often"), scale value 5, and a
mark may fall anywhere along it. Its position is measured with a ruler, or on
screen, as a fraction of the distance between the two end ticks, and the
value is $1 + 4f$ rounded to one decimal, the resolution B.2
requires ("determined at least with one decimal place").

**Parameters**

| Name | Description |
| :--- | :--- |
| `marked_fraction` | The position of each mark from the left-hand tick, 0, to the right-hand one, 1; `NaN` for a scale left blank. |

**Returns:** The scale values, a float for a scalar input.

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a fraction outside 0 to 1 or an infinite one. |

## METHOD_B_SCALES

*Constant* (`tuple`).

```python
METHOD_B_SCALES = (QuestionnaireScale(method='B', part=1, figure='C.7', subject='assessment of the sound environment', question='How loud is it here?', instruction='Mark your impression at any location on the scale below.', items=(), categories=('not at all', 'slightly', 'moderately', 'very', 'extremely'), scale_values=(1, 2, 3, 4, 5), continuous=True), QuestionnaireScale(method='B', part=1, figure='C.7', subject='assessment of the sound environment', question='How unpleasant is it here?', instruction='Mark your impression at any location on the scale below.', items=(), categories=('not at all', 'slightly', 'moderately', 'very', 'extremely'), scale_values=(1, 2, 3, 4, 5), continuous=True), QuestionnaireScale(method='B', part=1, figure='C.7', subject='assessment of the sound environment', question='How appropriate is the sound to the surrounding?', instruction='Mark your impression at any location on the scale below.', items=(), categories=('not at all', 'slightly', 'moderately', 'very', 'extremely'), scale_values=(1, 2, 3, 4, 5), continuous=True), QuestionnaireScale(method='B', part=1, figure='C.7', subject='assessment of the sound environment', question='How often would you like to visit this place again?', instruction='Mark your impression at any location on the scale below.', items=(), categories=('never', 'rarely', 'sometimes', 'often', 'very often'), scale_values=(1, 2, 3, 4, 5), continuous=True))
```

## method_b_source_ranking

```python
method_b_source_ranking(
    rankings: Sequence[Sequence[str]],
    *,
    sites: ArrayLike | Sequence[object] | None = None,
) -> SourceRanking
```

Median and range of the rank of each recognised sound source per site
(ISO/TS 12913-3 B.2, ISO/TS 12913-2 C.3.2.4 and Figure C.8).

**Parameters**

| Name | Description |
| :--- | :--- |
| `rankings` | For each participant, the sources they listed, the most noticeable first, at most eight and none twice. The names are compared as given, so a study should code them to one vocabulary first (for instance the taxonomy of ISO/TS 12913-2 Figure C.1). |
| `sites` | The site of each participant; `None` puts every participant at one site named `"all"`. |

**Returns:** A [`SourceRanking`](/phonometry/reference/api/environment/soundscape/#sourceranking).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a list longer than eight, a source listed twice by one participant, an empty source name, no participants, or sites that do not match the participants. |

## method_b_summary

```python
method_b_summary(
    scale_values: Mapping[str, ArrayLike] | ArrayLike,
    *,
    sites: ArrayLike | Sequence[object] | None = None,
    confidence_level: float = 0.95,
) -> MethodBSummary
```

Mean, standard deviation and confidence interval of Method B
ratings per site (ISO/TS 12913-3 B.2, Table B.1).

The confidence interval of the mean is
$\bar{x} \pm t_{(1+\gamma)/2,\,n-1}\, s/\sqrt{n}$, with $s$
the sample standard deviation and $\gamma$ the confidence level,
95 % as B.2 asks.

**Parameters**

| Name | Description |
| :--- | :--- |
| `scale_values` | The scale values from 1 to 5, read to one decimal by [`method_b_scale_values`](/phonometry/reference/api/environment/soundscape/#method_b_scale_values), `NaN` for a blank: a mapping from scale name to one value per response, a 1-D array for one scale, or a 2-D array `(responses, scales)` whose three or four columns are the scales of Figure C.7 in their printed order. |
| `sites` | The site of each response; `None` puts every response at one site named `"all"`. |
| `confidence_level` | The level of the interval, `0.95` by default. |

**Returns:** A [`MethodBSummary`](/phonometry/reference/api/environment/soundscape/#methodbsummary).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a value outside 1 to 5, a confidence level not strictly between 0 and 1, or sites that do not match the responses. |

## MethodASummary

```python
MethodASummary(
    part: int,
    items: tuple[str, ...],
    sites: tuple[str, ...],
    medians: NDArray[np.float64],
    minima: NDArray[np.float64],
    maxima: NDArray[np.float64],
    ranges: NDArray[np.float64],
    counts: NDArray[np.int64],
)
```

Median and range of Method A responses per site and item
(ISO/TS 12913-3 A.2 and Table A.1).

The level of measurement of every Method A scale is ordinal, so the
median is the measure of central tendency and the range, the largest
scale value given less the smallest, the measure of dispersion. A blank
answer is left out of both; a site where nobody answered an item has
`NaN` there and a count of zero.

**Attributes**

| Name | Description |
| :--- | :--- |
| `part` | The part of the questionnaire, 1 to 4. |
| `items` | The items rated (the attributes, the source types), or the subject of the part for a single scale. |
| `sites` | The sites, in the order they first appear in the responses. |
| `medians` | Median scale value, shape `(sites, items)`. |
| `minima` | Smallest scale value given, shape `(sites, items)`. |
| `maxima` | Largest scale value given, shape `(sites, items)`. |
| `ranges` | `maxima - minima`, the measure of dispersion. |
| `counts` | Number of answers, shape `(sites, items)`. |

### MethodASummary.plot()

```python
MethodASummary.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the median of each item per site, with its range as a bar.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the median markers of the first site; the other sites keep their own colour and style. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

## MethodBSummary

```python
MethodBSummary(
    items: tuple[str, ...],
    sites: tuple[str, ...],
    means: NDArray[np.float64],
    standard_deviations: NDArray[np.float64],
    confidence_lower: NDArray[np.float64],
    confidence_upper: NDArray[np.float64],
    medians: NDArray[np.float64],
    counts: NDArray[np.int64],
    confidence_level: float,
)
```

Arithmetic mean, standard deviation and confidence interval of Method
B ratings per site and scale (ISO/TS 12913-3 B.2 and Table B.1).

The level of measurement of the continuous-category scales is interval,
so B.2 reports the arithmetic mean with its standard deviation and 95 %
confidence interval. "Statistics for an ordinal scale level may be
additionally applied", so the median is here too. A blank answer is left
out; a site with fewer than two answers to a scale has no standard
deviation or interval there (`NaN`).

**Attributes**

| Name | Description |
| :--- | :--- |
| `items` | The scales (their questions, for Figure C.7). |
| `sites` | The sites, in the order they first appear. |
| `means` | Arithmetic mean, shape `(sites, items)`. |
| `standard_deviations` | Sample standard deviation, with `n - 1`. |
| `confidence_lower` | Lower end of the confidence interval of the mean. |
| `confidence_upper` | Upper end of the confidence interval of the mean. |
| `medians` | Median, the ordinal statistic. |
| `counts` | Number of answers. |
| `confidence_level` | The level of the interval, `0.95` unless chosen. |

### MethodBSummary.plot()

```python
MethodBSummary.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the mean of each scale per site with its confidence interval.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the mean markers of the first site; the other sites keep their own colour and style. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

## pearson_correlation

```python
pearson_correlation(
    x: ArrayLike,
    y: ArrayLike,
    *,
    alternative: Literal['two-sided', 'greater', 'less'] = 'two-sided',
) -> SoundscapeCorrelation
```

Pearson's correlation coefficient, for interval data
(ISO/TS 12913-3 B.3, Formulas (B.1) and (B.2)).

$$
r = \frac{\operatorname{cov}(x, y)}{\sigma_x \sigma_y}, \qquad \operatorname{cov}(x, y) = \frac{1}{n}\sum_{i=1}^{n} (x_i - \bar{x})(y_i - \bar{y}).
$$

Formula (B.2) divides by `n`, so the standard deviations are taken with
`n` too, which makes $r$ the usual coefficient; with the `n - 1`
of a sample standard deviation it would shrink by $(n - 1)/n$. The
probability value is that of the Student statistic
$r\sqrt{(n - 2)/(1 - r^2)}$ with $n - 2$ degrees of freedom,
exact for bivariate normal data.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | The first variable, for instance the mean Method B rating of each site. |
| `y` | The second, for instance an acoustic indicator of each site. |
| `alternative` | The alternative hypothesis: `"two-sided"` (default), `"greater"` or `"less"`. |

**Returns:** A [`SoundscapeCorrelation`](/phonometry/reference/api/environment/soundscape/#soundscapecorrelation).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for variables of different lengths, fewer than three pairs, a non-finite value or a constant variable. |

## PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES

*Constant* (`tuple`).

```python
PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES = ('pleasant', 'chaotic', 'vibrant', 'uneventful', 'calm', 'annoying', 'eventful', 'monotonous')
```

## pleasantness_eventfulness

```python
pleasantness_eventfulness(
    scale_values: Mapping[str, ArrayLike] | ArrayLike,
    *,
    sites: ArrayLike | Sequence[object] | None = None,
    central_tendency: Literal['median', 'mean'] = 'median',
) -> PleasantnessEventfulness
```

Pleasantness and eventfulness of a soundscape from its perceived
affective quality (ISO/TS 12913-3 A.3, Formulas (A.1) and (A.2)).

The scale values are those of part 2 of Method A, 5 for "strongly agree"
down to 1 for "strongly disagree" (Table A.1); [`method_a_scale_values`](/phonometry/reference/api/environment/soundscape/#method_a_scale_values)
converts box positions, which run the other way. Every respondent who
answered all eight attributes gets a coordinate pair. Each site gets the
pair of Formulas (A.1) and (A.2) applied to the site's median of each
attribute (A.2 makes the median the central tendency of the scale), or to
its mean with `central_tendency="mean"`. When every respondent answered
all eight attributes, that mean point is also the mean of the respondents'
coordinates, the formulas being linear; with blank answers it is not,
because each attribute mean is then taken over a different set of
respondents.

Clause A.3 says the formulas process "the results from part 3"; the
attributes they name are part 2, and that is what they are applied to
(see the module docstring and `docs/ERRATA.md`).

**Parameters**

| Name | Description |
| :--- | :--- |
| `scale_values` | The eight attributes: a mapping from each name of [`PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES`](/phonometry/reference/api/environment/soundscape/#perceived_affective_quality_attributes) to one scale value per respondent, or a 2-D array `(respondents, 8)` in that order. `NaN` marks a blank answer. A row may also be a statistic of a group of answers, such as a site's medians, which is why a value between two boxes is accepted here; anything outside 1 to 5 is not a scale value. |
| `sites` | The site of each respondent, any labels; `None` puts every respondent at one site named `"all"`. |
| `central_tendency` | `"median"` (default) or `"mean"`. |

**Returns:** A [`PleasantnessEventfulness`](/phonometry/reference/api/environment/soundscape/#pleasantnesseventfulness).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for a mapping that does not name the eight attributes, a value outside 1 to 5, or sites that do not match the respondents. |

## PLEASANTNESS_EVENTFULNESS_RANGE

*Constant* (`float`).

```python
PLEASANTNESS_EVENTFULNESS_RANGE = 9.65685424949238
```

## PleasantnessEventfulness

```python
PleasantnessEventfulness(
    sites: tuple[str, ...],
    central_tendency: str,
    attribute_values: NDArray[np.float64],
    pleasantness: NDArray[np.float64],
    eventfulness: NDArray[np.float64],
    respondent_sites: tuple[str, ...],
    respondent_pleasantness: NDArray[np.float64],
    respondent_eventfulness: NDArray[np.float64],
    respondent_counts: NDArray[np.int64],
)
```

Pleasantness and eventfulness of each site and each respondent
(ISO/TS 12913-3 A.3, Formulas (A.1) and (A.2)).

$$
P = (p - a) + \cos 45^\circ (ca - ch) + \cos 45^\circ (v - m)
$$

$$
E = (e - u) + \cos 45^\circ (ch - ca) + \cos 45^\circ (v - m)
$$

on the scale values of the eight attributes of part 2. The coordinates
range over $\pm (4 + \sqrt{32}) \approx \pm 9.66$; the
`normalized_*` properties divide by that, for the $\pm 1$ of A.3.

**Attributes**

| Name | Description |
| :--- | :--- |
| `sites` | The sites, in the order they first appear. |
| `central_tendency` | `"median"` or `"mean"`, the statistic of each attribute per site that the site coordinates are computed from. |
| `attribute_values` | That statistic, shape `(sites, 8)` in the order of [`PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES`](/phonometry/reference/api/environment/soundscape/#perceived_affective_quality_attributes). |
| `pleasantness` | $P$ of each site. |
| `eventfulness` | $E$ of each site. |
| `respondent_sites` | The site of each respondent. |
| `respondent_pleasantness` | $P$ of each respondent, `NaN` where one of the six attributes of Formula (A.1) was left blank. |
| `respondent_eventfulness` | $E$ of each respondent, `NaN` where one of the six attributes of Formula (A.2) was left blank. |
| `respondent_counts` | Respondents per site who answered all eight. |

### PleasantnessEventfulness.normalized_eventfulness

*property*

$E / (4 + \sqrt{32})$ of each site, in $\pm 1$.

### PleasantnessEventfulness.normalized_pleasantness

*property*

$P / (4 + \sqrt{32})$ of each site, in $\pm 1$.

### PleasantnessEventfulness.plot()

```python
PleasantnessEventfulness.plot(
    ax: Axes | None = None,
    *,
    normalized: bool = True,
    respondents: bool = False,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the sites on the two-dimensional model of Figure A.1.

Pleasantness on the horizontal axis and eventfulness on the vertical
one, with the eight attributes at the ends of their axes, the diagonal
ones at 45 degrees, and every site a point.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `normalized` | Draw the coordinates divided by $4 + \sqrt{32}$ (default), in $\pm 1$; `False` draws them raw, in $\pm 9.66$. |
| `respondents` | Also draw every respondent, faintly, in the colour of their site. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the site markers. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

## QuestionnaireScale

```python
QuestionnaireScale(
    method: str,
    part: int,
    figure: str,
    subject: str,
    question: str,
    instruction: str,
    items: tuple[str, ...],
    categories: tuple[str, ...],
    scale_values: tuple[int, ...],
    continuous: bool,
)
```

One scale of the soundscape questionnaire, as ISO/TS 12913-2 prints it.

The text is transcribed from the figure, misprints included: the questions
of Figures C.2 to C.4 read "To what extend" and their instructions
"reponse alternative", which `docs/ERRATA.md` records; a study that
prints its own questionnaire from this table should correct them.

**Attributes**

| Name | Description |
| :--- | :--- |
| `method` | `"A"` (clause C.3.1, the questionnaire) or `"B"` (clause C.3.2, the soundwalk data collection). |
| `part` | The part of the questionnaire the scale belongs to. |
| `figure` | The figure of ISO/TS 12913-2 Annex C that prints it. |
| `subject` | What the part assesses, as the heading of its clause and Table A.1 or Table B.1 of ISO/TS 12913-3 name it. |
| `question` | The question, as printed. |
| `instruction` | The instruction line under the question, as printed; empty where the figure has none. |
| `items` | The rows rated on the same categories (the sound source types of part 1, the eight attributes of part 2); empty for a scale that rates the environment as a whole. |
| `categories` | The response categories from the left-hand box to the right-hand one, as printed; for a continuous-category scale of Method B, the labels of its five ticks. |
| `scale_values` | The scale value of each category, in the same order: ISO/TS 12913-3 Table A.1 for Method A, Table B.1 for Method B. |
| `continuous` | Whether a mark may fall anywhere along the scale (Method B) rather than in one of the boxes (Method A). |

## SoundscapeAcousticEnvironment

```python
SoundscapeAcousticEnvironment(
    environment_type: str,
    sound_sources: str,
    weather_and_wind: str,
    time_of_year_and_day: str,
    measurement_points: str,
    measurement_results: Mapping[str, float],
    site_description: str | None = None,
    recording_and_reproduction: str | None = None,
)
```

The studied acoustic environment (ISO/TS 12913-2 A.3 a) to h)).

**Attributes**

| Name | Description |
| :--- | :--- |
| `environment_type` | A.3 a), `"real"`, `"recorded"` or `"virtual"`. |
| `sound_sources` | A.3 b), the sound sources and the composition of the acoustic environment, including the total sound, the background and the foreground sounds. |
| `weather_and_wind` | A.3 c). |
| `time_of_year_and_day` | A.3 d). |
| `measurement_points` | A.3 e), the measurement points, including the height and orientation of the binaural measurement system, and what acoustic measurements were taken. |
| `measurement_results` | A.3 f), the results of the measurements, keyed by the symbols A.3 f) prints: `"LAeq,T"`, `"LCeq,T"`, `"LAF5,T"`, `"LAF95,T"` (dB), `"N5"`, `"N95"` and `"Nrmc"` (sone), all seven required, others allowed. [`BinauralIndicators.reporting_results`](/phonometry/reference/api/environment/soundscape-binaural/#binauralindicatorsreporting_results) builds it from a binaural analysis. |
| `site_description` | A.3 g), required for a field study or a study based on audio recordings (`"real"` or `"recorded"`): the study site, including its type. |
| `recording_and_reproduction` | A.3 h), required for a recorded or virtual environment: how it was recorded or created and how it was reproduced. |

## SoundscapeCorrelation

```python
SoundscapeCorrelation(
    method: str,
    formula: str,
    coefficient: float,
    p_value: float,
    t_statistic: float,
    degrees_of_freedom: int,
    alternative: str,
    x: NDArray[np.float64],
    y: NDArray[np.float64],
    x_ranks: NDArray[np.float64] | None = None,
    y_ranks: NDArray[np.float64] | None = None,
)
```

A correlation coefficient between two variables and its probability
value (ISO/TS 12913-3 A.4 and B.3).

**Attributes**

| Name | Description |
| :--- | :--- |
| `method` | `"spearman"` (ordinal data, A.4) or `"pearson"` (interval data, B.3). |
| `formula` | The formula that gave the coefficient: `"(A.3)"` for untied ranks, `"(A.4)"` for tied ranks, `"(B.1)"` for Pearson. |
| `coefficient` | The correlation coefficient, in `[-1, 1]`. |
| `p_value` | Probability, under the null hypothesis of no correlation, of a coefficient at least as extreme as this one in the direction `alternative` names (either sign for `"two-sided"`). |
| `t_statistic` | The Student statistic the probability value comes from, $r\sqrt{(n - 2)/(1 - r^2)}$; infinite for $\vert r\vert  = 1$. |
| `degrees_of_freedom` | $n - 2$. |
| `alternative` | `"two-sided"`, `"greater"` or `"less"`. |
| `x` | The first variable, as given (a copy, read-only). |
| `y` | The second variable, as given (a copy, read-only). |
| `x_ranks` | The ranks of `x` (average ranks for ties); `None` for Pearson. |
| `y_ranks` | The ranks of `y`; `None` for Pearson. |

### SoundscapeCorrelation.n

*property*

Number of cases, the pairs the coefficient was computed from.

### SoundscapeCorrelation.plot()

```python
SoundscapeCorrelation.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the pairs, as ranks for Spearman, with the coefficient.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the scatter markers. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

## SoundscapeDataCollection

```python
SoundscapeDataCollection(
    methods: str,
    questions: str,
    language: str,
    instrument_copy: str,
    rating_scale_construction: str | None = None,
    behaviour_observation: str | None = None,
)
```

How the perception data were collected (ISO/TS 12913-2 A.4 a) to e)).

**Attributes**

| Name | Description |
| :--- | :--- |
| `methods` | A.4 a), the methods used. |
| `questions` | A.4 b), the questions asked, how they were formulated and how the responses were documented. |
| `language` | A.4 d), the language of the study, with examples of the questions in the original language and in translation. |
| `instrument_copy` | Where the copy of the data collection instrument (the questionnaire or the scales) that A.4 requires the report to include is found. |
| `rating_scale_construction` | A.4 c), for a study based on rating scales: how the questions, the response alternatives and the response format were constructed and formulated; `None` for a study without. |
| `behaviour_observation` | A.4 e), for observations of behaviour: how they were conducted and documented; `None` for a study without. |

## SoundscapeParticipants

```python
SoundscapeParticipants(
    selection: str,
    residents_or_visitors: str,
    lay_or_expert: str,
    age_and_gender_distribution: str,
    other_relevant_information: str,
)
```

The participants of a soundscape study (ISO/TS 12913-2 A.2 a) to e)).

Every field is required: "the participants shall be identified and the
following information recorded". Each is free text, because the annex
prescribes what is stated and not how.

**Attributes**

| Name | Description |
| :--- | :--- |
| `selection` | A.2 a), how the participants were selected. |
| `residents_or_visitors` | A.2 b), whether they were residents at or visitors to the study site. |
| `lay_or_expert` | A.2 c), whether they were lay people or experts in a field relevant to the study. |
| `age_and_gender_distribution` | A.2 d). |
| `other_relevant_information` | A.2 e), for example hearing ability; state "none" if there is nothing to add. |

## SoundscapeReport

```python
SoundscapeReport(
    participants: SoundscapeParticipants,
    acoustic_environment: SoundscapeAcousticEnvironment,
    data_collection: SoundscapeDataCollection,
)
```

The minimum reporting requirements of a soundscape study
(ISO/TS 12913-2 Annex A, normative, and clause 6).

A.1 lists three things a report shall comprise, and each is one record:
the selection and classification of the participants (A.2), the
characterization of the studied acoustic environment (A.3), and the data
collection on how people perceived it (A.4). Each record refuses to be
built with a required item missing, so a [`SoundscapeReport`](/phonometry/reference/api/environment/soundscape/#soundscapereport) that
exists meets the minimum of Annex A as far as a record can tell; whether
what is written is true and sufficient stays with the author.

**Attributes**

| Name | Description |
| :--- | :--- |
| `participants` | A.1 a), A.2. |
| `acoustic_environment` | A.1 b), A.3. |
| `data_collection` | A.1 c), A.4. |

## SourceRanking

```python
SourceRanking(
    sources: tuple[str, ...],
    sites: tuple[str, ...],
    median_ranks: NDArray[np.float64],
    lowest_ranks: NDArray[np.float64],
    highest_ranks: NDArray[np.float64],
    rank_ranges: NDArray[np.float64],
    mentions: NDArray[np.int64],
    participants: NDArray[np.int64],
)
```

The rank each recognised sound source was given, per site
(ISO/TS 12913-3 B.2, part 2 of Method B, Table B.1).

Every participant lists the sources they noticed from the most noticeable
down, at most eight, so a source listed first has rank 1. The level of
measurement is ordinal: the median rank is the central tendency and the
range the dispersion. Sources are ordered by their median rank over all
sites, then by how often they were listed.

**Attributes**

| Name | Description |
| :--- | :--- |
| `sources` | Every source listed at any site. |
| `sites` | The sites, in the order they first appear. |
| `median_ranks` | Median rank, shape `(sites, sources)`; `NaN` where nobody at the site listed the source. |
| `lowest_ranks` | The best rank the source was given, same shape. |
| `highest_ranks` | The worst rank it was given, same shape. |
| `rank_ranges` | `highest_ranks - lowest_ranks`, the dispersion. |
| `mentions` | How many participants listed the source, same shape. |
| `participants` | Participants per site. |

### SourceRanking.plot()

```python
SourceRanking.plot(
    ax: Axes | None = None,
    *,
    language: str = 'en',
    **kwargs: Any,
) -> Axes
```

Plot the median rank of each source per site, with its range.

**Parameters**

| Name | Description |
| :--- | :--- |
| `ax` | Existing axes, or `None` to create a figure. |
| `language` | Label language, `"en"` (default) or `"es"`. |
| `kwargs` | Forwarded to the bars of the first site; the other sites keep their own colour and style. |

**Returns:** The axes. Requires matplotlib (`pip install phonometry[plot]`).

## spearman_rank_correlation

```python
spearman_rank_correlation(
    x: ArrayLike,
    y: ArrayLike,
    *,
    alternative: Literal['two-sided', 'greater', 'less'] = 'two-sided',
) -> SoundscapeCorrelation
```

Spearman's rank correlation coefficient, for ordinal data
(ISO/TS 12913-3 A.4, Formulas (A.3) and (A.4)).

Each variable is ranked, tied values sharing the mean of the ranks they
span, and $d_i$ is the difference of the ranks of pair $i$.
Without ties Formula (A.3) applies,

$$
r_\mathrm{spearman} = 1 - \frac{6 \sum_{i=1}^{n} d_i^2}{n(n^2 - 1)},
$$

and with ties in either variable Formula (A.4),

$$
r_\mathrm{spearman} = \frac{2\,\frac{n^3 - n}{12} - T - U - \sum d_i^2} {2\sqrt{\left(\frac{n^3 - n}{12} - T\right) \left(\frac{n^3 - n}{12} - U\right)}}, \qquad T = \frac{\sum_{j} (t_j^3 - t_j)}{12},
$$

where $t_j$ is the number of values in the $j$-th group of
tied ranks of `x` and `U` is the same sum over `y`. (The page's
where-list garbles these definitions, see `docs/ERRATA.md`; this is the
reading the formula needs.) Formula (A.4) is Pearson's coefficient of the
average ranks, and reduces to (A.3) when nothing is tied.

The probability value is that of the Student statistic
$r\sqrt{(n - 2)/(1 - r^2)}$ with $n - 2$ degrees of freedom,
the usual approximation for Spearman's coefficient, which A.4 asks to be
reported without naming a test.

**Parameters**

| Name | Description |
| :--- | :--- |
| `x` | The first variable, for instance the median rating of each site. |
| `y` | The second, for instance an acoustic indicator of each site. |
| `alternative` | The alternative hypothesis: `"two-sided"` (default), `"greater"` (positive correlation) or `"less"`. |

**Returns:** A [`SoundscapeCorrelation`](/phonometry/reference/api/environment/soundscape/#soundscapecorrelation).

**Raises**

| Exception | When |
| :--- | :--- |
| ValueError | for variables of different lengths, fewer than three pairs, a non-finite value or a constant variable. |
