#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Predicting sound propagation in a workroom (ISO 11690-3:1998).

Part 1 of ISO 11690 says what a low-noise workplace is and part 2 says what to
do about it. Part 3 is the part that answers "what will it be like before we
build it", and it is unusual among the standards this library implements: it
prints almost no arithmetic. What it prints instead is a way of choosing, and
the choice is between two families of method and four levels of detail of the
data they are fed.

**The two families.** A *diffuse field* method sums a direct field and a
reverberant field that is assumed to be the same everywhere, which is cheap,
needs almost no data, and overestimates the level in a room whose field is not
diffuse. A *geometrical* method traces the sound along straight lines, which
costs a model of the room and pays for it in accuracy. Table 4 splits the
second family into three by how finely the room has to be described, and
Table E.1 says which level of detail of Tables 1 to 3 each category needs.

**What it does compute.** Annex C answers one practical question with one
graph: by how much does the level at a machine's own workstation rise when the
machine is put in a room rather than measured in the open? The answer is the
environmental correction of ISO 3744,

.. math::

   \Delta L_A = 10 \lg\left(1 + \frac{4S}{A}\right) \ \text{dB}, \qquad
   S = S_0 \, 10^{(L_{WA} - L_{pA})/10}

because the difference between the two printed emission quantities is the
measurement surface itself, and the level in the room is the emission level
plus that correction. Figure C.1 is that expression drawn as a flow chart, and
Table C.2 works it for eight machines in a room of 195 m2.

Annex B then adds the contributions of several machines at one workstation on
an energy basis, which is what turns a curve into a decision about which
machine to buy.

**The eighth machine of Table C.2.** Figure C.1 stops at 10 dB, and M8 of the
worked example needs more than that: its 29 dB between the two emission values
gives 12,4 dB in a room of 195 m2, so the row that reports 10 dB is reporting
the top edge of the diagram rather than a reading. The closed form has no such
ceiling, and the errata registry records the row.

