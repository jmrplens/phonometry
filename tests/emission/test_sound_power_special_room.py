#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound power in a special reverberation test room: ISO 3743-2:2018.

Normative anchors (ISO 3743-2:2018, second edition, read on the printed pages):
- 6.2: V >= 70 m3; V <= 300 m3 with the 4 kHz and 8 kHz octaves (direct
  method; the NOTE relaxes it for the comparison method).
- 6.3, Formula (1): R = 1 + 257/(f V^(1/3)); NOTE: R = 1 + cS/(8Vf); limits
  0,9 R Tnom to 1,1 R Tnom (0,8 and 1,2 above 6,3 kHz); 0,5 s <= Tnom <= 1,0 s.
- 6.4: floor alpha < 0,06; each wall and the ceiling within 0,5 and 1,5 times
  the mean of the walls and ceiling.
- 6.6, Formula (2): H(theta + 5 degC) within +/-10 %.
- 6.7, Table 1: +/-5 dB at 125 Hz, +/-3 dB from 250 Hz to 4 kHz, +/-4 dB at
  8 kHz.
- 9.4, Formula (4), (5), Table 3; 9.5 classes at 2,3 dB and 4 dB.
- 9.8, Table 4: 4, 5 -> 2 dB; 6, 7, 8 -> 1 dB; 9, 10 -> 0,5 dB; > 10 -> 0.
- 10.1, Formula (8); 10.2, Formula (9): LW = Lp - 10 lg(Tnom/T0) + 10 lg(V/V0)
  - 13 dB; 10.3, Formula (10): LWe = Lpe + (LWr - Lpr).
- 11, Table 5: 5,0 / 3,0 / 2,0 / 3,0 dB and 2,0 dB A-weighted; 11.5 EXAMPLE:
  U = 2 sqrt(2^2 + 2^2) = 5,7 dB; Table D.1, sigma_R0 = 2 row: 2,1 / 2,8 /
  4,5 dB.
