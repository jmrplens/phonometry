#  Copyright (c) 2026. Jose Manuel Requena Plens
"""IEC 60268-7:2010: the characteristics of headphones and earphones that are computations."""

from __future__ import annotations

import dataclasses
import math
from types import MappingProxyType

import numpy as np
import pytest
import reference_data as ref

import phonometry as ph

ea = ph.electroacoustics

FS = 48000

#: One-third-octave centres from 100 Hz to 10 kHz, with 500 Hz among them.
BANDS = np.array(
    [100.0, 125.0, 160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0]
    + [1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0, 8000.0]
    + [10000.0]
)


# ---------------------------------------------------------------------------
# Clause 4: the code
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(("impedance", "code"), ref.IEC60268_7_IMPEDANCE_CODES.items())
def test_impedance_code_reproduces_the_printed_examples(
    impedance: float, code: str
) -> None:
    assert ea.impedance_code(impedance) == code


@pytest.mark.parametrize(
    ("impedance", "code"),
    [(150.0, "15R1"), (300.0, "03R2"), (1000.0, "01R3"), (47.0, "47R0")],
)
def test_impedance_code_gives_every_trailing_zero_to_the_exponent(
    impedance: float, code: str
) -> None:
    assert ea.impedance_code(impedance) == code


@pytest.mark.parametrize(
    ("impedance", "reason"), [(4.7, "whole number of ohms"), (123.0, "NNRN form")]
)
def test_impedance_code_refuses_what_the_form_cannot_hold(
    impedance: float, reason: str
) -> None:
    with pytest.raises(ValueError, match=reason):
        ea.impedance_code(impedance)


def test_impedance_code_holds_470_ohm_as_47_r1() -> None:
    assert ea.impedance_code(470.0) == "47R1"


def test_classification_writes_and_reads_its_code() -> None:
    classification = ea.HeadphoneClassification("D", "C", "S", "C", 32.0, 2)
    assert classification.code == "60268-7-IEC-DCSC-32R0-2"
    assert ea.parse_classification_code(classification.code) == classification
    assert classification.description.startswith("electrodynamic (moving coil)")


def test_parse_reads_the_clause_layout_with_spaces() -> None:
    parsed = ea.parse_classification_code("60268-7 - IEC - MESO - 06R2 - 1")
    assert parsed.impedance_ohm == 600.0
    assert parsed.earphone_type == "E"
    assert parsed.channels == 1


def test_parse_refuses_another_form() -> None:
    with pytest.raises(ValueError, match="60268-7-IEC-XXXX-NNRN-N"):
        ea.parse_classification_code("60268-7-IEC-DCSC-32-2")


def test_parse_refuses_a_long_run_of_spaces_quickly() -> None:
    # A hundred thousand spaces with no hyphen after them: a pattern that
    # backtracks over the run would take quadratic time here.
    code = "60268-7-IEC-DCSC-32R0-2" + " " * 100_000 + "x"
    with pytest.raises(ValueError, match="60268-7-IEC-XXXX-NNRN-N"):
        ea.parse_classification_code(code)
    spaced = "60268-7" + " " * 100_000 + "-IEC-DCSC-32R0-2"
    assert ea.parse_classification_code(spaced).impedance_ohm == 32.0


def test_classification_refuses_an_unknown_letter() -> None:
    with pytest.raises(ValueError, match="earphone_type"):
        ea.HeadphoneClassification("D", "X", "S", "C", 32.0, 2)


def test_classification_refuses_ten_channels() -> None:
    with pytest.raises(ValueError, match="channels"):
        ea.HeadphoneClassification("D", "C", "S", "C", 32.0, 10)


def test_code_letters_are_published_read_only() -> None:
    for table in (
        ea.TRANSDUCER_PRINCIPLES,
        ea.EARPHONE_TYPES,
        ea.ACOUSTIC_COUPLINGS,
        ea.BACK_RADIATIONS,
    ):
        assert isinstance(table, MappingProxyType)
    assert sorted(ea.TRANSDUCER_PRINCIPLES) == ["D", "E", "F", "M", "P", "S"]
    assert sorted(ea.EARPHONE_TYPES) == ["C", "E", "H", "I", "M", "S", "T"]


# ---------------------------------------------------------------------------
# 8.2: impedance
# ---------------------------------------------------------------------------


def _impedance(minimum: float) -> tuple[np.ndarray, np.ndarray]:
    f = np.geomspace(10.0, 30000.0, 200)
    z = 40.0 + 20.0 * np.exp(-((np.log10(f / 80.0)) ** 2) / 0.02)
    z[100] = minimum
    return f, z


def test_rated_impedance_passes_at_exactly_80_percent() -> None:
    f, z = _impedance(25.6)
    verdict = ea.verify_rated_impedance(
        f, z, rated_impedance_ohm=32.0, rated_frequency_range_hz=(20.0, 20000.0)
    )
    assert verdict.minimum_ohm == 25.6
    assert verdict.minimum_ratio == pytest.approx(
        ref.IEC60268_7_RATED_IMPEDANCE_FRACTION
    )
    assert verdict.passes
    assert verdict.frequencies_to_state_hz.size == 0


