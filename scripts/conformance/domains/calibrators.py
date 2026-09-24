#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound calibrators (IEC 60942:2017) and the conformance rule of IEC TC 29.

Two things are pinned here. The first is the rule itself, which IEC 60942
prints in 5.1.15 and IEC 61672-1:2013 in 5.1.21 in the same sentence: a
requirement is met when the measured deviation is within the acceptance
limits AND the actual expanded uncertainty is within the maximum permitted,
both limits inclusive. Each standard prints worked examples with the verdict
and the reason, eight in IEC 60942 Table E.1 and ten in IEC 61672-1 Table C.1,
and each is a row: the verdict, the outcome number and the printed reason
have to come back, the boundary cases included (a deviation equal to its
limit, an uncertainty equal to its maximum, and the deviation of -1,2 dB on
the lower limit of C.1).

The second is IEC 60942 itself: Tables 2 to 7 and A.1 to A.5 and the limits
four clauses print in their text (5.9.4.2, A.5.5.7, A.6.4.7 and A.7.4.8), each
cell against an independent transcription of the rasterised page, dashes and
range ends included, the two frequencies of every range as well as which of
them it includes, and the verdict of
:func:`phonometry.metrology.verify_sound_calibrator` where the tables meet the
rule, at 1 kHz and at 2 kHz, where Table 2 and Table 5 differ.

Oracle: IEC 60942:2017 read in UNE-EN IEC 60942:2018 (PDF page = folio + 8):
Tables 2 and 3 (folio 16), 4 (17), 5 and 6 (18), 7 (19), A.1 (28), A.2 (29),
A.3 (30), A.4 (32), A.5 (35), the text of 5.9.4.2 (21), A.5.5.7 (27), A.6.4.7
(34) and A.7.4.8 (40), and Table E.1 (52). IEC 61672-1:2013 read in BS EN
61672-1:2013 (PDF page = folio + 2): 5.1.21 (folio 16) and Table C.1 (45).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import reference_data as ref

import phonometry as ph

from ..registry import Outcome, count, record, register

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from phonometry.metrology import CalibratorTableRow

_CALIBRATORS = "Sound calibrators and the conformance rule (IEC 60942, IEC 61672-1)"

_CLASSES = ("LS", "1", "2")

_VERDICT = {True: "Yes", False: "No"}


def _verdict_record(
    result: ph.metrology.ConformanceVerification, *, conforms: bool, outcome: int
) -> Outcome:
    """The printed verdict and reason against the ones the rule gives."""
    expected = {"conforms": float(conforms), "outcome": float(outcome), "reason": 1.0}
    computed = {
        "conforms": float(result.passes),
        "outcome": float(result.outcome),
        "reason": float(result.reason == ref.TC29_REASONS[outcome]),
    }
    return record(
        expected,
        computed,
        label=f"{_VERDICT[conforms]}: {ref.TC29_REASONS[outcome]}",
        computed_label=f"{_VERDICT[result.passes]}: {result.reason}",
    )


def _register_table_e1() -> None:
    """One row per example of IEC 60942:2017 Table E.1."""
    for (
        example,
        deviation,
        limit,
        uncertainty,
        maximum,
        conforms,
        outcome,
    ) in ref.IEC60942_TABLE_E1:

        def check(
            deviation: float = deviation,
            limit: float = limit,
            uncertainty: float = uncertainty,
            maximum: float = maximum,
            conforms: bool = conforms,  # noqa: FBT001
            outcome: int = outcome,
        ) -> Outcome:
            result = ph.metrology.verify_conformance(
                deviation,
                uncertainty=uncertainty,
                acceptance_limits=limit,
                max_uncertainty=maximum,
            )
            return _verdict_record(result, conforms=conforms, outcome=outcome)

        register(
            _CALIBRATORS,
            "IEC 60942:2017 Table E.1",
            f"Example {example}: |deviation| {deviation:.2f} dB, U {uncertainty:.2f} dB "
            f"against {limit:.2f} dB and {maximum:.2f} dB",
        )(check)