Read from BS EN ISO 11690-3:1999, which endorses EN ISO 11690-3:1998 without
modification. The document is dated 1998 in its own header and 1999 on the
British cover.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from .._internal.levels_math import energy_sum
from .._internal.validation import (
    require_finite,
    require_finite_array,
    require_positive,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

    from numpy.typing import ArrayLike

__all__ = [
    "FITTING_DETAIL_LEVELS",
    "PREDICTION_METHODS",
    "RECOMMENDED_DETAIL",
    "ROOM_DETAIL_LEVELS",
    "SOURCE_DETAIL_LEVELS",
    "TYPICAL_DECAY_RANGE_DB",
    "TYPICAL_EXCESS_RANGE_DB",
    "DetailVerdict",
    "PredictionMethod",
    "detail_is_sufficient",
    "fitting_density",
    "prediction_method",
    "total_workstation_level",
    "typical_decay_range",
    "typical_excess_range",
    "workstation_level",
    "workstation_level_increase",
]

#: A range 4.3 states, whose ends may be open where the clause prints none.
_Range = tuple[float | None, float | None]

#: Table 1: how finely the empty room is described, by level of detail.
ROOM_DETAIL_LEVELS: dict[int, str] = {
    1: "the volume and the mean absorption coefficient of the surfaces",
    2: "a box-like shape, one absorption coefficient per surface",
    3: "a box-like shape, surfaces subdivided by absorption coefficient",
    4: "the actual shape, with absorption and reflection distributed over it",
}

#: Table 2: how finely the fittings are described. The NOTE adds that levels 2,
#: 3 and 4 are not mutually exclusive.
FITTING_DETAIL_LEVELS: dict[int, str] = {
    1: "fittings are not taken into account",
    2: "one mean density and one mean absorption for the whole room",
    3: "one mean density and one mean absorption per part of the room",
    4: "the actual shape and location, with shielding and reflection",
}

#: Table 3: how finely the sources are described.
SOURCE_DETAIL_LEVELS: dict[int, str] = {
    1: "omnidirectional point sources",
    2: "point sources with a directivity pattern",
    3: "complex sources",
}

#: 4.3: the range each descriptor of ISO 14257 usually falls in, by region, in
#: decibels. The far region is the one with no upper bound printed: there
#: ``DL2`` may pass 6 dB and ``DLf`` may be negative, because the fittings
#: scatter more than the walls reflect.
TYPICAL_DECAY_RANGE_DB: dict[str, _Range] = {
    "near": (5.0, 6.0),
    "middle": (2.0, 5.0),
    "far": (6.0, None),
}
TYPICAL_EXCESS_RANGE_DB: dict[str, _Range] = {
    "near": (None, None),
    "middle": (2.0, 10.0),
    "far": (None, None),
}


@dataclass(frozen=True)
class PredictionMethod:
    """One row of Table 4, with what Table E.1 asks it to be fed.

    :param category: ``"1"``, ``"2a"``, ``"2b"`` or ``"2c"``.
    :param family: ``"diffuse field"`` or ``"geometrical"``.
    :param rooms: The rooms the category is for, in the words of Table 4.
    :param room_detail: The levels of Table 1 it may be fed.
    :param fitting_detail: The levels of Table 2 it may be fed.
    :param source_detail: The levels of Table 3 it may be fed.
    """

    category: str
    family: str
    rooms: str
    room_detail: tuple[int, ...]
    fitting_detail: tuple[int, ...]
    source_detail: tuple[int, ...]


#: Table 4 and Table E.1 as one table: the four categories with the levels of
#: detail each of them is recommended to be fed.
PREDICTION_METHODS: dict[str, PredictionMethod] = {
    "1": PredictionMethod(
        category="1",
        family="diffuse field",
        rooms="rooms whose field may be treated as diffuse",
        room_detail=(1,),
        fitting_detail=(1,),
        source_detail=(1, 2, 3),
    ),
    "2a": PredictionMethod(
        category="2a",
        family="geometrical",
        rooms=(
            "rooms that can be approximated by one mean absorption coefficient "
            "for each wall and one mean density for the fittings"
        ),
        room_detail=(1, 2),
        fitting_detail=(1, 2),
        source_detail=(1, 2, 3),
    ),
    "2b": PredictionMethod(
        category="2b",
        family="geometrical",
        rooms=(
            "rooms that can be approximated by one mean absorption coefficient "
            "for each room surface and one mean density for the fittings in "
            "each zone"
        ),
        room_detail=(1, 2, 3),
        fitting_detail=(1, 2, 3),
        source_detail=(1, 2, 3),
    ),
    "2c": PredictionMethod(
        category="2c",
        family="geometrical",
        rooms=(
            "rooms for which the individual distribution of absorption and "
            "fittings has to be considered"
        ),
        room_detail=(1, 2, 3, 4),
        fitting_detail=(1, 2, 3, 4),
        source_detail=(1, 2, 3),
    ),
}

#: Table E.1 on its own, as the level ranges keyed by category.
RECOMMENDED_DETAIL: dict[
    str, tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]
] = {
    key: (method.room_detail, method.fitting_detail, method.source_detail)
    for key, method in PREDICTION_METHODS.items()
}


@dataclass(frozen=True)
class DetailVerdict:
    """Whether the data in hand is what a category of method asks for.

    :param category: The category asked about.
    :param satisfied: Whether all three levels fall inside Table E.1.
    :param room_ok: Whether the room description does.
    :param fittings_ok: Whether the fitting description does.
    :param sources_ok: Whether the source description does.
    """

    category: str
    satisfied: bool
    room_ok: bool
    fittings_ok: bool
    sources_ok: bool


def prediction_method(category: str) -> PredictionMethod:
    """One category of Table 4, with the detail levels of Table E.1.

    :param category: ``"1"``, ``"2a"``, ``"2b"`` or ``"2c"``.
    :return: The row, as a :class:`PredictionMethod`.
    :raises ValueError: For a category Table 4 does not print.
    """
    if category not in PREDICTION_METHODS:
        printed = ", ".join(sorted(PREDICTION_METHODS))
        msg = f"Table 4 of ISO 11690-3 prints categories {printed}; got {category!r}."
        raise ValueError(msg)
    return PREDICTION_METHODS[category]


