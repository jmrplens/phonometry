#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Periodic tests of a sound level meter (IEC 61672-3:2013): the verdict.

IEC 61672-3:2013 is the short list of tests a laboratory runs on a working
sound level meter every year or two, to show that it still meets the class it
was built to under IEC 61672-1:2013. The laboratory measures; this module
grades what it measured, clause by clause, and writes the statement Clause 22
prescribes for the outcome.

**The rule.** Every result is judged by the conformance rule of IEC TC 29
that 4.1 states (:func:`phonometry.metrology.verify_conformance`): the
measured deviation from the design goal within the acceptance limits **and**
the laboratory's actual expanded uncertainty, for a coverage probability of
95 %, within the maximum permitted by Table B.1 of IEC 61672-1, both limits
inclusive. A result whose uncertainty exceeds its maximum "shall not be used
to evaluate conformance" (4.3): it is neither a pass nor, by itself, a
failure of the meter, :attr:`SoundLevelMeterPeriodicVerification.unusable`
lists it and the verdict does not pass while it is there.

**The manufacturer's correction data (4.4).** The acoustical test of the
frequency weighting (Clause 12) and the electrical one (Clause 13, 13.7)
correct the indications with the manufacturer's free-field or
random-incidence correction data, whose uncertainty the laboratory's budget
carries. The laboratory's uncertainty without it "shall not exceed" the
maximum; when the total exceeds the maximum only because of it, "testing may
proceed", and the result is one that did not conform, with the reason the
NOTE to 22 t) gives in the statement. The record takes that uncertainty
beside the total,
:attr:`SoundLevelMeterPeriodicMeasurements.acoustic_weighting_uncertainties_without_correction_data_db`
and its Clause 13 twin, and a result it clears is listed under
:attr:`SoundLevelMeterPeriodicVerification.over_maximum_by_correction_data`
and :attr:`SoundLevelMeterPeriodicVerification.failed` rather than under
``unusable``. Without it the total is all the verdict knows, and 4.3 applies.

**What is graded**, with the acceptance limits of IEC 61672-1:2013 each clause
of IEC 61672-3 points to and the maximum of its Table B.1:

* ``acoustic_weighting`` (12): the relative frequency weighting at 125 Hz and
  8 kHz, relative to 1 kHz (12.7, 12.15), against Table 3, with 0,60 dB and
  0,70 dB;
* ``electrical_weighting`` (13): every frequency weighting the meter provides
  at the octave frequencies of 13.4 (63 Hz to 16 kHz for class 1, to 8 kHz for
  class 2), against Table 3, with 0,60 dB up to 4 kHz, 0,70 dB above it and
  1,00 dB above 10 kHz;
* ``weighting_at_1khz`` (14.2): C and Z against A at 1 kHz, 5.5.9, +/-0,2 dB,
  with 0,20 dB;
* ``time_weighting_at_1khz`` (14.3): S and time-averaged against F at 1 kHz,
  5.8.3, +/-0,1 dB, with 0,20 dB (the maximum uncertainty is larger than the
  acceptance limit, as the page prints them);
* ``long_term_stability`` (15): the final minus the initial indication over
  25 min to 35 min, 5.14.2, +/-0,1 dB (class 1) or +/-0,3 dB (class 2), with
  0,10 dB;
* ``level_linearity`` (16): the level linearity deviations at 8 kHz on the
  reference level range, 5.6.5, +/-0,8 dB or +/-1,1 dB, with 0,30 dB; and
  the absence of an overload or under-range indication within the linear
  operating range the instruction manual states (16.4; IEC 61672-1 5.6.10);
* ``range_linearity`` (17): the level linearity deviations including the
  level range control, the same limits;
* ``toneburst`` (18): the 4 kHz toneburst responses of 18.5 to 18.7 less the
  reference responses of Table 4, against its limits, with 0,30 dB;
* ``c_peak`` (19): :math:`L_\mathrm{Cpeak} - L_\mathrm{C}` for one cycle at
  8 kHz and the two half cycles at 500 Hz, less the reference differences of
  Table 5, against its limits, with 0,35 dB; and the absence of an overload
  indication while those signals are applied (19.3, 19.5);
* ``overload`` (20): the difference between the positive and the negative
  one-half-cycle input levels that first cause an overload indication,
  5.11.3, 1,5 dB either way, with 0,25 dB; and the latching of the indicator
  (20.5);
* ``high_level_stability`` (21): the final minus the initial indication over
  5 min near the top of the least-sensitive range, 5.15.2, +/-0,1 dB or
  +/-0,3 dB, with 0,10 dB.

**What is recorded, not graded.** The indications at the calibration check
frequency before and after adjustment (Clause 10) and the self-generated
noise (Clause 11), which "is reported for information only and is not used to
assess conformance to a requirement" and without an uncertainty (11.1.2,
NOTE 2). Both are still part of a complete test, so a record without them is
incomplete. The environmental conditions (Clause 7) are checked against the
ranges of 7.1, and a test outside them is not a valid periodic test: its
statement says so before anything its results would say.

**What a complete test covers.** 8.1 asks for every test of a design feature
IEC 61672-1 requires and the meter provides. A record shows a feature through
the results it holds, and :class:`SoundLevelMeterFeatures` declares the
optional ones the meter has or lacks, as its instruction manual states them;
the verdict holds the record to both: frequency weighting A always and C for
class 1 (5.1.9, 5.1.10), C as well for a meter that measures C-weighted peak
sound level, which "shall also be able to measure C-weighted time-averaged
sound levels" (5.1.10), and every weighting declared or named by a clause of
the record, tested in Clause 13, in the self-generated noise of 11.2 and, C
and Z, in 14.2. The displays are held to the same rule both ways: the F, S
and time-averaged displays are tested in the toneburst tests of Clause 18,
where 18.2 calculates the sound exposure level from the time-averaged one for
a meter that does not measure it, and a display another clause shows is
compared with F in 14.3: S for a meter whose S-time-weighted toneburst
response Clause 18 holds, time-averaged for a meter whose overload indication
Clause 20 holds, as 20.1 tests only a meter that displays time-averaged sound
level. Clause 20 in turn is required of a meter 14.3 shows to display
time-averaged sound level, Clause 17 of a meter with more than one level
range (17.1) and Clause 19 of one that measures C-weighted peak sound level.
A measured clause is held to the extent its procedure gives: the steps of
Clause 16 rise from the starting point in 5 dB steps until within 5 dB of
the upper boundary of the linear operating range and in 1 dB steps from
there up to the first overload indication, and fall the same way down to the
first under-range indication (16.3), so the record carries that range, the
starting point and the two indications; Clause 17 records 5 dB above the
first indication of under-range on every level range, the reference one
included (17.4), and the reference sound level held on every other one
(17.3), whose number the declared features give. A declared feature carries
what IEC 61672-1 makes of it: a meter without frequency weighting C measures
no C-weighted peak sound level (5.1.10), one without the F time weighting has
no S either (5.1.9), and one without F, a time-averaged display or sound
exposure level indicates nothing 5.1.9 asks of a sound level meter and is
refused.
:attr:`SoundLevelMeterPeriodicVerification.missing` names the clauses a
complete test lacks, :attr:`SoundLevelMeterPeriodicVerification.incomplete`
what a measured clause is short of,
:attr:`SoundLevelMeterPeriodicVerification.not_applicable` the clauses a
feature declared absent takes out, and
:attr:`SoundLevelMeterPeriodicVerification.undeclared` the features the
record neither shows nor declares, which a record that left their tests out
cannot be told from: the verdict does not pass while one is open.

**The tables.** The acceptance limits of Table 3 are read through
:func:`phonometry.filters.weighting_class_limits`, which already publishes
them. Table 4 (the reference toneburst responses), Table 5 (the reference
differences of the C-weighted peak) and Table B.1 (the maximum-permitted
uncertainties) are published here, read-only, as :data:`IEC61672_TABLE_4`,
:data:`IEC61672_TABLE_5` and :data:`IEC61672_TABLE_B1`.

**What a pass here is, and is not.** It is a verdict on the numbers put in:
the preliminary inspection (Clause 5), the power supply (Clause 6), the
calibrator's own conformance to IEC 60942 (Clause 9, which
:func:`phonometry.metrology.verify_sound_calibrator` grades), the general
test requirements of 8.2 to 8.5 (among them the confirmation of 8.4 that an
electrical output used for the tests reads as the display does) and the
source of the correction data (12.2 to 12.6) are the laboratory's record. And
even a
meter that passes every periodic test supports no general conclusion about the
specifications of IEC 61672-1 unless the model's pattern approval under
IEC 61672-2 is publicly available and the correction data for the acoustical
test came from the instruction manual (Clause 1; 22 r and s): the statement
the verdict writes is the one Clause 22 prescribes for the case at hand. Both
are the laboratory's to declare, as 22 c) and 12.5 have it state them, and
the verdict assumes neither: without both declared it writes 22 s).

Oracle: BS EN 61672-3:2013 (IEC 61672-3:2013) and BS EN 61672-1:2013
(IEC 61672-1:2013), PDF page = printed folio + 2 in both. Tables 3 (folio
22), 4 (25), 5 (28) and B.1 (42 and 43) of Part 1; the clauses of Part 3 on
folios 6 to 19.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.validation import is_class_designation, require_real
from .conformance import ConformanceVerification, verify_conformance

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from matplotlib.axes import Axes

__all__ = [
    "ACOUSTIC_TEST_FREQUENCIES_HZ",
    "ELECTRICAL_TEST_FREQUENCIES_HZ",
    "IEC61672_TABLE_4",
    "IEC61672_TABLE_5",
    "IEC61672_TABLE_B1",
    "PERIODIC_TEST_ENVIRONMENT",
    "SLM_PERIODIC_REQUIREMENTS",
    "TONEBURST_TEST_DURATIONS_MS",
    "MaxUncertaintyRow",
    "PeakReference",
    "SoundLevelMeterFeatures",
    "SoundLevelMeterPeriodicMeasurements",
    "SoundLevelMeterPeriodicRequirement",
    "SoundLevelMeterPeriodicVerification",
    "ToneburstReference",
    "verify_sound_level_meter_periodic",
]

#: The performance classes IEC 61672-1:2013 defines.
_CLASSES = (1, 2)


# ---------------------------------------------------------------------------
# The tables of IEC 61672-1:2013
# ---------------------------------------------------------------------------


def _limits_for(
    meter_class: int,
    class_1: tuple[float, float],
    class_2: tuple[float, float],
) -> tuple[float, float]:
    """The ``(lower, upper)`` limits of a row for a class, 1 or 2.

    :raises ValueError: for a class IEC 61672-1:2013 does not define.
    """
    if not is_class_designation(meter_class, _CLASSES):
        msg = f"'meter_class' must be 1 or 2 (IEC 61672-1:2013); got {meter_class!r}."
        raise ValueError(msg)
    return class_1 if int(meter_class) == 1 else class_2


@dataclass(frozen=True)
class ToneburstReference:
    r"""One row of IEC 61672-1:2013 Table 4, the reference 4 kHz toneburst response.

    :ivar duration_ms: The toneburst duration :math:`T_\mathrm{b}`, in
        milliseconds.
    :ivar reference_response_db: The reference response
        :math:`\delta_\mathrm{ref}` relative to the steady sound level, in
        decibels: Equation (7) rounded to a tenth for a maximum time-weighted
        level, Equation (8) for a sound exposure level.
    :ivar class_1_limits_db: The class 1 acceptance limits on the deviation
        from it, ``(lower, upper)``, in decibels.
    :ivar class_2_limits_db: The class 2 acceptance limits, in decibels.
    """

    duration_ms: float
    reference_response_db: float
    class_1_limits_db: tuple[float, float]
    class_2_limits_db: tuple[float, float]

    def limits_db(self, meter_class: int) -> tuple[float, float]:
        """The ``(lower, upper)`` acceptance limits for a class, in decibels.

        :param meter_class: 1 or 2.
        :return: The limits of that class's column.
        :raises ValueError: for another class.
        """
        return _limits_for(meter_class, self.class_1_limits_db, self.class_2_limits_db)


@dataclass(frozen=True)
class PeakReference:
    r"""One row of IEC 61672-1:2013 Table 5, the C-weighted peak reference difference.

    :ivar signal: The test signal: ``"one cycle"``, ``"positive half cycle"``
        or ``"negative half cycle"``.
    :ivar nominal_frequency_hz: The nominal frequency of the steady signal it
        is extracted from, in hertz (the test uses the exact frequency of
        Annex D, NOTE to Table 5).
    :ivar reference_difference_db: The reference difference
        :math:`L_\mathrm{Cpeak} - L_\mathrm{C}`, in decibels.
    :ivar class_1_limits_db: The class 1 acceptance limits on the deviation
        from it, ``(lower, upper)``, in decibels.
    :ivar class_2_limits_db: The class 2 acceptance limits, in decibels.
    """

    signal: str
    nominal_frequency_hz: float
    reference_difference_db: float
    class_1_limits_db: tuple[float, float]
    class_2_limits_db: tuple[float, float]

    def limits_db(self, meter_class: int) -> tuple[float, float]:
        """The ``(lower, upper)`` acceptance limits for a class, in decibels.

        :param meter_class: 1 or 2.
        :return: The limits of that class's column.
        :raises ValueError: for another class.
        """
        return _limits_for(meter_class, self.class_1_limits_db, self.class_2_limits_db)


@dataclass(frozen=True)
class MaxUncertaintyRow:
    """One row of IEC 61672-1:2013 Table B.1, a maximum-permitted uncertainty.

    :ivar requirement: The requirement, as the "Requirement" column prints it.
    :ivar reference: The "Table or subclause" column, as printed (decimal
        commas included).
    :ivar max_uncertainty: The maximum-permitted expanded uncertainty for a
        coverage probability of 95 %, in :attr:`unit`.
    :ivar unit: ``"dB"``, or ``"dB/s"`` for the two decay rates of 5.8.2,
        which the page prints in one cell ("3,50 dB/s for F; 0,40 dB/s for
        S") and this table in two rows.
    :ivar lower_hz: The lower end of the frequency range the row covers, in
        hertz, or ``None`` for a row that is not banded by frequency.
    :ivar upper_hz: The upper end, inclusive, in hertz, or ``None``.
    :ivar includes_lower: Whether :attr:`lower_hz` belongs to the row; the
        page writes the bands after the first as "> 1 kHz to 2 kHz".
    """

    requirement: str
    reference: str
    max_uncertainty: float
    unit: str = "dB"
    lower_hz: float | None = None
    upper_hz: float | None = None
    includes_lower: bool = True

    def contains(self, frequency_hz: float) -> bool:
        """Whether a nominal frequency falls in the row's band.

        A row that is not banded by frequency contains every frequency.

        :param frequency_hz: The nominal frequency, in hertz.
        :return: ``True`` inside the band, its included ends counted.
        """
        if self.lower_hz is None or self.upper_hz is None:
            return True
        f = float(frequency_hz)
        above = f >= self.lower_hz if self.includes_lower else f > self.lower_hz
        return above and f <= self.upper_hz


def _burst(
    duration_ms: float,
    reference_db: float,
    class_1: tuple[float, float],
    class_2: tuple[float, float],
) -> ToneburstReference:
    """One printed row of Table 4."""
    return ToneburstReference(duration_ms, reference_db, class_1, class_2)


#: The acceptance-limit columns of IEC 61672-1:2013 Table 4 shared by the
#: maximum F-weighted level and the sound exposure level, by duration (ms):
#: class 1 then class 2, each ``(lower, upper)``.
_F_AND_E_LIMITS_DB: dict[float, tuple[tuple[float, float], tuple[float, float]]] = {
    1000.0: ((-0.5, 0.5), (-1.0, 1.0)),
    500.0: ((-0.5, 0.5), (-1.0, 1.0)),
    200.0: ((-0.5, 0.5), (-1.0, 1.0)),
    100.0: ((-1.0, 1.0), (-1.0, 1.0)),
    50.0: ((-1.0, 1.0), (-1.5, 1.0)),
    20.0: ((-1.0, 1.0), (-2.0, 1.0)),
    10.0: ((-1.0, 1.0), (-2.0, 1.0)),
    5.0: ((-1.0, 1.0), (-2.5, 1.0)),
    2.0: ((-1.5, 1.0), (-2.5, 1.0)),
    1.0: ((-2.0, 1.0), (-3.0, 1.0)),
    0.5: ((-2.5, 1.0), (-4.0, 1.0)),
    0.25: ((-3.0, 1.0), (-5.0, 1.5)),
}

#: The reference responses of Table 4: maximum F-weighted level (Equation (7),
#: tau = 0,125 s) and sound exposure level (Equation (8)), by duration (ms).
_F_REFERENCES_DB = (
    0.0,
    -0.1,
    -1.0,
    -2.6,
    -4.8,
    -8.3,
    -11.1,
    -14.1,
    -18.0,
    -21.0,
    -24.0,
    -27.0,
)
_E_REFERENCES_DB = (
    0.0,
    -3.0,
    -7.0,
    -10.0,
    -13.0,
    -17.0,
    -20.0,
    -23.0,
    -27.0,
    -30.0,
    -33.0,
    -36.0,
)

