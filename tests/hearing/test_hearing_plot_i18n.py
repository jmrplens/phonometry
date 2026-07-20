#  Copyright (c) 2026. Jose M. Requena-Plens
"""EN/ES language option of the hearing ``.plot()`` renderers."""

from __future__ import annotations

import pytest

from phonometry import age_threshold


def test_spanish_labels() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    res = age_threshold(60.0, "male", fractile=0.9)

    ax_en = res.plot(language="en")
    assert ax_en.get_ylabel() == "Threshold deviation from age 18 [dB]"

    ax_es = res.plot(language="es")
    assert ax_es.get_ylabel() == "Desviación del umbral respecto a 18 años [dB]"
    assert "umbral de audición" in ax_es.get_title()


def test_unknown_language_raises() -> None:
    pytest.importorskip("matplotlib")
    import matplotlib

    matplotlib.use("Agg")
    result = age_threshold(60.0, "male")
    with pytest.raises(ValueError, match="Unknown language"):
        result.plot(language="xx")
