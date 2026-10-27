#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate for markdown that does not render the way it reads.

``scripts/check_markdown_hazards.py`` reads a page the way CommonMark and MDX
will, so it can go wrong in both directions: miss a source that breaks the
page, or refuse one that builds. The fifth rule is where the second is easy.
MDX fails on a ``<`` of prose glued to a digit or an operator, and builds the
same characters inside a quoted attribute value of a JSX tag, such as an
``alt`` text, and in the YAML frontmatter, which Astro blanks before MDX
reads the body. The site's own compiler, ``@mdx-js/mdx`` 3.1.1 with
``remark-math``, fails on every case the fifth rule refuses below and
compiles every case it accepts, once the frontmatter is blanked as Astro
blanks it. The first four rules get one case each, since each one has a
function of its own, and the first gets three more. A ``$`` inside an
inline code span is code, and CommonMark reads the span before any maths
could open in it, so the ``$schema`` key of a JSON document in a table cell
opens nothing. The rule has to keep catching the defect it exists for,
maths that wraps onto a block marker, whether or not the line also holds a
code span.
"""

from __future__ import annotations

import pathlib
import sys

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_markdown_hazards as cmh

_GLUED = "no tag name starts with"


def _glued(text: str, name: str = "page.mdx") -> list[str]:
    """The fifth rule's reports for a page, and only those."""
    return [problem for problem in cmh.check_text(text, name) if _GLUED in problem]


@pytest.mark.parametrize(
    ("text", "seen"),
    [
        ('A quoted "<0,02 above 200 Hz" in prose.\n', "'<0,02 above '"),
        ("The bound holds for x <=5 and no more.\n", "'<=5 and no m'"),
        ('<span id="a"></span> and then <0,02 here.\n', "'<0,02 here.'"),
    ],
    ids=["digit", "operator", "after-a-closed-tag"],
)
def test_a_less_than_glued_to_what_follows_in_mdx_prose_is_refused(
    text: str, seen: str
) -> None:
    problems = _glued(text)
    assert len(problems) == 1
    assert problems[0].startswith(f"page.mdx:1: {seen} puts a '<'")


@pytest.mark.parametrize(
    "text",
    [
        "A bound of < b holds.\n",
        "The code `<0.1` stays code.\n",
        "The maths $a <0.1$ stays maths.\n",
        "An escaped \\<0.1 stays text.\n",
        "```python\nx <0\n```\n",
        "$$\na <0,1\n$$\n",
        '<ThemeImage src="a.svg" alt="a band of <0.1 dB up to 8 kHz" width="100%" />\n',
        '<ThemeImage\n  src="a.svg"\n  alt="a band of <0.1 dB up to 8 kHz"\n  width="100%"\n/>\n',
        "<ThemeImage src='a.svg' alt='a band of <0.1 dB' />\n",
        '<ThemeImage alt={"a band of <0.1 dB"} />\n',
        '<ThemeImage\n  alt="a band of\n  <0.1 dB up to 8 kHz"\n/>\n',
        '---\ntitle: Probe\ndescription: "The special case prints <0,02 dB above 200 Hz."\n---\n',
    ],
    ids=[
        "space",
        "inline-code",
        "inline-maths",
        "escaped",
        "code-fence",
        "display-maths",
        "alt-text",
        "alt-text-of-a-tag-on-five-lines",
        "single-quoted-value",
        "expression-value",
        "value-on-two-lines",
        "frontmatter",
    ],
)
def test_a_less_than_mdx_does_not_read_as_a_tag_is_accepted(text: str) -> None:
    assert _glued(text) == []


#: A JSX element further down the page, whose ``>`` a ``<`` read as the start
#: of a tag would run on to, taking every quoted string on the way with it.
_LATER_TAG = '\n\n<ThemeImage src="a.svg" alt="x" />\n'


