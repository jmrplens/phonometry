#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Suspended ceilings in a reverberation room: EN 16487:2014.

EN ISO 354 measures the sound absorption of a specimen in a reverberation room
and leaves a good deal to the laboratory: how big the specimen is, how it is
mounted, how deep the air space behind it is. For a suspended ceiling those
choices move the answer by more than the measurement uncertainty, so a product
measured in two laboratories could be compared only by accident. This test code
closes them.

**What it fixes.** A specimen area as close to 10,80 m2 as the product allows,
test objects of 0,6 m by 0,6 m butted together with no seal in the joints
between them, the exposed face level with the top of the mounting fixture and
the joint between the specimen and that fixture taped, the edges at an angle to
the room walls, and a mounting fixture of solid material with a surface density
of at least 20 kg/m2. For the type E mounting that a suspended ceiling actually
uses, it fixes the overall depth of construction at 200 mm for the measurement
that CE marking rests on, the substructure at no more than 30 mm wide and 50 mm
deep on a pitch of about 0,6 m, the support units under it at no more than
50 mm by 50 mm in cross-section and at least 1,2 m apart, and the deflection of
the specimen at no more than 5 mm.

**What it costs to ignore the air.** 4.2.1 asks for test conditions under which
the air-absorption correction

.. math::

   \Delta\alpha = \frac{4V(m_2 - m_1)}{S}

of EN ISO 354 Formulae (8) and (9) stays under 0,05 at every frequency, with
the relative humidity at 50 % or more. That correction is the difference between
two measurements of the same room on two different days, and a dry room makes it
large exactly where a ceiling absorbs most.

**What it is worth.** Table 1 is the reproducibility between European
laboratories, from the round robin of Annex A: ``+/- 0,23`` on the absorption
coefficient at 125 Hz and 250 Hz, falling to ``+/- 0,10`` at 1 kHz and 2 kHz,
and ``+/- 0,08`` on the weighted rating, with a coverage factor of 2,8 applied
to the reproducibility standard deviation. The figures hold for a plane absorber
with the type E mounting and for nothing else, which the clause says in as many
words.

Read from BS EN 16487:2014.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING

import numpy as np

from ..._internal.validation import (
    require_choice,
    require_finite_array,
    require_non_negative,
    require_positive,
    require_positive_array,
)
from ..._internal.warnings import PhonometryWarning

if TYPE_CHECKING:  # pragma: no cover - typing only
    from collections.abc import Mapping

    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "AIR_CORRECTION_LIMIT",
    "CEILING_UNCERTAINTY",
    "EN16487_COVERAGE_FACTOR",
    "MAX_DEFLECTION_MM",
    "MIN_FIXTURE_DENSITY_KG_M2",
    "MIN_RELATIVE_HUMIDITY_PERCENT",
    "MIN_ROOM_EDGE_ANGLE_DEG",
    "MIN_SUPPORT_SPACING_M",
    "MOUNTING_TYPES",
    "SUBSTRUCTURE_LIMITS_MM",
    "SUBSTRUCTURE_SPACING_M",
    "SUPPORT_SECTION_MM",
    "TEST_OBJECT_SIZE_M",
    "TYPE_E_DEPTH_MM",
    "TARGET_SPECIMEN_AREA_M2",
    "WEIGHTED_UNCERTAINTY",
    "CeilingSpecimenCheck",
    "SuspendedCeilingWarning",
    "air_absorption_correction",
    "check_ceiling_specimen",
    "mounting_type",
    "reproducibility_uncertainty",
]


class SuspendedCeilingWarning(PhonometryWarning):
    """The test arrangement departs from a condition EN 16487 states.

    Most often a limit of clause 4 it has left. The one exception is a type E
    depth other than 200 mm: the test code admits it, and the warning says only
    that the result is not the one CE marking data is compiled from.
    """


#: 4.1.1.1.1: the specimen area the test code aims at, in square metres, which
#: is the middle of the range EN ISO 354 allows.
TARGET_SPECIMEN_AREA_M2: float = 10.80

#: 4.1.1.1.2: the size one test object should be, in metres, or failing that
#: the closest size in the product range. A target to build to, so
#: :func:`check_ceiling_specimen` does not judge it.
TEST_OBJECT_SIZE_M: tuple[float, float] = (0.6, 0.6)

