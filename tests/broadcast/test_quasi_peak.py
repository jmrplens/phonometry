#  Copyright (c) 2026. Jose Manuel Requena Plens
"""ITU-R BS.468-4 clause 2: the psophometric quasi-peak programme-level meter.

Clause 2 prints no time constant, no rise time and no transfer function. It
specifies the detector through eleven acceptance windows (Tables 2 and 3),
one absolute calibration (clause 2.6) and four small requirements that a
float64 chain satisfies by construction. This file is organised the same
way, and each group says which of the three it is:

* **Conformance.** The eleven windows, run at five sample rates. This is the
  whole conformance statement the Recommendation authorises for a detector.
* **A self-imposed regression bound.** How close the readings sit to the
  *reference* column, which the standard does not require them to match, and
  how little they move between sample rates.
* **True by construction.** Clauses 2.1 (attenuators), 2.3 (overload
  linearity), 2.4 (reversibility) and 2.5 (overswing). Rectification,
  first-order recursions and a maximum are positively homogeneous and cannot
  overshoot a monotone step, so these pass exactly rather than nearly. They
  are kept as live tests because the first three would catch a chain that
  stopped being homogeneous and the fourth would catch a second-order
  reading device added for realism.

The windows themselves are transcribed in ``tests/reference_data/broadcast``
from the rendered page, independently of the copy the module carries.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import FrozenInstanceError, replace
from pathlib import Path

import numpy as np
import pytest
from reference_data import (
    BS468_BURST_HZ,
    BS468_CALIBRATION_V,
    BS468_OVERLOAD_BURST_MS,
    BS468_OVERLOAD_RANGE_DB,
    BS468_OVERLOAD_TOL_DB,
    BS468_OVERSWING_TOL_DB,
    BS468_REVERSIBILITY_TOL_DB,
    BS468_TABLE2_SINGLE_BURSTS,
    BS468_TABLE3_BURST_TRAINS,
)

from phonometry.broadcast import (
    BS468_BALLISTICS,
    DBQPS_REFERENCE_V,
    QuasiPeakBallistics,
    QuasiPeakDynamicsResult,
    QuasiPeakResult,
    quasi_peak_meter,
    verify_quasi_peak_dynamics,
)
from phonometry.broadcast import quasi_peak as quasi_peak_module
from phonometry.io import Signal
from phonometry.signals import tone_burst

FS = 48000.0

#: The rates the ballistics are checked over. 32 kHz is the lowest broadcast
#: rate, 192 kHz the highest this library designs the network at, and
#: 44.1 kHz is the one where the 25-cycle burst is not sample-exact.
RATES = (32000.0, 44100.0, FS, 96000.0, 192000.0)

#: Self-imposed, not from BS.468-4: how far a reading may sit from the
#: *reference* reading printed in Tables 2 and 3. The worst of the eleven is
#: 0.148 dB, at 10 bursts per second. The reference is printed to two
#: significant figures on nine of the eleven cells, so its own quantum is
#: 0.027 to 0.108 dB and nothing tighter than this would be meaningful.
REFERENCE_BOUND_DB = 0.15

#: Self-imposed: how much of its own acceptance window a reading may spend on
#: moving between sample rates. The worst of the eleven is 1.80 %, at 100
#: bursts per second, whose window is the narrowest in the document.
RATE_SPREAD_FRACTION = 0.05


def _steady_sine(rms: float, fs: float, seconds: float = 3.0) -> np.ndarray:
    """A settled sine of *rms* volts at 1 kHz, the clause 2.6 stimulus."""
    t = np.arange(int(round(seconds * fs))) / fs
    return math.sqrt(2.0) * rms * np.sin(2.0 * math.pi * 1000.0 * t)


@pytest.fixture(scope="module")
def dynamics() -> dict[float, QuasiPeakDynamicsResult]:
    """The eleven windows at every rate, computed once for the whole module.

    44.1 kHz warns from ``tone_burst``: 25 cycles of 5 kHz span 220.5 samples
    there, so the gate cannot close on the tone's final zero crossing. The
    warning is correct, and gating the burst a whole sample later moves the
    reading by under 0.0001 dB against a 2.626 dB window, which
    :func:`test_the_44_1_khz_gate_moves_the_reading_by_less_than_published`
    measures and :func:`test_a_reading_barely_moves_between_sample_rates`
    holds with the other ten.
    """
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=r".*incommensurate with fs.*")
        return {fs: verify_quasi_peak_dynamics(fs) for fs in RATES}


# ---------------------------------------------------------------------------
# Conformance: the eleven acceptance windows of Tables 2 and 3
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("duration_ms", "lower", "upper"),
    [(d, lo, hi) for d, _cycles, lo, _ref, hi in BS468_TABLE2_SINGLE_BURSTS],
    ids=[f"{d:g}ms" for d, *_ in BS468_TABLE2_SINGLE_BURSTS],
)
def test_a_single_burst_lands_inside_its_table_2_window(
    dynamics: dict[float, QuasiPeakDynamicsResult],
    duration_ms: float,
    lower: float,
    upper: float,
) -> None:
    """Table 2: one 5 kHz burst of an integral number of periods, weighted."""
    rows = dynamics[FS].stimuli
    assert isinstance(rows, tuple)
    row = next(r for r in rows if r["stimulus"] == f"{duration_ms:g} ms")
    assert lower <= row["reading_percent"] <= upper


@pytest.mark.parametrize(
    ("rate", "lower", "upper"),
    [(r, lo, hi) for r, lo, _ref, hi in BS468_TABLE3_BURST_TRAINS],
    ids=[f"{r:g}per_s" for r, *_ in BS468_TABLE3_BURST_TRAINS],
)
def test_a_burst_train_lands_inside_its_table_3_window(
    dynamics: dict[float, QuasiPeakDynamicsResult],
    rate: float,
    lower: float,
    upper: float,
) -> None:
    """Table 3: 5 ms bursts at 2, 10 and 100 per second, the decay constraint."""
    rows = dynamics[FS].stimuli
    assert isinstance(rows, tuple)
    row = next(r for r in rows if r["stimulus"] == f"{rate:g} bursts/s")
    assert lower <= row["reading_percent"] <= upper


@pytest.mark.parametrize("fs", RATES, ids=[f"{f:g}Hz" for f in RATES])
def test_every_window_is_met_at_every_sample_rate(
    dynamics: dict[float, QuasiPeakDynamicsResult], fs: float
) -> None:
    """The verifier's own verdict, at each rate, with the margin it reports."""
    report = dynamics[fs]
    assert report.passes
    assert report.fs == fs
    margin = report.worst_margin_db
    assert isinstance(margin, float)
    assert margin > 0.0


