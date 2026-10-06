#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where the fences of a markdown page open and close, as CommonMark reads them.

Every script that reads a page reads its fences here: the checks of its prose
step over the code first, and the checks of its examples take the code out.
A fence opens on a run of at least three backticks or three tildes, and only
a line of the same character, at least as long as that run, with nothing
after it but blanks, closes it (CommonMark 0.31.2, 4.5). An info string after
a run of backticks may not hold a backtick itself: such a line is an inline
code span, not a fence. A reader that closes a fence on any run of three
markers loses track at the first block that shows a fence inside another, and
from there it reads the page inside out: code as prose and prose as code. One
that knows only backticks never sees a tilde fence at all.
``site/src/lib/markdown-fences.mjs`` is the same reading in JavaScript, for
the site's own code, and ``tests/test_markdown_fences.py`` holds the two to
the same answer on every page. ``scripts/check_fence_readers.py`` fails on a
script, or on a piece of the site's code, that reads fences any other way.

CommonMark lets the marker be indented by three spaces at most. These pages
nest fences inside list items, indented with the item, so any indentation is
read as a fence here. The body of an indented fence loses as much indentation
as its opening marker carried, as CommonMark has it, so the code it holds reads
as written.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

#: A run of three or more backticks or tildes opening a line, and the rest.
_MARKER = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


@dataclass(frozen=True)
class Fence:
    """One fenced block of a page.

    :param line: The line number of the opening marker, counted from 1.
    :param info: The info string after the opening marker, stripped.
    :param body: The lines between the two markers, each with its line end,
        without the indentation the opening marker carried. A fence never
        closed runs to the end of the page.
    """

    line: int
    info: str
    body: str

    @property
    def language(self) -> str:
        """The first word of the info string, empty when there is none."""
        words = self.info.split(maxsplit=1)
        return words[0] if words else ""


@dataclass(frozen=True)
class _Line:
    """One line as the fence reading classifies it."""

    text: str
    #: ``"prose"``, ``"open"``, ``"body"`` or ``"close"``.
    role: str
    #: The info string, on an opening line.
    info: str = ""
    #: The indentation of the opening marker, on every line of a fence.
    indent: int = 0


def _read(lines: Iterable[str]) -> Iterator[_Line]:
    """Every line with its part in the page: prose, or a fence's opening, body or close."""
    opening = ""
    indent = 0
    for line in lines:
        marker = _MARKER.match(line)
        if not opening:
            lead, run, rest = marker.groups() if marker else ("", "", "")
            if run and not (run[0] == "`" and "`" in rest):
                opening, indent = run, len(lead)
                yield _Line(line, "open", rest.strip(), indent)
            else:
                yield _Line(line, "prose")
            continue
        if (
            marker is not None
            and marker.group(2)[0] == opening[0]
            and len(marker.group(2)) >= len(opening)
            and not marker.group(3).strip()
        ):
            opening = ""
            yield _Line(line, "close", indent=indent)
        else:
            yield _Line(line, "body", indent=indent)


def code_lines(lines: Iterable[str]) -> Iterator[bool]:
    """Whether each line is code: a fence's opening line, its body or its closing line.

    A fence never closed runs to the end of the page, as CommonMark has it.
    """
    for line in _read(lines):
        yield line.role != "prose"


def _dedent(line: str, indent: int) -> str:
    """The line without up to ``indent`` leading blanks."""
    stripped = line.lstrip(" \t")
    return line[min(indent, len(line) - len(stripped)) :]


def fences(text: str) -> Iterator[Fence]:
    """Every fenced block of a page, in reading order.

    :param text: The page.
    :return: One :class:`Fence` per block, closed or running to the end.
    """
    start = 0
    info = ""
    body: list[str] = []
    for number, line in enumerate(_read(text.splitlines(keepends=True)), start=1):
        if line.role == "open":
            start, info, body = number, line.info, []
        elif line.role == "body":
            body.append(_dedent(line.text, line.indent))
        elif line.role == "close":
            yield Fence(start, info, "".join(body))
            start = 0
    if start:
        yield Fence(start, info, "".join(body))


def python_fences(text: str) -> list[str]:
    """The bodies of a page's Python fences, in reading order.

    A fence is Python when the first word of its info string is ``python``,
    whatever attributes follow it.
    """
    return [fence.body for fence in fences(text) if fence.language == "python"]
