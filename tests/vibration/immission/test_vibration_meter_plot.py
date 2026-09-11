#  Copyright (c) 2026. Jose Manuel Requena Plens
"""What the DIN 45669-1 figures say, in both languages.

Looking at a renderer is not covering it: these assert the numbers the artists
carry, because a figure that draws the wrong tolerance band or the wrong
guideline line is a figure that reads as a verdict and is not one.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from phonometry.vibration import immission as im

pytest.importorskip("matplotlib")

import matplotlib as mpl

mpl.use("Agg")

FS_HZ = 2048.0


def _record() -> np.ndarray:
    """Two seconds of a 24 Hz burst inside a 70 s record, so two clock intervals."""
    t = np.arange(int(70.0 * FS_HZ)) / FS_HZ
    record = np.zeros_like(t)
    burst = (t > 20.0) & (t < 22.0)
    record[burst] = (
        4.0 * np.sin(2.0 * math.pi * 24.0 * t[burst]) * np.hanning(int(burst.sum()))
    )
    return record


def test_reading_figure_draws_the_two_numbers_a_meter_displays() -> None:
    """KB_Fmax and KB_FTm as lines, and one marker per clock interval."""
    reading = im.measure_vibration_immission(_record(), FS_HZ)
    ax = reading.plot()
    horizontals = [
        line.get_ydata()[0]
        for line in ax.lines
        if len(set(np.asarray(line.get_ydata()).tolist())) == 1
    ]
    assert reading.kbf_max == pytest.approx(max(horizontals))
    assert any(value == pytest.approx(reading.kbf_takt_rms) for value in horizontals)
    markers = [line for line in ax.lines if line.get_marker() == "s"]
    assert len(markers) == 1
    assert markers[0].get_ydata() == pytest.approx(reading.takt_maxima)
    assert ax.get_ylabel().startswith("Weighted vibration severity")


def test_reading_figure_of_a_record_with_no_whole_clock_interval() -> None:
    """A short record has no clock maxima, so the figure draws none.

    The renderer has to survive it: 5.1.6.4 drops a part-interval, and a
    twenty-second measurement is an ordinary thing to plot.
    """
    short = _record()[: int(20.0 * FS_HZ)]
    ax = im.measure_vibration_immission(short, FS_HZ).plot()
    assert not [line for line in ax.lines if line.get_marker() == "s"]


def test_verification_figure_draws_the_band_from_the_tables() -> None:
    """The shaded region is Tables 2 and 3, not a fixed number of per cent."""
    freqs = np.array([1.0, 2.0, 4.0, 8.0, 16.0, 31.5, 63.0, 80.0])
    measured = np.abs(im.kb_weighting_response(freqs)) * 1.02
    measured[5] *= 1.15
    result = im.verify_vibration_meter(freqs, measured)
    ax = result.plot()
    assert not result.passes
    assert "FAIL" in ax.get_title()
    band = ax.collections[0].get_paths()[0].vertices
    lower_edge = band[:, 1].min()
    upper_edge = band[:, 1].max()
    assert lower_edge == pytest.approx(-result.lower_percent.max())
    assert upper_edge == pytest.approx(result.upper_percent.max())
    outside = [line for line in ax.lines if line.get_marker() == "X"]
    assert len(outside) == 1
    assert outside[0].get_xdata() == pytest.approx([31.5])


def test_assessment_figure_draws_the_guideline_both_ways() -> None:
    """Table E.2 is one number, and the quantity judged is an absolute value."""
    result = im.assess_short_term_vibration(
        _record(), FS_HZ, building_class="residential"
    )
    ax = result.plot()
    horizontals = sorted(
        line.get_ydata()[0]
        for line in ax.lines
        if len(set(np.asarray(line.get_ydata()).tolist())) == 1
    )
    assert horizontals == pytest.approx([-5.0, 5.0])
    assert "PASS" in ax.get_title()


@pytest.mark.parametrize(
    ("language", "title_fragment", "ylabel"),
    [
        ("en", "against DIN 45669-1", "Response deviation $F(f)$ [%]"),
        ("es", "frente a DIN 45669-1", "Desviación de la respuesta $F(f)$ [%]"),
    ],
)
def test_verification_figure_speaks_both_languages(
    language: str, title_fragment: str, ylabel: str
) -> None:
    """The Spanish edition translates the prose and keeps the symbols."""
    freqs = np.array([1.0, 16.0, 31.5, 80.0])
    result = im.verify_vibration_meter(freqs, np.abs(im.kb_weighting_response(freqs)))
    ax = result.plot(language=language)
    assert title_fragment in ax.get_title()
    assert ax.get_ylabel() == ylabel


def test_spanish_labels_of_the_other_two_figures() -> None:
    """The reading and the assessment, in Spanish."""
    reading = im.measure_vibration_immission(_record(), FS_HZ)
    ax = reading.plot(language="es")
    assert ax.get_xlabel() == "Tiempo [s]"
    assert "Inmisión de vibración" in ax.get_title()
    assert "rango edificios" in ax.get_title()

    assessment = im.assess_short_term_vibration(
        _record(), FS_HZ, building_class="sensitive"
    )
    ax_es = assessment.plot(language="es")
    assert ax_es.get_ylabel() == "Velocidad de valoración $v_B$ [mm/s]"
    assert "especialmente sensible" in ax_es.get_title()
    assert "CUMPLE" in ax_es.get_title()
