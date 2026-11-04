#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where the inline code and maths spans of a page open and close.

``scripts/markdown_spans.py`` is the reading the prose checks step over
inline code with, and the maths too where they do. The cases are the ones
where an escape decides: a backslash before an opening run shows the
character and opens nothing, and one inside a span escapes nothing, so a
span still closes on a run behind it. Each reader that went its own way
before took the first for a span and hid the prose after it, or ran the
second past its closing run.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from markdown_fences import page_lines
from markdown_spans import (
    SPAN_MARK,
    blank_inline_spans,
    block_starts,
    drop_inline_spans,
    drop_inline_spans_by_block,
    inline_spans,
    lines_read_whole,
    replace_inline_spans_by_block,
)


def _spans(text: str, markers: str = "`") -> list[str]:
    return [text[start:end] for start, end in inline_spans(text, markers)]


@pytest.mark.parametrize(
    ("text", "markers", "spans"),
    [
        pytest.param("a `x` b", "`", ["`x`"], id="a code span"),
        pytest.param("a ``x ` y`` b", "`", ["``x ` y``"], id="a longer run"),
        pytest.param("a `` x ` b", "`", [], id="a run no later run matches"),
        pytest.param(r"a \`x -- y\` b", "`", [], id="escaped backticks are text"),
        pytest.param(
            r"\``x` and `y`", "`", ["`x`", "`y`"], id="an escaped tick shortens a run"
        ),
        pytest.param(
            r"a \\`x` b", "`", ["`x`"], id="an escaped backslash escapes no tick"
        ),
        pytest.param(
            r"`%APPDATA%\phonometry\` on Windows",
            "`",
            [r"`%APPDATA%\phonometry\`"],
            id="a backslash in a span escapes nothing",
        ),
        pytest.param(
            r"`\\` ends a row", "`", [r"`\\`"], id="two backslashes in a span"
        ),
        pytest.param("$x$ and `y`", "`", ["`y`"], id="dollars are text to code alone"),
        pytest.param("$x$ and `y`", "`$", ["$x$", "`y`"], id="maths and code"),
        pytest.param(r"\$5 -- \$10", "`$", [], id="escaped dollars are text"),
        pytest.param(
            r"$a\$ -- b$", "`$", [r"$a\$"], id="a maths span closes behind a backslash"
        ),
        pytest.param("`$x` then $`y$`", "`$", ["`$x`", "$`y$"], id="the first opens"),
        pytest.param(
            "$a$$b$", "`$", ["$a$$b$"], id="a run of two closes no run of one"
        ),
    ],
)
def test_a_span_is_read_as_the_site_reads_it(
    text: str, markers: str, spans: list[str]
) -> None:
    assert _spans(text, markers) == spans


def test_blanking_keeps_every_column_and_line() -> None:
    text = "a `x\ny` b \\`c -- d\\`"
    blanked = blank_inline_spans(text)
    assert blanked == "a   \n   b \\`c -- d\\`"
    assert len(blanked) == len(text)


def test_dropping_takes_the_spans_out() -> None:
    assert drop_inline_spans("a `x` b `y`") == f"a {SPAN_MARK} b {SPAN_MARK}"
    assert drop_inline_spans(r"a \`x -- y\` b") == r"a \`x -- y\` b"


def test_a_replacement_is_handed_each_span_whole_opening_run_first() -> None:
    """A reader can tell a maths span from a code span by its first character.

    A backslash before an opening run escapes its first character alone, so
    the span handed over starts on the run's second one, still the marker.
    """
    handed: list[str] = []

    def keep(span: str) -> str:
        handed.append(span)
        return span[0] + "\n" * span.count("\n")

    text = "a `x` $y\nz$ \\$$w$\n\n- one `p\n- two` q"
    assert replace_inline_spans_by_block(text, keep, "`$") == (
        "a ` $\n \\$$\n\n- one `p\n- two` q"
    )
    assert handed == ["`x`", "$y\nz$", "$w$"]


@pytest.mark.parametrize(
    ("text", "joined"),
    [
        pytest.param("!``x``[alt](a.png)", "![", id="a figure"),
        pytest.param("&`x`mdash;", "&mdash;", id="an entity"),
        pytest.param("x_`c`\\sqrt", "_\\sqrt", id="a subscript"),
        pytest.param("$`x`$", "$$", id="a display delimiter"),
    ],
)
def test_the_text_either_side_of_a_span_stays_apart(text: str, joined: str) -> None:
    """A span taken out leaves a mark no check reads, never the two sides joined.

    The sides of a dropped span were joined, so ``!``x``[alt](a.png)`` read
    as a figure, ``&`x`mdash;`` as the entity of an em dash and ``$`x`$`` as
    a display delimiter, none of which the page shows.
    """
    assert joined not in drop_inline_spans(text)


