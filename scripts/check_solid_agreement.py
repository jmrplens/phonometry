#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Report what the books disagree about, and fail when one of them is a typo.

The solids catalogue holds the same material from up to four books. That is
the point of it: a published value is worth more beside another published
value than alone. But two numbers that disagree are one of three things, and
only the reader can tell them apart if something separates them first.

1. **A transcription error**, almost always ours. It is the only one of the
   three this script fails on, and density is where it shows: every density
   this script does not already accept agrees across these books to within
   2,6 per cent, because a density is the one property a table cannot get very
   wrong without the material becoming a different material. A density that
   disagrees by more than :data:`DENSITY_TOLERANCE`, which is 8 per cent, is a
   digit somebody typed wrong, and the somebody is usually whoever transcribed
   the page. Anything under that is not reported at all.

2. **A disagreement between the books themselves**, which is not a defect of
   either and must not be smoothed over. Moduli disagree by twenty and thirty
   per cent across these six tables, and that is the real spread of the
   literature rather than anybody's mistake. Those are reported and never
   failed. :data:`ACCEPTED` holds the density disagreements that fall in this
   class, each with the reason it is not a typo.

3. **A defect in a page**, which belongs in ``docs/ERRATA.md`` with its
   evidence, not here. This script can point at one, and has, but it cannot
   establish one: that takes the printed page.

What it compares is magnitudes and never column headings. Three of the six
books print a "longitudinal speed" and they are not the same wave, which is
why the catalogue keeps the bar, plate and unbounded speeds in three fields
and the unqualified one in a fourth. Comparing by heading would report a
sixteen per cent disagreement between two books that agree perfectly.

Rows the page marks as a specimen of their own, through
:attr:`~phonometry.solids.SolidMaterial.variant`, are reported but never
failed on: Bies prints annealed, rolled and sheet lead, and they are three
things under one name. The failing check only groups rows that no page
distinguished.

Usage::

    python scripts/check_solid_agreement.py          # report and check
    python scripts/check_solid_agreement.py --report # report only, never fails

Exit status 0 when every density agrees, 1 otherwise, naming the material, the
books and the values.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from collections import defaultdict
from typing import TYPE_CHECKING

from phonometry.solids import PUBLISHED_SOLIDS, SolidMaterial

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

#: How far the density of one material may vary between books before it is
#: read as a typo rather than as a disagreement. The widest spread the script
#: does not accept is iron at 2,6 per cent, and a mistyped digit moves a
#: density by ten per cent at the very least, so the band is set between the
#: two. The one accepted disagreement is far above it, at 21,5 per cent, which
#: is what a real difference between books looks like beside a rounding.
DENSITY_TOLERANCE = 0.08

#: Density disagreements that are real rather than typed, with the reason.
#: This is a ratchet in both directions: an entry whose books come to agree
#: fails until it is deleted, and a new disagreement fails until somebody has
#: read the pages and written down which of the three things it is.
ACCEPTED: dict[str, str] = {
    "polypropylene": (
        "Mechel prints 1100 kg/m3 on printed page 530 and Bies 905 on printed "
        "page 720. Read again at 300 dpi, the 1100 is what the page says, and "
        "Mechel's own Z_m column is computed from it, so his table is "
        "consistent with itself. Polypropylene is the lightest common "
        "thermoplastic and floats, so 905 is the value the material has; but "
        "that is a fact about the material rather than something either page "
        "contradicts, so it is a disagreement between books and not an errata."
    ),
}

#: The quantities worth comparing, in the order the report prints them, with
#: the divisor that makes the printed number readable.
COMPARED: tuple[tuple[str, float, str], ...] = (
    ("density_kg_m3", 1.0, "kg/m3"),
    ("youngs_modulus_pa", 1e9, "GPa"),
    ("shear_modulus_pa", 1e9, "GPa"),
    ("poisson_ratio", 1.0, ""),
    ("bar_longitudinal_speed_m_s", 1.0, "m/s"),
    ("plate_longitudinal_speed_m_s", 1.0, "m/s"),
    ("bulk_longitudinal_speed_m_s", 1.0, "m/s"),
    ("thickness_critical_frequency_product_m_hz", 1.0, "m Hz"),
)

#: How far apart two books have to be, on a row neither of them marked as a
#: specimen of its own, before the default run prints the material at all.
#: Everything is in ``--report``; this is the line above which a reader should
#: go and look at the pages, and it is set well above the spread of the moduli,
#: which run to thirty per cent between books without anybody being wrong.
NOTABLE = 0.5


def normalised(name: str) -> str:
    """The material name reduced to what two books would have to share.

    Case and punctuation only, never the variant: Bies prints aerated concrete
    at 300 to 600 kg/m3 beside normal concrete at 2300, and folding those
    together would invent a factor of five where the page put a distinction.

    Digits stay for the same reason. Bies prints Nylon 6, Nylon 66 and Nylon 12
    as three rows, and they are three polymers rather than one material a page
    happened to number.
    """
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", name.lower()).split())


def _reading(row: SolidMaterial, field: str) -> tuple[str, float, bool] | None:
    """``(book, value, derived)`` for a row that has this quantity."""
    value = getattr(row, field)
    if value is None:
        return None
    return row.table, float(value), row.is_derived(field)


def spread(readings: list[tuple[str, float, bool]]) -> float:
    """How far apart the extremes are, as a fraction of the smaller.

    A quantity at or below zero has no ratio to anything, and none of the
    compared ones can legitimately reach it, so the answer is infinite rather
    than an exception: the gate is then loud about a row somebody has to look
    at instead of dying on it.
    """
    values = [value for _, value, _ in readings]
    if min(values) <= 0.0:
        return math.inf
    return max(values) / min(values) - 1.0


