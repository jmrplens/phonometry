#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Gate for the committed ``docs/conformance.json``.

The artefact cannot be gated by a byte diff alone. GitHub's runner fleet is
hardware-heterogeneous, so the same pinned stack computes a few values a unit
in the last place apart, and a value sitting on a rounding boundary then stores
one quantum away from the committed one. The figures met this first and the
answer is the same here: compare structure exactly and numbers within a
tolerance (:mod:`conformance.compare`).

Two modes, because they cost two very different things.

``--validate`` (the default) reads the committed document and checks that it is
internally consistent - the counts agree with the rows, every leaf is a
built-in type and none is null, no two checks share an id, every unit is in the
vocabulary, and every citation still rebuilds from its split. It runs no check
and needs no scientific stack, so it is cheap enough to run beside every other
read-only gate. It is what catches a truncated write, a hand-edit and a numpy
scalar.

``--regenerate`` runs all the checks and compares the result against the
committed document. This is the authoritative staleness gate, and it costs the
same as the harness because it *is* the harness.
"""

from __future__ import annotations

import argparse
import functools
import pathlib
import sys
from typing import TYPE_CHECKING, Any

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from conformance.artifact import SCHEMA, build_document, load
from conformance.compare import document_problems
from conformance.references import (
    OVERRIDES_PATH,
    Cited,
    Reference,
    ReferenceKind,
    Relation,
    expansion_of,
    recompose,
    relation_for,
    work_kinds,
)
from conformance.registry import Kind, Verdict
from conformance.units import UNITS

if TYPE_CHECKING:
    from collections.abc import Mapping

#: Leaves that must be a built-in ``float`` if they are present at all.
#: Checked with ``type(x) is float`` and never ``isinstance``: ``numpy.float64``
#: is a subclass of ``float``, so an ``isinstance`` test passes on exactly the
#: value that breaks ``json.dumps`` further down the chain.
_FLOAT_LEAVES = (
    ("expected", "value"),
    ("computed", "value"),
    ("tolerance", "value"),
    ("deviation", "value"),
)


def _count_problems(document: Mapping[str, Any]) -> list[str]:
    """The written counts must agree with the rows they count.

    This is the check a derived count cannot make: a truncated write derives a
    total that agrees with the rows that survived it.
    """
    counts, checks = document["counts"], document["checks"]
    passing = sum(1 for check in checks if check["verdict"] == str(Verdict.PASS))
    problems = []
    if counts["checks"] != len(checks):
        problems.append(
            f"counts.checks is {counts['checks']} but the document carries "
            f"{len(checks)} checks."
        )
    if counts["passing"] != passing:
        problems.append(
            f"counts.passing is {counts['passing']} but {passing} rows say pass."
        )
    if counts["passing"] + counts["failing"] != counts["checks"]:
        problems.append(
            f"counts.passing + counts.failing is "
            f"{counts['passing'] + counts['failing']}, not {counts['checks']}."
        )
    if counts["domains"] != len(document["domains"]):
        problems.append(
            f"counts.domains is {counts['domains']} but the document carries "
            f"{len(document['domains'])} domains."
        )
    return problems


def _null_problems(value: object, path: str = "") -> list[str]:
    """No field may be null: a field a check does not have is left out.

    The builder drops every null-valued key before the document is written, so
    a citation with nothing after its last document has no ``tail`` at all
    rather than a null one. The site reads the document through a schema that
    declares each of those fields optional and none of them nullable, which
    makes ``null`` a value the documentation build rejects, and without this
    the first place to say so would be that build, far from the check that
    wrote it.

    :param value: The document, or any branch of it.
    :param path: Where ``value`` sits in the document, for the message.
    :return: One problem per null, naming its path.
    """
    if value is None:
        return [
            f"{path} is null. Leave the key out instead: the site schema reads "
            "an absent field and rejects a null one."
        ]
    if isinstance(value, dict):
        return [
            problem
            for key, inner in value.items()
            for problem in _null_problems(inner, f"{path}.{key}" if path else key)
        ]
    if isinstance(value, list):
        return [
            problem
            for index, item in enumerate(value)
            for problem in _null_problems(item, f"{path}[{index}]")
        ]
    return []


def _type_problems(check: Mapping[str, Any]) -> list[str]:
    """Every numeric leaf of one check must be a built-in ``float``."""
    problems = []
    for outer, inner in _FLOAT_LEAVES:
        holder = check.get(outer)
        if not isinstance(holder, dict) or inner not in holder:
            continue
        value = holder[inner]
        if type(value) is not float:
            problems.append(
                f"{check['id']}.{outer}.{inner} is {type(value).__name__}, not "
                "float. A numpy scalar passes every isinstance test and fails "
                "json.dumps; coerce it in the check."
            )
    return problems


def _vocabulary_problems(check: Mapping[str, Any]) -> list[str]:
    """A check's unit, kind and verdict must all be in their vocabularies."""
    problems = []
    unit = check.get("unit")
    if unit is not None and unit not in UNITS:
        problems.append(
            f"{check['id']}.unit is {unit!r}, which is not in the vocabulary "
            "declared at the head of the document."
        )
    if check["kind"] not in tuple(Kind):
        problems.append(f"{check['id']}.kind is {check['kind']!r}.")
    if check["verdict"] not in tuple(Verdict):
        problems.append(f"{check['id']}.verdict is {check['verdict']!r}.")
    return problems


