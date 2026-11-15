#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The decimal comma gate, held against every case it keeps and every case it refuses.

``scripts/check_decimal_comma.py`` holds the rule of 2026-11-15: in English
text every decimal number the text writes itself takes a point, a value
restated from a standard that prints a comma among them, and the comma stays
only in a literal transcription of the print (text in quotation marks, a
block quote, the print field of an errata entry, the printed column of the
conformance report) and in Spanish. A comma that is no decimal at all is left
alone wherever it stands: a thousands group, a list, code and notation.

The gate can go wrong both ways, so each kept class and each refused class
has a planted case of its own, in every kind of file the rule reaches:
Markdown and MDX read by their structure, Python read by its tokens and its
tree, JavaScript and JSON read by their strings and keys, and the comments of
the configuration files. The second half is the older check of the same
script, the Spanish figure label that would keep an English point.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_decimal_comma as gate


def _decimals(text: str, rel: str = "docs/page.md") -> list[str]:
    """The tokens the gate refuses in *text*, read as the file *rel*."""
    return [f.token for f in gate.findings_in(text, rel) if f.kind == "decimal"]


def _ambiguous(text: str, rel: str = "docs/page.md") -> list[str]:
    """The tokens the gate reports for a person to decide."""
    return [f.token for f in gate.findings_in(text, rel) if f.kind == "ambiguous"]


# ---------------------------------------------------------------------------
# Refused: a decimal comma the English text writes itself.
# ---------------------------------------------------------------------------


def test_a_decimal_of_our_own_prose_is_refused() -> None:
    assert _decimals("The level is 0,5 dB at the receiver.\n") == ["0,5"]


def test_a_value_restated_from_a_print_is_refused() -> None:
    """The case the old F58 licensed: a printed value restated outside quotes."""
    text = "ISO 9613-1 prints 2,2560 per metre for the coefficient a.\n"
    assert _decimals(text) == ["2,2560"]


def test_a_latex_decimal_comma_in_maths_is_refused() -> None:
    assert _decimals("The print gives $a = 2{,}256 \\times 10^{-5}$.\n") == ["2{,}256"]


def test_a_decimal_in_display_maths_is_refused() -> None:
    text = "Then\n\n$$\nL = 83{,}5\\ \\text{dB}\n$$\n\nso it holds.\n"
    assert _decimals(text) == ["83{,}5"]


def test_a_grouped_decimal_is_refused_as_one_number() -> None:
    assert _decimals("The sum is 83,523\u202f38 dB.\n") == ["83,523"]


def test_a_decimal_in_the_frontmatter_is_refused() -> None:
    text = '---\ntitle: "Levels"\ndescription: A floor of 0,5 m.\n---\n\nBody.\n'
    assert _decimals(text, "site/src/content/docs/x.mdx") == ["0,5"]


def test_a_decimal_in_a_prose_attribute_is_refused() -> None:
    text = '<ThemeImage src="a.svg" alt="The field at 0,25 m from the wall" />\n'
    assert _decimals(text, "site/src/content/docs/x.mdx") == ["0,25"]


def test_a_decimal_in_a_callout_is_refused() -> None:
    """A block quote that opens on a label is a note of ours, not the print."""
    text = "> **The page rule.** A ratio within 0,5 % of pi is a lost glyph.\n"
    assert _decimals(text) == ["0,5"]
    assert _decimals("> [!NOTE]\n> Keep 0,5 % of margin.\n") == ["0,5"]


def test_an_errata_field_of_our_own_is_refused() -> None:
    text = (
        "## ISO 717-2:2020, Annex C\n\n"
        "- **The print:** $L = 83{,}523\\,8$ dB.\n"
        "- **The problem:** the column sums to 83,523 4 dB, not the printed 83,8.\n"
    )
    assert _decimals(text, "docs/ERRATA.md") == ["83,523", "83,8"]


def test_a_comment_in_a_python_fence_is_prose() -> None:
    text = "```python\nlevel = band(1.5)  # 0,5 dB above the floor\n```\n"
    assert _decimals(text) == ["0,5"]


