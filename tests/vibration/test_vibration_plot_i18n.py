#  Copyright (c) 2026. Jose M. Requena-Plens
"""EN/ES language option of the vibration ``.plot()`` renderers."""

from __future__ import annotations

import numpy as np
import pytest

from phonometry import sdof_mobility_result


def _result():
    return sdof_mobility_result(np.linspace(1.0, 50.0, 200), 2.0, 8000.0, 5.0)


def test_spanish_labels() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    res = _result()

    ax_en = res.plot(language="en")
    assert ax_en.get_xlabel() == "Frequency [Hz]"
    assert ax_en.get_title() == "ISO 7626-1 mechanical mobility"

    ax_es = res.plot(language="es")
    assert ax_es.get_xlabel() == "Frecuencia [Hz]"
    assert ax_es.get_title() == "ISO 7626-1 movilidad mecánica"


def test_unknown_language_raises() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    result = _result()
    with pytest.raises(ValueError, match="Unknown language"):
        result.plot(language="xx")
