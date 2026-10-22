#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A test that waits on another process or thread waits a bounded time.

A wait without a bound hangs the run when what it waits on never answers:
pytest-xdist reports nothing more from the worker it holds, and the CI job
runs to the runner's limit with no name on it. :mod:`child_process` stops
what a test starts at its limit on every platform, and the scan below finds
any wait in the suite that has none.
"""

from __future__ import annotations

import ast
import contextlib
import multiprocessing
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import child_process
import pytest

_TESTS = Path(__file__).resolve().parent
_ROOT = _TESTS.parent

#: How long a test here lets a program run before stopping it [s].
_LIMIT_S = 1.0
#: How long a program here would run if nothing stopped it [s]: long past
#: :data:`_LIMIT_S` and past anything a stopped program may still take.
_RUNS_ON_S = 60.0
#: How long a stopped program may take to come back [s]: well short of
#: :data:`_RUNS_ON_S`, so that a run that waited for the program comes back
#: too late.
_PROMPT_S = 30.0
#: How long a launcher here runs before it is stopped [s]: time to start its
#: child and write down the child's process id, on a loaded runner too.
_LAUNCHER_LIMIT_S = 10.0


class _Started:
    """``subprocess`` as child_process.py sees it, keeping every process it starts."""

    def __init__(self) -> None:
        self.processes: list[subprocess.Popen[bytes]] = []

    # Whatever subprocess holds, of whatever type it has.
    def __getattr__(self, name: str) -> Any:  # noqa: ANN401
        return getattr(subprocess, name)

    # subprocess's own name, which child_process.py calls.
    def Popen(  # noqa: N802
        self, args: list[str], **options: Any
    ) -> subprocess.Popen[bytes]:
        process = subprocess.Popen(args, **options)
        self.processes.append(process)
        return process


def test_a_program_that_outlives_its_limit_is_killed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = _Started()
    monkeypatch.setattr(child_process, "subprocess", started)
    begun = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        child_process.run(
            [sys.executable, "-c", f"import time; time.sleep({_RUNS_ON_S})"],
            capture_output=True,
            timeout=_LIMIT_S,
        )
    assert time.monotonic() - begun < _PROMPT_S
    (process,) = started.processes
    assert process.returncode is not None, "the program was not waited for"
    if sys.platform != "win32":
        # On Windows the threads that read them close them.
        assert process.stdout is not None
        assert process.stderr is not None
        assert process.stdout.closed, "the killed program's output was left open"
        assert process.stderr.closed, "the killed program's output was left open"


def test_a_program_whose_child_keeps_its_pipes_is_still_stopped_on_time(
    tmp_path: Path,
) -> None:
    """The program a launcher such as Git for Windows' ``git.exe`` starts outlives the kill.

    It still holds the pipes, so a run that read them to their end after
    the kill, as ``subprocess.run`` does on Windows, would wait as long as
    that child lives.
    """
    pid_file = tmp_path / "grandchild.pid"
    launcher = (
        "import subprocess, sys, time\n"
        "child = subprocess.Popen(\n"
        f"    [sys.executable, '-c', 'import time; time.sleep({_RUNS_ON_S})'],\n"
        "    stdout=sys.stdout, stderr=sys.stderr,\n"
        ")\n"
        f"open({str(pid_file)!r}, 'w').write(str(child.pid))\n"
        f"time.sleep({_RUNS_ON_S})\n"
    )
    started = time.monotonic()
    try:
        with pytest.raises(subprocess.TimeoutExpired):
            child_process.run(
                [sys.executable, "-c", launcher],
                capture_output=True,
                timeout=_LAUNCHER_LIMIT_S,
            )
        elapsed = time.monotonic() - started
        # Without a child of the launcher, nothing held the pipes past the
        # kill, and the time says nothing.
        assert pid_file.exists(), "the launcher had not started its child when stopped"
        assert elapsed < _PROMPT_S, f"the run came back {elapsed:.0f} s after it began"
    finally:
        if pid_file.exists():
            with contextlib.suppress(OSError):
                os.kill(int(pid_file.read_text(encoding="utf-8")), signal.SIGTERM)


def test_a_finished_program_comes_back_as_subprocess_run_returns_it() -> None:
    done = child_process.run(
        [sys.executable, "-c", "import sys; print('out'); sys.exit(3)"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert (done.returncode, done.stdout.strip(), done.stderr) == (3, "out", "")


def test_a_failed_program_raises_when_checked() -> None:
    with pytest.raises(subprocess.CalledProcessError, match="exit status 3"):
        child_process.run(
            [sys.executable, "-c", "import sys; sys.exit(3)"], check=True, timeout=120
        )


def test_a_child_process_that_outlives_its_limit_is_killed_and_fails_the_test() -> None:
    child = multiprocessing.get_context("spawn").Process(
        target=time.sleep, args=(_RUNS_ON_S,)
    )
    child.start()
    started = time.monotonic()
    with pytest.raises(pytest.fail.Exception, match="ran past"):
        child_process.join(child, timeout=_LIMIT_S)
    assert not child.is_alive()
    assert time.monotonic() - started < _PROMPT_S


# --------------------------------------------------------------------------
# Every wait in the suite has a bound.

#: The ``subprocess`` functions that wait for the program they start.
_RUNNERS = frozenset({"run", "call", "check_call", "check_output"})
#: Methods that wait on another process or thread, and wait for good when
#: called with no argument: a thread's or process's ``join``, a process's or
#: an event's ``wait``, a future's ``result``, a lock's ``acquire``.
_WAITS = frozenset({"join", "wait", "result", "acquire"})
#: Waits with no bound, keyed by ``"path::function"``, each with its reason.
_UNBOUNDED = {
    "tests/simulation/fake_ssh.py::main": (
        "the stand-in for ssh runs as its own process and waits for the "
        "command it ran as ssh does; the client under test bounds the wait "
        "and kills the stand-in"
    ),
}


def _forever(limit: ast.expr | None) -> bool:
    """Whether *limit*, the time limit a call is given, sets none: absent, ``None`` or ``-1``."""
    if limit is None:
        return True
    if isinstance(limit, ast.UnaryOp) and isinstance(limit.op, ast.USub):
        return isinstance(limit.operand, ast.Constant) and limit.operand.value == 1
    return isinstance(limit, ast.Constant) and limit.value is None


def _argument(call: ast.Call, name: str, position: int | None) -> ast.expr | None:
    """The argument *call* passes as *name*, by keyword or at *position*; ``None`` when absent.

    A *position* of ``None`` is a keyword-only parameter. What ``**options``
    holds is not in the text, so it passes nothing.
    """
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    if position is None or len(call.args) <= position:
        return None
    return call.args[position]


def _unbounded(call: ast.Call, modules: frozenset[str]) -> str | None:
    """What *call* waits on with no bound, or ``None`` for a call that is bounded or waits on nothing.

    *modules* are the names ``subprocess`` goes by in the file. A ``join``,
    ``wait`` or ``result`` called with arguments other than a limit belongs
    to some other API (``str.join``, a builder's ``result``) and passes; one
    given ``None`` or ``-1`` for its limit waits for good, as one given
    nothing does.
    """
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    what = f"{ast.unparse(func.value)}.{func.attr} without a timeout"
    if func.attr in _RUNNERS:
        bare = isinstance(func.value, ast.Name) and func.value.id in modules
        return what if bare and _forever(_argument(call, "timeout", None)) else None
    if func.attr == "communicate":
        return what if _forever(_argument(call, "timeout", 1)) else None
    if func.attr == "acquire":
        blocking = _argument(call, "blocking", 0)
        blocks = blocking is None or (
            isinstance(blocking, ast.Constant) and blocking.value is True
        )
        return what if blocks and _forever(_argument(call, "timeout", 1)) else None
    if func.attr in _WAITS:
        limit = _argument(call, "timeout", 0)
        bare = not call.args and not call.keywords
        return what if bare or (limit is not None and _forever(limit)) else None
    return None


def _waits(path: Path) -> list[tuple[str, str]]:
    """Each wait in *path* with no bound, as ``("path::function", what)``."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    where = path.relative_to(_ROOT).as_posix()
    modules = frozenset(
        alias.asname or alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "subprocess"
    )
    found: list[tuple[str, str]] = []

    def visit(node: ast.AST, scope: str) -> None:
        key = f"{where}::{scope or '<module>'}"
        for child in ast.iter_child_nodes(node):
            inner = scope
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                inner = f"{scope}.{child.name}" if scope else child.name
            if isinstance(child, ast.ImportFrom) and child.module == "subprocess":
                names = {alias.name for alias in child.names} & _RUNNERS
                found.extend(
                    (key, f"subprocess.{name} imported bare") for name in names
                )
            if isinstance(child, ast.Call) and (what := _unbounded(child, modules)):
                found.append((key, f"line {child.lineno}: {what}"))
            visit(child, inner)

    visit(tree, "")
    return found


@pytest.mark.parametrize(
    "source",
    [
        "subprocess.run(['git'])",
        "subprocess.run(['git'], timeout=None)",
        "sp.check_output(['git'])",
        "process.communicate(b'')",
        "process.communicate(timeout=None)",
        "thread.join()",
        "thread.join(None)",
        "thread.join(timeout=None)",
        "event.wait(timeout=None)",
        "future.result()",
        "lock.acquire()",
        "lock.acquire(True)",
        "lock.acquire(timeout=-1)",
        "subprocess.run(['git'], **options)",
    ],
)
def test_a_wait_with_no_bound_is_found(source: str) -> None:
    (call,) = (
        node for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Call)
    )
    assert _unbounded(call, frozenset({"subprocess", "sp"}))


