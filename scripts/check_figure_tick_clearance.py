#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a tick label that something else is drawn over.

A tick label is the number that turns a curve into a reading, and three
things in a drawing can land on one while every gate stays green:

* a **legend**, placed by hand beside the axes and wide enough to reach back
  over them. ``cnossos_rail_directivity`` set its legend over the radial "15"
  and the "−90°" of its half disc;
* a **stroke**. The radial labels of a polar axes sit inside the plot, strung
  along one ray, and a lobe that crosses the ray runs through the numbers on
  it: the dipole beside that half disc ran through "−10.0". An inset draws
  its labels over the data of the panel it sits in, and the unit circle of
  ``pole_migration`` ran through the "1.0000" of its zoom;
* a **marker**, for the same two reasons.

None of the other gates asks. The tick-label audit
(:mod:`figure_tick_audit`) measures the labels of one axis against each
other, the annotation audit measures the labels a generator places and not
the ones an axis draws, and the legend gate (:mod:`check_figure_legends`)
measures plotted points under a legend.

What it reads
-------------
The committed SVG, like the legend gate: it costs seconds, needs no
generation run and answers about the drawing as it ships.
``svg.fonttype = "path"`` writes a label as glyph outlines placed with
``<use>``, so the box of a label here is the union of the outlines it places,
taken through every transform on the way down: the letters, not the line box
matplotlib reserves for them. What the label says comes from the comment
matplotlib writes beside the outlines.

* A **tick label** is a ``text_N`` group inside an ``xtick_N`` or ``ytick_N``
  group. Every axes writes them that way: a colorbar, an inset and a 3-D
  plate as much as an ordinary panel.
* A **legend** is its plate, found the way the legend gate finds it. A legend
  drawn without one stands in with the box its entries fill.
* A **stroke** is any stroked path outside the axis furniture, the legends and
  the text: plotted lines, collections, contours, arrows, the outline of a
  patch and the spines. It is read as its centre line with half its width on
  either side, and only where it is visible: a line clipped to the axes runs on
  in the file past their edge and draws nothing there.
* A **marker** is a ``<use>`` of a glyph small enough to be one, exactly as in
  the legend gate, and it counts where its clip lets it be seen.

Every tick label of the drawing is measured against every one of these,
whichever axes each belongs to: a legend of one panel over the labels of a
twin or of the panel next door hides them just as well. The plates draw their
axes by hand and write no tick group, so a plate has nothing here to read.

What is left out, and why
-------------------------
* The gridlines and the tick marks. They are drawn inside the tick groups, a
  polar radial label sits on its own ring by design, and the annotation audit
  leaves them out for the same reason.
* Filled areas. A fill under a label is a backing, as the chip of an
  annotation is, and counting one as a cover would flag every band a label
  sits on.
* The order things are painted in. A stroke under the letters is as hard to
  read as one over them, which is the annotation audit's "behind" measure,
  and a legend's plate over a label hides it.

A mark counts once it reaches :data:`TOLERANCE_PT` into a label's box, so a
curve that grazes the corner of a glyph's box is not read as running through
it. The light drawings only, in both languages: the dark twin is the same
geometry, and the Spanish labels are wider.

Usage::

    python scripts/check_figure_tick_clearance.py            # gate: exit 1 on any
    python scripts/check_figure_tick_clearance.py --report   # every finding, exit 0
    python scripts/check_figure_tick_clearance.py FILE ...   # restrict to given files

