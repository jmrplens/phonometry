#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Free-field qualification: ISO 26101:2017 and ISO 3745:2012/Amd.1:2017 Annex A.

Normative anchors, read on the printed page:
- ISO 26101:2017 Formula (1), PDF page 10, folio 4: the monitor correction
  L_pi = L'_pi - L_p,ref,i + L_p,ref,0.
- ISO 26101:2017 Formula (2), PDF page 12, folio 6: L_p(r_i) = b - 20 lg(r_i/r0).
- ISO 26101:2017 Formulae (3) and (4), PDF page 13, folio 7.
- ISO 26101:2017 Table A.1, PDF page 15, folio 9, and ISO 3745:2012/Amd.1:2017
  Table A.1, PDF page 6, folio 2 (the same cells).
- ISO 26101:2017 A.4.3, PDF page 17, folio 11: lambda/10 below 1 kHz, 25 mm above.
- ISO 26101:2017 B.3.2 and Table B.1, PDF pages 18-19, folios 12-13.
- ISO 3745:2012/Amd.1:2017 A.2.3 and A.2.4, PDF page 7, folio 3; A.3.3, PDF
  page 8, folio 4; A.4.3, PDF page 9, folio 5.

No source prints a worked example, so the oracles are closed forms: an exact
inverse-square field qualifies at every distance, and a field with one known
reflection deviates by the known amount.
"""

from __future__ import annotations

import math
import warnings

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import emission

#: The eleven frequencies of A.2.3 over 100 Hz to 10 000 Hz.
_GRID = (
    100.0,
    125.0,
    250.0,
    500.0,
    1000.0,
    2000.0,
    4000.0,
    5000.0,
    6300.0,
    8000.0,
    10000.0,
)
#: Six traverse directions that stay 20 deg to 80 deg from the vertical.
_DIRECTIONS = (
    (1.0, 1.0, 1.0),
    (1.0, 1.0, 0.3),
    (0.0, 1.0, 0.5),
    (1.0, 0.0, 0.2),
    (-1.0, 0.5, 0.6),
    (0.3, -1.0, 0.8),
)
#: What each of those paths is selected towards (A.3.3 a) to e)).
_TARGETS: tuple[tuple[str, ...], ...] = (
    ("trihedral corner",),
    ("dihedral corner",),
    ("boundary centre",),
    ("closest boundary",),
    ("unique features",),
    (),
)
_L1M = 90.0


def _free_field_traverses(
    distances: np.ndarray,
    freqs: tuple[float, ...] = _GRID,
    *,
    directions: tuple[tuple[float, float, float], ...] = _DIRECTIONS,
    background: float | None = 20.0,
) -> list[emission.MicrophoneTraverse]:
    """Traverses in an exact inverse-square field of 90 dB at 1 m."""
    level = _L1M - 20.0 * np.log10(distances)
    grid = np.repeat(level[:, np.newaxis], len(freqs), axis=1)
    return [
        emission.MicrophoneTraverse.along(
            u,
            distances,
            grid,
            background_levels_db=None
            if background is None
            else np.full(len(freqs), background),
            name=f"path {i + 1}",
            targets=_TARGETS[i % len(_TARGETS)],  # type: ignore[arg-type]
        )
        for i, u in enumerate(directions)
    ]


def _directionality(room: str = "hemi-anechoic") -> emission.SourceDirectionalityResult:
    count = 32 if room == "hemi-anechoic" else 64
    return emission.verify_source_directionality(
        np.full((count, len(_GRID)), 80.0), frequencies_hz=_GRID, room=room
    )


def _qualified(
    traverses: list[emission.MicrophoneTraverse], **kwargs: object
) -> emission.FreeFieldCheck:
    fit = emission.inverse_square_law_deviations(
        traverses, frequencies_hz=_GRID, room="hemi-anechoic"
    )
    options: dict[str, object] = {
        "bandwidth": "discrete-frequency",
        "source_directionality": _directionality(),
        "reflecting_plane_absorption_coefficient": 0.02,
        "reflecting_plane_margin_m": 1.0,
        "paths_in_working_area": True,
    }
    options.update(kwargs)
    return emission.check_free_field(fit, **options)  # type: ignore[arg-type]


# --- the tables ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("frequency", "anechoic", "hemi"),
    [
        (100.0, 1.5, 2.5),
        (630.0, 1.5, 2.5),
        (800.0, 1.0, 2.0),
        (5000.0, 1.0, 2.0),
        (6300.0, 1.5, 3.0),
        (10000.0, 1.5, 3.0),
    ],
)
def test_table_a1_cells(frequency: float, anechoic: float, hemi: float) -> None:
    """Table A.1 of ISO 26101 and of the amended ISO 3745 print the same cells."""
    assert (
        emission.inverse_square_law_tolerance_db([frequency], room="anechoic")[0]
        == anechoic
    )
    assert (
        emission.inverse_square_law_tolerance_db([frequency], room="hemi-anechoic")[0]
        == hemi
    )


def test_a_tone_is_read_in_the_band_that_contains_it() -> None:
    """A tone at the exact one-third octave centre 794 Hz is held to the 800 Hz row."""
    assert emission.inverse_square_law_tolerance_db([794.3], room="anechoic")[0] == 1.0
    assert emission.inverse_square_law_tolerance_db([630.96], room="anechoic")[0] == 1.5


@pytest.mark.parametrize(
    ("frequency", "anechoic", "hemi"),
    [
        (630.0, 1.5, 2.0),
        (800.0, 2.0, 2.5),
        (5000.0, 2.0, 2.5),
        (6300.0, 2.5, 3.0),
        (10000.0, 2.5, 3.0),
        (12500.0, 5.0, 5.0),
    ],
)
def test_table_b1_cells(frequency: float, anechoic: float, hemi: float) -> None:
    """ISO 26101 Table B.1: the allowable deviations in directionality."""
    assert (
        emission.directionality_tolerance_db([frequency], room="anechoic")[0]
        == anechoic
    )
    assert (
        emission.directionality_tolerance_db([frequency], room="hemi-anechoic")[0]
        == hemi
    )


def test_unknown_room_is_refused() -> None:
    with pytest.raises(ValueError, match="'room'"):
        emission.inverse_square_law_tolerance_db([1000.0], room="reverberant")  # type: ignore[arg-type]


def test_qualification_frequencies_of_a23() -> None:
    """One-third octaves below 125 Hz and above 4 kHz, octaves between."""
    np.testing.assert_array_equal(emission.qualification_frequencies_hz(), _GRID)
    extended = emission.qualification_frequencies_hz(50.0, 20000.0)
    np.testing.assert_array_equal(
        extended,
        [50.0, 63.0, 80.0, *_GRID, 12500.0, 16000.0, 20000.0],
    )


def test_qualification_frequencies_refuse_an_empty_range() -> None:
    with pytest.raises(ValueError, match="'high_hz'"):
        emission.qualification_frequencies_hz(1000.0, 500.0)


# --- Formulae (1) to (4): the closed forms --------------------------------------


def test_an_exact_inverse_square_field_qualifies_at_every_distance() -> None:
    d = np.arange(0.30, 3.0001, 0.05)
    fit = emission.inverse_square_law_deviations(
        _free_field_traverses(d), frequencies_hz=_GRID, room="anechoic"
    )
    np.testing.assert_allclose(fit.traverse_radius_m, d[-1], rtol=0, atol=1e-12)
    assert fit.maximum_qualified_radius_m == pytest.approx(d[-1], abs=1e-12)
    np.testing.assert_allclose(fit.source_strength_db, _L1M, rtol=0, atol=1e-12)
    np.testing.assert_allclose(fit.initial_source_strength_db, _L1M, rtol=0, atol=1e-12)
    for deviation in fit.deviations_db:
        np.testing.assert_allclose(deviation, 0.0, rtol=0, atol=1e-12)
    np.testing.assert_allclose(fit.largest_deviation_db, 0.0, rtol=0, atol=1e-12)


def test_formula_3_is_the_mean_of_level_plus_20_lg_r() -> None:
    """NOTE 1: b starts at (sum 20 lg(r_i/r0) + sum L_pi) / N."""
    d = np.array([0.5, 1.0, 1.5, 2.0])
    levels = np.array([85.0, 80.5, 76.0, 73.5])
    traverse = emission.MicrophoneTraverse.along((1, 0, 0), d, levels)
    fit = emission.inverse_square_law_deviations(
        [traverse], frequencies_hz=[1000.0], room="anechoic"
    )
    expected = (np.sum(20.0 * np.log10(d)) + np.sum(levels)) / d.size
    assert fit.initial_source_strength_db[0, 0] == pytest.approx(expected, abs=1e-12)


def _incoherent_reflection(
    rho2: float, wall_m: float, d: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Direct field plus an incoherent image in a wall ``wall_m`` ahead."""
    image = 2.0 * wall_m - d
    excess = 10.0 * np.log10(1.0 + rho2 * (d / image) ** 2)
    return _L1M - 20.0 * np.log10(d) + excess, excess


