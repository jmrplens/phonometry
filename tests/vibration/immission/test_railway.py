#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the railway evaluation of DIN 45672-2:1995-07.

The standard prints no worked example, so these hold it to what it does print
and to what its formulas imply: Table 1 line for line, the reference values,
the start-up statement of Clause 4, Formula (14) and the calibration check of
7.3.3 (a density that does not change with the bandwidth), Annex A's factor,
and a synthetic passage whose every quantity has a closed form.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry import emission, vibration
from phonometry.vibration import immission as im
from phonometry.vibration.immission import railway

#: An integer rate that carries the railway working range: the third-octave
#: bank needs an integer, and 315 Hz needs a Nyquist well above it.
FS_HZ = 2048

#: The length of the synthetic passage, in seconds.
RECORD_S = 30.0


def _sine(freq_hz: float, amplitude: float, duration_s: float, fs: float) -> np.ndarray:
    t = np.arange(round(duration_s * fs)) / fs
    return amplitude * np.sin(2.0 * math.pi * freq_hz * t)


def _passage(freq_hz: float = 16.0, amplitude: float = 1.0) -> np.ndarray:
    """Quiet, a raised-cosine rise, twelve steady seconds, a fall, quiet."""
    t = np.arange(round(RECORD_S * FS_HZ)) / FS_HZ
    envelope = np.zeros_like(t)
    rise = (t >= 6.0) & (t < 8.0)
    envelope[rise] = 0.5 * (1.0 - np.cos(math.pi * (t[rise] - 6.0) / 2.0))
    envelope[(t >= 8.0) & (t < 20.0)] = 1.0
    fall = (t >= 20.0) & (t < 22.0)
    envelope[fall] = 0.5 * (1.0 + np.cos(math.pi * (t[fall] - 20.0) / 2.0))
    return amplitude * envelope * np.sin(2.0 * math.pi * freq_hz * t)


# -- Reference values ----------------------------------------------------------


def test_the_velocity_reference_is_the_one_emission_uses() -> None:
    """Formula (2): 5·10⁻⁸ m/s, the DIN EN 21683 value, here in mm/s."""
    assert im.VELOCITY_LEVEL_REFERENCE_MM_S == pytest.approx(
        emission.REFERENCE_VELOCITY * 1000.0, rel=1e-12
    )


def test_a_steady_one_millimetre_per_second_is_86_decibels() -> None:
    """20 lg(1 / 5·10⁻⁵) = 86,02 dB once the running r.m.s. has settled."""
    level = im.running_velocity_level(_sine(80.0, math.sqrt(2.0), 3.0, FS_HZ), FS_HZ)
    assert np.mean(level[-FS_HZ:]) == pytest.approx(86.02, abs=0.05)


def test_the_acceleration_level_is_referred_to_a_micrometre_per_second_squared() -> (
    None
):
    """Formula (3): a0 = 10⁻⁶ m/s², so 1 m/s² r.m.s. is 120 dB."""
    level = im.running_acceleration_level(
        _sine(80.0, math.sqrt(2.0), 3.0, FS_HZ), FS_HZ
    )
    assert np.mean(level[-FS_HZ:]) == pytest.approx(120.0, abs=0.05)


def test_the_acceleration_reference_is_the_one_human_exposure_publishes() -> None:
    assert railway._ACCELERATION_REFERENCE_M_S2 == pytest.approx(
        vibration.REFERENCE_ACCELERATION, rel=1e-12
    )


def test_a_level_before_the_first_sample_is_minus_infinity() -> None:
    """A record that opens with silence has no level until it has a signal."""
    record = np.concatenate([np.zeros(10), np.ones(10)])
    level = im.running_velocity_level(record, FS_HZ)
    assert np.isneginf(level[0])
    assert np.isfinite(level[-1])


# -- Clause 4: the running r.m.s. started from rest ------------------------------


