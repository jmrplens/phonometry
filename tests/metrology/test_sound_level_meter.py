#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Periodic tests of a sound level meter (IEC 61672-3:2013): tables and verdict.

The published tables of IEC 61672-1:2013 (Tables 4, 5 and B.1, and Table 3 at
the test frequencies) are held against an independent transcription of the
rasterised pages (``tests/reference_data/sound_level_meters.py``), parsed from
the strings the page prints. The verdict is held to the conformance rule of
4.1 just inside, on and just past every acceptance limit a clause reads, for
both classes, and on and just past every maximum of Table B.1 it reads, all
generated from that transcription; to the exception of 4.4, to the
completeness 8.1 asks for and to the statements of 22 r), s) and t), word for
word.
"""

from __future__ import annotations

import dataclasses
import math
import re
from collections.abc import Callable
from types import MappingProxyType
from typing import Any

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref

from phonometry import metrology

_NAN = math.nan


def _number(text: str) -> float:
    """A printed number, ``"-0,1"`` or ``"-∞"``, its thousands grouped with a space."""
    return float(text.replace(" ", "").replace(",", ".").replace("∞", "inf"))


def _limits(text: str) -> tuple[float, float]:
    """``"±0,5"`` or ``"+1,0; -1,5"`` as ``(lower, upper)``."""
    if text.startswith("±"):
        value = _number(text[1:])
        return -value, value
    upper, lower = (part.strip() for part in text.split(";"))
    return _number(lower), _number(upper)


def _statement(template: str, meter_class: int) -> str:
    """A statement of Clause 22 with class Y and the date filled in."""
    return template.replace("class Y", f"class {meter_class}").replace(":–", ":2013")


#: The steps of 16.3 for the meter of :func:`_record`, in the order they are
#: taken: from the starting point of 94 dB up in 5 dB steps to 119 dB, within
#: 5 dB of the upper boundary of its linear operating range, 120 dB, then in
#: 1 dB steps to 120 dB, below the first indication of overload at 121 dB;
#: and down the same way to 55 dB, above the first under-range at 54 dB.
_STEPS_DB = (
    *(94.0, 99.0, 104.0, 109.0, 114.0, 119.0, 120.0),
    *(89.0, 84.0, 79.0, 74.0, 69.0, 64.0, 59.0, 58.0, 57.0, 56.0, 55.0),
)

#: What the instruction manual of that meter states, and where its overload
#: and under-range indications first appeared, as the record carries them.
_PROCEDURE: dict[str, Any] = {
    "linear_operating_range_db": [55.0, 120.0],
    "linearity_starting_point_db": 94.0,
    "linearity_overload_level_db": 121.0,
    "linearity_under_range_level_db": 54.0,
}

#: The 16 results of that meter, one per step.
_LINEARITY_DB = [0.0, 0.1, 0.1, -0.1, 0.2, 0.2, 0.3, *[-0.1, 0.1, -0.2] * 3, -0.2, 0.0]


def _record(**over: Any) -> metrology.SoundLevelMeterPeriodicMeasurements:
    """A complete class 1 record, every result well inside its limits.

    Of a meter with three level ranges, which :data:`_METER` declares, so
    Clause 17 holds 17.3 on the two besides the reference one and 17.4 on
    all three, the reference one first.
    """
    base: dict[str, Any] = {
        "static_pressures_kpa": [100.8, 100.6],
        "air_temperatures_c": [23.1, 23.4],
        "relative_humidities_percent": [45.0, 47.0],
        "calibration_check_initial_db": 93.9,
        "calibration_check_adjusted_db": 94.0,
        "self_noise_microphone_db": 17.2,
        "self_noise_electrical_db": {"A": 12.1, "C": 14.0, "Z": 19.5},
        "acoustic_weighting_deviations_db": [0.2, -0.6],
        "acoustic_weighting_uncertainties_db": [0.25, 0.4],
        "electrical_weighting_deviations_db": {
            "A": [0.1, 0.0, 0.0, 0.0, 0.0, 0.0, -0.1, -0.2, -0.5],
            "C": [0.1, 0.0, 0.0, 0.0, 0.0, 0.0, -0.1, -0.3, -0.7],
            "Z": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.1, -0.4],
        },
        "electrical_weighting_uncertainties_db": {
            k: [0.15] * 9 for k in ("A", "C", "Z")
        },
        "weighting_at_1khz_deviations_db": {"C": 0.0, "Z": 0.1},
        "weighting_at_1khz_uncertainties_db": {"C": 0.12, "Z": 0.12},
        "time_weighting_at_1khz_deviations_db": {"S": 0.0, "eq": 0.05},
        "time_weighting_at_1khz_uncertainties_db": {"S": 0.12, "eq": 0.12},
        "long_term_stability_db": 0.05,
        "long_term_stability_uncertainty_db": 0.08,
        "linearity_deviations_db": _LINEARITY_DB,
        "linearity_uncertainties_db": [0.2] * len(_STEPS_DB),
        "linearity_levels_db": list(_STEPS_DB),
        **_PROCEDURE,
        "range_linearity_deviations_db": {
            "17.3": [0.1, -0.1],
            "17.4": [0.1, 0.0, 0.2],
        },
        "range_linearity_uncertainties_db": {
            "17.3": [0.2, 0.2],
            "17.4": [0.2, 0.2, 0.2],
        },
        "toneburst_responses_db": {
            "F": [-1.0, -18.1, -27.4],
            "S": [-7.4, -27.2],
            "E": [-7.0, -27.0, -36.1],
        },
        "toneburst_uncertainties_db": {
            "F": [0.2, 0.2, 0.2],
            "S": [0.2, 0.2],
            "E": [0.2, 0.2, 0.2],
        },
        "c_peak_differences_db": [3.6, 2.5, 2.3],
        "c_peak_uncertainties_db": [0.3, 0.3, 0.3],
        "c_peak_overload_indicated": False,
        "overload_difference_db": 0.3,
        "overload_uncertainty_db": 0.2,
        "overload_latched": True,
        "high_level_stability_db": 0.02,
        "high_level_stability_uncertainty_db": 0.08,
    }
    base.update(over)
    return metrology.SoundLevelMeterPeriodicMeasurements(**base)


def _class_2_record(**over: Any) -> metrology.SoundLevelMeterPeriodicMeasurements:
    """A complete class 2 record of a meter with A only, F and no Leq."""
    base: dict[str, Any] = {
        "self_noise_electrical_db": {"A": 14.0},
        "electrical_weighting_deviations_db": {"A": [0.0] * 8},
        "electrical_weighting_uncertainties_db": {"A": [0.2] * 8},
        "weighting_at_1khz_deviations_db": None,
        "weighting_at_1khz_uncertainties_db": None,
        "time_weighting_at_1khz_deviations_db": None,
        "time_weighting_at_1khz_uncertainties_db": None,
        "range_linearity_deviations_db": None,
        "range_linearity_uncertainties_db": None,
        "toneburst_responses_db": {"F": [-1.0, -18.0, -27.0]},
        "toneburst_uncertainties_db": {"F": [0.2, 0.2, 0.2]},
        "c_peak_differences_db": None,
        "c_peak_uncertainties_db": None,
        "c_peak_overload_indicated": None,
        "overload_difference_db": None,
        "overload_uncertainty_db": None,
        "overload_latched": None,
    }
    base.update(over)
    return _record(**base)


#: The meter of :func:`_record` as its manual declares the one feature a
#: record cannot count: three level ranges.
_METER = metrology.SoundLevelMeterFeatures(level_ranges=3)


def _verify(
    record: metrology.SoundLevelMeterPeriodicMeasurements,
    meter_class: int = 1,
    **kw: Any,
) -> metrology.SoundLevelMeterPeriodicVerification:
    """The verdict; a record holding Clause 17 is of the meter of :data:`_METER`.

    Unless ``features`` says otherwise: a record without Clause 17 is left to
    the features the test gives, which is what the tests of 8.1 read.
    """
    if record.range_linearity_deviations_db is not None:
        kw.setdefault("features", _METER)
    return metrology.verify_sound_level_meter_periodic(meter_class, record, **kw)


#: The meter of :func:`_class_2_record` as its manual declares it: A and F
#: only, one level range, no time-averaged display, no sound exposure level
#: and no C-weighted peak.
_BASIC = metrology.SoundLevelMeterFeatures(
    c_weighting=False,
    z_weighting=False,
    s_time_weighting=False,
    time_averaged=False,
    sound_exposure_level=False,
    level_ranges=1,
    c_weighted_peak=False,
)


def _basic(**declared: int | None) -> metrology.SoundLevelMeterFeatures:
    """:data:`_BASIC` with some answers changed."""
    return dataclasses.replace(_BASIC, **declared)


# ---------------------------------------------------------------------------
# The tables of IEC 61672-1:2013
# ---------------------------------------------------------------------------


def test_table_4_f_and_e_match_the_page() -> None:
    f_rows = metrology.IEC61672_TABLE_4["F"]
    e_rows = metrology.IEC61672_TABLE_4["E"]
    assert len(f_rows) == len(e_rows) == len(ref.IEC61672_1_TABLE_4_F_AND_E)
    for f_row, e_row, printed in zip(
        f_rows, e_rows, ref.IEC61672_1_TABLE_4_F_AND_E, strict=True
    ):
        duration, f_ref, e_ref, class_1, class_2 = printed
        for row, reference in ((f_row, f_ref), (e_row, e_ref)):
            assert row.duration_ms == _number(duration)
            assert row.reference_response_db == _number(reference)
            assert row.class_1_limits_db == _limits(class_1)
            assert row.class_2_limits_db == _limits(class_2)


def test_table_4_s_matches_the_page() -> None:
    rows = metrology.IEC61672_TABLE_4["S"]
    assert len(rows) == len(ref.IEC61672_1_TABLE_4_S)
    for row, (duration, reference, class_1, class_2) in zip(
        rows, ref.IEC61672_1_TABLE_4_S, strict=True
    ):
        assert row.duration_ms == _number(duration)
        assert row.reference_response_db == _number(reference)
        assert row.limits_db(1) == _limits(class_1)
        assert row.limits_db(2) == _limits(class_2)


@pytest.mark.parametrize(("key", "tau_s"), [("F", 0.125), ("S", 1.0)])
def test_table_4_time_weighted_rows_follow_equation_7(key: str, tau_s: float) -> None:
    """delta_ref = 10 lg(1 - exp(-Tb/tau)), rounded to a tenth (NOTE 1)."""
    for row in metrology.IEC61672_TABLE_4[key]:
        exact = 10.0 * math.log10(1.0 - math.exp(-row.duration_ms / 1000.0 / tau_s))
        assert round(exact, 1) == pytest.approx(row.reference_response_db, abs=1e-9)


def test_table_4_exposure_rows_follow_equation_8() -> None:
    """delta_ref = 10 lg(Tb / T0), T0 = 1 s, rounded to a tenth (NOTE 2)."""
    for row in metrology.IEC61672_TABLE_4["E"]:
        exact = 10.0 * math.log10(row.duration_ms / 1000.0)
        assert round(exact, 1) == pytest.approx(row.reference_response_db, abs=1e-9)


def test_table_5_matches_the_page() -> None:
    signals = {"one": "one cycle"}
    rows = metrology.IEC61672_TABLE_5
    assert len(rows) == len(ref.IEC61672_1_TABLE_5)
    for row, (cycles, frequency, reference, class_1, class_2) in zip(
        rows, ref.IEC61672_1_TABLE_5, strict=True
    ):
        assert row.signal == signals.get(cycles, cycles)
        assert row.nominal_frequency_hz == _number(frequency)
        assert row.reference_difference_db == _number(reference)
        assert row.limits_db(1) == _limits(class_1)
        assert row.limits_db(2) == _limits(class_2)


@pytest.mark.parametrize("meter_class", [1, 2])
def test_table_3_is_read_as_printed_at_the_test_frequencies(meter_class: int) -> None:
    """The verdict reads Table 3 through ``filters.weighting_class_limits``."""
    from phonometry.filters import weighting_class_limits

    frequencies, lower, upper = weighting_class_limits(meter_class)
    published = {
        float(f): (float(lo), float(up))
        for f, lo, up in zip(frequencies, lower, upper, strict=True)
    }
    for printed in ref.IEC61672_1_TABLE_3_TEST_LIMITS:
        assert published[_number(printed[0])] == _limits(printed[meter_class])


def test_table_b1_matches_the_page() -> None:
    """Every printed row, the decay-rate cell split in its F and S halves."""
    rows = iter(metrology.IEC61672_TABLE_B1)
    for requirement, reference, printed in ref.IEC61672_1_TABLE_B1:
        if "dB/s" in printed:
            halves = [part.strip().split(" dB/s for ") for part in printed.split(";")]
            for value, which in halves:
                row = next(rows)
                assert (row.requirement, row.reference) == (
                    requirement,
                    f"{reference}, {which}",
                )
                assert (row.max_uncertainty, row.unit) == (_number(value), "dB/s")
            continue
        row = next(rows)
        assert (row.requirement, row.reference) == (requirement, reference)
        assert (row.max_uncertainty, row.unit) == (_number(printed), "dB")
    assert next(rows, None) is None


def test_table_b1_bands_read_the_printed_ends() -> None:
    """ ">1 kHz to 2 kHz" leaves 1 kHz to the band below it."""
    weighting = [
        r for r in metrology.IEC61672_TABLE_B1 if r.requirement.startswith("Frequency")
    ]
    assert [r.contains(4000.0) for r in weighting] == [True, False, False]
    assert [r.contains(4000.1) for r in weighting] == [False, True, False]
    assert [r.contains(10000.0) for r in weighting] == [False, True, False]
    assert [r.contains(16000.0) for r in weighting] == [False, False, True]
    unbanded = next(r for r in metrology.IEC61672_TABLE_B1 if r.reference == "5.5.9")
    assert unbanded.contains(123.0)


def test_tables_are_read_only() -> None:
    assert isinstance(metrology.IEC61672_TABLE_4, MappingProxyType)
    assert isinstance(metrology.ELECTRICAL_TEST_FREQUENCIES_HZ, MappingProxyType)
    assert isinstance(metrology.TONEBURST_TEST_DURATIONS_MS, MappingProxyType)
    assert isinstance(metrology.PERIODIC_TEST_ENVIRONMENT, MappingProxyType)
    assert isinstance(metrology.IEC61672_TABLE_5, tuple)
    assert isinstance(metrology.IEC61672_TABLE_B1, tuple)
    row = metrology.IEC61672_TABLE_4["F"][0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.reference_response_db = 1.0  # type: ignore[misc]


def test_limits_refuse_a_class_the_standard_does_not_define() -> None:
    row = metrology.IEC61672_TABLE_5[0]
    with pytest.raises(ValueError, match="'meter_class' must be 1 or 2"):
        row.limits_db(3)


def test_test_frequencies_and_durations() -> None:
    assert metrology.ELECTRICAL_TEST_FREQUENCIES_HZ[1][-1] == 16000.0
    assert len(metrology.ELECTRICAL_TEST_FREQUENCIES_HZ[1]) == 9
    assert len(metrology.ELECTRICAL_TEST_FREQUENCIES_HZ[2]) == 8
    assert metrology.ACOUSTIC_TEST_FREQUENCIES_HZ == (125.0, 8000.0)
    assert metrology.TONEBURST_TEST_DURATIONS_MS["S"] == (200.0, 2.0)


# ---------------------------------------------------------------------------
# The verdict and the statements of Clause 22
# ---------------------------------------------------------------------------


def test_a_complete_record_passes_with_statement_s() -> None:
    result = _verify(_record())
    assert result.passes
    assert result.missing == ()
    assert result.incomplete == ()
    assert result.statement == _statement(ref.IEC61672_3_STATEMENT_S, 1)
    assert [r.name for r in result.requirements] == list(
        metrology.SLM_PERIODIC_REQUIREMENTS
    )


def test_public_pattern_approval_and_manual_corrections_give_statement_r() -> None:
    result = _verify(
        _record(), pattern_approval_public=True, corrections_in_manual=True
    )
    assert result.statement == _statement(ref.IEC61672_3_STATEMENT_R, 1)


def test_corrections_from_elsewhere_give_statement_s() -> None:
    result = _verify(
        _record(), pattern_approval_public=True, corrections_in_manual=False
    )
    assert result.statement == _statement(ref.IEC61672_3_STATEMENT_S, 1)


def test_a_source_of_the_corrections_not_declared_gives_statement_s() -> None:
    """12.5 has the laboratory state the source; 22 r) is not assumed."""
    result = _verify(_record(), pattern_approval_public=True)
    assert not result.corrections_in_manual
    assert result.statement == _statement(ref.IEC61672_3_STATEMENT_S, 1)


def test_a_class_2_meter_with_a_only_passes() -> None:
    result = _verify(_class_2_record(), 2, features=_BASIC)
    assert result.passes, (result.missing, result.incomplete, result.undeclared)
    assert result.statement == _statement(ref.IEC61672_3_STATEMENT_S, 2)
    assert "14.2" not in {r.clause for r in result.requirements}
    assert [clause for clause, _ in result.not_applicable] == [
        "14.2",
        "14.3",
        "17",
        "19",
        "20",
    ]


def test_a_failure_gives_statement_t_and_its_reason() -> None:
    record = _record(linearity_deviations_db=_placed(_LINEARITY_DB, 2, 0.9))
    result = _verify(record, pattern_approval_public=True)
    assert not result.passes
    assert result.failed == (("16", "104 dB"),)
    head = _statement(ref.IEC61672_3_STATEMENT_T, 1)
    assert result.statement.startswith(head)
    assert "measured level linearity deviations exceeded" in result.statement
    assert "clause 16 (level linearity on the reference level range), 104 dB" in (
        result.statement
    )


def _electrical(weighting: str, index: int, value: float) -> dict[str, list[float]]:
    rows = {k: [0.0] * 9 for k in ("A", "C", "Z")}
    rows[weighting][index] = value
    return rows


def _toneburst(key: str, index: int, value: float) -> dict[str, list[float]]:
    rows = {"F": [-1.0, -18.0, -27.0], "S": [-7.4, -27.0], "E": [-7.0, -27.0, -36.0]}
    rows[key][index] = value
    return rows


def _full_class_2(**over: Any) -> metrology.SoundLevelMeterPeriodicMeasurements:
    """The meter of :func:`_record`, with every feature, tested as class 2."""
    base: dict[str, Any] = {
        "electrical_weighting_deviations_db": {k: [0.0] * 8 for k in "ACZ"},
        "electrical_weighting_uncertainties_db": {k: [0.15] * 8 for k in "ACZ"},
    }
    base.update(over)
    return _record(**base)


#: How far inside and past a printed limit or maximum the verdict is read, dB:
#: a hundredth of the 0,1 dB a meter displays.
_STEP_DB = 0.01

#: IEC 61672-3:2013 12.7 and 13.4: the nominal test frequencies, as the
#: transcription of Table 3 prints them, by class.
_ACOUSTIC_FREQUENCIES = ("125", "8 000")
_ELECTRICAL_FREQUENCIES = {
    1: ("63", "125", "250", "500", "1 000", "2 000", "4 000", "8 000", "16 000"),
    2: ("63", "125", "250", "500", "1 000", "2 000", "4 000", "8 000"),
}

#: IEC 61672-3:2013 18.5 to 18.7: the toneburst durations each measurement
#: is tested at, as Table 4 prints them.
_TONEBURST_DURATIONS = {
    "F": ("200", "2", "0,25"),
    "S": ("200", "2"),
    "E": ("200", "2", "0,25"),
}


def _table_3(frequency: str, meter_class: int) -> tuple[float, float]:
    row = next(r for r in ref.IEC61672_1_TABLE_3_TEST_LIMITS if r[0] == frequency)
    return _limits(row[meter_class])


def _text_limits(clause: str, meter_class: int) -> tuple[float, float]:
    """A limit printed in the text: "±0,8", or "1,5" for either way (5.11.3)."""
    printed = ref.IEC61672_1_TEXT_LIMITS[clause][meter_class - 1]
    if "±" in printed or ";" in printed:
        return _limits(printed.replace("± ", "±"))
    return -_number(printed), _number(printed)


def _table_4(key: str, duration: str, meter_class: int) -> tuple[float, float, float]:
    """``(reference, lower, upper)`` of a Table 4 row as the page prints it."""
    if key == "S":
        row = next(r for r in ref.IEC61672_1_TABLE_4_S if r[0] == duration)
        return (_number(row[1]), *_limits(row[1 + meter_class]))
    row_fe = next(r for r in ref.IEC61672_1_TABLE_4_F_AND_E if r[0] == duration)
    reference = row_fe[1] if key == "F" else row_fe[2]
    return (_number(reference), *_limits(row_fe[2 + meter_class]))


def _placed(base: list[float], index: int, value: float) -> list[float]:
    row = list(base)
    row[index] = value
    return row


#: The fields of a record a value goes in.
_Fields = Callable[[float], dict[str, Any]]


@dataclasses.dataclass(frozen=True)
class _Limit:
    """One printed limit of one result: the verdict flips across it."""

    case: str
    name: str
    meter_class: int
    at_limit: float
    outward: float
    fields: _Fields

    def record(self, offset: float) -> metrology.SoundLevelMeterPeriodicMeasurements:
        build = _record if self.meter_class == 1 else _full_class_2
        return build(**self.fields(self.at_limit + self.outward * offset))


def _both_limits(
    case: str,
    name: str,
    meter_class: int,
    limits: tuple[float, float],
    fields: _Fields,
    reference: float = 0.0,
) -> list[_Limit]:
    """A case per finite end of ``limits``, around ``reference``."""
    lower, upper = limits
    return [
        _Limit(
            f"{case}-{side}-class{meter_class}",
            name,
            meter_class,
            reference + end,
            sign,
            fields,
        )
        for side, end, sign in (("lower", lower, -1.0), ("upper", upper, 1.0))
        if math.isfinite(end)
    ]


def _limit_cases() -> list[_Limit]:
    """Every acceptance limit a clause of IEC 61672-3 reads, for both classes."""
    cases: list[_Limit] = []
    for cls in (1, 2):
        for k, f in enumerate(_ACOUSTIC_FREQUENCIES):
            cases += _both_limits(
                f"12-{f}",
                "acoustic_weighting",
                cls,
                _table_3(f, cls),
                lambda v, k=k: {
                    "acoustic_weighting_deviations_db": _placed([0.0, 0.0], k, v)
                },
            )
        count = len(_ELECTRICAL_FREQUENCIES[cls])
        for k, f in enumerate(_ELECTRICAL_FREQUENCIES[cls]):
            cases += _both_limits(
                f"13-{f}",
                "electrical_weighting",
                cls,
                _table_3(f, cls),
                lambda v, k=k, n=count: {
                    "electrical_weighting_deviations_db": {
                        "A": _placed([0.0] * n, k, v),
                        "C": [0.0] * n,
                        "Z": [0.0] * n,
                    }
                },
            )
        cases += _both_limits(
            "14.2",
            "weighting_at_1khz",
            cls,
            _text_limits("5.5.9", cls),
            lambda v: {"weighting_at_1khz_deviations_db": {"C": v, "Z": 0.0}},
        )
        cases += _both_limits(
            "14.3",
            "time_weighting_at_1khz",
            cls,
            _text_limits("5.8.3", cls),
            lambda v: {"time_weighting_at_1khz_deviations_db": {"S": v, "eq": 0.0}},
        )
        cases += _both_limits(
            "15",
            "long_term_stability",
            cls,
            _text_limits("5.14.2", cls),
            lambda v: {"long_term_stability_db": v},
        )
        cases += _both_limits(
            "16",
            "level_linearity",
            cls,
            _text_limits("5.6.5", cls),
            lambda v: {
                "linearity_deviations_db": _placed([0.0] * len(_STEPS_DB), 2, v)
            },
        )
        cases += _both_limits(
            "17",
            "range_linearity",
            cls,
            _text_limits("5.6.5", cls),
            lambda v: {
                "range_linearity_deviations_db": {
                    "17.3": [0.0, 0.0],
                    "17.4": [0.0, 0.0, v],
                }
            },
        )
        for key, durations in _TONEBURST_DURATIONS.items():
            for k, duration in enumerate(durations):
                reference, lower, upper = _table_4(key, duration, cls)
                cases += _both_limits(
                    f"18-{key}-{duration}",
                    "toneburst",
                    cls,
                    (lower, upper),
                    lambda v, key=key, k=k: {
                        "toneburst_responses_db": _toneburst(key, k, v)
                    },
                    reference,
                )
        for k, row in enumerate(ref.IEC61672_1_TABLE_5[2:]):
            cases += _both_limits(
                f"19-{row[0]}-{row[1]}",
                "c_peak",
                cls,
                _limits(row[2 + cls]),
                lambda v, k=k: {
                    "c_peak_differences_db": _placed([3.4, 2.4, 2.4], k, v)
                },
                _number(row[2]),
            )
        cases += _both_limits(
            "20",
            "overload",
            cls,
            _text_limits("5.11.3", cls),
            lambda v: {"overload_difference_db": v},
        )
        cases += _both_limits(
            "21",
            "high_level_stability",
            cls,
            _text_limits("5.15.2", cls),
            lambda v: {"high_level_stability_db": v},
        )
    return cases


_LIMITS = _limit_cases()


@pytest.mark.parametrize("case", _LIMITS, ids=[c.case for c in _LIMITS])
def test_the_verdict_flips_at_every_printed_limit(case: _Limit) -> None:
    """Just inside and on the limit conform; 0,01 dB past it does not."""
    inside = _verify(case.record(-_STEP_DB), case.meter_class)
    at_limit = _verify(case.record(0.0), case.meter_class)
    past = _verify(case.record(_STEP_DB), case.meter_class)
    assert inside.passes
    assert at_limit.passes
    assert not past.requirement(case.name).passes
    assert {clause for clause, _ in past.failed} == {past.requirement(case.name).clause}


def test_the_limit_sweep_reads_every_printed_limit() -> None:
    """Both classes, every limit of 12 to 21 the standard prints finite."""
    per_class = {1: 0, 2: 0}
    for case in _LIMITS:
        per_class[case.meter_class] += 1
    # 12: 2 frequencies, 13: 9 or 8, 14.2, 14.3, 15, 16, 17, 20 and 21: one
    # each, 18: 8 results, 19: 3 signals; two ends each.
    assert per_class == {1: 2 * (2 + 9 + 7 + 8 + 3), 2: 2 * (2 + 8 + 7 + 8 + 3)}


def _b1(requirement: str, frequency: str | None = None) -> float:
    """A maximum of the transcription of Table B.1, its band read as printed."""
    for name, reference, value in ref.IEC61672_1_TABLE_B1:
        if name != requirement:
            continue
        if frequency is None:
            return _number(value)
        f = _number(frequency)
        low_text, high_text = reference.split(", ", 1)[1].split(" to ")
        low = _number(low_text.lstrip(">").split(" ")[0])
        low *= 1000.0 if low_text.endswith("kHz") else 1.0
        high = _number(high_text.split(" ")[0])
        high *= 1000.0 if high_text.endswith("kHz") else 1.0
        above = f > low if low_text.startswith(">") else f >= low
        if above and f <= high:
            return _number(value)
    msg = f"no Table B.1 row for {requirement!r} at {frequency!r}"
    raise LookupError(msg)


_WEIGHTING_B1 = "Frequency weightings A, C, Z"


def _maximum_cases() -> list[tuple[str, str, float, _Fields]]:
    """Every maximum of Table B.1 the verdict reads: (case, name, maximum, fields)."""
    cases: list[tuple[str, str, float, _Fields]] = [
        (
            f"12-{f}",
            "acoustic_weighting",
            _b1(_WEIGHTING_B1, f),
            lambda u, k=k: {
                "acoustic_weighting_uncertainties_db": _placed([0.25, 0.4], k, u)
            },
        )
        for k, f in enumerate(_ACOUSTIC_FREQUENCIES)
    ]
    cases += [
        (
            f"13-{f}",
            "electrical_weighting",
            _b1(_WEIGHTING_B1, f),
            lambda u, k=k: {
                "electrical_weighting_uncertainties_db": {
                    w: _placed([0.15] * 9, k, u) for w in "ACZ"
                }
            },
        )
        for k, f in enumerate(_ELECTRICAL_FREQUENCIES[1])
    ]
    cases += [
        (
            "14.2",
            "weighting_at_1khz",
            _b1("A vs. C or Z at 1 kHz"),
            lambda u: {"weighting_at_1khz_uncertainties_db": {"C": 0.12, "Z": u}},
        ),
        (
            "14.3",
            "time_weighting_at_1khz",
            _b1("F vs. S level at 1 kHz"),
            lambda u: {"time_weighting_at_1khz_uncertainties_db": {"S": u, "eq": 0.12}},
        ),
        (
            "15",
            "long_term_stability",
            _b1("Stability during continuous operation"),
            lambda u: {"long_term_stability_uncertainty_db": u},
        ),
        (
            "16",
            "level_linearity",
            _b1("Level linearity deviation"),
            lambda u: {
                "linearity_uncertainties_db": _placed([0.2] * len(_STEPS_DB), 5, u)
            },
        ),
        (
            "17",
            "range_linearity",
            _b1("Level linearity deviation"),
            lambda u: {
                "range_linearity_uncertainties_db": {
                    "17.3": [u, 0.2],
                    "17.4": [0.2] * 3,
                }
            },
        ),
        (
            "20",
            "overload",
            _b1("Overload indication"),
            lambda u: {"overload_uncertainty_db": u},
        ),
        (
            "21",
            "high_level_stability",
            _b1("High-level stability"),
            lambda u: {"high_level_stability_uncertainty_db": u},
        ),
    ]
    spread = {"F": [0.2] * 3, "S": [0.2] * 2, "E": [0.2] * 3}
    for key, durations in _TONEBURST_DURATIONS.items():
        cases += [
            (
                f"18-{key}-{duration}",
                "toneburst",
                _b1("Toneburst response"),
                lambda u, key=key, k=k: {
                    "toneburst_uncertainties_db": {
                        **spread,
                        key: _placed(spread[key], k, u),
                    }
                },
            )
            for k, duration in enumerate(durations)
        ]
    cases += [
        (
            f"19-{k}",
            "c_peak",
            _b1("C-weighted peak sound levels"),
            lambda u, k=k: {"c_peak_uncertainties_db": _placed([0.3] * 3, k, u)},
        )
        for k in range(3)
    ]
    return cases


_MAXIMA = _maximum_cases()


@pytest.mark.parametrize(
    ("name", "maximum", "fields"),
    [case[1:] for case in _MAXIMA],
    ids=[case[0] for case in _MAXIMA],
)
def test_an_uncertainty_past_its_maximum_makes_the_result_unusable(
    name: str, maximum: float, fields: _Fields
) -> None:
    inside = _verify(_record(**fields(maximum)))
    outside = _verify(_record(**fields(maximum + _STEP_DB)))
    assert inside.requirement(name).passes
    assert outside.requirement(name).unusable
    assert not outside.requirement(name).failed
    assert not outside.passes
    assert "(IEC 61672-3:2013, 4.3)" in outside.statement


def test_time_weighting_maximum_is_wider_than_its_limit() -> None:
    """5.8.3 allows 0,1 dB and Table B.1 0,20 dB; both are read as printed."""
    result = _verify(_record()).requirement("time_weighting_at_1khz")
    first = result.verifications[0]
    assert (first.lower_limit, first.upper_limit) == (-0.1, 0.1)
    assert first.max_uncertainty == pytest.approx(0.20)


def test_toneburst_and_peak_deviations_are_taken_from_the_tables() -> None:
    result = _verify(_record())
    burst = result.requirement("toneburst")
    assert burst.labels[:3] == ("F, 200 ms", "F, 2 ms", "F, 0.25 ms")
    # -27,4 dB measured against the -27,0 dB of Table 4 at 0,25 ms.
    assert burst.verifications[2].deviation == pytest.approx(-0.4)
    peak = result.requirement("c_peak")
    # 3,6 dB measured against the 3,4 dB of Table 5, one cycle at 8 kHz.
    assert peak.verifications[0].deviation == pytest.approx(0.2)
    assert peak.labels[0] == "one cycle, 8 kHz"


# ---------------------------------------------------------------------------
# What a complete test covers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("dropped", "clause"),
    [
        (
            (
                "static_pressures_kpa",
                "air_temperatures_c",
                "relative_humidities_percent",
            ),
            "7",
        ),
        (("calibration_check_initial_db", "calibration_check_adjusted_db"), "10"),
        (("self_noise_microphone_db", "self_noise_electrical_db"), "11"),
        (
            ("acoustic_weighting_deviations_db", "acoustic_weighting_uncertainties_db"),
            "12",
        ),
        (
            (
                "electrical_weighting_deviations_db",
                "electrical_weighting_uncertainties_db",
            ),
            "13",
        ),
        (("long_term_stability_db", "long_term_stability_uncertainty_db"), "15"),
        (
            (
                "linearity_deviations_db",
                "linearity_uncertainties_db",
                "linearity_levels_db",
                *_PROCEDURE,
            ),
            "16",
        ),
        (("toneburst_responses_db", "toneburst_uncertainties_db"), "18"),
        (("high_level_stability_db", "high_level_stability_uncertainty_db"), "21"),
        (
            ("weighting_at_1khz_deviations_db", "weighting_at_1khz_uncertainties_db"),
            "14.2",
        ),
        (
            ("overload_difference_db", "overload_uncertainty_db", "overload_latched"),
            "20",
        ),
    ],
)
def test_a_clause_left_out_is_missing(dropped: tuple[str, ...], clause: str) -> None:
    result = _verify(_record(**dict.fromkeys(dropped)))
    assert result.missing == (clause,)
    assert not result.passes
    assert result.statement.startswith(
        "The periodic tests of IEC 61672-3:2013 are incomplete"
    )
    assert f"clause {clause} (" in result.statement


def test_17_and_19_left_out_and_not_declared_keep_the_test_open() -> None:
    """8.1: a record without 17 and 19 reads as a meter without those features."""
    record = _record(
        range_linearity_deviations_db=None,
        range_linearity_uncertainties_db=None,
        c_peak_differences_db=None,
        c_peak_uncertainties_db=None,
        c_peak_overload_indicated=None,
    )
    result = _verify(record)
    assert result.missing == ()
    assert result.incomplete == ()
    assert result.undeclared == (
        (
            "level_ranges",
            "it is not declared how many level ranges the meter has, and Clause 17 "
            "tests a meter with more than one (8.1)",
        ),
        (
            "c_weighted_peak",
            "it is not declared whether the meter measures C-weighted peak sound "
            "level, which Clause 19 tests (8.1)",
        ),
    )
    assert not result.passes
    assert result.statement.startswith(
        "The periodic tests of IEC 61672-3:2013 are incomplete"
    )
    assert "Clause 17 tests a meter with more than one (8.1)" in result.statement


def test_class_1_needs_c_in_clause_13_and_11_2() -> None:
    rows = {"A": [0.0] * 9, "Z": [0.0] * 9}
    record = _record(
        electrical_weighting_deviations_db=rows,
        electrical_weighting_uncertainties_db={k: [0.2] * 9 for k in rows},
        self_noise_electrical_db={"A": 12.0},
    )
    result = _verify(record)
    assert [clause for clause, _ in result.incomplete] == ["11", "11", "13"]
    assert "lacks frequency weighting C" in result.incomplete[0][1]
    assert "lacks frequency weighting Z" in result.incomplete[1][1]
    assert result.incomplete[2][1] == (
        "frequency weighting C was not tested, and a class 1 meter provides it "
        "(IEC 61672-1 5.1.9, 5.1.10)"
    )


def test_class_1_provides_c_even_when_no_clause_names_it() -> None:
    """A class 1 record that names only A still owes C in 11.2, 13 and 14.2.

    Without Clause 19, whose C-weighted peak would show C as well.
    """
    record = _record(
        electrical_weighting_deviations_db={"A": [0.0] * 9},
        electrical_weighting_uncertainties_db={"A": [0.2] * 9},
        self_noise_electrical_db={"A": 12.0},
        weighting_at_1khz_deviations_db=None,
        weighting_at_1khz_uncertainties_db=None,
        c_peak_differences_db=None,
        c_peak_uncertainties_db=None,
        c_peak_overload_indicated=None,
    )
    result = _verify(record)
    assert result.missing == ("14.2",)
    assert result.incomplete == (
        (
            "11",
            "11.2 lacks frequency weighting C, and it records every weighting "
            "the meter provides",
        ),
        (
            "13",
            "frequency weighting C was not tested, and a class 1 meter provides it "
            "(IEC 61672-1 5.1.9, 5.1.10)",
        ),
    )
    assert not result.passes


def test_a_c_weighted_peak_result_shows_the_meter_provides_c() -> None:
    """IEC 61672-1 5.1.10: a meter with C-weighted peak measures C-weighted Leq."""
    record = _class_2_record(
        c_peak_differences_db=[3.4, 2.4, 2.4],
        c_peak_uncertainties_db=[0.3] * 3,
        c_peak_overload_indicated=False,
    )
    result = _verify(record, 2)
    assert result.missing == ("14.2",)
    assert result.incomplete == (
        (
            "11",
            "11.2 lacks frequency weighting C, and it records every weighting "
            "the meter provides",
        ),
        (
            "13",
            "frequency weighting C was not tested, and the meter measures "
            "C-weighted peak sound level (Clause 19), so it measures C-weighted "
            "time-averaged sound level too (IEC 61672-1 5.1.10)",
        ),
    )
    assert not result.passes


def test_a_weighting_any_clause_names_is_one_the_meter_provides() -> None:
    """Z in 11.2 and 14.2 but not in Clause 13: 8.1 asks for its test there."""
    rows = {"A": [0.0] * 8}
    record = _class_2_record(
        electrical_weighting_deviations_db=rows,
        electrical_weighting_uncertainties_db={"A": [0.2] * 8},
        self_noise_electrical_db={"A": 12.0, "Z": 19.0},
        weighting_at_1khz_deviations_db={"Z": 0.0},
        weighting_at_1khz_uncertainties_db={"Z": 0.1},
    )
    result = _verify(record, 2)
    assert result.incomplete == (
        (
            "13",
            "frequency weighting Z was not tested, and the record shows the "
            "meter provides it (8.1)",
        ),
    )


def test_a_class_2_meter_with_z_owes_the_comparison_of_14_2() -> None:
    record = _class_2_record(
        electrical_weighting_deviations_db={"A": [0.0] * 8, "Z": [0.0] * 8},
        electrical_weighting_uncertainties_db={"A": [0.2] * 8, "Z": [0.2] * 8},
        self_noise_electrical_db={"A": 12.0, "Z": 19.0},
    )
    assert _verify(record, 2).missing == ("14.2",)


def test_a_frequency_not_measured_leaves_clause_13_incomplete() -> None:
    rows = {k: [0.0] * 9 for k in ("A", "C", "Z")}
    rows["C"][0] = _NAN
    spread = {k: [0.2] * 9 for k in rows}
    spread["C"][0] = _NAN
    result = _verify(
        _record(
            electrical_weighting_deviations_db=rows,
            electrical_weighting_uncertainties_db=spread,
        )
    )
    assert result.incomplete == (
        ("13", "C: not measured at 63 Hz, and 13.4 requires it"),
    )
    assert result.missing == ()
    assert result.failed == ()
    assert not result.passes
    assert result.statement.startswith(
        "The periodic tests of IEC 61672-3:2013 are incomplete"
    )
    assert len(result.requirement("electrical_weighting").verifications) == 26


def test_14_2_records_every_weighting_clause_13_tested() -> None:
    record = _record(
        weighting_at_1khz_deviations_db={"C": 0.0},
        weighting_at_1khz_uncertainties_db={"C": 0.1},
    )
    assert _verify(record).incomplete == (
        (
            "14.2",
            "Z was not compared with A at 1 kHz, and 14.1 records every weighting "
            "the meter provides",
        ),
    )


def test_the_displays_14_3_shows_are_toneburst_tested() -> None:
    record = _record(
        toneburst_responses_db={"F": [-1.0, -18.0, -27.0], "E": [-7.0, -27.0, -36.0]},
        toneburst_uncertainties_db={"F": [0.2] * 3, "E": [0.2] * 3},
    )
    result = _verify(record)
    assert result.incomplete == (
        (
            "18",
            "the maximum S-time-weighted response was not measured, and 14.3 "
            "shows the meter provides it (18.2)",
        ),
    )


def test_an_s_toneburst_shows_the_s_display_14_3_compares() -> None:
    """Clause 18 holds S, so 14.1 records S against F at 1 kHz (8.1)."""
    record = _record(
        time_weighting_at_1khz_deviations_db=None,
        time_weighting_at_1khz_uncertainties_db=None,
        overload_difference_db=None,
        overload_uncertainty_db=None,
        overload_latched=None,
    )
    result = _verify(record, pattern_approval_public=True)
    assert result.missing == ("14.3",)
    assert not result.passes
    assert "clause 14.3 (time weightings at 1 kHz) was not measured" in (
        result.statement
    )


def test_an_overload_test_shows_the_time_averaged_display() -> None:
    """20.1 tests only a meter that displays time-averaged sound level."""
    record = _class_2_record(
        overload_difference_db=0.2,
        overload_uncertainty_db=0.2,
        overload_latched=True,
    )
    assert _verify(record, 2).missing == ("14.3",)
    compared = _class_2_record(
        overload_difference_db=0.2,
        overload_uncertainty_db=0.2,
        overload_latched=True,
        time_weighting_at_1khz_deviations_db={"S": 0.0},
        time_weighting_at_1khz_uncertainties_db={"S": 0.1},
        toneburst_responses_db={"F": [-1.0, -18.0, -27.0], "S": [-7.4, -27.0]},
        toneburst_uncertainties_db={"F": [0.2] * 3, "S": [0.2] * 2},
    )
    result = _verify(compared, 2)
    assert result.missing == ()
    assert result.incomplete == (
        (
            "14.3",
            "the time-averaged indication was not compared with F at 1 kHz, and "
            "Clause 20 shows the meter displays it, as 20.1 tests the overload "
            "indication only on such a meter",
        ),
        (
            "18",
            "the sound exposure level response was not measured, and the meter "
            "displays time-averaged sound level, from which it is calculated "
            "(18.2)",
        ),
    )


def test_a_sound_exposure_toneburst_shows_no_time_averaged_display() -> None:
    """An integrating meter need not display Leq (IEC 61672-1 5.1.9)."""
    record = _class_2_record(
        toneburst_responses_db={"F": [-1.0, -18.0, -27.0], "E": [-7.0, -27.0, -36.0]},
        toneburst_uncertainties_db={"F": [0.2] * 3, "E": [0.2] * 3},
    )
    result = _verify(
        record, 2, features=_basic(time_averaged=None, sound_exposure_level=None)
    )
    assert result.missing == ()
    assert result.incomplete == ()
    assert [name for name, _ in result.undeclared] == ["time_averaged"]
    declared = _verify(record, 2, features=_basic(sound_exposure_level=True))
    assert declared.passes


@pytest.mark.parametrize(
    ("shows", "missing"),
    [({"eq": 0.0}, ("20",)), ({"S": 0.0}, ())],
    ids=["time-averaged", "S"],
)
def test_clause_20_is_owed_by_the_time_averaged_display_only(
    shows: dict[str, float], missing: tuple[str, ...]
) -> None:
    record = _class_2_record(
        time_weighting_at_1khz_deviations_db=shows,
        time_weighting_at_1khz_uncertainties_db=dict.fromkeys(shows, 0.1),
    )
    assert _verify(record, 2).missing == missing


# ---------------------------------------------------------------------------
# The extent of Clauses 16 and 17 (16.3, 17.3, 17.4)
# ---------------------------------------------------------------------------


def _linearity(levels: list[float], **over: Any) -> dict[str, Any]:
    """The fields of Clause 16 for these steps, every result 0,1 dB."""
    return {
        "linearity_deviations_db": [0.1] * len(levels),
        "linearity_uncertainties_db": [0.2] * len(levels),
        "linearity_levels_db": levels,
        **over,
    }


def _16_gaps(result: metrology.SoundLevelMeterPeriodicVerification) -> list[str]:
    return [what for clause, what in result.incomplete if clause == "16"]


def test_the_steps_of_16_3_complete_the_clause() -> None:
    result = _verify(_record())
    assert _16_gaps(result) == []
    assert result.requirement("level_linearity").checks == (
        (
            "no overload or under-range indication within the linear operating "
            "range (16.4)",
            True,
        ),
    )


def test_one_step_of_clause_16_does_not_pass() -> None:
    """A single result, without the levels, reads as no extent at all."""
    record = _record(
        linearity_deviations_db=[0.0],
        linearity_uncertainties_db=[0.2],
        linearity_levels_db=None,
    )
    result = _verify(record, pattern_approval_public=True)
    assert not result.passes
    assert _16_gaps(result) == [
        "the record does not give 'linearity_levels_db', and without it it cannot "
        "show that the steps rise from the starting point up to the first "
        "indication of overload and fall to the first indication of under-range "
        "(16.3)"
    ]
    assert result.statement.startswith(
        "The periodic tests of IEC 61672-3:2013 are incomplete: 16: the record "
        "does not give"
    )


def test_a_record_without_the_extent_of_clause_16_names_what_it_lacks() -> None:
    record = _record(**dict.fromkeys(_PROCEDURE))
    gaps = _16_gaps(_verify(record))
    assert len(gaps) == 1
    assert gaps[0].startswith(
        "the record does not give 'linear_operating_range_db', "
        "'linearity_starting_point_db', 'linearity_overload_level_db' and "
        "'linearity_under_range_level_db', and without them"
    )


def test_one_step_at_the_starting_point_covers_nothing_around_it() -> None:
    result = _verify(_record(**_linearity([94.0])))
    assert not result.passes
    assert _16_gaps(result) == [
        "the steps go from 94 dB to the first indication of overload at 121 dB, "
        "and 16.3 rises by 5 dB at most until within 5 dB of the upper boundary "
        "of the linear operating range, 120 dB, and by 1 dB from there up to the "
        "first indication of overload",
        "the steps go from 94 dB to the first indication of under-range at 54 dB, "
        "and 16.3 falls by 5 dB at most until within 5 dB of the lower boundary "
        "of the linear operating range, 55 dB, and by 1 dB from there down to "
        "the first indication of under-range",
    ]


@pytest.mark.parametrize(
    ("dropped", "gap"),
    [
        (99.0, "the steps go from 94 dB to 104 dB"),
        (
            120.0,
            "the steps go from 119 dB to the first indication of overload at 121 dB",
        ),
        (59.0, "the steps go from 64 dB to 58 dB"),
        (
            55.0,
            "the steps go from 56 dB to the first indication of under-range at 54 dB",
        ),
        (
            94.0,
            "no step is at the starting point of 94 dB the instruction manual "
            "gives (16.2)",
        ),
    ],
    ids=[
        "coarse",
        "fine to overload",
        "into the fine steps",
        "fine to under-range",
        "starting point",
    ],
)
def test_a_step_left_out_of_16_3_leaves_the_clause_incomplete(
    dropped: float, gap: str
) -> None:
    levels = [level for level in _STEPS_DB if level != dropped]
    result = _verify(_record(**_linearity(levels)))
    gaps = _16_gaps(result)
    assert len(gaps) == 1
    assert gaps[0].startswith(gap)
    assert not result.passes


def test_steps_finer_than_16_3_and_in_any_order_are_complete() -> None:
    levels = [float(level) for level in range(120, 54, -1)]
    result = _verify(_record(**_linearity(levels)))
    assert _16_gaps(result) == []
    shuffled = [*_STEPS_DB[7:], *_STEPS_DB[:7]]
    assert _16_gaps(_verify(_record(**_linearity(shuffled)))) == []


def test_the_5_db_steps_stop_within_5_db_of_the_upper_boundary() -> None:
    """At 115 dB, 5 dB below the 120 dB boundary, 16.3 steps by 1 dB; at 114, by 5."""
    down = list(_STEPS_DB[7:])
    wide = [94.0, 99.0, 104.0, 109.0, 114.0, 119.0, 120.0]
    assert _16_gaps(_verify(_record(**_linearity([*wide, *down])))) == []
    within = [94.0, 99.0, 104.0, 109.0, 114.0, 115.0, 120.0]
    gaps = _16_gaps(_verify(_record(**_linearity([*within, *down]))))
    assert len(gaps) == 1
    assert gaps[0].startswith("the steps go from 115 dB to 120 dB")


def test_the_5_db_steps_stop_within_5_db_of_the_lower_boundary() -> None:
    """At 60 dB, 5 dB above the 55 dB boundary, 16.3 steps by 1 dB; at 61, by 5."""
    up = list(_STEPS_DB[:7])
    wide = [89.0, 84.0, 79.0, 74.0, 69.0, 64.0, 61.0, 56.0, 55.0]
    assert _16_gaps(_verify(_record(**_linearity([*up, *wide])))) == []
    within = [89.0, 84.0, 79.0, 74.0, 69.0, 65.0, 60.0, 55.0]
    gaps = _16_gaps(_verify(_record(**_linearity([*up, *within]))))
    assert len(gaps) == 1
    assert gaps[0].startswith("the steps go from 60 dB to 55 dB")


@pytest.mark.parametrize(
    ("step", "wider", "gap"),
    [
        (99.0, 99.1, "the steps go from 94 dB to 99.1 dB"),
        (58.0, 57.9, "the steps go from 59 dB to 57.9 dB"),
    ],
    ids=["5.1 dB where 16.3 steps by 5", "1.1 dB where 16.3 steps by 1"],
)
def test_a_step_0_1_db_wider_than_16_3_leaves_the_clause_incomplete(
    step: float, wider: float, gap: str
) -> None:
    """The step sizes of 16.3 are limits, with no allowance beyond rounding."""
    levels = [wider if level == step else level for level in _STEPS_DB]
    result = _verify(_record(**_linearity(levels)))
    gaps = _16_gaps(result)
    assert len(gaps) == 1
    assert gaps[0].startswith(gap)
    assert not result.passes


def test_an_overload_inside_the_linear_operating_range_fails_clause_16() -> None:
    """16.4 with IEC 61672-1 5.6.10: the range is free of both indications."""
    record = _record(
        **_linearity([level for level in _STEPS_DB if level != 120.0]),
        linearity_overload_level_db=120.0,
    )
    result = _verify(record, pattern_approval_public=True)
    check = (
        "no overload or under-range indication within the linear operating range (16.4)"
    )
    assert result.failed == (("16", check),)
    assert result.requirement("level_linearity").failure_reason(check) == (
        "an indication of overload or under-range was displayed within the linear "
        "operating range stated in the Instruction Manual"
    )
    assert _16_gaps(result) == []
    under = _record(
        **_linearity([level for level in _STEPS_DB if level != 55.0]),
        linearity_under_range_level_db=55.0,
    )
    assert _verify(under).failed == (("16", check),)


@pytest.mark.parametrize(
    ("fields", "match"),
    [
        ({"linear_operating_range_db": [120.0, 55.0]}, "lower boundary below"),
        ({"linear_operating_range_db": [55.0, 55.0]}, "lower boundary below"),
        (
            {"linear_operating_range_db": [55.0]},
            "'linear_operating_range_db' must hold 2 results",
        ),
        (
            {"linearity_starting_point_db": 125.0},
            "starting point of 125 dB lies outside",
        ),
        (
            {"linearity_overload_level_db": 120.0},
            "at or above the first indication of overload",
        ),
        (
            {"linearity_under_range_level_db": 60.0},
            "at or below the first indication of under-range",
        ),
        (
            {"linearity_under_range_level_db": 55.0},
            "at or below the first indication of under-range",
        ),
        (
            {
                "linearity_deviations_db": None,
                "linearity_uncertainties_db": None,
                "linearity_levels_db": None,
            },
            "describe the steps of Clause 16, whose results are missing",
        ),
    ],
    ids=[
        "reversed",
        "empty",
        "one boundary",
        "start outside",
        "at overload",
        "past under-range",
        "at under-range",
        "no results",
    ],
)
def test_the_record_refuses_a_contradicted_procedure_of_16(
    fields: dict[str, Any], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        _record(**fields)


def _17(rows: dict[str, list[float]]) -> dict[str, Any]:
    """The fields of Clause 17 for these readings, each with 0,2 dB."""
    return {
        "range_linearity_deviations_db": rows,
        "range_linearity_uncertainties_db": {
            key: [_NAN if math.isnan(v) else 0.2 for v in row]
            for key, row in rows.items()
        },
    }


def _17_gaps(result: metrology.SoundLevelMeterPeriodicVerification) -> list[str]:
    return [what for clause, what in result.incomplete if clause == "17"]


def test_17_4_on_one_other_range_does_not_pass_a_meter_with_three_ranges() -> None:
    result = _verify(_record(**_17({"17.4": [0.1, 0.0]})), pattern_approval_public=True)
    assert not result.passes
    assert _17_gaps(result) == [
        "17.3 was not recorded: the reference sound level held on every other "
        "level range where it is displayed",
        "the record holds 1 of the 2 level ranges besides the reference one, and "
        "17.3 and 17.4 test every one",
    ]
    assert "17: the record holds 1 of the 2 level ranges" in result.statement


def test_17_4_on_every_range_and_17_3_on_every_other_complete_clause_17() -> None:
    result = _verify(_record(**_17({"17.3": [0.1, -0.1], "17.4": [0.1, 0.0, 0.2]})))
    assert _17_gaps(result) == []
    assert result.requirement("range_linearity").labels == (
        "17.3, range 1",
        "17.3, range 2",
        "17.4, reference range",
        "17.4, range 1",
        "17.4, range 2",
    )
    two = _verify(
        _record(**_17({"17.3": [0.1], "17.4": [0.1, 0.0]})),
        features=metrology.SoundLevelMeterFeatures(level_ranges=2),
    )
    assert two.passes


def test_17_4_is_owed_on_the_reference_level_range_too() -> None:
    """IEC 61672-3:2013 17.4 reads "for each level range", the reference one too.

    17.3 has nothing to read there: the reference sound level 17.2 set is
    the anticipated level, a deviation of zero by construction (IEC 61672-1
    5.6.3). 17.4 sets a level 17.2 did not, 5 dB above the first
    indication of under-range, so the reference range owes that reading.
    """
    without = _verify(
        _record(**_17({"17.3": [0.1, -0.1], "17.4": [_NAN, 0.0, 0.2]})),
        pattern_approval_public=True,
    )
    assert not without.passes
    assert _17_gaps(without) == [
        "17.4 was not measured on the reference level range, and it tests every "
        "level range, the reference one included"
    ]
    assert "17.4, reference range" not in without.requirement("range_linearity").labels
    assert "17: 17.4 was not measured on the reference level range" in (
        without.statement
    )
    with_it = _verify(
        _record(**_17({"17.3": [0.1, -0.1], "17.4": [0.3, 0.0, 0.2]})),
        pattern_approval_public=True,
    )
    assert with_it.passes
    reading = with_it.requirement("range_linearity")
    k = reading.labels.index("17.4, reference range")
    assert reading.verifications[k].deviation == pytest.approx(0.3)


def test_17_4_past_its_limit_on_the_reference_level_range_fails_the_clause() -> None:
    result = _verify(_record(**_17({"17.3": [0.1, -0.1], "17.4": [0.9, 0.0, 0.2]})))
    assert result.failed == (("17", "17.4, reference range"),)


def test_17_3_reads_only_where_the_reference_level_is_displayed() -> None:
    shown_once = _verify(
        _record(**_17({"17.3": [_NAN, -0.1], "17.4": [0.1, 0.0, 0.2]}))
    )
    assert _17_gaps(shown_once) == []
    assert shown_once.requirement("range_linearity").labels == (
        "17.3, range 2",
        "17.4, reference range",
        "17.4, range 1",
        "17.4, range 2",
    )
    nowhere = _verify(_record(**_17({"17.3": [_NAN, _NAN], "17.4": [0.1, 0.0, 0.2]})))
    assert nowhere.passes


def test_17_4_left_out_on_a_range_leaves_the_clause_incomplete() -> None:
    result = _verify(_record(**_17({"17.3": [0.1, -0.1], "17.4": [0.1, 0.0, _NAN]})))
    assert _17_gaps(result) == [
        "17.4 was not measured on range 2, and it tests every level range, the "
        "reference one included"
    ]
    both = _verify(_record(**_17({"17.3": [0.1, -0.1], "17.4": [_NAN, 0.0, _NAN]})))
    assert _17_gaps(both) == [
        "17.4 was not measured on the reference level range and range 2, and it "
        "tests every level range, the reference one included"
    ]
    missing = _verify(_record(**_17({"17.3": [0.1, -0.1]})))
    assert _17_gaps(missing) == [
        "17.4 was not recorded: 5 dB above the first indication of under-range "
        "on every level range, the reference one included"
    ]


def test_the_number_of_level_ranges_stays_open_until_declared() -> None:
    result = metrology.verify_sound_level_meter_periodic(1, _record())
    assert result.undeclared == (
        (
            "level_ranges",
            "it is not declared how many level ranges the meter has, and 17.4 "
            "tests every one and 17.3 every one besides the reference level range",
        ),
    )
    assert _17_gaps(result) == []
    assert not result.passes


def test_more_readings_than_level_ranges_is_refused() -> None:
    features = metrology.SoundLevelMeterFeatures(level_ranges=2)
    for record in (_record(), _record(**_17({"17.4": [0.1, 0.0, 0.2]}))):
        with pytest.raises(
            ValueError, match="covers 2 level ranges besides the reference one"
        ):
            _verify(record, features=features)


@pytest.mark.parametrize(
    ("rows", "match"),
    [
        (
            {"17.3": [0.1, 0.2], "17.4": [0.0, 0.2]},
            "holds one value per level range in '17.4', the reference one first, "
            "and one per level range besides the reference one in '17.3'; got 2 "
            "and 2",
        ),
        ({"17.3": [0.1], "17.4": [0.0, 0.2, 0.3]}, "; got 3 and 1"),
        ({"17.3": [_NAN, _NAN]}, "holds no measured value"),
        ({"17.4": [_NAN, _NAN]}, "holds no measured value"),
        ({"17.5": [0.0]}, "must be a non-empty mapping keyed by '17.3', '17.4'"),
        ([0.1, 0.2], "must be a mapping keyed by"),
    ],
    ids=[
        "17.4 without the reference range",
        "17.4 on too many",
        "17.3 nowhere",
        "17.4 nowhere",
        "unknown key",
        "flat",
    ],
)
def test_the_record_refuses_unreadable_rows_of_clause_17(
    rows: object, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        _record(
            range_linearity_deviations_db=rows,
            range_linearity_uncertainties_db=rows,
        )


# ---------------------------------------------------------------------------
# The meter's optional features (8.1)
# ---------------------------------------------------------------------------

#: What the verdict says when a feature is declared present and its tests are
#: left out of the basic record: the clauses missing and the gaps found.
_DECLARED_PRESENT: list[tuple[dict[str, int], tuple[str, ...], list[str]]] = [
    ({"level_ranges": 2}, ("17",), []),
    ({"c_weighted_peak": True, "c_weighting": True}, ("14.2", "19"), ["11", "13"]),
    ({"c_weighting": True}, ("14.2",), ["11", "13"]),
    ({"z_weighting": True}, ("14.2",), ["11", "13"]),
    ({"s_time_weighting": True}, ("14.3",), ["18"]),
    ({"time_averaged": True}, ("14.3", "20"), ["18"]),
    ({"sound_exposure_level": True}, (), ["18"]),
]


@pytest.mark.parametrize(
    ("declared", "missing", "gaps"),
    _DECLARED_PRESENT,
    ids=[next(iter(d)) for d, _, _ in _DECLARED_PRESENT],
)
def test_a_feature_declared_present_owes_its_tests(
    declared: dict[str, int], missing: tuple[str, ...], gaps: list[str]
) -> None:
    result = _verify(_class_2_record(), 2, features=_basic(**declared))
    assert result.missing == missing
    assert [clause for clause, _ in result.incomplete] == gaps
    assert result.undeclared == ()
    assert not result.passes
    for clause in (*missing, *gaps):
        assert clause not in {c for c, _ in result.not_applicable}


def test_a_declared_feature_is_the_reason_the_verdict_gives() -> None:
    result = _verify(
        _class_2_record(), 2, features=_basic(z_weighting=True, s_time_weighting=True)
    )
    assert (
        "13",
        "frequency weighting Z was not tested, and the features declared for the "
        "meter include it",
    ) in result.incomplete
    assert (
        "18",
        "the maximum S-time-weighted response was not measured, and the features "
        "declared for the meter include it (18.2)",
    ) in result.incomplete


@pytest.mark.parametrize(
    ("clause", "present"),
    [
        ("17", [{"level_ranges": 2}]),
        ("19", [{"c_weighted_peak": True, "c_weighting": True}]),
        ("20", [{"time_averaged": True}]),
        ("14.3", [{"s_time_weighting": True}, {"time_averaged": True}]),
        ("14.2", [{"c_weighting": True}, {"z_weighting": True}]),
    ],
    ids=["ranges", "peak", "time-averaged", "S and Leq", "C and Z"],
)
def test_a_feature_declared_absent_takes_its_clause_out(
    clause: str, present: list[dict[str, int]]
) -> None:
    """Declared absent, the clause is not applicable; declared present, it is owed."""
    result = _verify(_class_2_record(), 2, features=_BASIC)
    assert clause in {c for c, _ in result.not_applicable}
    assert clause not in result.missing
    assert result.passes
    for declared in present:
        owed = _verify(_class_2_record(), 2, features=_basic(**declared))
        assert clause not in {c for c, _ in owed.not_applicable}
        assert clause in owed.missing


def test_not_applicable_says_why() -> None:
    result = _verify(_class_2_record(), 2, features=_BASIC)
    assert result.not_applicable == (
        ("14.2", "the meter provides no frequency weighting but A (14.1)"),
        (
            "14.3",
            "the meter displays neither S-time-weighted nor time-averaged sound "
            "level (14.1)",
        ),
        ("17", "the meter has one level range (17.1)"),
        ("19", "the meter does not measure C-weighted peak sound level (8.1)"),
        ("20", "the meter does not display time-averaged sound level (20.1)"),
    )


@pytest.mark.parametrize(
    "name",
    [
        "c_weighting",
        "z_weighting",
        "s_time_weighting",
        "time_averaged",
        "sound_exposure_level",
        "level_ranges",
    ],
)
def test_a_feature_neither_declared_nor_shown_keeps_the_test_open(name: str) -> None:
    result = _verify(_class_2_record(), 2, features=_basic(**{name: None}))
    assert [feature for feature, _ in result.undeclared] == [name]
    assert result.missing == ()
    assert result.incomplete == ()
    assert not result.passes
    assert result.undeclared[0][1] in result.statement


def test_the_f_time_weighting_of_an_integrating_meter() -> None:
    """IEC 61672-1 5.1.9: a meter that only integrates need not have F."""
    record = _class_2_record(
        toneburst_responses_db={"E": [-7.0, -27.0, -36.0]},
        toneburst_uncertainties_db={"E": [0.2] * 3},
    )
    unsaid = _verify(record, 2, features=_basic(sound_exposure_level=True))
    assert [name for name, _ in unsaid.undeclared] == ["f_time_weighting"]
    without = _verify(
        record, 2, features=_basic(sound_exposure_level=True, f_time_weighting=False)
    )
    assert without.passes
    assert (
        "14.3",
        "the meter has no F time weighting to compare the other displays with (14.3)",
    ) in without.not_applicable
    with_f = _verify(
        record, 2, features=_basic(sound_exposure_level=True, f_time_weighting=True)
    )
    assert with_f.incomplete == (
        (
            "18",
            "the maximum F-time-weighted response was not measured, and the "
            "features declared for the meter include it (18.2)",
        ),
    )


def test_a_time_averaged_display_settles_the_sound_exposure_level() -> None:
    """18.2 calculates it from Leq, so the question does not stay open."""
    result = _verify(
        _class_2_record(),
        2,
        features=_basic(time_averaged=True, sound_exposure_level=None),
    )
    assert "sound_exposure_level" not in {name for name, _ in result.undeclared}
    assert (
        "18",
        "the sound exposure level response was not measured, and the meter "
        "displays time-averaged sound level, from which it is calculated (18.2)",
    ) in result.incomplete


@pytest.mark.parametrize(
    ("declared", "fields", "match"),
    [
        (
            {"level_ranges": 1},
            {
                "range_linearity_deviations_db": {"17.4": [0.1, 0.0]},
                "range_linearity_uncertainties_db": {"17.4": [0.2, 0.2]},
            },
            "'features.level_ranges' is 1, but Clause 17 shows it",
        ),
        (
            {"c_weighted_peak": False},
            {
                "c_peak_differences_db": [3.4, 2.4, 2.4],
                "c_peak_uncertainties_db": [0.3] * 3,
                "c_peak_overload_indicated": False,
            },
            "'features.c_weighted_peak' is False, but Clause 19 shows it",
        ),
        (
            {"time_averaged": False},
            {
                "time_weighting_at_1khz_deviations_db": {"eq": 0.0},
                "time_weighting_at_1khz_uncertainties_db": {"eq": 0.1},
            },
            "'features.time_averaged' is False, but 14.3 shows",
        ),
        (
            {"s_time_weighting": False},
            {
                "toneburst_responses_db": {
                    "F": [-1.0, -18.0, -27.0],
                    "S": [-7.4, -27.0],
                },
                "toneburst_uncertainties_db": {"F": [0.2] * 3, "S": [0.2] * 2},
            },
            "'features.s_time_weighting' is False, but Clause 18 shows",
        ),
        (
            {"z_weighting": False},
            {"self_noise_electrical_db": {"A": 12.0, "Z": 19.0}},
            "'features.z_weighting' is False, but the record shows",
        ),
        (
            {"f_time_weighting": False, "sound_exposure_level": True},
            {},
            "'features.f_time_weighting' is False, but Clause 18 shows",
        ),
        (
            {},
            {
                "toneburst_responses_db": {
                    "F": [-1.0, -18.0, -27.0],
                    "E": [-7.0, -27.0, -36.0],
                },
                "toneburst_uncertainties_db": {"F": [0.2] * 3, "E": [0.2] * 3},
            },
            "the record holds sound exposure level toneburst responses",
        ),
    ],
    ids=["ranges", "peak", "time-averaged", "S", "Z", "F", "exposure"],
)
def test_a_declaration_the_record_contradicts_is_refused(
    declared: dict[str, int], fields: dict[str, Any], match: str
) -> None:
    record = _class_2_record(**fields)
    features = _basic(**declared)
    with pytest.raises(ValueError, match=match):
        _verify(record, 2, features=features)


def test_class_1_cannot_be_declared_without_c() -> None:
    features = metrology.SoundLevelMeterFeatures(c_weighting=False)
    record = _record()
    with pytest.raises(
        ValueError, match="a class 1 meter provides frequency weighting C"
    ):
        _verify(record, 1, features=features)


@pytest.mark.parametrize(
    ("declared", "match"),
    [
        ({"c_weighted_peak": True, "c_weighting": False}, "IEC 61672-1 5.1.10"),
        ({"s_time_weighting": True, "f_time_weighting": False}, "IEC 61672-1 5.1.9"),
        ({"z_weighting": "yes"}, "'z_weighting' must be True, False or None"),
    ],
    ids=["peak without C", "S without F", "not a bool"],
)
def test_the_features_refuse_a_meter_the_standard_rules_out(
    declared: dict[str, Any], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        metrology.SoundLevelMeterFeatures(**declared)


def test_a_meter_without_c_measures_no_c_weighted_peak() -> None:
    """IEC 61672-1 5.1.10: Clause 19 is not applicable, not an open question."""
    result = _verify(_class_2_record(), 2, features=_basic(c_weighted_peak=None))
    assert result.undeclared == ()
    assert result.passes
    assert (
        "19",
        "the meter provides no frequency weighting C, which a meter that measures "
        "C-weighted peak sound level provides (IEC 61672-1 5.1.10)",
    ) in result.not_applicable
    open_c = _verify(
        _class_2_record(), 2, features=_basic(c_weighting=None, c_weighted_peak=None)
    )
    assert [name for name, _ in open_c.undeclared] == ["c_weighting", "c_weighted_peak"]


def test_a_meter_without_f_has_no_s() -> None:
    """IEC 61672-1 5.1.9: an integrating meter declared without F owes no S."""
    record = _class_2_record(
        toneburst_responses_db={"E": [-7.0, -27.0, -36.0]},
        toneburst_uncertainties_db={"E": [0.2] * 3},
    )
    features = _basic(
        f_time_weighting=False, s_time_weighting=None, sound_exposure_level=True
    )
    result = _verify(record, 2, features=features)
    assert result.undeclared == ()
    assert result.passes


@pytest.mark.parametrize(
    ("declared", "fields", "match"),
    [
        (
            {"c_weighted_peak": None},
            {
                "c_peak_differences_db": [3.4, 2.4, 2.4],
                "c_peak_uncertainties_db": [0.3] * 3,
                "c_peak_overload_indicated": False,
            },
            "'features.c_weighting' is False, and a meter that measures C-weighted "
            "peak sound level provides frequency weighting C \\(IEC 61672-1 "
            "5.1.10\\), but Clause 19 shows it",
        ),
        (
            {
                "f_time_weighting": False,
                "s_time_weighting": None,
                "sound_exposure_level": True,
            },
            {
                "toneburst_responses_db": {
                    "S": [-7.4, -27.0],
                    "E": [-7.0, -27.0, -36.0],
                },
                "toneburst_uncertainties_db": {"S": [0.2] * 2, "E": [0.2] * 3},
            },
            "'features.f_time_weighting' is False, and a meter with the S time "
            "weighting has the F time weighting too \\(IEC 61672-1 5.1.9\\), but "
            "Clause 18 shows",
        ),
    ],
    ids=["peak without C", "S without F"],
)
def test_a_feature_the_declaration_takes_away_cannot_be_shown(
    declared: dict[str, Any], fields: dict[str, Any], match: str
) -> None:
    record = _class_2_record(**fields)
    features = _basic(**declared)
    with pytest.raises(ValueError, match=match):
        _verify(record, 2, features=features)


@pytest.mark.parametrize(
    "declared",
    [
        {
            "f_time_weighting": False,
            "time_averaged": False,
            "sound_exposure_level": False,
        },
        {
            "f_time_weighting": False,
            "s_time_weighting": False,
            "time_averaged": False,
            "sound_exposure_level": False,
        },
    ],
    ids=["S implied", "S declared"],
)
def test_a_meter_that_indicates_nothing_is_refused(declared: dict[str, bool]) -> None:
    """IEC 61672-1 5.1.9: F, a time-averaged display or sound exposure level."""
    with pytest.raises(ValueError, match="cannot all be False"):
        metrology.SoundLevelMeterFeatures(**declared)


@pytest.mark.parametrize("count", [0, -2, 1.5, True, "3", np.float64(2.0)], ids=repr)
def test_the_number_of_level_ranges_is_a_whole_number_from_1(count: object) -> None:
    with pytest.raises(ValueError, match="'level_ranges' must be the number"):
        metrology.SoundLevelMeterFeatures(level_ranges=count)  # type: ignore[arg-type]


def test_the_number_of_level_ranges_is_held_as_an_int() -> None:
    features = metrology.SoundLevelMeterFeatures(level_ranges=np.int64(3))
    assert type(features.level_ranges) is int
    assert features.level_ranges == 3


def test_the_features_are_frozen_and_hold_plain_booleans() -> None:
    features = metrology.SoundLevelMeterFeatures(z_weighting=np.True_)
    assert features.z_weighting is True
    with pytest.raises(dataclasses.FrozenInstanceError):
        features.z_weighting = False  # type: ignore[misc]
    result = _verify(_record(), features=features)
    assert result.features is features
    unsaid = metrology.verify_sound_level_meter_periodic(1, _record())
    assert unsaid.features == metrology.SoundLevelMeterFeatures()


@pytest.mark.parametrize(
    ("dropped", "what"),
    [
        ("self_noise_microphone_db", "11.1, with the microphone installed"),
        ("self_noise_electrical_db", "11.2, with the electrical input-signal device"),
    ],
)
def test_one_half_of_clause_11_left_out_is_incomplete(dropped: str, what: str) -> None:
    result = _verify(_record(**{dropped: None}))
    assert result.missing == ()
    assert result.incomplete == (("11", f"{what}, was not recorded"),)
    assert not result.passes


def test_a_duration_not_measured_leaves_clause_18_incomplete() -> None:
    record = _record(
        toneburst_responses_db={
            "F": [-1.0, -18.0, _NAN],
            "S": [-7.4, -27.0],
            "E": [-7.0, -27.0, -36.0],
        },
        toneburst_uncertainties_db={
            "F": [0.2, 0.2, _NAN],
            "S": [0.2] * 2,
            "E": [0.2] * 3,
        },
    )
    assert _verify(record).incomplete == (
        ("18", "F: not measured at 0.25 ms, and 18.5 to 18.7 require it"),
    )


def test_one_environmental_reading_is_short_of_7_2() -> None:
    record = _record(
        static_pressures_kpa=[100.0],
        air_temperatures_c=[23.0, 23.0],
        relative_humidities_percent=[50.0, 50.0],
    )
    assert [c for c, _ in _verify(record).incomplete] == ["7"]


def test_tests_outside_the_conditions_of_7_1_are_not_valid() -> None:
    record = _record(air_temperatures_c=[23.0, 26.5])
    result = _verify(record)
    assert result.conditions_outside == ("air_temperatures_c = 26.5, outside 20 to 26",)
    assert not result.passes
    assert result.statement.startswith(
        "The periodic tests of IEC 61672-3:2013 were not performed within"
    )


@pytest.mark.parametrize(
    ("fields", "outcome"),
    [
        ({"long_term_stability_db": 0.2}, "failed"),
        ({"high_level_stability_uncertainty_db": 0.2}, "unusable"),
        ({"overload_latched": None}, "incomplete"),
    ],
    ids=["failure", "unusable", "incomplete"],
)
def test_conditions_outside_7_1_come_before_what_the_results_say(
    fields: dict[str, Any], outcome: str
) -> None:
    """A test outside 7.1 is no periodic test, so neither 22 t) nor 4.3 is said."""
    record = _record(air_temperatures_c=[23.0, 26.5], **fields)
    result = _verify(record, pattern_approval_public=True, corrections_in_manual=True)
    assert getattr(result, outcome)
    assert result.conditions_outside == ("air_temperatures_c = 26.5, outside 20 to 26",)
    assert not result.passes
    assert result.statement.startswith(
        "The periodic tests of IEC 61672-3:2013 were not performed within"
    )
    assert "did not conform" not in result.statement
    assert "4.3" not in result.statement


def test_the_conditions_of_7_1_are_inclusive() -> None:
    record = _record(
        static_pressures_kpa=[80.0, 105.0],
        air_temperatures_c=[20.0, 26.0],
        relative_humidities_percent=[25.0, 70.0],
    )
    assert _verify(record).passes


def test_an_overload_during_the_peak_test_fails_clause_19() -> None:
    result = _verify(_record(c_peak_overload_indicated=True))
    assert result.failed == (("19", "no overload indication (19.3, 19.5)"),)
    assert "caused an indication of an overload condition" in result.statement


def test_an_indicator_that_does_not_latch_fails_clause_20() -> None:
    result = _verify(_record(overload_latched=False))
    assert result.failed == (("20", "latching of the overload indicator (20.5)"),)
    assert "did not latch on" in result.statement


def test_checks_not_recorded_leave_the_clause_incomplete() -> None:
    result = _verify(_record(c_peak_overload_indicated=None, overload_latched=None))
    assert [c for c, _ in result.incomplete] == ["19", "20"]


def test_a_peak_signal_not_measured_leaves_clause_19_incomplete() -> None:
    record = _record(
        c_peak_differences_db=[3.4, _NAN, 2.4],
        c_peak_uncertainties_db=[0.3, _NAN, 0.3],
    )
    result = _verify(record)
    assert result.incomplete == (
        ("19", "not measured for positive half cycle, 500 Hz, and 19.1 requires it"),
    )


def test_a_failure_outweighs_an_unusable_result_in_the_statement() -> None:
    record = _record(
        long_term_stability_db=0.2, high_level_stability_uncertainty_db=0.2
    )
    result = _verify(record)
    assert result.unusable == (("21", "final - initial"),)
    assert result.failed == (("15", "final - initial"),)
    assert result.statement.startswith(_statement(ref.IEC61672_3_STATEMENT_T, 1))


# ---------------------------------------------------------------------------
# The manufacturer's correction data (4.4)
# ---------------------------------------------------------------------------

#: 4.4 as the record gives it: the 8 kHz result of Clause 12 with a total
#: uncertainty of 0,85 dB, past the 0,70 dB of Table B.1 only by the
#: manufacturer's correction data.
_OVER_BY_CORRECTIONS: dict[str, Any] = {
    "acoustic_weighting_deviations_db": [0.0, -0.9],
    "acoustic_weighting_uncertainties_db": [0.3, 0.85],
}


def test_over_the_maximum_only_by_the_correction_data_did_not_conform() -> None:
    record = _record(
        **_OVER_BY_CORRECTIONS,
        acoustic_weighting_uncertainties_without_correction_data_db=[0.3, 0.6],
    )
    result = _verify(record, pattern_approval_public=True)
    assert result.unusable == ()
    assert result.over_maximum_by_correction_data == (("12", "8 kHz"),)
    assert result.failed == (("12", "8 kHz"),)
    assert not result.passes
    assert result.statement == (
        _statement(ref.IEC61672_3_STATEMENT_T, 1)
        + " Tests not successfully completed: clause 12 (acoustical signal tests "
        "of a frequency weighting), 8 kHz: the actual expanded uncertainty "
        "exceeded the maximum permitted only because the manufacturer-provided "
        "uncertainty for the free-field or random-incidence correction data was "
        "a significant part of the laboratory's uncertainty budget (4.4)."
    )


def test_without_the_split_the_result_is_unusable() -> None:
    result = _verify(_record(**_OVER_BY_CORRECTIONS))
    assert result.unusable == (("12", "8 kHz"),)
    assert result.over_maximum_by_correction_data == ()
    assert "(IEC 61672-3:2013, 4.3)" in result.statement


@pytest.mark.parametrize(
    ("split_db", "four_four"),
    [(0.69, True), (0.70, True), (0.71, False)],
    ids=["inside", "at-maximum", "past-maximum"],
)
def test_4_4_holds_the_uncertainty_without_the_data_to_the_maximum(
    split_db: float, *, four_four: bool
) -> None:
    """Its first sentence: without the data, the maximum still binds."""
    record = _record(
        **_OVER_BY_CORRECTIONS,
        acoustic_weighting_uncertainties_without_correction_data_db=[0.3, split_db],
    )
    result = _verify(record)
    assert bool(result.over_maximum_by_correction_data) is four_four
    assert bool(result.unusable) is not four_four


def test_a_deviation_past_its_limit_under_4_4_gives_both_reasons() -> None:
    record = _record(
        acoustic_weighting_deviations_db=[0.0, -2.6],
        acoustic_weighting_uncertainties_db=[0.3, 0.85],
        acoustic_weighting_uncertainties_without_correction_data_db=[0.3, 0.6],
    )
    requirement = _verify(record).requirement("acoustic_weighting")
    assert requirement.failure_reason("8 kHz") == (
        "measured deviations from the design-goal frequency weighting exceeded "
        "the applicable acceptance limits, and the actual expanded uncertainty "
        "exceeded the maximum permitted only because the manufacturer-provided "
        "uncertainty for the free-field or random-incidence correction data was "
        "a significant part of the laboratory's uncertainty budget (4.4)"
    )


def test_4_4_reads_clause_13_by_its_band() -> None:
    """16 kHz: 1,00 dB of Table B.1; a total of 1,2 dB, 0,9 dB without the data."""
    total = {k: [0.15] * 8 + [1.2] for k in "ACZ"}
    split = {k: [0.15] * 8 + [0.9] for k in "ACZ"}
    record = _record(
        electrical_weighting_uncertainties_db=total,
        electrical_weighting_uncertainties_without_correction_data_db=split,
    )
    result = _verify(record)
    assert result.over_maximum_by_correction_data == (
        ("13", "A, 16 kHz"),
        ("13", "C, 16 kHz"),
        ("13", "Z, 16 kHz"),
    )
    assert result.unusable == ()


def test_a_4_4_result_is_drawn_as_not_conforming() -> None:
    record = _record(
        **_OVER_BY_CORRECTIONS,
        acoustic_weighting_uncertainties_without_correction_data_db=[0.3, 0.6],
    )
    result = _verify(record)
    ax = result.requirement("acoustic_weighting").plot()
    legend = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "Does not conform" in legend
    assert "Unusable (§4.3)" not in legend
    assert ax.get_title().startswith("IEC 61672-3 §12: does not conform")
    plt.close(ax.figure)
    ax = result.plot()
    legend = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "Unusable (§4.3)" not in legend
    plt.close(ax.figure)


def test_only_a_failed_result_has_a_reason() -> None:
    requirement = _verify(_record()).requirement("level_linearity")
    with pytest.raises(ValueError, match="'94 dB' did not fail"):
        requirement.failure_reason("94 dB")


def test_a_4_4_result_must_be_over_its_maximum() -> None:
    requirement = _verify(_record()).requirement("acoustic_weighting")
    with pytest.raises(ValueError, match=r"\['8 kHz'\] are not results"):
        dataclasses.replace(requirement, over_maximum_by_correction_data=("8 kHz",))


def test_a_heading_keeps_the_capital_of_a_weighting_letter() -> None:
    """Clause 19, "C-weighted peak sound level", stays C in running text."""
    result = _verify(_record(c_peak_differences_db=[5.6, 2.5, 2.3]))
    assert "clause 19 (C-weighted peak sound level), one cycle, 8 kHz:" in (
        result.statement
    )
    assert (
        "clause 18 (toneburst response)"
        in _verify(_record(toneburst_responses_db=_toneburst("F", 2, -30.2))).statement
    )


def test_requirement_lookup_names_what_was_measured() -> None:
    result = _verify(_class_2_record(), 2)
    with pytest.raises(KeyError, match="'c_peak' was not measured"):
        result.requirement("c_peak")


def test_verdicts_refuse_a_truth_value() -> None:
    result = _verify(_record())
    requirement = result.requirement("overload")
    with pytest.raises(TypeError, match="SoundLevelMeterPeriodicVerification"):
        bool(result)
    with pytest.raises(TypeError, match="SoundLevelMeterPeriodicRequirement"):
        bool(requirement)


# ---------------------------------------------------------------------------
# The record
# ---------------------------------------------------------------------------


def test_the_record_is_frozen() -> None:
    record = _record()
    assert isinstance(record.toneburst_responses_db, MappingProxyType)
    assert isinstance(record.toneburst_responses_db["F"], tuple)
    assert isinstance(record.linearity_deviations_db, tuple)
    assert isinstance(record.self_noise_electrical_db, MappingProxyType)
    with pytest.raises(dataclasses.FrozenInstanceError):
        record.long_term_stability_db = 1.0  # type: ignore[misc]


_SPLIT = "acoustic_weighting_uncertainties_without_correction_data_db"
_ELECTRICAL_SPLIT = "electrical_weighting_uncertainties_without_correction_data_db"


@pytest.mark.parametrize(
    ("fields", "match"),
    [
        ({"long_term_stability_uncertainty_db": None}, "clause 15 needs"),
        ({"calibration_check_adjusted_db": None}, "clause 10 needs"),
        ({"air_temperatures_c": None}, "clause 7 records"),
        (
            {"relative_humidities_percent": [45.0, 120.0]},
            "'relative_humidities_percent' holds a reading",
        ),
        (
            {"acoustic_weighting_deviations_db": [0.1]},
            "'acoustic_weighting_deviations_db' must hold 2 results",
        ),
        (
            {"linearity_uncertainties_db": [0.2] * 17},
            "clause 16: 18 results but 17 uncertainties",
        ),
        (
            {"linearity_uncertainties_db": [0.2] * 17 + [-0.1]},
            "'linearity_uncertainties_db' must be non-negative",
        ),
        ({"linearity_levels_db": [94.0]}, "'linearity_levels_db' labels"),
        (
            {"linearity_deviations_db": _placed(_LINEARITY_DB, 1, _NAN)},
            "'linearity_deviations_db' must hold finite values",
        ),
        (
            {"weighting_at_1khz_deviations_db": {"C": 0.0, "B": 0.0}},
            "'weighting_at_1khz_deviations_db' must be a non-empty mapping keyed by",
        ),
        (
            {
                "toneburst_responses_db": {
                    "F": [-1.0, -18.0],
                    "S": [-7.4, -27.0],
                    "E": [-7.0, -27.0, -36.0],
                }
            },
            re.escape("'toneburst_responses_db['F']' must hold 3 results"),
        ),
        (
            {
                "toneburst_responses_db": {
                    "F": [_NAN] * 3,
                    "S": [-7.4, -27.0],
                    "E": [-7.0, -27.0, -36.0],
                }
            },
            re.escape("'toneburst_responses_db['F']' holds no measured value"),
        ),
        (
            {"c_peak_uncertainties_db": [0.3, _NAN, 0.3]},
            "clause 19: a result and its uncertainty must be NaN together",
        ),
        (
            {"c_peak_overload_indicated": "no"},
            "'c_peak_overload_indicated' must be True or False",
        ),
        (
            {"weighting_at_1khz_uncertainties_db": {"C": 0.1}},
            "clause 14.2: 'weighting_at_1khz_deviations_db' and "
            "'weighting_at_1khz_uncertainties_db' must have the same keys",
        ),
        (
            {
                "acoustic_weighting_deviations_db": None,
                "acoustic_weighting_uncertainties_db": None,
                _SPLIT: [0.2, 0.3],
            },
            f"'{_SPLIT}' splits 'acoustic_weighting_uncertainties_db', which is missing",
        ),
        (
            {_SPLIT: [0.25, 0.41]},
            f"'{_SPLIT}' must not exceed 'acoustic_weighting_uncertainties_db'",
        ),
        ({_SPLIT: [0.25, -0.1]}, f"'{_SPLIT}' must be non-negative"),
        ({_SPLIT: [0.25]}, f"'{_SPLIT}' must hold one value per value"),
        (
            {_ELECTRICAL_SPLIT: {"A": [0.1] * 9}},
            f"'{_ELECTRICAL_SPLIT}' and 'electrical_weighting_uncertainties_db' "
            "must have the same keys",
        ),
        (
            {_ELECTRICAL_SPLIT: {k: [0.1] * 8 + [_NAN] for k in "ACZ"}},
            re.escape(
                f"'{_ELECTRICAL_SPLIT}['A']': a result and its uncertainty must "
                "be NaN together"
            ),
        ),
    ],
)
def test_the_record_refuses_what_the_rule_cannot_read(
    fields: dict[str, Any], match: str
) -> None:
    record = _record()
    base = {f.name: getattr(record, f.name) for f in dataclasses.fields(record)}
    base.update(fields)
    with pytest.raises(ValueError, match=match):
        metrology.SoundLevelMeterPeriodicMeasurements(**base)


def test_an_observation_needs_its_test() -> None:
    with pytest.raises(
        ValueError, match="'overload_latched' is observed during the test of"
    ):
        metrology.SoundLevelMeterPeriodicMeasurements(overload_latched=True)


@pytest.mark.parametrize("meter_class", [0, 3, 1.0, True, "1"])
def test_the_class_is_1_or_2(meter_class: object) -> None:
    record = _record()
    with pytest.raises(ValueError, match="'meter_class' must be 1 or 2"):
        metrology.verify_sound_level_meter_periodic(meter_class, record)  # type: ignore[arg-type]


def test_a_class_2_row_of_nine_frequencies_is_refused() -> None:
    record = _record()
    with pytest.raises(
        ValueError,
        match=re.escape(
            "'electrical_weighting_deviations_db['A']' must hold 8 results for class 2"
        ),
    ):
        metrology.verify_sound_level_meter_periodic(2, record)


def test_an_empty_record_has_nothing_to_grade() -> None:
    record = metrology.SoundLevelMeterPeriodicMeasurements(
        calibration_check_initial_db=94.0, calibration_check_adjusted_db=94.0
    )
    with pytest.raises(ValueError, match="'measurements' holds no result to grade"):
        metrology.verify_sound_level_meter_periodic(1, record)


# ---------------------------------------------------------------------------
# The figures
# ---------------------------------------------------------------------------


def test_the_requirement_figure_names_each_result() -> None:
    result = _verify(_record(toneburst_responses_db=_toneburst("F", 2, -30.2)))
    ax = result.requirement("toneburst").plot(language="es")
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels[2] == "F, 0,25 ms"
    assert "no conforme" in ax.get_title()
    plt.close(ax.figure)


def test_the_range_figure_names_each_reading_by_its_subclause() -> None:
    """17.3 is a subclause, not a decimal: it keeps its point in Spanish."""
    requirement = _verify(_record()).requirement("range_linearity")
    for language, word, reference in (
        ("en", "range", "reference range"),
        ("es", "rango", "rango de referencia"),
    ):
        ax = requirement.plot(language=language)
        labels = [t.get_text() for t in ax.get_xticklabels()]
        assert labels == [
            f"17.3, {word} 1",
            f"17.3, {word} 2",
            f"17.4, {reference}",
            f"17.4, {word} 1",
            f"17.4, {word} 2",
        ]
        plt.close(ax.figure)


def test_the_peak_figure_translates_the_signals() -> None:
    ax = _verify(_record()).requirement("c_peak").plot(language="es")
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels == [
        "un ciclo\n8 kHz",
        "semiciclo positivo\n500 Hz",
        "semiciclo negativo\n500 Hz",
    ]
    plt.close(ax.figure)


def test_the_margin_figures_mark_an_unusable_result() -> None:
    record = _record(long_term_stability_uncertainty_db=0.12)
    result = _verify(record)
    ax = result.plot(language="es")
    legend = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "No utilizable (§4.3)" in legend
    assert "no superados" in ax.get_title()
    plt.close(ax.figure)
    ax = result.requirement("electrical_weighting").plot()
    assert len(ax.get_xticklabels()) == 27
    plt.close(ax.figure)


@pytest.mark.parametrize("language", ["en", "es"])
def test_every_requirement_title_fits_its_default_figure(language: str) -> None:
    """The verdict is the end of the title's first line, never cut off."""
    record = _record(long_term_stability_uncertainty_db=0.12)
    result = _verify(record)
    for requirement in result.requirements:
        ax = requirement.plot(language=language)
        figure = ax.figure
        figure.canvas.draw()
        extent = ax.title.get_window_extent()
        assert 0.0 <= extent.x0
        assert extent.x1 <= figure.bbox.width, ax.get_title()
        plt.close(figure)


