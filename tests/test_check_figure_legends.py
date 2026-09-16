#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The legend-over-datum gate, read off real matplotlib SVG output.

``scripts/check_figure_legends.py`` never runs a generator: it parses the
committed drawing, so everything it believes about the file has to be true of
what matplotlib actually writes. A legend is a group whose first unnamed filled
path is its frame, a plotted point is a ``<use>`` of a glyph small enough to be
a marker, and the box the legend draws for its own handles is not a datum. The
figures below are built so the expected answer is obvious: a series that ends
under the box, the same series with the box in the other corner, a shaded band
wide enough that it can only be a band, and a panel with no legend at all.

Then the arithmetic on top: the gate, the exemptions and their staleness, the
two languages of one drawing, and the command line.
"""

from __future__ import annotations

import pathlib
import sys
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Literal

import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_figure_legends as cfl

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def _save(tmp_path: pathlib.Path, name: str) -> pathlib.Path:
    """Write the current figure to *name* and return its path."""
    path = tmp_path / f"{name}.svg"
    plt.savefig(path)
    plt.close()
    return path


def _handles_in_legend(path: pathlib.Path) -> int:
    """How many marker glyphs are placed inside a legend group of *path*."""
    root = ET.parse(path).getroot()
    glyphs = cfl._glyphs(root)
    return sum(
        1
        for element, _dx, _dy, legend in cfl._walk(root)
        if legend is not None
        and element.tag == cfl.SVG + "use"
        and (element.get(cfl.XLINK + "href") or "").lstrip("#") in glyphs
    )


def _series(corner: Literal["upper right", "lower right"]) -> None:
    """A rising series with the legend in *corner*, which the end may be under."""
    _fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1, 2, 3], [0.1, 0.3, 0.6, 1.0], "o-", label="a series")
    ax.legend(loc=corner)


def test_a_legend_over_a_plotted_point_is_reported(tmp_path: pathlib.Path) -> None:
    """The series climbs into the box, so its last marks are under it."""
    _series("upper right")
    found = cfl.measure(_save(tmp_path, "covered"))

    assert found, "the end of the series is under the box and was not seen"
    assert {overlap.legend for overlap in found} == {"legend_1"}
    assert all(overlap.drawing == "covered" for overlap in found)


def test_the_same_series_with_the_box_in_the_free_corner_is_silent(
    tmp_path: pathlib.Path,
) -> None:
    """Nothing is drawn in the lower right, so nothing is covered there."""
    _series("lower right")

    assert cfl.measure(_save(tmp_path, "clear")) == []


def test_the_handle_of_a_legend_is_not_a_datum(tmp_path: pathlib.Path) -> None:
    """Every legend draws a marker of its own, inside its own frame."""
    _fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1, 2, 3], [0.1, 0.2, 0.15, 0.1], "o-", label="a low series")
    ax.set_ylim(0.0, 1.0)
    ax.legend(loc="upper right")
    path = _save(tmp_path, "handle")

    assert _handles_in_legend(path) == 1, "the handle marker is drawn somewhere else"
    assert cfl.measure(path) == []


def test_a_legend_without_a_frame_is_not_a_plate(tmp_path: pathlib.Path) -> None:
    """``frameon=False`` puts letters over the drawing, and nothing else."""
    _fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1, 2, 3], [0.1, 0.3, 0.6, 1.0], "o-", label="a series")
    ax.legend(loc="upper right", frameon=False)
    path = _save(tmp_path, "frameless")

    root = ET.parse(path).getroot()
    assert cfl._frames(cfl._walk(root)) == {}
    assert cfl.measure(path) == []


def test_a_shaded_band_under_the_box_is_not_a_marker(tmp_path: pathlib.Path) -> None:
    """A band and a marker are named alike by matplotlib; size separates them."""
    _fig, ax = plt.subplots(figsize=(4, 3))
    ax.fill_between([0, 1, 2, 3], 0.0, 1.0, color="#aec7e8", label="a band")
    ax.legend(loc="upper right")

    assert cfl.measure(_save(tmp_path, "band")) == []


#: A legend frame with one glyph placed inside it, written out rather than
#: drawn: the diagram plates bake their labels to outlines at final size, which
#: is what makes a letter exactly marker-sized, and no matplotlib call produces
#: that shape.
_PLATE = """<svg xmlns="http://www.w3.org/2000/svg"
  xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 200 100">
 <defs><path id="{glyph}" d="M 0 0 L 10 0 L 10 12 L 0 12 z"/></defs>
 <g id="figure_1"><g id="axes_1">
  <g id="line2d_7"><g><use xlink:href="#{glyph}" x="60" y="30"/></g></g>
  <g id="legend_1"><g id="patch_2">
   <path d="M 50 20 L 150 20 L 150 50 L 50 50 z" style="fill: #ffffff"/>
  </g></g>
 </g></g>
