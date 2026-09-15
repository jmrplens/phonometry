#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Splitting a citation string into the documents it names.

Every check registers one free-text citation: ``IEC 61260-1:2014 Table 1``,
``Long, Architectural Acoustics 2e, Table 8.1``, ``Ainslie (2010) §11.4.6``.
Read as a whole string, seven clauses of one book are seven documents, which is
how the report came to publish a count of "standards" that counts citations.
Read as ``(designation, edition, clause)`` the seven are one document cited
seven times, and a row can be joined to the bibliography, filtered by issuing
body, or grouped by document.

A citation is not one document, though. ``IEC 61260:1995 / ANSI S1.11-2004
Table 1`` names the same table in two standards, ``ISO 3747:2010 Eq. 11 vs ISO
3741:2010 Eq. 21`` compares two methods, and ``IEC 651:1979 Table V (via BS
5969:1981)`` says which copy the numbers were read from. So a citation owns a
*list* of documents, :class:`Cited`, in the order it writes them, and every
consumer iterates it. There is no headline document to read instead, because
reading the first one and ignoring the rest is the defect this shape exists to
end.

The split is done by :func:`parse` and **verified**, not asserted:
:func:`recompose` rebuilds the citation from the list and must reproduce the
original string character for character, connectors included. A citation that
cannot be rebuilt carries its split explicitly in ``reference_overrides.txt``, a
two-way ratchet - a line that is no longer needed fails just as loudly as a
citation that is missing one - so the file can only shrink as the parser
improves.

