#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A process a test starts, stopped at its time limit on every platform.

``subprocess.run(timeout=...)`` kills the child it started once the time is
up, and then, on Windows only, reads the child's pipes to their end with no
limit of its own. A program that hands its pipes on to a process it starts
keeps them open past that kill, and the read never ends. Git for Windows is
such a program: the ``git.exe`` on the path is a launcher that starts the
``git.exe`` doing the work and gives it the pipes. :func:`run` kills the
child and waits for it alone; on Windows the pipes are left to the
threads reading them, which end with the last process that holds them,
and elsewhere they are closed.

:func:`join` waits for a :mod:`multiprocessing` child the same way: a
forked child that never ends, which a fork of a process with threads can
leave, is killed and fails the test instead of holding the worker.
"""

from __future__ import annotations

import contextlib
import subprocess  # nosec B404 - the tests' own programs, never a shell
import sys
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from collections.abc import Sequence
    from multiprocessing.process import BaseProcess

#: How long a killed child may take to end [s]: a kill ends it at once.
_KILLED_S = 30.0


def run(
    args: Sequence[str],
    *,
    timeout: float,
    check: bool = False,
    capture_output: bool = False,
    **options: Any,
) -> subprocess.CompletedProcess[Any]:
    """Run *args* as :func:`subprocess.run` does, ending it after *timeout* seconds.

    *options* are those of :class:`subprocess.Popen` (``text``, ``cwd``,
    ``env``).

    :raises TypeError: for a *timeout* of ``None``, which sets no limit.
    :raises subprocess.TimeoutExpired: once the program has run *timeout*
        seconds; it has been killed, and the processes it started may still
        hold its output.
    :raises subprocess.CalledProcessError: with *check*, for a status other
        than 0.
    """
    if timeout is None:
        msg = "child_process.run takes a limit in seconds, not None"
        raise TypeError(msg)
    if capture_output:
        options["stdout"] = options["stderr"] = subprocess.PIPE
    process = subprocess.Popen(args, **options)  # nosec B603 - a test's own argument list
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except BaseException:
        process.kill()
        process.wait(_KILLED_S)
        _close_pipes(process)
        raise
    done = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
    if check:
        done.check_returncode()
    return done


def _close_pipes(process: subprocess.Popen[Any]) -> None:
    """Close the pipes of a killed *process*, where no thread still reads them.

    On POSIX ``communicate`` reads them in the calling thread, which has
    given up on them. On Windows a thread of ``communicate`` reads each one
    until the last process holding it ends, holding the file's lock while
    it reads, and closes it then: closing it here would wait as long.
    """
    if sys.platform == "win32":
        return
    for pipe in (process.stdin, process.stdout, process.stderr):
        if pipe is not None:
            with contextlib.suppress(OSError):
                pipe.close()


def join(child: BaseProcess, *, timeout: float) -> None:
    """Wait for *child* to end; kill it and fail the test once it has run *timeout* seconds."""
    child.join(timeout)
    if child.is_alive():
        child.kill()
        child.join(_KILLED_S)
        pytest.fail(f"the child process ran past {timeout:g} s and was killed")
