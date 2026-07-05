#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for filter design helpers and response plotting utilities.
"""

from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np
import pytest
from scipy import signal as sg

from pyoctaveband import OctaveFilterBank, octavefilter
from pyoctaveband.filter_design import _design_sos_filter, _showfilter


def _edge_gains_db(bank: OctaveFilterBank, band_idx: int) -> tuple[float, float]:
    """Measured gain (dB) at the band's lower and upper edge frequencies."""
    fsd = bank.fs / bank.factor[band_idx]
    w, h = sg.sosfreqz(bank.sos[band_idx], worN=2**16, fs=fsd)
    mag = 20 * np.log10(np.abs(h) + 1e-300)

    def gain_at(f: float) -> float:
        return float(mag[np.argmin(np.abs(w - f))])

    return gain_at(bank.freq_d[band_idx]), gain_at(bank.freq_u[band_idx])


@pytest.mark.parametrize("fraction", [1, 3])
def test_cheby2_minus3db_at_band_edges(fraction: float) -> None:
    """
    Verify cheby2 places its -3 dB points at the ANSI band edges.

    **Purpose:**
    ``Wn`` in Chebyshev II is the STOPBAND edge. Passing the band edges
    directly attenuated them by the full ``attenuation`` (-60 dB) instead
    of ~-3 dB, violating ANSI S1.11 band definitions.

    **Verification:**
    - Gain at every band's lower and upper edge is -3 dB (+/- 0.4 dB).
    """
    bank = OctaveFilterBank(
        fs=48000, fraction=fraction, order=6,
        limits=[100, 5000], filter_type="cheby2", attenuation=60.0,
    )
    for idx in range(bank.num_bands):
        g_lo, g_hi = _edge_gains_db(bank, idx)
        assert g_lo == pytest.approx(-3.01, abs=0.4), f"band {idx} lower edge: {g_lo:.2f} dB"
        assert g_hi == pytest.approx(-3.01, abs=0.4), f"band {idx} upper edge: {g_hi:.2f} dB"


def test_cheby2_broadband_levels_match_butter() -> None:
    """
    Verify cheby2 band levels agree with butter for broadband noise.

    **Purpose:**
    With the stopband placed on the band edges, cheby2 underestimated
    white-noise band levels by ~2.8 dB versus butter.

    **Verification:**
    - Max deviation between cheby2 and butter band levels < 0.5 dB.
    """
    rng = np.random.default_rng(42)
    x = rng.standard_normal(48000 * 5)
    spl_b, _ = octavefilter(x, 48000, fraction=3, filter_type="butter", limits=[100, 10000])
    spl_c, _ = octavefilter(x, 48000, fraction=3, filter_type="cheby2", limits=[100, 10000])
    diff = np.asarray(spl_c) - np.asarray(spl_b)
    assert np.abs(diff).max() < 0.5, f"max deviation {np.abs(diff).max():.2f} dB"


@pytest.mark.parametrize("fraction", [1, 3])
def test_bessel_minus3db_at_band_edges(fraction: float) -> None:
    """
    Verify bessel places its -3 dB points at the ANSI band edges.

    **Purpose:**
    ``norm="phase"`` shifted the -3 dB crossings inward (~-10 dB at the
    edges); ``norm="mag"`` defines them exactly at ``Wn``.

    **Verification:**
    - Gain at every band's lower and upper edge is -3 dB (+/- 0.6 dB).
    """
    bank = OctaveFilterBank(
        fs=48000, fraction=fraction, order=6,
        limits=[100, 5000], filter_type="bessel",
    )
    for idx in range(bank.num_bands):
        g_lo, g_hi = _edge_gains_db(bank, idx)
        assert g_lo == pytest.approx(-3.01, abs=0.6), f"band {idx} lower edge: {g_lo:.2f} dB"
        assert g_hi == pytest.approx(-3.01, abs=0.6), f"band {idx} upper edge: {g_hi:.2f} dB"


def test_showfilter_saves_shows_and_noops(tmp_path) -> None:
    """Verify _showfilter handles save, show, and no-output branches."""
    fs = 8000
    sos = [np.array([[1, 0, 0, 1, 0, 0]])]
    freq = [1000.0]
    freq_u = [1414.0]
    freq_d = [707.0]
    factor = np.array([1])
    plot_path = tmp_path / "test_plot_coverage.png"

    _showfilter(sos, freq, freq_u, freq_d, fs, factor, show=False, plot_file=str(plot_path))
    assert plot_path.exists()

    with patch.object(plt, "show") as mock_show:
        _showfilter(sos, freq, freq_u, freq_d, fs, factor, show=True, plot_file=None)
        mock_show.assert_called_once()

    _showfilter(sos, freq, freq_u, freq_d, fs, factor, show=False, plot_file=None)


def test_all_filter_architectures_design() -> None:
    """Verify all supported architectures produce SOS coefficients."""
    filter_types = ["butter", "cheby1", "cheby2", "ellip", "bessel"]

    for filter_type in filter_types:
        sos = _design_sos_filter(
            freq=[1000],
            freq_d=[707],
            freq_u=[1414],
            fs=48000,
            order=4,
            factor=np.array([1]),
            filter_type=filter_type,
            ripple=1.0,
            attenuation=40.0,
        )
        assert len(sos) == 1
        assert len(sos[0]) > 0


def test_design_sos_with_internal_plot(tmp_path) -> None:
    """Verify _design_sos_filter forwards plot output to _showfilter."""
    plot_path = tmp_path / "test_design_plot.png"

    _design_sos_filter(
        [1000],
        [707],
        [1414],
        8000,
        2,
        np.array([1]),
        "butter",
        0.1,
        60,
        plot_file=str(plot_path),
    )

    assert plot_path.exists()