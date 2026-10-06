#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate on results that keep the caller's array instead of a copy.

``scripts/check_array_aliasing.py`` follows every parameter of every function
of the package to the places an array is kept. Its own run only says the tree
is clean today; these tests fix what it must catch, on small packages written
for the purpose. The defects are here in the shapes the tree held them in:
the ISO 3743 helper that read the band frequencies with ``np.asarray``, the
validation helper whose return is the caller's array, the coupler record that
cleared the writeable flag on the caller's own columns, and the copy of a
caller's record made with ``dataclasses.replace``. So are the shapes it must
leave alone, because a gate that refuses ``levels[levels > 0]`` or
``levels - 10.0`` would be switched off within a week.
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import ast_scan
import check_array_aliasing as caa

#: The helpers every package below imports, as the real one spells them.
_FROZEN = """
import numpy as np

def read_only(array):
    array.flags.writeable = False
    return array

def read_only_copy(array, dtype=None):
    if array is None:
        return None
    return read_only(np.array(array, dtype=dtype))
"""

#: A validation helper of the kind ``_internal/validation.py`` holds: its
#: return is the caller's array whenever that is already ``float64``.
_VALIDATION = """
import numpy as np

def require_finite_array(x, name):
    arr = np.atleast_1d(np.asarray(x, dtype=np.float64))
    if not np.all(np.isfinite(arr)):
        raise ValueError(name)
    return arr
"""

_RESULT = """
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

@dataclass(frozen=True)
class BandResult:
    frequencies: NDArray[np.float64]
    levels_db: NDArray[np.float64] | None
    label: str = ""
"""


def _findings(tmp_path: pathlib.Path, **modules: str) -> set[tuple[str, str, str]]:
    """``(function, sink, parameters)`` for a package of the modules given.

    The package is ``pkg`` with the two private helpers above beside the
    modules, so ``from ._internal.frozen import read_only_copy`` reads as it
    does in the tree.
    """
    root = tmp_path / "pkg"
    files = {
        "__init__.py": "",
        "_internal/__init__.py": "",
        "_internal/frozen.py": _FROZEN,
        "_internal/validation.py": _VALIDATION,
        "results.py": _RESULT,
        **{f"{name}.py": source for name, source in modules.items()},
    }
    for name, source in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(source), encoding="utf-8")
    found = caa.findings_in(sorted(root.rglob("*.py")), root)
    return {(f.function, f.sink, ", ".join(f.parameters)) for f in found}


# ---------------------------------------------------------------------------
# The defects, as the tree held them
# ---------------------------------------------------------------------------


def test_the_iso_3743_helper_before_its_fix_is_refused(tmp_path: pathlib.Path) -> None:
    """``_octave_frequencies`` read the bands with ``np.asarray`` (#915)."""
    found = _findings(
        tmp_path,
        power="""
        import numpy as np

        from .results import BandResult

        def _octave_frequencies(frequencies, n_bands):
            freqs = np.asarray(frequencies, dtype=np.float64)
            if freqs.shape != (n_bands,):
                raise ValueError("frequencies")
            return freqs

        def sound_power(levels, frequencies):
            freqs = _octave_frequencies(frequencies, len(levels))
            return BandResult(frequencies=freqs, levels_db=np.asarray(levels) + 3.0)
        """,
    )
    assert found == {("sound_power", "BandResult.frequencies", "frequencies")}


def test_a_validation_helper_carries_the_caller_s_array(tmp_path: pathlib.Path) -> None:
    """The helper's return is summarised once, and every caller inherits it."""
    found = _findings(
        tmp_path,
        rating="""
        from ._internal.validation import require_finite_array
        from .results import BandResult

        def rating(frequencies, levels):
            f = require_finite_array(frequencies, "frequencies")
            return BandResult(frequencies=f, levels_db=f * 0.0)
        """,
    )
    assert found == {("rating", "BandResult.frequencies", "frequencies")}