@pytest.mark.parametrize(
    ("text", "line", "seen"),
    [
        (
            "A quiet room reads `below the\nlabel <NC-15` on it, and the case "
            'prints "<0,02 above 200 Hz".' + _LATER_TAG,
            2,
            "'<0,02 above '",
        ),
        (
            'It holds for $f\n= g <f_c$ only, and the case prints "<0,02 above '
            '200 Hz".' + _LATER_TAG,
            2,
            "'<0,02 above '",
        ),
        (
            "A quiet room reads `below the\nlabel <NC-15` on it.\n\nThe case "
            'prints "<0,02 above 200 Hz".' + _LATER_TAG,
            4,
            "'<0,02 above '",
        ),
        (
            "The option `mode is\nset <auto` by default. The meter's band is "
            "<0,1 dB, it's small." + _LATER_TAG,
            2,
            '"<0,1 dB, it\'"',
        ),
        ('An escaped \\<b and then "x <0.1" y> here.\n', 1, "'<0.1\" y> her'"),
        ("A path \\\\<0 here.\n", 1, "'<0 here.'"),
        (
            '<ThemeImage alt="a\n\n<0.1 dB" /> and text after it.\n',
            3,
            "'<0.1 dB\" /> '",
        ),
        ("A span `a\n- b <0 c` here.\n", 2, "'<0 c` here.'"),
        ("A span `a\\` <0 b` here.\n", 1, "'<0 b` here.'"),
    ],
    ids=[
        "after-a-code-span-on-two-lines",
        "after-inline-maths-on-two-lines",
        "a-paragraph-after-a-code-span-on-two-lines",
        "between-apostrophes",
        "in-quotes-after-an-escaped-less-than",
        "after-an-escaped-backslash",
        "after-a-tag-with-text-after-it-on-its-line",
        "in-a-code-span-a-list-item-cuts",
        "after-a-code-span-a-backslash-does-not-escape",
    ],
)
def test_a_less_than_that_no_span_or_tag_holds_is_refused(
    text: str, line: int, seen: str
) -> None:
    r"""MDX reads a page from left to right, and so does the fifth rule.

    A ``<`` and a letter inside a code span or inline maths starts no tag,
    even when the span runs on to a second line, and an escaped ``\<``
    starts none either. So none of them hides a ``<0`` further on: MDX fails
    on each of these, where a ``<`` read as the start of a tag would have
    swallowed every quoted string, and every pair of apostrophes, up to the
    ``>`` of the element at the end.
    """
    problems = _glued(text)
    assert len(problems) == 1
    assert problems[0].startswith(f"page.mdx:{line}: {seen} puts a '<'")


@pytest.mark.parametrize(
    "text",
    [
        "A span `a\nb <0 c` here.\n",
        "A span $a\nb <0 c$ here.\n",
        "A span `` a ` <0 `` here.\n",
        "A `` run nothing closes, then `code <0` here.\n",
        "A $$a\nb <0$$ z.\n",
        'See <abbr title="a `b">x</abbr> and `c <0` d.\n',
        '<ThemeImage\n\n  alt="a <0.1"\n/>\n',
        '<ThemeImage alt="a\n\n<0.1 dB" />\n',
        'A paragraph.\n<ThemeImage\n\n  alt="a <0.1"\n/>\n',
    ],
    ids=[
        "code-span-on-two-lines",
        "inline-maths-on-two-lines",
        "code-span-of-two-backticks",
        "backticks-nothing-closes",
        "inline-maths-of-two-dollars",
        "backtick-in-a-value",
        "tag-with-a-blank-line-between-its-attributes",
        "value-with-a-blank-line",
        "tag-starting-a-line-under-a-paragraph",
    ],
)
def test_a_less_than_in_a_span_or_a_value_over_several_lines_is_accepted(
    text: str,
) -> None:
    """A span runs on to the next line of its paragraph, a tag across blanks.

    A code span and inline maths end with their paragraph; a tag that has
    its lines to itself is a block, and MDX lets it run across blank lines.
    """
    assert _glued(text) == []


def test_prose_after_a_tag_on_several_lines_is_read_on_its_own_line() -> None:
    """The tag ends at its ``>``: the prose after it is read, on its own line."""
    text = '<ThemeImage\n  alt="a band of <0.1 dB"\n/>\n\nThen x <=5 in prose.\n'
    problems = _glued(text)
    assert len(problems) == 1
    assert problems[0].startswith("page.mdx:5: '<=5 in prose'")


def test_a_less_than_between_the_attributes_of_a_tag_is_still_refused() -> None:
    """Only the quoted values of a tag are blanked, not the tag itself.

    MDX fails on this one too, reading the ``<`` where an attribute name has
    to start.
    """
    problems = _glued('<ThemeImage src="a.svg"\n  <0,1 dB\n/>\n')
    assert len(problems) == 1
    assert problems[0].startswith("page.mdx:2: '<0,1 dB'")


