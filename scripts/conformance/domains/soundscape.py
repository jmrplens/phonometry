#  Copyright (c) 2026. Jose Manuel Requena Plens
"""How people hear a place: the soundscape analysis of ISO/TS 12913-3:2019.

ISO/TS 12913-3:2019 prints no worked example: no questionnaire answered, no
coordinate computed, no correlation reported. Every row below is therefore a
closed form or an independent implementation, and each says which. The printed
numbers it does have are checked where they are: the scale values of Table A.1,
the range of the coordinates, 9,66, and the rows of Table D.1.

The edition implemented is the first, of 2019. ISO/TS 12913-3:2025 revises
Annex A and was not available for this implementation, so these rows say
nothing about it.

Oracle: ISO/TS 12913-3:2019(E), Table A.1 on printed folio 4 (PDF page 10),
Formulas (A.1) and (A.2) and the range on folio 5 (PDF page 11), Figure A.1
and Formulas (A.3) and (A.4) on folio 6 (PDF page 12), Table B.1 on folio 8
(PDF page 14), Formulas (B.1) and (B.2) on folio 9 (PDF page 15), Table D.1 on
folio 13 (PDF page 19).
"""

from __future__ import annotations

import math

import numpy as np
import reference_data as ref
from scipy import stats

from phonometry import environment, psychoacoustics, signals

from ..registry import Outcome, count, numeric, register

_SOUNDSCAPE = "Soundscape analysis (ISO/TS 12913-3)"

_ATTRIBUTES = environment.PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES


def _answers(**scores: float) -> dict[str, list[float]]:
    """One respondent, every attribute at 3 unless named."""
    return {name: [float(scores.get(name, 3.0))] for name in _ATTRIBUTES}


