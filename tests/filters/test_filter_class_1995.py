#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""IEC 61260:1995 in the design verifier: 4.5.3 and 4.9 beside Table 1.

The filter integrated response of 4.5 is :math:`10\lg(B_e/B_r)` with the
effective bandwidth of equation (14), integrated over :math:`f/f_m` with no
:math:`1/\Omega` weight by the trapezoidal rule of equation (16), and the
reference bandwidth :math:`G^{1/(2b)} - G^{-1/(2b)}` of equation (9). The
summation of 4.9 is equation (19) of 5.8.3, run "from the lowest midband
frequency to the highest midband frequency of the filter set" (5.8.4).
Their limits are read off 4.5.3 and 4.9 (BS EN 61260:1996, printed p. 12).
Equations (16) and (19) come with no worked example, so they are anchored in
closed form; the verifier is then held to them on a passing and on failing
banks.
"""

from __future__ import annotations

import math
from types import MappingProxyType

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
    _band_relative_attenuation,
    _bank_bandwidth_deviation,
    _bank_summation,
    _effective_bandwidth_1995,
    _reference_bandwidth_1995,
    _summation_deviation,
    _test_frequencies,
)

#: 10 lg 2: the relative attenuation of an ideal band exactly at its edge.
_HALF_POWER_DB = 10.0 * math.log10(2.0)

#: An octave bank of six bands the 1995 limits below are graded on.
_GRADED_BANK = filters.OctaveFilterBank(
    fs=48000, fraction=1, order=6, limits=[125, 4000]
)


# --------------------------------------------------------------------------
# Equations (9) and (16), in closed form
# --------------------------------------------------------------------------
@pytest.mark.parametrize("fraction", [1, 3])
def test_equation_9_is_the_band_edges_over_the_midband(fraction: int) -> None:
    """B_r = (f_2 - f_1)/f_m = G^(1/(2b)) - G^(-1/(2b))."""
    edge = _G ** (1.0 / (2.0 * fraction))
    assert _reference_bandwidth_1995(fraction) == pytest.approx(
        edge - 1.0 / edge, rel=1e-15
    )


def test_equation_16_integrates_a_flat_response_to_its_span() -> None:
    """With no weight on f/f_m, a flat response telescopes to the grid's span."""
    omega = _test_frequencies(1, 24, -120, 121)
    b_e = _effective_bandwidth_1995(omega, np.zeros(omega.size))
    assert b_e == pytest.approx(float(omega[-1] - omega[0]), rel=1e-14)


@pytest.mark.parametrize(("fraction", "points"), [(1, 24), (3, 24), (3, 48)])
def test_equation_16_on_an_ideal_band(fraction: int, points: int) -> None:
    """An ideal band summed by hand, interval by interval.

    Flat inside the band, half power on its two edges and nothing outside:
    the trapezoids inside the band count whole, the two that reach an edge
    from inside three quarters, the two that reach it from outside one
    quarter, and the rest nothing.
    """
    half = points // 2
    n = 5 * points
    omega = _test_frequencies(fraction, points, -n, n + 1)
    i = np.arange(-n, n + 2)
    delta_a = np.where(
        np.abs(i) < half, 0.0, np.where(np.abs(i) == half, _HALF_POWER_DB, np.inf)
    )
    r = _G ** (1.0 / (fraction * points))
    by_hand = (
        (r ** (half - 1) - r ** -(half - 1))
        + 0.75 * (r ** -(half - 1) - r**-half)
        + 0.75 * (r**half - r ** (half - 1))
        + 0.25 * (r**-half - r ** -(half + 1))
        + 0.25 * (r ** (half + 1) - r**half)
    )
    assert _effective_bandwidth_1995(omega, delta_a) == pytest.approx(
        by_hand, rel=1e-13
    )


