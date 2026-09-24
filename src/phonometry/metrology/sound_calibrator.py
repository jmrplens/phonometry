#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Sound calibrators (IEC 60942:2017): the class tables and the verdict on one.

A calibrator is the one instrument every calibrated level in this library
leans on: :func:`phonometry.metrology.sensitivity` turns its tone into the
factor that converts digital units into pascals, so an error in the tone is
an error in every level measured after it. IEC 60942:2017 (EN IEC 60942:2018)
says how good the tone has to be, in three classes: **LS** (laboratory
standard), **1** and **2**, with the designations **LS/M** and **1/M** for
pistonphones that meet their class only once a static-pressure correction from
the manufacturer is applied (5.1.5, Table 1).

**What is graded.** Every requirement of the standard that is a measured
number with an acceptance limit and a maximum-permitted uncertainty:

* ``level`` (5.3.2): Table 2, with the maximum uncertainty of Table A.1;
* ``fluctuation`` (5.3.3): Table 2, with Table A.1;
* ``frequency`` (5.4.2): Table 4, with Table A.2;
* ``distortion`` (5.6): Table 7, with Table A.3;
* ``supply_voltage`` (5.3.4): Table 3, with the maximum A.5.5.7 and A.5.5.8
  print in their text;
* ``environmental_level`` (5.5): Table 5, or the reduced limits of A.6.4.7,
  with Table A.4;
* ``environmental_frequency`` (5.5): Table 6, or A.6.4.7, with Table A.5;
* ``field_immunity`` (5.9.4.2): the limits 5.9.4.2 prints, with the maximum of
  A.7.4.8.

Each is judged by the conformance rule of IEC TC 29
(:func:`phonometry.metrology.verify_conformance`, 5.1.15): the measured
deviation within the acceptance limit **and** the laboratory's actual expanded
uncertainty within the maximum permitted, both inclusive. The deviation limits
of the level, the supply-voltage effect, the frequency and the field immunity
bound an *absolute* difference, so a signed deviation is judged against
:math:`\pm` the limit; the short-term fluctuation and the total distortion +
noise are magnitudes, judged against zero and the limit.

**The tables.** Tables 2, 5 and 7 and Tables A.1, A.3 and A.4 are keyed by a
range of nominal frequencies, published as tuples of :class:`CalibratorTableRow`;
Tables 3, 4 and 6 and Tables A.2 and A.5 hold one figure per class, published as
read-only mappings keyed by ``"LS"``, ``"1"`` and ``"2"``. A dash in the printed
table, the ranges of nominal frequency "for which this document provides no
acceptance limits", is ``None``: classes LS and 2 are specified only from
160 Hz to 1 250 Hz, and 5.1.2 forbids stating conformance where there is no
limit, so :func:`verify_sound_calibrator` refuses such a nominal frequency
rather than grading it against a neighbouring row.

**The /M correction is an input.** A class LS/M or 1/M pistonphone's output
follows the ambient static pressure, and its manual gives the correction to
the reference 101,325 kPa (5.1.5, 6.3 i). That correction depends on the
barometer reading and on data only the manufacturer has, so this module does
not compute it: the caller supplies it as
:attr:`SoundCalibratorMeasurements.static_pressure_correction_db` and it is
added to the measured level before the level is graded (5.3.2, A.5.1.2,
B.4.3.2). Every other calibrator shall not need any environmental correction
(5.1.7), and is refused one.

**The abbreviated environmental test.** A.6.4 lets a laboratory replace the
full temperature and humidity tests (A.6.5 to A.6.7) with a few combined
conditions judged against tighter limits: Table 5 reduced by 0,05 dB for
classes LS and 1 and by 0,10 dB for class 2, and 0,5 %, 0,5 % and 1,3 % for the
frequency (A.6.4.7). A calibrator that meets those is deemed to conform; one
that does not is **not** thereby non-conforming, it has to be given the full
tests (A.6.1.2). ``environmental_test="abbreviated"`` applies the reduced limits
and the verdict means exactly that.

**What a verdict here is and is not.** It grades the numbers a laboratory
measured; it measures nothing. The requirements that are not numbers with a
tolerance (the markings and the manual of Clause 6, the stabilization time of
5.1.10, the supply indicator of 5.7, the radio-frequency emission limits of
5.9.2 and the electrostatic discharges of 5.9.3) are hardware and paperwork
checks outside it. And 5.1.18 is explicit that full conformance needs both
halves: the model passing the pattern evaluation of Annex A and the specimen
passing the periodic tests of Annex B, whose own verdict names only what was
tested (B.6 g, h).
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, cast

import numpy as np

from .._internal.validation import require_choice, require_positive
from .conformance import ConformanceVerification, verify_conformance

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes

__all__ = [
    "ABBREVIATED_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT",
    "ABBREVIATED_LEVEL_REDUCTIONS_DB",
    "CALIBRATOR_CLASSES",
    "CALIBRATOR_REQUIREMENTS",
    "DISTORTION_ACCEPTANCE_LIMITS_PERCENT",
    "DISTORTION_MAX_UNCERTAINTY_PERCENT",
    "ENVIRONMENTAL_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT",
    "ENVIRONMENTAL_FREQUENCY_MAX_UNCERTAINTY_PERCENT",
    "ENVIRONMENTAL_LEVEL_ACCEPTANCE_LIMITS_DB",
    "ENVIRONMENTAL_LEVEL_MAX_UNCERTAINTY_DB",
    "FIELD_IMMUNITY_ACCEPTANCE_LIMITS_DB",
    "FIELD_IMMUNITY_MAX_UNCERTAINTY_DB",
    "FLUCTUATION_ACCEPTANCE_LIMITS_DB",
    "FLUCTUATION_MAX_UNCERTAINTY_DB",
    "FREQUENCY_ACCEPTANCE_LIMITS_PERCENT",
    "FREQUENCY_MAX_UNCERTAINTY_PERCENT",
    "LEVEL_ACCEPTANCE_LIMITS_DB",
    "LEVEL_MAX_UNCERTAINTY_DB",
    "SUPPLY_VOLTAGE_ACCEPTANCE_LIMITS_DB",
    "SUPPLY_VOLTAGE_MAX_UNCERTAINTY_DB",
    "CalibratorTableRow",
    "SoundCalibratorMeasurements",
    "SoundCalibratorRequirement",
    "SoundCalibratorVerification",
    "verify_sound_calibrator",
]


