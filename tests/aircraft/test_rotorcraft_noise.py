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

# NORAH2 guidance Table 4, complete: one-third-octave atmospheric attenuation per
# km (dB) at ICAO reference conditions (25 °C, 70 % RH, 101.325 kPa). Independent
# oracle. Per-band tolerance: the module implements the guidance Eq. 27 pure-tone
# coefficient (which the NORAH2 prototype uses), while Table 4 tabulates the SAE
# (Rickley) band mapping; both agree to ~0.05 dB/km below 800 Hz and to
# ~0.3 dB/km up to 3.15 kHz, then drift apart towards 8-10 kHz (up to
# 2.2 dB/km), which the wider high-band tolerances make explicit.
_TABLE4 = {
    10: 0.0, 12.5: 0.0, 16: 0.0, 20: 0.0, 25: 0.0, 31.5: 0.0, 40: 0.0, 50: 0.0,
    63: 0.1, 80: 0.1, 100: 0.2, 125: 0.3, 160: 0.5, 200: 0.7, 250: 1.1,
    315: 1.6, 400: 2.3, 500: 3.1, 630: 4.1, 800: 5.2, 1000: 6.3, 1250: 7.5,
    1600: 8.9, 2000: 10.6, 2500: 13.0, 3150: 16.6, 4000: 22.5, 5000: 31.0,
    6300: 44.9, 8000: 67.6, 10000: 101.0,
}


def _table4_tolerance(freq: float) -> float:
    if freq <= 630.0:
        return 0.1
    if freq <= 3150.0:
        return 0.3
    if freq <= 6300.0:
        return 1.0
    return 2.5


def test_spherical_spreading_matches_inverse_square() -> None:
    assert spherical_spreading_adjustment(60.0) == pytest.approx(0.0)
    assert spherical_spreading_adjustment(600.0) == pytest.approx(-20.0)
    assert spherical_spreading_adjustment(120.0) == pytest.approx(-20.0 * np.log10(2.0))
    with pytest.raises(ValueError, match="distance"):
        spherical_spreading_adjustment(0.0)


@pytest.mark.parametrize("freq", list(_TABLE4))
def test_atmospheric_matches_table4(freq: float) -> None:
    # ΔLa over a 1 km excess path (r = 1060 m) against Table 4, all 31 bands.
    la = atmospheric_adjustment([float(freq)], 1000.0 + 60.0)[0]
    assert la == pytest.approx(-_TABLE4[freq], abs=_table4_tolerance(freq))


def test_atmospheric_low_bands_do_not_warn() -> None:
    # The standard NORAH grid starts at 10 Hz, below the ISO 9613-1 tabulated
    # range; the advisory out-of-range warning is suppressed (alpha ~ 0 there).
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        la = atmospheric_adjustment(np.array(list(_TABLE4), dtype=float), 1060.0)
    assert np.all(la <= 0.0)
    # Above the 10 kHz top of the NORAH grid alpha is large and extrapolated:
    # the advisory warning must still propagate there.
    from phonometry.environmental.air_absorption import AtmosphericAbsorptionWarning

    with pytest.warns(AtmosphericAbsorptionWarning):
        atmospheric_adjustment([16000.0], 1060.0)


def test_adjustments_honour_reference_distance() -> None:
    # Hemispheres recorded at a non-standard polar distance (e.g. 70 m hover
    # rings) pass their distance through 'reference_distance'.
    assert spherical_spreading_adjustment(70.0, reference_distance=70.0) == pytest.approx(0.0)
    assert spherical_spreading_adjustment(700.0, reference_distance=70.0) == pytest.approx(-20.0)
    la = atmospheric_adjustment([1000.0], 70.0, reference_distance=70.0)
    assert la[0] == pytest.approx(0.0)


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


