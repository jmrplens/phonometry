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
import re
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

#: How the page's own figure was written into the hand-written ``derived`` of
#: the rows that only converted it, and the unit it was printed in. The
#: ``degrees F`` and ``psi`` wordings are Ver and Beranek Table 14.1's; the
#: two ``sabins`` wordings are what ``_metric`` wrote for Long Table 7.1.
_CONVERSION_WORDINGS = (
    (
        re.compile(
            r"^(?P<figure>\S+) degrees F as the page prints it, by \(5/9\)\(F - 32\)$"
        ),
        "°F",
    ),
    (
        re.compile(
            r"^(?P<figure>\S+) psi as the page prints it, "
            r"by the exact 6894\.757293 Pa/psi$"
        ),
        "psi",
    ),
    (
        re.compile(
            r"^from the (?P<figure>\S+) sabins per 1000 cubic feet the page prints, "
        ),
        "sabins per 1000 ft3",
    ),
    (re.compile(r"^from the (?P<figure>\S+) sabins the page prints, "), "sabins"),
)

#: The rows whose hand-written ``derived`` said the page leaves the cell blank
#: and carries it from another row, by mapping.
CARRIED_ROWS = {
    "PUBLISHED_FLOW_RESISTANCE": (
        "ver-beranek-2006-table-8-7/sintered_fm_127",
        "ver-beranek-2006-table-8-7/sintered_fm_185",
        "ver-beranek-2006-table-8-7/sintered_347_10_20_ac3a_a",
        "ver-beranek-2006-table-8-7/sintered_347_10_30_ac3a_a",
        "ver-beranek-2006-table-8-7/sintered_fm_802",
        "ver-beranek-2006-table-8-7/sintered_fm_126",
        "ver-beranek-2006-table-8-7/sintered_fm_190",
        "ver-beranek-2006-table-8-7/sintered_347_50_30_ac3a_a",
    ),
    "PUBLISHED_DUCT_TRANSMISSION_LOSS": (
        "ashrae-2019-tables-29-to-34/t30_spiral_wound_610_gage_24_lined",
        "ashrae-2019-tables-29-to-34/t30_spiral_wound_610_gage_16",
    ),
    "PUBLISHED_IMPACT_INSULATION": (
        "harris-1995-tables-32-1-to-32-8/29",
        "harris-1995-tables-32-1-to-32-8/32",
        "harris-1995-tables-32-1-to-32-8/34B",
    ),
}


#: The row notes that said what the old hedges said, as the sentence each
#: had and the sentence it has now. ``None`` for a note the row did not have:
#: the musician of Long Table 7.1 prints its figures with no unit, which the
#: sabins recorded in ``converted`` would otherwise claim it prints.
NOTE_CHANGES: dict[tuple[str, str], tuple[str | None, str]] = {
    **{
        ("PUBLISHED_DUCT_TRANSMISSION_LOSS", key): (
            "The diameter cell is blank on the page, so the 610 mm this row "
            "carries was not read from it and is held as a derivation rather "
            "than as a printed number.",
            "The diameter cell is blank on the page, and the 610 mm this row "
            "serves is carried down from the row of its block that prints it "
            "rather than read from this row.",
        )
        for key in CARRIED_ROWS["PUBLISHED_DUCT_TRANSMISSION_LOSS"]
    },
    (
        "PUBLISHED_ABSORPTION_AREAS",
        "long-2014-table-7-1/musician_per_person_with_instrument",
    ): (
        None,
        "The page prints these six figures with no unit. They are held as "
        "sabins, square feet of absorption per person: the row is priced per "
        "person in a table set in inches and pounds, its figures run from 4.0 "
        "to 15.0 where no coefficient of the table passes 1.33, and the row "
        "below it names its sabins.",
    ),
}


def _renoted(name: str, key: str, row: Row) -> None:
    """Rewrite the note of *row* as :data:`NOTE_CHANGES` lists, in place.

    :raises ValueError: when the sentence the change replaces is not in the
        note, so that a step can never claim a rewrite it did not make.
    """
    change = NOTE_CHANGES.get((name, key))
    if change is None:
        return
    before, after = change
    note = row.get("note", "")
    if before is None:
        if note:
            msg = f"{name}[{key!r}] already has a note"
            raise ValueError(msg)
        row["note"] = after
        return
    if before not in note:
        msg = f"{name}[{key!r}]: the note does not say {before!r}"
        raise ValueError(msg)
    row["note"] = note.replace(before, after)


