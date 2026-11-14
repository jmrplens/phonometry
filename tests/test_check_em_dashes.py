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
in its paragraph quotes nothing, and everything the gate caught before it learned
about wrapping it still catches.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

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


def test_dash_after_a_fence_shown_inside_another_is_prose() -> None:
    text = "````\n```\na — b\n````\nThe level rises — and falls.\n"
    assert ced.markdown_hits(text) == [5]


def test_dash_alone_in_a_table_cell_is_an_empty_cell() -> None:
    assert ced.markdown_hits("| a | — | b |\n|---|---|---|\n") == []


def test_an_unclosed_quotation_quotes_nothing() -> None:
    """A quotation mark with no partner silences neither the page nor its paragraph."""
    text = 'He said "Table 1 — Maximum\n\nThe level rises — and falls.\n'
    assert ced.markdown_hits(text) == [1, 3]


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


@pytest.mark.parametrize("marks", [">\t> ", "> \t> ", " >\t>\t", ">\t"])
def test_a_caption_behind_marks_parted_by_a_tab_is_a_caption(marks: str) -> None:
    """A tab after a quotation mark is the blank the mark may take, its
    columns past the first left as spaces, and up to three of those columns
    may stand before the next mark (CommonMark 0.31.2, 2.2 and 5.1). The
    caption behind a mark, a tab and a mark is one, and its dash is refused.

    The marks were read with spaces alone between them, so the second mark
    stayed on the line, the line did not open with the caption's ``*`` and
    the caption's dash passed as one of a citation.
    """
    text = f"{marks}*A caption, with a dash \u2014 in it.*\n"
    assert ced.markdown_hits(text) == [1]
    assert ced.markdown_hits(text, mdx=True) == [1]


def test_a_mark_deeper_than_three_columns_is_code_on_a_markdown_page() -> None:
    """On a ``.md`` page, a ``>`` four columns past the blank of the mark
    before it opens indented code inside the quotation, not a quotation, and
    the line is code; an ``.mdx`` page has no indented code, and the same
    ``>`` opens a quotation whose caption's dash is refused.
    """
    text = ">\t\t> *A caption, with a dash \u2014 in it.*\n"
    assert ced.markdown_hits(text) == []
    assert ced.markdown_hits(text, mdx=True) == [1]


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


# Maths: what sits between dollar signs is read by remark-math, not as prose, so
# an asterisk there is a superscript star and a quotation mark a symbol. The
# guard toggled its italic state on every asterisk of the paragraph, and the
# star of $DI_i^*$ and of $F v^*$ opened a span that ran on to the paragraph's
# end, where three dashes of the published guides passed as titles in italics.


def test_an_asterisk_in_math_opens_no_italic_span() -> None:
    """The apparent directivity index, as the sound power guide writes it."""
    text = (
        "$DI_i^*$ is the apparent directivity index, per position\n"
        "*and* per band. A machine does not have a broken array — it has a\n"
        "directivity the positions cannot resolve.\n"
    )
    assert ced.markdown_hits(text) == [2]


def test_an_asterisk_in_math_does_not_run_on_through_a_list() -> None:
    """A list with no blank line between its items is one paragraph to the guard."""
    text = (
        "- Form $\\tfrac{1}{2}\\operatorname{Re}\\{F v^*\\}$ at the drive point.\n"
        "- The band must hold enough modes — which is what the densities are for.\n"
    )
    assert ced.markdown_hits(text) == [2]


def test_an_asterisk_in_a_display_math_block_opens_no_italic_span() -> None:
    text = "$$\nv^* = v_x - i v_y\n$$\nThe level rises — and falls.\n"
    assert ced.markdown_hits(text) == [4]


def test_a_display_math_block_is_maths_whatever_its_lines_start_with() -> None:
    """A line of a ``$$`` block that opens like a block of markdown is still maths.

    remark-math reads the block as flow maths, as a fenced code block is
    read, so a line of it that opens with ``+``, ``-``, ``|``, ``>``, a
    heading mark or ``1.`` starts no list, table, quote or heading. The guard
    read such a line as the start of a new block, the ``$$`` fences never
    paired, and the asterisk or the quotation mark on the line opened a span
    that hid the dash of the prose below.
    """
    for opening in ("+ ", "- ", "|", "> ", "# ", "1. "):
        assert ced.markdown_hits(
            f"$$\nL = a\n{opening}v^* b\n$$\nThe level rises — and falls.\n"
        ) == [5], opening
    modulus = "$$\n|v^*|^2 = 1\n$$\nThe level rises — and falls.\n"
    assert ced.markdown_hits(modulus) == [4]
    ditto = '$$\n+ \\text{"} b\n$$\nThe level rises — and falls.\n'
    assert ced.markdown_hits(ditto) == [4]


def test_a_dash_in_a_display_math_block_is_still_read() -> None:
    """The site shows a dash written in maths, whatever the line opens with."""
    assert ced.markdown_hits("$$\n+ a — b\n$$\n") == [2]
    assert ced.markdown_hits("$$ —\nx\n$$\n") == [1]


def test_nothing_pairs_across_a_display_math_block() -> None:
    """A ``$$`` fence ends the paragraph before it, as a code fence does.

    The block was read as a mark on the lines of the paragraph, so a backtick,
    an asterisk or a quotation mark on one side paired with its partner on
    the other, and the dash between them was taken for code or for a title.
    """
    assert ced.markdown_hits("First `a — b\n$$\nx\n$$\nc` after.\n") == [1]
    assert ced.markdown_hits("An *open\n$$\nx\n$$\nprose — here* end.\n") == [5]
    assert ced.markdown_hits('A "quote\n$$\nx\n$$\nprose — here" end.\n') == [5]


def test_nothing_is_carried_across_a_fenced_block() -> None:
    """The same for a code fence: the reader stepped over it with its state open."""
    assert ced.markdown_hits("An *open\n```\nx\n```\nprose — here* end.\n") == [5]
    assert ced.markdown_hits('A "quote\n```\nx\n```\nprose — here" end.\n') == [5]


def test_the_paragraph_after_a_block_is_read_afresh() -> None:
    """A caption right under a block opens a paragraph, so it is a caption."""
    assert ced.markdown_hits("$$\nx\n$$\n*A caption — with a dash.*\n") == [4]
    assert ced.markdown_hits("Text.\n```\nx\n```\n*A caption — with a dash.*\n") == [5]


def test_nothing_is_carried_from_one_block_to_the_next() -> None:
    """A list item, a heading and a table row are blocks to the site.

    An italic span or a quotation left open in one does not close in the
    next, so the marks there are shown as written and the dash after them is
    the page's own.
    """
    assert ced.markdown_hits("- An *open\n- prose — here* end.\n") == [2]
    assert ced.markdown_hits('- A "quote\n- prose — here" end.\n') == [2]
    assert ced.markdown_hits("# A *heading\nprose — here* end.\n") == [2]
    assert ced.markdown_hits("| a *b |\n|---|\n| prose — here* |\n") == [3]
    assert ced.markdown_hits("> - An *open\n> - prose — here* end.\n") == [2]


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param("a * b — c * d\n", [1], id="a star between blanks"),
        pytest.param("2 * 3 — x\n", [1], id="a multiplication"),
        pytest.param("a ***\nb — c\n", [2], id="three stars at a line's end"),
        pytest.param("a *\nb — c* d\n", [2], id="a star a line break follows"),
        pytest.param("a *b — c * d\n", [1], id="a star nothing closes"),
        pytest.param("a *b — c\nd — e\n", [1, 2], id="over the lines of the paragraph"),
        pytest.param("a *b — c\n\nd — e* f\n", [1, 3], id="and across a blank line"),
        pytest.param('a "b — c\nd — e\n', [1, 2], id="a quote nothing closes"),
        pytest.param("a «b — c\n\nd» e\n", [1], id="guillemets nothing closes"),
        pytest.param("- a “b — c\n- d\n", [1], id="curly quotes on an item"),
        pytest.param("a *b — c\n", [1], id="to the end of the page"),
        pytest.param("a *b — c* d\n", [], id="a span"),
        pytest.param("x *a\nb — c* d\n", [], id="a span over two lines"),
        pytest.param("a*b — c*d\n", [], id="a span inside a word"),
        pytest.param("a ***b — c*** d\n", [], id="a span in bold"),
        pytest.param('a "b\nc — d" e\n', [], id="a quotation over two lines"),
        pytest.param("a *b — c* d *e — f\n", [1], id="a span, then a star left open"),
        pytest.param("<div>\nx *a — b* c\n</div>\n", [2], id="a raw block's stars"),
        pytest.param("a *b — c *d e* f\n", [1], id="a closing star takes the nearest"),
        pytest.param("a *b — c\nd *e f* g\n", [1], id="and over a line"),
    ],
)
def test_a_mark_that_closes_nothing_exempts_nothing(text: str, hits: list[int]) -> None:
    """The site shows a star or a quote left open as written, and the dash after it.

    The reader took any star for a mark and carried it open to the end of the
    block, so a multiplication hid the rest of its paragraph.
    """
    assert ced.markdown_hits(text) == hits


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param("| a | — |\nb\n", [1], id="a pipe line with no table"),
        pytest.param("| a | — |\n", [1], id="alone"),
        pytest.param("| a | — |\n|---|---|\n", [], id="a cell of a table"),
        pytest.param("a | —\n--|--\n", [], id="a cell with no outer pipes"),
        pytest.param("> | a | — |\n> |---|---|\n", [], id="in a quotation"),
        pytest.param("- | a | — |\n  |---|---|\n", [], id="in an item"),
        pytest.param("| a |\n|---|\n— / h\n", [], id="a row with no pipes"),
    ],
)
def test_an_empty_cell_is_one_only_in_a_table(text: str, hits: list[int]) -> None:
    """A pipe with no delimiter row under it is text, and so is what it fills."""
    assert ced.markdown_hits(text) == hits
    assert ced.markdown_double_hyphen_hits(text.replace("—", "--")) == hits


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param("a\n--\n", [], id="under a paragraph"),
        pytest.param("- a\n  --\n", [], id="in its item"),
        pytest.param("> a\n--\nb\n", [2], id="a lazy line of the paragraph"),
        pytest.param("- a\n--\nb\n", [2], id="out of the item"),
    ],
)
def test_a_double_hyphen_that_underlines_is_published_by_nothing(
    text: str, hits: list[int]
) -> None:
    assert ced.markdown_double_hyphen_hits(text) == hits


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param("- `x` - y\n", [1], id="an item"),
        pytest.param("a\n1. `x` - y\n", [2], id="a marker that can interrupt"),
        pytest.param("a\n2. `x` - y\n", [], id="a marker that cannot"),
        pytest.param("- a\n  2. `x` - y\n", [], id="and in an item"),
        pytest.param("> a\n2. `x` - y\n", [2], id="where the container has ended"),
        pytest.param("- - `x` - y\n", [1], id="a nested item"),
        pytest.param("> - - `x` - y\n", [1], id="and in a quotation"),
        pytest.param("- > `x` - y\n", [], id="a quotation, no item's head"),
        pytest.param("    - `x` - y\n", [], id="indented code"),
    ],
)
def test_an_item_head_is_read_where_the_walk_says_an_item_opens(
    text: str, hits: list[int]
) -> None:
    assert ced.markdown_bullet_hyphen_hits(text) == hits


