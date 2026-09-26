#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Periodic tests of a sound level meter (IEC 61672-3) and the tables of IEC 61672-1.

Three things are pinned here.

The tables of IEC 61672-1:2013 the periodic tests read, each cell against an
independent transcription of the rasterised page, parsed from the strings the
page prints: the reference toneburst responses and their limits of Table 4,
the reference differences of the C-weighted peak of Table 5 and the
maximum-permitted uncertainties of Table B.1. Table 4 is also held to the two
equations its notes give it by, (7) for a maximum time-weighted level and (8)
for a sound exposure level, rounded to a tenth as the page rounds them.

The verdict of :func:`phonometry.metrology.verify_sound_level_meter_periodic`
across the printed limits: a synthetic record whose result lies 0,01 dB
inside a printed limit or on it conforms, and one 0,01 dB past it does not.
The rows sample one or two limits of each graded requirement for class 1, and
for class 2 wherever its column differs (Table 3 at 125 Hz and 8 kHz, Table 4
at 0,25 ms and 2 ms, Table 5, 5.14.2, 5.6.5 and 5.15.2); the test suite
sweeps every limit of every requirement for both classes. Every maximum of
Table B.1 the verdict uses conforms at its value and makes the result
unusable (4.3) 0,01 dB above it, at one band per requirement here and at
every band in the test suite. 4.4: a result over its maximum only by the
manufacturer's correction data is a result that did not conform, until its
uncertainty without that data passes the maximum too. And the completeness of
8.1 where another clause shows a feature: C for a meter with C-weighted peak
(IEC 61672-1 5.1.10), and the S and time-averaged displays 14.3 compares; and
the extent of Clauses 16 and 17: the steps of 16.3 from the starting point up
to the first overload and down to the first under-range indication, 17.4
on every level range, the reference one included, and 17.3 on every one
besides it.

The statements of Clause 22: the texts of r), s) and t), with the class and
the year filled in as the clause says, word for word against the page.

Oracles read on the rasterised pages of BS EN 61672-1:2013 and BS EN
61672-3:2013 (PDF page = printed folio + 2 in both): Part 1 5.1.10 (folio
15), Table 3 (22), 5.5.9 (21), 5.6.5 (23), 5.8.3 (24), Table 4 (25), 5.11.3
(27), Table 5 and 5.14.2 (28), 5.15.2 (29) and Table B.1 (42 and 43); Part 3
4.3 and 4.4 (7), 8.1 (8), 14.1 (13), 16.3 (14), 17.3 and 17.4 (15), 20.1 (16)
and 22 r), s) and t) (18 and 19).
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

import reference_data as ref

import phonometry as ph

from ..registry import Outcome, count, record, register

_SLM = "Sound level meter periodic tests (IEC 61672-3, IEC 61672-1)"

#: How far past a printed limit or maximum the failing side is taken, dB: a
#: hundredth of the 0,1 dB a meter displays.
_PAST_DB = 0.01


def _number(text: str) -> float:
    """A printed number, ``"-0,1"`` or ``"-∞"``, its thousands grouped with a space."""
    return float(text.replace(" ", "").replace(",", ".").replace("∞", "inf"))


def _limits(text: str) -> tuple[float, float]:
    """A printed limit, ``"±0,5"`` or ``"+1,0; -1,5"``, as ``(lower, upper)``."""
    if text.lstrip().startswith("±"):
        value = _number(text.lstrip()[1:].strip())
        return -value, value
    upper, lower = (part.strip() for part in text.split(";"))
    return _number(lower), _number(upper)


# --------------------------------------------------------------------------
# IEC 61672-1:2013 Tables 4, 5 and B.1
# --------------------------------------------------------------------------
@register(
    _SLM,
    "IEC 61672-1:2013 Table 4",
    "Reference responses and limits of LAFmax - LA and LAE - LA, 12 durations",
)
def _chk_table_4_f_and_e() -> Outcome:
    matching = total = 0
    rows = zip(
        ph.metrology.IEC61672_TABLE_4["F"],
        ph.metrology.IEC61672_TABLE_4["E"],
        ref.IEC61672_1_TABLE_4_F_AND_E,
        strict=True,
    )
    for f_row, e_row, (duration, f_ref, e_ref, class_1, class_2) in rows:
        for row, printed in ((f_row, f_ref), (e_row, e_ref)):
            cells = (
                (row.duration_ms, _number(duration)),
                (row.reference_response_db, _number(printed)),
                (row.class_1_limits_db, _limits(class_1)),
                (row.class_2_limits_db, _limits(class_2)),
            )
            matching += sum(built == page for built, page in cells)
            total += len(cells)
    return count(matching, total, subject="cells")


