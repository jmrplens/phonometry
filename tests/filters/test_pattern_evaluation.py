#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 61260-2:2016 in the design verifier: effective bandwidth and summation.

Formulas (2) and (3) of IEC 61260-2 come with no worked example, so they are
anchored in closed form: a response the formula can be summed by hand gives
the number it has to give, and an ideal band gives a deviation of zero. The
verifier is then held to what the formulas say about the library's own banks.
"""

from __future__ import annotations

import copy
import dataclasses
import math

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref

from phonometry import filters
from phonometry.filters import compliance
from phonometry.filters.compliance import (
    _G,
    _band_class,
    _bank_summation,
    _effective_bandwidth,
    _reference_bandwidth,
    _summation_deviation,
    _test_frequencies,
)

#: 10 lg 2: the relative attenuation of an ideal band exactly at its edge,
#: where it shares the power of a tone with its neighbour.
_HALF_POWER_DB = 10.0 * math.log10(2.0)


# --------------------------------------------------------------------------
# Formula (1): the test frequencies
# --------------------------------------------------------------------------
@pytest.mark.parametrize("fraction", [1, 3, 6, 24])
def test_formula_1_steps_by_g_to_the_one_over_bs(fraction: int) -> None:
    """Omega_i = G^(i/(bS)): S steps span one bandwidth G^(1/b)."""
    s = 24
    omega = _test_frequencies(fraction, s, -s, s)
    ratios = omega[1:] / omega[:-1]
    np.testing.assert_allclose(ratios, _G ** (1.0 / (fraction * s)), rtol=1e-12)
    assert omega[s] == pytest.approx(1.0, abs=1e-15)
    assert omega[s + s // 2] == pytest.approx(_G ** (1.0 / (2 * fraction)), rel=1e-13)
    assert omega[s - s // 2] == pytest.approx(_G ** (-1.0 / (2 * fraction)), rel=1e-13)


def test_fewer_than_24_points_per_bandwidth_is_refused() -> None:
    """7.2.1.4: S "shall be not less than 24"."""
    bank = filters.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[500, 2000])
    with pytest.raises(
        ValueError, match="'points_per_bandwidth' must be a whole number"
    ):
        filters.verify_filter_class(bank, points_per_bandwidth=23)


# --------------------------------------------------------------------------
# Formula (2): the trapezoidal effective bandwidth, in closed form
# --------------------------------------------------------------------------
def test_formula_2_on_a_flat_response_sums_the_interval_weights() -> None:
    """With Delta A = 0 everywhere each interval contributes 2(r-1)/(r+1)."""
    s, b, n = 24, 3, 48
    omega = _test_frequencies(b, s, -n, n + 1)
    r = _G ** (1.0 / (b * s))
    expected = (2 * n + 1) * 2.0 * (r - 1.0) / (r + 1.0)
    assert _effective_bandwidth(omega, np.zeros(omega.size)) == pytest.approx(
        expected, rel=1e-12
    )


def test_formula_2_on_a_uniform_attenuation_scales_by_its_power() -> None:
    """A uniform 3 dB of attenuation scales B_e by 10^(-0.3), exactly."""
    omega = _test_frequencies(1, 24, -48, 49)
    flat = _effective_bandwidth(omega, np.zeros(omega.size))
    three = _effective_bandwidth(omega, np.full(omega.size, 3.0))
    assert three / flat == pytest.approx(10.0**-0.3, rel=1e-12)


@pytest.mark.parametrize(("fraction", "points"), [(1, 24), (3, 24), (3, 48), (12, 24)])
def test_an_ideal_band_has_no_effective_bandwidth_deviation(
    fraction: int, points: int
) -> None:
    """An ideal band gives Delta B = 0, to the trapezoid's own error.

    Zero relative attenuation inside the band, infinite outside, and half
    the power exactly on each edge (10 lg 2 dB): Formula (2) then weighs S
    whole intervals, S * 2(r-1)/(r+1) with r = G^(1/(bS)), against the
    reference (1/b) ln G = S ln r of Formula (15). The ratio is
    tanh(x/2)/(x/2) with x = ln r, so Delta B is -(10 lg e) x^2/12 to leading
    order: 3e-4 dB for octaves at S = 24 and smaller for everything finer.
    """
    n = 2 * points
    omega = _test_frequencies(fraction, points, -n, n + 1)
    i = np.arange(-n, n + 2)
    half = points // 2
    delta_a = np.where(np.abs(i) < half, 0.0, np.inf)
    delta_a[np.abs(i) == half] = _HALF_POWER_DB
    b_e = _effective_bandwidth(omega, delta_a)
    b_r = _reference_bandwidth(fraction)
    x = math.log(_G) / (fraction * points)
    assert b_e / b_r == pytest.approx(math.tanh(x / 2.0) / (x / 2.0), rel=1e-12)
    delta_b = 10.0 * math.log10(b_e / b_r)
    assert abs(delta_b) < 4e-4
    assert delta_b == pytest.approx(-10.0 * math.log10(math.e) * x**2 / 12.0, rel=1e-2)


def test_reference_bandwidth_is_the_printed_note_of_5_11_3() -> None:
    """IEC 61260-1:2014 5.11.3 NOTE: 0,690 776 (octave), 0,230 259 (third)."""
    assert _reference_bandwidth(1) == pytest.approx(0.690776, abs=5e-7)
    assert _reference_bandwidth(3) == pytest.approx(0.230259, abs=5e-7)


# --------------------------------------------------------------------------
# Formula (3): the summation of output signals, in closed form
# --------------------------------------------------------------------------
def test_an_ideal_bank_sums_to_the_input_everywhere() -> None:
    """Inside a band only it passes; on an edge two share the power: Delta P = 0."""
    inside = _summation_deviation(np.array([[np.inf], [0.0], [np.inf]]))
    edge = _summation_deviation(
        np.array([[np.inf], [_HALF_POWER_DB], [_HALF_POWER_DB]])
    )
    assert inside[0] == 0.0
    assert edge[0] == pytest.approx(0.0, abs=1e-15)


def test_formula_3_adds_powers_not_levels() -> None:
    """Three outputs each 10 lg 3 dB down restore the input; three at 0 dB add 10 lg 3."""
    third = 10.0 * math.log10(3.0)
    assert _summation_deviation(np.full((3, 1), third))[0] == pytest.approx(
        0.0, abs=1e-14
    )
    assert _summation_deviation(np.zeros((3, 1)))[0] == pytest.approx(third, rel=1e-14)


# --------------------------------------------------------------------------
# The acceptance limits of 5.12.2 and 5.16, as the verdict applies them
# --------------------------------------------------------------------------
#: A one-third-octave bank whose seven bands the limits below are graded on.
_GRADED_BANK = filters.OctaveFilterBank(
    fs=48000, fraction=3, order=6, limits=[500, 2000]
)


def test_the_pattern_limits_are_the_printed_ones() -> None:
    """IEC 61260-1:2014 5.12.2 and 5.16, as the design verifier holds them."""
    assert compliance._BANDWIDTH_LIMITS_DB == ref.IEC61260_1_BANDWIDTH_LIMITS_DB
    assert compliance._SUMMATION_LIMITS_DB == ref.IEC61260_1_SUMMATION_LIMITS_DB


@pytest.mark.parametrize(
    ("deviation_db", "expected"),
    [(0.4, 1), (-0.4, 1), (0.41, 2), (-0.6, 2), (0.61, None)],
)
def test_the_bandwidth_limits_grade_every_band(
    monkeypatch: pytest.MonkeyPatch, deviation_db: float, expected: int | None
) -> None:
    """5.12.2: +/-0,4 dB for class 1 and +/-0,6 dB for class 2, inclusive."""
    monkeypatch.setattr(
        compliance, "_bank_bandwidth_deviation", lambda *_: deviation_db
    )
    result = filters.verify_filter_class(_GRADED_BANK)
    assert result.requirement_class("effective_bandwidth") == expected


def _flat_summation(delta_p_db: float) -> object:
    """A stand-in for the Formula (3) curve: *delta_p_db* at every frequency."""

    def curve(*_: object) -> tuple[np.ndarray, np.ndarray]:
        omega = np.array([0.9, 1.0, 1.1])
        return omega, np.full(omega.shape, delta_p_db)

    return curve


@pytest.mark.parametrize(
    ("delta_p_db", "expected"),
    [
        (0.8, 1),
        (0.81, 2),
        (-1.8, 1),
        (-1.81, 2),
        (1.8, 2),
        (1.81, None),
        (-3.8, 2),
        (-3.81, None),
    ],
)
def test_the_summation_limits_grade_every_inner_band(
    monkeypatch: pytest.MonkeyPatch, delta_p_db: float, expected: int | None
) -> None:
    """5.16: +0,8/-1,8 dB for class 1 and +1,8/-3,8 dB for class 2, inclusive."""
    monkeypatch.setattr(compliance, "_bank_summation", _flat_summation(delta_p_db))
    result = filters.verify_filter_class(_GRADED_BANK)
    assert result.requirement_class("summation") == expected


@pytest.mark.parametrize(("offset_db", "expected"), [(-1.0, 2), (1.0, 1)])
def test_the_5_16_limits_bound_formula_3_as_printed(
    monkeypatch: pytest.MonkeyPatch, offset_db: float, expected: int
) -> None:
    """7.2.4.5 applies +0,8/-1,8 dB to Delta P_j of Formula (3) as printed.

    Three outputs each 10 lg 3 - 1 dB down sum 1 dB above the input: Formula
    (3) reads +1 dB, past the +0,8 dB of class 1. Read with the sign the
    words of 7.2.4.3 and 5.16 give it (docs/ERRATA.md) the same sum would be
    -1 dB and class 1; the verifier follows the formula.
    """
    third = 10.0 * math.log10(3.0)
    delta_p = _summation_deviation(np.full((3, 3), third + offset_db))
    assert delta_p[0] == pytest.approx(-offset_db, abs=1e-12)

    def curve(*_: object) -> tuple[np.ndarray, np.ndarray]:
        return np.array([0.9, 1.0, 1.1]), delta_p

    monkeypatch.setattr(compliance, "_bank_summation", curve)
    result = filters.verify_filter_class(_GRADED_BANK)
    assert result.requirement_class("summation") == expected


def test_a_band_on_its_limit_meets_the_class() -> None:
    """Every limit is inclusive: a margin of exactly zero meets the class."""
    band = {
        "margin_class1_db": 0.0,
        "margin_class2_db": 0.2,
        "bandwidth_margin_class1_db": 0.0,
        "bandwidth_margin_class2_db": 0.2,
        "summation_margin_class1_db": -1e-9,
        "summation_margin_class2_db": 0.0,
    }
    assert _band_class(band, (1, 2)) == 2
    band["summation_margin_class1_db"] = 0.0
    assert _band_class(band, (1, 2)) == 1


# --------------------------------------------------------------------------
# The verifier on the library's banks
# --------------------------------------------------------------------------
def test_third_octave_default_meets_class1_on_every_requirement() -> None:
    bank = filters.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[100, 5000])
    result = filters.verify_filter_class(bank)
    assert result.requirements == (
        "relative_attenuation",
        "effective_bandwidth",
        "summation",
    )
    assert {r: result.requirement_class(r) for r in result.requirements} == {
        "relative_attenuation": 1,
        "effective_bandwidth": 1,
        "summation": 1,
    }
    deviations = [b["bandwidth_deviation_db"] for b in result.bands]
    assert min(deviations) > 0.04
    assert max(deviations) < 0.06


@pytest.mark.parametrize("i", [-5, 5])
def test_the_summation_is_what_tones_through_the_bank_read(i: int) -> None:
    """Formula (3) on the designed sections is what the running bank delivers.

    A tone at the test frequencies where the 500 Hz band of a decimated
    octave bank of order 2 sums its neighbours highest, filtered by the bank
    itself (anti-alias decimation included), and the three band levels summed
    on an energy basis re the level a mid-band tone reads: the same Delta P
    the verifier computes, to a hundredth of a decibel. The shallow order 2
    skirts overlap enough for the sum to pass +0.45 dB there, so the
    agreement is not two zeros agreeing.
    """
    fs = 48000
    bank = filters.OctaveFilterBank(fs=fs, fraction=1, order=2, limits=[125, 4000])
    assert bank.factor[1] > 1
    j = 2
    time_s = np.arange(4 * fs) / fs
    mid = float(bank.freq[j])
    reference = bank.filter(np.sin(2.0 * np.pi * mid * time_s)).levels[j]
    tone_hz = mid * _G ** (i / 24)
    levels = bank.filter(np.sin(2.0 * np.pi * tone_hz * time_s)).levels
    measured = 10.0 * math.log10(
        sum(10.0 ** (levels[k] / 10.0) for k in (j - 1, j, j + 1))
    ) - float(reference)
    rates = np.asarray([fs / float(f) for f in bank.factor])
    omega, curve = _bank_summation(
        bank.sos, np.asarray(bank.freq, dtype=float), rates, 1, 24, j
    )
    computed = float(curve[np.argmin(np.abs(omega - _G ** (i / 24)))])
    assert computed > 0.45
    assert measured == pytest.approx(computed, abs=0.01)


def test_end_bands_carry_no_summation() -> None:
    """7.2.4.4 runs the test from the second band to the last but one."""
    bank = filters.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[500, 2000])
    result = filters.verify_filter_class(bank)
    for band in (result.bands[0], result.bands[-1]):
        assert band["summation_min_db"] is None
        assert band["summation_max_db"] is None
        assert band["summation_margin_class1_db"] is None
    for band in result.bands[1:-1]:
        assert band["summation_min_db"] <= band["summation_max_db"]


@pytest.mark.parametrize("limits", [[800, 1200], [500, 1000]])
def test_a_bank_with_no_inner_band_is_not_graded_on_the_summation(
    limits: list[int],
) -> None:
    """One or two bands leave 7.2.4.4 nothing to test: 5.16 is not graded."""
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=limits)
    result = filters.verify_filter_class(bank)
    assert result.requirements == ("relative_attenuation", "effective_bandwidth")
    with pytest.raises(KeyError, match="'summation' was not graded"):
        result.requirement_class("summation")


def test_the_band_class_is_the_strictest_met_on_every_requirement() -> None:
    """A band misses class 1 as soon as one requirement does."""
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[125, 4000])
    result = filters.verify_filter_class(bank)
    for band in result.bands:
        margins = [
            band["margin_class1_db"],
            band["bandwidth_margin_class1_db"],
            band["summation_margin_class1_db"],
        ]
        meets_1 = all(m is None or m >= 0.0 for m in margins)
        assert (band["class"] == 1) == meets_1


def test_a_finer_grid_moves_the_verdict_by_nothing_it_can_see() -> None:
    """S = 24 is converged: S = 48 moves Delta B by well under 0.01 dB."""
    bank = filters.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[500, 2000])
    coarse = filters.verify_filter_class(bank)
    fine = filters.verify_filter_class(bank, points_per_bandwidth=48)
    assert fine.points_per_bandwidth == 48
    for a, b in zip(coarse.bands, fine.bands, strict=True):
        assert a["bandwidth_deviation_db"] == pytest.approx(
            b["bandwidth_deviation_db"], abs=1e-3
        )


def test_stateful_bank_grades_like_its_stateless_twin() -> None:
    kwargs = {
        "fs": 48000,
        "fraction": 3,
        "order": 6,
        "limits": [500, 2000],
        "design": filters.FilterDesign(resample=False),
    }
    stateful = filters.OctaveFilterBank(
        **kwargs, block_processing=filters.BlockProcessing(stateful=True)
    )
    stateless = filters.OctaveFilterBank(**kwargs)
    a = filters.verify_filter_class(stateful)
    b = filters.verify_filter_class(stateless)
    for x, y in zip(a.bands, b.bands, strict=True):
        assert x["bandwidth_deviation_db"] == y["bandwidth_deviation_db"]
        assert x["summation_max_db"] == y["summation_max_db"]


def test_the_1995_edition_grades_table_1_alone() -> None:
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[250, 4000])
    result = filters.verify_filter_class(bank, edition="1995")
    assert result.requirements == ("relative_attenuation",)
    assert "bandwidth_deviation_db" not in result.bands[0]
    with pytest.raises(KeyError, match="'summation' was not graded"):
        result.requirement_class("summation")


def test_binding_margin_reads_the_requirement_and_refuses_a_foreign_class() -> None:
    bank = filters.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[500, 2000])
    result = filters.verify_filter_class(bank)
    expected = min(b["bandwidth_margin_class1_db"] for b in result.bands)
    assert result.binding_margin_db("effective_bandwidth", 1) == expected
    with pytest.raises(KeyError, match="class 0 is not one of"):
        result.binding_margin_db("effective_bandwidth", 0)


def test_a_verdict_refuses_a_requirement_carried_by_some_bands_only() -> None:
    bank = filters.OctaveFilterBank(fs=48000, fraction=3, order=6, limits=[500, 2000])
    result = filters.verify_filter_class(bank)
    bands = tuple(copy.deepcopy(b) for b in result.bands)
    del bands[2]["bandwidth_margin_class1_db"]
    with pytest.raises(
        ValueError, match="'effective_bandwidth' requirement in every band"
    ):
        dataclasses.replace(result, bands=bands)


@pytest.mark.parametrize("requirement", ["effective_bandwidth", "summation"])
@pytest.mark.parametrize("language", ["en", "es"])
def test_each_requirement_plots(requirement: str, language: str) -> None:
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[125, 4000])
    result = filters.verify_filter_class(bank)
    ax = result.plot(requirement=requirement, language=language)
    title = ax.get_title()
    assert (
        ("5.12" in title) if requirement == "effective_bandwidth" else ("5.16" in title)
    )
    if requirement == "summation":
        # The default octave bank is class 1 on 5.16.
        assert title.endswith(("class 1", "clase 1"))
    plt.close("all")


@pytest.mark.parametrize("requirement", ["effective_bandwidth", "summation"])
def test_a_failing_requirement_is_drawn_inside_the_axes(requirement: str) -> None:
    """A bank past both classes: every value it is graded on stays in view."""
    bank = filters.OctaveFilterBank(
        48000,
        fraction=3,
        order=2,
        limits=[125, 1000],
        design=filters.FilterDesign("cheby1", ripple=3.0),
    )
    result = filters.verify_filter_class(bank)
    assert result.requirement_class(requirement) is None
    ax = result.plot(requirement=requirement)
    low, high = ax.get_ylim()
    drawn = np.concatenate([np.asarray(line.get_ydata(), float) for line in ax.lines])
    drawn = drawn[np.isfinite(drawn)]
    assert low <= float(np.min(drawn))
    assert float(np.max(drawn)) <= high
    plt.close("all")


def test_the_class_mask_of_a_full_rate_band_stops_at_g_squared() -> None:
    """Filtered at the full rate, a band's window stops at the G**2 breakpoint."""
    bank = filters.OctaveFilterBank(
        48000,
        fraction=1,
        order=6,
        limits=[125, 4000],
        design=filters.FilterDesign(resample=False),
    )
    ax = filters.verify_filter_class(bank).plot()
    low, high = ax.get_xlim()
    assert high == pytest.approx(_G**2)
    assert low == pytest.approx(_G**-2)
    labels = [t.get_text() for t in ax.get_xticklabels()]
    assert labels == ["0.5", "0.7", "1", "1.4", "2"]
    plt.close("all")


def test_plotting_a_requirement_the_verdict_did_not_grade_is_refused() -> None:
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[250, 4000])
    result = filters.verify_filter_class(bank, edition="1995")
    with pytest.raises(ValueError, match="'requirement' must be one of"):
        result.plot(requirement="summation")
