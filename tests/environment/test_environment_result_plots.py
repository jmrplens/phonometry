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
