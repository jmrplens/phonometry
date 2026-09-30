#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The gate against mathematics in the sources that KaTeX will refuse.

``scripts/check_docstring_math.py`` reads the *value* of every docstring in the
package rather than the text of the file, because the two kinds of docstring
this tree has spell the same backslash two different ways. The first tests fix
that distinction, which is the reason the check exists: a raw docstring
carrying ``\\mathrm`` is the defect, and a plain one carrying the same four
characters is correct.

The defect it was written for is real. Four parameters of
``room/spatial_decay.py`` carried it, the pages shipped, and the site build was
the only thing that noticed, twelve minutes in.

The second shape is a bare command as a sub- or superscript, ``|dL_n|_\max``,
which KaTeX refuses and the ISO 17534-1 pages carried in five docstrings and
three guides. The tests after the first group fix what the rule reads, a
docstring's mathematics and a page's prose outside code, and what it lets
through bare, a symbol or a font command.
"""

from __future__ import annotations

import pathlib
import sys

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_docstring_math as cdm


def _module(source: str, tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "module.py"
    path.write_text(source, encoding="utf-8")
    return path


def test_a_raw_docstring_with_one_backslash_is_clean(
    tmp_path: pathlib.Path,
) -> None:
    source = 'r"""The rate :math:`\\mathrm{DL}_2` per doubling."""\n'
    assert cdm._findings(_module(source, tmp_path)) == []


def test_a_raw_docstring_with_two_backslashes_is_the_defect(
    tmp_path: pathlib.Path,
) -> None:
    source = 'r"""The rate :math:`\\\\mathrm{DL}_2` per doubling."""\n'
    found = cdm._findings(_module(source, tmp_path))
    assert len(found) == 1
    assert "mathrm" in found[0][1]


def test_a_plain_docstring_with_two_backslashes_is_clean(
    tmp_path: pathlib.Path,
) -> None:
    """Without the ``r`` prefix, two backslashes are how one is written."""
    source = '"""The rate :math:`\\\\mathrm{DL}_2` per doubling."""\n'
    assert cdm._findings(_module(source, tmp_path)) == []


def test_a_plain_docstring_with_four_backslashes_is_the_defect(
    tmp_path: pathlib.Path,
) -> None:
    source = '"""The rate :math:`\\\\\\\\mathrm{DL}_2` per doubling."""\n'
    assert len(cdm._findings(_module(source, tmp_path))) == 1


def test_a_row_break_in_a_display_block_is_not_a_defect(
    tmp_path: pathlib.Path,
) -> None:
    r"""``\\`` ends a row of an aligned block, and a newline follows it."""
    source = 'r"""A block.\n\n.. math::\n\n   a &= b \\\\\n   c &= d\n"""\n'
    assert cdm._findings(_module(source, tmp_path)) == []


def test_every_kind_of_docstring_is_read(tmp_path: pathlib.Path) -> None:
    """Module, class, function and method, since each publishes a page entry."""
    source = (
        'r"""Module :math:`\\\\mathrm{a}`."""\n\n\n'
        'def free() -> None:\n    r"""Function :math:`\\\\mathrm{b}`."""\n\n\n'
        'class Thing:\n    r"""Class :math:`\\\\mathrm{c}`."""\n\n'
        "    def method(self) -> None:\n"
        '        r"""Method :math:`\\\\mathrm{d}`."""\n'
    )
    assert len(cdm._findings(_module(source, tmp_path))) == 4


def test_the_line_reported_is_the_one_the_passage_is_on(
    tmp_path: pathlib.Path,
) -> None:
    source = (
        "def free() -> None:\n"
        '    r"""A summary.\n\n'
        "    :param x: the rate :math:`\\\\mathrm{DL}_2`.\n"
        '    """\n'
    )
    found = cdm._findings(_module(source, tmp_path))
    assert [line for line, _ in found] == [4]


