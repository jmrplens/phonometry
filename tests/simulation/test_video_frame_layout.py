#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A simulation video's frame is laid out once for its whole run, and no text of it leaves the frame.

A frame is at least 479 by 245 pixels: the smallest in which every text keeps
its own size inside the frame's margin, over no other text, and the field
still shows, with matplotlib 3.10 as with 3.11; a smaller one is refused when
the record is built.
"""

from __future__ import annotations

import contextlib
import io
import itertools
import math
import warnings
from typing import TYPE_CHECKING, Any, NamedTuple

import numpy as np
import pytest

pytest.importorskip("matplotlib")
import matplotlib as mpl
from matplotlib import style
from matplotlib.text import Text

from phonometry._plot import simulation as plot
from phonometry.simulation import (
    AnimationFrame,
    ExplosionSource,
    ForceSource,
    GaussianPulse,
)
from phonometry.simulation import video as video_module

if TYPE_CHECKING:
    from collections.abc import Generator

    from matplotlib.backend_bases import RendererBase
    from matplotlib.figure import Figure
    from matplotlib.transforms import Bbox
    from matplotlib.typing import RcKeyType

    from phonometry._i18n import Language
    from phonometry.simulation.elastic_fdtd import ElasticSource

#: The last frame of a long run: 9999.99 ms, four digits before the point,
#: the most a run of up to ten seconds shows (the library's own figures stop
#: at 350 ms).
_LAST_S = 9.99999

#: Frame sizes in pixels: the default, a few others, the size the writers'
#: own tests draw at, and the three at which the layout, when it was made
#: again at every draw, put the y label out.
_SIZES = (
    (960, 540),
    (480, 246),
    (640, 360),
    (1280, 720),
    (720, 720),
    (540, 960),
    (960, 630),
    (832, 540),
    (840, 540),
)

#: Grids from wide to tall, rows by columns: small, so they draw fast.
_GRIDS = {
    "1:10": (6, 60),
    "1:3": (10, 30),
    "1:1": (16, 16),
    "3:1": (30, 10),
    "10:1": (60, 6),
}

#: The field each writer draws, with a colour limit and a cell size each:
#: wide numbers on the colour bar, an offset text above it, numbers of three
#: decimals and of none on the axes.
_FIELDS = {
    "acoustic": ("p", 2500.0, 1.0),
    "elastic p": ("p", 1.0, 0.01),
    "elastic vx": ("vx", 1e-6, 0.001),
    "elastic vy": ("vy", 0.0123, 10.0),
}

#: What the encoder forces while it saves each frame.
_SAVED: dict[RcKeyType, str] = {
    "savefig.bbox": "standard",
    "savefig.dpi": "figure",
    "savefig.facecolor": "auto",
}


#: A text drawn: the artist, what it said, and where it was drawn.
_Drawn = tuple[Text, str, "Bbox"]


@pytest.fixture
def drawn(monkeypatch: pytest.MonkeyPatch) -> list[_Drawn]:
    """Every text drawn, with where it was drawn, as it is drawn."""
    texts: list[_Drawn] = []
    original = Text.draw

    def recording(self: Text, renderer: RendererBase) -> None:
        original(self, renderer)
        if self.get_visible() and self.get_text():
            texts.append((self, self.get_text(), self.get_window_extent(renderer)))

    monkeypatch.setattr(Text, "draw", recording)
    return texts


def _frames(
    kind: str,
    size: tuple[int, int],
    grid: tuple[int, int],
    language: Language,
    times: tuple[float, ...],
) -> Generator[Figure, None, None]:
    """Draw a video's frames at *times*, through the writer's own set-up and update.

    The figure is the writer's, set up under matplotlib's default style for
    the run that ends at the last of *times*, and each frame is saved as the
    encoder saves it; the figure is yielded after each.
    """
    name, limit, dx = _FIELDS[kind]
    rows, columns = grid
    rng = np.random.default_rng(7)
    pulse = GaussianPulse(ix=columns // 2, iy=rows // 2, half_width_s=4e-5)
    where: dict[str, Any] = {
        "dx": dx,
        "shape": grid,
        "probe_positions": np.array([[1.5, 1.5]]) * dx,
        "obstacle_mask": None,
        "decimation": 1,
        "color_limit": limit,
        "time_s": times[0],
        "last_time_s": times[-1],
        "language": language,
    }
    with style.context("default"), mpl.rc_context(_SAVED):
        figure = video_module._frame_figure(size)
        ax = figure.add_subplot()
        if kind == "acoustic":
            image = plot.fdtd_frame(
                ax, rng.standard_normal(grid) * limit, sources=[pulse], **where
            )
        else:
            sources: list[ElasticSource] = [
                ExplosionSource(ix=columns // 2, iy=rows // 2, waveform=pulse.value),
                ForceSource(ix=1, iy=1, direction="x", waveform=pulse.value),
            ]
            image = plot.elastic_frame(
                ax,
                rng.standard_normal(grid) * limit,
                sources=sources,
                snapshot_field=name,
                **where,
            )
        for k, time_s in enumerate(times):
            if k:
                title = (
                    plot.fdtd_snapshot_title(time_s, language)
                    if kind == "acoustic"
                    else plot.elastic_snapshot_title(time_s, name, language)
                )
                plot._update_snapshot(image, rng.standard_normal(grid) * limit, title)
            figure.savefig(io.BytesIO(), format="rgba")
            yield figure


def _outside(extent: Bbox, size: tuple[int, int]) -> bool:
    """Whether *extent* comes within a pixel of the frame's edge, or past it."""
    width, height = size
    return bool(
        extent.x0 < 1
        or extent.y0 < 1
        or extent.x1 > width - 1
        or extent.y1 > height - 1
    )


