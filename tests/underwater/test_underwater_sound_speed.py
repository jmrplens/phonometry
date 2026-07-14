#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for the speed of sound in sea water (UNESCO / Del Grosso / Mackenzie).

Oracles: the canonical Mackenzie check value 1550.744 m/s (published, absolute),
mutual agreement of the three independent equations within their common domain,
and the Leroy & Parthiot standard-ocean pressure.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

from phonometry.underwater.sound_speed import (
    SoundSpeedProfile,
    depth_to_pressure,
    sea_water_sound_speed,
    sound_speed_profile,
)


def test_mackenzie_canonical_check_value() -> None:
    # Mackenzie (1981) canonical check: c(25 C, 35 ppt, 1000 m) = 1550.744 m/s.
    c = sea_water_sound_speed(25.0, 35.0, 1000.0, model="mackenzie")
    assert c == pytest.approx(1550.744, abs=1e-3)


def test_depth_to_pressure_leroy_parthiot() -> None:
    # 1000 m at 45 deg -> ~10.106 MPa (standard ocean); ~1 MPa per 100 m.
    assert depth_to_pressure(1000.0, 45.0) == pytest.approx(10.1064, abs=1e-3)
    assert depth_to_pressure(0.0) == pytest.approx(0.0, abs=1e-9)


def test_three_models_agree_in_common_domain() -> None:
    # UNESCO, Del Grosso and Mackenzie must agree within ~1 m/s at a mid-ocean
    # point inside all three domains (10 C, 35 ppt, 1000 m).
    kw = dict(latitude=45.0)
    c_u = sea_water_sound_speed(10.0, 35.0, 1000.0, model="unesco", **kw)
    c_d = sea_water_sound_speed(10.0, 35.0, 1000.0, model="del_grosso", **kw)
    c_m = sea_water_sound_speed(10.0, 35.0, 1000.0, model="mackenzie", **kw)
    assert c_u == pytest.approx(1506.52, abs=0.05)
    assert c_d == pytest.approx(1506.31, abs=0.05)
    assert c_m == pytest.approx(1506.26, abs=0.05)
    assert max(abs(c_u - c_d), abs(c_u - c_m), abs(c_d - c_m)) < 1.0


def test_surface_speed_increases_with_temperature() -> None:
    cold = sea_water_sound_speed(5.0, 35.0, 0.0, model="unesco")
    warm = sea_water_sound_speed(20.0, 35.0, 0.0, model="unesco")
    assert warm > cold


def test_unknown_model_rejected() -> None:
    with pytest.raises(ValueError, match="model"):
        sea_water_sound_speed(10.0, 35.0, 100.0, model="wilson")


def test_negative_depth_rejected() -> None:
    with pytest.raises(ValueError, match="depth"):
        sea_water_sound_speed(10.0, 35.0, -5.0)


def test_profile_gradient_and_shape() -> None:
    depths = np.linspace(0.0, 2000.0, 21)
    prof = sound_speed_profile(depths, temperatures=10.0, salinities=35.0, model="unesco")
    assert isinstance(prof, SoundSpeedProfile)
    assert prof.sound_speed.shape == depths.shape
    assert prof.gradient.shape == depths.shape
    # Isothermal/isohaline column: speed rises with depth (pressure), gradient > 0.
    assert np.all(np.diff(prof.sound_speed) > 0.0)
    assert np.all(prof.gradient > 0.0)


def test_profile_requires_increasing_depths() -> None:
    with pytest.raises(ValueError, match="increasing"):
        sound_speed_profile([0.0, 100.0, 50.0], 10.0, 35.0)


def test_profile_plot_smoke() -> None:
    depths = np.linspace(0.0, 1000.0, 11)
    prof = sound_speed_profile(depths, 12.0, 35.0)
    assert prof.plot() is not None


def test_unesco_published_canonical_check_value() -> None:
    # Fofonoff & Millard 1983 (UNESCO Tech. Pap. Mar. Sci. 44) canonical check:
    # SVEL(S = 40, T68 = 40 C, P = 10000 dbar) = 1731.995 m/s. The module uses
    # the Wong-Zhu ITS-90 refit, so convert T90 = T68/1.00024; the tolerance
    # covers the published refit residual (~0.01 m/s).
    from phonometry.underwater.sound_speed import _unesco

    assert float(_unesco(40.0 / 1.00024, 40.0, 1000.0)) == pytest.approx(
        1731.995, abs=0.02)
