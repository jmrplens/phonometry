#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The single-number ratings of EN 1793 and EN 16272, and the two spectra.

Oracles, all from the printed pages:

- EN 1793-3:1997 Table 1, the eighteen relative levels of the normalised
  traffic noise spectrum, read from the rendered page (PDF page 5, printed
  folio 3): they peak at 1 kHz and fall to -20 dB and -18 dB at the ends.
- EN 1793-1:2012 Clause 5, ``DLα``, and its Table A.1 categories A1 to A5.
- EN 1793-2:2012 Clause 5.2, ``DL_R``, and its Table A.1 categories B1 to B4.
- EN 16272-3-1:2012 Table 1 (PDF page 8, printed folio 6), the normalised
  railway noise spectrum, and its Clauses 5 and 6, which are the same two
  formulas with that table in the weights and no category ladder at all.

Closed-form checks the two formulas have to satisfy whatever the spectrum
is, which is what makes them oracles rather than regression pins:

- a device with the same ``R`` in every band rates exactly that ``R``,
  because the weighting cancels between numerator and denominator;
- the same holds for absorption: a constant ``α`` rates -10 lg(1 - α);
- a perfect absorber is capped by Clause 5 at 0,99 and therefore at 20 dB;
- a device that does nothing (α = 0, R = 0) rates 0 dB;
- shifting every ``R`` by ``d`` shifts ``DL_R`` by exactly ``d``.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
import pytest

from phonometry.environment import propagation as prop

_BANDS = len(prop.TRAFFIC_NOISE_BANDS_HZ)


class TestNormalisedSpectrum:
    """EN 1793-3:1997, Table 1."""

    def test_the_table_is_eighteen_bands_from_100_hz_to_5_khz(self) -> None:
        assert _BANDS == 18
        assert prop.TRAFFIC_NOISE_BANDS_HZ[0] == pytest.approx(100.0)
        assert prop.TRAFFIC_NOISE_BANDS_HZ[-1] == pytest.approx(5000.0)
        assert len(prop.NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB) == _BANDS

    def test_the_printed_levels(self) -> None:
        # Read from the rendered page: -20 at 100 Hz and 125 Hz, up to the
        # -8 dB peak at 1 kHz, back down to -18 at 5 kHz.
        assert prop.NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB == (
            -20.0,
            -20.0,
            -18.0,
            -16.0,
            -15.0,
            -14.0,
            -13.0,
            -12.0,
            -11.0,
            -9.0,
            -8.0,
            -9.0,
            -10.0,
            -11.0,
            -13.0,
            -15.0,
            -16.0,
            -18.0,
        )

    def test_the_peak_is_the_1_khz_band(self) -> None:
        peak = int(np.argmax(prop.NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB))
        assert prop.TRAFFIC_NOISE_BANDS_HZ[peak] == pytest.approx(1000.0)