@dataclass(frozen=True)
class CalibratorTableRow:
    """One row of an IEC 60942:2017 table keyed by a range of nominal frequencies.

    The printed ranges close and open their ends differently ("31,5 to 63",
    "> 63 to < 160", "> 1 250 to 4 000"), so each row says which of its two
    ends it includes. A cell the table prints as a dash, a range the standard
    gives that class no limit in, is ``None``.

    :ivar lower_hz: The lower end of the range of nominal frequencies, in hertz.
    :ivar upper_hz: The upper end, in hertz.
    :ivar includes_lower: Whether a nominal frequency equal to ``lower_hz``
        belongs to the row.
    :ivar includes_upper: Whether a nominal frequency equal to ``upper_hz``
        belongs to the row.
    :ivar class_ls: The class LS figure, or ``None`` for a dash.
    :ivar class_1: The class 1 figure, or ``None`` for a dash.
    :ivar class_2: The class 2 figure, or ``None`` for a dash.
    """

    lower_hz: float
    upper_hz: float
    includes_lower: bool
    includes_upper: bool
    class_ls: float | None
    class_1: float | None
    class_2: float | None

    def contains(self, nominal_frequency_hz: float) -> bool:
        """Whether a nominal frequency falls in this row's range.

        :param nominal_frequency_hz: The nominal frequency, in hertz.
        :return: ``True`` inside the range, its included ends counted.
        """
        f = float(nominal_frequency_hz)
        above = f >= self.lower_hz if self.includes_lower else f > self.lower_hz
        below = f <= self.upper_hz if self.includes_upper else f < self.upper_hz
        return above and below

    def for_class(self, calibrator_class: str) -> float | None:
        """The figure this row prints for a class, or ``None`` for a dash.

        :param calibrator_class: ``"LS"``, ``"1"`` or ``"2"``, or a /M
            designation, which reads the column of its class (5.1.14).
        :return: The printed figure, or ``None`` where the table prints a dash.
        :raises ValueError: for an unknown class.
        """
        column = {"LS": self.class_ls, "1": self.class_1, "2": self.class_2}
        return column[_base_class(calibrator_class)]


def _row(
    lower_hz: float,
    upper_hz: float,
    ends: str,
    cells: tuple[float | None, float | None, float | None],
) -> CalibratorTableRow:
    """One printed row: ``ends`` is ``"[]"``, ``"()"``, ``"(]"`` or ``"[)"``."""
    return CalibratorTableRow(
        lower_hz, upper_hz, ends[0] == "[", ends[1] == "]", *cells
    )


#: The classes and designations of IEC 60942:2017 Table 1 (folio 13): LS
#: (laboratory standard), 1 and 2, and the pistonphone designations LS/M and
#: 1/M that meet their class only with the manufacturer's static-pressure
#: correction applied (5.1.5).
CALIBRATOR_CLASSES: tuple[str, ...] = ("LS", "LS/M", "1", "1/M", "2")

#: The requirements :func:`verify_sound_calibrator` grades, in the order it
#: reports them. The unit of each is in its name in
#: :class:`SoundCalibratorMeasurements`.
CALIBRATOR_REQUIREMENTS: tuple[str, ...] = (
    "level",
    "fluctuation",
    "frequency",
    "distortion",
    "supply_voltage",
    "environmental_level",
    "environmental_frequency",
    "field_immunity",
)

#: IEC 60942:2017 Table 2 (folio 16), sound pressure level half: the
#: acceptance limit on the absolute difference between the generated and the
#: specified sound pressure level, in decibels, at and around the reference
#: environmental conditions (5.3.2). Classes LS and 2 are specified from
#: 160 Hz to 1 250 Hz only.
LEVEL_ACCEPTANCE_LIMITS_DB: tuple[CalibratorTableRow, ...] = (
    _row(31.5, 63.0, "[]", (None, 0.30, None)),
    _row(63.0, 160.0, "()", (None, 0.30, None)),
    _row(160.0, 1250.0, "[]", (0.10, 0.25, 0.40)),
    _row(1250.0, 4000.0, "(]", (None, 0.35, None)),
    _row(4000.0, 8000.0, "(]", (None, 0.45, None)),
    _row(8000.0, 16000.0, "(]", (None, 0.50, None)),
)

#: IEC 60942:2017 Table 2 (folio 16), short-term level fluctuation half: the
#: acceptance limit on each of the absolute differences between the maximum
#: and the minimum F-weighted level and their mean over 60 s (5.3.3), in
#: decibels. It is raised at low frequency because the F time weighting
#: itself ripples there (5.3.3, NOTE 2).
FLUCTUATION_ACCEPTANCE_LIMITS_DB: tuple[CalibratorTableRow, ...] = (
    _row(31.5, 63.0, "[]", (None, 0.20, None)),
    _row(63.0, 160.0, "()", (None, 0.10, None)),
    _row(160.0, 1250.0, "[]", (0.03, 0.07, 0.15)),
    _row(1250.0, 4000.0, "(]", (None, 0.07, None)),
    _row(4000.0, 8000.0, "(]", (None, 0.07, None)),
    _row(8000.0, 16000.0, "(]", (None, 0.07, None)),
)

