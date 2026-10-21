#!/usr/bin/env python3
"""Find strokes that composite to near-invisibility on the dark page.

The contrast checker measures filled regions. A stroke is not a fill, so a
half-opacity mid grey on a 0.4 pt line passed every gate and disappeared on the
dark theme, which is how the ISO 3745 wireframe shipped invisible.

Blends every stroke colour with its opacity over the page it is drawn on and
reports the ones that land close to it, weighted by how thin the line is: a
hairline needs more contrast than a thick one to read at all.

The opacity is everything SVG multiplies into the stroke: its own
``stroke-opacity``, the ``opacity`` of the element (where matplotlib writes the
alpha of a patch faded with ``set_alpha``, an arc or a polygon outline) and the
``opacity`` of every group it sits in. Reading the first alone measured a
faded patch outline at full strength.

The page is the one the drawing paints behind the stroke, read off the drawing
itself, not a constant: the background of the axes the stroke is in, else of
the figure, else the plate a hand-made diagram lays first, else the dark
ground of the site (:data:`SITE_PAGE`) the drawing would sit on with none of
its own. A dark matplotlib figure writes its figure and axes patches with no
fill, which SVG paints opaque black, so its strokes are read on black; the
diagrams paint ``#0d1117``. Measuring them all on one panel grey judged a
translucent stroke more leniently, and an opaque one more strictly, than the
page the reader sees behind it.

Two kinds of stroke are not measured, because for them the page is not what
the reader sees behind the line:

* **Grid and axis furniture**, which is drawn to recede.  In two dimensions it
  is recognised by colour (:data:`SCAFFOLDING`); in three, matplotlib names
  the group itself (:data:`SCAFFOLD_GROUPS`), which is how the 3-D grid of the
  microphone arrays is exempt without pinning the theme-derived grey it is
  drawn in.
* **Strokes inside an axes that an opaque field covers** -- a filled contour
  set, a mesh, an embedded raster.  The level lines of a noise contour are
  drawn on viridis and the ISO 1999 contours on YlOrRd; they are read against
  that field, and the field's own legibility is
  ``scripts/check_figure_contrast.py``'s business, not this one's.
"""

from __future__ import annotations

import pathlib
import re
import sys
from xml.etree import ElementTree as ET

_SCRIPTS = pathlib.Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import check_figure_contrast as fill_contrast

#: The dark ground of the documentation site (``--sl-color-black`` in
#: ``site/src/styles/theme.css``): what is behind a stroke whose drawing
#: paints no page of its own.
SITE_PAGE = (0x0D, 0x11, 0x14)

#: An RGB colour on the 0-255 scale.
Rgb = tuple[int, int, int]

SVG_NS = "{http://www.w3.org/2000/svg}"

#: Grid and axis furniture: drawn to recede, so the floor below does not apply.
#: Everything else with a stroke and no fill is a line somebody meant to be seen.
SCAFFOLDING = {(0x55, 0x55, 0x55), (0xE0, 0xE0, 0xE0), (0xB0, 0xB0, 0xB0)}

#: Groups matplotlib names for its own scaffolding. The 3-D grid is drawn in a
#: colour derived from the page (``theme_fill(foreground, ax, delta_e=24)``),
#: so it cannot be recognised from a list of literal greys the way the 2-D grid
#: is; the group name is what stays true when the theme moves.
SCAFFOLD_GROUPS = ("grid3d",)

#: Group names that mean the axes is covered by an opaque field rather than by
#: the page: a filled contour set, a quadrilateral mesh (``pcolormesh``, and
#: the colourbar of either).
FIELD_GROUPS = ("QuadContourSet", "QuadMesh")


