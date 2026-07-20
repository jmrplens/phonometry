#  Copyright (c) 2026. Jose M. Requena-Plens
"""EN/ES language option for the underwater ``.plot()`` renderers."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

from phonometry.underwater.ocean_ambient_noise import ocean_ambient_noise
from phonometry.underwater.sonar_equation import passive_sonar_equation


def _result() -> object:
    return passive_sonar_equation(140.0, 80.0, 60.0, directivity_index=10.0,
                                  detection_threshold=5.0)


def test_plot_default_is_english() -> None:
    ax = _result().plot()
    assert ax.get_title() == "Sonar equation"
    assert ax.get_xlabel() == "Transmission loss [dB]"
    assert ax.get_ylabel() == "Signal excess [dB]"
    plt.close("all")


def test_plot_spanish_labels() -> None:
    ax = _result().plot(language="es")
    assert ax.get_title() == "Ecuación del sonar"
    assert ax.get_ylabel() == "Exceso de señal [dB]"
    plt.close("all")


def test_plot_unknown_language_raises() -> None:
    result = _result()
    with pytest.raises(ValueError, match="Unknown language"):
        result.plot(language="xx")
    plt.close("all")


def test_ambient_noise_legend_localized() -> None:
    # A legend-heavy renderer: the composite curve plus its wind/thermal
    # components. Guards that every legend entry is localized (the composite
    # "Total"/"wind"/"thermal" labels), not only the axis titles.
    result = ocean_ambient_noise([100.0, 1000.0, 10000.0], wind_speed_knots=15.0)
    ax = result.plot(language="es")
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert any(text.startswith("Total") for text in labels)
    assert "Viento" in labels
    assert "Térmico" in labels
    assert not any("Wind" in text or "Thermal" in text for text in labels)
    plt.close("all")
