#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the sound of artificial rain (ISO 10140-1:2021 Annex K).

With ISO 10140-5:2021 Annexes H (the artificial rain) and I (the reference
glass pane).

Oracles:

- Tables K.1, H.1, H.2 and I.1 cell by cell, typed from the printed pages.
- Table K.2: the 18 :math:`C_j` are the A-weighting of IEC 61672-1 at the
  exact base-ten midband frequencies, rounded to 0,1 dB (at the nominal
  centres five of them would round differently). The test recomputes that
  weighting from the closed form of IEC 61672-1:2013 Annex E (poles 20,6 Hz,
  107,7 Hz, 737,9 Hz and 12 194 Hz, normalised at 1 kHz), independently of the
  library.
- Formula (K.1) with a unit room, a 1 s decay and 1 m² excited: the intensity
  level is the pressure level minus 14 dB; and with V, T and Se away from one,
  every term of the formula.
- Table I.1 round trip, built from the page transcription: a pane whose loss
  factor is exactly the reference one and whose level is exactly the reference
  level needs no correction, and one with twice the loss factor 10 lg 2 dB.
- The printed tolerances of H.1 at their bounds, which they include, also
  when the rate or a drop reaches them through a division that rounds.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
import reference_data as ref

from phonometry import building
from phonometry.building.measurement.rainfall_sound import RainfallSoundResult

#: The 18 bands of Formula (K.2), 100 Hz to 5000 Hz.
_BANDS = [
    100.0,
    125.0,
    160.0,
    200.0,
    250.0,
    315.0,
    400.0,
    500.0,
    630.0,
    800.0,
    1000.0,
    1250.0,
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
]


def _iec_61672_a_weighting(frequency_hz: float) -> float:
    """A-weighting of IEC 61672-1:2013 Annex E, Formulas (E.1) to (E.6)."""
    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217

    def gain(f: float) -> float:
        return (f4**2 * f**4) / (
            (f**2 + f1**2) * math.sqrt((f**2 + f2**2) * (f**2 + f3**2)) * (f**2 + f4**2)
        )

    return 20.0 * math.log10(gain(frequency_hz) / gain(1000.0))


# --- The tables --------------------------------------------------------------


def test_table_k2_is_the_iec_61672_a_weighting() -> None:
    """Every C_j of Table K.2 is the A-weighting at the exact midband frequency."""
    for index, (band, value) in enumerate(building.RAINFALL_A_WEIGHTING.items()):
        exact = 10.0 ** ((20 + index) / 10.0)  # 100 Hz is band 20 of base ten
        assert band == _BANDS[index]
        assert round(_iec_61672_a_weighting(exact), 1) == pytest.approx(value), band


def test_table_i1_reads_as_printed() -> None:
    """All 36 cells of ISO 10140-5:2021 Table I.1."""
    loss = building.RAINFALL_REFERENCE_LOSS_FACTOR_DB
    level = building.RAINFALL_REFERENCE_INTENSITY_DB
    printed = ref.ISO10140_5_TABLE_I1
    assert tuple(loss.items()) == tuple((band, eta) for band, eta, _ in printed)
    assert tuple(level.items()) == tuple((band, lic) for band, _, lic in printed)
    assert tuple(loss) == tuple(_BANDS)


@pytest.mark.parametrize("rain", sorted(ref.ISO10140_5_TABLES_H1_H2))
def test_tables_h1_and_h2_read_as_printed(rain: str) -> None:
    """Every cell of ISO 10140-5:2021 Tables H.1 and H.2, and the H.1 tolerances."""
    row = building.ARTIFICIAL_RAIN[rain]
    cells = (
        row.rainfall_rate_mm_h,
        row.median_drop_diameter_mm,
        row.fall_velocity_m_s,
        row.hole_diameter_mm,
        row.holes_per_m2,
        row.fall_height_m,
    )
    tolerances = (
        row.rainfall_rate_tolerance_mm_h,
        row.drop_diameter_tolerance_mm,
        row.fall_velocity_tolerance_m_s,
    )
    assert cells == ref.ISO10140_5_TABLES_H1_H2[rain]
    assert tolerances == ref.ISO10140_5_H1_TOLERANCES


