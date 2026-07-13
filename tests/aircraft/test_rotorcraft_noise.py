#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for the rotorcraft hemisphere method (ECAC Doc 32 / NORAH2).

Oracles: the guidance Table 4 (one-third-octave atmospheric attenuation per km at
ICAO reference conditions) for the atmospheric term; closed-form spherical
spreading; analytic ground-effect limits; and exact hemisphere interpolation at
the grid nodes.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import numpy as np
import pytest

from phonometry.aircraft.rotorcraft_noise import (
    RotorcraftHemisphere,
    atmospheric_adjustment,
    ground_effect_adjustment,
    hemisphere_source_level,
    spherical_spreading_adjustment,
)

# NORAH2 guidance Table 4: one-third-octave atmospheric attenuation per km (dB) at
# ICAO reference conditions (25 °C, 70 % RH, 101.325 kPa). Independent oracle.
_TABLE4 = {
    100: 0.2, 160: 0.5, 250: 1.1, 400: 2.3, 630: 4.1, 1000: 6.3,
    1600: 8.9, 2000: 10.6, 2500: 13.0, 4000: 22.5,
}


def test_spherical_spreading_matches_inverse_square() -> None:
    assert spherical_spreading_adjustment(60.0) == pytest.approx(0.0)
    assert spherical_spreading_adjustment(600.0) == pytest.approx(-20.0)
    assert spherical_spreading_adjustment(120.0) == pytest.approx(-20.0 * np.log10(2.0))
    with pytest.raises(ValueError, match="distance"):
        spherical_spreading_adjustment(0.0)


@pytest.mark.parametrize("freq", list(_TABLE4))
def test_atmospheric_matches_table4(freq: int) -> None:
    # ΔLa over a 1 km excess path (r = 1060 m) reproduces −Table 4 (ISO 9613-1
    # pure-tone coefficient at ICAO reference); tight below 4 kHz.
    la = atmospheric_adjustment([float(freq)], 1000.0 + 60.0)[0]
    assert la == pytest.approx(-_TABLE4[freq], abs=0.7)


def test_atmospheric_reference_distance_is_zero() -> None:
    la = atmospheric_adjustment([1000.0, 4000.0], 60.0)
    assert np.allclose(la, 0.0)


def test_ground_effect_hard_ground_reinforces_low_frequency() -> None:
    # Over a hard surface the direct and reflected rays are nearly in phase at low
    # frequency and small path difference, giving a positive (up to ~+6 dB) ΔLg.
    lg = ground_effect_adjustment([50.0], 100.0, 1.5, 200.0, flow_resistivity="G")[0]
    assert 0.0 < lg <= 6.02
    # Soft ground absorbs the reflection, so its low-frequency gain is smaller.
    lg_soft = ground_effect_adjustment([50.0], 100.0, 1.5, 200.0, flow_resistivity="D")[0]
    assert lg_soft < lg


def test_ground_effect_class_letters_and_values_agree() -> None:
    by_letter = ground_effect_adjustment([500.0, 1000.0], 100.0, 1.5, 300.0, flow_resistivity="G")
    by_value = ground_effect_adjustment([500.0, 1000.0], 100.0, 1.5, 300.0, flow_resistivity=20.0e6)
    assert np.allclose(by_letter, by_value)


def test_ground_effect_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="horizontal_distance"):
        ground_effect_adjustment([500.0], 100.0, 1.5, 0.0)
    with pytest.raises(ValueError, match="flow_resistivity"):
        ground_effect_adjustment([500.0], 100.0, 1.5, 300.0, flow_resistivity="Z")


def _synthetic_hemisphere() -> RotorcraftHemisphere:
    az = np.array([-90.0, -45.0, 0.0, 45.0, 90.0])
    po = np.array([0.0, 45.0, 90.0, 135.0, 180.0])
    fr = np.array([500.0, 1000.0, 2000.0])
    # Level falls linearly with polar angle and is symmetric in azimuth.
    lv = np.zeros((az.size, po.size, fr.size))
    for i in range(az.size):
        for j, t in enumerate(po):
            lv[i, j, :] = np.array([100.0, 98.0, 96.0]) - 0.05 * t
    return RotorcraftHemisphere(fr, az, po, lv)


def test_hemisphere_exact_at_nodes() -> None:
    h = _synthetic_hemisphere()
    assert np.allclose(hemisphere_source_level(h, 0.0, 90.0), [95.5, 93.5, 91.5])
    assert np.allclose(hemisphere_source_level(h, -45.0, 0.0), [100.0, 98.0, 96.0])


def test_hemisphere_energy_bilinear_midpoint() -> None:
    h = _synthetic_hemisphere()
    # Between θ = 0 (100 dB) and θ = 45 (97.75 dB) at φ = 0, band 500 Hz: energy mean.
    got = hemisphere_source_level(h, 0.0, 22.5)[0]
    expected = 10.0 * np.log10(0.5 * 10.0 ** (100.0 / 10.0) + 0.5 * 10.0 ** (97.75 / 10.0))
    assert got == pytest.approx(expected)


def test_hemisphere_clips_outside_grid() -> None:
    h = _synthetic_hemisphere()
    # Beyond the grid edges the lookup clamps to the boundary node.
    assert np.allclose(hemisphere_source_level(h, 200.0, 300.0),
                       hemisphere_source_level(h, 90.0, 180.0))


