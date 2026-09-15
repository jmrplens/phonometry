#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate that keeps the site speaking the vocabularies the checks produce.

``scripts/check_conformance_vocabulary.py`` compares three statements of the
same five closed vocabularies: the Python enums a check writes into
``docs/conformance.json``, the Zod enums that validate the artefact into the
site, and the label maps that word a verdict and a relation in each language.
They drifted once already, when reading a citation as a list of documents gave
the relation vocabulary its fifth value and the site build stopped on ten rows
with a content error that named no cause.

The tests below fix what that comparison has to survive: two fields called
``kind`` in two schemas, a declaration too long for one line, and each label
map ending up under the language it is actually written in. The last one is
the half that fails quietly, because a relation with no word is printed raw
rather than refused.
"""

from __future__ import annotations

import collections
import pathlib
import sys

import pytest

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_conformance_vocabulary as gate

SCHEMA = """\
const conformanceCited = z.object({
  kind: z.enum(['standard', 'book']),
  relation: z
    .enum(['corroborates', 'supplies'])
    .optional(),
});

const conformanceCheck = z
  .object({
    kind: z.enum(['scalar', 'mask']),
    verdict: z.enum(['pass', 'fail']),
  });
"""

PAGE = """\
const t =
\tlang === 'es'
\t\t? {
\t\t\t\trelations: {
\t\t\t\t\tcorroborates: 'corroborado por',
\t\t\t\t\tsupplies: 'resuelto con',
\t\t\t\t} as Record<string, string>,
\t\t\t}
\t\t: {
\t\t\t\trelations: {
\t\t\t\t\tcorroborates: 'corroborated by',
\t\t\t\t} as Record<string, string>,
\t\t\t};
"""


def _vocabulary(name: str = "relation", *, labelled: bool = True) -> gate.Vocabulary:
    """The relation vocabulary, wired to the synthetic sources above."""
    return gate.Vocabulary(
        name,
        gate.Relation,
        ("conformanceCited", "relation"),
        "relations" if labelled else None,
        lambda _document: collections.Counter(),
    )


def test_two_fields_called_kind_are_told_apart_by_their_schema() -> None:
    """The field name alone does not identify a vocabulary.

    A citation's ``kind`` is the sort of document and a check's is the shape of
    the comparison. Read without the enclosing schema, each looks like a
    vocabulary that lost four values and gained two.
    """
    enums = gate.schema_enums(SCHEMA)
    assert enums["conformanceCited", "kind"] == frozenset({"standard", "book"})
    assert enums["conformanceCheck", "kind"] == frozenset({"scalar", "mask"})


def test_a_declaration_wrapped_over_three_lines_is_still_read() -> None:
    """``relation: z`` with ``.enum([...])`` under it is the file's own style.

    A pattern that insisted on one line would report the vocabulary as absent
    the moment adding a value pushed the declaration past the margin, which is
    exactly when it is being changed.
    """
    accepted = gate.schema_enums(SCHEMA)["conformanceCited", "relation"]
    assert accepted == frozenset({"corroborates", "supplies"})


def test_each_label_map_lands_under_the_language_it_is_written_in() -> None:
    """The page holds both tables in one ternary, Spanish branch first."""
    labels = gate.page_labels(PAGE)
    assert labels["Spanish", "relations"] == frozenset({"corroborates", "supplies"})
    assert labels["English", "relations"] == frozenset({"corroborates"})


def test_a_page_without_the_two_branches_is_a_defect_in_this_gate() -> None:
    """A rewritten page must fail loudly rather than pass in silence.

    If the words move somewhere this cannot read, the answer is to teach this
    where they went, not to let an unworded vocabulary through.
    """
    rewritten = PAGE.replace("\n\t\t: {", "\n\t\telse {")
    with pytest.raises(LookupError, match="translation tables"):
        gate.page_labels(rewritten)


def test_a_value_the_schema_refuses_is_reported_with_what_it_costs() -> None:
    """The defect this gate was written for, as the artefact shows it."""
    enums = {("conformanceCited", "relation"): frozenset({"corroborates"})}
    counts = collections.Counter({"supplies": 10})
    problems = gate._schema_problems(_vocabulary(), enums, counts)
    assert any("'supplies'" in problem and "10 rows" in problem for problem in problems)


def test_a_value_no_check_can_produce_fails_in_both_places() -> None:
    """A vocabulary that shrinks moves everywhere, or the leftovers mislead."""
    dead = frozenset(str(value) for value in gate.Relation) | {"retired"}
    enums = {("conformanceCited", "relation"): dead}
    schema = gate._schema_problems(_vocabulary(), enums, collections.Counter())
    labels = gate._label_problems(
        _vocabulary(), {("English", "relations"): dead}, ["English"]
    )
    assert [problem for problem in schema if "'retired'" in problem]
    assert [problem for problem in labels if "'retired'" in problem]


def test_a_value_only_the_committed_file_carries_is_a_hand_edit() -> None:
    """The artefact is generated, so a value no enum defines was typed in.

    Read the other way round from the two above: there the site had fallen
    behind the enums, here the committed file has run ahead of them, which is
    what an artefact edited by hand rather than regenerated looks like.
    """
    counts = collections.Counter({"supersedes": 2})
    problems = gate._artefact_problems(_vocabulary(), counts)
    assert any(
        "'supersedes'" in problem and "2 rows" in problem for problem in problems
    )


def test_a_vocabulary_the_page_never_words_is_not_asked_for_labels() -> None:
    """A document kind is drawn, not written, so it has no map to be missing."""
    assert gate._label_problems(_vocabulary(labelled=False), {}, ["English"]) == []


def test_the_committed_tree_agrees_with_itself() -> None:
    """The gate, run where it runs in CI: the three statements in step."""
    assert gate.problems() == []
