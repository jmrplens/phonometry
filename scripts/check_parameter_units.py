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
:data:`WORD_QUANTITIES`, and inside one package the words of
:data:`PACKAGE_WORD_QUANTITIES`) ends either in a unit (:data:`UNITS`) or in a
suffix that says the quantity carries no unit of its own
(:data:`DIMENSIONLESS`, which covers the decibel levels, the ratios and the
indicators). Anything else keeps its unit in the docstring, which is not where
the mistake is made. A parameter typed ``bool`` is outside the rule whatever
its name says: a verdict such as ``humidity_ok`` holds no number of the
quantity it names.

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

The last rule is about functions: one is named for the quantity it returns,
and a quantity whose unit never changes does not put it in the name. A public
function or method whose name ends in one of :data:`FUNCTION_REJECTED_UNITS`
(a level, a correction, a difference, an index or a tolerance in decibels, a
frequency in hertz) is reported with the name it reads as without it.
One more is about decibels. A level and a level difference are in decibels
by definition, so a name whose head noun is one (a level, a loss, an
insulation, an isolation, a reduction, a rejection, a difference, an
improvement, a single-value attenuation, a correction, an adjustment, an
index, an emergence, the adaptation term of ISO 717, a shift, an increase,
a decrease or an excess of a named level, or the printed symbol of one)
says its unit already and carries no ``_db`` (:func:`decibel_head`): any
public name that does is reported with the name it reads as without it. A name whose head noun does not say decibel (a
tolerance, a margin, an uncertainty, a deviation, a step, a slope, a rate,
a ratio, a difference of another quantity) keeps it, and the parameter rule
above still asks it of a bare one: a plateau height in decibels named
``plateau_height`` fails as it always did. :data:`LEVEL_SUFFIX_EXEMPT` lists
the names that keep the suffix under such a noun, each with its reason.

