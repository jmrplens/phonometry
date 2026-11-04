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
tests hold the two to the same answer on every page and every case here. What
each case expects is what the site's parser reads, micromark with its math, GFM
and directive extensions, and MDX on top of them on an ``.mdx`` page.
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SCRIPTS = str(_ROOT / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from markdown_fences import (
    Fence,
    code_lines,
    display_math_parts,
    fences,
    page_lines,
    python_fences,
)


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


#: Pages whose fences stand behind the marks of a quotation or a list item, with
#: which of their lines are code: what the site's parser reads in each.
_BEHIND_MARKS = (
    ("> ```\n> x\n> ```\n> prose\n", [True, True, True, False]),
    ("> ~~~\n> x\n> ~~~\n> prose\n", [True, True, True, False]),
    (">```\n>x\n>```\n>prose\n", [True, True, True, False]),
    ("> > ```\n> > x\n> > ```\n> prose\n", [True, True, True, False]),
    ("> ```\n> > x\n> ```\n> prose\n", [True, True, True, False]),
    ("> ```\n>\n> x\n> ```\n> prose\n", [True, True, True, True, False]),
    ("> ```\nprose\n```\nx\n", [True, False, True, True]),
    ("> > ```\n> prose\n", [True, False]),
    ("```\n> ```\nx\n```\nprose\n", [True, True, True, True, False]),
    ("- ```\n  x\n  ```\nprose\n", [True, True, True, False]),
    ("1. ~~~\n   x\n   ~~~\nprose\n", [True, True, True, False]),
    ("> - ```\n>   x\n>   ```\n> prose\n", [True, True, True, False]),
    ("- > ```\n  > x\n  > ```\nprose\n", [True, True, True, False]),
    ("- ```\n  x\nprose\n", [True, True, False]),
    ("- ```\n\n  x\n  ```\nprose\n", [True, True, True, True, False]),
    ("- ```a`b\nprose\n", [False, False]),
    ("> ```a`b\nprose\n", [False, False]),
    ("- ``x`` y\n", [False]),
    ("- > ```\n> text\n", [True, False]),
    ("1. > ```\n> text\n", [True, False]),
    ("> - > ```\n> > text\n", [True, False]),
    ("- > ```\n  > x\n> y\n", [True, True, False]),
    ("a\n2. ```\n   b\n", [False, False, False]),
    ("a\n2. ~~~\n   b\n", [False, False, False]),
    ("a\n1. ```\n   b\n", [False, True, True]),
    ("> a\n2. ```\n   b\n", [False, True, True]),
    ("- a\n2. ```\n   b\n", [False, True, True]),
    ("- a\n  2. ```\n     b\n", [False, False, False]),
    ("a\n> 2. ```\n> b\n", [False, False, False]),
    ("- a\n  ```\n  x\nprose\n", [False, True, True, False]),
    ("- a\n  ~~~\n  x\nprose\n", [False, True, True, False]),
    ("- a\n\n  ```\n  x\nprose\n", [False, False, True, True, False]),
    ("> - a\n>   ```\n>   x\n> prose\n", [False, True, True, False]),
    ("- a\nb\n  ```\n  x\nprose\n", [False, False, True, True, False]),
    ("- a\n\nb\n  ```\n  x\nprose\n", [False, False, False, True, True, True]),
    ("-\ta\n    ```\n    x\nprose\n", [False, True, True, False]),
    ("-\t```\n\tx\nprose\n", [True, True, False]),
    (">\t```\n>\tx\n>\t```\n> prose\n", [True, True, True, False]),
    ("$$\n```\n$$\nprose\n", [False, False, False, False]),
    (":::note\n```\nx\n:::\nprose\n", [False, True, True, False, False]),
)


@pytest.mark.parametrize(("page", "code"), _BEHIND_MARKS)
def test_a_fence_behind_marks_is_code(page: str, code: list[bool]) -> None:
    """The marks of its containers are not the line's text, as the site reads them.

    Nothing saw a fence behind a mark, so a backtick on one side of it paired
    with one on the other and hid the prose between them, and the closing fence
    of one a list item opened read as an opening one that ran to the end of the
    page. A quoted fence ends with its quotation, and one a list item holds with
    the item, on whichever of its lines the fence opened and behind whatever else.
    A marker that cannot interrupt the paragraph above is that paragraph's text.
    """
    assert _code(page) == code


@pytest.mark.parametrize(
    ("page", "body"),
    [
        ("> ```python\n> x = 1\n>\n>     y = 2\n> ```\n", "x = 1\n\n    y = 2\n"),
        ("> > ```python\n> > x = 1\n> > ```\n", "x = 1\n"),
        ("- ```python\n  for x in y:\n      f(x)\n  ```\n", "for x in y:\n    f(x)\n"),
        ("> - ```python\n>   x = 1\n>   ```\n", "x = 1\n"),
        ("- > ```python\n  > x = 1\n  > ```\n", "x = 1\n"),
    ],
)
def test_the_body_of_a_fence_behind_marks_has_lost_them(page: str, body: str) -> None:
    assert python_fences(page) == [body]


def test_a_fence_that_ends_with_what_holds_it_is_a_fence_all_the_same() -> None:
    """The reader lost one whose container ended: a later fence took its place."""
    page = "> ```python\n> x = 1\n\n```python\ny = 2\n```\n"
    assert python_fences(page) == ["x = 1\n", "y = 2\n"]
    assert python_fences("- ```python\n  x = 1\nprose\n") == ["x = 1\n"]


@pytest.mark.parametrize(
    ("page", "md", "mdx"),
    [
        pytest.param("    ```\n    x\n", [True, True], [True, True], id="alone"),
        pytest.param(
            "a\n    ```\n    x\n",
            [False, False, False],
            [False, True, True],
            id="under a paragraph",
        ),
        pytest.param(
            "    ```\nprose\n", [True, False], [True, True], id="closed by nothing"
        ),
        pytest.param(
            "```\na\n    ```\nb\n",
            [True, True, True, True],
            [True, True, True, False],
            id="a closing fence four columns in",
        ),
        pytest.param(
            "- a\n\n      ```\n      b\n  c\n",
            [False, False, True, True, False],
            [False, False, True, True, True],
            id="four columns past its item",
        ),
        pytest.param(
            "<pre>\n```\n</pre>\nprose\n",
            [False, False, False, False],
            [False, True, True, True],
            id="in a raw HTML block",
        ),
        pytest.param(
            "<A>\n```\nx\n```\n</A>\nprose\n",
            [False, False, False, False, False, False],
            [False, True, True, True, False, False],
            id="in a component",
        ),
    ],
)
def test_the_kind_of_a_page_says_what_indentation_and_a_tag_mean(
    page: str, md: list[bool], mdx: list[bool]
) -> None:
    """A ``.md`` page has indented code and raw HTML; an ``.mdx`` page has neither."""
    lines = page.splitlines()
    assert list(code_lines(lines, kind="md")) == md
    assert list(code_lines(lines, kind="mdx")) == mdx


@pytest.mark.parametrize(
    ("page", "parts"),
    [
        pytest.param(
            "> $$\n> x\n> $$\n> prose\n",
            ["open", "maths", "maths", "prose"],
            id="in a quotation",
        ),
        pytest.param(
            ">$$\n>x\n>$$\n>prose\n",
            ["open", "maths", "maths", "prose"],
            id="with no blank after the mark",
        ),
        pytest.param(
            "> First\n> $$\n> x\n> $$\n",
            ["prose", "open", "maths", "maths"],
            id="under a paragraph of a quotation",
        ),
        pytest.param("> $$\nprose\n", ["open", "prose"], id="ends with the quotation"),
        pytest.param(
            "> > $$\n> prose\n", ["open", "prose"], id="ends with the deeper quotation"
        ),
        pytest.param(
            "> $$\n> x\n$$\ny\n$$\nprose\n",
            ["open", "maths", "open", "maths", "maths", "prose"],
            id="a fence of no quotation opens its own",
        ),
        pytest.param(
            "$$\n> x\n> $$\n$$\nprose\n",
            ["open", "maths", "maths", "maths", "prose"],
            id="marks are maths in a block of no quotation",
        ),
        pytest.param(
            "> $$\n> > x\n> $$\n> prose\n",
            ["open", "maths", "maths", "prose"],
            id="a deeper mark is maths",
        ),
        pytest.param(
            "> $$\n>\n> x\n> $$\n",
            ["open", "maths", "maths", "maths"],
            id="a bare mark is maths",
        ),
        pytest.param(
            "> $$$\n> $$\n> x\n> $$$\n",
            ["open", "maths", "maths", "maths"],
            id="a shorter run closes nothing",
        ),
        pytest.param(
            "> $$\n> x\n> $$ tail\n> $$\n",
            ["open", "maths", "maths", "maths"],
            id="a run with text after it closes nothing",
        ),
        pytest.param(
            "- $$\n  x\n  $$\nprose\n",
            ["open", "maths", "maths", "prose"],
            id="on a list item's first line",
        ),
        pytest.param(
            "1. $$\n   x\n   $$\nprose\n",
            ["open", "maths", "maths", "prose"],
            id="on a numbered item's first line",
        ),
        pytest.param(
            "- $$\n  x\nprose\n", ["open", "maths", "prose"], id="ends with the item"
        ),
        pytest.param(
            "> - $$\n>   x\n>   $$\n> prose\n",
            ["open", "maths", "maths", "prose"],
            id="on an item of a quotation",
        ),
        pytest.param(
            "- > $$\n  > x\n  > $$\nprose\n",
            ["open", "maths", "maths", "prose"],
            id="in a quotation of an item",
        ),
        pytest.param(
            "- $$x$$ y\nprose\n", ["prose", "prose"], id="a run closed on its line"
        ),
        pytest.param(
            "```\n> $$\n```\nprose\n",
            ["prose", "prose", "prose", "prose"],
            id="in a fence",
        ),
        pytest.param(
            "$$\n```\n$$\nprose\n",
            ["open", "maths", "maths", "prose"],
            id="a fence in the block is maths",
        ),
        pytest.param(
            "- > $$\n> prose\n", ["open", "prose"], id="out of the item behind it"
        ),
        pytest.param(
            "a\n2. $$\n   b\n   $$\n",
            ["prose", "prose", "prose", "open"],
            id="a marker that cannot interrupt the paragraph",
        ),
        pytest.param(
            "a\n1. $$\n   b\n",
            ["prose", "open", "maths"],
            id="a marker that can",
        ),
        pytest.param(
            "- a\n  $$\n  x\nprose\n",
            ["prose", "open", "maths", "prose"],
            id="ends with the item it opened on a later line of",
        ),
    ],
)
def test_a_display_block_is_read_through_the_marks_of_its_containers(
    page: str, parts: list[str]
) -> None:
    """What the site's parser reads: a block ends with what holds it."""
    lines = page.splitlines()
    assert display_math_parts(lines) == parts


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
    "> ```python\n> x = 1\n>\n>     y = 2\n> ```\nprose\n",
    "- ```python\n  for x in y:\n      f(x)\n  ```\n",
    "> a\r\n> ```\r\n> b\r\n> ```\r\n",
    *(page for page, _ in _BEHIND_MARKS),
)


