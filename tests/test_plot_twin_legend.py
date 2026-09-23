#  Copyright (c) 2026. Jose Manuel Requena Plens
"""One legend over two scales, placed clear of both.

matplotlib resolves ``loc="best"`` by scoring its candidate boxes against the
artists of the axes that carries the legend, and an axes made by ``twinx()`` is
a separate axes. On a panel with two scales the second one's curves are
invisible to that search, so the box lands on them as readily as on blank
paper. :func:`~phonometry._plot.common.place_legend_clear` runs the same search
against every scale, and each renderer that puts one legend over two scales
places it with that.

What is under a legend is measured here without the helper: every stroke of an
axes is sampled along its drawn segments in display coordinates, every marker
is grown by its size and every bar is read by its extent, and the samples that
fall inside the legend's frame are what it covers. Each case is built so that
matplotlib's own ``"best"`` covers the twin's data, and that is asserted too: a
case where the host alone already finds a clear spot would pass with or without
the fix and prove nothing.

The marks the search reads are checked one by one on a panel of their own:
the edge of a marker, the steps of a stepped line, ``hlines``, a text, and a
hidden artist that must count for nothing.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cbook import STEP_LOOKUP_MAP
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.legend import Legend
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox

import phonometry as ph
from phonometry._plot.common import _drawn_marks, _legend_badness, place_legend_clear
from phonometry.building.prediction.detailed_model import BandPath

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from matplotlib.axes import Axes

#: Samples per drawn segment: enough that a stroke crossing a legend frame
#: between two of its vertices leaves a sample inside it.
_SAMPLES_PER_SEGMENT = 64

#: The one-third octave centres the renderer cases are drawn on.
_THIRDS = np.array(
    [100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000,
     2500, 3150, 4000, 5000],
    dtype=np.float64,
)  # fmt: skip


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    yield
    plt.close("all")


def _inside(box: Bbox, points: np.ndarray) -> np.ndarray:
    """Which of *points*, in display coordinates, lie strictly inside *box*."""
    x, y = points[:, 0], points[:, 1]
    with np.errstate(invalid="ignore"):
        return np.asarray(
            (box.x0 < x) & (x < box.x1) & (box.y0 < y) & (y < box.y1), dtype=bool
        )


def _sampled(vertices: np.ndarray) -> np.ndarray:
    """The drawn segments through *vertices*, sampled finely.

    A segment with a non-finite end is a gap in the line and is not drawn, so
    it is not sampled either.
    """
    vertices = np.asarray(vertices, dtype=np.float64).reshape(-1, 2)
    start, end = vertices[:-1], vertices[1:]
    drawn = np.isfinite(start).all(axis=1) & np.isfinite(end).all(axis=1)
    t = np.linspace(0.0, 1.0, _SAMPLES_PER_SEGMENT)[None, :, None]
    samples = start[drawn, None, :] * (1.0 - t) + end[drawn, None, :] * t
    return samples.reshape(-1, 2)


def _covered(box: Bbox, ax: Axes) -> list[str]:
    """What of the data *ax* has drawn the display box *box* closes over."""
    pixels_per_point = ax.figure.dpi / 72.0
    found: list[str] = []
    for line in ax.lines:
        if not line.get_visible():
            continue
        xy = np.asarray(line.get_xydata(), dtype=np.float64).reshape(-1, 2)
        drawn = np.column_stack(STEP_LOOKUP_MAP[line.get_drawstyle()](*xy.T))
        transform = line.get_transform()
        stroke = _sampled(transform.transform(drawn))
        hits = int(_inside(box, stroke).sum()) if line.get_linestyle() != "None" else 0
        if str(line.get_marker()) not in {"", " ", "None", "none"}:
            reach = 0.5 * line.get_markersize() * pixels_per_point
            hits += int(_inside(box.padded(reach), transform.transform(xy)).sum())
        if hits:
            found.append(f"line {line.get_label()!r}")
    for patch in ax.patches:
        if not patch.get_visible():
            continue
        if isinstance(patch, Rectangle):
            if box.overlaps(patch.get_window_extent()):
                found.append(f"bar at {patch.get_x():.4g}")
            continue
        outline = patch.get_transform().transform_path(patch.get_path())
        if _inside(box, _sampled(np.asarray(outline.vertices))).any():
            found.append(f"patch {patch.get_label()!r}")
    for collection in ax.collections:
        if isinstance(collection, LineCollection | PolyCollection):
            transform = collection.get_transform()
            for path in collection.get_paths():
                outline = transform.transform_path(path)
                if _inside(box, _sampled(np.asarray(outline.vertices))).any():
                    found.append(f"collection {collection.get_label()!r}")
                    break
        else:
            centres = collection.get_offset_transform().transform(
                np.asarray(collection.get_offsets(), dtype=np.float64)
            )
            if _inside(box, centres).any():
                found.append(f"points {collection.get_label()!r}")
    return found


def _twins(ax: Axes) -> list[Axes]:
    """The axes that share *ax*'s frame: its ``twinx()`` or ``twiny()``."""
    shared = {*ax.get_shared_x_axes().get_siblings(ax)}
    shared |= {*ax.get_shared_y_axes().get_siblings(ax)}
    return [other for other in ax.figure.axes if other in shared and other is not ax]


