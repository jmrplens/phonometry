#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Reference sound sources: ISO 6926:2016, read on the printed page.

- Table 1, PDF page 11, folio 5: sigma_r of 0,8 / 0,4 / 0,2 dB; 5.2, same
  page: no band varies by more than +-0,3 dB over the declared supply range.
- 5.4 and 5.5, PDF pages 11-12, folios 5-6: 12 dB / 3 dB, 16 dB / 4 dB, +6 dB.
- 5.6.2 and 5.6.3, PDF page 12, folio 6: 2,83 times Table 1.
- Formula (1), PDF page 17, folio 11: sigma_r about the energy average.
- Formula (2) and C1, C3, PDF pages 17-18, folios 11-12.
- Table 2, PDF page 20, folio 14: sigma_R per environment and arrangement.
- Annex A, Formulae (A.1) to (A.5), PDF pages 22-23, folios 16-17.
- Table B.1, PDF page 24, folio 18: 4,0 dB and 1,0 dB.
- 8.4, PDF page 18, folio 12: the C2 of the calibration is the one the user
  applies; ISO 3741:2010 Eq. (21), PDF page 32, folio 23: L_W(RSS) "corrected to
  the meteorological conditions at the time of test".
- ISO 3743-1:2010 Eq. (14), 8.1.4, PDF page 23 of BS EN ISO 3743-1:2010,
  folio 14, and Annex A, PDF page 31, folio 22: the L_W of Eq. (14) is "under
  the meteorological conditions which occurred at the time and place of the
  test".
- ISO 3743-2:2018 Formula (10), 10.3, PDF page 18, folio 12, and Annex E, PDF
  page 42, folio 36: the L_W of Formula (10) likewise.