@register(
    _SLM,
    "IEC 61672-1:2013 Table 4",
    "Reference responses and limits of LASmax - LA, 9 durations",
)
def _chk_table_4_s() -> Outcome:
    matching = total = 0
    for row, (duration, reference, class_1, class_2) in zip(
        ph.metrology.IEC61672_TABLE_4["S"], ref.IEC61672_1_TABLE_4_S, strict=True
    ):
        cells = (
            (row.duration_ms, _number(duration)),
            (row.reference_response_db, _number(reference)),
            (row.class_1_limits_db, _limits(class_1)),
            (row.class_2_limits_db, _limits(class_2)),
        )
        matching += sum(built == page for built, page in cells)
        total += len(cells)
    return count(matching, total, subject="cells")


@register(
    _SLM,
    "IEC 61672-1:2013 Table 4, Equations (7) and (8)",
    "Reference toneburst responses against 10 lg(1 - exp(-Tb/tau)) and 10 lg(Tb/T0)",
)
def _chk_table_4_equations() -> Outcome:
    """The 33 reference responses, rounded to a tenth as the page rounds them."""
    matching = total = 0
    for key, tau_s in (("F", 0.125), ("S", 1.0), ("E", None)):
        for row in ph.metrology.IEC61672_TABLE_4[key]:
            seconds = row.duration_ms / 1000.0
            exact = (
                10.0 * math.log10(seconds)
                if tau_s is None
                else 10.0 * math.log10(1.0 - math.exp(-seconds / tau_s))
            )
            matching += math.isclose(
                round(exact, 1), row.reference_response_db, abs_tol=1e-9
            )
            total += 1
    return count(matching, total, subject="reference responses")


@register(
    _SLM,
    "IEC 61672-1:2013 Table 5",
    "Reference differences LCpeak - LC and limits, 5 test signals",
)
def _chk_table_5() -> Outcome:
    signals = {"one": "one cycle"}
    matching = total = 0
    for row, (cycles, frequency, reference, class_1, class_2) in zip(
        ph.metrology.IEC61672_TABLE_5, ref.IEC61672_1_TABLE_5, strict=True
    ):
        cells = (
            (row.signal, signals.get(cycles, cycles)),
            (row.nominal_frequency_hz, _number(frequency)),
            (row.reference_difference_db, _number(reference)),
            (row.class_1_limits_db, _limits(class_1)),
            (row.class_2_limits_db, _limits(class_2)),
        )
        matching += sum(built == page for built, page in cells)
        total += len(cells)
    return count(matching, total, subject="cells")


@register(
    _SLM,
    "IEC 61672-1:2013 Table B.1",
    "Maximum-permitted uncertainties, 31 printed rows (the F and S decay rates in two)",
)
def _chk_table_b1() -> Outcome:
    printed: list[tuple[str, str, float, str]] = []
    for requirement, reference, value in ref.IEC61672_1_TABLE_B1:
        if "dB/s" in value:
            for half in value.split(";"):
                number, which = half.strip().split(" dB/s for ")
                printed.append(
                    (requirement, f"{reference}, {which}", _number(number), "dB/s")
                )
        else:
            printed.append((requirement, reference, _number(value), "dB"))
    built = [
        (row.requirement, row.reference, row.max_uncertainty, row.unit)
        for row in ph.metrology.IEC61672_TABLE_B1
    ]
    matching = sum(b == p for b, p in zip(built, printed, strict=False))
    return count(matching, max(len(built), len(printed)), subject="rows")


# --------------------------------------------------------------------------
# The verdict at every limit IEC 61672-3 reads
# --------------------------------------------------------------------------
#: The steps of 16.3 on the reference level range of the meter of
#: :func:`_record`: from the starting point of 94 dB up in 5 dB steps to
#: within 5 dB of the upper boundary of its linear operating range, 120 dB,
#: and in 1 dB steps short of the overload at 121 dB; down the same way to
#: the lower boundary, 55 dB, short of the under-range at 54 dB.
_STEPS_DB = (
    *(94.0, 99.0, 104.0, 109.0, 114.0, 119.0, 120.0),
    *(89.0, 84.0, 79.0, 74.0, 69.0, 64.0, 59.0, 58.0, 57.0, 56.0, 55.0),
)

#: That meter as its instruction manual declares the one feature a record
#: cannot count: two level ranges, so 17.3 reads the one besides the
#: reference one and 17.4 both, the reference one first.
_METER = ph.metrology.SoundLevelMeterFeatures(level_ranges=2)


def _steps(index: int, value: float) -> list[float]:
    """The 16 results of that meter, ``value`` at one step and 0 elsewhere."""
    row = [0.0] * len(_STEPS_DB)
    row[index] = value
    return row