def _one_row_shape(name: str, key: str, row: Row) -> Row:
    """One row taken through the change that gave every row one shape.

    Three things moved, and nothing else may:

    * ``estimated``, a set the solids and the orthotropic woods each kept,
      became an entry of ``basis`` per field, with the value
      ``"estimated"``;
    * a hand-written ``derived`` that recorded a unit conversion became
      ``converted``, the page's figure and its unit, and one that recorded a
      value the page gives by reference to another row became ``carried``,
      word for word. ``derived`` keeps only what the library computes;
    * the notes of :data:`NOTE_CHANGES` stopped saying what the old hedge
      said, or started saying what the new one could not.
    """
    row = dict(row)
    _renoted(name, key, row)
    estimated = row.pop("estimated", [])
    if estimated:
        row["basis"] = dict.fromkeys(estimated, "estimated")
    derived = dict(row.pop("derived", {}))
    converted: dict[str, list[str]] = {}
    carried: dict[str, str] = {}
    for field, wording in list(derived.items()):
        if key in CARRIED_ROWS.get(name, ()):
            carried[field] = derived.pop(field)
            continue
        for pattern, unit in _CONVERSION_WORDINGS:
            match = pattern.match(wording)
            if match:
                converted[field] = [match["figure"], unit]
                del derived[field]
                break
    for hedge, entries in (
        ("derived", derived),
        ("converted", converted),
        ("carried", carried),
    ):
        if entries:
            row[hedge] = entries
    return row


def one_row_shape(
    catalogues: Mapping[str, Mapping[str, Row]],
) -> dict[str, dict[str, Row]]:
    """The whole dump taken through :func:`_one_row_shape`."""
    return {
        name: {key: _one_row_shape(name, key, row) for key, row in rows.items()}
        for name, rows in catalogues.items()
    }


#: The packaged table the resilient layers are read from since they became
#: catalogue rows. Before, they were written out in the module and keyed by
#: the row half alone.
RESILIENT_LAYER_TABLE = "hopkins-2007-table-a3"


#: The density cells Table A3 prints blank, with the row of their block that
#: prints the figure. The rows held the figure before as if each printed it.
RESILIENT_LAYER_CARRIED: dict[str, str] = {
    "mineral_wool_glass_36_25": (
        "carried down the blank cell of Table A3 from the 13 mm glass-wool row "
        "above it, which prints 36 kg/m3 once for the two rows of its block"
    ),
    "mineral_wool_glass_75_40": (
        "carried down the blank cell of Table A3 from the 25 mm glass-wool row "
        "above it, which prints 75 kg/m3 once for the two rows of its block"
    ),
    "rebond_foam_64_15": (
        "carried up the blank cell of Table A3 from the 20 mm rebond-foam row "
        "below it, which prints 64 kg/m3 once, level with the middle of the "
        "three rows of its block"
    ),
    "rebond_foam_64_25": (
        "carried down the blank cell of Table A3 from the 20 mm rebond-foam row "
        "above it, which prints 64 kg/m3 once, level with the middle of the "
        "three rows of its block"
    ),
}


def _resilient_layer_row(key: str, row: Row) -> Row:
    """One resilient layer taken through the change that made it a catalogue row."""
    row = dict(row)
    row["table"] = RESILIENT_LAYER_TABLE
    credit = row.pop("attributed_to", "")
    if credit:
        row["attributed_to"] = {"row": credit}
    if key in RESILIENT_LAYER_CARRIED:
        row["carried"] = {"density_kg_m3": RESILIENT_LAYER_CARRIED[key]}
    return row


def resilient_layer_row(
    catalogues: Mapping[str, Mapping[str, Row]],
) -> dict[str, dict[str, Row]]:
    """The dump taken through the change that made the resilient layers rows.

    Hopkins Table A3 moved out of the module into a packaged data file and
    its fifteen rows became catalogue rows like every other. Four things
    moved, and nothing else may:

    * the key gained the table half every catalogue key has,
      ``"hopkins-2007-table-a3/<row>"``, in the same order;
    * ``table`` names that table;
    * ``attributed_to``, a string on the four rebond foams, became the mapping
      every other row holds, the credit covering the whole row;
    * the four rows whose density cell the page prints blank, under or over
      the row of their block that prints it, gained a ``carried`` entry for
      ``density_kg_m3`` naming that row (:data:`RESILIENT_LAYER_CARRIED`).
      The density itself did not change.

    Every quantity became optional and none changed. The stiffness stays in
    ``dynamic_stiffness_n_m3``: the heading of Table A3 prints ``s'``, which
    the book defines as the stiffness of the installed layer, so the apparent
    ``s't`` field the rows gained stays empty and the dump leaves it out.
    """
    out = {name: dict(rows) for name, rows in catalogues.items()}
    out["PUBLISHED_RESILIENT_LAYERS"] = {
        f"{RESILIENT_LAYER_TABLE}/{key}": _resilient_layer_row(key, row)
        for key, row in catalogues["PUBLISHED_RESILIENT_LAYERS"].items()
    }
    return out


