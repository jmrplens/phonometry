#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the ISO 8041-1:2017 saw-tooth signal-burst response (5.9).

Anchored on the printed pages: the test signal of Table 6 (folio 17) and the
indications of Tables 7, 8 and 9 (folios 17, 18 and 19), which the library
chain has to reproduce inside the tolerance printed beside each column.

Three of these tests are about conventions the tables do not print, and each
of them also runs the reading that was rejected, because a reproduction that
only ever tries the right convention proves nothing: the continuous row read
from the start time, the circular filtering of ``apply_weighting`` and a burst
started at the peak instead of at a zero crossing.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import vibration
from phonometry.vibration.human import signal_burst as sb

# Table 6 (folio 17): the angular frequency in radians per second, the hertz
# printed beside it, the start time, the repeat time and the duration.
TABLE_6_PRINTED = {
    "hand-arm": (500.0, 79.58, 0.2, 2.0, 12.0),
    "whole-body": (100.0, 15.915, 1.0, 10.0, 60.0),
    "low-frequency-whole-body": (2.5, 0.3979, 40.0, 400.0, 2400.0),
}

# Table 7 (folio 17), r.m.s. value, band limiting and Wh.
TABLE_7_PRINTED = {
    ("band-limiting", 1): 0.0448,
    ("band-limiting", 16): 0.179,
    ("band-limiting", None): 0.565,
    ("Wh", 1): 0.0103,
    ("Wh", 8): 0.0224,
    ("Wh", None): 0.0946,
}

# Table 8 (folios 18 and 19): r.m.s. value, VDV, MTVV linear, MTVV
# exponential, for the rows this file re-types from the page.
TABLE_8_PRINTED = {
    ("band-limiting", 1): (0.0433, 0.498, 0.137, 0.135),
    ("band-limiting", None): (0.546, 1.77, 0.547, 0.549),
    ("Wb", 2): (0.0435, 0.403, 0.137, 0.132),
    ("Wc", 8): (0.055, 0.374, 0.174, 0.153),
    ("Wd", None): (0.059, 0.197, 0.0611, 0.0594),
    ("We", 16): (0.0102, 0.0592, 0.0311, 0.0244),
    ("Wj", 4): (0.0874, 0.723, 0.277, 0.261),
    ("Wk", 1): (0.0299, 0.323, 0.0944, 0.0922),
    ("Wk", 16): (0.115, 0.648, 0.363, 0.289),
    ("Wk", None): (0.362, 1.15, 0.364, 0.363),
    ("Wm", None): (0.158, 0.52, 0.16, 0.159),
}

# Table 9 (folio 19): r.m.s. value and MSDV.
TABLE_9_PRINTED = {
    ("band-limiting", 1): (0.0341, 1.671),
    ("band-limiting", None): (0.439, 21.51),
    ("Wf", 1): (0.0197, 0.9651),
    ("Wf", 16): (0.0571, 2.797),
    ("Wf", None): (0.176, 8.622),
}


# ---------------------------------------------------------------------------
# Table 6: the test signal
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(("application", "printed"), TABLE_6_PRINTED.items())
def test_the_test_signal_is_table_6(
    application: str, printed: tuple[float, float, float, float, float]
) -> None:
    """Angular frequency, its hertz, start time, repeat time and duration."""
    omega, hertz, start, repeat, duration = printed
    test = sb.SAWTOOTH_BURST_TESTS[application]
    assert test.angular_frequency_rad_s == pytest.approx(omega)
    # The hertz are derived from the radians per second, so the decimal
    # printed beside them is the independent side of this check.
    assert test.frequency_hz == pytest.approx(hertz, rel=1e-4)
    assert test.start_time_s == pytest.approx(start)
    assert test.repeat_time_s == pytest.approx(repeat)
    assert test.duration_s == pytest.approx(duration)
    assert test.cycle_counts == (1, 2, 4, 8, 16)
    assert test.burst_count == 6


