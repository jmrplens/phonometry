#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A simulation travels to a node as data, never as code.

A run has to reach the node as the record the caller built: the tables below
give every field of each run a value, away from its default where the run
takes another, and every parameter of each function a node runs an example,
and the guards fail when a field or a parameter is added without one. A
callable travels only as the ``value`` of a library source; anything else is
refused with a TypeError that names it.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
from types import MappingProxyType
from typing import Any

import numpy as np
import pytest

from phonometry import simulation
from phonometry.simulation import (
    CWSource,
    ElasticBoundaries,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDRecording,
    FDTDRun,
    ForceSource,
    GaussianPulse,
    PlaneWaveSource,
    SignalSource,
)
from phonometry.simulation._remote import wire

_MASK = np.zeros((10, 12), dtype=bool)
_MASK[4:6, 7:9] = True

#: A value for every field of an FDTDRun, away from its default where the run
#: takes another (``shape`` is read only with a scalar ``c``).
_EVERY_ACOUSTIC_FIELD: dict[str, Any] = {
    "c": np.full((10, 12), 343.0),
    "dx": 0.01,
    "duration": 1e-4,
    "sources": [
        GaussianPulse(ix=2, iy=3, half_width_s=4e-5, t0=1.6e-4, amplitude=2.0),
        CWSource(ix=3, iy=3, frequency=2000.0, ramp_cycles=1.5),
        SignalSource(ix=4, iy=3, samples=np.sin(np.linspace(0.0, 6.0, 50)), fs=48000.0),
        PlaneWaveSource(
            direction="down",
            waveform=CWSource(ix=0, iy=0, frequency=3000.0).value,
            offset=1,
        ),
    ],
    "shape": None,
    "rho": np.full((10, 12), 1.21),
    "cfl": 0.5,
    "recording": FDTDRecording(
        probes=[(2, 2), (9, 8)], snapshot_every=2, snapshot_decimation=3
    ),
    "boundaries": MappingProxyType(
        {"left": "absorbing", "top": 413.0, "right": np.linspace(400.0, 500.0, 10)}
    ),
    "absorbing_layer_cells": 2,
    "obstacle_mask": _MASK,
    "damping": np.linspace(0.0, 3.0, 120).reshape(10, 12),
}

#: A value for every field of an ElasticRun.
_EVERY_ELASTIC_FIELD: dict[str, Any] = {
    "c_p": np.full((10, 12), 4000.0),
    "c_s": np.float32(2300.0),
    "dx": 0.01,
    "duration": 2e-4,
    "sources": [
        ExplosionSource(
            ix=5, iy=4, waveform=GaussianPulse(ix=0, iy=0, half_width_s=2e-5).value
        ),
        ForceSource(
            ix=3,
            iy=2,
            direction="y",
            waveform=SignalSource(ix=0, iy=0, samples=np.ones(8), fs=1e5).value,
            amplitude=0.5,
        ),
    ],
    "rho": 2500,
    "shape": None,
    "cfl": 0.55,
    "recording": ElasticRecording(
        probes=[(6, 5)],
        probe_fields=("p", "vy"),
        snapshot_every=2,
        snapshot_field="vx",
        snapshot_decimation=2,
    ),
    "boundaries": ElasticBoundaries(
        sides={"top": "free", "bottom": "absorbing"}, absorbing_layer_cells=2
    ),
    "obstacle_mask": _MASK,
    "damping": np.float64(0.5),
}

#: The fields the tables leave at their default: ``shape`` is read only with a
#: scalar speed, and both tables give a map.
_AT_DEFAULT = frozenset({"shape"})

#: Each function a node runs, and an example of each of its parameters but
#: ``compute``, which travels as the job's placement.
_EVERY_PARAMETER: dict[str, dict[str, Any]] = {
    "fdtd_simulation": {"run": FDTDRun(**_EVERY_ACOUSTIC_FIELD)},
    "elastic_fdtd_simulation": {"run": ElasticRun(**_EVERY_ELASTIC_FIELD)},
}


def _round_trip(arguments: dict[str, Any]) -> dict[str, object]:
    tree, buffers = wire.encode_arguments(arguments)
    text = json.dumps(tree, allow_nan=False)  # the tree is JSON as it stands
    return wire.decode_arguments(json.loads(text), [bytearray(b) for b in buffers])


