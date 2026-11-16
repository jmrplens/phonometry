#!/usr/bin/env python3
r"""Fail on a decimal comma in English text, and on a Spanish label that keeps a point.

Two checks of the one decimal marker, each the other's mirror.

**English text takes a point** (rules P9 and F58, decided on 2026-11-15).
Every decimal number an English text writes itself is written with a point,
a value restated from a standard that prints it with a comma among them:
"ISO 9613-1 prints 2.2560 per metre", not "prints 2,2560". The comma is kept
in a literal transcription of the print and nowhere else:

- text between quotation marks (``"..."``, ``“...”``,
  ``‘...’``, ``«...»``, and ``'1,5'`` written as a value);
- a block quote that reproduces the print (a quote that opens on a label,
  ``> **Note.**``, ``> *Tip.*``, ``> Note:`` or ``> [!NOTE]``, is a note of
  ours and is read);
- the ``**The print:**`` field of an entry of ``docs/ERRATA.md``, every line
  of it, its maths and its tables included, and of an entry a Markdown fence
  shows;
- the printed column of the conformance report, where a cell gives the
  printed values as the page prints them: the ``expected`` and ``printed``
  values of ``scripts/conformance/``, the ``expected`` record of
  ``docs/conformance.json`` and the ``Expected`` column of
  ``docs/CONFORMANCE.md``. A sentence of ours in that column takes the point
  (rule P9); this check cannot tell the two apart there, so the column is a
  person's to read.

Straight double quotes pair by where they stand: a quote opens after a blank,
an opening bracket or the start of the text, and closes after a character that
is no blank, so the inch mark of ``a 2" pipe`` quotes nothing.

Spanish keeps the comma everywhere, and is never read: a Spanish file
(``es/``, ``*.es.md``, ``catalogue-es.json``, a ``*_es.svg`` figure), the
Spanish value of a translation table, a branch taken when the language is
``"es"``, a value held under an ``es`` key, a catalogue row transcribed from
a Spanish edition, and any string or paragraph that reads as Spanish once its
quotations are set aside: an English sentence that quotes a Spanish clause is
English.

A comma between digits that is no decimal marker is left alone wherever it
stands: a list (``1,2,3``), a pair of indices in brackets or braces
(``a[1,2]``, ``(2,1)``, ``{2,4}``, ``k_{1,2}``) or after a letter (``k2,1``),
a list of clauses (``5.2,5.3``), a chemical locant (``1,2-DHCP``), a list of
coordinates (``(0,90), (45,135)``), the unit interval in each of its forms
(``[0,1]``, ``(0,1]``, ``[0,1)``, ``(0,1)``), and everything that is code: an
inline code span that writes code or data, the code of a fence, a doctest, a
reStructuredText literal, a regular expression, a string of the test suite
(test data), an SVG path, a dash pattern or a list of coordinates, CSV (a
file, or the rows of one a string holds) and the data files. An index has one
or two digits and no leading zero, so “q_{0,1}”, ``(0,05)`` and “R(q0,9)” are
decimals; a mode, whose orders start at 0, is the exception: ``(0,2)`` beside
the word "mode" is notation, alone it is listed for a person, and after a
value (``71,8 (0,0)``) it is a decimal. A number such as ``1,500``, which may
be a decimal or a thousands group, is not refused: it is listed for a person
to decide, and ``--strict`` refuses it too.

An inline code span that writes a formula is text: a decimal comma or a
thousands group beside a variable or a unit, which Python would not parse as
integers (“A = 0,16 V / T”, “R(q0,1)”), is read and refused, while
``f(1,5)`` and a span with no letter, the cell ``0,30..0,50`` a catalogue
reads, stay code. A thousands group written with commas (``101,325 Pa``,
``91,658,333``) is refused in English text: P8 groups with a thin space.

How each file is read. Python through :mod:`tokenize` and :mod:`ast`: every
string and bytes literal with its role in the tree (a docstring, a value of a
Spanish table, an argument of a regular expression, a conformance column),
the pieces an implicit concatenation joins read as one, and every comment.
Markdown and MDX by their structure, through the shared readers of
``scripts/markdown_fences.py`` and ``scripts/markdown_spans.py``: the
frontmatter, the paragraphs, the table cells by column, the header row
among them, the block quotes, the inline code and maths, the tags and every
attribute a reader sees (all but the ones that hold code, ``class``, ``href``,
``src`` and their kind), quoted or as a string expression, and the strings of
an expression. A fence by its language: Python as a module, a script language
by its strings and comments, Markdown and plain text as a page, any other by
its ``#`` comments; the Don't example of a rule is not read. JavaScript,
TypeScript and JSON by their string literals, their comments and the keys that
hold them. The configuration files by their ``#`` comments and the values a
reader sees (a ``name``, ``title``, ``description`` or ``abstract``, a line
a recipe prints), and a BibTeX file by its prose fields. An English figure or
plate by the text it draws, which its committed SVG keeps in a comment beside
the outlines (a ``_es`` figure is Spanish). A generated file that copies the
text of another one (the GitHub edition under ``docs/``, ``llms.txt``, the API
reference written from the docstrings, the errata pages written from the
registry, ``README_PYPI.md``) is left to its source, which is read instead;
a generated file that writes numbers of its own (the catalogue data, the
conformance report) is read, since only its output shows what its generator
does.

**A Spanish label beside mathematics keeps its point** (rule F29). The Spanish
edition of a figure is the English one with its text rewritten at save time,
and the last step of that rewrite is the decimal comma::

    if s and "$" not in s and re.search(r"\d\.\d", s):
        artist.set_text(_decimal_comma(s))

The guard is deliberate -- a bare comma inside ``$...$`` sets as a maths
separator with the wrong spacing -- but it tests the WHOLE string. So a label
that carries mathematics ANYWHERE and a decimal number ANYWHERE ELSE keeps the
English point in its Spanish variant:

    "$L_\mathrm{eq}$ = 52.4 dB"   ->  Spanish figure still prints 52.4

Nothing downstream can see it: the language gate compares what each pass could
not translate, and a number is not a word. This reads the translation tables
of the figure code and reports a Spanish value that mixes a maths run with a
hard-coded decimal outside it. A label whose number is interpolated through
``format_number(value, language)`` localises itself, so placeholders are
ignored, and a clause number or a standard's designation is no measurement.

``--labels`` runs the second check alone, ``--english`` the first; with
neither, both run. Exit status 0 when nothing is refused, 1 otherwise.
"""

from __future__ import annotations

import argparse
import ast
import bisect
import html
import io
import json
import pathlib
import re
import subprocess  # nosec B404 - lists the tracked files with git, no shell
import sys
import tokenize
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from github_edition import is_edition_file
from markdown_fences import (
    MDX_EXPRESSION,
    MDX_TAG,
    PageLine,
    cell_spans,
    page_lines,
    quotation_marks,
)
from markdown_spans import inline_spans, replace_inline_spans_by_block

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence

#: The repository.
ROOT = pathlib.Path(__file__).resolve().parent.parent

# ===========================================================================
# The Spanish figure label beside mathematics (rule F29).
# ===========================================================================

DEFAULT_ROOTS = ("src/phonometry/_plot", "scripts/figures")

#: A decimal number: a digit, a point, a digit. Also the shape of a clause
#: number and of a standard designation, which is why the guards below exist.
_DECIMAL = re.compile(r"\d\.\d")

#: Numbers that are not measurements, and so keep their point in Spanish too: a
#: clause number ("5.3.3"), a standard's designation ("S3.5", "ISO 9613-2"), and
#: a pointer into a document -- an equation, a clause, a table, an example. The
#: last group is why this list is bilingual: a Spanish label writes "apartado
#: 8.2" and "Ec. 9.52", and neither number is a quantity.
_NOT_A_MEASUREMENT = re.compile(
    r"\d+\.\d+\.\d"  # 5.3.3
    r"|[A-Z]\d*\.\d"  # S3.5
    r"|(?:ISO|IEC|EN|UNE|ANSI|ASTM|AES|ITU|EBU|ECMA|DIN|BS)[\s\d.\-]*\d\.\d"
    r"|(?i:"
    r"Eq\.|Ec\.|Ecuaci[oó]n|Equation"
    r"|clause|apartado|cl[aá]usula|secci[oó]n|section"
    r"|cap[ií]tulo|chapter|annex|anexo"
    r"|table|tabla|figure|figura|fig\.|formula|f[oó]rmula"
    r"|example|ejemplo|note|nota"
    r")[\s\w&]*\d\.\d"
)

#: An f-string placeholder or a ``str.format`` field: the number is computed,
#: so the label's own text carries no decimal to lose.
_PLACEHOLDER = re.compile(r"\{[^{}]*\}")


def maths_runs(text: str) -> list[tuple[int, int]]:
    """Index pairs of the ``$...$`` regions of *text*."""
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for i, char in enumerate(text):
        if char != "$" or (i and text[i - 1] == "\\"):
            continue
        if start is None:
            start = i
        else:
            runs.append((start, i))
            start = None
    return runs


def at_risk(text: str) -> str | None:
    """The decimal a Spanish figure would print with a point, or None."""
    runs = maths_runs(text)
    if not runs:
        return None  # no dollar: the comma pass runs normally
    # Blank out the maths and every placeholder, then look at what is left.
    outside = list(text)
    for lo, hi in runs:
        for i in range(lo, hi + 1):
            outside[i] = " "
    rest = "".join(outside)
    rest = _PLACEHOLDER.sub(" ", rest)
    for match in _DECIMAL.finditer(rest):
        window = rest[max(0, match.start() - 12) : match.end() + 6]
        if _NOT_A_MEASUREMENT.search(window):
            continue
        return rest[max(0, match.start() - 20) : match.end() + 12].strip()
    return None