def test_rated_impedance_fails_below_80_percent() -> None:
    f, z = _impedance(25.0)
    verdict = ea.verify_rated_impedance(
        f, z, rated_impedance_ohm=32.0, rated_frequency_range_hz=(20.0, 20000.0)
    )
    assert not verdict.passes
    assert verdict.minimum_frequency_hz == float(f[100])
    np.testing.assert_array_equal(verdict.frequencies_to_state_hz, [f[100]])


def test_a_dip_outside_the_rated_range_is_listed_but_not_judged() -> None:
    f, z = _impedance(40.0)
    z[5] = 20.0  # below 20 Hz, outside a rated range starting at 50 Hz
    z[195] = 20.0  # above 20 kHz, beyond the "0 kHz and 20 kHz" of 8.2.1 b)
    assert f[195] > ref.IEC60268_7_IMPEDANCE_RANGE_HZ[1]
    verdict = ea.verify_rated_impedance(
        f, z, rated_impedance_ohm=32.0, rated_frequency_range_hz=(50.0, 15000.0)
    )
    assert verdict.passes
    np.testing.assert_array_equal(verdict.frequencies_to_state_hz, [f[5]])


def test_the_modulus_of_a_complex_impedance_is_taken() -> None:
    f = np.array([20.0, 1000.0, 20000.0])
    verdict = ea.verify_rated_impedance(
        f,
        [30.0 + 40.0j, 50.0, 60.0],
        rated_impedance_ohm=50.0,
        rated_frequency_range_hz=(20.0, 20000.0),
    )
    np.testing.assert_allclose(verdict.impedance_ohm, [50.0, 50.0, 60.0])
    assert verdict.covers_measurement_range


def test_a_measurement_short_of_20_khz_does_not_cover_the_range() -> None:
    f = np.array([20.0, 1000.0, 16000.0])
    verdict = ea.verify_rated_impedance(
        f,
        [32.0, 32.0, 32.0],
        rated_impedance_ohm=32.0,
        rated_frequency_range_hz=(20.0, 16000.0),
    )
    assert not verdict.covers_measurement_range


def test_rated_impedance_needs_a_point_in_the_rated_range() -> None:
    f = np.array([10.0, 15.0])
    z = np.array([32.0, 32.0])
    with pytest.raises(ValueError, match="rated frequency range"):
        ea.verify_rated_impedance(
            f, z, rated_impedance_ohm=32.0, rated_frequency_range_hz=(20.0, 20000.0)
        )


def test_rated_impedance_verdict_has_no_truth_value() -> None:
    f, z = _impedance(30.0)
    verdict = ea.verify_rated_impedance(
        f, z, rated_impedance_ohm=32.0, rated_frequency_range_hz=(20.0, 20000.0)
    )
    with pytest.raises(TypeError, match="passes"):
        bool(verdict)


# ---------------------------------------------------------------------------
# 8.3 to 8.5: voltages, powers and levels
# ---------------------------------------------------------------------------


def test_characteristic_voltage_scales_a_reading_to_94_db() -> None:
    voltage = ea.characteristic_voltage(0.1, 100.0)
    assert voltage == pytest.approx(0.1 * 10.0 ** (-6.0 / 20.0), rel=1e-12)
    assert ea.characteristic_voltage(0.25, ref.IEC60268_7_STANDARD_LEVEL_DB) == 0.25


def test_input_power_and_source_emf_are_inverse() -> None:
    impedances = {
        "rated_impedance_ohm": 32.0,
        "rated_source_impedance_ohm": ref.IEC60268_7_IEC61938_SOURCE_IMPEDANCE_OHM,
    }
    emf = ea.headphone_source_emf(ref.IEC60268_7_WORKING_POWER_W, **impedances)
    assert emf == pytest.approx(math.sqrt(1e-3 * 32.0) * 152.0 / 32.0, rel=1e-12)
    assert ea.headphone_input_power(emf, **impedances) == pytest.approx(1e-3, rel=1e-12)


def test_input_power_without_source_impedance_is_e_squared_over_r() -> None:
    power = ea.headphone_input_power(
        2.0, rated_impedance_ohm=8.0, rated_source_impedance_ohm=0.0
    )
    assert power == pytest.approx(0.5, rel=1e-12)


def test_working_level_is_the_level_at_one_milliwatt() -> None:
    impedances = {"rated_impedance_ohm": 300.0, "rated_source_impedance_ohm": 120.0}
    emf = ea.headphone_source_emf(1e-3, **impedances)
    level = ea.working_sound_pressure_level(96.0, 2.0 * emf, **impedances)
    assert level == pytest.approx(96.0 - 20.0 * math.log10(2.0), abs=1e-12)


