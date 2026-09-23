#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for a silencer measured where it stands (ISO 11820:1996).

The standard prints no worked example, so the first oracles are its printed
tables and thresholds, the closed forms of its own equations, and the
identities the equations satisfy: a level shift common to both sides leaves a
loss alone, the area term is a ratio, and the temperature correction vanishes
when the two temperatures agree.

The second half of the file is what other people printed. Annex B of
ISO 14163:1998 works the conversion of clause 9.1.5 through three spectra; a
2014 master's thesis at the Universidad Politécnica de Madrid measured three
splitter silencers to UNE-EN ISO 11820 and printed the whole reduction; and
six textbooks and engineering guidelines print worked examples of the closed
forms ISO 11820 shares with the rest of the field. Those numbers, with the
document, the edition, the PDF page and the printed folio each was read on,
are in ``tests/reference_data/silencer_in_situ.py``, which the conformance
report reads as well so that the two can never assert different values.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest
from reference_data import silencer_in_situ as oracle

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
    assert res.area_term_db.shape == (2,)
    assert np.allclose(res.area_term_db, [area_term, area_term])
    assert res.field_correction_difference_db.shape == (2,)
    assert np.allclose(res.field_correction_difference_db, [-1.0, -1.0])
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
    assert res.area_term_db.shape == (1,)
    assert np.allclose(res.area_term_db, [0.0])


def test_the_areas_of_a_diffuse_room_move_band_by_band() -> None:
    """ISO 11820:1996 3.3 and 3.4, printed folio 3 (PDF page 11).

    S = (6 ln 10) V/(c T) with T the reverberation time, and every level of
    Equations (5) to (11) is "in one-third-octave or octave bands", so where a
    side is a diffuse room its area is a band quantity. An array of areas and
    an array of field corrections each apply band for band.
    """
    areas = noise_control.reverberant_surface_area_m2(200.0, [2.0, 1.0, 0.5])
    res = noise_control.in_situ_transmission_loss(
        [95.0, 96.0, 94.0],
        [70.0, 68.0, 63.0],
        source_area_m2=0.9,
        receiver_area_m2=areas,
        field_correction_difference_db=[0.5, 0.0, -0.5],
    )
    expected_terms = 10.0 * np.log10(0.9 / areas)
    assert np.allclose(res.area_term_db, expected_terms, rtol=0.0, atol=1e-12)
    assert res.area_term_db.shape == (3,)
    assert np.allclose(
        res.loss_db,
        np.array([25.0, 28.0, 31.0]) + expected_terms + np.array([0.5, 0.0, -0.5]),
        rtol=0.0,
        atol=1e-12,
    )


def test_a_single_area_broadcasts_over_the_bands() -> None:
    scalar = noise_control.in_situ_insertion_loss(
        [90.0, 92.0, 88.0],
        [72.0, 70.0, 69.0],
        area_without_m2=2.0,
        area_with_m2=[1.5],
        field_correction_difference_db=0.3,
    )
    repeated = noise_control.in_situ_insertion_loss(
        [90.0, 92.0, 88.0],
        [72.0, 70.0, 69.0],
        area_without_m2=[2.0, 2.0, 2.0],
        area_with_m2=[1.5, 1.5, 1.5],
        field_correction_difference_db=[0.3, 0.3, 0.3],
    )
    assert np.array_equal(scalar.loss_db, repeated.loss_db)
    assert np.array_equal(scalar.area_term_db, repeated.area_term_db)
    assert np.array_equal(
        scalar.field_correction_difference_db,
        repeated.field_correction_difference_db,
    )
    assert scalar.area_term_db.shape == (3,)
    assert scalar.field_correction_difference_db.shape == (3,)


def test_areas_that_do_not_match_the_bands_are_refused() -> None:
    with pytest.raises(ValueError, match="'receiver_area_m2' must be one value"):
        noise_control.in_situ_transmission_loss(
            [95.0, 96.0, 94.0],
            [70.0, 68.0, 63.0],
            source_area_m2=0.9,
            receiver_area_m2=[10.0, 9.0],
        )
    with pytest.raises(ValueError, match="'area_without_m2' must be one value"):
        noise_control.in_situ_insertion_loss(
            [90.0, 92.0],
            [72.0, 70.0],
            area_without_m2=[1.0, 1.0, 1.0],
            area_with_m2=1.0,
        )
    with pytest.raises(
        ValueError, match="'field_correction_difference_db' must be one value"
    ):
        noise_control.in_situ_insertion_loss(
            [90.0, 92.0],
            [72.0, 70.0],
            area_without_m2=1.0,
            area_with_m2=1.0,
            field_correction_difference_db=[0.0, 0.1, 0.2],
        )


