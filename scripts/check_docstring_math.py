#!/usr/bin/env python3
r"""Fail on mathematics in the sources that KaTeX will refuse to render.

Two shapes, each of which the site build only finds at the end, after every
page has been rendered, and each of which ships a page whose formula is an
error message and whose following block may be swallowed.

1. **A doubled backslash in a docstring.** ``generate_api_docs.py`` copies the
   mathematics of a docstring to the site verbatim: ``:math:`\mathrm{DL}_2```
   becomes ``$\mathrm{DL}_2$`` and a ``.. math::`` block becomes a display
   formula. KaTeX then reads what the docstring actually holds, and
   ``\\mathrm`` is not ``\mathrm``: it is a line break with a ``mathrm`` after
   it, which KaTeX refuses with *Got function '\\' with no arguments as
   subscript*.

   The defect is invisible in review because both spellings look right in the
   two kinds of docstring this tree has. In a docstring opened with an ``r``
   prefix, one backslash is one backslash and ``\\mathrm`` is the defect. In
   one without it, two backslashes are how a single backslash is written and
   that same spelling is correct. Reading the file as text cannot tell the two
   apart, so this reads the *value* of each docstring, the way Python builds
   it, and judges that.

   What it looks for is a backslash immediately followed by another backslash
   and then a letter. A ``\\`` that ends a row of an ``aligned`` block is
   followed by a newline, never by a letter, so the rule costs no legitimate
   construct, and the corpus confirms it: zero occurrences outside the defect
   it was written for.

2. **A bare command as a sub- or superscript**, in a docstring or in a
   hand-written page. KaTeX takes a single symbol there, ``x_\alpha`` or
   ``10^\circ``, and a font or text command, ``R_\mathrm{w}``, but a command
   that wants an argument of its own is refused: ``|dL_n|_\max`` in the ISO
   17534-1 pages rendered as *Got function '\max' with no arguments as
   subscript* in place of the formula, and an accent (``x_\bar{a}``), a root
   (``x_\sqrt{2}``) or ``\operatorname`` fail the same way. Braces render the
   same glyphs and are right for every command, ``|dL_n|_{\max}``, so the rule
   is a list of what KaTeX *takes* bare rather than of what it refuses: a
   command it takes but the list omits only asks for braces it did not need,
   while a refusal a list forgot would ship.

   In a docstring the rule reads the mathematics ``generate_api_docs.py``
   publishes, the ``:math:`` roles and the ``.. math::`` blocks. In a page it
   reads the prose outside code, since a ``_\`` or a ``^\`` there is always
   TeX; the generated API reference is left to its docstrings.

The site's own ``check-math-render.mjs`` catches both, but only after a full
build of every page, which is twelve minutes, and never in a docstring the
reference does not publish. This reads the sources, so it costs a second and
can run before the commit.

Exit status 0 when every docstring and page is clean, 1 otherwise.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from markdown_fences import code_lines

if TYPE_CHECKING:
    from collections.abc import Iterator

#: The repository, for paths a reader can click.
_REPO = Path(__file__).resolve().parent.parent

#: The package whose docstrings the API reference publishes.
_ROOT = _REPO / "src" / "phonometry"

#: Trees of hand-written pages. The API reference is generated from the
#: docstrings, which are read at their source, and ``superpowers/`` is local
#: working notes.
_PAGE_ROOTS = (_REPO / "site" / "src" / "content" / "docs", _REPO / "docs")
_PAGE_SKIP = ("reference/api/", "superpowers/")

#: A backslash pair followed by a letter: the one shape that is a defect in
#: every docstring of this tree and a legitimate construct in none.
_DOUBLED = re.compile(r"\\\\[A-Za-z]")

#: A sub- or superscript whose argument is a bare command, spaces allowed.
_BARE_SCRIPT = re.compile(r"[_^]\s*\\([A-Za-z]+)")

#: The commands KaTeX takes bare as a sub- or superscript: the Greek letters
#: and a few symbols, each a single atom, and the font and text commands, which
#: it allows as an argument. Each one renders both ways, ``x_\name`` and
#: ``x^\name``, under the KaTeX the site pins. Anything else goes in braces.
BARE_SCRIPT_COMMANDS = frozenset(
    {
        # Greek, lower case and the variants.
        "alpha",
        "beta",
        "gamma",
        "delta",
        "epsilon",
        "varepsilon",
        "zeta",
        "eta",
        "theta",
        "vartheta",
        "iota",
        "kappa",
        "varkappa",
        "lambda",
        "mu",
        "nu",
        "xi",
        "pi",
        "varpi",
        "rho",
        "varrho",
        "sigma",
        "varsigma",
        "tau",
        "upsilon",
        "phi",
        "varphi",
        "chi",
        "psi",
        "omega",
        # Greek, upper case.
        "Gamma",
        "Delta",
        "Theta",
        "Lambda",
        "Xi",
        "Pi",
        "Sigma",
        "Upsilon",
        "Phi",
        "Psi",
        "Omega",
        # Symbols.
        "infty",
        "circ",
        "prime",
        "ast",
        "star",
        "dagger",
        "ddagger",
        "ell",
        "perp",
        "parallel",
        "partial",
        "nabla",
        "bullet",
        # Font and text commands.
        "mathrm",
        "mathit",
        "mathbf",
        "mathsf",
        "mathtt",
        "mathcal",
        "mathbb",
        "mathfrak",
        "text",
        "textrm",
        "textit",
        "textbf",
    }
)

#: The inline mathematics of a docstring, as ``generate_api_docs.py`` reads it.
_MATH_ROLE = re.compile(r":math:`([^`]+)`")

#: An inline code span in a page: a run of backticks, its text, and a run of
#: the same length again.
_CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")

#: How much of the line to show either side of the hit.
_CONTEXT = 30

_DOCUMENTED = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def bare_script_commands(tex: str) -> list[re.Match[str]]:
    r"""Every sub- or superscript in ``tex`` whose bare argument KaTeX refuses.

    Group 1 of each match is the command's name, without its backslash.
    """
    return [
        match
        for match in _BARE_SCRIPT.finditer(tex)
        if match.group(1) not in BARE_SCRIPT_COMMANDS
    ]


def _excerpt(text: str, start: int, end: int) -> str:
    """The passage round ``text[start:end]``, on one line."""
    return text[max(0, start - _CONTEXT) : end + _CONTEXT].replace("\n", " ").strip()


def _docstrings(path: Path) -> Iterator[tuple[int, str]]:
    """Each docstring of one file, as Python builds it, with the line it opens on."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, _DOCUMENTED):
            continue
        doc = ast.get_docstring(node, clean=False)
        if doc is None:
            continue
        # The docstring is the first statement, and its own line is where the
        # literal opens: counting from the class or function would point at the
        # signature instead of at the passage.
        yield node.body[0].lineno, doc