def test_a_computed_column_of_the_conformance_report_is_refused() -> None:
    text = (
        "| Standard | Quantity | Expected (norm) | Computed |\n"
        "|:---|:---|:---|:---|\n"
        "| ISO 1 | Level at 0,5 m | 2,9 d fails | 2,9 d fails |\n"
    )
    assert _decimals(text, "docs/CONFORMANCE.md") == ["0,5", "2,9"]


def test_a_python_docstring_comment_and_message_are_refused() -> None:
    source = (
        '"""Module of 0,5 dB steps."""\n'
        "\n"
        "# a step of 0,25 dB\n"
        'msg = "temperature must be above -273,15 degC"\n'
        "x = (1,5)\n"
    )
    assert _decimals(source, "src/phonometry/x.py") == ["0,5", "0,25", "273,15"]


def test_the_line_of_a_python_finding_is_the_line_it_is_written_on() -> None:
    source = 'msg = (\n    f"a {name} of "\n    "6,5 dB"\n)\n'
    (finding,) = gate.findings_in(source, "src/phonometry/x.py")
    assert (finding.token, finding.line) == ("6,5", 3)


def test_an_f_string_literal_part_is_refused() -> None:
    assert _decimals('label = f"{value} at 0,5 m"\n', "scripts/figures/x.py") == ["0,5"]


def test_an_english_label_key_of_a_translation_table_is_refused() -> None:
    source = (
        "_ES = {\n"
        '    "Wall at 0,25 m": "Pared a 0,25 m",\n'
        '    "Floor level": "Nivel del suelo",\n'
        '    "Room of the test": "Sala del ensayo",\n'
        "}\n"
    )
    assert _decimals(source, "scripts/diagrams/i18n.py") == ["0,25"]


def test_a_conformance_row_description_is_refused() -> None:
    source = 'Row(quantity="Level of a 0,5 s burst", expected="83,5 dB", computed=x)\n'
    assert _decimals(source, "scripts/conformance/domains/x.py") == ["0,5"]


def test_a_test_docstring_and_comment_are_refused() -> None:
    source = (
        "def test_x():\n"
        '    """The floor at 0,5 m."""\n'
        "    # and 1,5 more\n"
        '    assert f("2,5") == 1\n'
    )
    assert _decimals(source, "tests/test_x.py") == ["0,5", "1,5"]


def test_a_javascript_string_and_comment_are_refused() -> None:
    source = (
        "// the step is 0,1 dB\n"
        'export const glossary = { text: "falls below 0,50 beyond it" };\n'
    )
    assert _decimals(source, "site/src/data/glossary.mjs") == ["0,1", "0,50"]


def test_a_json_string_of_a_catalogue_is_refused() -> None:
    text = '{\n  "about": "Held in pascals: 0,84 kg/cm2 is 82 375.86 Pa."\n}\n'
    assert _decimals(text, "src/phonometry/building/data/t.json") == ["0,84"]


def test_a_configuration_comment_is_refused() -> None:
    assert _decimals(
        "# within 2,6 per cent\nrun: x 1,5\n", ".github/workflows/a.yml"
    ) == ["2,6"]
    assert _decimals("# lasts 0,5 s\nall:\n", "Makefile") == ["0,5"]


# ---------------------------------------------------------------------------
# Kept: a literal transcription of the print.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "quoted",
    [
        "the page reads \u201cthe flux density is 1,256 \u00b5T\u201d here",
        'the page reads "a = 2,2560" here',
        "the page reads \u2018a = 2,2560\u2019 here",
        "the page reads \u00aba = 2,2560\u00bb here",
        "a quoted '<0,02 above 200 Hz' in the prose",
    ],
)
def test_a_value_in_quotation_marks_is_kept(quoted: str) -> None:
    assert _decimals(quoted + ".\n") == []


def test_a_quotation_wrapped_over_lines_is_kept() -> None:
    text = "The caption reads \u201cvalues at\n0,5 m from the wall\u201d.\n"
    assert _decimals(text) == []


def test_a_block_quote_of_the_print_is_kept() -> None:
    assert _decimals("> The value shall be 0,5 dB or less.\n") == []


def test_the_print_field_of_an_errata_entry_is_kept() -> None:
    text = (
        "## ISO 717-2:2020, Annex C\n\n"
        "- **The print:** $L_{n,\\text{sum}} = 83{,}523\\,8$ and the\n"
        "  continuation line 0,5 dB.\n"
        "- **Status:** open.\n"
    )
    assert _decimals(text, "docs/ERRATA.md") == []