def _record(**over: Any) -> ph.metrology.SoundLevelMeterPeriodicMeasurements:
    """A complete record of a meter with A, C, Z, F, S and Leq, all well inside."""
    base: dict[str, Any] = {
        "static_pressures_kpa": [100.8, 100.6],
        "air_temperatures_c": [23.1, 23.4],
        "relative_humidities_percent": [45.0, 47.0],
        "calibration_check_initial_db": 93.9,
        "calibration_check_adjusted_db": 94.0,
        "self_noise_microphone_db": 17.2,
        "self_noise_electrical_db": {"A": 12.1, "C": 14.0, "Z": 19.5},
        "acoustic_weighting_deviations_db": [0.0, 0.0],
        "acoustic_weighting_uncertainties_db": [0.3, 0.4],
        "electrical_weighting_deviations_db": {k: [0.0] * 9 for k in "ACZ"},
        "electrical_weighting_uncertainties_db": {k: [0.15] * 9 for k in "ACZ"},
        "weighting_at_1khz_deviations_db": {"C": 0.0, "Z": 0.0},
        "weighting_at_1khz_uncertainties_db": {"C": 0.1, "Z": 0.1},
        "time_weighting_at_1khz_deviations_db": {"S": 0.0, "eq": 0.0},
        "time_weighting_at_1khz_uncertainties_db": {"S": 0.1, "eq": 0.1},
        "long_term_stability_db": 0.0,
        "long_term_stability_uncertainty_db": 0.05,
        "linearity_deviations_db": [0.0] * len(_STEPS_DB),
        "linearity_uncertainties_db": [0.2] * len(_STEPS_DB),
        "linearity_levels_db": list(_STEPS_DB),
        "linear_operating_range_db": [55.0, 120.0],
        "linearity_starting_point_db": 94.0,
        "linearity_overload_level_db": 121.0,
        "linearity_under_range_level_db": 54.0,
        "range_linearity_deviations_db": {"17.3": [0.0], "17.4": [0.0, 0.0]},
        "range_linearity_uncertainties_db": {"17.3": [0.2], "17.4": [0.2, 0.2]},
        "toneburst_responses_db": {
            "F": [-1.0, -18.0, -27.0],
            "S": [-7.4, -27.0],
            "E": [-7.0, -27.0, -36.0],
        },
        "toneburst_uncertainties_db": {
            "F": [0.2] * 3,
            "S": [0.2] * 2,
            "E": [0.2] * 3,
        },
        "c_peak_differences_db": [3.4, 2.4, 2.4],
        "c_peak_uncertainties_db": [0.3] * 3,
        "c_peak_overload_indicated": False,
        "overload_difference_db": 0.0,
        "overload_uncertainty_db": 0.2,
        "overload_latched": True,
        "high_level_stability_db": 0.0,
        "high_level_stability_uncertainty_db": 0.05,
    }
    base.update(over)
    return ph.metrology.SoundLevelMeterPeriodicMeasurements(**base)


def _class_2(**over: Any) -> ph.metrology.SoundLevelMeterPeriodicMeasurements:
    """The same meter tested as class 2: eight octaves to 8 kHz."""
    fields: dict[str, Any] = {
        "electrical_weighting_deviations_db": {k: [0.0] * 8 for k in "ACZ"},
        "electrical_weighting_uncertainties_db": {k: [0.15] * 8 for k in "ACZ"},
    }
    fields.update(over)
    return _record(**fields)


def _flip(
    name: str,
    meter_class: int,
    fields: Callable[[float], dict[str, Any]],
    limit: float,
    outward: float,
) -> Outcome:
    """The requirement conforms 0,01 dB inside the limit and on it, not past it."""
    build = _record if meter_class == 1 else _class_2
    verify = ph.metrology.verify_sound_level_meter_periodic
    states = {"just inside": -_PAST_DB, "at the limit": 0.0, "past it": _PAST_DB}
    computed = {
        state: verify(meter_class, build(**fields(limit + outward * offset)))
        .requirement(name)
        .passes
        for state, offset in states.items()
    }

    verdict = {True: "conforms", False: "does not conform"}

    return record(
        {"just inside": 1.0, "at the limit": 1.0, "past it": 0.0},
        {state: float(passes) for state, passes in computed.items()},
        label="conforms 0.01 dB inside and at the limit, not 0.01 dB past it",
        computed_label=(
            f"{verdict[computed['just inside']]} inside, "
            f"{verdict[computed['at the limit']]} at the limit, "
            f"{verdict[computed['past it']]} past it"
        ),
    )


def _weightings(
    weighting: str, index: int, value: float, count: int = 9
) -> dict[str, list[float]]:
    rows = {k: [0.0] * count for k in "ACZ"}
    rows[weighting][index] = value
    return rows


def _bursts(key: str, index: int, value: float) -> dict[str, list[float]]:
    rows = {"F": [-1.0, -18.0, -27.0], "S": [-7.4, -27.0], "E": [-7.0, -27.0, -36.0]}
    rows[key][index] = value
    return rows


def _table_3(frequency_hz: float, meter_class: int) -> tuple[float, float]:
    """``(lower, upper)`` of the independent transcription of Table 3."""
    row = next(
        r for r in ref.IEC61672_1_TABLE_3_TEST_LIMITS if _number(r[0]) == frequency_hz
    )
    return _limits(row[meter_class])