def detail_is_sufficient(
    category: str,
    *,
    room_detail: int,
    fitting_detail: int,
    source_detail: int,
) -> DetailVerdict:
    """Does the data in hand match what Table E.1 asks of this category?

    The table reads in both directions and both are useful: a reader with a
    room description of level 1 and fittings of level 1 is limited to the
    diffuse-field method, and a reader who wants ray tracing over an actual
    room shape has to go and gather a level-4 description of it.

    :param category: ``"1"``, ``"2a"``, ``"2b"`` or ``"2c"``.
    :param room_detail: The level of Table 1 the room is described at.
    :param fitting_detail: The level of Table 2 the fittings are described at.
    :param source_detail: The level of Table 3 the sources are described at.
    :return: The verdict, as a :class:`DetailVerdict`.
    :raises ValueError: For an unknown category or a level no table prints.
    """
    method = prediction_method(category)
    _require_level(room_detail, ROOM_DETAIL_LEVELS, "room_detail", 1)
    _require_level(fitting_detail, FITTING_DETAIL_LEVELS, "fitting_detail", 2)
    _require_level(source_detail, SOURCE_DETAIL_LEVELS, "source_detail", 3)
    room_ok = room_detail in method.room_detail
    fittings_ok = fitting_detail in method.fitting_detail
    sources_ok = source_detail in method.source_detail
    return DetailVerdict(
        category=method.category,
        satisfied=room_ok and fittings_ok and sources_ok,
        room_ok=room_ok,
        fittings_ok=fittings_ok,
        sources_ok=sources_ok,
    )


def _require_level(value: int, table: dict[int, str], name: str, number: int) -> int:
    """A level of detail that one of Tables 1 to 3 actually prints."""
    if value not in table:
        printed = ", ".join(str(key) for key in sorted(table))
        msg = (
            f"Table {number} of ISO 11690-3 prints levels {printed}; "
            f"'{name}' is {value!r}."
        )
        raise ValueError(msg)
    return value


def fitting_density(surface_area_m2: float, volume_m3: float) -> float:
    r"""The density of the fittings, NOTE 3 of 6.2.2.

    .. math::

       q = \frac{S}{4V} \ \text{m}^{-1}

    with :math:`S` the total surface area of the fittings and :math:`V` the
    volume of the room or of the zone they stand in. It is the quantity a
    geometrical method of category 2a or 2b takes instead of the fittings
    themselves.

    :param surface_area_m2: :math:`S`, in square metres.
    :param volume_m3: :math:`V`, in cubic metres.
    :return: :math:`q`, in reciprocal metres.
    :raises ValueError: For a non-positive area or volume.
    """
    area = require_positive(surface_area_m2, "surface_area_m2")
    volume = require_positive(volume_m3, "volume_m3")
    return area / (4.0 * volume)


def workstation_level_increase(
    *,
    sound_power_level_db: float,
    emission_level_db: float,
    absorption_area_m2: float,
) -> float:
    r"""How much the room adds at the machine's own workstation, Annex C.

    .. math::

       \Delta L_A = 10 \lg\left(1 + \frac{4S}{A}\right) \ \text{dB}, \qquad
       \frac{S}{S_0} = 10^{(L_{WA} - L_{pA})/10}

    The two emission quantities a machine is declared with differ by the
    measurement surface: the sound power level is the emission sound pressure
    level plus :math:`10 \lg(S/S_0)`. Put the machine in a room and the
    reverberant field adds the environmental correction of ISO 3744 on top,
    which is what Figure C.1 draws against the equivalent absorption area with
    :math:`L_{WA} - L_{pA}` as the parameter.

    :param sound_power_level_db: :math:`L_{WA}` of the machine, in decibels.
    :param emission_level_db: :math:`L_{pA}` at its workstation, in decibels.
    :param absorption_area_m2: :math:`A` of the room, in square metres.
    :return: :math:`\Delta L_A`, in decibels.
    :raises ValueError: For a non-finite level, a non-positive absorption
        area, or an emission level above the sound power level, which would
        put the workstation inside a measurement surface smaller than a square
        metre.
    """
    power = require_finite(sound_power_level_db, "sound_power_level_db")
    emission = require_finite(emission_level_db, "emission_level_db")
    absorption = require_positive(absorption_area_m2, "absorption_area_m2")
    difference = power - emission
    if difference < 0.0:
        msg = (
            "Annex C reads the measurement surface off the difference "
            "'sound_power_level_db' minus 'emission_level_db', and here that "
            f"difference is {difference:.1f} dB, which is no surface at all."
        )
        raise ValueError(msg)
    surface = 10.0 ** (difference / 10.0)
    return 10.0 * math.log10(1.0 + 4.0 * surface / absorption)