@pytest.mark.parametrize(
    ("text", "shown"),
    [
        pytest.param(
            "> Run `python\n> --version` here.",
            f"> Run {SPAN_MARK}\n here.",
            id="over the lines of a quotation",
        ),
        pytest.param(
            "> - Run `python\n>   --version` here.",
            f"> - Run {SPAN_MARK}\n here.",
            id="over the lines of a list item in a quotation",
        ),
        pytest.param(
            "> Run `python\n--version` here.",
            f"> Run {SPAN_MARK}\n here.",
            id="onto a lazy line",
        ),
        pytest.param(
            "> > Run `python\n> --version` here.",
            f"> > Run {SPAN_MARK}\n here.",
            id="onto a lazy line of a nested quotation",
        ),
        pytest.param(
            "> Run\nlazily\n> `python\n> --version` here.",
            f"> Run\nlazily\n> {SPAN_MARK}\n here.",
            id="past a lazy line",
        ),
    ],
)
def test_a_span_wraps_inside_a_quotation(text: str, shown: str) -> None:
    """A quotation's marks are not its text, so its paragraph reads as one.

    Each line that opened with ``>`` was read as a block of its own, so the
    two backticks of a span the quotation wraps never paired.
    """
    assert drop_inline_spans_by_block(text) == shown


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("> Run `python\n>\n> --version` here.", id="a blank line of it"),
        pytest.param("> - Run `python\n> - --version` here.", id="two items in it"),
        pytest.param("> Run `python\n> > --version` here.", id="a deeper quotation"),
        pytest.param("> # Run `python\n> --version` here.", id="a heading in it"),
        pytest.param(
            "> | Run `python |\n> |---|\n> --version` here.", id="a table row in it"
        ),
        pytest.param("Run `python\n> --version` here.", id="a quotation that opens"),
        pytest.param("- Run `python\n> --version` here.", id="after a list item"),
        pytest.param("- Run `python\n- --version` here.", id="two list items"),
    ],
)
def test_a_span_stays_inside_the_paragraph_of_a_quotation(text: str) -> None:
    """Each of these is two blocks to the site, so the two backticks stay apart."""
    assert drop_inline_spans_by_block(text) == text


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("a `b\n---\nc` d", id="a rule of hyphens"),
        pytest.param("a `b\n***\nc` d", id="a rule of asterisks"),
        pytest.param("a `b\n___\nc` d", id="a rule of underscores"),
        pytest.param("a `b\n* * *\nc` d", id="a spaced rule"),
        pytest.param("a `b\n- - -\nc` d", id="a spaced rule of hyphens"),
        pytest.param("a `b\n===\nc` d", id="a setext underline"),
        pytest.param("a `b\n-\nc` d", id="an underline of one hyphen"),
        pytest.param("a `b\n--\nc` d", id="an underline of two hyphens"),
        pytest.param("> a `b\n> ---\n> c` d", id="a rule of a quotation"),
        pytest.param("> a `b\n> ===\n> c` d", id="an underline of a quotation"),
        pytest.param("- a `b\n  ---\n  c` d", id="a rule of a list item"),
        pytest.param("a `b\n$$\nc` d", id="a display fence"),
        pytest.param("a `b\n$$ meta\nc` d", id="a display fence with a meta"),
        pytest.param("> a `b\n> $$\n> c` d", id="a display fence of a quotation"),
        pytest.param("a `b\n<!-- x -->\nc` d", id="a comment"),
        pytest.param("> a `b\n> <!-- x -->\n> c` d", id="a comment of a quotation"),
        pytest.param("- a `b\n    - c` d", id="an item nested four columns in"),
        pytest.param("1. a `b\n    - c` d", id="an item under a numbered one"),
        pytest.param("> - a `b\n>     - c` d", id="a nested item of a quotation"),
        pytest.param("- a `b\n    ## c` d", id="a heading under an item"),
        pytest.param("- a\n\n  b `c\n    - d` e", id="under a paragraph of an item"),
        pytest.param("- a\n  - b `c\n      - d` e", id="three levels down"),
        pytest.param("- a\nb `c\n    - d` e", id="under a lazy line of an item"),
        pytest.param(
            "> - a\n>\n>   b `c\n>     - d` e", id="past a bare mark of a quotation"
        ),
        pytest.param("---\nkey: a `b\n---\nc` d", id="the fence of a frontmatter"),
        pytest.param("- # h `b\nc` d", id="a heading on an item's first line"),
        pytest.param("- ## h `b\n  c` d", id="a heading the item goes on after"),
        pytest.param("1. # h `b\n   c` d", id="a heading on a numbered item"),
        pytest.param("> - # h `b\n> c` d", id="a heading on an item of a quotation"),
        pytest.param("- <!-- y --> `b\n  c` d", id="a comment on an item's first line"),
        pytest.param("a `b\n<div>\nc` d", id="a block tag"),
        pytest.param("a `b\n</div>\nc` d", id="a closing block tag"),
        pytest.param("a `b\n<details>\nc` d", id="a details tag"),
        pytest.param("a `b\n<script>\nc` d", id="a script tag"),
        pytest.param("a `b\n<pre>\nc` d", id="a pre tag"),
        pytest.param("a `b\n<?php\nc` d", id="a processing instruction"),
        pytest.param("a `b\n<!x\nc` d", id="a declaration"),
        pytest.param("a `b\n<![CDATA[\nc` d", id="a CDATA section"),
        pytest.param("> a `b\n> <div>\n> c` d", id="a block tag of a quotation"),
        pytest.param("-\ta `b\n    - c` d", id="an item a tab sets the column of"),
        pytest.param("-\ta `b\n\t- c` d", id="a nested item behind a tab"),
        pytest.param("a `b\n| c |\n|---|\nd` e", id="the head of a table"),
        pytest.param("a `b\nc | d\n--|--\ne` f", id="a head with no outer pipes"),
        pytest.param("a `b\nc\n:--\nd` e", id="a head over a colon"),
        pytest.param("| a `b |\n|---|\n| c` d |", id="two rows of a table"),
        pytest.param("| a |\n|---|\nb `c\nd` e", id="two rows with no pipes"),
        pytest.param("| `a | b` |\n|---|---|", id="two cells of a row"),
        pytest.param("a `b\n:::note\nc` d\n:::", id="an aside"),
        pytest.param(":::note\na `b\n:::\nc` d", id="the end of an aside"),
        pytest.param("a `b\n::x\nc` d", id="a leaf directive"),
        pytest.param("    a `b\nc` d", id="indented code"),
    ],
)
def test_a_span_stops_at_a_line_that_ends_the_paragraph(text: str) -> None:
    """Each of these is two blocks to the site, so the two backticks stay apart.

    The reader took all of them for a line of the paragraph: a rule, a setext
    underline, a display fence, a comment and an item nested past three columns.
    A block on an item's first line went unread behind the marker, as did all but
    one of the raw HTML blocks, which end a paragraph as a comment does.
    """
    assert drop_inline_spans_by_block(text) == text


