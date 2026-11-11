#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The one way the library warns (``phonometry._internal.warnings.warn_caller``).

A warning is shown at a file and a line, and Python keys its memory of what it
has shown on that line: under the ``default`` action a warning attributed to a
library line prints once per process, so the same call in a later notebook
cell is silent, and a filter by the caller's module misses it. The helper skips
every frame of the package and the few frames that run the package's code from
elsewhere, so each route to a warning, however deep, lands on the caller's own
line.

The routes below run from code compiled with a file name inside the package
and with the globals of a module of the package, as the library's own code is.
"""

from __future__ import annotations

import dataclasses
import os
import sys
import types
import warnings
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import phonometry
from phonometry._internal import warnings as library_warnings
from phonometry._internal.warnings import PhonometryWarning, warn_caller
from phonometry.simulation import fdtd

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

_PROBE = """
import contextlib
import dataclasses
import functools

from phonometry._internal.warnings import advisories_held, warn_caller


class ProbeWarning(UserWarning):
    pass


def advise():
    warn_caller("advised", ProbeWarning)


def held(*, refuse=False):
    with advisories_held():
        advise()
        warn_caller("advised again", ProbeWarning)
        if refuse:
            raise ValueError("refused")
    return 1


def nested(*, refuse=False):
    with advisories_held():
        held()
        if refuse:
            raise ValueError("refused after the inner block")
    return 2


def deeper():
    advise()


def through(callback):
    return callback()


@dataclasses.dataclass
class Record:
    x: int

    def __post_init__(self):
        advise()


class Holder:
    @functools.cached_property
    def cached(self):
        advise()
        return 1


@contextlib.contextmanager
def session():
    yield
    advise()
"""


@pytest.fixture
def probe(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """A module of the package, as the import system would have read it."""
    module = types.ModuleType("phonometry._attribution_probe")
    monkeypatch.setitem(sys.modules, module.__name__, module)
    filename = f"{library_warnings._PACKAGE_PREFIX}_attribution_probe.py"
    exec(compile(_PROBE, filename, "exec"), module.__dict__)  # noqa: S102
    return module


@contextmanager
def _recorded() -> Iterator[list[warnings.WarningMessage]]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        yield caught


def _here() -> int:
    """The line after the one that calls this, where a test makes its call."""
    return sys._getframe(1).f_lineno + 1


def test_a_warning_two_library_frames_deep_names_the_callers_line(
    probe: types.ModuleType,
) -> None:
    with _recorded() as caught:
        line = _here()
        probe.deeper()
    assert [(w.filename, w.lineno) for w in caught] == [(__file__, line)]


def test_a_records_post_init_warns_at_the_line_that_built_the_record(
    probe: types.ModuleType,
) -> None:
    """The ``__init__`` a dataclass generates is compiled from ``<string>``.

    Skipping the package's files alone stopped at that frame, so a record's
    advisory was reported at ``<string>``, keyed in the package module's own
    memory of warnings and shown once per process.
    """
    with _recorded() as caught:
        line = _here()
        probe.Record(1)
    assert [(w.filename, w.lineno) for w in caught] == [(__file__, line)]


def test_a_replaced_record_warns_at_the_line_that_replaced_it(
    probe: types.ModuleType,
) -> None:
    record = probe.Record.__new__(probe.Record)
    record.x = 0
    with _recorded() as caught:
        line = _here()
        dataclasses.replace(record, x=2)
    assert [(w.filename, w.lineno) for w in caught] == [(__file__, line)]


def test_a_cached_property_warns_at_the_line_that_read_it(
    probe: types.ModuleType,
) -> None:
    holder = probe.Holder()
    with _recorded() as caught:
        line = _here()
        assert holder.cached == 1
    assert [(w.filename, w.lineno) for w in caught] == [(__file__, line)]


def test_a_context_managers_exit_warns_in_the_callers_file(
    probe: types.ModuleType,
) -> None:
    with _recorded() as caught, probe.session():
        pass
    assert [w.filename for w in caught] == [__file__]


def test_a_callback_the_library_runs_is_the_caller_of_what_it_calls(
    probe: types.ModuleType,
) -> None:
    """The innermost line outside the package is the one that made the call."""

    def callback() -> None:
        nonlocal line
        line = _here()
        probe.advise()

    line = 0
    with _recorded() as caught:
        probe.through(callback)
    assert [(w.filename, w.lineno) for w in caught] == [(__file__, line)]


def test_code_compiled_from_a_string_by_the_caller_is_the_callers(
    probe: types.ModuleType,
) -> None:
    """``python -c`` runs ``<string>`` in ``__main__``: that frame is the caller's."""
    with _recorded() as caught:
        exec(  # noqa: S102
            compile("probe.deeper()", "<string>", "exec"),
            {"__name__": "__main__", "probe": probe},
        )
    assert [(w.filename, w.lineno) for w in caught] == [("<string>", 1)]