#: 4.1.1.1.5: the angle the specimen edges should make with the nearest room
#: edge, in degrees. The clause says it "should be aimed at", so it is a target
#: and :func:`check_ceiling_specimen` does not judge it.
MIN_ROOM_EDGE_ANGLE_DEG: float = 10.0

#: 4.1.1.1.6: the surface density of the mounting fixture, in kilograms per
#: square metre.
MIN_FIXTURE_DENSITY_KG_M2: float = 20.0

#: 4.1.1.2.3.1: the overall depth of construction of the type E mounting that
#: CE marking data rests on, in millimetres.
TYPE_E_DEPTH_MM: float = 200.0

#: 4.1.1.2.3.4: the largest substructure profile, in millimetres, as width and
#: height, and the pitch it is laid on, in metres. The pitch is printed as
#: "approx. 0,6 m", so :func:`check_ceiling_specimen` judges the profile and
#: not the pitch.
SUBSTRUCTURE_LIMITS_MM: tuple[float, float] = (30.0, 50.0)
SUBSTRUCTURE_SPACING_M: float = 0.6

#: 4.1.1.2.3.5: the largest deflection of the specimen, in millimetres.
MAX_DEFLECTION_MM: float = 5.0

#: 4.1.1.2.3.6: the largest support unit cross-section, in millimetres, and the
#: smallest centre distance between supports, in metres.
SUPPORT_SECTION_MM: tuple[float, float] = (50.0, 50.0)
MIN_SUPPORT_SPACING_M: float = 1.2

#: 4.2.1: the air-absorption correction shall stay under this at every
#: frequency, as an absorption coefficient.
AIR_CORRECTION_LIMIT: float = 0.05

#: 4.2.2: the lowest relative humidity of the room, in percent, which 4.2.3
#: asks to be checked for each measurement.
MIN_RELATIVE_HUMIDITY_PERCENT: float = 50.0

#: Saturation, the physical ceiling on a relative humidity, in percent.
_SATURATION_PERCENT = 100.0

#: Table 1: the reproducibility uncertainty of the sound absorption
#: coefficient, by nominal octave centre frequency in hertz. The 125 Hz row
#: carries its own footnote: that band is not part of the weighted rating.
CEILING_UNCERTAINTY: Mapping[float, float] = MappingProxyType(
    {
        125.0: 0.23,
        250.0: 0.23,
        500.0: 0.11,
        1000.0: 0.10,
        2000.0: 0.10,
        4000.0: 0.13,
    }
)

#: Table 1, last row: the same for the weighted sound absorption coefficient,
#: computed without rounding anywhere in the EN ISO 11654 chain.
WEIGHTED_UNCERTAINTY: float = 0.08

#: The note under Table 1: the coverage factor ISO 5725-6 applies to the
#: reproducibility standard deviation to reach those figures.
EN16487_COVERAGE_FACTOR: float = 2.8

#: 4.1.1.2 and 4.1.2.1: the mountings this test code admits, by the letter
#: EN ISO 354 Annex B gives them.
MOUNTING_TYPES: Mapping[str, str] = MappingProxyType(
    {
        "A": "attached directly against a hard surface, with no air space",
        "B": "glued to a hard surface with a 3 mm air space kept by corner shims",
        "E": "suspended from a hard surface with an air space behind it",
        "J": "a discrete absorber, freely suspended or standing",
    }
)