def test_working_level_by_8_5_3_c_sets_the_voltage_across_the_headphone() -> None:
    impedances = {"rated_impedance_ohm": 32.0, "rated_source_impedance_ohm": 120.0}
    by_definition = ea.working_sound_pressure_level(100.0, 0.5, **impedances)
    by_method = ea.working_sound_pressure_level(
        100.0, 0.5, **impedances, headphone_impedance_ohm=40.0
    )
    # 8.5.2 b): E = sqrt(PR)(R + Rs)/R; 8.5.3 c): E = sqrt(PR)|Z + Rs|/|Z|.
    terminal = math.sqrt(1e-3 * 32.0)
    assert by_definition == pytest.approx(
        100.0 + 20.0 * math.log10(terminal * 152.0 / 32.0 / 0.5), abs=1e-12
    )
    assert by_method == pytest.approx(
        100.0 + 20.0 * math.log10(terminal * 160.0 / 40.0 / 0.5), abs=1e-12
    )
    # (152/32)/(160/40) = 1.1875, the 1.49 dB the docstring quotes.
    assert by_definition - by_method == pytest.approx(20.0 * math.log10(1.1875))
    assert round(by_definition - by_method, 2) == 1.49


def test_the_two_working_levels_agree_on_the_rated_impedance() -> None:
    impedances = {"rated_impedance_ohm": 32.0, "rated_source_impedance_ohm": 120.0}
    by_definition = ea.working_sound_pressure_level(100.0, 0.5, **impedances)
    by_method = ea.working_sound_pressure_level(
        100.0, 0.5, **impedances, headphone_impedance_ohm=32.0
    )
    assert by_method == pytest.approx(by_definition, abs=1e-12)


def test_working_level_by_8_5_3_c_takes_a_complex_impedance() -> None:
    impedance = 30.0 + 40.0j
    level = ea.working_sound_pressure_level(
        90.0,
        1.0,
        rated_impedance_ohm=50.0,
        rated_source_impedance_ohm=120.0,
        headphone_impedance_ohm=impedance,
    )
    emf = math.sqrt(1e-3 * 50.0) * abs(impedance + 120.0) / abs(impedance)
    assert level == pytest.approx(90.0 + 20.0 * math.log10(emf), abs=1e-12)


def test_working_level_refuses_a_zero_headphone_impedance() -> None:
    with pytest.raises(ValueError, match="headphone_impedance_ohm"):
        ea.working_sound_pressure_level(
            90.0,
            1.0,
            rated_impedance_ohm=32.0,
            rated_source_impedance_ohm=120.0,
            headphone_impedance_ohm=0.0,
        )


def test_a_negative_source_impedance_is_refused() -> None:
    with pytest.raises(ValueError, match="rated_source_impedance_ohm"):
        ea.headphone_input_power(
            1.0, rated_impedance_ohm=32.0, rated_source_impedance_ohm=-1.0
        )


def test_programme_level_is_the_power_sum_of_the_bands() -> None:
    level = ea.programme_signal_level(BANDS, np.full(BANDS.size, 70.0))
    assert level == pytest.approx(70.0 + 10.0 * math.log10(BANDS.size), abs=1e-12)


@pytest.mark.parametrize(
    ("frequency", "a_weighting"), [(100.0, -19.1), (1000.0, 0.0), (10000.0, -2.5)]
)
def test_a_weighting_reproduces_iec_61672_table_3(
    frequency: float, a_weighting: float
) -> None:
    pair = np.array([frequency, frequency * 10.0**0.1])
    level = ea.programme_signal_level(pair, [80.0, -300.0], a_weighted=True)
    assert round(level - 80.0, 1) == a_weighting


def test_free_field_compensation_subtracts_the_response() -> None:
    response = np.linspace(0.0, 10.0, BANDS.size)
    flat = np.full(BANDS.size, 70.0)
    compensated = ea.programme_signal_level(
        BANDS, flat, free_field_response_db=response
    )
    expected = 10.0 * math.log10(float(np.sum(10.0 ** ((flat - response) / 10.0))))
    assert compensated == pytest.approx(expected, abs=1e-12)


def test_programme_characteristic_voltage_averages_the_fittings() -> None:
    levels = np.array(
        [np.full(BANDS.size, 80.0) + offset for offset in (0.0, 1.0, -1.0)]
    )
    result = ea.programme_characteristic_voltage(0.05, BANDS, levels)
    sums = 80.0 + 10.0 * math.log10(BANDS.size) + np.array([0.0, 1.0, -1.0])
    expected = 0.05 * 10.0 ** ((94.0 - sums) / 20.0)
    np.testing.assert_allclose(result.voltages_v, expected, rtol=1e-12)
    assert result.characteristic_voltage_v == pytest.approx(float(np.mean(expected)))
    assert result.fittings_conform


def test_one_fitting_does_not_conform_to_8_3_5() -> None:
    result = ea.programme_characteristic_voltage(0.05, BANDS, np.full(BANDS.size, 80.0))
    assert not result.fittings_conform


