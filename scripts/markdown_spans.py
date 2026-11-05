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

from markdown_fences import NOT_INLINE_ROLES, cell_spans, page_lines, quotation_marks

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

    from markdown_fences import PageLine

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


def quote_depth(line: str, *, kind: str = "mdx") -> int:
    """How many quotation marks open *line*, read by their columns
    (:func:`markdown_fences.quotation_marks`).

    :param kind: The page's kind, ``"md"`` or ``"mdx"``.
    """
    return quotation_marks(line, kind=kind)[0]


def inside_quotation(line: str, *, kind: str = "mdx") -> str:
    """*line* without the quotation marks that open it and the blank each may
    take, a tab after a mark leaving the rest of its columns as spaces
    (:func:`markdown_fences.quotation_marks`).

    :param kind: The page's kind, ``"md"`` or ``"mdx"``.
    """
    return quotation_marks(line, kind=kind)[1]


@dataclass
class _Block:
    """The lines a code span stays inside, and how they read.

    :param reads: ``"text"``: spans read over the lines of the block. ``"raw"``: a
        raw HTML block, shown as written, where no span opens. ``"row"``: a row of
        a table, whose cells each bound what opens in them. ``"code"``: a line of
        code or display maths, which nothing reads.
    """

    lines: list[str]
    reads: str = "text"


def _blocks(
    lines: list[str],
    comments: str | None,
    kind: str,
    walked: Iterable[PageLine] | None = None,
) -> list[_Block]:
    """*lines* in the blocks a code span stays inside, every line in one.

    The walk of the page says what each line is (:func:`markdown_fences.page_lines`):
    only the lines of a paragraph, and those of a raw HTML block, stay together. A
    blank line is a block of its own, a line that holds only the marks of a
    quotation among them, and so is a heading, a row of a table, a thematic break,
    a setext underline, an aside's fence, a line of a fence or of a display block.
    With *comments* set a line that opens a comment opens a block that runs to the
    comment's end, blank lines included.

    :param walked: The walk of the page as written, for a reader that blanks some
        of its lines first: a line blanked is no line the walk can read, and the
        container it opened would be lost with it.
    """
    blocks: list[_Block] = []
    current: _Block | None = None
    closer = None if comments is None else _COMMENTS[comments]
    opener = None if comments is None else _COMMENT_LINE[comments]
    read_lines = page_lines(lines, kind=kind) if walked is None else walked
    for line, read in zip(lines, read_lines, strict=True):
        if (
            current is not None
            and closer is not None
            and _unclosed(current.lines, closer, opener)
        ):
            current.lines.append(line)
            continue
        if current is not None and read.role in ("text", "raw"):
            current.lines.append(line)
            continue
        if current is not None:
            blocks.append(current)
            current = None
        if read.role in NOT_INLINE_ROLES:
            blocks.append(_Block([line], "code"))
        elif read.role in ("paragraph", "text") or (opener and opener.match(line)):
            current = _Block([line])
        elif read.role in ("html", "raw"):
            current = _Block([line], "raw")
        else:
            blocks.append(_Block([line], "row" if read.role == "row" else "text"))
    if current is not None:
        blocks.append(current)
    return blocks


def block_starts(lines: Sequence[str], *, kind: str = "md") -> list[bool]:
    """Whether each of *lines* opens a block of the page, a blank line among them.

    For a reader that carries a state of its own down a paragraph, such as an
    open italic span, and has to drop it where a code span would stop. Each line
    of a raw HTML block counts as one: nothing there is markup to carry.

    :param kind: ``"md"`` or ``"mdx"``, the page's kind.
    """
    return [
        index == 0 or block.reads == "raw"
        for block in _blocks(list(lines), None, kind)
        for index in range(len(block.lines))
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
    """The code spans and comments of a piece of a block, read left to right.

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


def _block_spans(
    block: _Block, text: str, markers: str, comments: str | None
) -> list[tuple[int, int]]:
    """The spans and comments of one block, whose lines are joined in *text*."""
    if block.reads == "code":
        return []
    if block.reads == "raw":
        return _spans_and_comments(text, "", comments)
    if block.reads == "text":
        return _spans_and_comments(text, markers, comments)
    return [
        (first + start, last + start)
        for start, end in cell_spans(text)
        for first, last in _spans_and_comments(text[start:end], markers, comments)
    ]


def blank_inline_spans_by_block(
    text: str,
    markers: str = "`",
    comments: str | None = None,
    *,
    kind: str = "",
    walked: Iterable[PageLine] | None = None,
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
    :param kind: ``"md"`` or ``"mdx"``, the page's kind, if not said by *comments*;
        a ``.md`` page if neither says.
    :param walked: The walk of the page as written, for a reader that blanked some
        of its lines (:func:`_blocks`).
    :return: The text, its spans blanked, with as many lines as it had.
    """
    return replace_inline_spans_by_block(
        text,
        lambda span: re.sub(r"[^\n]", " ", span),
        markers,
        comments,
        kind=kind,
        walked=walked,
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
    text: str, markers: str = "`", comments: str | None = None, *, kind: str = ""
) -> str:
    """*text* with its spans taken out, each block of a page read whole.

    As :func:`blank_inline_spans_by_block`, but each span leaves
    :data:`SPAN_MARK` and the line breaks it held, as
    ``dropInlineSpansByBlock`` of the site leaves them: every line is where
    it was, its columns past a span are not.
    """
    return replace_inline_spans_by_block(
        text,
        lambda span: SPAN_MARK + "\n" * span.count("\n"),
        markers,
        comments,
        kind=kind,
    )


def replace_inline_spans_by_block(
    text: str,
    replace: Callable[[str], str],
    markers: str = "`",
    comments: str | None = None,
    *,
    kind: str = "",
    walked: Iterable[PageLine] | None = None,
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
    :param kind: ``"md"`` or ``"mdx"``, the page's kind, if not said by *comments*;
        a ``.md`` page if neither says.
    :param walked: The walk of the page as written, for a reader that blanked some
        of its lines (:func:`_blocks`).
    """
    read: list[str] = []
    page_kind = kind or comments or "md"
    for block in _blocks(text.split("\n"), comments, page_kind, walked):
        joined = "\n".join(block.lines)
        pieces: list[str] = []
        done = 0
        for start, end in _block_spans(block, joined, markers, comments):
            pieces.extend((joined[done:start], replace(joined[start:end])))
            done = end
        pieces.append(joined[done:])
        read.append("".join(pieces))
    return "\n".join(read)
