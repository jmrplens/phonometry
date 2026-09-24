#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""How people hear a place: the soundscape questionnaire and its analysis
(ISO/TS 12913-2:2018 Annexes A and C, ISO/TS 12913-3:2019 Annexes A and B).

A soundscape is the acoustic environment as a person perceives it in context
(ISO 12913-1). Its study "relies primarily upon human perception, and only
then turns to physical measurement" (ISO/TS 12913-2, Introduction), which
makes this the first module of the library whose input is not a signal but a
**questionnaire**: the boxes people ticked on a soundwalk, turned into
numbers and statistics the way ISO/TS 12913-3 prescribes.

What is implemented, in the order a study runs:

* the **questionnaires** of ISO/TS 12913-2 Annex C as read-only tables:
  Method A (clause C.3.1, Figures C.2 to C.6), four parts on five-category
  scales, and the continuous-category scales of Method B (clause C.3.2,
  Figure C.7), with every question, item and response category as printed,
  in :data:`METHOD_A_SCALES`, :data:`METHOD_A_ALTERNATIVE_PART_1` and
  :data:`METHOD_B_SCALES`; the eight attributes of the perceived affective
  quality in :data:`PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES`;
* the **scale values** of Method A (ISO/TS 12913-3 A.2, Table A.1): parts 1
  and 4 run 1 to 5 from the left-hand box to the right-hand one, parts 2 and 3
  run 5 to 1, :func:`method_a_scale_values`; and their median and range per
  site and item, :func:`method_a_summary`;
* the **pleasantness and eventfulness** coordinates of Formulas (A.1) and
  (A.2), per respondent and per site, raw and normalised to :math:`\pm 1`,
  with the two-dimensional model of Figure A.1 as the plot,
  :func:`pleasantness_eventfulness`;
* the **correlations** that link ratings to acoustic data: Spearman's rank
  correlation with the untied Formula (A.3) and the tied Formula (A.4),
  :func:`spearman_rank_correlation`, and Pearson's of Formulas (B.1) and
  (B.2), :func:`pearson_correlation`, each with its probability value;
* **Method B** (Annex B): the scale value of a mark on a continuous-category
  scale with one decimal, :func:`method_b_scale_values`; the arithmetic mean,
  standard deviation and 95 % confidence interval per site,
  :func:`method_b_summary`; and the median and range of the rank each
  recognised sound source was given, :func:`method_b_source_ranking`;
* the **minimum reporting requirements** of ISO/TS 12913-2 Annex A
  (normative), as a record that checks itself when it is built,
  :class:`SoundscapeReport`.

The binaural analysis of ISO/TS 12913-3 Annex D is
:mod:`phonometry.environment.assessment.soundscape_binaural`.

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
formulas are applied to part 2, and the slip is in ``docs/ERRATA.md``.

**Per site.** A.3 derives "the values on two dimensions (pleasantness and
eventfulness) for each site" from the results of the questionnaire, and A.2
makes the median the central tendency of every Method A scale. The site
coordinates are therefore Formulas (A.1) and (A.2) applied to the site medians
of the eight attributes. Because the formulas are linear, the alternative
``central_tendency="mean"`` gives the same point as the mean of the
respondents' own coordinates; the median of those coordinates is a third
reading, which the per-respondent values let a caller form.

**Formula (A.3).** The page prints :math:`r = 1 - 1\,\frac{6\sum
d_i^2}{n(n^2 - 1)}`, with a stray factor 1; read as a product it is the usual
coefficient for untied ranks, which is what is implemented.

**Formulas (B.1) and (B.2).** (B.2) divides the covariance by ``n``, so the
standard deviations of (B.1) are taken with ``n`` as well; with the ``n - 1``
of a sample standard deviation the coefficient would shrink by
:math:`(n - 1)/n`.

**Probability values.** A.4 and B.3 ask for the significance of each
coefficient and its probability value without naming a test. Both use the
Student :math:`t` statistic :math:`t = r\sqrt{(n - 2)/(1 - r^2)}` with
:math:`n - 2` degrees of freedom, which is exact for Pearson's coefficient of
bivariate normal data and the usual large-sample approximation for Spearman's. The 95 %
confidence interval of Method B uses the Student distribution with
:math:`n - 1` degrees of freedom about the mean, with the sample standard
deviation.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
from scipy import stats

from ..._internal.frozen import read_only
from ..._internal.validation import require_choice

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "METHOD_A_ALTERNATIVE_PART_1",
    "METHOD_A_SCALES",
    "METHOD_B_MAXIMUM_SOURCES",
    "METHOD_B_SCALES",
    "PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES",
    "PLEASANTNESS_EVENTFULNESS_RANGE",
    "MethodASummary",
    "MethodBSummary",
    "PleasantnessEventfulness",
    "QuestionnaireScale",
    "SoundscapeAcousticEnvironment",
    "SoundscapeCorrelation",
    "SoundscapeDataCollection",
    "SoundscapeParticipants",
    "SoundscapeReport",
    "SourceRanking",
    "method_a_scale_values",
    "method_a_summary",
    "method_b_scale_values",
    "method_b_source_ranking",
    "method_b_summary",
    "pearson_correlation",
    "pleasantness_eventfulness",
    "spearman_rank_correlation",
]


# ---------------------------------------------------------------------------
# The questionnaire of ISO/TS 12913-2 Annex C
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class QuestionnaireScale:
    """One scale of the soundscape questionnaire, as ISO/TS 12913-2 prints it.

    The text is transcribed from the figure, misprints included: the questions
    of Figures C.2 to C.4 read "To what extend" and their instructions
    "reponse alternative", which ``docs/ERRATA.md`` records; a study that
    prints its own questionnaire from this table should correct them.

    :ivar method: ``"A"`` (clause C.3.1, the questionnaire) or ``"B"`` (clause
        C.3.2, the soundwalk data collection).
    :ivar part: The part of the questionnaire the scale belongs to.
    :ivar figure: The figure of ISO/TS 12913-2 Annex C that prints it.
    :ivar subject: What the part assesses, as the heading of its clause and
        Table A.1 or Table B.1 of ISO/TS 12913-3 name it.
    :ivar question: The question, as printed.
    :ivar instruction: The instruction line under the question, as printed;
        empty where the figure has none.
    :ivar items: The rows rated on the same categories (the sound source types
        of part 1, the eight attributes of part 2); empty for a scale that
        rates the environment as a whole.
    :ivar categories: The response categories from the left-hand box to the
        right-hand one, as printed; for a continuous-category scale of Method
        B, the labels of its five ticks.
    :ivar scale_values: The scale value of each category, in the same order:
        ISO/TS 12913-3 Table A.1 for Method A, Table B.1 for Method B.
    :ivar continuous: Whether a mark may fall anywhere along the scale
        (Method B) rather than in one of the boxes (Method A).
    """

    method: str
    part: int
    figure: str
    subject: str
    question: str
    instruction: str
    items: tuple[str, ...]
    categories: tuple[str, ...]
    scale_values: tuple[int, ...]
    continuous: bool


#: The eight attributes of the perceived affective quality, part 2 of Method
#: A, in the order Figure C.4 of ISO/TS 12913-2 lists them. These are the
#: variables of Formulas (A.1) and (A.2) of ISO/TS 12913-3: ``p`` pleasant,
#: ``ch`` chaotic, ``v`` vibrant, ``u`` uneventful, ``ca`` calm, ``a``
#: annoying, ``e`` eventful, ``m`` monotonous.
PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES: tuple[str, ...] = (
    "pleasant",
    "chaotic",
    "vibrant",
    "uneventful",
    "calm",
    "annoying",
    "eventful",
    "monotonous",
)

_TICK_INSTRUCTION = "Please tick off one reponse alternative per type of sound"
_HUMAN_SOUNDS = (
    "Sounds from human beings (e.g., conversation, laughter, children at play, "
    "footsteps)"
)
_NATURAL_SOUNDS = (
    "Natural sounds (e.g., singing birds, flowing water, wind in vegetation)"
)
_HEAR_CATEGORIES = (
    "Not at all",
    "A little",
    "Moderately",
    "A lot",
    "Dominates completely",
)
_SOURCE_IDENTIFICATION = "sound source identification"
_ASCENDING = (1, 2, 3, 4, 5)
_DESCENDING = (5, 4, 3, 2, 1)