No worked example is printed; the oracles are the closed forms and the cells.
"""

from __future__ import annotations

import math
import warnings

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import emission

_THIRDS = np.array(
    [100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000,
     2500, 3150, 4000, 5000, 6300, 8000, 10000],
    dtype=float,
)  # fmt: skip
_AREA_TERM = 10.0 * math.log10(2.0 * math.pi * 2.0**2)


def _calibration(
    levels: float | np.ndarray = 80.0, **kwargs: object
) -> emission.ReferenceSourceCalibration:
    grid = (
        np.full((20, _THIRDS.size), float(levels)) if np.ndim(levels) == 0 else levels
    )
    return emission.reference_source_calibration(
        grid,
        frequencies_hz=_THIRDS,
        arrangement="fixed",
        **kwargs,  # type: ignore[arg-type]
    )


# --- Formula (1), Table 1, Table 2, Annex A --------------------------------------


def test_formula_1_uses_the_energy_average() -> None:
    levels = np.array([80.0, 80.2, 79.9])
    mean = 10.0 * math.log10(np.mean(10.0 ** (levels / 10.0)))
    expected = math.sqrt(np.sum((levels - mean) ** 2) / 2.0)
    got = emission.repeatability_standard_deviation(levels)
    assert got[0] == pytest.approx(expected, abs=1e-12)
    arithmetic = math.sqrt(np.sum((levels - levels.mean()) ** 2) / 2.0)
    assert got[0] != pytest.approx(arithmetic, abs=1e-6)


def test_formula_1_needs_two_repetitions() -> None:
    with pytest.raises(ValueError, match="'levels_db'"):
        emission.repeatability_standard_deviation([80.0])


@pytest.mark.parametrize(
    ("frequency", "paths", "fixed", "reverberation"),
    [
        (50.0, 2.0, 2.0, 2.5),
        (80.0, 2.0, 2.0, 2.5),
        (100.0, 0.8, 0.8, 1.0),
        (160.0, 0.8, 0.8, 1.0),
        (200.0, 0.3, 0.5, 0.3),
        (3150.0, 0.3, 0.5, 0.3),
        (4000.0, 0.3, 1.0, 0.3),
        (10000.0, 0.3, 1.0, 0.3),
        (12500.0, 0.3, 1.0, 0.4),
        (20000.0, 0.3, 1.0, 0.4),
    ],
)
def test_table_2_one_third_octave_cells(
    frequency: float, paths: float, fixed: float, reverberation: float
) -> None:
    def cell(environment: str, arrangement: str | None) -> float:
        return float(
            emission.reference_source_reproducibility_db(
                [frequency],
                environment=environment,
                arrangement=arrangement,  # type: ignore[arg-type]
            )[0]
        )

    assert cell("hemi-anechoic", "paths") == paths
    assert cell("hemi-anechoic", "fixed") == fixed
    assert cell("reverberation-room", None) == reverberation


def test_table_2_octave_cells() -> None:
    got = emission.reference_source_reproducibility_db(
        [63, 125, 250, 2000, 4000, 8000, 16000],
        environment="hemi-anechoic",
        arrangement="fixed",
        bandwidth="octave",
    )
    np.testing.assert_array_equal(got, [2.0, 0.8, 0.5, 0.5, 1.0, 1.0, 1.0])


def test_table_2_refuses_a_band_it_does_not_print() -> None:
    with pytest.raises(ValueError, match="Table 2"):
        emission.reference_source_reproducibility_db(
            [40.0], environment="reverberation-room"
        )
    with pytest.raises(ValueError, match="'arrangement'"):
        emission.reference_source_reproducibility_db(
            [1000.0], environment="hemi-anechoic"
        )


def test_knee_frequency_of_formula_a1() -> None:
    assert emission.knee_frequency(0.2, speed_of_sound=343.0) == pytest.approx(
        343.0 / (2.0 * math.pi * 0.2)
    )


def test_annex_a_c2_for_each_radiation_character() -> None:
    """(A.2) to (A.5) at 30 degC and 95 kPa."""
    pressure = -10.0 * math.log10(95.0 / 101.325)
    ratio = math.log10(303.15 / 296.0)
    unknown = emission.radiation_impedance_correction(
        temperature_c=30.0, static_pressure_kpa=95.0
    )
    assert unknown[0] == pytest.approx(pressure + 7.5 * ratio, abs=1e-12)
    monopole = emission.radiation_impedance_correction(
        temperature_c=30.0,
        static_pressure_kpa=95.0,
        radiation="monopole",
        frequencies_hz=[100.0, 1000.0],
        knee_frequency_hz=500.0,
    )
    np.testing.assert_allclose(
        monopole, [pressure + 15.0 * ratio, pressure + 5.0 * ratio], rtol=0, atol=1e-12
    )
    dipole = emission.radiation_impedance_correction(
        temperature_c=30.0,
        static_pressure_kpa=95.0,
        radiation="dipole",
        frequencies_hz=[500.0, 1000.0],
        knee_frequency_hz=500.0,
    )
    np.testing.assert_allclose(dipole, pressure + 25.0 * ratio, rtol=0, atol=1e-12)


def test_a_dipole_below_its_knee_has_no_c2() -> None:
    with pytest.raises(ValueError, match="dipole"):
        emission.radiation_impedance_correction(
            radiation="dipole", frequencies_hz=[100.0], knee_frequency_hz=500.0
        )
    with pytest.raises(ValueError, match="knee"):
        emission.radiation_impedance_correction(radiation="monopole")


# --- the calibration of clause 8 -----------------------------------------------------


def test_formula_2_on_a_uniform_hemisphere() -> None:
    """C3 at a realistic a(f) = 0,5 dB/m, where its curvature term is 1e-3 dB."""
    cal = _calibration(
        conditions=emission.CalibrationConditions(air_absorption_db_per_m=0.5)
    )
    c1 = 5.0 * math.log10(296.15 / 314.0)
    c2 = 7.5 * math.log10(296.15 / 296.0)
    a0 = 1.0
    c3 = a0 * (1.0053 - 0.0012 * a0) ** 1.6
    np.testing.assert_allclose(
        cal.sound_power_level_db, 80.0 + _AREA_TERM + c1 + c2 + c3, rtol=0, atol=1e-12
    )
    np.testing.assert_allclose(cal.c3_db, c3, rtol=0, atol=1e-12)
    assert cal.c1_db == pytest.approx(c1, abs=1e-12)
    np.testing.assert_allclose(cal.directivity_index_db, 0.0, rtol=0, atol=1e-12)
    np.testing.assert_allclose(cal.surface_pressure_level_db, 80.0, rtol=0, atol=1e-12)


def test_formula_2_at_95_kpa_and_30_degc() -> None:
    """C1 and C2 by hand from the printed formulas, away from the reference.

    C1 = -10 lg(ps/ps0) + 5 lg(theta/314 K) and, for a source whose
    radiation is unknown, C2 = -10 lg(ps/ps0) + 7,5 lg(theta/296 K).
    """
    cal = _calibration(
        conditions=emission.CalibrationConditions(
            temperature_c=30.0, static_pressure_kpa=95.0
        )
    )
    pressure = -10.0 * math.log10(95.0 / 101.325)
    c1 = pressure + 5.0 * math.log10(303.15 / 314.0)
    c2 = pressure + 7.5 * math.log10(303.15 / 296.0)
    assert cal.c1_db == pytest.approx(c1, abs=1e-12)
    np.testing.assert_allclose(cal.c2_db, c2, rtol=0, atol=1e-12)
    np.testing.assert_allclose(
        cal.sound_power_level_db, 80.0 + _AREA_TERM + c1 + c2, rtol=0, atol=1e-12
    )


def test_the_manufacturers_c2_overrides_annex_a() -> None:
    cal = _calibration(c2_db=0.3)
    np.testing.assert_allclose(cal.c2_db, 0.3)
    assert cal.radiation is None


def test_a_calibration_is_read_at_the_conditions_of_a_test() -> None:
    """8.4: L_W less the C2 of the calibration, evaluated at the test."""
    cal = _calibration(
        radiation="monopole",
        knee_frequency_hz=1000.0,
        conditions=emission.CalibrationConditions(temperature_c=20.0),
    )
    pressure = -10.0 * math.log10(90.0 / 101.325)
    ratio = math.log10(293.15 / 296.0)
    c2_test = pressure + np.where(_THIRDS >= 1000.0, 5.0, 15.0) * ratio
    np.testing.assert_allclose(
        cal.sound_power_level_at(_THIRDS, temperature_c=20.0, static_pressure_kpa=90.0),
        cal.sound_power_level_db - c2_test,
        rtol=0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        cal.sound_power_level_at(_THIRDS), cal.sound_power_level_db, rtol=0, atol=1e-12
    )


def test_one_condition_alone_is_refused() -> None:
    cal = _calibration()
    with pytest.raises(ValueError, match="together"):
        cal.sound_power_level_at([1000.0], temperature_c=20.0)


def test_the_manufacturers_c2_cannot_be_read_at_a_test() -> None:
    cal = _calibration(c2_db=0.3)
    with pytest.raises(ValueError, match="manufacturer"):
        cal.sound_power_level_at([1000.0], temperature_c=20.0, static_pressure_kpa=90.0)


def test_the_expanded_uncertainty_is_1_96_sigma_r() -> None:
    cal = _calibration()
    by_band = dict(zip(_THIRDS, cal.expanded_uncertainty_db, strict=True))
    assert by_band[125.0] == pytest.approx(1.96 * 0.8)
    assert by_band[1000.0] == pytest.approx(1.96 * 0.5)
    assert by_band[4000.0] == pytest.approx(1.96 * 1.0)
    assert cal.a_weighted_expanded_uncertainty_db == pytest.approx(1.96 * 0.5)


def test_the_directivity_index_of_3_9() -> None:
    levels = np.full((20, _THIRDS.size), 80.0)
    levels[3] += 6.0
    cal = _calibration(levels)
    mean = 10.0 * math.log10((19 + 10.0**0.6) / 20.0) + 80.0
    np.testing.assert_allclose(
        cal.maximum_directivity_index_db, 86.0 - mean, rtol=0, atol=1e-12
    )


def test_traverse_maxima_give_the_directivity_index() -> None:
    maxima = np.full((20, _THIRDS.size), 83.0)
    cal = _calibration(maximum_levels_db=maxima)
    np.testing.assert_allclose(
        cal.maximum_directivity_index_db, 3.0, rtol=0, atol=1e-12
    )


#: Unequal one-third octaves in the 125 Hz octave (100, 125 and 160 Hz), dB:
#: their energy sum, 85,31 dB, is neither the middle third plus 10 lg 3,
#: 84,77 dB, nor their arithmetic mean plus 10 lg 3, 84,44 dB.
_UNEQUAL_THIRDS_DB = (76.0, 80.0, 83.0)


def _unequal_calibration() -> emission.ReferenceSourceCalibration:
    levels = np.full((20, _THIRDS.size), 80.0)
    levels[:, :3] = _UNEQUAL_THIRDS_DB
    return _calibration(levels)


def _energy_sum_of_the_unequal_thirds() -> float:
    return 10.0 * math.log10(sum(10.0 ** (0.1 * lv) for lv in _UNEQUAL_THIRDS_DB))


def test_octave_bands_are_the_energy_sum_of_their_thirds() -> None:
    cal = _calibration()
    one_third = cal.sound_power_level_db[_THIRDS == 1000.0][0]
    got = cal.sound_power_level_at([1000.0], bandwidth="octave")[0]
    assert got == pytest.approx(one_third + 10.0 * math.log10(3.0), abs=1e-12)
    with pytest.raises(ValueError, match="does not cover"):
        cal.sound_power_level_at([12500.0])


def test_an_octave_of_unequal_thirds_is_their_energy_sum() -> None:
    """76, 80 and 83 dB at the surface sum to 85,31 dB, away from both the
    middle third and the arithmetic mean plus 10 lg 3.
    """
    cal = _unequal_calibration()
    to_power = (
        _AREA_TERM + 5.0 * math.log10(296.15 / 314.0) + 7.5 * math.log10(296.15 / 296.0)
    )
    got = cal.sound_power_level_at([125.0, 250.0], bandwidth="octave")
    expected = np.array(
        [_energy_sum_of_the_unequal_thirds(), 80.0 + 10.0 * math.log10(3.0)]
    )
    np.testing.assert_allclose(got, expected + to_power, rtol=0, atol=1e-12)
    shortcuts = (80.0, sum(_UNEQUAL_THIRDS_DB) / 3.0)
    for shortcut in shortcuts:
        assert abs(expected[0] - shortcut - 10.0 * math.log10(3.0)) > 0.5


def test_an_octave_is_read_only_at_an_octave_mid_band() -> None:
    """160 Hz is a one-third octave; its "octave" would sum 125 to 200 Hz."""
    cal = _calibration()
    with pytest.raises(ValueError, match="160 Hz is not an octave mid-band"):
        cal.sound_power_level_at([160.0], bandwidth="octave")
    with pytest.raises(ValueError, match="160 Hz is not an octave mid-band"):
        emission.reference_source_reproducibility_db(
            [160.0],
            environment="hemi-anechoic",
            arrangement="fixed",
            bandwidth="octave",
        )


def test_the_a_weighted_level_names_its_range() -> None:
    cal = _calibration()
    assert cal.a_weighted_range_hz == (100.0, 10000.0)
    ck = np.array(
        [-19.1, -16.1, -13.4, -10.9, -8.6, -6.6, -4.8, -3.2, -1.9, -0.8, 0.0,
         0.6, 1.0, 1.2, 1.3, 1.2, 1.0, 0.5, -0.1, -1.1, -2.5]
    )  # fmt: skip
    expected = 10.0 * math.log10(
        np.sum(10.0 ** ((cal.sound_power_level_db + ck) / 10.0))
    )
    assert cal.sound_power_level_a_db == pytest.approx(expected, abs=1e-12)


def test_annex_b_replaces_the_lowest_bands_when_they_agree() -> None:
    freqs = np.concatenate([[50.0, 63.0, 80.0], _THIRDS])
    levels = np.full((20, freqs.size), 80.0)
    pressure = emission.reference_source_calibration(
        levels, frequencies_hz=freqs, arrangement="fixed"
    ).sound_power_level_db
    intensity = np.full(freqs.size, np.nan)
    low = freqs <= 315.0
    intensity[low] = pressure[low] + np.where(freqs[low] <= 80.0, 3.5, 0.8)
    cal = emission.reference_source_calibration(
        levels,
        frequencies_hz=freqs,
        arrangement="fixed",
        intensity_sound_power_level_db=intensity,
    )
    assert cal.intensity_agreement is True
    np.testing.assert_array_equal(cal.intensity_bands, freqs <= 80.0)
    np.testing.assert_allclose(cal.sound_power_level_db[:3], pressure[:3] + 3.5)
    np.testing.assert_allclose(cal.sound_power_level_db[3:], pressure[3:])
    intensity[freqs == 200.0] = pressure[freqs == 200.0][0] + 1.2
    refused = emission.reference_source_calibration(
        levels,
        frequencies_hz=freqs,
        arrangement="fixed",
        intensity_sound_power_level_db=intensity,
    )
    assert refused.intensity_agreement is False
    assert not np.any(refused.intensity_bands)


def test_the_calibration_bands_must_be_one_third_octaves_from_50_hz() -> None:
    levels = np.full((20, 2), 80.0)
    with pytest.raises(ValueError, match="'frequencies_hz'"):
        emission.reference_source_calibration(
            levels, frequencies_hz=[40.0, 50.0], arrangement="fixed"
        )


def test_a_calibration_needs_bands() -> None:
    levels = np.full((20, 0), 80.0)
    with pytest.raises(ValueError, match="'frequencies_hz' must be a non-empty"):
        emission.reference_source_calibration(
            levels, frequencies_hz=[], arrangement="fixed"
        )


@pytest.mark.parametrize("bad", ["no positions", math.nan, math.inf])
def test_a_calibration_needs_finite_levels(bad: object) -> None:
    """No position, or one level that is not finite, would carry into every band."""
    if bad == "no positions":
        levels = np.empty((0, _THIRDS.size))
    else:
        levels = np.full((20, _THIRDS.size), 80.0)
        levels[2, 0] = bad
    with pytest.raises(ValueError, match="'levels_db' must hold the finite levels"):
        _calibration(levels)


@pytest.mark.parametrize("name", ["background_levels_db", "maximum_levels_db"])
def test_the_background_and_the_maxima_must_be_finite(name: str) -> None:
    extra = np.full((20, _THIRDS.size), 60.0)
    extra[4, 3] = np.nan
    with pytest.raises(ValueError, match=f"'{name}' must be finite"):
        _calibration(**{name: extra})


def test_the_manufacturers_c2_must_be_finite() -> None:
    with pytest.raises(ValueError, match="'c2_db' must be finite"):
        _calibration(c2_db=np.nan)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("temperature_c", math.nan),
        ("temperature_c", -273.5),
        ("static_pressure_kpa", 0.0),
        ("air_absorption_db_per_m", -0.01),
        ("air_absorption_db_per_m", math.inf),
    ],
)
def test_the_calibration_conditions_refuse_what_formula_2_cannot_read(
    field: str, value: float
) -> None:
    """C1 and C2 take the logarithm of the temperature and of the pressure, and
    C3 reads an attenuation, which is finite and never negative.
    """
    kwargs = {field: value}
    with pytest.raises(ValueError, match=f"'{field}' must be finite"):
        emission.CalibrationConditions(**kwargs)


def test_the_calibration_conditions_hold_their_own_air_absorption() -> None:
    alpha = np.full(_THIRDS.size, 0.01)
    conditions = emission.CalibrationConditions(air_absorption_db_per_m=alpha)
    alpha[:] = 1.0
    np.testing.assert_array_equal(conditions.air_absorption_db_per_m, 0.01)
    default = _calibration()
    reference = _calibration(
        conditions=emission.CalibrationConditions(
            temperature_c=23.0, static_pressure_kpa=101.325
        )
    )
    np.testing.assert_array_equal(
        default.sound_power_level_db, reference.sound_power_level_db
    )


def _hemi_check(radius_end: float) -> emission.FreeFieldCheck:
    grid = emission.qualification_frequencies_hz()
    d = np.arange(0.30, radius_end + 1e-9, 0.02)
    directions = (
        ((1, 1, 1), ("trihedral corner",)),
        ((1, 1, 0.3), ("dihedral corner",)),
        ((0, 1, 0.5), ("boundary centre",)),
        ((1, 0, 0.2), ("closest boundary",)),
        ((-1, 0.5, 0.6), ("unique features",)),
        ((0.3, -1, 0.8), ()),
    )
    level = 90.0 - 20.0 * np.log10(d)
    traverses = [
        emission.MicrophoneTraverse.along(
            u,
            d,
            np.repeat(level[:, None], grid.size, axis=1),
            background_levels_db=np.full(grid.size, 20.0),
            targets=targets,
        )
        for u, targets in directions
    ]
    fit = emission.inverse_square_law_deviations(
        traverses, frequencies_hz=grid, room="hemi-anechoic"
    )
    return emission.check_free_field(
        fit,
        bandwidth="broadband",
        source_directionality=emission.verify_source_directionality(
            np.full((32, grid.size), 80.0), frequencies_hz=grid, room="hemi-anechoic"
        ),
        reflecting_plane_absorption_coefficient=0.02,
        reflecting_plane_margin_m=1.0,
        paths_in_working_area=True,
    )


def test_clause_8_1_reads_the_room_qualification() -> None:
    qualified = _hemi_check(3.0)
    small_room = _hemi_check(1.5)
    with warnings.catch_warnings():
        warnings.simplefilter("error", emission.SoundPowerWarning)
        cal = _calibration(room_qualification=qualified)
    assert cal.room_qualified is True
    with pytest.warns(emission.SoundPowerWarning, match="8.1"):
        small = _calibration(room_qualification=small_room)
    assert small.room_qualified is False


def test_the_annex_b_bands_need_no_qualified_room() -> None:
    """Clause 10: a room not qualified below 100 Hz calibrates 50-80 Hz by Annex B."""
    freqs = np.concatenate([[50.0, 63.0, 80.0], _THIRDS])
    levels = np.full((20, freqs.size), 80.0)
    pressure = emission.reference_source_calibration(
        levels, frequencies_hz=freqs, arrangement="fixed"
    ).sound_power_level_db
    intensity = np.where(freqs <= 315.0, pressure + 0.5, np.nan)
    check = _hemi_check(3.0)  # qualified from 100 Hz to 10 kHz only
    cal = emission.reference_source_calibration(
        levels,
        frequencies_hz=freqs,
        arrangement="fixed",
        intensity_sound_power_level_db=intensity,
        room_qualification=check,
    )
    assert cal.room_qualified is True
    with pytest.warns(emission.SoundPowerWarning, match="8.1"):
        pressure_only = emission.reference_source_calibration(
            levels, frequencies_hz=freqs, arrangement="fixed", room_qualification=check
        )
    assert pressure_only.room_qualified is False


# --- the requirements of clause 5 ---------------------------------------------------


def _steady(cal: emission.ReferenceSourceCalibration) -> np.ndarray:
    return cal.sound_power_level_db[None, :] + np.array([[0.1], [-0.1], [0.05]])


def test_a_steady_flat_omnidirectional_source_complies() -> None:
    cal = _calibration()
    verdict = emission.verify_reference_sound_source(
        cal, repeated_levels_db=_steady(cal), supply_variation_db=0.2
    )
    assert verdict.passes
    assert verdict.stability_met
    assert verdict.supply_met
    assert verdict.spectrum_met
    assert verdict.directivity_met
    assert verdict.core_range_db == pytest.approx(0.0, abs=1e-12)


def test_5_2_holds_the_supply_variation_to_0_3_db() -> None:
    cal = _calibration()
    variation = np.full(_THIRDS.size, 0.3)
    at_limit = emission.verify_reference_sound_source(
        cal, repeated_levels_db=_steady(cal), supply_variation_db=variation
    )
    assert at_limit.supply_met is True
    variation[4] = -0.35
    beyond = emission.verify_reference_sound_source(
        cal, repeated_levels_db=_steady(cal), supply_variation_db=variation
    )
    assert beyond.supply_met is False
    assert not beyond.passes


def test_the_supply_variation_needs_one_value_per_band() -> None:
    cal = _calibration()
    two = [0.1, 0.2]
    with pytest.raises(ValueError, match="'supply_variation_db'"):
        emission.verify_reference_sound_source(cal, supply_variation_db=two)


def test_table_1_limits_the_repeatability() -> None:
    cal = _calibration()
    repeated = _steady(cal)
    repeated[0, _THIRDS == 1000.0] += 0.6
    verdict = emission.verify_reference_sound_source(cal, repeated_levels_db=repeated)
    assert verdict.stability_met is False
    assert not verdict.passes
    np.testing.assert_array_equal(
        verdict.repeatability_limit_db,
        np.where(_THIRDS <= 160.0, 0.4, 0.2),
    )


def test_the_repetitions_are_three_or_five() -> None:
    cal = _calibration()
    four = np.vstack([_steady(cal), _steady(cal)[:1]])
    with pytest.raises(ValueError, match="'repeated_levels_db'"):
        emission.verify_reference_sound_source(cal, repeated_levels_db=four)


def test_a_spectrum_wider_than_12_db_fails_5_4() -> None:
    lw = np.linspace(80.0, 92.5, _THIRDS.size)  # 0,625 dB steps, 12,5 dB range
    verdict = emission.verify_reference_sound_source(
        lw, frequencies_hz=_THIRDS, directivity_index_db=np.zeros(_THIRDS.size),
        repeated_levels_db=np.vstack([lw, lw, lw]),
    )  # fmt: skip
    assert verdict.core_range_db == pytest.approx(12.5)
    assert not verdict.spectrum_met


def test_a_step_of_more_than_3_db_fails_5_4() -> None:
    lw = np.full(_THIRDS.size, 90.0)
    lw[10] = 93.1
    verdict = emission.verify_reference_sound_source(
        lw, frequencies_hz=_THIRDS, directivity_index_db=np.zeros(_THIRDS.size),
        repeated_levels_db=np.vstack([lw, lw, lw]),
    )  # fmt: skip
    assert verdict.adjacent_step_db[10] == pytest.approx(3.1)
    assert not verdict.spectrum_met


def test_an_extended_range_is_held_to_16_db_and_4_db() -> None:
    freqs = np.concatenate([[50.0, 63.0, 80.0], _THIRDS])
    lw = np.concatenate([[80.5, 84.0, 87.8], np.full(_THIRDS.size, 91.5)])
    verdict = emission.verify_reference_sound_source(
        lw, frequencies_hz=freqs, directivity_index_db=np.zeros(freqs.size),
        repeated_levels_db=np.vstack([lw, lw, lw]),
    )  # fmt: skip
    assert verdict.extended_range_db == pytest.approx(11.0)
    assert verdict.adjacent_limit_db[0] == 4.0
    assert verdict.spectrum_met
    lw[0] = 75.0  # 16,5 dB range, 9 dB step
    assert not emission.verify_reference_sound_source(
        lw, frequencies_hz=freqs, directivity_index_db=np.zeros(freqs.size),
        repeated_levels_db=np.vstack([lw, lw, lw]),
    ).spectrum_met  # fmt: skip


@pytest.mark.parametrize(("lowest", "met"), [(72.0, False), (72.5, True)])
def test_the_16_db_range_is_judged_on_its_own(*, lowest: float, met: bool) -> None:
    """Every step within 4 dB and 3 dB; only the extended range decides.

    From ``lowest`` the three extended bands rise 4 dB a band, then the core
    rises from 83 dB to 88,5 dB: an extended range of 16,5 dB fails, 16,0 dB
    is on the limit and passes.
    """
    freqs = np.concatenate([[50.0, 63.0, 80.0], _THIRDS])
    lw = np.concatenate(
        [lowest + np.array([0.0, 4.0, 8.0]), np.linspace(83.0, 88.5, _THIRDS.size)]
    )
    verdict = emission.verify_reference_sound_source(lw, frequencies_hz=freqs)
    assert np.all(verdict.adjacent_step_db <= verdict.adjacent_limit_db + 1e-12)
    assert verdict.core_range_db <= 12.0
    assert verdict.extended_range_db == pytest.approx(88.5 - lowest, abs=1e-12)
    assert verdict.spectrum_met is met


def test_a_missing_core_band_fails_5_4() -> None:
    lw = np.full(_THIRDS.size - 1, 90.0)
    verdict = emission.verify_reference_sound_source(
        lw, frequencies_hz=_THIRDS[:-1], directivity_index_db=np.zeros(lw.size),
        repeated_levels_db=np.vstack([lw, lw, lw]),
    )  # fmt: skip
    assert not verdict.frequency_range_met
    assert not verdict.passes


def test_a_directivity_index_above_6_db_fails_5_5() -> None:
    lw = np.full(_THIRDS.size, 90.0)
    directivity = np.zeros(_THIRDS.size)
    directivity[5] = 6.2
    verdict = emission.verify_reference_sound_source(
        lw, frequencies_hz=_THIRDS, directivity_index_db=directivity,
        repeated_levels_db=np.vstack([lw, lw, lw]),
    )  # fmt: skip
    assert verdict.directivity_met is False
    labelled = emission.verify_reference_sound_source(
        lw, frequencies_hz=_THIRDS, repeated_levels_db=np.vstack([lw, lw, lw]),
        supply_variation_db=0.1, reverberation_rooms_only=True,
    )  # fmt: skip
    assert labelled.directivity_met is True
    assert labelled.passes


def test_unjudged_requirements_hold_the_verdict() -> None:
    verdict = emission.verify_reference_sound_source(_calibration())
    assert verdict.not_judged == ("temporal steadiness", "supply variation")
    assert verdict.stability_met is None
    assert verdict.supply_met is None
    assert not verdict.passes
    with pytest.raises(TypeError, match="passes"):
        bool(verdict)


def test_a_calibration_brings_its_own_bands() -> None:
    calibration = _calibration()
    with pytest.raises(ValueError, match="'frequencies_hz'"):
        emission.verify_reference_sound_source(calibration, frequencies_hz=_THIRDS)
    levels = np.full(3, 90.0)
    with pytest.raises(ValueError, match="'frequencies_hz'"):
        emission.verify_reference_sound_source(levels)


# --- 5.6: recalibration -----------------------------------------------------------------


def test_a_change_beyond_2_83_times_table_1_calls_for_recalibration() -> None:
    freqs = [80.0, 125.0, 1000.0]
    reference = np.array([85.0, 88.0, 90.0])
    within = emission.verify_reference_source_drift(
        reference, reference + [2.26, -1.13, 0.56], frequencies_hz=freqs
    )
    np.testing.assert_allclose(within.limit_db, [2.264, 1.132, 0.566])
    assert within.passes
    assert not within.recalibration_required
    beyond = emission.verify_reference_source_drift(
        reference, reference + [0.0, 0.0, 0.57], frequencies_hz=freqs
    )
    assert beyond.recalibration_required
    with pytest.raises(TypeError, match="passes"):
        bool(beyond)


# --- the comparison methods consume the calibration ----------------------------------


def test_iso_3741_reads_the_one_third_octave_bands() -> None:
    cal = _calibration()
    freqs = np.array([500.0, 1000.0, 2000.0])
    levels = np.full((6, 3), 75.0)
    ref_levels = np.full((6, 3), 72.0)
    from_object = emission.sound_power_comparison(
        levels, ref_levels, cal, frequencies=freqs
    )
    at_test = cal.sound_power_level_at(
        freqs, temperature_c=23.0, static_pressure_kpa=101.325
    )
    from_levels = emission.sound_power_comparison(
        levels, ref_levels, at_test, frequencies=freqs
    )
    np.testing.assert_allclose(
        from_object.sound_power_level, from_levels.sound_power_level, rtol=0, atol=1e-12
    )
    with pytest.raises(ValueError, match="'frequencies'"):
        emission.sound_power_comparison(levels, ref_levels, cal)


def test_iso_3741_carries_the_calibration_to_the_test_conditions() -> None:
    """Eq. (21) at 20 degC and 90 kPa, with C2 of both sources by hand.

    The calibration's C2 (A.5, radiation unknown) at the test is 0,483 dB and
    ISO 3741's own C2 is 0,452 dB: L_W = L_W,ref - 0,483 + 4 + 0,452.
    """
    cal = _calibration()
    freqs = np.array([500.0, 1000.0, 2000.0])
    lp = np.full(3, 70.0)
    got = emission.sound_power_comparison(
        lp + 4.0,
        lp,
        cal,
        frequencies=freqs,
        temperature_c=20.0,
        static_pressure_kpa=90.0,
    )
    pressure = -10.0 * math.log10(90.0 / 101.325)
    c2_rss = pressure + 7.5 * math.log10(293.15 / 296.0)
    c2_3741 = pressure + 15.0 * math.log10(293.15 / 296.0)
    assert c2_rss == pytest.approx(0.483, abs=5e-4)
    expected = cal.sound_power_level_at(freqs) - c2_rss + 4.0 + c2_3741
    np.testing.assert_allclose(got.sound_power_level, expected, rtol=0, atol=1e-12)


def test_iso_3741_energy_comparison_reads_the_calibration() -> None:
    cal = _calibration()
    freqs = np.array([500.0, 1000.0, 2000.0])
    events = np.full((6, 3), 78.0)
    ref_levels = np.full((6, 3), 72.0)
    from_object = emission.sound_energy_comparison(
        events,
        ref_levels,
        cal,
        frequencies=freqs,
        temperature_c=20.0,
        static_pressure_kpa=90.0,
    )
    at_test = cal.sound_power_level_at(
        freqs, temperature_c=20.0, static_pressure_kpa=90.0
    )
    from_levels = emission.sound_energy_comparison(
        events,
        ref_levels,
        at_test,
        frequencies=freqs,
        temperature_c=20.0,
        static_pressure_kpa=90.0,
    )
    np.testing.assert_allclose(
        from_object.sound_energy_level,
        from_levels.sound_energy_level,
        rtol=0,
        atol=1e-12,
    )
    with pytest.raises(ValueError, match="'frequencies'"):
        emission.sound_energy_comparison(events, ref_levels, cal)


def test_iso_3747_reads_the_octave_bands() -> None:
    """Eq. (9) corrects the reference source's levels instead: read as calibrated."""
    cal = _calibration()
    freqs = np.array([250.0, 500.0, 1000.0, 2000.0])
    st = np.full((4, 4), 84.0)
    rss = np.full((4, 4), 82.0)
    background = np.full(4, 60.0)
    from_object = emission.sound_power_in_situ(
        st, rss, cal, freqs, background_levels=background, temperature_c=20.0,
        static_pressure_kpa=90.0,
    )  # fmt: skip
    from_levels = emission.sound_power_in_situ(
        st,
        rss,
        cal.sound_power_level_at(freqs, bandwidth="octave"),
        freqs,
        background_levels=background,
        temperature_c=20.0,
        static_pressure_kpa=90.0,
    )
    np.testing.assert_allclose(
        from_object.sound_power_level, from_levels.sound_power_level, rtol=0, atol=1e-12
    )


