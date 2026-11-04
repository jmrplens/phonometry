#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where the blocks of a markdown page open and close, as the site's parser reads them.

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

Whether a line opens a block depends on the lines above it, so the page is
walked once, line by line (:func:`page_lines`), as a parser's first phase walks
it (CommonMark 0.31.2, 5 and appendix). The walk keeps the quotations and the
list items open at each line and what stands open inside them, and reads each
line against them:

- A line stays in a quotation behind its mark, and in a list item at the item's
  column or blank. A block ends with what holds it, so a fence or a ``$$`` block
  opened on a later line of an item ends with the item, and one behind ``- >``
  ends at a line with a mark but without the item's column.
- A paragraph carries on through a line with fewer marks or less indentation
  than it opened with, unless that line opens a block of its own. A setext
  underline is never such a line, so at a shallower container ``===`` and ``--``
  are text. An ordered marker other than 1 and an empty marker do not interrupt
  the paragraph above them in their own container, and do start a list where
  that container has ended.
- A pipe opens a table only over a delimiter row with as many cells, one that
  holds a pipe or a colon; without one, it is text. A cell bounds what opens in
  it (:func:`cell_spans`).
- An aside (``:::note``) interrupts a paragraph, and a lone ``:::`` closes one
  and is text with none open. A display-math block is read as a fence of ``$``,
  as remark-math has it (:func:`display_math_parts`), so neither reads the other
  as an opening.

The page's kind decides what indentation and a tag mean. On a ``.md`` page, four
columns past the container open no block: they are a line of the paragraph above
or indented code. A raw HTML block (types 1 to 7 of CommonMark 4.6) runs to its
end condition, and all but the seventh interrupt a paragraph. On a ``.mdx`` page
indented code does not exist, so any indentation opens a block and the pages
nest fences that way inside a component, and there is no HTML: a tag or an
expression with its lines to itself ends a paragraph instead. A reader that does
not say which page it holds is read as ``.mdx``, whose fences are the wider
reading.

The body of an indented fence loses as much indentation as its opening marker
carried, as CommonMark has it, so the code it holds reads as written.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

