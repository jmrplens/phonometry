#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which lines of a page are code, the reading every prose check starts from.

``scripts/markdown_fences.py`` closes a fence the way CommonMark does: on a
line of the same character, at least as long as the opening run, with nothing
after it. The defect it replaced closed a fence on any run of three markers,
so a page that shows a fence inside another was read inside out from there
on. The tests fix the cases where the two readings part, and the plain ones
that must not move.
"""

from __future__ import annotations

import pathlib
import sys

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from markdown_fences import code_lines


def _code(text: str) -> list[bool]:
    return list(code_lines(text.splitlines()))


def test_a_plain_fence_is_code_from_its_opening_to_its_closing_line() -> None:
    assert _code("prose\n```python\nx = 1\n```\nprose\n") == [
        False,
        True,
        True,
        True,
        False,
    ]


def test_a_tilde_fence_is_code() -> None:
    assert _code("~~~\nx = 1\n~~~\nprose\n") == [True, True, True, False]


def test_backticks_inside_a_tilde_fence_close_nothing() -> None:
    assert _code("~~~~\n```\nexample\n~~~~\nprose\n") == [True] * 4 + [False]


def test_a_shorter_run_of_the_same_marker_closes_nothing() -> None:
    assert _code("````\n```\nexample\n````\nprose\n") == [True] * 4 + [False]


def test_a_longer_run_of_the_same_marker_closes_the_fence() -> None:
    assert _code("```\nx = 1\n`````\nprose\n") == [True, True, True, False]


def test_a_marker_with_text_after_it_closes_nothing() -> None:
    assert _code("```\n```python\n```\nprose\n") == [True, True, True, False]


def test_a_backtick_run_whose_info_string_holds_a_backtick_is_not_a_fence() -> None:
    assert _code("```a`b\nprose\n") == [False, False]


def test_an_indented_fence_in_a_list_item_is_code() -> None:
    assert _code("- item\n\n    ```\n    x = 1\n    ```\nprose\n") == [
        False,
        False,
        True,
        True,
        True,
        False,
    ]


def test_a_fence_never_closed_runs_to_the_end_of_the_page() -> None:
    assert _code("prose\n```\nx = 1\nmore\n") == [False, True, True, True]