Exit status 0 when nothing is drawn over a tick label, 1 otherwise.
"""

from __future__ import annotations

import argparse
import itertools
import math
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from typing import NamedTuple

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import check_figure_legends as legends

SVG = legends.SVG
XLINK = legends.XLINK

#: How far, in points, a mark has to reach into a label's box to count. A
#: tenth of a millimetre: below anything a reader sees, and above the
#: rounding of the two decimals the committed coordinates are written with.
TOLERANCE_PT = 0.3

#: An (x, y) pair in the drawing's coordinates, y growing downwards.
Point = tuple[float, float]

#: A box as ``(x0, y0, x1, y1)``.
Box = tuple[float, float, float, float]

#: An affine map ``(a, b, c, d, e, f)``, as SVG writes ``matrix()``:
#: ``x' = a x + c y + e`` and ``y' = b x + d y + f``.
Matrix = tuple[float, float, float, float, float, float]

_IDENTITY: Matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)

_NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")

#: The transforms matplotlib writes on a group or a ``<use>``.
_FUNCTION = re.compile(r"(matrix|translate|scale|rotate)\s*\(([^)]*)\)")

#: One command of a path's ``d`` and its arguments. matplotlib writes absolute
#: moves, lines, quadratic and cubic curves, and closes.
_COMMAND = re.compile(r"([MLQCZz])([^MLQCZz]*)")

#: How many numbers each command takes.
_ARITY = {"M": 2, "L": 2, "Q": 4, "C": 6}

#: The number of chords a curve is read as. A curve in a figure is a quarter
#: of a circle at most, so eight chords stay within a hundredth of its radius.
_CURVE_STEPS = 8

#: Points sampled along the stretch of a stroke inside a label's box, to ask
#: whether any of it is visible through the clip.
_CLIP_SAMPLES = 5

_CLIP_REF = re.compile(r"url\(#([^)]+)\)")
_STROKE = re.compile(r"(?:^|;)\s*stroke:\s*([^;]+)")
_STROKE_WIDTH = re.compile(r"stroke-width:\s*([-+\d.eE]+)")

#: The group of one tick: its mark, its gridline and its label.
_TICK = re.compile(r"^[xy]tick_\d+$")

#: What a drawing with any tick in it writes, so one without is not parsed.
_TICK_GROUP = re.compile(r'id="[xy]tick_\d')

#: Groups whose strokes are axis furniture on a 3-D plate: the panes and the
#: grid drawn on them, which play the part of the gridlines.
_FURNITURE = ("grid3d_", "pane3d_")

#: What the report says about each kind of cover, and what to do about it.
ADVICE = {
    "legend": (
        "a legend covers them: move it clear of the axis labels with loc= and "
        "bbox_to_anchor=, or out beside the axes"
    ),
    "stroke": (
        "a stroke runs through them: park the radial labels of a polar axes "
        "where no curve runs with ax.set_rlabel_position(angle), and move an "
        "inset, or its labels, off the curves of the panel it sits in"
    ),
    "marker": "a marker sits on them: move the labels or the panel that draws it",
}


class Cover(NamedTuple):
    """One mark drawn over one tick label."""

    drawing: str
    kind: str
    artist: str
    label: str
    #: For a stroke, how far its centre line runs through the label's box; for
    #: a plate or a marker, how deep it reaches into it. Points either way.
    amount: float

    def describe(self) -> str:
        """One line naming the drawing, what covers the label and by how much."""
        verb = "runs through" if self.kind == "stroke" else "covers"
        return (
            f"{self.drawing}: {self.artist} {verb} the tick label "
            f"{self.label!r} ({self.amount:.1f} pt)"
        )


class _Node(NamedTuple):
    """One drawn element, with everything it inherits on the way down."""

    element: ET.Element
    #: From its own coordinates to the drawing's, its own transform included.
    matrix: Matrix
    #: The ids of the groups it sits in, outermost first.
    groups: tuple[str, ...]
    #: The clip regions in force, each with the map into the drawing that the
    #: element carrying it had.
    clips: tuple[tuple[str, Matrix], ...]


class _Label(NamedTuple):
    """One tick label: what it says and the box of its letters."""

    text: str
    box: Box


# --------------------------------------------------------------------------
# Geometry.


def _compose(outer: Matrix, inner: Matrix) -> Matrix:
    """The map that applies *inner* first and *outer* after it."""
    a, b, c, d, e, f = outer
    p, q, r, s, t, u = inner
    return (
        a * p + c * q,
        b * p + d * q,
        a * r + c * s,
        b * r + d * s,
        a * t + c * u + e,
        b * t + d * u + f,
    )


def _transform(attribute: str | None) -> Matrix:
    """The map a ``transform`` attribute describes, the identity when absent.

    ``rotate`` is read about the origin, which is the only form matplotlib
    writes: a turned label is written ``translate(...) rotate(...)``.
    """
    matrix = _IDENTITY
    for name, arguments in _FUNCTION.findall(attribute or ""):
        values = [float(n) for n in _NUMBER.findall(arguments)]
        if name == "matrix":
            a, b, c, d, e, f = values[:6]
            step: Matrix = (a, b, c, d, e, f)
        elif name == "translate":
            step = (1.0, 0.0, 0.0, 1.0, values[0], values[1] if values[1:] else 0.0)
        elif name == "scale":
            sy = values[1] if values[1:] else values[0]
            step = (values[0], 0.0, 0.0, sy, 0.0, 0.0)
        else:
            turn = math.radians(values[0])
            cos, sin = math.cos(turn), math.sin(turn)
            step = (cos, sin, -sin, cos, 0.0, 0.0)
        matrix = _compose(matrix, step)
    return matrix


def _apply(matrix: Matrix, point: Point) -> Point:
    """*point* carried through *matrix*."""
    a, b, c, d, e, f = matrix
    x, y = point
    return (a * x + c * y + e, b * x + d * y + f)


def _box(points: list[Point]) -> Box:
    """The box around *points*."""
    xs = [x for x, _ in points]
    ys = [y for _, y in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _mapped(matrix: Matrix, box: Box) -> Box:
    """The box around *box* once its corners are carried through *matrix*."""
    x0, y0, x1, y1 = box
    corners = [(x0, y0), (x1, y0), (x0, y1), (x1, y1)]
    return _box([_apply(matrix, corner) for corner in corners])


def _union(boxes: list[Box]) -> Box | None:
    """The box around every one of *boxes*, or ``None`` when there are none."""
    if not boxes:
        return None
    return (
        min(box[0] for box in boxes),
        min(box[1] for box in boxes),
        max(box[2] for box in boxes),
        max(box[3] for box in boxes),
    )


def _grown(box: Box, margin: float) -> Box:
    """*box* with *margin* added on every side (taken off, when negative)."""
    return (box[0] - margin, box[1] - margin, box[2] + margin, box[3] + margin)


def _depth(one: Box, other: Box) -> float:
    """How far two boxes reach into each other: the smaller of the two overlaps."""
    across = min(one[2], other[2]) - max(one[0], other[0])
    down = min(one[3], other[3]) - max(one[1], other[1])
    return min(across, down)


def _bezier(controls: list[Point], t: float) -> Point:
    """The point at *t* of the curve with these control points (de Casteljau)."""
    points = controls
    while len(points) > 1:
        points = [
            ((1.0 - t) * p[0] + t * q[0], (1.0 - t) * p[1] + t * q[1])
            for p, q in itertools.pairwise(points)
        ]
    return points[0]


def _polylines(d: str) -> list[list[Point]]:
    """The subpaths of a path's ``d`` as polylines, its curves read as chords."""
    lines: list[list[Point]] = []
    here: Point = (0.0, 0.0)
    for command, arguments in _COMMAND.findall(d):
        if command in "Zz":
            if lines:
                lines[-1].append(lines[-1][0])
                here = lines[-1][0]
            continue
        values = [float(n) for n in _NUMBER.findall(arguments)]
        arity = _ARITY[command]
        for start in range(0, len(values) - arity + 1, arity):
            chunk = values[start : start + arity]
            end = (chunk[-2], chunk[-1])
            if command == "M" and start == 0:
                lines.append([end])
                here = end
                continue
            if not lines:
                lines.append([here])
            if command in "ML":
                lines[-1].append(end)
            else:
                controls = [here, *zip(chunk[0::2], chunk[1::2], strict=True)]
                steps = range(1, _CURVE_STEPS + 1)
                lines[-1].extend(_bezier(controls, k / _CURVE_STEPS) for k in steps)
            here = end
    return lines