``kind`` reuses the vocabulary the site bibliography already declares in
``site/src/content.config.ts`` (``standard``, ``book``, ``article``,
``report``, ``web``) and adds ``derivation`` for the checks that cite no
document at all: a closed form synthesised to a known result, such as "All-pass
decomposition of a pure latency", is evidence, but it is not a citation.
"""

from __future__ import annotations

import dataclasses
import enum
import functools
import pathlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

#: The ratchet. One document per line, tab-separated, holding the split the
#: parser cannot derive: ``cite<TAB>kind<TAB>designation<TAB>edition<TAB>clause``
#: for a citation naming one document, and the seven-field form
#: ``...<TAB>lead<TAB>written`` on consecutive lines for a citation naming
#: more. An empty field is written as ``-``.
OVERRIDES_PATH = pathlib.Path(__file__).with_name("reference_overrides.txt")


class ReferenceKind(enum.StrEnum):
    """What sort of document a check cites."""

    STANDARD = "standard"
    BOOK = "book"
    ARTICLE = "article"
    REPORT = "report"
    WEB = "web"
    DERIVATION = "derivation"


class Relation(enum.StrEnum):
    """Why a citation names a further document, read off the connector.

    The citation says this much and no more, so the relation is taken from the
    words it is written with and never inferred from what the documents are.
    """

    #: " / " or " + ": the same value is printed in both documents.
    CORROBORATES = "corroborates"
    #: " vs " or " against ": the check compares what the two of them give.
    COMPARES = "compares"
    #: " via ", " per " or " (via ": the number was read through this one.
    VIA = "via"
    #: " with ", " and ": the check runs the clause with what this document
    #: prints, an input it supplies or a rule it states.
    SUPPLIES = "supplies"
    #: " (...)": named in passing, as the apparatus, the input or the source.
    MENTIONS = "mentions"


@dataclass(frozen=True)
class Cited:
    """One document a citation names, and the place inside it."""

    kind: ReferenceKind
    #: Always written out: ``ISO 16283-2``, never the ``-2`` the string writes.
    designation: str
    edition: str | None
    #: This document's own place, never the one that follows it.
    clause: str | None
    #: The literal text that introduces it, empty for the first document.
    lead: str = ""
    #: What that text says, ``None`` for the first document.
    relation: Relation | None = None
    #: What the citation writes, when it differs from the designation.
    written: str | None = None


@dataclass(frozen=True)
class Reference:
    """One citation, split into the documents it names."""

    cite: str
    documents: tuple[Cited, ...]
    #: The literal text after the last document, a closing bracket or nothing.
    tail: str = ""


def documents(reference: Reference) -> tuple[Cited, ...]:
    """Every document one citation names, in the order it writes them.

    The one way to read a reference. A consumer that wants "the" document of a
    check is asking a question the citation does not answer: ``ISO
    16283-1:2014 Clause 8.1 / -2:2020 Clause 8.1 / -3:2016 Clause 7.3.1`` is
    three documents and the check is about all three.

    :param reference: The split citation.
    :return: Its documents.
    """
    return reference.documents


# Issuing bodies whose designations the parser recognises. A citation opening
# with one of these is a standard, a regulation or an official report; the list
# is explicit rather than a pattern because "AS" and "RD" are also English and
# Spanish words, and a guess here silently changes what `counts` counts.
#
# Some entries name a body and the series it publishes in, "ECAC Doc" or
# "SAE ARP", because the number alone does not identify the document: Doc 29 is
# the airport-noise method and Doc 32 the rotorcraft one, and reading the body
# as the designation filed both under "ECAC Doc" as though they were one book.
# The rule for the ones that follow is the same as for the bodies: a fixed
# prefix that every citation of that series is written with. Longest first,
# since the alternation takes the first branch that matches.
_BODIES = (
    "BS EN ISO",
    "BS EN",
    "UNE-EN ISO",
    "EN ISO",
    "ISO/IEC Guide",
    "ISO/IEC",
    "ISO/PAS",
    "ISO/TR",
    "ISO/TS",
    "ISO",
    "IEC/TR",
    "IEC",
    "CEN/TS",
    "EN",
    "CEN",
    "ANSI/ASA",
    "ANSI",
    "ASTM",
    "ASA WG",
    "ASA",
    "AES",
    "EBU Tech",
    "EBU R",
    "EBU",
    "ITU-R",
    "ITU-T",
    "ECMA",
    "SAE ARP",
    "SAE",
    "ARP",
    "ICAO Annex",
    "ICAO Doc",
    "ICAO",
    "SMPTE",
    "IEEE",
    "NIST",
    "ASHRAE",
    "VDI",
    "NT ACOU",
    "NORDTEST",
    "DIN",
    "BS",
    "NF",
    "UNE",
    "JIS A",
    "JIS",
    "NASA CR",
    "NASA",
    "ECAC Doc",
    "ECAC",
    "FAA",
    "FHWA",
    "EASA",
    "WHO",
    "NIOSH",
    "OSHA",
    "MIL",
    "CTE",
    "RD",
    "Directive (EU)",
    "Directive",
    "Regulation",
    "Reglamento",
    "Recommendation",
    "Real Decreto",
)

#: Bodies whose documents are reports rather than standards: they are published
#: findings, not normative texts, and the bibliography types them accordingly.
_REPORT_BODIES = frozenset(
    {"NASA", "ECAC", "FAA", "FHWA", "EASA", "WHO", "NIOSH", "OSHA"}
)

#: Works cited as ``Author (year)`` or ``Series number (year)`` whose kind the
#: citation string cannot say. The year form reads as an article, which is
#: right for a paper and wrong for a book or a published report, and nothing in
#: "Barron (2003)" tells the two apart. Keyed by designation and edition, so
#: that one author's book and paper stay apart: "Harris 1978" is the windows
#: paper and "Harris (1991)" the noise control manual. An entry names a work
#: whose kind was read off the document itself. A work also cited bare, as
#: Vigran is, is declared in :data:`_WORKS` as well, and the two declarations
#: have to agree: the artefact gate holds every record filed under the name to
#: the kind :data:`_WORKS` gives it.
_DATED_WORK_KINDS: dict[tuple[str, str], ReferenceKind] = {
    ("Barron", "(2003)"): ReferenceKind.BOOK,
    ("Bies, Hansen and Howard", "(2017)"): ReferenceKind.BOOK,
    ("Fuchs", "(2013)"): ReferenceKind.BOOK,
    ("Hansen", "(2005)"): ReferenceKind.BOOK,
    ("Harris", "(1991)"): ReferenceKind.BOOK,
    ("Schirmer", "(2006)"): ReferenceKind.BOOK,
    ("Ver and Beranek", "(2006)"): ReferenceKind.BOOK,
    ("Vigran", "(2008)"): ReferenceKind.BOOK,
    ("AGH report 5.5.130.", "(2023)"): ReferenceKind.REPORT,
    ("AGH report 5.5.130.680", "(2017)"): ReferenceKind.REPORT,
    ("IFA-LSA 01-234", "(2020)"): ReferenceKind.REPORT,
    ("IFA-LSA 01-243", "(2014)"): ReferenceKind.REPORT,
    ("INSHT NTP 668", "(2004)"): ReferenceKind.REPORT,
    ("NPL CIRA(EXT) 009", "(1996)"): ReferenceKind.REPORT,
    ("Probst", "(2006)"): ReferenceKind.REPORT,
    ("SGS-CSTC report SDHL260400706101HI", "(2026)"): ReferenceKind.REPORT,
    ("Suva 66008.f", "(2006)"): ReferenceKind.REPORT,
    ("Suva 66026.d", "(2010)"): ReferenceKind.REPORT,
}

_BODY_ALTERNATION = "|".join(re.escape(body) for body in _BODIES)

#: ``IEC 61260-1:2014 Table 1`` - body, designation, optional edition, clause.
#: The designation stops at the first space that is followed by something that
#: is not part of a designation token, which the non-greedy run plus the
#: optional edition group achieves. The edition takes an amendment marker,
#: because ``ISO 10140-5:2010+A1`` otherwise matches no year at all and the
#: whole of ``10140-5:2010+A1`` falls into the clause, leaving the bare body as
#: the document.
#:
#: The year is anchored to a century, because a series number is written the
#: same way an edition is: ``NASA CR-3406`` read with four loose digits is the
#: body "NASA CR" issued in the year 3406, and the document number is gone.
#: Nothing else moves by it - no citation in the tree names an edition outside
#: 1900-2099 - and ``ISO 10140-5:2010+A1`` and ``DIN 45669-1:2010-09`` read as
#: they did.
#:
#: The clause may follow a comma, because that is how a citation writes the
#: copy it was read on: "BS EN 16487:2014, printed folio 14, PDF page 16" read
#: with a space alone stops the designation at the body and files the document
#: number in the clause. The rebuild already writes that pair of separators.
#:
#: Two more shapes a German designation is written in. The edition takes a
#: month, because DIN and VDI identify an edition by it: ``DIN 45669-1:2010-09``
#: matched no edition at all while the group stopped at the year, and fell
#: back to the bare body. And a sheet, part or corrigendum number belongs to
#: the designation, ``VDI 2081 Blatt 1`` and ``DIN 45669-1 Ber 1`` being
#: documents of their own with dates of their own: read as the start of the
#: clause, both sheets of VDI 2081 were one designation with no edition.
_STANDARD = re.compile(
    rf"^(?P<designation>(?:{_BODY_ALTERNATION})[ ]?[A-Za-z]?[\w./()-]*?"
    r"(?:\s(?:Blatt|Teil|Ber|Berichtigung)\s\d+)?)"
    r"(?:(?P<sep>[:-])(?P<edition>(?:19|20)\d{2}(?:-(?:0[1-9]|1[0-2]))?"
    r"(?:\+A\d+)?))?"
    r"(?:,?\s+(?P<clause>\S.*))?$"
)

#: ``Long, Architectural Acoustics 2e, Table 8.1`` - an edition marker splits
#: the work from the place in it. ``2e``, ``4th ed``, ``6e`` all appear.
_EDITION = re.compile(
    r"^(?P<designation>.+?)\s+(?P<edition>\d+(?:e|nd ed|rd ed|th ed|st ed))"
    r"(?:(?:,\s+|\s+)(?P<clause>\S.*))?$"
)

#: The authors a work is cited by, which is where the only comma a designation
#: may carry sits: "Bies, Hansen and Howard" is three names and one book. The
#: comma continues the list only when a further name follows it, which is what
#: keeps "(W. C. Sabine, 1922)" and "(Acustica 65, 1988, Formula 18)" from
#: reading the year after the comma as the edition of the words before it.
_AUTHORS = r"[A-Z](?:[^,]|,\s(?=[A-Z]))*?"

#: ``Havelock 2008 Part I Ch. 6`` / ``Vigran (2008) Eqs. (9.18)-(9.20)`` - an
#: author (or authors) then the year the work is cited by.
_YEAR = re.compile(
    rf"^(?P<designation>{_AUTHORS})\s+(?P<edition>\(?(?:19|20)\d{{2}}\)?)"
    r"(?:(?:,\s+|\s+)(?P<clause>\S.*))?$"
)

#: Words that open the "where in the document" half of a citation. A citation
#: with no edition is split here instead, so ``Fastl & Zwicker Eq (10.2)``
#: still names one work rather than one more.
_CLAUSE_OPENERS = (
    "Eq",
    "Eqs",
    "Equation",
    "Ch",
    "Chapter",
    "Sec",
    "Secs",
    "Sect",
    "Sects",
    "Section",
    "Table",
    "Tables",
    "Fig",
    "Figs",
    "Figure",
    "App",
    "Appendix",
    "Annex",
    "Clause",
    "clause",
    "Formula",
    "Formulas",
    "Part",
    "Example",
    "Ejemplo",
    "Art",
    "Article",
    "p",
    "pp",
    "Note",
)

_CLAUSE_ALTERNATION = "|".join(re.escape(word) for word in _CLAUSE_OPENERS)

_CLAUSE_START = re.compile(
    rf"^(?P<designation>.+?),?\s+(?P<clause>(?:{_CLAUSE_ALTERNATION})\b.*|§.*)$"
)

#: The place in a document, read on its own rather than after a work's title.
_CLAUSE_ONLY = re.compile(rf"^(?:(?:{_CLAUSE_ALTERNATION})\b|§)")


# --------------------------------------------------------------------------
# The connectors a citation writes between two documents
# --------------------------------------------------------------------------

#: The closed vocabulary, each with what it says and the text that closes it.
#: A connector that opens another comes first, since the alternation takes the
#: first branch that matches: "(via" would otherwise be read as a bare bracket
#: followed by a work called "via". It is closed on purpose: arbitrary prose
#: before a bracket would make "Poiseuille limit (Stinson 1991)" two documents,
#: and a citation is split only where one of these introduces something that
#: *opens like a document*, which is what keeps "Normal modes vs ideal
#: waveguide" whole.
#:
#: The lowercase phrase the last entry allows is what reads "(coupler, IEC
#: 60303)" and "(artificial ear, IEC 60318)" with no special case: the
#: qualifier is part of the lead, so the rebuild puts it back.
_LEADS: tuple[tuple[str, Relation, str], ...] = (
    (r" \(via ", Relation.VIA, ")"),
    (r" against ", Relation.COMPARES, ""),
    (r" via ", Relation.VIA, ""),
    (r" per ", Relation.VIA, ""),
    (r" vs ", Relation.COMPARES, ""),
    (r" / ", Relation.CORROBORATES, ""),
    (r" \+ ", Relation.CORROBORATES, ""),
    (r" with ", Relation.SUPPLIES, ""),
    (r", and ", Relation.SUPPLIES, ""),
    (r" and ", Relation.SUPPLIES, ""),
    (r" in ", Relation.VIA, ""),
    (r", as ", Relation.MENTIONS, ""),
    (r"; ", Relation.MENTIONS, ")"),
    (r" \((?:[a-z][a-z ]*, )?", Relation.MENTIONS, ")"),
)

#: The connectors written as ordinary words, which a work's own name can
#: carry: "Ver and Beranek" is one book, "Noise Control in Industry" one more,
#: and "Acoustics and Noise Control" a third. A citation is still split on
#: them, because the span on either side has to read as a document for the
#: split to happen at all, but finding one of them inside a designation says
#: nothing, where a "/" or a "vs" inside one is a name that swallowed a
#: document.
_PROSE_LEADS = frozenset({" with ", ", and ", " and ", " in ", ", as "})


_LEAD_RE = re.compile(
    "|".join(
        f"(?P<lead{index}>{pattern})" for index, (pattern, _, _) in enumerate(_LEADS)
    )
)


def _lead_of(match: re.Match[str]) -> tuple[str, Relation, str]:
    """The literal connector a match found, what it says, and its closer."""
    index = next(
        number for number, group in enumerate(match.groups()) if group is not None
    )
    _, relation, tail = _LEADS[index]
    return match.group(), relation, tail


def relation_for(lead: str) -> Relation | None:
    """What a connector says, read from the connector alone.

    The one mapping from the text to the relation, so the ratchet file and the
    artefact gate answer the question the parser answered.

    :param lead: The literal text introducing a document, ``""`` for the first.
    :return: The relation, or ``None`` when there is no connector at all.
    """
    if not lead:
        return None
    for pattern, relation, _ in _LEADS:
        if re.fullmatch(pattern, lead):
            return relation
    return None


@dataclass(frozen=True, slots=True)
class _Work:
    """A work the reader knows by name, and what the corpus records it as.

    ``designation`` is what the bibliography carries, which is not always what
    the citation writes: "(NORAH2 Eq. 8)" names the report the corpus records
    as "NORAH2 guidance", exactly as "-3:2016" names ISO 16283-3. The name the
    citation writes goes into the document's :attr:`Cited.written`, so the
    rebuild still reproduces the string it came from.
    """

    kind: ReferenceKind
    designation: str


#: Works the corpus cites bare, with neither an edition mark nor a year, behind
#: a connector: "Hopkins Eq. 2.201 / Bies Eq. 7.3", "UNESCO/Chen-Millero vs
#: Mackenzie". Nothing in the shape of those names says they are documents, so
#: they are listed, and the list is committed here rather than gathered from
#: the corpus: the artefact is a function of the source tree and nothing else,
#: and a rule that learned the names from the checks would tie a committed
#: field to the order the domains happen to be imported in.
#:
#: The kind is declared here and nowhere else. A name is also readable by the
#: rules that need no list - "Mackenzie (1981) nine-term equation" is an author
#: and a year - and those rules judge by shape alone, so a work read both ways
#: was filed under two kinds in the same artefact. The kinds below win over the
#: shape, and the artefact gate fails on a record that disagrees with them.
#:
#: Membership: a work the corpus cites bare, undated, behind a connector, at
#: least once. A new multi-document citation that names a work which is not
#: here fails the class test in tests/test_conformance_artifact.py, and the fix
#: is a line here.
_WORKS: dict[str, _Work] = {
    "Mackenzie": _Work(ReferenceKind.ARTICLE, "Mackenzie"),
    "Hopkins": _Work(ReferenceKind.BOOK, "Hopkins"),
    "Ainslie": _Work(ReferenceKind.BOOK, "Ainslie"),
    "Vigran": _Work(ReferenceKind.BOOK, "Vigran"),
    "Bies": _Work(ReferenceKind.BOOK, "Bies"),
    "NORAH2": _Work(ReferenceKind.REPORT, "NORAH2 guidance"),
}

#: Longest first, so a name that opens another is tried after it.
_WORK_NAMES = tuple(sorted(_WORKS, key=len, reverse=True))

#: The declared kind of each named work, keyed by the designation it is
#: recorded under rather than by the name a citation writes.
_WORK_KINDS: dict[str, ReferenceKind] = {
    work.designation: work.kind for work in _WORKS.values()
}


def work_kinds() -> dict[str, ReferenceKind]:
    """What the reader declares each work it knows by name to be.

    The one mapping, so the artefact gate can ask of the committed record the
    question the parser answered when it wrote it.

    :return: Declared kind by designation.
    """
    return dict(_WORK_KINDS)


def expansion_of(written: str, previous: Cited) -> str:
    """The designation a shorthand expands to.

    Two shorthands are written. A sibling part expands against the series
    before it, so "-3:2016" after ISO 16283-1 is ISO 16283-3. A work the
    reader knows by name expands to the designation declared for it, and owes
    nothing to the document before it.

    :param written: The shorthand the citation writes.
    :param previous: The document written before it.
    :return: The designation the shorthand names.
    """
    work = _WORKS.get(written)
    if work is not None:
        return work.designation
    return series_stem(previous.designation) + written


#: A number that identifies a document, guarded against the ordinal in
#: "AES 108th Conv.", which is a conference and not a document of the AES.
_DOCUMENT_NUMBER = re.compile(r"\d+(?!\d)(?!st\b|nd\b|rd\b|th\b)")

#: ``-3:2016``: a sibling part, written the short way once its series is known.
_RELATIVE_PART = re.compile(
    r"^(?P<written>-\d+)(?::(?P<edition>(?:19|20)\d{2}))?(?:\s+(?P<clause>\S.*))?$"
)

#: The part number a series designation ends with, which a sibling replaces.
_SERIES_PART = re.compile(r"-\d+$")

#: An author with the year or the edition their work is cited by. The comma is
#: load-bearing: without it "(Acustica 65, 1988, Formula 18)" reads as a work
#: called "Acustica 65" published in 1988, and "(W. C. Sabine, 1922)" as a
#: second Sabine.
_AUTHOR_HEAD = re.compile(
    rf"^{_AUTHORS}\s(?:\(?(?:19|20)\d{{2}}\)?(?!\w)"
    r"|\d+(?:e|st ed|nd ed|rd ed|th ed)\b)"
)


def series_stem(designation: str) -> str:
    """The series a numbered part belongs to: ``ISO 16283-1`` to ``ISO 16283``.

    :param designation: A document's designation.
    :return: The designation without its trailing part number, unchanged when
        it has none.
    """
    return _SERIES_PART.sub("", designation)


def _rebuilt(document: Cited, joiners: tuple[str, str]) -> str:
    """One document written back out with one pair of separators."""
    parts = [document.written or document.designation]
    if document.edition is not None:
        parts.append(document.edition)
    if document.clause is not None:
        parts.append(document.clause)
    text = parts[0]
    for part, joiner in zip(parts[1:], joiners, strict=False):
        text += joiner + part
    return text


def _rebuilds(document: Cited, span: str) -> bool:
    """Whether a document accounts for every character of the span it came
    from.
    """
    return any(_rebuilt(document, joiners) == span for joiners in _JOINERS)


def _accepted(document: Cited, span: str) -> bool:
    """Whether a reading of a span is one the split may keep.

    It has to rebuild the span, and it has to leave the name whole: a reading
    that rebuilds by cutting a title inside a phrase is refused, so the next
    reading, or in the end the whole string, is taken instead.
    """
    return _is_whole(document.designation) and _rebuilds(document, span)


def recompose(reference: Reference) -> str:
    """Rebuild the citation string from the documents it was split into.

    The verification the whole split rests on, and it is stricter than the one
    it replaces: every document has to account for its own span, where before
    anything at all could sit in a single ``clause`` and still rebuild. Only
    the separators a citation is actually written with are tried - ``:`` and
    ``-`` before a standard's year, a comma or a space before a clause - and
    the connectors are written back verbatim, so a rebuild that succeeds proves
    the list carries every character of the original in the original order.

    :param reference: The split to rebuild.
    :return: The citation, or the empty string when the list does not
        reproduce it.
    """
    rebuilt = ""
    for document in reference.documents:
        rebuilt += document.lead
        piece = _fitted(document, reference.cite, len(rebuilt))
        if piece is None:
            return ""
        rebuilt += piece
    rebuilt += reference.tail
    return rebuilt if rebuilt == reference.cite else ""


def _fitted(document: Cited, cite: str, offset: int) -> str | None:
    """The document written back out where the citation writes it.

    The separator pairs differ in what they put where, so at most one of them
    can sit at a given offset; the equality :func:`recompose` ends with is what
    proves nothing was dropped or moved.
    """
    for joiners in _JOINERS:
        candidate = _rebuilt(document, joiners)
        if cite.startswith(candidate, offset):
            return candidate
    return None


#: Separator pairs tried when rebuilding: first before the edition, then before
#: the clause. Ordered so the commonest shape is found first.
_JOINERS: tuple[tuple[str, str], ...] = (
    (":", " "),
    ("-", " "),
    (" ", " "),
    (" ", ", "),
    (":", ", "),
    ("-", ", "),
    (", ", ", "),
)


def _kind_for(designation: str) -> ReferenceKind:
    """Classify a designation that opens with a known issuing body.

    The body ends at a space or at the hyphen a report number is joined to it
    with, as in ``FHWA-PD-96-046``.
    """
    body = re.split(r"[ -]", designation, maxsplit=1)[0]
    if body in _REPORT_BODIES:
        return ReferenceKind.REPORT
    return ReferenceKind.STANDARD


def _as_standard(span: str) -> Cited | None:
    """Split a span that opens with a recognised issuing body."""
    match = _STANDARD.match(span)
    if match is None:
        return None
    return Cited(
        kind=_kind_for(match["designation"]),
        designation=match["designation"],
        edition=match["edition"],
        clause=match["clause"],
    )


def _declared(
    written: str, shape: ReferenceKind
) -> tuple[str, str | None, ReferenceKind]:
    """A work name as the corpus records it: designation, name written, kind.

    An author with a year looks like an article and an author with an edition
    mark like a book, which is the best a rule reading the string alone can
    do, and it is wrong often enough to matter: Mackenzie (1981) is a journal
    paper cited bare elsewhere, Ainslie (2010) a book cited with its year. So
    a work named in :data:`_WORKS` is what that list says it is, and the shape
    decides only for the works no list mentions.

    The name a citation writes is not always the designation the corpus files
    the work under: "NORAH2 (2015)" names the report recorded as "NORAH2
    guidance". :data:`_WORK_KINDS` is keyed by the designation, so reading it
    with the written name would miss that one and file the report as an
    article under a designation nothing else cites. The written name is looked
    up first and carries the expansion with it, exactly as :func:`_as_work`
    does for the same name without a year.
    """
    work = _WORKS.get(written)
    if work is not None:
        expanded = written if work.designation != written else None
        return work.designation, expanded, work.kind
    return written, None, _WORK_KINDS.get(written, shape)


def _as_edition(span: str) -> Cited | None:
    """Split a span carrying a book edition marker (``2e``, ``4th ed``)."""
    match = _EDITION.match(span)
    if match is None:
        return None
    designation, written, kind = _declared(match["designation"], ReferenceKind.BOOK)
    return Cited(
        kind=kind,
        designation=designation,
        edition=match["edition"],
        clause=match["clause"],
        written=written,
    )


def _as_year(span: str) -> Cited | None:
    """Split ``Author 1999 Eq. (17)`` or ``Author (2010) §11.4.6``.

    The kind is an article unless :data:`_DATED_WORK_KINDS` knows this edition
    of the work to be a book or a report, or :data:`_WORKS` declares the work.
    """
    match = _YEAR.match(span)
    if match is None:
        return None
    designation, written, kind = _declared(match["designation"], ReferenceKind.ARTICLE)
    return Cited(
        kind=_DATED_WORK_KINDS.get((match["designation"], match["edition"]), kind),
        designation=designation,
        edition=match["edition"],
        clause=match["clause"],
        written=written,
    )


def _as_clause(span: str) -> Cited | None:
    """Split an undated work from the clause word that follows it."""
    match = _CLAUSE_START.match(span)
    if match is None:
        return None
    designation, written, kind = _declared(match["designation"], ReferenceKind.BOOK)
    return Cited(
        kind=kind,
        designation=designation,
        edition=None,
        clause=match["clause"],
        written=written,
    )


def _as_work(span: str) -> Cited | None:
    """Read a span that opens with one of the works listed in :data:`_WORKS`.

    What follows the name has to be a place in it or nothing at all, which is
    what keeps "(Urick/Etter)" and "(NORAH2 prototype)" from being read as a
    document with a title after it. A name followed by a year or an edition
    mark needs no list: it is already a document by its shape.

    A work whose record carries a longer designation than the name the citation
    writes is expanded to it, the way a sibling part is, and the name goes into
    ``written``.
    """
    for name in _WORK_NAMES:
        work = _WORKS[name]
        written = name if work.designation != name else None
        if span == name:
            return Cited(
                kind=work.kind,
                designation=work.designation,
                edition=None,
                clause=None,
                written=written,
            )
        if not span.startswith(f"{name} "):
            continue
        rest = span[len(name) + 1 :]
        if _CLAUSE_ONLY.match(rest):
            return Cited(
                kind=work.kind,
                designation=work.designation,
                edition=None,
                clause=rest,
                written=written,
            )
    return None


def _as_relative(span: str, previous: Cited | None) -> Cited | None:
    """Read ``-3:2016`` as the sibling part of the series before it.

    The designation is written out, because a count and a bibliography need
    the document and not the shorthand; ``written`` keeps what the citation
    says, so the rebuild still reproduces it.
    """
    if previous is None:
        return None
    match = _RELATIVE_PART.match(span)
    if match is None:
        return None
    stem = series_stem(previous.designation)
    if stem == previous.designation:
        return None
    return Cited(
        kind=_kind_for(stem),
        designation=stem + match["written"],
        edition=match["edition"],
        clause=match["clause"],
        written=match["written"],
    )


def _splitters() -> tuple[Callable[[str], Cited | None], ...]:
    """The splitters, in the order they are tried."""
    return (_as_standard, _as_edition, _as_year, _as_clause, _as_work)


def _first_document(span: str) -> Cited | None:
    """The document a citation opens with."""
    for splitter in _splitters():
        document = splitter(span)
        if document is not None and _accepted(document, span):
            return document
    return None


def _heads(span: str, previous: Cited) -> Iterator[Cited]:
    """The readings under which a span *opens like a document*, in order.

    A connector decides nothing on its own: "ISO 7196:1995 Table 2 / A.3" and
    "ISO 8041-1:2017 Table 1 + Table B.3" write one between two places of one
    document. A citation is split only where what follows the connector opens
    one of these four ways.
    """
    # A body and a document number. The number is required: without it
    # "(ASHRAE end reflection, flush)" yields the designation "ASHRAE end" and
    # publishes it as a normative document.
    standard = _as_standard(span)
    if standard is not None and _DOCUMENT_NUMBER.search(standard.designation):
        yield standard
    # A sibling part of the series the document before it belongs to.
    relative = _as_relative(span, previous)
    if relative is not None:
        yield relative
    # An author with a year or an edition mark.
    if _AUTHOR_HEAD.match(span):
        for splitter in (_as_edition, _as_year):
            document = splitter(span)
            if document is not None:
                yield document
    # An undated work the reader is told about by name.
    work = _as_work(span)
    if work is not None:
        yield work


def _next_document(span: str, previous: Cited) -> Cited | None:
    """The document a connector introduced, or ``None`` if it introduced none."""
    for document in _heads(span, previous):
        if _accepted(document, span):
            return document
    return None


def _document(
    span: str, previous: Cited | None, lead: str, relation: Relation | None
) -> Cited | None:
    """One span of a citation, read as the document it names."""
    document = (
        _first_document(span) if previous is None else _next_document(span, previous)
    )
    if document is None:
        return None
    return dataclasses.replace(document, lead=lead, relation=relation)


def _next_split(
    cite: str, start: int, previous: Cited | None, lead: str, relation: Relation | None
) -> tuple[Cited, re.Match[str]] | None:
    """Where the span that starts at ``start`` ends, if it ends at all.

    A connector is a split only when the span before it reads as a document
    *and* the span after it opens like one, so a connector inside a locator or
    a title leaves the citation alone.
    """
    for match in _LEAD_RE.finditer(cite, start):
        current = _document(cite[start : match.start()], previous, lead, relation)
        if current is None:
            continue
        rest = cite[match.end() :]
        _, _, closer = _lead_of(match)
        if closer and rest.endswith(closer):
            rest = rest[: -len(closer)]
        if _next_document(rest, current) is None:
            continue
        return current, match
    return None


def _split(cite: str) -> Reference | None:
    """Read a citation as every document it names, left to right."""
    found: list[Cited] = []
    start, lead, relation, closer = 0, "", None, ""
    while True:
        split = _next_split(cite, start, found[-1] if found else None, lead, relation)
        if split is None:
            break
        current, match = split
        found.append(current)
        lead, relation, closer = _lead_of(match)
        start = match.end()
    text, tail = cite[start:], ""
    if closer and text.endswith(closer):
        text, tail = text[: -len(closer)], closer
    last = _document(text, found[-1] if found else None, lead, relation)
    if last is None:
        return None
    found.append(last)
    return Reference(cite=cite, documents=tuple(found), tail=tail)


def parse(cite: str, overrides: dict[str, Reference] | None = None) -> Reference:
    """Split one citation into the documents it names.

    :param cite: The citation exactly as the check registered it.
    :param overrides: The ratchet, keyed by citation; defaults to the committed
        file.
    :return: The split, guaranteed to rebuild the citation verbatim.
    """
    table = _load_overrides() if overrides is None else overrides
    recorded = table.get(cite)
    if recorded is not None:
        return recorded
    reference = _split(cite)
    if reference is not None and recompose(reference) == cite:
        return reference
    # No split survives the round trip, so the citation names no document at
    # all: a closed-form derivation, or a work whose title is the whole of it.
    return Reference(
        cite=cite,
        documents=(
            Cited(
                kind=ReferenceKind.DERIVATION,
                designation=cite,
                edition=None,
                clause=None,
            ),
        ),
    )


#: The tail a designation is left with when a split cuts it inside a phrase:
#: the comma or the conjunction that was joining it to what follows.
_CUT_TAIL = re.compile(r"(?:,|\s(?:and|or|against|with))$")


def _is_whole(designation: str) -> bool:
    """Whether a split left the designation a whole name.

    A split that rebuilds the citation can still cut it in the wrong place.
    "Poiseuille limit (Stinson 1991)" splits at the year into "Poiseuille
    limit (Stinson" and "1991)", and "Suva 66008.f, 8th revised edition,
    August 2006, Tableau 2 and Figure 7" splits at the clause word into a
    designation that ends in "and". Neither is a document. A designation with a
    parenthesis it never closes, or one that ends in a comma or a conjunction,
    is refused, and the next splitter, or in the end the whole string, is
    taken instead.

    :param designation: The document half of a candidate split.
    :return: ``False`` when the split cut the name.
    """
    if designation.count("(") != designation.count(")"):
        return False
    return _CUT_TAIL.search(designation) is None


@functools.cache
def _load_overrides() -> dict[str, Reference]:
    """Read the ratchet file, keyed by the citation it corrects.

    A citation naming more than one document is written as consecutive lines
    sharing the first field, in the order the citation writes them.

    Cached: :func:`parse` is called once per check, and re-reading a file 554
    times to answer the same question is 554 answers to one question.
    """
    if not OVERRIDES_PATH.is_file():
        return {}
    recorded: dict[str, list[tuple[Cited, int]]] = {}
    for number, line in enumerate(
        OVERRIDES_PATH.read_text(encoding="utf8").splitlines(), start=1
    ):
        if not line.strip() or line.startswith("#"):
            continue
        cite, document = _override_line(line, number)
        recorded.setdefault(cite, []).append((document, number))
    return {
        cite: _override_reference(cite, entries) for cite, entries in recorded.items()
    }


def _override_reference(cite: str, entries: list[tuple[Cited, int]]) -> Reference:
    """The documents of one citation, as its lines record them.

    :raises ValueError: If a line other than the first carries no connector,
        which would leave two documents with nothing written between them.
    """
    for document, number in entries[1:]:
        if not document.lead:
            msg = (
                f"{OVERRIDES_PATH.name}:{number}: the second and later "
                f"documents of a citation need the text that introduces them "
                f"in the lead field."
            )
            raise ValueError(msg)
    return Reference(cite=cite, documents=tuple(document for document, _ in entries))


def _override_line(line: str, number: int) -> tuple[str, Cited]:
    """Parse one ratchet line into its citation and one document of it.

    Five fields record a citation naming one document, seven a citation naming
    more, and the relation is derived from the connector rather than written
    out, so the file cannot record one the parser would read differently.

    :raises ValueError: If the line does not carry five or seven tab-separated
        fields, names a kind outside the vocabulary, or writes a connector that
        is not one the parser reads.
    """
    fields = line.split("\t")
    if len(fields) not in {5, 7}:
        msg = (
            f"{OVERRIDES_PATH.name}:{number}: expected 5 tab-separated fields "
            f"(cite, kind, designation, edition, clause), or 7 with (lead, "
            f"written) for a citation naming more than one document, found "
            f"{len(fields)}."
        )
        raise ValueError(msg)
    cite, kind, designation, edition, clause = fields[:5]
    lead, written = (fields[5], fields[6]) if len(fields) == 7 else ("-", "-")
    if kind not in tuple(ReferenceKind):
        msg = (
            f"{OVERRIDES_PATH.name}:{number}: kind {kind!r} is not one of "
            f"{[str(k) for k in ReferenceKind]}."
        )
        raise ValueError(msg)
    relation = None if lead == "-" else relation_for(lead)
    if lead != "-" and relation is None:
        msg = (
            f"{OVERRIDES_PATH.name}:{number}: lead {lead!r} is not a connector "
            f"the parser reads."
        )
        raise ValueError(msg)
    return cite, Cited(
        kind=ReferenceKind(kind),
        designation=designation,
        edition=None if edition == "-" else edition,
        clause=None if clause == "-" else clause,
        lead="" if lead == "-" else lead,
        relation=relation,
        written=None if written == "-" else written,
    )