def test_the_body_after_the_frontmatter_is_read_on_its_own_lines() -> None:
    text = '---\ndescription: "<0,02 dB"\n---\n\nA quoted "<0,02 dB" here.\n'
    problems = _glued(text)
    assert len(problems) == 1
    assert problems[0].startswith("page.mdx:5: ")


def test_a_plain_markdown_page_is_not_read_as_mdx() -> None:
    assert _glued('A quoted "<0,02 above 200 Hz" in prose.\n', "page.md") == []


def test_a_dollar_in_the_frontmatter_opens_no_maths() -> None:
    """A price in a YAML description does not leak into the first rule."""
    text = "---\ndescription: costs $5 a band\n---\nIntro line\n- a list item\n"
    assert cmh.check_text(text, "page.mdx") == []


def test_inline_maths_cut_off_by_a_list_marker_is_refused() -> None:
    problems = cmh.check_text("The level $L_{n,ij,w} = a\n- K_{ij}$ holds.\n", "p.md")
    assert len(problems) == 1
    assert problems[0].startswith("p.md:2: inline maths opened on line 1")


def _problems(tmp_path: pathlib.Path, text: str) -> list[str]:
    page = tmp_path / "page.md"
    page.write_text(text, encoding="utf-8")
    original = cmh._ROOT
    cmh._ROOT = tmp_path
    try:
        return cmh._check(page)
    finally:
        cmh._ROOT = original


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
    assert cmh._unescaped_dollars("`$a` and ``b $ c`` and \\$ and $$") == 0
    assert cmh._unescaped_dollars("`$a` then $x$") == 2
    # A closing run is a whole run of the opener's length: one tick of `` never
    # closes a single ` , so the $ after an unmatched ` is prose.
    assert cmh._unescaped_dollars("a `$x`` b") == 1
    assert cmh._unescaped_dollars("a ``$x` b``") == 0


def test_a_wrapped_greater_than_sign_is_refused() -> None:
    problems = cmh.check_text("The level is always\n> 5 dB above it.\n", "p.md")
    assert len(problems) == 1
    assert "starts a block quote" in problems[0]


def test_a_same_page_link_to_an_accented_heading_is_refused() -> None:
    problems = cmh.check_text("See [it](#la-medición).\n", "p.md")
    assert len(problems) == 1
    assert "'#la-medición' will be percent-encoded" in problems[0]


def test_a_link_to_an_accented_heading_on_another_page_is_refused() -> None:
    """The audit of the published site found 150 of these, all cross-page."""
    text = "See [it](/phonometry/es/reference/theory/vibration/#la-medición).\n"
    problems = cmh.check_text(text, "p.md")
    assert len(problems) == 1
    assert "'/phonometry/es/reference/theory/vibration/#la-medición'" in problems[0]


@pytest.mark.parametrize(
    "text",
    [
        "See [it](/phonometry/es/reference/theory/vibration/#la-medicion).\n",
        "See [it](https://es.wikipedia.org/wiki/Ac%C3%BAstica#Historia).\n",
        "See [it](https://es.wikipedia.org/wiki/Acústica#Física).\n",
    ],
)
def test_an_ascii_fragment_or_another_site_is_left_alone(text: str) -> None:
    assert cmh.check_text(text, "p.md") == []


@pytest.mark.parametrize(
    ("text", "level"),
    [
        # The errata entry that gave its page a second h1: a formula wrapped
        # just before its equals sign, inside a list item.
        ("- **The problem:** the quotient $M^2\n  =\n  (M_1 M_2)$ of three.\n", "h1"),
        ("A sentence that wrapped\n---\n", "h2"),
        ("A sentence that wrapped\n-\n", "h2"),
    ],
)
def test_a_line_of_equals_or_hyphens_under_text_is_refused(
    text: str, level: str
) -> None:
    problems = cmh.check_text(text, "p.md")
    assert len(problems) == 1
    assert f"becomes an {level}" in problems[0]


