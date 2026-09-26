#  Copyright (c) 2026. Jose Manuel Requena Plens
"""JSON a caller hands in, held to what a reader can take before it is decoded.

A file or a text a caller gives one of the library's readers (a catalogue
file, a calibration sidecar) is held to two bounds no decoder gives: at most
so many bytes, whatever the file system says the file holds, and brackets
nested at most so deep, counted in the text before any decoder runs. Each
reader turns what these find into its own error, with the place in the file.
"""

from __future__ import annotations

import os
import re
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


class TooLargeError(Exception):
    """A file past the bytes a reader takes, and its size when that is known."""

    def __init__(self, size: int | None) -> None:
        super().__init__(size)
        #: The size the file system gives for the file, or ``None`` for a
        #: file that gives none that is true (a pipe, a device, a link to
        #: either), which was read one byte past the limit.
        self.size = size


def read_at_most(path: Path, limit: int) -> bytes:
    """The bytes of *path*, never reading more than one byte past *limit*.

    The file is opened once. A file whose size, read from the open file,
    is past the limit is refused before a byte of it is read; any other is
    read to one byte past the limit at most, so a file whose size says
    nothing true about it, a pipe, a device or a link to either, is refused
    as soon as that byte arrives rather than read without end.

    :param path: The file.
    :param limit: The most bytes the reader takes.
    :return: Every byte of the file, at most *limit* of them.
    :raises TooLargeError: for a file that holds more than *limit* bytes.
    :raises OSError: as the file system raises it, untouched.
    """
    with path.open("rb") as handle:
        size = os.fstat(handle.fileno()).st_size
        if size > limit:
            raise TooLargeError(size)
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