@pytest.mark.parametrize(("multiple", "printed"), [(2.0, 0.14), (4.0, 0.02)])
def test_clause_4_quotes_the_shortfall_of_the_mean_square(
    multiple: float, printed: float
) -> None:
    """14 % after 2 tau and 2 % after 4 tau are e^-2 and e^-4, rounded.

    The mean square of the running average of a sine is short of its final
    value by exp(-t/tau) once the ripple is averaged out. The r.m.s., which is
    what the sentence and Figure 3 are about, is short by about half that.
    """
    freq_hz = 200.0
    tau = im.KB_TIME_CONSTANT_S
    rms = im.running_velocity_rms(_sine(freq_hz, 1.0, 1.0, FS_HZ), FS_HZ)
    at = round(multiple * tau * FS_HZ)
    half_period = round(FS_HZ / freq_hz / 2.0)
    mean_square = float(np.mean(rms[at - half_period : at + half_period] ** 2))
    shortfall = 1.0 - mean_square / 0.5
    assert shortfall == pytest.approx(math.exp(-multiple), abs=0.003)
    assert round(shortfall, 2) == pytest.approx(printed)
    rms_shortfall = 1.0 - math.sqrt(mean_square / 0.5)
    assert rms_shortfall == pytest.approx(printed / 2.0, abs=0.006)


def test_formula_5_approximates_formula_4_once_settled() -> None:
    """Clause 6.1: the r.m.s. of the running r.m.s. is close to the true one."""
    record = _sine(31.5, 1.0, 6.0, FS_HZ)
    running = im.running_velocity_rms(record, FS_HZ)
    direct = im.interval_rms(record, FS_HZ, interval_s=(2.0, 6.0))
    approx = im.interval_rms(running, FS_HZ, interval_s=(2.0, 6.0))
    assert direct == pytest.approx(1.0 / math.sqrt(2.0), rel=1e-3)
    assert approx == pytest.approx(direct, rel=0.01)


def test_an_interval_outside_the_record_is_refused() -> None:
    record = np.ones(FS_HZ)
    with pytest.raises(ValueError, match="runs outside the record"):
        im.interval_rms(record, FS_HZ, interval_s=(5.0, 6.0))
    with pytest.raises(ValueError, match="runs outside the record"):
        im.interval_rms(record, FS_HZ, interval_s=(-0.5, 0.5))
    with pytest.raises(ValueError, match="end > start"):
        im.interval_rms(record, FS_HZ, interval_s=(0.5, 0.5))


# -- Clause 6.2: the event value and its level -----------------------------------


def test_the_event_value_refers_the_passage_to_one_hour() -> None:
    """Formula (8): 0,1 mm/s for 36 s is 0,01 mm/s over the hour."""
    assert im.event_velocity(0.1, 36.0) == pytest.approx(0.01)


def test_the_event_level_is_the_event_value_as_a_level() -> None:
    """Formula (9) is Formula (8) in decibels, term for term."""
    v_e = im.event_velocity(0.1, 36.0)
    level = im.event_velocity_level(0.1, 36.0)
    assert level == pytest.approx(20.0 * math.log10(v_e / 5.0e-5))
    assert level == pytest.approx(46.02, abs=0.005)


def test_event_values_add_in_square() -> None:
    """Formula (10): two passages of 3 and 4 make 5."""
    assert im.combined_event_velocity([0.03, 0.04]) == pytest.approx(0.05)


def test_a_negative_event_value_is_refused() -> None:
    with pytest.raises(ValueError, match="not negative"):
        im.combined_event_velocity([0.1, -0.1])
    with pytest.raises(ValueError, match="non-negative"):
        im.event_velocity(-0.1, 36.0)


# -- Clause 9: averaging over passages -----------------------------------------


def test_passages_average_in_energy() -> None:
    """Clause 9: the root of the mean square, and the level of it."""
    assert im.passage_average_velocity([0.0, 2.0]) == pytest.approx(math.sqrt(2.0))
    assert im.passage_average_level([60.0, 70.0]) == pytest.approx(
        10.0 * math.log10((1e6 + 1e7) / 2.0)
    )


