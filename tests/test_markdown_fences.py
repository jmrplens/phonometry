#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Which lines of a page are code, the reading every prose check starts from.

``scripts/markdown_fences.py`` closes a fence the way CommonMark does: on a
line of the same character, at least as long as the opening run, with nothing
after it. The defect it replaced closed a fence on any run of three markers,
so a page that shows a fence inside another was read inside out from there
on. The tests fix the cases where the two readings part, and the plain ones
that must not move, and then the blocks the example checks take out of a page
through the same reading. The site's JavaScript reads its pages with the
same reading written again, ``site/src/lib/markdown-fences.mjs``, and the last
test holds the two to the same answer on every page and every case here.
"""

from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from markdown_fences import Fence, code_lines, fences, python_fences


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


def test_a_tilde_run_inside_a_backtick_fence_closes_nothing() -> None:
    """As long as the opening run, so only the marker character keeps it open."""
    assert _code("```\n~~~\nx = 1\n```\nprose\n") == [True] * 4 + [False]


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


def test_a_fence_carries_its_line_its_info_string_and_its_body() -> None:
    page = "prose\n```python title=room.py\nx = 1\ny = 2\n```\n"
    assert list(fences(page)) == [Fence(2, "python title=room.py", "x = 1\ny = 2\n")]
    assert next(fences(page)).language == "python"


def test_a_fence_without_an_info_string_has_no_language() -> None:
    assert next(fences("~~~\nplain\n~~~\n")).language == ""


def test_a_python_fence_shown_inside_another_is_not_an_example() -> None:
    page = "````markdown\n```python\nshown = 1\n```\n````\n```python\nrun = 2\n```\n"
    assert python_fences(page) == ["run = 2\n"]


def test_a_python_fence_with_attributes_is_still_python() -> None:
    assert python_fences("```python {3}\nx = 1\n```\n") == ["x = 1\n"]


def test_an_indented_fence_loses_the_indentation_of_its_marker() -> None:
    page = "- item\n\n    ```python\n    for x in y:\n        f(x)\n    ```\n"
    assert python_fences(page) == ["for x in y:\n    f(x)\n"]


def test_a_python_fence_never_closed_is_read_to_the_end_of_the_page() -> None:
    assert python_fences("prose\n```python\nx = 1\n") == ["x = 1\n"]


_NODE = shutil.which("node")
_SITE_READER = _ROOT / "site" / "src" / "lib" / "markdown-fences.mjs"
#: The cases above where two readings part, as whole pages.
_CASES = (
    "prose\n```python\nx = 1\n```\nprose\n",
    "~~~~\n```\nexample\n~~~~\nprose\n",
    "```\n~~~\nx = 1\n```\nprose\n",
    "````\n```\nexample\n````\nprose\n",
    "```\nx = 1\n`````\nprose\n",
    "```\n```python\n```\nprose\n",
    "```a`b\nprose\n",
    "- item\n\n    ```python\n    for x in y:\n        f(x)\n    ```\nprose\n",
    "prose\n```python title=room.py\nx = 1\n",
    "````markdown\n```python\nshown = 1\n```\n````\n```python\nrun = 2\n```",
    "a\r\n```\r\nb\r\n```\r\n",
)


def _pages() -> list[str]:
    """Every page of the documentation and the site, and the cases above."""
    paths = [
        *sorted((_ROOT / "docs").rglob("*.md")),
        *sorted((_ROOT / "site" / "src" / "content").rglob("*.md*")),
    ]
    return [*(path.read_text(encoding="utf-8") for path in paths), *_CASES]


@pytest.mark.skipif(_NODE is None, reason="no JavaScript engine to compare with")
def test_the_site_reads_every_page_as_the_scripts_do() -> None:
    """Which lines are code, and every block with its line, info string and body."""
    pages = _pages()
    script = (
        "import {codeLines, fences, splitLines} from "
        f"{json.dumps(_SITE_READER.as_uri())};"
        "let input = '';"
        "for await (const chunk of process.stdin) input += chunk;"
        "process.stdout.write(JSON.stringify(JSON.parse(input).map((text) => ["
        "  codeLines(splitLines(text)),"
        "  fences(text).map((f) => [f.line, f.info, f.body, f.language]),"
        "])));"
    )
    ran = subprocess.run(
        [str(_NODE), "--input-type=module", "-e", script],
        input=json.dumps(pages),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=True,
    )
    python = [
        [
            list(code_lines(text.splitlines())),
            [[f.line, f.info, f.body, f.language] for f in fences(text)],
        ]
        for text in pages
    ]
    javascript = json.loads(ran.stdout)
    differ = [
        text[:80]
        for text, one, other in zip(pages, python, javascript, strict=True)
        if one != other
    ]
    assert (len(pages) > len(_CASES), differ) == (True, [])
