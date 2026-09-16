#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate against a grouped number a line break can split in two.

``scripts/check_digit_grouping.py`` asks that the space holding the groups of a
long number apart be U+202F, the narrow no-break space, and not an ordinary
one. The hazard is real and invisible in the source: ``6,251 5`` written with a
plain space renders as two numbers whenever the line happens to break there.

The tests that matter most are the negative ones. Two shapes in this tree look
exactly like a grouped number and are not: the printed output of an array,
``0.404 0.512``, where the space separates two values, and a value followed by
its unit, ``0,005 1/m``, where the digit belongs to the unit. A first sweep over
the corpus took both for groupings and corrupted them, which is why the gate
carries the closing conditions it does.
"""

from __future__ import annotations

import pathlib
import sys

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_digit_grouping as gate

NNBSP = gate.NARROW_NO_BREAK_SPACE


def _file(text: str, tmp_path: pathlib.Path) -> pathlib.Path:
    path = tmp_path / "page.md"
    path.write_text(text, encoding="utf-8")
    return path


def test_a_decimal_grouped_with_a_plain_space_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    assert gate._findings(_file("sum to 6,251 5 dB\n", tmp_path)) == [(1, "6,251 5")]


def test_an_integer_grouped_with_a_plain_space_is_refused(
    tmp_path: pathlib.Path,
) -> None:
    """One atmosphere is as breakable as any decimal."""
    assert gate._findings(_file("at 101 325 Pa\n", tmp_path)) == [(1, "101 325")]


def test_the_narrow_no_break_space_passes(tmp_path: pathlib.Path) -> None:
    text = f"sum to 6,251{NNBSP}5 dB at 101{NNBSP}325 Pa\n"
    assert gate._findings(_file(text, tmp_path)) == []


def test_the_printed_output_of_an_array_is_not_a_grouping(
    tmp_path: pathlib.Path,
) -> None:
    """``[0.404 0.512 0.318]`` is three numbers, and joining them would lie."""
    assert gate._findings(_file("print(a)  # [0.404 0.512 0.318]\n", tmp_path)) == []


def test_a_value_followed_by_its_unit_is_not_a_grouping(
    tmp_path: pathlib.Path,
) -> None:
    """In ``0,005 1/m`` the 1 belongs to the unit, not to the number."""
    assert gate._findings(_file("alpha = 0,005 1/m as printed\n", tmp_path)) == []


def test_a_grouping_at_the_end_of_a_sentence_is_still_refused(
    tmp_path: pathlib.Path,
) -> None:
    """A full stop is not a decimal marker, and must not hide the defect."""
    assert gate._findings(_file("the sum is 0,012 5.\n", tmp_path)) == [(1, "0,012 5")]


def test_a_grouping_before_a_comma_is_still_refused(tmp_path: pathlib.Path) -> None:
    assert gate._findings(_file("at 1 000, 2 000 and 4 000 Hz\n", tmp_path)) == [
        (1, "1 000"),
        (1, "2 000"),
        (1, "4 000"),
    ]


def test_a_three_decimal_number_is_left_alone(tmp_path: pathlib.Path) -> None:
    """Grouping starts at four digits; ``0,005`` has nothing to hold apart."""
    assert gate._findings(_file("a of 0,005 and 0.125 alike\n", tmp_path)) == []


def test_the_corpus_is_clean() -> None:
    """The published prose itself, which is what the gate protects."""
    assert gate.main() == 0