def test_band_levels_at_the_characteristic_voltage_sum_to_94_db() -> None:
    levels = np.tile(np.linspace(70.0, 85.0, BANDS.size), (3, 1))
    result = ea.programme_characteristic_voltage(
        [0.05, 0.05, 0.05], BANDS, levels, a_weighted=True
    )
    at_voltage = result.band_levels_at_characteristic_db
    total = 10.0 * math.log10(float(np.sum(10.0 ** (at_voltage / 10.0))))
    assert total == pytest.approx(94.0, abs=1e-9)


def test_programme_characteristic_voltage_results_are_read_only() -> None:
    result = ea.programme_characteristic_voltage(0.05, BANDS, np.full(BANDS.size, 80.0))
    assert not result.band_levels_db.flags.writeable
    with pytest.raises(dataclasses.FrozenInstanceError, match="a_weighted"):
        result.a_weighted = True  # type: ignore[misc]


# ---------------------------------------------------------------------------
# 8.3.2: the limiting voltages' test signal
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ratio", [1.8, 2.0, 2.2])
def test_the_clipped_programme_signal_passes(ratio: float) -> None:
    x = ea.simulated_programme_signal(FS, 30.0, peak_to_rms=ratio, seed=8)
    check = ea.check_limiting_test_signal(x, FS)
    assert check.peak_to_rms == pytest.approx(ratio, rel=1e-9)
    assert check.passes


@pytest.mark.parametrize("ratio", [1.7, 2.3])
def test_a_ratio_just_outside_1_8_to_2_2_fails(ratio: float) -> None:
    x = ea.simulated_programme_signal(FS, 30.0, peak_to_rms=ratio, seed=8)
    check = ea.check_limiting_test_signal(x, FS)
    assert check.peak_to_rms == pytest.approx(ratio, rel=1e-9)
    assert check.spectrum.passes
    assert not check.peak_to_rms_passes
    assert not check.passes


def test_the_unclipped_programme_signal_fails_on_its_peaks() -> None:
    x = ea.simulated_programme_signal(FS, 30.0, seed=8)
    check = ea.check_limiting_test_signal(x, FS)
    assert check.spectrum.passes
    assert not check.peak_to_rms_passes
    assert not check.passes


def test_at_44_1_khz_the_20_khz_band_is_left_out() -> None:
    x = ea.simulated_programme_signal(44100, 30.0, peak_to_rms=2.0, seed=8)
    check = ea.check_limiting_test_signal(x, 44100)
    assert check.spectrum.frequencies_hz[-1] == 16000.0
    assert check.passes


def test_limiting_check_has_no_truth_value() -> None:
    x = ea.simulated_programme_signal(FS, 5.0, peak_to_rms=2.0, seed=8)
    check = ea.check_limiting_test_signal(x, FS)
    with pytest.raises(TypeError, match="passes"):
        bool(check)


def test_a_constant_record_is_refused() -> None:
    silence = np.zeros(FS)
    with pytest.raises(ValueError, match="constant"):
        ea.check_limiting_test_signal(silence, FS)


# ---------------------------------------------------------------------------
# 8.3.6: protective devices
# ---------------------------------------------------------------------------


def test_protection_voltage_interpolates_the_1_db_change() -> None:
    emf = np.array([0.1, 0.2, 0.4, 0.8, 1.6])
    # Linear (94 dB at 0.1 V) up to 0.4 V, then 0.5 dB and 2 dB short.
    levels = 94.0 + 20.0 * np.log10(emf / 0.1) - np.array([0.0, 0.0, 0.0, 0.5, 2.0])
    result = ea.protection_voltage(emf, levels)
    expected = 10.0 ** (
        (20.0 * math.log10(0.8) + (1.0 / 3.0) * 20.0 * math.log10(2.0)) / 20.0
    )
    assert result.protection_voltage_v == pytest.approx(expected, rel=1e-12)
    low, high = result.measurement_voltages_v or (0.0, 0.0)
    assert 20.0 * math.log10(high / low) == pytest.approx(2.0, abs=1e-12)


def test_a_device_that_never_operates_has_no_protection_voltage() -> None:
    emf = np.array([0.1, 1.0])
    result = ea.protection_voltage(emf, 94.0 + 20.0 * np.log10(emf / 0.1))
    assert result.protection_voltage_v is None
    assert result.measurement_voltages_v is None


def test_protection_needs_two_steps() -> None:
    with pytest.raises(ValueError, match="two steps"):
        ea.protection_voltage([0.1], [94.0])


# ---------------------------------------------------------------------------
# 8.6.2 and 8.12: coupler response and crosstalk
# ---------------------------------------------------------------------------


def test_coupler_response_is_referred_to_500_hz() -> None:
    levels = 100.0 + np.linspace(-3.0, 3.0, BANDS.size)
    response = ea.coupler_frequency_response(
        BANDS, levels, rated_frequency_range_hz=(100.0, 10000.0)
    )
    relative = response.relative_response_db()
    assert relative[list(BANDS).index(500.0)] == 0.0
    assert response.covers_rated_range