#: A run of three or more backticks or tildes opening a line, and the rest.
_MARKER = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
#: A line that may open or close display maths, as remark-math reads it: a run
#: of two dollar signs or more and a meta with no dollar sign in it. A line with
#: another dollar sign after the run opens nothing: it is a paragraph that holds
#: inline maths.
_DISPLAY = re.compile(r"^[ \t]*(\${2,})([^$]*)$")
#: What stands for a quotation among the containers open at a line. A list item
#: stands for itself, by the width of its marker.
_QUOTATION = -1
#: Four columns past its container, a line opens no block on a ``.md`` page.
_CODE_INDENT = 4
#: How many columns a marker may leave before its text and still set its column,
#: on a ``.md`` page: past those, the item opens on indented code.
_MOST_BLANKS_AFTER_MARKER = 4
#: A tab's stop, in columns.
_TAB_STOP = 4
#: The marker of a list item, the number of an ordered one captured. Nothing but
#: a blank or the end of the line may follow it.
_ITEM_MARKER = re.compile(r"(?:[-*+]|(\d{1,9})[.)])(?=[ \t]|$)")
#: A heading written with its marks.
_ATX_HEADING = re.compile(r"#{1,6}(?:[ \t]|$)")
#: A thematic break, as written past what opens the line.
_THEMATIC_BREAK = re.compile(r"([-*_])[ \t]*(?:\1[ \t]*){2,}$")
#: A setext underline, as written past what opens the line.
_UNDERLINE = re.compile(r"(?:=+|-+)[ \t]*$")
#: The delimiter row of a table: one cell or more of hyphens and alignment colons.
_DELIMITER_ROW = re.compile(r"\|?[ \t]*:?-+:?[ \t]*(?:\|[ \t]*:?-+:?[ \t]*)*\|?[ \t]*$")
#: What decides a table's cells, left to right: an escape, or the pipe between two.
_CELL_MARK = re.compile(r"\\.|\|")
#: The attributes and the label a directive may carry.
_DIRECTIVE_REST = r"[A-Za-z0-9][A-Za-z0-9_-]*(?:\[[^\]]*\])?(?:\{[^}]*\})?[ \t]*$"
#: A line that opens an aside, a container directive of three colons or more.
_ASIDE = re.compile(rf"(:{{3,}}){_DIRECTIVE_REST}")
#: A line that is one leaf directive, of two colons exactly.
_LEAF_DIRECTIVE = re.compile(rf"::{_DIRECTIVE_REST}")
#: A line of colons alone, which closes an aside as long as it or longer.
_ASIDE_CLOSE = re.compile(r"(:{3,})[ \t]*$")
#: The element names of a raw HTML block of type 6, which may interrupt a paragraph
#: (``HTML_BLOCK_TAG`` of ``site/src/lib/markdown-fences.mjs``).
_HTML_BLOCK_NAMES = (
    "address|article|aside|base|basefont|blockquote|body|caption|center|col|"
    "colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|"
    "form|frame|frameset|h[1-6]|head|header|hr|html|iframe|legend|li|link|main|"
    "menu|menuitem|nav|noframes|ol|optgroup|option|p|param|search|section|summary|"
    "table|tbody|td|tfoot|th|thead|title|tr|track|ul"
)
#: How a raw HTML block of types 1 to 6 opens and what ends it, ``None`` being a
#: blank line (CommonMark 0.31.2, 4.6). These are the ends the Markdown parser reads,
#: which is what decides a page: ``--!>``, which a browser takes as the end of a
#: comment, does not end a block here.
_HTML_BLOCKS: tuple[tuple[re.Pattern[str], Callable[[str], bool] | None], ...] = (
    (
        re.compile(r"<(?:script|pre|style|textarea)(?:[ \t>]|$)", re.IGNORECASE),
        lambda line: (
            re.search(r"</(?:script|pre|style|textarea)>", line, re.IGNORECASE)
            is not None
        ),
    ),
    (re.compile(r"<!--"), lambda line: "-->" in line),
    (re.compile(r"<\?"), lambda line: "?>" in line),
    (re.compile(r"<![A-Za-z]"), lambda line: ">" in line),
    (re.compile(r"<!\[CDATA\["), lambda line: "]]>" in line),
    (
        re.compile(rf"</?(?:{_HTML_BLOCK_NAMES})(?:[ \t]|/?>|$)", re.IGNORECASE),
        None,
    ),
)
#: A raw HTML block of type 7: any other complete tag alone on its line. It runs
#: to a blank line, it cannot interrupt a paragraph in its own container, and on a
#: lazy line the site's parser opens it in the paragraph's container, which stays.
_HTML_LONE_TAG = re.compile(
    r"(?:<[A-Za-z][A-Za-z0-9-]*(?:[ \t]+[A-Za-z_:][\w.:-]*"
    r"(?:[ \t]*=[ \t]*(?:[^ \t\"'=<>`]+|'[^']*'|\"[^\"]*\"))?)*[ \t]*/?>"
    r"|</[A-Za-z][A-Za-z0-9-]*[ \t]*>)[ \t]*$"
)
#: A tag of an ``.mdx`` page, over as many lines as it takes: a quoted value and
#: an expression among its attributes may hold a ``>``.
_MDX_TAG = re.compile(
    r"</?(?:[A-Za-z_$][\w.:$-]*"
    r"(?:[^\"'>{]|\"[^\"]*\"|'[^']*'|\{(?:[^{}]|\{[^{}]*\})*\})*)?>"
)
#: An expression of an ``.mdx`` page, over as many lines as it takes: a comment,
#: or braces balanced three levels down.
_MDX_EXPRESSION = re.compile(
    r"\{\s*/\*.*?\*/\s*\}|\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}", re.DOTALL
)
#: The roles of a line that is code.
_CODE_ROLES = frozenset({"open", "body", "close", "indented"})
#: The roles of a line of a display block.
_MATHS_ROLES = {"maths-open": "open", "maths": "maths"}
#: The roles of a line whose text no inline span of the page reaches.
NOT_INLINE_ROLES = _CODE_ROLES | set(_MATHS_ROLES)