def _text_limit(clause: str, meter_class: int) -> float:
    """The +/- limit a clause of IEC 61672-1 prints in its text."""
    printed = ref.IEC61672_1_TEXT_LIMITS[clause][meter_class - 1]
    return _limits(printed)[1] if "±" in printed else _number(printed)


def _toneburst_row(
    key: str, duration_ms: float, meter_class: int = 1
) -> tuple[float, tuple[float, float]]:
    """The printed reference and limits of a Table 4 row for a class."""
    if key == "S":
        row = next(r for r in ref.IEC61672_1_TABLE_4_S if _number(r[0]) == duration_ms)
        return _number(row[1]), _limits(row[1 + meter_class])
    row_fe = next(
        r for r in ref.IEC61672_1_TABLE_4_F_AND_E if _number(r[0]) == duration_ms
    )
    reference = row_fe[1] if key == "F" else row_fe[2]
    return _number(reference), _limits(row_fe[2 + meter_class])


def _peak_row(index: int, meter_class: int) -> tuple[float, tuple[float, float]]:
    """The printed reference difference and limits of a Table 5 row."""
    row = ref.IEC61672_1_TABLE_5[index]
    return _number(row[2]), _limits(row[2 + meter_class])


#: One flip row: (source, quantity, requirement, class, the fields a value
#: goes in, the limit, +1 for an upper limit or -1 for a lower one).
_FlipRow = tuple[str, str, str, int, Callable[[float], dict[str, Any]], float, float]