def test_coupler_response_short_of_the_rated_range() -> None:
    response = ea.coupler_frequency_response(
        BANDS, np.full(BANDS.size, 100.0), rated_frequency_range_hz=(20.0, 20000.0)
    )
    assert response.covers_rated_range is False
    unstated = ea.coupler_frequency_response(BANDS, np.full(BANDS.size, 100.0))
    assert unstated.covers_rated_range is None


def test_crosstalk_is_the_difference_of_the_levels() -> None:
    result = ea.crosstalk_attenuation(
        BANDS, np.full(BANDS.size, 100.0), np.linspace(40.0, 60.0, BANDS.size)
    )
    np.testing.assert_allclose(
        result.attenuation_db, np.linspace(60.0, 40.0, BANDS.size)
    )
    assert result.minimum_db == pytest.approx(40.0)


# ---------------------------------------------------------------------------
# 8.6.3 to 8.6.5: the responses with test persons
# ---------------------------------------------------------------------------


def test_field_comparison_response_is_the_quotient_referred_to_1_khz() -> None:
    rng = np.random.default_rng(1)
    emf = 0.05 * 10.0 ** (
        rng.normal(0.0, 1.0, (ref.IEC60268_7_MIN_PERSONS, BANDS.size)) / 20.0
    )
    field = np.linspace(68.0, 72.0, BANDS.size)
    result = ea.field_comparison_response(BANDS, field, emf, field="free")
    assert (
        result.reference_frequency_hz == ref.IEC60268_1_STANDARD_REFERENCE_FREQUENCY_HZ
    )
    quotient = field - 20.0 * np.log10(emf)
    reference = list(BANDS).index(ref.IEC60268_1_STANDARD_REFERENCE_FREQUENCY_HZ)
    np.testing.assert_allclose(
        result.response_db, quotient - quotient[:, [reference]], atol=1e-12
    )
    assert np.all(result.response_db[:, reference] == 0.0)
    np.testing.assert_allclose(result.mean_db, np.mean(result.response_db, axis=0))
    np.testing.assert_allclose(
        result.standard_deviation_db, np.std(result.response_db, axis=0, ddof=1)
    )
    assert result.meets_panel_size
    assert not result.qualifies_as_reference


def test_field_comparison_may_be_referred_to_500_hz() -> None:
    rng = np.random.default_rng(3)
    emf = 0.05 * 10.0 ** (rng.normal(0.0, 1.0, (8, BANDS.size)) / 20.0)
    at_1_khz = ea.field_comparison_response(BANDS, 70.0, emf, field="diffuse")
    at_500_hz = ea.field_comparison_response(
        BANDS, 70.0, emf, field="diffuse", reference_frequency_hz=500.0
    )
    shift = at_1_khz.response_db[:, [list(BANDS).index(500.0)]]
    np.testing.assert_allclose(at_500_hz.response_db, at_1_khz.response_db - shift)
    assert at_500_hz.reference_frequency_hz == 500.0


def test_sixteen_persons_qualify_a_substitution_reference() -> None:
    emf = np.full((ref.IEC60268_7_MIN_REFERENCE_PERSONS, BANDS.size), 0.05)
    result = ea.field_comparison_response(BANDS, 70.0, emf, field="diffuse")
    assert result.qualifies_as_reference
    np.testing.assert_allclose(result.mean_db, 0.0, atol=1e-12)


def test_seven_persons_are_too_few() -> None:
    emf = np.full((7, BANDS.size), 0.05)
    result = ea.field_comparison_response(BANDS, 70.0, emf, field="free")
    assert not result.meets_panel_size


def test_field_comparison_needs_the_reference_band() -> None:
    emf = np.full((8, 3), 0.05)
    with pytest.raises(ValueError, match="reference band"):
        ea.field_comparison_response([100.0, 500.0, 2000.0], 70.0, emf, field="free")


def test_field_comparison_refuses_another_field() -> None:
    emf = np.full((8, BANDS.size), 0.05)
    with pytest.raises(ValueError, match="'free' or 'diffuse'"):
        ea.field_comparison_response(BANDS, 70.0, emf, field="near")  # type: ignore[arg-type]


def _ear_canal_levels() -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(2)
    persons = ref.IEC60268_7_MIN_PERSONS
    field = 70.0 + rng.normal(0.0, 0.5, (persons, 2, BANDS.size))
    earphone = 70.0 + rng.normal(0.0, 0.5, (persons, 2, BANDS.size))
    return earphone, field


