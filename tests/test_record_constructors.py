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
sequence and every other one taking all its field's annotation names. The
first test holds the package to that; the others fix what the reading must
catch on small packages written for the purpose.
"""

from __future__ import annotations

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