#: IEC 61672-1:2013 Table 4 (folio 25): the reference 4 kHz toneburst
#: responses relative to the steady sound level and their acceptance limits,
#: keyed by the measurement: ``"F"`` for the maximum F-time-weighted level
#: (:math:`L_\mathrm{AFmax} - L_\mathrm{A}`, 12 rows from 1 s to
#: 0,25 ms), ``"S"`` for the maximum S-time-weighted level (9 rows from
#: 1 s to 2 ms, with limits of their own) and ``"E"`` for the sound
#: exposure level (:math:`L_\mathrm{AE} - L_\mathrm{A}`, the 12 durations of
#: F, whose limits it shares). The rows hold for the A, C and Z weightings
#: alike (NOTE 3).
IEC61672_TABLE_4: Mapping[str, tuple[ToneburstReference, ...]] = MappingProxyType(
    {
        "F": tuple(
            _burst(duration, reference, *_F_AND_E_LIMITS_DB[duration])
            for duration, reference in zip(
                _F_AND_E_LIMITS_DB, _F_REFERENCES_DB, strict=True
            )
        ),
        "S": (
            _burst(1000.0, -2.0, (-0.5, 0.5), (-1.0, 1.0)),
            _burst(500.0, -4.1, (-0.5, 0.5), (-1.0, 1.0)),
            _burst(200.0, -7.4, (-0.5, 0.5), (-1.0, 1.0)),
            _burst(100.0, -10.2, (-1.0, 1.0), (-1.0, 1.0)),
            _burst(50.0, -13.1, (-1.0, 1.0), (-1.5, 1.0)),
            _burst(20.0, -17.0, (-1.5, 1.0), (-2.0, 1.0)),
            _burst(10.0, -20.0, (-2.0, 1.0), (-3.0, 1.0)),
            _burst(5.0, -23.0, (-2.5, 1.0), (-4.0, 1.0)),
            _burst(2.0, -27.0, (-3.0, 1.0), (-5.0, 1.0)),
        ),
        "E": tuple(
            _burst(duration, reference, *_F_AND_E_LIMITS_DB[duration])
            for duration, reference in zip(
                _F_AND_E_LIMITS_DB, _E_REFERENCES_DB, strict=True
            )
        ),
    }
)

#: The complete-cycle signal of IEC 61672-1:2013 Table 5, named once for its
#: three rows.
_ONE_CYCLE = "one cycle"

#: IEC 61672-1:2013 Table 5 (folio 28): the reference differences between the
#: C-weighted peak sound level and the C-weighted level of the steady signal,
#: and their acceptance limits, in the printed order. The periodic test of
#: IEC 61672-3 19.1 uses the last three rows.
IEC61672_TABLE_5: tuple[PeakReference, ...] = (
    PeakReference(_ONE_CYCLE, 31.5, 2.5, (-2.0, 2.0), (-3.0, 3.0)),
    PeakReference(_ONE_CYCLE, 500.0, 3.5, (-1.0, 1.0), (-2.0, 2.0)),
    PeakReference(_ONE_CYCLE, 8000.0, 3.4, (-2.0, 2.0), (-3.0, 3.0)),
    PeakReference("positive half cycle", 500.0, 2.4, (-1.0, 1.0), (-2.0, 2.0)),
    PeakReference("negative half cycle", 500.0, 2.4, (-1.0, 1.0), (-2.0, 2.0)),
)


def _directional(angle: str, cells: tuple[float, ...]) -> tuple[MaxUncertaintyRow, ...]:
    """The five frequency bands of a directional-response row of Table B.1."""
    bands = (
        (250.0, 1000.0, True, "250 Hz to 1 kHz"),
        (1000.0, 2000.0, False, ">1 kHz to 2 kHz"),
        (2000.0, 4000.0, False, ">2 kHz to 4 kHz"),
        (4000.0, 8000.0, False, ">4 kHz to 8 kHz"),
        (8000.0, 12500.0, False, ">8 kHz to 12,5 kHz"),
    )
    return tuple(
        MaxUncertaintyRow(
            f"Directional response: θ = {angle}",
            f"Table 2; {text}",
            value,
            lower_hz=lower,
            upper_hz=upper,
            includes_lower=closed,
        )
        for (lower, upper, closed, text), value in zip(bands, cells, strict=True)
    )


#: The frequency-weighting requirement of Table B.1, named once for the grader.
_B1_WEIGHTING = "Frequency weightings A, C, Z"
#: The requirements of Table B.1 the grader reads by name. Three of them are
#: also, word for word, the headings of Clauses 18, 20 and 21 of Part 3.
_B1_LINEARITY = "Level linearity deviation"
_TONEBURST_RESPONSE = "Toneburst response"
_OVERLOAD_INDICATION = "Overload indication"
_HIGH_LEVEL_STABILITY = "High-level stability"

#: IEC 61672-1:2013 Table B.1 (folios 42 and 43): the maximum-permitted
#: uncertainties of measurement for a coverage probability of 95 %, for
#: pattern-evaluation and periodic tests, in the printed order. The one cell
#: that prints two figures, the F and S decay rates of 5.8.2, is two rows.
IEC61672_TABLE_B1: tuple[MaxUncertaintyRow, ...] = (
    *_directional("30°", (0.25, 0.25, 0.35, 0.45, 0.55)),
    *_directional("90° & 150°", (0.25, 0.45, 0.45, 0.85, 1.15)),
    MaxUncertaintyRow(
        _B1_WEIGHTING, "Table 3, 10 Hz to 4 kHz", 0.60, lower_hz=10.0, upper_hz=4000.0
    ),
    MaxUncertaintyRow(
        _B1_WEIGHTING,
        "Table 3, >4 kHz to 10 kHz",
        0.70,
        lower_hz=4000.0,
        upper_hz=10000.0,
        includes_lower=False,
    ),
    MaxUncertaintyRow(
        _B1_WEIGHTING,
        "Table 3, >10 kHz to 20 kHz",
        1.00,
        lower_hz=10000.0,
        upper_hz=20000.0,
        includes_lower=False,
    ),
    MaxUncertaintyRow("A vs. C or Z at 1 kHz", "5.5.9", 0.20),
    MaxUncertaintyRow(_B1_LINEARITY, "5.6.5", 0.30),
    MaxUncertaintyRow("1 dB to 10 dB change in level", "5.6.6", 0.25),
    MaxUncertaintyRow("F and S decay rates", "5.8.2, F", 3.50, unit="dB/s"),
    MaxUncertaintyRow("F and S decay rates", "5.8.2, S", 0.40, unit="dB/s"),
    MaxUncertaintyRow("F vs. S level at 1 kHz", "5.8.3", 0.20),
    MaxUncertaintyRow(_TONEBURST_RESPONSE, "5.9.2, Table 4", 0.30),
    MaxUncertaintyRow("Repeated tonebursts", "5.10.1, Table 4", 0.30),
    MaxUncertaintyRow(_OVERLOAD_INDICATION, "5.11.3", 0.25),
    MaxUncertaintyRow("C-weighted peak sound levels", "5.13.3, Table 5", 0.35),
    MaxUncertaintyRow("Stability during continuous operation", "5.14.2", 0.10),
    MaxUncertaintyRow(_HIGH_LEVEL_STABILITY, "5.15.2", 0.10),
    MaxUncertaintyRow("Analogue electrical output", "5.19.2", 0.15),
    MaxUncertaintyRow("Power supply voltage", "5.23.2", 0.20),
    MaxUncertaintyRow("Static pressure influence", "6.2.1; 6.2.2", 0.30),
    MaxUncertaintyRow("Air temperature influence", "6.3.3; 6.3.4", 0.30),
    MaxUncertaintyRow("Humidity influence", "6.4", 0.30),
    MaxUncertaintyRow("Combined temperature and humidity", "6.3.3, 6.3.4, 6.4", 0.35),
    MaxUncertaintyRow("AC and radio-frequency fields", "6.6.6", 0.30),
)


# ---------------------------------------------------------------------------
# What IEC 61672-3:2013 tests
# ---------------------------------------------------------------------------

#: IEC 61672-3:2013 12.7: the frequencies at which the acoustical test
#: determines the frequency weighting relative to its response at 1 kHz, in
#: hertz.
ACOUSTIC_TEST_FREQUENCIES_HZ: tuple[float, ...] = (125.0, 8000.0)

#: IEC 61672-3:2013 13.4: the nominal test frequencies of the electrical
#: tests of the frequency weightings, in hertz, by class: the nine octaves
#: from 63 Hz to 16 kHz for class 1 and the eight to 8 kHz for class 2.
ELECTRICAL_TEST_FREQUENCIES_HZ: Mapping[int, tuple[float, ...]] = MappingProxyType(
    {
        1: (63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0, 16000.0),
        2: (63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0),
    }
)

#: IEC 61672-3:2013 18.5 to 18.7: the toneburst durations each measurement is
#: tested at, in milliseconds: 200 ms, 2 ms and 0,25 ms for the maximum
#: F-weighted level and the sound exposure level, 200 ms and 2 ms for the
#: maximum S-weighted level.
TONEBURST_TEST_DURATIONS_MS: Mapping[str, tuple[float, ...]] = MappingProxyType(
    {"F": (200.0, 2.0, 0.25), "S": (200.0, 2.0), "E": (200.0, 2.0, 0.25)}
)

#: IEC 61672-3:2013 7.1: the ranges of environmental conditions periodic tests
#: are performed in, each ``(lower, upper)`` inclusive, keyed by the field of
#: :class:`SoundLevelMeterPeriodicMeasurements` that records it.
PERIODIC_TEST_ENVIRONMENT: Mapping[str, tuple[float, float]] = MappingProxyType(
    {
        "static_pressures_kpa": (80.0, 105.0),
        "air_temperatures_c": (20.0, 26.0),
        "relative_humidities_percent": (25.0, 70.0),
    }
)

#: The requirements :func:`verify_sound_level_meter_periodic` grades, in the
#: order of IEC 61672-3:2013.
SLM_PERIODIC_REQUIREMENTS: tuple[str, ...] = (
    "acoustic_weighting",
    "electrical_weighting",
    "weighting_at_1khz",
    "time_weighting_at_1khz",
    "long_term_stability",
    "level_linearity",
    "range_linearity",
    "toneburst",
    "c_peak",
    "overload",
    "high_level_stability",
)

#: The clause of IEC 61672-3:2013 each requirement is tested in.
_CLAUSES: dict[str, str] = {
    "acoustic_weighting": "12",
    "electrical_weighting": "13",
    "weighting_at_1khz": "14.2",
    "time_weighting_at_1khz": "14.3",
    "long_term_stability": "15",
    "level_linearity": "16",
    "range_linearity": "17",
    "toneburst": "18",
    "c_peak": "19",
    "overload": "20",
    "high_level_stability": "21",
}

#: What each clause tests, as its heading in IEC 61672-3:2013 reads (14.2 and
#: 14.3 share the heading of Clause 14 and are told apart here). Clauses 7,
#: 10 and 11 are records, named for the statement.
_TITLES: dict[str, str] = {
    "7": "Environmental conditions",
    "10": "Indication at the calibration check frequency",
    "11": "Self-generated noise",
    "12": "Acoustical signal tests of a frequency weighting",
    "13": "Electrical signal tests of frequency weightings",
    "14.2": "Frequency weightings at 1 kHz",
    "14.3": "Time weightings at 1 kHz",
    "15": "Long-term stability",
    "16": "Level linearity on the reference level range",
    "17": "Level linearity including the level range control",
    "18": _TONEBURST_RESPONSE,
    "19": "C-weighted peak sound level",
    "20": _OVERLOAD_INDICATION,
    "21": _HIGH_LEVEL_STABILITY,
}

#: Where each requirement's acceptance limits and maximum uncertainty are
#: printed in IEC 61672-1:2013.
_TABLES: dict[str, str] = {
    "acoustic_weighting": "Table 3, Table B.1",
    "electrical_weighting": "Table 3, Table B.1",
    "weighting_at_1khz": "5.5.9, Table B.1",
    "time_weighting_at_1khz": "5.8.3, Table B.1",
    "long_term_stability": "5.14.2, Table B.1",
    "level_linearity": "5.6.5, Table B.1",
    "range_linearity": "5.6.5, Table B.1",
    "toneburst": "Table 4, Table B.1",
    "c_peak": "Table 5, Table B.1",
    "overload": "5.11.3, Table B.1",
    "high_level_stability": "5.15.2, Table B.1",
}

#: The requirement of Table B.1 that sets each requirement's maximum.
_B1_ROWS: dict[str, str] = {
    "acoustic_weighting": _B1_WEIGHTING,
    "electrical_weighting": _B1_WEIGHTING,
    "weighting_at_1khz": "A vs. C or Z at 1 kHz",
    "time_weighting_at_1khz": "F vs. S level at 1 kHz",
    "long_term_stability": "Stability during continuous operation",
    "level_linearity": _B1_LINEARITY,
    "range_linearity": _B1_LINEARITY,
    "toneburst": _TONEBURST_RESPONSE,
    "c_peak": "C-weighted peak sound levels",
    "overload": _OVERLOAD_INDICATION,
    "high_level_stability": _HIGH_LEVEL_STABILITY,
}

#: The reason 22 t) gives for a requirement whose deviation exceeds its limits,
#: in the words of its NOTE where it prints one.
_REASONS: dict[str, str] = {
    "acoustic_weighting": (
        "measured deviations from the design-goal frequency weighting exceeded "
        "the applicable acceptance limits"
    ),
    "electrical_weighting": (
        "measured deviations from the design-goal frequency weighting exceeded "
        "the applicable acceptance limits"
    ),
    "weighting_at_1khz": (
        "the measured difference from the A-weighted indication exceeded the "
        "applicable acceptance limits"
    ),
    "time_weighting_at_1khz": (
        "the measured difference from the F-time-weighted indication exceeded "
        "the applicable acceptance limits"
    ),
    "long_term_stability": (
        "the measured change of indication exceeded the applicable acceptance limits"
    ),
    "level_linearity": (
        "measured level linearity deviations exceeded the applicable acceptance limits"
    ),
    "range_linearity": (
        "measured level linearity deviations exceeded the applicable acceptance limits"
    ),
    "toneburst": (
        "measured deviations from the reference toneburst responses exceeded "
        "the applicable acceptance limits"
    ),
    "c_peak": (
        "measured deviations from the design goal for indications of "
        "C-weighted peak sound levels exceeded the applicable acceptance limits"
    ),
    "overload": (
        "the measured difference between the one-half-cycle input levels that "
        "first cause an overload indication exceeded the applicable acceptance "
        "limits"
    ),
    "high_level_stability": (
        "the measured change of indication exceeded the applicable acceptance limits"
    ),
}

#: IEC 61672-1:2013 5.5.9: C or Z against A at 1 kHz, +/- dB.
_WEIGHTING_AT_1KHZ_LIMIT_DB = 0.2

#: IEC 61672-1:2013 5.8.3: S or time-averaged against F at 1 kHz, +/- dB.
_TIME_WEIGHTING_AT_1KHZ_LIMIT_DB = 0.1

#: IEC 61672-1:2013 5.6.5: level linearity deviations, +/- dB, by class.
_LINEARITY_LIMITS_DB: dict[int, float] = {1: 0.8, 2: 1.1}

#: IEC 61672-1:2013 5.14.2 and 5.15.2: the change of indication over the
#: stability tests, +/- dB, by class.
_STABILITY_LIMITS_DB: dict[int, float] = {1: 0.1, 2: 0.3}

#: IEC 61672-1:2013 5.11.3: the difference between the one-half-cycle input
#: levels that first cause an overload indication, +/- dB.
_OVERLOAD_LIMIT_DB = 1.5

#: The rows of :data:`IEC61672_TABLE_5` IEC 61672-3:2013 19.1 tests, in the
#: order :attr:`SoundLevelMeterPeriodicMeasurements.c_peak_differences_db`
#: takes them: one cycle at 8 kHz, then the positive and the negative half
#: cycle at 500 Hz.
_C_PEAK_ROWS = (2, 3, 4)

#: The frequency weightings a sound level meter may provide (5.1.9, 5.1.10).
_WEIGHTINGS: tuple[str, ...] = ("A", "C", "Z")

#: The weightings 14.2 compares with A.
_WEIGHTINGS_VS_A: tuple[str, ...] = ("C", "Z")

#: The displays 14.3 compares with F: S-time-weighted and time-averaged.
_TIME_WEIGHTINGS_VS_F: tuple[str, ...] = ("S", "eq")

#: The toneburst measurements of 18.2, as :data:`IEC61672_TABLE_4` keys them.
_TONEBURST_KEYS: tuple[str, ...] = ("F", "S", "E")

#: The readings of Clause 17: the reference sound level held on each level
#: range besides the reference one (17.3), and 5 dB above the first
#: indication of under-range on each level range, the reference one first
#: (17.4). On the reference level range 17.3 reads the reference sound level
#: 17.2 set, a deviation of zero by construction (IEC 61672-1 5.6.3); 17.4
#: reads a level 17.2 did not set, and "for each level range".
_RANGE_READINGS: tuple[str, ...] = ("17.3", "17.4")