def test_ear_canal_response_is_formula_1() -> None:
    earphone, field = _ear_canal_levels()
    result = ea.ear_canal_frequency_response(BANDS, earphone, field)
    difference = earphone.mean(axis=1) - field.mean(axis=1)
    reference = list(BANDS).index(500.0)
    np.testing.assert_allclose(
        result.response_db, difference - difference[:, [reference]], atol=1e-12
    )
    np.testing.assert_allclose(result.mean_db, result.response_db.mean(axis=0))
    np.testing.assert_allclose(
        result.standard_deviation_db, np.std(result.response_db, axis=0, ddof=1)
    )
    assert result.reference_frequency_hz == ref.IEC60268_7_STANDARD_FREQUENCY_HZ
    assert result.meets_panel_size
    assert not result.qualifies_as_reference


def test_sixteen_persons_calibrate_the_reference_of_the_indirect_method() -> None:
    rng = np.random.default_rng(4)
    persons = ref.IEC60268_7_MIN_REFERENCE_PERSONS
    field = 70.0 + rng.normal(0.0, 0.5, (persons, 2, BANDS.size))
    earphone = 70.0 + rng.normal(0.0, 0.5, (persons, 2, BANDS.size))
    result = ea.ear_canal_frequency_response(BANDS, earphone, field)
    assert result.qualifies_as_reference
    fewer = ea.ear_canal_frequency_response(BANDS, earphone[:15], field[:15])
    assert not fewer.qualifies_as_reference


def test_fittings_more_than_2_5_db_apart_are_flagged() -> None:
    earphone, field = _ear_canal_levels()
    earphone[:, 1] = earphone[:, 0]
    earphone[3, 1, 4] += ref.IEC60268_7_MAX_FITTING_DIFFERENCE_DB
    earphone[5, 1, 6] += 2.6
    result = ea.ear_canal_frequency_response(BANDS, earphone, field)
    expected = np.ones(8, dtype=bool)
    expected[5] = False
    np.testing.assert_array_equal(result.fittings_consistent, expected)


def test_the_500_hz_band_is_matched_within_3_db() -> None:
    earphone, field = _ear_canal_levels()
    reference = list(BANDS).index(500.0)
    earphone[:, 0, reference] = field[:, 0, reference]
    earphone[2, 0, reference] += ref.IEC60268_7_LEVEL_MATCH_DB
    earphone[4, 0, reference] -= 3.1
    result = ea.ear_canal_frequency_response(BANDS, earphone, field)
    assert result.levels_matched[2]
    assert not result.levels_matched[4]


def test_one_person_may_be_given_without_the_panel_axis() -> None:
    earphone, field = _ear_canal_levels()
    result = ea.ear_canal_frequency_response(BANDS, earphone[0], field[0])
    assert result.persons == 1
    np.testing.assert_array_equal(result.standard_deviation_db, 0.0)
    assert not result.meets_panel_size


def test_ear_canal_needs_two_readings() -> None:
    levels = np.zeros((8, 3, BANDS.size))
    with pytest.raises(ValueError, match=r"\(persons, 2, bands\)"):
        ea.ear_canal_frequency_response(BANDS, levels, levels)


# ---------------------------------------------------------------------------
# Annex B
# ---------------------------------------------------------------------------


def _microphone(**overrides: object) -> ea.EarCanalMicrophoneVerification:
    limits = ref.IEC60268_7_ANNEX_B
    values: dict[str, object] = {
        "entrance_area_mm2": limits["entrance_area_mm2"],
        "canal_section_area_mm2": 20.0,
        "volume_mm3": 100.0,
        "pink_noise_band_levels_db": [60.0, 63.0, 61.0],
        "open_levels_db": [60.0, 62.0],
        "sealed_levels_db": [45.0, 40.0],
    }
    values.update(overrides)
    return ea.verify_ear_canal_microphone(**values)  # type: ignore[arg-type]


def test_a_microphone_on_its_inclusive_limits_passes() -> None:
    verdict = _microphone()
    assert verdict.neighbour_difference_db == 3.0
    assert verdict.sealed_attenuation_db == 15.0
    assert verdict.passes


def test_area_ratio_of_0_6_is_not_less_than_0_6() -> None:
    verdict = _microphone(canal_section_area_mm2=27.0)
    assert verdict.area_ratio == pytest.approx(0.6)
    assert not verdict.requirements["b"]
    assert not verdict.passes


def test_a_volume_of_130_mm3_is_not_less_than_130() -> None:
    verdict = _microphone(volume_mm3=ref.IEC60268_7_ANNEX_B["volume_mm3"])
    assert not verdict.requirements["c"]


def test_a_leaky_seal_fails_item_e() -> None:
    verdict = _microphone(sealed_levels_db=[46.0, 40.0])
    assert not verdict.requirements["e"]


def test_microphone_verdict_has_no_truth_value() -> None:
    verdict = _microphone()
    with pytest.raises(TypeError, match="passes"):
        bool(verdict)


# ---------------------------------------------------------------------------
# 8.7: the distortion test signals
# ---------------------------------------------------------------------------


def _tone_level_db(x: np.ndarray, frequency: float) -> float:
    spectrum = np.fft.rfft(x) / x.size
    k = round(frequency * x.size / FS)
    return 20.0 * math.log10(2.0 * abs(spectrum[k]) / math.sqrt(2.0))


