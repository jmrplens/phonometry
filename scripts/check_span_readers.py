#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Fail on a script that decides for itself where an inline code span opens or closes.

A code span opens on a run of backticks and closes on the next run of exactly
as many (CommonMark 0.31.2, 6.1); a backslash before the opening run escapes
its first backtick, and inside the span a backslash escapes nothing. The
scripts that read the prose of a page each used to work that out with a
pattern of their own, a backtick, anything but a backtick, a backtick, and
each read a span of two backticks, an escaped backtick or a span that held a
backslash wrongly, hiding prose from its check or checking code as prose.
``scripts/markdown_spans.py`` now reads the spans for every Python script, and
``site/scripts/shared/markdown-spans.mjs``, the same reading in JavaScript,
for the site's own scripts. This keeps it that way, as
``scripts/check_fence_readers.py`` does for fences.

It reads every Python script under ``scripts/`` but the shared reader and
itself, and refuses a regular expression handed to the ``re`` module that
reads a span by hand:

- **A span by its content**: a backtick, or a run of them written out or
  with a quantifier (``+``, ``{2}``, ``{2,}``), white space a reader lets
  pad it (``\\s*``, ``[ \\t]*``, `` ?``), then, inside a group or not, what a
  span holds written as anything but a backtick (``[^`]``, ``[^`\\n]``) or as
  anything at all (``.*?``, ``.+``), and a backtick after it:
  ``r"`[^`]+`"``, ``r"``(.+?)``"``, ``r"`+(.+)`+"``. A pattern that takes
  only some characters between backticks (``(\\S+?)``, ``([\\w.]+)``) reads a
  token no span stops at, and is left alone.