class TestAbsorptionRating:
    """EN 1793-1:2012, Clause 5 and Table A.1."""

    def test_a_constant_coefficient_is_the_closed_form(self) -> None:
        for alpha in (0.2, 0.5, 0.8):
            got = prop.sound_absorption_rating(np.full(_BANDS, alpha))
            assert got.rating == pytest.approx(-10.0 * math.log10(1.0 - alpha))

    def test_a_device_that_absorbs_nothing_rates_zero(self) -> None:
        got = prop.sound_absorption_rating(np.zeros(_BANDS))
        assert got.rating == pytest.approx(0.0)
        assert got.reported == 0
        assert got.category == "A1"

    def test_a_perfect_absorber_is_capped_by_the_clause(self) -> None:
        with pytest.warns(prop.RoadDeviceWarning, match="0.99 limit"):
            got = prop.sound_absorption_rating(np.ones(_BANDS))
        # -10 lg(1 - 0,99) = 20 dB exactly, which is the ceiling the cap puts
        # on any device however absorptive it measures.
        assert got.rating == pytest.approx(20.0)
        assert got.category == "A5"

    def test_a_coefficient_above_one_does_not_break_the_logarithm(self) -> None:
        # alpha_S above 1 happens in a reverberation room; Clause 5 exists
        # for it, and the answer is the cap rather than a domain error.
        with pytest.warns(prop.RoadDeviceWarning):
            got = prop.sound_absorption_rating(np.full(_BANDS, 1.05))
        assert math.isfinite(got.rating)

    def test_the_weighting_is_the_spectrum_and_not_the_mean(self) -> None:
        # Absorptive only where the spectrum is loudest versus only where it
        # is quietest: same arithmetic mean, different rating.
        loud = np.zeros(_BANDS)
        quiet = np.zeros(_BANDS)
        loud[8:12] = 1.0  # 630 Hz to 1,25 kHz, around the peak
        quiet[[0, 1, 16, 17]] = 1.0  # the two ends
        assert (
            prop.sound_absorption_rating(loud).rating
            > prop.sound_absorption_rating(quiet).rating
        )

    @pytest.mark.parametrize(
        ("reported", "category"),
        [
            (0, "A1"),
            (3, "A1"),
            (4, "A2"),
            (7, "A2"),
            (8, "A3"),
            (11, "A3"),
            (12, "A4"),
            (15, "A4"),
            (16, "A5"),
            (20, "A5"),
        ],
    )
    def test_table_a1_categories(self, reported: int, category: str) -> None:
        # Solve for the constant coefficient that lands on each boundary.
        alpha = 1.0 - 10.0 ** (-0.1 * reported)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", prop.RoadDeviceWarning)
            got = prop.sound_absorption_rating(np.full(_BANDS, alpha))
        assert got.reported == reported
        assert got.category == category


class TestInsulationRating:
    """EN 1793-2:2012, Clause 5.2 and Table A.1."""

    def test_a_constant_index_rates_itself(self) -> None:
        for index in (5.0, 18.0, 42.0):
            got = prop.airborne_insulation_rating(np.full(_BANDS, index))
            assert got.rating == pytest.approx(index)

    def test_a_shift_in_every_band_shifts_the_rating(self) -> None:
        base = np.linspace(12.0, 38.0, _BANDS)
        first = prop.airborne_insulation_rating(base).rating
        second = prop.airborne_insulation_rating(base + 4.0).rating
        assert second - first == pytest.approx(4.0)

    def test_a_wall_that_does_nothing_rates_zero(self) -> None:
        got = prop.airborne_insulation_rating(np.zeros(_BANDS))
        assert got.rating == pytest.approx(0.0)
        assert got.category == "B1"

    def test_one_weak_band_costs_more_where_the_spectrum_is_loud(self) -> None:
        loud, quiet = np.full(_BANDS, 40.0), np.full(_BANDS, 40.0)
        loud[10] = 10.0  # the 1 kHz peak
        quiet[0] = 10.0  # the 100 Hz end, 12 dB down
        assert prop.airborne_insulation_rating(loud).rating < (
            prop.airborne_insulation_rating(quiet).rating
        )

    @pytest.mark.parametrize(
        ("reported", "category"),
        [
            (0, "B1"),
            (14, "B1"),
            (15, "B2"),
            (24, "B2"),
            (25, "B3"),
            (34, "B3"),
            (35, "B4"),
            (60, "B4"),
        ],
    )
    def test_table_a1_categories(self, reported: int, category: str) -> None:
        got = prop.airborne_insulation_rating(np.full(_BANDS, float(reported)))
        assert got.reported == reported
        assert got.category == category


