#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound calibrators (IEC 60942:2017) and the conformance rule of IEC TC 29.

Two things are pinned here. The first is the rule itself, which IEC 60942
prints in 5.1.15 and IEC 61672-1:2013 in 5.1.21 in the same sentence: a
requirement is met when the measured deviation is within the acceptance
limits AND the actual expanded uncertainty is within the maximum permitted,
both limits inclusive. Each standard prints worked examples with the verdict
and the reason, eight in IEC 60942 Table E.1 and ten in IEC 61672-1 Table C.1,
and each is a row: the verdict and the printed reason have to come back, the
boundary cases included (a deviation equal to its limit, an uncertainty equal
to its maximum, and the deviation of -1,2 dB on the lower limit of C.1).

The second is IEC 60942 itself: Tables 2 to 7 and A.1 to A.5 and the three
limits the clauses print in their text, each cell against an independent
transcription of the rasterised page, dashes and range ends included, and the
verdict of :func:`phonometry.metrology.verify_sound_calibrator` where the
tables meet the rule.

Oracle: IEC 60942:2017 read in UNE-EN IEC 60942:2018 (PDF page = folio + 8):
Tables 2 and 3 (folio 16), 4 (17), 5 and 6 (18), 7 (19), A.1 (28), A.2 (29),
A.3 (30), A.4 (32), A.5 (35), the text of 5.9.4.2 (21), A.5.5.7 (27), A.6.4.7
(34) and A.7.4.8 (40), and Table E.1 (52). IEC 61672-1:2013 read in BS EN
61672-1:2013 (PDF page = folio + 2): 5.1.21 (folio 16) and Table C.1 (45).
"""

from __future__ import annotations

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
    expected = {"conforms": float(conforms), "outcome": float(outcome)}
    computed = {"conforms": float(result.passes), "outcome": float(result.outcome)}
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


def _ends(printed: str) -> tuple[bool, bool]:
    """Which ends a printed range includes: ``"> 63 to < 160"`` includes neither."""
    low, high = printed.split(" to ")
    return not low.startswith(">"), not high.startswith("<")


def _banded_matches(
    table: Sequence[CalibratorTableRow],
    printed: Sequence[tuple[str, tuple[float | None, float | None, float | None]]],
) -> tuple[int, int]:
    """Agreeing cells and range ends between a published table and the page."""
    matching = total = 0
    for row, (label, cells) in zip(table, printed, strict=True):
        published = (row.class_ls, row.class_1, row.class_2)
        ends = (row.includes_lower, row.includes_upper)
        matching += sum(a == b for a, b in zip(published, cells, strict=True))
        matching += sum(a == b for a, b in zip(ends, _ends(label), strict=True))
        total += 5
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
    "Level and short-term fluctuation limits, dashes and range ends, by class",
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