def _flip_rows() -> list[_FlipRow]:
    """One row per limit, each read off the independent transcription."""
    table_3 = "with IEC 61672-1:2013 Table 3"
    table_4 = "IEC 61672-3:2013 18.8 with IEC 61672-1:2013 Table 4"
    table_5 = "IEC 61672-3:2013 19.6 with IEC 61672-1:2013 Table 5"
    low_125_2, _ = _table_3(125.0, 2)
    low_8k, high_8k = _table_3(8000.0, 1)
    _, high_8k_2 = _table_3(8000.0, 2)
    low_16k, _ = _table_3(16000.0, 1)
    _, high_1k = _table_3(1000.0, 1)
    low_z_8k_2, _ = _table_3(8000.0, 2)
    burst_ref, (burst_low, _) = _toneburst_row("F", 0.25)
    burst_ref_2, (burst_low_2, burst_high_2) = _toneburst_row("F", 0.25, 2)
    slow_ref, (slow_low, _) = _toneburst_row("S", 2.0)
    slow_ref_2, (slow_low_2, _) = _toneburst_row("S", 2.0, 2)
    peak_ref, (_, peak_high) = _peak_row(2, 1)
    peak_ref_2, (_, peak_high_2) = _peak_row(2, 2)
    half_ref, (half_low, _) = _peak_row(4, 1)
    half_ref_2, (half_low_2, _) = _peak_row(4, 2)

    def acoustic(index: int) -> Callable[[float], dict[str, Any]]:
        def fields(v: float) -> dict[str, Any]:
            row = [0.0, 0.0]
            row[index] = v
            return {"acoustic_weighting_deviations_db": row}

        return fields

    def electrical(
        weighting: str, index: int, count: int = 9
    ) -> Callable[[float], dict[str, Any]]:
        return lambda v: {
            "electrical_weighting_deviations_db": _weightings(
                weighting, index, v, count
            )
        }

    def burst(key: str, index: int) -> Callable[[float], dict[str, Any]]:
        return lambda v: {"toneburst_responses_db": _bursts(key, index, v)}

    def peak(index: int) -> Callable[[float], dict[str, Any]]:
        def fields(v: float) -> dict[str, Any]:
            row = [3.4, 2.4, 2.4]
            row[index] = v
            return {"c_peak_differences_db": row}

        return fields

    return [
        (
            f"IEC 61672-3:2013 12.16 {table_3}",
            "Acoustical weighting at 8 kHz, class 1, upper limit",
            "acoustic_weighting",
            1,
            acoustic(1),
            high_8k,
            1.0,
        ),
        (
            f"IEC 61672-3:2013 12.16 {table_3}",
            "Acoustical weighting at 8 kHz, class 1, lower limit",
            "acoustic_weighting",
            1,
            acoustic(1),
            low_8k,
            -1.0,
        ),
        (
            f"IEC 61672-3:2013 12.16 {table_3}",
            "Acoustical weighting at 125 Hz, class 2, lower limit",
            "acoustic_weighting",
            2,
            acoustic(0),
            low_125_2,
            -1.0,
        ),
        (
            f"IEC 61672-3:2013 12.16 {table_3}",
            "Acoustical weighting at 8 kHz, class 2, upper limit",
            "acoustic_weighting",
            2,
            acoustic(1),
            high_8k_2,
            1.0,
        ),
        (
            f"IEC 61672-3:2013 13.10 {table_3}",
            "Electrical weighting A at 16 kHz, class 1, lower limit",
            "electrical_weighting",
            1,
            electrical("A", 8),
            low_16k,
            -1.0,
        ),
        (
            f"IEC 61672-3:2013 13.10 {table_3}",
            "Electrical weighting C at 1 kHz, class 1, upper limit",
            "electrical_weighting",
            1,
            electrical("C", 4),
            high_1k,
            1.0,
        ),
        (
            f"IEC 61672-3:2013 13.10 {table_3}",
            "Electrical weighting Z at 8 kHz, class 2, lower limit",
            "electrical_weighting",
            2,
            electrical("Z", 7, 8),
            low_z_8k_2,
            -1.0,
        ),
        (
            "IEC 61672-3:2013 14.2 with IEC 61672-1:2013 5.5.9",
            "C against A at 1 kHz",
            "weighting_at_1khz",
            1,
            lambda v: {"weighting_at_1khz_deviations_db": {"C": v, "Z": 0.0}},
            _text_limit("5.5.9", 1),
            1.0,
        ),
        (
            "IEC 61672-3:2013 14.3 with IEC 61672-1:2013 5.8.3",
            "Time-averaged against F at 1 kHz",
            "time_weighting_at_1khz",
            1,
            lambda v: {"time_weighting_at_1khz_deviations_db": {"S": 0.0, "eq": v}},
            -_text_limit("5.8.3", 1),
            -1.0,
        ),
        (
            "IEC 61672-3:2013 15.3 with IEC 61672-1:2013 5.14.2",
            "Long-term stability, class 1",
            "long_term_stability",
            1,
            lambda v: {"long_term_stability_db": v},
            _text_limit("5.14.2", 1),
            1.0,
        ),
        (
            "IEC 61672-3:2013 15.3 with IEC 61672-1:2013 5.14.2",
            "Long-term stability, class 2",
            "long_term_stability",
            2,
            lambda v: {"long_term_stability_db": v},
            -_text_limit("5.14.2", 2),
            -1.0,
        ),
        (
            "IEC 61672-3:2013 16.4 with IEC 61672-1:2013 5.6.5",
            "Level linearity on the reference level range, class 1",
            "level_linearity",
            1,
            lambda v: {"linearity_deviations_db": _steps(1, v)},
            _text_limit("5.6.5", 1),
            1.0,
        ),
        (
            "IEC 61672-3:2013 16.4 with IEC 61672-1:2013 5.6.5",
            "Level linearity on the reference level range, class 2",
            "level_linearity",
            2,
            lambda v: {"linearity_deviations_db": _steps(0, v)},
            -_text_limit("5.6.5", 2),
            -1.0,
        ),
        (
            "IEC 61672-3:2013 17.5 with IEC 61672-1:2013 5.6.5",
            "Level linearity including the range control, class 1",
            "range_linearity",
            1,
            lambda v: {
                "range_linearity_deviations_db": {"17.3": [0.0], "17.4": [0.0, v]}
            },
            -_text_limit("5.6.5", 1),
            -1.0,
        ),
        (
            "IEC 61672-3:2013 17.5 with IEC 61672-1:2013 5.6.5",
            "Level linearity including the range control, class 2",
            "range_linearity",
            2,
            lambda v: {
                "range_linearity_deviations_db": {"17.3": [0.0], "17.4": [v, 0.0]}
            },
            _text_limit("5.6.5", 2),
            1.0,
        ),
        (
            table_4,
            "Toneburst LAFmax - LA at 0.25 ms, class 1, lower limit",
            "toneburst",
            1,
            burst("F", 2),
            burst_ref + burst_low,
            -1.0,
        ),
        (
            table_4,
            "Toneburst LAFmax - LA at 0.25 ms, class 2, lower limit",
            "toneburst",
            2,
            burst("F", 2),
            burst_ref_2 + burst_low_2,
            -1.0,
        ),
        (
            table_4,
            "Toneburst LAFmax - LA at 0.25 ms, class 2, upper limit",
            "toneburst",
            2,
            burst("F", 2),
            burst_ref_2 + burst_high_2,
            1.0,
        ),
        (
            table_4,
            "Toneburst LASmax - LA at 2 ms, class 1, lower limit",
            "toneburst",
            1,
            burst("S", 1),
            slow_ref + slow_low,
            -1.0,
        ),
        (
            table_4,
            "Toneburst LASmax - LA at 2 ms, class 2, lower limit",
            "toneburst",
            2,
            burst("S", 1),
            slow_ref_2 + slow_low_2,
            -1.0,
        ),
        (
            table_5,
            "C-weighted peak, one cycle at 8 kHz, class 1, upper limit",
            "c_peak",
            1,
            peak(0),
            peak_ref + peak_high,
            1.0,
        ),
        (
            table_5,
            "C-weighted peak, one cycle at 8 kHz, class 2, upper limit",
            "c_peak",
            2,
            peak(0),
            peak_ref_2 + peak_high_2,
            1.0,
        ),
        (
            table_5,
            "C-weighted peak, negative half cycle at 500 Hz, class 1, lower limit",
            "c_peak",
            1,
            peak(2),
            half_ref + half_low,
            -1.0,
        ),
        (
            table_5,
            "C-weighted peak, negative half cycle at 500 Hz, class 2, lower limit",
            "c_peak",
            2,
            peak(2),
            half_ref_2 + half_low_2,
            -1.0,
        ),
        (
            "IEC 61672-3:2013 20.4 with IEC 61672-1:2013 5.11.3",
            "Overload indication, positive less negative half cycle",
            "overload",
            1,
            lambda v: {"overload_difference_db": v},
            _text_limit("5.11.3", 1),
            1.0,
        ),
        (
            "IEC 61672-3:2013 21.3 with IEC 61672-1:2013 5.15.2",
            "High-level stability, class 1",
            "high_level_stability",
            1,
            lambda v: {"high_level_stability_db": v},
            -_text_limit("5.15.2", 1),
            -1.0,
        ),
        (
            "IEC 61672-3:2013 21.3 with IEC 61672-1:2013 5.15.2",
            "High-level stability, class 2",
            "high_level_stability",
            2,
            lambda v: {"high_level_stability_db": v},
            _text_limit("5.15.2", 2),
            1.0,
        ),
    ]


