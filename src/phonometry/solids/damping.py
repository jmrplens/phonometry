#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Commercial damping materials, with the temperature and the frequency.

Every other loss factor this library holds is a figure with no conditions
attached. Bies prints 0.0001 for mild steel, Cremer a band of 0.00002 to
0.0003 for steel and Hopkins one of 0 to 0.0001, and not one of them says at
what temperature or at what frequency, because for a metal it hardly moves.
For the materials on this page it moves by two orders of magnitude, and
neither a number nor a band is a property of them at all.

A viscoelastic damping treatment is a polymer worked near its glass
transition. Below that transition it is stiff and stores the energy it is
given; above it, it is soft and stores almost none; and in the narrow band
between, it turns a large part of each cycle into heat. The loss factor peaks
in that band, and the band moves up in temperature as the frequency rises.
That is why :attr:`DampingMaterial.max_loss_factor` is useless on its own and
why this table prints three temperatures beside it: the temperature at which
the peak occurs when the material is worked at 10 Hz, at 100 Hz and at
1000 Hz. A material whose peak sits at 20 C at 100 Hz is doing nothing for you
at 100 Hz on a winter morning.

The four moduli follow the same argument. :attr:`youngs_modulus_max_pa` is the
stiff end, low temperature or high frequency; :attr:`youngs_modulus_min_pa` is
the soft end; :attr:`youngs_modulus_transition_pa` is the one that applies in
the band where the loss factor peaks, which is the only one of the three that
belongs beside :attr:`max_loss_factor`. The fourth,
:attr:`loss_modulus_max_pa`, is not a storage modulus at all: it is the
imaginary part, and the running text gives it as the product of the other two,
which is the cheapest check there is on a row of this table.

Where the rows live
-------------------
In ``solids/data/ver-beranek-2006-table-14-1.json``, read at import through the
package-data reader in ``phonometry._internal``, the same as every other
catalogue here.

What it is not
--------------
It is not a specification and it is not a measurement. The page says in a
footnote that the values were read off published curves, and the text around
it says to get damping data from the supplier of the material. Three of its
cells are corrupted in the printing; they are registered in ``docs/ERRATA.md``
and this catalogue refuses them rather than guessing what the digits were.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import TYPE_CHECKING

from .._internal.catalogue import CatalogueRow, read_table, rows_to_search, take

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "PUBLISHED_DAMPING",
    "DampingMaterial",
    "damping_named",
]

#: Hertz the peak temperature columns of the table are printed for.
_PEAK_FREQUENCIES_HZ = (10, 100, 1000)


