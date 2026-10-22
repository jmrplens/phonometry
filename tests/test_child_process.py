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
#: child and write down the child's process id.
_LAUNCHER_LIMIT_S = 5.0


def test_a_program_that_outlives_its_limit_is_killed() -> None:
    started = time.monotonic()
    with pytest.raises(subprocess.TimeoutExpired):
        child_process.run(
            [sys.executable, "-c", f"import time; time.sleep({_RUNS_ON_S})"],
            capture_output=True,
            timeout=_LIMIT_S,
        )
    assert time.monotonic() - started < _PROMPT_S


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


def _unbounded(call: ast.Call) -> str | None:
    """What *call* waits on with no bound, or ``None`` for a call that is bounded or waits on nothing."""
    func = call.func
    if not isinstance(func, ast.Attribute):
        return None
    keywords = {keyword.arg for keyword in call.keywords}
    if "timeout" in keywords:
        return None
    if func.attr in _RUNNERS:
        bare = isinstance(func.value, ast.Name) and func.value.id == "subprocess"
        return f"subprocess.{func.attr} without a timeout" if bare else None
    if func.attr == "communicate" and len(call.args) < 2:
        return f"{ast.unparse(func.value)}.communicate without a timeout"
    if func.attr in _WAITS and not call.args and not keywords:
        return f"{ast.unparse(func.value)}.{func.attr}() without a timeout"
    return None


def _waits(path: Path) -> list[tuple[str, str]]:
    """Each wait in *path* with no bound, as ``("path::function", what)``."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    where = path.relative_to(_ROOT).as_posix()
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
            if isinstance(child, ast.Call) and (what := _unbounded(child)):
                found.append((key, f"line {child.lineno}: {what}"))
            visit(child, inner)

    visit(tree, "")
    return found


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