def _register_flips() -> None:
    """Register one check per row of :func:`_flip_rows`."""
    for source, quantity, name, meter_class, fields, limit, outward in _flip_rows():

        def check(
            name: str = name,
            meter_class: int = meter_class,
            fields: Callable[[float], dict[str, Any]] = fields,
            limit: float = limit,
            outward: float = outward,
        ) -> Outcome:
            return _flip(name, meter_class, fields, limit, outward)

        register(_SLM, source, quantity)(check)


_register_flips()


def _b1(requirement: str, frequency_hz: float | None = None) -> float:
    """A maximum of the independent transcription of Table B.1."""
    for name, reference, value in ref.IEC61672_1_TABLE_B1:
        if name != requirement:
            continue
        if frequency_hz is None:
            return _number(value)
        band = reference.split(", ", 1)[1]
        low_text, high_text = band.split(" to ")
        low = _number(low_text.lstrip(">").removesuffix(" Hz").removesuffix(" kHz"))
        low *= 1000.0 if low_text.endswith("kHz") else 1.0
        high = _number(high_text.removesuffix(" kHz").removesuffix(" Hz"))
        high *= 1000.0 if high_text.endswith("kHz") else 1.0
        above = frequency_hz > low if low_text.startswith(">") else frequency_hz >= low
        if above and frequency_hz <= high:
            return _number(value)
    msg = f"no Table B.1 row for {requirement!r} at {frequency_hz!r}"
    raise LookupError(msg)


