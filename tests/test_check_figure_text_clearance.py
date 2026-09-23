#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The gate that reads the committed drawings for a text something is drawn over.

``scripts/check_figure_text_clearance.py`` never runs a generator: it parses
the drawing as matplotlib, or the plate canvas, wrote it, so everything it
believes about the file has to be true of real output. The drawings below are
built so the answer is plain: a note moved onto a tick label and the same note
moved off it, two notes run together, a line struck through a note, the same
line behind the note's chip, a line clipped at the axes, and on a plate a line
through a heading and a dimension line that stops at its value.

The cases that must *not* fire matter as much as the ones that must: a label
turned through an angle, which an upright box would say reaches over
everything near it; the leader of an annotation, which starts at its own
words; the gridlines a label sits on by design; and a note clipped away with
its axes, which is in the file and not on the page.

Then the geometry the reading rests on, and the command line.
"""

from __future__ import annotations

import math
import pathlib
import sys
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_figure_text_clearance as gate
from diagrams.canvas import LIGHT, SVG

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from matplotlib.axes import Axes


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
    """What is drawn over which text in *path*, as ``(kind, text)`` pairs."""
    return {(finding.kind, finding.text) for finding in gate.measure(path)}


def _panel() -> Axes:
    """A unit panel with nothing in it but its axes."""
    _fig, ax = plt.subplots(figsize=(4, 3))
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    return ax


def _tick_label(ax: Axes, text: str) -> tuple[float, float, float]:
    """The two ends and the middle height of the y tick label *text* of *ax*.

    In axes fractions: its left end, its right end, and its height.
    """
    ax.figure.canvas.draw()
    for label in ax.get_yticklabels():
        if label.get_text() == text:
            box = label.get_window_extent()
            middle = (box.y0 + box.y1) / 2.0
            inverse = ax.transAxes.inverted()
            (x0, y), (x1, _) = inverse.transform([(box.x0, middle), (box.x1, middle)])
            return float(x0), float(x1), float(y)
    msg = f"no y tick label reads {text!r}"
    raise AssertionError(msg)


def _plate(
    tmp_path: pathlib.Path, name: str, build: Callable[[SVG], None]
) -> pathlib.Path:
    """Draw a small plate with the plate canvas and write it to *name*."""
    svg = SVG(400, 200, LIGHT)
    build(svg)
    path = tmp_path / f"{name}.svg"
    path.write_text(svg.render("A plate"), encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# A text over a tick label, or over another text.


def test_a_note_over_a_tick_label_fires(tmp_path: pathlib.Path) -> None:
    """The published defect: a note set beside the axis, over its numbers."""
    ax = _panel()
    x, _, y = _tick_label(ax, "0.6")
    ax.text(x, y, "a note", transform=ax.transAxes, va="center", clip_on=False)
    assert ("tick", "0.6") in _kinds(_save(tmp_path, "tick_over"))


def test_the_same_note_inside_the_panel_passes(tmp_path: pathlib.Path) -> None:
    ax = _panel()
    ax.text(0.3, 0.6, "a note", transform=ax.transAxes, va="center")
    assert gate.measure(_save(tmp_path, "tick_clear")) == []


def test_two_notes_run_together_fire(tmp_path: pathlib.Path) -> None:
    ax = _panel()
    ax.text(0.2, 0.5, "the first note", transform=ax.transAxes)
    ax.text(0.45, 0.51, "the second note", transform=ax.transAxes)
    assert {kind for kind, _ in _kinds(_save(tmp_path, "notes_over"))} == {"text"}


def test_the_lines_of_one_note_are_one_text(tmp_path: pathlib.Path) -> None:
    """Tight line spacing inside one artist is its own business."""
    ax = _panel()
    ax.text(0.2, 0.5, "one line\nand the next", linespacing=0.6)
    assert gate.measure(_save(tmp_path, "one_note")) == []


def test_a_note_clipped_away_with_its_axes_does_not_fire(
    tmp_path: pathlib.Path,
) -> None:
    """``clip_on=True`` keeps the glyphs in the file and off the page."""
    ax = _panel()
    _, x, y = _tick_label(ax, "0.6")
    for clip, fired in ((True, False), (False, True)):
        ax.text(
            x, y, "a", transform=ax.transAxes, ha="right", va="center", clip_on=clip
        )
        path = _save(tmp_path, f"tick_clipped_{clip}")
        assert (("tick", "0.6") in _kinds(path)) is fired
        ax = _panel()


# --------------------------------------------------------------------------
# A stroke through a text.


def test_a_line_through_a_note_fires(tmp_path: pathlib.Path) -> None:
    ax = _panel()
    ax.text(0.3, 0.5, "a note on the curve", va="center")
    ax.plot([0.45, 0.45], [0.2, 0.8], color="black", linewidth=1.5)
    assert ("cut", "a note on the curve") in _kinds(_save(tmp_path, "cut"))


def test_a_line_along_a_note_fires(tmp_path: pathlib.Path) -> None:
    """Struck through lengthwise: no stretch of it spans the line, the ink does."""
    ax = _panel()
    ax.text(0.3, 0.5, "a note on the curve", va="baseline")
    ax.plot([0.1, 0.9], [0.51, 0.51], color="black", linewidth=1.5)
    assert ("ink", "a note on the curve") in _kinds(_save(tmp_path, "ink"))


def test_a_spine_through_a_note_that_runs_out_fires(tmp_path: pathlib.Path) -> None:
    """A note that runs out of its axes is struck through by the spine."""
    ax = _panel()
    ax.text(0.9, 0.5, "a note that runs out", va="center")
    assert ("cut", "a note that runs out") in _kinds(_save(tmp_path, "spine"))


def test_the_same_line_behind_a_chip_passes(tmp_path: pathlib.Path) -> None:
    """An opaque chip painted over the line hides it where the words are."""
    ax = _panel()
    ax.text(
        0.3,
        0.5,
        "a note on the curve",
        va="center",
        zorder=5,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white"},
    )
    ax.plot([0.45, 0.45], [0.2, 0.8], color="black", linewidth=1.5)
    assert gate.measure(_save(tmp_path, "chip")) == []


def test_a_line_clipped_short_of_a_note_does_not_fire(tmp_path: pathlib.Path) -> None:
    """The file keeps the whole line; the page shows it inside the axes only."""
    ax = _panel()
    ax.text(1.02, 0.5, "outside", transform=ax.transAxes, va="center")
    ax.plot([0.5, 3.0], [0.5, 0.5], color="black", linewidth=2.0)
    assert gate.measure(_save(tmp_path, "clipped")) == []


def test_the_leader_of_an_annotation_does_not_fire(tmp_path: pathlib.Path) -> None:
    """Its own arrow starts at its words by design, even run back across them."""
    ax = _panel()
    ax.annotate(
        "a note with its arrow",
        xy=(0.95, 0.52),
        xytext=(0.1, 0.5),
        va="center",
        arrowprops={"arrowstyle": "-", "relpos": (0.0, 0.5), "patchA": None},
    )
    assert gate.measure(_save(tmp_path, "leader")) == []


def test_the_spine_written_before_a_text_is_not_its_leader(
    tmp_path: pathlib.Path,
) -> None:
    """The last spine stands just before the first text, and is no arrow of it."""
    ax = _panel()
    ax.text(0.5, 1.0, "a note on the top spine", ha="center", va="center")
    assert ("ink", "a note on the top spine") in _kinds(_save(tmp_path, "top"))


def test_the_same_line_drawn_by_another_artist_fires(tmp_path: pathlib.Path) -> None:
    """The control for the leader: what exempts it is whose it is."""
    ax = _panel()
    ax.annotate(
        "a note with its arrow",
        xy=(0.95, 0.52),
        xytext=(0.1, 0.5),
        va="center",
        arrowprops={"arrowstyle": "-", "relpos": (0.0, 0.5), "patchA": None},
    )
    ax.annotate(
        "",
        xy=(0.95, 0.52),
        xytext=(0.1, 0.5),
        arrowprops={"arrowstyle": "-", "shrinkA": 0.0, "shrinkB": 0.0},
    )
    assert ("ink", "a note with its arrow") in _kinds(_save(tmp_path, "not_leader"))


def test_the_gridlines_a_note_sits_on_do_not_fire(tmp_path: pathlib.Path) -> None:
    ax = _panel()
    ax.grid(visible=True, linewidth=2.0)
    ax.set_xticks([0.0, 0.25, 0.5, 0.75, 1.0])
    ax.text(0.2, 0.6, "a note across the grid", va="center")
    assert gate.measure(_save(tmp_path, "grid")) == []


def test_a_turned_label_is_read_as_its_letters(tmp_path: pathlib.Path) -> None:
    """A line in the corner of a turned label's upright box, clear of its letters."""
    ax = _panel()
    label = ax.text(
        0.5,
        0.5,
        "a long label turned on its side",
        rotation=45,
        ha="center",
        va="center",
    )
    ax.figure.canvas.draw()
    box = label.get_window_extent()
    inverse = ax.transData.inverted()
    (x0, y0), (x1, y1) = inverse.transform([(box.x0, box.y0), (box.x1, box.y1)])
    # The upper left corner of the box, well off the diagonal the letters run on.
    y = y1 - 0.1 * (y1 - y0)
    ax.plot([x0 + 0.05 * (x1 - x0), x0 + 0.3 * (x1 - x0)], [y, y], color="black")
    assert gate.measure(_save(tmp_path, "turned")) == []


