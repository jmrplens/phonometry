#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for a silencer measured where it stands (ISO 11820:1996).

The standard prints no worked example, so the oracles are its printed tables
and thresholds, the closed forms of its own equations, and the identities the
equations satisfy: a level shift common to both sides leaves a loss alone, the
area term is a ratio, and the temperature correction vanishes when the two
temperatures agree.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import noise_control
from phonometry.noise_control.silencer_in_situ import (
    INSTALLATION_CASES,
    ISO11820_AIR_GAS_CONSTANT,
    ISO11820_BACKGROUND_CORRECTIONS_DB,
    ISO11820_GAS_CONSTANT,
    ISO11820_MINIMUM_BACKGROUND_MARGIN_DB,
    ISO11820_SOUND_SPEED_M_S,
    SABINE_AREA_COEFFICIENT,
    SilencerInSituWarning,
)

BANDS = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])


def test_table_one_reproduces_its_printed_rows() -> None:
    printed = {3: 3.0, 4: 2.0, 5: 2.0, 6: 1.0, 7: 1.0, 8: 1.0, 9: 0.5, 10: 0.5}
    assert ISO11820_BACKGROUND_CORRECTIONS_DB == printed
    margins = np.arange(3, 16, dtype=float)
    corrections = noise_control.silencer_background_correction_db(margins)
    assert corrections[:8].tolist() == [3.0, 2.0, 2.0, 1.0, 1.0, 1.0, 0.5, 0.5]
    assert np.all(corrections[8:] == 0.0)


def test_the_table_is_not_the_logarithmic_subtraction() -> None:
    margins = np.arange(3, 11, dtype=float)
    table = noise_control.silencer_background_correction_db(margins)
    exact = -10.0 * np.log10(1.0 - 10.0 ** (-0.1 * margins))
    # The table is a rounded version of the formula and it departs from it in
    # both directions: at 5 dB it takes off 2,0 where the formula takes off
    # 1,65, and at 6 dB it takes off 1,0 where the formula takes off 1,26. The
    # largest departure over the printed rows is under four tenths of a
    # decibel.
    assert table[2] > exact[2]
    assert table[3] < exact[3]
    assert float(np.max(np.abs(table - exact))) < 0.35


def test_a_margin_under_three_decibels_is_refused() -> None:
    with pytest.raises(ValueError, match="invalid"):
        noise_control.silencer_background_correction_db([2.9])


def test_a_difference_between_two_rows_reads_the_lower_one() -> None:
    assert noise_control.silencer_background_correction_db([4.9]).tolist() == [2.0]
    assert noise_control.silencer_background_correction_db([5.0]).tolist() == [2.0]


def test_a_fraction_over_the_last_row_takes_nothing_off() -> None:
    """10 dB is the last row Table 1 prints; over it the correction is zero."""
    got = noise_control.silencer_background_correction_db([10.0, 10.0001, 10.5])
    assert got.tolist() == [0.5, 0.0, 0.0]


def test_equation_two_is_the_energy_mean() -> None:
    levels = [78.0, 80.0, 82.0]
    expected = 10.0 * math.log10(
        sum(10.0 ** (0.1 * value) for value in levels) / len(levels)
    )
    assert noise_control.mean_sound_pressure_level_db(levels) == pytest.approx(expected)


def test_equation_one_names_its_sides() -> None:
    source = np.array([95.0, 96.0, 94.0])
    receiver = np.array([70.0, 68.0, 63.0])
    difference = noise_control.transmission_level_difference_db(source, receiver)
    assert difference.tolist() == [25.0, 28.0, 31.0]


def test_equation_three_names_its_runs() -> None:
    difference = noise_control.insertion_level_difference_db([90.0], [72.0])
    assert difference.tolist() == [18.0]


def test_the_extraneous_route_subtracts_energy() -> None:
    corrected, capped = noise_control.extraneous_corrected_mean_level_db(
        [80.0, 80.0], [70.0, 70.0]
    )
    expected = 10.0 * math.log10(10.0**8.0 - 10.0**7.0)
    assert corrected == pytest.approx(expected)
    assert capped is False


def test_the_extraneous_correction_is_capped_at_three_decibels() -> None:
    with pytest.warns(SilencerInSituWarning, match="3 dB"):
        corrected, capped = noise_control.extraneous_corrected_mean_level_db(
            [80.0, 80.0], [78.0, 78.0]
        )
    assert capped is True
    assert corrected < 80.0