def check(paths: list[pathlib.Path]) -> list[tuple[str, int, str, str]]:
    """Report a translation PAIR whose Spanish half still carries the point.

    Asking "does this string mix maths with a decimal" alone is too blunt: the
    answer is yes for every label whose number is fine because its Spanish twin
    already bakes the comma in, and yes again for an equation reference, whose
    number is not a measurement in either language.

    The defect has a sharper shape. The tables are ``{english: spanish}``
    literals, so the question is whether the SPANISH value keeps a decimal point
    the comma pass will not reach. That is a defect whatever the English says.
    """
    found: list[tuple[str, int, str, str]] = []
    for path in paths:
        try:
            tree = ast.parse(path.read_bytes())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            for key, value in zip(node.keys, node.values, strict=False):
                if not isinstance(value, ast.Constant) or not isinstance(
                    value.value, str
                ):
                    continue
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    continue
                risky = at_risk(value.value)
                if risky:
                    found.append((str(path), value.lineno, value.value[:80], risky))
    return found


def _labels_main(roots: Sequence[str]) -> int:
    """Run the label check over *roots* and report it; the exit status."""
    paths: list[pathlib.Path] = []
    for root in roots:
        target = pathlib.Path(root)
        paths.extend([target] if target.is_file() else sorted(target.rglob("*.py")))

    found = check(paths)
    if not found:
        print(
            f"No label in {len(paths)} files mixes mathematics with a "
            f"hard-coded decimal."
        )
        return 0

    print(
        f"{len(found)} label(s) would keep an English decimal point in Spanish:\n",
        file=sys.stderr,
    )
    for path, line, text, risky in found:
        print(f"  {path}:{line}", file=sys.stderr)
        print(f"      {text!r}", file=sys.stderr)
        print(
            f"      the maths blocks the comma pass, so {risky!r} keeps its point",
            file=sys.stderr,
        )
    print(
        "\nEither bake the comma into the Spanish value, or format the number "
        "through format_number(value, language), which localises itself.",
        file=sys.stderr,
    )
    return 1


# ===========================================================================
# English text takes a point (rules P9 and F58).
# ===========================================================================

#: One number with a comma between two of its digits; the LaTeX decimal comma
#: ``{,}`` counts as one. ``1,2,3`` is one token, so a list is seen whole.
TOKEN = re.compile(r"(?<![0-9])[0-9]+(?:(?:,|\{,\})[0-9]+)+(?![0-9])")

#: A group of the fraction written after the first three digits, which only
#: a decimal has: “83,523 38” with a space, a narrow no-break space, a thin
#: space, a no-break space or the ``\,`` and ``~`` of LaTeX.
_GROUP_AFTER = re.compile(r"(?: | | | |\\,|\\ |~)[0-9]{1,3}(?![0-9])")

#: How many digits a thousands group holds.
_GROUP = 3

#: What a stretch of code leaves in the text it is taken out of: the object
#: replacement character, which is no digit, no letter, no space and no quote,
#: so the numbers on either side of it stay apart.
MARK = "￼"

#: The shapes a number with a comma takes. Only the first two are reported.
DECIMAL, AMBIGUOUS, THOUSANDS, LIST, NOTATION = (
    "decimal",
    "ambiguous",
    "thousands",
    "list",
    "notation",
)


#: A pair of numbers in parentheses, which a list of coordinates is written with.
_BRACKETED_PAIR = re.compile(r"\(\s*[-+]?\d+,\s*[-+]?\d+\s*\)")


#: A value written right before a bracket: ``71,8 (0,0)``.
_VALUE_BEFORE = re.compile(r"[0-9][ \u202f\u00a0]*$")
#: A word that says the bracketed pairs of its text are modes.
_MODE = re.compile(r"\bmodes?\b|\bmodo|\bmode\b", re.IGNORECASE)

#: What opens a subscript, right before its first index: ``_{``,
#: ``_\mathrm{``, ``_\text{``, ``_\rm{`` or the ``<sub>`` of HTML.
_SUBSCRIPT_OPEN = re.compile(r"(?:_(?:\\(?:mathrm|text|rm))?\{|<sub>)$")


def _index_pair(whole: str, fraction: str) -> bool:
    """Whether ``whole,fraction`` reads as a pair of indices, ``2,1`` or ``1,0``.

    An index has one or two digits and no leading zero; a part that opens on
    a zero (``0,1``, ``0,05``, ``1,05``) is a decimal however it is bracketed:
    the 0.1-quantile is written ``q_{0.1}``, and ``(0,05)(900)`` is a product.
    """
    short = len(whole) <= 2 and len(fraction) <= 2
    return (
        short
        and not whole.startswith("0")
        and not (len(fraction) > 1 and fraction.startswith("0"))
    )


def number_shape(text: str, start: int, end: int) -> str:
    """What the number ``text[start:end]``, which holds a comma, is.

    :return: :data:`DECIMAL` for a decimal comma; :data:`AMBIGUOUS` for a
        number of one to three digits, a comma and exactly three more, which a
        thousands group writes too; :data:`THOUSANDS` for groups of three
        after the first; :data:`LIST` for a list, a pair of indices in
        brackets or braces, or a list of clauses; :data:`NOTATION` for
        indices after a letter or a designation.
    """
    token = text[start:end]
    before = text[start - 1] if start else ""
    after = text[end : end + 1]
    latex = "{,}" in token
    parts = re.split(r"\{,\}|,", token)
    if before == "." or (after == "." and text[end + 1 : end + 2].isdigit()):
        return LIST
    if len(parts) > 2:
        groups = all(len(part) == _GROUP for part in parts[1:])
        if not latex and 1 <= len(parts[0]) <= _GROUP and groups:
            return THOUSANDS
        return LIST
    whole, fraction = parts
    pair = not latex and _index_pair(whole, fraction)
    if pair and (before.isalpha() or before == "_"):
        return NOTATION
    if pair and _SUBSCRIPT_OPEN.search(text, 0, start):
        return NOTATION  # the indices of a subscript: L_{1,2m}, L_\mathrm{1,2m}
    if pair and before and before in "[({" and after and after in "])}":
        return LIST
    if pair and before == "-" and start >= 2 and text[start - 2].isalpha():
        return NOTATION
    if pair and after == "-" and text[end + 1 : end + 2].isalpha():
        return LIST  # a chemical locant: 1,2-DHCP
    if before == "(" and after == ")" and len(_BRACKETED_PAIR.findall(text)) > 1:
        return LIST  # one of a list of coordinates: (0,90), (45,135)
    if (
        whole == "0"
        and len(fraction) == 1
        and before == "("
        and after == ")"
        and _VALUE_BEFORE.search(text, 0, start - 1)
    ):
        return DECIMAL  # a value in brackets after a value: ``71,8 (0,0)``
    if whole == "0" and fraction == "1" and before in "([" and after in ")]":
        return LIST  # the unit interval: [0,1], (0,1], [0,1), (0,1)
    if whole == "0" and len(fraction) == 1 and before == "(" and after == ")":
        # The pair (0,2) is a mode, the modes start at 0; with nothing to say
        # so it is listed for a person, never refused and never rewritten.
        return NOTATION if _MODE.search(text) else AMBIGUOUS
    if latex or len(fraction) != _GROUP or _GROUP_AFTER.match(text, end):
        return DECIMAL
    if len(whole) > _GROUP or whole.startswith("0"):
        return DECIMAL
    return AMBIGUOUS


#: The typographic quotation marks, each with the one that closes it.
_QUOTES = {"“": "”", "‘": "’", "«": "»"}
_CLOSERS = frozenset(_QUOTES.values())
#: A quotation between single quotes, as code and messages write one:
#: ``'1,5'``, ``'<0,02 above 200 Hz'``. No letter outside either mark, so the
#: apostrophes of ``it's`` and ``the tests' output`` open and close nothing.
_SINGLE_QUOTED = re.compile(r"(?<![\w'])'[^'\n]+'(?![\w'])")


def quoted_spans(text: str) -> list[tuple[int, int]]:
    """The ``(start, end)`` of every quotation of *text*, its marks included.

    Typographic marks pair by kind, the innermost first, and a closing mark
    with nothing open is an apostrophe. Straight double quotes pair in turn
    over the whole text, which is a paragraph, a string or a comment, so a
    quotation wrapped over lines is one span.
    """
    spans: list[tuple[int, int]] = []
    opened: list[tuple[str, int]] = []
    for index, char in enumerate(text):
        if char in _QUOTES:
            opened.append((char, index))
        elif char in _CLOSERS:
            for depth in range(len(opened) - 1, -1, -1):
                if _QUOTES[opened[depth][0]] == char:
                    spans.append((opened[depth][1], index + 1))
                    del opened[depth:]
                    break
    spans.extend(_straight_quotations(text))
    spans.extend((m.start(), m.end()) for m in _SINGLE_QUOTED.finditer(text))
    return spans


#: What may stand right before a straight quote that opens a quotation.
_OPENS_AFTER = frozenset(" \t\n([{=:-/\u2014\u2013")


def _straight_quotations(text: str) -> list[tuple[int, int]]:
    """The quotations between straight double quotes, read by where each stands.

    A quote opens after a blank, an opening bracket or the start of the text,
    before a character that is no blank; it closes after one that is no blank.
    So the inch mark of ``a 2" pipe``, which follows a digit, opens nothing.
    A quotation of a print may run over several sentences, so a stray opening
    quote still quotes the text up to the next closing one.
    """
    spans: list[tuple[int, int]] = []
    opened: int | None = None
    for index, char in enumerate(text):
        if char != '"':
            continue
        before = text[index - 1] if index else " "
        after = text[index + 1] if index + 1 < len(text) else " "
        if opened is None:
            if before in _OPENS_AFTER and not after.isspace():
                opened = index
        elif not before.isspace():
            spans.append((opened, index + 1))
            opened = None
    return spans