@dataclass(frozen=True)
class CeilingSpecimenCheck:
    """Whether a test arrangement meets the printed limits of clause 4.

    The verdict covers the limits clause 4 puts a number on and a measured
    arrangement can be held to: the mounting fixture of 4.1.1.1.6, the
    substructure profile of 4.1.1.2.3.4, the deflection of 4.1.1.2.3.5, the
    support units of 4.1.1.2.3.6 and, when it was given, the relative humidity
    of 4.2.2. Two figures are reported beside the verdict and kept out of it,
    because the clause does not make them a pass or a fail: the area error,
    since 4.1.1.1.1 asks for an area "as close to 10,80 m2 as possible", and the
    CE marking depth, since 4.1.1.2.3.1 recommends 200 mm and requires it only
    of the data CE marking is compiled from.

    :param area_m2: The specimen area as built, in square metres.
    :param area_error_m2: How far it sits from the 10,80 m2 the code aims at,
        reported and not judged.
    :param mounting: The mounting letter the arrangement uses.
    :param depth_mm: The overall depth of construction, in millimetres, for a
        type E mounting, or ``None`` for the others.
    :param deflection_ok: Whether the deflection stays inside 5 mm.
    :param substructure_ok: Whether the profile stays inside 30 mm by 50 mm.
    :param fixture_ok: Whether the mounting fixture is heavy enough.
    :param supports_ok: Whether the support units stay inside 50 mm by 50 mm
        in cross-section and, when their centre distance was given, stand at
        least 1,2 m apart.
    :param humidity_ok: Whether every measurement was made at 50 % relative
        humidity or more, or ``None`` when no humidity was given.
    :param ce_marking_depth: Whether the depth is the 200 mm the CE marking
        data rests on, reported and not judged.
    :param satisfied: Whether every judged limit holds: the fixture, the
        substructure, the deflection, the supports and, when it was given, the
        humidity.
    """

    area_m2: float
    area_error_m2: float
    mounting: str
    depth_mm: float | None
    deflection_ok: bool
    substructure_ok: bool
    fixture_ok: bool
    supports_ok: bool
    humidity_ok: bool | None
    ce_marking_depth: bool
    satisfied: bool


def mounting_type(letter: str) -> str:
    """What one mounting letter of EN ISO 354 Annex B means here.

    :param letter: ``"A"``, ``"B"``, ``"E"`` or ``"J"``.
    :return: The description in the words of 4.1.1.2.
    :raises ValueError: For a letter this test code does not admit.
    """
    key = require_choice(str(letter).upper(), "letter", tuple(MOUNTING_TYPES))
    return MOUNTING_TYPES[key]


def air_absorption_correction(
    *,
    volume_m3: float,
    specimen_area_m2: float,
    attenuation_with: ArrayLike,
    attenuation_empty: ArrayLike,
) -> NDArray[np.float64]:
    r"""The correction 4.2.1 caps, as an absorption coefficient.

    .. math::

       \Delta\alpha = \frac{4V(m_2 - m_1)}{S}

    the part of EN ISO 354 Formulae (8) and (9) that comes from the air rather
    than from the specimen. The two attenuation coefficients belong to the two
    measurements, with the specimen and empty, and the correction is their
    difference because everything else about the room cancels.

    A room measured on two days of different humidity can carry more of this
    than the specimen carries of its own absorption at 4 kHz, which is why the
    clause caps it at :data:`AIR_CORRECTION_LIMIT` and asks for 50 % relative
    humidity or more.

    :param volume_m3: :math:`V` of the reverberation room, in cubic metres.
    :param specimen_area_m2: :math:`S` of the specimen, in square metres.
    :param attenuation_with: :math:`m_2` per band, in reciprocal metres.
    :param attenuation_empty: :math:`m_1` per band, in reciprocal metres.
    :return: :math:`\Delta\alpha` per band.
    :raises ValueError: For a non-positive volume or area, or coefficients
        that do not match band for band.
    """
    volume = require_positive(volume_m3, "volume_m3")
    area = require_positive(specimen_area_m2, "specimen_area_m2")
    with_specimen = require_finite_array(attenuation_with, "attenuation_with")
    empty = require_finite_array(attenuation_empty, "attenuation_empty")
    if with_specimen.shape != empty.shape:
        msg = "'attenuation_with' and 'attenuation_empty' must match band for band."
        raise ValueError(msg)
    correction = np.asarray(
        4.0 * volume * (with_specimen - empty) / area, dtype=np.float64
    )
    worst = float(np.max(np.abs(correction)))
    if worst > AIR_CORRECTION_LIMIT:
        msg = (
            f"The air-absorption correction reaches {worst:.3f} at one band, "
            f"over the {AIR_CORRECTION_LIMIT:g} of 4.2.1: the test conditions "
            "are not the ones the clause asks for, and 5.2 asks for the empty "
            "room to be measured again rather than for the result to be "
            "reported."
        )
        warnings.warn(msg, SuspendedCeilingWarning, stacklevel=2)
    return correction