def test_modulation_signal_levels_are_those_of_note_1() -> None:
    x = ea.headphone_modulation_signal(FS, 1.0, rated_source_emf_v=1.0)
    assert float(np.max(np.abs(x))) == pytest.approx(math.sqrt(2.0), rel=1e-12)
    for frequency, printed in ref.IEC60268_7_MODULATION_LEVELS_DB.items():
        assert round(_tone_level_db(x, frequency), 1) == printed


def test_modulation_products_are_read_at_460_hz_not_470_hz() -> None:
    x = ea.headphone_modulation_signal(FS, 1.0, rated_source_emf_v=1.0)
    low, high = ref.IEC60268_7_MODULATION_HZ
    result = ea.modulation_distortion(x, FS, f_low=low, f_high=high)
    products = np.asarray(result.sideband_frequencies)
    np.testing.assert_allclose(
        products,
        sorted(ref.IEC60268_7_SECOND_ORDER_HZ + ref.IEC60268_7_THIRD_ORDER_HZ),
    )
    assert ref.IEC60268_7_FORMULA3_PRINTED_HZ not in products


def test_difference_frequency_signal_has_two_tones_at_half_the_voltage() -> None:
    x = ea.headphone_difference_frequency_signal(
        FS, 1.0, upper_frequency_hz=1000.0, rated_source_emf_v=2.0
    )
    lower = 1000.0 - ref.IEC60268_7_DIFFERENCE_FREQUENCY_HZ
    for frequency in (lower, 1000.0):
        assert _tone_level_db(x, frequency) == pytest.approx(0.0, abs=1e-9)
    assert float(np.max(np.abs(x))) == pytest.approx(2.0 * math.sqrt(2.0), rel=1e-12)


def test_difference_frequency_signal_needs_room_for_80_hz() -> None:
    with pytest.raises(ValueError, match="upper_frequency_hz"):
        ea.headphone_difference_frequency_signal(
            FS, 1.0, upper_frequency_hz=60.0, rated_source_emf_v=1.0
        )


# ---------------------------------------------------------------------------
# What the plots draw
# ---------------------------------------------------------------------------

_VERDICT_WORDS = {("en", True): "pass", ("en", False): "fail"}
_VERDICT_WORDS |= {("es", True): "cumple", ("es", False): "no cumple"}