#: What each reading of Clause 17 is, as the statement names it.
_RANGE_READING_NAMES: dict[str, str] = {
    "17.3": (
        "the reference sound level held on every other level range where it is displayed"
    ),
    "17.4": (
        "5 dB above the first indication of under-range on every level range, "
        "the reference one included"
    ),
}

#: How many values the row of 17.4 holds beyond that of 17.3: the reading on
#: the reference level range, first.
_REFERENCE_RANGE_READINGS = 1

#: How a result of Clause 17 names the reference level range, after its
#: subclause.
_RANGE_LABEL_REFERENCE = "reference range"

#: The fields of the record that say what the steps of Clause 16 cover.
_LINEARITY_PROCEDURE: tuple[str, ...] = (
    "linear_operating_range_db",
    "linearity_starting_point_db",
    "linearity_overload_level_db",
    "linearity_under_range_level_db",
)

#: IEC 61672-3:2013 16.3: the steps of the level linearity test, dB: 5 dB
#: until within 5 dB of a boundary of the linear operating range, and 1 dB
#: from there to the first indication of overload or under-range.
_COARSE_STEP_DB = 5.0
_FINE_STEP_DB = 1.0

#: How far two anticipated levels may differ from a step of 16.3 and still be
#: one, dB: the rounding of the arithmetic, not a tolerance on the step.
_STEP_ROUNDING_DB = 1e-6

#: IEC 61672-3:2013 7.2: the environmental conditions are measured at the
#: start and the end of periodic testing, at least.
_MIN_ENVIRONMENT_READINGS = 2

#: What each environmental reading can physically be: a positive pressure, a
#: temperature above absolute zero and a relative humidity from 0 % to 100 %.
#: Each is ``(lower, upper, lower included)``.
_PHYSICAL: dict[str, tuple[float, float, bool]] = {
    "static_pressures_kpa": (0.0, math.inf, False),
    "air_temperatures_c": (-273.15, math.inf, False),
    "relative_humidities_percent": (0.0, 100.0, True),
}


def _physical(name: str, value: float) -> bool:
    """Whether an environmental reading is one its quantity can take."""
    low, high, closed = _PHYSICAL[name]
    above = value >= low if closed else value > low
    return above and value <= high


#: The clauses every complete periodic test holds, whatever the meter:
#: environment, calibration check, self-generated noise, the two
#: frequency-weighting tests, the stabilities, the linearity on the reference
#: range and the tonebursts. 14.2 joins them for class 1, which has C.
_ALWAYS = ("7", "10", "11", "12", "13", "15", "16", "18", "21")

#: The outcome number of IEC 61672-1:2013 C.2.2 for a deviation outside its
#: limits measured with an acceptable uncertainty.
_OUTCOME_DEVIATION_EXCEEDS = 3

#: One kilohertz, where a frequency label switches to the "kHz" form.
_HZ_PER_KHZ = 1000.0


# ---------------------------------------------------------------------------
# The measurement record
# ---------------------------------------------------------------------------


def _scalar(value: float, name: str) -> float:
    """One finite number.

    :raises ValueError: for anything that is not one finite number.
    """
    number = require_real(value, f"'{name}' must be one number.")
    if not math.isfinite(number):
        msg = f"'{name}' must be finite."
        raise ValueError(msg)
    return number


def _row(
    values: object, name: str, *, allow_nan: bool, all_nan: bool = False
) -> tuple[float, ...]:
    """A flat, non-empty sequence of numbers as a tuple of floats.

    :param allow_nan: Whether a NaN may stand for a result not measured.
    :param all_nan: Whether every value may be NaN, for a row whose readings
        may all be ones the meter does not display.
    :raises ValueError: for a nested or empty sequence, an infinity, or a NaN
        where none is allowed.
    """
    try:
        array = np.asarray(values, dtype=np.float64)
    except (TypeError, ValueError):
        msg = f"'{name}' must be a sequence of numbers."
        raise ValueError(msg) from None
    if array.ndim != 1 or array.size == 0:
        msg = f"'{name}' must be a non-empty one-dimensional sequence."
        raise ValueError(msg)
    if np.any(np.isinf(array)) or (not allow_nan and np.any(np.isnan(array))):
        extra = ", or NaN where a result was not measured" if allow_nan else ""
        msg = f"'{name}' must hold finite values{extra}."
        raise ValueError(msg)
    if not all_nan and np.all(np.isnan(array)):
        msg = f"'{name}' holds no measured value; leave it out instead."
        raise ValueError(msg)
    return tuple(float(v) for v in array)


def _keyed(
    values: Mapping[str, Any], name: str, keys: tuple[str, ...]
) -> dict[str, Any]:
    """A mapping whose keys are among ``keys``, in their order.

    :raises ValueError: for something that is not a mapping, an empty one or
        an unknown key.
    """
    try:
        items = dict(values)
    except (TypeError, ValueError):
        msg = f"'{name}' must be a mapping keyed by {', '.join(map(repr, keys))}."
        raise ValueError(msg) from None
    unknown = [k for k in items if k not in keys]
    if unknown or not items:
        msg = (
            f"'{name}' must be a non-empty mapping keyed by "
            f"{', '.join(map(repr, keys))}; got {sorted(map(str, items))}."
        )
        raise ValueError(msg)
    return {k: items[k] for k in keys if k in items}


def _require_non_negative(values: tuple[float, ...], name: str) -> None:
    """An expanded uncertainty cannot be negative (NaN is a gap, not a value).

    :raises ValueError: for a negative value.
    """
    if any(v < 0.0 for v in values if not math.isnan(v)):
        msg = f"'{name}' must be non-negative: they are expanded uncertainties."
        raise ValueError(msg)


def _same_gaps(
    values: tuple[float, ...], uncertainties: tuple[float, ...], what: str
) -> None:
    """The results and their uncertainties leave the same places out (NaN).

    :raises ValueError: for different lengths or different gaps.
    """
    if len(values) != len(uncertainties):
        msg = f"{what}: {len(values)} results but {len(uncertainties)} uncertainties."
        raise ValueError(msg)
    if any(
        math.isnan(v) != math.isnan(u)
        for v, u in zip(values, uncertainties, strict=True)
    ):
        msg = f"{what}: a result and its uncertainty must be NaN together."
        raise ValueError(msg)


def _check_keyed_pair(
    clause: str,
    values_name: str,
    spread_name: str,
    values: Mapping[str, Any],
    spread: Mapping[str, Any],
) -> None:
    """A keyed clause's results beside their uncertainties, key by key.

    :raises ValueError: for different keys, lengths or gaps, or a negative
        uncertainty.
    """
    if set(values) != set(spread):
        msg = (
            f"clause {clause}: '{values_name}' and '{spread_name}' must "
            f"have the same keys; got {sorted(values)} and {sorted(spread)}."
        )
        raise ValueError(msg)
    for key in values:
        row = values[key]
        row_u = spread[key]
        if isinstance(row, tuple):
            _same_gaps(row, row_u, f"clause {clause} [{key!r}]")
            _require_non_negative(row_u, spread_name)
        else:
            _require_non_negative((row_u,), spread_name)


def _split_rows(
    split: tuple[float, ...] | Mapping[str, tuple[float, ...]],
    total: tuple[float, ...] | Mapping[str, tuple[float, ...]],
    split_name: str,
    total_name: str,
) -> list[tuple[str, tuple[float, ...], tuple[float, ...]]]:
    """``(where, part, whole)`` for each row a split of 4.4 pairs with its total.

    :raises ValueError: for a keyed split whose keys differ from its total's.
    """
    if isinstance(split, tuple) and isinstance(total, tuple):
        return [("", split, total)]
    if isinstance(split, tuple) or isinstance(total, tuple) or set(split) != set(total):
        msg = (
            f"'{split_name}' and '{total_name}' must have the same "
            f"keys; got {sorted(split)} and {sorted(total)}."
        )
        raise ValueError(msg)
    return [(f"[{k!r}]", split[k], total[k]) for k in split]


def _check_split_row(
    part: tuple[float, ...], whole: tuple[float, ...], part_name: str, whole_name: str
) -> None:
    """One row of a 4.4 split against its total: same length and gaps, no more.

    :raises ValueError: for a different length or gaps, a negative value, or
        a value above its total.
    """
    if len(part) != len(whole):
        msg = (
            f"'{part_name}' must hold one value per value of "
            f"'{whole_name}'; got {len(part)} for {len(whole)}."
        )
        raise ValueError(msg)
    _same_gaps(part, whole, f"'{part_name}'")
    _require_non_negative(part, part_name.split("[", 1)[0])
    if any(p > w for p, w in zip(part, whole, strict=True) if not math.isnan(p)):
        msg = (
            f"'{part_name}' must not exceed '{whole_name}': it is the same "
            "uncertainty without one of its components (4.4)."
        )
        raise ValueError(msg)


def _range_rows(values: Mapping[str, Any], name: str) -> dict[str, tuple[float, ...]]:
    """The rows of Clause 17, keyed ``"17.3"`` and ``"17.4"``.

    17.3 holds one value per level range besides the reference one, and reads
    only where the reference level is displayed, which may be on no other
    range, so its row may be all NaN; 17.4 holds one value per level range,
    the reference one first, so one value more. The two together hold a
    value.

    :raises ValueError: for an unknown key, rows whose lengths do not differ
        by the reading on the reference level range, or rows with no measured
        value between them.
    """
    rows = {
        k: _row(v, f"{name}[{k!r}]", allow_nan=True, all_nan=k == "17.3")
        for k, v in _keyed(values, name, _RANGE_READINGS).items()
    }
    if len(rows) == len(_RANGE_READINGS) and (
        len(rows["17.4"]) != len(rows["17.3"]) + _REFERENCE_RANGE_READINGS
    ):
        msg = (
            f"'{name}' holds one value per level range in '17.4', the reference "
            "one first, and one per level range besides the reference one in "
            f"'17.3'; got {len(rows['17.4'])} and {len(rows['17.3'])}."
        )
        raise ValueError(msg)
    if all(math.isnan(v) for row in rows.values() for v in row):
        msg = f"'{name}' holds no measured value; leave it out instead."
        raise ValueError(msg)
    return rows


def _other_ranges_held(rows: Mapping[str, Sequence[float]]) -> int:
    """How many level ranges besides the reference one the rows of 17 cover."""
    if "17.3" in rows:
        return len(rows["17.3"])
    return len(rows["17.4"]) - _REFERENCE_RANGE_READINGS


