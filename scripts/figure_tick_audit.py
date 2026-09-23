#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Record, while the figures are being generated, which tick labels run together.

Two defects, and the first is a special case of a class the second measures
in general:

* **stray.** A generator places the major ticks of an axis by hand
  (``set_xticks`` with the band labels, on a logarithmic axis) and leaves the
  minor formatter where the scale put it. matplotlib then keeps labelling the
  minor ticks in its own notation between the hand-written ones, and a band
  axis that should read "125 250 500 1k" reads "2 × 10²50 4 × 10²500": the
  labels nobody asked for land on the ones that were. The library's own axis
  helpers (``format_frequency_axis`` and the private ones built on it) clear
  the minor formatter; the defect is always a generator that took the major
  ticks over itself, which is why a hand-set locator or formatter is what
  makes it one. An axis whose majors are left to the scale and whose minors
  are labelled is matplotlib doing what it was designed to do on a short
  span, and is left to the second measure.
* **overlap.** Any two labels one axis draws whose boxes run into each other,
  whoever wrote them: two hand-set labels too close for their width, the
  radial labels of a polar plot strung along one ray, a crowded category
  axis, or the stray labels above.

Neither can be read off the shipped file. ``svg.fonttype = "path"`` writes
every label as glyph outlines, so ``.github/images`` holds no text to find a
tick label in, and which of two labels at one spot is a minor one is a fact
about the axis, not about the drawing. So it is measured here, on the live
figure, as it is saved.

What a label's box is
---------------------

The line box ``Text.get_window_extent`` returns: the advance widths of the
characters across, ascent to descent up. Captured while the label draws
(:func:`_drawn_labels`), for the reason the annotation audit gives about
three-dimensional plates: the axis of a 3-D plate projects its tick labels
inside its own draw, and asking afterwards would re-run its tick update and
throw that projection away.

Only the labels the draw actually reached are measured, which is the whole
filter: a tick outside the view interval, a label switched off with
``tick_params`` and an empty string are never drawn, so they are never in the
capture.

A label turned through an angle has an axis-aligned box much larger than its
letters, and two such boxes on a slanted category axis cross where the words
do not. So the pair is compared in the labels' own frame: each is the
rectangle of its unrotated extent, turned about the centre of its box, and
two labels at the same angle are two axis-aligned rectangles once the page is
turned back by it. Labels at different angles are compared by their boxes,
which can only over-report, and no axis in the corpus mixes angles.

How deep an overlap is
----------------------

The depth of an overlap is the smaller of the two penetrations, along the
reading direction and across it, in points: how far one label would have to
move to clear the other. In points, the unit the fonts are set in, so the
number reads the same on any canvas, and kept to a hundredth of one, so two
boxes that merely abut do not record the last bits of a subtraction as an
overlap. Anything left above zero is recorded; why every
one of them fails is the checker's business
(``scripts/check_figure_ticks.py``).

Recording is off unless :data:`AUDIT_ENV` names a directory, so a plain
``python scripts/generate_graphs.py`` is untouched. When it is set, every
process that draws figures writes its own ``<pid>.json`` fragment there at
exit, and ``scripts/check_figure_ticks.py`` merges them. Fragments
accumulate: whoever sets the variable empties the directory first, which is
what ``make graphs`` does.