@pytest.mark.parametrize(
    ("text", "shown"),
    [
        pytest.param("a `b\n$$x$$\nc` d", f"a {SPAN_MARK}\n\n d", id="inline maths"),
        pytest.param(
            "a `b\n----x\nc` d", f"a {SPAN_MARK}\n\n d", id="hyphens and text"
        ),
        pytest.param("a `b\n<span>\nc` d", f"a {SPAN_MARK}\n\n d", id="an inline tag"),
        pytest.param("  a `b\n    - c` d", f"  a {SPAN_MARK}\n d", id="no item above"),
        pytest.param("- a `b\n      - c` d", f"- a {SPAN_MARK}\n d", id="too deep"),
        pytest.param("- a `b\n  c` d", f"- a {SPAN_MARK}\n d", id="a wrapped item"),
        pytest.param(
            "- a\n\nb `c\n    - d` e", f"- a\n\nb {SPAN_MARK}\n e", id="out of the item"
        ),
        pytest.param("> a `b\n===\nc` d", f"> a {SPAN_MARK}\n\n d", id="a lazy ==="),
        pytest.param("> a `b\n=\nc` d", f"> a {SPAN_MARK}\n\n d", id="a lazy ="),
        pytest.param("> a `b\n--\nc` d", f"> a {SPAN_MARK}\n\n d", id="a lazy --"),
        pytest.param(
            "- a `b\n===\nc` d", f"- a {SPAN_MARK}\n\n d", id="out of an item"
        ),
        pytest.param(
            "1. a `b\n===\nc` d",
            f"1. a {SPAN_MARK}\n\n d",
            id="out of a numbered item",
        ),
        pytest.param(
            "> > a `b\n> ===\n> c` d",
            f"> > a {SPAN_MARK}\n\n d",
            id="a shallower mark",
        ),
        pytest.param(
            "- > a `b\n  ===\n  c` d",
            f"- > a {SPAN_MARK}\n\n d",
            id="in the item only",
        ),
        pytest.param("a `b\n2. c` d", f"a {SPAN_MARK}\n d", id="an ordered marker"),
        pytest.param(
            "- a `b\n    2. c` d", f"- a {SPAN_MARK}\n d", id="an ordered marker in it"
        ),
        pytest.param("a `b\n* \nc` d", f"a {SPAN_MARK}\n\n d", id="an empty marker"),
        pytest.param("a `b\n| c` d", f"a {SPAN_MARK}\n d", id="a lone pipe"),
        pytest.param("- a `b\n    | c` d", f"- a {SPAN_MARK}\n d", id="a pipe in it"),
        pytest.param("| a `b\nc` d", f"| a {SPAN_MARK}\n d", id="a pipe that opens it"),
        pytest.param(
            "> | Run `python |\n> --version` here.",
            f"> | Run {SPAN_MARK}\n here.",
            id="a pipe of a quotation",
        ),
        pytest.param("a `b\n:::\nc` d", f"a {SPAN_MARK}\n\n d", id="no aside to close"),
        pytest.param(
            "a `b\n:::x y\nc` d", f"a {SPAN_MARK}\n\n d", id="no aside to open"
        ),
        pytest.param(
            "a `b\n</span>\nc` d", f"a {SPAN_MARK}\n\n d", id="a closing inline tag"
        ),
    ],
)
def test_a_span_still_runs_over_a_line_of_its_paragraph(text: str, shown: str) -> None:
    """The site reads each of these as a line of the paragraph, so a span crosses.

    An underline is never lazy, and a pipe with no delimiter row under it, an
    ordered marker other than 1 and an empty marker do not interrupt a paragraph.
    """
    assert drop_inline_spans_by_block(text) == shown


