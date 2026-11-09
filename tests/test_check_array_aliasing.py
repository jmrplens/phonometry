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
from typing import TYPE_CHECKING

import guard_caches
import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import ast_scan
import check_array_aliasing as caa

if TYPE_CHECKING:
    from collections.abc import Iterator


#: The tests that read the whole package share what the guard keeps of it, so
#: they run on one worker (rule T19), and the guard lets it go after them.
pytestmark = pytest.mark.xdist_group("array-aliasing")


@pytest.fixture(scope="module", autouse=True)
def _forget_the_guard() -> Iterator[None]:
    """Let go of what the guard read once this module's tests are done."""
    yield
    guard_caches.forget(caa)


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
    module and read from another; a call's result ends the alias as well.

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

        made = handing_back
        made = np.vectorize(np.copy)

        standing = handing_back

        def through_a_lambda(frequencies, levels):
            f = lam(frequencies)
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


def test_a_loop_s_target_leaves_an_alias_standing(tmp_path: pathlib.Path) -> None:
    """A loop binds its target only on a turn it runs, and it may run none,
    so after it the name may still hold the alias before it, as after the
    branches of an ``if``, at the top of the module and read from another.

    The target was read as bound on every way past the loop, so it ended
    ``keep = handing_back``, and the record that keeps what the function
    hands back passed.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def handing_back(a):
            return a

        no_turn = handing_back
        for no_turn in ():
            pass

        a_turn = handing_back
        for a_turn in [np.copy]:
            pass

        def through_no_turn(frequencies, levels):
            f = no_turn(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_turn(frequencies, levels):
            f = a_turn(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
        helpers="""
        def handing_back(a):
            return a

        keep = handing_back
        for keep in ():
            pass
        """,
        importer="""
        from .helpers import keep
        from .results import BandResult

        def through_an_import(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {
        ("through_no_turn", "BandResult.frequencies", "frequencies"),
        ("through_a_turn", "BandResult.frequencies", "frequencies"),
        ("through_an_import", "BandResult.frequencies", "frequencies"),
    }


def test_an_alias_reaches_the_definition_its_value_named_where_it_was_bound(
    tmp_path: pathlib.Path,
) -> None:
    """``keep = handing_back`` holds the function ``handing_back`` names
    where the assignment runs, whatever a later ``def`` or ``class`` binds
    that name to, at the top of a module, in an assignment expression and
    read from another module.

    The definitions of ``handing_back`` were chosen again where ``keep(...)``
    runs, or once the module had run, so a later copying ``def`` of the name
    stood for the alias and the record that keeps the caller's array passed,
    and an alias of a copying ``def`` a later one replaced with one that
    hands its argument back was refused.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def handing_back(a):
            return a

        keep = handing_back
        (walrus := handing_back)

        def handing_back(a):
            return np.array(a)

        def copying(a):
            return np.array(a)

        copied = copying

        def copying(a):
            return a

        def through_an_alias(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_walrus(frequencies, levels):
            f = walrus(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_copying_alias(frequencies, levels):
            f = copied(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
        helpers="""
        import numpy as np

        def handing_back(a):
            return a

        kept = handing_back

        def handing_back(a):
            return np.array(a)
        """,
        importer="""
        from . import helpers
        from .helpers import kept
        from .results import BandResult

        def through_an_import(frequencies, levels):
            f = kept(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_an_attribute(frequencies, levels):
            f = helpers.kept(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {
        ("through_an_alias", "BandResult.frequencies", "frequencies"),
        ("through_a_walrus", "BandResult.frequencies", "frequencies"),
        ("through_an_import", "BandResult.frequencies", "frequencies"),
        ("through_an_attribute", "BandResult.frequencies", "frequencies"),
    }


def test_an_alias_of_a_def_holds_it_whatever_a_later_class_binds_the_name_to(
    tmp_path: pathlib.Path,
) -> None:
    """``keep = handing_back`` followed by ``class handing_back`` still holds
    the ``def``, at the top of a module, in an assignment expression and read
    from another module, while an alias of a ``class`` a later ``def``
    replaces holds the class; and a call of a name whose ``class`` a later
    ``def`` replaces reaches the ``def``, in its module and through an
    import.

    A function and a class of one name share one key, and a call that
    reached the key was read as a call of the class whenever the class was
    there, whatever the alias had held where it was bound or the name held
    where the call ran, so a record that keeps the caller's array through
    the alias or the replacing ``def`` passed.
    """
    found = _findings(
        tmp_path,
        rating="""
        import numpy as np

        from .results import BandResult

        def handing_back(a):
            return a

        keep = handing_back
        (walrus := handing_back)

        class handing_back:
            pass

        class made:
            pass

        held = made

        def made(a):
            return a

        class direct:
            pass

        def direct(a):
            return a

        def through_an_alias(frequencies, levels):
            f = keep(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_a_walrus(frequencies, levels):
            f = walrus(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_an_alias_of_a_class(frequencies, levels):
            f = held(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_the_name(frequencies, levels):
            f = direct(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
        helpers="""
        def handing_back(a):
            return a

        kept = handing_back

        class handing_back:
            pass

        class replaced:
            pass

        def replaced(a):
            return a
        """,
        importer="""
        from . import helpers
        from .helpers import kept, replaced
        from .results import BandResult

        def through_an_imported_def(frequencies, levels):
            f = replaced(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_an_import(frequencies, levels):
            f = kept(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)

        def through_an_attribute(frequencies, levels):
            f = helpers.kept(frequencies)
            return BandResult(frequencies=f, levels=f * 0.0)
        """,
    )
    assert found == {
        ("through_an_alias", "BandResult.frequencies", "frequencies"),
        ("through_a_walrus", "BandResult.frequencies", "frequencies"),
        ("through_an_import", "BandResult.frequencies", "frequencies"),
        ("through_an_attribute", "BandResult.frequencies", "frequencies"),
        ("through_the_name", "BandResult.frequencies", "frequencies"),
        ("through_an_imported_def", "BandResult.frequencies", "frequencies"),
    }


def test_a_call_that_may_reach_a_def_or_the_class_of_its_name_reads_both(
    tmp_path: pathlib.Path,
) -> None:
    """``make`` bound to a saved ``def BandRecord`` in one branch and to the
    record class of that name in the other builds the record on one of the
    two paths, at the top of a module and read from another module; and
    ``built``, bound to a saved ``def Spectrum`` that hands back its argument
    in one branch and to a record of that name that copies in the other,
    hands back the caller's array on the first path, whatever the second
    does.

    A function and a class of one name share one key, and the ``def`` an
    alias pinned there made the call a call of the ``def`` alone, so the
    record the other branch builds kept the caller's arrays and passed. The
    record that copies takes nothing away from what the ``def`` returns, so
    reading the class alone at such a call would pass ``BandResult`` the
    caller's array unseen.
    """
    found = _findings(
        tmp_path,
        rating="""
        import os
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        def BandRecord(frequencies, levels):
            return np.array(frequencies)

        saved = BandRecord

        @dataclass(frozen=True)
        class BandRecord:
            frequencies: NDArray[np.float64]
            levels: NDArray[np.float64]

        if os.environ.get("RATING"):
            make = saved
        else:
            make = BandRecord

        def through_either(frequencies, levels):
            return make(frequencies, levels)

        def through_the_saved_def(frequencies, levels):
            return saved(frequencies, levels)
        """,
        importer="""
        from . import rating

        def through_an_attribute(frequencies, levels):
            return rating.make(frequencies, levels)
        """,
        owning="""
        import os
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import OwnsArrays
        from .results import BandResult

        def Spectrum(frequencies):
            return frequencies

        handing_back = Spectrum

        @dataclass(frozen=True)
        class Spectrum(OwnsArrays):
            frequencies: NDArray[np.float64]

        if os.environ.get("RATING"):
            built = handing_back
        else:
            built = Spectrum

        def through_either_spectrum(frequencies, levels):
            f = built(frequencies)
            return BandResult(frequencies=f, levels=None)

        def through_the_copying_record(frequencies, levels):
            f = Spectrum(frequencies)
            return BandResult(frequencies=f, levels=None)
        """,
    )
    assert found == {
        ("through_either", "BandRecord.frequencies", "frequencies"),
        ("through_either", "BandRecord.levels", "levels"),
        ("through_an_attribute", "BandRecord.frequencies", "frequencies"),
        ("through_an_attribute", "BandRecord.levels", "levels"),
        ("through_either_spectrum", "BandResult.frequencies", "frequencies"),
    }


def test_a_class_an_alias_holds_is_read_with_its_own_fields(
    tmp_path: pathlib.Path,
) -> None:
    """``saved``, bound to a ``class Kept`` before a later one of the name
    replaced it, builds the class it was bound to, and ``copying`` likewise;
    a name with a ``class Either`` in each branch of an ``if`` builds either.

    A key held one class, the last ``class`` statement of it, so the guard
    read each of these with the fields and bases of the last: the record
    that keeps the caller's array passed, a copy it needs was refused as
    made twice, and the other way round for the record that copies.
    """
    found = _findings(
        tmp_path,
        kept="""
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import OwnsArrays, read_only_copy

        @dataclass(frozen=True)
        class Kept:
            frequencies: NDArray[np.float64]

        saved = Kept

        @dataclass(frozen=True)
        class Kept(OwnsArrays):
            frequencies: NDArray[np.float64]

        def through_the_kept_class(frequencies):
            return saved(frequencies)

        def a_copy_the_kept_class_needs(frequencies):
            return saved(read_only_copy(frequencies))

        def a_copy_the_last_class_makes(frequencies):
            return Kept(read_only_copy(frequencies))
        """,
        owned="""
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import OwnsArrays, read_only_copy

        @dataclass(frozen=True)
        class Owned(OwnsArrays):
            frequencies: NDArray[np.float64]

        copying = Owned

        @dataclass(frozen=True)
        class Owned:
            frequencies: NDArray[np.float64]

        def through_the_copying_class(frequencies):
            return copying(frequencies)

        def a_copy_made_twice(frequencies):
            return copying(read_only_copy(frequencies))
        """,
        either="""
        import os
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import OwnsArrays, read_only_copy

        if os.environ.get("BANDS"):
            @dataclass(frozen=True)
            class Either:
                frequencies: NDArray[np.float64]
        else:
            @dataclass(frozen=True)
            class Either(OwnsArrays):
                frequencies: NDArray[np.float64]

        def through_either_class(frequencies):
            return Either(frequencies)

        def a_copy_one_class_needs(frequencies):
            return Either(read_only_copy(frequencies))
        """,
    )
    assert found == {
        ("through_the_kept_class", "Kept.frequencies", "frequencies"),
        ("a_copy_the_last_class_makes", "Kept.frequencies (copied twice)", ""),
        ("a_copy_made_twice", "Owned.frequencies (copied twice)", ""),
        ("through_either_class", "Either.frequencies", "frequencies"),
    }


def test_a_copy_is_made_twice_only_where_every_path_of_the_call_copies(
    tmp_path: pathlib.Path,
) -> None:
    """A name that may run a function handing back its argument, or build a
    record that does not copy, as well as a record that copies, needs the
    copy it is handed on the other path; one whose every function or class
    is a record that copies copies twice: the record alone, either of two
    records that copy, bound in two branches, or a class written in each
    branch that copies in both, called by its name or as a module's
    attribute, and handed the copy itself or a name bound to it.

    Each record that copies a call may build was held to the copy alone, so
    ``make(read_only_copy(f))`` was refused as a copy made twice where
    ``make`` is a saved ``def`` in one branch, or another record in the
    other, and dropping the copy would hand that path the caller's array.
    Then a copy was refused only where the call named one key that built
    one ``class`` statement, so one handed to either of two records that
    both copy passed, and so did one bound to a name first.
    """
    found = _findings(
        tmp_path,
        owning="""
        import os
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import OwnsArrays, read_only_copy

        def Spectrum(frequencies):
            return frequencies

        handing_back = Spectrum

        @dataclass(frozen=True)
        class Spectrum(OwnsArrays):
            frequencies: NDArray[np.float64]

        @dataclass(frozen=True)
        class Plain:
            frequencies: NDArray[np.float64]

        if os.environ.get("RATING"):
            built = handing_back
            record = Plain
        else:
            built = Spectrum
            record = Spectrum

        def beside_a_function(frequencies):
            return built(read_only_copy(frequencies))

        def beside_a_record_that_keeps(frequencies):
            return record(read_only_copy(frequencies))

        def alone(frequencies):
            return Spectrum(read_only_copy(frequencies))
        """,
        copying="""
        import os
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import OwnsArrays, read_only_copy

        @dataclass(frozen=True)
        class First(OwnsArrays):
            frequencies: NDArray[np.float64]

        @dataclass(frozen=True)
        class Second(OwnsArrays):
            frequencies: NDArray[np.float64]

        if os.environ.get("RATING"):
            either = First

            @dataclass(frozen=True)
            class Shown(OwnsArrays):
                frequencies: NDArray[np.float64]
        else:
            either = Second

            @dataclass(frozen=True)
            class Shown(OwnsArrays):
                frequencies: NDArray[np.float64]

        def either_record(frequencies):
            return either(read_only_copy(frequencies))

        def either_class_statement(frequencies):
            return Shown(read_only_copy(frequencies))

        def bound_copy_to_either_record(frequencies):
            f = read_only_copy(frequencies)
            return either(frequencies=f)

        def bound_copy_to_either_class_statement(frequencies):
            f = read_only_copy(frequencies)
            return Shown(frequencies=f)
        """,
        elsewhere="""
        from . import copying
        from ._internal.frozen import read_only_copy

        def either_record_of_the_module(frequencies):
            return copying.either(read_only_copy(frequencies))

        def either_class_statement_of_the_module(frequencies):
            return copying.Shown(read_only_copy(frequencies))
        """,
    )
    assert found == {
        ("alone", "Spectrum.frequencies (copied twice)", ""),
        ("either_record", "First.frequencies (copied twice)", ""),
        ("either_record", "Second.frequencies (copied twice)", ""),
        ("either_class_statement", "Shown.frequencies (copied twice)", ""),
        ("either_record_of_the_module", "First.frequencies (copied twice)", ""),
        ("either_record_of_the_module", "Second.frequencies (copied twice)", ""),
        (
            "either_class_statement_of_the_module",
            "Shown.frequencies (copied twice)",
            "",
        ),
        ("bound_copy_to_either_record", "First.frequencies (copied twice, as f)", ""),
        (
            "bound_copy_to_either_record",
            "Second.frequencies (copied twice, as f)",
            "",
        ),
        (
            "bound_copy_to_either_class_statement",
            "Shown.frequencies (copied twice, as f)",
            "",
        ),
    }


def test_a_call_reads_the_def_or_class_its_function_defines_where_it_runs(
    tmp_path: pathlib.Path,
) -> None:
    """A ``def`` a function writes after a ``class`` of its name is what the
    name calls from there on, and one written in a branch beside a class in
    the other may be.

    The name was read as the class whenever the function defined one of it,
    so what the ``def`` hands back, the caller's array, never reached the
    record built from it.
    """
    found = _findings(
        tmp_path,
        local="""
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import OwnsArrays
        from .results import BandResult

        def through_a_later_def(frequencies, levels):
            @dataclass(frozen=True)
            class Keep(OwnsArrays):
                frequencies: NDArray[np.float64]

            def Keep(frequencies):
                return frequencies

            f = Keep(frequencies)
            return BandResult(frequencies=f, levels=None)

        def through_either_branch(frequencies, levels):
            if levels is None:
                @dataclass(frozen=True)
                class Local(OwnsArrays):
                    frequencies: NDArray[np.float64]
            else:
                def Local(frequencies):
                    return frequencies
            f = Local(frequencies)
            return BandResult(frequencies=f, levels=None)

        def through_a_later_class(frequencies, levels):
            def Owned(frequencies):
                return frequencies

            @dataclass(frozen=True)
            class Owned(OwnsArrays):
                frequencies: NDArray[np.float64]

            f = Owned(frequencies)
            return BandResult(frequencies=f.frequencies, levels=None)
        """,
    )
    assert found == {
        ("through_a_later_def", "BandResult.frequencies", "frequencies"),
        ("through_either_branch", "BandResult.frequencies", "frequencies"),
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
    ("helpers", "call"),
    [
        (
            """
            def _head(n):
                return np.arange(n)

            class _head:
                def __init__(self, n):
                    self.row = 0

                def __index__(self):
                    return self.row
            """,
            "_head(3)",
        ),
        (
            """
            def _head(n):
                return np.arange(n)

            if os.environ.get("ROW"):
                class _head:
                    def __init__(self, n):
                        self.row = 0

                    def __index__(self):
                        return self.row
            """,
            "_head(3)",
        ),
        (
            """
            from . import rows
            """,
            "rows._head(3)",
        ),
    ],
    ids=["class-replaces-it", "class-in-a-branch", "from-another-module"],
)
def test_a_helper_a_class_of_its_name_may_stand_for_selects_a_view(
    tmp_path: pathlib.Path, helpers: str, call: str
) -> None:
    """A call of a helper that returns positions, where a ``class`` of its
    name that indexes as one number may stand instead, may select a row,
    which is a view.

    The call was read as the helper alone, so the record kept the caller's
    array with no finding.
    """
    found = _findings(
        tmp_path,
        rows="""
        import numpy as np

        def _head(n):
            return np.arange(n)

        class _head:
            def __init__(self, n):
                self.row = 0

            def __index__(self):
                return self.row
        """,
        head=f"""
        import os

        import numpy as np

        from .results import BandResult
        {textwrap.indent(textwrap.dedent(helpers), " " * 8)}
        def head(frequencies):
            return BandResult(frequencies=frequencies[{call}], levels=None)
        """,
    )
    assert found == {("head", "BandResult.frequencies", "frequencies")}


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


def test_each_class_statement_of_a_public_record_is_held_to_it(
    tmp_path: pathlib.Path,
) -> None:
    """A ``class Kept`` that a later one of the name replaced is still built
    by hand through ``saved``, and a ``class Either`` in one branch of an
    ``if`` is the record whenever that branch runs.

    Only the last ``class`` statement of a name was read, so a record that
    does not copy passed beside one of its name that does.
    """
    found = _unequipped(
        tmp_path,
        kept="""
        from dataclasses import dataclass

        import numpy as np

        from ._internal.frozen import OwnsArrays

        @dataclass(frozen=True)
        class Kept:
            frequencies: np.ndarray

        saved = Kept

        @dataclass(frozen=True)
        class Kept(OwnsArrays):
            frequencies: np.ndarray
        """,
        either="""
        import os
        from dataclasses import dataclass

        import numpy as np

        from ._internal.frozen import OwnsArrays

        if os.environ.get("BANDS"):
            @dataclass(frozen=True)
            class Either:
                frequencies: np.ndarray

            @dataclass(frozen=True)
            class Both(OwnsArrays):
                frequencies: np.ndarray
        else:
            @dataclass(frozen=True)
            class Either(OwnsArrays):
                frequencies: np.ndarray

            @dataclass(frozen=True)
            class Both(OwnsArrays):
                frequencies: np.ndarray
        """,
    )
    assert found == {"BandResult", "Kept", "Either"}


#: Records whose base is read where their ``class`` statement reads it: a
#: base with a class in each branch of an ``if``, one that copies and one
#: that does not; one a later class of its name replaces after the record,
#: either way round; and one an alias holds, bound again after the record,
#: either way round.
_BASES = """
import os
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ._internal.frozen import OwnsArrays, read_only_copy

if os.environ.get("BANDS"):
    @dataclass(frozen=True)
    class _Either:
        pass
else:
    @dataclass(frozen=True)
    class _Either(OwnsArrays):
        pass

@dataclass(frozen=True)
class OnEither(_Either):
    frequencies: NDArray[np.float64]

@dataclass(frozen=True)
class _Late:
    pass

@dataclass(frozen=True)
class BeforeTheCopy(_Late):
    frequencies: NDArray[np.float64]

@dataclass(frozen=True)
class _Late(OwnsArrays):
    pass

@dataclass(frozen=True)
class _Early(OwnsArrays):
    pass

@dataclass(frozen=True)
class BeforeThePlainOne(_Early):
    frequencies: NDArray[np.float64]

@dataclass(frozen=True)
class _Early:
    pass

@dataclass(frozen=True)
class _Plain:
    pass

base = _Plain

@dataclass(frozen=True)
class ThroughAnAlias(base):
    frequencies: NDArray[np.float64]

base = _Late

shown = _Late

@dataclass(frozen=True)
class ThroughACopyingAlias(shown):
    frequencies: NDArray[np.float64]

shown = _Plain

def build_on_either(frequencies):
    return OnEither(frequencies)

def build_before_the_copy(frequencies):
    return BeforeTheCopy(frequencies)

def build_through_an_alias(frequencies):
    return ThroughAnAlias(frequencies)

def build_through_a_copying_alias(frequencies):
    return ThroughACopyingAlias(frequencies)

def a_copy_the_record_makes(frequencies):
    return BeforeThePlainOne(read_only_copy(frequencies))
"""


def test_a_record_s_base_is_the_class_its_statement_reads(
    tmp_path: pathlib.Path,
) -> None:
    """A record copies through its base only when every class the base's
    name may stand for where its ``class`` statement reads it copies: not a
    base with a plain class in one branch, nor one a class that copies
    replaced only after the record, nor an alias bound to such a class only
    after it; and a record built on a base that copies, or on an alias of
    one, still copies when a plain class takes the name later.

    A base was every class of the package of its bare name, and the record
    copied when any one of them did, so the first two passed, by hand and
    from a factory; an alias was no class at all, so a record built on an
    alias of a class that copies was refused, and the one built on an alias
    of a plain class was refused only for that reason.
    """
    assert _unequipped(tmp_path / "a", bases=_BASES) == {
        "BandResult",
        "OnEither",
        "BeforeTheCopy",
        "ThroughAnAlias",
    }
    assert _findings(tmp_path / "b", bases=_BASES) == {
        ("build_on_either", "OnEither.frequencies", "frequencies"),
        ("build_before_the_copy", "BeforeTheCopy.frequencies", "frequencies"),
        ("build_through_an_alias", "ThroughAnAlias.frequencies", "frequencies"),
        ("a_copy_the_record_makes", "BeforeThePlainOne.frequencies (copied twice)", ""),
    }


def test_a_base_s_fields_copies_and_attributes_are_those_of_the_class_it_reads(
    tmp_path: pathlib.Path,
) -> None:
    """The fields a record inherits are those of the base its ``class``
    statement reads, here the second of two classes of the name, and a
    field a base's ``__post_init__`` copies or seals is the record's own
    only when every class the base may be does so; an attribute annotated in
    a plain base is read from the class that stood.

    A base was every class of the package of its name: the fields came from
    the first, so ``Shaped(frequencies)`` filled a text field; a field one
    branch's class copied or sealed counted as copied or sealed on both; and
    an attribute's annotation came from the first class that had it.
    """
    found = _findings(
        tmp_path,
        fields="""
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        @dataclass(frozen=True)
        class _Shape:
            label: str

        @dataclass(frozen=True)
        class _Shape:
            frequencies: NDArray[np.float64]

        @dataclass(frozen=True)
        class Shaped(_Shape):
            note: str = ""

        def build_shaped(frequencies):
            return Shaped(frequencies)
        """,
        owned="""
        import os
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import read_only_copy
        from .results import BandResult

        if os.environ.get("BANDS"):
            @dataclass(frozen=True)
            class _Kept:
                data: NDArray[np.float64]

                def __post_init__(self):
                    object.__setattr__(self, "data", read_only_copy(self.data))
        else:
            @dataclass(frozen=True)
            class _Kept:
                data: NDArray[np.float64]

        @dataclass(frozen=True)
        class Kept(_Kept):
            levels: NDArray[np.float64]

        def build_kept(data, levels):
            return Kept(data, levels)

        def passed_on(record: Kept):
            return BandResult(frequencies=record.data, levels=None)
        """,
        held="""
        import numpy as np

        class _Holder:
            sos: float

        class _Holder:
            sos: np.ndarray

        class Bank(_Holder):
            def __init__(self, sos):
                self.sos = np.asarray(sos)
        """,
    )
    assert found == {
        ("build_shaped", "Shaped.frequencies", "frequencies"),
        ("build_kept", "Kept.data", "data"),
        ("build_kept", "Kept.levels", "levels"),
        ("passed_on", "BandResult.frequencies", "record"),
        ("Bank.__init__", "self.sos", "sos"),
    }


def test_an_argument_fills_the_field_of_its_place_in_each_order_a_base_gives(
    tmp_path: pathlib.Path,
) -> None:
    """A record on a base with a class in each branch of an ``if`` takes its
    fields in the order of the class that stood, so an argument fills the
    field of its place in each: ``Child(None, values)`` keeps ``values`` in
    ``payload`` on one path and in ``data`` on the other, and a label handed
    first may be ``data`` itself.

    The fields of the classes a base may be were merged by name in the order
    the first gave them, ``data, note, payload``, so the second argument
    filled ``note``, a text, and the array the record keeps passed.
    """
    found = _findings(
        tmp_path,
        either="""
        import os
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        if os.environ.get("BANDS"):
            @dataclass(frozen=True)
            class _Base:
                data: NDArray[np.float64]
        else:
            @dataclass(frozen=True)
            class _Base:
                note: str
                data: NDArray[np.float64]

        @dataclass(frozen=True)
        class Child(_Base):
            payload: NDArray[np.float64] | None = None

        def build_either(values):
            return Child(None, values)

        def build_labelled(label, values):
            return Child(label, values)
        """,
    )
    assert found == {
        ("build_either", "Child.data", "values"),
        ("build_either", "Child.payload", "values"),
        ("build_labelled", "Child.data", "label, values"),
        ("build_labelled", "Child.payload", "values"),
    }


#: Records whose constructor takes its fields in another order than the one
#: they are written in, each built by position with the caller's array.
_FIELD_ORDERS = """
from dataclasses import KW_ONLY, dataclass, field

import numpy as np
from numpy.typing import NDArray

from ._internal.frozen import OwnsArrays

@dataclass(frozen=True)
class _Base:
    data: NDArray[np.float64]
    note: str

@dataclass(frozen=True)
class Redefined(_Base):
    data: NDArray[np.float64]

@dataclass(frozen=True)
class _Levels:
    levels: NDArray[np.float64]

@dataclass(frozen=True)
class _Label:
    label: str

@dataclass(frozen=True)
class Both(_Levels, _Label):
    pass

@dataclass(frozen=True, kw_only=True)
class _Tagged:
    label: str = ""

@dataclass(frozen=True)
class Tagged(_Tagged):
    data: NDArray[np.float64]

@dataclass(frozen=True)
class Marked:
    label: str = field(default="", kw_only=True)
    data: NDArray[np.float64] | None = None

@dataclass(frozen=True)
class _Sentinel:
    _: KW_ONLY
    label: str = ""

@dataclass(frozen=True)
class AfterTheSentinel(_Sentinel):
    data: NDArray[np.float64]

@dataclass(frozen=True)
class _Plain:
    data: NDArray[np.float64]

class _Mixin(_Plain):
    cache: NDArray[np.float64] | None = None

    def describe(self):
        return ""

@dataclass(frozen=True)
class Described(_Mixin):
    note: str = ""

@dataclass(frozen=True)
class _Owning(OwnsArrays):
    data: NDArray[np.float64]

class _Showing(_Owning):
    def describe(self):
        return ""

@dataclass(frozen=True)
class Shown(_Showing):
    note: str = ""

@dataclass(frozen=True)
class TaggedCopy(_Tagged, OwnsArrays):
    data: NDArray[np.float64]

def build_redefined(values):
    return Redefined(values, "x")

def build_both(values):
    return Both("x", values)

def build_tagged(values):
    return Tagged(values)

def build_marked(values):
    return Marked(values)

def build_after_the_sentinel(values):
    return AfterTheSentinel(values)

def build_described(values):
    return Described(values)

def build_described_late(label, values):
    return Described(label, values)

def build_shown(values):
    return Shown(values)

def build_tagged_copy(values):
    return TaggedCopy(values.copy())
"""


def test_a_record_takes_its_fields_in_the_order_its_constructor_does(
    tmp_path: pathlib.Path,
) -> None:
    """An argument fills the field of its place in the constructor's order:
    a field a record writes again keeps the place its base gave it, the
    fields of the last base come first, a keyword-only field takes no place,
    and a class that is no record lends the fields of the record it is built
    on, and its copies, but no annotation of its own.

    The fields were read as written, the base's first and in the order of the
    bases, a field written again last, a keyword-only field in its place and
    a class that is no record with none, so each of these records filled a
    text with the caller's array and passed; ``values.copy()`` handed to a
    record that copies was read against a text and passed; and a record on a
    plain class over one that copies would have kept what it copies.
    """
    found = _findings(tmp_path / "a", orders=_FIELD_ORDERS)
    assert found == {
        ("build_redefined", "Redefined.data", "values"),
        ("build_both", "Both.levels", "values"),
        ("build_tagged", "Tagged.data", "values"),
        ("build_marked", "Marked.data", "values"),
        ("build_after_the_sentinel", "AfterTheSentinel.data", "values"),
        ("build_described", "Described.data", "values"),
        ("build_described_late", "Described.data", "label"),
        ("build_tagged_copy", "TaggedCopy.data (copied twice)", ""),
    }
    assert _unequipped(tmp_path / "b", orders=_FIELD_ORDERS) == {
        "BandResult",
        "Redefined",
        "Both",
        "Tagged",
        "Marked",
        "AfterTheSentinel",
        "Described",
    }


def test_an_argument_after_a_star_may_fill_any_place_from_the_star_s_on(
    tmp_path: pathlib.Path,
) -> None:
    """The ``*`` argument hands an unknown number of values, so an argument
    written after it may fill any field from the star's place on: with
    nothing in ``head`` it fills ``first``, with one ``label``, with two
    ``data``. The star's own items fill the fields from its place on, but
    leave ``values`` a field after them: ``first`` or ``label``, never
    ``data``.

    It was read at its written place alone, the text ``label``, so the two
    fields that may keep the caller's array passed; then the star was read
    as filling ``data`` too, which a call that returns never lets it.
    """
    found = _findings(
        tmp_path,
        spread="""
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        @dataclass(frozen=True)
        class Spread:
            first: NDArray[np.float64]
            label: str = ""
            data: NDArray[np.float64] | None = None

        def build_spread(head, values):
            return Spread(*head, values)
        """,
    )
    assert found == {
        ("build_spread", "Spread.first", "head, values"),
        ("build_spread", "Spread.data", "values"),
    }


def test_a_star_fills_no_place_from_a_keyword_s_on(
    tmp_path: pathlib.Path,
) -> None:
    """The items of a ``*`` argument fill the places from its lowest on one
    each, so on a call that returns they stop before the first place an
    explicit keyword fills: ``Rec(*head, label="")`` hands ``head`` the
    first field alone, never ``data``, and ``_pass(*head, label="")`` hands
    it ``first`` alone, never ``data`` or ``*rest``.

    The star was read as filling every place from its lowest on that no
    keyword fills, and ``*args`` past them, so ``head`` was reported as kept
    in ``data`` and as handed back through ``_pass``.
    """
    found = _findings(
        tmp_path,
        stopped="""
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        @dataclass(frozen=True)
        class Rec:
            first: str = ""
            label: str = ""
            data: NDArray[np.float64] | None = None

        def build_rec(head):
            return Rec(*head, label="")

        def _pass(first, label="", data=None, *rest):
            return data, rest

        @dataclass(frozen=True)
        class Holder:
            data: NDArray[np.float64]

        def build_holder(head):
            data, rest = _pass(*head, label="")
            return Holder(data)
        """,
    )
    assert found == set()


#: Calls whose ``*`` argument fills the fields or parameters from its lowest
#: place on, and whose arguments after it never fill one before theirs.
_LOWEST_PLACES = """
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ._internal.frozen import read_only_copy
from .results import BandResult

@dataclass(frozen=True)
class _Rec:
    a: NDArray[np.float64]
    b: NDArray[np.float64]

@dataclass(frozen=True)
class Trailing:
    data: NDArray[np.float64] | None = None
    label: str = ""
    other: str = ""

@dataclass(frozen=True)
class Copied:
    data: NDArray[np.float64] | None = None
    label: str = ""

    def __post_init__(self):
        object.__setattr__(self, "data", read_only_copy(self.data))

@dataclass(frozen=True)
class Named:
    first: NDArray[np.float64]
    data: NDArray[np.float64]

def _second(x, rest):
    rec = _Rec(x, *rest)
    return rec.b

def _first(rest):
    rec = _Rec(*rest)
    return rec.a

def _picked(first, label=None, data=None):
    return first

def build_second(x, rest):
    return BandResult(frequencies=_second(x, rest), levels=None)

def build_first(rest):
    return BandResult(frequencies=_first(rest), levels=None)

def build_trailing(head, values):
    return Trailing(*head, 1, values)

def build_picked(head, values):
    return BandResult(frequencies=_picked(*head, None, values), levels=None)

def build_copied(rest):
    return Copied(*rest)

def _kept(head, values):
    return _Rec(*head, b=values).b

def build_named(head, values):
    return Named(*head, data=values)

def build_kept(head, values):
    return BandResult(frequencies=_kept(head, values), levels=None)
"""


def test_a_star_fills_each_place_from_the_lowest_it_may_take_on(
    tmp_path: pathlib.Path,
) -> None:
    """A ``*`` argument hands its items to the places from its own on, and
    none to those before: ``_Rec(x, *rest)`` keeps an item of ``rest`` in
    ``b``, and ``_Rec(*rest)`` in ``a`` too, so the field a helper hands
    back carries ``rest``. An argument after a star never fills a place
    before the plain arguments written ahead of it allow: in
    ``Trailing(*head, 1, values)`` and ``_picked(*head, None, values)``
    the array lands in the second place or a later one, never in ``data``
    or ``first``, which only an item of ``head`` may fill. A field an
    explicit keyword fills is that keyword's alone, as Python raises rather
    than put an item there: ``Named(*head, data=values)`` keeps ``head`` in
    ``first`` alone, and ``_Rec(*head, b=values).b`` hands back ``values``
    alone. A field the record copies keeps nothing of the star.

    The star was kept in no field, only spread over the fields an argument
    had already filled, so the two fields it alone filled carried nothing
    and the caller's array went back unseen; every argument after a star
    was read from the star's own place on, so ``values`` was refused as
    kept in ``data`` and handed back as ``first``; and the star was read as
    spread over the record, so ``Copied(*rest)`` was refused though the
    record copies its one array; then the star was kept in a field a keyword
    fills too, so ``head`` was read as kept in ``data`` and handed back as
    ``b``.
    """
    found = _findings(tmp_path, lowest=_LOWEST_PLACES)
    assert found == {
        ("build_second", "BandResult.frequencies", "rest"),
        ("build_first", "BandResult.frequencies", "rest"),
        ("build_trailing", "Trailing.data", "head"),
        ("build_picked", "BandResult.frequencies", "head"),
        ("build_named", "Named.first", "head"),
        ("build_named", "Named.data", "values"),
        ("build_kept", "BandResult.frequencies", "values"),
    }


#: Classes whose call runs an ``__init__`` other than their own, and so a
#: ``__post_init__`` other than theirs, or none.
_INIT_RUNS = """
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from ._internal.frozen import OwnsArrays, read_only_copy

@dataclass(frozen=True)
class _Base:
    data: NDArray[np.float64]
    other: NDArray[np.float64]

@dataclass(frozen=True)
class _Hooking:
    data: NDArray[np.float64]
    other: NDArray[np.float64]

    def __post_init__(self):
        pass

@dataclass(frozen=True, init=False)
class Unwritten(_Base):
    def __post_init__(self):
        object.__setattr__(self, "data", read_only_copy(self.data))

class PlainNoHook(_Base):
    pass

class Owned(_Base):
    def __post_init__(self):
        object.__setattr__(self, "data", read_only_copy(self.data))

class Hooked(_Hooking):
    def __post_init__(self):
        object.__setattr__(self, "data", read_only_copy(self.data))

@dataclass(frozen=True)
class Handing(_Hooking):
    def __init__(self, data, other):
        super().__init__(data, other)

    def __post_init__(self):
        object.__setattr__(self, "data", read_only_copy(self.data))

@dataclass(frozen=True, init=False)
class Lent(_Base, OwnsArrays):
    pass

@dataclass(frozen=True)
class Stubbed:
    data: NDArray[np.float64]
    other: NDArray[np.float64]

    if TYPE_CHECKING:

        def __init__(self, data, other): ...

    def __post_init__(self):
        object.__setattr__(self, "data", read_only_copy(self.data))

def build_unwritten(data, other):
    return Unwritten(data, other)

def build_plain(data, other):
    return PlainNoHook(data, other)

def build_owned(data, other):
    return Owned(data=data, other=other)

def build_hooked(data, other):
    return Hooked(data, other)

def build_handing(data, other):
    return Handing(data, other)

def build_stubbed(data, other):
    return Stubbed(data, other)
"""


def test_a_call_keeps_what_the_init_it_runs_keeps(tmp_path: pathlib.Path) -> None:
    """A call of a class runs the ``__init__`` of the first class of its
    method resolution order that has one of its own, and the copies its
    ``__post_init__`` makes only when that ``__init__`` calls it: the one
    ``@dataclass`` wrote for ``_Base`` calls none, so ``Unwritten``,
    ``Owned`` and ``Lent`` keep the caller's arrays whatever they copy, and
    a call of ``PlainNoHook``, a class that is no record, keeps both. The
    one written for ``_Hooking`` calls the hook ``Hooked`` writes, and so
    does ``Handing``'s, which hands its values on to it. An ``__init__``
    written under ``if TYPE_CHECKING:`` never runs: ``Stubbed`` runs the one
    ``@dataclass`` writes it, and its hook.

    A record's own ``__post_init__`` was read as copying whatever
    ``__init__`` ran, so ``data`` was read as owned, and a call of a class
    that is no record as keeping nothing.
    """
    found = _findings(tmp_path, runs=_INIT_RUNS)
    assert found == {
        ("build_unwritten", "Unwritten.data", "data"),
        ("build_unwritten", "Unwritten.other", "other"),
        ("build_plain", "PlainNoHook.data", "data"),
        ("build_plain", "PlainNoHook.other", "other"),
        ("build_owned", "Owned.data", "data"),
        ("build_owned", "Owned.other", "other"),
        ("build_hooked", "Hooked.other", "other"),
        ("build_handing", "Handing.other", "other"),
        ("build_stubbed", "Stubbed.other", "other"),
    }
    root = _package(tmp_path / "unequipped", {"runs": _INIT_RUNS})
    lent = [
        finding.sink
        for finding in caa.records_without_mechanism(sorted(root.rglob("*.py")), root)
        if finding.function == "Lent"
    ]
    assert lent == [
        "Lent can hold an array (data, other) and inherits OwnsArrays, but the "
        "__init__ a call of it runs calls no __post_init__"
    ]


#: Records whose own ``__init__`` hands its values on to the ``__init__`` of
#: a base it names, past a base before it in their order.
_NAMED_HAND_OFFS = """
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ._internal.frozen import OwnsArrays, read_only_copy

@dataclass(frozen=True)
class _Copying:
    data: NDArray[np.float64]

    def __post_init__(self):
        object.__setattr__(self, "data", read_only_copy(self.data))

@dataclass(frozen=True)
class _Owning(OwnsArrays):
    data: NDArray[np.float64]

class _Mixin:
    def __init__(self):
        pass

@dataclass(frozen=True)
class NamedPast(_Mixin, _Copying):
    def __init__(self, data):
        _Copying.__init__(self, data)

@dataclass(frozen=True)
class SuperPast(_Mixin, _Copying):
    def __init__(self, data):
        super(_Mixin, self).__init__(data)

@dataclass(frozen=True)
class NamedMixin(_Copying, _Mixin):
    def __init__(self, data):
        _Mixin.__init__(self)
        object.__setattr__(self, "data", data)

@dataclass(frozen=True)
class LentPast(_Mixin, _Owning):
    def __init__(self, data):
        _Owning.__init__(self, data)

def build_named_past(data):
    return NamedPast(data)

def build_super_past(data):
    return SuperPast(data)

def build_named_mixin(data):
    return NamedMixin(data)
"""


def test_an_init_handed_on_to_is_the_one_its_call_names(
    tmp_path: pathlib.Path,
) -> None:
    """``_Copying.__init__(self, data)`` runs the ``__init__`` ``_Copying``
    looks up, the one ``@dataclass`` wrote for it, which calls the hook that
    copies ``data``, though ``_Mixin`` comes before it in the order of
    ``NamedPast``; ``super(_Mixin, self).__init__(data)`` runs the first one
    after ``_Mixin``, the same. ``_Mixin.__init__`` calls none, though the
    class after ``NamedMixin`` in its order has one that does: the caller's
    array is kept. ``LentPast`` hands its values to the ``__init__`` written
    for ``_Owning``, which calls the hook ``OwnsArrays`` lends.

    Every ``__init__`` a hand-written one named was read as the one of the
    next class of the order that has one: ``_Mixin``'s for ``NamedPast``,
    ``SuperPast`` and ``LentPast``, so arrays their hook copies were
    reported as kept and ``LentPast`` as running no hook, and
    ``_Copying``'s for ``NamedMixin``, so the array it keeps passed.
    """
    found = _findings(tmp_path, runs=_NAMED_HAND_OFFS)
    assert found == {
        ("NamedMixin.__init__", "NamedMixin.data", "data"),
        ("build_named_mixin", "NamedMixin.data", "data"),
    }
    root = _package(tmp_path / "unequipped", {"runs": _NAMED_HAND_OFFS})
    unhooked = [
        finding.function
        for finding in caa.records_without_mechanism(sorted(root.rglob("*.py")), root)
        if finding.function == "LentPast"
    ]
    assert unhooked == []


def test_a_method_called_through_its_class_takes_the_instance_first(
    tmp_path: pathlib.Path,
) -> None:
    """``Box._first(self, kept, other)`` hands ``self`` to the method's
    ``self``, ``kept`` to ``kept``; a ``classmethod`` called through the
    class, ``Box._first_of(kept, other)``, is bound to it, and one called on
    ``self`` binds ``self``.

    A method called through the class's name was bound as one called on
    ``self``, so each argument landed one place too far: ``give`` was
    reported as keeping ``other``, which the method never returns, and not
    ``kept``.
    """
    found = _findings(
        tmp_path,
        runs="""
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        @dataclass(frozen=True)
        class Rec:
            data: NDArray[np.float64]

        class Box:
            def _first(self, kept, other):
                return kept

            @classmethod
            def _first_of(cls, kept, other):
                return kept

            def give(self, kept, other):
                return Rec(Box._first(self, kept, other))

            def give_bound(self, kept, other):
                return Rec(self._first(kept, other))

            def give_class(self, kept, other):
                return Rec(Box._first_of(kept, other))
        """,
    )
    assert found == {
        ("Box.give", "Rec.data", "kept"),
        ("Box.give_bound", "Rec.data", "kept"),
        ("Box.give_class", "Rec.data", "kept"),
    }


def test_a_call_on_self_reaches_the_method_the_class_of_the_instance_holds(
    tmp_path: pathlib.Path,
) -> None:
    """``self._wrap(data)`` in ``Base.give`` runs what the class of the
    instance holds: on a ``Sub``, ``Sub._wrap``, which hands the caller's
    array back as it is, so ``Sub().give(data)`` keeps it in ``Rec.data``;
    and ``self._wrap(data)`` in ``Inheriting.give`` runs the ``_wrap`` it
    takes from ``Holder``, which keeps it too.

    A call on ``self`` reached only a method the class body of the caller
    writes: ``Base._wrap``, which copies, and none in ``Inheriting``, so
    neither ``give`` was read as keeping the caller's array.
    """
    found = _findings(
        tmp_path,
        runs="""
        from dataclasses import dataclass

        import numpy as np
        from numpy.typing import NDArray

        from ._internal.frozen import read_only_copy

        @dataclass(frozen=True)
        class Rec:
            data: NDArray[np.float64]

        class Base:
            def _wrap(self, data):
                return read_only_copy(data)

            def give(self, data):
                return Rec(self._wrap(data))

        class Sub(Base):
            def _wrap(self, data):
                return data

        class Holder:
            def _wrap(self, data):
                return data

        class Inheriting(Holder):
            def give(self, data):
                return Rec(self._wrap(data))
        """,
    )
    assert found == {
        ("Base.give", "Rec.data", "data"),
        ("Inheriting.give", "Rec.data", "data"),
    }


#: Records whose constructor takes the fields of their bases in their method
#: resolution order, which reading each base's own order whole, the last
#: base's first, does not give.
_RESOLUTION_ORDERS = """
from dataclasses import dataclass
from typing import ClassVar

import numpy as np
from numpy.typing import NDArray

from ._internal.frozen import OwnsArrays

@dataclass(frozen=True)
class _Note:
    note: str

@dataclass(frozen=True)
class _Data:
    data: NDArray[np.float64]

@dataclass(frozen=True)
class _Left(_Note, _Data):
    pass

@dataclass(frozen=True)
class _Right(_Note):
    pass

@dataclass(frozen=True)
class Diamond(_Left, _Right):
    pass

@dataclass(frozen=True)
class OwnedDiamond(_Left, _Right, OwnsArrays):
    pass

@dataclass(frozen=True)
class _Pair(_Data, _Note):
    pass

@dataclass(frozen=True)
class Again(_Pair, _Data):
    pass

@dataclass(frozen=True)
class _Kinds:
    kind: ClassVar[str] = "band"
    label: str = ""

@dataclass(frozen=True)
class Kinded(_Kinds):
    kind: NDArray[np.float64] | None = None

def build_diamond(values):
    return Diamond(values, "x")

def build_diamond_copy(values):
    return OwnedDiamond(values.copy(), "x")

def build_diamond_label_copy(values):
    return OwnedDiamond("x", values.copy())

def build_again(values):
    return Again("x", values)

def build_kinded(values):
    return Kinded(values)
"""


def test_a_record_takes_its_bases_fields_in_its_method_resolution_order(
    tmp_path: pathlib.Path,
) -> None:
    """``dataclasses`` reads the fields of each class of the record's method
    resolution order, from the farthest to the nearest: ``Diamond(_Left,
    _Right)``, ``_Left`` built on ``_Note`` and ``_Data`` and ``_Right`` on
    ``_Note``, resolves ``_Left, _Right, _Note, _Data`` and takes ``data``
    first; ``Again(_Pair, _Data)`` takes ``note`` first, ``_Data`` coming
    after ``_Pair``. A ``ClassVar`` is no field but holds its place: a field
    a later class writes of its name takes it, before the fields after it.

    Each base's own order was read whole, the last base's first, so
    ``Diamond`` read ``note, data`` and ``Again`` read ``data, note``, and
    the ``ClassVar`` held no place: the caller's array filled a text, and a
    copy handed to the place of ``data`` passed while one handed to the
    text was refused as made twice.
    """
    found = _findings(tmp_path, orders=_RESOLUTION_ORDERS)
    assert found == {
        ("build_diamond", "Diamond.data", "values"),
        ("build_diamond_copy", "OwnedDiamond.data (copied twice)", ""),
        ("build_again", "Again.data", "values"),
        ("build_kinded", "Kinded.kind", "values"),
    }


def test_an_attribute_takes_the_annotation_of_its_resolution_order(
    tmp_path: pathlib.Path,
) -> None:
    """A class reads an attribute from the first class of its method
    resolution order that annotates it: ``Holder(_Left, _Right)``, both on
    ``_Base``, resolves ``_Left, _Right, _Base``, so ``cache`` is the array
    ``_Right`` annotates, and a method storing the caller's array there
    keeps it.

    The bases were read depth first, ``_Left`` then its own base, so
    ``cache`` was the text ``_Base`` annotates and the array passed.
    """
    found = _findings(
        tmp_path,
        holder="""
        import numpy as np
        from numpy.typing import NDArray

        class _Base:
            cache: str | None = None

        class _Left(_Base):
            pass

        class _Right(_Base):
            cache: NDArray[np.float64] | None = None

        class Holder(_Left, _Right):
            def keep(self, values):
                self.cache = values
        """,
    )
    assert found == {("Holder.keep", "self.cache", "values")}


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


#: A ``def`` and a class of one name, each standing where a call reaches the
#: name: the class a record that keeps what it is given, saved beside the
#: ``def`` that writes into its array, and a record that copies, replaced by
#: a ``def`` that keeps the array; and a name bound to that record in one
#: branch and to a function that keeps the array in the other.
_RECORD_OR_DEF = """
import os
from dataclasses import dataclass

from numpy.typing import NDArray

from ._internal.frozen import OwnsArrays

def fill(frames, n):
    frames[0] = 1.0

saved = fill

@dataclass(frozen=True)
class fill:
    frames: NDArray[np.float64]
    n: int

if os.environ.get("RUN"):
    writer = saved
else:
    writer = fill

@dataclass(frozen=True)
class Box(OwnsArrays):
    frames: NDArray[np.float64]
    times: NDArray[np.float64]

_KEPT = []

def keep_it(frames, times):
    _KEPT.append(frames)
    return frames

if os.environ.get("RUN"):
    make = Box
else:
    make = keep_it

def Box(frames, times):
    _KEPT.append(frames)
    return frames
"""


@pytest.mark.parametrize(
    ("body", "reason"),
    [
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                writer(frames, n)
                return Run(frames=handed_over(frames), times=np.arange(n))
            """,
            "frames is read where it may be kept",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                return Box(frames=handed_over(frames), times=np.arange(n))
            """,
            "it is not an argument of a record that inherits OwnsArrays",
        ),
        (
            """
            def run(n):
                frames = np.zeros((n, 3))
                return make(frames=handed_over(frames), times=np.arange(n))
            """,
            "it is not an argument of a record that inherits OwnsArrays",
        ),
    ],
    ids=["class-beside-a-saved-def", "def-after-the-record", "record-or-a-function"],
)
def test_a_handover_reads_every_def_and_class_a_call_may_reach(
    tmp_path: pathlib.Path, body: str, reason: str
) -> None:
    """A call that may build the class a saved ``def`` shares its name with
    may keep the array; a call of the name a later ``def`` took from a record
    that copies runs the ``def``, which builds no record; and a call of a
    name bound to that record in one branch and to a function in the other
    may run the function.

    Each was read as one of the two: the saved ``def`` alone wrote into the
    array, and the record class was what the other two built, whatever the
    name held where it was read, so all three handovers passed.
    """
    found = _handovers(tmp_path, _RECORD_OR_DEF + textwrap.dedent(body))
    assert len(found) == 1, found
    ((function, sink),) = found
    assert function == "run"
    assert sink.startswith("handed_over(...): " + reason), sink


#: Two records that copy bound to one name in two branches, a record that
#: copies written in each branch, and a name bound to a record that copies in
#: one branch and to one that keeps what it is given in the other.
_EITHER_RECORD = """
import os
from dataclasses import dataclass

from numpy.typing import NDArray

from ._internal.frozen import OwnsArrays

@dataclass(frozen=True)
class Other(OwnsArrays):
    frames: NDArray[np.float64] | None
    times: NDArray[np.float64]

if os.environ.get("RUN"):
    either = Run
    mixed = Run

    @dataclass(frozen=True)
    class Shown(OwnsArrays):
        frames: NDArray[np.float64] | None
        times: NDArray[np.float64]
else:
    either = Other
    mixed = _Plain

    @dataclass(frozen=True)
    class Shown(OwnsArrays):
        frames: NDArray[np.float64] | None
        times: NDArray[np.float64]
"""


@pytest.mark.parametrize(
    ("name", "refused"),
    [
        ("either", None),
        ("Shown", None),
        ("mixed", "it is not an argument of a record that inherits OwnsArrays"),
    ],
    ids=["two-records-that-copy", "a-class-in-each-branch", "one-that-keeps-it"],
)
def test_a_handover_to_a_record_that_copies_whichever_path_runs_passes(
    tmp_path: pathlib.Path, name: str, refused: str | None
) -> None:
    """An array handed over to either of two records that copy, bound to one
    name in two branches, or to a class that copies written in each branch,
    goes into a record that copies whichever path runs; one that may go into
    a record that keeps what it is given is refused.

    The check took a call for the argument of a record only where it named
    one key that built one ``class`` statement, so it refused the first two
    as well.
    """
    body = f"""
    def run(n):
        frames = np.zeros((n, 3))
        return {name}(frames=handed_over(frames), times=np.arange(n))
    """
    found = _handovers(tmp_path, _EITHER_RECORD + textwrap.dedent(body))
    assert found == (
        set() if refused is None else {("run", f"handed_over(...): {refused}")}
    )


#: What a factory defines of its own: a record that copies, and the list a
#: ``def`` of the record's name keeps what it is given in.
_LOCAL_RECORD = """
from dataclasses import dataclass

from numpy.typing import NDArray

from ._internal.frozen import OwnsArrays

_KEPT = []
"""


@pytest.mark.parametrize(
    ("body", "refused"),
    [
        (
            """
            def run(n):
                @dataclass(frozen=True)
                class Box(OwnsArrays):
                    frames: NDArray[np.float64]

                def Box(frames):
                    _KEPT.append(frames)
                    return frames

                frames = np.zeros(n)
                return Box(frames=handed_over(frames))
            """,
            "run",
        ),
        (
            """
            def run(n):
                if n > 1:
                    @dataclass(frozen=True)
                    class Box(OwnsArrays):
                        frames: NDArray[np.float64]
                else:
                    def Box(frames):
                        _KEPT.append(frames)
                        return frames
                frames = np.zeros(n)
                return Box(frames=handed_over(frames))
            """,
            "run",
        ),
        (
            """
            def factory():
                @dataclass(frozen=True)
                class Box(OwnsArrays):
                    frames: NDArray[np.float64]

                def Box(frames):
                    _KEPT.append(frames)
                    return frames

                def run(n):
                    frames = np.zeros(n)
                    return Box(frames=handed_over(frames))

                return run
            """,
            "factory.run",
        ),
        (
            """
            def run(n):
                def Box(frames):
                    _KEPT.append(frames)
                    return frames

                @dataclass(frozen=True)
                class Box(OwnsArrays):
                    frames: NDArray[np.float64]

                frames = np.zeros(n)
                return Box(frames=handed_over(frames))
            """,
            None,
        ),
        (
            """
            def factory():
                def Box(frames):
                    _KEPT.append(frames)
                    return frames

                @dataclass(frozen=True)
                class Box(OwnsArrays):
                    frames: NDArray[np.float64]

                def run(n):
                    frames = np.zeros(n)
                    return Box(frames=handed_over(frames))

                return run
            """,
            None,
        ),
    ],
    ids=[
        "def-after-the-class",
        "one-in-each-branch",
        "around-def-after-the-class",
        "class-after-the-def",
        "around-class-after-the-def",
    ],
)
def test_a_handover_reads_the_def_or_class_its_function_defines(
    tmp_path: pathlib.Path, body: str, refused: str | None
) -> None:
    """A ``def`` a function writes after a ``class`` of its name, or in the
    branch beside it, may be what the name calls where the record is built,
    and it keeps the array; so may one the function around it writes, from
    the ``def`` of the function that calls it on. A ``class`` written after
    the ``def`` replaces it there.

    The name was read as the class whenever the function defined one of it,
    so the handover passed where the ``def`` stands.
    """
    found = _handovers(tmp_path, _LOCAL_RECORD + textwrap.dedent(body))
    if refused is None:
        assert found == set()
        return
    assert found == {
        (
            refused,
            "handed_over(...): it is not an argument of a record that inherits "
            "OwnsArrays",
        )
    }


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


@pytest.mark.whole_tree
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


#: The imports of the records below.
_RECORDS_HEAD = """
import contextlib
import sys
from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

from ._internal.frozen import OwnsArrays, handed_over, read_only_copy
"""

#: A base whose own ``__post_init__`` copies ``data``, and a record over it
#: whose ``__init__`` is the one ``@dataclass`` writes for the base.
_COPYING_BASE = """
@dataclass(frozen=True)
class Base:
    data: NDArray[np.float64]

    def __post_init__(self):
        object.__setattr__(self, "data", read_only_copy(self.data))
"""


@pytest.mark.parametrize(
    ("base", "body", "expected"),
    [
        # A subclass's hook that hands on to none replaces the base's.
        (
            _COPYING_BASE,
            """
            class Plain(Base):
                def __post_init__(self):
                    pass

            def make(data):
                return Plain(data)
            """,
            {("make", "Plain.data", "data")},
        ),
        (
            _COPYING_BASE,
            """
            class Plain(Base):
                def __post_init__(self):
                    super().__post_init__()

            def make(data):
                return Plain(data)
            """,
            set(),
        ),
        # A hook declared for the type checker alone is none: the base's
        # generated __init__ calls no hook, the subclass's included.
        (
            "",
            """
            @dataclass(frozen=True)
            class Base:
                data: NDArray[np.float64]

                if TYPE_CHECKING:
                    def __post_init__(self) -> None: ...

            class Plain(Base):
                def __post_init__(self):
                    object.__setattr__(self, "data", read_only_copy(self.data))

            def make(data):
                return Plain(data)
            """,
            {("make", "Plain.data", "data")},
        ),
        (
            "",
            """
            @dataclass(frozen=True)
            class Base:
                data: NDArray[np.float64]

                def __post_init__(self) -> None:
                    pass

            class Plain(Base):
                def __post_init__(self):
                    object.__setattr__(self, "data", read_only_copy(self.data))

            def make(data):
                return Plain(data)
            """,
            set(),
        ),
    ],
    ids=["override", "delegates", "type-checking-hook", "running-hook"],
)
def test_the_hook_a_call_runs_is_the_one_its_order_resolves(
    tmp_path: pathlib.Path,
    base: str,
    body: str,
    expected: set[tuple[str, str, str]],
) -> None:
    """The ``__post_init__`` a record's constructor calls is the first its
    method resolution order holds that a run defines, and it copies what it
    copies itself or what a hook it hands on to does.

    Every hook of the order was read as copying what any of them copies, so
    ``Plain``, whose own hook replaces the base's and copies nothing, was
    read as copying ``data``; and a ``__post_init__`` declared under ``if
    TYPE_CHECKING:`` was read as one the base's generated ``__init__``
    calls, so ``Plain``'s copying hook, which never runs, was credited.
    """
    source = _RECORDS_HEAD + base + textwrap.dedent(body)
    assert _findings(tmp_path, records=source) == expected


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (
            """
            @dataclass(frozen=True)
            class Rec:
                data: NDArray[np.float64]

                __init__ = _Keeper.__init__

                def __post_init__(self):
                    object.__setattr__(self, "data", read_only_copy(self.data))
            """,
            {("make", "Rec.data", "data")},
        ),
        (
            """
            @dataclass(frozen=True)
            class Rec:
                data: NDArray[np.float64]

                def __post_init__(self):
                    object.__setattr__(self, "data", read_only_copy(self.data))
            """,
            set(),
        ),
    ],
    ids=["assigned", "generated"],
)
def test_an_init_a_record_binds_by_assignment_is_the_one_a_call_runs(
    tmp_path: pathlib.Path, body: str, expected: set[tuple[str, str, str]]
) -> None:
    """A record whose body binds ``__init__ = _Keeper.__init__`` keeps that
    one, which ``@dataclass`` does not replace: a call runs it, and it
    keeps the caller's array and calls no hook, so the copying hook never
    runs. With no assignment, the generated one runs and calls the hook.

    The assignment was passed over for the ``__init__`` ``@dataclass``
    would write, which calls the hook, so the copy was credited.
    """
    source = (
        _RECORDS_HEAD
        + textwrap.dedent(
            """
            class _Keeper:
                def __init__(self, data):
                    object.__setattr__(self, "data", data)
            """
        )
        + textwrap.dedent(body)
        + "\ndef make(data):\n    return Rec(data)\n"
    )
    assert _findings(tmp_path, records=source) == expected


#: A record with no hook, whose generated ``__init__`` calls none, and the
#: start of a module that decorates a class over it.
_KEEPING_BASE = """
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from ._internal.frozen import read_only_copy


@dataclass
class Base:
    data: NDArray[np.float64]
"""

#: A class over :data:`_KEEPING_BASE` whose hook copies, built by ``make``.
_COPYING_OVER = """
@dataclass
class Sub(Base):
    def __post_init__(self):
        object.__setattr__(self, "data", read_only_copy(self.data))


def make(data):
    return Sub(data)
"""


@pytest.mark.parametrize(
    ("rebinding", "expected"),
    [
        (
            """
            def dataclass(cls):
                return cls
            """,
            {("make", "Sub.data", "data")},
        ),
        ("dataclass = lambda cls: cls", {("make", "Sub.data", "data")}),
        (
            """
            if (dataclass := lambda cls: cls):
                pass
            """,
            {("make", "Sub.data", "data")},
        ),
        (
            """
            try:
                from dataclasses import dataclass
            except ImportError:
                def dataclass(cls):
                    return cls
            """,
            {("make", "Sub.data", "data")},
        ),
        ("", set()),
    ],
    ids=["defined", "assigned", "walrus", "either", "imported"],
)
def test_a_decorator_is_read_through_the_bindings_that_stand_where_the_class_runs(
    tmp_path: pathlib.Path, rebinding: str, expected: set[tuple[str, str, str]]
) -> None:
    """``@dataclass`` is what the name holds where the ``class`` statement
    runs: once a ``def``, an assignment or a ``:=`` has replaced the import,
    ``Sub`` is no record, a call of it runs the ``__init__`` ``Base``'s
    decorator wrote, which calls no hook, and the caller's array is kept;
    with an import and a fallback that may each stand, either may run. With
    the import alone, the generated ``__init__`` calls the copying hook.

    The decorator was read by its spelling, so each replacement was read as
    ``dataclasses``' own, writing an ``__init__`` that calls the copying
    hook, and the array kept passed.
    """
    source = _KEEPING_BASE + textwrap.dedent(rebinding) + textwrap.dedent(_COPYING_OVER)
    assert _findings(tmp_path, records=source) == expected


@pytest.mark.parametrize(
    ("imported", "exporting", "expected"),
    [
        ("from ._dc import dataclass", "from dataclasses import dataclass", set()),
        ("from pkg._dc import dataclass", "from dataclasses import dataclass", set()),
        (
            "from . import _dc\n\ndataclass = _dc.dataclass",
            "import dataclasses\n\ndataclass = dataclasses.dataclass",
            set(),
        ),
        (
            "import functools\n\nfrom ._dc import dataclass as _record\n\n"
            "dataclass = functools.partial(_record, eq=False)",
            "from dataclasses import dataclass",
            set(),
        ),
        (
            "from ._dc import dataclass",
            "def dataclass(cls):\n    return cls",
            {("make", "Sub.data", "data")},
        ),
    ],
    ids=["relative", "absolute", "alias", "partial", "own"],
)
def test_a_decorator_a_module_of_the_package_re_exports_is_read_through_it(
    tmp_path: pathlib.Path,
    imported: str,
    exporting: str,
    expected: set[tuple[str, str, str]],
) -> None:
    """``@dataclass`` taken from a module of the package is what that module
    took, and an alias of it is what it names: ``dataclasses``' own,
    through a relative import or an absolute one, an alias in either module
    or a ``functools.partial`` of it, so ``Sub``'s generated ``__init__``
    calls the copying hook and the caller's array is not kept. A module that
    writes a ``dataclass`` of its own makes ``Sub`` no record, and
    ``Sub(data)`` runs the ``__init__`` ``Base``'s decorator wrote, which
    keeps it.

    An import was read as it is written and every assignment as replacing
    the decorator, so each of these was read as no record decorator,
    ``Sub`` as running ``Base``'s ``__init__``, and the array as kept.
    """
    source = _KEEPING_BASE + imported + "\n" + textwrap.dedent(_COPYING_OVER)
    found = _findings(tmp_path, records=source, _dc=exporting + "\n")
    assert found == expected


@pytest.mark.parametrize(
    ("rebinding", "expected"),
    [
        (
            "import functools\n\ndataclass = functools.partial(dataclass, init=False)",
            {("make", "Sub.data", "data")},
        ),
        (
            "import functools\n\n_OPTIONS = {'init': False}\n"
            "dataclass = functools.partial(dataclass, **_OPTIONS)",
            {("make", "Sub.data", "data")},
        ),
        ("dataclass = dataclass(eq=False)", set()),
        ("dataclass = dataclass(init=False)", {("make", "Sub.data", "data")}),
        (
            "import functools\n\ndataclass = functools.partial(dataclass, eq=False)",
            set(),
        ),
    ],
    ids=[
        "partial-init-off",
        "partial-double-star",
        "called",
        "called-init-off",
        "partial",
    ],
)
def test_what_an_alias_of_the_decorator_presets_is_read_with_it(
    tmp_path: pathlib.Path, rebinding: str, expected: set[tuple[str, str, str]]
) -> None:
    """An alias of ``@dataclass`` that presets ``init=False``, a
    ``functools.partial`` of it or a call of it with keywords alone, writes
    ``Sub`` no ``__init__``, so ``Sub(data)`` runs the one ``Base``'s
    decorator wrote, which calls no hook and keeps the caller's array; one
    whose ``**`` may preset it is read both ways. A call of the decorator
    with keywords alone that leaves ``init`` on writes the ``__init__`` that
    calls the copying hook, as a partial that presets ``eq=False`` does.

    What a partial presets was not read, so ``init=False`` was read as
    writing an ``__init__`` that copies, and ``dataclass(eq=False)`` was
    read as another decorator, and the copy its hook makes was missed.
    """
    source = _KEEPING_BASE + rebinding + "\n" + textwrap.dedent(_COPYING_OVER)
    assert _findings(tmp_path, records=source) == expected


#: A record with no hook, one over it whose hook copies, and a record whose
#: ``__init__`` is written by hand over that.
_HAND_WRITTEN_HEAD = """
@dataclass(frozen=True)
class Plain:
    data: NDArray[np.float64]

@dataclass(frozen=True)
class Rec(Plain):
    def __post_init__(self):
        object.__setattr__(self, "data", read_only_copy(self.data))
"""


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (
            """
            def __init__(self, data, check=False):
                Plain.__init__(self, data)
                if check:
                    self.__post_init__()
            """,
            {("make", "Sub.data", "data")},
        ),
        (
            """
            def __init__(self, data):
                Plain.__init__(self, data)
                hook = self.__post_init__
            """,
            {("make", "Sub.data", "data")},
        ),
        (
            """
            def __init__(self, data):
                other = object.__new__(Rec)
                Rec.__init__(other, data)
                Plain.__init__(self, data)
            """,
            {("make", "Sub.data", "data")},
        ),
        (
            """
            def __init__(self, data):
                with contextlib.suppress(ValueError):
                    Rec.__init__(self, data)
            """,
            {("make", "Sub.data", "data")},
        ),
        (
            """
            def __init__(self, data):
                Plain.__init__(self, data)
                self.__post_init__()
            """,
            set(),
        ),
        (
            """
            def __init__(self, data):
                Rec.__init__(self, data)
            """,
            set(),
        ),
    ],
    ids=[
        "one-branch",
        "named-only",
        "other-instance",
        "swallowed",
        "called",
        "handed-on",
    ],
)
def test_a_hand_written_init_runs_the_hook_it_calls_on_self_on_every_path(
    tmp_path: pathlib.Path, body: str, expected: set[tuple[str, str, str]]
) -> None:
    """An ``__init__`` written by hand runs ``__post_init__`` when it calls
    ``self.__post_init__()``, or hands ``self`` to an ``__init__`` that
    does, on every path a call that returns takes.

    Any mention of ``__post_init__`` in its body was read as a call, so a
    hook called on one branch, or only looked up, was credited; any
    ``Base.__init__(...)`` was read as a hand-off, so ``Rec.__init__(other,
    data)``, which copies into another instance, was credited to ``self``;
    and so was one in a ``with`` block, whose context manager may swallow
    what the hook raises before it copies.
    """
    source = (
        _RECORDS_HEAD
        + _HAND_WRITTEN_HEAD
        + "\n@dataclass(frozen=True, init=False)\nclass Sub(Rec):\n"
        + textwrap.indent(textwrap.dedent(body), "    ")
        + "\ndef make(data):\n    return Sub(data)\n"
    )
    assert _findings(tmp_path, records=source) == expected


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        ("NO_INIT = False\n", {("make", "Rec.data", "data")}),
        ("NO_INIT = True\n", set()),
        ("NO_INIT = sys.flags.optimize > 9\n", {("make", "Rec.data", "data")}),
    ],
    ids=["false", "true", "unread"],
)
def test_an_init_option_is_read_through_the_name_that_holds_it(
    tmp_path: pathlib.Path, option: str, expected: set[tuple[str, str, str]]
) -> None:
    """``@dataclass(init=NO_INIT)`` reads the constant its module binds the
    name to, and a value the guard cannot read both ways: the ``__init__``
    the decorator writes, or the base's, which calls no hook.

    A name was read as ``init=True``, so the copy the record's own hook
    makes was credited to a call that runs the base's ``__init__``.
    """
    source = (
        _RECORDS_HEAD
        + option
        + """
@dataclass(frozen=True)
class Base:
    data: NDArray[np.float64]

@dataclass(frozen=True, init=NO_INIT)
class Rec(Base):
    def __post_init__(self):
        object.__setattr__(self, "data", read_only_copy(self.data))

def make(data):
    return Rec(data)
"""
    )
    assert _findings(tmp_path, records=source) == expected


#: A record that keeps what it is built with.
_KEPT_REC = """
@dataclass(frozen=True)
class Rec:
    data: NDArray[np.float64]
"""


@pytest.mark.parametrize(
    "body",
    [
        # A class method a later plain method of its name replaces.
        """
        class Maker:
            @classmethod
            def pick(cls, data):
                return read_only_copy(data)

            def pick(self, data):
                return data

            @classmethod
            def build(cls, holder, data):
                return Rec(cls.pick(holder, data))
        """,
        """
        class Maker:
            @classmethod
            def pick(cls, data):
                return read_only_copy(data)

            def pick(self, data):
                return data

            def build(self, holder, data):
                return Rec(Maker.pick(holder, data))
        """,
        # A plain method called through ``cls`` takes the call's first argument.
        """
        class Maker:
            def pick(self, data):
                return data

            @classmethod
            def build(cls, holder, data):
                return Rec(cls.pick(holder, data))
        """,
    ],
    ids=["replaced-through-cls", "replaced-through-name", "plain-through-cls"],
)
def test_a_method_call_binds_each_definition_it_reaches_by_its_kind(
    tmp_path: pathlib.Path, body: str
) -> None:
    """A call through ``cls`` or the class's name fills the first parameter
    of a class method with the class, and hands a plain method the call's
    first argument there, whichever definition of the name the call reaches.

    A call through ``cls`` was read as binding the first parameter of every
    definition, and one through the class's name as binding it when any
    definition of the name was a class method, so ``pick(self, data)`` took
    ``holder`` as ``data`` and ``holder`` was reported as kept in
    ``Rec.data`` beside ``data``.
    """
    source = _RECORDS_HEAD + _KEPT_REC + textwrap.dedent(body)
    assert _findings(tmp_path, records=source) == {("Maker.build", "Rec.data", "data")}


def test_cls_and_type_of_self_build_through_the_constructor_they_run(
    tmp_path: pathlib.Path,
) -> None:
    """``cls(data)`` and ``type(self)(data)`` run the constructor a call of
    the class runs: the base's, when the record is told ``init=False`` or is
    a class that is no record over one, with the base's fields.

    They were read with the class's own fields, so a field its own
    declaration leaves out of ``__init__`` dropped the array the base's
    constructor keeps, and a class that is no record kept nothing.
    """
    source = (
        _RECORDS_HEAD
        + """
@dataclass(frozen=True)
class Base:
    data: NDArray[np.float64]

@dataclass(frozen=True, init=False)
class Rec(Base):
    data: NDArray[np.float64] = field(init=False)

    @classmethod
    def build(cls, data):
        return cls(data)

    def again(self, data):
        return type(self)(data)

class Over(Base):
    @classmethod
    def build(cls, data):
        return cls(data)
"""
    )
    assert _findings(tmp_path, records=source) == {
        ("Rec.build", "Rec.data", "data"),
        ("Rec.again", "Rec.data", "data"),
        ("Over.build", "Over.data", "data"),
    }


def test_a_class_over_an_owning_record_is_a_record_it_builds(
    tmp_path: pathlib.Path,
) -> None:
    """A class that is no record over one that inherits ``OwnsArrays`` runs
    the record's generated constructor, which copies: a copy handed to it is
    made twice, and an array built for it passes through ``handed_over``.

    Only a record was read as built, so the second copy went unreported and
    ``handed_over`` was refused as handing no record that copies.
    """
    source = (
        _RECORDS_HEAD
        + """
@dataclass(frozen=True)
class Base(OwnsArrays):
    data: NDArray[np.float64]

class Rec(Base):
    pass

def twice(data):
    return Rec(read_only_copy(data))

def built(n):
    data = np.zeros(n)
    return Rec(handed_over(data))
"""
    )
    assert _findings(tmp_path, records=source) == {
        ("twice", "Rec.data (copied twice)", "")
    }
    root = tmp_path / "pkg"
    refused = caa.handovers_in(sorted(root.rglob("*.py")), root)
    assert [(f.function, f.sink) for f in refused] == []


def test_a_class_over_a_base_written_in_each_branch_keeps_what_either_keeps(
    tmp_path: pathlib.Path,
) -> None:
    """A class that is no record over a base written in each branch of an
    ``if`` runs either base's generated constructor, and keeps what each
    keeps.

    The two constructors disagreeing was read as none running, so the call
    kept nothing though both keep ``data``.
    """
    source = (
        _RECORDS_HEAD
        + """
if sys.platform == "win32":
    @dataclass(frozen=True)
    class Base:
        data: NDArray[np.float64]
else:
    @dataclass(frozen=True)
    class Base:
        data: NDArray[np.float64]
        label: str = ""

class Rec(Base):
    pass

def make(data):
    return Rec(data)
"""
    )
    assert _findings(tmp_path, records=source) == {("make", "Rec.data", "data")}


def test_an_init_var_is_handed_to_the_hook_and_held_by_no_field(
    tmp_path: pathlib.Path,
) -> None:
    """An ``InitVar`` takes a place of the constructor and is handed to
    ``__post_init__``, and the record holds it in no field: what the hook
    stores of it is read in the hook.

    It was read as a field the record keeps, so ``Rec(3, data)`` was
    reported as keeping ``data`` in ``Rec.seed``, which no record has.
    """
    source = (
        _RECORDS_HEAD
        + """
@dataclass(frozen=True)
class Base:
    size: int
    seed: InitVar[NDArray[np.float64]]

    def __post_init__(self, seed):
        pass

class Rec(Base):
    pass

def make(data):
    return Rec(3, data)

@dataclass(frozen=True)
class Stored:
    size: int
    seed: InitVar[NDArray[np.float64]]
    kept: NDArray[np.float64] = field(init=False)

    def __post_init__(self, seed):
        object.__setattr__(self, "kept", seed)

def store(data):
    return Stored(3, data)
"""
    )
    assert _findings(tmp_path, records=source) == {
        ("Stored.__post_init__", "Stored.kept", "seed")
    }