def test_hemisphere_partial_cell_keeps_valid_corners() -> None:
    # Gap-fill semantics (Eq. 14/15): the grid is filled FIRST (each empty bin
    # takes its nearest filled bin), then the bilinear interpolation uses all
    # four corners. A cell with three valid corners must therefore keep their
    # contribution instead of snapping to the single bin nearest to the query.
    h = _synthetic_hemisphere()
    lv = h.levels.copy()
    lv[2, 2, 0] = np.nan  # drop φ=0, θ=90 at 500 Hz
    hole = RotorcraftHemisphere(h.frequencies, h.azimuth, h.polar, lv)
    got = hemisphere_source_level(hole, 22.5, 112.5)[0]  # centre of the φ 0-45/θ 90-135 cell
    # The dropped corner fills with the energetic mean of its four equidistant
    # neighbours (ρ = 45°: (±45°, 90°), (0°, 45°), (0°, 135°)).
    neigh = np.array([95.5, 95.5, 97.75, 93.25])
    fill = 10.0 * np.log10(np.mean(10.0 ** (neigh / 10.0)))
    corners = np.array([fill, 93.25, 95.5, 93.25])  # (0,90) filled, (0,135), (45,90), (45,135)
    expected = 10.0 * np.log10(np.mean(10.0 ** (corners / 10.0)))
    assert got == pytest.approx(expected)


def test_hemisphere_single_row_grid() -> None:
    # A single measured azimuth row (size-1 axis) interpolates along polar only.
    fr = np.array([500.0, 1000.0])
    po = np.array([80.0, 90.0])
    lv = np.array([[[70.0, 68.0], [74.0, 72.0]]])  # shape (1, 2, 2)
    h = RotorcraftHemisphere(fr, np.array([0.0]), po, lv)
    assert np.allclose(hemisphere_source_level(h, 0.0, 80.0), [70.0, 68.0])
    mid = hemisphere_source_level(h, 30.0, 85.0)  # azimuth clamps to the only row
    expected = 10.0 * np.log10(0.5 * 10.0 ** (np.array([70.0, 68.0]) / 10.0)
                               + 0.5 * 10.0 ** (np.array([74.0, 72.0]) / 10.0))
    assert np.allclose(mid, expected)


def test_hemisphere_all_nan_band_returns_nan() -> None:
    # A band with no filled bin anywhere cannot be extrapolated: NaN, documented.
    h = _synthetic_hemisphere()
    lv = h.levels.copy()
    lv[:, :, 1] = np.nan
    hole = RotorcraftHemisphere(h.frequencies, h.azimuth, h.polar, lv)
    out = hemisphere_source_level(hole, 10.0, 70.0)
    assert np.isnan(out[1]) and np.isfinite(out[0]) and np.isfinite(out[2])


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


# Off-node bilinear spot checks against the NORAH2 reference database
# (EASA.2020.FC.06, © EASA — factual reference points from the approach
# hemispheres listed in _TYPE_SPECTRA; the raw database is not redistributed).
# Three query points per rotorcraft type, each in a different grid cell and
# band. Corner order: [L(φ0,θ0), L(φ0,θ1), L(φ1,θ0), L(φ1,θ1)]; the expected
# level is the energy-domain bilinear value (Eq. 13) at the query weights,
# evaluated offline: a pinned regression on real corner data rather than an
# external oracle (the propagation-chain rows below are the external oracle).
_BILINEAR_QUERIES = [
    # (φ, θ, cell φ0/φ1, cell θ0/θ1, band index into _TYPE_BANDS-like triple)
    (5.0, 95.0, (0.0, 10.0), (90.0, 100.0)),
    (-17.0, 117.0, (-20.0, -10.0), (110.0, 120.0)),
    (17.0, 72.0, (10.0, 20.0), (70.0, 80.0)),
]
_BILINEAR_CASES = [
    # type, [(corners, expected)] per query: 500 Hz, 2000 Hz, 125 Hz.
    ("A109", [([82.0, 80.7, 82.0, 79.5], 81.1693), ([70.0, 69.9, 68.8, 68.2], 69.5224),
              ([81.8, 83.7, 81.5, 83.7], 82.1035)]),
    ("AS350", [([72.6, 71.5, 72.2, 71.0], 71.8687), ([68.7, 66.8, 66.4, 65.9], 67.0858),
               ([78.6, 76.8, 78.9, 77.7], 78.5716)]),
    ("B412", [([76.6, 75.7, 76.9, 76.4], 76.4220), ([70.6, 72.1, 69.2, 69.1], 71.0767),
              ([85.8, 84.6, 83.7, 82.9], 84.2671)]),
    ("Cabri", [([69.8, 70.9, 67.9, 71.2], 70.1285), ([63.5, 59.4, 61.4, 59.7], 60.8533),
               ([69.4, 68.0, 71.3, 66.1], 70.2504)]),
    ("EC120", [([69.9, 67.0, 70.7, 68.0], 69.1438), ([67.8, 68.3, 66.6, 66.9], 67.7946),
               ([67.2, 69.8, 67.5, 70.4], 68.1403)]),
    ("EC135", [([75.2, 73.7, 74.6, 73.1], 74.2248), ([69.0, 68.9, 68.8, 68.2], 68.7748),
               ([79.3, 79.2, 79.5, 78.1], 79.2617)]),
    ("R22", [([73.9, 70.6, 74.6, 71.2], 72.9032), ([63.3, 62.4, 63.3, 62.3], 62.6706),
             ([74.6, 74.5, 76.2, 75.7], 75.7006)]),
    ("R44", [([72.0, 72.1, 71.6, 71.6], 71.8310), ([62.7, 61.6, 61.4, 60.7], 61.6740),
             ([80.3, 79.3, 79.6, 79.6], 79.7619)]),
    ("R66", [([73.6, 72.7, 73.3, 72.5], 73.0477), ([67.2, 67.0, 66.1, 65.9], 66.7592),
             ([79.3, 79.2, 77.5, 78.6], 78.2641)]),
    ("S300", [([70.2, 66.9, 68.8, 67.1], 68.4639), ([57.4, 55.7, 58.4, 58.1], 56.9488),
              ([67.8, 69.4, 66.1, 68.0], 67.1040)]),
    ("S92", [([81.4, 83.1, 79.4, 81.7], 81.5928), ([75.5, 72.4, 76.6, 74.6], 74.1725),
             ([95.2, 87.5, 90.9, 89.4], 92.1467)]),
]