def test_the_verifier_reports_all_eleven_stimuli(
    dynamics: dict[float, QuasiPeakDynamicsResult],
) -> None:
    """Eight single bursts and three trains, each with its printed window."""
    rows = dynamics[FS].stimuli
    assert isinstance(rows, tuple)
    assert len(rows) == len(BS468_TABLE2_SINGLE_BURSTS) + len(BS468_TABLE3_BURST_TRAINS)
    printed = {
        f"{d:g} ms": (lo, ref, hi)
        for d, _cycles, lo, ref, hi in BS468_TABLE2_SINGLE_BURSTS
    }
    printed |= {
        f"{r:g} bursts/s": (lo, ref, hi) for r, lo, ref, hi in BS468_TABLE3_BURST_TRAINS
    }
    for row in rows:
        lower, reference, upper = printed[row["stimulus"]]
        assert (
            row["lower_percent"],
            row["reference_percent"],
            row["upper_percent"],
        ) == (
            lower,
            reference,
            upper,
        )


# ---------------------------------------------------------------------------
# Self-imposed regression bounds: the reference column and the sample rate
# ---------------------------------------------------------------------------


def test_the_readings_stay_near_the_printed_reference_column(
    dynamics: dict[float, QuasiPeakDynamicsResult],
) -> None:
    """Not conformance: BS.468-4 requires the window, not the reference.

    Pinned anyway, because the windows are 0.5 to 4.0 dB wide and a refit
    that moved a reading by a decibel would still pass every one of them.
    """
    worst = dynamics[FS].worst_deviation_db
    assert isinstance(worst, float)
    assert worst < REFERENCE_BOUND_DB


@pytest.mark.parametrize(
    "stimulus",
    [f"{d:g} ms" for d, *_ in BS468_TABLE2_SINGLE_BURSTS]
    + [f"{r:g} bursts/s" for r, *_ in BS468_TABLE3_BURST_TRAINS],
)
def test_a_reading_barely_moves_between_sample_rates(
    dynamics: dict[float, QuasiPeakDynamicsResult], stimulus: str
) -> None:
    """The property the whole discretisation rests on, per stimulus.

    A peak follower on raw rectified samples reads the largest *sample*, not
    the largest value of the waveform, and that deficit is rate dependent (a
    5 kHz sine can be read 0.47 dB low at 48 kHz). This chain never takes
    such a peak: the 1.41 ms charge spans fourteen half-periods of the
    rectified carrier, so the ripple is gone before any maximum is taken.
    """
    readings = []
    window_db = 0.0
    for fs in RATES:
        rows = dynamics[fs].stimuli
        assert isinstance(rows, tuple)
        row = next(r for r in rows if r["stimulus"] == stimulus)
        readings.append(row["reading_percent"])
        window_db = 20.0 * math.log10(row["upper_percent"] / row["lower_percent"])
    spread_db = 20.0 * math.log10(max(readings) / min(readings))
    assert spread_db < RATE_SPREAD_FRACTION * window_db