#: Words that only Spanish writes, and words that only English writes, for
#: telling the language of a stretch of text that nothing else names.
_SPANISH_WORDS = frozenset(
    [
        "de",
        "del",
        "la",
        "las",
        "los",
        "el",
        "en",
        "con",
        "según",
        "para",
        "por",
        "que",
        "una",
        "un",
        "y",
        "se",
        "al",
        "sobre",
        "entre",
        "es",
        "son",
        "está",
        "están",
        "su",
        "sus",
        "como",
        "más",
        "cada",
        "desde",
        "hasta",
        "sin",
        "tabla",
        "figura",
        "ecuación",
        "norma",
        "nivel",
        "niveles",
        "banda",
        "bandas",
        "frecuencia",
        "presión",
        "potencia",
        "sonido",
        "ruido",
        "valor",
        "valores",
        "medida",
        "medidas",
        "página",
        "impresa",
        "impreso",
        "igual",
        "salvo",
        "grosor",
        "hormigón",
        "suelo",
        "techo",
        "pared",
        "muro",
        "paso",
    ]
)
_ENGLISH_WORDS = frozenset(
    [
        "the",
        "of",
        "and",
        "to",
        "in",
        "is",
        "at",
        "for",
        "with",
        "from",
        "on",
        "by",
        "per",
        "are",
        "this",
        "that",
        "which",
        "it",
        "its",
        "as",
        "an",
        "be",
        "or",
        "not",
        "than",
        "each",
        "where",
        "when",
        "into",
        "level",
        "levels",
        "value",
        "values",
        "band",
        "bands",
        "printed",
        "prints",
        "print",
        "page",
        "table",
        "figure",
        "equation",
    ]
)
_ACCENTED = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡]")
_WORD = re.compile(r"[^\W\d_]+")
#: How much an accented letter weighs against a word of the other language.
_ACCENT_WEIGHT = 2


def reads_as_spanish(text: str) -> bool:
    """Whether *text* reads as Spanish: more of its words and accents are."""
    words = _WORD.findall(text.lower())
    spanish = sum(word in _SPANISH_WORDS for word in words)
    spanish += _ACCENT_WEIGHT * len(_ACCENTED.findall(text))
    english = sum(word in _ENGLISH_WORDS for word in words)
    return spanish >= _ACCENT_WEIGHT and spanish > english


def _reads_as_english(text: str) -> bool:
    """Whether *text* reads as English: more of its words are."""
    words = _WORD.findall(text.lower())
    english = sum(word in _ENGLISH_WORDS for word in words)
    return english > 0 and not reads_as_spanish(text)


#: One number of a list of coordinates.
_COORDINATE = r"[-+]?\d*\.?\d+"
#: A list of coordinates or path data, which is no text: two comma pairs or
#: more, held apart by blanks or by the commands of an SVG path.
_COORDINATES = re.compile(
    rf"^\s*[A-Za-z]?\s*{_COORDINATE},{_COORDINATE}"
    rf"(?:(?:\s+|\s*[MmLlHhVvCcSsQqTtAaZz]\s*){_COORDINATE},{_COORDINATE})+"
    r"\s*[Zz]?\s*$"
)


@dataclass(frozen=True)
class Finding:
    """One decimal comma in English text.

    :param path: The file, relative to the repository.
    :param line: The line it is written on, counted from 1.
    :param token: The number as written.
    :param kind: :data:`DECIMAL`, refused, or :data:`AMBIGUOUS`, for a person
        to decide.
    :param where: The part of the file: prose, a docstring, a comment, a
        string, a table cell.
    :param context: The text around it.
    """

    path: str
    line: int
    token: str
    kind: str
    where: str
    context: str = field(compare=False)


def _on_line(number: int) -> Callable[[int], int]:
    """A function that puts every position on line *number*."""
    return lambda _pos: number


def _line_counter(first: int, text: str) -> Callable[[int], int]:
    """A function from a position in *text* to its line, *text* opening on *first*."""
    breaks = [index for index, char in enumerate(text) if char == "\n"]
    return lambda pos: first + bisect.bisect_left(breaks, pos)


def _scan(
    out: list[Finding],
    rel: str,
    text: str,
    where: str,
    line_of: Callable[[int], int],
) -> None:
    """Add to *out* every decimal comma *text*, one unit of English text, writes.

    A unit that reads as Spanish writes none. A number between quotation
    marks is a transcription; a list, a group of thousands and notation are
    no decimal.
    """
    if not TOKEN.search(text) or _COORDINATES.match(text.strip()):
        return
    quotes = quoted_spans(text)
    if _unit_reads_as_spanish(text, quotes):
        return
    for match in TOKEN.finditer(text):
        shape = number_shape(text, match.start(), match.end())
        if shape not in (DECIMAL, AMBIGUOUS, THOUSANDS):
            continue
        if any(start < match.start() < end for start, end in quotes):
            continue
        context = text[max(0, match.start() - 50) : match.end() + 40]
        out.append(
            Finding(
                rel,
                line_of(match.start()),
                match.group(),
                shape,
                where,
                re.sub(r"\s+", " ", context.replace(MARK, "")).strip(),
            )
        )


def _unit_reads_as_spanish(text: str, quotes: Sequence[tuple[int, int]]) -> bool:
    """Whether a unit reads as Spanish, its quotations aside.

    An English sentence that quotes a long Spanish clause is English: what it
    writes outside the quotation decides. Only a unit whose own words are none
    of either language is read whole.
    """
    outside = list(text)
    for start, end in quotes:
        outside[start:end] = " " * (end - start)
    own = "".join(outside)
    if reads_as_spanish(own):
        return True
    words = _WORD.findall(own.lower())
    english = any(word in _ENGLISH_WORDS for word in words)
    return not english and reads_as_spanish(text)


def _blank(text: str) -> str:
    """*text* as :data:`MARK` characters, its line ends kept."""
    return re.sub(r"[^\n]", MARK, text)


def _blank_rst_literals(text: str) -> str:
    """*text* with its reStructuredText inline literals blanked.

    A literal opens on two backticks and closes on the next two that no third
    one follows (``:math:`x``` closes on the last two of its three), which is
    not how a Markdown span pairs its runs, so it is read here before them.
    """
    pieces: list[str] = []
    done = 0
    while (start := text.find("``", done)) >= 0:
        end = text.find("``", start + 2)
        while end >= 0 and text[end + 2 : end + 3] == "`":
            end += 1
        if end < 0:
            break
        literal = text[start : end + 2]
        kept = literal if _formula_span(literal) else _blank(literal)
        pieces.extend((text[done:start], kept))
        done = end + 2
    pieces.append(text[done:])
    return "".join(pieces)


#: A letter of a variable or a unit, which a formula writes and a data cell
#: (``0,85``, ``0,30..0,50``, ``"0,97"``) does not.
_LETTER = re.compile(r"[A-Za-z\u0391-\u03c9\u00b5]")


def _int_constants(code: str) -> set[tuple[int, int]] | None:
    """The spans of the integer literals *code* holds, or ``None`` if it is no code.

    *code* is read as a Python expression, then as a module; a span is a pair
    of character offsets on its one line.
    """
    for mode in ("eval", "exec"):
        try:
            tree = ast.parse(code, mode=mode)
        except (SyntaxError, ValueError):
            continue
        return {
            (node.col_offset, node.end_col_offset or node.col_offset)
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant)
            and type(node.value) is int
            and node.lineno == node.end_lineno == 1
        }
    return None


def _formula_span(span: str) -> bool:
    """Whether the backtick span *span* writes a formula and not code.

    A span is code unless it writes a number with a decimal comma or a
    thousands group beside a variable or a unit, which no code and no data
    cell would: ``foo(1,5)`` passes two integers and is code, and a span with
    no letter at all (``0,30..0,50``, the cell a catalogue reads) is data,
    while “A = 0,16 V / T” does not parse and “R(q0,1)” passes a name and
    an integer, so both write a decimal and are read as text.
    """
    inner = span.strip("`")
    tokens = [
        match
        for match in TOKEN.finditer(inner)
        if number_shape(inner, match.start(), match.end()) in (DECIMAL, THOUSANDS)
    ]
    if not tokens or "\n" in inner or not _LETTER.search(inner):
        return False  # no variable and no unit: a cell, a literal, data
    constants = _int_constants(inner)
    if constants is None:
        return True
    for match in tokens:
        parts = [part.span() for part in re.finditer(r"[0-9]+", match.group())]
        spans = {(match.start() + a, match.start() + b) for a, b in parts}
        if not spans <= constants:
            return True
    return False


def _blank_code_spans(text: str, *, roles: bool = False) -> str:
    """*text* with its backtick spans blanked, read by the shared span reader.

    :param roles: Whether *text* is reStructuredText, whose ``:math:`` role
        holds maths, which is read, where any other span is code.
    """
    if roles:
        text = _blank_rst_literals(text)
    pieces: list[str] = []
    done = 0
    for start, end in inline_spans(text, "`"):
        pieces.append(text[done:start])
        span = text[start:end]
        if roles and text[:start].endswith(":math:"):
            pieces.append(span)
        elif _formula_span(span):
            pieces.append(span)  # a formula we write, read as text
        else:
            pieces.append(_blank(span))
        done = end
    pieces.append(text[done:])
    return "".join(pieces)


# ---------------------------------------------------------------------------
# Markdown and MDX.
# ---------------------------------------------------------------------------