def test_a_record_that_freezes_the_caller_s_column_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """``read_only`` on a normalised field clears the flag on the caller's own
    array: the coupler record of IEC 61094-2 did it to three columns.
    """
    found = _findings(
        tmp_path,
        coupler="""
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import read_only

        @dataclass(frozen=True)
        class Coupler:
            impedance: NDArray[np.complex128]

            def __post_init__(self):
                column = np.asarray(self.impedance, dtype=np.complex128).reshape(-1)
                object.__setattr__(self, "impedance", read_only(column))
        """,
    )
    assert found == {
        ("Coupler.__post_init__", "Coupler.impedance", "self.impedance"),
        ("Coupler.__post_init__", "read_only(...)", "self.impedance"),
    }


def test_a_record_copied_with_replace_keeps_the_caller_s_axes(
    tmp_path: pathlib.Path,
) -> None:
    """``dataclasses.replace`` carries over every field it is not given."""
    found = _findings(
        tmp_path,
        curves="""
        import dataclasses

        from .results import BandResult

        def revise(curves: BandResult, levels):
            return dataclasses.replace(curves, levels_db=levels * 1.0)
        """,
    )
    assert found == {
        ("revise", "BandResult.frequencies (kept by replace)", "curves"),
    }


# ---------------------------------------------------------------------------
# The fixes pass
# ---------------------------------------------------------------------------


def test_the_fixes_pass(tmp_path: pathlib.Path) -> None:
    """A copy of its own, made read only, ends every trail above."""
    found = _findings(
        tmp_path,
        fixed="""
        import dataclasses
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import read_only, read_only_copy
        from ._internal.validation import require_finite_array
        from .results import BandResult

        def rating(frequencies, levels):
            f = require_finite_array(frequencies, "frequencies")
            return BandResult(frequencies=read_only_copy(f), levels_db=f * 0.0)

        def revise(curves: BandResult, levels):
            return dataclasses.replace(
                curves,
                frequencies=read_only_copy(curves.frequencies),
                levels_db=levels * 1.0,
            )

        @dataclass(frozen=True)
        class Coupler:
            impedance: NDArray[np.complex128]

            def __post_init__(self):
                column = np.asarray(self.impedance, dtype=np.complex128).reshape(-1)
                object.__setattr__(self, "impedance", read_only(column.copy()))

        def coupler(impedance):
            return Coupler(impedance=np.asarray(impedance))
        """,
    )
    assert found == set()


# ---------------------------------------------------------------------------
# The rule, case by case
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "kept",
    [
        "levels",
        "np.asarray(levels)",
        "np.atleast_2d(levels)[:, 0]",
        "levels.T",
        "levels.reshape(-1)",
        "np.ravel(levels)",
        "levels[1:]",
        "levels if levels.ndim else None",
    ],
)
def test_the_caller_s_array_or_a_view_of_it_is_refused(
    tmp_path: pathlib.Path, kept: str
) -> None:
    found = _findings(
        tmp_path,
        views=f"""
        import numpy as np

        from .results import BandResult

        def views(levels):
            return BandResult(frequencies=np.arange(3.0), levels_db={kept})
        """,
    )
    assert found == {("views", "BandResult.levels_db", "levels")}


@pytest.mark.parametrize(
    "kept",
    [
        "levels - 10.0",
        "np.array(levels)",
        "levels.copy()",
        "levels.astype(float)",
        "levels[levels > 0.0]",
        "np.asarray([levels, levels])",
        "None",
    ],
)
def test_a_new_array_passes(tmp_path: pathlib.Path, kept: str) -> None:
    """Arithmetic, a copy, a mask or a stack is an array of the result's own."""
    found = _findings(
        tmp_path,
        fresh=f"""
        import numpy as np

        from .results import BandResult

        def fresh(levels):
            return BandResult(frequencies=np.arange(3.0), levels_db={kept})
        """,
    )
    assert found == set()