def _reference_problems(check: Mapping[str, Any]) -> list[str]:
    """The documents must still rebuild the citation they came from.

    The whole reference split rests on this: a list that cannot be reassembled
    into the original string, connectors included, has lost or moved
    something, and the designation count is then counting the wrong thing.
    Because the rebuild walks the citation left to right, it is also what
    proves the documents cover it in order and do not overlap.

    Three things the rebuild cannot see are asked separately: the expanded
    designation behind a shorthand, which is written out and therefore not in
    the string; the relation, which is read off the connector; and the kind,
    which is a judgement about the document rather than about the text and is
    asked of the whole artefact at once in :func:`_work_kind_problems`.
    """
    reference = check["reference"]
    problems = [
        f"{check['id']}.reference.documents[{index}].kind is {document['kind']!r}."
        for index, document in enumerate(reference["documents"])
        if document["kind"] not in tuple(ReferenceKind)
    ]
    problems += [
        f"{check['id']}.reference.documents[{index}].relation is "
        f"{document['relation']!r}."
        for index, document in enumerate(reference["documents"])
        if document.get("relation") is not None
        and document["relation"] not in tuple(Relation)
    ]
    if problems:
        return problems
    cited = [_cited(document) for document in reference["documents"]]
    problems += _relation_problems(check, cited)
    problems += _written_problems(check, cited)
    rebuilt = recompose(
        Reference(
            cite=reference["cite"],
            documents=tuple(cited),
            tail=reference.get("tail") or "",
        )
    )
    # The ratchet lines are exempt from the rebuild, and they have to be: the
    # CNOSSOS-EU rows name a clause of Annex II, and the directive the clause
    # belongs to appears nowhere in the citation, so nothing rebuilt from the
    # record can reproduce the string.
    if rebuilt != reference["cite"] and reference["cite"] not in _overridden():
        problems.append(
            f"{check['id']}: the citation split does not rebuild its citation. "
            f"{[document['designation'] for document in reference['documents']]} "
            f"does not reproduce {reference['cite']!r}. "
            f"Fix the parser, or record the split in {OVERRIDES_PATH.name}."
        )
    return problems


def _cited(document: Mapping[str, Any]) -> Cited:
    """One stored document, read back as the parser writes it."""
    relation = document.get("relation")
    return Cited(
        kind=ReferenceKind(document["kind"]),
        designation=document["designation"],
        edition=document.get("edition"),
        clause=document.get("clause"),
        lead=document.get("lead") or "",
        relation=None if relation is None else Relation(relation),
        written=document.get("written"),
    )


def _relation_problems(check: Mapping[str, Any], cited: list[Cited]) -> list[str]:
    """Each document must say what the words that introduced it say."""
    return [
        f"{check['id']}.reference.documents[{index}]: lead {document.lead!r} "
        f"reads as {relation_for(document.lead)!r}, but the document records "
        f"{document.relation!r}."
        for index, document in enumerate(cited)
        if document.relation is not relation_for(document.lead)
    ]


