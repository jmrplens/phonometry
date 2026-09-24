#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What a duct wall does to sound, out of it and into it.

A duct is not a pipe with a number on it. The sheet it is rolled from is a
partition like any other, and two different things happen across it: the sound
travelling inside the duct leaks out through the wall into the ceiling void, and
the sound already in that void leaks in and is carried away down the duct. The
chapter calls the first breakout and the second break-in, writes them TL_out and
TL_in, and tabulates them apart, because they are not the same number and the
duct is not symmetric about its own wall.

Why they are not one column
---------------------------
Breakout is a wall radiating into a room from a duct that is behaving as a
waveguide; break-in is a wall driven by a diffuse field and feeding a waveguide.
They are separate measurements on separate specimens, and the chapter's own
tables show it: the round ducts it measured for breakout are 200, 350, 560 and
810 mm at 4.6 m, and the ones it measured for break-in are 203, 356, 559 and
813 mm at 4.57 m, with spiral blocks that share not one diameter and not one
length, 300, 610 and 915 mm at 3.6, 7.3 and 3 m against 203, 356, 660 and
813 mm all at 3.05 m. There is no single construction to hang the two numbers
on, so this catalogue holds one row per printed row and each row says, in
:attr:`DuctWallSpectrum.direction`, which of the two it is. The rectangular and
flat oval tables do print the same seven sizes, row for row and each at the
same gauge as its twin, and they are still two rows each, because the page
nowhere says the specimen was the same one and a merged row would be this
library making that claim on the chapter's behalf.

What tells one row from another
-------------------------------
The cross section, the length and the gauge of the sheet. A rectangular or flat
oval duct prints two sides, held in :attr:`DuctWallSpectrum.first_side_mm` and
:attr:`DuctWallSpectrum.second_side_mm` in the order the page prints them, which
is not the same order in the two kinds of table; a round or circular one prints
:attr:`DuctWallSpectrum.diameter_mm`, and the two tables that print a length per
row put it in :attr:`DuctWallSpectrum.duct_length_m`. The gauge is a US
sheet-metal gauge number, and the chapter prints a thickness for one of the six
gauges these tables use, in passing and five folios past the last of them:
"16 ga (1.6 mm thickness)" in the running text on folio 49.37, against tables
that end on folio 49.32, with nothing anywhere for the
18, 20, 22, 24 and 26 the same tables print. So
:attr:`DuctWallSpectrum.sheet_metal_gauge` holds the characters the page prints
and nothing is converted from them.

What a cell can be instead of a number
--------------------------------------
Two things, and a third that is a number with a mark beside it. A cell written
``>45`` is a lower bound, because the background sound swamped what the duct
wall was radiating; it is held as a range whose printed end is the number the
page gives and whose other end is left empty, because a transmission loss has
no ceiling and a number put there to stand for one would be read as a
measurement. It is flagged ``bounded_below``, so a caller who asks for the band
is refused rather than handed the bound. A cell printed as a rule has no legend
anywhere in the chapter, so it is held as ``unquantified`` with the glyph the
page prints and no reading of it is supplied.

A cell in parentheses is the third, and it is not a hedge at all: the number is
a measurement and it is held exactly as printed. What the parentheses add is
what the note under Table 32 says they add, "measurements in which background
sound produced greater uncertainty than usual", and no hedge of this library
means that. It is not ``approximate``, which is a number an author rounded on
purpose and which the published table reads back as a printed tilde, so the
mark is recorded in the row's note instead and the value is left alone.

Where the rows live
-------------------
In ``noise_control/data/ashrae-2019-tables-29-to-34.json``, read at import
through the package-data reader in ``phonometry._internal``, the same as every
other catalogue here.

What it is not
--------------
It is not a specification. Only two of the six tables say in their titles how
they were obtained, "Experimentally Measured", and they are the two that carry
the bounds and the parenthesised values the background sound left; the other
four say nothing at all about measurement or calculation and carry no source
line either. The credit for all six is in the running text and travels with
each row in ``attributed_to``. Machine-room walls are not here: the chapter's
Table 40 is an ordinary partition, the same quantity
:data:`phonometry.building.PUBLISHED_TRANSMISSION_LOSS` holds from Bies, and it
is published from there.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, ClassVar

