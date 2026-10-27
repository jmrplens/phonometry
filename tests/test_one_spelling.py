#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A choice typed ``Literal`` takes the spelling its ``Literal`` lists, and only it.

These functions folded the case, stripped the spaces, swapped separators,
mapped an alias of their own or made a text of any value with ``str()``
before they looked a choice up, so ``"a"`` passed for ``"A"`` and ``2023`` for
``"2023"`` while a type checker refused both. Each case below is a spelling
one of them took and now refuses: with :class:`ValueError` for a text that
names no option, with :class:`TypeError` for a value that is not text (rule
A45). The spellings a ``Literal`` lists on purpose stay; the last tests pin
them. ``scripts/check_choice_literals.py`` holds the code to the rule; these
tests hold the calls to it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from phonometry import (
    aircraft,
    building,
    emission,
    environment,
    filters,
    fluids,
    hearing,
    materials,
    metrology,
    noise_control,
    psychoacoustics,
    signals,
    underwater,
    vibration,
)

if TYPE_CHECKING:
    from collections.abc import Callable


class _Printed:
    """A value that is not a text but prints as an option."""

    def __init__(self, text: str) -> None:
        self.text = text

    def __str__(self) -> str:
        return self.text


_SIGNAL = np.sin(2.0 * np.pi * 1000.0 * np.arange(4800) / 48000.0)

#: The ANP database the aircraft cases look their operations up in.
_ANP = aircraft.load_anp_database()

#: A receiver of an ANP single event, 500 m along and 600 m beside the track.
_OBSERVER = [500.0, 600.0, 0.0]

#: An ``LpAF`` history with one onset of 30 dB over 0,1 s.
_ONSET = np.concatenate(
    [np.full(20, 50.0), np.linspace(50.0, 80.0, 10), np.full(20, 80.0)]
)


def _not_a_text(name: str) -> str:
    """What ``require_choice`` says of a value that is not text."""
    return rf"'{name}' must be one of .*, a text; got "