@pytest.mark.parametrize(
    "text",
    [
        "A paragraph.\n\n---\n\nAnother.\n",
        "## A heading\n---\n",
        "| a | b |\n|---|---|\n",
        "```text\nlabel\n=====\n```\n",
        "```text\nlabel\n```\n---\n",
    ],
)
def test_a_thematic_break_a_table_or_code_is_not_a_setext_heading(text: str) -> None:
    assert cmh.check_text(text, "p.md") == []


@pytest.mark.parametrize(
    "text",
    [
        "$$\nx\n=\ny\n$$\n",
        "Where\n\n$$\nL\n=\n10 \\lg x\n$$\n",
        "- item\n\n  $$\n  a\n  -\n  b\n  $$\n",
        "$$\nx = y\n$$\n---\n",
        "$$\nx = y\n$$\n=\n",
        "```math\nx\n=\ny\n```\n",
    ],
    ids=[
        "equals-in-a-formula",
        "after-a-paragraph",
        "hyphen-in-a-list-item",
        "rule-after-the-closing-fence",
        "equals-after-the-closing-fence",
        "math-code-fence",
    ],
)
def test_a_line_of_equals_or_hyphens_in_display_maths_is_maths(text: str) -> None:
    """A formula written one term per line may put ``=`` alone on a line.

    remark-math reads a display block as a fence, so that line is maths, not
    a setext underline, and the line after the closing ``$$`` underlines
    nothing either: CommonMark has no paragraph above it to turn into a
    heading.
    """
    assert cmh.check_text(text, "p.md") == []


@pytest.mark.parametrize(
    ("text", "line"),
    [
        ("A sentence that wrapped\n=\n\n$$\nx\n=\ny\n$$\n", 2),
        ("$$\nx\n=\ny\n$$\n\nA sentence that wrapped\n=\n", 8),
        ("```math\nx\n=\n```\n\nA sentence that wrapped\n=\n", 7),
    ],
    ids=["before-the-block", "after-the-block", "after-a-math-fence"],
)
def test_a_setext_underline_beside_display_maths_is_still_refused(
    text: str, line: int
) -> None:
    problems = cmh.check_text(text, "p.md")
    assert len(problems) == 1
    assert f"p.md:{line}:" in problems[0]
    assert "becomes an h1" in problems[0]


def test_a_display_fence_that_holds_a_dollar_opens_no_block() -> None:
    """``$$x = 1$$`` is inline maths in a paragraph, so a ``=`` under it underlines.

    remark-math refuses a ``$`` in the meta of an opening fence, so the line
    is a paragraph, the fourth rule reports it, and the line under it turns
    it into a heading.
    """
    problems = cmh.check_text("$$x = 1$$\n=\n", "p.md")
    assert len(problems) == 2
    assert "It closes on this line" in problems[0]
    assert "becomes an h1" in problems[1]


def test_a_formula_on_the_opening_display_fence_is_refused() -> None:
    problems = cmh.check_text("$$x = 1\n", "p.md")
    assert len(problems) == 1
    assert "Nothing closes it" in problems[0]


@pytest.mark.parametrize(
    ("text", "consequence"),
    [
        ("- item\n\n  $$x = 1$$\n", "It closes on this line"),
        ("- item\n\n  $$x = 1\n  $$\n", "Nothing closes it"),
    ],
)
def test_a_formula_on_an_indented_display_fence_is_refused(
    text: str, consequence: str
) -> None:
    """A list item indents its display block, and the fence is the same fence.

    The errata registers carried six such one-line blocks inside list items
    with every gate green, because the check read the fence at column 0 only.
    """
    problems = cmh.check_text(text, "p.md")
    assert len(problems) == 1
    assert consequence in problems[0]


def test_a_hazard_in_a_tilde_fence_is_code() -> None:
    assert (
        cmh.check_text("~~~\nThe level is always\n> 5 dB above it.\n~~~\n", "p.md")
        == []
    )


def test_a_fence_shown_inside_another_closes_nothing() -> None:
    text = "````\n```\nexample\n````\nThe level is always\n> 5 dB above it.\n"
    problems = cmh.check_text(text, "p.md")
    assert len(problems) == 1
    assert "p.md:6:" in problems[0]
    assert "starts a block quote" in problems[0]


def test_the_shipped_pages_pass(capsys: pytest.CaptureFixture[str]) -> None:
    assert cmh.main() == 0
    assert "Markdown renders the way it reads" in capsys.readouterr().out