_ATTRIBUTE = re.compile(
    r"""([A-Za-z_:][\w.:-]*)\s*=\s*("[^"]*"|'[^']*'|\{\s*(?:"[^"]*"|'[^']*')\s*\})"""
)
#: The attributes of a tag whose value is code, never text: every other
#: attribute a reader may see (``legend``, ``label``, ``note``) is read.
_CODE_ATTRIBUTES = frozenset(
    {"class", "classname", "style", "href", "src", "srcset", "sizes", "id", "slug"}
    | {"d", "points", "viewbox", "transform", "lang", "type", "name", "key", "ref"}
    | {"width", "height", "loading", "decoding", "target", "rel", "for", "role"}
    | {"fill", "stroke", "stroke-dasharray", "x", "y", "cx", "cy", "r", "media"}
    | {"catalogue", "file", "path", "url", "icon", "variant", "lazy", "poster"}
)
#: The languages of a fence whose ``#`` comments are prose.
_HASH_COMMENT_FENCES = frozenset(
    {"python", "py", "pycon", "bash", "sh", "shell", "console", "toml", "yaml", "ini"}
)
#: The languages of a fence read as a Python module, its strings among it.
_PYTHON_FENCES = frozenset({"python", "py"})
#: The languages of a fence read as a script, its strings and comments.
_SCRIPT_FENCES = frozenset(
    {"js", "javascript", "mjs", "ts", "typescript", "jsx", "tsx", "json", "jsonc"}
)
#: The languages of a fence read as a page.
_MARKDOWN_FENCES = frozenset({"markdown", "md", "mdx", "text", "txt", "plaintext"})
#: A field of an errata entry, ``- **The print:**``, and what it is named.
_ERRATA_FIELD = re.compile(r"^(\s*)[-*+]\s+\*\*([^*]+?)\*\*")
#: The fields of an errata entry that transcribe the print.
_PRINT_FIELD = re.compile(r"^(?:The print|As printed|Printed)\b", re.IGNORECASE)
#: A line that opens an item of a list.
_ITEM = re.compile(r"^\s*(?:[-*+]|\d{1,9}[.)])(?:\s|$)")
#: A header of the conformance report's column that transcribes the print.
_PRINTED_COLUMN = re.compile(r"\b(?:expected|printed)\b", re.IGNORECASE)
#: How a block quote of ours opens: on an admonition (``[!NOTE]``), a bold
#: label (``**Note.**``), an emphasised one (``*Tip.*``) or a label word
#: (``Note:``). A print's own note opens on ``NOTE 1``, in capitals, and stays
#: a transcription.
_NOTE_OF_OURS = re.compile(
    r"\[!|\*\*|__"
    r"|[*_][A-Z][\w ]{0,30}[.:][*_](?:\s|$)"
    r"|(?:Note|Notes|Tip|Hint|Warning|Caution|Important|Example|Remark|Aside)"
    r"[.:](?:\s|$)"
)
#: The kinds of line that hold no prose.
_CODE_ROLES = frozenset({"open", "body", "close", "indented"})


def _tag_text(tag: str) -> str:
    """*tag* blanked but for the values of the attributes a reader sees.

    A value is read whether it is quoted or a string expression
    (``caption={"..."}``); only the attributes that hold code are not.
    """
    shown = list(_blank(tag))
    for match in _ATTRIBUTE.finditer(tag):
        name = match.group(1).lower()
        if name in _CODE_ATTRIBUTES or name.startswith(("data-", "on", "client:")):
            continue
        value = match.group(2)
        start = match.start(2) + 1
        end = match.end(2) - 1
        if value.startswith("{"):
            inner = re.search(r"([\"'])(.*)\1", value, re.DOTALL)
            if inner is None:
                continue
            start, end = match.start(2) + inner.start(2), match.start(2) + inner.end(2)
        shown[start:end] = tag[start:end]
    return "".join(shown)


#: A string literal inside an expression of a page; a template literal builds
#: its text from code, a class name or a path, and is code.
_EXPRESSION_STRING = re.compile(r"\"((?:[^\"\\\n]|\\.)*)\"|'((?:[^'\\\n]|\\.)*)'")


def _expression_text(span: str) -> str:
    """An expression of a page blanked but for the text of its string literals."""
    shown = list(_blank(span))
    for match in _EXPRESSION_STRING.finditer(span):
        group = 1 if match.group(1) is not None else 2
        start, end = match.start(group), match.end(group)
        shown[start:end] = span[start:end]
    return "".join(shown)


def _shown(span: str) -> str:
    """What a span, a comment, a tag or an expression of a page leaves to read."""
    if span.startswith("`"):
        return span if _formula_span(span) else _blank(span)
    if span.startswith(("$", "<!--")) or re.match(r"\{\s*/\*", span):
        return span  # maths and comments are text
    if span.startswith("<"):
        return _tag_text(span)
    return _expression_text(span)  # an MDX expression: its strings are text


def _frontmatter_end(lines: Sequence[str]) -> int:
    """How many lines the frontmatter of a page takes, its fences included."""
    if not lines or lines[0].strip() != "---":
        return 0
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return index + 1
    return 0


@dataclass
class _Unit:
    """The lines of one unit of a page: a paragraph, an item, a heading."""

    first: int
    lines: list[str]
    transcription: bool


def _dont_example(lines: Sequence[str], index: int) -> bool:
    """Whether the fence opening at *index* is the Don't example of a rule."""
    for back in range(index - 1, -1, -1):
        if lines[back].strip():
            return lines[back].strip() == "**Don't**"
    return False


def _hash_comment(line: str) -> int | None:
    """Where the ``#`` comment of a line of code opens, outside its quotes."""
    quote: str | None = None
    for index, char in enumerate(line):
        if quote:
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif char == "#" and (index == 0 or line[index - 1] in " \t"):
            return index
    return None


def _fence_comments(
    out: list[Finding], rel: str, lines: Sequence[str], walked: Sequence[PageLine]
) -> None:
    """Read the text a fence writes, as its language writes it.

    A Python fence is read as a module, its strings and comments with their
    roles; a fence of a script language by its comments and strings; a
    Markdown fence and a fence of plain text as a page, since the text a
    program of this library prints writes the point too and an example of the
    contributor guide is prose; the other languages by their ``#`` comments.
    The Don't example of a rule is a mistake on purpose, and is not read.
    """
    language = ""
    skip = False
    body: list[tuple[int, str]] = []
    for index, read in enumerate(walked):
        if read.role == "open":
            words = read.info.split(maxsplit=1)
            language = words[0].lower() if words else ""
            skip = _dont_example(lines, index)
            body = []
        elif read.role == "body":
            body.append(
                (index, read.inner.rstrip("\n") if read.inner else lines[index])
            )
        elif read.role == "close" and body and not skip:
            _fence_body(out, rel, language, body)
            body = []


def _fence_body(
    out: list[Finding], rel: str, language: str, body: Sequence[tuple[int, str]]
) -> None:
    """Read the body of one fence, each line at its line of the page."""
    first = body[0][0]
    padded = "\n" * first + "\n".join(text for _, text in body)
    if language in _PYTHON_FENCES and _python(out, rel, padded, fence=True):
        return
    if language in _SCRIPT_FENCES:
        _ScriptReader(rel, padded, out, strings=True, printed_file=False).read()
        return
    if language in _MARKDOWN_FENCES:
        kind = "md" if language in ("markdown", "md") else "mdx"
        _markdown(out, rel, padded, kind, errata=True)
        return
    if language not in _HASH_COMMENT_FENCES:
        return
    for index, text in body:
        at = _hash_comment(text)
        if at is not None:
            comment = _blank(text[: at + 1]) + _blank_code_spans(text[at + 1 :])
            _scan(out, rel, comment, "fence comment", _on_line(index + 1))


def _table_cells(
    out: list[Finding],
    rel: str,
    row: str,
    number: int,
    header: list[str],
    *,
    transcription: bool,
) -> None:
    """Read the cells of a row of a table, but those of a printed column."""
    pieces = [row[start:end] for start, end in cell_spans(row.strip())]
    if pieces and not pieces[0].strip():
        pieces = pieces[1:]
    for column, cell in enumerate(pieces):
        name = header[column] if column < len(header) else ""
        printed = rel.endswith("CONFORMANCE.md") and _PRINTED_COLUMN.search(name)
        if transcription or printed:
            continue
        _scan(out, rel, cell, "table cell", _on_line(number))


def _markdown(
    out: list[Finding], rel: str, text: str, kind: str, *, errata: bool = False
) -> None:
    """Read a Markdown or MDX page by its structure.

    :param errata: Whether the page may hold entries of the errata registry,
        whose print field is a transcription: the registry and its pages, and
        a Markdown fence that shows one.
    """
    lines = text.split("\n")
    front = _frontmatter_end(lines)
    for index in range(1, max(front - 1, 1)):
        value = re.sub(r"^\s*(?:-\s+)?(?:[\w$-]+\s*:\s*)?", "", lines[index])
        _scan(out, rel, value, "frontmatter", _on_line(index + 1))
    body = [""] * front + lines[front:]
    walked = list(page_lines(body, kind=kind))
    _fence_comments(out, rel, body, walked)
    prose = [
        "" if read.role in _CODE_ROLES else line
        for line, read in zip(body, walked, strict=True)
    ]
    constructs = [MDX_TAG, MDX_EXPRESSION] if kind == "mdx" else [MDX_TAG]
    shown = replace_inline_spans_by_block(
        "\n".join(prose),
        _shown,
        "`$",
        kind,
        kind=kind,
        walked=walked,
        constructs=constructs,
    ).split("\n")
    errata = errata or rel == "docs/ERRATA.md" or "/reference/errata/" in rel
    field_name, field_indent = "", -1
    header: list[str] = []
    callout = False
    unit: _Unit | None = None
    units: list[_Unit] = []

    def flush() -> None:
        nonlocal unit
        if unit is not None:
            units.append(unit)
            unit = None

    for index in range(front, len(body)):
        raw, read, line = body[index], walked[index], shown[index]
        if errata:
            opened = _ERRATA_FIELD.match(raw)
            if opened:
                field_name, field_indent = opened.group(2), len(opened.group(1))
            elif (
                raw.lstrip().startswith("#")
                or raw.strip() == "---"
                or _ITEM.match(raw)
                and len(raw) - len(raw.lstrip()) <= field_indent
            ):
                field_name, field_indent = "", -1
        in_print = bool(errata and _PRINT_FIELD.match(field_name))
        depth, inner = quotation_marks(raw, kind=kind)
        if depth == 0:
            callout = False
        elif index == front or quotation_marks(body[index - 1], kind=kind)[0] == 0:
            callout = _NOTE_OF_OURS.match(inner.lstrip()) is not None
        quoted = depth > 0 and not callout
        if read.role in _CODE_ROLES or read.role == "blank" or not line.strip():
            flush()
            if read.role != "row":
                header = []
            continue
        if read.role == "row":
            flush()
            if not header:
                header = [
                    raw.strip()[start:end].strip()
                    for start, end in cell_spans(raw.strip())
                ]
                if header and not header[0]:
                    header = header[1:]
                _table_cells(
                    out, rel, line, index + 1, [], transcription=in_print or quoted
                )
                continue
            if re.fullmatch(r"[\s|:\-]+", raw):
                continue
            _table_cells(
                out, rel, line, index + 1, header, transcription=in_print or quoted
            )
            continue
        header = []
        starts = (
            unit is None
            or read.role in ("paragraph", "heading", "single", "html")
            or _ITEM.match(raw) is not None
            or (errata and _ERRATA_FIELD.match(raw) is not None)
        )
        if starts:
            flush()
            unit = _Unit(index + 1, [line], in_print or quoted)
        elif unit is not None:
            unit.lines.append(line)
    flush()
    for each in units:
        if each.transcription:
            continue
        joined = "\n".join(each.lines)
        _scan(out, rel, joined, "prose", _line_counter(each.first, joined))