def test_spectra_average_band_by_band() -> None:
    spectra = np.array([[60.0, 50.0], [70.0, 50.0]])
    averaged = im.passage_average_level(spectra, axis=0)
    assert averaged.shape == (2,)
    assert averaged[1] == pytest.approx(50.0)


# -- Clause 6.3: the amplitude distribution --------------------------------------


def test_the_amplitude_distribution_is_a_density() -> None:
    """Formula (11): p2 integrates to one and P2 rises from 0 to 1."""
    rng = np.random.default_rng(7)
    dist = im.amplitude_distribution(0.12 * rng.standard_normal(20_000))
    widths = np.diff(dist.edges_mm_s)
    assert np.sum(dist.density_per_mm_s * widths) == pytest.approx(1.0)
    assert dist.cumulative[-1] == pytest.approx(1.0)
    assert np.all(np.diff(dist.cumulative) >= 0.0)
    middle = dist.cumulative.size // 2
    assert dist.cumulative[middle] == pytest.approx(0.5, abs=0.03)


def test_a_silent_stretch_still_has_a_distribution() -> None:
    dist = im.amplitude_distribution(np.zeros(100), bins=3)
    assert dist.cumulative[-1] == pytest.approx(1.0)
    with pytest.raises(ValueError, match="at least 2"):
        im.amplitude_distribution(np.zeros(100), bins=1)


# -- Clause 7.3: narrow band --------------------------------------------------


def test_the_density_adds_back_to_the_mean_square() -> None:
    """Formula (14): the lines of G times the spacing give the r.m.s."""
    spectrum = im.narrowband_psd(_sine(40.0, 1.0, 16.0, FS_HZ), FS_HZ)
    spacing = spectrum.frequencies[1] - spectrum.frequencies[0]
    assert spacing == pytest.approx(im.NARROWBAND_RESOLUTION_HZ, rel=1e-3)
    assert np.sum(spectrum.psd) * spacing == pytest.approx(0.5, rel=1e-3)


def test_the_density_does_not_depend_on_the_bandwidth() -> None:
    """7.3.3 check 2: a broadband noise reads the same at two resolutions."""
    rng = np.random.default_rng(3)
    noise = rng.standard_normal(round(120.0 * FS_HZ))
    fine = im.narrowband_psd(noise, FS_HZ, resolution_hz=1.25)
    coarse = im.narrowband_psd(noise, FS_HZ, resolution_hz=2.5)
    band = (fine.frequencies > 20.0) & (fine.frequencies < 400.0)
    band_c = (coarse.frequencies > 20.0) & (coarse.frequencies < 400.0)
    assert np.mean(fine.psd[band]) == pytest.approx(
        np.mean(coarse.psd[band_c]), rel=0.02
    )
    assert np.mean(fine.psd[band]) == pytest.approx(2.0 / FS_HZ, rel=0.02)


def test_a_stretch_shorter_than_a_block_is_refused() -> None:
    with pytest.raises(ValueError, match="one block"):
        im.narrowband_psd(np.ones(100), FS_HZ)
    with pytest.raises(ValueError, match="makes a block of 20 samples"):
        im.narrowband_psd(np.ones(1000), 100.0, resolution_hz=5.0)


def test_the_energy_density_is_formula_13_as_printed() -> None:
    """e2 = |V2|²/4 = G2·T2/2, so its lines add up to half the energy."""
    duration = 16.0
    record = _sine(40.0, 1.0, duration, FS_HZ)
    spectrum = im.narrowband_psd(record, FS_HZ)
    spacing = spectrum.frequencies[1] - spectrum.frequencies[0]
    esd = im.passage_energy_spectral_density(spectrum.psd, duration)
    energy = float(np.sum(record**2) / FS_HZ)
    assert np.sum(esd) * spacing == pytest.approx(energy / 2.0, rel=1e-3)


