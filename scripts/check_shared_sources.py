#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Check the rows two books took from the same place against each other.

A catalogue that holds the same material from several books is worth more than
one that holds it from one, and the reason is this script. Where two books
print a material and credit the same study for it, they are not two
measurements: they are two readings of one measurement, passed through two
editorial pipelines and two unit conventions. A disagreement there is somebody
misreading a page, and the somebody is usually whoever transcribed it.

What it pairs
-------------
Two rows pair when they are in different books, carry the same material name,
and their ``attributed_to`` name one source in common. Bies and Cox both take
sugar snow from Embleton, Piercy and Daigle (1983), so their two rows pair; a
grass that Cox fitted himself and Bies measured himself does not, because
those are two measurements and are free to disagree.

The name has to match for the pair to be made, which leaves out the pairs only
a reader can see: Cox's "Mineral wool" and Mechel's "Mineral fibre materials"
are the same row of the same compilation under two names, and no string
comparison should be trusted to say so. Those live in the tests, written out
by hand, where a human decided it.

What counts as agreement
------------------------
Overlap, and not equality. A book that prints an interval and a book that
prints a value from one study inside it agree: Bies gives a bare sandy plain
250 to 500 kPa s/m2 and Cox gives 370, which is the same ground seen at two
resolutions. What cannot happen is two readings of one study that do not
overlap at all, and that is what this fails on.

Usage::

    python scripts/check_shared_sources.py           # report and check
    python scripts/check_shared_sources.py --report  # report only, never fails