# ---------------------------------------------------------------------------
# Python.
# ---------------------------------------------------------------------------

#: The functions whose arguments are regular expressions.
_REGEX_FUNCTIONS = frozenset(
    {"compile", "search", "match", "fullmatch", "findall", "finditer", "sub"}
    | {"subn", "split", "escape"}
)
#: The string methods whose arguments are characters to look for, not text.
_STRING_METHODS = frozenset(
    {"replace", "split", "rsplit", "strip", "lstrip", "rstrip", "startswith"}
    | {"endswith", "find", "rfind", "index", "count", "partition", "removeprefix"}
    | {"removesuffix"}
)
#: The keywords whose value is a regular expression.
_PATTERN_KEYWORDS = frozenset({"match", "pattern", "regex"})
#: The keywords and names of the conformance rows that transcribe the print.
_PRINTED_NAMES = frozenset({"expected", "printed", "expected_text", "printed_text"})
#: A name that says it holds Spanish.
_SPANISH_NAME = re.compile(r"(?:^|_)(?:es|ES|spanish|Spanish|SPANISH)(?:_|$)")
#: The reStructuredText directives whose body is code.
_CODE_DIRECTIVES = frozenset(
    {"code", "code-block", "sourcecode", "doctest", "testcode", "testoutput"}
    | {"literalinclude", "highlight", "plot"}
)
#: The calls of the figure and plate code that draw the text handed to them.
_TEXT_CALLS = frozenset(
    {"text", "tspan", "label", "title", "caption", "annotate", "set_text", "note"}
    | {"chip", "set_title", "set_xlabel", "set_ylabel", "suptitle", "heading"}
)
#: The keywords that hand a call the text it draws.
_TEXT_KEYWORDS = frozenset({"text", "label", "title", "caption", "s"})
#: How many pairs a dictionary holds before its values make a table.
_TABLE_PAIRS = 3


def _spanish_key(key: str) -> bool:
    """Whether a key or a keyword names the Spanish of what it holds."""
    return key in ("es", "es-ES", "spanish") or key.endswith(("Es", "_es", "_ES"))


def _language_test(test: ast.expr) -> str | None:
    """``"es"`` when *test* holds for Spanish, ``"not-es"`` when it fails for it."""
    if isinstance(test, ast.Compare) and len(test.ops) == 1:
        sides = [test.left, *test.comparators]
        spanish = any(
            isinstance(side, ast.Constant) and side.value == "es" for side in sides
        )
        if spanish and isinstance(test.ops[0], ast.Eq | ast.Is):
            return "es"
        if spanish and isinstance(test.ops[0], ast.NotEq | ast.IsNot):
            return "not-es"
    if (
        isinstance(test, ast.Call)
        and isinstance(test.func, ast.Attribute)
        and test.func.attr == "startswith"
        and test.args
        and isinstance(test.args[0], ast.Constant)
        and test.args[0].value == "es"
    ):
        return "es"
    return None


def _target_names(node: ast.Assign | ast.AnnAssign) -> list[str]:
    """The names an assignment binds, by name or by attribute."""
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    names: list[str] = []
    for target in targets:
        for part in ast.walk(target):
            if isinstance(part, ast.Name):
                names.append(part.id)
            elif isinstance(part, ast.Attribute):
                names.append(part.attr)
    return names


def _dash_default(arguments: ast.arguments, default: ast.AST) -> bool:
    """Whether *default* is the default value of a parameter named for a dash pattern."""
    positional = [*arguments.posonlyargs, *arguments.args]
    pairs = list(
        zip(
            positional[len(positional) - len(arguments.defaults) :],
            arguments.defaults,
            strict=True,
        )
    )
    pairs += [
        (arg, value)
        for arg, value in zip(arguments.kwonlyargs, arguments.kw_defaults, strict=True)
        if value is not None
    ]
    return any(value is default and "dash" in arg.arg for arg, value in pairs)


def _call_name(func: ast.expr) -> tuple[str, str]:
    """The receiver and the name of a call: ``("re", "compile")``."""
    if isinstance(func, ast.Attribute):
        owner = func.value.id if isinstance(func.value, ast.Name) else ""
        return owner, func.attr
    if isinstance(func, ast.Name):
        return "", func.id
    return "", ""


def _is_str(node: ast.AST | None) -> bool:
    """Whether *node* is a string literal."""
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def _str_value(node: ast.AST | None) -> str | None:
    """The text of a string literal, or ``None`` for any other node."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


class _Roles:
    """What each string literal of a module is: a docstring, Spanish, code or text."""

    def __init__(self, tree: ast.Module, *, conformance: bool) -> None:
        self.parents: dict[int, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                self.parents[id(child)] = node
        self.conformance = conformance
        self.spanish_tables: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                values = [
                    text
                    for key, value in zip(node.keys, node.values, strict=True)
                    if _is_str(key) and (text := _str_value(value)) is not None
                ]
                spanish = sum(reads_as_spanish(value) for value in values)
                english = sum(_reads_as_english(value) for value in values)
                if len(values) >= _TABLE_PAIRS and spanish > english:
                    self.spanish_tables.add(id(node))

    def role(self, node: ast.AST) -> str:
        """``"docstring"``, ``"spanish"``, ``"code"``, ``"printed"`` or ``"text"``."""
        parent = self.parents.get(id(node))
        if isinstance(parent, ast.Expr):
            return "docstring"
        child: ast.AST = node
        in_key = False
        while parent is not None:
            found = self._step(parent, child, in_key=in_key)
            if found is not None:
                return found
            if isinstance(parent, ast.Dict) and any(
                key is child for key in parent.keys
            ):
                in_key = True
            child, parent = parent, self.parents.get(id(parent))
        return "text"

    def _step(self, parent: ast.AST, child: ast.AST, *, in_key: bool) -> str | None:
        """What *parent* makes of the literal held under *child*, if anything."""
        if isinstance(parent, ast.Dict):
            return self._in_dict(parent, child)
        if isinstance(parent, ast.keyword) and parent.arg:
            if _spanish_key(parent.arg):
                return "spanish"
            if parent.arg in _PATTERN_KEYWORDS or "dash" in parent.arg:
                return "code"
            if self.conformance and parent.arg in _PRINTED_NAMES:
                return "printed"
        if isinstance(parent, ast.arguments) and _dash_default(parent, child):
            return "code"
        if isinstance(parent, ast.Call) and any(arg is child for arg in parent.args):
            owner, name = _call_name(parent.func)
            if owner in ("re", "regex") and name in _REGEX_FUNCTIONS:
                return "code"
            if name in _STRING_METHODS and owner != "":
                return "code"
        if isinstance(parent, ast.IfExp | ast.If):
            return self._in_branch(parent, child)
        if isinstance(parent, ast.Assign | ast.AnnAssign):
            names = _target_names(parent)
            if not in_key and any(_SPANISH_NAME.search(name) for name in names):
                return "spanish"
            if (
                self.conformance
                and not in_key
                and any(
                    part in name.lower()
                    for name in names
                    for part in ("printed", "expected")
                )
            ):
                return "printed"
        if isinstance(parent, ast.Subscript) and parent.slice is child:
            return "code"
        if isinstance(parent, ast.Compare):
            return "code"
        return None

    def drawn(self, node: ast.AST) -> bool:
        """Whether *node* is handed straight to a call that draws text."""
        parent = self.parents.get(id(node))
        if isinstance(parent, ast.keyword):
            return parent.arg in _TEXT_KEYWORDS
        if not isinstance(parent, ast.Call):
            return False
        _, name = _call_name(parent.func)
        return name in _TEXT_CALLS and any(arg is node for arg in parent.args)

    def _in_dict(self, parent: ast.Dict, child: ast.AST) -> str | None:
        """What a dictionary makes of the value it holds under *child*."""
        for key, value in zip(parent.keys, parent.values, strict=True):
            if value is not child:
                continue
            name = _str_value(key) or ""
            if _spanish_key(name) or id(parent) in self.spanish_tables:
                return "spanish"
            if self.conformance and name in _PRINTED_NAMES:
                return "printed"
        return None

    @staticmethod
    def _in_branch(parent: ast.IfExp | ast.If, child: ast.AST) -> str | None:
        """``"spanish"`` when *child* is the branch a Spanish language takes."""
        language = _language_test(parent.test)
        if language is None:
            return None
        body = parent.body if isinstance(parent.body, list) else [parent.body]
        orelse = parent.orelse if isinstance(parent.orelse, list) else [parent.orelse]
        if language == "es" and any(each is child for each in body):
            return "spanish"
        if language == "not-es" and any(each is child for each in orelse):
            return "spanish"
        return None


@dataclass
class _Literal:
    """A string literal of a module, its pieces joined, with the line of each."""

    node: ast.AST
    text: str = ""
    starts: list[int] = field(default_factory=list)
    lines: list[int] = field(default_factory=list)

    def add(self, piece: str, line: int) -> None:
        """Join one piece written on *line*."""
        self.starts.append(len(self.text))
        self.lines.append(line)
        self.text += piece

    def line_of(self, pos: int) -> int:
        """The line of the character at *pos*."""
        index = max(bisect.bisect_right(self.starts, pos) - 1, 0)
        start = self.starts[index] if self.starts else 0
        first = self.lines[index] if self.lines else 1
        return first + self.text.count("\n", start, pos)


#: The prefix of a string literal, and an escaped line end in its body.
_PREFIX = re.compile(r"^[A-Za-z]*")
_ESCAPED_LINE_END = re.compile(r"(?<!\\)((?:\\\\)*)\\n")


def _decoded(source: str) -> str | None:
    r"""The text of one string literal as written in *source*, its fields marked.

    An escaped line end (``\\n``) is read as a blank, so that every line end
    of the text is one of the source and the lines counted in it are the
    lines the literal is written on.
    """
    source = source.strip()
    prefix = _PREFIX.match(source)
    if prefix is None or "r" not in prefix.group().lower():
        source = _ESCAPED_LINE_END.sub(r"\1 ", source)
    try:
        node = ast.parse(source, mode="eval").body
    except SyntaxError:
        return None
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bytes):
            return node.value.decode("utf-8", "replace")
        return node.value if isinstance(node.value, str) else None
    if isinstance(node, ast.JoinedStr):
        return "".join(
            str(part.value) if isinstance(part, ast.Constant) else MARK
            for part in node.values
        )
    return None


def _string_pieces(
    text: str,
) -> tuple[list[tuple[int, int, str, int]], list[tokenize.TokenInfo]]:
    """Every string literal piece of a module, and its comments, by its tokens.

    :return: For each piece its start and end as offsets of *text*, its
        decoded text and its first line; and the comment tokens.
    """
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))

    def at(position: tuple[int, int]) -> int:
        return offsets[position[0] - 1] + position[1]

    pieces: list[tuple[int, int, str, int]] = []
    comments: list[tokenize.TokenInfo] = []
    depth = 0
    opening = (0, 0)
    fstring_start = getattr(tokenize, "FSTRING_START", -1)
    fstring_end = getattr(tokenize, "FSTRING_END", -1)
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type == fstring_start:
            if depth == 0:
                opening = token.start
            depth += 1
        elif token.type == fstring_end:
            depth -= 1
            if depth == 0:
                start, end = at(opening), at(token.end)
                decoded = _decoded(text[start:end])
                if decoded is not None:
                    pieces.append((start, end, decoded, opening[0]))
        elif token.type == tokenize.STRING and depth == 0:
            decoded = _decoded(token.string)
            if decoded is not None:
                pieces.append((at(token.start), at(token.end), decoded, token.start[0]))
        elif token.type == tokenize.COMMENT:
            comments.append(token)
    return pieces, comments


def _char_offset(text: str, offsets: Sequence[int], line: int, column: int) -> int:
    """The offset in *text* of a node's position, whose column counts UTF-8 bytes."""
    start = offsets[line - 1]
    end = offsets[line] if line < len(offsets) else len(text)
    written = text[start:end].encode("utf-8")[:column]
    return start + len(written.decode("utf-8", "ignore"))