# ---------------------------------------------------------------------------
# Clause 2.6: the one absolute statement in clause 2
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fs", RATES, ids=[f"{f:g}Hz" for f in RATES])
def test_a_steady_1_khz_sine_at_0_775_volts_reads_0_dbqps(fs: float) -> None:
    """Clause 2.6, the sentence that fixes the scale of the whole instrument.

    It is an equality, not a tolerance, so it is checked as one: the scale
    factor is measured per rate rather than frozen at 48 kHz, which is what
    keeps this exact at 32 and 192 kHz too.
    """
    result = quasi_peak_meter(_steady_sine(BS468_CALIBRATION_V, fs), fs)
    assert result.reading == pytest.approx(BS468_CALIBRATION_V, abs=1e-12)
    assert result.level == pytest.approx(0.0, abs=1e-9)
    assert result.level_unit == "dBqps"


def test_the_detector_reads_the_rms_of_a_steady_sine_not_its_peak() -> None:
    """The consequence of clause 2.6 an implementer trips over first."""
    peak = 2.0
    result = quasi_peak_meter(_steady_sine(peak / math.sqrt(2.0), FS), FS)
    assert result.reading == pytest.approx(peak / math.sqrt(2.0), rel=1e-9)


# ---------------------------------------------------------------------------
# True by construction: clauses 2.1, 2.3, 2.4 and 2.5
# ---------------------------------------------------------------------------


def test_scaling_the_input_scales_the_reading_by_the_same_factor() -> None:
    """Clause 2.1's two attenuator variants, which cannot disagree here.

    The tests are run "without adjusting the attenuators" and again with them
    reset per duration. A chain of rectification, first-order recursions and
    a maximum is positively homogeneous, so the two variants are the same
    measurement and "80 % of full scale" constrains the bench, not the
    quantity. That is also why this module models no full scale at all.
    """
    burst = tone_burst(FS, BS468_BURST_HZ, 250, post_silence=0.5).signal
    plain = quasi_peak_meter(burst, FS).reading
    scaled = quasi_peak_meter(3.7 * burst, FS).reading
    assert scaled == pytest.approx(3.7 * plain, rel=1e-12)


def test_the_reading_tracks_over_20_db_of_short_bursts() -> None:
    """Clause 2.3: isolated 0.6 ms bursts stepped down 20 dB, within +-1 dB.

    The only clause that exercises a burst shorter than Table 2's shortest,
    and the only one that reaches three whole carrier periods. In float64 it
    passes on the same homogeneity as clause 2.1, so the residual is rounding
    and the +-1 dB allowance is spent to fourteen decimal places.

    Three periods of 5 kHz span 28.8 samples at 48 kHz, the one stimulus in
    the Recommendation whose gate cannot close on a zero crossing there
    (every Table 2 and Table 3 duration is a multiple of five periods and so
    is sample-exact). ``tone_burst`` says so, and it makes no difference to a
    test that only compares scaled copies of the very same burst.
    """
    cycles = round(BS468_OVERLOAD_BURST_MS * 1e-3 * BS468_BURST_HZ)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=r".*incommensurate with fs.*")
        burst = tone_burst(FS, BS468_BURST_HZ, cycles, post_silence=0.5).signal
    top = quasi_peak_meter(burst, FS).level
    for step_db in np.linspace(0.0, BS468_OVERLOAD_RANGE_DB, 5):
        attenuated = quasi_peak_meter(10.0 ** (-step_db / 20.0) * burst, FS).level
        assert abs((top - attenuated) - step_db) < BS468_OVERLOAD_TOL_DB
        assert (top - attenuated) == pytest.approx(step_db, abs=1e-12)


def test_reversing_the_polarity_leaves_the_reading_unchanged() -> None:
    """Clause 2.4: 1 ms d.c. pulses at 100 per second, in the unweighted mode.

    The only test the Recommendation runs without the weighting network, and
    for the right reason: the network has a zero at the origin and would kill
    a d.c. pulse train. Full-wave rectification as ``abs(x)`` makes the
    difference exactly zero rather than merely under the 0.5 dB limit.
    """
    n = int(round(0.5 * FS))
    pulses = np.zeros(n)
    period = int(round(FS / 100.0))
    width = int(round(1e-3 * FS))
    for start in range(0, n - period, period):
        pulses[start : start + width] = 0.8
    forward = quasi_peak_meter(pulses, FS, weighting="Z").level
    reversed_ = quasi_peak_meter(-pulses, FS, weighting="Z").level
    assert abs(forward - reversed_) < BS468_REVERSIBILITY_TOL_DB
    assert forward == reversed_


