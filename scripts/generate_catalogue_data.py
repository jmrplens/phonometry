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
import functools
import math
import pathlib
import statistics
import sys
from typing import TYPE_CHECKING, Any, NamedTuple

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from phonometry.building.prediction.detailed_model import EN_12354_AIR  # noqa: E402
from phonometry.environment.propagation import PUBLISHED_GROUND  # noqa: E402
from phonometry.fluids import PUBLISHED_FLUIDS  # noqa: E402
from phonometry.materials.absorbers import PUBLISHED_POROUS  # noqa: E402
from phonometry.materials.absorbers.airflow_resistance import ANNEX_A_AIR  # noqa: E402
from phonometry.materials.absorbers.porous import PUBLISHED_AIR  # noqa: E402
from phonometry.simulation.ntff import SIMULATION_AIR  # noqa: E402
from phonometry.solids import PUBLISHED_SOLIDS  # noqa: E402

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping

    from phonometry._internal.catalogue import CatalogueRow

#: Where the site imports the catalogues from.
OUTPUT = (
    pathlib.Path(__file__).resolve().parents[1] / "site/src/generated/catalogues.mjs"
)

#: The columns each catalogue shows, as ``(field, heading, heading in Spanish,
#: unit)``. A unit of the empty string is a dimensionless quantity, which is
#: not the same as a quantity whose unit the heading already carries. The
#: headings travel in both languages because the site publishes the page in
#: both and a column called "Young's modulus" over a Spanish table is the one
#: string a reader cannot look up; the material names do not, because they are
#: what the book printed.
SOLID_COLUMNS = (
    ("density_kg_m3", "Density", "Densidad", "kg/m³"),
    ("youngs_modulus_pa", "Young's modulus", "Módulo de Young", "Pa"),
    ("shear_modulus_pa", "Shear modulus", "Módulo de cizalla", "Pa"),
    ("poisson_ratio", "Poisson ratio", "Coeficiente de Poisson", ""),
    ("longitudinal_speed_m_s", "Longitudinal speed", "Velocidad longitudinal", "m/s"),
    ("bar_longitudinal_speed_m_s", "Bar speed", "Velocidad de barra", "m/s"),
    ("plate_longitudinal_speed_m_s", "Plate speed", "Velocidad de placa", "m/s"),
    ("bulk_longitudinal_speed_m_s", "Bulk speed", "Velocidad de medio infinito", "m/s"),
    ("transverse_speed_m_s", "Transverse speed", "Velocidad transversal", "m/s"),
    ("loss_factor", "Loss factor", "Factor de pérdidas", ""),
    (
        "flexural_loss_factor",
        "Flexural loss factor",
        "Factor de pérdidas a flexión",
        "",
    ),
    (
        "longitudinal_loss_factor",
        "Longitudinal loss factor",
        "Factor de pérdidas longitudinal",
        "",
    ),
    ("in_situ_loss_factor", "In-situ loss factor", "Factor de pérdidas in situ", ""),
    (
        "thickness_critical_frequency_product_m_hz",
        "Thickness × critical frequency",
        "Espesor × frecuencia crítica",
        "m·Hz",
    ),
)

POROUS_COLUMNS = (
    (
        "flow_resistivity_pa_s_m2",
        "Flow resistivity",
        "Resistividad al flujo",
        "Pa·s/m²",
    ),
    ("porosity", "Porosity", "Porosidad", ""),
    ("tortuosity", "Tortuosity", "Tortuosidad", ""),
    ("viscous_length_um", "Viscous length", "Longitud viscosa", "µm"),
    ("thermal_length_um", "Thermal length", "Longitud térmica", "µm"),
    ("thermal_permeability_m2", "Thermal permeability", "Permeabilidad térmica", "m²"),
    ("fibre_diameter_um", "Fibre diameter", "Diámetro de fibra", "µm"),
    (
        "fibre_diameter_distribution_parameter",
        "Diameter distribution",
        "Distribución de diámetros",
        "",
    ),
    ("shot_content_percent", "Shot content", "Contenido de perdigón", "%"),
    ("binder_content_percent", "Binder content", "Contenido de ligante", "%"),
    ("frame_density_kg_m3", "Frame density", "Densidad del esqueleto", "kg/m³"),
    ("thickness_mm", "Thickness", "Espesor", "mm"),
    ("youngs_modulus_pa", "Young's modulus", "Módulo de Young", "Pa"),
    ("shear_modulus_pa", "Shear modulus", "Módulo de cizalla", "Pa"),
    ("poisson_ratio", "Poisson ratio", "Coeficiente de Poisson", ""),
    (
        "structural_loss_factor",
        "Structural loss factor",
        "Factor de pérdidas estructural",
        "",
    ),
)

