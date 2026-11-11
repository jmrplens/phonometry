#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The list of numpy types the package annotates without their type arguments.

``scripts/check_bare_array_annotations.py`` reads every type expression of the
package and reports a numpy array or abstract scalar type written without the
type arguments it takes below numpy 2.3 (``np.ndarray``, ``np.floating``,
``NDArray``), an array whose dtype is left open (``NDArray[Any]``) and
``np.generic`` written elsewhere. These tests fix what it must find, on small
packages written for the purpose, one route at a time (each place a type is
written, each way a name reaches numpy), and what it must let through: a
complete type, a runtime use of a numpy class, a value inside ``Literal``.
"""

from __future__ import annotations

import json
import pathlib
import sys
import textwrap

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_bare_array_annotations as cba
import pytest

_IMPORTS = """
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, Any, Literal, TypeAlias, cast

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray
"""


def _package(tmp_path: pathlib.Path, **modules: str) -> pathlib.Path:
    """Write ``phonometry`` with *modules*, each opened by the shared imports.

    A module named ``__init__`` is written as the package's own, without them.
    """
    root = tmp_path / "phonometry"
    root.mkdir()
    (root / "__init__.py").write_text(
        textwrap.dedent(modules.pop("__init__", "")), encoding="utf-8"
    )
    for name, source in modules.items():
        (root / f"{name}.py").write_text(
            _IMPORTS + textwrap.dedent(source), encoding="utf-8"
        )
    return root


def _found(tmp_path: pathlib.Path, **modules: str) -> set[tuple[str, str, str, str]]:
    """What the check reports, as ``(kind, scope, slot, written)``."""
    root = _package(tmp_path, **modules)
    return {
        (finding.kind, finding.scope, finding.slot, finding.written)
        for finding in cba.findings_in(root)
    }


def test_a_bare_array_in_a_parameter_is_found(tmp_path: pathlib.Path) -> None:
    """The defect the check exists for, named where a reader looks for it."""
    root = _package(
        tmp_path,
        levels="""
        def energy_mean(levels: np.ndarray) -> NDArray[np.float64]:
            return np.asarray(levels, dtype=np.float64)
        """,
    )
    (finding,) = cba.findings_in(root)
    assert finding.kind == "bare"
    assert finding.key == (finding.path, "energy_mean", "parameter levels")
    assert finding.path.endswith("phonometry/levels.py")
    assert finding.line == len(_IMPORTS.splitlines()) + 2
    assert finding.written == "np.ndarray"


def test_the_check_fails_on_a_bare_type(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The check lists a bare type and fails on it, with no option asked."""
    root = _package(
        tmp_path, levels="def energy_mean(levels: np.ndarray) -> float: ...\n"
    )
    assert cba.main(["--root", str(root)]) == 1
    listed = capsys.readouterr().out
    assert "bare: np.ndarray in energy_mean parameter levels" in listed
    assert "1 bare, 0 open and 0 generic" in listed
    assert "::error::1 numpy type(s)" in listed


def test_the_check_takes_no_option_that_turns_the_refusal_off() -> None:
    """A bare type fails every run: no flag of the command line asks for it."""
    with pytest.raises(SystemExit):
        cba.main(["--refuse"])


