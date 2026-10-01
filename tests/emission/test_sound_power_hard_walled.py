#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound power and sound energy in a hard-walled test room: ISO 3743-1:2010.

Normative anchors (BS EN ISO 3743-1:2010, read on the printed pages):
- 4.2: V >= 40 m3 and >= 40 times the reference box; largest box dimension
  <= 1,0 m for 40 m3 to 100 m3 and <= 2,0 m above 100 m3.
- 4.3: no boundary absorbs more than 0,20.
- 4.4: the largest spread between the eight orientations in each band from
  125 Hz to 8 kHz does not exceed Table 3.
- 7.4, Eq. (7), (8), Table 2: sM about the arithmetic mean; sM <= 2,5 -> 1
  location; 2,5 < sM <= 4,0 -> 2; sM > 4,0 -> 2 plus 2 in another room.
- Eq. (9)-(12): energy means over source locations and positions.
- Eq. (13) and 8.1.3: K1 = -10 lg(1 - 10^(-0,1 dLp)); dLp > 15 -> 0;
  6 <= dLp <= 15 -> Eq. (13); dLp < 6 -> 1,3 dB, an upper bound. 8.1.3
  writes dLp = L'p(ST) - Lp(B) only: K1(RSS) enters Eq. (14) with a plus
  sign, so a capped K1(RSS) lowers LW and makes no upper bound.
- Eq. (14): LW = LW(RSS) - L'p(RSS) + L'p(ST) + K1(RSS) - K1.
- Eq. (15)-(20): the sound energy level.
- Eq. (22), (23), 9.5: sigma_tot = sqrt(sigma_R0^2 + sigma_omc^2), U = k
  sigma_tot, k = 2; EXAMPLE: U = 2 sqrt(1,5^2 + 2^2) = 5 dB.
- Eq. (24): sigma'_R0 = sqrt(sigma'_tot^2 - sigma'_omc^2), with sigma_omc
  not above sigma_tot / sqrt(2).
- Table 3: 3,0 / 2,0 / 1,5 (the "400 to 5 000" row, read as the octaves
  500 Hz to 4 kHz) / 2,5 dB, and 1,5 dB A-weighted.
- Table C.1, sigma_R0 = 1,5 dB row: 1,6 / 2,5 / 4,3 dB for sigma_omc = 0,5 /
  2 / 4 dB.
- Annex A: C2 = -10 lg(ps/ps0) + 15 lg((273,15 + theta)/296).
- Table B.1: Ck = -26,2 -16,1 -8,6 -3,2 0,0 1,2 1,0 -1,1 dB.
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
#: Calibrated octave-band sound power of the reference source, dB re 1 pW.
LW_RSS = np.array([87.0, 90.5, 92.5, 93.8, 94.0, 93.0, 90.0])
#: Time-averaged levels of the source under test at three positions, dB.
ST = np.array(
    [
        [80.1, 83.4, 85.0, 84.2, 81.0, 76.5, 70.2],
        [79.0, 82.8, 84.6, 83.9, 80.4, 75.8, 69.5],
        [81.2, 84.0, 85.9, 85.0, 81.9, 77.1, 70.9],
    ]
)
#: Time-averaged levels of the reference source at the same positions, dB.
RSS = np.array(
    [
        [78.5, 81.9, 83.7, 84.9, 84.8, 83.5, 79.8],
        [77.9, 81.2, 83.1, 84.3, 84.1, 82.9, 79.2],
        [79.3, 82.6, 84.4, 85.5, 85.4, 84.1, 80.3],
    ]
)
#: Background at every position, more than 15 dB below both sources, dB.
BACKGROUND = np.array([60.0, 62.0, 63.0, 62.0, 60.0, 55.0, 50.0])
#: Table B.1, k = 2..8, typed in from the printed page.
CK_TABLE_B1 = np.array([-16.1, -8.6, -3.2, 0.0, 1.2, 1.0, -1.1])
#: Table 3, the octave bands of FREQS, typed in from the printed page.
SIGMA_R0_TABLE_3 = np.array([3.0, 2.0, 1.5, 1.5, 1.5, 1.5, 2.5])


def _energy_mean(levels: np.ndarray, axis: int) -> np.ndarray:
    """10 lg[(1/n) sum 10^(0,1 L)] along ``axis`` (Eq. 9 to 12, 15, 17, 18)."""
    return np.asarray(10.0 * np.log10(np.mean(10.0 ** (0.1 * levels), axis=axis)))