_DROPPED_SPELLINGS: list[tuple[str, Callable[[], object], type[Exception], str]] = [
    (
        "WeightingFilter 'a'",
        lambda: filters.WeightingFilter(48000, "a"),  # type: ignore[arg-type]
        ValueError,
        r"'weighting' must be 'A'",
    ),
    (
        "time_weighting mode 'FAST'",
        lambda: filters.time_weighting(_SIGNAL, 48000, mode="FAST"),  # type: ignore[call-overload]
        ValueError,
        "Invalid time weighting mode",
    ),
    (
        "TimeWeighting mode 'Slow'",
        lambda: filters.TimeWeighting(48000, mode="Slow"),  # type: ignore[arg-type]
        ValueError,
        "Invalid time weighting mode",
    ),
    (
        "time_weighting initial_state 'ZERO'",
        lambda: filters.time_weighting(_SIGNAL, 48000, initial_state="ZERO"),  # type: ignore[call-overload]
        ValueError,
        "initial_state must be",
    ),
    (
        "OctaveFilterBank.filter mode 'RMS'",
        lambda: filters.OctaveFilterBank(48000).filter(_SIGNAL, mode="RMS"),  # type: ignore[arg-type]
        ValueError,
        "'mode' must be one of",
    ),
    (
        "ln_levels mode 'FAST'",
        lambda: signals.ln_levels(_SIGNAL, 48000, mode="FAST"),  # type: ignore[arg-type]
        ValueError,
        "Invalid time weighting mode",
    ),
    (
        "ln_levels weighting 'z'",
        lambda: signals.ln_levels(_SIGNAL, 48000, weighting="z"),  # type: ignore[arg-type]
        ValueError,
        r"'weighting' must be 'A'",
    ),
    (
        "engine mounting 'Wing'",
        lambda: aircraft.engine_installation_correction(10.0, mounting="Wing"),  # type: ignore[arg-type]
        ValueError,
        "'mounting' must be one of",
    ),
    (
        "engine mounting alias 'prop'",
        lambda: aircraft.engine_installation_correction(10.0, mounting="prop"),  # type: ignore[arg-type]
        ValueError,
        "'mounting' must be one of",
    ),
    (
        "start-of-roll engine alias 'turbofan'",
        lambda: aircraft.start_of_roll_directivity(120.0, 500.0, engine="turbofan"),  # type: ignore[arg-type]
        ValueError,
        "'engine' must be one of",
    ),
    (
        "rotorcraft ground class 'g'",
        lambda: aircraft.ground_effect_adjustment(
            [500.0],
            10.0,
            2.0,
            100.0,
            flow_resistivity="g",  # type: ignore[arg-type]
        ),
        ValueError,
        "'flow_resistivity' class must be one of",
    ),
    (
        "survey room alias 'other'",
        lambda: building.estimate_reverberation_index(30.0, "other"),  # type: ignore[call-overload]
        ValueError,
        "'room' must be one of",
    ),
    (
        "single-number quantity 'R_w'",
        lambda: building.single_number_uncertainty("R_w", "A"),  # type: ignore[arg-type]
        ValueError,
        "'quantity' must be one of",
    ),
    (
        "DB-HR spectrum 'Pink'",
        lambda: building.db_hr_global_index([0.0] * 18, "Pink"),  # type: ignore[arg-type]
        ValueError,
        "'spectrum' must be one of",
    ),
    (
        "DB-HR receiving room 'Protected'",
        lambda: building.db_hr_airborne_requirement("Protected", "other_unit"),  # type: ignore[arg-type]
        ValueError,
        "'receiving_room' must be one of",
    ),
    (
        "DB-HR building use 'Residential'",
        lambda: building.db_hr_facade_requirement(60.0, "Residential", "bedrooms"),  # type: ignore[arg-type]
        ValueError,
        "'building_use' must be one of",
    ),
    (
        "DB-HR room type 'living room'",
        lambda: building.db_hr_facade_requirement(60.0, "residential", "living room"),  # type: ignore[arg-type]
        ValueError,
        "'room_type' must be one of",
    ),
    (
        "DB-HR source room ' other_unit '",
        lambda: building.db_hr_impact_requirement("protected", " other_unit "),  # type: ignore[arg-type]
        ValueError,
        "'source_room' must be one of",
    ),
    (
        "DB-HR room use 'conference hall'",
        lambda: building.db_hr_reverberation_requirement("conference hall"),  # type: ignore[arg-type]
        ValueError,
        "'room_use' must be one of",
    ),
    (
        "DB-HR party wall ' DnT,A '",
        lambda: building.db_hr_party_wall_requirement(" DnT,A "),  # type: ignore[arg-type]
        ValueError,
        "'quantity' must be one of",
    ),
    (
        "RD 1367 area type 'A'",
        lambda: environment.outdoor_quality_objectives("A"),  # type: ignore[arg-type]
        ValueError,
        "'area_type' must be one of",
    ),
    (
        "RD 1367 urbanization 'NEW'",
        lambda: environment.outdoor_quality_objectives("a", urbanization="NEW"),  # type: ignore[arg-type]
        ValueError,
        "'urbanization' must be one of",
    ),
    (
        "RD 1367 room type 'Bedrooms'",
        lambda: environment.indoor_quality_objectives("residential", "Bedrooms"),  # type: ignore[arg-type]
        ValueError,
        "'room_type' must be one of",
    ),
    (
        "RD 1367 building use 'Hospital'",
        lambda: environment.vibration_quality_objective("Hospital"),  # type: ignore[arg-type]
        ValueError,
        "'building_use' must be one of",
    ),
    (
        "pass-by vehicle category '2A'",
        lambda: environment.pass_by_regression(
            [50.0, 60.0, 70.0],
            [70.0, 72.0, 74.0],
            vehicle_category="2A",  # type: ignore[arg-type]
            road_speed_category="low",
        ),
        ValueError,
        "'vehicle_category' must be one of",
    ),
    (
        "CNOSSOS brake code 'C'",
        lambda: environment.wheel_roughness("C"),  # type: ignore[arg-type]
        ValueError,
        "'brake' must be one of",
    ),
    (
        "CNOSSOS vehicle category 1",
        lambda: environment.road_rolling_noise(1, 50.0),  # type: ignore[arg-type]
        TypeError,
        _not_a_text("category"),
    ),
    (
        "sea-water sound speed model 'UNESCO'",
        lambda: fluids.sea_water_sound_speed(10.0, 35.0, 100.0, model="UNESCO"),  # type: ignore[call-overload]
        ValueError,
        "'model' must be one of",
    ),
    (
        "ceiling mounting letter 'e'",
        lambda: materials.mounting_type("e"),  # type: ignore[arg-type]
        ValueError,
        "'letter' must be one of",
    ),
    (
        "calibrator class 'ls'",
        lambda: metrology.verify_sound_calibrator(
            "ls",  # type: ignore[arg-type]
            None,  # type: ignore[arg-type]
            nominal_frequency_hz=1000.0,
        ),
        ValueError,
        "'calibrator_class' must be one of",
    ),
    (
        "calibrator class 1",
        lambda: metrology.verify_sound_calibrator(
            1,  # type: ignore[arg-type]
            None,  # type: ignore[arg-type]
            nominal_frequency_hz=1000.0,
        ),
        TypeError,
        _not_a_text("calibrator_class"),
    ),
    (
        "cabin method not a text",
        lambda: noise_control.uncertainty_conditions(
            room_volume_m3=200.0,
            cabin_volume_m3=20.0,
            method=_Printed("laboratory"),  # type: ignore[arg-type]
        ),
        TypeError,
        _not_a_text("method"),
    ),
    (
        "enclosure condition not a text",
        lambda: noise_control.applicable_methods(
            condition=_Printed("laboratory"),  # type: ignore[arg-type]
        ),
        TypeError,
        _not_a_text("condition"),
    ),
    (
        "audiogram group 'hf'",
        lambda: underwater.audiogram_parameters("hf"),  # type: ignore[arg-type]
        ValueError,
        "'group' must be one of",
    ),
    (
        "hearing group 'lf'",
        lambda: underwater.weighting_parameters("lf"),  # type: ignore[arg-type]
        ValueError,
        "'group' must be one of",
    ),
    (
        "weighting guidance 'nmfs_2024'",
        lambda: underwater.weighting_parameters("LF", guidance="nmfs_2024"),  # type: ignore[arg-type]
        ValueError,
        "'guidance' must be one of",
    ),
    (
        "spreading law 'Spherical'",
        lambda: underwater.spreading_loss([100.0], law="Spherical"),  # type: ignore[arg-type]
        ValueError,
        "'law' must be one of",
    ),
    (
        "absorption model 'Thorp'",
        lambda: underwater.seawater_absorption(1000.0, model="Thorp"),  # type: ignore[arg-type]
        ValueError,
        "'model' must be one of",
    ),
    (
        "volume absorption model 'Thorp'",
        lambda: underwater.VolumeAbsorption(model="Thorp"),  # type: ignore[arg-type]
        ValueError,
        "'model' must be one of",
    ),
    (
        "normal modes bottom 'Rigid'",
        lambda: underwater.normal_modes(
            100.0,
            [0.0, 100.0],
            [1500.0, 1500.0],
            source_depth=50.0,
            receiver_depth=50.0,
            bottom="Rigid",  # type: ignore[arg-type]
        ),
        ValueError,
        "'bottom' must be one of",
    ),
    (
        "Weston seabed 'Sand'",
        lambda: underwater.effective_depth(100.0, 100.0, seabed="Sand"),  # type: ignore[arg-type]
        ValueError,
        "'seabed' must be one of",
    ),
    (
        "detection crossing 'First'",
        lambda: underwater.detection_range_from_curve(
            80.0,
            [100.0, 200.0],
            [70.0, 90.0],
            crossing="First",  # type: ignore[arg-type]
        ),
        ValueError,
        "'crossing' must be one of",
    ),
    (
        "ship model 'RANDI'",
        lambda: underwater.ship_source_spectrum(model="RANDI"),  # type: ignore[arg-type]
        ValueError,
        "'model' must be one of",
    ),
    (
        "ship vessel class 'Containership'",
        lambda: underwater.ship_source_spectrum(vessel_class="Containership"),  # type: ignore[arg-type]
        ValueError,
        "'vessel_class' must be one of",
    ),
    (
        "frequency weighting name not a text",
        lambda: vibration.reference_indication(_Printed("Wk")),  # type: ignore[arg-type]
        TypeError,
        _not_a_text("name"),
    ),
    (
        "signal burst application not a text",
        lambda: vibration.sawtooth_burst(_Printed("hand-arm"), 1),  # type: ignore[arg-type]
        TypeError,
        _not_a_text("application"),
    ),
    (
        "displayed quantity not a text",
        lambda: vibration.instrument_confidence_limit_percent(_Printed("rms")),  # type: ignore[arg-type]
        TypeError,
        _not_a_text("quantity"),
    ),
    (
        "guide values edition 1999",
        lambda: vibration.guide_values("residential", edition=1999),  # type: ignore[arg-type]
        TypeError,
        _not_a_text("edition"),
    ),
    (
        "geometric exponent geometry not a text",
        lambda: vibration.geometric_exponent(
            geometry=_Printed("point"),  # type: ignore[arg-type]
            character="harmonic",
            wave="surface",
        ),
        TypeError,
        _not_a_text("geometry"),
    ),
    (
        "floor not a text",
        lambda: vibration.ground_to_floor_level_difference(
            _Printed("concrete"),  # type: ignore[arg-type]
            floor_natural_frequency_hz=20.0,
        ),
        TypeError,
        _not_a_text("floor"),
    ),
    (
        "train kind not a text",
        lambda: vibration.train_weighting_factor(_Printed("freight")),  # type: ignore[arg-type]
        TypeError,
        _not_a_text("kind"),
    ),
    (
        "junction 'x'",
        lambda: vibration.junction_transmission(
            "x",  # type: ignore[arg-type]
            0.1,
            3000.0,
            200.0,
            0.1,
            3000.0,
            200.0,
        ),
        ValueError,
        "'junction' must be one of",
    ),
    (
        "junction section 'Corner'",
        lambda: vibration.angular_average_transmission_coefficient(
            1.0,
            0.5,
            section="Corner",  # type: ignore[arg-type]
        ),
        ValueError,
        "'section' must be one of",
    ),
    (
        "ANPDatabase.event_level operation 'takeoff'",
        lambda: _ANP.event_level("747100", _OBSERVER, "takeoff"),  # type: ignore[arg-type]
        ValueError,
        "'operation' must be one of",
    ),
    (
        "ANPAircraft.noise_contour operation ' departure '",
        lambda: _ANP.aircraft("747100").noise_contour(
            " departure ",  # type: ignore[arg-type]
            x=[0.0, 1000.0],
            y=[0.0, 500.0],
        ),
        ValueError,
        "'operation' must be one of",
    ),
    (
        "ANPAircraft.event_level metric 'EXPOSURE'",
        lambda: _ANP.aircraft("747100").event_level(
            _OBSERVER,
            "departure",
            metric="EXPOSURE",  # type: ignore[arg-type]
        ),
        ValueError,
        "'metric' must be one of",
    ),
    (
        "detect_onsets onset_rate_method 'UPPER_HALF'",
        lambda: environment.detect_onsets(
            _ONSET,
            0.01,
            onset_rate_method="UPPER_HALF",  # type: ignore[arg-type]
        ),
        ValueError,
        "'onset_rate_method' must be one of",
    ),
    (
        "impulsive_sound_adjustment onset_rate_method 5",
        lambda: environment.impulsive_sound_adjustment(
            _SIGNAL,
            48000,
            onset_rate_method=5,  # type: ignore[arg-type]
        ),
        TypeError,
        _not_a_text("onset_rate_method"),
    ),
    (
        "job_based_exposure instrument 'Class 1'",
        lambda: hearing.job_based_exposure(
            [80.0, 82.0, 81.0, 83.0, 80.0],
            8.0,
            instrument="Class 1",  # type: ignore[arg-type]
        ),
        ValueError,
        "'instrument' must be one of",
    ),
    (
        "task_based_exposure instrument 5",
        lambda: hearing.task_based_exposure(
            [hearing.Task(samples=(80.0, 81.0, 82.0), duration_hours=8.0)],
            instrument=5,  # type: ignore[arg-type]
        ),
        TypeError,
        _not_a_text("instrument"),
    ),
    (
        "sound_power_pressure grade 5",
        lambda: emission.sound_power_pressure(
            np.full((10, 1), 80.0),
            "hemisphere",
            radius=1.0,
            grade=5,  # type: ignore[arg-type]
        ),
        TypeError,
        _not_a_text("grade"),
    ),
    (
        "weighting_class_limits edition 2013",
        lambda: filters.weighting_class_limits(1, edition=2013),  # type: ignore[arg-type]
        TypeError,
        _not_a_text("edition"),
    ),
    (
        "loudness_zwicker_from_spectrum field 5",
        lambda: psychoacoustics.loudness_zwicker_from_spectrum(
            np.full(28, 60.0),
            field=5,  # type: ignore[arg-type]
        ),
        TypeError,
        _not_a_text("field"),
    ),
    (
        "exposure_assessment kind 5",
        lambda: vibration.exposure_assessment(2.0, kind=5),  # type: ignore[arg-type]
        TypeError,
        _not_a_text("kind"),
    ),
    (
        "barrier_insertion_loss method 5",
        lambda: environment.barrier_insertion_loss(
            [500.0, 1000.0],
            1.0,
            50.0,
            4.0,
            100.0,
            1.5,
            method=5,  # type: ignore[arg-type]
        ),
        TypeError,
        _not_a_text("method"),
    ),
]