def test_an_extraneous_level_above_the_measurement_is_refused() -> None:
    with pytest.raises(ValueError, match="invalid"):
        noise_control.extraneous_corrected_mean_level_db([70.0], [70.0])


def test_the_reverberant_area_is_a_quarter_of_the_absorption() -> None:
    area = noise_control.reverberant_surface_area_m2(300.0, [1.2])
    expected = SABINE_AREA_COEFFICIENT * 300.0 / (ISO11820_SOUND_SPEED_M_S * 1.2)
    assert area[0] == pytest.approx(expected)
    assert ISO11820_SOUND_SPEED_M_S == 340.0


def test_a_non_positive_reverberation_time_is_refused() -> None:
    with pytest.raises(ValueError, match="reverberation_time_s"):
        noise_control.reverberant_surface_area_m2(300.0, [0.0])


def test_the_sound_power_level_adds_the_area_and_the_field_correction() -> None:
    levels = noise_control.sound_power_level_db(
        [80.0], area_m2=[10.0], field_correction_db=[1.0]
    )
    assert levels[0] == pytest.approx(80.0 + 10.0 * math.log10(10.0) + 1.0)


def test_a_field_correction_past_three_decibels_is_reported() -> None:
    with pytest.warns(SilencerInSituWarning, match="NOTE 4"):
        noise_control.sound_power_level_db(
            [80.0], area_m2=[10.0], field_correction_db=[4.0]
        )


def test_equal_temperatures_make_no_field_correction() -> None:
    assert noise_control.temperature_field_correction_db(
        receiver_temperature_c=20.0, source_temperature_c=20.0
    ) == pytest.approx(0.0)


def test_a_hot_source_makes_a_negative_correction() -> None:
    correction = noise_control.temperature_field_correction_db(
        receiver_temperature_c=20.0, source_temperature_c=200.0
    )
    assert correction == pytest.approx(5.0 * math.log10(293.0 / 473.0))
    assert correction < 0.0


def test_the_equation_uses_the_printed_273() -> None:
    with pytest.raises(ValueError, match="273"):
        noise_control.temperature_field_correction_db(
            receiver_temperature_c=-300.0, source_temperature_c=20.0
        )


def test_equation_nineteen_is_the_difference_plus_two_terms() -> None:
    res = noise_control.in_situ_transmission_loss(
        [95.0, 96.0],
        [70.0, 68.0],
        source_area_m2=2.0,
        receiver_area_m2=1.0,
        frequencies=[500.0, 1000.0],
        field_correction_difference_db=-1.0,
    )
    area_term = 10.0 * math.log10(2.0)
    assert res.area_term_db == pytest.approx(area_term)
    assert res.loss_db[0] == pytest.approx(25.0 + area_term - 1.0)
    assert res.symbol == "D_ts"


def test_a_common_level_shift_leaves_the_loss_alone() -> None:
    plain = noise_control.in_situ_transmission_loss(
        [95.0, 96.0], [70.0, 68.0], source_area_m2=2.0, receiver_area_m2=1.0
    )
    shifted = noise_control.in_situ_transmission_loss(
        [98.0, 99.0], [73.0, 71.0], source_area_m2=2.0, receiver_area_m2=1.0
    )
    assert np.allclose(plain.loss_db, shifted.loss_db)


def test_equal_areas_leave_no_area_term() -> None:
    res = noise_control.in_situ_transmission_loss(
        [95.0], [70.0], source_area_m2=1.4, receiver_area_m2=1.4
    )
    assert res.area_term_db == pytest.approx(0.0)


def test_equation_twenty_one_is_the_insertion_shape() -> None:
    res = noise_control.in_situ_insertion_loss(
        [90.0, 92.0],
        [72.0, 70.0],
        area_without_m2=1.0,
        area_with_m2=1.0,
        case=17,
    )
    assert res.loss_db.tolist() == [18.0, 22.0]
    assert res.symbol == "D_is"
    assert res.case is not None
    assert res.case.number == 17


def test_a_case_of_the_wrong_kind_is_refused() -> None:
    with pytest.raises(ValueError, match="insertion measurement"):
        noise_control.in_situ_transmission_loss(
            [95.0], [70.0], source_area_m2=1.0, receiver_area_m2=1.0, case=18
        )
    with pytest.raises(ValueError, match="transmission measurement"):
        noise_control.in_situ_insertion_loss(
            [95.0], [70.0], area_without_m2=1.0, area_with_m2=1.0, case=4
        )