GROUND_COLUMNS = (
    (
        "flow_resistivity_pa_s_m2",
        "Effective flow resistivity",
        "Resistividad al flujo efectiva",
        "Pa·s/m²",
    ),
    ("porosity", "Porosity", "Porosidad", ""),
    ("water_content_percent", "Water content", "Contenido de agua", "%"),
    (
        "porosity_decay_rate_per_m",
        "Porosity decay",
        "Decaimiento de porosidad",
        "1/m",
    ),
    (
        "iso_9613_ground_factor",
        "ISO 9613-2 ground factor",
        "Factor de suelo ISO 9613-2",
        "",
    ),
    (
        "nmpb_ground_factor",
        "NMPB-2008 ground factor",
        "Factor de suelo NMPB-2008",
        "",
    ),
)

#: Significant figures a **derived** number is rounded to before it is shown.
#: Its inputs were printed to four at most, so a plate speed worked out of a
#: modulus and a density is not known to fifteen and must not be shown to
#: fifteen. A value the page itself printed is shown as stored, whatever its
#: length: the 345,866 52 m/s of the metrology annex is what that annex
#: prints, and rounding it here would erase what distinguishes it.
_DERIVED_FIGURES = 4

#: Where a column stops reading as digits. A modulus of 471 700 000 000 Pa is
#: twelve digits of a number nobody says out loud, and a permeability of
#: 0,0000000033 m2 is eight leading zeros. A column like that is rewritten:
#: first by moving the prefix into the heading, so the moduli are a column of
#: GPa, and where the unit takes no prefix, by a mantissa and a power of ten.
#: The test is made once per column and not per cell, because a column is what
#: a reader compares down.
#:
#: It is made on the median and not on the extremes, because one outlier must
#: not set the form of a whole column: the loss factors of the solids run from
#: 0,000003 to 0,3 around a median of 0,005, and writing that column in powers
#: of ten to spare its smallest cell would turn every ordinary 0,005 in it
#: into 5 x 10^-3.
_BIG = 1e7
_TINY = 1e-4

#: The prefixes a heading may take, as (exponent, symbol), largest first.
_PREFIXES = (
    (9, "G"),
    (6, "M"),
    (3, "k"),
    (0, ""),
    (-3, "m"),
    (-6, "µ"),
    (-9, "n"),
)

#: The units a prefix may be moved into. A unit that already carries one
#: (``kg/m3``), a squared one (``m2``, where a prefix would square with it) and
#: a compound of two quantities (``m.Hz``) are left alone, and a column in one
#: of those that still does not read as digits falls back on a power of ten.
_PREFIXABLE = frozenset({"Pa", "Pa·s", "Pa·s/m²"})

#: The superscript digits a power of ten is written with, so the exponent sets
#: as an exponent in a table cell, in the markdown twin of the page and in the
#: text a reader copies out of either.
_SUPERSCRIPT = str.maketrans(
    "-0123456789", "\u207b\u2070\u00b9\u00b2\u00b3\u2074\u2075\u2076\u2077\u2078\u2079"
)

#: The narrow no-break space this corpus groups thousands with, which is what
#: keeps a group from breaking across a line.
_GROUP = "\u202f"