def test_the_labels_of_a_three_d_plate_do_not_fire(tmp_path: pathlib.Path) -> None:
    """Axis labels turned with the box, over its panes and grid."""
    fig = plt.figure(figsize=(5, 4))
    ax = fig.add_subplot(projection="3d")
    ax.plot([0.0, 1.0], [0.0, 1.0], [0.0, 1.0])
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_zlabel("z [m]")
    assert gate.measure(_save(tmp_path, "three_d")) == []


# --------------------------------------------------------------------------
# Plates.


def test_a_line_through_a_plate_heading_fires(tmp_path: pathlib.Path) -> None:
    def build(svg: SVG) -> None:
        svg.text(200, 100, "the last lane", size=14)
        svg.line(200, 80, 200, 120, "#000000")

    path = _plate(tmp_path, "plate_cut", build)
    assert ("cut", "the last lane") in _kinds(path)


def test_a_dimension_line_stopping_at_its_value_passes(tmp_path: pathlib.Path) -> None:
    """The end of an open line points at the words it stops on."""

    def build(svg: SVG) -> None:
        svg.text(200, 100, "0.5 m", size=14, anchor="start")
        svg.line(120, 95, 202, 95, "#000000", sw=1.0)

    assert gate.measure(_plate(tmp_path, "plate_pointer", build)) == []