def workstation_level(
    *,
    sound_power_level_db: float,
    emission_level_db: float,
    absorption_area_m2: float,
) -> float:
    r"""The level at the machine's own workstation in the room, Annex C.

    :math:`L'_{pA} = L_{pA} + \Delta L_A`, the emission value the machine was
    declared with plus what the room adds to it.

    :param sound_power_level_db: :math:`L_{WA}` of the machine, in decibels.
    :param emission_level_db: :math:`L_{pA}` at its workstation, in decibels.
    :param absorption_area_m2: :math:`A` of the room, in square metres.
    :return: :math:`L'_{pA}`, in decibels.
    :raises ValueError: As :func:`workstation_level_increase`.
    """
    return emission_level_db + workstation_level_increase(
        sound_power_level_db=sound_power_level_db,
        emission_level_db=emission_level_db,
        absorption_area_m2=absorption_area_m2,
    )


def total_workstation_level(
    contributions_db: ArrayLike, *, existing_level_db: float | None = None
) -> float:
    """What a workstation hears once the new machines are installed, Annex B.

    The contributions are added on an energy basis, with whatever was already
    there added the same way. Annex B reads each contribution off the spatial
    sound distribution curve of the room at the distance between the machine
    and the workstation, except at a machine's own workstation, where
    :func:`workstation_level` gives it from the declared emission values.

    :param contributions_db: The level each new machine alone would give at
        this workstation, in decibels.
    :param existing_level_db: The level already there, in decibels, which for
        a workstation with no machine is the background noise.
    :return: The total, in decibels.
    :raises ValueError: For levels that are not finite.
    """
    levels = require_finite_array(contributions_db, "contributions_db")
    if existing_level_db is not None:
        levels = np.append(
            levels, require_finite(existing_level_db, "existing_level_db")
        )
    return float(energy_sum(levels))


def typical_decay_range(region: str) -> _Range:
    """What 4.3 says ``DL2`` usually is in one region, in decibels.

    :param region: ``"near"``, ``"middle"`` or ``"far"``.
    :return: The lower bound and the upper one, which is ``None`` in the far
        region because the clause prints none.
    :raises ValueError: For a region 4.3 does not name.
    """
    return _region(region, TYPICAL_DECAY_RANGE_DB)


def typical_excess_range(region: str) -> _Range:
    """What 4.3 says ``DLf`` usually is in one region, in decibels.

    The clause prints a range for the middle region alone, and adds that in
    the far region ``DLf`` may be negative; the near region it leaves open.

    :param region: ``"near"``, ``"middle"`` or ``"far"``.
    :return: The lower bound and the upper one, either of which may be
        ``None``.
    :raises ValueError: For a region 4.3 does not name.
    """
    return _region(region, TYPICAL_EXCESS_RANGE_DB)


def _region(region: str, table: Mapping[str, _Range]) -> _Range:
    """One row of the 4.3 ranges, or a refusal naming the three it prints."""
    if region not in table:
        printed = ", ".join(sorted(table))
        msg = f"4.3 of ISO 11690-3 names the regions {printed}; got {region!r}."
        raise ValueError(msg)
    return table[region]