def _math_spans(doc: str) -> Iterator[tuple[int, str]]:
    """The mathematics of a docstring, each piece with its offset in it.

    Each ``:math:`` role, and each line of a ``.. math::`` block: the directive,
    which may carry a formula of its own, and every line after it that is blank
    or indented deeper than it.
    """
    for role in _MATH_ROLE.finditer(doc):
        yield role.start(1), role.group(1)
    offset = 0
    directive: int | None = None
    for line in doc.splitlines(keepends=True):
        depth = len(line) - len(line.lstrip())
        if directive is not None and line.strip() and depth <= directive:
            directive = None
        if directive is None and line.lstrip().startswith(".. math::"):
            directive = depth
        if directive is not None:
            yield offset, line
        offset += len(line)


def _findings(path: Path) -> list[tuple[int, str]]:
    """Every doubled backslash in the docstrings of one file, with its line."""
    return [
        (
            opens + doc[: match.start()].count("\n"),
            _excerpt(doc, match.start(), match.end()),
        )
        for opens, doc in _docstrings(path)
        for match in _DOUBLED.finditer(doc)
    ]


def _bare_scripts(path: Path) -> list[tuple[int, str, str]]:
    """Every refused bare script in the docstrings of one file: line, command, passage."""
    found: list[tuple[int, str, str]] = []
    for opens, doc in _docstrings(path):
        for offset, tex in _math_spans(doc):
            for match in bare_script_commands(tex):
                start, end = offset + match.start(), offset + match.end()
                found.append(
                    (
                        opens + doc[:start].count("\n"),
                        match.group(1),
                        _excerpt(doc, start, end),
                    )
                )
    return found


def _page_bare_scripts(path: Path) -> list[tuple[int, str, str]]:
    """Every refused bare script in the prose of one page: line, command, passage."""
    found: list[tuple[int, str, str]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for number, (line, code) in enumerate(
        zip(lines, code_lines(lines), strict=True), start=1
    ):
        if code:
            continue
        prose = _CODE_SPAN.sub("", line)
        for match in bare_script_commands(prose):
            excerpt = _excerpt(prose, match.start(), match.end())
            found.append((number, match.group(1), excerpt))
    return found


def _pages() -> Iterator[Path]:
    """Every hand-written page, in a stable order."""
    for root in _PAGE_ROOTS:
        for path in sorted(root.rglob("*.md*")):
            if not any(part in path.as_posix() for part in _PAGE_SKIP):
                yield path


def main() -> int:
    """Report every passage whose mathematics KaTeX would refuse."""
    doubled = 0
    bare = 0
    files = 0
    for path in sorted(_ROOT.rglob("*.py")):
        files += 1
        relative = path.relative_to(_REPO)
        for line, excerpt in _findings(path):
            doubled += 1
            print(f"{relative}:{line}: doubled backslash in a docstring")
            print(f"    ...{excerpt}...")
        for line, command, excerpt in _bare_scripts(path):
            bare += 1
            print(f"{relative}:{line}: \\{command} bare as a script in a docstring")
            print(f"    ...{excerpt}...")
    pages = 0
    for path in _pages():
        pages += 1
        for line, command, excerpt in _page_bare_scripts(path):
            bare += 1
            print(f"{path.relative_to(_REPO)}:{line}: \\{command} bare as a script")
            print(f"    ...{excerpt}...")
    if doubled:
        print()
        print(
            f"{doubled} docstring passage(s) carry a doubled backslash. Write the "
            "single backslash the mathematics needs: a raw docstring takes "
            r"\mathrm, a plain one \\mathrm."
        )
    if bare:
        print()
        print(
            f"{bare} formula(s) give a sub- or superscript a bare command that "
            "KaTeX refuses with 'Got function ... with no arguments'. Brace the "
            r"argument: |dL_n|_{\max}, not |dL_n|_\max."
        )
    if doubled or bare:
        return 1
    print(f"Every formula reaches the page intact: {files} modules and {pages} pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