:data:`FUNCTION_UNIT_EXEMPT` lists the methods that keep the suffix, each with
its reason.
"""

from __future__ import annotations

import argparse
import dataclasses
import functools
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
    from collections.abc import Callable, Iterable, Iterator
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

#: Matched as a word of the name or as a run of words, split on underscores
#: and before a trailing digit, so the ``thickness1`` of a plate pair is held
#: to the rule like its ``thickness``. Each word is listed with its plural.
#: The molar mass of a gas is written per mole by the fluids catalogue and
#: per kilomole by the clauses of IEC 60534-8-3 and ISO 11820, a factor of a
#: thousand under one name. A thickness is in metres on a layer and in
#: millimetres on the catalogue row it comes from, a spacing is a distance
#: between two microphones or the hertz between two spectral lines, and a
#: height is in metres beside a plateau height in decibels: each of them has
#: had two units under one name in this tree. A phase is in radians on a
#: transfer function and in degrees on the calibration records beside it. A
#: speed is a vehicle's in km/h in CNOSSOS-EU, in m/s along a flight path and
#: in knots on an aerodrome, or a shaft's in revolutions per minute; the speed
#: of sound is not one of them (:data:`_SOUND_SPEED`), because it has only
#: ever been written in m/s.
WORD_QUANTITIES = frozenset(
    {
        "diameter",
        "diameters",
        "angle",
        "angles",
        "period",
        "periods",
        "gradient",
        "gradients",
        "molar_mass",
        "molecular_mass",
        "thickness",
        "thicknesses",
        "spacing",
        "spacings",
        "height",
        "heights",
        "phase",
        "phases",
        "speed",
        "speeds",
        "airspeed",
        "airspeeds",
    }
)

#: The speed of sound, which a speed word inside it does not put under the
#: rule: ``speed_of_sound``, a ``seabed_sound_speed`` and the ``wave_speed``
#: of a bending wave are in m/s and nowhere else, so they are read without
#: the phrase.
_SOUND_SPEED = re.compile(r"speeds?_of_sound|sound_speeds?|wave_speeds?")

#: Where a name breaks into words: at an underscore, and between a letter and
#: the digit that numbers it (``thickness1`` is the word ``thickness`` of
#: plate 1, so a split on underscores alone would let it through bare).
_WORD_BREAK = re.compile(r"_|(?<=[a-z])(?=\d)")

#: Words held to the rule inside one package only, because only there does a
#: second unit compete for them. A distance is in metres everywhere in this
#: tree except aircraft, where the ANP database prints its noise-power-distance
#: tables in feet and the propagation beside them is computed in metres;
#: elsewhere the bare ``distances`` is the vocabulary.
PACKAGE_WORD_QUANTITIES: dict[str, frozenset[str]] = {
    "phonometry.aircraft": frozenset({"distance", "distances"}),
}

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
#: Pa² s, ``_m_hz`` is the product of a plate's thickness and its critical
#: frequency that the rows of the solids catalogue print) unless ``per``
#: puts it under the line, and the last one is the denominator of a speed, a
#: density or a stiffness (``_m_s2``, ``_kg_m3``, ``_n_m``). ``_hz`` is also
#: the other unit a spacing is written in, the spacing of spectral lines.
#: The electrical units (``_ohm``, ``_v``, ``_ma``), the imperial ones of the
#: ANP database (``_lb``, ``_hp``), the millisecond of a toneburst, the day of
#: a construction site and the decibels per 100 m of SAE ARP 866A are here
#: because the tree writes them, so the pair rule below can tell a name
#: written with one of them from the same name written bare. The minute is
#: ``_minutes``, spelled out as the hour is, because a trailing ``_min`` is a
#: minimum (``f_min``, ``kij_min``): a period that ends in ``_min`` names no
#: unit, and the rule reports it. A minute under ``per`` is the denominator
#: of a rate and reads as one, as in the feet per minute of the ANP climb
#: rates (``_ft_per_min``).
UNITS = (
    "_kpa",
    "_pa",
    "_inhg",
    "_percent",
    "_c",
    "_k",
    "_ft",
    "_ft_per_min",
    "_mm",
    "_um",
    "_m",
    "_rad",
    "_deg",
    "_sr",
    "_s",
    "_per_s",
    "_np_per_rad",
    "_minutes",
    "_hours",
    "_days",
    "_ms",
    "_hz",
    "_m_hz",
    "_khz",
    "_kmh",
    "_kt",
    "_rpm",
    "_m_s",
    "_m_s2",
    "_mm_s",
    "_kg",
    "_kg_m2",
    "_kg_m3",
    "_lb",
    "_kn",
    "_hp",
    "_m2",
    "_m3",
    "_m3_s",
    "_mm2",
    "_mm3",
    "_j_kg_k",
    "_j_kmol_k",
    "_j_mol_k",
    "_kg_mol",
    "_kg_kmol",
    "_psu",
    "_v",
    "_ma",
    "_ohm",
    "_mv_per_pa",
    "_v2_per_hz",
    "_a_per_m",
    "_per_m",
    "_per_cm",
    "_db_per_km",
    "_db_per_100m",
    "_per_hz",
    "_n_m",
    "_n_m3",
    "_n_per_m",
    "_pa_s_m",
    "_pa_s_m2",
    "_kpa_s_m2",
    "_pa2_s",
)

#: Single letters that are a unit on some names and a subscript of the
#: printed symbol on many more: newtons (``force_n``) beside the normalized
#: ``d_n``, watts (``input_power_w``) beside the weighted ``r_w``, amperes
#: (``current_a``) beside the A-weighted ``sound_power_level_a``, henries
#: (``inductance_h``). The first three rules cannot take them as units, or
#: every subscript would declare a unit it does not hold; the pair rule reads
#: them, and lists each subscript pair in :data:`PAIR_EXEMPT` with its reason.
PAIR_ONLY_UNITS = ("_n", "_w", "_a", "_h")

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
}

#: A function is named for the quantity it returns, and these are the units a
#: function name never ends in: a level, a correction, a difference, an index
#: or a tolerance is in decibels and a frequency in hertz wherever the library
#: computes one, so ``_db`` or ``_hz`` on a function only restates the
#: convention beside siblings that do not. A function keeps a unit where its
#: quantity has more than one customary unit, which is where a hazard is fixed
#: by naming: ``_mm_s`` and ``_um_s`` against metres per second, ``_s``
#: against hours, ``_m`` and ``_m2``, ``_per_m`` against decibels and nepers
#: per metre, ``_pa`` and ``_percent``.
FUNCTION_REJECTED_UNITS = ("_db", "_hz")

#: Public methods that end in one of :data:`FUNCTION_REJECTED_UNITS` and keep
#: it, keyed by the module that defines the class and the qualified name, with
#: the reason.
_A_ROW_ACCESSOR = (
    "reads the columns of one printed row, which are named for their unit as "
    "the page prints them, and is named as they are"
)
FUNCTION_UNIT_EXEMPT: dict[tuple[str, str], str] = {
    (
        "phonometry.metrology.sound_level_meter",
        "PeakReference.limits_db",
    ): _A_ROW_ACCESSOR,
    (
        "phonometry.metrology.sound_level_meter",
        "ToneburstReference.limits_db",
    ): _A_ROW_ACCESSOR,
    ("phonometry.signals.windows", "WindowMetricsResult.enbw_hz"): (
        "the equivalent noise bandwidth in hertz, beside the same bandwidth in "
        "bins that the record holds as enbw_bins"
    ),
}

#: Published constants under the rule that stay without a unit, keyed by the
#: module that owns them, with the reason. Every one is a count, a label, a
#: pure number or a set of figures that carry their own units; a constant in
#: decibels says so with ``_DB`` instead of a place here, or by its head noun
#: when it names a level or a level difference (:func:`decibel_head`).
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
        "AM_MIN_VALID_BLOCKS",
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
    **_exempt(_A_COUNT, "environment.assessment.soundscape", "METHOD_B_MAX_SOURCES"),
    **_exempt(
        "the half-range of the ISO/TS 12913-3 coordinates, which are scale "
        "points and carry no unit",
        "environment.assessment.soundscape",
        "PLEASANTNESS_EVENTFULNESS_RANGE",
    ),
    **_exempt(_A_COUNT, "environment.propagation.barrier_in_situ", "MIN_REPETITIONS"),
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
    **_exempt(_A_COUNT, "environment.propagation.software_quality", "MIN_SAMPLE_SIZE"),
    **_exempt(
        "how many standard deviations of the measured speed, a pure number",
        "environment.sources._statistical_pass_by",
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
        "noise_control._cabin_insulation",
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
        "MIN_FLOW_RATES",
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
        "MAX_PASSAGE_ASPECT",
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
        "MIN_BANDWIDTH_TIME_PRODUCT",
    ),
    **_exempt(_A_MULTIPLE, "room.acoustics", "MIN_DETECTOR_MULTIPLE"),
    **_exempt(
        "a difference of IACC, a correlation coefficient and a pure number",
        "room.auditorium",
        "IACC_JND",
    ),
    **_exempt(_A_COUNT, "room.auditorium", "STAGE_SUPPORT_POSITIONS"),
    **_exempt(
        "the directivity factor Q, a ratio of two intensities and a pure number",
        "room._crowd_noise",
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
        _A_COUNT, "vibration.structural.building_damage", "STORY_FREQUENCY_MIN_STORIES"
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
        "vibration.structural._impact_mobility",
        "CHANNEL_MAGNITUDE_TOLERANCE",
    ),
    **_exempt(_A_COUNT, "vibration.structural._impact_mobility", "COHERENCE_RECORDS"),
    **_exempt(
        "a coherence, a pure number",
        "vibration.structural._impact_mobility",
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


def _exempt_parameters(
    reason: str, module: str, *owners: tuple[str, str]
) -> dict[tuple[str, str, str], str]:
    """One reason for several ``(owner, parameter)`` pairs of one module."""
    return {(f"phonometry.{module}", owner, name): reason for owner, name in owners}


EXEMPT: dict[tuple[str, str, str], str] = {
    (
        "phonometry.materials.absorbers.catalogue",
        "PorousMaterial",
        "fiber_diameter_distribution_parameter",
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
    # A selector that names the source line by its height, not a height.
    (
        "phonometry.environment.sources.cnossos_rail",
        "vertical_directivity",
        "height",
    ): (
        "the label 1 (source A, 0.5 m) or 2 (source B, 4.0 m) that picks "
        "formula (2.3.16) or (2.3.17), a choice of source line and not a length"
    ),
    # A phase of an activity, not of a wave: RD 1367/2007 (Annex IV
    # A.3.4.2 b) splits an assessment period into the noise phases of the
    # activity.
    **_exempt_parameters(
        "a noise phase of the activity (RD 1367/2007, Annex IV A.3.4.2 b)), "
        "a stage of the period and not an angle",
        "environment.assessment.spain",
        ("PeriodAssessment", "phases"),
        ("evaluation_period_level", "phases"),
    ),
    (
        "phonometry.environment.assessment.spain",
        "PeriodAssessment",
        "phase_limit",
    ): (
        "the limit + 5 dB of Article 25.1 b iii for one noise phase of the "
        "activity, a level and not an angle"
    ),
    # A phase that is an object, a count or a complex response.
    **_exempt_parameters(
        "the SequentialComparisonPhase or SimultaneousComparisonPhase record of "
        "the IEC 61094-8 phase step, an object and not an angle",
        "metrology.comparison_calibration",
        ("sequential_comparison", "phase"),
        ("simultaneous_comparison", "phase"),
    ),
    (
        "phonometry.signals._cepstrum",
        "CepstrumResult",
        "linear_phase_samples",
    ): "a count of samples, which is what the name already says",
    (
        "phonometry.signals.phase",
        "PhaseDecompositionResult",
        "min_phase_response",
    ): (
        "the complex minimum-phase response |H| exp(j min_phase_rad), "
        "dimensionless, not an angle"
    ),
    # Verdicts held in arrays: a bool per band carries no length or angle.
    **_exempt_parameters(
        "a per-band verdict array, True where the rule is met; it holds no "
        "spacing, only whether one was respected",
        "emission.free_field_qualification",
        ("FreeFieldCheck", "spacing_met"),
        ("FreeFieldCheck", "equal_spacing_met"),
        ("FreeFieldCheck", "iso26101_spacing_met"),
    ),
    (
        "phonometry.vibration.structural._impact_mobility",
        "ChannelMatchVerification",
        "phase_within",
    ): "a per-line verdict array, True where the phase match holds; no angle",
    (
        "phonometry.building.measurement.service_equipment",
        "MeasurementDisturbanceCheck",
        "disturbed_periods",
    ): "the indices of the disturbed measurement periods, counts and not durations",
    # Speeds that are a label, a logarithm or a database's own unit.
    **_exempt_parameters(
        'the ISO 11819-1 road speed category "low", "medium" or "high", a label',
        "environment.sources._statistical_pass_by",
        ("PassByRegression", "road_speed_category"),
        ("StatisticalPassByResult", "road_speed_category"),
        ("pass_by_regression", "road_speed_category"),
        ("statistical_pass_by", "road_speed_category"),
        ("statistical_pass_by_index", "road_speed_category"),
    ),
    (
        "phonometry.environment.sources._statistical_pass_by",
        "PassByRegression",
        "lg_speed_standard_deviation",
    ): (
        "the standard deviation of lg(v), a decimal logarithm and a pure number "
        "whatever unit the speed was in"
    ),
    **_exempt_parameters(
        "an airspeed of the rotorcraft source database, in the unit its "
        "hemispheres are tabulated in: the Eq. 3-10 weights read it only as a "
        "fraction of the database span, and the docstring asks for m/s when "
        "the track supplies the query",
        "aircraft.rotorcraft_noise",
        ("RotorcraftTrackState", "airspeed"),
        ("flight_condition_weights", "airspeed"),
        ("flight_condition_weights", "airspeeds"),
        ("interpolated_source_level", "airspeed"),
        ("interpolated_source_level", "airspeeds"),
        ("rotorcraft_event_level", "airspeeds"),
        ("rotorcraft_noise_contour", "airspeeds"),
    ),
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
    #: What the docstring says the parameter, field or property holds: its
    #: ``:param:`` or ``:ivar:`` entry, or the first paragraph of a property.
    doc: str = ""
    #: The public module whose ``__all__`` publishes it, which is where a
    #: caller meets a callable defined in a private module such as ``_plot``.
    publisher: str = ""


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


def documented(doc: str | None, name: str) -> str:
    """The ``:param name:`` or ``:ivar name:`` entry of a docstring, or ``""``.

    The entry runs to the next field list item or the next blank line, so a
    description wrapped over several lines is read whole.
    """
    if not doc:
        return ""
    found = re.search(
        rf":(?:param|ivar|var)\s+{re.escape(name)}:(.*?)(?=\n\s*:[a-z]+[\s:]|\n\s*\n|\Z)",
        inspect.cleandoc(doc),
        re.DOTALL,
    )
    return " ".join(found.group(1).split()) if found else ""


def _first_paragraph(doc: str | None) -> str:
    """The summary paragraph of a docstring, on one line."""
    if not doc:
        return ""
    return " ".join(inspect.cleandoc(doc).split("\n\n", 1)[0].split())


def _properties(obj: object) -> Iterator[tuple[str, Callable[..., object]]]:
    """The public properties of a class, ``functools.cached_property`` included.

    A property is a name a caller reads off a result like a field, so the
    unit rule holds it as it holds the field beside it.
    """
    if not inspect.isclass(obj):
        return
    for attribute, member in vars(obj).items():
        if not _is_public(attribute):
            continue
        if isinstance(member, property) and member.fget is not None:
            yield attribute, member.fget
        elif isinstance(member, functools.cached_property):
            yield attribute, member.func


def _property_parameters(
    module_name: str, exported: str, obj: object
) -> Iterator[Parameter]:
    """One :class:`Parameter` per public property of an exported class."""
    for attribute, getter in _properties(obj):
        try:
            returns = inspect.signature(getter).return_annotation
        except (TypeError, ValueError):
            continue
        declared = "" if returns is inspect.Signature.empty else str(returns)
        home = getattr(obj, "__module__", module_name)
        yield Parameter(
            home,
            exported,
            attribute,
            _where(obj),
            annotation=declared,
            doc=_first_paragraph(getattr(getter, "__doc__", None)),
            publisher=module_name,
        )


def public_parameters() -> Iterator[Parameter]:
    """Every parameter a caller can name in a call to the published API.

    The properties of the published classes come with them: a caller reads
    ``result.phase_rad`` as it reads a field, and the unit is lost there as
    easily.
    """
    seen: set[tuple[str, str, str]] = set()
    for module_name, module in public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported, None)
            if not callable(obj):
                continue
            for entry in _property_parameters(module_name, exported, obj):
                key = (entry.module, entry.qualname, entry.name)
                if key not in seen:
                    seen.add(key)
                    yield entry
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
                        documented(getattr(target, "__doc__", None), parameter.name),
                        module_name,
                    )


def _says(lowered: str, words: frozenset[str]) -> bool:
    """Whether a lowercase name holds one of ``words`` as a word or a run of words.

    The name is broken into words at its underscores and before a trailing
    digit (:data:`_WORD_BREAK`), so ``thickness1`` says ``thickness``.
    """
    padded = "_" + "_".join(_WORD_BREAK.split(lowered)) + "_"
    return any(f"_{word}_" in padded for word in words)


def names_a_quantity(name: str, module: str = "") -> bool:
    """Whether the parameter name says one of the quantities under the rule.

    ``module`` is where the parameter is defined, so the words of
    :data:`PACKAGE_WORD_QUANTITIES` are held to the rule in their own package
    and nowhere else.
    """
    lowered = name.lower()
    if _says(_SOUND_SPEED.sub("", lowered), WORD_QUANTITIES):
        return True
    for package, scoped in PACKAGE_WORD_QUANTITIES.items():
        if (module == package or module.startswith(package + ".")) and _says(
            lowered, scoped
        ):
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


#: The head nouns of a level. A level is in decibels by definition and names
#: its reference elsewhere, so a name whose head noun is one of these carries
#: no ``_db``. ``spl``, ``lw``, ``lwa`` and ``leq`` are the abbreviations of a
#: sound pressure, a sound power and an equivalent level that names spell as
#: a word.
LEVEL_NOUNS = frozenset({"level", "levels", "spl", "lw", "lwa", "leq"})

#: The head nouns of a level difference that only ever hold decibels: an
#: index (the sound reduction index, the directivity index, a single-number
#: index) and a correction, which the parameter rule already reads as
#: declaring their unit (:data:`DIMENSIONLESS`), and an emergence, the
#: ambient level less the residual one (IEC TS 61400-11-2:2024 Equation
#: (J.1)).
LEVEL_DIFFERENCE_NOUNS = frozenset(
    {"index", "indices", "correction", "corrections", "emergence", "emergences"}
)

#: The head nouns of a level difference that a name can also give to a
#: difference of another quantity: a phase difference is in radians, a
#: pressure loss in pascals and a temperature reduction in kelvin. They say
#: decibel when the name names no other quantity (:func:`names_a_quantity`),
#: or names the level they are the difference of (``pressure_level_difference``).
#: An ``attenuation`` here is a single value; a rate per distance ends in
#: one of :data:`RATE_UNITS` instead. An ``adjustment`` is a quantity added
#: to a level (ISO 1996-1:2016, 3.3.1), an ``isolation`` the level with a
#: seal absent less the level with it on, and a ``rejection`` the drop of a
#: level the way an insertion loss is.
BOUND_DIFFERENCE_NOUNS = frozenset(
    {
        "difference",
        "differences",
        "loss",
        "losses",
        "insulation",
        "isolation",
        "reduction",
        "reductions",
        "rejection",
        "rejections",
        "improvement",
        "improvements",
        "attenuation",
        "attenuations",
        "adjustment",
        "adjustments",
    }
)

#: The head nouns of a change that is a level difference only when the name
#: names the level that changes: a ``level_shift``, a ``level_increase`` or a
#: ``level_excess`` is in decibels, while the ``shift`` of a rating curve is
#: a step of the absorption coefficient and a ``drop_height`` a length.
LEVEL_CHANGE_NOUNS = frozenset(
    {
        "shift",
        "shifts",
        "increase",
        "increases",
        "decrease",
        "decreases",
        "excess",
        "drop",
        "drops",
        "rise",
        "rises",
        "change",
        "changes",
        "increment",
        "increments",
    }
)

#: The spectrum adaptation term of ISO 717-1 and ISO 717-2, which the
#: standards define as a value in decibels added to a single-number rating:
#: a correction to a level difference, named by its two words.
_ADAPTATION_TERM = ("adaptation", "term")

#: A name spelled as the printed symbol of a level, read by its first word:
#: :math:`L` with its subscripts (``l_n``, ``l_i_fmax``, ``l1``, ``lp_aeqt``),
#: and an improvement or a reduction written :math:`\Delta L` or
#: :math:`\Delta R` (``delta_lw``, ``delta_rw``).
_DECIBEL_SYMBOL = re.compile(r"l\d*|lw|lwa|lp|spl")
_DELTA_OF_A_LEVEL = re.compile(r"[lr].*")

#: An :math:`\ell` with a number is a length in ``materials``: the distances
#: :math:`\ell_1` and :math:`\ell_2` from the specimen to the nearest
#: microphones of ASTM E2611 (``l1``, ``l2``), not the :math:`L` of a level.
_LENGTH_SYMBOL = re.compile(r"l\d*")
LENGTH_SYMBOL_PACKAGES = ("phonometry.materials",)

#: Symbols that say decibel inside one package only, read as the first word of
#: a name or as its head (``min_multi_junction_kij``, ``max_k3``). In
#: ``building`` the sound reduction index :math:`R` (``r_s_w``), a level
#: difference :math:`D` (``d_2m_nt``), the C, Ctr and CI of ISO 717, the
#: spectrum adaptation terms of a rating, and the vibration reduction index
#: :math:`K_{ij}` of EN ISO 12354-1 with the path indices :math:`K_{Ff}`,
#: :math:`K_{Fd}` and :math:`K_{Df}` (``k_ij``, ``k_ff``, ``kij``). In
#: ``emission`` the corrections of the sound power standards: :math:`C_1`,
#: :math:`C_2` and :math:`C_3` for the meteorological conditions, the radiation
#: impedance and the air absorption (ISO 3745, ISO 6926), and :math:`K_1`,
#: :math:`K_2` and :math:`K_3` for the background, the environment and the
#: local environment (ISO 3744, ISO 11202). Elsewhere an ``r`` is a distance
#: (``r_direct``), a ``d`` a directivity, a ``c`` a gain or a constant of a
#: weighting function (``c_db`` of the underwater weighting is its gain) and a
#: ``c1`` a sound speed.
PACKAGE_DECIBEL_SYMBOLS: dict[str, frozenset[str]] = {
    "phonometry.building": frozenset({"r", "d", "c", "ctr", "ci", "k", "kij"}),
    "phonometry.emission": frozenset({"c1", "c2", "c3", "k1", "k2", "k3"}),
}

#: The first words of a name that is a statistic of what follows: the
#: standard deviation :math:`\sigma_L` of a level (``sigma_level_db``) or a
#: standard uncertainty :math:`u`, which are not levels.
_STATISTIC_SYMBOLS = frozenset({"sigma", "u"})

#: The words that qualify a level from behind without being its head noun:
#: a band (``_1000``, ``_1khz``), a frequency weighting (``_a``, ``_c``,
#: ``_z``), the state it was read in (``_before``, ``_after``, ``_with``,
#: ``_without``, ``_direct``, ``_measured``), a reference (``_ref``,
#: ``_norm``) or an extreme (``_max``, ``_min``).
_TRAILING_QUALIFIER = re.compile(
    r"\d+(?:khz|hz)?|[acz]|before|after|with|without|direct|measured|ref|norm"
    r"|max|min"
)

#: A level qualified by a phrase after it: ``band_levels_at_characteristic``,
#: ``linearity_levels_below_upper``. The head noun is the word before the
#: first of these.
_PREPOSITIONS = frozenset({"at", "below", "above", "to", "of", "from", "over"})


def _in_package(module: str, package: str) -> bool:
    """Whether ``module`` is ``package`` or one of its submodules."""
    return module == package or module.startswith(package + ".")


def _package_symbol(word: str, module: str) -> bool:
    """Whether ``word`` is a symbol that says decibel in the package of ``module``."""
    return any(
        _in_package(module, package) and word in symbols
        for package, symbols in PACKAGE_DECIBEL_SYMBOLS.items()
    )


def _decibel_symbol(words: list[str], module: str) -> bool:
    """Whether a name split into ``words`` is the symbol of a level or a difference.

    The subscripts after the symbol may say anything but another quantity:
    an ``l_thickness`` would be a length, whatever its first letter.
    """
    rest = "_".join(words[1:])
    if rest and names_a_quantity(rest, module):
        return False
    first = words[0]
    if _DECIBEL_SYMBOL.fullmatch(first):
        return not (
            _LENGTH_SYMBOL.fullmatch(first)
            and any(_in_package(module, p) for p in LENGTH_SYMBOL_PACKAGES)
        )
    if first == "delta" and len(words) > 1 and _DELTA_OF_A_LEVEL.fullmatch(words[1]):
        return True
    return _package_symbol(first, module)


def _head_says_decibel(words: list[str], module: str) -> bool:
    """Whether the last word of ``words``, past its qualifiers, says decibel.

    The last word may be a noun or, in its package, the printed symbol of a
    correction or an index (:data:`PACKAGE_DECIBEL_SYMBOLS`): the cap on
    :math:`K_3` of ISO 11202 is ``max_k3``.
    """
    words = list(words)
    while len(words) > 1 and _TRAILING_QUALIFIER.fullmatch(words[-1]):
        words.pop()
    if tuple(words[-2:]) == _ADAPTATION_TERM:
        return True
    head = words[-1]
    if head in LEVEL_NOUNS or head in LEVEL_DIFFERENCE_NOUNS:
        return True
    if _package_symbol(head, module):
        return True
    names_a_level = any(word in LEVEL_NOUNS for word in words[:-1])
    if head in LEVEL_CHANGE_NOUNS:
        return names_a_level
    if head not in BOUND_DIFFERENCE_NOUNS:
        return False
    stem = "_".join(words[:-1])
    return names_a_level or not (stem and names_a_quantity(stem, module))


def decibel_head(name: str, module: str = "") -> bool:
    """Whether the head noun of a name says it holds a level or a level difference.

    The head noun is the last word of the name once the words that qualify
    it from behind are set aside (:data:`_TRAILING_QUALIFIER`), or, when that
    word says nothing of the kind, the word before a prepositional phrase
    (:data:`_PREPOSITIONS`): ``band_levels_at_characteristic`` is a level,
    ``front_to_random_index`` an index. A name spelled as a printed symbol
    is read by its first word (:data:`_DECIBEL_SYMBOL`), and a name that is
    a statistic of a level (``sigma_level``) is not a level. ``module`` is
    where the name is defined, for the symbols that say decibel in one
    package only.
    """
    words = [word for word in name.lower().split("_") if word]
    if not words or words[0] in _STATISTIC_SYMBOLS:
        return False
    if _decibel_symbol(words, module) or _head_says_decibel(words, module):
        return True
    cut = next((i for i, word in enumerate(words) if i and word in _PREPOSITIONS), None)
    return cut is not None and _head_says_decibel(words[:cut], module)


def decibel_suffix(name: str, module: str = "") -> str | None:
    """The ``_db`` a level or a level difference carries in its name, if any.

    The suffix ends the name (``insertion_loss_db``) or stands inside it
    before a qualifier (``level_db_at``). A ``_db`` that opens a rate
    (``_db_per_m``) or closes one (``class_densities_per_db``) is a unit of
    another quantity and is not this one.
    """
    words = name.lower().split("_")
    for position, word in enumerate(words):
        if word != "db" or not position:
            continue
        if words[position - 1] == "per" or words[position + 1 : position + 2] == [
            "per"
        ]:
            continue
        if decibel_head("_".join(words[:position]), module):
            return "_" + "_".join(words[position:])
    return None


def declares_its_unit(name: str, module: str = "") -> bool:
    """Whether the name ends in a unit or says it carries none.

    A level or a level difference says it carries none by its head noun
    (:func:`decibel_head`), which is why it carries no ``_db``.
    """
    lowered = name.lower()
    return (
        lowered.endswith(UNITS)
        or lowered.endswith(DIMENSIONLESS)
        or decibel_head(lowered, module)
    )


def constant_declares_its_unit(name: str, module: str = "") -> bool:
    """Whether a constant's name ends in a unit or says it carries none.

    ``module`` is where the constant is published, for the symbols that say
    decibel in one package only (``MAX_K3`` in ``emission``).
    """
    return declares_its_unit(name, module) or name.lower().endswith(
        CONSTANT_DIMENSIONLESS
    )


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
        if not names_a_quantity(parameter.name, parameter.module):
            continue
        if holds_a_truth_value(parameter.annotation):
            continue
        key = (parameter.module, parameter.qualname, parameter.name)
        if key in EXEMPT or key in POSITIONAL:
            used.add(key)
            if key in POSITIONAL and not declares_its_unit(
                parameter.name, parameter.module
            ):
                unnamed.append(parameter)
            continue
        if not declares_its_unit(parameter.name, parameter.module):
            unnamed.append(parameter)
        # Only the dimensional half: a level, a ratio or an index carries no
        # unit to get wrong, so nothing is lost by passing one by position.
        if parameter.positional_with_default and parameter.name.lower().endswith(UNITS):
            loose.append(parameter)
    stale = [k for k in (*EXEMPT, *POSITIONAL) if k not in used]
    return unnamed, loose, stale


#: The words of a rate at which a wave loses energy over distance. Only a
#: rate is held to the rule below: an absorption coefficient alpha is a pure
#: number and an attenuation in decibels is a level difference, and both keep
#: the names they have.
RATE_WORDS = frozenset({"absorption", "attenuation"})

#: A coefficient is the other word a rate goes by: ISO 9613-1 calls its alpha
#: in dB/m "the attenuation coefficient", and a record that holds it per band
#: can name the field ``coefficient`` alone, which says neither word above.
#: A coefficient documented per distance is held to the rate rule; one that
#: is a pure number never is, because its docstring gives no distance.
RATE_COEFFICIENT_WORDS = frozenset({"coefficient", "coefficients"})

#: The endings an attenuation or absorption rate takes: decibels per metre,
#: decibels per kilometre, or a coefficient per metre whose own unit (neper,
#: or the power ratio of ISO 354's ``m``) the name says before ``_per_m``.
RATE_UNITS = ("_db_per_m", "_db_per_km", "_per_m")

#: A unit per distance as a docstring writes it: dB/m, dB/km, Np/m, 1/m,
#: m^-1, "per metre" or "reciprocal metres".
_PER_DISTANCE = re.compile(
    r"(?:\bdB|\bNp|neper)s?\s*(?:/|per)\s*(?:k?m\b|100\s*m\b|metre|meter|kilomet)"
    r"|\b1\s*/\s*m\b|m\^\{?-1|m\u207b\u00b9|\bper\s+(?:kilo)?met(?:re|er)"
    r"|reciprocal\s+met(?:re|er)",
    re.IGNORECASE,
)

#: Names under the rate rule that are not a rate, keyed by location.
RATE_EXEMPT: dict[tuple[str, str, str], str] = {}


def misnamed_rates(
    parameters: Iterable[Parameter] | None = None,
) -> tuple[list[Parameter], list[tuple[str, str, str]]]:
    """The attenuation and absorption rates whose name hides the distance.

    A name that says ``absorption``, ``attenuation`` or ``coefficient`` and
    whose docstring gives it a unit per distance ends in one of
    :data:`RATE_UNITS`: an ``absorption_coefficient`` in dB/km beside the
    dimensionless ``absorption_coefficient`` of a wall reads as the wall's,
    a ``_coefficient`` suffix is what the rule reads as a pure number, and a
    bare ``coefficient`` in dB/m beside one in dB/100 m says neither unit.
    """
    found: list[Parameter] = []
    used: set[tuple[str, str, str]] = set()
    for parameter in public_parameters() if parameters is None else parameters:
        lowered = parameter.name.lower()
        says_a_rate = _says(lowered, RATE_WORDS) or _says(
            lowered, RATE_COEFFICIENT_WORDS
        )
        if not says_a_rate or not _PER_DISTANCE.search(parameter.doc):
            continue
        if lowered.endswith(RATE_UNITS):
            continue
        key = (parameter.module, parameter.qualname, parameter.name)
        if key in RATE_EXEMPT:
            used.add(key)
            continue
        found.append(parameter)
    return found, [k for k in RATE_EXEMPT if k not in used]


#: The pressure of the medium has one stem. ``static_pressure_`` is the
#: absolute pressure of the medium a quantity is computed in (the air, a gas
#: or sea water), with
#: the ``_pa`` or ``_kpa`` the clause it comes from writes it in; a gauge
#: pressure in a duct, which some signatures carry beside it, says
#: ``gauge`` or is the ``static_pressure_pa`` of a velocity-pressure formula.
#: Any other word for the ambient pressure is refused.
_AMBIENT_PRESSURE = re.compile(
    r"(?:^|_)(?:ambient|barometric|atmospheric|air|absolute|environmental"
    r"|outdoor|outside)_pressure(?:_|$)"
)

#: Where ``atmospheric_pressure_`` is the name, with the reason: the outside
#: atmosphere where the same method measures a stream pressure in a duct or
#: a pipe, so ``static_pressure_`` would read as the stream's.
_OUTSIDE_THE_STREAM = (
    "the atmosphere outside the duct or pipe, beside the gauge static "
    "pressure of the stream the same method measures"
)
ATMOSPHERIC_ADMITTED: dict[tuple[str, str, str], str] = {
    (
        "phonometry.noise_control.valves",
        "pipe_transmission_loss",
        "atmospheric_pressure_pa",
    ): _OUTSIDE_THE_STREAM,
    (
        "phonometry.noise_control.valves",
        "DownstreamPipe",
        "atmospheric_pressure_pa",
    ): _OUTSIDE_THE_STREAM,
    (
        "phonometry.noise_control.silencer_measurement",
        "normal_air_density",
        "atmospheric_pressure_pa",
    ): _OUTSIDE_THE_STREAM,
    (
        "phonometry.noise_control.silencer_in_situ",
        "gas_density_kg_m3",
        "atmospheric_pressure_pa",
    ): _OUTSIDE_THE_STREAM,
    (
        "phonometry.noise_control.silencer_in_situ",
        "",
        "ISO11820_ATMOSPHERIC_PRESSURE_PA",
    ): _OUTSIDE_THE_STREAM,
}


def ambient_pressure_names(
    parameters: Iterable[Parameter] | None = None,
) -> tuple[list[PublicName], list[tuple[str, str, str]]]:
    """The names that call the pressure of the medium anything but its stem.

    Parameters, fields and properties are read from the walk, and the
    published constants beside them, so a default does not keep a second
    word alive under the name it defaults.
    """
    found: list[PublicName] = []
    used: set[tuple[str, str, str]] = set()
    entries: list[PublicName] = [
        PublicName(p.module, p.qualname, p.name, p.where)
        for p in (public_parameters() if parameters is None else parameters)
    ]
    entries.extend(entry for entry, _ in public_constants())
    for entry in entries:
        lowered = entry.name.lower()
        if not _AMBIENT_PRESSURE.search(lowered):
            continue
        key = (entry.module, entry.qualname, entry.name)
        if key in ATMOSPHERIC_ADMITTED and "atmospheric_pressure" in lowered:
            used.add(key)
            continue
        found.append(entry)
    return found, [k for k in ATMOSPHERIC_ADMITTED if k not in used]


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


#: Where the bare name and the same name with a unit are allowed to stand
#: side by side in one subpackage, keyed by ``(subpackage, bare, suffixed)``,
#: with the reason. Every other pair is one quantity spelled two ways, and
#: the rule above says which way: with the unit where a second unit competes
#: for the word, without it where the word only ever had one.
_FREQUENCY_HZ = (
    "a frequency is in hertz throughout; the bare word is a result's stated "
    "frequency or a vectorised argument, and frequency_hz the scalar argument "
    "the 4.0 vocabulary keeps (upgrading guide, One spelling per concept)"
)
_KHZ_FORMULAS = (
    "the underwater formulas behind the inputs are printed with f in kHz and "
    "ranges in km beside a dB/km absorption, so the inputs name their unit "
    "and the result fields keep the axis vocabulary"
)
_SUBSCRIPT = "the suffix is a subscript of the printed symbol, not a unit"


def _pair(
    reason: str, package: str, *pairs: tuple[str, str]
) -> dict[tuple[str, str, str], str]:
    """One reason for several ``(bare, suffixed)`` pairs of one subpackage."""
    return {(f"phonometry.{package}", bare, unit): reason for bare, unit in pairs}


_A_WEIGHTED = "the A-weighted figure beside the band or unweighted one; " + _SUBSCRIPT
_WEIGHTED = (
    "the weighted single-number rating of ISO 717 or ISO 11654 beside the "
    "band values it is read from; " + _SUBSCRIPT
)
_NORMALIZED = "the normalized quantity beside the raw one; " + _SUBSCRIPT
_PATH_AND_RATE = (
    "an attenuation over a path, in dB, beside the rate per distance it is "
    "accumulated from"
)

PAIR_EXEMPT: dict[tuple[str, str, str], str] = {
    **_pair(
        "the engine power setting P that indexes the NPD curves, in whatever "
        "unit the ANP database tabulates it (pounds of thrust, per cent), "
        "beside the propulsive power of a propeller engine in horsepower",
        "aircraft",
        ("power", "power_hp"),
    ),
    **_pair(
        _NORMALIZED,
        "building",
        ("d", "d_n"),
        ("d_2m", "d_2m_n"),
        ("l_xy", "l_xy_n"),
    ),
    **_pair(
        _WEIGHTED,
        "building",
        ("d_2m_nt", "d_2m_nt_w"),
        ("delta_l", "delta_l_w"),
        ("l_prime_n", "l_prime_n_w"),
        ("r", "r_w"),
        ("r_direct", "r_direct_w"),
        ("r_prime", "r_prime_w"),
        ("r_tr_s", "r_tr_s_w"),
    ),
    **_pair(
        "the sound reduction index R_s of a joint (ISO 10140-1:2021 Annex J), "
        "its weighted R_s,w and R_s,w + C, beside the R of a facade element; "
        + _SUBSCRIPT,
        "building",
        ("r", "r_s"),
        ("r", "r_s_w"),
        ("r", "r_s_w_c"),
        ("r_s", "r_s_w"),
        ("r_s", "r_s_w_c"),
        ("r_s_w", "r_s_w_c"),
    ),
    **_pair(
        "a loudspeaker impedance curve (frequencies, modulus) or a "
        "LoopImpedance record, beside the modulus of an impedance in ohms",
        "electroacoustics",
        ("impedance", "impedance_ohm"),
    ),
    **_pair(
        "the normalized radiation resistance R1(2ka) of a piston, a pure "
        "number, beside a series resistance in ohms",
        "electroacoustics",
        ("resistance", "resistance_ohm"),
    ),
    **_pair(
        _A_WEIGHTED,
        "emission",
        ("achieved_grade", "achieved_grade_a"),
        ("background_requirement_met", "background_requirement_met_a"),
        ("expanded_uncertainty", "expanded_uncertainty_a"),
        ("sigma_r0", "sigma_r0_a"),
        ("sigma_tot", "sigma_tot_a"),
        ("sound_energy_level", "sound_energy_level_a"),
        ("sound_power_level", "sound_power_level_a"),
    ),
    **_pair(
        "the TrackDecayRate records of a reference-track check, beside the "
        "rates in dB/m one of them holds",
        "environment",
        ("decay_rates", "decay_rates_db_per_m"),
    ),
    **_pair(
        "the table limit of a Spanish evaluation period, in dB, beside a "
        "lower limit on a track decay rate in dB/m",
        "environment",
        ("limit", "limit_db_per_m"),
    ),
    **_pair(
        "the CNOSSOS-EU levels L_WR and L_WP beside the coefficients A_R and "
        "A_P they are computed from; " + _SUBSCRIPT,
        "environment",
        ("propulsion", "propulsion_a"),
        ("rolling", "rolling_a"),
    ),
    **_pair(
        "the weighted sound absorption coefficient of ISO 11654 beside the "
        "band coefficients; " + _SUBSCRIPT,
        "materials",
        ("alpha", "alpha_w"),
    ),
    **_pair(
        "the four transfer functions of the one-load method beside those of "
        "load a of the two-load method, a label",
        "materials",
        ("load", "load_a"),
    ),
    **_pair(
        "the catalogue row names the unit of every column, because the books "
        "it is transcribed from print the frame density in several; the "
        "models take the same kg/m3",
        "materials",
        ("frame_density", "frame_density_kg_m3"),
    ),
    **_pair(
        "a recorded response beside the response to code a of a Golay pair, a label",
        "room",
        ("recorded", "recorded_a"),
    ),
    **_pair(
        "the probability density p2(v) of the DIN 45672-2 amplitude "
        "distribution, in 1/(mm/s), beside the mass density of a rod in kg/m3",
        "vibration",
        ("density", "density_per_mm_s"),
    ),
    **_pair(
        "the velocity power spectral density in (mm/s)2/Hz the railway "
        "functions read, beside the voltage density in V2/Hz of the analyser "
        "that velocity_psd_from_voltage converts from",
        "vibration",
        ("psd", "psd_v2_per_hz"),
    ),
    **_pair(
        "the airspeed of the rotorcraft database, in whatever unit its "
        "hemispheres are tabulated in, beside the airspeed the track "
        "kinematics derive in m/s",
        "aircraft",
        ("airspeed", "airspeed_m_s"),
    ),
    **_pair(
        "Delta(Rw + C), the C spectrum adaptation term of ISO 717-1, not degrees "
        "Celsius",
        "building",
        ("delta_rw", "delta_rw_c"),
    ),
    **_pair(_FREQUENCY_HZ, "electroacoustics", ("frequency", "frequency_hz")),
    **_pair(
        "the MicrophoneNoise record of Clause 17 beside the duration of a "
        "stretch of noise in a combined test signal",
        "electroacoustics",
        ("noise", "noise_s"),
    ),
    **_pair(
        "a time signal x(t) or y(t), or the dimensionless 2ka of a piston, "
        "beside the coordinates of a point in metres",
        "electroacoustics",
        ("x", "x_m"),
        ("y", "y_m"),
    ),
    **_pair(
        "the PlantMeasurementContour record beside the vertices it is built "
        "from, in metres",
        "emission",
        ("contour", "contour_m"),
    ),
    **_pair(_FREQUENCY_HZ, "emission", ("frequency", "frequency_hz")),
    **_pair(
        "the number N of measurement positions beside their coordinates",
        "emission",
        ("positions", "positions_m"),
    ),
    **_pair(
        _PATH_AND_RATE,
        "environment",
        ("attenuation", "attenuation_db_per_m"),
        ("air_attenuation", "air_attenuation_db_per_km"),
    ),
    **_pair(_FREQUENCY_HZ, "environment", ("frequency", "frequency_hz")),
    **_pair(
        "the label 1 or 2 that picks a CNOSSOS-EU source line beside a height "
        "in metres",
        "environment",
        ("height", "height_m"),
    ),
    **_pair(
        "a roughness limit in dB per wavelength beside a decay-rate limit in dB/m",
        "environment",
        ("limit_db", "limit_db_per_m"),
    ),
    **_pair(
        'the evaluation period "day", "evening" or "night", a label, beside '
        "the durations of the periods in hours",
        "environment",
        ("period", "period_hours"),
    ),
    **_pair(
        "a roughness spectrum, a roughness class or the level L_R,TOT in dB, "
        "beside a raw roughness record in micrometres",
        "environment",
        ("roughness", "roughness_um"),
    ),
    **_pair(_FREQUENCY_HZ, "hearing", ("frequency", "frequency_hz")),
    **_pair(
        "the absorption coefficient alpha_s of ISO 354; " + _SUBSCRIPT,
        "materials",
        ("alpha", "alpha_s"),
    ),
    **_pair(
        "the complex shear modulus the Biot model takes, beside the real "
        "modulus a catalogue row holds in the unit the catalogue holds every "
        "row in",
        "materials",
        ("shear_modulus", "shear_modulus_pa"),
    ),
    **_pair(_FREQUENCY_HZ, "metrology", ("frequency", "frequency_hz")),
    **_pair(
        "the phase record of a comparison calibration, an object, beside the "
        "phase of a sensitivity in degrees",
        "metrology",
        ("phase", "phase_deg"),
    ),
    **_pair(_FREQUENCY_HZ, "room", ("frequency", "frequency_hz")),
    **_pair(
        "the number N of source and receiver positions beside the distances "
        "of the microphones in metres",
        "room",
        ("positions", "positions_m"),
    ),
    **_pair(
        "the sound-speed map c beside the S-wave speed c_s of an elastic "
        "cell; " + _SUBSCRIPT,
        "simulation",
        ("c", "c_s"),
    ),
    **_pair(
        "the volume-absorption loss in dB, or the name of the model applied, "
        "beside the absorption rate in dB/km",
        "underwater",
        ("absorption", "absorption_db_per_km"),
    ),
    **_pair(
        _KHZ_FORMULAS,
        "underwater",
        ("frequencies", "frequencies_hz"),
        ("frequency", "frequency_hz"),
        ("ranges", "ranges_m"),
    ),
    **_pair(
        "the acceleration, displacement and velocity ratings AR, DR and VR "
        "that index the tables of ISO 20816-9, or an acceleration record a "
        "Signal carries with its own calibration, beside bare arrays in their "
        "units",
        "vibration",
        ("acceleration", "acceleration_m_s2"),
        ("displacement", "displacement_um"),
        ("velocity", "velocity_mm_s"),
    ),
    **_pair(
        "a dimensionless coefficient of a building code beside the k of a "
        "peak-velocity law in mm/s",
        "vibration",
        ("coefficient", "coefficient_mm_s"),
    ),
    **_pair(
        'the duration class "short_term" or "long_term" of DIN 4150-3, a '
        "label, beside durations in seconds and the working days of a "
        "construction site",
        "vibration",
        ("duration", "duration_days"),
        ("duration", "duration_s"),
    ),
    **_pair(_FREQUENCY_HZ, "vibration", ("frequency", "frequency_hz")),
    **_pair(
        "the KB_FTr of a railway assessment spread one class below or above, "
        "beside the limits of a meter verification in per cent",
        "vibration",
        ("lower", "lower_percent"),
        ("upper", "upper_percent"),
    ),
}


def _subpackage(module: str) -> str:
    """The first-level package a module belongs to, the root for a private one."""
    parts = module.split(".")
    if len(parts) < 2 or not _is_public(parts[1]):
        return parts[0]
    return ".".join(parts[:2])


def _package_of(parameter: Parameter) -> str:
    """The subpackage a caller meets a name in.

    That is the subpackage of the module that defines it, or, for a callable
    defined in a private module (a ``_plot`` renderer published by
    ``building``), of the public module that publishes it.
    """
    home = _subpackage(parameter.module)
    if home == "phonometry" and parameter.publisher:
        return _subpackage(parameter.publisher)
    return home


#: Every unit the pair rule reads, single letters included.
_PAIR_UNITS = frozenset((*UNITS, *RATE_UNITS, *PER_HOUR_UNITS, *PAIR_ONLY_UNITS))

#: The words a compound unit is written in, ``per`` and the decibel aside:
#: ``_kg_m3`` is ``kg`` and ``m3``, ``_pa_s_m2`` is ``pa``, ``s`` and ``m2``.
_UNIT_WORDS = frozenset(
    word for unit in _PAIR_UNITS for word in unit.strip("_").split("_")
) - {"per", "db"}


def is_unit_tail(tail: str) -> bool:
    """Whether what follows a name and an underscore is a unit.

    One word is a unit when :data:`UNITS` or :data:`PAIR_ONLY_UNITS` lists it,
    so the ``j`` of an element ``area_j`` is not one. Several words are a
    unit when each is a word of a listed unit, ``per`` stands between two of
    them and ``db`` only opens a rate (``db_per_100m``): a compound the tree
    has not written yet is read like the ones it has, and a level's bare
    ``_db`` is not a unit (:data:`DIMENSIONLESS`).
    """
    words = tail.split("_")
    if len(words) == 1:
        return f"_{tail}" in _PAIR_UNITS
    for i, word in enumerate(words):
        if word == "db":
            if i or words[1] != "per":
                return False
        elif word == "per":
            if i == len(words) - 1 or words[i + 1] in {"per", "db"}:
                return False
        elif word not in _UNIT_WORDS:
            return False
    return True


def bare_and_suffixed(
    parameters: Iterable[Parameter] | None = None,
) -> tuple[list[tuple[str, str, str, str, str]], list[tuple[str, str, str]]]:
    """Names written both bare and with a unit inside one subpackage, and stale keys.

    The three unit rules hold a name to its unit one name at a time, so they
    cannot see that ``volume`` and ``volume_m3`` sit in the same package, or
    a ``density`` beside a ``density_kg_m3``. A caller who has typed one has
    every reason to expect the other to mean the same thing in the same unit,
    and the pair says nothing about whether it does. A name is paired with
    every shorter public name of its package that it extends by a unit
    (:func:`is_unit_tail`), compound units included, and each pair is
    reported with the place of the bare spelling and of the suffixed one.
    """
    names: dict[str, dict[str, str]] = {}
    for parameter in public_parameters() if parameters is None else parameters:
        bucket = names.setdefault(_package_of(parameter), {})
        owner = f"{parameter.qualname}({parameter.name})"
        bucket.setdefault(parameter.name, f"{owner}  <- {parameter.where}")
    found: list[tuple[str, str, str, str, str]] = []
    used: set[tuple[str, str, str]] = set()
    for package, spelled in sorted(names.items()):
        for name in sorted(spelled):
            for cut, char in enumerate(name):
                if char != "_" or not cut:
                    continue
                bare, tail = name[:cut], name[cut + 1 :]
                if bare not in spelled or not tail or not is_unit_tail(tail.lower()):
                    continue
                key = (package, bare, name)
                if key in PAIR_EXEMPT:
                    used.add(key)
                    continue
                found.append((package, bare, name, spelled[bare], spelled[name]))
    return found, [k for k in PAIR_EXEMPT if k not in used]


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
        if constant_declares_its_unit(entry.name, entry.module):
            continue
        key = (entry.module, entry.name)
        if key in CONSTANT_EXEMPT:
            used.add(key)
            continue
        found.append(entry)
    return found, [k for k in CONSTANT_EXEMPT if k not in used]


def _class_methods(cls: type) -> Iterator[tuple[str, object]]:
    """Each public method a class answers to, named by the class that defines it.

    The class's own namespace is not enough: a method a published class
    inherits from a base no module exports (``_DrawableLayer.plot``,
    ``ScatteringBands.scattering_coefficient``) is called on the published
    class all the same. The method resolution order is walked, an attribute
    is taken from the first class that defines it, as Python resolves it, and
    only the classes of this package are read. Keying by the defining class
    reports a method shared by many published classes once.
    """
    resolved: set[str] = set()
    for klass in inspect.getmro(cls):
        ours = (getattr(klass, "__module__", "") or "").startswith("phonometry")
        for attribute, member in vars(klass).items():
            if attribute in resolved:
                continue
            resolved.add(attribute)
            if (
                ours
                and _is_public(attribute)
                and (
                    inspect.isfunction(member)
                    or isinstance(member, (classmethod, staticmethod))
                )
            ):
                yield f"{klass.__qualname__}.{attribute}", member


def _public_functions() -> Iterator[PublicName]:
    """Every public function and method a caller calls by name, once each.

    A property is left out: it reads like a field, and a field keeps the unit
    of what it holds. A classmethod or a staticmethod is a function by the
    name it is called with. A method is found on every published class that
    answers to it, inherited ones included (:func:`_class_methods`).
    """
    seen: set[tuple[str, str]] = set()
    for _, module in public_modules():
        for exported in getattr(module, "__all__", ()):
            obj = getattr(module, exported, None)
            if inspect.isfunction(obj):
                callables: list[tuple[str, object]] = [(exported, obj)]
            elif inspect.isclass(obj):
                callables = list(_class_methods(obj))
            else:
                continue
            for qualname, member in callables:
                target = getattr(member, "__func__", member)
                home = getattr(target, "__module__", "") or ""
                if (home, qualname) in seen:
                    continue
                seen.add((home, qualname))
                yield PublicName(
                    home, qualname, qualname.rpartition(".")[2], _where(target)
                )


def unit_named_functions() -> tuple[list[PublicName], list[tuple[str, str]]]:
    """The public functions named with a unit their quantity never changes, and stale keys."""
    found: list[PublicName] = []
    used: set[tuple[str, str]] = set()
    for entry in _public_functions():
        if not entry.name.lower().endswith(FUNCTION_REJECTED_UNITS):
            continue
        key = (entry.module, entry.qualname)
        if key in FUNCTION_UNIT_EXEMPT:
            used.add(key)
            continue
        found.append(entry)
    return found, [k for k in FUNCTION_UNIT_EXEMPT if k not in used]


#: Names whose head noun says decibel and that keep ``_db``, keyed by
#: ``(module, qualified name, name)``, with the reason. The suffix stays where
#: the name holds something else under the word: the same quantity in a
#: second form, or the uncertainty of the quantity it is named for.
_IN_TWO_FORMS = (
    "the same correction as the complex factor the record holds under the bare "
    "name, so the suffix says which of the two this returns"
)
_A_BUDGET_COMPONENT = (
    "a component of an uncertainty budget named for the input it is the "
    "uncertainty of (ISO 4869-3 Table B.1): it holds a standard uncertainty in "
    "decibels, not the level"
)


def _level_exempt(
    reason: str, module: str, *owners: tuple[str, str]
) -> dict[tuple[str, str, str], str]:
    """One reason for several ``(owner, name)`` pairs of one module."""
    return {(f"phonometry.{module}", owner, name): reason for owner, name in owners}


LEVEL_SUFFIX_EXEMPT: dict[tuple[str, str, str], str] = {
    **_level_exempt(
        _IN_TWO_FORMS,
        "metrology.reciprocity_coupler",
        ("CouplerTransferImpedance", "capillary_correction_db"),
    ),
    **_level_exempt(
        _A_BUDGET_COMPONENT,
        "hearing._earmuff_insertion_loss",
        ("InsertionLossUncertaintyBudget", "open_level_db"),
        ("InsertionLossUncertaintyBudget", "occluded_level_db"),
    ),
}


def decibel_suffixed() -> tuple[
    list[tuple[PublicName, str]], list[tuple[str, str, str]]
]:
    """The public names of a level or a level difference that carry ``_db``, and stale keys.

    Every name a caller writes is read: the parameters, fields and
    properties, the methods and functions, and the published constants. A
    level and a level difference are in decibels by definition, so the head
    noun already says the unit (:func:`decibel_head`); a name whose head noun
    does not say decibel (a tolerance, a margin, an uncertainty, a deviation,
    a step, a slope, a rate) keeps its ``_db``.
    """
    found: list[tuple[PublicName, str]] = []
    used: set[tuple[str, str, str]] = set()
    entries = list(public_names())
    known = {(e.module, e.qualname, e.name) for e in entries}
    for entry in _public_functions():
        owner, _, name = entry.qualname.rpartition(".")
        if (entry.module, owner, name) not in known:
            entries.append(PublicName(entry.module, owner, name, entry.where))
    seen: set[tuple[str, str, str]] = set()
    for entry in entries:
        key = (entry.module, entry.qualname, entry.name)
        if key in seen:
            continue
        seen.add(key)
        suffix = decibel_suffix(entry.name, entry.module)
        if suffix is None:
            continue
        if key in LEVEL_SUFFIX_EXEMPT:
            used.add(key)
            continue
        found.append((entry, suffix))
    return found, [k for k in LEVEL_SUFFIX_EXEMPT if k not in used]


def _report_levels(levels: list[tuple[PublicName, str]]) -> None:
    """Print the level rule's findings."""
    if not levels:
        return
    print("::error::a level or a level difference carries a unit suffix")
    print(f"{len(levels)} name(s) say decibel twice, by the head noun and by _db:")
    for entry, suffix in sorted(levels):
        dotted = ".".join(p for p in (entry.qualname, entry.name) if p)
        wanted = entry.name[: -len(suffix)] + suffix[3:]
        print(f"  {dotted} -> {wanted}  <- {entry.where}")
    print(
        "  -> a level and a level difference (a loss, an insulation, an "
        "isolation, a reduction, a rejection, a difference, an improvement, "
        "an attenuation, a correction, an adjustment, an index, an "
        "emergence, an adaptation term, a shift or an increase of a named "
        "level, or the symbol of one) are in decibels by "
        "definition, so the name carries no _db; a name whose head noun does "
        "not say decibel (tolerance, margin, uncertainty, deviation, step, "
        "slope, rate) keeps it. A name that holds something else under the "
        "word goes in LEVEL_SUFFIX_EXEMPT at the top of "
        "scripts/check_parameter_units.py with its reason."
    )


