#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The unclosed-maths rule of ``scripts/check_markdown_hazards.py``.

A ``$`` inside an inline code span is code, and CommonMark reads the span
before any maths could open in it, so the ``$schema`` key of a JSON
document in a table cell opens nothing. The rule has to keep catching the
defect it exists for, maths that wraps onto a block marker, whether or not
the line also holds a code span.
"""

from __future__ import annotations

import pathlib
import sys

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_markdown_hazards as checker  # noqa: E402


def _problems(tmp_path: pathlib.Path, text: str) -> list[str]:
    page = tmp_path / "page.md"
    page.write_text(text, encoding="utf-8")
    original = checker._ROOT
    checker._ROOT = tmp_path
    try:
        return checker._check(page)
    finally:
        checker._ROOT = original


def test_a_dollar_in_a_code_span_opens_no_maths(tmp_path: pathlib.Path) -> None:
    table = (
        "| Key | What it holds |\n"
        "|---|---|\n"
        "| `$schema` | Optional: where an editor finds the schema. |\n"
        "| `rows` | The rows. |\n"
    )
    assert _problems(tmp_path, table) == []


def test_maths_cut_off_by_a_block_marker_is_still_found(tmp_path: pathlib.Path) -> None:
    text = "The index is $L_{n,ij,w} = L_{n,w} - \\Delta R_{j,w}\n- K_{ij}$ in dB.\n"
    problems = _problems(tmp_path, text)
    assert len(problems) == 1
    assert "inline maths opened on line 1" in problems[0]


def test_a_code_span_beside_open_maths_does_not_close_it(
    tmp_path: pathlib.Path,
) -> None:
    text = "Write `$schema` and the level $L_{p,A}\n| a | b |\n"
    problems = _problems(tmp_path, text)
    assert len(problems) == 1
    assert "cut off by a block marker" in problems[0]


def test_counting_skips_escaped_display_and_code_dollars() -> None:
    assert checker._unescaped_dollars("`$a` and ``b $ c`` and \\$ and $$") == 0
    assert checker._unescaped_dollars("`$a` then $x$") == 2