from .._internal.catalogue import BandedRow, read_table, take

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = [
    "DUCT_WALL_BANDS_HZ",
    "PUBLISHED_DUCT_TRANSMISSION_LOSS",
    "DuctWallSpectrum",
    "duct_wall_named",
]

#: The octave-band centre frequencies a duct-wall table can print, in hertz.
#: The rectangular tables print all eight; the round, circular and flat oval
#: ones stop at 4 kHz and leave the last field empty on every row.
DUCT_WALL_BANDS_HZ: tuple[int, ...] = (63, 125, 250, 500, 1000, 2000, 4000, 8000)

#: What the two directions are called, in the chapter's own words.
_BREAKOUT = "breakout"
_BREAK_IN = "break-in"


@dataclass(frozen=True, kw_only=True)
class DuctWallSpectrum(BandedRow):
    """One duct wall of one printed table, in one of the two directions.

    The hedges a cell can carry instead of a number are the ones every
    catalogue row has. What this class adds is that the quantity is only half
    named by the column: a transmission loss here is a breakout or a break-in
    transmission loss, never both, and :attr:`direction` is what says which.

    :ivar transmission_loss_63_db: The transmission loss in the 63 Hz octave
        band, in decibels, in the direction :attr:`direction` names.
    :ivar transmission_loss_125_db: The same in the 125 Hz band.
    :ivar transmission_loss_250_db: The same in the 250 Hz band.
    :ivar transmission_loss_500_db: The same in the 500 Hz band.
    :ivar transmission_loss_1000_db: The same in the 1 kHz band.
    :ivar transmission_loss_2000_db: The same in the 2 kHz band.
    :ivar transmission_loss_4000_db: The same in the 4 kHz band.
    :ivar transmission_loss_8000_db: The same in the 8 kHz band, which only the
        two rectangular tables print a column for.
    :ivar direction: ``"breakout"`` for the sound that leaves the duct through
        its wall, ``"break-in"`` for the sound that enters it through the same
        wall. Two rows of the same size and gauge in the two directions are two
        measurements and not two columns of one.
    :ivar shape: What the table's own title calls the duct:
        ``"rectangular"``, ``"round"``, ``"flat oval"`` or ``"circular"``. The
        chapter uses "round" for its breakout table and "circular" for its
        break-in one although the geometry is the same, and each row keeps the
        word its own page prints.
    :ivar printed_table: Which table of the chapter this row is printed in,
        ``"Table 29"`` to ``"Table 34"``.
    :ivar sheet_metal_gauge: The gauge of the sheet, exactly as printed,
        including the asterisk that marks an internally lined duct. It is a US
        sheet-metal gauge number, and the chapter converts one of the six
        these tables use, "16 ga (1.6 mm thickness)" in the running text of
        folio 49.37, and none of the other five, so no thickness is offered
        here.
    :ivar first_side_mm: The first of the two sides a rectangular or flat oval
        duct prints, in millimetres. The page does not say which side is the
        width, and it does not print them in one order: the rectangular tables
        put the smaller first and the flat oval tables the larger.
    :ivar second_side_mm: The second of those two sides, in millimetres.
    :ivar diameter_mm: The diameter of a round or circular duct, in
        millimetres. In one block of one table a printed diameter covers three
        consecutive rows, and the two whose cell the page leaves blank carry it
        down from the row that prints it: ``carried["diameter_mm"]`` names
        that row, and ``is_derived("diameter_mm")`` answers ``False``, because
        the number is the page's and this library computed nothing.
    :ivar duct_length_m: The length of the duct that was measured, in metres,
        for the two tables that print one per row. The four tables that do not
        say in a note that their data are for a length of 6.1 m, which is how
        the page writes it.
    """

    transmission_loss_63_db: float | None = None
    transmission_loss_125_db: float | None = None
    transmission_loss_250_db: float | None = None
    transmission_loss_500_db: float | None = None
    transmission_loss_1000_db: float | None = None
    transmission_loss_2000_db: float | None = None
    transmission_loss_4000_db: float | None = None
    transmission_loss_8000_db: float | None = None
    direction: str = ""
    shape: str = ""
    printed_table: str = ""
    sheet_metal_gauge: str = ""
    first_side_mm: float | None = None
    second_side_mm: float | None = None
    diameter_mm: float | None = None
    duct_length_m: float | None = None

    _bands_hz: ClassVar[tuple[int, ...]] = DUCT_WALL_BANDS_HZ
    _band_prefix: ClassVar[str] = "transmission_loss_"
    _band_suffix: ClassVar[str] = "_db"
    _band_kind: ClassVar[str] = "an octave"
    _table_kind: ClassVar[str] = "duct wall"

    @property
    def is_breakout(self) -> bool:
        """Whether this row is the sound leaving the duct through its wall."""
        return self.direction == _BREAKOUT

    @property
    def is_break_in(self) -> bool:
        """Whether this row is the sound entering the duct through its wall."""
        return self.direction == _BREAK_IN

    def transmission_loss_db(self, band_hz: int) -> float:
        """The loss in one band, or a refusal that says what the page had.

        Which of the two transmission losses it is follows from
        :attr:`direction`, and the two are never mixed in one row.

        :param band_hz: An octave-band centre frequency between 63 Hz and
            8 kHz; :meth:`~phonometry.io.BandedRow.bands` says
            which ones this row fills.
        :return: The printed transmission loss, in decibels.
        :raises ValueError: when the page has no number in that band, naming
            the row, the band and what the cell held instead, which for these
            tables is a lower bound, a rule the chapter never explains, or a
            column the table does not print at all; or when *band_hz* is not a
            band these tables print.
        """
        return self._in_band(band_hz)


