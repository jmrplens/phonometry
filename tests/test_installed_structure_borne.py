#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for EN 12354-5:2009 installed structure-borne sound from equipment.

Anchored on the standard's closed-form chain: the coupling term (Formula 19b)
and its force- and velocity-source limits (Formulae 19c/19d), the installed
power level L_Ws,inst = L_Ws,c − D_C (Formula 18b), the per-path normalised SPL
(Formula 18a) and the energetic path sum (Formula 17).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import (
    InstalledSourceResult,
    coupling_term,
    coupling_term_force_source,
    coupling_term_velocity_source,
    installed_source_prediction,
    installed_structure_borne_power_level,
    structure_borne_pressure_level_path,
    total_structure_borne_pressure_level,
)

S0 = 10.0


# ---------------------------------------------------------------------------
# Coupling term (Formula 19b) and its limiting forms (19c/19d)
# ---------------------------------------------------------------------------
def test_coupling_term_hand_value() -> None:
    ys, yi = 1e-4 + 0j, 1e-5 + 0j
    expected = 10.0 * math.log10(abs(ys + yi) ** 2 / (abs(ys) * yi.real))
    assert coupling_term(ys, yi) == pytest.approx(expected)


def test_coupling_reduces_to_force_source_limit() -> None:
    """|Y_s| >> |Y_i|: Formula 19b -> 19c (10 lg(|Y_s|/Re Y_i))."""
    ys, yi = 1e-3 + 0j, 1e-7 + 0j
    assert coupling_term(ys, yi) == pytest.approx(
        float(coupling_term_force_source(ys, yi)), abs=1e-2
    )


def test_coupling_reduces_to_velocity_source_limit() -> None:
    """|Y_s| << |Y_i|: Formula 19b -> 19d (−10 lg(|Y_s| Re Z_i))."""
    ys, yi = 1e-8 + 0j, 1e-4 + 0j
    zi = 1.0 / yi
    assert coupling_term(ys, yi) == pytest.approx(
        float(coupling_term_velocity_source(ys, zi)), abs=1e-2
    )


def test_coupling_elastic_support_reduces_transmission() -> None:
    # Adding a soft elastic support (large transfer mobility) raises D_C.
    ys, yi = 1e-4 + 0j, 1e-5 + 0j
    rigid = float(coupling_term(ys, yi))
    isolated = float(coupling_term(ys, yi, transfer_mobility=1e-3 + 0j))
    assert isolated > rigid


# ---------------------------------------------------------------------------
# Installed power (Formula 18b)
# ---------------------------------------------------------------------------
def test_installed_power_level() -> None:
    lw = installed_structure_borne_power_level(80.0, 10.828)
    assert float(lw) == pytest.approx(69.172)


def test_installed_power_per_band() -> None:
    lwc = np.array([75.0, 78.0, 80.0])
    dc = np.array([8.0, 9.0, 10.0])
    assert np.allclose(
        installed_structure_borne_power_level(lwc, dc), lwc - dc
    )


# ---------------------------------------------------------------------------
# Path SPL (Formula 18a) and total (Formula 17)
# ---------------------------------------------------------------------------
def test_path_level_hand_value() -> None:
    lp = structure_borne_pressure_level_path(69.0, 5.0, 50.0, 12.0)
    expected = 69.0 - 5.0 - 50.0 - 10.0 * math.log10(12.0 / S0) - 10.0 * math.log10(S0 / 4.0)
    assert float(lp) == pytest.approx(expected)


def test_path_level_rejects_bad_area() -> None:
    with pytest.raises(ValueError, match="element_area"):
        structure_borne_pressure_level_path(69.0, 5.0, 50.0, 0.0)


def test_total_is_energetic_sum() -> None:
    paths = np.array([[40.0, 42.0], [44.0, 41.0], [38.0, 39.0]])
    expected = 10.0 * np.log10(np.sum(10.0 ** (0.1 * paths), axis=0))
    assert np.allclose(total_structure_borne_pressure_level(paths), expected)


# ---------------------------------------------------------------------------
# Full prediction / result
# ---------------------------------------------------------------------------
def test_prediction_bundle() -> None:
    bands = np.array([250.0, 500.0, 1000.0])
    lwc = np.array([78.0, 80.0, 77.0])
    dc = np.array([9.0, 10.0, 11.0])
    paths = [
        {"adjustment_term": 5.0,
         "flanking_reduction_index": np.array([50.0, 52.0, 55.0]),
         "element_area": 12.0},
        {"adjustment_term": 6.0,
         "flanking_reduction_index": np.array([52.0, 54.0, 57.0]),
         "element_area": 8.0},
    ]
    res = installed_source_prediction(lwc, dc, paths, frequencies=bands)
    assert isinstance(res, InstalledSourceResult)
    assert res.path_levels.shape == (2, 3)
    # total is the energetic combination of the two paths
    assert np.allclose(
        res.total_level, total_structure_borne_pressure_level(res.path_levels)
    )
    # installed power is L_Ws,c − D_C
    assert np.allclose(res.installed_power_level, lwc - dc)


def test_prediction_requires_paths() -> None:
    with pytest.raises(ValueError, match="paths"):
        installed_source_prediction(80.0, 10.0, [])


def test_prediction_missing_path_key() -> None:
    with pytest.raises(ValueError, match="missing required key"):
        installed_source_prediction(
            80.0, 10.0, [{"adjustment_term": 5.0, "element_area": 12.0}]
        )


def test_prediction_band_count_mismatch() -> None:
    with pytest.raises(ValueError, match="flanking_reduction_index"):
        installed_source_prediction(
            np.array([80.0, 82.0, 78.0]), np.array([9.0, 10.0, 11.0]),
            [{"adjustment_term": 5.0,
              "flanking_reduction_index": np.array([50.0, 52.0]),  # 2 vs 3 bands
              "element_area": 12.0}],
        )


def test_overall_level_numeric() -> None:
    res = installed_source_prediction(
        np.array([80.0, 82.0]), np.array([10.0, 10.0]),
        [{"adjustment_term": 0.0, "flanking_reduction_index": np.array([0.0, 0.0]),
          "element_area": 10.0}],
    )
    expected = 10.0 * math.log10(np.sum(10.0 ** (0.1 * res.total_level)))
    assert res.overall_level == pytest.approx(expected)


def test_total_level_1d_paths_only() -> None:
    # a 1-D (paths-only) array reduces to a scalar-like total
    total = total_structure_borne_pressure_level(np.array([40.0, 44.0, 38.0]))
    expected = 10.0 * math.log10(np.sum(10.0 ** (0.1 * np.array([40.0, 44.0, 38.0]))))
    assert float(total) == pytest.approx(expected)


def test_coupling_elastic_support_hand_value() -> None:
    ys, yi, yk = 1e-4 + 0j, 1e-5 + 0j, 5e-4 + 0j
    expected = 10.0 * math.log10(abs(ys + yi + yk) ** 2 / (abs(ys) * yi.real))
    assert coupling_term(ys, yi, transfer_mobility=yk) == pytest.approx(expected)


def test_plot_returns_axes() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    bands = np.array([250.0, 500.0, 1000.0])
    paths = [
        {"adjustment_term": 5.0,
         "flanking_reduction_index": np.array([50.0, 52.0, 55.0]),
         "element_area": 12.0},
    ]
    res = installed_source_prediction(
        np.array([78.0, 80.0, 77.0]), np.array([9.0, 10.0, 11.0]),
        paths, frequencies=bands,
    )
    assert res.plot() is not None