- **A span by its run**: a run of backticks captured (``(`+)``) and matched
  again by a backreference, the shape of a reader that pairs the runs itself.

A pattern is read the way Python builds it: written out, joined with ``+`` or
in an f-string, chosen (``a if flag else b``, ``a or b``), or behind a name
bound to one in the function, an enclosing function or the module. A name
bound to several strings (in two branches, to the items of a tuple, by
``+=``, or by a loop or a comprehension to each item it walks) stands for
each of them, and a pattern built from such names is read as every string it
can be, up to :data:`MOST_PATTERNS`;
one that can be more is refused unread, since reading some of them could
pass a reader by hand. A backtick right after a colon opens a role of
reStructuredText (``:math:`x```), which Markdown does not have, and is not
read as a span.

The site's JavaScript has no parser here, so for it the rule is lexical: no
line of code under ``site/`` but the shared module spells either shape.

A script that reads the docstrings of the library reads reStructuredText,
whose inline literal is two backticks and whose roles open on a colon, and a
script that reads a JavaScript template literal reads no span at all; each
goes in :data:`EXEMPT`, keyed by the file relative to the repository, with
the reason. An entry that covers nothing fails.
"""

from __future__ import annotations

import argparse
import ast
import os
import pathlib
import re
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ast_scan import ROOT, relative, scoped

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

#: The Python scripts this reads; the default, with :data:`SITE`, when no path
#: is given.
SCRIPTS = ROOT / "scripts"
#: The site, whose JavaScript, TypeScript and components this reads.
SITE = ROOT / "site"
#: The two modules that read spans, which every other one calls, and this
#: check, which has to spell the shapes out to look for them.
OWNERS = frozenset(
    {
        (SCRIPTS / "markdown_spans.py").resolve(),
        (SITE / "scripts" / "shared" / "markdown-spans.mjs").resolve(),
        pathlib.Path(__file__).resolve(),
    }
)
#: The suffixes of the site's own code.
_SITE_SUFFIXES = frozenset({".js", ".mjs", ".cjs", ".ts", ".mts", ".astro"})
#: The directories under the site that hold installed or built code.
_SITE_SKIPPED = frozenset({"node_modules", "dist", ".astro"})
#: How a comment line opens in the site's code.
_SITE_COMMENTS = ("//", "/*", "*", "<!--")

#: The functions of ``re`` that take a pattern first.
_RE_FUNCTIONS = frozenset(
    {
        "compile",
        "match",
        "search",
        "fullmatch",
        "findall",
        "finditer",
        "sub",
        "subn",
        "split",
    }
)

#: Padding a reader allows around what a span holds: ``\s*``, ``[ \t]*``,
#: `` ?`` or `` *``, any of them taken any number of times.
_PADDING = r"(?:\\s[*+?]?|\[ ?\\t ?\][*+?]?| [*+?]?)*"
#: A backtick that may open a span, not right after the colon of a role, or a
#: run of them written with a quantifier (``+``, ``{2}``, ``{2,}``), the
#: padding before the group it may open (``(``, ``(?:`` or ``(?P<name>``) and
#: the padding inside it.
_OPENING = re.compile(
    rf"(?<!:)`+(?:\+|\{{\d+(?:,\d*)?\}})?{_PADDING}"
    rf"(?:\((?:\?:|\?P<\w+>)?)?{_PADDING}"
)
#: What a span holds, written by hand: a class of anything but a backtick, or
#: anything at all, taken lazily or not.
_CONTENT = re.compile(r"\[\^[^\]]*`[^\]]*\]|\.[*+]|\(\?:\[\^[^\]]*`")
#: A run of backticks captured, and a backreference that pairs it.
_RUN_GROUP = re.compile(r"\((?:\?P<\w+>)?`\+\)")
_BACKREFERENCE = re.compile(r"\\[1-9]|\(\?P=\w+\)|\\k<\w+>")

#: The most strings one pattern is read as: every combination of the strings
#: its parts stand for is read, and a pattern that can be more is refused
#: unread rather than read in part.
MOST_PATTERNS = 1024

#: Readers that keep their own span logic, keyed by the file relative to the
#: repository, with the reason.
EXEMPT: dict[str, str] = {
    "scripts/check_em_dashes.py": (
        "reads the docstrings of the library, reStructuredText, whose inline "
        "literal is two backticks and whose roles and interpreted text open "
        "on one; a page's list item is read through the shared reader"
    ),
    "scripts/generate_api_docs.py": (
        "converts the docstrings of the library, reStructuredText: it rewrites "
        "their inline literals of two backticks as code spans of one, and "
        "keeps those from the escaping that follows"
    ),
    "site/src/data/reports.mjs": (
        "reads the value of a component's prop, a JavaScript template literal "
        "between braces in an MDX tag, which no code span is"
    ),
    "scripts/check_doc_snippets.py": (
        "reads the JavaScript template literal a guide's code block is kept "
        "in, a const of the page, which no code span is"
    ),
}


@dataclass(frozen=True)
class Finding:
    """One place a script reads a code span by itself, or builds a pattern
    out of more strings than :data:`MOST_PATTERNS`, which is not read.
    """

    path: pathlib.Path
    line: int
    function: str
    source: str
    unread: bool = False

    @property
    def file(self) -> str:
        """The file relative to the repository, as :data:`EXEMPT` keys it."""
        return relative(self.path)

    def describe(self) -> str:
        """One line naming the place and the code."""
        place = f"{self.file}:{self.line}  {self.function}  {self.source}"
        if self.unread:
            return f"{place}  (more than {MOST_PATTERNS} patterns, not read)"
        return place


def reads_span(pattern: str) -> bool:
    """Whether a regular expression reads an inline code span by hand.

    :param pattern: The pattern, as the ``re`` module is handed it.
    :return: Whether it holds a span by its content or by its run.
    """
    for opening in _OPENING.finditer(pattern):
        content = _CONTENT.match(pattern, opening.end())
        if content is not None and "`" in pattern[content.end() :]:
            return True
    return bool(_RUN_GROUP.search(pattern) and _BACKREFERENCE.search(pattern))


class UnreadPatternError(Exception):
    """An expression that stands for more strings than :data:`MOST_PATTERNS`."""


def _combined(parts: Iterable[set[str]]) -> set[str]:
    """Every string the parts make one after the other, a part of none as empty.

    :raises UnreadPatternError: past :data:`MOST_PATTERNS` strings.
    """
    combined = {""}
    for part in parts:
        choices = part or {""}
        if len(combined) * len(choices) > MOST_PATTERNS:
            raise UnreadPatternError
        combined = {head + tail for head in combined for tail in choices}
    return combined


def _either(parts: Iterable[set[str]]) -> set[str]:
    """Every string any of the parts stands for: the sides of a conditional
    expression, or of an ``and`` or an ``or``.

    :raises UnreadPatternError: past :data:`MOST_PATTERNS` strings.
    """
    either: set[str] = set()
    for part in parts:
        either |= part
        if len(either) > MOST_PATTERNS:
            raise UnreadPatternError
    return either


@dataclass
class _Strings:
    """The strings each name of a script stands for, scope by scope.

    A name bound to an expression that stands for more strings than
    :data:`MOST_PATTERNS` stands for ``None``, and so does everything built
    from it.
    """

    bindings: dict[str, dict[str, set[str] | None]] = field(default_factory=dict)

    def bind(self, scope: str, name: str, values: set[str] | None) -> None:
        names = self.bindings.setdefault(scope, {})
        held = names.setdefault(name, set())
        if values is None or held is None:
            names[name] = None
            return
        held.update(values)
        if len(held) > MOST_PATTERNS:
            names[name] = None

    def lookup(self, scope: str, name: str) -> set[str] | None:
        """What *name* stands for seen from *scope*: its own, then outwards."""
        parts = [] if scope == "<module>" else scope.split(".")
        for end in range(len(parts), -1, -1):
            found = self.bindings.get(".".join(parts[:end]) or "<module>", {})
            if name in found:
                return found[name]
        return set()

    def fold(self, node: ast.expr, scope: str) -> set[str]:
        """Every string an expression stands for, as far as the script says.

        :raises UnreadPatternError: for an expression that stands for more
            strings than :data:`MOST_PATTERNS`.
        """
        if isinstance(node, ast.Constant):
            return {node.value} if isinstance(node.value, str) else set()
        if isinstance(node, ast.Name):
            found = self.lookup(scope, node.id)
            if found is None:
                raise UnreadPatternError
            return found
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return _combined(
                [self.fold(node.left, scope), self.fold(node.right, scope)]
            )
        if isinstance(node, ast.JoinedStr):
            return _combined(self._pieces(node, scope))
        if isinstance(node, ast.IfExp):
            return _either([self.fold(node.body, scope), self.fold(node.orelse, scope)])
        if isinstance(node, ast.BoolOp):
            return _either([self.fold(value, scope) for value in node.values])
        if isinstance(node, ast.NamedExpr):
            return self.fold(node.value, scope)
        return set()

    def _pieces(self, node: ast.JoinedStr, scope: str) -> Iterator[set[str]]:
        for value in node.values:
            inner = value.value if isinstance(value, ast.FormattedValue) else value
            yield self.fold(inner, scope)

    def bound(self, value: ast.expr, scope: str) -> set[str] | None:
        """What a name bound to *value* stands for, ``None`` past the bound."""
        try:
            return self.fold(value, scope)
        except UnreadPatternError:
            return None


def _assigned(node: ast.AST) -> Iterator[tuple[str, ast.expr]]:
    """Each name a node binds to an expression, the items of a tuple included.

    An assignment binds its value, ``x += y`` what ``x + y`` makes, and a
    loop or a comprehension each item of what it walks: the items of a tuple,
    a list or a set written out, or the strings a name it walks stands for.
    """
    value: ast.expr | None
    if isinstance(node, ast.Assign):
        targets: list[ast.expr] = list(node.targets)
        value = node.value
    elif isinstance(node, ast.AnnAssign | ast.NamedExpr):
        targets, value = [node.target], node.value
    elif isinstance(node, ast.AugAssign) and isinstance(node.op, ast.Add):
        targets = [node.target]
        value = ast.BinOp(left=node.target, op=ast.Add(), right=node.value)
    elif isinstance(node, ast.For | ast.AsyncFor | ast.comprehension):
        targets, value = [node.target], node.iter
    else:
        return
    for target in targets:
        if isinstance(target, ast.Name) and value is not None:
            items = (
                value.elts
                if isinstance(value, ast.Tuple | ast.List | ast.Set)
                else [value]
            )
            yield from ((target.id, item) for item in items)


def _re_names(tree: ast.Module) -> tuple[set[str], set[str]]:
    """The names ``re`` goes by in a script, and the functions imported from it."""
    modules: set[str] = set()
    functions: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(a.asname or a.name for a in node.names if a.name == "re")
        elif isinstance(node, ast.ImportFrom) and node.module == "re":
            functions.update(
                a.asname or a.name for a in node.names if a.name in _RE_FUNCTIONS
            )
    return modules, functions


def _patterns(node: ast.Call, names: tuple[set[str], set[str]]) -> list[ast.expr]:
    """The pattern a call hands ``re``, when it calls a function that takes one."""
    modules, functions = names
    function = node.func
    is_re = (isinstance(function, ast.Name) and function.id in functions) or (
        isinstance(function, ast.Attribute)
        and function.attr in _RE_FUNCTIONS
        and isinstance(function.value, ast.Name)
        and function.value.id in modules
    )
    if not is_re:
        return []
    return [*node.args[:1], *(k.value for k in node.keywords if k.arg == "pattern")]


def _python_findings(path: pathlib.Path) -> list[Finding]:
    """The calls of one Python script that read a code span by hand."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    strings = _Strings()
    nodes = list(scoped(tree))
    for scope, node in nodes:
        for name, value in _assigned(node):
            strings.bind(scope, name, strings.bound(value, scope))
    names = _re_names(tree)
    found: list[Finding] = []
    for scope, node in nodes:
        if not isinstance(node, ast.Call):
            continue
        patterns = _patterns(node, names)
        if not patterns:
            continue
        segment = ast.get_source_segment(source, node) or ast.unparse(node)
        try:
            texts = {t for p in patterns for t in strings.fold(p, scope)}
        except UnreadPatternError:
            found.append(Finding(path, node.lineno, scope, segment, unread=True))
            continue
        if any(reads_span(text) for text in texts):
            found.append(Finding(path, node.lineno, scope, segment))
    return found


def _site_findings(path: pathlib.Path) -> list[Finding]:
    """The lines of one file of the site's code that read a code span by hand."""
    found: list[Finding] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        code = line.strip()
        if not code.startswith(_SITE_COMMENTS) and reads_span(code):
            found.append(Finding(path, number, "<script>", code))
    return found


def findings(path: pathlib.Path) -> list[Finding]:
    """The places in one script that read a code span without the shared reader.

    :param path: A Python file, or a file of the site's JavaScript, TypeScript
        or components.
    :return: One :class:`Finding` per place, in source order.
    """
    if path.suffix in _SITE_SUFFIXES:
        return _site_findings(path)
    return _python_findings(path)


def _site_files(root: pathlib.Path) -> list[pathlib.Path]:
    """The site's own code under ``root``, installed and built code left out."""
    found: list[pathlib.Path] = []
    for directory, subdirectories, names in os.walk(root):
        subdirectories[:] = sorted(d for d in subdirectories if d not in _SITE_SKIPPED)
        found.extend(
            pathlib.Path(directory) / name
            for name in sorted(names)
            if pathlib.Path(name).suffix in _SITE_SUFFIXES
        )
    return found


def files(arguments: Sequence[str]) -> list[pathlib.Path]:
    """The files named, the scripts under the directories named, or the defaults.

    :param arguments: Files or directories; none means ``scripts/`` and ``site/``.
    :return: The Python files and the files of site code to read.
    """
    if not arguments:
        return [*sorted(SCRIPTS.rglob("*.py")), *_site_files(SITE)]
    found: list[pathlib.Path] = []
    for argument in arguments:
        path = pathlib.Path(argument)
        if path.is_dir():
            found.extend([*sorted(path.rglob("*.py")), *_site_files(path)])
        else:
            found.append(path)
    return found


def check(
    paths: Iterable[pathlib.Path], exempt: dict[str, str]
) -> tuple[list[Finding], list[str], int]:
    """The hand-written readings, the stale exemptions and the files read.

    :param paths: The files to read.
    :param exempt: The escape hatch, file to reason.
    :return: The findings no exemption covers, the exempted files that read
        no span any more, and how many files were read.
    """
    read = [path for path in paths if path.resolve() not in OWNERS]
    every = [finding for path in read for finding in findings(path)]
    kept = [finding for finding in every if finding.file not in exempt]
    used = {finding.file for finding in every}
    return kept, sorted(set(exempt) - used), len(read)


def main(argv: list[str] | None = None) -> int:
    """Report every script that reads a code span without the shared reader."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        help="files or directories to read (default: scripts/ and site/)",
    )
    arguments = parser.parse_args(argv)
    found, stale, read = check(files(arguments.paths), EXEMPT)
    if not found and not stale:
        print(f"None of the {read} scripts reads an inline code span by hand.")
        return 0
    if found:
        print(f"::error::{len(found)} place(s) read an inline code span by hand")
        for finding in found:
            print(f"  {finding.describe()}")
        print(
            "  -> read the spans through scripts/markdown_spans.py: inline_spans(), "
            "blank_inline_spans() or drop_inline_spans(); in the site's code "
            "through site/scripts/shared/markdown-spans.mjs. If it cannot, add "
            "the file to EXEMPT in scripts/check_span_readers.py with the reason. "
            f"A pattern built from more than {MOST_PATTERNS} strings is not read: "
            "build it from fewer."
        )
    for path in stale:
        print(f"::error::EXEMPT lists {path}, which no longer reads a code span")
    return 1


if __name__ == "__main__":
    sys.exit(main())