#: IEC 60942:2017 Table 3 (folio 16): the acceptance limit on the absolute
#: difference between the level generated over the range of supply voltage
#: and the level at the nominal supply voltage (5.3.4), in decibels, by class.
SUPPLY_VOLTAGE_ACCEPTANCE_LIMITS_DB: Mapping[str, float] = MappingProxyType(
    {"LS": 0.02, "1": 0.06, "2": 0.16}
)

#: IEC 60942:2017 Table 4 (folio 17): the acceptance limit on the absolute
#: difference between the generated and the specified frequency (5.4.2), in
#: per cent of the specified frequency, by class.
FREQUENCY_ACCEPTANCE_LIMITS_PERCENT: Mapping[str, float] = MappingProxyType(
    {"LS": 0.7, "1": 0.7, "2": 1.7}
)

#: IEC 60942:2017 Table 5 (folio 18): the acceptance limit on the absolute
#: difference between the level generated over the environmental range of 5.5
#: (outside the band around reference conditions that Table 2 covers) and the
#: level measured at reference conditions, in decibels.
ENVIRONMENTAL_LEVEL_ACCEPTANCE_LIMITS_DB: tuple[CalibratorTableRow, ...] = (
    _row(31.5, 160.0, "[)", (None, 0.25, None)),
    _row(160.0, 1250.0, "[]", (0.10, 0.25, 0.40)),
    _row(1250.0, 4000.0, "(]", (None, 0.30, None)),
    _row(4000.0, 8000.0, "(]", (None, 0.45, None)),
    _row(8000.0, 16000.0, "(]", (None, 0.60, None)),
)

#: IEC 60942:2017 Table 6 (folio 18): the acceptance limit on the absolute
#: difference between the frequency generated over the environmental range
#: of 5.5 and the frequency measured at reference conditions, in per cent of
#: the specified frequency, by class.
ENVIRONMENTAL_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT: Mapping[str, float] = (
    MappingProxyType({"LS": 0.7, "1": 0.7, "2": 1.7})
)

#: IEC 60942:2017 Table 7 (folio 19): the maximum total distortion + noise
#: (5.6), in per cent, over the applicable range of environmental conditions.
DISTORTION_ACCEPTANCE_LIMITS_PERCENT: tuple[CalibratorTableRow, ...] = (
    _row(31.5, 160.0, "[)", (None, 3.0, None)),
    _row(160.0, 1250.0, "[]", (2.0, 2.5, 3.0)),
    _row(1250.0, 16000.0, "(]", (None, 3.0, None)),
)

#: IEC 60942:2017 Table A.1 (folio 28), generated sound pressure level half:
#: the maximum-permitted expanded uncertainty for a coverage probability of
#: 95 %, in decibels, at and around reference environmental conditions.
LEVEL_MAX_UNCERTAINTY_DB: tuple[CalibratorTableRow, ...] = (
    _row(31.5, 63.0, "[]", (None, 0.20, None)),
    _row(63.0, 160.0, "()", (None, 0.20, None)),
    _row(160.0, 1250.0, "[]", (0.10, 0.15, 0.35)),
    _row(1250.0, 4000.0, "(]", (None, 0.25, None)),
    _row(4000.0, 8000.0, "(]", (None, 0.35, None)),
    _row(8000.0, 16000.0, "(]", (None, 0.50, None)),
)

#: IEC 60942:2017 Table A.1 (folio 28), short-term level fluctuation half: the
#: maximum-permitted expanded uncertainty for a coverage probability of 95 %,
#: in decibels.
FLUCTUATION_MAX_UNCERTAINTY_DB: tuple[CalibratorTableRow, ...] = (
    _row(31.5, 63.0, "[]", (None, 0.15, None)),
    _row(63.0, 160.0, "()", (None, 0.10, None)),
    _row(160.0, 1250.0, "[]", (0.02, 0.03, 0.05)),
    _row(1250.0, 4000.0, "(]", (None, 0.03, None)),
    _row(4000.0, 8000.0, "(]", (None, 0.03, None)),
    _row(8000.0, 16000.0, "(]", (None, 0.03, None)),
)

#: IEC 60942:2017 Table A.2 (folio 29): the maximum-permitted expanded
#: uncertainty of the frequency at and around reference conditions, for a
#: coverage probability of 95 %, in per cent of the specified frequency.
FREQUENCY_MAX_UNCERTAINTY_PERCENT: Mapping[str, float] = MappingProxyType(
    {"LS": 0.2, "1": 0.2, "2": 0.2}
)

#: IEC 60942:2017 Table A.3 (folio 30): the maximum-permitted expanded
#: uncertainty of the total distortion + noise, for a coverage probability of
#: 95 %, in percentage distortion.
DISTORTION_MAX_UNCERTAINTY_PERCENT: tuple[CalibratorTableRow, ...] = (
    _row(31.5, 160.0, "[)", (None, 1.0, None)),
    _row(160.0, 1250.0, "[]", (0.5, 0.5, 1.0)),
    _row(1250.0, 16000.0, "(]", (None, 1.0, None)),
)