def _written_problems(check: Mapping[str, Any], cited: list[Cited]) -> list[str]:
    """A shorthand must expand to the designation it names.

    ``-3:2016`` is ISO 16283-3 only because ISO 16283-1 opened the citation,
    and ``NORAH2`` is the NORAH2 guidance because the reader says so. Either
    way the expanded designation is not in the citation string, so the rebuild
    cannot see it and this asks instead.
    """
    problems = []
    for index, document in enumerate(cited[1:], start=1):
        if document.written is None:
            continue
        expected = expansion_of(document.written, cited[index - 1])
        if document.designation != expected:
            problems.append(
                f"{check['id']}.reference.documents[{index}]: "
                f"{document.written!r} after {cited[index - 1].designation!r} "
                f"is {expected!r}, not {document.designation!r}."
            )
    return problems


@functools.cache
def _overridden() -> frozenset[str]:
    """Citations whose split is recorded by hand and is exempt from rebuilding.

    Cached: the round-trip is checked once per check, and the answer is one
    file that does not change while the process runs.
    """
    if not OVERRIDES_PATH.is_file():
        return frozenset()
    return frozenset(
        line.split("\t")[0]
        for line in OVERRIDES_PATH.read_text(encoding="utf8").splitlines()
        if line.strip() and not line.startswith("#")
    )


def _work_kind_problems(document: Mapping[str, Any]) -> list[str]:
    """A work the reader knows by name is filed as one sort of document.

    The kind is the one field the rebuild cannot see: it is a judgement about
    the document rather than about the text, so nothing else in this gate
    compares it against anything. A name the reader lists is also readable by
    the rules that need no list, and those judge by shape, so the same work
    could be filed two ways in the same artefact and no gate would say a word.
    It was: Mackenzie was an article where the citation wrote the year and a
    book where it did not, and the NORAH2 guidance was a book where the parser
    read it and a report where the override file did.
    """
    declared = work_kinds()
    recorded: dict[tuple[str, str], str] = {}
    for check in document["checks"]:
        for cited in check["reference"]["documents"]:
            if cited["designation"] in declared:
                key = (cited["designation"], cited["kind"])
                recorded.setdefault(key, check["reference"]["cite"])
    return [
        f"{designation!r} is recorded as {kind!r} in {cite!r}, and the reader "
        f"declares it {str(declared[designation])!r}."
        for (designation, kind), cite in sorted(recorded.items())
        if kind != str(declared[designation])
    ]


def _ratchet_problems(document: Mapping[str, Any]) -> list[str]:
    """The override file may only shrink.

    A line for a citation no check registers any more is dead weight that hides
    the next real one, so it fails just as loudly as a missing entry would.
    """
    cited = {check["reference"]["cite"] for check in document["checks"]}
    return [
        f"{OVERRIDES_PATH.name}: no check cites {cite!r} any more; delete the line."
        for cite in sorted(_overridden() - cited)
    ]


def validate(document: Mapping[str, Any]) -> list[str]:
    """Everything the committed document must be true about itself."""
    problems: list[str] = []
    if document.get("schema") != SCHEMA:
        problems.append(
            f"schema is {document.get('schema')!r}, this checkout reads {SCHEMA}."
        )
    problems += _count_problems(document)
    problems += _null_problems(document)
    seen: set[str] = set()
    for check in document["checks"]:
        if check["id"] in seen:
            problems.append(f"duplicate check id {check['id']!r}.")
        seen.add(check["id"])
        problems += _type_problems(check)
        problems += _vocabulary_problems(check)
        problems += _reference_problems(check)
    problems += _work_kind_problems(document)
    problems += _ratchet_problems(document)
    return problems


def main(argv: list[str] | None = None) -> int:
    """Validate the committed artefact, or compare it against a fresh run."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help=(
            "run every check and compare the result against the committed "
            "document, instead of only validating what is committed"
        ),
    )
    args = parser.parse_args(argv)

    document = load()
    problems = validate(document)
    if args.regenerate:
        problems += document_problems(document, build_document())

    if problems:
        print(
            "docs/conformance.json is not consistent with the checks. "
            "Regenerate it with `make conformance` and commit the result:\n",
            file=sys.stderr,
        )
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    counts = document["counts"]
    print(
        f"docs/conformance.json consistent: {counts['passing']}/{counts['checks']} "
        f"checks, {counts['domains']} domains, {counts['designations']} normative "
        f"designations, {counts['sources']} further sources."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
