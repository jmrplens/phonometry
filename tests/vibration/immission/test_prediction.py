#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the prediction of vibration quantities of DIN 4150-1:2001-06.

The standard prints seven formulas and no worked example with a result;
what it prints are two figures drawn from the formulas with every parameter
given, Figure A.19 for Formula (2) and Figure A.18 for Formula (7), the
damping curves of Figure 2, the exponents of Figure 1 and the constants of
Clauses 4 and 5. The tests hold the library to those.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry.vibration import immission as im

# Figure A.19 (printed page 34): 0,44 mm/s at 13 m, alpha 0,005, drawn for n = 0, 0,5, 1.
A19 = {"reference_distance_m": 13.0, "attenuation_per_m": 0.005}


def test_figure_1_the_exponents_of_the_eight_codes() -> None:
    """Printed page 6: 0 for a harmonic line on a surface wave, 0,5 more for
    each of point, impulsive and body wave.
    """
    assert (
        im.geometric_exponent(geometry="line", character="harmonic", wave="surface")
        == 0.0
    )
    assert (
        im.geometric_exponent(geometry="point", character="harmonic", wave="surface")
        == 0.5
    )
    assert (
        im.geometric_exponent(geometry="line", character="impulsive", wave="surface")
        == 0.5
    )
    assert (
        im.geometric_exponent(geometry="line", character="harmonic", wave="body") == 0.5
    )
    assert (
        im.geometric_exponent(geometry="point", character="impulsive", wave="surface")
        == 1.0
    )
    assert (
        im.geometric_exponent(geometry="point", character="harmonic", wave="body")
        == 1.0
    )
    assert (
        im.geometric_exponent(geometry="line", character="impulsive", wave="body")
        == 1.0
    )
    assert (
        im.geometric_exponent(geometry="point", character="impulsive", wave="body")
        == 1.5
    )
    for (geometry, character, wave), n in im.SOURCE_EXPONENTS.items():
        expected = 0.5 * (
            (geometry == "point") + (character == "impulsive") + (wave == "body")
        )
        assert n == expected
    # A.4 and A.7: an impact pile driver and a truck over a step are PQ/I/O, n = 1;
    # A.5.1: a vibratory driver is PQ/HS/O, n = 0,5.
    assert (
        im.geometric_exponent(geometry="point", character="harmonic", wave="surface")
        == 0.5
    )
    with pytest.raises(ValueError, match="wave"):
        im.geometric_exponent(geometry="point", character="harmonic", wave="shear")


def test_figure_a19_formula_2_with_every_parameter_printed() -> None:
    """Printed page 34: the three curves at 80 m read 0,32, 0,13 and 0,05 mm/s;
    the formula gives 0,315, 0,127 and 0,051.
    """
    distances = np.array([15.0, 20.0, 30.0, 40.0, 60.0, 80.0])
    flat = im.far_field_velocity_mm_s(0.44, distances, exponent=0.0, **A19)
    half = im.far_field_velocity_mm_s(0.44, distances, exponent=0.5, **A19)
    unit = im.far_field_velocity_mm_s(0.44, distances, exponent=1.0, **A19)
    assert flat[-1] == pytest.approx(0.3149, abs=0.0005)
    assert half[-1] == pytest.approx(0.1269, abs=0.0005)
    assert unit[-1] == pytest.approx(0.0512, abs=0.0005)
    # Read off the drawing at a hundredth of a millimetre per second, a pixel.
    drawn = {
        0.0: [0.442, 0.430, 0.408, 0.386, 0.353, 0.32],
        0.5: [0.415, 0.343, 0.264, 0.214, 0.164, 0.13],
        1.0: [0.386, 0.274, 0.173, 0.120, 0.077, 0.05],
    }
    for exponent, values in drawn.items():
        computed = im.far_field_velocity_mm_s(0.44, distances, exponent=exponent, **A19)
        assert np.all(np.abs(computed - values) < 0.01), exponent
    # At the reference distance the amplitude is the reference amplitude.
    at_reference = im.far_field_velocity_mm_s(0.44, [13.0], exponent=1.0, **A19)
    assert at_reference[0] == pytest.approx(0.44)
    with pytest.raises(ValueError, match="far field"):
        im.far_field_velocity_mm_s(0.44, [10.0], exponent=1.0, **A19)


