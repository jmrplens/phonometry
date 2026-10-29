#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A record a caller builds says what its constructor takes.

A frozen record that converts what it is given stores the converted value,
so its fields say what it holds: ``levels: NDArray[np.float64]``. A caller
hands it a list, a tuple or an array of any dtype, and a type checker reads
the fields to type the call, so it would refuse the list the record takes.
The record therefore declares the constructor a type checker reads, inside
``if TYPE_CHECKING:`` in its body (``def __init__(self, *, levels:
ArrayLike) -> None: ...``), which the running class never defines.

``scripts/check_parameter_annotations.py`` reads the records
(``constructor_problems``): a record a caller builds (one a public function
takes, one such a record holds, or one ``CALLER_BUILT`` names) that converts
a field annotated as a container of a fixed kind or as a sequence of
numbers declares the constructor, and every declared constructor keeps step
with its fields, name for name, keyword-only exactly where the field is,
with the field's default, a converted field taking ``ArrayLike`` or an open
sequence (of numbers or arrays, beside the numpy array of them) and every
other one taking all its field's annotation names. A
constructor of more keywords than a function takes (the 13 of Sonar's rule
S107) takes them as the keys of a ``TypedDict``, ``**measurements:
Unpack[Keywords]``, each key read as the keyword it stands for. The first
test holds the package to that; the others fix what the reading must catch
on small packages written for the purpose.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
import pathlib
import sys
import textwrap

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_parameter_annotations as cpa
import check_return_overloads as overloads
from ast_scan import ROOT, python_files
from markdown_fences import python_fences

_SOURCE = ROOT / "src" / "phonometry"

_IMPORTS = """
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import KW_ONLY, dataclass, field, fields
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import ArrayLike, NDArray
"""


@pytest.fixture(scope="module")
def reader() -> cpa.Reader:
    """The package, read once."""
    package = overloads.Package(python_files([], _SOURCE), _SOURCE)
    return cpa.Reader(package)


def _in_gpu_files(reader: cpa.Reader, record: str) -> bool:
    module = reader.annotations.classes[record][0]
    path = cpa.repository_path(reader.package.paths[module], _SOURCE)
    return path in set(cpa.gpu_parity_files())


def test_every_record_says_what_its_constructor_takes(reader: cpa.Reader) -> None:
    problems: dict[str, list[str]] = {}
    for record in cpa.public_records(reader.package, reader.annotations):
        if _in_gpu_files(reader, record):
            continue
        found = cpa.constructor_problems(reader, record)
        if found:
            problems[record] = found
    assert problems == {}


def test_the_records_a_caller_builds_cover_the_named_ones(reader: cpa.Reader) -> None:
    built = cpa.built_records(reader)
    for name in cpa.CALLER_BUILT:
        assert name in reader.annotations.classes, name
        assert name in built, name
        # Named only where no public function takes it: a record one takes is
        # read as built by a caller already, and the entry would say nothing.
        assert name not in reader.input_records, name


#: Where the guides live: the plain-markdown mirror GitHub serves, both
#: languages of the site, and the two front pages. The API reference the
#: site generates from the docstrings is left out: it states signatures, it
#: builds nothing.
_GUIDES = (ROOT / "docs", ROOT / "site" / "src" / "content" / "docs")
_FRONT_PAGES = (ROOT / "README.md", ROOT / "README_PYPI.md")


def _guide_pages() -> list[pathlib.Path]:
    pages = [
        page
        for folder in _GUIDES
        for page in sorted(folder.rglob("*.md*"))
        # docs/superpowers is gitignored scratch space, not documentation.
        if "superpowers" not in page.parts and "reference/api" not in page.as_posix()
    ]
    return pages + [page for page in _FRONT_PAGES if page.exists()]


def _phonometry_names(tree: ast.Module, names: dict[str, str]) -> None:
    """Add to *names* each name a block binds to a module or object of the package."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] == "phonometry":
                for alias in node.names:
                    names[alias.asname or alias.name] = f"{node.module}.{alias.name}"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "phonometry":
                    bound = alias.asname or alias.name.split(".")[0]
                    names[bound] = alias.name if alias.asname else "phonometry"


def _dotted(node: ast.expr, names: dict[str, str]) -> str | None:
    """The package path a called name or attribute chain stands for, if it is one."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not (isinstance(node, ast.Name) and node.id in names):
        return None
    return ".".join([names[node.id], *reversed(parts)])