def test_a_non_positive_area_inside_an_array_is_refused() -> None:
    for bad in (0.0, -1.0):
        with pytest.raises(ValueError, match="source_area_m2"):
            noise_control.in_situ_transmission_loss(
                [95.0, 96.0],
                [70.0, 68.0],
                source_area_m2=[0.9, bad],
                receiver_area_m2=1.0,
            )
        with pytest.raises(ValueError, match="area_with_m2"):
            noise_control.in_situ_insertion_loss(
                [90.0, 92.0],
                [72.0, 70.0],
                area_without_m2=1.0,
                area_with_m2=[bad, 1.0],
            )


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
            field_correction_difference_db=math.nan,
        )


def test_a_non_finite_temperature_is_refused() -> None:
    with pytest.raises(ValueError, match="source_temperature_c"):
        noise_control.temperature_field_correction_db(
            receiver_temperature_c=20.0, source_temperature_c=math.nan
        )


# ---------------------------------------------------------------------------
# Printed numbers, from documents that are not ISO 11820
# ---------------------------------------------------------------------------

#: Equations (17) and (18) at one measuring point take off a correction that
#: depends on the margin alone, so the level they are swept on cancels.
CARRIER_DB = 90.0

#: ISO 11820 3.3 reads S as a quarter of the Sabine equivalent absorption area
#: A. Ver and Beranek and Barron both print A, so their numbers are four times
#: what ``reverberant_surface_area_m2`` returns; the factor is theirs, printed
#: as the 55,26 = 24 ln 10 in front of their own expression.
SABINE_QUARTERS = 4.0


def folded_octave_level(third_octave_db: tuple[float, ...]) -> float:
    """One octave level out of its three one-third octaves, 9.1.5."""
    return float(noise_control.octave_levels_from_third_octave_db(third_octave_db)[0])


def background_correction_db(margin_db: float) -> float:
    """What Equations (17) and (18) take off at a single measuring point."""
    with warnings.catch_warnings():
        # Barron's table reaches down to a 1 dB margin, where ISO 11820 caps
        # the correction and refuses to call the level determined. The cap is
        # tested on its own below; this helper is about the arithmetic under
        # it, which the module returns uncapped either way.
        warnings.simplefilter("ignore", SilencerInSituWarning)
        corrected, _ = noise_control.extraneous_corrected_mean_level_db(
            [CARRIER_DB], [CARRIER_DB - margin_db]
        )
    return CARRIER_DB - corrected


def sabine_absorption_m2(volume_m3: float, time_s: float, speed_m_s: float) -> float:
    """The Sabine absorption area the books print, four times our own."""
    area = noise_control.reverberant_surface_area_m2(
        volume_m3, [time_s], speed_of_sound=speed_m_s
    )
    return SABINE_QUARTERS * float(area[0])


def test_iso14163_table_b1_folds_to_its_printed_octave_levels() -> None:
    """ISO 14163:1998 Table B.1, the one worked example ISO prints of 9.1.5."""
    for name, sides in oracle.ISO14163_TABLE_B1_THIRD_OCTAVE_DB.items():
        printed = oracle.ISO14163_TABLE_B1_OCTAVE_DB[name]
        for side, want in zip(sides, printed, strict=True):
            assert folded_octave_level(side) == pytest.approx(want, abs=0.5)
            assert round(folded_octave_level(side)) == want


def test_iso14163_table_b1_octave_attenuation_follows_the_spectrum() -> None:
    """The printed attenuation row, and why 9.1.5 forbids the other route.

    The three spectra share one one-third-octave attenuation, so folding the
    difference has nothing to vary with and answers 7 dB for every one of
    them. Folding the levels on each side and subtracting afterwards, which is
    what the clause permits, gives the 7, 12 and 5 dB the table prints.
    """
    for name, sides in oracle.ISO14163_TABLE_B1_THIRD_OCTAVE_DB.items():
        source, attenuated = (round(folded_octave_level(side)) for side in sides)
        assert (
            source - attenuated
            == (oracle.ISO14163_TABLE_B1_OCTAVE_ATTENUATION_DB[name])
        )
    forbidden = noise_control.octave_insertion_loss(
        list(oracle.ISO14163_TABLE_B1_THIRD_OCTAVE_ATTENUATION_DB)
    )
    assert round(float(forbidden[0])) == 7.0
    assert set(oracle.ISO14163_TABLE_B1_OCTAVE_ATTENUATION_DB.values()) == {
        7.0,
        12.0,
        5.0,
    }


