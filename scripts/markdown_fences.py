#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which lines of a markdown page are code, as CommonMark reads its fences.

Every check that reads the prose of a page steps over its code first. A fence
opens on a run of at least three backticks or three tildes, and only a line
of the same character, at least as long as that run, with nothing after it
but blanks, closes it (CommonMark 0.31.2, 4.5). An info string after a run of
backticks may not hold a backtick itself: such a line is an inline code span,
not a fence. A check that closes a fence on any run of three markers loses
track at the first block that shows a fence inside another, and from there
it reads the page inside out: code as prose and prose as code. One that knows
only backticks never sees a tilde fence at all.

CommonMark lets the marker be indented by three spaces at most. These pages
nest fences inside list items, indented with the item, so any indentation is
read as a fence here.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

#: A run of three or more backticks or tildes opening a line, and the rest.
_MARKER = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")


def code_lines(lines: Iterable[str]) -> Iterator[bool]:
    """Whether each line is code: a fence's opening line, its body or its closing line.

    A fence never closed runs to the end of the page, as CommonMark has it.
    """
    opening = ""
    for line in lines:
        marker = _MARKER.match(line)
        if not opening:
            run, rest = marker.groups() if marker else ("", "")
            if run and not (run[0] == "`" and "`" in rest):
                opening = run
            yield bool(opening)
            continue
        if (
            marker is not None
            and marker.group(1)[0] == opening[0]
            and len(marker.group(1)) >= len(opening)
            and not marker.group(2).strip()
        ):
            opening = ""
        yield True