def _isd_answers() -> np.ndarray:
    """The 93 answers of the ISD subset, NaN for a blank (CC BY 4.0)."""
    return np.array(
        [
            [np.nan if v is None else v for v in row]
            for row in ref.ISD_REGENTS_PARK_JAPAN_ANSWERS
        ],
        dtype=float,
    )


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 A.2, Table A.1",
    "Scale value of each of the five boxes of the four parts of Method A",
)
def _chk_table_a1() -> Outcome:
    """Box positions 1 to 5, left to right, through method_a_scale_values.

    Parts 1 and 4 run 1 to 5 from the left-hand box, parts 2 and 3 run 5 to 1:
    20 cells against the table as printed.
    """
    matching = 0
    for part, printed in ref.ISO12913_3_TABLE_A1_SCALE_VALUES.items():
        values = environment.method_a_scale_values([1, 2, 3, 4, 5], part=part)
        matching += int(np.count_nonzero(np.asarray(values) == np.asarray(printed)))
    return count(matching, 20, subject="scale values of Table A.1")


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 Formulas (A.1) and (A.2)",
    "Every attribute at one score puts the respondent at the origin",
)
def _chk_origin() -> Outcome:
    """For each score 1 to 5, the largest |P| and |E| of the eight at that score.

    Every term of both formulas is a difference of two attributes, so equal
    answers cancel to zero whatever the score.
    """
    largest = 0.0
    for score in (1.0, 2.0, 3.0, 4.0, 5.0):
        result = environment.pleasantness_eventfulness(
            {name: [score] for name in _ATTRIBUTES}
        )
        largest = max(
            largest,
            abs(float(result.pleasantness[0])),
            abs(float(result.eventfulness[0])),
        )
    return numeric(
        0.0, largest, 1e-12, places=12, computed_label=f"max |P|, |E| = {largest:.1e}"
    )


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 A.3",
    "Range of the coordinates, 4 + sqrt(32), printed as 9,66",
)
def _chk_range() -> Outcome:
    """Pleasant, calm and vibrant at 5 and their opposites at 1.

    The main axis contributes 4 and each diagonal 4 cos 45 degrees, so P is
    4 + 8 cos 45 degrees = 4 + sqrt(32); the page prints it to two decimals.
    """
    most = _answers(pleasant=5, calm=5, vibrant=5, annoying=1, chaotic=1, monotonous=1)
    value = float(environment.pleasantness_eventfulness(most).pleasantness[0])
    return numeric(ref.ISO12913_3_COORDINATE_RANGE_PRINTED, value, 0.005, places=4)


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 A.3",
    "The four extremes of P and E divided by 4 + sqrt(32) are plus and minus 1",
)
def _chk_normalised_extremes() -> Outcome:
    """Most and least pleasant, most and least eventful, normalised."""
    cases = (
        (
            "P",
            1.0,
            _answers(
                pleasant=5, calm=5, vibrant=5, annoying=1, chaotic=1, monotonous=1
            ),
        ),
        (
            "P",
            -1.0,
            _answers(
                pleasant=1, calm=1, vibrant=1, annoying=5, chaotic=5, monotonous=5
            ),
        ),
        (
            "E",
            1.0,
            _answers(
                eventful=5, chaotic=5, vibrant=5, uneventful=1, calm=1, monotonous=1
            ),
        ),
        (
            "E",
            -1.0,
            _answers(
                eventful=1, chaotic=1, vibrant=1, uneventful=5, calm=5, monotonous=5
            ),
        ),
    )
    matching = 0
    for axis, expected, answers in cases:
        result = environment.pleasantness_eventfulness(answers)
        value = (
            result.normalized_pleasantness[0]
            if axis == "P"
            else result.normalized_eventfulness[0]
        )
        matching += int(abs(float(value) - expected) <= 1e-12)
    return count(matching, 4, subject="normalised extremes at plus or minus 1")


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 Figure A.1, Formulas (A.1) and (A.2)",
    "Each attribute raised alone moves the point along its own arrow of the figure",
)
def _chk_axes_of_figure_a1() -> Outcome:
    """Pleasant at 0 degrees, vibrant 45, eventful 90 ... calm 315, as drawn.

    One attribute at 5, the rest at 3: the displacement is 2 along the
    attribute's arrow, on the main axes and the rotated ones alike.
    """
    angles = {
        "pleasant": 0.0,
        "vibrant": 45.0,
        "eventful": 90.0,
        "chaotic": 135.0,
        "annoying": 180.0,
        "monotonous": 225.0,
        "uneventful": 270.0,
        "calm": 315.0,
    }
    matching = 0
    for name, angle in angles.items():
        result = environment.pleasantness_eventfulness(_answers(**{name: 5}))
        p, e = float(result.pleasantness[0]), float(result.eventfulness[0])
        on_axis = abs((math.degrees(math.atan2(e, p)) % 360.0) - angle) <= 1e-9
        matching += int(on_axis and abs(math.hypot(p, e) - 2.0) <= 1e-12)
    return count(matching, 8, subject="attribute axes of Figure A.1")


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 Formula (A.3)",
    "Spearman's coefficient without ties is Pearson's coefficient of the ranks",
)
def _chk_spearman_untied() -> Outcome:
    """Twelve untied pairs; the ranks correlated by numpy, independently."""
    x = np.array([3.1, 1.2, 5.6, 4.4, 2.0, 7.3, 6.5, 9.9, 8.1, 0.4, 11.0, 10.2])
    y = np.array([2.2, 1.0, 4.9, 6.1, 3.3, 5.5, 8.8, 7.7, 9.1, 0.9, 12.4, 10.0])
    result = environment.spearman_rank_correlation(x, y)
    expected = float(np.corrcoef(stats.rankdata(x), stats.rankdata(y))[0, 1])
    return numeric(expected, result.coefficient, 1e-12, places=10)


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 Formula (A.4) against scipy.stats.spearmanr",
    "Spearman's coefficient with ties, on 93 real ordinal answers",
)
def _chk_spearman_tied() -> Outcome:
    """Pleasant against annoying at one site of the ISD subset: heavy ties.

    Formula (A.4) with its tie sums T and U against scipy's Pearson of the
    average ranks, which is how scipy handles ties and shares no code with it.
    """
    answers = _isd_answers()
    rows = ~np.isnan(answers[:, 0]) & ~np.isnan(answers[:, 5])
    x, y = answers[rows, 0], answers[rows, 5]
    result = environment.spearman_rank_correlation(x, y)
    return numeric(
        float(stats.spearmanr(x, y).statistic), result.coefficient, 1e-12, places=10
    )


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 A.4 against scipy.stats.spearmanr",
    "Probability value of Spearman's coefficient, Student t with n - 2 degrees of freedom",
)
def _chk_spearman_p_value() -> Outcome:
    """The same 93 answers, two-sided."""
    answers = _isd_answers()
    rows = ~np.isnan(answers[:, 0]) & ~np.isnan(answers[:, 5])
    x, y = answers[rows, 0], answers[rows, 5]
    result = environment.spearman_rank_correlation(x, y)
    return numeric(
        float(stats.spearmanr(x, y).pvalue), result.p_value, 1e-9, rel=True, places=8
    )


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 Formulas (B.1) and (B.2) against scipy.stats.pearsonr",
    "Pearson's coefficient with the covariance over n",
)
def _chk_pearson() -> Outcome:
    """Site pleasantness against site LAeq of the 26 ISD locations."""
    medians = np.array([row[3] for row in ref.ISD_LOCATION_MEDIANS], dtype=float)
    laeq = np.array([row[4] for row in ref.ISD_LOCATION_MEDIANS])
    pleasantness = environment.pleasantness_eventfulness(
        medians
    ).respondent_pleasantness
    result = environment.pearson_correlation(pleasantness, laeq)
    return numeric(
        float(stats.pearsonr(pleasantness, laeq).statistic),
        result.coefficient,
        1e-12,
        places=10,
    )


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 B.2 against scipy.stats.t.interval",
    "Upper end of the 95 % confidence interval of a Method B mean",
)
def _chk_method_b_interval() -> Outcome:
    """Six ratings to one decimal; Student t with n - 1 degrees of freedom."""
    ratings = np.array([2.1, 3.4, 2.9, 3.8, 2.5, 3.0])
    summary = environment.method_b_summary(ratings)
    _, upper = stats.t.interval(
        0.95, ratings.size - 1, loc=ratings.mean(), scale=stats.sem(ratings)
    )
    return numeric(
        float(upper), float(summary.confidence_upper[0, 0]), 1e-12, places=10
    )


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 Table D.1",
    "Metrics of each parameter and the representative-value rule, as printed",
)
def _chk_table_d1() -> Outcome:
    """Six rows: parameter, metrics, whether the average is allowed, reference."""
    matching = 0
    for row, printed in zip(
        environment.BINAURAL_PARAMETERS.values(), ref.ISO12913_3_TABLE_D1, strict=True
    ):
        parameter, metrics, average, reference = printed
        matching += int(row.parameter == parameter)
        matching += int(row.metrics == metrics)
        matching += int(row.average_allowed is average)
        matching += int(row.reference == reference)
    return count(matching, 24, subject="cells of Table D.1")


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-3:2019 D.2",
    "Representative LAeq,T of two ears 6 dB apart is the louder ear's",
)
def _chk_representative_ear() -> Outcome:
    """The higher of the two channels; the louder one computed alone as oracle."""
    import warnings

    rng = np.random.default_rng(12913)
    left = 0.2 * rng.standard_normal(48_000)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", environment.SoundscapeWarning)
        result = environment.binaural_indicators(
            np.vstack([0.5 * left, left]), 48_000, parameters="sound_pressure_level"
        )
    expected = float(signals.laeq(left, 48_000))
    return numeric(expected, result.representative("LAeq,T"), 1e-9, unit="dB", places=4)


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-2:2018 Figures C.2 to C.6",
    "Response categories of the four parts of Method A, and the eight attributes",
)
def _chk_questionnaire_vocabulary() -> Outcome:
    """The published questionnaire against a second transcription of the page.

    Five categories for each of Figures C.2, C.3, C.4, C.5 and C.6, and the
    eight scales of Figure C.4 in their printed order: 33 strings.
    """
    tables = {
        "C.2": environment.METHOD_A_SCALES[1],
        "C.3": environment.METHOD_A_ALTERNATIVE_PART_1,
        "C.4": environment.METHOD_A_SCALES[2],
        "C.5": environment.METHOD_A_SCALES[3],
        "C.6": environment.METHOD_A_SCALES[4],
    }
    matching = 0
    for figure, printed in ref.ISO12913_2_METHOD_A_CATEGORIES.items():
        scale = tables[figure]
        matching += sum(
            int(a == b) for a, b in zip(scale.categories, printed, strict=True)
        )
    matching += sum(
        int(a == b)
        for a, b in zip(
            environment.PERCEIVED_AFFECTIVE_QUALITY_ATTRIBUTES,
            ref.ISO12913_2_FIGURE_C4_ATTRIBUTES,
            strict=True,
        )
    )
    return count(matching, 33, subject="printed strings of Annex C")


@register(
    _SOUNDSCAPE,
    "ISO/TS 12913-2:2018 A.3 f) with ISO 532-1:2017",
    "Root mean cubed loudness Nrmc of an ear, by the formula of the NOTE",
)
def _chk_root_mean_cubed_loudness() -> Outcome:
    """The cube root of the mean of the cubes of the ISO 532-1 loudness trace.

    The trace is the library's time-varying loudness of the ear; the row holds
    the binaural analysis to the formula A.3 f) prints for it.
    """
    import warnings

    rng = np.random.default_rng(12913)
    t = np.arange(96_000) / 48_000
    ear = (
        0.05 * rng.standard_normal(t.size) * (1.0 + 0.6 * np.sin(2.0 * np.pi * 0.7 * t))
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", environment.SoundscapeWarning)
        result = environment.binaural_indicators(
            np.vstack([ear, ear]), 48_000, parameters="loudness"
        )
    trace = np.asarray(psychoacoustics.loudness_zwicker(ear, 48_000).loudness_vs_time)
    expected = float(np.mean(trace**3)) ** (1.0 / 3.0)
    return numeric(expected, result.metrics["Nrmc"].left, 1e-12, rel=True, places=6)
