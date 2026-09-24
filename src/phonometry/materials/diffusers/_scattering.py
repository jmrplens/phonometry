#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The band fields a scattering table prints, shared by two catalogues (private).

A scattering coefficient measured in a reverberation room and one computed by
a boundary element solver are the same quantity in the same bands, and they
are not interchangeable. This library keeps them in two catalogues with two
classes precisely so that a row cannot travel from one to the other unnoticed,
and neither class inherits from the other: a caller narrowing on the type has
to get a straight answer.

What they do share is the shape of a row, which is eighteen optional fields
and the bands they stand for. Declaring that twice is how the two classes
would drift apart, one gaining a band or a docstring the other never gets, so
it is declared here once and both inherit it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ..._internal.catalogue import BandedRow

__all__ = ["SCATTERING_BANDS_HZ", "ScatteringBands"]

#: The one-third octave centre frequencies a published scattering table can
#: print, in hertz. A table prints a subset; the field for a band it does not
#: print stays ``None`` on every row of it.
SCATTERING_BANDS_HZ: tuple[int, ...] = (
    100,
    125,
    160,
    200,
    250,
    315,
    400,
    500,
    630,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
    3150,
    4000,
    5000,
)


@dataclass(frozen=True, kw_only=True)
class ScatteringBands(BandedRow):
    """One row's worth of scattering coefficients, one field per band.

    Private: the two public classes that inherit this are what a caller
    handles, and which of them a row is says whether it was measured or
    computed.

    :ivar scattering_coefficient_100: Scattering coefficient in the 100 Hz
        one-third octave band, dimensionless, as printed. ``None`` where the
        table prints nothing there, which is not the same as zero: a zero is a
        surface that sends every ray back along the specular direction.
    :ivar scattering_coefficient_125: The same in the 125 Hz band.
    :ivar scattering_coefficient_160: The same in the 160 Hz band.
    :ivar scattering_coefficient_200: The same in the 200 Hz band.
    :ivar scattering_coefficient_250: The same in the 250 Hz band.
    :ivar scattering_coefficient_315: The same in the 315 Hz band.
    :ivar scattering_coefficient_400: The same in the 400 Hz band.
    :ivar scattering_coefficient_500: The same in the 500 Hz band.
    :ivar scattering_coefficient_630: The same in the 630 Hz band.
    :ivar scattering_coefficient_800: The same in the 800 Hz band.
    :ivar scattering_coefficient_1000: The same in the 1 kHz band.
    :ivar scattering_coefficient_1250: The same in the 1.25 kHz band.
    :ivar scattering_coefficient_1600: The same in the 1.6 kHz band.
    :ivar scattering_coefficient_2000: The same in the 2 kHz band.
    :ivar scattering_coefficient_2500: The same in the 2.5 kHz band.
    :ivar scattering_coefficient_3150: The same in the 3.15 kHz band.
    :ivar scattering_coefficient_4000: The same in the 4 kHz band.
    :ivar scattering_coefficient_5000: The same in the 5 kHz band.
    """

    scattering_coefficient_100: float | None = None
    scattering_coefficient_125: float | None = None
    scattering_coefficient_160: float | None = None
    scattering_coefficient_200: float | None = None
    scattering_coefficient_250: float | None = None
    scattering_coefficient_315: float | None = None
    scattering_coefficient_400: float | None = None
    scattering_coefficient_500: float | None = None
    scattering_coefficient_630: float | None = None
    scattering_coefficient_800: float | None = None
    scattering_coefficient_1000: float | None = None
    scattering_coefficient_1250: float | None = None
    scattering_coefficient_1600: float | None = None
    scattering_coefficient_2000: float | None = None
    scattering_coefficient_2500: float | None = None
    scattering_coefficient_3150: float | None = None
    scattering_coefficient_4000: float | None = None
    scattering_coefficient_5000: float | None = None

    _bands_hz: ClassVar[tuple[int, ...]] = SCATTERING_BANDS_HZ
    _band_prefix: ClassVar[str] = "scattering_coefficient_"
    _band_kind: ClassVar[str] = "a one-third octave"
    _bands_per_octave: ClassVar[int] = 3
    _table_kind: ClassVar[str] = "scattering"

    def scattering_coefficient(self, band_hz: int) -> float:
        """The coefficient in one band, or a refusal that says what the page had.

        :param band_hz: A one-third octave centre frequency from
            :data:`SCATTERING_BANDS_HZ`.
        :return: The scattering coefficient, dimensionless.
        :raises ValueError: when the table has no number in that band, naming
            the row, the band and what the cell held instead; or when
            *band_hz* is not a band these tables print.
        """
        return self._in_band(band_hz)