</svg>
"""


def test_a_letter_under_the_box_is_not_a_plotted_point(
    tmp_path: pathlib.Path,
) -> None:
    """A baked letter is marker-sized, and its name is what tells it apart."""
    letter = tmp_path / "lettered.svg"
    letter.write_text(_PLATE.format(glyph="DejaVuSans-11"))
    marker = tmp_path / "marked.svg"
    marker.write_text(_PLATE.format(glyph="m3d27035b55"))

    assert cfl.measure(letter) == []
    assert [overlap.artist for overlap in cfl.measure(marker)] == ["line2d_7"]


def test_a_drawing_with_no_legend_is_not_measured(tmp_path: pathlib.Path) -> None:
    """Without a frame there is nothing to be under."""
    _fig, ax = plt.subplots(figsize=(4, 3))
    ax.plot([0, 1, 2, 3], [0.1, 0.3, 0.6, 1.0], "o-")

    assert cfl.measure(_save(tmp_path, "bare")) == []


def test_each_legend_of_a_panel_is_measured(tmp_path: pathlib.Path) -> None:
    """A second legend added by hand covers its own points and is named."""
    _fig, ax = plt.subplots(figsize=(4, 3))
    rising = ax.plot([0, 1, 2, 3], [0.1, 0.3, 0.6, 1.0], "o-", label="rising")
    falling = ax.plot([0, 1, 2, 3], [1.0, 0.6, 0.3, 0.1], "s-", label="falling")
    ax.add_artist(ax.legend(handles=rising, loc="upper right"))
    ax.legend(handles=falling, loc="upper left")
    found = cfl.measure(_save(tmp_path, "two_boxes"))

    assert {overlap.legend for overlap in found} == {"legend_1", "legend_2"}


def test_a_covered_point_is_named_by_the_artist_that_drew_it(
    tmp_path: pathlib.Path,
) -> None:
    """The report points at an artist of the drawing, not at an anonymous path."""
    _series("upper right")
    first = cfl.measure(_save(tmp_path, "named"))[0]

    assert first.artist.startswith("line2d_")
    assert first.artist in first.describe()
    assert "named" in first.describe()


def test_the_two_languages_of_a_drawing_are_one_figure() -> None:
    """An exemption is written once and covers the Spanish twin as well."""
    assert cfl._drawing("silencer_selection_es") == "silencer_selection"
    assert cfl._drawing("silencer_selection") == "silencer_selection"


def test_only_the_light_drawings_are_read(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The dark twin is the same geometry, so reading it says nothing new."""
    for name in ("a.svg", "a_dark.svg", "a_es.svg", "a_es_dark.svg"):
        (tmp_path / name).write_text("<svg/>")
    monkeypatch.setattr(cfl, "IMG_DIR", tmp_path)

    assert [p.name for p in cfl.light_figures()] == ["a.svg", "a_es.svg"]


def test_the_gate_fails_and_names_the_offender(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A point under a box that nobody wrote down is a failure."""
    _series("upper right")
    path = _save(tmp_path, "covered")

    assert cfl.main([str(path)]) == 1
    printed = capsys.readouterr().out
    assert "covered: legend_1 covers" in printed
    assert "EXEMPTIONS" in printed


def test_a_written_down_figure_passes(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A decision is a line in the file, and the line is what makes it pass."""
    _series("upper right")
    path = _save(tmp_path, "covered_es")
    monkeypatch.setattr(cfl, "EXEMPTIONS", {"covered": "the marks are a rail"})

    assert cfl.main([str(path)]) == 0


def test_an_exemption_that_stopped_being_true_fails(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The file ratchets both ways: a figure that was fixed owes its line back."""
    _series("lower right")
    path = _save(tmp_path, "clear")
    monkeypatch.setattr(cfl, "EXEMPTIONS", {"clear": "no longer true"})

    assert cfl.main([str(path)]) == 1
    assert "delete the entry" in capsys.readouterr().out


def test_the_report_prints_every_overlap_and_passes(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--report`` is for reading, exemptions included, and never fails."""
    _series("upper right")
    path = _save(tmp_path, "covered")
    monkeypatch.setattr(cfl, "EXEMPTIONS", {"covered": "written down"})

    assert cfl.main(["--report", str(path)]) == 0
    printed = capsys.readouterr().out
    assert "covered: legend_1 covers" in printed
    assert "overlap(s) in 1 drawings." in printed


def test_a_clean_drawing_passes_and_says_so(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The passing line counts what was read and what was written down."""
    _series("lower right")
    path = _save(tmp_path, "clear")
    monkeypatch.setattr(cfl, "EXEMPTIONS", {})

    assert cfl.main([str(path)]) == 0
    assert "No legend covers a plotted point" in capsys.readouterr().out


def test_every_exemption_carries_a_reason() -> None:
    """A figure is written down with why the mark under it is not a reading."""
    assert cfl.EXEMPTIONS
    for name, reason in cfl.EXEMPTIONS.items():
        assert name == name.strip()
        assert len(reason.split()) >= 10, f"{name} is written down without a reason"
