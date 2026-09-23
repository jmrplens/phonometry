#!/usr/bin/env python3
#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Fail on a text that another text or a stroke is drawn over.

A label placed by hand has three ways to land on something while every other
gate stays green:

* on a **tick label**. ``sound_power_grades_declaration`` set its
  "$U$ = 1.0 dB" over the "90" of the axis beside it, and the "Reflecting
  plane" of ``microphone_positions_hemisphere`` reached the "1" of its y axis;
* on **another text**: two notes placed apart in one language and run
  together in the other;
* under a **stroke**, a curve, a guide line, an arrow or a spine run across
  it. The heading of the last lane of ``diagram_sweep_budget`` was crossed by
  the impulse it names and by the dashed zero line under it, and a note that
  runs out of its axes is struck through by the spine it crosses, as
  "$2 f_2$ = 12 kHz" was in ``swept_sine_methods``.

The tick clearance gate (:mod:`check_figure_tick_clearance`) measures the
marks drawn over a tick label, but not a text; the legend gate measures a
legend; the annotation audit (:mod:`figure_annotation_audit`) measures the
labels a generator places, during the generation run, and the plates drawn
under ``scripts/diagrams`` are outside it altogether.

What it reads
-------------
The committed SVG, like its two siblings, and every drawing: the plates as
much as the figures. A string is the glyph outlines placed after the comment
that names it, in a matplotlib ``text_N`` group or in a run of ``<use>`` on a
plate, each glyph taken through every transform on the way down as the
parallelogram its outline fills. A label turned on a 3-D plate is read along
its own baseline, not as the upright box round it, which would reach over
everything near it.

* Two **texts** count when the letters of one come within :data:`GAP_PT` of
  the letters of the other, glyph against glyph. The lines of one matplotlib
  artist are not measured against each other, and tick labels against each
  other are left to the tick audit.
* A **stroke** is any stroked shape outside the furniture: plotted lines,
  contours, arrows, the outline of a patch, the spines, and every line of a
  plate. It is read as its centre line with half its width either side, with
  its caps and its dashes, and only where it puts ink down: a line clipped to
  its axes draws nothing past their edge, and a line painted before an opaque
  fill, the chip of a note or the plate of a legend, is hidden where the fill
  is. It fails a text in two ways. It **runs across** the text when a stretch
  of it spans the whole height of the line, between its first letter and its
  last, which strikes the line through whether or not it meets a letter on
  the way. It **runs into** the letters when the ink it lays inside their
  outlines, sampled every :data:`_STEP` points, comes to more than
  :data:`INK_PT2` square points.

What is left out, and why
-------------------------
* The gridlines, the tick marks and the grid and panes of a 3-D plate. A
  label sits on the grid by design, and the sibling gates leave them out for
  the same reason.
* The frame and handles of a legend and the chip of a text, which are drawn
  to sit round words.
* The leader of an annotation, against its own text: matplotlib writes it as
  the patch just before the text, and it starts at the words by design. The
  end of any open line is read as pointing for the last :data:`POINTER_PT`
  past its cap, so a curve labelled at its end, or a dimension line that
  stops at its value, passes.
* Fills. A band under a label is a backing, as a chip is, and the contrast
  gates judge whether the words read on it.
* A string clipped away with its axes (``clip_on=True``), glyph by glyph: it
  is not on the page.

A text that is meant to sit where it does is named in :data:`EXEMPTIONS` with
the reason, and an entry that no longer fires fails the gate until it is
deleted. The light drawings only, in both languages: the dark twin is the
same geometry, and the Spanish labels are wider.

Usage::

    python scripts/check_figure_text_clearance.py            # gate: exit 1 on any
    python scripts/check_figure_text_clearance.py --report   # every finding, exit 0
    python scripts/check_figure_text_clearance.py FILE ...   # restrict to given files

Exit status 0 when every text is clear, 1 otherwise.
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
import check_figure_tick_clearance as ticks

SVG = legends.SVG
XLINK = legends.XLINK

#: How far, in points, one mark has to reach into another to count: the tick
#: clearance gate's tolerance, for the same reason.
TOLERANCE_PT = ticks.TOLERANCE_PT

#: How close, in points, the letters of a text may come to the letters of a
#: tick label or of another text.
GAP_PT = 1.0

#: How much of a text's letters, in square points, a stroke may cover.
INK_PT2 = 0.25

#: How far, in points, the end of a stroke may reach into the line of a text
#: and still be read as pointing at it rather than running into it.
POINTER_PT = 1.5

#: How far, in points, the arrow of an annotation may start from the letters
#: of its text: matplotlib starts it at the box round the text, padded when
#: the text has a chip, and draws it back from there by two points.
LEADER_PT = 12.0

#: The step, in points, of the grid the ink of a stroke is sampled on.
_STEP = 0.2

Point = ticks.Point
Box = ticks.Box
Matrix = ticks.Matrix

#: The box of one glyph carried into the drawing: its corners, in order round.
Quad = tuple[Point, Point, Point, Point]