def test_a_title_stays_exempt_over_the_lines_of_its_own_block() -> None:
    """What wraps inside one block is still read whole."""
    assert (
        ced.markdown_hits("- See *Acoustics — Rooms,\n  wrapped — here* now.\n") == []
    )
    assert (
        ced.markdown_hits("> See *Acoustics — Rooms,\n> wrapped — here* now.\n") == []
    )
    assert (
        ced.markdown_hits('> See "Acoustics — Rooms,\n> wrapped — here" now.\n') == []
    )


def test_a_quotation_mark_in_math_opens_no_quotation() -> None:
    text = 'The ditto $\\text{"}$ repeats the row, and the level rises — and falls.\n'
    assert ced.markdown_hits(text) == [1]


def test_a_year_in_math_or_code_opens_no_bibliographic_entry() -> None:
    """A level at 1000 Hz in parentheses is not an author's year.

    The guard took a list item with four digits in parentheses for the first
    line of a reference, and exempted every dash of the item as a reproduced
    title, wherever the digits stood.
    """
    assert ced.markdown_hits("- At $L(1000)$ the level rises — and falls.\n") == [1]
    assert ced.markdown_hits(
        "- The call `band(2000)` returns — wrongly — a list.\n"
    ) == [1]


def test_a_dash_written_inside_math_is_still_read() -> None:
    """The site shows a dash between dollar signs, so the guard reads it there.

    Two dollar signs are maths to the site even where they were meant as
    money, so taking maths out of the reading whole would hide the sentence
    between them.
    """
    assert ced.markdown_hits("It costs $5 — or $6 with the case.\n") == [1]


def test_no_title_exemption_covers_a_dash_in_maths() -> None:
    """A dash in maths is shown whatever stands around it, so it is always read.

    What a maths span left in the text was the dash itself, which the exempt
    readings could not tell from a dash of the prose: a quotation took it
    out, and a part number in the prose after it read as a standard's title.
    """
    assert ced.markdown_hits('"A $a — b$"\n') == [1]
    assert ced.markdown_hits("«A $a — b$»\n") == [1]
    assert ced.markdown_hits('A "wrapped $a\n— b$ quotation"\n') == [2]
    assert ced.markdown_hits("A level $a — b$ Part 3 of it.\n") == [1]
    assert ced.markdown_hits("A level $a —$Part 3 of it.\n") == [1]
    assert ced.markdown_hits("A *title $a — b$* here.\n") == [1]
    assert ced.markdown_hits("- Author (2001) $a — b$\n") == [1]
    assert ced.markdown_hits("- Author (2001) x\n  $a — b$ y\n") == [2]
    assert ced.markdown_hits("- Author (2001) x\n  $$\n  a — b\n  $$\n") == [3]
    assert ced.markdown_hits("title: $a — b$\n") == [1]


def test_a_dash_in_maths_inside_a_caption_is_read() -> None:
    assert ced.markdown_hits("*The ratio $a — b$ holds across the band.*\n") == [1]


def test_the_exemptions_still_hold_for_the_prose_beside_maths() -> None:
    assert ced.markdown_hits('"Acoustics — Rooms" and $a$ here.\n') == []
    assert ced.markdown_hits("See *Acoustics — Rooms* and $a$ here.\n") == []
    assert ced.markdown_hits("ISO 1 — Part 3: rooms, and $a$ here.\n") == []
    assert ced.markdown_hits("- Author (2001) Acoustics — Rooms, $a$.\n") == []


def test_only_a_title_of_the_frontmatter_is_a_title() -> None:
    """Under the frontmatter ``title:`` is a word of the page's own prose."""
    assert ced.markdown_hits("---\ntitle: Acoustics — Rooms\n---\n") == []
    assert ced.markdown_hits("---\nhead:\n  - title: A — B\n---\n") == []
    assert ced.markdown_hits("---\na: b\n---\ntitle: A — B\n") == [4]
    assert ced.markdown_hits("Text.\n\ntitle: The level rises — and falls.\n") == [3]


def test_the_frontmatter_holds_no_span() -> None:
    """A value of the frontmatter is plain text, shown with its marks as written.

    Two dollar signs in a title are no maths, so its dash stays the title's,
    and a pair of backticks in a description is no code, so its dash is shown.
    """
    assert ced.markdown_hits("---\ntitle: Costs $5 — or $6\n---\n") == []
    assert ced.markdown_hits("---\ndescription: Uses `a — b` here\n---\n") == [2]
    assert ced.markdown_hits("---\ndescription: Costs $5 — or $6\n---\n") == [2]
    assert ced.markdown_hits("---\ntitle: A `page\n---\nCode` and — this.\n") == [4]


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param(
            '---\ndescription: "Uses $a^*$ — for measurement."\n---\n',
            [2],
            id="a star in maths",
        ),
        pytest.param(
            "---\ndescription: Uses a* — for measurement.\n---\n",
            [2],
            id="a star",
        ),
        pytest.param(
            "---\ndescription: See *Acoustics — Rooms* here.\n---\n",
            [2],
            id="a pair of stars",
        ),
        pytest.param(
            "---\nkeywords:\n  - Author (2001) a — b\n---\n",
            [3],
            id="an author and a year",
        ),
        pytest.param(
            "---\nkeywords:\n  - Author (2001) a\n    wrapped — b\n---\n",
            [4],
            id="the line under an author and a year",
        ),
        pytest.param(
            "---\nnote: |\n  | a | — | b |\n---\n",
            [3],
            id="an empty cell",
        ),
        pytest.param(
            "---\ndescription: Uses “Acoustics — Rooms” here.\n---\n",
            [],
            id="a quotation stays one",
        ),
        pytest.param(
            '---\ndescription: Uses "Acoustics — Rooms" here.\n---\n',
            [],
            id="a straight quotation stays one",
        ),
        pytest.param(
            '---\nnote: "ISO 1 — Part 3: rooms"\n---\n',
            [],
            id="a part number stays one",
        ),
    ],
)
def test_a_frontmatter_value_holds_no_mark_of_markdown(
    text: str, hits: list[int]
) -> None:
    """The site shows a value with its marks as written, so they exempt nothing.

    Read as a line of a page, a star opened an italic span that hid the dash
    after it, and an author and a year passed the line as a reference.
    """
    assert ced.markdown_hits(text) == hits


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param('---\ndescription: "a — b"\n---\n', [2], id="a key's value"),
        pytest.param('---\nkeywords:\n  - "a — b"\n---\n', [3], id="an entry"),
        pytest.param('---\nkeywords: ["a — b", "c"]\n---\n', [2], id="a flow entry"),
        pytest.param('---\nnote: "wrapped\n  a — b"\n---\n', [3], id="a wrapped value"),
        pytest.param('---\nnote: "x “a — b” y"\n---\n', [], id="a quotation inside"),
    ],
)
def test_the_quotes_of_a_frontmatter_value_are_no_quotation(
    text: str, hits: list[int]
) -> None:
    """They are YAML's, gone from what the site shows, and quote nothing."""
    assert ced.markdown_hits(text) == hits


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param(
            '---\ndescription: "A *value"\n---\nBody — with a dash.\n',
            [4],
            id="a star into the body",
        ),
        pytest.param(
            "---\ndescription: A *value\n---\nBody — with a dash.\n",
            [4],
            id="a plain star into the body",
        ),
        pytest.param(
            "---\ndescription: A “value\n---\nBody — with a dash.\n",
            [4],
            id="a quotation into the body",
        ),
        pytest.param(
            "---\ndescription: A *value\nsummary: a — b\n---\n",
            [3],
            id="a star into the next value",
        ),
        pytest.param(
            "---\ndescription: A “value\nsummary: a — b\n---\n",
            [3],
            id="a quotation into the next value",
        ),
        pytest.param(
            "---\nkeywords:\n  - Author (2001) a\n---\n  wrapped — b\n",
            [5],
            id="a reference into the body",
        ),
        pytest.param(
            "---\ndescription: |\n  ```\n---\nThe level rises — and falls.\n",
            [5],
            id="a fence into the body",
        ),
        pytest.param(
            '---\ndescription: |\n  $$\n---\nSee "Acoustics — Rooms" here.\n',
            [],
            id="a display block into the body",
        ),
        pytest.param(
            "---\ndescription: Plain\n---\n*A caption — with a dash.*\n",
            [4],
            id="a caption right under it",
        ),
    ],
)
def test_what_a_frontmatter_value_leaves_open_stops_at_its_line(
    text: str, hits: list[int]
) -> None:
    """Nothing a value opens carries to the next value or into the body."""
    assert ced.markdown_hits(text) == hits


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param("---\na: x `y\n---\nc -- d` e\n", [4], id="a backtick"),
        pytest.param("---\na: x $y\n---\nc -- d$ e\n", [4], id="a dollar sign"),
        pytest.param(
            "---\na: x <!-- y\n---\nc -- d\n<!-- z -->\n", [2, 4], id="a comment"
        ),
        pytest.param(
            '---\na: x href="y\n---\nc -- d "\n', [4], id="an attribute value"
        ),
        pytest.param("---\na: |\n  $$\n---\nc -- d\n", [5], id="a display block"),
        pytest.param("---\na: |\n  ```\n---\nc -- d\n", [5], id="a fence"),
        pytest.param("---\na: Uses `x -- y` here\n---\n", [2], id="a code span"),
        pytest.param("---\na: Costs $x -- y$ here\n---\n", [2], id="a maths span"),
        pytest.param(
            "---\na: https://example.org/b--c\n---\n", [], id="an address stays one"
        ),
    ],
)
def test_a_frontmatter_value_hides_no_double_hyphen(text: str, hits: list[int]) -> None:
    """A value holds no span, and what it leaves open stops at the frontmatter."""
    assert ced.markdown_double_hyphen_hits(text) == hits


#: A page citing one report, its number written ``{number}`` and its note
#: ``{note}``, and a key of the page's own after the list.
_REPORT_PAGE = (
    "---\n"
    'title: "A page"\n'
    "references:\n"
    "  - type: report\n"
    '    title: "{title}"\n'
    '    number: "{number}"\n'
    "    doi: {doi}\n"
    '    note: "{note}"\n'
    "  - {first}\n"
    'description: "{description}"\n'
    "---\n"
    "The body.\n"
)


