#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound calibrators (IEC 60942:2017): the published tables and the verdict.

The tables are held against an independent transcription of the rasterised
pages (``tests/reference_data/calibrators.py``), including which end of each
range of nominal frequencies a row includes, read off the printed ">" and
"<" signs rather than off the library. The verdict is held to the
conformance rule of 5.1.15 through the limits the class and the nominal
frequency select, the /M static-pressure correction of 5.3.2 and B.4.3.2, and
the reduced limits of the abbreviated environmental test of A.6.4.7.
"""

from __future__ import annotations

import re
from types import MappingProxyType

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import pytest
import reference_data as ref

from phonometry import metrology
from phonometry.metrology.sound_calibrator import _fluctuation_limit_db

_CLASSES = ("LS", "1", "2")


def _bounds(printed: str) -> tuple[float, float, bool, bool]:
    """Read ``"> 63 to < 160"`` as (63, 160, excludes 63, excludes 160)."""
    match = re.fullmatch(r"(>?)\s*([\d ,]+?)\s+to\s+(<?)\s*([\d ,]+)", printed)
    assert match is not None, printed
    low_sign, low, high_sign, high = match.groups()

    def number(text: str) -> float:
        return float(text.replace(" ", "").replace(",", "."))

    return number(low), number(high), low_sign != ">", high_sign != "<"


def _check_banded(
    table: tuple[metrology.CalibratorTableRow, ...],
    printed: list[tuple[str, tuple[float | None, float | None, float | None]]],
) -> None:
    assert len(table) == len(printed)
    for row, (label, cells) in zip(table, printed, strict=True):
        lower, upper, with_lower, with_upper = _bounds(label)
        assert (row.lower_hz, row.upper_hz) == (lower, upper), label
        assert (row.includes_lower, row.includes_upper) == (with_lower, with_upper)
        assert (row.class_ls, row.class_1, row.class_2) == cells, label


def test_table_2_level_and_fluctuation() -> None:
    _check_banded(
        metrology.LEVEL_ACCEPTANCE_LIMITS_DB,
        [(label, level) for label, level, _ in ref.IEC60942_TABLE2],
    )
    _check_banded(
        metrology.FLUCTUATION_ACCEPTANCE_LIMITS_DB,
        [(label, fluct) for label, _, fluct in ref.IEC60942_TABLE2],
    )


def test_tables_5_and_7() -> None:
    _check_banded(
        metrology.ENVIRONMENTAL_LEVEL_ACCEPTANCE_LIMITS_DB, ref.IEC60942_TABLE5
    )
    _check_banded(metrology.DISTORTION_ACCEPTANCE_LIMITS_PERCENT, ref.IEC60942_TABLE7)


def test_tables_a1_a3_a4() -> None:
    _check_banded(
        metrology.LEVEL_MAX_UNCERTAINTY_DB,
        [(label, level) for label, level, _ in ref.IEC60942_TABLE_A1],
    )
    _check_banded(
        metrology.FLUCTUATION_MAX_UNCERTAINTY_DB,
        [(label, fluct) for label, _, fluct in ref.IEC60942_TABLE_A1],
    )
    _check_banded(metrology.DISTORTION_MAX_UNCERTAINTY_PERCENT, ref.IEC60942_TABLE_A3)
    _check_banded(
        metrology.ENVIRONMENTAL_LEVEL_MAX_UNCERTAINTY_DB, ref.IEC60942_TABLE_A4
    )


@pytest.mark.parametrize(
    ("published", "printed"),
    [
        (metrology.SUPPLY_VOLTAGE_ACCEPTANCE_LIMITS_DB, ref.IEC60942_TABLE3),
        (metrology.FREQUENCY_ACCEPTANCE_LIMITS_PERCENT, ref.IEC60942_TABLE4),
        (
            metrology.ENVIRONMENTAL_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT,
            ref.IEC60942_TABLE6,
        ),
        (metrology.FREQUENCY_MAX_UNCERTAINTY_PERCENT, ref.IEC60942_TABLE_A2),
        (
            metrology.ENVIRONMENTAL_FREQUENCY_MAX_UNCERTAINTY_PERCENT,
            ref.IEC60942_TABLE_A5,
        ),
        (
            metrology.SUPPLY_VOLTAGE_MAX_UNCERTAINTY_DB,
            ref.IEC60942_SUPPLY_VOLTAGE_MAX_U,
        ),
        (metrology.FIELD_IMMUNITY_ACCEPTANCE_LIMITS_DB, ref.IEC60942_FIELD_IMMUNITY),
        (
            metrology.FIELD_IMMUNITY_MAX_UNCERTAINTY_DB,
            (ref.IEC60942_FIELD_IMMUNITY_MAX_U,) * 3,
        ),
        (
            metrology.ABBREVIATED_LEVEL_REDUCTIONS_DB,
            ref.IEC60942_ABBREVIATED_REDUCTIONS,
        ),
        (
            metrology.ABBREVIATED_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT,
            ref.IEC60942_ABBREVIATED_FREQUENCY,
        ),
    ],
    ids=[
        "Table 3",
        "Table 4",
        "Table 6",
        "Table A.2",
        "Table A.5",
        "A.5.5.7",
        "5.9.4.2",
        "A.7.4.8",
        "A.6.4.7 level",
        "A.6.4.7 frequency",
    ],
)
def test_the_per_class_tables(
    published: MappingProxyType[str, float], printed: tuple[float, float, float]
) -> None:
    assert isinstance(published, MappingProxyType)
    assert tuple(published[c] for c in _CLASSES) == printed


def test_the_tables_refuse_writes() -> None:
    with pytest.raises(TypeError, match="does not support item assignment"):
        metrology.FREQUENCY_ACCEPTANCE_LIMITS_PERCENT["1"] = 5.0  # type: ignore[index]


def test_table_1_classes() -> None:
    assert metrology.CALIBRATOR_CLASSES == ("LS", "LS/M", "1", "1/M", "2")


@pytest.mark.parametrize(
    ("frequency_hz", "row_index"),
    [(31.5, 0), (63.0, 0), (63.5, 1), (159.9, 1), (160.0, 2), (1250.0, 2), (1251.0, 3)],
)
def test_row_ends_follow_the_printed_signs(frequency_hz: float, row_index: int) -> None:
    table = metrology.LEVEL_ACCEPTANCE_LIMITS_DB
    hits = [i for i, row in enumerate(table) if row.contains(frequency_hz)]
    assert hits == [row_index]


def test_a_mp_designation_reads_its_class_column() -> None:
    row = metrology.LEVEL_ACCEPTANCE_LIMITS_DB[2]
    assert row.for_class("1/M") == row.class_1
    assert row.for_class("LS/M") == row.class_ls


# --------------------------------------------------------------------------
# The verdict
# --------------------------------------------------------------------------
def _full_record(**overrides: object) -> metrology.SoundCalibratorMeasurements:
    fields: dict[str, object] = {
        "level_deviation_db": 0.12,
        "level_uncertainty_db": 0.10,
        "fluctuation_db": 0.02,
        "fluctuation_uncertainty_db": 0.02,
        "frequency_deviation_percent": -0.1,
        "frequency_uncertainty_percent": 0.05,
        "distortion_percent": 0.8,
        "distortion_uncertainty_percent": 0.3,
        "supply_voltage_deviation_db": [0.01, -0.02],
        "supply_voltage_uncertainty_db": 0.03,
        "environmental_level_deviation_db": [0.10, -0.15],
        "environmental_level_uncertainty_db": 0.12,
        "environmental_level_in_band_deviation_db": [0.0, -0.08],
        "environmental_level_in_band_uncertainty_db": 0.10,
        "environmental_frequency_deviation_percent": [0.1, -0.2],
        "environmental_frequency_uncertainty_percent": 0.1,
        "field_immunity_deviation_db": -0.05,
        "field_immunity_uncertainty_db": 0.04,
    }
    fields.update(overrides)
    return metrology.SoundCalibratorMeasurements(**fields)  # type: ignore[arg-type]


def test_a_class_1_calibrator_at_1_khz_that_conforms() -> None:
    result = metrology.verify_sound_calibrator(
        "1", _full_record(), nominal_frequency_hz=1000.0
    )
    assert result.passes
    assert result.failed == ()
    assert [r.name for r in result.requirements] == list(
        metrology.CALIBRATOR_REQUIREMENTS
    )
    level = result.requirement("level")
    assert level.acceptance_limits == (-0.25, 0.25)
    assert level.max_uncertainty == 0.15
    assert level.clause == "5.3.2"
    fluctuation = result.requirement("fluctuation")
    assert fluctuation.acceptance_limits == (0.0, 0.07)
    assert result.requirement("supply_voltage").max_uncertainty == 0.04
    assert len(result.requirement("supply_voltage").verifications) == 2


def _printed_cell(
    printed: list[tuple[str, tuple[float | None, float | None, float | None]]],
    frequency_hz: float,
    calibrator_class: str,
) -> float | None:
    """The cell a transcribed banded table prints for a class at a frequency."""
    column = _CLASSES.index(calibrator_class)
    for label, cells in printed:
        lower, upper, with_lower, with_upper = _bounds(label)
        above = frequency_hz >= lower if with_lower else frequency_hz > lower
        below = frequency_hz <= upper if with_upper else frequency_hz < upper
        if above and below:
            return cells[column]
    return None


def _page_limits(
    requirement: str, calibrator_class: str, frequency_hz: float
) -> tuple[tuple[float, float], float]:
    """The acceptance limits and the maximum uncertainty the page prints.

    Read from the transcription, never from the library: which table each
    requirement takes its limit and its maximum from is what is under test.
    """
    column = _CLASSES.index(calibrator_class)
    level = [(label, cells) for label, cells, _ in ref.IEC60942_TABLE2]
    fluctuation = [(label, cells) for label, _, cells in ref.IEC60942_TABLE2]
    level_u = [(label, cells) for label, cells, _ in ref.IEC60942_TABLE_A1]
    fluctuation_u = [(label, cells) for label, _, cells in ref.IEC60942_TABLE_A1]
    f, c = frequency_hz, calibrator_class
    sources: dict[str, tuple[float | None, float | None, bool]] = {
        "level": (_printed_cell(level, f, c), _printed_cell(level_u, f, c), False),
        "fluctuation": (
            _printed_cell(fluctuation, f, c),
            _printed_cell(fluctuation_u, f, c),
            True,
        ),
        "frequency": (
            ref.IEC60942_TABLE4[column],
            ref.IEC60942_TABLE_A2[column],
            False,
        ),
        "distortion": (
            _printed_cell(ref.IEC60942_TABLE7, f, c),
            _printed_cell(ref.IEC60942_TABLE_A3, f, c),
            True,
        ),
        "supply_voltage": (
            ref.IEC60942_TABLE3[column],
            ref.IEC60942_SUPPLY_VOLTAGE_MAX_U[column],
            False,
        ),
        "environmental_level": (
            _printed_cell(ref.IEC60942_TABLE5, f, c),
            _printed_cell(ref.IEC60942_TABLE_A4, f, c),
            False,
        ),
        "environmental_level_in_band": (
            _printed_cell(level, f, c),
            _printed_cell(ref.IEC60942_TABLE_A4, f, c),
            False,
        ),
        "environmental_frequency": (
            ref.IEC60942_TABLE6[column],
            ref.IEC60942_TABLE_A5[column],
            False,
        ),
        "field_immunity": (
            ref.IEC60942_FIELD_IMMUNITY[column],
            ref.IEC60942_FIELD_IMMUNITY_MAX_U,
            False,
        ),
    }
    limit, maximum, magnitude = sources[requirement]
    assert limit is not None, (requirement, c, f)
    assert maximum is not None, (requirement, c, f)
    return ((0.0, limit) if magnitude else (-limit, limit)), maximum


#: A nominal frequency inside every printed row a class has a figure in: class
#: 1 over 31,5 Hz to 16 kHz, both ends of each row and a point inside it, and
#: classes LS and 2 over 160 Hz to 1,25 kHz.
_ROW_FREQUENCIES = [
    *(
        ("1", f)
        for f in (31.5, 50.0, 63.0, 100.0, 160.0, 1000.0, 1250.0, 2000.0)
        + (4000.0, 5000.0, 8000.0, 10000.0, 16000.0)
    ),
    *((c, f) for c in ("LS", "2") for f in (160.0, 1000.0, 1250.0)),
]


@pytest.mark.parametrize("requirement", metrology.CALIBRATOR_REQUIREMENTS)
@pytest.mark.parametrize(
    ("calibrator_class", "frequency_hz"),
    _ROW_FREQUENCIES,
    ids=[f"class {c} at {f:g} Hz" for c, f in _ROW_FREQUENCIES],
)
def test_each_requirement_reads_its_own_tables(
    requirement: str, calibrator_class: str, frequency_hz: float
) -> None:
    """Every requirement, every class and every row, against the page.

    At 1 kHz Table 2 equals Table 5 for every class, and Table A.1 equals
    Table A.4 for classes LS and 1, so a requirement wired to its neighbour's
    table only shows away from 1 kHz: at 2 kHz class 1 prints 0,35 dB in
    Table 2 and 0,30 dB in Table 5.
    """
    result = metrology.verify_sound_calibrator(
        calibrator_class, _full_record(), nominal_frequency_hz=frequency_hz
    )
    measured = result.requirement(requirement)
    limits, maximum = _page_limits(requirement, calibrator_class, frequency_hz)
    assert measured.acceptance_limits == pytest.approx(limits)
    assert measured.max_uncertainty == pytest.approx(maximum)


@pytest.mark.parametrize(
    ("requirement", "deviation", "conforms"),
    [
        ("frequency", -0.7, True),
        ("frequency", -0.75, False),
        ("environmental_frequency", -0.6, True),
        ("field_immunity", -0.25, True),
        ("field_immunity", -0.30, False),
        ("supply_voltage", -0.06, True),
        ("level", -0.26, False),
    ],
)
def test_a_negative_deviation_meets_the_lower_limit(
    requirement: str,
    deviation: float,
    conforms: bool,  # noqa: FBT001
) -> None:
    """The level, supply-voltage, frequency and field limits bound |deviation|.

    Class 1 at 1 kHz: 0,7 % (Table 4), 0,7 % (Table 6), 0,25 dB (5.9.4.2),
    0,06 dB (Table 3) and 0,25 dB (Table 2), each on the negative side too.
    """
    deviation_field, uncertainty_field = _FIELD_NAMES[requirement]
    record = metrology.SoundCalibratorMeasurements(
        **{deviation_field: deviation, uncertainty_field: 0.01}
    )
    result = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=1000.0)
    assert result.passes is conforms


#: The record fields of the requirements the sign test above measures.
_FIELD_NAMES = {
    "level": ("level_deviation_db", "level_uncertainty_db"),
    "frequency": ("frequency_deviation_percent", "frequency_uncertainty_percent"),
    "supply_voltage": ("supply_voltage_deviation_db", "supply_voltage_uncertainty_db"),
    "environmental_frequency": (
        "environmental_frequency_deviation_percent",
        "environmental_frequency_uncertainty_percent",
    ),
    "field_immunity": ("field_immunity_deviation_db", "field_immunity_uncertainty_db"),
}


def test_the_static_pressure_sweep_inside_and_outside_the_band() -> None:
    """A.6.2.4: Table 2 inside the band of 5.3.2, Table 5 outside it.

    Class 1 at 2 kHz: 0,33 dB is inside the 0,35 dB of Table 2 and outside the
    0,30 dB of Table 5, with the 0,30 dB maximum of Table A.4 for both. The
    abbreviated test replaces the temperature and humidity tests only, so the
    in-band points keep Table 2 under it.
    """
    record = metrology.SoundCalibratorMeasurements(
        environmental_level_deviation_db=0.33,
        environmental_level_uncertainty_db=0.10,
        environmental_level_in_band_deviation_db=0.33,
        environmental_level_in_band_uncertainty_db=0.10,
    )
    result = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=2000.0)
    assert result.failed == ("environmental_level",)
    in_band = result.requirement("environmental_level_in_band")
    assert in_band.passes
    assert in_band.clause == "A.6.2.4"
    assert in_band.acceptance_limits == (-0.35, 0.35)
    assert in_band.max_uncertainty == 0.30
    short = metrology.verify_sound_calibrator(
        "1", record, nominal_frequency_hz=2000.0, environmental_test="abbreviated"
    )
    assert short.requirement("environmental_level_in_band").acceptance_limits == (
        -0.35,
        0.35,
    )
    assert short.requirement("environmental_level_in_band").clause == "A.6.2.4"


@pytest.mark.parametrize(
    ("example", "deviation", "limit", "uncertainty", "maximum", "conforms", "outcome"),
    [row for row in ref.IEC60942_TABLE_E1 if row[0] <= 7],
    ids=[f"E.1-{row[0]}" for row in ref.IEC60942_TABLE_E1 if row[0] <= 7],
)
def test_table_e1_through_the_class_1_level_at_1_khz(
    example: int,
    deviation: float,
    limit: float,
    uncertainty: float,
    maximum: float,
    conforms: bool,  # noqa: FBT001
    outcome: int,
) -> None:
    """Examples 1 to 7 use 0,25 dB and 0,15 dB, Table 2 and A.1 for class 1."""
    assert (limit, maximum) == (0.25, 0.15)
    record = metrology.SoundCalibratorMeasurements(
        level_deviation_db=deviation, level_uncertainty_db=uncertainty
    )
    result = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=1000.0)
    assert result.passes is conforms, f"example {example}"
    assert result.requirement("level").verifications[0].outcome == outcome


@pytest.mark.parametrize(
    ("calibrator_class", "frequency_hz"),
    [("LS", 125.0), ("2", 2000.0), ("LS", 1600.0), ("1", 20.0), ("1", 20000.0)],
)
def test_no_verdict_where_the_class_has_no_limit(
    calibrator_class: str, frequency_hz: float
) -> None:
    """5.1.2: conformance shall not be stated where there is no limit."""
    record = metrology.SoundCalibratorMeasurements(
        frequency_deviation_percent=0.1, frequency_uncertainty_percent=0.05
    )
    with pytest.raises(ValueError, match=r"5\.1\.2"):
        metrology.verify_sound_calibrator(
            calibrator_class, record, nominal_frequency_hz=frequency_hz
        )


def test_class_limits_at_the_ends_of_their_span() -> None:
    record = metrology.SoundCalibratorMeasurements(
        level_deviation_db=0.3, level_uncertainty_db=0.2
    )
    low = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=31.5)
    assert low.passes
    high = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=16000.0)
    assert high.requirement("level").acceptance_limits == (-0.5, 0.5)
    assert high.requirement("level").max_uncertainty == 0.5


def test_classes_ls_and_2_at_1_khz() -> None:
    record = metrology.SoundCalibratorMeasurements(
        level_deviation_db=0.10,
        level_uncertainty_db=0.10,
        distortion_percent=2.0,
        distortion_uncertainty_percent=0.5,
    )
    ls = metrology.verify_sound_calibrator("LS", record, nominal_frequency_hz=1000.0)
    assert ls.passes
    assert ls.requirement("distortion").acceptance_limits == (0.0, 2.0)
    two = metrology.verify_sound_calibrator(2, record, nominal_frequency_hz=1000.0)
    assert two.requirement("level").acceptance_limits == (-0.40, 0.40)
    assert two.requirement("level").max_uncertainty == 0.35
    assert two.calibrator_class == "2"


def test_the_pistonphone_correction_is_added_to_the_level() -> None:
    """At 100 Hz a 0,2 dB reading and a +0,1 dB correction land on 0,30 dB.

    In binary the sum is 0,300 000 000 000 000 04, one bit past the Table 2
    limit of class 1 below 160 Hz, and it still conforms; a correction of
    0,11 dB does not.
    """
    record = metrology.SoundCalibratorMeasurements(
        level_deviation_db=0.2,
        level_uncertainty_db=0.15,
        static_pressure_correction_db=0.1,
    )
    result = metrology.verify_sound_calibrator(
        "1/M", record, nominal_frequency_hz=100.0
    )
    assert result.passes
    assert result.requirement("level").verifications[0].deviation == pytest.approx(0.3)
    assert result.calibrator_class == "1/M"
    over = metrology.SoundCalibratorMeasurements(
        level_deviation_db=0.2,
        level_uncertainty_db=0.15,
        static_pressure_correction_db=0.11,
    )
    refused = metrology.verify_sound_calibrator("1/M", over, nominal_frequency_hz=100.0)
    assert not refused.passes


def test_a_pistonphone_level_needs_its_correction() -> None:
    record = metrology.SoundCalibratorMeasurements(
        level_deviation_db=0.20, level_uncertainty_db=0.15
    )
    with pytest.raises(ValueError, match="static_pressure_correction_db"):
        metrology.verify_sound_calibrator("LS/M", record, nominal_frequency_hz=250.0)


def test_only_a_pistonphone_takes_a_correction() -> None:
    """5.1.7: no other calibrator may need an environmental correction."""
    record = metrology.SoundCalibratorMeasurements(
        level_deviation_db=0.20,
        level_uncertainty_db=0.15,
        static_pressure_correction_db=0.0,
    )
    with pytest.raises(ValueError, match=r"5\.1\.7"):
        metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=250.0)


def test_one_correction_per_level_measurement() -> None:
    record = metrology.SoundCalibratorMeasurements(
        level_deviation_db=[0.20, 0.10],
        level_uncertainty_db=0.05,
        static_pressure_correction_db=[0.05, -0.30],
    )
    result = metrology.verify_sound_calibrator(
        "LS/M", record, nominal_frequency_hz=500.0
    )
    deviations = [v.deviation for v in result.requirement("level").verifications]
    assert deviations == pytest.approx([0.25, -0.20])
    assert not result.passes


def test_the_abbreviated_environmental_test() -> None:
    """A.6.4.7: Table 5 less 0,05 dB (class 1) and 0,5 % for the frequency."""
    record = metrology.SoundCalibratorMeasurements(
        environmental_level_deviation_db=0.22,
        environmental_level_uncertainty_db=0.10,
        environmental_frequency_deviation_percent=0.6,
        environmental_frequency_uncertainty_percent=0.1,
    )
    full = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=1000.0)
    assert full.passes
    short = metrology.verify_sound_calibrator(
        "1", record, nominal_frequency_hz=1000.0, environmental_test="abbreviated"
    )
    assert short.failed == ("environmental_level", "environmental_frequency")
    level = short.requirement("environmental_level")
    assert level.acceptance_limits == pytest.approx((-0.20, 0.20))
    assert level.clause == "A.6.4.7"
    assert short.requirement("environmental_frequency").acceptance_limits == (
        -0.5,
        0.5,
    )


def test_the_abbreviated_class_2_reductions() -> None:
    record = metrology.SoundCalibratorMeasurements(
        environmental_level_deviation_db=0.30,
        environmental_level_uncertainty_db=0.2,
        environmental_frequency_deviation_percent=1.3,
        environmental_frequency_uncertainty_percent=0.2,
    )
    result = metrology.verify_sound_calibrator(
        "2", record, nominal_frequency_hz=1000.0, environmental_test="abbreviated"
    )
    assert result.passes
    assert result.requirement("environmental_level").acceptance_limits == (
        pytest.approx((-0.30, 0.30))
    )


def test_an_unknown_environmental_test() -> None:
    record = _full_record()
    with pytest.raises(ValueError, match="environmental_test"):
        metrology.verify_sound_calibrator(
            "1", record, nominal_frequency_hz=1000.0, environmental_test="quick"
        )


def test_an_unknown_class() -> None:
    record = _full_record()
    with pytest.raises(ValueError, match="calibrator_class"):
        metrology.verify_sound_calibrator("0", record, nominal_frequency_hz=1000.0)


def test_a_record_with_nothing_in_it_passes_nothing() -> None:
    result = metrology.verify_sound_calibrator(
        "1", metrology.SoundCalibratorMeasurements(), nominal_frequency_hz=1000.0
    )
    assert result.requirements == ()
    assert not result.passes


def test_a_requirement_not_measured() -> None:
    record = metrology.SoundCalibratorMeasurements(
        level_deviation_db=0.1, level_uncertainty_db=0.1
    )
    result = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=1000.0)
    with pytest.raises(KeyError, match="'distortion' was not measured"):
        result.requirement("distortion")


def test_the_verdicts_have_no_truth_value() -> None:
    result = metrology.verify_sound_calibrator(
        "1", _full_record(), nominal_frequency_hz=1000.0
    )
    requirement = result.requirement("level")
    with pytest.raises(TypeError, match="SoundCalibratorVerification has no truth"):
        bool(result)
    with pytest.raises(TypeError, match="SoundCalibratorRequirement has no truth"):
        bool(requirement)


@pytest.mark.parametrize(
    ("fields", "fragment"),
    [
        ({"level_deviation_db": 0.1}, "level_uncertainty_db"),
        ({"level_uncertainty_db": 0.1}, "level_deviation_db"),
        (
            {"fluctuation_db": -0.01, "fluctuation_uncertainty_db": 0.01},
            "fluctuation_db",
        ),
        (
            {"distortion_percent": 1.0, "distortion_uncertainty_percent": -0.1},
            "distortion_uncertainty_percent",
        ),
        (
            {"level_deviation_db": [0.1, 0.2], "level_uncertainty_db": [0.1, 0.1, 0.1]},
            "level_uncertainty_db",
        ),
        ({"static_pressure_correction_db": 0.1}, "static_pressure_correction_db"),
        (
            {
                "frequency_deviation_percent": float("nan"),
                "frequency_uncertainty_percent": 0.1,
            },
            "frequency_deviation_percent",
        ),
        (
            {"level_deviation_db": [[0.1]], "level_uncertainty_db": 0.1},
            "level_deviation_db",
        ),
    ],
)
def test_a_record_that_cannot_be_graded(
    fields: dict[str, object], fragment: str
) -> None:
    with pytest.raises(ValueError, match=fragment):
        metrology.SoundCalibratorMeasurements(**fields)  # type: ignore[arg-type]


def test_the_record_freezes_what_it_is_given() -> None:
    values = [0.1, 0.2]
    record = metrology.SoundCalibratorMeasurements(
        level_deviation_db=values, level_uncertainty_db=0.1
    )
    values[0] = 9.0
    assert record.level_deviation_db == (0.1, 0.2)
    assert record.pairs("level") == ((0.1, 0.1), (0.2, 0.1))
    assert record.pairs("distortion") == ()


# --------------------------------------------------------------------------
# The fluctuation limit sensitivity() screens a recording with
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("frequency_hz", "calibrator_class", "limit"),
    [
        (63.0, "1", 0.20),
        (100.0, "1", 0.10),
        (160.0, "1", 0.07),
        (1000.0, "1", 0.07),
        (1000.0, "LS", 0.03),
        (1000.0, "2", 0.15),
        (1000.0, "1/M", 0.07),
        (20.0, "1", 0.07),
        (4000.0, "LS", 0.03),
        (63.0, "2", 0.15),
    ],
)
def test_the_fluctuation_limit_of_table_2(
    frequency_hz: float, calibrator_class: str, limit: float
) -> None:
    """The printed cell, or the strictest of the class column where it is a dash."""
    assert _fluctuation_limit_db(frequency_hz, calibrator_class) == pytest.approx(limit)


# --------------------------------------------------------------------------
# The figures
# --------------------------------------------------------------------------
def test_the_verification_plot_draws_two_bars_per_measurement() -> None:
    record = _full_record(environmental_level_deviation_db=[0.10, 0.30])
    result = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=1000.0)
    ax = result.plot()
    measurements = sum(len(r.verifications) for r in result.requirements)
    assert len(ax.patches) == 2 * measurements
    red = mpl.colors.to_rgba("#d62728")
    reds = [p for p in ax.patches if p.get_facecolor() == red]
    assert len(reds) == 1, "only the 0,30 dB environmental reading exceeds its limit"
    assert reds[0].get_width() == pytest.approx(120.0)
    labels = [t.get_text() for t in ax.get_yticklabels()]
    assert "Environmental level (§5.5) #2" in labels
    assert "does not conform" in ax.get_title()
    plt.close("all")


def test_the_verification_plot_in_spanish() -> None:
    result = metrology.verify_sound_calibrator(
        "1", _full_record(), nominal_frequency_hz=1000.0
    )
    ax = result.plot(language="es")
    assert ax.get_title().startswith("Calibrador acústico (IEC 60942:2017): conforme")
    assert "Nivel generado (§5.3.2)" in [t.get_text() for t in ax.get_yticklabels()]
    assert ax.get_xlabel() == "Parte del margen consumida [%]"
    plt.close("all")


def test_an_empty_verification_has_nothing_to_draw() -> None:
    result = metrology.verify_sound_calibrator(
        "1", metrology.SoundCalibratorMeasurements(), nominal_frequency_hz=1000.0
    )
    with pytest.raises(ValueError, match="at least one measured requirement"):
        result.plot()


def test_the_requirement_plot_draws_every_measurement() -> None:
    record = metrology.SoundCalibratorMeasurements(
        environmental_level_deviation_db=[0.10, -0.15, 0.30],
        environmental_level_uncertainty_db=0.12,
    )
    result = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=1000.0)
    ax = result.requirement("environmental_level").plot()
    diamonds = [line for line in ax.lines if line.get_marker() == "D"]
    crosses = [line for line in ax.lines if line.get_marker() == "X"]
    assert len(diamonds) == 2
    assert len(crosses) == 1
    assert crosses[0].get_xdata()[0] == 3.0
    assert ax.get_title() == "Environmental level (§5.5): does not conform"
    plt.close("all")


def test_a_verdict_on_its_limit_is_not_drawn_as_a_failure() -> None:
    """0,2 dB plus a 0,1 dB correction reads a hair over 100 % of 0,30 dB.

    The verdict forgives that last bit and conforms; the bar has to follow the
    verdict rather than the share, or a conforming calibrator is drawn red.
    """
    record = metrology.SoundCalibratorMeasurements(
        level_deviation_db=0.2,
        level_uncertainty_db=0.15,
        static_pressure_correction_db=0.1,
    )
    result = metrology.verify_sound_calibrator(
        "1/M", record, nominal_frequency_hz=100.0
    )
    assert result.passes
    assert result.requirement("level").verifications[0].share_of_acceptance_limit > 1
    ax = result.plot()
    red = mpl.colors.to_rgba("#d62728")
    assert [p for p in ax.patches if p.get_facecolor() == red] == []
    legend = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "Past its allowance" not in legend
    plt.close("all")


def test_the_legend_names_the_red_bars_and_the_dashed_line() -> None:
    record = _full_record(environmental_level_deviation_db=[0.10, 0.30])
    result = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=1000.0)
    legend = [t.get_text() for t in result.plot().get_legend().get_texts()]
    assert legend == [
        "Deviation / acceptance limit",
        "Uncertainty / maximum permitted",
        "Past its allowance",
        "Whole allowance (100 %)",
    ]
    plt.close("all")
    spanish = result.plot(language="es").get_legend().get_texts()
    assert "Supera su margen" in [t.get_text() for t in spanish]
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize(
    "fields",
    [
        {"level_deviation_db": 0.12, "level_uncertainty_db": 0.10},
        {
            "level_deviation_db": 0.12,
            "level_uncertainty_db": 0.10,
            "frequency_deviation_percent": -0.05,
            "frequency_uncertainty_percent": 0.02,
            "distortion_percent": 0.9,
            "distortion_uncertainty_percent": 0.3,
        },
    ],
    ids=["one requirement", "an Annex B periodic test"],
)
def test_the_legend_clears_the_x_label(fields: dict[str, float], language: str) -> None:
    """The legend sits below the x label however few rows the figure has."""
    record = metrology.SoundCalibratorMeasurements(**fields)  # type: ignore[arg-type]
    result = metrology.verify_sound_calibrator("1", record, nominal_frequency_hz=1000.0)
    ax = result.plot(language=language)
    figure = ax.get_figure()
    assert figure is not None
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()  # type: ignore[attr-defined]
    legend = ax.get_legend().get_window_extent(renderer)
    label = ax.xaxis.label.get_window_extent(renderer)
    assert not legend.overlaps(label)
    assert legend.y1 < label.y0
    assert legend.y0 >= figure.bbox.y0
    plt.close("all")


@pytest.mark.parametrize(
    ("requirement", "axis_label"),
    [
        ("distortion", "Total distortion + noise [%]"),
        ("fluctuation", "Short-term level fluctuation [dB]"),
    ],
)
def test_a_magnitude_is_drawn_against_its_maximum_alone(
    requirement: str, axis_label: str
) -> None:
    """Table 7 and 5.3.3 print a maximum, not a deviation with two limits."""
    result = metrology.verify_sound_calibrator(
        "1", _full_record(), nominal_frequency_hz=1000.0
    )
    ax = result.requirement(requirement).plot()
    assert ax.get_ylabel() == axis_label
    legend = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "Acceptance limit" in legend
    assert "Lower acceptance limit" not in legend
    assert "Upper acceptance limit" not in legend
    plt.close("all")
    spanish = result.requirement("distortion").plot(language="es")
    assert spanish.get_ylabel() == "Distorsión total + ruido [%]"
    plt.close("all")


def test_a_signed_requirement_keeps_both_limits_and_its_axis() -> None:
    result = metrology.verify_sound_calibrator(
        "1", _full_record(), nominal_frequency_hz=1000.0
    )
    ax = result.requirement("environmental_level_in_band").plot()
    assert ax.get_ylabel() == "Deviation from design goal [dB]"
    legend = [t.get_text() for t in ax.get_legend().get_texts()]
    assert {"Upper acceptance limit", "Lower acceptance limit"} <= set(legend)
    assert ax.get_title() == "Level in the reference band (§A.6.2.4): conforms"
    plt.close("all")
