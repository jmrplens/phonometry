#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A record that refuses a ``bytearray`` names it as the ``bytearray`` the caller gave.

A record holds a ``bytearray`` it is given as the ``bytes`` it spells, before
its own checks run (``phonometry._internal.frozen``), so that they refuse it
as the text it is and the record never keeps a value the caller can still
change. The checks read a ``bytes``, then, and a refusal that named the type
of what they read, or quoted it, told the caller they gave a ``bytes``:
``RotorcraftGround(terrain=bytearray(b"abc"))`` was refused as ``not bytes``.
The checks name and quote it through ``given_type`` and ``given_repr``, which
know the ``bytes`` held for a caller's ``bytearray`` while the checks run.

Every record the factories of ``tests/result_factories.py`` build through the
public API, and every record one of them holds (a band set, a run, a
boundary), is built again here with a ``bytearray`` in each of its fields,
whole, as the first member of a tuple or a list, and inside a mapping, a
read-only mapping, a named tuple and an array of objects given in the
field's place, and every refusal the library raises names no ``bytes`` and
quotes none. :data:`OTHERS` builds the
records with a refusal of their own that no factory reaches. A field whose value goes
straight to Python or NumPy is refused in their words
(``could not convert string to float: b'ab'``): that refusal is not raised
by the library, and is left out.
"""

from __future__ import annotations

import dataclasses
import inspect
import linecache
import pathlib
import re
import warnings
from collections.abc import Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
import pytest
import result_factories

import phonometry

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

#: Where the library's own sources lie: a refusal raised there is the
#: library's.
_SOURCE = pathlib.Path(phonometry.__file__).resolve().parent

#: A type named ``bytes``, or a ``bytes`` quoted outside ``bytearray(...)``.
_SAYS_BYTES = re.compile(r"\bbytes\b|(?<!bytearray\()(?<!\w)b['\"]")


def _factories() -> list[tuple[str, Callable[[], object]]]:
    """Every factory of ``result_factories`` that builds a record unasked."""
    found = []
    for name, function in vars(result_factories).items():
        if not (
            inspect.isfunction(function)
            and function.__module__ == result_factories.__name__
            and name.startswith("_")
        ):
            continue
        parameters = inspect.signature(function).parameters.values()
        if any(p.default is p.empty and p.kind != p.VAR_KEYWORD for p in parameters):
            continue
        found.append((name, function))
    return found


class _Held(NamedTuple):
    first: object
    second: object


def _held_in_objects() -> np.ndarray:
    """An array of objects whose first member is a ``bytearray``."""
    held = np.empty(2, dtype=object)
    held[0] = bytearray(b"ab")
    held[1] = 1.0
    return held


def _probes(value: object) -> Iterator[tuple[str, object]]:
    """A ``bytearray`` in place of *value*: whole, as its first member, and in a container.

    A refusal that quotes a container the field was given quotes its
    members, and a record holds the ``bytearray`` among them as the
    ``bytes`` it spells, in a mapping, a read-only mapping, a named tuple
    and an array of objects as in a tuple or a list.
    """
    yield "whole", bytearray(b"ab")
    yield "one byte", bytearray(b"1")
    if type(value) in {tuple, list} and value:
        members = list(value)  # type: ignore[call-overload]
        members[0] = bytearray(b"ab")
        yield "first member", type(value)(members)
    yield "in a mapping", {"k": bytearray(b"ab")}
    yield "in a read-only mapping", MappingProxyType({"k": bytearray(b"ab")})
    yield "in a named tuple", _Held(bytearray(b"ab"), 1.0)
    yield "in an array of objects", _held_in_objects()


def _raised_by_the_library(error: BaseException) -> bool:
    """Whether *error* was raised by a ``raise`` in the library's sources."""
    trace = error.__traceback__
    if trace is None:
        return False
    while trace.tb_next is not None:
        trace = trace.tb_next
    path = pathlib.Path(trace.tb_frame.f_code.co_filename).resolve()
    if not path.is_relative_to(_SOURCE):
        return False
    line = linecache.getline(str(path), trace.tb_lineno).strip()
    return line.startswith("raise")


def _records(value: object) -> Iterator[object]:
    """*value*, if it is a record of the library, and every record it holds, once each."""
    seen: set[int] = set()
    pending = [value]
    while pending:
        item = pending.pop()
        if id(item) in seen:
            continue
        seen.add(id(item))
        if dataclasses.is_dataclass(item) and not isinstance(item, type):
            if type(item).__module__.startswith("phonometry."):
                yield item
            pending.extend(getattr(item, f.name) for f in dataclasses.fields(item))
        elif isinstance(item, tuple | list):
            pending.extend(item)
        elif isinstance(item, Mapping):
            pending.extend(item.values())


def _refusals(record: object) -> Iterator[tuple[str, str]]:
    """Each refusal of a field given a ``bytearray`` that names or quotes a ``bytes``."""
    fields = getattr(type(record), "__dataclass_fields__", {})
    if any(f._field_type is dataclasses._FIELD_INITVAR for f in fields.values()):  # type: ignore[attr-defined]
        return
    name = type(record).__name__
    for field in dataclasses.fields(record):  # type: ignore[arg-type]
        if not field.init:
            continue
        for probe_name, probe in _probes(getattr(record, field.name)):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dataclasses.replace(record, **{field.name: probe})  # type: ignore[type-var]
            except Exception as error:
                message = str(error)
                if _raised_by_the_library(error) and _SAYS_BYTES.search(message):
                    yield f"{name}.{field.name} ({probe_name})", message