def _report_functions(functions: list[PublicName]) -> None:
    """Print the function-name rule's findings."""
    if not functions:
        return
    print("::error::a public function is named with a unit its quantity never changes")
    print(
        f"{len(functions)} function(s) end in {' or '.join(FUNCTION_REJECTED_UNITS)}:"
    )
    for entry in sorted(functions):
        wanted = re.sub(r"_(?:db|hz)$", "", entry.qualname, flags=re.IGNORECASE)
        print(f"  {entry.qualname} -> {wanted}  <- {entry.where}")
    print(
        "  -> a function is named for the quantity it returns; a level, a "
        "correction, a difference, an index or a tolerance is in decibels and "
        "a frequency in hertz, so the name carries neither. Where the bare name "
        "collides or claims more than the function computes, take the family's "
        "prefix (silencer_sound_power_level). A method that reads a row's "
        "columns or returns a quantity the record also holds in another unit "
        "goes in FUNCTION_UNIT_EXEMPT at the top of "
        "scripts/check_parameter_units.py with its reason."
    )


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


def _report_closing(
    rates: list[Parameter],
    pressures: list[PublicName],
    pairs: list[tuple[str, str, str, str, str]],
) -> None:
    """Print the findings of the rate, pressure-stem and pair rules."""
    if rates:
        print("::error::an attenuation or absorption rate hides its distance")
        print(f"{len(rates)} rate(s) documented per distance end in no rate unit:")
        for parameter in sorted(rates):
            print(f"  {parameter.qualname}({parameter.name})  <- {parameter.where}")
        print(
            "  -> end the name in "
            + ", ".join(RATE_UNITS)
            + "; a name that is not a rate goes in RATE_EXEMPT with its reason."
        )
    if pressures:
        print("::error::the pressure of the medium is called by another stem")
        print(f"{len(pressures)} name(s) use a stem other than static_pressure_:")
        for entry in sorted(pressures):
            dotted = ".".join(p for p in (entry.qualname, entry.name) if p)
            print(f"  {dotted}  <- {entry.where}")
        print(
            "  -> static_pressure_pa or static_pressure_kpa, as the clause "
            "writes it; atmospheric_pressure_ only for the outside atmosphere "
            "beside a stream pressure, listed in ATMOSPHERIC_ADMITTED."
        )
    if pairs:
        print("::error::one name is public both bare and with its unit")
        print(f"{len(pairs)} pair(s) inside one subpackage:")
        for package, bare, suffixed, at_bare, at_suffixed in pairs:
            print(f"  {package}: {bare} / {suffixed}")
            print(f"      {at_bare}")
            print(f"      {at_suffixed}")
        print(
            "  -> keep the unit where a second unit competes for the word and "
            "drop it where the word only ever had one; two different "
            "quantities under one word go in PAIR_EXEMPT with the reason."
        )


