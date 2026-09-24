#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The conformance artefact says what the checks said, and stays saying it.

``docs/conformance.json`` is committed, so three properties have to hold or the
file is worse than no file: it must be a function of the source tree alone
(same tree, same bytes, on any machine), everything in it must be a built-in
type ``json.dumps`` can write, and the verdict it carries must be the verdict
the check decided at full precision rather than one re-derived from rounded
numbers.

The guards below are the ones that would otherwise fail somewhere far away: a
numpy scalar fails at serialisation, a non-finite value fails inside the site
build's ``JSON.parse``, a lost citation fragment fails as a wrong published
count, and a verdict re-derived at the boundary fails as a green report for a
check that does not pass.
"""

from __future__ import annotations

import json
import math
import pathlib
import re
import sys

import numpy as np
import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_conformance_artifact as gate
import conformance_report as cr
from conformance import artifact, compare, metrics, references, registry, units

#: A clause that opens with a sheet, part or corrigendum number, which belongs
#: to the designation of a standard rather than to the place inside it.
_SHEET_OPENER = re.compile(r"(?:Blatt|Teil|Ber|Berichtigung)\s+\d+\b")

#: An issuing body followed by a document number, anywhere in a string. The
#: number must not be an ordinal: "Farina 2000, AES 108th Conv." names the
#: conference Farina presented at, not a document of the Audio Engineering
#: Society.
_BODY_AND_NUMBER = re.compile(
    r"\b(?:"
    + "|".join(re.escape(body) for body in references._BODIES)
    + r")[ ]?[A-Za-z]?[\w./()-]*?\d+(?!\d)(?!st\b|nd\b|rd\b|th\b)"
)

#: ``/ -3:2016``: a sibling part of the series the document before it belongs
#: to, written the short way a citation writes it.
_RELATIVE_PART = re.compile(r"/\s*-\d+(?::(?:19|20)\d{2})?")

#: An author with the year or the edition their work is cited by.
_AUTHOR_AND_DATE = re.compile(
    r"\b[A-Z][^,]*?\s(?:\(?(?:19|20)\d{2}\)?(?!\w)"
    r"|\d+(?:e|st ed|nd ed|rd ed|th ed)\b)"
)

#: The connectors a citation writes between two documents in prose. The
#: bracket the reader also reads is left out on purpose: a bracket is how a
#: body writes its own name, as in "Directive (EU) 2015/996", and how a
#: descriptor is written in front of a work, as in "Poiseuille limit (Stinson
#: 1991)", which is a defect of its own in the same reader and not this one.
#: The reader's prose connectors are left out for the same reason: "and" and
#: "in" are words a title is written with, so what is left is the connectors
#: no name can carry.
_DOCUMENT_JOINER = re.compile(
    "|".join(
        pattern
        for pattern, relation, _ in references._LEADS
        if relation is not references.Relation.MENTIONS
        and pattern not in references._PROSE_LEADS
    )
)

#: A place inside a document, opening a clause. The reader's own vocabulary,
#: so the net asks the question the reader asks. The word boundary sits outside
#: the alternation, as it does in the reader: written inside it, it would bind
#: to the last opener alone and the bare "p" would then match the "prototype"
#: of "(NORAH2 prototype)", turning a descriptor into a document.
_CLAUSE_OPENER = (
    "(?:" + "|".join(re.escape(word) for word in references._CLAUSE_OPENERS) + r")\b|§"
)

#: The documentation tree whose frontmatter names every document a guide cites.
_DOCS = (
    pathlib.Path(__file__).resolve().parent.parent / "site" / "src" / "content" / "docs"
)

#: An edition identified by year and month, the way DIN and VDI identify one.
_MONTH_DATED = re.compile(r":(?:19|20)\d{2}-(?:0[1-9]|1[0-2])$")

#: One ``designation:`` line of a page's frontmatter reference list.
_FRONTMATTER_DESIGNATION = re.compile(r'^\s*designation:\s*"([^"]+)"', re.MULTILINE)

# One xdist worker runs this module with the report smoke tests: the registry
# memoizes each check per process, so building the document here and rendering
# the report there compute every check once instead of once per worker.
pytestmark = pytest.mark.xdist_group("conformance-report")


@pytest.fixture(scope="module")
def committed() -> dict:
    """The artefact as committed, which is what every consumer reads."""
    return artifact.load()


@pytest.fixture(scope="module")
def fresh() -> dict:
    """A document built from the registry in this process."""
    return artifact.build_document()


# --------------------------------------------------------------------------
# Types at the boundary
# --------------------------------------------------------------------------


def test_a_numpy_verdict_is_coerced_to_a_builtin_bool() -> None:
    """``numpy.bool_`` is not JSON-serialisable and nine checks produced one.

    ``numpy.float64`` subclasses ``float``, so a numpy scalar reaches
    :func:`numeric` with no annotation and no type checker objecting, and
    ``abs(delta) <= limit`` then hands back a ``numpy.bool_``. Coercing in the
    constructor is what catches the outcomes built by hand as well.
    """
    outcome = registry.Outcome(expected="1", computed="1", delta="0", passed=np.True_)
    assert type(outcome.passed) is bool
    assert outcome.verdict is registry.Verdict.PASS


def test_numeric_coerces_numpy_scalars_on_the_way_in() -> None:
    outcome = registry.numeric(np.float64(2.0), np.float64(2.5), np.float64(1.0))
    assert type(outcome.passed) is bool
    assert type(outcome.deviation.value) is float


def test_every_stored_number_is_a_builtin_float(committed: dict) -> None:
    """Checked with ``type(x) is float``, never ``isinstance``.

    ``isinstance(numpy.float64(1.0), float)`` is ``True``, so an isinstance
    test passes on exactly the value that breaks the write.
    """
    assert gate.validate(committed) == []


def test_the_committed_document_is_internally_consistent(committed: dict) -> None:
    counts = committed["counts"]
    assert counts["checks"] == len(committed["checks"])
    assert counts["passing"] + counts["failing"] == counts["checks"]
    assert counts["domains"] == len(committed["domains"])


# --------------------------------------------------------------------------
# Rounding, verdicts and reproducibility
# --------------------------------------------------------------------------


def test_the_verdict_survives_a_deviation_that_rounds_onto_its_limit() -> None:
    """The boundary case the stored verdict exists for.

    A deviation of 0.0499 against a limit of 0.05 passes at full precision and
    rounds to 0.05 at two decimals, where a consumer recomputing
    ``|deviation| <= tolerance`` would see equality and a consumer using ``<``
    would flip it. The artefact stores what the check decided.
    """
    outcome = registry.numeric(1.0, 1.0499, 0.05, places=2)
    assert outcome.verdict is registry.Verdict.PASS
    stored = artifact._rounded(outcome.deviation.value, 2)
    assert stored == pytest.approx(0.05)


def test_a_deviation_is_never_reported_coarser_than_three_decimals() -> None:
    """A distance printed to the foot still has a deviation of hundredths.

    Applying the value's precision to its deviation reported a real 0.036 ft as
    zero, which is the coarsening the per-check precision was meant to end.
    """
    outcome = registry.numeric(5280.0, 5280.036, 0.1, unit="ft", places=0)
    assert outcome.delta == "0.036 ft"
    assert registry.deviation_places(0) == 3
    assert registry.deviation_places(6) == 6


def test_negative_zero_is_normalised_away(committed: dict) -> None:
    """A rounded-down negative is ``-0.0``, which is not ``0.0`` to a byte diff.

    Both paths into the document normalise it, and the whole committed file is
    checked for the literal, because one occurrence is one byte a fresh run on
    another machine might not produce.
    """
    assert math.copysign(1.0, artifact._rounded(-0.0, 3)) > 0
    assert math.copysign(1.0, artifact._exact(-0.0)) > 0
    assert re.search(r"-0\.0(?=[,\n}])", artifact.dumps(committed)) is None


def test_a_value_smaller_than_its_precision_keeps_its_digits() -> None:
    """Rounding 4.2e-7 to five decimals would store a zero against a real limit."""
    assert artifact._rounded(4.2e-7, 5) == pytest.approx(4.2e-7)


def test_a_non_finite_value_fails_at_write_time() -> None:
    """``Infinity`` is not JSON and would throw inside the site build."""
    with pytest.raises(ValueError, match="non-finite value"):
        artifact._rounded(math.inf, 3)


def test_the_document_serialises_the_same_way_twice(fresh: dict) -> None:
    """Committed means reproducible: no timestamp, no SHA, no library version."""
    assert artifact.dumps(fresh) == artifact.dumps(artifact.build_document())


def test_the_document_carries_no_provenance_that_changes_by_itself(
    committed: dict,
) -> None:
    text = artifact.dumps(committed)
    assert "timestamp" not in text
    assert "numpy" not in text


# --------------------------------------------------------------------------
# The reference split
# --------------------------------------------------------------------------


def _first(cite: str) -> references.Cited:
    """The document a citation opens with, for the citations that name one."""
    return references.documents(references.parse(cite, overrides={}))[0]


def test_every_citation_rebuilds_from_its_split(committed: dict) -> None:
    """The whole split rests on this: a list of documents that cannot be
    reassembled into the original string, connectors and all, has lost or
    moved something, and the designation count is then counting the wrong
    thing.
    """
    overridden = gate._overridden()
    for check in committed["checks"]:
        reference = check["reference"]
        if reference["cite"] in overridden:
            continue
        rebuilt = references.recompose(
            references.Reference(
                cite=reference["cite"],
                documents=tuple(
                    references.Cited(
                        kind=references.ReferenceKind(document["kind"]),
                        designation=document["designation"],
                        edition=document.get("edition"),
                        clause=document.get("clause"),
                        lead=document.get("lead") or "",
                        relation=(
                            None
                            if document.get("relation") is None
                            else references.Relation(document["relation"])
                        ),
                        written=document.get("written"),
                    )
                    for document in reference["documents"]
                ),
                tail=reference.get("tail") or "",
            )
        )
        assert rebuilt == reference["cite"], check["id"]


def test_the_override_ratchet_carries_no_dead_lines(committed: dict) -> None:
    """A line for a citation nobody makes hides the next real one."""
    assert gate._ratchet_problems(committed) == []


# --------------------------------------------------------------------------
# A citation that names more than one document
# --------------------------------------------------------------------------


def _named(cite: str) -> list[tuple]:
    """Every document one citation names, read the only way there is.

    Each document as ``(kind, designation, edition, clause, lead, relation)``,
    in the order the citation writes them.
    """
    reference = references.parse(cite, overrides={})
    return [
        (
            str(document.kind),
            document.designation,
            document.edition,
            document.clause,
            document.lead,
            None if document.relation is None else str(document.relation),
        )
        for document in references.documents(reference)
    ]


def test_a_citation_names_every_document_it_writes() -> None:
    """The defect this closes: a citation naming two or three documents was
    filed under the first one, and the others never appeared as cited at all.

    ANSI S1.11, BS 5969, JIS A 1418-2 and EBU R 98 were named by a check and
    counted by nothing, while four guides carried ANSI S1.11-2004 in their
    bibliography. The clause of the second document sat inside the clause of
    the first, so the row could not be found by searching for the document it
    is about.
    """
    assert _named(
        "ISO 16283-1:2014 Clause 8.1 / -2:2020 Clause 8.1 / -3:2016 Clause 7.3.1"
    ) == [
        ("standard", "ISO 16283-1", "2014", "Clause 8.1", "", None),
        ("standard", "ISO 16283-2", "2020", "Clause 8.1", " / ", "corroborates"),
        ("standard", "ISO 16283-3", "2016", "Clause 7.3.1", " / ", "corroborates"),
    ]
    assert _named("IEC 61260:1995 / ANSI S1.11-2004 Table 1") == [
        ("standard", "IEC 61260", "1995", None, "", None),
        ("standard", "ANSI S1.11", "2004", "Table 1", " / ", "corroborates"),
    ]
    assert _named("ISO 16283-2:2020 Table A.1 / JIS A 1418-2:2019 Table A.2") == [
        ("standard", "ISO 16283-2", "2020", "Table A.1", "", None),
        ("standard", "JIS A 1418-2", "2019", "Table A.2", " / ", "corroborates"),
    ]
    assert _named("ISO 3747:2010 Eq. 11 vs ISO 3741:2010 Eq. 21") == [
        ("standard", "ISO 3747", "2010", "Eq. 11", "", None),
        ("standard", "ISO 3741", "2010", "Eq. 21", " vs ", "compares"),
    ]
    assert _named("IEC 651:1979 Table V (via BS 5969:1981)") == [
        ("standard", "IEC 651", "1979", "Table V", "", None),
        ("standard", "BS 5969", "1981", None, " (via ", "via"),
    ]


def test_a_trailing_clause_belongs_to_the_document_before_it() -> None:
    """The printed pages settle it. In ISO 10846-3:2002, 7.6 is the test for
    linearity; 7.6 of part 2 is "Measurements" and its test for linearity is
    7.7. A clause shared backwards would file the check against a clause that
    is about something else, so the first document is recorded with none.
    """
    assert _named("ISO 10846-2:2008 / -3:2002 7.6") == [
        ("standard", "ISO 10846-2", "2008", None, "", None),
        ("standard", "ISO 10846-3", "2002", "7.6", " / ", "corroborates"),
    ]


def test_every_connector_the_corpus_writes_is_read() -> None:
    """One citation per connector, and the relation each one records.

    The connector vocabulary is closed: a citation is split only where one of
    these introduces something that opens like a document, so "Normal modes vs
    ideal waveguide" and "ISO 7196:1995 Table 2 / A.3" stay whole.
    """
    assert _named("Cox & D'Antonio Eq (5.8) + ISO 17497-2 Formula (7)") == [
        ("book", "Cox & D'Antonio", None, "Eq (5.8)", "", None),
        ("standard", "ISO 17497-2", None, "Formula (7)", " + ", "corroborates"),
    ]
    assert _named("ISO 11690-3:1998 4.3 against ISO 14257 Annex C") == [
        ("standard", "ISO 11690-3", "1998", "4.3", "", None),
        ("standard", "ISO 14257", None, "Annex C", " against ", "compares"),
    ]
    assert _named("IEC 537:1976 (withdrawn) via NASA CR-3406 Table SLD-I") == [
        ("standard", "IEC 537", "1976", "(withdrawn)", "", None),
        ("report", "NASA CR-3406", None, "Table SLD-I", " via ", "via"),
    ]
    assert _named(
        "EBU Tech 3285:2011 (2.3): CodingHistory row per EBU R 98 Appendix 1"
    ) == [
        ("standard", "EBU Tech 3285", "2011", "(2.3): CodingHistory row", "", None),
        ("standard", "EBU R 98", None, "Appendix 1", " per ", "via"),
    ]
    assert _named("Moore, Psychology of Hearing 6e, p. 77 (Glasberg & Moore 1990)") == [
        ("book", "Moore, Psychology of Hearing", "6e", "p. 77", "", None),
        ("article", "Glasberg & Moore", "1990", None, " (", "mentions"),
    ]
    assert _named("ISO 389-1:1998 Table 1 (coupler, IEC 60303)") == [
        ("standard", "ISO 389-1", "1998", "Table 1", "", None),
        ("standard", "IEC 60303", None, None, " (coupler, ", "mentions"),
    ]


def test_a_relative_part_is_expanded_against_the_series_it_belongs_to() -> None:
    """ "-2:2020" is ISO 16283-2, and the count and the bibliography need it
    written out; the citation still has to rebuild from what it wrote, so the
    document keeps "-2" as well.
    """
    documents = references.documents(
        references.parse(
            "ISO 16283-1:2014 Formula (12) / -2:2020 Formula (15)", overrides={}
        )
    )
    assert [(document.designation, document.written) for document in documents] == [
        ("ISO 16283-1", None),
        ("ISO 16283-2", "-2"),
    ]


def test_a_single_document_is_not_split_by_its_own_locator() -> None:
    """A connector decides nothing on its own.

    Every one of these writes a connector between two places in one document,
    between two methods, or inside a title, and a reader that split on the
    word alone would invent a document for each.
    """
    for cite in (
        "ISO 7196:1995 Table 2 / A.3",
        "ANSI S1.4-1983 Tables IV/V",
        "ISO/PAS 1996-3:2022 3.5",
        "ISO/IEC Guide 98-3-1 clause 9.2",
        "ITU-R BS.468-4 Table 1",
        "RD 1367/2007 Annex I A.2 d",
        "Directive (EU) 2015/996 Appendix F, Tables F-2 and F-3",
        "UNESCO sound speed (EOS-80 canonical value)",
        "Farina 2000, AES 108th Conv. (THD from one sweep)",
        "Hopkins Eq. 2.229 (Leppington/Maidanik)",
        "Bies 5e Table 8.14 (ASHRAE end reflection, flush)",
        "ISO 2631-5:2018 Formula 1 vs Annex D Table D.1",
        "Allard & Atalla 2e Eq. (6.107) vs Sect. 11.5 assembly",
        "Normal modes vs ideal waveguide",
        "ISO 8041-1:2017 Table 1 + Table B.3",
        "ISO 14257:2001 Eq. (5) against Eq. (8)",
        "ISO 12999-2:2020 Clause 7, Examples 1/2",
        "Sabine (W. C. Sabine, 1922)",
    ):
        assert len(_named(cite)) == 1, cite


def test_a_series_read_on_its_own_keeps_its_number() -> None:
    """The documents a multi-document citation names have to survive being
    read alone, and three of them did not: the body took the whole designation
    and left the number in the clause.
    """
    for cite, split in (
        ("JIS A 1418-2:2019 Table A.2", ("JIS A 1418-2", "2019", "Table A.2")),
        ("EBU R 98 Appendix 1", ("EBU R 98", None, "Appendix 1")),
        ("NASA CR-3406 Table SLD-I", ("NASA CR-3406", None, "Table SLD-I")),
    ):
        document = references.documents(references.parse(cite, overrides={}))[0]
        read = (document.designation, document.edition, document.clause)
        assert read == split, cite


def test_every_named_work_is_earned_by_a_citation(committed: dict) -> None:
    """The undated works the reader knows by name are a ratchet of their own.

    A work is on the list because a citation names it behind a connector with
    neither an edition mark nor a year, which is the one shape no rule can
    read. An entry no citation uses any more is dead weight that hides the
    next real one, exactly as a stale override line is.

    The heads counted are only the ones the list could have produced, which
    means the ones with no edition. Asking for the name alone does not close
    the ratchet: an author cited "Mechel 2e" everywhere is read by the edition
    rule long before the list is consulted, so a "Mechel" entry would sit here
    unused and unnoticed. The name is taken as the citation writes it, since
    that is what the list is keyed by: a work whose record expands to a longer
    designation is earned by the short form the citation puts behind the
    connector.
    """
    heads = {
        document.get("written") or document["designation"]
        for check in committed["checks"]
        for document in check["reference"]["documents"]
        if document.get("lead") and document.get("edition") is None
    }
    assert sorted(set(references._WORKS) - heads) == []


def test_every_prose_connector_is_one_the_reader_reads() -> None:
    """The prose connectors are listed by the pattern the reader writes them
    as, so a connector reworded in one place and not the other would quietly
    stop being excluded from the net below, which would then turn red on the
    next book called "Ver and Beranek".
    """
    written = {pattern for pattern, _, _ in references._LEADS}
    assert sorted(references._PROSE_LEADS - written) == []


def test_no_document_carries_another_document(committed: dict) -> None:
    """The committed artefact, asked the question the reader was not.

    This is the net. It is deliberately more liberal than the reader: a
    citation that names a document the reader cannot recognise turns red here
    as soon as the corpus records that document anywhere, and the fix is a
    line in the tool, never a citation trimmed until it fits.
    """
    recorded = {
        document["designation"]
        for check in committed["checks"]
        for document in check["reference"]["documents"]
        if document["kind"] != "derivation"
    }
    swallowed = []
    for check in committed["checks"]:
        for document in check["reference"]["documents"]:
            clause = document.get("clause") or ""
            designation = document["designation"]
            if (
                _BODY_AND_NUMBER.search(clause)
                or _RELATIVE_PART.search(clause)
                or _AUTHOR_AND_DATE.search(clause)
            ):
                swallowed.append((check["reference"]["cite"], clause))
            # A derivation names no document: its designation is the whole
            # citation, prose and all, and "Passive sonar equation
            # (Urick/Etter)" credits two books inside one closed form.
            if document["kind"] == "derivation":
                continue
            if _DOCUMENT_JOINER.search(designation):
                swallowed.append((check["reference"]["cite"], designation))
            swallowed += [
                (check["reference"]["cite"], clause)
                for other in recorded - {designation}
                if _clause_names(other, clause)
            ]
    assert sorted(set(swallowed)) == []


def _clause_names(designation: str, clause: str) -> bool:
    """Whether a clause writes a recorded designation, whole or shortened.

    Asking for the whole designation leaves a blind spot exactly where the
    reader has one. A citation writes the name a reader would recognise and
    leaves the rest of the title off: the clause "flight-condition
    interpolation (NORAH2 Eq. 8)" named Eq. 8 of a second document while the
    designation on record is "NORAH2 guidance", so the full string never
    matched and the net stayed green over the last citation of the class.

    The shortened form only counts in front of a place in the document. That
    is what separates a document from a descriptor: "NORAH2 Eq. 8" is a clause
    of a report, "(NORAH2 prototype)" is a word about the model the check ran.
    """
    if re.search(rf"\b{re.escape(designation)}(?!\w)", clause):
        return True
    head = designation.split(" ", 1)[0]
    if head == designation:
        return False
    return bool(re.search(rf"\b{re.escape(head)}\s+(?:{_CLAUSE_OPENER})", clause))


def test_no_designation_stops_before_the_document_number(committed: dict) -> None:
    """A designation that names the series but not the document files two
    documents under one name. ECAC Doc 29 is the airport-noise method and Doc
    32 the rotorcraft one, and both were "ECAC Doc" until the parser learned
    the series prefixes; the bibliography then joined eighteen checks of two
    different documents onto one row.

    The tell is that a standard's number carries a digit and always follows the
    body, so a designation with no digit whose clause opens with one has lost
    it. Books and articles are cited the other way round -- "Hopkins (2007)
    3.6.3.1" is one work and a section of it -- which is why only the
    documents issued by a body are asked.
    """
    truncated = [
        (document["designation"], check["reference"]["cite"])
        for check in committed["checks"]
        for document in check["reference"]["documents"]
        if document["kind"] in {"standard", "report"}
        and not any(char.isdigit() for char in document["designation"])
        and any(char.isdigit() for char in _opening_word(document.get("clause")))
    ]
    assert truncated == []


def _opening_word(clause: str | None) -> str:
    """The first word of a clause, or nothing at all when there is none."""
    words = (clause or "").split()
    return words[0] if words else ""


def test_a_document_series_is_part_of_the_designation() -> None:
    """ "Doc 29" and "Doc 32" are two documents, not two clauses of one."""
    for cite, designation in (
        ("ECAC Doc 29 NPD interpolation", "ECAC Doc 29"),
        ("ECAC Doc 32 Table 4", "ECAC Doc 32"),
        ("SAE ARP 5534 pure-tone coefficient (ISO 9613-1)", "SAE ARP 5534"),
        ("ICAO Annex 16 Vol. I App. 2 Table A2-3", "ICAO Annex 16"),
        ("ICAO Doc 9501 ETM Vol. I Table 3-7", "ICAO Doc 9501"),
        ("ISO/IEC Guide 98-3 Annex G.4", "ISO/IEC Guide 98-3"),
        ("ISO/PAS 20065:2016 Clause 5.3.8", "ISO/PAS 20065"),
        ("ASA WG S3-79 CB.TST", "ASA WG S3-79"),
        ("EBU Tech 3341:2023 Table 1 case 1", "EBU Tech 3341"),
        (
            "Directive (EU) 2015/996 Appendix F, Tables F-2 and F-3",
            "Directive (EU) 2015/996",
        ),
    ):
        assert _first(cite).designation == designation, cite


def test_an_amended_edition_is_still_an_edition() -> None:
    """``ISO 10140-5:2010+A1`` matched no year, so the whole of the number fell
    into the clause and the document became the bare body "ISO".
    """
    document = _first("ISO 10140-5:2010+A1 Annex B, Table B.1")
    assert (document.designation, document.edition, document.clause) == (
        "ISO 10140-5",
        "2010+A1",
        "Annex B, Table B.1",
    )


def test_an_edition_dated_to_the_month_keeps_its_month() -> None:
    """DIN and VDI identify an edition by year and month, and so must the split.

    The edition group took four digits and nothing after them, so
    ``DIN 45669-1:2010-09`` matched no edition at all and fell back to the
    bare body, and the way round it that the tree took was to cut the month
    off the citation until it fitted. That is the reference losing exactly
    what distinguishes one edition of a DIN from the next.
    """
    for cite, split in (
        ("DIN 45669-1:2010-09 Table 9", ("DIN 45669-1", "2010-09", "Table 9")),
        ("DIN 4150-3:1999-02 Bild 1", ("DIN 4150-3", "1999-02", "Bild 1")),
        ("DIN 45692:2009-08 Clause 6", ("DIN 45692", "2009-08", "Clause 6")),
    ):
        document = _first(cite)
        read = (document.designation, document.edition, document.clause)
        assert read == split, cite


def test_a_sheet_or_a_corrigendum_is_part_of_the_designation() -> None:
    """``VDI 2081 Blatt 1`` and ``Blatt 2`` are two documents, and so is a
    corrigendum: each has its own date and its own entry in a bibliography.

    Read with the sheet in the clause, both sheets of VDI 2081 were one
    designation with no edition, and the report joined an equation of the 2001
    guideline and a worked example of the 2005 one onto a single row.
    """
    for cite, split in (
        (
            "VDI 2081 Blatt 1:2001-07 Eq. (13)",
            ("VDI 2081 Blatt 1", "2001-07", "Eq. (13)"),
        ),
        (
            "VDI 2081 Blatt 2:2005-05 Table 1, element 1",
            ("VDI 2081 Blatt 2", "2005-05", "Table 1, element 1"),
        ),
        (
            "DIN 45669-1 Ber 1:2012-12 Table 8",
            ("DIN 45669-1 Ber 1", "2012-12", "Table 8"),
        ),
    ):
        document = _first(cite)
        read = (document.designation, document.edition, document.clause)
        assert read == split, cite


def test_no_clause_opens_with_a_sheet_or_a_corrigendum(committed: dict) -> None:
    """The committed artefact, asked the question the parser was not.

    A sheet, part or corrigendum number that opens a clause is a piece of the
    designation that the split dropped, whatever the designation it left
    behind looks like: ``VDI 2081`` carries digits, so the check above that
    catches a bare body never fired for it.
    """
    dropped = [
        check["reference"]["cite"]
        for check in committed["checks"]
        for document in check["reference"]["documents"]
        if document["kind"] in {"standard", "report"}
        and _SHEET_OPENER.match(document.get("clause") or "")
    ]
    assert dropped == []


def test_a_dated_edition_is_the_edition_the_guides_cite(committed: dict) -> None:
    """For the bodies that date an edition to the month, the report and the
    guides name the same document.

    The site bibliography carries each designation as the guide that
    implements it cites it, and the conformance rows were free to drift from
    it: DIN 4150-3 was 1999-02 on its page and 1999 in the report. Asked only
    of DIN and VDI, because those are the bodies whose month is part of the
    edition rather than a publication detail.
    """
    cited = set()
    for page in _DOCS.rglob("*.md*"):
        cited.update(_FRONTMATTER_DESIGNATION.findall(page.read_text(encoding="utf-8")))
    drifted = sorted(
        {
            named
            for check in committed["checks"]
            for document in check["reference"]["documents"]
            if document["designation"].split(" ", 1)[0] in {"DIN", "VDI"}
            for named in [_named_edition(document)]
            if named not in cited
        }
    )
    assert drifted == []


def test_every_dated_edition_in_the_guides_carries_its_month() -> None:
    """The half the cross-check above cannot see.

    Comparing the report with the guides catches a citation that drifted from
    its page, and passes both when both were cut the same way: DIN 45692 was
    ``2009`` on its pages and in the report, while the title page reads August
    2009. So the guides are asked on their own, and a DIN or VDI designation
    they cite has to name the month its edition is identified by.
    """
    undated = sorted(
        {
            designation
            for page in _DOCS.rglob("*.md*")
            for designation in _FRONTMATTER_DESIGNATION.findall(
                page.read_text(encoding="utf-8")
            )
            if designation.split(" ", 1)[0] in {"DIN", "VDI", "E"}
            and not _MONTH_DATED.search(designation)
        }
    )
    assert undated == []


def _named_edition(document: dict) -> str:
    """The designation with its edition, as a frontmatter reference writes it.

    A citation of one of these bodies with no edition at all is itself the
    drift the test is after, and comes back as the bare designation, which no
    dated frontmatter entry can equal.
    """
    edition = document.get("edition")
    return (
        f"{document['designation']}:{edition}" if edition else document["designation"]
    )


def test_a_series_prefix_does_not_swallow_a_plain_designation() -> None:
    """The series entries sit before the bodies they extend, so the longest
    match wins; a citation of the body alone must be unaffected.
    """
    for cite, designation in (
        ("ISO 9613-2:1996 Table 3", "ISO 9613-2"),
        ("IEC 61672-1:2013 (Leq)", "IEC 61672-1"),
        ("Directive 2002/49/EC Annex II", "Directive 2002/49/EC"),
        ("ISO/TR 17534-3:2015 Table 1", "ISO/TR 17534-3"),
    ):
        assert _first(cite).designation == designation, cite


def test_a_series_designation_keeps_its_body_kind() -> None:
    """ECAC publishes reports, and "ECAC Doc 29" is still an ECAC document."""
    assert _first("ECAC Doc 29 NPD interpolation").kind is (
        references.ReferenceKind.REPORT
    )


def test_a_standard_splits_into_designation_edition_and_clause() -> None:
    document = _first("IEC 61260-1:2014 Table 1")
    assert document.kind is references.ReferenceKind.STANDARD
    assert (document.designation, document.edition, document.clause) == (
        "IEC 61260-1",
        "2014",
        "Table 1",
    )


def test_a_book_edition_is_a_string_not_a_year() -> None:
    """An edition has to hold "2e" and "4th ed" as well as "2014"."""
    document = _first("Long, Architectural Acoustics 2e, Table 8.1")
    assert document.kind is references.ReferenceKind.BOOK
    assert document.edition == "2e"
    assert document.designation == "Long, Architectural Acoustics"


def test_a_closed_form_is_a_derivation_and_not_a_document() -> None:
    document = _first("Model identity (uniform absorption)")
    assert document.kind is references.ReferenceKind.DERIVATION
    assert document.clause is None


def test_no_designation_is_cut_inside_a_phrase(committed: dict) -> None:
    """The committed artefact, asked whether any split cut a name in two.

    The site prints the designation as the leading text of every row, so a
    split that rebuilds the citation but cuts it inside a phrase publishes
    "Tab. 4.2 (printed folio 14, PDF" as the name of a document. The tell is a
    parenthesis the designation opens and never closes, or a trailing comma or
    conjunction that was joining it to the rest of the citation.
    """
    cut = sorted(
        {
            document["designation"]
            for check in committed["checks"]
            for document in check["reference"]["documents"]
            if not references._is_whole(document["designation"])
        }
    )
    assert cut == []


def test_a_split_that_cuts_a_name_falls_through_to_the_next_reading() -> None:
    """Refused splits land on the next splitter, or on the whole string."""
    for cite, read in (
        (
            "Poiseuille limit (Stinson 1991)",
            ("derivation", "Poiseuille limit (Stinson 1991)", None, None),
        ),
        (
            "Manual de acústica ambiental y arquitectónica, Ejemplo 7.1",
            (
                "book",
                "Manual de acústica ambiental y arquitectónica",
                None,
                "Ejemplo 7.1",
            ),
        ),
        (
            "Suva 66008.f, 8th revised edition, August 2006, Tableau 2 and Figure 7",
            (
                "derivation",
                "Suva 66008.f, 8th revised edition, August 2006, Tableau 2 and Figure 7",
                None,
                None,
            ),
        ),
    ):
        reference = references.parse(cite, overrides={})
        got = [
            (
                str(document.kind),
                document.designation,
                document.edition,
                document.clause,
            )
            for document in references.documents(reference)
        ]
        assert got == [read], cite
        assert references.recompose(reference) == cite


def test_the_year_form_files_a_known_book_or_report_as_what_it_is() -> None:
    """ "Barron (2003)" reads as a paper and is a book; the table says so.

    A work named second in a citation is asked the same question: "Fuchs
    (2013)" is a Springer monograph and "INSHT NTP 668 (2004)" a national
    institute's technical note, and both are only ever written behind a
    connector.
    """
    kinds = references.ReferenceKind
    for cite, kind in (
        ("Barron (2003) Table 7-5, PDF p. 320, printed folio 308", kinds.BOOK),
        ("Fuchs (2013) Table 13.4, PDF page 588, folio 574", kinds.BOOK),
        ("Ver and Beranek (2006) Example 4.2, PDF page 96, folio 91", kinds.BOOK),
        ("INSHT NTP 668 (2004) Ec. 2 and Ec. 3, PDF pages 3 and 4", kinds.REPORT),
        ("Harris (1991) Figures A3-2 and A3-8", kinds.BOOK),
        ("Harris 1978 closed form (DFT-even Hann)", kinds.ARTICLE),
        ("NPL CIRA(EXT) 009 (1996) Tables 8 to 14", kinds.REPORT),
        ("IFA-LSA 01-234 (2020) Tab. 4.2 (printed folio 14, PDF p. 14)", kinds.REPORT),
        ("Heisterkamp (2024) Table 3, PDF p. 10, printed folio 186", kinds.ARTICLE),
    ):
        assert _first(cite).kind is kind, cite


def test_a_declared_work_keeps_its_kind_whatever_shape_follows_the_name() -> None:
    """A work listed in ``_WORKS`` is what the list says, in all four shapes.

    The name a citation writes is not always the designation the work is filed
    under, and the kind table is keyed by the designation. Reading it with the
    written name misses exactly the works whose record expands the name:
    "NORAH2 (2015)" looked like an author with a year and came back an article
    called "NORAH2", which is neither the kind nor the designation the rest of
    the corpus cites. Every shape has to land on the same document.
    """
    kinds = references.ReferenceKind
    for cite in (
        "NORAH2",
        "NORAH2 Eq. 8",
        "NORAH2 (2015) Eq. 8",
        "NORAH2 2e Eq. 8",
    ):
        document = _first(cite)
        assert document.kind is kinds.REPORT, cite
        assert document.designation == "NORAH2 guidance", cite
        assert document.written == "NORAH2", cite


def test_a_work_whose_name_is_its_designation_is_not_given_a_written_form() -> None:
    """``written`` records an expansion, so a name that needs none stays bare.

    It is what ``recompose`` puts back on the page, and a citation rebuilt with
    a redundant written form would no longer match the string it came from.
    """
    for cite in ("Bies (2017) 4.9.2", "Mackenzie (1981)", "Ainslie (2010) §3.2"):
        assert _first(cite).written is None, cite


def test_a_report_number_joined_to_its_body_keeps_the_body_kind() -> None:
    """FHWA writes its report numbers onto the body with a hyphen."""
    document = _first("FHWA-PD-96-046 Table 3, printed folio 35 (PDF page 52)")
    assert document.kind is references.ReferenceKind.REPORT
    assert document.designation == "FHWA-PD-96-046"


def test_an_override_line_needs_five_fields() -> None:
    with pytest.raises(ValueError, match="expected 5 tab-separated fields"):
        references._override_line("only\ttwo", 3)


def test_an_override_line_needs_a_known_kind() -> None:
    with pytest.raises(ValueError, match="is not one of"):
        references._override_line("cite\tpamphlet\tX\t-\t-", 4)


# --------------------------------------------------------------------------
# Units
# --------------------------------------------------------------------------


def test_a_unit_spelling_collapses_onto_one_form() -> None:
    assert units.canonical_unit("dB(A)") == "dBA"
    assert units.canonical_unit("Pa s/m2") == "Pa·s/m²"
    assert units.canonical_unit("m/s^2") == "m/s²"


def test_an_unknown_unit_is_rejected_rather_than_passed_through() -> None:
    """A silent new spelling is how the report reached 58 spellings of 54 units."""
    with pytest.raises(ValueError, match="not in the conformance unit vocabulary"):
        units.canonical_unit("furlongs")


def test_the_vocabulary_at_the_document_head_covers_every_row(
    committed: dict,
) -> None:
    declared = set(committed["units"])
    used = {check["unit"] for check in committed["checks"] if check.get("unit")}
    assert used <= declared


# --------------------------------------------------------------------------
# The builders
# --------------------------------------------------------------------------


def test_a_record_check_compares_the_same_names_on_both_sides() -> None:
    with pytest.raises(ValueError, match="record check compares different names"):
        registry.record({"Rw": 52.0}, {"Rw": 52.0, "C": -1.0})


def test_a_record_check_counts_the_names_that_disagree() -> None:
    outcome = registry.record({"Rw": 52.0, "C": -1.0}, {"Rw": 52.0, "C": -2.0})
    assert outcome.kind is registry.Kind.RECORD
    assert outcome.deviation.value == 1.0
    assert outcome.verdict is registry.Verdict.FAIL


def test_a_count_check_carries_no_unit() -> None:
    """ "mismatches" sat in the unit column among the newtons and the pascals."""
    outcome = registry.count(160, 160, subject="coefficients")
    assert outcome.unit is None
    assert outcome.kind is registry.Kind.COUNT
    assert outcome.computed == "160/160 coefficients"


def test_a_mask_is_judged_by_the_nearer_edge_of_its_band() -> None:
    """The Tech 3341 true-peak window is +0.2/-0.4 dB: no single figure says it."""
    outcome = registry.mask(
        expected="-6 dBTP (+0.2/-0.4 dB)",
        computed="-5.9 dBTP",
        deviation=0.1,
        lower=-0.4,
        upper=0.2,
        unit="dBTP",
    )
    assert outcome.kind is registry.Kind.MASK
    assert outcome.delta == "headroom 0.1 dBTP"
    assert outcome.verdict is registry.Verdict.PASS


def test_a_one_sided_criterion_has_an_unbounded_edge() -> None:
    outcome = registry.mask(
        expected="m >= 0.5", computed="0.981", deviation=0.981, lower=0.5
    )
    assert outcome.delta == "headroom 0.481"


def test_an_outcome_built_from_strings_alone_keeps_working() -> None:
    """Four checks live in a module this pipeline does not own, and a new row
    added there must land in the artefact without an edit here.
    """
    outcome = registry.Outcome(
        expected="class 0",
        computed="class 0 (margin +0.650 dB)",
        delta="+0.650 dB",
        passed=True,
    )
    assert outcome.kind is registry.Kind.MASK
    assert outcome.deviation.value == pytest.approx(0.65)
    assert outcome.deviation.label == "+0.650 dB"


def test_a_delta_carrying_two_quantities_is_not_guessed_at() -> None:
    """ "+0.12 / -0.34 Hz" is two numbers; storing either one would be a lie."""
    deviation = registry._inferred("+0.12 / -0.34 Hz")
    assert deviation.value is None
    assert deviation.label == "+0.12 / -0.34 Hz"


# --------------------------------------------------------------------------
# Tolerance utilisation
# --------------------------------------------------------------------------


def _scalar(deviation: float, limit: float, mode: str = "absolute") -> dict:
    return {
        "deviation": {"value": deviation},
        "tolerance": {"mode": mode, "value": limit},
        "expected": {"value": 10.0},
    }


def test_utilisation_is_the_fraction_of_the_limit_a_deviation_spends() -> None:
    assert metrics.utilisation(_scalar(0.05, 0.1)) == pytest.approx(0.5)
    assert metrics.utilisation(_scalar(-0.1, 0.1)) == pytest.approx(1.0)


def test_a_relative_tolerance_is_a_fraction_of_the_expected_value() -> None:
    assert metrics.utilisation(_scalar(0.5, 0.1, "relative")) == pytest.approx(0.5)


def test_a_check_with_no_declared_limit_has_no_utilisation() -> None:
    assert metrics.utilisation({"deviation": {"value": 1.0}}) is None


def test_a_one_sided_mask_has_no_utilisation() -> None:
    """Half of an unbounded band is not a fraction of anything."""
    check = {
        "deviation": {"value": 0.9},
        "tolerance": {"mode": "mask", "value": 0.0},
        "binding": {"lower": 0.5},
        "expected": {},
    }
    assert metrics.utilisation(check) is None


def test_no_committed_check_spends_more_than_its_limit(committed: dict) -> None:
    """A utilisation over one with a passing verdict would mean the stored
    limit and the stored verdict disagree about the same check.
    """
    for check in committed["checks"]:
        used = metrics.utilisation(check)
        if used is None or check["verdict"] != "pass":
            continue
        assert used <= 1.0 + 1e-9, check["id"]


# --------------------------------------------------------------------------
# The comparator
# --------------------------------------------------------------------------


def test_an_unchanged_document_reports_nothing(committed: dict) -> None:
    assert compare.document_problems(committed, json.loads(json.dumps(committed))) == []


def test_a_flipped_verdict_is_never_within_tolerance(committed: dict) -> None:
    moved = json.loads(json.dumps(committed))
    moved["checks"][0]["verdict"] = "fail"
    problems = compare.document_problems(committed, moved)
    assert any("verdict" in problem for problem in problems)


def test_a_last_digit_wobble_is_within_tolerance(committed: dict) -> None:
    """The drift the gate exists to tolerate: one quantum of the check's own
    precision, which is what a rounding boundary moves by across BLAS builds.
    """
    moved = json.loads(json.dumps(committed))
    check = next(c for c in moved["checks"] if c["deviation"].get("value") is not None)
    check["deviation"]["value"] += 10.0 ** -max(int(check["precision"]), 3)
    assert compare.document_problems(committed, moved) == []


def test_a_real_move_is_not_within_tolerance(committed: dict) -> None:
    moved = json.loads(json.dumps(committed))
    check = next(c for c in moved["checks"] if c["deviation"].get("value") is not None)
    check["deviation"]["value"] += 1000.0
    assert compare.document_problems(committed, moved) != []


def test_an_added_check_fails_the_comparison(committed: dict) -> None:
    grown = json.loads(json.dumps(committed))
    extra = json.loads(json.dumps(grown["checks"][0]))
    extra["id"] += "-copy"
    grown["checks"].append(extra)
    grown["counts"]["checks"] += 1
    assert compare.document_problems(committed, grown) != []


def test_two_checks_may_not_share_an_id() -> None:
    """A shared id would make the pull-request diff join two different checks."""
    with pytest.raises(ValueError, match="duplicate conformance check id"):
        artifact._reject_duplicate_ids([{"id": "a/b/c"}, {"id": "a/b/c"}])


# --------------------------------------------------------------------------
# The two renderers read one document
# --------------------------------------------------------------------------


def test_the_markdown_shows_every_check_exactly_once(committed: dict) -> None:
    """The drift guard: Markdown and the site component render one artefact,
    and the Markdown must account for all of it.
    """
    markdown, passed, total = cr.render_markdown(committed)
    assert (passed, total) == (
        committed["counts"]["passing"],
        committed["counts"]["checks"],
    )
    for check in committed["checks"]:
        quantity = cr._cell(check["quantity"])
        assert markdown.count(f"| {quantity} |") >= 1, check["id"]


def test_the_markdown_headline_states_the_recorded_counts(committed: dict) -> None:
    markdown, _, _ = cr.render_markdown(committed)
    counts = committed["counts"]
    assert (
        f"**{counts['passing']}/{counts['checks']} conformance checks pass** "
        f"across {counts['domains']} domains and {counts['standards']} standards"
    ) in markdown


def test_the_markdown_is_a_pure_function_of_the_artefact(committed: dict) -> None:
    """Rendering twice from one document must give one file, which is what
    lets docs/CONFORMANCE.md keep a byte gate while the values behind it are
    compared within a tolerance.
    """
    first, _, _ = cr.render_markdown(committed)
    second, _, _ = cr.render_markdown(committed)
    assert first == second


def test_the_committed_markdown_is_what_the_artefact_renders(committed: dict) -> None:
    markdown, _, _ = cr.render_markdown(committed)
    expected = cr._DOC_HEADER + markdown + "\n"
    on_disk = (artifact._ROOT / "docs" / "CONFORMANCE.md").read_text(encoding="utf8")
    assert on_disk == expected


#: A whole document with three checks, one of each interesting shape. The
#: renderer is a pure function of the artefact, so it can be exercised on this
#: instead of only end to end on 554 rows.
FIXTURE = {
    "schema": 2,
    "library": "0.0.0",
    "generator": "test",
    "counts": {
        "checks": 3,
        "passing": 3,
        "failing": 0,
        "domains": 1,
        "standards": 2,
        "citations": 3,
        "designations": 2,
        "sources": 0,
    },
    "units": ["dB"],
    "domains": [{"id": "d", "title": "D", "checks": 3, "passing": 3}],
    "panels": [
        {
            "id": "filter-class",
            "title": "T",
            "rows": [
                {
                    "architecture": "butter",
                    "verdict": "pass",
                    "class": 1,
                    "binding": {
                        "frequency_hz": 1000.0,
                        "measured": 0.0,
                        "limit": -0.3,
                        "side": "ceil",
                    },
                    "margin_class1": 0.4,
                    "margin_class2": 0.9,
                }
            ],
        },
        {
            "id": "weighting-deviation",
            "title": "W",
            "rows": [
                {
                    "curve": "A",
                    "fs_hz": 48000,
                    "worst": {"frequency_hz": 20.0, "deviation": -0.7},
                    "binding": {
                        "frequency_hz": 20.0,
                        "deviation": -0.7,
                        "lower": -2.0,
                        "upper": 2.0,
                    },
                    "headroom": 1.3,
                    "verdict": "pass",
                }
            ],
        },
    ],
    "checks": [
        {
            "id": "d/iso-1-2020-table-1/scalar",
            "domain": "d",
            "reference": {
                "cite": "ISO 1:2020 Table 1",
                "documents": [
                    {
                        "kind": "standard",
                        "designation": "ISO 1",
                        "edition": "2020",
                        "clause": "Table 1",
                    }
                ],
            },
            "quantity": "Scalar",
            "kind": "scalar",
            "expected": {"value": 1.0},
            "computed": {"value": 1.02},
            "unit": "dB",
            "tolerance": {"mode": "absolute", "value": 0.05},
            "deviation": {"value": 0.02},
            "precision": 2,
            "verdict": "pass",
        },
        {
            "id": "d/iso-1-2020-table-2/mask",
            "domain": "d",
            "reference": {
                "cite": "ISO 1:2020 Table 2",
                "documents": [
                    {
                        "kind": "standard",
                        "designation": "ISO 1",
                        "edition": "2020",
                        "clause": "Table 2",
                    }
                ],
            },
            "quantity": "Mask",
            "kind": "mask",
            "expected": {"label": "within band"},
            "computed": {"label": "+0.10 dB"},
            "unit": "dB",
            "tolerance": {"mode": "mask", "value": 0.0},
            "deviation": {"value": 0.1},
            "binding": {"frequency_hz": 1000.0, "lower": -1.0, "upper": 1.0},
            "precision": 3,
            "verdict": "pass",
        },
        {
            "id": "d/iso-2-2020-annex-a/record",
            "domain": "d",
            "reference": {
                "cite": "ISO 2:2020 Annex A",
                "documents": [
                    {
                        "kind": "standard",
                        "designation": "ISO 2",
                        "edition": "2020",
                        "clause": "Annex A",
                    }
                ],
            },
            "quantity": "Record",
            "kind": "record",
            "expected": {"label": "Rw = 52", "record": {"Rw": 52.0}},
            "computed": {"label": "Rw = 52", "record": {"Rw": 52.0}},
            "tolerance": {"mode": "absolute", "value": 0.0},
            "deviation": {"value": 0.0},
            "precision": 0,
            "verdict": "pass",
        },
    ],
}


def test_the_fixture_is_a_document_the_gate_accepts() -> None:
    """A fixture that states a schema has to be one.

    The renderer reads one field of a reference, so a fixture can carry a
    superseded shape and stay green forever while claiming, in the file whose
    subject is the artefact's invariants, that the artefact looks like that.
    This one did: it still declared schema 1 and a single headline document
    per citation after a citation had become a list of them.

    The override ratchet is the one thing the gate asks that is about the
    corpus rather than about the document in front of it, and three checks are
    not the corpus, so it is the one thing excused here.
    """
    assert FIXTURE["schema"] == artifact.SCHEMA
    problems = [
        problem
        for problem in gate.validate(FIXTURE)
        if not problem.startswith(gate.OVERRIDES_PATH.name)
    ]
    assert problems == []


def test_a_citation_with_nothing_after_its_last_document_has_no_tail() -> None:
    """Absent, never null, because the site reads the document that way.

    The site schema declares ``tail`` an optional string of at least one
    character, and no field of a check there is nullable, so ``null`` is
    rejected wherever it appears.
    A reference keeps an empty tail, which the builder writes as ``None`` and
    then drops along with every other null-valued key, so the key is left out
    of the file. The bracket a citation does close on is still written.

    The builder is the only thing between a null and a documentation build
    that fails far from the check that wrote it, so the gate asks the whole
    document for nulls as well. It did not before, and accepted the fixture
    above while it carried twelve of them.
    """
    bare = references.parse("ISO 16283-1:2014 Clause 8.1", overrides={})
    closed = references.parse("IEC 651:1979 Table V (via BS 5969:1981)", overrides={})
    assert bare.tail == ""
    assert "tail" not in artifact._without_nulls(artifact._reference_document(bare))
    assert artifact._without_nulls(artifact._reference_document(closed))["tail"] == ")"

    written = json.loads(json.dumps(FIXTURE))
    written["checks"][0]["reference"]["tail"] = None
    written["checks"][1]["reference"]["documents"][0]["lead"] = None
    # Through validate(), not only the helper: a gate that stopped calling it
    # would otherwise accept the nulls with every test still green.
    nulls = [
        problem.split(" ", 1)[0]
        for problem in gate.validate(written)
        if not problem.startswith(gate.OVERRIDES_PATH.name)
    ]
    assert nulls == [
        "checks[0].reference.tail",
        "checks[1].reference.documents[0].lead",
    ]
    assert gate._null_problems(FIXTURE) == []


def test_a_null_where_a_list_belongs_is_reported_rather_than_raised() -> None:
    """The validators after the null check walk lists and mappings."""
    written = json.loads(json.dumps(FIXTURE))
    written["checks"][0]["reference"]["documents"] = None
    problems = [
        problem
        for problem in gate.validate(written)
        if not problem.startswith(gate.OVERRIDES_PATH.name)
    ]
    assert [problem.split(" ", 1)[0] for problem in problems] == [
        "checks[0].reference.documents"
    ]


def test_the_renderer_works_on_a_three_check_document() -> None:
    """The point of making the Markdown a pure function of the artefact."""
    markdown, passed, total = cr.render_markdown(FIXTURE)
    assert (passed, total) == (3, 3)
    assert (
        "**3/3 conformance checks pass** across 1 domains and 2 standards" in markdown
    )
    assert "| 1.02 dB |" in markdown  # the scalar's computed value
    assert "| headroom 0.9 dB |" in markdown  # the mask's headroom, derived
    assert "| exact |" in markdown  # the record's deviation
    assert "ISO 1:2020 Table 1" in markdown


def test_a_verdict_is_printed_and_never_re_derived() -> None:
    """The stored verdict wins over anything the stored numbers imply.

    A deviation that rounds onto its limit would flip a re-derived judgement,
    so the renderer must not have one. Handed a row whose deviation is ten
    times its tolerance and whose verdict says pass, it prints pass.
    """
    document = json.loads(json.dumps(FIXTURE))
    document["checks"][0]["deviation"]["value"] = 0.5
    markdown, _, _ = cr.render_markdown(document)
    # The domain table's copy of the row, not the closest-to-its-limit table's:
    # a check that spends ten times its allowance leads that ranking, and that
    # table prints no verdict at all.
    row = next(
        line for line in markdown.splitlines() if "| Scalar |" in line and "cv-" in line
    )
    # The mark and the word, both saying pass: the indicator is drawn from the
    # stored verdict too, so a re-derivation would show up here as a red
    # hexagon beside the word "Pass".
    assert row.endswith("| ![Pass][cv-pass] Pass |")


def test_a_missing_panel_is_named() -> None:
    with pytest.raises(KeyError, match="carries no 'filter-class' panel"):
        cr._numerical_validation_section({"panels": []}, filters_ok=True)


def test_a_missing_artefact_says_how_to_make_one(tmp_path: pathlib.Path) -> None:
    with pytest.raises(SystemExit, match="make conformance"):
        artifact.load(tmp_path / "conformance.json")


# ---------------------------------------------------------------------------
# A record check keeps its own values
# ---------------------------------------------------------------------------
#
# `record` sets precision to zero because its deviation is a count of names
# that disagreed, not a decimal figure. Two separate places then read that
# zero as "round these values to integers", and between them the artefact
# published 1.0 where ISO 9614-1 Table B.1 prints 0,60: the serialiser rounded
# it, and the comparison that decides whether to rewrite the file tolerated the
# 0.4 that made, so no regeneration could dislodge it and no gate objected.
# The label beside it still read 0.6 and the verdict still read pass.


def test_a_record_check_publishes_its_values_unrounded() -> None:
    """A fractional record value survives serialisation.

    The values of a record check are compared for equality, so the check's
    precision says nothing about how many decimals they carry.
    """
    outcome = registry.record(
        {"precision (all bands)": 0.2, "survey (A-weighted)": 0.6},
        {"precision (all bands)": 0.2, "survey (A-weighted)": 0.6},
    )
    document = artifact._computed_document(outcome)
    assert document["record"] == {
        "precision (all bands)": 0.2,
        "survey (A-weighted)": 0.6,
    }


def test_a_record_value_that_moved_is_not_tolerated_away() -> None:
    """The rewrite guard sees a record value move, whatever the precision.

    Without this the artefact could hold a value the harness never produced:
    a zero-decimal tolerance is 1.0 absolute, which swallows the whole
    difference between a published 0,60 and a stored 1.0.
    """
    outcome = registry.record({"survey": 0.6}, {"survey": 0.6})
    fresh = {
        "id": "x",
        "kind": str(registry.Kind.RECORD),
        "precision": 0,
        "reference": {},
        "expected": {"record": {"survey": 0.6}},
        "computed": {"record": {"survey": 0.6}},
    }
    stale = {**fresh, "computed": {"record": {"survey": 1.0}}}
    assert outcome.kind is registry.Kind.RECORD
    problems = compare._check_problems(stale, fresh)
    assert any("computed.record.survey" in problem for problem in problems), problems


def test_a_spanish_title_keeps_the_id_it_had_without_its_accents() -> None:
    """The slug keeps the base letter of a spelling mark, and nothing else moves.

    "Catálogo" slugged to ``cat-logo`` before, so writing a Spanish title
    correctly would have renamed its rows. The circumflex is notation here (the
    ``â`` of a peak acceleration), and a letter carrying it is still dropped, so
    no id already in the artefact changes.
    """
    assert artifact.slug("CTE Catálogo de Elementos Constructivos") == (
        artifact.slug("CTE Catalogo de Elementos Constructivos")
    )
    assert artifact.slug("Rodiño & Masson (2015)") == "rodino-masson-2015"
    assert artifact.slug("Calibration L_v from â = 9,81 m/s²") == (
        "calibration-l-v-from-9-81-m-s"
    )


def test_a_decomposed_accent_reduces_to_the_same_id() -> None:
    """ "á" and "a" with a combining acute are one letter, so one slug."""
    assert artifact.slug("Catálogo") == artifact.slug("Catálogo") == "catalogo"


# --------------------------------------------------------------------------
# Machine noise is not published
# --------------------------------------------------------------------------
#: A number printed with an exponent below the noise floor.
_NOISE_DIGITS = re.compile(r"\d(?:\.\d+)?e-(?:1[3-9]|[2-9]\d)\b")


def test_a_residue_below_the_noise_floor_is_stored_as_zero() -> None:
    """The residue of an identity differs between CPUs in its leading digits."""
    assert artifact._rounded(5.68e-14, 6) == 0.0
    assert artifact._rounded(-6.39e-14, 6) == 0.0
    assert artifact._rounded(4.2e-7, 5) == pytest.approx(4.2e-7)
    assert registry.residue_text(5.68e-14, "dB") == "below 1e-12 dB"
    assert registry.residue_text(0.0) == "below 1e-12"
    assert registry.residue_text(0.0438, "dB", ".3g") == "0.0438 dB"


def test_the_report_publishes_no_machine_noise(committed: dict) -> None:
    """No stored value and no label carries digits a second CPU would not."""
    noisy = []
    for check in committed["checks"]:
        for side in ("computed", "deviation"):
            part = check.get(side) or {}
            value = part.get("value")
            if isinstance(value, float) and 0.0 < abs(value) < registry.NOISE_FLOOR:
                noisy.append(f"{check['id']} {side}.value {value!r}")
            label = part.get("label") or ""
            if _NOISE_DIGITS.search(label):
                noisy.append(f"{check['id']} {side}.label {label!r}")
    assert noisy == []
