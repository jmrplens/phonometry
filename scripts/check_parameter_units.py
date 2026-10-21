#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a public parameter that names a quantity without saying which unit
it is in.

A number the caller types is where a unit is lost, and the loss is silent: a
static pressure of 101 325 handed to a function that wants kilopascals is a
thousand times the atmosphere, and every result downstream is still a float.
No guard can catch that by magnitude, because both readings are legitimate
values of the same quantity elsewhere in this library, so the unit has to be
in the name, where the caller writes it and where a reader of the call site
can see it.

The rule is one line: a public parameter whose name says one of the quantities
this tree has written in two units (:data:`QUANTITIES` and
:data:`WORD_QUANTITIES`) ends either in a unit (:data:`UNITS`) or in a suffix
that says the quantity carries no unit of its own (:data:`DIMENSIONLESS`, which
covers the decibel levels, the ratios and the indicators). Anything else keeps
its unit in the docstring, which is not where the mistake is made. A parameter
typed ``bool`` is outside the rule whatever its name says: a verdict such as
``humidity_ok`` holds no number of the quantity it names.

The surface is the one a caller reaches: every name in the ``__all__`` of every
public module, the public methods and properties of the classes among them, and
the fields a dataclass turns into keyword arguments. That is why this walks the
imported package rather than the source tree: :class:`ReportMetadata` is
published from the root and defined in a private module, and a scan by file
path would never see it.

The second half of the rule is where the name has to appear: a parameter under
the rule that carries a default is keyword-only, so the number cannot be
written as a bare positional argument with the name nowhere on the line.

:data:`EXEMPT` is the escape hatch for the first half and :data:`POSITIONAL`
for the second, both keyed by module, qualified name and parameter, and each
entry carries the reason it is one.

Two more rules ride on the same walk. A unit has one spelling: a public name
of any kind (a function, a method, a property, a field, a parameter or a
constant) that ends in a spelling :data:`REJECTED_SPELLINGS` lists is
reported with the one the tree writes instead, so ``_seconds`` and ``_s``
never name the same unit on two neighbouring results. And a published
constant says its unit. An UPPER_CASE name in the ``__all__`` of a public
module that holds a single number is held to the rule whatever its name
says, because a lone number has nowhere else to carry its unit: it ends in a
unit, in a dimensionless suffix (decibels included, as for a parameter) or
in one of :data:`CONSTANT_DIMENSIONLESS`, or it is a count, a label or a pure
number listed in :data:`CONSTANT_EXEMPT`. A table, which holds several
figures and often several units, is held to it when its name says a quantity
(the parameter quantities and :data:`CONSTANT_QUANTITIES`), and ends in the
unit of what the name says. :data:`SPELLING_EXEMPT` and
:data:`CONSTANT_EXEMPT` are the escape hatches of the two rules, keyed by
location, each with its reason.
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib
import inspect
import pathlib
import pkgutil
import re
import sys
from collections.abc import Mapping
from typing import TYPE_CHECKING, NamedTuple

import numpy as np

import phonometry

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from types import ModuleType

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: The quantities whose unit a caller can get wrong by a factor of a thousand
#: (kPa against Pa), by 273 (degrees Celsius against kelvin) or by 57 (degrees
#: against radians). A quantity earns its place here by having had two units
#: competing for one name in this tree, which is what makes the mistake
#: silent; the ones that only ever had one unit are not listed, because a
#: suffix there would restate the convention rather than resolve anything.
#:
#: ``pressure``, ``temperature`` and ``humid`` are matched anywhere in a name.
#: The geometric ones are matched as whole words inside it, so ``critical_angle``
#: and ``duct_diameter`` are held to the rule and ``triangles`` is not.
QUANTITIES = ("pressure", "temperature", "humid")

#: Matched as a word of the name, split on underscores, or as a run of
#: words: the molar mass of a gas is written per mole by the fluids catalogue
#: and per kilomole by the clauses of IEC 60534-8-3 and ISO 11820, a factor of
#: a thousand under one name.
WORD_QUANTITIES = frozenset(
    {
        "diameter",
        "angle",
        "angles",
        "period",
        "periods",
        "gradient",
        "molar_mass",
        "molecular_mass",
    }
)

#: The unit suffixes the tree uses. Every one of them is already in the
#: published API. ``_ft`` is here because a pressure altitude is a length: the
#: quantity a name says is not always the quantity it holds, and the unit still
#: has to be on it. ``_um`` is here because a micro-geometry is written in
#: micrometres by every book that prints one, and an empirical constant fitted
#: in those units is wrong by twelve orders of magnitude in metres. The gas
#: constants and the molar masses carry their whole unit, because the
#: specific constant of air, the molar constant per kilomole and the molar
#: constant per mole are three figures 29 and 1000 apart under one word.
#: The compound units read as the display of a record reads them: a unit
#: after the first is a factor (``_pa_s_m`` is Pa s/m, ``_pa2_s`` is
#: Pa² s) unless ``per`` puts it under the line, and the
#: last one is the denominator of a speed, a density or a stiffness
#: (``_m_s2``, ``_kg_m3``, ``_n_m``).
UNITS = (
    "_kpa",
    "_pa",
    "_inhg",
    "_percent",
    "_c",
    "_k",
    "_ft",
    "_mm",
    "_um",
    "_m",
    "_rad",
    "_deg",
    "_sr",
    "_s",
    "_per_s",
    "_np_per_rad",
    "_min",
    "_hours",
    "_hz",
    "_khz",
    "_kmh",
    "_kt",
    "_m_s",
    "_m_s2",
    "_mm_s",
    "_kg",
    "_m2",
    "_m3",
    "_j_kg_k",
    "_j_kmol_k",
    "_j_mol_k",
    "_kg_mol",
    "_kg_kmol",
    "_v",
    "_per_m",
    "_per_hz",
    "_n_m",
    "_pa_s_m",
    "_pa2_s",
)