def _k1(delta: float) -> float:
    """Eq. (13) evaluated by hand."""
    return float(-10.0 * np.log10(1.0 - 10.0 ** (-0.1 * delta)))


def _power(**kwargs: object) -> emission.HardWalledSoundPowerResult:
    kwargs.setdefault("background_levels", BACKGROUND)
    return emission.sound_power_hard_walled(ST, RSS, LW_RSS, FREQS, **kwargs)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# Eq. (14) and the means of Eq. (10), (11)
# --------------------------------------------------------------------------
def test_sound_power_is_eq14_with_the_background_negligible() -> None:
    """With every margin above 15 dB, K1 = K1(RSS) = 0 and Eq. (14) is the
    calibrated power carried across by the difference of the energy means.
    """
    res = _power()
    expected = LW_RSS - _energy_mean(RSS, 0) + _energy_mean(ST, 0)
    np.testing.assert_allclose(res.sound_power_level, expected, atol=1e-12)
    np.testing.assert_allclose(res.mean_source_level, _energy_mean(ST, 0), atol=1e-12)
    np.testing.assert_allclose(
        res.mean_reference_level, _energy_mean(RSS, 0), atol=1e-12
    )
    np.testing.assert_allclose(res.mean_background_level, BACKGROUND, atol=1e-12)
    assert np.all(res.background_correction == 0.0)
    assert np.all(res.background_correction_ref == 0.0)
    assert bool(np.all(res.background_requirement_met))
    assert res.quantity == "power"
    assert np.all(np.isnan(res.sound_energy_level))
    assert res.microphone_positions == 3
    assert res.source_positions == 1


def test_background_correction_is_eq13_of_the_two_means() -> None:
    """8.1.3 corrects the *means*, once per band, for each source."""
    margin_st, margin_rss = 8.0, 11.0
    mean_st = _energy_mean(ST, 0)
    mean_rss = _energy_mean(RSS, 0)
    background = BACKGROUND.copy()
    background[3] = mean_st[3] - margin_st
    bg_ref = BACKGROUND.copy()
    bg_ref[3] = mean_rss[3] - margin_rss
    res = _power(background_levels=background, background_levels_ref=bg_ref)
    assert res.background_correction[3] == pytest.approx(_k1(margin_st), abs=1e-9)
    assert res.background_correction_ref[3] == pytest.approx(_k1(margin_rss), abs=1e-9)
    expected = LW_RSS[3] - mean_rss[3] + mean_st[3] + _k1(margin_rss) - _k1(margin_st)
    assert res.sound_power_level[3] == pytest.approx(expected, abs=1e-9)


@pytest.mark.parametrize(
    ("margin", "expected"),
    [
        # -10 lg(1 - 10^-0,6): the 6 dB edge is still Eq. (13)
        (6.0, 1.2563),
        (10.0, 0.4576),
        # -10 lg(1 - 10^-1,5): the 15 dB edge is still Eq. (13)
        (15.0, 0.1396),
        # above 15 dB: nothing to correct
        (15.01, 0.0),
        # below 6 dB: 1,3 dB, "the value for dLp = 6 dB" to one decimal
        (5.99, 1.3),
        (2.0, 1.3),
    ],
)
def test_background_rules_of_8_1_3(margin: float, expected: float) -> None:
    background = _energy_mean(ST, 0) - margin
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", emission.SoundPowerWarning)
        res = _power(background_levels=background, background_levels_ref=BACKGROUND)
    np.testing.assert_allclose(res.background_correction, expected, atol=5e-5)
    assert bool(np.all(res.background_requirement_met)) is (margin >= 6.0)


def test_margin_of_the_source_below_6_db_is_an_upper_bound() -> None:
    """8.1.3: the source under test's margin below 6 dB fixes K1 at 1,3 dB,
    less than Eq. (13) would take, so the band reads high: an upper bound.
    """
    background = BACKGROUND.copy()
    background[0] = _energy_mean(ST, 0)[0] - 3.0
    with pytest.warns(emission.SoundPowerWarning, match="source under test.*upper"):
        res = _power(background_levels=background, background_levels_ref=BACKGROUND)
    assert not bool(res.background_requirement_met[0])
    assert bool(np.all(res.background_requirement_met[1:]))
    assert res.upper_bound.tolist() == [True] + [False] * 6
    uncapped = res.sound_power_level[0] + 1.3 - _k1(3.0)
    assert res.sound_power_level[0] > uncapped


