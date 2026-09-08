#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The audiometric zero of a supra-aural earphone (ISO 389-1:1998).

Oracles, read from the rendered printed pages of the standard:

- Table 1 (PDF page 8, printed folio 8): the reference levels of the Beyer
  DT 48 with a flat cushion and of the Telephonics TDH 39 with the MX 41/AR
  cushion, both on an acoustic coupler to IEC 60303;
- Table 2 (PDF page 10, printed folio 10): the levels of any other
  supra-aural earphone meeting the four requirements of 4.3, on an
  artificial ear to IEC 60318.

Both tables carry a note that their values are rounded to the nearest half
decibel, which is what makes the whole-and-half pattern below a check on the
transcription rather than a coincidence.
"""

from __future__ import annotations

import numpy as np
import pytest

from phonometry import hearing as h


class TestPrintedTables:
    """The three columns, digit for digit."""

    def test_the_twenty_three_frequencies(self) -> None:
        assert h.RETSPL_FREQUENCIES_HZ.size == 23
        assert h.RETSPL_FREQUENCIES_HZ[0] == pytest.approx(125.0)
        assert h.RETSPL_FREQUENCIES_HZ[-1] == pytest.approx(8000.0)
        # The intermediate frequencies an audiometer may offer are in the
        # table too, which is what makes it wider than ISO 389-7's eleven.
        for extra in (160.0, 315.0, 750.0, 1500.0, 3150.0, 6300.0):
            assert np.isclose(h.RETSPL_FREQUENCIES_HZ, extra).any()

    def test_table_1_dt48(self) -> None:
        got = h.earphone_reference_level("DT 48")
        np.testing.assert_allclose(
            got,
            [
                47.5,
                40.5,
                34.0,
                28.5,
                23.0,
                18.5,
                14.5,
                11.5,
                9.5,
                9.0,
                8.0,
                7.5,
                7.5,
                7.5,
                8.0,
                7.0,
                6.0,
                6.0,
                5.5,
                7.0,
                8.0,
                9.0,
                14.5,
            ],
        )

    def test_table_1_tdh39(self) -> None:
        got = h.earphone_reference_level("TDH 39")
        np.testing.assert_allclose(
            got,
            [
                45.0,
                37.5,
                31.5,
                25.5,
                20.0,
                15.0,
                11.5,
                8.5,
                7.5,
                7.0,
                7.0,
                6.5,
                6.5,
                7.0,
                9.0,
                9.5,
                10.0,
                10.0,
                9.5,
                13.0,
                15.5,
                15.0,
                13.0,
            ],
        )

    def test_table_2_other_supra_aural(self) -> None:
        got = h.earphone_reference_level("other supra-aural")
        np.testing.assert_allclose(
            got,
            [
                45.0,
                38.5,
                32.5,
                27.0,
                22.0,
                17.0,
                13.5,
                10.5,
                9.0,
                8.5,
                7.5,
                7.5,
                7.5,
                8.0,
                9.0,
                10.5,
                11.5,
                11.5,
                12.0,
                11.0,
                16.0,
                21.0,
                15.5,
            ],
        )

    def test_every_value_is_a_whole_or_half_decibel(self) -> None:
        for earphone in h.EARPHONES:
            values = h.earphone_reference_level(earphone)
            np.testing.assert_allclose(values * 2.0, np.round(values * 2.0))

    def test_the_coupler_belongs_to_the_earphone(self) -> None:
        # The two named models are calibrated on a coupler, everything else
        # on an artificial ear, which is why there are two tables.
        assert "60303" in h.EARPHONE_COUPLERS["DT 48"]
        assert "60303" in h.EARPHONE_COUPLERS["TDH 39"]
        assert "60318" in h.EARPHONE_COUPLERS["other supra-aural"]
        assert set(h.EARPHONE_COUPLERS) == set(h.EARPHONES)


class TestShape:
    """What the curves have to look like, whatever the transcription is."""

    def test_the_low_end_is_the_expensive_one(self) -> None:
        # Every earphone needs tens of decibels at 125 Hz for a threshold and
        # single digits around 1 kHz: that is the shape of the ear, not of
        # the earphone.
        for earphone in h.EARPHONES:
            values = h.earphone_reference_level(earphone)
            assert values[0] > 40.0
            assert values[10] < 10.0

    def test_the_two_coupler_models_differ_where_the_cushion_does(self) -> None:
        dt48 = h.earphone_reference_level("DT 48")
        tdh39 = h.earphone_reference_level("TDH 39")
        # The flat cushion of the DT 48 needs more level low down and less up
        # high than the MX 41/AR of the TDH 39.
        assert dt48[0] > tdh39[0]
        assert dt48[-1] > tdh39[-1]
        assert dt48[18] < tdh39[18]  # 4 kHz


class TestHearingLevel:
    """dB HL is dB SPL measured from the audiometric zero, and nothing else."""

    def test_zero_hearing_level_is_the_reference_itself(self) -> None:
        zeros = np.zeros(h.RETSPL_FREQUENCIES_HZ.size)
        np.testing.assert_allclose(
            h.hearing_level_to_coupler_spl(zeros, "TDH 39"),
            h.earphone_reference_level("TDH 39"),
        )

    def test_a_loss_is_a_decibel_for_a_decibel(self) -> None:
        got = h.hearing_level_to_coupler_spl([40.0], "TDH 39", [4000.0])
        assert got[0] == pytest.approx(9.5 + 40.0)

    def test_an_audiogram_of_its_own_frequencies(self) -> None:
        freqs = [500.0, 1000.0, 2000.0, 4000.0]
        audiogram = [10.0, 15.0, 30.0, 55.0]
        got = h.hearing_level_to_coupler_spl(audiogram, "DT 48", freqs)
        np.testing.assert_allclose(got, [24.5, 23.0, 38.0, 60.5])

    def test_a_mismatched_audiogram_is_refused(self) -> None:
        with pytest.raises(ValueError, match="covers 2 frequency"):
            h.hearing_level_to_coupler_spl([10.0], "TDH 39", [500.0, 1000.0])


class TestRefusals:
    """What the two functions will not answer."""

    def test_an_unknown_earphone(self) -> None:
        with pytest.raises(ValueError, match="earphone must be one of"):
            h.earphone_reference_level("HDA 200")

    def test_a_frequency_the_table_does_not_carry(self) -> None:
        with pytest.raises(ValueError, match="not an ISO 389-1 test frequency"):
            h.earphone_reference_level("TDH 39", [440.0])

    def test_the_iso_389_7_frequencies_are_a_different_set(self) -> None:
        # 8 kHz is in both; the ISO 389-7 table has no 6300 Hz and this one
        # has no 12,5 kHz, so neither is a subset of the other by accident.
        assert np.isclose(h.RETSPL_FREQUENCIES_HZ, 8000.0).any()
        assert not np.isclose(h.AUDIOMETRIC_FREQUENCIES, 6300.0).any()
