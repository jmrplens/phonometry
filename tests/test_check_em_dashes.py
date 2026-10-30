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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