def test_a_scalar_field_is_not_an_array(tmp_path: pathlib.Path) -> None:
    """Only a field that can hold an array is a place an array is kept."""
    found = _findings(
        tmp_path,
        named="""
        import numpy as np

        from .results import BandResult

        def named(levels, label):
            return BandResult(np.arange(3.0), None, label)
        """,
    )
    assert found == set()


def test_a_private_record_carries_what_it_was_given(tmp_path: pathlib.Path) -> None:
    """A private record is plumbing, but what it carries reaches the result."""
    found = _findings(
        tmp_path,
        plumbing="""
        from dataclasses import dataclass

        import numpy as np

        from .results import BandResult

        @dataclass(frozen=True)
        class _Setup:
            frequencies: np.ndarray
            scale: float

        def _setup(frequencies):
            return _Setup(frequencies=np.asarray(frequencies), scale=2.0)

        def predict(frequencies):
            setup = _setup(frequencies)
            return BandResult(frequencies=setup.frequencies, levels_db=None)
        """,
    )
    assert found == {("predict", "BandResult.frequencies", "frequencies")}


def test_a_record_parameter_s_text_fields_are_not_arrays(
    tmp_path: pathlib.Path,
) -> None:
    """A parameter annotated with a record is read field by field."""
    found = _findings(
        tmp_path,
        combine="""
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from .results import BandResult

        @dataclass(frozen=True)
        class Contributions:
            parts: tuple[tuple[str, NDArray[np.float64]], ...]

        def combine(paths: list[BandResult]):
            labels = Contributions(parts=tuple((p.label, p.levels_db * 1.0) for p in paths))
            kept = Contributions(parts=tuple((p.label, p.levels_db) for p in paths))
            return labels, kept
        """,
    )
    assert found == {("combine", "Contributions.parts", "paths")}


def test_a_field_the_record_copies_itself_needs_no_copy_at_the_factory(
    tmp_path: pathlib.Path,
) -> None:
    """A record whose ``__post_init__`` copies a field owns it, whoever builds it."""
    found = _findings(
        tmp_path,
        owned="""
        from dataclasses import dataclass

        import numpy as np

        from ._internal.frozen import read_only_copy

        @dataclass(frozen=True)
        class Owned:
            data: np.ndarray
            other: np.ndarray

            def __post_init__(self):
                object.__setattr__(self, "data", read_only_copy(self.data))

        def build(data, other):
            return Owned(data=data, other=other)
        """,
    )
    assert found == {("build", "Owned.other", "other")}


def test_a_record_s_writeable_copy_is_still_the_caller_s_to_edit(
    tmp_path: pathlib.Path,
) -> None:
    """A record that copies a field but leaves it writeable hands a later
    result an array its caller can still edit, through the record; one that
    seals its copy read-only does not.
    """
    found = _findings(
        tmp_path,
        traverse="""
        from dataclasses import dataclass

        import numpy as np

        from ._internal.frozen import read_only_copy
        from .results import BandResult

        @dataclass(frozen=True)
        class Traverse:
            positions: np.ndarray
            levels: np.ndarray

            def __post_init__(self):
                object.__setattr__(self, "positions", np.array(self.positions))
                object.__setattr__(self, "levels", read_only_copy(self.levels))

        def deviations(traverse: Traverse):
            return BandResult(frequencies=traverse.positions, levels_db=traverse.levels)
        """,
    )
    assert found == {("deviations", "BandResult.frequencies", "traverse")}


def test_read_only_on_an_argument_is_refused_anywhere(tmp_path: pathlib.Path) -> None:
    """It would clear the flag on the caller's own array."""
    found = _findings(
        tmp_path,
        freeze="""
        import numpy as np

        from ._internal.frozen import read_only

        def freeze(levels):
            return read_only(np.asarray(levels, dtype=np.float64))
        """,
    )
    assert found == {("freeze", "read_only(...)", "levels")}


def test_a_nested_function_sees_the_arrays_of_its_closure(
    tmp_path: pathlib.Path,
) -> None:
    found = _findings(
        tmp_path,
        closure="""
        import numpy as np

        from .results import BandResult

        def outer(levels):
            aligned = np.asarray(levels)

            def build(label):
                return BandResult(frequencies=np.arange(3.0), levels_db=aligned, label=label)

            return build("x")
        """,
    )
    assert found == {("outer.build", "BandResult.levels_db", "levels")}


