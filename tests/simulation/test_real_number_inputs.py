#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every real input of the FDTD engines refuses a complex value and a text.

NumPy reads both as real numbers nobody gave: a complex value as its real
part, with no more than a ``ComplexWarning`` (``float(np.complex128(343 +
50j))`` is ``343.0``, and so is each element of ``np.asarray(z,
dtype=np.float64)``), and a text as the number it spells
(``np.asarray([["343"]], dtype=np.float64)``). The acoustic engine refused a
complex ``c`` or ``rho`` with ``TypeError``, while the elastic engine stepped
the real part of a complex ``c_p``, ``c_s`` or ``rho`` (silently for a
number, ``float(np.real(value))``), every map of both engines took a text,
and every scalar of both engines that a check read through ``float`` (``dx``,
``cfl``, a source's frequency or amplitude, a material's speeds) took the
real part of a NumPy complex number: a run that steps a medium nobody gave.
Each case here hands one input a complex value or a text, in each spelling a
caller writes it, and the input refuses it by name, as the wrong type
([A42](docs/contributing/api.md#a42)).

A ``Decimal`` or a ``Fraction`` is a real number of another type, and is
read as the float it holds wherever a real number belongs
([A61](docs/contributing/api.md#a61)): a run, a source or an engine given
one steps as the one given that float, a source holds that float and so
travels to a node, and a number of any type past a float's range is refused
naming the input it was given to. A NumPy ``float32`` is read the same way,
as the float it holds, so no step, sponge or waveform is computed in
``float32`` for it.
"""

from __future__ import annotations

import inspect
import re
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest

from phonometry.simulation import (
    FDTD2D,
    STEEL,
    CWSource,
    ElasticFDTD2D,
    ElasticRecording,
    ElasticRun,
    ExplosionSource,
    FDTDBoundaries,
    FDTDRecording,
    FDTDRun,
    ForceSource,
    GaussianPulse,
    Material,
    PlaneWaveSource,
    SignalSource,
    elastic_fdtd_simulation,
    fdtd_simulation,
    scholte_speed,
)
from phonometry.simulation._remote.wire import encode_arguments
from phonometry.simulation.fdtd import ContourProbe
from phonometry.simulation.ntff import ContourPhasors, far_field_from_contour

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

#: A small grid, ``(ny, nx)``.
_NY, _NX = 16, 16

#: A case: its label ``owner(parameter=spelling)``, the call, and what the
#: refusal says.
Case = tuple[str, "Callable[[], object]", str]


def _complex_numbers(real: float) -> dict[str, object]:
    """The complex spellings of one number: a Python and a NumPy complex."""
    return {
        "python complex": complex(real, 1.0),
        "numpy complex": np.complex128(complex(real, 1.0)),
    }


def _complex_maps(real: float) -> dict[str, object]:
    """The complex spellings of a map: an array, and lists of each kind of number."""
    grid = np.full((_NY, _NX), complex(real, 1.0))
    return {
        "complex array": grid,
        "list of python complex": grid.tolist(),
        "list of numpy complex": [list(row) for row in grid],
        "complex objects": grid.astype(object),
    }


def _text_maps(real: float) -> dict[str, object]:
    """The text spellings of a map: a list of texts and an array of them."""
    return {
        "list of texts": [[str(real)] * _NX for _ in range(_NY)],
        "array of texts": np.full((_NY, _NX), str(real)),
    }


def _spellings(real: float, *, is_map: bool) -> dict[str, tuple[object, str]]:
    """Each wrong spelling of a number or a map, with the word its refusal holds."""
    found = {
        spelling: (value, "real|number")
        for spelling, value in _complex_numbers(real).items()
    }
    found["text"] = (str(real), "number")
    if is_map:
        found |= {
            spelling: (value, "real") for spelling, value in _complex_maps(real).items()
        }
        found |= {
            spelling: (value, "numbers, not text")
            for spelling, value in _text_maps(real).items()
        }
    return found


def _pulse() -> GaussianPulse:
    return GaussianPulse(ix=8, iy=8, half_width_s=1e-4)


def _blast() -> ExplosionSource:
    return ExplosionSource(ix=8, iy=8, waveform=lambda t: 0.0)


#: The real number each real input is handed as, when it is right.
_REALS = {
    "c": 343.0,
    "rho": 1.2,
    "c_p": 2000.0,
    "c_s": 1000.0,
    "damping": 0.0,
    "dx": 0.01,
    "cfl": 0.5,
    "duration_s": 1e-3,
    "absorbing_layer_reflection": 1e-4,
}

#: The inputs that take a map as well as one number.
_MAPS = frozenset({"c", "rho", "c_p", "c_s", "damping"})


#: What each owner of real inputs is inspected as, by the label its cases carry.
_OWNERS: dict[str, Callable[..., object]] = {
    "FDTD2D": FDTD2D,
    "FDTDRun": FDTDRun,
    "ElasticFDTD2D": ElasticFDTD2D,
    "ElasticRun": ElasticRun,
    "FDTDBoundaries": FDTDBoundaries,
    "GaussianPulse": GaussianPulse,
    "CWSource": CWSource,
    "SignalSource": SignalSource,
    "PlaneWaveSource": PlaneWaveSource,
    "ExplosionSource": ExplosionSource,
    "ForceSource": ForceSource,
    "Material": Material,
    "add_plane_wave": FDTD2D.add_plane_wave,
    "scholte_speed": scholte_speed,
    "from_regions": ElasticFDTD2D.from_regions,
    "GaussianPulse.value": GaussianPulse.value,
    "CWSource.value": CWSource.value,
    "SignalSource.value": SignalSource.value,
    "ContourProbe": ContourProbe,
    "add_contour_probe": FDTD2D.add_contour_probe,
    "phasors": ContourProbe.phasors,
    "ContourPhasors": ContourPhasors,
    "far_field_from_contour": far_field_from_contour,
}

#: An annotation that holds a real number, alone or in a map, a sequence or
#: a material's triple.
_HOLDS_A_REAL = re.compile(
    r"\bfloat\b|ArrayLike|Field2D|NDArray\[np\.(float64|complex128)\]"
)

#: Inputs whose annotation names a number they do not hold: a waveform is
#: a function of time, and an obstacle is a mask of flags, which its own
#: check holds to booleans.
_NOT_A_NUMBER = frozenset({"waveform", "obstacle_mask"})


def _real_parameters(owner: str) -> list[str]:
    """The parameters of *owner* that take a real number, in any form."""
    return [
        name
        for name, parameter in inspect.signature(_OWNERS[owner]).parameters.items()
        if name not in _NOT_A_NUMBER and _HOLDS_A_REAL.search(str(parameter.annotation))
    ]


def _engine_cases() -> Iterator[Case]:
    """Each real input of the two engines and the two runs."""
    acoustic: dict[str, object] = {"c": 343.0, "dx": 0.01, "shape": (_NY, _NX)}
    elastic: dict[str, object] = {
        "c_p": 2000.0,
        "c_s": 1000.0,
        "dx": 0.01,
        "rho": 1000.0,
        "shape": (_NY, _NX),
    }
    owners: list[tuple[str, dict[str, object], Callable[..., object]]] = [
        ("FDTD2D", acoustic, lambda **kw: FDTD2D(**kw)),
        (
            "FDTDRun",
            {**acoustic, "duration_s": 1e-3, "sources": [_pulse()]},
            lambda **kw: FDTDRun(**kw),
        ),
        ("ElasticFDTD2D", elastic, lambda **kw: ElasticFDTD2D(**kw)),
        (
            "ElasticRun",
            {**elastic, "duration_s": 1e-3, "sources": [_blast()]},
            lambda **kw: ElasticRun(**kw),
        ),
    ]
    for owner, base, build in owners:
        for name in _real_parameters(owner):
            if name not in _REALS:
                continue
            spellings = _spellings(_REALS[name], is_map=name in _MAPS)
            for spelling, (value, said) in spellings.items():
                kwargs = {**base, name: value}
                if name in {"c", "c_p"} and spelling not in {
                    "python complex",
                    "numpy complex",
                    "text",
                }:
                    # A map names its grid; a shape beside it must agree.
                    kwargs.pop("shape")
                yield (
                    f"{owner}({name}={spelling})",
                    lambda kwargs=kwargs, build=build: build(**kwargs),
                    rf"'?{name}'? must be (?:[^,]*, )?.*(?:{said})",
                )
    # A text alone is a termination's name to the boundaries, and a name
    # that is none is a ValueError there; a profile of texts is no number.
    for spelling, value in {
        **_complex_numbers(415.0),
        "list of numpy complex": [np.complex128(415.0 + 1j)] * _NY,
        "list of texts": ["415.0"] * _NY,
    }.items():
        yield (
            f"FDTD2D(edge_impedance={spelling})",
            lambda value=value: FDTD2D(
                c=343.0, dx=0.01, shape=(_NY, _NX), edge_impedance={"left": value}
            ),
            "impedance for side 'left' must be a real number",
        )
        yield (
            f"FDTDBoundaries(sides={spelling})",
            lambda value=value: FDTDBoundaries(sides={"left": value}),
            "impedance for side 'left' must be a real number",
        )


def _record_cases() -> Iterator[Case]:
    """Each number of the sources, the material and a material's triple."""
    records: list[
        tuple[str, Callable[..., object], dict[str, object], dict[str, float]]
    ] = [
        (
            "GaussianPulse",
            lambda **kw: GaussianPulse(**kw),
            {"ix": 8, "iy": 8, "half_width_s": 1e-4},
            {"half_width_s": 1e-4, "t0": 1e-3, "amplitude": 1.0},
        ),
        (
            "CWSource",
            lambda **kw: CWSource(**kw),
            {"ix": 8, "iy": 8, "frequency": 1000.0},
            {"frequency": 1000.0, "amplitude": 1.0, "ramp_cycles": 3.0},
        ),
        (
            "SignalSource",
            lambda **kw: SignalSource(**kw),
            {"ix": 8, "iy": 8, "samples": np.zeros(8), "fs": 48000.0},
            {"fs": 48000.0, "amplitude": 1.0},
        ),
        (
            "PlaneWaveSource",
            lambda **kw: PlaneWaveSource(**kw),
            {"direction": "right", "waveform": lambda t: 0.0},
            {"amplitude": 1.0},
        ),
        (
            "ExplosionSource",
            lambda **kw: ExplosionSource(**kw),
            {"ix": 8, "iy": 8, "waveform": lambda t: 0.0},
            {"amplitude": 1.0},
        ),
        (
            "ForceSource",
            lambda **kw: ForceSource(**kw),
            {"ix": 8, "iy": 8, "direction": "x", "waveform": lambda t: 0.0},
            {"amplitude": 1.0},
        ),
        (
            "Material",
            lambda **kw: Material(**kw),
            {"c_p": 2000.0, "c_s": 1000.0, "rho": 1000.0},
            {"c_p": 2000.0, "c_s": 1000.0, "rho": 1000.0},
        ),
        (
            "add_plane_wave",
            lambda **kw: FDTD2D(c=343.0, dx=0.01, shape=(_NY, _NX)).add_plane_wave(
                "right", **kw
            ),
            {"center_m": 0.05, "half_width_m": 0.02},
            {
                "center_m": 0.05,
                "half_width_m": 0.02,
                "amplitude": 1.0,
                "wavelength_m": 0.04,
            },
        ),
    ]
    for owner, build, base, reals in records:
        for name, real in reals.items():
            for spelling, (value, said) in _spellings(real, is_map=False).items():
                kwargs = {**base, name: value}
                yield (
                    f"{owner}({name}={spelling})",
                    lambda kwargs=kwargs, build=build: build(**kwargs),
                    rf"'?{name}'? must be .*(?:{said})",
                )
    for spelling, samples in {
        "complex array": np.zeros(8) + 1j,
        "list of python complex": [1j] * 8,
        "list of numpy complex": [np.complex128(1j)] * 8,
        "list of texts": ["0.0"] * 8,
        "array of texts": np.array(["0.0"] * 8),
    }.items():
        yield (
            f"SignalSource(samples={spelling})",
            lambda samples=samples: SignalSource(
                ix=8, iy=8, samples=samples, fs=48000.0
            ),
            "samples must be (real|numbers)",
        )
    yield from _triple_cases()


def _triple_cases() -> Iterator[Case]:
    """A ``(c_p, c_s, rho)`` triple, read as a material is."""
    fluid = (343.0, 0.0, 1.2)
    mask = np.zeros((_NY, _NX), dtype=bool)
    mask[8:, :] = True
    for index, member in enumerate(("c_p", "c_s", "rho")):
        for spelling, (value, said) in _spellings(fluid[index], is_map=False).items():
            triple: list[object] = list(fluid)
            triple[index] = value
            medium = tuple(triple)
            label = f"{member} {spelling}"
            match = rf"'?{member}'? must be .*(?:{said})"
            yield (
                f"scholte_speed(fluid={label})",
                lambda medium=medium: scholte_speed(medium, STEEL),  # type: ignore[arg-type]
                match,
            )
            yield (
                f"scholte_speed(solid={label})",
                lambda medium=medium: scholte_speed((343.0, 0.0, 1.2), medium),  # type: ignore[arg-type]
                match,
            )
            yield (
                f"from_regions(background={label})",
                lambda medium=medium: ElasticFDTD2D.from_regions(
                    (_NY, _NX),
                    0.01,
                    background=medium,  # type: ignore[arg-type]
                ),
                match,
            )
            yield (
                f"from_regions(regions={label})",
                lambda medium=medium: ElasticFDTD2D.from_regions(
                    (_NY, _NX),
                    0.01,
                    background=STEEL,
                    regions=[(mask, medium)],  # type: ignore[list-item]
                ),
                match,
            )
    for spelling, (value, said) in _spellings(0.01, is_map=False).items():
        yield (
            f"from_regions(dx={spelling})",
            lambda value=value: ElasticFDTD2D.from_regions(
                (_NY, _NX),
                value,  # type: ignore[arg-type]
                background=STEEL,
            ),
            rf"'?dx'? must be .*(?:{said})",
        )
    # The options from_regions hands the engine, each refused as the engine
    # refuses it.
    for name in ("cfl", "absorbing_layer_reflection", "damping"):
        spellings = _spellings(_REALS[name], is_map=name in _MAPS)
        for spelling, (value, said) in spellings.items():
            yield (
                f"from_regions({name}={spelling})",
                lambda name=name, value=value: ElasticFDTD2D.from_regions(
                    (_NY, _NX),
                    0.01,
                    background=STEEL,
                    absorbing_layer_cells=2,
                    **{name: value},
                ),
                rf"'?{name}'? must be .*(?:{said})",
            )


def _time_cases() -> Iterator[Case]:
    """The time each point source's waveform is asked for, ``value(t)``."""
    sources: dict[str, object] = {
        "GaussianPulse.value": GaussianPulse(ix=8, iy=8, half_width_s=1e-4),
        "CWSource.value": CWSource(ix=8, iy=8, frequency=1000.0),
        "SignalSource.value": SignalSource(ix=8, iy=8, samples=np.ones(8), fs=48000.0),
    }
    #: What is no time at all: nothing, and a buffer NumPy reads as an array.
    not_numbers: dict[str, tuple[object, str]] = {
        "None": (None, "real number"),
        "bytearray": (bytearray(b"1"), "real number"),
    }
    for owner, source in sources.items():
        spellings = _spellings(5e-5, is_map=False) | not_numbers
        for spelling, (value, said) in spellings.items():
            yield (
                f"{owner}(t={spelling})",
                lambda source=source, value=value: source.value(value),  # type: ignore[attr-defined]
                rf"'?t'? must be .*(?:{said})",
            )


_POSITIONS = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
_NORMALS = np.array([[0.0, -1.0], [1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]])


def _contour(**changes: object) -> ContourPhasors:
    fields: dict[str, object] = {
        "frequency": 1000.0,
        "positions": _POSITIONS,
        "normals": _NORMALS,
        "pressure": np.ones(4, dtype=complex),
        "normal_velocity": np.ones(4, dtype=complex),
        "segment": 0.1,
        **changes,
    }
    return ContourPhasors(**fields)  # type: ignore[arg-type]


def _probe(frequencies: object = (1000.0,)) -> ContourProbe:
    return ContourProbe(
        FDTD2D(c=343.0, dx=0.01, shape=(_NY, _NX)),
        3,
        10,
        3,
        10,
        frequencies,  # type: ignore[arg-type]
    )


def _contour_cases() -> Iterator[Case]:
    """The contour probe, the phasors of a contour and the far-field transform."""
    frequencies = {
        **_complex_numbers(1000.0),
        "list of python complex": [1000.0 + 1j],
        "list of numpy complex": [np.complex128(1000.0 + 1j)],
        "text": "1000.0",
        "list of texts": ["1000.0"],
    }
    for spelling, value in frequencies.items():
        yield (
            f"ContourProbe(frequencies={spelling})",
            lambda value=value: _probe(value),
            "frequencies must be (real|numbers)",
        )
        yield (
            f"add_contour_probe(frequencies={spelling})",
            lambda value=value: FDTD2D(
                c=343.0, dx=0.01, shape=(_NY, _NX)
            ).add_contour_probe(
                3,
                10,
                3,
                10,
                frequencies=value,  # type: ignore[arg-type]
            ),
            "frequencies must be (real|numbers)",
        )
    for spelling, (value, said) in _spellings(1000.0, is_map=False).items():
        yield (
            f"phasors(frequency={spelling})",
            lambda value=value: _probe().phasors(value),  # type: ignore[arg-type]
            rf"'?frequency'? must be .*(?:{said})",
        )
    for name, real in (("frequency", 1000.0), ("segment", 0.1)):
        for spelling, (value, said) in _spellings(real, is_map=False).items():
            yield (
                f"ContourPhasors({name}={spelling})",
                lambda name=name, value=value: _contour(**{name: value}),
                rf"'?{name}'? must be .*(?:{said})",
            )
    for name, geometry in (("positions", _POSITIONS), ("normals", _NORMALS)):
        for spelling, value in {
            "complex array": geometry + 1j,
            "list of numpy complex": [
                [np.complex128(x + 1j) for x in row] for row in geometry
            ],
            "list of texts": [[str(x) for x in row] for row in geometry],
        }.items():
            yield (
                f"ContourPhasors({name}={spelling})",
                lambda name=name, value=value: _contour(**{name: value}),
                rf"{name} must be (real|numbers)",
            )
    for name in ("pressure", "normal_velocity"):
        yield (
            f"ContourPhasors({name}=list of texts)",
            lambda name=name: _contour(**{name: ["1"] * 4}),
            rf"{name} must be numbers, not text",
        )
    for spelling, angles in {
        "complex array": np.array([0.0, 90.0]) + 1j,
        "list of numpy complex": [np.complex128(1j)],
        "numpy complex": np.complex128(1j),
        "list of texts": ["0.0", "90.0"],
        "text": "90.0",
    }.items():
        yield (
            f"far_field_from_contour(angles_deg={spelling})",
            lambda angles=angles: far_field_from_contour(_contour(), angles),
            "angles_deg must be (real|numbers)",
        )
    for spelling, (value, said) in _spellings(10.0, is_map=False).items():
        yield (
            f"far_field_from_contour(distance={spelling})",
            lambda value=value: far_field_from_contour(
                _contour(),
                [0.0],
                distance=value,  # type: ignore[arg-type]
            ),
            rf"'?distance'? must be .*(?:{said})",
        )
    for spelling, origin in {
        "numpy complex": (np.complex128(0.5 + 1j), 0.5),
        "text": ("0.5", 0.5),
    }.items():
        yield (
            f"far_field_from_contour(origin={spelling})",
            lambda origin=origin: far_field_from_contour(
                _contour(),
                [0.0],
                origin=origin,  # type: ignore[arg-type]
            ),
            "origin must be (real|numbers)",
        )


_CASES = [*_engine_cases(), *_record_cases(), *_contour_cases(), *_time_cases()]


@pytest.mark.parametrize(
    ("build", "match"),
    [pytest.param(build, match, id=label) for label, build, match in _CASES],
)
def test_a_complex_value_or_a_text_where_a_real_number_belongs_is_refused(
    build: Callable[[], object], match: str
) -> None:
    """A complex value and a text are the wrong type, refused by the input's name.

    Before, the elastic engine, both runs, every source, the material and
    the contour took the real part of most of these, the scalars of a NumPy
    complex number and the maps of a complex array, and every map took a
    text as the number it spells.
    """
    with pytest.raises(TypeError, match=match):
        build()


def test_every_real_input_is_held_to_both_refusals() -> None:
    """Each real input of every owner has a case, a complex one and a text one among them.

    An input added to an engine, a source, a material or the contour
    transform without its cases fails here, rather than taking the real
    part of a complex number nobody refused.
    """
    labels = [label for label, _, _ in _CASES]
    assert len(labels) == len(set(labels))
    spelt: dict[tuple[str, str], set[str]] = {}
    for label in labels:
        owner, rest = label.split("(", 1)
        name, spelling = rest.rstrip(")").split("=", 1)
        spelt.setdefault((owner, name), set()).add(spelling)
    missing = [
        f"{owner}({name})"
        for owner in _OWNERS
        for name in _real_parameters(owner)
        if not any("complex" in spelling for spelling in spelt.get((owner, name), ()))
        and (owner, name)
        not in {("ContourPhasors", "pressure"), ("ContourPhasors", "normal_velocity")}
    ]
    untexted = [
        f"{owner}({name})"
        for owner in _OWNERS
        for name in _real_parameters(owner)
        if not any("text" in spelling for spelling in spelt.get((owner, name), ()))
    ]
    assert missing == []
    assert untexted == []


#: The samples a waveform may wrongly return, by how a caller writes them.
_WRONG_SAMPLES: dict[str, object] = {
    "python complex": 1.0 + 1.0j,
    "numpy complex": np.complex128(1.0 + 1.0j),
    "complex64": np.complex64(1.0 + 1.0j),
    "zero-dimensional complex array": np.asarray(1.0 + 1.0j),
    "text": "1.0",
    "None": None,
    "list of one number": [1.0],
    "array of two numbers": np.array([1.0, 2.0]),
    "bytearray": bytearray(b"1"),
}


def _step_plane_wave(sample: object) -> None:
    sim = FDTD2D(c=343.0, dx=0.01, shape=(_NY, _NX), absorbing_layer_cells=4)
    sim.add_source(PlaneWaveSource(direction="right", waveform=lambda t: sample))
    sim.step()


def _step_explosion(sample: object) -> None:
    sim = ElasticFDTD2D(c_p=2000.0, c_s=1000.0, dx=0.01, rho=1000.0, shape=(_NY, _NX))
    sim.add_source(ExplosionSource(ix=8, iy=8, waveform=lambda t: sample))
    sim.step()


def _step_force(sample: object) -> None:
    sim = ElasticFDTD2D(c_p=2000.0, c_s=1000.0, dx=0.01, rho=1000.0, shape=(_NY, _NX))
    sim.add_source(ForceSource(ix=8, iy=8, direction="y", waveform=lambda t: sample))
    sim.step()


def _run_explosion(sample: object) -> None:
    from phonometry.simulation import elastic_fdtd_simulation

    blast = ExplosionSource(ix=8, iy=8, waveform=lambda t: sample)
    elastic_fdtd_simulation(
        ElasticRun(
            c_p=2000.0,
            c_s=1000.0,
            dx=0.01,
            rho=1000.0,
            shape=(_NY, _NX),
            duration_s=1e-5,
            sources=[blast],
        )
    )


_STEPPERS: dict[str, Callable[[object], None]] = {
    "PlaneWaveSource": _step_plane_wave,
    "ExplosionSource": _step_explosion,
    "ForceSource": _step_force,
    "elastic_fdtd_simulation": _run_explosion,
}


@pytest.mark.parametrize("spelling", sorted(_WRONG_SAMPLES))
@pytest.mark.parametrize("stepper", sorted(_STEPPERS))
def test_a_waveform_that_returns_no_real_number_is_refused_by_name(
    stepper: str, spelling: str
) -> None:
    """A sample that is not one real number stops the step, naming the waveform.

    The engines add each sample into their real fields: the elastic engine
    stepped the real part of a complex sample with no more than a
    ``ComplexWarning``, and the plane wave of the acoustic engine failed with
    NumPy's casting error, which names nothing the caller wrote. ``None``, a
    list, an array or a ``bytearray`` failed with a ``TypeError`` or a
    ``ValueError`` of NumPy's or Python's that named nothing either, or
    broadcast an array into the field.
    """
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error", np.exceptions.ComplexWarning)
        with pytest.raises(TypeError, match=r"waveform of .* must return a real"):
            _STEPPERS[stepper](_WRONG_SAMPLES[spelling])


#: Whether a long double holds numbers a float does not: it does on x86-64
#: Linux (80 bits), and is a float on Windows and on macOS on Apple silicon.
_WIDE_LONG_DOUBLE = bool(np.finfo(np.longdouble).max > np.finfo(np.float64).max)

_ONLY_WITH_A_WIDE_LONG_DOUBLE = pytest.mark.skipif(
    not _WIDE_LONG_DOUBLE, reason="a long double is a float on this platform"
)

#: Finite numbers of the right type that no float holds, by how a caller
#: writes them, each built when it is used: a long double is one only where
#: it is wider than a float. ``float()`` refuses the integer with an
#: ``OverflowError``, and reads the others as an infinity.
_TOO_LARGE: dict[str, Callable[[], object]] = {
    "python integer": lambda: 10**400,
    "Decimal": lambda: Decimal("1e400"),
    "negative Decimal": lambda: Decimal("-1e400"),
    "long double": lambda: np.longdouble("1e400"),
}

_TOO_LARGE_SPELLINGS = [
    pytest.param(
        spelling,
        marks=_ONLY_WITH_A_WIDE_LONG_DOUBLE if "long double" in spelling else (),
    )
    for spelling in sorted(_TOO_LARGE)
]


@pytest.mark.parametrize("spelling", _TOO_LARGE_SPELLINGS)
@pytest.mark.parametrize("stepper", sorted(_STEPPERS))
def test_a_waveform_sample_no_float_holds_is_refused_by_name(
    stepper: str, spelling: str
) -> None:
    """A number beyond a float's range stops the step, naming the waveform.

    A Python integer passed the check as surely one real number, being an
    ``int``, and failed in the field update with Python's ``OverflowError``,
    which names nothing the caller wrote. A long double passed it as a NumPy
    float, and a ``Decimal`` was read by ``float()`` as an infinity, so both
    stepped an infinite sample into the field. Each is a value of the right
    type, refused with ``ValueError`` as :func:`require_real` refuses it.
    """
    sample = _TOO_LARGE[spelling]()
    with pytest.raises(ValueError, match=r"waveform of .* must return a real"):
        _STEPPERS[stepper](sample)


@pytest.mark.parametrize("spelling", _TOO_LARGE_SPELLINGS)
@pytest.mark.parametrize(
    "source",
    [
        GaussianPulse(ix=8, iy=8, half_width_s=1e-4),
        CWSource(ix=8, iy=8, frequency=1000.0),
        SignalSource(ix=8, iy=8, samples=np.ones(8), fs=48000.0),
    ],
    ids=type,
)
def test_a_time_no_float_holds_is_refused_by_name(
    source: GaussianPulse | CWSource | SignalSource, spelling: str
) -> None:
    """``value(t)`` refuses a number beyond a float's range by the name ``t``."""
    t = _TOO_LARGE[spelling]()
    with pytest.raises(ValueError, match=r"t must be one real number"):
        source.value(t)  # type: ignore[arg-type]


@_ONLY_WITH_A_WIDE_LONG_DOUBLE
def test_a_long_double_is_read_as_the_float_it_rounds_to() -> None:
    """A long double sample or time is the float it rounds to, as a Python integer is.

    It passed as it was, being a NumPy float, so a sample the engine scaled
    before adding it into a float field was scaled with the long double's
    extra digits, and one beyond a float's range became an infinity there.
    """
    from phonometry.simulation import fdtd

    value = np.longdouble(1) / np.longdouble(3)
    source = _blast()
    for read in (fdtd._real_sample(value, source), fdtd._real_time(value)):  # type: ignore[arg-type]
        assert type(read) is float
        assert read == float(value)


#: What a waveform returns, and what an engine hands ``value(t)``, when it is
#: right: a NumPy scalar of another width among them. A Python integer is
#: not here: it has no width, so it is read as the float it rounds to.
_FAST_SAMPLES: dict[str, object] = {
    "python float": 0.5,
    "float64": np.float64(0.5),
    "float32": np.float32(0.5),
    "int64": np.int64(1),
}


@pytest.mark.parametrize("spelling", sorted(_FAST_SAMPLES))
def test_a_real_number_of_any_numpy_width_passes_without_the_slow_check(
    spelling: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A NumPy float32 or int64 sample or time is handed back as it is, unchecked.

    The engines check every sample a waveform returns, each step, so the
    check of what is surely one real number is one ``isinstance``. It named
    only ``float`` and ``int``, so a ``np.float32`` or a ``np.int64`` went
    through the full check, some twenty times slower, though it is as
    surely one real number as a ``np.float64``.
    """
    from phonometry.simulation import fdtd

    def slow(*args: object, **kwargs: object) -> None:
        msg = "the slow check was reached"
        raise AssertionError(msg)

    source = _blast()
    for name in ("require_real", "refuse_complex", "refuse_text", "_real_numbers"):
        monkeypatch.setattr(fdtd, name, slow, raising=False)
    value = _FAST_SAMPLES[spelling]
    assert fdtd._real_sample(value, source) is value  # type: ignore[arg-type]
    assert fdtd._real_time(value) is value  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [0, 1, -3, True, 2**53 + 1])
def test_a_python_integer_is_read_as_its_float_without_the_slow_check(
    value: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A Python integer within a float's range steps as the float it rounds to.

    The engine adds it into float fields, where it would round the same way,
    so the sample and the time are the same number; reading it is one
    ``float``, not the full check.
    """
    from phonometry.simulation import fdtd

    def slow(*args: object, **kwargs: object) -> None:
        msg = "the slow check was reached"
        raise AssertionError(msg)

    source = _blast()
    for name in ("require_real", "refuse_complex", "refuse_text", "_real_numbers"):
        monkeypatch.setattr(fdtd, name, slow, raising=False)
    for read in (fdtd._real_sample(value, source), fdtd._real_time(value)):
        assert type(read) is float
        assert read == float(value)


class _Waveform:
    """A tone that returns *wrong* instead of its sample while it is refused."""

    def __init__(self, wrong: object = 1.0 + 1.0j) -> None:
        self.wrong = wrong
        self.refused = False

    def __call__(self, t: float) -> object:
        if self.refused:
            return self.wrong
        return float(np.sin(2.0 * np.pi * 2000.0 * t))


def _engine_driven_by(kind: str, waveform: _Waveform) -> FDTD2D | ElasticFDTD2D:
    """A small engine one of whose sources is driven by *waveform*."""
    if kind == "PlaneWaveSource":
        sim = FDTD2D(c=343.0, dx=0.01, shape=(_NY, _NX), absorbing_layer_cells=4)
        sim.add_source(PlaneWaveSource(direction="right", waveform=waveform))
        return sim
    solid = ElasticFDTD2D(c_p=2000.0, c_s=1000.0, dx=0.01, rho=1000.0, shape=(_NY, _NX))
    if kind == "ForceSource":
        solid.add_source(ForceSource(ix=8, iy=8, direction="y", waveform=waveform))
        return solid
    if kind == "ExplosionSource after a ForceSource":
        solid.add_source(ForceSource(ix=5, iy=5, direction="x", waveform=_Waveform()))
    solid.add_source(ExplosionSource(ix=8, iy=8, waveform=waveform))
    return solid


def _fields(sim: FDTD2D | ElasticFDTD2D) -> dict[str, np.ndarray]:
    """A copy of every field the engine steps, by name."""
    names = (
        ("p", "vx", "vy")
        if isinstance(sim, FDTD2D)
        else ("vx", "vy", "txx", "tyy", "txy")
    )
    return {name: np.array(getattr(sim, name), copy=True) for name in names}


@pytest.mark.parametrize(
    "kind",
    [
        "PlaneWaveSource",
        "ForceSource",
        "ExplosionSource",
        "ExplosionSource after a ForceSource",
    ],
)
def test_a_refused_sample_leaves_the_engine_as_it_was(kind: str) -> None:
    """A step whose waveform returns no real number changes no field and no count.

    The engines sampled a plane wave, a force and an explosion where they
    injected it, after the step had already advanced the velocity, the
    pressure or the stresses, so the refusal left the fields one step on and
    the step count behind them: a caller that caught it and stepped again
    stepped the same instant twice. The step now samples every waveform
    before it moves a field, and a caller that steps again once the
    waveform is right steps as an engine that was never refused.
    """
    waveform = _Waveform()
    sim = _engine_driven_by(kind, waveform)
    twin = _engine_driven_by(kind, _Waveform())
    for _ in range(5):
        sim.step()
        twin.step()
    before = _fields(sim)
    waveform.refused = True
    with pytest.raises(TypeError, match=r"waveform of .* must return a real"):
        sim.step()
    assert sim.n == 5
    after = _fields(sim)
    assert [
        name for name in before if not np.array_equal(after[name], before[name])
    ] == []
    waveform.refused = False
    sim.step()
    twin.step()
    stepped, never_refused = _fields(sim), _fields(twin)
    assert [
        name
        for name in stepped
        if not np.array_equal(stepped[name], never_refused[name])
    ] == []


class _SecondSampleWrong:
    """A plane wave's waveform whose pressure sample is right and whose velocity sample is not.

    A step asks the waveform for the pressure line's sample, then for the
    velocity face's, so every second call returns a complex number.
    """

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, t: float) -> object:
        self.calls += 1
        return 0.25 if self.calls % 2 else 1.0 + 1.0j


def test_a_refused_velocity_sample_leaves_the_engine_as_it_was() -> None:
    """The velocity face's sample is checked on its own, before any field moves.

    Every other case hands both samples the same wrong value, so the
    pressure line's check refuses it first, and a step that checked only
    that sample would pass them all.
    """
    sim = FDTD2D(c=343.0, dx=0.01, shape=(_NY, _NX), absorbing_layer_cells=4)
    sim.add_source(PlaneWaveSource(direction="right", waveform=_SecondSampleWrong()))
    before = _fields(sim)
    with pytest.raises(TypeError, match=r"waveform of .* must return a real"):
        sim.step()
    assert sim.n == 0
    after = _fields(sim)
    assert [
        name for name in before if not np.array_equal(after[name], before[name])
    ] == []


def _tone(t: float) -> float:
    """A 2 kHz tone, the waveform of the plane wave a step adds."""
    return float(np.sin(2.0 * np.pi * 2000.0 * t))


#: The plane wave a waveform adds to its engine while a step runs.
_ADDED = PlaneWaveSource(direction="down", waveform=_tone)


@dataclass(frozen=True, kw_only=True)
class _PulseThatAddsAPlaneWave(GaussianPulse):
    """A pulse whose waveform adds a plane wave to its engine the first time it is asked."""

    engine: FDTD2D

    def value(self, t: float) -> float:
        if _ADDED not in self.engine._plane_sources:
            self.engine.add_source(_ADDED)
        return super().value(t)


class _ToneThatAddsAPlaneWave:
    """A plane wave's waveform that adds another plane wave the first time it is asked."""

    def __init__(self, engine: FDTD2D) -> None:
        self.engine = engine

    def __call__(self, t: float) -> float:
        if _ADDED not in self.engine._plane_sources:
            self.engine.add_source(_ADDED)
        return _tone(t)


def _engine_whose_waveform_adds(adder: str) -> FDTD2D:
    """A small engine one of whose waveforms adds :data:`_ADDED` while it steps."""
    sim = FDTD2D(c=343.0, dx=0.01, shape=(_NY, _NX), absorbing_layer_cells=4)
    if adder == "point source":
        sim.add_source(
            _PulseThatAddsAPlaneWave(ix=8, iy=8, half_width_s=1e-4, engine=sim)
        )
    else:
        sim.add_source(
            PlaneWaveSource(direction="right", waveform=_ToneThatAddsAPlaneWave(sim))
        )
    return sim


def _engine_with_the_same_sources(adder: str) -> FDTD2D:
    """The same engine with waveforms that add nothing."""
    sim = FDTD2D(c=343.0, dx=0.01, shape=(_NY, _NX), absorbing_layer_cells=4)
    if adder == "point source":
        sim.add_source(GaussianPulse(ix=8, iy=8, half_width_s=1e-4))
    else:
        sim.add_source(PlaneWaveSource(direction="right", waveform=_tone))
    return sim


@pytest.mark.parametrize("adder", ["point source", "plane wave"])
def test_a_plane_wave_added_while_a_step_runs_enters_on_the_next_step(
    adder: str,
) -> None:
    """A step injects the plane waves it began with, so one added during it waits a step.

    The step sampled every plane wave before it moved a field and then
    paired the samples with the plane waves the engine held by then, so a
    plane wave added by a point source's waveform, after the sampling and
    before the injection, stopped the step with ``zip``'s ``ValueError``
    once the pressure had moved and before the count did; one added by a
    plane wave's own waveform was sampled and injected in the step that
    added it. Either enters on the next step now, as one added between the
    two steps does.
    """
    sim = _engine_whose_waveform_adds(adder)
    twin = _engine_with_the_same_sources(adder)
    sim.step()
    twin.step()
    twin.add_source(_ADDED)
    for _ in range(3):
        sim.step()
        twin.step()
    stepped, added_between = _fields(sim), _fields(twin)
    assert sim.n == twin.n == 4
    assert [
        name
        for name in stepped
        if not np.array_equal(stepped[name], added_between[name])
    ] == []


#: A ``Decimal`` and a ``Fraction`` of a number written in decimal, each the
#: same number as the float literal: both read back as the float nearest to
#: the digits, as the literal does.
_EXACT_SPELLINGS: dict[str, Callable[[float], object]] = {
    "Decimal": lambda real: Decimal(repr(real)),
    "Fraction": lambda real: Fraction(repr(real)),
}

#: The samples of a :class:`SignalSource` in the cases below.
_SAMPLES = np.hanning(8)


def _drive() -> GaussianPulse:
    """The pulse whose ``value`` drives a plane wave or an elastic source here."""
    return GaussianPulse(ix=0, iy=0, half_width_s=4e-5)


def _acoustic_run(**fields: object) -> FDTDRun:
    """A small acoustic run with one probe, *fields* written over its own."""
    given: dict[str, object] = {
        "c": 343.0,
        "dx": 0.01,
        "shape": (_NY, _NX),
        "duration_s": 2e-4,
        "sources": [_pulse()],
        "recording": FDTDRecording(probes=[(4, 4)]),
        **fields,
    }
    return FDTDRun(**given)  # type: ignore[arg-type]


def _elastic_run(**fields: object) -> ElasticRun:
    """A small elastic run with one probe, *fields* written over its own."""
    given: dict[str, object] = {
        "c_p": 2000.0,
        "c_s": 1000.0,
        "rho": 1000.0,
        "dx": 0.01,
        "shape": (_NY, _NX),
        "duration_s": 5e-5,
        "sources": [ExplosionSource(ix=8, iy=8, waveform=_drive().value)],
        "recording": ElasticRecording(probes=[(4, 4)]),
        **fields,
    }
    return ElasticRun(**given)  # type: ignore[arg-type]


#: Each real input of a run and of a source, by ``owner(input)``: the float
#: it is written as when it is right, and the run built around it.
_RUN_INPUTS: dict[str, tuple[float, Callable[[object], FDTDRun | ElasticRun]]] = {
    "FDTDRun(c)": (343.0, lambda v: _acoustic_run(c=v)),
    "FDTDRun(dx)": (0.01, lambda v: _acoustic_run(dx=v)),
    "FDTDRun(duration_s)": (2e-4, lambda v: _acoustic_run(duration_s=v)),
    "FDTDRun(rho)": (1.2, lambda v: _acoustic_run(rho=v)),
    "FDTDRun(cfl)": (0.5, lambda v: _acoustic_run(cfl=v)),
    "FDTDRun(damping)": (10.0, lambda v: _acoustic_run(damping=v)),
    "FDTDBoundaries(sides)": (
        415.0,
        lambda v: _acoustic_run(boundaries=FDTDBoundaries(sides={"left": v})),  # type: ignore[dict-item]
    ),
    "GaussianPulse(half_width_s)": (
        1e-4,
        lambda v: _acoustic_run(sources=[GaussianPulse(ix=8, iy=8, half_width_s=v)]),  # type: ignore[arg-type]
    ),
    "GaussianPulse(t0)": (
        3e-4,
        lambda v: _acoustic_run(
            sources=[GaussianPulse(ix=8, iy=8, half_width_s=1e-4, t0=v)]  # type: ignore[arg-type]
        ),
    ),
    "GaussianPulse(amplitude)": (
        0.5,
        lambda v: _acoustic_run(
            sources=[GaussianPulse(ix=8, iy=8, half_width_s=1e-4, amplitude=v)]  # type: ignore[arg-type]
        ),
    ),
    "CWSource(frequency)": (
        2000.0,
        lambda v: _acoustic_run(sources=[CWSource(ix=8, iy=8, frequency=v)]),  # type: ignore[arg-type]
    ),
    "CWSource(amplitude)": (
        0.5,
        lambda v: _acoustic_run(
            sources=[CWSource(ix=8, iy=8, frequency=2000.0, amplitude=v)]  # type: ignore[arg-type]
        ),
    ),
    "CWSource(ramp_cycles)": (
        2.0,
        lambda v: _acoustic_run(
            sources=[CWSource(ix=8, iy=8, frequency=2000.0, ramp_cycles=v)]  # type: ignore[arg-type]
        ),
    ),
    "SignalSource(fs)": (
        48000.0,
        lambda v: _acoustic_run(
            sources=[SignalSource(ix=8, iy=8, samples=_SAMPLES, fs=v)]  # type: ignore[arg-type]
        ),
    ),
    "SignalSource(amplitude)": (
        0.5,
        lambda v: _acoustic_run(
            sources=[
                SignalSource(ix=8, iy=8, samples=_SAMPLES, fs=48000.0, amplitude=v)  # type: ignore[arg-type]
            ]
        ),
    ),
    "PlaneWaveSource(amplitude)": (
        0.5,
        lambda v: _acoustic_run(
            sources=[
                PlaneWaveSource(direction="right", waveform=_drive().value, amplitude=v)  # type: ignore[arg-type]
            ]
        ),
    ),
    "ElasticRun(c_p)": (2000.0, lambda v: _elastic_run(c_p=v)),
    "ElasticRun(c_s)": (1000.0, lambda v: _elastic_run(c_s=v)),
    "ElasticRun(rho)": (1000.0, lambda v: _elastic_run(rho=v)),
    "ElasticRun(dx)": (0.01, lambda v: _elastic_run(dx=v)),
    "ElasticRun(duration_s)": (5e-5, lambda v: _elastic_run(duration_s=v)),
    "ElasticRun(cfl)": (0.5, lambda v: _elastic_run(cfl=v)),
    "ElasticRun(damping)": (10.0, lambda v: _elastic_run(damping=v)),
    "ExplosionSource(amplitude)": (
        0.5,
        lambda v: _elastic_run(
            sources=[ExplosionSource(ix=8, iy=8, waveform=_drive().value, amplitude=v)]  # type: ignore[arg-type]
        ),
    ),
    "ForceSource(amplitude)": (
        0.5,
        lambda v: _elastic_run(
            sources=[
                ForceSource(
                    ix=8,
                    iy=8,
                    direction="y",
                    waveform=_drive().value,
                    amplitude=v,  # type: ignore[arg-type]
                )
            ]
        ),
    ),
}


def _probe_histories(run: FDTDRun | ElasticRun) -> np.ndarray:
    """What *run* records at its probe, stepped on this machine."""
    if isinstance(run, FDTDRun):
        return fdtd_simulation(run).pressures
    return elastic_fdtd_simulation(run).signals


@pytest.mark.parametrize("spelling", sorted(_EXACT_SPELLINGS))
@pytest.mark.parametrize("case", sorted(_RUN_INPUTS))
def test_a_decimal_or_a_fraction_steps_as_the_float_it_reads_as(
    case: str, spelling: str
) -> None:
    """A run given a ``Decimal`` or a ``Fraction`` steps as the run given its float.

    A run checked such a number through ``float`` and built, then a
    ``Decimal`` on a source failed at the first step with Python's own
    ``unsupported operand type(s)``, and a ``Decimal`` or a ``Fraction``
    ``cfl`` or ``ramp_cycles`` failed when the run was built with NumPy's
    ``ufunc 'isfinite' not supported``, neither of which names the input.
    """
    real, build = _RUN_INPUTS[case]
    expected = _probe_histories(build(real))
    given = build(_EXACT_SPELLINGS[spelling](real))
    np.testing.assert_array_equal(_probe_histories(given), expected)


def _acoustic_engine(**options: object) -> FDTD2D:
    """A small acoustic engine with a sponge and one pulse, *options* over its own."""
    sim = FDTD2D(
        **{  # type: ignore[arg-type]
            "c": 343.0,
            "dx": 0.01,
            "shape": (_NY, _NX),
            "absorbing_layer_cells": 4,
            **options,
        }
    )
    sim.add_source(_pulse())
    return sim


def _elastic_engine(**options: object) -> ElasticFDTD2D:
    """A small elastic engine with a sponge and one explosion, *options* over its own."""
    sim = ElasticFDTD2D(
        **{  # type: ignore[arg-type]
            "c_p": 2000.0,
            "c_s": 1000.0,
            "rho": 1000.0,
            "dx": 0.01,
            "shape": (_NY, _NX),
            "absorbing_layer_cells": 4,
            **options,
        }
    )
    sim.add_source(ExplosionSource(ix=8, iy=8, waveform=_drive().value))
    return sim


def _plane_wave(**options: object) -> FDTD2D:
    """A small acoustic engine driven by :meth:`FDTD2D.add_plane_wave`."""
    sim = FDTD2D(c=343.0, dx=0.01, shape=(_NY, _NX), absorbing_layer_cells=4)
    given: dict[str, Any] = {"center_m": 0.08, "half_width_m": 0.03, **options}
    sim.add_plane_wave("right", **given)
    return sim


#: Each real input of an engine, by ``owner(input)``: the float it is
#: written as when it is right, and the engine built around it.
_ENGINE_INPUTS: dict[str, tuple[float, Callable[[object], FDTD2D | ElasticFDTD2D]]] = {
    "FDTD2D(c)": (343.0, lambda v: _acoustic_engine(c=v)),
    "FDTD2D(dx)": (0.01, lambda v: _acoustic_engine(dx=v)),
    "FDTD2D(rho)": (1.2, lambda v: _acoustic_engine(rho=v)),
    "FDTD2D(cfl)": (0.5, lambda v: _acoustic_engine(cfl=v)),
    "FDTD2D(absorbing_layer_reflection)": (
        1e-3,
        lambda v: _acoustic_engine(absorbing_layer_reflection=v),
    ),
    "FDTD2D(damping)": (10.0, lambda v: _acoustic_engine(damping=v)),
    "FDTD2D(edge_impedance)": (
        415.0,
        lambda v: _acoustic_engine(
            absorbing_layer_cells=0, edge_impedance={"left": v, "right": v}
        ),
    ),
    "add_plane_wave(center_m)": (0.08, lambda v: _plane_wave(center_m=v)),
    "add_plane_wave(half_width_m)": (0.03, lambda v: _plane_wave(half_width_m=v)),
    "add_plane_wave(amplitude)": (0.5, lambda v: _plane_wave(amplitude=v)),
    "add_plane_wave(wavelength_m)": (0.04, lambda v: _plane_wave(wavelength_m=v)),
    "ElasticFDTD2D(c_p)": (2000.0, lambda v: _elastic_engine(c_p=v)),
    "ElasticFDTD2D(c_s)": (1000.0, lambda v: _elastic_engine(c_s=v)),
    "ElasticFDTD2D(rho)": (1000.0, lambda v: _elastic_engine(rho=v)),
    "ElasticFDTD2D(dx)": (0.01, lambda v: _elastic_engine(dx=v)),
    "ElasticFDTD2D(cfl)": (0.5, lambda v: _elastic_engine(cfl=v)),
    "ElasticFDTD2D(absorbing_layer_reflection)": (
        1e-3,
        lambda v: _elastic_engine(absorbing_layer_reflection=v),
    ),
    "ElasticFDTD2D(damping)": (10.0, lambda v: _elastic_engine(damping=v)),
}


def _stepped_fields(sim: FDTD2D | ElasticFDTD2D) -> dict[str, np.ndarray]:
    """Every field of *sim* after ten steps, by name."""
    sim.run(10)
    return _fields(sim)


@pytest.mark.parametrize("spelling", sorted(_EXACT_SPELLINGS))
@pytest.mark.parametrize("case", sorted(_ENGINE_INPUTS))
def test_an_engine_steps_a_decimal_or_a_fraction_as_the_float_it_reads_as(
    case: str, spelling: str
) -> None:
    """An engine given a ``Decimal`` or a ``Fraction`` steps as the engine given its float.

    Both engines failed when they were built with NumPy's own words for a
    ``Decimal`` or a ``Fraction`` ``cfl`` (``ufunc 'isfinite' not
    supported``) or ``absorbing_layer_reflection`` (``loop of ufunc does not
    support argument 0``), and the acoustic one refused a ``Decimal`` edge
    impedance as no real number, though it took a ``Fraction``.
    """
    real, build = _ENGINE_INPUTS[case]
    expected = _stepped_fields(build(real))
    stepped = _stepped_fields(build(_EXACT_SPELLINGS[spelling](real)))
    assert [
        name for name in expected if not np.array_equal(stepped[name], expected[name])
    ] == []


def _stepped_with(case: str, value: object) -> dict[str, np.ndarray]:
    """What the run or the engine of *case* records once stepped, given *value*."""
    if case in _RUN_INPUTS:
        return {"probe": _probe_histories(_RUN_INPUTS[case][1](value))}
    return _stepped_fields(_ENGINE_INPUTS[case][1](value))


@pytest.mark.parametrize("case", sorted([*_RUN_INPUTS, *_ENGINE_INPUTS]))
def test_a_numpy_float32_steps_as_the_float_it_holds(case: str) -> None:
    """A run, a source or an engine given a NumPy ``float32`` steps as the one given its float.

    A ``float32`` Courant number, sponge reflection or number of a source
    was kept as given, so the time step, the sponge and the source's waveform
    were computed in ``float32``: ``cfl=np.float32(0.5)``, which holds 0.5
    exactly, stepped by another time step than ``cfl=0.5``.
    """
    narrow = np.float32(
        _RUN_INPUTS[case][0] if case in _RUN_INPUTS else _ENGINE_INPUTS[case][0]
    )
    expected = _stepped_with(case, float(narrow))
    stepped = _stepped_with(case, narrow)
    assert [
        name for name in expected if not np.array_equal(stepped[name], expected[name])
    ] == []


#: The owners whose every real input a ``Decimal`` and a ``Fraction`` case
#: above covers, and the table that holds the cases.
_DECIMAL_OWNERS: dict[str, dict[str, Any]] = {
    "FDTDRun": _RUN_INPUTS,
    "ElasticRun": _RUN_INPUTS,
    "FDTDBoundaries": _RUN_INPUTS,
    "GaussianPulse": _RUN_INPUTS,
    "CWSource": _RUN_INPUTS,
    "SignalSource": _RUN_INPUTS,
    "PlaneWaveSource": _RUN_INPUTS,
    "ExplosionSource": _RUN_INPUTS,
    "ForceSource": _RUN_INPUTS,
    "FDTD2D": _ENGINE_INPUTS,
    "ElasticFDTD2D": _ENGINE_INPUTS,
    "add_plane_wave": _ENGINE_INPUTS,
}

#: Real inputs the tables above leave out, with the reason.
_NOT_A_DECIMAL_CASE = {
    # Samples are an array, read as the float64 array it holds whatever
    # numbers it is given, and checked as one where a source holds them.
    ("SignalSource", "samples"): "an array, held as float64",
}


def test_every_real_input_of_a_run_a_source_and_an_engine_has_a_decimal_case() -> None:
    """A real input added to a run, a source or an engine without its case fails here."""
    missing = [
        f"{owner}({name})"
        for owner, table in _DECIMAL_OWNERS.items()
        for name in _real_parameters(owner)
        if f"{owner}({name})" not in table and (owner, name) not in _NOT_A_DECIMAL_CASE
    ]
    assert missing == []


#: Each real input a source holds, by ``source(input)``: the float it is
#: written as when it is right, and the source built around it.
_SOURCE_INPUTS: dict[str, tuple[float, Callable[[object], object]]] = {
    "GaussianPulse(half_width_s)": (
        1e-4,
        lambda v: GaussianPulse(ix=8, iy=8, half_width_s=v),  # type: ignore[arg-type]
    ),
    "GaussianPulse(t0)": (
        3e-4,
        lambda v: GaussianPulse(ix=8, iy=8, half_width_s=1e-4, t0=v),  # type: ignore[arg-type]
    ),
    "GaussianPulse(amplitude)": (
        0.5,
        lambda v: GaussianPulse(ix=8, iy=8, half_width_s=1e-4, amplitude=v),  # type: ignore[arg-type]
    ),
    "CWSource(frequency)": (
        2000.0,
        lambda v: CWSource(ix=8, iy=8, frequency=v),  # type: ignore[arg-type]
    ),
    "CWSource(amplitude)": (
        0.5,
        lambda v: CWSource(ix=8, iy=8, frequency=2000.0, amplitude=v),  # type: ignore[arg-type]
    ),
    "CWSource(ramp_cycles)": (
        2.0,
        lambda v: CWSource(ix=8, iy=8, frequency=2000.0, ramp_cycles=v),  # type: ignore[arg-type]
    ),
    "SignalSource(fs)": (
        48000.0,
        lambda v: SignalSource(ix=8, iy=8, samples=_SAMPLES, fs=v),  # type: ignore[arg-type]
    ),
    "SignalSource(amplitude)": (
        0.5,
        lambda v: SignalSource(ix=8, iy=8, samples=_SAMPLES, fs=48000.0, amplitude=v),  # type: ignore[arg-type]
    ),
    "PlaneWaveSource(amplitude)": (
        0.5,
        lambda v: PlaneWaveSource(
            direction="right",
            waveform=_drive().value,
            amplitude=v,  # type: ignore[arg-type]
        ),
    ),
    "ExplosionSource(amplitude)": (
        0.5,
        lambda v: ExplosionSource(ix=8, iy=8, waveform=_drive().value, amplitude=v),  # type: ignore[arg-type]
    ),
    "ForceSource(amplitude)": (
        0.5,
        lambda v: ForceSource(
            ix=8,
            iy=8,
            direction="y",
            waveform=_drive().value,
            amplitude=v,  # type: ignore[arg-type]
        ),
    ),
}


@pytest.mark.parametrize("spelling", sorted(_EXACT_SPELLINGS))
@pytest.mark.parametrize("case", sorted(_SOURCE_INPUTS))
def test_a_source_holds_a_decimal_or_a_fraction_as_the_float_it_reads_as(
    case: str, spelling: str
) -> None:
    """A source holds the float a ``Decimal`` or a ``Fraction`` reads as, and travels.

    A source held the number as it was given: a ``Decimal`` failed at the
    first step, and either one, a ``Fraction`` that stepped here among them,
    was refused when the run was sent to a node, which rebuilds no
    ``Decimal`` and no ``Fraction``.
    """
    real, build = _SOURCE_INPUTS[case]
    name = case.split("(")[1].rstrip(")")
    source = build(_EXACT_SPELLINGS[spelling](real))
    held = getattr(source, name)
    assert type(held) is float
    assert held == real
    run = (
        _elastic_run(sources=[source])
        if isinstance(source, ExplosionSource | ForceSource)
        else _acoustic_run(sources=[source])
    )
    encode_arguments({"run": run})


#: The two numbers of a contour's phasors, by name, and the float each is
#: written as when it is right.
_CONTOUR_NUMBERS = {"frequency": 1000.0, "segment": 0.1}


@pytest.mark.parametrize("spelling", [*sorted(_EXACT_SPELLINGS), "float32"])
@pytest.mark.parametrize("name", sorted(_CONTOUR_NUMBERS))
def test_contour_phasors_hold_the_float_a_number_of_another_type_reads_as(
    name: str, spelling: str
) -> None:
    """The phasors of a contour hold the float a ``Decimal``, a ``Fraction`` or a ``float32`` reads as.

    A ``Decimal`` or a ``Fraction`` as the ``frequency`` or the ``segment``
    of a :class:`ContourPhasors` was refused with NumPy's ``ufunc
    'isfinite' not supported``, which names neither, and a ``float32`` was
    kept as given.
    """
    real = _CONTOUR_NUMBERS[name]
    given = (
        np.float32(real) if spelling == "float32" else _EXACT_SPELLINGS[spelling](real)
    )
    held = getattr(_contour(**{name: given}), name)
    assert type(held) is float
    assert held == float(given)


#: Finite numbers no float holds, by how a caller writes them, each built
#: when it is used; a long double is one only where it is wider than a float.
_BEYOND_A_FLOAT: dict[str, Callable[[], object]] = {
    "python integer": lambda: 10**400,
    "Fraction": lambda: Fraction(10**400),
    "Decimal": lambda: Decimal("1e400"),
    "long double": lambda: np.longdouble("1e400"),
}

_BEYOND_A_FLOAT_SPELLINGS = [
    pytest.param(
        spelling,
        marks=_ONLY_WITH_A_WIDE_LONG_DOUBLE if spelling == "long double" else (),
    )
    for spelling in sorted(_BEYOND_A_FLOAT)
]


def _probe_for(frequency: object) -> object:
    """The phasors of a stepped contour probe at *frequency*."""
    sim = FDTD2D(c=343.0, dx=0.01, shape=(_NY, _NX))
    sim.add_source(_pulse())
    probe = sim.add_contour_probe(3, 10, 3, 10, frequencies=[1000.0])
    sim.run(2)
    return probe.phasors(frequency)  # type: ignore[arg-type]


def _number_in(build: Callable[..., object], name: str) -> Callable[[object], object]:
    """The call that hands *build* a number as its input *name*."""
    return lambda number: build(**{name: number})


def _map_in(build: Callable[..., object], name: str) -> Callable[[object], object]:
    """The call that hands *build* a map, written as lists, of one number as *name*."""
    return lambda number: build(**{name: [[number] * _NX] * _NY})


def _material(**fields: object) -> Material:
    """A material with *fields* written over a solid's speeds and density."""
    given: dict[str, Any] = {"c_p": 2000.0, "c_s": 1000.0, "rho": 1000.0, **fields}
    return Material(**given)


#: Each real input of a run, a source, a material and an engine that a
#: number no float holds can reach, by ``owner(input)``: the input's name,
#: and the call that hands it the number.
_TOO_LARGE_INPUTS: dict[str, tuple[str, Callable[[object], object]]] = {
    **{
        f"FDTDRun({name})": (name, _number_in(_acoustic_run, name))
        for name in ("c", "dx", "duration_s", "rho", "cfl", "damping")
    },
    **{
        f"FDTDRun({name} map)": (name, _map_in(_acoustic_run, name))
        for name in ("c", "rho", "damping")
    },
    **{
        f"ElasticRun({name})": (name, _number_in(_elastic_run, name))
        for name in ("c_p", "c_s", "rho", "dx", "duration_s", "cfl", "damping")
    },
    **{
        f"ElasticRun({name} map)": (name, _map_in(_elastic_run, name))
        for name in ("c_p", "c_s", "rho", "damping")
    },
    **{
        case: (case.split("(")[1].rstrip(")"), build)
        for case, (_, build) in _SOURCE_INPUTS.items()
    },
    "SignalSource(samples)": (
        "samples",
        lambda v: SignalSource(
            ix=8, iy=8, samples=np.array([0.0, v, 0.0], dtype=object), fs=48000.0
        ),
    ),
    **{
        f"Material({name})": (name, _number_in(_material, name))
        for name in ("c_p", "c_s", "rho")
    },
    "FDTD2D(absorbing_layer_reflection)": (
        "absorbing_layer_reflection",
        lambda v: _acoustic_engine(absorbing_layer_reflection=v),
    ),
    "ElasticFDTD2D(absorbing_layer_reflection)": (
        "absorbing_layer_reflection",
        lambda v: _elastic_engine(absorbing_layer_reflection=v),
    ),
    **{
        f"add_plane_wave({name})": (name, _number_in(_plane_wave, name))
        for name in ("center_m", "half_width_m", "amplitude", "wavelength_m")
    },
    "add_contour_probe(frequencies)": (
        "frequencies",
        lambda v: FDTD2D(c=343.0, dx=0.01, shape=(_NY, _NX)).add_contour_probe(
            3, 10, 3, 10, frequencies=np.array([v], dtype=object)
        ),
    ),
    "phasors(frequency)": ("frequency", _probe_for),
    **{
        f"ContourPhasors({name})": (name, lambda v, name=name: _contour(**{name: v}))
        for name in ("frequency", "segment")
    },
}


@pytest.mark.parametrize("spelling", _BEYOND_A_FLOAT_SPELLINGS)
@pytest.mark.parametrize("case", sorted(_TOO_LARGE_INPUTS))
def test_a_number_no_float_holds_is_refused_by_name(case: str, spelling: str) -> None:
    """A finite number past a float's largest is refused naming the input it was given to.

    The checks read one number through ``float``, which refused a Python
    integer or a ``Fraction`` that large with Python's ``OverflowError``
    (``int too large to convert to float``), naming nothing, and a map
    through ``np.asarray`` the same way; a long double ``ramp_cycles`` that
    large passed as a finite number.
    """
    name, build = _TOO_LARGE_INPUTS[case]
    number = _BEYOND_A_FLOAT[spelling]()
    with pytest.raises(ValueError, match=rf"(?<!\w)'?{name}'? (?:must|holds)"):
        build(number)