def test_table_6_covers_the_nine_weightings_once_each() -> None:
    """Each weighting is tested under exactly one application."""
    tested = [
        name for test in sb.SAWTOOTH_BURST_TESTS.values() for name in test.weightings
    ]
    assert sorted(tested) == sorted(vibration.WEIGHTING_NAMES)
    assert sb.SAWTOOTH_BURST_TESTS["whole-body"].weightings == (
        "Wb",
        "Wc",
        "Wd",
        "We",
        "Wj",
        "Wk",
        "Wm",
    )


def test_the_fall_time_limit_is_one_fifth_of_the_upper_corner() -> None:
    """12.13 (folio 36): no more than ``1/(5 f2)`` of Table 3.

    ``f2`` is 10**3,1 Hz for the hand-arm band limiting, 100 Hz for whole-body
    and 0,63 Hz for the low-frequency case, so the limits are 0,159 ms, 2 ms
    and 0,317 s.
    """
    limits = {
        application: test.max_fall_time_s
        for application, test in sb.SAWTOOTH_BURST_TESTS.items()
    }
    assert limits["hand-arm"] == pytest.approx(1.0 / (5.0 * 10.0**3.1))
    assert limits["hand-arm"] == pytest.approx(1.589e-4, rel=1e-3)
    assert limits["whole-body"] == pytest.approx(2e-3)
    assert limits["low-frequency-whole-body"] == pytest.approx(1.0 / (5.0 * 0.63))


def test_the_burst_is_a_rising_ramp_from_a_zero_crossing() -> None:
    """Figure 3 (folio 17): ramp up, vertical fall, zero at both ends."""
    fs = 20_000.0
    record = sb.sawtooth_burst("whole-body", 1, fs=fs)
    test = sb.SAWTOOTH_BURST_TESTS["whole-body"]
    period = 1.0 / test.frequency_hz
    start = round(test.start_time_s * fs)

    assert np.count_nonzero(record[:start]) == 0
    assert record[start] == pytest.approx(0.0, abs=1e-12)
    # One cycle: a single vertical fall of the full 2 m/s2, and a rise of the
    # same size at every other step, which is what a linear ramp is.
    burst = record[start : start + round(period * fs)]
    steps = np.diff(burst)
    falls = np.flatnonzero(steps < 0.0)
    assert falls.size == 1
    assert steps[falls[0]] < -1.99
    rises = np.delete(steps, falls)
    assert np.allclose(rises, rises[0], rtol=1e-9)
    assert burst.max() > 0.99
    assert burst.min() < -0.99
    # And the record still holds the bursts that come after this one.
    assert np.count_nonzero(record[start + round(period * fs) :]) > 0


def test_the_record_holds_six_bursts_at_the_printed_repeat_time() -> None:
    """Table 6: six bursts fit the printed duration in all three cases."""
    fs = 2_000.0
    record = sb.sawtooth_burst("whole-body", 4, fs=fs)
    test = sb.SAWTOOTH_BURST_TESTS["whole-body"]
    assert record.size == round(test.duration_s * fs)
    active = np.flatnonzero(np.abs(record) > 1e-9) / fs
    gaps = np.flatnonzero(np.diff(active) > 1.0)
    assert gaps.size + 1 == test.burst_count
    assert active[0] == pytest.approx(test.start_time_s, abs=2.0 / fs)


def test_the_continuous_row_starts_at_zero_not_at_the_start_time() -> None:
    """The convention that reproduces Table 7, and the one that does not.

    Filled from ``t = 0`` the band-limiting continuous cell of Table 7 comes
    out 0,564 9 against the 0,565 printed; started at the Table 6 start time
    it comes out 0,560 1, four times further away.
    """
    fs = 20_000.0
    continuous = sb.sawtooth_burst("hand-arm", None, fs=fs)
    test = sb.SAWTOOTH_BURST_TESTS["hand-arm"]
    assert np.max(np.abs(continuous[: round(test.start_time_s * fs)])) > 0.99

    printed = TABLE_7_PRINTED["band-limiting", None]
    from_zero = sb.signal_burst_indications("hand-arm", "band-limiting", None)["rms"]
    assert from_zero == pytest.approx(printed, rel=5e-3)

    delayed = continuous.copy()
    delayed[: round(test.start_time_s * fs)] = 0.0
    weighted = sb._zero_state_filter(delayed, fs, "Wh", band_limiting=True)
    late = float(np.sqrt(np.mean(weighted**2)))
    assert late == pytest.approx(0.5601, rel=5e-3)
    assert abs(late / printed - 1.0) > 4.0 * abs(from_zero / printed - 1.0)