def test_table_k1_reads_as_printed() -> None:
    """Every cell of ISO 10140-1:2021 Table K.1, in its order."""
    classes = building.RAINFALL_CLASSIFICATION
    assert tuple(classes) == tuple(ref.ISO10140_1_TABLE_K1)
    for name, printed in ref.ISO10140_1_TABLE_K1.items():
        row = classes[name]
        got = (row.rainfall_rate_mm_h, row.drop_diameter_mm, row.fall_velocity_m_s)
        assert got == printed, name


def test_rain_tables_refuse_writes() -> None:
    weighting = building.RAINFALL_A_WEIGHTING
    with pytest.raises(TypeError, match=r"does not support item assignment"):
        weighting[100.0] = 0.0  # type: ignore[index]


# --- The generator -----------------------------------------------------------


def test_rainfall_rate_is_depth_per_hour() -> None:
    """4 litres over 0,1 m² in one hour is 40 mm of water, 40 mm/h."""
    assert building.rainfall_rate(4.0, 0.1, 3600.0) == pytest.approx(40.0)
    assert building.rainfall_rate(1.0, 0.1, 900.0) == pytest.approx(40.0)


@pytest.mark.parametrize(
    ("rate", "passes"), [(38.0, True), (42.0, True), (37.9, False), (42.1, False)]
)
def test_rate_tolerance_is_two_millimetres_per_hour(
    rate: float, *, passes: bool
) -> None:
    assert building.verify_rain_generator(rate).passes is passes


@pytest.mark.parametrize(
    ("litres", "area_m2", "rain_type", "passes"),
    [
        (3.8, 0.1, "heavy", True),  # 37,99999999999999 mm/h, on the bound
        (4.2, 0.1, "heavy", True),
        (3.79, 0.1, "heavy", False),
        (4.21, 0.1, "heavy", False),
        (1.3, 0.1, "intense", True),
        (1.7, 0.1, "intense", True),
        (1.29, 0.1, "intense", False),
    ],
)
def test_collected_rate_on_the_tolerance_bound_passes(
    litres: float, area_m2: float, rain_type: str, *, passes: bool
) -> None:
    """H.1 "within ±2 mm/h" includes its bound, however the rate was divided out.

    3,8 L on 0,1 m² in one hour is 38 mm/h, but the division leaves it a few
    units in the last place below 38, and a bare ``<=`` would fail it.
    """
    rate = building.rainfall_rate(litres, area_m2, 3600.0)
    check = building.verify_rain_generator(rate, rain_type=rain_type)
    assert check.rate_ok is passes
    assert check.passes is passes


def test_drop_windows_include_their_bounds() -> None:
    """Drops on the edge of the H.1 windows count as inside them.

    A drop timed over 0,6 m in 0,1 s falls at 6 m/s, 1 m/s below the heavy
    rain's 7 m/s, but the division gives 5,999999999999999; a drop whose
    shadow is 3,85 mm across at a magnification of 0,7 is 5,5 mm, and the
    division gives 5,500000000000001. The intense rain's 3 m/s and 1,5 mm come
    out of the same kind of division a hair outside as well.
    """
    heavy = building.verify_rain_generator(
        40.0,
        drop_diameters_mm=[3.85 / 0.7, 5.6],
        fall_velocities_m_s=[0.6 / 0.1, 8.2],
    )
    assert heavy.drop_share == pytest.approx(0.5)
    assert heavy.velocity_share == pytest.approx(0.5)
    assert heavy.passes
    intense = building.verify_rain_generator(
        15.0,
        rain_type="intense",
        drop_diameters_mm=[0.15 / 0.1, 2.6],
        fall_velocities_m_s=[0.3 / 0.1, 5.2],
    )
    assert intense.drop_share == pytest.approx(0.5)
    assert intense.velocity_share == pytest.approx(0.5)
    assert intense.passes


def test_drops_are_judged_by_the_share_inside_the_window() -> None:
    inside = np.full(6, 5.2)
    outside = np.full(4, 6.0)
    ok = building.verify_rain_generator(40.0, drop_diameters_mm=np.r_[inside, outside])
    assert ok.drop_share == pytest.approx(0.6)
    assert ok.drops_ok is True
    too_few = building.verify_rain_generator(
        40.0, drop_diameters_mm=np.r_[inside[:4], outside, outside[:2]]
    )
    assert too_few.drops_ok is False
    assert too_few.passes is False
    fast = building.verify_rain_generator(
        15.0, rain_type="intense", fall_velocities_m_s=[4.5, 4.9, 5.2]
    )
    assert fast.velocity_share == pytest.approx(2.0 / 3.0)
    assert fast.passes


