#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tables of the sound power standards that the noise-control ratings read too.

The A-weighting band corrections of ISO 3744:2010 Annex E and the mean sound
absorption coefficients of a room by description of ISO 11546-2:1995
Annex C. The sound power methods of :mod:`phonometry.emission` read them, and
so do the insulation ratings of enclosures and cabins in
:mod:`phonometry.noise_control`, which take a difference of two sound powers,
without importing another domain.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["ROOM_ABSORPTION_ESTIMATES"]

# --- ISO 3744:2010 Annex E, A-weighting band corrections Ck (dB) ------------
#: Table E.1 - one-third-octave mid-band frequencies.
_CK_THIRD: dict[int, float] = {
    50: -30.2,
    63: -26.2,
    80: -22.5,
    100: -19.1,
    125: -16.1,
    160: -13.4,
    200: -10.9,
    250: -8.6,
    315: -6.6,
    400: -4.8,
    500: -3.2,
    630: -1.9,
    800: -0.8,
    1000: 0.0,
    1250: 0.6,
    1600: 1.0,
    2000: 1.2,
    2500: 1.3,
    3150: 1.2,
    4000: 1.0,
    5000: 0.5,
    6300: -0.1,
    8000: -1.1,
    10000: -2.5,
}
#: Table E.2 - octave mid-band frequencies (subset of E.1 values).
_CK_OCTAVE: dict[int, float] = {
    63: -26.2,
    125: -16.1,
    250: -8.6,
    500: -3.2,
    1000: 0.0,
    2000: 1.2,
    4000: 1.0,
    8000: -1.1,
}


def _a_weighting_corrections(frequencies: np.ndarray) -> np.ndarray:
    """A-weighting band corrections Ck for the given nominal mid-band
    frequencies (ISO 3744:2010 Annex E, Tables E.1/E.2). The octave-band
    values (Table E.2) coincide with the one-third-octave values (Table E.1)
    at the shared mid-band frequencies, so a single lookup serves both.
    """
    nominal = [round(f) for f in frequencies]
    # Use the octave table (E.2) when every band is an octave mid-band centre,
    # otherwise the one-third-octave table (E.1); the two agree where they
    # overlap, so the result is identical either way.
    table = _CK_OCTAVE if set(nominal) <= set(_CK_OCTAVE) else _CK_THIRD
    ck = []
    for freq in nominal:
        if freq not in table:
            msg = (
                f"No ISO 3744 Annex E A-weighting value for {freq} Hz; "
                "expected a nominal octave or one-third-octave mid-band "
                "frequency (50 Hz to 10 kHz)."
            )
            raise ValueError(msg)
        ck.append(table[freq])
    return np.asarray(ck, dtype=np.float64)


#: Approximate mean sound absorption coefficient of a room by description, the
#: seven rows of ISO 11546-2:1995 Table C.2, Annex C, printed folio 13.
#: It answers the question that annex asks first: what is ``alpha`` in this
#: room, when nobody measured it. The keys are the coefficients themselves, so
#: a caller reads the value it needs and the description says what it stands
#: for.
#:
#: The 2010 editions of the sound power standards print a different table under
#: the same title, and it is not this one: ISO 3744:2010 Table A.1 (printed
#: folio 36) and ISO 3746:2010 Table A.1 (printed folio 24) have eight rows,
#: adding 0,30 for a room with an absorbing ceiling and bare walls, and they
#: reword two of the seven kept here, saying "right cuboid" where ISO 11546-2
#: says "rectangular" and "on part of ceiling or walls" where it says "with a
#: small amount of sound-absorbing material on ceiling or walls". ISO 11202:2010
#: prints no such table at all; its Annex A refers ``alpha`` out to ISO 3746.
ROOM_ABSORPTION_ESTIMATES: Mapping[float, str] = MappingProxyType(
    {
        0.05: (
            "Nearly empty room with smooth hard walls made of concrete, brick, "
            "plaster or tile"
        ),
        0.1: "Partly empty room; room with smooth walls",
        0.15: "Room with furniture; rectangular machinery room; rectangular industrial room",
        0.2: (
            "Irregularly shaped room with furniture; irregularly shaped machinery "
            "room or industrial room"
        ),
        0.25: (
            "Room with upholstered furniture; machinery or industrial room with a "
            "small amount of sound-absorbing material on ceiling or walls "
            "(e.g. partially absorptive ceiling)"
        ),
        0.35: "Room with sound-absorbing materials on both ceiling and walls",
        0.5: "Room with large amounts of sound-absorbing materials on ceiling and walls",
    }
)