def test_a_burst_started_at_the_peak_misses_the_printed_cell() -> None:
    """Figure 3's phase is load-bearing, not decorative.

    A saw-tooth that starts at its peak instead of at an upward zero crossing
    reads more than a quarter high on the single-cycle row of Table 8, which
    is over twice the printed tolerance.
    """
    fs = 20_000.0
    printed = TABLE_8_PRINTED["Wk", 1][0]
    test = sb.SAWTOOTH_BURST_TESTS["whole-body"]
    good = sb.sawtooth_burst("whole-body", 1, fs=fs)
    times = np.arange(good.size) / fs
    peak_phased = np.zeros_like(good)
    start = test.start_time_s
    span = 1.0 / test.frequency_hz
    for _ in range(test.burst_count):
        inside = (times >= start) & (times < start + span)
        cycles = test.frequency_hz * (times[inside] - start)
        peak_phased[inside] = 2.0 * np.mod(cycles, 1.0) - 1.0
        start += test.repeat_time_s

    def _rms(record: np.ndarray) -> float:
        weighted = sb._zero_state_filter(record, fs, "Wk", band_limiting=False)
        return float(np.sqrt(np.mean(weighted**2)))

    assert _rms(good) == pytest.approx(printed, rel=5e-3)
    assert _rms(peak_phased) / printed - 1.0 > 0.25


# ---------------------------------------------------------------------------
# Tables 7, 8 and 9 as data, and as an oracle
# ---------------------------------------------------------------------------
def test_the_response_table_has_every_printed_cell() -> None:
    """72 printed lines over the three tables, and 228 printed cells."""
    rows = sb.SIGNAL_BURST_RESPONSE
    assert len(rows) == 72
    assert sum(len(cells) for cells in rows.values()) == 228
    band_limiting = [key for key in rows if key[1] == sb.BAND_LIMITING]
    assert len(band_limiting) == 18
    per_application = {
        "hand-arm": ("rms",),
        "whole-body": ("rms", "vdv", "mtvv_linear", "mtvv_exponential"),
        "low-frequency-whole-body": ("rms", "msdv"),
    }
    for (application, row, cycles), cells in rows.items():
        test = sb.SAWTOOTH_BURST_TESTS[application]
        assert row == sb.BAND_LIMITING or row in test.weightings
        assert cycles is None or cycles in test.cycle_counts
        assert tuple(cells) == per_application[application]


def test_the_tolerance_is_ten_per_cent_except_the_dose_value() -> None:
    """Every printed column is 10 %, and the VDV column is 12 %."""
    assert sb.BURST_TOLERANCE_PERCENT["vdv"] == pytest.approx(12.0)
    for quantity, tolerance in sb.BURST_TOLERANCE_PERCENT.items():
        if quantity != "vdv":
            assert tolerance == pytest.approx(10.0), quantity


@pytest.mark.parametrize(("key", "printed"), TABLE_7_PRINTED.items())
def test_table_7_is_transcribed(key: tuple[str, int | None], printed: float) -> None:
    row, cycles = key
    assert sb.SIGNAL_BURST_RESPONSE["hand-arm", row, cycles]["rms"] == printed


@pytest.mark.parametrize(("key", "printed"), TABLE_8_PRINTED.items())
def test_table_8_is_transcribed(
    key: tuple[str, int | None], printed: tuple[float, ...]
) -> None:
    row, cycles = key
    cells = sb.SIGNAL_BURST_RESPONSE["whole-body", row, cycles]
    assert tuple(cells.values()) == printed


