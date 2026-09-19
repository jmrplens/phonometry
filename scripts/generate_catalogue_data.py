#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Dump the published catalogues for the site to render.

The rows live in the package, as one data file per published table, and the
loader that reads them adds what follows from the cells a page printed: the
three wave speeds of a solid, the shear modulus of a frame whose page printed
a Young's modulus. A page of the site that imported the data files directly
would show the printed half and miss the derived one, and would have to
interpret the hedges (a range, a bound, a word where a number would be) in
JavaScript, which is a second implementation of a thing the library already
does.

So the site reads what the **library** holds, dumped here into one module it
imports at build time. The same arrangement as the conformance counts and the
API sidebar: Python writes, Astro imports, and CI fails if the artefact drifts
from a fresh run, which is what stops the page from still showing last
quarter's catalogue.

Every value arrives already formatted for reading. A row of a materials table
is not a row of floats: a density may be an interval the book declined to
collapse, a loss factor may be an upper bound, a tortuosity may be the word
"model". Formatting in Python keeps the rendering rules in the same place as
the rules about what a cell means, and leaves the component to place text.

Run through ``make catalogue-data``; ``--check`` exits non-zero when the
committed file differs from a fresh run, which is what CI does.
"""

from __future__ import annotations

import argparse
import decimal
import math
import pathlib
import sys
from typing import TYPE_CHECKING, Any

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from phonometry.building.prediction.detailed_model import EN_12354_AIR  # noqa: E402
from phonometry.fluids import PUBLISHED_FLUIDS  # noqa: E402
from phonometry.materials.absorbers import PUBLISHED_POROUS  # noqa: E402
from phonometry.materials.absorbers.airflow_resistance import ANNEX_A_AIR  # noqa: E402
from phonometry.materials.absorbers.porous import PUBLISHED_AIR  # noqa: E402
from phonometry.simulation.ntff import SIMULATION_AIR  # noqa: E402
from phonometry.solids import PUBLISHED_SOLIDS  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from phonometry._internal.catalogue import CatalogueRow

#: Where the site imports the catalogues from.
OUTPUT = (
    pathlib.Path(__file__).resolve().parents[1] / "site/src/generated/catalogues.mjs"
)

#: The columns each catalogue shows, as ``(field, heading, unit)``. A unit of
#: the empty string is a dimensionless quantity, which is not the same as a
#: quantity whose unit the heading already carries.
SOLID_COLUMNS = (
    ("density_kg_m3", "Density", "kg/m³"),
    ("youngs_modulus_pa", "Young's modulus", "Pa"),
    ("shear_modulus_pa", "Shear modulus", "Pa"),
    ("poisson_ratio", "Poisson ratio", ""),
    ("longitudinal_speed_m_s", "Longitudinal speed", "m/s"),
    ("bar_longitudinal_speed_m_s", "Bar speed", "m/s"),
    ("plate_longitudinal_speed_m_s", "Plate speed", "m/s"),
    ("bulk_longitudinal_speed_m_s", "Bulk speed", "m/s"),
    ("transverse_speed_m_s", "Transverse speed", "m/s"),
    ("loss_factor", "Loss factor", ""),
    ("flexural_loss_factor", "Flexural loss factor", ""),
    ("longitudinal_loss_factor", "Longitudinal loss factor", ""),
    ("in_situ_loss_factor", "In-situ loss factor", ""),
    ("thickness_critical_frequency_product_m_hz", "h.f_c", "m·Hz"),
)

POROUS_COLUMNS = (
    ("flow_resistivity_pa_s_m2", "Flow resistivity", "Pa·s/m²"),
    ("porosity", "Porosity", ""),
    ("tortuosity", "Tortuosity", ""),
    ("viscous_length_um", "Viscous length", "µm"),
    ("thermal_length_um", "Thermal length", "µm"),
    ("thermal_permeability_m2", "Thermal permeability", "m²"),
    ("frame_density_kg_m3", "Frame density", "kg/m³"),
    ("thickness_mm", "Thickness", "mm"),
    ("youngs_modulus_pa", "Young's modulus", "Pa"),
    ("shear_modulus_pa", "Shear modulus", "Pa"),
    ("poisson_ratio", "Poisson ratio", ""),
    ("structural_loss_factor", "Structural loss factor", ""),
)

#: Significant figures a **derived** number is rounded to before it is shown.
#: Its inputs were printed to four at most, so a plate speed worked out of a
#: modulus and a density is not known to fifteen and must not be shown to
#: fifteen. A value the page itself printed is shown as stored, whatever its
#: length: the 345,866 52 m/s of the metrology annex is what that annex
#: prints, and rounding it here would erase what distinguishes it.
_DERIVED_FIGURES = 4

#: Below this magnitude a number reads better as a mantissa and an exponent
#: than as a run of leading zeros.
_SMALL = 1e-3

#: The narrow no-break space this corpus groups thousands with, which is what
#: keeps a group from breaking across a line.
_GROUP = "\u202f"


def _plain(value: float) -> str:
    """*value* as a decimal string: no exponent, no digit it does not carry.

    ``repr`` gives the shortest string that round-trips, which is the digits
    the number actually has, and :class:`~decimal.Decimal` turns that into
    positional notation without inventing any. ``format(value, "g")`` cannot
    be used: it drops into exponent form at 1e5, which is where the densities
    and the moduli of these tables live.

    :param value: The number.
    :return: Its positional form, trailing zeros trimmed.
    """
    text = format(decimal.Decimal(repr(value)), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def number(value: float, *, exact: bool = True) -> str:
    """One number, written the way this corpus writes numbers.

    The decimal separator is the comma, as in every figure and every table of
    this documentation, and the thousands are separated by the narrow no-break
    space.

    :param value: The number.
    :param exact: Whether a page printed it, in which case every digit it
        carries is shown. A number this library derived is rounded to
        :data:`_DERIVED_FIGURES` significant figures first, because its inputs
        were printed to no more than that.
    :return: The number as the site should print it.
    """
    if value == 0:
        return "0"
    if not exact:
        value = round(value, _DERIVED_FIGURES - 1 - math.floor(math.log10(abs(value))))
    if abs(value) < _SMALL:
        mantissa, _, exponent = f"{value:e}".partition("e")
        return f"{_plain(float(mantissa)).replace('.', ',')}e{int(exponent)}"
    whole, _, fraction = _plain(value).partition(".")
    grouped = f"{int(whole.lstrip('-')):,}".replace(",", _GROUP)
    if whole.startswith("-"):
        grouped = f"-{grouped}"
    return f"{grouped},{fraction}" if fraction else grouped


def cell(row: CatalogueRow, field: str) -> dict[str, Any]:
    """One cell, with the number and what the page said around it.

    :param row: The catalogue row.
    :param field: The quantity wanted.
    :return: ``text`` to print, ``kind`` for the component to style by, and
        ``note`` for the hedge a reader needs to read the number correctly.
    """
    value = getattr(row, field, None)
    if value is not None:
        derived = row.is_derived(field)
        kind = "derived" if derived else "printed"
        note = row.derived.get(field, "")
        if row.is_approximate(field):
            kind, note = "approximate", "the page prints it with a tilde"
        return {"text": number(value, exact=not derived), "kind": kind, "note": note}
    if field in row.ranges:
        low, high = row.ranges[field]
        bound = field in row.bounded_above
        return {
            "text": f"< {number(high)}"
            if bound
            else f"{number(low)} to {number(high)}",
            "kind": "bound" if bound else "range",
            "note": row.why_missing(field),
        }
    if field in row.reported:
        listed = ", ".join(
            f"{number(entry[0])} to {number(entry[1])}"
            if isinstance(entry, tuple)
            else number(entry)
            for entry in row.reported[field]
        )
        return {"text": listed, "kind": "reported", "note": row.why_missing(field)}
    if field in row.unquantified:
        return {
            "text": row.unquantified[field],
            "kind": "unquantified",
            "note": row.why_missing(field),
        }
    return {"text": "", "kind": "absent", "note": ""}


def rows(
    catalogue: Mapping[str, CatalogueRow],
    columns: tuple[tuple[str, str, str], ...],
) -> Iterator[dict[str, Any]]:
    """Every row of a catalogue, formatted.

    :param catalogue: The catalogue.
    :param columns: The columns to show, as ``(field, heading, unit)``.
    :return: One record per row, in the catalogue's own order.
    """
    for key, row in catalogue.items():
        table, _, _ = key.partition("/")
        yield {
            "key": key,
            "table": table,
            "name": row.name,
            "variant": row.variant,
            "source": row.source,
            "note": row.note,
            "attributedTo": dict(row.attributed_to),
            "cells": [cell(row, field) for field, _, _ in columns],
        }


#: The named air of this library that does not live in the fluids catalogue,
#: keyed the way the catalogue keys its own rows. Each sits beside the model or
#: the standard that fixes it, which is where it belongs: ``fluids`` is part of
#: the transverse toolbox, so a catalogue there that imported ``materials``,
#: ``building`` and ``simulation`` to gather them would make the medium depend
#: on three of the domains that stand on it. A script is free to import the
#: whole tree, so the comparison a reader wants is assembled here, where it
#: costs the library nothing.
IN_TREE_FLUIDS = {
    "iec-61094-2-annex-f/air": ANNEX_A_AIR,
    "en-12354-annex-a/air": EN_12354_AIR,
    "allard-2009-jca/air": PUBLISHED_AIR,
    "phonometry-solver/air": SIMULATION_AIR,
}


def fluids() -> list[dict[str, Any]]:
    """The fluid states, which are not rows of a table and do not format alike.

    A :class:`~phonometry.fluids.Fluid` carries a temperature, a pressure and
    whatever properties its model fixed, which differ from one state to the
    next: the metrology annex's air knows its thermal conductivity and the
    building standard's air knows a density and a speed and nothing else. So
    the columns are the union of what the states carry, and a state that does
    not determine a quantity leaves the cell empty rather than borrowing one.

    The states read from a page come first, then the four the tree carries
    elsewhere, which is the order that puts the airs of the four documents
    next to each other where their disagreement is visible.

    :return: One record per state.
    """
    quantities = ("speed_of_sound", "density", "viscosity", "heat_capacity_ratio")
    out: list[dict[str, Any]] = []
    for key, state in {**PUBLISHED_FLUIDS, **IN_TREE_FLUIDS}.items():
        out.append(
            {
                "key": key,
                "table": key.partition("/")[0],
                "name": key.rpartition("/")[2].replace("_", " "),
                "temperature": number(state.temperature_c),
                "pressure": number(state.static_pressure_pa),
                "model": state.model,
                "validity": state.validity,
                "cells": [
                    {
                        "text": number(state.properties[name])
                        if name in state.properties
                        else "",
                        "kind": "printed" if name in state.properties else "absent",
                        "note": "",
                    }
                    for name in quantities
                ],
            }
        )
    return out


def render() -> str:
    """The module the site imports.

    :return: Its whole text, ending in a newline.
    """
    import json

    document = {
        "solids": {
            "columns": [
                {"field": field, "heading": heading, "unit": unit}
                for field, heading, unit in SOLID_COLUMNS
            ],
            "rows": list(rows(PUBLISHED_SOLIDS, SOLID_COLUMNS)),
        },
        "porous": {
            "columns": [
                {"field": field, "heading": heading, "unit": unit}
                for field, heading, unit in POROUS_COLUMNS
            ],
            "rows": list(rows(PUBLISHED_POROUS, POROUS_COLUMNS)),
        },
        "fluids": {
            "columns": [
                {"field": "speed_of_sound", "heading": "Speed of sound", "unit": "m/s"},
                {"field": "density", "heading": "Density", "unit": "kg/m³"},
                {"field": "viscosity", "heading": "Viscosity", "unit": "Pa·s"},
                {
                    "field": "heat_capacity_ratio",
                    "heading": "Heat capacity ratio",
                    "unit": "",
                },
            ],
            "rows": fluids(),
        },
    }
    body = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=False)
    return (
        "// Auto-generated by scripts/generate_catalogue_data.py "
        "(make catalogue-data).\n"
        "// Do not edit by hand.\n"
        f"export const catalogues = {body};\n"
    )


def main(argv: list[str] | None = None) -> int:
    """Write the module, or check that the committed one is current.

    :param argv: Command line, for the tests.
    :return: The process exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero when the committed file differs from a fresh run",
    )
    args = parser.parse_args(argv)
    fresh = render()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if current != fresh:
            print(
                f"{OUTPUT.relative_to(OUTPUT.parents[3])} is stale; "
                "run `make catalogue-data`.",
                file=sys.stderr,
            )
            return 1
        print(f"{OUTPUT.name} is current.")
        return 0
    OUTPUT.write_text(fresh, encoding="utf-8")
    counts = {
        "solids": len(PUBLISHED_SOLIDS),
        "porous": len(PUBLISHED_POROUS),
        "fluids": len(PUBLISHED_FLUIDS) + len(IN_TREE_FLUIDS),
    }
    print(f"{OUTPUT.name}: " + ", ".join(f"{n} {k}" for k, n in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
