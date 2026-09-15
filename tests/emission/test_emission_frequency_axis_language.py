#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The IEC 61043 class figure hands the caller's language to the frequency formatter.

:func:`~phonometry._i18n.localize_axes` cannot reach tick labels installed as
fixed strings, so the octave labels are written by ``format_frequency_axis``
and by nothing else: a renderer that does not pass its ``language`` on draws
``31.5`` in a Spanish figure. Table 2 runs from 50 Hz to 6.3 kHz, where no
octave label carries a decimal, so the labels read the same in both languages;
the test watches the language the renderer hands to the formatter instead.
"""

from __future__ import annotations

from typing import Any

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import emission
from phonometry._plot import emission as emission_plot


@pytest.mark.parametrize("language", ["es", "en"])
def test_the_class_figure_hands_its_language_to_the_formatter(
    monkeypatch: pytest.MonkeyPatch, language: str
) -> None:
    real = emission_plot.format_frequency_axis
    seen: list[str] = []

    def recording(*args: Any, **kwargs: Any) -> None:
        seen.append(kwargs.get("language", "en"))
        real(*args, **kwargs)

    monkeypatch.setattr(emission_plot, "format_frequency_axis", recording)
    frequencies, class1, _class2 = emission.residual_index_limits("instrument")
    verdict = emission.verify_intensity_class(
        np.asarray(class1, dtype=np.float64) + 1.0, frequencies
    )
    verdict.plot(language=language)
    plt.close("all")
    assert seen == [language]
