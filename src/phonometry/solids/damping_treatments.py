#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Damping treatments rated by the decay rate of a treated panel.

:data:`~phonometry.solids.PUBLISHED_DAMPING` holds viscoelastic materials by
their loss factor, which is a property of the material. This module holds the
older way of rating a damping treatment, which is a property of the treatment
on a panel: glue it to a standard steel plate, strike the plate, and measure
how fast the vibration dies away, in decibels per second.

The standard panel
------------------
The chapter the rows come from fixes the test in its own text: every damping
capacity it quotes is a decay rate "en decibelios por segundo a 160 cps, para
un panel normalizado de ensayo de 50 x 50 x 0,6 cm", at room temperature unless
it says otherwise, on a thick plate whose bare decay rate is below 1 dB/s. The
table's heading gives its temperature, 21 °C. So a row here is comparable with
another row here and with nothing else: the same felt on a thinner panel, or at
another frequency, decays at another rate.

At 160 Hz a decay rate ``D`` corresponds to a loss factor of the treated panel
of ``D / (27.3 * 160)``, and the 400 dB/s of a notched ply under a metal sheet
is about 0.09. That is the composite loss factor of that panel with that
treatment on it, not a loss factor of the felt, and this module does not
compute it: the row holds the decay rate the page prints.

Where the rows live
-------------------
In ``solids/data/harris-1977-table-14-2.json``, read at import through the
package-data reader in ``phonometry._internal``, the same as every other
catalogue here.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

from .._internal.catalogue import (
    CatalogueRow,
    read_table,
    rows_to_search,
    search_text,
    take,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_DAMPING_TREATMENTS",
    "DampingTreatment",
    "damping_treatments_named",
]


@dataclass(frozen=True, kw_only=True)
class DampingTreatment(CatalogueRow):
    """One damping treatment, rated on the chapter's standard panel.

    :ivar decay_rate_db_s: The decay rate of the vibration of the treated
        standard panel, in decibels per second. Printed as a range on most
        rows, which :attr:`~phonometry.io.CatalogueRow.ranges`
        holds.
    :ivar temperature_c: The temperature of the measurement, in degrees
        Celsius, which the table prints once, in the decay rate's heading.
    :ivar adhered_area_percent: The percentage of the panel the treatment is
        bonded over. Two rows print the word "No" instead, for a treatment laid
        without adhesive, which
        :meth:`~phonometry.io.CatalogueRow.why_missing` hands
        back.
    :ivar surface_density_kg_m2: The weight of the treatment, in kg/m2.
    """

    decay_rate_db_s: float | None = None
    temperature_c: float | None = None
    adhered_area_percent: float | None = None
    surface_density_kg_m2: float | None = None


#: The published tables this catalogue reads.
_TABLES = ("harris-1977-table-14-2",)


def _load() -> dict[str, DampingTreatment]:
    """Every row of every packaged table, keyed by table and row."""
    out: dict[str, DampingTreatment] = {}
    for table in _TABLES:
        citation, rows = read_table("phonometry.solids", f"{table}.json")
        for row in rows:
            out[f"{table}/{row['key']}"] = DampingTreatment.from_printed(
                source=citation, table=table, **take(row)
            )
    return out


#: The damping treatments this library has read from a page, keyed
#: ``"<table>/<row>"``: Harris (1977) Table 14.2, PDF page 496 (printed
#: p. 483), eight asphalt felt treatments rated by the decay rate of the
#: chapter's standard panel.
PUBLISHED_DAMPING_TREATMENTS: Mapping[str, DampingTreatment] = MappingProxyType(_load())


def damping_treatments_named(
    name: str, *, catalogue: Mapping[str, DampingTreatment] | None = None
) -> tuple[DampingTreatment, ...]:
    """Every treatment whose printed description contains *name*.

    :param name: Part of the description as the page prints it, in Spanish,
        matched without regard to case: ``"muescado"`` answers with every
        notched felt.
    :param catalogue: The rows to search in place of
        :data:`PUBLISHED_DAMPING_TREATMENTS`: a catalogue of your own that
        :func:`phonometry.io.read_catalogue` returns,
        ``PUBLISHED_DAMPING_TREATMENTS | mine`` to search both at once, or any
        mapping of key to row (Default: ``None``, which searches
        :data:`PUBLISHED_DAMPING_TREATMENTS`).
    :return: The matching rows, in catalogue order. Empty when nothing
        matches, which is not an error.
    :raises TypeError: for a *catalogue* that is not a mapping, or that holds a
        row that is not a :class:`DampingTreatment`, naming its key.
    """
    wanted = search_text(name)
    return tuple(
        row
        for row in rows_to_search(
            catalogue,
            PUBLISHED_DAMPING_TREATMENTS,
            DampingTreatment,
            "damping_treatments_named",
        )
        if wanted in search_text(row.name)
    )
