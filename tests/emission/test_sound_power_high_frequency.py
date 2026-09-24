#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Sound power levels in the 16 kHz octave band: ISO 9295:2015.

Normative anchors (UNE-EN ISO 9295:2015, the Spanish adoption):
- Formula (1), PDF page 11: the energy mean over N orientations or revolutions.
- Formula (2), PDF page 11: Delta f = 2 f v / c; Formula (3), PDF page 12: the
  energy sum of the sidebands.
- Formulae (4) and (5), PDF page 13: R = S alpha_room / (1 - alpha_room),
  alpha_room = 1 - exp(-0,16 V / (S T)).
- Formula (6), PDF page 13: LW = Lp(ST) - 10 lg(4/R) dB.
- Formula (7), PDF page 14: R = 8 alpha V / (1 - 8 alpha V / S), alpha in Np/m.
- Tables 1 and 2, PDF pages 15 and 16: alpha in Np/m, 10 000 Hz to 22 400 Hz,
  18 degC to 27 degC, 40 %, 50 %, 60 %, the oracle of Annex A.
- Formulae (8) and (9), PDF pages 17 and 18: LW = LW(FAR) - Lp(FAR) + Lp(ST)
  (+ 10 lg(Delta F / 1 Hz) for tones, Delta F <= 112 Hz for an FFT).
- Formula (10), PDF page 21: K = r alpha (alpha in dB/m) when r > 2 m.
- Clause 10.1, PDF page 21: reference meteorological conditions per ISO 3741,
  C1 + C2 for a direct method and C2 for the comparison.
