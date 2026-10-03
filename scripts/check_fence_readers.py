#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a script that decides for itself where a markdown fence opens or closes.

A fence closes only on a line of its own marker, at least as long as the run
that opened it, with nothing after it (CommonMark 0.31.2, 4.5). The scripts
that read the pages used to work that out each in their own way: a flag
flipped on any line that started with three backticks, a slice of three
characters compared with a tuple, a regular expression that ran to the next
three backticks anywhere. Each was right on the pages it was written against
and each read a page that shows a fence inside another one inside out, code as
prose and prose as code, and one of them never saw a tilde fence at all.
``scripts/markdown_fences.py`` now reads fences for every Python script, and
``site/src/lib/markdown-fences.mjs``, the same reading in JavaScript, for the
site's own scripts and components. This keeps it that way.

It reads every Python script under ``scripts/`` but the shared reader and
itself, and refuses three shapes a hand-rolled reader cannot avoid:

- **A toggle**: a name that says it holds whether the reader is inside a
  fence, a code block or a block, flipped with ``not`` or with ``^ True``
  (``fenced = not fenced``, ``in_code = not in_code``, ``in_block ^= True``).
- **A test for a marker**: a string that opens with three backticks or three
  tildes compared with ``==``, ``!=``, ``in`` or ``not in``, or handed to a
  string method that looks for it in a line (``startswith``, ``endswith``,
  ``count``, ``find``, ``split`` and their kin), alone or in a tuple.