#: Suffixes that say the quantity has no unit of its own: a level is in
#: decibels and names its reference elsewhere, a ratio and an index are pure
#: numbers, a correction is the decibels one of them adds, and an indicator is
#: the difference of two levels that the ISO 9614 family names in decibels.
DIMENSIONLESS = (
    "_level",
    "_levels",
    "_index",
    "_indices",
    "_indicator",
    "_ratio",
    "_recovery",
    "_uncertainty",
    "_coefficient",
    "_correction",
    "_db",
    "_db_per_m",
    "_db_per_decade",
)

#: The quantities a published table is held to on top of the parameter
#: ones. A constant is a number nobody types, so the unit a caller loses is
#: the one they assume when they read it: a reference speed of 70 is km/h in
#: CNOSSOS-EU and ISO 11819-1 while other speeds in the tree are in m/s or kt,
#: a band set of 63 to 8000 is hertz and a reference velocity of 5e-8 is m/s
#: only for the reader who has the docstring open. Matched like
#: :data:`WORD_QUANTITIES`, as words or runs of words; ``low_frequency`` and
#: ``high_frequency`` are read as the adjective they are and not as a
#: frequency. A single number needs no word to be under the rule
#: (:func:`holds_a_single_number`).
CONSTANT_QUANTITIES = frozenset(
    {
        "speed",
        "speeds",
        "velocity",
        "acceleration",
        "frequency",
        "frequencies",
        "band",
        "bands",
        "height",
        "heights",
        "length",
        "lengths",
        "radius",
        "mass",
        "area",
        "areas",
        "volume",
        "gas_constant",
    }
)

#: Endings that say a published number is a pure one, on top of
#: :data:`DIMENSIONLESS`: a factor multiplies and a fraction divides another
#: figure of the same unit, so neither carries a unit of its own. They apply
#: to constants only, where a coverage factor, a clearance factor and a mole
#: fraction are the common case.
CONSTANT_DIMENSIONLESS = ("_factor", "_fraction")

#: A unit has one spelling, and these are the ones the tree retired, each
#: with the spelling it writes instead. ``_h`` is the hour of a duration; an
#: hour that ends a rate, as in ``_mm_h``, is the denominator of a compound
#: unit and stays (:data:`PER_HOUR_UNITS`).
REJECTED_SPELLINGS: dict[str, str] = {
    "_degrees": "_deg",
    "_seconds": "_s",
    "_km_h": "_kmh",
    "_db_s": "_db_per_s",
    "_knots": "_kt",
    "_h": "_hours",
}

#: Compound units whose last word is the hour of a rate, not a duration.
PER_HOUR_UNITS = ("_mm_h",)

#: Names that end in a rejected spelling and mean something else by it.
_HENRY = "an inductance in henries, H, the SI unit of inductance, not hours"
SPELLING_EXEMPT: dict[tuple[str, str, str], str] = {
    (
        "phonometry.electroacoustics.induction_loop_components",
        "LoopImpedance",
        "inductance_h",
    ): _HENRY,
    (
        "phonometry.electroacoustics.induction_loop_components",
        "loop_impedance",
        "inductance_h",
    ): _HENRY,
    (
        "phonometry.hearing.hearing_protectors",
        "HMLRatingResult",
        "subject_h",
    ): (
        "H_j of ISO 4869-2 Formula (12) per test subject, the H of the HML "
        "rating and a value in decibels, not hours"
    ),
}

#: Published constants under the rule that stay without a unit, keyed by the
#: module that owns them, with the reason. Every one is a count, a label, a
#: pure number or a set of figures that carry their own units; a constant in
#: decibels says so with ``_DB`` instead of a place here.
_A_COUNT = "a count, which is what the name already says"
_A_LABEL = (
    "the number Clause 5.2 of IEC 60534-8-3 gives a noise regime, a label and "
    "not a quantity"
)
_A_FRACTION = "a relative figure, a fraction of the quantity it names"
_A_RATIO = "a ratio of two figures in one unit, a pure number"
_A_MULTIPLE = "a multiple of another figure in the same unit, a pure number"
_A_MACH = "a Mach number, a pure number"
_A_KB = (
    "a weighted vibration severity KB of DIN 4150-2, which the standard "
    "defines without a unit"
)
_A_VDV = (
    "a vibration dose value in m/s^1.75, the one unit that quantity has; no "
    "other quantity in the tree shares it and no suffix spells the power"
)


def _exempt(reason: str, module: str, *names: str) -> dict[tuple[str, str], str]:
    """One reason for several constants of one module."""
    return {(f"phonometry.{module}", name): reason for name in names}