def _points(d: str) -> list[Point]:
    """Every coordinate pair of a path's ``d``, control points included."""
    numbers = [float(n) for n in _NUMBER.findall(d)]
    return list(zip(numbers[0::2], numbers[1::2], strict=False))


def _inside(point: Point, polygon: list[Point]) -> bool:
    """Whether *point* is inside *polygon*, by the even-odd rule."""
    x, y = point
    inside = False
    for (x1, y1), (x2, y2) in itertools.pairwise([*polygon, polygon[0]]):
        if (y1 > y) != (y2 > y) and x < x1 + (x2 - x1) * (y - y1) / (y2 - y1):
            inside = not inside
    return inside


def _through(start: Point, end: Point, box: Box) -> tuple[float, float] | None:
    """The stretch of the segment inside *box*, as fractions of its length.

    Liang and Barsky's clip: each side of the box cuts the parameter range the
    segment keeps, and an empty range is a segment that misses.
    """
    dx, dy = end[0] - start[0], end[1] - start[1]
    low, high = 0.0, 1.0
    for step, room in (
        (-dx, start[0] - box[0]),
        (dx, box[2] - start[0]),
        (-dy, start[1] - box[1]),
        (dy, box[3] - start[1]),
    ):
        if step == 0.0:
            if room < 0.0:
                return None
            continue
        cut = room / step
        if step < 0.0:
            low = max(low, cut)
        else:
            high = min(high, cut)
        if low > high:
            return None
    return low, high


