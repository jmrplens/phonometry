#  Copyright (c) 2026. Jose M. Requena-Plens
"""Tests for :mod:`phonometry.hearing.sii` (Speech Intelligibility Index, ANSI S3.5-1997).

The one-third-octave-band procedure is validated against the standard's own
tabulated constants (the Table 3 band-importance function sums to one) and its
masking intermediates (the equivalent masking spectrum level ``Zi`` of the
standard normal-effort spectrum in quiet, used here as reference values), and
against the known index for speech in quiet with normal hearing.
"""

from __future__ import annotations

import numpy as np
import pytest
from reference_data import (
    ANSIS3_5_BAND_IMPORTANCE_SUM,
    ANSIS3_5_LOUD_1KHZ,
    ANSIS3_5_STANDARD_QUIET,
)

from phonometry.hearing import sii


def test_band_importance_sums_to_one() -> None:
    # ANSI S3.5-1997 Table 3: the band-importance function is normalised.
    assert sii.BAND_IMPORTANCE.sum() == pytest.approx(
        ANSIS3_5_BAND_IMPORTANCE_SUM, abs=1e-12
    )
    assert sii.BAND_IMPORTANCE.size == 18
    np.testing.assert_allclose(
        sii.BAND_CENTERS,
        [160.0, 200.0, 250.0, 315.0, 400.0, 500.0, 630.0, 800.0, 1000.0,
         1250.0, 1600.0, 2000.0, 2500.0, 3150.0, 4000.0, 5000.0, 6300.0,
         8000.0],
    )


def test_sii_standard_speech_in_quiet() -> None:
    # Standard normal-effort spectrum, quiet field, normal hearing.
    result = sii.speech_intelligibility_index("normal")
    assert result.sii == pytest.approx(ANSIS3_5_STANDARD_QUIET, abs=5e-4)
    assert 0.0 <= result.sii <= 1.0


def test_masking_spectrum_matches_reference() -> None:
    # Equivalent masking spectrum level Zi for the standard spectrum in quiet
    # (reference values for the first four one-third-octave bands).
    result = sii.speech_intelligibility_index("normal")
    reference_zi = np.array([8.41, -1.6647, 0.7052, 0.3817])
    np.testing.assert_allclose(result.masking[:4], reference_zi, atol=1e-4)


def test_noise_reduces_index_monotonically() -> None:
    # More masking noise can only lower the index.
    quiet = sii.speech_intelligibility_index("normal").sii
    mild = sii.speech_intelligibility_index("normal", np.full(18, 20.0)).sii
    loud = sii.speech_intelligibility_index("normal", np.full(18, 40.0)).sii
    assert quiet > mild > loud >= 0.0


def test_hearing_loss_reduces_index() -> None:
    # A raised hearing threshold lifts the internal noise and lowers the index.
    normal = sii.speech_intelligibility_index("normal").sii
    impaired = sii.speech_intelligibility_index(
        "normal", threshold=np.full(18, 40.0)
    ).sii
    assert impaired < normal


def test_extreme_speech_level_stays_bounded() -> None:
    # The level-distortion factor is clipped to [0, 1], so even an absurdly loud
    # speech level cannot drive the audibility (or the index) negative.
    result = sii.speech_intelligibility_index(np.full(18, 200.0))
    assert np.all(result.band_audibility >= 0.0)
    assert 0.0 <= result.sii <= 1.0


def test_standard_speech_spectrum_values() -> None:
    spectrum = sii.standard_speech_spectrum("normal")
    assert spectrum[0] == pytest.approx(32.41)
    assert spectrum[8] == pytest.approx(25.01)
    assert spectrum[17] == pytest.approx(1.13)
    # A returned copy must not alias the module constant.
    spectrum[0] = 0.0
    assert sii.standard_speech_spectrum("normal")[0] == pytest.approx(32.41)


def test_vocal_effort_spectra_spot_values() -> None:
    # ANSI S3.5-1997 Table 3, cross-verified against reference implementations
    # (Google speech_intelligibility_index, R CRAN SII) at 1 kHz (band 8).
    assert sii.standard_speech_spectrum("raised")[8] == pytest.approx(33.86)
    assert sii.standard_speech_spectrum("loud")[8] == pytest.approx(ANSIS3_5_LOUD_1KHZ)
    assert sii.standard_speech_spectrum("shout")[8] == pytest.approx(51.31)
    assert sii.VOCAL_EFFORTS == ("normal", "raised", "loud", "shout")


def test_vocal_effort_overall_level_increases() -> None:
    # The overall speech level grows with vocal effort (Table 3): reconstruct
    # each spectrum's overall free-field SPL and check it is monotone.
    f = sii.BAND_CENTERS
    bw = (2.0 ** (1 / 6) - 2.0 ** (-1 / 6)) * f
    overall = [
        10.0 * np.log10(
            np.sum(10.0 ** ((sii.standard_speech_spectrum(e) + 10 * np.log10(bw)) / 10))
        )
        for e in sii.VOCAL_EFFORTS
    ]
    assert overall == sorted(overall)  # normal < raised < loud < shout
    # Matches the known ANSI vocal-effort overall levels (dB SPL).
    assert overall[0] == pytest.approx(62.35, abs=0.1)
    assert overall[1] == pytest.approx(68.3, abs=0.1)
    assert overall[2] == pytest.approx(74.86, abs=0.1)
    assert overall[3] == pytest.approx(82.36, abs=0.1)


def test_higher_effort_raises_index_in_noise() -> None:
    # In a fixed noise, speaking louder improves intelligibility.
    noise = np.full(18, 40.0)
    indices = [
        sii.speech_intelligibility_index(e, noise).sii for e in sii.VOCAL_EFFORTS
    ]
    assert indices == sorted(indices)
    assert indices[3] > indices[0]


def test_custom_speech_spectrum_accepted() -> None:
    result = sii.speech_intelligibility_index(np.full(18, 40.0))
    assert 0.0 <= result.sii <= 1.0
    assert result.speech_spectrum.shape == (18,)


def test_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError, match="18"):
        sii.speech_intelligibility_index([1.0, 2.0, 3.0])
    with pytest.raises(ValueError, match="18"):
        sii.speech_intelligibility_index("normal", noise_spectrum=[1.0, 2.0])
    with pytest.raises(ValueError, match="18"):
        sii.speech_intelligibility_index("normal", threshold=np.zeros(5))
    with pytest.raises(ValueError, match="vocal_effort"):
        sii.standard_speech_spectrum("whisper")


def test_result_fields_present() -> None:
    result = sii.speech_intelligibility_index("normal")
    assert result.band_audibility.shape == (18,)
    assert result.band_importance.shape == (18,)
    assert result.disturbance.shape == (18,)
    assert result.masking.shape == (18,)
    np.testing.assert_allclose(result.frequencies, sii.BAND_CENTERS)


def test_plot_returns_axes() -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ax = sii.speech_intelligibility_index("normal").plot()
    assert isinstance(ax, plt.Axes)
    plt.close("all")