def _frame(legend: Legend) -> Bbox:
    """The legend's frame where it is drawn."""
    legend.figure.canvas.draw()
    return legend.get_window_extent()


def _best_frame(legend: Legend) -> Bbox:
    """Where matplotlib's own ``loc="best"`` would have put the frame."""
    legend.set_loc("best")
    return _frame(legend)


# ---------------------------------------------------------------------------
# The helper on a panel built for it.
# ---------------------------------------------------------------------------


def _two_scale_panel() -> tuple[Axes, Axes, Legend]:
    """Two falling curves on the host, a rising one on the twin.

    The host's curves leave its upper right corner empty, which is where
    ``"best"`` goes, and the twin's curve climbs into that corner. The twin is
    made before anything is drawn, and each scale's data lies far from the
    default limits, so a search that read the limits before autoscaling had
    run would see nothing on either scale.
    """
    _fig, ax = plt.subplots(figsize=(6.4, 4.8))
    twin = ax.twinx()
    x = np.linspace(100.0, 200.0, 50)
    u = (x - 100.0) / 100.0
    ax.plot(x, 80.0 - 30.0 * u, label="falling")
    ax.plot(x, 74.0 - 30.0 * u, label="falling too")
    twin.plot(x, 500.0 + 1000.0 * u**4, color="C2", label="rising")
    handles, labels = ax.get_legend_handles_labels()
    extra_handles, extra_labels = twin.get_legend_handles_labels()
    legend = ax.legend(handles + extra_handles, labels + extra_labels)
    return ax, twin, legend


def test_best_covers_the_twin_and_the_clear_place_covers_neither_scale() -> None:
    ax, twin, legend = _two_scale_panel()
    loc = place_legend_clear(legend, twin)
    placed = _frame(legend)

    best = _best_frame(legend)
    assert _covered(best, twin), "the case no longer puts 'best' on the twin"
    assert not _covered(best, ax)

    assert _covered(placed, ax) == []
    assert _covered(placed, twin) == []
    legend.set_loc(loc)
    assert _frame(legend).bounds == placed.bounds


def test_the_answer_is_the_same_before_the_first_draw_and_after_it() -> None:
    ax, twin, legend = _two_scale_panel()
    before = place_legend_clear(legend, twin)
    ax.figure.canvas.draw()
    assert place_legend_clear(legend, twin) == before


def test_no_artist_is_added_to_or_taken_from_either_axes() -> None:
    ax, twin, legend = _two_scale_panel()
    containers = ("lines", "patches", "collections", "texts", "images", "artists")

    def inventory() -> list[list[int]]:
        return [
            [id(artist) for artist in getattr(axes, name)]
            for axes in (ax, twin)
            for name in containers
        ] + [[id(child) for child in axes.get_children()] for axes in (ax, twin)]

    held = inventory()
    entries = [text.get_text() for text in legend.get_texts()]
    place_legend_clear(legend, twin)
    assert inventory() == held
    assert ax.get_legend() is legend
    assert [text.get_text() for text in legend.get_texts()] == entries


