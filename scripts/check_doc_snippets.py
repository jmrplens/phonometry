#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Gate for the Python snippets printed in the documentation.

The guides teach by example, and an example that does not run teaches the
wrong thing. Four checks, cheapest first:

1. **Shadowing.** A name imported from ``phonometry`` must not be rebound
   later in the same block, by an assignment or by another import. This is
   the failure the package split walked into: ``from scipy import signal``
   next to ``from phonometry import signal`` rebinds the name silently, and
   the snippet crashes several lines further down with an ``AttributeError``
   that points nowhere near the import. Python gives no warning for it and
   the interpreter is the only thing that notices.

2. **Same API in both languages.** A Spanish page is free to translate its
   comments and its plot labels and to ask for a Spanish figure
   (``plot(language="es")``), but it must teach the same API: the imports it
   takes from ``phonometry`` have to match its English twin exactly, name for
   name. Comparing whole token streams was tried first and is wrong: it fails
   on the ``language="es"`` argument, which is the one difference the pages
   are supposed to have. The ``docs/`` mirror is not paired with anything: it
   is written by hand for GitHub and does not carry the same set of examples,
   so it is not held to the imports of a twin.

3. **Execution.** Every page's blocks, in English, in Spanish and in the
   ``docs/`` mirror, plus those of the README, of ``llms.txt`` and of the
   site's home page, are concatenated in reading order (a guide is a
   narrative: later blocks use the variables the earlier ones bound) and run
   in a subprocess. A page that reads a file the reader brings runs on one
   :data:`_FIXTURES` writes first. Pages that cannot run standalone are
   listed in :data:`_SKIP` with a reason, and the list is checked for
   staleness: a page that starts passing must leave it. A block that passes
   ``...`` to a call is a sketch of a call rather than a computation, so it is
   read but not run.

4. **Output.** The guides teach through the value a print writes, given in a
   comment at the end of the print's line or on the comment line under it:
   ``print(round(bulk, 1))  # 5958.0 MPa``. Running a page proves only that it
   finishes, so a change to a solver, a catalogue row or a rounding that moved
   a printed value left the old value in the comment with every check green.
   Each page runs with ``print`` wrapped to record what every print of the
   page's own code writes, keyed by its line and by where on it the call
   stands, and every comment that opens like a value
   (:data:`_OUTPUT_OPENING`) once a symbol, an ``e.g.`` or an aligning ``#``
   before it is read past (:func:`_reading`), or opens on the word the print
   writes first, is held to that text (:func:`output_disagreement`): the
   values first, in their order, each at the decimals the comment writes it
   to, with units, labels and annotation read past, and none of them left
   out at the end. A comment whose print never runs is a failure too. There
   is no list of excused comments: one the check misreads is taught to it,
   and one that is wrong is corrected on the page.

Usage::

    python scripts/check_doc_snippets.py            # all four checks
    python scripts/check_doc_snippets.py --static   # skip the execution and output passes

Exit status 0 when everything passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import io
import json
import locale
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import tokenize
from dataclasses import dataclass
from decimal import (
    MAX_EMAX,
    MIN_EMIN,
    Context,
    Decimal,
    DecimalException,
    Inexact,
    InvalidOperation,
)
from typing import TYPE_CHECKING, NamedTuple, TypeGuard

import ast_scan
from markdown_fences import fences, page_kind

if TYPE_CHECKING:
    from collections.abc import Sequence

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DOCS = _ROOT / "docs"
_SITE = _ROOT / "site" / "src" / "content" / "docs"
_SITE_ES = _SITE / "es"

#: Pages whose snippets cannot run as a standalone script, with the reason.
#: Anything not listed here must run to completion. Keep the reasons specific:
#: "needs a file the repository does not ship" is a fact, "example" is not.
_SKIP: dict[str, str] = {
    # The page reads something the repository does not ship.
    "block-processing": "streams through soundfile, an optional dependency",
    # The page shows excerpts of a workflow rather than a script: a block
    # starts from a variable the prose introduced, or a later block rebinds
    # one an earlier block still relies on. Reading order and running order
    # are not the same thing on these pages, and that is the author's call.
    "aircraft-noise": "excerpt: starts from the spl of the prose",
    "detailed-prediction": "excerpt: starts from the measured spectra of the prose",
    "electroacoustics": "excerpt: starts from the captured signal of the prose",
    "panel-sound-insulation": "excerpt: two scenarios share a variable name",
    "room-to-room": "excerpt: two scenarios share the band vector name",
    "rotorcraft-noise": "excerpt: starts from the measured spectrum",
    "spectral-analysis": "excerpt: starts from the record of the prose",
    "synchronous-averaging": "excerpt: a later block shortens the record an "
    "earlier one averages",
    "time-weighting": "excerpt: starts from the block stream of the prose",
}

#: Files a page reads that the reader brings, written by code run in the
#: page's directory before its first block, so the page runs on a file of the
#: kind its prose describes instead of being skipped. The code is the
#: harness's, not the page's: no reader sees it, and its names start with an
#: underscore and are deleted, so no block can lean on them.
_FIXTURES: dict[str, str] = {
    # The two WAVs of one measurement chain, float as a meter writes them: 3 s
    # of the calibrator's 1 kHz tone, then a second of a 100 Hz and a 1 kHz
    # tone, both well below full scale.
    "getting-started": (
        "import numpy as _np\n"
        "from scipy.io import wavfile as _wavfile\n"
        "_fs = 48000\n"
        "_t = _np.arange(3 * _fs) / _fs\n"
        "_tone = 0.25 * _np.sin(2 * _np.pi * 1000 * _t)\n"
        "_wavfile.write('calibrator.wav', _fs, _tone.astype(_np.float32))\n"
        "_t = _np.arange(_fs) / _fs\n"
        "_tones = _np.sin(2 * _np.pi * 100 * _t) + _np.sin(2 * _np.pi * 1000 * _t)\n"
        "_wavfile.write('measurement.wav', _fs, (0.1 * _tones).astype(_np.float32))\n"
        "del _np, _wavfile, _fs, _t, _tone, _tones\n"
    ),
}

#: Timeout per page, generous enough for the FDTD and ECMA pages.
_TIMEOUT_S = 600

#: The encoding a page's stdout and stderr are read in. A page runs on this
#: interpreter, in this environment, so its streams take the encoding this
#: process would give its own, the one :mod:`subprocess` reads text in when
#: it is given none. A page, or a library it calls, can still write raw bytes
#: that do not decode in it, and each such byte is read as a replacement
#: character, so the report of that page is made all the same.
_STREAM_ENCODING = "utf-8" if sys.flags.utf8_mode else locale.getencoding()


#: The site's home page, which prints its examples from a data module rather
#: than from Markdown: each is a template literal bound to a ``*_CODE``
#: constant. It is the first code a visitor reads.
_HOME = _ROOT / "site" / "src" / "data" / "home.ts"

#: ``const NAME_CODE = `...`;``, the literal captured whole.
_TEMPLATE_CODE = re.compile(r"^const \w+_CODE = `(.*?)`;$", re.DOTALL | re.MULTILINE)


def _template_literal(raw: str) -> str:
    """The text a JavaScript template literal holds, with no substitution.

    A ``${`` would splice JavaScript into the example, which no snippet
    does, so it is refused rather than guessed at.
    """
    if "${" in raw.replace("\\${", ""):
        msg = "a home-page example interpolates ${...}; write it out in full"
        raise ValueError(msg)
    return re.sub(r"\\([`$\\])", r"\1", raw)


def _located_blocks(path: pathlib.Path) -> list[tuple[int, str]]:
    """Python blocks of a page, in reading order, each with the line of the
    page its first line stands on, counted from 1.
    """
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".ts":
        return [
            (text.count("\n", 0, m.start(1)) + 1, _template_literal(m.group(1)))
            for m in _TEMPLATE_CODE.finditer(text)
        ]
    return [
        (fence.line + 1, fence.body)
        for fence in fences(text, kind=page_kind(path.name))
        if fence.language == "python"
    ]


def _blocks(path: pathlib.Path) -> list[str]:
    """Python blocks of a page, in reading order."""
    return [body for _, body in _located_blocks(path)]


def _imported_names(code: str) -> list[str]:
    """Every name a block takes from phonometry, as ``module.name``."""
    out: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "phonometry"
        ):
            out += [f"{node.module}.{alias.name}" for alias in node.names]
        elif isinstance(node, ast.Import):
            out += [a.name for a in node.names if a.name.startswith("phonometry")]
    return out


def _phonometry_imports(tree: ast.AST) -> dict[str, int]:
    """Names bound by an import from phonometry, mapped to their line."""
    bound: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
            "phonometry"
        ):
            for alias in node.names:
                bound[alias.asname or alias.name] = node.lineno
    return bound


def _rebindings(tree: ast.AST, names: dict[str, int]) -> list[str]:
    """Reports for every name from ``names`` rebound after its import."""
    reports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and not (node.module or "").startswith(
            "phonometry"
        ):
            for alias in node.names:
                name = alias.asname or alias.name
                if name in names:
                    reports.append(
                        f"line {node.lineno}: 'from {node.module} import {name}' "
                        f"rebinds the name imported from phonometry on line "
                        f"{names[name]}"
                    )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                if name in names:
                    reports.append(
                        f"line {node.lineno}: 'import {alias.name}' rebinds the "
                        f"name imported from phonometry on line {names[name]}"
                    )
        elif isinstance(node, ast.Assign):
            reports += [
                f"line {node.lineno}: '{target.id} = ...' rebinds the name "
                f"imported from phonometry on line {names[target.id]}"
                for target in node.targets
                if isinstance(target, ast.Name) and target.id in names
            ]
    return reports