def _register_table_c1() -> None:
    """One row per example of IEC 61672-1:2013 Table C.1."""
    for example, deviation, (
        upper,
        lower,
    ), uncertainty, maximum, conforms, outcome in ref.IEC61672_1_TABLE_C1:

        def check(
            deviation: float = deviation,
            lower: float = lower,
            upper: float = upper,
            uncertainty: float = uncertainty,
            maximum: float = maximum,
            conforms: bool = conforms,  # noqa: FBT001
            outcome: int = outcome,
        ) -> Outcome:
            result = ph.metrology.verify_conformance(
                deviation,
                uncertainty=uncertainty,
                acceptance_limits=(lower, upper),
                max_uncertainty=maximum,
            )
            return _verdict_record(result, conforms=conforms, outcome=outcome)

        register(
            _CALIBRATORS,
            "IEC 61672-1:2013 Table C.1",
            f"Example {example}: deviation {deviation:+.1f} dB, U {uncertainty:.1f} dB "
            f"against +{upper:.1f}; {lower:.1f} dB and {maximum:.1f} dB",
        )(check)


_register_table_e1()
_register_table_c1()


#: A printed range of nominal frequencies, ``"31,5 to 63"`` or ``"> 63 to < 160"``:
#: an optional sign, a number with a decimal comma and a space between the
#: thousands, ``to``, and the same again. The last row of Table A.1 prints no
#: space after its sign, which the pattern allows.
_RANGE = re.compile(r"(>?)\s*([\d ,]+?)\s+to\s+(<?)\s*([\d ,]+)")


def _bounds(printed: str) -> tuple[float, float, bool, bool]:
    """The two frequencies of a printed range and whether each is included.

    ``"> 63 to < 160"`` is ``(63.0, 160.0, False, False)``.
    """
    match = _RANGE.fullmatch(printed)
    if match is None:
        msg = f"not a printed range of nominal frequencies: {printed!r}"
        raise ValueError(msg)
    low_sign, low, high_sign, high = match.groups()

    def number(text: str) -> float:
        return float(text.replace(" ", "").replace(",", "."))

    return number(low), number(high), low_sign != ">", high_sign != "<"


def _banded_matches(
    table: Sequence[CalibratorTableRow],
    printed: Sequence[tuple[str, tuple[float | None, float | None, float | None]]],
) -> tuple[int, int]:
    """Agreeing cells, range frequencies and range ends against the page.

    Seven per row: the three class cells, the two frequencies of the range and
    whether each of them belongs to it.
    """
    matching = total = 0
    for row, (label, cells) in zip(table, printed, strict=True):
        published = (
            row.class_ls,
            row.class_1,
            row.class_2,
            row.lower_hz,
            row.upper_hz,
            row.includes_lower,
            row.includes_upper,
        )
        lower, upper, with_lower, with_upper = _bounds(label)
        page = (*cells, lower, upper, with_lower, with_upper)
        matching += sum(a == b for a, b in zip(published, page, strict=True))
        total += len(page)
    return matching, total


def _per_class_matches(
    table: Mapping[str, float], printed: Sequence[float]
) -> tuple[int, int]:
    """Agreeing cells between a per-class table and the page."""
    published = tuple(table[c] for c in _CLASSES)
    return sum(a == b for a, b in zip(published, printed, strict=True)), 3


@register(
    _CALIBRATORS,
    "IEC 60942:2017 Table 2",
    "Level and short-term fluctuation limits, dashes and ranges, by class",
)
def _chk_table_2() -> Outcome:
    level = _banded_matches(
        ph.metrology.LEVEL_ACCEPTANCE_LIMITS_DB,
        [(label, cells) for label, cells, _ in ref.IEC60942_TABLE2],
    )
    fluctuation = _banded_matches(
        ph.metrology.FLUCTUATION_ACCEPTANCE_LIMITS_DB,
        [(label, cells) for label, _, cells in ref.IEC60942_TABLE2],
    )
    return count(
        level[0] + fluctuation[0], level[1] + fluctuation[1], subject="printed cells"
    )


@register(
    _CALIBRATORS,
    "IEC 60942:2017 Tables 3, 4 and 6",
    "Supply-voltage, frequency and environmental-frequency limits, by class",
)
def _chk_tables_3_4_6() -> Outcome:
    pairs = (
        (ph.metrology.SUPPLY_VOLTAGE_ACCEPTANCE_LIMITS_DB, ref.IEC60942_TABLE3),
        (ph.metrology.FREQUENCY_ACCEPTANCE_LIMITS_PERCENT, ref.IEC60942_TABLE4),
        (
            ph.metrology.ENVIRONMENTAL_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT,
            ref.IEC60942_TABLE6,
        ),
    )
    tallies = [_per_class_matches(table, printed) for table, printed in pairs]
    return count(
        sum(t[0] for t in tallies), sum(t[1] for t in tallies), subject="printed cells"
    )


