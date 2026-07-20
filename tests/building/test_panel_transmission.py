#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for the predicted panel sound reduction index (Bies 5e Section 7.2).

Anchored on: the exact mass law (Bies Eq. 7.40) rising 6 dB per octave and 6 dB
per doubling of surface mass; the field-incidence correction of 5.5 dB (1/3
octave) / 4.0 dB (octave) (Eq. 7.42); Sharp's coincidence-dip design-chart point
B ``TL = 20 lg(fc m'') + 10 lg eta - 44`` (Fig. 7.9a); the mass-air-mass
resonance ``f0 = 60 sqrt((m1 + m2)/(m1 m2 d))`` (Bies Eq. 7.62 / Hopkins
Eq. 4.73); the double-wall low-frequency limit (below f0 = mass law of the
combined mass, Eq. 7.64); and the measured 6 mm glass / 12.5 mm plasterboard
curves of Hopkins Fig. 4.8 / 4.9 as a few-dB sanity check in the mass-law range.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import (
    coincidence_frequency,
    double_wall_transmission_loss,
    field_incidence_correction,
    mass_law_transmission_loss,
    mass_spring_mass_resonance,
    plate_bending_stiffness,
    single_panel_transmission_loss,
)
from phonometry.materials import miki

# ISO 717-1 one-third-octave band centres, 100 Hz to 3150 Hz.
BANDS = np.array(
    [100, 125, 160, 200, 250, 315, 400, 500, 630, 800,
     1000, 1250, 1600, 2000, 2500, 3150], dtype=float
)


# ---------------------------------------------------------------------------
# Mass law (Bies Eq. 7.40 / 7.42).
# ---------------------------------------------------------------------------
def test_mass_law_six_db_per_octave() -> None:
    lo = mass_law_transmission_loss(500.0, 20.0, incidence="normal")
    hi = mass_law_transmission_loss(1000.0, 20.0, incidence="normal")
    assert float(hi - lo) == pytest.approx(6.02, abs=0.01)


def test_mass_law_six_db_per_mass_doubling() -> None:
    light = mass_law_transmission_loss(500.0, 20.0, incidence="normal")
    heavy = mass_law_transmission_loss(500.0, 40.0, incidence="normal")
    assert float(heavy - light) == pytest.approx(6.02, abs=0.01)


def test_field_incidence_correction_values() -> None:
    assert field_incidence_correction("third") == 5.5
    assert field_incidence_correction("octave") == 4.0
    normal = mass_law_transmission_loss(500.0, 20.0, incidence="normal")
    field = mass_law_transmission_loss(500.0, 20.0, incidence="field", band="third")
    assert float(normal - field) == pytest.approx(5.5)


def test_mass_law_hand_value() -> None:
    # TL_normal = 10 lg(1 + (pi f m / rho0 c0)**2).
    f, m = 500.0, 20.0
    ratio = math.pi * f * m / (1.205 * 343.0)
    expected = 10.0 * math.log10(1.0 + ratio**2)
    assert mass_law_transmission_loss(f, m, incidence="normal") == pytest.approx(
        expected
    )


# ---------------------------------------------------------------------------
# Single panel, Sharp's method (Bies 7.2.4.1).
# ---------------------------------------------------------------------------
def test_single_panel_coincidence_dip_point_b() -> None:
    m, eta = 15.0, 0.024
    bp = plate_bending_stiffness(6.2e10, 0.006, 0.24)
    fc = coincidence_frequency(m, bp)
    tl_fc = single_panel_transmission_loss(
        [fc], m, critical_frequency=fc, loss_factor=eta
    ).transmission_loss[0]
    point_b = 20.0 * math.log10(fc * m) + 10.0 * math.log10(eta) - 44.0
    assert float(tl_fc) == pytest.approx(point_b, abs=0.5)


def test_single_panel_dip_at_coincidence() -> None:
    m = 15.0
    bp = plate_bending_stiffness(6.2e10, 0.006, 0.24)
    fc = coincidence_frequency(m, bp)
    res = single_panel_transmission_loss(BANDS, m, critical_frequency=fc,
                                         loss_factor=0.024)
    # A local dip must sit near the coincidence frequency.
    dip_band = BANDS[int(np.argmin(np.abs(BANDS - fc)))]
    below = res.transmission_loss[BANDS == 1000.0][0]
    at_dip = res.transmission_loss[BANDS == dip_band][0]
    assert at_dip < below


def test_single_panel_glass_rating_realistic() -> None:
    # 6 mm float glass: catalogue Rw is about 31-32 dB.
    m = 15.0
    bp = plate_bending_stiffness(6.2e10, 0.006, 0.24)
    fc = coincidence_frequency(m, bp)
    res = single_panel_transmission_loss(BANDS, m, critical_frequency=fc,
                                         loss_factor=0.024)
    assert 29 <= res.rating().rating <= 34


def test_single_panel_matches_glass_measurement_masslaw_range() -> None:
    # Hopkins Fig. 4.8, 6 mm glass, below coincidence, within a few dB.
    m = 15.0
    bp = plate_bending_stiffness(6.2e10, 0.006, 0.24)
    fc = coincidence_frequency(m, bp)
    freqs = np.array([250.0, 500.0, 1000.0])
    measured = np.array([25.0, 28.5, 33.0])
    res = single_panel_transmission_loss(freqs, m, critical_frequency=fc,
                                         loss_factor=0.024)
    np.testing.assert_allclose(res.transmission_loss, measured, atol=4.0)