def test_the_printed_column_of_the_conformance_report_is_kept() -> None:
    text = (
        "| Standard | Quantity | Expected (norm) | Computed |\n"
        "|:---|:---|:---|:---|\n"
        "| ISO 1 | Level | 2,9 d fails | 2.9 d fails |\n"
    )
    assert _decimals(text, "docs/CONFORMANCE.md") == []
    source = (
        'Row(quantity="Level", expected="83,5 dB", computed=x)\n'
        'printed_levels = "39,0 / 31,0"\n'
    )
    assert _decimals(source, "scripts/conformance/domains/x.py") == []
    data = (
        '{"checks": [{"expected": {"label": "2,9 d"}, "computed": {"label": "3"}}]}\n'
    )
    assert _decimals(data, "docs/conformance.json") == []


def test_an_apostrophe_quotes_nothing() -> None:
    text = "the tests' level of 0,5 dB, and the user's 1,5 dB.\n"
    assert _decimals(text) == ["0,5", "1,5"]


def test_a_python_string_in_quotes_is_kept() -> None:
    source = "msg = 'the page prints \"0,5 dB\" there'\n# reads '1,5'\n"
    assert _decimals(source, "src/phonometry/x.py") == []


# ---------------------------------------------------------------------------
# Kept: Spanish.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel",
    [
        "site/src/content/docs/es/guide.mdx",
        "docs/ERRATA.es.md",
        "site/src/data/catalogue-es.json",
    ],
)
def test_a_spanish_file_is_never_read(rel: str) -> None:
    assert gate.findings_in("El nivel 0,5 dB.\n", rel) == []


def test_a_spanish_paragraph_in_an_english_page_is_kept() -> None:
    text = "La tabla B.3 de la misma norma da 0,005 para el hormigón.\n"
    assert _decimals(text) == []


def test_the_spanish_values_of_a_translation_table_are_kept() -> None:
    source = (
        "_ES = {\n"
        '    "6.5": "6,5",\n'
        '    "Floor level": "Nivel del suelo",\n'
        '    "Room of the test": "Sala del ensayo",\n'
        "}\n"
    )
    assert _decimals(source, "scripts/diagrams/i18n.py") == []


def test_a_spanish_branch_is_kept() -> None:
    source = (
        'label = "0,5 m del muro" if language == "es" else "0.5 m from the wall"\n'
        'if language == "es":\n'
        '    title = "Paso de 2,5"\n'
        'note = text(en="0.5 dB", es="0,5 dB")\n'
    )
    assert _decimals(source, "src/phonometry/_plot/x.py") == []


def test_a_spanish_key_of_a_javascript_or_json_object_is_kept() -> None:
    source = 'const x = { en: "0.5 dB", es: "0,5 dB", headingEs: "Paso 2,5" };\n'
    assert _decimals(source, "site/src/data/home.ts") == []
    data = '{"name": "Moqueta Wilton, 9,5 mm", "group": "Tabla 19.2. Valores del hormigón"}\n'
    assert _decimals(data, "src/phonometry/building/data/t.json") == []


# ---------------------------------------------------------------------------
# Kept: what is no decimal at all.
# ---------------------------------------------------------------------------


def test_a_thousands_group_is_left_to_the_digit_grouping_rule() -> None:
    assert gate.findings_in("91,658,333 inputs, zero exceptions.\n", "docs/a.md") == []


def test_an_ambiguous_number_is_reported_and_does_not_fail() -> None:
    text = "about 1,500 such comments\n"
    assert _decimals(text) == []
    assert _ambiguous(text) == ["1,500"]


@pytest.mark.parametrize(
    "notation",
    [
        "the list 1,2,3 of bands",
        "the element a[1,2] of the matrix",
        "the pair (1,2) of indices",
        "the quantifier {2,4} of the pattern",
        "the subscript $k_{1,2}$ of the coupling",
        "the index k2,1 of the path",
        "the clauses 5.2,5.3 of the part",
        "the mode (2,1) of the room",
        "the solvent 1,2-DHCP of the table",
        "the corners (0,90), (0,135) and (45,90) of the grid",
    ],
)
def test_lists_and_notation_are_kept(notation: str) -> None:
    assert _decimals(notation + ".\n") == []