#: Method A of ISO/TS 12913-2 (clause C.3.1), keyed by the part of the
#: questionnaire: part 1, sound source identification (Figure C.2); part 2,
#: perceived affective quality (Figure C.4); part 3, assessment of the
#: surrounding sound environment (Figure C.5); part 4, appropriateness of the
#: surrounding sound environment (Figure C.6). The scale values are Table A.1
#: of ISO/TS 12913-3: parts 1 and 4 run 1 to 5 from the left-hand box, parts 2
#: and 3 run 5 to 1. Figure C.3, the alternative to Figure C.2 with three
#: source types, is :data:`METHOD_A_ALTERNATIVE_PART_1`.
METHOD_A_SCALES: Mapping[int, QuestionnaireScale] = MappingProxyType(
    {
        1: QuestionnaireScale(
            method="A",
            part=1,
            figure="C.2",
            subject=_SOURCE_IDENTIFICATION,
            question=(
                "To what extend do you presently hear the following four types "
                "of sounds?"
            ),
            instruction=_TICK_INSTRUCTION,
            items=(
                "Traffic noise (e.g., cars, buses, trains, air planes)",
                "Other noise (e.g., sirens, construction, industry, loading of goods)",
                _HUMAN_SOUNDS,
                _NATURAL_SOUNDS,
            ),
            categories=_HEAR_CATEGORIES,
            scale_values=_ASCENDING,
            continuous=False,
        ),
        2: QuestionnaireScale(
            method="A",
            part=2,
            figure="C.4",
            subject="perceived affective quality",
            question=(
                "For each of the 8 scales below, to what extend do you agree or "
                "disagree that the present surrounding sound environment is..."
            ),
            instruction="Please tick off one reponse alternative per scale",
            items=PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES,
            categories=(
                "Strongly agree",
                "Agree",
                "Neither agree, nor disagree",
                "Disagree",
                "Strongly disagree",
            ),
            scale_values=_DESCENDING,
            continuous=False,
        ),
        3: QuestionnaireScale(
            method="A",
            part=3,
            figure="C.5",
            subject="assessment of the surrounding sound environment",
            question=(
                "Overall, how would you describe the present surrounding sound "
                "environment?"
            ),
            instruction="",
            items=(),
            categories=(
                "Very good",
                "Good",
                "Neither good, nor bad",
                "Bad",
                "Very bad",
            ),
            scale_values=_DESCENDING,
            continuous=False,
        ),
        4: QuestionnaireScale(
            method="A",
            part=4,
            figure="C.6",
            subject="appropriateness of the surrounding sound environment",
            question=(
                "Overall, to what extent is the present surrounding sound "
                "environment appropriate to the present place?"
            ),
            instruction="",
            items=(),
            categories=("Not at all", "Slightly", "Moderately", "Very", "Perfectly"),
            scale_values=_ASCENDING,
            continuous=False,
        ),
    }
)

#: Figure C.3 of ISO/TS 12913-2, the alternative to Figure C.2 for part 1 of
#: Method A: one scale for each of the three main types of sound source, with
#: the categories and scale values of Figure C.2.
METHOD_A_ALTERNATIVE_PART_1: QuestionnaireScale = QuestionnaireScale(
    method="A",
    part=1,
    figure="C.3",
    subject=_SOURCE_IDENTIFICATION,
    question=(
        "To what extend do you presently hear the following three types of sounds?"
    ),
    instruction=_TICK_INSTRUCTION,
    items=(
        "Noise (e.g., traffic, construction, industry)",
        _HUMAN_SOUNDS,
        _NATURAL_SOUNDS,
    ),
    categories=_HEAR_CATEGORIES,
    scale_values=_ASCENDING,
    continuous=False,
)

_MARK_INSTRUCTION = "Mark your impression at any location on the scale below."
_DEGREE_TICKS = ("not at all", "slightly", "moderately", "very", "extremely")
_ASSESSMENT = "assessment of the sound environment"

#: Part 1 of Method B of ISO/TS 12913-2 (clause C.3.2.3), the four
#: continuous-category scales of Figure C.7, in the order printed. A mark may
#: fall anywhere along a scale; its scale value runs from 1 at the left-hand
#: tick to 5 at the right-hand one (ISO/TS 12913-3 B.2 and Table B.1). The
#: text of C.3.2.3 speaks of three scales labelled from "not at all" to
#: "extremely", and the figure prints four, the fourth labelled from "never"
#: to "very often"; ``docs/ERRATA.md`` records the difference, and all four
#: are here.
METHOD_B_SCALES: tuple[QuestionnaireScale, ...] = (
    QuestionnaireScale(
        method="B",
        part=1,
        figure="C.7",
        subject=_ASSESSMENT,
        question="How loud is it here?",
        instruction=_MARK_INSTRUCTION,
        items=(),
        categories=_DEGREE_TICKS,
        scale_values=_ASCENDING,
        continuous=True,
    ),
    QuestionnaireScale(
        method="B",
        part=1,
        figure="C.7",
        subject=_ASSESSMENT,
        question="How unpleasant is it here?",
        instruction=_MARK_INSTRUCTION,
        items=(),
        categories=_DEGREE_TICKS,
        scale_values=_ASCENDING,
        continuous=True,
    ),
    QuestionnaireScale(
        method="B",
        part=1,
        figure="C.7",
        subject=_ASSESSMENT,
        question="How appropriate is the sound to the surrounding?",
        instruction=_MARK_INSTRUCTION,
        items=(),
        categories=_DEGREE_TICKS,
        scale_values=_ASCENDING,
        continuous=True,
    ),
    QuestionnaireScale(
        method="B",
        part=1,
        figure="C.7",
        subject=_ASSESSMENT,
        question="How often would you like to visit this place again?",
        instruction=_MARK_INSTRUCTION,
        items=(),
        categories=("never", "rarely", "sometimes", "often", "very often"),
        scale_values=_ASCENDING,
        continuous=True,
    ),
)

#: Part 2 of Method B (ISO/TS 12913-2 C.3.2.4 and Figure C.8): the number of
#: sound sources a participant lists is "not predefined but limited to
#: eight", so a rank runs from 1, the most noticeable, to at most 8
#: (ISO/TS 12913-3 Table B.1).
METHOD_B_MAXIMUM_SOURCES = 8

#: The half-range of the coordinates of Formulas (A.1) and (A.2) of
#: ISO/TS 12913-3, :math:`4 + \sqrt{32} \approx 9.66`: every attribute at
#: one end of its scale and its opposite at the other gives
#: :math:`4 + 2 \cdot 4\cos 45^\circ`. Dividing by it maps the coordinates to
#: :math:`\pm 1`, as A.3 describes.
PLEASANTNESS_EVENTFULNESS_RANGE = 4.0 + math.sqrt(32.0)

#: The weight Formulas (A.1) and (A.2) give the two diagonal axes, which lie at
#: 45 degrees to pleasantness and eventfulness in Figure A.1.
_COS_45 = math.cos(math.radians(45.0))

#: The lowest and highest scale value of a five-category or continuous scale
#: (Tables A.1 and B.1).
_SCALE_MIN = 1.0
_SCALE_MAX = 5.0

#: The central tendencies :func:`pleasantness_eventfulness` accepts.
_CENTRAL_TENDENCIES = ("median", "mean")

#: The alternative hypotheses a probability value may be taken against.
_ALTERNATIVES = ("two-sided", "greater", "less")

#: The label of the one site of a set of responses given without sites.
_ALL = "all"

#: A table of answers is a matrix: one row per response, one column per item.
_MATRIX_RANK = 2

#: The fewest pairs a correlation coefficient and its probability value need:
#: the Student statistic has ``n - 2`` degrees of freedom.
_MIN_PAIRS = 3


# ---------------------------------------------------------------------------
# Shared validation
# ---------------------------------------------------------------------------


def _as_responses(
    values: ArrayLike, name: str, *, integer: bool
) -> NDArray[np.float64]:
    """A 1-D array of scale values, ``NaN`` where a question was left blank.

    :raises ValueError: for a value outside 1 to 5, an infinite value, or,
        when *integer*, a value between two categories.
    """
    if np.iscomplexobj(values):
        msg = f"'{name}' must hold real scale values."
        raise ValueError(msg)
    try:
        array = np.asarray(values, dtype=np.float64).ravel()
    except (TypeError, ValueError) as exc:
        msg = f"'{name}' must hold numeric scale values."
        raise ValueError(msg) from exc
    given = array[~np.isnan(array)]
    if np.any(np.isinf(given)) or np.any((given < _SCALE_MIN) | (given > _SCALE_MAX)):
        msg = (
            f"'{name}' must hold scale values from 1 to 5 (NaN for a blank "
            "answer); convert box positions with method_a_scale_values first."
        )
        raise ValueError(msg)
    if integer and np.any(np.mod(given, 1.0) > 0.0):
        msg = (
            f"'{name}' must hold whole scale values: a Method A box is 1, 2, 3, 4 or 5."
        )
        raise ValueError(msg)
    return array


