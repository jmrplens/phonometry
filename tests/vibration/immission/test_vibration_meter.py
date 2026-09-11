#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the vibration meter of DIN 45669-1:2010-09 (+ Corrigendum 1).

Anchored on what the standard prints: the reference indications of 6.2.3.12,
the rows of Table 9 that follow its own formulas, Table 8 in the redraft the
corrigendum gives it, the tolerance limits of Tables 2 and 3, and the Annex E
weighting curves against the DIN 4150-3 table they invert.

The chain is exercised end to end rather than checked formula by formula: a
sine is generated, filtered, averaged and read, exactly as the meter under
test would be fed. That is what makes the printed values usable as an oracle,
because ``KB_Fmax`` above ``KB_F`` is the ripple of the running r.m.s. and no
closed form for the pair is printed anywhere.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import signal as sig

from phonometry.vibration import immission as im

#: A rate that carries 315 Hz comfortably: the bilinear design warps the
#: response near Nyquist, and the 315 Hz column of Table 9 is read at the very
#: top of the building working range, where the low pass is already 20 dB down.
FS_HZ = 8192.0

#: Long enough for the running r.m.s. to have settled (4 tau is 0,5 s) with
#: room to spare, and short enough to keep the suite quick.
RECORD_S = 12.0

#: How long the test signal takes to reach full amplitude, in seconds. It
#: matters: a sine that starts abruptly drives the band limitation with a
#: step, and the peak indication is a max-hold that keeps the transient. A
#: calibration exciter comes up smoothly, and so does this.
RAMP_S = 1.0


def _sine(frequency_hz: float, *, amplitude_mm_s: float = 1.0) -> np.ndarray:
    """A sine of *frequency_hz*, raised over :data:`RAMP_S` and then steady."""
    t = np.arange(int(RECORD_S * FS_HZ)) / FS_HZ
    onset = 0.5 * (1.0 - np.cos(math.pi * np.clip(t / RAMP_S, 0.0, 1.0)))
    return amplitude_mm_s * onset * np.sin(2.0 * math.pi * frequency_hz * t)


def _settled(values: np.ndarray) -> np.ndarray:
    """The part of a per-sample signal after the averaging has settled."""
    return values[int((RAMP_S + 3.0) * FS_HZ) :]


@pytest.mark.parametrize(
    ("frequency_hz", "printed"), list(im.KB_TEST_INDICATIONS.items())
)
def test_table_9_weighted_rows(frequency_hz: float, printed: tuple[float, ...]) -> None:
    """Table 9: the KB_F, KB_Fmax and KB_FTm a 1 mm/s sine has to display.

    KB_F is the settled indication, which fluctuates: the standard prints it
    with a 2 % band and the value here is its mean. KB_Fmax is the maximum of
    the same signal, above it by the ripple of the running r.m.s., and for a
    steady sine the clock maximum r.m.s. is that maximum again.
    """
    kbf = im.kbf_signal(_sine(frequency_hz), FS_HZ)
    settled = _settled(kbf)
    assert settled.mean() == pytest.approx(printed[0], abs=1e-3)
    assert settled.max() == pytest.approx(printed[1], abs=1e-3)


def test_table_9_clock_maximum_rms_of_a_steady_sine() -> None:
    """For a signal that does not change, KB_FTm is KB_Fmax (Formula (2))."""
    t = np.arange(int(65.0 * FS_HZ)) / FS_HZ
    onset = 0.5 * (1.0 - np.cos(math.pi * np.clip(t / RAMP_S, 0.0, 1.0)))
    record = onset * np.sin(2.0 * math.pi * 31.5 * t)
    reading = im.measure_vibration_immission(record, FS_HZ)
    assert reading.takt_maxima.size == 2
    assert reading.kbf_takt_rms == pytest.approx(0.700, abs=1e-3)
    assert reading.kbf_takt_rms == pytest.approx(reading.kbf_max, rel=1e-3)


