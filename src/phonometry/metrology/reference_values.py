#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Preferred reference values for acoustical and vibratory levels (ISO 1683:2015).

A level in decibels is a ratio to a reference value, so the number means
nothing until the reference is known: the same pressure reads 26 dB higher
against the 1 µPa of water than against the 20 µPa of air, and the same
vibration 34 dB higher against 1 nm/s than against 50 nm/s. ISO 1683:2015
fixes one reference per quantity in three tables, and the level functions of
this library count their decibels from them unless the standard they
implement names another:

- **Table 1**, sounds in air and other gases: sound pressure 20 µPa, sound
  exposure (20 µPa)² s, sound power 1 pW, sound energy 1 pJ and sound
  intensity 1 pW/m².
- **Table 2**, sounds in water and other liquids: sound pressure 1 µPa, sound
  exposure 1 µPa² s, sound power 1 pW, sound energy 1 pJ, sound intensity
  1 pW/m², sound particle displacement 1 pm, velocity 1 nm/s and acceleration
  1 µm/s², and a distance of 1 m for the compound quantities of its note c
  (a source level re 1 µPa m, for one).
- **Table 3**, vibratory quantities: displacement 1 pm, velocity 1 nm/s,
  acceleration 1 µm/s² and force 1 µN. Its note b adds the 50 nm/s that is
  also used for structure-borne sound, against which the velocity level comes
  out close to the associated sound pressure and intensity levels.

:data:`ISO1683_REFERENCE_VALUES` holds all of them, keyed by medium and then
by quantity, and every value is in the coherent SI unit its row names, so the
20 µPa of air is ``2e-05`` Pa::

    from phonometry import metrology

    p0 = metrology.ISO1683_REFERENCE_VALUES["gas"]["sound_pressure"]
    p0.value, p0.unit, p0.printed  # (2e-05, 'Pa', '20 µPa')

Note b of Table 2 gives the offset between the two pressure references, a
level re 1 µPa being :math:`10 \lg(20^2/1^2) \approx 26.0` dB above the same
pressure re 20 µPa; :func:`phonometry.underwater.in_air_to_underwater_spl`
applies it.

The values were transcribed from the Spanish text UNE-EN ISO 1683:2016, which
adopts ISO 1683:2015 unchanged, PDF pages 8 and 9 (printed folios 8 and 9),
and the quantity names are given here in English. A module that counts its
decibels from a different reference keeps it, and names the document it comes
from beside it: the railway vibration of DIN 45672-2 is referred to the
5·10⁻⁸ m/s of DIN EN 21683 (ISO 1683:1983), and the surface velocity of
ISO/TS 7849 and ISO 9611 to the same 5·10⁻⁸ m/s. ``scripts/check_reference_values.py``
holds the tree to that: a reference value declared in the package either
points at this table or says where it was read.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

__all__ = ["ISO1683_REFERENCE_VALUES", "ReferenceValue"]


@dataclass(frozen=True)
class ReferenceValue:
    """One reference value of ISO 1683:2015, with what it is a reference of.

    :ivar quantity: The quantity the value is the reference of, in English
        (``"sound pressure"``, ``"vibratory velocity"``).
    :ivar medium: ``"gas"`` (Table 1), ``"liquid"`` (Table 2) or ``"solid"``
        (Table 3, structure-borne sound and vibration).
    :ivar value: The reference value, in the coherent SI unit :attr:`unit`
        names: 20 µPa is ``2e-05`` with ``unit`` ``"Pa"``.
    :ivar unit: The SI unit of :attr:`value`.
    :ivar printed: The value as the table prints it, prefix and all.
    :ivar table: Where the value is printed: ``"Table 1"`` to ``"Table 3"``,
        or ``"Table 3, note b"`` for the 50 nm/s alternative.
    """

    quantity: str
    medium: str
    value: float
    unit: str
    printed: str
    table: str


def _rows(rows: dict[str, ReferenceValue]) -> Mapping[str, ReferenceValue]:
    return MappingProxyType(rows)