def test_the_title_names_the_clause_its_verdict_and_its_heading() -> None:
    ax = _verify(_record()).requirement("c_peak").plot()
    assert ax.get_title() == "IEC 61672-3 §19: conforms\nC-weighted peak sound level"
    plt.close(ax.figure)
    ax = _verify(_record()).requirement("toneburst").plot(language="es")
    assert ax.get_title() == ("IEC 61672-3 §18: conforme\nRespuesta a una ráfaga tonal")
    plt.close(ax.figure)


def test_the_verdict_figure_names_the_clauses_it_does_not_hold() -> None:
    """Not measured, not applicable and not declared are three different ticks."""
    result = _verify(
        _class_2_record(),
        2,
        features=_basic(level_ranges=2, c_weighting=None, c_weighted_peak=None),
    )
    ax = result.plot()
    ticks = {t.get_text(): t.get_color() for t in ax.get_xticklabels()}
    assert "§17\nnot measured" in ticks
    assert "§19\nnot declared" in ticks
    assert "§20\nnot applicable" in ticks
    assert "§16" in ticks
    assert len({ticks["§17\nnot measured"], ticks["§19\nnot declared"]}) == 2
    assert ticks["§20\nnot applicable"] != ticks["§16"]
    upright = {t.get_text(): t.get_rotation() for t in ax.get_xticklabels()}
    assert upright["§17\nnot measured"] == pytest.approx(90.0)
    assert upright["§16"] == pytest.approx(0.0)
    plt.close(ax.figure)
    ax = result.plot(language="es")
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert "§17\nno medido" in labels
    assert "§19\nno declarado" in labels
    assert "§20\nno aplicable" in labels
    plt.close(ax.figure)


