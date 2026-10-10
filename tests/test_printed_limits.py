#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A verdict reads the limit its standard prints; it is not handed one.

Verdict classes used to take the standard's limit as a constructor field: the
ISO 11957 flatness limit, the ISO 10846 level differences, the Table 3 spread
of ISO 3743-1 and some thirty more. A verdict built by hand, or rewritten with
:func:`dataclasses.replace`, could then judge a measurement against any number
and still print the standard's name over the result. Every one of those limits
is now a read-only property derived from the fields that select it (the bands,
the condition, the class, the source, the room), and this module keeps the
class closed.

A verdict class is a dataclass that carries a verdict, as a field or as a
property: ``passes``, ``satisfied``, ``acceptable``, ``applicable``,
``holds``, ``complies``, ``overall_class``, ``zone``, a name that starts with
``within``, ``exceeds`` or ``meets``, one that ends in ``_met`` or one that
says something is ``qualified``; or a class whose name says it judges
(``...Check``, ``...Verification``, ``...Verdict``, ``...Assessment``,
``...Requirement``, ``...Applicability``). None of its fields may be named
like a limit (a limit, a tolerance, a criterion, a requirement, a guide value,
a threshold, a nominal or printed value, a minimum or a maximum, a lower or an
upper bound, an action value, an offset) unless it is listed below with the
reason it stays a field: a limit the standard leaves to the user, or a value
that only shares the name (a measured maximum, a verdict flag, the text of a
requirement). A new field of that kind fails here until it is either derived
from the standard or justified.

What the guard cannot see is a verdict that names neither itself nor its
verdict in any of those ways, and a limit field named like none of them; the
classes converted so far are pinned one by one in :data:`_DERIVED_LIMITS`.

The second half closes the verdict itself. A result's function used to work
out ``passes``, ``complies``, the ``*_met`` and ``*_ok`` flags, the advisories
and the class of each band, and store them beside the readings they came
from, so a result built by hand could hold readings that fail and a flag that
says they pass. No public result outside the private packages may store a
field that is a verdict, found two ways: by the class alone, a field annotated
``bool`` (a bool, an optional bool, an array annotated as one) or named like a
verdict flag; and by the source, a field some function of the package fills
with an ordering comparison, a combination of them, or a label one chose (a
per-band mask annotated ``np.ndarray``, a category held as a string, an enum
member), traced by :mod:`stored_verdicts`. A field either way fails unless
:data:`_STATED_FLAGS` lists it with the reason it stays: an option the caller
states, a branch the caller chose by what they gave, a fact of an input the
result does not hold, a property of the file read, the convergence of an
iterative solver, a column of a published table row, a row a verdict's own
property builds, the yes/no observations a tester records, or the ISO 8297
requirement record. A regime or a classification the function reached by
comparing values the result holds, or could hold, with a constant or a
printed threshold (the over-critical hammer, the cavitating valve, the
screened section, the identified tone) is a verdict like any other and stays
out of that list. The verdicts and regimes turned into read-only properties
are pinned class by class in :data:`_DERIVED_FLAGS`.

