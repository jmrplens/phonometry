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
"""

from __future__ import annotations

import inspect
import re
from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry.simulation import (
    FDTD2D,
    STEEL,
    CWSource,
    ElasticFDTD2D,
    ElasticRun,
    ExplosionSource,
    FDTDBoundaries,
    FDTDRun,
    ForceSource,
    GaussianPulse,
    Material,
    PlaneWaveSource,
    SignalSource,
    scholte_speed,
)
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
                343.0, 0.01, shape=(_NY, _NX), edge_impedance={"left": value}
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
            lambda **kw: FDTD2D(343.0, 0.01, shape=(_NY, _NX)).add_plane_wave(
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
        FDTD2D(343.0, 0.01, shape=(_NY, _NX)),
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
            lambda value=value: FDTD2D(343.0, 0.01, shape=(_NY, _NX)).add_contour_probe(
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


_CASES = [*_engine_cases(), *_record_cases(), *_contour_cases()]


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