def test_a_plate_line_under_a_backing_passes(tmp_path: pathlib.Path) -> None:
    def build(svg: SVG) -> None:
        svg.line(200, 80, 200, 120, "#000000")
        svg.rect(150, 85, 100, 22, "#ffffff")
        svg.text(200, 100, "the last lane", size=14)

    assert gate.measure(_plate(tmp_path, "plate_backing", build)) == []


def test_a_dashed_plate_line_with_its_gap_on_the_words_passes(
    tmp_path: pathlib.Path,
) -> None:
    """A dash pattern draws nothing in its gaps."""

    def build(svg: SVG) -> None:
        svg.text(300, 100, "lane", size=14)
        svg.line(300, 0, 300, 200, "#000000", dash="80 40")

    assert gate.measure(_plate(tmp_path, "plate_dashes", build)) == []


# --------------------------------------------------------------------------
# The geometry underneath.


def test_an_arc_is_read_on_its_circle() -> None:
    lines = gate._outline("M 0 0 A 10 10 0 0 1 20 0")
    assert len(lines) == 1
    points = lines[0]
    assert len(points) > 10
    for x, y in points:
        assert math.hypot(x - 10.0, y) == pytest.approx(10.0, abs=1e-9)
    assert points[-1] == (20.0, 0.0)