def test_generator_verdict_has_no_truth_value() -> None:
    check = building.verify_rain_generator(40.0)
    with pytest.raises(TypeError, match=r"passes"):
        bool(check)


def test_unknown_rain_type_is_refused() -> None:
    with pytest.raises(ValueError, match=r"rain_type"):
        building.verify_rain_generator(40.0, rain_type="drizzle")


# --- The reference specimen --------------------------------------------------


#: The printed Table I.1: the bands, the linear ηref and LIc,ref, in band order.
_I1_BANDS = np.asarray([row[0] for row in ref.ISO10140_5_TABLE_I1])
_I1_ETA_REF = 10.0 ** (np.asarray([row[1] for row in ref.ISO10140_5_TABLE_I1]) / 10.0)
_I1_LEVEL = np.asarray([row[2] for row in ref.ISO10140_5_TABLE_I1])


def test_reference_pane_at_the_reference_needs_no_correction() -> None:
    t_s = 2.2 / (_I1_BANDS * _I1_ETA_REF)  # Formula (I.1) solved for Ts
    res = building.rainfall_reference_correction(_I1_LEVEL, t_s)
    np.testing.assert_allclose(res.loss_factor, _I1_ETA_REF, rtol=1e-12)
    np.testing.assert_allclose(res.reference_loss_factor, _I1_ETA_REF, rtol=1e-12)
    np.testing.assert_allclose(res.l_ic_ref_db, _I1_LEVEL)
    np.testing.assert_allclose(res.correction_db, 0.0, atol=1e-9)


def test_doubling_the_loss_factor_adds_three_decibels() -> None:
    """Formula (I.2): 10 lg(η/ηref) with η = 2 ηref."""
    t_s = 2.2 / (_I1_BANDS * 2.0 * _I1_ETA_REF)
    res = building.rainfall_reference_correction(_I1_LEVEL, t_s)
    np.testing.assert_allclose(res.correction_db, 10.0 * np.log10(2.0), rtol=1e-12)


def test_reference_correction_on_a_subset_of_bands() -> None:
    """At 500 Hz and 1 kHz the pane sits on LIc,ref, so only the loss factor moves it."""
    res = building.rainfall_reference_correction([47.0, 44.0], [0.5, 0.2], [500, 1000])
    eta = 2.2 / (np.array([500.0, 1000.0]) * np.array([0.5, 0.2]))
    eta_ref = 10.0 ** (np.array([-14.0, -16.0]) / 10.0)
    np.testing.assert_allclose(res.correction_db, 10.0 * np.log10(eta / eta_ref))


def test_correction_missing_a_measured_band_names_it() -> None:
    """A correction over five bands cannot normalize the sixth, which is a band."""
    t_s = 2.2 / (_I1_BANDS * _I1_ETA_REF)
    partial = building.rainfall_reference_correction(
        _I1_LEVEL[:5], t_s[:5], _I1_BANDS[:5]
    )
    levels = np.full(18, 60.0)
    with pytest.raises(ValueError, match=r"carries no value at 315 Hz; compute it"):
        building.rainfall_sound(
            levels,
            np.ones(18),
            _I1_BANDS,
            volume_m3=1.0,
            excited_area_m2=1.0,
            reference_correction=partial,
        )
    with pytest.raises(ValueError, match=r"carries no value at 315 Hz; compute it"):
        building.rainfall_sound_from_intensity(
            levels,
            _I1_BANDS,
            measuring_area_m2=1.0,
            excited_area_m2=1.0,
            reference_correction=partial,
        )


def test_correction_at_a_band_outside_table_i1_says_why() -> None:
    t_s = 2.2 / (_I1_BANDS * _I1_ETA_REF)
    full = building.rainfall_reference_correction(_I1_LEVEL, t_s, _I1_BANDS)
    with pytest.raises(ValueError, match=r"no value at 80 Hz, and Table I\.1 has none"):
        building.rainfall_sound(
            np.full(19, 60.0),
            np.ones(19),
            np.r_[80.0, _I1_BANDS],
            volume_m3=1.0,
            excited_area_m2=1.0,
            reference_correction=full,
        )