CONSTANT_EXEMPT: dict[tuple[str, str], str] = {
    **_exempt(
        "the number of 10 s blocks in one 10 min period, a count",
        "environment.assessment.wind_turbine_modulation",
        "AM_PERIOD_BLOCKS",
    ),
    **_exempt(
        _A_COUNT,
        "environment.assessment.wind_turbine_modulation",
        "AM_BLOCK_SAMPLES",
        "AM_MINIMUM_VALID_BLOCKS",
    ),
    **_exempt(
        "the prominence ratio p_AM of Formula (13), one spectral line over the "
        "mean of its neighbours and a pure number",
        "environment.assessment.wind_turbine_modulation",
        "AM_PROMINENCE_THRESHOLD",
    ),
    **_exempt(
        "the local clock hour each evaluation period starts and ends at, not a "
        "duration",
        "environment.assessment.spain",
        "RD1367_PERIOD_CLOCK_LIMITS",
    ),
    **_exempt(
        _A_COUNT, "environment.assessment.soundscape", "METHOD_B_MAXIMUM_SOURCES"
    ),
    **_exempt(
        "the half-range of the ISO/TS 12913-3 coordinates, which are scale "
        "points and carry no unit",
        "environment.assessment.soundscape",
        "PLEASANTNESS_EVENTFULNESS_RANGE",
    ),
    **_exempt(
        _A_COUNT, "environment.propagation.barrier_in_situ", "MINIMUM_REPETITIONS"
    ),
    **_exempt(
        "the numbers of the microphones of the grid, labels",
        "environment.propagation.barrier_reflection",
        "REFLECTION_LOW_BAND_MICROPHONES",
    ),
    **_exempt(
        _A_RATIO,
        "environment.propagation.noise_reducing_devices",
        "ABSORPTION_RATIO_LIMIT",
    ),
    **_exempt(
        _A_COUNT, "environment.propagation.software_quality", "MINIMUM_SAMPLE_SIZE"
    ),
    **_exempt(
        "how many standard deviations of the measured speed, a pure number",
        "environment.sources.statistical_pass_by",
        "SPB_SPEED_WINDOW_STANDARD_DEVIATIONS",
    ),
    **_exempt(
        "the temporal variability indicator F1 of ISO 9614-1, a standard "
        "deviation over a mean and a pure number",
        "emission.intensity",
        "TEMPORAL_VARIABILITY_LIMIT",
    ),
    **_exempt(
        "an absorption coefficient, a pure number",
        "materials.absorbers.suspended_ceilings",
        "AIR_CORRECTION_LIMIT",
    ),
    **_exempt(
        _A_COUNT,
        "noise_control.cabin_insulation",
        "MAX_SOURCE_POSITIONS_IN_SITU",
        "MIN_FIXED_MICROPHONE_POSITIONS",
        "MIN_LOUDSPEAKER_POSITIONS",
        "MIN_SOURCE_POSITIONS_IN_SITU",
    ),
    **_exempt(
        _A_RATIO,
        "noise_control.enclosure_insulation",
        "ARTIFICIAL_SOURCE_LEAK_RATIO_ADVISORY",
    ),
    **_exempt(
        _A_COUNT,
        "noise_control.screen_in_situ",
        "DIRECTIVITY_POSITIONS",
        "IMPULSE_REPEATS",
    ),
    **_exempt(
        "a number of equivalent diameters, a multiple of the duct's own size",
        "noise_control.silencer_in_situ",
        "UPSTREAM_DISTANCE_DIAMETERS",
    ),
    **_exempt(
        "a number of equivalent diameters, a multiple of the duct's own size",
        "noise_control.silencer_measurement",
        "UPSTREAM_STRAIGHT_DIAMETERS",
    ),
    **_exempt(
        "how many airflow rates a series is measured at, a count",
        "noise_control.silencer_measurement",
        "MINIMUM_FLOW_RATES",
    ),
    **_exempt(
        "solid angles, whose only unit is the steradian; the degree and radian "
        "of a plane angle, which put angles under the rule, do not reach them",
        "noise_control.silencer_measurement",
        "RADIATION_SOLID_ANGLES",
    ),
    **_exempt(
        "a ratio of two areas, a pure number",
        "noise_control.silencer_measurement",
        "SURVEY_AREA_RATIO_RANGE",
    ),
    **_exempt(
        _A_MACH,
        "noise_control.valves",
        "EXPANDER_PIPE_MACH_LIMIT",
        "MACH_LIMIT_STANDARD_TRIM",
        "PIPE_WALL_MACH_LIMIT",
    ),
    **_exempt(
        "the length-to-diameter ratio of a flow passage, a pure number",
        "noise_control.valves",
        "MAXIMUM_PASSAGE_ASPECT",
    ),
    **_exempt(
        _A_LABEL,
        "noise_control.valves",
        "REGIME_SUBSONIC",
        "REGIME_CHOKED",
        "REGIME_SUPERSONIC",
        "REGIME_SHOCK",
        "REGIME_CONSTANT_EFFICIENCY",
    ),
    **_exempt(_A_COUNT, "noise_control.valves", "REGIME_COUNT"),
    **_exempt(
        "N_16 of IEC 60534-8-3 Table 1, the numerical constant whose units "
        "follow from the ones the table fixes for Equation (27)",
        "noise_control.valves",
        "LAST_STAGE_AREA_CONSTANTS",
    ),
    **_exempt(
        "a width in x_F, a ratio of two pressure differentials and a pure number",
        "noise_control.valves_hydrodynamic",
        "CAVITATION_FLOOR_WIDTH",
    ),
    **_exempt(_A_COUNT, "room.acoustics", "INTEGRATED_RESPONSE_DECAYS"),
    **_exempt(
        "a bandwidth times a decay time, a pure number",
        "room.acoustics",
        "MINIMUM_BANDWIDTH_TIME_PRODUCT",
    ),
    **_exempt(_A_MULTIPLE, "room.acoustics", "MINIMUM_DETECTOR_MULTIPLE"),
    **_exempt(
        "a difference of IACC, a correlation coefficient and a pure number",
        "room.auditorium",
        "IACC_JND",
    ),
    **_exempt(_A_COUNT, "room.auditorium", "STAGE_SUPPORT_POSITIONS"),
    **_exempt(
        "the directivity factor Q, a ratio of two intensities and a pure number",
        "room.crowd_noise",
        "TALKER_DIRECTIVITY",
    ),
    **_exempt(
        "lg 2 as Equation (5) of ISO 14257 prints it, a pure number",
        "room.spatial_decay",
        "DECADE_TO_DOUBLING",
    ),
    **_exempt(_A_VDV, "vibration.human.exposure", "WBV_EAV_VDV", "WBV_ELV_VDV"),
    **_exempt(
        _A_FRACTION,
        "vibration.human.seat_vibration",
        "DAMPING_TEST_MASS_TOLERANCE",
        "RUN_AGREEMENT_TOLERANCE",
    ),
    **_exempt(_A_COUNT, "vibration.human.seat_vibration", "TEST_RUNS"),
    **_exempt(
        "a SEAT factor or a transmissibility of one, a ratio of two magnitudes",
        "vibration.human.seat_vibration",
        "UNITY_TRANSMISSION",
    ),
    **_exempt(
        "a ratio of two masses, a pure number",
        "vibration.immission.coupling",
        "MASS_LOADING_RATIO_LIMIT",
    ),
    **_exempt(
        "a shear strain, a ratio of two lengths and a pure number",
        "vibration.immission.ground",
        "SHEAR_STRAIN_LINEAR_LIMIT",
    ),
    **_exempt(
        _A_KB,
        "vibration.immission.people",
        "BLASTING_EXCEPTION_KB_FMAX",
        "CONSTRUCTION_BLASTING_A_O",
        "ROAD_NIGHT_INVESTIGATION_KB",
    ),
    **_exempt(
        "how many events in a week or a day, a count",
        "vibration.immission.people",
        "BLASTING_MAX_PER_WEEK",
        "RARE_EVENTS_PER_DAY",
    ),
    **_exempt(
        "the weight of Formula (5), a pure number",
        "vibration.immission.people",
        "REST_TIME_WEIGHT",
    ),
    **_exempt(
        "a transfer value, a ratio of two vibration magnitudes",
        "vibration.immission.prediction",
        "FOUNDATION_TRANSFER_ABOVE_RESONANCE",
    ),
    **_exempt(
        "the system damping D_0, a damping ratio and a pure number",
        "vibration.immission.prediction",
        "LOOSE_GROUND_SYSTEM_DAMPING",
    ),
    **_exempt(_A_COUNT, "vibration.immission.prediction", "STOREY_FORMULA_MIN_STOREYS"),
    **_exempt(
        _A_FRACTION,
        "vibration.immission.railway_prediction",
        "SPEED_RESCALING_LIMIT",
    ),
    **_exempt(
        _A_FRACTION,
        "vibration.immission.vibration_meter",
        "ASSESSMENT_WEIGHTING_TOLERANCE",
    ),
    **_exempt(
        _A_KB,
        "vibration.immission.vibration_meter",
        "KB_DETECTION_LIMIT",
        "TAKT_SUPPRESSION_THRESHOLD",
    ),
    **_exempt(
        _A_MULTIPLE,
        "vibration.machinery.evaluation",
        "GEAR_ACCEPTANCE_HEADROOM",
        "OPERATIONAL_LIMIT_HEADROOM",
    ),
    **_exempt(
        "the slenderness ratio y_max / i of Formula (1), a pure number",
        "vibration.structural.building_damage",
        "BENDING_STRESS_CONSTANT",
    ),
    **_exempt(
        _A_COUNT, "vibration.structural.building_damage", "STOREY_FREQUENCY_MIN_STOREYS"
    ),
    **_exempt(
        "the ranges of k_1, k_2 and k_3 of ISO 4866 Annex D, Formulas (D.1) to "
        "(D.3), each in the unit its own formula gives it",
        "vibration.structural.building_response",
        "PERIOD_COEFFICIENT_RANGES",
    ),
    **_exempt(
        _A_FRACTION,
        "vibration.structural.building_response",
        "EMPIRICAL_FREQUENCY_TOLERANCE",
    ),
    **_exempt(
        _A_FRACTION,
        "vibration.structural.impact_mobility",
        "CHANNEL_MAGNITUDE_TOLERANCE",
    ),
    **_exempt(_A_COUNT, "vibration.structural.impact_mobility", "COHERENCE_RECORDS"),
    **_exempt(
        "a coherence, a pure number",
        "vibration.structural.impact_mobility",
        "HIGH_COHERENCE",
    ),
    **_exempt(
        _A_COUNT, "vibration.structural.transfer_stiffness", "MIN_FREQUENCIES_PER_BAND"
    ),
    **_exempt(
        "a transmissibility magnitude, a ratio of two accelerations",
        "vibration.structural.transfer_stiffness",
        "TRANSMISSIBILITY_LIMIT",
    ),
}