def _positions(figure: Figure) -> list[tuple[float, ...]]:
    """Where every axes of *figure* sits, the colour bar's included, as drawn."""
    return [tuple(ax.get_position().bounds) for ax in figure.axes]


def _overlap(one: Bbox, other: Bbox) -> bool:
    """Whether two extents share any area, more than touching."""
    across = min(one.x1, other.x1) - max(one.x0, other.x0)
    along = min(one.y1, other.y1) - max(one.y0, other.y0)
    return bool(across > 0 and along > 0)


def _crossings(figure: Figure, drawn: list[_Drawn]) -> list[tuple[str, str]]:
    """The pairs of texts drawn on *figure* that overlap, the title's first.

    Every text counts, the tick labels too: an axis keeps only as many
    ticks as leave its labels apart.
    """
    title = figure.axes[0].title
    heading = [
        (title.get_text(), text)
        for artist, text, extent in drawn
        if artist is not title and _overlap(extent, title.get_window_extent())
    ]
    others = [
        (one_text, other_text)
        for (one, one_text, one_extent), (other, other_text, other_extent) in (
            itertools.combinations(drawn, 2)
        )
        if title not in (one, other) and _overlap(one_extent, other_extent)
    ]
    return heading + others


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("kind", list(_FIELDS))
@pytest.mark.parametrize("size", _SIZES, ids=[f"{w}x{h}" for w, h in _SIZES])
def test_no_text_leaves_the_frame_and_nothing_moves(
    drawn: list[_Drawn], size: tuple[int, int], kind: str, language: Language
) -> None:
    """At every size, for grids from wide to tall: no warning, every text inside, one layout.

    The first frame, one halfway and the last, whose time has the most
    digits of the run, are drawn; after each, every text drawn and every
    axes (the field's and the colour bar's) lie inside the frame, no text
    overlaps the title or another text, and every axes sits where it sat in
    the first.
    """
    times = (0.0, _LAST_S / 2, _LAST_S)
    for grid in _GRIDS.values():
        where = f"{kind} {language} {size} grid {grid}"
        with (
            warnings.catch_warnings(record=True) as caught,
            contextlib.closing(_frames(kind, size, grid, language, times)) as frames,
        ):
            warnings.simplefilter("always")
            first: list[tuple[float, ...]] = []
            for figure in frames:
                out = [
                    (text, extent.extents)
                    for _, text, extent in drawn
                    if _outside(extent, size)
                ]
                assert not out, f"{where}: {out}"
                crossing = _crossings(figure, drawn)
                assert not crossing, f"{where}: {crossing}"
                boxes = [ax.get_window_extent() for ax in figure.axes]
                assert not [box for box in boxes if _outside(box, size)], where
                first = first or _positions(figure)
                assert _positions(figure) == first, where
                drawn.clear()
        assert not [str(w.message) for w in caught], where