def test_a_complete_verdict_figure_names_only_clauses() -> None:
    ax = _verify(_record()).plot()
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels == [
        "§12",
        "§13",
        "§14.2",
        "§14.3",
        "§15",
        "§16",
        "§17",
        "§18",
        "§19",
        "§20",
        "§21",
    ]
    plt.close(ax.figure)


def test_a_failed_check_is_named_in_red() -> None:
    result = _verify(_record(overload_latched=False))
    ax = result.plot()
    ticks = {t.get_text(): t.get_color() for t in ax.get_xticklabels()}
    assert ticks["§20"] != ticks["§21"]
    plt.close(ax.figure)


#: The colour of the dashes the verdict figure draws, one per result.
_DASH_COLOR = mpl.colors.to_hex("#1f77b4")

#: The markers the verdict figure draws for the result that decides a
#: clause: conforms, does not conform, unusable (4.3).
_VERDICT_MARKERS = ("D", "X", "o")


def _slots(
    ax: plt.Axes,
) -> tuple[dict[float, list[float]], dict[float, tuple[str, float]]]:
    """The verdict figure read back: each slot's dashes and its one marker."""
    dashes: dict[float, list[float]] = {}
    markers: dict[float, tuple[str, float]] = {}
    for line in ax.get_lines():
        marker = line.get_marker()
        xs = np.asarray(line.get_xdata(), dtype=float)
        ys = np.asarray(line.get_ydata(), dtype=float)
        if marker == "_" and mpl.colors.to_hex(line.get_color()) == _DASH_COLOR:
            assert np.all(xs == xs[0])
            dashes[float(xs[0])] = sorted(ys.tolist())
        elif marker in _VERDICT_MARKERS:
            assert float(xs[0]) not in markers
            markers[float(xs[0])] = (str(marker), float(ys[0]))
    return dashes, markers


