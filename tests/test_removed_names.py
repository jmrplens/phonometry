#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What each generation of phonometry removed, pinned gone.

Every rename this library has made announced the release that would remove the
old spelling, and every one of those releases has now happened. Nothing here
tests a deprecation, because none is left: 4.0 carries no aliases, no shim
modules and no rename notices. What it tests is that the removals hold, which
is a different thing and needs saying out loud, because a name can come back by
accident. A module re-exported one level up, a constant reintroduced under its
old spelling, a stale file left on disk after a package split: each of those
resurrects a path the documentation says is gone, and none of them fails
anything else in the suite.

Three generations, all removed:

* **3.1** renamed functions, constants and keyword arguments, and named 4.0.
  ``docs/reference/api/index.md`` publishes that list; this file is what holds
  the page to it.
* **3.2** grouped the flat top-level modules into domain subpackages and named
  4.0. ``phonometry.levels`` and its eighty-odd siblings went then.
* **4.0** rebuilt the taxonomy (``metrology`` into ``filters``, ``signals`` and
  a narrowed ``metrology``; the speech intelligibility of ``hearing`` into
  ``speech``; ``environmental`` into ``environment``) and, unlike its
  predecessors, removed the old paths in the same release rather than shimming
  them for one more.
"""

from __future__ import annotations

import importlib
import inspect
import re
import sys

import numpy as np
import pytest

import phonometry as ph

RNG = np.random.default_rng(1234)
SIGNAL = RNG.standard_normal(4800)
FS = 48_000.0


# --------------------------------------------------------------------------- #
# 3.1 renames: the function aliases, the renamed constants and the deprecated
# keywords were removed in 4.0, as their notices said since 3.1. Frozen lists;
# the point is that they stay gone.
# --------------------------------------------------------------------------- #
_REMOVED_FUNCTIONS = [
    ("phonometry", "octavefilter"),
    ("phonometry.filters", "octavefilter"),
    ("phonometry.filters.core", "octavefilter"),
    ("phonometry.filters.frequencies", "getansifrequencies"),
    ("phonometry.filters.frequencies", "normalizedfreq"),
    ("phonometry.metrology.calibration", "calculate_sensitivity"),
    ("phonometry.building.measurement.uncertainty", "coverage_factor"),
    ("phonometry.building.measurement.uncertainty", "expanded_uncertainty"),
    ("phonometry.environment.assessment.measurement", "expanded_uncertainty"),
]

_REMOVED_CONSTANTS = [
    ("phonometry", "OCTAVE_BANDS_HZ"),
    ("phonometry", "THIRD_OCTAVE_BANDS_HZ"),
    ("phonometry", "BASE_PLATE_BANDS_HZ"),
    ("phonometry", "ExposureWarning"),
    ("phonometry.materials.absorbers.rating", "OCTAVE_BANDS_HZ"),
    ("phonometry.materials.diffusers.scattering_diffusion", "BASE_PLATE_BANDS_HZ"),
    ("phonometry.speech.sii", "BAND_CENTRES"),
    ("phonometry.hearing.occupational_exposure", "ExposureWarning"),
]

#: ``(package, function, keyword)``: the keyword has to be absent from the
#: signature the package publishes today.
_REMOVED_KEYWORDS = [
    ("materials", "adrienne_window", "sample_rate"),
    ("materials", "in_situ_reflection_factor", "sample_rate"),
    ("materials", "in_situ_absorption_spectrum", "sample_rate"),
    ("environment", "atmospheric_absorption", "humidity"),
    ("environment", "outdoor_propagation_attenuation", "humidity"),
    ("environment", "predicted_receiver_level", "humidity"),
    ("emission", "environmental_correction", "room_volume"),
    ("emission", "sound_power_pressure", "room_volume"),
]


@pytest.mark.parametrize(("module", "name"), _REMOVED_FUNCTIONS + _REMOVED_CONSTANTS)
def test_removed_3_1_alias_is_gone(module: str, name: str) -> None:
    home = importlib.import_module(module)
    with pytest.raises(AttributeError, match=rf"has no attribute '{name}'"):
        getattr(home, name)


@pytest.mark.parametrize(("package", "func", "keyword"), _REMOVED_KEYWORDS)
def test_removed_3_1_keyword_is_gone(package: str, func: str, keyword: str) -> None:
    home = getattr(ph, package)
    assert keyword not in inspect.signature(getattr(home, func)).parameters


def test_the_canonical_names_the_3_1_aliases_pointed_at_are_all_here() -> None:
    """The removal took the aliases, not the functions they delegated to."""
    for package, name in (
        ("filters", "octave_filter"),
        ("filters", "nominal_frequencies"),
        ("filters", "normalized_frequencies"),
        ("metrology", "sensitivity"),
        ("building", "insulation_coverage_factor"),
        ("building", "insulation_expanded_uncertainty"),
        ("environment", "environmental_expanded_uncertainty"),
        ("emission", "emission_expanded_uncertainty"),
        ("materials", "RATING_OCTAVE_BANDS_HZ"),
        ("materials", "RATING_THIRD_OCTAVE_BANDS_HZ"),
        ("materials", "BASE_PLATE_BANDS_HZ"),
        ("hearing", "OccupationalExposureWarning"),
    ):
        assert hasattr(getattr(ph, package), name), f"{package}.{name}"


def test_the_plot_renderers_moved_out_of_the_deprecated_module() -> None:
    """``phonometry._plotting`` was the 3.2 re-export; ``_plot`` is the home."""
    # Naming the module matters: a module that came back carrying a broken
    # optional import would raise ModuleNotFoundError too, about something else.
    with pytest.raises(
        ModuleNotFoundError, match=r"No module named 'phonometry\._plotting'"
    ):
        importlib.import_module("phonometry._plotting")
    assert callable(importlib.import_module("phonometry._plot.room").plot_excitation)


# --------------------------------------------------------------------------- #
# 3.2 package reorganization: its flat module paths were removed in 4.0, as
# announced. A sample of them, frozen; the point is that they stay gone, and
# that a stale file left on disk would be caught rather than silently served.
# --------------------------------------------------------------------------- #
_REMOVED_FLAT_MODULE_PATHS = [
    "phonometry.core",
    "phonometry.insulation",
    "phonometry.levels",
    "phonometry.loudness",
    "phonometry.room_ir",
    "phonometry.underwater_acoustics",
    "phonometry.utils",
]


@pytest.mark.parametrize("path", _REMOVED_FLAT_MODULE_PATHS)
def test_removed_flat_module_path_raises(path: str) -> None:
    with pytest.raises(
        ModuleNotFoundError, match=rf"No module named '(?:{_import_chain(path)})'"
    ):
        importlib.import_module(path)
    assert path not in sys.modules
    # The names these modules held never moved; the package that owns each of
    # them publishes it, which is what the flat paths were a shortcut to.
    assert callable(ph.signals.leq)


# --------------------------------------------------------------------------- #
# 4.0 taxonomy: the release that rebuilt it also removed the paths it replaced,
# instead of shimming them for one more generation. A sample of the old paths,
# one per kind of move: a package that split, a package that was renamed, a
# module that gained a second level, and a module that was renamed in place.
# --------------------------------------------------------------------------- #
_REMOVED_4_0_MODULE_PATHS = [
    "phonometry.metrology.core",
    "phonometry.metrology.levels",
    "phonometry.metrology.intensity_compliance",
    "phonometry.hearing.sti",
    "phonometry.hearing.sii",
    "phonometry.environmental",
    "phonometry.environmental.cnossos_road",
    "phonometry.vibration.human_vibration",
    "phonometry.building.spanish_building_code",
    "phonometry.materials.porous_absorber",
    "phonometry.psychoacoustics.loudness_zwicker",
    "phonometry.underwater.ocean_ambient_noise",
    "phonometry.room.room_ir",
    "phonometry.aircraft.aircraft_noise",
]


def _import_chain(path: str) -> str:
    """``a.b.c`` -> a regex alternation of ``a.b.c``, ``a.b`` and ``a``.

    Python reports the FIRST missing ancestor, not the path asked for: with
    ``phonometry.environmental`` removed too, importing its ``cnossos_road``
    submodule reports the parent. Either is a correct refusal of this path, and
    naming the chain still excludes the failure worth catching, which is some
    unrelated third-party import going missing underneath a module that came
    back.
    """
    parts = path.split(".")
    return "|".join(
        re.escape(".".join(parts[: i + 1])) for i in reversed(range(len(parts)))
    )


@pytest.mark.parametrize("path", _REMOVED_4_0_MODULE_PATHS)
def test_removed_4_0_module_path_raises(path: str) -> None:
    with pytest.raises(
        ModuleNotFoundError, match=rf"No module named '(?:{_import_chain(path)})'"
    ):
        importlib.import_module(path)
    assert path not in sys.modules


def test_a_removed_path_is_not_served_by_its_parent_package() -> None:
    """The three ways a caller can reach for a moved module, all refused.

    ``import a.b`` and ``from a.b import name`` raise ``ModuleNotFoundError``,
    ``from a import b`` raises ``ImportError`` because ``a`` imports and only
    the name lookup inside it fails, and ``a.b`` as an attribute raises
    ``AttributeError``. Three exception types for one removal, which is why the
    CHANGELOG names them separately.
    """
    with pytest.raises(
        ModuleNotFoundError, match=r"No module named 'phonometry\.hearing\.sti'"
    ):
        importlib.import_module("phonometry.hearing.sti")
    with pytest.raises(ImportError, match=r"cannot import name 'sti'"):
        from phonometry.hearing import sti  # noqa: F401
    with pytest.raises(AttributeError, match=r"has no attribute 'sti'"):
        _ = ph.hearing.sti
    with pytest.raises(AttributeError, match=r"has no attribute 'environmental'"):
        _ = ph.environmental


def test_the_names_the_4_0_moves_carried_are_all_reachable() -> None:
    """The paths went; the public names they held did not."""
    assert callable(ph.signals.leq)
    assert callable(ph.filters.octave_filter)
    assert callable(ph.speech.sti_from_impulse_response)
    assert callable(ph.emission.verify_intensity_class)
    assert callable(ph.environment.lden)
    assert callable(ph.room.impulse_response)


def test_a_namespace_does_not_serve_a_name_that_left_it() -> None:
    """A name that moved between packages is gone from the one it left.

    The 4.0 split let each of these keep answering from its old namespace for
    one release; that indirection went with the shims, so reading one from
    where it used to live now fails where it used to warn.
    """
    for namespace, name in (
        (ph.metrology, "leq"),
        (ph.metrology, "octave_filter"),
        (ph.metrology, "verify_intensity_class"),
        (ph.hearing, "sti_from_impulse_response"),
        (ph.hearing, "speech_intelligibility_index"),
        (ph.filters, "verify_aircraft_noise_system"),
    ):
        with pytest.raises(AttributeError, match=rf"has no attribute '{name}'"):
            getattr(namespace, name)


def test_the_verdict_wrappers_the_4_0_folded_in_are_gone() -> None:
    """The two twins that only wrapped a verdict dictionary went with it.

    ``filter_class_compliance`` and ``intensity_class_compliance`` existed to
    package what their ``verify_*`` sibling returned as a dictionary. The
    verifier returns the result object itself now, so the second door onto the
    same computation is gone rather than kept as an alias.
    """
    for namespace, name in (
        (ph.filters, "filter_class_compliance"),
        (ph.emission, "intensity_class_compliance"),
    ):
        with pytest.raises(AttributeError, match=rf"has no attribute '{name}'"):
            getattr(namespace, name)


# --------------------------------------------------------------------------- #
# 4.0 one address per name: the alias, the re-export shims and the type
# aliases that gave a public name a second address, or gave a private one a
# first, are gone. The names they pointed at are where they always were.
# --------------------------------------------------------------------------- #
_REMOVED_4_0_SECOND_NAMES = [
    ("phonometry.vibration", "partial_exposure"),
    ("phonometry.vibration.human", "partial_exposure"),
    ("phonometry.vibration.human.exposure", "partial_exposure"),
    ("phonometry.building.prediction.resilient_layers", "LiningImprovementResult"),
    ("phonometry.building.prediction.resilient_layers", "lining_improvement"),
    ("phonometry.building.prediction.resilient_layers", "lining_improvement_in_situ"),
    ("phonometry.building.prediction.resilient_layers", "lining_resonance_frequency"),
    (
        "phonometry.building.prediction.resilient_layers",
        "weighted_lining_improvement",
    ),
    ("phonometry.emission", "DeclarationForm"),
    # insulation imports the five ISO 717 names its own body calls; the rest
    # of ratings, and its private tables, no longer resolve there at all.
    *(
        ("phonometry.building.measurement.insulation", name)
        for name in (
            "ExtendedImpactRatingResult",
            "ExtendedWeightedRatingResult",
            "impact_improvement_adaptation_term",
            "weighted_impact_improvement",
            "weighted_impact_rating_extended",
            "weighted_rating_extended",
            "_INDEX_500_THIRD",
            "_REF_IMPACT_THIRD_OCTAVE",
            "_REF_THIRD_OCTAVE",
            "_SPECTRUM1_50_5000",
            "_SPECTRUM2_50_5000",
        )
    ),
    ("phonometry.noise_control.screen_in_situ", "OPERATOR_SPHERE_RADIUS_M"),
    ("phonometry.noise_control.cabin_insulation", "MANDATORY_BAND_RANGE_HZ"),
    ("phonometry.noise_control.cabin_insulation", "leak_ratio"),
    ("phonometry.noise_control.cabin_insulation", "seal_ratio"),
    # Public-looking constants its package never published: the two defaults
    # are private now, and the reference sound power is ISO 1683's own.
    ("phonometry.emission.vibration_sound_power", "REFERENCE_AREA"),
    ("phonometry.emission.vibration_sound_power", "REFERENCE_IMPEDANCE"),
    ("phonometry.emission.vibration_sound_power", "REFERENCE_SOUND_POWER"),
]


@pytest.mark.parametrize(("module", "name"), _REMOVED_4_0_SECOND_NAMES)
def test_a_second_name_the_4_0_removed_is_gone(module: str, name: str) -> None:
    home = importlib.import_module(module)
    with pytest.raises(AttributeError, match=rf"has no attribute '{name}'"):
        getattr(home, name)


#: ``(package, class, keyword)``: a constructor keyword 4.0 withdrew. The
#: aircraft's database is ``database`` now, and a database built by hand takes
#: no performance tables, which only an ANP export carries.
_REMOVED_4_0_KEYWORDS = [
    ("aircraft", "ANPAircraft", "_database"),
    ("aircraft", "ANPDatabase", "performance"),
]


@pytest.mark.parametrize(("package", "owner", "keyword"), _REMOVED_4_0_KEYWORDS)
def test_a_constructor_keyword_the_4_0_removed_is_gone(
    package: str, owner: str, keyword: str
) -> None:
    home = getattr(ph, package)
    assert keyword not in inspect.signature(getattr(home, owner)).parameters


def test_a_leaf_module_publishes_only_what_it_defines() -> None:
    """``insulation`` lists its own results, not the ISO 717 names it calls."""
    insulation = importlib.import_module("phonometry.building.measurement.insulation")
    assert sorted(insulation.__all__) == [
        "AirborneInsulationResult",
        "FacadeInsulationResult",
        "ImpactInsulationResult",
        "airborne_insulation",
        "energy_average_level",
        "facade_insulation",
        "impact_insulation",
    ]
    for module, alias in (
        ("phonometry.emission.sound_power", "Grade"),
        ("phonometry.emission.sound_power", "Surface"),
        ("phonometry.filters.equalizer", "EQFilterType"),
    ):
        assert alias not in importlib.import_module(module).__all__


@pytest.mark.parametrize(
    ("module", "package"),
    [
        ("phonometry.building.measurement.ratings", "phonometry.building.measurement"),
        ("phonometry.emission.vibration_sound_power", "phonometry.emission"),
    ],
)
def test_an_owner_module_lists_what_its_package_takes_from_it(
    module: str, package: str
) -> None:
    """The module a package imports from says, in ``__all__``, what it gives.

    Neither module had an ``__all__``, so a name it defined and its package
    never took up (a type alias, a default's constant) looked as public as the
    ones the package publishes.
    """
    owner = importlib.import_module(module)
    published = importlib.import_module(package)
    taken = {
        name
        for name in published.__all__
        if name in vars(owner) and vars(owner)[name] is getattr(published, name)
    }
    assert sorted(owner.__all__) == sorted(taken)


def test_the_names_the_second_addresses_pointed_at_are_all_here() -> None:
    """The second address went; the one each name really has did not."""
    assert callable(ph.vibration.daily_exposure)
    assert callable(ph.building.weighted_rating)
    assert callable(ph.building.lining_improvement)
    for module, name in (
        ("phonometry.building.measurement.ratings", "weighted_rating_extended"),
        ("phonometry.building.prediction.linings", "lining_improvement"),
    ):
        owner = importlib.import_module(module)
        assert getattr(owner, name).__module__ == module


# --------------------------------------------------------------------------- #
# 4.0 one name per computation: a formula two modules published under two
# names keeps the one, a function is named for what it returns, and the old
# spellings are gone with no alias.
# --------------------------------------------------------------------------- #
_REMOVED_4_0_FUNCTION_NAMES = [
    # DIN 4150-1 Formula (4) is the storey estimate of DIN 4150-3 6.4 and
    # ISO 4866 D.2; vibration.story_fundamental_frequency is the one function.
    *(
        (module, name)
        for module in (
            "phonometry.vibration",
            "phonometry.vibration.immission",
            "phonometry.vibration.immission.prediction",
        )
        for name in ("storey_frequency_hz", "STOREY_FORMULA_MIN_STOREYS")
    ),
    # One conversion from the ISO 9613-1 alpha to the power attenuation m.
    ("phonometry.environment", "air_attenuation_m"),
    ("phonometry.materials", "attenuation_from_alpha"),
    ("phonometry.materials", "air_attenuation_coefficient"),
    ("phonometry.materials.diffusers", "air_attenuation_coefficient"),
    # One root-sum-square, in metrology, and the GUM propagation named for
    # what it does; the expanded uncertainty is the result's own method.
    ("phonometry.building", "combine_uncertainties"),
    ("phonometry.building.measurement.uncertainty", "combine_uncertainties"),
    ("phonometry.environment", "combined_standard_uncertainty"),
    ("phonometry.environment.assessment.measurement", "combined_standard_uncertainty"),
    ("phonometry.metrology", "combine_uncertainty"),
    ("phonometry.metrology", "expanded_uncertainty"),
    ("phonometry.metrology.uncertainty", "expanded_uncertainty"),
    # A computation is a noun phrase.
    ("phonometry.building", "combine_linings"),
    ("phonometry.building", "combine_subareas"),
    ("phonometry.noise_control", "combine_stage_levels"),
    ("phonometry.noise_control", "combine_internal_levels"),
    ("phonometry.vibration", "combine_partial_exposures"),
    ("phonometry.hearing", "combine_age_and_noise"),
    # The Johnson-Champoux-Allard air is named for its model.
    ("phonometry.materials", "PUBLISHED_AIR"),
]


@pytest.mark.parametrize(("module", "name"), _REMOVED_4_0_FUNCTION_NAMES)
def test_a_function_name_the_4_0_retired_is_gone(module: str, name: str) -> None:
    home = importlib.import_module(module)
    with pytest.raises(AttributeError, match=rf"has no attribute '{name}'"):
        getattr(home, name)


def test_the_reflection_index_has_no_uncertainty_method_of_its_own() -> None:
    """EN 1793-5 A.2 reads Table A.1 alone, so it is a function of the package."""
    assert not hasattr(ph.environment.ReflectionIndexResult, "expanded_uncertainty")
    assert callable(ph.environment.reflection_index_expanded_uncertainty)


def test_the_one_name_each_retired_function_left_is_here() -> None:
    """Each retired name left one function computing what it computed."""
    assert ph.vibration.story_fundamental_frequency(8) == pytest.approx(1.25)
    assert ph.metrology.combined_standard_uncertainty([3.0, 4.0]) == pytest.approx(5.0)
    assert ph.noise_control.combined_stage_level([80.0, 80.0]) == pytest.approx(
        80.0 + 10.0 * np.log10(2.0)
    )
    alpha = 10.0 * np.log10(np.e)
    assert float(ph.materials.power_attenuation_from_alpha(alpha)) == pytest.approx(1.0)
    m = ph.environment.air_power_attenuation_per_m([1000.0], temperature_c=20.0)
    expected = ph.environment.air_attenuation([1000.0], temperature_c=20.0) / alpha
    np.testing.assert_allclose(m, expected, rtol=1e-12)


# --------------------------------------------------------------------------- #
# 4.0 spells every identifier in American English, and in situ as ``in_situ``.
# The British spellings and the run-together ``insitu`` went with no alias: a
# sample of each kind, a function, a class, a constant, a module, a keyword and
# a choice the caller types.
# --------------------------------------------------------------------------- #
_REMOVED_4_0_SPELLINGS = [
    ("phonometry.materials", "insitu_absorption_coefficient"),
    ("phonometry.materials", "insitu_absorption_from_reflection"),
    ("phonometry.materials", "insitu_absorption_spectrum"),
    ("phonometry.materials", "insitu_reflection_factor"),
    ("phonometry.materials", "plot_insitu_geometry"),
    ("phonometry.materials", "InsituAbsorptionResult"),
    ("phonometry.materials", "fibre_characteristic_lengths"),
    ("phonometry.materials", "FibreResistivityFit"),
    ("phonometry.metrology", "acoustic_centre"),
    ("phonometry.metrology", "AcousticCentre"),
    ("phonometry.electroacoustics", "check_programme_signal"),
    ("phonometry.electroacoustics", "loop_centre_field"),
    ("phonometry.vibration", "storey_fundamental_frequency"),
    ("phonometry.vibration", "STOREY_FREQUENCY_MIN_STOREYS"),
    ("phonometry.vibration", "centred_interval"),
    ("phonometry.simulation", "ALUMINIUM"),
    ("phonometry.environment", "MODELLING_UNCERTAINTY_DB"),
    ("phonometry.building", "DB_HR_NORMALISED_SPECTRA"),
]


@pytest.mark.parametrize(("module", "name"), _REMOVED_4_0_SPELLINGS)
def test_a_british_spelling_the_4_0_retired_is_gone(module: str, name: str) -> None:
    home = importlib.import_module(module)
    with pytest.raises(AttributeError, match=rf"has no attribute '{name}'"):
        getattr(home, name)


def test_the_programme_signal_module_path_is_gone() -> None:
    path = "phonometry.electroacoustics.programme_signal"
    with pytest.raises(
        ModuleNotFoundError,
        match=r"No module named 'phonometry\.electroacoustics\.programme_signal'",
    ):
        importlib.import_module(path)


#: ``(package, function, keyword)``: a British keyword 4.0 renamed.
_REMOVED_4_0_SPELLING_KEYWORDS = [
    ("room", "filter_bandwidth", "centre"),
    ("room", "source_directivity_limit", "centre"),
    ("environment", "tonal_audibility", "centre_frequency"),
    ("environment", "outdoor_quality_objectives", "urbanisation"),
    ("underwater", "monopole_source_level", "draught"),
    ("vibration", "fundamental_period", "storeys"),
    ("electroacoustics", "verify_amplifier_overload", "programme"),
    ("noise_control", "stage_conditions", "vapour_pressure_pa"),
]


@pytest.mark.parametrize(("package", "func", "keyword"), _REMOVED_4_0_SPELLING_KEYWORDS)
def test_a_british_keyword_the_4_0_retired_is_gone(
    package: str, func: str, keyword: str
) -> None:
    home = getattr(ph, package)
    assert keyword not in inspect.signature(getattr(home, func)).parameters


def test_a_british_choice_the_4_0_retired_is_refused() -> None:
    """A choice is typed like a name, and the British one is refused by name."""
    spectra = np.zeros((5, 24))
    with pytest.raises(ValueError, match=r"'model' must be one of"):
        ph.vibration.fundamental_period("storeys", stories=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match=r"'location' must be 'center' or 'edge'"):
        ph.vibration.infinite_plate_impedance(1.0, 10.0, location="centre")
    with pytest.raises(ValueError, match=r"Unknown procedure 'aeroplane'"):
        ph.aircraft.effective_perceived_noise_level(spectra, procedure="aeroplane")


def test_the_american_spellings_are_all_here() -> None:
    """The British spelling went; the American one each name took did not."""
    for module, name in (
        ("phonometry.materials", "in_situ_absorption_spectrum"),
        ("phonometry.materials", "InSituAbsorptionResult"),
        ("phonometry.metrology", "acoustic_center"),
        ("phonometry.electroacoustics", "check_program_signal"),
        ("phonometry.electroacoustics.program_signal", "check_program_signal"),
        ("phonometry.vibration", "story_fundamental_frequency"),
        ("phonometry.simulation", "ALUMINUM"),
    ):
        assert hasattr(importlib.import_module(module), name), (module, name)


# --------------------------------------------------------------------------- #
# 4.0 one spelling per word: acronyms in capitals, abbreviations spelled out,
# a count as n_<plural> and the time signal as x. The old spellings are gone,
# with no alias; a sample of each kind, the 3.3.0 top-level names among them.
# --------------------------------------------------------------------------- #
_RESPELLED_4_0_NAMES = [
    ("hearing", "HtlanResult", "HTLANResult"),
    ("hearing", "NiptsResult", "NIPTSResult"),
    ("aircraft", "AnpAircraft", "ANPAircraft"),
    ("aircraft", "AnpDatabase", "ANPDatabase"),
    ("aircraft", "AnpNpdCurves", "ANPNPDCurves"),
    ("aircraft", "AnpProfile", "ANPProfile"),
    ("aircraft", "NpdLevelResult", "NPDLevelResult"),
    ("noise_control", "HvacSpectrumResult", "HVACSpectrumResult"),
    ("noise_control", "HvacWarning", "HVACWarning"),
    ("building", "DbHrCheck", "DBHRCheck"),
    ("underwater", "StrikeSelSpectrum", "StrikeSELSpectrum"),
    ("materials", "mic_calibration_factor", "microphone_calibration_factor"),
    ("materials", "apply_mic_calibration", "apply_microphone_calibration"),
    ("building", "lab_airborne_insulation", "laboratory_airborne_insulation"),
    ("building", "lab_impact_insulation", "laboratory_impact_insulation"),
    ("building", "LabAirborneInsulationResult", "LaboratoryAirborneInsulationResult"),
    ("building", "LabImpactInsulationResult", "LaboratoryImpactInsulationResult"),
    ("building", "LabInsulationWarning", "LaboratoryInsulationWarning"),
    ("noise_control", "MINIMUM_MICROPHONE_DISTANCE_M", "MIN_MICROPHONE_DISTANCE_M"),
    ("room", "MAXIMUM_DIRECTIVITY_STEP_DEG", "MAX_DIRECTIVITY_STEP_DEG"),
    ("environment", "RAILWAY_MINIMUM_SPEED", "RAILWAY_MIN_SPEED_KMH"),
    (
        "building",
        "junction_min_vibration_reduction",
        "junction_minimum_vibration_reduction",
    ),
    ("materials", "max_sampled_area_radius", "maximum_sampled_area_radius"),
    ("environment", "max_infrastructure_limit", "maximum_infrastructure_limit"),
    ("metrology", "MaxUncertaintyRow", "MaximumUncertaintyRow"),
    ("vibration", "floor_transfer_max", "floor_transfer_maximum"),
]


@pytest.mark.parametrize(("package", "old", "new"), _RESPELLED_4_0_NAMES)
def test_a_spelling_the_4_0_retired_is_gone(package: str, old: str, new: str) -> None:
    home = getattr(ph, package)
    assert hasattr(home, new), f"{package}.{new}"
    with pytest.raises(AttributeError, match=rf"has no attribute '{old}'"):
        getattr(home, old)


@pytest.mark.parametrize(
    "path",
    [
        "phonometry.building.measurement.lab_insulation",
        "phonometry.building.measurement.lab_improvement",
    ],
)
def test_the_laboratory_modules_left_their_abbreviated_paths(path: str) -> None:
    with pytest.raises(
        ModuleNotFoundError, match=rf"No module named '(?:{_import_chain(path)})'"
    ):
        importlib.import_module(path)


#: ``(package, callable, old keyword, new keyword)``.
_RENAMED_4_0_KEYWORDS = [
    ("filters", "verify_filter_class", "num_points", "n_points"),
    ("noise_control", "fan_sound_power", "blade_count", "n_blades"),
    ("psychoacoustics", "loudness_ecma", "signal_in", "x"),
    ("electroacoustics", "thd", "signal", "x"),
    ("vibration", "running_rms", "signal", "x"),
    ("psychoacoustics", "tone_to_noise_ratio", "tone_freq", "tone_frequency"),
    ("vibration", "gear_mesh_frequencies", "harmonics", "n_harmonics"),
    (
        "building",
        "check_varying_background",
        "background_maximum_db",
        "background_maximum_level_db",
    ),
    ("emission", "plant_steady_reading", "maximum_db", "maximum_level_db"),
]


@pytest.mark.parametrize(("package", "owner", "old", "new"), _RENAMED_4_0_KEYWORDS)
def test_a_keyword_the_4_0_respelled_is_gone(
    package: str, owner: str, old: str, new: str
) -> None:
    parameters = inspect.signature(getattr(getattr(ph, package), owner)).parameters
    assert new in parameters
    assert old not in parameters
