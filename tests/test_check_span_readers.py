#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate on scripts that read an inline code span without the shared reader.

``scripts/check_span_readers.py`` refuses a regular expression handed to
``re`` that finds a code span by hand, a backtick, what a span holds and a
backtick, or a captured run of backticks paired by a backreference, anywhere
in ``scripts/`` but ``scripts/markdown_spans.py``, and either shape spelled
in the site's own code but ``site/scripts/shared/markdown-spans.mjs``. The
two readers it found on the tree are here in their own shapes, the cells of
the curated API table and the values of the translation tables, and so are
the other ways Python spells the same pattern and the shapes it must not
refuse: a role of reStructuredText, a class that only leaves a backtick out,
a pattern for anything else.
"""

from __future__ import annotations

import pathlib
import sys
import textwrap

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_span_readers as csr

#: Patterns that read a code span by hand.
_READERS = {
    "a backticked name of a table cell": r"`([^`]+)`",
    "a code span among the things that are no prose": r"\{[^{}]*\}|`[^`]*`",
    "a span on one line": r"`[^`\n]+`",
    "two backticks, lazily": r"``(.+?)``",
    "anything at all, lazily": r"`.*?`",
    "a span of two backticks that may hold one": r"``(?:[^`]|`(?!`))+``",
    "a run paired by a backreference": r"(`+)(.+?)\1",
    "a named run paired by name": r"(?P<run>`+)(.+?)(?P=run)",
    "a run of backticks on each side": r"`+([^`]+)`+",
    "a run of two or more": r"`{2,}([^`]+)`{2,}",
    "anything at all, greedily": r"`(.+)`",
    "anything or nothing, greedily": r"`(.*)`",
    "padded by white space": r"`\s*([^`]+?)\s*`",
    "padded by spaces and tabs": r"`[ \t]*([^`]+)[ \t]*`",
    "padded by one space at most": r"` ?([^`]+) ?`",
}

#: Patterns that hold a backtick and read no span.
_NO_READERS = {
    "a role of reStructuredText": r":math:`([^`]+)`",
    "a cross-reference role": r":(?:class|func):`(~?)([^`<]+?)`",
    "a class that leaves a backtick out": r"[^\n`]*?(?<=\s)",
    "a run of backticks alone": r"`+",
    "a fence": r"^(\s*)(`{3,}|~{3,})(.*)$",
    "an escaped backtick or dollar": r"\\([`$\\])",
    # A token between backticks, which no span reader stops at: the limit of
    # the rule, which reads what a span holds only as anything but a backtick.
    "a file name between backticks": r"``([\w./-]+\.json)``",
    "a word between backticks": r"`(\S+?)`",
}


@pytest.mark.parametrize("shape", sorted(_READERS))
def test_a_pattern_that_reads_a_span_is_one(shape: str) -> None:
    assert csr.reads_span(_READERS[shape])


@pytest.mark.parametrize("shape", sorted(_NO_READERS))
def test_a_pattern_that_reads_no_span_is_none(shape: str) -> None:
    assert not csr.reads_span(_NO_READERS[shape])


def _places(tmp_path: pathlib.Path, source: str, name: str = "reader.py") -> list[str]:
    """The function of each place a script written from ``source`` reads a span."""
    path = tmp_path / name
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    return [finding.function for finding in csr.findings(path)]


def test_a_compiled_pattern_at_the_top_of_a_script_is_read(
    tmp_path: pathlib.Path,
) -> None:
    """The shape the API-reference check read its table cells with."""
    source = """
        import re

        _BACKTICKED = re.compile(r"`([^`]+)`")
    """
    assert _places(tmp_path, source) == ["<module>"]


def test_a_pattern_behind_a_name_or_built_is_read(tmp_path: pathlib.Path) -> None:
    """A name bound in the module or the function, a join, an f-string."""
    source = """
        import re
        from re import findall

        TICK = "`"
        SPAN = TICK + "[^`]+" + TICK

        def by_name(text):
            return re.sub(SPAN, "", text)

        def by_join(text):
            body = "[^`]*"
            return findall(f"`{body}`", text)
    """
    assert _places(tmp_path, source) == ["by_name", "by_join"]


def test_a_pattern_for_something_else_is_not_read(tmp_path: pathlib.Path) -> None:
    source = """
        import re

        def roles(text):
            return re.findall(r":math:`([^`]+)`", text)

        def words(text):
            return re.findall(r"\\w+", text)
    """
    assert _places(tmp_path, source) == []


def test_a_line_of_the_site_s_code_is_read(tmp_path: pathlib.Path) -> None:
    source = """
        // A span by hand, in a comment: `[^`]*`
        const prose = text.replace(/`[^`]*`/g, ' ');
        const kept = text.replace(/\\$+/g, ' ');
    """
    assert _places(tmp_path, source, "page.mjs") == ["<script>"]


@pytest.mark.parametrize(
    "shape",
    [
        "a run of backticks on each side",
        "a run of two or more",
        "anything at all, greedily",
        "anything or nothing, greedily",
        "padded by white space",
        "padded by spaces and tabs",
        "padded by one space at most",
    ],
)
def test_each_shape_is_read_in_a_script_and_in_the_site_s_code(
    shape: str, tmp_path: pathlib.Path
) -> None:
    """A shape is found where Python hands it to ``re`` and on a line of the site."""
    pattern = _READERS[shape]
    script = f"import re\n\nSPANS = re.compile({pattern!r})\n"
    assert _places(tmp_path, script) == ["<module>"]
    line = f"const spans = text.match(/{pattern}/g);\n"
    assert _places(tmp_path, line, "page.mjs") == ["<script>"]


def test_an_exemption_that_covers_nothing_is_stale(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "plain.py"
    path.write_text("import re\nre.compile(r'\\w+')\n", encoding="utf-8")
    found, stale, read = csr.check([path], {"scripts/gone.py": "a reason"})
    assert (found, stale, read) == ([], ["scripts/gone.py"], 1)


def test_the_tree_keeps_the_rule() -> None:
    found, stale, _ = csr.check(csr.files([]), csr.EXEMPT)
    assert [finding.describe() for finding in found] == []
    assert stale == []
