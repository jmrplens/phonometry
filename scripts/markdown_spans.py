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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

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


#: A line that opens a block of its own: a heading, a row of a table, an item
#: of a list or a quotation, which a code span never crosses into
#: (``BLOCK_START`` of ``site/scripts/shared/markdown-spans.mjs``).
_BLOCK_START = re.compile(r" {0,3}(?:#{1,6}(?:\s|$)|\||[-*+]\s|\d{1,9}[.)]\s|>)")
#: A block on its own line only: a heading or a row of a table.
_ONE_LINE_BLOCK = re.compile(r" {0,3}(?:#{1,6}(?:\s|$)|\|)")
#: A comment and the line that opens one, by the page's kind: an HTML comment
#: on a ``.md`` page, which opening a line is an HTML block that ends at its
#: ``-->``, and an MDX comment, an expression, beside it on a ``.mdx`` page.
_COMMENTS = {
    "md": re.compile(r"<!--.*?-->", re.DOTALL),
    "mdx": re.compile(r"<!--.*?-->|\{/\*.*?\*/\}", re.DOTALL),
}
_COMMENT_LINE = {
    "md": re.compile(r" {0,3}<!--"),
    "mdx": re.compile(r" {0,3}(?:<!--|\{/\*)"),
}


def _blocks(lines: list[str], comments: str | None) -> list[list[str]]:
    """*lines* in the blocks a code span stays inside, every line in one.

    A blank line is a block of its own and ends the one before it; a heading,
    a table row, a list item or a quotation opens one, and a line that opens
    a comment opens one that runs to the comment's end, blank lines included.
    """
    blocks: list[list[str]] = []
    current: list[str] = []
    closer = None if comments is None else _COMMENTS[comments]
    opener = None if comments is None else _COMMENT_LINE[comments]
    for line in lines:
        if current and closer is not None and _unclosed(current, closer, opener):
            current.append(line)
            continue
        if (
            not line.strip()
            or _BLOCK_START.match(line)
            or (opener and opener.match(line))
        ):
            if current:
                blocks.append(current)
            current = []
        if not line.strip():
            blocks.append([line])
            continue
        current.append(line)
        if _ONE_LINE_BLOCK.match(line):
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def _unclosed(
    block: list[str], closer: re.Pattern[str], opener: re.Pattern[str] | None
) -> bool:
    """Whether *block* opens with a comment its lines have not closed yet."""
    if opener is None or not opener.match(block[0]):
        return False
    return closer.match("\n".join(block).lstrip()) is None


def _spans_and_comments(
    text: str, markers: str, comments: str | None
) -> list[tuple[int, int]]:
    """The code spans and comments of one block, read left to right.

    Whichever opens first wins: a comment opened in a span is code, and a
    backtick in a comment is the comment's.
    """
    if comments is None:
        return inline_spans(text, markers)
    pattern = _COMMENTS[comments]
    found: list[tuple[int, int]] = []
    done = 0
    while True:
        spans = inline_spans(text[done:], markers)
        comment = pattern.search(text, done)
        span = (spans[0][0] + done, spans[0][1] + done) if spans else None
        if comment is not None and (span is None or comment.start() < span[0]):
            span = comment.span()
        if span is None:
            return found
        found.append(span)
        done = span[1]


def blank_inline_spans_by_block(
    text: str, markers: str = "`", comments: str | None = None
) -> str:
    """*text* with its spans blanked, each block of a page read whole.

    The reading of ``dropInlineSpansByBlock`` of
    ``site/scripts/shared/markdown-spans.mjs``: a code span may run over the
    lines of its paragraph, as the page reads it, but never past a blank line
    or into another block. Each character of a span but a line end becomes a
    space, so every line, and every column of it, is where it was.

    :param text: Prose, its fenced code already out (left as blank lines).
    :param markers: ``"`"`` for the code spans, ``"`$"`` for code and maths.
    :param comments: ``"md"`` or ``"mdx"`` to blank the page's comments too,
        read with the spans in one pass, as the page reads them.
    :return: The text, its spans blanked, with as many lines as it had.
    """
    return _by_block(text, markers, comments, lambda span: re.sub(r"[^\n]", " ", span))


def drop_inline_spans_by_block(
    text: str, markers: str = "`", comments: str | None = None
) -> str:
    """*text* with its spans taken out, each block of a page read whole.

    As :func:`blank_inline_spans_by_block`, but each span leaves
    :data:`SPAN_MARK` and the line breaks it held, as
    ``dropInlineSpansByBlock`` of the site leaves them: every line is where
    it was, its columns past a span are not.
    """
    return _by_block(
        text, markers, comments, lambda span: SPAN_MARK + "\n" * span.count("\n")
    )


def _by_block(
    text: str,
    markers: str,
    comments: str | None,
    replace: Callable[[str], str],
) -> str:
    """*text*, each span and comment of each block replaced by *replace* of it."""
    read: list[str] = []
    for block in _blocks(text.split("\n"), comments):
        joined = "\n".join(block)
        pieces: list[str] = []
        done = 0
        for start, end in _spans_and_comments(joined, markers, comments):
            pieces.extend((joined[done:start], replace(joined[start:end])))
            done = end
        pieces.append(joined[done:])
        read.append("".join(pieces))
    return "\n".join(read)
