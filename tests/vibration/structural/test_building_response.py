#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the empirical predictors of ISO 4866:2010 Annex D.

Anchored on the printed formulae: the storey rule ``f = 10/n`` of D.2, the
three code forms (D.1), (D.2) and (D.3) with the coefficient ranges the annex
prints for each, the measured fit ``f = 46/h`` of D.3 with its ± 50 % band,
and the damping range of D.4.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import vibration
from phonometry.vibration.structural import building_response as br


def test_the_three_coefficient_ranges_are_the_printed_ones() -> None:
    """D.2 prints a range for each of its three code forms."""
    assert br.PERIOD_COEFFICIENT_RANGES["height"] == pytest.approx((0.014, 0.03))
    assert br.PERIOD_COEFFICIENT_RANGES["height_width"] == pytest.approx((0.087, 0.109))
    assert br.PERIOD_COEFFICIENT_RANGES["slenderness"] == pytest.approx((0.06, 0.08))


def test_the_storey_model_is_the_rule_din_4150_3_also_prints() -> None:
    """``T = 0,1 n`` and ``f = 10/n`` are the same sentence twice."""
    for n in (5, 8, 10, 20):
        assert br.fundamental_period("storeys", storeys=n) == pytest.approx(0.1 * n)
        assert br.fundamental_frequency("storeys", storeys=n) == pytest.approx(
            vibration.storey_fundamental_frequency(n)
        )


def test_formula_d_1_is_linear_in_the_height() -> None:
    """``T = k1 h``, with the coefficient the caller states."""
    assert br.fundamental_period(
        "height", height_m=50.0, coefficient=0.014
    ) == pytest.approx(0.7)
    assert br.fundamental_period(
        "height", height_m=50.0, coefficient=0.03
    ) == pytest.approx(1.5)


def test_the_default_coefficient_is_the_middle_of_the_printed_range() -> None:
    """D.2 gives a range and no way to choose inside it, so take the middle."""
    for model, (low, high) in br.PERIOD_COEFFICIENT_RANGES.items():
        kwargs: dict = {"height_m": 40.0}
        if model != "height":
            kwargs["width_m"] = 25.0
        default = br.fundamental_period(model, **kwargs)
        middle = br.fundamental_period(model, coefficient=0.5 * (low + high), **kwargs)
        assert default == pytest.approx(middle)


def test_the_midpoint_of_k1_is_the_coefficient_the_measured_fit_gives() -> None:
    """A quiet agreement worth pinning: 0,022 twice, from two directions.

    The middle of the ``k1`` range the codes span is 0,022 s/m, and D.3's fit
    to 163 measured buildings prints ``T = 0,022 h`` s. The default height
    model therefore lands within a percent and a half of ``f = 46/h``, which
    is a good deal closer than the ± 50 % the annex warns about.
    """
    low, high = br.PERIOD_COEFFICIENT_RANGES["height"]
    assert 0.5 * (low + high) == pytest.approx(br.HEIGHT_PERIOD_COEFFICIENT_S_PER_M)
    predicted = br.fundamental_frequency("height", height_m=46.0)
    assert predicted == pytest.approx(
        float(br.height_fundamental_frequency(46.0)), rel=0.02
    )


def test_formula_d_2_divides_by_the_root_of_the_width() -> None:
    """``T = k2 h / sqrt(b)``."""
    got = br.fundamental_period(
        "height_width", height_m=60.0, width_m=20.0, coefficient=0.1
    )
    assert got == pytest.approx(0.1 * 60.0 / math.sqrt(20.0))


def test_formula_d_3_adds_the_slenderness_factor() -> None:
    """``T = (k3 h / sqrt(b)) sqrt(h / (h + b))``, always shorter than (D.2)."""
    kw = {"height_m": 60.0, "width_m": 20.0, "coefficient": 0.1}
    plain = br.fundamental_period("height_width", **kw)
    slender = br.fundamental_period("slenderness", **kw)
    assert slender == pytest.approx(plain * math.sqrt(60.0 / 80.0))
    assert slender < plain


def test_a_wider_building_of_the_same_height_is_stiffer() -> None:
    """Both width-aware forms shorten the period as the building widens."""
    for model in ("height_width", "slenderness"):
        narrow = br.fundamental_period(model, height_m=50.0, width_m=10.0)
        wide = br.fundamental_period(model, height_m=50.0, width_m=40.0)
        assert wide < narrow


def test_the_measured_fit_of_d_3() -> None:
    """``f = 46/h`` hertz, and the same line as a period."""
    assert br.height_fundamental_frequency(46.0) == pytest.approx(1.0)
    assert br.height_fundamental_frequency(92.0) == pytest.approx(0.5)
    assert br.HEIGHT_FREQUENCY_CONSTANT_HZ_M == pytest.approx(46.0)
    assert br.HEIGHT_PERIOD_COEFFICIENT_S_PER_M == pytest.approx(0.022)