def test_the_trapezoids_run_at_least_5s_on_each_side(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """5.4.2: N of equation (16) "shall be equal to or greater than 5S"."""
    assert (
        compliance._INTEGRATION_BANDWIDTHS["1995"]
        == ref.IEC61260_1995_INTEGRATION_SPAN_BANDWIDTHS
    )
    seen: list[np.ndarray] = []

    def spy(omega: np.ndarray, delta_a: np.ndarray) -> float:
        seen.append(omega)
        return _effective_bandwidth_1995(omega, delta_a)

    monkeypatch.setattr(
        compliance,
        "_BANDWIDTH_INTEGRALS",
        MappingProxyType(
            {
                **compliance._BANDWIDTH_INTEGRALS,
                "1995": (spy, _reference_bandwidth_1995),
            }
        ),
    )
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[800, 1200])
    points = filters.verify_filter_class(bank, edition="1995").points_per_bandwidth
    # Every S that 5.3.3 tries integrates over five bandwidths each side, the
    # one graded last.
    assert len(seen) >= 2
    for omega in seen:
        assert omega[0] == pytest.approx(_G**-5.0, rel=1e-13)
    assert seen[-1][-1] == pytest.approx(_G ** (5.0 + 1.0 / points), rel=1e-13)


# --------------------------------------------------------------------------
# The limits of 4.5.3 and 4.9, as the verdict applies them
# --------------------------------------------------------------------------
def test_the_1995_limits_are_the_printed_ones() -> None:
    """4.5.3 and 4.9 of IEC 61260:1995, as the design verifier holds them."""
    assert (
        compliance._BANDWIDTH_LIMITS_DB["1995"]
        == ref.IEC61260_1995_INTEGRATED_RESPONSE_LIMITS_DB
    )
    assert (
        compliance._SUMMATION_LIMITS_DB["1995"] == ref.IEC61260_1995_SUMMATION_LIMITS_DB
    )


@pytest.mark.parametrize(
    ("deviation_db", "expected"),
    [
        (0.15, 0),
        (-0.15, 0),
        (0.16, 1),
        (0.3, 1),
        (-0.31, 2),
        (0.5, 2),
        (0.51, None),
    ],
)
def test_the_integrated_response_limits_grade_every_band(
    monkeypatch: pytest.MonkeyPatch, deviation_db: float, expected: int | None
) -> None:
    """4.5.3: +/-0,15, +/-0,3 and +/-0,5 dB for classes 0, 1 and 2, inclusive."""
    monkeypatch.setattr(
        compliance, "_bank_bandwidth_deviation", lambda *_: deviation_db
    )
    result = filters.verify_filter_class(_GRADED_BANK, edition="1995")
    assert result.requirement_class("effective_bandwidth") == expected


def _flat_summation(delta_p_db: float) -> object:
    """A stand-in for the equation (19) curve: *delta_p_db* at every frequency."""

    def curve(*_: object) -> tuple[np.ndarray, np.ndarray]:
        omega = np.array([0.9, 1.0, 1.1])
        return omega, np.full(omega.shape, delta_p_db)

    return curve


@pytest.mark.parametrize(
    ("delta_p_db", "expected"),
    [
        (1.0, 0),
        (-1.0, 0),
        (1.01, 2),
        (-1.01, 1),
        (-2.0, 1),
        (-2.01, 2),
        (2.0, 2),
        (2.01, None),
        (-4.0, 2),
        (-4.01, None),
    ],
)
def test_the_summation_limits_grade_every_band(
    monkeypatch: pytest.MonkeyPatch, delta_p_db: float, expected: int | None
) -> None:
    """4.9: +/-1,0 dB; +1,0/-2,0 dB and +2,0/-4,0 dB for classes 0, 1, 2."""
    monkeypatch.setattr(compliance, "_bank_summation", _flat_summation(delta_p_db))
    result = filters.verify_filter_class(_GRADED_BANK, edition="1995")
    assert result.requirement_class("summation") == expected


def test_the_4_9_limits_bound_equation_19_as_printed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """5.8.5 applies the 4.9 limits to Delta P of equation (19) as printed.

    Three outputs each 10 lg 3 + 1,5 dB down sum 1,5 dB below the input:
    equation (19) reads -1,5 dB, inside the -2,0 dB of class 1. Read with the
    sign the words of 4.9 and 5.8.3 give it (docs/ERRATA.md) the same sum
    would be +1,5 dB and fail class 1; the verifier follows the equation.
    """
    third = 10.0 * math.log10(3.0)
    delta_p = _summation_deviation(np.full((3, 3), third + 1.5))
    assert delta_p[0] == pytest.approx(-1.5, abs=1e-12)

    def curve(*_: object) -> tuple[np.ndarray, np.ndarray]:
        return np.array([0.9, 1.0, 1.1]), delta_p

    monkeypatch.setattr(compliance, "_bank_summation", curve)
    result = filters.verify_filter_class(_GRADED_BANK, edition="1995")
    assert result.requirement_class("summation") == 1