def _site_groups(
    sites: ArrayLike | Sequence[object] | None, n: int
) -> tuple[tuple[str, ...], list[NDArray[np.intp]]]:
    """The site labels in order of first appearance, and each site's rows."""
    if sites is None:
        return (_ALL,), [np.arange(n)]
    labels = [str(site) for site in np.asarray(sites, dtype=object).ravel()]
    if len(labels) != n:
        msg = f"'sites' must name the site of every response: {n} responses, {len(labels)} sites."
        raise ValueError(msg)
    order: dict[str, list[int]] = {}
    for row, label in enumerate(labels):
        order.setdefault(label, []).append(row)
    return tuple(order), [np.asarray(rows, dtype=np.intp) for rows in order.values()]


def _columns(
    scale_values: Mapping[str, ArrayLike] | ArrayLike,
    default_items: Sequence[tuple[str, ...]],
    single_item: str,
    *,
    integer: bool,
) -> tuple[tuple[str, ...], NDArray[np.float64]]:
    """Items and an ``(n, items)`` matrix from a mapping or an array.

    A mapping names its own items. A 1-D array is one scale named
    *single_item*; a 2-D array ``(responses, items)`` takes the item names of
    the first entry of *default_items* with as many items as it has columns.
    """
    if isinstance(scale_values, Mapping):
        items = tuple(str(key) for key in scale_values)
        if not items:
            msg = "'scale_values' must hold at least one item."
            raise ValueError(msg)
        arrays = [
            _as_responses(scale_values[key], f"scale_values[{key!r}]", integer=integer)
            for key in scale_values
        ]
        lengths = {a.size for a in arrays}
        if len(lengths) != 1:
            msg = (
                "'scale_values' must hold the same number of responses for every item."
            )
            raise ValueError(msg)
        return items, np.column_stack(arrays)
    matrix = np.asarray(scale_values, dtype=object)
    if matrix.ndim == 1:
        return (single_item,), _as_responses(
            scale_values, "scale_values", integer=integer
        ).reshape(-1, 1)
    if matrix.ndim != _MATRIX_RANK:
        msg = "'scale_values' must be a mapping, a 1-D array or a 2-D (responses, items) array."
        raise ValueError(msg)
    columns = matrix.shape[1]
    for items in default_items:
        if len(items) == columns:
            flat = _as_responses(scale_values, "scale_values", integer=integer)
            return items, flat.reshape(-1, columns)
    counts = sorted({len(items) for items in default_items})
    msg = (
        f"'scale_values' has {columns} columns; this part has {counts} items, "
        "or pass a mapping from item name to values."
    )
    raise ValueError(msg)


def _nan_statistic(
    matrix: NDArray[np.float64], groups: list[NDArray[np.intp]], statistic: str
) -> NDArray[np.float64]:
    """A per-site, per-item statistic over the answers given, ``NaN`` for none."""
    out = np.full((len(groups), matrix.shape[1]), np.nan)
    for i, rows in enumerate(groups):
        for j in range(matrix.shape[1]):
            answered = matrix[rows, j]
            answered = answered[~np.isnan(answered)]
            if answered.size:
                out[i, j] = float(getattr(np, statistic)(answered))
    return out


def _answer_counts(
    matrix: NDArray[np.float64], groups: list[NDArray[np.intp]]
) -> NDArray[np.int64]:
    return np.asarray(
        [np.sum(~np.isnan(matrix[rows]), axis=0) for rows in groups], dtype=np.int64
    ).reshape(len(groups), matrix.shape[1])


# ---------------------------------------------------------------------------
# Method A: scale values, median and range
# ---------------------------------------------------------------------------


def _method_a_scale(part: int) -> QuestionnaireScale:
    if isinstance(part, bool) or part not in METHOD_A_SCALES:
        msg = f"'part' must be 1, 2, 3 or 4 (the parts of Method A), got {part!r}."
        raise ValueError(msg)
    return METHOD_A_SCALES[part]


def method_a_scale_values(
    positions: ArrayLike, *, part: int
) -> float | NDArray[np.float64]:
    """The scale value of a ticked box of Method A (ISO/TS 12913-3 Table A.1).

    A box is counted from the left-hand end of its scale, 1 to 5, as the
    questionnaire of ISO/TS 12913-2 prints it. Parts 1 and 4 assign the scale
    values 1 to 5 from left to right, so the value is the position; parts 2
    and 3 assign 5 to 1, so "strongly agree" (part 2) and "very good" (part 3)
    are 5 and the value is ``6 - position``.

    :param positions: The position of each ticked box, 1 (left) to 5 (right);
        ``NaN`` for a question left blank.
    :param part: The part of the questionnaire, 1 to 4.
    :return: The scale values, a float for a scalar input.
    :raises ValueError: for a part other than 1 to 4 or a position that is
        not a whole number from 1 to 5.
    """
    scale = _method_a_scale(part)
    array = np.asarray(positions, dtype=np.float64)
    checked = _as_responses(array, "positions", integer=True).reshape(array.shape)
    values = (
        checked if scale.scale_values == _ASCENDING else (_SCALE_MAX + 1.0) - checked
    )
    return float(values) if values.ndim == 0 else values


@dataclass(frozen=True)
class MethodASummary:
    """Median and range of Method A responses per site and item
    (ISO/TS 12913-3 A.2 and Table A.1).

    The level of measurement of every Method A scale is ordinal, so the
    median is the measure of central tendency and the range, the largest
    scale value given less the smallest, the measure of dispersion. A blank
    answer is left out of both; a site where nobody answered an item has
    ``NaN`` there and a count of zero.

    :ivar part: The part of the questionnaire, 1 to 4.
    :ivar items: The items rated (the attributes, the source types), or the
        subject of the part for a single scale.
    :ivar sites: The sites, in the order they first appear in the responses.
    :ivar medians: Median scale value, shape ``(sites, items)``.
    :ivar minima: Smallest scale value given, shape ``(sites, items)``.
    :ivar maxima: Largest scale value given, shape ``(sites, items)``.
    :ivar ranges: ``maxima - minima``, the measure of dispersion.
    :ivar counts: Number of answers, shape ``(sites, items)``.
    """

    part: int
    items: tuple[str, ...]
    sites: tuple[str, ...]
    medians: NDArray[np.float64]
    minima: NDArray[np.float64]
    maxima: NDArray[np.float64]
    ranges: NDArray[np.float64]
    counts: NDArray[np.int64]

    def __post_init__(self) -> None:
        """Refuse columns that disagree with the sites and items they describe.

        :raises ValueError: if a matrix is not ``(sites, items)``.
        """
        shape = (len(self.sites), len(self.items))
        for name in ("medians", "minima", "maxima", "ranges", "counts"):
            if np.shape(getattr(self, name)) != shape:
                msg = (
                    f"MethodASummary: '{name}' must have shape {shape} (sites, items)."
                )
                raise ValueError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the median of each item per site, with its range as a bar.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the median markers.
        :return: The axes. Requires matplotlib (``pip install phonometry[plot]``).
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_method_a_summary

        return plot_method_a_summary(
            self, ax=ax, language=check_language(language), **kwargs
        )


