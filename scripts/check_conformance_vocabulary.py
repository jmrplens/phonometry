#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Keep the site's vocabularies equal to the ones a check can produce.

``docs/conformance.json`` is written by the checks and read by the site, and
five of its fields are closed vocabularies: the verdict of a check, the shape
of its comparison, how its tolerance applies, what sort of document a citation
names, and why a citation names a further one. Python owns all five as string
enums, and the site restates them twice: once in the Zod schema that validates
the artefact on its way into the content collection
(``site/src/content.config.ts``), and once in the label maps that give each
value a word in English and in Spanish
(``site/src/components/Conformance.astro``).

Nothing compared the restatements with the original, and they drifted. Reading
a citation as a list of documents gave the relation vocabulary a fifth value,
``supplies``, for the ``with`` and ``and`` that introduce a document the check
runs the clause with. Ten rows of the regenerated artefact carried it, the Zod
enum listed the other four, and the site build stopped with an
``InvalidContentEntryDataError`` naming ten checks and no cause. The label maps
had not heard of it either, which fails more quietly: the page falls back to
printing the raw value, so the Spanish conformance table would have said
``supplies`` beside ``corroborado por`` and ``comparado con``.

This holds the three in step, in both directions:

* every value a check can produce is accepted by the Zod enum, and worded in
  both languages where the page words that vocabulary at all;
* a value the site still accepts or words that no check can produce any more
  fails just as loudly, so a vocabulary that shrinks cannot leave a dead entry
  behind to mislead the next reader;
* a value in the committed artefact that Python cannot produce fails too,
  which is what a hand-edited artefact looks like.

Python is the authority and is read by importing the enums. The two site files
are read as text, because neither can be imported outside Astro's build: the
schema pulls in ``astro:content`` and the component is a page. Their shape is
therefore part of what this gate knows, and a rewrite that hides a vocabulary
from these patterns fails with a message that says so rather than passing in
silence.

Usage::

    python scripts/check_conformance_vocabulary.py