def _resolved(dotted: str) -> object | None:
    """The object a package path names, the longest importable module first."""
    parts = dotted.split(".")
    for cut in range(len(parts), 0, -1):
        try:
            found: object = importlib.import_module(".".join(parts[:cut]))
        except ImportError:
            continue
        for part in parts[cut:]:
            found = getattr(found, part, None)
            if found is None:
                return None
        return found
    return None


def guide_built_records() -> dict[str, list[str]]:
    """Every record of the package a guide builds, by dotted name, with its pages.

    A block's call to a dataclass of the package, written as
    ``<domain>.<Record>(`` or through a name it imports, builds one. The
    names a page imports carry from one block to the next, as the page is
    read.
    """
    found: dict[str, list[str]] = {}
    for page in _guide_pages():
        names: dict[str, str] = {}
        for code in python_fences(page.read_text(encoding="utf-8")):
            try:
                tree = ast.parse(code)
            except SyntaxError:
                continue
            _phonometry_names(tree, names)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                dotted = _dotted(node.func, names)
                target = _resolved(dotted) if dotted is not None else None
                if isinstance(target, type) and dataclasses.is_dataclass(target):
                    record = f"{target.__module__}.{target.__qualname__}"
                    where = page.relative_to(ROOT).as_posix()
                    if where not in found.setdefault(record, []):
                        found[record].append(where)
    return found


def test_every_record_a_guide_builds_is_read_as_built_by_a_caller(
    reader: cpa.Reader,
) -> None:
    # A guide that builds a record by hand teaches a caller to: what that
    # caller hands it must be converted as for any record a caller builds,
    # so the record is one a public function takes or one CALLER_BUILT names.
    built = cpa.built_records(reader)
    guides = guide_built_records()
    assert guides, "no guide builds a record: the reading of the guides is broken"
    missing = {
        record: pages[:3]
        for record, pages in guides.items()
        if record in reader.annotations.classes and record not in built
    }
    assert missing == {}


def test_the_guide_reading_finds_a_record_built_through_its_domain() -> None:
    guides = guide_built_records()
    # transfer-stiffness.md builds it as vibration.TransferStiffnessResult(...),
    # upgrading.md as room.ImpulseResponseResult(...).
    assert (
        "docs/vibration/structural/transfer-stiffness.md"
        in guides[
            "phonometry.vibration.structural.transfer_stiffness.TransferStiffnessResult"
        ]
    )
    assert (
        "docs/start/upgrading.md"
        in guides["phonometry.room._impulse_response.ImpulseResponseResult"]
    )


def test_the_guide_reading_follows_each_way_of_importing() -> None:
    names: dict[str, str] = {}
    code = textwrap.dedent(
        """
        import phonometry as pm
        import phonometry.room
        from phonometry import vibration as vib
        from phonometry.room import ImpulseResponseResult as IR
        pm.room.ImpulseResponseResult([0.0], 1.0, "mls")
        phonometry.room.ImpulseResponseResult([0.0], 1.0, "mls")
        IR([0.0], 1.0, "mls")
        vib.TransferStiffnessResult([1.0], [1.0])
        print(len([]))
        """
    )
    tree = ast.parse(code)
    _phonometry_names(tree, names)
    calls = [node.func for node in ast.walk(tree) if isinstance(node, ast.Call)]
    found = [_dotted(call, names) for call in calls]
    assert found.count("phonometry.room.ImpulseResponseResult") == 3
    assert "phonometry.vibration.TransferStiffnessResult" in found
    assert found.count(None) == 2  # print and len
    for dotted in filter(None, found):
        assert dataclasses.is_dataclass(_resolved(dotted))


def test_a_stub_exemption_still_covers_a_record_that_converts(
    reader: cpa.Reader,
) -> None:
    for base in cpa.STUB_EXEMPT:
        covered = [
            record
            for record in cpa.built_records(reader)
            if cpa.stub_exemption(reader, record) == base
            and cpa.constructor_problems(reader, record, exempt={})
        ]
        assert covered, f"STUB_EXEMPT lists {base}, which covers no record any more"


def _reader(tmp_path: pathlib.Path, source: str) -> cpa.Reader:
    root = tmp_path / "pkg"
    root.mkdir()
    (root / "__init__.py").write_text("", encoding="utf-8")
    (root / "api.py").write_text(_IMPORTS + textwrap.dedent(source), encoding="utf-8")
    package = overloads.Package(sorted(root.rglob("*.py")), root)
    return cpa.Reader(package, handed_on=frozenset())


