#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A record's required fields refuse ``None``, not only a missing argument.

Most of the fields below used to default to ``None`` so that a result built
by hand from a few of its numbers would still construct; the columns of an
:class:`~phonometry.building.OctaveBandSpectrum` never did. All of them are
required now, and leaving one out of the call raises ``TypeError``. ``None``
can still be passed for one explicitly, or put there with
:func:`dataclasses.replace`, and the shape and value guards skip ``None`` on
purpose, so each record also refuses it by name at construction instead of
failing later in a report or a plot.
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from result_factories import (
    _airborne_insulation,
    _airborne_rating,
    _extended_impact_rating,
    _extended_rating,
    _impact_insulation,
    _impact_rating,
    _intensity,
    _slit_aperture,
    _zwicker_stationary,
)

import phonometry as ph

if TYPE_CHECKING:
    from collections.abc import Callable


def _facade() -> ph.building.FacadePredictionResult:
    return ph.building.facade_sound_reduction(
        [ph.building.FacadeElement(name="wall", area=10.0, r=[40.0, 41.0, 42.0])],
        area=10.0,
        volume=50.0,
    )


def _barrier() -> ph.environment.BarrierInsertionLoss:
    return ph.environment.barrier_insertion_loss(
        np.array([125.0, 250.0, 500.0, 1000.0]), 1.5, 5.0, 3.0, 20.0, 1.5
    )


def _open_plan() -> ph.room.OpenPlanResult:
    return ph.room.open_plan_metrics(
        np.array([2.0, 4.0, 6.0, 8.0, 10.0]),
        np.array([52.0, 48.0, 45.0, 43.0, 41.0]),
        np.array([0.75, 0.6, 0.48, 0.38, 0.3]),
    )


def _resonator() -> ph.materials.HelmholtzResonator:
    return ph.materials.HelmholtzResonator(
        neck_length_m=1.0e-3,
        neck_side_m=3.0e-3,
        cavity_length_m=30.0e-3,
        cavity_side_m=27.0e-3,
    )


def _metadiffuser() -> ph.materials.MetadiffuserResult:
    well = ph.materials.MetadiffuserWell(
        slit_height_m=1.0e-3, resonators=(_resonator(),)
    )
    return ph.materials.metadiffuser_reflection(
        np.array([500.0, 1000.0]), (well, None), depth_m=0.03, period_m=0.1
    )


def _junction() -> ph.vibration.JunctionTransmissionResult:
    return ph.vibration.junction_transmission(
        "L", 0.1, 3500.0, 230.0, 0.2, 3500.0, 460.0
    )


def _in_situ() -> ph.materials.InSituAbsorptionResult:
    return ph.materials.InSituAbsorptionResult(
        frequencies=np.array([500.0, 1000.0]),
        absorption=np.array([0.2, 0.4]),
        source_height_m=0.25,
        microphone_height_m=0.25,
    )


def _layered() -> ph.materials.LayeredAbsorberResult:
    return ph.materials.layered_absorber(
        np.array([500.0, 1000.0]), [ph.materials.AirLayer(thickness_m=0.05)]
    )


def _diffuser() -> ph.materials.DiffuserPolarResponse:
    return ph.materials.predict_diffuser_polar_response(
        0.12, 1000.0, depths=[0.0, 0.02, 0.08, 0.02, 0.0], n_repetitions=2
    )


def _silencer() -> ph.noise_control.ReactiveSilencerResult:
    return ph.noise_control.expansion_chamber(
        np.array([100.0, 200.0]), 0.3, 0.03, 0.005
    )


def _impedance_tube() -> ph.materials.ImpedanceTubeResult:
    reflection = np.array([0.4 - 0.3j, 0.3 - 0.2j])
    normalized = (1.0 + reflection) / (1.0 - reflection)
    return ph.materials.ImpedanceTubeResult(
        frequencies=np.array([500.0, 1000.0]),
        reflection=reflection,
        surface_impedance=413.0 * normalized,
        normalized_impedance=normalized,
        absorption=1.0 - np.abs(reflection) ** 2,
        spacing_m=0.05,
        x1=0.1,
    )


