#!/usr/bin/env python3
r"""Fail on a grouped decimal whose groups are held apart by a breakable space.

ISO 80000-1 and the SI Brochure group long strings of digits in threes on both
sides of the decimal marker, and the standards this library reads print their
numbers that way. So the corpus writes ``6,251 5`` and ``101 325``, and it
should: a reader checking a value against a printed table wants to see it in
the same shape the page has it.

Written with an ordinary space, that grouping is a defect. A line break may
fall inside the number, leaving ``6,251`` at the end of one line and ``5`` at
the start of the next, which reads as two numbers. ISO 80000-1 says the
separator "shall be a space", and the typographic reading of that, the one the
SI Brochure follows, is a thin space that does not break.

This refuses the ordinary space and asks for U+202F, NARROW NO-BREAK SPACE. It
is in the font the figures are drawn with and in every web font the site loads,
and it survives the plain-Markdown twins and ``llms.txt`` unchanged.

**Where it does not apply.** Figure and diagram labels are exempt, and the
reason is that the defect cannot occur there: a label is drawn as a single line
of text in an SVG, and SVG text does not reflow. There is nothing for a break
to fall into. Inside ``$...$`` mathtext the right separator is ``\,`` rather
than any space character, which is a different rule for a different renderer.

In a Python file only the docstrings and the comments are read as prose. Every
other string may be data, and one of them is: the CNOSSOS traction table is
keyed by names like ``"diesel locomotive, c. 2 200 kW"``, which a caller passes
in. Putting an invisible character inside a key breaks the lookup on the spot,
and inside a published vocabulary it would break every caller. A first sweep
did exactly that, and the conformance run caught it.

Exit status 0 when every grouped decimal in the published prose holds together,
1 otherwise.
"""

from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from pathlib import Path

#: The repository, for paths a reader can click.
_REPO = Path(__file__).resolve().parent.parent

#: Everything whose text reflows when it is read: the guides and their plain
#: twins, the registries, the release notes, and the docstrings that become
#: reference pages. Figure generators are deliberately absent.
_ROOTS: tuple[str, ...] = (
    "docs",
    "site/src/content/docs",
    "src/phonometry",
    "scripts/conformance",
    "scripts/reports",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "README.md",
)

#: Generated from the sources above, so a finding there is a finding here that
#: has already been reported once.
_SKIP: tuple[str, ...] = ("llms", "node_modules", ".astro")

#: The separator the grouping is written with.
NARROW_NO_BREAK_SPACE = " "

#: The two shapes a line break can split. On the left of the marker, groups of
#: exactly three digits: ``101 325``. On its right, groups of three and a tail
#: of one to three: ``6,251 5``, ``0,647 829``.
#:
#: The closing conditions are what keep a number apart from two numbers. A
#: following digit or decimal marker means the space separated two values, as
#: the printed output of an array does (``0.404 0.512``); a following slash,
#: caret or letter means the digit belongs to a unit or an exponent, which is
#: how ``0,005 1/m`` reads. Both were in the tree, and a sweep that took them
#: for groupings would have published two corrupted numbers.
_GROUPED_DECIMAL = r"(?<![\d.,])\d+[.,]\d{3}(?:[ ]\d{3})*(?:[ ]\d{1,3})"
_GROUPED_INTEGER = r"(?<![\d.,])\d{1,3}(?:[ ]\d{3})+"
_BREAKABLE = re.compile(
    rf"(?:{_GROUPED_DECIMAL}|{_GROUPED_INTEGER})(?!\d)(?![.,]\d)(?![/^\w])"
)


#: A fenced block, and a span of inline code. Both show a literal, and a
#: literal is quoted as it is written: an array prints its values apart, and a
#: table keyed by ``"diesel locomotive, c. 2 200 kW"`` is keyed by that exact
#: string. Neither is prose, and neither reflows.
_FENCE = re.compile(r"^[ \t]*(```|~~~).*?^[ \t]*\1[ \t]*$", re.MULTILINE | re.DOTALL)
_SPAN = re.compile(r"`[^`\n]*`")


def _markdown_prose(text: str) -> list[tuple[int, str]]:
    """The lines of a Markdown file with the code blanked out, line numbers kept."""
    blanked = _FENCE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    return [
        (number, _SPAN.sub("", line))
        for number, line in enumerate(blanked.splitlines(), start=1)
    ]


def _prose_of(path: Path) -> list[tuple[int, str]]:
    """The lines of *path* that are read as prose, with their line numbers.

    Everything in Markdown. In Python, the docstrings and the comments, so that
    a string holding data keeps whatever spelling its key has.
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix != ".py":
        return _markdown_prose(text)
    prose: list[tuple[int, str]] = []
    tree = ast.parse(text, filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        doc = ast.get_docstring(node, clean=False)
        if doc is None:
            continue
        first = node.body[0].lineno
        prose.extend(
            (first + offset, line) for offset, line in enumerate(doc.splitlines())
        )
    prose.extend(
        (token.start[0], token.string)
        for token in tokenize.generate_tokens(io.StringIO(text).readline)
        if token.type == tokenize.COMMENT
    )
    return prose


def _findings(path: Path) -> list[tuple[int, str]]:
    """Every breakable grouped number in the prose of one file, with its line."""
    found: list[tuple[int, str]] = []
    for number, line in _prose_of(path):
        found.extend((number, match.group(0)) for match in _BREAKABLE.finditer(line))
    return sorted(found)


def _files() -> list[Path]:
    """Every text file of the published prose, in a stable order."""
    out: list[Path] = []
    for root in _ROOTS:
        base = _REPO / root
        candidates = [base] if base.is_file() else sorted(base.rglob("*"))
        out.extend(
            path
            for path in candidates
            if path.is_file()
            and path.suffix in {".md", ".mdx", ".py"}
            and not any(skip in str(path) for skip in _SKIP)
        )
    return out


def main() -> int:
    """Report every grouped decimal a line break could split in two."""
    bad = 0
    files = 0
    for path in _files():
        files += 1
        for line, number in _findings(path):
            bad += 1
            relative = path.relative_to(_REPO)
            print(f"{relative}:{line}: {number!r} is grouped with a breakable space")
    if bad:
        print()
        print(
            f"{bad} grouped decimal(s) could break across a line. Separate the "
            "groups with U+202F, the narrow no-break space, which is what the "
            "rest of the corpus uses."
        )
        return 1
    print(f"Every grouped decimal holds together: {files} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