#: A band between two parallel lines: its unit normal and the two offsets.
Slab = tuple[Point, float, float]

#: The rings of a glyph's outline, filled by the even-odd rule.
Outline = tuple[tuple[Point, ...], ...]

_FILL = re.compile(r"(?:^|;)\s*fill:\s*([^;]+)")
_OPACITY = re.compile(r"(?:^|;)\s*opacity:\s*([-+\d.eE]+)")
_FILL_OPACITY = re.compile(r"(?:^|;)\s*fill-opacity:\s*([-+\d.eE]+)")
_STROKE_OPACITY = re.compile(r"(?:^|;)\s*stroke-opacity:\s*([-+\d.eE]+)")
_DASHARRAY = re.compile(r"(?:^|;)\s*stroke-dasharray:\s*([^;]+)")
_DASHOFFSET = re.compile(r"(?:^|;)\s*stroke-dashoffset:\s*([^;]+)")
_LINECAP = re.compile(r"(?:^|;)\s*stroke-linecap:\s*([^;]+)")

#: Groups whose strokes are furniture rather than marks: the grid and panes of
#: a 3-D plate, a legend's handles and frame, and the chip of a text.
_FURNITURE = ("grid3d_", "pane3d_", "legend_", "text_")

#: The shapes a drawing strokes or fills.
_SHAPES = ("line", "path", "rect", "circle", "ellipse", "polyline")

#: Chords a full turn of a circle, an ellipse or an arc is read as.
_ARC_STEPS = 48

#: A fill at least this opaque hides what is painted under it.
_OPAQUE = 0.5

#: One command letter or one number of a path's ``d``.
_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")

#: How many numbers each path command takes.
_ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7}

#: Drawings, or ``drawing: text`` pairs, that are allowed to fire, with the
#: reason each is a decision and not a defect. Keyed by the light drawing's
#: name with its language suffix.
EXEMPTIONS: dict[str, str] = {}


class Finding(NamedTuple):
    """One mark drawn over one text."""

    drawing: str
    #: ``"tick"`` (a text over a tick label), ``"text"`` (over another text),
    #: ``"cut"`` (a stroke across a text's line) or ``"ink"`` (a stroke on its
    #: letters).
    kind: str
    #: What is drawn over the text: another text, quoted, or an artist.
    over: str
    text: str
    #: Points for a text (how far the two reach into each other, negative
    #: for a gap), how far inside the line for a cut, square points for ink.
    amount: float
    where: Point

    @property
    def key(self) -> str:
        """The ``drawing: text`` key an exemption names."""
        return f"{self.drawing}: {self.text}"

    def describe(self) -> str:
        """One line naming the drawing, what is drawn over the text and by how much."""
        what = {
            "tick": f"the text {self.over} is drawn over the tick label",
            "text": f"the text {self.over} is drawn over",
            "cut": f"{self.over} runs across",
            "ink": f"{self.over} runs into the letters of",
        }[self.kind]
        unit = "pt²" if self.kind == "ink" else "pt"
        return (
            f"{self.drawing}: {what} {self.text!r} "
            f"({self.amount:.2f} {unit} at {self.where[0]:.0f}, {self.where[1]:.0f})"
        )


class _Letter(NamedTuple):
    """One glyph of a text: its outline, the map that places it and its box."""

    outline: Outline
    #: The box of the outline in the glyph's own coordinates.
    local: Box
    #: From the drawing back into the glyph's own coordinates.
    inverse: Matrix
    quad: Quad
    box: Box


class _Text(NamedTuple):
    """One string a drawing writes, with its letters."""

    text: str
    #: The artist that drew it (``text_N``), or ``label_N`` on a plate.
    owner: str
    #: ``"tick"``, ``"legend"`` or ``"text"``.
    role: str
    letters: tuple[_Letter, ...]
    box: Box


class _Stroke(NamedTuple):
    """One stroked shape: its centre lines, half its width and its dashes."""

    artist: str
    lines: list[list[Point]]
    half_width: float
    #: The dash pattern as on-off lengths, empty for a solid line.
    dashes: tuple[float, ...]
    offset: float
    #: Where it is painted, in document order.
    order: int
    clips: tuple[tuple[str, Matrix], ...]
    box: Box


class _Fill(NamedTuple):
    """One opaque filled shape, which hides whatever was painted before it."""

    polygon: list[Point]
    box: Box
    order: int
    clips: tuple[tuple[str, Matrix], ...]


class _Frame(NamedTuple):
    """A text's own axes and how far its letters reach along and across them."""

    along: Point
    across: Point
    start: float
    end: float
    top: float
    bottom: float

    def inset(self, point: Point) -> float:
        """How far inside the letters' extent *point* lies (negative outside)."""
        a = point[0] * self.along[0] + point[1] * self.along[1]
        c = point[0] * self.across[0] + point[1] * self.across[1]
        return min(a - self.start, self.end - a, c - self.top, self.bottom - c)


# --------------------------------------------------------------------------
# Geometry.