def test_the_layout_is_made_once_for_the_widest_title() -> None:
    """The last frame's time is the widest, and nothing is placed again for it."""
    times = (0.0, _LAST_S)
    with contextlib.closing(
        _frames("elastic p", (960, 540), _GRIDS["10:1"], "es", times)
    ) as frames:
        figure = next(frames)
        ax = figure.axes[0]
        title = ax.title
        before = (_positions(figure), title.get_fontsize(), title.get_position())
        assert title.get_text().endswith("= 0,00 ms")
        figure = next(frames)
        assert title.get_text().endswith("= 9999,99 ms")
        after = (_positions(figure), title.get_fontsize(), title.get_position())
    assert after == before


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("kind", ["elastic vx", "elastic vy"])
@pytest.mark.parametrize("width", [479, 960])
@pytest.mark.parametrize("height", [245, 250, 260])
def test_the_colour_bar_s_label_stays_under_the_title(
    drawn: list[_Drawn], height: int, width: int, kind: str, language: Language
) -> None:
    """In a low frame the colour bar's longest label neither reaches the title nor leaves the frame.

    It takes the height from the bottom of the frame to just under the
    title, nothing being under the colour bar, at its own size.
    """
    size = (width, height)
    with contextlib.closing(
        _frames(kind, size, _GRIDS["1:1"], language, (0.0, _LAST_S))
    ) as frames:
        next(frames)
        drawn.clear()
        figure = next(frames)
        label = figure.axes[1].yaxis.label
        extent = label.get_window_extent()
        assert not _outside(extent, size), extent.extents
        assert not _overlap(extent, figure.axes[0].title.get_window_extent())


#: Field axes with less room than the labels matplotlib chooses for them:
#: the frame, the field, the grid and the language, and the labels the x
#: axis then draws. At the floor a tall grid's x axis is some 15 pixels
#: wide, too narrow for "0.00" and "0.05" side by side, so it keeps its
#: first tick alone; at 960 x 630 a 3:1 grid's five labels of four
#: decimals touch, and every second is kept; an axis with room for its
#: labels keeps them all.
_THINNED: dict[str, tuple[tuple[int, int], str, str, Language, list[str]]] = {
    "the first alone": ((479, 245), "elastic p", "10:1", "en", ["0"]),
    "every second": (
        (960, 630),
        "elastic vx",
        "3:1",
        "es",
        ["0,000", "0,005", "0,010"],
    ),
    "all of them": ((479, 245), "acoustic", "10:1", "en", ["0", "5"]),
}


@pytest.mark.parametrize("case", list(_THINNED))
def test_an_axis_keeps_as_many_ticks_as_leave_its_labels_apart(
    drawn: list[_Drawn], case: str
) -> None:
    size, kind, grid, language, shown = _THINNED[case]
    with contextlib.closing(
        _frames(kind, size, _GRIDS[grid], language, (0.0, _LAST_S))
    ) as frames:
        figure = next(frames)
    labels = {id(tick.label1) for tick in figure.axes[0].xaxis.get_major_ticks()}
    assert [text for artist, text, _ in drawn if id(artist) in labels] == shown


def test_a_video_figure_has_no_layout_engine() -> None:
    """Nothing moves the frame's parts at a draw: the set-up placed them for the run."""
    assert video_module._frame_figure((960, 540)).get_layout_engine() is None


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("kind", ["acoustic", "elastic p", "elastic vx"])
def test_a_tall_grid_s_title_fits_the_default_frame_on_one_line_at_its_size(
    kind: str, language: Language
) -> None:
    """A 10:1 grid at 960 x 540: the title is not shrunk, broken or cut."""
    from matplotlib.font_manager import FontProperties

    times = (0.0, _LAST_S)
    with contextlib.closing(
        _frames(kind, (960, 540), _GRIDS["10:1"], language, times)
    ) as frames:
        next(frames)
        title = next(frames).axes[0].title
        own = FontProperties(size=mpl.rcParams["axes.titlesize"]).get_size_in_points()
        assert title.get_fontproperties().get_size_in_points() == pytest.approx(own)
        assert "\n" not in title.get_text()
        assert not _outside(title.get_window_extent(), (960, 540))