def _margin(v: metrology.ConformanceVerification) -> float:
    """The distance from a deviation to its nearer finite acceptance limit."""
    return min(
        m
        for m in (v.deviation - v.lower_limit, v.upper_limit - v.deviation)
        if math.isfinite(m)
    )


def _dense_16() -> dict[str, Any]:
    """Clause 16 in 1 dB steps across an 80 dB linear operating range.

    85 steps from 38 dB to 122 dB, finer than 16.3 asks and so complete, on
    a range from 40 dB to 120 dB with overload first at 123 dB and
    under-range at 37 dB.
    """
    levels = [float(level) for level in range(38, 123)]
    return _linearity(
        levels,
        linear_operating_range_db=[40.0, 120.0],
        linearity_starting_point_db=94.0,
        linearity_overload_level_db=123.0,
        linearity_under_range_level_db=37.0,
    )


@pytest.mark.parametrize("language", ["en", "es"])
def test_the_verdict_figure_gives_every_clause_one_slot_whatever_its_size(
    language: str,
) -> None:
    """85 steps of Clause 16 take one slot, and no clause's name runs into another."""
    result = _verify(_record(**_dense_16()))
    assert result.incomplete == ()
    ax = result.plot(language=language)
    assert list(ax.get_xticks()) == list(range(1, 12))
    assert ax.get_xlim() == (0.5, 11.5)
    dashes, markers = _slots(ax)
    held = {float(k): r for k, r in enumerate(result.requirements, 1)}
    assert set(dashes) == set(held) == set(markers)
    for x, requirement in held.items():
        assert dashes[x] == pytest.approx(
            sorted(_margin(v) for v in requirement.verifications)
        )
    assert len(dashes[6.0]) == 85
    ax.figure.canvas.draw()
    boxes = [t.get_window_extent() for t in ax.get_xticklabels()]
    assert all(a.x1 < b.x0 for a, b in zip(boxes, boxes[1:], strict=False))
    plt.close(ax.figure)


