#  Copyright (c) 2026. Jose Manuel Requena Plens

"""What the outdoor-propagation ``.plot()`` renderer draws (ISO 9613-2).

The octave-band attenuation is a sum of named terms, geometrical divergence,
atmospheric absorption, ground effect and screening, and the figure is a stacked
bar so a reader can see which term carries the band. That makes the plot
answerable to arithmetic: the signed heights of the four stacks must add up to
``A_total`` band by band, and the total line must be ``A_total`` itself. The
ground term is signed, so in a scenario with hard ground at both ends it is a
net *gain* at 63 Hz and its bar hangs below the axis, which is exactly the case
this test builds.

These are the content assertions. The generic plot contract lives in
``tests/test_result_plots.py``.
"""

from __future__ import annotations

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from result_factories import _outdoor


# --------------------------------------------------------------------------
# Outdoor attenuation breakdown (ISO 9613-2)
# --------------------------------------------------------------------------
def test_outdoor_plot_stacks_terms_to_total() -> None:
    res = _outdoor()
    ax = res.plot()
    n = res.frequencies.size
    # four stacked terms -> 4 bars per band; signed heights sum to a_total.
    assert len(ax.patches) == 4 * n
    heights = np.array([p.get_height() for p in ax.patches]).reshape(4, n)
    np.testing.assert_allclose(heights.sum(axis=0), res.a_total, atol=1e-9)
    # the ground term is a net gain (negative) at 63 Hz in this scenario.
    assert res.a_gr[0] < 0.0
    # the total line echoes a_total.
    np.testing.assert_allclose(ax.lines[0].get_ydata(), res.a_total)
    plt.close("all")


def test_road_device_plot_draws_the_bands_against_the_spectrum() -> None:
    """The rating plot carries both halves of the weighting.

    A single number comes out of two spectra, and the figure has to show
    them both or it explains nothing: the device's own per-band values as
    bars on the left axis, and the normalised traffic noise spectrum of
    EN 1793-3 as a line on a right axis. The title carries the reported
    integer and its category, since that is what a declaration prints.
    """
    from phonometry.environment import propagation as prop

    alpha = np.linspace(0.1, 0.9, len(prop.TRAFFIC_NOISE_BANDS_HZ))
    result = prop.sound_absorption_rating(alpha)

    fig, ax = plt.subplots()
    try:
        result.plot(ax=ax)
        bars = [p for p in ax.patches if p.get_height() != 0.0]
        assert len(bars) == len(prop.TRAFFIC_NOISE_BANDS_HZ)
        np.testing.assert_allclose([p.get_height() for p in bars], alpha)

        twin = next(other for other in ax.figure.axes if other is not ax)
        (line,) = twin.get_lines()
        np.testing.assert_allclose(
            line.get_ydata(), prop.NORMALISED_TRAFFIC_NOISE_SPECTRUM_DB
        )

        title = ax.get_title()
        assert str(result.reported) in title
        assert result.category in title
    finally:
        plt.close(fig)


@pytest.mark.parametrize(
    ("rating", "ylabel"),
    [
        ("absorption", "Coeficiente de absorción acústica"),
        ("insulation", "Índice de reducción acústica [dB]"),
    ],
)
def test_road_device_plot_speaks_spanish(rating: str, ylabel: str) -> None:
    """The laboratory ratings label their axes and legend in Spanish too."""
    from phonometry.environment import propagation as prop

    bands = len(prop.TRAFFIC_NOISE_BANDS_HZ)
    result = (
        prop.sound_absorption_rating(np.full(bands, 0.5))
        if rating == "absorption"
        else prop.airborne_insulation_rating(np.full(bands, 25.0))
    )
    fig, ax = plt.subplots()
    try:
        result.plot(ax=ax, language="es")
        assert ax.get_ylabel() == ylabel
        assert "categoría" in ax.get_title()
        legend = [text.get_text() for text in ax.get_legend().get_texts()]
        assert any("ruido de tráfico normalizado" in text for text in legend)
    finally:
        plt.close(fig)


def test_a_railway_rating_title_names_no_category() -> None:
    """EN 16272 prints no category ladder, so the title stops at the number."""
    from phonometry.environment import propagation as prop

    alpha = np.full(len(prop.TRAFFIC_NOISE_BANDS_HZ), 0.5)
    result = prop.sound_absorption_rating(alpha, spectrum="railway")
    fig, ax = plt.subplots()
    try:
        result.plot(ax=ax)
        assert result.category is None
        assert ax.get_title() == rf"$DL_\alpha$ = {result.reported} dB"
    finally:
        plt.close(fig)