@pytest.mark.parametrize(
    ("fields", "hits"),
    [
        pytest.param({}, [], id="identifiers as they are issued"),
        pytest.param({"number": "NRL -- 95-9628"}, [6], id="a spaced run is a dash"),
        pytest.param({"number": "--95-9628"}, [6], id="a run at the edge"),
        pytest.param({"number": "---95-9628"}, [6], id="a longer run at the edge"),
        pytest.param({"number": "95-9628---"}, [6], id="a longer run at the end"),
        pytest.param({"number": "NRL--- 95-9628"}, [6], id="a longer run by a blank"),
        pytest.param({"number": "NRL/FR/7176---95"}, [], id="a longer run inside"),
        pytest.param({"note": "Its Table 2--the source"}, [8], id="the note is prose"),
        pytest.param({"title": "Physics--description"}, [5], id="so is the title"),
        pytest.param({"description": "NRL/FR/7176--95"}, [10], id="the page's own"),
    ],
)
def test_an_identifier_of_a_reference_keeps_its_hyphens(
    fields: dict[str, str], hits: list[int]
) -> None:
    """A reference's number, DOI, ISBN or address is printed as written.

    The References section prints those fields outside the text smartypants
    reads, so the Naval Research Laboratory's NRL/FR/7176--95-9628 is a report
    number and no dash. A run with a blank on either side, or at the edge of
    the value, is a dash written in ASCII still, however many hyphens it holds,
    and so is one in any other field of the entry or in a key of the page after
    the list.
    """
    values = {
        "title": "Physics description",
        "number": "NRL/FR/7176--95-9628",
        "doi": "10.1000/a--b",
        "note": "Its Table 2.",
        "first": 'isbn: "0-00--000000-0"',
        "description": "A page.",
    }
    page = _REPORT_PAGE.format(**(values | fields))
    assert ced.markdown_double_hyphen_hits(page) == hits
    assert ced.markdown_double_hyphen_hits(page, mdx=True) == hits


def test_an_identifier_key_off_the_references_is_read_as_prose() -> None:
    """Only an entry of ``references`` holds a reference's identifiers."""
    page = '---\nnumber: "A--1"\nextra:\n  - number: "B--2"\n---\n'
    assert ced.markdown_double_hyphen_hits(page) == [2, 4]
    listed = '---\nreferences:\n  - number: "A--1"\n    url: "x--y"\n---\n'
    assert ced.markdown_double_hyphen_hits(listed) == []


@pytest.mark.parametrize(
    "text",
    [
        pytest.param(
            '---\ndescription: "He read «A —\n  B» there"\n---\n', id="double-quoted"
        ),
        pytest.param(
            "---\ndescription: 'He read «A —\n  B» there'\n---\n", id="single-quoted"
        ),
        pytest.param("---\ndescription: He read «A —\n  B» there\n---\n", id="plain"),
        pytest.param(
            "---\ndescription: |\n  He read «A —\n  B» there\n---\n", id="a block"
        ),
        pytest.param(
            "---\ndescription: >\n  He read “A —\n  B” there\n---\n", id="a folded one"
        ),
        pytest.param(
            '---\ndescription: He read "A —\n  B" there\n---\n', id="in straight quotes"
        ),
        pytest.param(
            "---\ndescription:\n  He read «A —\n  B» there\n---\n", id="under its key"
        ),
        pytest.param(
            "---\ndescription: A —\n  Part 3 there\n---\n", id="a part number"
        ),
    ],
)
def test_a_quotation_wraps_with_its_value(text: str) -> None:
    """The lines of one value are one text: only the next value stops a quotation.

    Each physical line was read alone, so a title quoted across the wrap of its
    value was refused, though the same value on one line passed.
    """
    assert ced.markdown_hits(text) == []


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param(
            "---\ndescription: He read «A —\nnext: B» — x\n---\n",
            [2, 3],
            id="into the next value",
        ),
        pytest.param(
            "---\ndescription: He read «A —\n  B there\nnext: C»\n---\n",
            [2],
            id="closed by the next value alone",
        ),
        pytest.param(
            "---\ndescription: a —\n  b\n---\n", [2], id="no quotation at all"
        ),
        pytest.param(
            "---\ndescription: A\n  b — c\n  d «e» — f\n---\n",
            [3, 4],
            id="a line of the value with its own dash",
        ),
    ],
)
def test_a_value_names_the_line_of_its_dash(text: str, hits: list[int]) -> None:
    assert ced.markdown_hits(text) == hits


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("---\ntitle: Acoustics\n  — Rooms — x\n---\n", id="wrapped"),
        pytest.param(
            "---\ntitle: |\n  Acoustics — Rooms\n  — x\n---\n", id="in a block of text"
        ),
    ],
)
def test_a_title_is_a_title_on_every_line_of_its_value(text: str) -> None:
    assert ced.markdown_hits(text) == []


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param(
            "---\ntitle: |\n    Acoustics — Rooms\n  # a note — here\n---\n",
            [4],
            id="a comment short of the content",
        ),
        pytest.param(
            "---\ntitle: |2\n    Acoustics — Rooms\n  # Still — title\n---\n",
            [],
            id="at the column the indicator sets",
        ),
        pytest.param(
            "---\ntitle: |\n    Acoustics — Rooms\n    # Still — title\n---\n",
            [],
            id="at the content column",
        ),
    ],
)
def test_a_title_block_ends_at_a_line_short_of_its_content(
    text: str, hits: list[int]
) -> None:
    """A block of text holds the lines indented as far as its first line, or
    as its indicator says; a ``#`` line short of that column, deeper than the
    key, is a comment YAML ends the block on, and its dash is the comment's.

    The block was read as every line deeper than the key, so the comment was
    a line of the title and its dash passed as one of the title.
    """
    assert ced.markdown_hits(text) == hits


def test_a_value_that_quotes_with_an_escaped_quote_quotes() -> None:
    """A double-quoted value decodes it, so the page shows a quotation."""
    text = '---\ndescription: "He said \\"A — B\\" there"\n---\n'
    assert ced.markdown_hits(text) == []
    assert ced.markdown_hits('---\ndescription: "He said \\"A\\" — B"\n---\n') == [2]


_SCRIPT = "---\nhead:\n  - tag: script\n    content: "


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param(
            _SCRIPT + '|\n      {"a": ["A — B"]}\n---\n', [5], id="an array in a block"
        ),
        pytest.param(
            _SCRIPT + '\'{"a": ["A — B"]}\'\n---\n', [4], id="an array, single-quoted"
        ),
        pytest.param(
            _SCRIPT + '|\n      {"name": "A — B"}\n---\n', [5], id="a value in a block"
        ),
        pytest.param(
            _SCRIPT + '|\n      ["A", "B — C"]\n---\n', [5], id="after a comma"
        ),
        pytest.param(
            _SCRIPT + '|\n      {"a": "x «A — B» y"}\n---\n',
            [],
            id="a title in guillemets",
        ),
        pytest.param(
            _SCRIPT + '|\n      {"a": "x \\"A — B\\" y"}\n---\n',
            [],
            id="a title in escaped quotes",
        ),
        pytest.param(
            _SCRIPT + '\'{"a": "x\n      «A — B» y"}\'\n---\n',
            [],
            id="a title on a wrapped line",
        ),
        pytest.param(
            _SCRIPT + '|\n      He read "A — B" there\n---\n',
            [],
            id="a block that holds no JSON",
        ),
        pytest.param(
            _SCRIPT + 'He read "A — B" there\n---\n', [], id="a value that holds none"
        ),
    ],
)
def test_the_quotes_of_a_json_string_are_no_quotation(
    text: str, hits: list[int]
) -> None:
    """The JSON-LD a page's head carries is published, whatever opens a string.

    A string after a bracket or a comma read as a quotation, so ``["A — B"]`` hid
    a dash the JSON-LD publishes, where ``{"name": "A — B"}`` was refused.
    """
    assert ced.markdown_hits(text) == hits


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param(
            _SCRIPT + '\'{"a": "A \\u2014 B"}\'\n---\n', [4], id="single-quoted"
        ),
        pytest.param(
            _SCRIPT + '|\n      {"a": "A \\u2014 B"}\n---\n', [5], id="a block"
        ),
        pytest.param(
            _SCRIPT + "|\n      A \\u2014 B\n---\n", [], id="a block of no JSON"
        ),
        pytest.param(_SCRIPT + "'A \\u2014 B'\n---\n", [], id="a value of no JSON"),
    ],
)
def test_an_escape_is_read_in_the_json_of_a_value_and_nowhere_else(
    text: str, hits: list[int]
) -> None:
    """A single-quoted value hid one; a block of plain text took one for JSON's."""
    assert ced.markdown_hits(text) == hits


def test_an_indented_fence_opens_no_frontmatter() -> None:
    """The site reads one only at the first column, and the rest is the page's."""
    assert ced.markdown_hits("    ---\ntitle: a — b\n---\n") == [2]


def test_a_frontmatter_value_is_no_list_item() -> None:
    """The site shows an entry of a YAML sequence as text, hyphen and all."""
    assert ced.markdown_bullet_hyphen_hits("---\na:\n  - `x` - text\n---\n") == []
    opened = "---\na: |\n  $$\n---\n- `x` - text\n"
    assert ced.markdown_bullet_hyphen_hits(opened) == [5]