#: IEC 60942:2017 Table A.4 (folio 32): the maximum-permitted expanded
#: uncertainty of the level difference over the environmental range, for a
#: coverage probability of 95 %, in decibels. It includes the uncertainty of
#: manufacturer-supplied corrections and excludes that of the measurement at
#: reference conditions (Table A.1).
ENVIRONMENTAL_LEVEL_MAX_UNCERTAINTY_DB: tuple[CalibratorTableRow, ...] = (
    _row(31.5, 160.0, "[)", (None, 0.25, None)),
    _row(160.0, 1250.0, "[]", (0.10, 0.15, 0.20)),
    _row(1250.0, 4000.0, "(]", (None, 0.30, None)),
    _row(4000.0, 8000.0, "(]", (None, 0.35, None)),
    _row(8000.0, 16000.0, "(]", (None, 0.40, None)),
)

#: IEC 60942:2017 Table A.5 (folio 35): the maximum-permitted expanded
#: uncertainty of the frequency over the environmental range, for a coverage
#: probability of 95 %, in per cent of the specified frequency.
ENVIRONMENTAL_FREQUENCY_MAX_UNCERTAINTY_PERCENT: Mapping[str, float] = MappingProxyType(
    {"LS": 0.2, "1": 0.2, "2": 0.2}
)

#: IEC 60942:2017 A.5.5.7 and A.5.5.8 (folios 26 and 27): the
#: maximum-permitted expanded uncertainty of the supply-voltage level
#: difference, for a coverage probability of 95 %, in decibels. The clauses
#: print it in the text, 0,02 dB for class LS and 0,04 dB for classes 1 and 2,
#: and note that it is included in Table A.1.
SUPPLY_VOLTAGE_MAX_UNCERTAINTY_DB: Mapping[str, float] = MappingProxyType(
    {"LS": 0.02, "1": 0.04, "2": 0.04}
)

#: IEC 60942:2017 5.9.4.2 (folio 21): the acceptance limit on the absolute
#: difference between the level generated in the presence of a power- or
#: radio-frequency field and in its absence, in decibels, by class.
FIELD_IMMUNITY_ACCEPTANCE_LIMITS_DB: Mapping[str, float] = MappingProxyType(
    {"LS": 0.10, "1": 0.25, "2": 0.45}
)

#: IEC 60942:2017 A.7.4.8 and A.7.4.10 (folios 40 and 41): the
#: maximum-permitted expanded uncertainty of that level difference, for a
#: coverage probability of 95 %, in decibels: 0,05 dB for every class, the
#: measurement of the field itself excluded.
FIELD_IMMUNITY_MAX_UNCERTAINTY_DB: Mapping[str, float] = MappingProxyType(
    {"LS": 0.05, "1": 0.05, "2": 0.05}
)

#: IEC 60942:2017 A.6.4.7 (folio 34): how much the abbreviated combined
#: temperature and humidity test reduces the Table 5 level limits, in
#: decibels, by class.
ABBREVIATED_LEVEL_REDUCTIONS_DB: Mapping[str, float] = MappingProxyType(
    {"LS": 0.05, "1": 0.05, "2": 0.10}
)

#: IEC 60942:2017 A.6.4.7 (folio 34): the reduced frequency acceptance limits
#: of the abbreviated combined temperature and humidity test, in per cent of
#: the specified frequency, by class.
ABBREVIATED_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT: Mapping[str, float] = MappingProxyType(
    {"LS": 0.5, "1": 0.5, "2": 1.3}
)

#: The two environmental tests A.6 allows.
_ENVIRONMENTAL_TESTS: tuple[str, ...] = ("full", "abbreviated")


def _base_class(calibrator_class: str) -> str:
    """The class a designation reads its limits from: ``"1/M"`` is class 1.

    :raises ValueError: for a designation Table 1 does not list.
    """
    designation = _designation(calibrator_class)
    return designation.split("/", 1)[0]


def _designation(calibrator_class: str | int) -> str:
    """Normalise a class designation, accepting ``1``, ``"1"`` and ``"ls/m"``.

    :raises ValueError: for a designation Table 1 does not list.
    """
    designation = str(calibrator_class).strip().upper()
    if designation not in CALIBRATOR_CLASSES:
        msg = (
            f"'calibrator_class' must be one of {', '.join(CALIBRATOR_CLASSES)} "
            f"(IEC 60942:2017 Table 1); got {calibrator_class!r}."
        )
        raise ValueError(msg)
    return designation


def _banded(
    table: tuple[CalibratorTableRow, ...], base: str, nominal_frequency_hz: float
) -> float | None:
    """The figure a banded table prints for a class at a nominal frequency."""
    for row in table:
        if row.contains(nominal_frequency_hz):
            return row.for_class(base)
    return None


def _fluctuation_limit_db(nominal_frequency_hz: float, calibrator_class: str) -> float:
    """The Table 2 fluctuation limit, or the strictest of its column outside it.

    :func:`phonometry.metrology.sensitivity` screens a *recording* with this,
    which may be at a frequency the calibrator's class has no limit at, so a
    dash falls back to the strictest figure the class prints anywhere, rather
    than to none: 0,03 dB for LS, 0,07 dB for class 1 and 0,15 dB for class 2.
    """
    base = _base_class(calibrator_class)
    limit = _banded(FLUCTUATION_ACCEPTANCE_LIMITS_DB, base, nominal_frequency_hz)
    if limit is not None:
        return limit
    column = [row.for_class(base) for row in FLUCTUATION_ACCEPTANCE_LIMITS_DB]
    return min(value for value in column if value is not None)


# ---------------------------------------------------------------------------
# The measurement record
# ---------------------------------------------------------------------------