@pytest.mark.parametrize(("key", "printed"), TABLE_9_PRINTED.items())
def test_table_9_is_transcribed(
    key: tuple[str, int | None], printed: tuple[float, ...]
) -> None:
    row, cycles = key
    cells = sb.SIGNAL_BURST_RESPONSE["low-frequency-whole-body", row, cycles]
    assert tuple(cells.values()) == printed


@pytest.mark.parametrize(
    ("row", "cycles"), [("band-limiting", 1), ("band-limiting", None), ("Wh", 1)]
)
def test_the_library_reproduces_table_7(row: str, cycles: int | None) -> None:
    """Hand-arm, r.m.s. value: the printed cell to better than 0,5 %."""
    printed = TABLE_7_PRINTED[row, cycles]
    got = sb.signal_burst_indications("hand-arm", row, cycles, fs=50_000.0)["rms"]
    assert got == pytest.approx(printed, rel=5e-3)


@pytest.mark.parametrize(
    ("row", "cycles"), [("band-limiting", 1), ("Wk", 1), ("Wk", 16), ("Wk", None)]
)
def test_the_library_reproduces_table_8(row: str, cycles: int | None) -> None:
    """Whole-body, all four printed columns at once, to better than 0,5 %.

    The continuous row of ``Wk`` is the interesting one: its linear MTVV is
    0,364 05 against the 0,364 printed, and it only lands there because the
    filtering starts from rest.
    """
    printed = dict(
        zip(
            ("rms", "vdv", "mtvv_linear", "mtvv_exponential"),
            TABLE_8_PRINTED[row, cycles],
            strict=True,
        )
    )
    got = sb.signal_burst_indications("whole-body", row, cycles, fs=5_000.0)
    for quantity, value in printed.items():
        assert got[quantity] == pytest.approx(value, rel=5e-3), quantity


@pytest.mark.parametrize(
    ("row", "cycles"), [("band-limiting", 1), ("Wf", 1), ("Wf", 16)]
)
def test_the_library_reproduces_table_9(row: str, cycles: int | None) -> None:
    """Low-frequency whole-body: r.m.s. value and MSDV, to better than 1 %."""
    printed = dict(zip(("rms", "msdv"), TABLE_9_PRINTED[row, cycles], strict=True))
    got = sb.signal_burst_indications("low-frequency-whole-body", row, cycles)
    for quantity, value in printed.items():
        assert got[quantity] == pytest.approx(value, rel=1e-2), quantity


def test_the_msdv_is_the_rms_over_the_printed_duration() -> None:
    """Table 9 closes on itself: MSDV = r.m.s. times the square root of 2 400 s.

    The cleanest evidence that the measurement duration of the continuous row
    is the printed one: 0,439 times sqrt(2 400) is 21,51, the printed cell.
    """
    rms, msdv = TABLE_9_PRINTED["band-limiting", None]
    duration = sb.SAWTOOTH_BURST_TESTS["low-frequency-whole-body"].duration_s
    assert rms * math.sqrt(duration) == pytest.approx(msdv, rel=2e-3)


def test_zero_state_filtering_is_what_lands_on_the_continuous_cells() -> None:
    """The second convention, with the reading it replaced.

    Filtered circularly, the linear MTVV of the ``Wd`` continuous row of
    Table 8 sits 3,2 % low, and ``We`` 5,2 % low, because the wrap-around
    erases the switch-on transient the linear MTVV is built to catch. From
    rest they sit inside half a per cent.
    """
    fs = 5_000.0
    for name, printed in (("Wd", 0.0611), ("We", 0.0311)):
        record = sb.sawtooth_burst("whole-body", None, fs=fs)
        circular = vibration.apply_weighting(record, fs, name=name)
        wrapped = float(
            np.max(vibration.running_rms(circular, fs, integration_time=1.0))
        )
        from_rest = sb.signal_burst_indications("whole-body", name, None, fs=fs)[
            "mtvv_linear"
        ]
        assert wrapped / printed - 1.0 < -0.02, name
        assert from_rest == pytest.approx(printed, rel=5e-3), name