def test_a_known_reflection_deviates_by_the_known_amount() -> None:
    """Incoherent image source: D(r) = 10 lg(1 + rho^2 r^2/(2h - r)^2), monotone.

    The qualified distance is where D has risen 2t above its first value,
    solved for r in closed form; b centres the deviations over that run.
    """
    rho2, wall, tol = 1.0, 2.5, 1.0  # anechoic, 1 kHz row of Table A.1
    d = np.arange(0.50, 2.4001, 0.05)
    levels, excess = _incoherent_reflection(rho2, wall, d)
    traverse = emission.MicrophoneTraverse.along((1, 0, 0), d, levels)
    fit = emission.inverse_square_law_deviations(
        [traverse], frequencies_hz=[1000.0], room="anechoic"
    )
    q1 = d[0] / (2.0 * wall - d[0])
    q = math.sqrt(((1.0 + rho2 * q1**2) * 10.0 ** (2.0 * tol / 10.0) - 1.0) / rho2)
    r_limit = 2.0 * wall * q / (1.0 + q)
    expected_radius = float(d[d <= r_limit][-1])
    assert expected_radius < d[-1]  # the reflection, not the traverse, ends the run
    assert fit.traverse_radius_m[0, 0] == pytest.approx(expected_radius, abs=1e-12)
    inside = d <= expected_radius
    b = _L1M + (excess[inside].max() + excess[inside].min()) / 2.0
    assert fit.source_strength_db[0, 0] == pytest.approx(b, abs=1e-9)
    np.testing.assert_allclose(
        fit.deviations_db[0][:, 0], excess - (b - _L1M), rtol=0, atol=1e-9
    )
    assert fit.largest_deviation_db[0] <= tol + 1e-12
    assert np.ptp(fit.deviations_db[0][inside, 0]) == pytest.approx(
        np.ptp(excess[inside]), abs=1e-12
    )


def test_a_coherent_reflection_ripples_by_the_known_amount() -> None:
    """A tone and its image: D = 10 lg(1 + a^2 + 2 a cos(k(r' - r))), a = rho r/r'.

    The ripple grows with the distance, since a does, and crosses twice the
    Table A.1 limit of the band (2 x 2,5 dB at 500 Hz, hemi-anechoic) before
    the traverse ends. The qualified distance is the last point before the
    running spread of D leaves 2t, walked here point by point on D alone, and
    b is L(1 m) plus the midpoint of D over that run.
    """
    rho, wall, frequency = 0.5, 2.5, 500.0
    k = 2.0 * math.pi * frequency / 343.0
    d = np.arange(0.40, 2.4001, 0.02)
    image = 2.0 * wall - d
    a = rho * d / image
    excess = 10.0 * np.log10(1.0 + a**2 + 2.0 * a * np.cos(k * (image - d)))
    traverse = emission.MicrophoneTraverse.along(
        (0, 0, 1), d, _L1M - 20.0 * np.log10(d) + excess
    )
    fit = emission.inverse_square_law_deviations(
        [traverse], frequencies_hz=[frequency], room="hemi-anechoic"
    )
    t = float(
        emission.inverse_square_law_tolerance_db([frequency], room="hemi-anechoic")[0]
    )
    assert t == 2.5
    last = 0
    high = low = float(excess[0])
    for i, value in enumerate(excess):
        high, low = max(high, float(value)), min(low, float(value))
        if high - low > 2.0 * t:
            break
        last = i
    assert last < d.size - 1  # the reflection, not the traverse, ends the run
    assert fit.traverse_radius_m[0, 0] == pytest.approx(d[last], abs=1e-12)
    run = excess[: last + 1]
    b = _L1M + (run.max() + run.min()) / 2.0
    assert fit.source_strength_db[0, 0] == pytest.approx(b, abs=1e-9)
    assert np.ptp(excess[: last + 2]) > 2.0 * t


def test_formula_1_removes_the_source_drift() -> None:
    d = np.arange(0.3, 2.0, 0.1)
    drift = np.linspace(0.0, 0.8, d.size)
    monitor = 70.0 + drift
    traverse = emission.MicrophoneTraverse.along(
        (1, 0, 0),
        d,
        _L1M - 20.0 * np.log10(d) + drift,
        monitor_levels_db=monitor,
    )
    fit = emission.inverse_square_law_deviations(
        [traverse], frequencies_hz=[1000.0], room="anechoic"
    )
    np.testing.assert_allclose(fit.deviations_db[0], 0.0, rtol=0, atol=1e-12)
    assert fit.source_stability_db[0][0] == pytest.approx(0.8)


def test_a_point_not_measured_at_one_frequency_is_left_out_there() -> None:
    d = np.arange(0.3, 2.0, 0.1)
    levels = np.repeat((_L1M - 20.0 * np.log10(d))[:, None], 2, axis=1)
    levels[-1, 1] = np.nan
    fit = emission.inverse_square_law_deviations(
        [emission.MicrophoneTraverse.along((1, 0, 0), d, levels)],
        frequencies_hz=[1000.0, 2000.0],
        room="anechoic",
    )
    assert fit.traverse_radius_m[0, 0] == pytest.approx(d[-1])
    assert fit.traverse_radius_m[0, 1] == pytest.approx(d[-2])


# --- the mathematical origin -----------------------------------------------------


def _offset_field(origin: np.ndarray) -> list[emission.MicrophoneTraverse]:
    """Traverses laid out from (0, 0, 0) in a field centred at ``origin``."""
    d = np.arange(0.30, 2.5001, 0.02)
    out = []
    for u in _DIRECTIONS:
        unit = np.asarray(u) / np.linalg.norm(u)
        points = d[:, None] * unit[None, :]
        r = np.linalg.norm(points - origin[None, :], axis=1)
        out.append(
            emission.MicrophoneTraverse(
                positions_m=points,
                levels_db=(_L1M - 20.0 * np.log10(r))[:, None],
            )
        )
    return out