#: ISO 1683:2015 Tables 1 to 3 and the alternative of note b of Table 3, keyed
#: by medium (``"gas"``, ``"liquid"``, ``"solid"``) and then by quantity. Read
#: from UNE-EN ISO 1683:2016, PDF pages 8 and 9 (printed folios 8 and 9).
ISO1683_REFERENCE_VALUES: Mapping[str, Mapping[str, ReferenceValue]] = MappingProxyType(
    {
        "gas": _rows(
            {
                "sound_pressure": ReferenceValue(
                    quantity="sound pressure",
                    medium="gas",
                    value=20e-6,
                    unit="Pa",
                    printed="20 µPa",
                    table="Table 1",
                ),
                "sound_exposure": ReferenceValue(
                    quantity="sound exposure",
                    medium="gas",
                    value=4e-10,
                    unit="Pa²·s",
                    printed="(20 µPa)² s",
                    table="Table 1",
                ),
                "sound_power": ReferenceValue(
                    quantity="sound power",
                    medium="gas",
                    value=1e-12,
                    unit="W",
                    printed="1 pW",
                    table="Table 1",
                ),
                "sound_energy": ReferenceValue(
                    quantity="sound energy",
                    medium="gas",
                    value=1e-12,
                    unit="J",
                    printed="1 pJ",
                    table="Table 1",
                ),
                "sound_intensity": ReferenceValue(
                    quantity="sound intensity",
                    medium="gas",
                    value=1e-12,
                    unit="W/m²",
                    printed="1 pW/m²",
                    table="Table 1",
                ),
            }
        ),
        "liquid": _rows(
            {
                "sound_pressure": ReferenceValue(
                    quantity="sound pressure",
                    medium="liquid",
                    value=1e-6,
                    unit="Pa",
                    printed="1 µPa",
                    table="Table 2",
                ),
                "sound_exposure": ReferenceValue(
                    quantity="sound exposure",
                    medium="liquid",
                    value=1e-12,
                    unit="Pa²·s",
                    printed="1 µPa² s",
                    table="Table 2",
                ),
                "sound_power": ReferenceValue(
                    quantity="sound power",
                    medium="liquid",
                    value=1e-12,
                    unit="W",
                    printed="1 pW",
                    table="Table 2",
                ),
                "sound_energy": ReferenceValue(
                    quantity="sound energy",
                    medium="liquid",
                    value=1e-12,
                    unit="J",
                    printed="1 pJ",
                    table="Table 2",
                ),
                "sound_intensity": ReferenceValue(
                    quantity="sound intensity",
                    medium="liquid",
                    value=1e-12,
                    unit="W/m²",
                    printed="1 pW/m²",
                    table="Table 2",
                ),
                "particle_displacement": ReferenceValue(
                    quantity="sound particle displacement",
                    medium="liquid",
                    value=1e-12,
                    unit="m",
                    printed="1 pm",
                    table="Table 2",
                ),
                "particle_velocity": ReferenceValue(
                    quantity="sound particle velocity",
                    medium="liquid",
                    value=1e-9,
                    unit="m/s",
                    printed="1 nm/s",
                    table="Table 2",
                ),
                "particle_acceleration": ReferenceValue(
                    quantity="sound particle acceleration",
                    medium="liquid",
                    value=1e-6,
                    unit="m/s²",
                    printed="1 µm/s²",
                    table="Table 2",
                ),
                "distance": ReferenceValue(
                    quantity="distance",
                    medium="liquid",
                    value=1.0,
                    unit="m",
                    printed="1 m",
                    table="Table 2",
                ),
            }
        ),
        "solid": _rows(
            {
                "displacement": ReferenceValue(
                    quantity="vibratory displacement",
                    medium="solid",
                    value=1e-12,
                    unit="m",
                    printed="1 pm",
                    table="Table 3",
                ),
                "velocity": ReferenceValue(
                    quantity="vibratory velocity",
                    medium="solid",
                    value=1e-9,
                    unit="m/s",
                    printed="1 nm/s",
                    table="Table 3",
                ),
                "acceleration": ReferenceValue(
                    quantity="vibratory acceleration",
                    medium="solid",
                    value=1e-6,
                    unit="m/s²",
                    printed="1 µm/s²",
                    table="Table 3",
                ),
                "force": ReferenceValue(
                    quantity="vibratory force",
                    medium="solid",
                    value=1e-6,
                    unit="N",
                    printed="1 µN",
                    table="Table 3",
                ),
                "velocity_alternative": ReferenceValue(
                    quantity="vibratory velocity",
                    medium="solid",
                    value=50e-9,
                    unit="m/s",
                    printed="50 nm/s",
                    table="Table 3, note b",
                ),
            }
        ),
    }
)