def test_a_density_at_the_reference_is_zero_decibels() -> None:
    """Figure 7: G0 = (5·10⁻⁸ m/s)²/Hz."""
    levels = im.spectral_density_level([2.5e-9, 2.5e-7, 0.0])
    assert levels[0] == pytest.approx(0.0, abs=1e-9)
    assert levels[1] == pytest.approx(20.0)
    assert np.isneginf(levels[2])


def test_annex_a_divides_by_both_coefficients_squared() -> None:
    """Annex A: 0,030 V/(mm/s) and a gain of 10 divide the density by 0,09."""
    converted = im.velocity_psd_from_voltage(
        [0.09, 1.0], sensitivity_v_per_mm_s=0.030, gain=10.0
    )
    assert converted[0] == pytest.approx(1.0)
    assert converted[1] == pytest.approx(1.0 / (0.030**2 * 10.0**2))


# -- Clause 7.4: Table 1 ----------------------------------------------------------


def _lines(upper_hz: float = 600.0) -> np.ndarray:
    return np.arange(0.0, upper_hz, im.NARROWBAND_RESOLUTION_HZ)


def test_each_band_takes_the_lines_table_1_gives_it() -> None:
    """A flat density of one: each band's mean square is K_n · 1,25."""
    f = _lines()
    centres, rms = im.third_octaves_from_narrowband(f, np.ones_like(f))
    assert list(centres) == list(im.THIRD_OCTAVE_LINES)
    counts = rms**2 / im.NARROWBAND_RESOLUTION_HZ
    assert np.allclose(counts, list(im.THIRD_OCTAVE_LINES.values()))


def _band_of(line_hz: float) -> list[float]:
    """The bands a single line of power lands in."""
    f = _lines()
    density = np.where(np.isclose(f, line_hz), 1.0, 0.0)
    centres, rms = im.third_octaves_from_narrowband(f, density)
    return [float(c) for c, r in zip(centres, rms, strict=True) if r > 0.0]


def test_table_1_is_a_sixth_of_an_octave_either_side_but_at_10_hz() -> None:
    """Every line lands where the nominal band edges put it, except one.

    The 11,25 Hz line lies 0,03 Hz above the nominal edge between 10 Hz and
    12,5 Hz, and Table 1 counts it in the 10 Hz band, which is where the
    nearest-lines rule puts it too.
    """
    f = _lines()
    for line_hz in f[(f > 3.5) & (f < 560.0)]:
        inside = [
            nominal
            for nominal in im.THIRD_OCTAVE_LINES
            if nominal * 2 ** (-1 / 6) <= line_hz < nominal * 2 ** (1 / 6)
        ]
        expected = [10.0] if math.isclose(line_hz, 11.25) else inside
        assert _band_of(float(line_hz)) == expected, line_hz


def test_nominal_bands_leave_six_lines_out_and_share_five() -> None:
    """The consequence of nominal edges, stated so it cannot change unseen."""
    f = _lines()
    swept = f[(f > 3.5) & (f < 560.0)]
    outside = [float(line) for line in swept if not _band_of(float(line))]
    shared = [float(line) for line in swept if len(_band_of(float(line))) == 2]
    assert outside == [71.25, 141.25, 142.5, 353.75, 355.0, 356.25]
    assert shared == [178.75, 223.75, 446.25, 447.5, 448.75]
    assert _band_of(178.75) == [160.0, 200.0]
    assert _band_of(447.5) == [400.0, 500.0]


def test_a_short_spectrum_stops_at_the_last_whole_band() -> None:
    f = _lines(100.0)
    centres, _rms = im.third_octaves_from_narrowband(f, np.ones_like(f))
    assert centres[-1] == 80.0