@dataclass(frozen=True, kw_only=True)
class SoundLevelMeterPeriodicMeasurements:
    r"""What a laboratory measured in the periodic tests of IEC 61672-3:2013.

    Every graded result comes with the actual expanded uncertainty the
    laboratory calculated for it, for a coverage probability of 95 % (4.2),
    in the same position or under the same key. A clause left at ``None`` was
    not measured. Levels and deviations are in decibels, and every field is
    keyword-only, so the unit in its name is written at the call site.

    :ivar static_pressures_kpa: Clause 7: the static pressure at the start and
        the end of the tests at least (7.2), in kilopascals.
    :ivar air_temperatures_c: The air temperature at the same times, in
        degrees Celsius.
    :ivar relative_humidities_percent: The relative humidity, in per cent.
    :ivar calibration_check_initial_db: Clause 10: the indication at the
        calibration check frequency on the sound calibrator before any
        adjustment.
    :ivar calibration_check_adjusted_db: The indication after adjustment (the
        same number when none was needed).
    :ivar self_noise_microphone_db: 11.1: the A-weighted self-generated noise
        with the microphone installed, on the most-sensitive level range;
        reported for information only, without an uncertainty.
    :ivar self_noise_electrical_db: 11.2: the self-generated noise with the
        electrical input-signal device, keyed by frequency weighting
        (``"A"``, ``"C"``, ``"Z"``), every weighting the meter provides.
    :ivar acoustic_weighting_deviations_db: 12.16: the deviations of the
        relative frequency weighting from its design goal at 125 Hz and 8 kHz,
        in that order (:data:`ACOUSTIC_TEST_FREQUENCIES_HZ`), after the
        corrections of 12.14.
    :ivar acoustic_weighting_uncertainties_db: Their uncertainties.
    :ivar acoustic_weighting_uncertainties_without_correction_data_db:
        Optional, for 4.4: the same uncertainties without the uncertainty of
        the manufacturer's free-field or random-incidence correction data,
        never more than the totals. A result whose total exceeds its maximum
        and whose uncertainty without that data does not is a result that did
        not conform, for that reason, rather than one 4.3 forbids using.
    :ivar electrical_weighting_deviations_db: 13.9: for every frequency
        weighting the meter provides, keyed ``"A"``, ``"C"``, ``"Z"``, the
        corrected relative frequency weightings, which are the deviations from
        the design goal, at :data:`ELECTRICAL_TEST_FREQUENCIES_HZ` for the
        class in order, NaN at a frequency not measured.
    :ivar electrical_weighting_uncertainties_db: The same keys and shape.
    :ivar electrical_weighting_uncertainties_without_correction_data_db:
        Optional, for 4.4: the same without the uncertainty of the
        manufacturer's correction data, which 13.7 applies too; the same keys,
        shape and gaps.
    :ivar weighting_at_1khz_deviations_db: 14.2: the C-weighted and
        Z-weighted indications at 1 kHz less the A-weighted one, keyed
        ``"C"`` and ``"Z"``.
    :ivar weighting_at_1khz_uncertainties_db: The same keys.
    :ivar time_weighting_at_1khz_deviations_db: 14.3: the A-weighted
        S-time-weighted (``"S"``) and time-averaged (``"eq"``) indications at
        1 kHz less the F-time-weighted one.
    :ivar time_weighting_at_1khz_uncertainties_db: The same keys.
    :ivar long_term_stability_db: 15.3: the final less the initial A-weighted
        indication over 25 min to 35 min of operation.
    :ivar long_term_stability_uncertainty_db: Its uncertainty.
    :ivar linearity_deviations_db: 16: the level linearity deviations at
        8 kHz on the reference level range, indicated less anticipated level,
        one per step of 16.3, in any order.
    :ivar linearity_uncertainties_db: Their uncertainties.
    :ivar linearity_levels_db: The anticipated level of each 16 result, which
        labels it and shows which steps of 16.3 the record holds.
    :ivar linear_operating_range_db: The lower and the upper boundary of the
        linear operating range at 8 kHz on the reference level range, as the
        instruction manual states them (IEC 61672-1 5.6.10): the extent the
        steps of 16.3 cover and 16.4 holds to the limits.
    :ivar linearity_starting_point_db: The starting point the instruction
        manual gives for the tests of level linearity at 8 kHz on the
        reference level range (16.2; IEC 61672-1 5.6.11).
    :ivar linearity_overload_level_db: The anticipated level of the step that
        first caused an indication of overload, which the rising steps of
        16.3 stop short of.
    :ivar linearity_under_range_level_db: The anticipated level of the step
        that first caused an indication of under-range, which the falling
        steps of 16.3 stop short of.
    :ivar range_linearity_deviations_db: 17.5: the level linearity deviations
        including the level range control, at 1 kHz, keyed ``"17.3"`` (the
        reference sound level of 17.2 held on each level range besides the
        reference one, NaN where it is not displayed) and ``"17.4"`` (5 dB
        above the first indication of under-range on each level range, NaN
        where not measured). ``"17.4"`` starts with the reference level
        range, which 17.4 tests "for each level range" as well, and then
        takes the other ranges in the order of ``"17.3"``, so it holds one
        value more; 17.3 has no reading on the reference range, where the
        reference sound level of 17.2 deviates by zero by construction
        (IEC 61672-1 5.6.3).
    :ivar range_linearity_uncertainties_db: The same keys, shape and gaps.
    :ivar toneburst_responses_db: 18: the toneburst responses relative to the
        steady level, keyed ``"F"`` (:math:`L_\mathrm{AFmax} -
        L_\mathrm{A}`), ``"S"`` (:math:`L_\mathrm{ASmax} - L_\mathrm{A}`) and
        ``"E"`` (:math:`L_\mathrm{AE} - L_\mathrm{A}`), each at
        :data:`TONEBURST_TEST_DURATIONS_MS` in order, NaN where not measured.
        The deviation from Table 4 is taken by the verdict.
    :ivar toneburst_uncertainties_db: The same keys and shape.
    :ivar c_peak_differences_db: 19.6: :math:`L_\mathrm{Cpeak} -
        L_\mathrm{C}` for one cycle at 8 kHz, a positive half cycle at 500 Hz
        and a negative half cycle at 500 Hz, in that order, NaN where not
        measured. The deviation from Table 5 is taken by the verdict.
    :ivar c_peak_uncertainties_db: Their uncertainties.
    :ivar c_peak_overload_indicated: Whether any of those signals caused an
        overload indication, which 19.3 and 19.5 forbid.
    :ivar overload_difference_db: 20.4: the level of the positive
        one-half-cycle input signal that first caused an overload indication
        less that of the negative one.
    :ivar overload_uncertainty_db: Its uncertainty.
    :ivar overload_latched: 20.5: whether the overload indicator latched on
        as IEC 61672-1 5.11.5 specifies.
    :ivar high_level_stability_db: 21.3: the final less the initial
        A-weighted indication over 5 min of exposure near the upper boundary of
        the least-sensitive level range.
    :ivar high_level_stability_uncertainty_db: Its uncertainty.
    """

    static_pressures_kpa: Sequence[float] | None = None
    air_temperatures_c: Sequence[float] | None = None
    relative_humidities_percent: Sequence[float] | None = None
    calibration_check_initial_db: float | None = None
    calibration_check_adjusted_db: float | None = None
    self_noise_microphone_db: float | None = None
    self_noise_electrical_db: Mapping[str, float] | None = None
    acoustic_weighting_deviations_db: Sequence[float] | None = None
    acoustic_weighting_uncertainties_db: Sequence[float] | None = None
    acoustic_weighting_uncertainties_without_correction_data_db: (
        Sequence[float] | None
    ) = None
    electrical_weighting_deviations_db: Mapping[str, Sequence[float]] | None = None
    electrical_weighting_uncertainties_db: Mapping[str, Sequence[float]] | None = None
    electrical_weighting_uncertainties_without_correction_data_db: (
        Mapping[str, Sequence[float]] | None
    ) = None
    weighting_at_1khz_deviations_db: Mapping[str, float] | None = None
    weighting_at_1khz_uncertainties_db: Mapping[str, float] | None = None
    time_weighting_at_1khz_deviations_db: Mapping[str, float] | None = None
    time_weighting_at_1khz_uncertainties_db: Mapping[str, float] | None = None
    long_term_stability_db: float | None = None
    long_term_stability_uncertainty_db: float | None = None
    linearity_deviations_db: Sequence[float] | None = None
    linearity_uncertainties_db: Sequence[float] | None = None
    linearity_levels_db: Sequence[float] | None = None
    linear_operating_range_db: Sequence[float] | None = None
    linearity_starting_point_db: float | None = None
    linearity_overload_level_db: float | None = None
    linearity_under_range_level_db: float | None = None
    range_linearity_deviations_db: Mapping[str, Sequence[float]] | None = None
    range_linearity_uncertainties_db: Mapping[str, Sequence[float]] | None = None
    toneburst_responses_db: Mapping[str, Sequence[float]] | None = None
    toneburst_uncertainties_db: Mapping[str, Sequence[float]] | None = None
    c_peak_differences_db: Sequence[float] | None = None
    c_peak_uncertainties_db: Sequence[float] | None = None
    c_peak_overload_indicated: bool | None = None
    overload_difference_db: float | None = None
    overload_uncertainty_db: float | None = None
    overload_latched: bool | None = None
    high_level_stability_db: float | None = None
    high_level_stability_uncertainty_db: float | None = None

    def __post_init__(self) -> None:
        """Freeze every field and refuse a record the rule cannot be read on.

        :raises ValueError: if a result comes without its uncertainty or the
            other way round, if their lengths, keys or gaps differ, if a value
            is not finite (NaN is allowed only where a field says so), if an
            uncertainty is negative, if a key is unknown or a toneburst row
            has the wrong length, if an environmental reading is outside
            what the quantity can be, if an uncertainty without the
            correction data comes without its total or exceeds it, or if
            the procedure of Clause 16 is contradicted: a linear operating
            range whose lower boundary is not below its upper one, a
            starting point outside it, or a step at or past the first
            indication of overload or under-range.
        """
        self._freeze_environment()
        self._freeze_scalars()
        self._freeze_rows()
        self._freeze_mappings()
        self._check_range_rows()
        self._check_pairs()
        self._check_correction_data_split()
        self._check_bool("c_peak_overload_indicated", "c_peak_differences_db")
        self._check_bool("overload_latched", "overload_difference_db")

    def _set(self, name: str, value: object) -> None:
        """Replace a field of the frozen record while it is being built."""
        object.__setattr__(self, name, value)

    def _freeze_environment(self) -> None:
        """Clause 7: three sequences of physical readings."""
        names = tuple(PERIODIC_TEST_ENVIRONMENT)
        given = [getattr(self, n) is not None for n in names]
        if any(given) and not all(given):
            msg = (
                "clause 7 records 'static_pressures_kpa', 'air_temperatures_c' and "
                "'relative_humidities_percent' together (7.2)."
            )
            raise ValueError(msg)
        for name in names:
            values = getattr(self, name)
            if values is None:
                continue
            row = _row(values, name, allow_nan=False)
            if not all(_physical(name, v) for v in row):
                msg = f"'{name}' holds a reading the quantity cannot take."
                raise ValueError(msg)
            self._set(name, row)

    def _freeze_scalars(self) -> None:
        """The single numbers of Clauses 10, 11.1, 15, 16, 20 and 21."""
        for name in (
            "calibration_check_initial_db",
            "calibration_check_adjusted_db",
            "self_noise_microphone_db",
            "long_term_stability_db",
            "long_term_stability_uncertainty_db",
            "linearity_starting_point_db",
            "linearity_overload_level_db",
            "linearity_under_range_level_db",
            "overload_difference_db",
            "overload_uncertainty_db",
            "high_level_stability_db",
            "high_level_stability_uncertainty_db",
        ):
            value = getattr(self, name)
            if value is not None:
                self._set(name, _scalar(value, name))

    def _freeze_rows(self) -> None:
        """The flat sequences of Clauses 12, 16 and 19."""
        for name, allow_nan in (
            ("acoustic_weighting_deviations_db", False),
            ("acoustic_weighting_uncertainties_db", False),
            ("acoustic_weighting_uncertainties_without_correction_data_db", False),
            ("linearity_deviations_db", False),
            ("linearity_uncertainties_db", False),
            ("linearity_levels_db", False),
            ("linear_operating_range_db", False),
            ("c_peak_differences_db", True),
            ("c_peak_uncertainties_db", True),
        ):
            value = getattr(self, name)
            if value is not None:
                self._set(name, _row(value, name, allow_nan=allow_nan))
        for name, count in (
            ("acoustic_weighting_deviations_db", len(ACOUSTIC_TEST_FREQUENCIES_HZ)),
            ("linear_operating_range_db", 2),
            ("c_peak_differences_db", len(_C_PEAK_ROWS)),
        ):
            row = getattr(self, name)
            if row is not None and len(row) != count:
                msg = f"'{name}' must hold {count} results; got {len(row)}."
                raise ValueError(msg)

    def _freeze_mappings(self) -> None:
        """The keyed fields of Clauses 11.2, 13, 14 and 18."""
        noise = self.self_noise_electrical_db
        if noise is not None:
            items = _keyed(noise, "self_noise_electrical_db", _WEIGHTINGS)
            self._set(
                "self_noise_electrical_db",
                MappingProxyType(
                    {
                        k: _scalar(v, f"self_noise_electrical_db[{k!r}]")
                        for k, v in items.items()
                    }
                ),
            )
        for name, keys in (
            ("weighting_at_1khz_deviations_db", _WEIGHTINGS_VS_A),
            ("weighting_at_1khz_uncertainties_db", _WEIGHTINGS_VS_A),
            ("time_weighting_at_1khz_deviations_db", _TIME_WEIGHTINGS_VS_F),
            ("time_weighting_at_1khz_uncertainties_db", _TIME_WEIGHTINGS_VS_F),
        ):
            value = getattr(self, name)
            if value is not None:
                items = _keyed(value, name, keys)
                self._set(
                    name,
                    MappingProxyType(
                        {k: _scalar(v, f"{name}[{k!r}]") for k, v in items.items()}
                    ),
                )
        for name, keys in (
            ("electrical_weighting_deviations_db", _WEIGHTINGS),
            ("electrical_weighting_uncertainties_db", _WEIGHTINGS),
            (
                "electrical_weighting_uncertainties_without_correction_data_db",
                _WEIGHTINGS,
            ),
            ("toneburst_responses_db", _TONEBURST_KEYS),
            ("toneburst_uncertainties_db", _TONEBURST_KEYS),
        ):
            value = getattr(self, name)
            if value is not None:
                items = _keyed(value, name, keys)
                self._set(
                    name,
                    MappingProxyType(
                        {
                            k: _row(v, f"{name}[{k!r}]", allow_nan=True)
                            for k, v in items.items()
                        }
                    ),
                )
        for name in ("toneburst_responses_db", "toneburst_uncertainties_db"):
            rows = getattr(self, name)
            for key, row in (rows or {}).items():
                count = len(TONEBURST_TEST_DURATIONS_MS[key])
                if len(row) != count:
                    msg = (
                        f"'{name}[{key!r}]' must hold {count} results, at "
                        f"{TONEBURST_TEST_DURATIONS_MS[key]} ms; got {len(row)}."
                    )
                    raise ValueError(msg)

    def _check_range_rows(self) -> None:
        """Clause 17: the rows of 17.3 and 17.4, 17.4 on the reference range too.

        :raises ValueError: for rows whose lengths do not differ by the
            reading of 17.4 on the reference level range, or rows with no
            measured value between them.
        """
        for name in (
            "range_linearity_deviations_db",
            "range_linearity_uncertainties_db",
        ):
            value = getattr(self, name)
            if value is not None:
                self._set(name, MappingProxyType(_range_rows(value, name)))

    def _check_pairs(self) -> None:
        """Each result with its uncertainty, the same length, keys and gaps."""
        self._together(
            "10", ("calibration_check_initial_db", "calibration_check_adjusted_db")
        )
        for requirement, (values_name, spread_name) in _PAIRS.items():
            clause = _CLAUSES[requirement]
            self._together(clause, (values_name, spread_name))
            self._check_pair(clause, values_name, spread_name)
        self._check_linearity_levels()
        self._check_linearity_procedure()

    def _check_pair(self, clause: str, values_name: str, spread_name: str) -> None:
        """One clause's results beside their uncertainties: one number, a row or a mapping."""
        values = getattr(self, values_name)
        spread = getattr(self, spread_name)
        if values is None or spread is None:
            return
        if isinstance(values, float):
            _require_non_negative((spread,), spread_name)
            return
        if isinstance(values, tuple):
            _same_gaps(values, spread, f"clause {clause}")
            _require_non_negative(spread, spread_name)
            return
        _check_keyed_pair(clause, values_name, spread_name, values, spread)

    def _check_linearity_levels(self) -> None:
        """The anticipated levels of Clause 16, one per result."""
        levels = self.linearity_levels_db
        deviations = self.linearity_deviations_db
        if levels is not None and (
            deviations is None or len(levels) != len(deviations)
        ):
            msg = "'linearity_levels_db' labels the 16 results: one level per result."
            raise ValueError(msg)

    def _check_linearity_procedure(self) -> None:
        """16.2 and 16.3: the range, the starting point and where the steps stop.

        :raises ValueError: for any of them without the results of Clause 16,
            a range whose lower boundary is not below its upper one, a
            starting point outside it, or a step at or past the first
            indication of overload or under-range.
        """
        given = [n for n in _LINEARITY_PROCEDURE if getattr(self, n) is not None]
        if given and self.linearity_deviations_db is None:
            msg = f"{given} describe the steps of Clause 16, whose results are missing."
            raise ValueError(msg)
        bounds = self.linear_operating_range_db
        start = self.linearity_starting_point_db
        if bounds is not None and bounds[0] >= bounds[1]:
            msg = (
                "'linear_operating_range_db' is (lower, upper) with the lower "
                f"boundary below the upper one; got {bounds}."
            )
            raise ValueError(msg)
        if (
            bounds is not None
            and start is not None
            and (start < bounds[0] or start > bounds[1])
        ):
            msg = (
                f"the starting point of {start:g} dB lies outside the linear "
                f"operating range {bounds}, where 16.2 begins (IEC 61672-1 5.6.11)."
            )
            raise ValueError(msg)
        levels = self.linearity_levels_db or ()
        overload = self.linearity_overload_level_db
        under_range = self.linearity_under_range_level_db
        if overload is not None and any(level >= overload for level in levels):
            msg = (
                f"a step of Clause 16 is at or above the first indication of "
                f"overload, {overload:g} dB, which 16.3 stops short of."
            )
            raise ValueError(msg)
        if under_range is not None and any(level <= under_range for level in levels):
            msg = (
                f"a step of Clause 16 is at or below the first indication of "
                f"under-range, {under_range:g} dB, which 16.3 stops short of."
            )
            raise ValueError(msg)

    def _check_correction_data_split(self) -> None:
        """4.4: each uncertainty without the correction data beside its total.

        :raises ValueError: for a split whose total is missing, whose keys,
            lengths or gaps differ from it, or which is negative or exceeds
            it.
        """
        for total_name, split_name in _CORRECTION_DATA_SPLITS:
            split = getattr(self, split_name)
            if split is None:
                continue
            total = getattr(self, total_name)
            if total is None:
                msg = f"'{split_name}' splits '{total_name}', which is missing (4.4)."
                raise ValueError(msg)
            for where, part, whole in _split_rows(split, total, split_name, total_name):
                _check_split_row(
                    part, whole, f"{split_name}{where}", f"{total_name}{where}"
                )

    def _together(self, clause: str, names: tuple[str, ...]) -> None:
        """All fields of one clause are given together or not at all."""
        given = [getattr(self, n) is not None for n in names]
        if any(given) and not all(given):
            missing = [n for n, g in zip(names, given, strict=True) if not g]
            msg = (
                f"clause {clause} needs {', '.join(repr(n) for n in names)} "
                f"together; missing {missing}: IEC 61672-3:2013 grades a result "
                "only with the uncertainty it was measured with (4.1)."
            )
            raise ValueError(msg)

    def _check_bool(self, name: str, companion: str) -> None:
        """A yes/no observation belongs to the test it was made in."""
        value = getattr(self, name)
        if value is None:
            return
        if not isinstance(value, bool | np.bool_):
            msg = f"'{name}' must be True or False."
            raise ValueError(msg)
        if getattr(self, companion) is None:
            msg = f"'{name}' is observed during the test of '{companion}', which is missing."
            raise ValueError(msg)
        self._set(name, bool(value))


#: IEC 61672-3:2013 4.4: each total uncertainty that carries the
#: manufacturer's free-field or random-incidence correction data, and the
#: field that holds it without that data.
_CORRECTION_DATA_SPLITS: tuple[tuple[str, str], ...] = (
    (
        "acoustic_weighting_uncertainties_db",
        "acoustic_weighting_uncertainties_without_correction_data_db",
    ),
    (
        "electrical_weighting_uncertainties_db",
        "electrical_weighting_uncertainties_without_correction_data_db",
    ),
)

#: Each graded requirement's result field and uncertainty field.
_PAIRS: dict[str, tuple[str, str]] = {
    "acoustic_weighting": (
        "acoustic_weighting_deviations_db",
        "acoustic_weighting_uncertainties_db",
    ),
    "electrical_weighting": (
        "electrical_weighting_deviations_db",
        "electrical_weighting_uncertainties_db",
    ),
    "weighting_at_1khz": (
        "weighting_at_1khz_deviations_db",
        "weighting_at_1khz_uncertainties_db",
    ),
    "time_weighting_at_1khz": (
        "time_weighting_at_1khz_deviations_db",
        "time_weighting_at_1khz_uncertainties_db",
    ),
    "long_term_stability": (
        "long_term_stability_db",
        "long_term_stability_uncertainty_db",
    ),
    "level_linearity": ("linearity_deviations_db", "linearity_uncertainties_db"),
    "range_linearity": (
        "range_linearity_deviations_db",
        "range_linearity_uncertainties_db",
    ),
    "toneburst": ("toneburst_responses_db", "toneburst_uncertainties_db"),
    "c_peak": ("c_peak_differences_db", "c_peak_uncertainties_db"),
    "overload": ("overload_difference_db", "overload_uncertainty_db"),
    "high_level_stability": (
        "high_level_stability_db",
        "high_level_stability_uncertainty_db",
    ),
}


# ---------------------------------------------------------------------------
# The meter's optional features (8.1)
# ---------------------------------------------------------------------------

#: The optional design features of IEC 61672-1:2013 the periodic tests
#: cover, as :class:`SoundLevelMeterFeatures` names them, in its order.
_FEATURES: tuple[str, ...] = (
    "c_weighting",
    "z_weighting",
    "f_time_weighting",
    "s_time_weighting",
    "time_averaged",
    "sound_exposure_level",
    "level_ranges",
    "c_weighted_peak",
)

#: What each feature is, as a sentence names the meter having it.
_FEATURE_WHAT: dict[str, str] = {
    "c_weighting": "provides frequency weighting C",
    "z_weighting": "provides frequency weighting Z",
    "f_time_weighting": "has the F time weighting",
    "s_time_weighting": "has the S time weighting",
    "time_averaged": "displays time-averaged sound level",
    "sound_exposure_level": "measures sound exposure level",
    "c_weighted_peak": "measures C-weighted peak sound level",
}

#: Where IEC 61672-3:2013 tests each feature, as a sentence names it.
_FEATURE_TESTS: dict[str, str] = {
    "c_weighting": "11.2, 13 and 14.2 test",
    "z_weighting": "11.2, 13 and 14.2 test",
    "f_time_weighting": "Clause 18 tests and 14.3 compares with",
    "s_time_weighting": "14.3 and Clause 18 test",
    "time_averaged": "14.3, Clause 18 and Clause 20 test",
    "sound_exposure_level": "Clause 18 tests",
    "c_weighted_peak": "Clause 19 tests",
}