class TestReporting:
    """What the two parts print, and what they refuse."""

    def test_the_reported_value_rounds_half_up(self) -> None:
        # 24,5 dB is reported as 25 dB, which is also where B2 becomes B3.
        got = prop.airborne_insulation_rating(np.full(_BANDS, 24.5))
        assert got.reported == 25
        assert got.category == "B3"

    def test_a_spectrum_of_the_wrong_length_is_refused(self) -> None:
        with pytest.raises(ValueError, match="18 one-third octave bands"):
            prop.sound_absorption_rating(np.zeros(16))
        with pytest.raises(ValueError, match="18 one-third octave bands"):
            prop.airborne_insulation_rating(np.zeros(20))

    def test_a_value_that_is_not_finite_is_refused(self) -> None:
        bad = np.zeros(_BANDS)
        bad[3] = np.nan
        with pytest.raises(ValueError, match="finite"):
            prop.sound_absorption_rating(bad)

    def test_the_result_carries_what_it_was_computed_from(self) -> None:
        alpha = np.linspace(0.1, 0.9, _BANDS)
        got = prop.sound_absorption_rating(alpha)
        assert got.quantity == "absorption"
        np.testing.assert_allclose(got.values, alpha)
        np.testing.assert_allclose(
            got.weights, prop.NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB
        )
        np.testing.assert_allclose(got.bands_hz, prop.TRAFFIC_NOISE_BANDS_HZ)


class TestRailwaySpectrum:
    """EN 16272-3-1:2012, Table 1 and Clauses 5 and 6."""

    def test_the_printed_levels(self) -> None:
        assert prop.NORMALISED_RAILWAY_NOISE_SPECTRUM_DB == (
            -27.0,
            -25.0,
            -23.0,
            -21.0,
            -19.0,
            -17.0,
            -15.0,
            -13.0,
            -12.0,
            -11.0,
            -10.0,
            -9.0,
            -9.0,
            -9.0,
            -9.0,
            -10.0,
            -13.0,
            -17.0,
        )

    def test_it_covers_the_same_eighteen_bands(self) -> None:
        assert len(prop.NORMALISED_RAILWAY_NOISE_SPECTRUM_DB) == _BANDS
        assert set(prop.SPECTRA) == {"road", "railway"}

    def test_the_railway_plateau_is_where_rolling_noise_is(self) -> None:
        # Flat within a decibel from 1,25 kHz to 2,5 kHz, where the road
        # spectrum has already begun to fall away.
        rail = np.asarray(prop.NORMALISED_RAILWAY_NOISE_SPECTRUM_DB)
        road = np.asarray(prop.NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB)
        plateau = rail[11:15]
        assert float(plateau.max() - plateau.min()) == pytest.approx(0.0)
        assert rail[14] - rail[10] > road[14] - road[10]

    def test_a_constant_device_rates_the_same_on_either_spectrum(self) -> None:
        # The weighting cancels, so a device that behaves the same in every
        # band cannot tell the two standards apart.
        for spectrum in prop.SPECTRA:
            got = prop.airborne_insulation_rating(
                np.full(_BANDS, 26.0), spectrum=spectrum
            )
            assert got.rating == pytest.approx(26.0)
            assert got.spectrum == spectrum

    def test_a_rising_absorber_rates_higher_on_the_railway_spectrum(self) -> None:
        # Rolling noise sits higher up, so an absorber that improves with
        # frequency is worth more against it.
        alpha = np.linspace(0.2, 0.9, _BANDS)
        road = prop.sound_absorption_rating(alpha).rating
        rail = prop.sound_absorption_rating(alpha, spectrum="railway").rating
        assert rail > road

    def test_the_railway_parts_print_no_category(self) -> None:
        # Their annexes are guidance notes: the rating is the number and
        # nothing more, and inventing an A or B letter for it would be an
        # invention.
        alpha = np.full(_BANDS, 0.6)
        assert prop.sound_absorption_rating(alpha, spectrum="railway").category is None
        assert (
            prop.airborne_insulation_rating(
                np.full(_BANDS, 20.0), spectrum="railway"
            ).category
            is None
        )
        assert prop.sound_absorption_rating(alpha).category is not None

    def test_the_cap_applies_to_the_railway_rating_too(self) -> None:
        with pytest.warns(prop.RoadDeviceWarning, match="EN 16272-3-1"):
            got = prop.sound_absorption_rating(np.ones(_BANDS), spectrum="railway")
        assert got.rating == pytest.approx(20.0)

    def test_an_unknown_spectrum_is_refused(self) -> None:
        with pytest.raises(ValueError, match="spectrum must be one of"):
            prop.sound_absorption_rating(np.zeros(_BANDS), spectrum="aircraft")