def test_a_late_spectrum_starts_at_the_first_whole_band() -> None:
    """A band short of a line is left out, not filled from its neighbour."""
    f = _lines()
    from_line = im.third_octaves_from_narrowband(f[3:], np.ones(f.size - 3))
    assert from_line[0][0] == 4.0  # 3,75 Hz is the whole 4 Hz band
    from_20 = im.third_octaves_from_narrowband(f[16:], np.ones(f.size - 16))
    assert from_20[0][0] == 25.0  # the 20 Hz band needs 18,75 Hz
    assert np.allclose(from_20[1] ** 2 / 1.25, list(im.THIRD_OCTAVE_LINES.values())[8:])


def test_table_1_refuses_a_spectrum_of_another_resolution() -> None:
    f = np.arange(0.0, 600.0, 2.5)
    with pytest.raises(ValueError, match="Table 1 counts lines"):
        im.third_octaves_from_narrowband(f, np.ones_like(f))
    uneven = np.array([0.0, 1.25, 2.0, 3.75])
    with pytest.raises(ValueError, match="evenly spaced"):
        im.third_octaves_from_narrowband(uneven, np.ones(4))
    f = _lines()
    with pytest.raises(ValueError, match="negative"):
        im.third_octaves_from_narrowband(f, -np.ones(f.size))


# -- Annex B -----------------------------------------------------------------------


def test_annex_b_differences_and_sums() -> None:
    """(B.1) band by band; (B.3) two equal bands are 3 dB up."""
    loss = im.elastic_insertion_loss([60.0, 55.0], [50.0, 52.0])
    assert list(loss) == [10.0, 3.0]
    assert im.band_sum_level([60.0, 60.0]) == pytest.approx(63.0103, abs=1e-4)
    with pytest.raises(ValueError, match="band for band"):
        im.elastic_insertion_loss([60.0], [50.0, 52.0])


# -- Clause 5 and the whole chain ----------------------------------------------


def test_t1_is_centred_on_the_largest_amplitude() -> None:
    record = np.zeros(20 * FS_HZ)
    record[10 * FS_HZ] = 1.0
    assert im.centred_interval(record, FS_HZ) == pytest.approx((8.0, 12.0))
    record[:] = 0.0
    record[FS_HZ] = 1.0
    assert im.centred_interval(record, FS_HZ) == pytest.approx((0.0, 4.0))
    assert im.centred_interval(record[: 2 * FS_HZ], FS_HZ) == pytest.approx((0.0, 2.0))


def test_a_steady_passage_reduces_to_its_closed_forms() -> None:
    """A 1 mm/s sine at 16 Hz, well inside the band: every number is known."""
    passage = im.evaluate_train_passage(_passage(), FS_HZ, t2_s=(8.0, 20.0))
    t1, t2, t3 = passage.intervals_s
    assert t2 == pytest.approx((8.0, 20.0))
    assert t3 == pytest.approx((0.0, RECORD_S))
    assert t1[1] - t1[0] == pytest.approx(im.T1_DURATION_S)
    assert t2[0] <= t1[0]
    assert t1[1] <= t2[1]
    assert passage.peak_velocity_mm_s == pytest.approx(1.0, abs=0.02)
    assert passage.interval_rms_mm_s[1] == pytest.approx(1.0 / math.sqrt(2.0), rel=0.01)
    energy = float(np.sum(passage.velocity_mm_s**2) / FS_HZ)
    assert passage.event_velocity_mm_s == pytest.approx(
        math.sqrt(energy / im.EVENT_REFERENCE_DURATION_S), rel=1e-6
    )
    assert passage.event_level_db == pytest.approx(
        20.0
        * math.log10(passage.event_velocity_mm_s / im.VELOCITY_LEVEL_REFERENCE_MM_S)
    )
    band = list(passage.band_centres_hz).index(16.0)
    expected = 20.0 * math.log10(
        (1.0 / math.sqrt(2.0)) / im.VELOCITY_LEVEL_REFERENCE_MM_S
    )
    assert passage.band_interval_levels_db[1, band] == pytest.approx(expected, abs=0.2)
    assert passage.band_max_levels_db[band] == pytest.approx(expected, abs=0.5)
    others = np.delete(passage.band_interval_levels_db[1], band)
    assert np.all(others < expected - 15.0)