def test_the_verdict_figure_marks_each_clause_by_the_result_that_decides_it() -> None:
    """A failure first (4.4 included), then an unusable result, then the nearest.

    Clause 12: 125 Hz conforms 0.8 dB inside its limit, and 8 kHz, 1.9 dB
    inside its own, is over its maximum only by the correction data, a
    result that did not conform (4.4): the cross at 1.9 dB stands for the
    clause, not the diamond nearer its limit. Clause 15 is unusable (4.3);
    Clause 16 conforms, drawn at its nearest step; Clause 18 fails.
    """
    record = _record(
        acoustic_weighting_uncertainties_db=[0.25, 0.85],
        acoustic_weighting_uncertainties_without_correction_data_db=[0.25, 0.6],
        long_term_stability_uncertainty_db=0.12,
        toneburst_responses_db=_toneburst("F", 2, -30.4),
    )
    result = _verify(record)
    ax = result.plot()
    _, markers = _slots(ax)
    assert markers[1.0][0] == "X"
    assert markers[1.0][1] == pytest.approx(1.9)
    assert markers[5.0] == ("o", pytest.approx(0.05))
    linearity = result.requirement("level_linearity").verifications
    assert markers[6.0] == ("D", pytest.approx(min(_margin(v) for v in linearity)))
    assert markers[8.0] == ("X", pytest.approx(-0.4))
    assert all(markers[x][0] == "D" for x in (2.0, 3.0, 4.0, 7.0, 9.0, 10.0, 11.0))
    plt.close(ax.figure)