def test_the_origin_is_found_inside_the_source_volume() -> None:
    """The acoustic centre sits 16 cm from the frame's origin, inside the source.

    From the frame's origin the near points deviate by up to 8,7 (u.o)/r dB and
    the run breaks early; searched inside the box, the origin moves to where
    every point qualifies.
    """
    true_origin = np.array([0.08, -0.06, 0.12])
    traverses = _offset_field(true_origin)
    fixed = emission.inverse_square_law_deviations(
        traverses, frequencies_hz=[1000.0], room="anechoic"
    )
    fitted = emission.inverse_square_law_deviations(
        traverses,
        frequencies_hz=[1000.0],
        room="anechoic",
        source_box_m=((-0.1, -0.1, 0.0), (0.1, 0.1, 0.2)),
    )
    assert fitted.origin_fitted
    assert fitted.maximum_qualified_radius_m > fixed.maximum_qualified_radius_m
    assert np.all(fitted.origin_m >= [-0.1, -0.1, 0.0])
    assert np.all(fitted.origin_m <= [0.1, 0.1, 0.2])
    np.testing.assert_allclose(fitted.origin_m, true_origin, rtol=0, atol=2e-3)
    assert float(fitted.largest_deviation_db[0]) < 0.05


@pytest.mark.parametrize("seed", range(6))
def test_an_exact_field_is_found_at_its_centre_wherever_it_sits(seed: int) -> None:
    """Exact fields centred anywhere in the box: the origin lands on the centre.

    Every run reaches its last point, which the measurement bounds; the room
    ends none, so the flattest curves decide, and they are flat only from
    the point the field diverges from.
    """
    rng = np.random.default_rng(seed)
    true_origin = rng.uniform([-0.1, -0.1, 0.0], [0.1, 0.1, 0.2])
    fitted = emission.inverse_square_law_deviations(
        _offset_field(true_origin),
        frequencies_hz=[1000.0],
        room="anechoic",
        source_box_m=((-0.1, -0.1, 0.0), (0.1, 0.1, 0.2)),
    )
    np.testing.assert_allclose(fitted.origin_m, true_origin, rtol=0, atol=3e-3)
    assert float(fitted.largest_deviation_db[0]) < 0.05


def test_a_field_that_qualifies_everywhere_returns_its_centre() -> None:
    """Traverses laid out from the centre of an exact field inside the box.

    Every point qualifies from every origin near the centre, so the radius is
    the distance to the nearest end of a traverse, which is longest from the
    point the traverses start at; there the curves are also flat, and the
    search returns it.
    """
    true_origin = np.array([0.02, -0.01, 0.03])
    d = np.arange(0.30, 2.5001, 0.02)
    traverses = []
    for u in _DIRECTIONS:
        unit = np.asarray(u) / np.linalg.norm(u)
        traverses.append(
            emission.MicrophoneTraverse.along(
                unit, d, (_L1M - 20.0 * np.log10(d))[:, None], start_m=true_origin
            )
        )
    fitted = emission.inverse_square_law_deviations(
        traverses,
        frequencies_hz=[1000.0],
        room="anechoic",
        source_box_m=((-0.05, -0.05, 0.0), (0.05, 0.05, 0.08)),
    )
    np.testing.assert_allclose(fitted.origin_m, true_origin, rtol=0, atol=1.5e-3)
    assert fitted.maximum_qualified_radius_m == pytest.approx(2.5, abs=2e-3)
    assert float(fitted.largest_deviation_db[0]) < 0.05


def test_ties_go_to_the_origin_that_fills_the_least_of_the_band() -> None:
    """Two origins qualify to the same radius: the flatter curves win.

    Along one traverse on the x axis, every origin on the y axis sees the
    last point at the same distance to within a fraction of a millimetre; the
    curves are flat only from the distance the field is centred at, 3 cm off
    the axis (on either side, which the axis cannot tell apart).
    """
    true_origin = np.array([0.0, 0.03, 0.0])
    d = np.arange(0.5, 2.0001, 0.05)
    points = d[:, None] * np.array([1.0, 0.0, 0.0])[None, :]
    r = np.linalg.norm(points - true_origin[None, :], axis=1)
    traverse = emission.MicrophoneTraverse(
        positions_m=points, levels_db=(_L1M - 20.0 * np.log10(r))[:, None]
    )
    fitted = emission.inverse_square_law_deviations(
        [traverse],
        frequencies_hz=[1000.0],
        room="anechoic",
        source_box_m=((0.0, -0.05, 0.0), (0.0, 0.05, 0.0)),
    )
    assert abs(fitted.origin_m[1]) == pytest.approx(0.03, abs=1.5e-3)
    assert float(fitted.largest_deviation_db[0]) < 0.05


def test_a_short_traverse_does_not_pull_the_origin_off_the_centre() -> None:
    """The measurement ends one traverse at 1 m; the room ends another beyond it.

    Traverses along +x, -x, +y, -y and +z in an exact field centred on the
    box. The +x one stops at 1,0 m, so its run reaches its last point from
    every origin, at a distance that moves as far as the origin does. The +y
    one carries an incoherent image in a wall 2,5 m ahead, and the room ends
    it near 2,2 m. Counted from each origin, the short traverse would
    reward the origin that backs away from its last point; counted, as the
    search counts it, from the centre of the box, it is the same for every
    origin, the flattest curves decide and the origin stays at the centre.
    """
    traverses = []
    for u, end in (
        ((1.0, 0.0, 0.0), 1.0),
        ((-1.0, 0.0, 0.0), 2.4),
        ((0.0, 1.0, 0.0), 2.4),
        ((0.0, -1.0, 0.0), 2.4),
        ((0.0, 0.0, 1.0), 2.4),
    ):
        d = np.arange(0.30, end + 1e-9, 0.02)
        levels = _L1M - 20.0 * np.log10(d)
        if u[1] > 0.0:
            levels = _incoherent_reflection(1.0, 2.5, d)[0]
        traverses.append(emission.MicrophoneTraverse.along(u, d, levels[:, None]))
    fitted = emission.inverse_square_law_deviations(
        traverses,
        frequencies_hz=[1000.0],
        room="anechoic",
        source_box_m=((-0.1, -0.1, -0.1), (0.1, 0.1, 0.1)),
    )
    assert fitted.traverse_radius_m[2, 0] < 2.3  # the room ends the +y run
    np.testing.assert_allclose(fitted.origin_m, 0.0, rtol=0, atol=5e-3)
    assert fitted.maximum_qualified_radius_m == pytest.approx(1.0, abs=5e-3)
    assert float(fitted.largest_deviation_db[0]) < 0.2


def test_the_origin_never_leaves_the_box() -> None:
    """The acoustic centre lies outside the source: the origin stops at the box."""
    traverses = _offset_field(np.array([0.3, 0.0, 0.1]))
    fitted = emission.inverse_square_law_deviations(
        traverses,
        frequencies_hz=[1000.0],
        room="anechoic",
        source_box_m=((-0.05, -0.05, 0.0), (0.05, 0.05, 0.2)),
    )
    assert np.all(fitted.origin_m >= np.array([-0.05, -0.05, 0.0]) - 1e-12)
    assert np.all(fitted.origin_m <= np.array([0.05, 0.05, 0.2]) + 1e-12)