def _assert_same(got: object, want: object, where: str = "") -> None:
    """*got* is *want* rebuilt: same types, same values, arrays bit for bit."""
    assert type(got) is type(want), where
    if isinstance(want, np.ndarray):
        assert isinstance(got, np.ndarray), where
        assert got.dtype == want.dtype, where
        assert np.array_equal(got, want), where
    elif inspect.ismethod(want):
        _assert_same(got.__self__, want.__self__, f"{where}.__self__")  # type: ignore[attr-defined]
        assert got.__func__ is want.__func__, where  # type: ignore[attr-defined]
    elif dataclasses.is_dataclass(want):
        for f in dataclasses.fields(want):
            _assert_same(
                getattr(got, f.name), getattr(want, f.name), f"{where}.{f.name}"
            )
    elif isinstance(want, dict | MappingProxyType):
        assert list(got) == list(want), where  # type: ignore[call-overload]
        for key in want:
            _assert_same(got[key], want[key], f"{where}[{key!r}]")  # type: ignore[index]
    elif isinstance(want, list | tuple):
        assert len(got) == len(want), where  # type: ignore[arg-type]
        for k, (a, b) in enumerate(zip(got, want, strict=True)):  # type: ignore[call-overload]
            _assert_same(a, b, f"{where}[{k}]")
    else:
        assert got == want, where


@pytest.mark.parametrize(
    ("record", "table"),
    [(FDTDRun, _EVERY_ACOUSTIC_FIELD), (ElasticRun, _EVERY_ELASTIC_FIELD)],
)
def test_every_field_of_a_run_travels(record: type, table: dict[str, Any]) -> None:
    fields = {f.name for f in dataclasses.fields(record) if f.init}
    assert set(table) == fields, "give every field of the run a value here"
    at_default = [
        f.name
        for f in dataclasses.fields(record)
        if f.default is not dataclasses.MISSING
        and f.name not in _AT_DEFAULT
        and not _away_from(table[f.name], f.default)
    ]
    assert not at_default, (
        f"give these fields a value away from their default: {at_default}"
    )
    run = record(**table)
    _assert_same(_round_trip({"run": run})["run"], run, "run")


def _away_from(value: object, default: object) -> bool:
    """Whether *value* differs from a field's *default*, a number, a name or None."""
    if default is None:
        return value is not None
    if np.isscalar(value):
        return bool(value != default)
    # A map, a mapping or a record where the default is one number or one name.
    return True


@pytest.mark.parametrize("name", sorted(_EVERY_PARAMETER))
def test_every_parameter_of_a_remote_function_travels(name: str) -> None:
    function = getattr(simulation, name)
    parameters = set(inspect.signature(function).parameters) - {"compute"}
    assert set(_EVERY_PARAMETER[name]) == parameters, (
        "give every parameter an example here"
    )
    back = _round_trip(_EVERY_PARAMETER[name])
    for key, value in _EVERY_PARAMETER[name].items():
        _assert_same(back[key], value, key)


def test_a_number_keeps_its_numpy_type_and_every_bit() -> None:
    values = {
        "a": np.float32(0.1),
        "b": np.int64(-7),
        "c": np.True_,
        "d": 0.1 + 2e-17,
        "e": float("inf"),
    }
    back = _round_trip(values)
    for name, value in values.items():
        _assert_same(back[name], value, name)


def test_an_array_keeps_its_dtype_shape_and_order() -> None:
    arrays = {
        "big": np.arange(12, dtype=">f8").reshape(3, 4),
        "fortran": np.asfortranarray(np.arange(6.0).reshape(2, 3)),
        "empty": np.zeros((0, 5)),
        "scalar": np.array(3.5),
        "mask": np.array([[True, False]]),
    }
    back = _round_trip(arrays)
    for name, value in arrays.items():
        got = back[name]
        assert isinstance(got, np.ndarray)
        assert got.shape == value.shape, name
        assert np.array_equal(got, value), name
        assert got.dtype == value.dtype.newbyteorder("="), name


@pytest.mark.parametrize(
    ("arguments", "match"),
    [
        (
            {"sources": [ExplosionSource(ix=1, iy=1, waveform=lambda t: 0.0 * t)]},
            r"sources\[0\]\.waveform cannot travel to a node: only the \.value of a GaussianPulse",
        ),
        (
            {"sources": [PlaneWaveSource(direction="down", waveform=np.sin)]},
            r"sources\[0\]\.waveform cannot travel to a node",
        ),
        (
            {"c": np.zeros(3, dtype=complex)},
            "c cannot travel to a node: an array of complex128",
        ),
        ({"c": np.array(["343"])}, "c cannot travel to a node: an array of <U3"),
        (
            {"boundaries": {1: "rigid"}},
            r"boundaries cannot travel to a node: its key 1 is not a text",
        ),
        ({"shape": {10, 12}}, "shape cannot travel to a node: a set"),
        (
            {"sources": GaussianPulse},
            "sources cannot travel to a node: only the .value",
        ),
    ],
)
def test_what_cannot_travel_is_refused_by_name(
    arguments: dict[str, object], match: str
) -> None:
    with pytest.raises(TypeError, match=match):
        wire.encode_arguments(arguments)