def test_the_site_data_modules_are_read_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The home page's text and the catalogue notes are published prose.

    The guard once read the glossary cards and nothing else under
    ``site/src/data``, so an em dash in the home page's text reached the
    site with the gate green.
    """
    monkeypatch.chdir(pathlib.Path(__file__).resolve().parent.parent)
    assert "site/src/data" in ced.DEFAULT_ROOTS
    read = {path.as_posix() for path in ced.iter_files(ced.DEFAULT_ROOTS)}
    for published in (
        "site/src/data/home.ts",
        "site/src/data/glossary.mjs",
        "site/src/data/catalogue-es.json",
    ):
        assert published in read


def test_dash_in_a_typescript_data_module_is_refused(tmp_path: pathlib.Path) -> None:
    page = tmp_path / "home.ts"
    page.write_text(
        "// A comment keeps its dash — nobody reads it on the page.\n"
        "export const NOTE = 'One call — and the figure is drawn.';\n",
        encoding="utf-8",
    )
    assert ced.scan(page) == [2]


def test_dash_in_a_json_string_is_refused_unless_it_quotes_a_source(
    tmp_path: pathlib.Path,
) -> None:
    notes = tmp_path / "catalogue-es.json"
    notes.write_text(
        "{\n"
        '  "the page prints “—” where the number would be": "x",\n'
        '  "empty": "—",\n'
        '  "note": "la tabla — sin cifra",\n'
        "}\n",
        encoding="utf-8",
    )
    assert ced.scan(notes) == [4]


def test_dash_in_a_plain_text_file_is_refused(tmp_path: pathlib.Path) -> None:
    """The site serves its robots.txt as written, comments and all.

    Nothing converts a double hyphen there, so only the character is read.
    """
    robots = tmp_path / "robots.txt"
    robots.write_text(
        "# phonometry documentation — robots.txt\n# Two -- hyphens stay two.\n",
        encoding="utf-8",
    )
    assert ced.findings(robots) == [(1, "em dash")]


def test_a_quotation_exempts_only_itself_in_a_plain_text_file() -> None:
    """The whole line went when a quotation on it held a dash."""
    assert ced.text_hits('# "ISO 1 — Scope" — additional guidance\n') == [1]
    assert ced.text_hits("# «ISO 1 — Scope» — additional guidance\n") == [1]
    assert ced.text_hits("# “ISO 1 — Scope” — additional guidance\n") == [1]
    assert ced.text_hits('# "ISO 1 — Scope" and "ISO 2 — Rooms"\n') == []


def test_the_dash_between_two_quotations_is_read() -> None:
    """Quotations are read left to right, so a closing mark opens nothing."""
    assert ced.text_hits('# "ISO 1" — "ISO 2"\n') == [1]
    assert ced.python_hits('"""Cites "ISO 1" — "ISO 2"."""\n') == [1]


def test_a_quotation_that_never_closes_on_its_line_quotes_nothing() -> None:
    assert ced.text_hits('# "ISO 1 — Scope\n') == [1]
    assert ced.text_hits("# «ISO 1 — Scope\n") == [1]


def test_a_part_number_exempts_only_its_own_dash(tmp_path: pathlib.Path) -> None:
    """The whole line, or the whole string, went when a part number stood on it."""
    prose = "The level rises — and ISO 1 — Part 3: rooms falls."
    assert ced.text_hits(f"# {prose}\n") == [1]
    assert ced.markdown_hits(f"{prose}\n") == [1]
    assert ced.python_hits(f'"""{prose}"""\n') == [1]
    module = tmp_path / "home.ts"
    module.write_text(f"export const NOTE = '{prose}';\n", encoding="utf-8")
    assert ced.scan(module) == [1]
    notes = tmp_path / "catalogue-es.json"
    notes.write_text(f'{{"note": "{prose}"}}\n', encoding="utf-8")
    assert ced.scan(notes) == [1]
    for title in ("ISO 1 — Part 3: rooms", "ISO 1 — Teil 3", "ISO 1 — Partie 3"):
        assert ced.text_hits(f"# {title}\n") == []
        assert ced.markdown_hits(f"{title}\n") == []
        assert ced.python_hits(f'"""{title}"""\n') == []


@pytest.mark.parametrize(
    ("line", "hits"),
    [
        pytest.param(
            "A = 'ISO 1 — Part 3: “Acoustics — Rooms”';", [], id="both titles"
        ),
        pytest.param("A = '“Acoustics — Rooms”';", [], id="a curly quotation"),
        pytest.param("A = '«Acoustics — Rooms»';", [], id="guillemets"),
        pytest.param('A = "“Acoustics — Rooms”";', [], id="inside a double-quoted one"),
        pytest.param("A = '“Acoustics — Rooms” — and more';", [1], id="beside one"),
        pytest.param("A = 'ISO 1 — Part 3: a — b';", [1], id="beside a part number"),
        pytest.param("A = '“Acoustics — Rooms';", [1], id="never closed"),
        pytest.param('A = "The level rises — and falls";', [1], id="a string's quotes"),
        pytest.param('A = "ISO 1 — Part 3: a — b";', [1], id="a string's quotes too"),
    ],
)
def test_a_data_module_reads_a_quotation_by_the_marks_that_say_which_end(
    line: str, hits: list[int]
) -> None:
    """A curly quote and a guillemet quote; a straight one delimits the string.

    The module's strings are read as written, so a straight quote there is
    the language's, and the prose between two of them quotes nothing. The
    other marks can only be a quotation, and it exempts its own dash as it
    does everywhere else.
    """
    assert ced.data_hits(f"{line}\n") == hits


@pytest.mark.parametrize(
    ("line", "hits"),
    [
        pytest.param('A = f"ISO 1 — Part 3: {x}"', [], id="a part number"),
        pytest.param('A = f"“Acoustics — Rooms” {x}"', [], id="a quotation"),
        pytest.param('A = f"``a — b`` {x}"', [], id="an inline literal"),
        pytest.param('A = f"{x} — {y}"', [1], id="a dash alone between two fields"),
        pytest.param('A = f"The level — {x}"', [1], id="prose"),
        pytest.param('A = f"“Acoustics — Rooms” — {x}"', [1], id="beside a quotation"),
    ],
)
def test_an_f_string_exempts_what_any_other_string_does(
    line: str, hits: list[int]
) -> None:
    """The text between its fields is read as the lines of a string are."""
    assert ced.python_hits(f"{line}\n") == hits


@pytest.mark.parametrize(
    ("source", "hits"),
    [
        pytest.param(
            'x = f"\\"A — B\\" {y}"\n', [], id="a quotation in escaped quotes"
        ),
        pytest.param('x = f"\\"A {y} — B\\""\n', [], id="and a field inside it"),
        pytest.param('x = f"“A {y} — B”"\n', [], id="a field inside curly quotes"),
        pytest.param('x = f"—"\n', [], id="a dash that fills it"),
        pytest.param(
            'x = fr"\\"A — B\\" {y}"\n', [1], id="raw, where it escapes nothing"
        ),
        pytest.param('x = f"a — b {y}"\n', [1], id="prose before a field"),
        pytest.param('x = f"{y} a — b"\n', [1], id="prose after a field"),
        pytest.param('x = f"{{a — b}}"\n', [1], id="prose in doubled braces"),
        pytest.param('x = f"{y:—>3}"\n', [1], id="a dash that fills a field"),
        pytest.param("x = f\"{f'a — b'}\"\n", [1], id="an f-string in a field"),
        pytest.param('x = f"\\u2014 {y}"\n', [1], id="an escape of the dash"),
        pytest.param('x = rf"\\u2014 {y}"\n', [], id="and a raw one, which is none"),
        pytest.param('x = f"""a {y}\nb\nc — d\n"""\n', [3], id="its own line"),
        pytest.param('x = f"""a {y}\nb {z}\nc — d\n"""\n', [3], id="past two fields"),
        pytest.param('x = f"a {\n  y\n} b — c"\n', [3], id="past a field of lines"),
        pytest.param('x = f"""\n{y}\nA — Part 3\n"""\n', [], id="a part number"),
    ],
)
def test_an_f_string_is_read_whole_as_any_other_string(
    source: str, hits: list[int]
) -> None:
    """Its value is what is read, each field a mark, and each dash names its line.

    Each piece between two fields was read alone with its escapes as written, so a
    quote escaped in it quoted nothing and a field in a quotation split it, and
    every dash was reported on the line the piece began on.
    """
    assert ced.python_hits(source) == hits


@pytest.mark.parametrize(
    ("source", "hits"),
    [
        pytest.param('x = f"{y} -- {z}"\n', [1], id="between two fields"),
        pytest.param('x = f"a -- {y}"\n', [1], id="before one"),
        pytest.param('x = f"--{y}"\n', [], id="an option of a command line"),
        pytest.param('x = f"-- {y}"\n', [], id="at its start, as in any other string"),
        pytest.param('x = f"`a {y} -- b`"\n', [], id="in a literal a field splits"),
        pytest.param('x = f"""a {y}\nb\nc -- d\n"""\n', [3], id="its own line"),
    ],
)
def test_an_f_string_reads_whole_for_a_double_hyphen_too(
    source: str, hits: list[int]
) -> None:
    assert ced.python_double_hyphen_hits(source) == hits


def test_a_title_of_several_dashes_is_marked_as_a_title() -> None:
    """Only the dash before the part number says so; the marks say the rest."""
    title = "Acoustics — Rooms — Part 3: halls"
    assert ced.markdown_hits(f"{title}\n") == [1]
    assert ced.markdown_hits(f"See *{title}* here.\n") == []
    assert ced.markdown_hits(f'See "{title}" here.\n') == []
    assert ced.python_hits(f'"""See "{title}" here."""\n') == []


def test_an_exempt_dash_of_a_string_exempts_only_itself() -> None:
    """One quotation or part number in a docstring passed every line of it."""
    quoted = '"""Cites "Acoustics — Rooms".\n\nThe level rises — and falls.\n"""\n'
    assert ced.python_hits(quoted) == [3]
    part = '"""Cites ISO 1 — Part 3: rooms.\n\nThe level rises — and falls.\n"""\n'
    assert ced.python_hits(part) == [3]
    assert ced.python_hits('"""Cites "Acoustics — Rooms" — and more."""\n') == [1]
    assert ced.python_hits('NOTE = """Cites "Acoustics — Rooms"."""\n') == []


def test_an_exempt_dash_of_a_json_string_exempts_only_itself(
    tmp_path: pathlib.Path,
) -> None:
    notes = tmp_path / "catalogue-es.json"
    notes.write_text(
        "{\n"
        '  "a": "“Acoustics — Rooms” — and more",\n'
        '  "b": "“Acoustics — Rooms”"\n'
        "}\n",
        encoding="utf-8",
    )
    assert ced.scan(notes) == [2]


def test_an_inline_literal_of_a_string_is_code() -> None:
    """The placeholder a fiche prints, named in its docstring, is data.

    Three docstrings passed only because the quotation marks inside their
    literal were read as a quotation.
    """
    assert ced.python_hits('"""Shown as ``"—"``, the empty cell."""\n') == []
    assert ced.python_hits('"""Shown as ``a — b``, the empty cell."""\n') == []
    assert ced.python_hits('"""Shown as ``a``, the empty cell — or not."""\n') == [1]


def test_a_plain_text_file_has_no_empty_cell_and_no_code() -> None:
    """A line of robots.txt is no table cell and no string, whatever it holds.

    The file was read as a string of a module, which took a line of nothing
    but a dash for a placeholder and a pair of backticks for code, and rule
    P6 grants neither outside a table and a page.
    """
    assert ced.text_hits("—\n") == [1]
    assert ced.text_hits("  —  \n") == [1]
    assert ced.text_hits("# `a — b`\n") == [1]


def test_the_robots_file_is_read_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """The guard read no plain-text file, so the subpath robots.txt opened on a dash."""
    monkeypatch.chdir(pathlib.Path(__file__).resolve().parent.parent)
    read = {path.as_posix() for path in ced.iter_files(ced.DEFAULT_ROOTS)}
    assert "site/public/robots.txt" in read


def test_a_plain_text_file_is_read_only_where_a_root_names_it(
    tmp_path: pathlib.Path,
) -> None:
    """The llms shards beside robots.txt are generated from the pages read here."""
    (tmp_path / "shard.txt").write_text("Acoustics — Part 2\n", encoding="utf-8")
    (tmp_path / "page.md").write_text("The level rises.\n", encoding="utf-8")
    assert [path.name for path in ced.iter_files((str(tmp_path),))] == ["page.md"]


# The double hyphen: the ASCII spelling of the dash, which Astro's smartypants
# publishes as the em dash itself. The first defect the reading was written
# against is the docstring bullet ``* :func:`npd_level` -- the level``, which
# reached the API reference as an em dash in 92 list items and nearly five hundred
# other docstring lines.


def test_a_double_hyphen_in_page_prose_is_refused() -> None:
    assert ced.markdown_double_hyphen_hits("The level rises -- and falls.\n") == [1]


def test_an_unspaced_double_hyphen_is_refused_too() -> None:
    """Smartypants converts the run whether or not spaces surround it."""
    assert ced.markdown_double_hyphen_hits("The level rises--and falls.\n") == [1]


def test_a_double_hyphen_in_code_is_data() -> None:
    text = "Run `make audit --only` here.\n```bash\npython x.py --count\n```\n"
    assert ced.markdown_double_hyphen_hits(text) == []


def test_a_code_span_that_wraps_keeps_its_option() -> None:
    """A code span the paragraph wraps puts the option at the start of a line."""
    text = "Run `python scripts/generate_graphs.py --animations\n--audit-only` once.\n"
    assert ced.markdown_double_hyphen_hits(text) == []


def test_a_code_span_that_wraps_in_a_quotation_keeps_its_option() -> None:
    """A quotation's marks are not its text, so its paragraph reads as one."""
    text = "> Run `python\n> --version` here.\n"
    assert ced.markdown_double_hyphen_hits(text) == []
    assert ced.markdown_hits("> Run `a —\n> b` here.\n") == []
    assert ced.markdown_hits("> Run `a\n> b` here — and stop.\n") == [2]