def test_the_verdict_figure_names_the_dashes_once() -> None:
    for language, text in (
        ("en", "Every result of the clause"),
        ("es", "Cada resultado del apartado"),
    ):
        ax = _verify(_record()).plot(language=language)
        legend = [t.get_text() for t in ax.get_legend().get_texts()]
        assert legend.count(text) == 1
        assert ax.get_xlabel() == ("Clause" if language == "en" else "Apartado")
        plt.close(ax.figure)


def test_a_verdict_that_holds_no_requirement_still_draws_its_slots() -> None:
    """Every graded clause keeps its named slot on the margin axis, with no marks."""
    result = metrology.SoundLevelMeterPeriodicVerification(
        meter_class=1,
        pattern_approval_public=False,
        corrections_in_manual=True,
        measurements=metrology.SoundLevelMeterPeriodicMeasurements(),
        requirements=(),
    )
    ax = result.plot()
    measured, declared = "not measured", "not declared"
    slots = (
        ("12", measured),
        ("13", measured),
        ("14.2", measured),
        ("14.3", declared),
        ("15", measured),
        ("16", measured),
        ("17", declared),
        ("18", measured),
        ("19", declared),
        ("20", declared),
        ("21", measured),
    )
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels == [f"§{clause}\n{status}" for clause, status in slots]
    assert ax.get_xlim() == (0.5, 11.5)
    assert _slots(ax) == ({}, {})
    assert ax.get_yscale() == "symlog"
    assert ax.get_ylim() == pytest.approx((-0.5, 1.0))
    legend = [t.get_text() for t in ax.get_legend().get_texts()]
    assert legend == ["Acceptance limit"]
    assert ax.get_title() == "IEC 61672-3 periodic tests, class 1: not passed"
    plt.close(ax.figure)