def test_iso_3747_energy_reads_the_octave_bands() -> None:
    cal = _calibration()
    freqs = np.array([250.0, 500.0, 1000.0, 2000.0])
    events = np.full((4, 5, 4), 86.0)  # (positions, events, bands)
    rss = np.full((4, 4), 82.0)
    background = np.full(4, 60.0)
    from_object = emission.sound_energy_in_situ(
        events, rss, cal, freqs, background_levels=background
    )
    from_levels = emission.sound_energy_in_situ(
        events,
        rss,
        cal.sound_power_level_at(freqs, bandwidth="octave"),
        freqs,
        background_levels=background,
    )
    np.testing.assert_allclose(
        from_object.sound_energy_level,
        from_levels.sound_energy_level,
        rtol=0,
        atol=1e-12,
    )


def _c2_at_20_degc_and_90_kpa(exponent: float) -> float:
    """Annex A's C2 at 20 degC and 90 kPa with the temperature term's factor."""
    return -10.0 * math.log10(90.0 / 101.325) + exponent * math.log10(293.15 / 296.0)


def test_iso_3743_1_reads_the_octave_bands_at_the_test_conditions() -> None:
    """Eq. (14) at 20 degC and 90 kPa, with C2 of both sources by hand.

    The calibration's thirds are equal, so each octave is one third plus
    10 lg 3, less the calibration's C2 at the test (A.5, radiation unknown),
    0,483 dB; Annex A of ISO 3743-1, 0,452 dB, carries the result back.
    """
    cal = _calibration()
    freqs = np.array([125.0, 500.0, 2000.0])
    st = np.full((6, 3), 74.0)
    rss = np.full((6, 3), 70.0)
    background = np.full(3, 40.0)  # margins above 15 dB: K1 = K1(RSS) = 0
    got = emission.sound_power_hard_walled(
        st, rss, cal, freqs, background_levels=background, temperature_c=20.0,
        static_pressure_kpa=90.0,
    )  # fmt: skip
    c2_rss = _c2_at_20_degc_and_90_kpa(7.5)
    c2_3743 = _c2_at_20_degc_and_90_kpa(15.0)
    assert c2_rss == pytest.approx(0.483, abs=5e-4)
    assert c2_3743 == pytest.approx(0.452, abs=5e-4)
    octave = cal.sound_power_level_at(freqs) + 10.0 * math.log10(3.0) - c2_rss
    np.testing.assert_allclose(got.reference_power_level, octave, rtol=0, atol=1e-12)
    np.testing.assert_allclose(got.sound_power_level, octave + 4.0, rtol=0, atol=1e-12)
    np.testing.assert_allclose(
        got.sound_power_level_ref, octave + 4.0 + c2_3743, rtol=0, atol=1e-12
    )
    at_test = cal.sound_power_level_at(
        freqs, bandwidth="octave", temperature_c=20.0, static_pressure_kpa=90.0
    )
    from_levels = emission.sound_power_hard_walled(
        st, rss, at_test, freqs, background_levels=background, temperature_c=20.0,
        static_pressure_kpa=90.0,
    )  # fmt: skip
    np.testing.assert_allclose(
        got.sound_power_level, from_levels.sound_power_level, rtol=0, atol=1e-12
    )