@pytest.mark.parametrize(
    ("call", "error", "match"),
    [case[1:] for case in _DROPPED_SPELLINGS],
    ids=[case[0] for case in _DROPPED_SPELLINGS],
)
def test_a_spelling_the_literal_does_not_list_is_refused(
    call: Callable[[], object], error: type[Exception], match: str
) -> None:
    """A case variant, a padded or separated variant, an alias of the
    function's own or a value that is not text is no option any more.
    """
    with pytest.raises(error, match=match):
        call()


def test_the_aliases_a_literal_lists_on_purpose_stay() -> None:
    """``"docente"`` is educational, ``"dnt_w"`` reads the row of ``"r_w"``, and
    ``"conference_hall"`` the classroom requirement, as the ``Literal`` offers.
    """
    teaching = building.db_hr_facade_requirement(60.0, "docente", "aulas")
    educational = building.db_hr_facade_requirement(60.0, "educational", "classrooms")
    assert teaching == educational
    assert building.single_number_uncertainty(
        "dnt_w", "B"
    ) == building.single_number_uncertainty("r_w", "B")
    hall = building.db_hr_reverberation_requirement("conference_hall")
    assert hall == building.db_hr_reverberation_requirement("classroom")
    assert environment.outdoor_quality_objectives(
        "residential"
    ) == environment.outdoor_quality_objectives("a")