def check_shadowing(pages: list[pathlib.Path], *, carry: bool = True) -> list[str]:
    """Failures for every page that rebinds a name it imported.

    A page is read top to bottom, so the imports of an earlier block are still
    in scope in a later one: the check carries them forward instead of looking
    at each block alone. ``carry=False`` is for the generated dumps, which glue
    unrelated pages into one file: there the blocks share no scope, and
    carrying an import across them invents collisions that no reader can hit.
    """
    failures: list[str] = []
    for page in pages:
        carried: dict[str, int] = {}
        for i, block in enumerate(_blocks(page)):
            try:
                tree = ast.parse(block)
            except SyntaxError as exc:
                failures.append(f"{_rel(page)} block {i}: does not parse ({exc})")
                continue
            imported = _phonometry_imports(tree)
            seen = {**carried, **imported}
            if seen:
                failures += [
                    f"{_rel(page)} block {i}: {report}"
                    for report in _rebindings(tree, seen)
                ]
            # A block that rebinds a carried name owns it from here on.
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            carried.pop(target.id, None)
            if carry:
                carried.update(imported)
            else:
                carried = {}
    return failures


def check_translations(pairs: list[tuple[pathlib.Path, pathlib.Path]]) -> list[str]:
    """Failures for every pair that does not teach the same API."""
    failures: list[str] = []
    for left, right in pairs:
        want = sorted(n for b in _blocks(left) for n in _imported_names(b))
        got = sorted(n for b in _blocks(right) for n in _imported_names(b))
        if want == got:
            continue
        missing = sorted(set(want) - set(got))
        extra = sorted(set(got) - set(want))
        detail = []
        if missing:
            detail.append("missing " + ", ".join(missing))
        if extra:
            detail.append("has " + ", ".join(extra) + " which its twin does not")
        if not detail:  # same names, different multiplicity
            detail.append("imports the same names a different number of times")
        failures.append(f"{_rel(right)}: {'; '.join(detail)} against {_rel(left)}")
    return failures