def test_a_bare_operator_as_a_subscript_is_refused(tmp_path: pathlib.Path) -> None:
    """The defect the rule was written for, as the ISO 17534-1 module had it."""
    source = 'r"""The largest :math:`|dL_n|_\\max` at each receiver."""\n'
    found = cdm._bare_scripts(_module(source, tmp_path))
    assert [(line, command) for line, command, _ in found] == [(1, "max")]
    assert "|dL_n|_\\max" in found[0][2]


def test_a_braced_operator_is_clean(tmp_path: pathlib.Path) -> None:
    source = 'r"""The largest :math:`|dL_n|_{\\max}` at each receiver."""\n'
    assert cdm._bare_scripts(_module(source, tmp_path)) == []


def test_a_symbol_or_a_font_command_bare_is_clean(tmp_path: pathlib.Path) -> None:
    """KaTeX takes a single atom or a font command bare, and the corpus uses both."""
    source = (
        'r"""Take :math:`x_\\alpha`, :math:`10^\\circ`, :math:`L_\\infty`,\n'
        ':math:`R_\\mathrm{w}` and :math:`L_\\text{eq}` as written."""\n'
    )
    assert cdm._bare_scripts(_module(source, tmp_path)) == []


def test_every_command_that_wants_an_argument_is_refused() -> None:
    """Operators, accents, a root: each is an error message on the page."""
    tex = r"q_\min + x^\log + y_\bar{a} + z^ \sqrt{2} + w_\operatorname{f}"
    commands = [m.group(1) for m in cdm.bare_script_commands(tex)]
    assert commands == ["min", "log", "bar", "sqrt", "operatorname"]


def test_a_bare_script_in_a_math_block_is_found_on_its_line(
    tmp_path: pathlib.Path,
) -> None:
    source = (
        "def free() -> None:\n"
        '    r"""A summary.\n\n'
        "    .. math::\n\n"
        "       k = 2/(q_\\max + q_\\min)\n"
        '    """\n'
    )
    found = cdm._bare_scripts(_module(source, tmp_path))
    assert [(line, command) for line, command, _ in found] == [(6, "max"), (6, "min")]


def test_prose_outside_the_mathematics_is_not_read(tmp_path: pathlib.Path) -> None:
    r"""A pattern quoted as a literal is not TeX, so its ``^\s`` is nothing."""
    source = 'r"""Split on ``re.compile(r"^\\s+")`` and :math:`x_{\\max}`."""\n'
    assert cdm._bare_scripts(_module(source, tmp_path)) == []


def test_a_page_with_a_bare_operator_is_refused(tmp_path: pathlib.Path) -> None:
    page = tmp_path / "page.mdx"
    page.write_text(
        "The distribution of\n$|dL_n|_\\max$ drawn as the figure.\n", encoding="utf-8"
    )
    found = cdm._page_bare_scripts(page)
    assert [(line, command) for line, command, _ in found] == [(2, "max")]


def test_code_on_a_page_is_not_read(tmp_path: pathlib.Path) -> None:
    """A code span or a fence carries Python, whose strings are not KaTeX's."""
    page = tmp_path / "page.md"
    page.write_text(
        "Write `x_\\max` in a label.\n\n"
        "```python\n"
        'ax.set_ylabel(r"$|dL_n|_\\max$")\n'
        "```\n\n"
        "Then $|dL_n|_{\\max}$ in the prose.\n",
        encoding="utf-8",
    )
    assert cdm._page_bare_scripts(page) == []


def test_a_fence_closes_only_on_its_own_marker(tmp_path: pathlib.Path) -> None:
    """A fence shown inside a tilde fence closes nothing, so what follows is prose."""
    page = tmp_path / "page.md"
    page.write_text("~~~~\n```\nexample\n~~~~\n$|dL_n|_\\max$\n", encoding="utf-8")
    found = cdm._page_bare_scripts(page)
    assert [(line, command) for line, command, _ in found] == [(5, "max")]


def test_the_package_is_clean() -> None:
    """The corpus itself, docstrings and pages, which is what the gate protects."""
    assert cdm.main() == 0