def test_iso_3743_1_energy_reads_the_calibration() -> None:
    cal = _calibration()
    freqs = np.array([250.0, 1000.0, 4000.0])
    events = np.full((6, 3), 78.0)  # one measurement over five events
    rss = np.full((6, 3), 72.0)
    background = np.full(3, 40.0)
    from_object = emission.sound_energy_hard_walled(
        events, rss, cal, freqs, events=5, background_levels=background,
        integration_time_s=10.0, temperature_c=20.0, static_pressure_kpa=90.0,
    )  # fmt: skip
    at_test = cal.sound_power_level_at(
        freqs, bandwidth="octave", temperature_c=20.0, static_pressure_kpa=90.0
    )
    from_levels = emission.sound_energy_hard_walled(
        events, rss, at_test, freqs, events=5, background_levels=background,
        integration_time_s=10.0, temperature_c=20.0, static_pressure_kpa=90.0,
    )  # fmt: skip
    np.testing.assert_allclose(
        from_object.sound_energy_level,
        from_levels.sound_energy_level,
        rtol=0,
        atol=1e-12,
    )


def test_iso_3743_2_comparison_reads_the_calibration() -> None:
    """Formula (10) with the calibration read at the test (Annex E)."""
    cal = _calibration()
    freqs = np.array([125.0, 500.0, 2000.0, 8000.0])
    st = np.full((6, 4), 75.0)
    rss = np.full((6, 4), 71.0)
    background = np.full(4, 50.0)  # margins above 10 dB: no Table 4 correction
    got = emission.sound_power_special_room_comparison(
        st, rss, cal, freqs, background_levels=background, temperature_c=20.0,
        static_pressure_kpa=90.0,
    )  # fmt: skip
    octave = (
        cal.sound_power_level_at(freqs)
        + 10.0 * math.log10(3.0)
        - _c2_at_20_degc_and_90_kpa(7.5)
    )
    np.testing.assert_allclose(got.reference_power_level, octave, rtol=0, atol=1e-12)
    np.testing.assert_allclose(got.sound_power_level, octave + 4.0, rtol=0, atol=1e-12)
    np.testing.assert_allclose(
        got.sound_power_level_ref,
        octave + 4.0 + _c2_at_20_degc_and_90_kpa(15.0),
        rtol=0,
        atol=1e-12,
    )