def _is_sketch(code: str) -> bool:
    """True for a block that calls something with ``...`` in the arguments.

    ``building.airborne_insulation(...)`` shows the shape of a call, not a
    computation, and the README leads with one. A keyword placeholder
    (``f(level=...)``) is the same thing said differently. Such a block parses, so the
    static checks still see it; running it would only assert that Ellipsis is
    not a sound pressure level.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False

    def placeholder(node: ast.Call) -> bool:
        args = [*node.args, *(kw.value for kw in node.keywords)]
        return any(isinstance(a, ast.Constant) and a.value is Ellipsis for a in args)

    return any(isinstance(n, ast.Call) and placeholder(n) for n in ast.walk(tree))


#: How a comment that states an output opens, once what leads it is read past
#: (:func:`_reading`): past the reference of a formula a print writes before
#: its values (``(A.4) -0.638``), a ``~`` that gives a value roughly and the
#: brackets of a printed container, with a number (a digit, or a sign or a
#: decimal point before one), a constant Python prints by its name, an
#: ellipsis, the quote of a printed string or an empty container. A comment
#: that opens on a word, or on a bracket around words (``(n_samples,)``,
#: ``(Formula C.4)``), describes the line; it does not state what the line
#: prints.
_OUTPUT_OPENING = re.compile(
    r"(?:\([A-Z]\.\d+(?:\.\d+)*\)\s*)?"
    r"[~\u2248]?[\s(\[{]*"
    r"(?:[-+\u2212]?\.?\d|(?:True|False|None|nan|-?inf)\b|\.\.\.|\u2026|['\"]"
    r"|\(\)|\[\]|\{\})"
)

#: A number as a comment writes one in the arithmetic that leads to a value.
_FIGURE = r"[-+\u2212]?(?:\d+(?:\.\d*)?|\.\d+)"

#: What leads the output in a comment and is read past: the second ``#`` of a
#: comment aligned under another (``#            # [ 6.57 23.28] dB``), an
#: ``e.g.``, or ``p. ej.`` on a Spanish page, that offers the value as an
#: example, and the symbol a comment names the value by (``LWA = 89.7 dB``),
#: with any arithmetic that leads from it to the value (``Ld = 12 - 10 =
#: 2.0 dB``), so that the value read is the one after the last ``=``; before
#: a ``≈`` only the symbol, the ``≈`` giving the value roughly.
_LEAD = re.compile(
    r"(?:#\s*)+"
    r"|(?:e\.\s?g\.|p\.\s?ej\.)[\s,:]*"
    r"|[^\W\d][^\s=(){}\[\]\u2248]*\s*=(?!=)"
    rf"(?:\s*{_FIGURE}(?:\s*[-+*/\u2212\u00d7]\s*{_FIGURE})+\s*=(?!=))*\s*"
    r"|[^\W\d][^\s=(){}\[\]\u2248]*\s*(?=\u2248)"
)


def _reading(text: str) -> str:
    """*text*, a comment, from where the output it states begins (:data:`_LEAD`)."""
    while (lead := _LEAD.match(text)) is not None and lead.end():
        text = text[lead.end() :]
    return text


#: A real number as Python and NumPy print one: ``2``, ``-1.``, ``.5``, ``2e-05``.
#: A point before an ellipsis is the ellipsis's, not the number's.
_REAL = r"(?:\d+(?:\.(?!\.\.)\d*)?|\.\d+)(?:[eE][-+]?\d+)?"

#: What a sign that follows it joins to what comes after, as the hyphen of a
#: range (``50-80 Hz``) or of a name (``NC-35``) does: a digit, a letter, an
#: underscore, a point or a closing bracket. Such a sign is no value's, in a
#: comment and in what a print wrote alike, whoever wrote it.
_JOINS = r"[\w.)\]}]"

#: The sign of a value: one that does not follow what :data:`_JOINS` names.
_SIGN = rf"(?:(?<!{_JOINS})[-+])?"

#: The parts of an output, as :func:`output_disagreement` reads them: a value
#: (a complex number, a real one, or a constant printed by its name), a word,
#: and an ellipsis, which stands for values left out. A ``~`` before a value
#: gives it roughly, and an ellipsis right after its digits says they go on.
#: Punctuation and spaces are not parts: a container prints them its own way
#: and a comment lays them out its own, so a complex number may carry spaces
#: before and after the sign of its imaginary part, as NumPy pads one to the
#: width of the others in an array (``[ 1.  +1.j  1.25-2.j]``). A sign is a
#: value's only where :data:`_SIGN` says it is.
_OUTPUT_PART = re.compile(
    r"(?P<rough>[~\u2248]\s*)?"
    rf"(?P<value>{_SIGN}{_REAL} *[-+] *{_REAL}j|{_SIGN}{_REAL}j?"
    r"|(?<![\w.])(?:True|False|None|nan|-?inf)(?![\w.]))"
    r"(?P<cut>\.\.\.|\u2026)?"
    r"|(?P<word>[^\W\d]\w*)"
    r"|(?P<gap>\.\.\.|\u2026)"
)

#: What a comment writes beside its values that only looks like one: the power
#: of a unit (``m/s^2``, ``m/s^1.5``) and the index of a symbol (``A(8)``).
_NOT_A_VALUE = re.compile(r"\^[-+]?\d+(?:\.\d+)?|(?<=[A-Za-z])\(\d+\)")


@dataclass(frozen=True)
class _Part:
    """One part of an output or of a comment.

    :param kind: ``"value"``, ``"word"``, ``"gap"`` (an ellipsis) or, in an
        output, ``"line"``, the end of a line it writes.
    :param text: The part as written.
    :param label: True for a part of an output that the print's own string
        literal writes: a label around the values, which a comment need not
        repeat.
    :param rough: True for a value a comment gives roughly, after a ``~``.
    :param cut: True for a value a comment cuts short, its digits followed by
        an ellipsis.
    :param before: What the text writes between the part before and this
        one: the spaces, the punctuation and the brackets.
    :param segment: For a part of an output, which stretch of it the part
        stands in: the output is read in stretches of what the page's own
        text wrote and of what its code computed, one after another, and a
        computed value written apart from another by a stretch of the page's
        text is in a stretch of its own.
    """

    kind: str
    text: str
    label: bool = False
    rough: bool = False
    cut: bool = False
    before: str = ""
    segment: int = 0


#: What one argument of a print is: ``None`` for a value the code computes, or
#: the pieces of a string the page writes, each literal text or ``None`` for a
#: value an f-string formats into it.
_Argument = tuple[str | None, ...] | None

#: Where a call stands in a script: the line it opens on, the line it closes
#: on, and the columns it opens and closes at, in the order the interpreter
#: gives them for the instruction that makes the call
#: (:meth:`~types.CodeType.co_positions`), which places it where
#: :func:`ast.parse` places the call. Two calls that open on one line, one
#: inside the other's arguments, are told apart by it. The interpreter gives
#: ``None`` for a column it was asked not to keep.
_Place = tuple[int | None, int | None, int | None, int | None]


def _place(call: ast.Call) -> _Place:
    """Where *call* stands in its script (:data:`_Place`)."""
    return (call.lineno, call.end_lineno, call.col_offset, call.end_col_offset)


@dataclass(frozen=True)
class _Promise:
    """The output a comment promises for one print of a page's script.

    :param first: The line of the script the statement the print stands in
        opens on, or the print's own first line where the comment is its own
        (:func:`promised_outputs`) or in the header of a compound statement
        (:func:`_print_calls`).
    :param last: The line that statement, or that print, closes on.
    :param lines: The comment and the comment lines that continue it.
    :param prints: The prints that open on the lines from *first* to *last*
        whose calls the comment stands for, each where it stands
        (:data:`_Place`) with what each of its arguments is
        (:data:`_Argument`), or ``None`` when they cannot be told apart
        (``*args``): a call is read with the arguments of the print that
        made it.
    :param word: For a comment that opens on a word, the word: such a comment
        states the output only when the print writes that word first, which
        the run tells (:func:`output_disagreements`); ``None`` for a comment
        that opens like an output whatever the print writes.
    :param apart: Where the prints stand that open on those lines and whose
        calls the comment does not stand for: one with a comment of its own on
        fewer lines inside them, with the prints inside its arguments that
        comment holds, and one that runs on past *last*, the print whose
        arguments hold this one.
    :param builtin: Whether the print reads the builtin ``print``: a name
        the script binds to something else (``from rich import print``, or
        any name a ``from rich import *`` may bind) need
        not reach the recorder, so a run that records none of its calls does
        not show that the page never runs it.
    """

    first: int
    last: int
    lines: tuple[str, ...]
    prints: tuple[tuple[_Place, tuple[_Argument, ...] | None], ...] = ()
    word: str | None = None
    apart: tuple[_Place, ...] = ()
    builtin: bool = True

    @property
    def text(self) -> str:
        """The comment, its continuation lines joined to it."""
        return " ".join(self.lines)


def _is_print(node: ast.AST) -> TypeGuard[ast.Call]:
    """True for a call of ``print`` by that name, a statement of its own or
    inside another one (``result = print(2)``, ``[print(x) for x in xs]``):
    the record holds what every call writes, wherever it stands. Whether the
    name is the builtin's there is :func:`_reads_builtin`'s to tell.
    """
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    )


def _imports_every_name(tree: ast.Module) -> bool:
    """Whether *tree* imports every public name of a module
    (``from rich import *``), which binds whatever that module lists,
    ``print`` among them for one that lists it: Python takes such an import
    at the top level of a module only, in any block there.
    """
    return any(
        isinstance(node, ast.ImportFrom)
        and any(alias.name == "*" for alias in node.names)
        for node in ast.walk(tree)
    )


def _binds_print(tree: ast.Module) -> bool:
    """Whether any scope of *tree*, the module, a function, a lambda, a class
    body or a comprehension, binds the name ``print``, as its own or under
    ``global``: when none does, and the module imports no module's every
    name (:func:`_imports_every_name`), every call of the name reads the
    builtin, and none is looked up (:func:`_reads_builtin`).
    """
    scopes = [
        tree,
        *(node for node in ast.walk(tree) if isinstance(node, ast_scan.SCOPES)),
    ]
    return any(
        ast_scan.own_names(scope).binds("print")
        or ast_scan.own_names(scope).rebinds("print")
        for scope in scopes
    )


def _reads_builtin(tree: ast.Module, call: ast.Call) -> bool:
    """Whether the name *call* calls is the builtin ``print``: no scope it is
    looked up in binds it (:func:`ast_scan.binding_of`), neither the module
    nor a function that declares it ``global`` and binds it there.
    """
    how, _ = ast_scan.binding_of(tree, call.func, "print")
    return (
        how in {"outside", "global"}
        and not ast_scan.own_names(tree).binds("print")
        and "print" not in ast_scan.global_bindings(tree)
    )


def _prints_around(tree: ast.AST) -> dict[ast.Call, ast.Call]:
    """Each print of *tree* inside the arguments of another, at any depth,
    with the innermost print around it: the calls a print's arguments make
    before it writes, which its comment stands for unless one has a comment
    of its own.
    """
    around: dict[ast.Call, ast.Call] = {}

    def visit(node: ast.AST, outer: ast.Call | None) -> None:
        for child in ast.iter_child_nodes(node):
            if _is_print(child):
                if outer is not None:
                    around[child] = outer
                visit(child, child)
            else:
                visit(child, outer)

    visit(tree, None)
    return around


#: The first and the last line of a stretch of a script.
_Span = tuple[int, int]


def _print_calls(tree: ast.AST) -> dict[ast.Call, tuple[_Span, _Span]]:
    """Every call of ``print`` in *tree*, with its own lines and the lines of
    the statement it stands in, whose last line is where a reader writes the
    comment of a list comprehension of prints over three lines; in the header
    of a compound statement, the call's own lines twice. Two calls in one
    statement stand for its lines alike, as two prints written on one line
    with a semicolon between them do.
    """
    found: dict[ast.Call, tuple[_Span, _Span]] = {}

    def visit(node: ast.AST, span: _Span | None) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt):
                simple = not hasattr(child, "body") and not hasattr(child, "cases")
                lines = (child.lineno, child.end_lineno or child.lineno)
                visit(child, lines if simple else None)
                continue
            if _is_print(child):
                own = (child.lineno, child.end_lineno or child.lineno)
                found[child] = (own, span or own)
            visit(child, span)

    visit(tree, None)
    return found


def _open_brackets(text: str) -> int:
    """How many brackets *text* opens and leaves open."""
    return sum(text.count(c) for c in "([{") - sum(text.count(c) for c in ")]}")


def _arguments(call: ast.Call) -> tuple[_Argument, ...] | None:
    """What each argument of *call* is, as :data:`_Argument` says."""
    if any(isinstance(arg, ast.Starred) for arg in call.args):
        return None
    out: list[_Argument] = []
    for arg in call.args:
        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
            out.append((arg.value,))
        elif isinstance(arg, ast.JoinedStr):
            out.append(
                tuple(
                    piece.value
                    if isinstance(piece, ast.Constant) and isinstance(piece.value, str)
                    else None
                    for piece in arg.values
                )
            )
        else:
            out.append(None)
    return tuple(out)


def _label_word(call: ast.Call) -> str | None:
    """The first word the string literal a print opens with writes, if any."""
    if not call.args:
        return None
    first = call.args[0]
    if isinstance(first, ast.JoinedStr) and first.values:
        first = first.values[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        match = re.match(r"\s*([^\W\d]\w*)", first.value)
        return match.group(1) if match else None
    return None


def _opens_output(text: str, call: ast.Call) -> bool:
    """True for a comment that opens like the output of *call*: like a value
    (:data:`_OUTPUT_OPENING`) once what leads it is read past (:func:`_reading`),
    or on the word the print's own label opens with.
    """
    if _OUTPUT_OPENING.match(_reading(text)):
        return True
    word = _label_word(call)
    return word is not None and re.match(rf"{re.escape(word)}\b", text) is not None


def _opening_word(text: str) -> str | None:
    """The word a comment opens on, once what leads it is read past."""
    match = re.match(r"[^\W\d]\w*", _reading(text))
    return match.group() if match else None


def promised_outputs(script: str) -> list[_Promise]:
    """The output each print of *script* promises in a comment.

    A print promises an output when the comment at the end of its last line,
    or else the comment line right under it, opens like that output
    (:func:`_opens_output`), or opens on a word, which the run then has to
    show the print writes first (:attr:`_Promise.word`): the name of a class
    or a rating, a message. The comment goes on over the comment lines under
    it that open like an output too, one for each line a print in a loop
    writes, and over any that a bracket it leaves open carries on to, as a
    printed container goes on over lines. Prints that follow one another line
    after line with no comment of their own share out the comment lines under
    the last of them, one line each, when each of those lines opens like the
    output of its print or on a word.

    A print inside a statement that runs on past it is read first on its own
    lines, where a comment that opens like its output is its own; a word
    there is more likely a note on an argument than a message the print
    writes, and is not read. The prints that have no comment there are read
    on the lines of their statement, and that comment stands for their calls
    only, not for those of the prints that have one of their own. A comment
    on a print's own lines stands for the calls of that print and of the
    prints inside its arguments, at any depth, that have none of their own,
    not for those of the print whose arguments hold it, which opens on its
    line: the run tells the calls apart by where each stands
    (:data:`_Place`), not by the line alone. A print inside another that
    closes on the line the outer one closes on shares its comment, which
    stands for the calls of both, and a print a comment on the lines of a
    print around it holds is not read again on the lines of its statement.
    """
    tree = ast.parse(script)
    try:
        return _promises(script, tree)
    finally:
        # The scopes read for each print are kept by the tree they came from;
        # a page's tree is read once, so nothing of it is kept for the next.
        ast_scan.forget_trees()


def _promises(script: str, tree: ast.Module) -> list[_Promise]:
    """:func:`promised_outputs`, of *script* parsed as *tree*."""
    lines = script.splitlines()
    comments: dict[int, tuple[int, str]] = {}
    for token in tokenize.generate_tokens(io.StringIO(script).readline):
        if token.type == tokenize.COMMENT:
            comments[token.start[0]] = (token.start[1], token.string[1:].strip())

    def comment_only(number: int) -> bool:
        return (
            number in comments and not lines[number - 1][: comments[number][0]].strip()
        )

    def trailing(number: int) -> str | None:
        """The comment at the end of line *number*, after code."""
        return (
            None
            if number not in comments or comment_only(number)
            else comments[number][1]
        )

    def run_from(number: int, said: list[str], call: ast.Call) -> list[str]:
        """*said* and the comment lines from *number* down that go on with it.

        The brackets *said* leaves open are counted on as each line joins it,
        not counted again over all of it for each line.
        """
        said = list(said)
        depth = sum(_open_brackets(text) for text in said)
        while comment_only(number):
            text = comments[number][1]
            if not (depth > 0 or _opens_output(text, call)):
                break
            said.append(text)
            depth += _open_brackets(text)
            number += 1
        return said

    found = _print_calls(tree)
    span: dict[ast.Call, _Span] = {}
    said_by: dict[ast.Call, list[str]] = {}
    word_by: dict[ast.Call, str] = {}

    def read(calls: list[ast.Call], *, words: bool) -> None:
        """Find the comment of each of *calls* at the lines :data:`span`
        gives it, a comment that opens on a word too when *words* is true.
        """
        prints = sorted(
            calls, key=lambda node: (span[node][0], node.lineno, node.col_offset)
        )

        def start(index: int) -> int:
            return span[prints[index]][0]

        def end(index: int) -> int:
            return span[prints[index]][1]

        def opening(text: str, index: int) -> bool:
            """Whether *text* opens like the output of the print at *index*,
            or on a word, noted for the run to settle.
            """
            if _opens_output(text, prints[index]):
                return True
            word = _opening_word(text) if words else None
            if word is not None:
                word_by[prints[index]] = word
            return word is not None

        at = 0
        while at < len(prints):
            node = prints[at]
            comment = trailing(end(at))
            if comment is not None:
                if opening(comment, at):
                    said_by[node] = run_from(end(at) + 1, [comment], node)
                at += 1
                continue
            stack = [at]
            while (
                stack[-1] + 1 < len(prints)
                and start(stack[-1] + 1) == end(stack[-1]) + 1
                and trailing(end(stack[-1] + 1)) is None
            ):
                stack.append(stack[-1] + 1)
            under = end(stack[-1]) + 1
            dealt = [
                comments[under + place][1]
                for place, index in enumerate(stack)
                if comment_only(under + place)
                and opening(comments[under + place][1], index)
            ]
            last = prints[stack[-1]]
            # A line that opens on a word may be prose that starts a comment
            # the next lines go on with, so a share-out that counts one holds
            # only when there is exactly one comment line for each print.
            depth = 0
            while comment_only(under + depth):
                depth += 1
            worded = any(prints[index] in word_by for index in stack)
            if (
                len(stack) > 1
                and len(dealt) == len(stack)
                and (not worded or depth == len(stack))
            ):
                for place, index in enumerate(stack[:-1]):
                    said_by[prints[index]] = [dealt[place]]
                said_by[last] = run_from(under + len(stack), [dealt[-1]], last)
            else:
                for index in stack:
                    word_by.pop(prints[index], None)
                run = run_from(under, [], last)
                if run:
                    said_by[last] = run
                elif comment_only(under) and opening(comments[under][1], stack[-1]):
                    said_by[last] = run_from(under + 1, [comments[under][1]], last)
            at = stack[-1] + 1

    # The prints a statement runs on past are read on their own lines first,
    # and those left without a comment there on the lines of the statement.
    for node, (own, _statement) in found.items():
        span[node] = own
    read([node for node, (own, stmt) in found.items() if own[1] < stmt[1]], words=False)
    # A print inside the arguments of one with a comment on its own lines is
    # held by that comment, the print whose comment holds it kept for it
    # here: one that closes on the line the comment is read from shares that
    # comment, which stands for the calls of both, and one with no comment of
    # its own is not read again on the lines of its statement.
    around = _prints_around(tree)
    holder: dict[ast.Call, ast.Call] = {}
    for node in found:  # each print before the prints inside its arguments
        outer = holder.get(around[node]) if node in around else None
        if outer is not None and (
            node not in said_by or span[node][1] == span[outer][1]
        ):
            holder[node] = outer
            said_by.pop(node, None)
            word_by.pop(node, None)
        elif node in said_by:
            holder[node] = node
    for node, (_own, statement) in found.items():
        if node not in holder:
            span[node] = statement
    read([node for node in found if node not in holder], words=True)

    # The run records a call under the line it opens on, so the prints a
    # comment may stand for are those that open on its lines.
    opening: dict[int, list[ast.Call]] = {}
    for node in found:
        opening.setdefault(node.lineno, []).append(node)
    shares: dict[_Span, tuple[list[ast.Call], list[ast.Call]]] = {}

    def stands_for(stretch: _Span) -> tuple[list[ast.Call], list[ast.Call]]:
        """The prints that open on the lines of *stretch* whose calls a
        comment there stands for, and those whose calls it does not: a print
        held by a comment of its own on fewer lines inside them, its own or
        that of a print around it, and one that runs on past them.

        Read once for each stretch, and only over the prints that open on
        it, so that a page of many prints each with its comment is read in a
        time that grows with the page, not with its square.
        """
        if stretch not in shares:
            first, last = stretch
            kept: list[ast.Call] = []
            left: list[ast.Call] = []
            for number in range(first, last + 1):
                for node in opening.get(number, ()):
                    owner = holder.get(node, node)
                    own = owner in said_by and span[owner] != stretch
                    inside = own and first <= span[owner][0] and span[owner][1] <= last
                    past = (node.end_lineno or node.lineno) > last
                    (left if inside or past else kept).append(node)
            shares[stretch] = (kept, left)
        return shares[stretch]

    # A module that imports another's every name may hold its print: no
    # call of the name is then known to read the builtin.
    every_name = _imports_every_name(tree)
    bound = every_name or _binds_print(tree)
    promises: list[_Promise] = []
    for node in sorted(
        said_by, key=lambda node: (span[node][0], node.lineno, node.col_offset)
    ):
        kept, left = stands_for(span[node])
        promises.append(
            _Promise(
                span[node][0],
                span[node][1],
                tuple(said_by[node]),
                tuple((_place(each), _arguments(each)) for each in kept),
                word_by.get(node),
                tuple(_place(each) for each in left),
                not bound or (not every_name and _reads_builtin(tree, node)),
            )
        )
    return promises


def _parts(text: str, *, label: bool = False, segment: int = 0) -> list[_Part]:
    """The values, words and ellipses of *text*, in order, each in *segment*."""
    return [part for _, _, part in _located_parts(text, label=label, segment=segment)]


def _located_parts(
    text: str, *, label: bool = False, segment: int = 0
) -> list[tuple[int, int, _Part]]:
    """:func:`_parts`, each with where it opens and closes in *text*."""
    parts: list[tuple[int, int, _Part]] = []
    at = 0
    for match in _OUTPUT_PART.finditer(text):
        before, at = text[at : match.start()], match.end()
        if match.group("value") is not None:
            part = _Part(
                "value",
                match.group("value").replace(" ", ""),
                label,
                rough=match.group("rough") is not None,
                cut=match.group("cut") is not None,
                before=before,
                segment=segment,
            )
        else:
            kind = "word" if match.group("word") is not None else "gap"
            part = _Part(kind, match.group(), label, before=before, segment=segment)
        parts.append((match.start(), match.end(), part))
    return parts


def _pieces(text: str, argument: _Argument) -> list[tuple[str, bool]]:
    """*text*, what one argument of a print wrote, cut into the pieces the
    page's own string literal wrote (``True``) and the values in between.
    """
    if argument is None:
        return [(text, False)]
    pieces: list[tuple[str, bool]] = []
    at = 0
    for index, literal in enumerate(argument):
        if literal is None:
            continue
        if index == 0:
            start = 0 if text.startswith(literal) else -1
        elif index == len(argument) - 1:
            start = len(text) - len(literal) if text.endswith(literal) else -1
        else:
            start = text.find(literal, at)
        if start < at:
            return [(text, False)]  # the literal is not where it should be
        if start > at:
            pieces.append((text[at:start], False))
        pieces.append((literal, True))
        at = start + len(literal)
    if at < len(text):
        pieces.append((text[at:], False))
    return pieces


class _Call(NamedTuple):
    """What one call of a print wrote, as the recorder keeps it."""

    #: What the file took of each separator between two arguments the call
    #: wrote: all of it, part of it, or none, as each write said.
    separators: Sequence[str]
    #: What each argument wrote.
    texts: Sequence[str]
    #: What the call wrote after the last of them: its ending, or the
    #: separator before an argument it failed to write.
    end: str
    #: What each argument of the print that made the call is
    #: (:data:`_Argument`), or ``None`` when that print is not known or its
    #: arguments cannot be told apart.
    arguments: tuple[_Argument, ...] | None = None

    @property
    def text(self) -> str:
        """What the call wrote, whole."""
        pieces = [self.texts[0]] if self.texts else []
        for separator, text in zip(self.separators, self.texts[1:], strict=True):
            pieces += [separator, text]
        return "".join([*pieces, self.end])


#: One call the run recorded: the order it began to write in among all the
#: calls of the run, where it stands in the script (:data:`_Place`), ``None``
#: when that is not known, and what it wrote.
_Recorded = tuple[int, _Place | None, _Call]


#: How a value a sign may stand before opens: with a digit, a point before
#: one, or the infinity a float prints by name.
_UNSIGNED = re.compile(r"\.?\d|inf(?![\w.])")


def _joins(char: str) -> bool:
    """Whether a sign right after *char* joins what stands either side of it
    (:data:`_JOINS`) rather than signing the value after it.
    """
    return re.fullmatch(_JOINS, char) is not None


def _signed(pieces: list[tuple[str, bool]]) -> list[tuple[str, bool]]:
    """*pieces*, none of them empty, with each sign between the page's own
    text and a value its code computed given to the side the output reads it
    with (:data:`_SIGN`), as a comment's is.

    A sign the text writes right before the value, as ``f"-{x:.2f} dB"``, or
    its minus sign (U+2212), signs what it formats: the reader reads a
    negative number. One that follows a digit, a letter, a point or a closing
    bracket joins what stands either side of it and stays the text's, as the
    hyphen of a range ``f"{a:.0f}-{b:.0f} Hz"`` or of a name ``f"NC-{n}"``
    does, and so does the sign of a negative value right after such a
    character, as in ``f"NC{n}"``: both print ``NC-35``, which reads the same
    whichever wrote the hyphen.
    """
    out = list(pieces)
    for at in range(len(out) - 1):
        (text, label), (value, value_label) = out[at], out[at + 1]
        if not label or value_label:
            continue
        if text[-1] in "-+\u2212" and _UNSIGNED.match(value) is not None:
            # What the output writes right before the sign: the text's own
            # character before it, or the end of the piece before.
            before = (
                text[-2:-1] if len(text) > 1 else (out[at - 1][0][-1:] if at else "")
            )
            if not (before and _joins(before)):
                out[at], out[at + 1] = (text[:-1], True), (text[-1] + value, False)
        elif (
            value[0] in "-+\u2212"
            and _UNSIGNED.match(value, 1) is not None
            and _joins(text[-1])
        ):
            out[at], out[at + 1] = (text + value[0], True), (value[1:], False)
    return [piece for piece in out if piece[0]]


def _stretches(calls: Sequence[_Call]) -> list[tuple[str, bool]]:
    """What a print wrote over all its calls, in the order it wrote it, cut
    into stretches of the page's own text (``True``: its literals, the
    separator, the ending) and of what its code computed (``False``), each
    call read with the arguments of the print that made it.

    Two pieces of the same kind written one after the other are one stretch,
    as a reader reads them: ``print(1, 2, sep="")`` writes the value ``12``,
    and a loop of ``print(x, end="")`` one value of all their digits. A
    computed value and the page's text never join, so ``f"A{x}"`` still
    writes the label ``A`` and the value of ``x``; a sign where the two meet
    goes to the side the output reads it with (:func:`_signed`).
    """
    pieces: list[tuple[str, bool]] = []
    for call in calls:
        arguments = call.arguments
        if arguments is not None and len(arguments) != len(call.texts):
            arguments = None
        for index, text in enumerate(call.texts):
            if index:
                pieces.append((call.separators[index - 1], True))
            pieces += _pieces(text, None if arguments is None else arguments[index])
        pieces.append((call.end, True))
    # Each stretch gathers its pieces and joins them once, so a loop of many
    # calls that write one stretch does not copy it again for each call.
    stretches: list[tuple[list[str], bool]] = []
    for text, label in _signed([piece for piece in pieces if piece[0]]):
        if stretches and stretches[-1][1] == label:
            stretches[-1][0].append(text)
        else:
            stretches.append(([text], label))
    return [("".join(texts), label) for texts, label in stretches]


def _written_parts(calls: Sequence[_Call]) -> list[_Part]:
    """The parts of what a print wrote over all its calls (:func:`_stretches`),
    a ``"line"`` part where it ended a line, its own text marked as a label
    and each part in the stretch it stands in, a complex number written
    across stretches read as one value (:func:`_line_parts`). A minus sign
    (U+2212) reads as a hyphen, as it does in a comment.
    """
    return _written_readings(calls)[0]


def _written_readings(calls: Sequence[_Call]) -> list[list[_Part]]:
    """The readings of what a print wrote over all its calls: its parts
    (:func:`_written_parts`), and, where it spells a complex number one of
    whose parts its own text writes, the parts read with that number as one
    value too (:func:`_line_parts`), which a comment may state whole as it
    may state the computed part alone.
    """
    out: list[_Part] = []
    whole: list[_Part] = []
    line: list[tuple[str, bool, int]] = []
    for segment, (text, label) in enumerate(_stretches(calls)):
        for number, piece in enumerate(text.replace("\u2212", "-").split("\n")):
            if number:
                computed, spelled = _line_parts(line)
                out += computed
                whole += spelled
                line = []
                out.append(_Part("line", "\n", segment=segment))
                whole.append(out[-1])
            if piece:
                line.append((piece, label, segment))
    computed, spelled = _line_parts(line)
    out += computed
    whole += spelled
    return [out] if whole == out else [out, whole]


#: A complex number as a print may spell one across the page's own text and
#: the values its code computes: ``f"{a} + {b}j"``, ``f"{a}{b:+}j"``.
_SPELLED_COMPLEX = re.compile(rf"{_SIGN}{_REAL} *[-+] *{_REAL}j")


def _line_parts(
    pieces: Sequence[tuple[str, bool, int]],
) -> tuple[list[_Part], list[_Part]]:
    """The parts of one line of what a print wrote, from the *pieces* of its
    stretches it is written in, each with whether the page's own text wrote
    it and the stretch it stands in, read twice.

    A complex number whose two parts the code computed and whose sign and
    ``j`` the page's own text writes around them, as ``f"{a} + {b}j"`` does,
    is the one value the reader reads there, not two values and a label: it
    is read as a value the code computed, in the stretch of its real part.
    One whose other part the page's text writes, as ``f"{a} + 2.5j"``, is
    read so in the second reading only: the first keeps that part a label,
    which a comment may leave out.
    """
    located: list[tuple[int, int, _Part]] = []
    at = 0
    for text, label, segment in pieces:
        located += [
            (at + start, at + end, part)
            for start, end, part in _located_parts(text, label=label, segment=segment)
        ]
        at += len(text)
    if len(pieces) < 2:
        parts = [part for _, _, part in located]
        return parts, parts
    whole = "".join(text for text, _, _ in pieces)
    return (
        _merged(located, whole, written=False),
        _merged(located, whole, written=True),
    )


def _merged(
    located: Sequence[tuple[int, int, _Part]], whole: str, *, written: bool
) -> list[_Part]:
    """The *located* parts of the line *whole*, each complex number it spells
    across them (:func:`_spells_complex`) read as one computed value.
    """
    out: list[_Part] = []
    index = 0
    for match in _SPELLED_COMPLEX.finditer(whole):
        while index < len(located) and located[index][0] < match.start():
            out.append(located[index][2])
            index += 1
        inside = index
        while inside < len(located) and located[inside][1] <= match.end():
            inside += 1
        covered = located[index:inside]
        if _spells_complex(covered, match.start(), match.end(), written=written):
            real = covered[0][2]
            out.append(
                _Part(
                    "value",
                    match.group().replace(" ", ""),
                    before=real.before,
                    segment=real.segment,
                )
            )
            index = inside
    return out + [part for _, _, part in located[index:]]


def _spells_complex(
    covered: Sequence[tuple[int, int, _Part]], start: int, end: int, *, written: bool
) -> bool:
    """Whether the parts *covered*, each where it opens and closes in a line,
    are a complex number spelled from *start* to *end* (:data:`_SPELLED_COMPLEX`):
    its real and its imaginary part, both computed or, when *written*, one
    of them written by the page's own text, and at most the page's ``j``
    after them, opening and closing where it does.
    """
    parts = [part for _, _, part in covered]
    if len(parts) < 2 or (covered[0][0], covered[-1][1]) != (start, end):
        return False
    real, imaginary, *rest = parts
    if any(part.kind != "value" for part in (real, imaginary)):
        return False
    labels = [part.label for part in (real, imaginary)]
    if any(labels) and not (written and not all(labels)):
        return False
    if not rest:
        return imaginary.text.endswith("j")
    return [(part.kind, part.text) for part in rest] == [("word", "j")]


def _read_number(text: str) -> Decimal | None:
    """The number *text* writes, digit for digit, or ``None`` when its
    exponent is longer than a :class:`~decimal.Decimal` holds, some eighteen
    digits on a 64-bit build.
    """
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _states(said: Decimal, wrote: Decimal, *, rough: bool, cut: bool) -> bool:
    """True when the finite *said* states the finite *wrote*, held at the last
    digit *said* writes: ``0.67`` writes hundredths, ``126`` units, and
    ``1.0012e6`` hundreds.

    The step of that digit is built from the exponent, and the bounds are
    worked in a context with room for every digit of *said* and two more and
    for every exponent a decimal holds, so they are exact and the comparisons
    with them are too: no gap is rounded onto a bound, as it was in the 28
    digits of the default context, and no step overflows or underflows.
    Past the exponents a decimal holds, where a bound would be rounded, the
    context raises a :class:`~decimal.DecimalException` instead.
    """
    digits = len(said.as_tuple().digits)
    exponent = said.adjusted() - digits + 1  # that of the last digit
    exact = Context(prec=digits + 2, Emax=MAX_EMAX, Emin=MIN_EMIN, traps=[Inexact])
    step = Decimal((0, (1,), exponent))
    if cut:  # its digits begin the printed ones, sign and all
        if said.is_signed() != wrote.is_signed():
            return False  # only a zero of the other sign gets past the bounds
        if said.is_signed():
            return exact.subtract(said, step) < wrote <= said
        return said <= wrote < exact.add(said, step)
    reach = step if rough else Decimal((0, (5,), exponent - 1))
    return exact.subtract(said, reach) <= wrote <= exact.add(said, reach)


def _number_parts(text: str) -> tuple[str | None, str | None]:
    """The real and the imaginary part a number *text* writes, as written,
    each ``None`` where it writes none: ``1.2+3.4j`` writes both, ``3.4j``
    only the imaginary one, ``5`` and ``nan`` only the real one.
    """
    if not text.endswith("j"):
        return text, None
    both = re.fullmatch(rf"([-+]?{_REAL})([-+]{_REAL})j", text)
    if both is not None:
        return both.group(1), both.group(2)
    return None, text[:-1]


def _same_part(said: str | None, wrote: str | None, *, rough: bool, cut: bool) -> bool:
    """True when the comment's part *said* states the printed part *wrote*,
    a part either writes none of standing for an exact zero.
    """
    if said is None:
        if wrote is None:
            return True
        zero = _read_number(wrote)
        return zero is not None and zero == 0
    # Decimals, not floats: a comment written to every digit of a float is
    # held to its last digit, a step finer than the spacing of floats there,
    # and two numbers that round to one float are still two numbers.
    a, b = _read_number(said), _read_number("0" if wrote is None else wrote)
    if a is None or b is None:  # an exponent no decimal holds: the text
        return said == wrote
    if a.is_nan() or b.is_nan():
        return a.is_nan() and b.is_nan()
    if a.is_infinite() or b.is_infinite():
        return a == b
    try:
        return _states(a, b, rough=rough, cut=cut)
    except DecimalException:  # a bound past the exponents a decimal holds
        return said == wrote


def _same_value(said: _Part, wrote: str) -> bool:
    """True when the comment's value *said* states the printed value *wrote*.

    A number states a printed one that rounds to it at the last digit it
    writes, so ``0.67`` states ``0.6667``, ``126`` states ``125.89`` and
    ``1.0012e6`` states ``1001249.2``. Given roughly (``~``), it states one
    within a unit of that digit; cut short (``55.350667...``), one whose digits
    begin with its own. The digits decide, not the float they read as:
    ``9007199254740993`` does not state ``9007199254740992``. A complex
    number holds each of its parts that way, ``(1.23+4.57j)`` stating
    ``(1.234+4.567j)``, and a part it does not write is an exact zero; an
    ellipsis cuts short only the part it follows, so ``1.23+4.56j...``
    states ``(1.2296+4.5678j)``. A constant states only itself.
    """
    try:
        complex(said.text), complex(wrote)
    except ValueError:
        return said.text == wrote
    parts = _number_parts(said.text)
    # An ellipsis cuts short the digits it follows, those of the last part
    # the comment writes; a sign closes the real part before it in full.
    last = 0 if parts[1] is None else 1
    return all(
        _same_part(a, b, rough=said.rough, cut=said.cut and index == last)
        for index, (a, b) in enumerate(zip(parts, _number_parts(wrote), strict=True))
    )


def _meet_after_gap(
    said: list[_Part], k: int, wrote: list[_Part], j: int
) -> tuple[int, int] | None:
    """Where the comment, past an ellipsis at ``said[k - 1]``, meets the
    output again from ``wrote[j]`` on: the next part of each to read.

    The values after an ellipsis are the last ones of a line of the output, or
    of the whole of it: the ellipsis stands for the middle of an array or for
    the lines of a loop between the first and the last. The fewest values
    that meet that way win, so words and numbers of annotation after them
    stay annotation. Failing that, the ellipsis stands for what comes before
    the first value that meets the next one, as at the head of a quoted
    message. A second ellipsis before any value leaves out the same stretch,
    words between the two or not, so the values after it are the ones that
    meet: ``[1 ... ... 9]`` and ``1 ... one line a band ... 9`` still end on
    the 9.
    """
    after: list[int] = []
    for n in range(k, len(said)):
        if said[n].kind == "gap":
            if after:
                break
            continue
        if said[n].kind == "value":
            after.append(n)
    if not after:
        return len(said), len(wrote)
    stated = [
        n
        for n in range(j, len(wrote))
        if wrote[n].kind == "value" and not wrote[n].label
    ]
    ends = [n for n in range(j, len(wrote)) if wrote[n].kind == "line"]
    # How many of the stated values stand before each end, counted on as the
    # ends go by rather than again for each one, which made a loop of many
    # lines quadratic; an end with no new value before it is the last again.
    reached = 0
    tried = -1
    for end in [*ends, len(wrote)]:
        while reached < len(stated) and stated[reached] < end:
            reached += 1
        if reached == tried:
            continue
        tried = reached
        for count in range(min(len(after), reached), 0, -1):
            tail = stated[reached - count : reached]
            if all(
                _same_value(said[a], wrote[b].text)
                for a, b in zip(after[:count], tail, strict=True)
            ):
                return after[count - 1] + 1, tail[-1] + 1
    for n in stated:
        if _same_value(said[after[0]], wrote[n].text):
            return after[0] + 1, n + 1
    return None


def _promised_after(said: list[_Part], last: int, read: int) -> int | None:
    """Where the comment writes the first value after ``said[last]``, the last
    value the print bore out (``-1`` for none), when that value is still part
    of what the comment promises the print writes, or ``None``.

    The parts before ``said[read]``, the first part of the comment the print
    did not reach, are words the comment read beside the print and numbers of
    the print's own label: they say what the print wrote, so they are read
    past as if they were not there, and so is a colon or an equals sign after
    them.

    The value is promised when it stands inside the innermost bracket that
    was open at ``said[last]`` and has not closed since, as the print that
    writes ``[0.52 0.7  0.8 ]`` or ``(5,)`` has lost a value of its comment
    ``[0.52 0.7  0.8  0.89]`` or ``(5 bands, 59225 samples)``; when only
    spaces, commas and opening brackets stand between the two and no word
    follows it, as in ``2 3 4``, ``True 0.12 (40.0, 315.0)`` or, the print's
    words read past, ``Lp: 99.8 Bands: [12.6 15.8]`` beside a print that
    wrote ``Lp: 99.8 Bands: []``; and when the comment opens on it, whatever
    follows it, as the print that writes ``Bands: []`` has lost the ``12.6``
    of ``Bands: [12.6, 15.8]``. A value after a word of the comment's own,
    outside that bracket, is a note, as the ``2`` of ``engineering (Table 2
    class 3)`` is beside a print that wrote ``engineering``, and so is one a
    word follows, the ``0.458`` of ``0.358  (0.458 with normal hearing)`` or
    the ``1`` of a unit ``1/s``.

    A note ends the reading of the values next to the printed ones, not what
    an ellipsis promises: the first ellipsis after ``said[last]``, a note
    before it or not, says the print goes on to the values after it, so the
    first of them is promised wherever it stands, as it is when the print
    does go on (:func:`_meet_after_gap`). The print that writes ``[99.8]`` has
    lost the ``87.7`` of ``[99.8 ... 87.7]``, and the print that writes
    ``99.8 dB`` that of ``99.8 dB at 125 Hz ... 87.7 dB at 8000 Hz``; a note
    that writes an ellipsis before a number of its own, as ``7 octaves ... 3
    thirds``, promises that number too, so such a note goes after an arrow
    (:data:`_ARROW`). An ellipsis with no value after it, ``[0 1 2 ...]``,
    promises none.
    """
    depth = sum(_open_brackets(part.before) for part in said[: last + 1])
    floor = depth
    inside = depth > 0
    adjacent = True
    for at in range(last + 1, len(said)):
        part = said[at]
        for char in part.before:
            depth += (char in "([{") - (char in ")]}")
            inside = inside and depth >= floor
        if at < read:
            continue  # read beside the print's own text
        between = r"[\s:=,(\[{]*" if last + 1 < read == at else r"[\s,(\[{]*"
        adjacent = adjacent and re.fullmatch(between, part.before) is not None
        if part.kind == "gap":
            break
        if part.kind == "value":
            followed = at + 1 < len(said) and said[at + 1].kind == "word"
            if inside or (adjacent and (last < 0 or not followed)):
                return at
            break
        adjacent = False
    gap = next((n for n in range(last + 1, len(said)) if said[n].kind == "gap"), None)
    if gap is None:
        return None
    return next((n for n in range(gap + 1, len(said)) if said[n].kind == "value"), None)


def _apart(wrote: list[_Part], j: int, segment: int) -> _Part | None:
    """The first value the print computed from ``wrote[j]`` to the end of that
    line that stands outside *segment*, or ``None``: a comment that quotes a
    message may stop inside the message, and not before a value written apart
    from it, as the ``5`` of ``print(message, 5)``.
    """
    for part in wrote[j:]:
        if part.kind == "line":
            return None
        if part.kind == "value" and not part.label and part.segment != segment:
            return part
    return None


def _held(said: list[_Part], wrote: list[_Part]) -> str:
    """Why the comment's parts *said* do not state the output's parts *wrote*,
    or ``""`` (:func:`output_disagreement` gives the reading).
    """
    said_values = [part for part in said if part.kind == "value"]
    wrote_values = [p for p in wrote if p.kind == "value" and not p.label]
    if (
        len(said_values) == 1
        and len(wrote_values) > 1
        and all(_same_value(said_values[0], p.text) for p in wrote_values)
    ):
        return ""  # one value for an output that is that value throughout
    # The last value of the comment the print has borne out so far, a number
    # of the print's own label left out: the comment repeats that, as it
    # repeats a word the print wrote.
    last = -1
    k = j = 0
    # Whether the comment has stated a value, whether a line of the output
    # has ended since the last one it stated, how many words of a computed
    # text (a message) the comment has quoted in a row, the stretch of the
    # output the last of them stands in, and whether that row was broken by a
    # part either side read past. A word of the print's own label is repeated,
    # not quoted: it leaves the row as it was.
    stated = crossed = broken = False
    quoted = 0
    quoted_in = -1
    while j < len(wrote):
        part = wrote[j]
        if part.kind == "line":
            crossed = True
        elif part.kind == "word":
            if k < len(said) and said[k].kind == "word" and said[k].text == part.text:
                k += 1
                if not part.label:
                    quoted = 1 if broken else quoted + 1
                    quoted_in = part.segment
                elif broken:
                    quoted = 0
                broken = False
            elif k < len(said):
                broken = True
        else:
            while k < len(said) and said[k].kind == "word":
                k += 1
                broken = True
            if k < len(said) and said[k].kind == "gap":
                meet = _meet_after_gap(said, k + 1, wrote, j)
                if meet is None:
                    value = next(p.text for p in said[k + 1 :] if p.kind == "value")
                    return f"the comment's {value} after its ellipsis is never printed"
                k, j = meet
                if said[k - 1].kind == "value":
                    last = k - 1
                stated, crossed, broken, quoted = True, False, True, 0
                continue
            if k == len(said):
                if not part.label:
                    if stated and crossed:
                        return ""
                    if quoted and not broken:
                        apart = _apart(wrote, j, quoted_in)
                        if apart is None:
                            return ""
                        return f"the comment stops before the printed {apart.text}"
                    return f"the comment stops before the printed {part.text}"
            elif _same_value(said[k], part.text):
                if not part.label:
                    last = k
                k += 1
                if broken:
                    quoted, broken = 0, False
                stated, crossed = True, False
            elif part.label:
                broken = True
            else:
                return (
                    f"the comment says {said[k].text} where the print wrote {part.text}"
                )
        j += 1
    promised = _promised_after(said, last, k)
    if promised is None:
        return ""
    value = said[promised].text
    if any(part.kind == "gap" for part in said[last + 1 : promised]):
        return f"the comment's {value} after its ellipsis is never printed"
    if last < 0:
        return f"the comment says {value} where the print wrote no value"
    return f"the print stops before the comment's {value}"


def _lines_of(parts: list[_Part]) -> list[list[_Part]]:
    """*parts* cut at each ``"line"`` part, the empty lines left out."""
    lines: list[list[_Part]] = [[]]
    for part in parts:
        if part.kind == "line":
            lines.append([])
        else:
            lines[-1].append(part)
    return [line for line in lines if line]


#: An arrow, which in a comment leads from the output to a note on it:
#: ``78.2 Hz, 38.6 Hz -> valid here``.
_ARROW = re.compile(r"\s*(?:->|\u2192)")

#: A comma between two digits, which a Spanish comment writes as its decimal
#: point (``35,9 m``) or as the comma of a list it writes without spaces.
_DIGIT_COMMA = re.compile(r"(?<=\d),(?=\d)")


def _decimal_points(texts: Sequence[str], *, in_brackets: bool) -> list[str]:
    """*texts*, the lines of a Spanish comment, each comma between two digits
    read as a decimal point, or, with *in_brackets* false, only those outside
    a bracket the comment opens, the ones inside one left the commas of a list
    (``[1,2]``). A bracket a line leaves open goes on over the next line, as
    the comment's container does.

    Outside a bracket a comma between two digits is never a list's: read as
    one, the digits after it would be a value a word may follow as a note, so
    that ``0,5 dB`` would state ``0.4 dB`` on its ``0``.
    """
    out: list[str] = []
    # The brackets open at each comma are counted on from the last one, not
    # counted again from the start of the line, which made a long line of
    # values quadratic.
    depth = 0
    for text in texts:
        pieces: list[str] = []
        at = 0
        for match in _DIGIT_COMMA.finditer(text):
            depth += _open_brackets(text[at : match.start()])
            pieces.append(text[at : match.start()])
            pieces.append("," if depth > 0 and not in_brackets else ".")
            at = match.end()
        out.append("".join([*pieces, text[at:]]))
        depth += _open_brackets(text[at:])
    return out


def _disagreement(
    said_lines: Sequence[str],
    wrote: list[_Part],
    *,
    decimal_comma: bool,
    arrow: bool = True,
    spelled: list[_Part] | None = None,
) -> str:
    """Why the comment lines *said_lines* do not state the output *wrote*.

    :param decimal_comma: Read a comma between two digits as a decimal point,
        or, when the comment does not state the output that way and the comma
        stands inside a bracket, as the comma between two values that it is
        in ``[1,2]`` (:func:`_decimal_points`). The commas of all the
        comment's brackets are read alike: one that writes a decimal comma in
        a bracket has said what its commas are, so the ``[1,2]`` of
        ``[0,5; 1,5] [1,2]`` is 1.2, as a reader takes it.
    :param arrow: Let a line of the comment end what it states at an arrow
        (:data:`_ARROW`), the rest of it a note; off when the print writes an
        arrow itself.
    :param spelled: The output read with each complex number it spells
        across a part the page's own text writes as one value
        (:func:`_written_readings`), which the comment may state instead:
        the reason given is the one of the reading that reads such a number
        as the comment does, whole when the comment writes a complex number.
    """
    texts = [
        _NOT_A_VALUE.sub("", _reading(text).replace("\u2212", "-"))
        for text in said_lines
    ]
    readings = [texts]
    if decimal_comma:
        decimal = _decimal_points(texts, in_brackets=True)
        listed = _decimal_points(texts, in_brackets=False)
        readings = [decimal] if listed == decimal else [decimal, listed]
    outputs = [wrote] if spelled is None else [wrote, spelled]
    if spelled is not None and any(
        part.kind == "value" and part.text.endswith("j")
        for part in _parts(" ".join(texts))
    ):
        outputs.reverse()
    why = ""
    for output in outputs:
        for reading in readings:
            failed = _read(reading, output)
            if not failed:
                return ""
            why = why or failed
            if arrow:
                noted = [_ARROW.split(text, maxsplit=1)[0] for text in reading]
                if noted != reading and not _read(noted, output):
                    return ""
    return why


def _read(texts: list[str], wrote: list[_Part]) -> str:
    """Why the comment lines *texts*, as :func:`_disagreement` prepared them,
    do not state the output *wrote*, or ``""``.
    """
    said = _parts(" ".join(texts))
    if said and said[0].kind == "word" and texts[0].lstrip("~\u2248 ")[:1] in "'\"":
        first = next((p.text for p in wrote if p.kind == "word"), None)
        if first != said[0].text:
            return f"the comment opens on {said[0].text!r}, the print on {first!r}"
    why = _held(said, wrote)
    if why and len(texts) > 1:
        lines = _lines_of(wrote)
        if len(lines) >= len(texts) and not any(
            _held(_parts(text), line) for text, line in zip(texts, lines, strict=False)
        ):
            return ""
    return why


def _reads_decimal_comma(output: str, *, spanish: bool) -> bool:
    """Whether a comma between two digits of a comment is a decimal point.

    It is on a Spanish page, unless the print writes such a comma itself, in a
    row of text it prints (``'0,025'``): then the comment quotes it as written.
    """
    return spanish and re.search(r"\d,\d", output) is None


def output_disagreement(
    promised: str | Sequence[str],
    written: str | Sequence[str],
    *,
    decimal_comma: bool = False,
) -> str:
    """Why the comment *promised* does not state the output *written*, or ``""``.

    The comment states the printed values in their order, every one of them,
    each at the decimals it writes it to (:func:`_same_value`); what follows
    the last is annotation, unless the print stops short of a value the
    comment still promises (:func:`_promised_after`), and an arrow may start
    that annotation early (:data:`_ARROW`). Between two values it may write a
    unit or a word,
    and it need not repeat a word the print wrote, nor a number of the
    print's own string literal, the label around the values. It may stop at
    the end of a line of the output, having stated the lines before in full,
    as a comment beside a print in a loop states the first time round; and a
    comment that quotes a message word for word may stop where its quotation
    does. An ellipsis stands for the values it leaves out (:func:`_meet_after_gap`),
    and one value states an output that is that value throughout. A comment
    over several lines may also state the output line by line, each line with
    its own annotation. A comment that opens on a quoted word quotes the word
    the print opens with. *decimal_comma* reads a comma between two digits as
    a decimal point, as a Spanish page may write one, or, inside a bracket,
    as the comma of a list where the comment states the output that way,
    unless the print writes such a comma itself (:func:`_reads_decimal_comma`).

    :param promised: The comment, or its lines.
    :param written: What the print wrote, or what each of its calls wrote, as
        values with no label.
    """
    lines = promised.splitlines() if isinstance(promised, str) else list(promised)
    calls = [written] if isinstance(written, str) else list(written)
    wrote, *spelled = _written_readings([_Call((), [text], "\n") for text in calls])
    output = "\n".join(calls)
    comma = _reads_decimal_comma(output, spanish=decimal_comma)
    arrow = _ARROW.search(output) is None
    return _disagreement(
        lines,
        wrote,
        decimal_comma=comma,
        arrow=arrow,
        spelled=spelled[0] if spelled else None,
    )


def output_disagreements(
    page: pathlib.Path,
    script: str,
    lines: dict[int, int],
    written: dict[int, list[_Recorded]],
    *,
    rebound: bool = False,
) -> list[str]:
    """Failures for every output comment of *page* that its print contradicts.

    :param script: The script the page ran as (:func:`_script`).
    :param lines: The line of the page each line of the script stands on.
    :param written: What each print wrote, keyed by the line of the script
        its call opens on: one ``(order, place, call)`` per call
        (:data:`_Recorded`), *order* counting the calls of the whole run in
        the order they began to write. A comment that stands for the prints
        of several lines is held to their calls in that order, as they took
        turns: two prints of a comprehension over two lines write one value
        each time round. A call is the comment's when it opens on the
        comment's lines and does not stand where a print stands whose calls
        the comment does not stand for (:attr:`_Promise.apart`), and it is
        read with the arguments of the print that stands where it does.
    :param rebound: Whether the run ended with the name ``print`` bound to
        something else than the recorder, in the builtins or in the
        script's own module (:data:`_RECORDER`): a print whose calls the
        run did not record then need not be one the page never runs.
    """
    failures: list[str] = []
    spanish = page.is_relative_to(_SITE_ES)
    for promise in promised_outputs(script):
        where = f"{_rel(page)}:{lines.get(promise.first, promise.first)}"
        apart = set(promise.apart)
        arguments = dict(promise.prints)
        kept = [
            (order, call._replace(arguments=arguments.get(place) if place else None))
            for number in range(promise.first, promise.last + 1)
            for order, place, call in written.get(number, [])
            if place not in apart
        ]
        calls = [call for _, call in sorted(kept, key=lambda kept: kept[0])]
        wrote, *spelled = _written_readings(calls)
        if promise.word is not None:
            first = next((part for part in wrote if part.kind != "line"), None)
            if first is None or (first.kind, first.text) != ("word", promise.word):
                continue  # prose about the line, not what the print writes
        if not calls:
            if promise.builtin and not rebound:
                failures.append(
                    f"{where}: the comment promises {promise.text!r}, but the "
                    "page never runs this print"
                )
            continue
        output = "".join(call.text for call in calls).removesuffix("\n")
        comma = _reads_decimal_comma(output, spanish=spanish)
        arrow = _ARROW.search(output) is None
        why = _disagreement(
            promise.lines,
            wrote,
            decimal_comma=comma,
            arrow=arrow,
            spelled=spelled[0] if spelled else None,
        )
        if why:
            failures.append(
                f"{where}: {why}; the comment promises {promise.text!r}, the "
                f"print wrote {output!r}"
            )
    return failures


#: The module a page's script imports before anything else. It wraps
#: ``print`` so that every call made from the script itself, at any depth of
#: its own functions and loops, also records what the call writes, keyed by
#: the line of the script the call opens on, with where the call stands
#: (:data:`_Place`), and numbered in the order the calls began to write; a
#: print made inside the library is not the page's and is not recorded. The
#: call writes through a file that hands each piece on to the one it was
#: given and keeps what that file took, so the record holds what the print
#: wrote and nothing else: each argument converted once, by the print
#: itself, each separator and the ending as the file took them, of a write
#: the file took in part only the characters it says it took, by the count
#: its ``write`` returns or on the :class:`BlockingIOError` it raises, and of
#: a print that fails part of the way, or to a closed file, only what it
#: wrote before it failed. When the script ends, however it ends, the record
#: is saved beside it as JSON for :func:`_run_page` to read, with whether the
#: name ``print`` then still reaches the wrapper, in the builtins and in the
#: script's own module: a page that bound it to something else while it ran
#: (``builtins.print = ...``, ``globals()["print"] = ...``) made calls that
#: need not have reached it.
_RECORDER = """\
import atexit
import builtins
import itertools
import json
import os
import sys

