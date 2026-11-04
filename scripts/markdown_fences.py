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

The marks of the containers that hold a fence are not the text of its line
(CommonMark 0.31.2, 5.1 and 5.2): a fence opens behind the marks of a quotation
and on the first line of a list item, each of its lines loses those marks, and
it ends with what holds it, where its quotation or its item ends. A reader that
sees no fence behind a mark takes the block for a part of the paragraph around
it, and the closing fence of one a list item opened for an opening one that runs
to the end of the page. :func:`display_math_parts` reads a ``$$`` block the same
way, as remark-math has it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

#: A run of three or more backticks or tildes opening a line, and the rest.
_MARKER = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
#: The mark of a quotation, what may stand before it and the one blank after it.
#: Any indentation is read, as for a fence, since a quotation nests in an item.
_QUOTE_MARK = re.compile(r"[ \t]*>[ \t]?")
#: The marker of a list item and the blanks after it.
_ITEM_MARKER = re.compile(r"[ \t]*(?:[-*+]|\d{1,9}[.)])[ \t]+")
#: A line that may open or close display maths, as remark-math reads it: a run
#: of two dollar signs or more and a meta with no dollar sign in it. A line with
#: another dollar sign after the run opens nothing: it is a paragraph that holds
#: inline maths.
_DISPLAY = re.compile(r"^[ \t]*(\${2,})([^$]*)$")


@dataclass(frozen=True)
class Marks:
    """What the containers of a line leave of it.

    :param depth: How many quotation marks stand before its text.
    :param within: The column of the content of the list item the line opens,
        0 when the marks end on a quotation or there are none: a line indented
        less than that is out of the item.
    :param rest: The line past its marks, each list marker left as blanks, so
        that its indentation is the column inside the last quotation.
    """

    depth: int
    within: int
    rest: str


def past_marks(line: str) -> Marks:
    """*line* read past the quotation marks and the list markers that open it."""
    depth = at = width = 0
    while True:
        mark = _QUOTE_MARK.match(line, at)
        if mark is not None:
            depth, at, width = depth + 1, mark.end(), 0
            continue
        marker = _ITEM_MARKER.match(line, at)
        if marker is None:
            return Marks(depth, width, " " * width + line[at:])
        width += marker.end() - at
        at = marker.end()


def inside_block(line: str, depth: int, within: int) -> str | None:
    """*line* inside a block opened behind marks, or ``None`` if the block has ended.

    It ends with what holds it: at a line with fewer quotation marks than it
    opened behind, and at a line of text indented less than the content of the
    list item it opened on.

    :param depth: The quotation marks it opened behind, which the line loses.
    :param within: The column of the content of the item it opened on, or 0.
    """
    for _ in range(depth):
        mark = _QUOTE_MARK.match(line)
        if mark is None:
            return None
        line = line[mark.end() :]
    if line.strip() and len(line) - len(line.lstrip(" \t")) < within:
        return None
    return line


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
    #: The line past the marks of what holds its fence, on a line of its body.
    inner: str = ""


def _read(lines: Iterable[str]) -> Iterator[_Line]:
    """Every line with its part in the page: prose, or a fence's opening, body or close."""
    opening = ""
    indent = depth = within = 0
    for line in lines:
        inner = inside_block(line, depth, within) if opening else None
        if inner is None:
            opening = ""
            marks = past_marks(line)
            marker = _MARKER.match(marks.rest)
            lead, run, rest = marker.groups() if marker else ("", "", "")
            if run and not (run[0] == "`" and "`" in rest):
                opening, indent = run, len(lead)
                depth, within = marks.depth, marks.within
                yield _Line(line, "open", rest.strip(), indent)
            else:
                yield _Line(line, "prose")
            continue
        marker = _MARKER.match(inner)
        if (
            marker is not None
            and marker.group(2)[0] == opening[0]
            and len(marker.group(2)) >= len(opening)
            and not marker.group(3).strip()
        ):
            opening = ""
            yield _Line(line, "close", indent=indent)
        else:
            yield _Line(line, "body", indent=indent, inner=inner)


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
            body.append(_dedent(line.inner, line.indent))
        elif line.role == "close":
            yield Fence(start, info, "".join(body))
            start = 0
    if start:
        yield Fence(start, info, "".join(body))


def display_math_parts(lines: Iterable[str], code: Iterable[bool]) -> list[str]:
    """Each line's part in display maths: ``"open"``, ``"maths"`` or ``"prose"``.

    ``"maths"`` is a line of the formula or the line that closes it: a run of
    dollar signs at least as long as the opening one, with nothing after it but
    blanks. A line of code opens nothing, and a block never closed runs to the
    end of the page or of what holds it, as remark-math has it. The block opens
    on such a line wherever it stands, in the middle of a paragraph too, even
    one that leaves a code span open: the structure of the blocks comes before
    the spans inside them (CommonMark 0.31.2, 6).

    :param lines: The lines of a page, its frontmatter out.
    :param code: Whether each of them is code (:func:`code_lines`).
    """
    parts: list[str] = []
    opening = ""
    depth = within = 0
    for line, is_code in zip(lines, code, strict=True):
        inner = inside_block(line, depth, within) if opening else None
        if inner is not None:
            closing = _DISPLAY.match(inner)
            if (
                closing is not None
                and len(closing.group(1)) >= len(opening)
                and not closing.group(2).strip()
            ):
                opening = ""
            parts.append("maths")
            continue
        opening = ""
        marks = past_marks(line)
        found = None if is_code else _DISPLAY.match(marks.rest)
        if found is None:
            parts.append("prose")
        else:
            opening, depth, within = found.group(1), marks.depth, marks.within
            parts.append("open")
    return parts


def python_fences(text: str) -> list[str]:
    """The bodies of a page's Python fences, in reading order.

    A fence is Python when the first word of its info string is ``python``,
    whatever attributes follow it.
    """
    return [fence.body for fence in fences(text) if fence.language == "python"]
