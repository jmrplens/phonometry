#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Calibration of a measurement microphone by comparison with a reference
microphone (IEC 61094-5:2016, pressure; IEC 61094-8:2012, free field).

A working standard microphone is not calibrated by reciprocity. It is put
beside, or in place of, a reference microphone whose sensitivity is already
known, both are exposed to the same sound pressure, and the ratio of their
open-circuit output voltages carries the reference's sensitivity over to it.
IEC 61094-5 does this in a pressure field, in a coupler or a jig; IEC 61094-8
does it in a free field, in an anechoic room or behind a time window. Annex D
of the first part writes the model once for both:

.. math::

   M_\mathrm{test} = M_\mathrm{ref}\,\frac{R_V}{R_P}

where :math:`R_V` is the ratio of the output voltages of the test and
reference microphones and :math:`R_P` that of the effective sound pressures
acting on them, reduced to unity by the procedure and the corrections. In
sensitivity levels, the form every function here computes,

.. math::

   L_\mathrm{test} = L_\mathrm{ref} + 20\lg R_V - 20\lg R_P + \sum_j C_j

with :math:`C_j` the corrections the part asks for.

**Simultaneous excitation** (IEC 61094-5 5.1.2 and Annex C, IEC 61094-8 5.3).
Both microphones sit in the field at once, each on its own measuring channel.
The level reading difference between the channels, reference on channel 1, is
Formula (C.1); after the microphones are interchanged it is Formula (C.2); and
their difference cancels the gains of the two channels and the asymmetry of
the field, Formula (C.3):

.. math::

   L_\mathrm{ref} - L_\mathrm{test} = \tfrac12\left(L_\mathrm{C12} - L_\mathrm{C21}\right)

IEC 61094-5 requires the interchange in a coupler or a jig ("shall be used",
5.1.2); :func:`simultaneous_comparison` refuses a pressure calibration without
it. IEC 61094-8 does not, and without it the channel difference is taken as
read.

**Sequential excitation** (IEC 61094-5 5.1.3 and Annex B, IEC 61094-8 5.2 and
Annex A). The microphones take the same place in turn. Either the exchange
does not change the sound pressure significantly, or any change is detected
and corrected, for example with a monitor microphone near the source: the
ratio of each microphone's output to the monitor's, and the quotient of the
two ratios, is the output ratio corrected for the drift (IEC 61094-8 A.2).
:func:`sequential_comparison` computes it, with the monitor or without.

**Corrections.** IEC 61094-8 7.6 always corrects the reference's sensitivity
to the environmental conditions of the test. IEC 61094-5 6.6 does so when the
two microphones are different models; for two of the same model it allows the
result to be referred instead to the conditions at which the reference's
calibration is valid. Both parts allow the result to be referred to the
reference conditions of clause 4 (23,0 °C, 101,325 kPa, 50 %) when reliable
correction data are available.
:func:`environmental_sensitivity_correction` writes that correction to first
order from the coefficients of the microphone, in the units IEC 61094-2
Annex D gives them. :func:`jig_diameter_correction` returns the corrections of
IEC 61094-5 Table A.1 for a type WS3 microphone calibrated against an LS2aP in
the jig of Figure A.4. A free-field calibration against a reference calibrated
in a pressure field takes the reference's free-field to pressure sensitivity
level difference of IEC/TS 61094-7 (IEC 61094-8 Table 1 and 8.2).

**Uncertainty.** :func:`comparison_uncertainty_budget` combines, on
:func:`~phonometry.metrology.combine_uncertainty`, the components of IEC
61094-5 Table D.1 or IEC 61094-8 Table 2, each with a sensitivity of 1 in the
level model above, and multiplies the combined standard uncertainty by the
coverage factor :math:`k = 2` both parts report with (IEC 61094-5 7.9 and D.2,
IEC 61094-8 8.8). The expanded uncertainty is then passed to the calibration,
which draws it as a band.

**The effective free-field region** (IEC 61094-8 B.1).
:func:`free_field_region` gives the prolate spheroid inside which a time
window of length :math:`\tau` simulates a free field, with the source and the
microphone at its foci and the major diameter

.. math::

   A = d + \tau c

at the speed of sound :math:`c` of IEC 61094-2 Annex F for the conditions of
the test (:func:`~phonometry.fluids.air`).

Two printed values the library does not follow
----------------------------------------------

**IEC 61094-5 D.3.** The root-sum-square of the eight components Table D.1
prints is 0,0437 dB, not the 0,040 dB D.3 states; with :math:`k = 2` it is
0,087 dB rather than 0,08 dB. :func:`comparison_uncertainty_budget` gives the
sum of the printed components, and the defect is in ``docs/ERRATA.md``.

**IEC 61094-8 B.10.** The spectrum of Formula (B.10) is that of a rectangular
pulse of duration :math:`2b`, although the text calls :math:`b` the duration;
the library does not implement the direct impulse method of B.6, which the
standard itself calls largely superseded, and the defect is in
``docs/ERRATA.md``.

The IEC 61183 diffuse-field comparison of clause 5
(:func:`~phonometry.metrology.diffuse_field_sensitivity`) is the same
sequential comparison without a monitor, and computes its level difference and
its sensitivity level through this module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.frozen import read_only
from .._internal.validation import (
    require_above_absolute_zero,
    require_choice,
    require_positive,
)
from .free_field_corrections import (
    _band_column,
    _common_rows,
    _determinations,
    _frequency_axis,
)
from .uncertainty import Quantity, UncertaintyResult, combine_uncertainty

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

__all__ = [
    "IEC61094_5_TABLE_A1",
    "IEC61094_5_TABLE_D1",
    "IEC61094_8_TABLE_1",
    "IEC61094_8_TABLE_2",
    "ComparisonCalibration",
    "ComparisonUncertaintyBudget",
    "ComparisonUncertaintyRow",
    "EnvironmentalSensitivityCorrection",
    "FreeFieldRegion",
    "JigDiameterCorrection",
    "ReferenceCalibrationRow",
    "comparison_uncertainty_budget",
    "environmental_sensitivity_correction",
    "free_field_region",
    "jig_diameter_correction",
    "sequential_comparison",
    "simultaneous_comparison",
]

# ---------------------------------------------------------------------------
# Vocabulary and reference conditions
# ---------------------------------------------------------------------------

#: The two sound fields, one part each: a pressure field (IEC 61094-5) and a
#: free field (IEC 61094-8).
_FIELDS = ("pressure", "free_field")

#: The designation each field is calibrated by.
_STANDARDS: Mapping[str, str] = MappingProxyType(
    {"pressure": "IEC 61094-5:2016", "free_field": "IEC 61094-8:2012"}
)

#: The two ways of exposing the microphones: at once, or in turn.
_EXCITATIONS = ("simultaneous", "sequential")

#: IEC 61094-5:2016 and IEC 61094-8:2012 clause 4, the reference
#: environmental conditions: "temperature 23,0 °C".
_REFERENCE_TEMPERATURE_C = 23.0
#: IEC 61094-5:2016 and IEC 61094-8:2012 clause 4: "static pressure
#: 101,325 kPa".
_REFERENCE_STATIC_PRESSURE_KPA = 101.325
#: IEC 61094-5:2016 and IEC 61094-8:2012 clause 4: "relative humidity 50 %".
_REFERENCE_RELATIVE_HUMIDITY_PERCENT = 50.0

#: A relative humidity is a percentage of saturation: 0 % is dry air, 100 %
#: saturated air, and no state of the air lies outside them.
_SATURATED_PERCENT = 100.0

#: Relative agreement asked of two frequency axes for them to be the same
#: frequencies: the rounding of a value that went through arithmetic, nothing
#: more. A nominal 3150 Hz against an exact 3162 Hz is another frequency.
_SAME_FREQUENCY_REL_TOL = 1e-9

#: The name under which a free-field calibration carries the reference's
#: free-field to pressure sensitivity level difference in ``corrections_db``.
_FREE_FIELD_DIFFERENCE = "reference free-field difference"

#: The coverage factor both parts report the expanded uncertainty with
#: (IEC 61094-5 7.9 and D.2, IEC 61094-8 8.8).
_COVERAGE_FACTOR = 2.0

#: IEC 61094-5 Table A.1 NOTE: "The expanded uncertainty is estimated to be
#: 1/10th of the value of the correction (in decibels)." Neither the NOTE, A.2
#: nor the special case of Table D.1 gives its coverage factor; it is read as
#: the k = 2 that 7.9 and D.2 report every expanded uncertainty with.
_JIG_CORRECTION_RELATIVE_EXPANDED = 0.1

