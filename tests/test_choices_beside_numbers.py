#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A choice beside numbers refuses, by name, a text where its numbers go.

A public parameter or record field that takes one of a few words or numbers
reads a ``str`` as the choice and anything else as the numbers. A ``bytes``, a
``bytearray``, a text inside a sequence or an array, ``None`` where it is no
option and an object that is no number are not a ``str``, so each reached the
conversion of the numbers. A text that reads as a number was parsed:
``materials.layered_absorber(termination=["400", "400"])`` closed the stack
with an impedance of 400 Pa s/m, ``materials.delany_bazley`` took
``coefficients=b"12345678"`` as the codes of its eight characters, and
``filters.time_weighting`` started from ``initial_state=["0.5", "0.5"]``. The
rest was refused with an error that named no parameter, or, in
``aircraft.RotorcraftGround``, stored and left to the event that read it.
Each is the wrong type whatever it reads as, a :class:`TypeError` naming the
parameter (rule A43 of the contributor guide), raised where the call starts
or where the record is built.

The walk reads every public parameter and record field of the imported
package from its annotation, through the aliases of its module: a union that
sets a ``Literal`` of texts beside a number, an array of numbers or a
sequence of them, at the top or inside a container or a mapping, is a choice
beside numbers. Each one found has a call in :data:`CALLS`, and each call a
parameter the walk finds, so one published later is walked as soon as it
exists and a call that outlives its parameter fails.

The walk sees a choice only where the annotation states it, so a second one
reads the bodies. A public parameter or record field whose annotation names
numbers and no choice, but whose body, or a function of the package it is
handed to, reads a ``str`` of it as something other than numbers, is a choice
beside numbers its annotation hides (``speech.speech_intelligibility_index``
read a vocal effort from a ``speech_spectrum`` annotated ``ArrayLike``), and
fails until the annotation states it, where the walk then finds it.
"""

from __future__ import annotations

import ast
import dataclasses
import functools
import inspect
import pathlib
import sys
import warnings
from typing import TYPE_CHECKING, NamedTuple

import numpy as np
import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_choice_literals as ccl

from phonometry import aircraft, building, filters, materials, room, simulation, speech

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

#: The bare names an annotation spells a number, an array of numbers or a
#: value that converts itself to one with, once its aliases are spelt out.
_NUMBER_NAMES = frozenset(
    {
        "ArrayLike",
        "NDArray",
        "SupportsNumericArray",
        "complex",
        "float",
        "int",
    }
)

#: The numpy scalar and array types an annotation spells a number with.
_NUMPY_NUMBERS = frozenset(
    {
        "complex128",
        "complexfloating",
        "float32",
        "float64",
        "floating",
        "inexact",
        "int64",
        "integer",
        "ndarray",
        "number",
        "signedinteger",
        "unsignedinteger",
    }
)

#: The containers whose items, all numbers, make a sequence of numbers.
_CONTAINERS = frozenset(
    {"Collection", "Iterable", "NestedSequence", "Sequence", "list", "tuple"}
)


class Member(NamedTuple):
    """A choice beside numbers: where it is published and whether ``None`` is an option."""

    module: str
    owner: str
    parameter: str
    takes_none: bool


def _origin(node: ast.expr) -> str:
    """The last name of what an annotation node names (``np.floating`` is ``floating``)."""
    if isinstance(node, ast.Subscript):
        return _origin(node.value)
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _union(node: ast.expr) -> list[ast.expr]:
    """The members of a union written with ``|``, or the node alone."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return [*_union(node.left), *_union(node.right)]
    return [node]


def _items(node: ast.Subscript) -> list[ast.expr]:
    """The arguments of a subscript, an ellipsis left out."""
    found = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
    return [
        item
        for item in found
        if not (isinstance(item, ast.Constant) and item.value is Ellipsis)
    ]


def _is_text_choice(node: ast.expr) -> bool:
    """Whether *node* is a ``Literal`` that offers a text."""
    return (
        isinstance(node, ast.Subscript)
        and _origin(node) == "Literal"
        and any(
            isinstance(item, ast.Constant) and isinstance(item.value, str)
            for item in _items(node)
        )
    )