def _plain(value: float, exponent: int = 0) -> str:
    """*value* as a decimal string: no exponent, no digit it does not carry.

    ``repr`` gives the shortest string that round-trips, which is the digits
    the number actually has, and :class:`~decimal.Decimal` turns that into
    positional notation without inventing any. ``format(value, "g")`` cannot
    be used: it drops into exponent form at 1e5, which is where the densities
    and the moduli of these tables live.

    The scaling is a decimal shift and not a division, because dividing
    143 000 000 by a thousand in binary floating point gives
    143 000,000 000 000 01 and the page would print it.

    :param value: The number.
    :param exponent: Powers of ten to take out of it, which is how a column
        moves its prefix into the heading: 3 writes 4 400 Pa as 4,4 in a
        column of kPa.
    :return: Its positional form, trailing zeros trimmed.
    """
    text = format(decimal.Decimal(repr(value)).scaleb(-exponent), "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def number(
    value: float,
    *,
    exact: bool = True,
    exponent: int = 0,
    scientific: bool = False,
) -> str:
    """One number, written the way this corpus writes numbers.

    The decimal separator is the comma, as in every figure and every table of
    this documentation, and the thousands are separated by the narrow no-break
    space.

    :param value: The number.
    :param exact: Whether a page printed it, in which case every digit it
        carries is shown. A number this library derived is rounded to
        :data:`_DERIVED_FIGURES` significant figures first, because its inputs
        were printed to no more than that.
    :param exponent: Powers of ten this column moved into its heading, as a
        prefix: 3 writes 4 400 Pa as 4,4 under a heading of kPa.
    :param scientific: Whether this number's column is written as a mantissa
        and a power of ten, which is what a unit that takes no prefix falls
        back on. Decided once for the column by :func:`column_style`.
    :return: The number as the site should print it.
    """
    if value == 0:
        return "0"
    if not exact:
        value = round(value, _DERIVED_FIGURES - 1 - math.floor(math.log10(abs(value))))
    if scientific:
        mantissa, _, power = f"{value:e}".partition("e")
        written = str(int(power)).translate(_SUPERSCRIPT)
        return f"{_plain(float(mantissa)).replace('.', ',')} \u00d7 10{written}"
    whole, _, fraction = _plain(value, exponent).partition(".")
    grouped = f"{int(whole.lstrip('-')):,}".replace(",", _GROUP)
    if whole.startswith("-"):
        grouped = f"-{grouped}"
    return f"{grouped},{fraction}" if fraction else grouped


def values(catalogue: Mapping[str, CatalogueRow], field: str) -> Iterator[float]:
    """Every number a column holds, wherever in the row it is kept.

    :param catalogue: The catalogue.
    :param field: The quantity wanted.
    :return: The printed value, both ends of a range, and every reading of a
        cell that lists several.
    """
    for row in catalogue.values():
        value = getattr(row, field, None)
        if value is not None:
            yield value
        interval = row.ranges.get(field)
        if interval is not None:
            yield from interval
        for entry in row.reported.get(field, ()):
            yield from entry if isinstance(entry, tuple) else (entry,)


def in_powers_of_ten(numbers: Iterable[float]) -> bool:
    """Whether a column of *numbers* is written as mantissa and power of ten.

    One decision for the whole column, so that a reader comparing down it
    compares like with like.

    :param numbers: Every number the column holds.
    :return: True when the middle of the column is at :data:`_BIG` or beyond,
        or below :data:`_TINY`, which is where digits stop being readable.
    """
    magnitudes = [abs(value) for value in numbers if value != 0]
    if not magnitudes:
        return False
    middle = statistics.median(magnitudes)
    return middle >= _BIG or middle < _TINY


def by_powers(catalogue: Mapping[str, CatalogueRow], field: str) -> bool:
    """Whether one catalogue column is written in powers of ten.

    :param catalogue: The catalogue.
    :param field: The quantity wanted.
    :return: What :func:`in_powers_of_ten` says about that column.
    """
    return in_powers_of_ten(values(catalogue, field))


class Style(NamedTuple):
    """How one column is written: its heading's unit and its cells' form.

    :ivar unit: The unit the heading carries, prefix included.
    :ivar exponent: Powers of ten taken out of every cell to match it.
    :ivar scientific: Whether the cells are a mantissa and a power of ten,
        which is where a unit that takes no prefix ends up.
    """

    unit: str
    exponent: int = 0
    scientific: bool = False