def test_reference_indications_of_6_2_3_12() -> None:
    """The four values a meter must show for the 1 mm/s, 16 Hz reference."""
    record = _sine(im.KB_REFERENCE_FREQUENCY_HZ)
    reading = im.measure_vibration_immission(record, FS_HZ)
    kbf = _settled(reading.kbf)
    assert reading.peak_velocity_mm_s == pytest.approx(
        im.KB_REFERENCE_INDICATIONS["peak_velocity_mm_s"], abs=5e-3
    )
    assert kbf.mean() == pytest.approx(im.KB_REFERENCE_INDICATIONS["kbf"], abs=1e-3)
    assert kbf.max() == pytest.approx(im.KB_REFERENCE_INDICATIONS["kbf_max"], abs=1e-3)


def test_reference_kbf_fluctuation_stays_inside_the_printed_two_percent() -> None:
    """6.2.3.12 prints KB_F(t) as 0,667 with a 2 % fluctuation, not a number."""
    kbf = _settled(im.kbf_signal(_sine(im.KB_REFERENCE_FREQUENCY_HZ), FS_HZ))
    swing = (kbf.max() - kbf.min()) / kbf.mean()
    assert 0.0 < swing <= 0.04  # a band of +-2 % is a swing of 4 %


@pytest.mark.parametrize(
    ("duration_ms", "cycles", "percent"), im.KB_PULSE_RESPONSE_PERCENT
)
def test_table_8_pulse_response(
    duration_ms: float, cycles: int, percent: float
) -> None:
    """Table 8 as Corrigendum 1 rewrites it: bursts of 80 Hz, once a second.

    The reference is the display for the continuous signal, which is why the
    first row is above 100 %: the ripple of the running r.m.s. puts the
    maximum of a steady indication above its mean.
    """
    t = np.arange(int(20.0 * FS_HZ)) / FS_HZ
    carrier = np.sin(2.0 * math.pi * 80.0 * t)
    continuous = _settled(im.kbf_signal(carrier, FS_HZ))
    if math.isinf(duration_ms):
        shown = continuous.max()
    else:
        gate = (np.mod(t, 1.0) < duration_ms / 1000.0).astype(float)
        assert round(gate.sum() / 20.0 * 80.0 / FS_HZ) == cycles
        shown = _settled(im.kbf_signal(carrier * gate, FS_HZ)).max()
    # 0,7 points of allowance, which the two shortest bursts need: one and two
    # cycles of an 80 Hz sine are where a digital chain and a printed value
    # part company, and the standard prints no tolerance for this table.
    assert shown / continuous.mean() * 100.0 == pytest.approx(percent, abs=0.7)


def test_formula_5_is_the_magnitude_of_formula_3() -> None:
    """The complex response and the printed magnitude agree, both ranges."""
    f = np.array([0.5, 1.0, 5.6, 16.0, 31.5, 80.0, 200.0, 315.0])
    for name, (lower_hz, upper_hz) in im.WORKING_RANGES_HZ.items():
        printed = 1.0 / np.sqrt(
            (1.0 + (im.BAND_LIMIT_CORNER_FACTOR * lower_hz / f) ** 4)
            * (1.0 + (im.BAND_LIMIT_CORNER_FACTOR * f / upper_hz) ** 4)
        )
        got = np.abs(im.band_limitation_response(f, working_range=name))
        assert got == pytest.approx(printed, rel=1e-12)


def test_formula_6_is_the_magnitude_of_formula_4() -> None:
    """The KB weighting is the band limitation with one more first-order pole."""
    f = np.array([1.0, 5.6, 16.0, 31.5, 80.0])
    band = np.abs(im.band_limitation_response(f))
    printed = band / np.sqrt(1.0 + (im.KB_CORNER_HZ / f) ** 2)
    assert np.abs(im.kb_weighting_response(f)) == pytest.approx(printed, rel=1e-12)


