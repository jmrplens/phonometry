#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A simulation is one record, checked when it is built.

:class:`FDTDRun` and :class:`ElasticRun` hold every argument of a run and
refuse a bad one where the run is written, the grid's included (the time
step, the density, the sponge, the impedance edges, the obstacle, the
sources and the probes on the grid), so that a run which builds is one the
simulation function can step, here or on a node. Nothing the caller changes
afterwards reaches a checked run.
"""

from __future__ import annotations

import copy
import dataclasses
import pickle
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
import pytest

from phonometry.simulation import (
    FDTD2D,
    ElasticBoundaries,
    ElasticFDTD2D,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDBoundaries,
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    elastic_fdtd_simulation,
    fdtd_simulation,
)

if TYPE_CHECKING:
    from collections.abc import Callable

_PULSE = GaussianPulse(ix=4, iy=4, half_width_s=4e-5)

#: Which engine a test builds a run for.
Engine = Literal["acoustic", "elastic"]


def _acoustic(**changes: Any) -> FDTDRun:
    fields: dict[str, Any] = {
        "duration_s": 1e-4,
        "shape": (8, 8),
        "sources": [_PULSE],
        **changes,
    }
    return FDTDRun(c=343.0, dx=0.01, **fields)


def _elastic(**changes: Any) -> ElasticRun:
    source = ExplosionSource(ix=4, iy=4, waveform=_PULSE.value)
    fields: dict[str, Any] = {
        "duration_s": 1e-4,
        "shape": (8, 8),
        "rho": 2500.0,
        "sources": [source],
        **changes,
    }
    return ElasticRun(c_p=4000.0, c_s=2300.0, dx=0.01, **fields)


@pytest.mark.parametrize(
    ("build", "bad", "error", "match"),
    [
        (_acoustic, {"rho": -1.0}, ValueError, "rho must be strictly positive"),
        (
            _acoustic,
            {"boundaries": FDTDBoundaries(sides={"left": np.ones(3)})},
            ValueError,
            "impedance for side 'left'",
        ),
        (
            _acoustic,
            {"boundaries": FDTDBoundaries(sides="absorbing", absorbing_layer_cells=0)},
            ValueError,
            "absorbing_layer_cells must be >= 1",
        ),
        (
            _acoustic,
            {"boundaries": "absorbing"},
            TypeError,
            r"'boundaries' must be an FDTDBoundaries or None, got str\.",
        ),
        (
            _acoustic,
            {"boundaries": {"left": "absorbing"}},
            TypeError,
            r"'boundaries' must be an FDTDBoundaries or None, got dict\.",
        ),
        (
            _acoustic,
            {"boundaries": ElasticBoundaries(sides="absorbing")},
            TypeError,
            "'boundaries' must be an FDTDBoundaries or None, got ElasticBoundaries",
        ),
        (
            _acoustic,
            {"duration_s": 0.0},
            ValueError,
            "duration_s must be positive and finite",
        ),
        (
            _acoustic,
            {"duration_s": "1e-4"},
            TypeError,
            "'duration_s' must be one number, not a text",
        ),
        (_acoustic, {"sources": []}, ValueError, "at least one source is required"),
        (
            _acoustic,
            {"sources": [GaussianPulse(ix=40, iy=4, half_width_s=4e-5)]},
            ValueError,
            "source position lies outside the grid",
        ),
        (
            _acoustic,
            {"recording": FDTDRecording(probes=[(40, 40)])},
            ValueError,
            r"probe \(40, 40\) lies outside the grid",
        ),
        (
            _acoustic,
            {"recording": ElasticRecording()},
            TypeError,
            "'recording' must be an FDTDRecording or None",
        ),
        (_elastic, {"rho": -1.0}, ValueError, "rho must be strictly positive"),
        (
            _elastic,
            {"recording": ElasticRecording(probes=[(40, 40)])},
            ValueError,
            r"probe \(40, 40\) lies outside the grid",
        ),
        (
            _elastic,
            {
                "boundaries": ElasticBoundaries(
                    sides="absorbing", absorbing_layer_cells=0
                )
            },
            ValueError,
            "absorbing_layer_cells must be >= 1",
        ),
        (
            _elastic,
            {"boundaries": "free"},
            TypeError,
            "'boundaries' must be an ElasticBoundaries or None",
        ),
        (
            _elastic,
            {"boundaries": FDTDBoundaries(sides="absorbing")},
            TypeError,
            "'boundaries' must be an ElasticBoundaries or None, got FDTDBoundaries",
        ),
        (
            _elastic,
            {"duration_s": 1e-12},
            ValueError,
            "duration_s must cover at least one time step",
        ),
    ],
)
def test_a_run_refuses_a_bad_argument_when_it_is_built(
    build: Callable[..., FDTDRun | ElasticRun],
    bad: dict[str, object],
    error: type[Exception],
    match: str,
) -> None:
    with pytest.raises(error, match=match):
        build(**bad)


def test_a_changed_copy_of_a_run_is_checked_again() -> None:
    corner = GaussianPulse(ix=1, iy=1, half_width_s=4e-5)
    run = _acoustic(sources=[corner], recording=FDTDRecording(probes=[(6, 6)]))
    with pytest.raises(ValueError, match=r"probe \(6, 6\) lies outside the grid"):
        dataclasses.replace(run, shape=(4, 4))


def test_a_run_takes_every_field_by_name() -> None:
    # Swapping two of the leading numbers would still build a valid run, so
    # neither record takes one by position.
    with pytest.raises(TypeError, match="positional argument"):
        FDTDRun(343.0, 0.01, 0.02, sources=[_PULSE])  # type: ignore[misc]
    source = ExplosionSource(ix=4, iy=4, waveform=_PULSE.value)
    with pytest.raises(TypeError, match="positional argument"):
        ElasticRun(  # type: ignore[misc]
            4000.0, 2300.0, 0.01, 1e-4, rho=2500.0, shape=(8, 8), sources=[source]
        )
    run = _acoustic()
    assert (run.c, run.dx, run.duration_s, run.shape) == (343.0, 0.01, 1e-4, (8, 8))
    with pytest.raises(dataclasses.FrozenInstanceError):
        run.dx = 0.02  # type: ignore[misc]


def test_a_run_does_not_follow_what_its_caller_changes() -> None:
    c = np.full((8, 8), 343.0)
    sources = [_PULSE]
    edge = np.full(8, 413.0)
    boundaries: dict[str, Any] = {"left": "absorbing", "top": edge}
    run = FDTDRun(
        c=c,
        dx=0.01,
        duration_s=1e-4,
        sources=sources,
        boundaries=FDTDBoundaries(sides=boundaries, absorbing_layer_cells=2),
        recording=FDTDRecording(probes=[(5, 5)]),
    )
    before = fdtd_simulation(run)
    c[:] = 686.0
    edge[:] = -1.0
    sources.append(GaussianPulse(ix=40, iy=40, half_width_s=4e-5))
    boundaries["right"] = "absorbing"
    after = fdtd_simulation(run)
    assert np.array_equal(after.pressures, before.pressures)
    assert run.sources == (_PULSE,)
    assert run.boundaries is not None
    assert isinstance(run.boundaries.sides, MappingProxyType)
    assert set(run.boundaries.sides) == {"left", "top"}
    assert not run.c.flags.writeable

    sides: dict[str, Any] = {"top": "free", "bottom": "absorbing"}
    elastic = _elastic(
        boundaries=ElasticBoundaries(sides=sides, absorbing_layer_cells=2),
        recording=ElasticRecording(probes=[(5, 5)], probe_fields=("p", "vy")),
    )
    first = elastic_fdtd_simulation(elastic)
    sides["top"] = "absorbing"
    sides["left"] = "free"
    again = elastic_fdtd_simulation(elastic)
    rebuilt = elastic_fdtd_simulation(pickle.loads(pickle.dumps(elastic)))
    assert isinstance(elastic.boundaries, ElasticBoundaries)
    assert dict(elastic.boundaries.sides) == {"top": "free", "bottom": "absorbing"}
    for later in (again, rebuilt):
        assert np.array_equal(later.signals, first.signals)
        assert later.free_sides == first.free_sides == ("top",)

    # A map given as nested lists becomes the run's own array, read as the
    # engine reads it, so the run steps what an array would have given and
    # an edit to the lists afterwards reaches neither this run nor a node.
    def grid(value: float) -> list[list[float]]:
        return [[value] * 8 for _ in range(8)]

    speeds, densities, rates = grid(343.0), grid(1.2), grid(5.0)
    walls = [[False] * 8 for _ in range(8)]
    walls[2][6] = True
    profile = [413.0] * 8
    listed = FDTDRun(
        c=speeds,
        dx=0.01,
        duration_s=1e-4,
        sources=[_PULSE],
        rho=densities,
        damping=rates,
        obstacle_mask=walls,
        boundaries=FDTDBoundaries(sides={"top": profile}),
        recording=FDTDRecording(probes=[(5, 5)]),
    )
    as_arrays = FDTDRun(
        c=np.array(speeds),
        dx=0.01,
        duration_s=1e-4,
        sources=[_PULSE],
        rho=np.array(densities),
        damping=np.array(rates),
        obstacle_mask=np.array(walls),
        boundaries=FDTDBoundaries(sides={"top": np.array(profile)}),
        recording=FDTDRecording(probes=[(5, 5)]),
    )
    held = fdtd_simulation(listed)
    assert np.array_equal(held.pressures, fdtd_simulation(as_arrays).pressures)
    for rows in (speeds, densities, rates):
        rows[5][5] *= 3.0
    walls[3][3] = True
    profile[0] = -1.0
    assert np.array_equal(fdtd_simulation(listed).pressures, held.pressures)
    for name in ("c", "rho", "damping", "obstacle_mask"):
        assert not getattr(listed, name).flags.writeable, name
    assert listed.boundaries is not None
    assert isinstance(listed.boundaries.sides, MappingProxyType)
    assert not listed.boundaries.sides["top"].flags.writeable

    p_speeds, s_speeds, solid, losses = (
        grid(4000.0),
        grid(2300.0),
        grid(2500.0),
        grid(5.0),
    )
    elastic_listed = ElasticRun(
        c_p=p_speeds,
        c_s=s_speeds,
        dx=0.01,
        duration_s=1e-4,
        rho=solid,
        damping=losses,
        obstacle_mask=[[False] * 7 + [True]] + [[False] * 8 for _ in range(7)],
        sources=[ExplosionSource(ix=4, iy=4, waveform=_PULSE.value)],
        recording=ElasticRecording(probes=[(5, 5)], probe_fields=("p",)),
    )
    signals = elastic_fdtd_simulation(elastic_listed).signals
    for rows in (p_speeds, s_speeds, solid, losses):
        rows[5][5] *= 1.5
    assert np.array_equal(elastic_fdtd_simulation(elastic_listed).signals, signals)
    for name in ("c_p", "c_s", "rho", "damping", "obstacle_mask"):
        assert not getattr(elastic_listed, name).flags.writeable, name


#: A map of numbers too large for a float, which the test below puts in ``c``,
#: in ``damping`` and in the elastic ``c_s``; an impedance takes a row of them.
_HUGE = [[10**400] * 8 for _ in range(8)]


class _NoFloat:
    """A number whose conversion to a float divides by zero."""

    def __float__(self) -> float:
        msg = "a float of this number divides by zero"
        raise ZeroDivisionError(msg)


@pytest.mark.parametrize(
    "build",
    [
        lambda: FDTDRun(c=_HUGE, dx=0.01, duration_s=-1.0, sources=[_PULSE]),
        lambda: FDTDRun(
            c=343.0,
            dx=0.01,
            duration_s=-1.0,
            shape=(8, 8),
            sources=[_PULSE],
            damping=_HUGE,
        ),
        lambda: ElasticRun(
            c_p=4000.0,
            c_s=_HUGE,
            dx=0.01,
            duration_s=-1.0,
            rho=2500.0,
            shape=(8, 8),
            sources=[ExplosionSource(ix=4, iy=4, waveform=_PULSE.value)],
        ),
        lambda: FDTDRun(
            c=[[_NoFloat()] * 8 for _ in range(8)],
            dx=0.01,
            duration_s=-1.0,
            sources=[_PULSE],
        ),
    ],
    ids=["c", "damping", "elastic c_s", "no float in c"],
)
def test_a_map_the_float_conversion_refuses_is_checked_in_its_turn(
    build: Callable[[], FDTDRun | ElasticRun],
) -> None:
    """A map the float conversion refuses is left as given, for the checks.

    Reading a map of numbers too large for a float raises OverflowError, and
    one whose number divides by zero when made a float raises
    ZeroDivisionError. The run checks its duration before its medium, so a
    bad duration is the error named, as it always was.
    """
    with pytest.raises(ValueError, match="duration_s must be positive and finite"):
        build()


def test_elastic_boundaries_hold_a_mapping_of_sides_read_only() -> None:
    sides: dict[str, Any] = {"top": "free", "left": "absorbing"}
    boundaries = ElasticBoundaries(sides=sides, absorbing_layer_cells=3)
    sides["top"] = "absorbing"
    assert isinstance(boundaries.sides, MappingProxyType)
    assert dict(boundaries.sides) == {"top": "free", "left": "absorbing"}
    for back in (pickle.loads(pickle.dumps(boundaries)), copy.deepcopy(boundaries)):
        assert isinstance(back.sides, MappingProxyType)
        assert back == boundaries
    assert ElasticBoundaries(sides="free").sides == "free"


def test_acoustic_boundaries_hold_a_mapping_of_sides_read_only() -> None:
    profile = [400.0, 450.0, 500.0]
    sides: dict[str, Any] = {"top": "absorbing", "left": 413.0, "right": profile}
    boundaries = FDTDBoundaries(sides=sides, absorbing_layer_cells=3)
    sides["top"] = "rigid"
    profile[0] = -1.0
    assert isinstance(boundaries.sides, MappingProxyType)
    assert list(boundaries.sides) == ["top", "left", "right"]
    assert boundaries.sides["top"] == "absorbing"
    held = boundaries.sides["right"]
    assert isinstance(held, np.ndarray)
    assert not held.flags.writeable
    assert held.tolist() == [400.0, 450.0, 500.0]
    for back in (pickle.loads(pickle.dumps(boundaries)), copy.deepcopy(boundaries)):
        assert isinstance(back, FDTDBoundaries)
        assert isinstance(back.sides, MappingProxyType)
        assert back.absorbing_layer_cells == 3
        assert back.sides["left"] == 413.0
        rebuilt = back.sides["right"]
        assert isinstance(rebuilt, np.ndarray)
        assert not rebuilt.flags.writeable
        assert np.array_equal(rebuilt, held)
    assert FDTDBoundaries().sides == "rigid"
    assert FDTDBoundaries().absorbing_layer_cells == 20
    with pytest.raises(TypeError, match="positional argument"):
        FDTDBoundaries("absorbing")  # type: ignore[misc]


def test_acoustic_boundaries_hold_each_impedance_as_the_run_reads_it() -> None:
    """A real scalar of any type is held as a float, a profile of any real
    type as a read-only float64 array of the record's own: what the run
    reads, read once when the record is built.
    """
    profile = np.full(8, 415, dtype=np.int64)
    boundaries = FDTDBoundaries(
        sides={"left": profile, "right": np.float32(415.0), "top": np.int64(415)}
    )
    sides = boundaries.sides
    assert not isinstance(sides, str)
    held = sides["left"]
    assert isinstance(held, np.ndarray)
    assert held.dtype == np.float64
    assert not held.flags.writeable
    assert held.tolist() == [415.0] * 8
    profile[0] = 1
    assert held[0] == 415.0
    for side in ("right", "top"):
        assert type(sides[side]) is float
        assert sides[side] == 415.0
    run = _acoustic(boundaries=boundaries)
    reference = _acoustic(
        boundaries=FDTDBoundaries(
            sides={"left": [415.0] * 8, "right": 415.0, "top": 415.0}
        )
    )
    assert np.array_equal(fdtd_simulation(run).times, fdtd_simulation(reference).times)


@pytest.mark.parametrize(
    "value",
    [
        None,
        True,
        np.True_,
        object(),
        1 + 2j,
        [415, None],
        [True, 415.0],
        (415.0, np.True_),
        [[True], [415.0]],
    ],
)
def test_acoustic_boundaries_refuse_an_impedance_that_is_no_real_number(
    value: object,
) -> None:
    """A flag ran as an impedance of 1 Pa s/m and ``None`` was refused only
    by the run, as an impedance that is not finite: each is refused when the
    record is built, as the type it is, a flag among the numbers of a profile
    too, which NumPy reads as ``1.0`` beside them.
    """
    with pytest.raises(TypeError, match="impedance for side 'left' must be a real"):
        FDTDBoundaries(sides={"left": value})  # type: ignore[dict-item]


@pytest.mark.parametrize("value", [10**400, [10**400] * 8, [[415.0, 415.0], [415.0]]])
def test_acoustic_boundaries_refuse_an_impedance_no_float_holds(value: object) -> None:
    with pytest.raises(ValueError, match="impedance for side 'left' must be"):
        FDTDBoundaries(sides={"left": value})  # type: ignore[dict-item]


@pytest.mark.parametrize("value", [None, True, "415", [True] + [415.0] * 7])
def test_the_acoustic_engine_refuses_an_impedance_that_is_no_real_number(
    value: object,
) -> None:
    with pytest.raises(TypeError, match="impedance for side 'left' must be a real"):
        FDTD2D(c=np.full((8, 8), 343.0), dx=0.01, edge_impedance={"left": value})  # type: ignore[dict-item]


def test_no_boundaries_is_rigid_on_all_four_sides() -> None:
    run = _acoustic(recording=FDTDRecording(probes=[(5, 5)]))
    rigid = _acoustic(
        recording=FDTDRecording(probes=[(5, 5)]),
        boundaries=FDTDBoundaries(sides="rigid"),
    )
    assert run.boundaries is None
    assert np.array_equal(
        fdtd_simulation(run).pressures, fdtd_simulation(rigid).pressures
    )


@pytest.mark.parametrize("build", [_acoustic, _elastic])
def test_a_run_crosses_a_process_boundary(
    build: Callable[..., FDTDRun | ElasticRun],
) -> None:
    run = (
        build(
            boundaries=FDTDBoundaries(
                sides={"left": "absorbing"}, absorbing_layer_cells=2
            )
        )
        if build is _acoustic
        else build()
    )
    back = pickle.loads(pickle.dumps(run))
    simulate = fdtd_simulation if build is _acoustic else elastic_fdtd_simulation
    here, there = simulate(run), simulate(back)
    assert np.array_equal(here.times, there.times)
    assert back._checked.steps == run._checked.steps


def test_a_simulation_function_takes_its_own_run_only() -> None:
    elastic, acoustic = _elastic(), _acoustic()
    with pytest.raises(TypeError, match="'run' must be an FDTDRun, got ElasticRun"):
        fdtd_simulation(elastic)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="'run' must be an ElasticRun, got FDTDRun"):
        elastic_fdtd_simulation(acoustic)  # type: ignore[arg-type]


def _over_a_map(engine: Engine, shape: object) -> FDTDRun | ElasticRun:
    """A run whose speed is a map, with *shape* beside it."""
    if engine == "acoustic":
        return FDTDRun(
            c=np.full((8, 8), 343.0),
            dx=0.01,
            duration_s=1e-4,
            sources=[_PULSE],
            shape=shape,  # type: ignore[arg-type]
        )
    return ElasticRun(
        c_p=np.full((8, 8), 4000.0),
        c_s=2300.0,
        dx=0.01,
        duration_s=1e-4,
        sources=[ExplosionSource(ix=4, iy=4, waveform=_PULSE.value)],
        rho=2500.0,
        shape=shape,  # type: ignore[arg-type]
    )


@pytest.mark.parametrize("engine", ["acoustic", "elastic"])
def test_a_run_holds_the_shape_it_is_given_as_a_pair_of_ints(engine: Engine) -> None:
    """A list or NumPy counts read back as the tuple of ints the grid is.

    With a map, the shape was not read and the run kept whatever it was
    handed, a list a caller could still append to included.
    """
    by_speed = (_acoustic if engine == "acoustic" else _elastic)(shape=[np.int64(8), 8])
    by_map = _over_a_map(engine, [np.int64(8), 8])
    for run in (by_speed, by_map):
        assert run.shape == (8, 8)
        assert [type(n) for n in run.shape] == [int, int]


@pytest.mark.parametrize("engine", ["acoustic", "elastic"])
@pytest.mark.parametrize(
    "shape", [range(8, 10), np.array([8, 9]), np.array([8, 9], dtype=np.int32)]
)
def test_a_shape_is_any_sequence_of_two_counts_or_an_array_of_them(
    engine: Engine, shape: object
) -> None:
    """The annotation took any sequence and the run a tuple or a list only:
    ``range(8, 10)`` passed mypy and raised ``TypeError``. Any sequence of the
    two counts is read now, and a one-dimensional integer array as its items.
    """
    run = (_acoustic if engine == "acoustic" else _elastic)(shape=shape)
    assert run.shape == (8, 9)
    assert [type(n) for n in run.shape] == [int, int]


@pytest.mark.parametrize("engine", ["acoustic", "elastic"])
@pytest.mark.parametrize(
    ("shape", "error"),
    [
        ((8, 8, 1), ValueError),
        ((8, 0), ValueError),
        (8, TypeError),
        ("xx", TypeError),
        (np.array([[8, 8]]), TypeError),
    ],
)
def test_a_run_refuses_a_malformed_shape_beside_a_map_too(
    engine: Engine, shape: object, error: type[Exception]
) -> None:
    with pytest.raises(error, match="shape must be a pair of positive integers"):
        _over_a_map(engine, shape)


@pytest.mark.parametrize("engine", ["acoustic", "elastic"])
def test_a_shape_beside_a_map_names_the_map_s_grid(engine: Engine) -> None:
    """A shape beside a map was held as given, the map's grid or not, and
    the engine read none: each now refuses one that names another grid.
    """
    name = "c" if engine == "acoustic" else "c_p"
    match = rf"shape \(4, 8\) does not match the {name} map, whose shape is \(8, 8\)"
    with pytest.raises(ValueError, match=match):
        _over_a_map(engine, (4, 8))
    if engine == "acoustic":
        with pytest.raises(ValueError, match=match):
            FDTD2D(c=np.full((8, 8), 343.0), dx=0.01, shape=(4, 8))
        with pytest.raises(TypeError, match="shape must be a pair"):
            FDTD2D(c=np.full((8, 8), 343.0), dx=0.01, shape="garbage")  # type: ignore[arg-type]
        assert FDTD2D(
            c=np.full((8, 8), 343.0), dx=0.01, shape=[8, np.int64(8)]
        ).c.shape == (
            8,
            8,
        )
        return
    with pytest.raises(ValueError, match=match):
        ElasticFDTD2D(
            c_p=np.full((8, 8), 4000.0), c_s=2300.0, dx=0.01, rho=2500.0, shape=(4, 8)
        )
    with pytest.raises(TypeError, match="shape must be a pair"):
        ElasticFDTD2D(
            c_p=np.full((8, 8), 4000.0), c_s=2300.0, dx=0.01, rho=2500.0, shape="xx"
        )  # type: ignore[arg-type]
    assert ElasticFDTD2D(
        c_p=4000.0, c_s=2300.0, dx=0.01, rho=2500.0, shape=[np.int64(8), 8]
    ).c_p.shape == (8, 8)


@pytest.mark.parametrize(
    ("shape", "error"),
    [((8, 8, 3), ValueError), ("xx", TypeError), ((8, 1.5), ValueError)],
)
def test_from_regions_reads_its_shape_as_the_engines_do(
    shape: object, error: type[Exception]
) -> None:
    """A third count was dropped and a text indexed a letter at a time."""
    with pytest.raises(error, match="shape must be a pair of positive integers"):
        ElasticFDTD2D.from_regions(shape, 0.01, background=(4000.0, 2300.0, 2500.0))  # type: ignore[arg-type]


def test_a_single_probe_field_is_one_field() -> None:
    """``probe_fields="vy"`` was read a letter at a time and refused "v"."""
    assert ElasticRecording(probe_fields="vy").probe_fields == ("vy",)
    assert ElasticRecording(probe_fields="p").probe_fields == ("p",)
    with pytest.raises(ValueError, match="'probe_fields' must be one of"):
        ElasticRecording(probe_fields="pv")  # type: ignore[arg-type]