def test_reference_source_margin_fails_4_5_but_is_no_upper_bound() -> None:
    """The reference source enters Eq. (14) with its own K1(RSS), so its
    margin is held to 4.5 as well; but a capped K1(RSS) enters with a plus
    sign and lowers LW, so the band is not the upper bound of 8.1.3.
    """
    bg_ref = BACKGROUND.copy()
    bg_ref[6] = _energy_mean(RSS, 0)[6] - 4.0
    with pytest.warns(emission.SoundPowerWarning, match="not upper bounds"):
        res = _power(background_levels_ref=bg_ref)
    assert res.background_correction_ref[6] == pytest.approx(1.3)
    assert not bool(res.background_requirement_met[6])
    assert not bool(np.any(res.upper_bound))
    expected = LW_RSS[6] - _energy_mean(RSS, 0)[6] + _energy_mean(ST, 0)[6] + 1.3
    assert res.sound_power_level[6] == pytest.approx(expected, abs=1e-9)
    assert res.sound_power_level[6] < expected - 1.3 + _k1(4.0)


def test_both_margins_short_is_no_upper_bound() -> None:
    background = BACKGROUND.copy()
    background[0] = min(_energy_mean(ST, 0)[0], _energy_mean(RSS, 0)[0]) - 3.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", emission.SoundPowerWarning)
        res = _power(background_levels=background)
    assert not bool(res.background_requirement_met[0])
    assert not bool(res.upper_bound[0])


def test_no_background_warns_and_meets_nothing() -> None:
    with pytest.warns(emission.SoundPowerWarning, match="No background levels"):
        res = emission.sound_power_hard_walled(ST, RSS, LW_RSS, FREQS)
    assert not bool(np.any(res.background_requirement_met))
    assert not bool(np.any(res.upper_bound))
    assert np.all(np.isnan(res.mean_background_level))
    np.testing.assert_allclose(
        res.sound_power_level, LW_RSS - _energy_mean(RSS, 0) + _energy_mean(ST, 0)
    )


def test_source_locations_are_energy_averaged_first_eq9() -> None:
    """Eq. (9) averages each position over the NS locations, Eq. (10) the
    positions; two locations 2 dB apart give their energy mean.
    """
    locations = np.stack([ST, ST + 2.0])
    res = emission.sound_power_hard_walled(
        locations, RSS, LW_RSS, FREQS, background_levels=BACKGROUND
    )
    per_position = _energy_mean(locations, 0)
    expected = LW_RSS - _energy_mean(RSS, 0) + _energy_mean(per_position, 0)
    np.testing.assert_allclose(res.sound_power_level, expected, atol=1e-12)
    assert res.source_positions == 2


def test_a_traverse_is_a_1d_spectrum_and_needs_a_traverse_reference() -> None:
    """NOTE to 8.1.2: a traverse gives the means directly."""
    res = emission.sound_power_hard_walled(
        _energy_mean(ST, 0), _energy_mean(RSS, 0), LW_RSS, FREQS,
        background_levels=BACKGROUND,
    )  # fmt: skip
    np.testing.assert_allclose(res.sound_power_level, _power().sound_power_level)
    assert res.microphone_positions == 1


def test_fixed_reference_levels_are_refused_for_a_traverse() -> None:
    mean_st = _energy_mean(ST, 0)
    with pytest.raises(ValueError, match="levels_ref"):
        emission.sound_power_hard_walled(mean_st, RSS, LW_RSS, FREQS)


def test_fewer_than_three_positions_warn() -> None:
    with pytest.warns(emission.SoundPowerWarning, match=r"7\.3"):
        emission.sound_power_hard_walled(
            ST[:2], RSS[:2], LW_RSS, FREQS, background_levels=BACKGROUND
        )


# --------------------------------------------------------------------------
# Annex A, Annex B, clause 9
# --------------------------------------------------------------------------
def test_annex_a_c2_at_the_reference_conditions_is_theta1_residue() -> None:
    """theta_1 = 296 K beside a 23,0 degC reference leaves C2 = 15 lg(296,15/296)."""
    res = _power()
    assert res.c2 == pytest.approx(15.0 * math.log10(296.15 / 296.0), abs=1e-12)
    np.testing.assert_allclose(
        res.sound_power_level_ref, res.sound_power_level + res.c2
    )
    assert res.sound_power_level_a_ref == pytest.approx(
        res.sound_power_level_a + res.c2
    )