_SUITABILITY_FREQS = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
_TABLE_1_DB = np.array([5.0, 3.0, 3.0, 3.0, 3.0, 3.0, 4.0])


def test_iso_3743_2_suitability_reads_the_calibration_at_the_test() -> None:
    """6.7 compares the room's Formula (9) level, which Annex E reads as the
    power under the conditions of the test, with the calibration read there:
    each octave three equal thirds plus 10 lg 3, less the calibration's own
    C2 at 20 degC and 90 kPa (A.5, radiation unknown), 0,483 dB.
    """
    cal = _calibration()
    octave = (
        cal.sound_power_level_at(_SUITABILITY_FREQS)
        + 10.0 * math.log10(3.0)
        - _c2_at_20_degc_and_90_kpa(7.5)
    )
    measured = octave - _TABLE_1_DB  # every band on its Table 1 limit, low
    check = emission.check_special_room_suitability(
        measured, cal, _SUITABILITY_FREQS, temperature_c=20.0, static_pressure_kpa=90.0
    )
    np.testing.assert_allclose(
        check.calibrated_power_level_db, octave, rtol=0, atol=1e-12
    )
    np.testing.assert_allclose(check.measured_power_level_db, measured, rtol=0, atol=0)
    np.testing.assert_allclose(check.difference_db, -_TABLE_1_DB, rtol=0, atol=1e-9)
    assert check.passes