def test_single_panel_from_bending_stiffness() -> None:
    m = 15.0
    bp = plate_bending_stiffness(6.2e10, 0.006, 0.24)
    a = single_panel_transmission_loss(BANDS, m, bending_stiffness=bp)
    b = single_panel_transmission_loss(
        BANDS, m, critical_frequency=coincidence_frequency(m, bp)
    )
    np.testing.assert_allclose(a.transmission_loss, b.transmission_loss)


def test_single_panel_requires_fc_or_stiffness() -> None:
    with pytest.raises(ValueError, match="critical_frequency"):
        single_panel_transmission_loss(BANDS, 15.0)


# ---------------------------------------------------------------------------
# Double wall (Bies 7.2.6).
# ---------------------------------------------------------------------------
def test_mass_spring_mass_resonance_closed_form() -> None:
    m1, m2, d = 12.16, 12.16, 0.1
    f0 = mass_spring_mass_resonance(m1, m2, d)
    # Bies/Hopkins round the air-cavity constant to 60; the exact rho0 c0**2
    # form gives 59.9, so the design constant agrees to about 0.2 %.
    assert f0 == pytest.approx(60.0 * math.sqrt((m1 + m2) / (m1 * m2 * d)), rel=5e-3)
    # Exact closed form f0 = (1/2pi) sqrt(rho0 c0**2 / d * (m1+m2)/(m1 m2)).
    stiffness = 1.205 * 343.0**2 / d
    exact = math.sqrt(stiffness * (m1 + m2) / (m1 * m2)) / (2.0 * math.pi)
    assert f0 == pytest.approx(exact, rel=1e-9)


def test_double_wall_below_f0_is_total_mass_law() -> None:
    m1, m2, d = 12.16, 12.16, 0.1
    f0 = mass_spring_mass_resonance(m1, m2, d)
    fb = 0.5 * f0
    dw = double_wall_transmission_loss([fb], m1, m2, d).transmission_loss[0]
    ml = mass_law_transmission_loss(fb, m1 + m2)
    assert float(dw) == pytest.approx(float(ml))


def test_double_wall_continuous_at_limiting_frequency() -> None:
    m1, m2, d = 12.16, 12.16, 0.1
    f_l = 343.0 / (2.0 * math.pi * d)
    lo = double_wall_transmission_loss([f_l * 0.999], m1, m2, d).transmission_loss[0]
    hi = double_wall_transmission_loss([f_l * 1.001], m1, m2, d).transmission_loss[0]
    # 20 lg(2 k d) = 6.02 dB at f_l, the +6 dB high branch: continuous to ~0.05 dB.
    assert abs(float(hi - lo)) < 0.1


def test_double_wall_beats_single_leaf_above_resonance() -> None:
    m1, m2, d = 12.16, 12.16, 0.1
    dw = double_wall_transmission_loss([500.0], m1, m2, d).transmission_loss[0]
    single = mass_law_transmission_loss(500.0, m1 + m2)
    assert float(dw) > float(single) + 10.0


def test_double_wall_porous_fill_lowers_resonance() -> None:
    m1, m2, d = 12.16, 12.16, 0.1
    f0_air = mass_spring_mass_resonance(m1, m2, d)
    # Flow resistivity chosen so f/sigma stays within the Miki fit range at f0.
    medium = miki([f0_air], 7000.0)
    f0_fill = mass_spring_mass_resonance(m1, m2, d, cavity_medium=medium)
    assert f0_fill < f0_air


def test_double_wall_degenerate_f0_above_fl_is_partitioned() -> None:
    # Very light leaves with a wide gap push f0 above f_l = c0/(2 pi d); the
    # transition band collapses but the masks must stay a strict partition
    # (no silent overwrite), giving finite, monotone-ish values everywhere.
    m1 = m2 = 0.3          # kg/m2 (thin membranes)
    d = 0.3                # 300 mm gap
    f0 = mass_spring_mass_resonance(m1, m2, d)
    f_l = 343.0 / (2.0 * math.pi * d)
    assert f0 > f_l        # the degenerate regime
    res = double_wall_transmission_loss(BANDS, m1, m2, d)
    assert np.all(np.isfinite(res.transmission_loss))
    # Below f0 it is still the combined-mass law; above f0 it is the +6 branch.
    lo = float(res.transmission_loss[BANDS <= f0][0])
    assert lo == pytest.approx(
        float(mass_law_transmission_loss(BANDS[BANDS <= f0][0], m1 + m2))
    )


def test_double_wall_rejects_bad_input() -> None:
    with pytest.raises(ValueError, match="gap"):
        double_wall_transmission_loss(BANDS, 10.0, 10.0, -0.1)


def test_plot_language_spanish_and_validation() -> None:
    # The .plot() renderer accepts a language option: Spanish localises the
    # axis labels and title, and an unknown code is rejected up front.
    m = 15.0
    bp = plate_bending_stiffness(6.2e10, 0.006, 0.24)
    fc = coincidence_frequency(m, bp)
    res = single_panel_transmission_loss(BANDS, m, critical_frequency=fc,
                                         loss_factor=0.024)
    ax = res.plot(language="es")
    assert "Frecuencia" in ax.get_xlabel()
    assert "reducción acústica" in ax.get_ylabel()
    assert "Aislamiento" in ax.get_title()
    # English (the default) stays byte-for-byte the original text.
    ax_en = res.plot()
    assert ax_en.get_xlabel() == "Frequency [Hz]"
    assert ax_en.get_ylabel() == "Sound reduction index $R$ [dB]"
    with pytest.raises(ValueError, match="Unknown language"):
        res.plot(language="xx")