def test_a_held_advisory_is_issued_at_the_callers_line_once_the_block_ends(
    probe: types.ModuleType,
) -> None:
    with _recorded() as caught:
        line = _here()
        assert probe.held() == 1
    assert [(w.filename, w.lineno, str(w.message)) for w in caught] == [
        (__file__, line, "advised"),
        (__file__, line, "advised again"),
    ]


@pytest.mark.parametrize("call", ["held", "nested"])
def test_a_refusal_in_the_block_drops_every_advisory_it_held(
    probe: types.ModuleType, call: str
) -> None:
    """Under ``-W error`` the caller meets the refusal, not the advisory before it."""
    function = getattr(probe, call)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        with pytest.raises(ValueError, match="refused"):
            function(refuse=True)


def test_a_block_inside_another_hands_its_advisories_to_the_outer_one(
    probe: types.ModuleType,
) -> None:
    with _recorded() as caught:
        line = _here()
        assert probe.nested() == 2
    assert [(w.filename, w.lineno) for w in caught] == [(__file__, line)] * 2
    assert library_warnings._HELD.get() is None


def test_a_warning_instance_is_raised_again_with_its_own_class() -> None:
    class RelayedWarning(PhonometryWarning):
        pass

    with _recorded() as caught:
        line = _here()
        warn_caller(RelayedWarning("from the node"))
    assert [(w.category, str(w.message)) for w in caught] == [
        (RelayedWarning, "from the node")
    ]
    assert (caught[0].filename, caught[0].lineno) == (__file__, line)


def test_the_skipped_prefix_is_the_package_directory_as_imported() -> None:
    prefix = library_warnings._PACKAGE_PREFIX
    assert phonometry.__file__ == f"{prefix}__init__.py"
    assert fdtd.__file__.startswith(prefix)
    # The trailing separator keeps a sibling named like the package outside.
    assert not f"{prefix[:-1]}_extra{os.sep}module.py".startswith(prefix)


def _warns(prefix: str) -> None:
    warnings.warn("fell back", UserWarning, skip_file_prefixes=(prefix,))


def _hands_on(call: Callable[..., None], *args: object) -> None:
    call(*args)


def _read_from(function: Callable[..., None], filename: str) -> Callable[..., None]:
    """*function* as if the interpreter had read it from *filename*."""
    code = function.__code__.replace(co_filename=filename)
    return types.FunctionType(code, function.__globals__)


def test_a_dot_in_the_import_path_still_skips_the_whole_package() -> None:
    """A ``/./`` in a ``sys.path`` entry stays in every frame's file name.

    The warning is raised two frames deep in the package, so the frame it
    skips by its file name is the outer one: a prefix normalised through
    ``Path`` loses the ``/./`` and leaves the warning on that library line.
    """
    root = f"{os.sep}site{os.sep}.{os.sep}"
    package = f"{root}phonometry{os.sep}_internal{os.sep}"
    helper, module, script = (
        f"{package}warnings.py",
        f"{package}module.py",
        f"{root}script.py",
    )
    prefix = library_warnings._package_prefix(helper)
    assert prefix == f"{root}phonometry{os.sep}"
    warns = _read_from(_warns, helper)
    library = _read_from(_hands_on, module)
    caller = _read_from(_hands_on, script)
    normalised = f"{Path(helper).parent.parent}{os.sep}"
    with _recorded() as caught:
        caller(library, warns, prefix)
        caller(library, warns, normalised)
    assert [w.filename for w in caught] == [script, module]
