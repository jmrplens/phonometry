#  Copyright (c) 2026. Jose Manuel Requena Plens
"""EN/ES language option for the aircraft ``.plot()`` renderers."""

from __future__ import annotations

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry.aircraft.atmospheric_absorption import band_attenuation_arp5534


def _result() -> object:
    f = np.array([100.0, 1000.0, 4000.0, 8000.0])
    return band_attenuation_arp5534(
        f, 2000.0, temperature_c=25.0, relative_humidity_percent=70.0
    )


def test_plot_default_is_english() -> None:
    ax = _result().plot()
    assert ax.get_xlabel() == "Frequency [Hz]"
    assert ax.get_ylabel() == "Attenuation [dB]"
    assert ax.get_title() == "Aircraft atmospheric absorption (SAE ARP 5534)"
    plt.close("all")


def test_plot_spanish_labels() -> None:
    ax = _result().plot(language="es")
    assert ax.get_ylabel() == "Atenuación [dB]"
    assert ax.get_title() == "Absorción atmosférica de aeronaves (SAE ARP 5534)"
    plt.close("all")


def test_plot_unknown_language_raises() -> None:
    result = _result()
    with pytest.raises(ValueError, match="Unknown language"):
        result.plot(language="xx")
    plt.close("all")
