#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Every published catalogue, dumped cell by cell, and what changed it since.

The catalogues are data the library stands behind, and the gates that watch
them each see part of it: the provenance gate reads the citations, the page
generator's ``--check`` reads the numbers as the site prints them. Neither
sees the last digit of a float, and a change to how a row is built (a
conversion done in a different order, a hedge moved from one field to
another) moves exactly that and nothing a reader of the page would spot.

So the whole of every ``PUBLISHED_*`` mapping was dumped once, every float by
its ``repr``, into ``tests/data/published_catalogues/baseline.json``, before
the row shape was reworked. That file is never regenerated. Each change that
is meant to move a published cell is written here instead, as a step that
takes the baseline forward, and ``tests/test_published_catalogue_fingerprint.py``
asserts that the baseline carried through every step is exactly what the
library builds today. A cell that moves without a step fails; a step that
claims a change the library did not make fails too.
"""

from __future__ import annotations

import dataclasses
import importlib
import json
import pathlib
import pkgutil
from collections.abc import Callable, Mapping
from typing import Any, cast

#: Where the dump taken before the row shape was reworked is kept.
BASELINE = (
    pathlib.Path(__file__).resolve().parent
    / "data"
    / "published_catalogues"
    / "baseline.json"
)

#: What a dumped value is made of: what JSON has, and nothing else.
type Json = None | bool | int | float | str | list[Json] | dict[str, Json]

#: One row as it is dumped: field name to its canonical value.
Row = dict[str, Any]

#: A change to the published cells, as a step that takes a dump forward.
Change = Callable[[Mapping[str, Mapping[str, Row]]], dict[str, dict[str, Row]]]


def _is_empty(value: object) -> bool:
    """Whether a field holds nothing, so that the dump can leave it out.

    A field that holds nothing on every row is a column no row fills, and
    leaving it out keeps a new field with an empty default from moving every
    row of every table.
    """
    if value is None or value == "":
        return True
    if isinstance(value, (Mapping, tuple, list, frozenset, set)):
        return len(value) == 0
    return False


def canonical(value: object) -> Json:
    """*value* as JSON can hold it, exactly.

    A float stays a float: ``json`` writes one with ``repr``, which reads back
    as the same double, so the dump keeps every digit. A set is sorted, a
    tuple is a list, a mapping is keyed by text, and a dataclass is its
    fields, minus the ones that hold nothing.

    :param value: A field of a catalogue row, or a row.
    :return: The same content, built only of what JSON has.
    :raises TypeError: for a value no catalogue row should hold.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (frozenset, set)):
        return sorted(value)
    if isinstance(value, (tuple, list)):
        return [canonical(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): canonical(item) for key, item in value.items()}
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: canonical(getattr(value, field.name))
            for field in dataclasses.fields(value)
            if not _is_empty(getattr(value, field.name))
        }
    msg = f"a catalogue row should not hold a {type(value).__name__}"
    raise TypeError(msg)


def published_mappings() -> dict[str, Mapping[str, object]]:
    """Every ``PUBLISHED_*`` mapping the public packages export, by name.

    Found rather than listed, so that a new catalogue lands in the dump the
    day it is published rather than the day someone remembers to add it here.
    """
    import phonometry

    found: dict[str, Mapping[str, object]] = {}
    for module in pkgutil.iter_modules(phonometry.__path__):
        if module.name.startswith("_") or not module.ispkg:
            continue
        package = importlib.import_module(f"phonometry.{module.name}")
        for name in getattr(package, "__all__", ()):
            value = getattr(package, name)
            if name.startswith("PUBLISHED_") and isinstance(value, Mapping):
                found[name] = value
    return dict(sorted(found.items()))


def dump() -> dict[str, dict[str, Row]]:
    """Every published row as it is built now, through a JSON round trip.

    The round trip is what makes the dump comparable with the baseline read
    from disk: both sides are then made of the same types.
    """
    live = {
        name: {key: canonical(row) for key, row in mapping.items()}
        for name, mapping in published_mappings().items()
    }
    return cast(
        "dict[str, dict[str, Row]]", json.loads(json.dumps(live, ensure_ascii=False))
    )


def render(catalogues: Mapping[str, Mapping[str, Row]]) -> str:
    """The dump as text, one row per line so that a change is one line."""
    lines = ["{"]
    names = list(catalogues)
    for index, name in enumerate(names):
        lines.append(f"{json.dumps(name)}: {{")
        rows = list(catalogues[name].items())
        for position, (key, row) in enumerate(rows):
            comma = "," if position < len(rows) - 1 else ""
            body = json.dumps(row, ensure_ascii=False, sort_keys=True)
            lines.append(f"{json.dumps(key, ensure_ascii=False)}: {body}{comma}")
        lines.append("}," if index < len(names) - 1 else "}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def baseline() -> dict[str, dict[str, Row]]:
    """The dump taken before the row shape was reworked."""
    return cast(
        "dict[str, dict[str, Row]]", json.loads(BASELINE.read_text(encoding="utf-8"))
    )


# ---------------------------------------------------------------------------
# The changes, in the order they were made. Each one takes a dump forward.
# ---------------------------------------------------------------------------

#: Every change since the baseline, oldest first.
CHANGES: tuple[Change, ...] = ()


def expected() -> dict[str, dict[str, Row]]:
    """What the published catalogues should hold today."""
    catalogues: dict[str, dict[str, Row]] = baseline()
    for change in CHANGES:
        catalogues = change(catalogues)
    return catalogues