def test_the_band_limits_sit_where_the_note_of_5_2_3_2_says() -> None:
    """1 Hz to 80 Hz is made by corners at 0,8 Hz and 100 Hz, 3 dB down."""
    at_corners = np.abs(im.band_limitation_response([0.8, 100.0]))
    assert at_corners == pytest.approx([1.0 / math.sqrt(2.0)] * 2, rel=1e-7)
    railway = np.abs(
        im.band_limitation_response([3.2, 393.75], working_range="railway")
    )
    assert railway == pytest.approx([1.0 / math.sqrt(2.0)] * 2, rel=1e-7)


@pytest.mark.parametrize(
    ("frequency_hz", "lower", "upper"),
    [
        (16.0, 10.0, 10.0),  # inside 1,25 f_u to 0,8 f_o
        (1.25, 10.0, 10.0),  # the lower edge of the central band
        (64.0, 10.0, 10.0),  # 0,8 f_o, still central
        (1.0, 20.0, 20.0),  # below 1,25 f_u, inside 0,5 f_u to 2 f_o
        (100.0, 20.0, 20.0),  # above 0,8 f_o, inside 2 f_o
        (0.4, 100.0, 20.0),  # outside every band of Table 2
        (200.0, 100.0, 20.0),
    ],
)
def test_tables_2_and_3_limits(frequency_hz: float, lower: float, upper: float) -> None:
    """Every band of the two tables, read at its own edge."""
    got_lower, got_upper = im.response_tolerance_percent([frequency_hz])
    assert got_lower[0] == pytest.approx(lower)
    assert got_upper[0] == pytest.approx(upper)


def test_a_meter_on_its_design_response_passes() -> None:
    """The design response itself is the centre of the band, at every point."""
    f = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 31.5, 63.0, 80.0])
    result = im.verify_vibration_meter(f, np.abs(im.kb_weighting_response(f)))
    assert result.passes
    assert result.deviation_percent == pytest.approx(np.zeros(f.size - 1), abs=1e-9)
    # The reference frequency carries no requirement and is not graded.
    assert result.frequencies_hz.size == f.size - 1
    assert im.KB_REFERENCE_FREQUENCY_HZ not in result.frequencies_hz


def test_a_meter_outside_the_central_band_fails_there_and_only_there() -> None:
    """One frequency pushed 12 % up fails; the tail keeps its wider limit."""
    f = np.array([1.0, 16.0, 31.5, 80.0])
    measured = np.abs(im.kb_weighting_response(f))
    measured[2] *= 1.12
    measured[0] *= 1.15
    result = im.verify_vibration_meter(f, measured)
    assert not result.passes
    graded = dict(zip(result.frequencies_hz, result.within_tolerance, strict=True))
    assert not graded[31.5]
    assert graded[1.0]  # 15 % is inside the 20 % of the skirt
    assert result.worst_frequency_hz == pytest.approx(31.5)


def test_verification_normalises_at_the_reference_and_needs_it() -> None:
    """A meter with a flat gain error passes; without f_r nothing can be said."""
    f = np.array([1.0, 16.0, 31.5, 80.0])
    scaled = np.abs(im.kb_weighting_response(f)) * 3.0
    assert im.verify_vibration_meter(f, scaled).passes
    with pytest.raises(ValueError, match="reference_frequency_hz"):
        im.verify_vibration_meter([1.0, 31.5], [1.0, 1.0])


def test_verification_refuses_mismatched_inputs() -> None:
    """Two arrays that do not line up cannot be compared point by point."""
    with pytest.raises(ValueError, match="same shape"):
        im.verify_vibration_meter([1.0, 16.0, 31.5], [1.0, 1.0])
    with pytest.raises(ValueError, match="weighting"):
        im.verify_vibration_meter([16.0, 31.5], [1.0, 1.0], weighting="A")


def test_clock_maxima_drop_a_partial_interval() -> None:
    """5.1.6.4: the averaging time spans whole clock intervals only."""
    kbf = np.ones(int(75.0 * FS_HZ))
    maxima = im.takt_maxima(kbf, FS_HZ)
    assert maxima.size == 2
    assert im.takt_maxima(np.ones(int(29.0 * FS_HZ)), FS_HZ).size == 0