- B.5, Formula (B.2): Tnom = T1000/1,06, R(1 000 Hz) = 1,06 for 70 m3.
- Annex E: C2 of ISO 3743-1:2010 Annex A; Table F.1 = Table B.1 of Part 1.
"""

from __future__ import annotations

import dataclasses
import math
import warnings

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import emission

FREQS = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0])
#: Levels of the source under test at six positions, dB.
ST = np.array(
    [
        [74.0, 78.5, 80.1, 79.4, 77.0, 73.2, 68.1],
        [73.1, 78.0, 79.6, 79.0, 76.6, 72.9, 67.7],
        [74.8, 79.1, 80.4, 79.9, 77.5, 73.6, 68.4],
        [73.6, 78.4, 79.9, 79.2, 76.9, 73.0, 67.9],
        [74.4, 78.8, 80.3, 79.6, 77.3, 73.4, 68.3],
        [73.3, 78.2, 79.8, 79.1, 76.8, 72.8, 67.8],
    ]
)
#: Levels of the reference source at six positions, dB.
RSS = ST + np.array([3.0, 2.5, 2.0, 2.2, 2.4, 2.1, 1.8])
#: Calibrated octave-band power of the reference source, dB re 1 pW.
LW_RSS = np.array([88.0, 91.0, 92.5, 92.0, 90.5, 87.0, 83.0])
#: Background far below both sources (margins above 10 dB), dB.
BACKGROUND = np.array([55.0, 58.0, 60.0, 59.0, 55.0, 50.0, 45.0])
#: Table 5, typed in from the printed page.
SIGMA_R0_TABLE_5 = np.array([5.0, 3.0, 2.0, 2.0, 2.0, 2.0, 3.0])
#: Table F.1, k = 2..8.
CK_TABLE_F1 = np.array([-16.1, -8.6, -3.2, 0.0, 1.2, 1.0, -1.1])
#: One-third-octave centres of Figure B.3.
THIRDS = np.array(
    [100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0,
     1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0, 10000.0]
)  # fmt: skip


def _energy_mean(levels: np.ndarray, axis: int | None = None) -> np.ndarray:
    return np.asarray(10.0 * np.log10(np.mean(10.0 ** (0.1 * levels), axis=axis)))


def _direct(**kwargs: object) -> emission.SpecialRoomSoundPowerResult:
    kwargs.setdefault("background_levels", BACKGROUND)
    kwargs.setdefault("volume_m3", 70.0)
    kwargs.setdefault("nominal_reverberation_time_s", 0.73)
    return emission.sound_power_special_room(ST, FREQS, **kwargs)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# 6.3, Formula (1) and the centring of Tnom
# --------------------------------------------------------------------------
def test_formula1_gives_the_1_06_of_formula_b2_for_70_m3() -> None:
    """B.5: 1,06 is the value of R at 1 000 Hz for a 70 m3 room."""
    r = emission.reverberation_parameter([1000.0], 70.0)
    assert round(float(r[0]), 2) == 1.06
    assert float(r[0]) == pytest.approx(1.0 + 257.0 / (1000.0 * 70.0 ** (1 / 3)))


def test_the_note_form_agrees_with_formula1_for_a_cube_at_342_7_m_s() -> None:
    """For a cube S = 6 V^(2/3), so cS/(8V) = 257/V^(1/3) when c = 257 x 8/6."""
    volume = 70.0
    surface = 6.0 * volume ** (2.0 / 3.0)
    note = emission.reverberation_parameter(
        THIRDS, volume, surface_area_m2=surface, speed_of_sound=257.0 * 8.0 / 6.0
    )
    np.testing.assert_allclose(note, emission.reverberation_parameter(THIRDS, volume))


def test_the_note_form_needs_both_its_inputs() -> None:
    with pytest.raises(ValueError, match="surface_area_m2"):
        emission.reverberation_parameter(THIRDS, 70.0, surface_area_m2=100.0)


def test_a_room_that_follows_the_curve_centres_on_formula_b2() -> None:
    """If the specified curve is exactly obtained, Tnom = T1000 / R(1 000)."""
    r = emission.reverberation_parameter(THIRDS, 70.0)
    t = 0.8 * r / r[10]
    check = emission.check_special_room_reverberation(t, THIRDS, volume_m3=70.0)
    assert check.centred
    assert check.nominal_reverberation_time_s == pytest.approx(0.8 / float(r[10]))
    np.testing.assert_allclose(check.normalized_ratio, 1.0, atol=1e-12)
    assert check.passes


def test_centring_balances_the_worst_bands_against_their_tolerances() -> None:
    """With one tolerance throughout, the centred scale puts the largest and
    the smallest ratio equally far above and below 1.
    """
    r = emission.reverberation_parameter(THIRDS[:-2], 70.0)
    shape = np.linspace(0.95, 1.05, r.size) ** 2
    check = emission.check_special_room_reverberation(
        0.7 * r * shape, THIRDS[:-2], volume_m3=70.0
    )
    ratio = check.normalized_ratio
    assert float(ratio.max()) - 1.0 == pytest.approx(
        1.0 - float(ratio.min()), abs=1e-12
    )


def test_centring_weighs_each_band_by_its_own_tolerance() -> None:
    """Above 6,3 kHz the half-width is 0,2, so a deviation there counts half
    as much as below it. The oracle is an independent brute-force scan of
    k = 1/Tnom minimising the largest |k T/R - 1| / w; a uniform 0,1 would
    centre this room near 0,753 s instead.
    """
    r = emission.reverberation_parameter(THIRDS, 70.0)
    shape = np.ones(THIRDS.size)
    shape[0] = 0.96
    shape[-2:] = [1.16, 1.19]  # the 8 kHz and 10 kHz thirds run long
    t = 0.7 * r * shape
    check = emission.check_special_room_reverberation(t, THIRDS, volume_m3=70.0)
    q = t / r
    width = np.where(THIRDS > 7000.0, 0.2, 0.1)
    scales = np.linspace(1.0, 2.0, 1_000_001)
    worst = np.max(np.abs(scales[:, None] * q[None, :] - 1.0) / width[None, :], axis=1)
    assert check.nominal_reverberation_time_s == pytest.approx(
        1.0 / float(scales[int(np.argmin(worst))]), abs=1e-5
    )
    assert check.nominal_reverberation_time_s == pytest.approx(0.72567, abs=1e-5)


def test_bands_above_6_3_khz_take_the_wider_tolerance() -> None:
    check = emission.check_special_room_reverberation(
        np.full(THIRDS.size, 0.8),
        THIRDS,
        volume_m3=70.0,
        nominal_reverberation_time_s=0.8,
    )
    np.testing.assert_array_equal(check.lower_limit[-3:], [0.9, 0.8, 0.8])
    np.testing.assert_array_equal(check.upper_limit[-3:], [1.1, 1.2, 1.2])


def test_a_supplied_nominal_time_is_checked_as_given() -> None:
    r = emission.reverberation_parameter(THIRDS, 70.0)
    check = emission.check_special_room_reverberation(
        0.73 * r * 1.15, THIRDS, volume_m3=70.0, nominal_reverberation_time_s=0.73
    )
    assert not check.centred
    assert not bool(np.any(check.band_within[:-2]))
    assert not check.passes


@pytest.mark.parametrize(
    ("tnom", "ok"), [(0.5, True), (0.49, False), (1.0, True), (1.01, False)]
)
def test_nominal_time_between_0_5_and_1_0_s(tnom: float, *, ok: bool) -> None:
    r = emission.reverberation_parameter(THIRDS, 70.0)
    check = emission.check_special_room_reverberation(tnom * r, THIRDS, volume_m3=70.0)
    assert check.nominal_in_range is ok


@pytest.mark.parametrize(
    ("volume", "method", "large", "small"),
    [
        (70.0, "direct", True, True),
        (69.0, "direct", False, True),
        (300.0, "direct", True, True),
        (301.0, "direct", True, False),
        (301.0, "comparison", True, True),
    ],
)
def test_volume_criteria_of_6_2(
    volume: float, method: str, *, large: bool, small: bool
) -> None:
    r = emission.reverberation_parameter(THIRDS, volume)
    check = emission.check_special_room_reverberation(
        0.7 * r,
        THIRDS,
        volume_m3=volume,
        method=method,  # type: ignore[arg-type]
    )
    assert check.volume_large_enough is large
    assert check.volume_small_enough is small


def test_the_300_m3_ceiling_needs_the_8_khz_octave_in_range() -> None:
    r = emission.reverberation_parameter(THIRDS[:-3], 400.0)
    check = emission.check_special_room_reverberation(
        0.7 * r, THIRDS[:-3], volume_m3=400.0
    )
    assert check.volume_small_enough


@pytest.mark.parametrize(
    ("humidity", "temperature", "stable"),
    [
        # 50 (20 + 5) = 1 250 against 1 250 x 1,10 = 1 375 and x 0,90 = 1 125
        (55.0, 20.0, True),  # 1 375: at +10 %
        (56.0, 20.0, False),
        (45.0, 20.0, True),  # 1 125: at -10 %
        (40.0, 22.0, False),  # 1 080
        # the + 5 degC decides this one: 80 (10 + 5) = 1 200 is -4 %, whereas
        # 80 x 10 = 800 against 50 x 20 = 1 000 would be -20 %
        (80.0, 10.0, True),
    ],
)
def test_climate_product_of_6_6(
    humidity: float, temperature: float, *, stable: bool
) -> None:
    r = emission.reverberation_parameter(THIRDS, 70.0)
    check = emission.check_special_room_reverberation(
        0.7 * r, THIRDS, volume_m3=70.0,
        relative_humidity_percent=humidity, temperature_c=temperature,
        reverberation_relative_humidity_percent=50.0, reverberation_temperature_c=20.0,
    )  # fmt: skip
    assert check.climate_stable is stable


def test_climate_given_in_part_is_refused() -> None:
    r = emission.reverberation_parameter(THIRDS, 70.0)
    with pytest.raises(ValueError, match=r"6\.6"):
        emission.check_special_room_reverberation(
            0.7 * r, THIRDS, volume_m3=70.0, relative_humidity_percent=50.0
        )


def test_reverberation_check_has_no_truth_value() -> None:
    r = emission.reverberation_parameter(THIRDS, 70.0)
    check = emission.check_special_room_reverberation(0.7 * r, THIRDS, volume_m3=70.0)
    with pytest.raises(TypeError, match="passes"):
        bool(check)


def test_surface_check_has_no_truth_value() -> None:
    check = emission.check_special_room_surfaces(
        np.full((5, 7), 0.15), [0.03] * 7, FREQS
    )
    with pytest.raises(TypeError, match="passes"):
        bool(check)


def test_suitability_check_has_no_truth_value() -> None:
    check = emission.check_special_room_suitability(LW_RSS + 1.0, LW_RSS, FREQS)
    with pytest.raises(TypeError, match="passes"):
        bool(check)


# --------------------------------------------------------------------------
# 6.4 and 6.7
# --------------------------------------------------------------------------
def test_surfaces_within_half_and_one_and_a_half_times_the_mean() -> None:
    walls = np.array([[0.2] * 7, [0.1] * 7, [0.3] * 7])  # mean 0,2: ratios 1, 0,5, 1,5
    check = emission.check_special_room_surfaces(walls, [0.05] * 7, FREQS)
    np.testing.assert_allclose(check.mean_absorption, 0.2)
    assert bool(np.all(check.surfaces_uniform))
    assert check.passes


def test_surface_within_names_the_wall_and_the_band() -> None:
    walls = np.full((5, 7), 0.15)
    walls[1, 0] = 0.40  # mean 0,2 at 125 Hz: 0,4/0,2 = 2 and 0,15/0,2 = 0,75
    check = emission.check_special_room_surfaces(walls, [0.03] * 7, FREQS)
    expected = np.ones((5, 7), dtype=bool)
    expected[1, 0] = False
    np.testing.assert_array_equal(check.surface_within, expected)
    np.testing.assert_array_equal(check.surfaces_uniform, expected.all(axis=0))


def test_a_floor_at_0_06_is_not_reflective_enough() -> None:
    walls = np.full((5, 7), 0.15)
    check = emission.check_special_room_surfaces(walls, [0.06] * 7, FREQS)
    assert not bool(np.any(check.floor_reflective))
    assert not check.passes


def test_area_weighting_moves_the_mean() -> None:
    walls = np.array([[0.1] * 7, [0.4] * 7])
    plain = emission.check_special_room_surfaces(walls, [0.02] * 7, FREQS)
    weighted = emission.check_special_room_surfaces(
        walls, [0.02] * 7, FREQS, surface_areas_m2=[30.0, 10.0]
    )
    np.testing.assert_allclose(plain.mean_absorption, 0.25)
    np.testing.assert_allclose(weighted.mean_absorption, 0.175)
    assert not plain.passes  # 0,1/0,25 = 0,4
    assert not weighted.passes  # 0,4/0,175 = 2,29


def test_suitability_limits_of_table_1() -> None:
    measured = LW_RSS + np.array([5.0, 3.0, -3.0, 3.0, -3.0, 3.0, -4.0])
    check = emission.check_special_room_suitability(measured, LW_RSS, FREQS)
    np.testing.assert_array_equal(check.limit_db, [5.0, 3.0, 3.0, 3.0, 3.0, 3.0, 4.0])
    assert check.passes
    worse = measured + np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.0])
    assert not emission.check_special_room_suitability(worse, LW_RSS, FREQS).passes


def test_suitability_refuses_63_hz() -> None:
    freqs = np.array([63.0, 125.0])
    with pytest.raises(ValueError, match="Table 1"):
        emission.check_special_room_suitability([80.0, 80.0], [80.0, 80.0], freqs)


# --------------------------------------------------------------------------
# 9.4, 9.5, Table 3
# --------------------------------------------------------------------------
#: Table 3, typed in from the printed page: (sM class, band group) -> NS for
#: NM = 3, 6, 12.
TABLE_3 = {
    ("broadband", 125.0): (1, 1, 1),
    ("broadband", 1000.0): (1, 1, 1),
    ("narrow-band", 125.0): (1, 1, 1),
    ("narrow-band", 250.0): (2, 2, 1),
    ("narrow-band", 500.0): (2, 2, 1),
    ("narrow-band", 1000.0): (2, 1, 1),
    ("narrow-band", 8000.0): (2, 1, 1),
    ("discrete tone", 125.0): (3, 2, 2),
    ("discrete tone", 250.0): (4, 3, 2),
    ("discrete tone", 500.0): (4, 2, 2),
    ("discrete tone", 1000.0): (3, 2, 1),
    ("discrete tone", 4000.0): (3, 2, 1),
}
#: A standard deviation inside each class.
S_M_OF = {"broadband": 1.0, "narrow-band": 3.0, "discrete tone": 4.5}


def _survey(s_m: float, n_bands: int = 1) -> np.ndarray:
    """Six levels spanning at most 5 dB, whose deviation about their
    arithmetic mean is ``s_m``.
    """
    pattern = np.array([-1.0, 1.0, -1.0, 1.0, 0.0, 0.0])
    scale = s_m / float(np.std(pattern, ddof=1))
    return 70.0 + scale * pattern[:, None] * np.ones((1, n_bands))


@pytest.mark.parametrize(("key", "row"), list(TABLE_3.items()))
@pytest.mark.parametrize("column", [0, 1, 2])
def test_table3_cells(
    key: tuple[str, float], row: tuple[int, int, int], column: int
) -> None:
    cls, band = key
    survey = _survey(S_M_OF[cls])
    if cls == "discrete tone":
        # 4,5 dB about the mean needs a range above 5 dB, where Formula (5)
        # takes over; the class is what matters here, not the mean.
        survey = 70.0 + np.array([[-4.6], [4.6], [-4.6], [4.6], [0.0], [0.0]])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", emission.SoundPowerWarning)
        plan = emission.special_room_source_locations(
            survey, [band], microphone_positions=(3, 6, 12)[column]
        )
    assert plan.spectral_character == (cls,)
    assert int(plan.source_locations[0]) == row[column]


@pytest.mark.parametrize(
    ("cls", "row"),
    [
        ("broadband", (1, 1, 1)),
        ("narrow-band", (2, 2, 1)),
        ("discrete tone", (4, 3, 2)),
    ],
)
def test_table3_a_weighted_row(cls: str, row: tuple[int, int, int]) -> None:
    a_levels = (
        70.0 + np.array([-4.6, 4.6, -4.6, 4.6, 0.0, 0.0])
        if cls == "discrete tone"
        else _survey(S_M_OF[cls])[:, 0]
    )
    for column, mics in enumerate((3, 6, 12)):
        plan = emission.special_room_source_locations(
            _survey(1.0),
            [1000.0],
            microphone_positions=mics,
            a_weighted_levels=a_levels,
        )
        assert plan.a_weighted_spectral_character == cls
        assert plan.a_weighted_source_locations == row[column]


@pytest.mark.parametrize(("s_m", "cls"), [(2.29, "broadband"), (2.3, "narrow-band")])
def test_9_5_lower_class_edge(s_m: float, cls: str) -> None:
    """Six alternating levels keep the range under 5 dB, so the deviation is
    about the arithmetic mean and lands on the 2,3 dB edge as typed.
    """
    pattern = np.array([-1.0, 1.0, -1.0, 1.0, -1.0, 1.0])
    scale = s_m / float(np.std(pattern, ddof=1))
    survey = 70.0 + scale * pattern[:, None]
    plan = emission.special_room_source_locations(survey, [1000.0])
    assert plan.spectral_character == (cls,)


@pytest.mark.parametrize(
    ("s_m", "cls"),
    [
        (2.29, "broadband"),
        (2.3, "narrow-band"),
        (4.0, "narrow-band"),
        (4.01, "discrete tone"),
    ],
)
def test_9_5_class_edges_are_those_of_table_3(s_m: float, cls: str) -> None:
    """Above 2,74 dB six levels cannot stay within 5 dB of each other, so the
    upper edge is reached only through Formula (5); the classification itself
    is read at the edge directly.
    """
    from phonometry.emission.sound_power_special_room import _sm_class

    assert _sm_class(s_m) == cls


def test_formula5_takes_over_above_a_5_db_range() -> None:
    """9.4: a range above 5 dB replaces the arithmetic mean by Formula (5),
    and Formula (4) is taken about that mean.
    """
    levels = np.array([60.0, 66.0, 60.0, 60.0, 60.0, 60.0])
    plan = emission.special_room_source_locations(levels[:, None], [500.0])
    energy = float(_energy_mean(levels))
    expected = math.sqrt(float(np.sum((levels - energy) ** 2)) / 5.0)
    assert float(plan.standard_deviation_db[0]) == pytest.approx(expected, abs=1e-12)
    arithmetic = np.array([60.0, 65.0, 60.0, 60.0, 60.0, 60.0])
    plan = emission.special_room_source_locations(arithmetic[:, None], [500.0])
    assert float(plan.standard_deviation_db[0]) == pytest.approx(
        float(np.std(arithmetic, ddof=1)), abs=1e-12
    )


def test_a_5_db_range_read_in_decimal_keeps_the_arithmetic_mean() -> None:
    """9.4 keeps the arithmetic mean while the range "is not greater than
    5 dB". 64,4 dB and 59,4 dB span 5,0 dB as read, which in binary is
    5,000 000 000 000 007 dB; the range is settled before the comparison, so
    Formula (5) does not take over, for the octave bands and the A-weighted
    row alike.
    """
    levels = np.array([64.4, 59.4, 61.0, 62.3, 63.1, 60.2])
    assert float(np.ptp(levels)) > 5.0  # noqa: PLR2004
    plan = emission.special_room_source_locations(
        levels[:, None], [500.0], a_weighted_levels=levels
    )
    arithmetic = float(np.std(levels, ddof=1))
    assert float(plan.standard_deviation_db[0]) == pytest.approx(arithmetic, abs=1e-12)
    assert plan.a_weighted_standard_deviation_db == pytest.approx(arithmetic, abs=1e-12)


def test_table3_has_no_column_for_four_microphones() -> None:
    survey = _survey(1.0, FREQS.size)
    with pytest.raises(ValueError, match="microphone_positions"):
        emission.special_room_source_locations(survey, FREQS, microphone_positions=4)


# --------------------------------------------------------------------------
# 9.8, Table 4
# --------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("margin", "correction"),
    [
        (4.0, 2.0), (5.0, 2.0), (6.0, 1.0), (7.0, 1.0), (8.0, 1.0),
        (9.0, 0.5), (10.0, 0.5), (10.01, 0.0), (25.0, 0.0),
        # the nearest whole decibel: 5,4 -> 5 and 5,5 -> 6
        (5.4, 2.0), (5.5, 1.0), (9.6, 0.5),
    ],
)  # fmt: skip
def test_table4_rows(margin: float, correction: float) -> None:
    assert float(emission.special_room_background_correction(80.0, 80.0 - margin)) == (
        correction
    )


def test_table4_below_4_db_takes_the_4_db_row_and_warns() -> None:
    with pytest.warns(emission.SoundPowerWarning, match="below 4 dB"):
        correction = emission.special_room_background_correction([80.0], [77.0])
    assert float(correction[0]) == 2.0


# --------------------------------------------------------------------------
# 10.1, 10.2, 10.3
# --------------------------------------------------------------------------
def test_direct_method_is_formula9_of_the_energy_mean() -> None:
    res = _direct()
    expected = (
        _energy_mean(ST, 0) - 10.0 * math.log10(0.73) + 10.0 * math.log10(70.0) - 13.0
    )
    np.testing.assert_allclose(res.sound_power_level, expected, atol=1e-12)
    assert res.method == "direct"
    assert bool(np.all(res.background_requirement_met))
    assert np.all(res.background_correction == 0.0)
    assert np.all(np.isnan(res.mean_reference_level))
    assert res.volume_m3 == 70.0


def test_direct_method_corrects_each_position_by_table4() -> None:
    background = np.tile(BACKGROUND, (6, 1))
    background[0, 3] = ST[0, 3] - 6.2  # 1 dB at this position only
    res = _direct(background_levels=background)
    corrected = ST.copy()
    corrected[0, 3] -= 1.0
    assert res.mean_pressure_level[3] == pytest.approx(
        float(_energy_mean(corrected[:, 3])), abs=1e-12
    )
    assert res.background_correction[3] == pytest.approx(
        float(_energy_mean(ST[:, 3]) - _energy_mean(corrected[:, 3])), abs=1e-12
    )


def test_source_locations_all_enter_formula8() -> None:
    locations = np.stack([ST, ST + 2.0])
    res = emission.sound_power_special_room(
        locations, FREQS, volume_m3=70.0, nominal_reverberation_time_s=0.73,
        background_levels=BACKGROUND,
    )  # fmt: skip
    np.testing.assert_allclose(
        res.mean_pressure_level, _energy_mean(locations.reshape(-1, FREQS.size), 0)
    )
    assert res.source_positions == 2


def test_a_weighted_levels_take_table4_before_formula9() -> None:
    """A 5 dB margin takes the 2 dB of Table 4 at every position before
    Formula (8), so the mean is 82 dB, not 84 dB.
    """
    res = _direct(a_weighted_levels=np.full(6, 84.0), a_weighted_background_levels=79.0)
    room = -10.0 * math.log10(0.73) + 10.0 * math.log10(70.0) - 13.0
    assert res.mean_a_weighted_level == pytest.approx(82.0, abs=1e-12)
    assert res.sound_power_level_a_direct == pytest.approx(82.0 + room, abs=1e-12)
    assert res.background_requirement_met_a


def test_a_weighted_level_by_formula9_directly() -> None:
    a_levels = np.array([84.0, 83.5, 84.6, 84.1, 84.4, 83.8])
    res = _direct(a_weighted_levels=a_levels, a_weighted_background_levels=60.0)
    room = -10.0 * math.log10(0.73) + 10.0 * math.log10(70.0) - 13.0
    assert res.sound_power_level_a_direct == pytest.approx(
        float(_energy_mean(a_levels)) + room, abs=1e-12
    )
    assert res.background_requirement_met_a
    total = 10.0 * np.log10(
        np.sum(10.0 ** (0.1 * (res.sound_power_level + CK_TABLE_F1)))
    )
    assert res.sound_power_level_a == pytest.approx(float(total), abs=1e-12)


def test_direct_method_warns_outside_6_2_and_6_3() -> None:
    with pytest.warns(emission.SoundPowerWarning, match=r"6\.2"):
        _direct(volume_m3=350.0)


def test_direct_method_warns_below_70_m3() -> None:
    with pytest.warns(emission.SoundPowerWarning, match=r"at least 70"):
        _direct(volume_m3=60.0)


def test_nominal_time_outside_6_3_warns() -> None:
    with pytest.warns(emission.SoundPowerWarning, match=r"between 0\.5 s and 1 s"):
        _direct(nominal_reverberation_time_s=1.2)


def test_comparison_method_is_formula10() -> None:
    res = emission.sound_power_special_room_comparison(
        ST, RSS, LW_RSS, FREQS, background_levels=BACKGROUND
    )
    expected = _energy_mean(ST, 0) + (LW_RSS - _energy_mean(RSS, 0))
    np.testing.assert_allclose(res.sound_power_level, expected, atol=1e-12)
    assert res.method == "comparison"
    assert math.isnan(res.volume_m3)
    np.testing.assert_allclose(res.reference_power_level, LW_RSS)


def test_comparison_a_weighted_total_is_annex_f() -> None:
    """10.4 sends the octave bands of the comparison method to Annex F,
    although F.1 names only 10.2: Formula (F.1) with Table F.1 applies.
    """
    res = emission.sound_power_special_room_comparison(
        ST, RSS, LW_RSS, FREQS, background_levels=BACKGROUND
    )
    total = 10.0 * np.log10(
        np.sum(10.0 ** (0.1 * (res.sound_power_level + CK_TABLE_F1)))
    )
    assert res.sound_power_level_a == pytest.approx(float(total), abs=1e-12)
    assert math.isnan(res.sound_power_level_a_direct)


def test_comparison_reference_below_six_positions_warns() -> None:
    with pytest.warns(emission.SoundPowerWarning, match=r"10\.3"):
        emission.sound_power_special_room_comparison(
            ST, RSS[:4], LW_RSS, FREQS, background_levels=BACKGROUND
        )


def test_comparison_background_margin_of_the_reference_counts() -> None:
    bg_ref = np.tile(BACKGROUND, (6, 1))
    bg_ref[:, 0] = RSS[:, 0] - 3.0
    with pytest.warns(emission.SoundPowerWarning, match="below 4 dB"):
        res = emission.sound_power_special_room_comparison(
            ST,
            RSS,
            LW_RSS,
            FREQS,
            background_levels=BACKGROUND,
            background_levels_ref=bg_ref,
        )
    assert not bool(res.background_requirement_met[0])


def test_comparison_corrects_the_reference_levels_by_table4() -> None:
    """10.3 a): Lpr is the mean of the reference levels after the Table 4
    correction at each position (9.8), and Formula (10) uses it.
    """
    margins = np.array([5.0, 7.0, 9.0, 12.0, 20.0, 6.0])
    bg_ref = np.tile(BACKGROUND, (6, 1))
    bg_ref[:, 0] = RSS[:, 0] - margins
    table4 = np.array([2.0, 1.0, 0.5, 0.0, 0.0, 1.0])
    res = emission.sound_power_special_room_comparison(
        ST,
        RSS,
        LW_RSS,
        FREQS,
        background_levels=BACKGROUND,
        background_levels_ref=bg_ref,
    )
    lpr = float(_energy_mean(RSS[:, 0] - table4))
    assert res.mean_reference_level[0] == pytest.approx(lpr, abs=1e-12)
    expected = float(_energy_mean(ST[:, 0])) + LW_RSS[0] - lpr
    assert res.sound_power_level[0] == pytest.approx(expected, abs=1e-12)
    assert bool(res.background_requirement_met[0])


def test_comparison_reference_correction_moves_formula10_by_its_table4_row() -> None:
    """ST = 75 dB, RSS = 80 dB, LWr = 90 dB and a reference margin of 5 dB:
    Table 4 takes 2 dB, so Lpr = 78 dB and LW = 75 + 90 - 78 = 87 dB.
    """
    res = emission.sound_power_special_room_comparison(
        np.full((6, 1), 75.0),
        np.full((6, 1), 80.0),
        [90.0],
        [1000.0],
        background_levels=[50.0],
        background_levels_ref=[75.0],
    )
    assert res.mean_reference_level[0] == pytest.approx(78.0, abs=1e-12)
    assert res.sound_power_level[0] == pytest.approx(87.0, abs=1e-12)


def test_table5_and_the_11_5_example() -> None:
    """11.5 EXAMPLE: sigma_R0 = 2,0 dB, sigma_omc = 2,0 dB, k = 2 -> 5,7 dB."""
    res = _direct(sigma_omc_db=2.0)
    np.testing.assert_array_equal(res.sigma_r0, SIGMA_R0_TABLE_5)
    assert res.sigma_r0_a == 2.0
    assert round(res.expanded_uncertainty_a, 1) == 5.7


@pytest.mark.parametrize(("omc", "printed"), [(0.5, 2.1), (2.0, 2.8), (4.0, 4.5)])
def test_table_d1_row_of_the_grade_2_method(omc: float, printed: float) -> None:
    res = _direct(sigma_omc_db=omc)
    assert round(res.sigma_tot_a, 1) == printed


def test_annex_e_c2_matches_part_1() -> None:
    direct = _direct(temperature_c=15.0, static_pressure_kpa=95.0)
    part1 = emission.sound_power_hard_walled(
        ST, RSS, LW_RSS, FREQS, background_levels=BACKGROUND, temperature_c=15.0,
        static_pressure_kpa=95.0,
    )  # fmt: skip
    assert direct.c2 == pytest.approx(part1.c2, abs=1e-15)
    np.testing.assert_allclose(
        direct.sound_power_level_ref, direct.sound_power_level + direct.c2
    )


# --------------------------------------------------------------------------
# Result objects and plots
# --------------------------------------------------------------------------
def test_result_refuses_an_unknown_method() -> None:
    res = _direct()
    with pytest.raises(ValueError, match="method"):
        dataclasses.replace(res, method="survey")


def test_plot_of_the_direct_method() -> None:
    background = np.tile(BACKGROUND, (6, 1))
    background[:, 1] = ST[:, 1] - 3.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", emission.SoundPowerWarning)
        res = _direct(background_levels=background, sigma_omc_db=1.0)
    ax = res.plot()
    bars = ax.patches[: FREQS.size]
    np.testing.assert_allclose([p.get_height() for p in bars], res.sound_power_level)
    # 9.8 never calls such a band an upper bound: it only fails the requirement.
    assert bars[1].get_hatch() == "xx"
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "Background requirement (9.8) not shown to be met" in labels
    assert not any(label.startswith("Upper bound") for label in labels)
    assert "ISO 3743-2" in ax.get_title()
    assert "direct method" in ax.get_title()
    plt.close("all")


def test_plot_of_the_comparison_method_in_spanish() -> None:
    res = emission.sound_power_special_room_comparison(
        ST, RSS, LW_RSS, FREQS, background_levels=BACKGROUND
    )
    ax = res.plot(language="es")
    assert "método de comparación" in ax.get_title()
    plt.close("all")


def test_reverberation_plot_rings_bands_outside_the_limits() -> None:
    r = emission.reverberation_parameter(THIRDS, 70.0)
    t = 0.7 * r
    t[3] *= 1.3
    check = emission.check_special_room_reverberation(
        t, THIRDS, volume_m3=70.0, nominal_reverberation_time_s=0.7
    )
    ax = check.plot()
    labels = [line.get_label() for line in ax.lines]
    assert "Outside the limiting curves" in labels
    assert "0.70 s" in ax.get_title()
    plt.close("all")


def test_surface_and_suitability_plots_draw() -> None:
    surfaces = emission.check_special_room_surfaces(
        np.full((5, 7), 0.15), [0.03] * 7, FREQS
    )
    ax = surfaces.plot()
    assert len([line for line in ax.lines if line.get_label().startswith("Wall")]) == 5
    assert ax.get_title().endswith(": complies")
    assert "Outside 6.4" not in [line.get_label() for line in ax.lines]
    suitability = emission.check_special_room_suitability(LW_RSS + 1.0, LW_RSS, FREQS)
    ax = suitability.plot(language="es")
    assert "idónea" in ax.get_title()
    plt.close("all")


def test_surface_plot_rings_what_fails_and_says_so() -> None:
    walls = np.full((5, 7), 0.15)
    walls[1, 0] = 0.40
    floor = np.array([0.03, 0.03, 0.03, 0.03, 0.03, 0.08, 0.08])
    check = emission.check_special_room_surfaces(walls, floor, FREQS)
    ax = check.plot(language="es")
    assert ax.get_title().endswith(": no cumple")
    (ring,) = [
        line for line in ax.lines if line.get_label() == "Fuera del apartado 6.4"
    ]
    np.testing.assert_allclose(ring.get_xdata(), [125.0, 4000.0, 8000.0])
    np.testing.assert_allclose(ring.get_ydata(), [0.40, 0.08, 0.08])
    plt.close("all")


def test_reverberation_plot_states_the_verdict() -> None:
    r = emission.reverberation_parameter(THIRDS, 70.0)
    passing = emission.check_special_room_reverberation(0.7 * r, THIRDS, volume_m3=70.0)
    assert passing.plot().get_title().endswith(": qualified")
    failing = emission.check_special_room_reverberation(0.7 * r, THIRDS, volume_m3=60.0)
    assert failing.plot().get_title().endswith(": not qualified")
    plt.close("all")


def test_source_location_plot_names_each_limit_line() -> None:
    plan = emission.special_room_source_locations(_survey(3.0, FREQS.size), FREQS)
    labels = [t.get_text() for t in plan.plot().get_legend().get_texts()]
    assert "Table 3: 2.3 dB, narrow-band components (9.5)" in labels
    assert "Table 3: 4 dB, discrete tone (9.5)" in labels
    plt.close("all")


def test_source_location_plot_adds_the_a_weighted_bar() -> None:
    plan = emission.special_room_source_locations(
        _survey(3.0, FREQS.size), FREQS, a_weighted_levels=_survey(1.0)[:, 0]
    )
    ax = plan.plot()
    assert len(ax.patches) == FREQS.size + 1
    assert ax.get_xticklabels()[-1].get_text() == "A"
    plt.close("all")


# --------------------------------------------------------------------------
# B.5 EXAMPLE: Figure B.4 centred
# --------------------------------------------------------------------------
#: Figure B.4 (PDF page 29, printed page 23): T/T1000 read off the printed
#: curve at the one-third-octave centres from 100 Hz to 10 kHz, two readings
#: made apart agreeing within 0,01.
FIGURE_B4 = np.array(
    [1.398, 1.294, 1.292, 1.335, 1.298, 1.237, 1.176, 1.002, 0.967, 0.990, 1.0,
     1.0, 1.0, 1.0, 1.031, 1.018, 1.006, 0.987, 0.954, 0.919, 0.801]
)  # fmt: skip


def test_the_b5_example_centres_the_room_within_its_curves() -> None:
    """B.5: T1000 = 0,8 s on the curve of Figure B.4. The library's centring
    qualifies the room, as the NOTE to Figure B.3 says it is centred within
    the limiting curves, at T/Tnom = 1,05 at 1 kHz and Tnom = 0,76 s.
    """
    check = emission.check_special_room_reverberation(
        0.8 * FIGURE_B4, THIRDS, volume_m3=70.0
    )
    assert check.passes
    assert 0.8 / check.nominal_reverberation_time_s == pytest.approx(1.053, abs=0.012)
    assert check.nominal_reverberation_time_s == pytest.approx(0.760, abs=0.009)


def test_the_printed_1_09_of_b5_is_the_narrow_midpoint_and_fails_250_hz() -> None:
    """The printed T/Tnom = 1,09 is the midpoint of the extreme ratios taken
    against 0,9 and 1,1 alone; with Tnom = 0,8/1,09 = 0,73 s it puts the
    250 Hz band of Figure B.4 above 1,1 R, so the room would not qualify.
    The library departs from it by 10 lg(0,760/0,73) = 0,17 dB in L_W.
    """
    t = 0.8 * FIGURE_B4
    q = t / emission.reverberation_parameter(THIRDS, 70.0)
    midpoint = 0.8 / (0.5 * float(q.max() + q.min()))
    assert midpoint == pytest.approx(1.09, abs=0.015)
    printed = emission.check_special_room_reverberation(
        t, THIRDS, volume_m3=70.0, nominal_reverberation_time_s=0.73
    )
    assert not printed.passes
    assert float(printed.normalized_ratio[4]) > 1.1
    centred = emission.check_special_room_reverberation(t, THIRDS, volume_m3=70.0)
    shift = 10.0 * math.log10(centred.nominal_reverberation_time_s / 0.73)
    assert shift == pytest.approx(0.17, abs=0.05)


# --------------------------------------------------------------------------
# Clause 5: the size of the source
# --------------------------------------------------------------------------
def test_source_of_1_percent_of_the_room_is_recommended() -> None:
    """Clause 5: at most 1 % of the room, 0,7 m3 in the smallest room."""
    r = emission.reverberation_parameter(THIRDS, 70.0)
    with warnings.catch_warnings():
        warnings.simplefilter("error", emission.SoundPowerWarning)
        check = emission.check_special_room_reverberation(
            0.7 * r, THIRDS, volume_m3=70.0, source_volume_m3=0.7
        )
    assert check.source_size_recommended is True
    assert check.source_volume_m3 == 0.7


def test_a_larger_source_warns_but_leaves_the_verdict() -> None:
    """Clause 5 says "should": a source above 1 % warns and is read, but the
    requirements of 6.2, 6.3 and 6.6 alone decide ``passes``.
    """
    r = emission.reverberation_parameter(THIRDS, 70.0)
    with pytest.warns(emission.SoundPowerWarning, match="clause 5"):
        check = emission.check_special_room_reverberation(
            0.7 * r, THIRDS, volume_m3=70.0, source_volume_m3=0.75
        )
    assert check.source_size_recommended is False
    assert check.passes


def test_no_source_volume_reads_nothing() -> None:
    r = emission.reverberation_parameter(THIRDS, 70.0)
    check = emission.check_special_room_reverberation(0.7 * r, THIRDS, volume_m3=70.0)
    assert check.source_size_recommended is None
    assert math.isnan(check.source_volume_m3)


def test_a_source_volume_must_be_positive() -> None:
    r = emission.reverberation_parameter(THIRDS, 70.0)
    with pytest.raises(ValueError, match="source_volume_m3"):
        emission.check_special_room_reverberation(
            0.7 * r, THIRDS, volume_m3=70.0, source_volume_m3=-0.1
        )


# --------------------------------------------------------------------------
# Edges of 6.4, 6.7, 9.8 and 10.3
# --------------------------------------------------------------------------
def test_a_wall_at_1_55_times_the_mean_is_not_uniform() -> None:
    """6.4: 1,5 times the mean is the last ratio allowed."""
    other = (4.0 * 0.2 - 0.31) / 3.0  # the mean of the four is 0,2
    walls = np.array([[0.31] * 7, [other] * 7, [other] * 7, [other] * 7])
    check = emission.check_special_room_surfaces(walls, [0.03] * 7, FREQS)
    np.testing.assert_allclose(check.surface_ratio[0], 1.55)
    assert not bool(np.any(check.surface_within[0]))
    assert bool(np.all(check.surface_within[1:]))
    assert not check.passes


@pytest.mark.parametrize(("band", "offset"), [(2, -3.1), (3, -3.5), (6, -4.1)])
def test_suitability_fails_a_band_read_too_low(band: int, offset: float) -> None:
    """6.7 bounds the difference both ways: a room that reads the reference
    source more than its Table 1 limit low is as unsuitable as one that reads
    it high.
    """
    measured = LW_RSS.copy()
    measured[band] += offset
    check = emission.check_special_room_suitability(measured, LW_RSS, FREQS)
    expected = np.ones(FREQS.size, dtype=bool)
    expected[band] = False
    np.testing.assert_array_equal(check.band_within, expected)
    assert not check.passes


def test_a_4_db_margin_meets_9_8_without_a_warning() -> None:
    """Table 4 starts at 4 dB: that margin is met, with its 2 dB, silently."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", emission.SoundPowerWarning)
        correction = emission.special_room_background_correction([80.0], [76.0])
        res = _direct(background_levels=ST - 4.0)
    assert float(correction[0]) == 2.0
    assert bool(np.all(res.background_requirement_met))


