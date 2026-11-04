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

from markdown_spans import (
    SPAN_MARK,
    blank_inline_spans,
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
        pytest.param("> | Run `python |\n> --version` here.", id="a table row in it"),
        pytest.param("Run `python\n> --version` here.", id="a quotation that opens"),
        pytest.param("- Run `python\n> --version` here.", id="after a list item"),
        pytest.param("- Run `python\n- --version` here.", id="two list items"),
    ],
)
def test_a_span_stays_inside_the_paragraph_of_a_quotation(text: str) -> None:
    """Each of these is two blocks to the site, so the two backticks stay apart."""
    assert drop_inline_spans_by_block(text) == text


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