def test_band_outside_table_i1_is_refused() -> None:
    level = [47.0]
    t_s = [0.5]
    with pytest.raises(ValueError, match=r"Table I\.1"):
        building.rainfall_reference_correction(level, t_s, [63.0])


# --- The level ---------------------------------------------------------------


def test_formula_k1_in_a_unit_room() -> None:
    res = building.rainfall_sound(
        np.full(18, 60.0), np.ones(18), _BANDS, volume_m3=1.0, excited_area_m2=1.0
    )
    np.testing.assert_allclose(res.l_i_db, 46.0)
    assert res.method == "pressure"


def test_formula_k1_terms() -> None:
    """V = 100 m³, T = 2 s, Se = 4 m²: -10 lg 2 + 20 - 14 - 10 lg 4 = -3,03 dB."""
    res = building.rainfall_sound(
        np.full(18, 60.0),
        np.full(18, 2.0),
        _BANDS,
        volume_m3=100.0,
        excited_area_m2=4.0,
    )
    np.testing.assert_allclose(res.l_i_db, 60.0 + 6.0 - 10.0 * np.log10(8.0))


def test_three_generator_positions_add_energetically() -> None:
    one = building.rainfall_sound(
        np.full(18, 60.0), np.ones(18), _BANDS, volume_m3=1.0, excited_area_m2=1.0
    )
    three = building.rainfall_sound(
        np.full((3, 18), 60.0), np.ones(18), _BANDS, volume_m3=1.0, excited_area_m2=1.0
    )
    np.testing.assert_allclose(three.l_i_db - one.l_i_db, 10.0 * np.log10(3.0))


def test_formula_k2_weights_each_band() -> None:
    res = building.rainfall_sound(
        np.full(18, 60.0), np.ones(18), _BANDS, volume_m3=1.0, excited_area_m2=1.0
    )
    weights = np.fromiter(building.RAINFALL_A_WEIGHTING.values(), float)
    expected = 10.0 * np.log10(np.sum(10.0 ** ((46.0 + weights) / 10.0)))
    assert res.l_ia_db == pytest.approx(expected)


def test_no_a_weighted_level_without_the_18_bands() -> None:
    res = building.rainfall_sound(
        [60.0], [1.0], [1000.0], volume_m3=1.0, excited_area_m2=1.0
    )
    assert res.l_ia_db is None


def test_formula_k3_sums_three_bands() -> None:
    res = building.rainfall_sound(
        np.full(18, 60.0), np.ones(18), _BANDS, volume_m3=1.0, excited_area_m2=1.0
    )
    centres, octaves = res.octave_bands()
    assert centres.tolist() == [125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0]
    np.testing.assert_allclose(octaves, 46.0 + 10.0 * np.log10(3.0))


def test_background_is_removed_before_the_sum() -> None:
    background = np.full(18, 50.0)
    res = building.rainfall_sound(
        np.full(18, 60.0),
        np.ones(18),
        _BANDS,
        volume_m3=1.0,
        excited_area_m2=1.0,
        background_db=background,
    )
    corrected = 10.0 * np.log10(10.0**6.0 - 10.0**5.0)
    np.testing.assert_allclose(res.l_i_db, corrected - 14.0)


def test_normalization_formula_k5() -> None:
    correction = building.rainfall_reference_correction(
        np.full(18, 50.0), np.full(18, 0.3)
    )
    res = building.rainfall_sound(
        np.full(18, 60.0),
        np.ones(18),
        _BANDS,
        volume_m3=1.0,
        excited_area_m2=1.0,
        reference_correction=correction,
    )
    assert res.l_i_norm_db is not None
    np.testing.assert_allclose(res.l_i_norm_db, res.l_i_db - correction.correction_db)
    as_array = building.rainfall_sound(
        np.full(18, 60.0),
        np.ones(18),
        _BANDS,
        volume_m3=1.0,
        excited_area_m2=1.0,
        reference_correction=correction.correction_db,
    )
    assert as_array.l_ia_norm_db == pytest.approx(res.l_ia_norm_db)
    _, octaves = res.octave_bands(normalized=True)
    assert octaves.size == 6


