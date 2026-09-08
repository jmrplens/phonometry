#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the ISO 8041-1:2017 instrument verification.

Anchored on the printed tables: the transition frequencies of Table 4, the
tolerance bands of Table 5, the reference conditions and nominal frequency
ranges of Table 1, the indication tolerances of Table 2, the phase columns of
Tables B.1 to B.9 and the two formulae that grade them, (6) and (H.4).
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest
from reference_data import ISO8041_1_ANNEX_B_PHASES_DEG

from phonometry import vibration
from phonometry.vibration.human import instrumentation as ins
from phonometry.vibration.human.exposure import HumanVibrationWarning

# Table 4, as the decimals printed beside the exponents. The module builds
# them from the exponents, so these are the independent side of the check.
TABLE_4_PRINTED = {
    "Wb": (0.2512, 0.631, 63.1, 158.5),
    "Wf": (0.05012, 0.1259, 0.3981, 1.0),
    "Wh": (3.981, 10.0, 794.3, 1995.0),
    "Wm": (0.5012, 1.259, 63.1, 158.5),
}

# Table 1: reference frequency in hertz, weighting factor there, and the
# weighted acceleration a conforming meter indicates.
TABLE_1_PRINTED = {
    "Wb": (15.915, 0.8126, 0.8126),
    "Wc": (15.915, 0.5145, 0.5145),
    "Wd": (15.915, 0.1261, 0.1261),
    "We": (15.915, 0.06287, 0.06287),
    "Wf": (0.3979, 0.3888, 0.03888),
    "Wh": (79.58, 0.2020, 2.020),
    "Wj": (15.915, 1.019, 1.019),
    "Wk": (15.915, 0.7718, 0.7718),
    "Wm": (15.915, 0.3362, 0.3362),
}


@pytest.mark.parametrize(("name", "printed"), TABLE_4_PRINTED.items())
def test_the_transition_frequencies_are_table_4(
    name: str, printed: tuple[float, ...]
) -> None:
    """Built from the exponents, checked against the decimals beside them."""
    got = ins.TRANSITION_FREQUENCIES_HZ[name]
    assert got == pytest.approx(printed, rel=2e-4)


def test_every_weighting_has_its_four_transition_frequencies() -> None:
    assert set(ins.TRANSITION_FREQUENCIES_HZ) == set(vibration.WEIGHTING_NAMES)
    for name, corners in ins.TRANSITION_FREQUENCIES_HZ.items():
        assert len(corners) == 4, name
        assert list(corners) == sorted(corners), name


@pytest.mark.parametrize(("name", "printed"), TABLE_1_PRINTED.items())
def test_the_reference_conditions_are_table_1(
    name: str, printed: tuple[float, float, float]
) -> None:
    """The reference frequency, the factor there, and their product.

    The frequencies are derived from the radians per second the standard
    prints, so the hertz beside them are the independent check; the factor is
    what the already-implemented weighting has to reproduce.
    """
    frequency, factor, indication = printed
    assert ins.REFERENCE_FREQUENCY_HZ[name] == pytest.approx(frequency, rel=1e-4)
    got = float(np.asarray(vibration.weighting_factors(name, [frequency]))[0])
    assert got == pytest.approx(factor, rel=1e-3)
    assert ins.reference_indication(name) == pytest.approx(indication, rel=1e-3)


def test_the_indication_tolerance_singles_out_the_low_frequency_case() -> None:
    """Table 2 gives Wf five per cent and everything else four."""
    assert ins.indication_tolerance_percent("Wf") == pytest.approx(5.0)
    for name in vibration.WEIGHTING_NAMES:
        if name != "Wf":
            assert ins.indication_tolerance_percent(name) == pytest.approx(4.0)


def test_the_tolerance_band_widens_at_the_table_4_corners() -> None:
    """Table 5, region by region, read across one weighting."""
    ft1, ft2, ft3, ft4 = ins.TRANSITION_FREQUENCIES_HZ["Wk"]
    inside = [ft1 * 0.5, ft1 * 1.5, ft2, (ft2 + ft3) / 2, ft3, ft3 * 1.5, ft4 * 2.0]
    upper, lower = ins.weighting_tolerance_percent("Wk", inside)
    assert list(upper) == pytest.approx([26, 26, 12, 12, 12, 26, 26])
    assert list(lower) == pytest.approx([-100, -21, -11, -11, -11, -21, -100])


def test_the_transition_frequencies_belong_to_the_region_they_close() -> None:
    """Table 5 writes the central band closed and the skirts open.

    ``ft2 <= f <= ft3`` is the central region, so both corners take the
    tighter tolerance rather than the wider one on either side of them.
    """
    _, ft2, ft3, _ = ins.TRANSITION_FREQUENCIES_HZ["Wd"]
    upper, lower = ins.weighting_tolerance_percent("Wd", [ft2, ft3])
    assert list(upper) == pytest.approx([12.0, 12.0])
    assert list(lower) == pytest.approx([-11.0, -11.0])