#: Parameters that name a quantity and stay bare, with the reason. Two shapes
#: qualify. One is an acoustic pressure: a waveform or a field, always in
#: pascals, and often a :class:`~phonometry.io.Signal` whose calibration says
#: so itself, so a suffix would restate the type rather than resolve an
#: ambiguity. The other is a name that speaks of a quantity without holding
#: one: the parameter of a distribution of diameters is a property of the fit
#: and not a diameter, and giving it a length suffix would be a lie about what
#: it is.
_ACOUSTIC = "acoustic pressure, always in pascals; a Signal carries its own calibration"
_OF_A_DISTRIBUTION = (
    "the parameter of a Poisson distribution fitted to the diameters, not a "
    "diameter: dimensionless, with the class width it is referred to stated in "
    "the data file it is read from"
)
EXEMPT: dict[tuple[str, str, str], str] = {
    (
        "phonometry.materials.absorbers.catalogue",
        "PorousMaterial",
        "fibre_diameter_distribution_parameter",
    ): _OF_A_DISTRIBUTION,
    ("phonometry.underwater.acoustics", "sound_pressure_level", "pressure"): _ACOUSTIC,
    ("phonometry.underwater.acoustics", "sound_exposure_level", "pressure"): _ACOUSTIC,
    (
        "phonometry.underwater.acoustics",
        "peak_sound_pressure_level",
        "pressure",
    ): _ACOUSTIC,
    (
        "phonometry.underwater.sources.pile_driving_noise",
        "single_strike_sel",
        "pressure",
    ): _ACOUSTIC,
    (
        "phonometry.underwater.sources.pile_driving_noise",
        "strike_sel_spectrum",
        "pressure",
    ): _ACOUSTIC,
    (
        "phonometry.underwater.sources.pile_driving_noise",
        "pile_strike_metrics",
        "pressure",
    ): _ACOUSTIC,
    (
        "phonometry.underwater.sources.pile_driving_noise",
        "PileStrikeResult",
        "pressure",
    ): _ACOUSTIC,
    (
        "phonometry.underwater.propagation.numerical",
        "GaussianBeamResult",
        "pressure",
    ): _ACOUSTIC,
    ("phonometry.simulation.ntff", "ContourPhasors", "pressure"): _ACOUSTIC,
    ("phonometry.simulation.fdtd", "FDTDResult", "pressures"): _ACOUSTIC,
    # An evaluation period is not a length of time here: it is which of the
    # three the assessment is about, or the assessments themselves.
    (
        "phonometry.environment.assessment.spain",
        "PeriodAssessment",
        "period",
    ): 'the label "day", "evening" or "night", not a duration',
    (
        "phonometry.environment.assessment.spain",
        "ActivityAssessment",
        "periods",
    ): "the per-period assessments themselves, one result object each",
    (
        "phonometry.environment.assessment.rating",
        "composite_rating_level",
        "periods",
    ): "(level, hours, adjustment) triples; each carries its own unit",
    # Counts and waveforms built on the word, not quantities in its unit.
    (
        "phonometry.signals.synchronous_average",
        "SynchronousAverageResult",
        "period_waveform",
    ): "the averaged waveform itself, in the unit of the record it came from",
    (
        "phonometry.signals.synchronous_average",
        "SynchronousAverageResult",
        "samples_per_period",
    ): "a count of samples, which is what the name already says",
    (
        "phonometry.signals.test_signals",
        "ToneBurstResult",
        "period_samples",
    ): "a count of samples, which is what the name already says",
    # The bearing formulae use the two diameters as a ratio d/D, so the unit
    # cancels and the docstring asks only that both be the same one.
    (
        "phonometry.vibration.machinery.diagnostics",
        "bearing_fault_frequencies",
        "element_diameter",
    ): "d of the ratio d/D; any unit, as long as it matches pitch_diameter",
    (
        "phonometry.vibration.machinery.diagnostics",
        "bearing_fault_frequencies",
        "pitch_diameter",
    ): "D of the ratio d/D; any unit, as long as it matches element_diameter",
}