def _module_literals(
    text: str, tree: ast.Module
) -> tuple[list[_Literal], list[tokenize.TokenInfo]]:
    """Every string literal of a module with its text and lines, and its comments.

    A literal is a node of the tree, a string or an f-string, and its text is
    read from its tokens, a piece for each part an implicit concatenation
    joins, so that each piece keeps the line it is written on. A string inside
    the replacement field of an f-string is code, and is no literal of its own.
    """
    nodes: list[ast.expr] = []
    pending: list[ast.AST] = [tree]
    while pending:
        node = pending.pop()
        if isinstance(node, ast.JoinedStr) or (
            isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes))
        ):
            nodes.append(node)
            continue  # what an f-string holds is no literal of its own
        pending.extend(ast.iter_child_nodes(node))
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    spans = sorted(
        (
            _char_offset(text, offsets, node.lineno, node.col_offset),
            _char_offset(
                text,
                offsets,
                node.end_lineno or node.lineno,
                node.end_col_offset or node.col_offset,
            ),
            index,
        )
        for index, node in enumerate(nodes)
    )
    starts = [start for start, _, _ in spans]
    literals = {index: _Literal(nodes[index]) for _, _, index in spans}
    pieces, comments = _string_pieces(text)
    for start, end, decoded, first_line in pieces:
        at = bisect.bisect_right(starts, start) - 1
        if at < 0 or end > spans[at][1]:
            continue
        literals[spans[at][2]].add(decoded, first_line)
    return [literals[index] for _, _, index in spans], comments


def _rst_prose(doc: str) -> str:
    """A docstring with its code blanked: doctests, literal blocks, code directives
    and inline literals, every line kept. A ``#`` comment of a doctest is prose,
    and so is the maths of ``:math:`` and of ``.. math::``.
    """
    out: list[str] = []
    code_indent: int | None = None
    doctest = False
    for line in doc.split("\n"):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if code_indent is not None:
            if not stripped or indent > code_indent:
                out.append(_blank(line))
                continue
            code_indent = None
        if doctest and not stripped:
            doctest = False
        if stripped.startswith((">>>", "... ")) or (doctest and stripped == "..."):
            doctest = True
            at = _hash_comment(line)
            out.append(_blank(line) if at is None else _blank(line[:at]) + line[at:])
            continue
        if doctest:
            out.append(_blank(line))
            continue
        directive = re.match(r"\s*\.\.\s+([\w-]+)::", line)
        if directive and directive.group(1) in _CODE_DIRECTIVES:
            code_indent = indent
            out.append(_blank(line))
            continue
        if stripped.endswith("::") and not directive:
            code_indent = indent
        out.append(line)
    paragraphs = "\n".join(out).split("\n\n")
    return "\n\n".join(_blank_code_spans(each, roles=True) for each in paragraphs)


def _comment_groups(
    comments: Sequence[tokenize.TokenInfo],
) -> Iterable[tuple[int, str]]:
    """The comments of a module, the comments of consecutive lines joined."""
    group: list[tokenize.TokenInfo] = []
    for token in comments:
        if group and token.start[0] != group[-1].start[0] + 1:
            yield group[0].start[0], "\n".join(t.string[1:] for t in group)
            group = []
        group.append(token)
    if group:
        yield group[0].start[0], "\n".join(t.string[1:] for t in group)


#: A string that is nothing but whole numbers and the commas between them,
#: which the plates' SVG writer takes as a dash pattern: “6,4”, ``"9,4,2,4"``.
_DASH_PATTERN = re.compile(r"[1-9][0-9]*(?:,[1-9][0-9]*)+")


#: A row of a delimited file: three separators or more, ``;`` or a tab.
_DELIMITED_ROW = re.compile(r"^[^;\t\n]*(?:[;\t][^;\t\n]*){3,}$")


def _csv_rows(text: str) -> bool:
    """Whether every line of *text* is a row of a delimited file."""
    rows = [line for line in text.split("\n") if line.strip()]
    return bool(rows) and all(_DELIMITED_ROW.match(line) for line in rows)


def _python(out: list[Finding], rel: str, text: str, *, fence: bool = False) -> bool:
    """Read a Python module by its tokens and its tree; whether it parses.

    :param fence: Whether *text* is a fence of a page, whose strings are text
        however the page is named.
    """
    try:
        tree = ast.parse(text)
        literals, comments = _module_literals(text, tree)
    except (SyntaxError, tokenize.TokenError, ValueError):
        return False
    test_file = not fence and (rel.startswith("tests/") or "/tests/" in rel)
    svg_writer = rel.startswith("scripts/diagrams/")
    roles = _Roles(tree, conformance=rel.startswith("scripts/conformance/"))
    for literal in literals:
        role = roles.role(literal.node)
        if role == "docstring":
            prose = _rst_prose(literal.text)
            for paragraph, offset in _paragraphs(prose):
                _scan(
                    out,
                    rel,
                    paragraph,
                    "docstring",
                    _shifted(literal.line_of, offset),
                )
        elif role == "text" and not test_file:
            if (
                svg_writer
                and _DASH_PATTERN.fullmatch(literal.text)
                and not roles.drawn(literal.node)
            ):
                continue  # a dash pattern of the plates' SVG: "6,4"
            if _csv_rows(literal.text):
                continue  # the rows of a CSV file the code writes: data
            _scan(out, rel, _blank_code_spans(literal.text), "string", literal.line_of)
    for first, comment in _comment_groups(comments):
        _scan(
            out,
            rel,
            _blank_code_spans(comment),
            "comment",
            _line_counter(first, comment),
        )
    return True


def _shifted(line_of: Callable[[int], int], offset: int) -> Callable[[int], int]:
    """*line_of* read *offset* characters further on."""
    return lambda pos: line_of(offset + pos)


def _paragraphs(text: str) -> Iterable[tuple[str, int]]:
    """The paragraphs of *text* with the offset each opens at."""
    at = 0
    for paragraph in text.split("\n\n"):
        yield paragraph, at
        at += len(paragraph) + 2


# ---------------------------------------------------------------------------
# JavaScript, TypeScript and JSON.
# ---------------------------------------------------------------------------

#: The keys whose value is code, not text.
_CODE_KEYS = frozenset(
    {"pattern", "regex", "href", "src", "d", "points", "viewBox", "transform"}
    | {"path", "url", "className", "class", "id", "slug", "key", "style", "$id"}
    | {"$ref", "format", "fill", "stroke", "srcset", "sizes"}
)
#: The keys of a catalogue row whose values are printed labels of the row.
_LABEL_KEYS = frozenset(
    {"name", "group", "variant", "mounting", "heading", "per", "model"}
    | {"direction", "shape", "gauge", "weave", "bonding"}
)
#: What a ``/`` after it opens: a regular expression, not a division.
_REGEX_AFTER = frozenset("(,=:[!&|?{};+-*%<>~^")
#: The words after which a ``/`` opens a regular expression.
_REGEX_WORDS = frozenset({"return", "typeof", "case", "in", "of", "delete", "void"})