@pytest.mark.parametrize(
    "factory",
    [function for _, function in _factories()],
    ids=[n for n, _ in _factories()],
)
def test_a_refusal_names_a_bytearray_the_caller_gave(
    factory: Callable[[], object],
) -> None:
    """Each field of a real record, given a ``bytearray``, is refused naming one."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        record = factory()
    held = list(_records(record))
    if not held:
        pytest.skip("holds no record")
    offenders = {field: message for each in held for field, message in _refusals(each)}
    assert not offenders, offenders


def _signal_burst() -> object:
    from phonometry.vibration.human.signal_burst import SIGNAL_BURST_RESPONSE

    measured = {
        cycles: {
            "rms": SIGNAL_BURST_RESPONSE["hand-arm", "band-limiting", cycles]["rms"]
        }
        for cycles in (1, 2, 4, 8, 16, None)
    }
    return phonometry.vibration.verify_signal_burst_response(
        "hand-arm", "band-limiting", measured
    )


def _fdtd_run() -> object:
    return phonometry.simulation.FDTDRun(
        c=343.0,
        dx=0.02,
        duration_s=1e-3,
        sources=[phonometry.simulation.GaussianPulse(ix=5, iy=5, half_width_s=2e-4)],
        shape=(20, 20),
    )


_THIRD_OCTAVES = [
    100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0,
    630.0, 800.0, 1000.0, 1250.0, 1600.0, 2000.0, 2500.0, 3150.0,
]  # fmt: skip

#: Records that refuse a text by a check of their own, which no factory of
#: ``result_factories`` reaches, each built through the public API.
OTHERS: dict[str, Callable[[], object]] = {
    "EPNLIntegration": lambda: phonometry.aircraft.EPNLIntegration(
        90.0, 95.0, 0.0, (0, 1)
    ),
    "EPNLResult": lambda: phonometry.aircraft.EPNLResult(
        frequencies=[50.0, 63.0],
        times=[0.0, 1.0, 2.0],
        pnl=[0.0, 0.0, 0.0],
        tone_correction=[0.0, 0.0, 0.0],
        pnlt=[0.0, 0.0, 0.0],
        pnltm=0.0,
        bandsharing_adjustment=0.0,
        duration_correction=0.0,
        epnl=0.0,
        band_limits=(0, 2),
    ),
    "SignalBurstVerification": _signal_burst,
    "FloorCoveringImprovementResult": lambda: phonometry.building.impact_improvement(
        [70.0] * 16, [50.0] * 16, frequencies=_THIRD_OCTAVES
    ),
    "DiffuseSoundFieldCheck": lambda: phonometry.hearing.check_diffuse_sound_field(
        dict.fromkeys(("front", "back", "left", "right", "up", "down"), [0.5] * 11),
        [0.0] * 11,
    ),
    "IntensityInstrumentComplianceResult": lambda: (
        phonometry.emission.verify_intensity_class(
            [20.0] * 16, frequencies=_THIRD_OCTAVES
        )
    ),
    "RailwayTrack": lambda: phonometry.environment.RailwayTrack(
        rail_roughness=phonometry.environment.WavelengthSpectrum(
            wavelengths_mm=[1.0, 2.0, 3.0], levels=[0.0, 0.0, 0.0]
        ),
        track_transfer=[0.0, 0.0, 0.0],
    ),
    "FDTDRun": _fdtd_run,
    "FDTDResult": lambda: phonometry.simulation.fdtd_simulation(_fdtd_run()),
    "ElasticRun": lambda: phonometry.simulation.ElasticRun(
        c_p=5900.0,
        c_s=3200.0,
        dx=1e-3,
        duration_s=1e-6,
        sources=[phonometry.simulation.ExplosionSource(ix=5, iy=5, waveform=[0.0] * 4)],
        rho=7850.0,
        shape=(20, 20),
    ),
}


def _names_the_bytearray(record: object) -> bool:
    """Whether a field of *record*, given a ``bytearray``, is refused naming it."""
    for field in dataclasses.fields(record):  # type: ignore[arg-type]
        if not field.init:
            continue
        for _, probe in _probes(getattr(record, field.name)):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    dataclasses.replace(record, **{field.name: probe})  # type: ignore[type-var]
            except Exception as error:
                if _raised_by_the_library(error) and "bytearray" in str(error):
                    return True
    return False


@pytest.mark.parametrize("build", list(OTHERS.values()), ids=list(OTHERS))
def test_a_record_no_factory_builds_names_the_bytearray_too(
    build: Callable[[], object],
) -> None:
    """A record with a refusal of its own names the ``bytearray`` the caller gave."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        record = build()
    held = list(_records(record))
    offenders = {field: message for each in held for field, message in _refusals(each)}
    assert not offenders, offenders
    assert _names_the_bytearray(record)