def _blank_columns(text: str, column: int) -> int:
    """How many columns the blanks that open *text* take, it standing at *column*."""
    at = column
    for char in text:
        if char == " ":
            at += 1
        elif char == "\t":
            at += _TAB_STOP - at % _TAB_STOP
        else:
            break
    return at - column


def _past_columns(text: str, column: int, width: int) -> str:
    """*text* past *width* columns of its opening blanks, a split tab left as spaces."""
    at = column
    end = column + width
    for index, char in enumerate(text):
        if at >= end:
            return " " * (at - end) + text[index:]
        if char == " ":
            at += 1
        elif char == "\t":
            at += _TAB_STOP - at % _TAB_STOP
        else:
            return text[index:]
    return " " * max(at - end, 0)


def cell_spans(row: str) -> list[tuple[int, int]]:
    """The ``(start, end)`` of each piece of a table's row, between its unescaped pipes."""
    spans: list[tuple[int, int]] = []
    start = 0
    for mark in _CELL_MARK.finditer(row):
        if mark.group() == "|":
            spans.append((start, mark.start()))
            start = mark.end()
    spans.append((start, len(row)))
    return spans


def _cell_count(row: str) -> int:
    """How many cells a row holds, its outer pipes opening and closing none."""
    pieces = [row[start:end] for start, end in cell_spans(row.strip(" \t"))]
    if len(pieces) > 1 and not pieces[0].strip(" \t"):
        pieces.pop(0)
    if len(pieces) > 1 and not pieces[-1].strip(" \t"):
        pieces.pop()
    return len(pieces)


@dataclass(frozen=True)
class PageLine:
    """One line of a page, as the walk reads it.

    :param text: The line as written.
    :param role: Its part in the page. ``"blank"``: nothing past its marks.
        ``"paragraph"``: it opens one; ``"text"``: it carries one on, a lazy line
        among them. ``"single"``: a block of its own, a heading, a thematic break,
        an aside's fence, a tag or an expression alone. ``"underline"``: the setext
        underline of the paragraph above. ``"row"``: a row of a table, its delimiter
        row among them. ``"html"``: it opens a raw HTML block; ``"raw"``: it carries
        one on. ``"indented"``: indented code. ``"open"``, ``"body"``, ``"close"``:
        a line of a fence. ``"maths-open"``, ``"maths"``: the line that opens a
        display block, and any other of it, its closing fence among them.
    :param info: The info string of a fence or the meta of a display block, on the
        line that opens it.
    :param indent: The indentation of the opening marker, on every line of a fence.
    :param inner: The line past the marks of what holds its fence, on a line of
        its body, its line end kept.
    :param rest: The line past the marks and the columns of its containers, and
        past those it opens.
    :param item: Whether the last container it opens is a list item, so that
        *rest* opens with the item's text.
    """

    text: str
    role: str
    info: str = ""
    indent: int = 0
    inner: str = ""
    rest: str = ""
    item: bool = False