@register(
    _CALIBRATORS,
    "IEC 60942:2017 Tables 5 and 7",
    "Environmental level and total distortion + noise limits, by class",
)
def _chk_tables_5_7() -> Outcome:
    level = _banded_matches(
        ph.metrology.ENVIRONMENTAL_LEVEL_ACCEPTANCE_LIMITS_DB, ref.IEC60942_TABLE5
    )
    distortion = _banded_matches(
        ph.metrology.DISTORTION_ACCEPTANCE_LIMITS_PERCENT, ref.IEC60942_TABLE7
    )
    return count(
        level[0] + distortion[0], level[1] + distortion[1], subject="printed cells"
    )


@register(
    _CALIBRATORS,
    "IEC 60942:2017 Tables A.1, A.3 and A.4",
    "Maximum-permitted uncertainties keyed by frequency, by class",
)
def _chk_tables_a1_a3_a4() -> Outcome:
    tallies = [
        _banded_matches(
            ph.metrology.LEVEL_MAX_UNCERTAINTY_DB,
            [(label, cells) for label, cells, _ in ref.IEC60942_TABLE_A1],
        ),
        _banded_matches(
            ph.metrology.FLUCTUATION_MAX_UNCERTAINTY_DB,
            [(label, cells) for label, _, cells in ref.IEC60942_TABLE_A1],
        ),
        _banded_matches(
            ph.metrology.DISTORTION_MAX_UNCERTAINTY_PERCENT, ref.IEC60942_TABLE_A3
        ),
        _banded_matches(
            ph.metrology.ENVIRONMENTAL_LEVEL_MAX_UNCERTAINTY_DB, ref.IEC60942_TABLE_A4
        ),
    ]
    return count(
        sum(t[0] for t in tallies), sum(t[1] for t in tallies), subject="printed cells"
    )


@register(
    _CALIBRATORS,
    "IEC 60942:2017 Tables A.2 and A.5, A.5.5.7",
    "Maximum-permitted uncertainties of the frequency and the supply-voltage effect",
)
def _chk_tables_a2_a5() -> Outcome:
    pairs = (
        (ph.metrology.FREQUENCY_MAX_UNCERTAINTY_PERCENT, ref.IEC60942_TABLE_A2),
        (
            ph.metrology.ENVIRONMENTAL_FREQUENCY_MAX_UNCERTAINTY_PERCENT,
            ref.IEC60942_TABLE_A5,
        ),
        (
            ph.metrology.SUPPLY_VOLTAGE_MAX_UNCERTAINTY_DB,
            ref.IEC60942_SUPPLY_VOLTAGE_MAX_U,
        ),
    )
    tallies = [_per_class_matches(table, printed) for table, printed in pairs]
    return count(
        sum(t[0] for t in tallies), sum(t[1] for t in tallies), subject="printed cells"
    )


@register(
    _CALIBRATORS,
    "IEC 60942:2017 5.9.4.2 and A.7.4.8",
    "Level change in a power- or radio-frequency field and its maximum uncertainty",
)
def _chk_field_immunity() -> Outcome:
    limits = _per_class_matches(
        ph.metrology.FIELD_IMMUNITY_ACCEPTANCE_LIMITS_DB, ref.IEC60942_FIELD_IMMUNITY
    )
    maxima = _per_class_matches(
        ph.metrology.FIELD_IMMUNITY_MAX_UNCERTAINTY_DB,
        (ref.IEC60942_FIELD_IMMUNITY_MAX_U,) * 3,
    )
    return count(limits[0] + maxima[0], limits[1] + maxima[1], subject="printed cells")


@register(
    _CALIBRATORS,
    "IEC 60942:2017 A.6.4.7",
    "Reduced limits of the abbreviated environmental test",
)
def _chk_abbreviated_limits() -> Outcome:
    reductions = _per_class_matches(
        ph.metrology.ABBREVIATED_LEVEL_REDUCTIONS_DB,
        ref.IEC60942_ABBREVIATED_REDUCTIONS,
    )
    frequency = _per_class_matches(
        ph.metrology.ABBREVIATED_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT,
        ref.IEC60942_ABBREVIATED_FREQUENCY,
    )
    return count(
        reductions[0] + frequency[0],
        reductions[1] + frequency[1],
        subject="printed cells",
    )