def test_annex_a_c2_at_500_m_is_0_26_db() -> None:
    """Eq. (A.2) at 500 m and 23 degC: ps = 95,46 kPa, C2 = 0,26 dB, not the
    0,4 dB C.4.2.5 quotes (see docs/ERRATA.md).
    """
    ps = emission.static_pressure_from_altitude(500.0)
    res = _power(static_pressure_kpa=ps)
    assert ps == pytest.approx(95.46, abs=0.005)
    assert res.c2 == pytest.approx(0.262, abs=5e-4)


def test_annex_b_a_weighted_total_uses_table_b1() -> None:
    res = _power()
    expected = 10.0 * np.log10(
        np.sum(10.0 ** (0.1 * (res.sound_power_level + CK_TABLE_B1)))
    )
    assert res.sound_power_level_a == pytest.approx(expected, abs=1e-12)


def test_63_hz_is_accepted_under_the_table_b1_footnote() -> None:
    freqs = np.array([63.0, 125.0])
    res = emission.sound_power_hard_walled(
        ST[:, :2], RSS[:, :2], LW_RSS[:2], freqs, background_levels=BACKGROUND[:2]
    )
    assert math.isnan(float(res.sigma_r0[0]))
    assert res.sigma_r0[1] == 3.0


def test_frequencies_above_8_khz_are_refused() -> None:
    freqs = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 16000.0])
    with pytest.raises(ValueError, match="frequencies"):
        emission.sound_power_hard_walled(ST, RSS, LW_RSS, freqs)


def test_table3_sigma_r0_per_band_and_a_weighted() -> None:
    res = _power()
    np.testing.assert_array_equal(res.sigma_r0, SIGMA_R0_TABLE_3)
    assert res.sigma_r0_a == 1.5


def test_9_5_example_expanded_uncertainty_is_5_db() -> None:
    """9.5 EXAMPLE: sigma_omc = 2,0 dB, k = 2, sigma_R0 = 1,5 dB -> U = 5 dB."""
    res = _power(sigma_omc_db=2.0)
    assert res.expanded_uncertainty_a == pytest.approx(5.0, abs=1e-12)
    np.testing.assert_allclose(
        res.expanded_uncertainty, 2.0 * np.hypot(SIGMA_R0_TABLE_3, 2.0)
    )


@pytest.mark.parametrize(("omc", "printed"), [(0.5, 1.6), (2.0, 2.5), (4.0, 4.3)])
def test_table_c1_row_of_the_grade_2_method(omc: float, printed: float) -> None:
    """Table C.1, sigma_R0 = 1,5 dB: the printed totals to one decimal."""
    res = _power(sigma_omc_db=omc)
    assert round(res.sigma_tot_a, 1) == printed


def test_uncertainty_is_nan_without_sigma_omc() -> None:
    res = _power()
    assert math.isnan(res.sigma_tot_a)
    assert np.all(np.isnan(res.expanded_uncertainty))


def test_negative_sigma_omc_is_refused() -> None:
    with pytest.raises(ValueError, match="sigma_omc_db"):
        _power(sigma_omc_db=-1.0)


def test_coverage_factor_must_be_positive() -> None:
    with pytest.raises(ValueError, match="coverage_factor"):
        _power(coverage_factor=0.0)


# --------------------------------------------------------------------------
# Sound energy, Eq. (15)-(20)
# --------------------------------------------------------------------------
def test_steady_source_energy_is_power_plus_10_lg_t() -> None:
    """3.4 NOTE 1: a source steady over T gives L'E = L'p + 10 lg(T/T0), and
    with the background compared as its exposure over the same T,
    LJ = LW + 10 lg(T/T0) band for band, corrections included.
    """
    t = 10.0
    background = BACKGROUND.copy()
    background[2] = _energy_mean(ST, 0)[2] - 8.0
    power = _power(background_levels=background)
    events = np.stack([ST + 10.0 * math.log10(t)] * 5)
    energy = emission.sound_energy_hard_walled(
        events, RSS, LW_RSS, FREQS, background_levels=background, integration_time_s=t
    )
    np.testing.assert_allclose(
        energy.sound_energy_level, power.sound_power_level + 10.0, atol=1e-9
    )
    assert energy.background_correction[2] == pytest.approx(_k1(8.0), abs=1e-9)
    assert energy.quantity == "energy"
    assert np.all(np.isnan(energy.sound_power_level))
    assert energy.sound_energy_level_a == pytest.approx(
        power.sound_power_level_a + 10.0
    )