def test_the_passage_reads_the_same_kbf_max_as_the_meter() -> None:
    """KB_Fmax of the passage is the railway meter's reading of the record."""
    record = _passage(31.5)
    passage = im.evaluate_train_passage(record, FS_HZ, t2_s=(8.0, 20.0))
    reading = im.measure_vibration_immission(record, FS_HZ, working_range="railway")
    assert passage.kbf_max == pytest.approx(reading.kbf_max, rel=1e-12)


def test_the_band_limitation_is_applied_before_anything_is_read() -> None:
    """A 1 Hz component is outside the 4-315 Hz railway range and is filtered."""
    record = _passage(1.0)
    passage = im.evaluate_train_passage(record, FS_HZ, t2_s=(8.0, 20.0))
    assert passage.peak_velocity_mm_s < 0.1


def test_t1_may_be_as_long_as_t2_and_no_longer() -> None:
    record = _passage()
    short = im.evaluate_train_passage(record, FS_HZ, t2_s=(12.0, 14.5))
    t1, t2, _t3 = short.intervals_s
    assert t1 == pytest.approx(t2)
    with pytest.raises(ValueError, match="no longer"):
        im.evaluate_train_passage(record, FS_HZ, t2_s=(12.0, 14.0), t1_s=(10.0, 15.0))


def test_the_bands_can_stop_at_80_hz() -> None:
    """Clause 7.2 allows the DIN 45672-1 special case."""
    passage = im.evaluate_train_passage(
        _passage(), FS_HZ, t2_s=(8.0, 20.0), upper_band_hz=80.0
    )
    assert passage.band_centres_hz[-1] == 80.0
    assert passage.band_interval_levels_db.shape == (3, passage.band_centres_hz.size)
    record = _passage()
    for upper in (500.0, 100.5):
        with pytest.raises(ValueError, match="upper_band_hz"):
            im.evaluate_train_passage(
                record, FS_HZ, t2_s=(8.0, 20.0), upper_band_hz=upper
            )


def test_a_rate_that_cannot_carry_the_top_band_is_refused() -> None:
    """At 700 Hz the bank would drop the 315 Hz band; that is an error."""
    record = np.random.default_rng(1).standard_normal(20 * 700)
    with pytest.raises(ValueError, match="cannot carry the 315 Hz third octave"):
        im.evaluate_train_passage(record, 700, t2_s=(5.0, 15.0))
    shorter = im.evaluate_train_passage(
        record, 700, t2_s=(5.0, 15.0), upper_band_hz=250.0
    )
    assert shorter.band_centres_hz[-1] == 250.0


def test_the_stretches_nest_and_stay_inside_the_record() -> None:
    record = _passage()
    with pytest.raises(ValueError, match="runs outside the record"):
        im.evaluate_train_passage(record, FS_HZ, t2_s=(8.0, 45.0))
    with pytest.raises(ValueError, match="nest"):
        im.evaluate_train_passage(record, FS_HZ, t2_s=(8.0, 20.0), t3_s=(0.0, 12.0))
    with pytest.raises(ValueError, match="nest"):
        im.evaluate_train_passage(record, FS_HZ, t2_s=(8.0, 12.0), t1_s=(13.0, 15.0))


def test_the_bank_needs_an_integer_rate() -> None:
    record = _passage()
    with pytest.raises(ValueError, match="integer sampling frequency"):
        im.evaluate_train_passage(record, 2048.5, t2_s=(8.0, 20.0))


def test_a_silent_record_has_no_event_level() -> None:
    passage = im.evaluate_train_passage(np.zeros(4 * FS_HZ), FS_HZ, t2_s=(1.0, 3.0))
    assert passage.event_velocity_mm_s == 0.0
    assert math.isinf(passage.event_level_db)


def test_the_module_lists_what_it_publishes() -> None:
    for name in railway.__all__:
        assert getattr(im, name) is getattr(railway, name)