def main() -> int:
    """Report every public name whose unit is hidden or spelled the retired way."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    parameters = list(public_parameters())
    unnamed, loose, stale = offenders(parameters)
    misspellings, stale_spellings = misspelled(parameters)
    constants, stale_constants = unitless_constants()
    rates, stale_rates = misnamed_rates(parameters)
    pressures, stale_pressures = ambient_pressure_names(parameters)
    pairs, stale_pairs = bare_and_suffixed(parameters)
    functions, stale_functions = unit_named_functions()
    levels, stale_levels = decibel_suffixed()
    stale_keys = [
        *stale,
        *stale_spellings,
        *stale_constants,
        *stale_rates,
        *stale_pressures,
        *stale_pairs,
        *stale_functions,
        *stale_levels,
    ]
    if not (
        unnamed
        or loose
        or misspellings
        or constants
        or rates
        or pressures
        or pairs
        or functions
        or levels
        or stale_keys
    ):
        print(
            "Every public parameter and constant under the rule names its unit, "
            "in the one spelling the tree uses, and asks for it by name; every "
            "public function is named for what it returns."
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
    _report_closing(rates, pressures, pairs)
    _report_functions(functions)
    _report_levels(levels)
    for key in stale_keys:
        print(
            f"::error::an exemption at the top of scripts/check_parameter_units.py "
            f"lists {key}, which no longer exists or no longer needs it"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
