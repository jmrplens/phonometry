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
:func:`sequential_comparison` computes it, with the :class:`MonitorReadings`
of the monitor or without.

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
the test (:func:`~phonometry.fluids.air`). Turned round,
:func:`reflection_free_window_s` gives the longest window that keeps a
reflection of a known path outside it.

**The phase of the sensitivity** (IEC 61094-5 5.1.1, IEC 61094-8 5.1). Both
parts carry the phase over with the modulus: IEC 61094-5 calculates "the
sensitivity (both modulus and phase) of the test microphone", and IEC
61094-8 "both the modulus and phase of the free-field sensitivity of the
microphone under test". The model of D.2 holds for the complex ratios, so
the phase follows the level term by term:

.. math::

   \varphi_\mathrm{test} = \varphi_\mathrm{ref} + \arg R_V - \arg R_P

and the interchange of Annex C cancels the phase shifts of the two channels
and of the field just as (C.3) cancels their gains,
:math:`\varphi_\mathrm{ref} - \varphi_\mathrm{test} =
\tfrac12(\Phi_\mathrm{C12} - \Phi_\mathrm{C21})`. In a free field the phases
have to be referred to the acoustic centres of the microphones (5.1 of the
second part), which 7.3 positions "at the measurement points"; in a
sequential substitution both centres go to the same point in turn, and the
pressures on the two microphones have the same phase there. The phase inputs
of a calibration travel together, as a :class:`SimultaneousComparisonPhase`
or a :class:`SequentialComparisonPhase`.

**Different acoustic impedances** (IEC 61094-5 7.4 and 7.5). Two microphones
of different acoustic impedance do not see the same sound pressure; neither
clause prints a model, and both ask for the effect to be assessed and taken
into the budget. :func:`impedance_pressure_ratio` writes it in one form, each
microphone's equivalent volume :math:`V_\mathrm{e}` (IEC 61094-1 6.2.2)
against the equivalent volume :math:`V_x` of what it works into,

.. math::

   R_P = \frac{V_x + V_\mathrm{e,ref}}{V_x + V_\mathrm{e,test}}

for two circuits: a closed coupler, the printed Formula (3) of IEC 61094-2,
for a sequential substitution; and, for a simultaneous excitation, each
microphone behind the air between the two, a divider that is this library's
reading of the sentence of Table D.1 ("Microphone impedance") that puts them
in series, which prints no circuit.
:meth:`ReciprocityMicrophone.complex_equivalent_volume_m3` gives
:math:`V_\mathrm{e}` from the lumped parameters of IEC 61094-2 E.4.

**Time-selective processing** (IEC 61094-8 Annex B). A free field can be
simulated by keeping only the direct sound of an impulse response:
:func:`time_selective_response` weights the response with a time window
(B.1.3), with the "'tapered' edges" B.1.2 says it "normally has", and
transforms what is left by Formula (B.2), at any frequency. The impulse response comes from any of the methods of B.2 to B.6:
:func:`stepped_sine_impulse_response` takes a stepped-sine measurement to
the time domain by Formula (B.3), and the sweeps, the maximum length
sequences and the random noise of B.3 to B.5 are those of
:mod:`phonometry.room` and :mod:`phonometry.electroacoustics`. For the direct
impulse method of B.6, :func:`rectangular_pulse` is the pulse of Formula
(B.10) and :func:`rectangular_pulse_duration_s` the duration whose first
spectral zero lies an order of magnitude above the frequencies of interest.

Two printed values the library does not follow
----------------------------------------------

**IEC 61094-5 D.3.** The root-sum-square of the eight components Table D.1
prints is 0,0437 dB, not the 0,040 dB D.3 states; with :math:`k = 2` it is
0,087 dB rather than 0,08 dB. :func:`comparison_uncertainty_budget` gives the
sum of the printed components, and the defect is in ``docs/ERRATA.md``.

**IEC 61094-8 B.10.** The spectrum of Formula (B.10) is that of a rectangular
pulse of duration :math:`2b`, although the text calls :math:`b` the duration.
The formula and the first zero it puts at :math:`1/(2b)` agree, so the library
follows them and reads :math:`b` as the half-duration:
:func:`rectangular_pulse` takes the whole duration :math:`T = 2b`. The defect
is in ``docs/ERRATA.md``.