def test_a_code_span_does_not_cross_into_the_next_item_of_a_quotation() -> None:
    assert ced.markdown_double_hyphen_hits("> - Run `a\n> - b -- c` here.\n") == [2]
    assert ced.markdown_hits("> - Run `a\n> - b — c` here.\n") == [2]


def test_a_line_of_a_quotation_is_read_through_its_marks() -> None:
    """A quotation's marks are not its text, so every reading looks past them.

    An asterisk bullet behind one opened an italic span that hid the item's
    dash, a caption behind one passed for a citation, and an empty cell, a
    reference, a table's separator row and a rule behind one were refused.
    """
    assert ced.markdown_hits("> The level rises — and falls.\n") == [1]
    assert ced.markdown_hits("> * A list item — with a dash.\n") == [1]
    assert ced.markdown_hits("> *A caption — with a dash.*\n") == [1]
    assert ced.markdown_hits("> | a | — | b |\n> |---|---|---|\n") == []
    assert ced.markdown_hits("> - Author (2001) Acoustics — Rooms\n") == []
    assert (
        ced.markdown_hits("> - Author (2001) Acoustics — Rooms,\n>   wrapped — title\n")
        == []
    )
    assert ced.markdown_hits('>"Acoustics — Rooms"\n') == []
    table = "> | a | b |\n> |---|---|\n> | x | -- |\n"
    assert ced.markdown_double_hyphen_hits(table) == []
    assert ced.markdown_double_hyphen_hits("> ---\n") == []
    assert ced.markdown_double_hyphen_hits("> The level -- falls.\n") == [1]
    assert ced.markdown_bullet_hyphen_hits("> - `x` - the text\n") == [1]


#: Pages the walk of the page decides, with the lines where the site's parser
#: shows a dash, each measured on it: ``markdown_hits`` of each with an em dash,
#: and ``markdown_double_hyphen_hits`` of each with a double hyphen in its place.
_WALKED_PAGES = (
    pytest.param("- > ```\n> text — y\n", [2], id="behind a quotation in an item"),
    pytest.param("- > $$\n> text — y\n", [2], id="maths behind a quotation in an item"),
    pytest.param("1. > ```\n> text — y\n", [2], id="behind a quotation in a numbered"),
    pytest.param("> - > ```\n> > text — y\n", [2], id="and in a quotation"),
    pytest.param("a\n2. ```\n   b — y\n", [3], id="a marker that cannot interrupt"),
    pytest.param("a\n2. ~~~\n   b — y\n", [3], id="a marker on a tilde fence"),
    pytest.param("a\n2. $$\n   b — y\n   $$\n", [3], id="a marker on a display block"),
    pytest.param("> a `b — x\n===\nc` d\n", [], id="a lazy line of ==="),
    pytest.param("> a `b — x\n=\nc` d\n", [], id="a lazy line of ="),
    pytest.param("- a `b — x\n===\nc` d\n", [], id="a line of === out of an item"),
    pytest.param("1. a `b — x\n===\nc` d\n", [], id="and out of a numbered one"),
    pytest.param("> > a `b — x\n> ===\n> c` d\n", [], id="a shallower quotation"),
    pytest.param("- > a `b — x\n  ===\n  c` d\n", [], id="an item's own column"),
    pytest.param("- a `b — x\n    2. c` d\n", [], id="an ordered marker in an item"),
    pytest.param("- a `b — x\n    | c` d\n", [], id="a pipe in an item"),
    pytest.param("a `b — x\n2. c` d\n", [], id="an ordered marker in a paragraph"),
    pytest.param("- # h `b\nc — x` d\n", [2], id="a heading on an item's line"),
    pytest.param("- ## h `b\n  c — x` d\n", [2], id="and the item goes on"),
    pytest.param("1. # h `b\n   c — x` d\n", [2], id="on a numbered item's line"),
    pytest.param("> - # h `b\n> c — x` d\n", [2], id="and in a quotation"),
    pytest.param("- ***\n  c — x\n", [2], id="a rule on an item's line"),
    pytest.param("> - ***\n> c — x\n", [2], id="and in a quotation"),
    pytest.param(
        "- <!-- y --> `b\n  c — x` d\n", [2], id="a comment on an item's line"
    ),
    pytest.param("a `b — x\n<div>\nc` d\n", [1], id="a block tag"),
    pytest.param("a `b — x\n</div>\nc` d\n", [1], id="a closing block tag"),
    pytest.param("a `b — x\n<details>\nc` d\n", [1], id="a details tag"),
    pytest.param("a `b — x\n<script>\nc` d\n", [1], id="a script tag"),
    pytest.param("a `b — x\n<?php\nc` d\n", [1], id="a processing instruction"),
    pytest.param("<div>\n`x — y`\n</div>\n", [2], id="a raw block holds no code span"),
    pytest.param("a `b — x\n<span>\nc` d\n", [], id="an inline tag"),
    pytest.param("- a\n  ```\n  x\nprose — y\n", [4], id="a fence ends with its item"),
    pytest.param("- a\n  ~~~\n  x\nprose — y\n", [4], id="and a tilde fence"),
    pytest.param("- a\n  $$\n  x\nprose — y\n", [4], id="and a display block"),
    pytest.param("* a `b —\n  ```\n- item —\n", [1, 3], id="an item after the fence"),
    pytest.param("-\ta `b — x\n    - c` d\n", [1], id="an item marked with a tab"),
    pytest.param("$$\n```\n$$\nprose — y\n", [4], id="a fence in a display block"),
    pytest.param("a `b — x\n:::note\nc` d\n:::\n", [1], id="an aside"),
    pytest.param(":::note\na `b — x\n:::\nc` d\n", [2], id="the end of an aside"),
    pytest.param("| `a | b — x` |\n|---|---|\n", [1], id="two cells of a row"),
    pytest.param("| a `b — x\nc` d\n", [], id="a pipe with no table"),
    pytest.param("    a `b\nc — x` d\n", [2], id="indented code"),
)


@pytest.mark.parametrize(("page", "hits"), _WALKED_PAGES)
def test_a_dash_is_read_where_the_walk_of_the_page_says_it_stands(
    page: str, hits: list[int]
) -> None:
    """Each of these read otherwise, hiding prose or refusing a code span.

    A reader of each line by itself cannot say which of them opens a block: that
    takes the quotations and the items open at it and the paragraph above it.
    """
    assert ced.markdown_hits(page) == hits
    assert ced.markdown_double_hyphen_hits(page.replace("—", "--")) == hits


@pytest.mark.parametrize(
    ("page", "md", "mdx"),
    [
        pytest.param("a `b — x\n    - c` d\n", [], [1], id="an item four columns in"),
        pytest.param("a `b — x\n<A />\nc` d\n", [], [1], id="a tag alone"),
        pytest.param("<A />\n`x — y`\n", [2], [], id="a line under a lone tag"),
        pytest.param("    a — b\n", [], [1], id="indented code"),
        pytest.param(
            "a\n    ```\n    b — y\n", [3], [], id="a fence under a paragraph"
        ),
    ],
)
def test_the_kind_of_a_page_says_what_a_line_opens(
    page: str, md: list[int], mdx: list[int]
) -> None:
    """On an MDX page any indentation opens a block, and there is no raw HTML."""
    assert ced.markdown_hits(page) == md
    assert ced.markdown_hits(page, mdx=True) == mdx
    assert ced.markdown_double_hyphen_hits(page.replace("—", "--")) == md
    assert ced.markdown_double_hyphen_hits(page.replace("—", "--"), mdx=True) == mdx


def test_the_guard_reads_a_page_by_its_kind(tmp_path: pathlib.Path) -> None:
    """The suffix says which: both spellings of the dash go by it."""
    page = "a `b — x\n    - c` d\n"
    (tmp_path / "page.md").write_text(page, encoding="utf-8")
    (tmp_path / "page.mdx").write_text(page, encoding="utf-8")
    assert ced.scan(tmp_path / "page.md") == []
    assert ced.scan(tmp_path / "page.mdx") == [1]


