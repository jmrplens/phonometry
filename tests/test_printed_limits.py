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
"""

from __future__ import annotations

import dataclasses
import importlib
import pkgutil
import re
from typing import TYPE_CHECKING

import pytest

import phonometry

if TYPE_CHECKING:
    from collections.abc import Iterator

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
    "phonometry.building.measurement.joint_insulation.JointGapSeriesCheck."
    "minimum_measured": "a verdict flag",
    "phonometry.building.measurement.joint_insulation.JointGapSeriesCheck."
    "nominal_measured": "a verdict flag",
    "phonometry.building.measurement.service_equipment.MeasurementDisturbanceCheck."
    "maximum_levels_db": "the measured maximum levels",
    "phonometry.building.measurement.service_equipment.VaryingBackgroundCheck."
    "background_maximum_db": "the measured maximum of the background",
    "phonometry.electroacoustics.induction_loop.BackgroundNoiseAssessment."
    "report_required": "a flag, not a limit",
    "phonometry.emission.free_field_qualification.FreeFieldCheck."
    "maximum_qualified_radius_m": "the radius the fit qualified, a result",
    "phonometry.emission.free_field_qualification.SourceDirectionalityResult."
    "maximum_negative_deviation_db": "the measured largest deviation",
    "phonometry.emission.free_field_qualification.SourceDirectionalityResult."
    "maximum_positive_deviation_db": "the measured largest deviation",
    "phonometry.emission.sound_power_hard_walled.HardWalledRoomCheck."
    "max_absorption_coefficient": "the largest coefficient of the room's surfaces",
    "phonometry.emission.sound_power_hard_walled.HardWalledSoundPowerResult."
    "background_requirement_met": "a verdict flag per band",
    "phonometry.emission.sound_power_hard_walled.HardWalledSoundPowerResult."
    "upper_bound": "a flag per band: the level is an upper bound",
    "phonometry.emission.sound_power_in_situ.InSituSoundPowerResult."
    "background_requirement_met": "a verdict flag per band",
    "phonometry.emission.sound_power_in_situ.InSituSoundPowerResult.upper_bound": (
        "a flag per band: the level is an upper bound"
    ),
    "phonometry.emission.sound_power_intensity.PrecisionCriteria.criterion_1": (
        "the pass flags of ISO 9614-3 Annex C"
    ),
    "phonometry.emission.sound_power_intensity.PrecisionCriteria.criterion_2": (
        "the pass flags of ISO 9614-3 Annex C"
    ),
    "phonometry.emission.sound_power_intensity.PrecisionCriteria.criterion_3": (
        "the pass flags of ISO 9614-3 Annex C"
    ),
    "phonometry.emission.sound_power_intensity.PrecisionCriteria.criterion_4": (
        "the pass flags of ISO 9614-3 Annex C"
    ),
    "phonometry.emission.sound_power_intensity.PrecisionCriteria.criterion_5": (
        "the pass flags of ISO 9614-3 Annex C"
    ),
    "phonometry.emission.sound_power_special_room.SpecialRoomSoundPowerResult."
    "background_requirement_met": "a verdict flag per band",
    "phonometry.emission.sound_power_special_room.SpecialRoomSoundPowerResult."
    "background_requirement_met_a": "a verdict flag",
    "phonometry.environment.assessment.spain.PeriodAssessment.max_phase_level": (
        "the largest measured level of the period"
    ),
    "phonometry.environment.sources.rolling_stock_noise.TrackCondition.requirement": (
        "the requirement in words, not a value"
    ),
    "phonometry.environment.sources.statistical_pass_by.PassByRegression.max_levels_db": (
        "the measured maximum level of each pass-by"
    ),
    "phonometry.metrology.sound_level_meter.SoundLevelMeterPeriodicRequirement."
    "over_maximum_by_correction_data": "the names of the results it concerns",
    "phonometry.noise_control.cabin_insulation.SourcePositionCheck."
    "max_octave_spread_db": "the measured spread",
    "phonometry.vibration.immission.people.PeopleAssessment.criterion": (
        "the name of the comparison that decided, not a value"
    ),
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
