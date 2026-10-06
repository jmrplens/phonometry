#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Tests for Method B of EN 15610:2009, the digital one-third octave filters of 7.4.3.

7.4.3 prints its own numbers: 2 m discarded at either end of a record after
filtering, a record of at least 5 m (NOTE 1) and 15 m analysed in total, and
filters that "shall comply with EN 61260", the 1995 edition its normative
references date. That edition prints the limits the bank is held to: Table 1
on the relative attenuation, 4.5.3 on the filter integrated response
(:math:`\pm 0{,}15` dB for class 0) and 4.9 on the summation of the outputs
(:math:`\pm 1{,}0` dB for class 0).

Methods A and B are compared on records whose band levels are known in
closed form. A tone on a Fourier line, its three Hanning lines inside its
band, is read exactly by Method A; Method B reads it through the relative
attenuation of its filter at the tone, so the two differ by no more than
Table 1 lets a class 0 filter attenuate there. A record whose lines are
spread evenly across the bands is read by Method B within the class 0
integrated response of the ideal band, the sum of the lines inside it.
"""

from __future__ import annotations

import math

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest
from reference_data import rolling_stock_noise as ref

from phonometry import environment
from phonometry.environment.sources.acoustic_roughness import (
    AcousticRoughnessSpectrum,
    acoustic_roughness_spectrum,
    average_roughness_spectra,
    filtered_roughness_spectrum,
    roughness_filter_bank,
)
from phonometry.filters import (
    FilterDesign,
    OctaveFilterBank,
    class_limits,
    verify_filter_class,
)
from phonometry.filters.compliance import _band_relative_attenuation

_DX = 1.0e-3

#: EN 61260:1995 4.5.3 and 4.9: the class 0 limits, dB.
_CLASS_0_INTEGRATED_RESPONSE_DB = 0.15
_CLASS_0_SUMMATION_DB = 1.0

#: The base-ten octave ratio, EN 61260:1995 equation (1).
_G = 10.0**0.3

#: EN 61260:1995 equation (10): the normalized frequency :math:`G^{4}` maps to
#: for one-third octave filters, from where Table 1 asks class 0 for +75 dB.
_OMEGA_G4 = 1.0 + (_G ** (1.0 / 6.0) - 1.0) / (_G**0.5 - 1.0) * (_G**4 - 1.0)

#: The sampling intervals the record-length tests run at: 1 mm and 0,5 mm.
_SPACINGS_M = (1.0e-3, 5.0e-4)


def _plain(record: np.ndarray, spacing_m: float = _DX) -> AcousticRoughnessSpectrum:
    """Method B with neither spike removal nor curvature processing."""
    return filtered_roughness_spectrum(
        record,
        sample_spacing_m=spacing_m,
        spike_removal=False,
        curvature_processing=False,
    )


def _tones(
    wavenumbers: tuple[int, ...], length_m: float, spacing_m: float = _DX
) -> np.ndarray:
    """Tones of 1 um amplitude, one per wavenumber in cycles per metre."""
    x = np.arange(round(length_m / spacing_m)) * spacing_m
    rng = np.random.default_rng(15610)
    return np.sum(
        [
            np.cos(2.0 * np.pi * k * x + rng.uniform(0.0, 2.0 * np.pi))
            for k in wavenumbers
        ],
        axis=0,
    )


def _even_lines(
    period_m: float, length_m: float, amplitude_um: float
) -> tuple[np.ndarray, np.ndarray]:
    """Lines every 1/period per metre up to 480 per metre, of equal amplitude.

    One period is built by an inverse Fourier transform and repeated, so the
    lines are orthogonal over any stretch one period long.
    """
    samples = round(period_m / _DX)
    rng = np.random.default_rng(3)
    spectrum = np.zeros(samples // 2 + 1, dtype=complex)
    lines = np.arange(1, round(480.0 * period_m))
    spectrum[lines] = (
        amplitude_um
        * samples
        / 2.0
        * np.exp(1j * rng.uniform(0, 2 * np.pi, lines.size))
    )
    period = np.fft.irfft(spectrum, n=samples)
    total = round(length_m / _DX)
    return np.resize(period, total), lines / period_m


# ---------------------------------------------------------------------------
# The bank: EN 61260:1995, as 7.4.3 asks.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("spacing_m", [1.0e-3, 5.0e-4, 2.5e-4])
def test_the_bank_is_class_0_on_table_1_of_en_61260_1995(spacing_m: float) -> None:
    """Every band is within the class 0 limits of Table 1 up to the Nyquist wavenumber.

    The bands run at the record's own rate, with no decimation, so the grade
    covers every wavenumber a record can hold and no alias folds back into a
    band below the limits.
    """
    bank = roughness_filter_bank(sample_spacing_m=spacing_m)
    result = verify_filter_class(bank, edition="1995")
    assert result.overall_class == 0
    assert all(int(factor) == 1 for factor in bank.factor)
    nyquist = bank.fs / 2.0
    reach = [
        band["checked_to_omega"] * float(centre) / nyquist
        for band, centre in zip(result.bands, bank.freq, strict=True)
    ]
    np.testing.assert_allclose(reach, 1.0, rtol=1e-9)


def test_the_bank_attenuates_class_0_beyond_g4_on_a_record() -> None:
    r"""Unit tones run through the bank as Method B runs it: +75 dB beyond :math:`G^{\pm 4}`.

    Table 1 of EN 61260:1995 asks class 0 for a relative attenuation of at
    least 75 dB at and beyond the normalized frequencies :math:`G^{\pm 4}`
    maps to. Tones from 0,3 per metre to just under the Nyquist wavenumber,
    and the two wavenumbers that fold onto bands of a decimated bank
    (74,773 per metre onto the 0,5 m band, 88,202 per metre onto the 0,4 m
    band), are filtered on a 40 m record; the mean square of the
    last 15 m, once every filter has rung out, is compared with that of a
    tone at the band's midband wavenumber.
    """
    bank = roughness_filter_bank(sample_spacing_m=_DX)
    x = np.arange(round(40.0 / _DX)) * _DX
    settled = round(25.0 / _DX)

    def mean_squares(wavenumber: float) -> np.ndarray:
        bands = bank.filter(
            np.cos(2.0 * np.pi * wavenumber * x + 0.4),
            sigbands=True,
            calculate_level=False,
            detrend=False,
        ).require_bands()
        return np.array([np.mean(np.asarray(b)[settled:] ** 2) for b in bands])

    centres = np.asarray(bank.freq, dtype=float)
    reference = np.array([mean_squares(float(f))[i] for i, f in enumerate(centres)])
    wavenumbers = [*np.geomspace(0.3, 499.0, 61), 74.773, 88.202]
    worst = math.inf
    judged = 0
    for wavenumber in wavenumbers:
        omega = wavenumber / centres
        beyond = (omega >= _OMEGA_G4) | (omega <= 1.0 / _OMEGA_G4)
        attenuation = 10.0 * np.log10(
            reference[beyond] / mean_squares(wavenumber)[beyond]
        )
        lower, _ = class_limits(3, 0, omega[beyond], edition="1995")
        np.testing.assert_array_equal(lower, ref.EN61260_1995_CLASS_0_BEYOND_G4_DB)
        worst = min(worst, float(np.min(attenuation - lower)))
        judged += int(np.count_nonzero(beyond))
    assert judged == 870
    assert worst > 0.0


def _relative_attenuation_db(
    bank: OctaveFilterBank, index: int, omega: np.ndarray
) -> np.ndarray:
    """Relative attenuation of one band at normalized frequencies, dB (equation 8).

    Read as the class check reads it: the response the band has at the
    record's own rate, a decimated band's alias images included.
    """
    mid = float(bank.freq[index])
    return _band_relative_attenuation(
        bank.sos[index], int(bank.factor[index]), float(bank.fs), mid, omega * mid
    )


def test_the_integrated_response_of_every_band_is_within_class_0() -> None:
    r"""EN 61260:1995 4.5: :math:`\Delta B = 10 \lg (B_e / B_r)` within ±0,15 dB.

    :math:`B_e` is the integral of :math:`10^{-0.1 \Delta A}` over the
    normalized frequency (equation 14) and :math:`B_r = G^{1/6} - G^{-1/6}`
    (equation 9).
    """
    bank = roughness_filter_bank(sample_spacing_m=_DX)
    omega = np.linspace(1.0e-4, 20.0, 200001)
    reference = _G ** (1.0 / 6.0) - _G ** (-1.0 / 6.0)
    deviations = []
    for index in range(bank.num_bands):
        power = 10.0 ** (-0.1 * _relative_attenuation_db(bank, index, omega))
        effective = float(np.trapezoid(power, omega))
        deviations.append(10.0 * math.log10(effective / reference))
    assert max(abs(d) for d in deviations) <= _CLASS_0_INTEGRATED_RESPONSE_DB


def test_the_summation_of_outputs_is_within_class_0() -> None:
    """EN 61260:1995 4.9: between two midbands, the summed outputs within ±1,0 dB."""
    bank = roughness_filter_bank(sample_spacing_m=_DX)
    worst = 0.0
    for index in range(1, bank.num_bands - 1):
        frequencies = np.geomspace(bank.freq[index - 1], bank.freq[index + 1], 201)
        total = np.zeros(frequencies.size)
        for other in range(max(0, index - 3), min(bank.num_bands, index + 4)):
            omega = frequencies / float(bank.freq[other])
            total += 10.0 ** (-0.1 * _relative_attenuation_db(bank, other, omega))
        worst = max(worst, float(np.max(np.abs(10.0 * np.log10(total)))))
    assert worst <= _CLASS_0_SUMMATION_DB


def test_order_4_is_the_lowest_order_whose_bank_is_class_0() -> None:
    """Order 3 misses Table 1 near the Nyquist wavenumber; order 4 meets class 0."""
    limits = [2.0, 398.0]
    full_rate = FilterDesign(resample=False)
    third = OctaveFilterBank(1000, fraction=3, order=3, limits=limits, design=full_rate)
    fourth = OctaveFilterBank(
        1000, fraction=3, order=4, limits=limits, design=full_rate
    )
    assert verify_filter_class(third, edition="1995").overall_class != 0
    assert verify_filter_class(fourth, edition="1995").overall_class == 0


def test_the_bank_holds_the_bands_the_annex_b_listing_filters() -> None:
    """At 1 mm the default bank runs the 24 bands of ``wl_d``, 0,5 m to 2,5 mm (B.9.2)."""
    bank = roughness_filter_bank(sample_spacing_m=_DX)
    listing = ref.EN15610_LISTING_FILTER_WAVELENGTHS_M
    centres = np.asarray(bank.freq)
    assert bank.order == 4
    assert bank.fs == 1000
    np.testing.assert_allclose(centres, 10.0 ** (np.arange(3, 27) / 10.0), rtol=1e-12)
    nominal = [1.0 / float(f) for f in bank.nominal_freq]
    np.testing.assert_allclose(nominal, listing, rtol=0.01)


def test_the_bank_needs_a_whole_number_of_samples_per_metre() -> None:
    """0,3 mm is 3 333,3 samples per metre, which the bank cannot run at."""
    with pytest.raises(ValueError, match="whole number of samples per metre"):
        roughness_filter_bank(sample_spacing_m=3.0e-4)


def test_the_bank_refuses_a_sampling_interval_over_a_millimetre() -> None:
    with pytest.raises(ValueError, match="5.5 asks for 1 mm or less"):
        roughness_filter_bank(sample_spacing_m=2.0e-3)


def test_the_bank_refuses_a_reach_past_the_nyquist_band() -> None:
    with pytest.raises(ValueError, match="no one-third octave band"):
        roughness_filter_bank(sample_spacing_m=_DX, longest_wavelength_m=0.001)


# ---------------------------------------------------------------------------
# Methods A and B on the same record.
# ---------------------------------------------------------------------------

#: One tone in every other band from 6,3 cm to 2,5 mm, on a whole number of
#: cycles per metre with the whole width of its three Hanning lines inside the
#: band, which the 0,1 m band, 2,3 per metre wide, cannot hold.
_TONE_WAVENUMBERS = (16, 25, 40, 63, 100, 158, 251, 398)


def test_a_tone_at_a_band_centre_reads_its_mean_square() -> None:
    """A 3 um sinusoid at exactly 100 per metre reads 10 lg(9/2) dB re 1 um."""
    x = np.arange(0.0, 20.0, _DX)
    spectrum = _plain(3.0 * np.cos(2.0 * np.pi * 100.0 * x))
    assert spectrum.level_at(0.01) == pytest.approx(10.0 * math.log10(4.5), abs=1e-9)


def test_methods_a_and_b_agree_on_tones_within_table_1_class_0() -> None:
    """Method A reads each tone exactly; Method B within its class 0 relative attenuation.

    Each tone is 1 um, a mean square of 1/2, in a band of its own; the next
    tone is two bands away, under the filter skirt by more than 40 dB.
    """
    record = _tones(_TONE_WAVENUMBERS, 20.0)
    fourier = acoustic_roughness_spectrum(
        record, sample_spacing_m=_DX, spike_removal=False, curvature_processing=False
    )
    filtered = _plain(record)
    for k in _TONE_WAVENUMBERS:
        band = round(10.0 * math.log10(k))
        wavelength = filtered.wavelengths_m[list(filtered.bands).index(band)]
        level_a = fourier.level_at(wavelength)
        level_b = filtered.level_at(wavelength)
        assert level_a == pytest.approx(10.0 * math.log10(0.5), abs=1e-6)
        omega = np.array([k / 10.0 ** (band / 10.0)])
        lower, upper = class_limits(3, 0, omega, edition="1995")
        assert -float(upper[0]) - 1e-3 <= level_b - level_a <= -float(lower[0]) + 1e-3


def test_method_b_reads_an_even_spread_within_the_class_0_integrated_response() -> None:
    """Lines every 1/17 per metre: each band within ±0,15 dB of the sum of its lines.

    A 21 m record leaves 17 m once 2 m are discarded at either end, one period
    of the lines, so they add on their mean squares exactly there. Bands with
    a hundred lines or more are judged, where the count at the edges no longer
    matters.
    """
    amplitude = 0.05
    record, wavenumbers = _even_lines(17.0, 21.0, amplitude)
    spectrum = _plain(record)
    judged = 0
    for wavelength, level in zip(
        spectrum.wavelengths_m, spectrum.levels_db, strict=True
    ):
        band = round(-10.0 * math.log10(wavelength))
        inside = np.count_nonzero(
            (wavenumbers >= 10.0 ** (band / 10.0 - 0.05))
            & (wavenumbers < 10.0 ** (band / 10.0 + 0.05))
        )
        if inside < 100:
            continue
        ideal = 10.0 * math.log10(inside * amplitude**2 / 2.0)
        assert abs(level - ideal) <= _CLASS_0_INTEGRATED_RESPONSE_DB
        judged += 1
    assert judged == 12


def test_both_methods_report_the_same_bands_on_a_five_metre_record() -> None:
    """1 m analysed by B and 1 m segments by A: both from 0,25 m to 2,5 mm (7.5)."""
    record = _tones((40,), 5.0)
    fourier = acoustic_roughness_spectrum(
        record, sample_spacing_m=_DX, spike_removal=False, curvature_processing=False
    )
    filtered = _plain(record)
    assert filtered.bands == fourier.bands
    assert filtered.wavelengths_m[0] == pytest.approx(0.25)


# ---------------------------------------------------------------------------
# 7.4.3: the ends, the shortest record, the reach.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("spacing_m", _SPACINGS_M)
def test_two_metres_are_discarded_at_either_end(spacing_m: float) -> None:
    """A burst 100 times the tone in the first and last metre is not read.

    The 1 cm filter rings out within a few centimetres, so a burst that ends
    a metre before the analysed stretch, or starts a metre after it, leaves
    the tone alone in the 1 cm band.
    """
    x = np.arange(round(9.0 / spacing_m)) * spacing_m
    record = 3.0 * np.cos(2.0 * np.pi * 100.0 * x)
    ends = (x < 1.0) | (x >= 8.0)
    record[ends] += 300.0 * np.cos(2.0 * np.pi * 103.0 * x[ends])
    spectrum = _plain(record, spacing_m)
    assert spectrum.level_at(0.01) == pytest.approx(10.0 * math.log10(4.5), abs=1e-3)


@pytest.mark.parametrize("spacing_m", _SPACINGS_M)
def test_the_record_length_is_the_length_analysed(spacing_m: float) -> None:
    """A 20 m record leaves 16 m analysed, and Method B segments nothing."""
    spectrum = _plain(_tones((40,), 20.0, spacing_m), spacing_m)
    expected = 20.0 - 2.0 * ref.EN15610_FILTER_TRANSIENT_M
    assert spectrum.record_length_m == pytest.approx(expected)
    assert spectrum.segment_count is None
    assert spectrum.method == "B"


@pytest.mark.parametrize("spacing_m", _SPACINGS_M)
def test_five_metres_is_the_shortest_record(spacing_m: float) -> None:
    """7.4.3 NOTE 1: 5 m leaves 1 m once 2 m are gone at either end."""
    shortest = ref.EN15610_SHORTEST_FILTERED_RECORD_M
    record = _tones((40,), shortest, spacing_m)
    analysed = shortest - 2.0 * ref.EN15610_FILTER_TRANSIENT_M
    assert _plain(record, spacing_m).record_length_m == pytest.approx(analysed)
    short = record[:-1]
    with pytest.raises(ValueError, match="NOTE 1 asks for at least 5 m"):
        _plain(short, spacing_m)


def test_a_long_record_reaches_as_far_as_its_filters_settle() -> None:
    """19 m leaves 15 m: 7.5 would allow 3,15 m, the filters settle to 0,5 m.

    The 0,63 m filter has not built up to within 0,15 dB of its steady output
    over the 15 m analysed, after the 2 m discarded; the 0,5 m one has.
    """
    spectrum = _plain(_tones((40,), 19.0))
    assert spectrum.wavelengths_m[0] == pytest.approx(0.5)
    assert spectrum.wavelengths_m[-1] == pytest.approx(0.0025)


def test_a_steady_long_wave_reads_its_level_once_the_filter_settles() -> None:
    """A 2 um sinusoid in the 0,5 m band of a 19 m record reads 10 lg 2 within 0,15 dB."""
    x = np.arange(0.0, 19.0, _DX)
    spectrum = _plain(2.0 * np.cos(2.0 * np.pi * 2.0 * x))
    assert spectrum.level_at(0.5) == pytest.approx(10.0 * math.log10(2.0), abs=0.15)


@pytest.mark.parametrize("processed", [False, True])
def test_an_offset_and_a_slope_do_not_reach_the_filters(*, processed: bool) -> None:
    """The mean and the linear trend go before the filters, as in the Annex B listing.

    A 1 mm offset and a slope of 100 um per metre under the 2 um sinusoid of
    the 0,5 m band leave its level at 10 lg 2 within 0,15 dB, with the 7.1
    processing or without it; left in, the offset alone reads 20 dB high.
    """
    x = np.arange(0.0, 19.0, _DX)
    record = 2.0 * np.cos(2.0 * np.pi * 2.0 * x) + 1000.0 + 100.0 * x
    spectrum = filtered_roughness_spectrum(
        record,
        sample_spacing_m=_DX,
        spike_removal=processed,
        curvature_processing=processed,
    )
    assert spectrum.level_at(0.5) == pytest.approx(10.0 * math.log10(2.0), abs=0.15)


def test_the_record_is_processed_as_7_1_asks() -> None:
    """Spike removal and curvature processing come before the filters, as in Method A."""
    record = _tones((40, 100), 6.0)
    record[3000] += 40.0
    processed = environment.curvature_processed_roughness(
        environment.remove_roughness_spikes(record, sample_spacing_m=_DX),
        sample_spacing_m=_DX,
    )
    direct = filtered_roughness_spectrum(record, sample_spacing_m=_DX)
    by_hand = _plain(processed)
    np.testing.assert_allclose(direct.levels_db, by_hand.levels_db, atol=1e-9)


def test_the_record_needs_a_whole_number_of_samples_per_metre() -> None:
    record = np.zeros(20000)
    with pytest.raises(ValueError, match="whole number of samples per metre"):
        filtered_roughness_spectrum(record, sample_spacing_m=3.0e-4)


# ---------------------------------------------------------------------------
# The spectrum's method, the average and the reference track.
# ---------------------------------------------------------------------------


def test_each_method_labels_its_spectrum() -> None:
    record = _tones((40,), 6.0)
    fourier = acoustic_roughness_spectrum(record, sample_spacing_m=_DX)
    assert fourier.method == "A"
    assert _plain(record).method == "B"


def test_the_average_keeps_a_shared_method_and_drops_a_mixed_one() -> None:
    record = _tones((40,), 6.0)
    filtered = _plain(record)
    fourier = acoustic_roughness_spectrum(record, sample_spacing_m=_DX)
    both_b = average_roughness_spectra([filtered, filtered])
    assert both_b.method == "B"
    assert both_b.record_length_m == pytest.approx(4.0)
    assert average_roughness_spectra([filtered, fourier]).method is None


def test_a_spectrum_refuses_an_unknown_method() -> None:
    with pytest.raises(ValueError, match="'method'"):
        AcousticRoughnessSpectrum([0.01], [0.0], method="C")


def _spectrum_under_limit(length_m: float | None) -> AcousticRoughnessSpectrum:
    limit = environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB
    wavelengths = sorted(limit, reverse=True)
    return AcousticRoughnessSpectrum(
        wavelengths,
        [limit[w] - 2.0 for w in wavelengths],
        record_length_m=length_m,
        method="B",
    )


def _passing_decay_rates() -> list[environment.TrackDecayRate]:
    """Vertical and lateral decay rates 10 % over the limits of Figure 3."""
    limits = environment.REFERENCE_TRACK_DECAY_LIMITS_DB_PER_M
    return [
        environment.TrackDecayRate(
            direction,
            list(limits[direction]),
            [1.1 * v for v in limits[direction].values()],
        )
        for direction in ("vertical", "lateral")
    ]


def _filtered_length(
    check: environment.ReferenceTrackCheck,
) -> environment.TrackCondition:
    return next(c for c in check.conditions if c.clause == "EN 15610 7.4.3")


@pytest.mark.parametrize(
    ("length_m", "holds"),
    [(ref.EN15610_FILTERED_TOTAL_M, True), (ref.EN15610_FILTERED_TOTAL_M - 0.1, False)],
)
def test_a_method_b_line_needs_15_m_analysed(length_m: float, *, holds: bool) -> None:
    """7.4.3: at least 15 m of record once the 2 x 2 m have gone from each record."""
    check = environment.check_reference_track(
        [_spectrum_under_limit(length_m)], _passing_decay_rates(), speed_kmh=160.0
    )
    assert _filtered_length(check).holds is holds
    assert check.passes is holds


def test_the_shortest_method_b_line_decides_the_15_m() -> None:
    """A 16 m line does not carry a 10 m one: 7.4.3 holds every line to 15 m."""
    check = environment.check_reference_track(
        [_spectrum_under_limit(16.0), _spectrum_under_limit(10.0)],
        _passing_decay_rates(),
        speed_kmh=160.0,
    )
    condition = _filtered_length(check)
    assert condition.holds is False
    assert "10 m" in condition.detail
    assert check.passes is False


def test_a_method_b_line_without_its_length_is_not_judged_and_does_not_pass() -> None:
    """Every other requirement holds; the 7.4.3 length unjudged keeps the track from passing."""
    decay = _passing_decay_rates()
    unknown = environment.check_reference_track(
        [_spectrum_under_limit(None)], decay, speed_kmh=160.0
    )
    known = environment.check_reference_track(
        [_spectrum_under_limit(16.0)], decay, speed_kmh=160.0
    )
    assert _filtered_length(unknown).holds is None
    assert all(
        c.holds is True for c in unknown.conditions if c.clause != "EN 15610 7.4.3"
    )
    assert unknown.passes is False
    assert known.passes is True


def test_a_method_a_line_is_not_held_to_the_15_m() -> None:
    """For Method A the 15 m is a NOTE of 7.4.2, not a requirement."""
    spectrum = _spectrum_under_limit(1.0)
    fourier = AcousticRoughnessSpectrum(
        spectrum.wavelengths_m, spectrum.levels_db, record_length_m=1.0, method="A"
    )
    check = environment.check_reference_track([fourier], [], speed_kmh=160.0)
    assert all(c.clause != "EN 15610 7.4.3" for c in check.conditions)


def test_methods_a_and_b_plot_on_the_same_axes() -> None:
    record = _tones(_TONE_WAVENUMBERS, 20.0)
    fourier = acoustic_roughness_spectrum(record, sample_spacing_m=_DX)
    filtered = filtered_roughness_spectrum(record, sample_spacing_m=_DX)
    ax = fourier.plot(
        limit_db=environment.REFERENCE_TRACK_ROUGHNESS_LIMIT_DB, label="Method A"
    )
    filtered.plot(ax=ax, label="Method B")
    labels = [line.get_label() for line in ax.get_lines()]
    assert {"Method A", "Method B", "Limit"} <= set(labels)
    plt.close(ax.figure)