def test_the_widest_time_texts_have_every_digit_the_last_one_has() -> None:
    texts = plot._widest_time_texts(9.89596, "es")
    assert texts == [digit * 4 + "," + digit * 2 for digit in "0123456789"]
    assert plot._widest_time_texts(0.00198, "en") == [
        f"{digit}.{digit * 2}" for digit in "0123456789"
    ]


#: The smallest frame a simulation video is drawn at, in pixels.
_FLOOR = (479, 245)

#: The margin, in pixels, the layout keeps between the frame's edges and
#: every text: the pad of matplotlib's points at the frame's dots per inch.
_MARGIN = plot._FRAME_PAD * video_module._DPI / 72.0

#: The narrowest side, in pixels, of a field that still shows.
_FIELD_SHOWS = 14.0

#: The languages a frame's labels are drawn in.
_LANGUAGES: tuple[Language, ...] = ("en", "es")


def _normal_sizes(figure: Figure) -> dict[int, float]:
    """The size, in points, matplotlib's default style gives each text a frame draws, by artist.

    The title is an axes title; the axis labels and the colour bar's label
    are axis labels; the tick labels and the offset texts take the size of
    their axis' tick labels.
    """
    from matplotlib.font_manager import FontProperties

    def points(key: RcKeyType) -> float:
        with style.context("default"):
            return FontProperties(size=mpl.rcParams[key]).get_size_in_points()

    label = points("axes.labelsize")
    sizes = {id(figure.axes[0].title): points("axes.titlesize")}
    for ax in figure.axes:
        for axis, ticks in (
            (ax.xaxis, points("xtick.labelsize")),
            (ax.yaxis, points("ytick.labelsize")),
        ):
            sizes[id(axis.label)] = label
            sizes[id(axis.offsetText)] = ticks
            for tick in axis.get_major_ticks():
                sizes[id(tick.label1)] = sizes[id(tick.label2)] = ticks
    return sizes


def _in_margin(extent: Bbox, size: tuple[int, int]) -> bool:
    """Whether *extent* reaches into the margin the layout keeps at the frame's edges.

    A hundredth of a pixel is allowed for the rounding of the placement.
    """
    width, height = size
    inner = _MARGIN - 0.01
    return bool(
        extent.x0 < inner
        or extent.y0 < inner
        or extent.x1 > width - inner
        or extent.y1 > height - inner
    )


def _defects(
    figure: Figure, drawn: list[_Drawn], size: tuple[int, int]
) -> dict[str, set[str]]:
    """What a frame just drawn shows of what the floor keeps out, by kind; empty when nothing."""
    normal = _normal_sizes(figure)
    field = figure.axes[0].get_window_extent()
    found = {
        "not at its own size": {
            text
            for artist, text, _ in drawn
            if not math.isclose(
                artist.get_fontproperties().get_size_in_points(),
                normal.get(id(artist), 0.0),
            )
        },
        "in the margin": {
            text for _, text, extent in drawn if _in_margin(extent, size)
        },
        "over another text": {f"{a} | {b}" for a, b in _crossings(figure, drawn)},
        "a field that does not show": (
            {f"{field.width:.2f} x {field.height:.2f}"}
            if min(field.width, field.height) < _FIELD_SHOWS
            else set()
        ),
    }
    return {kind: texts for kind, texts in found.items() if texts}


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("kind", list(_FIELDS))
def test_at_the_floor_every_text_keeps_its_size_inside_the_frame_and_the_field_shows(
    drawn: list[_Drawn], kind: str, language: Language
) -> None:
    """479 x 245, on grids from ten times wider than tall to ten times taller.

    The first frame, one halfway and the last, whose time has the most
    digits a run of up to ten seconds shows, drawn as the writer draws
    them: no warning; every text at the size matplotlib's default style
    gives its kind, outside the margin the layout keeps at the frame's
    edges, over no other text, tick labels included; the field at least 14
    pixels on its narrow side. A caller's dark style does not reach the
    frames, which the writers' own tests hold (``test_write_fdtd_animation``):
    here the frames are drawn under the default style by this module's
    helper, so a dark half would test the helper.
    """
    times = (0.0, _LAST_S / 2, _LAST_S)
    for grid in _GRIDS.values():
        where = f"{kind} {language} grid {grid}"
        with (
            warnings.catch_warnings(record=True) as caught,
            contextlib.closing(_frames(kind, _FLOOR, grid, language, times)) as frames,
        ):
            warnings.simplefilter("always")
            for figure in frames:
                assert _defects(figure, drawn, _FLOOR) == {}, where
                drawn.clear()
        assert not [str(w.message) for w in caught], where


