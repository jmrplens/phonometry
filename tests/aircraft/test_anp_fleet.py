#  Copyright (c) 2026. Jose M. Requena-Plens
"""EASA ANP fleet loader and its bridge to the ECAC Doc 29 chain.

The primary check is a clean-room round-trip: the loader must recover the ANP
database's own published NPD values exactly when interpolated at a tabulated
(power, distance) node. This validates the parser and the log-linear/power
interpolation, which are the main risk in wiring the real fleet data in.
"""

from __future__ import annotations

import csv
from importlib.resources import files

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from phonometry.aircraft import (  # noqa: E402
    AnpAircraft,
    AnpNpdCurves,
    AnpProfile,
    load_anp_database,
)

_FT_M = 0.3048
_KT_MS = 0.514444
#: Representative aircraft with both NPD data and a fixed-point profile: a heavy
#: jet (wing), a narrowbody (fuselage) and a propeller aircraft.
_REPRESENTATIVE = ("747100", "727200", "PA31")
_DB = load_anp_database()


def _npd_oracle() -> list[dict[str, str]]:
    """Independent parse of the bundled NPD CSV (the published-value oracle)."""
    text = files("phonometry.aircraft.data.anp").joinpath("NPD_data.csv").read_text()
    return list(csv.DictReader(text.splitlines(), delimiter=";"))


def test_database_loads_full_fleet() -> None:
    ids = _DB.aircraft_ids
    assert len(ids) > 100  # full EASA ANP v2.3 (155 aircraft types)
    for rep in _REPRESENTATIVE:
        assert rep in ids
    assert "A320-211" in ids  # a modern narrowbody present in the full DB


def test_metadata_and_mounting_mapping() -> None:
    assert _DB.aircraft("747100").mounting == "wing"
    assert _DB.aircraft("727200").mounting == "fuselage"
    assert _DB.aircraft("PA31").mounting == "propeller"
    assert _DB.aircraft("747100").num_engines == 4
    assert "747" in _DB.aircraft("747100").description


def test_npd_round_trip_is_exact() -> None:
    """Every tabulated (power, distance) node is recovered to machine precision."""
    npd_ids = {_DB.aircraft(a).npd_id: a for a in _REPRESENTATIVE}
    dist_cols = [c for c in _npd_oracle()[0] if c.startswith("L_") and c.endswith("ft")]
    checked = 0
    for row in _npd_oracle():
        if row["NPD_ID"] not in npd_ids or row["Noise Metric"] not in ("SEL", "LAmax"):
            continue
        curves = _DB.npd_curves(npd_ids[row["NPD_ID"]], row["Op Mode"], row["Noise Metric"])
        power = float(row["Power Setting"])
        for col in dist_cols:
            d_m = float(col[2:-2]) * _FT_M
            expected = float(row[col])
            got = float(curves.level(power, d_m)[0])
            assert got == pytest.approx(expected, abs=1e-9), (row["NPD_ID"], col)
            checked += 1
    assert checked > 100  # all three aircraft, both metrics, both operations


def test_npd_log_midpoint_interpolation() -> None:
    """Between two nodes the level is log-linear in distance (Doc 29 Eq. 4-4)."""
    curves = _DB.npd_curves("747100", "departure", "SEL")
    d0, d1 = curves.distances[0], curves.distances[1]
    mid = float(curves.level(curves.powers[0], np.sqrt(d0 * d1))[0])
    assert mid == pytest.approx(0.5 * (curves.levels[0, 0] + curves.levels[0, 1]), abs=1e-9)


def test_modern_aircraft_has_npd_but_no_fixed_point_profile() -> None:
    """A320-211 ships only procedural steps: NPD loads, the profile guard fires."""
    curves = _DB.npd_curves("A320-211", "departure", "SEL")
    assert curves.levels.shape[1] == 10
    with pytest.raises(KeyError, match="procedural-step"):
        _DB.profile("A320-211", "departure")


