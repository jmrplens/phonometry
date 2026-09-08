#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the ISO 8041-1:2017 instrument verification.

Anchored on the printed tables: the transition frequencies of Table 4, the
tolerance bands of Table 5, the reference conditions of Table 1 and the
indication tolerances of Table 2.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import vibration
from phonometry.vibration.human import instrumentation as ins

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
        lambda: ins.weighting_tolerance_percent("Wz", [1.0]),
        lambda: ins.phase_tolerance_degrees("Wz", [1.0]),
        lambda: ins.indication_tolerance_percent("Wz"),
        lambda: ins.reference_indication("Wz"),
    ):
        with pytest.raises(ValueError, match=r"'name'"):
            call()
