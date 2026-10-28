#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Render the committed evidence documents as Starlight pages.

The documents that carry the project's numerical evidence live under ``docs/``
and are the authority for their own content. This script owns one of them:

* ``docs/ERRATA.md`` - the hand-maintained registry of defects found in the
  published sources the library implements from.

It used to own the conformance report too. That one is now structured data,
``docs/conformance.json``, and its pages render from it through a component
rather than carrying a copy of its text, so a transplant would be copying a
rendering of the same rows into a page that already has the rows.

The registry used to be reachable only on GitHub: the site merely described it
and linked out. This script transplants it into Starlight pages so the site
renders the evidence itself, without anyone ever hand-copying a table.

**One page per document family, and an index.** The registry was one page
until it outgrew what a search engine reads of one: Googlebot fetches the
first 2 MB of a page, counted uncompressed, and indexes nothing past it, and
the typeset mathematics of 351 entries came to 4.9 MB, so two thirds of the
registry never reached the index. Each entry now lands on the page of the
document family it is about (:func:`family_of`): ``ISO 3743-1:2010`` and
``ISO 3743-2:2018`` on ``/reference/errata/iso-3743/``, a book on a page named
after its authors. ``/reference/errata/`` keeps its hand-written introduction
and the registry's own, and lists every family with every entry in it (through
``src/components/ErrataFamily.astro``, which reads the anchors off the family
pages as the build renders them); a link written against the old single page,
``/reference/errata/#<entry>``, still lands on the entry, because the index
sends a fragment it does not hold to the page that does
(``src/components/ErrataRouter.astro``).

The family pages are generated whole, frontmatter included. The index keeps
its hand-written introduction above a marker line, and everything below the
marker is replaced on every run. The transformation is purely textual and
deterministic (no timestamps, no environment-dependent text), so CI can diff a
fresh run against the committed pages exactly like it does for the generated
API reference (see the ``site-reports`` job in .github/workflows/python-app.yml).

The Spanish pages transplant ``docs/ERRATA.es.md``, the hand-maintained
entry-for-entry translation of the registry. The English wording stays the
authoritative one (it is what has been or will be communicated to the issuing
bodies; both introductions say so), and this script holds the two editions
together: same number of ``##`` entries, same order, and each pair of headings
naming the same source document. A run fails before writing anything when the
editions drift. Entry *i* of the Spanish edition goes to the family page of
entry *i* of the English one, so the two languages split identically even
where a heading is translated past recognition ("Anexo 16 de la OACI").

