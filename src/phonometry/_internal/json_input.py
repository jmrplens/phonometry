#  Copyright (c) 2026. Jose Manuel Requena Plens
"""JSON a caller hands in, held to what a reader can take before it is decoded.

A file or a text a caller gives one of the library's readers (a catalogue
file, a calibration sidecar) is held to what no decoder checks: a file is a
regular file, never a pipe, a device, a socket or a directory, which could
keep the reader waiting at the open or reading without end; it holds at most
so many bytes, whatever the file system says it holds; the brackets of its
text nest at most so deep, counted before any decoder runs; and a text it
decodes to holds no lone surrogate, which a JSON escape can spell and UTF-8
cannot write. Each reader turns what these find into its own error, with the
place in the file.

A file the library writes back at such a name is written beside it and
renamed into place, so that the name is never opened for writing: opening a
pipe for writing waits for a reader, which may never come, and a reader of
the name finds the old file or the new one whole, never half of either.
"""

from __future__ import annotations

import os
import re
import secrets
import stat
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

#: How deep the brackets of a text may nest for the text to be decoded at all.
#: A small part of how deep a decoder follows before it gives out, which
#: depends on the interpreter: some 500 levels for CPython's pure-Python
#: scanner at the default recursion limit, 10 000 for the C scanner of CPython
#: 3.13 on Linux, and from 3.14 as deep as the stack of the thread allows.
#: Counting the brackets makes the refusal the same everywhere. And far above
#: how deep a document of the library nests (a catalogue file six levels, a
#: calibration sidecar two), so that a document nested a few levels too deep,
#: by hand or by a program's mistake, is still decoded and told where.
MAX_NESTING = 64

#: What the nesting of a JSON text is read from: a string, taken whole with its
#: escapes and every bracket it quotes (one left open runs to the end of the
#: text, as the decoder reads it), or a run of brackets that open, or of
#: brackets that close. Every branch starts with its own character, so the
#: scan passes over numbers, names and blanks without stopping.
_BRACKETS = re.compile(
    r'"[^"\\]*(?:\\.[^"\\]*)*"?|\[[\[{]*|\{[\[{]*|\][\]}]*|\}[\]}]*', re.DOTALL
)

#: Half of a pair of UTF-16 code units, alone. A JSON escape such as
#: ``\ud800`` decodes to one, and a text that holds it has no UTF-8 bytes, so
#: whatever keeps it can never be written out again.
LONE_SURROGATE = re.compile(r"[\ud800-\udfff]")

#: The flag that keeps an open from waiting: opening a pipe for reading waits
#: until a writer comes, which may be never. Windows has no such flag.
_NO_WAIT = getattr(os, "O_NONBLOCK", 0)
#: What the open adds to the flags Python opens a file with: not to wait, and
#: not to take a terminal for the reader's own. A regular file is read the same.
_OPEN_FLAGS = _NO_WAIT | getattr(os, "O_NOCTTY", 0)


class NotRegularError(Exception):
    """A name that holds something other than a regular file, and what it is."""

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        #: What the name holds, as a message says it: "a named pipe (FIFO)",
        #: "a character device", "a directory".
        self.kind = kind


class TooLargeError(Exception):
    """A file past the bytes a reader takes, and its size when that is known."""

    def __init__(self, size: int | None) -> None:
        super().__init__(size)
        #: The size the file system gives for the file, or ``None`` for a
        #: file that held more than its size said (one that grew while it
        #: was read, or one of the files of ``/proc``, whose size is zero),
        #: which was read one byte past the limit.
        self.size = size


def _not_regular(mode: int) -> str | None:
    """What a file of *mode* is when it is not a regular file, or ``None``."""
    if stat.S_ISREG(mode):
        return None
    for test, kind in (
        (stat.S_ISFIFO, "a named pipe (FIFO)"),
        (stat.S_ISCHR, "a character device"),
        (stat.S_ISBLK, "a block device"),
        (stat.S_ISSOCK, "a socket"),
        (stat.S_ISDIR, "a directory"),
    ):
        if test(mode):
            return kind
    return "a special file"