@pytest.mark.parametrize(("rotorcraft", "cases"), _BILINEAR_CASES)
def test_reference_bilinear_off_node(rotorcraft: str, cases: list) -> None:
    for (corners, expected), (phi, theta, (a0, a1), (p0, p1)) in zip(cases, _BILINEAR_QUERIES):
        lv = np.array(corners, dtype=np.float64).reshape(2, 2, 1)
        h = RotorcraftHemisphere(np.array([500.0]), np.array([a0, a1]),
                                 np.array([p0, p1]), lv)
        got = hemisphere_source_level(h, phi, theta)[0]
        assert got == pytest.approx(expected, abs=5e-4), (rotorcraft, phi, theta)


# Full propagation-chain oracle: single-emission rows of the NORAH2 prototype
# ARP cases whose TriOrNear id selects a single nearest hemisphere (no
# flight-condition blending), so L(fc,φ,θ) + ΔLs + ΔLa + ΔLg + A-weighting,
# energy-summed, must reproduce the prototype's tabulated LA. The 31-band
# source spectra below are the hemisphere lookups at the row emission angles,
# derived from the reference database (EASA.2020.FC.06, © EASA — factual
# derived values; the raw database is not redistributed). Case 4 rows
# (R22_H1_APP_STD2_NE, mic (0,0), hr 0.2 m, σ = 1e6 Pa·s/m²) reproduce to
# 0.1 dB; the Case 2 rows (R22_H1_DEP_STD1_NE, mic (-300,-400), hr 1.2 m,
# σ = 2e5) exercise softer ground within 0.5 dB.
_CHAIN_BANDS = np.array([
    10.0, 12.5, 16.0, 20.0, 25.0, 31.5, 40.0, 50.0, 63.0, 80.0, 100.0, 125.0,
    160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0, 1250.0,
    1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0, 10000.0])