def test_the_thesis_position_means_reproduce_its_printed_column() -> None:
    """Holgado Palacios (2014), Tabla XL: six positions, twenty-one bands."""
    for positions, printed in oracle.HOLGADO_TABLE_XL.values():
        mean = noise_control.mean_sound_pressure_level_db(positions)
        assert mean == pytest.approx(printed, abs=0.05)
        assert round(mean, 1) == printed


def test_the_energy_mean_is_what_the_thesis_used_and_not_the_plain_one() -> None:
    """The oracle discriminates: an arithmetic mean fails nineteen of the rows."""
    agreeing = 0
    worst = 0.0
    for positions, printed in oracle.HOLGADO_TABLE_XL.values():
        plain = float(np.mean(positions))
        agreeing += round(plain, 1) == printed
        worst = max(worst, abs(plain - printed))
    assert agreeing == 2
    assert worst > 2.5


def test_the_thesis_insertion_loss_reproduces_its_three_printed_columns() -> None:
    """Tablas LXIV to LXVI: three silencers, sixty-three bands of Equation (21).

    Case 18 of Figure 1, a duct on the source side and a diffuse room on the
    receiver side, so both areas are a quarter of the room absorption and both
    move band by band with the reverberation time. The whole table goes in at
    once, with the two areas as the band arrays reverberant_surface_area_m2
    returns. The tolerance is the rounding of the printed inputs, 0,1 dB on
    the levels and 0,01 s on the times, which together reach about 0,13 dB;
    the printed tenth of the D_is column is out of reach from these summary
    columns and the thesis computed it from unrounded position means.
    """
    for table in oracle.HOLGADO_INSERTION_TESTS.values():
        rows = list(table.values())
        area_without = noise_control.reverberant_surface_area_m2(
            oracle.HOLGADO_ROOM_VOLUME_M3, [row[0] for row in rows]
        )
        area_with = noise_control.reverberant_surface_area_m2(
            oracle.HOLGADO_ROOM_VOLUME_M3, [row[2] for row in rows]
        )
        result = noise_control.in_situ_insertion_loss(
            [row[1] for row in rows],
            [row[3] for row in rows],
            area_without_m2=area_without,
            area_with_m2=area_with,
            frequencies=list(table),
            field_correction_difference_db=0.0,
            case=18,
        )
        assert result.loss_db == pytest.approx([row[4] for row in rows], abs=0.15)
        # The same numbers as one band at a time with scalar areas.
        for index, row in enumerate(rows):
            band = noise_control.in_situ_insertion_loss(
                [row[1]],
                [row[3]],
                area_without_m2=float(area_without[index]),
                area_with_m2=float(area_with[index]),
                case=18,
            )
            assert float(result.loss_db[index]) == pytest.approx(
                float(band.loss_db[0]), abs=1e-12
            )


def test_the_thesis_area_term_is_not_negligible_in_every_band() -> None:
    """The area term carries its own weight, so the row is not a subtraction.

    At 80 Hz of the 100-200 test the two reverberation times differ enough to
    move the answer by more than a decibel, and dropping the term would miss
    the printed value; at 400 Hz the two times agree and it is exactly zero.
    """
    table = oracle.HOLGADO_TABLE_LXIV
    without = noise_control.reverberant_surface_area_m2(
        oracle.HOLGADO_ROOM_VOLUME_M3, [row[0] for row in table.values()]
    )
    with_silencer = noise_control.reverberant_surface_area_m2(
        oracle.HOLGADO_ROOM_VOLUME_M3, [row[2] for row in table.values()]
    )
    terms = 10.0 * np.log10(without / with_silencer)
    bands = list(table)
    assert float(terms[bands.index(80.0)]) == pytest.approx(-1.13, abs=0.01)
    assert float(terms[bands.index(400.0)]) == pytest.approx(0.0, abs=1e-12)
    assert float(np.max(np.abs(terms))) > 1.0


def test_barron_table_3_4_is_the_energy_subtraction_at_one_point() -> None:
    """Barron (2003) Table 3-4, twenty-two printed margins from 1 dB to 20 dB."""
    for margin, printed in oracle.BARRON_TABLE_3_4_DB.items():
        correction = background_correction_db(margin)
        assert correction == pytest.approx(printed, abs=0.05)
        assert round(correction, 1) == printed