def test_a_block_under_a_reference_is_read_for_itself() -> None:
    """Only the wrapped lines of a bibliographic entry reproduce its title.

    A heading, an item or a table row under the entry opens a block of its
    own, and it kept the entry's exemption for as long as it stayed indented.
    """
    assert ced.markdown_hits("- Author (2001) x\n  ## Heading — y\n") == [2]
    assert ced.markdown_hits("- Author (2001) x\n  - item — y\n") == [2]
    assert ced.markdown_hits("- Author (2001) x\n  | a — b |\n  |---|\n") == [2]
    assert ced.markdown_hits("> - Author (2001) x\n>   ## Heading — y\n") == [2]
    assert ced.markdown_hits("- Author (2001) x\n  wrapped — title\n") == []
    assert ced.markdown_hits("- Author (2001) x\n- Author (2002) a — b\n") == []


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param(
            "> First `a — b\n> $$\n> x\n> $$\n> c` after.\n",
            [1],
            id="a code span across quoted maths",
        ),
        pytest.param(
            "> First `a — b\n> ```\n> x\n> ```\n> c` after.\n",
            [1],
            id="a code span across a quoted fence",
        ),
        pytest.param(
            "> First `a — b\n> ~~~\n> x\n> ~~~\n> c` after.\n",
            [1],
            id="a code span across a quoted tilde fence",
        ),
        pytest.param(
            "> a *b\n> $$\n> x\n> $$\n> c — d* after.\n",
            [5],
            id="an italic span across quoted maths",
        ),
        pytest.param(
            '> a "b\n> $$\n> x\n> $$\n> c — d" after.\n',
            [5],
            id="a quotation across quoted maths",
        ),
        pytest.param("> $$\n> a — b\n> $$\n", [2], id="a dash in quoted maths"),
        pytest.param("> ```\n> a — b\n> ```\n", [], id="a dash in a quoted fence"),
        pytest.param("> $$\n> *a\n> $$\n> c — d\n", [4], id="a star in quoted maths"),
        pytest.param(
            "> $$\n> x\nc — d\n", [3], id="quoted maths ends with its quotation"
        ),
        pytest.param(
            "- First `a — b\n  $$\n  x\n  $$\n  c` after.\n",
            [1],
            id="a code span across an item's maths",
        ),
        pytest.param(
            "- $$\n  a\n  $$\nSee *Acoustics — Rooms* here.\n",
            [],
            id="a title after maths on an item's first line",
        ),
        pytest.param(
            "- $$\n  a — b\n  $$\n", [2], id="a dash in maths on an item's first line"
        ),
        pytest.param(
            "- ```\n  a\n  ```\n*The level — rises.*\n",
            [4],
            id="a caption after a fence on an item's first line",
        ),
        pytest.param(
            "- ```\n  a — b\n  ```\n",
            [],
            id="a dash in a fence on an item's first line",
        ),
    ],
)
def test_a_block_behind_marks_ends_the_paragraph_as_any_other(
    text: str, hits: list[int]
) -> None:
    """The site ends the paragraph there, so nothing pairs across such a block.

    The fence readers saw no fence behind a mark, so to them the block was part
    of the paragraph, and the block a list item opened ran to the end of the
    page, refusing every dash after it, a title's among them.
    """
    assert ced.markdown_hits(text) == hits


@pytest.mark.parametrize(
    ("text", "hits"),
    [
        pytest.param(
            "> First `a -- b\n> $$\n> x\n> $$\n> c` after.\n",
            [1],
            id="a code span across quoted maths",
        ),
        pytest.param(
            "> First `a -- b\n> ```\n> x\n> ```\n> c` after.\n",
            [1],
            id="a code span across a quoted fence",
        ),
        pytest.param(
            "> ```\n> a\n>\n> b -- c\n> ```\n", [], id="a bare mark in a quoted fence"
        ),
        pytest.param(
            "> $$\n> a\n>\n> b -- c\n> $$\n", [], id="a bare mark in quoted maths"
        ),
        pytest.param(
            "- $$\n  a\n  $$\nafter -- prose\n",
            [4],
            id="after maths on an item's first line",
        ),
        pytest.param(
            "- ```\n  a\n  ```\nafter -- prose\n",
            [4],
            id="after a fence on an item's first line",
        ),
    ],
)
def test_a_block_behind_marks_hides_no_double_hyphen_after_it(
    text: str, hits: list[int]
) -> None:
    assert ced.markdown_double_hyphen_hits(text) == hits


def test_a_block_behind_marks_is_no_list_item() -> None:
    assert ced.markdown_bullet_hyphen_hits("> ```\n> - `x` - text\n> ```\n") == []
    assert ced.markdown_bullet_hyphen_hits("> $$\n> - `x` - text\n> $$\n") == []
    after = "- $$\n  a\n  $$\n- `x` - text\n"
    assert ced.markdown_bullet_hyphen_hits(after) == [4]


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("a `b {dash} c\n---\nd` e\n", id="a rule"),
        pytest.param("a `b {dash} c\n***\nd` e\n", id="a rule of asterisks"),
        pytest.param("a `b {dash} c\n===\nd` e\n", id="a setext underline"),
        pytest.param("> a `b {dash} c\n> ---\n> d` e\n", id="a rule of a quotation"),
        pytest.param("a `b {dash} c\n<!-- x -->\nd` e\n", id="a comment"),
        pytest.param("- a `b {dash} c\n    - d` e\n", id="a nested item"),
    ],
)
def test_nothing_pairs_across_a_line_that_ends_the_paragraph(text: str) -> None:
    """Each of them ends the paragraph, so the backticks are text and the dash prose."""
    assert ced.markdown_hits(text.format(dash="—")) == [1]
    assert ced.markdown_double_hyphen_hits(text.format(dash="--")) == [1]


def test_an_item_nested_under_a_reference_is_read_for_itself() -> None:
    assert ced.markdown_hits("- Author (2001) x\n    - item — y\n") == [2]
    assert ced.markdown_hits("- Author (2001) x\n    ## Heading — y\n") == [2]
    assert ced.markdown_hits("- Author (2001) x\n      - wrapped — y\n") == []


def test_an_escaped_backtick_opens_no_code_span() -> None:
    r"""``\`x -- y\``` is prose a reader sees, backticks and all.

    A backslash shows the backtick after it and opens nothing, so the double
    hyphen between two escaped backticks is published as a dash. The page
    reader counted every backtick as a code marker and hid it. Inside a span
    a backslash escapes nothing, so a span still closes on a backtick behind
    one (``%APPDATA%\phonometry\``), and the prose after it is read.
    """
    assert ced.markdown_double_hyphen_hits("Write \\`x -- y\\` here.\n") == [1]
    assert ced.markdown_hits("Write \\`x — y\\` here.\n") == [1]
    closed = "Kept in `%APPDATA%\\phonometry\\` -- and read.\n"
    assert ced.markdown_double_hyphen_hits(closed) == [1]
    assert ced.markdown_double_hyphen_hits("Kept in `a\\` b --x` here.\n") == [1]


def test_a_maths_span_closes_on_a_dollar_behind_a_backslash() -> None:
    r"""Inside ``$...$`` a backslash escapes nothing, as inside a code span.

    remark-math closes the span on the next dollar sign, so ``$a\$`` is the
    whole of it and the prose after it is shown; the page reader took the
    dollar behind the backslash for an escaped one and ran the span on.
    """
    assert ced.markdown_double_hyphen_hits("Set $a\\$ -- and $b$ here.\n") == [1]
    assert ced.markdown_double_hyphen_hits("Costs \\$5 -- \\$10.\n") == [1]


def test_a_link_fragment_keeps_the_double_hyphen_of_its_slug() -> None:
    text = (
        "See [the bands](#octave-band-frequencies-ansi-s111--iec-61260) and\n"
        "<https://example.org/a--b>, or https://example.org/c--d.\n"
        "[ref]: https://example.org/e--f\n"
    )
    assert ced.markdown_double_hyphen_hits(text) == []


def test_an_html_comment_is_not_shown() -> None:
    text = "<!-- generated,\ndo not edit -->\nThe level rises.\n"
    assert ced.markdown_double_hyphen_hits(text) == []


def test_a_style_attribute_is_not_prose() -> None:
    text = '<span style="color: var(--sl-color-accent)">a</span>\n'
    assert ced.markdown_double_hyphen_hits(text) == []


@pytest.mark.parametrize(
    ("text", "mdx", "hits"),
    [
        pytest.param("`http://x` `--y`\n", False, [], id="a URL closes no later span"),
        pytest.param(
            "Polled `http://localhost`. Then\nand `--ignore-lock`, which.\n",
            False,
            [],
            id="nor one its paragraph wraps to",
        ),
        pytest.param(
            "See `http://x` then -- here and `y`.\n",
            False,
            [1],
            id="nor hides the prose after it",
        ),
        pytest.param(
            "Write `<!--` then -- here and `-->`.\n", False, [1], id="a comment"
        ),
        pytest.param(
            "Write `{/*` then -- here and `*/}`.\n", True, [1], id="an MDX comment"
        ),
        pytest.param("`<http://a` -- here `b>`\n", False, [1], id="an autolink"),
        pytest.param('`href="` -- here `"`\n', False, [1], id="an attribute"),
        pytest.param("Write `f[0](`--`)` here.\n", False, [1], id="a link destination"),
        pytest.param(
            "Run `a\n[x]: y` -- here `b`.\n", False, [2], id="a reference definition"
        ),
    ],
)
def test_what_a_code_span_holds_is_code_whatever_it_spells(
    text: str, *, mdx: bool, hits: list[int]
) -> None:
    """A URL, a link destination, a comment or an attribute inside a span is code.

    The site reads a line from left to right, and the construct that opens
    first wins: a code span that opens on a backtick holds what its runs
    enclose, whatever it spells. The guard blanked the addresses and the
    comments of a page before it read its spans, so a URL took the backtick
    that closed its span, and each span after it paired with the wrong run:
    a later option (``--ignore-lock``) read as prose, and the prose between
    two spans read as code.
    """
    assert ced.markdown_double_hyphen_hits(text, mdx=mdx) == hits


@pytest.mark.parametrize(
    ("text", "mdx", "hits"),
    [
        pytest.param("<http://a`b> -- here `c`\n", False, [1], id="an autolink"),
        pytest.param("[a](/f`b) -- here `c`\n", False, [1], id="a link destination"),
        pytest.param("http://x`y -- z `w`\n", False, [1], id="a URL"),
        pytest.param(
            "See http://x<!-- an -- aside --> here.\n", False, [], id="up to a `<`"
        ),
        pytest.param("<!-- ` --> then -- here `x`.\n", False, [1], id="a comment"),
        pytest.param('<A href="`" /> -- here `b`\n', True, [1], id="an attribute"),
        pytest.param(
            "{ /* old -- wording */ }\nShown.\n", True, [], id="a spaced MDX comment"
        ),
        pytest.param(
            "{ /*\nold -- wording\n\nmore -- old\n*/ }\nShown -- prose.\n",
            True,
            [6],
            id="one that runs over a blank line",
        ),
    ],
)
def test_a_construct_that_opens_first_holds_its_backtick(
    text: str, *, mdx: bool, hits: list[int]
) -> None:
    """An address or a comment that opens before a backtick holds it, as the site reads it.

    The backtick is the URL's, the destination's, the comment's or the
    attribute's, and opens no span that would hide the prose after it. A URL
    ends where GFM ends a bare one, at a blank or a ``<``, so the comment after
    it is a comment. MDX shows nothing of an expression that holds only a
    comment, the blanks around it included.
    """
    assert ced.markdown_double_hyphen_hits(text, mdx=mdx) == hits