#: Each requirement's deviation field and uncertainty field in the record.
_FIELDS: dict[str, tuple[str, str]] = {
    "level": ("level_deviation_db", "level_uncertainty_db"),
    "fluctuation": ("fluctuation_db", "fluctuation_uncertainty_db"),
    "frequency": ("frequency_deviation_percent", "frequency_uncertainty_percent"),
    "distortion": ("distortion_percent", "distortion_uncertainty_percent"),
    "supply_voltage": (
        "supply_voltage_deviation_db",
        "supply_voltage_uncertainty_db",
    ),
    "environmental_level": (
        "environmental_level_deviation_db",
        "environmental_level_uncertainty_db",
    ),
    "environmental_frequency": (
        "environmental_frequency_deviation_percent",
        "environmental_frequency_uncertainty_percent",
    ),
    "field_immunity": (
        "field_immunity_deviation_db",
        "field_immunity_uncertainty_db",
    ),
}

#: Requirements whose measured value is a magnitude and cannot be negative.
_MAGNITUDES = frozenset({"fluctuation", "distortion"})

#: The two requirements the abbreviated test of A.6.4 judges with its own limits.
_ENVIRONMENTAL_REQUIREMENTS = frozenset(
    {"environmental_level", "environmental_frequency"}
)


def _frozen(record: object, name: str) -> tuple[float, ...] | None:
    """A field of the record as the tuple its ``__post_init__`` made of it."""
    return cast("tuple[float, ...] | None", getattr(record, name))


def _values(value: float | Sequence[float], name: str) -> tuple[float, ...]:
    """One number or a 1-D sequence of them, as a tuple of finite floats.

    :raises ValueError: for an empty, multi-dimensional or non-finite input.
    """
    array = np.asarray(value, dtype=np.float64)
    if array.ndim > 1 or array.size == 0:
        msg = f"'{name}' must be one number or a flat sequence of numbers."
        raise ValueError(msg)
    if not np.all(np.isfinite(array)):
        msg = f"'{name}' must be finite."
        raise ValueError(msg)
    return tuple(float(v) for v in np.atleast_1d(array))


@dataclass(frozen=True)
class SoundCalibratorMeasurements:
    """What a laboratory measured on a sound calibrator, for IEC 60942:2017.

    Each requirement is a pair of fields, the measured deviation and the
    actual expanded uncertainty of its measurement for a coverage probability
    of 95 %, and each pair is given or left out together. A field takes one
    number or a sequence of them, one per measurement condition (the supply
    voltages of A.5.5.6 to A.5.5.8, the static pressures, temperatures and
    humidities of A.6, the settings of a multi-level calibrator at one
    frequency); an uncertainty given as one number applies to all of them.

    :ivar level_deviation_db: Measured minus specified sound pressure level
        (5.3.2), each the mean of at least three couplings (A.5.5.3,
        B.4.6.3.1), in decibels. For an /M pistonphone, as measured: the
        correction below is added to it.
    :ivar level_uncertainty_db: Its expanded uncertainty, in decibels.
    :ivar static_pressure_correction_db: The manufacturer's correction to the
        reference static pressure for a class LS/M or 1/M pistonphone
        (5.1.5, B.4.3.2), in decibels, added to ``level_deviation_db``.
        Required for those designations whenever the level is given (``0.0``
        at the reference pressure) and refused for every other (5.1.7).
    :ivar fluctuation_db: The short-term level fluctuation (5.3.3): the larger
        of the absolute differences between the maximum and the minimum
        F-weighted level and their mean over 60 s, in decibels.
    :ivar fluctuation_uncertainty_db: Its expanded uncertainty, in decibels.
    :ivar frequency_deviation_percent: Measured minus specified frequency, in
        per cent of the specified frequency (5.4.2).
    :ivar frequency_uncertainty_percent: Its expanded uncertainty, in per cent
        of the specified frequency.
    :ivar distortion_percent: The total distortion + noise over 22,4 Hz to
        22,4 kHz (5.6), in per cent.
    :ivar distortion_uncertainty_percent: Its expanded uncertainty, in per
        cent distortion.
    :ivar supply_voltage_deviation_db: The level at a supply voltage at an end
        of the permitted range minus the level at the nominal voltage (5.3.4),
        in decibels.
    :ivar supply_voltage_uncertainty_db: Its expanded uncertainty, in decibels.
    :ivar environmental_level_deviation_db: The level at an environmental
        condition outside the band of 5.3.2 minus the level at reference
        conditions (5.5), in decibels; for an /M pistonphone already
        corrected for static pressure, one correction per condition (A.6.2.3).
    :ivar environmental_level_uncertainty_db: Its expanded uncertainty, in
        decibels.
    :ivar environmental_frequency_deviation_percent: The frequency at such a
        condition minus the frequency at reference conditions, in per cent of
        the specified frequency (5.5).
    :ivar environmental_frequency_uncertainty_percent: Its expanded
        uncertainty, in per cent of the specified frequency.
    :ivar field_immunity_deviation_db: The level in a power- or
        radio-frequency field minus the level without it (5.9.4.2), in
        decibels.
    :ivar field_immunity_uncertainty_db: Its expanded uncertainty, in
        decibels, the field measurement excluded (A.7.4.8).
    """

    level_deviation_db: float | Sequence[float] | None = None
    level_uncertainty_db: float | Sequence[float] | None = None
    static_pressure_correction_db: float | Sequence[float] | None = None
    fluctuation_db: float | Sequence[float] | None = None
    fluctuation_uncertainty_db: float | Sequence[float] | None = None
    frequency_deviation_percent: float | Sequence[float] | None = None
    frequency_uncertainty_percent: float | Sequence[float] | None = None
    distortion_percent: float | Sequence[float] | None = None
    distortion_uncertainty_percent: float | Sequence[float] | None = None
    supply_voltage_deviation_db: float | Sequence[float] | None = None
    supply_voltage_uncertainty_db: float | Sequence[float] | None = None
    environmental_level_deviation_db: float | Sequence[float] | None = None
    environmental_level_uncertainty_db: float | Sequence[float] | None = None
    environmental_frequency_deviation_percent: float | Sequence[float] | None = None
    environmental_frequency_uncertainty_percent: float | Sequence[float] | None = None
    field_immunity_deviation_db: float | Sequence[float] | None = None
    field_immunity_uncertainty_db: float | Sequence[float] | None = None

    def __post_init__(self) -> None:
        """Freeze every field into a tuple and check that the pairs match.

        :raises ValueError: for a deviation without its uncertainty or the
            other way round, a non-finite or negative-where-impossible value,
            an uncertainty that is negative, a sequence of uncertainties whose
            length does not match its deviations, or a static-pressure
            correction without a level.
        """
        for field in fields(self):
            value = getattr(self, field.name)
            if value is not None:
                object.__setattr__(self, field.name, _values(value, field.name))
        for requirement, (deviation, uncertainty) in _FIELDS.items():
            self._check_pair(requirement, deviation, uncertainty)
        correction = _frozen(self, "static_pressure_correction_db")
        if correction is not None:
            level = _frozen(self, "level_deviation_db")
            if level is None:
                msg = (
                    "'static_pressure_correction_db' corrects the measured level "
                    "and needs 'level_deviation_db'."
                )
                raise ValueError(msg)
            _broadcast(level, correction, "static_pressure_correction_db")

    def _check_pair(self, requirement: str, deviation: str, uncertainty: str) -> None:
        """Validate one requirement's deviation and uncertainty fields."""
        values = _frozen(self, deviation)
        spread = _frozen(self, uncertainty)
        if (values is None) != (spread is None):
            given, missing = (
                (deviation, uncertainty) if spread is None else (uncertainty, deviation)
            )
            msg = (
                f"'{given}' needs '{missing}': IEC 60942:2017 grades a "
                f"measurement only with the uncertainty it was made with (5.1.15)."
            )
            raise ValueError(msg)
        if values is None or spread is None:
            return
        if requirement in _MAGNITUDES and min(values) < 0.0:
            msg = f"'{deviation}' is a magnitude and must be non-negative."
            raise ValueError(msg)
        if min(spread) < 0.0:
            msg = f"'{uncertainty}' must be non-negative."
            raise ValueError(msg)
        _broadcast(values, spread, uncertainty)

    def pairs(self, requirement: str) -> tuple[tuple[float, float], ...]:
        """The ``(deviation, uncertainty)`` pairs measured for a requirement.

        :param requirement: One of :data:`CALIBRATOR_REQUIREMENTS`.
        :return: One pair per measurement, empty when it was not measured.
        :raises ValueError: for an unknown requirement.
        """
        name = require_choice(requirement, "requirement", CALIBRATOR_REQUIREMENTS)
        deviation, uncertainty = _FIELDS[name]
        values = _frozen(self, deviation)
        spread = _frozen(self, uncertainty)
        if values is None or spread is None:
            return ()
        return tuple(zip(values, _broadcast(values, spread, uncertainty), strict=True))


