#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for :mod:`phonometry.uncertainty` (GUM Guide 98-3 and Supplement 1).

Validated against the Guides' own worked examples: the combined uncertainty of
the additive model (Supplement 1 clause 9.2), the coverage factor of the
end-gauge example (GUM Annex H.1 / Table G.2), the Welch-Satterthwaite
effective degrees of freedom (Annex G.4) and the Monte Carlo coverage interval
of the four-rectangular additive model (Supplement 1 Table 3, clause 9.2.3).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import uncertainty as u


def _add4(a, b, c, d):  # type: ignore[no-untyped-def]
    return a + b + c + d


def test_additive_model_combined_uncertainty() -> None:
    # Supplement 1 clause 9.2: y = x1+x2+x3+x4, u(xi)=1 -> uc = 2.0.
    qs = [u.Quantity(0.0, 1.0) for _ in range(4)]
    result = u.combine_uncertainty(_add4, qs)
    assert result.value == pytest.approx(0.0)
    assert result.combined_uncertainty == pytest.approx(2.0, abs=1e-6)
    np.testing.assert_allclose(result.sensitivities, 1.0, atol=1e-6)


def test_coverage_factor_matches_gum_table() -> None:
    # GUM Annex H.1 / Table G.2: t at p=0.99, v=16 -> k = 2.92.
    assert u.coverage_factor(0.99, 16) == pytest.approx(2.92, abs=5e-3)
    # Large dof approaches the normal quantile.
    assert u.coverage_factor(0.95) == pytest.approx(1.960, abs=1e-3)
    assert u.coverage_factor(0.9545) == pytest.approx(2.0, abs=1e-3)


def test_end_gauge_expanded_uncertainty() -> None:
    # GUM Annex H.1: uc = 32 nm, v_eff = 16 -> U99 = 2.92 * 32 = 93 nm.
    k = u.coverage_factor(0.99, 16)
    assert k * 32.0 == pytest.approx(93.0, abs=1.0)


def test_welch_satterthwaite_effective_dof() -> None:
    # Equal contributions each with dof v -> v_eff = N*v (Annex G.4).
    qs = [u.Quantity(0.0, 1.0, dof=10) for _ in range(4)]
    result = u.combine_uncertainty(_add4, qs)
    assert result.effective_dof == pytest.approx(40.0, abs=1e-6)


def test_all_type_b_gives_infinite_dof() -> None:
    qs = [u.rectangular(0.0, 1.0), u.triangular(0.0, 1.0)]
    result = u.combine_uncertainty(lambda a, b: a + b, qs)
    assert math.isinf(result.effective_dof)
    _, big = result.expanded(0.95)
    assert big == pytest.approx(1.960 * result.combined_uncertainty, rel=1e-3)


def test_type_b_standard_uncertainties() -> None:
    assert u.rectangular(5.0, 3.0).uncertainty == pytest.approx(3.0 / math.sqrt(3))
    assert u.triangular(5.0, 3.0).uncertainty == pytest.approx(3.0 / math.sqrt(6))
    assert u.u_shaped(5.0, 3.0).uncertainty == pytest.approx(3.0 / math.sqrt(2))


def test_correlation_matrix() -> None:
    # Fully correlated sum: uc = u1 + u2 (not the quadrature sum).
    qs = [u.Quantity(0.0, 1.0), u.Quantity(0.0, 1.0)]
    r = np.array([[1.0, 1.0], [1.0, 1.0]])
    result = u.combine_uncertainty(lambda a, b: a + b, qs, correlation=r)
    assert result.combined_uncertainty == pytest.approx(2.0, abs=1e-6)
    # Uncorrelated for comparison: sqrt(2).
    plain = u.combine_uncertainty(lambda a, b: a + b, qs)
    assert plain.combined_uncertainty == pytest.approx(math.sqrt(2.0), abs=1e-6)


def test_monte_carlo_matches_supplement1_table3() -> None:
    # Supplement 1 Table 3 (clause 9.2.3): four rectangular Xi, mean 0, sd 1
    # -> u(y) = 2.00 and a 95 % symmetric coverage interval ~ [-3.88, 3.88].
    qs = [u.Quantity(0.0, 1.0, "rectangular") for _ in range(4)]
    mc = u.monte_carlo(_add4, qs, trials=2_000_000, coverage=0.95, seed=42)
    assert mc.value == pytest.approx(0.0, abs=0.01)
    assert mc.standard_uncertainty == pytest.approx(2.0, abs=0.01)
    assert mc.interval[0] == pytest.approx(-3.88, abs=0.03)
    assert mc.interval[1] == pytest.approx(3.88, abs=0.03)


