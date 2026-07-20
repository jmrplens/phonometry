#  Copyright (c) 2026. Jose M. Requena-Plens
"""EN/ES language option for the environmental ``.plot()`` renderers."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry.environmental.wind_turbine_noise import wind_turbine_tonality


def _result() -> object:
    df = 2.0
    freqs = np.arange(440.0, 560.0 + df, df)
    levels = np.full(freqs.size, 30.0)
    levels[int(np.argmin(np.abs(freqs - 500.0)))] = 60.0
    return wind_turbine_tonality(levels, freqs)


def test_plot_default_is_english() -> None:
    ax = _result().plot()
    assert ax.get_xlabel() == "Frequency [Hz]"
    assert ax.get_ylabel() == "Level [dB]"
    plt.close("all")


def test_plot_spanish_labels() -> None:
    ax = _result().plot(language="es")
    assert ax.get_xlabel() == "Frecuencia [Hz]"
    assert ax.get_ylabel() == "Nivel [dB]"
    plt.close("all")


def test_plot_unknown_language_raises() -> None:
    result = _result()
    with pytest.raises(ValueError, match="Unknown language"):
        result.plot(language="xx")
    plt.close("all")
