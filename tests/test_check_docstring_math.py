#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The gate against a docstring whose mathematics reaches KaTeX doubled.

``scripts/check_docstring_math.py`` reads the *value* of every docstring in the
package rather than the text of the file, because the two kinds of docstring
this tree has spell the same backslash two different ways. The tests below fix
that distinction, which is the whole reason the check exists: a raw docstring
carrying ``\\mathrm`` is the defect, and a plain one carrying the same four
characters is correct.

The defect it was written for is real. Four parameters of
``room/spatial_decay.py`` carried it, the pages shipped, and the site build was
the only thing that noticed, twelve minutes in.
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


def test_the_package_is_clean() -> None:
    """The corpus itself, which is what the gate protects."""
    assert cdm.main() == 0