_CHAIN_ROWS = [
    # (label, spectrum dB @60 m, slant m, hs m, hr m, dp m, sigma, LA ref, tol)
    ("APP_STD2 t=748.00 (53kts_5deg)",
     [72.1, 66.196, 63.3, 77.5, 58.5, 63.2, 79.1, 67.4, 75.6, 71.1, 81.0,
      76.3, 67.104, 65.2, 76.7, 79.0, 82.8, 86.5, 88.2, 85.204, 85.604,
      83.804, 75.0, 73.2, 71.2, 69.8, 70.8, 70.1, 73.1, 73.3, 73.3],
     2377.77, 299.18, 0.2, 2358.902, 1.0e6, 53.16, 0.1),
    ("APP_STD2 t=790.00 (53kts_5deg)",
     [46.0, 49.4, 77.4, 66.2, 50.7, 63.1, 55.3, 60.9, 61.2, 79.7, 73.7, 70.9,
      67.2, 68.4, 74.6, 70.0, 65.8, 64.6, 62.5, 63.9, 64.2, 62.7, 63.4, 62.7,
      59.9, 56.8, 54.8, 54.7, 53.3, 52.2, 52.3],
     1300.08, 205.02, 0.2, 1283.848, 1.0e6, 47.21, 0.1),
    ("APP_STD2 t=825.00 (53kts_12deg)",
     [35.8, 52.2, 70.0, 63.6, 48.4, 59.2, 53.1, 63.3, 61.2, 74.6, 68.7, 61.8,
      65.7, 59.7, 59.7, 63.6, 57.9, 57.7, 58.6, 61.0, 61.9, 64.7, 65.7, 65.6,
      64.1, 61.6, 57.9, 55.8, 56.4, 53.4, 52.9],
     374.55, 43.19, 0.2, 372.072, 1.0e6, 54.93, 0.1),
    ("APP_STD2 t=831.26 (53kts_12deg)",
     [35.8, 52.2, 70.0, 63.6, 48.4, 59.2, 53.1, 63.3, 61.2, 74.6, 68.7, 61.8,
      65.7, 59.7, 59.7, 63.6, 57.9, 57.7, 58.6, 61.0, 61.9, 64.7, 65.7, 65.6,
      64.1, 61.6, 57.9, 55.8, 56.4, 53.4, 52.9],
     223.66, 5.0, 0.2, 223.607, 1.0e6, 55.87, 0.1),
    ("DEP_STD1 t=0.00 (54kts_8.5deg)",
     [47.992, 50.306, 77.582, 78.82, 55.472, 72.727, 74.719, 70.448, 62.609,
      78.785, 80.74, 76.042, 69.093, 71.592, 67.773, 66.552, 67.625, 64.61,
      61.615, 62.097, 69.004, 72.176, 71.897, 69.595, 65.737, 66.233, 65.226,
      62.767, 59.982, 60.554, 56.737],
     721.12, 5.0, 1.2, 721.11, 2.0e5, 46.86, 0.5),
    ("DEP_STD1 t=10.00 (54kts_8.5deg)",
     [47.947, 50.414, 78.59, 78.512, 54.966, 73.537, 74.053, 70.789, 63.086,
      79.737, 80.806, 75.942, 70.201, 71.781, 67.13, 66.899, 67.466, 64.435,
      61.714, 62.613, 69.192, 72.564, 72.477, 70.021, 65.789, 66.575, 65.735,
      63.389, 60.461, 60.856, 57.021],
     993.00, 46.06, 1.2, 991.993, 2.0e5, 51.00, 0.5),
    ("DEP_STD1 t=20.00 (54kts_8.5deg)",
     [47.895, 50.327, 79.023, 78.209, 54.829, 73.844, 73.682, 71.056, 63.942,
      80.128, 80.606, 75.558, 70.72, 71.661, 67.061, 67.086, 67.329, 64.267,
      61.627, 62.9, 68.977, 72.529, 72.645, 70.228, 66.056, 66.648, 65.864,
      63.656, 60.789, 61.004, 57.228],
     1267.45, 87.12, 1.2, 1264.532, 2.0e5, 47.20, 0.5),
]


def _a_weighting_db(frequencies: "np.ndarray") -> "np.ndarray":
    # IEC 61672-1 analytic A-weighting at the exact band centres.
    f = np.asarray(frequencies, dtype=np.float64)
    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217

    def ra(x: "np.ndarray") -> "np.ndarray":
        return (f4**2 * x**4) / ((x**2 + f1**2)
                                 * np.sqrt((x**2 + f2**2) * (x**2 + f3**2))
                                 * (x**2 + f4**2))

    return 20.0 * np.log10(ra(f) / ra(np.array(1000.0)))


@pytest.mark.parametrize(("label", "spectrum", "slant", "hs", "hr", "dp", "sigma",
                          "la_ref", "tol"), _CHAIN_ROWS)
def test_propagation_chain_reproduces_prototype_la(
    label: str, spectrum: list[float], slant: float, hs: float, hr: float,
    dp: float, sigma: float, la_ref: float, tol: float,
) -> None:
    level = (np.asarray(spectrum, dtype=np.float64)
             + spherical_spreading_adjustment(slant)
             + atmospheric_adjustment(_CHAIN_BANDS, slant)
             + ground_effect_adjustment(_CHAIN_BANDS, hs, hr, dp, flow_resistivity=sigma)
             + _a_weighting_db(_CHAIN_BANDS))
    la = float(10.0 * np.log10(np.sum(10.0 ** (level / 10.0))))
    assert la == pytest.approx(la_ref, abs=tol), label