The IEC 61183 diffuse-field comparison of clause 5
(:func:`~phonometry.metrology.diffuse_field_sensitivity`) is the same
sequential comparison without a monitor, and computes its level difference and
its sensitivity level through this module.
"""

from __future__ import annotations

import math
from dataclasses import KW_ONLY, dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.frozen import read_only
from .._internal.validation import (
    require_above_absolute_zero,
    require_choice,
    require_finite_array,
    require_non_negative,
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
    "ImpedancePressureRatio",
    "JigDiameterCorrection",
    "MonitorReadings",
    "RectangularPulse",
    "ReferenceCalibrationRow",
    "SequentialComparisonPhase",
    "SimultaneousComparisonPhase",
    "SteppedSineImpulseResponse",
    "TimeSelectiveResponse",
    "comparison_uncertainty_budget",
    "environmental_sensitivity_correction",
    "free_field_region",
    "impedance_pressure_ratio",
    "jig_diameter_correction",
    "rectangular_pulse",
    "rectangular_pulse_duration_s",
    "reflection_free_window_s",
    "sequential_comparison",
    "simultaneous_comparison",
    "stepped_sine_impulse_response",
    "time_selective_response",
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

#: The names the monitor's readings go by in a refusal and in the rows the
#: sequential comparison lines up by determination.
_MONITOR_REFERENCE_PHASE = "monitor.reference_phase_deg"
_MONITOR_TEST_PHASE = "monitor.test_phase_deg"
_MONITOR_REFERENCE_LEVEL = "monitor.reference_level_db"
_MONITOR_TEST_LEVEL = "monitor.test_level_db"

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

#: A full turn, in degrees: a phase is known modulo it.
_FULL_TURN_DEG = 360.0

#: Half a turn, in degrees: a phase or a difference of phases is reported in
#: the interval from minus half a turn, excluded, to half a turn, included,
#: the one :func:`numpy.angle` reports.
_HALF_TURN_DEG = 180.0

#: IEC 61094-1:2000 6.2.2, the ratio of the specific heat capacities at the
#: reference conditions in the definition of the equivalent volume of a
#: microphone: "The value of κr shall be taken as 1,40".
_KAPPA_REFERENCE = 1.40

#: The window shapes the library offers, among those IEC 61094-8 B.1.3 names
#: ("Hann, Hamming, Tukey, Butterworth Cosine and Gaussian"), and the
#: rectangular window it does not recommend, kept for comparison.
_WINDOW_SHAPES = ("tukey", "hann", "hamming", "rectangular")

#: The fraction of a Tukey window that is taper, split between its two edges:
#: an eighth of the window rises at the start and an eighth falls at the end.
#: B.1.2 says the window "normally has 'tapered' edges" so as not to produce
#: artefacts, and no clause of Annex B prints a proportion; this is the
#: library's choice.
_DEFAULT_TAPER_FRACTION = 0.25

#: IEC 61094-8 B.6.1: the first zero of the pulse spectrum "must be
#: approximately an order of magnitude higher than the upper limit of the
#: frequency range of interest".
_PULSE_ZERO_RATIO = 10.0

#: The fewest samples a time window can hold: a window of one sample is a
#: single value and has no shape.
_MIN_WINDOW_SAMPLES = 2

#: How close a time, in samples, has to sit to a sample to be read as that
#: sample: the rounding of a value that went through arithmetic.
_SAMPLE_TOLERANCE = 1e-9

#: How many products of a frequency and a sample the transform holds at once.
_TRANSFORM_BLOCK = 1 << 22

#: How close a stepped-sine frequency axis has to be to a uniform one, and its
#: first frequency to 0 Hz, relative to the step.
_STEP_REL_TOL = 1e-9


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


def _wrapped_deg(phase_deg: ArrayLike) -> NDArray[np.float64]:
    """A phase or a difference of phases, in degrees, taken into the half-open
    interval from -180° (excluded) to 180° (included).
    """
    phase = np.asarray(phase_deg, dtype=np.float64)
    return _HALF_TURN_DEG - np.mod(_HALF_TURN_DEG - phase, _FULL_TURN_DEG)


def _mean_phase_deg(rows: NDArray[np.float64]) -> NDArray[np.float64]:
    """The mean of the phases of several determinations, one row each.

    Each row is taken against the first, so that two readings either side of
    ±180° average to a phase next to them and not to one half a turn away.
    """
    first = rows[0]
    deviations = _wrapped_deg(rows - first)
    return _wrapped_deg(first + np.mean(deviations, axis=0))


def _interchange_phase_difference_deg(
    channel_phase_difference_deg: NDArray[np.float64],
    interchanged_channel_phase_difference_deg: NDArray[np.float64],
) -> NDArray[np.float64]:
    r""":math:`\arg R_V` from the two channel phase differences.

    The phase counterpart of Formula (C.3): with the reference as microphone 1,
    :math:`\varphi_\mathrm{test} - \varphi_\mathrm{ref} =
    -\tfrac12(\Phi_\mathrm{C12} - \Phi_\mathrm{C21})`. The difference of the two
    readings is twice the phase difference of the microphones and is taken
    into one turn first, so the half is unique while the microphones differ
    by less than a quarter of a turn.
    """
    return -0.5 * _wrapped_deg(
        channel_phase_difference_deg - interchanged_channel_phase_difference_deg
    )


def _require_phase_pair(
    reference_sensitivity_phase_deg: ArrayLike | None,
    *,
    readings_given: bool,
    readings: str,
) -> None:
    """Refuse a reference phase without the phase readings, or the readings
    without the reference phase: the test microphone's phase needs both.

    :raises ValueError: when one is given without the other.
    """
    if (reference_sensitivity_phase_deg is None) == readings_given:
        msg = (
            "The phase of the test microphone needs both the reference's phase, "
            f"'reference_sensitivity_phase_deg', and the phase readings, {readings}; "
            "give both or neither."
        )
        raise ValueError(msg)


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
    :ivar reference_sensitivity_phase_deg: :math:`\varphi_\mathrm{ref}`, the
        phase of the reference microphone's sensitivity, in degrees, or
        ``None`` for a calibration of the level alone.
    :ivar output_phase_differences_deg: :math:`\arg R_V` of each
        determination, one row per determination, in degrees, or ``None``.
    :ivar pressure_phase_difference_deg: :math:`\arg R_P`, in degrees, or
        ``None``.
    """

    frequencies_hz: NDArray[np.float64]
    reference_sensitivity_level_db: NDArray[np.float64]
    output_level_differences_db: NDArray[np.float64]
    pressure_level_difference_db: NDArray[np.float64]
    corrections_db: Mapping[str, NDArray[np.float64]]
    field: str
    excitation: str
    expanded_uncertainty_db: NDArray[np.float64] | None = None
    _: KW_ONLY
    reference_sensitivity_phase_deg: NDArray[np.float64] | None = None
    output_phase_differences_deg: NDArray[np.float64] | None = None
    pressure_phase_difference_deg: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        """Refuse columns that disagree or an unknown field or excitation, and
        publish everything read-only.

        :raises ValueError: for frequencies that are not positive and
            increasing, a column or a correction that is not one finite value
            per frequency, determinations that are not one row per
            determination, a negative uncertainty, an unknown field or
            excitation, or the phase of the reference without the phase
            readings, or the other way round.
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
        self._publish_phases(count, rows.shape[0])

    def _publish_phases(self, count: int, determinations: int) -> None:
        """Check the three phase columns against each other and the levels,
        and publish them read-only.

        :raises ValueError: for the reference phase without the phase
            readings or the other way round, a pressure phase without either,
            or phase readings whose determinations are not those of the
            levels.
        """
        _require_phase_pair(
            self.reference_sensitivity_phase_deg,
            readings_given=self.output_phase_differences_deg is not None,
            readings="'output_phase_differences_deg'",
        )
        if self.output_phase_differences_deg is None:
            if self.pressure_phase_difference_deg is not None:
                msg = (
                    "ComparisonCalibration: 'pressure_phase_difference_deg' needs "
                    "the phases of the calibration."
                )
                raise ValueError(msg)
            return
        reference = _band_column(
            self.reference_sensitivity_phase_deg,  # type: ignore[arg-type]
            "reference_sensitivity_phase_deg",
            count,
        )
        phases = _determinations(
            self.output_phase_differences_deg, "output_phase_differences_deg", count
        )
        if phases.shape[0] not in {1, determinations}:
            msg = (
                "ComparisonCalibration: 'output_phase_differences_deg' must hold one "
                f"row per determination ({determinations}) or a single row; got "
                f"{phases.shape[0]}."
            )
            raise ValueError(msg)
        pressure = _band_column(
            0.0
            if self.pressure_phase_difference_deg is None
            else self.pressure_phase_difference_deg,
            "pressure_phase_difference_deg",
            count,
        )
        object.__setattr__(
            self, "reference_sensitivity_phase_deg", read_only(reference.copy())
        )
        object.__setattr__(
            self, "output_phase_differences_deg", read_only(phases.copy())
        )
        object.__setattr__(
            self, "pressure_phase_difference_deg", read_only(pressure.copy())
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

    @property
    def output_phase_difference_deg(self) -> NDArray[np.float64] | None:
        r""":math:`\arg R_V`, the mean over the determinations, in degrees, or
        ``None`` for a calibration of the level alone.
        """
        if self.output_phase_differences_deg is None:
            return None
        return _mean_phase_deg(self.output_phase_differences_deg)

    @property
    def sensitivity_phase_deg(self) -> NDArray[np.float64] | None:
        r""":math:`\varphi_\mathrm{test} = \varphi_\mathrm{ref} + \arg R_V -
        \arg R_P`, in degrees from -180° (excluded) to 180°, or ``None`` for a
        calibration of the level alone (IEC 61094-5 5.1.1, IEC 61094-8 5.1).
        """
        mean = self.output_phase_difference_deg
        if mean is None:
            return None
        return _wrapped_deg(
            self.reference_sensitivity_phase_deg  # type: ignore[operator]
            + mean
            - self.pressure_phase_difference_deg
        )

    def plot(
        self,
        ax: Axes | None = None,
        *,
        quantity: str = "level",
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        r"""Plot :math:`L_\mathrm{test}` and the reference's level against
        frequency, with the expanded uncertainty as a band when it is known,
        or the two phases.

        The reference's level is :math:`L_\mathrm{ref}`, or, in a free field
        against a pressure-calibrated reference, :math:`L_\mathrm{ref}` plus
        its free-field difference: the level the test microphone was
        compared with.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param quantity: ``"level"`` (default), or ``"phase"`` for
            :math:`\varphi_\mathrm{test}` and :math:`\varphi_\mathrm{ref}` of
            a calibration that carries them.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the curve of the microphone under test.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        :raises ValueError: for an unknown quantity, or the phase of a
            calibration of the level alone.
        """
        from .._i18n import check_language
        from .._plot.metrology import (
            plot_comparison_calibration,
            plot_comparison_phase,
        )

        require_choice(quantity, "quantity", ("level", "phase"))
        language = check_language(language)
        if quantity == "level":
            return plot_comparison_calibration(self, ax=ax, language=language, **kwargs)
        if self.sensitivity_phase_deg is None:
            msg = "This calibration carries no phase; plot its 'level'."
            raise ValueError(msg)
        return plot_comparison_phase(self, ax=ax, language=language, **kwargs)


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
    phases: _Phases | None = None,
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
        reference_sensitivity_phase_deg=None if phases is None else phases.reference,
        output_phase_differences_deg=None if phases is None else phases.output,
        pressure_phase_difference_deg=None if phases is None else phases.pressure,
    )


@dataclass(frozen=True)
class _Phases:
    r"""The phase inputs of a calibration, read and combined.

    :ivar reference: :math:`\varphi_\mathrm{ref}`, in degrees.
    :ivar output: :math:`\arg R_V`, one row per determination, in degrees.
    :ivar pressure: :math:`\arg R_P`, in degrees.
    """

    reference: NDArray[np.float64]
    output: NDArray[np.float64]
    pressure: NDArray[np.float64]


@dataclass(frozen=True)
class SimultaneousComparisonPhase:
    r"""The phase inputs of a calibration by simultaneous excitation
    (IEC 61094-5:2016 5.1.1, IEC 61094-8:2012 5.1).

    They travel together because the phase of the test microphone needs all of
    them at once: the phase of the reference's sensitivity it is carried over
    from, and the phase readings of the two channels that carry it, given as
    the level readings are; :math:`\arg R_P` completes them where the pressures
    on the two microphones differ in phase. Pass one to
    :func:`simultaneous_comparison` as ``phase``.

    :param reference_sensitivity_phase_deg: :math:`\varphi_\mathrm{ref}`, the
        phase of the reference's sensitivity, in degrees, one value or one per
        frequency.
    :param channel_phase_difference_deg: :math:`\Phi_\mathrm{C12}`, the phase
        of channel 1's reading re channel 2's with the reference on channel 1,
        in degrees, one row per determination.
    :param interchanged_channel_phase_difference_deg:
        :math:`\Phi_\mathrm{C21}`, the same after the interchange, in degrees
        (Default: None; given exactly when the interchanged level reading is).
    :param pressure_phase_difference_deg: :math:`\arg R_P`, the phase of the
        effective sound pressure on the test microphone re that on the
        reference, in degrees (Default: None, 0).
    """

    _: KW_ONLY
    reference_sensitivity_phase_deg: ArrayLike
    channel_phase_difference_deg: ArrayLike
    interchanged_channel_phase_difference_deg: ArrayLike | None = None
    pressure_phase_difference_deg: ArrayLike | None = None


@dataclass(frozen=True)
class SequentialComparisonPhase:
    r"""The phase inputs of a calibration by sequential excitation
    (IEC 61094-5:2016 5.1.1, IEC 61094-8:2012 5.1).

    They travel together because the phase of the test microphone needs all of
    them at once: the phase of the reference's sensitivity it is carried over
    from, and the phases of the two outputs, read against the monitor's output
    or against the signal driving the source; :math:`\arg R_P` completes them
    where the pressures on the two microphones differ in phase. The monitor's
    own phases are read with its levels, in :class:`MonitorReadings`. Pass one
    to :func:`sequential_comparison` as ``phase``.

    :param reference_sensitivity_phase_deg: :math:`\varphi_\mathrm{ref}`, the
        phase of the reference's sensitivity, in degrees, one value or one per
        frequency.
    :param reference_output_phase_deg: The phase of the reference
        microphone's output, in degrees, one row per determination.
    :param test_output_phase_deg: The phase of the test microphone's output,
        in degrees, one row per determination.
    :param pressure_phase_difference_deg: :math:`\arg R_P`, in degrees
        (Default: None, 0).
    """

    _: KW_ONLY
    reference_sensitivity_phase_deg: ArrayLike
    reference_output_phase_deg: ArrayLike
    test_output_phase_deg: ArrayLike
    pressure_phase_difference_deg: ArrayLike | None = None


@dataclass(frozen=True)
class MonitorReadings:
    r"""The readings of the monitor microphone that watches the source of a
    sequential calibration (IEC 61094-5:2016 5.1.3, IEC 61094-8:2012 A.2).

    They travel together because they are one instrument's: the monitor is
    read in the measurement of each microphone, and each microphone's output
    is taken re the monitor reading taken with it, so a source that drifts
    between the two measurements cancels in the quotient of the two ratios.
    Its phases are read with its levels when the calibration carries the
    phase. Pass one to :func:`sequential_comparison` as ``monitor``.

    :param reference_level_db: :math:`20\lg V_\mathrm{mon,1}`, the monitor's
        output level in the measurement of the reference, in dB, one row per
        determination.
    :param test_level_db: :math:`20\lg V_\mathrm{mon,2}`, the monitor's
        output level in the measurement of the test microphone, in dB.
    :param reference_phase_deg: :math:`\varphi_\mathrm{mon,1}`, the monitor's
        phase in the measurement of the reference, in degrees (Default: None).
    :param test_phase_deg: :math:`\varphi_\mathrm{mon,2}`, the monitor's
        phase in the measurement of the test microphone, in degrees (Default:
        None; given with the other or not at all).
    :raises ValueError: for one phase without the other.
    """

    _: KW_ONLY
    reference_level_db: ArrayLike
    test_level_db: ArrayLike
    reference_phase_deg: ArrayLike | None = None
    test_phase_deg: ArrayLike | None = None

    def __post_init__(self) -> None:
        """Refuse one phase without the other.

        :raises ValueError: when only one of the two phases is given.
        """
        if (self.reference_phase_deg is None) != (self.test_phase_deg is None):
            msg = (
                "MonitorReadings: give both 'reference_phase_deg' and "
                "'test_phase_deg', or neither."
            )
            raise ValueError(msg)


def _pressure_phase(
    pressure_phase_difference_deg: ArrayLike | None, count: int
) -> NDArray[np.float64]:
    r""":math:`\arg R_P` as a column, 0 when it is not given."""
    value = (
        0.0 if pressure_phase_difference_deg is None else pressure_phase_difference_deg
    )
    return _band_column(value, "pressure_phase_difference_deg", count)


def _simultaneous_phases(
    count: int,
    phase: SimultaneousComparisonPhase | None,
    *,
    interchanged: bool,
) -> _Phases | None:
    """The phases of a simultaneous calibration, or ``None`` without them.

    The phase readings follow the level readings: the interchanged one is
    given exactly when the interchanged level is.

    :raises ValueError: for an interchanged phase reading without the
        interchanged level or the other way round.
    """
    if phase is None:
        return None
    if (phase.interchanged_channel_phase_difference_deg is not None) != interchanged:
        msg = (
            "The phase readings follow the level readings: give "
            "'interchanged_channel_phase_difference_deg' exactly when "
            "'interchanged_channel_difference_db' is given."
        )
        raise ValueError(msg)
    first = _determinations(
        phase.channel_phase_difference_deg, "channel_phase_difference_deg", count
    )
    if phase.interchanged_channel_phase_difference_deg is None:
        output = _wrapped_deg(-first)
    else:
        second = _determinations(
            phase.interchanged_channel_phase_difference_deg,
            "interchanged_channel_phase_difference_deg",
            count,
        )
        _common_rows(
            {
                "channel_phase_difference_deg": first,
                "interchanged_channel_phase_difference_deg": second,
            }
        )
        output = _interchange_phase_difference_deg(first, second)
    return _Phases(
        reference=_band_column(
            phase.reference_sensitivity_phase_deg,
            "reference_sensitivity_phase_deg",
            count,
        ),
        output=output,
        pressure=_pressure_phase(phase.pressure_phase_difference_deg, count),
    )


def _sequential_phases(
    count: int,
    phase: SequentialComparisonPhase | None,
    monitor: MonitorReadings | None,
) -> _Phases | None:
    """The phases of a sequential calibration, or ``None`` without them.

    Each output phase is taken re the monitor's phase in the same measurement
    when the monitor was read in phase, and as read otherwise.

    :raises ValueError: for monitor phases without the output phases they are
        read against.
    """
    if phase is None:
        if monitor is not None and monitor.reference_phase_deg is not None:
            msg = (
                "The monitor phases need the output phases they are read "
                "against; pass 'phase' too."
            )
            raise ValueError(msg)
        return None
    rows = {
        "reference_output_phase_deg": _determinations(
            phase.reference_output_phase_deg, "reference_output_phase_deg", count
        ),
        "test_output_phase_deg": _determinations(
            phase.test_output_phase_deg, "test_output_phase_deg", count
        ),
    }
    if (
        monitor is not None
        and monitor.reference_phase_deg is not None
        and monitor.test_phase_deg is not None
    ):
        rows[_MONITOR_REFERENCE_PHASE] = _determinations(
            monitor.reference_phase_deg, _MONITOR_REFERENCE_PHASE, count
        )
        rows[_MONITOR_TEST_PHASE] = _determinations(
            monitor.test_phase_deg, _MONITOR_TEST_PHASE, count
        )
    _common_rows(rows)
    test = rows["test_output_phase_deg"]
    reference = rows["reference_output_phase_deg"]
    if _MONITOR_TEST_PHASE in rows:
        test = test - rows[_MONITOR_TEST_PHASE]
        reference = reference - rows[_MONITOR_REFERENCE_PHASE]
    return _Phases(
        reference=_band_column(
            phase.reference_sensitivity_phase_deg,
            "reference_sensitivity_phase_deg",
            count,
        ),
        output=np.atleast_2d(_wrapped_deg(test - reference)),
        pressure=_pressure_phase(phase.pressure_phase_difference_deg, count),
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
    phase: SimultaneousComparisonPhase | None = None,
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

    **Phase** (IEC 61094-5 5.1.1, IEC 61094-8 5.1). With the phase of the
    reference's sensitivity and the phase readings of the two channels, given
    together as a :class:`SimultaneousComparisonPhase`, the calibration
    carries the phase of the test microphone too. The phase of
    each channel's reading re the other's adds up as its level does in (C.1)
    and (C.2), so their difference cancels the phase shifts of the channels
    and of the field:

    .. math::

       \varphi_\mathrm{ref} - \varphi_\mathrm{test}
       = \tfrac12\left(\Phi_\mathrm{C12} - \Phi_\mathrm{C21}\right)

    with the difference of the two readings taken into one turn before it is
    halved, so the result is unique while the two microphones differ by less
    than 90°. Without the interchange, :math:`-\Phi_\mathrm{C12}` is taken as
    :math:`\arg R_V`. Neither part prints this form; it is (C.3) written for
    the complex ratio the sensitivity "both modulus and phase" is.

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
    :param phase: The :class:`SimultaneousComparisonPhase` of the
        calibration: the reference's phase, the phase readings and
        :math:`\arg R_P` (Default: None, a calibration of the level alone).
    :return: The :class:`ComparisonCalibration`.
    :raises ValueError: for an unknown field, a pressure calibration without
        the interchange, a free-field correction on a pressure calibration, an
        environmental correction made at other frequencies, readings whose
        numbers of determinations disagree, any column that is not one
        finite value per frequency, or phase readings that do not follow the
        level readings.
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
    phases = _simultaneous_phases(
        count, phase, interchanged=interchanged_channel_difference_db is not None
    )
    if phases is not None:
        _common_rows({"level readings": ratios, "phase readings": phases.output})
    return _calibration(
        frequencies,
        reference_sensitivity_level_db,
        ratios,
        phases=phases,
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
    monitor: MonitorReadings | None = None,
    field: str = "pressure",
    pressure_level_difference_db: ArrayLike = 0.0,
    corrections_db: Mapping[str, ArrayLike] | None = None,
    reference_environment: EnvironmentalSensitivityCorrection | None = None,
    test_environment: EnvironmentalSensitivityCorrection | None = None,
    reference_free_field_difference_db: ArrayLike | None = None,
    expanded_uncertainty_db: ArrayLike | None = None,
    phase: SequentialComparisonPhase | None = None,
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

    **Phase** (IEC 61094-5 5.1.1, IEC 61094-8 5.1). With the phase of the
    reference's sensitivity and the phases of the two outputs, given together
    as a :class:`SequentialComparisonPhase` and read against the monitor's
    output (its phases in the :class:`MonitorReadings`) or against the signal
    driving the source, the calibration carries the phase of the test
    microphone too, the quotient of the ratios written for their phases:

    .. math::

       \arg R_V = (\varphi_\mathrm{test} - \varphi_\mathrm{mon,2})
       - (\varphi_\mathrm{ref} - \varphi_\mathrm{mon,1})

    In a free field the phases are those at the acoustic centres of the
    microphones (IEC 61094-8 5.1); with each centre placed in turn at the
    same measurement point (7.3), :math:`\arg R_P` is 0.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param reference_sensitivity_level_db: :math:`L_\mathrm{ref}`, the
        reference microphone's sensitivity level, in dB re 1 V/Pa.
    :param reference_output_level_db: :math:`20\lg V_\mathrm{ref}`, the
        reference microphone's output level, in dB re any voltage the test
        microphone is read against too.
    :param test_output_level_db: :math:`20\lg V_\mathrm{test}`, the test
        microphone's output level, in dB re the same voltage.
    :param monitor: The :class:`MonitorReadings` of a monitor microphone,
        :math:`20\lg V_\mathrm{mon,1}` and :math:`20\lg V_\mathrm{mon,2}`
        in the measurements of the reference and of the test microphone, with
        their phases when the calibration carries the phase (Default: None,
        no monitor).
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
    :param phase: The :class:`SequentialComparisonPhase` of the calibration:
        the reference's phase, the output phases and :math:`\arg R_P`
        (Default: None, a calibration of the level alone).
    :return: The :class:`ComparisonCalibration`.
    :raises ValueError: for an unknown field, a free-field correction on a
        pressure calibration, an environmental correction made at other
        frequencies, readings whose numbers of determinations disagree, any
        column that is not one finite value per frequency, or monitor phases
        without the output phases.
    """
    field = require_choice(field, "field", _FIELDS)
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    readings = {
        "reference_output_level_db": _determinations(
            reference_output_level_db, "reference_output_level_db", count
        ),
        "test_output_level_db": _determinations(
            test_output_level_db, "test_output_level_db", count
        ),
    }
    if monitor is not None:
        readings[_MONITOR_REFERENCE_LEVEL] = _determinations(
            monitor.reference_level_db, _MONITOR_REFERENCE_LEVEL, count
        )
        readings[_MONITOR_TEST_LEVEL] = _determinations(
            monitor.test_level_db, _MONITOR_TEST_LEVEL, count
        )
    _common_rows(readings)
    ratios = _output_level_difference_db(
        readings["test_output_level_db"],
        readings["reference_output_level_db"],
        readings.get(_MONITOR_TEST_LEVEL),
        readings.get(_MONITOR_REFERENCE_LEVEL),
    )
    phases = _sequential_phases(count, phase, monitor)
    if phases is not None:
        _common_rows({"level readings": ratios, "phase readings": phases.output})
    return _calibration(
        frequencies,
        reference_sensitivity_level_db,
        np.atleast_2d(ratios),
        phases=phases,
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
    return FreeFieldRegion(
        source_distance_m=source_distance_m,
        window_time_s=window_time_s,
        speed_of_sound=_speed_of_sound(
            temperature_c, static_pressure_kpa, relative_humidity_percent
        ),
    )


def _speed_of_sound(
    temperature_c: float, static_pressure_kpa: float, relative_humidity_percent: float
) -> float:
    """The speed of sound of the IEC 61094-2 Annex F air, in m/s.

    :raises ValueError: for conditions Annex F refuses or a pressure that is
        not positive.
    """
    from ..fluids.air import air

    pressure_kpa = require_positive(static_pressure_kpa, "static_pressure_kpa")
    medium = air(
        temperature_c=temperature_c,
        static_pressure_pa=1000.0 * pressure_kpa,
        relative_humidity_percent=relative_humidity_percent,
    )
    return float(medium.speed_of_sound)


def reflection_free_window_s(
    source_distance_m: float,
    reflected_path_m: float,
    *,
    temperature_c: float = _REFERENCE_TEMPERATURE_C,
    static_pressure_kpa: float = _REFERENCE_STATIC_PRESSURE_KPA,
    relative_humidity_percent: float = _REFERENCE_RELATIVE_HUMIDITY_PERCENT,
) -> float:
    r"""The longest time window that keeps a reflection outside the effective
    free-field region (IEC 61094-8:2012 B.1 and B.1.3 a)).

    A point on the boundary of the region of Formula (B.1) reflects along a
    path of the major diameter :math:`A = d + \tau c`, from the source to it
    and on to the microphone, so a reflection whose path is :math:`L` stays
    outside the region, and out of the window, while

    .. math::

       \tau \le \frac{L - d}{c}

    with :math:`\tau` measured from the arrival of the direct sound. B.1.3
    places the window by "the relative distance between source and
    microphone [...] and from the source to the walls or other reflecting
    objects"; for a plane reflector the path is that of the image of the
    source in it. The tapered edge the window "normally has" (B.1.2) has to
    fall within this time too.

    :param source_distance_m: :math:`d`, the separation of the acoustic
        centres of the source and the microphone, in m.
    :param reflected_path_m: :math:`L`, the length of the shortest reflected
        path, from the source by the reflector to the microphone, in m.
    :param temperature_c: The air temperature, in °C (Default: 23,0).
    :param static_pressure_kpa: The static pressure, in kPa (Default:
        101,325).
    :param relative_humidity_percent: The relative humidity, in % (Default:
        50).
    :return: :math:`(L - d)/c`, in s.
    :raises ValueError: for a separation that is not positive, a reflected
        path that is not longer than the direct one, or conditions Annex F
        refuses.
    """
    distance = require_positive(source_distance_m, "source_distance_m")
    path = require_positive(reflected_path_m, "reflected_path_m")
    if path <= distance:
        msg = (
            f"A reflected path of {path:g} m is not longer than the direct one of "
            f"{distance:g} m; a reflection travels further than the direct sound."
        )
        raise ValueError(msg)
    speed = _speed_of_sound(
        temperature_c, static_pressure_kpa, relative_humidity_percent
    )
    return (path - distance) / speed


# ---------------------------------------------------------------------------
# Different acoustic impedances (IEC 61094-5 7.4 and 7.5)
# ---------------------------------------------------------------------------


def _complex_column(values: ArrayLike, name: str, count: int) -> NDArray[np.complex128]:
    """A finite complex column of one value per frequency, a scalar spread over
    all.

    :raises ValueError: for a value that is not finite or a column that is
        neither a scalar nor one value per frequency.
    """
    try:
        column = np.asarray(values, dtype=np.complex128).reshape(-1)
    except (TypeError, ValueError) as exc:
        msg = f"'{name}' must be numeric."
        raise ValueError(msg) from exc
    if column.size == 0 or not np.all(np.isfinite(column)):
        msg = f"'{name}' must contain only finite values."
        raise ValueError(msg)
    if column.size == 1:
        return np.full(count, column[0], dtype=np.complex128)
    if column.size != count:
        msg = (
            f"'{name}' must hold one value per frequency ({count}) or a single "
            f"value; got {column.size}."
        )
        raise ValueError(msg)
    return column


@dataclass(frozen=True)
class ImpedancePressureRatio:
    r"""The ratio of the sound pressures on the test and the reference
    microphone that their different acoustic impedances cause
    (IEC 61094-5:2016 7.4 and 7.5).

    .. math::

       R_P = \frac{V_x + V_\mathrm{e,ref}}{V_x + V_\mathrm{e,test}}

    with :math:`V_\mathrm{e}` the equivalent volume of each microphone and
    :math:`V_x` that of what it works into. Its level,
    :attr:`level_difference_db`, is the ``pressure_level_difference_db`` of a
    comparison, and its phase the ``pressure_phase_difference_deg``.

    :ivar frequencies_hz: The frequencies, in Hz.
    :ivar ratio: :math:`R_P` at each frequency, complex.
    :ivar coupling: ``"coupler"``, a closed coupler small against the
        wavelength (IEC 61094-2 Formula (3)), or ``"series"``, the air between
        the microphones in series with each, this library's reading of
        IEC 61094-5 Table D.1.
    :ivar coupling_equivalent_volume_m3: :math:`V_x` at each frequency,
        complex, in m³.
    """

    frequencies_hz: NDArray[np.float64]
    ratio: NDArray[np.complex128]
    coupling: str
    coupling_equivalent_volume_m3: NDArray[np.complex128]

    def __post_init__(self) -> None:
        """Refuse columns that disagree and publish them read-only.

        :raises ValueError: for frequencies that are not positive and
            increasing, an unknown coupling, or a column that is not one
            finite value per frequency.
        """
        require_choice(self.coupling, "coupling", ("coupler", "series"))
        frequencies = _frequency_axis(self.frequencies_hz)
        count = frequencies.size
        object.__setattr__(self, "frequencies_hz", read_only(frequencies.copy()))
        for name in ("ratio", "coupling_equivalent_volume_m3"):
            column = _complex_column(getattr(self, name), name, count)
            object.__setattr__(self, name, read_only(column.copy()))

    @property
    def level_difference_db(self) -> NDArray[np.float64]:
        r""":math:`20\lg\lvert R_P\rvert`, in dB: what the test microphone
        hears more than the reference.
        """
        return 20.0 * np.log10(np.abs(self.ratio))

    @property
    def phase_difference_deg(self) -> NDArray[np.float64]:
        r""":math:`\arg R_P`, in degrees."""
        return np.degrees(np.angle(self.ratio))

    @property
    def standard_uncertainty_db(self) -> NDArray[np.float64]:
        r"""The level difference taken as the semi-range of a rectangular
        distribution, :math:`\lvert 20\lg\lvert R_P\rvert\rvert/\sqrt{3}`, in
        dB.

        This is how Table D.1 of IEC 61094-5 carries the effect, a semi-range
        of 0,005 dB at 2 kHz giving 0,003 dB, and how 7.5 asks for it when no
        reference of similar impedance is available: "the size of the error
        caused should be estimated and added to the uncertainty budget". It
        is the ``"impedance"`` component of
        :func:`comparison_uncertainty_budget`; a calibration that corrects for
        :math:`R_P` instead takes only what is left of it. The same row of
        Table D.1 warns that "when microphones have significantly differing
        impedances (for example WS2F microphone compared against LS2P at
        frequencies above 10 kHz), the measurement uncertainty can be
        considerably larger and should be established experimentally": there
        this value is an estimate of the model's, not a substitute for that
        experiment.
        """
        return np.abs(self.level_difference_db) / _SQRT3

    def plot(
        self,
        ax: Axes | None = None,
        *,
        quantity: str = "level",
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        r"""Plot :math:`20\lg\lvert R_P\rvert` and its standard uncertainty,
        or :math:`\arg R_P`, against frequency.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param quantity: ``"level"`` (default) or ``"phase"``.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the curve of :math:`R_P`.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        :raises ValueError: for an unknown quantity.
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_impedance_pressure_ratio

        require_choice(quantity, "quantity", ("level", "phase"))
        return plot_impedance_pressure_ratio(
            self, ax=ax, quantity=quantity, language=check_language(language), **kwargs
        )


def impedance_pressure_ratio(
    frequencies_hz: ArrayLike,
    *,
    reference_equivalent_volume_m3: ArrayLike,
    test_equivalent_volume_m3: ArrayLike,
    coupling_equivalent_volume_m3: ArrayLike | None = None,
    coupling_impedance_pa_s_m3: ArrayLike | None = None,
) -> ImpedancePressureRatio:
    r"""The ratio of the sound pressures that the different acoustic
    impedances of two microphones cause (IEC 61094-5:2016 7.4 and 7.5).

    "Differences in the acoustic impedance between the test and reference
    microphones can cause the sound pressure at the test and reference
    microphones to differ" (7.4), most where a pressure and a free-field
    response microphone meet above 10 kHz (7.5). Neither clause prints a
    model; both refer the effect to the uncertainty, and 7.4 to the
    literature for a model. This function writes two circuits: the closed
    coupler that IEC 61094-2 prints as Formula (3), and a series divider that
    is this library's reading of the one sentence Table D.1 gives the
    simultaneous excitation. Each microphone enters by its equivalent volume
    :math:`V_\mathrm{e} = \kappa_\mathrm{r} p_{s,\mathrm{r}}/(\mathrm{j}\omega
    Z_\mathrm{a})` (IEC 61094-1 6.2.2, with :math:`\kappa_\mathrm{r} = 1{,}40`
    and :math:`p_{s,\mathrm{r}}` = 101,325 kPa):

    * **A closed coupler, sequential substitution.** In a coupler small
      against the wavelength, the source drives the sum of the admittances of
      the gas and of every microphone in it, IEC 61094-2:2009 Formula (3),
      :math:`1/Z = \mathrm{j}\omega\,[V/(\kappa p_s) + \sum
      V_\mathrm{e}/(\kappa_\mathrm{r} p_{s,\mathrm{r}})]`, so putting the test
      microphone in the place of the reference changes the pressure by
      :math:`R_P = (V_x + V_\mathrm{e,ref})/(V_x + V_\mathrm{e,test})`, with
      :math:`V_x` the rest of the load: the gas volume referred to the
      reference conditions, :math:`V \kappa_\mathrm{r}
      p_{s,\mathrm{r}}/(\kappa p_s)`, and the equivalent volumes of
      the source and of any monitor. A monitor that "accurately sense[s]
      changes in the sound pressure at the test/reference microphone
      position" (5.1.3) corrects for this ratio; without one it is the
      correction. Pass ``coupling_equivalent_volume_m3``.
    * **The air between the microphones in series, simultaneous
      excitation.** "The acoustical impedance of the microphone acts in
      series with that of the air in the space between the two microphones.
      Microphones with different acoustic impedance therefore see slightly
      different pressures when simultaneously exposed to the same pressure
      field" (Table D.1, "Microphone impedance"). The row prints no circuit;
      this library reads it as a divider, each diaphragm taking the pressure
      :math:`p_0 Z_\mathrm{a}/(Z_\mathrm{a} + Z_x)` of the common field
      :math:`p_0` behind the same series impedance :math:`Z_x`, the reading
      in which the two microphones see the different pressures the row
      concludes they do. Written with volumes this is
      the same ratio, :math:`V_x` being the equivalent volume of
      :math:`Z_x`, :math:`\kappa_\mathrm{r} p_{s,\mathrm{r}}/(\mathrm{j}\omega
      Z_x)`. Pass ``coupling_impedance_pa_s_m3``; the parts print no value
      for it, and Table D.1 asks for the effect to be "established
      experimentally" when the impedances differ significantly.

    :param frequencies_hz: The frequencies, in Hz, increasing.
    :param reference_equivalent_volume_m3: :math:`V_\mathrm{e,ref}`, complex,
        in m³, one value or one per frequency, such as
        :meth:`ReciprocityMicrophone.complex_equivalent_volume_m3` gives it
        from the lumped parameters of IEC 61094-2 E.4. Its ratio to
        :math:`V_\mathrm{eq}` holds no :math:`\kappa_\mathrm{r}`, so the
        volume keeps the definition :math:`V_\mathrm{eq}` was given in, the
        :math:`\kappa_\mathrm{r} = 1{,}40` of IEC 61094-1 for the values of
        its Table 3; a series impedance is turned into :math:`V_x` with that
        same 1,40.
    :param test_equivalent_volume_m3: :math:`V_\mathrm{e,test}`, in m³.
    :param coupling_equivalent_volume_m3: :math:`V_x` of a closed coupler, in
        m³ at the reference conditions (Default: None).
    :param coupling_impedance_pa_s_m3: :math:`Z_x`, the acoustic impedance in
        series with each microphone, in Pa·s/m³ (Default: None; give exactly
        one of the two).
    :return: The :class:`ImpedancePressureRatio`.
    :raises ValueError: for frequencies that are not positive and increasing,
        not exactly one of the two couplings, a series impedance of zero, a
        column that is not one finite value per frequency, or a coupling and
        a test microphone whose equivalent volumes cancel.
    """
    frequencies = _frequency_axis(frequencies_hz)
    count = frequencies.size
    if (coupling_equivalent_volume_m3 is None) == (coupling_impedance_pa_s_m3 is None):
        msg = (
            "Give exactly one of 'coupling_equivalent_volume_m3' (a closed coupler) "
            "and 'coupling_impedance_pa_s_m3' (the air in series with each "
            "microphone)."
        )
        raise ValueError(msg)
    reference = _complex_column(
        reference_equivalent_volume_m3, "reference_equivalent_volume_m3", count
    )
    test = _complex_column(
        test_equivalent_volume_m3, "test_equivalent_volume_m3", count
    )
    if coupling_impedance_pa_s_m3 is None:
        coupling = "coupler"
        volume = _complex_column(
            coupling_equivalent_volume_m3,  # type: ignore[arg-type]
            "coupling_equivalent_volume_m3",
            count,
        )
    else:
        coupling = "series"
        impedance = _complex_column(
            coupling_impedance_pa_s_m3, "coupling_impedance_pa_s_m3", count
        )
        if not np.all(np.abs(impedance) > 0.0):
            msg = "'coupling_impedance_pa_s_m3' must not be zero."
            raise ValueError(msg)
        omega = 2.0 * np.pi * frequencies
        volume = (
            _KAPPA_REFERENCE
            * 1000.0
            * _REFERENCE_STATIC_PRESSURE_KPA
            / (1j * omega * impedance)
        )
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = (volume + reference) / (volume + test)
    if not np.all(np.isfinite(ratio)):
        msg = (
            "The coupling and the test microphone have equivalent volumes that "
            "cancel at some frequency: a resonance without loss. Give the "
            "microphone a loss factor."
        )
        raise ValueError(msg)
    return ImpedancePressureRatio(
        frequencies_hz=frequencies,
        ratio=ratio,
        coupling=coupling,
        coupling_equivalent_volume_m3=volume,
    )


# ---------------------------------------------------------------------------
# Time-selective processing (IEC 61094-8 Annex B)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RectangularPulse:
    r"""The rectangular pulse of the direct impulse method (IEC 61094-8:2012
    B.6.1, Formula (B.10)).

    A pulse of amplitude :math:`a` lasting :math:`T` has the spectrum

    .. math::

       X(f) = \frac{2ab\sin(2\pi f b)}{2\pi f b}, \qquad b = T/2

    Formula (B.10), whose first zero is at :math:`f = 1/(2b) = 1/T`. The
    standard calls :math:`b` the duration; the formula and its first zero
    are those of a pulse lasting :math:`2b` (``docs/ERRATA.md``), and the
    library follows them.

    :ivar duration_s: :math:`T = 2b`, how long the pulse lasts, in s.
    :ivar amplitude_v: :math:`a`, the voltage applied to the source, in V.
    """

    duration_s: float
    amplitude_v: float = 1.0

    def __post_init__(self) -> None:
        """Refuse a duration or an amplitude that is not positive.

        :raises ValueError: for either not finite and positive.
        """
        for name in ("duration_s", "amplitude_v"):
            object.__setattr__(self, name, require_positive(getattr(self, name), name))

    @property
    def half_duration_s(self) -> float:
        """:math:`b` of Formula (B.10), half the duration, in s."""
        return self.duration_s / 2.0

    @property
    def first_zero_hz(self) -> float:
        """:math:`1/(2b)`, the first zero of the spectrum, in Hz (B.6.1)."""
        return 1.0 / self.duration_s

    @property
    def area_v_s(self) -> float:
        r""":math:`X(0) = 2ab`, the area of the pulse, in V·s."""
        return self.amplitude_v * self.duration_s

    def spectrum_at(self, frequencies_hz: ArrayLike) -> NDArray[np.float64]:
        r""":math:`X(f)` of Formula (B.10), in V·s, the transform of the pulse
        centred on the time origin, where it is real.

        :param frequencies_hz: Any frequencies, in Hz.
        :return: :math:`X(f)` at each.
        :raises ValueError: for a frequency that is not finite.
        """
        frequencies = require_finite_array(frequencies_hz, "frequencies_hz")
        # numpy's sinc is sin(pi x)/(pi x): with x = 2 f b it is (B.10) over 2ab.
        return self.area_v_s * np.sinc(frequencies * self.duration_s)

    def level_db_at(self, frequencies_hz: ArrayLike) -> NDArray[np.float64]:
        r""":math:`20\lg\lvert X(f)/X(0)\rvert`, how far the spectrum has
        fallen from its value at 0 Hz, in dB (minus infinity at a zero).

        :param frequencies_hz: Any frequencies, in Hz.
        :return: The level at each, in dB.
        """
        relative = np.abs(self.spectrum_at(frequencies_hz)) / self.area_v_s
        with np.errstate(divide="ignore"):
            return 20.0 * np.log10(relative)

    def plot(
        self,
        ax: Axes | None = None,
        *,
        upper_frequency_hz: float | None = None,
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        r"""Plot :math:`\lvert X(f)/X(0)\rvert` in dB up to past its second
        zero, with the first zero and, when given, the upper limit of the
        frequencies of interest.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param upper_frequency_hz: The upper limit of the frequencies of
            interest, in Hz, marked with the level the pulse has fallen by
            there (Default: None).
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the spectrum.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_rectangular_pulse

        upper = (
            None
            if upper_frequency_hz is None
            else require_positive(upper_frequency_hz, "upper_frequency_hz")
        )
        return plot_rectangular_pulse(
            self,
            ax=ax,
            upper_frequency_hz=upper,
            language=check_language(language),
            **kwargs,
        )


def rectangular_pulse(
    duration_s: float, *, amplitude_v: float = 1.0
) -> RectangularPulse:
    r"""The rectangular pulse of the direct impulse method (IEC 61094-8:2012
    B.6.1).

    "A signal that approximates an idealized unit impulse (delta function)
    can be directly applied to the sound source", and "in order to have a
    flat spectrum in the frequency range of interest [...] the duration of
    the input signal needs to be sufficiently short": its spectrum is Formula
    (B.10). Give the whole duration :math:`T`; Formula (B.10) writes it as
    :math:`2b` (``docs/ERRATA.md``). :func:`rectangular_pulse_duration_s`
    gives the duration for an upper limit of frequency.

    :param duration_s: :math:`T = 2b`, in s.
    :param amplitude_v: :math:`a`, in V (Default: 1).
    :return: The :class:`RectangularPulse`.
    :raises ValueError: for a duration or an amplitude that is not positive.
    """
    return RectangularPulse(duration_s=duration_s, amplitude_v=amplitude_v)


def rectangular_pulse_duration_s(
    upper_frequency_hz: float, *, zero_ratio: float = _PULSE_ZERO_RATIO
) -> float:
    r"""The duration of a rectangular pulse whose first spectral zero lies a
    given factor above the frequencies of interest (IEC 61094-8:2012 B.6.1).

    The first zero, :math:`1/(2b) = 1/T`, "must be approximately an order of
    magnitude higher than the upper limit of the frequency range of interest,
    leading to a requirement for the duration, :math:`b` of just a few
    microseconds":

    .. math::

       T = 2b = \frac{1}{r\, f_\mathrm{max}}

    with :math:`r` the factor, 10 by default. For 20 kHz that is 5 µs, a
    half-duration :math:`b` of 2,5 µs, at which the spectrum has fallen by
    0,14 dB.

    :param upper_frequency_hz: :math:`f_\mathrm{max}`, in Hz.
    :param zero_ratio: :math:`r`, the first zero over :math:`f_\mathrm{max}`
        (Default: 10, an order of magnitude).
    :return: :math:`T`, in s.
    :raises ValueError: for a frequency that is not positive or a ratio that
        is not above 1.
    """
    upper = require_positive(upper_frequency_hz, "upper_frequency_hz")
    ratio = require_positive(zero_ratio, "zero_ratio")
    if ratio <= 1.0:
        msg = (
            "'zero_ratio' must be above 1: the first zero of the pulse has to lie "
            "above the frequencies of interest."
        )
        raise ValueError(msg)
    return 1.0 / (ratio * upper)


def _sample_index(time_s: float, sample_rate_hz: float, *, up: bool) -> int:
    """The first sample at or after a time (``up``), or the last at or before
    it, with a time within the rounding of a sample read as that sample.
    """
    position = time_s * sample_rate_hz
    nearest = round(position)
    if abs(position - nearest) <= _SAMPLE_TOLERANCE * max(1.0, abs(position)):
        return int(nearest)
    return int(math.ceil(position) if up else math.floor(position))


def _window_shape(
    shape: str, samples: int, taper_fraction: float
) -> NDArray[np.float64]:
    """The window over ``samples`` samples."""
    from scipy.signal import windows

    if shape == "tukey":
        return np.asarray(
            windows.tukey(samples, alpha=taper_fraction), dtype=np.float64
        )
    if shape == "hann":
        return np.asarray(windows.hann(samples), dtype=np.float64)
    if shape == "hamming":
        return np.asarray(windows.hamming(samples), dtype=np.float64)
    return np.ones(samples)


def _fourier_transform(
    samples: NDArray[np.float64],
    first_index: int,
    sample_rate_hz: float,
    frequencies: NDArray[np.float64],
) -> NDArray[np.complex128]:
    r"""Formula (B.2) for sampled data at any frequencies:
    :math:`H(f) = \sum_n h_n \mathrm{e}^{-\mathrm{j}2\pi f t_n}/f_\mathrm{s}`,
    with :math:`t_n = n/f_\mathrm{s}` counted from the start of the record.
    """
    times = (first_index + np.arange(samples.size)) / sample_rate_hz
    result = np.empty(frequencies.size, dtype=np.complex128)
    block = max(1, _TRANSFORM_BLOCK // max(1, samples.size))
    for start in range(0, frequencies.size, block):
        chunk = frequencies[start : start + block]
        kernel = np.exp(-2j * np.pi * np.outer(chunk, times))
        result[start : start + block] = kernel @ samples
    return result / sample_rate_hz


@dataclass(frozen=True)
class TimeSelectiveResponse:
    r"""The frequency response of the direct sound alone, an impulse response
    weighted with a time window and transformed (IEC 61094-8:2012 B.1.3 and
    B.2).

    The window keeps the samples from :attr:`window_start_s` to
    :attr:`window_end_s`, counted from the start of the record, with tapered
    edges, and :meth:`response_at` transforms them by Formula (B.2),
    :math:`H(f) = \int h(t)\,\mathrm{e}^{-\mathrm{j}2\pi f t}\,\mathrm{d}t`,
    at any frequency. With an :attr:`excitation`, the transform is divided by
    the pulse's, as a pulse that begins at the start of the record.

    :ivar impulse_response: The impulse response, sampled.
    :ivar sample_rate_hz: Its sample rate, in Hz.
    :ivar window_start_s: Where the window begins, in s.
    :ivar window_end_s: Where it ends, in s.
    :ivar window_shape: ``"tukey"``, ``"hann"``, ``"hamming"`` or
        ``"rectangular"``.
    :ivar taper_fraction: The fraction of a Tukey window that is taper, half
        at each edge.
    :ivar excitation: The :class:`RectangularPulse` the response was taken
        with, divided out, or ``None``.
    """

    impulse_response: NDArray[np.float64]
    sample_rate_hz: float
    window_start_s: float
    window_end_s: float
    window_shape: str = "tukey"
    taper_fraction: float = _DEFAULT_TAPER_FRACTION
    excitation: RectangularPulse | None = None

    def __post_init__(self) -> None:
        """Refuse a window outside the record or with no room for a shape,
        and publish the response read-only.

        :raises ValueError: for a response that is not one finite value per
            sample, a sample rate that is not positive, an unknown window
            shape, a taper outside 0 to 1, or a window that does not begin
            before it ends, begins before the record or ends after it, or
            holds fewer than two samples.
        """
        response = require_finite_array(self.impulse_response, "impulse_response")
        if response.size < _MIN_WINDOW_SAMPLES:
            msg = "'impulse_response' must be one value per sample, at least two."
            raise ValueError(msg)
        object.__setattr__(self, "impulse_response", read_only(response.copy()))
        rate = require_positive(self.sample_rate_hz, "sample_rate_hz")
        object.__setattr__(self, "sample_rate_hz", rate)
        require_choice(self.window_shape, "window_shape", _WINDOW_SHAPES)
        taper = require_positive(self.taper_fraction, "taper_fraction")
        if taper > 1.0:
            msg = "'taper_fraction' must be within 0 (excluded) and 1."
            raise ValueError(msg)
        start = require_non_negative(self.window_start_s, "window_start_s")
        end = require_positive(self.window_end_s, "window_end_s")
        last = _sample_index(end, rate, up=False)
        first = _sample_index(start, rate, up=True)
        if (
            end <= start
            or last >= response.size
            or last - first + 1 < _MIN_WINDOW_SAMPLES
        ):
            msg = (
                f"The window from {start:g} s to {end:g} s must begin before it ends, "
                f"hold at least {_MIN_WINDOW_SAMPLES} samples and end within the "
                f"record of {(response.size - 1) / rate:g} s."
            )
            raise ValueError(msg)

    @property
    def _bounds(self) -> tuple[int, int]:
        """The first and the last sample of the window."""
        first = _sample_index(self.window_start_s, self.sample_rate_hz, up=True)
        last = _sample_index(self.window_end_s, self.sample_rate_hz, up=False)
        return first, last

    @property
    def time_s(self) -> NDArray[np.float64]:
        """The time of each sample from the start of the record, in s."""
        return np.arange(self.impulse_response.size) / self.sample_rate_hz

    @property
    def window(self) -> NDArray[np.float64]:
        """The window at each sample of the record, 0 outside it."""
        first, last = self._bounds
        weights = np.zeros(self.impulse_response.size)
        weights[first : last + 1] = _window_shape(
            self.window_shape, last - first + 1, self.taper_fraction
        )
        return weights

    @property
    def windowed_impulse_response(self) -> NDArray[np.float64]:
        """The impulse response times the window."""
        return self.impulse_response * self.window

    @property
    def window_length_s(self) -> float:
        """How long the window lasts, in s."""
        return self.window_end_s - self.window_start_s

    @property
    def frequency_resolution_hz(self) -> float:
        """The inverse of the window length, in Hz: the spacing of the
        frequencies the window can tell apart, as B.2.2 relates the length of
        an impulse response to its frequency step.
        """
        return 1.0 / self.window_length_s

    def response_at(self, frequencies_hz: ArrayLike) -> NDArray[np.complex128]:
        r""":math:`H(f)`, Formula (B.2) applied to the windowed response, at
        each frequency, complex, in the unit of the response times seconds
        (divided by the pulse's spectrum, in V·s, when there is one).

        :param frequencies_hz: The frequencies, in Hz, increasing.
        :return: :math:`H(f)` at each.
        :raises ValueError: for frequencies that are not positive and
            increasing, or, with an excitation, a frequency at or above the
            first zero of its spectrum.
        """
        first, last = self._bounds
        return self._transform(
            self.windowed_impulse_response[first : last + 1],
            first,
            _frequency_axis(frequencies_hz),
        )

    def record_response_at(self, frequencies_hz: ArrayLike) -> NDArray[np.complex128]:
        r""":math:`H(f)` of the whole record with no window, the reflections
        included: what the window takes away, for comparison.

        :param frequencies_hz: The frequencies, in Hz, increasing.
        :return: :math:`H(f)` at each.
        :raises ValueError: for frequencies that are not positive and
            increasing.
        """
        return self._transform(
            self.impulse_response, 0, _frequency_axis(frequencies_hz)
        )

    def _transform(
        self,
        samples: NDArray[np.float64],
        first: int,
        frequencies: NDArray[np.float64],
    ) -> NDArray[np.complex128]:
        """Formula (B.2) of the samples from ``first`` on, divided by the
        pulse's spectrum when there is one.
        """
        response = _fourier_transform(samples, first, self.sample_rate_hz, frequencies)
        if self.excitation is not None:
            pulse = self.excitation
            if frequencies[-1] >= pulse.first_zero_hz:
                msg = (
                    f"{frequencies[-1]:g} Hz is at or above the first zero of the "
                    f"pulse's spectrum, {pulse.first_zero_hz:g} Hz, where there is "
                    "nothing to divide by (IEC 61094-8 B.6.1)."
                )
                raise ValueError(msg)
            # A pulse that begins at the start of the record is the centred
            # pulse of (B.10) delayed by half its duration.
            delay = np.exp(-1j * np.pi * frequencies * pulse.duration_s)
            response = response / (pulse.spectrum_at(frequencies) * delay)
        return response

    def level_db_at(self, frequencies_hz: ArrayLike) -> NDArray[np.float64]:
        r""":math:`20\lg\lvert H(f)\rvert`, in dB re 1 of the response's unit
        times a second.

        :param frequencies_hz: The frequencies, in Hz, increasing.
        :return: The level at each, in dB.
        """
        return 20.0 * np.log10(np.abs(self.response_at(frequencies_hz)))

    def phase_deg_at(self, frequencies_hz: ArrayLike) -> NDArray[np.float64]:
        r""":math:`\arg H(f)`, in degrees, with the time origin at the start of
        the record.

        :param frequencies_hz: The frequencies, in Hz, increasing.
        :return: The phase at each, in degrees.
        """
        return np.degrees(np.angle(self.response_at(frequencies_hz)))

    def free_field_region(
        self,
        source_distance_m: float,
        arrival_time_s: float,
        *,
        temperature_c: float = _REFERENCE_TEMPERATURE_C,
        static_pressure_kpa: float = _REFERENCE_STATIC_PRESSURE_KPA,
        relative_humidity_percent: float = _REFERENCE_RELATIVE_HUMIDITY_PERCENT,
    ) -> FreeFieldRegion:
        r"""The effective free-field region of this window (B.1, Formula
        (B.1)), with :math:`\tau` "the time from the arrival of the sound at
        the microphone under test, to the end of the time window".

        :param source_distance_m: :math:`d`, in m.
        :param arrival_time_s: When the direct sound reaches the microphone,
            in s from the start of the record.
        :param temperature_c: The air temperature, in °C (Default: 23,0).
        :param static_pressure_kpa: The static pressure, in kPa (Default:
            101,325).
        :param relative_humidity_percent: The relative humidity, in %
            (Default: 50).
        :return: The :class:`FreeFieldRegion`.
        :raises ValueError: for an arrival at or after the end of the window,
            or what :func:`free_field_region` refuses.
        """
        arrival = require_non_negative(arrival_time_s, "arrival_time_s")
        if arrival >= self.window_end_s:
            msg = (
                f"The direct sound arrives at {arrival:g} s, not before the window "
                f"ends at {self.window_end_s:g} s."
            )
            raise ValueError(msg)
        return free_field_region(
            source_distance_m,
            self.window_end_s - arrival,
            temperature_c=temperature_c,
            static_pressure_kpa=static_pressure_kpa,
            relative_humidity_percent=relative_humidity_percent,
        )

    def plot(
        self,
        ax: Axes | None = None,
        *,
        quantity: str = "impulse",
        frequencies_hz: ArrayLike | None = None,
        language: str = "en",
        **kwargs: Any,
    ) -> Axes:
        r"""Plot the impulse response with the window over it, or the level of
        :math:`H(f)` with and without the window.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param quantity: ``"impulse"`` (default) or ``"response"``.
        :param frequencies_hz: The frequencies of the response, in Hz
            (Default: None, 200 from the frequency resolution to a quarter of
            the sample rate, or, with an :attr:`excitation`, to a tenth of
            the first zero of its spectrum if that is lower, B.6.1).
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the windowed curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        :raises ValueError: for an unknown quantity.
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_time_selective_response

        require_choice(quantity, "quantity", ("impulse", "response"))
        frequencies = (
            None if frequencies_hz is None else _frequency_axis(frequencies_hz)
        )
        return plot_time_selective_response(
            self,
            ax=ax,
            quantity=quantity,
            frequencies_hz=frequencies,
            language=check_language(language),
            **kwargs,
        )


def time_selective_response(
    impulse_response: ArrayLike,
    sample_rate_hz: float,
    *,
    window_start_s: float,
    window_end_s: float,
    window_shape: str = "tukey",
    taper_fraction: float = _DEFAULT_TAPER_FRACTION,
    excitation: RectangularPulse | None = None,
) -> TimeSelectiveResponse:
    r"""The frequency response of the direct sound alone, through a time
    window (IEC 61094-8:2012 Annex B).

    "An impulse response (IR) can be obtained from the measured output of the
    reference microphone or device under test, which separates the direct
    and reflected energy components [...] enabling the two to be separated by
    applying a time window" (B.1.1); "a time-domain to frequency-domain
    transformation can then be used to obtain the desired frequency
    response". The window is a weighting function that is zero outside the
    chosen interval (B.1.3); a rectangular one "is not recommended because it
    usually leads to spectral leakage", so the default is a Tukey window, flat
    in the middle with cosine-tapered edges. Its placement and duration are
    the user's, by the three criteria of B.1.3: the distances from the source
    to the microphone and to the reflectors (see :func:`reflection_free_window_s`),
    the supporting structure beyond the rod, and a look at the impulse
    response.

    The impulse response may come from any method of Annex B: a stepped sine
    by :func:`stepped_sine_impulse_response`, a sweep or a maximum length
    sequence by :func:`phonometry.room.impulse_response` and
    :func:`phonometry.room.mls_impulse_response`, or a direct impulse (B.6), in
    which case ``excitation`` divides the spectrum of the pulse out. The
    reference and the test microphone are windowed alike, and the levels of
    their responses at the calibration frequencies go to
    :func:`sequential_comparison` as the two output levels.

    :param impulse_response: The impulse response, one value per sample,
        from the start of the record.
    :param sample_rate_hz: Its sample rate, in Hz.
    :param window_start_s: Where the window begins, in s from the start of the
        record: before the direct sound arrives.
    :param window_end_s: Where it ends, in s: before the first reflection.
    :param window_shape: ``"tukey"`` (default), ``"hann"``, ``"hamming"`` or
        ``"rectangular"``.
    :param taper_fraction: The fraction of a Tukey window that is taper, half
        at each edge (Default: 0,25).
    :param excitation: The :class:`RectangularPulse` of a direct impulse
        measurement, divided out of the response (Default: None).
    :return: The :class:`TimeSelectiveResponse`.
    :raises ValueError: for what :class:`TimeSelectiveResponse` refuses.
    """
    return TimeSelectiveResponse(
        impulse_response=np.asarray(impulse_response, dtype=np.float64),
        sample_rate_hz=sample_rate_hz,
        window_start_s=window_start_s,
        window_end_s=window_end_s,
        window_shape=window_shape,
        taper_fraction=taper_fraction,
        excitation=excitation,
    )


@dataclass(frozen=True)
class SteppedSineImpulseResponse:
    r"""The impulse response of a stepped-sine measurement (IEC 61094-8:2012
    B.2, Formula (B.3)).

    :ivar frequency_step_hz: :math:`\Delta f`, the step of the measured
        frequencies, in Hz.
    :ivar impulse_response: :math:`h(t)` at :math:`t = n/f_\mathrm{s}`, in the
        unit of the response per second.
    """

    frequency_step_hz: float
    impulse_response: NDArray[np.float64]

    def __post_init__(self) -> None:
        """Refuse a step that is not positive and publish the response
        read-only.

        :raises ValueError: for a step that is not positive or a response that
            is not one finite value per sample.
        """
        object.__setattr__(
            self,
            "frequency_step_hz",
            require_positive(self.frequency_step_hz, "frequency_step_hz"),
        )
        response = require_finite_array(self.impulse_response, "impulse_response")
        if response.size < _MIN_WINDOW_SAMPLES:
            msg = "'impulse_response' must be one value per sample, at least two."
            raise ValueError(msg)
        object.__setattr__(self, "impulse_response", read_only(response.copy()))

    @property
    def sample_rate_hz(self) -> float:
        r""":math:`f_\mathrm{s} = N\,\Delta f`, in Hz."""
        return self.impulse_response.size * self.frequency_step_hz

    @property
    def duration_s(self) -> float:
        r""":math:`1/\Delta f`, how long the impulse response lasts, in s:
        "the length of the impulse response will be the inverse of the size
        of the frequency step" (B.2.2).
        """
        return 1.0 / self.frequency_step_hz

    @property
    def time_s(self) -> NDArray[np.float64]:
        """The time of each sample, in s."""
        return np.arange(self.impulse_response.size) / self.sample_rate_hz

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the impulse response against time.

        :param ax: Existing axes to draw on, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the curve.
        :return: The axes. Requires matplotlib
            (``pip install phonometry[plot]``).
        """
        from .._i18n import check_language
        from .._plot.metrology import plot_stepped_sine_impulse_response

        return plot_stepped_sine_impulse_response(
            self, ax=ax, language=check_language(language), **kwargs
        )


def stepped_sine_impulse_response(
    frequencies_hz: ArrayLike, response: ArrayLike
) -> SteppedSineImpulseResponse:
    r"""The impulse response of a frequency response measured at linearly
    spaced frequencies (IEC 61094-8:2012 B.2, Formula (B.3)).

    "When the full range frequency response can be measured, an inverse
    Fourier transform, Equation B.3, can be applied to transform this response
    to the time domain, where time selective processes can be applied" (B.2.1),

    .. math::

       h(t) = \int_{-\infty}^{\infty} H(f)\,\mathrm{e}^{\mathrm{j}2\pi f t}\,
       \mathrm{d}f

    computed by the inverse FFT, which needs "the frequency response to be
    measured at discrete frequencies and linearly spaced frequency
    increments" and a range extended to 0 Hz: "the low frequency response can
    be estimated from a knowledge of the pressure sensitivities of the
    microphones", and the measurement should reach "about three times the
    resonance frequency of the microphones". The axis therefore starts at
    0 Hz, holds :math:`K + 1` frequencies :math:`k\,\Delta f`, and the
    response is taken as that of a real :math:`h(t)`: the negative frequencies
    are the complex conjugates of the positive ones, and the imaginary part
    of the value at 0 Hz, which a real response does not have, is dropped.
    The result has :math:`N = 2K + 1` samples at :math:`f_\mathrm{s} = N\,\Delta f`
    and lasts :math:`1/\Delta f`, which has to be long enough "to include"
    the reflections that matter (B.2.2): 120 Hz in a small anechoic room
    whose primary reflections all arrive before 8 ms, about 30 Hz in a large
    one.

    :param frequencies_hz: :math:`k\,\Delta f`, from 0 Hz, in Hz, equally
        spaced.
    :param response: :math:`H(k\,\Delta f)`, complex, one value per frequency.
    :return: The :class:`SteppedSineImpulseResponse`; pass its
        ``impulse_response`` and ``sample_rate_hz`` to
        :func:`time_selective_response`.
    :raises ValueError: for fewer than two frequencies, an axis that does not
        start at 0 Hz or is not equally spaced, or a response that is not one
        finite value per frequency.
    """
    frequencies = require_finite_array(frequencies_hz, "frequencies_hz")
    if frequencies.size < _MIN_WINDOW_SAMPLES:
        msg = "'frequencies_hz' must hold at least two frequencies, from 0 Hz."
        raise ValueError(msg)
    steps = np.diff(frequencies)
    step = float(frequencies[1] - frequencies[0])
    if step <= 0.0 or not np.allclose(steps, step, rtol=_STEP_REL_TOL, atol=0.0):
        msg = "'frequencies_hz' must be equally spaced and increasing (B.2.1)."
        raise ValueError(msg)
    if abs(float(frequencies[0])) > _STEP_REL_TOL * step:
        msg = (
            f"'frequencies_hz' must start at 0 Hz, not {frequencies[0]:g} Hz: extend "
            "the measurement to 0 Hz from the pressure sensitivities (B.2.1)."
        )
        raise ValueError(msg)
    # A copy: the caller's array is not the place to drop the imaginary part.
    values = _complex_column(response, "response", frequencies.size).copy()
    values[0] = values[0].real
    samples = 2 * (frequencies.size - 1) + 1
    rate = samples * step
    impulse = rate * np.fft.irfft(values, n=samples)
    return SteppedSineImpulseResponse(frequency_step_hz=step, impulse_response=impulse)