def test_the_band_limiting_row_uses_the_shared_corner_pair() -> None:
    """Six of the seven whole-body weightings share 0,4 Hz and 100 Hz.

    ``Wm`` does not, and its corners miss the printed band-limiting row by
    more than the shared pair does, which is how the row was decided.
    """
    assert sb.SAWTOOTH_BURST_TESTS["whole-body"].band_limiting_weighting == "Wb"
    fs = 5_000.0
    printed = TABLE_8_PRINTED["band-limiting", 1][0]
    record = sb.sawtooth_burst("whole-body", 1, fs=fs)
    shared = float(
        np.sqrt(
            np.mean(sb._zero_state_filter(record, fs, "Wb", band_limiting=True) ** 2)
        )
    )
    other = float(
        np.sqrt(
            np.mean(sb._zero_state_filter(record, fs, "Wm", band_limiting=True) ** 2)
        )
    )
    assert shared == pytest.approx(printed, rel=5e-3)
    assert abs(other / printed - 1.0) > abs(shared / printed - 1.0)


# ---------------------------------------------------------------------------
# The generator refuses what the clause does not define
# ---------------------------------------------------------------------------
def test_an_unknown_application_is_refused() -> None:
    with pytest.raises(ValueError, match="'application' must be one of"):
        sb.sawtooth_burst("hand", 1, fs=20_000.0)
    assert sb.sawtooth_burst("hand-arm", 1, fs=20_000.0).size > 0


def test_a_weighting_of_another_application_is_refused() -> None:
    """Table 6 pairs each weighting with one application and only one."""
    with pytest.raises(ValueError, match="'name' must be one of"):
        sb.signal_burst_indications("hand-arm", "Wk", 1)
    assert sb.signal_burst_indications("whole-body", "Wk", 1, fs=2_000.0)


def test_a_burst_length_the_tables_do_not_print_is_refused() -> None:
    """Four cycles is a printed row; three is not, and has no expected cell."""
    with pytest.raises(ValueError, match=r"'cycles' must be one of \(1, 2, 4, 8, 16\)"):
        sb.sawtooth_burst("whole-body", 3, fs=2_000.0)
    assert sb.sawtooth_burst("whole-body", 4, fs=2_000.0).size > 0


def test_a_non_integer_burst_length_is_refused() -> None:
    with pytest.raises(TypeError, match="'cycles' must be an integer"):
        sb.sawtooth_burst("whole-body", 4.0, fs=2_000.0)  # type: ignore[arg-type]


def test_a_sampling_rate_below_the_band_limit_is_refused() -> None:
    """Twice the upper band-limiting corner of Table 3 is the floor."""
    with pytest.raises(ValueError, match="'fs' must exceed 200 Hz"):
        sb.sawtooth_burst("whole-body", 1, fs=200.0)
    assert sb.sawtooth_burst("whole-body", 1, fs=200.5).size > 0


def test_a_non_positive_sampling_rate_or_amplitude_is_refused() -> None:
    with pytest.raises(ValueError, match="'fs' must be a positive"):
        sb.sawtooth_burst("whole-body", 1, fs=0.0)
    with pytest.raises(ValueError, match="'amplitude_m_s2' must be positive"):
        sb.sawtooth_burst("whole-body", 1, fs=2_000.0, amplitude_m_s2=0.0)
    assert sb.sawtooth_burst("whole-body", 1, fs=2_000.0, amplitude_m_s2=0.5).size > 0


def test_the_amplitude_scales_the_record() -> None:
    """5.9: the printed responses are for 1 m/s2 and scale with the signal."""
    unit = sb.sawtooth_burst("whole-body", 2, fs=2_000.0)
    doubled = sb.sawtooth_burst("whole-body", 2, fs=2_000.0, amplitude_m_s2=2.0)
    assert np.allclose(doubled, 2.0 * unit)