def test_figure_one_has_twenty_installations() -> None:
    assert len(INSTALLATION_CASES) == 20
    transmission = [
        c for c in INSTALLATION_CASES.values() if c.quantity == "transmission"
    ]
    insertion = [c for c in INSTALLATION_CASES.values() if c.quantity == "insertion"]
    assert len(transmission) == 16
    assert len(insertion) == 4


def test_the_source_area_rule_follows_the_case_number() -> None:
    assert "measurement surface" in noise_control.installation_case(1).source_area_rule
    assert "one-quarter" in noise_control.installation_case(5).source_area_rule
    assert "one-half" in noise_control.installation_case(9).source_area_rule
    assert "one-half" in noise_control.installation_case(16).source_area_rule


def test_the_receiver_area_rule_follows_the_receiver_side() -> None:
    for number in (1, 5, 9, 13):
        case = noise_control.installation_case(number)
        assert case.receiver_side == "duct"
        assert "duct cross-section" in case.receiver_area_rule
    for number in (2, 6, 10, 14):
        case = noise_control.installation_case(number)
        assert case.receiver_side == "diffuse_room"
        assert "absorption" in case.receiver_area_rule
    for number in (3, 4, 7, 8, 11, 12, 15, 16):
        assert (
            "enveloping" in noise_control.installation_case(number).receiver_area_rule
        )


def test_the_insertion_cases_name_their_run() -> None:
    case = noise_control.installation_case(18)
    assert "without the silencer" in case.source_area_rule
    assert "with the silencer" in case.receiver_area_rule
    assert case.source_side.startswith("any")


def test_a_case_outside_the_figure_is_refused() -> None:
    with pytest.raises(ValueError, match="1 to 20"):
        noise_control.installation_case(21)


def test_the_octave_fold_is_the_energy_sum_of_three() -> None:
    octaves = noise_control.octave_levels_from_third_octave_db(
        [70.0, 70.0, 70.0, 80.0, 80.0, 80.0]
    )
    assert octaves[0] == pytest.approx(70.0 + 10.0 * math.log10(3.0))
    assert octaves[1] == pytest.approx(80.0 + 10.0 * math.log10(3.0))


def test_the_octave_fold_needs_whole_octaves() -> None:
    with pytest.raises(ValueError, match="multiple of 3"):
        noise_control.octave_levels_from_third_octave_db([70.0, 70.0])


def test_the_permitted_fold_is_not_the_forbidden_one() -> None:
    # 9.1.5 permits the fold on levels and forbids it on level differences.
    # The library does perform the forbidden one for ISO 11691, and the two
    # give different answers on the same three numbers, which is the point.
    thirds = [30.0, 30.0, 5.0]
    permitted = noise_control.octave_levels_from_third_octave_db(thirds)
    forbidden = noise_control.octave_insertion_loss(thirds)
    assert not np.isclose(permitted[0], forbidden[0])


def test_equation_thirteen_is_a_pressure_difference() -> None:
    assert noise_control.total_pressure_loss_pa(320.0, 180.0) == pytest.approx(140.0)


def test_equation_fourteen_vanishes_for_equal_areas() -> None:
    static = noise_control.static_pressure_difference_pa(
        140.0,
        volume_flow_m3_s=3.0,
        density_kg_m3=1.2,
        upstream_area_m2=0.5,
        downstream_area_m2=0.5,
    )
    assert static == pytest.approx(140.0)


def test_equation_fourteen_moves_with_the_area_change() -> None:
    static = noise_control.static_pressure_difference_pa(
        140.0,
        volume_flow_m3_s=3.0,
        density_kg_m3=1.2,
        upstream_area_m2=0.5,
        downstream_area_m2=1.0,
    )
    expected = 140.0 - 1.2 * 9.0 / 2.0 * (1.0 / 0.25 - 1.0 / 1.0)
    assert static == pytest.approx(expected)


def test_equation_fifteen_is_one_and_a_half_diameters() -> None:
    distance = noise_control.measurement_distance_upstream_m(0.25)
    assert distance == pytest.approx(1.5 * math.sqrt(4.0 * 0.25 / math.pi))