def test_a_traverse_starting_beyond_the_radius_is_centred_on_its_own_run() -> None:
    """One path breaks at 0,7 m; another starts at 0,9 m, beyond that radius.

    The second path has no point within the radius every path meets, so its
    source strength is the midpoint over its own qualified run and its
    deviations stay defined.
    """
    near = np.arange(0.3, 1.5001, 0.05)
    step = np.where(near > 0.72, 3.0, 0.0)  # a 3 dB jump beyond 0,7 m
    broken = emission.MicrophoneTraverse.along(
        (1, 0, 0), near, _L1M - 20.0 * np.log10(near) + step
    )
    far = np.arange(0.9, 2.0001, 0.05)
    late = emission.MicrophoneTraverse.along(
        (0, 1, 0), far, _L1M + 1.0 - 20.0 * np.log10(far)
    )
    fit = emission.inverse_square_law_deviations(
        [broken, late], frequencies_hz=[1000.0], room="anechoic"
    )
    assert fit.maximum_qualified_radius_m == pytest.approx(0.70)
    assert fit.source_strength_db[1, 0] == pytest.approx(_L1M + 1.0, abs=1e-9)
    np.testing.assert_allclose(fit.deviations_db[1][:, 0], 0.0, rtol=0, atol=1e-9)


def test_a_flat_box_holds_that_coordinate() -> None:
    traverses = _offset_field(np.array([0.0, 0.0, 0.05]))
    fitted = emission.inverse_square_law_deviations(
        traverses,
        frequencies_hz=[1000.0],
        room="anechoic",
        source_box_m=((-0.1, -0.1, 0.0), (0.1, 0.1, 0.0)),
    )
    assert fitted.origin_m[2] == 0.0


def test_origin_and_box_together_are_refused() -> None:
    traverses = _free_field_traverses(np.arange(0.3, 1.0, 0.1), (1000.0,))
    with pytest.raises(ValueError, match="'source_box_m'"):
        emission.inverse_square_law_deviations(
            traverses,
            frequencies_hz=[1000.0],
            room="anechoic",
            origin_m=(0, 0, 0),
            source_box_m=((0, 0, 0), (1, 1, 1)),
        )


def test_a_point_on_the_origin_is_refused() -> None:
    traverse = emission.MicrophoneTraverse.along((1, 0, 0), [0.0, 0.5], [90.0, 84.0])
    with pytest.raises(ValueError, match="mathematical origin"):
        emission.inverse_square_law_deviations(
            [traverse], frequencies_hz=[1000.0], room="anechoic"
        )


def test_a_traverse_needs_two_points_in_three_coordinates() -> None:
    flat, levels = np.zeros((3, 2)), np.zeros(3)
    with pytest.raises(ValueError, match="'positions_m'"):
        emission.MicrophoneTraverse(positions_m=flat, levels_db=levels)


def test_level_columns_must_match_the_frequencies() -> None:
    traverse = emission.MicrophoneTraverse.along((1, 0, 0), [0.5, 1.0], [90.0, 84.0])
    with pytest.raises(ValueError, match="level columns"):
        emission.inverse_square_law_deviations(
            [traverse], frequencies_hz=[500.0, 1000.0], room="anechoic"
        )


def test_two_frequencies_in_one_band_are_refused() -> None:
    traverse = emission.MicrophoneTraverse.along(
        (1, 0, 0), [0.5, 1.0], [[90.0, 90.0], [84.0, 84.0]]
    )
    with pytest.raises(ValueError, match="same one-third octave"):
        emission.inverse_square_law_deviations(
            [traverse], frequencies_hz=[1000.0, 1010.0], room="anechoic"
        )


# --- Annex B: the test source directionality -----------------------------------


def test_directionality_positions_of_b32() -> None:
    hemi = emission.directionality_positions("hemi-anechoic")
    full = emission.directionality_positions("anechoic")
    assert hemi.shape == (32, 3)
    assert full.shape == (64, 3)
    np.testing.assert_allclose(np.linalg.norm(full, axis=1), 1.5)
    polar = np.degrees(np.arccos(full[:, 2] / 1.5))
    np.testing.assert_allclose(
        sorted(set(np.round(polar, 9))), [20, 40, 60, 80, 100, 120, 140, 160]
    )
    assert np.all(hemi[:, 2] > 0.0)


def test_a_uniform_source_is_suitable() -> None:
    assert _directionality().passes
    assert _directionality("anechoic").passes


def test_a_lobe_beyond_table_b1_is_not_suitable() -> None:
    levels = np.full((32, 1), 80.0)
    levels[5, 0] = 82.7  # 2,62 dB above the mean at 1 kHz; the limit is 2,5 dB
    result = emission.verify_source_directionality(
        levels, frequencies_hz=[1000.0], room="hemi-anechoic"
    )
    mean = levels.mean()
    assert result.maximum_positive_deviation_db[0] == pytest.approx(82.7 - mean)
    assert result.maximum_negative_deviation_db[0] == pytest.approx(80.0 - mean)
    assert not result.passes


def test_directionality_needs_the_positions_of_b32() -> None:
    hemisphere = np.full((32, 1), 80.0)
    with pytest.raises(ValueError, match="'levels_db'"):
        emission.verify_source_directionality(
            hemisphere, frequencies_hz=[1000.0], room="anechoic"
        )


def test_directionality_verdict_has_no_truth_value() -> None:
    result = _directionality()
    with pytest.raises(TypeError, match="passes"):
        bool(result)


# --- the verdict of Annex A -----------------------------------------------------


_SPACING = np.arange(0.30, 3.0001, 0.02)


def test_a_free_field_is_in_full_conformity() -> None:
    check = _qualified(_free_field_traverses(_SPACING))
    assert check.passes
    assert check.full_frequency_range
    assert check.not_judged == ()
    assert check.maximum_qualified_radius_m == pytest.approx(_SPACING[-1])
    assert check.conforming_range_hz == (100.0, 10000.0)
    assert check.path_angles_met is True
    assert check.discrete_frequency


def test_a_missing_background_leaves_the_room_unjudged() -> None:
    check = _qualified(_free_field_traverses(_SPACING, background=None))
    assert "background" in check.not_judged
    assert check.background_met is None
    assert not check.passes


def test_a_missing_directionality_leaves_the_room_unjudged() -> None:
    check = _qualified(_free_field_traverses(_SPACING), source_directionality=None)
    assert "source directionality" in check.not_judged
    assert not check.passes


def test_a_hemi_anechoic_room_needs_its_reflecting_plane_judged() -> None:
    check = _qualified(
        _free_field_traverses(_SPACING),
        reflecting_plane_absorption_coefficient=None,
        reflecting_plane_margin_m=None,
    )
    assert "reflecting plane" in check.not_judged
    assert not check.passes


def test_a_reflecting_plane_that_absorbs_too_much_fails() -> None:
    check = _qualified(
        _free_field_traverses(_SPACING), reflecting_plane_absorption_coefficient=0.08
    )
    assert check.reflecting_plane_met is False
    assert not check.passes


