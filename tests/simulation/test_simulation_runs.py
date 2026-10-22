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
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from phonometry.simulation import (
    ElasticBoundaries,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDRecording,
    FDTDRun,
    GaussianPulse,
    elastic_fdtd_simulation,
    fdtd_simulation,
)

if TYPE_CHECKING:
    from collections.abc import Callable

_PULSE = GaussianPulse(ix=4, iy=4, half_width_s=4e-5)


def _acoustic(**changes: Any) -> FDTDRun:
    fields: dict[str, Any] = {"shape": (8, 8), "sources": [_PULSE], **changes}
    return FDTDRun(343.0, 0.01, 1e-4, **fields)


def _elastic(**changes: Any) -> ElasticRun:
    source = ExplosionSource(ix=4, iy=4, waveform=_PULSE.value)
    fields: dict[str, Any] = {
        "shape": (8, 8),
        "rho": 2500.0,
        "sources": [source],
        **changes,
    }
    return ElasticRun(4000.0, 2300.0, 0.01, 1e-4, **fields)


@pytest.mark.parametrize(
    ("build", "bad", "error", "match"),
    [
        (_acoustic, {"rho": -1.0}, ValueError, "rho must be strictly positive"),
        (
            _acoustic,
            {"boundaries": {"left": np.ones(3)}},
            ValueError,
            "impedance for side 'left'",
        ),
        (
            _acoustic,
            {"boundaries": "absorbing", "absorbing_layer_cells": 0},
            ValueError,
            "absorbing_layer_cells must be >= 1",
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


def test_a_run_takes_its_grid_and_duration_by_position_and_the_rest_by_name() -> None:
    with pytest.raises(TypeError):
        FDTDRun(343.0, 0.01, 1e-4, [_PULSE])  # type: ignore[misc]
    run = _acoustic()
    assert (run.c, run.dx, run.duration, run.shape) == (343.0, 0.01, 1e-4, (8, 8))
    with pytest.raises(dataclasses.FrozenInstanceError):
        run.dx = 0.02  # type: ignore[misc]


def test_a_run_does_not_follow_what_its_caller_changes() -> None:
    c = np.full((8, 8), 343.0)
    sources = [_PULSE]
    edge = np.full(8, 413.0)
    boundaries: dict[str, Any] = {"left": "absorbing", "top": edge}
    run = FDTDRun(
        c,
        0.01,
        1e-4,
        sources=sources,
        boundaries=boundaries,
        absorbing_layer_cells=2,
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
    assert isinstance(run.boundaries, MappingProxyType)
    assert set(run.boundaries) == {"left", "top"}
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
        speeds,
        0.01,
        1e-4,
        sources=[_PULSE],
        rho=densities,
        damping=rates,
        obstacle_mask=walls,
        boundaries={"top": profile},
        recording=FDTDRecording(probes=[(5, 5)]),
    )
    as_arrays = FDTDRun(
        np.array(speeds),
        0.01,
        1e-4,
        sources=[_PULSE],
        rho=np.array(densities),
        damping=np.array(rates),
        obstacle_mask=np.array(walls),
        boundaries={"top": np.array(profile)},
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
    assert not listed.boundaries["top"].flags.writeable

    p_speeds, s_speeds, solid, losses = (
        grid(4000.0),
        grid(2300.0),
        grid(2500.0),
        grid(5.0),
    )
    elastic_listed = ElasticRun(
        p_speeds,
        s_speeds,
        0.01,
        1e-4,
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
        lambda: FDTDRun(_HUGE, 0.01, -1.0, sources=[_PULSE]),
        lambda: FDTDRun(
            343.0, 0.01, -1.0, shape=(8, 8), sources=[_PULSE], damping=_HUGE
        ),
        lambda: FDTDRun(
            343.0,
            0.01,
            -1.0,
            shape=(8, 8),
            sources=[_PULSE],
            boundaries={"top": [10**400] * 8},
        ),
        lambda: ElasticRun(
            4000.0,
            _HUGE,
            0.01,
            -1.0,
            rho=2500.0,
            shape=(8, 8),
            sources=[ExplosionSource(ix=4, iy=4, waveform=_PULSE.value)],
        ),
        lambda: FDTDRun(
            [[_NoFloat()] * 8 for _ in range(8)], 0.01, -1.0, sources=[_PULSE]
        ),
    ],
    ids=["c", "damping", "impedance", "elastic c_s", "no float in c"],
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
    with pytest.raises(ValueError, match="duration must be positive and finite"):
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


@pytest.mark.parametrize("build", [_acoustic, _elastic])
def test_a_run_crosses_a_process_boundary(
    build: Callable[..., FDTDRun | ElasticRun],
) -> None:
    run = (
        build(boundaries={"left": "absorbing"}, absorbing_layer_cells=2)
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