def test_iso_3743_2_suitability_sums_unequal_thirds_at_the_test() -> None:
    """The 125 Hz octave of thirds at 76, 80 and 83 dB, by hand: their energy
    sum over the 2 m hemisphere, with C1 and C2 at the reference conditions,
    less the calibration's C2 at 20 degC and 90 kPa (A.5, radiation unknown).
    """
    cal = _unequal_calibration()
    as_calibrated = (
        _AREA_TERM + 5.0 * math.log10(296.15 / 314.0) + 7.5 * math.log10(296.15 / 296.0)
    )
    octave = (
        np.array(
            [_energy_sum_of_the_unequal_thirds()]
            + [80.0 + 10.0 * math.log10(3.0)] * (_SUITABILITY_FREQS.size - 1)
        )
        + as_calibrated
        - _c2_at_20_degc_and_90_kpa(7.5)
    )
    check = emission.check_special_room_suitability(
        octave + 1.0,
        cal,
        _SUITABILITY_FREQS,
        temperature_c=20.0,
        static_pressure_kpa=90.0,
    )
    np.testing.assert_allclose(
        check.calibrated_power_level_db, octave, rtol=0, atol=1e-12
    )
    np.testing.assert_allclose(check.difference_db, 1.0, rtol=0, atol=1e-9)
    assert check.passes


