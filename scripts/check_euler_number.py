#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Gate for Euler's number set in italic.

ISO 80000-2:2019, Clause 4 (PDF page 7, folio 1), prints the mathematical
constants upright, "e.g. e = 2,718 281 828 ...", beside the upright exp, ln and
sin of a function that does not depend on the context, and Table 9, item
2-13.1, gives the e of the natural logarithm the same upright letter. An italic
*e* is a variable: the eccentricity of an ellipse, the error of an estimate.
Setting the constant italic says it is one of those.

KaTeX and matplotlib's mathtext both set a bare letter italic, so the constant
is upright only where the source asks for it, ``\mathrm{e}^{-t/\tau}``, and a
page that writes ``e^{-t/\tau}`` publishes the variable. The corpus had both:
about seventy italic and forty upright on the site alone, often a few lines
apart on one page.

What this reads: every ``$...$``, ``$$...$$``, ``:math:`...``` and
``.. math::`` region of the docstrings and of the three editions of the
guides, the errata register and the drawing modules included, and the source
of every text of every figure and plate under ``.github/images`` (matplotlib
keeps a figure's mathtext in an XML comment ahead of its glyphs, and the plate
canvas keeps the label it was handed). An ``e`` standing alone on the baseline,
outside any upright command and outside any script, with an exponent after it,
is the exponential, and it is reported unless it is upright. The ``e`` of a
subscript (:math:`T_\mathrm{e}`) is a different letter and is not read, and
neither is an ``e`` inside a word. The one subscript that is the constant
again is the base of the natural logarithm, which Table 9, item 2-13.5, prints
upright in :math:`\ln x = \log_\mathrm{e} x`; an italic ``\log_e`` is
reported.

A row break ``\\`` of a ``cases`` or ``aligned`` block is read as TeX, and so
is a formula that wraps onto the next line of its paragraph; a label in a plain
Python string, whose backslashes are doubled, is read with them undone (see
``tex_regions`` in ``check_subscript_slope.py``, which both gates share).

A plate is held to the same rule from its source: the canvas has no commands
and sets every lone letter of a ``$...$`` span italic, so a plate writes the
exponential as ``exp(...)``, the other form ISO 80000-2 gives it (Table 9, item
2-13.3), and an ``e^`` in a plate label is the italic letter.

Where an ``e`` with an exponent really is a variable, :data:`DECLARED` names
the file and says what the letter is.