def _broadcast(
    values: tuple[float, ...], other: tuple[float, ...], name: str
) -> tuple[float, ...]:
    """``other`` repeated to the length of ``values`` when it is one number.

    :raises ValueError: when it is a sequence of another length.
    """
    if len(other) == 1:
        return other * len(values)
    if len(other) != len(values):
        msg = (
            f"'{name}' must be one number or one per measurement "
            f"({len(values)}); got {len(other)}."
        )
        raise ValueError(msg)
    return other


# ---------------------------------------------------------------------------
# The verdicts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SoundCalibratorRequirement:
    """One requirement of IEC 60942:2017, judged on every measurement of it.

    :ivar name: The requirement, one of :data:`CALIBRATOR_REQUIREMENTS`.
    :ivar clause: The subclause of IEC 60942:2017 that states it.
    :ivar tables: Where its acceptance limit and maximum-permitted uncertainty
        are printed.
    :ivar verifications: One :class:`ConformanceVerification` per measurement,
        in the order they were given.
    """

    name: str
    clause: str
    tables: str
    verifications: tuple[ConformanceVerification, ...]

    @property
    def passes(self) -> bool:
        """Whether every measurement of the requirement demonstrates conformance."""
        return bool(self.verifications) and all(v.passes for v in self.verifications)

    @property
    def unit(self) -> str:
        """The unit the requirement is measured in, ``"dB"`` or ``"%"``."""
        return self.verifications[0].unit

    @property
    def acceptance_limits(self) -> tuple[float, float]:
        """The ``(lower, upper)`` acceptance limits, the same for every measurement."""
        first = self.verifications[0]
        return first.lower_limit, first.upper_limit

    @property
    def max_uncertainty(self) -> float:
        """The maximum-permitted expanded uncertainty for the requirement."""
        return self.verifications[0].max_uncertainty

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a SoundCalibratorRequirement has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw each measurement against the requirement's limits, as Figure E.1.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.metrology.plot_sound_calibrator_requirement`.
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_sound_calibrator_requirement

        check_language(language)
        return plot_sound_calibrator_requirement(self, ax, language=language, **kwargs)