def test_iso_3743_2_suitability_fails_against_the_calibration_left_at_23_degc() -> None:
    """Read at the default conditions instead, the calibration stands 0,482 dB
    higher, and a room on its Table 1 limits at the test is beyond them.
    """
    cal = _calibration()
    at_test = cal.sound_power_level_at(
        _SUITABILITY_FREQS,
        bandwidth="octave",
        temperature_c=20.0,
        static_pressure_kpa=90.0,
    )
    check = emission.check_special_room_suitability(
        at_test - _TABLE_1_DB, cal, _SUITABILITY_FREQS
    )
    shift = _c2_at_20_degc_and_90_kpa(7.5) - 7.5 * math.log10(296.15 / 296.0)
    np.testing.assert_allclose(
        check.difference_db, -_TABLE_1_DB - shift, rtol=0, atol=1e-9
    )
    assert not bool(np.any(check.band_within))
    assert not check.passes


def test_iso_3743_2_suitability_from_the_levels_read_at_the_test() -> None:
    """The calibration and the levels it gives at the test judge alike, and
    levels are taken as they are whatever the conditions say.
    """
    cal = _calibration()
    at_test = cal.sound_power_level_at(
        _SUITABILITY_FREQS,
        bandwidth="octave",
        temperature_c=20.0,
        static_pressure_kpa=90.0,
    )
    measured = at_test + np.array([1.0, -0.5, 0.2, 0.0, 0.4, -1.1, 2.0])
    from_object = emission.check_special_room_suitability(
        measured, cal, _SUITABILITY_FREQS, temperature_c=20.0, static_pressure_kpa=90.0
    )
    from_levels = emission.check_special_room_suitability(
        measured,
        at_test,
        _SUITABILITY_FREQS,
        temperature_c=20.0,
        static_pressure_kpa=90.0,
    )
    at_default = emission.check_special_room_suitability(
        measured, at_test, _SUITABILITY_FREQS
    )
    for other in (from_levels, at_default):
        np.testing.assert_array_equal(
            other.calibrated_power_level_db, from_object.calibrated_power_level_db
        )
        np.testing.assert_array_equal(other.difference_db, from_object.difference_db)