@dataclass(frozen=True, kw_only=True)
class DampingMaterial(CatalogueRow):
    """One commercial damping material, as its published table prints it.

    The name, the citation and the hedges a cell can carry instead of a number
    are the ones every catalogue row has. What this class adds is that a loss
    factor here is never alone: it comes with the temperature at which it
    peaks, once per printed frequency.

    :ivar max_loss_factor: The greatest loss factor the material reaches,
        dimensionless. Not the loss factor at any temperature you happen to
        have: the peak, which the temperatures below locate.
    :ivar peak_temperature_at_10_hz_c: Temperature at which
        :attr:`max_loss_factor` occurs when the material is worked at 10 Hz.
    :ivar peak_temperature_at_100_hz_c: The same at 100 Hz.
    :ivar peak_temperature_at_1000_hz_c: The same at 1000 Hz.
    :ivar youngs_modulus_max_pa: Storage Young's modulus at the stiff end, for
        low temperatures or high frequencies.
    :ivar youngs_modulus_min_pa: Storage Young's modulus at the soft end, for
        high temperatures or low frequencies.
    :ivar youngs_modulus_transition_pa: Storage Young's modulus in the band
        where the loss factor peaks, which is the one that belongs beside
        :attr:`max_loss_factor`.
    :ivar loss_modulus_max_pa: The greatest value of the loss (imaginary)
        modulus. The chapter gives it as the product of the two above it, so a
        row where it is not about
        ``max_loss_factor * youngs_modulus_transition_pa`` is worth a second
        look at the page.
    """

    max_loss_factor: float | None = None
    peak_temperature_at_10_hz_c: float | None = None
    peak_temperature_at_100_hz_c: float | None = None
    peak_temperature_at_1000_hz_c: float | None = None
    youngs_modulus_max_pa: float | None = None
    youngs_modulus_min_pa: float | None = None
    youngs_modulus_transition_pa: float | None = None
    loss_modulus_max_pa: float | None = None

    def peak_temperature_c(self, frequency_hz: float) -> float:
        """The temperature at which the loss factor peaks, at one frequency.

        :param frequency_hz: One of the frequencies the table prints, in hertz.
        :return: The temperature in degrees Celsius.
        :raises ValueError: when the table prints no column for that frequency,
            or when it prints one and this row leaves it empty. An infinite or
            not-a-number frequency is refused the same way: converting it to an
            integer first raised ``OverflowError`` instead, which is not what
            this method documents and says nothing about the catalogue.
        """
        if not isfinite(frequency_hz) or frequency_hz not in _PEAK_FREQUENCIES_HZ:
            printed = ", ".join(f"{hz} Hz" for hz in _PEAK_FREQUENCIES_HZ)
            msg = (
                f"{self.name} has no peak temperature at {frequency_hz} Hz: the "
                f"table prints one at {printed} and nothing between them. The "
                "peak moves with frequency, so reading the nearest column as if "
                "it were this one is the mistake this method exists to prevent."
            )
            raise ValueError(msg)
        wanted = int(frequency_hz)
        return self.printed(
            f"peak_temperature_at_{wanted}_hz_c",
            wanted_by=f"the peak temperature at {wanted} Hz",
        )


def _rows() -> dict[str, DampingMaterial]:
    """Every damping material of every table this catalogue reads."""
    out: dict[str, DampingMaterial] = {}
    for filename in _TABLES:
        citation, rows = read_table("phonometry.solids", f"{filename}.json")
        for row in rows:
            key = f"{filename}/{row['key']}"
            out[key] = DampingMaterial.from_printed(
                source=citation, table=filename, **take(row)
            )
    return out


#: The tables this catalogue is read from, in the order they were added.
_TABLES = ("ver-beranek-2006-table-14-1",)

#: Commercial damping materials as their tables print them, keyed
#: ``"<table>/<material>"``. Read from
#: ``solids/data/ver-beranek-2006-table-14-1.json``: Vér & Beranek 2e
#: TABLE 14.1, PDF page 599 (printed p. 598).
PUBLISHED_DAMPING: MappingProxyType[str, DampingMaterial] = MappingProxyType(_rows())


def damping_named(
    name: str, *, catalogue: Mapping[str, DampingMaterial] | None = None
) -> tuple[DampingMaterial, ...]:
    """Every damping material whose name contains *name*, case-insensitively.

    A tuple and not one row, because a name can be printed by more than one
    table and this catalogue never chooses between books on the caller's
    behalf.

    :param name: Part of a material name, as its page prints it.
    :param catalogue: The rows to search in place of :data:`PUBLISHED_DAMPING`:
        a catalogue of your own that :func:`phonometry.io.read_catalogue`
        returns, ``PUBLISHED_DAMPING | mine`` to search both at once, or any
        mapping of key to row (Default: ``None``, which searches
        :data:`PUBLISHED_DAMPING`).
    :return: The matching rows, in catalogue order. Empty when none match.
    :raises TypeError: for a *catalogue* that is not a mapping, or that holds a
        row that is not a :class:`DampingMaterial`, naming its key.
    """
    needle = name.casefold()
    return tuple(
        row
        for row in rows_to_search(
            catalogue, PUBLISHED_DAMPING, DampingMaterial, "damping_named"
        )
        if needle in row.name.casefold()
    )