def test_the_printed_alpha_of_figure_a19_and_the_curves_of_figure_2() -> None:
    """Page 34 prints alpha = 0,005 for D = 0,01 and lambda = 12,5 m; Figure 2
    (page 7) draws the damping alone for D = 0,01 and c_s = 200 m/s, and at
    100 m its five curves read 0,73, 0,53, 0,39, 0,28 and 0,21.
    """
    alpha = im.attenuation_coefficient_per_m(0.01, wavelength_m=12.5)
    assert alpha == pytest.approx(0.005027, abs=1e-6)
    assert round(alpha, 3) == 0.005
    factors = [
        im.material_damping_factor(
            [100.0], damping_ratio=0.01, frequency_hz=f, wave_speed_m_s=200.0
        )[0]
        for f in (10.0, 20.0, 30.0, 40.0, 50.0)
    ]
    assert factors == pytest.approx([0.730, 0.534, 0.390, 0.285, 0.208], abs=0.001)
    read = [0.73, 0.53, 0.39, 0.28, 0.21]
    assert np.all(np.abs(np.array(factors) - read) < 0.02)
    assert (
        im.material_damping_factor(
            [0.0], damping_ratio=0.01, frequency_hz=10.0, wave_speed_m_s=200.0
        )[0]
        == 1.0
    )
    assert im.reference_distance_m(10.0, rayleigh_wavelength_m=12.5) == 17.5
    assert im.LOOSE_GROUND_DAMPING_RATIO == 0.01
    assert im.TRAIN_CHAIN_EXPONENT_RANGE == (0.3, 0.5)


def test_clause_4_3_the_building_on_its_ground() -> None:
    """Formula (3), the guide frequencies, V_F = 1/(2 D_0) = 2 for loose
    ground, V_D from 25 to 10 for a concrete floor, and the storey formula.
    """
    assert im.soil_building_natural_frequency_hz(
        4.0 * math.pi**2 * 1e8, mass_kg=1e6
    ) == pytest.approx(10.0)
    assert im.soil_building_frequency_guide_hz(1) == (15.0, 15.0)
    assert im.soil_building_frequency_guide_hz(2) == (8.0, 15.0)
    assert im.soil_building_frequency_guide_hz(4) == (8.0, 12.0)
    assert im.soil_building_frequency_guide_hz(9) == (0.0, 8.0)
    assert im.foundation_transfer_max() == 2.0
    assert im.foundation_transfer_max(0.5) == 1.0
    assert im.floor_transfer_max(0.02) == 25.0
    assert im.floor_transfer_max(0.05) == 10.0
    assert im.FLOOR_DAMPING_RATIO_RANGE == (0.02, 0.05)
    assert im.FOUNDATION_TRANSFER_ABOVE_RESONANCE == 0.5
    assert im.storey_frequency_hz(5) == 2.0
    assert im.storey_frequency_hz(10) == 1.0
    with pytest.raises(ValueError, match="5 storeys"):
        im.storey_frequency_hz(3)
    with pytest.raises(ValueError, match="storeys"):
        im.soil_building_frequency_guide_hz(0)
    with pytest.raises(ValueError, match="storeys"):
        im.soil_building_frequency_guide_hz(float("inf"))
    with pytest.raises(ValueError, match="storeys"):
        im.soil_building_frequency_guide_hz("3")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="harmonics"):
        im.track_excitation_frequency_hz(20.0, spacing_m=0.6, harmonics=2.9)  # type: ignore[arg-type]