_TAKER = """
__all__ = ["Spectrum", "level"]


def level(spectrum: Spectrum) -> float:
    return float(np.max(spectrum.levels))
"""


def test_a_record_that_converts_and_declares_nothing_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    reader = _reader(
        tmp_path,
        _TAKER
        + """

@dataclass(frozen=True, kw_only=True)
class Spectrum:
    levels: NDArray[np.float64]

    def __post_init__(self) -> None:
        object.__setattr__(self, "levels", np.asarray(self.levels, dtype=float))
""",
    )
    assert cpa.constructor_problems(reader, "pkg.api.Spectrum") == [
        "converts levels and declares no TYPE_CHECKING __init__ that says what it takes"
    ]


def test_a_conversion_through_a_setter_or_a_loop_over_the_fields_is_read(
    tmp_path: pathlib.Path,
) -> None:
    reader = _reader(
        tmp_path,
        _TAKER
        + """

@dataclass(frozen=True, kw_only=True)
class Spectrum:
    levels: NDArray[np.float64]
    weights: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        for name in ("levels",):
            self._set(
                name,
                np.asarray(getattr(self, name), dtype=float),
            )
        for each in fields(self):
            object.__setattr__(self, each.name, getattr(self, each.name))

    def _set(self, name: str, value: object) -> None:
        object.__setattr__(self, name, value)
""",
    )
    assert cpa.converted_fields(reader, "pkg.api.Spectrum") == {"levels", "weights"}
    assert cpa.kept_as_given(reader, "pkg.api.Spectrum") == []


def test_a_stub_out_of_step_with_its_fields_is_refused(tmp_path: pathlib.Path) -> None:
    reader = _reader(
        tmp_path,
        _TAKER
        + """

@dataclass(frozen=True)
class Spectrum:
    levels: NDArray[np.float64]
    _: KW_ONLY
    name: str = ""
    bands: Mapping[str, Sequence[float]] = field(default_factory=dict)
    count: int = 1

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            levels: NDArray[np.float64],
            name: str = "x",
            bands: Mapping[str, ArrayLike] = ...,
            count: bool = 1,
        ) -> None: ...

    def __post_init__(self) -> None:
        object.__setattr__(self, "levels", np.asarray(self.levels, dtype=float))
""",
    )
    assert cpa.constructor_problems(reader, "pkg.api.Spectrum") == [
        "levels is a field taken by position, not so in the stub",
        "levels is converted, and the stub takes NDArray[np.float64], which is "
        "no ArrayLike nor an open sequence",
        "name defaults to '' as a field and to 'x' in the stub",
        "count is int as a field and the stub takes bool, which does not take "
        "all of it",
    ]


def test_a_stub_that_drops_a_field_is_refused(tmp_path: pathlib.Path) -> None:
    reader = _reader(
        tmp_path,
        _TAKER
        + """

@dataclass(frozen=True, kw_only=True)
class Spectrum:
    levels: NDArray[np.float64]
    name: str = ""

    if TYPE_CHECKING:

        def __init__(self, *, levels: ArrayLike) -> None: ...

    def __post_init__(self) -> None:
        object.__setattr__(self, "levels", np.asarray(self.levels, dtype=float))
""",
    )
    assert cpa.constructor_problems(reader, "pkg.api.Spectrum") == [
        "its TYPE_CHECKING __init__ takes ['levels'], its fields are ['levels', 'name']"
    ]


def test_a_stub_in_step_with_its_fields_passes(tmp_path: pathlib.Path) -> None:
    reader = _reader(
        tmp_path,
        _TAKER
        + """

@dataclass(frozen=True, kw_only=True)
class Spectrum:
    levels: NDArray[np.float64]
    bands: Mapping[str, Sequence[float]] = field(default_factory=dict)
    count: int = 1

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            levels: ArrayLike,
            bands: Mapping[str, ArrayLike] = ...,
            count: int | np.integer[Any] = 1,
        ) -> None: ...

    def __post_init__(self) -> None:
        object.__setattr__(self, "levels", np.asarray(self.levels, dtype=float))
""",
    )
    assert cpa.constructor_problems(reader, "pkg.api.Spectrum") == []


_FOURTEEN = [f"band_{index}" for index in range(14)]