def test_the_phase_band_is_a_separate_question() -> None:
    """Footnote a: only a meter that reports a non-r.m.s. parameter is graded.

    Kept as its own function rather than a third array beside the magnitudes,
    so an r.m.s.-only instrument is never handed a phase verdict it is not
    subject to.
    """
    ft1, ft2, ft3, ft4 = ins.TRANSITION_FREQUENCIES_HZ["Wk"]
    got = ins.phase_tolerance_degrees("Wk", [ft1 * 0.5, ft1 * 1.5, ft2, ft4 * 2.0])
    assert got[0] == math.inf
    assert got[1] == pytest.approx(12.0)
    assert got[2] == pytest.approx(6.0)
    assert got[3] == math.inf


def test_a_response_equal_to_the_design_goal_passes_everywhere() -> None:
    frequencies = np.array([0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 31.5, 63.0, 80.0])
    design = np.asarray(vibration.weighting_factors("Wk", frequencies))
    got = vibration.verify_weighting("Wk", frequencies, design)
    assert got.passes
    assert got.worst_deviation_percent == pytest.approx(0.0, abs=1e-9)
    assert got.failing_frequencies_hz.size == 0


def test_the_acceptance_test_is_the_one_annex_b_prints() -> None:
    """``(measured / design - 1) * 100`` against the band, and nothing else.

    A response 11,9 % high in the central region passes and one 12,1 % high
    fails, which is the only difference between a conforming instrument and a
    rejected one at that frequency.
    """
    frequency = 16.0
    design = float(np.asarray(vibration.weighting_factors("Wk", [frequency]))[0])
    inside = vibration.verify_weighting("Wk", [frequency], [design * 1.119])
    outside = vibration.verify_weighting("Wk", [frequency], [design * 1.121])
    assert inside.passes
    assert not outside.passes
    assert outside.worst_deviation_percent == pytest.approx(12.1, abs=0.05)
    assert outside.failing_frequencies_hz == pytest.approx([frequency])


def test_the_tails_constrain_the_response_from_above_only() -> None:
    """``-100 %`` is not a wide band, it is the absence of a lower limit.

    Below the first transition frequency an instrument may roll off as far as
    it likes, and a response of exactly zero there still conforms.
    """
    ft1 = ins.TRANSITION_FREQUENCIES_HZ["Wk"][0]
    frequency = ft1 * 0.5
    got = vibration.verify_weighting("Wk", [frequency], [0.0])
    assert got.passes
    assert got.deviation_percent == pytest.approx([-100.0])

    design = float(np.asarray(vibration.weighting_factors("Wk", [frequency]))[0])
    over = vibration.verify_weighting("Wk", [frequency], [design * 1.27])
    assert not over.passes


def test_the_verdict_is_about_the_weighting_and_says_so() -> None:
    """The class of thing this can answer, pinned by the docstring."""
    assert "never a certificate" in ins.__doc__
    assert "hardware measurements" in vibration.WeightingVerification.passes.__doc__


def test_a_response_of_the_wrong_length_is_refused() -> None:
    with pytest.raises(ValueError, match=r"same shape"):
        vibration.verify_weighting("Wk", [1.0, 2.0, 4.0], [0.5, 0.6])


