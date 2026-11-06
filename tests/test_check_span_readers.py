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

import ast
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


@pytest.mark.whole_tree
def test_the_tree_keeps_the_rule() -> None:
    found, stale, _ = csr.check(csr.files([]), csr.EXEMPT)
    assert [finding.describe() for finding in found] == []
    assert stale == []


def _folded(source: str, name: str) -> set[str]:
    """The strings the last expression bound to *name* in a module stands for."""
    tree = ast.parse(textwrap.dedent(source))
    strings = csr._Strings(tree)
    value: ast.expr | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target, item in csr._assigned(node):
                assert isinstance(target, ast.Name)
                assert item is not None
                if target.id == name:
                    value = item
                else:
                    strings.bind(tree, target.id, strings.fold(item))
    assert value is not None
    return strings.fold(value)


def test_an_f_string_stands_for_every_string_its_names_stand_for() -> None:
    """Each name of an f-string was read as one of its strings, whichever the
    set of them gave first, so a reader built in one branch passed or failed
    with the order of a set.
    """
    source = """
        body = "[^`]+"
        body = "\\\\w+"
        tick = "`"
        tick = "'"
        pattern = f"{tick}{body}{tick}"
    """
    assert _folded(source, "pattern") == {
        f"{a}{b}{c}" for a in "`'" for b in ("[^`]+", "\\w+") for c in "`'"
    }


def test_a_reader_in_one_branch_of_an_f_string_is_found(tmp_path: pathlib.Path) -> None:
    source = """
        import re

        def spans(text, strict):
            if strict:
                body = "[^`]+"
            else:
                body = "\\\\w+"
            for word in ("a", "b", "c", "d", "e", "f", "g"):
                body = word
            return re.findall(f"`{body}`", text)
    """
    assert _places(tmp_path, source) == ["spans"]


def test_a_pattern_of_too_many_strings_is_refused_unread(
    tmp_path: pathlib.Path,
) -> None:
    """Every combination is read up to a bound; past it the pattern is refused,
    since reading only some of them could pass a reader by hand.
    """
    letters = ", ".join(repr(c) for c in "abcdefghijklmnopqrstuvwxyz")
    source = f"""
        import re

        A = ({letters})
        B = ({letters})
        C = ({letters})

        def spans(text):
            return re.findall(f"{{A}}{{B}}{{C}}", text)
    """
    path = tmp_path / "reader.py"
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    found = csr.findings(path)
    assert [(f.function, f.unread) for f in found] == [("spans", True)]


#: Patterns a script builds from what a choice or a loop binds: every string
#: such a name or expression can be is read, so a reader on one side of the
#: choice, or among the items of the loop, is found.
_CHOSEN_READERS = {
    "a_name_bound_to_a_conditional_expression": """
        import re

        TICK = "`"

        def spans(text, flag):
            inner = r"\\w+" if flag else "[^`]+"
            return re.findall(f"{TICK}{inner}{TICK}", text)
    """,
    "a_conditional_expression_handed_to_re": """
        import re

        def spans(text, flag):
            return re.findall(r"`\\w+`" if flag else "`[^`]+`", text)
    """,
    "an_or_of_two_patterns": """
        import re

        def spans(text, pattern):
            return re.findall(pattern or "`[^`]+`", text)
    """,
    "a_name_a_loop_binds_to_the_items_of_a_tuple": """
        import re

        def spans(text):
            for body in (r"\\w+", "[^`]+"):
                re.findall(f"`{body}`", text)
    """,
    "a_name_built_with_an_added_piece": """
        import re

        def spans(text):
            pattern = "`"
            pattern += "[^`]+`"
            return re.findall(pattern, text)
    """,
    "a_name_bound_in_the_test_of_an_if": """
        import re

        def spans(text):
            if (pattern := "`[^`]+`") and text:
                return re.findall(pattern, text)
            return []
    """,
    "a_name_a_comprehension_binds_to_the_items_of_a_list": """
        import re

        def spans(text):
            return [re.findall(f"`{body}`", text) for body in [r"\\w+", "[^`]+"]]
    """,
}


@pytest.mark.parametrize("shape", sorted(_CHOSEN_READERS))
def test_a_reader_built_from_a_choice_or_a_loop_is_found(
    tmp_path: pathlib.Path, shape: str
) -> None:
    """A conditional expression and an ``or`` folded to no string, and a name a
    loop bound to the items of a tuple stood for none, so each reader passed.
    """
    assert _places(tmp_path, _CHOSEN_READERS[shape]) == ["spans"]


#: Names a comprehension, a lambda or a nested function binds for itself:
#: Python keeps them there, so the same spelling outside stands for its own
#: strings only, and inside for theirs.
_OWN_SCOPES = {
    "a_comprehension_s_variable_beside_a_name_of_the_function": """
        import re

        def words(text):
            pattern = r"\\w+"
            ticks = [pattern for pattern in ("`[^`]+`",)]
            return re.findall(pattern, text), ticks
    """,
    "a_lambda_s_parameter_beside_a_module_name": """
        import re

        PATTERN = "`[^`]+`"

        def words(text):
            find = lambda PATTERN: re.findall(PATTERN, text)
            return find(r"\\w+")
    """,
    "a_nested_function_s_parameter_beside_a_module_name": """
        import re

        PATTERN = "`[^`]+`"

        def words(text):
            def find(PATTERN):
                return re.findall(PATTERN, text)

            return find(r"\\w+")
    """,
}