#: Conditions that keep their positional slot, with the reason. The bar is a
#: signature the caller cannot reach any other way, not a call site that would
#: be tedious to update.
POSITIONAL: dict[tuple[str, str, str], str] = {
    (
        "phonometry.metrology.calibration",
        "sensitivity",
        "reference_pressure_pa",
    ): (
        "the positional form is part of the Signal overload contract of this "
        "function, so it moves with that contract and not with a sweep of the "
        "ambient conditions"
    ),
}


class Parameter(NamedTuple):
    """One public parameter, and where a reader finds it."""

    module: str
    qualname: str
    name: str
    where: str
    positional_with_default: bool = False
    #: The annotation as written, so a sibling guard can read the type off it
    #: without walking the API a second time.
    annotation: str = ""
    #: ``True`` when a caller can still pass this one by position.
    positional: bool = False


def _is_public(name: str) -> bool:
    """Whether a module part, a definition or a parameter is public."""
    return not name.startswith("_")


def public_modules() -> Iterator[tuple[str, ModuleType]]:
    """Every module a caller can import by a public path, imported."""
    yield "phonometry", phonometry
    for found in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        if not all(_is_public(part) for part in found.name.split(".")):
            continue
        try:
            yield found.name, importlib.import_module(found.name)
        except ImportError:  # pragma: no cover - an optional backend
            continue


#: :func:`_where` by the identity of what it was asked about. The object is
#: kept beside its answer, so an id is never reused for another one while the
#: entry stands.
_WHERE: dict[int, tuple[object, str]] = {}