def reproducibility_uncertainty(
    frequencies: ArrayLike | None = None,
) -> NDArray[np.float64]:
    """Table 1, the reproducibility between European laboratories.

    The figures are an expanded uncertainty: the round robin of Annex A gives a
    reproducibility standard deviation and ISO 5725-6 multiplies it by
    :data:`EN16487_COVERAGE_FACTOR`. They hold for a plane absorber with the type E
    mounting and a 200 mm overall depth, and 6.2 says plainly that nothing has
    been investigated for any other absorber or mounting.

    :param frequencies: The nominal octave centres wanted, in hertz; omit for
        the six the table prints, in order.
    :return: The uncertainty of the absorption coefficient in each band.
    :raises ValueError: For a frequency Table 1 does not print.
    """
    if frequencies is None:
        return np.asarray(list(CEILING_UNCERTAINTY.values()), dtype=np.float64)
    bands = require_positive_array(frequencies, "frequencies")
    out = []
    for band in bands.tolist():
        match = [
            centre
            for centre in CEILING_UNCERTAINTY
            if math.isclose(band, centre, rel_tol=1e-3)
        ]
        if not match:
            printed = ", ".join(f"{centre:g}" for centre in CEILING_UNCERTAINTY)
            msg = f"Table 1 of EN 16487 prints {printed} Hz; got {band:g} Hz."
            raise ValueError(msg)
        out.append(CEILING_UNCERTAINTY[match[0]])
    return np.asarray(out, dtype=np.float64)


def _lowest_humidity(relative_humidity_percent: ArrayLike | None) -> float | None:
    """The driest of the measurements, or ``None`` when no humidity was given.

    4.2.3 checks the humidity for each measurement and 4.2.2 puts a floor under
    every one of them, so the driest measurement is the one the floor judges.
    A relative humidity outside 0 % to 100 % is not a state of the air at all,
    and is refused rather than judged.
    """
    if relative_humidity_percent is None:
        return None
    humidity = require_finite_array(
        relative_humidity_percent, "relative_humidity_percent"
    )
    if np.any(humidity < 0.0) or np.any(humidity > _SATURATION_PERCENT):
        msg = "'relative_humidity_percent' must be within [0, 100] %."
        raise ValueError(msg)
    return float(np.min(humidity))


def _warn_about(
    *,
    check: CeilingSpecimenCheck,
    section_ok: bool,
    spacing_ok: bool,
    deflection_mm: float,
    support_centre_distance_m: float | None,
    lowest_humidity_percent: float | None,
) -> None:
    """Say which printed limit of clause 4 the arrangement has left.

    Only the limits the verdict judges are warned about as leaving EN 16487.
    The CE marking depth is said in a sentence of its own: 4.1.1.2.3.1
    recommends 200 mm and requires it only of the data CE marking is compiled
    from, so another depth is still inside the test code. The specimen area is
    not warned about at all: 4.1.1.1.1 asks for an area "as close to 10,80 m2
    as possible", which is a target rather than a tolerance, so the check
    reports the difference and leaves the judgement to the laboratory.
    """
    max_width, max_height = SUBSTRUCTURE_LIMITS_MM
    support_width, support_height = SUPPORT_SECTION_MM
    reasons = []
    if not check.deflection_ok:
        reasons.append(
            f"the specimen deflects {deflection_mm:g} mm, over the "
            f"{MAX_DEFLECTION_MM:g} mm of 4.1.1.2.3.5"
        )
    if not check.substructure_ok:
        reasons.append(
            f"the substructure is larger than the {max_width:g} mm by "
            f"{max_height:g} mm of 4.1.1.2.3.4"
        )
    if not check.fixture_ok:
        reasons.append(
            f"the mounting fixture is lighter than the "
            f"{MIN_FIXTURE_DENSITY_KG_M2:g} kg/m2 of 4.1.1.1.6"
        )
    if not section_ok:
        reasons.append(
            f"the support units are larger in cross-section than the "
            f"{support_width:g} mm by {support_height:g} mm of 4.1.1.2.3.6"
        )
    if not spacing_ok:
        reasons.append(
            f"the support units stand {support_centre_distance_m:g} m apart, "
            f"closer than the {MIN_SUPPORT_SPACING_M:g} m of 4.1.1.2.3.6"
        )
    if check.humidity_ok is False:
        reasons.append(
            f"the relative humidity falls to {lowest_humidity_percent:g} % in a "
            f"measurement, under the {MIN_RELATIVE_HUMIDITY_PERCENT:g} % of 4.2.2"
        )
    sentences = []
    if reasons:
        sentences.append(
            "The arrangement is outside EN 16487: " + "; ".join(reasons) + "."
        )
    if check.mounting == "E" and not check.ce_marking_depth:
        sentences.append(
            f"The overall depth of {check.depth_mm:g} mm is not the "
            f"{TYPE_E_DEPTH_MM:g} mm that 4.1.1.2.3.1 recommends and fixes for "
            "the data CE marking is compiled from."
        )
    if sentences:
        warnings.warn(" ".join(sentences), SuspendedCeilingWarning, stacklevel=3)


