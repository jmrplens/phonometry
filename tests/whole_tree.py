#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The tests that read the whole repository, and the count that tells one.

Some tests read the repository's own files and assert on all of them: a
guard run over the package, the scripts, the documentation, the site or the
committed figures, a census of every public function or record, a generator
run over the package. What they judge is the repository's own text, which
neither the numba-jitted kernel nor the dependency floors change, so the two
CI jobs that exist for those, "tests (numba-jitted kernel)" and "Library
tests at the dependency floors", run ``pytest --without-whole-tree``, and the
nine jobs of the test matrix run these tests. Such a test carries the mark,
on itself or, for a module of them, as the module's ``pytestmark``::

    @pytest.mark.whole_tree

This plugin, which ``conftest.py`` loads, takes the option and deselects the
marked tests when it is given. No such module fails on import, as a module of
the figure tooling can at the floors (``pinned_stack.py``), so it is collected
as any other, and the mark works on one test as it does on a module.

What makes a test one is what it reads, so that is what this plugin checks.
While a test sets up and runs, it counts the files of the repository's own
trees (:data:`TREES`) the test opens, the files each fixture it was given
opened in the setup it was given included, when that setup is cached past
the test: a fixture of a wider scope, or one a parametrization with a scope
of its own caches. The fixtures are those pytest resolved for the test, the
ones it names and the ones it or a fixture asks for by name with
``request.getfixturevalue``, and every one each of them reached in its own
setup, as a parameter or by name, so the one of a wider scope that a
fixture of a narrower scope overrides and asks for under its own name
counts too. An unmarked test that opened :data:`LIMIT` of them or more
fails, saying how many and from which trees. A test that reads the tree to
find what it then runs through the library, so that the kernel or a floor
dependency decides its verdict, stays in those jobs: it stands in
:data:`RUNS_THE_LIBRARY` with its reason.