Exit status 0 when the three agree. ``make conformance`` runs it last and CI
runs it in the conformance job.
"""

from __future__ import annotations

import collections
import functools
import json
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from conformance.references import ReferenceKind, Relation
from conformance.registry import Kind, ToleranceMode, Verdict

if TYPE_CHECKING:
    import enum
    from collections.abc import Callable, Iterable, Mapping

ROOT = _SCRIPTS.parent
ARTEFACT = ROOT / "docs" / "conformance.json"
SCHEMA_FILE = ROOT / "site" / "src" / "content.config.ts"
PAGE_FILE = ROOT / "site" / "src" / "components" / "Conformance.astro"

#: Where a top-level declaration starts. The file holds several schemas, and
#: the field name alone does not identify a vocabulary: ``kind`` is the sort of
#: document on a citation and the shape of the comparison on a check. Matched
#: on the name alone rather than on ``z.``, because a schema that carries a
#: refinement writes the call on the next line (``= z`` then ``.object({``).
_OBJECT_RE = re.compile(r"^(?:export )?const (?P<name>\w+) = ", re.MULTILINE)

#: One ``field: z.enum(['a', 'b'])`` declaration, anywhere inside an object.
#: The whitespace is not decoration: a declaration too long for the line is
#: written ``field: z`` and ``.enum([...])`` under it, which is how the file
#: writes the longer half of its schemas, and a pattern that insisted on one
#: line would read a wrapped vocabulary as an absent one.
_ENUM_RE = re.compile(r"(?P<field>\w+):\s*z\s*\.enum\(\[(?P<values>[^\]]*)\]\)")

#: One label map in the page: ``verdicts: { ... } as Record<string, string>``.
#: The cast is what tells a map of words apart from every other object literal
#: in the translation table, and it is on both of them in both languages.
_MAP_RE = re.compile(
    r"(?P<name>\w+): \{(?P<body>[^{}]*)\} as Record<string, string>", re.DOTALL
)

#: A key inside such a map, quoted (``'by-design'``) or bare (``pass``).
_KEY_RE = re.compile(r"^\s*'?(?P<key>[A-Za-z][A-Za-z-]*)'?:", re.MULTILINE)

#: A single-quoted string, which is how the site writes every one of these.
_STRING_RE = re.compile(r"'([^']*)'")

#: The ternary that holds the page's two translation tables. Everything before
#: the English branch belongs to the Spanish one.
_SPANISH_BRANCH = "\n\t\t? {"
_ENGLISH_BRANCH = "\n\t\t: {"


def _cited_values(document: Mapping[str, Any], field: str) -> collections.Counter[str]:
    """What the committed artefact writes in ``field`` on a cited document."""
    return collections.Counter(
        cited[field]
        for check in document["checks"]
        for cited in check["reference"]["documents"]
        if cited.get(field) is not None
    )


def _check_values(document: Mapping[str, Any], field: str) -> collections.Counter[str]:
    """What the committed artefact writes in ``field`` on a check."""
    return collections.Counter(
        check[field] for check in document["checks"] if check.get(field) is not None
    )


def _tolerance_modes(document: Mapping[str, Any]) -> collections.Counter[str]:
    """How the committed artefact says each tolerance applies."""
    return collections.Counter(
        check["tolerance"]["mode"]
        for check in document["checks"]
        if check.get("tolerance") is not None
    )


@dataclass(frozen=True)
class Vocabulary:
    """One closed vocabulary, and the three places that have to agree on it."""

    #: What to call it in a message, as the artefact's own field names it.
    name: str
    #: The enum that defines it. Python is the authority, so this is read by
    #: importing it and never by parsing anything.
    values: type[enum.StrEnum]
    #: The Zod object and field that restate it in ``content.config.ts``.
    declared_in: tuple[str, str]
    #: The label map in ``Conformance.astro``, or ``None`` for a vocabulary
    #: the page never words: a document kind is drawn as a shape, and a
    #: tolerance mode decides the layout of a cell rather than its text.
    labelled_as: str | None
    #: How to count the rows of the committed artefact that carry each value.
    #: Only used to say how much a missing value costs.
    carried_by: Callable[[Mapping[str, Any]], collections.Counter[str]]

    @property
    def expected(self) -> frozenset[str]:
        """Every value a check can produce."""
        return frozenset(str(value) for value in self.values)


VOCABULARIES: tuple[Vocabulary, ...] = (
    Vocabulary(
        "relation",
        Relation,
        ("conformanceCited", "relation"),
        "relations",
        functools.partial(_cited_values, field="relation"),
    ),
    Vocabulary(
        "document kind",
        ReferenceKind,
        ("conformanceCited", "kind"),
        None,
        functools.partial(_cited_values, field="kind"),
    ),
    Vocabulary(
        "check kind",
        Kind,
        ("conformanceCheck", "kind"),
        None,
        functools.partial(_check_values, field="kind"),
    ),
    Vocabulary(
        "tolerance mode",
        ToleranceMode,
        ("conformanceCheck", "mode"),
        None,
        _tolerance_modes,
    ),
    Vocabulary(
        "verdict",
        Verdict,
        ("conformanceCheck", "verdict"),
        "verdicts",
        functools.partial(_check_values, field="verdict"),
    ),
)


def schema_enums(source: str) -> dict[tuple[str, str], frozenset[str]]:
    """Every ``z.enum`` in the content config, by object and field name.

    :param source: The text of ``site/src/content.config.ts``.
    :return: ``(object, field)`` to the values that object's field accepts.
    """
    starts = [(match.start(), match["name"]) for match in _OBJECT_RE.finditer(source)]
    enums: dict[tuple[str, str], frozenset[str]] = {}
    for index, (start, name) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(source)
        for match in _ENUM_RE.finditer(source, start, end):
            enums[name, match["field"]] = frozenset(_STRING_RE.findall(match["values"]))
    return enums


def page_labels(source: str) -> dict[tuple[str, str], frozenset[str]]:
    """Every label map in the page, by language and map name.

    :param source: The text of ``site/src/components/Conformance.astro``.
    :return: ``(language, map)`` to the values worded in that language.
    :raises LookupError: If the page no longer holds its two translation
        tables in the shape this reads, which is a defect in this gate and
        not in the page.
    """
    spanish = source.find(_SPANISH_BRANCH)
    english = source.find(_ENGLISH_BRANCH, spanish + 1)
    if spanish < 0 or english < 0:
        msg = (
            f"{PAGE_FILE.name} no longer writes its translation tables as one "
            f"ternary with the Spanish branch first, so this gate cannot tell "
            f"which language a label map belongs to."
        )
        raise LookupError(msg)
    labels: dict[tuple[str, str], frozenset[str]] = {}
    for match in _MAP_RE.finditer(source):
        language = "Spanish" if match.start() < english else "English"
        labels[language, match["name"]] = frozenset(
            found["key"] for found in _KEY_RE.finditer(match["body"])
        )
    return labels


def _cost(counts: collections.Counter[str], value: str) -> str:
    """How many rows of the committed artefact carry a value, in words."""
    rows = counts[value]
    if not rows:
        return "no row carries it yet"
    return f"{rows} row{'' if rows == 1 else 's'} of the artefact carry it"


def _schema_problems(
    vocabulary: Vocabulary,
    enums: Mapping[tuple[str, str], frozenset[str]],
    counts: collections.Counter[str],
) -> list[str]:
    """What the Zod enum accepts against what a check can produce."""
    obj, field = vocabulary.declared_in
    accepted = enums.get((obj, field))
    if accepted is None:
        return [
            f"{SCHEMA_FILE.name} no longer declares {obj}.{field} as a "
            f"z.enum([...]), so the {vocabulary.name} vocabulary is unguarded."
        ]
    return [
        f"{SCHEMA_FILE.name}: {obj}.{field} does not accept the "
        f"{vocabulary.name} {value!r} the checks produce ({_cost(counts, value)}); "
        f"the site build fails on every row that carries it."
        for value in sorted(vocabulary.expected - accepted)
    ] + [
        f"{SCHEMA_FILE.name}: {obj}.{field} accepts the {vocabulary.name} "
        f"{value!r}, which no check can produce any more; delete it."
        for value in sorted(accepted - vocabulary.expected)
    ]


def _label_problems(
    vocabulary: Vocabulary,
    labels: Mapping[tuple[str, str], frozenset[str]],
    languages: Iterable[str],
) -> list[str]:
    """What the page words against what a check can produce."""
    if vocabulary.labelled_as is None:
        return []
    problems = []
    for language in languages:
        worded = labels.get((language, vocabulary.labelled_as))
        if worded is None:
            problems.append(
                f"{PAGE_FILE.name} has no {language} `{vocabulary.labelled_as}` "
                f"map, so no {vocabulary.name} is worded in that language."
            )
            continue
        problems += [
            f"{PAGE_FILE.name}: the {language} `{vocabulary.labelled_as}` map "
            f"has no word for the {vocabulary.name} {value!r}; the page would "
            f"print the raw value beside the ones it does word."
            for value in sorted(vocabulary.expected - worded)
        ] + [
            f"{PAGE_FILE.name}: the {language} `{vocabulary.labelled_as}` map "
            f"words the {vocabulary.name} {value!r}, which no check can produce "
            f"any more; delete it."
            for value in sorted(worded - vocabulary.expected)
        ]
    return problems


def _artefact_problems(
    vocabulary: Vocabulary, counts: collections.Counter[str]
) -> list[str]:
    """A value in the committed artefact the enums cannot produce."""
    return [
        f"{ARTEFACT.name} carries the {vocabulary.name} {value!r}, which "
        f"{vocabulary.values.__name__} does not define ({_cost(counts, value)})."
        for value in sorted(frozenset(counts) - vocabulary.expected)
    ]


def problems() -> list[str]:
    """Everything the three statements of these vocabularies disagree on."""
    document = json.loads(ARTEFACT.read_text(encoding="utf8"))
    enums = schema_enums(SCHEMA_FILE.read_text(encoding="utf8"))
    labels = page_labels(PAGE_FILE.read_text(encoding="utf8"))
    languages = ("Spanish", "English")
    found: list[str] = []
    for vocabulary in VOCABULARIES:
        counts = vocabulary.carried_by(document)
        found += _artefact_problems(vocabulary, counts)
        found += _schema_problems(vocabulary, enums, counts)
        found += _label_problems(vocabulary, labels, languages)
    return found


def main() -> int:
    """Compare the vocabularies and report every disagreement."""
    found = problems()
    if found:
        print(
            "The site no longer speaks the vocabularies the checks produce:\n",
            file=sys.stderr,
        )
        for problem in found:
            print(f"  {problem}", file=sys.stderr)
        return 1
    worded = sum(1 for vocabulary in VOCABULARIES if vocabulary.labelled_as)
    values = sum(len(vocabulary.expected) for vocabulary in VOCABULARIES)
    print(
        f"Site vocabularies in step: {values} values across "
        f"{len(VOCABULARIES)} fields accepted by the content schema, "
        f"{worded} of the fields worded in both languages."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