def _slit_absorber() -> ph.materials.SlitResonatorAbsorberResult:
    return ph.materials.slit_helmholtz_absorber(
        np.array([500.0, 1000.0]),
        _resonator(),
        slit_height_m=1.0e-3,
        lattice_step_m=3.0e-2,
        period_m=5.0e-2,
    )


def _octave_bands() -> ph.building.OctaveBandSpectrum:
    return ph.building.improvement_octave_bands(
        np.arange(6.0), frequencies=[100.0, 125.0, 160.0, 200.0, 250.0, 315.0]
    )


_REQUIRED: tuple[tuple[Callable[[], Any], str], ...] = (
    (_open_plan, "positions_m"),
    *((_octave_bands, f) for f in ("frequencies", "values")),
    *((_metadiffuser, f) for f in ("wells", "depth_m", "period_m")),
    *((_junction, f) for f in ("thickness1_m", "thickness2_m")),
    *((_in_situ, f) for f in ("source_height_m", "microphone_height_m")),
    (_layered, "layers"),
    *((_diffuser, f) for f in ("well_width", "n_repetitions")),
    (_silencer, "plane_wave_limit"),
    *((_impedance_tube, f) for f in ("spacing_m", "x1")),
    *(
        (_slit_absorber, f)
        for f in ("resonators", "slit_height_m", "lattice_step_m", "period_m")
    ),
    *((_airborne_insulation, f) for f in ("d", "dnt", "l1", "l2", "t2", "t0")),
    *((_impact_insulation, f) for f in ("l_n_t", "li", "t2", "t0")),
    *((_airborne_rating, f) for f in ("frequencies", "measured", "shifted_reference")),
    *((_impact_rating, f) for f in ("frequencies", "measured", "shifted_reference")),
    *((_extended_rating, f) for f in ("frequencies", "measured")),
    *((_extended_impact_rating, f) for f in ("frequencies", "measured")),
    (_slit_aperture, "depth"),
    (_facade, "elements"),
    (_intensity, "spacing_m"),
    *(
        (_barrier, f)
        for f in (
            "source_height_m",
            "barrier_distance",
            "barrier_height_m",
            "receiver_distance",
            "receiver_height_m",
        )
    ),
    (_zwicker_stationary, "field"),
)


@pytest.mark.parametrize(
    ("factory", "field"),
    _REQUIRED,
    ids=[f"{factory.__name__.lstrip('_')}-{field}" for factory, field in _REQUIRED],
)
def test_a_required_field_refuses_none(factory: Callable[[], Any], field: str) -> None:
    """``replace(result, field=None)`` raises TypeError naming the field."""
    result = factory()
    record = type(result).__name__
    with pytest.raises(TypeError, match=rf"{record}: '{field}' is required"):
        dataclasses.replace(result, **{field: None})


@pytest.mark.parametrize(
    ("factory", "field"),
    [(_airborne_insulation, "r_prime"), (_impact_insulation, "l_n")],
    ids=["airborne-r_prime", "impact-l_n"],
)
def test_an_optional_quantity_may_still_be_absent(
    factory: Callable[[], Any], field: str
) -> None:
    """``R'`` and ``L'n`` stay optional: a measurement may not produce them."""
    result = dataclasses.replace(factory(), **{field: None})
    assert getattr(result, field) is None


def test_a_silencer_result_refuses_both_geometries_and_neither() -> None:
    """A named device holds ``geometry``, a chain ``chain``: never both, never none."""
    named = _silencer()
    chain = (
        ph.noise_control.SilencerChain(np.array([100.0, 200.0]))
        .duct(0.2, 0.005)
        .result(inlet_area=0.005, outlet_area=0.005)
    )
    with pytest.raises(TypeError, match=r"exactly one of 'geometry'.*neither"):
        dataclasses.replace(named, geometry=None)
    with pytest.raises(TypeError, match=r"exactly one of 'geometry'.*both"):
        dataclasses.replace(named, chain=chain.chain)


def test_the_diameter_of_an_impedance_tube_result_may_be_absent() -> None:
    """``spacing_m`` and ``x1`` are always there; the diameter may be absent."""
    assert _impedance_tube().diameter_m is None
