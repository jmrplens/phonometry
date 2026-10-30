#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A record converts what it is handed, and travels whole.

A record a caller builds takes a list, a tuple or an array of any dtype for
a field its constructor declares ``ArrayLike`` (``tests/test_record_
constructors.py``), and holds what the field says: a read-only array, a
tuple, a pair of numbers. Kept as given, a list would make the record's own
arithmetic list arithmetic (``[a, b] * 2`` repeats it) and stay open to an
``append`` inside a frozen record. So, for every record the result factories
of the plot tests build and every record a caller builds by hand below, each
field the record stores a value of its own in (as
``scripts/check_parameter_annotations.py`` reads it) is given a list and
must come back as something else, and a sequence field stored as a tuple is
given an array and must come back as a tuple.

Every one of them also survives ``pickle`` and ``copy.deepcopy``: a record
that holds a read-only mapping travels as plain dictionaries
(``__reduce__``), or a process pool or a cache cannot take it.
"""

from __future__ import annotations

import collections
import copy
import dataclasses
import inspect
import pathlib
import pickle
import sys
import warnings
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
import result_factories
from array_likes import ARRAY_LIKES

import phonometry as ph
from phonometry._internal.catalogue import BandedRow, CatalogueRow
from phonometry.io._sidecar import CalibrationSidecar

if TYPE_CHECKING:
    from collections.abc import Callable

    from numpy.typing import ArrayLike

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_parameter_annotations as cpa
import check_return_overloads as overloads
from ast_scan import ROOT, python_files

_SOURCE = ROOT / "src" / "phonometry"

_BANDS = [100.0, 125.0, 160.0]


def _hemisphere() -> object:
    return ph.aircraft.RotorcraftHemisphere(
        frequencies=[100.0, 200.0],
        azimuth_deg=[-90.0, 90.0],
        polar_deg=[0.0, 90.0, 180.0],
        levels=[[[90.0, 80.0]] * 3] * 2,
    )


def _npd_curves() -> object:
    return ph.aircraft.ANPNPDCurves(
        aircraft_id="JET",
        npd_id="JET",
        metric="SEL",
        operation="D",
        power_parameter="CNT (lb)",
        powers=[10000.0, 20000.0],
        distances_m=[61.0, 122.0, 244.0],
        levels=[[95.0, 90.0, 85.0], [100.0, 95.0, 90.0]],
    )


#: A record a caller builds that converts a field, built here from lists.
_HAND_BUILT: dict[str, Callable[[], object]] = {
    "FlightSegmentState": lambda: ph.aircraft.FlightSegmentState(
        ground_roll=[True, False], landing_roll=[False, False], bank=[0.0, 5.0]
    ),
    "ANPNPDCurves": _npd_curves,
    "FlightConditionInterpolation": lambda: ph.aircraft.FlightConditionInterpolation(
        triangles=[[0, 1, 2]]
    ),
    "RotorcraftGround": lambda: ph.aircraft.RotorcraftGround(
        ground_elevation=[0.0, 1.0],
        flow_resistivity=[200.0, 20000.0],
    ),
    "RotorcraftHemisphere": _hemisphere,
    "RotorcraftTrackState": lambda: ph.aircraft.RotorcraftTrackState(
        airspeed=[40.0, 41.0],
        path_angle_deg=[0.0, -3.0],
        heading=[90.0, 90.0],
        bank_angle_deg=[0.0, 0.0],
    ),
    "LowFrequencyProcedure": lambda: ph.building.LowFrequencyProcedure(
        volume=18.0,
        corner_levels=[[70.0, 71.0, 72.0], [69.0, 70.0, 71.0]],
        reverberation_63_octave=0.6,
    ),
    "BandPath": lambda: ph.building.BandPath(
        label="Dd", kind="Dd", values=[50.0, 52.0, 54.0]
    ),
    "FacadeElement": lambda: ph.building.FacadeElement(
        name="wall", area=10.0, r=[40.0, 41.0, 42.0]
    ),
    "LoudspeakerDirectivity": lambda: ph.electroacoustics.LoudspeakerDirectivity(
        polar=[[0.0, 90.0, 180.0], [0.0, -6.0, -12.0]], frequency=1000.0
    ),
    "LoudspeakerRatings": lambda: ph.electroacoustics.LoudspeakerRatings(
        frequency_range=[50.0, 20000.0]
    ),
    "MicrophoneDirectivity": lambda: ph.electroacoustics.MicrophoneDirectivity(
        polar=[[0.0, 90.0, 180.0], [0.0, -6.0, -20.0]], frequency=1000.0
    ),
    "MicrophoneNoise": lambda: ph.electroacoustics.MicrophoneNoise(
        spectrum=[[100.0, 1000.0], [10.0, 8.0]]
    ),
    "MicrophoneOverload": lambda: ph.electroacoustics.MicrophoneOverload(
        distortion=[[120.0, 130.0, 140.0], [0.1, 0.5, 3.0]]
    ),
    "MicrophoneTraverse": lambda: ph.emission.MicrophoneTraverse(
        positions_m=[[0.0, 0.0, 1.0], [0.0, 0.0, 2.0], [0.0, 0.0, 4.0]],
        levels=[[94.0], [88.0], [82.0]],
    ),
    "RoomEnvironment": lambda: ph.emission.RoomEnvironment(
        absorption_area=[30.0, 35.0, 40.0]
    ),
    "AtmosphericAttenuation": lambda: ph.environment.AtmosphericAttenuation(
        [500.0, 1000.0], [0.002, 0.005], 20.0, 70.0, 101.325
    ),
    "RailSourceSpectra": lambda: ph.environment.RailSourceSpectra(
        source_a=[80.0] * 24, source_b=[70.0] * 24
    ),
    "WavelengthSpectrum": lambda: ph.environment.WavelengthSpectrum(
        wavelengths_mm=[2000.0, 1600.0], levels=[5.0, 4.0]
    ),
    "RollingStock": lambda: ph.environment.RollingStock(
        n_axles=4,
        wheel_roughness=ph.environment.WavelengthSpectrum(
            wavelengths_mm=[2000.0], levels=[5.0]
        ),
        contact_filter=ph.environment.WavelengthSpectrum(
            wavelengths_mm=[2000.0], levels=[0.0]
        ),
        wheel_transfer=[80.0] * 24,
        superstructure_transfer=[70.0] * 24,
    ),
    "RailwayTrack": lambda: ph.environment.RailwayTrack(
        rail_roughness=ph.environment.WavelengthSpectrum(
            wavelengths_mm=[2000.0], levels=[5.0]
        ),
        track_transfer=[80.0] * 24,
        bridge_transfer=[3.0] * 24,
    ),
    "RoadEmissionCoefficients": lambda: ph.environment.RoadEmissionCoefficients(
        rolling_a=ph.environment.ROAD_COEFFICIENTS.rolling_a,
        rolling_b=ph.environment.ROAD_COEFFICIENTS.rolling_b,
        propulsion_a=ph.environment.ROAD_COEFFICIENTS.propulsion_a,
        propulsion_b=ph.environment.ROAD_COEFFICIENTS.propulsion_b,
        studded_a=list(ph.environment.ROAD_COEFFICIENTS.studded_a),
        studded_b=list(ph.environment.ROAD_COEFFICIENTS.studded_b),
        junction_c=ph.environment.ROAD_COEFFICIENTS.junction_c,
        temperature_coefficient_db_per_k=(
            ph.environment.ROAD_COEFFICIENTS.temperature_coefficient_db_per_k
        ),
    ),
    "RoadSurfaceCoefficients": lambda: ph.environment.RoadSurfaceCoefficients(
        name="national surface",
        alpha={"1": (0.0,) * 8},
        beta={"1": 0.0},
        speed_range_kmh=[50.0, 130.0],
    ),
    "FilterPeriodicMeasurements": lambda: ph.filters.FilterPeriodicMeasurements(
        midband_attenuations=[0.1, -0.2, 0.05],
        midband_uncertainties_db=[0.15, 0.15, 0.25],
    ),
    "Task": lambda: ph.hearing.Task(
        samples=[85.0, 86.0, 87.0],
        duration_hours=2.0,
        duration_observations_hours=[1.5, 2.0, 2.5],
        duration_range_hours=[1.0, 3.0],
    ),
    "CalibrationSidecar": lambda: CalibrationSidecar(
        calibration_factor=0.5, channel_labels=["L", "R"]
    ),
    "Signal": lambda: ph.Signal(
        [[0.0, 0.1, 0.2], [0.0, -0.1, -0.2]], 48000.0, channel_labels=["L", "R"]
    ),
    "TransferMatrix": lambda: ph.materials.TransferMatrix(
        [1.0, 1.0], [0.0, 0.0], [0.0, 0.0], [1.0, 1.0], frequencies=[500.0, 1000.0]
    ),
    "FiberResistivityFit": lambda: ph.materials.FiberResistivityFit(
        k1=353.0,
        k2=0.63,
        fiber_diameter_um=4.75,
        bulk_density_range_kg_m3=[31.0, 155.0],
        direction="lateral",
        source="a fit by hand",
    ),
    "MetadiffuserWell": lambda: ph.materials.MetadiffuserWell(
        slit_height_m=0.01,
        resonators=[
            ph.materials.HelmholtzResonator(
                neck_length_m=0.01,
                neck_side_m=0.004,
                cavity_length_m=0.02,
                cavity_side_m=0.02,
            )
        ],
    ),
    "SoundCalibratorMeasurements": lambda: ph.metrology.SoundCalibratorMeasurements(
        level_deviation_db=[0.12, 0.10],
        level_uncertainty_db=[0.10, 0.10],
    ),
    "SoundLevelMeterPeriodicMeasurements": lambda: (
        ph.metrology.SoundLevelMeterPeriodicMeasurements(
            acoustic_weighting_deviations_db=[0.3, -1.2],
            acoustic_weighting_uncertainties_db=[0.3, 0.5],
            linearity_deviations_db=[0.0, 0.2, -0.3],
            linearity_uncertainties_db=[0.2, 0.2, 0.2],
        )
    ),
    "ContourPhasors": lambda: ph.simulation.ContourPhasors(
        frequency=500.0,
        positions=[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
        normals=[[0.0, -1.0], [1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]],
        pressure=[1.0 + 0.0j] * 4,
        normal_velocity=[0.01 + 0.0j] * 4,
        segment=1.0,
    ),
    "AnimationFrame": lambda: ph.simulation.AnimationFrame(size=[960, 540]),
    "ImpulseResponseResult": lambda: ph.room.ImpulseResponseResult(
        ir=[1.0, 0.5, 0.25], fs=48000.0, method="farina"
    ),
    "TransferStiffnessResult": lambda: ph.vibration.TransferStiffnessResult(
        frequencies=[100.0, 200.0],
        transfer_stiffness=[1.0e6 + 1.0e4j, 1.0e6 + 2.0e4j],
        blocking_mass=8.0,
        transmissibility=[0.01, 0.02],
    ),
    "MultipleShockResult": lambda: ph.vibration.MultipleShockResult(
        sex="male",
        acceleration_dose=89.4,
        daily_dose=89.4,
        compression_dose=0.4,
        risk=1.22,
        probability=0.37,
        start_age=20.0,
        exposure_duration_years=20,
        days_per_year=120.0,
        peaks=[40.0] * 5,
        risk_thresholds=[0.72, 1.42, 2.17],
    ),
}


_ABSORPTION_BANDS = (
    *(100, 125, 160, 200, 250, 315, 400, 500, 630),
    *(800, 1000, 1250, 1600, 2000, 2500, 3150, 4000, 5000),
)
_OCTAVES = (125, 250, 500, 1000, 2000, 4000)


def _per_band(name: str, bands: tuple[int, ...], value: float) -> dict[str, Any]:
    """One field per band, ``<name>_<band>``, each holding *value*, to unpack."""
    return {f"{name}_{band}": value for band in bands}


def _catalogue() -> object:
    return ph.io.parse_catalogue(
        {
            "schema": "phonometry-catalogue",
            "schema_version": 1,
            "catalogue": "tiles",
            "row_type": "AbsorptionSpectrum",
            "about": "A sheet written by hand.",
            "provenance": {
                "kind": "datasheet",
                "document": "Example tile data sheet",
                "version": None,
                "consulted": "2026-09-25",
            },
            "basis": "measured",
            "rows": [
                {
                    "key": "tile",
                    "name": "Tile",
                    **{f"absorption_coefficient_{band}": 0.5 for band in _OCTAVES},
                }
            ],
        },
        row_type=ph.materials.AbsorptionSpectrum,
    )


def _facade() -> object:
    return ph.building.facade_sound_reduction(
        [ph.building.FacadeElement(name="wall", area=10.0, r=[40.0, 45.0])],
        area=10.0,
        volume=50.0,
        frequencies=[500.0, 1000.0],
        fraction=1,
    )


def _railway_emission() -> object:
    stock = _HAND_BUILT["RollingStock"]()
    track = _HAND_BUILT["RailwayTrack"]()
    assert isinstance(stock, ph.environment.RollingStock)
    assert isinstance(track, ph.environment.RailwayTrack)
    return ph.environment.railway_source_power(
        ph.environment.RailwayVehicle(stock=stock, flow_rate=10.0, speed_kmh=80.0),
        track,
    )


def _time_varying_loudness() -> object:
    times = np.arange(3200) / 32000.0
    return ph.psychoacoustics.loudness_moore_glasberg_time(
        0.02 * np.sin(2.0 * np.pi * 1000.0 * times), 32000.0, percentiles=(5.0, 50.0)
    )


#: A record that holds a mapping, one of each, for the round trip: a
#: ``MappingProxyType`` can be neither pickled nor deep-copied, so each must
#: say how it travels.
_MAPPING_HOLDERS: dict[str, Callable[[], object]] = {
    "CatalogueRow": lambda: CatalogueRow(name="a row", source="by hand"),
    "BandedRow": lambda: BandedRow(name="a row", source="by hand"),
    "Provenance": lambda: ph.io.Provenance(
        kind="publication", document="A book", version=None, consulted="2026-09-25"
    ),
    "Catalogue": _catalogue,
    "PerformanceAircraft": lambda: ph.aircraft.PerformanceAircraft(
        aircraft_id="JET",
        n_engines=2,
        max_static_thrust_lb=25000.0,
        max_landing_weight_lb=140000.0,
        jet_coefficients={
            "MaxTakeoff": ph.aircraft.JetEngineCoefficients(
                e=25000.0, f=-25.0, ga=0.0, gb=1.0e-5, h=0.0
            )
        },
    ),
    "AircraftSystemComplianceResult": lambda: (
        ph.aircraft.AircraftSystemComplianceResult(resolution=0.5)
    ),
    "SoundReductionSpectrum": lambda: ph.building.SoundReductionSpectrum(
        name="partition",
        source="a report",
        **_per_band("sound_reduction_index", (50, 63, 80, *_ABSORPTION_BANDS), 30.0),
    ),
    "ImpactImprovementSpectrum": lambda: ph.building.ImpactImprovementSpectrum(
        name="covering",
        source="a report",
        **_per_band("impact_improvement", _ABSORPTION_BANDS[:16], 10.0),
    ),
    "ThirdOctaveAbsorptionSpectrum": lambda: ph.materials.ThirdOctaveAbsorptionSpectrum(
        name="panel",
        source="a report",
        **_per_band("absorption_coefficient", _ABSORPTION_BANDS, 0.5),
    ),
    "PracticalAbsorptionSpectrum": lambda: ph.materials.PracticalAbsorptionSpectrum(
        name="panel",
        source="a sheet",
        **_per_band("practical_absorption_coefficient", _OCTAVES, 0.5),
    ),
    "OperatingCondition": lambda: ph.building.OperatingCondition(
        clause="B.9",
        equipment="a tap",
        max_level=True,
        equivalent_level=True,
        conditions="normal use",
        max_cycle=None,
        equivalent_cycle=None,
        nominal_integration_time_s=None,
        parameters={"x_m": 1.0},
    ),
    "SoundscapeAcousticEnvironment": lambda: (
        ph.environment.SoundscapeAcousticEnvironment(
            environment_type="real",
            sound_sources="traffic",
            weather_and_wind="dry",
            time_of_year_and_day="May, noon",
            measurement_points="one point",
            measurement_results=dict.fromkeys(
                ("LAeq,T", "LCeq,T", "LAF5,T", "LAF95,T", "N5", "N95", "Nrmc"), 60.0
            ),
            site_description="street",
        )
    ),
    "FilterComplianceResult": lambda: ph.filters.verify_filter_class(
        ph.filters.OctaveFilterBank(fs=48000, fraction=1, order=6, limits=[125, 4000])
    ),
    "WeightingComplianceResult": lambda: ph.filters.verify_weighting_class(
        ph.filters.WeightingFilter(48000, "B")
    ),
    "FDTDBoundaries": lambda: ph.simulation.FDTDBoundaries(
        sides={"top": "absorbing"}, absorbing_layer_cells=10
    ),
    "ElasticBoundaries": lambda: ph.simulation.ElasticBoundaries(
        sides={"top": "absorbing"}
    ),
    "FacadePredictionResult": _facade,
    "RailwayEmissionResult": _railway_emission,
    "ReactiveSilencerResult": lambda: ph.noise_control.silencers.expansion_chamber(
        [100.0, 200.0], 0.5, 0.08, 0.01
    ),
    "MooreGlasbergTimeVaryingLoudness": _time_varying_loudness,
}


def _factory_records() -> list[object]:
    """One record from each result factory of the plot tests."""
    found: list[object] = []
    for name, factory in list(vars(result_factories).items()):
        if not (
            inspect.isfunction(factory)
            and factory.__module__ == result_factories.__name__
            and name.startswith("_")
        ):
            continue
        parameters = inspect.signature(factory).parameters.values()
        if any(p.default is p.empty and p.kind != p.VAR_KEYWORD for p in parameters):
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            record = factory()
        if dataclasses.is_dataclass(record) and not isinstance(record, type):
            found.append(record)
    return found


@pytest.fixture(scope="module")
def reader() -> cpa.Reader:
    package = overloads.Package(python_files([], _SOURCE), _SOURCE)
    return cpa.Reader(package)


def _held(records: list[object]) -> list[object]:
    """The records, and every record each holds, at any depth, each once."""
    found: dict[int, object] = {}
    stack: list[object] = list(records)
    while stack:
        value = stack.pop()
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            # A record first: one may be a mapping of its rows too.
            if id(value) not in found:
                found[id(value)] = value
                stack.extend(
                    getattr(value, each.name)
                    for each in dataclasses.fields(value)
                    if hasattr(value, each.name)
                )
        elif isinstance(value, Mapping):
            stack.extend(value.values())
        elif isinstance(value, tuple | list):
            stack.extend(value)
    return list(found.values())


def _published_rows() -> list[object]:
    """One row of each catalogue row class the domains publish."""
    from phonometry._internal.catalogue import CatalogueRow

    rows: dict[type, object] = {}
    for name in sorted(dir(ph)):
        domain = getattr(ph, name)
        if name.startswith("_") or not inspect.ismodule(domain):
            continue
        for exported in getattr(domain, "__all__", ()):
            for value in _held([getattr(domain, exported)]):
                if isinstance(value, CatalogueRow):
                    rows.setdefault(type(value), value)
    return list(rows.values())


@pytest.fixture(scope="module")
def records() -> list[object]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        built = [
            build() for build in (*_HAND_BUILT.values(), *_MAPPING_HOLDERS.values())
        ]
    fluid = ph.fluids.air(
        temperature_c=20.0, static_pressure_pa=101325.0, relative_humidity_percent=50.0
    )
    return _held([*built, fluid, *_factory_records(), *_published_rows()])


def _dotted(record: object) -> str:
    return f"{type(record).__module__}.{type(record).__qualname__}"


def test_every_record_a_caller_builds_that_converts_is_built_here(
    reader: cpa.Reader, records: list[object]
) -> None:
    """A converting record a caller builds is held to the rule by an instance."""
    covered = {_dotted(record) for record in records}
    gpu_files = set(cpa.gpu_parity_files())
    missing = []
    for record in cpa.built_records(reader):
        module = reader.annotations.classes[record][0]
        if cpa.repository_path(reader.package.paths[module], _SOURCE) in gpu_files:
            continue
        if cpa.stub_exemption(reader, record) or record in covered:
            continue
        fields = cpa.record_fields(reader.package, reader.annotations, record)
        if any(
            cpa.fixed_containers(
                reader.annotations, fields[name].module, fields[name].annotation
            )
            for name in cpa.converted_fields(reader, record)
        ):
            missing.append(record)
    assert sorted(missing) == []


#: Records of the package that hold a mapping no instance is built of here,
#: with the reason.
MAPPING_HOLDERS_UNBUILT: dict[str, str] = {}


def _published_records() -> dict[str, type]:
    """Every dataclass a domain package (or the root) publishes, by dotted name."""
    owners = [ph] + [
        getattr(ph, name)
        for name in sorted(dir(ph))
        if not name.startswith("_") and inspect.ismodule(getattr(ph, name))
    ]
    return {
        f"{cls.__module__}.{cls.__qualname__}": cls
        for owner in owners
        for name in getattr(owner, "__all__", ())
        if inspect.isclass(cls := getattr(owner, name))
        and dataclasses.is_dataclass(cls)
    }


def test_every_record_holding_a_mapping_is_built_here(
    reader: cpa.Reader, records: list[object]
) -> None:
    """A published record whose field names a mapping travels under test.

    ``MappingProxyType`` can be neither pickled nor deep-copied, so a record
    that holds one fails ``pickle`` and ``copy.deepcopy`` unless it says how
    to travel; reading its source cannot tell whether a function hands it a
    read-only mapping, so an instance is built here and sent both ways. A
    field names a mapping at any depth, aliases spelt out
    (``tuple[Mapping[str, float], ...]`` included).
    """
    covered = {_dotted(record) for record in records}
    annotations = reader.annotations
    holders = set()
    for dotted in _published_records():
        assert dotted in annotations.classes, f"{dotted}: not read from the source"
        fields = cpa.record_fields(reader.package, annotations, dotted)
        if any(
            annotations.named_within(
                field.module, field.annotation, cpa._KEYED_CONTAINERS
            )
            for field in fields.values()
        ):
            holders.add(dotted)
    unbuilt = {dotted.rpartition(".")[2] for dotted in holders - covered}
    assert unbuilt - set(MAPPING_HOLDERS_UNBUILT) == set()
    assert set(MAPPING_HOLDERS_UNBUILT) - unbuilt == set(), (
        "stale MAPPING_HOLDERS_UNBUILT entries"
    )


def _given(value: object, *, arrays: bool) -> list[object]:
    """What a field's value is given back as.

    A list of it; and, for a tuple of numbers in a field whose constructor
    takes an array (*arrays*), an array of it.
    """
    if isinstance(value, np.ndarray) and value.ndim >= 1:
        listed: list[object] = value.tolist()
        return [listed]
    if type(value) is tuple:
        given: list[object] = [list(value)]
        if (
            arrays
            and value
            and all(
                isinstance(item, int | float) and not isinstance(item, bool)
                for item in value
            )
        ):
            given.append(np.asarray(value))
        return given
    return []


def _takes_arrays(reader: cpa.Reader, record: str) -> frozenset[str]:
    """The constructor parameters of a record that take an array."""
    stub = cpa._constructor_stub(reader.annotations, record)
    if stub is None:
        return frozenset()
    module = reader.annotations.classes[record][0]
    return frozenset(
        argument.arg
        for argument in [*stub.args.args, *stub.args.kwonlyargs]
        if reader.annotations.admits_array_like(module, argument.annotation, {})
    )


def test_a_list_given_to_a_converted_field_is_held_converted(
    reader: cpa.Reader, records: list[object]
) -> None:
    """A list comes back as an array or a tuple, an array given for a tuple as a tuple."""
    kept = []
    for record in records:
        dotted = _dotted(record)
        if dotted not in reader.annotations.classes:
            continue
        converted = cpa.converted_fields(reader, dotted)
        arrays = _takes_arrays(reader, dotted)
        for each in dataclasses.fields(record):  # type: ignore[arg-type]
            if not each.init or each.name not in converted:
                continue
            stored = getattr(record, each.name)
            if isinstance(stored, list):
                kept.append(f"{type(record).__name__}.{each.name}: held a list")
                continue
            for given in _given(stored, arrays=each.name in arrays):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    rebuilt = dataclasses.replace(record, **{each.name: given})  # type: ignore[type-var]
                held = getattr(rebuilt, each.name)
                if held is given or type(held) is not type(stored):
                    kept.append(
                        f"{type(record).__name__}.{each.name}: given a "
                        f"{type(given).__name__}, held a {type(held).__name__}"
                    )
    assert kept == []


def _arrays_held(value: object, seen: set[int] | None = None) -> list[np.ndarray]:
    """Every array *value* holds, in containers, mappings and records, at any depth."""
    seen = set() if seen is None else seen
    if id(value) in seen:
        return []
    seen.add(id(value))
    if isinstance(value, np.ndarray):
        if value.dtype != object:
            return [value]
        members: list[object] = list(value.flat)
    elif isinstance(value, Mapping):
        members = list(value.values())
    elif isinstance(value, tuple | list):
        members = list(value)
    elif dataclasses.is_dataclass(value) and not isinstance(value, type):
        members = [
            getattr(value, each.name)
            for each in dataclasses.fields(value)
            if hasattr(value, each.name)
        ]
    else:
        return []
    return [array for member in members for array in _arrays_held(member, seen)]


@pytest.mark.parametrize("kind", sorted(ARRAY_LIKES))
def test_a_record_given_an_array_like_holds_a_copy_of_its_own(
    records: list[object], kind: str
) -> None:
    """Every array field, given an object numpy reads as the caller's memory.

    The record held the object as it came, and its own ``__post_init__``
    either read it through ``np.asarray`` and sealed what came back, for a
    column the caller's very array, so the caller's next write raised; or
    only checked it, and kept the caller's object and its memory; or
    refused it as a single number, where the same array given bare was
    taken. A record now reads it as the array it stands for, a copy of its
    own, held as an array.
    """
    make = ARRAY_LIKES[kind]
    found = []
    for record in records:
        for each in dataclasses.fields(record):  # type: ignore[arg-type]
            stored = getattr(record, each.name)
            if not (
                each.init
                and isinstance(stored, np.ndarray)
                and stored.ndim
                and stored.dtype != object
            ):
                continue
            mine = np.array(stored)
            given = make(mine)
            where = f"{type(record).__name__}.{each.name}"
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    warnings.filterwarnings(
                        "error", message=".*__array__", category=DeprecationWarning
                    )
                    rebuilt = dataclasses.replace(record, **{each.name: given})  # type: ignore[type-var]
            except (TypeError, ValueError, DeprecationWarning) as error:
                found.append(f"{where}: refused it ({type(error).__name__}: {error})")
                continue
            kept = getattr(rebuilt, each.name)
            if not mine.flags.writeable:
                found.append(f"{where}: sealed the caller's array")
            elif not isinstance(kept, np.ndarray):
                found.append(f"{where}: keeps the caller's {type(kept).__name__}")
            elif any(np.shares_memory(held, mine) for held in _arrays_held(rebuilt)):
                found.append(f"{where}: holds the caller's array")
    assert found == []


def _pickled(value: object) -> object:
    """*value* through ``pickle``, there and back."""
    # The bytes are the ones made on this line, never read from elsewhere.
    return pickle.loads(pickle.dumps(value))  # noqa: S301


def _differences(
    where: str, before: object, after: object, depth: int = 0
) -> list[str]:
    """Where a value that travelled differs from the one that left, read-only flags included.

    An array must come back equal, of the same dtype and shape, and as
    read-only as it left; a container, a mapping and a record are compared
    member by member; anything else by ``==`` where that gives one answer.
    """
    if depth > _DEPTH:
        return []
    if type(after) is not type(before):
        return [f"{where}: {type(before).__name__} came back {type(after).__name__}"]
    if isinstance(before, np.ndarray):
        assert isinstance(after, np.ndarray)
        found = []
        if after.flags.writeable != before.flags.writeable:
            found.append(
                f"{where}: writeable {before.flags.writeable} came back "
                f"{after.flags.writeable}"
            )
        same = (
            after.dtype == before.dtype
            and after.shape == before.shape
            and np.array_equal(after, before, equal_nan=before.dtype.kind in "fc")
        )
        if not same:
            found.append(f"{where}: the array came back different")
        return found
    if isinstance(before, Mapping):
        assert isinstance(after, Mapping)
        if list(after) != list(before):
            return [f"{where}: the keys came back different"]
        return [
            difference
            for key in before
            for difference in _differences(
                f"{where}[{key!r}]", before[key], after[key], depth + 1
            )
        ]
    if isinstance(before, tuple | list):
        assert isinstance(after, tuple | list)
        if len(after) != len(before):
            return [f"{where}: {len(before)} members came back {len(after)}"]
        return [
            difference
            for index, (old, new) in enumerate(zip(before, after, strict=True))
            for difference in _differences(f"{where}[{index}]", old, new, depth + 1)
        ]
    if dataclasses.is_dataclass(before) and not isinstance(before, type):
        return [
            difference
            for each in dataclasses.fields(before)
            if hasattr(before, each.name)
            for difference in _differences(
                f"{where}.{each.name}",
                getattr(before, each.name),
                getattr(after, each.name, None),
                depth + 1,
            )
        ]
    if (
        isinstance(before, float)
        and isinstance(after, float)
        and np.isnan(before)
        and np.isnan(after)
    ):
        return []
    try:
        equal = before == after
    except (TypeError, ValueError):
        return []
    if isinstance(equal, bool | np.bool_) and not equal:
        return [f"{where}: {before!r} came back {after!r}"]
    return []


#: How deep the comparison of a travelled record goes, records in records
#: included.
_DEPTH = 8


def test_every_record_survives_pickle_and_deepcopy(records: list[object]) -> None:
    """Each record comes back whole: its values, and every array as read-only as it left.

    ``pickle`` and ``copy.deepcopy`` rebuild a record without its
    ``__post_init__``, and NumPy hands an array back writeable; a record
    that came back from a process pool or a cache held arrays a caller
    could write into while the one that left refused it.
    """
    failed = []
    for record in records:
        travels: tuple[tuple[str, Callable[[object], object]], ...] = (
            ("pickle", _pickled),
            ("deepcopy", copy.deepcopy),
        )
        for how, travel in travels:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    back: Any = travel(record)
            except (TypeError, pickle.PicklingError) as error:
                failed.append(f"{type(record).__name__} ({how}): {error}")
                continue
            failed.extend(
                f"{how}: {difference}"
                for difference in _differences(type(record).__name__, record, back)
            )
    assert failed == []


# ---------------------------------------------------------------------------
# What a converted record refuses and holds
# ---------------------------------------------------------------------------
def test_a_transfer_matrix_holds_read_only_complex_entries() -> None:
    """Each entry is a read-only ``complex128`` array, a 0-d one for a number.

    A scalar entry was kept as the ``complex`` it was given, a real array as
    the real array: the record held whatever came in, so ``m.t11.real``
    answered for one and ``m.t11.shape`` for the other.
    """
    scalar = ph.materials.TransferMatrix(1.0, 2j, 0.5, 1.0)
    assert scalar.t11.shape == ()
    assert scalar.t11.dtype == np.complex128
    assert not scalar.t11.flags.writeable
    assert complex(scalar.t12) == 2j
    assert scalar.t21.imag == 0.0
    assert scalar.frequencies is None
    given = np.array([1.0, 2.0])
    banded = ph.materials.TransferMatrix(
        given, given, given, given, frequencies=[500.0, 1000.0]
    )
    assert banded.t11.dtype == np.complex128
    assert banded.frequencies is not None
    assert banded.frequencies.dtype == np.float64
    assert not banded.frequencies.flags.writeable
    assert given.flags.writeable
    with pytest.raises(ValueError, match="read-only"):
        banded.t11[0] = 0.0


_PAIRS: tuple[tuple[str, Callable[[Any], object]], ...] = (
    ("polar", lambda pair: ph.electroacoustics.LoudspeakerDirectivity(polar=pair)),
    ("polar", lambda pair: ph.electroacoustics.MicrophoneDirectivity(polar=pair)),
    ("spectrum", lambda pair: ph.electroacoustics.MicrophoneNoise(spectrum=pair)),
    (
        "distortion",
        lambda pair: ph.electroacoustics.MicrophoneOverload(distortion=pair),
    ),
)


@pytest.mark.parametrize(("name", "build"), _PAIRS)
def test_a_pair_is_refused_when_the_record_is_built(
    name: str, build: Callable[[Any], object]
) -> None:
    """Anything but a pair fails where it is given, not where it is read."""
    with pytest.raises(TypeError, match=rf"'{name}' must be a pair .* not float"):
        build(1.0)
    with pytest.raises(TypeError, match=rf"'{name}' must be a pair .* not str"):
        build("ab")
    with pytest.raises(ValueError, match=rf"'{name}' must be a pair .* not 3 of them"):
        build([[1.0], [2.0], [3.0]])
    held = build(np.array([[100.0, 1000.0], [0.0, -3.0]]))
    first, second = getattr(held, name)
    assert first.tolist() == [100.0, 1000.0]
    assert second.tolist() == [0.0, -3.0]
    assert not first.flags.writeable


def _objects(members: list[np.ndarray]) -> np.ndarray:
    """An array of objects holding *members* as they are, one per element."""
    held = np.empty(len(members), dtype=object)
    for index, member in enumerate(members):
        held[index] = member
    return held


def _wrapped_in(
    make: Callable[[np.ndarray], object],
) -> Callable[[list[np.ndarray]], object]:
    """A holder that hands each array over inside an array-like *make* builds."""

    def hold(members: list[np.ndarray]) -> object:
        return tuple(make(member) for member in members)

    return hold


#: Every kind of sequence a record of a fixed count of arrays takes them in.
_HOLDERS: dict[str, Callable[[list[np.ndarray]], object]] = {
    "tuple": tuple,
    "list": list,
    "array of objects": _objects,
    "deque": collections.deque,
    "generator": lambda members: iter(members),
    **{f"each in {kind}": _wrapped_in(make) for kind, make in ARRAY_LIKES.items()},
}


def _curve() -> list[np.ndarray]:
    return [np.array([0.0, 90.0, 180.0]), np.array([0.0, -3.0, -12.0])]


def _elevation_model() -> list[np.ndarray]:
    return [np.array([0.0, 10.0, 20.0]), np.array([0.0, 10.0]), np.zeros((2, 3))]


#: The records that hold a fixed count of arrays as one field, each with the
#: field and the arrays a caller gives it.
_HELD_ARRAYS: tuple[
    tuple[str, Callable[[Any], object], Callable[[], list[np.ndarray]]], ...
] = (
    *((name, build, _curve) for name, build in _PAIRS),
    (
        "terrain",
        lambda axes: ph.aircraft.RotorcraftGround(terrain=axes),
        _elevation_model,
    ),
)


@pytest.mark.parametrize("holder", sorted(_HOLDERS))
@pytest.mark.parametrize(
    ("name", "build", "given"),
    _HELD_ARRAYS,
    ids=[
        "LoudspeakerDirectivity",
        "MicrophoneDirectivity",
        "MicrophoneNoise",
        "MicrophoneOverload",
        "RotorcraftGround",
    ],
)
def test_a_record_of_a_fixed_count_of_arrays_never_seals_the_caller_s(
    name: str,
    build: Callable[[Any], object],
    given: Callable[[], list[np.ndarray]],
    holder: str,
) -> None:
    """Whatever sequence holds them, the caller's arrays stay the caller's.

    The record seals the arrays it holds, so each has to be its own: an
    array of objects was copied one level down only, its arrays still the
    caller's, a deque or a generator not at all, and a column handed numpy
    the caller's array; the record sealed the caller's arrays, and a later
    write by the caller raised.
    """
    mine = given()
    record = build(_HOLDERS[holder](mine))
    kept = getattr(record, name)
    assert len(kept) == len(mine)
    for held, array in zip(kept, mine, strict=True):
        assert array.flags.writeable
        assert not np.shares_memory(held, array)
        assert not held.flags.writeable
        np.testing.assert_array_equal(held, array)
        array[...] = 7.0
        assert not np.any(held == 7.0)


def _road_surface(speed_range: ArrayLike) -> object:
    return ph.environment.RoadSurfaceCoefficients(
        name="national surface",
        alpha={"1": (0.0,) * 8},
        beta={"1": 0.0},
        speed_range_kmh=speed_range,
    )


def _fiber_fit(bulk_density_range: ArrayLike) -> object:
    return ph.materials.FiberResistivityFit(
        k1=353.0,
        k2=0.63,
        fiber_diameter_um=4.75,
        bulk_density_range_kg_m3=bulk_density_range,
        direction="lateral",
        source="a fit by hand",
    )


def _task(duration_range: ArrayLike) -> object:
    return ph.hearing.Task(
        samples=[85.0, 86.0, 87.0],
        duration_hours=2.0,
        duration_range_hours=duration_range,
    )


_NUMBER_PAIRS: tuple[tuple[str, Callable[[ArrayLike], object]], ...] = (
    ("duration_range_hours", _task),
    ("bulk_density_range_kg_m3", _fiber_fit),
    ("speed_range_kmh", _road_surface),
)


@pytest.mark.parametrize(("name", "build"), _NUMBER_PAIRS)
def test_a_pair_of_numbers_is_refused_when_the_record_is_built(
    name: str, build: Callable[[ArrayLike], object]
) -> None:
    """A range is two numbers, checked where it is given, its field named."""
    with pytest.raises(TypeError, match=rf"'{name}' must be a pair .* not float"):
        build(2.0)
    with pytest.raises(TypeError, match=rf"'{name}' must be a pair .* not str"):
        build("12")
    with pytest.raises(ValueError, match=rf"'{name}' must be a pair .* not 3 of them"):
        build([1.0, 2.0, 3.0])
    with pytest.raises(TypeError, match=rf"'{name}' must be a pair .* member is str"):
        build(["1", "2"])
    with pytest.raises(TypeError, match=rf"'{name}' must be a pair .* member is list"):
        build([[1.0], [2.0]])
    held = getattr(build(np.array([1, 3])), name)
    assert held == (1.0, 3.0)
    assert all(type(value) is float for value in held)


def test_a_sequence_of_numbers_is_refused_with_its_field_named() -> None:
    """Observations, studded-tyre coefficients and risk thresholds name their field."""
    with pytest.raises(TypeError, match="'duration_observations_hours' must be"):
        ph.hearing.Task(
            samples=[85.0], duration_hours=2.0, duration_observations_hours="12"
        )
    coefficients = _HAND_BUILT["RoadEmissionCoefficients"]()
    with pytest.raises(TypeError, match="'studded_a' must be .* not float"):
        dataclasses.replace(coefficients, studded_a=5.0)  # type: ignore[type-var]
    shock = _HAND_BUILT["MultipleShockResult"]()
    with pytest.raises(ValueError, match="'risk_thresholds' must be .* not 2 of them"):
        dataclasses.replace(shock, risk_thresholds=[0.72, 1.42])  # type: ignore[type-var]
    with pytest.raises(TypeError, match="'risk_thresholds' must be .* not str"):
        dataclasses.replace(shock, risk_thresholds="abc")  # type: ignore[type-var]
    assert isinstance(shock, ph.vibration.MultipleShockResult)
    assert shock.risk_thresholds == (0.72, 1.42, 2.17)
    assert shock.peaks.dtype == np.float64
    assert not shock.peaks.flags.writeable


def test_a_hand_built_stiffness_and_impulse_response_hold_their_dtypes() -> None:
    """A real stiffness reads as complex, a list of samples as a float array."""
    stiffness = ph.vibration.TransferStiffnessResult(
        frequencies=[100, 200], transfer_stiffness=[1.0e6, 2.0e6]
    )
    assert stiffness.frequencies.dtype == np.float64
    assert stiffness.transfer_stiffness.dtype == np.complex128
    assert stiffness.transmissibility is None
    assert not stiffness.transfer_stiffness.flags.writeable
    response = ph.room.ImpulseResponseResult(ir=[1, 0, 0], fs=48000.0, method="mls")
    assert response.ir.dtype == np.float64
    assert len(response) == 3
    with pytest.raises(ValueError, match="read-only"):
        response.ir[0] = 0.0


def test_a_rated_frequency_range_is_checked_when_built() -> None:
    """``LoudspeakerRatings.frequency_range`` is refused when built, not when read."""
    with pytest.raises(TypeError, match="'frequency_range' must be a"):
        ph.electroacoustics.LoudspeakerRatings(frequency_range=50.0)
    with pytest.raises(ValueError, match="got shape"):
        ph.electroacoustics.LoudspeakerRatings(frequency_range=[50.0, 100.0, 200.0])
    with pytest.raises(ValueError, match="frequency_range"):
        ph.electroacoustics.LoudspeakerRatings(frequency_range=(20000.0, 50.0))
    held = ph.electroacoustics.LoudspeakerRatings(frequency_range=[50.0, 20000.0])
    assert held.frequency_range == (50.0, 20000.0)


def test_one_text_is_refused_as_channel_labels() -> None:
    """A text is a sequence of letters, never the labels of as many channels."""
    with pytest.raises(TypeError, match="channel_labels"):
        ph.Signal([[0.0, 0.1], [0.0, -0.1]], 48000.0, channel_labels="LR")
    labelled = ph.Signal([[0.0, 0.1], [0.0, -0.1]], 48000.0, channel_labels=["L", "R"])
    assert labelled.channel_labels == ("L", "R")


def test_a_result_mapping_refuses_assignment() -> None:
    """The four results that held a ``dict`` hold a read-only mapping."""
    facade = _facade()
    silencer = _MAPPING_HOLDERS["ReactiveSilencerResult"]()
    railway = _railway_emission()
    loudness = _time_varying_loudness()
    assert isinstance(facade, ph.building.FacadePredictionResult)
    assert isinstance(silencer, ph.noise_control.ReactiveSilencerResult)
    assert isinstance(railway, ph.environment.RailwayEmissionResult)
    assert isinstance(loudness, ph.psychoacoustics.MooreGlasbergTimeVaryingLoudness)
    assert silencer.geometry is not None
    mappings: tuple[Mapping[Any, Any], ...] = (
        facade.element_r,
        silencer.geometry,
        railway.components,
        loudness.percentiles,
    )
    for mapping in mappings:
        key = next(iter(mapping))
        with pytest.raises(TypeError, match="does not support item assignment"):
            mapping[key] = mapping[key]  # type: ignore[index]