What this half cannot see is a verdict stored as a number (a margin, a
rating) that names itself like none of those, a verdict handed to the
constructor through ``**kwargs``, :func:`dataclasses.replace` or
``type(self)(...)``, and a flag kept as a key of a row dictionary; the rows a
verdict reads are held read-only, so a write cannot move it after the fact.
"""

from __future__ import annotations

import dataclasses
import functools
import importlib
import pkgutil
import re
from typing import TYPE_CHECKING

import pytest
import stored_verdicts

import phonometry

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

#: A field name that holds a limit, a tolerance, a criterion or a requirement.
_LIMIT_NAME = re.compile(
    r"(^|_)(limit|limits|tolerance|tolerances|criterion|criteria|required|"
    r"requirement|allowable|allowed|guide|guideline|threshold|nominal|printed|"
    r"minimum|maximum|min|max|lower|upper|action_value|offset)(_|$)"
)

#: An attribute, field or property, that holds a verdict.
_VERDICT_ATTRIBUTE = re.compile(
    r"^(passes|satisfied|all_satisfied|acceptable|applicable|holds|complies|"
    r"overall_class|zone|prominent|within(_\w+)?|exceeds(_\w+)?|meets(_\w+)?|"
    r"\w+_met|\w*qualified\w*)$"
)
_VERDICT_NAME = re.compile(
    r"(Check|Verification|Verdict|Assessment|Requirement|Applicability)$"
)

#: Limit fields the standard leaves to the user, each with the reason it stays
#: a field.
_CHOSEN_LIMITS = {
    "phonometry.building.measurement.joint_insulation.JointGapSeriesCheck."
    "minimum_gap_mm": (
        "ISO 10140-1 J.4: the minimal gap width the product's series declares"
    ),
    "phonometry.building.measurement.joint_insulation.JointGapSeriesCheck."
    "nominal_gap_mm": (
        "ISO 10140-1 J.4: the nominal gap width the product's series declares"
    ),
    "phonometry.building.measurement.lab_improvement.LiningCuringCheck."
    "required_curing_days": (
        "ISO 10140-1 G.4: two weeks unless the product specification sets another"
    ),
    "phonometry.building.measurement.service_equipment.BackgroundDurationCheck."
    "tolerance_s": "ISO/DIS 16032 7.6 says approximately and prints no tolerance",
    "phonometry.building.regulation.spain.DbHrCheck.requirement": (
        "the CTE DB-HR requirement the user looked up for the building"
    ),
    "phonometry.building.regulation.spain.DbHrRequirement.limit": (
        "the requirement object is the looked-up limit itself"
    ),
    "phonometry.electroacoustics.induction_loop.LoopRequirement.lower_db": (
        "one row of a generic requirement record, its limit mixing printed tolerances"
        " with the specified field strength and the measured noise"
    ),
    "phonometry.electroacoustics.induction_loop.LoopRequirement.upper_db": (
        "one row of a generic requirement record"
    ),
    "phonometry.emission.sound_power_plant.PlantRequirement.limit": (
        "one row of a generic requirement record, its limit mixing printed factors "
        "with the plant's own geometry"
    ),
    "phonometry.emission.sound_power_plant.PlantRequirement.tolerance": (
        "one row of a generic requirement record"
    ),
    "phonometry.emission.sound_power_special_room.SpecialRoomReverberationCheck."
    "nominal_reverberation_time_s": (
        "ISO 3743-2 6.2: the room's T_nom, supplied or centred on the measured values"
    ),
    "phonometry.emission.sound_power_special_room.SpecialRoomSoundPowerResult."
    "nominal_reverberation_time_s": (
        "ISO 3743-2 6.2: the room's T_nom, supplied or centred on the measured values"
    ),
    "phonometry.emission.sound_power_intensity.PrecisionCriteria."
    "repeatability_limit_db": (
        "ISO 9614-3 C.1: the s the caller sets in place of Table 1, which is read "
        "from the frequencies otherwise"
    ),
    "phonometry.environment.assessment.spain.ActivityAssessment.limits": (
        "RD 1367/2007 lets the area type and the municipal ordinance set them"
    ),
    "phonometry.environment.assessment.spain.PeriodAssessment.limit": (
        "RD 1367/2007 lets the area type and the municipal ordinance set them"
    ),
    "phonometry.environment.propagation.software_quality.CalculationVerification."
    "lower_limits_db": "ISO 17534-1: the limits of the test case the user runs",
    "phonometry.environment.propagation.software_quality.CalculationVerification."
    "upper_limits_db": "ISO 17534-1: the limits of the test case the user runs",
    "phonometry.environment.sources.rolling_stock_noise.ReferenceTrackCheck."
    "decay_limits_db_per_m": "ISO 3095:2013 6.2.6 prints default limits",
    "phonometry.environment.sources.rolling_stock_noise.ReferenceTrackCheck."
    "roughness_limit_db": "ISO 3095:2013 6.2.5 prints a default limit",
    "phonometry.environment.sources.rolling_stock_noise.SmallRoughnessDeviation."
    "limit_db": "ISO 3095:2013 6.2.5 prints a default limit",
    "phonometry.hearing.audiometry.AmbientNoiseCheck.allowed_threshold_shift_db": (
        "ISO 8253-1 Table 2 NOTE: the tester accepts a shift of 2 dB or 5 dB"
    ),
    "phonometry.metrology.conformance.ConformanceVerification.lower_limit": (
        "IEC TC 29 conformance rule: the limit of the requirement judged"
    ),
    "phonometry.metrology.conformance.ConformanceVerification.max_uncertainty": (
        "IEC TC 29 conformance rule: the maximum of the requirement judged"
    ),
    "phonometry.metrology.conformance.ConformanceVerification.upper_limit": (
        "IEC TC 29 conformance rule: the limit of the requirement judged"
    ),
    "phonometry.metrology.sound_calibrator.SoundCalibratorVerification."
    "nominal_frequency_hz": "IEC 60942: the calibrator's nominal frequency, as stated",
    "phonometry.noise_control.duct_path.DuctPathResult.criterion": (
        "the NC or RC family the user designs to, a name and not a value"
    ),
    "phonometry.noise_control.room_to_room.RoomToRoomResult.criterion": (
        "the NC or RC family the user designs to, a name and not a value"
    ),
    "phonometry.vibration.immission.coupling.MountingCheck.upper_frequency_hz": (
        "DIN 45669-2: the highest frequency the user's measurement has to carry"
    ),
    "phonometry.vibration.immission.people.PeopleAssessment.guide": (
        "DIN 4150-2: the guide-value row of the area the user assesses"
    ),
    "phonometry.vibration.immission.train_categories.RailwayChange.guide": (
        "DIN 4150-2: the guide-value row of the area the user assesses"
    ),
    "phonometry.vibration.structural.impact_mobility.CoherenceCheck.minimum_coherence": (
        "ISO 7626-5 prints no figure for a high coherence; the default is the user's"
    ),
    "phonometry.vibration.structural.impact_mobility.CoherenceCheck.minimum_records": (
        "ISO 7626-5 asks five to ten impacts; where in that range is the user's"
    ),
    "phonometry.vibration.structural.impact_mobility.DoubleHitCheck.threshold_ratio": (
        "ISO 7626-5 6.4 prints no threshold; the library's default is the user's"
    ),
    "phonometry.vibration.structural.impact_mobility.ForceSpectrumCheck.max_drop_db": (
        "ISO 7626-5 prints no drop for the force spectrum; the default is the user's"
    ),
}

#: Fields named like a limit that hold no limit: a measured or computed value,
#: a verdict flag, the words of a requirement.
_NOT_LIMITS = {
    "phonometry.building.measurement.service_equipment.MeasurementDisturbanceCheck."
    "maximum_levels_db": "the measured maximum levels",
    "phonometry.building.measurement.service_equipment.VaryingBackgroundCheck."
    "background_maximum_db": "the measured maximum of the background",
    "phonometry.emission.free_field_qualification.SourceDirectionalityResult."
    "maximum_negative_deviation_db": "the measured largest deviation",
    "phonometry.emission.free_field_qualification.SourceDirectionalityResult."
    "maximum_positive_deviation_db": "the measured largest deviation",
    "phonometry.emission.sound_power_hard_walled.HardWalledRoomCheck."
    "max_absorption_coefficient": "the largest coefficient of the room's surfaces",
    "phonometry.environment.sources.rolling_stock_noise.TrackCondition.requirement": (
        "the requirement in words, not a value"
    ),
    "phonometry.environment.sources.statistical_pass_by.PassByRegression."
    "max_levels_db": "the measured maximum level of each pass-by",
    "phonometry.metrology.sound_level_meter.SoundLevelMeterPeriodicRequirement."
    "over_maximum_by_correction_data": "the names of the results it concerns",
    "phonometry.noise_control.cabin_insulation.SourcePositionCheck."
    "max_octave_spread_db": "the measured spread",
    "phonometry.vibration.immission.people.RailwayAssessment.lower": (
        "KB_FTr with the spread taken off, a result"
    ),
    "phonometry.vibration.immission.people.RailwayAssessment.upper": (
        "KB_FTr with the spread added, a result"
    ),
}

#: The printed limits the sweep turned into read-only properties, by class,
#: with the verdicts that were stored beside them.
_DERIVED_LIMITS = {
    "phonometry.building.measurement.heavy_impact.HeavyImpactSourceCheck": (
        "nominal",
        "tolerance",
    ),
    "phonometry.building.measurement.service_equipment.PositionSpreadCheck": (
        "limit_db",
        "stage",
        "spread_db",
        "action",
        "next_positions",
        "corner_standard_deviation_db",
    ),
    "phonometry.electroacoustics.induction_loop_components.NeckLoopVerification": (
        "limits",
    ),
    "phonometry.electroacoustics.programme_signal.ProgrammeSignalCheck": (
        "relative_levels_db",
        "tolerance_plus_db",
        "tolerance_minus_db",
    ),
    "phonometry.emission.free_field_qualification.InverseSquareLawResult": (
        "tolerance_db",
    ),
    "phonometry.emission.free_field_qualification.SourceDirectionalityResult": (
        "tolerance_db",
    ),
    "phonometry.emission.intensity_compliance.IntensityInstrumentComplianceResult": (
        "limit_class1",
        "limit_class2",
        "spacing_offset_db",
    ),
    "phonometry.emission.reference_sound_source.ReferenceSoundSourceVerdict": (
        "repeatability_limit_db",
        "supply_limit_db",
        "adjacent_limit_db",
        "core_range_limit_db",
        "extended_range_limit_db",
        "directivity_limit_db",
    ),
    "phonometry.emission.reference_sound_source.ReferenceSourceDriftResult": (
        "limit_db",
    ),
    "phonometry.emission.sound_power_hard_walled.HardWalledRoomCheck": (
        "limit_db",
        "minimum_volume_m3",
        "box_dimension_limit_m",
        "minimum_microphone_distance_m",
    ),
    "phonometry.emission.sound_power_special_room.SpecialRoomReverberationCheck": (
        "lower_limit",
        "upper_limit",
    ),
    "phonometry.emission.sound_power_special_room.SpecialRoomSuitabilityCheck": (
        "limit_db",
    ),
    "phonometry.hearing.audiometry.AmbientNoiseCheck": (
        "limits_db",
        "table_bands_hz",
    ),
    "phonometry.hearing.earmuff_insertion_loss.FixtureIsolationCheck": ("required_db",),
    "phonometry.environment.propagation.barrier_reflection.ReflectionGridCheck": (
        "nominal_m",
        "deviations_m",
        "within",
    ),
    "phonometry.hearing.sound_field_audiometry.FreeSoundFieldCheck": (
        "axis_offset_m",
        "inverse_distance_difference_db",
    ),
    "phonometry.hearing.real_ear_attenuation.ReatSoundFieldCheck": (
        "allowable_variation_db",
    ),
    "phonometry.hearing.sound_field_audiometry.DiffuseSoundFieldCheck": (
        "allowable_variation_db",
    ),
    "phonometry.noise_control.cabin_insulation.BandFlatnessCheck": (
        "limit_db",
        "satisfied",
    ),
    "phonometry.noise_control.cabin_insulation.SourcePositionCheck": (
        "required_positions",
        "satisfied",
        "exceeds_maximum",
    ),
    "phonometry.noise_control.enclosure_insulation.TestEnvironmentApplicability": (
        "environmental_correction_limit_db",
        "background_margin_limit_db",
        "required_area_ratio",
        "applicable",
    ),
    "phonometry.psychoacoustics.quality.tonality.ToneAssessment": (
        "criterion_db",
        "prominent",
    ),
    "phonometry.underwater.bioacoustics.weighting.WeightedExposureResult": (
        "criteria",
    ),
    "phonometry.vibration.human.exposure.ExposureAssessment": (
        "action_value",
        "limit_value",
    ),
    "phonometry.vibration.human.instrumentation.PhaseVerification": (
        "tolerance_deg",
        "within_tolerance",
    ),
    "phonometry.vibration.human.instrumentation.RunningRmsDecayVerification": (
        "printed_time_s",
        "tolerance_s",
    ),
    "phonometry.vibration.human.instrumentation.WeightingVerification": (
        "within_tolerance",
    ),
    "phonometry.vibration.human.signal_burst.SignalBurstVerification": (
        "printed",
        "tolerance_percent",
        "within_tolerance",
    ),
    "phonometry.vibration.immission.coupling.MountingCheck": (
        "frequency_limit_hz",
        "peak_acceleration_limit_m_s2",
        "acceptable",
    ),
    "phonometry.vibration.immission.vibration_meter.AssessmentVelocity": (
        "guide_value_mm_s",
    ),
    "phonometry.vibration.immission.vibration_meter.VibrationMeterVerification": (
        "lower_percent",
        "upper_percent",
        "within_tolerance",
    ),
    "phonometry.vibration.structural.building_damage.DamageAssessment": (
        "guideline_mm_s",
    ),
    "phonometry.vibration.structural.mechanical_mobility.RigidMassCalibrationResult": (
        "tolerance",
        "within_tolerance",
        "passes",
    ),
    "phonometry.vibration.structural.transfer_stiffness.LevelDifferenceCheck": (
        "limit_db",
    ),
    "phonometry.vibration.structural.transfer_stiffness.OutputMassCheck": (
        "mass_limit_kg",
    ),
}


def _dataclasses() -> Iterator[type]:
    seen: set[type] = set()
    for info in pkgutil.walk_packages(phonometry.__path__, "phonometry."):
        module = importlib.import_module(info.name)
        for obj in vars(module).values():
            if (
                isinstance(obj, type)
                and dataclasses.is_dataclass(obj)
                and obj.__module__ == module.__name__
                and obj not in seen
            ):
                seen.add(obj)
                yield obj


def _is_verdict(cls: type) -> bool:
    # A field without a default is no class attribute, so the fields are read
    # beside dir(): a verdict stored as a field is the shape that most often
    # carries its limit beside it.
    names = {field.name for field in dataclasses.fields(cls)} | set(dir(cls))
    return bool(_VERDICT_NAME.search(cls.__name__)) or any(
        _VERDICT_ATTRIBUTE.match(name) for name in names
    )


def _limit_fields() -> set[str]:
    return {
        f"{cls.__module__}.{cls.__qualname__}.{field.name}"
        for cls in _dataclasses()
        if _is_verdict(cls)
        for field in dataclasses.fields(cls)
        if _LIMIT_NAME.search(field.name)
    }


def test_no_verdict_takes_a_printed_limit_at_construction() -> None:
    unexpected = sorted(_limit_fields() - set(_CHOSEN_LIMITS) - set(_NOT_LIMITS))
    assert not unexpected, (
        "These verdict fields are named like a limit: derive the printed ones "
        "from the standard as read-only properties, or list a limit the "
        "standard leaves to the user in _CHOSEN_LIMITS, or a value that only "
        f"shares the name in _NOT_LIMITS, with why: {unexpected}"
    )


def test_every_listed_field_is_still_a_field() -> None:
    listed = set(_CHOSEN_LIMITS) | set(_NOT_LIMITS)
    stale = sorted(listed - _limit_fields())
    assert not stale, f"the lists name fields that are gone: {stale}"
    assert not set(_CHOSEN_LIMITS) & set(_NOT_LIMITS)


@dataclasses.dataclass(frozen=True)
class _StoredVerdict:
    """The shape the guard has to see: a verdict stored as a field."""

    measured_db: float
    limit_db: float
    passes: bool


@dataclasses.dataclass(frozen=True)
class _QualifiedFit:
    """A fit whose verdict is a qualified radius, not a pass flag."""

    radius_m: float
    tolerance_db: float

    @property
    def maximum_qualified_radius_m(self) -> float:
        return self.radius_m


def test_the_guard_sees_a_verdict_stored_as_a_field() -> None:
    # A field without a default is no class attribute, so hasattr() alone
    # missed this shape, which is the one that keeps its limit beside it.
    assert _is_verdict(_StoredVerdict)
    assert _is_verdict(_QualifiedFit)


#: Derived names that are neither a limit nor a verdict by name: values read
#: from the fields (a spread, a stage, the bands of a table), and the one
#: printed spectrum whose name says only what it is. A class that brought one
#: back as a field is still pinned by _DERIVED_LIMITS.
_DERIVED_VALUES = frozenset(
    {
        "action",
        "corner_standard_deviation_db",
        "deviations_m",
        "inverse_distance_difference_db",
        "next_positions",
        "relative_levels_db",
        "spread_db",
        "stage",
        "table_bands_hz",
    }
)


@pytest.mark.parametrize(
    "name",
    sorted(
        {name for names in _DERIVED_LIMITS.values() for name in names} - _DERIVED_VALUES
    ),
)
def test_the_guard_reads_every_converted_name_as_a_limit_or_a_verdict(
    name: str,
) -> None:
    # Each name the sweep converted would be flagged again if it came back as
    # a field of a verdict.
    assert _LIMIT_NAME.search(name) or _VERDICT_ATTRIBUTE.match(name), name


@pytest.mark.parametrize(
    ("qualname", "names"), sorted(_DERIVED_LIMITS.items()), ids=lambda v: str(v)
)
def test_a_printed_limit_is_a_read_only_property(
    qualname: str, names: tuple[str, ...]
) -> None:
    module_name, _, class_name = qualname.rpartition(".")
    cls = getattr(importlib.import_module(module_name), class_name)
    fields = {field.name for field in dataclasses.fields(cls)}
    for name in names:
        assert name not in fields, f"{qualname}.{name} is a constructor field"
        assert isinstance(getattr(cls, name), property), f"{qualname}.{name}"


# ---------------------------------------------------------------------------
# Verdict flags: read from the values they judge, never stored beside them
# ---------------------------------------------------------------------------

#: A field name that holds a verdict flag: a pass or a fail, a met or an ok, a
#: class reached, a band admitted or refused.
_FLAG_NAME = re.compile(
    r"^(passes|satisfied|all_satisfied|acceptable|applicable|holds|complies|"
    r"overall_class|zone|prominent|significant|reliable|stable|valid|adequate|"
    r"qualifies|qualified|stateable|stationary|trend_free|upper_bound|unusable|"
    r"within(_\w+)?|exceeds(_\w+)?|meets(_\w+)?|is_\w+|needs_\w+|criterion_\d+|"
    r"\w+_ok|\w+_met|\w+_valid|\w+_pass|\w+_advisory|\w+_advised|\w+_satisfied|"
    r"\w+_measured|\w+_recommended|\w*qualified\w*)$"
)
#: A field type that holds one: a bool, an optional bool, an array of them.
_FLAG_TYPE = re.compile(r"\bbool\b|\bbool_\b")
#: Packages whose dataclasses are rendering and validation helpers, not results.
_PRIVATE_PACKAGES = ("phonometry._internal", "phonometry._plot", "phonometry._report")


def _is_flag_field(field: dataclasses.Field[object]) -> bool:
    return bool(_FLAG_TYPE.search(str(field.type)) or _FLAG_NAME.match(field.name))


@functools.cache
def _traced_fields() -> frozenset[str]:
    """The fields some function of the package fills with a verdict."""
    return frozenset(stored_verdicts.verdict_fields(phonometry))


def _flag_fields() -> set[str]:
    by_class = {
        f"{cls.__module__}.{cls.__qualname__}.{field.name}"
        for cls in _dataclasses()
        if not cls.__name__.startswith("_")
        and not cls.__module__.startswith(_PRIVATE_PACKAGES)
        for field in dataclasses.fields(cls)
        if _is_flag_field(field)
    }
    return by_class | _traced_fields()


_CALLER = "an option or a statement the caller gives, not a verdict the result reaches"
_BRANCH = (
    "the branch the caller chose by what they gave (a source box to search, a "
    "ground to reflect from), compared against no limit"
)
_INPUT = (
    "a fact the caller's input carried (a Signal's calibration), read as given; "
    "the result does not hold the input it was read from"
)
_FILE = "a property of the file read (its codec, its chunks), judged against no limit"
_CONVERGENCE = (
    "whether the root find met its tolerance with a solution inside the search "
    "bounds it was given, facts of the solve the result does not keep; the "
    "third condition of the flag, an absorption above 0,999, is read from the "
    "absorption the result holds, and a result that claims convergence "
    "without it is refused"
)
_ROW = "a column of a published table row, as the table prints it"
_RECORD = "one row of a generic requirement record, beside the limit it is judged by"
_DERIVED_ROW = (
    "a row a verdict's read-only property builds from the verdict's own fields "
    "each time it is read; no verdict reads one built elsewhere"
)
_OBSERVED = (
    "the yes/no observations a tester records (an overload indicated, an "
    "indicator latched, an indication inside the manual's range), judged "
    "against no printed limit"
)

#: Boolean or flag-named fields that are no stored verdict, each with why.
_STATED_FLAGS = {
    "phonometry.aircraft.airport_noise.FlightSegmentState.ground_roll": _CALLER,
    "phonometry.aircraft.airport_noise.FlightSegmentState.landing_roll": _CALLER,
    "phonometry.aircraft.anp_fleet.AnpProfile.ground_roll": _ROW,
    "phonometry.aircraft.anp_fleet.AnpProfile.landing_roll": _ROW,
    "phonometry.broadcast.quasi_peak.QuasiPeakResult.weighted": _CALLER,
    "phonometry.building.impact_catalogue.ImpactInsulation.has_section_drawing": _ROW,
    "phonometry.building.measurement.intensity_insulation.LowFrequencyElementResult."
    "absorbing_specimen_surface": _CALLER,
    "phonometry.building.measurement.intensity_insulation.LowFrequencyIntensityResult."
    "absorbing_specimen_surface": _CALLER,
    "phonometry.building.measurement.joint_insulation.JointTestElementCheck."
    "window_or_door_gap": _CALLER,
    "phonometry.building.measurement.joint_insulation.LabJointInsulationResult."
    "limit_at_maximum": _CALLER,
    "phonometry.building.measurement.service_equipment.OperatingCondition."
    "equivalent_level": _ROW,
    "phonometry.building.measurement.service_equipment.OperatingCondition."
    "maximum_level": _ROW,
    "phonometry.building.measurement.service_equipment."
    "ServiceEquipmentPositionCheck.small_room": _CALLER,
    "phonometry.building.measurement.uncertainty.BandUncertainty.upper_limit": _CALLER,
    "phonometry.building.measurement.uncertainty.UncertainValue.one_sided": _CALLER,
    "phonometry.building.prediction.linings.LiningImprovementResult.anchors": _CALLER,
    "phonometry.electroacoustics.headphones.ProgrammeCharacteristicVoltage."
    "a_weighted": _CALLER,
    "phonometry.electroacoustics.headphones.ProgrammeCharacteristicVoltage."
    "free_field_compensated": _CALLER,
    "phonometry.electroacoustics.induction_loop.BackgroundNoiseAssessment."
    "noise_is_tonal": _CALLER,
    "phonometry.emission.free_field_qualification.FreeFieldCheck."
    "paths_in_working_area": _CALLER,
    "phonometry.emission.free_field_qualification.InverseSquareLawResult."
    "origin_fitted": _BRANCH,
    "phonometry.emission.reference_sound_source.ReferenceSoundSourceVerdict."
    "reverberation_rooms_only": _CALLER,
    "phonometry.emission.sound_power_high_frequency.HighFrequencySoundPowerResult."
    "tonal": _CALLER,
    "phonometry.emission.sound_power_plant.PlantRequirement.advisory": _RECORD,
    "phonometry.emission.sound_power_plant.PlantRequirement.holds": _RECORD,
    "phonometry.emission.sound_power_special_room.SpecialRoomReverberationCheck."
    "centred": _CALLER,
    "phonometry.emission.turbine_noise.TurbineNoiseDeclaration.tonal": _CALLER,
    "phonometry.environment.assessment.soundscape.QuestionnaireScale.continuous": _ROW,
    "phonometry.environment.assessment.soundscape_binaural.BinauralParameter."
    "average_allowed": _ROW,
    "phonometry.environment.assessment.spain.ActivityAssessment.new_activity": _CALLER,
    "phonometry.environment.assessment.spain.PeriodAssessment.new_activity": _CALLER,
    "phonometry.environment.assessment.wind_turbine_modulation.ModulationBlock."
    "excluded": _CALLER,
    "phonometry.environment.assessment.wind_turbine_receptor.LowFrequencyLevel."
    "a_weighted": _CALLER,
    "phonometry.environment.propagation.ground_barriers.BarrierInsertionLoss."
    "ground": _BRANCH,
    "phonometry.environment.propagation.outdoor_propagation.Barrier."
    "ground_reflections_by_image": _CALLER,
    "phonometry.environment.propagation.outdoor_propagation.Barrier.lateral": _CALLER,
    "phonometry.environment.propagation.outdoor_propagation.Barrier."
    "line_of_sight_clear": _CALLER,
    "phonometry.environment.sources.cnossos_rail.RollingStock.tram": _ROW,
    "phonometry.environment.sources.rolling_stock_noise.TrackCondition.clause": (
        _DERIVED_ROW
    ),
    "phonometry.environment.sources.rolling_stock_noise.TrackCondition.holds": (
        _DERIVED_ROW
    ),
    "phonometry.filters.core.BlockProcessing.stateful": _CALLER,
    "phonometry.filters.core.BlockProcessing.steady_ic": _CALLER,
    "phonometry.filters.core.FilterDesign.resample": _CALLER,
    "phonometry.filters.core.LevelCalibration.dbfs": _CALLER,
    "phonometry.filters.core.ResponsePlot.show": _CALLER,
    "phonometry.filters.periodic_tests.FilterPeriodicVerification."
    "pattern_approval_public": _CALLER,
    "phonometry.filters.weighting.TimeWeightedEnvelope.calibrated": _INPUT,
    "phonometry.hearing.audiometry.AscendingThresholdResult.shortened": _CALLER,
    "phonometry.io._chunks.WavChunks.has_ixml": _FILE,
    "phonometry.io._signal.SignalOrigin.lossy": _FILE,
    "phonometry.io._wav.AudioFileInfo.has_ixml": _FILE,
    "phonometry.io._wav.AudioFileInfo.lossy": _FILE,
    "phonometry.materials.absorbers.slow_sound.CriticalCouplingResult.converged": (
        _CONVERGENCE
    ),
    "phonometry.metrology.reciprocity_coupler.CouplerCheck.in_air": _CALLER,
    "phonometry.metrology.sound_calibrator.CalibratorTableRow.includes_lower": _ROW,
    "phonometry.metrology.sound_calibrator.CalibratorTableRow.includes_upper": _ROW,
    "phonometry.metrology.sound_level_meter.MaxUncertaintyRow.includes_lower": _ROW,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterFeatures."
    "c_weighted_peak": _CALLER,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterFeatures."
    "c_weighting": _CALLER,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterFeatures."
    "f_time_weighting": _CALLER,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterFeatures."
    "s_time_weighting": _CALLER,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterFeatures."
    "sound_exposure_level": _CALLER,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterFeatures."
    "time_averaged": _CALLER,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterFeatures."
    "z_weighting": _CALLER,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterPeriodicMeasurements."
    "c_peak_overload_indicated": _CALLER,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterPeriodicMeasurements."
    "overload_latched": _CALLER,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterPeriodicRequirement."
    "checks": _OBSERVED,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterPeriodicVerification."
    "corrections_in_manual": _CALLER,
    "phonometry.metrology.sound_level_meter.SoundLevelMeterPeriodicVerification."
    "pattern_approval_public": _CALLER,
    "phonometry.noise_control.cabin_insulation.WeightedCabinInsulation.apparent": (
        _CALLER
    ),
    "phonometry.noise_control.enclosure_insulation.MethodEntry.band_values": _ROW,
    "phonometry.noise_control.enclosure_insulation.MethodEntry."
    "survey_grade_excluded": _ROW,
    "phonometry.noise_control.silencer_in_situ.InstallationCase.source_area_rule": _ROW,
    "phonometry.room.auditorium.AuditoriumQuantity.energy_averaged": _ROW,
    "phonometry.room.auditorium.AuditoriumQuantity.relative_jnd": _ROW,
    "phonometry.signals.envelope.EnvelopeResult.antialias": _CALLER,
    "phonometry.signals.envelope.EnvelopeSpectrumResult.remove_dc": _CALLER,
    "phonometry.signals.multitaper.MultitaperSpectralDensityResult.adaptive": _CALLER,
    "phonometry.simulation.elastic_fdtd.ElasticFDTDResult.obstacle_mask": _CALLER,
    "phonometry.simulation.fdtd.FDTDResult.obstacle_mask": _CALLER,
    "phonometry.speech.objective_intelligibility.STOIResult.extended": _CALLER,
    "phonometry.underwater.bioacoustics.audiograms.AudiogramParameters.in_air": _ROW,
    "phonometry.underwater.bioacoustics.audiograms.AudiogramResult.in_air": _ROW,
    "phonometry.underwater.bioacoustics.weighting.ExposureCriteria.impulsive": _ROW,
    "phonometry.underwater.bioacoustics.weighting.WeightedExposureResult."
    "impulsive": _CALLER,
    "phonometry.underwater.bioacoustics.weighting.WeightingParameters.in_air": _ROW,
    "phonometry.underwater.sonar_equation.SonarEquationResult."
    "reverberation_limited": _CALLER,
    "phonometry.vibration.human.exposure.WeightingResponse.band_limiting": _CALLER,
    "phonometry.vibration.immission.people.PeopleAssessment.rare_short_events": _CALLER,
    "phonometry.vibration.structural.building_damage.DamageAssessment."
    "massive_structure": _CALLER,
    "phonometry.vibration.structural.impact_mobility.ImpactMobilityResult."
    "driving_point": _CALLER,
    "phonometry.vibration.structural.impact_mobility.CoherenceCheck.judged": _CALLER,
    "phonometry.vibration.structural.impact_mobility.ResponseDecayCheck."
    "exponential_window": _CALLER,
    "phonometry.vibration.structural.mechanical_mobility.MobilityResult."
    "driving_point": _CALLER,
}


def test_no_result_stores_a_verdict_flag() -> None:
    unexpected = sorted(_flag_fields() - set(_STATED_FLAGS))
    assert not unexpected, (
        "These result fields hold a flag: read a verdict, a regime or a "
        "classification from the values it is reached from and the limit the "
        "standard prints, as a read-only property. List a field in _STATED_FLAGS, "
        "with why, only when it is none of those: an option or a statement the "
        "caller gives, a branch the caller chose, a fact of an input the result "
        "does not hold, a property of the file read, the convergence of an "
        "iterative solver, a column of a published table row, a row a verdict's "
        "property builds, a tester's observations or a requirement record: "
        + ", ".join(unexpected)
    )


def test_every_stated_flag_is_still_a_field() -> None:
    stale = sorted(set(_STATED_FLAGS) - _flag_fields())
    assert not stale, f"_STATED_FLAGS names fields that are gone: {stale}"


@dataclasses.dataclass(frozen=True)
class _StoredByType:
    """A verdict stored under a name the guard has no reason to suspect."""

    level_db: float
    clears_the_floor: bool


@dataclasses.dataclass(frozen=True)
class _StoredByName:
    """A per-band verdict typed loosely, as an untyped array."""

    level_db: float
    background_ok: object


def test_the_guard_sees_a_stored_flag_by_type_and_by_name() -> None:
    # A field typed bool is a flag whatever it is called, and one named like
    # a verdict is a flag whatever it is typed as.
    by_type = {
        field.name
        for field in dataclasses.fields(_StoredByType)
        if _is_flag_field(field)
    }
    by_name = {
        field.name
        for field in dataclasses.fields(_StoredByName)
        if _is_flag_field(field)
    }
    assert by_type == {"clears_the_floor"}
    assert by_name == {"background_ok"}


#: A module whose result is filled with three verdicts the class does not
#: betray: a mask annotated ``np.ndarray``, a label chosen inline and a label
#: a helper chooses. The method is chosen by an equality, which is a fact
#: checked rather than a limit judged, and the level is a reading.
_PROBE = """
from dataclasses import dataclass