def test_the_printed_table_of_iso11820_is_not_that_subtraction() -> None:
    """Table 1 is stepped and deliberately not the logarithmic subtraction.

    Barron prints 1,7 dB at a 5 dB margin and 0,7 dB at 8 dB; ISO 11820
    Table 1 takes off 2 dB and 1 dB at the same two margins. The two tables
    are two rules and the library keeps them apart.
    """
    for margin, table_value in ((5.0, 2.0), (8.0, 1.0)):
        stepped = noise_control.silencer_background_correction_db([margin])
        assert float(stepped[0]) == table_value
        assert oracle.BARRON_TABLE_3_4_DB[margin] != table_value


def test_the_two_routes_agree_at_the_three_decibel_margin() -> None:
    """Table 1 and the energy route share their boundary.

    BS EN ISO 11820:1997, clause 4.1 on printed folio 4 (PDF page 12): "If
    the measuring conditions are such that a correction of 3 dB is not
    sufficient, then L_p1 cannot be determined", and Table 1 on folio 5 (PDF
    page 13) prints "< 3" as invalid and "3" as a correction of 3. The energy
    route of 9.1.1, folio 10 (PDF page 18), is offered as an alternative to
    that table under the same "maximum correction is 3 dB". So a 3 dB margin
    is admitted on both routes, and the 3,0206 dB the energy subtraction
    takes off there is the printed 3 dB unrounded, which is how ISO 3746:2010
    8.3.3, folio 15 (PDF page 24), prints the same number: "3 dB (the value
    for dL_pA = 3 dB)". Barron's own table prints 3,0 dB there, rounded.
    """
    assert oracle.BARRON_TABLE_3_4_DB[3.0] == 3.0
    assert float(noise_control.silencer_background_correction_db([3.0])[0]) == 3.0
    with warnings.catch_warnings():
        warnings.simplefilter("error", SilencerInSituWarning)
        corrected, capped = noise_control.extraneous_corrected_mean_level_db(
            [CARRIER_DB], [CARRIER_DB - 3.0]
        )
    assert capped is False
    assert CARRIER_DB - corrected == pytest.approx(3.0206, abs=5e-4)


def test_a_margin_under_three_decibels_trips_the_extraneous_cap() -> None:
    """A tenth under the row Table 1 still accepts is past the cap."""
    with pytest.warns(SilencerInSituWarning, match="3 dB"):
        corrected, capped = noise_control.extraneous_corrected_mean_level_db(
            [CARRIER_DB], [CARRIER_DB - 2.9]
        )
    assert capped is True
    assert CARRIER_DB - corrected > 3.0206