def test_hemisphere_nearest_bin_fill_for_missing() -> None:
    h = _synthetic_hemisphere()
    lv = h.levels.copy()
    lv[2, 2, 0] = np.nan  # drop φ=0, θ=90, 500 Hz
    hole = RotorcraftHemisphere(h.frequencies, h.azimuth, h.polar, lv)
    out = hemisphere_source_level(hole, 0.0, 90.0)
    # The four axis-neighbours (±45°,90°), (0°,45°), (0°,135°) are all exactly
    # equidistant (ρ = 45°), so the fill is their energetic average (Eq. 14/15).
    neigh = np.array([95.5, 95.5, 97.75, 93.25])  # 100 − 0.05·θ at θ = 90,90,45,135
    assert out[0] == pytest.approx(10.0 * np.log10(np.mean(10.0 ** (neigh / 10.0))))
    assert out[1] == pytest.approx(93.5)  # other bands untouched


def test_hemisphere_plot() -> None:
    assert _synthetic_hemisphere().plot() is not None


# A 3×3×3 sub-grid of real hemisphere levels (dB at 60 m) transcribed from the
# NORAH2 reference database (helicopter A109, approach 60 kt / 3° descent;
# EASA.2020.FC.06, © EASA), azimuth φ ∈ {-10, 0, 10}°, polar θ ∈ {80, 90, 100}°,
# bands 500 / 1000 / 2000 Hz. Used as an independent oracle for the hemisphere
# interpolation (the raw NORAH data is not redistributed).
_A109_PHI = np.array([-10.0, 0.0, 10.0])
_A109_THETA = np.array([80.0, 90.0, 100.0])
_A109_FREQ = np.array([500.0, 1000.0, 2000.0])
_A109_LEVELS = np.array([
    [[79.6, 74.8, 72.2], [77.1, 73.5, 71.2], [76.0, 73.1, 69.9]],
    [[78.7, 73.9, 73.0], [76.0, 72.8, 71.5], [74.3, 71.8, 70.0]],
    [[77.0, 73.9, 73.4], [74.3, 74.1, 71.8], [72.5, 73.9, 70.5]],
])


def _a109_hemisphere() -> RotorcraftHemisphere:
    return RotorcraftHemisphere(_A109_FREQ, _A109_PHI, _A109_THETA, _A109_LEVELS)


def test_reference_hemisphere_exact_at_nodes() -> None:
    h = _a109_hemisphere()
    assert np.allclose(hemisphere_source_level(h, 0.0, 90.0), [76.0, 72.8, 71.5])
    assert np.allclose(hemisphere_source_level(h, -10.0, 80.0), [79.6, 74.8, 72.2])


def test_reference_hemisphere_energy_bilinear_between_real_nodes() -> None:
    # Midpoint of the φ=0/10, θ=80/90 cell at 500 Hz: energy mean of the 4 corners.
    h = _a109_hemisphere()
    got = hemisphere_source_level(h, 5.0, 85.0)[0]
    corners = np.array([78.7, 77.0, 76.0, 74.3])  # (0,80),(10,80),(0,90),(10,90)
    expected = 10.0 * np.log10(np.mean(10.0 ** (corners / 10.0)))
    assert got == pytest.approx(expected)


# Reference source spectra (dB at 60 m) at the φ = 0°, θ = 90° node for every
# rotorcraft type in the NORAH2 database (approach condition; EASA.2020.FC.06,
# © EASA — factual reference points, the raw database is not redistributed),
# over the 63 Hz - 8 kHz octave grid. Exercises the interpolation pipeline over
# every model and across the frequency range.
_TYPE_BANDS = np.array([63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
_TYPE_SPECTRA = [
    ("A109", [78.6, 83.6, 86.1, 82.0, 76.7, 70.9, 64.6, 56.1]),
    ("AS350", [75.6, 73.0, 71.8, 72.6, 69.7, 65.8, 59.1, 51.5]),
    ("B412", [85.6, 83.5, 79.4, 76.6, 74.2, 70.3, 62.6, 51.4]),
    ("Cabri", [66.1, 72.2, 69.9, 69.8, 64.8, 61.5, 54.7, 47.3]),
    ("EC120", [76.5, 70.4, 72.5, 69.9, 68.2, 66.3, 62.4, 58.1]),
    ("EC135", [68.7, 79.4, 76.7, 75.2, 72.9, 68.9, 65.5, 62.9]),
    ("R22", [67.6, 72.7, 74.7, 73.9, 70.7, 66.3, 60.1, 54.8]),
    ("R44", [70.9, 80.2, 78.5, 72.0, 68.7, 62.0, 55.6, 45.6]),
    ("R66", [83.1, 81.8, 79.0, 73.6, 68.8, 66.3, 64.3, 62.5]),
    ("S300", [66.6, 66.2, 67.9, 70.2, 65.8, 62.2, 53.3, 43.8]),
    ("S92", [87.1, 87.4, 85.5, 81.4, 78.8, 76.2, 71.3, 65.1]),
]


@pytest.mark.parametrize(("rotorcraft", "spectrum"), _TYPE_SPECTRA)
def test_reference_hemisphere_all_types(rotorcraft: str, spectrum: list[float]) -> None:
    # Place the reference spectrum at the φ=0, θ=90 corner and distinct (offset)
    # values at the other three corners, so recovering it at that exact node
    # genuinely exercises the azimuth/polar indexing and corner weighting.
    spec = np.asarray(spectrum, dtype=np.float64)
    az = np.array([0.0, 10.0])
    po = np.array([80.0, 90.0])
    levels = np.empty((az.size, po.size, spec.size))
    levels[0, 1, :] = spec                 # φ=0, θ=90 (the queried node)
    levels[0, 0, :] = spec - 3.0
    levels[1, 1, :] = spec + 2.0
    levels[1, 0, :] = spec - 5.0
    h = RotorcraftHemisphere(_TYPE_BANDS, az, po, levels)
    assert np.allclose(hemisphere_source_level(h, 0.0, 90.0), spec)
    # Physically-plausible helicopter spectrum: mid-frequency content, HF roll-off.
    assert spec[-1] < spec[3]
