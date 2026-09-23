#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate that reads the committed figures for a tick label something covers.

``scripts/check_figure_tick_clearance.py`` never runs a generator: it parses
the drawing as matplotlib wrote it, so everything it believes about the file
has to be true of real output. The figures below are built so the answer is
plain: a legend moved over the labels it sits beside and the same legend
inside the panel, a fan of lines across the radial labels of a polar axes and
the same labels parked on a ray the fan does not reach, a line clipped at the
axes and the same line let out past them, and a marker set on a label.

The cases that must *not* fire matter as much as the ones that must: the
gridlines a radial label sits on by design, the stretch of a clipped line that
the file keeps and the page never shows, and a legend or a curve that stays
inside its own panel.

Then the geometry the reading rests on, and the command line.
"""

from __future__ import annotations

import pathlib
import sys
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_figure_tick_clearance as gate

if TYPE_CHECKING:
    from collections.abc import Iterator

    from matplotlib.axes import Axes
    from matplotlib.projections.polar import PolarAxes


@pytest.fixture(autouse=True)
def _default_rc() -> Iterator[None]:
    """Stock matplotlib, because every figure here is measured geometrically."""
    with mpl.rc_context(mpl.rcParamsDefault):
        yield
    plt.close("all")


def _save(tmp_path: pathlib.Path, name: str) -> pathlib.Path:
    """Write the current figure to *name* and return its path."""
    path = tmp_path / f"{name}.svg"
    plt.savefig(path)
    plt.close()
    return path


def _kinds(path: pathlib.Path) -> set[tuple[str, str]]:
    """What covers which label in *path*, as ``(kind, label)`` pairs."""
    return {(cover.kind, cover.label) for cover in gate.measure(path)}


def _panel() -> Axes:
    """A unit panel with a curve in it, so it has a legend entry to show."""
    _fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0.2, 0.8], [0.3, 0.7], label="a reading")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    return ax


def _label_centre(ax: Axes, text: str) -> tuple[float, float]:
    """Where the y tick label *text* of *ax* is centred, in axes fractions."""
    ax.figure.canvas.draw()
    for label in ax.get_yticklabels():
        if label.get_text() == text:
            box = label.get_window_extent()
            centre = ((box.x0 + box.x1) / 2.0, (box.y0 + box.y1) / 2.0)
            x, y = ax.transAxes.inverted().transform(centre)
            return float(x), float(y)
    msg = f"no y tick label reads {text!r}"
    raise AssertionError(msg)


def _polar_fan(*, label_angle: float | None) -> None:
    """Radial lines from 10 to 35 degrees, across the default label ray."""
    _fig, axes = plt.subplots(subplot_kw={"projection": "polar"})
    polar: PolarAxes = axes
    for angle in np.radians(np.arange(10.0, 36.0, 1.0)):
        polar.plot([angle, angle], [0.0, 1.0], color="black", linewidth=1.0)
    polar.set_rmax(1.0)
    if label_angle is not None:
        polar.set_rlabel_position(label_angle)


# --------------------------------------------------------------------------
# Legends.


def test_a_legend_over_the_tick_labels_fires(tmp_path: pathlib.Path) -> None:
    """The published defect: a box moved out to the side, over the numbers."""
    ax = _panel()
    x, y = _label_centre(ax, "0.6")
    ax.legend(loc="center", bbox_to_anchor=(x, y))
    kinds = _kinds(_save(tmp_path, "legend_over"))
    assert ("legend", "0.6") in kinds


def test_a_legend_inside_the_panel_does_not_fire(tmp_path: pathlib.Path) -> None:
    ax = _panel()
    ax.legend(loc="upper left")
    assert gate.measure(_save(tmp_path, "legend_inside")) == []


def test_a_legend_over_the_labels_of_a_twin_fires(tmp_path: pathlib.Path) -> None:
    """Every tick label of the drawing counts, whichever axes draws it."""
    ax = _panel()
    twin = ax.twinx()
    twin.set_ylim(0.0, 10.0)
    ax.figure.canvas.draw()
    label = next(t for t in twin.get_yticklabels() if t.get_text() == "6")
    box = label.get_window_extent()
    centre = ((box.x0 + box.x1) / 2.0, (box.y0 + box.y1) / 2.0)
    x, y = ax.transAxes.inverted().transform(centre)
    ax.legend(loc="center", bbox_to_anchor=(float(x), float(y)))
    assert ("legend", "6") in _kinds(_save(tmp_path, "legend_twin"))


def test_a_legend_without_a_plate_still_fires(tmp_path: pathlib.Path) -> None:
    """The box its entries fill stands in for the plate it does not draw."""
    ax = _panel()
    x, y = _label_centre(ax, "0.6")
    ax.legend(loc="center", bbox_to_anchor=(x, y), frameon=False)
    assert ("legend", "0.6") in _kinds(_save(tmp_path, "legend_bare"))


# --------------------------------------------------------------------------
# Strokes.


def test_a_curve_through_the_radial_labels_fires(tmp_path: pathlib.Path) -> None:
    """The radial labels sit inside a polar plot, on one ray, over the data."""
    _polar_fan(label_angle=None)
    kinds = _kinds(_save(tmp_path, "fan_default"))
    assert {kind for kind, _ in kinds} == {"stroke"}
    assert ("stroke", "0.6") in kinds


def test_the_same_labels_on_a_clear_ray_pass(tmp_path: pathlib.Path) -> None:
    """``set_rlabel_position`` is the fix, and the gate has to see it work."""
    _polar_fan(label_angle=200.0)
    assert gate.measure(_save(tmp_path, "fan_parked")) == []


def test_the_gridlines_a_radial_label_sits_on_do_not_fire(
    tmp_path: pathlib.Path,
) -> None:
    """A radial label is drawn on its own ring by design."""
    _fig, axes = plt.subplots(subplot_kw={"projection": "polar"})
    polar: PolarAxes = axes
    polar.set_rmax(1.0)
    polar.grid(visible=True, linewidth=2.0)
    assert gate.measure(_save(tmp_path, "rings")) == []


def test_a_line_clipped_at_the_axes_does_not_fire(tmp_path: pathlib.Path) -> None:
    """The file keeps the whole line; the page shows it inside the axes only."""
    ax = _panel()
    ax.plot([-1.0, 2.0], [0.6, 0.6], color="black", linewidth=2.0)
    assert gate.measure(_save(tmp_path, "clipped")) == []


def test_the_same_line_let_out_past_the_axes_fires(tmp_path: pathlib.Path) -> None:
    ax = _panel()
    ax.plot([-1.0, 2.0], [0.6, 0.6], color="black", linewidth=2.0, clip_on=False)
    assert ("stroke", "0.6") in _kinds(_save(tmp_path, "unclipped"))


def test_a_line_passing_beside_a_label_does_not_fire(tmp_path: pathlib.Path) -> None:
    """Between two labels, clear of both by more than its own width."""
    ax = _panel()
    ax.plot([-1.0, 2.0], [0.5, 0.5], color="black", linewidth=1.0, clip_on=False)
    kinds = _kinds(_save(tmp_path, "between"))
    assert ("stroke", "0.4") not in kinds
    assert ("stroke", "0.6") not in kinds


# --------------------------------------------------------------------------
# Markers.


def test_a_marker_on_a_tick_label_fires(tmp_path: pathlib.Path) -> None:
    ax = _panel()
    x, y = _label_centre(ax, "0.4")
    ax.plot([x], [y], "o", transform=ax.transAxes, clip_on=False, markersize=8)
    assert ("marker", "0.4") in _kinds(_save(tmp_path, "marker_on"))


def test_a_marker_clipped_away_does_not_fire(tmp_path: pathlib.Path) -> None:
    """Clipped by the axes, the marker is in the file and not on the page."""
    ax = _panel()
    x, y = _label_centre(ax, "0.4")
    ax.plot([x], [y], "o", transform=ax.transAxes, markersize=8)
    assert gate.measure(_save(tmp_path, "marker_clipped")) == []


# --------------------------------------------------------------------------
# The geometry underneath.


@pytest.mark.parametrize(
    ("attribute", "point", "expected"),
    [
        (None, (1.0, 2.0), (1.0, 2.0)),
        ("translate(10 20)", (1.0, 2.0), (11.0, 22.0)),
        ("translate(10)", (1.0, 2.0), (11.0, 2.0)),
        ("scale(0.1 -0.1)", (10.0, 10.0), (1.0, -1.0)),
        ("scale(2)", (1.0, 2.0), (2.0, 4.0)),
        ("rotate(90)", (1.0, 0.0), (0.0, 1.0)),
        ("matrix(1 0 0 1 5 6)", (1.0, 2.0), (6.0, 8.0)),
        # Applied right to left, as SVG reads a list of transforms.
        ("translate(10 0) scale(2)", (1.0, 1.0), (12.0, 2.0)),
    ],
)
def test_a_transform_is_read_as_svg_means_it(
    attribute: str | None,
    point: tuple[float, float],
    expected: tuple[float, float],
) -> None:
    x, y = gate._apply(gate._transform(attribute), point)
    assert x == pytest.approx(expected[0], abs=1e-12)
    assert y == pytest.approx(expected[1], abs=1e-12)


def test_a_path_is_read_as_polylines() -> None:
    """Lines as they are, curves as chords, a close back to the start."""
    lines = gate._polylines("M 0 0 L 10 0 Q 10 10 0 10 z M 20 20 C 20 30 30 30 30 20")
    assert len(lines) == 2
    first, second = lines
    assert first[:2] == [(0.0, 0.0), (10.0, 0.0)]
    assert first[-1] == (0.0, 0.0)
    assert (0.0, 10.0) in first
    assert second[0] == (20.0, 20.0)
    assert second[-1] == pytest.approx((30.0, 20.0))
    # The chords of a curve stay on it: the top of this arch is at y = 27.5.
    assert max(y for _, y in second) == pytest.approx(27.5)


@pytest.mark.parametrize(
    ("start", "end", "hit"),
    [
        ((-5.0, 5.0), (15.0, 5.0), True),
        ((-5.0, -5.0), (15.0, 15.0), True),
        ((-5.0, 12.0), (15.0, 12.0), False),
        ((2.0, 2.0), (3.0, 3.0), True),
        ((12.0, -5.0), (12.0, 15.0), False),
    ],
)
def test_a_segment_is_clipped_to_a_box(
    start: tuple[float, float], end: tuple[float, float], *, hit: bool
) -> None:
    assert (gate._through(start, end, (0.0, 0.0, 10.0, 10.0)) is not None) is hit


# --------------------------------------------------------------------------
# The command line.


def test_the_command_line_fails_on_a_cover_and_passes_without(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ax = _panel()
    x, y = _label_centre(ax, "0.6")
    ax.legend(loc="center", bbox_to_anchor=(x, y))
    covered = _save(tmp_path, "covered")
    ax = _panel()
    ax.legend(loc="upper left")
    clear = _save(tmp_path, "clear")

    assert gate.main([str(covered), str(clear)]) == 1
    assert "covered: legend_1 covers the tick label '0.6'" in capsys.readouterr().out
    assert gate.main([str(clear)]) == 0
    assert gate.main(["--report", str(covered)]) == 0


def test_the_committed_figures_pass() -> None:
    """The corpus itself, which is what the gate protects."""
    assert gate.main([]) == 0
