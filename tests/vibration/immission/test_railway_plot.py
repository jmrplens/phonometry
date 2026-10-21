#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What the DIN 45672-2 figures say, in both languages.

The passage figure is read for the stretches it marks and the numbers it
draws, and the spectrum figure for the two curves of Figure 6, because a
figure that brackets the wrong stretch reads as a result and is not one.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry.vibration import immission as im

pytest.importorskip("matplotlib")

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt

FS_HZ = 2048


@pytest.fixture(scope="module")
def passage() -> im.TrainPassage:
    t = np.arange(12 * FS_HZ) / FS_HZ
    envelope = np.clip((t - 2.0) / 2.0, 0.0, 1.0) * np.clip((10.0 - t) / 2.0, 0.0, 1.0)
    record = envelope * (
        0.3 * np.sin(2.0 * math.pi * 40.0 * t) + 0.1 * np.sin(2.0 * math.pi * 63.0 * t)
    )
    return im.evaluate_train_passage(record, FS_HZ, t2_s=(3.0, 9.0))


def test_the_passage_figure_brackets_the_three_stretches(
    passage: im.TrainPassage,
) -> None:
    ax = passage.plot()
    labels = {text.get_text(): text.get_position()[0] for text in ax.texts}
    for index, (start, end) in enumerate(passage.intervals_s):
        assert labels[f"$T_{index + 1}$"] == pytest.approx(0.5 * (start + end))
    arrows = [child for child in ax.get_children() if hasattr(child, "arrow_patch")]
    spans = sorted(
        (arrow.xyann[0], arrow.xy[0]) for arrow in arrows if arrow.arrow_patch
    )
    assert spans == sorted(passage.intervals_s)
    plt.close("all")


def test_the_passage_figure_draws_the_running_rms_and_its_maximum(
    passage: im.TrainPassage,
) -> None:
    ax = passage.plot()
    running = next(line for line in ax.lines if "running" in line.get_label())
    assert np.allclose(running.get_ydata(), passage.running_rms_mm_s)
    maximum = next(line for line in ax.lines if "max" in line.get_label())
    assert maximum.get_ydata()[0] == pytest.approx(passage.running_rms_max_mm_s)
    assert "0.0" in ax.get_title()
    plt.close("all")


def test_the_spectrum_figure_is_figure_6(passage: im.TrainPassage) -> None:
    ax = passage.plot_spectrum(linewidth=2.5, label="mine")
    first, second = ax.lines[:2]
    assert np.allclose(first.get_ydata(), passage.band_max_levels_db)
    assert first.get_linewidth() == pytest.approx(2.5)
    assert first.get_label() == "mine"
    assert np.allclose(second.get_ydata(), passage.band_interval_levels_db[1])
    ticks = [tick.get_text() for tick in ax.get_xticklabels()]
    assert ticks[:3] == ["4", "5", "6.3"]
    plt.close("all")


def test_the_figures_speak_spanish(passage: im.TrainPassage) -> None:
    ax = passage.plot(language="es")
    assert ax.get_xlabel() == "Tiempo [s]"
    assert ax.get_ylabel() == "Velocidad [mm/s]"
    assert "Paso de tren" in ax.get_title()
    assert any("eficaz móvil" in line.get_label() for line in ax.lines)
    plt.close("all")
    ax = passage.plot_spectrum(language="es")
    ticks = [tick.get_text() for tick in ax.get_xticklabels()]
    assert "6,3" in ticks
    assert ax.get_ylabel().startswith("Nivel de velocidad")
    plt.close("all")


def test_an_unknown_language_is_refused(passage: im.TrainPassage) -> None:
    with pytest.raises(ValueError, match="language"):
        passage.plot(language="de")
    with pytest.raises(ValueError, match="language"):
        passage.plot_spectrum(language="de")