@dataclass(frozen=True)
class SoundCalibratorVerification:
    """The IEC 60942:2017 verdict on one setting of a sound calibrator.

    :ivar calibrator_class: The designation it was judged as, one of
        :data:`CALIBRATOR_CLASSES`.
    :ivar nominal_frequency_hz: The nominal frequency of the setting, in
        hertz, which selects the rows of the banded tables.
    :ivar environmental_test: ``"full"`` (Tables 5 and 6) or
        ``"abbreviated"`` (the reduced limits of A.6.4.7).
    :ivar measurements: The record the verdict was reached on.
    :ivar requirements: One :class:`SoundCalibratorRequirement` per
        requirement measured, in the order of :data:`CALIBRATOR_REQUIREMENTS`.
    """

    calibrator_class: str
    nominal_frequency_hz: float
    environmental_test: str
    measurements: SoundCalibratorMeasurements
    requirements: tuple[SoundCalibratorRequirement, ...]

    @property
    def passes(self) -> bool:
        """Whether every requirement measured demonstrates conformance.

        ``False`` when nothing was measured: a record with no measurement in it
        qualifies nothing. With ``environmental_test="abbreviated"`` a failed
        environmental requirement means the full tests of A.6.5 to A.6.7 are
        due (A.6.1.2), not that the calibrator does not conform.
        """
        return bool(self.requirements) and all(r.passes for r in self.requirements)

    @property
    def failed(self) -> tuple[str, ...]:
        """The names of the requirements that do not pass."""
        return tuple(r.name for r in self.requirements if not r.passes)

    def requirement(self, name: str) -> SoundCalibratorRequirement:
        """The verdict on one requirement.

        :param name: One of :data:`CALIBRATOR_REQUIREMENTS`.
        :return: Its :class:`SoundCalibratorRequirement`.
        :raises KeyError: when that requirement was not measured.
        """
        for requirement in self.requirements:
            if requirement.name == name:
                return requirement
        msg = f"'{name}' was not measured; measured: {[r.name for r in self.requirements]}"
        raise KeyError(msg)

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a SoundCalibratorVerification has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw how much of each allowance every measurement uses.

        One pair of bars per measurement: the deviation as a share of its
        acceptance limit and the uncertainty as a share of its maximum. A
        requirement conforms when both of its bars stop at or before 100 %.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to
            :func:`phonometry._plot.metrology.plot_sound_calibrator_verification`.
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_sound_calibrator_verification

        check_language(language)
        return plot_sound_calibrator_verification(self, ax, language=language, **kwargs)


@dataclass(frozen=True)
class _Rule:
    """How one requirement reads its limits: clause, tables, unit and sign."""

    clause: str
    tables: str
    unit: str
    magnitude: bool


_RULES: dict[str, _Rule] = {
    "level": _Rule("5.3.2", "Table 2, Table A.1", "dB", magnitude=False),
    "fluctuation": _Rule("5.3.3", "Table 2, Table A.1", "dB", magnitude=True),
    "frequency": _Rule("5.4.2", "Table 4, Table A.2", "%", magnitude=False),
    "distortion": _Rule("5.6", "Table 7, Table A.3", "%", magnitude=True),
    "supply_voltage": _Rule("5.3.4", "Table 3, A.5.5.7", "dB", magnitude=False),
    "environmental_level": _Rule("5.5", "Table 5, Table A.4", "dB", magnitude=False),
    "environmental_frequency": _Rule("5.5", "Table 6, Table A.5", "%", magnitude=False),
    "field_immunity": _Rule("5.9.4.2", "5.9.4.2, A.7.4.8", "dB", magnitude=False),
}


def _limits(
    requirement: str, base: str, nominal_frequency_hz: float, environmental_test: str
) -> tuple[float, float]:
    """The acceptance limit and the maximum uncertainty of one requirement."""
    f = nominal_frequency_hz
    abbreviated = environmental_test == "abbreviated"
    banded: dict[
        str, tuple[tuple[CalibratorTableRow, ...], tuple[CalibratorTableRow, ...]]
    ] = {
        "level": (LEVEL_ACCEPTANCE_LIMITS_DB, LEVEL_MAX_UNCERTAINTY_DB),
        "fluctuation": (
            FLUCTUATION_ACCEPTANCE_LIMITS_DB,
            FLUCTUATION_MAX_UNCERTAINTY_DB,
        ),
        "distortion": (
            DISTORTION_ACCEPTANCE_LIMITS_PERCENT,
            DISTORTION_MAX_UNCERTAINTY_PERCENT,
        ),
    }
    if requirement in banded:
        acceptance_table, uncertainty_table = banded[requirement]
        limit = _banded(acceptance_table, base, f)
        maximum = _banded(uncertainty_table, base, f)
    elif requirement == "environmental_level":
        limit = _banded(ENVIRONMENTAL_LEVEL_ACCEPTANCE_LIMITS_DB, base, f)
        if limit is not None and abbreviated:
            limit -= ABBREVIATED_LEVEL_REDUCTIONS_DB[base]
        maximum = _banded(ENVIRONMENTAL_LEVEL_MAX_UNCERTAINTY_DB, base, f)
    else:
        by_class: dict[str, tuple[Mapping[str, float], Mapping[str, float]]] = {
            "frequency": (
                FREQUENCY_ACCEPTANCE_LIMITS_PERCENT,
                FREQUENCY_MAX_UNCERTAINTY_PERCENT,
            ),
            "supply_voltage": (
                SUPPLY_VOLTAGE_ACCEPTANCE_LIMITS_DB,
                SUPPLY_VOLTAGE_MAX_UNCERTAINTY_DB,
            ),
            "environmental_frequency": (
                ABBREVIATED_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT
                if abbreviated
                else ENVIRONMENTAL_FREQUENCY_ACCEPTANCE_LIMITS_PERCENT,
                ENVIRONMENTAL_FREQUENCY_MAX_UNCERTAINTY_PERCENT,
            ),
            "field_immunity": (
                FIELD_IMMUNITY_ACCEPTANCE_LIMITS_DB,
                FIELD_IMMUNITY_MAX_UNCERTAINTY_DB,
            ),
        }
        acceptance, uncertainty = by_class[requirement]
        limit, maximum = acceptance[base], uncertainty[base]
    if limit is None or maximum is None:
        # Unreachable once the nominal frequency has been checked against
        # Table 2, whose class columns span the same ranges as every other
        # banded table; kept so a future table cannot be read past its dash.
        msg = (
            f"IEC 60942:2017 gives class {base} no '{requirement}' limit at "
            f"{f:g} Hz (5.1.2)."
        )
        raise ValueError(msg)
    return limit, maximum