def test_events_one_at_a_time_and_one_encompassing_measurement_agree() -> None:
    """Eq. (15) over Ne equal events and Eq. (16) over their sum agree."""
    n_events = 7
    one_at_a_time = emission.sound_energy_hard_walled(
        np.stack([ST] * n_events), RSS, LW_RSS, FREQS, background_levels=BACKGROUND,
        integration_time_s=1.0,
    )  # fmt: skip
    encompassing = emission.sound_energy_hard_walled(
        ST + 10.0 * math.log10(n_events), RSS, LW_RSS, FREQS, events=n_events,
        background_levels=BACKGROUND, integration_time_s=1.0,
    )  # fmt: skip
    np.testing.assert_allclose(
        encompassing.sound_energy_level, one_at_a_time.sound_energy_level, atol=1e-9
    )


def test_energy_source_locations_follow_eq17() -> None:
    events = np.stack([np.stack([ST, ST + 3.0])] * 5)  # (Ne, NS, NM, NB)
    res = emission.sound_energy_hard_walled(
        events, RSS, LW_RSS, FREQS, background_levels=BACKGROUND, integration_time_s=1.0
    )
    per_position = _energy_mean(np.stack([ST, ST + 3.0]), 0)
    expected = LW_RSS - _energy_mean(RSS, 0) + _energy_mean(per_position, 0)
    np.testing.assert_allclose(res.sound_energy_level, expected, atol=1e-9)
    assert res.source_positions == 2


def test_fewer_than_five_events_warn_citing_7_6() -> None:
    with pytest.warns(emission.SoundPowerWarning, match=r"ISO 3743-1:2010 7\.6"):
        emission.sound_energy_hard_walled(
            np.stack([ST] * 3), RSS, LW_RSS, FREQS, background_levels=BACKGROUND,
            integration_time_s=1.0,
        )  # fmt: skip


def test_energy_background_needs_the_integration_time() -> None:
    events = np.stack([ST] * 5)
    with pytest.raises(ValueError, match="integration_time_s"):
        emission.sound_energy_hard_walled(
            events, RSS, LW_RSS, FREQS, background_levels=BACKGROUND
        )


def test_energy_rank_neither_form_admits_is_refused() -> None:
    events = np.zeros((2, 2, 2, 3, 7))
    with pytest.raises(ValueError, match="event_levels"):
        emission.sound_energy_hard_walled(events, RSS, LW_RSS, FREQS)


# --------------------------------------------------------------------------
# Eq. (24)
# --------------------------------------------------------------------------
def test_round_robin_reproducibility_is_the_quadrature_difference() -> None:
    assert emission.reproducibility_from_round_robin(2.5, 1.5) == pytest.approx(2.0)


def test_round_robin_warns_beyond_sigma_tot_over_root_2() -> None:
    with pytest.warns(emission.SoundPowerWarning, match="low accuracy"):
        value = emission.reproducibility_from_round_robin(2.5, 2.0)
    assert value == pytest.approx(1.5)


def test_round_robin_refuses_an_operating_deviation_above_the_total() -> None:
    with pytest.raises(ValueError, match="operating_db"):
        emission.reproducibility_from_round_robin(1.0, 1.5)


# --------------------------------------------------------------------------
# 4.2 to 4.4
# --------------------------------------------------------------------------
def _orientations(spread: np.ndarray) -> np.ndarray:
    """Eight orientation means whose range per band is ``spread``."""
    base = np.array([80.0, 83.0, 85.0, 84.0, 81.0, 76.0, 70.0])
    return base + np.linspace(0.0, 1.0, 8)[:, None] * spread[None, :]


def test_room_qualifies_on_spreads_at_the_table3_limits() -> None:
    check = emission.check_hard_walled_room(
        _orientations(SIGMA_R0_TABLE_3), FREQS, volume_m3=60.0,
        reference_box_m=[0.8, 0.5, 0.6], absorption_coefficients=[0.05, 0.2],
    )  # fmt: skip
    np.testing.assert_allclose(check.level_range_db, SIGMA_R0_TABLE_3, atol=1e-12)
    assert check.passes
    assert check.surfaces_hard is True