#: An escape of a JavaScript or JSON string.
_ESCAPE = re.compile(
    r"\\(?:u\{([0-9A-Fa-f]+)\}|u([0-9A-Fa-f]{4})|x([0-9A-Fa-f]{2})|(.))", re.DOTALL
)
_SIMPLE_ESCAPES = {"n": "\n", "t": "\t", "r": "", "b": "", "f": "", "v": "", "0": ""}


def _unescape(body: str) -> str:
    """The text a JavaScript or JSON string literal writes, *body* between its quotes."""

    def one(match: re.Match[str]) -> str:
        code = match.group(1) or match.group(2) or match.group(3)
        if code:
            return chr(int(code, 16))
        char = match.group(4)
        return _SIMPLE_ESCAPES.get(char, char)

    return _ESCAPE.sub(one, body)


@dataclass
class _Frame:
    """An object or an array open in a JavaScript or JSON text."""

    key: str
    object: bool
    labels: list[tuple[str, int]] = field(default_factory=list)


#: A word of a script, and the colon that makes the word or string before it a key.
_JS_WORD = re.compile(r"[A-Za-z_$][\w$]*")
_JS_KEY_COLON = re.compile(r"\s*:(?!:)")


@dataclass
class _ScriptReader:
    """One pass over a JavaScript, TypeScript or JSON text."""

    rel: str
    text: str
    out: list[Finding]
    strings: bool
    printed_file: bool
    spanish_edition: bool = False
    frames: list[_Frame] = field(default_factory=list)
    key: str = ""
    previous: str = ""
    breaks: list[int] = field(default_factory=list)

    def line(self, pos: int) -> int:
        """The line of *pos*."""
        return bisect.bisect_left(self.breaks, pos) + 1

    def read(self) -> None:
        """Walk the text once."""
        text, at = self.text, 0
        self.breaks = [index for index, char in enumerate(text) if char == "\n"]
        self.spanish_edition = "Spanish edition" in text[:20000]
        while at < len(text):
            char = text[at]
            if text.startswith("//", at):
                end = text.find("\n", at)
                end = len(text) if end < 0 else end
                self.comment(text[at + 2 : end], at + 2)
                at = end
            elif text.startswith("/*", at):
                end = text.find("*/", at + 2)
                end = len(text) if end < 0 else end
                self.comment(text[at + 2 : end], at + 2)
                at = end + 2
            elif char in "'\"":
                at = self.quoted(at, char)
            elif char == "`":
                at = self.template(at)
            elif char == "/" and (
                self.previous in _REGEX_AFTER
                or self.previous in _REGEX_WORDS
                or not self.previous
            ):
                at = self.skip_regex(at)
            else:
                at = self.punctuation(at)

    def punctuation(self, at: int) -> int:
        """Read the punctuation and the words between literals."""
        char = self.text[at]
        word = _JS_WORD.match(self.text, at)
        if word:
            self.previous = word.group()
            if _JS_KEY_COLON.match(self.text, word.end()):
                self.key = word.group()
            return word.end()
        if char in "{[":
            self.frames.append(
                _Frame(
                    self.key if self.previous == ":" else self.inherited(), char == "{"
                )
            )
            self.key = ""
        elif char in "}]":
            if self.frames:
                self.close(self.frames.pop())
            self.key = ""
        elif char == ",":
            self.key = "" if self.frames and self.frames[-1].object else self.key
        if not char.isspace():
            self.previous = char
        return at + 1

    def inherited(self) -> str:
        """The key of the frame an array item stands in."""
        return self.frames[-1].key if self.frames else ""

    def keys(self) -> list[str]:
        """Every key that holds the current position."""
        return [frame.key for frame in self.frames] + [self.key]

    def quoted(self, at: int, quote: str) -> int:
        """Read a string literal; the position after it."""
        end = at + 1
        text = self.text
        while end < len(text) and text[end] != quote and text[end] != "\n":
            end += 2 if text[end] == "\\" else 1
        raw = text[at : end + 1]
        is_key = _JS_KEY_COLON.match(text, end + 1) is not None
        value = _unescape(raw[1:-1])
        if is_key:
            self.key = value
        else:
            self.value(value, at + 1)
        self.previous = "string"
        return end + 1

    def template(self, at: int) -> int:
        """Read a template literal, its expressions marked; the position after it."""
        text = self.text
        end = at + 1
        pieces: list[str] = []
        while end < len(text) and text[end] != "`":
            if text[end] == "\\":
                pieces.append(text[end : end + 2])
                end += 2
            elif text.startswith("${", end):
                depth = 1
                end += 2
                while end < len(text) and depth:
                    depth += {"{": 1, "}": -1}.get(text[end], 0)
                    end += 1
                pieces.append(MARK)
            else:
                pieces.append(text[end])
                end += 1
        self.value("".join(pieces), at + 1)
        self.previous = "string"
        return end + 1

    def skip_regex(self, at: int) -> int:
        """Step over a regular expression literal."""
        text = self.text
        end = at + 1
        klass = False
        while end < len(text) and text[end] != "\n":
            if text[end] == "\\":
                end += 2
                continue
            if text[end] == "[":
                klass = True
            elif text[end] == "]":
                klass = False
            elif text[end] == "/" and not klass:
                break
            end += 1
        self.previous = "regex"
        return end + 1

    def comment(self, body: str, at: int) -> None:
        """Read a comment."""
        first = self.line(at)
        lines = [re.sub(r"^\s*\*", "", line) for line in body.split("\n")]
        joined = _blank_code_spans("\n".join(lines))
        _scan(self.out, self.rel, joined, "comment", _line_counter(first, joined))

    def value(self, value: str, at: int) -> None:
        """Read a string value under the keys that hold it."""
        if not self.strings:
            return
        keys = self.keys()
        if any(_spanish_key(key) for key in keys) or keys[-1] in _CODE_KEYS:
            return
        if self.printed_file and "expected" in keys:
            return
        if keys[-1] in _LABEL_KEYS and self.frames and self.frames[-1].object:
            self.frames[-1].labels.append((value, at))
            return
        _scan(
            self.out,
            self.rel,
            _blank_code_spans(value),
            "string",
            _on_line(self.line(at)),
        )

    def close(self, frame: _Frame) -> None:
        """Read the labels of a closed object, unless one reads as Spanish."""
        if self.spanish_edition or any(
            reads_as_spanish(value) for value, _ in frame.labels
        ):
            return
        for value, at in frame.labels:
            _scan(self.out, self.rel, value, "string", _on_line(self.line(at)))


def _script(out: list[Finding], rel: str, text: str) -> None:
    """Read a JavaScript, TypeScript or JSON text by its literals and their keys."""
    name = rel.rsplit("/", 1)[-1]
    test = re.search(r"\.(?:test|spec)\.[cm]?[jt]sx?$", name) is not None
    _ScriptReader(
        rel,
        text,
        out,
        strings=not test,
        printed_file="conformance" in rel,
    ).read()


def _astro(out: list[Finding], rel: str, text: str) -> None:
    """Read an Astro component: its script as JavaScript, its template as MDX."""
    lines = text.split("\n")
    front = _frontmatter_end(lines)
    script = "\n".join(lines[:front])
    _script(out, rel, script)
    template = "\n" * max(front - 1, 0) + "\n".join(lines[front:]) if front else text
    blocks = re.compile(r"<(script|style)\b[^>]*>(.*?)</\1>", re.DOTALL)
    for block in blocks.finditer(template):
        if block.group(1) == "script":
            padded = "\n" * template.count("\n", 0, block.start(2)) + block.group(2)
            _script(out, rel, padded)
    template = blocks.sub(lambda m: "\n" * m.group().count("\n"), template)
    _markdown(out, rel, template, "mdx")


# ---------------------------------------------------------------------------
# Configuration files and notebooks.
# ---------------------------------------------------------------------------


def _hash_comments(out: list[Finding], rel: str, text: str) -> None:
    """Read the ``#`` comments of a configuration file, consecutive lines joined."""
    group: list[tuple[int, str]] = []

    def flush() -> None:
        if group:
            joined = "\n".join(comment for _, comment in group)
            _scan(
                out,
                rel,
                _blank_code_spans(joined),
                "comment",
                _line_counter(group[0][0], joined),
            )
            group.clear()

    for number, line in enumerate(text.split("\n"), start=1):
        at = _hash_comment(line)
        if at is None:
            flush()
            continue
        if group and group[-1][0] != number - 1:
            flush()
        group.append((number, line[at + 1 :]))
    flush()


#: A value a reader sees in a configuration file: the name, title or
#: description of a workflow, a step, a package or a citation, and a line a
#: Makefile recipe or a shell script prints.
_CONFIG_VALUE = re.compile(
    r"""^\s*(?:-\s+)?(?:name|description|summary|title|abstract|message|help)\s*[:=]\s*(.+)$"""
)
_PRINTED_LINE = re.compile(r"^\s*@?(?:echo|printf)\b(.*)$")
#: A field of a BibTeX entry whose value is prose.
_BIB_FIELD = re.compile(
    r"^\s*(?:title|note|abstract|annote|howpublished|booktitle)\s*=\s*[{\"](.*)[}\"],?\s*$"
)
#: A quoted stretch of a printed line.
_QUOTED_ARGUMENT = re.compile(r"\"((?:[^\"\\]|\\.)*)\"|'([^']*)'")