- **A pattern for a marker**: a regular expression handed to the ``re``
  module that holds three backticks or three tildes, written out, as a ``{3``
  repetition of one, or as a repetition of a class or a group that holds one
  (``[`~]{3,}``).

A string is read the way Python builds it: written out, repeated (``"`" * 3``),
joined with ``+`` or in an f-string, or behind a name bound to one in the
function, an enclosing function or the module, a loop over a tuple of them
included. A piece spliced into a larger string counts when every alternative
it offers looks for a marker. The markdown hazard check splices in a list of
everything that opens a block, a fence among them, to find a wrapped line that
would open one; that is no reading of fences, and it is not refused.

A toggle's name has to say what it holds: the figure checks flip ``inside`` on
every edge of an outline by the even-odd rule, and the markdown checks flip
display maths, and neither reads a fence.

The site's JavaScript has no parser here, so for it the rule is lexical and
stricter: no line of code under ``site/`` but the shared module spells three
backticks or tildes, in any of the forms above or as ``'`'.repeat(3)``, and
none flips a flag named for a fence, a code block or a block.

A script that writes a fence, as the API reference and the llms generators
do, puts the marker in a list or an f-string and is none of these. A
legitimate reader that cannot use the shared one goes in :data:`EXEMPT`, keyed
by file and function (``"<script>"`` for the site's JavaScript), with the
reason.
"""

from __future__ import annotations

import argparse
import ast
import itertools
import os
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ast_scan import ROOT, exempted, relative, scoped

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sequence

#: The Python scripts this reads; the default, with :data:`SITE`, when no path
#: is given.
SCRIPTS = ROOT / "scripts"
#: The site, whose JavaScript, TypeScript and components this reads.
SITE = ROOT / "site"
#: The two modules that read fences, which every other one calls, and this
#: check, which has to spell the markers out to look for them.
OWNERS = frozenset(
    {
        (SCRIPTS / "markdown_fences.py").resolve(),
        (SITE / "src" / "lib" / "markdown-fences.mjs").resolve(),
        pathlib.Path(__file__).resolve(),
    }
)
#: The suffixes of the site's own code.
_SITE_SUFFIXES = frozenset({".js", ".mjs", ".cjs", ".ts", ".mts", ".astro"})
#: The directories under the site that hold installed or built code.
_SITE_SKIPPED = frozenset({"node_modules", "dist", ".astro"})

#: A name that says it holds the state of a fence.
_STATE_NAME = re.compile(r"fence|code|block", re.IGNORECASE)
#: Three markers, written out, as a repetition of one, or as a repetition of a
#: class or a group that holds one.
_PATTERN_MARKER = re.compile(r"```|~~~|[`~]\{3|[\[(][^\])]*[`~][^\])]*[\])]\{3")
#: A marker character escaped in a pattern, which matches the character itself.
_ESCAPED_MARKER = re.compile(r"\\([`~])")
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
#: The string methods that look for their argument in a line.
_MARKER_SEARCHES = frozenset(
    {
        "startswith",
        "endswith",
        "removeprefix",
        "removesuffix",
        "count",
        "find",
        "rfind",
        "index",
        "rindex",
        "split",
        "rsplit",
        "partition",
        "rpartition",
    }
)
#: How many strings one expression may stand for before the rest are dropped,
#: and the longest repetition that is worked out.
_MAX_VALUES = 64
_MAX_REPEAT = 1000

#: A flag named for a fence, a code block or a block, flipped in JavaScript.
_SCRIPT_TOGGLE = re.compile(
    r"(?P<name>[\w$.]*(?:fence|code|block)[\w$]*)\s*"
    r"(?:=\s*!\s*(?P=name)(?![\w$])|\^=\s*(?:true|1)\b)",
    re.IGNORECASE,
)
#: A marker character repeated three times in JavaScript.
_SCRIPT_REPEAT = re.compile(r"""(['"])[`~]\1\.repeat\(\s*3\s*\)""")
#: How a comment line opens in the site's code.
_SCRIPT_COMMENTS = ("//", "/*", "*", "<!--")

#: Readers that keep their own fence logic, and why, keyed by the file relative
#: to the repository and the name of the function that holds the reading.
EXEMPT: dict[tuple[str, str], str] = {}

#: The strings a name in scope stands for.
type Lookup = Callable[[str], frozenset[str]]


@dataclass(frozen=True)
class Finding:
    """One place a script reads a fence by itself."""

    path: pathlib.Path
    line: int
    function: str
    shape: str
    source: str

    @property
    def key(self) -> tuple[str, str]:
        """The file relative to the repository, and the function, as EXEMPT keys them."""
        return relative(self.path), self.function

    def describe(self) -> str:
        """One line naming the place, the shape and the code."""
        return (
            f"{relative(self.path)}:{self.line}  {self.function}  "
            f"{self.shape}: {self.source}"
        )


def _is_marker(value: str) -> bool:
    """Whether a string opens with a fence marker."""
    return value.lstrip(" \t").startswith(("```", "~~~"))


def _looks_for_marker(pattern: str) -> bool:
    """Whether a pattern holds three markers in one of the forms it can take."""
    return _PATTERN_MARKER.search(_ESCAPED_MARKER.sub(r"\1", pattern)) is not None


def _alternatives(pattern: str) -> list[str]:
    """The alternatives of a regular expression outside any group or class."""
    alternatives: list[str] = []
    depth, start, escaped, in_class = 0, 0, False, False
    for index, character in enumerate(pattern):
        if escaped:
            escaped = False
        elif character == "\\":
            escaped = True
        elif in_class:
            in_class = character != "]"
        elif character in "()":
            depth += 1 if character == "(" else -1
        elif character == "[":
            in_class = True
        elif character == "|" and depth == 0:
            alternatives.append(pattern[start:index])
            start = index + 1
    return [*alternatives, pattern[start:]]


def _spliceable(value: str) -> bool:
    """Whether every alternative a piece of a string offers looks for a marker."""
    return all(_looks_for_marker(part) for part in _alternatives(value))


def _joined(parts: Iterable[frozenset[str]]) -> frozenset[str]:
    """Every string the pieces make when written one after the other."""
    texts = frozenset({""})
    for part in parts:
        made = (text + piece for text in texts for piece in part)
        texts = frozenset(itertools.islice(made, _MAX_VALUES))
    return texts


def _part(node: ast.expr, lookup: Lookup) -> frozenset[str]:
    """What an expression adds to a larger string.

    Written out, it adds itself. Built or behind a name, it adds the strings it
    stands for that look for a marker and nothing else, so that a list of the
    lines that open any block spliced into a pattern does not make the pattern
    a fence reader.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return frozenset({node.value})
    spliced = frozenset(value for value in _fold(node, lookup) if _spliceable(value))
    return spliced or frozenset({""})


def _repeated(node: ast.BinOp, lookup: Lookup) -> frozenset[str]:
    """The strings ``text * count`` stands for, with the count written out."""
    for text, times in ((node.left, node.right), (node.right, node.left)):
        count = times.value if isinstance(times, ast.Constant) else None
        if type(count) is int and 0 <= count <= _MAX_REPEAT:
            return frozenset(value * count for value in _fold(text, lookup))
    return frozenset()


def _fold(node: ast.expr, lookup: Lookup) -> frozenset[str]:
    """Every string an expression stands for, as far as its file says."""
    if isinstance(node, ast.Constant):
        return frozenset({node.value}) if isinstance(node.value, str) else frozenset()
    if isinstance(node, ast.Name):
        return lookup(node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return _joined([_part(node.left, lookup), _part(node.right, lookup)])
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
        return _repeated(node, lookup)
    if isinstance(node, ast.JoinedStr):
        return _joined(
            _part(
                value.value if isinstance(value, ast.FormattedValue) else value, lookup
            )
            for value in node.values
        )
    return frozenset()


def _values(node: ast.expr, lookup: Lookup) -> frozenset[str]:
    """The strings a name bound to an expression stands for, a collection's items included."""
    if isinstance(node, ast.Tuple | ast.List | ast.Set):
        return frozenset().union(*(_fold(element, lookup) for element in node.elts))
    return _fold(node, lookup)


def _bound(node: ast.AST) -> Iterator[tuple[str, ast.expr | None]]:
    """The names a node binds, each with the expression it binds or ``None``.

    An assignment binds its value, a loop each item of what it walks, and a
    function its parameters, to what nothing here can know.
    """
    if isinstance(node, ast.Assign):
        yield from ((t.id, node.value) for t in node.targets if isinstance(t, ast.Name))
    elif isinstance(node, ast.AnnAssign | ast.NamedExpr):
        if isinstance(node.target, ast.Name) and node.value is not None:
            yield node.target.id, node.value
    elif isinstance(node, ast.For | ast.AsyncFor | ast.comprehension):
        if isinstance(node.target, ast.Name):
            yield node.target.id, node.iter
    elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        arguments = node.args
        every = [*arguments.posonlyargs, *arguments.args, *arguments.kwonlyargs]
        every += [a for a in (arguments.vararg, arguments.kwarg) if a is not None]
        yield from ((argument.arg, None) for argument in every)


def _chain(scope: str) -> list[str]:
    """The scopes a name is looked up in from ``scope``, innermost first."""
    if scope == "<module>":
        return [scope]
    parts = scope.split(".")
    return [".".join(parts[:end]) for end in range(len(parts), 0, -1)] + ["<module>"]


def _re_names(tree: ast.Module) -> tuple[set[str], set[str]]:
    """The names ``re`` goes by in a file, and the functions imported from it."""
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


@dataclass(frozen=True)
class _File:
    """What one script binds that the shapes are read against."""

    #: Per scope, the strings each name bound there stands for.
    bindings: dict[str, dict[str, frozenset[str]]]
    #: The names ``re`` goes by, and the functions imported from it.
    re_modules: frozenset[str]
    re_functions: frozenset[str]

    @classmethod
    def of(cls, tree: ast.Module) -> _File:
        """Read what a parsed script binds, in source order."""
        modules, functions = _re_names(tree)
        file = cls({}, frozenset(modules), frozenset(functions))
        # ``scoped`` names a function after itself, so its parameters land in
        # its own scope with the names its body binds.
        for scope, node in scoped(tree):
            names = file.bindings.setdefault(scope, {})
            lookup = file.lookup(scope)
            for name, value in _bound(node):
                found = frozenset() if value is None else _values(value, lookup)
                names[name] = names.get(name, frozenset()) | found
        return file

    def lookup(self, scope: str) -> Lookup:
        """The strings a name stands for, seen from ``scope``."""
        chain = _chain(scope)

        def find(name: str) -> frozenset[str]:
            for link in chain:
                values = self.bindings.get(link, {}).get(name)
                if values is not None:
                    return values
            return frozenset()

        return find


def _holds_marker(node: ast.expr, lookup: Lookup) -> bool:
    """Whether an operand is a marker, stands for one, or is a collection of them."""
    if isinstance(node, ast.Tuple | ast.List | ast.Set):
        return any(_holds_marker(element, lookup) for element in node.elts)
    return any(_is_marker(value) for value in _fold(node, lookup))


def _is_true(node: ast.expr) -> bool:
    """Whether an expression is ``True`` or ``1`` written out."""
    value = node.value if isinstance(node, ast.Constant) else None
    return value is True or (type(value) is int and value == 1)


def _flipped(node: ast.AST) -> str | None:
    """The name a node flips, with ``not`` or with ``^ True``, if it flips one."""
    if isinstance(node, ast.AugAssign):
        flips = isinstance(node.op, ast.BitXor) and _is_true(node.value)
        return ast.unparse(node.target) if flips else None
    if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
        return None
    target, value = ast.unparse(node.targets[0]), node.value
    if isinstance(value, ast.UnaryOp) and isinstance(value.op, ast.Not):
        operands = [value.operand]
    elif isinstance(value, ast.BinOp) and isinstance(value.op, ast.BitXor):
        sides = ((value.left, value.right), (value.right, value.left))
        operands = [side for side, other in sides if _is_true(other)]
    else:
        return None
    return target if any(ast.unparse(o) == target for o in operands) else None


def _is_toggle(node: ast.AST) -> bool:
    """Whether a node flips a name that holds the state of a fence."""
    name = _flipped(node)
    return name is not None and _STATE_NAME.search(name) is not None


def _tests_marker(node: ast.AST, lookup: Lookup) -> bool:
    """Whether a node compares a line with a marker, or looks for one in it."""
    if isinstance(node, ast.Compare):
        return any(
            _holds_marker(side, lookup) for side in [node.left, *node.comparators]
        )
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in _MARKER_SEARCHES
        and any(_holds_marker(argument, lookup) for argument in node.args)
    )


def _is_re_call(node: ast.Call, file: _File) -> bool:
    """Whether a call goes to a function of ``re`` that takes a pattern first."""
    function = node.func
    if isinstance(function, ast.Name):
        return function.id in file.re_functions
    return (
        isinstance(function, ast.Attribute)
        and function.attr in _RE_FUNCTIONS
        and isinstance(function.value, ast.Name)
        and function.value.id in file.re_modules
    )


def _matches_marker(node: ast.AST, file: _File, lookup: Lookup) -> bool:
    """Whether a node hands ``re`` a pattern that looks for a marker."""
    if not isinstance(node, ast.Call) or not _is_re_call(node, file):
        return False
    patterns = [*node.args[:1], *(k.value for k in node.keywords if k.arg == "pattern")]
    return any(
        _looks_for_marker(text)
        for pattern in patterns
        for text in _fold(pattern, lookup)
    )


def _shape(node: ast.AST, file: _File, lookup: Lookup) -> str | None:
    """Which hand-rolled reading a node is, or ``None``."""
    if _is_toggle(node):
        return "a toggle"
    if _tests_marker(node, lookup):
        return "a test for a marker"
    if _matches_marker(node, file, lookup):
        return "a pattern for a marker"
    return None


def _python_findings(path: pathlib.Path) -> list[Finding]:
    """The places in one Python script that read a fence by hand."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    file = _File.of(tree)
    found: list[Finding] = []
    for function, node in scoped(tree):
        shape = _shape(node, file, file.lookup(function))
        if shape is not None:
            found.append(
                Finding(
                    path=path,
                    line=getattr(node, "lineno", 0),
                    function=function,
                    shape=shape,
                    source=ast.get_source_segment(source, node) or ast.unparse(node),
                )
            )
    return found


def _script_shape(code: str) -> str | None:
    """Which hand-rolled reading a line of the site's code is, or ``None``."""
    if code.startswith(_SCRIPT_COMMENTS):
        return None
    if _SCRIPT_TOGGLE.search(code):
        return "a toggle"
    if _looks_for_marker(code) or _SCRIPT_REPEAT.search(code):
        return "a marker in a script"
    return None


def _site_findings(path: pathlib.Path) -> list[Finding]:
    """The lines of one file of the site's code that read a fence by hand."""
    found: list[Finding] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, line in enumerate(lines, start=1):
        shape = _script_shape(line.strip())
        if shape is not None:
            found.append(Finding(path, number, "<script>", shape, line.strip()))
    return found


def findings(path: pathlib.Path) -> list[Finding]:
    """The places in one script that read a fence without the shared reader.

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
    paths: Iterable[pathlib.Path], exempt: dict[tuple[str, str], str]
) -> tuple[list[Finding], list[tuple[str, str]], int]:
    """The hand-rolled readings, the stale exemptions and the number of files read.

    :param paths: The files to read.
    :param exempt: The escape hatch, ``(file, function)`` to reason.
    :return: The findings no exemption covers, the exemptions that cover no
        finding any more, and how many files were read.
    """
    read = [path for path in paths if path.resolve() not in OWNERS]
    kept, stale = exempted([f for path in read for f in findings(path)], exempt)
    return kept, stale, len(read)


def main(argv: list[str] | None = None) -> int:
    """Report every script that reads a fence without the shared reader."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        help="files or directories to read (default: scripts/ and site/)",
    )
    arguments = parser.parse_args(argv)
    found, stale, read = check(files(arguments.paths), EXEMPT)
    if not found and not stale:
        print(f"None of the {read} scripts reads a markdown fence by hand.")
        return 0
    if found:
        print(f"::error::{len(found)} place(s) read a markdown fence by hand")
        for finding in found:
            print(f"  {finding.describe()}")
        print(
            "  -> read the page through scripts/markdown_fences.py: code_lines() "
            "for which lines are code, fences() or python_fences() for the "
            "blocks; in the site's code through site/src/lib/markdown-fences.mjs: "
            "codeLines(), prose() or fences(). If it cannot, add it to EXEMPT in "
            "scripts/check_fence_readers.py with the reason."
        )
    for path, function in stale:
        print(f"::error::EXEMPT lists {path} {function}, which no longer reads a fence")
    return 1


if __name__ == "__main__":
    sys.exit(main())
