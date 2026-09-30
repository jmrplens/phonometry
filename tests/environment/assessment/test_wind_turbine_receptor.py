#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Wind turbine sound at a receptor (IEC TS 61400-11-2:2024).

The printed tables are the oracle wherever the TS prints one: Tables K.1 and
K.2 cell by cell, Table 7 row by row (its fourth row is misprinted), Tables
C.2 to C.5, Table A.1 and the points of Figure A.1. The equations of 10.3,
Equation (C.1) and Equation (J.1) are checked against their closed forms on
numbers worked by hand here.
"""

from __future__ import annotations

import math
import warnings
from typing import TYPE_CHECKING

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from reference_data import wind_turbine_receptor as ref

from phonometry import environment as env
from phonometry.environment.assessment import wind_turbine_receptor as wtr
from phonometry.environment.propagation.air_absorption import air_attenuation
from phonometry.filters import weighting_compliance

if TYPE_CHECKING:
    from collections.abc import Callable


# ---------------------------------------------------------------------------
# Annex K: wind shear
# ---------------------------------------------------------------------------
def test_table_k1_every_cell() -> None:
    for alpha, row in zip(ref.WT_K1_EXPONENTS, ref.WT_K1_SPEEDS_10M, strict=True):
        speeds = env.power_law_wind_speed(
            np.asarray(ref.WT_K1_SPEEDS_120M),
            height_m=10.0,
            reference_height_m=120.0,
            shear_exponent=alpha,
        )
        np.testing.assert_array_equal(np.round(speeds, 1), row)


def test_table_k2_every_cell_and_every_blank() -> None:
    low, high = env.TYPICAL_WIND_SHEAR_EXPONENT_RANGE
    for v10 in range(1, 16):
        for v120 in range(3, 16):
            alpha = env.wind_shear_exponent(
                float(v120), float(v10), height_m=120.0, reference_height_m=10.0
            )
            printed = ref.WT_K2_SHEAR_EXPONENTS.get((v10, v120))
            if printed is None:
                assert not low <= alpha <= high, (v10, v120, alpha)
            else:
                assert round(alpha, 2) == pytest.approx(printed), (v10, v120)


def test_table_k3_roughness_lengths() -> None:
    assert dict(env.ROUGHNESS_LENGTHS_M) == ref.WT_K3_ROUGHNESS_LENGTHS_M


def test_logarithmic_profile_inverts_iec_61400_11_equation_29() -> None:
    """V_H = V_10 ln(H/z0ref)/ln(10/z0ref), so V_10 back from V_H is the same."""
    hub = 120.0
    v10 = 6.0
    v_hub = v10 * math.log(hub / 0.05) / math.log(10.0 / 0.05)
    back = env.logarithmic_wind_speed(v_hub, height_m=10.0, reference_height_m=hub)
    assert back == pytest.approx(v10, rel=1e-12)


def test_wind_shear_profile_through_two_heights() -> None:
    profile = env.wind_shear_profile(5.0, 9.0, upper_height_m=120.0)
    assert profile.shear_exponent == pytest.approx(math.log(9.0 / 5.0) / math.log(12.0))
    assert profile.typical
    assert profile.speed_at(120.0) == pytest.approx(9.0)
    assert profile.speed_at(10.0) == pytest.approx(5.0)


def test_a_strongly_unstable_profile_is_not_typical() -> None:
    profile = env.wind_shear_profile(6.0, 4.0, upper_height_m=120.0)
    assert not profile.typical


def test_the_upper_height_must_be_above_the_lower() -> None:
    with pytest.raises(ValueError, match=r"'upper_height_m' must be above"):
        env.wind_shear_profile(5.0, 9.0, lower_height_m=100.0, upper_height_m=10.0)


def test_equal_heights_give_no_exponent() -> None:
    with pytest.raises(ValueError, match=r"must differ"):
        env.wind_shear_exponent(5.0, 4.0, height_m=10.0, reference_height_m=10.0)


# ---------------------------------------------------------------------------
# 10.1 and 10.3: bins, averages and uncertainty
# ---------------------------------------------------------------------------
_LEVELS = np.array([40.0, 42.0, 41.0, 45.0, 44.0, 38.0])
_SPEEDS = np.array([4.5, 5.49, 5.2, 6.6, 6.5, 0.4])


def test_bins_are_one_metre_per_second_and_integer_centred() -> None:
    binned = env.bin_sound_levels(_LEVELS, _SPEEDS)
    np.testing.assert_array_equal(binned.wind_speeds_m_s, [0.0, 5.0, 7.0])
    np.testing.assert_array_equal(binned.counts, [1, 3, 2])


def test_equations_1_2_4_and_5() -> None:
    binned = env.bin_sound_levels(
        _LEVELS, _SPEEDS, type_b_uncertainty_db=[0.3, 0.4, 0.5, 0.2, 0.2, 0.1]
    )
    members = _LEVELS[0:3]
    mean = 10.0 * math.log10(np.mean(10.0 ** (members / 10.0)))
    s = math.sqrt(np.sum((members - mean) ** 2) / (3 * 2))
    u = math.sqrt(np.mean(np.array([0.3, 0.4, 0.5]) ** 2))
    assert binned.mean_levels_db[1] == pytest.approx(mean)
    assert binned.type_a_uncertainty_db[1] == pytest.approx(s)
    assert binned.type_b_uncertainty_db[1] == pytest.approx(u)
    assert binned.combined_uncertainty_db[1] == pytest.approx(math.hypot(s, u))
    assert math.isnan(binned.type_a_uncertainty_db[0])


def test_equations_8_and_9_for_statistical_levels() -> None:
    binned = env.bin_sound_levels(_LEVELS, _SPEEDS, averaging="arithmetic")
    members = _LEVELS[0:3]
    assert binned.mean_levels_db[1] == pytest.approx(np.mean(members))
    assert binned.type_a_uncertainty_db[1] == pytest.approx(
        np.std(members, ddof=1) / math.sqrt(3)
    )


def test_north_sector_spans_345_to_15_degrees() -> None:
    binned = env.bin_sound_levels(
        [40.0, 41.0, 42.0, 43.0], [5.0, 5.0, 5.0, 5.0], [345.0, 14.9, 15.0, 359.0]
    )
    np.testing.assert_array_equal(binned.wind_directions_deg, [0.0, 30.0])
    np.testing.assert_array_equal(binned.counts, [3, 1])


def test_a_sector_width_that_does_not_divide_a_turn_is_refused() -> None:
    directions = np.zeros(6)
    with pytest.raises(ValueError, match=r"must divide 360"):
        env.bin_sound_levels(_LEVELS, _SPEEDS, directions, sector_width_deg=25.0)


def test_an_unknown_averaging_is_refused() -> None:
    with pytest.raises(ValueError, match=r"'averaging' must be one of"):
        env.bin_sound_levels(_LEVELS, _SPEEDS, averaging="median")


def test_equations_6_and_7() -> None:
    result = env.turbine_sound_levels(
        [45.0], [40.0], total_uncertainty_db=[0.8], background_uncertainty_db=[0.6]
    )
    e_t, e_b = 10.0**4.5, 10.0**4.0
    assert result.turbine_levels_db[0] == pytest.approx(10.0 * math.log10(e_t - e_b))
    assert result.turbine_uncertainty_db[0] == pytest.approx(
        math.hypot(0.8 * e_t, 0.6 * e_b) / (e_t - e_b)
    )
    assert result.regimes == (env.BackgroundCorrectionRegime.LOGARITHMIC,)


def test_within_3_db_the_suggested_correction_is_3_db() -> None:
    result = env.turbine_sound_levels(
        [42.0, 40.0],
        [40.0, 41.0],
        total_uncertainty_db=0.5,
        background_uncertainty_db=0.4,
    )
    assert result.turbine_levels_db[0] == pytest.approx(39.0)
    # A fixed 3 dB offset carries the total's uncertainty, not the background's.
    assert result.turbine_uncertainty_db[0] == pytest.approx(0.5)
    assert result.regimes[0] is env.BackgroundCorrectionRegime.THREE_DB
    assert result.regimes[1] is env.BackgroundCorrectionRegime.UNDETERMINED
    assert math.isnan(result.turbine_levels_db[1])


def test_exactly_3_db_is_subtracted_logarithmically() -> None:
    result = env.turbine_sound_levels([43.0], [40.0])
    assert result.regimes[0] is env.BackgroundCorrectionRegime.LOGARITHMIC


def test_3_db_in_decimal_is_3_db_whatever_the_binary_says() -> None:
    """33.3 dB less 30.3 dB is 2.9999999999999964 dB in binary: "at least 3 dB"."""
    result = env.turbine_sound_levels([33.3], [30.3])
    assert result.level_differences_db[0] < 3.0
    assert result.regimes[0] is env.BackgroundCorrectionRegime.LOGARITHMIC


def test_bin_means_3_db_apart_are_subtracted_logarithmically() -> None:
    """Every interval 3 dB over its background; the energy means end 7e-15 dB short."""
    total = env.bin_sound_levels([41.0, 43.7], [5.0, 5.2])
    background = env.bin_sound_levels([38.0, 40.7], [5.1, 4.9])
    corrected = total.background_corrected(background)
    assert corrected.level_differences_db[0] < 3.0
    assert corrected.regimes[0] is env.BackgroundCorrectionRegime.LOGARITHMIC


def test_a_background_as_loud_as_the_total_takes_the_3_db_correction() -> None:
    """The same three levels in another order: equal means.

    Their difference is zero, or a few units in the last place below it,
    depending on how the platform sums the three energies (one machine gives
    -7e-15 dB, another exactly 0). 11.7 suggests the 3 dB correction from 0 dB
    up; only a background louder than the total leaves the bin undetermined
    (11.6.4).
    """
    total = env.bin_sound_levels([38.0, 38.6, 39.6], [5.0, 5.2, 4.8])
    background = env.bin_sound_levels([38.0, 39.6, 38.6], [5.0, 5.2, 4.8])
    corrected = total.background_corrected(background)
    assert abs(corrected.level_differences_db[0]) < 1e-12
    assert corrected.regimes[0] is env.BackgroundCorrectionRegime.THREE_DB
    assert corrected.turbine_levels_db[0] == pytest.approx(
        total.mean_levels_db[0] - 3.0
    )


def test_the_limits_of_11_7_hold_a_microdecibel_away() -> None:
    result = env.turbine_sound_levels([42.999999, 39.999999], [40.0, 40.0])
    assert result.regimes == (
        env.BackgroundCorrectionRegime.THREE_DB,
        env.BackgroundCorrectionRegime.UNDETERMINED,
    )


def test_bins_are_corrected_where_total_and_background_share_them() -> None:
    total = env.bin_sound_levels([45.0, 46.0, 50.0], [5.0, 5.2, 7.0])
    background = env.bin_sound_levels([38.0, 39.0, 36.0], [5.1, 4.9, 8.0])
    corrected = total.background_corrected(background)
    np.testing.assert_array_equal(corrected.wind_speeds_m_s, [5.0])
    assert corrected.total_levels_db[0] == pytest.approx(total.mean_levels_db[0])


def test_bins_pair_by_class_and_sector() -> None:
    """0.5 m/s bins and 20 degree sectors pair by their integer class."""
    total = env.bin_sound_levels(
        [45.0, 46.0, 50.0],
        [2.6, 2.4, 7.0],
        [355.0, 5.0, 181.0],
        bin_width_m_s=0.5,
        sector_width_deg=20.0,
    )
    background = env.bin_sound_levels(
        [38.0, 39.0],
        [2.55, 7.1],
        [1.0, 179.0],
        bin_width_m_s=0.5,
        sector_width_deg=20.0,
    )
    assert total.bin_width_m_s == pytest.approx(0.5)
    assert total.sector_width_deg == pytest.approx(20.0)
    corrected = total.background_corrected(background)
    np.testing.assert_allclose(corrected.wind_speeds_m_s, [2.5, 7.0])
    np.testing.assert_allclose(corrected.background_levels_db, [38.0, 39.0])


def test_one_wind_speed_class_pairs_sector_by_sector() -> None:
    """Two sectors of the same class each take their own background.

    The background is binned in the other order, so pairing on the class
    alone would take one sector's background for the other, or lose a sector.
    """
    total = env.bin_sound_levels([45.0, 50.0], [5.0, 5.0], [0.0, 90.0])
    background = env.bin_sound_levels([44.0, 38.0], [5.0, 5.0], [90.0, 0.0])
    corrected = total.background_corrected(background)
    np.testing.assert_allclose(corrected.wind_speeds_m_s, [5.0, 5.0])
    np.testing.assert_allclose(corrected.total_levels_db, [45.0, 50.0])
    np.testing.assert_allclose(corrected.background_levels_db, [38.0, 44.0])
    expected = [
        10.0 * math.log10(10.0**4.5 - 10.0**3.8),
        10.0 * math.log10(10.0**5.0 - 10.0**4.4),
    ]
    np.testing.assert_allclose(corrected.turbine_levels_db, expected)
    assert corrected.turbine_levels_db == pytest.approx([44.03, 48.74], abs=0.005)
    # Bins of one interval carry no type A uncertainty (NaN), and pass.
    assert np.all(np.isnan(corrected.turbine_uncertainty_db))


def _two_sectors() -> tuple[env.BinnedSoundLevels, env.BinnedSoundLevels]:
    """Totals and backgrounds of the same wind speed classes in two sectors."""
    speeds = [3.0, 4.0, 5.0, 3.0, 4.0, 5.0]
    directions = [0.0, 0.0, 0.0, 90.0, 90.0, 90.0]
    total = env.bin_sound_levels(
        [45.0, 47.0, 49.0, 40.0, 42.0, 44.0], speeds, directions
    )
    background = env.bin_sound_levels(
        [35.0, 34.0, 33.0, 32.0, 31.0, 30.0], speeds, directions
    )
    return total, background


def test_corrected_bins_keep_their_sector() -> None:
    """Binned by direction, each corrected bin says which sector it is (10.1)."""
    total, background = _two_sectors()
    corrected = total.background_corrected(background)
    np.testing.assert_array_equal(corrected.wind_speeds_m_s, [3.0, 4.0, 5.0] * 2)
    np.testing.assert_array_equal(
        corrected.wind_directions_deg, [0.0, 0.0, 0.0, 90.0, 90.0, 90.0]
    )
    assert not corrected.wind_directions_deg.flags.writeable
    by_speed = env.bin_sound_levels([45.0], [5.0]).background_corrected(
        env.bin_sound_levels([35.0], [5.0])
    )
    assert by_speed.wind_directions_deg is None


@pytest.mark.parametrize(
    ("language", "keys"),
    [
        ("en", ["Total", "Background", "Turbine"]),
        ("es", ["Total", "Fondo", "Aerogenerador"]),
    ],
)
def test_the_corrected_plot_draws_each_sector_apart(
    language: str, keys: list[str]
) -> None:
    """No line joins two sectors: each runs over its own wind speeds, in order.

    Within a sector the three levels share its colour, and each is drawn with
    the line style and marker its legend key shows.
    """
    total, background = _two_sectors()
    corrected = total.background_corrected(background)
    ax = corrected.plot(language=language)
    for line in ax.lines:
        np.testing.assert_array_equal(line.get_xdata(), [3.0, 4.0, 5.0])
    legend = ax.get_legend()
    texts = [t.get_text() for t in legend.get_texts()]
    assert texts == ["Sector 0°", "Sector 90°", *keys]
    key_style = {
        text: (handle.get_linestyle(), handle.get_marker())
        for text, handle in zip(texts, legend.legend_handles, strict=True)
    }
    by_label = {line.get_label(): line for line in ax.lines}
    for sector, rows in (("Sector 0°", slice(0, 3)), ("Sector 90°", slice(3, 6))):
        turbine = by_label[sector]
        sector_lines = [
            line for line in ax.lines if line.get_color() == turbine.get_color()
        ]
        assert len(sector_lines) == 3
        for key, levels in zip(
            keys,
            (
                corrected.total_levels_db,
                corrected.background_levels_db,
                corrected.turbine_levels_db,
            ),
            strict=True,
        ):
            (drawn,) = [
                line
                for line in sector_lines
                if np.allclose(np.asarray(line.get_ydata()), levels[rows])
            ]
            drawn_style = (drawn.get_linestyle(), drawn.get_marker())
            assert drawn_style == key_style[key]
    plt.close("all")


def test_a_sector_s_bins_are_joined_in_wind_speed_order() -> None:
    """Bins given out of order are drawn in wind speed order, sector by sector."""
    result = env.turbine_sound_levels(
        [50.0, 45.0, 47.0, 44.0, 40.0],
        [40.0, 35.0, 36.0, 34.0, 30.0],
        wind_speeds_m_s=[5.0, 3.0, 4.0, 5.0, 3.0],
        wind_directions_deg=[0.0, 0.0, 0.0, 90.0, 90.0],
    )
    ax = result.plot()
    by_label = {line.get_label(): line for line in ax.lines}
    np.testing.assert_array_equal(by_label["Sector 0°"].get_xdata(), [3.0, 4.0, 5.0])
    np.testing.assert_allclose(
        by_label["Sector 0°"].get_ydata(),
        result.turbine_levels_db[[1, 2, 0]],
    )
    np.testing.assert_array_equal(by_label["Sector 90°"].get_xdata(), [3.0, 5.0])
    plt.close("all")


#: The dark documentation page (scripts/figures/theme.py), on which every
#: sector line has to stay visible as it does on white.
_DARK_PAGE = "#1c2128"


def test_twelve_sectors_take_twelve_colours() -> None:
    """The twelve 30° sectors of 10.1 and 13.7 are told apart by colour.

    No two share a colour, none takes the grey of the level keys or the red of
    the ring of a bin within 3 dB of its background, and every sector line
    reads on the light page and on the dark one.
    """
    from matplotlib.colors import to_hex, to_rgb

    from phonometry._plot.common import contrast_ratio, delta_e_2000

    directions = np.repeat(np.arange(0.0, 360.0, 30.0), 2)
    speeds = np.tile([5.0, 6.0], 12)
    totals = 45.0 + 0.1 * np.arange(24)
    backgrounds = np.full(24, 35.0)
    backgrounds[-1] = totals[-1] - 2.0
    total = env.bin_sound_levels(totals, speeds, directions)
    background = env.bin_sound_levels(backgrounds, speeds, directions)
    ax = total.background_corrected(background).plot()
    legend = ax.get_legend()
    colours = {
        text.get_text(): to_rgb(handle.get_color())
        for text, handle in zip(legend.get_texts(), legend.legend_handles, strict=True)
    }
    sectors = [colours[f"Sector {angle}°"] for angle in range(0, 360, 30)]
    others = [colours[k] for k in ("Total", "Background", "Background within 3 dB")]
    assert len({to_hex(c) for c in sectors}) == 12
    for i, first in enumerate(sectors):
        for second in sectors[i + 1 :]:
            assert delta_e_2000(first, second) >= 15.0
        for other in others:
            assert delta_e_2000(first, other) >= 16.0
        for page in ((1.0, 1.0, 1.0), to_rgb(_DARK_PAGE)):
            assert contrast_ratio(first, page) >= 2.0
    plt.close("all")


@pytest.mark.parametrize(
    ("language", "names"),
    [
        ("en", ["Sector 22.5°", "Sector 45°"]),
        ("es", ["Sector 22,5°", "Sector 45°"]),
    ],
)
def test_a_sector_centre_is_written_in_the_plot_language(
    language: str, names: list[str]
) -> None:
    """A centre of 22.5° takes the decimal separator of the language."""
    directions = [22.5, 22.5, 45.0, 45.0]
    speeds = [5.0, 6.0, 5.0, 6.0]
    total = env.bin_sound_levels(
        [45.0, 46.0, 47.0, 48.0], speeds, directions, sector_width_deg=22.5
    )
    background = env.bin_sound_levels(
        [35.0] * 4, speeds, directions, sector_width_deg=22.5
    )
    ax = total.background_corrected(background).plot(language=language)
    texts = [t.get_text() for t in ax.get_legend().get_texts()]
    assert texts[:2] == names
    plt.close("all")


def test_equations_10_and_11() -> None:
    levels = np.array([35.0, 32.0, 28.0])
    u_w = np.array([1.0, 1.5, 2.0])
    result = env.predicted_receptor_level(levels, u_w)
    weights = 10.0 ** (levels / 10.0)
    propagated = float(np.sum(u_w * weights) / np.sum(weights))
    assert result.level_db == pytest.approx(10.0 * math.log10(np.sum(weights)))
    assert result.propagated_uncertainty_db == pytest.approx(propagated)
    assert result.combined_uncertainty_db == pytest.approx(
        math.sqrt(propagated**2 + 2.0**2 + 0.5**2)
    )


def test_quietest_turbines_leave_while_the_total_drops_1_db_or_less() -> None:
    """Totals: all 38.6 dB; without the three quietest 38.3 dB; without 32 dB, 37.1."""
    result = env.sound_relevant_turbines([35.0, 33.0, 32.0, 25.0, 20.0, 18.0])
    np.testing.assert_array_equal(
        result.relevant, [True, True, True, False, False, False]
    )
    assert result.indices == (0, 1, 2)
    assert result.total_level_db - result.relevant_level_db <= 1.0
    assert result.binning_wind_speed_m_s(
        [7.0, 8.0, 6.0, 5.0, 4.0, 3.0]
    ) == pytest.approx(7.0)


def test_one_loud_turbine_stands_alone() -> None:
    result = env.sound_relevant_turbines([40.0, 20.0, 19.0])
    assert result.indices == (0,)


def test_a_drop_of_1_db_to_within_rounding_leaves_the_turbine_out() -> None:
    """9.3.2.3 keeps a turbine whose exclusion reduces the total "by more than 1,0 dB".

    Taking the 24.531746756198842 dB turbine off the 30.4 dB one lowers the
    total by 0.99999999999999975 dB, which the energy sums compute as
    1.0000000000000036 dB. A drop of 2 mdB more keeps it.
    """
    levels = [30.4, 24.531746756198842]
    energies = 10.0 ** (np.asarray(levels) / 10.0)
    assert 10.0 * np.log10(energies.sum()) - 10.0 * np.log10(energies[0]) > 1.0
    result = env.sound_relevant_turbines(levels)
    np.testing.assert_array_equal(result.relevant, [True, False])
    kept = env.sound_relevant_turbines([30.4, 24.54])
    np.testing.assert_array_equal(kept.relevant, [True, True])


# ---------------------------------------------------------------------------
# Annex C: low frequency sound
# ---------------------------------------------------------------------------
def test_table_3_type_b_examples_are_transcribed() -> None:
    assert dict(env.TYPE_B_UNCERTAINTY_EXAMPLES_DB) == ref.WT_TABLE3_TYPE_B_DB


def test_table_c1_impedance_classes_are_transcribed() -> None:
    assert list(env.LOW_FREQUENCY_GROUND_IMPEDANCE_CLASSES) == list(
        ref.WT_C1_IMPEDANCE_CLASSES
    )
    for letter, (sigma, nordtest, text) in ref.WT_C1_IMPEDANCE_CLASSES.items():
        row = env.LOW_FREQUENCY_GROUND_IMPEDANCE_CLASSES[letter]
        assert row.flow_resistivity_kpa_s_m2 == pytest.approx(sigma)
        assert row.nordtest_classes_kpa_s_m2 == pytest.approx(nordtest)
        assert row.description == text


def test_tables_c2_to_c5_are_transcribed() -> None:
    np.testing.assert_array_equal(env.LOW_FREQUENCY_BANDS_HZ, ref.WT_C_BANDS_HZ)
    np.testing.assert_array_equal(
        env.LOW_FREQUENCY_GROUND_CORRECTION_DB, ref.WT_C2_GROUND_DB
    )
    np.testing.assert_array_equal(
        env.LOW_FREQUENCY_AIR_ATTENUATION_DB_PER_KM, ref.WT_C2_ALPHA_DB_PER_KM
    )
    for name, row in ref.WT_C3_FACADE_DB.items():
        np.testing.assert_array_equal(env.LOW_FREQUENCY_FACADE_INSULATION_DB[name], row)
    assert tuple(env.SWEDISH_LOW_FREQUENCY_LIMITS_DB.values()) == ref.WT_C5_SWEDEN_DB


def test_table_c4_a_weighting_is_iec_61672_table_3() -> None:
    table = {row[0]: row[1] for row in weighting_compliance._WEIGHTING_TABLE3}
    for frequency, value in zip(
        ref.WT_C_BANDS_HZ, ref.WT_C4_A_WEIGHTING_DB, strict=True
    ):
        assert wtr._A_WEIGHTING_DB[frequency] == pytest.approx(value)
        assert table[frequency] == pytest.approx(value)


def _iso_9613_1_db_per_km(humidity: float) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return 1000.0 * np.asarray(
            air_attenuation(
                np.asarray(ref.WT_C_BANDS_HZ),
                temperature_c=10.0,
                relative_humidity_percent=humidity,
            )
        )


def test_table_c2_air_attenuation_above_100_hz_is_iso_9613_1_at_70_percent() -> None:
    alpha = _iso_9613_1_db_per_km(70.0)
    np.testing.assert_array_equal(
        np.round(alpha[11:], 2), ref.WT_C2_ALPHA_DB_PER_KM[11:]
    )


def test_table_c2_air_attenuation_to_100_hz_is_the_danish_order_at_80_percent() -> None:
    """The cells up to 100 Hz are the order's, which it sets for 80 % humidity.

    At the 70 % of the caption, ISO 9613-1 is 0.01 dB/km to 0.02 dB/km higher
    from 50 Hz to 100 Hz. At 80 % it is within 0.01 dB/km of every cell from
    25 Hz to 100 Hz: the order's values are the Nord2000 band rates, a little
    above the pure-tone value at the band centre (0.26 at 100 Hz against 0.254),
    and nothing below 25 Hz.
    """
    np.testing.assert_array_equal(
        ref.WT_C2_ALPHA_DB_PER_KM[:11], ref.DK_BEK135_ALPHA_DB_PER_KM[:11]
    )
    printed = np.asarray(ref.WT_C2_ALPHA_DB_PER_KM)
    gap = np.round(_iso_9613_1_db_per_km(70.0)[7:11], 2) - printed[7:11]
    np.testing.assert_allclose(gap, [0.01, 0.01, 0.02, 0.02], atol=1e-12)
    at_80 = np.round(_iso_9613_1_db_per_km(80.0)[4:11], 2)
    assert np.max(np.abs(at_80 - printed[4:11])) <= 0.01 + 1e-12
    np.testing.assert_array_equal(printed[:4], 0.0)


def test_equation_c1_band_by_band() -> None:
    power = np.array([95.0, 96.0])
    result = env.wind_turbine_low_frequency_level(
        power,
        distance_m=500.0,
        hub_height_m=100.0,
        frequencies_hz=[63.0, 125.0],
        facade_insulation_db=[16.6, 20.2],
    )
    slant = math.hypot(500.0, 100.0)
    expected = (
        power
        + np.array([-26.2, -16.1])
        - 10.0 * math.log10(slant**2)
        - 11.0
        + np.array([4.3, 1.8])
        - np.array([0.11, 0.41]) * slant / 1000.0
    )
    np.testing.assert_allclose(result.outdoor_levels_db, expected)
    np.testing.assert_allclose(
        result.indoor_levels_db, expected - np.array([16.6, 20.2])
    )
    assert result.outdoor_level_db == pytest.approx(
        10.0 * math.log10(np.sum(10.0 ** (expected / 10.0)))
    )


def test_turbines_sum_energetically_per_band() -> None:
    one = env.wind_turbine_low_frequency_level(
        np.full(14, 100.0), distance_m=600.0, hub_height_m=120.0
    )
    two = env.wind_turbine_low_frequency_level(
        np.full((2, 14), 100.0), distance_m=[600.0, 600.0], hub_height_m=120.0
    )
    np.testing.assert_allclose(
        two.outdoor_levels_db, one.outdoor_levels_db + 10.0 * math.log10(2.0)
    )


def test_a_zero_air_attenuation_takes_nothing_off() -> None:
    """Zero is an absorption coefficient (Table C.2 prints 0,0 to 20 Hz).

    Only a negative one is refused.
    """
    result = env.wind_turbine_low_frequency_level(
        [95.0],
        distance_m=2000.0,
        hub_height_m=100.0,
        frequencies_hz=[50.0],
        air_attenuation_db_per_km=[0.0],
    )
    np.testing.assert_array_equal(result.air_attenuation_db, [[0.0]])
    slant = math.hypot(2000.0, 100.0)
    expected = 95.0 - 30.2 - 10.0 * math.log10(slant**2) - 11.0 + 4.7
    assert result.outdoor_level_db == pytest.approx(expected)


def test_a_band_without_a_table_value_needs_its_own() -> None:
    with pytest.raises(ValueError, match=r"Table C.2 has no value at 250 Hz"):
        env.wind_turbine_low_frequency_level(
            [90.0], distance_m=500.0, hub_height_m=100.0, frequencies_hz=[250.0]
        )


# ---------------------------------------------------------------------------
# Annexes J and A, Table 7
# ---------------------------------------------------------------------------
def test_equation_j1() -> None:
    result = env.sound_emergence([40.0, 44.5], [36.0, 41.0], wind_speeds_m_s=[5.0, 6.0])
    np.testing.assert_allclose(result.emergence_db, [4.0, 3.5])


def test_figure_a1_points() -> None:
    for depth, adjustment in ref.WT_FIGURE_A1_POINTS_DB:
        assert env.amplitude_modulation_adjustment(depth) == pytest.approx(adjustment)


def test_table_a1_is_iso_1996_2_table_j1() -> None:
    lower = -1.0
    for upper, adjustment in ref.WT_TABLE_A1:
        for audibility in (upper, (lower + upper) / 2.0):
            assert env.tonal_adjustment_from_mean_audibility(audibility) == adjustment
        lower = upper
    assert env.tonal_adjustment_from_mean_audibility(12.01) == 6
    for upper, adjustment in ref.WT_A2_COARSE:
        assert (
            env.tonal_adjustment_from_mean_audibility(upper, coarse=True) == adjustment
        )
    assert env.tonal_adjustment_from_mean_audibility(9.01, coarse=True) == 6


def test_the_most_severe_adjustment_alone_is_applied() -> None:
    result = env.wind_turbine_rating_level(
        40.0,
        tonal_adjustment_db=2.0,
        amplitude_modulation_adjustment_db=env.amplitude_modulation_adjustment(6.5),
        impulsive_adjustment_db=1.8,
    )
    assert result.governing == "amplitude_modulation"
    assert result.rating_level_db == pytest.approx(44.0)


def test_no_adjustment_governs_when_all_are_zero() -> None:
    result = env.wind_turbine_rating_level(40.0)
    assert result.governing is None
    assert result.rating_level_db == pytest.approx(40.0)


@pytest.mark.parametrize(
    "row",
    [r for i, r in enumerate(ref.WT_TABLE7_ROWS) if i != ref.WT_TABLE7_MISPRINTED_ROW],
)
def test_table_7_rows(row: tuple[float, float, tuple[float, ...]]) -> None:
    temperature, humidity, printed = row
    for distance, khz in zip(ref.WT_TABLE7_DISTANCES_M, printed, strict=True):
        found = env.upper_tone_search_frequency(
            distance, temperature_c=temperature, relative_humidity_percent=humidity
        ).upper_frequency_hz
        # Table 7 prints the nominal 3 150 Hz band as 3,2 kHz.
        assert found == pytest.approx(
            3150.0 if khz == pytest.approx(3.2) else khz * 1000.0
        )


def test_table_7_fourth_row_is_minus_10_degrees() -> None:
    _, humidity, printed = ref.WT_TABLE7_ROWS[ref.WT_TABLE7_MISPRINTED_ROW]
    at_minus_10 = [
        env.upper_tone_search_frequency(
            d, temperature_c=-10.0, relative_humidity_percent=humidity
        ).upper_frequency_hz
        / 1000.0
        for d in ref.WT_TABLE7_DISTANCES_M
    ]
    at_plus_10 = [
        env.upper_tone_search_frequency(
            d, temperature_c=10.0, relative_humidity_percent=humidity
        ).upper_frequency_hz
        / 1000.0
        for d in ref.WT_TABLE7_DISTANCES_M
    ]
    assert at_minus_10 == pytest.approx(printed)
    assert at_plus_10 == pytest.approx([10.0, 6.3, 5.0, 4.0])


# ---------------------------------------------------------------------------
# Published tables and plots
# ---------------------------------------------------------------------------
def test_published_arrays_are_read_only() -> None:
    for array in (
        env.LOW_FREQUENCY_BANDS_HZ,
        env.LOW_FREQUENCY_GROUND_CORRECTION_DB,
        env.LOW_FREQUENCY_AIR_ATTENUATION_DB_PER_KM,
        env.TONE_SEARCH_BANDS_HZ,
    ):
        assert not array.flags.writeable


def test_a_result_does_not_return_a_published_array() -> None:
    result = env.upper_tone_search_frequency(
        600.0, temperature_c=10.0, relative_humidity_percent=70.0
    )
    assert result.frequencies_hz is not env.TONE_SEARCH_BANDS_HZ


def test_plots_draw_their_numbers() -> None:
    lf = env.wind_turbine_low_frequency_level(
        np.full(14, 100.0),
        distance_m=600.0,
        hub_height_m=120.0,
        facade_insulation_db=env.LOW_FREQUENCY_FACADE_INSULATION_DB[
            "Denmark brick or similar"
        ],
    )
    ax = lf.plot()
    np.testing.assert_allclose(ax.lines[0].get_ydata(), lf.outdoor_levels_db)
    np.testing.assert_allclose(ax.lines[1].get_ydata(), lf.indoor_levels_db)
    plt.close("all")
    rating = env.wind_turbine_rating_level(40.0, tonal_adjustment_db=3.0)
    ax = rating.plot(language="es")
    assert "43,0" in ax.get_title()
    heights = [p.get_height() for p in ax.patches]
    assert heights == pytest.approx([3.0, 0.0, 0.0])
    plt.close("all")
    limit = env.upper_tone_search_frequency(
        300.0, temperature_c=10.0, relative_humidity_percent=50.0
    )
    ax = limit.plot()
    np.testing.assert_allclose(ax.lines[0].get_ydata(), limit.attenuation_db)
    plt.close("all")


def test_the_plots_say_what_their_marks_are() -> None:
    relevant = env.sound_relevant_turbines([33.5, 38.2, 29.4, 36.9, 25.1, 31.8, 27.0])
    ax = relevant.plot()
    assert [t.get_text() for t in ax.get_xticklabels()] == list("2416375")
    running = next(
        line for line in ax.lines if line.get_label() == "Energy sum of the loudest"
    )
    ydata = np.asarray(running.get_ydata())
    assert ydata[-1] == pytest.approx(relevant.total_level_db)
    # It first reaches the total less 1 dB at the last relevant turbine.
    first = int(np.argmax(ydata >= relevant.total_level_db - 1.0))
    assert first == len(relevant.indices) - 1
    assert ydata[first] == pytest.approx(relevant.relevant_level_db)
    plt.close("all")
    ax = env.wind_turbine_rating_level(
        41.0, tonal_adjustment_db=2.0, amplitude_modulation_adjustment_db=3.8
    ).plot()
    assert [t.get_text() for t in ax.get_legend().get_texts()] == [
        "Applied (the most severe, A.1)"
    ]
    plt.close("all")
    assert env.wind_turbine_rating_level(41.0).plot().get_legend() is None
    plt.close("all")
    ax = env.turbine_sound_levels([40.0, 42.0], [35.0, 38.0]).plot()
    assert ax.get_xlabel() == "Wind speed class"
    plt.close("all")


def _refusal_cases() -> list[tuple[str, object, str]]:
    by_speed = env.bin_sound_levels([45.0, 46.0], [5.0, 6.0])
    by_direction = env.bin_sound_levels([45.0, 46.0], [5.0, 6.0], [0.0, 90.0])
    elsewhere = env.bin_sound_levels([38.0], [9.0])
    half_metre = env.bin_sound_levels([38.0], [5.0], bin_width_m_s=0.5)
    profile = env.wind_shear_profile(4.5, 8.6, upper_height_m=120.0)
    relevant = env.sound_relevant_turbines([35.0, 33.0, 20.0])
    one_band = {"frequencies_hz": [63.0], "hub_height_m": 100.0}
    return [
        (
            "power law, speed not finite",
            lambda: env.power_law_wind_speed(
                np.nan, height_m=10.0, reference_height_m=120.0, shear_exponent=0.2
            ),
            r"'reference_speed_m_s' and 'shear_exponent' must be finite",
        ),
        (
            "power law, negative speed",
            lambda: env.power_law_wind_speed(
                -1.0, height_m=10.0, reference_height_m=120.0, shear_exponent=0.2
            ),
            r"'reference_speed_m_s' must not be negative",
        ),
        (
            "shear, speed not finite",
            lambda: env.wind_shear_exponent(
                np.nan, 5.0, height_m=120.0, reference_height_m=10.0
            ),
            r"The wind speeds must be finite",
        ),
        (
            "shear, zero speed",
            lambda: env.wind_shear_exponent(
                0.0, 5.0, height_m=120.0, reference_height_m=10.0
            ),
            r"must be positive for their ratio",
        ),
        (
            "log profile under the roughness length",
            lambda: env.logarithmic_wind_speed(
                5.0, height_m=0.01, reference_height_m=10.0
            ),
            r"Both heights must exceed the roughness length",
        ),
        (
            "log profile, negative speed",
            lambda: env.logarithmic_wind_speed(
                -5.0, height_m=10.0, reference_height_m=120.0
            ),
            r"'reference_speed_m_s' must be finite and not negative",
        ),
        (
            "profile at zero height",
            lambda: profile.speed_at(0.0),
            r"'height_m' must be finite and positive",
        ),
        (
            "one speed for two levels",
            lambda: env.bin_sound_levels([40.0, 41.0], [5.0]),
            r"'wind_speeds_m_s' must hold one value per data point",
        ),
        (
            "negative wind speed",
            lambda: env.bin_sound_levels([40.0], [-1.0]),
            r"'wind_speeds_m_s' must not be negative",
        ),
        (
            "one direction for two levels",
            lambda: env.bin_sound_levels([40.0, 41.0], [5.0, 6.0], [0.0]),
            r"'wind_directions_deg' must hold one value per data point",
        ),
        (
            "negative type B uncertainty",
            lambda: env.bin_sound_levels([40.0], [5.0], type_b_uncertainty_db=-0.1),
            r"'type_b_uncertainty_db' must be finite and not negative",
        ),
        (
            "background binned by direction",
            lambda: by_speed.background_corrected(by_direction),
            r"both by direction or neither",
        ),
        (
            "no bin in common",
            lambda: by_speed.background_corrected(elsewhere),
            r"share no bin",
        ),
        (
            "bins of other widths",
            lambda: by_speed.background_corrected(half_metre),
            r"with the same widths",
        ),
        (
            "total and background of other lengths",
            lambda: env.turbine_sound_levels([40.0, 41.0], [35.0]),
            r"must pair bin by bin",
        ),
        (
            "negative total uncertainty",
            lambda: env.turbine_sound_levels([40.0], [35.0], total_uncertainty_db=-0.1),
            r"'total_uncertainty_db' must be finite and not negative",
        ),
        (
            "minus infinity as the total uncertainty",
            lambda: env.turbine_sound_levels(
                [50.0, 45.0], [40.0, 44.0], total_uncertainty_db=-np.inf
            ),
            r"'total_uncertainty_db' must be finite and not negative",
        ),
        (
            "infinite background uncertainty",
            lambda: env.turbine_sound_levels(
                [50.0, 45.0], [40.0, 44.0], background_uncertainty_db=[np.inf, 0.5]
            ),
            r"'background_uncertainty_db' must be finite and not negative",
        ),
        (
            "minus infinity as a background uncertainty in the 3 dB regime",
            lambda: env.turbine_sound_levels(
                [50.0, 45.0], [40.0, 44.0], background_uncertainty_db=[0.5, -np.inf]
            ),
            r"'background_uncertainty_db' must be finite and not negative",
        ),
        (
            "two directions for one bin",
            lambda: env.turbine_sound_levels(
                [40.0], [35.0], wind_directions_deg=[0.0, 30.0]
            ),
            r"'wind_directions_deg' must hold one value per bin",
        ),
        (
            "two speeds for one bin",
            lambda: env.turbine_sound_levels(
                [40.0], [35.0], wind_speeds_m_s=[5.0, 6.0]
            ),
            r"'wind_speeds_m_s' must hold one value per bin",
        ),
        (
            "negative sound power uncertainty",
            lambda: env.predicted_receptor_level([35.0], [-1.0]),
            r"'sound_power_uncertainty_db' must be finite and not negative",
        ),
        (
            "negative model uncertainty",
            lambda: env.predicted_receptor_level(
                [35.0], [1.0], prediction_model_uncertainty_db=-1.0
            ),
            r"The model and modelling uncertainties must not be negative",
        ),
        (
            "one speed for three turbines",
            lambda: relevant.binning_wind_speed_m_s([6.0]),
            r"'turbine_wind_speeds_m_s' must hold one value per turbine",
        ),
        (
            "three columns for fourteen bands",
            lambda: env.wind_turbine_low_frequency_level(
                np.zeros((1, 3)), distance_m=500.0, hub_height_m=100.0
            ),
            r"one row per turbine and one column per band \(14\)",
        ),
        (
            "zero distance",
            lambda: env.wind_turbine_low_frequency_level(
                [95.0], distance_m=0.0, **one_band
            ),
            r"'distance_m' must be finite and positive",
        ),
        (
            "negative hub height",
            lambda: env.wind_turbine_low_frequency_level(
                [95.0], distance_m=500.0, frequencies_hz=[63.0], hub_height_m=-1.0
            ),
            r"'hub_height_m' must be finite and positive",
        ),
        (
            "a string as the weighting flag",
            lambda: env.wind_turbine_low_frequency_level(
                [95.0], distance_m=500.0, a_weighted="False", **one_band
            ),
            r"'a_weighted' must be True or False; got 'False'",
        ),
        (
            "negative air attenuation",
            lambda: env.wind_turbine_low_frequency_level(
                [95.0],
                distance_m=2000.0,
                air_attenuation_db_per_km=[-5.0],
                **{**one_band, "frequencies_hz": [50.0]},
            ),
            r"'air_attenuation_db_per_km' must not be negative",
        ),
        (
            "facade of two bands for one",
            lambda: env.wind_turbine_low_frequency_level(
                [95.0], distance_m=500.0, facade_insulation_db=[1.0, 2.0], **one_band
            ),
            r"'facade_insulation_db' must hold one value per band \(1\)",
        ),
        (
            "ambient and background of other lengths",
            lambda: env.sound_emergence([40.0, 41.0], [36.0]),
            r"must pair class by class",
        ),
        (
            "two speeds for one class",
            lambda: env.sound_emergence([40.0], [36.0], wind_speeds_m_s=[5.0, 6.0]),
            r"'wind_speeds_m_s' must hold one value per class",
        ),
        (
            "negative modulation depth",
            lambda: env.amplitude_modulation_adjustment(-1.0),
            r"'modulation_depth_db' must be finite and not negative",
        ),
        (
            "negative adjustment",
            lambda: env.wind_turbine_rating_level(40.0, tonal_adjustment_db=-1.0),
            r"The adjustments must not be negative",
        ),
    ]


@pytest.mark.parametrize(
    ("call", "match"),
    [case[1:] for case in _refusal_cases()],
    ids=[case[0] for case in _refusal_cases()],
)
def test_the_receptor_functions_refuse_what_they_cannot_compute(
    call: Callable[[], object], match: str
) -> None:
    with pytest.raises(ValueError, match=match):
        call()