# --------------------------------------------------------------------------
# Reading a drawing.


class Drawing:
    """One committed SVG, read once: its elements, glyphs, clips and labels."""

    def __init__(self, path: pathlib.Path) -> None:
        """Parse *path*, keeping the comments that say what each label reads."""
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        self.path = path
        self.root = ET.parse(path, parser).getroot()
        self._defined = {
            name: element
            for element in self.root.iter(SVG + "path")
            if (name := element.get("id"))
        }
        self._glyphs: dict[str, Box | None] = {}
        self._regions: dict[str, list[list[Point]]] | None = None
        self._polygons: dict[tuple[str, Matrix], list[list[Point]]] = {}
        self.nodes: list[_Node] = []
        self._walk(self.root, _IDENTITY, (), ())

    def glyph(self, name: str) -> Box | None:
        """The box of the defined path *name*, in the coordinates it is placed in.

        Worked out the first time it is asked for: a drawing defines its filled
        bands the same way it defines its letters, and a band thousands of
        points long that nothing here places is not worth reading.
        """
        if name not in self._glyphs:
            path = self._defined.get(name)
            points = _points(path.get("d", "")) if path is not None else []
            self._glyphs[name] = (
                _mapped(_transform(path.get("transform")), _box(points))
                if path is not None and points
                else None
            )
        return self._glyphs[name]

    def is_marker(self, name: str) -> bool:
        """Whether *name* is a marker glyph, by the legend gate's two tests."""
        box = self.glyph(name) if legends._GLYPH_ID.match(name) else None
        return box is not None and max(box[2] - box[0], box[3] - box[1]) <= (
            legends.MARKER_MAX_PT
        )

    def _clip_regions(self) -> dict[str, list[list[Point]]]:
        """Every clip region, as the polygons it is made of."""
        found: dict[str, list[list[Point]]] = {}
        for clip in self.root.iter(SVG + "clipPath"):
            shapes: list[list[Point]] = []
            for shape in clip:
                if shape.tag == SVG + "rect":
                    x, y = float(shape.get("x", "0")), float(shape.get("y", "0"))
                    w, h = (
                        float(shape.get("width", "0")),
                        float(shape.get("height", "0")),
                    )
                    shapes.append([(x, y), (x + w, y), (x + w, y + h), (x, y + h)])
                elif shape.tag == SVG + "path":
                    lines = _polylines(shape.get("d", ""))
                    shapes.append([point for line in lines for point in line])
            found[clip.get("id", "")] = shapes
        return found

    def _walk(
        self,
        element: ET.Element,
        matrix: Matrix,
        groups: tuple[str, ...],
        clips: tuple[tuple[str, Matrix], ...],
    ) -> None:
        """Record *element* and everything under it, skipping what is not drawn."""
        if element.tag in (SVG + "defs", SVG + "clipPath"):
            return
        matrix = _compose(matrix, _transform(element.get("transform")))
        clip = _CLIP_REF.search(element.get("clip-path") or "")
        if clip:
            clips = (*clips, (clip.group(1), matrix))
        self.nodes.append(_Node(element, matrix, groups, clips))
        name = element.get("id")
        if element.tag == SVG + "g" and name:
            groups = (*groups, name)
        for child in element:
            self._walk(child, matrix, groups, clips)

    def visible(self, point: Point, clips: tuple[tuple[str, Matrix], ...]) -> bool:
        """Whether every clip region in force lets *point* be drawn."""
        if self._regions is None:
            self._regions = self._clip_regions()
        for name, matrix in clips:
            key = (name, matrix)
            if key not in self._polygons:
                self._polygons[key] = [
                    [_apply(matrix, corner) for corner in shape]
                    for shape in self._regions.get(name, [])
                ]
            shapes = self._polygons[key]
            if shapes and not any(_inside(point, shape) for shape in shapes):
                return False
        return True

    def _placed(self, node: _Node) -> Box | None:
        """Where a ``<use>`` puts the glyph it names, or ``None`` for another element."""
        element = node.element
        if element.tag != SVG + "use":
            return None
        ref = (element.get(XLINK + "href") or element.get("href") or "").lstrip("#")
        glyph = self.glyph(ref)
        if glyph is None:
            return None
        shift = (
            1.0,
            0.0,
            0.0,
            1.0,
            float(element.get("x", "0")),
            float(element.get("y", "0")),
        )
        return _mapped(_compose(node.matrix, shift), glyph)

    def _ink(self, node: _Node) -> Box | None:
        """The box of what one element of a label or a legend lays down."""
        placed = self._placed(node)
        if placed is not None:
            return placed
        element = node.element
        if element.tag == SVG + "path" and not element.get("id"):
            points = _points(element.get("d", ""))
            return _mapped(node.matrix, _box(points)) if points else None
        return None

    def tick_labels(self) -> list[_Label]:
        """Every tick label the drawing writes, with the box of its letters."""
        texts: dict[str, str] = {}
        boxes: dict[str, list[Box]] = {}
        for node in self.nodes:
            if not any(_TICK.match(group) for group in node.groups):
                continue
            element = node.element
            name = element.get("id") or ""
            if element.tag == SVG + "g" and name.startswith("text_"):
                texts[name] = _comment(element)
                continue
            label = next((g for g in node.groups if g.startswith("text_")), None)
            ink = self._ink(node) if label else None
            if label and ink:
                boxes.setdefault(label, []).append(ink)
        found: list[_Label] = []
        for name, text in texts.items():
            box = _union(boxes.get(name, []))
            if box is not None:
                found.append(_Label(text, box))
        return found

    def legend_boxes(self) -> dict[str, Box]:
        """The plate of every legend, or the box its entries fill when it has none."""
        plates = legends._frames(legends._walk(self.root))
        entries: dict[str, list[Box]] = {}
        for node in self.nodes:
            legend = next((g for g in node.groups if g.startswith("legend_")), None)
            ink = self._ink(node) if legend and legend not in plates else None
            if legend and ink:
                entries.setdefault(legend, []).append(ink)
        boxes = dict(plates)
        for legend, inks in entries.items():
            box = _union(inks)
            if box is not None:
                boxes[legend] = box
        return boxes

    def strokes(self) -> list[tuple[_Node, float]]:
        """Every stroked path outside the furniture, with half its width in points."""
        found: list[tuple[_Node, float]] = []
        for node in self.nodes:
            element = node.element
            if element.tag != SVG + "path" or element.get("id") or _furniture(node):
                continue
            style = element.get("style") or ""
            stroke = _STROKE.search(style)
            if stroke is None or stroke.group(1).strip() == "none":
                continue
            width = _STROKE_WIDTH.search(style)
            a, b, c, d, _e, _f = node.matrix
            scale = math.sqrt(abs(a * d - b * c))
            found.append((node, (float(width.group(1)) if width else 1.0) * scale / 2))
        return found

    def placed_markers(self) -> list[tuple[_Node, Box]]:
        """Every marker drawn outside the furniture, where its clip shows it."""
        found: list[tuple[_Node, Box]] = []
        for node in self.nodes:
            element = node.element
            if element.tag != SVG + "use" or _furniture(node):
                continue
            ref = (element.get(XLINK + "href") or element.get("href") or "").lstrip("#")
            box = self._placed(node) if self.is_marker(ref) else None
            if box is None:
                continue
            centre = ((box[0] + box[2]) / 2.0, (box[1] + box[3]) / 2.0)
            if self.visible(centre, node.clips):
                found.append((node, box))
        return found