def check_ceiling_specimen(
    *,
    area_m2: float,
    mounting: str = "E",
    depth_mm: float | None = None,
    deflection_mm: float = 0.0,
    substructure_width_mm: float = 0.0,
    substructure_height_mm: float = 0.0,
    fixture_density_kg_m2: float = MIN_FIXTURE_DENSITY_KG_M2,
    support_width_mm: float = 0.0,
    support_height_mm: float = 0.0,
    support_centre_distance_m: float | None = None,
    relative_humidity_percent: ArrayLike | None = None,
) -> CeilingSpecimenCheck:
    """Does the test arrangement meet the printed limits of clause 4?

    Clause 4 of EN 16487, "Test arrangements", holds both the specimen of 4.1
    and the temperature and humidity of 4.2. The verdict judges every bound of
    it that a number of the arrangement as built can be held to:

    * a mounting fixture of at least 20 kg/m2 (4.1.1.1.6);
    * a substructure profile no wider than 30 mm and no higher than 50 mm
      (4.1.1.2.3.4);
    * a deflection of the specimen of no more than 5 mm (4.1.1.2.3.5);
    * support units no larger than 50 mm by 50 mm in cross-section, at centre
      distances of at least 1,2 m (4.1.1.2.3.6);
    * when it is given, a relative humidity of at least 50 % in every
      measurement (4.2.2, checked for each measurement by 4.2.3).

    Leaving one of them raises a :class:`SuspendedCeilingWarning` that names
    it, and makes ``satisfied`` false. A substructure and support units are
    what 4.1.1.2.3.4 and 4.1.1.2.3.6 allow rather than require, so their
    dimensions default to zero, which is none at all, and the centre distance
    is judged only when it is given. The cap of 4.2.1 on the air-absorption
    correction is judged where that correction is computed, by
    :func:`air_absorption_correction`.

    Two figures are reported and kept out of the verdict. The area error,
    because 4.1.1.1.1 asks for an area "as close to 10,80 m2 as possible",
    which is a target and not a tolerance. And whether a type E depth is the
    200 mm that 4.1.1.2.3.1 recommends and fixes for the data CE marking is
    compiled from: another depth is said in the warning and passes.

    Three printed figures are targets to build to and are not judged at all:
    the 0,6 m by 0,6 m test object of 4.1.1.1.2 (:data:`TEST_OBJECT_SIZE_M`),
    which "should" be that size and otherwise the closest in the product
    range; the 10 degree edge angle of 4.1.1.1.5
    (:data:`MIN_ROOM_EDGE_ANGLE_DEG`), which "should be aimed at"; and the
    substructure pitch of "approx. 0,6 m" of 4.1.1.2.3.4
    (:data:`SUBSTRUCTURE_SPACING_M`).

    :param area_m2: The specimen area as built, in square metres.
    :param mounting: The mounting letter, ``"E"`` by default.
    :param depth_mm: The overall depth of construction, in millimetres,
        required for a type E mounting.
    :param deflection_mm: The largest deflection of the specimen, in
        millimetres.
    :param substructure_width_mm: The substructure profile width, in
        millimetres.
    :param substructure_height_mm: Its height, in millimetres.
    :param fixture_density_kg_m2: The surface density of the mounting fixture,
        in kilograms per square metre.
    :param support_width_mm: One side of the cross-section of the support
        units, in millimetres; zero when the substructure has none.
    :param support_height_mm: The other side, in millimetres.
    :param support_centre_distance_m: The centre distance between support
        units, in metres, or ``None`` when there are none or it was not
        recorded.
    :param relative_humidity_percent: The relative humidity of the room in
        each measurement, in percent, one value per measurement, or ``None``
        to leave 4.2.2 unjudged.
    :return: The verdict, as a :class:`CeilingSpecimenCheck`.
    :raises ValueError: For a non-positive area or depth, a negative or
        non-finite deflection, substructure or support dimension or fixture
        density, a non-positive or non-finite support centre distance, a
        relative humidity that is empty, not one-dimensional, not finite or
        outside 0 % to 100 %, an unknown mounting letter, or a type E
        arrangement with no depth given.
    """
    area = require_positive(area_m2, "area_m2")
    letter = require_choice(str(mounting).upper(), "mounting", tuple(MOUNTING_TYPES))
    if letter == "E" and depth_mm is None:
        msg = (
            "A type E mounting is defined by the air space behind it, so "
            "'depth_mm' is what 4.1.1.2.3 asks to be reported."
        )
        raise ValueError(msg)
    depth = None if depth_mm is None else require_positive(depth_mm, "depth_mm")
    # Each of these is a measured length or a surface density, so it is read
    # before the limits rather than after: an upper bound alone would let a
    # negative width, or a negative infinity, pass 4.1.1.2.3.4 as conforming.
    deflection = require_non_negative(deflection_mm, "deflection_mm")
    width = require_non_negative(substructure_width_mm, "substructure_width_mm")
    height = require_non_negative(substructure_height_mm, "substructure_height_mm")
    fixture = require_non_negative(fixture_density_kg_m2, "fixture_density_kg_m2")
    support_width = require_non_negative(support_width_mm, "support_width_mm")
    support_height = require_non_negative(support_height_mm, "support_height_mm")
    spacing = (
        None
        if support_centre_distance_m is None
        else require_positive(support_centre_distance_m, "support_centre_distance_m")
    )
    lowest_humidity = _lowest_humidity(relative_humidity_percent)
    max_width, max_height = SUBSTRUCTURE_LIMITS_MM
    max_support_width, max_support_height = SUPPORT_SECTION_MM
    section_ok = (
        support_width <= max_support_width and support_height <= max_support_height
    )
    spacing_ok = spacing is None or spacing >= MIN_SUPPORT_SPACING_M
    humidity_ok = (
        None
        if lowest_humidity is None
        else lowest_humidity >= MIN_RELATIVE_HUMIDITY_PERCENT
    )
    deflection_ok = deflection <= MAX_DEFLECTION_MM
    substructure_ok = width <= max_width and height <= max_height
    fixture_ok = fixture >= MIN_FIXTURE_DENSITY_KG_M2
    supports_ok = section_ok and spacing_ok
    # 4.1.1.2.3.1 fixes the depth for the type E mounting alone, so a type A
    # specimen laid against a hard surface cannot reach the CE marking depth by
    # being 200 mm thick.
    ce_depth = (
        letter == "E"
        and depth is not None
        and math.isclose(depth, TYPE_E_DEPTH_MM, rel_tol=1e-6)
    )
    check = CeilingSpecimenCheck(
        area_m2=area,
        area_error_m2=area - TARGET_SPECIMEN_AREA_M2,
        mounting=letter,
        depth_mm=depth,
        deflection_ok=deflection_ok,
        substructure_ok=substructure_ok,
        fixture_ok=fixture_ok,
        supports_ok=supports_ok,
        humidity_ok=humidity_ok,
        ce_marking_depth=ce_depth,
        # A humidity that was not given is not judged, so only a measured
        # humidity under the floor fails the arrangement.
        satisfied=(
            deflection_ok
            and substructure_ok
            and fixture_ok
            and supports_ok
            and humidity_ok is not False
        ),
    )
    _warn_about(
        check=check,
        section_ok=section_ok,
        spacing_ok=spacing_ok,
        deflection_mm=deflection,
        support_centre_distance_m=spacing,
        lowest_humidity_percent=lowest_humidity,
    )
    return check