def groups(
    rows: Iterable[SolidMaterial], *, distinguished: bool
) -> dict[str, list[SolidMaterial]]:
    """Materials by name, across the books that print them.

    The rows are a parameter and not the catalogue itself so that a test can
    seed a disagreement and watch the gate go red on it.

    :param distinguished: whether to include rows the page marks as a specimen
        of its own. The report wants them; the failing check does not, because
        annealed lead and lead sheet are not the same thing to disagree about.
    """
    found: dict[str, list[SolidMaterial]] = defaultdict(list)
    for row in rows:
        if row.variant and not distinguished:
            continue
        found[normalised(row.name)].append(row)
    return {
        name: rows
        for name, rows in found.items()
        if len({row.table for row in rows}) >= 2
    }


def _readings(rows: list[SolidMaterial], field: str) -> list[tuple[str, float, bool]]:
    """Every book that prints this quantity for these rows, in table order."""
    return [r for row in rows if (r := _reading(row, field))]


def _worst(rows: list[SolidMaterial]) -> float:
    """The widest disagreement across the compared quantities, or zero.

    Measured on the rows no page distinguished, for the same reason the
    failing check ignores the rest: expanded polystyrene foam travels sound at
    a sixth of the speed moulded polystyrene does, and the two books are not
    disagreeing when they say so.
    """
    plain = [row for row in rows if not row.variant]
    apart = [0.0]
    for field, _, _ in COMPARED:
        readings = _readings(plain, field)
        if len({book for book, _, _ in readings}) >= 2:
            apart.append(spread(readings))
    return max(apart)


def report(catalogue: Iterable[SolidMaterial], *, everything: bool) -> list[str]:
    """Every quantity two books both print, and how far apart they are."""
    lines: list[str] = []
    for name, rows in sorted(groups(catalogue, distinguished=True).items()):
        if not everything and _worst(rows) < NOTABLE:
            continue
        books = len({row.table for row in rows})
        heading = f"{name} ({len(rows)} rows, {books} books)"
        entries: list[str] = []
        for field, unit, symbol in COMPARED:
            readings = _readings(rows, field)
            if len({book for book, _, _ in readings}) < 2:
                continue
            shown = ", ".join(
                f"{book.split('-')[0]}{'*' if derived else ''} {value / unit:.4g}"
                for book, value, derived in readings
            )
            entries.append(
                f"    {field:44s} {spread(readings) * 100:7.1f}%  "
                f"{shown} {symbol}".rstrip()
            )
        if entries:
            lines.append(heading)
            lines.extend(entries)
    return lines


def problems(
    catalogue: Iterable[SolidMaterial], accepted: Mapping[str, str] = ACCEPTED
) -> list[str]:
    """Densities that disagree by more than one page can round away.

    :param accepted: the disagreements somebody has read the pages for. It is
        a parameter for the same reason the rows are: a test that checks the
        ratchet has to supply its own registry rather than edit this one.
    """
    undistinguished = groups(catalogue, distinguished=False)
    found: list[str] = []
    compared: set[str] = set()
    for name, rows in sorted(undistinguished.items()):
        readings = _readings(rows, "density_kg_m3")
        if len({book for book, _, _ in readings}) < 2:
            continue
        compared.add(name)
        apart = spread(readings)
        if apart <= DENSITY_TOLERANCE:
            if name in accepted:
                found.append(
                    f"{name}: the books agree on the density to "
                    f"{apart * 100:.1f} per cent, so its entry in ACCEPTED is "
                    "stale and should be deleted"
                )
            continue
        if name in accepted:
            continue
        shown = ", ".join(
            f"{book.split('-')[0]} {value:g}" for book, value, _ in readings
        )
        found.append(
            f"{name}: the densities are {apart * 100:.1f} per cent apart "
            f"({shown} kg/m3). Read the pages: a density that disagrees by "
            "this much is usually a digit typed wrong, and if it is not, say "
            "why in ACCEPTED at the top of this script"
        )
    found.extend(
        f"{name}: is in ACCEPTED and no two books print a density for it"
        for name in sorted(set(accepted) - compared)
    )
    return found


def verdict(
    found: list[str], compared: int, accepted: int, *, reporting: bool
) -> tuple[list[str], int]:
    """What to print after the comparison, and what to exit with.

    The clean summary is the only line that tells a reader the catalogue is
    sound, so it is printed when and only when nothing was found. ``--report``
    returns 0 over a real disagreement, by design, which is exactly why it
    must not also print a line saying there was none.
    """
    if found:
        return (
            [
                "::error::published books disagree about a density",
                *(f"  {p}" for p in found),
            ],
            0 if reporting else 1,
        )
    return (
        [
            f"{compared} material(s) appear in two or more books, and every "
            f"density agrees within {DENSITY_TOLERANCE * 100:g} per cent except "
            f"{accepted} the registry accepts with a reason."
        ],
        0,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        action="store_true",
        help="print the comparison and return 0 whatever it says",
    )
    arguments = parser.parse_args()

    catalogue = list(PUBLISHED_SOLIDS.values())
    printed = report(catalogue, everything=arguments.report)
    if printed:
        if not arguments.report:
            print(
                f"Materials whose books are more than {NOTABLE * 100:g} per "
                "cent apart on something. Pass --report for all of them.\n"
            )
        for line in printed:
            print(line)
        print("\n* = derived by this library from the row's other cells\n")

    lines, status = verdict(
        problems(catalogue),
        len(groups(catalogue, distinguished=True)),
        len(ACCEPTED),
        reporting=arguments.report,
    )
    for line in lines:
        print(line)
    return status


if __name__ == "__main__":
    sys.exit(main())