def _many_fields(
    stub: str, keywords: str = "", required: frozenset[str] = frozenset()
) -> str:
    """A record of fourteen converted fields, with *stub* in its body and *keywords* above it.

    Every field defaults to an empty tuple but the *required* ones.
    """
    fields = "".join(
        f"    {name}: tuple[float, ...]{'' if name in required else ' = ()'}\n"
        for name in _FOURTEEN
    )
    return (
        _TAKER.replace("Spectrum", "Bands").replace(
            "spectrum.levels", "spectrum.band_0"
        )
        + "\n\n"
        + textwrap.dedent(keywords)
        + "\n\n@dataclass(frozen=True, kw_only=True)\nclass Bands:\n"
        + fields
        + "\n"
        + textwrap.indent(textwrap.dedent(stub), "    ")
        + """
    def __post_init__(self) -> None:
        for each in fields(self):
            object.__setattr__(self, each.name, tuple(getattr(self, each.name)))
"""
    )


def test_a_stub_of_more_parameters_than_a_function_takes_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """Fourteen keywords listed one by one are a signature Sonar's S107 refuses."""
    listed = "".join(f"            {name}: ArrayLike = (),\n" for name in _FOURTEEN)
    reader = _reader(
        tmp_path,
        _many_fields(
            "if TYPE_CHECKING:\n\n"
            "    def __init__(\n        self,\n        *,\n"
            + listed.replace("            ", "        ")
            + "    ) -> None: ...\n"
        ),
    )
    assert cpa.constructor_problems(reader, "pkg.api.Bands") == [
        "its TYPE_CHECKING __init__ takes 14 parameters besides self, more than "
        "the 13 a function takes (Sonar S107): it takes them as the keys of a "
        "TypedDict, **keywords: Unpack[...]"
    ]


_KEYWORDS = """
if TYPE_CHECKING:
    from typing import NotRequired, TypedDict, Unpack

    class BandsKeywords(TypedDict, total=False):
{keys}
"""


def _keywords(keys: list[str]) -> str:
    return _KEYWORDS.format(keys="".join(f"        {key}\n" for key in keys))


_TAKES_THE_KEYWORDS = """
if TYPE_CHECKING:

    def __init__(self, **bands: Unpack[BandsKeywords]) -> None: ...
"""


def test_a_stub_that_takes_its_keywords_as_a_typed_dict_passes(
    tmp_path: pathlib.Path,
) -> None:
    """Each key reads as the keyword it stands for, with its field's default."""
    reader = _reader(
        tmp_path,
        _many_fields(
            _TAKES_THE_KEYWORDS,
            _keywords([f"{name}: ArrayLike" for name in _FOURTEEN]),
        ),
    )
    assert cpa.constructor_problems(reader, "pkg.api.Bands") == []
    stub = cpa._constructor_stub(reader.annotations, "pkg.api.Bands")
    assert stub is not None
    assert stub.args.kwarg is None
    assert [argument.arg for argument in stub.args.kwonlyargs] == _FOURTEEN
    assert {ast.unparse(default) for default in stub.args.kw_defaults if default} == {
        "()"
    }


def test_a_typed_dict_out_of_step_with_its_fields_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """A key dropped, a key too narrow, and a key left optional or required against its field."""
    keys = [f"{name}: ArrayLike" for name in _FOURTEEN[:-1]]
    keys[2] = f"{_FOURTEEN[2]}: Required[ArrayLike]"
    reader = _reader(
        tmp_path,
        _many_fields(
            _TAKES_THE_KEYWORDS,
            _keywords(keys).replace("NotRequired,", "NotRequired, Required,"),
        ),
    )
    assert cpa.constructor_problems(reader, "pkg.api.Bands") == [
        f"{_FOURTEEN[2]} is a key a caller must give, and its field defaults to ()",
        f"its TYPE_CHECKING __init__ takes {_FOURTEEN[:-1]}, its fields are "
        f"{_FOURTEEN}",
    ]
    keys = [f"{name}: ArrayLike" for name in _FOURTEEN]
    keys[1] = f"{_FOURTEEN[1]}: tuple[int, ...]"
    (tmp_path / "narrow").mkdir()
    reader = _reader(
        tmp_path / "narrow",
        _many_fields(_TAKES_THE_KEYWORDS, _keywords(keys)),
    )
    assert cpa.constructor_problems(reader, "pkg.api.Bands") == [
        f"{_FOURTEEN[1]} is converted, and the stub takes tuple[int, ...], which is "
        "no ArrayLike nor an open sequence"
    ]
    (tmp_path / "required").mkdir()
    reader = _reader(
        tmp_path / "required",
        _many_fields(
            _TAKES_THE_KEYWORDS,
            _keywords([f"{name}: ArrayLike" for name in _FOURTEEN]),
            required=frozenset({_FOURTEEN[0]}),
        ),
    )
    assert cpa.constructor_problems(reader, "pkg.api.Bands") == [
        f"{_FOURTEEN[0]} is a key a caller may leave out, and its field has no default"
    ]