# ---------------------------------------------------------------------------
# The verdict
# ---------------------------------------------------------------------------
def _printed_rows(application: str, name: str) -> dict[int | None, dict[str, float]]:
    """The printed row as a laboratory would report it."""
    test = sb.SAWTOOTH_BURST_TESTS[application]
    return {
        cycles: dict(sb.SIGNAL_BURST_RESPONSE[application, name, cycles])
        for cycles in (*test.cycle_counts, None)
    }


def test_the_printed_table_passes_its_own_verdict() -> None:
    measured = _printed_rows("whole-body", "Wk")
    verdict = sb.verify_signal_burst_response("whole-body", "Wk", measured)
    assert verdict.passes
    assert verdict.cycle_counts == (1, 2, 4, 8, 16, None)
    assert verdict.quantities == ("rms", "vdv", "mtvv_linear", "mtvv_exponential")
    assert verdict.deviation_percent == pytest.approx(np.zeros((6, 4)))
    assert verdict.worst_deviation_percent == pytest.approx(0.0)


def test_the_verdict_turns_over_at_the_printed_tolerance() -> None:
    """Inside 10 % passes, outside fails, one cell at a time."""
    for factor, expected in ((1.099, True), (1.101, False)):
        measured = _printed_rows("hand-arm", "Wh")
        measured[4]["rms"] *= factor
        verdict = sb.verify_signal_burst_response("hand-arm", "Wh", measured)
        assert verdict.passes is expected
        assert verdict.worst_deviation_percent == pytest.approx(
            (factor - 1.0) * 100.0, rel=1e-6
        )


def test_the_dose_value_column_is_allowed_twelve_per_cent() -> None:
    """The same 11 % error passes as a VDV and fails as an r.m.s. value."""
    measured = _printed_rows("whole-body", "Wb")
    measured[2]["vdv"] *= 1.11
    assert sb.verify_signal_burst_response("whole-body", "Wb", measured).passes

    measured = _printed_rows("whole-body", "Wb")
    measured[2]["rms"] *= 1.11
    assert not sb.verify_signal_burst_response("whole-body", "Wb", measured).passes


def test_the_printed_responses_scale_with_the_test_amplitude() -> None:
    """5.9 (folio 16): multiply the printed response by the amplitude."""
    measured = {
        cycles: {"rms": 4.0 * value["rms"]}
        for cycles, value in _printed_rows("hand-arm", "band-limiting").items()
    }
    verdict = sb.verify_signal_burst_response(
        "hand-arm", "band-limiting", measured, amplitude_m_s2=4.0
    )
    assert verdict.passes
    assert verdict.printed[0, 0] == pytest.approx(4.0 * 0.0448)
    assert not sb.verify_signal_burst_response(
        "hand-arm", "band-limiting", measured
    ).passes


def test_a_subset_of_rows_and_columns_is_a_valid_verdict() -> None:
    """A laboratory that measured two rows and one column gets a verdict."""
    verdict = sb.verify_signal_burst_response(
        "whole-body",
        "Wk",
        {16: {"rms": 0.115}, 1: {"rms": 0.0299}},
    )
    assert verdict.cycle_counts == (1, 16)
    assert verdict.quantities == ("rms",)
    assert verdict.passes


def test_the_verdict_refuses_what_it_cannot_judge() -> None:
    with pytest.raises(ValueError, match="'measured' must report at least one"):
        sb.verify_signal_burst_response("whole-body", "Wk", {})
    with pytest.raises(ValueError, match=r"'cycles' must be one of"):
        sb.verify_signal_burst_response("whole-body", "Wk", {3: {"rms": 0.03}})
    with pytest.raises(ValueError, match="does not print"):
        sb.verify_signal_burst_response("whole-body", "Wk", {1: {"msdv": 0.03}})
    with pytest.raises(ValueError, match="has to report the same columns"):
        sb.verify_signal_burst_response(
            "whole-body", "Wk", {1: {"rms": 0.0299}, 2: {"vdv": 0.38}}
        )
    with pytest.raises(ValueError, match="'measured' must be non-negative"):
        sb.verify_signal_burst_response("whole-body", "Wk", {1: {"rms": float("nan")}})
    with pytest.raises(ValueError, match="'measured' must be non-negative"):
        sb.verify_signal_burst_response("whole-body", "Wk", {1: {"rms": -0.0299}})
    assert sb.verify_signal_burst_response("whole-body", "Wk", {1: {"rms": 0.0}})
    with pytest.raises(ValueError, match="'amplitude_m_s2' must be positive"):
        sb.verify_signal_burst_response(
            "whole-body", "Wk", {1: {"rms": 0.0299}}, amplitude_m_s2=-1.0
        )


