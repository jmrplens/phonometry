#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Taxonomy for the generated API reference (scripts/generate_api_docs.py).

Maps every public phonometry module to a documentation section. Sections
become directories under ``site/src/content/docs/reference/api/<section>/``
and collapsed subgroups in the site sidebar; their order here is the display
order on the index page and in the sidebar.

Modules are keyed by their full dotted name (``phonometry.<subpackage>.<mod>``)
so the mapping is unambiguous after the subpackage modularization. The bare
``"phonometry"`` entry is the package top level: the handful of names that
live in ``phonometry/__init__.py`` itself (``__version__`` and
:class:`PhonometryWarning`).

Consistency is enforced at import time (fails loudly):

- every module appears in exactly one section;
- each section only contains modules from the subpackages declared for it in
  ``_SECTION_SUBPACKAGES``. One section deliberately spans more than one
  parent: ``filters`` adds the package top level (``phonometry`` itself).

Section keys are subpackage names wherever the taxonomy allows it, so a
reader who knows where a function lives in the code can predict where its
page lives. The section listed above is the exception, and it is
deliberate.

The generator additionally checks the taxonomy against reality: every module
that owns a public name must be mapped here, and every mapped module must
still exist (see ``scripts/generate_api_docs.py``).
"""

from __future__ import annotations

import dataclasses
import inspect
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType


@dataclasses.dataclass(frozen=True)
class Section:
    """One API-reference section (a sidebar subgroup and URL directory)."""

    key: str
    label_en: str
    label_es: str
    modules: tuple[str, ...]


_SECTION_LIST: tuple[Section, ...] = (
    Section(
        key="filters",
        label_en="Filters and frequencies",
        label_es="Filtros y frecuencias",
        modules=(
            "phonometry",
            "phonometry.filters.core",
            "phonometry.filters.weighting",
            "phonometry.filters.equalizer",
            "phonometry.filters.frequencies",
            "phonometry.filters.compliance",
            "phonometry.filters.weighting_compliance",
        ),
    ),
    Section(
        key="signals",
        label_en="Signal analysis",
        label_es="Análisis de señal",
        modules=(
            "phonometry.signals.levels",
            "phonometry.signals.spectra",
            "phonometry.signals.multitaper",
            "phonometry.signals.windows",
            "phonometry.signals.miso",
            "phonometry.signals.time_frequency",
            "phonometry.signals.test_signals",
            "phonometry.signals.phase",
            "phonometry.signals.cepstrum",
            "phonometry.signals.synchronous_average",
            "phonometry.signals.inversion",
            "phonometry.signals.correlation",
            "phonometry.signals.envelope",
        ),
    ),
    Section(
        key="metrology",
        label_en="Calibration and uncertainty",
        label_es="Calibración e incertidumbre",
        modules=(
            "phonometry.metrology.calibration",
            "phonometry.metrology.uncertainty",
            "phonometry.metrology.data_qualification",
            "phonometry.metrology.reference_values",
        ),
    ),
    Section(
        key="fluids",
        label_en="Fluids",
        label_es="Fluidos",
        modules=(
            "phonometry.fluids",
            "phonometry.fluids.air",
            "phonometry.fluids.gas",
            "phonometry.fluids.water",
            "phonometry.fluids.catalogue",
            "phonometry.fluids.nonlinearity",
        ),
    ),
    Section(
        key="solids",
        label_en="Elastic solids",
        label_es="Sólidos elásticos",
        # The relations live in ``elastic`` and the published rows in
        # ``catalogue``; the ``__init__`` only re-exports, so it holds no
        # public name of its own.
        modules=(
            "phonometry.solids.elastic",
            "phonometry.solids.catalogue",
            "phonometry.solids.damping",
            "phonometry.solids.damping_treatments",
            "phonometry.solids.nonlinearity",
            "phonometry.solids.orthotropic_wood",
            "phonometry.solids.plateau",
        ),
    ),
    Section(
        key="io",
        label_en="Audio files",
        label_es="Archivos de audio",
        # The whole public surface of the subpackage lives in its
        # ``__init__`` (the implementation modules are private), so the one
        # documented module is the package itself.
        modules=("phonometry.io",),
    ),
    Section(
        key="psychoacoustics",
        label_en="Psychoacoustics",
        label_es="Psicoacústica",
        modules=(
            "phonometry.psychoacoustics.loudness.zwicker",
            "phonometry.psychoacoustics.loudness.moore_glasberg",
            "phonometry.psychoacoustics.loudness.moore_glasberg_time",
            "phonometry.psychoacoustics.loudness.ecma",
            "phonometry.psychoacoustics.loudness.contours",
            "phonometry.psychoacoustics.quality.sharpness",
            "phonometry.psychoacoustics.quality.roughness_ecma",
            "phonometry.psychoacoustics.quality.tonality",
            "phonometry.psychoacoustics.quality.tonality_ecma",
            "phonometry.psychoacoustics.quality.tone_audibility",
            "phonometry.psychoacoustics.quality.fluctuation_strength",
            "phonometry.psychoacoustics.quality.fluctuation_strength_ecma",
            "phonometry.psychoacoustics.quality.annoyance",
            "phonometry.psychoacoustics.erb_scale",
        ),
    ),
    Section(
        key="speech",
        label_en="Speech",
        label_es="Habla",
        modules=(
            "phonometry.speech.sti",
            "phonometry.speech.sii",
            "phonometry.speech.objective_intelligibility",
        ),
    ),
    Section(
        key="hearing",
        label_en="Hearing and exposure",
        label_es="Audición y exposición",
        modules=(
            "phonometry.hearing.threshold",
            "phonometry.hearing.noise_induced_hearing_loss",
            "phonometry.hearing.occupational_exposure",
            "phonometry.hearing.hearing_protectors",
        ),
    ),
    Section(
        key="rooms",
        label_en="Room acoustics",
        label_es="Acústica de salas",
        modules=(
            "phonometry.room.acoustics",
            "phonometry.room.auditorium",
            "phonometry.room.impulse_response",
            "phonometry.room.noise_criteria",
            "phonometry.room.open_plan",
            "phonometry.room.reverberation_prediction",
            "phonometry.room.enclosed_space_absorption",
            "phonometry.room.image_source",
            "phonometry.room.steady_field",
            "phonometry.room.modes",
            "phonometry.room.crowd_noise",
            "phonometry.room.spatial_decay",
            "phonometry.room.workroom_prediction",
        ),
    ),
    Section(
        key="building",
        label_en="Building acoustics",
        label_es="Acústica de la edificación",
        modules=(
            "phonometry.building.measurement.insulation",
            "phonometry.building.measurement.low_frequency",
            "phonometry.building.measurement.ratings",
            "phonometry.building.catalogue",
            "phonometry.building.impact_catalogue",
            "phonometry.building.prediction.panel_transmission",
            "phonometry.building.prediction.masonry_cavity_wall",
            "phonometry.building.measurement.heavy_impact",
            "phonometry.building.prediction.ceiling_plenum",
            "phonometry.building.prediction.aperture_transmission",
            "phonometry.building.measurement.lab_insulation",
            "phonometry.building.measurement.survey_insulation",
            "phonometry.building.measurement.intensity_insulation",
            "phonometry.building.measurement.flanking_transmission",
            "phonometry.building.prediction.facade",
            "phonometry.building.prediction.simplified_model",
            "phonometry.building.prediction.detailed_model",
            "phonometry.building.measurement.uncertainty",
            "phonometry.building.measurement.floor_covering_improvement",
            "phonometry.building.prediction.resilient_layers",
            "phonometry.building.prediction.linings",
            "phonometry.building.measurement.structure_borne_power",
            "phonometry.building.prediction.installed_structure_borne",
            "phonometry.building.regulation.spain",
        ),
    ),
    Section(
        key="materials",
        label_en="Materials and surfaces",
        label_es="Materiales y superficies",
        modules=(
            "phonometry.materials.absorbers.sound_absorption",
            "phonometry.materials.absorbers.rating",
            "phonometry.materials.absorbers.uncertainty",
            "phonometry.materials.absorbers.airflow_resistance",
            "phonometry.materials.resilient.dynamic_stiffness",
            "phonometry.materials.resilient.moduli",
            "phonometry.materials.absorbers.impedance_tube",
            "phonometry.materials.absorbers.four_microphone",
            "phonometry.materials.absorbers.standing_wave",
            "phonometry.materials.absorbers.porous",
            "phonometry.materials.absorbers.catalogue",
            "phonometry.materials.absorbers.resistive_sheets",
            "phonometry.materials.absorbers.measured",
            "phonometry.materials.absorbers.carpets",
            "phonometry.materials.absorbers.layered",
            "phonometry.materials.absorbers.biot",
            "phonometry.materials.absorbers.slow_sound",
            "phonometry.materials.absorbers.suspended_ceilings",
            "phonometry.materials.diffusers.scattering_diffusion",
            "phonometry.materials.diffusers.reverberation_room_scattering",
            "phonometry.materials.diffusers.design",
            "phonometry.materials.diffusers.metadiffuser",
            "phonometry.materials.diffusers.measured_scattering",
            "phonometry.materials.diffusers.predicted_diffusion",
            "phonometry.materials.diffusers.predicted_scattering",
            "phonometry.materials.surfaces.road_absorption",
        ),
    ),
    Section(
        key="vibration",
        label_en="Vibration and structure-borne sound",
        label_es="Vibración y ruido estructural",
        modules=(
            "phonometry.vibration.structural.mechanical_mobility",
            "phonometry.vibration.structural.point_mobility",
            "phonometry.vibration.structural.radiation_efficiency",
            "phonometry.vibration.structural.junction_transmission",
            "phonometry.vibration.structural.experimental_sea",
            "phonometry.vibration.machinery.diagnostics",
            "phonometry.vibration.machinery.evaluation",
            "phonometry.vibration.structural.transfer_stiffness",
            "phonometry.vibration.structural.building_damage",
            "phonometry.vibration.structural.building_response",
            "phonometry.vibration.human.exposure",
            "phonometry.vibration.human.multiple_shock",
            "phonometry.vibration.human.seat_vibration",
            "phonometry.vibration.human.instrumentation",
            "phonometry.vibration.human.signal_burst",
            "phonometry.vibration.immission.vibration_meter",
            "phonometry.vibration.immission.railway",
            "phonometry.vibration.immission.ground",
            "phonometry.vibration.immission.coupling",
            "phonometry.vibration.immission.people",
            "phonometry.vibration.immission.train_categories",
            "phonometry.vibration.immission.railway_prediction",
            "phonometry.vibration.immission.prediction",
        ),
    ),
    Section(
        key="environment",
        label_en="Environmental acoustics",
        label_es="Acústica ambiental",
        modules=(
            "phonometry.environment.propagation.outdoor_propagation",
            "phonometry.environment.sources.cnossos_road",
            "phonometry.environment.propagation.ground_barriers",
            "phonometry.environment.propagation.ground_surfaces",
            "phonometry.environment.propagation.noise_reducing_devices",
            "phonometry.environment.propagation.barrier_in_situ",
            "phonometry.environment.propagation.refraction",
            "phonometry.environment.propagation.air_absorption",
            "phonometry.environment.sources.cnossos_rail",
            "phonometry.environment.assessment.impulsive_sound",
            "phonometry.environment.assessment.rating",
            "phonometry.environment.sources.wind_turbine",
            "phonometry.environment.assessment.measurement",
            "phonometry.environment.assessment.spain",
        ),
    ),
    Section(
        key="aeroacoustics",
        label_en="Aircraft noise",
        label_es="Ruido de aeronaves",
        modules=(
            "phonometry.aircraft.certification",
            "phonometry.aircraft.atmospheric_absorption",
            "phonometry.aircraft.airport_noise",
            "phonometry.aircraft.anp_fleet",
            "phonometry.aircraft.flight_performance",
            "phonometry.aircraft.rotorcraft_noise",
            "phonometry.aircraft.rotorcraft_propagation",
            "phonometry.aircraft.measurement_system",
        ),
    ),
    Section(
        key="underwater",
        label_en="Underwater acoustics",
        label_es="Acústica submarina",
        modules=(
            "phonometry.underwater.acoustics",
            "phonometry.underwater.propagation.closed_form",
            "phonometry.underwater.propagation.weston_regimes",
            "phonometry.underwater.propagation.sound_speed",
            "phonometry.underwater.sonar_equation",
            "phonometry.underwater.sources.ambient_noise",
            "phonometry.underwater.propagation.seabed_reflection",
            "phonometry.underwater.sources.ship_radiated_noise",
            "phonometry.underwater.sources.ship_traffic_noise",
            "phonometry.underwater.sources.pile_driving_noise",
            "phonometry.underwater.bioacoustics.audiograms",
            "phonometry.underwater.bioacoustics.weighting",
            "phonometry.underwater.propagation.numerical",
        ),
    ),
    Section(
        key="power",
        label_en="Sound power and intensity",
        label_es="Potencia acústica e intensidad",
        modules=(
            "phonometry.emission.sound_power",
            "phonometry.emission.sound_power_anechoic",
            "phonometry.emission.sound_power_intensity",
            "phonometry.emission.sound_power_intensity_points",
            "phonometry.emission.sound_power_reverberation",
            "phonometry.emission.sound_power_in_situ",
            "phonometry.emission.sound_power_in_duct",
            "phonometry.emission.intensity",
            "phonometry.emission.intensity_compliance",
            "phonometry.emission.vibration_sound_power",
            "phonometry.emission.workstation",
            "phonometry.emission.declaration",
        ),
    ),
    Section(
        key="electroacoustics",
        label_en="Electroacoustics",
        label_es="Electroacústica",
        modules=(
            "phonometry.electroacoustics.distortion",
            "phonometry.electroacoustics.intermodulation",
            "phonometry.electroacoustics.noise_measurements",
            "phonometry.electroacoustics.frequency_response",
            "phonometry.electroacoustics.swept_sine",
            "phonometry.electroacoustics.piston",
            "phonometry.electroacoustics.loudspeaker",
            "phonometry.electroacoustics.microphone",
            "phonometry.electroacoustics.sound_reinforcement",
        ),
    ),
    Section(
        key="noise_control",
        label_en="Industrial noise control",
        label_es="Control de ruido industrial",
        modules=(
            "phonometry.noise_control.silencers",
            "phonometry.noise_control.silencer_measurement",
            "phonometry.noise_control.hvac",
            "phonometry.noise_control.duct_path",
            "phonometry.noise_control.duct_modes",
            "phonometry.noise_control.duct_walls",
            "phonometry.noise_control.enclosures",
            "phonometry.noise_control.enclosure_insulation",
            "phonometry.noise_control.cabin_insulation",
            "phonometry.noise_control.silencer_in_situ",
            "phonometry.noise_control.screen_in_situ",
            "phonometry.noise_control.room_to_room",
            "phonometry.noise_control.valves",
            "phonometry.noise_control.valves_hydrodynamic",
        ),
    ),
    Section(
        key="broadcast",
        label_en="Broadcast metering",
        label_es="Medición en radiodifusión",
        modules=(
            "phonometry.broadcast.program_loudness",
            "phonometry.broadcast.quasi_peak",
        ),
    ),
    Section(
        key="simulation",
        label_en="Wave simulation",
        label_es="Simulación de ondas",
        modules=(
            "phonometry.simulation.fdtd",
            "phonometry.simulation.ntff",
            "phonometry.simulation.elastic_fdtd",
        ),
    ),
)

#: Sections in display order, keyed by section key.
SECTIONS: dict[str, Section] = {s.key: s for s in _SECTION_LIST}

#: Parent subpackages allowed per section (the hard consistency contract).
#: ``""`` is the package top level (``phonometry/__init__.py``). Sections
#: spanning more than one parent are deliberate and documented in the module
#: docstring above.
_SECTION_SUBPACKAGES: dict[str, tuple[str, ...]] = {
    "filters": ("", "filters"),
    # ``phonometry.io`` is documented as the package itself (two dotted
    # parts), which the parent derivation reports as the top level.
    "fluids": ("", "fluids"),
    "solids": ("solids",),
    "io": ("",),
    "signals": ("signals",),
    "psychoacoustics": ("psychoacoustics",),
    "speech": ("speech",),
    "hearing": ("hearing",),
    "rooms": ("room",),
    "building": ("building",),
    "materials": ("materials",),
    "vibration": ("vibration",),
    "environment": ("environment",),
    "aeroacoustics": ("aircraft",),
    "underwater": ("underwater",),
    "power": ("emission",),
    "electroacoustics": ("electroacoustics",),
    "noise_control": ("noise_control",),
    "broadcast": ("broadcast",),
    "metrology": ("metrology",),
    "simulation": ("simulation",),
}

#: Public names whose home module cannot be derived from ``__module__``:
#: objects defined in private modules but exported publicly, module-level
#: constants without ``__module__``, and constants re-exported by more than
#: one public module. Maps public name -> full module key in the taxonomy.
OBJECT_MODULE_OVERRIDES: dict[str, str] = {
    # Defined in phonometry/__init__.py (reported as module "phonometry").
    "__version__": "phonometry",
    # The fluid state type and its diagnostics are defined in the private
    # phonometry/fluids/_state.py and published by the package, which is where
    # they are documented.
    "Fluid": "phonometry.fluids",
    "FluidAssumptionWarning": "phonometry.fluids",
    "FluidPropertyUnavailable": "phonometry.fluids",
    "FluidWarning": "phonometry.fluids",
    "characteristic_impedance": "phonometry.fluids",
    # A Fluid instance reports its class's module, so the published air of
    # the Johnson-Champoux-Allard model is credited to fluids unless said
    # otherwise. It belongs to the model that publishes those constants.
    "PUBLISHED_AIR": "phonometry.materials.absorbers.porous",
    "ANNEX_A_AIR": "phonometry.materials.absorbers.airflow_resistance",
    "EN_12354_AIR": "phonometry.building.prediction.detailed_model",
    "SIMULATION_AIR": "phonometry.simulation.ntff",
    # The three assumed conditions are owned by the air model and re-exported
    # by the package, so a plain scan sees them in both.
    "DEFAULT_CO2_MOLE_FRACTION": "phonometry.fluids.air",
    "DEFAULT_RELATIVE_HUMIDITY_PERCENT": "phonometry.fluids.air",
    "DEFAULT_STATIC_PRESSURE_PA": "phonometry.fluids.air",
    # The speed of sound the critical-frequency columns are printed for is
    # owned by the module that uses it and re-exported by the package, the
    # same shape as the three above.
    "DEFAULT_SPEED_OF_SOUND_M_S": "phonometry.solids.elastic",
    # The published catalogue is a mapping, so a plain scan sees it in the
    # module that builds it and in the package that re-exports it.
    "PUBLISHED_DAMPING": "phonometry.solids.damping",
    "PUBLISHED_DAMPING_TREATMENTS": "phonometry.solids.damping_treatments",
    "PUBLISHED_SOLID_NONLINEARITY": "phonometry.solids.nonlinearity",
    "PUBLISHED_RESILIENT_MODULI": "phonometry.materials.resilient.moduli",
    "PUBLISHED_CARPETS": "phonometry.materials.absorbers.carpets",
    "PUBLISHED_ORTHOTROPIC_WOOD": "phonometry.solids.orthotropic_wood",
    "PUBLISHED_PLATEAU_DATA": "phonometry.solids.plateau",
    "PUBLISHED_DUCT_TRANSMISSION_LOSS": "phonometry.noise_control.duct_walls",
    "DUCT_WALL_BANDS_HZ": "phonometry.noise_control.duct_walls",
    "PUBLISHED_SOLIDS": "phonometry.solids.catalogue",
    "PUBLISHED_GROUND": "phonometry.environment.propagation.ground_surfaces",
    "PUBLISHED_POROUS": "phonometry.materials.absorbers.catalogue",
    "PUBLISHED_FLOW_RESISTANCE": "phonometry.materials.absorbers.resistive_sheets",
    "PUBLISHED_ABSORPTION": "phonometry.materials.absorbers.measured",
    "PUBLISHED_TRANSMISSION_LOSS": "phonometry.building.catalogue",
    "TRANSMISSION_LOSS_BANDS_HZ": "phonometry.building.catalogue",
    "TransmissionLossSpectrum": "phonometry.building.catalogue",
    "transmission_loss_named": "phonometry.building.catalogue",
    "PUBLISHED_IMPACT_INSULATION": "phonometry.building.impact_catalogue",
    "PUBLISHED_SCATTERING": "phonometry.materials.diffusers.measured_scattering",
    "SCATTERING_BANDS_HZ": "phonometry.materials.diffusers.measured_scattering",
    "ScatteringCoefficientSpectrum": "phonometry.materials.diffusers.measured_scattering",
    "scattering_named": "phonometry.materials.diffusers.measured_scattering",
    "PUBLISHED_DIFFUSION": "phonometry.materials.diffusers.predicted_diffusion",
    "DIFFUSION_BANDS_HZ": "phonometry.materials.diffusers.predicted_diffusion",
    "NormalizedDiffusionSpectrum": "phonometry.materials.diffusers.predicted_diffusion",
    "diffusion_named": "phonometry.materials.diffusers.predicted_diffusion",
    "PUBLISHED_PREDICTED_SCATTERING": "phonometry.materials.diffusers.predicted_scattering",
    "PredictedScatteringSpectrum": "phonometry.materials.diffusers.predicted_scattering",
    "predicted_scattering_named": "phonometry.materials.diffusers.predicted_scattering",
    "PUBLISHED_ABSORPTION_AREAS": "phonometry.materials.absorbers.measured",
    "PUBLISHED_FLUIDS": "phonometry.fluids.catalogue",
    "PUBLISHED_GASES": "phonometry.fluids.catalogue",
    "PUBLISHED_NONLINEARITY": "phonometry.fluids.nonlinearity",
    "Gas": "phonometry.fluids.catalogue",
    "gases_named": "phonometry.fluids.catalogue",
    # The ideal-gas closure and its two published constants are owned by the
    # module that computes with them and re-exported by the package.
    "IDEAL_GAS_VALIDITY": "phonometry.fluids.gas",
    "MOLAR_GAS_CONSTANT": "phonometry.fluids.gas",
    "ideal_gas": "phonometry.fluids.gas",
    # The band ranges, the leak ratio and the seal ratio are printed in the
    # same words by ISO 11546 and ISO 11957, so they are defined once and
    # re-exported by both modules, and a plain scan sees them twice. The
    # enclosure is the older document and owns them.
    "MANDATORY_BAND_RANGE_HZ": "phonometry.noise_control.enclosure_insulation",
    "PREFERRED_BAND_RANGE_HZ": "phonometry.noise_control.enclosure_insulation",
    "leak_ratio": "phonometry.noise_control.enclosure_insulation",
    # ISO 11957 prints the operator sphere first and ISO 11821 reuses it, so
    # the cabin module owns the constant and the screen module imports it.
    "OPERATOR_SPHERE_RADIUS_M": "phonometry.noise_control.cabin_insulation",
    "seal_ratio": "phonometry.noise_control.enclosure_insulation",
    # The two sound speeds and the jet diameter are owned by the aerodynamic
    # valve module and imported by the hydrodynamic one, which IEC 60534-8-4
    # sends to IEC 60534-8-3 for all three, so a plain scan sees them twice.
    "AIR_SOUND_SPEED_M_S": "phonometry.noise_control.valves",
    "PIPE_SOUND_SPEED_M_S": "phonometry.noise_control.valves",
    "jet_diameter_m": "phonometry.noise_control.valves",
    # The running r.m.s. time constant is owned by the DIN 45669-1 meter and
    # imported by the DIN 45672-2 evaluation, whose Formula (1) is the same
    # integral with the same "Fast", so a plain scan sees it in both.
    "KB_TIME_CONSTANT_S": "phonometry.vibration.immission.vibration_meter",
    # The KB corner and the clock interval are the meter's, and the DIN 4150-2
    # assessment imports them for Formula (6) and the interval count N_r.
    "KB_CORNER_HZ": "phonometry.vibration.immission.vibration_meter",
    "TAKT_DURATION_S": "phonometry.vibration.immission.vibration_meter",
    "TAKT_SUPPRESSION_THRESHOLD": "phonometry.vibration.immission.vibration_meter",
    # The draft railway assessment and the draft prediction share names
    # with the people module, the meter and the Part 2 evaluation.
    "ASSESSMENT_TAKT_COUNT": "phonometry.vibration.immission.people",
    "GUIDE_VALUES": "phonometry.vibration.immission.people",
    "GUIDE_VALUES_2023": "phonometry.vibration.immission.people",
    "GuideValues": "phonometry.vibration.immission.people",
    "TRAIN_KB_FMAX_FACTOR": "phonometry.vibration.immission.train_categories",
    "VELOCITY_LEVEL_REFERENCE_MM_S": "phonometry.vibration.immission.railway",
    "band_sum_level": "phonometry.vibration.immission.railway",
    # The ERB_N / Cam constants are owned by erb_scale and imported by the
    # ISO 532-2 loudness model, so a plain scan sees them in both modules.
    "ERB_C1": "phonometry.psychoacoustics.erb_scale",
    "ERB_C2": "phonometry.psychoacoustics.erb_scale",
    "CAM_C": "phonometry.psychoacoustics.erb_scale",
    # The tapping-machine hammer mass is owned by resilient_layers and imported
    # by installed_structure_borne, where EN 12354-5 clause D.1.3 uses the same
    # 0,5 kg as the source mass of Formula (D.9b), so a plain scan sees it in
    # both modules.
    "TAPPING_HAMMER_MASS": "phonometry.building.prediction.resilient_layers",
    # The ISO 20816-1 tables and factors are plain containers, so a scan
    # by module finds no owner for them; they belong to the evaluation
    # module that publishes them.
    "TYPICAL_BOUNDARY_LADDER_MM_S": "phonometry.vibration.machinery.evaluation",
    "TYPICAL_ZONE_BOUNDARY_RANGES_MM_S": "phonometry.vibration.machinery.evaluation",
    "ZONE_LIMIT_FACTORS": "phonometry.vibration.machinery.evaluation",
    # Likewise the ISO 10816-3 tables and the two fractions its operational
    # limits are built from.
    "INDUSTRIAL_MACHINE_ZONES": "phonometry.vibration.machinery.evaluation",
    "SIGNIFICANT_CHANGE_FRACTION": "phonometry.vibration.machinery.evaluation",
    "OPERATIONAL_LIMIT_HEADROOM": "phonometry.vibration.machinery.evaluation",
    # And the ISO 20816-9 rating tables, curve corners and slopes.
    "GEAR_UNIT_ZONES": "phonometry.vibration.machinery.evaluation",
    "GEAR_UNIT_CLASSES": "phonometry.vibration.machinery.evaluation",
    "GEAR_ACCEPTANCE_HEADROOM": "phonometry.vibration.machinery.evaluation",
    "GEAR_DISPLACEMENT_CORNER_HZ": "phonometry.vibration.machinery.evaluation",
    "GEAR_DISPLACEMENT_SLOPE_DB_PER_DECADE": "phonometry.vibration.machinery.evaluation",
    "GEAR_VELOCITY_CORNERS_HZ": "phonometry.vibration.machinery.evaluation",
    "GEAR_VELOCITY_SLOPE_DB_PER_DECADE": "phonometry.vibration.machinery.evaluation",
    # The nine weighting names are owned by the exposure module and imported
    # by the instrumentation one, which grades a meter against those same
    # nine, so a plain scan sees them in both.
    "WEIGHTING_NAMES": "phonometry.vibration.human.exposure",
    # The ISO 8041-1 tolerance tables are plain containers too, so a scan by
    # module finds no owner; they belong to the instrumentation module that
    # publishes them.
    "TRANSITION_FREQUENCIES_HZ": "phonometry.vibration.human.instrumentation",
    "CENTRAL_TOLERANCE_PERCENT": "phonometry.vibration.human.instrumentation",
    "SKIRT_TOLERANCE_PERCENT": "phonometry.vibration.human.instrumentation",
    "TAIL_TOLERANCE_PERCENT": "phonometry.vibration.human.instrumentation",
    "REFERENCE_FREQUENCY_HZ": "phonometry.vibration.human.instrumentation",
    "REFERENCE_ACCELERATION_M_S2": "phonometry.vibration.human.instrumentation",
    # The ISO 1683 table is a mapping, so a scan by module finds no owner for
    # it; it belongs to the module that publishes it, which is where every
    # private reference value in the package points.
    "ISO1683_REFERENCE_VALUES": "phonometry.metrology.reference_values",
    # Defined in phonometry._internal.warnings, exported at the top level.
    "PhonometryWarning": "phonometry",
    # The io subpackage keeps its implementation modules private and
    # re-exports everything from phonometry/io/__init__.py, so every one of
    # its public names reports a private ``__module__`` and is documented
    # with the package itself.
    "AudioFileInfo": "phonometry.io",
    "BroadcastMetadata": "phonometry.io",
    "CalibrationSidecar": "phonometry.io",
    "ClippingWarning": "phonometry.io",
    "CuePoint": "phonometry.io",
    "LossyCompressionWarning": "phonometry.io",
    "Signal": "phonometry.io",
    "SignalOrigin": "phonometry.io",
    "convert": "phonometry.io",
    "info": "phonometry.io",
    "read": "phonometry.io",
    "read_blocks": "phonometry.io",
    "read_sidecar": "phonometry.io",
    "sidecar_path": "phonometry.io",
    "write": "phonometry.io",
    "write_sidecar": "phonometry.io",
    # Defined in phonometry.emission._shared, where the three sound power
    # standards share it; documented with the free-field method that raises it
    # most often.
    "SoundPowerWarning": "phonometry.emission.sound_power",
    # The ISO 9614-1 Table B.3 limit on F1, defined beside the F1 it bounds and
    # imported by the discrete-point determination that gates on it.
    "TEMPORAL_VARIABILITY_LIMIT": "phonometry.emission.intensity",
    # A typing.Literal alias, so it reports "typing" as its module; documented
    # with the declaration whose `form` argument it types.
    "DeclarationForm": "phonometry.emission.declaration",
    # Defined in phonometry._plot.room; documented helper for the ISO 18233
    # excitation signals that live in room.impulse_response.
    "plot_excitation": "phonometry.room.impulse_response",
    # Defined in phonometry._plot.geometry; documented with the materials
    # module whose devices each drawing depicts.
    "plot_absorber_stack": "phonometry.materials.absorbers.porous",
    "plot_helmholtz_resonator_geometry": "phonometry.materials.absorbers.slow_sound",
    "plot_slit_absorber_geometry": "phonometry.materials.absorbers.slow_sound",
    "plot_qrd_geometry": "phonometry.materials.diffusers.design",
    "plot_metadiffuser_panel_geometry": "phonometry.materials.diffusers.metadiffuser",
    "DEFAULT_POLAR_ANGLES": "phonometry.materials.diffusers.design",
    "plot_impedance_tube_geometry": "phonometry.materials.absorbers.impedance_tube",
    "plot_transmission_tube_geometry": "phonometry.materials.absorbers.impedance_tube",
    "plot_silencer_geometry": "phonometry.noise_control.silencers",
    "plot_plenum_geometry": "phonometry.noise_control.hvac",
    "plot_barrier_geometry": "phonometry.environment.propagation.ground_barriers",
    "plot_microphone_positions": "phonometry.emission.sound_power",
    "plot_aperture_geometry": "phonometry.building.prediction.aperture_transmission",
    "plot_piston_geometry": "phonometry.electroacoustics.piston",
    "plot_sound_reinforcement_geometry": "phonometry.electroacoustics.sound_reinforcement",
    "plot_facade_elements": "phonometry.building.prediction.facade",
    "plot_double_wall_geometry": "phonometry.building.prediction.panel_transmission",
    "plot_junction_geometry": "phonometry.vibration.structural.junction_transmission",
    "plot_insitu_geometry": "phonometry.materials.surfaces.road_absorption",
    "plot_dynamic_stiffness_rig": "phonometry.materials.resilient.dynamic_stiffness",
    "plot_goniometer_geometry": "phonometry.materials.diffusers.scattering_diffusion",
    "plot_plate_geometry": "phonometry.vibration.structural.radiation_efficiency",
    "plot_open_plan_geometry": "phonometry.room.open_plan",
    "plot_pp_probe_geometry": "phonometry.emission.intensity",
    # Defined in underwater.acoustics, also re-exported by
    # underwater.ship_radiated_noise (identity scan is ambiguous).
    "UNDERWATER_REFERENCE_PRESSURE": "phonometry.underwater.acoustics",
    # Defined in the private phonometry._report package; documented with the
    # building insulation ratings whose report() method it drives.
    "ReportMetadata": "phonometry.building.measurement.insulation",
}


def module_section(module: str) -> Section:
    """Return the section that documents ``module`` (full dotted name).

    :param module: Full module name, e.g. ``"phonometry.signals.levels"``.
    :raises KeyError: If the module is not mapped; new public modules must be
        added to a section in ``scripts/api_taxonomy.py``.
    """
    section = _MODULE_TO_SECTION.get(module)
    if section is None:
        msg = (
            f"module {module!r} is not mapped to any API-reference section; "
            "add it to the matching Section in scripts/api_taxonomy.py"
        )
        raise KeyError(msg)
    return section


def _parent_subpackage(module: str) -> str:
    """``phonometry.signals.levels`` -> ``signals``; top level -> ``""``."""
    parts = module.split(".")
    return parts[1] if len(parts) > 2 else ""


def _build_module_index() -> dict[str, Section]:
    index: dict[str, Section] = {}
    for section in _SECTION_LIST:
        allowed = _SECTION_SUBPACKAGES[section.key]
        for module in section.modules:
            if module in index:
                msg = (
                    f"module {module!r} is assigned to both "
                    f"{index[module].key!r} and {section.key!r}"
                )
                raise ValueError(msg)
            parent = _parent_subpackage(module)
            if parent not in allowed:
                msg = (
                    f"module {module!r} (subpackage {parent!r}) does not "
                    f"belong to section {section.key!r}, which only accepts "
                    f"subpackages {allowed!r}"
                )
                raise ValueError(msg)
            index[module] = section
    for name, module in OBJECT_MODULE_OVERRIDES.items():
        if module not in index:
            msg = (
                f"OBJECT_MODULE_OVERRIDES[{name!r}] points to unmapped "
                f"module {module!r}"
            )
            raise ValueError(msg)
    return index


_MODULE_TO_SECTION: dict[str, Section] = _build_module_index()


def public_names() -> dict[str, ModuleType]:
    """Every public name in the library, mapped to the package that owns it.

    Since 4.0 the top level publishes the twenty-one domain packages and the
    four names that belong to no domain, and a function is reached through its
    package. "The public API" is therefore the union of the domain ``__all__``
    plus those four, which is what the coverage gate walks and what the
    generator renders. Reading ``phonometry.__all__`` instead would now see
    twenty-four names and call the other thirteen hundred private.

    The value is the module to read the name off, which is the owning package
    for a domain name and ``phonometry`` itself for the four at the top.
    """
    import phonometry

    packages = [
        getattr(phonometry, name)
        for name in phonometry.__all__
        if inspect.ismodule(getattr(phonometry, name))
    ]
    owners: dict[str, ModuleType] = {}
    for package in packages:
        for member in getattr(package, "__all__", ()):
            previous = owners.get(member)
            if previous is not None:
                msg = (
                    f"{member!r} is published by both {previous.__name__} and "
                    f"{package.__name__}; one name, one owner"
                )
                raise ValueError(msg)
            owners[member] = package
    # The names the top level holds itself, which is every one it publishes
    # that no package does. `Signal` is not among them: it is published at the
    # top level and by `phonometry.io`, which owns it, and the top-level
    # re-export is a shortcut to the same object.
    for name in phonometry.__all__:
        attribute = getattr(phonometry, name)
        if not inspect.ismodule(attribute) and name not in owners:
            owners[name] = phonometry
    return owners
