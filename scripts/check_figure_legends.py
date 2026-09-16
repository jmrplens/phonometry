#!/usr/bin/env python3
"""Fail on a legend that closes over a plotted point.

A legend is an opaque plate the author places by hand, and its width is set by
its longest label. That is a defect waiting to happen in a bilingual corpus:
the Spanish label is routinely half again as long as the English one, so a box
that clears the data in one language reaches back over it in the other. The
figure still passes every other gate. The staleness check
(:mod:`scripts.check_figures`) compares a regeneration against what is
committed and knows nothing about what the drawing covers; the annotation
audit (:mod:`scripts.figure_annotation_audit`) measures *labels* and says in
its own docstring why this matters, that "a plotted point, a marker or the end
of a range bar under it is a datum the reader no longer has", and then looks
at no legend at all.

What it reads
-------------
The committed SVG, not a generation run. Everything this needs is declarative
in the shipped file, so it costs seconds and answers about the drawing as it
ships rather than about a rebuild of it:

* a legend is ``<g id="legend_N">``, and its frame is the first ``<path>``
  inside it that is filled with a colour, has no ``id`` of its own and holds
  the legend's own handles;
* a plotted point is a ``<use>`` outside every legend group, referencing a
  glyph defined in a ``<defs>``.

A legend drawn with ``frameon=False`` writes no such path and is not measured,
which is right rather than a gap: what it puts over the drawing is its own
letters, and letters over a curve are what the annotation audit measures.

Both are read in the figure's own coordinates. The ``translate()`` of every
ancestor group is accumulated on the way down, which costs nothing and is what
SVG means: the corpus as it stands places every marker absolutely, and a
generator that wraps a series in a moved group would otherwise have its points
read against the page.

Telling a marker from a filled band
-----------------------------------
matplotlib names the glyph of a marker and the polygon of a ``fill_between``
the same way, ``m`` followed by a hash, and places both with ``<use>``. Size is
what separates them and nothing else does: a marker glyph is a few points
across, a filled band is the width of the axes. :data:`MARKER_MAX_PT` is the
cut, and it is generous rather than tight because the largest marker in the
corpus is a 12 pt diamond and the smallest band is still hundreds of points
wide, so anything between the two is not a case that exists. A letter is
defined and placed the same way again, under its font's name rather than a
hash, and :data:`_GLYPH_ID` is what keeps a word inside a legend from reading
as a series of points under it.

The light drawings only. A figure ships as four files and the dark pair is the
same drawing in other colours, so the geometry is identical and reporting it
four times would say the same thing four times. Both languages are read,
because the language is the whole point.

The exemptions file
-------------------
This cannot tell a datum that carries a value from a rail of identical marks.
``true_peak_intersample`` draws its oversampled grid as a comb of tick markers
and the legend covers a stretch of it; the comb continues either side and the
reader loses nothing, which is a decision and not a defect. So the gate reports
what it measures and :data:`EXEMPTIONS` carries the decisions with the reason
each one is a decision, ratcheted in both directions like the annotation file
next to it: an entry whose figure no longer fires is deleted, and a figure that
starts firing has to be fixed or written down.

Usage::

    python scripts/check_figure_legends.py            # gate: exit 1 on any offender
    python scripts/check_figure_legends.py --report   # every overlap, always exit 0
    python scripts/check_figure_legends.py FILE ...   # restrict to given files

Exit status 0 when no legend covers a point that is not written down, 1
otherwise.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys
import xml.etree.ElementTree as ET
from typing import NamedTuple

SVG = "{http://www.w3.org/2000/svg}"
XLINK = "{http://www.w3.org/1999/xlink}"

#: The committed figures.
IMG_DIR = pathlib.Path(__file__).resolve().parent.parent / ".github" / "images"

#: The largest a glyph may be, in points, and still be a marker rather than a
#: filled band. See the module docstring for why the cut is where it is.
MARKER_MAX_PT = 20.0

#: Every number in a path's ``d``, which is enough for a bounding box: the
#: commands these paths use (``M``, ``L``, ``C``, ``Q``, ``z``) all write their
#: coordinates in pairs, and a curve's control points bound its arc.
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")

#: A ``translate()`` on a group. matplotlib writes no other transform on the
#: groups that hold markers.
_TRANSLATE = re.compile(r"translate\(\s*(-?[\d.eE+-]+)[ ,]+(-?[\d.eE+-]+)\s*\)")

#: How matplotlib names a glyph it will place with ``<use>``: an ``m`` and the
#: hash of what it draws. A letter is defined the same way and placed the same
#: way, under its font's name and the character's code point
#: (``DejaVuSans-31``), and the diagram plates bake their labels to outlines at
#: final size, which makes a small letter exactly marker-sized. The name is what
#: separates the two, so a word inside a legend box is not read as a series of
#: points under it.
_GLYPH_ID = re.compile(r"^m[0-9a-f]+$")

#: Drawings whose legend covers a mark that is not a datum, with the reason.
#: Read the module docstring before adding one: a legend that is merely
#: inconvenient to move does not belong here.
EXEMPTIONS: dict[str, str] = {
    "true_peak_intersample": (
        "the marks under the legend are the comb of the 4x oversampled grid, "
        "which is a rail of identical ticks and not a series of values: it "
        "continues either side of the box and the reader loses no reading"
    ),
}


class Overlap(NamedTuple):
    """One plotted point a legend frame closes over."""

    drawing: str
    legend: str
    artist: str
    x: float
    y: float

    def describe(self) -> str:
        """One line naming the drawing, the legend and where the point sits."""
        return (
            f"{self.drawing}: {self.legend} covers {self.artist} "
            f"at ({self.x:.1f}, {self.y:.1f})"
        )


def _box(d: str) -> tuple[float, float, float, float] | None:
    """The bounding box of a path's ``d``, or ``None`` when it has no points."""
    numbers = [float(n) for n in _NUMBER.findall(d)]
    xs, ys = numbers[0::2], numbers[1::2]
    if not xs or not ys:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def _glyphs(root: ET.Element) -> dict[str, tuple[float, float, float, float]]:
    """Every defined path small enough to be a marker, by id."""
    found: dict[str, tuple[float, float, float, float]] = {}
    for path in root.iter(SVG + "path"):
        name = path.get("id")
        if not name or not _GLYPH_ID.match(name):
            continue
        box = _box(path.get("d", ""))
        if box is None:
            continue
        if box[2] - box[0] <= MARKER_MAX_PT and box[3] - box[1] <= MARKER_MAX_PT:
            found[name] = box
    return found