def test_the_box_is_measured_without_a_search_of_its_own(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A legend left at ``"best"`` would search the host just to be measured.

    That search is wasted work, and on a large data set it is the one that
    warns about being slow, on a legend whose place is then fixed anyway.
    """
    _ax, twin, legend = _two_scale_panel()

    def searched(*_args: object) -> tuple[float, float]:
        msg = "the legend was measured at 'best'"
        raise AssertionError(msg)

    monkeypatch.setattr(Legend, "_find_best_position", searched)
    place_legend_clear(legend, twin)
    _frame(legend)


def test_twiny_is_read_through_its_own_abscissa() -> None:
    """A twin that shares the ordinate and keeps its own abscissa."""
    _fig, ax = plt.subplots(figsize=(6.4, 4.8))
    twin = ax.twiny()
    u = np.linspace(0.0, 1.0, 50)
    ax.plot(u, 1.0 - u, label="host")
    # The twin's abscissa runs backwards over a range of its own, so its curve
    # is on the panel only when read through that axis, and there it runs
    # along the top, over the corner the host leaves empty.
    twin.plot(1000.0 - 900.0 * u**4, u**0.25, color="C2", label="twin")
    twin.set_xlim(1000.0, 100.0)
    handles, labels = ax.get_legend_handles_labels()
    extra_handles, extra_labels = twin.get_legend_handles_labels()
    legend = ax.legend(handles + extra_handles, labels + extra_labels)

    place_legend_clear(legend, twin)
    placed = _frame(legend)
    assert _covered(_best_frame(legend), twin)
    assert _covered(placed, ax) == []
    assert _covered(placed, twin) == []


def test_without_a_twin_it_is_the_box_best_would_give() -> None:
    rng = np.random.default_rng(1793)
    for _ in range(12):
        fig, ax = plt.subplots()
        for k in range(3):
            walk = rng.standard_normal(40).cumsum()
            ax.plot(np.linspace(0.0, 1.0, 40), walk, label=f"walk {k}")
        legend = ax.legend()
        best = _best_frame(legend)
        place_legend_clear(legend)
        assert _frame(legend).bounds == pytest.approx(best.bounds)
        plt.close(fig)


def test_gaps_and_a_logarithmic_axis_are_read_without_complaint() -> None:
    _fig, ax = plt.subplots()
    twin = ax.twinx()
    f = np.geomspace(20.0, 20000.0, 30)
    level = 60.0 - 10.0 * np.log10(f / 20.0)
    level[5:8] = np.nan
    ax.semilogx(f, level, "o-", label="level")
    twin.semilogx(f, np.log10(f), label="rising")
    twin.axhline(3.0, color="C3", label="limit")
    legend = ax.legend()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        place_legend_clear(legend, twin)
        placed = _frame(legend)
    assert _covered(placed, ax) == []
    assert _covered(placed, twin) == []


# ---------------------------------------------------------------------------
# The marks the search reads, one at a time. Each panel has fixed unit limits
# and one mark, and a box that the mark reaches only in the way under test,
# next to a control that differs in that one respect and reaches nothing.
# ---------------------------------------------------------------------------


def _unit_panel() -> Axes:
    _fig, ax = plt.subplots(figsize=(6.4, 4.8))
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    return ax


def _box(ax: Axes, x0: float, y0: float, x1: float, y1: float) -> Bbox:
    """A box given in fractions of the axes, in display coordinates."""
    return Bbox(ax.transAxes.transform([[x0, y0], [x1, y1]]))


def _badness(ax: Axes, box: Bbox) -> int:
    marks, extents = _drawn_marks(ax, ax.figure.dpi / 72.0)
    return _legend_badness(box, marks, extents)


@pytest.mark.parametrize("size", [20.0, 2.0])
def test_a_marker_counts_once_its_edge_is_under_the_box(size: float) -> None:
    ax = _unit_panel()
    # A centre two hundredths of the axes below the box: about 7 px on this
    # canvas, less than half a 20 pt marker and more than half a 2 pt one.
    ax.plot([0.5], [0.48], "o", ms=size)
    under = _badness(ax, _box(ax, 0.3, 0.5, 0.7, 0.9))
    assert (under > 0) is (size > 10.0)


@pytest.mark.parametrize("style", ["", "None", "-"])
def test_a_line_drawn_as_markers_alone_has_no_stroke_to_avoid(style: str) -> None:
    """``linestyle=""`` or ``"None"`` keeps a path through the points, undrawn."""
    ax = _unit_panel()
    # Two markers far apart, and a box on the segment between them that only
    # the stroke would reach.
    ax.plot([0.1, 0.9], [0.5, 0.5], marker="o", ms=4, linestyle=style)
    under = _badness(ax, _box(ax, 0.4, 0.45, 0.6, 0.55))
    assert (under > 0) is (style == "-")


@pytest.mark.parametrize("area", [400.0, 4.0])
def test_a_scattered_marker_counts_once_its_edge_is_under_the_box(
    area: float,
) -> None:
    ax = _unit_panel()
    ax.scatter([0.5], [0.48], s=area)
    under = _badness(ax, _box(ax, 0.3, 0.5, 0.7, 0.9))
    assert (under > 0) is (area > 100.0)


@pytest.mark.parametrize("style", ["steps-post", "default"])
def test_a_stepped_line_is_read_through_its_steps(style: str) -> None:
    ax = _unit_panel()
    # Stepped, the line runs along the bottom and up the right edge; straight,
    # it is the diagonal, which the lower right box never meets.
    ax.plot([0.1, 0.9], [0.1, 0.9], drawstyle=style)
    under = _badness(ax, _box(ax, 0.6, 0.05, 0.95, 0.3))
    assert (under > 0) is (style != "default")


@pytest.mark.parametrize(("y0", "y1", "reached"), [(0.4, 0.6, True), (0.7, 0.9, False)])
def test_hlines_are_read_as_the_strokes_they_are(
    y0: float, y1: float, *, reached: bool
) -> None:
    ax = _unit_panel()
    ax.hlines(0.5, 0.1, 0.9)
    assert (_badness(ax, _box(ax, 0.3, y0, 0.7, y1)) > 0) is reached


@pytest.mark.parametrize("words", ["a reading", ""])
def test_a_text_counts_and_an_empty_one_does_not(words: str) -> None:
    ax = _unit_panel()
    ax.text(0.5, 0.5, words, ha="center", va="center")
    under = _badness(ax, _box(ax, 0.4, 0.45, 0.6, 0.55))
    assert (under > 0) is bool(words)


@pytest.mark.parametrize("visible", [True, False])
def test_a_hidden_artist_counts_for_nothing(*, visible: bool) -> None:
    ax = _unit_panel()
    (line,) = ax.plot([0.0, 1.0], [0.5, 0.5])
    bars = ax.bar([0.5], [0.8], width=0.2)
    line.set_visible(visible)
    for bar in bars:
        bar.set_visible(visible)
    under = _badness(ax, _box(ax, 0.3, 0.4, 0.7, 0.6))
    assert (under > 0) is visible


# ---------------------------------------------------------------------------
# Every renderer that puts one legend over two scales.
#
# Each input is shaped for the geometry and nothing else: the host's curves or
# bars leave the corner "best" picks empty, and the twin's data fills it.
# ---------------------------------------------------------------------------


def _transfer_matrix() -> Axes:
    """Transmission loss falling across the band, absorption rising to one.

    Built from its four poles rather than from a layer, because the shape is
    chosen for the geometry and nothing else, and the renderer draws whatever
    matrix it is given.
    """
    f = np.linspace(200.0, 1600.0, 40)
    rho_c = 407.0
    u = (f - f[0]) / (f[-1] - f[0])
    one = np.ones(f.size, dtype=np.complex128)
    series = (rho_c * 10.0 * (1.0 - u)).astype(np.complex128)
    shunt = (1.0 / (rho_c * (1.0 + 5.0 * (1.0 - u)))).astype(np.complex128)
    matrix = ph.materials.TransferMatrix(one, series, shunt, one)
    return matrix.plot(frequencies=f, characteristic_impedance=rho_c)


def _room_to_room() -> Axes:
    """Norton and Karczub problem 4.18, the chain of the published figure.

    On that figure's canvas: on the default one the two-column legend takes a
    third of the panel and no place in it is clear of both scales.
    """
    ceiling = [0.07, 0.20, 0.40, 0.52, 0.60, 0.67]
    walls = [0.03, 0.03, 0.03, 0.04, 0.05, 0.07]
    plant = [(80.0, [0.01, 0.01, 0.015, 0.02, 0.02, 0.02]), (80.0, ceiling),
             (108.0, walls)]  # fmt: skip
    operator = [(25.0, [0.08, 0.24, 0.57, 0.69, 0.71, 0.73]), (25.0, ceiling),
                (60.0, walls)]  # fmt: skip
    result = ph.noise_control.room_to_room_transmission(
        [125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0],
        [39.0, 42.0, 50.0, 58.0, 63.0, 67.0],
        5.0 * 3.0,
        ph.room.equivalent_absorption_area(operator),
        source=ph.noise_control.SourceRoom(
            power_level=[105.0, 103.0, 98.0, 108.0, 107.0, 109.0],
            room_constant=ph.room.room_constant(268.0, ph.room.mean_absorption(plant)),
            directivity=4.0,
            model="constant_volume",
        ),
        criterion=ph.noise_control.DesignCriterion(target=45.0),
        label="Plant room to operator room",
    )
    _fig, ax = plt.subplots(figsize=(10.0, 6.0))
    return result.plot(ax=ax)


def _intensity() -> Axes:
    """Levels falling with frequency, the index between them rising.

    Filled in directly, like the wide-band factory, because the pair of
    signals that would produce a chosen index in every band is beside the
    point of a placement test.
    """
    freqs = _THIRDS[:10]
    lp = np.linspace(80.0, 60.0, freqs.size)
    li = lp - np.linspace(1.0, 10.0, freqs.size)
    result = ph.emission.IntensityResult(
        frequencies=freqs,
        intensity=1.0e-12 * 10.0 ** (li / 10.0),
        intensity_level=li,
        pressure_level=lp,
        pressure_intensity_index=lp - li,
        direction=np.ones(freqs.size),
        bias_correction=np.ones(freqs.size),
        total_intensity=1.0e-6,
        total_intensity_level=60.0,
        total_pressure_level=62.0,
        total_pressure_intensity_index=2.0,
        total_direction=1,
        max_valid_frequency=5000.0,
    )
    return result.plot()


def _field_indicators() -> Axes:
    """A field that grows more uneven band by band as its intensity rises."""
    bands = _THIRDS[3:11]
    pattern = np.array([1.2, -0.8, 0.5, -1.4, 0.9, -0.3, 1.1, -1.2])
    pattern = (pattern - pattern.mean()) / pattern.std(ddof=1)
    mean = 1.0e-6 * 10.0 ** (0.25 * np.arange(bands.size))
    spread = np.linspace(0.05, 0.6, bands.size)
    intensity = mean[None, :] * (1.0 + spread[None, :] * pattern[:, None])
    levels = np.full((pattern.size, bands.size), 74.0)
    return ph.emission.field_indicators(levels, intensity, bands).plot()


def _ship_source_level() -> Axes:
    """A radiated level rising with frequency over the full ISO 17208-2 span."""
    f = np.array([10.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1e3, 2e3, 5e3, 1e4])
    rnl = np.linspace(150.0, 175.0, f.size)
    return ph.underwater.monopole_source_level(rnl, f, 5.0).plot()


#: Two runs falling with frequency, the quieter one faster, so their
#: difference climbs into the corner the runs leave empty. Over the 100 Hz to
#: 5 kHz range each of the four standards asks for.
_LOUDER = 80.0 - 1.0 * np.arange(_THIRDS.size)
_QUIETER = 78.0 - 2.0 * np.arange(_THIRDS.size)
_RUN_BANDS = _THIRDS


def _enclosure() -> Axes:
    return ph.noise_control.sound_power_insulation(
        _LOUDER, _QUIETER, frequencies=_RUN_BANDS
    ).plot()


def _cabin() -> Axes:
    return ph.noise_control.cabin_insulation(
        _LOUDER, _QUIETER, frequencies=_RUN_BANDS
    ).plot()


def _screen() -> Axes:
    return ph.noise_control.screen_attenuation(
        _LOUDER, _QUIETER, frequencies=_RUN_BANDS
    ).plot()


def _barrier() -> Axes:
    return ph.environment.measured_insertion_loss_direct(
        _LOUDER, _LOUDER, _LOUDER, _QUIETER, frequencies=_RUN_BANDS
    ).plot()


def _detailed_airborne() -> Axes:
    """Every path's index rising, so the apparent index climbs to the right."""
    bands = _THIRDS[:16]
    return ph.building.detailed_airborne_prediction(
        bands,
        direct_index=np.linspace(35.0, 65.0, bands.size),
        flanking_paths=[
            BandPath("Ff", "Ff", np.linspace(45.0, 60.0, bands.size)),
            BandPath("Df", "Df", np.linspace(50.0, 75.0, bands.size)),
        ],
    ).plot()


def _detailed_impact() -> Axes:
    """Both levels rising, so the apparent impact level climbs to the right."""
    bands = _THIRDS[:16]
    return ph.building.detailed_impact_prediction(
        bands,
        direct_level=np.linspace(50.0, 75.0, bands.size),
        flanking_paths=[BandPath("Df", "Df", np.linspace(45.0, 72.0, bands.size))],
    ).plot()


#: Source-side levels rising with frequency against a flat intensity, so the
#: index bars grow to the right, and a receiving-side pressure that stands far
#: above the intensity in the lowest band, which puts the indicator's peak in
#: the upper left.
_LF_BANDS = [50.0, 63.0, 80.0, 100.0, 125.0, 160.0]
_LF_SURFACE = [74.0, 78.0, 82.0, 86.0, 90.0, 94.0]
_LF_INTENSITY = [60.0] * 6
_LF_PRESSURE = [80.0, 70.0, 68.0, 66.0, 64.0, 62.0]


def _low_frequency_intensity() -> Axes:
    return ph.building.low_frequency_intensity_reduction(
        _LF_SURFACE,
        _LF_INTENSITY,
        measurement_area=12.0,
        area=10.0,
        l_p=_LF_PRESSURE,
        frequencies=_LF_BANDS,
    ).plot()


def _low_frequency_element() -> Axes:
    return ph.building.low_frequency_element_normalized_difference(
        _LF_SURFACE,
        _LF_INTENSITY,
        measurement_area=12.0,
        l_p=_LF_PRESSURE,
        frequencies=_LF_BANDS,
    ).plot()


def _road_device() -> Axes:
    """An absorber that is poor around 1 kHz, where traffic noise peaks."""
    alpha = [0.9, 0.9, 0.85, 0.8, 0.6, 0.4, 0.3, 0.2, 0.2, 0.2, 0.3, 0.4, 0.6,
             0.8, 0.85, 0.9, 0.9, 0.9]  # fmt: skip
    return ph.environment.sound_absorption_rating(alpha).plot()


RENDERERS: dict[str, Callable[[], Axes]] = {
    "plot_transfer_matrix": _transfer_matrix,
    "plot_room_to_room": _room_to_room,
    "plot_intensity": _intensity,
    "plot_field_indicators": _field_indicators,
    "plot_ship_source_level": _ship_source_level,
    "plot_enclosure_insulation": _enclosure,
    "plot_cabin_insulation": _cabin,
    "plot_screen_in_situ": _screen,
    "plot_barrier_in_situ": _barrier,
    "plot_detailed_airborne_prediction": _detailed_airborne,
    "plot_detailed_impact_prediction": _detailed_impact,
    "plot_low_frequency_intensity": _low_frequency_intensity,
    "plot_low_frequency_element": _low_frequency_element,
    "plot_road_device_rating": _road_device,
}


@pytest.mark.parametrize("draw", RENDERERS.values(), ids=RENDERERS.keys())
def test_the_renderer_places_its_legend_clear_of_the_twin(
    draw: Callable[[], Axes],
) -> None:
    ax = draw()
    twins = _twins(ax)
    assert len(twins) == 1
    legend = ax.get_legend()
    assert legend is not None
    placed = _frame(legend)

    assert _covered(_best_frame(legend), twins[0]), (
        "the case no longer puts 'best' on the twin, so it tests nothing"
    )
    assert _covered(placed, twins[0]) == []