Exit status 0 when no italic Euler e is found, 1 otherwise.
"""

from __future__ import annotations

import argparse
import html
import pathlib
import re
import sys

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from check_subscript_slope import (  # noqa: E402
    _UPRIGHT_WRAPPERS,
    tex_regions,
)

#: Where the prose lives: the docstrings that become the API reference, and the
#: three editions of the guides, the errata register among them.
DEFAULT_ROOTS = ("src/phonometry", "docs", "site/src/content/docs")

#: Where the figures and the plates are written.
IMAGES = ".github/images"

_SUFFIXES = {".py", ".md", ".mdx"}

#: Files whose ``e`` with an exponent is a variable, with what it is. Keyed on
#: the repository-relative path, matched against the tail of the file's own.
DECLARED: dict[str, str] = {}

#: One text a figure draws, or one label a plate draws: both keep the source
#: string in an XML comment.
_IMAGE_TEXT = re.compile(r"<!-- (.*?) -->", re.DOTALL)


def _script_end(region: str, caret: int) -> int:
    """The index just past the script that the ``^`` or ``_`` at *caret* opens."""
    k = caret + 1
    while k < len(region) and region[k] == " ":
        k += 1
    if k >= len(region):
        return k
    if region[k] == "{":
        depth = 0
        for index in range(k, len(region)):
            if region[index] == "{":
                depth += 1
            elif region[index] == "}":
                depth -= 1
                if depth == 0:
                    return index + 1
        return len(region)
    if region[k] == "\\":
        j = k + 1
        while j < len(region) and region[j].isalpha():
            j += 1
        return max(j, k + 2)
    return k + 1


def _is_exponential(region: str, caret: int) -> bool:
    r"""Whether the ``e`` before the ``^`` at *caret* is the constant.

    The constant never carries a subscript, so an ``e`` whose exponent is
    followed by one is a tensor or an indexed variable: the strain
    :math:`e^s_{ij}` of the frame of a Biot medium.
    """
    k = _script_end(region, caret)
    while k < len(region) and region[k] == " ":
        k += 1
    return not (k < len(region) and region[k] == "_")


def italic_exponential_spans(region: str) -> list[tuple[int, int]]:
    r"""``(start, end)`` of each italic Euler e *region* writes, read as TeX.

    A small reading, enough to tell where an ``e`` stands: a group opened by
    ``_`` or ``^`` is a script, and so is everything in it; a group opened by
    an upright command is upright. A lone ``e`` on the baseline, neither in a
    script nor upright, whose next character is ``^``, is the exponential;
    so is a group holding nothing but ``e`` (``{e}^{x}``). The span covers the
    letter, or the group, that would be replaced by ``\mathrm{e}``.
    """
    spans: list[tuple[int, int]] = []
    stack: list[tuple[bool, bool]] = [(False, False)]
    pending_script = False
    pending_upright = False
    i = 0
    n = len(region)
    while i < n:
        ch = region[i]
        script, upright = stack[-1]
        if ch == "\\":
            j = i + 1
            while j < n and region[j].isalpha():
                j += 1
            name = region[i + 1 : j] or region[i + 1 : i + 2]
            j = max(j, i + 2)
            if name in _UPRIGHT_WRAPPERS:
                if name == "rm":
                    stack[-1] = (script, True)
                else:
                    pending_upright = True
            elif pending_script:
                k = j
                while k < n and region[k] == " ":
                    k += 1
                if k >= n or region[k] != "{":
                    pending_script = False
            i = j
            continue
        if ch == "{":
            if (
                region[i + 1 : i + 3] == "e}"
                and region[i + 3 : i + 4] == "^"
                and not (script or pending_script or upright or pending_upright)
                and _is_exponential(region, i + 3)
            ):
                spans.append((i, i + 3))
            stack.append((script or pending_script, upright or pending_upright))
            pending_script = pending_upright = False
        elif ch == "}":
            if len(stack) > 1:
                stack.pop()
        elif ch in "_^":
            pending_script = True
        elif ch.isascii() and ch.isalpha():
            if pending_script:
                pending_script = False
                i += 1
                continue
            j = i
            while j < n and region[j].isascii() and region[j].isalpha():
                j += 1
            if region[i:j] == "e" and not (script or upright):
                k = j
                while k < n and region[k] == " ":
                    k += 1
                if k < n and region[k] == "^" and _is_exponential(region, k):
                    spans.append((i, j))
            i = j
            continue
        elif not ch.isspace():
            pending_script = False
        i += 1
    return spans


#: The base of a logarithm written as an italic e, ``\log_e`` or ``\log_{e}``.
#: ISO 80000-2:2019, Table 9, item 2-13.5 (PDF page 21, folio 15), prints
#: :math:`\ln x = \log_\mathrm{e} x` with the constant upright.
_ITALIC_LOG_BASE = re.compile(r"\\log_(?:\{\s*e\s*\}|e(?![A-Za-z]))")


def italic_log_base_spans(region: str) -> list[tuple[int, int]]:
    r"""``(start, end)`` of each ``\log_e`` *region* writes with an italic e."""
    return [match.span() for match in _ITALIC_LOG_BASE.finditer(region)]


def file_findings(text: str, suffix: str) -> list[int]:
    """The lines of *text* that write an italic Euler e, once per occurrence."""
    lines: list[int] = []
    for offset, region in tex_regions(text, suffix):
        first = text.count("\n", 0, offset) + 1
        spans = italic_exponential_spans(region) + italic_log_base_spans(region)
        lines.extend(first + region.count("\n", 0, start) for start, _ in sorted(spans))
    return lines


def image_findings(svg: str) -> list[str]:
    """The texts of one figure or plate that write an italic Euler e."""
    found: list[str] = []
    for match in _IMAGE_TEXT.finditer(svg):
        source = html.unescape(match.group(1))
        if "$" not in source or "e" not in source:
            continue
        if file_findings(source, ".md"):
            found.append(source)
    return found


def collect(roots: list[str]) -> list[pathlib.Path]:
    """The prose files to read, in a stable order."""
    paths: list[pathlib.Path] = []
    for root in roots:
        target = pathlib.Path(root)
        if target.is_file():
            paths.append(target)
            continue
        paths.extend(
            p
            for p in sorted(target.rglob("*"))
            if p.suffix in _SUFFIXES and p.is_file()
        )
    return paths


def declared(path: pathlib.Path) -> str | None:
    """Why *path* may write a variable e with an exponent, if it is declared."""
    posix = path.as_posix()
    for key, reason in DECLARED.items():
        if posix == key or posix.endswith("/" + key):
            return reason
    return None


def check(
    paths: list[pathlib.Path], images: pathlib.Path | None = None
) -> tuple[int, list[str]]:
    """``(files read, one report per file or image with an italic Euler e)``."""
    failures: list[str] = []
    for path in paths:
        if declared(path) is not None:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        lines = file_findings(text, path.suffix)
        if lines:
            where = ", ".join(str(n) for n in sorted(set(lines)))
            failures.append(f"  {path}: on line {where}")
    read = len(paths)
    if images is not None:
        for svg in sorted(images.glob("*.svg")):
            try:
                text = svg.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            read += 1
            failures.extend(
                f"  {svg.name}: {label!r}" for label in image_findings(text)
            )
    return read, failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "roots",
        nargs="*",
        default=list(DEFAULT_ROOTS),
        help="files or directories to scan (default: the prose)",
    )
    parser.add_argument(
        "--images",
        default=IMAGES,
        help=f"directory the figures and plates are read from (default: {IMAGES})",
    )
    args = parser.parse_args(argv)

    images = pathlib.Path(args.images)
    if not any(images.glob("*.svg")):
        # Read from the wrong directory, no image would be read and the gate
        # would pass having looked at none of them.
        print(f"No images in {images}: run from the repository root.", file=sys.stderr)
        return 1
    read, failures = check(collect(args.roots), images)
    if not failures:
        print(f"Euler's number is upright in all {read} files and images read.")
        return 0
    print(
        f"{len(failures)} files or image texts set Euler's number in italic:\n",
        file=sys.stderr,
    )
    for failure in failures:
        print(failure, file=sys.stderr)
    print(
        "\nWrite the constant \\mathrm{e}^{...} (ISO 80000-2:2019, Clause 4); a "
        "plate writes\nexp(...). Where the letter is a variable, declare the "
        "file in DECLARED and\nsay what it is.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