@pytest.mark.parametrize(
    ("text", "shown_md", "shown_mdx"),
    [
        pytest.param(
            "a `b\n<A />\nc` d",
            f"a {SPAN_MARK}\n\n d",
            "a `b\n<A />\nc` d",
            id="a tag alone ends a paragraph of a component page",
        ),
        pytest.param(
            "a `b\n    - c` d",
            f"a {SPAN_MARK}\n d",
            "a `b\n    - c` d",
            id="any indentation opens an item there",
        ),
        pytest.param(
            "a `b\n{x}\nc` d",
            f"a {SPAN_MARK}\n\n d",
            "a `b\n{x}\nc` d",
            id="and an expression alone ends one",
        ),
        pytest.param(
            "<div>\n`a`\n</div>",
            "<div>\n`a`\n</div>",
            f"<div>\n{SPAN_MARK}\n</div>",
            id="a raw HTML block holds no span",
        ),
    ],
)
def test_the_kind_of_a_page_says_where_a_span_stops(
    text: str, shown_md: str, shown_mdx: str
) -> None:
    """A ``.md`` page has raw HTML and indented code; an ``.mdx`` page has neither."""
    assert drop_inline_spans_by_block(text, kind="md") == shown_md
    assert drop_inline_spans_by_block(text, kind="mdx") == shown_mdx
    assert drop_inline_spans_by_block(text, comments="mdx") == shown_mdx


def test_a_line_of_code_is_not_read_for_a_span() -> None:
    """A span pairs on no line of a fence, handed over with its fence or not."""
    text = "a `b\n```\nc` d\n```\ne` f"
    assert drop_inline_spans_by_block(text) == text


def test_a_blanked_page_reads_by_the_walk_of_the_page_as_written() -> None:
    """A line blanked is no line the walk can read: it took its container along."""
    written = ["- ```", "  x", "  ```", "  a `b", "    - c` d"]
    blanked = ["", "", "", *written[3:]]
    text = "\n".join(blanked)
    assert drop_inline_spans_by_block(text) != text
    assert (
        replace_inline_spans_by_block(
            text, lambda span: span, walked=list(page_lines(written, kind="md"))
        )
        == text
    )


def test_the_lines_that_open_a_block_are_the_ones_the_spans_stop_at() -> None:
    lines = ["a", "b", "", "- c", "  d", "- e", "> f", "> g", ">", "> h", "# i", "j"]
    opening = [
        True,
        False,
        True,
        True,
        False,
        True,
        True,
        False,
        True,
        True,
        True,
        True,
    ]
    assert block_starts(lines) == opening
    assert block_starts([]) == []


def test_each_line_of_a_raw_html_block_opens_a_block() -> None:
    """Nothing there is markup, so no state is carried from one line to the next."""
    assert block_starts(["<div>", "a", "b", "", "c", "d"]) == [
        True,
        True,
        True,
        True,
        True,
        False,
    ]


def test_lines_read_whole_give_back_a_line_for_each_line() -> None:
    """No lines give none back: joined, they were the empty text, which split
    back into one empty line, and every reader that zipped that against the
    page's own lines raised a ``ValueError`` on an empty page.
    """
    assert lines_read_whole([], drop_inline_spans_by_block) == []
    assert lines_read_whole([""], drop_inline_spans_by_block) == [""]
    assert lines_read_whole(["a `b", "c` d"], drop_inline_spans_by_block) == [
        f"a {SPAN_MARK}",
        " d",
    ]


def test_a_reader_that_moves_a_line_break_is_refused() -> None:
    with pytest.raises(ValueError, match="2 lines came back as 1"):
        lines_read_whole(["a", "b"], lambda text: text.replace("\n", " "))
