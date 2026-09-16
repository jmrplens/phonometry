#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The em dash gate, held against the two things it has to tell apart.

``scripts/check_em_dashes.py`` refuses an em dash in the prose the project
publishes, and exempts the dash a citation reproduces, because ISO, IEC, EN
and DIN print their titles with one. The line between the two is where this
gate can go wrong in both directions: too strict and the registry of errata
cannot quote the page it is reporting, too loose and a dash walks back into
the prose behind a stray quotation mark.

The case that first got through was a quotation the paragraph wraps: the
opening mark on one line, the closing one two lines below, and the dash of
the quoted title in between, where a line-scoped match sees an opening mark
and no closing one and calls the dash prose. The tests below fix that reading
together with the readings that must not move: an attribute value and a YAML
value are the page's own prose and are scanned, a quotation that never closes
stops at the end of its paragraph, and everything the gate caught before it
learned about wrapping it still catches.
"""

from __future__ import annotations

import pathlib
import sys

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_em_dashes as ced


def test_prose_dash_is_refused() -> None:
    assert ced.markdown_hits("The level rises — and then falls.\n") == [1]


def test_dash_outside_a_quotation_closed_on_the_same_line_is_refused() -> None:
    text = 'He read "Table 1 — Maximum" aloud — and stopped.\n'
    assert ced.markdown_hits(text) == [1]


def test_dash_inside_a_quotation_wrapped_over_lines_is_exempt() -> None:
    """The reading that the line-scoped match could not reach.

    ISO 3382-1 prints its Table 1 caption with a dash, and the errata entry
    that reports the table quotes the caption whole, so the quotation opens
    on one line and closes on the next.
    """
    text = (
        'The caption reads "Table 1 — Maximum deviation\n'
        'of directivity of source in decibels".\n'
    )
    assert ced.markdown_hits(text) == []


def test_dash_after_a_wrapped_quotation_has_closed_is_refused() -> None:
    text = (
        'The caption reads "Table 1 — Maximum deviation\n'
        'of directivity" and the annex — wrongly — calls it a floor.\n'
    )
    assert ced.markdown_hits(text) == [2]


def test_dash_inside_wrapped_guillemets_is_exempt() -> None:
    text = "El pie reza «Table 1 — Maximum deviation\nof directivity of source».\n"
    assert ced.markdown_hits(text) == []


def test_dash_after_wrapped_guillemets_have_closed_is_refused() -> None:
    text = "El pie reza «Table 1 — Maximum\ndeviation» y el anexo — mal — lo llama suelo.\n"
    assert ced.markdown_hits(text) == [2]


def test_dash_in_an_alt_attribute_is_the_pages_own_prose() -> None:
    """Alt text is read aloud to a reader, so the house style governs it."""
    assert ced.markdown_hits(
        '<img alt="A curve — and its tolerance" src="a.svg" />\n'
    ) == [1]


def test_an_attribute_value_does_not_open_a_quotation() -> None:
    """The closing quote of an attribute must not be read as an opening one.

    Reading it as one would carry an open quotation over the rest of the
    paragraph and exempt every dash in it.
    """
    text = '<img alt="curve" src="a.svg" />\nThe level rises — and falls.\n'
    assert ced.markdown_hits(text) == [2]


def test_dash_in_a_yaml_description_is_the_pages_own_prose() -> None:
    assert ced.markdown_hits('description: "A guide — with a dash"\n') == [1]


def test_dash_in_a_frontmatter_title_is_a_reproduced_title() -> None:
    assert ced.markdown_hits("title: Acoustics — Part 2\n") == []


def test_dash_in_a_code_span_is_data() -> None:
    assert ced.markdown_hits("Call `a — b` here.\n") == []


def test_dash_in_a_fenced_block_is_data() -> None:
    assert ced.markdown_hits("```\na — b\n```\n") == []


def test_dash_alone_in_a_table_cell_is_an_empty_cell() -> None:
    assert ced.markdown_hits("| a | — | b |\n") == []


def test_an_unclosed_quotation_stops_at_the_end_of_its_paragraph() -> None:
    """A quotation mark with no partner must not silence the whole page."""
    text = 'He said "Table 1 — Maximum\n\nThe level rises — and falls.\n'
    assert ced.markdown_hits(text) == [3]


def test_dash_in_a_docstring_is_refused() -> None:
    assert ced.python_hits('"""The level rises — and falls."""\n') == [1]


def test_dash_in_a_reproduced_title_in_a_docstring_is_exempt() -> None:
    assert ced.python_hits('"""Cites "Acoustics — Part 2: rooms"."""\n') == []


def test_a_title_in_italics_inside_a_sentence_is_exempt() -> None:
    """The citation form: the title is reproduced as the document prints it."""
    text = "EN 12354-5:2009, *Building acoustics — Estimation of levels*, gives\n"
    assert ced.markdown_hits(text) == []


def test_a_caption_set_entirely_in_italics_is_not() -> None:
    """The other italics of this corpus: a figure caption, and the house prose."""
    text = "*The gate as a picture rather than an inequality — drawn in the\nISO 9614-1 naming.*\n"
    assert ced.markdown_hits(text) == [1]


def test_a_caption_carries_its_state_to_the_end_of_the_paragraph() -> None:
    """The closing asterisk may be several lines below the dash."""
    text = "*The two routes on one problem,\nand the price of each — which is the\npoint.*\n"
    assert ced.markdown_hits(text) == [2]


def test_bold_and_a_list_bullet_are_not_a_caption() -> None:
    """``**`` opens bold and ``* `` a list item; neither opens an italic span."""
    assert ced.markdown_hits("**Bold** text — and a dash.\n") == [1]
    assert ced.markdown_hits("* A list item — with a dash.\n") == [1]


def test_a_citation_inside_a_caption_still_carries_its_own_dash() -> None:
    """A caption may quote a title, and the title keeps the dash it prints.

    The quotation marks are what say so, which is the rule the guard already
    had; the italics no longer say anything on their own.
    """
    text = '*Read against "Acoustics — Part 2: rooms", the curve is flat.*\n'
    assert ced.markdown_hits(text) == []