def test_spread_over_the_limit_in_one_band_fails_4_4() -> None:
    spread = SIGMA_R0_TABLE_3.copy()
    spread[3] = 1.6
    check = emission.check_hard_walled_room(
        _orientations(spread), FREQS, volume_m3=60.0, reference_box_m=[0.8, 0.5, 0.6]
    )
    assert not check.acoustically_adequate
    assert not bool(check.band_adequate[3])
    assert not check.passes


@pytest.mark.parametrize(
    ("volume", "box", "volume_ok", "box_ok"),
    [
        (40.0, [1.0, 1.0, 1.0], True, True),  # 40 m3 and 40 boxes of 1 m3
        (39.9, [0.5, 0.5, 0.5], False, True),  # below 40 m3
        (45.0, [1.2, 1.0, 1.0], False, False),  # 48 m3 needed; 1,2 m > 1,0 m
        (100.0, [1.1, 0.5, 0.5], True, False),  # 100 m3 still takes 1,0 m
        (100.1, [1.1, 0.5, 0.5], True, True),  # above 100 m3: 2,0 m
        (150.0, [2.1, 0.5, 0.5], True, False),
        # Exactly 40 boxes of 2,56 m3 as read; 40 times the box is
        # 102,400 000 000 000 02 m3 in binary, and "at least" is inclusive.
        (102.4, [0.8, 1.6, 2.0], True, True),
    ],
)
def test_volume_and_reference_box_of_4_2(
    volume: float, box: list[float], *, volume_ok: bool, box_ok: bool
) -> None:
    check = emission.check_hard_walled_room(
        _orientations(np.full(7, 1.0)), FREQS, volume_m3=volume, reference_box_m=box
    )
    assert check.volume_adequate is volume_ok
    assert check.box_fits is box_ok
    assert check.surfaces_hard is None


def test_a_surface_above_0_20_fails_4_3() -> None:
    check = emission.check_hard_walled_room(
        _orientations(np.full(7, 1.0)), FREQS, volume_m3=60.0,
        reference_box_m=[0.5, 0.5, 0.5], absorption_coefficients=[[0.1, 0.21]],
    )  # fmt: skip
    assert check.surfaces_hard is False
    assert not check.passes


def test_minimum_microphone_distance_of_7_3() -> None:
    check = emission.check_hard_walled_room(
        _orientations(np.full(7, 1.0)),
        FREQS,
        volume_m3=64.0,
        reference_box_m=[0.5, 0.5, 0.5],
    )
    assert check.minimum_microphone_distance_m == pytest.approx(0.3 * 4.0)


def test_room_check_has_no_truth_value() -> None:
    check = emission.check_hard_walled_room(
        _orientations(np.full(7, 1.0)),
        FREQS,
        volume_m3=60.0,
        reference_box_m=[0.5, 0.5, 0.5],
    )
    with pytest.raises(TypeError, match="passes"):
        bool(check)


def test_room_check_refuses_63_hz() -> None:
    freqs = np.array([63.0, 125.0])
    orientations = _orientations(np.full(7, 1.0))[:, :2]
    with pytest.raises(ValueError, match="125 Hz to 8 kHz"):
        emission.check_hard_walled_room(
            orientations, freqs, volume_m3=60.0, reference_box_m=[0.5, 0.5, 0.5]
        )


def test_other_than_eight_orientations_warn() -> None:
    orientations = _orientations(np.full(7, 1.0))[:4]
    with pytest.warns(emission.SoundPowerWarning, match="eight|8"):
        emission.check_hard_walled_room(
            orientations, FREQS, volume_m3=60.0, reference_box_m=[0.5, 0.5, 0.5]
        )


# --------------------------------------------------------------------------
# 7.4, Table 2
# --------------------------------------------------------------------------
def _survey(s_m: float) -> np.ndarray:
    """Six positions whose sample standard deviation is ``s_m`` in every band."""
    pattern = np.array([-1.0, 1.0, -1.0, 1.0, 0.0, 0.0])
    scale = s_m / float(np.std(pattern, ddof=1))
    return 80.0 + scale * pattern[:, None] * np.ones((1, FREQS.size))