class _Measured(NamedTuple):
    """What one matplotlib line was measured to need, a pixel at a time."""

    #: The lowest frame, at the floor's width, whose frames are all clean.
    height: int
    #: The field whose frames, one pixel lower, show what the floor keeps
    #: out (the other fields' show nothing), and what they show, by kind:
    #: the text in the margin, or the size of the field that does not show.
    shown_by: str
    shows: dict[str, set[str]]
    #: The width the widest title of each longer run needs.
    widths: dict[str, int]


#: What each matplotlib line needs. 3.10 sets every text in a box 2 to 6
#: pixels taller than 3.11 does (a title 23 to 25 pixels high, against 18 or
#: 19): one pixel under 245, a field ten times taller than wide, the Spanish
#: v_x one, is under 14 pixels wide there, while 3.11 keeps every frame clean
#: down to 239, under which the Spanish particle velocity's colour bar label,
#: under the tallest title, the one of v_y, reaches into the margin at the
#: bottom. The floor's height is the higher of the two. A title six digits
#: long is a pixel narrower with 3.10, so there the width the writers ask for
#: such a run has a pixel to spare.
_MEASURED = {
    (3, 10): _Measured(
        245,
        "elastic vx",
        {"a field that does not show": {"13.94 x 139.44"}},
        {"five digits": 490, "six digits": 500},
    ),
    (3, 11): _Measured(
        239,
        "elastic vy",
        {"in the margin": {"Velocidad de partícula [m/s]"}},
        {"five digits": 490, "six digits": 501},
    ),
}

#: What the matplotlib the tests run on needs. A line measured on neither is
#: held to the newest one's numbers, so a change in how it sets text goes red
#: here until it is measured.
_HERE = _MEASURED.get(
    (mpl.__version_info__.major, mpl.__version_info__.minor),
    _MEASURED[max(_MEASURED)],
)


def _shown(
    drawn: list[_Drawn],
    kind: str,
    size: tuple[int, int],
    last_s: float = _LAST_S,
    languages: tuple[Language, ...] = _LANGUAGES,
) -> dict[str, set[str]]:
    """What the first and last frames of *kind* show of what the floor keeps out, on every grid."""
    found: dict[str, set[str]] = {}
    for language, grid in itertools.product(languages, _GRIDS.values()):
        with contextlib.closing(
            _frames(kind, size, grid, language, (0.0, last_s))
        ) as frames:
            for figure in frames:
                for what, texts in _defects(figure, drawn, size).items():
                    found.setdefault(what, set()).update(texts)
                drawn.clear()
    return found


@pytest.mark.parametrize("kind", list(_FIELDS))
def test_one_pixel_narrower_than_the_floor_the_widest_title_reaches_the_margin(
    drawn: list[_Drawn], kind: str
) -> None:
    """The Spanish title of the elastic pressure field at its last time, with 3.10 as with 3.11.

    Every text keeps its own size there too, so what shows is a text in the
    margin the layout keeps at the frame's edges, while in both languages'
    frames and on every grid the other fields show nothing. No text covers
    another there, and the field still shows.
    """
    title = "Campo de presión del FDTD elástico en $t$ = 9999,99 ms"
    shows = {"in the margin": {title}} if kind == "elastic p" else {}
    assert _shown(drawn, kind, (_FLOOR[0] - 1, _FLOOR[1])) == shows


@pytest.mark.parametrize("kind", list(_FIELDS))
def test_the_floor_is_as_low_as_the_matplotlib_with_the_tallest_text_allows(
    drawn: list[_Drawn], kind: str
) -> None:
    """At the floor's width, the lowest clean frame on this matplotlib, and one pixel lower.

    With 3.10 that frame is the floor itself, and one pixel lower a 10:1
    field is under 14 pixels wide; 3.11 keeps every frame clean down to 239
    pixels, one under which a colour bar label reaches into the margin.
    Every text keeps its own size there too. What shows is held whole, the
    label or the field's size in pixels, not only its kind, so a frame one
    pixel lower that fails for another text fails here.
    """
    assert _FLOOR[1] == max(line.height for line in _MEASURED.values())
    width = _FLOOR[0]
    assert _shown(drawn, kind, (width, _HERE.height)) == {}
    lower = _shown(drawn, kind, (width, _HERE.height - 1))
    assert lower == (_HERE.shows if kind == _HERE.shown_by else {})