@pytest.mark.parametrize("shape", sorted(_OWN_SCOPES))
def test_a_name_another_scope_binds_for_itself_stays_there(
    tmp_path: pathlib.Path, shape: str
) -> None:
    """A comprehension's variable joined the function's name of the same
    spelling, and a parameter of a lambda or a nested function was read as
    the module's name it shadows, so each pattern for words was found as a
    span reader.
    """
    assert _places(tmp_path, _OWN_SCOPES[shape]) == []


def test_a_reader_in_a_comprehension_is_read_with_its_variable(
    tmp_path: pathlib.Path,
) -> None:
    """Inside the comprehension, its variable stands for the items it walks,
    whatever the function binds under that name.
    """
    source = """
        import re

        def spans(text):
            body = r"\\w+"
            return [re.findall(f"`{body}`", text) for body in ("[^`]+",)], body
    """
    assert _places(tmp_path, source) == ["spans"]


#: Names written in one scope that Python binds in another: a ``:=`` in a
#: comprehension binds in the function around it, a name declared ``global``
#: in the module and one declared ``nonlocal`` in the function that binds it.
#: Each pattern is a span reader read through the name where Python reads it.
_BOUND_ELSEWHERE = {
    "a_walrus_in_a_generator_handed_to_any": """
        import re

        def finder(lines, text):
            if any((pat := r"`[^`]+`") for _ in lines):
                pass
            return re.findall(pat, text)
    """,
    "a_walrus_in_a_list_comprehension": """
        import re

        def finder(lines, text):
            [pat := r"`[^`]+`" for _ in lines]
            return re.findall(pat, text)
    """,
    "a_name_a_function_declares_global": """
        import re

        def setup():
            global PATTERN
            PATTERN = r"`[^`]+`"

        def finder(text):
            return re.findall(PATTERN, text)
    """,
    "a_name_a_nested_function_declares_nonlocal": """
        import re

        def finder(text):
            pattern = r"\\w+"

            def strict():
                nonlocal pattern
                pattern = r"`[^`]+`"

            strict()
            return re.findall(pattern, text)
    """,
}


@pytest.mark.parametrize("shape", sorted(_BOUND_ELSEWHERE))
def test_a_name_bound_in_the_scope_python_binds_it_in_is_read_there(
    tmp_path: pathlib.Path, shape: str
) -> None:
    """Each name landed in the scope it was written in, a comprehension's or
    the function's, and the read that Python makes through the function
    around it or through the module found nothing.
    """
    assert _places(tmp_path, _BOUND_ELSEWHERE[shape]) == ["finder"]


#: Parameters that stand for a span reader through their default, which a
#: caller that passes nothing hands on: the default is read in the scope
#: around the function or the lambda, where Python computes it.
_DEFAULTS = {
    "a_default_written_out": """
        import re

        def finder(text, pattern=r"`[^`]+`"):
            return re.findall(pattern, text)
    """,
    "a_keyword_only_default": """
        import re

        def finder(text, *, pattern=r"`[^`]+`"):
            return re.findall(pattern, text)
    """,
    "a_default_that_names_the_module_s_pattern": """
        import re

        SPAN = r"`[^`]+`"

        def finder(text):
            def inner(t, SPAN=SPAN):
                return re.findall(SPAN, t)

            return inner(text)
    """,
    "a_lambda_s_default": """
        import re

        def finder(text):
            find = lambda t, pattern=r"`[^`]+`": re.findall(pattern, t)
            return find(text)
    """,
}


@pytest.mark.parametrize("shape", sorted(_DEFAULTS))
def test_a_parameter_stands_for_its_default(tmp_path: pathlib.Path, shape: str) -> None:
    """Every parameter was bound to no string, its default left unread, so a
    reader that took its pattern from a default was never found.
    """
    nested = shape == "a_default_that_names_the_module_s_pattern"
    assert _places(tmp_path, _DEFAULTS[shape]) == [
        "finder.inner" if nested else "finder"
    ]


def test_a_class_body_s_name_is_not_read_from_its_methods(
    tmp_path: pathlib.Path,
) -> None:
    """A method reads a name of the module, never one of the class body around
    it, so the class's pattern of the same spelling is no pattern it hands on.
    """
    source = """
        import re

        PATTERN = r"\\w+"

        class Reader:
            PATTERN = r"`[^`]+`"

            def words(self, text):
                return re.findall(PATTERN, text)
    """
    assert _places(tmp_path, source) == []


def test_a_choice_of_more_strings_than_the_bound_is_refused_unread(
    tmp_path: pathlib.Path,
) -> None:
    letters = ", ".join(repr(c) for c in "abcdefghijklmnopqrstuvwxyz")
    source = f"""
        import re

        A = ({letters})

        def spans(text, flag):
            return re.findall(f"{{A}}{{A}}" if flag else f"{{A}}{{A}}{{A}}", text)
    """
    path = tmp_path / "reader.py"
    path.write_text(textwrap.dedent(source), encoding="utf-8")
    found = csr.findings(path)
    assert [(f.function, f.unread) for f in found] == [("spans", True)]
