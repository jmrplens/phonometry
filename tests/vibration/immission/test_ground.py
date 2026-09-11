#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the ground constants of DIN 45672-1:2009-12, Clause 4.5.

Formula (3) is the relation the clause prints right, so it is the anchor:
the speeds a continuum with known constants carries have to come back to
those constants. The two formulas printed wrong are held to the numbers that
show they are wrong, so that a well-meant edit back to the printed form fails
here.
"""

from __future__ import annotations

import math

import pytest

from phonometry.materials.absorbers.biot import frame_elastic_coefficient
from phonometry.vibration import immission as im

#: A medium-dense sand: 1800 kg/m³, G = 80 MPa, nu = 0,3.
DENSITY = 1800.0
SHEAR_MODULUS = 80.0e6
POISSON = 0.3


def test_the_shear_wave_gives_the_shear_modulus() -> None:
    """Formulae (2) and (5): G = v_s² rho, both ways round."""
    v_s = math.sqrt(SHEAR_MODULUS / DENSITY)
    assert im.shear_modulus_from_wave_speed(
        v_s, density_kg_m3=DENSITY
    ) == pytest.approx(SHEAR_MODULUS)


def test_the_compression_speed_is_the_p_wave_of_a_continuum() -> None:
    """sqrt(M / rho), with M the P-wave modulus the Biot frame uses too."""
    v_p = im.compression_wave_speed(
        SHEAR_MODULUS, poisson_ratio=POISSON, density_kg_m3=DENSITY
    )
    modulus = frame_elastic_coefficient(SHEAR_MODULUS, POISSON)
    assert v_p == pytest.approx(math.sqrt(modulus.real / DENSITY))


def test_formula_3_inverts_the_speeds_the_continuum_carries() -> None:
    """The speeds of a known continuum give back its Poisson's ratio."""
    for nu in (0.1, 0.25, 0.3, 0.4, 0.45, 0.49):
        v_p = im.compression_wave_speed(
            SHEAR_MODULUS, poisson_ratio=nu, density_kg_m3=DENSITY
        )
        v_s = math.sqrt(SHEAR_MODULUS / DENSITY)
        assert im.poisson_ratio_from_wave_speeds(v_p, v_s) == pytest.approx(nu)


def test_the_elastic_modulus_is_two_g_times_one_plus_nu() -> None:
    v_s = math.sqrt(SHEAR_MODULUS / DENSITY)
    v_p = im.compression_wave_speed(
        SHEAR_MODULUS, poisson_ratio=POISSON, density_kg_m3=DENSITY
    )
    e = im.youngs_modulus_from_wave_speeds(v_p, v_s, density_kg_m3=DENSITY)
    assert e == pytest.approx(2.0 * SHEAR_MODULUS * (1.0 + POISSON))


def test_formula_5_as_printed_gives_the_p_wave_modulus_not_e() -> None:
    """E = v_p² rho overstates E by 35 % at nu = 0,3 and 3,8 times at 0,45."""
    v_s = math.sqrt(SHEAR_MODULUS / DENSITY)
    for nu, factor in ((0.3, 1.346), (0.45, 3.79)):
        v_p = im.compression_wave_speed(
            SHEAR_MODULUS, poisson_ratio=nu, density_kg_m3=DENSITY
        )
        printed = v_p**2 * DENSITY
        e = im.youngs_modulus_from_wave_speeds(v_p, v_s, density_kg_m3=DENSITY)
        assert printed / e == pytest.approx(factor, abs=0.005)


def test_formula_1_as_printed_is_short_of_a_factor_two() -> None:
    """The second radical of Formula (1) is sqrt(2) slow at every ratio."""
    for nu in (0.2, 0.3, 0.45):
        v_p = im.compression_wave_speed(
            SHEAR_MODULUS, poisson_ratio=nu, density_kg_m3=DENSITY
        )
        printed = math.sqrt(SHEAR_MODULUS * (1 - nu) / (DENSITY * (1 - 2 * nu)))
        assert v_p / printed == pytest.approx(math.sqrt(2.0))


def test_the_two_printed_radicals_agree_only_at_one_ratio() -> None:
    """sqrt(E/rho) = sqrt(G(1-nu)/(rho(1-2nu))) only where 4nu² + nu - 1 = 0."""
    nu = (math.sqrt(17.0) - 1.0) / 8.0
    e = 2.0 * SHEAR_MODULUS * (1.0 + nu)
    rod = math.sqrt(e / DENSITY)
    second = math.sqrt(SHEAR_MODULUS * (1 - nu) / (DENSITY * (1 - 2 * nu)))
    assert rod == pytest.approx(second)
    assert nu == pytest.approx(0.390, abs=5e-4)


def test_the_strain_of_rail_traffic_stays_in_the_linear_range() -> None:
    """Formula (4): 0,1 mm/s in a ground with v_s = 100 m/s is 10⁻⁶."""
    strain = im.shear_strain_amplitude(1.0e-4, shear_wave_speed_m_s=100.0)
    assert strain == pytest.approx(1.0e-6)
    assert strain < im.SHEAR_STRAIN_LINEAR_LIMIT


def test_the_ranges_are_the_ones_the_clause_prints() -> None:
    assert im.GROUND_WAVE_SPEED_RANGES_M_S == {
        "compression": (200.0, 2000.0),
        "shear": (10.0, 1000.0),
    }


def test_a_compression_wave_slower_than_the_shear_wave_is_refused() -> None:
    with pytest.raises(ValueError, match="stable continuum"):
        im.poisson_ratio_from_wave_speeds(100.0, 150.0)
    with pytest.raises(ValueError, match="stable continuum"):
        im.youngs_modulus_from_wave_speeds(1.1, 1.0, density_kg_m3=1.0)
    with pytest.raises(ValueError, match="poisson_ratio"):
        im.compression_wave_speed(1e6, poisson_ratio=0.5, density_kg_m3=1800.0)
    with pytest.raises(ValueError, match="velocity_amplitude_m_s"):
        im.shear_strain_amplitude(-1.0, shear_wave_speed_m_s=100.0)


def test_a_close_pair_of_speeds_gives_a_negative_ratio() -> None:
    """Between 2/sqrt(3) and sqrt(2) the continuum allows -1 < nu < 0."""
    nu = im.poisson_ratio_from_wave_speeds(1.2, 1.0)
    assert -1.0 < nu < 0.0
    edge = 2.0 / math.sqrt(3.0) * (1.0 + 1e-9)
    assert im.poisson_ratio_from_wave_speeds(edge, 1.0) == pytest.approx(-1.0, abs=1e-6)