def _comment(group: ET.Element) -> str:
    """The string matplotlib wrote beside the outlines of a text group."""
    for child in group:
        # ElementTree marks a comment by putting its factory where the tag of
        # an element goes, which the type stubs do not describe.
        tag: object = child.tag
        if tag is ET.Comment:
            return (child.text or "").strip()
    return ""


def _furniture(node: _Node) -> bool:
    """Whether *node* is a tick, a legend, a text or the grid of a 3-D plate."""
    return any(
        _TICK.match(group) or group.startswith(("legend_", "text_", *_FURNITURE))
        for group in node.groups
    )


def _artist(node: _Node) -> str:
    """The artist that drew *node*: its nearest group named for a kind of artist."""
    return next((g for g in reversed(node.groups) if "_" in g), "an unnamed artist")


# --------------------------------------------------------------------------
# Measuring.


def _run_through(
    drawing: Drawing, node: _Node, half_width: float, labels: list[_Label]
) -> list[tuple[_Label, float]]:
    """The labels a stroke runs through, each with how far, in points."""
    lines = [
        [_apply(node.matrix, point) for point in line]
        for line in _polylines(node.element.get("d", ""))
    ]
    points = [point for line in lines for point in line]
    if not points:
        return []
    reach = _grown(_box(points), half_width)
    found: list[tuple[_Label, float]] = []
    for label in labels:
        box = _grown(label.box, half_width - TOLERANCE_PT)
        if box[0] >= box[2] or box[1] >= box[3] or _depth(reach, box) <= 0.0:
            continue
        length = 0.0
        for line in lines:
            for start, end in itertools.pairwise(line):
                stretch = _through(start, end, box)
                if stretch is None or not _seen(drawing, node, start, end, stretch):
                    continue
                low, high = stretch
                length += (high - low) * math.dist(start, end)
        if length > 0.0:
            found.append((label, length))
    return found