def _quad(matrix: Matrix, box: Box) -> Quad:
    """The corners of *box* carried through *matrix*, in order round it."""
    x0, y0, x1, y1 = box
    return (
        ticks._apply(matrix, (x0, y0)),
        ticks._apply(matrix, (x1, y0)),
        ticks._apply(matrix, (x1, y1)),
        ticks._apply(matrix, (x0, y1)),
    )


def _inverse(matrix: Matrix) -> Matrix | None:
    """The map that undoes *matrix*, or ``None`` when it flattens the plane."""
    a, b, c, d, e, f = matrix
    det = a * d - b * c
    if abs(det) < 1e-12:
        return None
    return (
        d / det,
        -b / det,
        -c / det,
        a / det,
        (c * f - d * e) / det,
        (b * e - a * f) / det,
    )


def _normals(quad: Quad) -> list[Point]:
    """The unit normals of two adjacent sides of *quad*, its separating axes."""
    found: list[Point] = []
    for (ax, ay), (bx, by) in ((quad[0], quad[1]), (quad[1], quad[2])):
        length = math.hypot(bx - ax, by - ay)
        if length > 1e-9:
            found.append((-(by - ay) / length, (bx - ax) / length))
    return found


def _project(
    points: tuple[Point, ...] | list[Point], axis: Point
) -> tuple[float, float]:
    """The span of *points* along *axis*."""
    values = [x * axis[0] + y * axis[1] for x, y in points]
    return min(values), max(values)


def _depth(one: Quad, other: Quad) -> float:
    """How far two glyph boxes reach into each other; negative is the gap.

    The separating-axis test on the two parallelograms: along each side's
    normal the overlap of the two spans, and the smallest of them. A label
    turned through an angle is compared as the letters it draws, not as the
    upright box around them.
    """
    depth = math.inf
    for axis in _normals(one) + _normals(other):
        a0, a1 = _project(one, axis)
        b0, b1 = _project(other, axis)
        depth = min(depth, min(a1, b1) - max(a0, b0))
    return depth


def _slabs(quad: Quad, margin: float) -> list[Slab]:
    """The two bands whose overlap is *quad*, each widened by *margin*."""
    slabs: list[Slab] = []
    for axis in _normals(quad):
        low, high = _project(quad, axis)
        slabs.append((axis, low - margin, high + margin))
    return slabs


def _clip(start: Point, end: Point, slabs: list[Slab]) -> tuple[float, float] | None:
    """The stretch of a segment inside every one of *slabs*, as fractions of it.

    Liang and Barsky's clip, with the bands of any convex quadrilateral in
    place of the sides of an upright box.
    """
    dx, dy = end[0] - start[0], end[1] - start[1]
    low, high = 0.0, 1.0
    for (nx, ny), lo, hi in slabs:
        p0 = nx * start[0] + ny * start[1]
        dp = nx * dx + ny * dy
        if abs(dp) < 1e-12:
            if p0 < lo or p0 > hi:
                return None
            continue
        t0, t1 = sorted(((lo - p0) / dp, (hi - p0) / dp))
        low, high = max(low, t0), min(high, t1)
        if low > high:
            return None
    return low, high


def _overlaps(one: Box, other: Box) -> bool:
    """Whether two boxes share any area."""
    return (
        one[0] < other[2]
        and other[0] < one[2]
        and one[1] < other[3]
        and other[1] < one[3]
    )


def _filled(point: Point, outline: Outline) -> bool:
    """Whether *point* is inside *outline*, by the even-odd rule."""
    x, y = point
    inside = False
    for ring in outline:
        for (x1, y1), (x2, y2) in itertools.pairwise(ring):
            if (y1 > y) != (y2 > y) and x < x1 + (x2 - x1) * (y - y1) / (y2 - y1):
                inside = not inside
    return inside


def _arc(here: Point, values: list[float]) -> list[Point]:
    """The points of an elliptical arc, from SVG's endpoint form of it.

    The conversion to a centre and two angles is the one the SVG
    specification gives (its appendix on arc implementation notes), radii
    too small to reach included.
    """
    rx, ry, rotation, large, sweep, x, y = values
    end = (x, y)
    rx, ry = abs(rx), abs(ry)
    if rx < 1e-9 or ry < 1e-9 or here == end:
        return [end]
    phi = math.radians(rotation)
    cos, sin = math.cos(phi), math.sin(phi)
    dx, dy = (here[0] - x) / 2.0, (here[1] - y) / 2.0
    x1, y1 = cos * dx + sin * dy, -sin * dx + cos * dy
    scale = (x1 * x1) / (rx * rx) + (y1 * y1) / (ry * ry)
    if scale > 1.0:
        rx, ry = rx * math.sqrt(scale), ry * math.sqrt(scale)
    numerator = rx * rx * ry * ry - rx * rx * y1 * y1 - ry * ry * x1 * x1
    denominator = rx * rx * y1 * y1 + ry * ry * x1 * x1
    factor = math.sqrt(max(0.0, numerator / denominator)) if denominator else 0.0
    if bool(large) == bool(sweep):
        factor = -factor
    cx1, cy1 = factor * rx * y1 / ry, -factor * ry * x1 / rx
    cx = cos * cx1 - sin * cy1 + (here[0] + x) / 2.0
    cy = sin * cx1 + cos * cy1 + (here[1] + y) / 2.0
    first = math.atan2((y1 - cy1) / ry, (x1 - cx1) / rx)
    turn = math.atan2((-y1 - cy1) / ry, (-x1 - cx1) / rx) - first
    if sweep and turn < 0.0:
        turn += 2.0 * math.pi
    elif not sweep and turn > 0.0:
        turn -= 2.0 * math.pi
    steps = max(2, math.ceil(abs(turn) / (2.0 * math.pi) * _ARC_STEPS))
    points = []
    for k in range(1, steps + 1):
        angle = first + turn * k / steps
        px, py = rx * math.cos(angle), ry * math.sin(angle)
        points.append((cos * px - sin * py + cx, sin * px + cos * py + cy))
    points[-1] = end
    return points