def _where(obj: object) -> str:
    """``path:line`` of a definition, or an empty string when it has none.

    Remembered: reading the source of a class is the costly step of the walk,
    and every member of a class asks for the same one.
    """
    known = _WHERE.get(id(obj))
    if known is not None and known[0] is obj:
        return known[1]
    try:
        path = inspect.getsourcefile(obj)  # type: ignore[arg-type]
        line = inspect.getsourcelines(obj)[1]  # type: ignore[arg-type]
    except (OSError, TypeError):
        path = None
    where = (
        ""
        if path is None
        else f"{pathlib.Path(path).resolve().relative_to(ROOT)}:{line}"
    )
    _WHERE[id(obj)] = (obj, where)
    return where


def _members(name: str, obj: object) -> Iterator[tuple[str, object]]:
    """One callable per name a caller can call: the object and its methods.

    A classmethod or a staticmethod is a descriptor in the class dictionary,
    not a function, so the function it wraps is the one yielded: an
    alternative constructor takes its parameters by name as much as
    ``__init__`` does.
    """
    yield name, obj
    if not inspect.isclass(obj):
        return
    for attribute, member in vars(obj).items():
        if not _is_public(attribute):
            continue
        if isinstance(member, property) and member.fget is not None:
            yield f"{name}.{attribute}", member.fget
        elif isinstance(member, (classmethod, staticmethod)):
            yield f"{name}.{attribute}", member.__func__
        elif inspect.isfunction(member):
            yield f"{name}.{attribute}", member


def public_parameters() -> Iterator[Parameter]:
    """Every parameter a caller can name in a call to the published API."""
    seen: set[tuple[str, str, str]] = set()
    for module_name, module in public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported, None)
            if not callable(obj):
                continue
            for qualname, target in _members(exported, obj):
                if not callable(target):
                    continue
                try:
                    signature = inspect.signature(target)
                except (TypeError, ValueError):
                    continue
                home = getattr(target, "__module__", module_name)
                params = list(signature.parameters.values())
                for position, parameter in enumerate(params):
                    if parameter.name in {"self", "cls"}:
                        continue
                    key = (home, qualname, parameter.name)
                    if key in seen:
                        continue
                    seen.add(key)
                    # The second half of the rule: a condition that carries a
                    # default and is not what the call is about should be
                    # written by name. Three bare numbers in a row is the
                    # order nobody remembers.
                    loose = (
                        position > 0
                        and parameter.default is not inspect.Parameter.empty
                        and parameter.kind is parameter.POSITIONAL_OR_KEYWORD
                    )
                    annotation = parameter.annotation
                    declared = (
                        "" if annotation is inspect.Parameter.empty else str(annotation)
                    )
                    yield Parameter(
                        home,
                        qualname,
                        parameter.name,
                        _where(target),
                        loose,
                        declared,
                        parameter.kind is parameter.POSITIONAL_OR_KEYWORD,
                    )


def _says(lowered: str, words: frozenset[str]) -> bool:
    """Whether a lowercase name holds one of ``words`` as a word or a run of words."""
    padded = f"_{lowered}_"
    return any(f"_{word}_" in padded for word in words)


def names_a_quantity(name: str) -> bool:
    """Whether the parameter name says one of the quantities under the rule."""
    lowered = name.lower()
    if _says(lowered, WORD_QUANTITIES):
        return True
    return any(quantity in lowered for quantity in QUANTITIES)


def holds_a_truth_value(annotation: str) -> bool:
    """Whether the annotation is ``bool``, alone or beside ``None``.

    A verdict such as ``humidity_ok`` or a switch such as a
    ``temperature_corrected`` flag names a quantity and holds no number of it,
    so there is no unit to lose and none to put in the name.
    """
    parts = {
        part.strip().strip("'\"")
        for part in annotation.replace("Optional[", "").rstrip("]").split("|")
    }
    return bool(parts) and parts - {"None"} == {"bool"}


def declares_its_unit(name: str) -> bool:
    """Whether the name ends in a unit or says it carries none."""
    lowered = name.lower()
    return lowered.endswith(UNITS) or lowered.endswith(DIMENSIONLESS)


def constant_declares_its_unit(name: str) -> bool:
    """Whether a constant's name ends in a unit or says it carries none."""
    return declares_its_unit(name) or name.lower().endswith(CONSTANT_DIMENSIONLESS)


def offenders(
    parameters: Iterable[Parameter] | None = None,
) -> tuple[list[Parameter], list[Parameter], list[tuple[str, str, str]]]:
    """The unnamed units, the ones a caller can still pass by position, and stale keys.

    ``parameters`` is a walk of :func:`public_parameters` already made, so
    :func:`main` walks the API once for the three rules.
    """
    unnamed: list[Parameter] = []
    loose: list[Parameter] = []
    used: set[tuple[str, str, str]] = set()
    for parameter in public_parameters() if parameters is None else parameters:
        if not names_a_quantity(parameter.name):
            continue
        if holds_a_truth_value(parameter.annotation):
            continue
        key = (parameter.module, parameter.qualname, parameter.name)
        if key in EXEMPT or key in POSITIONAL:
            used.add(key)
            if key in POSITIONAL and not declares_its_unit(parameter.name):
                unnamed.append(parameter)
            continue
        if not declares_its_unit(parameter.name):
            unnamed.append(parameter)
        # Only the dimensional half: a level, a ratio or an index carries no
        # unit to get wrong, so nothing is lost by passing one by position.
        if parameter.positional_with_default and parameter.name.lower().endswith(UNITS):
            loose.append(parameter)
    stale = [k for k in (*EXEMPT, *POSITIONAL) if k not in used]
    return unnamed, loose, stale