def column_style(unit: str, numbers: Iterable[float]) -> Style:
    """How to write a column of *numbers* whose quantity is in *unit*.

    A prefix in the heading beats a power of ten in every cell: a column of
    GPa reads as 62,11 and 23,17, where the same column in pascals reads as
    6,211 x 10^10 and 2,317 x 10^10, and a reader comparing two materials is
    comparing mantissas and exponents instead of numbers. So a unit that takes
    a prefix gets one, and only a unit that cannot (a squared metre, a unit
    that already carries a prefix, two quantities multiplied together) falls
    back on the power of ten.

    Which prefix is chosen by writing the whole column out under each one and
    keeping the shortest, which is what a reader means by the one that reads
    best: it is the prefix that leaves the fewest digits on the page, and it
    ties towards no prefix at all.

    :param unit: The unit of the quantity, as the heading has it.
    :param numbers: Every number the column holds.
    :return: The style that column is written in.
    """
    magnitudes = [value for value in numbers if value]
    if not magnitudes:
        return Style(unit)
    if unit not in _PREFIXABLE:
        return Style(unit, scientific=in_powers_of_ten(magnitudes))
    written = {
        exponent: sum(len(number(value, exponent=exponent)) for value in magnitudes)
        for exponent, _ in _PREFIXES
    }
    exponent = min(written, key=lambda power: (written[power], abs(power)))
    prefix = dict(_PREFIXES)[exponent]
    return Style(f"{prefix}{unit}", exponent)


def cell(
    row: CatalogueRow, field: str, *, style: Style | None = None
) -> dict[str, Any]:
    """One cell, with the number and what the page said around it.

    :param row: The catalogue row.
    :param field: The quantity wanted.
    :param style: How the column is written, from :func:`column_style`. The
        default writes plain digits in the unit the quantity is stored in.
    :return: ``text`` to print, ``kind`` for the component to style by, and
        ``note`` for the hedge a reader needs to read the number correctly.
    """
    style = style or Style("")
    written = functools.partial(
        number, exponent=style.exponent, scientific=style.scientific
    )
    value = getattr(row, field, None)
    if value is not None:
        derived = row.is_derived(field)
        kind = "derived" if derived else "printed"
        note = row.derived.get(field, "")
        if row.is_approximate(field):
            kind, note = "approximate", "the page prints it with a tilde"
        return {"text": written(value, exact=not derived), "kind": kind, "note": note}
    if field in row.ranges:
        low, high = row.ranges[field]
        bound = field in row.bounded_above
        return {
            "text": f"< {written(high)}"
            if bound
            else f"{written(low)} to {written(high)}",
            "kind": "bound" if bound else "range",
            "note": row.why_missing(field),
        }
    if field in row.reported:
        listed = ", ".join(
            f"{written(entry[0])} to {written(entry[1])}"
            if isinstance(entry, tuple)
            else written(entry)
            for entry in row.reported[field]
        )
        return {"text": listed, "kind": "reported", "note": row.why_missing(field)}
    if field in row.unquantified:
        return {
            "text": row.unquantified[field],
            "kind": "unquantified",
            "note": row.why_missing(field),
        }
    # A cell this library will not fill although the arithmetic would reach it
    # reads as empty, because the page is empty there; why it stays empty is
    # what the note says.
    if field in row.not_derivable:
        return {"text": "", "kind": "absent", "note": row.why_missing(field)}
    return {"text": "", "kind": "absent", "note": ""}


def styles(
    catalogue: Mapping[str, CatalogueRow],
    columns: tuple[tuple[str, str, str, str], ...],
) -> dict[str, Style]:
    """How each column of *catalogue* is written.

    :param catalogue: The catalogue.
    :param columns: The columns to show, as ``(field, heading, heading in
        Spanish, unit)``.
    :return: The style of each column, by field name.
    """
    return {
        field: column_style(unit, values(catalogue, field))
        for field, _, _, unit in columns
    }


def rows(
    catalogue: Mapping[str, CatalogueRow],
    columns: tuple[tuple[str, str, str, str], ...],
) -> Iterator[dict[str, Any]]:
    """Every row of a catalogue, formatted.

    :param catalogue: The catalogue.
    :param columns: The columns to show, as ``(field, heading, heading in
        Spanish, unit)``.
    :return: One record per row, in the catalogue's own order.
    """
    written = styles(catalogue, columns)
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
            "cells": [
                cell(row, field, style=written[field]) for field, _, _, _ in columns
            ],
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