def test_the_fit_takes_an_array_of_heights() -> None:
    got = br.height_fundamental_frequency([23.0, 46.0, 92.0])
    assert isinstance(got, np.ndarray)
    assert got == pytest.approx([2.0, 1.0, 0.5])


@pytest.mark.parametrize("bad", [0.0, -10.0, math.inf, math.nan])
def test_the_fit_refuses_a_height_that_is_not_one(bad: float) -> None:
    with pytest.raises(ValueError, match=r"'height' must be positive and finite"):
        br.height_fundamental_frequency(bad)


def test_the_error_band_is_the_fifty_percent_the_annex_prints() -> None:
    """D.3: "errors of ± 50 % are not uncommon"."""
    assert br.EMPIRICAL_FREQUENCY_TOLERANCE == pytest.approx(0.5)
    assert br.empirical_frequency_bounds(2.0) == pytest.approx((1.0, 3.0))


def test_the_damping_range_of_d_4() -> None:
    """D.4 reports measurements, not a predictor: 0,5 % to 2,1 % of critical."""
    assert br.DAMPING_RATIO_RANGE == pytest.approx((0.005, 0.021))


def test_a_model_needs_the_arguments_it_is_written_on() -> None:
    with pytest.raises(ValueError, match=r"needs 'storeys'"):
        br.fundamental_period("storeys")
    with pytest.raises(ValueError, match=r"'height' model needs 'height_m'"):
        br.fundamental_period("height")
    with pytest.raises(ValueError, match=r"'height_width' model needs 'width_m'"):
        br.fundamental_period("height_width", height_m=40.0)
    with pytest.raises(ValueError, match=r"'slenderness' model needs 'width_m'"):
        br.fundamental_period("slenderness", height_m=40.0)


def test_a_model_refuses_an_argument_it_does_not_use() -> None:
    """Every form is written on its own dimensions, and only on those.

    Taking an argument a form ignores is worse than refusing it: a height
    handed to the storey model would be carried into the estimate and drawn on
    Figure D.1 as if the prediction had used it.
    """
    with pytest.raises(ValueError, match=r"'storeys' model does not use 'coefficient'"):
        br.fundamental_period("storeys", storeys=10, coefficient=0.022)
    with pytest.raises(ValueError, match=r"'storeys' model does not use 'height_m'"):
        br.fundamental_period("storeys", storeys=10, height_m=60.0)
    with pytest.raises(ValueError, match=r"'height' model does not use 'width_m'"):
        br.fundamental_period("height", height_m=60.0, width_m=15.0)
    with pytest.raises(ValueError, match=r"does not use 'storeys'"):
        br.fundamental_period("height_width", height_m=60.0, width_m=15.0, storeys=18)


def test_the_estimate_refuses_the_height_it_would_have_drawn_wrongly() -> None:
    """The regression behind the rule above, at the entry point that draws."""
    with pytest.raises(ValueError, match=r"'storeys' model does not use 'height_m'"):
        br.estimate_fundamental_frequency("storeys", storeys=10, height_m=60.0)


def test_a_model_outside_the_four_is_refused() -> None:
    with pytest.raises(ValueError, match=r"'model' must be one of"):
        br.fundamental_period("finite_element", height_m=40.0)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"height_m": 0.0}, r"'height_m'"),
        ({"height_m": 40.0, "width_m": -1.0}, r"'width_m'"),
        ({"height_m": 40.0, "width_m": 20.0, "coefficient": 0.0}, r"'coefficient'"),
    ],
)
def test_a_dimension_that_is_not_one_is_refused(kwargs: dict, match: str) -> None:
    with pytest.raises(ValueError, match=match):
        br.fundamental_period("height_width", **kwargs)


def test_the_estimate_carries_the_coefficient_and_the_band() -> None:
    got = br.estimate_fundamental_frequency("height", height_m=46.0)
    assert got.period_s == pytest.approx(1.0 / got.frequency_hz)
    assert got.coefficient == pytest.approx(0.022)
    assert got.height_m == pytest.approx(46.0)
    low, high = got.bounds_hz
    assert low == pytest.approx(0.5 * got.frequency_hz)
    assert high == pytest.approx(1.5 * got.frequency_hz)


def test_the_storey_estimate_carries_no_coefficient_and_no_height() -> None:
    got = br.estimate_fundamental_frequency("storeys", storeys=10)
    assert got.coefficient is None
    assert got.height_m is None
    assert got.frequency_hz == pytest.approx(1.0)


def test_the_storey_estimate_cannot_be_placed_on_figure_d_1() -> None:
    """The figure is drawn against height, and this model never saw one."""
    got = br.estimate_fundamental_frequency("storeys", storeys=10)
    with pytest.raises(ValueError, match=r"storey model has no height"):
        got.plot()


def test_the_names_are_exported_from_the_domain() -> None:
    assert vibration.fundamental_frequency("storeys", storeys=10) == pytest.approx(1.0)
    assert vibration.PERIOD_MODELS == br.PERIOD_MODELS
    assert vibration.DAMPING_RATIO_RANGE == pytest.approx((0.005, 0.021))