- Annex A, PDF pages 25 and 26: ISO 9613-1 in Np/m (8,686 converts to dB/m).
"""

from __future__ import annotations

import math
import warnings

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
import reference_data as ref

from phonometry import emission
from phonometry.environment.propagation import air_attenuation
from phonometry.environment.propagation.air_absorption import (
    AtmosphericAbsorptionWarning,
    _pure_tone_terms,
)

THIRDS = np.array([12500.0, 16000.0, 20000.0])


def _printed_cells() -> list[tuple[int, float, float, float, float]]:
    """Every printed cell: (table, Hz, degC, %, alpha as printed)."""
    cells = []
    for table, rows, temperatures in (
        (1, ref.ISO9295_TABLE_1_NP_PER_M, ref.ISO9295_TABLE_1_TEMPERATURES_C),
        (2, ref.ISO9295_TABLE_2_NP_PER_M, ref.ISO9295_TABLE_2_TEMPERATURES_C),
    ):
        for frequency, row in zip(ref.ISO9295_FREQUENCIES_HZ, rows, strict=True):
            columns = [
                (t, rh) for t in temperatures for rh in ref.ISO9295_HUMIDITIES_PERCENT
            ]
            for (t, rh), printed in zip(columns, row, strict=True):
                cells.append((table, frequency, t, rh, printed))
    return cells


def _annex_a_at(frequency: float, temperature_k: float, humidity: float) -> float:
    """Annex A in Np/m at a temperature already in kelvins."""
    f2, bracket = _pure_tone_terms(
        np.asarray([frequency]), temperature_k, humidity, 101.325
    )
    return float((f2 * bracket)[0])


CELLS = _printed_cells()
CORRECT = [c for c in CELLS if c[:4] not in ref.ISO9295_MISPRINTED_CELLS]


# --- Annex A against Tables 1 and 2 -----------------------------------------


def test_the_transcription_holds_624_cells_of_which_43_are_misprinted() -> None:
    assert len(CELLS) == 624
    assert len(ref.ISO9295_MISPRINTED_CELLS) == ref.ISO9295_MISPRINT_COUNT == 43
    assert len(CORRECT) == 581


def test_annex_a_at_the_tables_conversion_rounds_to_every_correct_cell() -> None:
    """The tables are Annex A rounded to four decimals, with T = theta + 273,16 K."""
    offset = ref.ISO9295_TABLE_KELVIN_OFFSET
    wrong = [
        cell
        for cell in CORRECT
        if round(_annex_a_at(cell[1], cell[2] + offset, cell[3]), 4) != cell[4]
    ]
    assert wrong == []


@pytest.mark.parametrize("offset", [273.15, 273.155, 273.165, 273.17])
def test_no_other_conversion_reproduces_the_correct_cells(offset: float) -> None:
    """The 0,01 K is what the tables carry: a neighbour of 273,16 leaves cells off."""
    wrong = sum(
        1
        for cell in CORRECT
        if round(_annex_a_at(cell[1], cell[2] + offset, cell[3]), 4) != cell[4]
    )
    assert wrong > 0


def test_the_library_conversion_is_within_rounding_and_the_offset() -> None:
    """At theta + 273,15 K each correct cell is within half a unit plus the 0,01 K."""
    offset = ref.ISO9295_TABLE_KELVIN_OFFSET
    worst = 0.0
    for _, frequency, t, rh, printed in CORRECT:
        library = float(
            emission.air_absorption_np_per_m(
                frequency, temperature_c=t, relative_humidity_percent=rh
            )
        )
        shift = abs(library - _annex_a_at(frequency, t + offset, rh))
        assert abs(library - printed) <= 0.5e-4 + shift + 1e-12
        worst = max(worst, abs(library - printed))
    assert worst < 1e-4


def test_the_library_rounds_to_the_print_in_520_of_the_correct_cells() -> None:
    matching = sum(
        1
        for _, frequency, t, rh, printed in CORRECT
        if round(
            float(
                emission.air_absorption_np_per_m(
                    frequency, temperature_c=t, relative_humidity_percent=rh
                )
            ),
            4,
        )
        == printed
    )
    assert matching == 520


@pytest.mark.parametrize(
    ("cell", "entry"), sorted(ref.ISO9295_MISPRINTED_CELLS.items())
)
def test_each_misprinted_cell_is_a_zero_the_print_lost(
    cell: tuple[int, float, float, float], entry: tuple[str, float]
) -> None:
    table, frequency, t, rh = cell
    printed_text, correct = entry
    printed = next(c[4] for c in CELLS if c[:4] == cell)
    assert printed == float(printed_text.replace(" ", "").replace(",", "."))
    offset = ref.ISO9295_TABLE_KELVIN_OFFSET
    assert round(_annex_a_at(frequency, t + offset, rh), 4) == correct
    assert round(correct * 1e4) % 10 == 0
    assert printed != correct
    # The library evaluates the same cell within a unit of the corrected value.
    library = float(
        emission.air_absorption_np_per_m(
            frequency, temperature_c=t, relative_humidity_percent=rh
        )
    )
    assert abs(library - correct) < 1e-4
    assert table in (1, 2)


def test_forty_of_the_misprints_repeat_the_digit_before_the_lost_zero() -> None:
    repeated = 0
    for printed_text, correct in ref.ISO9295_MISPRINTED_CELLS.values():
        digits = printed_text.replace(" ", "").replace(",", "")
        right = f"{correct:.4f}".replace(".", "")
        if digits[:-1] == right[:-1] and digits[-1] == right[-2]:
            repeated += 1
    assert repeated == 40


def test_every_cell_whose_fourth_decimal_is_zero_is_counted() -> None:
    """The 43 are 43 of the 60 cells whose Annex A value ends in 0."""
    offset = ref.ISO9295_TABLE_KELVIN_OFFSET
    zeros = [
        cell
        for cell in CELLS
        if round(round(_annex_a_at(cell[1], cell[2] + offset, cell[3]), 4) * 1e4) % 10
        == 0
    ]
    assert len(zeros) == 60
    assert sum(1 for cell in zeros if cell[:4] in ref.ISO9295_MISPRINTED_CELLS) == 43


# --- Annex A: the range and the unit -----------------------------------------


def test_annex_a_is_iso_9613_1_in_nepers() -> None:
    frequencies = np.array([1000.0, 4000.0, 8000.0])
    nepers = emission.air_absorption_np_per_m(
        frequencies, temperature_c=20.0, relative_humidity_percent=50.0
    )
    decibels = air_attenuation(frequencies)
    np.testing.assert_allclose(8.686 * nepers, decibels, rtol=1e-14)


def test_annex_a_raises_no_advisory_up_to_22_4_khz() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        emission.air_absorption_np_per_m(
            [10_000.0, 16_000.0, 22_400.0],
            temperature_c=23.0,
            relative_humidity_percent=50.0,
        )


def test_annex_a_advises_above_the_octave() -> None:
    with pytest.warns(AtmosphericAbsorptionWarning, match="ISO 9295:2015 Annex A"):
        emission.air_absorption_np_per_m(
            30_000.0, temperature_c=23.0, relative_humidity_percent=50.0
        )


def test_iso_9613_1_itself_still_advises_above_10_khz() -> None:
    with pytest.warns(AtmosphericAbsorptionWarning, match="tabulated range"):
        air_attenuation(16_000.0)


def test_annex_a_refuses_a_humidity_above_saturation() -> None:
    with pytest.raises(ValueError, match="relative_humidity_percent"):
        emission.air_absorption_np_per_m(
            16_000.0, temperature_c=23.0, relative_humidity_percent=120.0
        )


# --- Formulae (4), (5) and (7): the room constant -----------------------------


def test_eyring_coefficient_closes_on_e() -> None:
    # 0,16 V / (S T) = 1 when V = S and T = 0,16 s.
    alpha = emission.room_absorption_coefficient(
        0.16, volume_m3=200.0, surface_area_m2=200.0
    )
    assert float(alpha[0]) == pytest.approx(1.0 - math.exp(-1.0), rel=1e-15)


def test_room_constant_from_reverberation_time_is_formula_4() -> None:
    room = emission.room_constant_from_reverberation_time(
        0.16, volume_m3=200.0, surface_area_m2=200.0
    )
    assert float(room[0]) == pytest.approx(200.0 * (math.e - 1.0), rel=1e-14)


def test_room_constant_is_per_band() -> None:
    room = emission.room_constant_from_reverberation_time(
        [1.2, 1.0, 0.8], volume_m3=200.0, surface_area_m2=210.0
    )
    assert room.shape == (3,)
    assert np.all(np.diff(room) > 0.0)  # shorter T, more absorption


def test_room_constant_refuses_a_zero_reverberation_time() -> None:
    with pytest.raises(ValueError, match="reverberation_time_s"):
        emission.room_constant_from_reverberation_time(
            0.0, volume_m3=200.0, surface_area_m2=210.0
        )


def test_room_constant_refuses_a_zero_volume() -> None:
    with pytest.raises(ValueError, match="volume_m3"):
        emission.room_constant_from_reverberation_time(
            1.0, volume_m3=0.0, surface_area_m2=210.0
        )


def test_room_constant_from_air_absorption_is_formula_7() -> None:
    volume, surface = 200.0, 210.0
    room = emission.room_constant_from_air_absorption(
        THIRDS,
        volume_m3=volume,
        surface_area_m2=surface,
        temperature_c=23.0,
        relative_humidity_percent=50.0,
    )
    alpha = emission.air_absorption_np_per_m(
        THIRDS, temperature_c=23.0, relative_humidity_percent=50.0
    )
    expected = 8.0 * alpha * volume / (1.0 - 8.0 * alpha * volume / surface)
    np.testing.assert_allclose(room, expected, rtol=1e-14)


def test_formula_7_is_formula_4_with_the_air_as_the_only_absorber() -> None:
    """8 alpha V is the air absorption area, so alpha_room = 8 alpha V / S."""
    volume, surface = 200.0, 210.0
    alpha = emission.air_absorption_np_per_m(
        THIRDS, temperature_c=23.0, relative_humidity_percent=50.0
    )
    mean = 8.0 * alpha * volume / surface
    room = emission.room_constant_from_air_absorption(
        THIRDS,
        volume_m3=volume,
        surface_area_m2=surface,
        temperature_c=23.0,
        relative_humidity_percent=50.0,
    )
    np.testing.assert_allclose(room, surface * mean / (1.0 - mean), rtol=1e-14)


def test_formula_7_refuses_a_room_the_air_alone_would_saturate() -> None:
    with pytest.raises(ValueError, match="Formula \\(7\\)"):
        emission.room_constant_from_air_absorption(
            [20_000.0],
            volume_m3=2000.0,
            surface_area_m2=100.0,
            temperature_c=23.0,
            relative_humidity_percent=50.0,
        )


def test_formula_7_advises_below_10_khz() -> None:
    with pytest.warns(emission.SoundPowerWarning, match="below 10 kHz"):
        emission.room_constant_from_air_absorption(
            [8_000.0],
            volume_m3=200.0,
            surface_area_m2=210.0,
            temperature_c=23.0,
            relative_humidity_percent=50.0,
        )


# --- Formula (6): the direct method -------------------------------------------


def test_formula_6_at_r_equal_4_is_the_mean_level_plus_c1_c2() -> None:
    res = emission.high_frequency_sound_power(
        [60.0, 58.0, 55.0], frequencies_hz=THIRDS, room_constant_m2=4.0
    )
    c1 = 5.0 * math.log10(296.15 / 314.0)
    c2 = 15.0 * math.log10(296.15 / 296.0)
    np.testing.assert_allclose(
        res.sound_power_level, np.array([60.0, 58.0, 55.0]) + c1 + c2, atol=1e-12
    )
    assert res.c1 == pytest.approx(c1, abs=1e-12)
    assert res.c2 == pytest.approx(c2, abs=1e-12)
    assert res.method == "direct"


def test_formula_6_adds_ten_lg_of_r_over_4() -> None:
    res = emission.high_frequency_sound_power(
        [60.0, 60.0, 60.0], frequencies_hz=THIRDS, room_constant_m2=[4.0, 40.0, 400.0]
    )
    steps = np.diff(res.sound_power_level)
    np.testing.assert_allclose(steps, [10.0, 10.0], atol=1e-12)


def test_formula_1_averages_the_orientations_on_an_energy_basis() -> None:
    orientations = np.array([[60.0, 50.0, 40.0], [60.0, 50.0, 40.0]])
    orientations[1] += 10.0 * math.log10(3.0)  # twice the energy plus one
    res = emission.high_frequency_sound_power(
        orientations, frequencies_hz=THIRDS, room_constant_m2=4.0
    )
    np.testing.assert_allclose(
        res.mean_pressure_level, np.array([63.0103, 53.0103, 43.0103]), atol=1e-4
    )


def test_direct_method_refuses_a_non_positive_room_constant() -> None:
    with pytest.raises(ValueError, match="room_constant_m2"):
        emission.high_frequency_sound_power(
            [60.0, 58.0, 55.0], frequencies_hz=THIRDS, room_constant_m2=[4.0, 0.0, 4.0]
        )


def test_direct_method_refuses_frequencies_of_another_length() -> None:
    with pytest.raises(ValueError, match="frequencies_hz"):
        emission.high_frequency_sound_power(
            [60.0, 58.0, 55.0], frequencies_hz=[16_000.0], room_constant_m2=4.0
        )


def test_direct_method_advises_outside_the_octave() -> None:
    with pytest.warns(emission.SoundPowerWarning, match="16 kHz octave band"):
        emission.high_frequency_sound_power(
            [60.0], frequencies_hz=[8_000.0], room_constant_m2=4.0
        )


def test_the_whole_chain_reproduces_formulae_6_and_7_by_hand() -> None:
    volume, surface = 200.0, 210.0
    alpha = emission.air_absorption_np_per_m(
        THIRDS, temperature_c=23.0, relative_humidity_percent=50.0
    )
    room = 8.0 * alpha * volume / (1.0 - 8.0 * alpha * volume / surface)
    levels = np.array([62.0, 60.0, 55.0])
    res = emission.high_frequency_sound_power(
        levels,
        frequencies_hz=THIRDS,
        room_constant_m2=emission.room_constant_from_air_absorption(
            THIRDS,
            volume_m3=volume,
            surface_area_m2=surface,
            temperature_c=23.0,
            relative_humidity_percent=50.0,
        ),
    )
    expected = levels - 10.0 * np.log10(4.0 / room) + res.c1 + res.c2
    np.testing.assert_allclose(res.sound_power_level, expected, atol=1e-12)


# --- Formulae (8) and (9): the comparison with a reference source -------------


def test_formula_8_moves_the_reference_power_by_the_level_difference() -> None:
    res = emission.high_frequency_sound_power_comparison(
        [60.0, 58.0, 55.0],
        frequencies_hz=THIRDS,
        reference_pressure_levels_db=[70.0, 69.0, 66.0],
        reference_sound_power_levels_db=[80.0, 79.0, 76.0],
    )
    c2 = 15.0 * math.log10(296.15 / 296.0)
    np.testing.assert_allclose(
        res.sound_power_level, np.array([70.0, 68.0, 65.0]) + c2, atol=1e-12
    )
    assert math.isnan(res.c1)
    assert res.method == "comparison"
    assert not res.tonal


def test_formula_9_adds_the_noise_bandwidth() -> None:
    broad = emission.high_frequency_sound_power_comparison(
        [55.0], frequencies_hz=[16_000.0],
        reference_pressure_levels_db=[45.0], reference_sound_power_levels_db=[50.0],
    )  # fmt: skip
    tonal = emission.high_frequency_sound_power_comparison(
        [55.0], frequencies_hz=[16_000.0],
        reference_pressure_levels_db=[45.0], reference_sound_power_levels_db=[50.0],
        noise_bandwidth_hz=10.0,
    )  # fmt: skip
    assert float(tonal.sound_power_level[0] - broad.sound_power_level[0]) == (
        pytest.approx(10.0, abs=1e-12)
    )
    assert tonal.tonal
    assert tonal.noise_bandwidth_hz == 10.0


def test_formula_9_advises_an_fft_wider_than_112_hz() -> None:
    with pytest.warns(emission.SoundPowerWarning, match="112 Hz"):
        emission.high_frequency_sound_power_comparison(
            [55.0], frequencies_hz=[16_000.0],
            reference_pressure_levels_db=[45.0], reference_sound_power_levels_db=[50.0],
            noise_bandwidth_hz=200.0,
        )  # fmt: skip


def test_comparison_refuses_reference_levels_of_another_length() -> None:
    with pytest.raises(ValueError, match="reference_pressure_levels_db"):
        emission.high_frequency_sound_power_comparison(
            [60.0, 58.0, 55.0], frequencies_hz=THIRDS,
            reference_pressure_levels_db=[70.0, 69.0],
            reference_sound_power_levels_db=80.0,
        )  # fmt: skip


# --- Formulae (2), (3) and (10) ------------------------------------------------


def test_formula_2_minimum_bandwidth() -> None:
    bandwidth = emission.minimum_analyzer_bandwidth_hz(
        16_000.0, microphone_speed_m_s=0.4, speed_of_sound=345.0
    )
    assert float(bandwidth[0]) == pytest.approx(2.0 * 16_000.0 * 0.4 / 345.0)


def test_formula_3_sums_equal_sidebands() -> None:
    total = emission.tone_level_from_sidebands([50.0, 50.0, 50.0])
    assert total == pytest.approx(50.0 + 10.0 * math.log10(3.0), abs=1e-12)


def test_formula_10_is_r_times_alpha_in_decibels() -> None:
    k = emission.free_field_absorption_correction(
        THIRDS, radius_m=4.0, temperature_c=23.0, relative_humidity_percent=50.0
    )
    alpha = emission.air_absorption_np_per_m(
        THIRDS, temperature_c=23.0, relative_humidity_percent=50.0
    )
    np.testing.assert_allclose(k, 4.0 * 8.686 * alpha, rtol=1e-15)


def test_formula_10_applies_only_beyond_2_m() -> None:
    k = emission.free_field_absorption_correction(
        THIRDS, radius_m=2.0, temperature_c=23.0, relative_humidity_percent=50.0
    )
    np.testing.assert_array_equal(k, np.zeros(3))


# --- The result ------------------------------------------------------------------


def _tones() -> emission.HighFrequencySoundPowerResult:
    return emission.high_frequency_sound_power_comparison(
        [55.0, 48.0, 40.0],
        frequencies_hz=[15_625.0, 17_000.0, 20_500.0],
        reference_pressure_levels_db=[45.0, 44.0, 43.0],
        reference_sound_power_levels_db=[50.0, 49.5, 49.0],
        noise_bandwidth_hz=12.5,
    )


def test_the_tones_within_10_db_of_the_highest_are_marked() -> None:
    np.testing.assert_array_equal(_tones().within_10_db_of_maximum, [True, True, False])


def test_a_result_with_disagreeing_bands_cannot_be_built() -> None:
    good = _tones()
    fields = {**good.__dict__, "mean_pressure_level": np.array([1.0, 2.0])}
    with pytest.raises(ValueError, match="mean_pressure_level"):
        emission.HighFrequencySoundPowerResult(**fields)


def test_a_result_names_its_method() -> None:
    fields = {**_tones().__dict__, "method": "semi-anechoic"}
    with pytest.raises(ValueError, match="method"):
        emission.HighFrequencySoundPowerResult(**fields)


@pytest.mark.parametrize("language", ["en", "es"])
def test_broadband_plot_draws_one_bar_per_third(language: str) -> None:
    res = emission.high_frequency_sound_power(
        [62.0, 60.0, 55.0], frequencies_hz=THIRDS, room_constant_m2=40.0
    )
    ax = res.plot(language=language)
    assert len(ax.patches) == 3
    heights = sorted(p.get_height() for p in ax.patches)
    np.testing.assert_allclose(heights, sorted(res.sound_power_level))
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
def test_tonal_plot_draws_the_reporting_line(language: str) -> None:
    res = _tones()
    ax = res.plot(language=language)
    threshold = float(np.max(res.sound_power_level)) - 10.0
    horizontal = [line for line in ax.lines if np.allclose(line.get_ydata(), threshold)]
    assert horizontal, "the line 10 dB below the highest tone is missing"
    assert "kHz" in ax.get_xlabel()
    plt.close("all")