class _Walk:
    """What stands open at each line of a page, read a line at a time."""

    def __init__(self, lines: list[str], kind: str) -> None:
        self.lines = lines
        #: Whether four columns past a container open no block, and whether a raw
        #: HTML block exists: both on a ``.md`` page, neither on an ``.mdx`` one.
        self.markdown = kind == "md"
        #: The containers open, outermost first.
        self.held: list[int] = []
        #: Whether the last item opened with nothing on its line: a blank line
        #: right under it ends it.
        self.fresh = False
        #: What stands open in the last container: ``""``, ``"paragraph"``,
        #: ``"table"``, ``"fence"``, ``"maths"``, ``"html"`` or ``"indented"``.
        self.leaf = ""
        #: The run that closes the fence or the display block open.
        self.opening = ""
        #: The indentation of the marker of the fence open.
        self.indent = 0
        #: What ends the raw HTML block open, ``None`` being a blank line.
        self.html_end: Callable[[str], bool] | None = None
        #: The asides open, innermost last, each with its colons, how many
        #: containers stood around it and the indentation of its fence, which its
        #: lines lose.
        self.asides: list[tuple[int, int, int]] = []
        #: How many more lines a tag or an expression of an ``.mdx`` page takes.
        self.left = 0
        #: Whether the last container the line read opened is a list item.
        self.item = False

    def read(self, index: int) -> PageLine:
        """The line at *index*, which has to come after the one read last."""
        written = self.lines[index]
        text = written.rstrip("\r\n")
        closed = self._closes_aside(text)
        if closed is not None:
            return PageLine(written, "single", rest=closed)
        rest, column, matched = self._past_held(text, len(self.held))
        self.fresh = False
        if self.left:
            self.left -= 1
            return PageLine(written, "single", rest=rest)
        if self.leaf in ("fence", "maths", "html"):
            if matched == len(self.held) and not self._ends_on_blank(rest):
                return self._inside(written, text, rest)
            self.leaf = ""
        return replace(
            self._opening(index, written, rest, column, matched), item=self.item
        )

    def _past_held(self, text: str, upto: int) -> tuple[str, int, int]:
        """*text* past the first *upto* containers: what is left, its column, how many held it."""
        rest, column = text, 0
        for index, held in enumerate(self.held[:upto]):
            rest, column = self._past_aside(rest, column, index)
            if held == _QUOTATION:
                mark = self._quote_mark(rest, column)
                if mark is None:
                    return rest, column, index
                rest, column = mark
            elif rest.strip(" \t"):
                if _blank_columns(rest, column) < held:
                    return rest, column, index
                rest = _past_columns(rest, column, held)
                column += held
            elif self.fresh and index == len(self.held) - 1:
                return rest, column, index
        rest, column = self._past_aside(rest, column, upto)
        return rest, column, upto

    def _past_aside(self, rest: str, column: int, depth: int) -> tuple[str, int]:
        """*rest* past the indentation of the asides at *depth* containers, and its column."""
        for _, around, indent in self.asides:
            if around == depth:
                width = min(indent, _blank_columns(rest, column))
                rest = _past_columns(rest, column, width)
                column += width
        return rest, column

    def _quote_mark(self, rest: str, column: int) -> tuple[str, int] | None:
        """What a quotation's mark leaves of *rest*, and at which column, or ``None``."""
        blanks = _blank_columns(rest, column)
        body = rest.lstrip(" \t")
        if not body.startswith(">") or (self.markdown and blanks >= _CODE_INDENT):
            return None
        at = column + blanks + 1
        after = body[1:]
        if after[:1] in (" ", "\t"):
            return _past_columns(after, at, 1), at + 1
        return after, at

    def _closes_aside(self, text: str) -> str | None:
        """What is left of a line that closes the innermost aside, or ``None``."""
        if not self.asides:
            return None
        colons, around, _ = self.asides[-1]
        rest, column, matched = self._past_held(text, around)
        close = _ASIDE_CLOSE.match(rest.lstrip(" \t"))
        if (
            matched < around
            or close is None
            or len(close.group(1)) < colons
            or (self.markdown and _blank_columns(rest, column) >= _CODE_INDENT)
        ):
            return None
        self.asides.pop()
        self._close_to(around)
        self.leaf = ""
        return rest

    def _ends_on_blank(self, rest: str) -> bool:
        """Whether *rest* ends a raw HTML block that a blank line ends."""
        return self.leaf == "html" and self.html_end is None and not rest.strip(" \t")

    def _inside(self, written: str, text: str, rest: str) -> PageLine:
        """A line that the fence, the display block or the HTML block open holds."""
        if self.leaf == "html":
            if self.html_end is not None and self.html_end(rest):
                self.leaf = ""
            return PageLine(written, "raw", rest=rest)
        deep = self.markdown and _blank_columns(rest, 0) >= _CODE_INDENT
        if self.leaf == "maths":
            closing = _DISPLAY.match(rest)
            if (
                closing is not None
                and not deep
                and len(closing.group(1)) >= len(self.opening)
                and not closing.group(2).strip()
            ):
                self.leaf = ""
            return PageLine(written, "maths", rest=rest)
        marker = _MARKER.match(rest)
        if (
            marker is not None
            and not deep
            and marker.group(2)[0] == self.opening[0]
            and len(marker.group(2)) >= len(self.opening)
            and not marker.group(3).strip()
        ):
            self.leaf = ""
            return PageLine(written, "close", indent=self.indent, rest=rest)
        inner = rest + written[len(text) :]
        return PageLine(written, "body", indent=self.indent, inner=inner, rest=rest)

    def _close_to(self, kept: int) -> None:
        """Close the containers past the first *kept*, and the asides they held."""
        del self.held[kept:]
        self.asides = [aside for aside in self.asides if aside[1] <= kept]

    def _opening(
        self, index: int, written: str, rest: str, column: int, matched: int
    ) -> PageLine:
        """A line that nothing concrete holds: what it opens, or the paragraph it carries on."""
        paragraph = self.leaf == "paragraph" and all(
            around <= matched for _, around, _ in self.asides
        )
        strict = (paragraph or self.leaf == "indented") and matched == len(self.held)
        opened = self.item = False
        while not (self.markdown and _blank_columns(rest, column) >= _CODE_INDENT):
            container = self._container(rest, column, strict=strict)
            if container is None:
                break
            if not opened:
                self._close_to(matched)
                self.leaf = ""
                opened, paragraph = True, False
            rest, column, held, self.fresh = container
            self.item = held != _QUOTATION
            self.held.append(held)
            matched = len(self.held)
        if not rest.strip(" \t"):
            kept = self.leaf == "indented" and matched == len(self.held)
            self._close_to(matched)
            self.leaf = "indented" if kept else ""
            return PageLine(written, "blank", rest=rest)
        if self.markdown and _blank_columns(rest, column) >= _CODE_INDENT:
            if paragraph:
                return PageLine(written, "text", rest=rest)
            self._close_to(matched)
            self.leaf = "indented"
            return PageLine(written, "indented", rest=rest)
        return self._leaf(index, written, rest, matched, paragraph=paragraph)

    def _container(
        self, rest: str, column: int, *, strict: bool
    ) -> tuple[str, int, int, bool] | None:
        """The container *rest* opens: what it leaves, at which column, itself, whether empty.

        :param strict: Whether a paragraph or indented code stood open above in the
            line's own container, which an ordered marker other than 1 and an empty
            marker do not interrupt, on any container the line opens. The site's
            parser holds indented code open past blank lines, waiting for more of it.
        """
        mark = self._quote_mark(rest, column)
        if mark is not None:
            return mark[0], mark[1], _QUOTATION, False
        body = rest.lstrip(" \t")
        if (strict and _UNDERLINE.match(body)) or _THEMATIC_BREAK.match(body):
            return None
        marker = _ITEM_MARKER.match(body)
        if marker is None:
            return None
        after = body[marker.end() :]
        empty = not after.strip(" \t")
        if strict and (empty or marker.group(1) not in (None, "1")):
            return None
        blanks = _blank_columns(rest, column)
        start = column + blanks + marker.end()
        spaces = _blank_columns(after, start)
        deep = self.markdown and spaces > _MOST_BLANKS_AFTER_MARKER
        padding = 1 if empty or deep else spaces
        left = "" if empty else _past_columns(after, start, padding)
        return left, start + padding, blanks + marker.end() + padding, empty

    def _leaf(
        self, index: int, written: str, rest: str, matched: int, *, paragraph: bool
    ) -> PageLine:
        """What a line with text on it opens past its containers, or the paragraph it continues."""
        body = rest.strip(" \t")
        strict = paragraph and matched == len(self.held)
        role = self._one_line_role(index, body, strict=strict)
        if role is not None:
            self._close_to(matched)
            self.leaf = ""
            return PageLine(written, role, rest=rest)
        opened = self._concrete(written, rest, body, matched, paragraph=paragraph)
        if opened is not None:
            return opened
        if self._table_row(index, body, matched, paragraph=paragraph):
            return PageLine(written, "row", rest=rest)
        if paragraph:
            return PageLine(written, "text", rest=rest)
        self._close_to(matched)
        self.leaf = "paragraph"
        return PageLine(written, "paragraph", rest=rest)

    def _one_line_role(self, index: int, body: str, *, strict: bool) -> str | None:
        """The role of a line that is a block by itself, or ``None``."""
        if strict and _UNDERLINE.match(body):
            return "underline"
        if _ATX_HEADING.match(body) or _THEMATIC_BREAK.match(body):
            return "single"
        if _LEAF_DIRECTIVE.match(body):
            return "single"
        if not self.markdown and body[0] in "<{":
            taken = self._mdx_flow(index, body)
            if taken is not None:
                self.left = taken
                return "single"
        return None

    def _mdx_flow(self, index: int, body: str) -> int | None:
        """How many more lines the tags and expressions *body* opens take.

        ``None`` when text stands beside them, so they are inline ones of a
        paragraph.
        """
        following = [line.rstrip("\r\n") for line in self.lines[index + 1 :]]
        text = "\n".join([body, *following])
        at = 0
        while True:
            reader = _MDX_TAG if text[at] == "<" else _MDX_EXPRESSION
            found = reader.match(text, at)
            if found is None:
                return None
            at = found.end()
            while text[at : at + 1] in (" ", "\t"):
                at += 1
            if text[at : at + 1] in ("", "\n"):
                return text.count("\n", 0, at)
            if text[at] not in "<{":
                return None

    def _concrete(
        self, written: str, rest: str, body: str, matched: int, *, paragraph: bool
    ) -> PageLine | None:
        """The fence, the display block, the aside or the HTML block a line opens, or ``None``."""
        marker = _MARKER.match(rest)
        if marker is not None and not (
            marker.group(2)[0] == "`" and "`" in marker.group(3)
        ):
            self._close_to(matched)
            self.leaf, self.opening = "fence", marker.group(2)
            self.indent = len(marker.group(1))
            return PageLine(
                written, "open", marker.group(3).strip(), self.indent, rest=rest
            )
        display = _DISPLAY.match(rest)
        if display is not None:
            self._close_to(matched)
            self.leaf, self.opening = "maths", display.group(1)
            return PageLine(written, "maths-open", display.group(2).strip(), rest=rest)
        aside = _ASIDE.match(body)
        if aside is not None:
            self._close_to(matched)
            self.leaf = ""
            indent = _blank_columns(rest, 0)
            self.asides.append((len(aside.group(1)), len(self.held), indent))
            return PageLine(written, "single", rest=rest)
        if not self.markdown:
            return None
        return self._html(written, rest, body, matched, paragraph=paragraph)

    def _html(
        self, written: str, rest: str, body: str, matched: int, *, paragraph: bool
    ) -> PageLine | None:
        """The raw HTML block a line of a ``.md`` page opens, or ``None``."""
        for opens, ends in _HTML_BLOCKS:
            if opens.match(body):
                self._close_to(matched)
                self.leaf, self.html_end = "html", ends
                if ends is not None and ends(body):
                    self.leaf = ""
                return PageLine(written, "html", rest=rest)
        lazy = paragraph and matched < len(self.held)
        if (lazy or not paragraph) and _HTML_LONE_TAG.match(body):
            if not lazy:
                self._close_to(matched)
            self.leaf, self.html_end = "html", None
            return PageLine(written, "html", rest=rest)
        return None

    def _table_row(
        self, index: int, body: str, matched: int, *, paragraph: bool
    ) -> bool:
        """Whether a line of text is a row of a table: the open one's, or a new one's head."""
        if self.leaf == "table" and matched == len(self.held):
            return True
        if not paragraph:
            self._close_to(matched)
        if index + 1 >= len(self.lines) or body == "|":
            return False
        following = self.lines[index + 1].rstrip("\r\n")
        rest, column, held = self._past_held(following, len(self.held))
        delimiter = rest.strip(" \t")
        if (
            held != len(self.held)
            or (self.markdown and _blank_columns(rest, column) >= _CODE_INDENT)
            or not ("|" in delimiter or ":" in delimiter)
            or not _DELIMITER_ROW.match(delimiter)
            or _ITEM_MARKER.match(delimiter)
            or _cell_count(body) != _cell_count(delimiter)
        ):
            return False
        self.leaf = "table"
        return True