The count leaves out a file the import system opens, so that importing a
module of the package for the first time is no read of it, and a file the
package opens itself (the remote runner ships its own modules), which is the
library at work. It cannot see a file a child process reads, a test that
lists the tree's names without opening its files, a test that takes what
a guard's own cache kept from an earlier test of its worker without opening
anything, or a fixture another fixture asks for by name in its setup when
the test that set that one up had reached the first before it, for a later
test that takes the second from its cache: the first was already resolved,
so asking for it again leaves no trace. ``linecache``, which
:func:`inspect.getsource` reads through, is emptied before each test, so a
source read that way is seen. In the two jobs that pass the option no marked
test runs, so what a guard's cache holds there an unmarked test read, and
the first one to read it fails.
"""

from __future__ import annotations

import contextlib
import linecache
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Iterator
    from types import FrameType

#: The mark a test that reads the whole repository carries, and the option
#: that leaves the marked tests out.
MARK = "whole_tree"
OPTION = "--without-whole-tree"

#: The repository.
ROOT = Path(__file__).resolve().parent.parent

#: The trees whose files a test that reads the repository opens, each with the
#: ending a file of it has to count (``""``: any file): the package's modules,
#: the scripts, the documentation, the site, the suite's own modules and
#: ``.github/``, where the committed figures are. The package's data and the
#: suite's oracle data are what library tests read through the library; they
#: do not count.
TREES = {
    "src": ".py",
    "scripts": "",
    "docs": "",
    "site": "",
    "tests": ".py",
    ".github": "",
}

#: Directories of those trees that hold nothing the repository wrote.
UNWRITTEN = frozenset({"__pycache__", "node_modules", "dist", ".astro"})

#: How many files of :data:`TREES` a test opens from which it reads the
#: repository whole. On 2026-11-06 the package held 469 modules, the scripts
#: 275 files, the documentation 236, the site 1,182, the suite 767 modules
#: and ``.github/`` 3,542 files, 3,332 of them figures, so a test that reads
#: one of them whole opens hundreds of files. A test that reads a smaller
#: part whole opens fewer (the 85 rows of the conformance package) and is
#: marked by review; the most a test that judges no part of the repository
#: opened was 50, the figure modules a clip test copies.
LIMIT = 100

#: The tests that open :data:`LIMIT` files of the trees or more and stay in
#: the numba and floors jobs, keyed ``"path::function"``, with the reason: what
#: they read is the list of what they run through the library, so the kernel
#: or a floor dependency decides their verdict.
RUNS_THE_LIBRARY: dict[str, str] = {
    "tests/test_result_plots.py::test_a_plot_returns_what_its_signature_promises": (
        "reads the plot methods' heads from the source, then builds each result "
        "and draws its plot, which the floor matplotlib and numpy decide"
    ),
    "tests/test_record_conversions.py::test_a_list_given_to_a_converted_field_is_held_converted": (
        "reads which fields convert from the source, then checks what the "
        "records the library built hold, which the floor numpy decides"
    ),
}

#: The files of :data:`TREES` a test, or a higher-scoped fixture, opened.
_OPENED = pytest.StashKey[set[str]]()


class TreeReads:
    """The files of :data:`TREES` under *root* each test and fixture opens.

    :meth:`audit` is an audit hook (:func:`sys.addaudithook`): the ``open``
    event comes with the path of every file the process opens, whichever
    way it is opened. A file counts for every set :meth:`counting` holds
    while it is opened: the test's, and each fixture's being set up, so a
    fixture set up inside another's setup counts for that one too.
    """

    def __init__(self, root: Path) -> None:
        self._root = root
        self._package = root / "src" / "phonometry"
        self._sets: list[set[str]] = []
        self._library: dict[str, bool] = {}
        #: What each fixture cached past a test opened, by ``(baseid, name)``,
        #: in the last setup of it, which is the one a test that uses it is
        #: given.
        self.fixtures: dict[tuple[str, str], set[str]] = {}
        #: The fixtures each of them reached in that setup, by the same key:
        #: those it takes as parameters and those it asked for by name, the
        #: one of a wider scope it overrides among them when it asked for
        #: its own name.
        self.reached: dict[tuple[str, str], tuple[tuple[str, str], ...]] = {}

    def forget(self, key: tuple[str, str]) -> None:
        """Let go of what a fixture's earlier setup, cached past its test, opened."""
        self.fixtures.pop(key, None)
        self.reached.pop(key, None)

    @contextlib.contextmanager
    def counting(self, opened: set[str]) -> Iterator[None]:
        """Add the files of the trees opened inside the block to *opened*."""
        self._sets.append(opened)
        try:
            yield
        finally:
            self._sets.pop()

    def audit(self, event: str, args: tuple[object, ...]) -> None:
        """Note a file of the trees opened for reading."""
        if event != "open" or not self._sets:
            return
        path, mode = args[0], args[1]
        if not isinstance(path, str | bytes | os.PathLike):
            return
        if isinstance(mode, str) and any(c in mode for c in "wax+"):
            return
        try:
            name = Path(os.fsdecode(path))
            if not name.is_absolute() or ".." in name.parts:
                name = name.resolve()
        except (OSError, TypeError, ValueError):
            return
        if not name.is_relative_to(self._root):
            return
        relative = name.relative_to(self._root)
        if (
            len(relative.parts) < 2
            or not relative.name.endswith(TREES.get(relative.parts[0], "/"))
            or UNWRITTEN.intersection(relative.parts)
            or self._opened_by_the_import_system_or_the_package(sys._getframe(1))
        ):
            return
        for opened in self._sets:
            opened.add(relative.as_posix())

    def _opened_by_the_import_system_or_the_package(
        self, frame: FrameType | None
    ) -> bool:
        while frame is not None:
            name = frame.f_code.co_filename
            known = self._library.get(name)
            if known is None:
                known = (
                    name.startswith("<frozen importlib")
                    or Path(name).name in ("_bootstrap.py", "_bootstrap_external.py")
                    or Path(name).is_relative_to(self._package)
                )
                self._library[name] = known
            if known:
                return True
            frame = frame.f_back
        return False

    def read_by(self, item: pytest.Item) -> set[str]:
        """The files *item* opened, and those the fixtures it was given opened.

        The fixtures are the ones its request resolved, each the one pytest
        gave it under its name: those it names, and those it or a fixture
        asked for by name with ``request.getfixturevalue``, which the names
        it was collected with leave out. Then each fixture any of them
        reached in its setup (:attr:`reached`), the one of a wider scope an
        override asks for under its own name among them, as far as they go.
        """
        nothing: set[str] = set()
        own = item.stash.get(_OPENED, nothing)
        opened = set(own)
        request = getattr(item, "_request", None)
        given: Iterable[pytest.FixtureDef[object]] = getattr(
            request, "_fixture_defs", {}
        ).values()
        waiting = [_key(fixturedef) for fixturedef in given]
        seen = set(waiting)
        while waiting:
            key = waiting.pop()
            opened |= self.fixtures.get(key, nothing)
            for further in self.reached.get(key, ()):
                if further not in seen:
                    seen.add(further)
                    waiting.append(further)
        return opened