def test_no_printed_three_decibel_margin_trips_the_cap() -> None:
    """Every level from 40 dB to 130 dB in tenths, 3,0 dB over its extraneous sound.

    The two energy means of such a pair differ from 3 dB by up to 1,4e-14 dB
    in floating point, and 111 of the 901 pairs land under it, so a bare
    comparison with 3 would flip printed 3,0 dB margins into capped ones.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("error", SilencerInSituWarning)
        for step in range(901):
            level = round(40.0 + 0.1 * step, 10)
            _, capped = noise_control.extraneous_corrected_mean_level_db(
                [level], [level - 3.0]
            )
            assert capped is False


def test_the_margin_window_is_the_declared_thousandth_of_a_nanodecibel() -> None:
    """A margin two nanodecibels short of 3 dB is short of it, not equal to it.

    The window that keeps a printed 3,0 dB margin out of the cap is the
    absolute one the module declares, so a deficit larger than it caps. Only
    a relative tolerance left at its default would widen the window to three
    times the declared figure, the 3 dB of clause 4 being the reference.
    """
    for deficit, expected in ((5e-10, False), (2e-9, True), (1e-8, True)):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SilencerInSituWarning)
            _, capped = noise_control.extraneous_corrected_mean_level_db(
                [CARRIER_DB], [CARRIER_DB - (3.0 - deficit)]
            )
        assert capped is expected


def test_two_worked_background_subtractions() -> None:
    """Bies, Hansen and Howard (2017) Example 1.4 and Barron (2003) Example 3-6."""
    for level, background, printed in (
        oracle.BIES_EXAMPLE_1_4_DB,
        oracle.BARRON_EXAMPLE_3_6_DB,
    ):
        corrected, capped = noise_control.extraneous_corrected_mean_level_db(
            [level], [background]
        )
        assert round(corrected, 1) == printed
        assert capped is False


def test_barron_example_3_6_agrees_with_its_own_tabulated_correction() -> None:
    """The book reaches 81,7 dB twice, by subtraction and off Table 3-4.

    Its second route takes 1,3 dB off the measured 83 dB at a 6 dB margin,
    which is the same row of Table 3-4 the sweep above checks.
    """
    level, _, printed = oracle.BARRON_EXAMPLE_3_6_DB
    assert round(level - oracle.BARRON_TABLE_3_4_DB[6.0], 1) == printed


def test_barron_example_3_4_mean_and_area_term() -> None:
    """Nine levels on a measurement surface, and the 10 lg (S/S0) of its area."""
    mean = noise_control.mean_sound_pressure_level_db(
        oracle.BARRON_EXAMPLE_3_4_LEVELS_DB
    )
    assert round(mean, 1) == oracle.BARRON_EXAMPLE_3_4_MEAN_DB
    term = noise_control.sound_power_level_db(
        [0.0], area_m2=[oracle.BARRON_EXAMPLE_3_4_AREA_M2]
    )
    assert round(float(term[0]), 2) == oracle.BARRON_EXAMPLE_3_4_AREA_TERM_DB
    # The area itself follows from the printed 2,60 m by 2,80 m by 1,60 m high
    # surface, which the solution writes out as 17,28 + 7,28.
    assert 2.0 * (2.60 + 2.80) * 1.60 + 2.60 * 2.80 == pytest.approx(
        oracle.BARRON_EXAMPLE_3_4_AREA_M2
    )


def test_barron_example_3_3_sound_power_needs_its_field_correction() -> None:
    """The three terms of Equation (5) together, on a hemisphere of 9,817 m2.

    The book's third term is the characteristic impedance of the room air,
    -10 lg(rho c / 400), which is the K of Equation (5) for this measurement.
    Left out, the answer reads 90,5 dB and misses the printed 90,4 dB, so the
    example does exercise the term.
    """
    mean = noise_control.mean_sound_pressure_level_db(
        oracle.BARRON_EXAMPLE_3_3_LEVELS_DB
    )
    correction = -10.0 * math.log10(oracle.BARRON_EXAMPLE_3_3_IMPEDANCE_RAYL / 400.0)
    level = noise_control.sound_power_level_db(
        [mean],
        area_m2=[oracle.BARRON_EXAMPLE_3_3_AREA_M2],
        field_correction_db=[correction],
    )
    assert round(float(level[0]), 1) == oracle.BARRON_EXAMPLE_3_3_SOUND_POWER_DB
    without = noise_control.sound_power_level_db(
        [mean], area_m2=[oracle.BARRON_EXAMPLE_3_3_AREA_M2]
    )
    assert round(float(without[0]), 1) != oracle.BARRON_EXAMPLE_3_3_SOUND_POWER_DB


def test_ver_beranek_absorption_area_and_its_decibel_term() -> None:
    """Ver and Beranek (2006) Example 4.2: a 200 m3 room at 21,4 C."""
    absorption = sabine_absorption_m2(
        oracle.VER_BERANEK_EXAMPLE_4_2_VOLUME_M3,
        oracle.VER_BERANEK_EXAMPLE_4_2_REVERBERATION_TIME_S,
        oracle.VER_BERANEK_EXAMPLE_4_2_SPEED_M_S,
    )
    assert round(absorption, 1) == oracle.VER_BERANEK_EXAMPLE_4_2_ABSORPTION_M2
    term = noise_control.sound_power_level_db([0.0], area_m2=[absorption])
    assert round(float(term[0]), 1) == oracle.VER_BERANEK_EXAMPLE_4_2_AREA_TERM_DB


def test_the_speed_of_sound_has_to_be_the_rooms_and_not_the_default() -> None:
    """The example is at 344 m/s, and ISO 11820 prints 340 for room temperature."""
    at_the_default = noise_control.reverberant_surface_area_m2(
        oracle.VER_BERANEK_EXAMPLE_4_2_VOLUME_M3,
        [oracle.VER_BERANEK_EXAMPLE_4_2_REVERBERATION_TIME_S],
    )
    assert round(SABINE_QUARTERS * float(at_the_default[0]), 1) != (
        oracle.VER_BERANEK_EXAMPLE_4_2_ABSORPTION_M2
    )


def test_barron_example_7_2_absorption_area() -> None:
    """A second room, a third speed of sound, and two independent routes to it.

    Barron reaches 40,41 m2 by the Eyring expression and 18,89 m2 by the
    Fitzroy relationship, then turns each into a reverberation time. Feeding
    the printed times back recovers the areas to within the rounding of the
    three figures he prints them to.
    """
    for time_s, printed in oracle.BARRON_EXAMPLE_7_2_ABSORPTION_M2.items():
        absorption = sabine_absorption_m2(
            oracle.BARRON_EXAMPLE_7_2_VOLUME_M3,
            time_s,
            oracle.BARRON_EXAMPLE_7_2_SPEED_M_S,
        )
        assert absorption == pytest.approx(printed, abs=0.03)


def test_barron_muffler_gas_densities() -> None:
    """Examples 8-11 and 8-10, both away from the default pressure of 100 kPa."""
    for (
        temperature_c,
        pressure_pa,
        printed,
    ) in oracle.BARRON_MUFFLER_GAS_DENSITY.values():
        density = noise_control.gas_density_kg_m3(
            temperature_c=temperature_c, ambient_pressure_pa=pressure_pa
        )
        assert round(density, 3) == printed


def test_ntp_668_flow_velocity_coefficients() -> None:
    """INSHT NTP 668 (2004) Ec. 2 and Ec. 3, one millimetre of water column."""
    for density_kg_m3, printed in oracle.NTP668_VELOCITY_COEFFICIENTS.values():
        velocity = noise_control.flow_velocity_m_s(
            [oracle.MILLIMETRE_WATER_COLUMN_PA], density_kg_m3
        )
        assert round(float(velocity[0]), 2) == printed


def test_vdi_2081_splitter_gap_velocity() -> None:
    """VDI 2081 Blatt 2:2005-05, Tabelle 1, element 2: 14,81 m/s in the gaps.

    Driven from the printed volume flow rather than from the printed face
    velocity of 4,94 m/s, which is itself rounded and gives 14,82 m/s.
    """
    face_velocity = (
        oracle.VDI2081_SPLITTER_VOLUME_FLOW_M3_H
        / 3600.0
        / oracle.VDI2081_SPLITTER_HOUSING_AREA_M2
    )
    assert round(face_velocity, 2) == 4.94
    velocity = noise_control.silencer_flow_velocity_m_s(
        face_velocity,
        upstream_area_m2=oracle.VDI2081_SPLITTER_HOUSING_AREA_M2,
        free_area_m2=oracle.VDI2081_SPLITTER_FREE_AREA_M2,
    )
    assert round(velocity, 2) == oracle.VDI2081_SPLITTER_GAP_VELOCITY_M_S


def test_fuchs_table_13_4_airway_velocities() -> None:
    """Twelve printed velocities, two splitter designs, three housing areas.

    The table truncates towards zero rather than rounding, which is visible
    where 66,67 m/s prints as 66 and 16,67 m/s as 16.
    """
    ratios = tuple(oracle.FUCHS_BLOCKAGE_RATIOS.values())
    for flow_m3_h, housing_m2, *velocities in oracle.FUCHS_TABLE_13_4:
        for printed, ratio in zip(velocities, ratios, strict=True):
            free_m2 = housing_m2 / (1.0 + ratio)
            velocity = noise_control.silencer_flow_velocity_m_s(
                flow_m3_h / 3600.0 / housing_m2,
                upstream_area_m2=housing_m2,
                free_area_m2=free_m2,
            )
            assert math.floor(velocity) == printed


def test_barron_example_5_7_equivalent_diameter() -> None:
    """The root inside Equation (15), for a 900 mm square duct.

    Half an oracle, and it says so: what Barron prints is the area-equivalent
    diameter sqrt(4 S / pi) = 1,016 m. The 1,5 diameters in front of it are
    ISO 11820's own coefficient, read on the printed page of Equation (15) and
    nowhere on his, so this pins the root and not the factor. The printed
    1,016 m carries half a millimetre of rounding, which the 1,5 scales to the
    0,75 mm this is asserted to.
    """
    distance = noise_control.measurement_distance_upstream_m(
        oracle.BARRON_EXAMPLE_5_7_AREA_M2
    )
    printed_upstream_diameters = 1.5
    expected = (
        printed_upstream_diameters * oracle.BARRON_EXAMPLE_5_7_EQUIVALENT_DIAMETER_M
    )
    assert distance == pytest.approx(expected, abs=printed_upstream_diameters * 5e-4)
    assert 0.9**2 == pytest.approx(oracle.BARRON_EXAMPLE_5_7_AREA_M2)
