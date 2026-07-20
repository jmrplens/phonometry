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
_EMBEDDED = ("747100", "727200", "PA31")


def _npd_oracle() -> list[dict[str, str]]:
    """Independent parse of the bundled NPD CSV (the published-value oracle)."""
    text = files("phonometry.aircraft.data.anp").joinpath("NPD_data.csv").read_text()
    return list(csv.DictReader(text.splitlines(), delimiter=";"))


def _npd_id_of(aircraft_id: str) -> str:
    return load_anp_database().aircraft(aircraft_id).npd_id


def test_database_contains_curated_subset() -> None:
    db = load_anp_database()
    assert db.aircraft_ids == sorted(_EMBEDDED)


def test_metadata_and_mounting_mapping() -> None:
    db = load_anp_database()
    assert db.aircraft("747100").mounting == "wing"
    assert db.aircraft("727200").mounting == "fuselage"
    assert db.aircraft("PA31").mounting == "propeller"
    assert db.aircraft("747100").num_engines == 4
    assert "747" in db.aircraft("747100").description


def test_npd_round_trip_is_exact() -> None:
    """Every tabulated (power, distance) node is recovered to machine precision."""
    db = load_anp_database()
    npd_to_acft = {_npd_id_of(a): a for a in _EMBEDDED}
    dist_cols = [c for c in _npd_oracle()[0] if c.startswith("L_") and c.endswith("ft")]
    checked = 0
    for row in _npd_oracle():
        acft = npd_to_acft[row["NPD_ID"]]
        curves = db.npd_curves(acft, row["Op Mode"], row["Noise Metric"])
        power = float(row["Power Setting"])
        for col in dist_cols:
            d_m = float(col[2:-2]) * _FT_M
            expected = float(row[col])
            got = float(curves.level(power, d_m)[0])
            assert got == pytest.approx(expected, abs=1e-9), (acft, row["Op Mode"], col)
            checked += 1
    assert checked > 100  # all three aircraft, both metrics, both operations


def test_npd_log_midpoint_interpolation() -> None:
    """Between two nodes the level is log-linear in distance (Doc 29 Eq. 4-4)."""
    curves = load_anp_database().npd_curves("747100", "departure", "SEL")
    d0, d1 = curves.distances[0], curves.distances[1]
    mid = float(curves.level(curves.powers[0], np.sqrt(d0 * d1))[0])
    assert mid == pytest.approx(0.5 * (curves.levels[0, 0] + curves.levels[0, 1]), abs=1e-9)


def test_profile_units_and_ground_roll_mask() -> None:
    db = load_anp_database()
    dep = db.profile("747100", "departure")
    assert isinstance(dep, AnpProfile)
    assert dep.path.shape[1] == 5
    # First departure point of 747100: distance 0 ft, altitude 0 ft, TAS 35 kt.
    assert dep.path[0, 0] == pytest.approx(0.0)
    assert dep.path[0, 2] == pytest.approx(0.0)
    assert dep.path[0, 4] == pytest.approx(35.0 * _KT_MS)
    # Only the initial zero-altitude segment is takeoff ground roll.
    assert dep.ground_roll[0] and not dep.ground_roll[1:].any()
    assert not dep.landing_roll.any()
    arr = db.profile("747100", "arrival")
    # Landing rollout: the trailing zero-altitude segments, no takeoff roll.
    assert arr.landing_roll[-1] and not arr.ground_roll.any()


@pytest.mark.parametrize("aircraft_id", _EMBEDDED)
@pytest.mark.parametrize("operation", ["departure", "arrival"])
def test_event_level_finite(aircraft_id: str, operation: str) -> None:
    db = load_anp_database()
    fr = db.event_level(aircraft_id, [500.0, 600.0, 0.0], operation, metric="exposure")
    assert np.isfinite(fr.level)
    assert db.aircraft(aircraft_id).event_level(
        [500.0, 600.0, 0.0], operation, metric="maximum").level == pytest.approx(
        db.event_level(aircraft_id, [500.0, 600.0, 0.0], operation,
                       metric="maximum").level)


def test_noise_contour_smoke() -> None:
    db = load_anp_database()
    x = np.linspace(-2000.0, 8000.0, 30)
    y = np.linspace(-3000.0, 3000.0, 25)
    contour = db.noise_contour("747100", "departure", x=x, y=y, metric="exposure")
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
    db = load_anp_database()
    with pytest.raises(KeyError):
        db.aircraft("NOPE")
    with pytest.raises(ValueError, match="metric"):
        db.npd_curves("747100", "departure", "EPNL")
    with pytest.raises(ValueError, match="operation"):
        db.npd_curves("747100", "sideways", "SEL")
    with pytest.raises(KeyError, match="procedural-step"):
        # A320-211 exists in the full DB but not in the curated subset; use a
        # curated aircraft and an absent stage length to hit the profile guard.
        db.profile("PA31", "departure", stage_length=9)


def test_plot_smoke_en_es() -> None:
    db = load_anp_database()
    npd = db.npd_curves("747100", "departure", "SEL")
    assert isinstance(npd, AnpNpdCurves)
    ax = npd.plot()
    assert "747100" in ax.get_title()
    npd.plot(language="es")
    prof = db.profile("747100", "departure")
    ax2 = prof.plot(language="es")
    assert ax2.get_xlabel().startswith("Distancia")
    with pytest.raises(ValueError, match="Unknown language"):
        npd.plot(language="xx")
    plt.close("all")


def test_aircraft_object_type() -> None:
    assert isinstance(load_anp_database().aircraft("PA31"), AnpAircraft)