def test_relative_and_shorthand_commands_are_read() -> None:
    lines = gate._outline("m 10 10 h 5 v 5 l -5 0 z M 0 0 H 3 V 4")
    assert lines[0] == [
        (10.0, 10.0),
        (15.0, 10.0),
        (15.0, 15.0),
        (10.0, 15.0),
        (10.0, 10.0),
    ]
    assert lines[1] == [(0.0, 0.0), (3.0, 0.0), (3.0, 4.0)]


def test_the_counter_of_a_letter_is_not_filled() -> None:
    """Even-odd: the hole of an "o" is not ink."""
    outer = ((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0))
    inner = ((3.0, 3.0), (7.0, 3.0), (7.0, 7.0), (3.0, 7.0), (3.0, 3.0))
    assert gate._filled((1.0, 5.0), (outer, inner))
    assert not gate._filled((5.0, 5.0), (outer, inner))
    assert not gate._filled((12.0, 5.0), (outer, inner))


def test_two_turned_boxes_are_compared_as_they_lie() -> None:
    """Two diamonds whose upright boxes overlap and whose sides do not."""
    one = ((0.0, 5.0), (5.0, 0.0), (10.0, 5.0), (5.0, 10.0))
    other = ((8.0, 13.0), (13.0, 8.0), (18.0, 13.0), (13.0, 18.0))
    assert gate._depth(one, other) < 0.0
    shifted = tuple((x - 4.0, y - 4.0) for x, y in other)
    assert gate._depth(one, shifted) > 0.0  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("start", "end", "hit"),
    [
        ((-5.0, 5.0), (15.0, 5.0), True),
        ((5.0, -5.0), (5.0, 15.0), True),
        ((-5.0, 12.0), (15.0, 12.0), False),
        ((12.0, -5.0), (12.0, 15.0), False),
    ],
)
def test_a_segment_is_clipped_to_a_turned_box(
    start: tuple[float, float], end: tuple[float, float], *, hit: bool
) -> None:
    diamond = ((0.0, 5.0), (5.0, 0.0), (10.0, 5.0), (5.0, 10.0))
    assert (gate._clip(start, end, gate._slabs(diamond, 0.0)) is not None) is hit


# --------------------------------------------------------------------------
# The command line.


def test_the_command_line_fails_on_a_cover_and_passes_without(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ax = _panel()
    ax.text(0.3, 0.5, "a note on the curve", va="center")
    ax.plot([0.45, 0.45], [0.2, 0.8], color="black", linewidth=1.5)
    covered = _save(tmp_path, "covered")
    ax = _panel()
    ax.text(0.3, 0.5, "a note on the curve", va="center")
    clear = _save(tmp_path, "clear")

    assert gate.main([str(covered), str(clear)]) == 1
    out = capsys.readouterr().out
    assert "covered: line2d_" in out
    assert "runs across 'a note on the curve'" in out
    assert gate.main([str(clear)]) == 0
    assert gate.main(["--report", str(covered)]) == 0


def test_an_exemption_lets_its_text_pass(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ax = _panel()
    ax.text(0.3, 0.5, "a note on the curve", va="center")
    ax.plot([0.45, 0.45], [0.2, 0.8], color="black", linewidth=1.5)
    covered = _save(tmp_path, "covered")
    monkeypatch.setattr(
        gate, "EXEMPTIONS", {"covered: a note on the curve": "a decision"}
    )
    assert gate.main([str(covered)]) == 0


def test_a_stale_exemption_fails(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An entry nothing fires on any more has to be deleted."""
    _panel()
    clear = _save(tmp_path, "clear")
    monkeypatch.setattr(gate.legends, "light_figures", lambda: [clear])
    monkeypatch.setattr(gate, "EXEMPTIONS", {"clear: a note": "a decision"})
    assert gate.main([]) == 1
    assert "no longer fires" in capsys.readouterr().out