def test_iso_3743_2_suitability_refuses_a_calibration_it_cannot_read() -> None:
    """The 125 Hz octave needs the 100 Hz third, and a manufacturer's C2 has
    no value at the test but the manufacturer's.
    """
    above_200 = emission.reference_source_calibration(
        np.full((20, 16), 80.0), frequencies_hz=_THIRDS[3:19], arrangement="fixed"
    )
    manufacturers = _calibration(c2_db=0.3)
    measured = np.full(_SUITABILITY_FREQS.size, 92.0)
    with pytest.raises(ValueError, match="does not cover the 100 Hz"):
        emission.check_special_room_suitability(measured, above_200, _SUITABILITY_FREQS)
    with pytest.raises(ValueError, match="manufacturer"):
        emission.check_special_room_suitability(
            measured, manufacturers, _SUITABILITY_FREQS
        )


def test_iso_3743_refuses_a_calibration_it_cannot_read() -> None:
    """The 63 Hz octave needs the 50 Hz third, and a manufacturer's C2 has no
    value at the test but the manufacturer's.
    """
    st = np.full((6, 2), 75.0)
    rss = np.full((6, 2), 71.0)
    background = np.full(2, 40.0)
    calibration = _calibration()
    manufacturers = _calibration(c2_db=0.3)
    with pytest.raises(ValueError, match="does not cover the 50 Hz"):
        emission.sound_power_hard_walled(
            st, rss, calibration, [63.0, 125.0], background_levels=background
        )
    with pytest.raises(ValueError, match="manufacturer"):
        emission.sound_power_special_room_comparison(
            st, rss, manufacturers, [125.0, 250.0], background_levels=background
        )


def test_iso_9295_reads_the_bands_of_the_16_khz_octave() -> None:
    freqs = np.array([12500.0, 16000.0, 20000.0])
    cal = emission.reference_source_calibration(
        np.full((20, 3), 70.0), frequencies_hz=freqs, arrangement="paths"
    )
    st = np.array([60.0, 58.0, 55.0])
    far = np.array([62.0, 61.0, 57.0])
    from_object = emission.high_frequency_sound_power_comparison(
        st,
        frequencies_hz=freqs,
        reference_pressure_levels_db=far,
        reference_sound_power_levels_db=cal,
        temperature_c=20.0,
        static_pressure_kpa=90.0,
    )
    at_test = cal.sound_power_level_at(
        freqs, temperature_c=20.0, static_pressure_kpa=90.0
    )
    np.testing.assert_allclose(
        from_object.sound_power_level,
        at_test - far + st + from_object.c2,
        rtol=0,
        atol=1e-12,
    )
    with pytest.raises(ValueError, match="per hertz"):
        emission.high_frequency_sound_power_comparison(
            st,
            frequencies_hz=freqs,
            reference_pressure_levels_db=far,
            reference_sound_power_levels_db=cal,
            noise_bandwidth_hz=10.0,
        )


# --- plots ---------------------------------------------------------------------------------


def test_the_calibration_plot_draws_one_bar_per_band() -> None:
    ax = _calibration().plot()
    from matplotlib.patches import Rectangle

    assert len([p for p in ax.patches if isinstance(p, Rectangle)]) == _THIRDS.size
    plt.close("all")


def test_the_verdict_plot_shares_each_limit() -> None:
    cal = _calibration()
    ax = emission.verify_reference_sound_source(
        cal, repeated_levels_db=_steady(cal), supply_variation_db=0.15
    ).plot()
    labels = ax.get_legend_handles_labels()[1]
    assert "Directivity index / 6 dB" in labels
    assert "Supply variation / 0.3 dB" in labels
    assert "Range, 100 Hz to 10 kHz / 12 dB" in labels
    assert "complies" in ax.get_title()
    plt.close("all")


def test_the_verdict_plot_draws_the_range_requirement() -> None:
    """A source that fails on the 12 dB range alone shows it above the limit."""
    lw = 80.0 + 1.2 * np.arange(_THIRDS.size)  # 24 dB over 100 Hz to 10 kHz
    verdict = emission.verify_reference_sound_source(
        lw, frequencies_hz=_THIRDS, repeated_levels_db=np.vstack([lw, lw, lw]),
        directivity_index_db=np.full(_THIRDS.size, 2.0), supply_variation_db=0.1,
    )  # fmt: skip
    ax = verdict.plot()
    segments = ax.collections[0].get_segments()
    assert segments[0][0][1] == pytest.approx(24.0 / 12.0)
    assert "does not comply" in ax.get_title()
    plt.close("all")


def test_a_judged_failure_titles_the_verdict_before_missing_data() -> None:
    """The spectrum fails; the steadiness is not judged: "does not comply"."""
    lw = 80.0 + 1.2 * np.arange(_THIRDS.size)
    verdict = emission.verify_reference_sound_source(lw, frequencies_hz=_THIRDS)
    assert verdict.not_judged
    ax = verdict.plot()
    assert ax.get_title().endswith("does not comply")
    plt.close("all")
    ax = verdict.plot(language="es")
    assert ax.get_title().endswith("no cumple")
    plt.close("all")
    pending = emission.verify_reference_sound_source(_calibration())
    ax = pending.plot()
    assert ax.get_title().endswith("not all judged")
    plt.close("all")


def test_the_drift_plot_draws_the_change() -> None:
    result = emission.verify_reference_source_drift(
        [85.0, 88.0], [85.1, 88.9], frequencies_hz=[500.0, 1000.0]
    )
    ax = result.plot(language="es")
    assert "requiere recalibración" in ax.get_title()
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("change", [0.1, 0.9])
def test_the_drift_title_fits_the_default_figure(language: str, change: float) -> None:
    result = emission.verify_reference_source_drift(
        np.full(_THIRDS.size, 85.0),
        np.full(_THIRDS.size, 85.0 + change),
        frequencies_hz=_THIRDS,
    )
    ax = result.plot(language=language)
    figure = ax.figure
    figure.tight_layout()
    figure.canvas.draw()
    box = ax.title.get_window_extent()
    width = figure.get_window_extent().width
    assert box.x0 >= 0.0
    assert box.x1 <= width
    plt.close("all")