#: Pages that walk through every shape, for the two languages to agree on.
_WALKS = (
    "> a\n===\nb\n",
    "- a\n  ===\nb\n",
    "- a\n---\nb\n",
    "> a\n-\nb\n",
    "a\n-\nb\n",
    "a\n2. b\n",
    "a\n1. b\n",
    "- a\n2. b\n",
    "- a\n  2. b\n",
    "a\n> 2. b\n",
    "    a\n\n2. b\n",
    "| a |\n|---|\n| b |\nc\n",
    "| a |\nb\n",
    "a | b\n--|--\nc\n",
    "a | b\n- | -\n",
    "a \\| b\n-|-\n",
    "|\n|-\n",
    "> a\n| b |\n> |---|\n",
    "> a\n| b |\n|---|\n",
    "<div>\na\n\nb\n",
    "<!-- a\n\nb -->\nc\n",
    "<?a\n?>\nb\n",
    "<!x\n>\nb\n",
    "<![CDATA[\n]]>\nb\n",
    "<script>\n\n</script>\nb\n",
    "<A />\na\n\nb\n",
    "| a |\n|---|\n<A />\nb\n",
    "a\n<A />\nb\n",
    "> a\n<A />\n> b\nc\n",
    '<A\n  b="c"\n/>\nd\n',
    "{x}\na\n",
    "{\n  x\n}\na\n",
    "<b>a</b> c\nd\n",
    ":::note\na\n:::\nb\n",
    "a\n:::\nb\n",
    "::::note\n:::\n::::\nb\n",
    "> :::note\n> a\nb\n> :::\n",
    ":::note\n> a\nb\n:::\n",
    "::x\na\n",
    "-\n\n  a\n",
    "-\n  a\n",
    "-      a\n  b\n",
    "-\ta\n\tb\n",
    ">\ta\n",
    "1.\t  a\n",
    "\ta\n",
    "- a\n\n\t\tb\n",
)