# --------------------------------------------------------------------------
# In situ sound reflection (EN 1793-5)
# --------------------------------------------------------------------------
def test_reflection_index_plot_draws_positions_average_and_rating() -> None:
    """Table B.1 as a figure: twelve positions, their mean, and DL_RI.

    The bands below 200 Hz are kept for information only, so they sit on a
    hatched background, and the title carries the single number with the
    range it sums.
    """
    from result_factories import _reflection_index

    result = _reflection_index()
    fig, ax = plt.subplots()
    try:
        result.plot(ax=ax)
        average, positions = ax.lines[1], ax.lines[0]
        np.testing.assert_allclose(average.get_ydata(), result.reflection_index)
        assert len(positions.get_ydata()) == result.position_values.size
        assert f"= {result.rating.reported} dB" in ax.get_title()
        assert "200 Hz" in ax.get_title()
        hatched = [patch for patch in ax.patches if patch.get_hatch()]
        assert len(hatched) == 1
    finally:
        plt.close(fig)


def test_reflection_index_plot_speaks_spanish() -> None:
    from result_factories import _reflection_index

    result = _reflection_index()
    fig, ax = plt.subplots()
    try:
        result.plot(ax=ax, language="es")
        assert ax.get_ylabel() == "Índice de reflexión acústica $RI$"
        assert "a 5 kHz" in ax.get_title()
        labels = ax.get_legend_handles_labels()[1]
        assert "Media de todas las posiciones" in labels
    finally:
        plt.close(fig)


def test_reflection_rating_plot_hatches_the_bands_it_leaves_out() -> None:
    from result_factories import _reflection_index

    rating = _reflection_index().rating
    fig, ax = plt.subplots()
    try:
        rating.plot(ax=ax)
        hatched = [patch for patch in ax.patches if patch.get_hatch()]
        assert len(hatched) == 3
        assert "category" not in ax.get_title()
        assert "(200 Hz to 5 kHz)" in ax.get_title()
    finally:
        plt.close(fig)


def test_direct_sound_subtraction_plot_draws_the_three_records() -> None:
    from result_factories import _direct_sound_subtraction

    result = _direct_sound_subtraction()
    fig, ax = plt.subplots()
    try:
        result.plot(ax=ax)
        front, aligned, residual = ax.lines
        peak = result.peak_index
        start = peak - round(1.0e-3 * result.fs)
        np.testing.assert_allclose(
            residual.get_ydata(),
            result.residual[start : start + len(residual.get_ydata())],
        )
        np.testing.assert_allclose(
            aligned.get_ydata(),
            result.aligned_free_field[start : start + len(aligned.get_ydata())],
        )
        assert front.get_xdata()[0] == pytest.approx(-1.0)
        assert "$R_{sub}$" in ax.get_title()
    finally:
        plt.close(fig)


def test_reflection_limit_plot_colours_what_ends_each_window() -> None:
    from result_factories import _reflection_limit

    result = _reflection_limit()
    fig, ax = plt.subplots()
    try:
        result.plot(ax=ax, language="es")
        heights = [patch.get_height() for patch in ax.patches]
        np.testing.assert_allclose(heights, result.low_frequency_limit_hz)
        labels = ax.get_legend_handles_labels()[1] or [
            text.get_text() for text in ax.get_legend().get_texts()
        ]
        assert "limitado por la reflexión en el suelo" in labels
        assert "limitado por el borde superior" in labels
        assert "3,5 m" in ax.get_title()
    finally:
        plt.close(fig)


def test_reflection_grid_check_plot_marks_the_microphone_out_of_tolerance() -> None:
    from result_factories import _reflection_grid_check

    result = _reflection_grid_check()
    fig, ax = plt.subplots()
    try:
        result.plot(ax=ax)
        deviation, outside = ax.lines[1], ax.lines[2]
        np.testing.assert_allclose(deviation.get_ydata(), result.deviations_m * 1e3)
        assert list(outside.get_xdata()) == [7.0]
        assert ax.get_title().endswith("position to adjust")
    finally:
        plt.close(fig)