def _title_verdict(title: str) -> str:
    """The verdict word a plot title ends with."""
    return title.rsplit(": ", 1)[1]


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("minimum", [25.6, 25.0])
def test_impedance_plot_draws_the_modulus_the_limit_and_the_minimum(
    language: str, minimum: float
) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    f, z = _impedance(minimum)
    verdict = ea.verify_rated_impedance(
        f, z, rated_impedance_ohm=32.0, rated_frequency_range_hz=(20.0, 20000.0)
    )
    ax = verdict.plot(language=language)
    curve, rated, limit, lowest = ax.lines
    np.testing.assert_array_equal(curve.get_xdata(), verdict.frequencies_hz)
    np.testing.assert_array_equal(curve.get_ydata(), verdict.impedance_ohm)
    assert tuple(rated.get_ydata()) == (32.0, 32.0)
    assert tuple(limit.get_ydata()) == (verdict.limit_ohm, verdict.limit_ohm)
    assert tuple(lowest.get_xdata()) == (verdict.minimum_frequency_hz,)
    assert tuple(lowest.get_ydata()) == (verdict.minimum_ohm,)
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    assert lowest.get_label() in labels
    assert _title_verdict(ax.get_title()) == _VERDICT_WORDS[(language, verdict.passes)]
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
def test_protection_plot_draws_the_change_and_the_1_db_line(language: str) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    emf = np.array([0.1, 0.2, 0.4, 0.8, 1.6])
    levels = 94.0 + 20.0 * np.log10(emf / 0.1) - np.array([0.0, 0.0, 0.0, 0.5, 2.0])
    result = ea.protection_voltage(emf, levels)
    ax = result.plot(language=language)
    change, step, voltage = ax.lines
    np.testing.assert_array_equal(change.get_xdata(), emf)
    np.testing.assert_allclose(change.get_ydata(), result.sensitivity_change_db)
    assert tuple(step.get_ydata()) == (-1.0, -1.0)
    assert tuple(voltage.get_xdata()) == (
        result.protection_voltage_v,
        result.protection_voltage_v,
    )
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("iec_scale", [True, False])
def test_coupler_plot_holds_50_db_to_the_decade(
    language: str, *, iec_scale: bool
) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    response = ea.coupler_frequency_response(
        BANDS, np.linspace(95.0, 105.0, BANDS.size)
    )
    ax = response.plot(language=language, iec_scale=iec_scale)
    np.testing.assert_array_equal(
        ax.lines[0].get_ydata(), response.sound_pressure_level_db
    )
    if iec_scale:
        assert ax.get_aspect() == pytest.approx(1.0 / 50.0)
    else:
        assert ax.get_aspect() == "auto"
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("iec_scale", [True, False])
def test_comparison_plot_draws_the_mean_and_the_spread(
    language: str, *, iec_scale: bool
) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    rng = np.random.default_rng(5)
    emf = 0.05 * 10.0 ** (rng.normal(0.0, 1.5, (8, BANDS.size)) / 20.0)
    result = ea.field_comparison_response(BANDS, 70.0, emf, field="free")
    ax = result.plot(language=language, iec_scale=iec_scale)
    heights = [patch.get_height() for patch in ax.patches]
    np.testing.assert_allclose(heights, result.mean_db)
    bars = ax.containers[1]
    segments = bars.lines[2][0].get_segments()
    spread = result.standard_deviation_db
    np.testing.assert_allclose([seg[0][1] for seg in segments], result.mean_db - spread)
    np.testing.assert_allclose([seg[1][1] for seg in segments], result.mean_db + spread)
    if iec_scale:
        # Ten bands to the decade, so 50 dB is ten bar positions long.
        assert ax.get_aspect() == pytest.approx(10.0 / 50.0)
        low, high = ax.get_ylim()
        assert high - low >= 40.0
    else:
        assert ax.get_aspect() == "auto"
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("iec_scale", [True, False])
def test_ear_canal_plot_draws_the_persons_the_mean_and_the_spread(
    language: str, *, iec_scale: bool
) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    earphone, field = _ear_canal_levels()
    result = ea.ear_canal_frequency_response(BANDS, earphone, field)
    ax = result.plot(language=language, iec_scale=iec_scale)
    persons = ax.lines[: result.persons]
    for line, response in zip(persons, result.response_db, strict=True):
        np.testing.assert_array_equal(line.get_ydata(), response)
    np.testing.assert_array_equal(ax.lines[result.persons].get_ydata(), result.mean_db)
    band = ax.collections[0].get_paths()[0].vertices[:, 1]
    lowest = result.mean_db - result.standard_deviation_db
    highest = result.mean_db + result.standard_deviation_db
    assert float(np.min(band)) == pytest.approx(float(np.min(lowest)))
    assert float(np.max(band)) == pytest.approx(float(np.max(highest)))
    if iec_scale:
        assert ax.get_aspect() == pytest.approx(1.0 / 50.0)
    else:
        assert ax.get_aspect() == "auto"
    plt.close("all")


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("sealed", [[45.0, 40.0], [52.0, 40.0]])
def test_microphone_plot_marks_item_e_as_a_minimum(
    language: str, sealed: list[float]
) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    verdict = _microphone(sealed_levels_db=sealed)
    ax = verdict.plot(language=language)
    heights = [patch.get_height() for patch in ax.patches]
    limits = ref.IEC60268_7_ANNEX_B
    expected = [
        100.0 * verdict.entrance_area_mm2 / limits["entrance_area_mm2"],
        100.0 * verdict.area_ratio / limits["canal_area_ratio"],
        100.0 * verdict.volume_mm3 / limits["volume_mm3"],
        100.0 * verdict.neighbour_difference_db / limits["neighbour_difference_db"],
        100.0 * verdict.sealed_attenuation_db / limits["sealed_attenuation_db"],
    ]
    np.testing.assert_allclose(heights, expected)
    assert ax.patches[4].get_hatch() == "//"
    assert all(not patch.get_hatch() for patch in ax.patches[:4])
    minimum = "(minimum)" if language == "en" else "(mínimo)"
    assert ax.get_xticklabels()[4].get_text().endswith(minimum)
    labels = [text.get_text() for text in ax.get_legend().get_texts()]
    outside = "Outside its limit" if language == "en" else "Fuera de su límite"
    assert (outside in labels) == (not verdict.passes)
    assert _title_verdict(ax.get_title()) == _VERDICT_WORDS[(language, verdict.passes)]
    plt.close("all")


@pytest.mark.parametrize(
    ("a_weighted", "free_field", "clause"),
    [
        (False, False, "(8.3.4)"),
        (True, True, "(8.3.5)"),
        (True, False, "A-weighted only"),
    ],
)
def test_characteristic_voltage_plot_names_what_was_corrected(
    clause: str, *, a_weighted: bool, free_field: bool
) -> None:
    plt = pytest.importorskip("matplotlib.pyplot")
    levels = np.tile(np.linspace(70.0, 85.0, BANDS.size), (3, 1))
    result = ea.programme_characteristic_voltage(
        0.05,
        BANDS,
        levels,
        a_weighted=a_weighted,
        free_field_response_db=np.zeros(BANDS.size) if free_field else None,
    )
    ax = result.plot()
    heights = np.array([patch.get_height() for patch in ax.patches])
    floor = ax.patches[0].get_y()
    np.testing.assert_allclose(heights + floor, result.band_levels_at_characteristic_db)
    assert clause in ax.get_title()
    plt.close("all")