@register(
    _SLM,
    "IEC 61672-3:2013 4.3 with IEC 61672-1:2013 Table B.1",
    "The maximum of every requirement: conforms at its value, unusable 0.01 dB above",
)
def _chk_maxima() -> Outcome:
    weighting = "Frequency weightings A, C, Z"
    u_125, u_8k, u_16k = (_b1(weighting, f) for f in (125.0, 8000.0, 16000.0))
    u_4k = _b1(weighting, 4000.0)
    cases: list[tuple[str, dict[str, Any], dict[str, Any]]] = [
        (
            "acoustic_weighting",
            {"acoustic_weighting_uncertainties_db": [u_125, u_8k]},
            {"acoustic_weighting_uncertainties_db": [u_125, u_8k + _PAST_DB]},
        ),
        (
            "electrical_weighting",
            {
                "electrical_weighting_uncertainties_db": {
                    k: [u_4k] * 7 + [u_8k, u_16k] for k in "ACZ"
                }
            },
            {
                "electrical_weighting_uncertainties_db": {
                    k: [u_4k] * 7 + [u_8k, u_16k + _PAST_DB] for k in "ACZ"
                }
            },
        ),
        (
            "weighting_at_1khz",
            {
                "weighting_at_1khz_uncertainties_db": dict.fromkeys(
                    "CZ", _b1("A vs. C or Z at 1 kHz")
                )
            },
            {
                "weighting_at_1khz_uncertainties_db": dict.fromkeys(
                    "CZ", _b1("A vs. C or Z at 1 kHz") + _PAST_DB
                )
            },
        ),
        (
            "time_weighting_at_1khz",
            {
                "time_weighting_at_1khz_uncertainties_db": dict.fromkeys(
                    ("S", "eq"), _b1("F vs. S level at 1 kHz")
                )
            },
            {
                "time_weighting_at_1khz_uncertainties_db": dict.fromkeys(
                    ("S", "eq"), _b1("F vs. S level at 1 kHz") + _PAST_DB
                )
            },
        ),
        (
            "long_term_stability",
            {
                "long_term_stability_uncertainty_db": _b1(
                    "Stability during continuous operation"
                )
            },
            {
                "long_term_stability_uncertainty_db": _b1(
                    "Stability during continuous operation"
                )
                + _PAST_DB
            },
        ),
        (
            "level_linearity",
            {
                "linearity_uncertainties_db": [_b1("Level linearity deviation")]
                * len(_STEPS_DB)
            },
            {
                "linearity_uncertainties_db": [
                    _b1("Level linearity deviation") + _PAST_DB
                ]
                * len(_STEPS_DB)
            },
        ),
        (
            "range_linearity",
            {
                "range_linearity_uncertainties_db": {
                    "17.3": [_b1("Level linearity deviation")],
                    "17.4": [_b1("Level linearity deviation")] * 2,
                }
            },
            {
                "range_linearity_uncertainties_db": {
                    "17.3": [_b1("Level linearity deviation") + _PAST_DB],
                    "17.4": [_b1("Level linearity deviation") + _PAST_DB] * 2,
                }
            },
        ),
        (
            "toneburst",
            {
                "toneburst_uncertainties_db": {
                    k: [_b1("Toneburst response")] * n
                    for k, n in (("F", 3), ("S", 2), ("E", 3))
                }
            },
            {
                "toneburst_uncertainties_db": {
                    k: [_b1("Toneburst response") + _PAST_DB] * n
                    for k, n in (("F", 3), ("S", 2), ("E", 3))
                }
            },
        ),
        (
            "c_peak",
            {"c_peak_uncertainties_db": [_b1("C-weighted peak sound levels")] * 3},
            {
                "c_peak_uncertainties_db": [
                    _b1("C-weighted peak sound levels") + _PAST_DB
                ]
                * 3
            },
        ),
        (
            "overload",
            {"overload_uncertainty_db": _b1("Overload indication")},
            {"overload_uncertainty_db": _b1("Overload indication") + _PAST_DB},
        ),
        (
            "high_level_stability",
            {"high_level_stability_uncertainty_db": _b1("High-level stability")},
            {
                "high_level_stability_uncertainty_db": _b1("High-level stability")
                + _PAST_DB
            },
        ),
    ]
    verify = ph.metrology.verify_sound_level_meter_periodic
    matching = 0
    for name, at_maximum, past_maximum in cases:
        inside = verify(1, _record(**at_maximum)).requirement(name)
        outside = verify(1, _record(**past_maximum)).requirement(name)
        matching += inside.passes and bool(outside.unusable) and not outside.failed
    return count(matching, len(cases), subject="maxima")


@register(
    _SLM,
    "IEC 61672-3:2013 4.4 with IEC 61672-1:2013 Table B.1",
    "Over the maximum only by the correction data: did not conform, and unusable past it",
)
def _chk_correction_data() -> Outcome:
    """The 8 kHz result of Clause 12, 0,15 dB over its maximum in total.

    Without the manufacturer's correction data its uncertainty is 0,01 dB
    inside the maximum, on it or 0,01 dB past it: 4.4 makes the first two a
    result that did not conform, and the last one is unusable (4.3), as the
    first sentence of 4.4 still holds the maximum.
    """
    maximum = _b1("Frequency weightings A, C, Z", 8000.0)
    verify = ph.metrology.verify_sound_level_meter_periodic
    states = {"just inside": -_PAST_DB, "at the maximum": 0.0, "past it": _PAST_DB}
    computed: dict[str, float] = {}
    for state, offset in states.items():
        result = verify(
            1,
            _record(
                acoustic_weighting_uncertainties_db=[0.3, maximum + 0.15],
                acoustic_weighting_uncertainties_without_correction_data_db=[
                    0.3,
                    maximum + offset,
                ],
            ),
        )
        four_four = result.over_maximum_by_correction_data == (("12", "8 kHz"),)
        computed[state] = float(
            four_four and result.failed == (("12", "8 kHz"),) and not result.unusable
        )
    return record(
        {"just inside": 1.0, "at the maximum": 1.0, "past it": 0.0},
        computed,
        label="4.4 inside and at the maximum, unusable (4.3) past it",
        computed_label=", ".join(
            f"{'4.4' if flag else 'not 4.4'} {state}"
            for state, flag in computed.items()
        ),
    )


@register(
    _SLM,
    "IEC 61672-3:2013 8.1 with IEC 61672-1:2013 5.1.10",
    "A class 2 meter with C-weighted peak owes C in 11.2, 13 and 14.2",
)
def _chk_c_from_peak() -> Outcome:
    record_a = _class_2(
        self_noise_electrical_db={"A": 12.1},
        electrical_weighting_deviations_db={"A": [0.0] * 8},
        electrical_weighting_uncertainties_db={"A": [0.15] * 8},
        weighting_at_1khz_deviations_db=None,
        weighting_at_1khz_uncertainties_db=None,
    )
    result = ph.metrology.verify_sound_level_meter_periodic(2, record_a)
    gaps = [
        result.missing == ("14.2",),
        [clause for clause, _ in result.incomplete] == ["11", "13"],
        "5.1.10" in result.incomplete[-1][1],
        not result.passes,
    ]
    return count(sum(gaps), len(gaps), subject="completeness findings")