def _walk(
    element: ET.Element,
    *,
    dx: float = 0.0,
    dy: float = 0.0,
    legend: str | None = None,
) -> list[tuple[ET.Element, float, float, str | None]]:
    """Every element with the offset it inherits and the legend it sits in."""
    name = element.get("id") or ""
    if element.tag == SVG + "g" and name.startswith("legend_"):
        legend = name
    moved = _TRANSLATE.search(element.get("transform") or "")
    if moved:
        dx, dy = dx + float(moved.group(1)), dy + float(moved.group(2))
    found = [(element, dx, dy, legend)]
    for child in element:
        found.extend(_walk(child, dx=dx, dy=dy, legend=legend))
    return found


def _placed(
    nodes: list[tuple[ET.Element, float, float, str | None]],
) -> dict[str, list[tuple[float, float]]]:
    """Where each legend puts the handle glyphs of its own entries."""
    placed: dict[str, list[tuple[float, float]]] = {}
    for element, dx, dy, legend in nodes:
        if legend is None or element.tag != SVG + "use":
            continue
        try:
            point = (float(element.get("x", "")) + dx, float(element.get("y", "")) + dy)
        except ValueError:
            continue
        placed.setdefault(legend, []).append(point)
    return placed


def _frames(
    nodes: list[tuple[ET.Element, float, float, str | None]],
) -> dict[str, tuple[float, float, float, float]]:
    """The frame of every legend that draws one, in figure coordinates.

    The frame is the first path inside the group that is filled with a colour,
    carries no ``id`` of its own and holds the legend's own handles. Holding
    them is what the test is for: a legend drawn with ``frameon=False`` writes
    no frame at all, and the first filled path inside it is then a swatch or a
    rule belonging to one of its entries, which is a mark of the legend rather
    than a plate over the drawing. Such a legend is left out, and the drawing
    under it is measured by the annotation audit instead.
    """
    placed = _placed(nodes)
    frames: dict[str, tuple[float, float, float, float]] = {}
    for element, dx, dy, legend in nodes:
        if legend is None or legend in frames:
            continue
        if element.tag != SVG + "path" or element.get("id"):
            continue
        style = element.get("style") or ""
        if "fill:" not in style or "fill: none" in style:
            continue
        box = _box(element.get("d", ""))
        if box is None:
            continue
        x0, y0 = box[0] + dx, box[1] + dy
        x1, y1 = box[2] + dx, box[3] + dy
        if all(x0 <= x <= x1 and y0 <= y <= y1 for x, y in placed.get(legend, [])):
            frames[legend] = (x0, y0, x1, y1)
    return frames


