#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for :mod:`phonometry.room_noise` (ANSI/ASA S12.2-2019 NC and RC Mark II).

The methods are validated against the standard's own tabulated curves: feeding
an NC curve of Table 1 back through the tangency method returns its NC value,
and the generated RC Mark II curves reproduce Table D.1 digit for digit. The
spectral tags (neutral / rumble / hiss) are checked against the deviation
rules of clause D.3.
"""

from __future__ import annotations

import numpy as np
import pytest
from reference_data import (
    ANSIS12_2_NC40_SELF,
    ANSIS12_2_RC31_63HZ,
    ANSIS12_2_RC35_LMF,
)

from phonometry import room_noise as rn


def test_octave_band_layout() -> None:
    assert rn.OCTAVE_BANDS.size == 10
    assert rn.OCTAVE_BANDS[0] == 16.0
    assert rn.OCTAVE_BANDS[-1] == 8000.0
    assert rn.NC_CURVES.shape == (rn.NC_INDICES.size, 10)


def test_nc_table_row_matches_standard() -> None:
    # Table 1: the NC-30 curve, 16 Hz - 8000 Hz.
    np.testing.assert_allclose(
        rn.nc_curve(30.0), [81, 68, 57, 48, 41, 35, 32, 29, 28, 27]
    )


@pytest.mark.parametrize("index", [15.0, 25.0, ANSIS12_2_NC40_SELF, 50.0, 70.0])
def test_nc_curve_returns_its_own_rating(index: float) -> None:
    # Feeding an NC curve back through the tangency method returns its value.
    result = rn.noise_criterion(rn.nc_curve(index))
    assert result.rating == pytest.approx(index, abs=1e-9)


def test_nc_governing_band_and_monotonicity() -> None:
    # Raising one band above the NC-50 curve lifts the rating and makes that
    # band the governing one.
    levels = rn.nc_curve(50.0).copy()
    levels[3] += 3.0  # 125 Hz band.
    result = rn.noise_criterion(levels)
    assert result.rating > 50.0
    assert result.governing_frequency == 125.0


def test_nc_out_of_range_curve_raises() -> None:
    with pytest.raises(ValueError, match="tabulated range"):
        rn.nc_curve(80.0)


def test_rc_curves_match_table_d1() -> None:
    # Table D.1, generated from the -5 dB/octave rule (Annex D).
    expected = {
        25.0: [55, 55, 45, 40, 35, 30, 25, 20, 15, 10],
        30.0: [55, 55, 50, 45, 40, 35, 30, 25, 20, 15],
        31.0: [56, 56, 51, 46, 41, 36, 31, 26, 21, 16],
        38.0: [63, 63, 58, 53, 48, 43, 38, 33, 28, 23],
        50.0: [75, 75, 70, 65, 60, 55, 50, 45, 40, 35],
    }
    for index, row in expected.items():
        np.testing.assert_allclose(rn.rc_curve(index), row)
    # Pin the inline Table D.1 transcription to the shared reference_data
    # constant used by the CI conformance report (RC-31 curve at 63 Hz).
    assert expected[31.0][2] == ANSIS12_2_RC31_63HZ


def test_rc_low_frequency_floor() -> None:
    # The 31.5 Hz level never drops below 55 dB and 16 Hz equals 31.5 Hz.
    curve = rn.rc_curve(25.0)
    assert curve[1] == 55.0
    assert curve[0] == curve[1]


def test_rc_neutral_spectrum() -> None:
    result = rn.room_criterion(rn.rc_curve(35.0))
    assert result.rating == 35
    assert result.lmf == pytest.approx(ANSIS12_2_RC35_LMF)
    assert result.classification == "N"
    assert result.label == "RC-35(N)"


def test_rc_rumble_tag() -> None:
    # A low band exceeding the RC curve by more than 5 dB -> rumble.
    levels = rn.rc_curve(35.0).copy()
    levels[4] += 8.0  # 250 Hz.
    assert rn.room_criterion(levels).classification == "R"


def test_rc_hiss_tag() -> None:
    # A high band exceeding the RC curve by more than 3 dB -> hiss.
    levels = rn.rc_curve(35.0).copy()
    levels[8] += 5.0  # 4000 Hz.
    assert rn.room_criterion(levels).classification == "H"


def test_rc_combined_rumble_and_hiss() -> None:
    levels = rn.rc_curve(35.0).copy()
    levels[4] += 8.0
    levels[8] += 5.0
    assert rn.room_criterion(levels).classification == "RH"


def test_rc_within_tolerance_stays_neutral() -> None:
    # Deviations of exactly the 5 dB / 3 dB tolerances are not exceedances.
    levels = rn.rc_curve(35.0).copy()
    levels[4] += 5.0   # low band, +5 dB (not > 5).
    levels[8] += 3.0   # high band, +3 dB (not > 3).
    assert rn.room_criterion(levels).classification == "N"


def test_subset_by_frequency() -> None:
    # A subset of the octave bands may be supplied with explicit frequencies.
    freqs = [500.0, 1000.0, 2000.0, 4000.0, 8000.0]
    levels = [40.0, 35.0, 30.0, 27.0, 22.0]
    result = rn.noise_criterion(levels, freqs)
    assert result.rating == pytest.approx(35.0, abs=1e-9)


def test_rc_requires_mid_frequency_bands() -> None:
    # Without 500/1000/2000 Hz the RC rating cannot be computed.
    with pytest.raises(ValueError, match="mid-frequency"):
        rn.room_criterion([50.0, 45.0], [63.0, 125.0])


def test_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError, match="octave-band values"):
        rn.noise_criterion([1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match="same shape"):
        rn.noise_criterion([1.0, 2.0], [63.0])
    with pytest.raises(ValueError, match="not one of"):
        rn.noise_criterion([50.0], [777.0])
    with pytest.raises(ValueError, match="1-D vector"):
        rn.noise_criterion(np.zeros((2, 10)))
    with pytest.raises(ValueError, match="no valid"):
        rn.noise_criterion([], [])


def test_result_fields_and_copy() -> None:
    result = rn.room_criterion(rn.rc_curve(40.0))
    assert result.frequencies.shape == (10,)
    assert result.levels.shape == (10,)
    assert result.reference_curve.shape == (10,)
    # The returned frequencies must not alias the module constant.
    result.frequencies[0] = 0.0
    assert rn.OCTAVE_BANDS[0] == 16.0


def test_nc_plot_returns_axes() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ax = rn.noise_criterion(rn.nc_curve(40.0)).plot()
    assert isinstance(ax, plt.Axes)
    plt.close("all")


def test_rc_plot_returns_axes() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ax = rn.room_criterion(rn.rc_curve(35.0)).plot()
    assert isinstance(ax, plt.Axes)
    plt.close("all")