class PublicName(NamedTuple):
    """One public name of any kind, and where a reader finds it."""

    module: str
    qualname: str
    name: str
    where: str


def _fields(obj: type) -> Iterator[str]:
    """The fields of a dataclass or a named tuple, ``init=False`` ones included."""
    if dataclasses.is_dataclass(obj):
        yield from (field.name for field in dataclasses.fields(obj))
    yield from getattr(obj, "_fields", ())


def _assigns(module: ModuleType, name: str) -> int:
    """The line a module assigns ``name`` at its top level on, or 0."""
    path = getattr(module, "__file__", None)
    if path is None:
        return 0
    pattern = re.compile(rf"^{re.escape(name)}\s*[:=]")
    lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
    return next((n for n, text in enumerate(lines, 1) if pattern.match(text)), 0)


def _owner(name: str, obj: object, exporters: list[str]) -> tuple[str, str]:
    """The module that writes a published constant, and ``path:line`` of it.

    A constant has no ``__module__``: the package that re-exports it and the
    module that assigns it hold the same object, and the module that assigns
    it may not list it in an ``__all__`` of its own. The owner is the module
    whose source assigns the name to that object.
    """
    candidates = [
        module
        for module_name, module in sorted(sys.modules.items())
        if module_name.startswith("phonometry")
        and module is not None
        and getattr(module, name, None) is obj
    ]
    for module in candidates:
        line = _assigns(module, name)
        if line:
            path = pathlib.Path(module.__file__ or "").resolve().relative_to(ROOT)
            return module.__name__, f"{path}:{line}"
    deepest = max(exporters, key=lambda m: m.count("."))
    return deepest, deepest


def public_constants() -> Iterator[tuple[PublicName, object]]:
    """Every UPPER_CASE constant a public module publishes, once, at its owner."""
    exporters: dict[tuple[str, int], list[str]] = {}
    objects: dict[tuple[str, int], object] = {}
    for module_name, module in public_modules():
        for exported in getattr(module, "__all__", ()):
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", exported):
                continue
            obj = getattr(module, exported, None)
            if inspect.ismodule(obj) or inspect.isclass(obj) or callable(obj):
                continue
            exporters.setdefault((exported, id(obj)), []).append(module_name)
            objects[(exported, id(obj))] = obj
    for key in sorted(exporters):
        name, _ = key
        owner, where = _owner(name, objects[key], exporters[key])
        yield PublicName(owner, "", name, where), objects[key]


def public_names(
    parameters: Iterable[Parameter] | None = None,
) -> Iterator[PublicName]:
    """Every name a caller can write: exports, members, fields and parameters."""
    seen: set[tuple[str, str, str]] = set()

    def once(entry: PublicName) -> Iterator[PublicName]:
        key = (entry.module, entry.qualname, entry.name)
        if key not in seen:
            seen.add(key)
            yield entry

    for entry, _ in public_constants():
        yield from once(entry)
    for module_name, module in public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported, None)
            if inspect.ismodule(obj):
                continue
            if not (inspect.isclass(obj) or callable(obj)):
                # An UPPER_CASE constant came out of public_constants() at
                # its owner; any other value is checked where it is exported.
                if not re.fullmatch(r"[A-Z][A-Z0-9_]*", exported):
                    yield from once(PublicName(module_name, "", exported, module_name))
                continue
            home = getattr(obj, "__module__", module_name)
            yield from once(PublicName(home, "", exported, _where(obj)))
            if not inspect.isclass(obj):
                continue
            members = {a for a in vars(obj) if _is_public(a)} | set(_fields(obj))
            for attribute in sorted(members):
                yield from once(PublicName(home, exported, attribute, _where(obj)))
    for parameter in public_parameters() if parameters is None else parameters:
        yield from once(
            PublicName(
                parameter.module, parameter.qualname, parameter.name, parameter.where
            )
        )


def rejected_spelling(name: str) -> str | None:
    """The suffix a name ends in that the tree spells another way, if any."""
    lowered = name.lower()
    for rejected in sorted(REJECTED_SPELLINGS, key=len, reverse=True):
        if not lowered.endswith(rejected):
            continue
        if rejected == "_h" and lowered.endswith(PER_HOUR_UNITS):
            return None
        return rejected
    return None


def misspelled(
    parameters: Iterable[Parameter] | None = None,
) -> tuple[list[tuple[PublicName, str]], list[tuple[str, str, str]]]:
    """The public names that spell a unit the retired way, and stale exemptions."""
    found: list[tuple[PublicName, str]] = []
    used: set[tuple[str, str, str]] = set()
    for entry in public_names(parameters):
        rejected = rejected_spelling(entry.name)
        if rejected is None:
            continue
        key = (entry.module, entry.qualname, entry.name)
        if key in SPELLING_EXEMPT:
            used.add(key)
            continue
        found.append((entry, rejected))
    return found, [k for k in SPELLING_EXEMPT if k not in used]


