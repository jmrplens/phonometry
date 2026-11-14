#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The tests that ask git about the repository, and the check that tells one.

Some tests ask git about the repository: which files it tracks, what their
attributes are, what the last commit holds. A tree unpacked from a source
archive (GitHub's "Source code", or a packager's export) has every file of
the repository but no ``.git``, and git refuses to answer there, so such a
test carries the mark, on itself or, for a module of them, as the module's
``pytestmark``::

    @pytest.mark.git_checkout

and is skipped, saying why, where the repository has no ``.git``. This
plugin, which ``conftest.py`` loads, adds that skip.

What makes a test one is that it runs git on the repository, so that is what
this plugin checks. While a test sets up and runs, it notes every git process
the test starts whose repository is this one, the processes the higher-scoped
fixtures it uses started when they were set up included, and an unmarked test
that started one fails, naming the command. Every job of CI runs from a
checkout, where such a test passes; without the check it would fail only in
a source archive. A git the test runs on a repository of its own, under
``tmp_path``, is no question about this one, and neither is a git that needs
no repository at all (``git init``, ``git --version``). A helper that asks git
and takes its refusal as an answer, so that the test runs the same in a tree
with no ``.git``, stands in :data:`TOLERATES_NO_CHECKOUT` with its reason.

The check reads the ``subprocess.Popen`` audit event (:func:`sys.addaudithook`),
which carries the program and its arguments. It cannot see a git that a
child process starts, such as a script run with ``sys.executable`` that runs
git in turn, a git run through a shell, or a test that takes what a helper's
own cache kept from an earlier test of its worker without running git again.
On Windows the event carries one command line instead of the arguments, and
the check leaves it unread: every test it would judge there runs on Linux and
macOS too, where the arguments are read.
"""

from __future__ import annotations

import contextlib
import os
import shlex
import subprocess  # nosec B404 - read for its file name, never run here
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator, Iterator, Mapping, Sequence
    from types import FrameType

#: The mark a test that asks git about the repository carries.
MARK = "git_checkout"

#: The repository.
ROOT = Path(__file__).resolve().parent.parent

#: Why a test that asks git about the repository is skipped outside a checkout.
NOT_A_CHECKOUT = "not a git checkout, so there is nothing to ask git about"

#: The helpers that ask git about the repository and take its refusal as an
#: answer, so that a test reaching them runs in a tree with no ``.git`` as it
#: does in a checkout, keyed ``"path::function"`` by the code that starts git,
#: with the reason.
TOLERATES_NO_CHECKOUT: dict[str, str] = {
    "scripts/generate_llms.py::_ignored_paths": (
        "lists the files git ignores under docs/ to leave them out, with "
        "check=False: a tree with no .git holds none, and the empty answer "
        "git's refusal gives is the right one"
    ),
    "scripts/generate_llms.py::_repository_files": (
        "lists the files git keeps, so that a link of the mirror names one of "
        "them, with check=False: a tree with no .git holds the repository's "
        "files and nothing git ignores, and the refusal sends the check to "
        "the files on disk"
    ),
}

#: The files whose frames start a process for someone else: the standard
#: library's, this suite's bounded runner and this plugin.
_STARTERS = frozenset(
    {
        os.path.realpath(subprocess.__file__),
        os.path.realpath(Path(__file__).with_name("child_process.py")),
        os.path.realpath(__file__),
    }
)

#: The options git reads before its command that take the next argument as
#: their value, so that the value is not read as the command.
_VALUED_OPTIONS = frozenset(
    {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}
)

#: The git commands that ask no repository anything: they start one or say
#: what git is.
_NO_REPOSITORY = frozenset({"init", "version", "help"})

#: The git commands, recorded by test or fixture, that ran on :data:`ROOT`.
_RUNS = pytest.StashKey[list[str]]()


def is_a_checkout(root: Path) -> bool:
    """Whether *root* is a git checkout: ``.git`` is a directory in a clone, a file in a linked worktree."""
    return (root / ".git").exists()


def _repository_of(directory: Path) -> Path | None:
    """The top of the git repository *directory* lies in, or ``None`` outside any."""
    for candidate in (directory, *directory.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def asked_about(
    argv: Sequence[str], cwd: str | None, env: Mapping[str, str] | None
) -> list[Path]:
    """The repositories the git command *argv*, started in *cwd*, asks about.

    The directory git starts from is *cwd* (the process's own when ``None``)
    moved by every ``-C``; ``--git-dir`` or ``GIT_DIR`` names the repository
    outright. A command that asks no repository anything gives none, and
    ``git clone`` asks about the local repository it copies, if it copies one.
    """
    where = Path(cwd) if cwd is not None else Path.cwd()
    environment = os.environ if env is None else env
    git_dir = environment.get("GIT_DIR")
    index = 1
    while index < len(argv):
        word = argv[index]
        if word.startswith("--git-dir="):
            git_dir = word.partition("=")[2]
        elif word in _VALUED_OPTIONS and index + 1 < len(argv):
            if word == "-C":
                where = where / argv[index + 1]
            elif word == "--git-dir":
                git_dir = argv[index + 1]
            index += 1
        elif not word.startswith("-"):
            break
        index += 1
    else:
        return []
    command = argv[index]
    if command in _NO_REPOSITORY:
        return []
    if git_dir is not None:
        named = (where / git_dir).resolve()
        return [named.parent if named.name == ".git" else named]
    if command == "clone":
        operands = [
            where / word for word in argv[index + 1 :] if not word.startswith("-")
        ]
        found = [_repository_of(path.resolve()) for path in operands if path.exists()]
        return [repository for repository in found if repository is not None]
    repository = _repository_of(where.resolve())
    return [] if repository is None else [repository]


def started_by(frame: FrameType | None) -> str | None:
    """``"path::function"`` of the code of the repository that started a process.

    The first frame outside :data:`_STARTERS`, read from the audit hook's
    caller; ``None`` when no frame of the repository is on the stack.
    """
    while frame is not None:
        name = os.path.realpath(frame.f_code.co_filename)
        if name not in _STARTERS:
            path = Path(name)
            if path.is_relative_to(ROOT):
                return (
                    f"{path.relative_to(ROOT).as_posix()}::{frame.f_code.co_qualname}"
                )
            return None
        frame = frame.f_back
    return None


def _arguments(args: object) -> list[str] | None:
    """The program and arguments a ``subprocess.Popen`` event carries, or ``None``."""
    if isinstance(args, str | bytes) or not isinstance(args, list | tuple):
        return None
    words = []
    for arg in args:
        if not isinstance(arg, str | bytes | os.PathLike):
            return None
        words.append(os.fsdecode(arg))
    return words


class GitRuns:
    """The git commands on *root* each test and each higher-scoped fixture starts.

    :meth:`audit` is an audit hook: the ``subprocess.Popen`` event comes with
    the program, its arguments, its working directory and its environment. A
    command counts while :meth:`recording` holds a list for it.
    """

    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._lists: list[list[str]] = []
        #: What each higher-scoped fixture ran, by ``(baseid, name)``.
        self.fixtures: dict[tuple[str, str], list[str]] = {}

    @contextlib.contextmanager
    def recording(self, runs: list[str]) -> Iterator[None]:
        """Add the git commands on the repository started inside the block to *runs*."""
        self._lists.append(runs)
        try:
            yield
        finally:
            self._lists.pop()

    def audit(self, event: str, args: tuple[object, ...]) -> None:
        """Note a git command whose repository is this one."""
        if event != "subprocess.Popen" or not self._lists:
            return
        words = _arguments(args[1])
        if not words or Path(words[0]).name not in ("git", "git.exe"):
            return
        cwd, env = args[2], args[3]
        directory = (
            os.fsdecode(cwd) if isinstance(cwd, str | bytes | os.PathLike) else None
        )
        # An audit hook that raises stops the process it watches from starting,
        # so a command this cannot read is left unjudged.
        try:
            repositories = asked_about(
                words, directory, env if isinstance(env, dict) else None
            )
        except (OSError, TypeError, ValueError):
            return
        if self._root not in repositories:
            return
        if started_by(sys._getframe(1)) in TOLERATES_NO_CHECKOUT:
            return
        self._lists[-1].append(shlex.join(["git", *words[1:]]))

    def run_by(self, item: pytest.Item) -> list[str]:
        """The commands *item* started, and those its higher-scoped fixtures started."""
        own: list[str] = item.stash.get(_RUNS, [])
        runs = [*own]
        for name in getattr(item, "fixturenames", ()):
            mine = [
                baseid
                for baseid, argname in self.fixtures
                if argname == name and _reaches(item.nodeid, baseid)
            ]
            if mine:
                runs += self.fixtures[(max(mine, key=len), name)]
        return runs


def _reaches(nodeid: str, baseid: str) -> bool:
    """Whether a fixture defined at *baseid* reaches the test *nodeid*.

    The reading ``whole_tree.py`` makes, kept here because that module is a
    plugin of its own: imported from here first, pytest could not rewrite
    its asserts.
    """
    return (
        not baseid
        or nodeid == baseid
        or nodeid.startswith((f"{baseid}/", f"{baseid}::"))
    )


def judged(item: pytest.Item, runs: list[str]) -> str | None:
    """Why *item*, which started *runs*, has to carry the mark; ``None`` if it need not."""
    if not runs or item.get_closest_marker(MARK) is not None:
        return None
    first = runs[0].replace(str(ROOT), "<repository>")
    more = f" and {len(runs) - 1} more" if len(runs) > 1 else ""
    return (
        f"the test ran git on the repository ({first}{more}) and carries no "
        f"{MARK} mark: a test that asks git about the repository carries it, so "
        "that a tree with no .git, as a source archive unpacks, skips it rather "
        "than failing (tests/git_checkout.py, rule T27 of docs/contributing/tests.md)"
    )


_GIT = GitRuns(ROOT)
_HOOKED: list[bool] = []


def pytest_configure(config: pytest.Config) -> None:
    del config
    if not _HOOKED:
        sys.addaudithook(_GIT.audit)
        _HOOKED.append(True)


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Skip the marked tests where the repository is not a git checkout."""
    del config
    if is_a_checkout(ROOT):
        return
    skip = pytest.mark.skip(reason=NOT_A_CHECKOUT)
    for item in items:
        if item.get_closest_marker(MARK) is not None:
            item.add_marker(skip)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_setup(item: pytest.Item) -> Generator[None, None, None]:
    with _GIT.recording(item.stash.setdefault(_RUNS, [])):
        return (yield)


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_call(item: pytest.Item) -> Generator[None, None, None]:
    with _GIT.recording(item.stash.setdefault(_RUNS, [])):
        return (yield)


@pytest.hookimpl(wrapper=True)
def pytest_fixture_setup(
    fixturedef: pytest.FixtureDef[object], request: pytest.FixtureRequest
) -> Generator[None, object, object]:
    del request
    if fixturedef.scope == "function":
        return (yield)
    runs = _GIT.fixtures.setdefault((fixturedef.baseid, fixturedef.argname), [])
    with _GIT.recording(runs):
        return (yield)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Generator[None, pytest.TestReport, pytest.TestReport]:
    report = yield
    if call.when == "call" and report.passed:
        problem = judged(item, _GIT.run_by(item))
        if problem is not None:
            report.outcome = "failed"
            report.longrepr = problem
    return report