def measure(path: pathlib.Path) -> list[Overlap]:
    """Every plotted point a legend of *path* closes over."""
    root = ET.parse(path).getroot()
    glyphs = _glyphs(root)
    nodes = _walk(root)
    frames = _frames(nodes)
    if not frames:
        return []
    parents = {child: parent for parent, *_ in nodes for child in parent}
    found: list[Overlap] = []
    for element, dx, dy, legend in nodes:
        if element.tag != SVG + "use" or legend is not None:
            continue
        ref = (element.get(XLINK + "href") or element.get("href") or "").lstrip("#")
        glyph = glyphs.get(ref)
        if glyph is None:
            continue
        try:
            x = float(element.get("x", "")) + dx
            y = float(element.get("y", "")) + dy
        except ValueError:
            continue
        for name, (x0, y0, x1, y1) in frames.items():
            covers = (
                x + glyph[2] > x0
                and x + glyph[0] < x1
                and y + glyph[3] > y0
                and y + glyph[1] < y1
            )
            if covers:
                found.append(Overlap(path.stem, name, _artist(element, parents), x, y))
    return found


def _artist(element: ET.Element, parents: dict[ET.Element, ET.Element]) -> str:
    """The nearest named ancestor of *element*, which is the artist drawing it.

    matplotlib names an artist for its kind and a running number, ``line2d_52``
    or ``patch_14``, and a clipping path for a hash, ``p9c3f0a1b2c``. The
    underscore is what tells the two apart, and only the first is worth
    printing: a clip is where a mark was cut, not what drew it.
    """
    walker: ET.Element | None = element
    while walker is not None:
        name = walker.get("id") or ""
        if "_" in name:
            return name
        walker = parents.get(walker)
    return "an unnamed artist"


def light_figures() -> list[pathlib.Path]:
    """The drawings this reads: both languages, light only."""
    return sorted(p for p in IMG_DIR.glob("*.svg") if not p.stem.endswith("_dark"))


def _drawing(stem: str) -> str:
    """The figure a drawing belongs to, with the language suffix taken off."""
    return stem.removesuffix("_es")


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
        help="print every overlap, exempt or not, and always exit 0",
    )
    args = parser.parse_args(argv)

    files = args.files or light_figures()
    overlaps: list[Overlap] = []
    for path in files:
        overlaps.extend(measure(path))

    if args.report:
        for overlap in overlaps:
            print(overlap.describe())
        print(f"\n{len(overlaps)} overlap(s) in {len(files)} drawings.")
        return 0

    offenders = [o for o in overlaps if _drawing(o.drawing) not in EXEMPTIONS]
    covered = {_drawing(o.drawing) for o in overlaps}
    stale = sorted(set(EXEMPTIONS) - covered)
    if stale:
        print(
            f"::error::{len(stale)} exemption(s) name a figure whose legend no "
            "longer covers anything; delete the entry:"
        )
        for name in stale:
            print(f"  {name}")
    if offenders:
        print(
            f"::error::{len(offenders)} plotted point(s) sit under a legend - "
            "move the legend, or write the figure down in EXEMPTIONS with the "
            "reason the mark is not a reading:"
        )
        for overlap in offenders:
            print(f"  {overlap.describe()}")
    if offenders or stale:
        return 1
    print(
        f"No legend covers a plotted point: {len(files)} drawings, "
        f"{len(EXEMPTIONS)} exempt."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