Exit status 0 when every pair overlaps, 1 otherwise, naming the material, the
books, the shared source and the two readings.
"""

from __future__ import annotations

import argparse
import pathlib
import sys
from collections import defaultdict
from typing import TYPE_CHECKING, NamedTuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from check_solid_agreement import normalised  # noqa: E402

from phonometry.environment.propagation import PUBLISHED_GROUND  # noqa: E402
from phonometry.materials.absorbers import PUBLISHED_POROUS  # noqa: E402
from phonometry.solids import PUBLISHED_SOLIDS  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from phonometry._internal.catalogue import CatalogueRow

#: The catalogues to walk, and the quantities worth comparing in each. A
#: quantity only one of the two books prints is skipped, so the list can be
#: generous; what it must not contain is two quantities one book prints under
#: one heading, which is why the wave speeds of the solids are named one by
#: one rather than compared as "the speed".
CATALOGUES: tuple[tuple[str, Mapping[str, CatalogueRow], tuple[str, ...]], ...] = (
    (
        "solids",
        PUBLISHED_SOLIDS,
        (
            "density_kg_m3",
            "youngs_modulus_pa",
            "shear_modulus_pa",
            "poisson_ratio",
            "bar_longitudinal_speed_m_s",
            "plate_longitudinal_speed_m_s",
            "bulk_longitudinal_speed_m_s",
        ),
    ),
    (
        "porous",
        PUBLISHED_POROUS,
        (
            "flow_resistivity_pa_s_m2",
            "porosity",
            "tortuosity",
            "viscous_length_um",
            "thermal_length_um",
            "fibre_diameter_um",
        ),
    ),
    (
        "ground",
        PUBLISHED_GROUND,
        (
            "flow_resistivity_pa_s_m2",
            "porosity",
            "porosity_decay_rate_per_m",
        ),
    ),
)

#: Pairs that share a source, do not overlap, and are not a defect, with the
#: reason somebody read the pages and decided so. Keyed by
#: ``"<catalogue>/<material>/<quantity>"``.
ACCEPTED: dict[str, str] = {}


class Reading(NamedTuple):
    """What one book publishes for one quantity of one row.

    :ivar book: The book, as the first word of the table key names it.
    :ivar table: The table the row came off.
    :ivar low: The bottom of what the page allows, which is the value itself
        when the page printed one.
    :ivar high: The top of it.
    """

    book: str
    table: str
    low: float
    high: float

    def spelt(self) -> str:
        """The reading as the report prints it."""
        if self.low == self.high:
            return f"{self.book} {self.low:g}"
        return f"{self.book} {self.low:g} to {self.high:g}"


def book_of(table: str) -> str:
    """The book a table key belongs to: ``"cox-2017-table-6-7"`` is Cox."""
    return table.split("-")[0]


def sources(row: CatalogueRow) -> frozenset[str]:
    """Every study the row credits, however the page attached the credit.

    A credit reaches a row per cell, per row or per table, and which of the
    three it is says nothing about what was copied from whom; all that matters
    here is the set of studies named.
    """
    named: set[str] = set()
    for text in row.attributed_to.values():
        named.update(piece.strip() for piece in text.split(";") if piece.strip())
    return frozenset(named)


def reading(row: CatalogueRow, field: str) -> Reading | None:
    """What *row* publishes for *field*, as the interval it allows.

    A printed value is an interval of zero width, an interval is itself, and a
    cell listing several readings spans them: a book that lists 25, 207 and 230
    has said the quantity is somewhere in there, which is what an overlap test
    needs. A cell holding a word, or nothing, is not a reading at all.
    """
    value = getattr(row, field, None)
    if value is not None:
        return Reading(book_of(row.table), row.table, float(value), float(value))
    interval = row.ranges.get(field)
    if interval is not None:
        low, high = interval
        return Reading(book_of(row.table), row.table, float(low), float(high))
    listed = row.reported.get(field)
    if listed:
        flat: list[float] = []
        for entry in listed:
            flat.extend(entry if isinstance(entry, tuple) else (entry,))
        return Reading(book_of(row.table), row.table, min(flat), max(flat))
    return None


def overlap(first: Reading, second: Reading) -> bool:
    """Whether the two readings leave any value both books allow."""
    return first.low <= second.high and second.low <= first.high


def pairs(
    catalogue: Iterable[CatalogueRow],
) -> list[tuple[str, CatalogueRow, CatalogueRow, frozenset[str]]]:
    """Rows of two books, under one name, crediting one study between them."""
    by_name: dict[str, list[CatalogueRow]] = defaultdict(list)
    for row in catalogue:
        by_name[normalised(row.name)].append(row)

    found: list[tuple[str, CatalogueRow, CatalogueRow, frozenset[str]]] = []
    for name, rows in sorted(by_name.items()):
        for index, first in enumerate(rows):
            for second in rows[index + 1 :]:
                if book_of(first.table) == book_of(second.table):
                    continue
                shared = sources(first) & sources(second)
                if shared:
                    found.append((name, first, second, shared))
    return found


def compare(
    label: str,
    catalogue: Iterable[CatalogueRow],
    fields: tuple[str, ...],
    accepted: Mapping[str, str] = ACCEPTED,
) -> tuple[list[str], list[str], int]:
    """Every shared-source pair of one catalogue, and what disagrees.

    :param label: The catalogue's name, for the keys of *accepted*.
    :param catalogue: Its rows.
    :param fields: The quantities to compare.
    :param accepted: Disagreements somebody has read the pages for. A
        parameter so that a test can supply its own registry rather than edit
        this one.
    :return: The report lines, the failures, and how many pairs were compared.
    """
    lines: list[str] = []
    failures: list[str] = []
    compared = 0
    for name, first, second, shared in pairs(catalogue):
        entries: list[str] = []
        for field in fields:
            one, other = reading(first, field), reading(second, field)
            if one is None or other is None:
                continue
            compared += 1
            agrees = overlap(one, other)
            key = f"{label}/{name}/{field}"
            entries.append(
                f"    {field:36s} {'overlap' if agrees else 'APART':>8}  "
                f"{one.spelt()}  |  {other.spelt()}"
            )
            if agrees or key in accepted:
                continue
            failures.append(
                f"{label}: {name}: {first.table} and {second.table} both credit "
                f"{min(shared)!r} and their {field} do not overlap "
                f"({one.spelt()}, {other.spelt()}). Read the two pages: two "
                f"readings of one study cannot exclude each other, and if they "
                f"really do, say why in ACCEPTED under {key!r}"
            )
        if entries:
            lines.append(f"{label}: {name} ({min(shared)})")
            lines.extend(entries)
    return lines, failures, compared


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        action="store_true",
        help="print every pair and return 0 whatever it says",
    )
    arguments = parser.parse_args()

    printed: list[str] = []
    failures: list[str] = []
    compared = 0
    for label, catalogue, fields in CATALOGUES:
        lines, found, count = compare(label, catalogue.values(), fields)
        printed.extend(lines)
        failures.extend(found)
        compared += count

    if arguments.report and printed:
        for line in printed:
            print(line)
        print()

    if failures:
        print("::error::two books credit one study and disagree about it")
        for failure in failures:
            print(f"  {failure}")
        return 0 if arguments.report else 1

    print(
        f"{compared} quantity reading(s) where two books credit the same "
        f"study overlap, across {len(CATALOGUES)} catalogues."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
