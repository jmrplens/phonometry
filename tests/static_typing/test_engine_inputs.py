#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The FDTD engines and their records take, for mypy too, what runs.

A medium map written as nested lists, a float32 map, a count NumPy hands
over as ``np.int64`` (a shape, an ``argmax``) and a side named with its
``Literal`` all ran, and the engines' annotations refused them: a map was
``float | NDArray[np.float64]``, a cell index or a step count ``int``. CI
type checks every file in this directory alongside ``src`` and ``scripts``,
so each call here holds an annotation to what its body takes, and each
refusal holds a misspelt choice to a type error as it is a ``ValueError``
when the call runs. ``scripts/check_parameter_annotations.py`` holds every
public parameter to the rule; this file holds the forms a caller writes.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry.simulation import (
    FDTD2D,
    CWSource,
    ElasticBoundaries,
    ElasticFDTD2D,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDBoundaries,
    FDTDRecording,
    FDTDRun,
    ForceSource,
    GaussianPulse,
    PlaneWaveSource,
    SignalSource,
)

if TYPE_CHECKING:
    from numpy.typing import NDArray

#: A small grid, ``(ny, nx)``.
_NY, _NX = 12, 16


def test_a_run_takes_its_maps_as_nested_lists() -> None:
    """A map written by hand is a list of rows; the run holds it as its own array."""
    run = FDTDRun(
        c=[[343.0] * _NX] * _NY,
        dx=0.01,
        duration_s=1e-4,
        sources=[GaussianPulse(ix=4, iy=5, half_width_s=4e-5)],
        shape=[_NY, _NX],
        rho=[[1.2] * _NX] * _NY,
        obstacle_mask=[[False] * _NX] * (_NY - 1) + [[False] * (_NX - 1) + [True]],
        damping=[[0.0] * _NX] * _NY,
    )
    assert isinstance(run.c, np.ndarray)
    assert run.shape == (_NY, _NX)
    elastic = ElasticRun(
        c_p=[[4000.0] * _NX] * _NY,
        c_s=[[2300.0] * _NX] * _NY,
        dx=0.01,
        duration_s=2e-4,
        sources=[ExplosionSource(ix=5, iy=4, waveform=math.sin)],
        rho=[[2700.0] * _NX] * _NY,
    )
    assert isinstance(elastic.c_p, np.ndarray)


def test_an_engine_takes_its_maps_as_nested_lists() -> None:
    sim = FDTD2D(
        [[343.0] * _NX] * _NY,
        0.01,
        rho=[[1.2] * _NX] * _NY,
        damping=[[0.0] * _NX] * _NY,
        edge_impedance={"left": [413.0] * _NY},
        obstacle_mask=[[False] * _NX] * _NY,
    )
    assert sim.c.shape == (_NY, _NX)
    elastic = ElasticFDTD2D(
        [[4000.0] * _NX] * _NY,
        [[2300.0] * _NX] * _NY,
        0.01,
        rho=[[2700.0] * _NX] * _NY,
        free_sides=("top", "bottom"),
    )
    assert elastic.free_sides == ("top", "bottom")


def test_a_float32_map_is_held_as_given() -> None:
    """A float32 map stays float32 in the run: ``Field2D`` admits any float dtype."""
    c: NDArray[np.float32] = np.full((_NY, _NX), 343.0, dtype=np.float32)
    run = FDTDRun(
        c=c,
        dx=0.01,
        duration_s=1e-4,
        sources=[GaussianPulse(ix=4, iy=5, half_width_s=4e-5)],
    )
    assert isinstance(run.c, np.ndarray)
    assert run.c.dtype == np.float32


def test_a_numpy_integer_is_a_cell_index_and_a_count() -> None:
    """``np.argmax`` and an array's shape give the counts numpy code passes on."""
    ix = np.int64(np.argmax([0.0, 1.0, 0.0, 0.0, 0.0]))
    pulse = GaussianPulse(ix=ix, iy=np.int64(5), half_width_s=4e-5)
    tone = CWSource(ix=np.int64(6), iy=np.int64(5), frequency=2000.0)
    sampled = SignalSource(
        ix=np.int64(7), iy=np.int64(5), samples=[0.0, 1.0, 0.0], fs=48000.0
    )
    plane = PlaneWaveSource(direction="down", waveform=math.sin, offset=np.int64(1))
    assert type(pulse.ix) is int
    assert type(sampled.iy) is int
    assert type(plane.offset) is int
    recording = FDTDRecording(
        probes=[(np.int64(3), 4), (5, np.int64(6))],
        snapshot_every=np.int64(2),
        snapshot_decimation=np.int64(2),
    )
    assert recording.probes == ((3, 4), (5, 6))
    boundaries = FDTDBoundaries(sides="absorbing", absorbing_layer_cells=np.int64(3))
    assert boundaries.absorbing_layer_cells == 3
    shape = np.zeros((_NY, _NX)).shape
    run = FDTDRun(
        c=343.0,
        dx=0.01,
        duration_s=1e-4,
        sources=[pulse, tone],
        shape=(np.int64(shape[0]), np.int64(shape[1])),
        recording=recording,
        boundaries=boundaries,
    )
    assert run.shape == (_NY, _NX)
    sim = FDTD2D(343.0, 0.01, shape=shape, absorbing_layer_cells=np.int64(2))
    sim.add_contour_probe(
        np.int64(4), np.int64(6), np.int64(4), np.int64(6), frequencies=[1000.0]
    )
    frames = sim.run(np.int64(2), snapshot_every=np.int64(1), snapshot_decimation=1)
    assert frames.shape[0] == 3