def verify_sound_calibrator(
    calibrator_class: str,
    measurements: SoundCalibratorMeasurements,
    *,
    nominal_frequency_hz: float,
    environmental_test: str = "full",
) -> SoundCalibratorVerification:
    """Verify what a laboratory measured on a sound calibrator against IEC 60942:2017.

    Every requirement given in ``measurements`` is judged by the conformance
    rule of IEC TC 29 (5.1.15, :func:`phonometry.metrology.verify_conformance`)
    against the acceptance limit and the maximum-permitted uncertainty that
    the class and the nominal frequency select, and the calibrator passes when
    every measurement of every requirement does. The requirements, their
    clauses and tables are listed in the module documentation of
    :mod:`phonometry.metrology.sound_calibrator`.

    One call judges one setting: a multi-frequency calibrator is verified once
    per frequency setting, because the banded tables change with it. For an
    LS/M or 1/M pistonphone the level is graded after the manufacturer's
    static-pressure correction is added to it (5.3.2, B.4.3.2).

    :param calibrator_class: ``"LS"``, ``"LS/M"``, ``"1"``, ``"1/M"`` or
        ``"2"`` (Table 1); ``1`` and ``2`` may be given as integers.
    :param measurements: What was measured, as
        :class:`SoundCalibratorMeasurements`.
    :param nominal_frequency_hz: The nominal frequency of the setting, in
        hertz. It has to be one the class has acceptance limits at: 31,5 Hz to
        16 kHz for class 1, 160 Hz to 1 250 Hz for classes LS and 2 (5.1.2).
    :param environmental_test: ``"full"`` (default) judges the environmental
        requirements against Tables 5 and 6; ``"abbreviated"`` against the
        reduced limits of A.6.4.7, where a failure calls for the full tests
        rather than a non-conformance (A.6.1.2).
    :return: The :class:`SoundCalibratorVerification`, whose ``passes`` is the
        verdict and whose ``requirements`` carry one verdict each.
    :raises ValueError: for an unknown class or environmental test, a nominal
        frequency the class has no acceptance limit at, a static-pressure
        correction given for a class that is not an /M pistonphone, or one
        missing for an /M pistonphone whose level is given.
    """
    designation = _designation(calibrator_class)
    base = designation.split("/", 1)[0]
    f = require_positive(float(nominal_frequency_hz), "nominal_frequency_hz")
    test = require_choice(
        str(environmental_test), "environmental_test", _ENVIRONMENTAL_TESTS
    )
    if _banded(LEVEL_ACCEPTANCE_LIMITS_DB, base, f) is None:
        span = "31.5 Hz to 16 kHz" if base == "1" else "160 Hz to 1250 Hz"
        msg = (
            f"IEC 60942:2017 gives class {base} acceptance limits from {span} "
            f"only, and conformance shall not be stated at {f:g} Hz (5.1.2)."
        )
        raise ValueError(msg)
    corrections = _corrections(designation, measurements)

    requirements: list[SoundCalibratorRequirement] = []
    for name in CALIBRATOR_REQUIREMENTS:
        pairs = measurements.pairs(name)
        if not pairs:
            continue
        rule = _RULES[name]
        limit, maximum = _limits(name, base, f, test)
        bounds = (0.0, limit) if rule.magnitude else limit
        shifts = corrections if name == "level" else (0.0,) * len(pairs)
        verifications = tuple(
            verify_conformance(
                deviation + shift,
                uncertainty=uncertainty,
                acceptance_limits=bounds,
                max_uncertainty=maximum,
                unit=rule.unit,
            )
            for (deviation, uncertainty), shift in zip(pairs, shifts, strict=True)
        )
        clause = (
            "A.6.4.7"
            if test == "abbreviated" and name in _ENVIRONMENTAL_REQUIREMENTS
            else rule.clause
        )
        requirements.append(
            SoundCalibratorRequirement(name, clause, rule.tables, verifications)
        )
    return SoundCalibratorVerification(
        calibrator_class=designation,
        nominal_frequency_hz=f,
        environmental_test=test,
        measurements=measurements,
        requirements=tuple(requirements),
    )


def _corrections(
    designation: str, measurements: SoundCalibratorMeasurements
) -> tuple[float, ...]:
    """The static-pressure correction to add to each measured level.

    :raises ValueError: for a correction on a calibrator that is not an /M
        pistonphone, or none on one that is.
    """
    level = measurements.pairs("level")
    given = _frozen(measurements, "static_pressure_correction_db")
    pistonphone = designation.endswith("/M")
    if given is not None and not pistonphone:
        msg = (
            f"a class {designation} calibrator shall need no environmental "
            f"correction to meet its class (IEC 60942:2017 5.1.7); "
            f"'static_pressure_correction_db' is for LS/M and 1/M only."
        )
        raise ValueError(msg)
    if not level:
        return ()
    if given is None:
        if pistonphone:
            msg = (
                f"a class {designation} pistonphone's level is graded after the "
                f"manufacturer's static-pressure correction (5.3.2, B.4.3.2): "
                f"give 'static_pressure_correction_db', 0.0 at the reference "
                f"101.325 kPa."
            )
            raise ValueError(msg)
        return (0.0,) * len(level)
    return _broadcast(
        tuple(d for d, _ in level), given, "static_pressure_correction_db"
    )