def test_the_verdict_reports_the_cell_that_failed() -> None:
    measured = _printed_rows("low-frequency-whole-body", "Wf")
    measured[8]["msdv"] *= 1.2
    verdict = sb.verify_signal_burst_response(
        "low-frequency-whole-body", "Wf", measured
    )
    assert not verdict.passes
    failed = np.argwhere(~verdict.within_tolerance)
    assert failed.tolist() == [[3, 1]]
    assert verdict.cycle_counts[3] == 8
    assert verdict.quantities[1] == "msdv"


# ---------------------------------------------------------------------------
# The figure
# ---------------------------------------------------------------------------
def _verdict() -> sb.SignalBurstVerification:
    measured = _printed_rows("whole-body", "Wk")
    measured[4]["mtvv_linear"] *= 1.06
    return sb.verify_signal_burst_response("whole-body", "Wk", measured)


def test_the_plot_draws_one_series_per_printed_column() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    ax = _verdict().plot()
    labels = ax.get_legend_handles_labels()[1]
    assert labels == [
        r"printed tolerance $\pm$10 %",
        r"printed tolerance $\pm$12 % (VDV)",
        "r.m.s. value",
        "VDV",
        "MTVV linear",
        "MTVV exponential",
    ]
    assert [text.get_text() for text in ax.get_xticklabels()] == [
        "1",
        "2",
        "4",
        "8",
        "16",
        "continuous",
    ]
    assert ax.get_ylabel() == "Deviation [%]"
    assert ax.get_title() == "Signal-burst response (ISO 8041-1)\nWk, whole-body"
    # The 12 % pair of the VDV column is drawn as its own dashed edge, on top
    # of the shaded 10 % band and the zero line.
    dashed = [line for line in ax.get_lines() if line.get_linestyle() == "--"]
    assert len(dashed) == 2
    assert sorted(line.get_ydata()[0] for line in dashed) == [-12.0, 12.0]


def test_the_plot_speaks_spanish_and_takes_a_kwarg_alias() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    ax = _verdict().plot(language="es", c="k")
    assert ax.get_xlabel() == "Ciclos de diente de sierra por ráfaga"
    assert ax.get_ylabel() == "Desviación [%]"
    assert ax.get_title() == (
        "Respuesta a ráfaga de señal (ISO 8041-1)\nWk, cuerpo entero"
    )
    assert [text.get_text() for text in ax.get_xticklabels()][-1] == "continua"
    series = [line for line in ax.get_lines() if line.get_marker() not in ("", "None")]
    assert len(series) == 4
    assert all(line.get_color() == "k" for line in series)


def test_the_band_limiting_row_is_named_in_the_title() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib as mpl

    mpl.use("Agg")
    measured = _printed_rows("low-frequency-whole-body", "band-limiting")
    verdict = sb.verify_signal_burst_response(
        "low-frequency-whole-body", "band-limiting", measured
    )
    ax = verdict.plot()
    assert ax.get_title() == (
        "Signal-burst response (ISO 8041-1)\nband limiting, low-frequency whole-body"
    )
    ax_es = verdict.plot(language="es")
    assert ax_es.get_title() == (
        "Respuesta a ráfaga de señal (ISO 8041-1)\n"
        "limitación de banda, cuerpo entero de baja frecuencia"
    )