# --------------------------------------------------------------------------
# 5.3.3: S raised in steps of 12 until the integrated response settles
# --------------------------------------------------------------------------
def _tenths(bank: filters.OctaveFilterBank, points: int) -> list[int]:
    """Each band's filter integrated response at S, to the nearest tenth of a dB."""
    return [
        round(
            10.0
            * _bank_bandwidth_deviation(
                bank.sos[idx],
                int(bank.factor[idx]),
                float(bank.fs),
                float(bank.freq[idx]),
                bank.fraction,
                points,
                "1995",
            )
        )
        for idx in range(bank.num_bands)
    ]


def test_s_stays_where_the_integrated_response_has_settled() -> None:
    """The one-third-octave bank reads the same tenths at S = 24 and at S = 36.

    The 2014 edition has no such rule and keeps the S it is given.
    """
    bank = filters.OctaveFilterBank(48000, fraction=3, limits=[125, 4000])
    assert _tenths(bank, 24) == _tenths(bank, 36)
    assert (
        filters.verify_filter_class(
            bank, edition="1995", num_points=2**10
        ).points_per_bandwidth
        == 24
    )
    assert (
        filters.verify_filter_class(bank, num_points=2**10).points_per_bandwidth == 24
    )


def test_s_is_raised_in_steps_of_12_until_the_tenths_settle() -> None:
    """The octave bank reads +0,0500 dB at S = 24, +0,0497 dB at 36, +0,0496 dB at 48.

    To the nearest tenth that is 0,1, 0,0 and 0,0: it changes from 24 to 36
    and not from 36 to 48, so the bank is graded at S = 36, the integrated
    response and the summation both.
    """
    assert _tenths(_GRADED_BANK, 24) != _tenths(_GRADED_BANK, 36)
    assert _tenths(_GRADED_BANK, 36) == _tenths(_GRADED_BANK, 48)
    result = filters.verify_filter_class(_GRADED_BANK, edition="1995")
    assert result.points_per_bandwidth == 36
    expected = [
        _bank_bandwidth_deviation(
            _GRADED_BANK.sos[idx],
            int(_GRADED_BANK.factor[idx]),
            float(_GRADED_BANK.fs),
            float(_GRADED_BANK.freq[idx]),
            1,
            36,
            "1995",
        )
        for idx in range(_GRADED_BANK.num_bands)
    ]
    np.testing.assert_allclose(
        [b["bandwidth_deviation_db"] for b in result.bands], expected, rtol=1e-12
    )