The record is keyed by the asset name, language suffix included (``foo`` and
``foo_es``), because the two languages are two drawings: a Spanish tick label
carries a decimal comma and, on a category axis, a longer word. Both light
passes are measured; the dark pass of each is the same geometry in other
colours.
"""

from __future__ import annotations

import atexit
import contextlib
import itertools
import json
import math
import os
import pathlib
from typing import TYPE_CHECKING, Any, NamedTuple

from matplotlib.axes import Axes
from matplotlib.text import Text

if TYPE_CHECKING:
    from matplotlib.axis import Axis, Tick
    from matplotlib.backend_bases import RendererBase
    from matplotlib.figure import Figure

#: Names the directory the fragments are written to. Unset means "do not
#: record", which is the default everywhere except the generation runs the
#: gate is wired into.
AUDIT_ENV = "PHONOMETRY_FIGURE_TICK_AUDIT"

#: Where ``make graphs`` points :data:`AUDIT_ENV`, and where the checker looks
#: when it is not told otherwise. Under ``build/``, which is gitignored.
DEFAULT_DIR = "build/figure-ticks"

#: Minor labels drawn by the scale's own formatter beside major ticks that
#: were set by hand.
STRAY = "stray"

#: Two labels of one axis whose boxes run into each other.
OVERLAP = "overlap"

#: Points per inch, to turn a depth in display units into points.
_PT_PER_INCH = 72.0

#: Decimals a depth is kept to, in points. A hundredth of a point is far below
#: anything a reader sees.
_DEPTH_DIGITS = 2

# key -> what that drawing's axes get wrong. A key with an empty list is a
# figure that was drawn and came out clean, which is what lets the checker
# tell "no longer overlapping" from "not generated in this run".
_FOUND: dict[str, list[dict[str, Any]]] = {}

_REGISTERED = False


class _Label(NamedTuple):
    """One tick label as it was drawn: what it says and where its letters are."""

    text: str
    minor: bool
    #: The centre of its box, in display units.
    centre: tuple[float, float]
    #: Its unrotated width and height, in display units.
    size: tuple[float, float]
    #: The angle it is drawn at, in degrees.
    angle: float


def audit_dir() -> str | None:
    """The directory fragments are written to, or ``None`` when recording is off."""
    return os.environ.get(AUDIT_ENV) or None


def audit(fig: Figure, key: str) -> None:
    """Measure the tick labels of *fig* and record what runs together, under *key*.

    Called once per language as the figure is saved -- on the light pass, since
    the dark one is the same drawing in other colours -- so a figure that
    comes out clean still leaves a record that it was generated at all. *key*
    is the asset name with the language suffix on it.
    """
    if audit_dir() is None:
        return
    _FOUND.setdefault(key, [])
    if not _REGISTERED:
        _register()
    hits = measure(fig)
    if hits:
        _FOUND[key] = hits


def measure(fig: Figure) -> list[dict[str, Any]]:
    """Every stray minor label and every overlap on the axes of *fig*, worst first."""
    drawn = _drawn_labels(fig)
    points_per_unit = _PT_PER_INCH / fig.dpi
    hits: list[dict[str, Any]] = []
    for number, ax in enumerate(_panels(fig), 1):
        for letter, axis in _axes_of(ax):
            name = _axis_name(number, ax, letter)
            labels = _labels_of(axis, drawn)
            stray = [label.text for label in labels if label.minor]
            if stray and _hand_placed(axis):
                hits.append({"kind": STRAY, "axis": name, "labels": stray})
            for one, other in itertools.combinations(labels, 2):
                depth = round(_depth(one, other) * points_per_unit, _DEPTH_DIGITS)
                if depth > 0.0:
                    hits.append(
                        {
                            "kind": OVERLAP,
                            "axis": name,
                            "labels": [one.text, other.text],
                            "depth_pt": depth,
                        }
                    )
    return sorted(hits, key=lambda hit: -float(hit.get("depth_pt", math.inf)))


def _panels(fig: Figure) -> list[Axes]:
    """Every axes of *fig*: its own, a colorbar's, an inset's, a subfigure's.

    ``Axes.inset_axes`` files its result under the host's ``child_axes`` and a
    subfigure keeps its axes to itself, so ``fig.axes`` does not name every
    axis that draws labels; walking the artist tree does. The figure's own
    list comes first, so a panel is numbered where the figure puts it and the
    ones only the walk finds follow.
    """
    found: list[Axes] = list(fig.axes)
    for artist in fig.findobj(Axes):
        if artist not in found:
            found.append(artist)
    return found


def _axes_of(ax: Axes) -> list[tuple[str, Axis]]:
    """The axes of one panel by letter: x and y, and z on a 3-D plate."""
    found: list[tuple[str, Axis]] = [("x", ax.xaxis), ("y", ax.yaxis)]
    zaxis = getattr(ax, "zaxis", None)
    if zaxis is not None:
        found.append(("z", zaxis))
    return found


def _axis_name(number: int, ax: Axes, letter: str) -> str:
    """How the report names an axis: the panel's number, its title, the letter."""
    title = ax.get_title().strip()
    return f"panel {number}" + (f" ({title})" if title else "") + f", {letter} axis"


def _hand_placed(axis: Axis) -> bool:
    """Whether the major ticks were set by hand and the minor labels were not.

    ``Axis.isDefault_majloc`` and ``isDefault_majfmt`` are how matplotlib
    itself remembers that nobody chose where the major ticks go or how they
    read: a ``set_xticks`` clears the first, its labels or a
    ``set_major_formatter`` the second, and a later ``set_xscale`` puts the
    scale's own back and sets both again. Either one cleared means the author
    took the major labels over. Their twin for the minor formatter says the
    minor labels were left to the scale, in the scale's notation.
    """
    by_hand = not (axis.isDefault_majloc and axis.isDefault_majfmt)
    return by_hand and axis.isDefault_minfmt


def _ticks(axis: Axis) -> list[tuple[Tick, bool]]:
    """Every tick object the axis holds, each with whether it is a minor one."""
    majors = [(tick, False) for tick in axis.majorTicks]
    minors = [(tick, True) for tick in axis.minorTicks]
    return majors + minors


def _labels_of(axis: Axis, drawn: dict[int, _Label]) -> list[_Label]:
    """The labels of *axis* the draw reached, with each marked major or minor."""
    found: list[_Label] = []
    for tick, minor in _ticks(axis):
        for text in (tick.label1, tick.label2):
            label = drawn.get(id(text))
            if label is not None:
                found.append(label._replace(minor=minor))
    return found