#: Six deviations whose sums of squares over n - 1 = 5 are exactly 6,25 and
#: 16, so that Eq. (7) lands on the 2,5 dB and 4,0 dB edges of Table 2 without
#: a rounding error deciding the row.
_EXACT_2_5 = np.array([3.75, -3.75, 1.25, -1.25, 0.0, 0.0])
_EXACT_4_0 = np.array([6.0, -6.0, 2.0, -2.0, 0.0, 0.0])


@pytest.mark.parametrize(
    ("deviations", "s_m", "locations", "other_room"),
    [
        (_EXACT_2_5, 2.5, 1, 0),  # sM <= 2,5 -> one location
        (_EXACT_4_0, 4.0, 2, 0),  # 2,5 < sM <= 4,0 -> two in the same room
    ],
)
def test_table2_edges_are_inclusive(
    deviations: np.ndarray, s_m: float, locations: int, other_room: int
) -> None:
    survey = 80.0 + deviations[:, None] * np.ones((1, FREQS.size))
    plan = emission.hard_walled_source_locations(survey, FREQS)
    np.testing.assert_allclose(plan.standard_deviation_db, s_m, rtol=0, atol=0)
    assert np.all(plan.source_locations == locations)
    assert np.all(plan.additional_room_locations == other_room)


@pytest.mark.parametrize(
    ("s_m", "locations", "other_room"),
    [(2.49, 1, 0), (2.51, 2, 0), (3.99, 2, 0), (4.01, 2, 2)],
)
def test_table2_rows(s_m: float, locations: int, other_room: int) -> None:
    plan = emission.hard_walled_source_locations(_survey(s_m), FREQS)
    np.testing.assert_allclose(plan.standard_deviation_db, s_m, atol=1e-12)
    assert np.all(plan.source_locations == locations)
    assert np.all(plan.additional_room_locations == other_room)
    assert plan.other_room_required is (other_room > 0)
    assert plan.required_source_locations == locations
    assert plan.spectral_character is None
    assert plan.standard == "ISO 3743-1:2010"


def test_survey_of_fewer_than_six_positions_warns() -> None:
    survey = _survey(1.0)[:4]
    with pytest.warns(emission.SoundPowerWarning, match=r"7\.4"):
        emission.hard_walled_source_locations(survey, FREQS)


# --------------------------------------------------------------------------
# The result object
# --------------------------------------------------------------------------
def test_result_refuses_mismatched_bands() -> None:
    res = _power()
    with pytest.raises(ValueError, match="sigma_r0"):
        dataclasses.replace(res, sigma_r0=np.array([1.0]))


def test_result_refuses_an_unknown_quantity() -> None:
    res = _power()
    with pytest.raises(ValueError, match="quantity"):
        dataclasses.replace(res, quantity="intensity")


def test_plot_draws_one_bar_per_band_hatches_and_error_bars() -> None:
    background = BACKGROUND.copy()
    background[0] = _energy_mean(ST, 0)[0] - 3.0
    bg_ref = BACKGROUND.copy()
    bg_ref[6] = _energy_mean(RSS, 0)[6] - 4.0
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", emission.SoundPowerWarning)
        res = _power(
            background_levels=background,
            background_levels_ref=bg_ref,
            sigma_omc_db=2.0,
        )
    ax = res.plot()
    bars = ax.patches[: FREQS.size]
    np.testing.assert_allclose([p.get_height() for p in bars], res.sound_power_level)
    assert bars[0].get_hatch() == "//"
    assert bars[1].get_hatch() is None
    assert bars[6].get_hatch() == "xx"
    assert "ISO 3743-1" in ax.get_title()
    assert f"{res.sound_power_level_a:.1f}" in ax.get_title()
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert "Upper bound: source margin below 6 dB" in labels
    assert "Background requirement (4.5) not shown to be met" in labels
    plt.close("all")


def test_plot_without_a_background_claims_no_upper_bound() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", emission.SoundPowerWarning)
        res = emission.sound_power_hard_walled(ST, RSS, LW_RSS, FREQS)
    ax = res.plot()
    assert {p.get_hatch() for p in ax.patches[: FREQS.size]} == {"xx"}
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels == ["Background requirement (4.5) not shown to be met"]
    plt.close("all")