def _key(fixturedef: pytest.FixtureDef[object]) -> tuple[str, str]:
    """``(baseid, name)`` of a fixture: where it is defined, and its name."""
    return (fixturedef.baseid, fixturedef.argname)


def key(nodeid: str) -> str:
    """``"path::function"`` of a test: no parameters, no pytest-xdist group."""
    parts = nodeid.split("::")
    parts[-1] = re.split(r"[\[@]", parts[-1], maxsplit=1)[0]
    return "::".join(parts)


def judged(item: pytest.Item, opened: set[str]) -> str | None:
    """Why *item*, which opened *opened*, has to carry the mark; ``None`` if it need not."""
    if len(opened) < LIMIT or item.get_closest_marker(MARK) is not None:
        return None
    if key(item.nodeid) in RUNS_THE_LIBRARY:
        return None
    trees = Counter(path.split("/", 1)[0] for path in opened)
    where = ", ".join(f"{count} in {tree}/" for tree, count in sorted(trees.items()))
    return (
        f"the test opened {len(opened)} files of the repository ({where}) and carries "
        f"no {MARK} mark: a test that reads the repository whole carries it, so "
        f"that the jobs that pass {OPTION} leave it out (tests/whole_tree.py, rule "
        "T26 of docs/contributing/tests.md); one whose verdict the library decides "
        "stands in RUNS_THE_LIBRARY there, with its reason"
    )


_READS = TreeReads(ROOT)
_HOOKED: list[bool] = []


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        OPTION,
        action="store_true",
        default=False,
        dest="without_whole_tree",
        help=(
            "leave out the tests that read the repository whole, whose verdict "
            "the jitted kernel and the dependency floors do not change"
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    del config
    if not _HOOKED:
        sys.addaudithook(_READS.audit)
        _HOOKED.append(True)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Leave the marked tests out under :data:`OPTION`."""
    if not config.getoption("without_whole_tree"):
        return
    dropped = [item for item in items if item.get_closest_marker(MARK)]
    if dropped:
        config.hook.pytest_deselected(items=dropped)
        items[:] = [item for item in items if not item.get_closest_marker(MARK)]


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> Generator[None, None, None]:
    linecache.clearcache()
    opened = item.stash.setdefault(_OPENED, set())
    with _READS.counting(opened):
        return (yield)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None, None, None]:
    with _READS.counting(item.stash.setdefault(_OPENED, set())):
        return (yield)


@pytest.hookimpl(wrapper=True)
def pytest_fixture_setup(
    fixturedef: pytest.FixtureDef[object], request: pytest.FixtureRequest
) -> Generator[None, object, object]:
    key = _key(fixturedef)
    # The scope the value is cached at, which a parametrization with a scope
    # of its own sets: a setup for one test alone runs in that test's setup,
    # whose count takes what it opens, and what an earlier setup cached past
    # its test opened is no longer what a test is given.
    if request.scope == "function":
        _READS.forget(key)
        return (yield)
    # Each setup counts afresh: a fixture with parameters is set up once for
    # each, and the test given one setup reads that one alone.
    opened: set[str] = set()
    _READS.fixtures[key] = opened
    _READS.reached[key] = ()
    # The fixtures pytest resolved for the test, shared by every request of
    # it: those the fixture takes as parameters are there before its setup
    # runs, and those it asks for by name, its own name among them, appear
    # while it runs, before pytest puts the fixture itself there.
    resolved: dict[str, pytest.FixtureDef[object]] = request._fixture_defs
    before = set(resolved)
    try:
        with _READS.counting(opened):
            return (yield)
    finally:
        names = (
            *fixturedef.argnames,
            *(name for name in resolved if name not in before),
        )
        reached = (resolved.get(name) for name in names)
        _READS.reached[key] = tuple(
            dict.fromkeys(
                _key(found)
                for found in reached
                if found is not None and found is not fixturedef
            )
        )


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    report = yield
    if call.when == "call" and report.passed:
        problem = judged(item, _READS.read_by(item))
        if problem is not None:
            report.outcome = "failed"
            report.longrepr = problem
    return report