def test_a_bad_display_is_reported_under_its_own_name() -> None:
    """``takt_maxima`` takes ``kbf``, so an error names ``kbf``."""
    with pytest.raises(ValueError, match="'kbf' must be a non-empty 1-D array"):
        im.takt_maxima(np.ones((2, 2)), FS_HZ)


def test_formula_2_counts_a_suppressed_interval_in_n() -> None:
    """A clock maximum at or below 0,1 enters as zero and still counts."""
    loud = 0.8
    assert im.takt_maximum_rms([loud, loud]) == pytest.approx(loud)
    assert im.takt_maximum_rms([loud, 0.05]) == pytest.approx(loud / math.sqrt(2.0))
    assert im.takt_maximum_rms([0.1, 0.05]) == pytest.approx(0.0)
    assert im.takt_maximum_rms([]) == pytest.approx(0.0)


def test_a_reading_below_the_detection_limits_says_so() -> None:
    """5.2.2 stops requiring a meter to resolve anything below them."""
    quiet = im.measure_vibration_immission(np.full(int(35.0 * FS_HZ), 1e-4), FS_HZ)
    assert not quiet.above_detection_limit
    assert im.measure_vibration_immission(_sine(16.0), FS_HZ).above_detection_limit


@pytest.mark.parametrize(
    ("building_class", "expected"),
    [
        ("commercial", [1.0, 1.0, 0.5, 0.4, 0.4]),
        ("residential", [1.0, 1.0, 1.0 / 3.0, 0.25, 0.25]),
        ("sensitive", [1.0, 1.0, 0.375, 0.3, 0.3]),
    ],
)
def test_annex_e_weighting_inverts_the_din_4150_3_curve(
    building_class: str, expected: list[float]
) -> None:
    """Table E.1 read at the corners of the table it comes from.

    The target magnitude is the guideline value of the 1 Hz to 10 Hz band over
    the guideline value at the frequency, so at 50 Hz the commercial class,
    whose curve has risen from 20 mm/s to 40 mm/s, weighs 0,5.
    """
    got = im.assessment_weighting_response(
        [1.0, 10.0, 50.0, 100.0, 200.0], building_class=building_class
    )
    assert got == pytest.approx(expected, rel=1e-12)


def test_annex_e_weighting_is_the_reciprocal_of_the_guideline_curve() -> None:
    """The same relation, checked against the module that owns that curve.

    Two standards and two modules: DIN 4150-3 prints the guideline values and
    DIN 45669-1 Annex E prints the weighting. If either table were transcribed
    wrongly this would part company, at every frequency of the sweep.
    """
    from phonometry.vibration.structural import building_damage as bd

    f = np.linspace(1.0, 100.0, 199)
    for cls, guide in im.ASSESSMENT_GUIDE_VALUES_MM_S.items():
        curve = np.asarray(bd.guideline_velocity(cls, f))
        assert im.assessment_weighting_response(f, building_class=cls) == pytest.approx(
            guide / curve, rel=1e-12
        )


@pytest.mark.parametrize("building_class", list(im.ASSESSMENT_GUIDE_VALUES_MM_S))
def test_annex_e_filter_stays_inside_the_five_percent_band(
    building_class: str,
) -> None:
    """Table E.1 allows the realised filter 5 % either side of the target."""
    fs_hz = 2048.0
    taps = im.assessment_weighting_taps(fs_hz, building_class=building_class)
    freqs, response = sig.freqz(taps, worN=4096, fs=fs_hz)
    graded = (freqs >= 1.0) & (freqs <= im.WORKING_RANGES_HZ["railway"][1])
    target = im.assessment_weighting_response(
        freqs[graded], building_class=building_class
    )
    deviation = np.abs(np.abs(response)[graded] / target - 1.0)
    assert deviation.max() < im.ASSESSMENT_WEIGHTING_TOLERANCE