def _is_numbers(node: ast.expr) -> bool:
    """Whether *node* is a number, an array of numbers or a sequence of them."""
    members = _union(node)
    if len(members) > 1:
        return all(_is_numbers(member) for member in members)
    origin = _origin(node)
    named = node.value if isinstance(node, ast.Subscript) else node
    if isinstance(named, ast.Attribute):
        return origin in _NUMPY_NUMBERS
    if origin in _NUMBER_NAMES:
        return True
    if isinstance(node, ast.Subscript) and origin in _CONTAINERS:
        items = _items(node)
        return bool(items) and all(_is_numbers(item) for item in items)
    return False


def sets_a_choice_beside_numbers(node: ast.expr) -> bool:
    """Whether a union of *node*, at the top or nested, sets a text choice beside numbers."""
    members = _union(node)
    if any(_is_text_choice(m) for m in members) and any(
        _is_numbers(m) for m in members if not _is_text_choice(m)
    ):
        return True
    return any(
        sets_a_choice_beside_numbers(item)
        for member in members
        if isinstance(member, ast.Subscript) and not _is_text_choice(member)
        for item in _items(member)
    )


def _takes_none(node: ast.expr) -> bool:
    return any(isinstance(m, ast.Constant) and m.value is None for m in _union(node))


def _read(annotation: object, module: str) -> ast.expr | None:
    """An annotation as a syntax tree, its module's aliases spelt out."""
    written = ccl.expanded(ccl._annotation(annotation), module)
    try:
        return ast.parse(written, mode="eval").body
    except SyntaxError:
        return None


def _annotated(module: str, owner: object) -> Iterator[tuple[str, object, str]]:
    """``(parameter, annotation, module)`` of what *owner* takes."""
    if inspect.isclass(owner) and dataclasses.is_dataclass(owner):
        for field in dataclasses.fields(owner):
            yield field.name, field.type, ccl._field_module(owner, field.name)
        return
    try:
        signature = inspect.signature(owner)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return
    for parameter in signature.parameters.values():
        if parameter.annotation is not inspect.Parameter.empty:
            yield parameter.name, parameter.annotation, module


def choices_beside_numbers() -> frozenset[Member]:
    """Every public parameter or record field that sets a text choice beside numbers.

    The generated constructor of a record takes its fields, which are read
    once, as the record's own.
    """
    found: set[Member] = set()
    for module, qualname, target in ccl._targets():
        owner_name, _, method = qualname.rpartition(".")
        if method == "__init__":
            record = getattr(sys.modules[module], owner_name.split(".")[0], None)
            if inspect.isclass(record) and dataclasses.is_dataclass(record):
                continue
        for name, annotation, where in _annotated(module, target):
            node = _read(annotation, where)
            if node is not None and sets_a_choice_beside_numbers(node):
                owner = qualname.removesuffix(".__init__")
                found.add(Member(module, owner, name, _takes_none(node)))
    return frozenset(found)


#: The module of the shared guards. A parameter is handed to them to be
#: refused or tested, never read as a choice, so they are not followed.
_GUARDS = "phonometry._internal.validation"


def _names_text(node: ast.expr) -> bool:
    """Whether the type an ``isinstance`` test names is ``str``, alone or among others."""
    if isinstance(node, ast.Tuple):
        return any(_names_text(item) for item in node.elts)
    return any(
        isinstance(member, ast.Name) and member.id == "str" for member in _union(node)
    )


def _text_branches(tree: ast.AST) -> Iterator[ast.expr]:
    """What each ``isinstance(<value>, str)`` that reads a text as a choice tests.

    A test that refuses the text, as the test of an ``if`` whose body ends in
    a ``raise``, or excludes it, under a ``not``, reads no choice.
    """
    passed: set[int] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.If)
            and node.body
            and isinstance(node.body[-1], ast.Raise)
        ):
            passed.update(id(inner) for inner in ast.walk(node.test))
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            passed.update(id(inner) for inner in ast.walk(node.operand))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "isinstance"
            and len(node.args) == 2
            and _names_text(node.args[1])
            and id(node) not in passed
        ):
            yield node.args[0]


class _Body(NamedTuple):
    """What the body census reads of one function: its tree, its branches on a text, and its calls."""

    tree: ast.AST
    branches: tuple[ast.expr, ...]
    calls: tuple[tuple[object, dict[str, ast.expr]], ...]