def test_a_complete_tree_passes_when_the_check_refuses(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _package(
        tmp_path,
        levels="def energy_mean(levels: NDArray[np.float64]) -> float: ...\n",
    )
    assert cba.main(["--root", str(root)]) == 0
    assert "0 bare, 0 open and 0 generic numpy types in 0 files." in (
        capsys.readouterr().out
    )


def test_every_place_a_type_is_written_is_read(tmp_path: pathlib.Path) -> None:
    found = _found(
        tmp_path,
        places="""
        from typing import NewType, TypeVar, assert_type

        Arrays = list[np.ndarray]
        type Grid = np.ndarray
        Table: TypeAlias = dict[str, np.floating]
        _TOP: np.ndarray = np.zeros(1)
        Bounded = TypeVar("Bounded", bound=np.integer)
        Wrapped = NewType("Wrapped", np.ndarray)


        @dataclass
        class Record:
            values: np.ndarray

            def scaled(self, *factors: np.ndarray, **named: np.ndarray) -> Grid:
                held: np.number = self.values[0]
                assert_type(held, np.inexact)
                return cast(np.ndarray, self.values)


        def first[T: np.floating](rows: Arrays, table: Table) -> "np.dtype":
            ...
        """,
    )
    assert found == {
        ("bare", "<module>", "alias Arrays", "np.ndarray"),
        ("bare", "<module>", "alias Grid", "np.ndarray"),
        ("bare", "<module>", "alias Table", "np.floating"),
        ("bare", "<module>", "variable _TOP", "np.ndarray"),
        ("bare", "<module>", "TypeVar Bounded", "np.integer"),
        ("bare", "<module>", "NewType Wrapped", "np.ndarray"),
        ("bare", "Record", "field values", "np.ndarray"),
        ("bare", "Record.scaled", "*factors", "np.ndarray"),
        ("bare", "Record.scaled", "**named", "np.ndarray"),
        ("bare", "Record.scaled", "variable held", "np.number"),
        ("bare", "Record.scaled", "assert_type", "np.inexact"),
        ("bare", "Record.scaled", "cast", "np.ndarray"),
        ("bare", "first", "type parameter T", "np.floating"),
        ("bare", "first", "return", "np.dtype"),
    }


def test_each_bare_type_inside_one_annotation_is_counted(
    tmp_path: pathlib.Path,
) -> None:
    root = _package(
        tmp_path,
        pairs="""
        def pair() -> tuple[np.ndarray, np.ndarray | None]: ...
        def quoted() -> "tuple[np.ndarray, np.ndarray]": ...
        """,
    )
    findings = cba.findings_in(root)
    assert [(f.scope, f.kind) for f in findings] == [("pair", "bare")] * 2 + [
        ("quoted", "bare")
    ] * 2
    assert len({(f.line, f.column) for f in findings}) == len(findings)


def test_complete_types_and_runtime_uses_pass(tmp_path: pathlib.Path) -> None:
    found = _found(
        tmp_path,
        complete="""
        _KINDS = np.floating
        Shape: TypeAlias = tuple[int, ...]


        def complete(
            levels: NDArray[np.float64],
            shaped: np.ndarray[Shape, np.dtype[np.complex128]],
            precision: np.floating[Any] | np.integer[Any] | np.number[Any],
            parts: np.complexfloating[Any, Any],
            items: NDArray[np.floating[Any]],
            choice: Literal["np.ndarray"],
            noted: Annotated[NDArray[np.bool_], np.ndarray],
        ) -> np.dtype[np.float64]:
            if isinstance(levels, np.ndarray) and issubclass(_KINDS, np.generic):
                return np.dtype(np.float64)
            return np.ndarray((2,)).dtype
        """,
    )
    assert found == set()


def test_a_type_argument_missing_below_numpy_2_3_is_bare(
    tmp_path: pathlib.Path,
) -> None:
    """``complexfloating`` takes two there, an array its shape and its dtype."""
    found = _found(
        tmp_path,
        short="""
        def short(z: np.complexfloating[Any], a: np.ndarray[Any]) -> None: ...
        """,
    )
    assert found == {
        ("bare", "short", "parameter z", "np.complexfloating[Any]"),
        ("bare", "short", "parameter a", "np.ndarray[Any]"),
    }


def test_an_open_dtype_is_listed_apart(tmp_path: pathlib.Path) -> None:
    found = _found(
        tmp_path,
        open_="""
        def opened(
            a: NDArray[Any],
            b: np.ndarray[Any, Any],
            c: np.ndarray[tuple[int], np.dtype[Any]],
            d: NDArray[np.generic],
            e: np.dtype[np.generic],
        ) -> None: ...
        """,
    )
    assert found == {
        ("open", "opened", "parameter a", "NDArray[Any]"),
        ("open", "opened", "parameter b", "np.ndarray[Any, Any]"),
        ("open", "opened", "parameter c", "np.dtype[Any]"),
        ("open", "opened", "parameter d", "NDArray[np.generic]"),
        ("open", "opened", "parameter e", "np.dtype[np.generic]"),
    }


def test_generic_elsewhere_is_listed_as_generic(tmp_path: pathlib.Path) -> None:
    found = _found(
        tmp_path,
        generic="""
        def same[T: np.generic](values: NDArray[T], scalar: np.generic) -> T: ...
        """,
    )
    assert found == {
        ("generic", "same", "type parameter T", "np.generic"),
        ("generic", "same", "parameter scalar", "np.generic"),
    }


def test_a_name_is_read_through_the_imports_that_bring_it_in(
    tmp_path: pathlib.Path,
) -> None:
    """Each spelling of numpy's array, and an import inside a function."""
    found = _found(
        tmp_path,
        spelt="""
        import numpy
        import numpy.typing as npt
        from numpy import ndarray as Array


        def spelt(a: numpy.ndarray, b: Array, c: npt.NDArray) -> np.typing.NDArray:
            ...


        def outer() -> None:
            import numpy as xp

            def inner() -> None:
                held: xp.floating = xp.float64(1.0)
        """,
    )
    assert found == {
        ("bare", "spelt", "parameter a", "numpy.ndarray"),
        ("bare", "spelt", "parameter b", "Array"),
        ("bare", "spelt", "parameter c", "npt.NDArray"),
        ("bare", "spelt", "return", "np.typing.NDArray"),
        ("bare", "outer.inner", "variable held", "xp.floating"),
    }


def test_a_class_of_the_package_named_like_numpys_is_not_numpys(
    tmp_path: pathlib.Path,
) -> None:
    found = _found(
        tmp_path,
        own="""
        # The name is the point.
        class ndarray:  # noqa: N801
            pass


        def take(value: ndarray) -> ndarray: ...
        """,
    )
    assert found == set()


def test_an_alias_is_read_once_where_it_is_defined(tmp_path: pathlib.Path) -> None:
    """Followed through a re-export, and reported at its definition alone."""
    found = _found(
        tmp_path,
        __init__="from .kinds import Samples\n",
        kinds="""
        Samples = np.ndarray
        Unused = np.ndarray
        """,
        user="""
        from . import Samples


        def mean(values: Samples) -> Samples: ...
        """,
    )
    assert found == {("bare", "<module>", "alias Samples", "np.ndarray")}


def test_a_union_or_a_subscript_at_the_top_is_an_alias_read_or_not(
    tmp_path: pathlib.Path,
) -> None:
    """As a type checker reads it: a bare name or a tuple is a value until read."""
    found = _found(
        tmp_path,
        held="""
        _REAL = float | np.integer
        _ROWS = list[np.ndarray]
        _KIND = np.floating
        _KINDS = (np.ndarray, np.floating)


        def real(value: object) -> bool:
            return isinstance(value, _REAL | _KIND | _KINDS)
        """,
    )
    assert found == {
        ("bare", "<module>", "alias _REAL", "np.integer"),
        ("bare", "<module>", "alias _ROWS", "np.ndarray"),
    }


def test_an_alias_an_alias_reads_is_read_too(tmp_path: pathlib.Path) -> None:
    found = _found(
        tmp_path,
        chain="""
        Inner = np.floating
        Outer = list[Inner]


        def take(values: Outer) -> None: ...
        """,
    )
    assert found == {("bare", "<module>", "alias Inner", "np.floating")}


def test_naming_a_file_narrows_the_listing(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _package(
        tmp_path,
        one="def one(a: np.ndarray) -> None: ...\n",
        two="def two(a: np.ndarray) -> None: ...\n",
    )
    assert cba.main(["--root", str(root), str(root / "two.py")]) == 1
    listed = capsys.readouterr().out
    assert "two parameter a" in listed
    assert "one parameter a" not in listed
    assert "1 bare, 0 open and 0 generic numpy types in 1 files." in listed


def test_the_findings_are_written_and_counted_by_file(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = _package(
        tmp_path,
        mixed="""
        def mixed(a: np.ndarray, b: NDArray[Any], c: np.generic) -> np.floating: ...
        """,
    )
    written = tmp_path / "findings.json"
    assert cba.main(["--root", str(root), "--json", str(written)]) == 1
    capsys.readouterr()
    rows = json.loads(written.read_text(encoding="utf-8"))
    assert sorted(row["kind"] for row in rows) == ["bare", "bare", "generic", "open"]
    counted = cba.counts(cba.findings_in(root))
    assert list(counted.values()) == [{"bare": 2, "open": 1, "generic": 1}]


@pytest.mark.whole_tree
def test_the_package_writes_no_bare_numpy_type() -> None:
    """Every numpy array and abstract scalar type of the package names its arguments."""
    assert cba.main([]) == 0