def _outline(d: str) -> list[list[Point]]:
    """The subpaths of a path's ``d`` as polylines.

    Every command SVG has, absolute and relative: the tick gate's reader
    takes the four matplotlib writes, and the plates write arcs, smooth
    curves and relative moves as well. Curves are read as chords.
    """
    tokens = _TOKEN.findall(d)
    lines: list[list[Point]] = []
    here: Point = (0.0, 0.0)
    control: Point | None = None
    command = ""
    k = 0
    while k < len(tokens):
        if tokens[k].isalpha():
            command = tokens[k]
            k += 1
            if command in "Zz":
                if lines:
                    lines[-1].append(lines[-1][0])
                    here = lines[-1][0]
                control = None
                continue
        upper = command.upper()
        count = _ARGS.get(upper, 0)
        values = [float(t) for t in tokens[k : k + count]]
        k += max(count, 1)
        if not count or len(values) < count:
            continue
        ox, oy = here if command.islower() else (0.0, 0.0)
        if upper == "A":
            values[5] += ox
            values[6] += oy
        elif upper == "H":
            values = [values[0] + ox, here[1]]
        elif upper == "V":
            values = [here[0], values[0] + oy]
        else:
            values = [v + (ox if i % 2 == 0 else oy) for i, v in enumerate(values)]
        if upper == "M":
            here = (values[0], values[1])
            lines.append([here])
            command = "l" if command == "m" else "L"
            control = None
            continue
        if not lines:
            lines.append([here])
        if upper in "LHV":
            here = (values[0], values[1])
            lines[-1].append(here)
            control = None
            continue
        if upper == "A":
            lines[-1].extend(_arc(here, values))
            here = (values[5], values[6])
            control = None
            continue
        mirror = (
            (2 * here[0] - control[0], 2 * here[1] - control[1]) if control else here
        )
        pairs = list(zip(values[0::2], values[1::2], strict=True))
        controls = [here, mirror, *pairs] if upper in "ST" else [here, *pairs]
        lines[-1].extend(
            ticks._bezier(controls, j / ticks._CURVE_STEPS)
            for j in range(1, ticks._CURVE_STEPS + 1)
        )
        here, control = controls[-1], controls[-2]
    return lines


def _number(value: str | None, default: float) -> float:
    """*value* as a number, or *default* when it is absent or not one."""
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


def _style(element: ET.Element, name: str, pattern: re.Pattern[str]) -> str | None:
    """A presentation property, as an attribute (plates) or in ``style`` (matplotlib)."""
    value = element.get(name)
    if value is not None:
        return value.strip()
    found = pattern.search(element.get("style") or "")
    return found.group(1).strip() if found else None