def holds_a_number(value: object) -> bool:
    """Whether a constant holds a bare number a reader could take in a wrong unit.

    A label (a string, a tuple of strings) holds none, and nor does a record:
    a dataclass or a named tuple carries its numbers in fields, whose names
    the parameter rule already holds to theirs.
    """
    if isinstance(value, (bool, str, bytes)):
        return False
    if isinstance(value, (int, float, complex, np.number)):
        return True
    if isinstance(value, np.ndarray):
        return value.dtype.kind in "iufc"
    if isinstance(value, Mapping):
        return any(holds_a_number(v) for v in (*value.keys(), *value.values()))
    if isinstance(value, tuple) and hasattr(value, "_fields"):
        return False
    if isinstance(value, (tuple, list, set, frozenset)):
        return any(holds_a_number(v) for v in value)
    return False


def holds_a_single_number(value: object) -> bool:
    """Whether a constant is one number on its own, not a table of them.

    A lone number is under the rule whatever its name says: a table keyed by
    band can let its name speak for what it holds, but ``10.0`` has only its
    name to say whether it is hertz, decibels or a count.
    """
    if isinstance(value, bool):
        return False
    if isinstance(value, np.ndarray):
        return value.ndim == 0 and value.dtype.kind in "iufc"
    return isinstance(value, (int, float, complex, np.number))


def constant_names_a_quantity(name: str) -> bool:
    """Whether a constant's name says a quantity under the parameter or constant rule."""
    lowered = re.sub(r"(?:^|_)(?:low|high)_frequency(?=_|$)", "", name.lower())
    return _says(lowered, CONSTANT_QUANTITIES) or names_a_quantity(lowered)


def unitless_constants() -> tuple[list[PublicName], list[tuple[str, str]]]:
    """The published constants that name a quantity and hide its unit, and stale keys."""
    found: list[PublicName] = []
    used: set[tuple[str, str]] = set()
    for entry, value in public_constants():
        if not holds_a_number(value):
            continue
        if not (holds_a_single_number(value) or constant_names_a_quantity(entry.name)):
            continue
        if constant_declares_its_unit(entry.name):
            continue
        key = (entry.module, entry.name)
        if key in CONSTANT_EXEMPT:
            used.add(key)
            continue
        found.append(entry)
    return found, [k for k in CONSTANT_EXEMPT if k not in used]


def _report_names(
    misspellings: list[tuple[PublicName, str]], constants: list[PublicName]
) -> None:
    """Print the two name rules' findings."""
    if misspellings:
        print("::error::a public name spells a unit the way the tree retired")
        print(f"{len(misspellings)} name(s) end in a rejected spelling:")
        for entry, rejected in sorted(misspellings):
            dotted = ".".join(p for p in (entry.qualname, entry.name) if p)
            wanted = entry.name[: -len(rejected)] + REJECTED_SPELLINGS[rejected]
            print(f"  {dotted} -> {wanted}  <- {entry.where}")
        print(
            "  -> one unit, one spelling: "
            + ", ".join(f"{k} is {v}" for k, v in REJECTED_SPELLINGS.items())
            + ". A name that means something else by the suffix goes in "
            "SPELLING_EXEMPT at the top of scripts/check_parameter_units.py "
            "with its reason."
        )
    if constants:
        print("::error::a published constant keeps its unit out of its name")
        print(
            f"{len(constants)} constant(s), single numbers or tables named for "
            "a quantity, do not say their unit:"
        )
        for entry in sorted(constants):
            print(f"  {entry.name}  <- {entry.where}")
        print(
            "  -> end the name in one of "
            + ", ".join(UNITS)
            + ", or, if it holds no unit, in one of "
            + ", ".join((*DIMENSIONLESS, *CONSTANT_DIMENSIONLESS))
            + "; a count, a label or a pure number goes in CONSTANT_EXEMPT at "
            "the top of scripts/check_parameter_units.py with its reason."
        )


def main() -> int:
    """Report every public name whose unit is hidden or spelled the retired way."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    parameters = list(public_parameters())
    unnamed, loose, stale = offenders(parameters)
    misspellings, stale_spellings = misspelled(parameters)
    constants, stale_constants = unitless_constants()
    stale_keys = [*stale, *stale_spellings, *stale_constants]
    if not (unnamed or loose or misspellings or constants or stale_keys):
        print(
            "Every public parameter and constant under the rule names its unit, "
            "in the one spelling the tree uses, and asks for it by name."
        )
        return 0
    if unnamed:
        print("::error::a public parameter names a quantity without its unit")
        print(f"{len(unnamed)} parameter(s) keep the unit out of the name:")
        for parameter in sorted(unnamed):
            print(f"  {parameter.qualname}({parameter.name})  <- {parameter.where}")
        print(
            "  -> end the name in one of "
            + ", ".join(UNITS)
            + ", or, if the quantity carries no unit, in one of "
            + ", ".join(DIMENSIONLESS)
            + "; an acoustic waveform goes in EXEMPT at the top of "
            "scripts/check_parameter_units.py with its reason."
        )
    if loose:
        print("::error::a public condition can still be passed as a bare number")
        print(f"{len(loose)} parameter(s) carry a default and stay positional:")
        for parameter in sorted(loose):
            print(f"  {parameter.qualname}({parameter.name})  <- {parameter.where}")
        print(
            "  -> put a bare '*' before it in the signature, or KW_ONLY before "
            "the field, so the unit in the name is written at the call site; "
            "a signature that has to keep its positional form goes in "
            "POSITIONAL with the reason."
        )
    _report_names(misspellings, constants)
    for key in stale_keys:
        print(
            f"::error::an exemption at the top of scripts/check_parameter_units.py "
            f"lists {key}, which no longer exists or no longer needs it"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