def test_a_plain_class_keeps_an_annotated_attribute(tmp_path: pathlib.Path) -> None:
    found = _findings(
        tmp_path,
        bank="""
        import numpy as np

        class Bank:
            sos: np.ndarray
            fs: float

            def __init__(self, sos, fs):
                self.sos = np.asarray(sos)
                self.fs = fs
        """,
    )
    assert found == {("Bank.__init__", "self.sos", "sos")}


@pytest.mark.parametrize(
    ("init", "attribute"),
    [
        ("self.sos = np.asarray(sos)", "self.sos"),
        ("self._sos = sos", "self._sos"),
        ("self._sos: np.ndarray = np.atleast_2d(sos)", "self._sos"),
        ("self._sections = [sos]", "self._sections"),
    ],
)
def test_a_plain_class_keeps_an_unannotated_attribute(
    tmp_path: pathlib.Path, init: str, attribute: str
) -> None:
    """No class-level annotation is needed: the parameter's own decides.

    ``SilencerChain`` kept the caller's frequency grid as ``self._frequencies``
    behind a ``frequencies`` property, and nothing in its class body said
    the attribute was an array.
    """
    found = _findings(
        tmp_path,
        bank=f"""
        import numpy as np

        class Bank:
            def __init__(self, sos, fs: float):
                {init}
                self.fs = fs

            @property
            def sos(self):
                return self._sos
        """,
    )
    assert found == {("Bank.__init__", attribute, "sos")}


def test_a_plain_class_reads_its_parameter_s_annotation(
    tmp_path: pathlib.Path,
) -> None:
    """A float parameter is not an array; one typed through an alias is.

    ``FDTD2D`` takes ``c: float | Field2D``, where ``Field2D`` is a module
    alias of ``NDArray[np.float64]``.
    """
    found = _findings(
        tmp_path,
        grid="""
        import numpy as np
        from numpy.typing import NDArray

        Field2D = NDArray[np.float64]

        class Grid:
            def __init__(self, c: float | Field2D, dx: float, label: str):
                self.c = np.asarray(c, dtype=np.float64)
                self.dx = dx
                self.label = label
        """,
    )
    assert found == {("Grid.__init__", "self.c", "c")}


def test_a_database_that_hands_out_its_constructor_s_arrays_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """``AnpDatabase`` kept the caller's distances and gave them to its curves.

    The record is built in a method, from ``self``; the array is caught where
    the constructor kept it.
    """
    found = _findings(
        tmp_path,
        database="""
        import numpy as np

        from .results import BandResult

        class Database:
            def __init__(self, curves, distances):
                self._curves = dict(curves)
                self._distances = distances

            def curve(self, key):
                return BandResult(frequencies=self._distances, levels_db=self._curves[key])
        """,
    )
    assert found == {
        ("Database.__init__", "self._curves", "curves"),
        ("Database.__init__", "self._distances", "distances"),
    }


def test_a_plain_class_that_files_the_caller_s_array_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """``self.items.append(x)`` keeps x as surely as ``self.x = x`` does.

    A record that holds no array, like an FDTD source, is not one.
    """
    found = _findings(
        tmp_path,
        chain="""
        from dataclasses import dataclass

        import numpy as np

        @dataclass(frozen=True)
        class Element:
            label: str
            length: float

        class Chain:
            def __init__(self):
                self._layers: list[np.ndarray] = []
                self._elements: list[Element] = []
                self._named: dict[str, np.ndarray] = {}

            def layer(self, levels):
                self._layers.append(np.asarray(levels))

            def element(self, element: Element):
                self._elements.append(element)

            def name(self, key: str, levels):
                self._named[key] = levels
        """,
    )
    assert found == {
        ("Chain.layer", "self._layers.append(...)", "levels"),
        ("Chain.name", "self._named[...]", "levels"),
    }


