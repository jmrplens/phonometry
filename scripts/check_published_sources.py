#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a published value that does not say which page it was read on.

A number transcribed from a book is only checkable if the next reader can open
the same page. Nothing in CI used to require that: the convention lived in
review, and review is where it was quietly dropped, which is how one table came
to cite a folio that prints no such number and another attributed to a table two
columns it does not print. This is the guard for that class.

Three things are checked, and the third is what stops the first two being
vacuous.

1. **The grammar of a ``source`` field.** Every public record that carries one,
   and every mapping or sequence of such records, has to write it the way the
   errata registry writes its evidence (CONTRIBUTING.md "Filing an errata
   entry"): the document, the table or section, the PDF page and the printed
   folio, cited by designation and never by file path. A row whose columns come
   off two pages names both, separated by ``"; "``. :data:`FOLIO_FORMS` has the
   four spellings, including the one for a page that prints no folio at all.
   Nothing published here needs that fourth form yet; it is accepted from the
   start so that the first row that does cannot invent a second spelling for an
   unnumbered page. ``scripts/check_errata_evidence.py``, which reads the same
   grammar in the errata registry, has still to be taught it, and whoever files
   the first such entry there does it in that change.

2. **The document exists in the bibliography.** Each distinct document named is
   split and recomposed by :mod:`conformance.references`, character for
   character, and then has to have an entry in ``docs/reference/bibliography.md``.
   A book cited from ``src`` and missing from the bibliography is a source the
   reader cannot resolve; the sweep that added this guard found one.

3. **The registry, so the guard has something to be true of.**
   :data:`SOURCED` names every table in ``src`` transcribed from a book or a
   paper, and requires its ``#:`` banner to cite **both** a PDF page and a
   printed folio. The census that fills it is re-run here, over the banners
   themselves, so a table transcribed from a new book fails until it is
   registered: that is what closes the class rather than pinning today's
   instances of it.

A standard is deliberately outside the registry. ISO, IEC, EN and DIN number
their own clauses and tables, and CONTRIBUTING.md asks for a citation by that
number; a PDF page would pin the reading to one copy of a document this project
does not redistribute. A book numbers nothing a reader can resolve without the
page, which is exactly why the errata rule demands one.

:data:`PAGE_UNKNOWN` is the escape hatch, and it is a ratchet in both
directions: an entry whose banner now cites its page fails until the line is
deleted, and a line naming a table that no longer exists fails too.

Usage::

    python scripts/check_published_sources.py

Exit status 0 when every published value says where it was read; 1 otherwise,
naming the record, the field and the module.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import importlib
import pathlib
import pkgutil
import re
import sys
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, NamedTuple

from conformance import references

import phonometry

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import ModuleType

ROOT = pathlib.Path(__file__).resolve().parent.parent
PACKAGE = pathlib.Path(phonometry.__file__).resolve().parent
BIBLIOGRAPHY = ROOT / "docs" / "reference" / "bibliography.md"

#: The field a record uses to say where it was read.
SOURCE_FIELD = "source"

#: One citation: the document and its locator, the PDF page, and the folio in
#: parentheses. Several are joined by ``"; "``.
CITATION = re.compile(
    r"^(?P<cite>.+?), PDF pages? (?P<pages>\d+(?:-\d+)?) \((?P<folio>[^()]+)\)$"
)

#: The four ways a folio may be written. The last is for a page that prints no
#: folio of its own, which happens on the landscape plates of an appendix; it
#: names the folios either side rather than inventing one.
#: Several citations are joined by ``"; "``, and the fourth folio form carries a
#: semicolon of its own, so the split is only made after a closing parenthesis.
JOINER = re.compile(r"(?<=\)); ")

FOLIO_FORMS = (
    re.compile(r"^printed p\. \d+$"),
    re.compile(r"^printed pp\. \d+-\d+$"),
    re.compile(r"^printed folio \d+$"),
    re.compile(r"^no printed folio; between folios \d+ and \d+$"),
)

#: Every table in ``src`` transcribed from a book or a paper, with what it holds.
#: A banner here must cite both the PDF page and the printed folio. Keyed by
#: module path relative to the package and the name of the constant.
#:
#: The value opens with the citation, up to its first comma, and that citation
#: is parsed and checked against the bibliography like any other: a book this
#: library transcribes a table from and does not list is a source the reader
#: cannot resolve.
SOURCED: dict[tuple[str, str], str] = {
    (
        "building/prediction/masonry_cavity_wall.py",
        "WALL_TIE_STIFFNESS",
    ): "Hopkins (2007) Table A4, four wall ties",
    (
        "building/prediction/panel_transmission.py",
        "PLATEAU_MATERIALS",
    ): "Norton & Karczub (2003) Table 3.1, eight plateau-method materials",
    (
        "materials/absorbers/porous.py",
        "DELANY_BAZLEY_COEFFICIENTS",
    ): "Bies 5e Table D.1, four coefficient sets C1..C8",
    (
        "materials/absorbers/porous.py",
        "PUBLISHED_POROUS_MATERIALS",
    ): "Allard & Atalla 2e, two porous specimens",
    (
        "materials/resilient/dynamic_stiffness.py",
        "RESILIENT_LAYER_STIFFNESS",
    ): "Hopkins (2007) Table A3, fifteen resilient layers",
    (
        "noise_control/duct_modes.py",
        "CIRCULAR_EIGENVALUES",
    ): "Norton & Karczub (2003) Table 7.1, twelve circular-duct eigenvalues",
    (
        "room/steady_field.py",
        "SOURCE_POWER_MODELS",
    ): "Norton & Karczub (2003) Table 4.5, three sound power models",
    (
        "underwater/bioacoustics/audiograms.py",
        "_AUDIOGRAM_ORIGINAL",
    ): "Southall et al. (2019) Table 2, seven group audiogram fits",
    (
        "underwater/bioacoustics/audiograms.py",
        "_AUDIOGRAM_NORMALIZED",
    ): "Southall et al. (2019) Table 3, the same fits normalised",
    (
        "underwater/bioacoustics/audiograms.py",
        "BEST_HEARING_FREQUENCY_KHZ",
    ): "Southall et al. (2019) Table 4, frequency of best hearing",
    (
        "underwater/bioacoustics/weighting.py",
        "_SOUTHALL_2019",
    ): "Southall et al. (2019) Table 5, the weighting-function parameters",
    (
        "underwater/bioacoustics/weighting.py",
        "_CRITERIA_SOUTHALL_CONTINUOUS",
    ): "Southall et al. (2019) Tables 6 and 7, TTS and PTS onset thresholds",
    (
        "underwater/propagation/weston_regimes.py",
        "WESTON_SEABEDS",
    ): "Ainslie (2010) Table 9.1, two characteristic seabeds",
}

#: Tables whose page cannot be established, each with the reason. Empty, and
#: meant to stay that way: every source this repository transcribes from is a
#: document it can open. A line added here is a promise to come back.
PAGE_UNKNOWN: dict[tuple[str, str], str] = {}

#: How this tree spells a book or a paper in a banner. A table whose banner
#: matches one of these and names a table, annex or section is a transcription
#: from a document with pages, and belongs in :data:`SOURCED`.
BOOK_OR_PAPER = re.compile(
    r"(Bies\b|Cox (?:&|and) D'Antonio|Hopkins\b|Allard (?:&|and) Atalla|Mechel\b"
    r"|Beranek\b|Ver (?:&|and) Beranek|Norton (?:&|and) Karczub|Ainslie\b|Vigran\b"
    r"|Kuttruff\b|Everest\b|Maa \d{4}|Miki \d{4}|Jimenez|Rindel\b|Fahy\b|Heckl\b"
    r"|[A-Z][a-z]+ et al\.?,? \(?\d{4}"
    r"|[A-Z][a-z]+ (?:&|and) [A-Z][a-z]+,? \(?\d{4})"
)

#: A locator inside a document: what makes a banner a transcription rather than
#: a sentence that happens to name a book.
LOCATOR = re.compile(r"\b(Table|Tables|Annex|Appendix|Fig\.|Figure|Eq\.|Sect\.)\b")

#: What a registered banner has to carry.
BANNER_PDF_PAGE = re.compile(r"PDF pages? \d+")
BANNER_FOLIO = re.compile(r"printed (?:p\.|pp\.|folio) \d+|no printed folio")


class Problem(NamedTuple):
    """One thing wrong, with where to look."""

    #: Where the offending value or banner lives.
    where: str
    #: What is wrong with it.
    detail: str


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def public_modules() -> Iterator[tuple[str, ModuleType]]:
    """Every module a caller can import by a public path, imported."""
    yield "phonometry", phonometry
    for found in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if not all(_is_public(part) for part in found.name.split(".")):
            continue
        try:
            yield found.name, importlib.import_module(found.name)
        except ImportError:  # pragma: no cover - an optional backend
            continue


def _sourced_records(obj: object) -> Iterator[object]:
    """Every record carrying a ``source`` field reachable from *obj*.

    A published table is a mapping or a sequence of records as often as it is
    one record, and the provenance rule is the same in all three shapes.
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        if any(field.name == SOURCE_FIELD for field in dataclasses.fields(obj)):
            yield obj
        return
    if isinstance(obj, Mapping):
        for value in obj.values():
            yield from _sourced_records(value)
        return
    if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes)):
        for value in obj:
            yield from _sourced_records(value)


def published_records() -> Iterator[tuple[str, str, object]]:
    """``(module, exported name, record)`` for every published sourced record."""
    seen: set[int] = set()
    for module_name, module in public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported, None)
            for record in _sourced_records(obj):
                if id(record) in seen:
                    continue
                seen.add(id(record))
                yield module_name, exported, record


def citation_problems(source: str) -> list[str]:
    """What is wrong with a ``source`` string, or an empty list.

    :param source: The field's value, one or more citations joined by ``"; "``.
    :return: One message per defect found.
    """
    problems: list[str] = []
    if not source.strip():
        return ["is empty; every published value names the page it was read on"]
    for citation in JOINER.split(source):
        match = CITATION.match(citation)
        if match is None:
            problems.append(
                f"{citation!r} is not '<Document> <Table>, PDF page N (printed p. M)'"
            )
            continue
        folio = match["folio"]
        if not any(form.match(folio) for form in FOLIO_FORMS):
            problems.append(
                f"{citation!r} writes the folio as {folio!r}; the four forms are "
                "'printed p. N', 'printed pp. N-M', 'printed folio N' and "
                "'no printed folio; between folios A and B'"
            )
            continue
        cite = match["cite"]
        try:
            parsed = references.parse(cite)
        except ValueError as error:
            problems.append(f"{cite!r} does not parse as a reference: {error}")
            continue
        if references.recompose(parsed) != cite:
            problems.append(
                f"{cite!r} does not recompose character for character; it reads back as "
                f"{references.recompose(parsed)!r}"
            )
            continue
        problems.extend(_bibliography_problems(cite, parsed))
    return problems


def _bibliography_problems(cite: str, parsed: references.Reference) -> list[str]:
    """Whether every document *cite* names has a bibliography entry."""
    text = BIBLIOGRAPHY.read_text(encoding="utf-8")
    problems = []
    for document in references.documents(parsed):
        designation = document.designation
        lead = re.split(r" (?:&|and) | et al\.?", designation)[0].strip()
        if not lead:
            continue
        if not re.search(rf"^- {re.escape(lead)}[,.]", text, re.MULTILINE):
            problems.append(
                f"{cite!r} names {designation!r}, which has no entry in "
                "docs/reference/bibliography.md"
            )
    return problems


def banner_above(lines: Sequence[str], index: int) -> str:
    """The ``#:`` doc-comment block immediately above line *index* (0-based)."""
    out: list[str] = []
    cursor = index - 1
    while cursor >= 0 and lines[cursor].lstrip().startswith("#:"):
        out.append(lines[cursor].lstrip()[2:].strip())
        cursor -= 1
    return " ".join(reversed(out))


def module_tables(path: pathlib.Path) -> Iterator[tuple[str, str]]:
    """``(constant name, banner)`` for every module-level table in *path*.

    A table is a literal collection of more than one entry, or a call that
    builds one; a scalar is a cited number and the errata registry covers it.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for node in ast.parse(text).body:
        names: list[str] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names, value = [node.target.id], node.value
        if value is None:
            continue
        if isinstance(value, (ast.Tuple, ast.List, ast.Set)):
            size = len(value.elts)
        elif isinstance(value, ast.Dict):
            size = len(value.keys)
        elif isinstance(value, ast.Call):
            size = 2
        else:
            continue
        if size < 2:
            continue
        for name in names:
            if not name.lstrip("_").isupper():
                continue
            yield name, banner_above(lines, node.lineno - 1)


def registry_problems() -> list[Problem]:
    """The registry against the tree: banners, the census, and stale entries."""
    problems: list[Problem] = []
    banners: dict[tuple[str, str], str] = {}
    census: set[tuple[str, str]] = set()
    for path in sorted(PACKAGE.rglob("*.py")):
        module = path.relative_to(PACKAGE).as_posix()
        for name, banner in module_tables(path):
            banners[module, name] = banner
            if banner and BOOK_OR_PAPER.search(banner) and LOCATOR.search(banner):
                census.add((module, name))

    for key, reason in SOURCED.items():
        registered = banners.get(key)
        where = f"{key[0]}::{key[1]}"
        cite = reason.split(",")[0].strip()
        try:
            parsed = references.parse(cite)
        except ValueError as error:
            problems.append(
                Problem(where, f"names {cite!r}, which does not parse: {error}")
            )
        else:
            problems.extend(
                Problem(where, detail)
                for detail in _bibliography_problems(cite, parsed)
            )
        if registered is None:
            problems.append(
                Problem(where, f"is registered as {reason!r} and no longer exists")
            )
            continue
        if key in PAGE_UNKNOWN:
            continue
        if not BANNER_PDF_PAGE.search(registered):
            problems.append(
                Problem(where, "cites no PDF page; a transcribed table names both")
            )
        if not BANNER_FOLIO.search(registered):
            problems.append(
                Problem(where, "cites no printed folio; a transcribed table names both")
            )

    for key, reason in PAGE_UNKNOWN.items():
        where = f"{key[0]}::{key[1]}"
        if key not in SOURCED:
            problems.append(
                Problem(
                    where, f"is allowed a missing page ({reason}) and is not in SOURCED"
                )
            )
            continue
        banner = banners.get(key, "")
        if BANNER_PDF_PAGE.search(banner) and BANNER_FOLIO.search(banner):
            problems.append(
                Problem(
                    where,
                    f"now cites its page, so the PAGE_UNKNOWN line ({reason}) must go",
                )
            )

    problems.extend(
        Problem(
            f"{module}::{name}",
            "is transcribed from a book or a paper and is not in SOURCED",
        )
        for module, name in sorted(census - set(SOURCED))
    )
    return problems


def record_problems() -> list[Problem]:
    """Every published record whose ``source`` does not say where it was read."""
    problems: list[Problem] = []
    for module_name, exported, record in published_records():
        source = getattr(record, SOURCE_FIELD, "")
        name = getattr(record, "name", type(record).__name__)
        where = f"{module_name}.{exported} -> {name!r}"
        problems.extend(
            Problem(where, detail) for detail in citation_problems(str(source))
        )
    return problems


def main() -> int:
    """Report every published value that does not name its page."""
    parser = argparse.ArgumentParser(
        description="Provenance gate for published values."
    )
    parser.parse_args()

    problems = record_problems() + registry_problems()
    if not problems:
        registered = len(SOURCED)
        records = sum(1 for _ in published_records())
        print(
            f"{records} published record(s) cite a page in the errata grammar, and "
            f"{registered} transcribed table(s) name their PDF page and printed folio."
        )
        return 0
    print("::error::a published value does not say which page it was read on")
    for problem in problems:
        print(f"  {problem.where}: {problem.detail}")
    print(
        "  -> write the source as '<Document> <Table>, PDF page N (printed p. M)', "
        "join several with '; ', and register a transcribed table in SOURCED at the "
        "top of scripts/check_published_sources.py."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