@register(
    _SLM,
    "IEC 61672-3:2013 8.1, 14.1 and 20.1",
    "S tonebursts and an overload test show the displays 14.3 compares with F",
)
def _chk_displays_shown() -> Outcome:
    verify = ph.metrology.verify_sound_level_meter_periodic
    without = verify(
        1,
        _record(
            time_weighting_at_1khz_deviations_db=None,
            time_weighting_at_1khz_uncertainties_db=None,
        ),
    )
    only_s = verify(
        1,
        _record(
            time_weighting_at_1khz_deviations_db={"S": 0.0},
            time_weighting_at_1khz_uncertainties_db={"S": 0.1},
        ),
    )
    gaps = [
        without.missing == ("14.3",),
        not without.passes,
        [clause for clause, _ in only_s.incomplete] == ["14.3"],
        "20.1" in only_s.incomplete[0][1],
    ]
    return count(sum(gaps), len(gaps), subject="completeness findings")


@register(
    _SLM,
    "IEC 61672-3:2013 16.3, 17.3 and 17.4",
    "Steps short of 16.3, or a level range left out of 17.4, the reference one "
    "included, leave the test open",
)
def _chk_linearity_extent() -> Outcome:
    """The extent the procedures of Clauses 16 and 17 give their readings.

    The record of every step 16.3 takes, of 17.3 on the other level range
    and of 17.4 on both, is complete; one step at the starting point leaves
    16.3 short both up to the overload and down to the under-range; 17.4 on
    two of the three level ranges of a meter leaves 17.3 out and one range
    short; and 17.4 without its reading on the reference level range, which
    it tests "for each level range", leaves that reading out.
    """
    verify = ph.metrology.verify_sound_level_meter_periodic
    complete = verify(1, _record(), features=_METER)
    one_step = verify(
        1,
        _record(
            linearity_deviations_db=[0.0],
            linearity_uncertainties_db=[0.2],
            linearity_levels_db=[94.0],
        ),
        features=_METER,
    )
    one_range = verify(
        1,
        _record(
            range_linearity_deviations_db={"17.4": [0.0, 0.0]},
            range_linearity_uncertainties_db={"17.4": [0.2, 0.2]},
        ),
        features=ph.metrology.SoundLevelMeterFeatures(level_ranges=3),
    )
    no_reference = verify(
        1,
        _record(
            range_linearity_deviations_db={"17.3": [0.0], "17.4": [math.nan, 0.0]},
            range_linearity_uncertainties_db={"17.3": [0.2], "17.4": [math.nan, 0.2]},
        ),
        features=_METER,
    )
    findings = [
        complete.passes,
        [clause for clause, _ in one_step.incomplete] == ["16", "16"],
        not one_step.passes,
        [clause for clause, _ in one_range.incomplete] == ["17", "17"],
        not one_range.passes,
        [clause for clause, _ in no_reference.incomplete] == ["17"],
        not no_reference.passes,
    ]
    return count(sum(findings), len(findings), subject="completeness findings")


# --------------------------------------------------------------------------
# IEC 61672-3:2013 22 r), s) and t): the statements
# --------------------------------------------------------------------------
def _filled(template: str, meter_class: int) -> str:
    """A statement with class Y and the date replaced, as Clause 22 says."""
    return template.replace("class Y", f"class {meter_class}").replace(":–", ":2013")


def _statement_outcome(printed: str, built: str) -> Outcome:
    return count(int(printed == built), 1, subject="statement word for word")


@register(
    _SLM,
    "IEC 61672-3:2013 22 r)",
    "Statement of a pass with public pattern approval, class 1",
)
def _chk_statement_r() -> Outcome:
    result = ph.metrology.verify_sound_level_meter_periodic(
        1,
        _record(),
        pattern_approval_public=True,
        corrections_in_manual=True,
        features=_METER,
    )
    return _statement_outcome(_filled(ref.IEC61672_3_STATEMENT_R, 1), result.statement)


@register(
    _SLM,
    "IEC 61672-3:2013 22 s)",
    "Statement of a pass without public pattern approval, class 2",
)
def _chk_statement_s() -> Outcome:
    result = ph.metrology.verify_sound_level_meter_periodic(
        2, _class_2(), features=_METER
    )
    return _statement_outcome(_filled(ref.IEC61672_3_STATEMENT_S, 2), result.statement)


@register(_SLM, "IEC 61672-3:2013 22 t)", "Statement of a failure, class 1")
def _chk_statement_t() -> Outcome:
    result = ph.metrology.verify_sound_level_meter_periodic(
        1, _record(overload_difference_db=1.6), pattern_approval_public=True
    )
    head = _filled(ref.IEC61672_3_STATEMENT_T, 1)
    return _statement_outcome(head, result.statement[: len(head)])