@functools.cache
def _body(function: object) -> _Body | None:
    """The tree of *function*, what its branches on a text test, and what it hands each function of the package it calls.

    Read once per function, however many parameters are followed through it.
    """
    tree = ccl._parsed(function)
    if tree is None:
        return None
    module = getattr(function, "__module__", "") or ""
    namespace = ccl._namespace(function, tree, module)
    spread = ccl._spread_dicts(tree)
    calls: list[tuple[object, dict[str, ast.expr]]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        callee = ccl._callee(node, namespace, module)
        if callee is not None and callee.__module__ != _GUARDS:
            calls.append((callee, ccl._arguments(node, callee, spread)))
    return _Body(tree, tuple(_text_branches(tree)), tuple(calls))


#: What :func:`reads_a_text_as_a_choice` found for a function and the name of
#: a parameter, so each is followed once. A pair being followed reads ``None``
#: until it is done, which ends a cycle of calls.
_READS: dict[tuple[object, str], str | None] = {}


def reads_a_text_as_a_choice(
    function: object,
    name: str,
    *,
    target: Callable[[ast.expr], bool] | None = None,
) -> str | None:
    """Where *function*, or a function it hands parameter *name* to, reads a ``str`` of it.

    The parameter is followed as the choice guard follows it, through the
    locals bound from it and into each function of the package it is handed
    to, the shared guards left out. *target* reads the value some other way
    than by its name: ``self.<field>`` in a ``__post_init__``.
    """
    key = (function, name)
    if target is None and key in _READS:
        return _READS[key]
    if target is None:
        _READS[key] = None
    found: str | None = None
    body = _body(function)
    if body is not None and (body.branches or body.calls):
        matches = ccl._following(body.tree, target or ccl._the_name(name))
        if any(matches(tested) for tested in body.branches):
            found = f"{getattr(function, '__qualname__', function)}({name})"
        for callee, handed in () if found else body.calls:
            received = next(
                (parameter for parameter, value in handed.items() if matches(value)),
                None,
            )
            found = (
                None if received is None else reads_a_text_as_a_choice(callee, received)
            )
            if found is not None:
                break
    if target is None:
        _READS[key] = found
    return found


def _numbers_and_no_choice(node: ast.expr | None) -> bool:
    """Whether an annotation names numbers at its top and sets no choice beside them."""
    return (
        node is not None
        and not sets_a_choice_beside_numbers(node)
        and any(_is_numbers(member) for member in _union(node))
    )


def unstated_choices() -> list[tuple[str, str, str, str]]:
    """``(module, owner, parameter, where)`` of each choice beside numbers no annotation states.

    A public parameter or record field whose annotation names numbers and
    sets no choice beside them, and whose body, or a function of the package
    it is handed to, reads a ``str`` of it as a choice.
    """
    found: list[tuple[str, str, str, str]] = []
    for module, qualname, target in ccl._targets():
        owner_name, _, method = qualname.rpartition(".")
        if method == "__init__":
            record = getattr(sys.modules[module], owner_name.split(".")[0], None)
            if inspect.isclass(record) and dataclasses.is_dataclass(record):
                continue
        if inspect.isclass(target) and dataclasses.is_dataclass(target):
            check = vars(target).get("__post_init__")
            for field in dataclasses.fields(target):
                node = _read(field.type, ccl._field_module(target, field.name))
                if check is None or not _numbers_and_no_choice(node):
                    continue
                where = reads_a_text_as_a_choice(
                    check, field.name, target=ccl._field_of_self(field.name)
                )
                if where is not None:
                    found.append((module, qualname, field.name, where))
            continue
        for name, annotation, home in _annotated(module, target):
            if not _numbers_and_no_choice(_read(annotation, home)):
                continue
            where = reads_a_text_as_a_choice(target, name)
            if where is not None:
                found.append((module, qualname, name, where))
    return sorted(found)


_BANDS = np.array([500.0, 1000.0])
_LAYERS = [materials.AirLayer(thickness_m=0.05)]
_SAMPLES = np.random.default_rng(7).standard_normal(480)


def _rotorcraft_ground(value: object) -> object:
    return aircraft.RotorcraftGround(flow_resistivity=value)  # type: ignore[arg-type]


def _ground_effect(value: object) -> object:
    return aircraft.ground_effect_adjustment(
        [500.0],
        10.0,
        1.2,
        100.0,
        flow_resistivity=value,  # type: ignore[arg-type]
    )


def _terrain_screening(value: object) -> object:
    return aircraft.terrain_screening_adjustment(
        (0.0, 10.0),
        (100.0, 1.2),
        [0.0, 50.0, 100.0],
        [0.0, 0.0, 0.0],
        frequencies=[500.0],
        flow_resistivity=value,  # type: ignore[arg-type]
    )


def _tie_coupling(value: object) -> object:
    return building.wall_tie_coupling_loss_factor(
        [500.0],
        200.0,
        200.0,
        1e6,
        1e6,
        ties_per_area=2.5,
        tie=value,  # type: ignore[arg-type]
    )


def _tie_stiffness(value: object) -> object:
    return building.wall_tie_stiffness_per_area(2.5, value)  # type: ignore[arg-type]


def _time_weighting(value: object) -> object:
    return filters.time_weighting(_SAMPLES, 48000.0, initial_state=value)  # type: ignore[call-overload]


def _layered(value: object) -> object:
    return materials.layered_absorber(_BANDS, _LAYERS, termination=value)  # type: ignore[arg-type]


def _diffuse(value: object) -> object:
    return materials.diffuse_field_absorption(
        _BANDS,
        _LAYERS,
        n_quadrature_points=4,
        termination=value,  # type: ignore[arg-type]
    )


def _delany_bazley(value: object) -> object:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", materials.PorousAbsorberWarning)
        return materials.delany_bazley(_BANDS, 1.0e4, coefficients=value)  # type: ignore[arg-type]


def _shaped_sweep(value: object) -> object:
    return room.shaped_sweep_signal(8000.0, 100.0, 1000.0, 0.25, target=value)  # type: ignore[arg-type]


def _speech_index(value: object) -> object:
    return speech.speech_intelligibility_index(value)  # type: ignore[arg-type]


def _fdtd_boundaries(value: object) -> object:
    return simulation.FDTDBoundaries(sides={"left": value})  # type: ignore[dict-item]


#: How each choice beside numbers is called with a value in place of its
#: numbers, and the name its refusal gives. An FDTD boundary names the side of
#: ``sides`` it reads, ``'left'``.
CALLS: dict[tuple[str, str, str], tuple[Callable[[object], object], str]] = {
    ("phonometry.aircraft.rotorcraft_noise", "RotorcraftGround", "flow_resistivity"): (
        _rotorcraft_ground,
        "'flow_resistivity'",
    ),
    (
        "phonometry.aircraft.rotorcraft_propagation",
        "ground_effect_adjustment",
        "flow_resistivity",
    ): (_ground_effect, "'flow_resistivity'"),
    (
        "phonometry.aircraft.rotorcraft_propagation",
        "terrain_screening_adjustment",
        "flow_resistivity",
    ): (_terrain_screening, "'flow_resistivity'"),
    (
        "phonometry.building.prediction.masonry_cavity_wall",
        "wall_tie_coupling_loss_factor",
        "tie",
    ): (_tie_coupling, "'tie'"),
    (
        "phonometry.building.prediction.masonry_cavity_wall",
        "wall_tie_stiffness_per_area",
        "tie",
    ): (_tie_stiffness, "'tie'"),
    ("phonometry.filters.weighting", "time_weighting", "initial_state"): (
        _time_weighting,
        "'initial_state'",
    ),
    ("phonometry.materials.absorbers.layered", "layered_absorber", "termination"): (
        _layered,
        "'termination'",
    ),
    (
        "phonometry.materials.absorbers.layered",
        "diffuse_field_absorption",
        "termination",
    ): (_diffuse, "'termination'"),
    ("phonometry.materials.absorbers.porous", "delany_bazley", "coefficients"): (
        _delany_bazley,
        "'coefficients'",
    ),
    ("phonometry.room._impulse_response", "shaped_sweep_signal", "target"): (
        _shaped_sweep,
        "'target'",
    ),
    ("phonometry.simulation.fdtd", "FDTDBoundaries", "sides"): (
        _fdtd_boundaries,
        "side 'left'",
    ),
    ("phonometry.speech.sii", "speech_intelligibility_index", "speech_spectrum"): (
        _speech_index,
        "'speech_spectrum'",
    ),
}


def _bytearrays_in_objects() -> np.ndarray:
    """An array of objects that holds two ``bytearray``, as given, not spread over rows."""
    held = np.empty(2, dtype=object)
    held[0] = bytearray(b"400")
    held[1] = bytearray(b"400")
    return held


#: What a caller writes where a choice's numbers go that is no number: a
#: text in every form but a ``str`` (which is the choice), ``None`` and an
#: object. ``None`` is passed over where the annotation offers it. A
#: ``bytearray`` inside a sequence is a row of the codes of its characters
#: to numpy, and :func:`float` parses one inside an array of objects.
PROBES: dict[str, object] = {
    "bytes": b"1",
    "numpy-bytes": np.bytes_(b"1"),
    "bytearray": bytearray(b"1"),
    "bytes-in-a-list": [b"1"],
    "bytearray-in-a-list": [bytearray(b"1")],
    "bytearrays-in-a-list": [bytearray(b"400"), bytearray(b"400")],
    "bytearrays-in-an-array-of-objects": _bytearrays_in_objects(),
    "text-in-a-list": ["1"],
    "texts-in-a-list": ["400", "400"],
    "array-of-text": np.array(["1"]),
    "zero-dimensional-text": np.array("1"),
    "none": None,
    "object": object(),
}

#: The probes a member takes on purpose, keyed by member and probe, with the
#: reason. A stale entry fails.
EXEMPT: dict[tuple[tuple[str, str, str], str], str] = {}


def _key(member: Member) -> tuple[str, str, str]:
    return (member.module, member.owner, member.parameter)


_FOUND = choices_beside_numbers()


def test_every_choice_beside_numbers_is_walked() -> None:
    """The walk and :data:`CALLS` name the same parameters, both ways."""
    found = {_key(member) for member in _FOUND}
    assert sorted(found - CALLS.keys()) == [], "a choice beside numbers has no call"
    assert sorted(CALLS.keys() - found) == [], "a call names no choice beside numbers"


def test_no_body_reads_a_choice_its_annotation_does_not_state() -> None:
    """A ``str`` read as a choice beside numbers is stated in the annotation."""
    assert unstated_choices() == []


def test_the_body_census_reads_a_choice_and_passes_over_a_refusal() -> None:
    """A branch on a text is a choice; a refusal of one, or its exclusion, is none."""

    def branches(source: str) -> int:
        return sum(1 for _ in _text_branches(ast.parse(source)))

    assert branches("x = load(v) if isinstance(v, str) else asarray(v)") == 1
    assert branches("if isinstance(v, str):\n    v = table[v]") == 1
    assert (
        branches("if isinstance(v, (str, bytes)) or n != 1:\n    raise TypeError") == 0
    )
    assert branches("ok = isinstance(v, Sequence) and not isinstance(v, str)") == 0


def test_every_exemption_is_a_probe_a_member_takes() -> None:
    """An exemption names a walked member and a probe, and the call still takes it."""
    for (key, probe), reason in EXEMPT.items():
        assert key in CALLS, key
        assert probe in PROBES, probe
        assert reason
        call, _ = CALLS[key]
        call(PROBES[probe])


def _cases() -> Iterator[tuple[tuple[str, str, str], str]]:
    for member in sorted(_FOUND):
        for probe in PROBES:
            if probe == "none" and member.takes_none:
                continue
            if (_key(member), probe) in EXEMPT:
                continue
            yield _key(member), probe


_CASES = list(_cases())


@pytest.mark.parametrize(
    ("key", "probe"),
    _CASES,
    ids=[f"{key[1]}.{key[2]}-{probe}" for key, probe in _CASES],
)
def test_a_choice_beside_numbers_refuses_what_is_no_number_by_name(
    key: tuple[str, str, str], probe: str
) -> None:
    call, named = CALLS[key]
    with pytest.raises(TypeError, match=named):
        call(PROBES[probe])


def test_the_walk_reads_a_choice_beside_numbers_wherever_the_union_is() -> None:
    """At the top, through an alias spelt out, and inside a mapping's values."""
    read = [
        ast.parse(text, mode="eval").body
        for text in (
            "Literal['rigid', 'free'] | complex | NestedSequence[complex]",
            "Literal['white', 'pink'] | tuple[ArrayLike, ArrayLike]",
            "Literal['a'] | Mapping[Literal['left'], Literal['rigid'] | float]",
            "Literal['delany_bazley'] | tuple[float, ...]",
            "Literal['A', 'B'] | np.floating[Any] | None",
        )
    ]
    assert [sets_a_choice_beside_numbers(node) for node in read] == [True] * 5


def test_the_walk_passes_over_what_sets_no_choice_beside_numbers() -> None:
    """A key of a mapping, a choice beside a record or a text, and numbers alone."""
    read = [
        ast.parse(text, mode="eval").body
        for text in (
            "Mapping[Literal['low', 'high'], float]",
            "Literal['sand'] | WestonSeabed",
            "Literal['a', 'b'] | Sequence[Literal['a', 'b']]",
            "float | NDArray[np.float64]",
            "Literal[1, 3] | float",
        )
    ]
    assert [sets_a_choice_beside_numbers(node) for node in read] == [False] * 5
