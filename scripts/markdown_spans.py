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
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

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


#: A block on its own line only: a heading, a row of a table, a thematic break,
#: a setext underline, the fence of a display-math block (a run of two dollar
#: signs or more and no other after it) and a comment closed on its line.
_ONE_LINE_SHAPES = (
    r"#{1,6}(?:\s|$)|\||([-*_])[ \t]*(?:\1[ \t]*){2,}$|(?:=+|-+)[ \t]*$"
    r"|\${2,}[^$]*$|<!--.*-->"
)
#: A line that opens a block of its own, which a code span never crosses into:
#: those, an item of a list, a quotation and a comment
#: (``BLOCK_START`` of ``site/scripts/shared/markdown-spans.mjs``).
_BLOCK_START = re.compile(
    rf" {{0,3}}(?:{_ONE_LINE_SHAPES}|[-*+]\s|\d{{1,9}}[.)]\s|>|<!--)"
)
_ONE_LINE_BLOCK = re.compile(rf" {{0,3}}(?:{_ONE_LINE_SHAPES})")
#: The marker of a list item, its indentation and the blanks after it, whose
#: width is the column the item's content stands at (CommonMark 0.31.2, 5.2).
_ITEM = re.compile(r" *(?:[-*+]|\d{1,9}[.)]) +")
#: The marks of a quotation that open a line, each with what may stand before
#: it, and the one blank after the last of them (CommonMark 0.31.2, 5.1).
_QUOTE_MARKS = re.compile(r"(?: {0,3}>)+ ?")
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


def quote_depth(line: str) -> int:
    """How many quotation marks open *line*."""
    marks = _QUOTE_MARKS.match(line)
    return marks.group().count(">") if marks else 0


def inside_quotation(line: str) -> str:
    """*line* without the quotation marks that open it."""
    marks = _QUOTE_MARKS.match(line)
    return line[marks.end() :] if marks else line


@dataclass
class _Under:
    """Where a line stands: the quotation it is in and the list item it is under.

    A list item's content sets the column a block opens at, so an item nested
    in it may stand four columns in or more, where anywhere else it would be a
    line of the paragraph (CommonMark 0.31.2, 5.2). A line the paragraph carries
    on leaves that column alone, a lazy one too; one that opens a block sets it.
    """

    depth: int = 0
    column: int = 0

    def read(self, line: str) -> str:
        """*line* past the marks of its quotation and the column of the item above."""
        depth = quote_depth(line)
        if depth != self.depth:
            self.depth, self.column = depth, 0
        rest = inside_quotation(line)
        return rest[min(self.column, len(rest) - len(rest.lstrip(" "))) :]

    def settle(self, line: str) -> None:
        """Take the column of *line*, which opens a block; a bare mark has none."""
        rest = inside_quotation(line)
        if not rest.strip():
            return
        item = _ITEM.match(rest)
        self.column = (
            item.end() if item else min(self.column, len(rest) - len(rest.lstrip(" ")))
        )


def _opens_block(line: str, read: str, block: list[str]) -> bool:
    """Whether *line*, which reads as *read*, opens a block after the lines of *block*.

    The marks of a quotation are not the paragraph's text, so what decides is
    what stands after them: a blank, a heading, a table row, a list item or a
    deeper quotation ends the paragraph inside the quotation as it would outside
    it. A line with fewer marks than the block opened with carries it on lazily.
    """
    if _BLOCK_START.match(read):
        return True
    depth = quote_depth(line)
    return depth > 0 and (
        not block or depth > quote_depth(block[0]) or not read.strip()
    )


def _blocks(lines: list[str], comments: str | None) -> list[list[str]]:
    """*lines* in the blocks a code span stays inside, every line in one.

    A blank line is a block of its own and ends the one before it; a heading,
    a table row, a list item, a quotation, a thematic break, a setext underline,
    a display fence or a comment opens one, and a line that opens a comment with
    *comments* set opens one that runs to the comment's end, blank lines
    included. A quotation is read through its marks: a later line of its
    paragraph stays in the block, and what opens a block outside a quotation
    opens one inside, a line that holds only the marks being its blank line.
    """
    blocks: list[list[str]] = []
    current: list[str] = []
    closer = None if comments is None else _COMMENTS[comments]
    opener = None if comments is None else _COMMENT_LINE[comments]
    under = _Under()
    for line in lines:
        if current and closer is not None and _unclosed(current, closer, opener):
            current.append(line)
            continue
        if not line.strip():
            if current:
                blocks.append(current)
            blocks.append([line])
            current = []
            continue
        read = under.read(line)
        opens = _opens_block(line, read, current) or bool(opener and opener.match(line))
        if opens or not current:
            under.settle(line)
        if opens and current:
            blocks.append(current)
            current = []
        current.append(line)
        if not read.strip() or _ONE_LINE_BLOCK.match(read):
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def block_starts(lines: Sequence[str]) -> list[bool]:
    """Whether each of *lines* opens a block of the page, a blank line among them.

    For a reader that carries a state of its own down a paragraph, such as an
    open italic span, and has to drop it where a code span would stop.
    """
    return [
        index == 0
        for block in _blocks(list(lines), None)
        for index in range(len(block))
    ]


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
    return replace_inline_spans_by_block(
        text, lambda span: re.sub(r"[^\n]", " ", span), markers, comments
    )


def lines_read_whole(lines: Sequence[str], read: Callable[[str], str]) -> list[str]:
    """*lines* joined, handed to *read* as one text, and split back, a line each.

    For a reader that keeps every line break of what it is handed, as the
    span readers here do, so that the lines it gives back stand where the
    ones it was handed did. No lines give none back: joined, they are the
    empty text, which splits into one empty line, and a reader zipping that
    against the page's own lines would raise on an empty page.

    :raises ValueError: if *read* added or took away a line break.
    """
    if not lines:
        return []
    shown = read("\n".join(lines)).split("\n")
    if len(shown) != len(lines):
        msg = f"{len(lines)} lines came back as {len(shown)}: the reader moved a line break"
        raise ValueError(msg)
    return shown


def drop_inline_spans_by_block(
    text: str, markers: str = "`", comments: str | None = None
) -> str:
    """*text* with its spans taken out, each block of a page read whole.

    As :func:`blank_inline_spans_by_block`, but each span leaves
    :data:`SPAN_MARK` and the line breaks it held, as
    ``dropInlineSpansByBlock`` of the site leaves them: every line is where
    it was, its columns past a span are not.
    """
    return replace_inline_spans_by_block(
        text, lambda span: SPAN_MARK + "\n" * span.count("\n"), markers, comments
    )


def replace_inline_spans_by_block(
    text: str,
    replace: Callable[[str], str],
    markers: str = "`",
    comments: str | None = None,
) -> str:
    """*text*, each span and comment of each block replaced by what *replace* makes of it.

    Read as :func:`blank_inline_spans_by_block` reads them, for a reader
    that treats a code span and a maths span apart: *replace* is handed each
    span whole, from its opening run to its closing one, so its first
    character is the marker that opened it (a backslash before a run escapes
    that one character, which the span does not hold). A comment begins with
    the ``<`` or ``{`` that opens it.

    :param replace: What a span leaves in its place. It has to hold as many
        line breaks as the span did, or the lines after it move.
    :param markers: ``"`"`` for the code spans, ``"`$"`` for code and maths.
    :param comments: ``"md"`` or ``"mdx"`` to hand the page's comments to
        *replace* too, read with the spans in one pass.
    """
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