def test_equation_sixteen_subtracts_the_free_area() -> None:
    distance = noise_control.measurement_distance_downstream_m(0.25, 0.09)
    assert distance == pytest.approx(12.0 * 0.5 - 10.0 * 0.3)


def test_a_free_area_that_leaves_no_distance_is_reported() -> None:
    with pytest.warns(SilencerInSituWarning, match="8.3.1"):
        noise_control.measurement_distance_downstream_m(0.25, 0.36)


def test_equation_twenty_seven_and_twenty_eight() -> None:
    velocity_pressure = noise_control.velocity_pressure_pa([260.0], [200.0])
    assert velocity_pressure.tolist() == [60.0]
    velocity = noise_control.flow_velocity_m_s(velocity_pressure, 1.2)
    assert velocity[0] == pytest.approx(math.sqrt(2.0 * 60.0 / 1.2))


def test_a_negative_velocity_pressure_is_refused() -> None:
    with pytest.raises(ValueError, match="velocity_pressure_pa"):
        noise_control.flow_velocity_m_s([-1.0], 1.2)


def test_equation_twenty_nine_takes_air_by_default() -> None:
    density = noise_control.gas_density_kg_m3(temperature_c=20.0)
    assert density == pytest.approx(100_000.0 / (ISO11820_AIR_GAS_CONSTANT * 293.0))
    assert ISO11820_AIR_GAS_CONSTANT == 287.0
    assert ISO11820_GAS_CONSTANT == 8314.4


def test_equation_twenty_nine_admits_another_gas() -> None:
    density = noise_control.gas_density_kg_m3(
        temperature_c=20.0, molar_mass_kg_kmol=44.01
    )
    assert density == pytest.approx(44.01 * 100_000.0 / (ISO11820_GAS_CONSTANT * 293.0))


def test_equation_thirty_one_scales_by_the_area_ratio() -> None:
    velocity = noise_control.silencer_flow_velocity_m_s(
        8.0, upstream_area_m2=0.5, free_area_m2=0.2
    )
    assert velocity == pytest.approx(8.0 * 0.5 / 0.2)


def test_the_printed_thresholds() -> None:
    assert ISO11820_MINIMUM_BACKGROUND_MARGIN_DB == 3.0
    assert noise_control.MAXIMUM_EXTRANEOUS_CORRECTION_DB == 3.0
    assert noise_control.ISO11820_OCTAVE_BAND_RANGE_HZ == (63.0, 4000.0)
    assert noise_control.ISO11820_THIRD_OCTAVE_BAND_RANGE_HZ == (50.0, 5000.0)


def test_the_plot_draws_the_difference_and_the_loss() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res = noise_control.in_situ_transmission_loss(
        np.full(BANDS.size, 95.0),
        np.full(BANDS.size, 70.0),
        source_area_m2=2.0,
        receiver_area_m2=1.0,
        frequencies=BANDS,
    )
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax)
    assert len(drawn.lines) == 2
    assert drawn.get_title()
    plt.close(fig)


def test_the_spanish_plot_translates_its_labels() -> None:
    matplotlib = pytest.importorskip("matplotlib")
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    res = noise_control.in_situ_insertion_loss(
        np.full(BANDS.size, 90.0),
        np.full(BANDS.size, 72.0),
        area_without_m2=1.0,
        area_with_m2=1.0,
        frequencies=BANDS,
    )
    fig, ax = plt.subplots()
    drawn = res.plot(ax=ax, language="es")
    assert "silenciador" in drawn.get_title()
    plt.close(fig)


def test_a_band_centre_at_zero_is_refused() -> None:
    with pytest.raises(ValueError, match="frequencies"):
        noise_control.in_situ_transmission_loss(
            [90.0, 80.0],
            [70.0, 60.0],
            source_area_m2=0.9,
            receiver_area_m2=9.0,
            frequencies=[0.0, 250.0],
        )


def test_a_non_finite_field_correction_is_refused() -> None:
    with pytest.raises(ValueError, match="field_correction_difference_db"):
        noise_control.in_situ_transmission_loss(
            [90.0],
            [70.0],
            source_area_m2=0.9,
            receiver_area_m2=9.0,
            field_correction_difference_db=float("nan"),
        )


def test_a_non_finite_temperature_is_refused() -> None:
    with pytest.raises(ValueError, match="source_temperature_c"):
        noise_control.temperature_field_correction_db(
            receiver_temperature_c=20.0, source_temperature_c=float("nan")
        )