def test_a_numpy_integer_is_an_elastic_count() -> None:
    explosion = ExplosionSource(ix=np.int64(5), iy=np.int64(4), waveform=math.sin)
    force = ForceSource(
        ix=np.int64(3), iy=np.int64(2), direction="y", waveform=math.sin
    )
    recording = ElasticRecording(
        probes=[(np.int64(3), 4)],
        probe_fields=("p", "vy"),
        snapshot_every=np.int64(2),
        snapshot_decimation=np.int64(1),
    )
    boundaries = ElasticBoundaries(
        sides={"top": "free", "bottom": "absorbing"},
        absorbing_layer_cells=np.int64(3),
    )
    run = ElasticRun(
        c_p=4000.0,
        c_s=2300.0,
        dx=0.01,
        duration_s=2e-4,
        sources=[explosion, force],
        rho=2700.0,
        shape=(np.int64(_NY), np.int64(_NX)),
        recording=recording,
        boundaries=boundaries,
    )
    assert run.shape == (_NY, _NX)
    sim = ElasticFDTD2D.from_regions(
        (np.int64(_NY), np.int64(_NX)),
        0.01,
        background=(4000.0, 2300.0, 2700.0),
        absorbing_layer_cells=np.int64(2),
    )
    assert sim.run(np.int64(1)).size == 0


def test_a_misspelt_side_is_a_type_error_and_refused_when_built() -> None:
    """A side outside its ``Literal`` is refused by mypy and by the record."""
    with pytest.raises(ValueError, match="'sides' must be one of"):
        FDTDBoundaries(sides="anechoic")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=r"'sides\['left'\]' must be one of"):
        ElasticBoundaries(sides={"left": "open"})  # type: ignore[dict-item]
    with pytest.raises(ValueError, match="'free_sides' must be one of"):
        ElasticFDTD2D(
            4000.0,
            2300.0,
            0.01,
            rho=2700.0,
            shape=(_NY, _NX),
            free_sides="middle",  # type: ignore[arg-type]
        )


def test_the_geometry_preview_takes_the_cells_a_recording_takes() -> None:
    """``plot_geometry(probes=...)`` reads each cell as ``FDTDRecording`` does:
    NumPy indices, a list for a pair, an array of pairs, a generator of them.
    """
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    sim = FDTD2D(343.0, 0.01, shape=(_NY, _NX))
    cells = np.array([[3, 4], [5, 6]], dtype=np.int64)
    for probes in (
        [(np.int64(3), np.int64(4))],
        [[3, 4], [5, 6]],
        cells,
        ((i, i) for i in range(2, 4)),
    ):
        sim.plot_geometry(probes=probes)
        plt.close("all")


def test_a_shape_is_any_sequence_of_two_counts_or_an_integer_array() -> None:
    """A range and an integer array of the two counts, as numpy code holds a grid."""
    counts: NDArray[np.int64] = np.array([_NY, _NX], dtype=np.int64)
    pulse = GaussianPulse(ix=2, iy=2, half_width_s=4e-5)
    run = FDTDRun(c=343.0, dx=0.01, duration_s=1e-4, sources=[pulse], shape=counts)
    assert run.shape == (_NY, _NX)
    sim = ElasticFDTD2D(4000.0, 2300.0, 0.01, rho=2500.0, shape=range(_NY, _NY + 2))
    assert sim.c_p.shape == (_NY, _NY + 1)
    regions = ElasticFDTD2D.from_regions(
        counts, 0.01, background=(4000.0, 2300.0, 2500.0)
    )
    assert regions.c_p.shape == (_NY, _NX)


def test_an_impedance_of_any_real_type_is_held_as_the_run_reads_it() -> None:
    """An integer profile, a float32 scalar and a NumPy integer all ran."""
    boundaries = FDTDBoundaries(
        sides={
            "left": np.full(_NY, 415, dtype=np.int64),
            "right": np.float32(415.0),
            "top": np.int64(415),
            "bottom": [415.0] * _NX,
        }
    )
    sides = boundaries.sides
    assert not isinstance(sides, str)
    assert sides["right"] == 415.0
    with pytest.raises(TypeError, match="impedance for side 'left' must be a real"):
        FDTDBoundaries(sides={"left": None})  # type: ignore[dict-item]


def test_a_profile_written_as_a_list_of_numpy_numbers_is_an_impedance() -> None:
    """A list of float32 or int64 impedances is a profile of real numbers.

    It ran, as a list of floats does, and a profile typed ``Sequence[float]``
    refused it: a NumPy float32 or int64 is no ``float`` to a type checker.
    """
    float32s: list[np.float32] = [np.float32(415.0)] * _NY
    int64s: list[np.int64] = [np.int64(415)] * _NX
    boundaries = FDTDBoundaries(sides={"left": float32s, "top": int64s})
    sides = boundaries.sides
    assert not isinstance(sides, str)
    left = sides["left"]
    assert isinstance(left, np.ndarray)
    assert left.dtype == np.float64
    assert left.tolist() == [415.0] * _NY


def test_a_single_probe_field_and_a_sweep_target_of_lists() -> None:
    """A single field name, and a sweep's target spectrum written as lists."""
    from phonometry.room import shaped_sweep_signal

    assert ElasticRecording(probe_fields="vx").probe_fields == ("vx",)
    sweep = shaped_sweep_signal(
        8000.0, 100.0, 2000.0, 0.1, target=([100.0, 1000.0, 4000.0], [0.0, -3.0, -6.0])
    )
    assert np.asarray(sweep).size > 0
