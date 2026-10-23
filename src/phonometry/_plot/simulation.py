#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Plot renderers for the simulation domain (lazy imports from result .plot())."""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Final

import numpy as np

from .common import (
    _C_MUTED,
    _C_REFERENCE,
    _field_cmap,
    _new_axes,
    refuse_fixed_keywords,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.artist import Artist
    from matplotlib.axes import Axes
    from matplotlib.axis import Axis
    from matplotlib.colorbar import Colorbar
    from matplotlib.image import AxesImage
    from matplotlib.text import Text
    from matplotlib.transforms import Bbox
    from numpy.typing import NDArray

    from .._i18n import Language
    from ..simulation.elastic_fdtd import ElasticFDTDResult, ElasticSource
    from ..simulation.fdtd import AnySource, FDTDResult

_TIME_LABEL = "Time [ms]"
_PRESSURE_LABEL = "Pressure [Pa]"
_VELOCITY_LABEL = "Particle velocity [m/s]"

#: Spanish translations of the fixed strings rendered by the simulation
#: ``.plot()`` renderers, keyed by their verbatim English text. ``_t``
#: returns the English key unchanged for any language other than ``"es"``,
#: so the English output is byte-for-byte identical to the pre-i18n
#: renderers.
_STRINGS: dict[str, str] = {
    "Time [ms]": "Tiempo [ms]",
    "Pressure [Pa]": "Presión [Pa]",
    "FDTD pressure field at $t$ = {t_txt} ms": "Campo de presión FDTD en $t$ = {t_txt} ms",
    "FDTD probe pressure": "Presión en las sondas FDTD",
    "probe": "sonda",
    "Particle velocity [m/s]": "Velocidad de partícula [m/s]",
    "Signal [Pa, m/s]": "Señal [Pa, m/s]",
    "Elastic FDTD probe signals": "Señales en las sondas del FDTD elástico",
    "Elastic FDTD pressure field at $t$ = {t_txt} ms": "Campo de presión del FDTD elástico en $t$ = {t_txt} ms",
    "Elastic FDTD $v_x$ field at $t$ = {t_txt} ms": "Campo de $v_x$ del FDTD elástico en $t$ = {t_txt} ms",
    "Elastic FDTD $v_y$ field at $t$ = {t_txt} ms": "Campo de $v_y$ del FDTD elástico en $t$ = {t_txt} ms",
}

#: Colorbar label of each elastic snapshot field.
_ELASTIC_FIELD_LABELS = {
    "p": _PRESSURE_LABEL,
    "vx": _VELOCITY_LABEL,
    "vy": _VELOCITY_LABEL,
}

#: Snapshot title of each elastic snapshot field. The velocity component is
#: set as mathematics (``$v_x$``, never ``$v_{x}$``): ``_t`` runs ``format``
#: over the whole template, so a brace group other than ``{t_txt}`` would
#: raise :class:`KeyError` at draw time.
_ELASTIC_FIELD_TITLES = {
    "p": "Elastic FDTD pressure field at $t$ = {t_txt} ms",
    "vx": "Elastic FDTD $v_x$ field at $t$ = {t_txt} ms",
    "vy": "Elastic FDTD $v_y$ field at $t$ = {t_txt} ms",
}

#: Legend symbol of each recorded probe field, for the elastic probe legend
#: that prefixes the probe label with the field. A symbol identifier is never
#: translated, so this table is language-independent.
_FIELD_SYMBOLS = {
    "p": "$p$",
    "vx": "$v_x$",
    "vy": "$v_y$",
}

#: The space, in points, a video frame keeps between its edges and what is
#: drawn on it, and between its title and the field below.
_FRAME_PAD: Final = 5.0

#: How many times longer than wide a video frame's colour bar is drawn, at
#: most: matplotlib's own default for a colour bar beside an axes.
_COLORBAR_ASPECT: Final = 20.0


def _t(text: str, language: Language = "en", **fmt: Any) -> str:
    """Localise a fixed string; English is returned verbatim (byte-identical)."""
    s = _STRINGS.get(text, text) if language == "es" else text
    return s.format(**fmt) if fmt else s


def _render_probe_lines(
    ax: Axes,
    t_ms: NDArray[np.float64],
    traces: Sequence[NDArray[np.float64]],
    labels: Sequence[str],
    *,
    xlabel: str,
    ylabel: str,
    title: str,
    language: Language,
    **kwargs: Any,
) -> Axes:
    """Draw labelled probe time histories with the shared styling."""
    from .._i18n import localize_axes

    for trace, label in zip(traces, labels, strict=True):
        trace_kwargs = dict(kwargs)
        trace_kwargs.setdefault("label", label)
        ax.plot(t_ms, trace, **trace_kwargs)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(visible=True, alpha=0.3)
    if labels:
        ax.legend(loc="upper right", fontsize="small")
    localize_axes(ax, language)
    return ax


def _probe_labels(
    positions: NDArray[np.float64],
    language: Language,
) -> list[str]:
    """One ``probe (x, y) m`` label per probe position."""
    from .._i18n import format_number

    label = _t("probe", language)
    out = []
    for k in range(positions.shape[0]):
        x, y = positions[k]
        px = format_number(x, language, decimals=2)
        py = format_number(y, language, decimals=2)
        out.append(f"{label} ({px}, {py}) m")
    return out


def _setup_snapshot(
    ax: Axes,
    field: NDArray[np.floating],
    *,
    shape: tuple[int, int],
    obstacle_mask: NDArray[np.bool_] | None,
    source_positions: Sequence[tuple[float, float]],
    probe_positions: NDArray[np.float64],
    colorbar_label: str,
    title: str,
    language: Language,
    decimation: int,
    dx: float,
    **kwargs: Any,
) -> AxesImage:
    """Render one field raster with the geometry overlaid, its colour bar beside it.

    The snapshot plot's own figure: the field as :func:`_draw_field` draws
    it, on a scale taken from this field, with the colour bar matplotlib
    places beside the axes and the title over them.
    """
    from .._i18n import localize_axes

    img = _draw_field(
        ax,
        field,
        shape=shape,
        obstacle_mask=obstacle_mask,
        source_positions=source_positions,
        probe_positions=probe_positions,
        decimation=decimation,
        dx=dx,
        color_limit=None,
        **kwargs,
    )
    cbar = ax.figure.colorbar(img, ax=ax, label=colorbar_label)
    localize_axes(cbar.ax, language)
    ax.set_xlabel("$x$ [m]")
    ax.set_ylabel("$y$ [m]")
    ax.set_title(title)
    localize_axes(ax, language)
    return img


def _draw_field(
    ax: Axes,
    field: NDArray[np.floating],
    *,
    shape: tuple[int, int],
    obstacle_mask: NDArray[np.bool_] | None,
    source_positions: Sequence[tuple[float, float]],
    probe_positions: NDArray[np.float64],
    decimation: int,
    dx: float,
    color_limit: float | None,
    **kwargs: Any,
) -> AxesImage:
    """Draw one field raster with the geometry overlaid (shared core).

    The domain is the ``shape`` grid of spacing ``dx``, the product a result's
    ``size`` is. A field recorded with ``decimation`` d keeps the first cell
    of every d by d block of that grid; the obstacle map is the whole grid
    whatever the field keeps, and is drawn over the domain.

    ``color_limit`` fixes the symmetric colour scale, as a video needs for all
    its frames; ``None`` takes it from this field. Returns the image, which
    :func:`_update_snapshot` redraws.
    """
    ny, nx = shape
    lx, ly = nx * dx, ny * dx
    domain = (0.0, lx, ly, 0.0)
    if decimation == 1:
        extent = domain
    else:
        # Each sample is the first cell of a decimation-by-decimation block,
        # drawn over that block; the last block may overhang the domain, and
        # the axis limits below cut it at the edge.
        rows, cols = field.shape
        extent = (0.0, cols * decimation * dx, rows * decimation * dx, 0.0)
    # A video fixes the scale for all its frames; a single plot takes it
    # from the field it draws, as it always has.
    vmax = (float(np.abs(field).max()) or 1.0) if color_limit is None else color_limit
    img = ax.imshow(
        field,
        **{
            "cmap": _field_cmap(ax),
            "vmin": -vmax,
            "vmax": vmax,
            "origin": "upper",
            "extent": extent,
            "interpolation": "nearest",
            **kwargs,
        },
    )
    if obstacle_mask is not None:
        overlay = np.ma.masked_where(~obstacle_mask, np.ones(shape))
        ax.imshow(
            overlay,
            cmap="gray",
            vmin=0.0,
            vmax=2.0,
            origin="upper",
            extent=domain,
            interpolation="nearest",
        )
    if decimation > 1:
        ax.set_xlim(0.0, lx)
        ax.set_ylim(ly, 0.0)
    for x, y in source_positions:
        ax.plot(x, y, marker="*", markersize=10, color=_C_REFERENCE, linestyle="none")
    for k in range(probe_positions.shape[0]):
        x, y = probe_positions[k]
        ax.plot(
            x,
            y,
            marker="o",
            markersize=5,
            color=_C_MUTED,
            markeredgecolor="black",
            linestyle="none",
        )
    return img


def _update_snapshot(image: AxesImage, field: NDArray[np.floating], title: str) -> None:
    """Draw the next field and its time into a video frame :func:`fdtd_frame` or :func:`elastic_frame` built.

    The data and the title's text change; the colour scale, the overlays,
    the colour bar, the axes and where each sits do not, so every frame of a
    video shares them.
    """
    image.set_data(field)
    image.axes.title.set_text(title)


def _time_text(time_s: float, language: Language) -> str:
    """A time in milliseconds, two decimals, in the language's notation."""
    from .._i18n import format_number

    return format_number(float(time_s) * 1000.0, language, decimals=2)


def _widest_time_texts(last_time_s: float, language: Language) -> list[str]:
    """The time texts as wide as any a run that ends at *last_time_s* shows.

    Times only grow, so no frame's time has more digits than the last
    one's. Each text here is the last one's with every digit set to one of
    the ten, so the widest of them is at least as wide as any time the run
    shows, whatever the font makes of each digit.
    """
    shown = _time_text(last_time_s, language)
    return [
        shown.translate(str.maketrans("0123456789", digit * 10))
        for digit in "0123456789"
    ]


def _fdtd_title(time_text: str, language: Language) -> str:
    """The title of an acoustic field at the time *time_text* (in milliseconds) writes."""
    return _t("FDTD pressure field at $t$ = {t_txt} ms", language, t_txt=time_text)


def _elastic_title(time_text: str, snapshot_field: str, language: Language) -> str:
    """The title of an elastic field at the time *time_text* (in milliseconds) writes."""
    return _t(_ELASTIC_FIELD_TITLES[snapshot_field], language, t_txt=time_text)


def fdtd_snapshot_title(time_s: float, language: Language) -> str:
    """The title of an acoustic field drawn at *time_s* seconds."""
    return _fdtd_title(_time_text(time_s, language), language)


def elastic_snapshot_title(
    time_s: float, snapshot_field: str, language: Language
) -> str:
    """The title of an elastic field (``"p"``, ``"vx"``, ``"vy"``) at *time_s* seconds."""
    return _elastic_title(_time_text(time_s, language), snapshot_field, language)


@dataclass(frozen=True)
class Reach:
    """How far, in pixels, an axes' tick labels, axis labels and offset text reach past each of its edges."""

    left: float
    right: float
    bottom: float
    top: float


@dataclass(frozen=True)
class FrameLayout:
    """Where the field, its colour bar and the bar's label sit in a video frame, for the whole run.

    ``image`` and ``colorbar`` are ``(left, bottom, width, height)``, and
    ``label_centre`` the height of the middle of the colour bar's label, in
    pixels from the frame's lower left corner.
    """

    image: tuple[float, float, float, float]
    colorbar: tuple[float, float, float, float]
    label_centre: float


def _clamped(value: float, low: float, high: float) -> float:
    """*value* moved into ``[low, high]``; to *high* when the two cross."""
    return min(max(value, low), high)


def frame_layout(
    frame: tuple[float, float],
    *,
    pad: float,
    title_height: float,
    image: Reach,
    colorbar: Reach,
    aspect: float,
    bar_label: float,
) -> FrameLayout:
    """Place a video frame's field and colour bar under its title, every label inside the frame.

    The title takes the top of the frame, *title_height* pixels below a
    *pad*, and nothing is drawn within a pad under it. The field takes the
    slot left under that, above what the axes' labels need below them, and
    keeps its cells square: an image *aspect* times wider than tall, as
    large as the slot holds. Its axis labels reach out to its left, the
    colour bar sits to its right, and the group of the two is centred
    across the frame. Nothing is drawn under the colour bar, so it may
    reach lower than the field, down to its own labels' reach over the
    bottom pad: it is centred on the field, at least as tall as its own
    label (*bar_label* pixels) where that room allows, and moved into it
    where it does not. Its label is centred on it, and moved, where it must
    be, into the height from the bottom pad to the pad under the title; if
    it is longer than that height it keeps under the title. Nothing reaches
    within *pad* pixels of an edge while the frame holds it all; a frame
    too small for that still gets a field of at least one pixel.

    :param frame: ``(width, height)`` of the frame in pixels.
    :param pad: The space kept at each edge and under the title, in pixels.
    :param title_height: The height of the title at its widest, in pixels.
    :param image: How far the field's labels reach past its axes.
    :param colorbar: How far the colour bar's labels reach past it, its
        own label left out of the top and the bottom.
    :param aspect: The field's width over its height.
    :param bar_label: The length of the colour bar's label, in pixels.
    :return: Where the field, the colour bar and its label sit.
    """
    width, height = frame
    under_title = height - 2.0 * pad - title_height
    floor = pad + max(image.bottom, colorbar.bottom)
    ceiling = under_title - max(image.top, colorbar.top)
    slot_height = max(ceiling - floor, 1.0)
    bar = min(slot_height, width / 2.0) / _COLORBAR_ASPECT
    gap = max(image.right, colorbar.left) + 2.0 * pad
    beside = image.left + gap + bar + colorbar.right
    slot_width = max(width - 2.0 * pad - beside, 1.0)
    field_width = min(slot_width, slot_height * aspect)
    field_height = field_width / aspect
    left = (width - beside - field_width) / 2.0 + image.left
    bottom = floor + (slot_height - field_height) / 2.0
    bar_floor = pad + colorbar.bottom
    bar_room = max(under_title - colorbar.top - bar_floor, 1.0)
    bar_height = min(max(field_height, bar_label), bar_room)
    bar_bottom = _clamped(
        bottom + (field_height - bar_height) / 2.0,
        bar_floor,
        bar_floor + bar_room - bar_height,
    )
    label_centre = _clamped(
        bar_bottom + bar_height / 2.0,
        pad + bar_label / 2.0,
        under_title - bar_label / 2.0,
    )
    return FrameLayout(
        image=(left, bottom, field_width, field_height),
        colorbar=(left + field_width + gap, bar_bottom, bar, bar_height),
        label_centre=label_centre,
    )


def _title_height(title: Text, texts: Sequence[str]) -> float:
    """The height, in pixels, of the tallest of *texts* set in *title*'s font; *title* keeps its own text."""
    shown = title.get_text()
    heights = []
    for text in texts:
        title.set_text(text)
        heights.append(title.get_window_extent().height)
    title.set_text(shown)
    return max(heights)


def _reach(ax: Axes, *parts: Artist) -> Reach:
    """How far *parts* (an axes' axes, their labels and ticks) reach past *ax*'s edges, in pixels."""
    from matplotlib.transforms import Bbox

    box = ax.get_window_extent()
    found = (part.get_tightbbox() for part in parts)
    whole = Bbox.union([box, *(extent for extent in found if extent is not None)])
    return Reach(
        left=box.x0 - whole.x0,
        right=whole.x1 - box.x1,
        bottom=box.y0 - whole.y0,
        top=whole.y1 - box.y1,
    )


def _colorbar_reach(colorbar: Colorbar) -> tuple[Reach, float]:
    """How far a colour bar's labels reach past it, and the length of its own label, in pixels.

    Its label is centred along the bar, which :func:`frame_layout` makes at
    least as long, so the label counts across the bar and not along it.
    """
    axis = colorbar.long_axis
    across = _reach(colorbar.ax, axis)
    axis.label.set_visible(False)
    try:
        along = _reach(colorbar.ax, axis)
    finally:
        axis.label.set_visible(True)
    reach = Reach(
        left=across.left, right=across.right, bottom=along.bottom, top=along.top
    )
    return reach, axis.label.get_window_extent().height


def _measured_layout(
    ax: Axes,
    colorbar: Colorbar,
    frame: tuple[float, float],
    pad: float,
    title_height: float,
) -> FrameLayout:
    """The layout :func:`frame_layout` gives for what *ax* and *colorbar* draw as they stand."""
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    bar, bar_label = _colorbar_reach(colorbar)
    return frame_layout(
        frame,
        pad=pad,
        title_height=title_height,
        image=_reach(ax, ax.xaxis, ax.yaxis),
        colorbar=bar,
        aspect=abs(x1 - x0) / abs(y1 - y0),
        bar_label=bar_label,
    )


def _place(ax: Axes, colorbar: Colorbar, layout: FrameLayout) -> None:
    """Move the field's axes, the colour bar and its label to where *layout* puts them.

    The label's height is set along the bar, in the bar's own fractions;
    how far it sits beside the bar matplotlib keeps finding from the bar's
    tick labels.
    """
    _, bar_bottom, _, bar_height = layout.colorbar
    colorbar.long_axis.label.set_y((layout.label_centre - bar_bottom) / bar_height)
    box = ax.figure.bbox
    for axes, (left, bottom, width, height) in (
        (ax, layout.image),
        (colorbar.ax, layout.colorbar),
    ):
        axes.set_position(
            (
                left / box.width,
                bottom / box.height,
                width / box.width,
                height / box.height,
            )
        )


def _overlapping(one: Bbox, other: Bbox) -> bool:
    """Whether two extents share any area, more than touching."""
    across = min(one.x1, other.x1) - max(one.x0, other.x0)
    along = min(one.y1, other.y1) - max(one.y0, other.y0)
    return bool(across > 0 and along > 0)


def _crowded(axis: Axis, locs: Sequence[float], drawn: Sequence[bool]) -> bool:
    """Whether, with its ticks at *locs*, two neighbouring labels *axis* draws overlap.

    *drawn* says, tick by tick, which are in view and so drawn; their labels
    are set as the axis' formatter writes them for *locs*.
    """
    from matplotlib.ticker import FixedLocator

    axis.set_major_locator(FixedLocator(locs))
    axis.get_majorticklabels()  # writes every tick's label for these locations
    labels = [
        label
        for tick, seen in zip(axis.get_major_ticks(len(locs)), drawn, strict=True)
        if seen
        for label in (tick.label1, tick.label2)
        if label.get_visible()
    ]
    extents = [label.get_window_extent() for label in labels]
    return any(_overlapping(*pair) for pair in itertools.pairwise(extents))


def _apart(axis: Axis) -> list[float]:
    """Where *axis* keeps its ticks: where they stand, or as few of them as keep their labels apart.

    When no two neighbouring labels of the ticks in view overlap, the ticks
    stay as they are. Otherwise every second tick in view is kept, counting
    from the first, then every third, and so on, the first step at which no
    two neighbouring labels overlap; an axis too short for even its first
    and last labels side by side keeps the first alone. So a narrow field's
    axis is never labelled with one number written over another.
    """
    locs: list[float] = axis.get_majorticklocs().tolist()
    low, high = sorted(axis.get_view_interval())
    # As matplotlib draws a tick that rounding puts a hair outside the view.
    slack = (high - low) * 1e-10
    drawn = [low - slack <= loc <= high + slack for loc in locs]
    if not _crowded(axis, locs, drawn):
        return locs
    shown = list(itertools.compress(locs, drawn))
    for step in range(2, len(shown)):
        kept = shown[::step]
        if not _crowded(axis, kept, [True] * len(kept)):
            return kept
    return shown[:1]


def _hold_ticks(ax: Axes, colorbar: Colorbar) -> None:
    """Fix the ticks of the field's axes and of the colour bar where they stand now.

    Each keeps as many of them as leave its labels apart (:func:`_apart`).
    """
    from matplotlib.ticker import FixedLocator

    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_locator(FixedLocator(_apart(axis)))
    colorbar.locator = FixedLocator(_apart(colorbar.long_axis))


def lay_out_frame(
    ax: Axes, colorbar: Colorbar, *, title: str, widest: Sequence[str]
) -> None:
    """Lay a video frame out once, for every title and label its run shows.

    *title* is the first frame's, set over the whole frame at its own size,
    its top a pad below the frame's, in a band as tall as the tallest of
    *widest*, titles as wide as any the run shows. Every text keeps its own
    size: a video's frame is never smaller than the one in which they all
    fit, each inside the frame and over no other. The field's axes, the
    colour bar and its label go where :func:`frame_layout` puts them for the
    labels they draw. Their ticks are then fixed, as many on each axis as
    leave its labels apart (:func:`_apart`), which fixes the labels, and
    they are placed once more for those. Nothing is placed again: the
    figure has no layout engine, so each frame draws into this layout, and
    only the field and the title's text change (:func:`_update_snapshot`).
    """
    figure = ax.figure
    # The frame is the whole pixels of the figure.
    frame = (math.floor(figure.bbox.width), math.floor(figure.bbox.height))
    pad = _FRAME_PAD * figure.dpi / 72.0
    ax.set_title(
        title,
        x=frame[0] / 2.0 / figure.bbox.width,
        y=(frame[1] - pad) / figure.bbox.height,
        transform=figure.transFigure,
        verticalalignment="top",
    )
    title_height = _title_height(ax.title, widest)
    _place(ax, colorbar, _measured_layout(ax, colorbar, frame, pad, title_height))
    _hold_ticks(ax, colorbar)
    _place(ax, colorbar, _measured_layout(ax, colorbar, frame, pad, title_height))


def _video_snapshot(
    ax: Axes,
    field: NDArray[np.floating],
    *,
    shape: tuple[int, int],
    obstacle_mask: NDArray[np.bool_] | None,
    source_positions: Sequence[tuple[float, float]],
    probe_positions: NDArray[np.float64],
    colorbar_label: str,
    title: str,
    widest: Sequence[str],
    language: Language,
    decimation: int,
    dx: float,
    color_limit: float,
) -> AxesImage:
    """The first frame of a video: the snapshot plot's field and labels, laid out once.

    The field, its colour scale and its colormap are the snapshot plot's;
    the colour bar is drawn on axes of its own, and the title over the
    whole frame rather than over the field, so that :func:`lay_out_frame`
    can place both, once, for the widest title in *widest*.
    """
    from .._i18n import localize_axes

    image = _draw_field(
        ax,
        field,
        shape=shape,
        obstacle_mask=obstacle_mask,
        source_positions=source_positions,
        probe_positions=probe_positions,
        decimation=decimation,
        dx=dx,
        color_limit=color_limit,
    )
    figure = ax.figure
    # Where the colour bar starts is of no matter: the layout moves it.
    colorbar = figure.colorbar(
        image, cax=figure.add_axes((0.9, 0.1, 0.02, 0.8)), label=colorbar_label
    )
    localize_axes(colorbar.ax, language)
    ax.set_xlabel("$x$ [m]")
    ax.set_ylabel("$y$ [m]")
    localize_axes(ax, language)
    lay_out_frame(ax, colorbar, title=title, widest=widest)
    return image


def acoustic_source_positions(
    sources: Sequence[AnySource], dx: float
) -> list[tuple[float, float]]:
    """Where to mark each point source; a plane wave has no cell to mark."""
    from ..simulation.fdtd import PlaneWaveSource

    return [
        ((s.ix + 0.5) * dx, (s.iy + 0.5) * dx)
        for s in sources
        if not isinstance(s, PlaneWaveSource)
    ]


def elastic_source_positions(
    sources: Sequence[ElasticSource], dx: float
) -> list[tuple[float, float]]:
    """Where to mark each elastic source (a force at its velocity node)."""
    return [_elastic_source_position(s, dx) for s in sources]


def fdtd_frame(
    ax: Axes,
    field: NDArray[np.floating],
    *,
    dx: float,
    shape: tuple[int, int],
    sources: Sequence[AnySource],
    probe_positions: NDArray[np.float64],
    obstacle_mask: NDArray[np.bool_] | None,
    decimation: int,
    color_limit: float,
    time_s: float,
    last_time_s: float,
    language: Language,
) -> AxesImage:
    """The first frame of an acoustic video, at *time_s*, laid out for every frame up to *last_time_s*.

    The snapshot plot's field, colour scale and colormap, on the scale
    *color_limit* fixes, laid out once (:func:`lay_out_frame`) for the
    widest title the run shows.
    """
    return _video_snapshot(
        ax,
        np.asarray(field, dtype=np.float64),
        shape=shape,
        obstacle_mask=obstacle_mask,
        source_positions=acoustic_source_positions(sources, dx),
        probe_positions=probe_positions,
        colorbar_label=_t(_PRESSURE_LABEL, language),
        title=fdtd_snapshot_title(time_s, language),
        widest=[
            _fdtd_title(text, language)
            for text in _widest_time_texts(last_time_s, language)
        ],
        language=language,
        decimation=decimation,
        dx=dx,
        color_limit=color_limit,
    )


def elastic_frame(
    ax: Axes,
    field: NDArray[np.floating],
    *,
    dx: float,
    shape: tuple[int, int],
    sources: Sequence[ElasticSource],
    probe_positions: NDArray[np.float64],
    obstacle_mask: NDArray[np.bool_] | None,
    decimation: int,
    snapshot_field: str,
    color_limit: float,
    time_s: float,
    last_time_s: float,
    language: Language,
) -> AxesImage:
    """The first frame of an elastic video, as :func:`fdtd_frame` draws an acoustic one."""
    return _video_snapshot(
        ax,
        np.asarray(field, dtype=np.float64),
        shape=shape,
        obstacle_mask=obstacle_mask,
        source_positions=elastic_source_positions(sources, dx),
        probe_positions=probe_positions,
        colorbar_label=_t(_ELASTIC_FIELD_LABELS[snapshot_field], language),
        title=elastic_snapshot_title(time_s, snapshot_field, language),
        widest=[
            _elastic_title(text, snapshot_field, language)
            for text in _widest_time_texts(last_time_s, language)
        ],
        language=language,
        decimation=decimation,
        dx=dx,
        color_limit=color_limit,
    )


def plot_fdtd_probes(
    result: FDTDResult,
    ax: Axes | None = None,
    *,
    language: Language = "en",
    **kwargs: Any,
) -> Axes:
    """Pressure time history at each probe of an FDTD run.

    :param result: A :class:`~phonometry.simulation.fdtd.FDTDResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``Axes.plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    t_ms = np.asarray(result.times, dtype=np.float64) * 1000.0
    return _render_probe_lines(
        ax,
        t_ms,
        [result.pressures[k] for k in range(result.pressures.shape[0])],
        _probe_labels(result.probe_positions, language),
        xlabel=_t(_TIME_LABEL, language),
        ylabel=_t(_PRESSURE_LABEL, language),
        title=_t("FDTD probe pressure", language),
        language=language,
        **kwargs,
    )


def plot_fdtd_snapshot(
    result: FDTDResult,
    ax: Axes | None = None,
    *,
    frame: int = -1,
    language: Language = "en",
    **kwargs: Any,
) -> Axes:
    """One recorded pressure-field snapshot with the geometry overlaid.

    The field is rendered as a single raster image (``imshow``, symmetric
    diverging scale); rigid obstacle cells are drawn in grey and the source
    and probe cells are marked.  The default colormap follows the axes
    background so zero pressure blends into the page -- ``RdBu_r`` on a
    light background, the black-centred ``phonometry_field_dark`` on a dark
    one -- and ``cmap`` overrides it. A snapshot recorded with
    ``snapshot_decimation`` d draws each sample over the d by d block of
    cells it was taken from, and the axes still end at the domain's edges:
    when d > 1 their limits are fixed there, which turns autoscaling off for
    anything drawn on them afterwards; with d = 1 they are left to autoscale.

    :param result: A :class:`~phonometry.simulation.fdtd.FDTDResult` with
        recorded snapshots.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param frame: Snapshot index (default: the last recorded frame).
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``imshow``.
    :return: The axes.
    :raises TypeError: for ``color_limit``, which the field drawn sets
        (``vmin`` and ``vmax`` reach ``imshow``).
    :raises ValueError: If the result holds no snapshots.
    """
    if result.snapshots is None or result.snapshot_times is None:
        msg = (
            "the result holds no snapshots; rerun the "
            "simulation with snapshot_every set"
        )
        raise ValueError(msg)
    refuse_fixed_keywords(
        kwargs,
        "plot_fdtd_snapshot",
        "color_limit",
        reason="takes its colour scale from the field it draws, or from vmin and vmax",
    )
    ax = ax if ax is not None else _new_axes()
    _setup_snapshot(
        ax,
        np.asarray(result.snapshots[frame], dtype=np.float64),
        shape=result.shape,
        obstacle_mask=result.obstacle_mask,
        source_positions=acoustic_source_positions(result.sources, result.dx),
        probe_positions=result.probe_positions,
        colorbar_label=_t(_PRESSURE_LABEL, language),
        title=fdtd_snapshot_title(float(result.snapshot_times[frame]), language),
        language=language,
        decimation=result.snapshot_decimation,
        dx=result.dx,
        **kwargs,
    )
    return ax


def _elastic_source_position(
    source: ElasticSource,
    dx: float,
) -> tuple[float, float]:
    """Physical position of an elastic source marker."""
    from ..simulation.elastic_fdtd import ForceSource

    if isinstance(source, ForceSource):
        if source.direction == "x":
            return (source.ix + 1.0) * dx, (source.iy + 0.5) * dx
        return (source.ix + 0.5) * dx, (source.iy + 1.0) * dx
    return (source.ix + 0.5) * dx, (source.iy + 0.5) * dx


def plot_elastic_probes(
    result: ElasticFDTDResult,
    ax: Axes | None = None,
    *,
    language: Language = "en",
    **kwargs: Any,
) -> Axes:
    """Recorded time history of every probe/field pair of an elastic run.

    One line per probe and recorded field; the field name prefixes the
    probe label when more than one field was recorded.

    :param result: An
        :class:`~phonometry.simulation.elastic_fdtd.ElasticFDTDResult`.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``Axes.plot``.
    :return: The axes.
    """
    ax = ax if ax is not None else _new_axes()
    t_ms = np.asarray(result.times, dtype=np.float64) * 1000.0
    base = _probe_labels(result.probe_positions, language)
    many = len(result.probe_fields) > 1
    traces = []
    labels = []
    for k in range(result.signals.shape[0]):
        for j, field in enumerate(result.probe_fields):
            traces.append(result.signals[k, j])
            symbol = _FIELD_SYMBOLS.get(field, field)
            labels.append(f"{symbol}, {base[k]}" if many else base[k])
    if set(result.probe_fields) <= {"vx", "vy"}:
        ylabel = _VELOCITY_LABEL
    elif result.probe_fields == ("p",):
        ylabel = _PRESSURE_LABEL
    else:
        ylabel = "Signal [Pa, m/s]"
    return _render_probe_lines(
        ax,
        t_ms,
        traces,
        labels,
        xlabel=_t(_TIME_LABEL, language),
        ylabel=_t(ylabel, language),
        title=_t("Elastic FDTD probe signals", language),
        language=language,
        **kwargs,
    )


def plot_elastic_snapshot(
    result: ElasticFDTDResult,
    ax: Axes | None = None,
    *,
    frame: int = -1,
    language: Language = "en",
    **kwargs: Any,
) -> Axes:
    """One recorded elastic field snapshot with the geometry overlaid.

    Renders the recorded ``snapshot_field`` (synthetic pressure or one
    velocity component, at cell centres) with the same raster styling as
    the acoustic snapshot renderer, including its background-aware default
    colormap (``RdBu_r`` on a light axes background, the black-centred
    ``phonometry_field_dark`` on a dark one; ``cmap`` overrides it) and its
    drawing of a decimated snapshot, each sample over its block of cells,
    with the axes limits fixed to the domain (autoscaling off) when
    ``snapshot_decimation`` is greater than 1.

    :param result: An
        :class:`~phonometry.simulation.elastic_fdtd.ElasticFDTDResult`
        with recorded snapshots.
    :param ax: Existing axes, or ``None`` to create a figure.
    :param frame: Snapshot index (default: the last recorded frame).
    :param language: Label language, ``"en"`` (default) or ``"es"``.
    :param kwargs: Forwarded to ``imshow``.
    :return: The axes.
    :raises TypeError: for ``color_limit``, which the field drawn sets
        (``vmin`` and ``vmax`` reach ``imshow``).
    :raises ValueError: If the result holds no snapshots.
    """
    if result.snapshots is None or result.snapshot_times is None:
        msg = (
            "the result holds no snapshots; rerun the "
            "simulation with snapshot_every set"
        )
        raise ValueError(msg)
    refuse_fixed_keywords(
        kwargs,
        "plot_elastic_snapshot",
        "color_limit",
        reason="takes its colour scale from the field it draws, or from vmin and vmax",
    )
    ax = ax if ax is not None else _new_axes()
    _setup_snapshot(
        ax,
        np.asarray(result.snapshots[frame], dtype=np.float64),
        shape=result.shape,
        obstacle_mask=result.obstacle_mask,
        source_positions=elastic_source_positions(result.sources, result.dx),
        probe_positions=result.probe_positions,
        colorbar_label=_t(_ELASTIC_FIELD_LABELS[result.snapshot_field], language),
        title=elastic_snapshot_title(
            float(result.snapshot_times[frame]), result.snapshot_field, language
        ),
        language=language,
        decimation=result.snapshot_decimation,
        dx=result.dx,
        **kwargs,
    )
    return ax