#: The six ground surfaces whose porosity Cox Table 6.7 prints in per cent,
#: in a column that prints a fraction on every other row and states no unit,
#: with the figure each prints there.
GROUND_POROSITY_IN_PER_CENT: Mapping[str, str] = {
    "cox-2017-table-6-7/mineral_layer_beneath_mixed_deciduous_forest": "36.5",
    "cox-2017-table-6-7/humus_on_pine_forest_floor": "58.1",
    "cox-2017-table-6-7/pine_forest_litter": "38.9",
    "cox-2017-table-6-7/grass_root_layer_in_loamy_sand": "48 ± 4",
    "cox-2017-table-6-7/loamy_sand": "37.5",
    "cox-2017-table-6-7/bare_sandy_plain": "26.9",
}

#: The sentence each of those six notes had, and the one it has now.
GROUND_POROSITY_NOTE = (
    "on the page it is plainly a percentage, but it is transcribed exactly as printed.",
    "on the page it is plainly a percentage, but the page does not say so, and "
    "the cell is held as misprinted (docs/ERRATA.md).",
)


def ground_porosity_misprint(figure: str) -> str:
    """What ``misprinted['porosity']`` says on one of the six rows."""
    return (
        f"the page prints “{figure}” in its Porosity column, which states no unit "
        "and prints a fraction on every other row, and a porosity is the open "
        "fraction of a volume, so it cannot pass 1. The figure reads as a per "
        "cent, but the page does not say so, and this library does not convert "
        "a unit the page does not print. The defect is registered in "
        "docs/ERRATA.md under “Cox & D'Antonio, Acoustic Absorbers and Diffusers "
        "3e (2017), Table 6.7”."
    )


def _porosity_misprinted(name: str, key: str, row: Row) -> Row:
    """One of the six ground surfaces with its porosity held as misprinted.

    :raises ValueError: when the row holds no porosity to empty, or its note
        does not say the sentence the step rewrites.
    """
    row = dict(row)
    if "porosity" not in row:
        msg = f"{name}[{key!r}] holds no porosity to empty"
        raise ValueError(msg)
    del row["porosity"]
    uncertainty = {
        field: spread
        for field, spread in row.get("uncertainty", {}).items()
        if field != "porosity"
    }
    if uncertainty:
        row["uncertainty"] = uncertainty
    else:
        row.pop("uncertainty", None)
    row["misprinted"] = {
        **row.get("misprinted", {}),
        "porosity": ground_porosity_misprint(GROUND_POROSITY_IN_PER_CENT[key]),
    }
    before, after = GROUND_POROSITY_NOTE
    if before not in row.get("note", ""):
        msg = f"{name}[{key!r}]: the note does not say {before!r}"
        raise ValueError(msg)
    row["note"] = row["note"].replace(before, after)
    return row


def row_contract(
    catalogues: Mapping[str, Mapping[str, Row]],
) -> dict[str, dict[str, Row]]:
    """The dump taken through the change that made every row check itself.

    Every row is now held, when it is built, to the contract
    ``CatalogueRow.__post_init__`` describes, and every packaged row but six
    already met it. Those six are ground surfaces of Cox Table 6.7 whose
    porosity the page prints in per cent (26.9 to 58.1) in a column of
    fractions that states no unit, and a porosity above 1 is refused. One
    thing moved for them, and nothing else may:

    * ``porosity`` was emptied, the ``48 ± 4`` of the grass root layer took
      its uncertainty with it, and ``misprinted['porosity']`` quotes the
      figure the page prints; the six notes say the cell is held as
      misprinted.
    """
    out = {name: dict(rows) for name, rows in catalogues.items()}
    name = "PUBLISHED_GROUND"
    ground = dict(out[name])
    for key in GROUND_POROSITY_IN_PER_CENT:
        ground[key] = _porosity_misprinted(name, key, ground[key])
    out[name] = ground
    return out


#: Every change since the baseline, oldest first.
CHANGES: tuple[Change, ...] = (one_row_shape, resilient_layer_row, row_contract)


def expected() -> dict[str, dict[str, Row]]:
    """What the published catalogues should hold today."""
    catalogues: dict[str, dict[str, Row]] = baseline()
    for change in CHANGES:
        catalogues = change(catalogues)
    return catalogues