#: How far a frequency may sit from a frequency Table A.1 prints and still be
#: read as it: an exact base-ten one-third-octave frequency is within 1 % of
#: its nominal value, and adjacent rows of the table are 25 % apart.
_NOMINAL_TOLERANCE = 0.02

#: Relative agreement asked of a budget's stated combination.
_COMBINATION_REL_TOL = 1e-9

#: The same, absolute, for a budget whose every component is zero.
_COMBINATION_ABS_TOL_DB = 1e-15

_SQRT3 = math.sqrt(3.0)


# ---------------------------------------------------------------------------
# The shared core: the level model of IEC 61094-5 D.2
# ---------------------------------------------------------------------------


def _output_level_difference_db(
    test_output_level_db: ArrayLike,
    reference_output_level_db: ArrayLike,
    test_monitor_level_db: ArrayLike | None = None,
    reference_monitor_level_db: ArrayLike | None = None,
) -> NDArray[np.float64]:
    r""":math:`20\lg R_V`, the output of the test microphone re the reference.

    Each reading is taken against the monitor reading made with it when there
    is one (IEC 61094-8 A.2): the quotient of the two ratios to the monitor is
    the ratio of the two outputs corrected for any change of the field.
    Without a monitor it is the plain difference of the two readings, which is
    also Formula (8) of IEC 61183.
    """
    test = np.asarray(test_output_level_db, dtype=np.float64)
    reference = np.asarray(reference_output_level_db, dtype=np.float64)
    if test_monitor_level_db is not None:
        test = test - np.asarray(test_monitor_level_db, dtype=np.float64)
    if reference_monitor_level_db is not None:
        reference = reference - np.asarray(reference_monitor_level_db, dtype=np.float64)
    return test - reference


def _interchange_level_difference_db(
    channel_difference_db: ArrayLike, interchanged_channel_difference_db: ArrayLike
) -> NDArray[np.float64]:
    r""":math:`20\lg R_V` from the two channel differences of Annex C.

    Formula (C.3) with the reference as microphone 1:
    :math:`L_\mathrm{test} - L_\mathrm{ref} = -\tfrac12(L_\mathrm{C12} -
    L_\mathrm{C21})`.
    """
    first = np.asarray(channel_difference_db, dtype=np.float64)
    second = np.asarray(interchanged_channel_difference_db, dtype=np.float64)
    return -0.5 * (first - second)