def test_a_response_that_never_settles_is_taken_at_the_largest_s(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """S stops at sixteen times 24 when the tenths never read the same twice."""

    def alternating(*args: object) -> float:
        points = int(args[5])  # type: ignore[call-overload]
        return 0.05 + 0.001 * (-1) ** (points // 12)

    monkeypatch.setattr(compliance, "_bank_bandwidth_deviation", alternating)
    result = filters.verify_filter_class(_GRADED_BANK, edition="1995", num_points=2**8)
    assert result.points_per_bandwidth == 16 * 24


# --------------------------------------------------------------------------
# 5.8.4: from the lowest to the highest mid-band frequency
# --------------------------------------------------------------------------
def test_the_end_bands_are_read_on_the_half_facing_the_set() -> None:
    """The lowest band from its mid-band up, the highest from its mid-band down.

    The neighbour the set lacks adds nothing to equation (19).
    """
    bank = _GRADED_BANK
    fs = float(bank.fs)
    mids = np.asarray(bank.freq, dtype=np.float64)
    last = bank.num_bands - 1
    omega, curve = _bank_summation(bank.sos, bank.factor, fs, mids, 1, 24, 0, "1995")
    np.testing.assert_allclose(omega, _test_frequencies(1, 24, 0, 12), rtol=1e-15)
    freqs = omega * mids[0]
    by_hand = _summation_deviation(
        np.vstack(
            [
                _band_relative_attenuation(
                    bank.sos[k], int(bank.factor[k]), fs, float(mids[k]), freqs
                )
                for k in (0, 1)
            ]
        )
    )
    np.testing.assert_allclose(curve, by_hand, rtol=1e-12, atol=1e-12)
    omega, _ = _bank_summation(bank.sos, bank.factor, fs, mids, 1, 24, last, "1995")
    np.testing.assert_allclose(omega, _test_frequencies(1, 24, -12, 0), rtol=1e-15)
    result = filters.verify_filter_class(bank, edition="1995")
    assert all(b["summation_min_db"] is not None for b in result.bands)


def test_a_single_band_has_no_summation_to_grade() -> None:
    """4.9 sums the outputs between two mid-band frequencies; one band has none."""
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[800, 1200])
    result = filters.verify_filter_class(bank, edition="1995")
    assert result.requirements == ("relative_attenuation", "effective_bandwidth")


# --------------------------------------------------------------------------
# The verifier on passing and failing banks
# --------------------------------------------------------------------------
@pytest.mark.parametrize("fraction", [1, 3])
def test_the_default_bank_is_class_0_on_4_5_3_and_4_9(fraction: int) -> None:
    """The order 6 Butterworth bank: Delta B near +0,05 dB, Delta P within 0 to +0,17 dB."""
    bank = filters.OctaveFilterBank(
        fs=48000, fraction=fraction, order=6, limits=[125, 4000]
    )
    result = filters.verify_filter_class(bank, edition="1995")
    assert result.requirement_class("effective_bandwidth") == 0
    assert result.requirement_class("summation") == 0
    deviations = [b["bandwidth_deviation_db"] for b in result.bands]
    assert 0.04 < min(deviations) <= max(deviations) < 0.06
    assert min(b["summation_min_db"] for b in result.bands) > -0.01
    assert max(b["summation_max_db"] for b in result.bands) < 0.17


@pytest.mark.parametrize(("order", "expected"), [(3, 1), (2, 2)])
def test_a_shallower_bank_fails_the_class_0_integrated_response(
    order: int, expected: int
) -> None:
    """Shallow Butterworth skirts widen B_e: up to +0,20 dB at order 3, +0,45 dB at order 2."""
    bank = filters.OctaveFilterBank(
        fs=48000, fraction=1, order=order, limits=[125, 4000]
    )
    result = filters.verify_filter_class(bank, edition="1995")
    assert result.requirement_class("effective_bandwidth") == expected


@pytest.mark.parametrize("filter_type", ["cheby1", "ellip"])
def test_a_bank_whose_neighbours_overlap_fails_the_summation(filter_type: str) -> None:
    """Equiripple pass bands that hold to their edges sum 3 dB over the input there.

    A Chebyshev or elliptic band is still within its ripple at the band edge,
    where its neighbour is too, so two whole outputs add: past the +2,0 dB of
    class 2.
    """
    bank = filters.OctaveFilterBank(
        fs=48000,
        fraction=1,
        order=6,
        limits=[125, 4000],
        design=filters.FilterDesign(filter_type),
    )
    result = filters.verify_filter_class(bank, edition="1995")
    assert result.requirement_class("summation") is None
    assert max(b["summation_max_db"] for b in result.bands) == pytest.approx(
        _HALF_POWER_DB, abs=0.01
    )


def test_the_bank_class_is_the_strictest_met_on_all_three() -> None:
    """Order 3: class 0 on Table 1 and 4.9, class 1 on 4.5.3, so class 1."""
    bank = filters.OctaveFilterBank(fs=48000, fraction=1, order=3, limits=[125, 4000])
    result = filters.verify_filter_class(bank, edition="1995")
    assert result.requirement_class("relative_attenuation") == 0
    assert result.requirement_class("summation") == 0
    assert result.overall_class == 1


@pytest.mark.parametrize("requirement", ["effective_bandwidth", "summation"])
@pytest.mark.parametrize("language", ["en", "es"])
def test_each_1995_requirement_plots_under_its_own_clause(
    requirement: str, language: str
) -> None:
    result = filters.verify_filter_class(_GRADED_BANK, edition="1995")
    ax = result.plot(requirement=requirement, language=language)
    title = ax.get_title()
    assert "IEC 61260:1995" in title
    assert (
        ("§4.5" in title) if requirement == "effective_bandwidth" else ("§4.9" in title)
    )
    assert title.endswith(("class 0", "clase 0"))
    labels = {line.get_label() for line in ax.lines}
    assert ("Class 0 limits" if language == "en" else "Límites clase 0") in labels
    plt.close("all")


def test_the_1995_mask_figure_names_its_edition() -> None:
    ax = filters.verify_filter_class(_GRADED_BANK, edition="1995").plot()
    assert ax.get_title().startswith("IEC 61260:1995 class 0 mask")
    plt.close("all")
