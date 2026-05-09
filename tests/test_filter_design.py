#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Tests for filter design helpers and response plotting utilities.
"""

from unittest.mock import patch

import matplotlib.pyplot as plt
import numpy as np

from pyoctaveband.filter_design import _design_sos_filter, _showfilter


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