import numpy as np

LIMIT_DB = 6.0
_HIGH = "high"


@dataclass(frozen=True)
class ProbeResult:
    margin_db: np.ndarray
    limited: np.ndarray
    category: str
    rating: str
    method: str
    level_db: float


def _rating(margin):
    if margin < LIMIT_DB:
        return "low"
    return _HIGH


def probe(margin_db, method):
    margin = np.asarray(margin_db)
    limited = margin < LIMIT_DB
    worst = float(margin.min())
    return ProbeResult(
        margin_db=margin,
        limited=np.asarray(limited, dtype=bool),
        category=_HIGH if worst >= LIMIT_DB else "low",
        rating=_rating(worst),
        method="fast" if method == "f" else "slow",
        level_db=worst,
    )
"""


def test_the_guard_traces_a_verdict_to_where_it_is_reached(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "phonometry_verdict_probe.py").write_text(_PROBE, encoding="utf-8")
    monkeypatch.syspath_prepend(str(tmp_path))
    found = stored_verdicts.module_verdict_fields("phonometry_verdict_probe")
    assert set(found) == {
        f"phonometry_verdict_probe.ProbeResult.{name}"
        for name in ("limited", "category", "rating")
    }


#: A module whose result is filled with four regimes chosen the ways the
#: regime results used to choose them: labels appended under an ``if``, a
#: label of a module tuple written through a mask, a mask narrowed in place,
#: and a numbered case a helper returns under an ``if``. The two values
#: written through a mask are readings, and the count is no named case.
_REGIME_PROBE = """
from dataclasses import dataclass