def page_lines(lines: Iterable[str], *, kind: str = "mdx") -> Iterator[PageLine]:
    """Every line of a page with its part in the page, read in one walk.

    :param lines: The lines, with or without their line ends.
    :param kind: ``"md"`` or ``"mdx"``, the page's kind, which decides what
        indentation and a tag mean; a reader that does not know it reads ``"mdx"``.
    """
    walk = _Walk(list(lines), kind)
    for index in range(len(walk.lines)):
        yield walk.read(index)


def code_lines(lines: Iterable[str], *, kind: str = "mdx") -> Iterator[bool]:
    """Whether each line is code: a fence's opening line, its body or its closing line.

    Indented code is code too, on the one kind of page that has it. A fence never
    closed runs to the end of the page or of what holds it, as CommonMark has it.

    :param kind: The page's kind (:func:`page_lines`).
    """
    for line in page_lines(lines, kind=kind):
        yield line.role in _CODE_ROLES


def _dedent(line: str, indent: int) -> str:
    """The line without up to ``indent`` leading blanks."""
    stripped = line.lstrip(" \t")
    return line[min(indent, len(line) - len(stripped)) :]


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


def fences(text: str) -> Iterator[Fence]:
    """Every fenced block of a page, in reading order.

    :param text: The page.
    :return: One :class:`Fence` per block, closed or running to the end.
    """
    start = 0
    info = ""
    body: list[str] = []
    for number, line in enumerate(page_lines(text.splitlines(keepends=True)), start=1):
        if line.role == "body":
            body.append(_dedent(line.inner, line.indent))
            continue
        if start:
            yield Fence(start, info, "".join(body))
            start = 0
        if line.role == "open":
            start, info, body = number, line.info, []
    if start:
        yield Fence(start, info, "".join(body))


def display_math_parts(lines: Iterable[str], *, kind: str = "mdx") -> list[str]:
    """Each line's part in display maths: ``"open"``, ``"maths"`` or ``"prose"``.

    ``"maths"`` is a line of the formula or the line that closes it: a run of
    dollar signs at least as long as the opening one, with nothing after it but
    blanks. A line of code opens nothing, and a block never closed runs to the
    end of the page or of what holds it, as remark-math has it. The block opens
    on such a line wherever it stands, in the middle of a paragraph too, even
    one that leaves a code span open: the structure of the blocks comes before
    the spans inside them (CommonMark 0.31.2, 6).

    :param lines: The lines of a page, its frontmatter out.
    :param kind: The page's kind (:func:`page_lines`).
    """
    return [
        _MATHS_ROLES.get(line.role, "prose") for line in page_lines(lines, kind=kind)
    ]


def python_fences(text: str) -> list[str]:
    """The bodies of a page's Python fences, in reading order.

    A fence is Python when the first word of its info string is ``python``,
    whatever attributes follow it.
    """
    return [fence.body for fence in fences(text) if fence.language == "python"]