def test_comparison_reuses_the_background_for_the_reference() -> None:
    """One background reading serves both sources unless the reference has its
    own (7.5 of Part 1, 9.8): ST at 81 dB is 11 dB above it and takes
    nothing, the reference at 75 dB is 5 dB above it and takes the 2 dB of
    Table 4, so Lpr = 73 dB and LW = 81 + 90 - 73 = 98 dB.
    """
    res = emission.sound_power_special_room_comparison(
        np.full((6, 1), 81.0),
        np.full((6, 1), 75.0),
        [90.0],
        [1000.0],
        background_levels=[70.0],
    )
    assert res.mean_reference_level[0] == pytest.approx(73.0, abs=1e-12)
    assert res.sound_power_level[0] == pytest.approx(98.0, abs=1e-12)


# --------------------------------------------------------------------------
# What the plots draw
# --------------------------------------------------------------------------
def test_reverberation_plot_draws_t_over_tnom_within_r_scaled_limits() -> None:
    r = emission.reverberation_parameter(THIRDS, 70.0)
    t = 0.7 * r
    t[3] *= 1.3
    check = emission.check_special_room_reverberation(
        t, THIRDS, volume_m3=70.0, nominal_reverberation_time_s=0.7
    )
    ax = check.plot()
    (measured,) = [
        line for line in ax.lines if line.get_label() == r"Measured $T/T_\mathrm{nom}$"
    ]
    np.testing.assert_allclose(measured.get_ydata(), check.ratio_to_nominal)
    drawn = [np.asarray(line.get_ydata(), dtype=float) for line in ax.lines]
    for limit in (check.lower_limit * r, check.upper_limit * r):
        assert any(y.shape == limit.shape and np.allclose(y, limit) for y in drawn)
    plt.close("all")