def not_regular_at(path: Path) -> str | None:
    """What is at *path* when it is not a regular file, or ``None``.

    A link is followed, so a link to a pipe is a pipe. ``None`` when a
    regular file is at the name, and when nothing is, or the link at it names
    nothing: a file written there makes one.

    :raises OSError: as the file system raises it, untouched, for anything
        but a name with nothing at it.
    """
    try:
        mode = path.stat().st_mode
    except FileNotFoundError:
        return None
    return _not_regular(mode)


def write_beside(target: Path, data: bytes) -> None:
    """Put *data* at *target* through a new file beside it, renamed into place.

    *target* itself is never opened. What is at the name is replaced by the
    rename, so a caller refuses first what it will not replace
    (:func:`not_regular_at` says what a name holds). The new file is flushed
    to the disk before the rename, and removed when anything fails before it.

    :param target: Where the file goes.
    :param data: Its bytes.
    :raises OSError: as the file system raises it, untouched.
    """
    temporary = target.with_name(f".{target.name}.{secrets.token_hex(8)}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(target)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _open_without_waiting(name: str, flags: int) -> int:
    """Open *name* as :func:`open` asks, never waiting for a writer to come."""
    return os.open(name, flags | _OPEN_FLAGS)


def read_at_most(path: Path, limit: int) -> bytes:
    """The bytes of the regular file *path*, never more than one past *limit*.

    Anything else at the name, a pipe, a device, a socket or a directory
    (behind a link or not), is refused before it is opened, since opening a
    pipe waits for a writer and reading a device may never end. The file is
    then opened without waiting and asked again what it is, so that a pipe
    put in its place in between is refused, not waited on. A regular file
    whose size, read from the open file, is past the limit is refused before
    a byte of it is read; any other is read to one byte past the limit at
    most, so one that grows while it is read, or whose size says nothing true
    about it, is refused as soon as that byte arrives.

    :param path: The file.
    :param limit: The most bytes the reader takes.
    :return: Every byte of the file, at most *limit* of them.
    :raises NotRegularError: for a name that holds anything but a regular file.
    :raises TooLargeError: for a file that holds more than *limit* bytes.
    :raises OSError: as the file system raises it, untouched.
    """
    kind = _not_regular(path.stat().st_mode)
    if kind is not None:
        raise NotRegularError(kind)
    with open(path, "rb", opener=_open_without_waiting) as handle:
        status = os.fstat(handle.fileno())
        kind = _not_regular(status.st_mode)
        if kind is not None:
            raise NotRegularError(kind)
        if _NO_WAIT:
            # A regular file, read as any other is read from here on.
            os.set_blocking(handle.fileno(), True)
        if status.st_size > limit:
            raise TooLargeError(status.st_size)
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise TooLargeError(None)
    return raw


def nesting_past(text: str, limit: int = MAX_NESTING) -> int | None:
    """Where the brackets of *text* first nest past *limit*, or ``None``.

    The brackets are counted outside the strings of the text, before it is
    decoded, so the answer never waits on a decoder running out of stack,
    which from Python 3.14 depends on how large the stack of the thread is.
    The count ends where the depth falls back to zero, at the bracket that
    closes the value the text opens with (or closes one that was never
    opened), since a decoder reads nothing past it: sixteen mebibytes of
    ``[]`` are answered at the second character.

    :param text: The text, before it is decoded.
    :param limit: How deep its brackets may nest.
    :return: The offset in *text* of the bracket that opens the level past
        *limit*, or ``None`` when no bracket does.
    """
    depth = 0
    for token in _BRACKETS.finditer(text):
        start, end = token.span()
        first = text[start]
        if first in "[{":
            if depth + end - start > limit:
                return start + limit - depth
            depth += end - start
        elif first != '"':
            depth -= end - start
            if depth <= 0:
                return None
    return None


def text_location(text: str, offset: int) -> str:
    """The line and column of *offset* in *text*, counted as JSON errors count."""
    line = text.count("\n", 0, offset) + 1
    column = offset - text.rfind("\n", 0, offset)
    return f"line {line}, column {column}"