def test_monte_carlo_agrees_with_gum_for_linear_gaussian() -> None:
    qs = [u.Quantity(10.0, 0.5), u.Quantity(5.0, 0.3)]
    gum = u.combine_uncertainty(lambda a, b: a - b, qs)
    mc = u.monte_carlo(lambda a, b: a - b, qs, trials=1_000_000, coverage=0.95, seed=1)
    assert mc.value == pytest.approx(gum.value, abs=0.01)
    assert mc.standard_uncertainty == pytest.approx(gum.combined_uncertainty, rel=0.02)


def test_nonlinear_model_sensitivities() -> None:
    # y = a * b: dy/da = b, dy/db = a at the estimates.
    qs = [u.Quantity(3.0, 0.1), u.Quantity(4.0, 0.2)]
    result = u.combine_uncertainty(lambda a, b: a * b, qs)
    assert result.value == pytest.approx(12.0)
    np.testing.assert_allclose(result.sensitivities, [4.0, 3.0], atol=1e-4)
    # uc = sqrt((4*0.1)^2 + (3*0.2)^2) = sqrt(0.16+0.36) = sqrt(0.52).
    assert result.combined_uncertainty == pytest.approx(math.sqrt(0.52), abs=1e-4)


def test_zero_uncertainty_input() -> None:
    # A constant (zero-uncertainty) input contributes nothing but is handled.
    qs = [u.Quantity(2.0, 0.0), u.Quantity(3.0, 0.5)]
    result = u.combine_uncertainty(lambda a, b: a + b, qs)
    assert result.value == pytest.approx(5.0)
    assert result.contributions[0] == pytest.approx(0.0)
    assert result.combined_uncertainty == pytest.approx(0.5, abs=1e-6)


def test_expanded_uncertainty_function() -> None:
    qs = [u.Quantity(0.0, 1.0) for _ in range(4)]
    result = u.combine_uncertainty(_add4, qs)
    k, big = u.expanded_uncertainty(result, 0.95)
    assert k == pytest.approx(1.960, abs=1e-3)
    assert big == pytest.approx(k * 2.0, abs=1e-6)


@pytest.mark.parametrize("dist", ["triangular", "u-shaped", "gaussian"])
def test_monte_carlo_distributions_recover_std(dist: str) -> None:
    # Every PDF is parameterised so that its standard deviation is the given
    # standard uncertainty; the Monte Carlo std must recover it.
    qs = [u.Quantity(0.0, 1.0, dist) for _ in range(2)]
    mc = u.monte_carlo(lambda a, b: a + b, qs, trials=500_000, coverage=0.95, seed=7)
    assert mc.standard_uncertainty == pytest.approx(math.sqrt(2.0), rel=0.03)


@pytest.mark.parametrize("dist", ["gaussian", "rectangular", "triangular", "u-shaped"])
def test_monte_carlo_zero_uncertainty_input(dist: str) -> None:
    # A constant (zero-uncertainty) input must not break the sampler for any
    # PDF (rng.triangular rejects a zero-width support, so it is guarded).
    qs = [u.Quantity(5.0, 0.0, dist), u.Quantity(0.0, 1.0)]
    mc = u.monte_carlo(lambda a, b: a + b, qs, trials=10_000, seed=3)
    assert mc.value == pytest.approx(5.0, abs=0.05)
    assert mc.standard_uncertainty == pytest.approx(1.0, rel=0.05)


def test_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        u.Quantity(0.0, -1.0)
    with pytest.raises(ValueError, match="distribution"):
        u.Quantity(0.0, 1.0, "weird")
    with pytest.raises(ValueError, match="dof must be positive"):
        u.Quantity(0.0, 1.0, dof=0.0)
    with pytest.raises(ValueError, match="at least one"):
        u.combine_uncertainty(lambda: 0.0, [])
    with pytest.raises(ValueError, match="coverage"):
        u.coverage_factor(1.5)
    with pytest.raises(ValueError, match="shape"):
        u.combine_uncertainty(_add4, [u.Quantity(0, 1)] * 2, correlation=np.eye(3))
    with pytest.raises(ValueError, match="trials"):
        u.monte_carlo(_add4, [u.Quantity(0, 1)], trials=0)
    with pytest.raises(ValueError, match="coverage"):
        u.monte_carlo(_add4, [u.Quantity(0, 1)], coverage=2.0)
    with pytest.raises(ValueError, match="at least one"):
        u.monte_carlo(_add4, [])


def test_result_fields_and_plot() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    qs = [u.Quantity(3.0, 0.1, name="a"), u.Quantity(4.0, 0.2, name="b")]
    result = u.combine_uncertainty(lambda a, b: a * b, qs)
    assert result.names == ("a", "b")
    assert result.contributions.shape == (2,)
    ax = result.plot()
    assert isinstance(ax, plt.Axes)
    plt.close("all")