@pytest.mark.parametrize(
    ("text", "token"),
    [
        ("the **0,1-quantile** of the differences", "0,1"),
        ("the quantile $q_{0,1}$ of the differences", "0,1"),
        ("the rank R(q0,9) of the sample", "0,9"),
        ("the product (0,05)(900) of the two", "0,05"),
        ("the floor 71,8 (0,0) of the table", "0,0"),
    ],
)
def test_a_decimal_that_looks_like_an_index_is_refused(text: str, token: str) -> None:
    """An index has no leading zero: a bracketed or subscript ``0,1`` is a decimal."""
    assert token in _decimals(text + ".\n")


def test_code_is_kept() -> None:
    text = (
        "The span `Sum 27,9` is code.\n\n"
        "```text\n6,251 5   0,647 829\n```\n\n"
        "```python\nx = f(1,5)\n```\n"
    )
    assert _decimals(text) == []


def test_python_code_is_kept() -> None:
    source = (
        "x = (1,5)\n"
        'pattern = re.compile(r"[0-9],[0-9]")\n'
        'POINTS = "0,0 10,10 20,5"\n'
        "def f():\n"
        '    """Example.\n'
        "\n"
        "    >>> f(1,5)\n"
        "    '1,5'\n"
        "\n"
        "    It reads ``1,5`` and :func:`g` with :math:`x`.\n"
        "    A literal ``:math:`x - 1```, then ``32,3 - 26,3 dB``.\n"
        '    """\n'
    )
    assert _decimals(source, "src/phonometry/x.py") == []


def test_a_string_of_a_test_is_test_data() -> None:
    assert _decimals('assert parse("0,5 dB") == 0.5\n', "tests/test_x.py") == []


def test_a_javascript_test_string_is_test_data() -> None:
    assert _decimals("check('| 125 Hz | 0,1 |');\n", "site/scripts/a.test.mjs") == []


def test_a_dont_example_fence_is_kept() -> None:
    text = "**Don't**\n\n```py\n# a step of 0,5 dB\nx = 1\n```\n"
    assert _decimals(text, "docs/contributing/prose.md") == []


def test_a_data_file_is_never_read() -> None:
    assert gate.findings_in("band,level\n125,0,5\n", "tests/data/x.csv") == []
    assert gate.findings_in("<path d='M0,5'/>\n", "docs/a.svg") == []


def test_a_generated_copy_is_left_to_its_source(tmp_path: pathlib.Path) -> None:
    """The GitHub edition is written from the site page, which is read instead."""
    page = tmp_path / "docs" / "guide.md"
    page.parent.mkdir()
    page.write_text(
        "<!-- Written by `make llms` from site/src/content/docs/guide.mdx -->\n"
        "The level is 0,5 dB.\n",
        encoding="utf-8",
    )
    assert gate.is_copy(page, "docs/guide.md")
    assert not gate.is_copy(tmp_path / "docs" / "other.md", "docs/other.md")


# ---------------------------------------------------------------------------
# The command line.
# ---------------------------------------------------------------------------


def test_the_command_fails_on_a_decimal_and_passes_an_ambiguous_number(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("The level is 0,5 dB.\n", encoding="utf-8")
    good = tmp_path / "good.md"
    good.write_text("About 1,500 comments and 0.5 dB.\n", encoding="utf-8")
    assert gate.main(["--english", str(bad)]) == 1
    assert "0,5" in capsys.readouterr().err
    assert gate.main(["--english", str(good)]) == 0
    assert "1,500" in capsys.readouterr().out
    assert gate.main(["--english", "--strict", str(good)]) == 1


# ---------------------------------------------------------------------------
# The Spanish figure label beside mathematics (rule F29).
# ---------------------------------------------------------------------------


def test_a_spanish_label_beside_maths_keeps_its_point() -> None:
    assert gate.at_risk("$L_\\mathrm{eq}$ = 52.4 dB") is not None
    assert gate.at_risk("$L_\\mathrm{eq}$ = 52,4 dB") is None
    assert gate.at_risk("según el apartado 7.4, $L$") is None