@register(
    _CALIBRATORS,
    "IEC 60942:2017 5.1.15 with Tables 2 and A.1",
    "Table E.1 examples 1 to 7 as a class 1 level at 1 kHz, 7 verdicts",
)
def _chk_e1_through_the_calibrator() -> Outcome:
    """Examples 1 to 7 use 0,25 dB and 0,15 dB, the class 1 figures at 1 kHz.

    So the same seven verdicts have to come back from the calibrator verdict,
    which reads its limits from Tables 2 and A.1 rather than being handed them.
    """
    agree = 0
    examples = [row for row in ref.IEC60942_TABLE_E1 if row[0] <= 7]
    for _example, deviation, _limit, uncertainty, _maximum, conforms, _o in examples:
        measured = ph.metrology.SoundCalibratorMeasurements(
            level_deviation_db=deviation, level_uncertainty_db=uncertainty
        )
        verdict = ph.metrology.verify_sound_calibrator(
            "1", measured, nominal_frequency_hz=1000.0
        )
        agree += int(verdict.passes is conforms)
    return count(
        agree,
        len(examples),
        subject="verdicts",
        expected_label="No, No, Yes, Yes, No, Yes, Yes",
    )


@register(
    _CALIBRATORS,
    "IEC 60942:2017 A.6.4.7",
    "0,22 dB conforms to Table 5 and not to the abbreviated test, 2 verdicts",
)
def _chk_abbreviated_verdict() -> Outcome:
    """Class 1 at 1 kHz: 0,25 dB in Table 5, reduced to 0,20 dB by A.6.4.7."""
    measured = ph.metrology.SoundCalibratorMeasurements(
        environmental_level_deviation_db=0.22,
        environmental_level_uncertainty_db=0.10,
    )
    full = ph.metrology.verify_sound_calibrator(
        "1", measured, nominal_frequency_hz=1000.0
    )
    short = ph.metrology.verify_sound_calibrator(
        "1", measured, nominal_frequency_hz=1000.0, environmental_test="abbreviated"
    )
    agree = int(full.passes) + int(not short.passes)
    return count(
        agree,
        2,
        subject="verdicts",
        expected_label="conforms to Table 5 (0,25 dB), not to A.6.4.7 (0,20 dB)",
    )


@register(
    _CALIBRATORS,
    "IEC 60942:2017 5.5 and A.6.2.4 with Tables 2, 5, A.4 and A.5",
    "Class 1 at 2 kHz: 0,33 dB out of the band and in it, -0,5 % with U 0,25 %, "
    "3 verdicts",
)
def _chk_environmental_at_2_khz() -> Outcome:
    """Where Table 2 and Table 5 part: class 1 at 2 kHz, 0,35 dB against 0,30 dB.

    A level 0,33 dB off at an environmental condition outside the band of
    5.3.2 exceeds Table 5 (0,30 dB); the same 0,33 dB at a static pressure of
    the A.6.2 sweep inside the band meets Table 2 (0,35 dB), which A.6.2.4
    applies there, both with the 0,30 dB maximum of Table A.4. A frequency
    0,5 % off, inside the 0,7 % of Table 6, measured with 0,25 % against the
    0,2 % of Table A.5, cannot demonstrate conformance.
    """
    measured = ph.metrology.SoundCalibratorMeasurements(
        environmental_level_deviation_db=0.33,
        environmental_level_uncertainty_db=0.10,
        environmental_level_in_band_deviation_db=0.33,
        environmental_level_in_band_uncertainty_db=0.10,
        environmental_frequency_deviation_percent=-0.5,
        environmental_frequency_uncertainty_percent=0.25,
    )
    verdict = ph.metrology.verify_sound_calibrator(
        "1", measured, nominal_frequency_hz=2000.0
    )
    outcomes = tuple(
        verdict.requirement(name).verifications[0].outcome
        for name in (
            "environmental_level",
            "environmental_level_in_band",
            "environmental_frequency",
        )
    )
    agree = sum(a == b for a, b in zip(outcomes, (3, 1, 2), strict=True))
    return count(
        agree,
        3,
        subject="verdicts",
        expected_label=(
            "No by Table 5 (0,30 dB); Yes by Table 2 (0,35 dB); "
            "No, U over Table A.5 (0,2 %)"
        ),
    )