def _drawn_labels(fig: Figure) -> dict[int, _Label]:
    """Every non-empty text *fig* draws, measured at the moment it is drawn.

    Wrapped around ``Text.draw`` for the reason the module docstring gives,
    and cheap: the figure is laid out and every artist's draw is run with the
    painting switched off, so nothing is painted.
    """
    captured: dict[int, _Label] = {}
    drawn = Text.draw

    def draw(text: Text, renderer: RendererBase) -> None:
        if text.get_visible() and text.get_text().strip():
            with contextlib.suppress(Exception):
                captured[id(text)] = _capture(text, renderer)
        drawn(text, renderer)

    Text.draw = draw  # type: ignore[method-assign,assignment]
    try:
        fig.draw_without_rendering()
    finally:
        Text.draw = drawn  # type: ignore[method-assign]
    return captured


def _capture(text: Text, renderer: RendererBase) -> _Label:
    """What one label says and the rectangle its letters take, as it is drawn."""
    box = Text.get_window_extent(text, renderer)
    angle = text.get_rotation()
    size = (box.width, box.height)
    if angle % 90.0:
        # The box of a slanted label is the box of the turned rectangle, so the
        # rectangle itself is measured with the angle taken off and put back.
        text.set_rotation(0.0)
        try:
            flat = Text.get_window_extent(text, renderer)
        finally:
            text.set_rotation(angle)
        size = (flat.width, flat.height)
    elif angle % 180.0:
        size = (box.height, box.width)
    return _Label(
        text=text.get_text(),
        minor=False,
        centre=((box.x0 + box.x1) / 2.0, (box.y0 + box.y1) / 2.0),
        size=size,
        angle=angle,
    )


def _depth(one: _Label, other: _Label) -> float:
    """How far into each other two labels run, in display units; zero if they do not.

    The smaller penetration of the two directions: how far one would have to
    move to clear the other. Two labels at the same angle are compared in
    their own frame, where both are axis-aligned rectangles; at different
    angles the page frame is used with each label's turned bounding box.
    """
    if one.angle % 360.0 == other.angle % 360.0:
        turn = math.radians(-one.angle)
        cos, sin = math.cos(turn), math.sin(turn)
        dx = other.centre[0] - one.centre[0]
        dy = other.centre[1] - one.centre[1]
        along = abs(dx * cos - dy * sin)
        across = abs(dx * sin + dy * cos)
        sizes = (one.size, other.size)
    else:
        along = abs(other.centre[0] - one.centre[0])
        across = abs(other.centre[1] - one.centre[1])
        sizes = (_page_size(one), _page_size(other))
    width = (sizes[0][0] + sizes[1][0]) / 2.0 - along
    height = (sizes[0][1] + sizes[1][1]) / 2.0 - across
    return max(0.0, min(width, height))


def _page_size(label: _Label) -> tuple[float, float]:
    """The width and height of the page-aligned box around a turned label."""
    turn = math.radians(label.angle)
    cos, sin = abs(math.cos(turn)), abs(math.sin(turn))
    width, height = label.size
    return (width * cos + height * sin, width * sin + height * cos)


# --------------------------------------------------------------------------
# Writing the recording out, and reading it back.


def _register() -> None:
    global _REGISTERED
    atexit.register(_dump)
    _REGISTERED = True


def _forget_after_fork() -> None:
    """Drop the parent's recording so a forked child records only its own.

    ``multiprocessing`` empties the ``atexit`` registry of a forked child, so
    a child that inherited ``_REGISTERED = True`` would never register a
    handler of its own and its measurements would be lost. The annotation
    audit carries the full account of why; the fix is the same.
    """
    global _REGISTERED
    _FOUND.clear()
    _REGISTERED = False


if hasattr(os, "register_at_fork"):  # POSIX only; Windows has no fork
    os.register_at_fork(after_in_child=_forget_after_fork)


def _dump() -> None:
    """Write this process's fragment. Registered on the first :func:`audit`."""
    directory = audit_dir()
    if directory is None or not _FOUND:
        return
    path = pathlib.Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{os.getpid()}.json").write_text(
        json.dumps(_FOUND, ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8",
    )


def load(directory: str) -> dict[str, list[dict[str, Any]]]:
    """Merge every fragment in *directory* into one ``key -> hits``.

    A key drawn by two fragments is the same drawing measured twice (a stale
    directory, or a run restarted): keep each distinct hit once, and the
    deeper of two overlaps between the same labels, so merging can only ever
    under-report a fix, never invent one.
    """
    merged: dict[str, dict[tuple[str, str, str], dict[str, Any]]] = {}
    for fragment in sorted(pathlib.Path(directory).glob("*.json")):
        data = json.loads(fragment.read_text(encoding="utf-8"))
        for key, hits in data.items():
            by_hit = merged.setdefault(key, {})
            for hit in hits:
                found = (hit["kind"], hit["axis"], json.dumps(hit["labels"]))
                seen = by_hit.get(found)
                if seen is None or hit.get("depth_pt", 0.0) > seen.get("depth_pt", 0.0):
                    by_hit[found] = hit
    return {
        key: sorted(by_hit.values(), key=lambda hit: -hit.get("depth_pt", math.inf))
        for key, by_hit in merged.items()
    }