def test_formulae_5_and_6_the_single_events() -> None:
    """No constants are printed; the shapes are: doubling the charge multiplies
    by 2^b, doubling the energy by root 2, and at 1 m the distance term is 1.
    """
    at_one = im.blast_peak_velocity_mm_s(
        2.0, [1.0], coefficient_mm_s=100.0, charge_exponent=0.5, distance_exponent=1.6
    )
    assert at_one[0] == pytest.approx(100.0 * math.sqrt(2.0))
    doubled = im.blast_peak_velocity_mm_s(
        4.0, [1.0], coefficient_mm_s=100.0, charge_exponent=0.5, distance_exponent=1.6
    )
    assert doubled[0] / at_one[0] == pytest.approx(math.sqrt(2.0))
    far = im.blast_peak_velocity_mm_s(
        2.0,
        [10.0, 100.0],
        coefficient_mm_s=100.0,
        charge_exponent=0.5,
        distance_exponent=1.6,
    )
    assert far[1] / far[0] == pytest.approx(10.0**-1.6)
    energy = im.fall_energy_kj(25506.0, drop_height_m=70.0)  # a 2 600 t chimney's head
    assert energy == pytest.approx(1.785e6, rel=1e-3)
    impact = im.impact_peak_velocity_mm_s(
        energy, [30.0, 60.0], coefficient_mm_s=0.1, distance_exponent=1.0
    )
    assert impact[0] / impact[1] == pytest.approx(2.0)
    assert impact[0] == pytest.approx(0.1 * math.sqrt(energy) / 30.0)
    assert im.BLASTING_RELEVANT_DISTANCE_M == {"quarry": 1500.0, "construction": 400.0}
    with pytest.raises(ValueError, match="distance_m"):
        im.blast_peak_velocity_mm_s(
            2.0,
            [0.0],
            coefficient_mm_s=100.0,
            charge_exponent=0.5,
            distance_exponent=1.6,
        )


def test_clause_5_3_2_what_a_track_excites() -> None:
    """f_A = v_Z / d and its multiples: 20 m/s over 0,6 m sleepers is 33,3 Hz."""
    freqs = im.track_excitation_frequency_hz(20.0, spacing_m=0.6, harmonics=3)
    assert freqs == pytest.approx([33.333, 66.667, 100.0], abs=0.001)
    assert im.RAIL_SUPPORT_SPACING_M == (0.6, 0.9)
    assert im.VEHICLE_NATURAL_FREQUENCIES_HZ == {
        "car_body": (1.0, 3.0),
        "bogie": (6.0, 10.0),
    }
    assert im.TRACK_TRANSMITTED_BANDS_HZ["ballast"] == (40.0, 80.0)
    assert im.RAIL_INFLUENCE_RANGE_M == 80.0
    assert im.MACHINE_FREQUENCY_BANDS_HZ["frame_saw"] == (4.0, 8.0)
    with pytest.raises(ValueError, match="harmonics"):
        im.track_excitation_frequency_hz(20.0, spacing_m=0.6, harmonics=0)


def test_figure_a18_formula_7_against_the_drawn_curve() -> None:
    """Printed page 33: the curve for v_B = 0,44 mm/s with N_B = 3 reads 0,68
    at 10 machines, 0,78 at 20, 0,90 at 40, 1,03 at 60, 1,16 at 80 and 1,27
    at 100; Figure 3 read at a five-hundredth reproduces it within 6 %. The
    formula lies below the drawn curve at every count, by 5 % at 10 machines
    and by 1 % at 100: the standard did not draw A.18 with exactly its own
    Figure 3, and the reading of the two drawings adds to that.
    """
    counts = np.array([10.0, 20.0, 40.0, 60.0, 80.0, 100.0])
    drawn = np.array([0.68, 0.78, 0.90, 1.03, 1.16, 1.27])
    computed = im.machine_hall_velocity_mm_s(0.44, counts, reference_count=3)
    assert np.all(np.abs(computed / drawn - 1.0) < 0.06)
    assert np.all(computed < drawn)
    assert im.machine_count_correction([10.0], reference_count=3)[0] == 0.471
    # Figure 3, the left frame at N = 4, and the right one at N = 100: the
    # N_B = 5 curve starts at 0,455, above 1 over root 5, so the family is
    # empirical and not a rule.
    assert im.machine_count_correction([4.0], reference_count=5)[0] == 0.455
    assert im.machine_count_correction([100.0], reference_count=100)[0] == 0.099
    assert im.machine_count_correction([7.0], reference_count=3)[0] == pytest.approx(
        (0.519 + 0.496) / 2
    )
    # The groups of Figure A.16 add up to the 252 machines of the example.
    assert 63 + 7 + 8 + 6 + 57 + 1 + 23 + 31 + 12 + 32 + 4 + 3 + 5 == 252
    with pytest.raises(ValueError, match="N_B"):
        im.machine_count_correction([10.0], reference_count=7)
    with pytest.raises(ValueError, match="from 4 to 100"):
        im.machine_count_correction([3.0], reference_count=3)


def test_the_module_lists_what_it_publishes() -> None:
    from phonometry.vibration.immission import prediction

    for name in prediction.__all__:
        assert getattr(im, name) is getattr(prediction, name)