def test_suitability_plot_draws_the_signed_difference() -> None:
    measured = LW_RSS + np.array([1.0, -2.0, 0.5, -3.5, 2.0, -1.0, 3.0])
    check = emission.check_special_room_suitability(measured, LW_RSS, FREQS)
    ax = check.plot()
    heights = [p.get_height() for p in ax.patches[: FREQS.size]]
    np.testing.assert_allclose(heights, check.difference_db)
    (marks,) = [c for c in ax.collections if c.get_label() == "Table 1 limits"]
    ys = sorted({round(float(seg[0][1]), 9) for seg in marks.get_segments()})
    assert ys == sorted({*(-check.limit_db), *check.limit_db})
    plt.close("all")


def test_surface_plot_shades_half_to_one_and_a_half_times_the_mean() -> None:
    walls = np.full((5, 7), 0.15)
    walls[:, 3] = [0.10, 0.20, 0.15, 0.12, 0.18]
    check = emission.check_special_room_surfaces(walls, [0.03] * 7, FREQS)
    ax = check.plot()
    (band,) = [
        c for c in ax.collections if c.get_label() == "0.5 to 1.5 times the mean"
    ]
    vertices = band.get_paths()[0].vertices
    for f, mean in zip(FREQS, check.mean_absorption, strict=True):
        ys = vertices[np.isclose(vertices[:, 0], f), 1]
        assert float(ys.min()) == pytest.approx(0.5 * mean)
        assert float(ys.max()) == pytest.approx(1.5 * mean)
    plt.close("all")