def _srgb_to_lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(rgb: tuple[float, float, float]) -> float:
    r, g, b = (_srgb_to_lin(v / 255.0) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _ratio(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    la, lb = _luminance(a), _luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _opacity(style: str) -> float:
    """The ``opacity`` an element or group declares, which fades all of it."""
    found = re.search(r"(?:^|;)\s*opacity:\s*([0-9.]+)", style)
    return float(found.group(1)) if found else 1.0


def _parse(style: str) -> tuple[Rgb | None, float, float]:
    """The stroke colour, its own ``stroke-opacity`` and its width.

    The ``opacity`` of the element is not in it: :func:`_strokes` multiplies
    that in with the opacity of the groups round the element.
    """
    colour = re.search(r"stroke:\s*#([0-9a-fA-F]{6})", style)
    opacity = re.search(r"stroke-opacity:\s*([0-9.]+)", style)
    width = re.search(r"stroke-width:\s*([0-9.]+)", style)
    if not colour:
        return None, 1.0, 1.0
    v = colour.group(1)
    rgb = (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16))
    return (
        rgb,
        float(opacity.group(1)) if opacity else 1.0,
        float(width.group(1)) if width else 1.0,
    )


def _rgb(colour: tuple[float, float, float]) -> Rgb:
    """A 0-1 colour as :mod:`check_figure_contrast` reads one, on 0-255."""
    return (round(colour[0] * 255), round(colour[1] * 255), round(colour[2] * 255))


def page_of(root: ET.Element) -> Rgb:
    """The page a drawing paints first, or :data:`SITE_PAGE` when it paints none.

    A hand-made diagram lays its plate as the first shape of the document; a
    matplotlib drawing paints its page inside ``figure_1``, which
    :func:`_strokes` reads on the way down.
    """
    for child in root:
        tag = child.tag.removeprefix(SVG_NS)
        if tag in ("title", "desc", "defs", "style", "metadata"):
            continue
        if tag == "rect":
            colour = fill_contrast._parse_color(
                fill_contrast._parse_style(child).get("fill", "black")
            )
            if colour is not None:
                return _rgb(colour)
        break
    return SITE_PAGE


def _group_id(element: ET.Element) -> str:
    """The ``id`` of a group element, without matplotlib's trailing counter."""
    if element.tag != f"{SVG_NS}g":
        return ""
    return element.get("id", "").rsplit("_", 1)[0]


def _is_field(element: ET.Element) -> bool:
    """Whether this subtree paints an opaque field over the axes it is in."""
    if element.tag == f"{SVG_NS}image":
        return True
    if _group_id(element) in FIELD_GROUPS:
        # A contour set drawn as *lines* is the thing being checked, not a
        # field: only the filled one hides the page.
        return any("fill: #" in (child.get("style") or "") for child in element.iter())
    return any(_is_field(child) for child in element)


def _strokes(
    element: ET.Element,
    *,
    on_field: bool = False,
    page: Rgb = SITE_PAGE,
    faded: float = 1.0,
) -> list[tuple[Rgb, float, float, Rgb]]:
    """Every measurable stroke in a subtree, as ``(rgb, opacity, width, page)``.

    *page* is what is painted behind the subtree, and *faded* the opacity
    its enclosing groups multiply into everything inside them.
    """
    group = _group_id(element)
    if group in SCAFFOLD_GROUPS:
        return []
    if group == "axes":
        on_field = any(_is_field(child) for child in element)
    if group in ("axes", "figure"):
        background, _area, _group = fill_contrast._axes_geometry(
            element,
            {},
            tuple(c / 255.0 for c in page),  # type: ignore[arg-type]
        )
        page = _rgb(background)
    found: list[tuple[Rgb, float, float, Rgb]] = []
    style = element.get("style") or ""
    # matplotlib writes the alpha of a ``Line2D`` as ``stroke-opacity`` and
    # that of a patch faded with ``set_alpha`` as ``opacity``: both fade the
    # line, as does the opacity of every group round it.
    here = faded * _opacity(style)
    if "stroke:" in style and "fill: none" in style and not on_field:
        rgb, alpha, width = _parse(style)
        if rgb is not None and rgb not in SCAFFOLDING:
            found.append((rgb, alpha * here, width, page))
    if element.tag == f"{SVG_NS}g":
        faded = here
    for child in element:
        found.extend(_strokes(child, on_field=on_field, page=page, faded=faded))
    return found


def faint_strokes(svg: pathlib.Path) -> list[tuple[float, str]]:
    """Every distinct stroke of one dark drawing that is too faint for its width.

    ``(ratio, detail)`` per stroke colour, opacity and width: the per-drawing
    half of :func:`main`, which the clip frame audit runs on each dark frame.
    """
    found: list[tuple[float, str]] = []
    seen: set[tuple[Rgb, float, float, Rgb]] = set()
    root = ET.parse(svg).getroot()
    for rgb, alpha, width, page in _strokes(root, page=page_of(root)):
        key = (rgb, round(alpha, 4), width, page)
        if key in seen:
            continue
        seen.add(key)
        blended = tuple(
            alpha * c + (1 - alpha) * p for c, p in zip(rgb, page, strict=True)
        )
        ratio = _ratio(blended, page)  # type: ignore[arg-type]
        # A hairline has to work harder: below 0.6 pt demand 3:1, else 2:1.
        floor = 3.0 if width < 0.6 else 2.0
        if ratio < floor:
            detail = (
                f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x} alpha={key[1]:g} "
                f"width={width} on #{page[0]:02x}{page[1]:02x}{page[2]:02x} "
                f"-> {ratio:.2f}:1 (min {floor})"
            )
            found.append((ratio, detail))
    return found


def main() -> int:
    images = pathlib.Path(".github/images")
    rows: list[tuple[float, str, str]] = []
    for svg in sorted(images.glob("*_dark.svg")):
        rows.extend((ratio, svg.name, detail) for ratio, detail in faint_strokes(svg))
    rows.sort()
    print(f"{len(rows)} low-contrast strokes on the dark page\n")
    for _, name, detail in rows:
        print(f"  {name:<52} {detail}")
    return 1 if rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