def _shape(element: ET.Element, name: str) -> list[list[Point]]:
    """The outline of one shape as polylines, in its own coordinates."""
    get = element.get
    if name == "path":
        return _outline(get("d", ""))
    if name == "line":
        start = (_number(get("x1"), 0.0), _number(get("y1"), 0.0))
        return [[start, (_number(get("x2"), 0.0), _number(get("y2"), 0.0))]]
    if name == "polyline":
        numbers = [float(n) for n in ticks._NUMBER.findall(get("points", ""))]
        return [list(zip(numbers[0::2], numbers[1::2], strict=False))]
    if name == "rect":
        x, y = _number(get("x"), 0.0), _number(get("y"), 0.0)
        w, h = _number(get("width"), 0.0), _number(get("height"), 0.0)
        return [[(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]]
    cx, cy = _number(get("cx"), 0.0), _number(get("cy"), 0.0)
    if name == "circle":
        rx = ry = _number(get("r"), 0.0)
    else:
        rx, ry = _number(get("rx"), 0.0), _number(get("ry"), 0.0)
    turn = 2.0 * math.pi / _ARC_STEPS
    return [
        [
            (cx + rx * math.cos(turn * k), cy + ry * math.sin(turn * k))
            for k in range(_ARC_STEPS + 1)
        ]
    ]


def _capped(line: list[Point], half: float) -> list[Point]:
    """*line* run on by *half* at each open end, as far as a round or square cap."""
    if len(line) < 2 or line[0] == line[-1]:
        return line

    def run_on(tip: Point, before: Point) -> Point:
        length = math.dist(tip, before)
        if length < 1e-9:
            return tip
        return (
            tip[0] + (tip[0] - before[0]) / length * half,
            tip[1] + (tip[1] - before[1]) / length * half,
        )

    return [run_on(line[0], line[1]), *line[1:-1], run_on(line[-1], line[-2])]


# --------------------------------------------------------------------------
# Reading a drawing.


class Sheet(ticks.Drawing):
    """One committed drawing, read for its texts, its strokes and its fills."""

    def __init__(self, path: pathlib.Path) -> None:
        """Parse *path* and tie every glyph to the string it belongs to."""
        super().__init__(path)
        self._strings: list[str] = []
        #: ``id()`` of every element that draws a string -> that string's index.
        self._owned: dict[int, int] = {}
        #: The arrow of an annotation -> the text it belongs to.
        self.leaders: dict[str, str] = {}
        self._outlines: dict[str, Outline] = {}
        self._tie(self.root)

    def _tie(self, element: ET.Element) -> None:
        """Tie the glyph groups under *element* to the comment that names them.

        matplotlib and the plate canvas both write a string as a comment
        followed by the groups that place its glyphs, so every group of
        ``<use>`` after a comment is that string's, until something else is
        drawn. An annotation draws its arrow as the patch just before its
        text group, which is how its own leader is told from any other mark.
        """
        current: int | None = None
        previous = ""
        for child in element:
            tag: object = child.tag
            if tag is ET.Comment:
                self._strings.append((child.text or "").strip())
                current = len(self._strings) - 1
                continue
            name = child.get("id") or ""
            if (
                current is not None
                and child.tag == SVG + "g"
                and not name
                and any(grand.tag == SVG + "use" for grand in child)
            ):
                for inner in child.iter():
                    self._owned[id(inner)] = current
            else:
                current = None
                if child.tag == SVG + "g":
                    self._tie(child)
            if name.startswith("text_") and previous.startswith("patch_"):
                self.leaders[previous] = name
            previous = name

    def outline(self, name: str) -> Outline:
        """The rings of the defined path *name*, in the coordinates it is placed in."""
        if name not in self._outlines:
            path = self._defined.get(name)
            rings: Outline = ()
            if path is not None:
                matrix = ticks._transform(path.get("transform"))
                rings = tuple(
                    tuple(ticks._apply(matrix, p) for p in line)
                    for line in _outline(path.get("d", ""))
                    if len(line) > 2
                )
            self._outlines[name] = rings
        return self._outlines[name]

    def _letter(self, node: ticks._Node) -> _Letter | None:
        """The glyph one element of a string places: a ``<use>``, or a rule of mathtext."""
        element = node.element
        if element.tag == SVG + "use":
            ref = (element.get(XLINK + "href") or element.get("href") or "").lstrip("#")
            local = self.glyph(ref)
            if local is None:
                return None
            x, y = _number(element.get("x"), 0.0), _number(element.get("y"), 0.0)
            matrix = ticks._compose(node.matrix, (1.0, 0.0, 0.0, 1.0, x, y))
            outline = self.outline(ref)
        elif element.tag == SVG + "path" and not element.get("id"):
            lines = _outline(element.get("d", ""))
            points = [p for line in lines for p in line]
            if not points:
                return None
            local = ticks._box(points)
            matrix = node.matrix
            outline = tuple(tuple(line) for line in lines if len(line) > 2)
        else:
            return None
        inverse = _inverse(matrix)
        if inverse is None or local[0] >= local[2] or local[1] >= local[3]:
            return None
        quad = _quad(matrix, local)
        return _Letter(outline, local, inverse, quad, ticks._box(list(quad)))

    def texts(self) -> list[_Text]:
        """Every string the drawing writes, with the glyphs it places."""
        letters: dict[int, list[_Letter]] = {}
        roles: dict[int, tuple[str, str]] = {}
        for node in self.nodes:
            index = self._owned.get(id(node.element))
            letter = self._letter(node) if index is not None else None
            if index is None or letter is None:
                continue
            # A string clipped with its axes (``clip_on=True``) is only where
            # its clip shows it: a glyph cut away is not on the page.
            centre = (
                sum(p[0] for p in letter.quad) / 4.0,
                sum(p[1] for p in letter.quad) / 4.0,
            )
            if not self.visible(centre, node.clips):
                continue
            letters.setdefault(index, []).append(letter)
            if index not in roles:
                groups = node.groups
                role = (
                    "tick"
                    if any(ticks._TICK.match(g) for g in groups)
                    else "legend"
                    if any(g.startswith("legend_") for g in groups)
                    else "text"
                )
                owner = next(
                    (g for g in reversed(groups) if g.startswith("text_")),
                    f"label_{index}",
                )
                roles[index] = (role, owner)
        found = []
        for index, glyphs in letters.items():
            box = ticks._union([letter.box for letter in glyphs])
            if box is not None:
                role, owner = roles[index]
                found.append(
                    _Text(self._strings[index], owner, role, tuple(glyphs), box)
                )
        return found

    def _shapes(self) -> list[tuple[int, ticks._Node, str]]:
        """Every shape drawn outside a string, with where it is painted."""
        found = []
        for k, node in enumerate(self.nodes):
            tag = node.element.tag
            if not isinstance(tag, str) or not tag.startswith(SVG):
                continue
            name = tag[len(SVG) :]
            if (
                name in _SHAPES
                and not node.element.get("id")
                and id(node.element) not in self._owned
            ):
                found.append((k, node, name))
        return found

    def pen_strokes(self) -> list[_Stroke]:
        """Every visible stroke outside the furniture, with its width and dashes."""
        found: list[_Stroke] = []
        for order, node, name in self._shapes():
            element = node.element
            if any(
                ticks._TICK.match(g) or g.startswith(_FURNITURE) for g in node.groups
            ):
                continue
            stroke = _style(element, "stroke", ticks._STROKE)
            # A patch whose edge is the colour of its fill draws no line: its
            # edge is the edge of the fill, a backing and not a stroke.
            if stroke in (None, "none", _style(element, "fill", _FILL)):
                continue
            opacity = _number(_style(element, "opacity", _OPACITY), 1.0) * _number(
                _style(element, "stroke-opacity", _STROKE_OPACITY), 1.0
            )
            width = _number(_style(element, "stroke-width", ticks._STROKE_WIDTH), 1.0)
            local = _shape(element, name)
            if opacity <= 0.0 or width <= 0.0 or not local:
                continue
            a, b, c, d, _e, _f = node.matrix
            scale = math.sqrt(abs(a * d - b * c))
            half = width * scale / 2.0
            lines = [[ticks._apply(node.matrix, p) for p in line] for line in local]
            if (_style(element, "stroke-linecap", _LINECAP) or "butt") != "butt":
                lines = [_capped(line, half) for line in lines]
            dashes: tuple[float, ...] = ()
            offset = 0.0
            pattern = _style(element, "stroke-dasharray", _DASHARRAY) or "none"
            lengths = [float(v) * scale for v in ticks._NUMBER.findall(pattern)]
            if sum(lengths) > 0.0:
                dashes = tuple(lengths * (2 if len(lengths) % 2 else 1))
                shift = _style(element, "stroke-dashoffset", _DASHOFFSET)
                offset = _number(shift, 0.0) * scale
            points = [p for line in lines for p in line]
            artist = ticks._artist(node) if node.groups else f"a <{name}>"
            found.append(
                _Stroke(
                    artist,
                    lines,
                    half,
                    dashes,
                    offset,
                    order,
                    node.clips,
                    ticks._box(points),
                )
            )
        return found

    def fills(self) -> list[_Fill]:
        """Every fill opaque enough to hide what is painted under it."""
        found: list[_Fill] = []
        for order, node, name in self._shapes():
            element = node.element
            if name in ("line", "polyline"):
                continue
            if any(ticks._TICK.match(g) for g in node.groups):
                continue
            # SVG fills in black when nothing says otherwise, and matplotlib
            # relies on it: the black plate of a legend on the dark page is
            # written with no fill at all.
            fill = _style(element, "fill", _FILL) or "#000000"
            opacity = _number(_style(element, "opacity", _OPACITY), 1.0) * _number(
                _style(element, "fill-opacity", _FILL_OPACITY), 1.0
            )
            if fill == "none" or opacity < _OPAQUE:
                continue
            for line in _shape(element, name):
                polygon = [ticks._apply(node.matrix, p) for p in line]
                if len(polygon) >= 3:
                    found.append(_Fill(polygon, ticks._box(polygon), order, node.clips))
        return found


# --------------------------------------------------------------------------
# Measuring.


def _frame(text: _Text) -> _Frame:
    """The axes of *text*, read off its first glyph, and its letters' extent on them."""
    first = text.letters[0].quad
    dx, dy = first[1][0] - first[0][0], first[1][1] - first[0][1]
    length = math.hypot(dx, dy) or 1.0
    along = (dx / length, dy / length)
    across = (-along[1], along[0])
    corners = [p for letter in text.letters for p in letter.quad]
    start, end = _project(corners, along)
    top, bottom = _project(corners, across)
    return _Frame(along, across, start, end, top, bottom)


def _hidden(sheet: Sheet, point: Point, order: int, fills: list[_Fill]) -> bool:
    """Whether an opaque fill painted after *order* covers *point*."""
    for fill in fills:
        box = fill.box
        if fill.order <= order or not (
            box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]
        ):
            continue
        if ticks._inside(point, fill.polygon) and sheet.visible(point, fill.clips):
            return True
    return False