def test_a_suddenly_applied_tone_does_not_overswing() -> None:
    """Clause 2.5: less than 0.3 dB of momentary excess reading.

    A cascade of first-order elements driven by a monotone step cannot
    overshoot, so the whole allowance goes unspent. The test earns its keep
    the day anyone gives the reading device a second order for realism.
    """
    tone = _steady_sine(BS468_CALIBRATION_V, FS)
    result = quasi_peak_meter(np.concatenate([np.zeros(int(FS // 10)), tone]), FS)
    # The settled indication is the needle over the last second, ripple and
    # all; the momentary reading is its largest excursion over the whole
    # record, transient included. Anything the transient adds shows up as the
    # difference between the two.
    settled = float(result.trace[-int(FS) :].max())
    excess_db = 20.0 * math.log10(result.reading / settled)
    assert excess_db < BS468_OVERSWING_TOL_DB
    assert excess_db == pytest.approx(0.0, abs=1e-12)


# ---------------------------------------------------------------------------
# The result object
# ---------------------------------------------------------------------------


def test_the_trace_is_the_needle_over_the_record_the_caller_gave() -> None:
    """One sample of trace per sample of record, and the reading is its peak.

    The record is padded with silence before the weighting network and
    un-padded after, so the trace the caller gets back covers their record
    and nothing else.
    """
    burst = tone_burst(FS, BS468_BURST_HZ, 500, post_silence=0.5).signal
    result = quasi_peak_meter(burst, FS)
    assert result.trace.shape == burst.shape
    assert result.times.size == burst.size
    assert result.reading == float(result.trace.max())
    assert result.fs == FS
    assert result.weighting == "468"


def test_the_reading_does_not_depend_on_where_the_record_ends() -> None:
    """What the padding before the weighting network is there to guarantee.

    The polyphase resampler's last output sample sits on an incomplete
    window and comes out 5.1 % above the settled peak of a weighted 5 kHz
    tone. Cutting a settled record at four consecutive samples therefore
    hands the detector four different final values, and the reading must not
    be able to tell: it is a measurement of the record, not of its last
    sample. The 1.41 ms charge already absorbs almost all of that on its own,
    which is why the tolerance here is tight rather than generous.
    """
    t = np.arange(int(3.0 * FS)) / FS
    tone = np.sin(2.0 * math.pi * BS468_BURST_HZ * t)
    cut = tone.size - 4
    readings = [quasi_peak_meter(tone[: cut + k], FS).reading for k in range(4)]
    assert max(readings) - min(readings) < 1e-7 * min(readings)


def test_switching_out_the_weighting_network_changes_the_reading() -> None:
    """Clause 2's preamble: every test but 2.4 runs through the network."""
    burst = tone_burst(FS, BS468_BURST_HZ, 25, post_silence=0.5).signal
    weighted = quasi_peak_meter(burst, FS)
    unweighted = quasi_peak_meter(burst, FS, weighting="Z")
    assert weighted.weighting == "468"
    assert unweighted.weighting == "Z"
    # The network is +11.7 dB at 5 kHz, so the weighted reading is far larger.
    assert weighted.reading > 3.0 * unweighted.reading


_468_OR_Z = r"'weighting' must be one of \('468', 'Z'\); got 'A'"


def test_the_meter_refuses_a_weighting_it_does_not_have() -> None:
    """The meter has the BS.468-4 network or none; an A-weighting is not none."""
    burst = tone_burst(FS, BS468_BURST_HZ, 25, post_silence=0.5).signal
    with pytest.raises(ValueError, match=_468_OR_Z):
        quasi_peak_meter(burst, FS, weighting="A")  # type: ignore[arg-type]


def test_a_reading_built_by_hand_refuses_another_weighting() -> None:
    burst = tone_burst(FS, BS468_BURST_HZ, 25, post_silence=0.5).signal
    result = quasi_peak_meter(burst, FS)
    with pytest.raises(ValueError, match=_468_OR_Z):
        replace(result, weighting="A")


@pytest.mark.parametrize(
    ("reference", "expected"),
    [
        (DBQPS_REFERENCE_V, "dBqps"),
        (2e-5, "dB re 20 uPa"),
        (1.0, "dB re 1"),
    ],
)
def test_the_level_names_the_scale_it_is_on(reference: float, expected: str) -> None:
    """Only 0.775 V earns the name dBqps; clause 3 gives no other scale one."""
    result = quasi_peak_meter(
        _steady_sine(0.775, FS, seconds=1.0), FS, reference=reference
    )
    assert result.level_unit == expected


def test_a_silent_record_reads_minus_infinity() -> None:
    """No excursion at all is a level of ``-inf``, not a division by zero."""
    result = quasi_peak_meter(np.zeros(4800), FS)
    assert result.reading == 0.0
    assert result.level == -math.inf


def test_the_result_is_frozen() -> None:
    """A measurement is a record of what happened, not a mutable buffer."""
    result = quasi_peak_meter(_steady_sine(0.775, FS, seconds=0.5), FS)
    with pytest.raises(FrozenInstanceError):
        result.reading = 1.0  # type: ignore[misc]


def test_the_plot_draws_the_trace_and_marks_the_reading() -> None:
    """The figure is the point of the result: a scalar hides the ballistics."""
    burst = tone_burst(FS, BS468_BURST_HZ, 250, post_silence=0.5).signal
    result = quasi_peak_meter(burst, FS)
    ax = result.plot()
    assert ax.get_xlabel() == "Time [s]"
    assert ax.get_ylabel() == "Quasi-peak reading"
    assert ax.get_title() == "Quasi-peak reading (ITU-R BS.468-4, weighted)"
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert any(label.startswith("Reading") and "dBqps" in label for label in labels)
    ax_es = result.plot(language="es")
    assert ax_es.get_xlabel() == "Tiempo [s]"
    assert ax_es.get_title() == "Lectura cuasipico (UIT-R BS.468-4, ponderada)"
    labels_es = [t.get_text() for t in ax_es.get_legend().get_texts()]
    assert any(label.startswith("Lectura ") for label in labels_es)


def test_the_plot_refuses_a_language_it_cannot_render() -> None:
    """The label table has two entries and says so."""
    result = quasi_peak_meter(_steady_sine(0.775, FS, seconds=0.5), FS)
    with pytest.raises(ValueError, match=r"Unknown language 'fr'"):
        result.plot(language="fr")


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


def test_an_empty_record_is_refused() -> None:
    """A meter with nothing to read has no reading, not a reading of zero."""
    with pytest.raises(ValueError, match=r"'x' cannot be empty"):
        quasi_peak_meter(np.array([]), FS)


def test_a_multichannel_record_is_refused() -> None:
    """One needle, one channel: mixing them would invent a measurement."""
    with pytest.raises(ValueError, match=r"'x' must be a 1-D time series"):
        quasi_peak_meter(np.zeros((2, 4800)), FS)


def test_a_bare_array_still_needs_its_rate() -> None:
    """The ballistics are in seconds; an array on its own has no time axis."""
    with pytest.raises(ValueError, match=r"fs is required when 'x' is a bare array"):
        quasi_peak_meter(np.zeros(4800))


def test_a_non_positive_rate_is_refused() -> None:
    """A rate of zero divides the time constants by nothing."""
    with pytest.raises(ValueError, match=r"'fs' must be positive"):
        quasi_peak_meter(np.zeros(4800), 0.0)


def test_a_non_positive_reference_is_refused() -> None:
    """A level is a ratio; the denominator has to be a level to divide by."""
    with pytest.raises(ValueError, match=r"'reference' must be positive"):
        quasi_peak_meter(np.zeros(4800), FS, reference=0.0)


def test_the_verifier_refuses_a_non_positive_rate() -> None:
    """The stimuli are built at this rate before anything is measured."""
    with pytest.raises(ValueError, match=r"'fs' must be positive"):
        verify_quasi_peak_dynamics(-1.0)


def test_a_result_whose_reading_is_not_its_trace_peak_is_refused() -> None:
    """The reading rule is the maximum of the needle, so it cannot disagree."""
    result = quasi_peak_meter(_steady_sine(0.775, FS, seconds=0.5), FS)
    with pytest.raises(ValueError, match=r"'reading' is .* but 'trace' peaks at"):
        replace(result, reading=result.reading * 2.0)


def test_a_two_dimensional_trace_is_refused() -> None:
    """The needle is one series; an extra axis would reach the plot intact."""
    with pytest.raises(
        ValueError, match=r"QuasiPeakResult: 'trace' must have one axis"
    ):
        QuasiPeakResult(
            reading=1.0,
            level=0.0,
            reference=DBQPS_REFERENCE_V,
            trace=np.ones((2, 3)),
            fs=FS,
            weighting="468",
        )


# ---------------------------------------------------------------------------
# The Signal contract
# ---------------------------------------------------------------------------


def test_an_uncalibrated_signal_reads_exactly_like_the_bare_array() -> None:
    """With no factor to apply, the object and the array are one recording."""
    record = _steady_sine(0.775, FS, seconds=0.5)
    from_signal = quasi_peak_meter(Signal(record, int(FS)))
    from_array = quasi_peak_meter(record, FS)
    assert from_signal.reading == from_array.reading
    assert from_signal.level == from_array.level


def test_a_calibrated_signal_is_read_in_pascals() -> None:
    """The library's one rule holds here: the factor scales the samples."""
    record = _steady_sine(0.775, FS, seconds=0.5)
    factor = 5.0
    from_signal = quasi_peak_meter(
        Signal(record, int(FS), calibration_factor=factor), reference=2e-5
    )
    from_array = quasi_peak_meter(factor * record, FS, reference=2e-5)
    assert from_signal.reading == from_array.reading
    assert from_signal.level == from_array.level


def test_a_calibrated_signal_needs_a_reference_of_its_own() -> None:
    """0.775 V is not a pressure, so it cannot become one by default."""
    record = _steady_sine(0.775, FS, seconds=0.5)
    calibrated = Signal(record, int(FS), calibration_factor=5.0)
    with pytest.raises(ValueError, match=r"'reference' is required for a calibrated"):
        quasi_peak_meter(calibrated)


def test_a_signal_refuses_a_rate_that_disagrees_with_its_own() -> None:
    """Exempt from nothing about the rate: the recording knows it."""
    record = _steady_sine(0.775, FS, seconds=0.5)
    signal = Signal(record, int(FS))
    with pytest.raises(ValueError, match=r"conflicts with the Signal's own fs"):
        quasi_peak_meter(signal, 44100)


# ---------------------------------------------------------------------------
# The ballistics constant
# ---------------------------------------------------------------------------


def test_the_shipped_ballistics_are_the_three_fitted_time_scales() -> None:
    """A fit to Tables 2 and 3; these numbers are nowhere in BS.468-4."""
    assert BS468_BALLISTICS.charge == pytest.approx(1.4096e-3)
    assert BS468_BALLISTICS.discharge == pytest.approx(293.20e-3)
    assert BS468_BALLISTICS.reading_device == pytest.approx(139.99e-3)


@pytest.mark.parametrize(
    "field",
    ["charge", "discharge", "reading_device"],
    ids=["charge", "discharge", "rd"],
)
def test_a_non_positive_time_constant_is_refused(field: str) -> None:
    """Seconds, and a positive number of them."""
    with pytest.raises(ValueError, match=rf"'{field}' must be positive"):
        replace(BS468_BALLISTICS, **{field: 0.0})


def test_a_non_finite_time_constant_is_refused() -> None:
    """An infinite constant freezes the stage it belongs to."""
    with pytest.raises(ValueError, match=r"'discharge'"):
        replace(BS468_BALLISTICS, discharge=math.inf)


def test_a_stage_that_falls_faster_than_it_rises_is_refused() -> None:
    """Swap the two and the peak rectifier becomes a valley follower."""
    with pytest.raises(
        ValueError, match=r"'charge' .* must be shorter than 'discharge'"
    ):
        QuasiPeakBallistics(charge=0.5, discharge=0.001, reading_device=0.14)


# ---------------------------------------------------------------------------
# The published identifiability statement
# ---------------------------------------------------------------------------
#
# The module and all three editions of its page publish how far each constant
# can move before one of the eleven windows fails. That is a claim about the
# standard, so it is pinned from both sides: each published edge must conform,
# and a step beyond it must not. Without the second half the range could be
# quietly narrowed and nothing would notice.
#
# These figures are only measurable because the chain takes the ballistics as
# an argument. While ``_calibration_factor`` and ``_steady_reference`` were
# keyed on the sample rate alone, moving the module constant left them
# answering with a reference computed for other ballistics, and the same value
# passed or failed depending on the order the probes ran in.


#: Published marginal range of each constant, in seconds, and a step outside
#: it. Marginal: measured with the other two frozen. They are not a box, which
#: :func:`test_two_constants_at_their_edges_leave_the_region` holds down.
_IDENTIFIED = {
    "charge": (1.02e-3, 1.90e-3, 1.00e-3, 1.92e-3),
    "discharge": (230.0e-3, 370.0e-3, 228.0e-3, 372.0e-3),
    "reading_device": (96.0e-3, 200.0e-3, 94.0e-3, 202.0e-3),
}


@pytest.mark.parametrize("field", sorted(_IDENTIFIED), ids=sorted(_IDENTIFIED))
def test_each_published_edge_is_a_conforming_instrument(field: str) -> None:
    """Both edges published for *field* meet all eleven windows."""
    low, high, _, _ = _IDENTIFIED[field]
    for value in (low, high):
        outcome = verify_quasi_peak_dynamics(
            48000.0, ballistics=replace(BS468_BALLISTICS, **{field: value})
        )
        assert outcome.passes, (
            f"{field} = {value * 1e3:g} ms is published as an edge of the "
            f"identified range and does not conform: worst margin "
            f"{outcome.worst_margin_db:+.4f} dB"
        )


@pytest.mark.parametrize("field", sorted(_IDENTIFIED), ids=sorted(_IDENTIFIED))
def test_the_published_range_is_not_quietly_wider(field: str) -> None:
    """A step outside either published edge fails, so the range is honest."""
    _, _, below, above = _IDENTIFIED[field]
    for value in (below, above):
        outcome = verify_quasi_peak_dynamics(
            48000.0, ballistics=replace(BS468_BALLISTICS, **{field: value})
        )
        assert not outcome.passes, (
            f"{field} = {value * 1e3:g} ms lies outside the published range "
            f"and conforms, so the range is understated"
        )


def test_two_constants_at_their_edges_leave_the_region() -> None:
    """The three ranges are marginal, so they do not combine into a box.

    The page says so in as many words, because reading three intervals as a
    box is the natural mistake and it is wrong by more than a decibel.
    """
    corner = replace(BS468_BALLISTICS, charge=1.02e-3, reading_device=96.0e-3)
    outcome = verify_quasi_peak_dynamics(48000.0, ballistics=corner)
    assert not outcome.passes
    assert outcome.worst_margin_db < -1.0


def test_the_verifier_answers_for_the_ballistics_it_is_given() -> None:
    """The caches are keyed by the ballistics, not by the sample rate alone.

    Asks in the order that used to give the wrong answer: a set far outside
    the region first, so its calibration and steady reference fill the caches,
    then the fitted set, which must still conform.
    """
    outside = replace(BS468_BALLISTICS, charge=0.3e-3)
    assert not verify_quasi_peak_dynamics(48000.0, ballistics=outside).passes
    assert verify_quasi_peak_dynamics(48000.0, ballistics=BS468_BALLISTICS).passes
    assert verify_quasi_peak_dynamics(48000.0).passes


# ---------------------------------------------------------------------------
# The verdict object: a summary its own eleven rows do not support is refused
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("count", [0, 10, 12])
def test_a_verdict_over_other_than_eleven_stimuli_is_rejected(count: int) -> None:
    """Clause 2 has eleven windows; fewer or more is not a conformance run."""
    report = verify_quasi_peak_dynamics()
    readings = (report.readings_percent * 2)[:count]
    with pytest.raises(ValueError, match=r"attested over the 11 stimuli of clause 2"):
        replace(report, readings_percent=readings)


@pytest.mark.parametrize("reading", [0.0, -5.0, float("nan"), float("inf")])
def test_a_reading_that_is_no_reading_is_rejected(reading: float) -> None:
    report = verify_quasi_peak_dynamics()
    readings = (reading, *report.readings_percent[1:])
    with pytest.raises(ValueError, match=r"'readings_percent' must be positive"):
        replace(report, readings_percent=readings)


def test_a_non_positive_sample_rate_is_rejected() -> None:
    report = verify_quasi_peak_dynamics()
    with pytest.raises(ValueError, match=r"'fs' must be positive"):
        replace(report, fs=0.0)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("passes", False),
        ("worst_margin_db", 99.0),
        ("worst_deviation_db", 0.0),
        ("stimuli", ()),
    ],
)
def test_the_summaries_are_read_from_the_rows(field: str, value: object) -> None:
    """The three summaries are the conjunction, the minimum and the maximum.

    A sheet that says the chain passed above a row whose margin is negative is
    the one this class exists to make impossible: the summaries are read from
    the rows and cannot be set.
    """
    report = verify_quasi_peak_dynamics()
    with pytest.raises(TypeError, match=field):
        replace(report, **{field: value})


def test_a_row_outside_its_window_fails_the_chain() -> None:
    """One reading outside its window is enough, and its margin is the worst."""
    report = verify_quasi_peak_dynamics()
    readings = list(report.readings_percent)
    # The 10 ms window of Table 2 is 41 % to 55 %: 60 % is 20 log10(55/60)
    # below its upper limit.
    readings[3] = 60.0
    failed = replace(report, readings_percent=tuple(readings))
    assert failed.stimuli[3]["stimulus"] == "10 ms"
    assert failed.passes is False
    assert failed.worst_margin_db == pytest.approx(20.0 * math.log10(55.0 / 60.0))


def test_the_window_is_read_from_the_table_not_from_the_row() -> None:
    """A row is read-only: its window and margin cannot be rewritten after the verdict."""
    report = verify_quasi_peak_dynamics()
    row = report.stimuli[0]
    assert (row["lower_percent"], row["upper_percent"]) == (13.5, 21.4)
    with pytest.raises(TypeError, match="does not support item assignment"):
        row["margin_db"] = -3.0  # type: ignore[index]
    assert report.passes is True


# ---------------------------------------------------------------------------
# The published figures of how the chain moves with the sample rate
# ---------------------------------------------------------------------------
#
# The module docstring, the helper that fixes the clause 2.6 scale, the
# verifier's docstring and all three editions of the page say in words how
# much the chain moves between the five rates of RATES. Each figure is worked
# out here from the chain and looked for, at the digits the prose writes it
# to, in every place that gives it: a change to the chain that moves one of
# them fails until the prose says the new figure, and so does prose edited to
# a figure the chain does not give.

_ROOT = Path(__file__).resolve().parents[2]
_PAGE = Path("devices") / "broadcast" / "quasi-peak"
_GUIDES = Path("site") / "src" / "content" / "docs"
#: The three editions of the page, each held to its own wording.
_EDITIONS = {
    "en": _GUIDES / _PAGE.with_suffix(".mdx"),
    "es": _GUIDES / "es" / _PAGE.with_suffix(".mdx"),
    "mirror": Path("docs") / _PAGE.with_suffix(".md"),
}


def _figures(dynamics: dict[float, QuasiPeakDynamicsResult]) -> dict[str, str]:
    """Every figure the prose gives, as the chain gives it, at the prose's digits."""
    scales = [quasi_peak_module._calibration_factor(fs) for fs in RATES]
    gains = [-20.0 * math.log10(scale) for scale in scales]
    peak_multiple = 1.0 / (quasi_peak_module._calibration_factor(FS) * math.sqrt(2.0))
    moves, shares = [], []
    for stimulus in (row["stimulus"] for row in dynamics[FS].stimuli):
        rows = [
            next(r for r in dynamics[fs].stimuli if r["stimulus"] == stimulus)
            for fs in RATES
        ]
        readings = [row["reading_percent"] for row in rows]
        move = 20.0 * math.log10(max(readings) / min(readings))
        window = 20.0 * math.log10(rows[0]["upper_percent"] / rows[0]["lower_percent"])
        moves.append(move)
        shares.append(move / window)
    deviations = [abs(dynamics[fs].worst_deviation_db) for fs in RATES]
    return {
        "gain_spread_db": f"{max(gains) - min(gains):.4f}",
        "peak_multiple": f"{peak_multiple:.4f}",
        "reading_move_db": f"{max(moves):.3f}",
        "window_share_percent": f"{100.0 * max(shares):.1f}",
        "margin_48k_db": f"{dynamics[48000.0].worst_margin_db:.3f}",
        "margin_32k_db": f"{dynamics[32000.0].worst_margin_db:.3f}",
        "deviation_db": f"{max(deviations):.3f}",
    }


def _phrases(figures: dict[str, str], *, spanish: bool) -> list[str]:
    """What a page says about the rates, with the chain's figures in it."""
    if spanish:
        f = {key: value.replace(".", ",") for key, value in figures.items()}
        return [
            f"se mueve {f['gain_spread_db']} dB entre 32, 44,1, 48, 96 y 192 kHz",
            "el peor margen está en la celda de 100 ráfagas por segundo",
            f"{f['margin_48k_db']} dB a 48 kHz",
            f"{f['margin_32k_db']} dB a 32 kHz, el menor de los cinco",
            f"ninguna lectura se mueve más de {f['reading_move_db']} dB, ni ninguna "
            f"más del {f['window_share_percent']} % de su propia ventana",
            f"La peor es de {f['deviation_db']} dB, a 10 ráfagas por segundo",
        ]
    return [
        f"steady-sine gain moves by {figures['gain_spread_db']} dB across 32, "
        "44.1, 48, 96 and 192 kHz",
        "the worst margin is at the 100 bursts per second cell",
        f"{figures['margin_48k_db']} dB at 48 kHz",
        f"{figures['margin_32k_db']} dB at 32 kHz, the smallest of the five",
        f"no reading moves by more than {figures['reading_move_db']} dB, and none "
        f"by more than {figures['window_share_percent']} % of its own window",
        f"The worst is {figures['deviation_db']} dB, at 10 bursts per second",
    ]


def _flat(text: str | None) -> str:
    """*text* with every run of white space one space, as a reader sees it."""
    return " ".join((text or "").split())


@pytest.mark.parametrize("edition", sorted(_EDITIONS))
def test_each_edition_of_the_page_gives_the_chains_rate_figures(
    dynamics: dict[float, QuasiPeakDynamicsResult], edition: str
) -> None:
    """The page quotes the figures the chain gives at the five rates."""
    path = _EDITIONS[edition]
    text = _flat((_ROOT / path).read_text(encoding="utf-8"))
    for phrase in _phrases(_figures(dynamics), spanish=edition == "es"):
        assert phrase in text, f"{path} does not say {phrase!r}"


def test_the_docstrings_give_the_chains_rate_figures(
    dynamics: dict[float, QuasiPeakDynamicsResult],
) -> None:
    """The module and the clause 2.6 helper quote the same figures as the page."""
    figures = _figures(dynamics)
    module = _flat(quasi_peak_module.__doc__)
    scale = _flat(quasi_peak_module._calibration_factor.__doc__)
    assert (
        f"no reading moves by more than {figures['reading_move_db']} dB, and none "
        f"by more than {figures['window_share_percent']} % of its own window"
    ) in module
    assert f"{figures['peak_multiple']} of it at 48 kHz" in scale
    assert f"the multiple moves by {figures['gain_spread_db']} dB" in scale


def test_the_worst_cells_are_the_ones_the_prose_names(
    dynamics: dict[float, QuasiPeakDynamicsResult],
) -> None:
    """At every rate the worst margin is at 100 bursts/s and the worst
    deviation at 10 bursts/s, and 32 kHz has the smallest margin of the five.
    """
    for report in dynamics.values():
        rows = report.stimuli
        assert min(rows, key=lambda r: r["margin_db"])["stimulus"] == "100 bursts/s"
        worst = max(rows, key=lambda r: abs(r["deviation_db"]))
        assert worst["stimulus"] == "10 bursts/s"
    smallest = min(RATES, key=lambda fs: dynamics[fs].worst_margin_db)
    assert smallest == 32000.0


def test_the_44_1_khz_gate_moves_the_reading_by_less_than_published() -> None:
    """The 25-cycle burst spans 220.5 samples at 44.1 kHz and is gated at 220.

    Gating it a whole sample later, at 221, bounds what the half sample costs,
    and the verifier's docstring publishes that bound.
    """
    fs = 44100.0
    reference = quasi_peak_module._steady_reference(fs, BS468_BALLISTICS)
    tail = np.zeros(int(round(quasi_peak_module._BURST_TAIL_SECONDS * fs)))

    def reading(samples: int) -> float:
        burst = np.sin(2.0 * math.pi * BS468_BURST_HZ * np.arange(samples) / fs)
        trace = quasi_peak_module._detector_trace(
            np.concatenate([burst, tail]), fs, weighted=True
        )
        return float(trace.max()) / reference

    shift_db = abs(20.0 * math.log10(reading(221) / reading(220)))
    assert shift_db < 1e-4
    published = _flat(verify_quasi_peak_dynamics.__doc__)
    assert "moves the reading by under 0.0001 dB" in published
