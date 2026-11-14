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
import string
from dataclasses import dataclass
from typing import TYPE_CHECKING

from markdown_fences import (
    MDX_EXPRESSION,
    MDX_TAG,
    NOT_INLINE_ROLES,
    cell_spans,
    page_lines,
    quotation_marks,
)

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
#: MDX shows nothing of an expression that holds only a comment, so the blanks
#: between its braces and the comment are the comment's too (``{ /* x */ }``).
_COMMENTS = {
    "md": re.compile(r"<!--.*?-->", re.DOTALL),
    "mdx": re.compile(r"<!--.*?-->|\{\s*/\*.*?\*/\s*\}", re.DOTALL),
}
_COMMENT_LINE = {
    "md": re.compile(r" {0,3}<!--"),
    "mdx": re.compile(r" {0,3}(?:<!--|\{[ \t]*/\*)"),
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


def block_starts(
    lines: Sequence[str],
    *,
    kind: str = "md",
    walked: Iterable[PageLine] | None = None,
) -> list[bool]:
    """Whether each of *lines* opens a block of the page, a blank line among them.

    For a reader that carries a state of its own down a paragraph, such as an
    open italic span, and has to drop it where a code span would stop. Each line
    of a raw HTML block counts as one: nothing there is markup to carry.

    :param kind: ``"md"`` or ``"mdx"``, the page's kind.
    :param walked: The walk of *lines* (:func:`markdown_fences.page_lines`), for a
        reader that holds it already, so that the page is walked once.
    """
    return [
        index == 0 or block.reads == "raw"
        for block in _blocks(list(lines), None, kind, walked)
        for index in range(len(block.lines))
    ]


def _unclosed(
    block: list[str], closer: re.Pattern[str], opener: re.Pattern[str] | None
) -> bool:
    """Whether *block* opens with a comment its lines have not closed yet."""
    if opener is None or not opener.match(block[0]):
        return False
    return closer.match("\n".join(block).lstrip()) is None


def _escaped_since(text: str, at: int, done: int) -> bool:
    """Whether a backslash escapes ``text[at]``, its run counted back no further than *done*.

    *done* is where the last span, comment or construct read ended: a backslash
    one of them holds escapes nothing after it.
    """
    count = 0
    while at - count > done and text[at - count - 1] == "\\":
        count += 1
    return count % 2 == 1


def _escaped_match(match: re.Match[str], text: str, done: int) -> bool:
    r"""Whether a backslash escapes the ASCII punctuation character *match* opens on.

    ``\{`` and ``\<`` show the character and open nothing (CommonMark 0.31.2,
    2.4), so a comment or a construct that opens there is no comment or
    construct, and what follows it is prose. A backslash before any other
    character escapes nothing.
    """
    start = match.start()
    return (
        start < len(text)
        and text[start] in string.punctuation
        and _escaped_since(text, start, done)
    )


def _search_unescaped(
    pattern: re.Pattern[str], text: str, done: int, stop: int
) -> tuple[re.Match[str] | None, int | None]:
    """The first match of *pattern* at or past *done* that no backslash escapes.

    :return: The match, or ``None``, and where the first escaped match it passed
        over stands, or ``None``, since that one opens after all once the
        reading ends a span right after its backslash.
    """
    at = done
    skipped = None
    while (match := pattern.search(text, at, stop)) is not None:
        if not _escaped_match(match, text, done):
            return match, skipped
        if skipped is None:
            skipped = match.start()
        at = match.start() + 1
    return None, skipped


def _first_found(
    found: list[tuple[re.Match[str] | None, int | None]],
    others: Sequence[re.Pattern[str]],
    text: str,
    done: int,
    stop: int,
) -> re.Match[str] | None:
    """The match of *others* that opens first at or past *done*, the earlier listed on a tie.

    *found* holds each pattern's next match and the escaped one it passed over,
    kept from one call to the next so that a pattern is searched again only once
    the reading has passed its match, or once a backslash may escape it or no
    longer escape the one it passed over.
    """
    for index, pattern in enumerate(others):
        match, skipped = found[index]
        stale = match is not None and (
            match.start() < done or _escaped_match(match, text, done)
        )
        if stale or (skipped is not None and skipped >= done):
            found[index] = _search_unescaped(pattern, text, done, stop)
    present = [match for match, _ in found if match is not None]
    return min(present, key=lambda match: match.start()) if present else None


def _spans_and_others(
    text: str,
    markers: str,
    others: Sequence[re.Pattern[str]],
    start: int = 0,
    end: int | None = None,
) -> list[tuple[int, int]]:
    """The spans of a piece of a block and what *others* find there, read left to right.

    Whichever opens first wins: a comment or a construct opened in a span is
    code, and a backtick in a comment or a construct is its own. One that opens
    on a character a backslash escapes opens nothing there. The spans past a
    comment or a construct that holds a run are read again from its end, since
    that run no longer opens or closes one.

    :param text: The block, its lines joined.
    :param others: The comments of the page and the reader's own constructs,
        each searched in *text* itself, so that what stands before the piece
        (the pipe before a cell, the start of a line) is what it sees there.
    :param start: Where the piece opens in *text*.
    :param end: Where it ends; the end of *text* by default.
    :return: The spans and the finds, from their start to their end in *text*,
        in the order they open.
    """
    stop = len(text) if end is None else end

    def spans_from(done: int) -> list[tuple[int, int]]:
        return [
            (first + done, last + done)
            for first, last in inline_spans(text[done:stop], markers)
        ]

    if not others:
        return spans_from(start)
    found: list[tuple[int, int]] = []
    matches = [_search_unescaped(pattern, text, start, stop) for pattern in others]
    spans = spans_from(start)
    upcoming = 0
    done = start
    while True:
        while upcoming < len(spans) and spans[upcoming][0] < done:
            upcoming += 1
        span = spans[upcoming] if upcoming < len(spans) else None
        other = _first_found(matches, others, text, done, stop)
        if other is not None and (span is None or other.start() < span[0]):
            found.append(other.span())
            done = other.end()
            if markers and any(marker in other.group() for marker in markers):
                spans, upcoming = spans_from(done), 0
            continue
        if span is None:
            return found
        found.append(span)
        done = span[1]


def _block_spans(
    block: _Block, text: str, markers: str, others: Sequence[re.Pattern[str]]
) -> list[tuple[int, int]]:
    """The spans, comments and constructs of one block, whose lines are joined in *text*."""
    if block.reads == "code":
        return []
    if block.reads == "raw":
        return _spans_and_others(text, "", others)
    if block.reads == "text":
        return _spans_and_others(text, markers, others)
    return [
        found
        for start, end in cell_spans(text)
        for found in _spans_and_others(text, markers, others, start, end)
    ]


def blank_inline_spans_by_block(
    text: str,
    markers: str = "`",
    comments: str | None = None,
    *,
    kind: str = "",
    walked: Iterable[PageLine] | None = None,
    constructs: Sequence[re.Pattern[str]] = (),
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
    :param constructs: The reader's own constructs to blank with the spans
        (:func:`replace_inline_spans_by_block`).
    :return: The text, its spans blanked, with as many lines as it had.
    """
    return replace_inline_spans_by_block(
        text,
        lambda span: re.sub(r"[^\n]", " ", span),
        markers,
        comments,
        kind=kind,
        walked=walked,
        constructs=constructs,
    )


#: JavaScript's ``\s``, which Astro's reading of a frontmatter is written with:
#: Python's own takes other characters and leaves the byte order mark out.
_JS_SPACE = (
    r"[\t\n\v\f\r \u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]"
)
#: A page's frontmatter as Astro reads it (``frontmatterRE`` of
#: ``@astrojs/internal-helpers``): fenced by ``---`` or by ``+++``, at the start
#: of the page behind a byte order mark or after blank lines, its closing fence
#: opening a line. One that never closes is no frontmatter.
_FRONTMATTER = re.compile(
    rf"(?:\A\ufeff?|\A{_JS_SPACE}*\n)(?:---|\+\+\+)(.*?\n)(?:---|\+\+\+)", re.DOTALL
)
#: A backslash and the ASCII punctuation character it escapes (CommonMark
#: 0.31.2, 2.4): the page shows the character, and it opens nothing.
_ESCAPE = re.compile(r"\\[!-/:-@\[-`{-~]")
#: A tag of raw HTML written in the prose of a ``.md`` page, open or closing,
#: and an autolink (CommonMark 0.31.2, 6.6 and 6.5), each taken whole.
_HTML_TAG = re.compile(
    r"<[A-Za-z][A-Za-z0-9-]*(?:[ \t\n]+[A-Za-z_:][\w.:-]*"
    r"(?:[ \t\n]*=[ \t\n]*(?:[^ \t\n\"'=<>`]+|'[^']*'|\"[^\"]*\"))?)*[ \t\n]*/?>"
    r"|</[A-Za-z][A-Za-z0-9-]*[ \t\n]*>"
    r"|<[A-Za-z][A-Za-z0-9+.-]{1,31}:[^ \t\n<>]*>"
)
#: What may open where a backslash, a tag, an expression or a comment does.
_OPENER = re.compile(r"[\\<{]")


def _blank(text: str) -> str:
    """*text* with every character but a line end a space."""
    return re.sub(r"[^\n]", " ", text)


def _opened_at(
    text: str, at: int, end: int, *, kind: str, reads: str
) -> tuple[int, bool] | None:
    """Where what opens at ``text[at]`` ends, and whether the page renders it as
    markup, or ``None`` when nothing opens there.

    A backslash escape and a comment end inside the piece of a block that ends at
    *end*; a tag and an expression may run on over the lines after it. On the
    lines of a raw HTML block only a comment opens.
    """
    opened = text[at]
    comment = _COMMENTS[kind].match(text, at, end) if opened in "<{" else None
    if comment is not None:
        return comment.end(), False
    if reads == "raw":
        return None
    if opened == "\\":
        escape = _ESCAPE.match(text, at, end)
        return None if escape is None else (escape.end(), False)
    if opened == "<":
        tag = (MDX_TAG if kind == "mdx" else _HTML_TAG).match(text, at)
        return None if tag is None else (tag.end(), True)
    if kind == "mdx":
        expression = MDX_EXPRESSION.match(text, at)
        return None if expression is None else (expression.end(), False)
    return None


def _first_opened(
    text: str, at: int, end: int, *, kind: str, reads: str
) -> tuple[int, int, bool] | None:
    """The first escape, comment, tag or expression past *at* and before *end*:
    where it opens and ends, and whether the page renders it as markup.
    """
    for opener in _OPENER.finditer(text, at, end):
        opened = _opened_at(text, opener.start(), end, kind=kind, reads=reads)
        if opened is not None:
            return opener.start(), *opened
    return None


def _unrendered(
    text: str, *, kind: str, walked: Sequence[PageLine]
) -> list[tuple[int, int]]:
    """The ``(start, end)`` of each part of *text* the page shows as text or hides.

    Read left to right, each block of the page (:func:`_blocks`) and each cell
    of a row on its own, as the site's parser reads them: at each character the
    first of a code or maths span, a backslash escape, a comment, a tag and an
    expression that opens there takes what follows. A tag the page renders is
    markup, and the spans, escapes and expressions are read again from its end:
    nothing between its quotes opens a span. Everything else that opened is in
    the result. A tag and an expression may run on over the lines after their
    block, as a component written over several lines does.

    The spans of a piece are read once and taken in turn, and are read again only
    past what else opened, which may have held a run of theirs; the next opener is
    looked for again only once a span has held it.

    :param text: The page, its frontmatter and its code and display maths blanked.
    :param kind: ``"md"`` or ``"mdx"``, the page's kind.
    :param walked: The walk of the page with its frontmatter blanked.
    """
    found: list[tuple[int, int]] = []
    at = 0
    start = 0
    for block in _blocks(text.split("\n"), kind, kind, walked):
        joined = "\n".join(block.lines)
        pieces = (
            [(start + first, start + last) for first, last in cell_spans(joined)]
            if block.reads == "row"
            else [(start, start + len(joined))]
        )
        start += len(joined) + 1
        if block.reads == "code":
            continue
        markers = "" if block.reads == "raw" else "`$"
        for first, last in pieces:
            at = max(at, first)
            spans: list[tuple[int, int]] | None = None
            opened: tuple[int, int, bool] | None = None
            looked = False
            while at < last:
                if spans is None:
                    spans = [
                        (at + a, at + b)
                        for a, b in inline_spans(text[at:last], markers)
                    ]
                    spans.reverse()
                if not looked or (opened is not None and opened[0] < at):
                    opened = _first_opened(text, at, last, kind=kind, reads=block.reads)
                    looked = True
                span = spans[-1] if spans else None
                if span is not None and (opened is None or span[0] < opened[0]):
                    found.append(spans.pop())
                    at = span[1]
                elif opened is not None:
                    if not opened[2]:
                        found.append(opened[:2])
                    at = opened[1]
                    spans, looked = None, False
                else:
                    break
    return found


def page_markup(text: str, *, kind: str = "mdx") -> str:
    """*text* with every part of the page that renders no tag blanked.

    A component a page renders, a ``<Video>`` or a ``<ReportPreview>``, is a tag
    written outside its frontmatter, its code, fenced or indented, its display
    maths, its inline code and maths spans, its comments and its expressions,
    and not behind a backslash. Written in any of those it is text the page
    shows or hides, and a reader that looks for a component in the page as
    written counts it as one the page embeds. Each of them is blanked here as
    the site reads it: the frontmatter as Astro finds it, after a byte order
    mark or blank lines too, the blocks by one walk of the page
    (:func:`markdown_fences.page_lines`), and the rest left to right over each
    block, whichever opens first taking what follows: a span written before a
    tag holds it, and a tag holds what its attributes write, a ``$`` or a
    backtick among them. On a ``.md`` page a tag is one of raw HTML, and there
    is no expression. Every character blanked but a line end becomes a space,
    so a tag found in the result stands at the line and the column where the
    page writes it, as the page writes it.

    ``pageMarkup`` of ``site/scripts/shared/markdown-spans.mjs`` is the same
    reading for the site's code.

    :param text: The page as written, its frontmatter in.
    :param kind: ``"md"`` or ``"mdx"``, the page's kind.
    :return: The page, as many lines long as it was.
    """
    head = _FRONTMATTER.match(text)
    body = text if head is None else _blank(text[: head.end()]) + text[head.end() :]
    lines = body.split("\n")
    walked = list(page_lines(lines, kind=kind))
    prose = "\n".join(
        " " * len(line) if read.role in NOT_INLINE_ROLES else line
        for line, read in zip(lines, walked, strict=True)
    )
    pieces: list[str] = []
    done = 0
    for start, end in _unrendered(prose, kind=kind, walked=walked):
        pieces.extend((prose[done:start], _blank(prose[start:end])))
        done = end
    pieces.append(prose[done:])
    return "".join(pieces)


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
    text: str,
    markers: str = "`",
    comments: str | None = None,
    *,
    kind: str = "",
    walked: Iterable[PageLine] | None = None,
) -> str:
    """*text* with its spans taken out, each block of a page read whole.

    As :func:`blank_inline_spans_by_block`, but each span leaves
    :data:`SPAN_MARK` and the line breaks it held, as
    ``dropInlineSpansByBlock`` of the site leaves them: every line is where
    it was, its columns past a span are not.

    :param walked: The walk of the page (:func:`_blocks`).
    """
    return replace_inline_spans_by_block(
        text,
        lambda span: SPAN_MARK + "\n" * span.count("\n"),
        markers,
        comments,
        kind=kind,
        walked=walked,
    )


def replace_inline_spans_by_block(
    text: str,
    replace: Callable[[str], str],
    markers: str = "`",
    comments: str | None = None,
    *,
    kind: str = "",
    walked: Iterable[PageLine] | None = None,
    constructs: Sequence[re.Pattern[str]] = (),
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
    :param constructs: What else the reader takes out of the prose, an address
        or an attribute of a tag, each handed to *replace* as a comment is. Each
        is read with the spans and the comments in the same pass, whichever
        opens first winning, in every block a comment is read in, a raw HTML
        block among them: a URL written in a code span is code, and a backtick
        in a URL opens no span. The site's scripts read no such construct, so
        ``dropInlineSpansByBlock`` takes none.
    """
    read: list[str] = []
    page_kind = kind or comments or "md"
    others = [*([_COMMENTS[comments]] if comments else []), *constructs]
    for block in _blocks(text.split("\n"), comments, page_kind, walked):
        joined = "\n".join(block.lines)
        pieces: list[str] = []
        done = 0
        for start, end in _block_spans(block, joined, markers, others):
            pieces.extend((joined[done:start], replace(joined[start:end])))
            done = end
        pieces.append(joined[done:])
        read.append("".join(pieces))
    return "\n".join(read)