#: The whole clauses a single feature brings into the test, and what the
#: verdict says of a meter without it.
_CLAUSE_FEATURES: dict[str, tuple[str, str]] = {
    "17": ("level_ranges", "the meter has one level range (17.1)"),
    "19": (
        "c_weighted_peak",
        "the meter does not measure C-weighted peak sound level (8.1)",
    ),
    "20": (
        "time_averaged",
        "the meter does not display time-averaged sound level (20.1)",
    ),
}

#: The features IEC 61672-1:2013 takes away with another one: a meter without
#: frequency weighting C measures no C-weighted peak sound level (5.1.10), and
#: one without the F time weighting has no S (5.1.9). Each is the feature it
#: needs and why, as a sentence says it.
_IMPLIED_ABSENT: dict[str, tuple[str, str]] = {
    "c_weighted_peak": (
        "c_weighting",
        "a meter that measures C-weighted peak sound level provides frequency "
        "weighting C (IEC 61672-1 5.1.10)",
    ),
    "s_time_weighting": (
        "f_time_weighting",
        "a meter with the S time weighting has the F time weighting too "
        "(IEC 61672-1 5.1.9)",
    ),
}

#: Why a clause is not applicable when its feature is absent only with the
#: one it needs (:data:`_IMPLIED_ABSENT`).
_IMPLIED_CLAUSE_WHY: dict[str, str] = {
    "c_weighted_peak": (
        "the meter provides no frequency weighting C, which a meter that "
        "measures C-weighted peak sound level provides (IEC 61672-1 5.1.10)"
    ),
}

#: The feature that is each frequency weighting besides A.
_WEIGHTING_FEATURES: dict[str, str] = {"C": "c_weighting", "Z": "z_weighting"}

#: Why the verdict holds a feature present when only the declaration says so.
_DECLARED = "the features declared for the meter include it"

#: Why the verdict holds a feature present when 14.3 compares it with F.
_SHOWN_BY_14_3 = "14.3 shows the meter provides it"

#: Why a meter owes the sound exposure level of the tonebursts without
#: measuring it: 18.2 calculates it from the time-averaged sound level.
_EXPOSURE_FROM_TIME_AVERAGE = (
    "the meter displays time-averaged sound level, from which it is calculated"
)


@dataclass(frozen=True, kw_only=True)
class SoundLevelMeterFeatures:
    r"""Which optional design features of IEC 61672-1:2013 a sound level meter has.

    IEC 61672-3:2013 8.1: the periodic tests "apply only for those design
    features that are required by IEC 61672-1 and that are available in the
    sound level meter submitted for test. All such features shall be
    tested." A record shows that a meter has a feature by holding its
    results; it cannot show that the meter lacks one, and a meter with one
    level range reads the same as a record that left Clause 17 out. The
    instruction manual says which features the meter has (IEC 61672-1
    5.1.9, 5.1.10, 5.1.12), and each field carries that answer: ``True`` the
    meter has the feature, ``False`` it has not, ``None`` (the default) not
    declared, and for the level ranges their number. The verdict owes the
    tests of every feature declared or shown, lists the clauses a feature
    declared absent takes out of the test under
    :attr:`SoundLevelMeterPeriodicVerification.not_applicable`, and holds a
    feature neither declared nor shown as an open question that keeps the
    test incomplete, under
    :attr:`SoundLevelMeterPeriodicVerification.undeclared`, as it holds the
    number of level ranges of a meter Clause 17 shows to have several, which
    17.3 and 17.4 cover. A feature declared absent takes with it the one IEC
    61672-1 makes depend on it: without frequency weighting C the meter
    measures no C-weighted peak sound level (5.1.10), and without the F time
    weighting it has no S (5.1.9). Frequency weighting A has no field: every
    meter has it (5.1.9).

    :ivar c_weighting: Frequency weighting C, tested in 11.2, 13 and 14.2. A
        class 1 meter has it, and so does a meter that measures C-weighted
        peak sound level (IEC 61672-1 5.1.10).
    :ivar z_weighting: Frequency weighting Z, tested in 11.2, 13 and 14.2,
        optional for both classes (5.1.10).
    :ivar f_time_weighting: The F time weighting: the maximum F-time-weighted
        toneburst responses of Clause 18, and the display 14.3 compares the
        others with. A time-weighting meter has it (5.1.9), so a meter with
        S has F.
    :ivar s_time_weighting: The S time weighting: 14.3 and the maximum
        S-time-weighted toneburst responses of Clause 18.
    :ivar time_averaged: A display of time-averaged sound level: 14.3, the
        overload indication of Clause 20 (20.1) and the sound exposure level
        of the tonebursts, which 18.2 calculates from it when the meter does
        not measure sound exposure level.
    :ivar sound_exposure_level: The measurement of sound exposure level: the
        sound exposure level toneburst responses of Clause 18 (18.2).
    :ivar level_ranges: How many level ranges the meter has, as the
        instruction manual identifies them (IEC 61672-1 5.1.12): 1 for a
        meter with one, which takes Clause 17 out (17.1), and for more, the
        number 17.4 covers, the reference level range included, and 17.3
        every one besides it.
    :ivar c_weighted_peak: The measurement of C-weighted peak sound level:
        Clause 19.
    """

    c_weighting: bool | None = None
    z_weighting: bool | None = None
    f_time_weighting: bool | None = None
    s_time_weighting: bool | None = None
    time_averaged: bool | None = None
    sound_exposure_level: bool | None = None
    level_ranges: int | None = None
    c_weighted_peak: bool | None = None

    def __post_init__(self) -> None:
        """Hold each answer as ``True``, ``False`` or ``None``, a count as an int.

        :raises ValueError: for an answer that is none of them, a number of
            level ranges that is not a whole number from 1 up, or a meter
            IEC 61672-1 rules out: C-weighted peak without frequency
            weighting C (5.1.10), S without F (5.1.9), or none of the F time
            weighting, a time-averaged display and sound exposure level, one
            of which 5.1.9 asks of every sound level meter.
        """
        for name in _FEATURES:
            value = getattr(self, name)
            if value is None or name == "level_ranges":
                continue
            if not isinstance(value, bool | np.bool_):
                msg = f"'{name}' must be True, False or None (not declared)."
                raise ValueError(msg)
            object.__setattr__(self, name, bool(value))
        self._hold_level_ranges()
        self._refuse_what_5_1_9_rules_out()

    def _hold_level_ranges(self) -> None:
        """The number of level ranges as an int from 1 up, or ``None``."""
        count = self.level_ranges
        if count is None:
            return
        if (
            isinstance(count, bool | np.bool_)
            or not isinstance(count, int | np.integer)
            or count < 1
        ):
            msg = (
                "'level_ranges' must be the number of level ranges, a whole "
                f"number from 1 up, or None (not declared); got {count!r}."
            )
            raise ValueError(msg)
        object.__setattr__(self, "level_ranges", int(count))

    def _refuse_what_5_1_9_rules_out(self) -> None:
        """A feature without the one it needs, or a meter that indicates nothing."""
        for name, (needed, why) in _IMPLIED_ABSENT.items():
            if getattr(self, name) and getattr(self, needed) is False:
                msg = f"{why}: '{name}' is True and '{needed}' is False."
                raise ValueError(msg)
        if (
            self.f_time_weighting is False
            and self.time_averaged is False
            and self.sound_exposure_level is False
        ):
            msg = (
                "a sound level meter indicates F-time-weighted sound level, "
                "time-averaged sound level or sound exposure level, one of them "
                "at least (IEC 61672-1 5.1.9), and a meter without F has no S "
                "either: 'f_time_weighting', 'time_averaged' and "
                "'sound_exposure_level' cannot all be False."
            )
            raise ValueError(msg)


# ---------------------------------------------------------------------------
# The verdicts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SoundLevelMeterPeriodicRequirement:
    """The verdict on one requirement of IEC 61672-3:2013.

    :ivar name: The requirement, one of :data:`SLM_PERIODIC_REQUIREMENTS`.
    :ivar clause: The clause of IEC 61672-3:2013 that tests it.
    :ivar tables: Where IEC 61672-1:2013 prints its acceptance limits and
        maximum-permitted uncertainty.
    :ivar labels: What each result is (the frequency, the weighting, the
        toneburst or the signal), in the order given.
    :ivar verifications: One
        :class:`~phonometry.metrology.ConformanceVerification` per result, on
        the deviation from the design goal.
    :ivar checks: The yes/no requirements of the clause, each ``(what,
        held)``: no overload or under-range indication within the linear
        operating range (16.4), no overload indication during the
        C-weighted peak test (19.3, 19.5) and the latching of the overload
        indicator (20.5).
    :ivar over_maximum_by_correction_data: The results whose actual
        uncertainty exceeds its maximum only because it includes the
        uncertainty of the manufacturer's free-field or random-incidence
        correction data (4.4): results that did not conform, for that
        reason, and not results 4.3 forbids using.
    """

    name: str
    clause: str
    tables: str
    labels: tuple[str, ...]
    verifications: tuple[ConformanceVerification, ...]
    checks: tuple[tuple[str, bool], ...] = ()
    over_maximum_by_correction_data: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """One label per result, and at least one result.

        :raises ValueError: if the labels and the results differ in number,
            there is no result, or a result of 4.4 is not one of the labels or
            is within its maximum.
        """
        if not self.verifications:
            msg = f"clause {self.clause} carries no result."
            raise ValueError(msg)
        if len(self.labels) != len(self.verifications):
            msg = (
                f"clause {self.clause}: {len(self.labels)} labels for "
                f"{len(self.verifications)} results."
            )
            raise ValueError(msg)
        within = {
            label
            for label, v in zip(self.labels, self.verifications, strict=True)
            if v.uncertainty_within_maximum
        }
        stray = [
            label
            for label in self.over_maximum_by_correction_data
            if label not in self.labels or label in within
        ]
        if stray:
            msg = (
                f"clause {self.clause}: {stray} are not results whose "
                "uncertainty exceeds its maximum (4.4)."
            )
            raise ValueError(msg)

    @property
    def title(self) -> str:
        """What the clause tests, as its heading reads."""
        return _TITLES[self.clause]

    @property
    def passes(self) -> bool:
        """Whether every result conforms (4.1) and every check held."""
        return all(v.passes for v in self.verifications) and all(
            held for _, held in self.checks
        )

    @property
    def unusable(self) -> tuple[str, ...]:
        """The results whose uncertainty exceeds the maximum permitted (4.3).

        All of them but those of :attr:`over_maximum_by_correction_data`,
        which 4.4 lets the test proceed with.
        """
        return tuple(
            label
            for label, v in zip(self.labels, self.verifications, strict=True)
            if not v.uncertainty_within_maximum
            and label not in self.over_maximum_by_correction_data
        )

    @property
    def failed(self) -> tuple[str, ...]:
        """The results that did not conform, and the failed checks.

        A result outside its acceptance limits and measured with an
        acceptable uncertainty, or one of
        :attr:`over_maximum_by_correction_data` (4.4). A result that is
        :attr:`unusable` shows nothing about the meter (4.3) and is not here.
        """
        results = tuple(
            label
            for label, v in zip(self.labels, self.verifications, strict=True)
            if v.outcome == _OUTCOME_DEVIATION_EXCEEDS
            or label in self.over_maximum_by_correction_data
        )
        return results + tuple(what for what, held in self.checks if not held)

    def failure_reason(self, label: str) -> str:
        """Why a result or a check did not complete, as 22 t) states it.

        :param label: One of :attr:`failed`.
        :return: The reason, in the words of the NOTE to 22 t) where it
            prints them.
        :raises ValueError: for a label that did not fail.
        """
        if label not in self.failed:
            msg = f"clause {self.clause}: {label!r} did not fail; failed: {self.failed}"
            raise ValueError(msg)
        if label in _CHECK_FAILURES:
            return _CHECK_FAILURES[label]
        deviation = _REASONS[self.name]
        if label not in self.over_maximum_by_correction_data:
            return deviation
        verification = self.verifications[self.labels.index(label)]
        if verification.deviation_within_limits:
            return _CORRECTION_DATA_REASON
        return f"{deviation}, and {_CORRECTION_DATA_REASON}"

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a SoundLevelMeterPeriodicRequirement has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw every result of the requirement against its limits.

        As IEC 61672-1:2013 Figure C.1 draws its examples: the acceptance
        limits, the deviation from the design goal, the actual uncertainty as
        its error bar and the maximum permitted as the band behind it. The
        electrical test of the frequency weightings, whose limits run from
        0,7 dB to 16 dB, is drawn as each result's margin to its nearer limit
        instead. A result whose uncertainty exceeds its maximum is drawn
        hollow, as 4.3 forbids using it, and a result of
        :attr:`over_maximum_by_correction_data` as one that did not conform
        (4.4). The title names the clause and its verdict above the clause's
        heading.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the verdict markers.
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_slm_periodic_requirement

        check_language(language)
        return plot_slm_periodic_requirement(self, ax, language=language, **kwargs)


def _in_running_text(heading: str) -> str:
    """A heading as it reads inside a sentence.

    Its initial capital is lowered when it only opens the sentence
    ("Toneburst response"), and kept when the first word is a designation
    ("C-weighted peak sound level").
    """
    first = heading.split(" ", 1)[0]
    if len(first) > 1 and first[1].islower():
        return heading[0].lower() + heading[1:]
    return heading


def _clause_label(clause: str) -> str:
    """``clause 16 (level linearity on the reference level range)``."""
    return f"clause {clause} ({_in_running_text(_TITLES[clause])})"