#: The published tables this catalogue reads. One file holds the six printed
#: tables, because they are one reading of one stretch of one chapter and each
#: row says which table it is printed in.
_TABLES = ("ashrae-2019-tables-29-to-34",)


def _load() -> dict[str, DuctWallSpectrum]:
    """Every row of every packaged table, keyed ``"<table>/<row>"``."""
    rows: dict[str, DuctWallSpectrum] = {}
    for table in _TABLES:
        source, records = read_table("phonometry.noise_control", f"{table}.json")
        for record in records:
            key = f"{table}/{record['key']}"
            rows[key] = DuctWallSpectrum.from_printed(
                table=table, source=source, **take(record)
            )
    return rows


#: The forty-six duct walls the chapter tabulates, keyed ``"<table>/<row>"``
#: and in the order the pages print them. Read from
#: ``noise_control/data/ashrae-2019-tables-29-to-34.json``: ASHRAE (2019)
#: HVAC Applications Handbook Chapter 49 Tables 29 to 34, the breakout of a
#: rectangular, round and flat oval duct wall and the break-in of the same
#: three. Each row is one direction, and the key carries the printed table, the
#: size and the gauge, because a size can be printed in two tables and a
#: diameter twice in one.
PUBLISHED_DUCT_TRANSMISSION_LOSS: Mapping[str, DuctWallSpectrum] = MappingProxyType(
    _load()
)


def duct_wall_named(name: str) -> tuple[DuctWallSpectrum, ...]:
    """Every duct wall whose printed label contains *name*, without case.

    A tuple and not one row, and a long one: the label a duct table prints is
    its size, and the same size is printed by the breakout table and by the
    break-in table, so the plain answer to ``"305 × 305 mm"`` is two rows that
    are two different quantities. Read :attr:`DuctWallSpectrum.direction` to
    tell them apart, and :attr:`DuctWallSpectrum.sheet_metal_gauge` to tell
    apart two rows of one diameter.

    :param name: Part of a row label, as its page prints it, with the unit its
        column heading carries: ``"610"``, ``"305 × 1220"``, ``"152 mm"``.
    :return: The matching rows, in catalogue order. Empty when none match.
    """
    needle = name.casefold()
    return tuple(
        row
        for row in PUBLISHED_DUCT_TRANSMISSION_LOSS.values()
        if needle in row.name.casefold()
    )