def test_a_reflecting_plane_that_ends_too_close_fails() -> None:
    """A.2.5: at least a quarter wavelength at 100 Hz (0,86 m) and 0,75 m."""
    check = _qualified(_free_field_traverses(_SPACING), reflecting_plane_margin_m=0.8)
    assert check.reflecting_plane_met is False


@pytest.mark.parametrize(("margin", "met"), [(0.70, False), (0.80, True)])
def test_the_plane_extends_at_least_0_75_m(*, margin: float, met: bool) -> None:
    """A.2.5 with 125 Hz lowest: the quarter wavelength is 0,686 m, so 0,75 m binds."""
    freqs = _GRID[1:]
    fit = emission.inverse_square_law_deviations(
        _free_field_traverses(_SPACING, freqs),
        frequencies_hz=freqs,
        room="hemi-anechoic",
    )
    check = emission.check_free_field(
        fit,
        bandwidth="broadband",
        reflecting_plane_absorption_coefficient=0.02,
        reflecting_plane_margin_m=margin,
    )
    assert check.reflecting_plane_met is met


def test_four_traverses_are_too_few() -> None:
    check = _qualified(_free_field_traverses(_SPACING, directions=_DIRECTIONS[:4]))
    assert not check.traverse_count_met
    assert not check.passes
    assert check.conforming_range_hz is None


def test_nine_traverses_are_too_many() -> None:
    """A.3.3: at least five, but not more than eight."""
    directions = (*_DIRECTIONS, (1.0, -1.0, 0.5), (-1.0, -1.0, 0.7), (-1.0, 0.0, 0.4))
    check = _qualified(_free_field_traverses(_SPACING, directions=directions))
    assert not check.traverse_count_met
    assert not check.passes
    eight = _qualified(_free_field_traverses(_SPACING, directions=directions[:8]))
    assert eight.traverse_count_met


def test_the_path_targets_of_a33_are_read_from_the_traverses() -> None:
    """a) to e): every target named; none named leaves them unjudged."""
    check = _qualified(_free_field_traverses(_SPACING))
    assert check.path_targets_met is True
    unnamed = [
        emission.MicrophoneTraverse(
            positions_m=t.positions_m,
            levels_db=t.levels_db,
            background_levels_db=t.background_levels_db,
        )
        for t in _free_field_traverses(_SPACING)
    ]
    unjudged = _qualified(unnamed)
    assert unjudged.path_targets_met is None
    assert "path targets" in unjudged.not_judged
    assert not unjudged.passes
    no_door = [
        emission.MicrophoneTraverse(
            positions_m=t.positions_m,
            levels_db=t.levels_db,
            background_levels_db=t.background_levels_db,
            targets=tuple(x for x in t.targets if x != "unique features"),
        )
        for t in _free_field_traverses(_SPACING)
    ]
    missing = _qualified(no_door)
    assert missing.path_targets_met is False
    assert not missing.passes
    assert missing.conforming_range_hz is None


def test_an_unknown_path_target_is_refused() -> None:
    points, levels = np.array([[0.5, 0, 0], [1.0, 0, 0]]), np.array([84.0, 78.0])
    with pytest.raises(ValueError, match="'targets'"):
        emission.MicrophoneTraverse(
            positions_m=points,
            levels_db=levels,
            targets=("window",),  # type: ignore[arg-type]
        )


def test_the_working_area_is_a_declaration() -> None:
    """A.3.3: the paths lie in the working area; the positions cannot tell."""
    unjudged = _qualified(_free_field_traverses(_SPACING), paths_in_working_area=None)
    assert unjudged.working_area_met is None
    assert "working area" in unjudged.not_judged
    assert not unjudged.passes
    outside = _qualified(_free_field_traverses(_SPACING), paths_in_working_area=False)
    assert outside.working_area_met is False
    assert not outside.passes
    assert outside.conforming_range_hz is None


def test_a_working_area_declaration_must_be_a_bool() -> None:
    """A string such as "no" is truthy, and would be read as a declaration."""
    traverses = _free_field_traverses(_SPACING)
    with pytest.raises(ValueError, match="'paths_in_working_area' must be True"):
        _qualified(traverses, paths_in_working_area="no")
    assert _qualified(traverses, paths_in_working_area=np.True_).working_area_met


@pytest.mark.parametrize("absorption", [-0.01, 1.01, math.nan])
def test_an_absorption_coefficient_outside_0_to_1_is_refused(absorption: float) -> None:
    traverses = _free_field_traverses(_SPACING)
    with pytest.raises(ValueError, match="'reflecting_plane_absorption_coefficient'"):
        _qualified(traverses, reflecting_plane_absorption_coefficient=absorption)


def test_a_fully_absorbing_plane_is_judged_not_refused() -> None:
    check = _qualified(
        _free_field_traverses(_SPACING), reflecting_plane_absorption_coefficient=1.0
    )
    assert check.reflecting_plane_met is False


@pytest.mark.parametrize("margin", [math.inf, math.nan])
def test_a_plane_margin_that_is_not_finite_is_refused(margin: float) -> None:
    traverses = _free_field_traverses(_SPACING)
    with pytest.raises(ValueError, match="'reflecting_plane_margin_m' must be finite"):
        _qualified(traverses, reflecting_plane_margin_m=margin)


@pytest.mark.parametrize("level", [math.inf, -math.inf])
def test_an_infinite_level_is_refused(level: float) -> None:
    """Only nan marks a point not measured; an infinite level is an error."""
    d = np.arange(0.3, 2.2001, 0.1)
    levels = _L1M - 20.0 * np.log10(d)
    levels[5] = level
    with pytest.raises(ValueError, match="'levels_db' must be finite"):
        emission.MicrophoneTraverse.along((1, 0, 0), d, levels)


@pytest.mark.parametrize(
    "direction", [(0.0, 0.0, 0.0), (1.0, math.nan, 0.0), (math.inf, 0.0, 0.0)]
)
def test_a_direction_that_is_zero_or_not_finite_is_refused(
    direction: tuple[float, float, float],
) -> None:
    """No line runs along it, so no point of the traverse can be placed."""
    d = np.arange(0.3, 2.2001, 0.1)
    levels = _L1M - 20.0 * np.log10(d)
    with pytest.raises(ValueError, match="'direction' must be a finite, non-zero"):
        emission.MicrophoneTraverse.along(direction, d, levels)


def test_a_monitor_reading_is_needed_wherever_a_level_is() -> None:
    """Formula (1) corrects every measured point to the reading of point 0."""
    d = np.arange(0.3, 2.2001, 0.1)
    levels = np.repeat((_L1M - 20.0 * np.log10(d))[:, None], 2, axis=1)
    monitor = np.full(levels.shape, 70.0)
    monitor[5, 0] = np.nan
    with pytest.raises(ValueError, match="'monitor_levels_db' must be finite"):
        emission.MicrophoneTraverse.along(
            (1, 0, 0), d, levels, monitor_levels_db=monitor
        )
    first = np.full(levels.shape, 70.0)
    first[0, 1] = np.nan
    unmeasured = levels.copy()
    unmeasured[0, 1] = np.nan
    with pytest.raises(ValueError, match="in its first row"):
        emission.MicrophoneTraverse.along(
            (1, 0, 0), d, unmeasured, monitor_levels_db=first
        )
    skipped = levels.copy()
    skipped[5, 0] = np.nan
    traverse = emission.MicrophoneTraverse.along(
        (1, 0, 0), d, skipped, monitor_levels_db=monitor
    )
    assert np.isnan(traverse.monitor_levels_db[5, 0])


