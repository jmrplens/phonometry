#  Copyright (c) 2026. Jose Manuel Requena Plens

"""The frequency labels of the psychoacoustics figures follow the caller's language.

:func:`~phonometry._i18n.localize_axes` cannot reach tick labels installed as
fixed strings, so the octave labels of these figures are written by
``format_frequency_axis`` and by nothing else: a renderer that does not pass
its ``language`` on draws ``31.5`` in a Spanish figure. The figures below span
31,5 Hz, the lowest octave centre whose label carries a decimal, because a
label without one proves nothing.

The ECMA-418-1 tone assessment is the exception: its axis is pinned to the
89.1 Hz to 11.2 kHz range of interest, where no octave label carries a decimal,
so the labels read the same in both languages and the test watches the
language the renderer hands to the formatter instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from phonometry import psychoacoustics
from phonometry._plot import psychoacoustics as psychoacoustics_plot
from phonometry.psychoacoustics.quality.tone_audibility import ToneAudibilityResult

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from matplotlib.axes import Axes


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def _tick_labels(ax: Axes) -> list[str]:
    return [t.get_text() for t in ax.get_xticklabels() if t.get_text()]


def _tone_audibility_levels(language: str) -> Axes:
    """A 60 Hz tone, whose 100 Hz critical band runs from 10 Hz to 110 Hz."""

    def one(value: float) -> np.ndarray:
        return np.array([value])

    result = ToneAudibilityResult(
        tone_frequencies=one(60.0),
        tone_levels=one(60.0),
        mean_narrowband_levels=one(40.0),
        line_spacing=1.0,
        critical_bandwidths=one(100.0),
        lower_corners=one(10.0),
        upper_corners=one(110.0),
        critical_band_levels=one(50.0),
        masking_indices=one(-2.0),
        audibilities=one(12.0),
    )
    return result.plot(view="levels", language=language)


def _equal_loudness_contours(language: str) -> Axes:
    # ISO 226:2023 tabulates 20 Hz to 12.5 kHz.
    return psychoacoustics.equal_loudness_contours().plot(language=language)


_FIGURES: list[Callable[[str], Axes]] = [
    _tone_audibility_levels,
    _equal_loudness_contours,
]


@pytest.mark.parametrize("draw", _FIGURES, ids=lambda draw: draw.__name__[1:])
def test_the_frequency_labels_reach_spanish(draw: Callable[[str], Axes]) -> None:
    labels = _tick_labels(draw("es"))
    assert "31,5" in labels, labels
    assert all("." not in label for label in labels), labels


@pytest.mark.parametrize("draw", _FIGURES, ids=lambda draw: draw.__name__[1:])
def test_the_frequency_labels_are_unchanged_in_english(
    draw: Callable[[str], Axes],
) -> None:
    labels = _tick_labels(draw("en"))
    assert "31.5" in labels, labels
    assert all("," not in label for label in labels), labels


@pytest.mark.parametrize("language", ["es", "en"])
def test_the_tone_assessment_hands_its_language_to_the_formatter(
    monkeypatch: pytest.MonkeyPatch, language: str
) -> None:
    real = psychoacoustics_plot.format_frequency_axis
    seen: list[str] = []

    def recording(*args: Any, **kwargs: Any) -> None:
        seen.append(kwargs.get("language", "en"))
        real(*args, **kwargs)

    monkeypatch.setattr(psychoacoustics_plot, "format_frequency_axis", recording)
    assessment = psychoacoustics.ToneAssessment(1000.0, 10.0, 8.0, prominent=True)
    assessment.plot(language=language)
    assert seen == [language]