def test_profile_units_and_ground_roll_mask() -> None:
    dep = _DB.profile("747100", "departure")
    assert isinstance(dep, AnpProfile)
    assert dep.path.shape[1] == 5
    # First departure point of 747100: distance 0 ft, altitude 0 ft, TAS 35 kt.
    assert dep.path[0, 0] == pytest.approx(0.0)
    assert dep.path[0, 2] == pytest.approx(0.0)
    assert dep.path[0, 4] == pytest.approx(35.0 * _KT_MS)
    # Only the initial zero-altitude segment is takeoff ground roll.
    assert dep.ground_roll[0] and not dep.ground_roll[1:].any()
    assert not dep.landing_roll.any()
    arr = _DB.profile("747100", "arrival")
    # Landing rollout: the trailing zero-altitude segments, no takeoff roll.
    assert arr.landing_roll[-1] and not arr.ground_roll.any()


@pytest.mark.parametrize("aircraft_id", _REPRESENTATIVE)
@pytest.mark.parametrize("operation", ["departure", "arrival"])
def test_event_level_finite(aircraft_id: str, operation: str) -> None:
    fr = _DB.event_level(aircraft_id, [500.0, 600.0, 0.0], operation, metric="exposure")
    assert np.isfinite(fr.level)
    # The aircraft-object accessor matches the database method.
    assert _DB.aircraft(aircraft_id).event_level(
        [500.0, 600.0, 0.0], operation, metric="maximum").level == pytest.approx(
        _DB.event_level(aircraft_id, [500.0, 600.0, 0.0], operation,
                        metric="maximum").level)


def test_noise_contour_smoke() -> None:
    x = np.linspace(-2000.0, 8000.0, 30)
    y = np.linspace(-3000.0, 3000.0, 25)
    contour = _DB.noise_contour("747100", "departure", x=x, y=y, metric="exposure")
    assert contour.level.shape == (y.size, x.size)
    assert np.isfinite(contour.level).all()
    # Loudest near the track (y = 0), quieter far to the side.
    near = contour.level[np.argmin(np.abs(y)), np.argmin(np.abs(x - 4000.0))]
    far = contour.level[0, np.argmin(np.abs(x - 4000.0))]
    assert near > far


def test_external_directory_load(tmp_path: object) -> None:
    """The loader reads a user-supplied CSV export directory (archive naming)."""
    import pathlib

    root = pathlib.Path(str(tmp_path))
    src = files("phonometry.aircraft.data.anp")
    for name in ("Aircraft.csv", "NPD_data.csv",
                 "Default_fixed_point_profiles.csv"):
        (root / f"ANP2.3_{name}").write_text(src.joinpath(name).read_text())
    db = load_anp_database(root)
    assert db.npd_curves("727200", "arrival", "SEL").levels.shape[1] == 10


def test_error_paths() -> None:
    with pytest.raises(KeyError):
        _DB.aircraft("NOPE")
    with pytest.raises(ValueError, match="metric"):
        _DB.npd_curves("747100", "departure", "EPNL")
    with pytest.raises(ValueError, match="operation"):
        _DB.npd_curves("747100", "sideways", "SEL")
    with pytest.raises(KeyError):
        _DB.profile("PA31", "departure", stage_length=9)


def test_plot_smoke_en_es() -> None:
    npd = _DB.npd_curves("747100", "departure", "SEL")
    assert isinstance(npd, AnpNpdCurves)
    ax = npd.plot()
    assert "747100" in ax.get_title()
    npd.plot(language="es")
    prof = _DB.profile("747100", "departure")
    ax2 = prof.plot(language="es")
    assert ax2.get_xlabel().startswith("Distancia")
    with pytest.raises(ValueError, match="Unknown language"):
        npd.plot(language="xx")
    plt.close("all")


def test_aircraft_object_type() -> None:
    assert isinstance(_DB.aircraft("PA31"), AnpAircraft)
