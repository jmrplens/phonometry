#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What a reader of JSON files finds at a name when it is not a regular file.

A named pipe with no writer keeps an open waiting, a device such as
``/dev/zero`` keeps a read going, and a directory holds no bytes at all. The
readers of catalogue files and calibration sidecars refuse each before they
wait on it; these helpers put one at a name, run the reader with a few seconds
to answer, so that a regression fails its test instead of hanging the suite,
and make the size of every file the readers open say nothing, as the size of
a file of ``/proc`` does.
"""

from __future__ import annotations

import contextlib
import os
import sys
import threading
from typing import TYPE_CHECKING

import pytest

from phonometry._internal import json_input

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from typing import IO

_POSIX = pytest.mark.skipif(sys.platform == "win32", reason="POSIX pipes and devices")

#: What a test puts at the name: a pipe no one writes to, a link to
#: ``/dev/zero``, and a directory, the one of the three Windows has.
SPECIAL_KINDS = (
    pytest.param("pipe", marks=_POSIX),
    pytest.param("device", marks=_POSIX),
    "directory",
)


def make_special(kind: str, path: Path) -> str:
    """Put a file of *kind* at *path*, and say what it is as a refusal says it."""
    if kind == "pipe":
        os.mkfifo(path)
        return "a named pipe (FIFO)"
    if kind == "device":
        path.symlink_to("/dev/zero")
        return "a character device"
    path.mkdir()
    return "a directory"


def raised_within(
    call: Callable[[], object], *, seconds: float = 5.0, pipe: Path | None = None
) -> BaseException | None:
    """What *call* raises, or ``None``, failing the test past *seconds*.

    The call runs in a thread of its own. When it is still running at the end
    of *seconds* the test fails; a named pipe at *pipe* is first opened for
    writing and for reading, which lets an open that waits on it for either
    return, and closed again, so that the thread ends rather than waits for
    the rest of the session.
    """
    outcome: list[BaseException | None] = []

    def run() -> None:
        try:
            call()
        except BaseException as error:
            outcome.append(error)
        else:
            outcome.append(None)

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        if pipe is not None:
            ends: list[int] = []
            for flags in (os.O_WRONLY, os.O_RDONLY):
                with contextlib.suppress(OSError):
                    ends.append(os.open(pipe, flags | os.O_NONBLOCK))
            thread.join(seconds)
            for end in ends:
                os.close(end)
        pytest.fail(f"the call was still waiting after {seconds} s")
    return outcome[0]


class _SizeSaysNothing:
    """The ``os`` module as the bounded read sees it: every open file is empty."""

    def fstat(self, fd: int) -> os.stat_result:
        status = os.fstat(fd)
        return os.stat_result((*status[:6], 0, *status[7:10]))

    def __getattr__(self, name: str) -> object:
        return getattr(os, name)


def size_says_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make every file the bounded read opens say it holds no byte."""
    monkeypatch.setattr(json_input, "os", _SizeSaysNothing())


class _Unread:
    """An open file whose size may be asked and whose bytes may not be read."""

    def __init__(self, handle: IO[bytes]) -> None:
        self.handle = handle

    def __enter__(self) -> _Unread:
        return self

    def __exit__(self, *_: object) -> None:
        self.handle.close()

    def fileno(self) -> int:
        return self.handle.fileno()

    def read(self, *_: object) -> bytes:
        raise AssertionError(self.handle.name)


def reads_refused(monkeypatch: pytest.MonkeyPatch, *refused: Path) -> list[Path]:
    """Let the bounded read open the files *refused* and never read a byte of them.

    Every other file is read as it is. The list returned fills with each file
    the bounded read opens, in order, so that a test can say which it opened.
    """
    opened: list[Path] = []

    def unread(file: Path, mode: str, **_: object) -> object:
        opened.append(file)
        handle = file.open(mode)
        return _Unread(handle) if file in refused else handle

    monkeypatch.setattr(json_input, "open", unread, raising=False)
    return opened