@pytest.mark.parametrize(("part", "first"), [("1", 2.5), ("2", 2.3)])
def test_source_location_plot_draws_each_class_line_where_its_table_does(
    part: str, first: float
) -> None:
    survey = _survey(3.0, FREQS.size)
    plan = (
        emission.hard_walled_source_locations(survey, FREQS)
        if part == "1"
        else emission.special_room_source_locations(survey, FREQS)
    )
    ax = plan.plot()
    levels = sorted(
        float(line.get_ydata()[0])
        for line in ax.lines
        if str(line.get_label()).startswith("Table")
    )
    assert levels == [first, 4.0]
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert (
        f"N over a bar: source locations (Table {'2' if part == '1' else '3'})"
        in labels
    )
    plt.close("all")


def test_source_location_plot_names_the_a_bar_on_its_axis() -> None:
    plan = emission.special_room_source_locations(
        _survey(3.0, FREQS.size), FREQS, a_weighted_levels=_survey(1.0)[:, 0]
    )
    assert plan.plot().get_xlabel() == "Frequency [Hz]; A: A-weighted level"
    assert (
        plan.plot(language="es").get_xlabel() == "Frecuencia [Hz]; A: nivel ponderado A"
    )
    plain = emission.special_room_source_locations(_survey(3.0, FREQS.size), FREQS)
    assert plain.plot().get_xlabel() == "Frequency [Hz]"
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("method", ["direct", "comparison"])
def test_spectrum_title_fits_a_default_figure(method: str, language: str) -> None:
    """The title keeps within a plain ``plt.subplots()`` figure."""
    res = (
        _direct()
        if method == "direct"
        else emission.sound_power_special_room_comparison(
            ST, RSS, LW_RSS, FREQS, background_levels=BACKGROUND
        )
    )
    ax = res.plot(language=language)
    fig = ax.figure
    fig.canvas.draw()
    box = ax.title.get_window_extent(fig.canvas.get_renderer())
    assert box.x0 >= 0.0
    assert box.x1 <= fig.bbox.width
    plt.close("all")