def test_octaves_of_levels_never_normalized_are_refused() -> None:
    res = building.rainfall_sound(
        np.full(18, 60.0), np.ones(18), _BANDS, volume_m3=1.0, excited_area_m2=1.0
    )
    with pytest.raises(ValueError, match=r"LInorm"):
        res.octave_bands(normalized=True)


def test_sound_power_of_the_whole_specimen() -> None:
    res = building.rainfall_sound(
        np.full(18, 60.0), np.ones(18), _BANDS, volume_m3=1.0, excited_area_m2=1.0
    )
    np.testing.assert_allclose(res.sound_power_levels(10.0), 56.0)


def test_formula_k4_direct_intensity() -> None:
    res = building.rainfall_sound_from_intensity(
        np.full(18, 50.0), _BANDS, measuring_area_m2=4.0, excited_area_m2=1.0
    )
    np.testing.assert_allclose(res.l_i_db, 50.0 + 10.0 * np.log10(4.0))
    assert res.method == "intensity"


def test_rainfall_sound_refuses_mismatched_bands() -> None:
    levels = np.full(18, 60.0)
    times = np.ones(17)
    with pytest.raises(ValueError, match=r"rainfall_sound"):
        building.rainfall_sound(
            levels, times, _BANDS, volume_m3=1.0, excited_area_m2=1.0
        )


def test_result_refuses_an_unknown_method() -> None:
    band = np.array([1000.0])
    level = np.array([40.0])
    with pytest.raises(ValueError, match=r"method"):
        RainfallSoundResult(
            frequencies_hz=band, l_i_db=level, l_ia_db=None, method="guess"
        )


# --- Figures -----------------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "es"])
def test_every_rain_result_plots(language: str) -> None:
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    correction = building.rainfall_reference_correction(
        np.full(18, 48.0), np.full(18, 0.4)
    )
    sound = building.rainfall_sound(
        np.full(18, 62.0),
        np.ones(18),
        _BANDS,
        volume_m3=90.0,
        excited_area_m2=1.875,
        reference_correction=correction,
    )
    generator = building.verify_rain_generator(
        41.0, drop_diameters_mm=np.linspace(4.2, 5.8, 20)
    )
    for result in (correction, sound, generator):
        ax = result.plot(language=language)
        assert ax.get_title()
        plt.close(ax.figure)


def _line(ax: object, label: str) -> np.ndarray:
    lines = [line for line in ax.get_lines() if line.get_label() == label]  # type: ignore[attr-defined]
    assert len(lines) == 1, label
    return np.asarray(lines[0].get_ydata(), dtype=float)


def test_rain_figure_draws_the_measured_and_normalized_levels() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    correction = np.linspace(-1.0, 2.0, 18)
    sound = building.rainfall_sound(
        np.linspace(50.0, 60.0, 18),
        np.ones(18),
        _BANDS,
        volume_m3=90.0,
        excited_area_m2=1.875,
        reference_correction=correction,
    )
    ax = sound.plot()
    assert sound.l_i_norm_db is not None
    np.testing.assert_allclose(_line(ax, r"$L_I$"), sound.l_i_db)
    np.testing.assert_allclose(
        _line(ax, r"$L_{I\mathrm{norm}}$ (normalized)"), sound.l_i_norm_db
    )
    assert sound.l_ia_db is not None
    assert f"= {round(sound.l_ia_db, 1)} dB" in ax.get_title()
    plt.close(ax.figure)


def test_reference_figure_draws_the_corrected_level_against_table_i1() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib.pyplot as plt

    res = building.rainfall_reference_correction(
        _I1_LEVEL + 1.0, 2.2 / (_I1_BANDS * 2.0 * _I1_ETA_REF)
    )
    ax = res.plot()
    np.testing.assert_allclose(_line(ax, r"$L_{I,\mathrm{m,ref}}$"), res.l_i_m_ref_db)
    np.testing.assert_allclose(
        _line(ax, r"$L_{I\mathrm{c,ref}}$ (Table I.1)"), _I1_LEVEL
    )
    plt.close(ax.figure)