def test_a_background_is_needed_wherever_a_level_is() -> None:
    d = np.arange(0.3, 2.2001, 0.1)
    levels = _L1M - 20.0 * np.log10(d)
    background = np.full(d.size, 20.0)
    background[3] = np.nan
    with pytest.raises(ValueError, match="'background_levels_db' must be finite"):
        emission.MicrophoneTraverse.along(
            (1, 0, 0), d, levels, background_levels_db=background
        )


@pytest.mark.parametrize(
    "lookup",
    [emission.inverse_square_law_tolerance_db, emission.directionality_tolerance_db],
)
def test_the_tolerance_lookups_take_one_frequency_axis(lookup: object) -> None:
    with pytest.raises(ValueError, match="1-D array of frequencies"):
        lookup([[1000.0, 2000.0]], room="anechoic")  # type: ignore[operator]


def test_a_background_closer_than_6_db_fails() -> None:
    check = _qualified(_free_field_traverses(_SPACING, background=75.0))
    assert check.background_met is not None
    assert not np.all(check.background_met)
    assert not check.passes


def test_100_mm_spacing_meets_iso_3745_but_not_iso_26101_above_343_hz() -> None:
    """The amended A.4.3 allows 100 mm; A.2.4 cites ISO 26101 A.4.3.

    A tenth of a wavelength is 100 mm at 343 Hz, so from 500 Hz up the 100 mm
    traverse is too coarse for ISO 26101, and above 1 kHz it asks for 25 mm.
    """
    d = np.arange(0.30, 3.0001, 0.10)
    check = _qualified(_free_field_traverses(d))
    freqs = check.frequencies_hz
    assert np.all(check.spacing_met[freqs > 250.0])
    assert np.all(check.iso26101_spacing_met[freqs < 343.0])
    assert not np.any(check.iso26101_spacing_met[freqs > 343.0])
    assert not check.passes


def test_points_that_are_not_equally_spaced_fail_a43() -> None:
    """Gaps alternating 5 mm and 20 mm are within every largest spacing."""
    gaps = np.tile([0.005, 0.020], 110)
    d = 0.30 + np.concatenate([[0.0], np.cumsum(gaps)])
    check = _qualified(_free_field_traverses(d))
    assert np.all(check.spacing_met)
    assert np.all(check.iso26101_spacing_met)
    assert not np.any(check.equal_spacing_met)
    assert not check.passes


def test_points_added_near_a_peak_keep_the_grid() -> None:
    """A.4.3, last paragraph: measurements added near a peak deviation."""
    d = np.sort(np.concatenate([_SPACING, [1.005, 1.01, 1.015, 2.207]]))
    check = _qualified(_free_field_traverses(d))
    assert np.all(check.equal_spacing_met)
    assert check.passes


@pytest.mark.parametrize(("shift_mm", "met"), [(1.9, True), (2.1, False)])
def test_a_grid_point_may_sit_a_tenth_of_the_step_off(
    *, shift_mm: float, met: bool
) -> None:
    """The library's reading of "equally spaced": a tenth of the step.

    One point of the 20 mm grid moved 1,9 mm stays on the grid, and moved
    2,1 mm it falls off; every largest spacing of A.4.3 holds either way.
    """
    d = _SPACING.copy()
    d[40] += shift_mm / 1000.0
    check = _qualified(_free_field_traverses(d))
    np.testing.assert_array_equal(check.equal_spacing_met, met)
    assert np.all(check.spacing_met)
    assert np.all(check.iso26101_spacing_met)
    assert check.passes is met


def test_the_edge_band_is_held_to_the_stricter_spacing() -> None:
    """At 250 Hz a tenth of a wavelength is 137 mm, and 100 mm applies."""
    d = np.arange(0.30, 3.0001, 0.12)
    check = _qualified(_free_field_traverses(d))
    at_250 = check.frequencies_hz == 250.0
    assert not check.spacing_met[at_250][0]
    assert check.spacing_met[check.frequencies_hz == 125.0][0]


def _counted(points: tuple[int, ...]) -> emission.FreeFieldCheck:
    """Traverses of ``points`` at 20 mm, judged at 1 kHz.

    The longest starts at 0,06 m and every one ends where it does, so that
    the radius, set by the traverse that ends first, takes in every point.
    """
    longest = max(points)
    traverses = []
    for count, u in zip(points, _DIRECTIONS * 2, strict=False):
        d = 0.06 + 0.02 * np.arange(longest - count, longest)
        traverses.append(
            emission.MicrophoneTraverse.along(
                u, d, (_L1M - 20.0 * np.log10(d))[:, None]
            )
        )
    fit = emission.inverse_square_law_deviations(
        traverses, frequencies_hz=[1000.0], room="anechoic"
    )
    return emission.check_free_field(fit, bandwidth="broadband")


@pytest.mark.parametrize(
    ("points", "met"),
    [
        ((10, 10, 10, 10, 10), True),  # 50 in all, 10 on each
        ((9, 9, 9, 9, 9), False),  # 45 in all
        ((10, 10, 10, 10, 10, 9), False),  # 59 in all, but one traverse of 9
        ((13, 13, 12, 12), True),  # 50 in all over four
        ((13, 12, 12, 12), False),  # at least 10 on each, but 49 in all
    ],
)
def test_a43_asks_for_10_points_a_traverse_and_50_in_all(
    *, points: tuple[int, ...], met: bool
) -> None:
    check = _counted(points)
    assert bool(check.points_met[0]) is met
    assert check.spacing_met[0]
    assert check.iso26101_spacing_met[0]
    assert check.equal_spacing_met[0]
    assert check.length_met[0]


def test_too_short_a_traverse_fails_5143() -> None:
    """ISO 26101 5.1.4.3: at least a quarter wavelength at 100 Hz, 0,86 m."""
    d = np.arange(0.30, 0.9, 0.02)
    check = _qualified(_free_field_traverses(d))
    assert not np.any(check.length_met)
    assert not check.passes


def test_a_traverse_starting_too_far_out_fails_5143() -> None:
    """ISO 26101 5.1.4.3: start at most a quarter wavelength (0,86 m at 100 Hz) out."""
    d = np.arange(1.0, 3.0001, 0.02)
    check = _qualified(_free_field_traverses(d))
    assert not np.any(check.length_met)
    assert not check.passes
    assert check.conforming_range_hz is None


def test_a_path_too_close_to_the_floor_fails_a33() -> None:
    directions = (*_DIRECTIONS[:5], (1.0, 0.0, 0.05))
    check = _qualified(_free_field_traverses(_SPACING, directions=directions))
    assert check.path_angles_met is False
    assert not check.passes


@pytest.mark.parametrize(
    ("direction", "met"),
    [
        ((0.0, 0.0, 1.0), False),  # straight up, 0 deg from the vertical
        ((math.tan(math.radians(18.0)), 0.0, 1.0), False),  # 18 deg
        ((math.tan(math.radians(82.0)), 0.0, 1.0), False),  # 82 deg
        ((math.tan(math.radians(79.0)), 0.0, 1.0), True),  # 79 deg
    ],
)
def test_the_path_angles_of_a33_both_ways(
    *, direction: tuple[float, float, float], met: bool
) -> None:
    """In a hemi-anechoic room, within the 20 deg to 80 deg of B.3.2."""
    directions = (*_DIRECTIONS[:5], direction)
    check = _qualified(_free_field_traverses(_SPACING, directions=directions))
    assert check.path_angles_met is met