Stdlib only. Regenerate with ``make site-reports``.
"""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import posixpath
import re
import sys
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
CONTENT = ROOT / "site" / "src" / "content" / "docs"

#: Blob root used to rewrite the source documents' repo-relative links, which
#: point at files (tests, modules) that have no page on the site.
BLOB = "https://github.com/jmrplens/phonometry/blob/main"

#: The site's base path, which every internal link carries.
SITE_BASE = "/phonometry"

#: Where the errata pages live, under ``site/src/content/docs`` (and under
#: ``es/`` for the Spanish ones).
ERRATA_DIR = "reference/errata"

#: Everything below this line in the index page is generated. The marker is
#: written back on every run, so a page that lost it is simply re-marked. The
#: index is MDX, which has no HTML comments, so the marker is an MDX comment.
BEGIN = (
    "{{/* BEGIN GENERATED BODY - transplanted from {source} by "
    "scripts/generate_site_reports.py (`make site-reports`). "
    "Edit the source document, never the text below. */}}"
)
END = "{/* END GENERATED BODY */}"

#: The first line of every family page, which this script writes whole. It is
#: also how a stale page is recognised as this script's to delete: a file in
#: the errata folder without it was written by hand and is left alone.
PAGE_MARKER = (
    "<!-- Generated from docs/{source} by scripts/generate_site_reports.py "
    "(`make site-reports`). Edit the source document, never this page. -->"
)

#: A markdown link target: ``](target)``. Bare enough for these two documents,
#: which contain no reference-style links and no parentheses inside targets.
_LINK_RE = re.compile(r"\]\((?P<target>[^)\s]+)\)")

#: Absolute or in-page targets that must be left alone.
_ABSOLUTE_RE = re.compile(r"^(?:[a-z][a-z0-9+.-]*:|//|#)")

#: The longest frontmatter description a generated page may carry. The site
#: checks every built page at 160 characters (scripts/check-descriptions.mjs);
#: refusing here, a little under, names the family instead of a URL.
MAX_DESCRIPTION = 155

#: The longest frontmatter title the site's pages carry (the pull request
#: pipeline builds the site, and its titles are held to this).
MAX_TITLE = 57

Lang = Literal["en", "es"]


def rewrite_links(body: str, *, relative_to: str) -> str:
    """Point repo-relative markdown links at the GitHub blob.

    ``docs/ERRATA.md`` cites source modules and regression tests with paths
    relative to ``docs/`` (``../tests/reference_data/``). Those files have no
    route on the site, so the site copy must reach them on GitHub.

    :param body: Markdown body to rewrite.
    :type body: str
    :param relative_to: Repo-relative directory the links resolve against.
    :type relative_to: str
    :return: The body with every repo-relative link turned into a blob URL.
    :rtype: str
    """

    def replace(match: re.Match[str]) -> str:
        target = match.group("target")
        if _ABSOLUTE_RE.match(target):
            return match.group(0)
        path, _, anchor = target.partition("#")
        resolved = posixpath.normpath(posixpath.join(relative_to, path))
        return f"]({BLOB}/{resolved}{'#' + anchor if anchor else ''})"

    return _LINK_RE.sub(replace, body)


def body_from(source: pathlib.Path, *, start: re.Pattern[str]) -> str:
    """Return the source document from its first ``start`` line onwards.

    Drops whatever precedes it: the "do not hand-edit" file banner, the
    back-link to the docs index and the H1 (the page frontmatter supplies the
    site's own title, and a second H1 would break the heading order).

    :param source: Document to read.
    :type source: pathlib.Path
    :param start: Pattern matching the first line to keep.
    :type start: re.Pattern[str]
    :return: The retained body, with trailing whitespace stripped.
    :rtype: str
    :raises SystemExit: If no line matches ``start``.
    """
    lines = source.read_text(encoding="utf8").splitlines()
    for index, line in enumerate(lines):
        if start.match(line):
            body = "\n".join(lines[index:]).rstrip()
            return rewrite_links(body, relative_to=source.parent.name)
    sys.exit(
        f"{source.relative_to(ROOT)}: no line matches {start.pattern!r}. "
        "The document layout changed; update scripts/generate_site_reports.py."
    )


@dataclasses.dataclass(frozen=True)
class Edition:
    """One language of the registry: where it is read and where it lands."""

    lang: Lang
    #: Document under ``docs/`` whose text is transplanted.
    source: pathlib.Path
    #: Pattern matching the first source line to keep (the registry's own
    #: introduction, which explains how to read every entry).
    start: re.Pattern[str]

    @property
    def folder(self) -> str:
        """The errata folder of this language, relative to the content root."""
        return ERRATA_DIR if self.lang == "en" else f"es/{ERRATA_DIR}"

    @property
    def index(self) -> str:
        """The index page of this language, relative to the content root."""
        return f"{self.folder}/index.mdx"


EDITIONS: tuple[Edition, ...] = (
    # The conformance report is not here. It used to be transplanted into two
    # pages, 109 kB of English table each, the Spanish one differing only in its
    # first heading. Those pages now render from ``docs/conformance.json``
    # through ``src/components/Conformance.astro``, which can do what a
    # transplanted table could not: rank the checks by how much of their
    # published tolerance they consume, filter, and give every row an anchor.
    # ``docs/CONFORMANCE.md`` stays as the text copy a GitHub reader and an
    # agent get; it is simply no longer copied into the site.
    Edition(
        lang="en",
        source=DOCS / "ERRATA.md",
        start=re.compile(r"^During the clean-room implementation"),
    ),
    Edition(
        lang="es",
        source=DOCS / "ERRATA.es.md",
        start=re.compile(r"^Durante la implementación en sala limpia"),
    ),
)


# ---------------------------------------------------------------------------
# Families: which page an entry belongs on.
# ---------------------------------------------------------------------------

#: A standard's designation as the registry writes one, from its adoption
#: prefix to its number: ``ISO 3743-2:2018``, ``UNE-EN ISO 9614-1:2010``,
#: ``E DIN 4150-2:2023-08``, ``IEC TS 61400-11-2:2024``, ``ECMA-418-1:2024``,
#: ``ITU-R BS.468-4``, ``ANSI S3.5-1997``, ``VDI 2081 Blatt 1:2001``. The
#: ``rest`` group runs to the end of the designation (parts, edition,
#: amendments), never into the prose after it.
#:
#: A national body's adoption prefix (``UNE-``, ``BS ``, ``DIN ``) is read
#: before the issuer, so ``DIN EN ISO 717-1`` is ISO 717 and ``DIN EN 61260``
#: is EN 61260; a standard of DIN's own (``DIN 4150-3``) leaves no issuer
#: after the prefix, and the expression falls back to reading DIN as the
#: issuer. ``ISO/IEC`` is not read: whether a joint document belongs on an
#: ISO page or one of its own is a choice to make the day the registry first
#: cites one, and until then :func:`family_of` stops on it and says so.
_DESIGNATION = re.compile(
    r"(?:UNE-|BS |DIN )?(?P<draft>E )?"
    r"(?P<issuer>EN ISO|ISO(?:/(?:TS|TR|PAS|DIS))?|IEC(?: TS| TR)?|EN|CEN(?:/TS)?|DIN|ECMA"
    r"|ITU-R BS|ANSI(?:/ASA)?|VDI)"
    r"(?P<sep>[ .-])(?P<number>S?\d+(?:\.\d+)?)(?P<rest>[^\s,()\"'«»“”]*(?: Blatt [^\s,()]+)?)"
)

#: The body a family is keyed on, for each way the registry writes an issuer:
#: a technical specification, report or draft of ISO is still ISO, a European
#: adoption of an ISO standard (``EN ISO``) is that standard, a CEN technical
#: specification belongs with the EN series of its number, and ANSI/ASA is
#: ANSI as the Acoustical Society publishes it.
_CANONICAL_ISSUER = {
    "EN ISO": "ISO",
    "ISO/TS": "ISO",
    "ISO/TR": "ISO",
    "ISO/PAS": "ISO",
    "ISO/DIS": "ISO",
    "IEC TS": "IEC",
    "IEC TR": "IEC",
    "CEN": "EN",
    "CEN/TS": "EN",
    "ANSI/ASA": "ANSI",
}

#: A heading that opens with what reads as a standard's designation, one or
#: more capitalised issuer words and a number (``ISO/IEC 17025``,
#: ``ASTM C423``), which :data:`_DESIGNATION` does not know. It tells the two
#: fixes apart when :func:`family_of` stops: a standard needs its prefix
#: taught to the expression, and a row in :data:`SOURCES` would file it under
#: the books and papers.
_LOOKS_LIKE_A_DESIGNATION = re.compile(r"^(?:[A-Z]{2,}[ /.-])+[A-Z]*\s?S?\d")

#: Families that are one document line under two issuers. EN 12354:2000 was
#: replaced by EN ISO 12354:2017, and EN 61260 and EN 61094 are the CENELEC
#: adoptions of the IEC series, so a reader looking for either finds both on
#: one page. Keyed and valued by slug; a slug never moves once published.
ALIASES = {
    "en-12354": "iso-12354",
    "en-61260": "iec-61260",
    "en-61094": "iec-61094",
}

#: The order the standards groups are listed in on the index, by issuer.
_ISSUER_ORDER = ("ISO", "IEC", "EN", "DIN", "ANSI", "ECMA", "ITU-R BS", "VDI")


@dataclasses.dataclass(frozen=True)
class Source:
    """A published source that is not a standard: a book, a paper, a guide.

    Their headings name them in prose ("Long, Architectural Acoustics 2e
    (2014)", "Allard & Atalla 2e (2009)"), which no rule reads reliably, so
    each is listed here by hand with the name its page carries. A heading that
    matches neither a designation nor a row here fails the run, which is how
    a new kind of source gets its row.
    """

    #: URL segment of the family page. Never changed once published.
    slug: str
    #: Matched against the start of the English heading.
    pattern: re.Pattern[str]
    #: The name the page and the index use, per language.
    name_en: str
    name_es: str
    #: The Spanish article the name takes in running text ("el", "la"), so a
    #: title reads "Erratas del Anexo 16 de la OACI" and not "de Anexo 16".
    #: Empty for an author or a designation, which take none.
    article_es: str = ""


def _source(
    slug: str,
    pattern: str,
    name_en: str,
    name_es: str | None = None,
    article_es: str = "",
) -> Source:
    return Source(slug, re.compile(pattern), name_en, name_es or name_en, article_es)


SOURCES: tuple[Source, ...] = (
    _source("ainslie", r"Ainslie\b", "Ainslie (2010)"),
    _source("allard-atalla", r"Allard & Atalla\b", "Allard & Atalla (2009)"),
    _source("ashrae", r"ASHRAE\b", "ASHRAE (2019)"),
    _source(
        "attenborough-van-renterghem",
        r"Attenborough & Van Renterghem\b",
        "Attenborough & Van Renterghem (2021)",
    ),
    _source(
        "barham-barrera-figueroa-avison",
        r"Barham\b",
        "Barham, Barrera-Figueroa & Avison (2014)",
    ),
    _source("bies-hansen-howard", r"Bies\b", "Bies, Hansen & Howard (2017)"),
    _source("cox-dantonio", r"Cox & D'Antonio\b", "Cox & D'Antonio (2017)"),
    _source(
        "directive-eu-2015-996",
        r"(?:Commission )?Directive \(EU\) 2015/996\b",
        "Directive (EU) 2015/996",
        "Directiva (UE) 2015/996",
        "la",
    ),
    _source("ecac-doc-29", r"ECAC Doc 29\b", "ECAC Doc 29"),
    _source("harris", r"Harris\b", "Harris (1995)"),
    _source(
        "icao-annex-16",
        r"ICAO Annex 16\b",
        "ICAO Annex 16",
        "Anexo 16 de la OACI",
        "el",
    ),
    _source("jarvis", r"Jarvis\b", "Jarvis (1996)"),
    _source("jimenez", r"Jiménez\b", "Jiménez et al. (2017)"),
    _source("long", r"Long, Architectural Acoustics\b", "Long (2014)"),
    _source("maa", r"Maa\b", "Maa (1998)"),
    _source("mechel", r"Mechel\b", "Mechel (2008)"),
    _source("medwin-clay", r"Medwin & Clay\b", "Medwin & Clay (1998)"),
    _source("nmfs", r"NMFS\b", "NMFS (2024)"),
    _source(
        "norah2",
        r"NORAH2\b",
        "NORAH2 rotorcraft guidance",
        "guía de rotorcraft NORAH2",
        "la",
    ),
    _source("norton-karczub", r"Norton & Karczub\b", "Norton & Karczub (2003)"),
    _source("osses-garcia-kohlrausch", r"Osses\b", "Osses, García & Kohlrausch (2016)"),
    _source("randi", r"RANDI\b", "RANDI 3.1 Physics Description"),
    _source(
        "real-decreto-1367-2007",
        r"Real Decreto 1367/2007\b",
        "Real Decreto 1367/2007",
        article_es="el",
    ),
    _source("rossing", r"Rossing\b", "Rossing (2014)"),
    _source("southall", r"Southall\b", "Southall et al. (2019)"),
    _source("ver-beranek", r"Ver & Beranek\b", "Ver & Beranek (2006)"),
    _source("vigran", r"Vigran\b", "Vigran (2008)"),
)

#: The registry's last ``##`` section, which is not an entry but a list of
#: properties of the sources that look like misprints and are not. It gets a
#: page of its own rather than a family.
NOT_ERRATA_HEADING = "Related source properties that are not errata"
NOT_ERRATA_SLUG = "not-errata"

Group = Literal["standards", "other", "not-errata"]


@dataclasses.dataclass(frozen=True)
class Family:
    """The page an entry belongs on."""

    slug: str
    group: Group
    #: For a standard, the issuer and number it is keyed on (``ISO 3743``),
    #: which sorts the index; empty for every other source.
    key: tuple[str, int, str] | None
    name_en: str
    name_es: str
    article_es: str = ""


@dataclasses.dataclass(frozen=True)
class Designation:
    """A standard's designation found in a heading."""

    #: As printed, adoption prefix and edition included.
    text: str
    #: The family slug it belongs to.
    slug: str
    #: The issuer and number a reader knows the series by (``ISO/TS 12913``).
    series: str
    #: Canonical issuer and number, for sorting.
    key: tuple[str, int, str]


def _slug_part(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def designations(heading: str) -> list[Designation]:
    """Every standard's designation a heading names, in order.

    :param heading: An entry heading, without its ``##``.
    :type heading: str
    :return: The designations, each with the family it belongs to.
    :rtype: list[Designation]
    """
    found: list[Designation] = []
    for match in _DESIGNATION.finditer(heading):
        printed_issuer = match.group("issuer")
        issuer = _CANONICAL_ISSUER.get(printed_issuer, printed_issuer)
        number = match.group("number")
        slug = f"{_slug_part(issuer)}-{_slug_part(number)}"
        slug = ALIASES.get(slug, slug)
        shown_issuer = "ISO" if printed_issuer == "EN ISO" else printed_issuer
        series = f"{shown_issuer}{match.group('sep')}{number}"
        digits = re.search(r"\d+", number)
        order = (
            _ISSUER_ORDER.index(issuer)
            if issuer in _ISSUER_ORDER
            else len(_ISSUER_ORDER)
        )
        key = (f"{order:02d}", int(digits.group(0)) if digits else 0, number)
        text = match.group(0).strip().rstrip(".")
        found.append(Designation(text=text, slug=slug, series=series, key=key))
    return found


def family_of(heading: str) -> Family:
    """The family page an English entry heading belongs on.

    A heading that opens with a standard's designation belongs to that
    standard's series, named after every way the registry writes it (see
    :func:`series_names`); any other heading must open with the name of a
    :data:`SOURCES` row.

    :param heading: An English entry heading, without its ``##``.
    :type heading: str
    :return: The family.
    :rtype: Family
    :raises SystemExit: If the heading opens with neither.
    """
    if heading == NOT_ERRATA_HEADING:
        return Family(
            slug=NOT_ERRATA_SLUG,
            group="not-errata",
            key=None,
            name_en="Source properties that are not errata",
            name_es="Propiedades de las fuentes que no son erratas",
        )
    first = _DESIGNATION.match(heading)
    if first is not None:
        designation = designations(heading)[0]
        return Family(
            slug=designation.slug,
            group="standards",
            key=designation.key,
            name_en=designation.series,
            name_es=designation.series,
        )
    for source in SOURCES:
        if source.pattern.match(heading):
            return Family(
                slug=source.slug,
                group="other",
                key=None,
                name_en=source.name_en,
                name_es=source.name_es,
                article_es=source.article_es,
            )
    if _LOOKS_LIKE_A_DESIGNATION.match(heading):
        sys.exit(
            f"docs/ERRATA.md: the entry {heading!r} opens with what looks like a "
            "standard's designation that scripts/generate_site_reports.py does not "
            "read. Teach _DESIGNATION its prefix and _CANONICAL_ISSUER the series it "
            "belongs to; a row in SOURCES would file a standard under 'Guidance, "
            "regulations, books and papers'. If it is not a standard, add a row to "
            "SOURCES naming the page it belongs on."
        )
    sys.exit(
        f"docs/ERRATA.md: the entry {heading!r} opens with neither a standard's "
        "designation nor a source scripts/generate_site_reports.py knows. Add a "
        "row to SOURCES naming the page it belongs on."
    )


# ---------------------------------------------------------------------------
# The registry, read into entries.
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class Registry:
    """One edition of the registry, cut at its ``##`` headings."""

    #: The registry's own introduction, everything before the first entry.
    preamble: str
    #: Each entry's heading (without ``## ``) and its full text.
    entries: tuple[tuple[str, str], ...]


#: A separator line the registry draws between runs of entries. It belongs to
#: the single document, not to the entry it happens to follow.
_RULE = re.compile(r"^-{3,}\s*$")


def _trim(lines: Sequence[str]) -> str:
    kept = list(lines)
    while kept and (not kept[-1].strip() or _RULE.match(kept[-1])):
        kept.pop()
    return "\n".join(kept)


def read_registry(edition: Edition) -> Registry:
    """Cut one edition of the registry into its introduction and entries.

    :param edition: The edition to read.
    :type edition: Edition
    :return: The registry, links already pointed at the GitHub blob.
    :rtype: Registry
    """
    lines = body_from(edition.source, start=edition.start).splitlines()
    starts = [index for index, line in enumerate(lines) if line.startswith("## ")]
    if not starts:
        sys.exit(f"{edition.source.relative_to(ROOT)}: no ``##`` entries found.")
    preamble = _trim(lines[: starts[0]])
    entries = []
    for position, begin in enumerate(starts):
        end = starts[position + 1] if position + 1 < len(starts) else len(lines)
        entries.append((lines[begin][3:].strip(), _trim(lines[begin:end])))
    return Registry(preamble=preamble, entries=tuple(entries))


# ---------------------------------------------------------------------------
# Page text.
# ---------------------------------------------------------------------------


def _yaml(text: str) -> str:
    """A double-quoted YAML scalar."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _join(items: Sequence[str], lang: Lang) -> str:
    """``a, b and c``, with the Spanish conjunction where Spanish needs it.

    Spanish writes ``e`` for ``y`` before a word that starts with the sound
    /i/, which every ``ISO`` and ``IEC`` here does: "ISO 3741 e ISO 3744".
    """
    if len(items) == 1:
        return items[0]
    head, last = ", ".join(items[:-1]), items[-1]
    if lang == "en":
        return f"{head} and {last}"
    word = "e" if last[:1] in {"I", "i", "Í"} else "y"
    return f"{head} {word} {last}"


def series_names(slug: str, found: Sequence[Designation]) -> list[str]:
    """Every series a standards family gathers, the one it is keyed on first.

    The caller joins them in its own language (:func:`_join`), which is what
    lets Spanish write "e" before a series that starts with the sound /i/.

    :param slug: The family's slug.
    :type slug: str
    :param found: Every designation of the family, in registry order.
    :type found: Sequence[Designation]
    :return: For example ``["ISO 12354", "EN 12354"]``.
    :rtype: list[str]
    """
    series = list(dict.fromkeys(d.series for d in found))
    keyed = [s for s in series if f"{_slug_part(s.split()[0])}-" in f"{slug}-"]
    return keyed[:1] + [s for s in series if s not in keyed[:1]]


def editions_of(found: Sequence[Designation]) -> list[str]:
    """The printed editions a family's entries are about, in registry order.

    A designation written without its edition is dropped when the same one is
    also written with it ("IEC 60268-1" beside "IEC 60268-1:1985").

    :param found: Every designation of the family, in registry order.
    :type found: Sequence[Designation]
    :return: The distinct designations as printed.
    :rtype: list[str]
    """
    texts = list(dict.fromkeys(d.text for d in found))
    return [
        text
        for text in texts
        if not any(other != text and other.startswith(text + ":") for other in texts)
    ]


@dataclasses.dataclass(frozen=True)
class FamilyPage:
    """Everything one family page and its index line need."""

    family: Family
    #: Positions of the family's entries in the registry, in order.
    positions: tuple[int, ...]
    #: Printed editions of a standards family (empty for any other source).
    editions: tuple[str, ...]
    name_en: str
    name_es: str

    def name(self, lang: Lang) -> str:
        """The family's name as the index lists it."""
        return self.name_en if lang == "en" else self.name_es

    def of(self) -> str:
        """The Spanish "de" phrase for the family: "de ISO 3743", "del Anexo 16"."""
        article = self.family.article_es
        if article == "el":
            return f"del {self.name_es}"
        if article:
            return f"de {article} {self.name_es}"
        return f"de {self.name_es}"

    def about(self) -> str:
        """The Spanish "sobre" phrase for the family, with its article."""
        article = self.family.article_es
        return f"sobre {article} {self.name_es}" if article else f"sobre {self.name_es}"


def plan_families(headings: Sequence[str]) -> list[FamilyPage]:
    """Assign every English entry heading to its family, in index order.

    :param headings: The English entry headings, in registry order.
    :type headings: Sequence[str]
    :return: One page per family: standards by issuer and number, then every
        other source by slug, then the page of properties that are not errata.
    :rtype: list[FamilyPage]
    """
    families: dict[str, Family] = {}
    positions: dict[str, list[int]] = {}
    found: dict[str, list[Designation]] = {}
    for position, heading in enumerate(headings):
        family = family_of(heading)
        families.setdefault(family.slug, family)
        positions.setdefault(family.slug, []).append(position)
        if family.group == "standards":
            found.setdefault(family.slug, []).extend(
                d for d in designations(heading) if d.slug == family.slug
            )
    pages = []
    for slug, family in families.items():
        own = found.get(slug, [])
        if family.group == "standards":
            series = series_names(slug, own)
            name_en = _join(series, "en")
            name_es = _join(series, "es")
        else:
            name_en, name_es = family.name_en, family.name_es
        pages.append(
            FamilyPage(
                family=family,
                positions=tuple(positions[slug]),
                editions=tuple(editions_of(own)),
                name_en=name_en,
                name_es=name_es,
            )
        )
    rank = {"standards": 0, "other": 1, "not-errata": 2}
    return sorted(
        pages,
        key=lambda page: (
            rank[page.family.group],
            page.family.key or ("", 0, ""),
            page.family.slug,
        ),
    )


def _count(n: int, lang: Lang) -> str:
    if lang == "en":
        return f"{n} defect" if n == 1 else f"{n} defects"
    return f"{n} defecto" if n == 1 else f"{n} defectos"


def page_title(page: FamilyPage, lang: Lang) -> str:
    """The frontmatter title of a family page."""
    if page.family.group == "not-errata":
        return page.name(lang)
    return f"Errata in {page.name(lang)}" if lang == "en" else f"Erratas {page.of()}"


def search_title(page: FamilyPage) -> str | None:
    """The title the site search ranks a family page by, if not its own.

    A family page is titled after the document it is about ("Errata in VDI
    2081"), and the site search gives a title five times the weight of the
    text. Ranked by that title, a page whose title is a designation came above
    the guides written to the document on a search for it, which is the one
    search the site's ranking exists to win for those guides
    (``site/src/lib/search-ranking.mjs``); and ranked by the register's name,
    two of the 95 pages came above the registry's own index on a search for
    "errata". So the page is ranked by no title at all, an empty one: its text
    is indexed as any page's, which is what finds it for its document and the
    register's word together ("Allard Atalla errata"), and the search panel
    still shows its own title. The page of properties that are not errata
    names no document and keeps its title, at the weight :func:`search_weight`
    gives it.

    :param page: The family.
    :type page: FamilyPage
    :return: The ranking title, empty, or ``None`` to rank the page by its own.
    :rtype: str | None
    """
    if page.family.group == "not-errata":
        return None
    return ""


#: The weight the site search gives the page of properties that are not
#: errata, against 1 for every other page. It is the one page of the registry
#: ranked by its own title, and that title carries the register's word as the
#: index's does ("Propiedades de las fuentes que no son erratas"); at full
#: weight the shorter page came first for "erratas" and "registro de erratas".
#: At 0.8 the index is first for both, by 2 % and 3.5 %, and the page still
#: comes first for its own name ("not errata", "no son erratas"), by 1.6 % and
#: 40 %. Measured over the built index; ``check:search`` holds all six.
SEARCH_WEIGHT = 0.8


def search_weight(page: FamilyPage) -> float | None:
    """The search weight a family page is indexed at, if not the usual one.

    :param page: The family.
    :type page: FamilyPage
    :return: :data:`SEARCH_WEIGHT` for the page of properties that are not
        errata, ``None`` for every other page.
    :rtype: float | None
    """
    return SEARCH_WEIGHT if page.family.group == "not-errata" else None


def page_description(page: FamilyPage, lang: Lang) -> str:
    """The frontmatter description of a family page, unique by its name."""
    n = len(page.positions)
    name = page.name(lang)
    if page.family.group == "not-errata":
        if lang == "en":
            return (
                "Properties of the published sources that look like misprints "
                "and are not, recorded so that nobody corrects the library to "
                "match them."
            )
        return (
            "Propiedades de las fuentes publicadas que parecen erratas y no lo "
            "son, registradas para que nadie corrija la biblioteca para "
            "ajustarse a ellas."
        )
    if lang == "en":
        each = "about it" if n == 1 else "about each"
        return (
            f"Errata in {name}: {_count(n, lang)} in the printed text, with the "
            f"evidence and what phonometry does {each}."
        )
    each = "al respecto" if n == 1 else "con cada uno"
    return (
        f"Erratas {page.of()}: {_count(n, lang)} del texto impreso, con la "
        f"evidencia y lo que hace phonometry {each}."
    )


def _index_url(lang: Lang) -> str:
    prefix = "" if lang == "en" else "/es"
    return f"{SITE_BASE}{prefix}/{ERRATA_DIR}/"


def page_intro(page: FamilyPage, lang: Lang) -> str:
    """The paragraph a family page opens with, above its entries."""
    index = _index_url(lang)
    n = len(page.positions)
    if page.family.group == "not-errata":
        if lang == "en":
            return (
                f"The [errata registry]({index}) also records properties of "
                "the published sources that look like defects and are not: "
                "a difference the source discloses itself, a rounding it "
                "shares with its family, a value that is right for a form of "
                "the material the other books do not describe. They are kept "
                'here so that a future reader does not "fix" the library to '
                "match them."
            )
        return (
            f"El [registro de erratas]({index}) recoge también propiedades de "
            "las fuentes publicadas que parecen defectos y no lo son: una "
            "diferencia que la propia fuente declara, un redondeo que comparte "
            "con su familia, un valor correcto para una forma del material que "
            "los otros libros no describen. Se guardan aquí para que nadie, en "
            "el futuro, «corrija» la biblioteca para ajustarse a ellas."
        )
    if lang == "en":
        about = _join(list(page.editions), lang) if page.editions else page.name(lang)
        lead = (
            f"This is the entry of the [errata registry]({index}) on {about}."
            if n == 1
            else (
                f"These are the {n} entries of the [errata registry]({index}) "
                f"on {about}, in the order the registry lists them."
            )
        )
        return (
            f"{lead} The registry's introduction says how each claim is "
            "checked against the printed page and what the status of an entry "
            "means."
        )
    about = (
        f"sobre {_join(list(page.editions), lang)}" if page.editions else page.about()
    )
    lead = (
        f"Esta es la entrada del [registro de erratas]({index}) {about}."
        if n == 1
        else (
            f"Estas son las {n} entradas del [registro de erratas]({index}) "
            f"{about}, en el orden en que las recoge el registro."
        )
    )
    return (
        f"{lead} La introducción del registro explica cómo se comprueba cada "
        "afirmación contra la página impresa y qué significa el estado de una "
        "entrada. La redacción autoritativa es la inglesa; las citas "
        "textuales, las matemáticas y los valores impresos se reproducen sin "
        "traducir."
    )


def render_family(page: FamilyPage, edition: Edition, registry: Registry) -> str:
    """The whole text of one family page.

    :param page: The family.
    :type page: FamilyPage
    :param edition: The language to render.
    :type edition: Edition
    :param registry: That language's registry.
    :type registry: Registry
    :return: The page, newline-terminated.
    :rtype: str
    """
    lang = edition.lang
    body = "\n\n".join(registry.entries[position][1] for position in page.positions)
    ranked_by = search_title(page)
    weight = search_weight(page)
    search = f"searchTitle: {_yaml(ranked_by)}\n" if ranked_by is not None else ""
    if weight is not None:
        search += f"searchWeight: {weight}\n"
    return (
        "---\n"
        f"title: {_yaml(page_title(page, lang))}\n"
        f"description: {_yaml(page_description(page, lang))}\n"
        f"{search}"
        "---\n\n"
        f"{PAGE_MARKER.format(source=edition.source.name)}\n\n"
        f"{page_intro(page, lang)}\n\n"
        f"{body}\n"
    )


_GROUP_HEADINGS: dict[Group, dict[Lang, str]] = {
    "standards": {"en": "Standards", "es": "Normas"},
    "other": {
        "en": "Guidance, regulations, books and papers",
        "es": "Guías, reglamentos, libros y artículos",
    },
    "not-errata": {
        "en": "Properties that are not errata",
        "es": "Propiedades que no son erratas",
    },
}

_GROUP_LEADS: dict[Group, dict[Lang, str]] = {
    "standards": {
        "en": (
            "One page per series, which gathers its parts, its editions and "
            "its national adoptions."
        ),
        "es": (
            "Una página por serie, que reúne sus partes, sus ediciones y sus "
            "adopciones nacionales."
        ),
    },
    "other": {
        "en": "One page per document, named after its authors or its issuer.",
        "es": "Una página por documento, con el nombre de sus autores o de quien lo emite.",
    },
    "not-errata": {
        "en": (
            "Properties of the sources that look like misprints and are not, "
            "recorded so that nobody corrects the library to match them."
        ),
        "es": (
            "Propiedades de las fuentes que parecen erratas y no lo son, "
            "registradas para que nadie corrija la biblioteca para ajustarse "
            "a ellas."
        ),
    },
}

#: What the MDX index may not carry outside inline code: a brace opens a
#: JavaScript expression and ``<`` an element, so a stray one in the
#: registry's introduction would either fail the build or, worse, render
#: something other than the text.
_MDX_HAZARD = re.compile(r"[{}<]")


def _mdx_safe(text: str, *, where: str) -> str:
    for line_number, line in enumerate(text.splitlines(), start=1):
        prose = re.sub(r"`[^`]*`", "", line)
        if _MDX_HAZARD.search(prose):
            sys.exit(
                f"{where}, line {line_number}: {line.strip()!r} carries a brace "
                "or a '<' outside inline code, which MDX would read as code. "
                "The index page is MDX; keep the registry's introduction to "
                "plain markdown."
            )
    return text


def _attribute(text: str) -> str:
    """An MDX attribute value in double quotes."""
    if '"' in text:
        sys.exit(f"a family name with a double quote cannot be an attribute: {text!r}")
    return f'"{text}"'


def render_index_body(
    edition: Edition, registry: Registry, pages: Sequence[FamilyPage]
) -> str:
    """The generated part of the index page: introduction, then every family.

    :param edition: The language to render.
    :type edition: Edition
    :param registry: That language's registry.
    :type registry: Registry
    :param pages: Every family, in index order.
    :type pages: Sequence[FamilyPage]
    :return: The body, without the markers.
    :rtype: str
    """
    lang = edition.lang
    # From site/src/content/docs/<folder>/ up to site/src/: one step per folder
    # level, then docs/ and content/.
    components = "../" * (len(edition.folder.split("/")) + 2) + "components"
    out = [
        f"import ErrataFamily from '{components}/ErrataFamily.astro';",
        f"import ErrataRouter from '{components}/ErrataRouter.astro';",
        "",
        _mdx_safe(registry.preamble, where=f"docs/{edition.source.name}"),
    ]
    for group in ("standards", "other", "not-errata"):
        members = [page for page in pages if page.family.group == group]
        if not members:
            continue
        out += [
            "",
            f"## {_GROUP_HEADINGS[group][lang]}",
            "",
            _GROUP_LEADS[group][lang],
            "",
        ]
        out += [
            f"<ErrataFamily slug={_attribute(page.family.slug)} "
            f"name={_attribute(page.name(lang))} />"
            for page in members
        ]
    out += ["", "<ErrataRouter />"]
    return "\n".join(out)


def render_index(
    edition: Edition, registry: Registry, pages: Sequence[FamilyPage]
) -> str:
    """The whole index page: kept introduction, marker, generated body.

    :raises SystemExit: If the index page does not exist yet.
    """
    path = CONTENT / edition.index
    if not path.is_file():
        sys.exit(
            f"{path.relative_to(ROOT)}: missing. Create the page with its "
            "frontmatter and hand-written introduction first; this script only "
            "fills in the generated body below the marker."
        )
    kept = path.read_text(encoding="utf8")
    # Split on the marker's stable prefix so a reworded marker still matches.
    prefix = kept.split("{/* BEGIN GENERATED BODY", 1)[0].rstrip()
    marker = BEGIN.format(source=f"docs/{edition.source.name}")
    body = render_index_body(edition, registry, pages)
    return f"{prefix}\n\n{marker}\n\n{body}\n\n{END}\n"


# ---------------------------------------------------------------------------
# Edition parity.
# ---------------------------------------------------------------------------

#: First designation-like token of a heading: an optional alphabetic run glued
#: to its first digit, plus the digits and punctuation that follow. It reduces
#: "ISO 717-2:2020, Annex C, example C.1" and "ISO 717-2:2020, Anexo C,
#: ejemplo C.1" alike to ``717-2:2020``, and survives headings whose prose is
#: reordered in translation (``NORAH2``, ``S3.5-1997``, ``2015/996``).
#:
#: Deliberately excluded: the space-separated issuer word, because translation
#: moves and translates it ("Commission Directive (EU) 2015/996" is "Directiva
#: (UE) 2015/996 de la Comisión"), so requiring it would fail correct pairs.
#: The residual blind spot is a swap of two entries that share the numeric
#: token -- which, designations being what they are, means two entries about
#: the same document -- and such a swap cannot pair a heading with the wrong
#: source. ``tests/test_generate_site_reports.py`` pins both sides of this.
_DESIGNATION_RE = re.compile(r"[A-Za-z]*\d[\dA-Za-z.:/-]*")


def check_edition_parity(english: pathlib.Path, spanish: pathlib.Path) -> None:
    """Refuse to render while the Spanish edition drifts from the registry.

    ``docs/ERRATA.es.md`` is a hand-maintained, entry-for-entry translation of
    ``docs/ERRATA.md``. Three structural invariants survive translation and
    are enforced here: the two documents carry the same number of ``##``
    headings, in the same order, and each pair of headings names the same
    source document (its first designation token, :data:`_DESIGNATION_RE`).
    The wording of each entry is deliberately not compared: the English text
    is the authoritative one and the translation tracks it by hand.

    Because entry *i* of both editions lands on the same family page, these
    invariants are also what keeps every Spanish family page holding the same
    entries as its English twin.

    :param english: The English registry, ``docs/ERRATA.md``.
    :type english: pathlib.Path
    :param spanish: The Spanish edition, ``docs/ERRATA.es.md``.
    :type spanish: pathlib.Path
    :raises SystemExit: If the heading counts differ or any pair of headings
        disagrees on its designation token.
    """

    def headings(path: pathlib.Path) -> list[str]:
        lines = path.read_text(encoding="utf8").splitlines()
        return [line for line in lines if line.startswith("## ")]

    def shown(path: pathlib.Path) -> str:
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)

    en, es = headings(english), headings(spanish)
    if len(en) != len(es):
        sys.exit(
            f"{shown(spanish)}: {len(es)} entries against "
            f"{len(en)} in {shown(english)}. Translate the "
            "missing entry (or delete the stale one) so the editions match."
        )
    pairs = zip(en, es, strict=True)
    for index, (heading_en, heading_es) in enumerate(pairs, start=1):
        match_en = _DESIGNATION_RE.search(heading_en)
        match_es = _DESIGNATION_RE.search(heading_es)
        token_en = match_en.group(0) if match_en else None
        token_es = match_es.group(0) if match_es else None
        if token_en != token_es:
            sys.exit(
                f"{shown(spanish)}: entry {index} names "
                f"{token_es!r} where {shown(english)} names "
                f"{token_en!r}:\n  {heading_en}\n  {heading_es}\n"
                "The editions are out of order or an entry was mistranslated."
            )


# ---------------------------------------------------------------------------
# Writing.
# ---------------------------------------------------------------------------


def check_page_metadata(pages: Iterable[FamilyPage]) -> None:
    """Refuse a title or description the site would reject.

    :raises SystemExit: If a generated title or description is too long.
    """
    for page in pages:
        for lang in ("en", "es"):
            title = page_title(page, lang)
            description = page_description(page, lang)
            if len(title) > MAX_TITLE:
                sys.exit(
                    f"{page.family.slug} ({lang}): the title {title!r} is "
                    f"{len(title)} characters, over {MAX_TITLE}. Give the "
                    "source a shorter name in SOURCES."
                )
            if len(description) > MAX_DESCRIPTION:
                sys.exit(
                    f"{page.family.slug} ({lang}): the description is "
                    f"{len(description)} characters, over {MAX_DESCRIPTION}: "
                    f"{description!r}. Give the source a shorter name."
                )


def rendered_pages() -> dict[pathlib.Path, str]:
    """Every errata page this script owns, path to full text.

    :return: The index pages and every family page, both languages.
    :rtype: dict[pathlib.Path, str]
    """
    check_edition_parity(DOCS / "ERRATA.md", DOCS / "ERRATA.es.md")
    registries = {edition.lang: read_registry(edition) for edition in EDITIONS}
    headings = [heading for heading, _ in registries["en"].entries]
    pages = plan_families(headings)
    check_page_metadata(pages)
    out: dict[pathlib.Path, str] = {}
    for edition in EDITIONS:
        registry = registries[edition.lang]
        out[CONTENT / edition.index] = render_index(edition, registry, pages)
        for page in pages:
            path = CONTENT / edition.folder / f"{page.family.slug}.md"
            out[path] = render_family(page, edition, registry)
    return out


def stale_pages(expected: Iterable[pathlib.Path]) -> list[pathlib.Path]:
    """Family pages this script wrote once and would not write now.

    Only a page carrying :data:`PAGE_MARKER` is this script's; anything else in
    the folder was written by hand and is never touched.
    """
    keep = set(expected)
    found = []
    for edition in EDITIONS:
        folder = CONTENT / edition.folder
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.md")):
            if path in keep:
                continue
            if "Generated from docs/ERRATA" in path.read_text(encoding="utf8"):
                found.append(path)
    return found


def main(argv: list[str] | None = None) -> int:
    """Write every errata page, reporting what changed.

    :param argv: Command-line arguments (defaults to :data:`sys.argv`).
    :type argv: list[str] | None
    :return: ``0`` on success, ``1`` when ``--check`` finds a stale page.
    :rtype: int
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit non-zero if any page is out of date",
    )
    args = parser.parse_args(argv)

    pages = rendered_pages()
    stale: list[str] = []
    for path, text in pages.items():
        if path.is_file() and path.read_text(encoding="utf8") == text:
            continue
        stale.append(str(path.relative_to(CONTENT)))
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf8")
    for path in stale_pages(pages):
        stale.append(f"{path.relative_to(CONTENT)} (no longer generated)")
        if not args.check:
            path.unlink()

    if args.check and stale:
        print(
            "Generated site pages are out of date; run `make site-reports`:",
            file=sys.stderr,
        )
        for target in stale:
            print(f"  site/src/content/docs/{target}", file=sys.stderr)
        return 1

    verb = "stale" if args.check else "written"
    print(f"[site-reports] {len(pages)} pages checked, {len(stale)} {verb}")
    for target in stale:
        print(f"  {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