def fluids() -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
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

    :return: The columns, headings and units included, and one record per
        state.
    """
    quantities = (
        ("speed_of_sound", "Speed of sound", "Velocidad del sonido", "m/s"),
        ("density", "Density", "Densidad", "kg/m³"),
        ("viscosity", "Viscosity", "Viscosidad", "Pa·s"),
        (
            "heat_capacity_ratio",
            "Heat capacity ratio",
            "Relación de calores específicos",
            "",
        ),
    )
    states = {**PUBLISHED_FLUIDS, **IN_TREE_FLUIDS}
    # The same decision the material columns take, made the same way: a
    # viscosity of 0,0000184 Pa s is a column of leading zeros, and moving the
    # prefix into the heading makes it 18,4 µPa·s.
    written = {
        name: column_style(
            unit,
            [
                state.properties[name]
                for state in states.values()
                if name in state.properties
            ],
        )
        for name, _, _, unit in quantities
    }
    columns = [
        {
            "field": name,
            "heading": heading,
            "headingEs": spanish,
            "unit": written[name].unit,
        }
        for name, heading, spanish, _ in quantities
    ]
    out: list[dict[str, Any]] = []
    for key, state in states.items():
        # A state read from a table and a state a model fixes are different
        # kinds of number, and the cell says which: 343 m/s is what Bies
        # printed, where the 345,86652 m/s of the metrology annex is what its
        # closed form returns at the conditions that annex assumes.
        kind = "printed" if key in PUBLISHED_FLUIDS else "fixed"
        out.append(
            {
                "key": key,
                "table": key.partition("/")[0],
                "name": key.rpartition("/")[2].replace("_", " ").capitalize(),
                "temperature": number(state.temperature_c),
                "pressure": number(state.static_pressure_pa),
                "model": state.model,
                "validity": state.validity,
                "cells": [
                    {
                        "text": number(
                            state.properties[name],
                            exponent=written[name].exponent,
                            scientific=written[name].scientific,
                        )
                        if name in state.properties
                        else "",
                        "kind": kind if name in state.properties else "absent",
                        "note": "",
                    }
                    for name, _, _, _ in quantities
                ],
            }
        )
    return columns, out


def render() -> str:
    """The module the site imports.

    :return: Its whole text, ending in a newline.
    """
    import json

    solid_styles = styles(PUBLISHED_SOLIDS, SOLID_COLUMNS)
    porous_styles = styles(PUBLISHED_POROUS, POROUS_COLUMNS)
    ground_styles = styles(PUBLISHED_GROUND, GROUND_COLUMNS)
    fluid_columns, fluid_rows = fluids()
    document = {
        "solids": {
            "columns": [
                {
                    "field": field,
                    "heading": heading,
                    "headingEs": spanish,
                    "unit": solid_styles[field].unit,
                }
                for field, heading, spanish, _ in SOLID_COLUMNS
            ],
            "rows": list(rows(PUBLISHED_SOLIDS, SOLID_COLUMNS)),
        },
        "porous": {
            "columns": [
                {
                    "field": field,
                    "heading": heading,
                    "headingEs": spanish,
                    "unit": porous_styles[field].unit,
                }
                for field, heading, spanish, _ in POROUS_COLUMNS
            ],
            "rows": list(rows(PUBLISHED_POROUS, POROUS_COLUMNS)),
        },
        "ground": {
            "columns": [
                {
                    "field": field,
                    "heading": heading,
                    "headingEs": spanish,
                    "unit": ground_styles[field].unit,
                }
                for field, heading, spanish, _ in GROUND_COLUMNS
            ],
            "rows": list(rows(PUBLISHED_GROUND, GROUND_COLUMNS)),
        },
        "fluids": {"columns": fluid_columns, "rows": fluid_rows},
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
        "ground": len(PUBLISHED_GROUND),
        "porous": len(PUBLISHED_POROUS),
        "fluids": len(PUBLISHED_FLUIDS) + len(IN_TREE_FLUIDS),
    }
    print(f"{OUTPUT.name}: " + ", ".join(f"{n} {k}" for k, n in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