class _LouderPulse(GaussianPulse):
    def value(self, t: float) -> float:
        return 2.0 * super().value(t)


def test_a_subclass_of_a_library_record_is_refused() -> None:
    pulse = _LouderPulse(ix=1, iy=1, half_width_s=1e-5)
    with pytest.raises(
        TypeError,
        match="sources\\[0\\] cannot travel to a node: _LouderPulse is a subclass of GaussianPulse",
    ):
        wire.encode_arguments({"sources": [pulse]})


def test_the_value_of_a_subclass_is_refused_as_a_waveform() -> None:
    source = ExplosionSource(
        ix=1, iy=1, waveform=_LouderPulse(ix=0, iy=0, half_width_s=1e-5).value
    )
    with pytest.raises(
        TypeError, match=r"sources\[0\]\.waveform cannot travel to a node"
    ):
        wire.encode_arguments({"sources": [source]})


@pytest.mark.skipif(
    np.dtype(np.longdouble).itemsize <= 8,
    reason="long double is float64 on this platform, and float64 travels",
)
def test_a_long_double_is_refused_rather_than_rounded() -> None:
    arguments = {"c": np.zeros(3, dtype=np.longdouble)}
    with pytest.raises(TypeError, match="c cannot travel to a node: an array of float"):
        wire.encode_arguments(arguments)


def test_a_read_only_mapping_of_a_run_is_read_only_again_on_the_node() -> None:
    """A run's boundaries travel as a dict, and the rebuilt run freezes them again.

    The acoustic run holds a mapping of sides with an impedance array in it,
    the elastic run an ElasticBoundaries holding a mapping of sides: each
    comes back as the record it was, its arrays the rebuilt run's own.
    """
    acoustic = FDTDRun(**_EVERY_ACOUSTIC_FIELD)
    elastic = ElasticRun(**_EVERY_ELASTIC_FIELD)
    back = _round_trip({"acoustic": acoustic, "elastic": elastic})
    _assert_same(back["acoustic"], acoustic, "acoustic")
    _assert_same(back["elastic"], elastic, "elastic")
    rebuilt_acoustic, rebuilt_elastic = back["acoustic"], back["elastic"]
    assert isinstance(rebuilt_acoustic, FDTDRun)
    assert isinstance(rebuilt_elastic, ElasticRun)
    assert isinstance(rebuilt_acoustic.boundaries, MappingProxyType)
    impedance = rebuilt_acoustic.boundaries["right"]
    assert isinstance(impedance, np.ndarray)
    assert not impedance.flags.writeable
    assert isinstance(rebuilt_acoustic.c, np.ndarray)
    assert not rebuilt_acoustic.c.flags.writeable
    assert rebuilt_elastic.boundaries is not None
    assert isinstance(rebuilt_elastic.boundaries.sides, MappingProxyType)


def test_a_float32_array_stays_float32() -> None:
    c = np.linspace(330.0, 350.0, 120, dtype=np.float32).reshape(10, 12)
    run = FDTDRun(c, 0.01, 1e-4, sources=[GaussianPulse(ix=2, iy=3, half_width_s=4e-5)])
    back = _round_trip({"c": c, "run": run})
    _assert_same(back["c"], c, "c")
    _assert_same(back["run"], run, "run")
    rebuilt = back["run"]
    assert isinstance(rebuilt, FDTDRun)
    assert isinstance(rebuilt.c, np.ndarray)
    assert rebuilt.c.dtype == np.float32


@pytest.mark.parametrize(
    "node",
    [
        1.5,
        [1, 2],
        {"$": "pickle", "data": "gASV"},
        {"$": ["array"]},
        {"$": "array", "dtype": "O", "shape": [1], "buffer": 0},
        {"$": "scalar", "dtype": "complex128", "value": 0},
    ],
)
def test_a_form_the_encoder_does_not_write_is_refused(node: object) -> None:
    with pytest.raises(ValueError, match="not a wire form"):
        wire.decode_arguments({"c": node}, [bytearray(8)])


def test_the_guard_names_every_function_a_node_runs() -> None:
    from phonometry.simulation._remote import node

    assert set(_EVERY_PARAMETER) == set(node.FUNCTIONS)