@pytest.mark.parametrize(
    "size", [(478, 245), (479, 244), (479, 239), (64, 64), (478, 1080)]
)
def test_a_frame_under_the_floor_is_refused_naming_it(size: tuple[int, int]) -> None:
    with pytest.raises(ValueError, match=r"at least 479 by 245 pixels"):
        AnimationFrame(size=size)


def test_a_frame_at_the_floor_is_built() -> None:
    assert AnimationFrame(size=(479, 245)).size == _FLOOR


#: A run longer than ten seconds, by the digits before the point of its last
#: frame's time in milliseconds: that time, and the width the writers ask for
#: it, which its title needs with 3.11 (and a pixel less with 3.10, for six).
_LONGER_RUNS = {
    "five digits": (99.99999, 490),
    "six digits": (999.99999, 501),
}


@pytest.mark.parametrize(
    ("last_s", "language", "width"),
    [
        (0.0, "en", 479),
        (9.99999, "es", 479),
        # 9999.996 ms is written 10000.00: the digits the title shows count.
        (9.999996, "en", 490),
        (99.99999, "es", 490),
        (100.0, "en", 501),
        (999.99999, "es", 501),
        (1000.0, "es", 511),
        (1e6, "en", 543),
    ],
)
def test_a_longer_run_needs_a_frame_as_wide_as_its_last_title(
    last_s: float, language: Language, width: int
) -> None:
    """479 pixels hold four digits before the point; each one more takes 10.6 more, rounded up."""
    assert video_module._width_for(last_s, language) == width


@pytest.mark.parametrize("kind", list(_FIELDS))
@pytest.mark.parametrize("run", list(_LONGER_RUNS))
def test_a_longer_run_at_the_width_it_needs_keeps_every_text_clear_of_the_margin(
    drawn: list[_Drawn], run: str, kind: str
) -> None:
    """At the width the writers ask for the run, by 245 pixels: what the floor holds, holds."""
    last_s, width = _LONGER_RUNS[run]
    size = (width, _FLOOR[1])
    for language, grid in itertools.product(_LANGUAGES, _GRIDS.values()):
        where = f"{kind} {language} grid {grid}"
        with (
            warnings.catch_warnings(record=True) as caught,
            contextlib.closing(
                _frames(kind, size, grid, language, (0.0, last_s))
            ) as frames,
        ):
            warnings.simplefilter("always")
            for figure in frames:
                assert _defects(figure, drawn, size) == {}, where
                drawn.clear()
        assert not [str(w.message) for w in caught], where


@pytest.mark.parametrize("run", list(_LONGER_RUNS))
def test_one_pixel_narrower_than_a_longer_run_needs_is_refused_and_would_show(
    drawn: list[_Drawn], run: str
) -> None:
    """The writers refuse it; one pixel under the width the title needs here, it shows.

    The width the writers ask for is never less than the one the run's
    widest title needs on this matplotlib, where that title clears the
    margin, and one pixel narrower it reaches into it.
    """
    last_s, width = _LONGER_RUNS[run]
    narrower = AnimationFrame(size=(width - 1, _FLOOR[1]))
    with pytest.raises(ValueError, match=rf"at least {width} pixels wide"):
        video_module._require_width(narrower, last_s)
    video_module._require_width(AnimationFrame(size=(width, _FLOOR[1])), last_s)
    needs = _HERE.widths[run]
    assert needs <= width
    time_text = plot._time_text(last_s, "es")
    title = f"Campo de presión del FDTD elástico en $t$ = {time_text} ms"
    spanish: tuple[Language, ...] = ("es",)
    assert _shown(drawn, "elastic p", (needs, _FLOOR[1]), last_s, spanish) == {}
    shown = _shown(drawn, "elastic p", (needs - 1, _FLOOR[1]), last_s, spanish)
    assert shown == {"in the margin": {title}}


