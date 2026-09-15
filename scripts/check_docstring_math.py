#!/usr/bin/env python3
r"""Fail on a docstring whose mathematics carries a backslash that reaches KaTeX doubled.

``generate_api_docs.py`` copies the mathematics of a docstring to the site
verbatim: ``:math:`\mathrm{DL}_2``` becomes ``$\mathrm{DL}_2$`` and a ``..
math::`` block becomes a display formula. KaTeX then reads what the docstring
actually holds, and ``\\mathrm`` is not ``\mathrm``: it is a line break with a
``mathrm`` after it, which KaTeX refuses with *Got function '\\' with no
arguments as subscript*. The page still ships, and everything after the bad
block may be swallowed.

The defect is invisible in review because both spellings look right in the two
kinds of docstring this tree has. In a docstring opened with an ``r`` prefix,
one backslash is one backslash and ``\\mathrm`` is the defect. In one without
it, two backslashes are how a single backslash is written and that same
spelling is correct. Reading the file as text cannot tell the two apart, so
this reads the *value* of each docstring, the way Python builds it, and judges
that.

What it looks for is a backslash immediately followed by another backslash and
then a letter. A ``\\`` that ends a row of an ``aligned`` block is followed by
a newline, never by a letter, so the rule costs no legitimate construct, and
the corpus confirms it: zero occurrences outside the defect it was written for.

The site's own ``check-math-render.mjs`` catches the same thing, but only after
a full build of every page, which is twelve minutes and runs in CI alone. This
reads the sources, so it costs a second and can run before the commit.

Exit status 0 when every docstring is clean, 1 otherwise.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

#: The repository, for paths a reader can click.
_REPO = Path(__file__).resolve().parent.parent

#: The package whose docstrings the API reference publishes.
_ROOT = _REPO / "src" / "phonometry"

#: A backslash pair followed by a letter: the one shape that is a defect in
#: every docstring of this tree and a legitimate construct in none.
_DOUBLED = re.compile(r"\\\\[A-Za-z]")

#: How much of the line to show either side of the hit.
_CONTEXT = 30

_DOCUMENTED = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


def _findings(path: Path) -> list[tuple[int, str]]:
    """Every doubled backslash in the docstrings of one file, with its line."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, _DOCUMENTED):
            continue
        doc = ast.get_docstring(node, clean=False)
        if doc is None:
            continue
        # The docstring is the first statement, and its own line is where the
        # literal opens: counting from the class or function would point at the
        # signature instead of at the passage.
        opens = node.body[0].lineno
        for match in _DOUBLED.finditer(doc):
            start = max(0, match.start() - _CONTEXT)
            excerpt = doc[start : match.end() + _CONTEXT].replace("\n", " ")
            found.append((opens + doc[: match.start()].count("\n"), excerpt.strip()))
    return found


def main() -> int:
    """Report every docstring whose mathematics would reach KaTeX doubled."""
    bad = 0
    files = 0
    for path in sorted(_ROOT.rglob("*.py")):
        files += 1
        for line, excerpt in _findings(path):
            bad += 1
            relative = path.relative_to(_REPO)
            print(f"{relative}:{line}: doubled backslash in a docstring")
            print(f"    ...{excerpt}...")
    if bad:
        print()
        print(
            f"{bad} docstring passage(s) carry a doubled backslash. Write the "
            "single backslash the mathematics needs: a raw docstring takes "
            r"\mathrm, a plain one \\mathrm."
        )
        return 1
    print(f"Every docstring's mathematics reaches the page intact: {files} modules.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