_SCRIPT = sys.argv[0]
_SAVED = os.path.join(os.path.dirname(os.path.abspath(_SCRIPT)), "printed.json")
_PRINT = builtins.print
_WRITTEN = {}
_ORDER = itertools.count()
_PLACES = {}


def _took(text, count):
    # A write that says it took fewer characters than it was given took
    # those first ones; one that says nothing, or something else, took all.
    if isinstance(count, int) and not isinstance(count, bool):
        if 0 <= count < len(text):
            return text[:count]
    return text


class _Kept:
    def __init__(self, file):
        self.file = file
        self.pieces = []
        self.order = None

    def write(self, text):
        if self.order is None:
            self.order = next(_ORDER)
        try:
            written = self.file.write(text)
        except BlockingIOError as blocked:
            # A write that blocks counts the characters it took before then.
            count = getattr(blocked, "characters_written", 0)
            if isinstance(count, int) and count > 0:
                self.pieces.append(text[:count])
            raise
        self.pieces.append(_took(text, written))
        return written

    def flush(self):
        self.file.flush()


def _place(frame):
    # Where the call the frame is making stands: the place the interpreter
    # gives the instruction it is at, read once for each code object.
    code = frame.f_code
    places = _PLACES.get(code)
    if places is None:
        places = _PLACES[code] = list(code.co_positions())
    return places[frame.f_lasti // 2]


def _keep(line, place, order, count, pieces):
    # A print writes its arguments, each separator between two of them and
    # then its ending, each by a write of its own: what the file took of a
    # separator is kept as it took it, and what it took after the last
    # argument it wrote is the ending, or the separator before an argument
    # the print failed to write.
    texts = pieces[0 : max(2 * count - 1, 0) : 2]
    separators = pieces[1 : max(2 * len(texts) - 1, 0) : 2]
    at = 2 * len(texts) - 1 if texts else 0
    after = pieces[at] if at < len(pieces) else ""
    _WRITTEN.setdefault(line, []).append([order, place, separators, texts, after])


def _print(*args, sep=" ", end="\\n", file=None, flush=False):
    caller = sys._getframe(1)
    target = sys.stdout if file is None else file
    if caller.f_code.co_filename != _SCRIPT or target is None:
        return _PRINT(*args, sep=sep, end=end, file=file, flush=flush)
    kept = _Kept(target)
    try:
        return _PRINT(*args, sep=sep, end=end, file=kept, flush=flush)
    finally:
        if kept.pieces:
            place = _place(caller)
            _keep(caller.f_lineno, place, kept.order, len(args), kept.pieces)


def _save():
    # Whether the page bound the name print to something else as it ran, in
    # the builtins or in its own module, where a call of the name finds it.
    script = sys.modules.get("__main__")
    rebound = builtins.print is not _print or (
        getattr(script, "print", _print) is not _print
    )
    with open(_SAVED, "w", encoding="utf-8") as out:
        json.dump({"calls": _WRITTEN, "rebound": rebound}, out)


builtins.print = _print
atexit.register(_save)
"""


def _script(page: pathlib.Path, fixture: str = "") -> tuple[str, dict[int, int]]:
    """The script a page runs as, and the line of the page each line of a
    block stands on, keyed by its line in the script.

    *fixture* runs first, after the harness's own lines: the files of
    :data:`_FIXTURES` the page reads.
    """
    # A deprecated phonometry name in a snippet is an error, exactly as it is
    # in the test suite (pyproject filterwarnings): the guides teach the
    # canonical API, and a page that teaches an alias teaches a path that the
    # next major release removes.
    script = (
        "import _snippet_recorder\n"
        "del _snippet_recorder\n"
        "import warnings\n"
        "warnings.filterwarnings('error', message='.*is deprecated since phonometry.*',"
        " category=DeprecationWarning)\n"
        "import matplotlib\nmatplotlib.use('Agg')\n" + fixture
    )
    lines: dict[int, int] = {}
    for first, block in _located_blocks(page):
        if _is_sketch(block):
            continue
        script += "\n"
        start = script.count("\n") + 1
        for offset in range(block.count("\n") + 1):
            lines[start + offset] = first + offset
        script += block
    return script, lines


def _text(output: bytes | str | None) -> str:
    """What a stopped child wrote on a pipe, as text: :mod:`subprocess` hands
    it over as bytes on POSIX whatever ``text=`` asked for, as text on
    Windows, and as ``None`` when the child wrote nothing. Bytes are read as
    :func:`_run_page` reads text (:data:`_STREAM_ENCODING`).
    """
    if isinstance(output, bytes):
        return output.decode(_STREAM_ENCODING, errors="replace")
    return output or ""


def _saved_place(saved: object) -> _Place | None:
    """The place the recorder saved for a call (:data:`_Place`), as JSON
    gives it back: a list of its two lines and its two columns.
    """
    if isinstance(saved, list) and len(saved) == 4:
        first, last, start, end = saved
        return (first, last, start, end)
    return None


def _run_page(
    page: pathlib.Path, fixture: str = ""
) -> tuple[pathlib.Path, str, list[str]]:
    """Run a page's blocks as one script.

    :return: The page; the tail of its stderr when it fails, empty when it
        runs; and when it runs, every output comment of the page that
        disagrees with what its print wrote (:func:`output_disagreements`).
    """
    script, lines = _script(page, fixture)
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / "snippet.py"
        path.write_text(script, encoding="utf-8")
        (pathlib.Path(tmp) / "_snippet_recorder.py").write_text(
            _RECORDER, encoding="utf-8"
        )
        # The recorder tells two calls on one line apart by their columns,
        # which the interpreter drops when asked not to keep them.
        env = {k: v for k, v in os.environ.items() if k != "PYTHONNODEBUGRANGES"}
        try:
            done = subprocess.run(
                [sys.executable, str(path)],
                check=False,
                capture_output=True,
                text=True,
                encoding=_STREAM_ENCODING,
                errors="replace",
                timeout=_TIMEOUT_S,
                cwd=tmp,
                env=env,
            )
        except subprocess.TimeoutExpired as stopped:
            # What the page wrote on stderr before it was stopped, a warning
            # of the step it was in, is the cause the report can give.
            tail = _text(stopped.stderr).strip().splitlines()
            said = f"; its last line on stderr: {tail[-1]}" if tail else ""
            return page, f"timed out after {_TIMEOUT_S} s{said}", []
        if done.returncode != 0:
            tail = done.stderr.strip().splitlines()
            return page, tail[-1] if tail else f"exit status {done.returncode}", []
        record = pathlib.Path(tmp) / "printed.json"
        if not record.exists():
            return page, "the run ended without saving what its prints wrote", []
        saved = json.loads(record.read_text("utf-8"))
    written = {
        int(line): [
            (order, _saved_place(place), _Call(separators, texts, end))
            for order, place, separators, texts, end in calls
        ]
        for line, calls in saved["calls"].items()
    }
    rebound = saved["rebound"] is True
    return page, "", output_disagreements(page, script, lines, written, rebound=rebound)


def check_execution(pages: list[pathlib.Path]) -> list[str]:
    """Failures for every runnable page that does not run, every output
    comment of a page that runs and disagrees with what its print wrote, and
    stale skips.
    """
    runnable = [p for p in pages if p.stem not in _SKIP and _blocks(p)]
    skipped = [p for p in pages if p.stem in _SKIP and _blocks(p)]
    failures: list[str] = []
    still_skipped: dict[str, list[pathlib.Path]] = {}
    with concurrent.futures.ProcessPoolExecutor() as pool:
        fixtures = [_FIXTURES.get(page.stem, "") for page in runnable]
        for page, error, disagreements in pool.map(_run_page, runnable, fixtures):
            if error:
                failures.append(f"{_rel(page)}: {error}")
            failures += disagreements
        # A page that starts running must leave the skip list, or the list
        # quietly grows into a list of pages nobody checks. An entry covers a
        # guide, and a guide is written three times, as the site page in each
        # language and as the hand-written mirror under docs/; the entry is
        # stale only once every edition runs, since dropping it while one of
        # them still fails would turn a stale-skip report into a failing page.
        fixtures = [_FIXTURES.get(page.stem, "") for page in skipped]
        for page, error, _ in pool.map(_run_page, skipped, fixtures):
            if error:
                still_skipped.setdefault(page.stem, []).append(page)
    for page in skipped:
        if page.stem not in still_skipped:
            failures.append(
                f"{_rel(page)}: runs now; remove it from _SKIP in "
                f"{_rel(pathlib.Path(__file__))}"
            )
            still_skipped[page.stem] = []
    return failures


def _rel(path: pathlib.Path) -> str:
    try:
        return path.relative_to(_ROOT).as_posix()
    except ValueError:  # pragma: no cover - paths are always inside the repo
        return path.as_posix()


def _published() -> list[pathlib.Path]:
    """Surfaces outside the guides that print snippets at the reader.

    The README is the PyPI front page, ``llms.txt`` is what an assistant
    reads first and the home page is what a visitor of the site reads first,
    so a broken example there is the most expensive kind. They are not
    guides, so they get the same checks by a different route: the dumps under
    ``site/public/llms`` and ``llms-full.txt`` restate guide material and only
    take the static ones (see :func:`main`).
    """
    published = [
        _ROOT / "README.md",
        _ROOT / "README_PYPI.md",
        _ROOT / "llms.txt",
        _HOME,
    ]
    return [p for p in published if p.exists()]


def _restated() -> list[pathlib.Path]:
    """Generated dumps that concatenate guide text; static checks only."""
    out = [
        _ROOT / "llms-full.txt",
        *sorted((_ROOT / "site" / "public" / "llms").glob("*.txt")),
    ]
    return [p for p in out if p.exists()]


def _pages() -> tuple[list[pathlib.Path], list[tuple[pathlib.Path, pathlib.Path]]]:
    """Every page with snippets, and the pairs that must carry the same code."""
    site_en = [
        p
        for p in sorted(_SITE.rglob("*.md*"))
        if "/es/" not in p.as_posix() and "reference/api" not in p.as_posix()
    ]
    # `superpowers/` is gitignored scratch space, as in
    # scripts/check_conformance_claims.py; it is not documentation.
    mirror = sorted(
        p
        for p in _DOCS.rglob("*.md")
        if "superpowers" not in p.relative_to(_DOCS).parts
    )
    pairs: list[tuple[pathlib.Path, pathlib.Path]] = []
    for page in site_en:
        twin = _SITE_ES / page.relative_to(_SITE)
        if twin.exists():
            pairs.append((page, twin))
    everything = (
        site_en
        + mirror
        + _published()
        + _restated()
        + [p for _, p in pairs if p.is_relative_to(_SITE_ES)]
    )
    return everything, pairs


def _runnable(pages: list[pathlib.Path]) -> list[pathlib.Path]:
    """The pages of *pages* the execution and output checks run.

    Every edition a reader can copy from: the site page in both languages,
    and the hand-written mirror under docs/ that GitHub serves, with the
    published surfaces. The mirror is not a copy -- 105 of its 171 pages
    carry different code from their site page, mostly reworded comments but
    not only -- so running the site page proves nothing about it, and its 835
    blocks were the largest body of published example code nothing executed.
    The Spanish page translates its strings and its comments, the output
    comments among them, and 42 of its pages bind more than that differently
    from their English twin, so what it prints is known only by running it.
    The generated dumps restate guide text and are not run.
    """
    return (
        [p for p in pages if p.is_relative_to(_SITE)]
        + [p for p in pages if p.is_relative_to(_DOCS)]
        + _published()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--static", action="store_true", help="skip the execution pass")
    args = parser.parse_args()

    pages, pairs = _pages()
    restated = set(_restated())
    failures = check_shadowing([p for p in pages if p not in restated])
    failures += check_shadowing(sorted(restated), carry=False)
    failures += check_translations(pairs)
    stage = "static checks"
    if not args.static:
        failures += check_execution(_runnable(pages))
        stage = "checks"

    if failures:
        print(f"{len(failures)} documentation snippet problems:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(
        f"Documentation snippets pass all {stage}: "
        f"{sum(len(_blocks(p)) for p in pages)} blocks over {len(pages)} pages."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