def _dash_on(stroke: _Stroke, distance: float) -> bool:
    """Whether the stroke's dash pattern draws at *distance* along its subpath."""
    if not stroke.dashes:
        return True
    phase = (distance + stroke.offset) % sum(stroke.dashes)
    for k, length in enumerate(stroke.dashes):
        if phase < length:
            return k % 2 == 0
        phase -= length
    return True


def _drawn(
    sheet: Sheet, stroke: _Stroke, point: Point, distance: float, fills: list[_Fill]
) -> bool:
    """Whether the stroke puts ink at *point*: on a dash, inside its clip, uncovered."""
    return (
        _dash_on(stroke, distance)
        and sheet.visible(point, stroke.clips)
        and not _hidden(sheet, point, stroke.order, fills)
    )


def _tip_room(stroke: _Stroke, line: list[Point]) -> float:
    """How far from each open end of *line* its ink is read as pointing.

    A leader, and a curve labelled at its end, stop at the words they name,
    and the cap they end in may touch the first letter. The last
    :data:`POINTER_PT` of an open subpath, past its cap, is read as pointing
    at whatever it ends on; the rest of it, however far it reaches into a
    text, runs into it. A closed shape has no end to point with.
    """
    if len(line) < 2 or line[0] == line[-1]:
        return 0.0
    return POINTER_PT + 2.0 * stroke.half_width


