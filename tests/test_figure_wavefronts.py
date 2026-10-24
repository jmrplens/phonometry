#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A closed clip's wavefronts do not outlive its figure.

``scripts/figures/schematics.py`` remembers the hue each wavefront arc was
made in, so :func:`_set_wavefronts` can quiet it as the front spreads. The
map held every arc strongly, and an arc keeps its axes and its figure alive:
a pool worker that rendered several clips kept every figure of every
wavefront clip it had drawn, twice over (the gate pass and the encode pass),
for the rest of the batch, although ``plt.close("all")`` had closed them.
"""

from __future__ import annotations

import gc
import pathlib
import sys
import weakref

import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))

# Importing the generator's figures sets the settings it draws with for the
# whole process: inside rc_context they are put back at once, so no test
# collected after this module draws with them.
with mpl.rc_context():
    from figures import schematics

pytestmark = pytest.mark.pinned_stack


def test_a_closed_figure_takes_its_wavefronts_with_it() -> None:
    fig, ax = plt.subplots()
    arcs = schematics._make_wavefronts(ax, 0.0, 0.0, "#1f77b4", n=3)
    schematics._set_wavefronts(arcs, [0.2, 0.4, 0.6], 1.0)
    held = [weakref.ref(arc) for arc in arcs]
    figure = weakref.ref(fig)
    assert all(ref() in schematics._WAVEFRONT_HUE for ref in held)
    plt.close(fig)
    del fig, ax, arcs
    gc.collect()
    assert figure() is None
    assert all(ref() is None for ref in held)
