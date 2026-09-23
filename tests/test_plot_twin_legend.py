#  Copyright (c) 2026. Jose Manuel Requena Plens
"""One legend over two scales, placed clear of both.

matplotlib resolves ``loc="best"`` by scoring its candidate boxes against the
artists of the axes that carries the legend, and an axes made by ``twinx()`` is
a separate axes. On a panel with two scales the second one's curves are
invisible to that search, so the box lands on them as readily as on blank
paper. :func:`~phonometry._plot.common.clearest_legend_loc` runs the same search
against every scale, and each renderer that puts one legend over two scales
places it with that answer.

What is under a legend is measured here without the helper: every stroke of an
axes is sampled along its drawn segments in display coordinates, every marker
is grown by its size and every bar is read by its extent, and the samples that
fall inside the legend's frame are what it covers. Each case is built so that
matplotlib's own ``"best"`` covers the twin's data, which is checked first: a
case where the host alone already finds a clear spot would pass with or without
the fix and prove nothing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cbook import STEP_LOOKUP_MAP
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import Rectangle

import phonometry as ph
from phonometry._plot.common import clearest_legend_loc
from phonometry.building.prediction.detailed_model import BandPath

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from matplotlib.axes import Axes
    from matplotlib.legend import Legend
    from matplotlib.transforms import Bbox

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
        return (box.x0 < x) & (x < box.x1) & (box.y0 < y) & (y < box.y1)


def _sampled(vertices: np.ndarray) -> np.ndarray:
    """The straight segments through *vertices*, sampled finely."""
    finite = vertices[np.isfinite(vertices).all(axis=1)]
    if len(finite) < 2:
        return finite
    t = np.linspace(0.0, 1.0, _SAMPLES_PER_SEGMENT)[None, :, None]
    return (finite[:-1, None, :] * (1.0 - t) + finite[1:, None, :] * t).reshape(-1, 2)


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
        if _inside(box, _sampled(outline.vertices)).any():
            found.append(f"patch {patch.get_label()!r}")
    for collection in ax.collections:
        if isinstance(collection, LineCollection | PolyCollection):
            transform = collection.get_transform()
            for path in collection.get_paths():
                outline = transform.transform_path(path)
                if _inside(box, _sampled(outline.vertices)).any():
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
    legend = ax.legend(handles + extra_handles, labels + extra_labels, loc="best")
    return ax, twin, legend


def test_best_covers_the_twin_and_the_clearest_location_covers_neither_scale() -> None:
    ax, twin, legend = _two_scale_panel()
    loc = clearest_legend_loc(legend, twin)

    best = _best_frame(legend)
    assert _covered(best, twin), "the case no longer puts 'best' on the twin"
    assert not _covered(best, ax)

    legend.set_loc(loc)
    frame = _frame(legend)
    assert _covered(frame, ax) == []
    assert _covered(frame, twin) == []


def test_the_answer_is_the_same_before_the_first_draw_and_after_it() -> None:
    ax, twin, legend = _two_scale_panel()
    before = clearest_legend_loc(legend, twin)
    ax.figure.canvas.draw()
    after = clearest_legend_loc(legend, twin)
    assert before == after
    assert clearest_legend_loc(legend, twin) == after


def test_no_artist_is_added_to_or_taken_from_either_axes() -> None:
    ax, twin, legend = _two_scale_panel()
    legend.set_loc("upper right")
    containers = ("lines", "patches", "collections", "texts", "images", "artists")

    def inventory() -> list[list[int]]:
        return [
            [id(artist) for artist in getattr(axes, name)]
            for axes in (ax, twin)
            for name in containers
        ] + [[id(child) for child in axes.get_children()] for axes in (ax, twin)]

    held = inventory()
    frame = legend.get_window_extent()
    clearest_legend_loc(legend, twin)
    assert inventory() == held
    assert ax.get_legend() is legend
    assert legend.get_window_extent().bounds == frame.bounds


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

    assert _covered(_best_frame(legend), twin)
    legend.set_loc(clearest_legend_loc(legend, twin))
    frame = _frame(legend)
    assert _covered(frame, ax) == []
    assert _covered(frame, twin) == []


def test_without_a_twin_it_is_the_box_best_would_give() -> None:
    rng = np.random.default_rng(1793)
    for _ in range(12):
        fig, ax = plt.subplots()
        for k in range(3):
            walk = rng.standard_normal(40).cumsum()
            ax.plot(np.linspace(0.0, 1.0, 40), walk, label=f"walk {k}")
        legend = ax.legend()
        best = _best_frame(legend)
        legend.set_loc(clearest_legend_loc(legend))
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
    loc = clearest_legend_loc(legend, twin)
    legend.set_loc(loc)
    frame = _frame(legend)
    assert _covered(frame, ax) == []
    assert _covered(frame, twin) == []


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
    series = rho_c * 10.0 * (1.0 - u)
    shunt = 1.0 / (rho_c * (1.0 + 5.0 * (1.0 - u)))
    one = np.ones_like(f)
    matrix = ph.materials.TransferMatrix(one + 0j, series + 0j, shunt + 0j, one + 0j)
    return matrix.plot(f, rho_c)


def _room_to_room() -> Axes:
    """Norton and Karczub problem 4.18, the chain of the published figure.

    On that figure's canvas: on the default one the two-column legend takes a
    third of the panel and no place in it is clear of both scales.
    """
    walls = [0.02, 0.02, 0.03, 0.04, 0.05, 0.05]
    ceiling = [0.05, 0.06, 0.07, 0.08, 0.08, 0.09]
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
        frequency=freqs,
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
    assert _covered(placed, twins[0]) == []

    assert _covered(_best_frame(legend), twins[0]), (
        "the case no longer puts 'best' on the twin, so it tests nothing"
    )