def _ink(
    sheet: Sheet, stroke: _Stroke, text: _Text, fills: list[_Fill]
) -> tuple[float, Point] | None:
    """How much of the letters of *text* the stroke covers, and where.

    Sampled on a grid :data:`_STEP` apart along and across the stroke, each
    sample tested against the outline of the glyph it falls in, so a stroke
    through the counter of an "o" or the gap between two words lays no ink
    on them here. That case is what :func:`_cut` is for.
    """
    half = stroke.half_width
    if not _overlaps(ticks._grown(stroke.box, half), text.box):
        return None
    across = max(1, round(2.0 * half / _STEP))
    offsets = [-half + (j + 0.5) * 2.0 * half / across for j in range(across)]
    area = 0.0
    where: Point | None = None
    for line in stroke.lines:
        room = _tip_room(stroke, line)
        total = sum(math.dist(p, q) for p, q in itertools.pairwise(line))
        walked = 0.0
        for start, end in itertools.pairwise(line):
            length = math.dist(start, end)
            reach = ticks._grown(ticks._box([start, end]), half)
            ux, uy = (
                (end[0] - start[0]) / (length or 1.0),
                (end[1] - start[1]) / (length or 1.0),
            )
            for letter in (
                text.letters if length > 1e-9 and _overlaps(reach, text.box) else ()
            ):
                stretch = (
                    _clip(start, end, _slabs(letter.quad, half))
                    if _overlaps(reach, letter.box)
                    else None
                )
                if stretch is None:
                    continue
                low, high = stretch[0] * length, stretch[1] * length
                steps = max(1, math.ceil((high - low) / _STEP))
                cell = (high - low) / steps * 2.0 * half / across
                for i in range(steps):
                    s = low + (i + 0.5) * (high - low) / steps
                    if min(walked + s, total - walked - s) < room:
                        continue
                    centre = (start[0] + ux * s, start[1] + uy * s)
                    drawn: bool | None = None
                    for w in offsets:
                        point = (centre[0] - uy * w, centre[1] + ux * w)
                        local = ticks._apply(letter.inverse, point)
                        box = letter.local
                        if not (
                            box[0] <= local[0] <= box[2]
                            and box[1] <= local[1] <= box[3]
                        ):
                            continue
                        if not _filled(local, letter.outline):
                            continue
                        if drawn is None:
                            drawn = _drawn(sheet, stroke, centre, walked + s, fills)
                        if drawn:
                            area += cell
                            where = where or point
            walked += length
    return (area, where) if where is not None else None


def _cut(
    sheet: Sheet, stroke: _Stroke, text: _Text, fills: list[_Fill]
) -> tuple[float, Point] | None:
    """Where the stroke crosses the line of *text* from one side to the other.

    The line is the band the letters fill, in the text's own axes, so a label
    turned on a 3-D plate is read along its own baseline. A crossing counts
    when a stretch of the stroke inside the band spans its whole height,
    within the ends of the line, and puts ink down there. Returns how far
    inside the nearer end of the line the crossing falls.
    """
    half = stroke.half_width
    if not _overlaps(ticks._grown(stroke.box, half), text.box):
        return None
    frame = _frame(text)
    grace = half - TOLERANCE_PT
    slabs: list[Slab] = [
        (frame.along, frame.start - grace, frame.end + grace),
        (frame.across, frame.top, frame.bottom),
    ]
    best: tuple[float, Point] | None = None
    for line in stroke.lines:
        runs: list[list[tuple[Point, float]]] = []
        walked = 0.0
        joined = False
        for start, end in itertools.pairwise(line):
            length = math.dist(start, end)
            stretch = _clip(start, end, slabs) if length > 1e-9 else None
            if stretch is None:
                joined = False
            else:
                low, high = stretch
                if not (joined and low < 1e-9):
                    runs.append([])
                runs[-1].extend(
                    (
                        (
                            start[0] + (end[0] - start[0]) * t,
                            start[1] + (end[1] - start[1]) * t,
                        ),
                        walked + t * length,
                    )
                    for t in (low, high)
                )
                joined = high > 1.0 - 1e-9
            walked += length
        for run in runs:
            spans = [p[0] * frame.across[0] + p[1] * frame.across[1] for p, _ in run]
            if max(spans) - min(spans) < (frame.bottom - frame.top) - 1e-6:
                continue
            for (p, s), (q, t) in itertools.pairwise(run):
                for k in range(ticks._CLIP_SAMPLES):
                    f = (k + 0.5) / ticks._CLIP_SAMPLES
                    point = (p[0] + (q[0] - p[0]) * f, p[1] + (q[1] - p[1]) * f)
                    if not _drawn(sheet, stroke, point, s + (t - s) * f, fills):
                        continue
                    a = point[0] * frame.along[0] + point[1] * frame.along[1]
                    inside = min(a - frame.start, frame.end - a) + half
                    if inside > TOLERANCE_PT and (best is None or inside > best[0]):
                        best = (inside, point)
    return best


