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

class OwnsArrays:
    def __post_init__(self):
        pass

def handed_over(array):
    return array
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
    levels: NDArray[np.float64] | None
    label: str = ""
"""


def _findings(tmp_path: pathlib.Path, **modules: str) -> set[tuple[str, str, str]]:
    """``(function, sink, parameters)`` for a package of the modules given.

    The package is ``pkg`` with the two private helpers above beside the
    modules, so ``from ._internal.frozen import read_only_copy`` reads as it
    does in the tree.
    """
    root = _package(tmp_path, modules)
    found = caa.findings_in(sorted(root.rglob("*.py")), root)
    return {(f.function, f.sink, ", ".join(f.parameters)) for f in found}


def _unequipped(tmp_path: pathlib.Path, **modules: str) -> set[str]:
    """The public records of the package that can hold an array and do not
    inherit ``OwnsArrays``, by qualified class name.
    """
    root = _package(tmp_path, modules)
    found = caa.records_without_mechanism(sorted(root.rglob("*.py")), root)
    return {f.function for f in found}


def _package(tmp_path: pathlib.Path, modules: dict[str, str]) -> pathlib.Path:
    """Write ``pkg`` with the helpers above and *modules*, and return it."""
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
    return root


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
            return BandResult(frequencies=freqs, levels=np.asarray(levels) + 3.0)
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
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {("rating", "BandResult.frequencies", "frequencies")}


def test_a_helper_the_function_defines_itself_is_followed(
    tmp_path: pathlib.Path,
) -> None:
    """A bare name is looked up as Python looks it up: the function first.

    A call through a bare name was looked up in the module alone, so a
    helper written inside the function was followed by no call, and what it
    hands back of the caller's array reached the record unseen.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def rating(frequencies, levels):
            def keep(a):
                return np.asarray(a, dtype=np.float64)

            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {("rating", "BandResult.frequencies", "frequencies")}