#: A pad, and how far the labels of a field and of its colour bar reach, in
#: pixels, about what a 960 x 540 frame measures.
_PAD = 7.0
_IMAGE = plot.Reach(left=50.0, right=12.0, bottom=36.0, top=7.0)
_BAR = plot.Reach(left=0.0, right=60.0, bottom=6.0, top=18.0)


def _layout(
    size: tuple[float, float], aspect: float, bar_label: float = 80.0
) -> plot.FrameLayout:
    return plot.frame_layout(
        size,
        pad=_PAD,
        title_height=20.0,
        image=_IMAGE,
        colorbar=_BAR,
        aspect=aspect,
        bar_label=bar_label,
    )


@pytest.mark.parametrize("aspect", [0.1, 1 / 3, 1.0, 3.0, 10.0])
@pytest.mark.parametrize("size", [(960.0, 540.0), (540.0, 960.0), (640.0, 360.0)])
def test_the_layout_keeps_every_reach_inside_the_frame_and_the_cells_square(
    size: tuple[float, float], aspect: float
) -> None:
    width, height = size
    layout = _layout(size, aspect)
    left, bottom, w, h = layout.image
    bar_left, bar_bottom, bar_w, bar_h = layout.colorbar
    assert w / h == pytest.approx(aspect)
    assert left - _IMAGE.left >= _PAD - 1e-9
    assert bottom - max(_IMAGE.bottom, _BAR.bottom) >= _PAD - 1e-9
    assert bar_bottom - _BAR.bottom >= _PAD - 1e-9
    assert bar_left + bar_w + _BAR.right <= width - _PAD + 1e-9
    # The title takes 20 pixels and a pad under it, under the top pad.
    ceiling = height - 2 * _PAD - 20.0
    assert bottom + h + _IMAGE.top <= ceiling + 1e-9
    assert bar_bottom + bar_h + _BAR.top <= ceiling + 1e-9
    # The colour bar sits right of the field's labels, centred on the field.
    assert bar_left >= left + w + _IMAGE.right + 2 * _PAD - 1e-9
    assert bar_bottom + bar_h / 2 == pytest.approx(bottom + h / 2)
    # The field is as large as the slot holds: it meets the slot's sides or
    # its top and bottom.
    reach_right = bar_left + bar_w + _BAR.right
    tall = bottom + h + max(_IMAGE.top, _BAR.top) == pytest.approx(ceiling)
    wide = left - _IMAGE.left == pytest.approx(_PAD)
    assert tall or wide
    # Either way the group is centred: as far from the left edge as the right.
    assert left - _IMAGE.left == pytest.approx(width - reach_right)
    # The colour bar's label lies between the bottom pad and the pad under
    # the title.
    assert layout.label_centre - 40.0 >= _PAD - 1e-9
    assert layout.label_centre + 40.0 <= ceiling + 1e-9


def test_in_a_low_frame_the_colour_bar_s_label_keeps_under_the_title() -> None:
    """The label takes the frame's height under the title, past the field's slot.

    The layout function alone, with no frame built: 320 by 240 pixels is
    under the floor, so no frame is ever drawn at that size, and it is used
    here because there a 199-pixel label is longer than the field's slot,
    the case this test is about.
    """
    layout = _layout((320.0, 240.0), 4 / 3, bar_label=199.0)
    ceiling = 240.0 - 2 * _PAD - 20.0
    assert layout.label_centre - 199.0 / 2 >= _PAD - 1e-9
    assert layout.label_centre + 199.0 / 2 <= ceiling + 1e-9
    # Nothing is under the colour bar: it reaches lower than the field's
    # slot, down to its own labels' reach over the bottom pad.
    bar_bottom = layout.colorbar[1]
    assert bar_bottom < _PAD + _IMAGE.bottom
    assert bar_bottom - _BAR.bottom >= _PAD - 1e-9
    assert bar_bottom + layout.colorbar[3] + _BAR.top <= ceiling + 1e-9


def test_the_colour_bar_is_at_least_as_tall_as_its_label() -> None:
    wide = _layout((960.0, 540.0), 10.0, bar_label=199.0)
    assert wide.image[3] < 199.0
    assert wide.colorbar[3] == pytest.approx(199.0)
    tall = _layout((960.0, 540.0), 0.1, bar_label=199.0)
    assert tall.colorbar[3] == pytest.approx(tall.image[3])