@pytest.mark.parametrize("building_class", list(im.ASSESSMENT_GUIDE_VALUES_MM_S))
def test_annex_e_filter_has_a_linear_phase(building_class: str) -> None:
    """Annex E requires it, and a symmetric FIR is how it is met."""
    taps = im.assessment_weighting_taps(2048.0, building_class=building_class)
    assert taps == pytest.approx(taps[::-1], rel=1e-12, abs=1e-15)


def test_assessment_velocity_below_ten_hertz_is_the_velocity_itself() -> None:
    """The weighting is 1 there, so the peak is the peak that went in."""
    fs_hz = 2048.0
    t = np.arange(int(4.0 * fs_hz)) / fs_hz
    record = 3.0 * np.sin(2.0 * math.pi * 5.0 * t)
    weighted = im.assessment_velocity(record, fs_hz, building_class="residential")
    assert np.max(np.abs(weighted)) == pytest.approx(3.0, rel=0.02)


def test_annex_e_verdict_uses_the_frequency_independent_guide_value() -> None:
    """Table E.2, and the point of the annex: no frequency is asked for."""
    fs_hz = 2048.0
    t = np.arange(int(4.0 * fs_hz)) / fs_hz
    record = 6.0 * np.sin(2.0 * math.pi * 8.0 * t)
    result = im.assess_short_term_vibration(record, fs_hz, building_class="residential")
    assert result.guide_value_mm_s == pytest.approx(5.0)
    assert not result.within_guideline
    assert result.ratio == pytest.approx(6.0 / 5.0, rel=0.02)
    # The same record at 60 Hz, where the guideline curve has risen to
    # 16,5 mm/s, is weighted down to a third and keeps to the same value.
    fast = 6.0 * np.sin(2.0 * math.pi * 60.0 * t)
    assert im.assess_short_term_vibration(
        fast, fs_hz, building_class="residential"
    ).within_guideline


def test_annex_d_zero_crossing_and_fourier_find_the_same_burst() -> None:
    """Two ways of naming a frequency an event does not really have."""
    fs_hz = 2048.0
    t = np.arange(int(2.0 * fs_hz)) / fs_hz
    record = np.sin(2.0 * math.pi * 24.0 * t) * np.hanning(t.size)
    by_crossing = im.dominant_frequency(record, fs_hz)
    by_fourier = im.dominant_frequency(record, fs_hz, method="fourier")
    assert by_crossing.frequency_hz == pytest.approx(24.0, rel=0.03)
    assert by_fourier.frequency_hz == pytest.approx(24.0, rel=0.03)
    assert by_crossing.candidates == ()
    assert len(by_fourier.candidates) == 2
    assert by_fourier.candidates[0][1] >= by_fourier.candidates[1][1]


def test_annex_d_refuses_a_record_with_no_half_period_around_its_peak() -> None:
    """A monotone ramp has a largest value and no zero crossing after it."""
    with pytest.raises(ValueError, match="zero crossing"):
        im.dominant_frequency(np.linspace(0.0, 1.0, 100), 1000.0)


def test_a_rate_that_cannot_carry_the_working_range_is_refused() -> None:
    """An aliased record reads like an ordinary one, so it is refused first."""
    with pytest.raises(ValueError, match="fs_hz"):
        im.kb_signal(np.zeros(100), 100.0)
    with pytest.raises(ValueError, match="fs_hz"):
        im.kb_signal(np.zeros(100), 500.0, working_range="railway")
    with pytest.raises(ValueError, match="fs_hz"):
        im.assessment_weighting_taps(600.0, building_class="residential")


def test_unknown_names_are_refused_by_the_names_they_are_not() -> None:
    """Every choice is spelled out in the message that refuses it."""
    with pytest.raises(ValueError, match="working_range"):
        im.band_limitation_response([16.0], working_range="tunnel")
    with pytest.raises(ValueError, match="building_class"):
        im.assessment_weighting_response([16.0], building_class="hospital")
    with pytest.raises(ValueError, match="method"):
        im.dominant_frequency(np.sin(np.arange(100) / 3.0), 1000.0, method="peak")