def _config_values(out: list[Finding], rel: str, text: str) -> None:
    """Read the values of a configuration file that a reader sees as text."""
    bib = rel.endswith(".bib")
    for number, line in enumerate(text.split("\n"), start=1):
        if bib:
            field = _BIB_FIELD.match(line)
            if field:
                _scan(out, rel, field.group(1), "value", _on_line(number))
            continue
        printed = _PRINTED_LINE.match(line)
        if printed:
            for match in _QUOTED_ARGUMENT.finditer(printed.group(1)):
                said = match.group(1) if match.group(1) is not None else match.group(2)
                _scan(out, rel, said, "printed line", _on_line(number))
            continue
        value = _CONFIG_VALUE.match(line)
        if value:
            said = value.group(1)
            at = _hash_comment(said)
            said = said[:at] if at is not None else said
            said = said.strip().strip("\"'")
            _scan(out, rel, said, "value", _on_line(number))


def _notebook(out: list[Finding], rel: str, text: str) -> None:
    """Read a notebook: its Markdown cells as Markdown, its code cells as Python."""
    try:
        cells = json.loads(text).get("cells", [])
    except (ValueError, AttributeError):
        return
    for index, cell in enumerate(cells, start=1):
        source = "".join(cell.get("source", []))
        where = f"{rel} (cell {index})"
        if cell.get("cell_type") == "markdown":
            _markdown(out, where, source, "md")
        elif cell.get("cell_type") == "code":
            _python(out, where, source)


# ---------------------------------------------------------------------------
# The files.
# ---------------------------------------------------------------------------

#: A Spanish file: the Spanish site, a Spanish register, the Spanish catalogue.
_SPANISH_FILE = re.compile(r"(?:^|/)es/|\.es\.mdx?$|catalogue-es\.json$")
#: Data and drawings, which hold no text: the test data, CSV, SVG and the rest.
_DATA_FILE = re.compile(
    r"^tests/data/|\.(?:csv|tsv|svg|xml|css|lock|asc|png|jpg|jpeg|webp|gif|pdf|wav|WAV"
    r"|npz|npy|zip|ttf|woff2?|ico|typed)$"
)
#: The generated files that copy the text of another file, which is read instead.
_COPIES = re.compile(
    r"^(?:llms[\w.-]*\.txt|README_PYPI\.md|site/src/content/docs/reference/api/.*)$"
)
#: How a page of the errata the site writes from the registry opens.
_ERRATA_COPY = "<!-- Generated from docs/ERRATA.md"
#: The configuration files, whose ``#`` comments are read.
_HASH_FILE = re.compile(
    r"\.(?:ya?ml|toml|cff|sh|cfg|in|properties|txt|gitignore|gitattributes|editorconfig)$"
    r"|(?:^|/)(?:Makefile|Dockerfile|pre-commit|\.git-blame-ignore-revs)$"
)


#: A number whose comma an implicit concatenation splits between two string
#: literals: ``"the floor is 0," "5 m"``.
_SPLIT_NUMBER = re.compile(r"[0-9],?[\"']\s*[rRbBuUfF]{0,2}[\"'],?[0-9]")
#: The committed figures and plates, whose drawn text is what a reader sees,
#: and their Spanish editions, which keep the comma.
_DRAWING = re.compile(r"^\.github/images/[^/]+\.svg$")
_SPANISH_DRAWING = re.compile(r"_es(?:_dark)?\.svg$")
#: The string a figure or a plate drew, which its SVG keeps in a comment.
_DRAWN = re.compile(r"<!--(.*?)-->", re.DOTALL)


def _drawing(rel: str, text: str) -> list[Finding]:
    """Every decimal comma an English figure or plate draws.

    Matplotlib and the plates' writer draw text as outlines and keep the string
    in a comment beside them, so the committed SVG says what the figure says.
    Its dash patterns and coordinates are attributes, never comments, and are
    not read. This is where the figure code's own text is seen whole: a label
    the source builds at run time, or one the source reader takes for a dash
    pattern, is drawn here as the reader sees it.
    """
    out: list[Finding] = []
    for match in _DRAWN.finditer(text):
        drawn = html.unescape(match.group(1)).strip()
        line = text.count("\n", 0, match.start()) + 1
        _scan(out, rel, drawn, "drawn text", _on_line(line))
    return out


def is_copy(path: pathlib.Path, rel: str) -> bool:
    """Whether *path*, *rel* in the repository, copies the text of another file."""
    if _COPIES.match(rel):
        return True
    if not path.is_file():
        return False
    if is_edition_file(path):
        return True
    if "/reference/errata/" in rel:
        with path.open(encoding="utf-8") as handle:
            return _ERRATA_COPY in handle.read(2000)
    return False


def findings_in(text: str, rel: str) -> list[Finding]:
    """Every decimal comma the English text of a file writes, read as *rel*."""
    if _SPANISH_FILE.search(rel) or _SPANISH_DRAWING.search(rel):
        return []
    if _DRAWING.match(rel):
        return _drawing(rel, text)
    python = rel.endswith((".py", ".pyi")) or (
        rel.startswith("hooks/") and text.startswith("#!/usr/bin/env python")
    )
    split = python and _SPLIT_NUMBER.search(text) is not None
    if _DATA_FILE.search(rel) or not (TOKEN.search(text) or split):
        return []
    out: list[Finding] = []
    name = rel.rsplit("/", 1)[-1]
    if python:
        _python(out, rel, text)
    elif rel.endswith((".md", ".mdx")):
        _markdown(out, rel, text, "md" if rel.endswith(".md") else "mdx")
    elif re.search(r"\.(?:[cm]?js|[cm]?ts|jsx|tsx|json)$", name):
        _script(out, rel, text)
    elif name.endswith(".astro"):
        _astro(out, rel, text)
    elif name.endswith(".ipynb"):
        _notebook(out, rel, text)
    elif _HASH_FILE.search(rel):
        _hash_comments(out, rel, text)
        _config_values(out, rel, text)
    elif rel.endswith(".bib"):
        _config_values(out, rel, text)
    return sorted(out, key=lambda f: (f.path, f.line))


def english_files(root: pathlib.Path = ROOT) -> list[tuple[pathlib.Path, str]]:
    """Every tracked file of the repository this check reads, and its name in it."""
    listed = subprocess.run(  # nosec B603 B607 - a fixed git command
        ["git", "-C", str(root), "ls-files"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.split("\n")
    files: list[tuple[pathlib.Path, str]] = []
    for rel in listed:
        path = root / rel
        if not rel or _SPANISH_FILE.search(rel) or _SPANISH_DRAWING.search(rel):
            continue
        if _DATA_FILE.search(rel) and not _DRAWING.match(rel):
            continue
        if path.is_file() and not path.is_symlink() and not is_copy(path, rel):
            files.append((path, rel))
    return files


def _given_files(paths: Sequence[str]) -> list[tuple[pathlib.Path, str]]:
    """The files named on the command line, a folder standing for its files."""
    files: list[tuple[pathlib.Path, str]] = []
    for given in paths:
        target = pathlib.Path(given)
        found = [target] if target.is_file() else sorted(target.rglob("*"))
        for path in found:
            if not path.is_file():
                continue
            resolved = path.resolve()
            try:
                rel = resolved.relative_to(ROOT).as_posix()
            except ValueError:
                rel = path.as_posix()
            files.append((path, rel))
    return files


def english_findings(files: Iterable[tuple[pathlib.Path, str]]) -> list[Finding]:
    """Every decimal comma in the English text of *files*."""
    found: list[Finding] = []
    for path, rel in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        found.extend(findings_in(text, rel))
    return found


def _english_main(paths: Sequence[str], *, strict: bool, tsv: bool) -> int:
    """Run the English check and report it; the exit status."""
    files = _given_files(paths) if paths else english_files()
    found = english_findings(files)
    decimals = [f for f in found if f.kind == DECIMAL]
    ambiguous = [f for f in found if f.kind == AMBIGUOUS]
    groups = [f for f in found if f.kind == THOUSANDS]
    if tsv:
        for f in found:
            print(f"{f.path}\t{f.line}\t{f.kind}\t{f.where}\t{f.token}\t{f.context}")
    else:
        for f in ambiguous:
            print(
                f"{f.path}:{f.line}: {f.token!r} may be a decimal or a thousands group ({f.where}): {f.context}"
            )
        for f in decimals:
            print(
                f"{f.path}:{f.line}: {f.token!r} is a decimal comma in English text ({f.where}): {f.context}",
                file=sys.stderr,
            )
        for f in groups:
            print(
                f"{f.path}:{f.line}: {f.token!r} groups thousands with a comma ({f.where}): {f.context}",
                file=sys.stderr,
            )
    print(
        f"{len(decimals)} decimal comma(s), {len(groups)} comma thousands group(s) "
        f"and {len(ambiguous)} number(s) to decide "
        f"in the English text of {len(files)} files."
    )
    if decimals:
        print(
            "\nEnglish text writes the decimal point, a value restated from a print "
            "among them; the comma stays only in a literal transcription of the "
            "print (quotation marks, a block quote, the print field of an errata "
            "entry, the printed column of the conformance report) and in Spanish "
            "(docs/contributing/prose.md#p9).",
            file=sys.stderr,
        )
    if groups:
        print(
            "\nA long number groups its digits in threes with U+202F, the narrow "
            "no-break space, never with a comma (docs/contributing/prose.md#p8).",
            file=sys.stderr,
        )
    return 1 if decimals or groups or (strict and ambiguous) else 0


def main(argv: list[str] | None = None) -> int:
    """Run the checks the command line asks for."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "paths",
        nargs="*",
        help="files or folders to read instead of the default ones",
    )
    parser.add_argument(
        "--labels",
        action="store_true",
        help="only the Spanish figure labels beside mathematics (rule F29)",
    )
    parser.add_argument(
        "--english",
        action="store_true",
        help="only the decimal comma in English text (rules P9 and F58)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="refuse a number that may be a thousands group too",
    )
    parser.add_argument(
        "--tsv",
        action="store_true",
        help="print every finding of the English check as a tab-separated row",
    )
    args = parser.parse_args(argv)
    status = 0
    if args.labels or not args.english:
        status |= _labels_main(args.paths or DEFAULT_ROOTS)
    if args.english or not args.labels:
        status |= _english_main(args.paths, strict=args.strict, tsv=args.tsv)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