def _seen(
    drawing: Drawing,
    node: _Node,
    start: Point,
    end: Point,
    stretch: tuple[float, float],
) -> bool:
    """Whether any of a segment's stretch inside a box survives its clip."""
    low, high = stretch
    for k in range(_CLIP_SAMPLES):
        t = low + (high - low) * (k + 0.5) / _CLIP_SAMPLES
        point = (start[0] + (end[0] - start[0]) * t, start[1] + (end[1] - start[1]) * t)
        if drawing.visible(point, node.clips):
            return True
    return False


def measure(path: pathlib.Path) -> list[Cover]:
    """Every legend, stroke and marker of *path* drawn over one of its tick labels."""
    if not _TICK_GROUP.search(path.read_text(encoding="utf-8", errors="replace")):
        return []
    drawing = Drawing(path)
    labels = drawing.tick_labels()
    if not labels:
        return []
    found: list[Cover] = []
    for legend, plate in drawing.legend_boxes().items():
        for label in labels:
            depth = _depth(plate, label.box)
            if depth > TOLERANCE_PT:
                found.append(Cover(path.stem, "legend", legend, label.text, depth))
    for node, half_width in drawing.strokes():
        for label, length in _run_through(drawing, node, half_width, labels):
            found.append(Cover(path.stem, "stroke", _artist(node), label.text, length))
    for node, box in drawing.placed_markers():
        for label in labels:
            depth = _depth(box, label.box)
            if depth > TOLERANCE_PT:
                found.append(
                    Cover(path.stem, "marker", _artist(node), label.text, depth)
                )
    return found


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; see the module docstring."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "files",
        nargs="*",
        type=pathlib.Path,
        help="SVG figures (default: every committed light drawing)",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="print every finding and always exit 0",
    )
    args = parser.parse_args(argv)

    files = args.files or legends.light_figures()
    covers = [cover for path in files for cover in measure(path)]
    if args.report:
        for cover in covers:
            print(cover.describe())
        print(f"\n{len(covers)} finding(s) in {len(files)} drawings.")
        return 0
    if not covers:
        print(f"Nothing is drawn over a tick label: {len(files)} drawings.")
        return 0
    drawings = len({cover.drawing for cover in covers})
    print(
        f"::error::{len(covers)} tick label(s) across {drawings} drawing(s) have "
        "something drawn over them:"
    )
    for kind, advice in ADVICE.items():
        of_kind = [cover for cover in covers if cover.kind == kind]
        for cover in of_kind:
            print(f"  {cover.describe()}")
        if of_kind:
            print(f"  -> {advice}.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