@pytest.mark.parametrize("mdx", [False, True])
def test_a_comment_opener_in_a_code_span_hides_no_list_item(*, mdx: bool) -> None:
    """A code span that spells a comment's opener opens no comment.

    The guard blanked a page's comments before anything else, so the opener
    in the head of one item and the closer in the head of the next hid both
    items, and the hyphen that joins each head to its text with them.
    """
    opener, closer = ("{/*", "*/}") if mdx else ("<!--", "-->")
    text = f"* `{opener}` - the opener.\n* `{closer}` - the closer.\n"
    assert ced.markdown_bullet_hyphen_hits(text, mdx=mdx) == [1, 2]


def test_rules_and_an_empty_cell_are_not_dashes() -> None:
    text = "---\ntitle: A page\n---\n\n| a | b |\n|---|---|\n| x | -- |\n\n---\n"
    assert ced.markdown_double_hyphen_hits(text) == []


def test_a_double_hyphen_beside_a_cell_value_is_prose() -> None:
    assert ced.markdown_double_hyphen_hits("| a | 2 -- 3 |\n") == [1]


def test_a_docstring_bullet_with_a_double_hyphen_is_refused() -> None:
    """The defect the reading was written against, as the module printed it."""
    text = (
        '"""Airport noise.\n'
        "\n"
        "* :func:`npd_level` -- the interpolated event level ``L(P, d)``.\n"
        '"""\n'
    )
    assert ced.python_double_hyphen_hits(text) == [3]


def test_a_docstring_line_that_opens_or_closes_on_the_dash_is_refused() -> None:
    text = '"""A list of steps\n-- climb, accelerate --\nand coefficients."""\n'
    assert ced.python_double_hyphen_hits(text) == [2]


def test_a_docstring_keeps_the_double_hyphen_of_its_code() -> None:
    text = (
        '"""Write with ``flac --keep-foreign-metadata``, :option:`--count` and\n'
        "``a\n"
        "--b``.\n"
        "\n"
        "Parameters\n"
        "----------\n"
        "x : float\n"
        "    The level.\n"
        "\n"
        "Run it as::\n"
        "\n"
        "    make audit -- --only\n"
        "\n"
        ".. code-block:: bash\n"
        "\n"
        "    python x.py --count -- y\n"
        "\n"
        ">>> run('--count')\n"
        "'--'\n"
        '"""\n'
    )
    assert ced.python_double_hyphen_hits(text) == []


def test_a_literal_of_a_docstring_stays_inside_its_block() -> None:
    """A docstring's literal pairs as a page's code span does, a block at a time.

    Read a paragraph at a time, the two marks of a literal left open paired
    across list items, and the double hyphen between them passed as code
    where the page generated from the docstring shows it.
    """
    item = '"""Summary.\n\n* ``open\n* a -- b`` shown.\n"""\n'
    assert ced.python_double_hyphen_hits(item) == [4]
    nested = '"""Summary.\n\n    * ``open\n    * a -- b`` shown.\n"""\n'
    assert ced.python_double_hyphen_hits(nested) == [4]
    wrapped = '"""Summary.\n\n* ``open\n  --b`` shown.\n"""\n'
    assert ced.python_double_hyphen_hits(wrapped) == []


def test_a_stray_backtick_of_a_string_hides_no_dash_of_a_later_paragraph() -> None:
    text = '"""A stray ` here.\n\nThe level rises — and a ` there.\n"""\n'
    assert ced.python_hits(text) == [3]
    assert ced.python_hits('"""A ``wrapped —\nliteral`` here.\n"""\n') == []


def test_a_note_is_prose() -> None:
    """A directive's body is code only for a code or math directive."""
    text = '"""Summary.\n\n.. note::\n    The level rises -- and falls.\n"""\n'
    assert ced.python_double_hyphen_hits(text) == [4]


def test_any_other_string_is_read_for_the_spaced_dash_only() -> None:
    text = (
        "MESSAGE = 'the level rises -- and falls'\n"
        "ARGV = ['flac', '--keep-foreign-metadata', '--', 'out.flac']\n"
        "print(f'--- Generating {clip} ---')\n"
    )
    assert ced.python_double_hyphen_hits(text) == [1]


def test_a_comment_is_not_published() -> None:
    text = "# -- names -----------------\nx = 1  # the level -- in dB\n"
    assert ced.python_double_hyphen_hits(text) == []


def test_a_generator_docstring_is_not_read_but_its_strings_are() -> None:
    """A figure script publishes what it draws, not what it documents."""
    text = '"""Both paths end here -- the pool too."""\nLABEL = "a -- b"\n'
    assert ced.python_double_hyphen_hits(text, docstrings=False) == [2]


def test_only_the_package_docstrings_are_read(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The API reference is generated from the package, and from nothing else."""
    package = tmp_path / "src" / "phonometry"
    package.mkdir(parents=True)
    monkeypatch.setattr(ced, "_PACKAGE", package)
    text = '"""Drawn here -- or not."""\n'
    inside = package / "airport_noise.py"
    outside = tmp_path / "figure.py"
    inside.write_text(text, encoding="utf-8")
    outside.write_text(text, encoding="utf-8")
    assert ced.scan_double_hyphens(inside) == [1]
    assert ced.scan_double_hyphens(outside) == []


def test_a_data_module_is_read_for_the_spaced_dash(tmp_path: pathlib.Path) -> None:
    page = tmp_path / "home.ts"
    page.write_text(
        "// A comment keeps it -- nobody reads it.\n"
        "export const NOTE = 'One call -- and the figure is drawn.';\n"
        "export const STYLE = 'color: var(--sl-color-accent)';\n"
        "for (let i = 9; i > 0; i--) {}\n",
        encoding="utf-8",
    )
    assert ced.scan_double_hyphens(page) == [2]


def test_a_json_string_is_read_for_the_spaced_dash(tmp_path: pathlib.Path) -> None:
    notes = tmp_path / "catalogue-es.json"
    notes.write_text(
        '{\n  "empty": "--",\n  "note": "la tabla -- sin cifra"\n}\n',
        encoding="utf-8",
    )
    assert ced.scan_double_hyphens(notes) == [3]


# The single spaced hyphen after a list item's head: the same bullet spelt with
# one hyphen. It is read in that one place, where it cannot be a minus; 35
# list items of eight modules carried it, and five API pages showed the two
# bullet forms side by side.


def test_a_docstring_list_item_joined_by_a_spaced_hyphen_is_refused() -> None:
    text = (
        '"""Entry points.\n'
        "\n"
        "* :func:`noise_signal` - Gaussian noise.\n"
        "* ``peaking`` - the bell of a parametric EQ.\n"
        "* ``lowshelf`` / ``highshelf`` - shelving filters.\n"
        "* **ISO 2631-1:1997** - whole-body vibration.\n"
        "* ``'gcc'`` (Knapp & Carter) - the generalized correlation.\n"
        "1. ``first`` -\n"
        "   the text on the next line.\n"
        '"""\n'
    )
    assert ced.python_bullet_hyphen_hits(text) == [3, 4, 5, 6, 7, 8]


def test_a_spaced_hyphen_that_is_not_after_the_head_is_not_read() -> None:
    """A minus inside a role, a hyphen in the text and a bullet with a colon stand."""
    text = (
        '"""Thresholds.\n'
        "\n"
        "* :math:`445.2 F^{-0.05401} - 344.3` for :math:`0.5 \\\\le F < 11.3`,\n"
        "* ``q``: the quality factor, :math:`1 - x` at most,\n"
        "* ``bw``-based spacing,\n"
        "The ``x`` - y line is not a list item.\n"
        "\n"
        "Run it as::\n"
        "\n"
        "    * ``x`` - shown as code\n"
        '"""\n'
    )
    assert ced.python_bullet_hyphen_hits(text) == []


def test_a_page_list_item_joined_by_a_spaced_hyphen_is_refused() -> None:
    text = (
        "* [noise_signal](/reference/api/signals/) - Gaussian noise.\n"
        "- `peaking` - the bell.\n"
        "* **ISO 8041-1:2017** - the master definition.\n"
        "* `q`: the quality factor.\n"
        "\n"
        "```text\n"
        "* `x` - shown as code\n"
        "```\n"
    )
    assert ced.markdown_bullet_hyphen_hits(text) == [1, 2, 3]


def test_a_comment_the_page_does_not_show_is_not_read_for_the_hyphens(
    tmp_path: pathlib.Path,
) -> None:
    """A comment is published nowhere, so neither hyphen reading reads it.

    An HTML comment, an MDX comment on an MDX page and a comment of the
    frontmatter are not shown, and their lines keep their place; a markdown
    page shows an MDX comment as written, a hash inside a quoted value of the
    frontmatter opens no comment, and a frontmatter never closed is none.
    """
    head = (
        "---\n"
        "title: A page\n"
        "# Kept as written -- the page does not show it.\n"
        "description: A guide # and its comment -- not shown\n"
        'summary: "Not # a comment -- shown"\n'
        "---\n"
    )
    body = (
        "<!--\n"
        "* `x` - an old wording -- kept\n"
        "-->\n"
        "Text <!-- an aside -- on its line --> goes on.\n"
        "{/*\n"
        "* `y` - an old wording -- kept\n"
        "*/}\n"
        "* `z` - shown wording\n"
        "Shown -- prose.\n"
    )
    mdx = tmp_path / "page.mdx"
    md = tmp_path / "page.md"
    mdx.write_text(head + body, encoding="utf-8")
    md.write_text(head + body, encoding="utf-8")
    assert ced.scan_double_hyphens(mdx) == [5, 15]
    assert ced.scan_bullet_hyphens(mdx) == [14]
    assert ced.scan_double_hyphens(md) == [5, 12, 15]
    assert ced.scan_bullet_hyphens(md) == [12, 14]
    # A page that opens on a rule no later line closes has no frontmatter, so
    # its heading is no comment.
    assert ced.markdown_double_hyphen_hits("---\n# A heading -- shown\n") == [2]