def _split_as_the_site_does(text: str) -> list[str]:
    """The lines of a page without their ends, as ``splitLines`` of the site gives them."""
    return re.split(r"\r\n|\r|\n", text.removesuffix("\n").removesuffix("\r"))


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


@pytest.mark.skipif(_NODE is None, reason="no JavaScript engine to compare with")
@pytest.mark.parametrize("kind", ["md", "mdx"])
def test_the_site_walks_every_page_as_the_scripts_do(kind: str) -> None:
    """Each line's role and what the walk leaves of it, on each kind of page."""
    pages = [*_pages(), *_WALKS]
    script = (
        "import {pageLines, splitLines} from "
        f"{json.dumps(_SITE_READER.as_uri())};"
        "let input = '';"
        "for await (const chunk of process.stdin) input += chunk;"
        "process.stdout.write(JSON.stringify(JSON.parse(input).map((text) => "
        f"  pageLines(splitLines(text), {{kind: {json.dumps(kind)}}})"
        "    .map((line) => [line.role, line.rest]))));"
    )
    ran = subprocess.run(
        [str(_NODE), "--input-type=module", "-e", script],
        input=json.dumps(pages),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
        check=True,
    )
    python = [
        [
            [line.role, line.rest]
            for line in page_lines(_split_as_the_site_does(text), kind=kind)
        ]
        for text in pages
    ]
    differ = [
        text[:80]
        for text, one, other in zip(pages, python, json.loads(ran.stdout), strict=True)
        if one != other
    ]
    assert differ == []