def test_every_definition_of_a_name_written_in_two_branches_is_read(
    tmp_path: pathlib.Path,
) -> None:
    """A function written in each branch of an ``if`` is either at run time.

    The functions were kept by their qualified name, so the second
    definition stood for both and the first was never read: the record it
    builds from the caller's own array passed unseen.
    """
    found = _findings(
        tmp_path,
        rating="""
        import sys

        import numpy as np

        from .results import BandResult

        if sys.version_info >= (3, 13):
            def rating(frequencies, levels):
                f = np.asarray(frequencies, dtype=np.float64)
                return BandResult(frequencies=f, levels=f * 0.0)
        else:
            def rating(frequencies, levels):
                f = np.array(frequencies, dtype=np.float64)
                return BandResult(frequencies=f, levels=f * 0.0)

        if sys.version_info >= (3, 13):
            def keep(a):
                return np.array(a)
        else:
            def keep(a):
                return np.asarray(a)

        def kept(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {
        ("rating", "BandResult.frequencies", "frequencies"),
        ("kept", "BandResult.frequencies", "frequencies"),
    }


def test_a_name_the_function_imports_itself_hides_the_module_s(
    tmp_path: pathlib.Path,
) -> None:
    """A name the function binds itself is not the module's function of that name.

    The function imports the validation helper as ``keep``, which hands back
    the caller's array, and the module defines a ``keep`` of its own that
    copies: the call was followed to the module's, and the record seemed to
    keep a copy.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def keep(a):
            return np.array(a)

        def rating(frequencies, levels):
            from ._internal.validation import require_finite_array as keep

            f = keep(frequencies, "frequencies")
            return BandResult(frequencies=f, levels=f * 0.0)

        def copied(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def handed(frequencies, levels, keep):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {("rating", "BandResult.frequencies", "frequencies")}


def test_each_definition_reads_its_own_parameter_annotation(
    tmp_path: pathlib.Path,
) -> None:
    """What a parameter carries is read through the definition's own annotation.

    The shape a record annotation gives a parameter was kept by the
    function's module, name and parameter, so the second of two definitions
    in the branches of an ``if`` took the first's: a parameter annotated
    with a record that keeps the caller's array read as one that copies it,
    and the array handed on to another record passed unseen.
    """
    found = _findings(
        tmp_path,
        combine="""
        import sys
        from dataclasses import dataclass

        import numpy as np

        from ._internal.frozen import read_only_copy

        @dataclass(frozen=True)
        class Sealed:
            data: np.ndarray

            def __post_init__(self):
                object.__setattr__(self, "data", read_only_copy(self.data))

        @dataclass(frozen=True)
        class Loose:
            data: np.ndarray

        @dataclass(frozen=True)
        class Kept:
            data: np.ndarray

        if sys.version_info >= (3, 13):
            def combine(source: Sealed):
                return Kept(data=source.data)
        else:
            def combine(source: Loose):
                return Kept(data=source.data)
        """,
    )
    assert found == {("combine", "Kept.data", "source")}


def test_a_call_reaches_the_definitions_it_can_run(tmp_path: pathlib.Path) -> None:
    """A call is bound to each definition it can reach, with that one's parameters.

    The definitions of one name were summarised together and bound to the
    last one's parameters, so a first definition that hands back its
    argument under another parameter name lost what it carries, and a
    helper written in one branch of a function was read with what the
    helper of the other branch returns, though the call runs only its own.
    """
    found = _findings(
        tmp_path,
        rating="""
        import sys

        import numpy as np

        from .results import BandResult

        if sys.version_info >= (3, 13):
            def keep(a):
                return a
        else:
            def keep(b):
                return np.array(b)

        def kept(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def branched(frequencies, levels, fast):
            if fast:
                def pick(a):
                    return np.array(a)

                f = pick(frequencies)
            else:
                def pick(a):
                    return a

                f = np.array(pick(frequencies))
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {("kept", "BandResult.frequencies", "frequencies")}


def test_a_name_declared_global_or_imported_elsewhere_is_read_as_python_reads_it(
    tmp_path: pathlib.Path,
) -> None:
    """``global`` sends a name to the module, and an import binds it in its scope.

    A name a function declares ``global`` was taken for the function's own
    binding, so a call through it reached no function and the caller's
    array it hands back passed, though a name the function rebinds after
    declaring it ``global`` is what the function put there; a ``nonlocal``
    name stopped the lookup the same way. The imports of a module were read from every node of it, so
    an import written inside one function replaced the module's own import
    of the name for every other function.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from ._internal.frozen import read_only_copy as copied
        from .results import BandResult

        def hand(a):
            from ._internal.validation import require_finite_array

            return require_finite_array(a, "a")

        def through_global(frequencies, levels):
            global hand
            f = hand(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_rebound_global(frequencies, levels):
            global hand
            hand = np.array
            f = hand(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_nonlocal(frequencies, levels):
            def pick(a):
                return a

            def inner():
                nonlocal pick
                return pick(frequencies)

            f = inner()
            return BandResult(frequencies=f, levels=f * 0.0)

        def other(a):
            from ._internal.validation import require_finite_array as copied

            return copied(a, "a")

        def beside_an_import(frequencies, levels):
            f = copied(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {
        ("through_global", "BandResult.frequencies", "frequencies"),
        ("through_nonlocal", "BandResult.frequencies", "frequencies"),
    }


def test_a_helper_with_no_parameter_hands_back_what_its_closure_holds(
    tmp_path: pathlib.Path,
) -> None:
    """A helper written in the function is read with what its closure holds.

    A call of a function written in the caller was read through that
    function's summary, made without its closure, so a helper with no
    parameter that hands back the caller's array was read as returning
    nothing of it, and the record that keeps it passed.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def rating(frequencies, levels):
            def keep():
                return frequencies

            f = keep()
            return BandResult(frequencies=f, levels=f * 0.0)

        def copied(frequencies, levels):
            def keep():
                return np.array(frequencies)

            f = keep()
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {("rating", "BandResult.frequencies", "frequencies")}


def test_a_definition_a_later_one_replaces_is_never_reached(
    tmp_path: pathlib.Path,
) -> None:
    """A call reaches the definition a name holds once the module has run.

    Every definition of a module's name, or of a class's method, was read as
    one the call may run, so a first ``keep`` that hands back its argument,
    replaced by a second that copies it, made the record that keeps the
    result refused for code that never runs. One in each branch of an
    ``if`` is still either.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def keep(a):
            return a

        def keep(a):
            return np.array(a)

        def kept(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        class Builder:
            def pick(self, a):
                return a

            def pick(self, a):
                return np.array(a)

            def build(self, frequencies):
                f = self.pick(frequencies)
                return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == set()


def test_a_call_from_a_function_reaches_every_definition_from_its_def_on(
    tmp_path: pathlib.Path,
) -> None:
    """A function reads the module's names when it is called, which may be
    during the import and before a later definition of a name, so a call in
    it may reach every definition that stands from its ``def`` on.

    ``TABLE = kept(...)`` runs ``kept`` while ``keep`` still hands back its
    argument; the module's names were read as they stand once it has run,
    so only the ``keep`` that copies was reached and the record passed.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def keep(a):
            return a

        def kept(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        TABLE = kept(np.ones(3), np.ones(3))

        def keep(a):
            return np.array(a)
        """,
    )
    assert found == {("kept", "BandResult.frequencies", "frequencies")}


def test_a_method_of_a_class_a_later_class_replaces_is_never_reached(
    tmp_path: pathlib.Path,
) -> None:
    """A method is read in the class that holds it, and a class a later one
    of its name replaces holds none the module keeps.

    The ``keep`` of two ``Bank`` classes were read against each other, and two
    blocks that share nothing keep both, so the first, which hands back its
    argument and which no call reaches, made the record refused.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        class Bank:
            def keep(self, x):
                return x

        class Bank:
            def keep(self, x):
                return x.copy()

            def build(self, frequencies, levels):
                f = self.keep(frequencies)
                return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == set()


def test_what_an_if_type_checking_block_binds_is_no_function_a_call_reaches(
    tmp_path: pathlib.Path,
) -> None:
    """A ``def`` under ``if TYPE_CHECKING:`` never runs, so the helper that
    copies is what the record keeps. It was read as what a function swaps in
    under ``global``, and as either of two beside the block's ``else``, so the
    record that keeps the copy was refused for keeping its argument.
    """
    found = _findings(
        tmp_path,
        rating="""
        from typing import TYPE_CHECKING

        import numpy as np

        from .results import BandResult

        def hand(a):
            return np.array(a)

        def swap():
            global hand
            if TYPE_CHECKING:
                def hand(a):
                    return a

        def rating(frequencies, levels):
            f = hand(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        if TYPE_CHECKING:
            def either(a):
                return a
        else:
            def either(a):
                return np.array(a)

        def rating_either(frequencies, levels):
            f = either(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == set()


_RATING_HEAD = """
from typing import TYPE_CHECKING

import numpy as np

from .results import BandResult
"""


@pytest.mark.parametrize(
    "source",
    [
        pytest.param(
            """
def rating(frequencies, levels):
    f = np.array(frequencies)
    if not TYPE_CHECKING:
        pass
    else:
        f = frequencies
    return BandResult(frequencies=f, levels=f * 0.0)
""",
            id="the-else-of-a-negated-test",
        ),
        pytest.param(
            """
def rating(frequencies, levels):
    f = np.array(frequencies)
    held = frequencies if TYPE_CHECKING else f
    return BandResult(frequencies=held, levels=f * 0.0)
""",
            id="a-branch-of-an-expression",
        ),
        pytest.param(
            """
if TYPE_CHECKING:
    def rating(frequencies, levels):
        return BandResult(frequencies=frequencies, levels=levels)
""",
            id="a-function-in-the-block-at-the-top",
        ),
        pytest.param(
            """
class Rater:
    if TYPE_CHECKING:
        def rating(self, frequencies, levels):
            return BandResult(frequencies=frequencies, levels=levels)
""",
            id="a-method-in-the-block",
        ),
    ],
)
def test_what_a_test_on_type_checking_keeps_from_running_keeps_no_array(
    tmp_path: pathlib.Path, source: str
) -> None:
    """A record no run builds keeps nothing, wherever the block is written."""
    assert _findings(tmp_path, rating=_RATING_HEAD + source) == set()


def test_the_body_of_a_negated_test_keeps_what_it_keeps(
    tmp_path: pathlib.Path,
) -> None:
    """``if not TYPE_CHECKING:`` is what the program runs."""
    found = _findings(
        tmp_path,
        rating=_RATING_HEAD
        + """
def rating(frequencies, levels):
    f = np.array(frequencies)
    if not TYPE_CHECKING:
        f = frequencies
    return BandResult(frequencies=f, levels=f * 0.0)
""",
    )
    assert {function for function, _sink, _parameters in found} == {"rating"}


def test_what_a_function_s_if_type_checking_block_binds_is_not_kept(
    tmp_path: pathlib.Path,
) -> None:
    """The body of an ``if TYPE_CHECKING:`` in a function never runs, so the copy
    is what the record keeps, and the caller's array that body binds is not.
    """
    found = _findings(
        tmp_path,
        rating="""
        from typing import TYPE_CHECKING

        import numpy as np

        from .results import BandResult

        def rating(frequencies, levels):
            f = np.array(frequencies)
            if TYPE_CHECKING:
                f = frequencies
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == set()


def test_a_def_or_an_import_a_function_makes_under_global_may_be_reached(
    tmp_path: pathlib.Path,
) -> None:
    """A function that declares a module name ``global`` and defines or
    imports it there may have run before any call into the module, so a call
    of the name may reach what it bound, as one in a branch of an ``if`` at
    the top may.

    The module's names were read from its top alone, so after ``swap()``
    replaced the ``hand`` that copies with one that hands back its argument,
    the record that keeps the result passed, in the module, through an
    import of the name and through the module's attribute; and so did one
    that keeps what the validation helper ``_swap_in`` imports under
    ``global`` returns.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def hand(a):
            return np.array(a)

        def swap():
            global hand
            def hand(a):
                return a

        def rating(frequencies, levels):
            f = hand(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def check(a):
            return np.array(a, dtype=np.float64)

        def _swap_in():
            global check
            from ._internal.validation import require_finite_array as check

        def checked(frequencies, levels):
            f = check(frequencies, "frequencies")
            return BandResult(frequencies=f, levels=f * 0.0)

        def keep(a):
            return np.array(a)

        def kept(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
        caller="""
        from . import rating as module
        from .rating import hand
        from .results import BandResult

        def through_the_import(frequencies, levels):
            f = hand(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_the_attribute(frequencies, levels):
            f = module.hand(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {
        ("rating", "BandResult.frequencies", "frequencies"),
        ("checked", "BandResult.frequencies", "frequencies"),
        ("through_the_import", "BandResult.frequencies", "frequencies"),
        ("through_the_attribute", "BandResult.frequencies", "frequencies"),
    }


def test_a_name_an_assignment_binds_to_a_function_reaches_that_function(
    tmp_path: pathlib.Path,
) -> None:
    """``alias = handing_back`` binds the name to the function the value
    names, at the top of the module, in a function under ``global`` and in
    the function that calls it, as a ``def`` or an import of it would, and
    so does ``(fn := handing_back)``.

    Only a ``def``, a ``class`` or an import was read as a binding, so a call
    of the name reached the ``def`` the assignment replaced, or nothing at
    all, and a record that keeps what the function hands back passed.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from ._internal import validation
        from .results import BandResult

        def handing_back(a):
            return a

        def hand(a):
            return np.array(a)

        def swap():
            global hand
            hand = handing_back

        def through_global(frequencies, levels):
            f = hand(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def keep(a):
            return np.array(a)

        keep = handing_back

        def through_the_top(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        alias = handing_back
        checked = validation.require_finite_array

        def through_an_alias(frequencies, levels):
            f = alias(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_module(frequencies, levels):
            f = checked(frequencies, "frequencies")
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_local(frequencies, levels):
            fn = handing_back
            f = fn(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_walrus(frequencies, levels):
            if (fn := handing_back) is not None:
                pass
            f = fn(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def copy(a):
            return np.array(a)

        def replaced(frequencies, levels):
            fn = handing_back
            fn = copy
            f = fn(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def unknown(frequencies, levels, fn=copy):
            f = fn(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
        helpers="""
        import numpy as np

        def handing_back(a):
            return a

        keep = handing_back

        def keep(a):
            return np.array(a)

        def kept(a):
            return np.array(a)

        kept = handing_back

        def copying(a):
            return np.array(a)

        def held(a):
            return a

        held = copying
        """,
        importer="""
        from . import helpers
        from .helpers import held, keep, kept
        from .results import BandResult

        def through_a_replaced_def(frequencies, levels):
            f = held(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_replaced_alias(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_replaced_attribute(frequencies, levels):
            f = helpers.keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_standing_alias(frequencies, levels):
            f = kept(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_standing_attribute(frequencies, levels):
            f = helpers.kept(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    # Another module reads the name once the module has run: an alias a
    # later ``def`` replaces, or a ``def`` a later alias replaces, stands
    # for nothing there.
    assert found == {
        ("through_global", "BandResult.frequencies", "frequencies"),
        ("through_the_top", "BandResult.frequencies", "frequencies"),
        ("through_an_alias", "BandResult.frequencies", "frequencies"),
        ("through_a_module", "BandResult.frequencies", "frequencies"),
        ("through_a_local", "BandResult.frequencies", "frequencies"),
        ("through_a_walrus", "BandResult.frequencies", "frequencies"),
        ("through_a_standing_alias", "BandResult.frequencies", "frequencies"),
        ("through_a_standing_attribute", "BandResult.frequencies", "frequencies"),
    }


def test_a_later_binding_of_another_kind_ends_an_alias(
    tmp_path: pathlib.Path,
) -> None:
    """``keep = handing_back`` then ``keep = lambda a: a.copy()`` leaves the
    name holding the lambda, which the guard cannot name, at the top of the
    module and read from another; a loop's target or a call's result ends the
    alias as well.

    Only a ``def``, a ``class``, an import and an alias were read as bindings
    of the top, so the alias stood past the lambda, a call of the name reached
    the function that hands its argument back, and the record that keeps the
    copy was refused.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def handing_back(a):
            return a

        lam = handing_back
        lam = lambda a: np.array(a)

        looped = handing_back
        for looped in [np.copy]:
            pass

        made = handing_back
        made = np.vectorize(np.copy)

        standing = handing_back

        def through_a_lambda(frequencies, levels):
            f = lam(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_loop(frequencies, levels):
            f = looped(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_call(frequencies, levels):
            f = made(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_standing_alias(frequencies, levels):
            f = standing(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
        helpers="""
        def handing_back(a):
            return a

        keep = handing_back
        keep = lambda a: a.copy()
        """,
        importer="""
        from . import helpers
        from .helpers import keep
        from .results import BandResult

        def through_an_import(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_an_attribute(frequencies, levels):
            f = helpers.keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {
        ("through_a_standing_alias", "BandResult.frequencies", "frequencies"),
    }


def test_an_argument_after_a_starred_one_may_reach_any_place_from_its_own_on(
    tmp_path: pathlib.Path,
) -> None:
    """A ``*`` argument unpacks an unknown number of values, so it and every
    argument after it may land in any place from its own on.

    Each argument was bound to the parameter of its index, so with ``rest``
    empty, ``keep(*rest, frequencies)`` handing the caller's array to ``a``,
    which ``keep`` returns, read as handing it to ``b``, and the record that
    keeps the result passed.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def keep(a, b=None):
            return a

        def rating(frequencies, levels):
            rest = []
            f = keep(*rest, frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def placed(frequencies, levels):
            f = keep(np.array(frequencies), frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {("rating", "BandResult.frequencies", "frequencies")}


def test_a_keyword_a_starred_argument_may_leave_to_it_reaches_its_place(
    tmp_path: pathlib.Path,
) -> None:
    """A ``*`` argument may unpack nothing, so a parameter it may fill is one
    ``**options`` may fill too.

    The parameters from the ``*`` argument's place on were read as filled by
    it, so ``keep(*rest, **options)`` with ``rest`` empty and the caller's
    array under ``"a"`` in ``options`` handed nothing of it to ``a``, which
    ``keep`` returns, and the record that keeps the result passed.

    A place an explicit keyword fills is that keyword's alone: were the
    ``*`` argument or the mapping to fill it too, the call would raise, so
    ``a=`` beside ``*rest`` and ``**options`` hands ``a`` the copy only.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def keep(a):
            return a

        def kept(a, b=None):
            return a

        def rating(frequencies, levels):
            rest = []
            options = {"a": frequencies}
            f = keep(*rest, **options)
            return BandResult(frequencies=f, levels=f * 0.0)

        def placed(frequencies, levels):
            options = {"a": frequencies}
            f = keep(np.array(levels), **options)
            return BandResult(frequencies=f, levels=f * 0.0)

        def named(frequencies, levels, rest):
            options = {"b": frequencies}
            f = kept(*rest, a=np.array(levels), **options)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {("rating", "BandResult.frequencies", "frequencies")}


def test_a_keyword_fills_no_positional_only_place(tmp_path: pathlib.Path) -> None:
    """A keyword, or a ``**`` mapping, that names a positional-only parameter
    goes to ``**kwargs``; the place is left to the arguments by place.

    The keyword was read as filling the place, so ``kept(frequencies,
    a=copy)`` and ``kept(*[frequencies], a=copy)``, which return the
    caller's array, read as returning the copy, and the records that keep
    the result passed; a mapping under the parameter's name read as
    reaching it.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def kept(a, /, **kw):
            return a

        def placed(frequencies, levels):
            f = kept(frequencies, a=np.array(levels))
            return BandResult(frequencies=f, levels=f * 0.0)

        def starred(frequencies, levels):
            f = kept(*[frequencies], a=np.array(levels))
            return BandResult(frequencies=f, levels=f * 0.0)

        def mapped(frequencies, levels):
            options = {"a": frequencies}
            f = kept(np.array(levels), **options)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {
        ("placed", "BandResult.frequencies", "frequencies"),
        ("starred", "BandResult.frequencies", "frequencies"),
    }


def test_a_helper_s_type_parameter_is_not_what_its_closure_holds(
    tmp_path: pathlib.Path,
) -> None:
    """A generic helper's type parameter is its own name, so what it returns
    under that spelling is no array of the function around.

    The helper was read with everything its closure holds, the name of its
    type parameter included, so the record that keeps what it returns was
    refused for the caller's array.
    """
    found = _findings(
        tmp_path,
        rating="""
        from .results import BandResult

        def rating(frequencies, levels):
            def hand[frequencies]():
                return frequencies

            f = hand()
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == set()


def test_a_helper_reads_a_sibling_written_after_it(tmp_path: pathlib.Path) -> None:
    """A helper written before the sibling it calls reads what that returns.

    Each helper was read where it is written, so ``hand``, written before
    ``keep``, read ``keep`` as returning nothing, and the caller's array
    ``keep`` hands back through ``hand`` was kept by the record unseen.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def later_sibling(frequencies, levels):
            def hand():
                return keep()

            def keep():
                return frequencies

            f = hand()
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {("later_sibling", "BandResult.frequencies", "frequencies")}


def _chain_of_helpers(count: int) -> str:
    """A function with *count* helpers, each written before the sibling it calls."""
    names = [f"h{index}" for index in range(count)]
    helpers = "".join(
        f"    def {name}():\n        return "
        f"{names[index + 1] + '()' if index + 1 < count else 'frequencies'}\n\n"
        for index, name in enumerate(names)
    )
    return (
        "import numpy as np\n\nfrom .results import BandResult\n\n"
        "def chained(frequencies, levels):\n"
        f"{helpers}"
        "    f = h0()\n"
        "    return BandResult(frequencies=f, levels=f * 0.0)\n"
    )


@pytest.mark.parametrize("count", range(1, 8))
def test_a_chain_of_helpers_of_any_length_is_read_to_its_end(
    tmp_path: pathlib.Path, count: int
) -> None:
    """Each helper written before the sibling it calls is read through.

    The body was read a fixed four times for its helpers to settle, and each
    reading settles one more helper of the chain, so a chain of six helpers or
    more handed the caller's array back unseen.
    """
    found = _findings(tmp_path, rating=textwrap.dedent(_chain_of_helpers(count)))
    assert found == {("chained", "BandResult.frequencies", "frequencies")}


@pytest.mark.parametrize(
    "block",
    [
        "match mode:\n    case 'a':\n{helper}\n    case _:\n{helper}",
        "async with lock:\n{helper}",
        "async for _ in modes:\n{helper}",
        "try:\n{helper}\nexcept* ValueError:\n    pass",
    ],
)
def test_a_helper_written_in_any_compound_statement_is_read(
    tmp_path: pathlib.Path, block: str
) -> None:
    """A function written in a ``case`` of a ``match``, an ``async with``, an
    ``async for`` or a ``try`` with ``except*`` is read as one in an ``if``.

    The functions of a body were collected through ``if``, ``try``, ``with``
    and the loops alone, so a helper written in a ``case`` got no record of
    its own and the call of it reached nothing.
    """
    helper = "        def keep(x):\n            return x"
    written = textwrap.indent(block.format(helper=helper), "    ")
    found = _findings(
        tmp_path,
        rating=(
            "from .results import BandResult\n\n"
            "async def matched(frequencies, levels, mode, lock, modes):\n"
            f"{written}\n"
            "    f = keep(frequencies)\n"
            "    return BandResult(frequencies=f, levels=f * 0.0)\n"
        ),
    )
    assert found == {("matched", "BandResult.frequencies", "frequencies")}


def test_a_call_reaches_a_definition_an_if_may_have_put_before_it(
    tmp_path: pathlib.Path,
) -> None:
    """A helper rebound inside an ``if`` before the call may be the one it runs.

    The call was bound to the last definition written before it in a block
    it sits in alone, so the copying ``pick`` hid the one the ``if`` may
    have put in its place, which hands back the caller's array.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def rebound(frequencies, levels, fast):
            def pick(a):
                return np.array(a)

            if fast:
                def pick(a):
                    return a

            f = pick(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def replaced(frequencies, levels, fast):
            if fast:
                def pick(a):
                    return a

            def pick(a):
                return np.array(a)

            f = pick(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {("rebound", "BandResult.frequencies", "frequencies")}


def test_a_call_reaches_the_import_of_its_own_branch(tmp_path: pathlib.Path) -> None:
    """Two branches that import two helpers under one name each call their own.

    Every call of the name was read through the first import of it in the
    function, so a call in the second branch took the first branch's
    helper: a copy there hid the array the second hands back, and a
    pass-through there refused the copy the second makes.
    """
    found = _findings(
        tmp_path,
        helpers="""
        def passthrough(a):
            return a
        """,
        rating="""
        from .results import BandResult

        def copied_first(frequencies, levels, fast):
            if fast:
                from ._internal.frozen import read_only_copy as pick

                f = pick(frequencies)
            else:
                from .helpers import passthrough as pick

                f = pick(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def passed_first(frequencies, levels, fast):
            if fast:
                from .helpers import passthrough as pick

                return pick(frequencies)
            from ._internal.frozen import read_only_copy as pick

            f = pick(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {("copied_first", "BandResult.frequencies", "frequencies")}


def test_a_helper_hands_back_what_a_sibling_helper_s_closure_holds(
    tmp_path: pathlib.Path,
) -> None:
    """A helper that returns what a sibling helper returns hands back its closure too.

    The sibling was read through its summary, made without its closure, so
    the caller's array it hands back was lost one call down, and the record
    that keeps it passed.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def sibling(frequencies, levels):
            def keep():
                return frequencies

            def hand():
                return keep()

            f = hand()
            return BandResult(frequencies=f, levels=f * 0.0)

        def copied_sibling(frequencies, levels):
            def keep():
                return np.array(frequencies)

            def hand():
                return keep()

            f = hand()
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {("sibling", "BandResult.frequencies", "frequencies")}


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
            return dataclasses.replace(curves, levels=levels * 1.0)
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
            return BandResult(frequencies=read_only_copy(f), levels=f * 0.0)

        def revise(curves: BandResult, levels):
            return dataclasses.replace(
                curves,
                frequencies=read_only_copy(curves.frequencies),
                levels=levels * 1.0,
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
            return BandResult(frequencies=np.arange(3.0), levels={kept})
        """,
    )
    assert found == {("views", "BandResult.levels", "levels")}


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
            return BandResult(frequencies=np.arange(3.0), levels={kept})
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
            return BandResult(frequencies=setup.frequencies, levels=None)
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
            labels = Contributions(parts=tuple((p.label, p.levels * 1.0) for p in paths))
            kept = Contributions(parts=tuple((p.label, p.levels) for p in paths))
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
            return BandResult(frequencies=traverse.positions, levels=traverse.levels)
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
                return BandResult(frequencies=np.arange(3.0), levels=aligned, label=label)

            return build("x")
        """,
    )
    assert found == {("outer.build", "BandResult.levels", "levels")}


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
    """``ANPDatabase`` kept the caller's distances and gave them to its curves.

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
                return BandResult(frequencies=self._distances, levels=self._curves[key])
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
            return BandResult(frequencies=frequencies[_head(3)], levels=None)
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
            return BandResult(frequencies=kept, levels=None)
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
            return BandResult(frequencies=mine["a"], levels=own)
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
            result = BandResult(frequencies=np.arange(3.0), levels=None)
            object.__setattr__(result, "levels", levels)
            object.__setattr__(result, "label", "patched")
            return result
        """,
    )
    assert found == {("patched", "BandResult.levels", "levels")}


# ---------------------------------------------------------------------------
# Records that copy what they are handed
# ---------------------------------------------------------------------------

#: A public record that copies every array it is built with.
_OWNING = """
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ._internal.frozen import OwnsArrays

@dataclass(frozen=True)
class Spectrum(OwnsArrays):
    frequencies: NDArray[np.float64]
    levels: NDArray[np.float64] | None
    columns: dict[str, np.ndarray]
    label: str = ""
"""


def test_a_public_record_that_can_hold_an_array_must_copy_it(
    tmp_path: pathlib.Path,
) -> None:
    """``BandResult``, written by hand, would keep the caller's array.

    No function of the package stands between a caller who builds the record
    and the record, so no trail reaches it: the class itself is refused.
    """
    assert _unequipped(tmp_path) == {"BandResult"}


def test_a_record_that_inherits_the_copy_passes(tmp_path: pathlib.Path) -> None:
    """Directly, or through a record it extends; and a record of numbers, or
    one only a private module holds, needs nothing.
    """
    found = _unequipped(
        tmp_path,
        results="""
        from dataclasses import dataclass

        import numpy as np

        from ._internal.frozen import OwnsArrays

        @dataclass(frozen=True)
        class BandResult(OwnsArrays):
            frequencies: np.ndarray

        @dataclass(frozen=True)
        class Rated(BandResult):
            rating_db: np.ndarray

        @dataclass(frozen=True)
        class Single:
            level: float
            label: str
        """,
        _plumbing="""
        from dataclasses import dataclass

        import numpy as np

        @dataclass(frozen=True)
        class Grid:
            nodes: np.ndarray
        """,
    )
    assert found == set()


def test_a_listed_record_and_a_named_tuple_are_held_to_it(
    tmp_path: pathlib.Path,
) -> None:
    """A record of a private module that a public ``__all__`` lists reaches
    callers; a named tuple cannot inherit the copy and is refused all the same.
    """
    found = _unequipped(
        tmp_path,
        _impl="""
        from dataclasses import dataclass

        import numpy as np

        @dataclass(frozen=True)
        class Listed:
            nodes: np.ndarray
        """,
        api="""
        from typing import NamedTuple

        import numpy as np

        from ._impl import Listed

        __all__ = ["Listed", "Pair"]

        class Pair(NamedTuple):
            frequencies: np.ndarray
            weight: float
        """,
    )
    assert found == {"BandResult", "Listed", "Pair"}


def test_a_record_that_copies_takes_the_caller_s_array_as_it_is(
    tmp_path: pathlib.Path,
) -> None:
    """Every field is the record's own, so a factory hands the array over as
    it is, and what the record's own ``__post_init__`` reads back from
    ``self`` is its copy: sealing it there touches nobody else's array.
    """
    found = _findings(
        tmp_path,
        owning=_OWNING,
        spectra="""
        import dataclasses
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import OwnsArrays, read_only
        from ._internal.validation import require_finite_array
        from .owning import Spectrum

        @dataclass(frozen=True)
        class Coupler(OwnsArrays):
            impedance: NDArray[np.complex128]

            def __post_init__(self):
                column = np.asarray(self.impedance, dtype=np.complex128).reshape(-1)
                object.__setattr__(self, "impedance", read_only(column))

        def spectrum(frequencies, levels):
            f = require_finite_array(frequencies, "frequencies")
            return Spectrum(frequencies=f, levels=levels[:, 0], columns={"a": f})

        def revise(spectrum: Spectrum, levels):
            return dataclasses.replace(spectrum, levels=levels)

        def coupler(impedance):
            return Coupler(impedance=impedance)
        """,
    )
    assert found == set()


@pytest.mark.parametrize(
    "argument",
    [
        "read_only_copy(f)",
        "read_only_copy(f, np.float64)",
        "f.copy()",
        "np.copy(f)",
        "read_only(f.copy())",
        "read_only(np.array(f))",
        "None if f is None else read_only_copy(f)",
        "f.astype(np.float64)",
        "read_only(f.astype(np.float64))",
    ],
)
def test_a_copy_handed_to_a_record_that_copies_is_refused(
    tmp_path: pathlib.Path, argument: str
) -> None:
    """The record copies the array again: the first copy is wasted."""
    found = _findings(
        tmp_path,
        owning=_OWNING,
        spectra=f"""
        import numpy as np

        from ._internal.frozen import read_only, read_only_copy
        from .owning import Spectrum

        def spectrum(f):
            return Spectrum(frequencies={argument}, levels=None, columns={{}})
        """,
    )
    assert found == {("spectrum", "Spectrum.frequencies (copied twice)", "")}


@pytest.mark.parametrize(
    ("field", "argument"),
    [
        ("frequencies", "np.asarray(f, dtype=np.float64)"),
        ("frequencies", "np.array([1.0, 2.0])"),
        ("frequencies", "f"),
        ("frequencies", "f.astype(np.float64, copy=False)"),
        ("columns", "table.copy()"),
    ],
)
def test_a_conversion_or_a_container_s_copy_is_not_a_second_copy(
    tmp_path: pathlib.Path, field: str, argument: str
) -> None:
    """``np.array`` of a list builds the array; a mapping's ``copy`` copies
    the mapping, which the record does not.
    """
    given = {"frequencies": "np.zeros(2)", "levels": "None", "columns": "{}"}
    given[field] = argument
    call = ", ".join(f"{name}={value}" for name, value in given.items())
    found = _findings(
        tmp_path,
        owning=_OWNING,
        spectra=f"""
        import numpy as np

        from .owning import Spectrum

        def spectrum(f, table):
            return Spectrum({call})
        """,
    )
    assert found == set()


#: A helper that only reads what it is handed, and two that write into it:
#: one through a subscript, one through an augmented assignment to the name.
_HELPERS = """
import numpy as np

def check_positive(values, name):
    if np.any(values <= 0.0):
        raise ValueError(f"{name} must be positive: {values}")

def fill_gaps(values):
    values[np.isnan(values)] = 0.0

def shift_in_place(values):
    values += 1.0
    return float(values.sum())
"""


@pytest.mark.parametrize(
    ("bound", "used"),
    [
        ("read_only_copy(x)", "Spectrum(frequencies=f, levels=None, columns={})"),
        (
            "x.copy()",
            "Spectrum(frequencies=read_only(f), levels=f * 2.0, columns={})",
        ),
        (
            "np.copy(x)",
            "Spectrum(frequencies=f, levels=np.log10(f[1:]), columns={})",
        ),
        (
            "x.astype(np.float64)",
            "Spectrum(frequencies=read_only(f), levels=None, columns={})",
        ),
    ],
)
def test_a_copy_bound_to_a_name_and_handed_over_is_refused(
    tmp_path: pathlib.Path, bound: str, used: str
) -> None:
    """The copy is read, checked and handed to a record that copies it again.

    The shape the tree held after the copies at the call were dropped:
    ``f = require_positive_array(...).copy()`` early in the function and
    ``frequencies=read_only(f)`` at the end, with only reads between.
    """
    found = _findings(
        tmp_path,
        owning=_OWNING,
        helpers=_HELPERS,
        spectra=f"""
        import numpy as np

        from ._internal.frozen import read_only, read_only_copy
        from .helpers import check_positive
        from .owning import Spectrum

        def spectrum(x):
            f = {bound}
            check_positive(f, "x")
            if f.size < 2 or f[0] > f[-1]:
                raise ValueError(f"x must ascend: {{f}}")
            return {used}
        """,
    )
    assert found == {("spectrum", "Spectrum.frequencies (copied twice, as f)", "")}


@pytest.mark.parametrize(
    "middle",
    [
        "f[0] = 1.0",
        "f += 1.0",
        "f.sort()",
        "np.copyto(f, x)",
        "np.add.at(f, 0, 1.0)",
        "np.multiply(f, 2.0, out=f)",
        "fill_gaps(f)",
        "shift_in_place(f)",
        "view = f[1:]",
        "kept = [f]",
        "f = x if x.size > 3 else f",
    ],
)
def test_a_copy_the_function_needs_is_not_a_second_copy(
    tmp_path: pathlib.Path, middle: str
) -> None:
    """A copy that something writes into, keeps a view of, or binds again
    is what keeps the caller's array whole: the rule never asks for it to
    be dropped. A helper of the package that writes into its parameter
    counts as writing.
    """
    found = _findings(
        tmp_path,
        owning=_OWNING,
        helpers=_HELPERS,
        spectra=f"""
        import numpy as np

        from .helpers import fill_gaps, shift_in_place
        from .owning import Spectrum

        def spectrum(x):
            f = x.copy()
            {middle}
            return Spectrum(frequencies=f, levels=None, columns={{}})
        """,
    )
    assert found == set()


def test_a_parameter_copied_into_itself_is_not_read_as_a_second_copy(
    tmp_path: pathlib.Path,
) -> None:
    """``x = x.copy()`` binds a parameter: the reading does not vouch for it."""
    found = _findings(
        tmp_path,
        owning=_OWNING,
        spectra="""
        from .owning import Spectrum

        def spectrum(x):
            x = x.copy()
            return Spectrum(frequencies=x, levels=None, columns={})
        """,
    )
    assert found == set()


# ---------------------------------------------------------------------------
# An array handed over to the record without a copy
# ---------------------------------------------------------------------------

#: A record that copies, a record that does not, and helpers that write into
#: their array, keep it or hand it on.
_RUN = """
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ._internal.frozen import OwnsArrays

@dataclass(frozen=True)
class Run(OwnsArrays):
    frames: NDArray[np.float64] | None
    times: NDArray[np.float64]

@dataclass(frozen=True)
class _Plain:
    frames: NDArray[np.float64] | None
    times: NDArray[np.float64]

def write(frames, n):
    if frames is not None:
        frames[0] = 1.0
    for i in range(n):
        frames[i, 0] += 2.0

def write_on(n, *, frames):
    write(frames, n)

def keep(store, frames):
    store.append(frames)

def fill_and_return(frames):
    frames[0] = 1.0
    return frames

def rebind(frames):
    frames = frames[::2]
    frames[0] = 1.0

def write_later(frames):
    frames[0] = 1.0
    yield

def write_deep_1(frames):
    write_deep_2(frames)

def write_deep_2(frames):
    write_deep_3(frames)

def write_deep_3(frames):
    write_deep_4(frames)

def write_deep_4(frames):
    frames[0] = 1.0

_SEEN = []

def remember(function):
    def wrapper(*args):
        _SEEN.append(args)
        return function(*args)
    return wrapper

@remember
def write_remembered(frames):
    frames[0] = 1.0
"""


def _handovers(tmp_path: pathlib.Path, body: str) -> set[tuple[str, str]]:
    """``(function, sink)`` of every handover the check refuses in *body*,
    a module ``sim`` that imports the helpers above.
    """
    source = (
        "import numpy as np\n\n"
        "from ._internal.frozen import handed_over\n"
        "from .run import (\n"
        "    Run, _Plain, fill_and_return, keep, rebind, write, write_deep_1,\n"
        "    write_deep_2, write_later, write_on, write_remembered,\n"
        ")\n" + textwrap.dedent(body)
    )
    root = _package(tmp_path, {"run": _RUN, "sim": source})
    found = caa.handovers_in(sorted(root.rglob("*.py")), root)
    return {(f.function, f.sink) for f in found}


@pytest.mark.parametrize(
    "body",
    [
        # Allocated, written in place, handed to the record returned.
        """
        def run(n):
            frames = np.zeros((n, 3))
            for i in range(n):
                frames[i] = i
                frames[i, 0] += 1.0
            return Run(frames=handed_over(frames), times=np.arange(n))
        """,
        # An optional array, tested against None, written by a helper of the
        # package (by position and by keyword), handed over by position.
        """
        def run(n, every=None):
            frames: np.ndarray | None = (
                None if every is None else np.empty((n, 3), dtype=np.float64)
            )
            if frames is not None:
                frames[0] = 0.0
            write(frames, n)
            write_on(n, frames=frames)
            return Run(handed_over(frames), np.arange(n))
        """,
        # Down three helpers, each only passing it on or writing into it.
        """
        def run(n):
            frames = np.ones((n, 3))
            write_deep_2(frames)
            return Run(frames=handed_over(frames), times=np.arange(n))
        """,
        # A comprehension, a lambda and a nested function each keep a
        # variable of the same spelling for themselves: Python keeps them
        # apart from the array.
        """
        def run(n):
            frames = np.zeros((n, 3))
            labels = [str(frames) for frames in range(n)]
            show = lambda frames: str(frames)

            def count():
                frames = len(labels)
                return frames

            show(count())
            return Run(frames=handed_over(frames), times=np.arange(n))
        """,
    ],
    ids=[
        "written-in-place",
        "optional-written-by-helpers",
        "three-helpers-deep",
        "same-name-in-other-scopes",
    ],
)
def test_an_array_nothing_else_can_reach_may_be_handed_over(
    tmp_path: pathlib.Path, body: str
) -> None:
    """The shape of the simulation factories: one allocation, writes into
    it there or in a helper, and the record that keeps it as the return.
    """
    assert _handovers(tmp_path, body) == set()


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        (
            """
            def run(frames):
                return Run(frames=handed_over(frames), times=np.arange(3))
            """,
            "frames is a parameter",
        ),
        (
            """
            from . import _internal

            def run(frames):
                return Run(
                    frames=_internal.frozen.handed_over(frames), times=np.arange(3)
                )
            """,
            "frames is a parameter",
        ),
        (
            """
            import pkg._internal.frozen

            def run(frames):
                return Run(
                    frames=pkg._internal.frozen.handed_over(frames),
                    times=np.arange(3),
                )
            """,
            "frames is a parameter",
        ),
        (
            """
            def run(x):
                frames = np.asarray(x)
                return Run(frames=handed_over(frames), times=np.arange(3))
            """,
            "frames is not bound once",
        ),
        (
            """
            def run(x):
                frames = np.zeros(3)
                frames = np.zeros(4)
                return Run(frames=handed_over(frames), times=np.arange(3))
            """,
            "frames is not bound once",
        ),
        (
            """
            def run(x):
                kept = frames = np.zeros(3)
                return Run(frames=handed_over(frames), times=kept)
            """,
            "frames is not bound once",
        ),
        (
            """
            def run(x):
                for frames in (np.zeros(3),):
                    pass
                return Run(frames=handed_over(frames), times=np.arange(3))
            """,
            "frames is not bound once",
        ),
        (
            """
            def run(x):
                def build():
                    frames = np.zeros(3)
                    return frames
                return Run(frames=handed_over(frames), times=build())
            """,
            "frames is not bound once",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))

                def swap():
                    nonlocal frames
                    frames = np.ones(3)

                swap()
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "frames is not bound once",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                rows = [frames for _ in range(n)]
                return Run(frames=handed_over(frames), times=rows)
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                first = frames[0]
                return Run(frames=handed_over(frames), times=first)
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                return Run(frames=handed_over(frames), times=frames.T)
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                frames[0][1] = 2.0
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n, store):
                frames = np.zeros((n, 3))
                keep(store, frames)
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                times = fill_and_return(frames)
                return Run(frames=handed_over(frames), times=times)
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                rebind(frames)
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                list(write_later(frames))
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                write_deep_1(frames)
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                write_remembered(frames)
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                return Run(frames=handed_over(frames), times=handed_over(frames))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n, hooks):
                frames = np.zeros((n, 3))
                def peek():
                    frames[0] = 1.0
                hooks.append(peek)
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n, hooks):
                frames = np.zeros((n, 3))
                hooks.append(lambda: frames)
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                rows = [frames[i] for i in range(n)]
                return Run(frames=handed_over(frames), times=np.asarray(rows))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n, cache):
                frames = np.zeros((n, 3))
                cache.update(locals())
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "the function can reach its own frame",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                yield n
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "the function can reach its own frame",
        ),
        (
            """
            def run(n, seen):
                frames = np.zeros((n, 3))
                if frames in seen:
                    raise ValueError(n)
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                result = Run(frames=handed_over(frames), times=np.arange(n))
                return result
            """,
            "the record is not built in the return statement",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                return _Plain(frames=handed_over(frames), times=np.arange(n))
            """,
            "it is not an argument of a record that inherits OwnsArrays",
        ),
        (
            """
            def run(n):
                frames = handed_over(np.zeros((n, 3)))
                return Run(frames=frames, times=np.arange(n))
            """,
            "it is not an argument of a record",
        ),
        (
            """
            def run(n):
                return Run(frames=handed_over(np.zeros((n, 3))), times=np.arange(n))
            """,
            "its argument is not a name",
        ),
    ],
    ids=[
        "parameter",
        "dotted-path",
        "absolute-dotted-path",
        "not-allocated",
        "bound-twice",
        "second-name",
        "loop-target",
        "bound-in-nested-scope",
        "rebound-nonlocal",
        "kept-by-a-comprehension",
        "view-kept",
        "transpose-kept",
        "view-written",
        "helper-keeps",
        "helper-returns",
        "helper-rebinds",
        "helper-generator",
        "four-helpers-deep",
        "decorated-helper",
        "handed-twice",
        "closure",
        "lambda",
        "comprehension",
        "locals",
        "generator",
        "membership-test",
        "record-not-returned",
        "record-without-mechanism",
        "outside-record",
        "not-a-name",
    ],
)
def test_an_array_something_else_may_reach_is_refused(
    tmp_path: pathlib.Path, body: str, reason: str
) -> None:
    """A parameter, a view, a second name, a helper that keeps or returns it
    or binds it again, a helper behind a decorator, a closure, a frame the
    function hands out, and a record that is not what the function returns:
    in each the record would not be the only one to hold the array it keeps
    without a copy. The function is found however it is spelt, a dotted path
    to its module included.
    """
    found = _handovers(tmp_path, body)
    assert len(found) == 1, found
    ((function, sink),) = found
    assert function == "run"
    assert sink.startswith("handed_over(...): " + reason), sink


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        ("KEPT = handed_over(np.zeros(3))\n", "it is not called in a function"),
        ("hand = handed_over\n", "the function is named where it is not called"),
        (
            "def run(n):\n"
            "    make = lambda frames: Run(frames=handed_over(frames), times=frames)\n"
            "    return make(np.zeros(n))\n",
            "it is not called in a function",
        ),
        (
            "from ._internal import frozen\n\n"
            "def run(frames):\n"
            "    hand = getattr(frozen, 'handed_over')\n"
            "    return Run(frames=hand(frames), times=np.arange(3))\n",
            "the function is named where it is not called",
        ),
    ],
    ids=["module-level", "named-not-called", "in-a-lambda", "named-in-a-string"],
)
def test_the_handover_named_outside_a_function_is_refused(
    tmp_path: pathlib.Path, body: str, reason: str
) -> None:
    """At module level, in a lambda, or the function passed around under
    another name or fetched by its name as a string, nothing can be proved
    of what it is handed.
    """
    found = _handovers(tmp_path, body)
    assert {sink for _, sink in found} == {"handed_over(...): " + reason}


def test_a_record_exemption_silences_its_class_and_goes_stale_without_it(
    tmp_path: pathlib.Path,
) -> None:
    root = _package(tmp_path, {})
    found = caa.records_without_mechanism(sorted(root.rglob("*.py")), root)
    key = (found[0].path, "BandResult")
    left, stale = ast_scan.exempted(found, {key: "reason"})
    assert (left, stale) == ([], [])
    left, stale = ast_scan.exempted([], {key: "reason"})
    assert stale == [key]


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


def test_a_numpy_scalar_class_written_with_its_argument_is_one_number() -> None:
    """``np.integer[Any]`` is a count numpy code hands over, not the ``Any`` of an array."""
    assert not caa.holds_array("int | np.integer[Any]")
    assert not caa.holds_array("float | np.floating[Any] | None")
    assert not caa.holds_array("BandFraction | numpy.integer[Any]")
    assert caa.holds_array("np.ndarray | np.integer[Any]")
    assert caa.holds_array("Mapping[str, Any]")
    assert caa.holds_array("Any")