import numpy as np

EDGE = 3.0
REGIMES = ("near", "far")
REGIME_LOW = 1
REGIME_HIGH = 2


@dataclass(frozen=True)
class RegimeProbe:
    appended: tuple
    labelled: np.ndarray
    kept: np.ndarray
    case: int
    corrected: np.ndarray
    count: int


def _case(x):
    if x <= EDGE:
        return REGIME_LOW
    return REGIME_HIGH


def probe(margins, x):
    margins = np.asarray(margins)
    appended = []
    corrected = margins.copy()
    for m in margins:
        if m >= EDGE:
            appended.append("plain")
        else:
            appended.append("limited")
    labelled = np.full(margins.shape, REGIMES[0])
    labelled[margins >= EDGE] = REGIMES[1]
    corrected[margins < EDGE] = 0.0
    kept = np.ones(margins.size, dtype=bool)
    kept[1:] &= ~(np.diff(margins) <= EDGE)
    return RegimeProbe(
        appended=tuple(appended),
        labelled=labelled,
        kept=kept,
        case=_case(x),
        corrected=corrected,
        count=int(margins.size),
    )
"""


def test_the_guard_traces_a_regime_to_where_it_is_chosen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "phonometry_regime_probe.py").write_text(
        _REGIME_PROBE, encoding="utf-8"
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    found = stored_verdicts.module_verdict_fields("phonometry_regime_probe")
    assert set(found) == {
        f"phonometry_regime_probe.RegimeProbe.{name}"
        for name in ("appended", "labelled", "kept", "case")
    }


#: The verdicts the sweep turned into read-only properties, by class, with the
#: values read beside them that were stored too.
_DERIVED_FLAGS = {
    "phonometry.aircraft.measurement_system.AircraftSystemComplianceResult": (
        "checks",
        "passes",
    ),
    "phonometry.broadcast.quasi_peak.QuasiPeakDynamicsResult": (
        "stimuli",
        "passes",
        "worst_margin_db",
        "worst_deviation_db",
    ),
    "phonometry.building.measurement.flanking_transmission.VibrationReductionResult": (
        "bracketed",
        "single_number",
    ),
    "phonometry.building.measurement.floor_covering_improvement."
    "FloorCoveringImprovementResult": ("limited",),
    "phonometry.building.measurement.intensity_insulation.LowFrequencyElementResult": (
        "qualified",
    ),
    "phonometry.building.measurement.intensity_insulation.LowFrequencyIntensityResult": (
        "qualified",
    ),
    "phonometry.building.measurement.joint_insulation.GapWidthCheck": (
        "gap_width_mm",
        "spread_mm",
        "enough_positions",
        "uniform",
        "passes",
    ),
    "phonometry.building.measurement.joint_insulation.JointGapSeriesCheck": (
        "nominal_measured",
        "minimum_measured",
        "working_range_measured",
        "passes",
    ),
    "phonometry.building.measurement.joint_insulation.LabJointInsulationResult": (
        "regime",
    ),
    "phonometry.building.measurement.joint_insulation.JointTestElementCheck": (
        "length_ok",
        "width_ok",
        "passes",
    ),
    "phonometry.building.measurement.lab_improvement.LiningCuringCheck": (
        "cured",
        "lag_within_third",
        "passes",
    ),
    "phonometry.building.measurement.rainfall_sound.RainGeneratorVerification": (
        "rate_deviation_mm_h",
        "rate_ok",
        "drop_share",
        "drops_ok",
        "velocity_share",
        "velocities_ok",
        "passes",
    ),
    "phonometry.building.measurement.service_equipment.ServiceEquipmentBackgroundResult": (
        "difference_db",
        "regime",
        "correction_db",
        "corrected_db",
    ),
    "phonometry.building.measurement.service_equipment.ServiceEquipmentResult": (
        "standardizable",
    ),
    "phonometry.building.measurement.service_equipment.ServiceEquipmentPositionCheck": (
        "separation_m",
        "surface_distance_m",
        "source_distance_m",
        "heights_m",
        "corner_height_m",
        "corner_wall_distances_m",
        "separation_ok",
        "surface_ok",
        "source_ok",
        "height_ok",
        "corner_height_ok",
        "corner_obstacle_ok",
    ),
    "phonometry.building.prediction.resilient_layers.TappingForceResult": (
        "over_critical",
    ),
    "phonometry.building.regulation.spain.DbHrCheck": (
        "reported",
        "margin",
        "complies",
    ),
    "phonometry.aircraft.rotorcraft_propagation.TerrainScreeningResult": ("screened",),
    "phonometry.electroacoustics.induction_loop.BackgroundNoiseAssessment": (
        "reference_signal_to_noise_ratio_db",
        "category",
        "report_required",
    ),
    "phonometry.electroacoustics.sound_reinforcement.FeedbackStabilityResult": (
        "is_stable",
    ),
    "phonometry.emission.free_field_qualification.FreeFieldCheck": (
        "room",
        "frequencies_hz",
        "band_radius_m",
        "maximum_qualified_radius_m",
        "points_met",
        "equal_spacing_met",
        "spacing_met",
        "iso26101_spacing_met",
        "length_met",
        "background_met",
        "directionality_met",
        "traverse_count_met",
        "path_targets_met",
        "working_area_met",
        "path_angles_met",
        "reflecting_plane_met",
        "full_frequency_range",
        "conforming_range_hz",
        "conforming_radius_m",
        "not_judged",
    ),
    "phonometry.emission.intensity_compliance.IntensityInstrumentComplianceResult": (
        "bands",
        "overall_class",
        "range_limited",
    ),
    "phonometry.emission.reference_sound_source.ReferenceSourceCalibration": (
        "sound_power_level_db",
        "intensity_bands",
        "intensity_agreement",
        "room_qualified",
    ),
    "phonometry.emission.sound_power_hard_walled.HardWalledSoundPowerResult": (
        "background_requirement_met",
        "upper_bound",
    ),
    "phonometry.emission.sound_power_hard_walled.SourceLocationPlan": (
        "spectral_character",
        "a_weighted_spectral_character",
    ),
    "phonometry.emission.sound_power_in_duct.InDuctSoundPowerResult": (
        "information_only_band",
    ),
    "phonometry.emission.sound_power_in_situ.InSituSoundPowerResult": (
        "background_requirement_met",
        "upper_bound",
        "grade",
        "sigma_r0",
        "sigma_tot",
        "expanded_uncertainty",
    ),
    "phonometry.emission.sound_power_intensity.PrecisionIntensityResult": (
        "sound_power",
        "not_applicable_band",
        "sound_power_level",
        "sound_power_level_normalized",
        "sound_power_level_a",
    ),
    "phonometry.emission.sound_power_intensity.SoundPowerIntensityResult": (
        "partial_power_level",
        "sound_power",
        "negative_band",
        "sound_power_level",
        "negative_partial_power_index",
        "dynamic_capability_index",
        "achieved_grade",
        "a_weighting_omitted_bands",
        "sound_power_level_a",
    ),
    "phonometry.emission.sound_power_intensity.PrecisionCriteria": (
        "criterion_1",
        "criterion_2",
        "criterion_3",
        "criterion_4",
        "criterion_5",
        "qualified",
    ),
    "phonometry.emission.sound_power_intensity_points.DiscretePointIntensityResult": (
        "partial_power",
        "sound_power",
        "sound_power_level",
        "not_applicable_band",
        "dynamic_capability_index",
        "criterion_1",
        "negative_power_within_limit",
        "criterion_2",
        "minimum_positions",
        "achieved_grade",
        "confidence_interval",
        "expanded_uncertainty",
        "a_weighting_omitted_bands",
        "sound_power_level_a",
        "field_nonuniformity_a",
        "achieved_grade_a",
    ),
    "phonometry.emission.sound_power_special_room.SpecialRoomSoundPowerResult": (
        "background_requirement_met",
        "background_requirement_met_a",
    ),
    "phonometry.emission.turbine_noise.TurbineTestEnvironmentCheck": (
        "correction_ok",
        "wind_ok",
        "windscreen_advised",
    ),
    "phonometry.emission.workstation.EmissionPressureResult": ("upper_bound",),
    "phonometry.environment.assessment.impulsive_sound.ImpulseOnset": (
        "level_difference",
        "prominence",
        "qualifies",
    ),
    "phonometry.environment.assessment.impulsive_sound.ImpulsiveSoundResult": (
        "prominence",
        "adjustment",
        "category",
        "adjusted_laeq",
    ),
    "phonometry.environment.assessment.impulsive_sound.ImpulseProminenceResult": (
        "per_impulse",
        "qualifies",
        "prominence",
        "adjustment",
    ),
    "phonometry.environment.assessment.measurement.ResidualCorrectionResult": (
        "reliable",
    ),
    "phonometry.environment.assessment.spain.PeriodAssessment": (
        "reported_level",
        "reported_long_term",
        "max_phase_level",
        "phase_pass",
        "daily_pass",
        "long_term_pass",
    ),
    "phonometry.environment.assessment.wind_turbine_modulation.ModulationBlock": (
        "status",
    ),
    "phonometry.environment.assessment.wind_turbine_modulation.ModulationPeriod": (
        "modulation_depths_db",
        "fundamental_frequencies_hz",
        "valid_blocks",
        "rated",
        "rating_db",
        "mean_modulation_frequency_hz",
        "mode_modulation_frequency_hz",
    ),
    "phonometry.environment.assessment.wind_turbine_receptor.SoundRelevantTurbines": (
        "relevant",
        "total_level_db",
        "relevant_level_db",
    ),
    "phonometry.environment.assessment.wind_turbine_receptor.TurbineSoundLevels": (
        "regimes",
    ),
    "phonometry.environment.assessment.wind_turbine_receptor.WindShearProfile": (
        "typical",
    ),
    "phonometry.environment.sources.rolling_stock_noise.ReferenceTrackCheck": (
        "conditions",
        "passes",
        "failed",
    ),
    "phonometry.environment.sources.wind_turbine.WindTurbineTonalityResult": (
        "is_audible",
        "has_identified_tone",
    ),
    "phonometry.filters.compliance.FilterComplianceResult": (
        "bands",
        "overall_class",
        "range_limited",
    ),
    "phonometry.filters.weighting_compliance.WeightingComplianceResult": (
        "bands",
        "overall_class",
        "range_limited",
    ),
    "phonometry.hearing.audiometry.AscendingThresholdResult": (
        "threshold_db",
        "determined",
        "series_exhausted",
    ),
    "phonometry.hearing.audiometry.AutomaticThresholdResult": (
        "is_peak",
        "retained",
    ),
    "phonometry.hearing.audiometry.SweepThresholdResult": ("is_peak",),
    "phonometry.hearing.occupational_exposure.ExposureResult": ("sampling_advisory",),
    "phonometry.hearing.occupational_exposure.TaskContribution": ("spread_advisory",),
    "phonometry.hearing.real_ear_attenuation.AttenuationDifferenceResult": (
        "difference_db",
        "criterion_db",
        "significant",
    ),
    "phonometry.materials.absorbers.suspended_ceilings.CeilingSpecimenCheck": (
        "area_error_m2",
        "deflection_ok",
        "substructure_ok",
        "fixture_ok",
        "supports_ok",
        "humidity_ok",
        "ce_marking_depth",
        "satisfied",
    ),
    "phonometry.metrology.data_qualification.StationarityTestResult": (
        "bounds",
        "stationary",
    ),
    "phonometry.metrology.data_qualification.TrendTestResult": (
        "bounds",
        "trend_free",
    ),
    "phonometry.metrology.reciprocity_coupler.CouplerCheck": (
        "ratio_recommended",
        "approximation_valid",
        "full_solution_advised",
        "conditions_valid",
    ),
    "phonometry.metrology.reciprocity_coupler.WaveMotionCorrection": ("interpolated",),
    "phonometry.metrology.reciprocity_free_field.FreeFieldArrangementCheck": (
        "distances_ok",
        "support_ok",
        "annex_a_range",
        "attenuation_accuracy",
    ),
    "phonometry.noise_control.cabin_insulation.CabinInsulationResult": ("apparent",),
    "phonometry.noise_control.cabin_insulation.CabinUncertainty": (
        "ratio_satisfied",
        "stateable",
        "stated_band_range_hz",
        "increased_uncertainty_band_range_hz",
        "excess_standard_deviation_db",
    ),
    "phonometry.noise_control.valves.AerodynamicValveNoise": ("regime",),
    "phonometry.noise_control.valves_hydrodynamic.HydrodynamicValveNoise": ("regime",),
    "phonometry.room.acoustics.RoomAcousticsResult": (
        "edt_valid",
        "t20_valid",
        "t30_valid",
    ),
    "phonometry.room.spatial_decay.BackgroundMarginCheck": (
        "needs_correction",
        "unusable",
        "satisfied",
    ),
    "phonometry.room.workroom_prediction.DetailVerdict": (
        "satisfied",
        "room_ok",
        "fittings_ok",
        "sources_ok",
    ),
    "phonometry.signals.synchronous_average.SynchronousAverageResult": (
        "interpolated",
    ),
    "phonometry.underwater.bioacoustics.weighting.WeightedExposureResult": (
        "exceeds_injury",
        "exceeds_tts",
    ),
    "phonometry.underwater.propagation.weston_regimes.WestonPropagationResult": (
        "regime",
    ),
    "phonometry.vibration.immission.people.PeopleAssessment": (
        "complies",
        "criterion",
        "within_uncertainty",
    ),
    "phonometry.vibration.immission.train_categories.RailwayChange": (
        "kb_fmax_increase_percent",
        "kb_ftr_increase_percent",
        "kb_fmax_met",
        "kb_ftr_met",
        "complies",
    ),
    "phonometry.vibration.structural.transfer_stiffness.DrivingPointStiffnessResult": (
        "adequate",
    ),
    "phonometry.vibration.structural.transfer_stiffness.TransferStiffnessResult": (
        "valid",
    ),
}


@pytest.mark.parametrize(
    ("qualname", "names"), sorted(_DERIVED_FLAGS.items()), ids=lambda v: str(v)
)
def test_a_verdict_flag_is_a_read_only_property(
    qualname: str, names: tuple[str, ...]
) -> None:
    module_name, _, class_name = qualname.rpartition(".")
    cls = getattr(importlib.import_module(module_name), class_name)
    fields = {field.name for field in dataclasses.fields(cls)}
    for name in names:
        assert name not in fields, f"{qualname}.{name} is a constructor field"
        assert isinstance(getattr(cls, name), property), f"{qualname}.{name}"