def method_a_summary(
    scale_values: Mapping[str, ArrayLike] | ArrayLike,
    *,
    part: int,
    sites: ArrayLike | Sequence[object] | None = None,
) -> MethodASummary:
    """Median and range of the Method A scale values per site and item
    (ISO/TS 12913-3 A.2, Table A.1).

    :param scale_values: The scale values of Table A.1, 1 to 5, ``NaN`` for a
        blank answer: a mapping from item name to one value per response; or,
        for a part with a single scale (3, 4), a 1-D array; or a 2-D array
        ``(responses, items)`` in the order of the part's figure (part 1: four
        columns for Figure C.2 or three for Figure C.3; part 2: the eight
        attributes of Figure C.4). Box positions are converted with
        :func:`method_a_scale_values` first.
    :param part: The part of the questionnaire, 1 to 4.
    :param sites: The site of each response, any labels; ``None`` puts every
        response at one site named ``"all"``.
    :return: A :class:`MethodASummary`.
    :raises ValueError: for a part other than 1 to 4, a scale value that is
        not a whole number from 1 to 5, or sites that do not match the
        responses.
    """
    scale = _method_a_scale(part)
    defaults = [scale.items] if scale.items else []
    if part == 1:
        defaults.append(METHOD_A_ALTERNATIVE_PART_1.items)
    items, matrix = _columns(scale_values, defaults, scale.subject, integer=True)
    labels, groups = _site_groups(sites, matrix.shape[0])
    medians = _nan_statistic(matrix, groups, "median")
    minima = _nan_statistic(matrix, groups, "min")
    maxima = _nan_statistic(matrix, groups, "max")
    return MethodASummary(
        part=part,
        items=items,
        sites=labels,
        medians=read_only(medians),
        minima=read_only(minima),
        maxima=read_only(maxima),
        ranges=read_only(maxima - minima),
        counts=read_only(_answer_counts(matrix, groups)),
    )


# ---------------------------------------------------------------------------
# Method A: pleasantness and eventfulness, Formulas (A.1) and (A.2)
# ---------------------------------------------------------------------------