@dataclass(frozen=True)
class SoundLevelMeterPeriodicVerification:
    """The IEC 61672-3:2013 verdict on the periodic tests of a sound level meter.

    :ivar meter_class: The class the meter was tested as, 1 or 2.
    :ivar pattern_approval_public: Whether evidence is publicly available
        that the model passed the pattern evaluation of IEC 61672-2 (22 c).
    :ivar corrections_in_manual: Whether the correction data for the
        acoustical test of the frequency weighting came from the instruction
        manual (12.3) rather than from another manufacturer (12.4).
    :ivar measurements: The record the verdict was reached on.
    :ivar requirements: One :class:`SoundLevelMeterPeriodicRequirement` per
        requirement measured, in the order of the standard.
    :ivar features: The optional features declared for the meter (8.1);
        every one left at ``None`` when none were declared.
    """

    meter_class: int
    pattern_approval_public: bool
    corrections_in_manual: bool
    measurements: SoundLevelMeterPeriodicMeasurements
    requirements: tuple[SoundLevelMeterPeriodicRequirement, ...]
    features: SoundLevelMeterFeatures = field(default_factory=SoundLevelMeterFeatures)

    def __post_init__(self) -> None:
        """Refuse a declaration the class or the record contradicts.

        :raises ValueError: for frequency weighting C declared absent on a
            class 1 meter (IEC 61672-1 5.1.10), a feature declared absent, or
            taken away with the one it needs, that a result of the record
            shows, rows of Clause 17 for more level ranges than the meter
            has besides the reference one, or sound exposure level toneburst
            responses from a meter declared to neither measure sound
            exposure level nor display time-averaged sound level (18.2).
        """
        declared = self.features
        if self.meter_class == 1 and declared.c_weighting is False:
            msg = (
                "a class 1 meter provides frequency weighting C (IEC 61672-1 "
                "5.1.10): 'features.c_weighting' cannot be False."
            )
            raise ValueError(msg)
        for name in _FEATURES:
            if name == "sound_exposure_level" or self._declared(name) is not False:
                continue
            evidence = self._evidence(name)
            if evidence is not None:
                msg = f"{self._declared_absent(name)}, but {evidence}."
                raise ValueError(msg)
        self._check_range_count()
        if (
            declared.sound_exposure_level is False
            and self._state("time_averaged") is False
            and "E" in (self.measurements.toneburst_responses_db or {})
        ):
            msg = (
                "the record holds sound exposure level toneburst responses, but "
                "'features' declares a meter that neither measures sound "
                "exposure level nor displays time-averaged sound level (18.2)."
            )
            raise ValueError(msg)

    def requirement(self, name: str) -> SoundLevelMeterPeriodicRequirement:
        """The verdict on one requirement.

        :param name: One of :data:`SLM_PERIODIC_REQUIREMENTS`.
        :return: Its :class:`SoundLevelMeterPeriodicRequirement`.
        :raises KeyError: when that requirement was not measured.
        """
        for item in self.requirements:
            if item.name == name:
                return item
        msg = (
            f"{name!r} was not measured; measured: "
            f"{[r.name for r in self.requirements]}"
        )
        raise KeyError(msg)

    def _measured(self) -> set[str]:
        """The clauses the record holds, records included."""
        m = self.measurements
        present = {r.clause for r in self.requirements}
        if m.static_pressures_kpa is not None:
            present.add("7")
        if m.calibration_check_initial_db is not None:
            present.add("10")
        if (
            m.self_noise_microphone_db is not None
            or m.self_noise_electrical_db is not None
        ):
            present.add("11")
        return present

    @property
    def missing(self) -> tuple[str, ...]:
        """The clauses a complete periodic test holds that the record lacks.

        Clauses 7, 10, 11, 12, 13, 15, 16, 18 and 21 for every meter; 14.2 for
        a meter with C or Z, which class 1 always has (IEC 61672-1 5.1.10)
        and any clause of a class 2 record can show, a C-weighted peak result
        included (5.1.10); 14.3 for a meter with F that another clause shows
        to display S (an S toneburst of Clause 18) or time-averaged sound
        level (the overload test of Clause 20, 20.1); Clause 20 for a meter
        14.3 shows to display time-averaged sound level (``"eq"``), which
        20.1 tests; and each of them, Clause 17 and Clause 19 as well, for a
        meter whose :attr:`features` declare what the clause tests. A record
        cannot show that a meter lacks a feature: a feature neither declared
        nor shown is under :attr:`undeclared`, and a clause a feature
        declared absent takes out is under :attr:`not_applicable`.
        """
        required = list(_ALWAYS)
        if self._weightings_vs_a():
            required.append("14.2")
        if self._displays_owed():
            required.append("14.3")
        required.extend(
            clause
            for clause, (feature, _) in _CLAUSE_FEATURES.items()
            if self._state(feature)
        )
        present = self._measured()
        return tuple(sorted((c for c in required if c not in present), key=_clause_key))

    @property
    def not_applicable(self) -> tuple[tuple[str, str], ...]:
        """``(clause, why)`` for every clause the declared features take out.

        8.1 applies the periodic tests only to the features the meter has:
        14.2 to a meter with C or Z besides A, 14.3 to one with F and S or a
        time-averaged display, Clause 17 to one with more than one level
        range (17.1), Clause 19 to one that measures C-weighted peak sound
        level and Clause 20 to one that displays time-averaged sound level
        (20.1). A clause is here when :attr:`features` declare the meter
        without what it tests, or without the feature it needs: Clause 19
        for a meter declared without frequency weighting C (IEC 61672-1
        5.1.10). It is neither :attr:`missing` nor needed for a pass.
        """
        out: list[tuple[str, str]] = []
        if not self._weightings_vs_a() and all(
            self._state(f) is False for f in _WEIGHTING_FEATURES.values()
        ):
            out.append(
                ("14.2", "the meter provides no frequency weighting but A (14.1)")
            )
        if self._state("f_time_weighting") is False:
            out.append(
                (
                    "14.3",
                    "the meter has no F time weighting to compare the other "
                    "displays with (14.3)",
                )
            )
        elif (
            self._state("s_time_weighting") is False
            and self._state("time_averaged") is False
        ):
            out.append(
                (
                    "14.3",
                    "the meter displays neither S-time-weighted nor time-averaged "
                    "sound level (14.1)",
                )
            )
        out.extend(
            (clause, _IMPLIED_CLAUSE_WHY.get(feature, why))
            if getattr(self.features, feature) is None
            else (clause, why)
            for clause, (feature, why) in _CLAUSE_FEATURES.items()
            if self._state(feature) is False
        )
        return tuple(sorted(out, key=lambda item: _clause_key(item[0])))

    @property
    def undeclared(self) -> tuple[tuple[str, str], ...]:
        """``(feature, what is open)`` for every feature neither declared nor shown.

        A feature the record shows through a result is the meter's; one the
        record holds no result of may be absent from the meter or left out of
        the test, and only :attr:`features` can tell the two apart (8.1). Each
        such feature, a field of :class:`SoundLevelMeterFeatures`, keeps the
        test from passing until it is declared. The sound exposure level is
        not asked for when the meter displays time-averaged sound level, from
        which 18.2 calculates it anyway. The number of level ranges stays open
        for a meter Clause 17 shows to have several until it is declared, as
        17.4 covers every level range and 17.3 every one besides the
        reference level range.
        """
        questions = ((name, self._open_question(name)) for name in _FEATURES)
        return tuple((name, what) for name, what in questions if what is not None)

    def _open_question(self, name: str) -> str | None:
        """What is open about a feature, or ``None`` when nothing is."""
        state = self._state(name)
        if name == "level_ranges" and self.features.level_ranges is None:
            if state is None:
                return (
                    "it is not declared how many level ranges the meter has, and "
                    "Clause 17 tests a meter with more than one (8.1)"
                )
            return (
                "it is not declared how many level ranges the meter has, and "
                "17.4 tests every one and 17.3 every one besides the reference "
                "level range"
            )
        if state is not None or (
            name == "sound_exposure_level" and self._state("time_averaged")
        ):
            return None
        return (
            f"it is not declared whether the meter {_FEATURE_WHAT[name]}, "
            f"which {_FEATURE_TESTS[name]} (8.1)"
        )

    def _state(self, name: str) -> bool | None:
        """Whether the meter has a feature: declared, shown, or ``None``.

        The declaration decides when there is one (the record cannot contradict
        it, :meth:`__post_init__`); a class 1 meter has C; otherwise a result
        the record holds shows the feature, and nothing else does.
        """
        declared = self._declared(name)
        if declared is not None:
            return declared
        if name == "c_weighting" and self.meter_class == 1:
            return True
        return True if self._evidence(name) is not None else None

    def _declared(self, name: str) -> bool | None:
        """What the features declare of one, with what IEC 61672-1 implies.

        The number of level ranges reads as whether the meter has more than
        one. A feature left undeclared is absent with the one it needs
        (:data:`_IMPLIED_ABSENT`): no C-weighted peak sound level without
        frequency weighting C (5.1.10), no S without F (5.1.9).
        """
        if name == "level_ranges":
            count = self.features.level_ranges
            return None if count is None else count > 1
        declared: bool | None = getattr(self.features, name)
        if declared is None and name in _IMPLIED_ABSENT:
            needed, _ = _IMPLIED_ABSENT[name]
            if getattr(self.features, needed) is False:
                return False
        return declared

    def _declared_absent(self, name: str) -> str:
        """How the features say a feature is absent, for a refusal or a reason."""
        value = getattr(self.features, name)
        if value is not None:
            return f"'features.{name}' is {value!r}"
        needed, why = _IMPLIED_ABSENT[name]
        return f"'features.{needed}' is False, and {why}"

    def _check_range_count(self) -> None:
        """Clause 17 holds no more readings than the meter has level ranges.

        :raises ValueError: for rows that cover more level ranges besides the
            reference one than the meter has.
        """
        rows = self.measurements.range_linearity_deviations_db
        count = self.features.level_ranges
        if rows is None or count is None:
            return
        held = _other_ranges_held(rows)
        if held > count - 1:
            msg = (
                f"'range_linearity_deviations_db' covers {held} level ranges "
                f"besides the reference one, and 'features.level_ranges' gives "
                f"the meter {count}."
            )
            raise ValueError(msg)

    def _reason(self, name: str) -> str:
        """Why the verdict holds that the meter has a feature it holds it has."""
        if name == "c_weighting" and self.meter_class == 1:
            return (
                f"a class {self.meter_class} meter provides it "
                "(IEC 61672-1 5.1.9, 5.1.10)"
            )
        return self._evidence(name) or _DECLARED

    def _evidence(self, name: str) -> str | None:
        """What in the record shows that the meter has a feature, if anything."""
        finders: dict[str, Callable[[], str | None]] = {
            "c_weighting": self._c_evidence,
            "z_weighting": self._z_evidence,
            "f_time_weighting": self._f_evidence,
            "s_time_weighting": self._s_evidence,
            "time_averaged": self._time_averaged_evidence,
            "sound_exposure_level": self._exposure_evidence,
            "level_ranges": self._ranges_evidence,
            "c_weighted_peak": self._peak_evidence,
        }
        return finders[name]()

    def _c_evidence(self) -> str | None:
        """C: named by a clause, or owed by the C-weighted peak (5.1.10)."""
        if "C" in self._weightings_named():
            return "the record shows the meter provides it (8.1)"
        if self._state("c_weighted_peak"):
            return (
                "the meter measures C-weighted peak sound level (Clause 19), so it "
                "measures C-weighted time-averaged sound level too "
                "(IEC 61672-1 5.1.10)"
            )
        return None

    def _z_evidence(self) -> str | None:
        """Z: named by a clause."""
        if "Z" in self._weightings_named():
            return "the record shows the meter provides it (8.1)"
        return None

    def _f_evidence(self) -> str | None:
        """F: the reference of 14.3, an F toneburst, or the S time weighting."""
        m = self.measurements
        if m.time_weighting_at_1khz_deviations_db is not None:
            return _SHOWN_BY_14_3
        if "F" in (m.toneburst_responses_db or {}):
            return (
                "Clause 18 shows the meter provides it, with its maximum "
                "F-time-weighted toneburst response"
            )
        if self._state("s_time_weighting"):
            return (
                "a meter with the S time weighting has the F time weighting too "
                "(IEC 61672-1 5.1.9)"
            )
        return None

    def _s_evidence(self) -> str | None:
        """S: an S toneburst of Clause 18, or S compared with F in 14.3."""
        m = self.measurements
        if "S" in (m.toneburst_responses_db or {}):
            return (
                "Clause 18 shows the meter displays it, with its S-time-weighted "
                "toneburst response"
            )
        if "S" in (m.time_weighting_at_1khz_deviations_db or {}):
            return _SHOWN_BY_14_3
        return None

    def _time_averaged_evidence(self) -> str | None:
        """Time-averaged: the overload test (20.1), or 14.3 comparing it with F."""
        m = self.measurements
        if m.overload_difference_db is not None:
            return (
                "Clause 20 shows the meter displays it, as 20.1 tests the "
                "overload indication only on such a meter"
            )
        if "eq" in (m.time_weighting_at_1khz_deviations_db or {}):
            return _SHOWN_BY_14_3
        return None

    def _exposure_evidence(self) -> str | None:
        """Sound exposure level: the toneburst responses of Clause 18 hold it."""
        if "E" in (self.measurements.toneburst_responses_db or {}):
            return "Clause 18 holds its sound exposure level toneburst responses"
        return None

    def _ranges_evidence(self) -> str | None:
        """Several level ranges: Clause 17 was measured."""
        if self.measurements.range_linearity_deviations_db is not None:
            return "Clause 17 shows it"
        return None

    def _peak_evidence(self) -> str | None:
        """C-weighted peak: Clause 19 was measured."""
        if self.measurements.c_peak_differences_db is not None:
            return "Clause 19 shows it"
        return None

    @property
    def incomplete(self) -> tuple[tuple[str, str], ...]:
        """``(clause, what is short)`` for every measured clause short of a result.

        A clause not measured at all is in :attr:`missing` instead; see the
        module docstring for what 8.1 makes a complete test.
        """
        return tuple(
            (clause, what)
            for clause, what in (
                *self._environment_gaps(),
                *self._noise_gaps(),
                *self._weighting_gaps(),
                *self._display_gaps(),
                *self._linearity_gaps(),
                *self._range_gaps(),
                *self._toneburst_gaps(),
                *self._check_gaps(),
            )
        )

    def _environment_gaps(self) -> list[tuple[str, str]]:
        """7.2: readings at the start and the end."""
        m = self.measurements
        short = []
        for name in PERIODIC_TEST_ENVIRONMENT:
            row = getattr(m, name)
            if row is not None and len(row) < _MIN_ENVIRONMENT_READINGS:
                short.append(
                    (
                        "7",
                        f"'{name}' holds one reading, and 7.2 records the "
                        "start and the end of the tests",
                    )
                )
        return short

    def _noise_gaps(self) -> list[tuple[str, str]]:
        """11.1 and 11.2, the latter for every weighting the meter provides."""
        m = self.measurements
        if m.self_noise_microphone_db is None and m.self_noise_electrical_db is None:
            return []
        short = []
        if m.self_noise_microphone_db is None:
            short.append(
                ("11", "11.1, with the microphone installed, was not recorded")
            )
        if m.self_noise_electrical_db is None:
            short.append(
                (
                    "11",
                    "11.2, with the electrical input-signal device, was not recorded",
                )
            )
            return short
        short.extend(
            (
                "11",
                f"11.2 lacks frequency weighting {weighting}, and it records "
                "every weighting the meter provides",
            )
            for weighting in self._weightings_provided()
            if weighting not in m.self_noise_electrical_db
        )
        return short

    def _weighting_gaps(self) -> list[tuple[str, str]]:
        """13: every weighting provided, at every frequency; 14.2 for C and Z."""
        m = self.measurements
        short: list[tuple[str, str]] = []
        rows = m.electrical_weighting_deviations_db
        if rows is not None:
            short.extend(
                (
                    "13",
                    f"frequency weighting {weighting} was not tested, and "
                    f"{self._why_provided(weighting)}",
                )
                for weighting in self._weightings_provided()
                if weighting not in rows
            )
            frequencies = ELECTRICAL_TEST_FREQUENCIES_HZ[self.meter_class]
            for weighting, row in rows.items():
                gaps = [
                    _hz_label(f)
                    for f, v in zip(frequencies, row, strict=True)
                    if math.isnan(v)
                ]
                if gaps:
                    short.append(
                        (
                            "13",
                            f"{weighting}: not measured at {', '.join(gaps)}, and "
                            "13.4 requires it",
                        )
                    )
        at_1khz = m.weighting_at_1khz_deviations_db
        if at_1khz is not None:
            short.extend(
                (
                    "14.2",
                    f"{weighting} was not compared with A at 1 kHz, and 14.1 "
                    "records every weighting the meter provides",
                )
                for weighting in self._weightings_vs_a()
                if weighting not in at_1khz
            )
        return short

    def _weightings_named(self) -> set[str]:
        """The frequency weightings a clause of the record names by key."""
        m = self.measurements
        named: set[str] = set()
        for keyed in (
            m.electrical_weighting_deviations_db,
            m.self_noise_electrical_db,
            m.weighting_at_1khz_deviations_db,
        ):
            named |= set(keyed or {})
        return named

    def _weightings_provided(self) -> tuple[str, ...]:
        """The frequency weightings the meter provides, as declared or shown.

        A always and C for class 1, which IEC 61672-1 requires of the meter
        (5.1.9, 5.1.10); C for a meter that measures C-weighted peak sound
        level (Clause 19), which "shall also be able to measure C-weighted
        time-averaged sound levels" (5.1.10); every weighting any clause of
        the record names: the electrical tests of Clause 13, the
        self-generated noise of 11.2 and the comparison with A of 14.2; and
        every weighting :attr:`features` declare. 8.1 asks every one of them
        to be tested wherever the standard tests a weighting.
        """
        return tuple(
            w for w in _WEIGHTINGS if w == "A" or self._state(_WEIGHTING_FEATURES[w])
        )

    def _why_provided(self, weighting: str) -> str:
        """Why the verdict holds that the meter provides a weighting."""
        if weighting == "A":
            return (
                f"a class {self.meter_class} meter provides it "
                "(IEC 61672-1 5.1.9, 5.1.10)"
            )
        return self._reason(_WEIGHTING_FEATURES[weighting])

    def _weightings_vs_a(self) -> tuple[str, ...]:
        """The weightings besides A the meter provides, which 14.2 compares."""
        return tuple(w for w in self._weightings_provided() if w != "A")

    def _displays_owed(self) -> dict[str, str]:
        """The displays 14.3 compares with F that the meter has, and why.

        ``"S"`` when Clause 18 holds an S-time-weighted toneburst response,
        ``"eq"`` when Clause 20 holds the overload test, which 20.1 performs
        only on a meter that displays time-averaged sound level, and either
        when 14.3 itself holds it or :attr:`features` declare it; none for a
        meter declared without F, which 14.3 compares them with. A sound
        exposure level toneburst shows no time-averaged display: an
        integrating meter need not have one (IEC 61672-1 5.1.9).
        """
        if self._state("f_time_weighting") is False:
            return {}
        return {
            key: self._reason(feature)
            for key, feature in (("S", "s_time_weighting"), ("eq", "time_averaged"))
            if self._state(feature)
        }

    def _display_gaps(self) -> list[tuple[str, str]]:
        """14.3: every display another clause shows, compared with F (14.1)."""
        shows = self.measurements.time_weighting_at_1khz_deviations_db
        if shows is None:
            return []
        return [
            (
                "14.3",
                f"the {_DISPLAY_NAMES[key]} was not compared with F at 1 kHz, "
                f"and {why}",
            )
            for key, why in self._displays_owed().items()
            if key not in shows
        ]

    def _linearity_gaps(self) -> list[tuple[str, str]]:
        """16.3: steps from the starting point to the overload and the under-range.

        Without the anticipated level of each step, the linear operating range
        and the starting point the instruction manual states, and the levels
        of the first overload and under-range indications, the record cannot
        show that its steps cover the clause; with them, every step too wide
        and a starting point without a step are named.
        """
        m = self.measurements
        if m.linearity_deviations_db is None:
            return []
        levels = m.linearity_levels_db
        bounds = m.linear_operating_range_db
        start = m.linearity_starting_point_db
        overload = m.linearity_overload_level_db
        under_range = m.linearity_under_range_level_db
        if (
            levels is None
            or bounds is None
            or start is None
            or overload is None
            or under_range is None
        ):
            absent = [
                f"'{name}'"
                for name in ("linearity_levels_db", *_LINEARITY_PROCEDURE)
                if getattr(m, name) is None
            ]
            return [
                (
                    "16",
                    f"the record does not give {_in_words(absent)}, and without "
                    f"{'them' if len(absent) > 1 else 'it'} it cannot show that "
                    "the steps rise from the starting "
                    "point up to the first indication of overload and fall to the "
                    "first indication of under-range (16.3)",
                )
            ]
        return [
            ("16", what)
            for what in _linearity_steps_short(
                tuple(levels), (bounds[0], bounds[1]), start, overload, under_range
            )
        ]

    def _range_gaps(self) -> list[tuple[str, str]]:
        """17.4 on every level range, and 17.3 on every one besides the reference.

        Read against the number of level ranges the features declare; while
        it is not declared, :attr:`undeclared` holds the question instead.
        17.4 reads "for each level range", the reference one as well, where
        the level it sets is not the reference sound level 17.2 set, so a
        record without that reading is short of it.
        """
        rows = self.measurements.range_linearity_deviations_db
        count = self.features.level_ranges
        if rows is None or count is None:
            return []
        short = [
            ("17", f"{key} was not recorded: {_RANGE_READING_NAMES[key]}")
            for key in _RANGE_READINGS
            if key not in rows
        ]
        held = _other_ranges_held(rows)
        if held < count - 1:
            short.append(
                (
                    "17",
                    f"the record holds {held} of the {count - 1} level ranges "
                    "besides the reference one, and 17.3 and 17.4 test every one",
                )
            )
        gaps = [
            "the reference level range" if k == 0 else f"range {k}"
            for k, v in enumerate(rows.get("17.4", ()))
            if math.isnan(v)
        ]
        if gaps:
            short.append(
                (
                    "17",
                    f"17.4 was not measured on {_in_words(gaps)}, and it tests "
                    "every level range, the reference one included",
                )
            )
        return short

    def _toneburst_gaps(self) -> list[tuple[str, str]]:
        """18: every duration of a measurement, and every measurement owed."""
        rows = self.measurements.toneburst_responses_db
        if rows is None:
            return []
        short = []
        for key, row in rows.items():
            gaps = [
                _ms_label(d)
                for d, v in zip(TONEBURST_TEST_DURATIONS_MS[key], row, strict=True)
                if math.isnan(v)
            ]
            if gaps:
                short.append(
                    (
                        "18",
                        f"{key}: not measured at {', '.join(gaps)}, and 18.5 to "
                        "18.7 require it",
                    )
                )
        owed = self._tonebursts_owed()
        short.extend(
            (
                "18",
                f"the {_TONEBURST_NAMES[key]} response was not measured, and "
                f"{owed[key]} (18.2)",
            )
            for key in _TONEBURST_KEYS
            if key in owed and key not in rows
        )
        return short

    def _tonebursts_owed(self) -> dict[str, str]:
        """The toneburst measurements of 18.2 the meter owes, and why.

        The maximum F- and S-time-weighted responses for a meter with those
        time weightings, and the sound exposure level for one that measures
        it or displays time-averaged sound level, from which 18.2 calculates
        it.
        """
        owed = {
            key: self._reason(feature)
            for key, feature in (("F", "f_time_weighting"), ("S", "s_time_weighting"))
            if self._state(feature)
        }
        if self._state("sound_exposure_level"):
            owed["E"] = self._reason("sound_exposure_level")
        elif self._state("time_averaged"):
            owed["E"] = _EXPOSURE_FROM_TIME_AVERAGE
        return owed

    def _check_gaps(self) -> list[tuple[str, str]]:
        """19 and 20: the yes/no observations that go with the results."""
        m = self.measurements
        short = []
        if m.c_peak_differences_db is not None:
            gaps = [
                _PEAK_LABELS[k]
                for k, v in enumerate(m.c_peak_differences_db)
                if math.isnan(v)
            ]
            if gaps:
                short.append(
                    ("19", f"not measured for {', '.join(gaps)}, and 19.1 requires it")
                )
            if m.c_peak_overload_indicated is None:
                short.append(
                    (
                        "19",
                        "whether the signals caused an overload indication was not "
                        "recorded (19.3, 19.5)",
                    )
                )
        if m.overload_difference_db is not None and m.overload_latched is None:
            short.append(
                (
                    "20",
                    "whether the overload indicator latched on was not recorded (20.5)",
                )
            )
        return short

    @property
    def conditions_outside(self) -> tuple[str, ...]:
        """The environmental readings outside the ranges of 7.1.

        Periodic tests "shall be performed within" 80 kPa to 105 kPa, 20 °C to
        26 °C and 25 % to 70 % (7.1); a test outside them is not a valid
        periodic test, whatever its results.
        """
        m = self.measurements
        return tuple(
            f"{name} = {value:g}, outside {low:g} to {high:g}"
            for name, (low, high) in PERIODIC_TEST_ENVIRONMENT.items()
            for value in getattr(m, name) or ()
            if value < low or value > high
        )

    @property
    def unusable(self) -> tuple[tuple[str, str], ...]:
        """``(clause, result)`` for every result 4.3 forbids using."""
        return tuple(
            (r.clause, label) for r in self.requirements for label in r.unusable
        )

    @property
    def over_maximum_by_correction_data(self) -> tuple[tuple[str, str], ...]:
        """``(clause, result)`` for every result over its maximum only by 4.4.

        Its uncertainty exceeds the maximum only because it includes the
        uncertainty of the manufacturer's correction data: the test
        proceeds, and the result is one that did not conform (4.4), for the
        reason the NOTE to 22 t) gives. Each is in :attr:`failed` as well.
        """
        return tuple(
            (r.clause, label)
            for r in self.requirements
            for label in r.over_maximum_by_correction_data
        )

    @property
    def failed(self) -> tuple[tuple[str, str], ...]:
        """``(clause, result)`` for every result that did not conform or check failed.

        A result outside its limits with an acceptable uncertainty, a result
        over its maximum only by the manufacturer's correction data (4.4),
        and a failed yes/no check.
        """
        return tuple((r.clause, label) for r in self.requirements for label in r.failed)

    @property
    def passes(self) -> bool:
        """Whether the meter completed the periodic tests successfully.

        Every clause a complete test holds was measured on everything it
        requires (nothing :attr:`missing` or :attr:`incomplete`), every
        optional feature is declared or shown (nothing :attr:`undeclared`),
        the tests were within the environmental conditions of 7.1, and every
        result conforms: no
        deviation outside its limits, no uncertainty above its maximum and no
        failed check.
        """
        return (
            bool(self.requirements)
            and not self.missing
            and not self.incomplete
            and not self.undeclared
            and not self.conditions_outside
            and all(r.passes for r in self.requirements)
        )

    @property
    def statement(self) -> str:
        """The statement IEC 61672-3:2013 Clause 22 prescribes for the result.

        In this order, the first that applies: a notice when the tests were
        not performed within the conditions of 7.1, as tests outside them are
        not periodic tests to IEC 61672-3, whatever their results, and none
        of 22 r), s) and t) is theirs; 22 t) when a result exceeds its limits, a
        check fails or a result exceeds its maximum only by the uncertainty
        of the manufacturer's correction data (4.4), followed by the tests
        not completed and why, as a result that did not conform settles the
        verdict whatever the others are; the 4.3 notice when results cannot
        be used; a notice naming the clauses not measured, what a clause
        lacks and the features not declared, as 22 r) and s) both need the
        results of all the periodic tests; and otherwise 22 r) with a public
        pattern approval and correction data from the manual, or 22 s)
        without either, which carries the caveat of Clause 1.
        """
        y = self.meter_class
        if self.conditions_outside:
            return (
                "The periodic tests of IEC 61672-3:2013 were not performed within "
                "the environmental conditions of 7.1 (80 kPa to 105 kPa, 20 °C to "
                f"26 °C, 25 % to 70 %): {'; '.join(self.conditions_outside)}."
            )
        if self.failed:
            by_clause = {r.clause: r for r in self.requirements}
            reasons = "; ".join(
                f"{_clause_label(clause)}, {label}: "
                f"{by_clause[clause].failure_reason(label)}"
                for clause, label in self.failed
            )
            return (
                f"The sound level meter submitted for periodic testing did not "
                f"successfully complete the class {y} tests of IEC 61672-3:2013. "
                f"The sound level meter did not conform to the class {y} "
                f"specifications of IEC 61672-1:2013. Tests not successfully "
                f"completed: {reasons}."
            )
        if self.unusable:
            clauses = ", ".join(sorted({c for c, _ in self.unusable}, key=_clause_key))
            return (
                f"The results of clause {clauses} cannot be used to evaluate "
                "conformance for periodic testing: their actual expanded "
                "uncertainty exceeds the maximum permitted by IEC 61672-1:2013 "
                "Annex B (IEC 61672-3:2013, 4.3)."
            )
        if self.missing or self.incomplete or self.undeclared:
            parts = [f"{_clause_label(c)} was not measured" for c in self.missing]
            if self.missing:
                parts[-1] += (
                    ", and every feature IEC 61672-1 requires that the meter "
                    "provides shall be tested (8.1)"
                )
            parts.extend(f"{clause}: {what}" for clause, what in self.incomplete)
            parts.extend(what for _, what in self.undeclared)
            return (
                "The periodic tests of IEC 61672-3:2013 are incomplete: "
                f"{'; '.join(parts)}."
            )
        return self._pass_statement()

    def _pass_statement(self) -> str:
        """22 r) or 22 s), verbatim with the class and the year filled in."""
        y = self.meter_class
        head = (
            "The sound level meter submitted for testing successfully completed "
            "the periodic tests of IEC 61672-3:2013, for the environmental "
            "conditions under which the tests were performed."
        )
        if self.pattern_approval_public and self.corrections_in_manual:
            return (
                f"{head} As evidence was publicly available, from an independent "
                "testing organization responsible for approving the results of "
                "pattern-evaluation tests performed in accordance with "
                "IEC 61672-2:2013, to demonstrate that the model of sound level "
                f"meter fully conformed to the class {y} specifications in "
                "IEC 61672-1:2013, the sound level meter submitted for testing "
                f"conforms to the class {y} specifications of IEC 61672-1:2013."
            )
        return (
            f"{head} However, no general statement or conclusion can be made "
            "about conformance of the sound level meter to the full "
            "specifications of IEC 61672-1:2013 because (a) evidence was not "
            "publicly available, from an independent testing organization "
            "responsible for pattern approvals, to demonstrate that the model of "
            f"sound level meter fully conformed to the class {y} specifications "
            "in IEC 61672-1:2013 or correction data for acoustical test of "
            "frequency weighting were not provided in the Instruction Manual and "
            "(b) because the periodic tests of IEC 61672-3:2013 cover only a "
            "limited subset of the specifications in IEC 61672-1:2013."
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a SoundLevelMeterPeriodicVerification has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw every graded clause at its margin to its acceptance limits.

        One slot per clause, however many results it holds: each result's
        distance from its deviation to the nearer acceptance limit is a dash,
        and the result that decides the clause is marked over them with its
        actual uncertainty as error bar; a result at or above zero lies
        within its limits. The mark is a cross for a result that did not
        conform, one over its maximum only by the manufacturer's correction
        data included (4.4), hollow for one 4.3 forbids using, and otherwise
        a diamond at the result nearest its limit. Each requirement's own
        :meth:`SoundLevelMeterPeriodicRequirement.plot` draws its results one
        by one.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the verdict markers.
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_slm_periodic_verification

        check_language(language)
        return plot_slm_periodic_verification(self, ax, language=language, **kwargs)


#: The reason 22 t) gives for a result over its maximum only by the
#: manufacturer's correction data, in the words of its NOTE (4.4).
_CORRECTION_DATA_REASON = (
    "the actual expanded uncertainty exceeded the maximum permitted only "
    "because the manufacturer-provided uncertainty for the free-field or "
    "random-incidence correction data was a significant part of the "
    "laboratory's uncertainty budget (4.4)"
)

#: The displays of 14.3 as the verdict names them.
_DISPLAY_NAMES: dict[str, str] = {
    "S": "S-time-weighted indication",
    "eq": "time-averaged indication",
}

#: The toneburst measurements as the statement names them.
_TONEBURST_NAMES: dict[str, str] = {
    "F": "maximum F-time-weighted",
    "S": "maximum S-time-weighted",
    "E": "sound exposure level",
}

#: The C-weighted peak signals of 19.1, in the order of the record.
_PEAK_LABELS: tuple[str, ...] = (
    "one cycle, 8 kHz",
    "positive half cycle, 500 Hz",
    "negative half cycle, 500 Hz",
)

#: The checks of Clauses 16, 19 and 20, and what 22 t) says when one fails.
_RANGE_CHECK = (
    "no overload or under-range indication within the linear operating range (16.4)"
)
_PEAK_CHECK = "no overload indication (19.3, 19.5)"
_LATCH_CHECK = "latching of the overload indicator (20.5)"
_CHECK_FAILURES: dict[str, str] = {
    _RANGE_CHECK: (
        "an indication of overload or under-range was displayed within the "
        "linear operating range stated in the Instruction Manual"
    ),
    _PEAK_CHECK: (
        "the C-weighted peak test signals caused an indication of an overload condition"
    ),
    _LATCH_CHECK: (
        "the overload indicator did not latch on as specified in IEC 61672-1"
    ),
}


def _clause_key(clause: str) -> tuple[int, ...]:
    """Sort ``"14.2"`` after ``"13"`` and before ``"15"``."""
    return tuple(int(part) for part in clause.split("."))


def _hz_label(frequency_hz: float) -> str:
    """``63 Hz`` or ``8 kHz``."""
    if frequency_hz >= _HZ_PER_KHZ:
        return f"{frequency_hz / _HZ_PER_KHZ:g} kHz"
    return f"{frequency_hz:g} Hz"


def _ms_label(duration_ms: float) -> str:
    """``200 ms`` or ``0.25 ms``."""
    return f"{duration_ms:g} ms"


def _in_words(items: Sequence[str]) -> str:
    """``a``, ``a and b`` or ``a, b and c``, of at least one item."""
    head, last = items[:-1], items[-1]
    return f"{', '.join(head)} and {last}" if head else last


def _steps_too_wide(
    points: Sequence[float], coarse: Callable[[float], bool], end: str, rule: str
) -> list[str]:
    """Each step between consecutive points wider than 16.3 allows there.

    :param points: The starting point, the steps in the order 16.3 takes them
        and the first overload or under-range indication, last.
    :param coarse: Whether a step from a level may be 5 dB wide: the level is
        not yet within 5 dB of the boundary.
    :param end: What the last point is, as the statement names it.
    :param rule: The rule of 16.3 for that direction, as the statement says it.
    """
    wide = []
    for k, (a, b) in enumerate(itertools.pairwise(points), 2):
        allowed = _COARSE_STEP_DB if coarse(a) else _FINE_STEP_DB
        if abs(b - a) > allowed + _STEP_ROUNDING_DB:
            to = f"{end} at {b:g} dB" if k == len(points) else f"{b:g} dB"
            wide.append(f"the steps go from {a:g} dB to {to}, and {rule}")
    return wide


def _linearity_steps_short(
    levels: tuple[float, ...],
    bounds: tuple[float, float],
    start: float,
    overload: float,
    under_range: float,
) -> list[str]:
    """What the steps of Clause 16 leave out of 16.3, each as the statement says it.

    16.3 rises from the starting point in 5 dB steps until within 5 dB of the
    upper boundary of the linear operating range, then in 1 dB steps up to,
    but not including, the first indication of overload, and falls the same
    way to the first indication of under-range. Smaller steps cover more and
    are not short of it.
    """
    lower, upper = bounds
    short = []
    if all(abs(level - start) > _STEP_ROUNDING_DB for level in levels):
        short.append(
            f"no step is at the starting point of {start:g} dB the instruction "
            "manual gives (16.2)"
        )
    rising = [start, *sorted(v for v in levels if v > start), overload]
    falling = [
        start,
        *sorted((v for v in levels if v < start), reverse=True),
        under_range,
    ]
    short.extend(
        _steps_too_wide(
            rising,
            lambda level: level < upper - _COARSE_STEP_DB,
            "the first indication of overload",
            f"16.3 rises by 5 dB at most until within 5 dB of the upper boundary "
            f"of the linear operating range, {upper:g} dB, and by 1 dB from there "
            "up to the first indication of overload",
        )
    )
    short.extend(
        _steps_too_wide(
            falling,
            lambda level: level > lower + _COARSE_STEP_DB,
            "the first indication of under-range",
            f"16.3 falls by 5 dB at most until within 5 dB of the lower boundary "
            f"of the linear operating range, {lower:g} dB, and by 1 dB from there "
            "down to the first indication of under-range",
        )
    )
    return short


def _max_uncertainty_db(requirement: str, frequency_hz: float | None = None) -> float:
    """The maximum of :data:`IEC61672_TABLE_B1` for a requirement.

    :param requirement: One of :data:`SLM_PERIODIC_REQUIREMENTS`.
    :param frequency_hz: The nominal test frequency, for the frequency
        weightings, whose maximum Table B.1 bands by frequency.
    """
    wanted = _B1_ROWS[requirement]
    for row in IEC61672_TABLE_B1:
        if row.requirement == wanted and (
            frequency_hz is None or row.contains(frequency_hz)
        ):
            return row.max_uncertainty
    # Unreachable for the requirements and frequencies of IEC 61672-3; kept so
    # a caller that drifts off the table is told, not handed a neighbour.
    msg = f"Table B.1 prints no maximum for {wanted!r} at {frequency_hz!r} Hz."
    raise ValueError(msg)


def _weighting_limits(meter_class: int) -> dict[float, tuple[float, float]]:
    """IEC 61672-1:2013 Table 3 for a class: nominal frequency -> (lower, upper).

    Read through :func:`phonometry.filters.weighting_class_limits`, which
    publishes the table, rather than transcribed a second time.
    """
    from ..filters.weighting_compliance import weighting_class_limits

    frequencies, lower, upper = weighting_class_limits(meter_class)
    return {
        float(f): (float(lo), float(up))
        for f, lo, up in zip(frequencies, lower, upper, strict=True)
    }


def _simple(
    name: str,
    labels: Sequence[str],
    deviations: Sequence[float],
    uncertainties: Sequence[float],
    limits: float | tuple[float, float],
    *,
    checks: tuple[tuple[str, bool], ...] = (),
) -> SoundLevelMeterPeriodicRequirement:
    """A requirement whose results share one limit and one maximum."""
    maximum = _max_uncertainty_db(name)
    return SoundLevelMeterPeriodicRequirement(
        name=name,
        clause=_CLAUSES[name],
        tables=_TABLES[name],
        labels=tuple(labels),
        verifications=tuple(
            verify_conformance(
                d, uncertainty=u, acceptance_limits=limits, max_uncertainty=maximum
            )
            for d, u in zip(deviations, uncertainties, strict=True)
        ),
        checks=checks,
    )


def _weighting_requirement(
    name: str,
    rows: Mapping[str, Sequence[float]],
    rows_u: Mapping[str, Sequence[float]],
    frequencies: tuple[float, ...],
    meter_class: int,
    rows_u_split: Mapping[str, Sequence[float]] | None = None,
) -> SoundLevelMeterPeriodicRequirement:
    """12 or 13: Table 3 at each nominal frequency, the maximum by band.

    ``rows_u_split`` holds the uncertainties without the manufacturer's
    correction data, when given: a result whose total exceeds its maximum and
    whose uncertainty without that data does not is a result of 4.4.
    """
    table = _weighting_limits(meter_class)
    labels: list[str] = []
    verifications: list[ConformanceVerification] = []
    over: list[str] = []
    for weighting, row in rows.items():
        split = rows_u_split[weighting] if rows_u_split is not None else None
        for k, (f, d, u) in enumerate(
            zip(frequencies, row, rows_u[weighting], strict=True)
        ):
            if math.isnan(d):
                continue
            maximum = _max_uncertainty_db(name, f)
            verification = verify_conformance(
                d, uncertainty=u, acceptance_limits=table[f], max_uncertainty=maximum
            )
            verifications.append(verification)
            prefix = f"{weighting}, " if weighting else ""
            labels.append(f"{prefix}{_hz_label(f)}")
            if (
                split is not None
                and not verification.uncertainty_within_maximum
                and verify_conformance(
                    d,
                    uncertainty=split[k],
                    acceptance_limits=table[f],
                    max_uncertainty=maximum,
                ).uncertainty_within_maximum
            ):
                over.append(labels[-1])
    return SoundLevelMeterPeriodicRequirement(
        name=name,
        clause=_CLAUSES[name],
        tables=_TABLES[name],
        labels=tuple(labels),
        verifications=tuple(verifications),
        over_maximum_by_correction_data=tuple(over),
    )


def _electrical_weighting(
    m: SoundLevelMeterPeriodicMeasurements, meter_class: int
) -> SoundLevelMeterPeriodicRequirement | None:
    """13: every weighting at the frequencies of 13.4 for the class."""
    rows = m.electrical_weighting_deviations_db
    rows_u = m.electrical_weighting_uncertainties_db
    if rows is None or rows_u is None:
        return None
    frequencies = ELECTRICAL_TEST_FREQUENCIES_HZ[meter_class]
    for weighting, row in rows.items():
        if len(row) != len(frequencies):
            msg = (
                f"'electrical_weighting_deviations_db[{weighting!r}]' must hold "
                f"{len(frequencies)} results for class {meter_class}, at "
                f"{frequencies} Hz (13.4); got {len(row)}."
            )
            raise ValueError(msg)
    return _weighting_requirement(
        "electrical_weighting",
        rows,
        rows_u,
        frequencies,
        meter_class,
        m.electrical_weighting_uncertainties_without_correction_data_db,
    )


def _toneburst(
    m: SoundLevelMeterPeriodicMeasurements, meter_class: int
) -> SoundLevelMeterPeriodicRequirement | None:
    """18: the deviation of each response from Table 4, its own limits."""
    rows = m.toneburst_responses_db
    rows_u = m.toneburst_uncertainties_db
    if rows is None or rows_u is None:
        return None
    labels: list[str] = []
    verifications: list[ConformanceVerification] = []
    maximum = _max_uncertainty_db("toneburst")
    for key, row in rows.items():
        table = {r.duration_ms: r for r in IEC61672_TABLE_4[key]}
        for duration, value, u in zip(
            TONEBURST_TEST_DURATIONS_MS[key], row, rows_u[key], strict=True
        ):
            if math.isnan(value):
                continue
            reference = table[duration]
            verifications.append(
                verify_conformance(
                    value - reference.reference_response_db,
                    uncertainty=u,
                    acceptance_limits=reference.limits_db(meter_class),
                    max_uncertainty=maximum,
                )
            )
            labels.append(f"{key}, {_ms_label(duration)}")
    return SoundLevelMeterPeriodicRequirement(
        name="toneburst",
        clause=_CLAUSES["toneburst"],
        tables=_TABLES["toneburst"],
        labels=tuple(labels),
        verifications=tuple(verifications),
    )


def _c_peak(
    m: SoundLevelMeterPeriodicMeasurements, meter_class: int
) -> SoundLevelMeterPeriodicRequirement | None:
    """19: the deviation of each difference from Table 5, and no overload."""
    values = m.c_peak_differences_db
    spread = m.c_peak_uncertainties_db
    if values is None or spread is None:
        return None
    labels: list[str] = []
    verifications: list[ConformanceVerification] = []
    maximum = _max_uncertainty_db("c_peak")
    for label, row_index, value, u in zip(
        _PEAK_LABELS, _C_PEAK_ROWS, values, spread, strict=True
    ):
        if math.isnan(value):
            continue
        reference = IEC61672_TABLE_5[row_index]
        verifications.append(
            verify_conformance(
                value - reference.reference_difference_db,
                uncertainty=u,
                acceptance_limits=reference.limits_db(meter_class),
                max_uncertainty=maximum,
            )
        )
        labels.append(label)
    indicated = m.c_peak_overload_indicated
    no_overload = None if indicated is None else not indicated
    return SoundLevelMeterPeriodicRequirement(
        name="c_peak",
        clause=_CLAUSES["c_peak"],
        tables=_TABLES["c_peak"],
        labels=tuple(labels),
        verifications=tuple(verifications),
        checks=_held_checks((_PEAK_CHECK, no_overload)),
    )


def _keyed_requirement(
    name: str,
    values: Mapping[str, float] | None,
    spread: Mapping[str, float] | None,
    limit: float,
    names: Mapping[str, str],
) -> SoundLevelMeterPeriodicRequirement | None:
    """14.2 or 14.3: one result per key, one limit and one maximum."""
    if values is None or spread is None:
        return None
    return _simple(
        name,
        [names[k] for k in values],
        list(values.values()),
        [spread[k] for k in values],
        limit,
    )


def _scalar_requirement(
    name: str,
    value: float | None,
    uncertainty: float | None,
    limit: float,
    label: str,
    *,
    checks: tuple[tuple[str, bool], ...] = (),
) -> SoundLevelMeterPeriodicRequirement | None:
    """15, 20 or 21: one result."""
    if value is None or uncertainty is None:
        return None
    return _simple(name, [label], [value], [uncertainty], limit, checks=checks)


def _sequence_requirement(
    name: str,
    values: Sequence[float] | None,
    spread: Sequence[float] | None,
    limit: float,
    labels: Sequence[str],
    *,
    checks: tuple[tuple[str, bool], ...] = (),
) -> SoundLevelMeterPeriodicRequirement | None:
    """16: one result per step, one limit and one maximum."""
    if values is None or spread is None:
        return None
    return _simple(name, labels, values, spread, limit, checks=checks)


def _held_checks(*checks: tuple[str, bool | None]) -> tuple[tuple[str, bool], ...]:
    """``(check, held)`` for each yes/no check the record answers.

    :param checks: ``(check, held)`` pairs, ``held`` ``None`` for a check the
        record does not answer, which is left out.
    """
    return tuple((name, held) for name, held in checks if held is not None)


def _linear_range_clear(m: SoundLevelMeterPeriodicMeasurements) -> bool | None:
    """16.4: no overload or under-range indication within the linear operating range.

    The instruction manual states the range as the one "over which sound
    levels can be measured without display of under-range or overload
    conditions" (IEC 61672-1 5.6.10), and 16.4 holds the deviations to the
    limits over its whole extent; an indication inside it leaves part of the
    range where the meter cannot be read.

    :return: Whether both indications lie outside the range, or ``None`` when
        the record does not give the range and both indications.
    """
    bounds = m.linear_operating_range_db
    overload = m.linearity_overload_level_db
    under_range = m.linearity_under_range_level_db
    if bounds is None or overload is None or under_range is None:
        return None
    return under_range < bounds[0] and overload > bounds[1]


def _range_name(k: int) -> str:
    """The level range of a reading of Clause 17, as its label names it.

    :param k: 0 for the reference level range, which only 17.4 reads, and
        from 1 for the others, in the order of the record.
    """
    return _RANGE_LABEL_REFERENCE if k == 0 else f"range {k}"


def _range_linearity(
    m: SoundLevelMeterPeriodicMeasurements, meter_class: int
) -> SoundLevelMeterPeriodicRequirement | None:
    """17: each reading of 17.3 and 17.4, in order.

    A reading is labelled with its subclause and the level range it was taken
    on: ``"17.4, reference range"`` for the reading of 17.4 on the reference
    level range, and ``"range k"`` for the others, numbered among the ranges
    besides the reference one in the order of the record.
    """
    rows = m.range_linearity_deviations_db
    rows_u = m.range_linearity_uncertainties_db
    if rows is None or rows_u is None:
        return None
    labels: list[str] = []
    values: list[float] = []
    spread: list[float] = []
    for key, row in rows.items():
        first = 1 if key == "17.3" else 0
        for k, (value, u) in enumerate(zip(row, rows_u[key], strict=True), first):
            if not math.isnan(value):
                labels.append(f"{key}, {_range_name(k)}")
                values.append(value)
                spread.append(u)
    return _simple(
        "range_linearity", labels, values, spread, _LINEARITY_LIMITS_DB[meter_class]
    )


#: The labels of the 14.2 and 14.3 results, by key.
_WEIGHTING_VS_A_LABELS = MappingProxyType({"C": "LC - LA", "Z": "LZ - LA"})
_TIME_WEIGHTING_VS_F_LABELS = MappingProxyType({"S": "LAS - LAF", "eq": "LAeq - LAF"})


def verify_sound_level_meter_periodic(
    meter_class: int,
    measurements: SoundLevelMeterPeriodicMeasurements,
    *,
    pattern_approval_public: bool = False,
    corrections_in_manual: bool = False,
    features: SoundLevelMeterFeatures | None = None,
) -> SoundLevelMeterPeriodicVerification:
    """Grade the periodic tests of a sound level meter, IEC 61672-3:2013.

    Each requirement measured is judged result by result by the conformance
    rule of IEC TC 29 (4.1), with the acceptance limits IEC 61672-1:2013
    prints for it and the maximum-permitted uncertainties of its Table B.1;
    see the module docstring for which clause reads which. The verdict passes
    when the record is complete, the tests were performed within the
    conditions of 7.1 and every result conforms; its
    :attr:`~SoundLevelMeterPeriodicVerification.statement` is the text
    Clause 22 prescribes for the case. A frequency-weighting result whose
    uncertainty exceeds its maximum only because of the manufacturer's
    correction data is a result that did not conform, by 4.4, when the record
    gives the uncertainty without that data. The optional features of the
    meter (8.1) are what ``features`` declares and what the record shows; a
    feature neither declared nor shown keeps the verdict from passing, as a
    record that left a test out reads the same as a meter without the
    feature.

    :param meter_class: The class the meter is tested as, 1 or 2.
    :param measurements: The laboratory's results and uncertainties.
    :param pattern_approval_public: Whether evidence is publicly available,
        from an independent testing organization, that the model passed the
        pattern evaluation of IEC 61672-2. Without it a passing meter still
        supports no general conclusion about IEC 61672-1 (Clause 1), and the
        statement is 22 s) rather than 22 r).
    :param corrections_in_manual: Whether the correction data for the
        acoustical test of the frequency weighting were provided in the
        instruction manual (12.3). Data from another source (12.4) lead to
        22 s) as well, and so does a source not declared: 12.5 has the
        laboratory state it, and 22 r) is written only on both declarations.
    :param features: Which optional design features of IEC 61672-1 the meter
        has, and how many level ranges, as its instruction manual states
        them: a :class:`SoundLevelMeterFeatures`, or ``None`` for none
        declared. A feature declared present owes its tests, and one
        declared absent takes its clauses out of the test.
    :return: A :class:`SoundLevelMeterPeriodicVerification`.
    :raises ValueError: for a class other than 1 or 2, a Clause 13 row of the
        wrong length for the class, a record with nothing graded in it, or
        ``features`` that the class or a result of the record contradicts.
    """
    if not is_class_designation(meter_class, _CLASSES):
        msg = f"'meter_class' must be 1 or 2 (IEC 61672-1:2013); got {meter_class!r}."
        raise ValueError(msg)
    cls = int(meter_class)
    m = measurements
    acoustic = None
    if (
        m.acoustic_weighting_deviations_db is not None
        and m.acoustic_weighting_uncertainties_db is not None
    ):
        split = m.acoustic_weighting_uncertainties_without_correction_data_db
        acoustic = _weighting_requirement(
            "acoustic_weighting",
            {"": m.acoustic_weighting_deviations_db},
            {"": m.acoustic_weighting_uncertainties_db},
            ACOUSTIC_TEST_FREQUENCIES_HZ,
            cls,
            {"": split} if split is not None else None,
        )
    levels = m.linearity_levels_db
    linearity_labels = (
        [f"{level:g} dB" for level in levels]
        if levels is not None
        else [f"step {n}" for n in range(1, len(m.linearity_deviations_db or ()) + 1)]
    )
    candidates = (
        acoustic,
        _electrical_weighting(m, cls),
        _keyed_requirement(
            "weighting_at_1khz",
            m.weighting_at_1khz_deviations_db,
            m.weighting_at_1khz_uncertainties_db,
            _WEIGHTING_AT_1KHZ_LIMIT_DB,
            _WEIGHTING_VS_A_LABELS,
        ),
        _keyed_requirement(
            "time_weighting_at_1khz",
            m.time_weighting_at_1khz_deviations_db,
            m.time_weighting_at_1khz_uncertainties_db,
            _TIME_WEIGHTING_AT_1KHZ_LIMIT_DB,
            _TIME_WEIGHTING_VS_F_LABELS,
        ),
        _scalar_requirement(
            "long_term_stability",
            m.long_term_stability_db,
            m.long_term_stability_uncertainty_db,
            _STABILITY_LIMITS_DB[cls],
            "final - initial",
        ),
        _sequence_requirement(
            "level_linearity",
            m.linearity_deviations_db,
            m.linearity_uncertainties_db,
            _LINEARITY_LIMITS_DB[cls],
            linearity_labels,
            checks=_held_checks((_RANGE_CHECK, _linear_range_clear(m))),
        ),
        _range_linearity(m, cls),
        _toneburst(m, cls),
        _c_peak(m, cls),
        _scalar_requirement(
            "overload",
            m.overload_difference_db,
            m.overload_uncertainty_db,
            _OVERLOAD_LIMIT_DB,
            "positive - negative",
            checks=_held_checks((_LATCH_CHECK, m.overload_latched)),
        ),
        _scalar_requirement(
            "high_level_stability",
            m.high_level_stability_db,
            m.high_level_stability_uncertainty_db,
            _STABILITY_LIMITS_DB[cls],
            "final - initial",
        ),
    )
    requirements = tuple(r for r in candidates if r is not None)
    if not requirements:
        msg = "'measurements' holds no result to grade."
        raise ValueError(msg)
    return SoundLevelMeterPeriodicVerification(
        meter_class=cls,
        pattern_approval_public=bool(pattern_approval_public),
        corrections_in_manual=bool(corrections_in_manual),
        measurements=m,
        requirements=requirements,
        features=features if features is not None else SoundLevelMeterFeatures(),
    )