def test_a_keyword_dictionary_the_reading_cannot_find_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """A ``**`` parameter that unpacks no ``TypedDict`` of the module says nothing of the keys."""
    reader = _reader(
        tmp_path,
        _many_fields(
            "if TYPE_CHECKING:\n\n"
            "    def __init__(self, **bands: ArrayLike) -> None: ...\n"
        ),
    )
    problems = cpa.constructor_problems(reader, "pkg.api.Bands")
    assert problems[0] == (
        "its TYPE_CHECKING __init__ takes **bands: ArrayLike, which is no Unpack "
        "of a TypedDict written in the record's module"
    )


def test_a_pair_of_arrays_takes_one_array_of_two_rows_too(
    tmp_path: pathlib.Path,
) -> None:
    """A stub that takes an open sequence of numbers or arrays takes their array too.

    A field of arrays or of numbers (``tuple[NDArray, NDArray]``, three
    floats) built from any sequence of them is built from an array of them,
    which ``Sequence[ArrayLike]`` alone refuses to a type checker; a stub
    that names its containers (``tuple[int, int] | list[int]``) claims no
    more than it takes, and a field of other objects is no array's rows.
    """
    source = (
        _TAKER
        + """

class Resonator:
    pass


@dataclass(frozen=True, kw_only=True)
class Spectrum:
    levels: tuple[NDArray[np.float64], NDArray[np.float64]]
    thresholds: tuple[float, float, float] = (1.0, 2.0, 3.0)
    resonators: tuple[Resonator, ...] = ()

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            levels: LEVELS,
            thresholds: THRESHOLDS = (1.0, 2.0, 3.0),
            resonators: Sequence[Resonator] = (),
        ) -> None: ...

    def __post_init__(self) -> None:
        first, second = (np.asarray(item, dtype=float) for item in self.levels)
        object.__setattr__(self, "levels", (first, second))
        object.__setattr__(self, "thresholds", tuple(map(float, self.thresholds)))
        object.__setattr__(self, "resonators", tuple(self.resonators))
"""
    )
    narrow = source.replace("LEVELS", "Sequence[ArrayLike]").replace(
        "THRESHOLDS", "Sequence[float]"
    )
    reader = _reader(tmp_path, narrow)
    assert cpa.constructor_problems(reader, "pkg.api.Spectrum") == [
        "levels is converted from numbers or arrays, and the stub takes "
        "Sequence[ArrayLike], an open sequence that refuses the numpy array of "
        "them",
        "thresholds is converted from numbers or arrays, and the stub takes "
        "Sequence[float], an open sequence that refuses the numpy array of them",
    ]
    (tmp_path / "wide").mkdir()
    wide = source.replace("LEVELS", "Sequence[ArrayLike] | NDArray[Any]").replace(
        "THRESHOLDS", "tuple[float, float, float] | list[float]"
    )
    reader = _reader(tmp_path / "wide", wide)
    assert cpa.constructor_problems(reader, "pkg.api.Spectrum") == []


def test_a_mapping_field_nothing_wraps_is_kept_as_given(
    tmp_path: pathlib.Path,
) -> None:
    """A ``dict`` given to a mapping field is the caller's own, edited after the check."""
    reader = _reader(
        tmp_path,
        _TAKER
        + """

Table = dict[str, float]


@dataclass(frozen=True, kw_only=True)
class Spectrum:
    levels: Mapping[str, float]
    extras: Table | None = None
    wrapped: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "wrapped", dict(self.wrapped))
""",
    )
    kept = {
        field.name: written
        for field, written in cpa.kept_as_given(reader, "pkg.api.Spectrum")
    }
    assert kept == {"levels": ["Mapping[str, float]"], "extras": ["dict[str, float]"]}
