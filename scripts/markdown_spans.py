#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Where the inline code and maths spans of a page open and close.

Every script that reads the prose of a page steps over its inline code, and
some over its inline maths, before it checks what is left; they read the
spans here, as the site's Markdown reader does. A code span opens on a run
of backticks and closes on the next run of exactly as many (CommonMark
0.31.2, 6.1); remark-math reads a run of dollar signs the same way, and the
first run on a line that finds its closing run is the span, whichever of the
two it is. A run that no later run matches opens nothing and stays text.

A backslash before the first character of a run escapes that character
alone (CommonMark 2.4): it is shown as written and opens nothing, and the
rest of the run, if any, is a run of its own. ``\`x -- y\``` is prose, and
so is ``\$5 -- \$10``. Inside a span a backslash is a character like any
other, so it escapes nothing there: ``%APPDATA%\phonometry\`` is one code
span, its closing backtick behind a backslash. A reader that took an escaped
backtick for an opening one hid the prose up to the next backtick from its
check, and one that took a backslash inside a span for an escape ran the
span on past its closing run, over the prose after it.
"""

from __future__ import annotations

import bisect
import re

#: A run of backticks or of dollar signs.
_RUN = re.compile(r"`+|\$+")


def _escaped(text: str, start: int) -> bool:
    """Whether an odd number of backslashes stands right before ``text[start]``."""
    count = 0
    while start - count > 0 and text[start - count - 1] == "\\":
        count += 1
    return count % 2 == 1


def inline_spans(text: str, markers: str = "`") -> list[tuple[int, int]]:
    """The ``(start, end)`` of every span of *text* that opens on one of *markers*.

    Read left to right: a run of a marker opens a span when a later run of
    the same marker and the same length closes it, the runs between them
    being part of the span; its first character is taken off when a
    backslash escapes it. A run of a character not in *markers* is text.
    Each closing run is looked up among the runs written the same way,
    never searched for run by run.

    :param text: A line, or the lines of a paragraph joined.
    :param markers: The characters whose runs open a span: ``"`"`` for the
        code spans, ``"`$"`` for the code and the maths spans together.
    :return: The spans, each from its opening run to the end of its closing
        one, in the order they open.
    """
    runs = [run for run in _RUN.finditer(text) if run.group()[0] in markers]
    alike: dict[str, list[int]] = {}
    for index, run in enumerate(runs):
        alike.setdefault(run.group(), []).append(index)
    spans: list[tuple[int, int]] = []
    index = 0
    while index < len(runs):
        start, written = runs[index].start(), runs[index].group()
        if _escaped(text, start):
            start, written = start + 1, written[1:]
        closing = _next(alike.get(written, []), index)
        if closing is None:
            index += 1
            continue
        spans.append((start, runs[closing].end()))
        index = closing + 1
    return spans


def _next(indexes: list[int], after: int) -> int | None:
    """The first of the sorted *indexes* past *after*, or ``None``."""
    found = bisect.bisect_right(indexes, after)
    return indexes[found] if found < len(indexes) else None


def blank_inline_spans(text: str, markers: str = "`") -> str:
    """*text* with every span of :func:`inline_spans` blanked, its line ends kept.

    Each character of a span but a line end becomes a space, so a column or
    a line counted in the result is the one of *text*.
    """
    pieces: list[str] = []
    done = 0
    for start, end in inline_spans(text, markers):
        pieces.extend((text[done:start], re.sub(r"[^\n]", " ", text[start:end])))
        done = end
    pieces.append(text[done:])
    return "".join(pieces)


#: What a span taken out leaves in its place: the object replacement
#: character, which no check reads as a letter, a digit, a space or markup.
#: The text on either side of a span stays apart, as the page shows it apart:
#: ``&`x`mdash;`` is no entity, ``1`x`000`` no number and ``x_`c`\sqrt`` no
#: subscript.
SPAN_MARK = "\ufffc"


def drop_inline_spans(text: str, markers: str = "`") -> str:
    """*text* with every span of :func:`inline_spans` taken out, each leaving :data:`SPAN_MARK`."""
    pieces: list[str] = []
    done = 0
    for start, end in inline_spans(text, markers):
        pieces.extend((text[done:start], SPAN_MARK))
        done = end
    pieces.append(text[done:])
    return "".join(pieces)