def test_a_path_is_judged_by_its_direction_not_by_its_first_point() -> None:
    """A.3.3 on a path 24 deg from the vertical seen from an offset origin.

    From an origin 5 cm aside, the first point of the path lies 9 deg from
    the vertical, outside the 20 deg to 80 deg of B.3.2, but the path itself
    runs at 24 deg and is within them.
    """
    directions = (*_DIRECTIONS[:5], (1.5, 1.0, 4.0))
    fit = emission.inverse_square_law_deviations(
        _free_field_traverses(_SPACING, directions=directions),
        frequencies_hz=_GRID,
        room="hemi-anechoic",
        origin_m=(0.05, 0.034, 0.0),
    )
    first = fit.positions_m[5][0] - fit.origin_m
    assert math.degrees(math.acos(first[2] / np.linalg.norm(first))) < 20.0
    check = emission.check_free_field(
        fit,
        bandwidth="discrete-frequency",
        source_directionality=_directionality(),
        reflecting_plane_absorption_coefficient=0.02,
        reflecting_plane_margin_m=1.0,
        paths_in_working_area=True,
    )
    assert check.path_angles_met is True


def test_an_anechoic_room_sets_no_path_angle() -> None:
    fit = emission.inverse_square_law_deviations(
        _free_field_traverses(_SPACING), frequencies_hz=_GRID, room="anechoic"
    )
    check = emission.check_free_field(
        fit,
        bandwidth="broadband",
        source_directionality=_directionality("anechoic"),
        paths_in_working_area=True,
    )
    assert check.path_angles_met is None
    assert check.reflecting_plane_met is None
    assert check.passes
    assert not check.discrete_frequency


def test_a_measurement_radius_beyond_the_qualified_one_fails() -> None:
    check = _qualified(_free_field_traverses(_SPACING), measurement_radius_m=3.5)
    assert not check.passes
    ok = _qualified(_free_field_traverses(_SPACING), measurement_radius_m=2.0)
    assert ok.passes


def test_a_range_short_of_100_hz_to_10_khz_is_not_in_full_conformity() -> None:
    """A.2.3: everything met over 100 Hz to 250 Hz is "in conformity", no more."""
    freqs = _GRID[:3]
    fit = emission.inverse_square_law_deviations(
        _free_field_traverses(_SPACING, freqs), frequencies_hz=freqs, room="anechoic"
    )
    check = emission.check_free_field(
        fit,
        bandwidth="broadband",
        source_directionality=emission.verify_source_directionality(
            np.full((64, 3), 80.0), frequencies_hz=freqs, room="anechoic"
        ),
        paths_in_working_area=True,
    )
    assert np.all(check.band_met)
    assert check.not_judged == ()
    assert not check.full_frequency_range
    assert not check.passes
    assert check.conforming_range_hz == (100.0, 250.0)


def test_a_failing_low_band_leaves_a_reduced_range() -> None:
    """A reflection at 100 Hz: the room conforms from 125 Hz up, not in full."""
    traverses = _free_field_traverses(_SPACING)
    spoiled = []
    for traverse in traverses:
        levels = traverse.levels_db.copy()
        levels[:, 0] += 4.0 * np.sin(2 * np.pi * _SPACING / 1.0)
        spoiled.append(
            emission.MicrophoneTraverse(
                positions_m=traverse.positions_m,
                levels_db=levels,
                background_levels_db=traverse.background_levels_db,
                targets=traverse.targets,
            )
        )
    check = _qualified(spoiled)
    assert not check.passes
    assert check.conforming_range_hz == (125.0, 10000.0)
    assert check.conforming_radius_m == pytest.approx(_SPACING[-1])


def test_two_sources_share_the_range() -> None:
    low = _GRID[:4]
    high = _GRID[4:]
    fits = [
        emission.inverse_square_law_deviations(
            _free_field_traverses(_SPACING, band),
            frequencies_hz=band,
            room="hemi-anechoic",
        )
        for band in (low, high)
    ]
    directionality = [
        emission.verify_source_directionality(
            np.full((32, len(band)), 80.0), frequencies_hz=band, room="hemi-anechoic"
        )
        for band in (low, high)
    ]
    check = emission.check_free_field(
        fits,
        bandwidth="discrete-frequency",
        source_directionality=directionality,
        reflecting_plane_absorption_coefficient=0.02,
        reflecting_plane_margin_m=1.0,
        paths_in_working_area=True,
    )
    assert check.passes
    np.testing.assert_array_equal(check.frequencies_hz, _GRID)


def test_one_band_measured_by_two_sources_is_refused() -> None:
    fit = emission.inverse_square_law_deviations(
        _free_field_traverses(_SPACING, (1000.0,)),
        frequencies_hz=[1000.0],
        room="anechoic",
    )
    with pytest.raises(ValueError, match="two test sources"):
        emission.check_free_field([fit, fit], bandwidth="broadband")


def test_directionality_must_align_with_the_sources() -> None:
    fit = emission.inverse_square_law_deviations(
        _free_field_traverses(_SPACING, (1000.0,)),
        frequencies_hz=[1000.0],
        room="anechoic",
    )
    with pytest.raises(ValueError, match="'source_directionality'"):
        emission.check_free_field(
            fit, bandwidth="broadband", source_directionality=[None, None]
        )


def test_an_unknown_bandwidth_is_refused() -> None:
    fit = emission.inverse_square_law_deviations(
        _free_field_traverses(_SPACING, (1000.0,)),
        frequencies_hz=[1000.0],
        room="anechoic",
    )
    with pytest.raises(ValueError, match="'bandwidth'"):
        emission.check_free_field(fit, bandwidth="tonal")  # type: ignore[arg-type]


def test_the_check_has_no_truth_value() -> None:
    check = _qualified(_free_field_traverses(_SPACING))
    with pytest.raises(TypeError, match="passes"):
        bool(check)


# --- the anechoic method consumes the verdict -----------------------------------


def test_sound_power_anechoic_reads_the_qualification() -> None:
    check = _qualified(_free_field_traverses(_SPACING))
    levels = np.full((20, 3), 80.0)
    freqs = np.array([500.0, 1000.0, 2000.0])
    with pytest.raises(ValueError, match="hemi-anechoic"):
        emission.sound_power_anechoic(
            levels, "sphere", radius=1.0, frequencies=freqs, room_qualification=check
        )
    with pytest.warns(emission.SoundPowerWarning, match="qualified radius"):
        emission.sound_power_anechoic(
            levels,
            "hemisphere",
            radius=3.5,
            frequencies=freqs,
            room_qualification=check,
        )
    one_band = np.full((20, 1), 80.0)
    above = np.array([12500.0])
    with pytest.warns(emission.SoundPowerWarning, match="frequency range"):
        emission.sound_power_anechoic(
            one_band,
            "hemisphere",
            radius=2.0,
            frequencies=above,
            room_qualification=check,
        )
    unjudged = _qualified(_free_field_traverses(_SPACING, background=None))
    with pytest.warns(emission.SoundPowerWarning, match="not qualified"):
        emission.sound_power_anechoic(
            levels,
            "hemisphere",
            radius=2.0,
            frequencies=freqs,
            room_qualification=unjudged,
        )


