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

import json
import pathlib
import re
import sys

import node_script
import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from markdown_fences import page_lines
from markdown_spans import (
    SPAN_MARK,
    blank_inline_spans,
    blank_inline_spans_by_block,
    block_starts,
    drop_inline_spans,
    drop_inline_spans_by_block,
    inline_spans,
    inside_quotation,
    lines_read_whole,
    page_markup,
    quote_depth,
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


@pytest.mark.parametrize(
    ("line", "kind", "depth", "inside"),
    [
        ("> > x", "md", 2, "x"),
        (">\t> x", "md", 2, "x"),
        ("> \t> x", "md", 2, "x"),
        (">\tx", "md", 1, "  x"),
        ("   >    > x", "md", 2, "x"),
        (">     > x", "md", 1, "    > x"),
        (">     > x", "mdx", 2, "x"),
        (">\t\t> x", "md", 1, "  \t> x"),
        (">\t\t> x", "mdx", 2, "x"),
        ("    > x", "md", 0, "    > x"),
        ("x > y", "md", 0, "x > y"),
    ],
)
def test_the_marks_of_a_quotation_are_read_by_their_columns(
    line: str, kind: str, depth: int, inside: str
) -> None:
    """A tab stands for the columns to its stop: one after a mark is the
    mark's blank, the rest stay as spaces, and a mark may stand up to three
    columns past the one before it on a ``.md`` page, where four open
    indented code, and any number on an ``.mdx`` page, which has none
    (CommonMark 0.31.2, 2.2 and 5.1). The walk of the page reads them so.
    """
    assert (quote_depth(line, kind=kind), inside_quotation(line, kind=kind)) == (
        depth,
        inside,
    )


#: The tag each case of the page markup writes, in a place that renders it or not.
_TAG = '<Video name="a" />'


@pytest.mark.parametrize(
    ("page", "kind"),
    [
        pytest.param(f"---\ndescription: '{_TAG}'\n---\n", "mdx", id="frontmatter"),
        pytest.param(f"```mdx\n{_TAG}\n```\n", "mdx", id="a fence of backticks"),
        pytest.param(f"~~~\n{_TAG}\n~~~\n", "mdx", id="a fence of tildes"),
        pytest.param(
            f"- item\n\n  ```\n  {_TAG}\n  ```\n", "mdx", id="a fence in a list item"
        ),
        pytest.param(f"Embed it with `{_TAG}` here.\n", "mdx", id="a code span"),
        pytest.param(
            f"Embed it with\n`{_TAG}`\nhere.\n", "mdx", id="a code span on its own line"
        ),
        pytest.param(f"{{/* {_TAG} */}}\n", "mdx", id="an MDX comment"),
        pytest.param(f"{{/*\n{_TAG}\n*/}}\n", "mdx", id="an MDX comment over lines"),
        pytest.param(f"$$\n{_TAG}\n$$\n", "mdx", id="display maths"),
        pytest.param(f"<!-- {_TAG} -->\n", "md", id="an HTML comment"),
        pytest.param(f"Text.\n\n    {_TAG}\n", "md", id="indented code"),
        pytest.param(f"Write \\{_TAG} here.\n", "mdx", id="an escaped tag"),
        pytest.param(f"Write \\{_TAG} here.\n", "md", id="an escaped tag on a md page"),
        pytest.param(
            f"<code>{{'{_TAG}'}}</code>\n", "mdx", id="a string in an expression"
        ),
        pytest.param(
            f"Text {{'{_TAG}'}} here.\n", "mdx", id="an expression in a paragraph"
        ),
        pytest.param(
            f"\n---\ndescription: '{_TAG}'\n---\n",
            "mdx",
            id="frontmatter after a blank line",
        ),
        pytest.param(
            f"\n \n---\ndescription: '{_TAG}'\n---\n",
            "mdx",
            id="frontmatter after blank lines",
        ),
        pytest.param(
            f"﻿---\ndescription: '{_TAG}'\n---\n",
            "mdx",
            id="frontmatter after a byte order mark",
        ),
        pytest.param(
            f"+++\ndescription = '{_TAG}'\n+++\n", "mdx", id="TOML frontmatter"
        ),
    ],
)
def test_a_tag_the_page_does_not_render_is_blanked(page: str, kind: str) -> None:
    """A tag quoted in code, a comment, maths or the frontmatter is gone, the lines kept."""
    shown = page_markup(page, kind=kind)
    assert "<Video" not in shown
    assert shown.count("\n") == page.count("\n")


@pytest.mark.parametrize(
    ("page", "kind"),
    [
        pytest.param(f"Text.\n\n{_TAG}\n", "mdx", id="a tag alone"),
        pytest.param('<Video\n  name="a"\n/>\n', "mdx", id="a tag over lines"),
        pytest.param(
            f"A clip, {_TAG}, in a paragraph.\n", "mdx", id="a tag in a paragraph"
        ),
        pytest.param(
            f"---\ntitle: A\n---\n\n{_TAG}\n", "mdx", id="a tag after the frontmatter"
        ),
        pytest.param(
            f"Use `code` and then\n{_TAG}\n", "mdx", id="a tag after a code span"
        ),
        pytest.param(f"Text.\n\n    {_TAG}\n", "mdx", id="indented on an mdx page"),
        pytest.param(
            f"Write \\\\{_TAG} here.\n", "mdx", id="behind an escaped backslash"
        ),
    ],
)
def test_a_tag_the_page_renders_stands_where_it_is_written(
    page: str, kind: str
) -> None:
    shown = page_markup(page, kind=kind)
    assert [line.find("<Video") for line in shown.split("\n")] == [
        line.find("<Video") for line in page.split("\n")
    ]


@pytest.mark.parametrize(
    ("tag", "kind"),
    [
        pytest.param(
            '<Video alt="from $20" name="a" caption="to $30" />',
            "mdx",
            id="two dollar signs among its attributes",
        ),
        pytest.param(
            '<Video alt="a `b" name="a" caption="c` d" />',
            "mdx",
            id="two backticks among its attributes",
        ),
        pytest.param(
            '<Video\n  alt="from $20" name="a" caption="to $30"\n/>',
            "mdx",
            id="dollar signs on a line of a tag over lines",
        ),
        pytest.param(
            '<Video name="a" caption={`a ${b}`} />',
            "mdx",
            id="a template literal in an expression of its own",
        ),
        pytest.param(
            '<span title="a `b">c</span> and `d`',
            "md",
            id="a raw HTML tag on a md page",
        ),
    ],
)
def test_a_tag_the_page_renders_is_read_whole(tag: str, kind: str) -> None:
    """No span or expression opens inside a tag the page renders: what it
    holds between its quotes is its own, as the site's parser reads it.
    """
    page = f"Text.\n\n{tag}\n"
    shown = page_markup(page, kind=kind)
    opened = tag.split(" and ")[0]
    assert opened in shown, shown


def test_what_opens_first_wins_between_a_tag_a_span_and_an_expression() -> None:
    """A span written before a tag holds the tag, a tag holds what it writes,
    and the spans and expressions after it are read again from its end.
    """
    written = [
        ('`<Video name="a" />`', False),
        (" ", True),
        ('<Video alt="`" name="b" />', True),
        (" ", True),
        ("{x}", False),
        (" ", True),
        ("`c`", False),
        (" ", True),
        ("\\$", False),
        ("d ", True),
        ("$e$", False),
        ("\n", True),
    ]
    page = "".join(piece for piece, _ in written)
    shown = "".join(piece if kept else " " * len(piece) for piece, kept in written)
    assert page_markup(page) == shown


def test_a_frontmatter_that_never_closes_is_read_as_the_page() -> None:
    page = f"---\n{_TAG}\n"
    assert page_markup(page) == page


_SITE_READER = _ROOT / "site" / "scripts" / "shared" / "markdown-spans.mjs"
#: The shapes where the two languages could part: the cases above, a line end
#: of two characters, a character outside the basic plane in what is blanked,
#: and a tag in a row of a table.
_MARKUP_CASES = (
    f"Write \\{_TAG} here.\n",
    f"Write \\\\{_TAG} here.\n",
    f"<code>{{'{_TAG}'}}</code>\n",
    f"\ufeff---\ndescription: '{_TAG}'\n---\n",
    f"\n \n---\ndescription: '{_TAG}'\n---\n",
    f"+++\ndescription = '{_TAG}'\n+++\n",
    '<Video alt="from $20" name="a" caption="to $30" />\n',
    '<Video\n  alt="from $20" name="a" caption="to $30"\n/>\n',
    '<Video name="a" caption={`a ${b}`} />\n',
    '<span title="a `b">c</span> and `d`\n',
    'a\r\n`b`\r\n<Video name="a" />\r\n',
    "Text `\U0001d465` and {'\U0001d466'} then $\U0001d467$.\n",
    '| a | <Video name="a" /> |\n|---|---|\n| `b` | {c} |\n',
)


def _in_code_units(text: str, shown: str) -> str:
    """*shown* as JavaScript holds it: a blanked character outside the basic plane
    is one space here and two there, as each language keeps the columns of its
    own strings.

    :param text: The page.
    :param shown: What :func:`page_markup` makes of it.
    """
    return "".join(
        "  " if blanked == " " and ord(char) > 0xFFFF else blanked
        for char, blanked in zip(text, shown, strict=True)
    )


@pytest.mark.whole_tree
@pytest.mark.skipif(
    node_script.NODE is None, reason="no JavaScript engine to compare with"
)
def test_the_site_reads_the_markup_of_every_page_as_the_scripts_do() -> None:
    """``pageMarkup`` of the site and :func:`page_markup` give the same page: every
    page of the site as its own kind, and the cases above as both.
    """
    paths = sorted((_ROOT / "site" / "src" / "content").rglob("*.md*"))
    pages = [
        *((path.read_text(encoding="utf-8"), path.suffix[1:]) for path in paths),
        *((case, kind) for case in _MARKUP_CASES for kind in ("md", "mdx")),
    ]
    script = (
        f"import {{pageMarkup}} from {json.dumps(_SITE_READER.as_uri())};"
        "let input = '';"
        "for await (const chunk of process.stdin) input += chunk;"
        "process.stdout.write(JSON.stringify(JSON.parse(input).map("
        "  ([text, kind]) => pageMarkup(text, {kind}))));"
    )
    javascript = node_script.answer(script, pages, timeout=300)
    differ = [
        f"{kind}: {text[:80]!r}"
        for (text, kind), other in zip(pages, javascript, strict=True)
        if _in_code_units(text, page_markup(text, kind=kind)) != other
    ]
    assert (len(paths) > 400, differ) == (True, [])


#: A URL and an attribute, two constructs of a reader's own that hold what
#: they hold: the em dash check reads a page's addresses this way.
_URL = re.compile(r"[a-z]+://[^\s)>\]]+")
_ATTRIBUTE = re.compile(r"\bhref=\"[^\"]*\"")


@pytest.mark.parametrize(
    ("text", "shown"),
    [
        pytest.param("`http://x` `--y`", " " * 16, id="a URL in a span"),
        pytest.param("http://x`y` z", " " * 12 + "z", id="a span in a URL"),
        pytest.param("`a http://x`y` b", " " * 12 + "y` b", id="a span the URL closes"),
        pytest.param(
            '`href="` x `"`', " " * 8 + " x " + " " * 3, id="an attribute in a span"
        ),
        pytest.param(
            '<a href="`"> x `y`',
            "<a " + " " * 8 + "> x " + " " * 3,
            id="a span in an attribute",
        ),
        pytest.param(
            "a\n\nhttp://x`y\n\n`b` c", "a\n\n" + " " * 10 + "\n\n    c", id="by block"
        ),
    ],
)
def test_a_construct_read_with_the_spans_wins_where_it_opens_first(
    text: str, shown: str
) -> None:
    """A reader's own constructs and the spans are read in one pass, left to right.

    Whichever opens first holds what it spans: a URL written in a code span is
    code, and a backtick inside a URL opens no span. Read one after the other,
    a URL took the backtick that closed its span and every span after it
    paired with the wrong run.
    """
    assert blank_inline_spans_by_block(text, constructs=(_URL, _ATTRIBUTE)) == shown


def test_a_construct_is_read_in_a_raw_html_block_too() -> None:
    """A raw HTML block holds no span, but what a reader reads there is read."""
    text = '<div href="a--b">\n`x`\n</div>'
    shown = "<div " + " " * len('href="a--b"') + ">\n`x`\n</div>"
    assert blank_inline_spans_by_block(text, constructs=(_ATTRIBUTE,)) == shown


@pytest.mark.parametrize(
    ("text", "shown"),
    [
        pytest.param("a { /* b */ } c", f"a {SPAN_MARK} c", id="blanks around it"),
        pytest.param(
            "{ /*\nb\n\nc\n*/ }\nd",
            f"{SPAN_MARK}\n\n\n\n\nd",
            id="over a blank line",
        ),
    ],
)
def test_an_mdx_comment_may_stand_between_blanks_in_its_braces(
    text: str, shown: str
) -> None:
    """MDX shows nothing of an expression that holds only a comment, blanks and all."""
    assert drop_inline_spans_by_block(text, comments="mdx") == shown
