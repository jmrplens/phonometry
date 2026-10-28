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

import phonometry as ph
from phonometry.io._sidecar import CalibrationSidecar

if TYPE_CHECKING:
    from collections.abc import Callable

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
        if isinstance(value, Mapping):
            stack.extend(value.values())
        elif isinstance(value, tuple | list):
            stack.extend(value)
        elif (
            dataclasses.is_dataclass(value)
            and not isinstance(value, type)
            and id(value) not in found
        ):
            found[id(value)] = value
            stack.extend(
                getattr(value, each.name)
                for each in dataclasses.fields(value)
                if hasattr(value, each.name)
            )
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
    built = [build() for build in _HAND_BUILT.values()]
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


def _pickled(value: object) -> object:
    """*value* through ``pickle``, there and back."""
    # The bytes are the ones made on this line, never read from elsewhere.
    return pickle.loads(pickle.dumps(value))  # noqa: S301


def test_every_record_survives_pickle_and_deepcopy(records: list[object]) -> None:
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
            assert type(back) is type(record)
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
    facade = ph.building.facade_sound_reduction(
        [ph.building.FacadeElement(name="wall", area=10.0, r=[40.0, 45.0])],
        area=10.0,
        volume=50.0,
        frequencies=[500.0, 1000.0],
        fraction=1,
    )
    silencer = ph.noise_control.silencers.expansion_chamber(
        [100.0, 200.0], 0.5, 0.08, 0.01
    )
    stock = _HAND_BUILT["RollingStock"]()
    track = _HAND_BUILT["RailwayTrack"]()
    assert isinstance(stock, ph.environment.RollingStock)
    assert isinstance(track, ph.environment.RailwayTrack)
    railway = ph.environment.railway_source_power(
        ph.environment.RailwayVehicle(stock=stock, flow_rate=10.0, speed_kmh=80.0),
        track,
    )
    times = np.arange(3200) / 32000.0
    loudness = ph.psychoacoustics.loudness_moore_glasberg_time(
        0.02 * np.sin(2.0 * np.pi * 1000.0 * times), 32000.0, percentiles=(5.0, 50.0)
    )
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