def test_plot_of_an_energy_result_in_spanish() -> None:
    res = emission.sound_energy_hard_walled(
        np.stack([ST] * 5), RSS, LW_RSS, FREQS, background_levels=BACKGROUND,
        integration_time_s=1.0,
    )  # fmt: skip
    ax = res.plot(language="es")
    assert "energía" in ax.get_ylabel()
    assert "ISO 3743-1" in ax.get_title()
    plt.close("all")


def test_room_check_plot_marks_the_failing_band_and_the_limits() -> None:
    spread = SIGMA_R0_TABLE_3.copy()
    spread[3] = 2.0
    check = emission.check_hard_walled_room(
        _orientations(spread), FREQS, volume_m3=60.0, reference_box_m=[0.5, 0.5, 0.5]
    )
    ax = check.plot()
    heights = [p.get_height() for p in ax.patches[: FREQS.size]]
    np.testing.assert_allclose(heights, spread, atol=1e-12)
    assert "not qualified" in ax.get_title()
    plt.close("all")


def test_source_location_plot_annotates_the_counts() -> None:
    plan = emission.hard_walled_source_locations(_survey(4.5), FREQS)
    ax = plan.plot()
    texts = [t.get_text() for t in ax.texts]
    assert texts == ["2+2"] * FREQS.size
    plt.close("all")


def test_round_robin_stays_quiet_up_to_sigma_tot_over_root_2() -> None:
    """9.3.2: sigma_omc up to sigma_tot/sqrt(2) is expected; 2,5/sqrt(2) is
    1,77 dB, so 1,6 dB passes silently and 1,8 dB warns.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error", emission.SoundPowerWarning)
        quiet = emission.reproducibility_from_round_robin(2.5, 1.6)
    assert quiet == pytest.approx(math.sqrt(2.5**2 - 1.6**2))
    with pytest.warns(emission.SoundPowerWarning, match="low accuracy"):
        emission.reproducibility_from_round_robin(2.5, 1.8)


def test_room_check_plot_draws_the_table3_marks_at_their_limits() -> None:
    check = emission.check_hard_walled_room(
        _orientations(SIGMA_R0_TABLE_3),
        FREQS,
        volume_m3=60.0,
        reference_box_m=[0.5, 0.5, 0.5],
    )
    ax = check.plot()
    (marks,) = [
        c for c in ax.collections if c.get_label() == r"Table 3 limit $\sigma_{R0}$"
    ]
    np.testing.assert_allclose(
        [seg[0][1] for seg in marks.get_segments()], check.limit_db
    )
    plt.close("all")


def test_room_check_legend_keys_each_colour_by_a_bar_of_it() -> None:
    """A failing first band must not lend its colour to the passing bars'
    legend entry: each entry takes the colour of a bar it names.
    """
    spread = SIGMA_R0_TABLE_3.copy()
    spread[0] = 4.9  # 125 Hz over its 3,0 dB
    check = emission.check_hard_walled_room(
        _orientations(spread), FREQS, volume_m3=60.0, reference_box_m=[0.5, 0.5, 0.5]
    )
    ax = check.plot()
    bars = ax.patches[: FREQS.size]
    legend = ax.get_legend()
    entries = dict(
        zip(
            [t.get_text() for t in legend.get_texts()],
            legend.legend_handles,
            strict=True,
        )
    )
    passing = entries["Largest spread between orientations"].get_facecolor()
    failing = entries["Spread above the limit"].get_facecolor()
    assert passing == bars[1].get_facecolor()
    assert failing == bars[0].get_facecolor()
    assert passing != failing
    plt.close("all")


def test_error_bars_are_the_expanded_uncertainty() -> None:
    res = _power(sigma_omc_db=1.0)
    ax = res.plot()
    (container,) = [c for c in ax.containers if hasattr(c, "has_yerr") and c.has_yerr]
    segments = container.lines[2][0].get_segments()
    half = [0.5 * abs(seg[1][1] - seg[0][1]) for seg in segments]
    np.testing.assert_allclose(half, res.expanded_uncertainty)
    assert not np.allclose(half, res.sigma_tot)
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
def test_spectrum_title_fits_a_default_figure(language: str) -> None:
    ax = _power(sigma_omc_db=1.0).plot(language=language)
    fig = ax.figure
    fig.canvas.draw()
    box = ax.title.get_window_extent(fig.canvas.get_renderer())
    assert box.x0 >= 0.0
    assert box.x1 <= fig.bbox.width
    plt.close("all")