def _indexed_by_helper(
    tmp_path: pathlib.Path, helper: str
) -> set[tuple[str, str, str]]:
    """The findings of a factory that indexes its argument with a helper."""
    return _findings(
        tmp_path,
        head=f"""
        import numpy as np

        from .results import BandResult

        def _head(n):
            {helper}

        def head(frequencies):
            return BandResult(frequencies=frequencies[_head(3)], levels_db=None)
        """,
    )


def test_a_helper_that_returns_a_slice_selects_a_view(tmp_path: pathlib.Path) -> None:
    """A private helper used as an index is read, not trusted to copy."""
    found = _indexed_by_helper(tmp_path, "return slice(0, n)")
    assert found == {("head", "BandResult.frequencies", "frequencies")}


@pytest.mark.parametrize(
    "helper",
    [
        "return np.arange(n)",
        "return np.asarray([i for i in range(n)], dtype=np.intp)",
        "return np.arange(5) < n",
    ],
)
def test_a_helper_that_returns_positions_selects_a_copy(
    tmp_path: pathlib.Path, helper: str
) -> None:
    assert _indexed_by_helper(tmp_path, helper) == set()


@pytest.mark.parametrize(
    "body",
    [
        "kept = dict(bands).copy()['a']",
        "kept = np.diag(bands)",
        "kept = np.trim_zeros(bands)",
    ],
)
def test_a_shallow_copy_or_a_numpy_view_is_refused(
    tmp_path: pathlib.Path, body: str
) -> None:
    """A mapping's ``copy`` keeps its arrays; ``np.diag`` of a matrix is a view."""
    found = _findings(
        tmp_path,
        shallow=f"""
        import numpy as np

        from .results import BandResult

        def shallow(bands):
            {body}
            return BandResult(frequencies=kept, levels_db=None)
        """,
    )
    assert found == {("shallow", "BandResult.frequencies", "bands")}


def test_a_mapping_parameter_s_copy_keeps_its_arrays(tmp_path: pathlib.Path) -> None:
    found = _findings(
        tmp_path,
        mapping="""
        from collections.abc import Mapping

        import numpy as np

        from .results import BandResult

        def mapping(bands: Mapping[str, np.ndarray], levels: np.ndarray):
            own = levels.copy()
            mine = bands.copy()
            return BandResult(frequencies=mine["a"], levels_db=own)
        """,
    )
    assert found == {("mapping", "BandResult.frequencies", "bands")}


def test_a_field_patched_in_a_factory_is_refused(tmp_path: pathlib.Path) -> None:
    """``object.__setattr__`` on a record just built keeps what it is given."""
    found = _findings(
        tmp_path,
        patched="""
        import numpy as np

        from .results import BandResult

        def patched(levels):
            result = BandResult(frequencies=np.arange(3.0), levels_db=None)
            object.__setattr__(result, "levels_db", levels)
            object.__setattr__(result, "label", "patched")
            return result
        """,
    )
    assert found == {("patched", "BandResult.levels_db", "levels")}


def test_an_exemption_silences_its_function_and_goes_stale_without_it(
    tmp_path: pathlib.Path,
) -> None:
    root = tmp_path / "pkg"
    root.mkdir()
    path = root / "keep.py"
    path.write_text(
        textwrap.dedent(
            """
            from dataclasses import dataclass

            import numpy as np

            @dataclass(frozen=True)
            class Kept:
                data: np.ndarray

            def keep(data):
                return Kept(data=data)
            """
        ),
        encoding="utf-8",
    )
    found = caa.findings_in([path], root)
    key = (found[0].path, "keep")
    left, stale = ast_scan.exempted(found, {key: "reason"})
    assert (left, stale) == ([], [])
    left, stale = ast_scan.exempted([], {key: "reason"})
    assert stale == [key]


def test_the_tree_passes(capsys: pytest.CaptureFixture[str]) -> None:
    status = caa.main([])
    assert status == 0, capsys.readouterr().out