def _formulas_a1_a2(
    attributes: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Formulas (A.1) and (A.2) on the last axis, in the attribute order."""
    p, ch, v, u, ca, a, e, m = np.moveaxis(attributes, -1, 0)
    pleasantness = (p - a) + _COS_45 * (ca - ch) + _COS_45 * (v - m)
    eventfulness = (e - u) + _COS_45 * (ch - ca) + _COS_45 * (v - m)
    return np.asarray(pleasantness), np.asarray(eventfulness)


@dataclass(frozen=True)
class PleasantnessEventfulness:
    r"""Pleasantness and eventfulness of each site and each respondent
    (ISO/TS 12913-3 A.3, Formulas (A.1) and (A.2)).

    .. math::

       P = (p - a) + \cos 45^\circ (ca - ch) + \cos 45^\circ (v - m)

       E = (e - u) + \cos 45^\circ (ch - ca) + \cos 45^\circ (v - m)

    on the scale values of the eight attributes of part 2. The coordinates
    range over :math:`\pm (4 + \sqrt{32}) \approx \pm 9.66`; the
    ``normalized_*`` properties divide by that, for the :math:`\pm 1` of A.3.

    :ivar sites: The sites, in the order they first appear.
    :ivar central_tendency: ``"median"`` or ``"mean"``, the statistic of each
        attribute per site that the site coordinates are computed from.
    :ivar attribute_values: That statistic, shape ``(sites, 8)`` in the order
        of :data:`PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES`.
    :ivar pleasantness: :math:`P` of each site.
    :ivar eventfulness: :math:`E` of each site.
    :ivar respondent_sites: The site of each respondent.
    :ivar respondent_pleasantness: :math:`P` of each respondent, ``NaN`` where
        one of the six attributes of Formula (A.1) was left blank.
    :ivar respondent_eventfulness: :math:`E` of each respondent, ``NaN`` where
        one of the six attributes of Formula (A.2) was left blank.
    :ivar respondent_counts: Respondents per site who answered all eight.
    """

    sites: tuple[str, ...]
    central_tendency: str
    attribute_values: NDArray[np.float64]
    pleasantness: NDArray[np.float64]
    eventfulness: NDArray[np.float64]
    respondent_sites: tuple[str, ...]
    respondent_pleasantness: NDArray[np.float64]
    respondent_eventfulness: NDArray[np.float64]
    respondent_counts: NDArray[np.int64]

    def __post_init__(self) -> None:
        """Refuse per-site and per-respondent columns of different lengths.

        :raises ValueError: if the columns disagree with the site or
            respondent labels.
        """
        sites = (len(self.sites),)
        for name in ("pleasantness", "eventfulness", "respondent_counts"):
            if np.shape(getattr(self, name)) != sites:
                msg = (
                    f"PleasantnessEventfulness: '{name}' must hold one value per site."
                )
                raise ValueError(msg)
        if np.shape(self.attribute_values) != (len(self.sites), 8):
            msg = "PleasantnessEventfulness: 'attribute_values' must be (sites, 8)."
            raise ValueError(msg)
        respondents = (len(self.respondent_sites),)
        for name in ("respondent_pleasantness", "respondent_eventfulness"):
            if np.shape(getattr(self, name)) != respondents:
                msg = (
                    f"PleasantnessEventfulness: '{name}' must hold one value per "
                    "respondent."
                )
                raise ValueError(msg)

    @property
    def normalized_pleasantness(self) -> NDArray[np.float64]:
        r""":math:`P / (4 + \sqrt{32})` of each site, in :math:`\pm 1`."""
        return self.pleasantness / PLEASANTNESS_EVENTFULNESS_RANGE

    @property
    def normalized_eventfulness(self) -> NDArray[np.float64]:
        r""":math:`E / (4 + \sqrt{32})` of each site, in :math:`\pm 1`."""
        return self.eventfulness / PLEASANTNESS_EVENTFULNESS_RANGE

    def plot(
        self,
        ax: Axes | None = None,
        *,
        normalized: bool = True,
        respondents: bool = False,
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        r"""Plot the sites on the two-dimensional model of Figure A.1.

        Pleasantness on the horizontal axis and eventfulness on the vertical
        one, with the eight attributes at the ends of their axes, the diagonal
        ones at 45 degrees, and every site a point.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param normalized: Draw the coordinates divided by
            :math:`4 + \sqrt{32}` (default), in :math:`\pm 1`; ``False``
            draws them raw, in :math:`\pm 9.66`.
        :param respondents: Also draw every respondent, faintly, in the colour
            of their site.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the site markers.
        :return: The axes. Requires matplotlib (``pip install phonometry[plot]``).
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_pleasantness_eventfulness

        return plot_pleasantness_eventfulness(
            self,
            ax=ax,
            normalized=normalized,
            respondents=respondents,
            language=check_language(language),
            **kwargs,
        )


def pleasantness_eventfulness(
    scale_values: Mapping[str, ArrayLike] | ArrayLike,
    *,
    sites: ArrayLike | Sequence[object] | None = None,
    central_tendency: Literal["median", "mean"] = "median",
) -> PleasantnessEventfulness:
    r"""Pleasantness and eventfulness of a soundscape from its perceived
    affective quality (ISO/TS 12913-3 A.3, Formulas (A.1) and (A.2)).

    The scale values are those of part 2 of Method A, 5 for "strongly agree"
    down to 1 for "strongly disagree" (Table A.1); :func:`method_a_scale_values`
    converts box positions, which run the other way. Every respondent who
    answered all eight attributes gets a coordinate pair. Each site gets the
    pair of Formulas (A.1) and (A.2) applied to the site's median of each
    attribute (A.2 makes the median the central tendency of the scale), or to
    its mean with ``central_tendency="mean"``, which is also the mean of the
    respondents' coordinates since the formulas are linear.

    Clause A.3 says the formulas process "the results from part 3"; the
    attributes they name are part 2, and that is what they are applied to
    (see the module docstring and ``docs/ERRATA.md``).

    :param scale_values: The eight attributes: a mapping from each name of
        :data:`PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES` to one scale value per
        respondent, or a 2-D array ``(respondents, 8)`` in that order. ``NaN``
        marks a blank answer. A row may also be a statistic of a group of
        answers, such as a site's medians, which is why a value between two
        boxes is accepted here; anything outside 1 to 5 is not a scale value.
    :param sites: The site of each respondent, any labels; ``None`` puts
        every respondent at one site named ``"all"``.
    :param central_tendency: ``"median"`` (default) or ``"mean"``.
    :return: A :class:`PleasantnessEventfulness`.
    :raises ValueError: for a mapping that does not name the eight
        attributes, a value outside 1 to 5, or sites that do not match the
        respondents.
    """
    require_choice(central_tendency, "central_tendency", _CENTRAL_TENDENCIES)
    if isinstance(scale_values, Mapping):
        missing = set(PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES) - set(scale_values)
        extra = set(scale_values) - set(PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES)
        if missing or extra:
            msg = (
                "'scale_values' must name exactly the eight attributes "
                f"{PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES}; missing "
                f"{sorted(missing)}, unexpected {sorted(extra)}."
            )
            raise ValueError(msg)
        ordered = {
            name: scale_values[name] for name in PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES
        }
        _, matrix = _columns(ordered, [], "", integer=False)
    else:
        _, matrix = _columns(
            scale_values, [PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES], "", integer=False
        )
        if matrix.shape[1] != len(PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES):
            msg = "'scale_values' must be (respondents, 8) in the attribute order."
            raise ValueError(msg)
    labels, groups = _site_groups(sites, matrix.shape[0])
    respondent_p, respondent_e = _formulas_a1_a2(matrix)
    attribute_values = _nan_statistic(matrix, groups, central_tendency)
    site_p, site_e = _formulas_a1_a2(attribute_values)
    complete = ~np.isnan(matrix).any(axis=1)
    row_site = np.empty(matrix.shape[0], dtype=object)
    for label, rows in zip(labels, groups, strict=True):
        row_site[rows] = label
    return PleasantnessEventfulness(
        sites=labels,
        central_tendency=central_tendency,
        attribute_values=read_only(attribute_values),
        pleasantness=read_only(np.asarray(site_p, dtype=np.float64)),
        eventfulness=read_only(np.asarray(site_e, dtype=np.float64)),
        respondent_sites=tuple(str(s) for s in row_site),
        respondent_pleasantness=read_only(respondent_p.astype(np.float64)),
        respondent_eventfulness=read_only(respondent_e.astype(np.float64)),
        respondent_counts=read_only(
            np.asarray([int(np.sum(complete[rows])) for rows in groups], dtype=np.int64)
        ),
    )


# ---------------------------------------------------------------------------
# Correlation: Formulas (A.3), (A.4), (B.1) and (B.2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SoundscapeCorrelation:
    r"""A correlation coefficient between two variables and its probability
    value (ISO/TS 12913-3 A.4 and B.3).

    :ivar method: ``"spearman"`` (ordinal data, A.4) or ``"pearson"``
        (interval data, B.3).
    :ivar formula: The formula that gave the coefficient: ``"(A.3)"`` for
        untied ranks, ``"(A.4)"`` for tied ranks, ``"(B.1)"`` for Pearson.
    :ivar coefficient: The correlation coefficient, in ``[-1, 1]``.
    :ivar p_value: Probability, under the null hypothesis of no correlation,
        of a coefficient at least as extreme as this one in the direction
        ``alternative`` names (either sign for ``"two-sided"``).
    :ivar t_statistic: The Student statistic the probability value comes
        from, :math:`r\sqrt{(n - 2)/(1 - r^2)}`; infinite for :math:`|r| = 1`.
    :ivar degrees_of_freedom: :math:`n - 2`.
    :ivar alternative: ``"two-sided"``, ``"greater"`` or ``"less"``.
    :ivar x: The first variable, as given.
    :ivar y: The second variable, as given.
    :ivar x_ranks: The ranks of ``x`` (average ranks for ties); ``None`` for
        Pearson.
    :ivar y_ranks: The ranks of ``y``; ``None`` for Pearson.
    """

    method: str
    formula: str
    coefficient: float
    p_value: float
    t_statistic: float
    degrees_of_freedom: int
    alternative: str
    x: NDArray[np.float64]
    y: NDArray[np.float64]
    x_ranks: NDArray[np.float64] | None = None
    y_ranks: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        """Refuse a coefficient outside [-1, 1] or variables of two lengths.

        :raises ValueError: if the coefficient or the probability is out of
            range, or the paired columns disagree.
        """
        if not -1.0 <= self.coefficient <= 1.0:
            msg = "SoundscapeCorrelation: 'coefficient' must be in [-1, 1]."
            raise ValueError(msg)
        if not 0.0 <= self.p_value <= 1.0:
            msg = "SoundscapeCorrelation: 'p_value' must be in [0, 1]."
            raise ValueError(msg)
        n = np.size(self.x)
        for name in ("y", "x_ranks", "y_ranks"):
            value = getattr(self, name)
            if value is not None and np.shape(value) != (n,):
                msg = f"SoundscapeCorrelation: '{name}' must pair with 'x'."
                raise ValueError(msg)

    @property
    def n(self) -> int:
        """Number of cases, the pairs the coefficient was computed from."""
        return int(np.size(self.x))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the pairs, as ranks for Spearman, with the coefficient.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the scatter markers.
        :return: The axes. Requires matplotlib (``pip install phonometry[plot]``).
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_soundscape_correlation

        return plot_soundscape_correlation(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _paired(
    x: ArrayLike, y: ArrayLike
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Two finite 1-D arrays of one length, at least three pairs, not constant."""
    arrays = []
    for name, values in (("x", x), ("y", y)):
        if np.iscomplexobj(values):
            msg = f"'{name}' must be real."
            raise ValueError(msg)
        array = np.asarray(values, dtype=np.float64).ravel()
        if not np.all(np.isfinite(array)):
            msg = f"'{name}' must be finite; drop the incomplete pairs first."
            raise ValueError(msg)
        arrays.append(array)
    x_arr, y_arr = arrays
    if x_arr.size != y_arr.size:
        msg = f"'x' and 'y' must pair up: {x_arr.size} and {y_arr.size} values."
        raise ValueError(msg)
    if x_arr.size < _MIN_PAIRS:
        msg = f"'x' and 'y' must hold at least {_MIN_PAIRS} pairs for a probability value."
        raise ValueError(msg)
    for name, array in (("x", x_arr), ("y", y_arr)):
        if np.ptp(array) <= 0.0:
            msg = f"'{name}' is constant, so it correlates with nothing."
            raise ValueError(msg)
    return x_arr, y_arr


def _significance(r: float, n: int, alternative: str) -> tuple[float, float]:
    """The Student statistic of ``r`` and its probability value."""
    dof = n - 2
    residual = 1.0 - r * r
    t = math.copysign(math.inf, r) if residual <= 0.0 else r * math.sqrt(dof / residual)
    if alternative == "two-sided":
        p = 2.0 * float(stats.t.sf(abs(t), dof))
    elif alternative == "greater":
        p = float(stats.t.sf(t, dof))
    else:
        p = float(stats.t.cdf(t, dof))
    return t, min(max(p, 0.0), 1.0)


def _tie_term(ranks: NDArray[np.float64]) -> float:
    r"""``T`` or ``U`` of Formula (A.4): :math:`\sum_j (t_j^3 - t_j)/12`."""
    _, counts = np.unique(ranks, return_counts=True)
    tied = counts[counts > 1].astype(np.float64)
    return float(np.sum(tied**3 - tied) / 12.0)


def spearman_rank_correlation(
    x: ArrayLike,
    y: ArrayLike,
    *,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> SoundscapeCorrelation:
    r"""Spearman's rank correlation coefficient, for ordinal data
    (ISO/TS 12913-3 A.4, Formulas (A.3) and (A.4)).

    Each variable is ranked, tied values sharing the mean of the ranks they
    span, and :math:`d_i` is the difference of the ranks of pair :math:`i`.
    Without ties Formula (A.3) applies,

    .. math::

       r_\mathrm{spearman} = 1 - \frac{6 \sum_{i=1}^{n} d_i^2}{n(n^2 - 1)},

    and with ties in either variable Formula (A.4),

    .. math::

       r_\mathrm{spearman} = \frac{2\,\frac{n^3 - n}{12} - T - U - \sum d_i^2}
       {2\sqrt{\left(\frac{n^3 - n}{12} - T\right)
       \left(\frac{n^3 - n}{12} - U\right)}},
       \qquad T = \frac{\sum_{j} (t_j^3 - t_j)}{12},

    where :math:`t_j` is the number of values in the :math:`j`-th group of
    tied ranks of ``x`` and ``U`` is the same sum over ``y``. Formula (A.4)
    is Pearson's coefficient of the average ranks, and reduces to (A.3) when
    nothing is tied.

    The probability value is that of the Student statistic
    :math:`r\sqrt{(n - 2)/(1 - r^2)}` with :math:`n - 2` degrees of freedom,
    the usual approximation for Spearman's coefficient, which A.4 asks to be
    reported without naming a test.

    :param x: The first variable, for instance the median rating of each site.
    :param y: The second, for instance an acoustic indicator of each site.
    :param alternative: The alternative hypothesis: ``"two-sided"``
        (default), ``"greater"`` (positive correlation) or ``"less"``.
    :return: A :class:`SoundscapeCorrelation`.
    :raises ValueError: for variables of different lengths, fewer than three
        pairs, a non-finite value or a constant variable.
    """
    require_choice(alternative, "alternative", _ALTERNATIVES)
    x_arr, y_arr = _paired(x, y)
    n = x_arr.size
    x_ranks = stats.rankdata(x_arr, method="average").astype(np.float64)
    y_ranks = stats.rankdata(y_arr, method="average").astype(np.float64)
    d_squared = float(np.sum((x_ranks - y_ranks) ** 2))
    tie_x, tie_y = _tie_term(x_ranks), _tie_term(y_ranks)
    if tie_x > 0.0 or tie_y > 0.0:
        base = (n**3 - n) / 12.0
        numerator = 2.0 * base - tie_x - tie_y - d_squared
        coefficient = numerator / (2.0 * math.sqrt((base - tie_x) * (base - tie_y)))
        formula = "(A.4)"
    else:
        coefficient = 1.0 - 6.0 * d_squared / (n * (n * n - 1.0))
        formula = "(A.3)"
    coefficient = min(max(coefficient, -1.0), 1.0)
    t, p = _significance(coefficient, n, alternative)
    return SoundscapeCorrelation(
        method="spearman",
        formula=formula,
        coefficient=coefficient,
        p_value=p,
        t_statistic=t,
        degrees_of_freedom=n - 2,
        alternative=alternative,
        x=read_only(x_arr),
        y=read_only(y_arr),
        x_ranks=read_only(x_ranks),
        y_ranks=read_only(y_ranks),
    )


def pearson_correlation(
    x: ArrayLike,
    y: ArrayLike,
    *,
    alternative: Literal["two-sided", "greater", "less"] = "two-sided",
) -> SoundscapeCorrelation:
    r"""Pearson's correlation coefficient, for interval data
    (ISO/TS 12913-3 B.3, Formulas (B.1) and (B.2)).

    .. math::

       r = \frac{\operatorname{cov}(x, y)}{\sigma_x \sigma_y}, \qquad
       \operatorname{cov}(x, y) = \frac{1}{n}\sum_{i=1}^{n}
       (x_i - \bar{x})(y_i - \bar{y}).

    Formula (B.2) divides by ``n``, so the standard deviations are taken with
    ``n`` too, which makes :math:`r` the usual coefficient; with the ``n - 1``
    of a sample standard deviation it would shrink by :math:`(n - 1)/n`. The
    probability value is that of the Student statistic
    :math:`r\sqrt{(n - 2)/(1 - r^2)}` with :math:`n - 2` degrees of freedom,
    exact for bivariate normal data.

    :param x: The first variable, for instance the mean Method B rating of
        each site.
    :param y: The second, for instance an acoustic indicator of each site.
    :param alternative: The alternative hypothesis: ``"two-sided"``
        (default), ``"greater"`` or ``"less"``.
    :return: A :class:`SoundscapeCorrelation`.
    :raises ValueError: for variables of different lengths, fewer than three
        pairs, a non-finite value or a constant variable.
    """
    require_choice(alternative, "alternative", _ALTERNATIVES)
    x_arr, y_arr = _paired(x, y)
    n = x_arr.size
    covariance = float(np.sum((x_arr - x_arr.mean()) * (y_arr - y_arr.mean())) / n)
    sigma_x = float(np.std(x_arr))
    sigma_y = float(np.std(y_arr))
    coefficient = min(max(covariance / (sigma_x * sigma_y), -1.0), 1.0)
    t, p = _significance(coefficient, n, alternative)
    return SoundscapeCorrelation(
        method="pearson",
        formula="(B.1)",
        coefficient=coefficient,
        p_value=p,
        t_statistic=t,
        degrees_of_freedom=n - 2,
        alternative=alternative,
        x=read_only(x_arr),
        y=read_only(y_arr),
    )


# ---------------------------------------------------------------------------
# Method B: continuous-category scales and the source ranking
# ---------------------------------------------------------------------------


def method_b_scale_values(marked_fraction: ArrayLike) -> float | NDArray[np.float64]:
    """The scale value of a mark on a Method B scale (ISO/TS 12913-3 B.2).

    A continuous-category scale of Figure C.7 runs from its left-hand tick
    ("not at all", or "never" on the fourth scale), scale value 1, to its
    right-hand one ("extremely", or "very often"), scale value 5, and a
    mark may fall anywhere along it. Its position is measured with a ruler, or on
    screen, as a fraction of the distance between the two end ticks, and the
    value is :math:`1 + 4f` rounded to one decimal, the resolution B.2
    requires ("determined at least with one decimal place").

    :param marked_fraction: The position of each mark from the left-hand
        tick, 0, to the right-hand one, 1; ``NaN`` for a scale left blank.
    :return: The scale values, a float for a scalar input.
    :raises ValueError: for a fraction outside 0 to 1 or an infinite one.
    """
    fraction = np.asarray(marked_fraction, dtype=np.float64)
    given = fraction[~np.isnan(fraction)]
    if np.any(np.isinf(given)) or np.any((given < 0.0) | (given > 1.0)):
        msg = (
            "'marked_fraction' must lie from 0 (left-hand tick) to 1 (right-hand tick)."
        )
        raise ValueError(msg)
    values = np.round(_SCALE_MIN + (_SCALE_MAX - _SCALE_MIN) * fraction, 1)
    return float(values) if values.ndim == 0 else values


@dataclass(frozen=True)
class MethodBSummary:
    """Arithmetic mean, standard deviation and confidence interval of Method
    B ratings per site and scale (ISO/TS 12913-3 B.2 and Table B.1).

    The level of measurement of the continuous-category scales is interval,
    so B.2 reports the arithmetic mean with its standard deviation and 95 %
    confidence interval. "Statistics for an ordinal scale level may be
    additionally applied", so the median is here too. A blank answer is left
    out; a site with fewer than two answers to a scale has no standard
    deviation or interval there (``NaN``).

    :ivar items: The scales (their questions, for Figure C.7).
    :ivar sites: The sites, in the order they first appear.
    :ivar means: Arithmetic mean, shape ``(sites, items)``.
    :ivar standard_deviations: Sample standard deviation, with ``n - 1``.
    :ivar confidence_lower: Lower end of the confidence interval of the mean.
    :ivar confidence_upper: Upper end of the confidence interval of the mean.
    :ivar medians: Median, the ordinal statistic.
    :ivar counts: Number of answers.
    :ivar confidence_level: The level of the interval, ``0.95`` unless chosen.
    """

    items: tuple[str, ...]
    sites: tuple[str, ...]
    means: NDArray[np.float64]
    standard_deviations: NDArray[np.float64]
    confidence_lower: NDArray[np.float64]
    confidence_upper: NDArray[np.float64]
    medians: NDArray[np.float64]
    counts: NDArray[np.int64]
    confidence_level: float

    def __post_init__(self) -> None:
        """Refuse columns that disagree with the sites and scales.

        :raises ValueError: if a matrix is not ``(sites, items)`` or the
            confidence level is not strictly between 0 and 1.
        """
        shape = (len(self.sites), len(self.items))
        for name in (
            "means",
            "standard_deviations",
            "confidence_lower",
            "confidence_upper",
            "medians",
            "counts",
        ):
            if np.shape(getattr(self, name)) != shape:
                msg = (
                    f"MethodBSummary: '{name}' must have shape {shape} (sites, items)."
                )
                raise ValueError(msg)
        if not 0.0 < self.confidence_level < 1.0:
            msg = (
                "MethodBSummary: 'confidence_level' must lie strictly between 0 and 1."
            )
            raise ValueError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the mean of each scale per site with its confidence interval.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the mean markers.
        :return: The axes. Requires matplotlib (``pip install phonometry[plot]``).
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_method_b_summary

        return plot_method_b_summary(
            self, ax=ax, language=check_language(language), **kwargs
        )


def method_b_summary(
    scale_values: Mapping[str, ArrayLike] | ArrayLike,
    *,
    sites: ArrayLike | Sequence[object] | None = None,
    confidence_level: float = 0.95,
) -> MethodBSummary:
    r"""Mean, standard deviation and confidence interval of Method B
    ratings per site (ISO/TS 12913-3 B.2, Table B.1).

    The confidence interval of the mean is
    :math:`\bar{x} \pm t_{(1+\gamma)/2,\,n-1}\, s/\sqrt{n}`, with :math:`s`
    the sample standard deviation and :math:`\gamma` the confidence level,
    95 % as B.2 asks.

    :param scale_values: The scale values from 1 to 5, read to one
        decimal by :func:`method_b_scale_values`, ``NaN`` for a blank: a
        mapping from scale name to one value per response, a 1-D array for one
        scale, or a 2-D array ``(responses, scales)`` whose three or four
        columns are the scales of Figure C.7 in their printed order.
    :param sites: The site of each response; ``None`` puts every response at
        one site named ``"all"``.
    :param confidence_level: The level of the interval, ``0.95`` by default.
    :return: A :class:`MethodBSummary`.
    :raises ValueError: for a value outside 1 to 5, a confidence level not
        strictly between 0 and 1, or sites that do not match the responses.
    """
    if not 0.0 < confidence_level < 1.0:
        msg = "'confidence_level' must lie strictly between 0 and 1."
        raise ValueError(msg)
    questions = tuple(scale.question for scale in METHOD_B_SCALES)
    items, matrix = _columns(
        scale_values,
        [questions, questions[:3]],
        METHOD_B_SCALES[0].subject,
        integer=False,
    )
    labels, groups = _site_groups(sites, matrix.shape[0])
    counts = _answer_counts(matrix, groups)
    means = _nan_statistic(matrix, groups, "mean")
    medians = _nan_statistic(matrix, groups, "median")
    sd = np.full_like(means, np.nan)
    for i, rows in enumerate(groups):
        for j in range(matrix.shape[1]):
            answered = matrix[rows, j]
            answered = answered[~np.isnan(answered)]
            if answered.size > 1:
                sd[i, j] = float(np.std(answered, ddof=1))
    with np.errstate(invalid="ignore"):
        dof = np.where(counts > 1, counts - 1, np.nan)
        quantile = stats.t.ppf(0.5 * (1.0 + confidence_level), dof)
        half = quantile * sd / np.sqrt(np.where(counts > 0, counts, np.nan))
    return MethodBSummary(
        items=items,
        sites=labels,
        means=read_only(means),
        standard_deviations=read_only(sd),
        confidence_lower=read_only(np.asarray(means - half, dtype=np.float64)),
        confidence_upper=read_only(np.asarray(means + half, dtype=np.float64)),
        medians=read_only(medians),
        counts=read_only(counts),
        confidence_level=float(confidence_level),
    )


@dataclass(frozen=True)
class SourceRanking:
    """The rank each recognised sound source was given, per site
    (ISO/TS 12913-3 B.2, part 2 of Method B, Table B.1).

    Every participant lists the sources they noticed from the most noticeable
    down, at most eight, so a source listed first has rank 1. The level of
    measurement is ordinal: the median rank is the central tendency and the
    range the dispersion. Sources are ordered by their median rank over all
    sites, then by how often they were listed.

    :ivar sources: Every source listed at any site.
    :ivar sites: The sites, in the order they first appear.
    :ivar median_ranks: Median rank, shape ``(sites, sources)``; ``NaN`` where
        nobody at the site listed the source.
    :ivar lowest_ranks: The best rank the source was given, same shape.
    :ivar highest_ranks: The worst rank it was given, same shape.
    :ivar rank_ranges: ``highest_ranks - lowest_ranks``, the dispersion.
    :ivar mentions: How many participants listed the source, same shape.
    :ivar participants: Participants per site.
    """

    sources: tuple[str, ...]
    sites: tuple[str, ...]
    median_ranks: NDArray[np.float64]
    lowest_ranks: NDArray[np.float64]
    highest_ranks: NDArray[np.float64]
    rank_ranges: NDArray[np.float64]
    mentions: NDArray[np.int64]
    participants: NDArray[np.int64]

    def __post_init__(self) -> None:
        """Refuse columns that disagree with the sites and sources.

        :raises ValueError: if a matrix is not ``(sites, sources)``.
        """
        shape = (len(self.sites), len(self.sources))
        for name in (
            "median_ranks",
            "lowest_ranks",
            "highest_ranks",
            "rank_ranges",
            "mentions",
        ):
            if np.shape(getattr(self, name)) != shape:
                msg = (
                    f"SourceRanking: '{name}' must have shape {shape} (sites, sources)."
                )
                raise ValueError(msg)
        if np.shape(self.participants) != (len(self.sites),):
            msg = "SourceRanking: 'participants' must hold one count per site."
            raise ValueError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the median rank of each source per site, with its range.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the bars.
        :return: The axes. Requires matplotlib (``pip install phonometry[plot]``).
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_source_ranking

        return plot_source_ranking(
            self, ax=ax, language=check_language(language), **kwargs
        )


def method_b_source_ranking(
    rankings: Sequence[Sequence[str]],
    *,
    sites: ArrayLike | Sequence[object] | None = None,
) -> SourceRanking:
    """Median and range of the rank of each recognised sound source per site
    (ISO/TS 12913-3 B.2, ISO/TS 12913-2 C.3.2.4 and Figure C.8).

    :param rankings: For each participant, the sources they listed, the most
        noticeable first, at most eight and none twice. The names are
        compared as given, so a study should code them to one vocabulary
        first (for instance the taxonomy of ISO/TS 12913-2 Figure C.1).
    :param sites: The site of each participant; ``None`` puts every
        participant at one site named ``"all"``.
    :return: A :class:`SourceRanking`.
    :raises ValueError: for a list longer than eight, a source listed twice by
        one participant, an empty source name, no participants, or sites
        that do not match the participants.
    """
    if isinstance(rankings, str) or not isinstance(rankings, Sequence):
        msg = "'rankings' must be a sequence of lists of source names, one list per participant."
        raise ValueError(msg)
    lists: list[tuple[str, ...]] = []
    for k, listed in enumerate(rankings):
        if isinstance(listed, str) or not isinstance(listed, Sequence):
            msg = f"'rankings[{k}]' must be a list of source names, the most noticeable first."
            raise ValueError(msg)
        names = tuple(str(name).strip() for name in listed)
        if len(names) > METHOD_B_MAXIMUM_SOURCES:
            msg = (
                f"'rankings[{k}]' lists {len(names)} sources; ISO/TS 12913-2 C.3.2.4 "
                f"limits the list to {METHOD_B_MAXIMUM_SOURCES}."
            )
            raise ValueError(msg)
        if any(not name for name in names) or len(set(names)) != len(names):
            msg = f"'rankings[{k}]' must name each source once, with a non-empty name."
            raise ValueError(msg)
        lists.append(names)
    if not lists:
        msg = "'rankings' must hold at least one participant."
        raise ValueError(msg)
    labels, groups = _site_groups(sites, len(lists))
    sources = sorted({name for names in lists for name in names})
    column = {name: j for j, name in enumerate(sources)}
    ranks = np.full((len(lists), len(sources)), np.nan)
    for row, names in enumerate(lists):
        for position, name in enumerate(names, start=1):
            ranks[row, column[name]] = float(position)
    overall_median = [float(np.nanmedian(ranks[:, j])) for j in range(len(sources))]
    overall_mentions = np.sum(~np.isnan(ranks), axis=0)
    order = sorted(
        range(len(sources)),
        key=lambda j: (overall_median[j], -overall_mentions[j], sources[j]),
    )
    ranks = ranks[:, order]
    medians = _nan_statistic(ranks, groups, "median")
    minima = _nan_statistic(ranks, groups, "min")
    maxima = _nan_statistic(ranks, groups, "max")
    return SourceRanking(
        sources=tuple(sources[j] for j in order),
        sites=labels,
        median_ranks=read_only(medians),
        lowest_ranks=read_only(minima),
        highest_ranks=read_only(maxima),
        rank_ranges=read_only(maxima - minima),
        mentions=read_only(_answer_counts(ranks, groups)),
        participants=read_only(
            np.asarray([rows.size for rows in groups], dtype=np.int64)
        ),
    )


# ---------------------------------------------------------------------------
# ISO/TS 12913-2 Annex A: the minimum reporting requirements
# ---------------------------------------------------------------------------

#: The kinds of acoustic environment ISO/TS 12913-2 A.3 a) distinguishes.
_ENVIRONMENT_TYPES = ("real", "recorded", "virtual")

#: The results A.3 f) requires, by the symbols it prints.
_REQUIRED_RESULTS = ("LAeq,T", "LCeq,T", "LAF5,T", "LAF95,T", "N5", "N95", "Nrmc")


def _require_text(owner: str, item: str, value: object) -> None:
    """A required Annex A item must be stated, not left empty."""
    if not isinstance(value, str) or not value.strip():
        msg = f"{owner}: ISO/TS 12913-2 {item} must be reported; got {value!r}."
        raise ValueError(msg)


def _optional_text(owner: str, item: str, value: object) -> None:
    """An item Annex A requires only in some studies is ``None`` or stated."""
    if value is not None:
        _require_text(owner, item, value)


@dataclass(frozen=True)
class SoundscapeParticipants:
    """The participants of a soundscape study (ISO/TS 12913-2 A.2 a) to e)).

    Every field is required: "the participants shall be identified and the
    following information recorded". Each is free text, because the annex
    prescribes what is stated and not how.

    :ivar selection: A.2 a), how the participants were selected.
    :ivar residents_or_visitors: A.2 b), whether they were residents at or
        visitors to the study site.
    :ivar lay_or_expert: A.2 c), whether they were lay people or experts in a
        field relevant to the study.
    :ivar age_and_gender_distribution: A.2 d).
    :ivar other_relevant_information: A.2 e), for example hearing ability;
        state "none" if there is nothing to add.
    """

    selection: str
    residents_or_visitors: str
    lay_or_expert: str
    age_and_gender_distribution: str
    other_relevant_information: str

    def __post_init__(self) -> None:
        """Refuse an item left empty, naming its clause.

        :raises ValueError: for an empty or non-text item.
        """
        owner = type(self).__name__
        _require_text(owner, "A.2 a)", self.selection)
        _require_text(owner, "A.2 b)", self.residents_or_visitors)
        _require_text(owner, "A.2 c)", self.lay_or_expert)
        _require_text(owner, "A.2 d)", self.age_and_gender_distribution)
        _require_text(owner, "A.2 e)", self.other_relevant_information)


@dataclass(frozen=True)
class SoundscapeAcousticEnvironment:
    """The studied acoustic environment (ISO/TS 12913-2 A.3 a) to h)).

    :ivar environment_type: A.3 a), ``"real"``, ``"recorded"`` or
        ``"virtual"``.
    :ivar sound_sources: A.3 b), the sound sources and the composition of the
        acoustic environment, including the total sound, the background and
        the foreground sounds.
    :ivar weather_and_wind: A.3 c).
    :ivar time_of_year_and_day: A.3 d).
    :ivar measurement_points: A.3 e), the measurement points, including the
        height and orientation of the binaural measurement system, and what
        acoustic measurements were taken.
    :ivar measurement_results: A.3 f), the results of the measurements, keyed
        by the symbols A.3 f) prints: ``"LAeq,T"``, ``"LCeq,T"``,
        ``"LAF5,T"``, ``"LAF95,T"`` (dB), ``"N5"``, ``"N95"`` and ``"Nrmc"``
        (sone), all seven required, others allowed.
        :meth:`BinauralIndicators.reporting_results
        <phonometry.environment.assessment.soundscape_binaural.BinauralIndicators.reporting_results>`
        builds it from a binaural analysis.
    :ivar site_description: A.3 g), required for a field study or a study
        based on audio recordings (``"real"`` or ``"recorded"``): the study
        site, including its type.
    :ivar recording_and_reproduction: A.3 h), required for a recorded or
        virtual environment: how it was recorded or created and how it was
        reproduced.
    """

    environment_type: str
    sound_sources: str
    weather_and_wind: str
    time_of_year_and_day: str
    measurement_points: str
    measurement_results: Mapping[str, float]
    site_description: str | None = None
    recording_and_reproduction: str | None = None

    def __post_init__(self) -> None:
        """Refuse an item left empty and a missing result, naming the clause.

        The results are frozen into a read-only mapping of floats.

        :raises ValueError: for an unknown environment type, an empty item, a
            required conditional item left out, or a missing or non-finite
            result.
        """
        owner = type(self).__name__
        require_choice(self.environment_type, "environment_type", _ENVIRONMENT_TYPES)
        _require_text(owner, "A.3 b)", self.sound_sources)
        _require_text(owner, "A.3 c)", self.weather_and_wind)
        _require_text(owner, "A.3 d)", self.time_of_year_and_day)
        _require_text(owner, "A.3 e)", self.measurement_points)
        if not isinstance(self.measurement_results, Mapping):
            msg = f"{owner}: ISO/TS 12913-2 A.3 f) must be a mapping from symbol to value."
            raise ValueError(msg)
        missing = [
            key for key in _REQUIRED_RESULTS if key not in self.measurement_results
        ]
        if missing:
            msg = f"{owner}: ISO/TS 12913-2 A.3 f) must report {missing}."
            raise ValueError(msg)
        results: dict[str, float] = {}
        for key, value in self.measurement_results.items():
            try:
                number = float(value)
            except (TypeError, ValueError):
                number = math.nan
            if not math.isfinite(number):
                msg = f"{owner}: ISO/TS 12913-2 A.3 f) result {key!r} must be finite."
                raise ValueError(msg)
            results[str(key)] = number
        object.__setattr__(self, "measurement_results", MappingProxyType(results))
        if self.environment_type in ("real", "recorded"):
            _require_text(owner, "A.3 g)", self.site_description)
        else:
            _optional_text(owner, "A.3 g)", self.site_description)
        if self.environment_type in ("recorded", "virtual"):
            _require_text(owner, "A.3 h)", self.recording_and_reproduction)
        else:
            _optional_text(owner, "A.3 h)", self.recording_and_reproduction)


@dataclass(frozen=True)
class SoundscapeDataCollection:
    """How the perception data were collected (ISO/TS 12913-2 A.4 a) to e)).

    :ivar methods: A.4 a), the methods used.
    :ivar questions: A.4 b), the questions asked, how they were formulated
        and how the responses were documented.
    :ivar language: A.4 d), the language of the study, with examples of the
        questions in the original language and in translation.
    :ivar instrument_copy: Where the copy of the data collection instrument
        (the questionnaire or the scales) that A.4 requires the report to
        include is found.
    :ivar rating_scale_construction: A.4 c), for a study based on rating
        scales: how the questions, the response alternatives and the response
        format were constructed and formulated; ``None`` for a study without.
    :ivar behaviour_observation: A.4 e), for observations of behaviour: how
        they were conducted and documented; ``None`` for a study without.
    """

    methods: str
    questions: str
    language: str
    instrument_copy: str
    rating_scale_construction: str | None = None
    behaviour_observation: str | None = None

    def __post_init__(self) -> None:
        """Refuse an item left empty, naming its clause.

        :raises ValueError: for an empty or non-text item.
        """
        owner = type(self).__name__
        _require_text(owner, "A.4 a)", self.methods)
        _require_text(owner, "A.4 b)", self.questions)
        _require_text(owner, "A.4 d)", self.language)
        _require_text(owner, "A.4 (copy of the instrument)", self.instrument_copy)
        _optional_text(owner, "A.4 c)", self.rating_scale_construction)
        _optional_text(owner, "A.4 e)", self.behaviour_observation)


@dataclass(frozen=True)
class SoundscapeReport:
    """The minimum reporting requirements of a soundscape study
    (ISO/TS 12913-2 Annex A, normative, and clause 6).

    A.1 lists three things a report shall comprise, and each is one record:
    the selection and classification of the participants (A.2), the
    characterization of the studied acoustic environment (A.3), and the data
    collection on how people perceived it (A.4). Each record refuses to be
    built with a required item missing, so a :class:`SoundscapeReport` that
    exists meets the minimum of Annex A as far as a record can tell; whether
    what is written is true and sufficient stays with the author.

    :ivar participants: A.1 a), A.2.
    :ivar acoustic_environment: A.1 b), A.3.
    :ivar data_collection: A.1 c), A.4.
    """

    participants: SoundscapeParticipants
    acoustic_environment: SoundscapeAcousticEnvironment
    data_collection: SoundscapeDataCollection

    def __post_init__(self) -> None:
        """Refuse a part of the report that is not the record for it.

        :raises ValueError: if a field holds anything but its record type.
        """
        for name, kind in (
            ("participants", SoundscapeParticipants),
            ("acoustic_environment", SoundscapeAcousticEnvironment),
            ("data_collection", SoundscapeDataCollection),
        ):
            if not isinstance(getattr(self, name), kind):
                msg = f"SoundscapeReport: '{name}' must be a {kind.__name__}."
                raise ValueError(msg)