def test_a_measurement_inside_the_qualification_raises_no_warning() -> None:
    """Within the radius and the range, the qualification says nothing."""
    check = _qualified(_free_field_traverses(_SPACING))
    levels = np.full((20, 3), 80.0)
    freqs = np.array([500.0, 1000.0, 2000.0])
    with warnings.catch_warnings():
        warnings.simplefilter("error", emission.SoundPowerWarning)
        result = emission.sound_power_anechoic(
            levels,
            "hemisphere",
            radius=2.0,
            frequencies=freqs,
            room_qualification=check,
        )
    assert np.all(np.isfinite(result.sound_power_level))


# --- plots -----------------------------------------------------------------------


def test_the_deviation_plot_draws_one_curve_per_traverse() -> None:
    fit = emission.inverse_square_law_deviations(
        _free_field_traverses(_SPACING), frequencies_hz=_GRID, room="hemi-anechoic"
    )
    ax = fit.plot(frequency_hz=1000.0)
    labels = ax.get_legend_handles_labels()[1]
    assert sum(label.startswith("path") for label in labels) == len(_DIRECTIONS)
    assert "Table A.1 limit" in labels
    plt.close("all")
    with pytest.raises(ValueError, match="'frequency_hz'"):
        fit.plot(frequency_hz=1234.0)
    plt.close("all")


def test_the_deviation_plot_draws_the_deviations_below_a_band_for_the_legend() -> None:
    """Each curve is the traverse's deviations by distance; the legend has room.

    The curves fill the panel from end to end, so the axes run on above the
    highest curve and the upper limit, where the legend goes.
    """
    fit = emission.inverse_square_law_deviations(
        _free_field_traverses(_SPACING), frequencies_hz=_GRID, room="hemi-anechoic"
    )
    column = int(np.flatnonzero(np.isclose(fit.frequencies_hz, 1000.0))[0])
    ax = fit.plot(frequency_hz=1000.0)
    first = ax.get_lines()[0]
    order = np.argsort(fit.distances_m[0])
    np.testing.assert_allclose(first.get_xdata(), fit.distances_m[0][order])
    np.testing.assert_allclose(first.get_ydata(), fit.deviations_db[0][order, column])
    limit = float(fit.tolerance_db[column])
    highest = max(limit, max(float(np.nanmax(d[:, column])) for d in fit.deviations_db))
    bottom, top = ax.get_ylim()
    assert bottom < -limit
    assert top > highest + 0.5 * (highest + limit)
    vertical = [
        line for line in ax.get_lines() if np.ptp(np.asarray(line.get_xdata())) == 0
    ]
    assert float(vertical[0].get_xdata()[0]) == pytest.approx(
        float(fit.band_radius_m[column])
    )
    plt.close("all")


def test_the_check_plot_draws_one_bar_per_frequency() -> None:
    check = _qualified(_free_field_traverses(_SPACING), measurement_radius_m=2.0)
    ax = check.plot()
    assert len(ax.patches) == len(_GRID)
    assert "full conformity" in ax.get_title()
    plt.close("all")
    ax = check.plot(language="es")
    assert "conformidad plena" in ax.get_title()
    plt.close("all")


def _legend_colours(ax: plt.Axes) -> dict[str, str]:
    from matplotlib.colors import to_hex

    legend = ax.get_legend()
    return {
        text.get_text(): to_hex(handle.get_facecolor())
        for text, handle in zip(legend.get_texts(), legend.legend_handles, strict=True)
        if hasattr(handle, "get_facecolor") and text.get_text().endswith("met")
    }


@pytest.mark.parametrize("style", ["default", "dark_background"])
def test_the_check_legend_swatches_match_the_bars(style: str) -> None:
    """Every swatch in the colour of its bars, in either style, passing or not."""
    from matplotlib.colors import to_hex

    passing = _qualified(_free_field_traverses(_SPACING))
    failing = _qualified(_free_field_traverses(_SPACING), measurement_radius_m=3.5)
    with plt.style.context(style):
        ax = passing.plot()
        bars = {to_hex(p.get_facecolor()) for p in ax.patches}
        assert _legend_colours(ax) == {"Every requirement met": bars.pop()}
        plt.close("all")
        ax = failing.plot()
        bars = {to_hex(p.get_facecolor()) for p in ax.patches}
        assert _legend_colours(ax) == {"A requirement not met": bars.pop()}
    plt.close("all")


def test_a_judged_failure_titles_the_check_before_missing_data() -> None:
    """Four traverses fail A.3.3 whatever the missing directionality shows."""
    few = _qualified(
        _free_field_traverses(_SPACING, directions=_DIRECTIONS[:4]),
        source_directionality=None,
    )
    assert few.not_judged
    assert few.plot().get_title().endswith("not qualified")
    plt.close("all")
    assert few.plot(language="es").get_title().endswith("no cualificada")
    plt.close("all")
    pending = _qualified(_free_field_traverses(_SPACING), source_directionality=None)
    assert pending.plot().get_title().endswith("requirements not judged")
    plt.close("all")


def test_the_check_plot_marks_the_reduced_range() -> None:
    traverses = _free_field_traverses(_SPACING)
    spoiled = []
    for traverse in traverses:
        levels = traverse.levels_db.copy()
        levels[:, 0] += 4.0 * np.sin(2 * np.pi * _SPACING / 1.0)
        spoiled.append(
            emission.MicrophoneTraverse(
                positions_m=traverse.positions_m,
                levels_db=levels,
                background_levels_db=traverse.background_levels_db,
                targets=traverse.targets,
            )
        )
    check = _qualified(spoiled)
    ax = check.plot()
    assert ax.get_title().endswith("reduced range")
    labels = ax.get_legend_handles_labels()[1]
    assert "Reduced range, 125 Hz to 10 kHz" in labels
    assert "Radius over the reduced range" in labels
    radius = [
        line
        for line in ax.get_lines()
        if line.get_label() == "Radius over the reduced range"
    ]
    assert float(radius[0].get_ydata()[0]) == pytest.approx(check.conforming_radius_m)
    plt.close("all")
    ax = check.plot(language="es")
    assert "Intervalo reducido, de 125 Hz a 10 kHz" in ax.get_legend_handles_labels()[1]
    plt.close("all")


def test_unnamed_traverses_are_labelled_in_the_plot_language() -> None:
    d = np.arange(0.3, 2.0, 0.05)
    traverses = [
        emission.MicrophoneTraverse.along(u, d, (_L1M - 20.0 * np.log10(d))[:, None])
        for u in _DIRECTIONS[:5]
    ]
    fit = emission.inverse_square_law_deviations(
        traverses, frequencies_hz=[1000.0], room="anechoic"
    )
    assert fit.traverse_names == ("",) * 5
    labels = fit.plot().get_legend_handles_labels()[1]
    assert "Traverse 1" in labels
    plt.close("all")
    labels = fit.plot(language="es").get_legend_handles_labels()[1]
    assert "Recorrido 5" in labels
    assert not any(label.startswith("Traverse") for label in labels)
    plt.close("all")


def test_the_directionality_plot_draws_both_extremes() -> None:
    from matplotlib.patches import Rectangle

    ax = _directionality().plot()
    bars = [p for p in ax.patches if isinstance(p, Rectangle)]
    assert len(bars) == 2 * len(_GRID)
    plt.close("all")