def _compared_level_db(
    reference_level_db: ArrayLike,
    output_level_difference_db: ArrayLike,
    pressure_level_difference_db: ArrayLike = 0.0,
    correction_db: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    r"""The sensitivity level of the microphone under test.

    IEC 61094-5 D.2, :math:`M_\mathrm{test} = M_\mathrm{ref} R_V / R_P`, in
    levels: :math:`L_\mathrm{ref} + 20\lg R_V - 20\lg R_P` plus the sum of the
    corrections. Formulas (9) to (11) of IEC 61183 are the same sum with no
    pressure ratio and no correction.
    """
    return (
        np.asarray(reference_level_db, dtype=np.float64)
        + np.asarray(output_level_difference_db, dtype=np.float64)
        - np.asarray(pressure_level_difference_db, dtype=np.float64)
        + np.asarray(correction_db, dtype=np.float64)
    )


# ---------------------------------------------------------------------------
# The printed tables
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ComparisonUncertaintyRow:
    r"""One row of the uncertainty table of IEC 61094-5 (Table D.1) or
    IEC 61094-8 (Table 2).

    Table D.1 is a worked example at 2 kHz: seven of its eight rows state a
    value, the distribution it is read with and the standard uncertainty that
    follows; the repeatability row prints its standard uncertainty alone.
    Table 2 lists the typical components with the subclause that discusses
    each and prints no value.

    :ivar component: The component as the table prints it.
    :ivar subclauses: The subclauses the table refers the component to
        (Table 2); empty for Table D.1, which prints none.
    :ivar stated_db: The value the row's text states, in dB: a semi-range or
        an expanded uncertainty with :math:`k = 2`, as :attr:`divisor` says;
        ``None`` for the repeatability of Table D.1, whose text states none,
        and for Table 2.
    :ivar divisor: What turns :attr:`stated_db` into a standard uncertainty:
        :math:`\sqrt{3}` for the semi-range of a rectangular distribution, 2
        for an expanded uncertainty with :math:`k = 2`; ``None`` where
        :attr:`stated_db` is.
    :ivar standard_uncertainty_db: The standard uncertainty the table prints,
        in dB; ``None`` for Table 2.
    """

    component: str
    subclauses: tuple[str, ...] = ()
    stated_db: float | None = None
    divisor: float | None = None
    standard_uncertainty_db: float | None = None


def _d1_row(
    component: str, stated_db: float, divisor: float, printed_db: float
) -> ComparisonUncertaintyRow:
    return ComparisonUncertaintyRow(
        component=component,
        stated_db=stated_db,
        divisor=divisor,
        standard_uncertainty_db=printed_db,
    )


#: IEC 61094-5:2016 Table D.1, "Example uncertainty budget", for a
#: simultaneous calibration of a low-sensitivity WS2P microphone against an
#: LS2P reference in the coupler of Figure A.1, at 2 kHz. Keyed by the name
#: :func:`comparison_uncertainty_budget` takes each component by, in the
#: table's order. The polarising voltage of (200,0 ± 0,2) V states a
#: semi-range of :math:`20\lg(200{,}2/200)` dB. The repeatability row states no
#: value, only that it was "found from the standard uncertainties of a large
#: number of similar measurements", so it holds the printed standard
#: uncertainty alone.
#:
#: The table goes on with two "additional components for special cases",
#: which are not rows here. The first, the diaphragm diameter correction of a
#: WS3 microphone against an LS2 reference, prints "frequency dependent (see
#: Table A.1)" and an expanded uncertainty of 10 % of the correction: it is
#: :attr:`JigDiameterCorrection.standard_uncertainty_db`. The second, the
#: uncertainties of a calibration made as a system with a preamplifier, prints
#: 0,002 dB, "frequency dependent" and "<0,02 above 200 Hz" in its column,
#: beside a heading and two notes: the effect of a polarising voltage that
#: deviates from 200 V, and the capacitance component to be reconsidered. A
#: set-up that needs them passes them to :func:`comparison_uncertainty_budget`
#: as ``additional_components``.
IEC61094_5_TABLE_D1: Mapping[str, ComparisonUncertaintyRow] = MappingProxyType(
    {
        "reference": _d1_row("Sensitivity of reference microphone", 0.05, 2.0, 0.025),
        "capacitance": _d1_row("Microphone capacitance", 0.01, _SQRT3, 0.006),
        "non_linearity": _d1_row("Non-linearity", 0.03, _SQRT3, 0.017),
        "impedance": _d1_row("Microphone impedance", 0.005, _SQRT3, 0.003),
        "polarizing_voltage": _d1_row(
            "Polarising voltage", 20.0 * math.log10(200.2 / 200.0), _SQRT3, 0.005
        ),
        "repeatability": ComparisonUncertaintyRow(
            component="Repeatability", standard_uncertainty_db=0.025
        ),
        "drift": _d1_row(
            "Drift in reference microphone sensitivity since last calibration",
            0.03,
            _SQRT3,
            0.017,
        ),
        "rounding": _d1_row("Rounding of reported results", 0.005, _SQRT3, 0.003),
    }
)

#: IEC 61094-8:2012 Table 2, "Typical uncertainty components", keyed by the
#: name :func:`comparison_uncertainty_budget` takes each component by, with
#: the subclause references the table prints ("-" for the rounding error).
#: The table prints no values: 8.8 asks for each as a standard uncertainty at
#: each frequency.
IEC61094_8_TABLE_2: Mapping[str, ComparisonUncertaintyRow] = MappingProxyType(
    {
        "reference": ComparisonUncertaintyRow(
            "Free-field sensitivity of the reference microphone", ("8.2",)
        ),
        "source_stability": ComparisonUncertaintyRow(
            "Stability of sound source", ("8.4",)
        ),
        "positioning": ComparisonUncertaintyRow(
            "Positioning accuracy (including acoustic centre uncertainty)",
            ("7.3", "8.4"),
        ),
        "alignment": ComparisonUncertaintyRow(
            "Alignment between source and receiver", ("7.4", "8.4")
        ),
        "free_field": ComparisonUncertaintyRow(
            "Quality of free-field environment or influence of signal processing",
            ("8.5", "8.6"),
        ),
        "non_plane_wave": ComparisonUncertaintyRow(
            "Influence of non-plane wave", ("6.3",)
        ),
        "environment": ComparisonUncertaintyRow(
            "Influence of environmental conditions", ("7.6",)
        ),
        "polarizing_voltage": ComparisonUncertaintyRow(
            "Polarizing voltage", ("7.2", "8.2")
        ),
        "capacitance": ComparisonUncertaintyRow("Microphone capacitance", ("8.7.1",)),
        "non_linearity": ComparisonUncertaintyRow(
            "Measurement system non-linearity", ("8.7.2",)
        ),
        "rounding": ComparisonUncertaintyRow("Rounding error"),
        "repeatability": ComparisonUncertaintyRow(
            "Measurement repeatability", ("8.3",)
        ),
    }
)

#: The table each field's budget draws its components from.
_BUDGET_TABLES: Mapping[str, Mapping[str, ComparisonUncertaintyRow]] = MappingProxyType(
    {"pressure": IEC61094_5_TABLE_D1, "free_field": IEC61094_8_TABLE_2}
)


@dataclass(frozen=True)
class ReferenceCalibrationRow:
    """One row of IEC 61094-8:2012 Table 1: a way the reference microphone's
    free-field sensitivity can be known, and the expanded uncertainty
    (:math:`k = 2`) it typically carries.

    :ivar microphone_types: The reference microphone types the row is for,
        ``"LS"`` or ``"LS and WS"``.
    :ivar method: The calibration method as the table prints it.
    :ivar references: The documents that define it.
    :ivar expanded_uncertainty_1khz_db: The typical expanded uncertainty at
        1 kHz, in dB.
    :ivar expanded_uncertainty_10khz_db: The same at 10 kHz, in dB.
    """

    microphone_types: str
    method: str
    references: tuple[str, ...]
    expanded_uncertainty_1khz_db: float
    expanded_uncertainty_10khz_db: float


#: IEC 61094-8:2012 Table 1, "Calibration options for the reference
#: microphone and associated typical measurement uncertainty", in the table's
#: order. "This part of IEC 61094" is written out as IEC 61094-8.
IEC61094_8_TABLE_1: Mapping[str, ReferenceCalibrationRow] = MappingProxyType(
    {
        "primary_free_field": ReferenceCalibrationRow(
            "LS", "Primary free-field calibration", ("IEC 61094-3",), 0.25, 0.10
        ),
        "primary_pressure": ReferenceCalibrationRow(
            "LS",
            "Primary pressure calibration with the addition of a free-field to "
            "pressure sensitivity level difference",
            ("IEC 61094-2", "IEC/TS 61094-7"),
            0.12,
            0.4,
        ),
        "secondary_pressure": ReferenceCalibrationRow(
            "LS",
            "Secondary pressure calibration with the addition of a free-field to "
            "pressure sensitivity level difference",
            ("IEC 61094-5", "IEC/TS 61094-7"),
            0.15,
            0.5,
        ),
        "secondary_free_field": ReferenceCalibrationRow(
            "LS and WS", "Secondary free-field calibration", ("IEC 61094-8",), 0.2, 0.5
        ),
        "electrostatic_actuator": ReferenceCalibrationRow(
            "LS and WS",
            "Electrostatic actuator calibration with the addition of a free-field "
            "to actuator response level difference",
            ("IEC 61094-6",),
            0.3,
            0.6,
        ),
    }
)

#: IEC 61094-5:2016 Table A.1, "Calculated corrections to be added to the
#: sensitivity level of the WS3 microphone when using the arrangement in
#: Figure A.4", keyed by frequency in Hz, in dB. They assume an LS2aP
#: reference and a radially symmetrical field, and hold for the 0,5 mm
#: separation of Figure A.4 only.
IEC61094_5_TABLE_A1: Mapping[float, float] = MappingProxyType(
    {
        1000.0: -0.004,
        1250.0: -0.006,
        1600.0: -0.009,
        2000.0: -0.015,
        2500.0: -0.023,
        3150.0: -0.036,
        4000.0: -0.059,
        5000.0: -0.092,
        6300.0: -0.146,
        8000.0: -0.235,
        10000.0: -0.367,
        12500.0: -0.572,
        16000.0: -0.933,
        20000.0: -1.443,
    }
)


# ---------------------------------------------------------------------------
# The environmental correction (IEC 61094-5 6.6, IEC 61094-8 7.6)
# ---------------------------------------------------------------------------


def _relative_humidity(value: float, name: str) -> float:
    """Refuse a relative humidity that is not finite or not within 0 % to
    100 %.

    :raises ValueError: for a humidity outside the closed range from dry to
        saturated air.
    """
    if not math.isfinite(value) or not 0.0 <= value <= _SATURATED_PERCENT:
        msg = f"'{name}' must be between 0 and 100."
        raise ValueError(msg)
    return float(value)


@dataclass(frozen=True)
class EnvironmentalSensitivityCorrection:
    r"""The change of a microphone's sensitivity level between two sets of
    environmental conditions, to first order in each.

    .. math::

       C_\mathrm{env} = \delta_p\,(p_s - p_{s,0}) + \delta_t\,(t - t_0)
       + \delta_H\,(H - H_0)

    with the static pressure coefficient :math:`\delta_p` in dB/kPa, the
    temperature coefficient :math:`\delta_t` in dB/K and the humidity
    coefficient :math:`\delta_H` in dB per percentage point, each one value
    or one per frequency. Added to a sensitivity level valid at
    :math:`(p_{s,0}, t_0, H_0)`, it gives the level at :math:`(p_s, t, H)`.

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar static_pressure_kpa: :math:`p_s`, where the level is wanted, in kPa.
    :ivar temperature_c: :math:`t`, in °C.
    :ivar relative_humidity_percent: :math:`H`, in %.
    :ivar reference_static_pressure_kpa: :math:`p_{s,0}`, where the level is
        known, in kPa.
    :ivar reference_temperature_c: :math:`t_0`, in °C.
    :ivar reference_relative_humidity_percent: :math:`H_0`, in %.
    :ivar static_pressure_coefficient_db_per_kpa: :math:`\delta_p` at each
        frequency, in dB/kPa.
    :ivar temperature_coefficient_db_per_k: :math:`\delta_t`, in dB/K.
    :ivar humidity_coefficient_db_per_percent: :math:`\delta_H`, in dB/%.
    """

    frequencies_hz: NDArray[np.float64]
    static_pressure_kpa: float
    temperature_c: float
    relative_humidity_percent: float
    reference_static_pressure_kpa: float
    reference_temperature_c: float
    reference_relative_humidity_percent: float
    static_pressure_coefficient_db_per_kpa: NDArray[np.float64]
    temperature_coefficient_db_per_k: NDArray[np.float64]
    humidity_coefficient_db_per_percent: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Refuse conditions that are no state of the air or coefficients that
        are not finite, and publish the columns read-only.

        :raises ValueError: for frequencies that are not positive and
            increasing, a pressure that is not positive, a temperature that is
            not finite or not above absolute zero, a relative humidity outside
            0 % to 100 %, or a coefficient column that is not one finite value
            per frequency.
        """
        frequencies = _frequency_axis(self.frequencies_hz)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        for name in ("static_pressure_kpa", "reference_static_pressure_kpa"):
            object.__setattr__(self, name, require_positive(getattr(self, name), name))
        for name in ("temperature_c", "reference_temperature_c"):
            value = require_above_absolute_zero(getattr(self, name), name)
            object.__setattr__(self, name, value)
        for name in (
            "relative_humidity_percent",
            "reference_relative_humidity_percent",
        ):
            object.__setattr__(
                self, name, _relative_humidity(getattr(self, name), name)
            )
        for name in (
            "static_pressure_coefficient_db_per_kpa",
            "temperature_coefficient_db_per_k",
            "humidity_coefficient_db_per_percent",
        ):
            column = _band_column(getattr(self, name), name, frequencies.size)
            object.__setattr__(self, name, read_only(column.copy()))

    @property
    def static_pressure_term_db(self) -> NDArray[np.float64]:
        r""":math:`\delta_p\,(p_s - p_{s,0})`, in dB."""
        return self.static_pressure_coefficient_db_per_kpa * (
            self.static_pressure_kpa - self.reference_static_pressure_kpa
        )

    @property
    def temperature_term_db(self) -> NDArray[np.float64]:
        r""":math:`\delta_t\,(t - t_0)`, in dB."""
        return self.temperature_coefficient_db_per_k * (
            self.temperature_c - self.reference_temperature_c
        )

    @property
    def humidity_term_db(self) -> NDArray[np.float64]:
        r""":math:`\delta_H\,(H - H_0)`, in dB."""
        return self.humidity_coefficient_db_per_percent * (
            self.relative_humidity_percent - self.reference_relative_humidity_percent
        )

    @property
    def correction_db(self) -> NDArray[np.float64]:
        r""":math:`C_\mathrm{env}`, the sum of the three terms, in dB."""
        pressure = self.static_pressure_term_db
        return pressure + self.temperature_term_db + self.humidity_term_db

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot :math:`C_\mathrm{env}` and its three terms against frequency.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the :math:`C_\mathrm{env}` curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_environmental_sensitivity_correction

        return plot_environmental_sensitivity_correction(
            self, ax=ax, language=check_language(language), **kwargs
        )


def environmental_sensitivity_correction(
    frequencies_hz: ArrayLike,
    *,
    static_pressure_kpa: float,
    temperature_c: float,
    relative_humidity_percent: float,
    static_pressure_coefficient_db_per_kpa: ArrayLike,
    temperature_coefficient_db_per_k: ArrayLike,
    humidity_coefficient_db_per_percent: ArrayLike = 0.0,
    reference_static_pressure_kpa: float = _REFERENCE_STATIC_PRESSURE_KPA,
    reference_temperature_c: float = _REFERENCE_TEMPERATURE_C,
    reference_relative_humidity_percent: float = _REFERENCE_RELATIVE_HUMIDITY_PERCENT,
) -> EnvironmentalSensitivityCorrection:
    r"""The correction of a sensitivity level from one set of environmental
    conditions to another (IEC 61094-5 6.6, IEC 61094-8 7.6).

    IEC 61094-8 7.6 asks for the reference microphone's sensitivity to be
    corrected to the conditions of the test in every case. IEC 61094-5 6.6
    asks for it when the two microphones are different models, and for two of
    the same model allows the result to be referred instead to the conditions
    at which the reference's calibration is valid. Both allow the result to be
    referred to the reference conditions of clause 4 when reliable correction
    data are available; neither prints a formula. This is the first-order
    one, a coefficient times a deviation for each of the three conditions,

    .. math::

       C_\mathrm{env} = \delta_p\,(p_s - p_{s,0}) + \delta_t\,(t - t_0)
       + \delta_H\,(H - H_0)

    with the coefficients in the units IEC 61094-2:2009 Annex D gives them:
    dB/kPa for the static pressure, dB/K for the temperature. Annex D of that
    part puts the low-frequency static pressure coefficient of LS1P
    microphones between -0,01 dB/kPa and -0,02 dB/kPa and of LS2P between
    -0,003 dB/kPa and -0,008 dB/kPa, the temperature coefficient within
    ±0,005 dB/K, and all three vary with frequency and from one microphone to
    another, so they are the microphone's own and are required here. 6.5.3 of
    the same part observes no influence of humidity on a laboratory standard
    microphone, hence the default of 0 for its coefficient.

    The reference conditions default to clause 4 of IEC 61094-5 and IEC
    61094-8, 101,325 kPa, 23,0 °C and 50 %. The correction adds to a level
    known at the reference conditions to give it at the conditions of the
    test; :func:`simultaneous_comparison` and :func:`sequential_comparison`
    add it to the reference microphone's level (``reference_environment=``)
    or subtract it from the result (``test_environment=``).

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param static_pressure_kpa: :math:`p_s`, the static pressure the level is
        wanted at, in kPa.
    :param temperature_c: :math:`t`, in °C.
    :param relative_humidity_percent: :math:`H`, in %.
    :param static_pressure_coefficient_db_per_kpa: :math:`\delta_p`, in dB/kPa,
        one value or one per frequency.
    :param temperature_coefficient_db_per_k: :math:`\delta_t`, in dB/K.
    :param humidity_coefficient_db_per_percent: :math:`\delta_H`, in dB per
        percentage point (Default: 0).
    :param reference_static_pressure_kpa: :math:`p_{s,0}`, where the level is
        known, in kPa (Default: 101,325).
    :param reference_temperature_c: :math:`t_0`, in °C (Default: 23,0).
    :param reference_relative_humidity_percent: :math:`H_0`, in % (Default:
        50).
    :return: The :class:`EnvironmentalSensitivityCorrection`.
    :raises ValueError: for frequencies that are not positive and increasing,
        a pressure that is not positive, a temperature that is not finite or
        not above absolute zero, a relative humidity outside 0 % to 100 %, a
        coefficient that is not finite, or a coefficient column that is not
        one value per frequency.
    """
    return EnvironmentalSensitivityCorrection(
        frequencies_hz=np.asarray(frequencies_hz, dtype=np.float64),
        static_pressure_kpa=static_pressure_kpa,
        temperature_c=temperature_c,
        relative_humidity_percent=relative_humidity_percent,
        reference_static_pressure_kpa=reference_static_pressure_kpa,
        reference_temperature_c=reference_temperature_c,
        reference_relative_humidity_percent=reference_relative_humidity_percent,
        static_pressure_coefficient_db_per_kpa=np.asarray(
            static_pressure_coefficient_db_per_kpa, dtype=np.float64
        ),
        temperature_coefficient_db_per_k=np.asarray(
            temperature_coefficient_db_per_k, dtype=np.float64
        ),
        humidity_coefficient_db_per_percent=np.asarray(
            humidity_coefficient_db_per_percent, dtype=np.float64
        ),
    )


# ---------------------------------------------------------------------------
# The WS3 correction of the jig (IEC 61094-5 Table A.1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class JigDiameterCorrection:
    r"""The corrections of IEC 61094-5 Table A.1 at the frequencies asked for.

    Added to the sensitivity level of a type WS3 microphone calibrated against
    a type LS2aP reference in the jig of Figure A.4, they account for the
    radial sensitivity of the two diaphragms and for the smaller one of the
    test microphone. Their expanded uncertainty is 10 % of their value
    (A.2 and the NOTE to Table A.1), a component of the budget of Table D.1.
    None of the three places that give the 10 % states its coverage factor;
    the library reads it as :math:`k = 2`, the factor 7.9 and D.2 report every
    expanded uncertainty with.

    :ivar frequencies_hz: The frequencies of the table asked for, in Hz.
    :ivar correction_db: The correction at each, in dB.
    """

    frequencies_hz: NDArray[np.float64]
    correction_db: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Publish the columns read-only.

        :raises ValueError: for columns of different lengths or values that
            are not finite.
        """
        frequencies = _frequency_axis(self.frequencies_hz)
        correction = _band_column(self.correction_db, "correction_db", frequencies.size)
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        object.__setattr__(self, "correction_db", read_only(correction.copy()))

    @property
    def expanded_uncertainty_db(self) -> NDArray[np.float64]:
        """The expanded uncertainty of each correction, one tenth of its
        magnitude, in dB (read as :math:`k = 2`, 7.9 and D.2).
        """
        return _JIG_CORRECTION_RELATIVE_EXPANDED * np.abs(self.correction_db)

    @property
    def standard_uncertainty_db(self) -> NDArray[np.float64]:
        """The standard uncertainty of each correction, the expanded one over
        :math:`k = 2` (a reading of 7.9 and D.2, since the 10 % comes without
        a coverage factor), in dB: the special-case component of Table D.1.
        """
        return self.expanded_uncertainty_db / _COVERAGE_FACTOR

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the corrections with their expanded uncertainty.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the correction curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_jig_diameter_correction

        return plot_jig_diameter_correction(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _table_a1_value(frequency: float) -> float:
    """The Table A.1 correction at a frequency the table prints.

    :raises ValueError: for a frequency that is not one of its rows.
    """
    keys = np.array(sorted(IEC61094_5_TABLE_A1), dtype=np.float64)
    nearest = float(keys[np.argmin(np.abs(np.log(keys / frequency)))])
    if not math.isclose(frequency, nearest, rel_tol=_NOMINAL_TOLERANCE):
        msg = (
            f"{frequency:g} Hz is not a frequency of IEC 61094-5 Table A.1, which "
            "prints the one-third octaves from 1 kHz to 20 kHz."
        )
        raise ValueError(msg)
    return IEC61094_5_TABLE_A1[nearest]


def jig_diameter_correction(
    frequencies_hz: ArrayLike | None = None,
) -> JigDiameterCorrection:
    r"""The corrections of IEC 61094-5:2016 Table A.1 for a type WS3 microphone
    against a type LS2aP reference in the jig of Figure A.4.

    The table gives them at the preferred one-third-octave frequencies from
    1 kHz, -0,004 dB, to 20 kHz, -1,443 dB, calculated for a radially
    symmetrical field and the 0,5 mm diaphragm separation of Figure A.4, "the
    only one for which the corrections specified in Table A.1 are valid". A
    frequency within 2 % of a row, such as an exact base-ten one-third-octave
    frequency, reads as that row. Pass ``.correction_db`` to the comparison as
    one of its ``corrections_db`` and ``.standard_uncertainty_db`` to the
    budget as an additional component.

    :param frequencies_hz: Frequencies of the table, in Hz, increasing
        (Default: None, the 14 rows).
    :return: The :class:`JigDiameterCorrection`.
    :raises ValueError: for a frequency the table does not print.
    """
    frequencies = (
        np.array(sorted(IEC61094_5_TABLE_A1), dtype=np.float64)
        if frequencies_hz is None
        else _frequency_axis(frequencies_hz)
    )
    correction = np.array([_table_a1_value(float(f)) for f in frequencies])
    return JigDiameterCorrection(frequencies_hz=frequencies, correction_db=correction)


# ---------------------------------------------------------------------------
# The calibration: IEC 61094-5 D.2 in levels
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ComparisonCalibration:
    r"""The sensitivity level of a microphone calibrated by comparison
    (IEC 61094-5:2016 D.2 for a pressure field, IEC 61094-8:2012 for a free
    field).

    .. math::

       L_\mathrm{test} = L_\mathrm{ref} + 20\lg R_V - 20\lg R_P + \sum_j C_j

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar reference_sensitivity_level_db: :math:`L_\mathrm{ref}`, the
        reference microphone's sensitivity level as calibrated, in dB re
        1 V/Pa.
    :ivar output_level_differences_db: :math:`20\lg R_V` of each
        determination, one row per determination, in dB: the output of the
        test microphone re that of the reference.
    :ivar pressure_level_difference_db: :math:`20\lg R_P`, the effective sound
        pressure on the test microphone re that on the reference, in dB.
    :ivar corrections_db: The corrections :math:`C_j` added to the level, by
        name, each in dB at every frequency.
    :ivar field: ``"pressure"`` (IEC 61094-5) or ``"free_field"``
        (IEC 61094-8).
    :ivar excitation: ``"simultaneous"`` or ``"sequential"``.
    :ivar expanded_uncertainty_db: The expanded uncertainty (:math:`k = 2`) of
        the sensitivity level at each frequency, in dB, or ``None``.
    """

    frequencies_hz: NDArray[np.float64]
    reference_sensitivity_level_db: NDArray[np.float64]
    output_level_differences_db: NDArray[np.float64]
    pressure_level_difference_db: NDArray[np.float64]
    corrections_db: Mapping[str, NDArray[np.float64]]
    field: str
    excitation: str
    expanded_uncertainty_db: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        """Refuse columns that disagree or an unknown field or excitation, and
        publish everything read-only.

        :raises ValueError: for frequencies that are not positive and
            increasing, a column or a correction that is not one finite value
            per frequency, determinations that are not one row per
            determination, a negative uncertainty, or an unknown field or
            excitation.
        """
        require_choice(self.field, "field", _FIELDS)
        require_choice(self.excitation, "excitation", _EXCITATIONS)
        frequencies = _frequency_axis(self.frequencies_hz)
        count = frequencies.size
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        for name in ("reference_sensitivity_level_db", "pressure_level_difference_db"):
            column = _band_column(getattr(self, name), name, count)
            object.__setattr__(self, name, read_only(column.copy()))
        rows = _determinations(
            self.output_level_differences_db, "output_level_differences_db", count
        )
        object.__setattr__(self, "output_level_differences_db", read_only(rows.copy()))
        corrections = {
            str(name): read_only(
                _band_column(value, f"corrections_db[{name!r}]", count).copy()
            )
            for name, value in self.corrections_db.items()
        }
        object.__setattr__(self, "corrections_db", MappingProxyType(corrections))
        if self.expanded_uncertainty_db is not None:
            uncertainty = _band_column(
                self.expanded_uncertainty_db, "expanded_uncertainty_db", count
            )
            if np.any(uncertainty < 0.0):
                msg = "ComparisonCalibration: 'expanded_uncertainty_db' must be non-negative."
                raise ValueError(msg)
            object.__setattr__(
                self, "expanded_uncertainty_db", read_only(uncertainty.copy())
            )

    @property
    def standard(self) -> str:
        """The designation the calibration follows."""
        return _STANDARDS[self.field]

    @property
    def determinations(self) -> int:
        """The number of determinations averaged."""
        return int(self.output_level_differences_db.shape[0])

    @property
    def output_level_difference_db(self) -> NDArray[np.float64]:
        r""":math:`20\lg R_V`, the mean over the determinations, in dB."""
        return np.mean(self.output_level_differences_db, axis=0)

    @property
    def correction_db(self) -> NDArray[np.float64]:
        r""":math:`\sum_j C_j`, in dB (0 without corrections)."""
        total = np.zeros(self.frequencies_hz.size)
        for value in self.corrections_db.values():
            total = total + value
        return total

    @property
    def sensitivity_level_db(self) -> NDArray[np.float64]:
        r""":math:`L_\mathrm{test}`, in dB re 1 V/Pa."""
        return _compared_level_db(
            self.reference_sensitivity_level_db,
            self.output_level_difference_db,
            self.pressure_level_difference_db,
            self.correction_db,
        )

    @property
    def sensitivity_mv_per_pa(self) -> NDArray[np.float64]:
        r""":math:`M_\mathrm{test} = 10^{L_\mathrm{test}/20}` V/Pa, in mV/Pa."""
        return 1000.0 * 10.0 ** (self.sensitivity_level_db / 20.0)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot :math:`L_\mathrm{test}` and the reference's level against
        frequency, with the expanded uncertainty as a band when it is known.

        The reference's level is :math:`L_\mathrm{ref}`, or, in a free field
        against a pressure-calibrated reference, :math:`L_\mathrm{ref}` plus
        its free-field difference: the level the test microphone was
        compared with.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the :math:`L_\mathrm{test}` curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_comparison_calibration

        return plot_comparison_calibration(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _frequencies_of(
    correction: EnvironmentalSensitivityCorrection,
    name: str,
    frequencies: NDArray[np.float64],
) -> None:
    """Refuse an environmental correction made at other frequencies.

    The coefficients are per frequency, so a correction made at as many
    frequencies as the calibration but not the same ones would apply each
    coefficient at the wrong frequency: the axes themselves have to agree,
    not their lengths alone.

    :raises ValueError: for a correction at another number of frequencies, or
        at as many but not the same ones.
    """
    made = correction.frequencies_hz
    if made.size != frequencies.size:
        msg = (
            f"'{name}' was made at {made.size} frequencies; the calibration "
            f"has {frequencies.size}."
        )
        raise ValueError(msg)
    same = np.isclose(made, frequencies, rtol=_SAME_FREQUENCY_REL_TOL, atol=0.0)
    if not np.all(same):
        first = int(np.flatnonzero(~same)[0])
        msg = (
            f"'{name}' was made at {made[first]:g} Hz where the calibration "
            f"has {frequencies[first]:g} Hz; make it at the calibration's "
            "frequencies."
        )
        raise ValueError(msg)


def _calibration(
    frequencies: NDArray[np.float64],
    reference_sensitivity_level_db: ArrayLike,
    output_level_differences_db: NDArray[np.float64],
    *,
    field: str,
    excitation: str,
    pressure_level_difference_db: ArrayLike,
    corrections_db: Mapping[str, ArrayLike] | None,
    reference_environment: EnvironmentalSensitivityCorrection | None,
    test_environment: EnvironmentalSensitivityCorrection | None,
    reference_free_field_difference_db: ArrayLike | None,
    expanded_uncertainty_db: ArrayLike | None,
) -> ComparisonCalibration:
    """Gather the corrections by name and build the result.

    The field is checked first, so that an unknown one is named as such and
    not taken for a pressure calibration by the free-field check below.
    """
    field = require_choice(field, "field", _FIELDS)
    named: dict[str, ArrayLike] = {}
    if reference_free_field_difference_db is not None:
        if field != "free_field":
            msg = (
                "'reference_free_field_difference_db' belongs to a free-field "
                "calibration (IEC 61094-8 Table 1), not to a pressure one."
            )
            raise ValueError(msg)
        named[_FREE_FIELD_DIFFERENCE] = reference_free_field_difference_db
    if reference_environment is not None:
        _frequencies_of(reference_environment, "reference_environment", frequencies)
        named["reference environment"] = reference_environment.correction_db
    if test_environment is not None:
        _frequencies_of(test_environment, "test_environment", frequencies)
        named["reference conditions"] = -test_environment.correction_db
    for name, value in (corrections_db or {}).items():
        if name in named:
            msg = f"'corrections_db' repeats the correction {name!r}."
            raise ValueError(msg)
        named[str(name)] = value
    return ComparisonCalibration(
        frequencies_hz=frequencies,
        reference_sensitivity_level_db=np.asarray(
            reference_sensitivity_level_db, dtype=np.float64
        ),
        output_level_differences_db=output_level_differences_db,
        pressure_level_difference_db=np.asarray(
            pressure_level_difference_db, dtype=np.float64
        ),
        corrections_db=named,  # type: ignore[arg-type]
        field=field,
        excitation=excitation,
        expanded_uncertainty_db=(
            None
            if expanded_uncertainty_db is None
            else np.asarray(expanded_uncertainty_db, dtype=np.float64)
        ),
    )


def simultaneous_comparison(
    frequencies_hz: ArrayLike,
    reference_sensitivity_level_db: ArrayLike,
    channel_difference_db: ArrayLike,
    interchanged_channel_difference_db: ArrayLike | None = None,
    *,
    field: str = "pressure",
    pressure_level_difference_db: ArrayLike = 0.0,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    reference_environment: EnvironmentalSensitivityCorrection | None = None,
    test_environment: EnvironmentalSensitivityCorrection | None = None,
    reference_free_field_difference_db: ArrayLike | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ComparisonCalibration:
    r"""Calibration by comparison with both microphones in the field at once
    (IEC 61094-5:2016 5.1.2 and Annex C; IEC 61094-8:2012 5.3).

    Each microphone is read on its own measuring channel. With the reference
    on channel 1, the level reading difference between the channels is
    Formula (C.1),

    .. math::

       L_\mathrm{C12} = (L_1 + L_\mathrm{m1} + L_\mathrm{d1} + L_\mathrm{WA})
       - (L_2 + L_\mathrm{m2} + L_\mathrm{d1} + L_\mathrm{WB})

    and after the microphones are interchanged, in the coupler ports and on
    the preamplifiers, it is Formula (C.2). Their difference leaves the two
    sensitivity levels alone, whatever the gains of the channels and the
    asymmetry of the field, Formula (C.3):

    .. math::

       L_\mathrm{ref} - L_\mathrm{test}
       = \tfrac12\left(L_\mathrm{C12} - L_\mathrm{C21}\right)

    so :math:`20\lg R_V = -\tfrac12(L_\mathrm{C12} - L_\mathrm{C21})`, and the
    sensitivity level of the test microphone follows by D.2. A pressure
    calibration requires the interchange ("the microphones shall be
    interchanged, and the measurement repeated", 5.1.2). A free-field one does
    not (5.3 relies on a symmetrical field instead); without it, the channel
    difference is taken as :math:`-20\lg R_V`, which assumes channels of equal
    gain.

    Each reading may be one value per frequency or a matrix of one row per
    determination (the three repeats of D.2, say); the calibration averages
    the determinations.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param reference_sensitivity_level_db: :math:`L_\mathrm{ref}`, the
        reference microphone's sensitivity level, in dB re 1 V/Pa, one value
        or one per frequency. For a free-field calibration it is the
        reference's free-field level, or its pressure level with
        ``reference_free_field_difference_db``.
    :param channel_difference_db: :math:`L_\mathrm{C12}`, the reading of
        channel 1 less that of channel 2 with the reference on channel 1, in
        dB.
    :param interchanged_channel_difference_db: :math:`L_\mathrm{C21}`, the
        same difference after the interchange, the test microphone on
        channel 1, in dB (Default: None; required for ``field="pressure"``).
    :param field: ``"pressure"`` (IEC 61094-5, default) or ``"free_field"``
        (IEC 61094-8).
    :param pressure_level_difference_db: :math:`20\lg R_P`, the effective
        sound pressure on the test microphone re that on the reference, in dB
        (Default: 0, the ratio reduced to unity).
    :param corrections_db: Further corrections added to the level, by name,
        in dB, such as ``jig_diameter_correction(f).correction_db`` (Default:
        none).
    :param reference_environment: The :class:`EnvironmentalSensitivityCorrection` that
        takes the reference's level from the conditions of its calibration to
        those of the test, added (Default: None).
    :param test_environment: The :class:`EnvironmentalSensitivityCorrection` of the test
        microphone from the reference conditions to those of the test,
        subtracted to refer the result to the reference conditions (Default:
        None, the result is at the conditions of the test).
    :param reference_free_field_difference_db: The reference's free-field to
        pressure sensitivity level difference (IEC/TS 61094-7), added to a
        pressure-calibrated reference in a free-field calibration only, in dB;
        the result carries it in ``corrections_db`` as ``"reference free-field
        difference"`` (Default: None).
    :param expanded_uncertainty_db: The expanded uncertainty (:math:`k = 2`)
        of the result at each frequency, in dB, as
        :func:`comparison_uncertainty_budget` gives it (Default: None).
    :return: The :class:`ComparisonCalibration`.
    :raises ValueError: for an unknown field, a pressure calibration without
        the interchange, a free-field correction on a pressure calibration, an
        environmental correction made at other frequencies, readings whose
        numbers of determinations disagree, or any column that is not one
        finite value per frequency.
    """
    field = require_choice(field, "field", _FIELDS)
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    first = _determinations(channel_difference_db, "channel_difference_db", count)
    if interchanged_channel_difference_db is None:
        if field == "pressure":
            msg = (
                "A pressure calibration by simultaneous excitation needs the "
                "reading after the microphones are interchanged (IEC 61094-5 "
                "5.1.2); pass 'interchanged_channel_difference_db'."
            )
            raise ValueError(msg)
        ratios = -first
    else:
        second = _determinations(
            interchanged_channel_difference_db,
            "interchanged_channel_difference_db",
            count,
        )
        _common_rows(
            {
                "channel_difference_db": first,
                "interchanged_channel_difference_db": second,
            }
        )
        ratios = _interchange_level_difference_db(first, second)
    return _calibration(
        frequencies,
        reference_sensitivity_level_db,
        ratios,
        field=field,
        excitation="simultaneous",
        pressure_level_difference_db=pressure_level_difference_db,
        corrections_db=corrections_db,
        reference_environment=reference_environment,
        test_environment=test_environment,
        reference_free_field_difference_db=reference_free_field_difference_db,
        expanded_uncertainty_db=expanded_uncertainty_db,
    )


def sequential_comparison(
    frequencies_hz: ArrayLike,
    reference_sensitivity_level_db: ArrayLike,
    reference_output_level_db: ArrayLike,
    test_output_level_db: ArrayLike,
    *,
    reference_monitor_level_db: ArrayLike | None = None,
    test_monitor_level_db: ArrayLike | None = None,
    field: str = "pressure",
    pressure_level_difference_db: ArrayLike = 0.0,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    reference_environment: EnvironmentalSensitivityCorrection | None = None,
    test_environment: EnvironmentalSensitivityCorrection | None = None,
    reference_free_field_difference_db: ArrayLike | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
) -> ComparisonCalibration:
    r"""Calibration by comparison with the microphones put in the field in
    turn (IEC 61094-5:2016 5.1.3 and Annex B; IEC 61094-8:2012 5.2 and
    Annex A).

    The reference and the test microphone take the same place one after the
    other. Either the exchange does not change the sound pressure
    significantly, or any change is detected and corrected (IEC 61094-5
    5.1.3, IEC 61094-8 5.2), for example with a monitor microphone near the
    source: the ratio of each microphone's output to the monitor's output,
    and the quotient of the two ratios, "gives the ratio of the microphone
    under test output voltage to the reference microphone output voltage,
    corrected for any variation in the sound pressure generated by the
    source" (IEC 61094-8 A.2). With :math:`V_\mathrm{ref}` and
    :math:`V_\mathrm{mon,1}` the outputs of the reference and the monitor in
    the first measurement, and :math:`V_\mathrm{test}` and
    :math:`V_\mathrm{mon,2}` those of the second,

    .. math::

       20\lg R_V = 20\lg\frac{V_\mathrm{test}}{V_\mathrm{mon,2}}
       - 20\lg\frac{V_\mathrm{ref}}{V_\mathrm{mon,1}}

    and without a monitor :math:`20\lg(V_\mathrm{test}/V_\mathrm{ref})`,
    the plain difference of the two output levels. The sensitivity level of
    the test microphone then follows by D.2.

    Each reading may be one value per frequency or a matrix of one row per
    determination; the calibration averages the determinations.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param reference_sensitivity_level_db: :math:`L_\mathrm{ref}`, the
        reference microphone's sensitivity level, in dB re 1 V/Pa.
    :param reference_output_level_db: :math:`20\lg V_\mathrm{ref}`, the
        reference microphone's output level, in dB re any voltage the test
        microphone is read against too.
    :param test_output_level_db: :math:`20\lg V_\mathrm{test}`, the test
        microphone's output level, in dB re the same voltage.
    :param reference_monitor_level_db: :math:`20\lg V_\mathrm{mon,1}`, the
        monitor's output level in the measurement of the reference, in dB
        (Default: None, no monitor).
    :param test_monitor_level_db: :math:`20\lg V_\mathrm{mon,2}`, the
        monitor's output level in the measurement of the test microphone, in
        dB (Default: None; given with the other or not at all).
    :param field: ``"pressure"`` (IEC 61094-5, default) or ``"free_field"``
        (IEC 61094-8).
    :param pressure_level_difference_db: :math:`20\lg R_P`, in dB (Default: 0).
    :param corrections_db: Further corrections added to the level, by name,
        in dB (Default: none).
    :param reference_environment: The :class:`EnvironmentalSensitivityCorrection` of the
        reference, added (Default: None).
    :param test_environment: The :class:`EnvironmentalSensitivityCorrection` of the test
        microphone, subtracted (Default: None).
    :param reference_free_field_difference_db: The reference's free-field to
        pressure sensitivity level difference (IEC/TS 61094-7), free field
        only, in dB; carried in ``corrections_db`` as ``"reference free-field
        difference"`` (Default: None).
    :param expanded_uncertainty_db: The expanded uncertainty (:math:`k = 2`)
        of the result at each frequency, in dB (Default: None).
    :return: The :class:`ComparisonCalibration`.
    :raises ValueError: for an unknown field, one monitor reading without the
        other, a free-field correction on a pressure calibration, an
        environmental correction made at other frequencies, readings whose
        numbers of determinations disagree, or any column that is not one
        finite value per frequency.
    """
    field = require_choice(field, "field", _FIELDS)
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    if (reference_monitor_level_db is None) != (test_monitor_level_db is None):
        msg = (
            "Give the monitor reading taken with each microphone, "
            "'reference_monitor_level_db' and 'test_monitor_level_db', or neither."
        )
        raise ValueError(msg)
    readings = {
        "reference_output_level_db": _determinations(
            reference_output_level_db, "reference_output_level_db", count
        ),
        "test_output_level_db": _determinations(
            test_output_level_db, "test_output_level_db", count
        ),
    }
    if reference_monitor_level_db is not None and test_monitor_level_db is not None:
        readings["reference_monitor_level_db"] = _determinations(
            reference_monitor_level_db, "reference_monitor_level_db", count
        )
        readings["test_monitor_level_db"] = _determinations(
            test_monitor_level_db, "test_monitor_level_db", count
        )
    _common_rows(readings)
    ratios = _output_level_difference_db(
        readings["test_output_level_db"],
        readings["reference_output_level_db"],
        readings.get("test_monitor_level_db"),
        readings.get("reference_monitor_level_db"),
    )
    return _calibration(
        frequencies,
        reference_sensitivity_level_db,
        np.atleast_2d(ratios),
        field=field,
        excitation="sequential",
        pressure_level_difference_db=pressure_level_difference_db,
        corrections_db=corrections_db,
        reference_environment=reference_environment,
        test_environment=test_environment,
        reference_free_field_difference_db=reference_free_field_difference_db,
        expanded_uncertainty_db=expanded_uncertainty_db,
    )


# ---------------------------------------------------------------------------
# The uncertainty budget (IEC 61094-5 Annex D, IEC 61094-8 8.8 and Table 2)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ComparisonUncertaintyBudget:
    r"""The uncertainty budget of a comparison calibration at one frequency
    (IEC 61094-5:2016 Annex D, IEC 61094-8:2012 8.8).

    Every component is a standard uncertainty in dB and enters the level model
    with a sensitivity of 1, so the combined standard uncertainty is their
    root-sum-square (D.3), and the expanded uncertainty is :math:`k = 2`
    times it (7.9 of the first part, 8.8 of the second).

    :ivar frequency_hz: The frequency, in Hz.
    :ivar field: ``"pressure"`` (Table D.1) or ``"free_field"`` (Table 2).
    :ivar names: The key of each component, then the names of any additional
        ones.
    :ivar components: The component as the table prints it, or the name of an
        additional one.
    :ivar standard_uncertainties_db: :math:`u_i`, in dB.
    :ivar uncertainty: The :class:`~phonometry.metrology.UncertaintyResult` of
        the combination, which has to be the combination of
        :attr:`standard_uncertainties_db`.
    :ivar coverage_factor: :math:`k`, 2 by both parts.
    """

    frequency_hz: float
    field: str
    names: tuple[str, ...]
    components: tuple[str, ...]
    standard_uncertainties_db: NDArray[np.float64]
    uncertainty: UncertaintyResult
    coverage_factor: float = _COVERAGE_FACTOR

    def __post_init__(self) -> None:
        """Refuse columns that disagree, and publish them read-only.

        :raises ValueError: for a frequency or coverage factor that is not
            positive, an unknown field, columns that do not hold one entry per
            component, a negative uncertainty, or an :attr:`uncertainty` that
            is not the root-sum-square of the components.
        """
        require_positive(self.frequency_hz, "frequency_hz")
        require_positive(self.coverage_factor, "coverage_factor")
        require_choice(self.field, "field", _FIELDS)
        count = len(self.names)
        if len(self.components) != count:
            msg = "ComparisonUncertaintyBudget: 'components' must hold one per name."
            raise ValueError(msg)
        column = np.array(self.standard_uncertainties_db, dtype=np.float64, ndmin=1)
        if column.shape != (count,):
            msg = (
                "ComparisonUncertaintyBudget: 'standard_uncertainties_db' must hold "
                f"one value per component ({count}); got shape {column.shape}."
            )
            raise ValueError(msg)
        if not np.all(np.isfinite(column)) or np.any(column < 0.0):
            msg = (
                "ComparisonUncertaintyBudget: 'standard_uncertainties_db' must be "
                "finite and non-negative."
            )
            raise ValueError(msg)
        object.__setattr__(self, "standard_uncertainties_db", read_only(column))
        combined = math.sqrt(float(np.sum(column**2)))
        if not math.isclose(
            float(self.uncertainty.combined_uncertainty),
            combined,
            rel_tol=_COMBINATION_REL_TOL,
            abs_tol=_COMBINATION_ABS_TOL_DB,
        ):
            msg = (
                "ComparisonUncertaintyBudget: 'uncertainty' must be the "
                "root-sum-square of 'standard_uncertainties_db'; build the budget "
                "with comparison_uncertainty_budget()."
            )
            raise ValueError(msg)

    @property
    def standard(self) -> str:
        """The designation whose table the budget follows."""
        return _STANDARDS[self.field]

    @property
    def combined_uncertainty_db(self) -> float:
        r""":math:`u_\mathrm{c}`, the combined standard uncertainty, in dB."""
        return float(self.uncertainty.combined_uncertainty)

    @property
    def expanded_uncertainty_db(self) -> float:
        r""":math:`U = k\,u_\mathrm{c}`, in dB."""
        return self.coverage_factor * self.combined_uncertainty_db

    @property
    def linear_combined_uncertainty_db(self) -> float:
        r""":math:`u_\mathrm{c}` combined in linear form, in dB.

        Each component converted to a relative uncertainty,
        :math:`r_i = 10^{u_i/20} - 1`, combined in quadrature and converted
        back, :math:`20\lg(1 + r_\mathrm{c})`: the "strict calculation" D.3
        mentions and 8.8 prefers. For components of a few hundredths of a
        decibel it differs from :attr:`combined_uncertainty_db` in the fourth
        decimal at most, which is why both parts accept the logarithmic form.
        """
        relative = 10.0 ** (self.standard_uncertainties_db / 20.0) - 1.0
        return 20.0 * math.log10(1.0 + math.sqrt(float(np.sum(relative**2))))

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot the standard uncertainty of each component, with
        :math:`u_\mathrm{c}`, :math:`k` and :math:`U`.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to :meth:`~matplotlib.axes.Axes.barh`.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_comparison_budget

        return plot_comparison_budget(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _component(value: float | Quantity, name: str) -> Quantity:
    """A component as a :class:`Quantity` of estimate 0.

    :raises ValueError: for a value that is negative or not finite.
    """
    if isinstance(value, Quantity):
        return Quantity(0.0, value.uncertainty, value.distribution, name=name)
    number = float(value)
    if not (math.isfinite(number) and number >= 0.0):
        msg = (
            f"The standard uncertainty of {name!r} must be finite and "
            f"non-negative; got {value!r}."
        )
        raise ValueError(msg)
    return Quantity(0.0, number, name=name)


def comparison_uncertainty_budget(
    standard_uncertainties_db: Mapping[str, float | Quantity],
    *,
    frequency_hz: float,
    field: str = "pressure",
    additional_components: Sequence[Quantity] = (),
    coverage_factor: float = _COVERAGE_FACTOR,
) -> ComparisonUncertaintyBudget:
    r"""The uncertainty budget of a comparison calibration at one frequency
    (IEC 61094-5:2016 Annex D; IEC 61094-8:2012 8.8 and Table 2).

    Each component is given as a standard uncertainty in dB, the column
    Table D.1 prints, or as a :class:`~phonometry.metrology.Quantity` whose
    standard uncertainty it takes: ``metrology.rectangular(0, 0.03)`` for a
    semi-range of 0,03 dB, say. They are keyed by the names of
    :data:`IEC61094_5_TABLE_D1` for a pressure calibration and of
    :data:`IEC61094_8_TABLE_2` for a free-field one; neither table is
    exhaustive (D.1, 8.1), so a component may be left out and
    ``additional_components`` adds the ones a set-up needs, such as the
    diameter correction of a WS3 microphone in the jig (Table D.1, special
    cases). The combination is :func:`~phonometry.metrology.combine_uncertainty`
    on the level model, every component with a sensitivity of 1, which is the
    root-sum-square of D.3; the expanded uncertainty is :math:`k = 2` times
    it, the coverage factor 7.9 and D.2 of the first part and 8.8 of the
    second report with.

    With the eight components of Table D.1 at 2 kHz the combined standard
    uncertainty is 0,0437 dB and the expanded one 0,087 dB. D.3 prints
    0,040 dB and 0,08 dB, which are not the root-sum-square of its own
    components (an erratum; see ``docs/ERRATA.md``).

    :param standard_uncertainties_db: The components, keyed by name, each a
        standard uncertainty in dB or a :class:`~phonometry.metrology.Quantity`.
    :param frequency_hz: The frequency the budget is for, in Hz.
    :param field: ``"pressure"`` (Table D.1, default) or ``"free_field"``
        (Table 2).
    :param additional_components: Further components, as named
        :class:`~phonometry.metrology.Quantity` objects (Default: none).
    :param coverage_factor: :math:`k` (Default: 2).
    :return: The :class:`ComparisonUncertaintyBudget`.
    :raises ValueError: for a key that is not a component of the field's
        table, an additional component without a name or with the name of
        another component, no component at all, or a value that is negative
        or not finite.
    """
    field = require_choice(field, "field", _FIELDS)
    table = _BUDGET_TABLES[field]
    unknown = [key for key in standard_uncertainties_db if key not in table]
    if unknown:
        msg = (
            f"{unknown} are not components of {_STANDARDS[field]}'s table; the "
            f"keys are {tuple(table)}. Pass other components through "
            "'additional_components'."
        )
        raise ValueError(msg)
    names: list[str] = []
    components: list[str] = []
    quantities: list[Quantity] = []
    for key, row in table.items():
        if key in standard_uncertainties_db:
            quantities.append(_component(standard_uncertainties_db[key], key))
            names.append(key)
            components.append(row.component)
    for extra in additional_components:
        if not extra.name or extra.name in names:
            msg = (
                "Each additional component needs a name of its own; got "
                f"{extra.name!r}."
            )
            raise ValueError(msg)
        quantities.append(_component(extra, extra.name))
        names.append(extra.name)
        components.append(extra.name)
    if not quantities:
        msg = "The budget needs at least one component."
        raise ValueError(msg)

    def model(*values: float) -> float:
        return float(sum(values))

    result = combine_uncertainty(model, quantities)
    return ComparisonUncertaintyBudget(
        frequency_hz=require_positive(frequency_hz, "frequency_hz"),
        field=field,
        names=tuple(names),
        components=tuple(components),
        standard_uncertainties_db=np.array([q.uncertainty for q in quantities]),
        uncertainty=result,
        coverage_factor=require_positive(coverage_factor, "coverage_factor"),
    )


# ---------------------------------------------------------------------------
# The effective free-field region of a time window (IEC 61094-8 B.1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FreeFieldRegion:
    r"""The effective free-field region of a time-selective calibration
    (IEC 61094-8:2012 B.1, Formula (B.1) and Figure B.1).

    A prolate spheroid generated by an ellipse with the acoustic centres of
    the source and of the microphone at its foci, :math:`d` apart, and the
    major diameter :math:`A = d + \tau c`. A reflection from any point on its
    surface arrives :math:`\tau` after the direct sound, at the end of the
    window; the device measured is inside, and any reflecting surface or
    obstacle has to be outside.

    :ivar source_distance_m: :math:`d`, the source to receiver separation, in
        m.
    :ivar window_time_s: :math:`\tau`, from the arrival of the sound at the
        microphone to the end of the window, in s.
    :ivar speed_of_sound: :math:`c` at the conditions of the test, in m/s.
    """

    source_distance_m: float
    window_time_s: float
    speed_of_sound: float

    def __post_init__(self) -> None:
        """Refuse a separation, window or speed that is not positive.

        :raises ValueError: for any of the three not finite and positive.
        """
        for name in ("source_distance_m", "window_time_s", "speed_of_sound"):
            object.__setattr__(self, name, require_positive(getattr(self, name), name))

    @property
    def major_axis_m(self) -> float:
        r""":math:`A = d + \tau c`, Formula (B.1), in m."""
        return self.source_distance_m + self.window_time_s * self.speed_of_sound

    @property
    def semi_minor_axis_m(self) -> float:
        r""":math:`b = \sqrt{(A/2)^2 - (d/2)^2}`, the radius of the region at
        mid-way between the source and the microphone, in m: the clearance a
        surface parallel to the axis needs to be outside it.
        """
        half_major = self.major_axis_m / 2.0
        half_distance = self.source_distance_m / 2.0
        return math.sqrt(half_major**2 - half_distance**2)

    @property
    def rod_clearance_m(self) -> float:
        r""":math:`(A - d)/2 = \tau c/2`, how far the region reaches behind the
        microphone along the axis, in m: the mounting rod "should be
        sufficiently long so that the end opposite to the microphone is
        completely outside" it (B.1).
        """
        return (self.major_axis_m - self.source_distance_m) / 2.0

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the region in a plane through the axis, as Figure B.1 draws it.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the boundary of the region.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_free_field_region

        return plot_free_field_region(
            self, ax=ax, language=check_language(language), **kwargs
        )


def free_field_region(
    source_distance_m: float,
    window_time_s: float,
    *,
    temperature_c: float = _REFERENCE_TEMPERATURE_C,
    static_pressure_kpa: float = _REFERENCE_STATIC_PRESSURE_KPA,
    relative_humidity_percent: float = _REFERENCE_RELATIVE_HUMIDITY_PERCENT,
) -> FreeFieldRegion:
    r"""The effective free-field region of a time window (IEC 61094-8:2012
    B.1).

    Formula (B.1), :math:`A = d + \tau c`, with :math:`c` "the speed of sound
    at the prevailing environmental conditions", which is taken from the
    IEC 61094-2:2009 Annex F air of :func:`~phonometry.fluids.air`. The
    conditions default to the reference conditions of clause 4, 23,0 °C,
    101,325 kPa and 50 %.

    :param source_distance_m: :math:`d`, the separation of the acoustic
        centres of the source and the microphone, in m.
    :param window_time_s: :math:`\tau`, from the arrival of the sound at the
        microphone to the end of the time window, in s.
    :param temperature_c: The air temperature, in °C (Default: 23,0).
    :param static_pressure_kpa: The static pressure, in kPa (Default:
        101,325).
    :param relative_humidity_percent: The relative humidity, in % (Default:
        50).
    :return: The :class:`FreeFieldRegion`.
    :raises ValueError: for a separation or window that is not positive, or
        conditions Annex F refuses.
    """
    from ..fluids.air import air

    pressure_kpa = require_positive(static_pressure_kpa, "static_pressure_kpa")
    medium = air(
        temperature_c=temperature_c,
        static_pressure_pa=1000.0 * pressure_kpa,
        relative_humidity_percent=relative_humidity_percent,
    )
    return FreeFieldRegion(
        source_distance_m=source_distance_m,
        window_time_s=window_time_s,
        speed_of_sound=medium.speed_of_sound,
    )