def _closeness(one: _Text, other: _Text) -> tuple[float, Point] | None:
    """How far the letters of two texts reach into each other, when within the gap."""
    if not _overlaps(ticks._grown(one.box, GAP_PT), other.box):
        return None
    best: tuple[float, Point] | None = None
    for la in one.letters:
        near = ticks._grown(la.box, GAP_PT)
        if not _overlaps(near, other.box):
            continue
        for lb in other.letters:
            if not _overlaps(near, lb.box):
                continue
            depth = _depth(la.quad, lb.quad)
            if depth > -GAP_PT and (best is None or depth > best[0]):
                x0, y0, x1, y1 = la.box
                best = (depth, ((x0 + x1) / 2.0, (y0 + y1) / 2.0))
    return best


def _leads(sheet: Sheet, stroke: _Stroke, text: _Text) -> bool:
    """Whether *stroke* is the arrow of the annotation that writes *text*.

    It is the patch written just before the text, and it starts at the
    words: the spine an axes writes last stands just before the first text
    after it too, and it starts at a corner of the axes.
    """
    if sheet.leaders.get(stroke.artist) != text.owner:
        return False
    x0, y0, x1, y1 = ticks._grown(text.box, LEADER_PT)
    return any(
        x0 <= x <= x1 and y0 <= y <= y1 for line in stroke.lines for x, y in line
    )


def measure(path: pathlib.Path) -> list[Finding]:
    """Every text of *path* that another text or a stroke is drawn over."""
    sheet = Sheet(path)
    texts = sheet.texts()
    found: list[Finding] = []
    for one, other in itertools.combinations(texts, 2):
        roles = {one.role, other.role}
        if one.owner == other.owner or "legend" in roles or roles == {"tick"}:
            continue
        hit = _closeness(one, other)
        if hit is None:
            continue
        if "tick" in roles:
            tick, text = (one, other) if one.role == "tick" else (other, one)
            found.append(Finding(path.stem, "tick", repr(text.text), tick.text, *hit))
        else:
            found.append(Finding(path.stem, "text", repr(other.text), one.text, *hit))
    fills = sheet.fills()
    for stroke in sheet.pen_strokes():
        for text in texts:
            if text.role == "tick" or _leads(sheet, stroke, text):
                continue
            cut = _cut(sheet, stroke, text, fills)
            if cut is not None:
                found.append(Finding(path.stem, "cut", stroke.artist, text.text, *cut))
                continue
            ink = _ink(sheet, stroke, text, fills)
            if ink is not None and ink[0] > INK_PT2:
                found.append(Finding(path.stem, "ink", stroke.artist, text.text, *ink))
    return found


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; see the module docstring."""
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "files",
        nargs="*",
        type=pathlib.Path,
        help="SVG figures (default: every committed light drawing)",
    )
    parser.add_argument(
        "--report", action="store_true", help="print every finding and always exit 0"
    )
    args = parser.parse_args(argv)
    files = args.files or legends.light_figures()
    findings = [finding for path in files for finding in measure(path)]
    if args.report:
        for finding in findings:
            print(finding.describe())
        print(f"\n{len(findings)} finding(s) in {len(files)} drawings.")
        return 0
    offenders = [
        f for f in findings if f.key not in EXEMPTIONS and f.drawing not in EXEMPTIONS
    ]
    fired = {f.key for f in findings} | {f.drawing for f in findings}
    stale = sorted(set(EXEMPTIONS) - fired) if not args.files else []
    for key in stale:
        print(
            f"::error::EXEMPTIONS names {key!r}, which no longer fires: delete the entry"
        )
    if offenders:
        print(f"::error::{len(offenders)} text(s) have something drawn over them:")
        for finding in offenders:
            print(f"  {finding.describe()}")
    if offenders or stale:
        return 1
    print(f"Every text is clear: {len(files)} drawings, {len(EXEMPTIONS)} exempt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