def test_only_the_package_docstrings_and_the_pages_are_read_for_the_bullet(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "src" / "phonometry"
    package.mkdir(parents=True)
    monkeypatch.setattr(ced, "_PACKAGE", package)
    text = '"""Entry points.\n\n* ``x`` - the level.\n"""\n'
    inside = package / "zwicker.py"
    outside = tmp_path / "figure.py"
    page = tmp_path / "page.md"
    inside.write_text(text, encoding="utf-8")
    outside.write_text(text, encoding="utf-8")
    page.write_text("* `x` - the level.\n", encoding="utf-8")
    assert ced.scan_bullet_hyphens(inside) == [3]
    assert ced.scan_bullet_hyphens(outside) == []
    assert ced.scan_bullet_hyphens(page) == [1]
    assert ced.findings(inside) == [
        (3, "spaced hyphen as a dash after a list item's head")
    ]


# Math on a page: remark-math takes ``$...$`` and a ``$$`` block before
# smartypants sees the text, so a double hyphen there is TeX, as it is in the
# ``:math:`` role the API generator turns into it.


def test_math_on_a_page_keeps_its_double_hyphen() -> None:
    text = (
        "The term $c^{--}$ here.\n"
        "\n"
        "$$\n"
        "a -- b\n"
        "$$\n"
        "\n"
        "It costs \\$5 -- or \\$6, which is prose.\n"
    )
    assert ced.markdown_double_hyphen_hits(text) == [7]


def test_a_display_math_fence_opens_inside_a_code_span_left_open() -> None:
    """The structure of the blocks comes before the spans inside them.

    remark-math opens the block on the ``$$`` line and shows the rest as
    maths, so the backtick on the far side of it closes nothing and the dash
    there is shown, as a fenced code block does in the same place.
    """
    assert ced.markdown_hits("Write `a\n$$\nb — c` here.\n") == [3]
    assert ced.markdown_double_hyphen_hits("Write `a\n$$\nb -- c` here.\n") == []


def test_a_display_math_block_closes_only_on_a_fence_of_its_own() -> None:
    """Only a run as long as the opening one, with nothing after it, closes a block.

    The reader closed on any line of two dollar signs, as remark-math does
    not, so a line of the block was read as prose and the true closing fence
    opened a block that hid the rest of the page.
    """
    text = "$$\na\n$$ b\nc -- d\n$$\nThe level rises -- and falls.\n"
    assert ced.markdown_double_hyphen_hits(text) == [6]
    longer = "$$$\na\n$$\nc -- d\n$$$\nThe level rises -- and falls.\n"
    assert ced.markdown_double_hyphen_hits(longer) == [6]
    shut = "$$\na\n$$$  \nThe level rises -- and falls.\n"
    assert ced.markdown_double_hyphen_hits(shut) == [4]


def test_a_math_span_does_not_cross_into_the_next_list_item() -> None:
    """The site reads a span within one block, and a list item is a block.

    Read a paragraph at a time, the dollar sign of one item paired with the
    one of the next, and the double hyphen between them was taken for maths
    where the site publishes it as an em dash.
    """
    text = "- The kit costs $5 -- the case included.\n- The spare costs $6.\n"
    assert ced.markdown_double_hyphen_hits(text) == [1]


def test_a_docstring_and_its_page_read_the_same() -> None:
    """One docstring, read as written and as the API generator publishes it.

    A construct the docstring reader exempts as code has to reach the page
    as code, or a contributor who followed the rule gets a red on the page
    that no change to the docstring can clear.
    """
    import generate_api_docs as gad

    cases = {
        "literal block": ("Run it as::\n\n    make audit -- --only\n", False),
        "code directive": (
            ".. code-block:: bash\n   :linenos:\n\n   python x.py --count -- y\n",
            False,
        ),
        "doctest": (">>> run('--count')\n'--'\n", False),
        "code directive that shows a fence": (
            ".. code-block:: markdown\n\n   ```bash\n   ls\n   ```\n\n"
            "   python x.py --count\n",
            False,
        ),
        "math directive": (".. math::\n\n   a -- b\n", False),
        "math role": ("The term :math:`c^{--}` here.\n", False),
        "prose": ("The level rises -- and falls.\n", True),
        "note": (".. note::\n   The level rises -- and falls.\n", True),
    }
    for name, (body, refused) in cases.items():
        docstring = "Summary.\n\n" + body
        in_docstring = bool(ced.python_double_hyphen_hits(f'"""{docstring}"""\n'))
        page = gad.render_prose(docstring, {}, gad.RoleStats())
        on_page = bool(ced.markdown_double_hyphen_hits(page))
        assert (in_docstring, on_page) == (refused, refused), name
    bullet = "Summary.\n\n* ``peaking`` - the bell.\n"
    page = gad.render_prose(bullet, {}, gad.RoleStats())
    assert ced.python_bullet_hyphen_hits(f'"""{bullet}"""\n') == [3]
    assert ced.markdown_bullet_hyphen_hits(page) == [3]


# The other spellings of the character: an entity on a page or in a string,
# an escape in a string literal. Each publishes the em dash itself.


def test_an_entity_of_the_dash_on_a_page_is_the_dash() -> None:
    text = (
        "The level rises &mdash; and falls.\n"
        "The level rises &#8212; and falls.\n"
        "The level rises &#x2014; and falls.\n"
        "Written as `&mdash;` in code.\n"
    )
    assert ced.markdown_hits(text) == [1, 2, 3]


def test_an_escape_in_the_frontmatter_is_the_dash() -> None:
    """YAML decodes the escape in a double-quoted value; the body shows it as written."""
    text = (
        "---\n"
        'title: "Acoustics \\u2014 Part 2: rooms"\n'
        'description: "The level rises \\u2014 and falls."\n'
        "---\n"
        "Written as \\u2014 in the body.\n"
    )
    assert ced.markdown_hits(text) == [3]


def test_an_escape_in_the_frontmatter_is_read_only_where_it_is_decoded() -> None:
    r"""YAML decodes the escape in a double-quoted value, and nowhere else.

    A single-quoted or a plain value, a block of text and a comment keep the
    backslash, an escaped backslash is a backslash, and ``\N`` is YAML's
    next-line character, not Python's named escape. The JSON-LD that a
    ``content`` block of the head hands a search engine is JSON, which
    decodes the escape in its strings.
    """
    shown = (
        "---\n"
        "description: 'Write \\u2014 to get the character.'\n"
        'summary: Write \\u2014 or "\\u2014" to get it.\n'
        'note: "Write \\\\u2014 to get it."\n'
        'aside: "A next line \\N{EM DASH} here."\n'
        "keywords: ['rises \\u2014 falls', plain \\u2014 item]\n"
        "# Write \\u2014 to get it.\n"
        "body: |\n"
        "  Write \\u2014 to get it.\n"
        "---\n"
        "Written as \\u2014 in the body.\n"
    )
    assert ced.markdown_hits(shown) == []
    decoded = (
        "---\n"
        'description: "The level rises \\u2014 and falls."\n'
        'summary: "The level rises \\U00002014 and falls."\n'
        'lead: "The level rises\n'
        '  \\u2014 and falls."\n'
        "head:\n"
        "  - tag: script\n"
        "    content: |\n"
        '      {"description": "The level rises \\u2014 and falls."}\n'
        "---\n"
    )
    assert ced.markdown_hits(decoded) == [2, 3, 5, 9]


def test_an_escaped_backslash_or_another_escape_is_not_the_dash(
    tmp_path: pathlib.Path,
) -> None:
    r"""``\\u2014`` is a backslash and five characters, ``\u00002014`` a NUL and four digits.

    The letter of an escape is read as written, and a backslash escapes the
    character after it, in an f-string and in a data module as in any
    string Python evaluates.
    """
    text = (
        'A = f"{x} \\\\u2014 stays six characters"\n'
        'B = f"{x} \\u00002014 is a NUL and four digits"\n'
        'C = f"{x} \\u2014 is the dash"\n'
    )
    assert ced.python_hits(text) == [3]
    home = tmp_path / "home.ts"
    home.write_text(
        "export const A = 'a \\\\u2014 b';\n"
        "export const B = 'a \\u00002014 b';\n"
        "export const C = 'a \\U2014 b';\n"
        "export const D = 'a \\u2014 b';\n",
        encoding="utf-8",
    )
    assert ced.scan(home) == [4]


def test_an_escape_or_entity_in_a_python_string_is_the_dash() -> None:
    text = (
        'ESCAPE = "the level rises \\u2014 and falls"\n'
        'NAMED = "the level rises \\N{EM DASH} and falls"\n'
        'LONG = "the level rises \\U00002014 and falls"\n'
        'ENTITY = "the level rises &mdash; and falls"\n'
        'RAW = r"\\u2014 stays six characters"\n'
        'EMPTY = "&#8212;"\n'
        'FORMATTED = f"the level {x} \\u2014 falls"\n'
        'RAW_FORMATTED = rf"\\u2014 {x} stays"\n'
    )
    assert ced.python_hits(text) == [1, 2, 3, 4, 7]


def test_an_escape_in_a_json_string_or_a_data_module_is_the_dash(
    tmp_path: pathlib.Path,
) -> None:
    notes = tmp_path / "catalogue-es.json"
    notes.write_text(
        "{\n"
        '  "note": "la tabla \\u2014 sin cifra",\n'
        '  "empty": "\\u2014",\n'
        '  "html": "la tabla &mdash; sin cifra"\n'
        "}\n",
        encoding="utf-8",
    )
    assert ced.scan(notes) == [2, 4]
    home = tmp_path / "home.ts"
    home.write_text(
        "// A comment keeps it \\u2014 nobody reads it.\n"
        "export const NOTE = 'One call \\u2014 and the figure is drawn.';\n"
        "export const WIDE = 'One call \\u{2014} and the figure is drawn.';\n",
        encoding="utf-8",
    )
    assert ced.scan(home) == [2, 3]


def test_a_data_module_is_read_with_the_escapes_of_javascript(
    tmp_path: pathlib.Path,
) -> None:
    r"""``\U00002014`` and ``\N{EM DASH}`` are Python's, not JavaScript's.

    JavaScript reads ``\U`` and ``\N`` as the letters themselves, so a
    string that writes either publishes the letters and digits, never the
    dash; the data reader decoded them with Python's escapes and refused a
    string that publishes none.
    """
    labels = tmp_path / "labels.mjs"
    labels.write_text(
        "export const LONG = 'Write \\U00002014 here';\n"
        "export const NAMED = 'Write \\N{EM DASH} here';\n"
        "export const SHORT = 'Write \\u2014 here';\n",
        encoding="utf-8",
    )
    assert ced.scan(labels) == [3]


def test_a_clean_run_names_every_form_it_refuses(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A green run once named two of the three forms the guard refuses."""
    page = tmp_path / "page.md"
    page.write_text("* ``peaking``: the bell of a parametric EQ.\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check_em_dashes.py", str(page)])
    assert ced.main() == 0
    said = capsys.readouterr().out
    assert "em dash" in said
    assert "double hyphen" in said
    assert "list item's head" in said


def test_a_code_span_across_a_line_break_hides_its_dash() -> None:
    """A dash inside a code span that crosses a line break is code.

    The spans were dropped one line at a time, so the first line kept its
    opening backtick and the dash after it as prose.
    """
    assert ced.markdown_hits("Text `a —\nb` more.\n") == []