@pytest.mark.parametrize(
    "source",
    [
        "subprocess.run(['git'], timeout=120)",
        "child_process.run(['git'], timeout=120)",
        "process.communicate(b'', 30)",
        "thread.join(30)",
        "thread.join(timeout=30)",
        "event.wait(_THREAD_S)",
        "future.result(timeout=30)",
        "lock.acquire(False)",
        "lock.acquire(blocking=False)",
        "lock.acquire(True, 30)",
        "text.join(parts)",
    ],
)
def test_a_wait_with_a_bound_or_no_wait_at_all_passes(source: str) -> None:
    (call,) = (
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    )
    assert _unbounded(call, frozenset({"subprocess"})) is None


def test_every_wait_in_the_suite_has_a_bound() -> None:
    """A wait on another process or thread names how long it waits.

    ``subprocess.run`` and its kin take ``timeout``; ``communicate``,
    ``join``, ``wait``, ``result`` and ``acquire`` take a timeout too. Which
    program may hand its pipes to a process of its own, and so has to run
    through :func:`child_process.run`, the scan cannot tell: review does.
    """
    found = [wait for path in sorted(_TESTS.rglob("*.py")) for wait in _waits(path)]
    unexplained = [f"{key}: {what}" for key, what in found if key not in _UNBOUNDED]
    assert not unexplained, "waits with no bound:\n" + "\n".join(unexplained)
    stale = sorted(set(_UNBOUNDED) - {key for key, _ in found})
    assert not stale, f"exemptions that no longer match a wait: {stale}"