@pytest.mark.parametrize(
    ("frequencies", "factors", "match"),
    [
        ([0.0, 1.0], [0.5, 0.5], r"positive and finite"),
        ([-1.0, 1.0], [0.5, 0.5], r"positive and finite"),
        ([1.0, 2.0], [0.5, -0.1], r"non-negative and finite"),
        ([1.0, 2.0], [0.5, math.nan], r"non-negative and finite"),
    ],
)
def test_the_measurement_is_checked_before_it_is_judged(
    frequencies: list[float], factors: list[float], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        vibration.verify_weighting("Wk", frequencies, factors)


def test_an_unknown_weighting_is_refused_by_every_entry_point() -> None:
    for call in (
        lambda: vibration.verify_weighting("Wz", [1.0], [1.0]),
        lambda: vibration.verify_phase_response("Wz", [1.0, 2.0], [0.0, 0.0]),
        lambda: ins.weighting_tolerance_percent("Wz", [1.0]),
        lambda: ins.phase_tolerance_degrees("Wz", [1.0]),
        lambda: ins.indication_tolerance_percent("Wz"),
        lambda: ins.reference_indication("Wz"),
    ):
        with pytest.raises(ValueError, match=r"'name'"):
            call()


# ---------------------------------------------------------------------------
# The decision rule of 13.1 and 14.1 (printed folios 42 and 48).
# ---------------------------------------------------------------------------
def _measured_at(weighting: str, frequency_hz: float, percent: float) -> list[float]:
    """A measured factor deviating from the design goal by ``percent``."""
    design = float(
        np.asarray(vibration.weighting_factors(weighting, [frequency_hz]))[0]
    )
    return [design * (1.0 + percent / 100.0)]


def test_the_laboratory_uncertainty_extends_the_deviation_upwards() -> None:
    """13.1 and 14.1, word for word in both.

    Compliance is demonstrated when the deviation, "extended by the actual
    expanded uncertainty of measurement of the testing laboratory", does not
    exceed the tolerance limits. So a deviation of 11,5 % against the +12 %
    of the central region conforms on its own and stops conforming once a
    laboratory that measures to 1 % declares it. The pair either side of the
    edge is the whole difference the keyword makes.
    """
    measured = _measured_at("Wk", 16.0, 11.5)
    assert vibration.verify_weighting("Wk", [16.0], measured).passes
    extended = vibration.verify_weighting(
        "Wk", [16.0], measured, expanded_uncertainty_percent=1.0
    )
    assert not extended.passes
    assert extended.failing_frequencies_hz == pytest.approx([16.0])
    # And an uncertainty small enough not to reach the limit leaves it standing.
    assert vibration.verify_weighting(
        "Wk", [16.0], measured, expanded_uncertainty_percent=0.4
    ).passes


def test_the_laboratory_uncertainty_extends_the_deviation_downwards() -> None:
    """The same sentence read against the -11 % of the same region."""
    measured = _measured_at("Wk", 16.0, -10.5)
    assert vibration.verify_weighting("Wk", [16.0], measured).passes
    assert not vibration.verify_weighting(
        "Wk", [16.0], measured, expanded_uncertainty_percent=1.0
    ).passes
    assert vibration.verify_weighting(
        "Wk", [16.0], measured, expanded_uncertainty_percent=0.4
    ).passes


def test_the_band_is_not_widened_by_the_uncertainty() -> None:
    """5.6.6 and 13.1 are different sentences and only one moves anything.

    The Table 5 limits already include the maximum permitted uncertainties,
    so they are returned as printed however large the laboratory's own
    uncertainty is; what 13.1 moves is the measurement.
    """
    upper, lower = ins.weighting_tolerance_percent("Wk", [16.0])
    assert (float(upper[0]), float(lower[0])) == pytest.approx((12.0, -11.0))
    verdict = vibration.verify_weighting(
        "Wk", [16.0], _measured_at("Wk", 16.0, 11.5), expanded_uncertainty_percent=1.0
    )
    assert verdict.deviation_percent == pytest.approx([11.5], abs=1e-9)
    assert verdict.expanded_uncertainty_percent == pytest.approx(1.0)


def test_no_uncertainty_is_the_default_and_is_recorded() -> None:
    """The bare comparison stays the default, and says that it was one."""
    frequencies = [1.0, 8.0, 63.0]
    design = np.asarray(vibration.weighting_factors("Wd", frequencies))
    verdict = vibration.verify_weighting("Wd", frequencies, design)
    assert verdict.expanded_uncertainty_percent == pytest.approx(0.0)
    assert verdict.passes


def test_the_uncertainty_never_reaches_the_unconstrained_tails() -> None:
    """``-100 %`` is the absence of a limit, so nothing is subtracted from it.

    A response of exactly zero below ft1 deviates by -100 % and conforms;
    extending that deviation downwards would reject an instrument for having
    been measured carefully.
    """
    ft1 = ins.TRANSITION_FREQUENCIES_HZ["Wk"][0]
    frequency = ft1 * 0.5
    verdict = vibration.verify_weighting(
        "Wk", [frequency], [0.0], expanded_uncertainty_percent=5.0
    )
    assert verdict.passes
    # The upper limit of the same tail is a real limit and is still extended.
    measured = _measured_at("Wk", frequency, 25.5)
    assert vibration.verify_weighting("Wk", [frequency], measured).passes
    assert not vibration.verify_weighting(
        "Wk", [frequency], measured, expanded_uncertainty_percent=1.0
    ).passes


@pytest.mark.parametrize("bad", [-0.1, math.inf, math.nan])
def test_an_uncertainty_that_is_not_one_is_refused(bad: float) -> None:
    """A negative or non-finite uncertainty is refused, never dropped."""
    with pytest.raises(ValueError, match=r"'expanded_uncertainty_percent'"):
        vibration.verify_weighting(
            "Wk", [16.0], [1.0], expanded_uncertainty_percent=bad
        )


def test_the_coverage_factor_and_the_maximum_permitted_uncertainties() -> None:
    """12.1, and the figures the individual test clauses print.

    13.1 and 14.1 print ``k = 2``; 12.11.2 permits 4,5 %, 12.11.3 3 %,
    12.11.4 5 %, 12.13 3 % and the two timing clauses 0,01 %.
    """
    assert ins.ISO8041_COVERAGE_FACTOR == pytest.approx(2.0)
    printed = {
        "12.7": 2.0,
        "12.10.1": 2.0,
        "12.10.2": 3.0,
        "12.10.2 additional ranges": 4.0,
        "12.11.2": 4.5,
        "12.11.3": 3.0,
        "12.11.4": 5.0,
        "12.13": 3.0,
        "12.14": 2.0,
        "12.18": 0.01,
        "13.9": 2.0,
        "13.11": 4.0,
        "13.14": 2.0,
        "13.15": 0.01,
        "14.9": 5.0,
    }
    assert ins.MAX_EXPANDED_UNCERTAINTY_PERCENT == pytest.approx(printed)


# ---------------------------------------------------------------------------
# The nominal frequency range column of Table 1 (printed folio 9).
# ---------------------------------------------------------------------------
def test_the_nominal_frequency_ranges_are_table_1() -> None:
    """The column 5.7, 5.10 and 12.11 are written against.

    "8 to 1 000" for hand-transmitted vibration, "0,5 to 80" for whole-body,
    "1 to 80" for Wm, which is the exception, and "0,1 to 0,5" for the
    low-frequency whole-body case.
    """
    printed = {
        "Wb": (0.5, 80.0),
        "Wc": (0.5, 80.0),
        "Wd": (0.5, 80.0),
        "We": (0.5, 80.0),
        "Wf": (0.1, 0.5),
        "Wh": (8.0, 1000.0),
        "Wj": (0.5, 80.0),
        "Wk": (0.5, 80.0),
        "Wm": (1.0, 80.0),
    }
    assert ins.NOMINAL_FREQUENCY_RANGE_HZ == printed
    assert set(ins.NOMINAL_FREQUENCY_RANGE_HZ) == set(vibration.WEIGHTING_NAMES)


def test_the_nominal_range_is_nominal_and_not_a_band_centre() -> None:
    """The printed 8 Hz is not the 7,943 Hz band it names.

    Table 1 prints round numbers and Annex B tabulates the response at the
    exact centres ``10**(n/10)``, so the lower bound of the hand-transmitted
    range and the first Annex B row inside it are different numbers. Keeping
    the printed one is the point of the constant.
    """
    lower = ins.NOMINAL_FREQUENCY_RANGE_HZ["Wh"][0]
    assert lower == pytest.approx(8.0)
    assert lower != pytest.approx(10.0 ** (9 / 10), abs=1e-3)


def test_every_nominal_range_ascends() -> None:
    for name, (lower, upper) in ins.NOMINAL_FREQUENCY_RANGE_HZ.items():
        assert 0.0 < lower < upper, name


# ---------------------------------------------------------------------------
# Formula (6), Annex H and the phase verdict.
# ---------------------------------------------------------------------------
def _annex_b_grid(weighting: str) -> tuple[np.ndarray, np.ndarray]:
    """The Annex B one-third-octave grid and its printed phase column."""
    rows = ISO8041_1_ANNEX_B_PHASES_DEG[weighting]
    frequencies = np.array([10.0 ** (n / 10.0) for n, _ in rows])
    printed = np.array([phase for _, phase in rows])
    return frequencies, printed


def _design_phase(weighting: str, frequencies: np.ndarray) -> np.ndarray:
    """The design-goal phase, on the continuous branch Annex B prints."""
    response = vibration.frequency_weighting(weighting, frequencies).response
    return np.degrees(np.unwrap(np.angle(response)))


def test_the_annex_b_phase_columns_reproduce() -> None:
    """All 318 printed phase cells of Tables B.1 to B.9.

    Formula (H.1) defines the design goal as the argument of ``H(s)``, and
    says the values are tabulated in those tables. The worst cell is 0,05
    degrees away from its printed figure, which is the rounding of the
    columns that print one decimal.
    """
    cells = 0
    for weighting, rows in ISO8041_1_ANNEX_B_PHASES_DEG.items():
        frequencies, printed = _annex_b_grid(weighting)
        got = _design_phase(weighting, frequencies)
        assert np.max(np.abs(got - printed)) <= 0.05, weighting
        cells += len(rows)
    assert cells == 318


def test_the_wh_phase_at_158_hz_is_the_printed_cell() -> None:
    """Table B.6, n = 22: 158,5 Hz, factor 0,100 7, phase -93,75 degrees."""
    frequencies, printed = _annex_b_grid("Wh")
    index = [n for n, _ in ISO8041_1_ANNEX_B_PHASES_DEG["Wh"]].index(22)
    assert frequencies[index] == pytest.approx(158.5, rel=1e-3)
    assert printed[index] == pytest.approx(-93.75)
    got = _design_phase("Wh", frequencies)[index]
    assert got == pytest.approx(-93.75, abs=0.05)
    factor = float(np.asarray(vibration.weighting_factors("Wh", frequencies))[index])
    assert factor == pytest.approx(0.1007, rel=1e-3)


def test_a_constant_phase_error_is_graded_at_face_value() -> None:
    """Formula (6) on a constant: ``c`` degrees everywhere gives ``c``."""
    frequencies = np.array([1.0, 1.259, 1.585, 2.0])
    got = vibration.characteristic_phase_deviation(frequencies, np.full(4, 4.5))
    assert got == pytest.approx([4.5, 4.5, 4.5])
    assert got.size == frequencies.size - 1


def test_a_constant_group_delay_is_graded_as_zero() -> None:
    """NOTE 1 of H.2.1, and H.2.3.4 n), as arithmetic.

    A phase deviation proportional to frequency is a constant group delay and
    "would influence neither the vibration parameters to be measured nor the
    characteristic phase deviation values", however large the phase error
    itself grows.
    """
    frequencies = np.array([10.0 ** (n / 10.0) for n in range(-1, 37)])
    deviation = -0.001 * 360.0 * frequencies  # one millisecond of delay
    assert np.max(np.abs(deviation)) > 1000.0
    got = vibration.characteristic_phase_deviation(frequencies, deviation)
    assert np.max(np.abs(got)) == pytest.approx(0.0, abs=1e-9)


def test_the_characteristic_deviation_belongs_to_the_lower_frequency() -> None:
    """(H.3): "at each frequency f_n except for the highest frequency".

    Which decides how a pair straddling a transition frequency is graded: by
    the region of ``f_n``. For Wh the second transition is 10 Hz, so the pair
    (7,943, 10) is graded in the skirt at 12 degrees and the pair (10, 12,59)
    in the central region at 6.
    """
    frequencies = np.array([10.0 ** (n / 10.0) for n in (9, 10, 11)])
    ft2 = ins.TRANSITION_FREQUENCIES_HZ["Wh"][1]
    assert frequencies[1] == pytest.approx(ft2)
    design = _design_phase("Wh", frequencies)
    verdict = vibration.verify_phase_response("Wh", frequencies, design + 9.0)
    assert verdict.characteristic_frequencies_hz == pytest.approx(frequencies[:-1])
    assert verdict.tolerance_deg == pytest.approx([12.0, 6.0])
    # 9 degrees of offset is inside the skirt limit and outside the central one.
    assert list(verdict.within_tolerance) == [True, False]
    assert verdict.failing_frequencies_hz == pytest.approx([frequencies[1]])


def test_the_phase_verdict_turns_at_the_table_5_limit() -> None:
    """The central region allows 6 degrees, and 5,9 is not 6,1."""
    frequencies, _ = _annex_b_grid("Wk")
    design = _design_phase("Wk", frequencies)
    assert vibration.verify_phase_response("Wk", frequencies, design + 5.9).passes
    assert not vibration.verify_phase_response("Wk", frequencies, design + 6.1).passes


def test_the_printed_phase_columns_conform_to_table_5() -> None:
    """A meter that is the printed design goal passes the printed criterion."""
    for weighting in ISO8041_1_ANNEX_B_PHASES_DEG:
        frequencies, printed = _annex_b_grid(weighting)
        verdict = vibration.verify_phase_response(weighting, frequencies, printed)
        assert verdict.passes, weighting
        assert verdict.weighting == weighting
        assert np.max(verdict.characteristic_deviation_deg) < 0.5


def test_the_peak_deviation_is_the_ten_per_cent_annex_h_prints() -> None:
    """(H.4): "For the maximum characteristic phase deviations of 12°, the
    maximum peak value deviation is approximately 10 %".
    """
    assert vibration.peak_deviation_percent(12.0) == pytest.approx(9.9798, abs=5e-4)
    assert vibration.peak_deviation_percent(12.0) == pytest.approx(10.0, abs=0.05)
    # The maximum of the printed formula is over the frequencies supplied.
    assert vibration.peak_deviation_percent([1.0, 12.0, 6.0]) == pytest.approx(
        vibration.peak_deviation_percent(12.0)
    )
    assert vibration.peak_deviation_percent(0.0) == pytest.approx(0.0)


def test_the_peak_deviation_warns_where_annex_h_stops_vouching() -> None:
    """NOTE 2: the approximation "applies to small Δφ0 values only (<30°)".

    The fence is printed as a strict inequality, so 30 degrees is already
    outside what the note vouches for and is warned about; 29,9 is inside.
    """
    with pytest.warns(HumanVibrationWarning, match=r"H\.2\.1, NOTE 2"):
        vibration.peak_deviation_percent(30.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert vibration.peak_deviation_percent(29.9) > 0.0


def test_the_peak_deviation_refuses_what_its_sine_cannot_rank() -> None:
    """Past a quarter turn the maximum of Formula (H.4) stops meaning anything.

    Its sine rises to 90 degrees, falls back to zero at 180 and is negative
    beyond, so the printed maximum stops picking the worst pair and the
    returned magnitude changes sign. An inverted meter, which sits at exactly
    half a turn, would otherwise be told its peak reading costs nothing.
    """
    for outside in (90.0, 180.0, 200.0):
        with pytest.raises(ValueError, match=r"only ranks pairs below"):
            vibration.peak_deviation_percent(outside)
    with pytest.warns(HumanVibrationWarning):
        assert vibration.peak_deviation_percent(89.9) > 0.0


def test_a_negative_characteristic_deviation_is_refused() -> None:
    """Formula (6) prints the quantity inside absolute-value bars."""
    with pytest.raises(ValueError, match=r"'characteristic_phase_deviation_deg'"):
        vibration.peak_deviation_percent([1.0, -0.1])
    assert vibration.peak_deviation_percent([1.0, 0.0]) > 0.0


def test_an_inverted_measurement_is_named_rather_than_only_failed() -> None:
    """H.2.3.4 k): the criterion "is not applicable to signal inversion"."""
    frequencies, _ = _annex_b_grid("Wk")
    design = _design_phase("Wk", frequencies)
    with pytest.warns(HumanVibrationWarning, match=r"H\.2\.3\.4 k\)"):
        verdict = vibration.verify_phase_response("Wk", frequencies, design + 180.0)
    assert not verdict.passes
    assert verdict.characteristic_deviation_deg == pytest.approx(
        np.full(frequencies.size - 1, 180.0)
    )
    # A response that is merely wrong, not inverted, is not called inverted.
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert not vibration.verify_phase_response(
            "Wk", frequencies, design + 20.0
        ).passes


def test_the_phase_verdict_carries_what_it_was_reached_from() -> None:
    """Every field of the verdict, on a response 3 degrees off everywhere."""
    frequencies, _ = _annex_b_grid("Wd")
    design = _design_phase("Wd", frequencies)
    verdict = vibration.verify_phase_response("Wd", frequencies, design + 3.0)
    assert verdict.frequencies_hz == pytest.approx(frequencies)
    assert verdict.measured_phase_deg == pytest.approx(design + 3.0)
    assert verdict.design_phase_deg == pytest.approx(design)
    assert verdict.deviation_deg == pytest.approx(np.full(frequencies.size, 3.0))
    assert verdict.characteristic_deviation_deg == pytest.approx(
        np.full(frequencies.size - 1, 3.0)
    )
    assert verdict.passes
    assert verdict.failing_frequencies_hz.size == 0
    # (H.4) of a 3-degree characteristic deviation, which is the whole record.
    assert verdict.peak_deviation_percent == pytest.approx(
        vibration.peak_deviation_percent(3.0)
    )


def test_a_perfect_phase_response_deviates_by_nothing() -> None:
    frequencies, _ = _annex_b_grid("Wh")
    design = _design_phase("Wh", frequencies)
    verdict = vibration.verify_phase_response("Wh", frequencies, design)
    assert verdict.passes
    assert np.max(verdict.characteristic_deviation_deg) == pytest.approx(0.0, abs=1e-9)
    assert verdict.peak_deviation_percent == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize(
    "call",
    [
        lambda f, p: vibration.characteristic_phase_deviation(f, p),
        lambda f, p: vibration.verify_phase_response("Wk", f, p),
    ],
)
def test_formula_6_needs_a_pair_of_ascending_frequencies(call) -> None:  # noqa: ANN001
    """One frequency is not a pair, and an unordered grid is not a grid.

    The formula divides by ``f(n+1) - f(n)``, so two equal frequencies are a
    division by zero and a descending pair silently reverses the sign of a
    quantity that is then read as a modulus. Both are refused; the ascending
    pair either side of each refusal is the case that works.
    """
    with pytest.raises(ValueError, match=r"'frequencies_hz' must hold at least two"):
        call([16.0], [1.0])
    with pytest.raises(ValueError, match=r"'frequencies_hz' must increase strictly"):
        call([16.0, 16.0], [1.0, 1.0])
    with pytest.raises(ValueError, match=r"'frequencies_hz' must increase strictly"):
        call([20.0, 16.0], [1.0, 1.0])
    assert call([16.0, 20.0], [1.0, 1.0]) is not None


@pytest.mark.parametrize(
    "call",
    [
        lambda f, p: vibration.characteristic_phase_deviation(f, p),
        lambda f, p: vibration.verify_phase_response("Wk", f, p),
    ],
)
def test_the_phase_measurement_is_checked_before_it_is_judged(call) -> None:  # noqa: ANN001
    with pytest.raises(ValueError, match=r"same shape"):
        call([1.0, 2.0, 4.0], [0.0, 0.0])
    with pytest.raises(ValueError, match=r"'frequencies_hz' must be strictly positive"):
        call([0.0, 2.0], [0.0, 0.0])
    with pytest.raises(ValueError, match=r"must contain only finite"):
        call([1.0, 2.0], [0.0, math.nan])


# The factor the second row of Table 2 needs, and the Wf reading (12.7).
# ---------------------------------------------------------------------------
def test_the_two_consistency_tolerances_are_the_printed_ones() -> None:
    """Table 2, rows 2 and 3: 3 % and 2 %."""
    assert ins.WEIGHTING_CONSISTENCY_TOLERANCE_PERCENT == pytest.approx(3.0)
    assert ins.RUNNING_RMS_CONSISTENCY_TOLERANCE_PERCENT == pytest.approx(2.0)


def test_the_band_limited_factor_is_the_ratio_of_the_two_responses() -> None:
    """``|H(f_ref)| / |H_BL(f_ref)|``, which is what 12.7 sets up."""
    for name in vibration.WEIGHTING_NAMES:
        frequencies = [ins.REFERENCE_FREQUENCY_HZ[name]]
        overall = float(np.asarray(vibration.weighting_factors(name, frequencies))[0])
        band = float(np.asarray(vibration.band_limiting_factors(name, frequencies))[0])
        assert ins.band_limited_weighting_factor(name) == pytest.approx(overall / band)


def test_eight_of_the_nine_close_on_the_table_1_factor() -> None:
    """Their band limiting is 0,999 68 or better at the reference frequency.

    So the printed Table 1 factor and the ratio are the same number to
    0,03 %, well inside the 3 % of the second row of Table 2.
    """
    for name, printed in TABLE_1_PRINTED.items():
        if name == ins.LOW_FREQUENCY_WEIGHTING:
            continue
        deviation = abs(ins.band_limited_weighting_factor(name) / printed[1] - 1.0)
        assert deviation * 100.0 < 0.05, name
        assert deviation * 100.0 < ins.WEIGHTING_CONSISTENCY_TOLERANCE_PERCENT, name


def test_the_second_row_of_table_2_cannot_close_for_wf_on_table_1() -> None:
    """The reference frequency of ``Wf`` sits inside its own band-limiting
    skirt, so the two readings of "the appropriate weighting factor" differ
    by more than twice the tolerance of the row they have to satisfy.

    The ratio is the quotient of the two cells Table B.5 prints at the
    neighbouring 0,398 1 Hz band centre, 0,388 4 / 0,927 9.
    """
    ratio = ins.band_limited_weighting_factor("Wf")
    printed_table_1 = TABLE_1_PRINTED["Wf"][1]
    deviation_percent = (ratio / printed_table_1 - 1.0) * 100.0
    assert deviation_percent == pytest.approx(7.75, abs=0.05)
    assert deviation_percent > ins.WEIGHTING_CONSISTENCY_TOLERANCE_PERCENT
    assert ratio == pytest.approx(0.3884 / 0.9279, rel=2e-3)


def test_the_band_limited_factor_refuses_an_unknown_weighting() -> None:
    with pytest.raises(ValueError, match=r"'name'"):
        ins.band_limited_weighting_factor("Wz")


# ---------------------------------------------------------------------------
# Tables 10 and 11: how the running r.m.s. decays after the signal stops.
# ---------------------------------------------------------------------------
# Table 10 (folio 20) and Table 11 (folio 21): time constant, time to 10 % of
# the original value, and the printed tolerance on it, in seconds.
TABLE_10_PRINTED = ((0.125, 0.124, 0.005), (1.0, 0.99, 0.05), (8.0, 7.92, 0.2))
TABLE_11_PRINTED = ((0.125, 0.58, 0.03), (1.0, 4.61, 0.25), (8.0, 36.8, 2.0))
# Table 11 only: the equivalent decay rate, in decibels per second.
TABLE_11_RATE_PRINTED = ((0.125, 31.0, 40.0), (1.0, 3.8, 4.9), (8.0, 0.48, 0.62))


def test_the_two_decay_tables_are_transcribed() -> None:
    assert ins.RUNNING_RMS_DECAY_TIME_S["linear"] == TABLE_10_PRINTED
    assert ins.RUNNING_RMS_DECAY_TIME_S["exponential"] == TABLE_11_PRINTED
    assert ins.RUNNING_RMS_DECAY_RATE_DB_PER_S == TABLE_11_RATE_PRINTED


@pytest.mark.parametrize(
    ("method", "table"),
    [("linear", TABLE_10_PRINTED), ("exponential", TABLE_11_PRINTED)],
)
def test_the_closed_form_decay_lands_inside_the_printed_band(
    method: str, table: tuple[tuple[float, float, float], ...]
) -> None:
    """0,99 tau and 2 tau ln 10, against the six printed cells."""
    for tau, printed, tolerance in table:
        assert (
            abs(ins.running_rms_decay_time(tau, method=method) - printed) <= tolerance
        )


@pytest.mark.parametrize(
    ("method", "table"),
    [("linear", TABLE_10_PRINTED), ("exponential", TABLE_11_PRINTED)],
)
def test_the_running_rms_itself_decays_the_way_the_tables_print(
    method: str, table: tuple[tuple[float, float, float], ...]
) -> None:
    """Measured rather than derived: 5.13 applied to the library's average.

    A steady sinusoid at the whole-body reference frequency is held for the
    5 time constants (linear) or 20 (exponential) the clause asks for, cut,
    and the running r.m.s. timed down to 10 % of the value it had at the cut.
    """
    fs = 5000.0
    frequency = ins.REFERENCE_FREQUENCY_HZ["Wk"]
    for tau, printed, tolerance in table:
        steady = 5.0 * tau if method == "linear" else 20.0 * tau
        decay = 1.5 * tau if method == "linear" else 6.0 * tau
        held = int(round(steady * fs))
        total = held + int(round(decay * fs))
        t = np.arange(total) / fs
        signal = np.where(
            np.arange(total) < held, np.sin(2.0 * math.pi * frequency * t), 0.0
        )
        indicated = vibration.running_rms(
            signal, fs, integration_time=tau, method=method
        )
        after = indicated[held - 1 :]
        measured = int(np.argmax(after < 0.1 * after[0])) / fs
        assert abs(measured - printed) <= tolerance, (method, tau)
        assert ins.verify_running_rms_decay(
            measured, integration_time_s=tau, method=method
        )


def test_the_decay_rate_column_is_the_looser_statement_of_the_same_decay() -> None:
    """Table 11 prints a dB/s band that contains 4,3429 / tau every time.

    It is not the reciprocal of the time column: its limits sit at 0,875 to
    0,892 and 1,128 to 1,151 times the closed-form rate, wider than the
    printed times map to, which is why the time column is the one the
    verdict is taken on.
    """
    for tau, lower, upper in TABLE_11_RATE_PRINTED:
        rate = 20.0 * math.log10(math.e) / (2.0 * tau)
        assert lower <= rate <= upper
        assert lower / rate == pytest.approx(0.883, abs=0.01)
        assert upper / rate == pytest.approx(1.14, abs=0.02)


def test_the_decay_verdict_is_the_printed_interval_and_nothing_wider() -> None:
    """0,99 +- 0,05 s for a 1 s linear average, both sides of the edge."""
    assert ins.verify_running_rms_decay(1.039, integration_time_s=1.0, method="linear")
    assert not ins.verify_running_rms_decay(
        1.041, integration_time_s=1.0, method="linear"
    )
    assert ins.verify_running_rms_decay(0.941, integration_time_s=1.0, method="linear")
    assert not ins.verify_running_rms_decay(
        0.939, integration_time_s=1.0, method="linear"
    )


def test_a_time_constant_the_tables_do_not_print_is_refused() -> None:
    """Tables 10 and 11 print three rows, and there is no band for a fourth.

    The closed form still answers for any averaging time; it is the verdict
    that has nothing printed to be taken against.
    """
    assert ins.running_rms_decay_time(2.0, method="linear") == pytest.approx(1.98)
    with pytest.raises(ValueError, match=r"'integration_time_s'"):
        ins.verify_running_rms_decay(1.98, integration_time_s=2.0, method="linear")


@pytest.mark.parametrize(
    ("call", "match"),
    [
        (
            lambda: ins.running_rms_decay_time(0.0, method="linear"),
            r"'integration_time_s'",
        ),
        (
            lambda: ins.running_rms_decay_time(math.inf, method="linear"),
            r"'integration_time_s'",
        ),
        (lambda: ins.running_rms_decay_time(1.0, method="rms"), r"'method'"),
        (
            lambda: ins.verify_running_rms_decay(
                0.0, integration_time_s=1.0, method="linear"
            ),
            r"'measured_time_s'",
        ),
        (
            lambda: ins.verify_running_rms_decay(
                math.nan, integration_time_s=1.0, method="linear"
            ),
            r"'measured_time_s'",
        ),
        (
            lambda: ins.verify_running_rms_decay(
                1.0, integration_time_s=1.0, method="Linear"
            ),
            r"'method'",
        ),
    ],
)
def test_the_decay_functions_check_what_they_are_given(
    call: object, match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        call()  # type: ignore[operator]
