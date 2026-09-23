#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Diagrams of the devices guides: emission, electroacoustics, broadcast and noise control.

One subject: a device under test and the setup that measures it. The
emission diagrams draw the sound power and intensity methods that grade a
machine, the electroacoustics diagrams draw the transducer measurements, the
broadcast diagrams draw the programme loudness chain and the tests of the
quasi-peak meter, and the noise control diagram draws what is done to a device
once it has been graded.
"""

from __future__ import annotations

import itertools
import math
from typing import TYPE_CHECKING, NamedTuple

from .parts import _accel, _box_solid, _box_wire, _motion_arrows, _rot_arrow

if TYPE_CHECKING:
    from .canvas import SVG, Theme

# ---------------------------------------------------------------------------
# d6 - Two-microphone (p-p) intensity probe (IEC 61043)
# ---------------------------------------------------------------------------


def _d_pp_probe(s: SVG, th: Theme) -> None:
    ay = 232.0  # probe axis height

    # Measurement axis / intensity direction (drawn first, under the probe)
    s.line(70, ay, 820, ay, th.accent, 1.4, dash="10,4,2,4")
    s.arrow(820, ay, 852, ay, th.accent, 1.8)
    s.text(450, 305, "measurement axis / intensity direction", 15, th.accent)

    # Two opposed capsules facing each other with a spacer between the tips
    for side in (-1, 1):
        # bodies: 180..320 and 580..720; capsules: 320..400 / 500..580;
        # tips (grilles): 400..414 / 486..500; gap 414..486 = Δr
        bx = 180.0 if side < 0 else 580.0
        cx = 320.0 if side < 0 else 500.0
        tx = 400.0 if side < 0 else 486.0
        s.rect(bx, ay - 28, 140, 56, th.panel, th.primary, rx=10, sw=2)
        s.rect(cx, ay - 20, 80, 40, th.fg, rx=4)
        s.rect(tx, ay - 16, 14, 32, th.muted, rx=2)
    s.rect(414, ay - 6, 72, 12, th.panel, th.muted, rx=4, sw=1.2)  # spacer

    s.text(360, ay - 38, "$p_1$", 17, th.fg, bold=True)
    s.text(540, ay - 38, "$p_2$", 17, th.fg, bold=True)

    # Δr dimension between the capsule tips, drafting style
    s.dim(414, ay - 16, 486, ay - 16, "$Δr$ = 12 mm", offset=-66, size=15)

    # p-p estimator notes near the capsules
    s.text(280, 365, "$u$ from the $p_2−p_1$ gradient", 16, th.muted)
    s.text(620, 365, "$p = (p_1+p_2)/2$", 16, th.muted)


# ---------------------------------------------------------------------------
# d10 - ISO 3744/3746 sound power measurement surfaces
# ---------------------------------------------------------------------------


def _d_surfaces(s: SVG, th: Theme) -> None:
    # ===== Left panel: hemispherical surface over a reflecting plane =====
    cx, gy, R = 235.0, 420.0, 150.0
    s.text(cx, 74, "Hemispherical surface", 19, th.fg, bold=True)

    # Reflecting plane (hatched line through the equator / footprint centre).
    s.ground(gy, 55, 430)
    # Under the footprint ellipse, which ran through the words at gy + 34;
    # the two captions below move down to make room.
    s.text(60, gy + 62, "Reflecting plane", 15, th.muted, anchor="start")

    # Hemisphere: dashed footprint ellipse + solid dome silhouette.
    ky = 0.30
    s.ellipse(cx, gy, R, R * ky, "none", th.muted, 1.3, dash="5,4")
    s.path(f"M {cx - R} {gy} A {R} {R} 0 0 1 {cx + R} {gy}", stroke=th.primary, sw=2.4)

    # Source box at the centre O.
    _box_solid(s, th, cx, gy, 30, 24, 34)
    s.circle(cx, gy, 3.4, th.fg)

    # Ten key microphone positions (ISO 3744 Table B.1), oblique-projected.
    b1 = [
        (0.16, -0.96, 0.22),
        (0.78, -0.60, 0.20),
        (0.78, 0.55, 0.31),
        (0.16, 0.90, 0.41),
        (-0.83, 0.32, 0.45),
        (-0.83, -0.40, 0.38),
        (-0.26, -0.65, 0.71),
        (0.74, -0.07, 0.67),
        (-0.26, 0.50, 0.83),
        (0.10, -0.10, 0.99),
    ]
    labelled = {1, 8, 10}
    pts = []
    for x, y, z in b1:
        px = cx + R * x + 42 * y
        py = gy - 34 * y - R * z
        pts.append((px, py))
    # radius r drawn to position 8 (a mid-height point on the surface).
    r8 = pts[7]
    s.line(cx, gy, r8[0], r8[1], th.accent, 1.6, dash="6,4")
    # Just outside the dome, level with the middle of the radius: beside the
    # radius itself, the dome ran through the label.
    s.text(
        cx + R + 10,
        (gy + r8[1]) / 2 + 4,
        "radius $r ≥ 2 d_0$",
        15,
        th.accent,
        anchor="start",
    )
    for i, (px, py) in enumerate(pts, start=1):
        s.circle(px, py, 6.5, th.secondary)
        s.circle(px, py, 2.2, th.bg)
        if i in labelled:
            s.text(px, py - 12, str(i), 14, th.fg, bold=True)
    s.text(cx, gy + 88, "10 key positions (Table B.1)", 15, th.muted)
    s.text(cx, gy + 112, "one plane · $S = 2πr^2$", 15, th.primary, bold=True)

    # ===== Right panel: parallelepiped measurement surface =====
    bx2, gy2 = 675.0, 420.0
    s.text(bx2, 74, "Parallelepiped surface", 19, th.fg, bold=True)
    s.ground(gy2, 500, 872)

    # Source box (solid) enclosed by the measurement box (dashed wireframe).
    _box_solid(s, th, bx2, gy2, 46, 40, 58)
    _box_wire(s, th, bx2, gy2, 96, 90, 108, th.accent)
    s.text(bx2, gy2 + 40, "Measurement surface", 15, th.muted)
    s.text(bx2, gy2 + 64, "one plane · $S = 4(a·b+b·c+c·a)$", 15, th.accent, bold=True)

    # Measurement distance d: vertical clearance between the source top face
    # and the enveloping measurement surface (labelled arrow + caption above).
    s.text(bx2, 208, "measurement distance $d$", 15, th.secondary, bold=True)
    # On the source's front-left edge, left of its top face: drawn at the
    # middle, the top face's back edge ran through the "d".
    s.dim(
        bx2 - 46,
        gy2 - 108,
        bx2 - 46,
        gy2 - 58,
        "$d$",
        offset=0,
        size=17,
        label_side="left",
    )


# ---------------------------------------------------------------------------
# d12 - Sound power methods comparison infographic
# ---------------------------------------------------------------------------


class _Method(NamedTuple):
    """One determination route as the sound power plate draws it.

    The designation goes in the header; the five attributes after it are the
    five every cell carries, in the order the cell prints them, so two cells
    of a row can be read against each other line by line.
    """

    name: str
    environment: str
    grade: str
    quantity: str
    relation: str
    limit: str
    color: str
    pictogram: str


#: Geometry of the sound power plate. Three cells of ``_METHOD_CW`` and the
#: two gutters between them fill the 900 px sheet; the one-route row is
#: shorter than a cell because its picture sits beside its text rather than
#: above it.
_METHOD_CW = 286.0
_METHOD_CH = 300.0
_METHOD_GAP = 12.0
_METHOD_BAND_H = 152.0


def _d_methods(s: SVG, th: Theme) -> None:
    """All seven determination routes, one row per measured quantity.

    Every cell carries the same five attributes -- environment, grade,
    measured quantity, headline relation and the limit that binds it -- so a
    row can be read across. The rows are the quantity the instrument actually
    reads: three routes read a sound pressure, three read a sound intensity,
    and one reads the surface velocity of the machine's own casing and takes
    no acoustic measurement at all. The last row therefore holds one route,
    and it spans the three columns rather than sitting in the first of them
    with two empty beside it: the row is the family, and this family has one
    member.
    """
    rows = (
        (
            "Sound pressure",
            (
                _Method(
                    "ISO 3744 / 3746",
                    "Free field over a reflecting plane",
                    "Grade 2 / 3 (engineering / survey)",
                    "Sound pressure · enveloping surface",
                    "$L_W = L̄′_p + 10 log_{10}(S/S_0) − K_1 − K_2$",
                    "$K_{2A}$ ≤ 4 dB (3744) / ≤ 7 dB (3746)",
                    th.primary,
                    "hemi",
                ),
                _Method(
                    "ISO 3745",
                    "Qualified anechoic / hemi-anechoic room",
                    "Grade 1 (precision)",
                    "Sound pressure · fixed 20 / 40 array",
                    "$L_W = L̄_p + 10 log_{10}(S/S_0) + C_1+C_2+C_3$",
                    "$r ≥ 2 d_0$ , qualified free field",
                    th.primary,
                    "anech",
                ),
                _Method(
                    "ISO 3741",
                    "Reverberation test room",
                    "Grade 1 (precision)",
                    "Sound pressure · diffuse field",
                    "$L_W ← L̄_p , A , V , S , f$",
                    "$V$ ≥ 200 m³ , source ≤ 2 % of $V$",
                    th.accent,
                    "reverb",
                ),
            ),
        ),
        (
            "Sound intensity",
            (
                _Method(
                    "ISO 9614-1",
                    "In situ, any environment",
                    "Grade 1 / 2 per band, 3 on $L_{WA}$",
                    "Sound intensity · discrete points",
                    "$L_W = 10 log_{10}(Σ I_i·S_i / P_0)$",
                    "no non-positive bands · two criteria (Annex B)",
                    th.secondary,
                    "points",
                ),
                _Method(
                    "ISO 9614-2",
                    "In situ, any environment",
                    "Grade 2 / 3 (engineering / survey)",
                    "Sound intensity · scanning",
                    "$L_W = 10 log_{10}(|Σ I_i·S_i| / P_0)$",
                    "no non-positive bands · $F_{pI} < L_d$",
                    th.secondary,
                    "scan",
                ),
                _Method(
                    "ISO 9614-3",
                    "In situ, any environment",
                    "Grade 1 (precision)",
                    "Sound intensity · scanning, tighter",
                    "$L_W = 10 log_{10}(|Σ I_i·S_i| / P_0)$",
                    "five Annex C criteria per band",
                    th.secondary,
                    "scan",
                ),
            ),
        ),
        (
            "Surface velocity",
            (
                _Method(
                    "ISO/TS 7849-1 / -2",
                    "Any, no acoustic measurement",
                    "Upper limit ($ε = 1$) / engineering",
                    "Surface velocity · accelerometers",
                    "$L_{WA} = L_{vA} + 10 lg(S/S_0) + 10 lg ε$",
                    "$ε$ assumed (-1) or measured (-2)",
                    th.fg,
                    "accel",
                ),
            ),
        ),
    )
    width = 3 * _METHOD_CW + 2 * _METHOD_GAP
    x0 = (900 - width) / 2
    y = 44.0
    for label, routes in rows:
        _methods_rail(s, th, x0, y, x0 + width, label)
        y += 26.0
        if len(routes) == 1:
            _methods_band(s, th, x0, y, width, routes[0])
            y += _METHOD_BAND_H + 28.0
        else:
            for i, route in enumerate(routes):
                _methods_card(s, th, x0 + i * (_METHOD_CW + _METHOD_GAP), y, route)
            y += _METHOD_CH + 28.0


def _methods_rail(
    s: SVG, th: Theme, x: float, y: float, right: float, label: str
) -> None:
    """The measured quantity a row shares, and a rule out to the margin."""
    s.text(x, y + 14, label, 13, th.muted, anchor="start", bold=True)
    s.line(
        x + s.text_width(label, 13, bold=True) + 12.0,
        y + 10,
        right,
        y + 10,
        th.muted,
        1.0,
    )


def _methods_header(
    s: SVG, th: Theme, x: float, top: float, w: float, m: _Method
) -> None:
    """Panel, coloured title bar and designation, shared by cell and band."""
    s.rect(x, top, w, 38, m.color, m.color, rx=12, sw=0)
    s.rect(x, top + 19, w, 19, m.color, "none")  # square off header bottom
    s.text(x + w / 2, top + 27, m.name, 16, th.bg, bold=True)


def _methods_relation(s: SVG, th: Theme, cx: float, top: float, m: _Method) -> None:
    """Headline relation in its dashed box, then the limit that binds it."""
    s.rect(cx - 137, top, 274, 36, "none", m.color, rx=8, dash="5,4")
    s.text(cx, top + 23, m.relation, 10, th.fg, bold=True)
    s.text(cx, top + 54, m.limit, 11, th.muted)


def _methods_attributes(s: SVG, th: Theme, cx: float, top: float, m: _Method) -> None:
    """Environment, grade and measured quantity, one line each."""
    for yy, txt, cc, bold in (
        (top, m.environment, th.fg, False),
        (top + 22, m.grade, m.color, True),
        (top + 44, m.quantity, th.muted, False),
    ):
        s.text(cx, yy, txt, 11, cc, bold=bold)


def _methods_card(s: SVG, th: Theme, x: float, ctop: float, m: _Method) -> None:
    """One route in a column: picture above, attributes below, relation last."""
    cxc = x + _METHOD_CW / 2
    s.rect(x, ctop, _METHOD_CW, _METHOD_CH, th.panel, m.color, rx=12, sw=2.2)
    _methods_header(s, th, x, ctop, _METHOD_CW, m)
    _methods_pictogram(s, th, cxc, ctop + 92.0, m)
    _methods_attributes(s, th, cxc, ctop + 170.0, m)
    _methods_relation(s, th, cxc, ctop + _METHOD_CH - 66.0, m)


def _methods_band(
    s: SVG, th: Theme, x: float, top: float, w: float, m: _Method
) -> None:
    """The sole route of its row, laid across the three columns.

    The same five attributes, turned on their side: the picture takes the
    first third, the three attribute lines the second and the relation with
    its limit the third.
    """
    third = w / 3.0
    s.rect(x, top, w, _METHOD_BAND_H, th.panel, m.color, rx=12, sw=2.2)
    _methods_header(s, th, x, top, w, m)
    _methods_pictogram(s, th, x + third / 2 - 12.0, top + 87.0, m)
    _methods_attributes(s, th, x + w / 2, top + 73.0, m)
    _methods_relation(s, th, x + w - third / 2, top + 65.0, m)


def _methods_pictogram(s: SVG, th: Theme, cxc: float, py: float, m: _Method) -> None:
    """The mini-drawing of a route, centred on ``(cxc, py)``."""
    draw = {
        "hemi": _methods_pic_hemi,
        "anech": _methods_pic_anech,
        "reverb": _methods_pic_reverb,
        "accel": _methods_pic_accel,
        "points": _methods_pic_points,
        "scan": _methods_pic_scan,
    }[m.pictogram]
    draw(s, th, cxc, py, m.color)


def _methods_pic_hemi(s: SVG, th: Theme, cxc: float, py: float, col: str) -> None:
    """Hemispherical measurement surface over a reflecting plane."""
    r = 44.0
    s.ellipse(cxc, py + 22, r, r * 0.3, "none", th.muted, 1.2, dash="4,3")
    s.path(
        f"M {cxc - r} {py + 22} A {r} {r} 0 0 1 {cxc + r} {py + 22}",
        stroke=col,
        sw=2.2,
    )
    s.line(cxc - r, py + 22, cxc + r, py + 22, th.muted, 1.4)
    _box_solid(s, th, cxc, py + 22, 10, 8, 13, stroke=col)
    for ang in (35, 90, 145):
        a = math.radians(ang)
        s.circle(cxc + r * math.cos(a), py + 22 - r * math.sin(a), 4.0, th.secondary)


def _methods_pic_anech(s: SVG, th: Theme, cxc: float, py: float, col: str) -> None:
    """Wedge-lined room with the source on the reflecting plane."""
    s.rect(cxc - 56, py - 24, 112, 68, th.bg, th.fg, rx=4, sw=1.8)
    for k in range(6):
        wx = cxc - 56 + k * 19
        s.path(
            f"M {wx} {py - 24} L {wx + 19} {py - 24} L {wx + 9.5} {py - 12} Z",
            fill=th.muted,
            stroke="none",
        )
    s.line(cxc - 56, py + 44, cxc + 56, py + 44, th.fg, 2.0)
    _box_solid(s, th, cxc, py + 44, 10, 8, 13, stroke=col)
    for ang in (30, 90, 150):
        a = math.radians(ang)
        s.circle(cxc + 42 * math.cos(a), py + 44 - 42 * math.sin(a), 4.0, th.secondary)


def _methods_pic_reverb(s: SVG, th: Theme, cxc: float, py: float, col: str) -> None:
    """Reverberation room: a hard-walled box carrying a diffuse field."""
    s.rect(cxc - 50, py - 22, 100, 68, "none", col, rx=6, sw=2.2)
    for k in range(3):
        yy = py - 10 + k * 18
        s.path(
            f"M {cxc - 38} {yy} q 10 -10 20 0 q 10 10 20 0 q 10 -10 20 0",
            stroke=th.muted,
            sw=1.5,
        )
    s.circle(cxc - 34, py + 36, 5, th.secondary)


def _methods_pic_accel(s: SVG, th: Theme, cxc: float, py: float, col: str) -> None:
    """Radiating casing carrying an accelerometer, and no microphone."""
    s.rect(cxc - 50, py + 6, 100, 34, th.panel, col, rx=3, sw=2.0)
    _accel(s, cxc + 18, py + 6)
    _motion_arrows(s, cxc - 20, py - 4, 12, th.secondary)
    for r in (18, 30):
        s.path(
            f"M {cxc + 44 + r * 0.3:.1f} {py + 6 - r:.1f} "
            f"A {r} {r} 0 0 1 {cxc + 44 + r:.1f} {py + 6 - r * 0.3:.1f}",
            stroke=th.accent,
            sw=1.5,
        )


def _methods_pic_points(s: SVG, th: Theme, cxc: float, py: float, col: str) -> None:
    """Measurement surface cut into segments, one held position in each.

    Ten of them, which is the floor clause 8.2 puts under the position set,
    and the drawn contrast with the scanning cells beside it: dots at rest in
    their own segments rather than one path swept over the whole surface.
    """
    cols, rows = 5, 2
    left, top, w, h = cxc - 46, py - 26, 92.0, 52.0
    s.rect(left, top, w, 76, "none", col, rx=6, sw=2.0)
    for k in range(1, cols):
        s.line(left + k * w / cols, top, left + k * w / cols, top + h, th.muted, 1.0)
    # The mid rule divides the two rows; the one below closes the grid off from
    # the strip that carries the label, so no divider ends in mid-panel.
    for k in (1, 2):
        s.line(left, top + k * h / rows, left + w, top + k * h / rows, th.muted, 1.0)
    for j, i in itertools.product(range(cols), range(rows)):
        s.circle(
            left + (j + 0.5) * w / cols,
            top + (i + 0.5) * h / rows,
            2.8,
            th.accent,
        )
    s.text(cxc, py + 44, "$I⊥$", 14, col, bold=True)


def _methods_pic_scan(s: SVG, th: Theme, cxc: float, py: float, col: str) -> None:
    """Probe swept over the measurement surface along a serpentine path."""
    s.rect(cxc - 46, py - 26, 92, 76, "none", col, rx=6, sw=2.0)
    s.path(
        f"M {cxc - 36} {py - 14} L {cxc + 32} {py - 14} "
        f"L {cxc + 32} {py + 2} L {cxc - 36} {py + 2} "
        f"L {cxc - 36} {py + 18} L {cxc + 32} {py + 18}",
        stroke=th.accent,
        sw=1.7,
    )
    s.circle(cxc + 32, py + 18, 5, th.secondary)
    s.text(cxc, py + 44, "$I⊥$", 14, col, bold=True)


# ---------------------------------------------------------------------------
# d19 - ISO 3745 precision sound power (anechoic / hemi-anechoic room)
# ---------------------------------------------------------------------------


def _d_precision_anechoic(s: SVG, th: Theme) -> None:
    """ISO 3745 precision sound power on a (hemi-)spherical array."""
    x0, y0, x1, gy = 60.0, 70.0, 840.0, 470.0
    s.rect(x0, y0, x1 - x0, gy - y0, th.bg, th.fg, sw=3)

    # Anechoic wedges lining the ceiling and the two side walls.
    for wx in range(int(x0) + 4, int(x1) - 36, 40):
        s.path(
            f"M {wx} {y0} L {wx + 40} {y0} L {wx + 20} {y0 + 28} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=1.0,
        )
    for wy in range(int(y0) + 30, int(gy) - 36, 40):
        s.path(
            f"M {x0} {wy} L {x0} {wy + 40} L {x0 + 28} {wy + 20} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=1.0,
        )
        s.path(
            f"M {x1} {wy} L {x1} {wy + 40} L {x1 - 28} {wy + 20} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=1.0,
        )
    s.text(200, 120, "Anechoic wedges", 13, th.muted, anchor="start")

    # Reflecting floor (hemi-anechoic room).
    s.ground(gy, x0, x1)
    # Under the floor at the right, where the base circle of the hemisphere
    # has drawn in: above the floor at the left, the hemisphere's edge and
    # its base circle ran through the words.
    s.text(x1, gy + 26, "Reflecting plane (hemi-anechoic)", 12, th.muted, anchor="end")

    # Source (DUT) at the centre of the reflecting plane.
    cx, R = 450.0, 200.0
    _box_solid(s, th, cx, gy, 34, 26, 40)
    s.circle(cx, gy, 3.4, th.fg)
    # Over the source, inside the hemisphere: beside it, the base circle ran
    # through the words.
    s.text(cx, gy - 66, "Source (DUT)", 15, th.fg, bold=True)

    # Hemispherical measurement surface of radius r.
    s.ellipse(cx, gy, R, R * 0.16, "none", th.muted, 1.3, dash="5,4")
    s.path(f"M {cx - R} {gy} A {R} {R} 0 0 1 {cx + R} {gy}", stroke=th.primary, sw=2.4)

    # Ten normative microphone positions (ISO 3744/3745 Annex B), projected.
    b1 = [
        (0.16, -0.96, 0.22),
        (0.78, -0.60, 0.20),
        (0.78, 0.55, 0.31),
        (0.16, 0.90, 0.41),
        (-0.83, 0.32, 0.45),
        (-0.83, -0.40, 0.38),
        (-0.26, -0.65, 0.71),
        (0.74, -0.07, 0.67),
        (-0.26, 0.50, 0.83),
        (0.10, -0.10, 0.99),
    ]
    pts = [(cx + R * x + 46 * y, gy - 30 * y - R * z) for x, y, z in b1]
    r8 = pts[7]
    s.line(cx, gy, r8[0], r8[1], th.accent, 1.6, dash="6,4")
    s.text(
        (cx + r8[0]) / 2 + 8,
        (gy + r8[1]) / 2 + 2,
        "radius $r$",
        14,
        th.accent,
        anchor="start",
    )
    for px, py in pts:
        s.circle(px, py, 6.5, th.secondary)
        s.circle(px, py, 2.2, th.bg)
    # Ending short of the side wall's wedges, which it ran into.
    s.text(804, 300, "20 / 40 mic positions", 14, th.muted, anchor="end")

    # Governing relations.
    # Starting lower, clear of the base circle, which touched the first line.
    for y, txt, col, bold in (
        (520, "$L_W = ⟨L_p⟩ + 10 log_{10}(S/S_0) + C_1 + C_2 + C_3$", th.fg, True),
        (545, "$S = 2πr^2$ (hemi-anechoic) · $4πr^2$ (anechoic)", th.primary, True),
        (568, "$K_1$: per-position background correction", th.muted, False),
        (
            591,
            ("$C_1$, $C_2$, $C_3$: meteorological corrections ($p_s$, $θ$, $a(f)$)"),
            th.muted,
            False,
        ),
    ):
        s.text(450, y, txt, 16 if bold else 15, col, bold=bold)


# ---------------------------------------------------------------------------
# d20 - ISO 9614-3 precision sound intensity scanning
# ---------------------------------------------------------------------------


def _d_intensity_scan(s: SVG, th: Theme) -> None:
    """ISO 9614-3 precision sound power by intensity scanning."""
    gy, bx = 470.0, 360.0

    # Measurement surface (dashed wireframe) enclosing the source.
    _box_wire(s, th, bx, gy, 150, 120, 240, th.primary)
    _box_solid(s, th, bx, gy, 45, 34, 70)
    # Above the box's back edge, which ran through the word 12 px lower.
    s.text(bx, gy - 94, "Source", 15, th.fg, bold=True)
    # Above the wireframe's topmost edge rather than across its back
    # corners: the caption is 325 px in Spanish and 305 in English, and
    # both reach the box's slanted edges where it used to sit.
    s.text(bx, 150, "Measurement surface (segments $S_i$)", 15, th.primary, bold=True)

    # Segment grid on the front face (3 x 3 segments Sᵢ).
    fl, fr, ft, fb = bx - 150, bx + 150, gy - 240, gy
    for gx in (fl + 100, fl + 200):
        s.line(gx, ft, gx, fb, th.muted, 1.2, dash="4,4")
    for gyy in (ft + 80, ft + 160):
        s.line(fl, gyy, fr, gyy, th.muted, 1.2, dash="4,4")
    # Under the first scan run, which ran through the label on the row above.
    s.text(fl + 50, ft + 70, "$S_i$", 15, th.fg, bold=True)

    # Serpentine scan path across the segment-row centres.
    ys = (ft + 40, ft + 120, ft + 200)
    px = [
        (fl + 30, ys[0]),
        (fr - 30, ys[0]),
        (fr - 30, ys[1]),
        (fl + 30, ys[1]),
        (fl + 30, ys[2]),
        (fr - 30, ys[2]),
    ]
    for (ax, ay), (bxx, byy) in itertools.pairwise(px):
        s.line(ax, ay, bxx, byy, th.accent, 2.0, dash="2,3")
    s.arrow(px[-2][0] + 60, px[-1][1], px[-1][0], px[-1][1], th.accent, 2.0)
    # Beyond the surface's slanted lower edge, which ran through the words
    # when they started just past the front face.
    s.text(fr + 62, ys[2] + 6, "serpentine scan", 13, th.accent, anchor="start")

    # A p-p intensity probe on the scan path.
    ppx, ppy = bx, ys[1]
    s.line(ppx, ppy, ppx + 46, ppy - 26, th.fg, 2.2)
    s.circle(ppx, ppy - 6, 5, th.fg)
    s.circle(ppx, ppy + 6, 5, th.fg)
    # 12 px, between the segment line and the scan's vertical run, which the
    # Spanish reached at 13.
    s.text(ppx + 54, ppy - 30, "p-p probe", 12, th.fg, anchor="start")

    # Normal-intensity arrows exiting the left column of segments.
    for yy in ys:
        s.arrow(fl, yy, fl - 34, yy + 8, th.secondary, 2.0)
    s.text(
        fl - 40, ys[1] + 30, "$I_n$ (normal intensity)", 13, th.secondary, anchor="end"
    )

    # Governing relations.
    for y, txt, col, bold in (
        (505, "$P = Σ I_{n,i} · S_i$   (partial powers per segment)", th.fg, True),
        (533, "$L_W = 10 log_{10}(P/P_0)$,  $P_0$ = 1 pW", th.accent, True),
        (559, "Field indicators: $F_{pIn}$ , $F_T$ , $F_S$", th.primary, True),
        (
            583,
            "Five acceptance criteria (Annex C); band invalid if $P < 0$",
            th.muted,
            False,
        ),
    ):
        s.text(450, y, txt, 16 if bold else 15, col, bold=bold)


# ---------------------------------------------------------------------------
# ISO 3741 reverberation test room: the direct and the comparison methods
# ---------------------------------------------------------------------------

_REV_MICS = (
    (3.6, 1.4),
    (6.0, 1.8),
    (6.4, 4.2),
    (4.8, 5.0),
    (2.8, 4.6),
    (1.2, 3.6),
)  #: six positions, in metres on the room floor plan
_REV_SOURCE = (1.7, 1.7)  #: source under test, asymmetric and 1,7 m off both walls


def _d_reverberation_power(s: SVG, th: Theme) -> None:
    """ISO 3741 reverberation test room drawn in plan, both methods.

    Left, the direct method (Eq. 20): the source on the floor at least 1,5 m
    from every wall and six microphone positions carrying the three clause 8.3
    clearances. Right, the comparison method (Eq. 21): the reference sound
    source run at the *same* six positions with the source under test left in
    the room. The room is the guide's own example, V = 200 m3, S = 220 m2,
    T60 = 2,0 s, so d_min = 0,08 sqrt(200/2) = 0,8 m (1,6 m recommended below
    5 kHz) and half a wavelength at 100 Hz is 1,7 m.
    """
    sc, base = 45.0, 352.0  # 45 px per metre; y of the plan origin

    def mp(x0: float, x: float, y: float) -> tuple[float, float]:
        return x0 + x * sc, base - y * sc

    def shell(x0: float, header: str) -> None:
        s.text(x0 + 180, 58, header, 17, th.fg, bold=True)
        # Hard walls, deliberately not parallel (the room's own skew).
        s.path(
            f"M {x0 - 6} {base + 10} L {x0 + 364} {base + 2} "
            f"L {x0 + 372} {base - 276} L {x0 + 2} {base - 268} Z",
            fill=th.panel,
            stroke=th.fg,
            sw=3.0,
        )

    def mic(px: float, py: float, n: str = "") -> None:
        s.circle(px, py, 6.5, th.secondary)
        s.circle(px, py, 2.2, th.bg)
        if n:
            s.text(px, py - 12, n, 13, th.fg, bold=True)

    # ===== Left panel: the direct method =====
    ax = 60.0
    shell(ax, "Direct method (Eq. 20)")

    # One hung diffuser, well clear of every fixed position.
    dpx, dpy = mp(ax, 0.9, 5.2)
    s.path(
        f"M {dpx - 24} {dpy - 12} L {dpx + 18} {dpy - 22} "
        f"L {dpx + 24} {dpy + 10} L {dpx - 18} {dpy + 20} Z",
        fill=th.bg,
        stroke=th.muted,
        sw=1.6,
    )
    s.text(dpx, dpy + 42, "diffuser", 12, th.muted)

    # Alternative continuous traverse, drawn under the fixed positions.
    s.ellipse(ax + 176, base - 140, 118.0, 86.0, "none", th.accent, 1.6, dash="7,5")
    s.arrow(ax + 292, base - 152, ax + 290, base - 128, th.accent, 1.6)
    s.text(ax + 176, base - 136, "or one continuous traverse", 12, th.accent)

    sx, sy = mp(ax, *_REV_SOURCE)
    for i, (mx, my) in enumerate(_REV_MICS, start=1):
        mic(*mp(ax, mx, my), str(i) if i != 4 else "")
    # The three clearances, each measured on the position that binds it.
    m4x, m4y = mp(ax, *_REV_MICS[3])
    # Position 4 is numbered under its circle: above it, the 1,0 m line to
    # the wall ran through the number, and beside it the traverse does.
    s.text(m4x, m4y + 22, "4", 13, th.fg, bold=True)
    s.line(m4x, m4y, m4x, base - 272, th.muted, 1.0, dash="4,3")
    s.text(m4x + 8, (m4y + base - 272) / 2, "> 1,0 m", 13, th.fg, anchor="start")
    m1x, m1y = mp(ax, *_REV_MICS[0])
    s.line(sx, sy, m1x, m1y, th.primary, 1.4, dash="6,4")
    s.text((sx + m1x) / 2, sy - 10, "$> d_{min}$", 13, th.primary, bold=True)
    m5x, m5y = mp(ax, *_REV_MICS[4])
    m6x, m6y = mp(ax, *_REV_MICS[5])
    s.line(m5x, m5y, m6x, m6y, th.secondary, 1.4, dash="6,4")
    lx_, ly_ = (m5x + m6x) / 2, (m5y + m6y) / 2
    s.line(lx_, ly_, lx_, ly_ - 34, th.secondary, 1.0)
    s.text(lx_, ly_ - 40, "$≥ λ/2$", 13, th.secondary, bold=True)

    s.rect(sx - 16, sy - 13, 32, 26, th.fg, rx=3)
    s.text(sx - 22, sy + 34, "Source under test", 13, th.fg, bold=True, anchor="start")

    # ===== Right panel: the comparison method =====
    bx = 480.0
    shell(bx, "Comparison method (Eq. 21)")
    sx2, sy2 = mp(bx, *_REV_SOURCE)
    s.rect(sx2 - 16, sy2 - 13, 32, 26, th.panel, th.muted, rx=3, sw=1.6)
    s.text(
        sx2 - 22,
        sy2 + 34,
        "source under test, left in place",
        12,
        th.muted,
        anchor="start",
    )
    for mx, my in _REV_MICS:
        mic(*mp(bx, mx, my))
    # At x = 3,9 m rather than 4,2, so that its two-line name ends inside the
    # room: the Spanish ran into the right-hand wall.
    rx_, ry_ = mp(bx, 3.9, 3.2)
    s.circle(rx_, ry_, 15.0, th.accent)
    s.circle(rx_, ry_, 6.0, th.bg)
    s.text(
        rx_ + 24, ry_ - 6, "Reference sound", 13, th.accent, bold=True, anchor="start"
    )
    s.text(
        rx_ + 24,
        ry_ + 12,
        "source (ISO 6926)",
        13,
        th.accent,
        bold=True,
        anchor="start",
    )
    s.line(sx2, sy2, rx_, ry_, th.muted, 1.2, dash="5,4")
    s.text((sx2 + rx_) / 2 + 6, (sy2 + ry_) / 2 + 22, "≥ 1,5 m", 13, th.fg)

    # ===== Footer: the rules the drawing cannot dimension =====
    s.line(50, 386, 850, 386, th.muted, 1.0)
    for k, (txt, col, bold) in enumerate(
        (
            (
                (
                    "$d_{min} = D_1 √(V / T_{60})$ ,  $D_1$ = 0,08  "
                    "(0,16 recommended below 5 kHz)"
                ),
                th.primary,
                True,
            ),
            (
                (
                    "$V$ = 200 m³ · $T_{60}$ = 2,0 s  →  $d_{min}$ = 0,8 m,  or 1,6 m "
                    "at the recommended $D_1$"
                ),
                th.primary,
                True,
            ),
            (
                (
                    "six positions: > 1,0 m from every room surface · $> d_{min}$ from "
                    "the source · spacing $≥ λ/2$ (1,7 m at 100 Hz)"
                ),
                th.fg,
                False,
            ),
            (
                (
                    "traverse instead: $≥ d_{min}$ from the source · ≥ 1,0 m from any "
                    "surface · ≥ 0,5 m from a diffuser"
                ),
                th.fg,
                False,
            ),
            (
                (
                    "· not within 10° of a room surface · length $≥ 3λ$ or 10,3 m, "
                    "whichever is smaller"
                ),
                th.fg,
                False,
            ),
            (
                (
                    "comparison method: the same six positions, and Eq. 21 without "
                    "$A$, $V$, $S$, Waterhouse or $C_1$"
                ),
                th.accent,
                True,
            ),
            (
                (
                    "averaging ≥ 30 s to 160 Hz, ≥ 10 s from 200 Hz · background at "
                    "those positions, before or after"
                ),
                th.secondary,
                True,
            ),
            (
                (
                    "hard walls, $α < 0,06$ within one wavelength of the source · "
                    "$T_{60}$ per ISO 3382-2, first 10 dB or 15 dB only"
                ),
                th.muted,
                False,
            ),
        )
    ):
        s.text(58, 412 + k * 23, txt, 13, col, anchor="start", bold=bold)


# ---------------------------------------------------------------------------
# ISO 3747 comparison in situ: one room, two sources, the same microphones
# ---------------------------------------------------------------------------


def _d_sound_power_in_situ(s: SVG, th: Theme) -> None:
    """The ISO 3747 comparison in plan: one room, two sources, the same microphones.

    The machine is measured where it stands, and its reference box is the
    guide's compressor, 2,2 m by 1,4 m. Its directivity survey spans 4 dB,
    which makes it directional (7.2), so the reference sound source goes on
    the side it emits towards, 0,5 m clear of the box (7.3.2, B.2), and one
    location serves (7.3.1, 7.3.3). The four microphone positions stand at
    the guide's measurement distance of 1,5 m, at least 2 m apart and 0,5 m
    from every boundary (7.4.1), and they are zoned by Table 1: position 1
    is as far from the source as from the box within 10 % (+/-), position 2
    is nearer the source (-), position 3 nearer the machine (+), and
    position 4 is screened by the machine, which is where B.4 recommends a
    single position. The dotted ring is the directivity survey of 7.2, 1 m
    out. The right-hand column shows the three readings of 7.5 and the
    several locations of 7.3.3; the boxed lines are Eq. (11) and Eq. (A.1).
    """
    sc = 64.0  # px per metre of the plan
    cx, cy = 292.0, 334.0  # centre of the reference box

    def at(x: float, y: float) -> tuple[float, float]:
        return cx + x * sc, cy - y * sc

    s.text(450, 66, "One room, two sources, the same microphones", 17, th.fg, bold=True)

    # The corner of the hall: the walls the clearances are read against.
    wall_x = cx - 3.55 * sc
    wall_y = cy - 3.1 * sc
    s.line(wall_x, wall_y, 588, wall_y, th.fg, 3.0)
    s.line(wall_x, wall_y, wall_x, 492, th.fg, 3.0)
    x = wall_x + 18
    while x < 588:
        s.line(x, wall_y, x - 9, wall_y - 9, th.muted, 1.1)
        x += 22
    y = wall_y + 22
    while y < 492:
        s.line(wall_x, y, wall_x - 9, y - 9, th.muted, 1.1)
        y += 22
    s.text(586, wall_y - 16, "the workroom, as it stands", 12, th.muted, anchor="end")

    bx0, by0 = at(-1.1, 0.7)
    bw, bh = 2.2 * sc, 1.4 * sc
    rx, ry = at(0.0, 1.2)

    mics = ((1.23, 2.19), (-0.85, 2.20), (-2.6, 0.55), (0.6, -2.2))
    pts = [at(*m) for m in mics]
    (m1x, m1y), (m2x, m2y), (m3x, m3y), (m4x, m4y) = pts

    # The lines of sight, under the machine, so the screened one is cut by it.
    s.line(m4x, m4y, rx, ry, th.muted, 1.3, dash="5,4")
    # The sight line from position 1 to the box's corner breaks around the
    # label of the 0.5 m clearance, which it ran straight through.
    gap_top, gap_bot = (by0 + ry) / 2 - 6, (by0 + ry) / 2 + 10
    for y_from, y_to in ((m1y, gap_top), (gap_bot, by0)):
        t_from = (y_from - m1y) / (by0 - m1y)
        t_to = (y_to - m1y) / (by0 - m1y)
        s.line(
            m1x + (bx0 + bw - m1x) * t_from,
            y_from,
            m1x + (bx0 + bw - m1x) * t_to,
            y_to,
            th.muted,
            1.2,
            dash="4,4",
        )
    s.line(m1x, m1y, rx, ry, th.accent, 1.3, dash="5,4")
    s.line(m2x, m2y, rx, ry, th.accent, 1.3, dash="5,4")

    # The directivity survey of 7.2: the locus 1 m out from the box.
    s.rect(
        cx - 2.1 * sc,
        cy - 1.7 * sc,
        4.2 * sc,
        3.4 * sc,
        "none",
        th.muted,
        rx=1.0 * sc,
        sw=1.3,
        dash="2,5",
    )
    s.text(74, 152, "directivity survey first,", 12, th.muted, anchor="start")
    s.text(74, 170, "1 m out and 1.5 m up:", 12, th.muted, anchor="start")
    s.text(74, 188, "±4 dB, so directional", 12, th.muted, anchor="start")

    # The machine and its reference box.
    s.rect(bx0 + 6, by0 + 6, bw - 12, bh - 12, th.panel, th.fg, rx=4, sw=2.2)
    s.rect(bx0, by0, bw, bh, "none", th.fg, rx=2, sw=1.3, dash="6,4")
    s.text(cx, cy - 4, "the reference box", 12, th.muted)
    s.text(cx, cy + 14, "2.2 m × 1.4 m", 12, th.fg)

    # The side the machine emits towards, which is the side the source goes on.
    s.arrow(236, by0 + 6, 236, ry + 5, th.primary, 2.0)
    s.text(230, 250, "main emission", 11, th.primary)

    # The reference sound source, on that side and 0.5 m clear of the box.
    s.dim(rx + 20, by0, rx + 20, ry, "≥ 0.5 m", size=12, label_side="right")
    s.circle(rx, ry, 11, th.accent)
    s.circle(rx, ry, 4.5, th.bg)
    s.line(426, 240, rx + 11, ry - 3, th.accent, 1.2)
    s.text(430, 234, "reference source", 12, th.accent, bold=True, anchor="start")
    s.text(430, 252, "on the emitting side", 12, th.muted, anchor="start")

    # Position 1, the +/- zone of Table 1: as far from the box as from the source.
    s.text(
        586,
        158,
        "position 1: 1.5 m to the box, 1.6 m to the source,",
        12,
        th.fg,
        anchor="end",
    )
    s.text(
        586,
        176,
        "equal within 10 %: the +/− zone of Table 1",
        12,
        th.muted,
        anchor="end",
    )

    # The measurement distance, the 2 m spacing and the 0.5 m off the wall.
    s.dim(m4x, by0 + bh, m4x, m4y, "$d_m$ = 1.5 m", offset=-38, size=12)
    s.line(m1x, m1y, m2x, m2y, th.secondary, 1.2, dash="3,4")
    s.text((m1x + m2x) / 2, 214, "≥ 2 m", 12, th.secondary)
    s.dim(wall_x + 3, m3y, m3x, m3y, "≥ 0.5 m", offset=30, size=12)

    tags = ("1 +/−", "2 −", "3 +", "4 ++")
    for px, py in pts:
        s.circle(px, py, 7, th.secondary)
        s.circle(px, py, 2.4, th.bg)
    # Position 1 is where the two sight lines leave, so its tag goes beside
    # the dot rather than under it: centred below, both dashed lines run
    # through the glyphs.
    s.text(m1x + 14, 198, tags[0], 13, th.fg, bold=True, anchor="start")
    s.text(m2x, 216, tags[1], 13, th.fg, bold=True)
    s.text(m3x, 280, tags[2], 13, th.fg, bold=True)
    s.text(344, 479, tags[3], 13, th.fg, bold=True, anchor="start")

    s.text(
        320,
        498,
        "three or four positions, each in sight of every emitting area "
        "or screened from all",
        12,
        th.muted,
    )
    s.text(
        320,
        516,
        "Table 1: 1 equally far from both, 2 nearer the source, 3 nearer the machine",
        12,
        th.muted,
    )
    s.text(
        320,
        534,
        "4 is screened from the source, where Annex B recommends a single position",
        12,
        th.muted,
    )

    # What is read at every position (7.5).
    col, cw = 604.0, 276.0
    s.rect(col, 92, cw, 176, th.panel, th.fg, rx=6, sw=1.4)
    s.text(col + cw / 2, 116, "At every position, three readings", 13, th.fg, bold=True)
    ix = col + 18
    s.rect(ix - 8, 134, 16, 12, th.panel, th.fg, rx=2, sw=1.6)
    s.text(col + 34, 144, "the machine running", 12, th.fg, anchor="start")
    s.text(col + 34, 163, "$L′_{pi(ST)}$", 13, th.fg, anchor="start")
    s.circle(ix, 184, 7, th.accent)
    s.circle(ix, 184, 2.8, th.bg)
    s.text(col + 34, 188, "the reference source, 30 s", 12, th.fg, anchor="start")
    s.text(col + 34, 207, "$L′_{pi(RSS)}$", 13, th.accent, anchor="start")
    s.circle(ix, 228, 6.5, "none", th.muted, sw=1.8)
    s.text(
        col + 32, 232, "the background, just before or after", 12, th.fg, anchor="start"
    )
    s.text(col + cw / 2, 256, "same positions, same orientations", 11, th.muted)

    # Several locations of the reference source (7.3.3).
    s.rect(col, 282, cw, 264, th.panel, th.fg, rx=6, sw=1.4)
    s.text(col + cw / 2, 306, "When one location is not enough", 13, th.fg, bold=True)
    lw, lh = 196.0, 28.0
    lx0, ly0 = col + (cw - lw) / 2, 360.0
    s.rect(lx0, ly0, lw, lh, th.bg, th.fg, rx=2, sw=1.3, dash="6,4")
    step = lw / 4
    for j in range(4):
        xx = lx0 + step * (j + 0.5)
        for yy in (ly0 - 13, ly0 + lh + 13):
            s.circle(xx, yy, 6, th.accent)
            s.circle(xx, yy, 2.4, th.bg)
    s.dim(lx0 + step * 0.5, ly0 - 30, lx0 + step * 1.5, ly0 - 30, "$d_m$", size=12)
    s.dim(lx0, ly0 + lh + 46, lx0 + lw, ly0 + lh + 46, "$a$ > $d_m$", size=12)
    s.text(
        col + cw / 2, 454, "omnidirectional: along the sides, $d_m$ apart", 12, th.fg
    )
    s.text(col + cw / 2, 472, "distinct emitting areas: one per area", 12, th.fg)
    s.text(col + cw / 2, 490, "$a$ ≤ $d_m$, omnidirectional, none on top:", 12, th.fg)
    s.text(col + cw / 2, 508, "one location by each vertical side", 12, th.fg)
    s.text(col + cw / 2, 530, "here, one emitting side: one location", 11, th.muted)

    # The comparison, the check on the room, and what the drawing cannot dimension.
    s.rect(52, 560, 796, 80, th.panel, th.fg, rx=6, sw=1.6)
    s.text(450, 592, "$L_W = L_{W(RSS)} − L̄_{p(RSS)} + L̄_{p(ST)}$", 19, th.fg)
    s.text(836, 592, "Eq. 11", 12, th.muted, anchor="end")
    s.text(
        440,
        622,
        "$ΔL_{f}(r) = L_{p(RSS),r} − L_{W(RSS)} + 11 dB + 20 lg(r/r_0)$, "
        "at least 7 dB where the microphones stand",
        13,
        th.muted,
    )
    s.text(836, 622, "Annex A", 12, th.muted, anchor="end")
    s.text(
        450,
        668,
        "background at each position: over 15 dB no correction, 6 dB to "
        "15 dB Eq. 7, under 6 dB 1.3 dB at most and an upper bound",
        12,
        th.muted,
    )
    s.text(
        450,
        690,
        "class 1 instruments and filters, a class 1 calibrator on each "
        "microphone before and after each series, 0.5 dB apart at most",
        12,
        th.muted,
    )
    s.text(
        450,
        712,
        "grade 2 needs $ΔL_f$ ≥ 7 dB A-weighted at every position and a "
        "directivity range within ±7 dB; otherwise grade 3",
        12,
        th.muted,
    )


# ---------------------------------------------------------------------------
# ISO 3744 parallelepiped measurement surface and its microphone array
# ---------------------------------------------------------------------------


def _d_box_array(s: SVG, th: Theme) -> None:
    """ISO 3744 Annex C array on a box surface, in two orthographic views.

    The reference box is the guide's own 1,4 x 0,9 x 1,1 m machine and the
    measurement distance is d = 1 m, so a = 1,7 m, b = 1,45 m, c = 2,1 m and
    S = 4(ab + bc + ca) = 36,3 m2. The 3,4 m long faces exceed the clause C.1
    limit of 3d on a partial-area side, so they split in two and the array
    grows past the nine-position minimum.
    """
    sc = 70.0  # pixels per metre, shared by both views

    def key(px: float, py: float, normal: tuple[float, float] | None) -> None:
        if normal is not None:
            s.arrow(px, py, px + normal[0], py + normal[1], th.secondary, 1.4)
        s.circle(px, py, 6.0, th.secondary)
        s.circle(px, py, 2.0, th.bg)

    # ===== Left: top view =====
    tx, ty = 68.0, 92.0  # top-left corner of the measurement box
    tw, td = 3.4 * sc, 2.9 * sc  # 2a x 2b
    s.text(tx + tw / 2, 68, "Top view", 17, th.fg, bold=True)
    s.rect(tx, ty, tw, td, th.bg, th.accent, sw=2.2, dash="7,5")
    rw, rd = 1.4 * sc, 0.9 * sc  # reference box, in plan
    s.rect(tx + (tw - rw) / 2, ty + (td - rd) / 2, rw, rd, th.panel, th.fg, sw=2.0)
    label_y = ty + (td + rd) / 2 + 20
    s.text(tx + tw / 2, label_y, "reference box", 13, th.fg)
    # The partial-area split of the top face and its key positions. The split
    # breaks around the box's name, which it ran straight through.
    for y_from, y_to in ((ty, label_y - 14), (label_y + 7, ty + td)):
        s.line(tx + tw / 2, y_from, tx + tw / 2, y_to, th.muted, 1.4, dash="4,4")
    for px, py in (
        (tx, ty),
        (tx + tw / 2, ty),
        (tx + tw, ty),
        (tx, ty + td),
        (tx + tw / 2, ty + td),
        (tx + tw, ty + td),
        (tx + tw / 4, ty + td / 2),
        (tx + 3 * tw / 4, ty + td / 2),
    ):
        key(px, py, None)
    s.dim(tx + tw / 2, ty + td + 30, tx + tw, ty + td + 30, "$≤ 3d$", offset=0, size=14)
    s.dim(tx, ty + 34, tx + (tw - rw) / 2, ty + 34, "$d$ = 1 m", offset=0, size=14)
    s.text(
        tx + tw / 2,
        ty + td + 74,
        "$2a = l_1 + 2d$ = 3,4 m   ·   $2b$ = 2,9 m",
        14,
        th.accent,
    )

    # ===== Right: side view =====
    ex, gy = 512.0, 336.0  # left edge and the reflecting plane
    ew, eh = 3.4 * sc, 2.1 * sc  # 2a x c
    s.text(ex + ew / 2, 68, "Side view", 17, th.fg, bold=True)
    s.ground(gy, ex - 44, ex + ew + 44)
    s.text(ex - 40, gy + 30, "Reflecting plane", 13, th.muted, anchor="start")
    s.rect(ex, gy - eh, ew, eh, th.bg, th.accent, sw=2.2, dash="7,5")
    rwe, rhe = 1.4 * sc, 1.1 * sc  # reference box, in elevation
    s.rect(ex + (ew - rwe) / 2, gy - rhe, rwe, rhe, th.panel, th.fg, sw=2.0)
    s.text(ex + ew / 2, gy - rhe / 2 + 6, "source", 13, th.fg)
    s.line(ex + ew / 2, gy - eh, ex + ew / 2, gy - rhe, th.muted, 1.4, dash="4,4")
    ox, oy = ex + ew / 2, gy
    for px, py in (
        (ex + ew / 4, gy - eh / 2),
        (ex + 3 * ew / 4, gy - eh / 2),
        (ex + ew, gy - eh),
    ):
        key(px, py, None)
    # One position of each kind carries its reference direction: the top-face
    # centre normal to its face, the corner aimed at the origin O.
    key(ex + ew / 2, gy - eh, (0.0, 34.0))
    # 11 px in English, whose 12 px line ran into the surface's right edge.
    normal = "normal to the face"
    s.text(
        ex + ew / 2 + 10,
        gy - eh + 24,
        normal,
        s.fit_size([normal], [12, 11], 104),
        th.muted,
        anchor="start",
    )
    dx_, dy_ = ox - ex, oy - (gy - eh)
    n = (dx_**2 + dy_**2) ** 0.5
    key(ex, gy - eh, (44 * dx_ / n, 44 * dy_ / n))
    s.text(
        ex + 6, gy - eh - 12, "at a corner: aimed at $O$", 12, th.muted, anchor="start"
    )
    s.circle(ox, oy, 3.8, th.fg)
    s.text(ox + 10, oy - 8, "$O$", 14, th.fg, bold=True, anchor="start")
    s.dim(
        ex + ew,
        gy,
        ex + ew,
        gy - eh,
        "$c$ = 2,1 m",
        offset=36,
        size=14,
        label_side="right",
    )

    # ===== Footer =====
    s.line(50, 418, 850, 418, th.muted, 1.0)
    for k, (txt, col, bold) in enumerate(
        (
            (
                (
                    "$S = 4(a·b + b·c + c·a)$ = 36,3 m²   for $l_1 × l_2 × l_3$ = "
                    "1,4 × 0,9 × 1,1 m at $d$ = 1 m"
                ),
                th.accent,
                True,
            ),
            (
                (
                    "each of the five planes is split on its own into equal partial "
                    "areas of side $≤ 3d$ (clause C.1)"
                ),
                th.fg,
                False,
            ),
            (
                (
                    "key positions: the centre of every partial area, plus its corners "
                    "except those in the reflecting plane"
                ),
                th.fg,
                False,
            ),
            (
                (
                    "nine is the minimum, for one partial area per plane; here "
                    "$2a > 3d$, so the long faces split and the array grows"
                ),
                th.muted,
                False,
            ),
            (
                "the survey method (ISO 3746) keeps only the partial-area centres",
                th.muted,
                False,
            ),
        )
    ):
        s.text(60, 446 + k * 25, txt, 13, col, anchor="start", bold=bold)


# ---------------------------------------------------------------------------
# ISO/TS 7849-2 determination of the radiation factor
# ---------------------------------------------------------------------------


def _d_radiation_factor(s: SVG, th: Theme) -> None:
    """The second, paired measurement Part 2 needs: an ISO 9614 intensity scan
    over a surface offset from the casing, taken on the same machine in the
    same operating mode as the velocity survey that runs on the casing.
    """
    gy = 400.0
    s.ground(gy, 60.0, 560.0)

    bx, hw, dp, ht = 280.0, 140.0, 108.0, 150.0
    _box_solid(s, th, bx, gy, hw, dp, ht)
    fx0, fx1, fy = bx - hw, bx + hw, gy - ht
    dxo, dyo = dp * 0.72, dp * 0.55

    # The Table 1 grid of the velocity survey: 5 x 2 cells on the 4 m2 face.
    for i in range(1, 5):
        gx = fx0 + i * (2 * hw) / 5
        s.line(gx, fy, gx + dxo, fy - dyo, th.muted, 1.0)
    s.line(
        fx0 + dxo * 0.5, fy - dyo * 0.5, fx1 + dxo * 0.5, fy - dyo * 0.5, th.muted, 1.0
    )
    cells = []
    for r_ in (0.25, 0.75):
        for i in range(5):
            u = (i + 0.5) / 5
            cells.append((fx0 + u * 2 * hw + r_ * dxo, fy - r_ * dyo))
    for cxp, cyp in cells:
        s.circle(cxp, cyp, 4.0, th.secondary)
        s.circle(cxp, cyp, 1.5, th.bg)
    _accel(s, cells[5][0], cells[5][1] - 4)
    _motion_arrows(s, cells[5][0], cells[5][1] - 46, 14, th.secondary)
    s.text(bx - 40, 120, "$⟨v_j^2⟩$ on the casing", 15, th.secondary, bold=True)
    s.line(bx - 10, 130, bx - 44, 196, th.muted, 1.0)

    # The ISO 9614 measurement surface, offset 0,25 m from the casing.
    off = 44.0
    _box_wire(s, th, bx, gy, hw + off, dp + off * 0.8, ht + off, th.primary)
    s.dim(fx1, fy - 26, fx1 + off, fy - 26, "0,25 m", offset=-30, size=14)
    s.text(bx, 84, "ISO 9614 measurement surface", 15, th.primary, bold=True)

    # A serpentine sweep over the front segment of that surface, with a probe.
    sl, sr = fx0 - off + 22, fx1 + off - 22
    for k, yy in enumerate((fy + 26, fy + 76, fy + 126)):
        s.line(sl, yy, sr, yy, th.accent, 1.8, dash="2,3")
        if k < 2:
            xx = sr if k % 2 == 0 else sl
            s.line(xx, yy, xx, yy + 50, th.accent, 1.8, dash="2,3")
    s.arrow(sr - 60, fy + 126, sr, fy + 126, th.accent, 1.8)
    ppx, ppy = bx + 10, fy + 76
    s.line(ppx, ppy, ppx + 42, ppy - 24, th.fg, 2.2)
    s.circle(ppx, ppy - 6, 5, th.fg)
    s.circle(ppx, ppy + 6, 5, th.fg)
    s.text(ppx + 48, ppy - 28, "p-p probe", 13, th.fg, anchor="start")

    # Radiated power leaving the surface.
    for yy in (fy + 26, fy + 76, fy + 126):
        s.arrow(fx0 - off, yy, fx0 - off - 34, yy + 8, th.primary, 2.0)
    s.text(fx0 - off - 44, fy + 82, "$P_j$", 15, th.primary, bold=True, anchor="end")

    # Relation strip.
    lx = 590.0
    s.text(lx, 120, "Determining $ε_j$ (Part 2)", 16, th.fg, bold=True, anchor="start")
    for y, txt, col, bold in (
        (154, "$ε_j = P_j / (Z_{c,n} ⟨v_j^2⟩ S)$", th.primary, True),
        (186, "$P_j$ : ISO 9614 band power", th.muted, False),
        (212, "$⟨v_j^2⟩$ : surface-averaged", th.muted, False),
        (238, "normal velocity, same bands", th.muted, False),
    ):
        s.text(lx, y, txt, 14 if bold else 13, col, anchor="start", bold=bold)
    # 272 px wide: at 260 the longest Spanish line ran into the right edge.
    s.rect(lx - 10, 268, 272, 118, th.panel, th.secondary, rx=10, sw=2.0)
    for k, txt in enumerate(
        (
            "one machine, one run:",
            "the same operating mode,",
            "the same mounting, the same bands.",
            "$ε_j$ is a property of the structure",
            "and its excitation together.",
        )
    ):
        s.text(lx, 292 + k * 22, txt, 13, th.fg, anchor="start", bold=(k == 0))
    s.text(
        450,
        450,
        "determined once, then the velocity survey alone serves the rest of the family",
        15,
        th.fg,
        bold=True,
    )
    s.text(
        450,
        478,
        "mean segment-to-source distance ≥ 200 mm (ISO 9614-2, clause 8.2)",
        14,
        th.muted,
    )
    s.text(
        450,
        506,
        "Part 1 skips this measurement and sets $ε = 1$, which "
        "is why it returns an upper limit",
        14,
        th.muted,
    )


# ---------------------------------------------------------------------------
# The residual-intensity test and the before-use probe check
# ---------------------------------------------------------------------------


def _d_residual_intensity_check(s: SVG, th: Theme) -> None:
    """What δpI0 is measured with, and the two checks that precede a series.

    Panel 1 is the IEC 61043 clause 10.2 residual-intensity testing device;
    panel 2 the clause 14 b) pressure calibration of both channels; panel 3
    the ISO 9614-2 clause 6.2.2 probe-reversal test in situ.
    """
    tops, w = (30.0, 315.0, 600.0), 270.0
    heads = (
        "1 · Residual-intensity test",
        "2 · Pressure check",
        "3 · Probe reversal, in situ",
    )
    # One size for the row, chosen on its longest heading: "1 · Ensayo de
    # intensidad residual" is 281 px against the 233 of its English twin,
    # and a panel that holds one does not hold the other.
    hsize = s.fit_size(heads, (15, 13), w - 24, bold=True)
    for x0, head in zip(tops, heads, strict=True):
        s.rect(x0, 62, w, 300, th.panel, th.muted, rx=12, sw=1.6)
        s.text(x0 + w / 2, 90, head, hsize, th.fg, bold=True)

    def capsules(cx: float, cy: float, col: str) -> None:
        for dx in (-30.0, 30.0):
            s.rect(cx + dx - 13, cy - 24, 26, 48, th.panel, col, rx=6, sw=2.0)
            s.rect(cx + dx - 8, cy - 30, 16, 8, th.fg, rx=2)
        s.rect(cx - 12, cy - 5, 24, 10, th.panel, th.muted, rx=3, sw=1.2)

    # --- 1: the coupler, both capsules in one identical pressure field ------
    x0 = tops[0]
    cx, cy = x0 + w / 2, 186.0
    s.rect(cx - 78, cy - 62, 156, 124, th.bg, th.fg, rx=10, sw=2.4)
    for k in range(3):
        s.path(
            f"M {cx - 60} {cy - 40 + k * 34} q 20 -14 40 0 q 20 14 40 0",
            stroke=th.primary,
            sw=1.6,
        )
    capsules(cx, cy, th.secondary)
    s.text(cx, cy + 84, "pink or white noise, 45 Hz to 7,1 kHz", 12, th.muted)
    s.text(cx, cy + 106, "both capsules within ± 0,1 dB", 12, th.muted)
    s.text(cx, cy + 134, "$δ_{pI0} = L_p − L_{I0}$", 15, th.primary, bold=True)

    # --- 2: the sound calibrator on one capsule at a time -------------------
    x1 = tops[1]
    cx, cy = x1 + w / 2, 186.0
    s.rect(cx - 74, cy - 40, 62, 80, th.bg, th.accent, rx=8, sw=2.2)
    s.text(cx - 43, cy + 4, "94,0", 13, th.accent, bold=True, mono=True)
    s.text(cx - 43, cy + 22, "dB", 12, th.accent, mono=True)
    s.rect(cx - 12, cy - 14, 22, 28, th.panel, th.secondary, rx=5, sw=2.0)
    s.rect(cx + 10, cy - 8, 44, 16, th.panel, th.muted, rx=4, sw=1.4)
    s.rect(cx + 54, cy - 14, 22, 28, th.panel, th.secondary, rx=5, sw=2.0)
    s.text(cx, cy + 66, "IEC 60942 calibrator, class 0 or 1", 12, th.muted)
    s.text(cx, cy + 88, "on each microphone in turn", 12, th.muted)
    s.text(cx, cy + 120, "adjust to ± 0,1 dB", 15, th.accent, bold=True)
    s.text(cx, cy + 144, "in both channels", 13, th.muted)

    # --- 3: the probe reversal on the measurement surface -------------------
    x2 = tops[2]
    cx, cy = x2 + w / 2, 196.0
    sxl = cx - 100
    s.line(sxl, cy - 78, sxl, cy + 78, th.fg, 2.6)
    for k in range(7):
        s.line(sxl, cy - 76 + k * 24, sxl - 9, cy - 67 + k * 24, th.muted, 1.1)
    s.text(cx, cy + 100, "measurement surface", 12, th.muted)
    s.arrow(sxl + 12, cy - 74, sxl + 92, cy - 74, th.muted, 2.0)
    s.text(sxl + 52, cy - 82, "energy leaving the source", 11, th.muted)
    for yy, col, lab, sgn in (
        (cy - 36, th.secondary, "$+ I_n$", 1.0),
        (cy + 36, th.primary, "$− I_n$", -1.0),
    ):
        s.line(cx - 34, yy, cx + 34, yy, th.fg, 2.0)
        s.circle(cx - 14, yy, 5.5, th.fg)
        s.circle(cx + 14, yy, 5.5, th.fg)
        s.arrow(cx, yy - 20, cx + sgn * 38, yy - 20, col, 2.0)
        s.text(cx + 50, yy + 5, lab, 13, col, bold=True, anchor="start")
    _rot_arrow(s, cx, cy, 46.0, 250.0, 470.0, th.muted, 1.8)
    s.text(cx - 52, cy + 5, "180°", 13, th.muted, anchor="end")
    s.text(cx, cy + 124, "acoustic centre held in place", 12, th.muted)

    # --- verdict strip ------------------------------------------------------
    s.rect(30, 390, 840, 62, th.panel, th.secondary, rx=10, sw=2.0)
    s.text(
        450,
        416,
        "accepted when the two readings have opposite signs and "
        "differ by less than 1,5 dB",
        15,
        th.fg,
        bold=True,
    )
    s.text(
        450,
        440,
        "in the band of maximum level (ISO 9614-2, clause 6.2.2)",
        13,
        th.muted,
    )
    for k, txt in enumerate(
        (
            "same signs → the two channels are swapped, or one is inverted",
            (
                "more than 1,5 dB apart → the probe disturbs its own field, or the "
                "channels are not matched"
            ),
            (
                "$δ_{pI0}$ belongs to the probe, its spacer and the analyser "
                "together, not to the microphones"
            ),
        )
    ):
        s.text(44, 482 + k * 24, txt, 13, th.muted, anchor="start")


def _d_loudspeaker_freefield(s: SVG, th: Theme) -> None:
    """IEC 60268-5 loudspeaker sensitivity on the reference axis (free field)."""
    x0, y0, x1, gy = 60.0, 70.0, 840.0, 470.0
    s.rect(x0, y0, x1 - x0, gy - y0, th.bg, th.fg, sw=3)

    # Anechoic wedges on all four boundaries (full free field: no floor).
    for wx in range(int(x0) + 4, int(x1) - 36, 40):
        s.path(
            f"M {wx} {y0} L {wx + 40} {y0} L {wx + 20} {y0 + 28} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=1.0,
        )
        s.path(
            f"M {wx} {gy} L {wx + 40} {gy} L {wx + 20} {gy - 28} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=1.0,
        )
    for wy in range(int(y0) + 30, int(gy) - 64, 40):
        s.path(
            f"M {x0} {wy} L {x0} {wy + 40} L {x0 + 28} {wy + 20} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=1.0,
        )
        s.path(
            f"M {x1} {wy} L {x1} {wy + 40} L {x1 - 28} {wy + 20} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=1.0,
        )
    s.text(210, 122, "Anechoic wedges", 13, th.muted, anchor="start")

    # Loudspeaker cabinet on a stand, reference point on the front baffle.
    ax_y, fx = 275.0, 250.0
    s.line(219, ax_y + 70, 219, 462, th.fg, 2.2)
    s.line(199, 462, 239, 462, th.fg, 2.2)
    s.rect(fx - 62, ax_y - 70, 62, 140, th.panel, th.primary, rx=6, sw=2)
    s.circle(fx - 18, ax_y, 14, th.primary)
    s.circle(fx - 18, ax_y, 5.5, th.bg)
    s.text(219, ax_y - 84, "Loudspeaker", 15, th.fg, bold=True)
    for r in (26, 44, 62):
        s.path(
            f"M {fx + r * 0.34:.1f} {ax_y - r * 0.94:.1f} "
            f"A {r} {r} 0 0 1 {fx + r * 0.34:.1f} {ax_y + r * 0.94:.1f}",
            stroke=th.accent,
            sw=1.5,
        )

    # Reference axis through the reference point, out to the right.
    s.circle(fx, ax_y, 3.4, th.fg)
    s.line(fx, ax_y, 782, ax_y, th.muted, 1.4, dash="7,5")
    s.arrow(760, ax_y, 792, ax_y, th.muted, 1.4)
    s.text(724, ax_y + 24, "Reference axis", 13, th.muted)

    # Measurement microphone on axis, capsule facing the loudspeaker.
    mx = 620.0
    s.line(mx + 23, ax_y + 6, mx + 23, 462, th.fg, 2.2)
    s.line(mx + 7, 462, mx + 39, 462, th.fg, 2.2)
    s.rect(mx, ax_y - 6, 46, 12, th.primary, rx=4)
    s.rect(mx - 12, ax_y - 4, 12, 8, th.fg, rx=2.5)
    s.text(mx + 24, ax_y - 24, "Measurement microphone", 15, th.fg, bold=True)

    # Reference distance, drafting style, between baffle and capsule tip.
    s.dim(fx, ax_y, mx - 12, ax_y, "$r$ = 1 m", offset=92)

    # Drive: amplifier delivering 1 W into the rated impedance.
    s.rect(85, 383, 140, 54, th.panel, th.primary, rx=8, sw=2)
    s.text(155, 405, "Amplifier", 15, th.fg, bold=True)
    s.text(155, 427, "2.83 V (8 Ω)", 13, th.secondary, mono=True)
    s.line(155, 383, 155, 345, th.fg, 1.6)
    s.line(155, 345, fx - 62, 345, th.fg, 1.6)

    # Governing relations. The Up, Lp(1 m) and LM relations stay plain: each
    # carries a unit as a factor or an argument (1 W, 1 m, 1 V/Pa), and the
    # composer has no upright run for a single-letter unit inside math.
    for y, txt, col, bold in (
        (
            508,
            (
                "Characteristic sensitivity: $L_p$ at 1 m for 1 W into the "
                "rated impedance"
            ),
            th.fg,
            True,
        ),
        (
            534,
            "Up = √(R · 1 W): 2.83 V is 1 W into 8 Ω but 2 W into 4 Ω (+3 dB)",
            th.secondary,
            True,
        ),
        (
            559,
            "Lp(1 m) = Lp(r) + 20 log10(r / 1 m)   (far field, inverse-distance law)",
            th.primary,
            True,
        ),
        (
            583,
            "Microphone (IEC 60268-4): M in mV/Pa, or LM = 20 log10(M / 1 V/Pa) dB",
            th.muted,
            False,
        ),
    ):
        s.text(450, y, txt, 16 if bold else 15, col, bold=bold)


# ---------------------------------------------------------------------------
# Sound power from surface vibration (ISO/TS 7849)
# ---------------------------------------------------------------------------


def _d_vibration_sound_power(s: SVG, th: Theme) -> None:
    """ISO/TS 7849 surface-velocity method: the machine's radiating surface
    divided into N equal cells, one accelerometer per cell centre, and the
    survey sound power from the mean velocity level over the area S.
    """
    gy = 470.0
    s.ground(gy, 50.0, 560.0)

    # Machine body with the vibrating measurement surface on top.
    bx, hw, dp, ht = 270.0, 140.0, 115.0, 170.0
    _box_solid(s, th, bx, gy, hw, dp, ht)
    fx0, fx1 = bx - hw, bx + hw  # top-face front edge
    fy = gy - ht
    dxo, dyo = dp * 0.72, dp * 0.55

    # Measurement grid: 5 x 2 cells on the top face (the Table 1 initial
    # count N = 10 for a 1-10 m2 surface), a dot per cell centre.
    for i in range(1, 5):
        gx = fx0 + i * (2 * hw) / 5
        s.line(gx, fy, gx + dxo, fy - dyo, th.muted, 1.0)
    for f_row in (0.5,):
        s.line(
            fx0 + dxo * f_row,
            fy - dyo * f_row,
            fx1 + dxo * f_row,
            fy - dyo * f_row,
            th.muted,
            1.0,
        )
    pts = []
    for r_ in (0.25, 0.75):
        for i in range(5):
            u = (i + 0.5) / 5
            pts.append((fx0 + u * 2 * hw + r_ * dxo, fy - r_ * dyo))
    for px_, py_ in pts:
        s.circle(px_, py_, 4, th.secondary)
        s.circle(px_, py_, 1.5, th.bg)
    # One accelerometer drawn explicitly, with its vibratory motion.
    _accel(s, pts[5][0], pts[5][1] - 4)
    _motion_arrows(s, pts[5][0], pts[5][1] - 46, 16, th.secondary)
    s.text(250, 150, "Vibrating measurement surface $S$", 16, th.fg, bold=True)
    s.line(310, 160, 340, 228, th.muted, 1.0)

    # Radiated sound from the surface.
    for r in (36, 60, 84):
        s.path(
            f"M {475 + r * 0.30:.1f} {370 - r:.1f} "
            f"A {r} {r} 0 0 1 {475 + r:.1f} {370 - r * 0.30:.1f}",
            stroke=th.accent,
            sw=1.6,
        )
    s.text(672, 432, "radiated airborne sound", 14, th.accent)
    s.line(618, 424, 570, 372, th.muted, 1.0)

    # Dimensions of the surface (2.5 m x 1.6 m -> S = 4 m2).
    s.dim(fx0, gy, fx1, gy, "2.5 m", offset=32, size=15)
    s.arrow(fx1 + 20, gy + 18, fx1 + dxo + 14, gy - dyo + 18, th.muted, 1.2)
    s.arrow(fx1 + dxo + 14, gy - dyo + 18, fx1 + 20, gy + 18, th.muted, 1.2)
    s.text(fx1 + dxo - 4, gy - dyo + 46, "1.6 m", 15, th.fg, anchor="start")
    s.text(bx, 540, "Machine under test", 15, th.fg, bold=True)

    # Number of measurement positions and the survey relation.
    lx = 575.0
    s.text(
        lx, 110, "Initial number of positions $N$", 16, th.fg, bold=True, anchor="start"
    )
    for y, txt in (
        (140, "$S$ < 1 m²   →   5"),
        (166, "1 m² ≤ $S$ ≤ 10 m²  →  10"),
        (192, "$S$ > 10 m²  →  $S / S_0$"),
    ):
        s.text(lx, y, txt, 14, th.fg, anchor="start")
    s.text(
        lx,
        220,
        "one accelerometer per cell of area $S/N$",
        13,
        th.muted,
        anchor="start",
    )
    s.text(lx, 284, "Survey sound power", 16, th.fg, bold=True, anchor="start")
    # Two logarithms in one line: the smaller face keeps it inside the column.
    s.text(
        lx,
        314,
        "$L_{WA} = L_{vA} + 10 log_{10}(S/S_0) + 10 log_{10} ε$",
        11,
        th.primary,
        anchor="start",
        bold=True,
    )
    s.text(
        lx,
        342,
        "$ε = 1$ assumed → upper limit $L_{WA,max}$",
        13,
        th.muted,
        anchor="start",
    )
    s.text(
        lx,
        368,
        "normal surface velocity, A-weighted r.m.s.",
        13,
        th.muted,
        anchor="start",
    )


# ---------------------------------------------------------------------------
# Swept-sine distortion: deconvolution and the harmonic pre-arrivals
# ---------------------------------------------------------------------------


def _d_swept_sine(s: SVG, th: Theme) -> None:
    """Farina's exponential-sweep method: sweep through the weakly nonlinear
    DUT, deconvolve with the inverse filter, and the order-n distortion
    products compress into impulse responses L*ln(n) ahead of the linear
    one (L = 0.701 s for 20 Hz to 6 kHz in 4 s; 260 px per second).
    """

    def box(x0: float, x1: float, y0: float, l1: str, l2: str, color: str) -> None:
        s.rect(x0, y0, x1 - x0, 76.0, th.panel, color, rx=10, sw=2)
        s.text((x0 + x1) / 2, y0 + 32.0, l1, 15, th.fg, bold=True)
        # The second line drops a size where the box would not hold it.
        size = s.fit_size([l2], [12, 11, 10], x1 - x0 - 20)
        s.text((x0 + x1) / 2, y0 + 56.0, l2, size, th.muted)

    # The middle box 280 px wide: at 220 the Spanish of its second line ran
    # out through both sides.
    box(40, 280, 64, "Exponential sweep $x(t)$", "20 Hz → 6 kHz in $T$ = 4 s", th.fg)
    box(
        310,
        590,
        64,
        "Device under test",
        "weakly nonlinear: gain + harmonics",
        th.primary,
    )
    box(620, 860, 64, "Recording $y(t)$", "sweep + distortion products", th.fg)
    s.arrow(280.0, 102.0, 306.0, 102.0, th.fg, 2.0)
    s.arrow(590.0, 102.0, 616.0, 102.0, th.fg, 2.0)
    box(
        520,
        840,
        180,
        "Deconvolve with the inverse filter",
        "time-reversed sweep with a +6 dB/octave tilt",
        th.secondary,
    )
    s.arrow(740.0, 140.0, 740.0, 176.0, th.fg, 2.0)
    s.arrow(660.0, 256.0, 648.0, 298.0, th.fg, 2.0)

    # --- impulse-response timeline -----------------------------------------
    ax_y = 430.0
    s.line(80.0, ax_y, 830.0, ax_y, th.fg, 1.8)
    s.arrow(830.0, ax_y, 850.0, ax_y, th.fg, 1.8)
    s.text(845.0, 452.0, "time", 12, th.muted, anchor="end")
    s.line(640.0, ax_y - 5, 640.0, ax_y + 6, th.fg, 1.8)

    def ir(x0: float, amp: float, color: str) -> None:
        d = (
            f"M {x0:.0f} {ax_y:.0f} L {x0:.0f} {ax_y - amp:.0f} "
            f"L {x0 + 4:.0f} {ax_y:.0f} L {x0 + 10:.0f} {ax_y - amp * 0.45:.0f} "
            f"L {x0 + 16:.0f} {ax_y:.0f} L {x0 + 22:.0f} {ax_y - amp * 0.2:.0f} "
            f"L {x0 + 28:.0f} {ax_y:.0f} L {x0 + 36:.0f} {ax_y - amp * 0.08:.0f} "
            f"L {x0 + 44:.0f} {ax_y:.0f}"
        )
        s.path(d, stroke=color, sw=2.0)

    ir(640.0, 94.0, th.primary)
    ir(514.0, 60.0, th.secondary)
    ir(440.0, 38.0, th.accent)
    ir(387.0, 22.0, th.muted)
    s.rect(630, 322, 66, 108, "none", th.primary, rx=8, sw=1.2, dash="5,4")
    s.rect(505, 358, 62, 72, "none", th.secondary, rx=8, sw=1.2, dash="5,4")
    s.rect(432, 382, 60, 48, "none", th.accent, rx=8, sw=1.2, dash="5,4")
    s.rect(380, 402, 54, 28, "none", th.muted, rx=6, sw=1.0, dash="5,4")
    s.text(663.0, 310.0, "$h_1$ (linear), $t = 0$", 13, th.primary, bold=True)
    s.text(536.0, 346.0, "$h_2$", 13, th.secondary, bold=True)
    s.text(462.0, 370.0, "$h_3$", 13, th.accent, bold=True)
    s.text(398.0, 396.0, "$h_4$", 11, th.muted)
    s.text(210.0, 344.0, "harmonic orders arrive early,", 13, th.muted, italic=True)
    s.text(210.0, 366.0, "each in its own window", 13, th.muted, italic=True)

    # Pre-arrival advances (260 px per second).
    s.dim(514.0, ax_y, 640.0, ax_y, "$L·ln 2$ = 0.49 s", offset=42, size=13)
    s.dim(440.0, ax_y, 640.0, ax_y, "$L·ln 3$ = 0.77 s", offset=80, size=13)

    s.text(
        450.0,
        562.0,
        "$L = T / ln(f_2/f_1)$ = 0.70 s; the order-$n$ products compress "
        "$L·ln n$ ahead of the linear response",
        15,
        th.fg,
        bold=True,
    )
    s.text(
        450.0,
        590.0,
        "window each arrival  →  $H_{1}(f)$, $H_{2}(f)$, $H_{3}(f)$, …  →  "
        "$THD(f) = √( Σ |H_{n}(n f)|^2 ) / |H_{1}(f)|$",
        14,
        th.primary,
    )


# ---------------------------------------------------------------------------
# Programme loudness (ITU-R BS.1770 / EBU R 128)
# ---------------------------------------------------------------------------


def _d_program_loudness(s: SVG, th: Theme) -> None:
    """K-weighting, 400 ms blocks and the two gates into the integrated
    loudness of the guide's example (I = -23.1 LUFS, relative threshold
    -39.0 LUFS), with the LRA and true-peak branches beside the chain.
    """
    cx, bw = 450.0, 560.0
    x0 = cx - bw / 2

    def step(y: float, l1: str, l2: str, color: str) -> None:
        s.rect(x0, y, bw, 58, th.panel, color, rx=10, sw=2)
        s.text(cx, y + 25, l1, 13, th.fg, bold=True)
        s.text(cx, y + 45, l2, 10, th.muted)

    step(
        52,
        "Programme $x$, channel weights $G_i$: 1.0 front, 1.41 surround",
        "anchor: a 0 dB FS 997 Hz sine on one front channel reads −3.01 LKFS",
        th.fg,
    )
    step(
        138,
        "K-weighting: +4 dB spherical-head shelf + RLB high-pass",
        "$L_K = −0.691 + 10·log_{10} Σ G_i·z_i$;  LKFS ≡ LUFS, 1 LU = 1 dB",
        th.primary,
    )
    step(
        224,
        "Mean square in 400 ms blocks, 75 % overlap",
        "absolute gate: blocks below −70 LUFS are dropped",
        th.primary,
    )
    step(
        310,
        "Relative gate: −10 LU below the survivors",
        "example: 10 s at −23 dBFS + 30 s of quiet → threshold −39.0 LUFS",
        th.primary,
    )
    s.rect(x0, 396, bw, 60, "none", th.accent, rx=10, sw=2.4)
    s.text(
        cx,
        421,
        "Integrated loudness $I$ = −23.1 LUFS: the tail is gated out",
        14,
        th.fg,
        bold=True,
    )
    s.text(
        cx,
        443,
        "EBU R 128 target −23.0 LUFS; tolerance ±0.2 LU in QC, ±1.0 LU live",
        10,
        th.muted,
    )
    for y0, y1 in ((110, 134), (196, 220), (282, 306), (368, 392)):
        s.arrow(cx, y0, cx, y1, th.fg, 1.8)

    # Side rails: LRA taps the K-weighted signal, true peak the raw one.
    s.line(170, 167, 120, 167, th.muted, 1.4)
    s.line(120, 167, 120, 484, th.muted, 1.4)
    s.arrow(120, 484, 120, 488, th.muted, 1.4)
    s.text(120, 157, "K-weighted", 10, th.muted)
    s.line(730, 81, 780, 81, th.muted, 1.4)
    s.line(780, 81, 780, 484, th.muted, 1.4)
    s.arrow(780, 484, 780, 488, th.muted, 1.4)
    s.text(780, 71, "raw signal", 10, th.muted)

    s.rect(70, 492, 360, 82, th.panel, th.secondary, rx=10, sw=2)
    s.text(250, 517, "Loudness range $LRA = P_{95} − P_{10}$", 12, th.fg, bold=True)
    s.text(250, 538, "short-term 3 s windows, deeper −20 LU gate", 10, th.muted)
    s.text(
        250, 558, "10.0 LU on the Tech 3342 two-step case", 10, th.secondary, bold=True
    )
    s.rect(470, 492, 360, 82, th.panel, th.secondary, rx=10, sw=2)
    s.text(650, 517, "True peak: 4× oversampling, in dBTP", 12, th.fg, bold=True)
    s.text(
        650,
        538,
        "the $f_s/4$ tone: sample peak −3.01 dB, true peak +0.12 dBTP",
        10,
        th.muted,
    )
    s.text(650, 558, "R 128 production ceiling −1 dBTP", 10, th.secondary, bold=True)

    s.text(
        450,
        618,
        "the gates keep quiet passages from dragging the foreground down",
        12,
        th.fg,
    )
    s.text(
        450,
        642,
        "ungated, the same 40 s example would read near −29 LUFS",
        11,
        th.muted,
    )


# ---------------------------------------------------------------------------
# The quasi-peak meter and the tests clause 2 puts it through (ITU-R BS.468-4)
# ---------------------------------------------------------------------------


def _qp_sine(
    s: SVG,
    x0: float,
    x1: float,
    cy: float,
    amp: float,
    period: float,
    colour: str,
    sw: float = 1.6,
) -> None:
    """A sine that starts at a zero crossing, as every clause 2 burst does."""
    n = max(2, int((x1 - x0) * 2))
    points = []
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        y = cy - amp * math.sin(2.0 * math.pi * (x - x0) / period)
        points.append(f"{x:.1f} {y:.1f}")
    s.path("M " + " L ".join(points), stroke=colour, sw=sw)


#: The 2.6 calibration and one row per Method of measurement of ITU-R
#: BS.468-4 clause 2, in the order a bench runs them (the calibration first,
#: because 2.5 is read against its 0 dB): the label, whether the test goes
#: through the weighting network (every test but 2.4, clause 2 preamble), and
#: three lines of what is applied and what it must read.
_QP_TEST_ROWS: tuple[tuple[str, bool, tuple[str, str, str]], ...] = (
    (
        "2.6 Calibration",
        True,
        (
            "steady 1 kHz sine at 0.775 V r.m.s., distortion under 1 %",
            "must read 0.775 V, that is 0 dB",
            "0 dB placed 2 dB to 10 dB below full scale, on a 20 dB scale or more",
        ),
    ),
    (
        "2.1 Single bursts",
        True,
        (
            "single 5 kHz bursts from a zero crossing, 1 ms to 200 ms",
            "whole periods; Table 2: 5 ms reads 34 % to 46 % of the steady tone",
            "attenuators fixed, then reset for each duration to hold 80 %",
        ),
    ),
    (
        "2.2 Repetitive bursts",
        True,
        (
            "5 ms bursts of 5 kHz at 2, 10 and 100 per second",
            "Table 3: 43 % to 53 %, 72 % to 82 %, 94 % to 100 %",
            "attenuators fixed, and within tolerance on every range",
        ),
    ),
    (
        "2.3 Overload",
        True,
        (
            "isolated 0.6 ms bursts of 5 kHz, reading full scale",
            "on the most sensitive range, then 20 dB down in steps",
            "readings follow the steps within ±1 dB overall, on every range",
        ),
    ),
    (
        "2.4 Reversibility",
        False,
        (
            "1 ms rectangular d.c. pulses, 100 per second or fewer",
            "reading 80 % of full scale, then with the polarity reversed",
            "the two readings differ by no more than 0.5 dB",
        ),
    ),
    (
        "2.5 Overswing",
        True,
        (
            "1 kHz tone applied suddenly at the level that reads 0 dB",
            "momentary excess reading under 0.3 dB",
            "",
        ),
    ),
)


def _qp_stimulus(s: SVG, th: Theme, row: int, mid: float, colour: str) -> None:
    """Sketch the stimulus of one row between x = 244 and x = 424.

    The carrier periods keep their ratio, 22.5 px for 1 kHz against 4.5 px
    for 5 kHz, so a burst reads five times denser than the calibration tone,
    and every burst runs a whole number of periods from a zero crossing, as
    clause 2 asks. Burst lengths are not on that scale, bar the 0.6 ms of
    2.3, which is its three periods: 5 ms would be 112 px, so 2.1 and 2.2
    keep only the order, the 2.2 bursts drawn longer than the 2.3 ones.
    """
    xb0, xb1 = 244.0, 424.0
    if row == 0:  # 2.6: the steady 1 kHz sine
        _qp_sine(s, xb0, xb1, mid, 13, 22.5, colour)
    elif row == 1:  # 2.1: separate single bursts of growing duration
        for sx, blen in ((xb0, 9.0), (xb0 + 62, 22.5), (xb0 + 124, 40.5)):
            s.line(sx, mid, sx + 12, mid, colour, 1.4)
            _qp_sine(s, sx + 12, sx + 12 + blen, mid, 13, 4.5, colour, 1.3)
            s.line(sx + 12 + blen, mid, sx + 56, mid, colour, 1.4)
    elif row == 2:  # 2.2: a train of the longer bursts
        s.line(xb0, mid, xb1, mid, colour, 1.4)
        for k in range(5):
            bx = xb0 + 6 + 36 * k
            _qp_sine(s, bx, bx + 18, mid, 13, 4.5, colour, 1.3)
    elif row == 3:  # 2.3: isolated three-period bursts stepped down
        s.line(xb0, mid, xb1, mid, colour, 1.4)
        for k, amp in enumerate((14.0, 11.0, 8.5, 6.0, 4.0)):
            bx = xb0 + 12 + 36 * k
            _qp_sine(s, bx, bx + 13.5, mid, amp, 4.5, colour, 1.3)
    elif row == 4:  # 2.4: d.c. pulses, then the same pulses reversed
        s.line(xb0, mid, xb1, mid, colour, 1.4)
        for x_first, sign in ((xb0 + 10, -1.0), (xb0 + 116, 1.0)):
            y = mid + sign * 13
            for k in range(3):
                px = x_first + 24 * k
                s.path(
                    f"M {px} {mid} L {px} {y} L {px + 6} {y} L {px + 6} {mid}",
                    stroke=colour,
                    sw=1.6,
                )
        s.arrow(xb0 + 74, mid - 8, xb0 + 104, mid - 8, th.muted, 1.2)
    else:  # 2.5: the 1 kHz tone switched on suddenly
        s.line(xb0, mid, xb0 + 60, mid, colour, 1.4)
        _qp_sine(s, xb0 + 60, xb1, mid, 13, 22.5, colour)


def _d_quasi_peak_test(s: SVG, th: Theme) -> None:
    """The ITU-R BS.468-4 measuring set, its calibration and its five tests.

    The chain is the Recommendation's own: the weighting network of clause 1
    with the amplifier that clause 1 counts into the measuring equipment
    (Fig. 1a, Table 1), the attenuator that 2.1 to 2.3 hold, reset and step,
    the quasi-peak detector of clause 2, which the preamble defines
    by its readings and not by a circuit, and a reading device scaled in
    dBqps (clause 3), with the input impedance of 2.7 at the terminals. The
    dashed path around the network is the unweighted mode that only 2.4 uses.
    The table is the 2.6 calibration and one row per Method of measurement,
    each with its stimulus sketched and its acceptance limits written out,
    and the box at the foot says what the percentages of Tables 2 and 3 and
    the 0 dB of 2.6 are ratios of.
    """
    ay = 190.0  # the signal axis of the chain

    s.text(
        450,
        66,
        "The measuring set, and the six stimuli clause 2 tests it with",
        15,
        th.fg,
        bold=True,
    )

    # The generator, outside the instrument.
    s.rect(30, 150, 116, 80, th.panel, th.fg, rx=8, sw=2.2)
    s.text(88, 178, "Generator", 14, th.fg, bold=True)
    _qp_sine(s, 60, 116, 204, 8, 28, th.fg)
    s.text(88, 256, "a stimulus from the table", 12, th.muted)

    # The instrument itself.
    s.rect(172, 92, 708, 220, "none", th.muted, rx=8, sw=1.3, dash="6,4")
    s.text(870, 112, "the measuring set", 13, th.muted, anchor="end")

    # The input terminals and the impedance clause 2.7 puts across them.
    s.arrow(146, ay, 190, ay, th.fg, 2.0)
    s.circle(196, ay, 5, th.bg, th.fg, 2.0)
    s.line(196, ay + 5, 196, 206, th.fg, 2.0)
    s.rect(188, 206, 16, 36, th.bg, th.fg, rx=2, sw=2.0)
    s.line(196, 242, 196, 254, th.fg, 2.0)
    for k, hw in enumerate((12.0, 7.5, 3.0)):
        s.line(196 - hw, 254 + 5 * k, 196 + hw, 254 + 5 * k, th.fg, 2.0)
    s.text(216, 286, "input impedance ≥ 20 kΩ", 12, th.fg, anchor="start")
    s.text(216, 302, "termination, if any: 600 Ω ±1 %", 12, th.muted, anchor="start")

    # Unweighted mode: the one test clause 2 runs around the network. The
    # attenuator stays in circuit, so the path rejoins before it.
    s.line(201, ay, 240, ay, th.fg, 2.0)
    s.arrow(226, ay, 240, ay, th.fg, 2.0)
    s.path(
        f"M 218 {ay} L 218 124 L 432 124 L 432 {ay}",
        stroke=th.secondary,
        sw=1.8,
        dash="6,4",
    )
    s.circle(218, ay, 3.5, th.fg)
    s.circle(432, ay, 3.5, th.fg)
    s.text(325, 114, "unweighted mode: the 2.4 test only", 12, th.secondary)

    # Clause 1: the weighting network, and the amplifier clause 1 counts in
    # with it when it states the tolerance of the measuring equipment.
    s.rect(240, 144, 184, 94, th.panel, th.primary, rx=8, sw=2.2)
    s.text(332, 170, "Weighting network", 14, th.fg, bold=True)
    s.text(332, 190, "and amplifier", 12, th.muted)
    s.text(332, 210, "Table 1: 0 dB at 1 kHz", 12, th.muted)
    s.text(332, 228, "+12.2 dB at 6.3 kHz", 12, th.muted)
    s.text(332, 262, "clause 1, Fig. 1a", 12, th.muted)

    # The attenuator the table keeps sending the reader to: 2.1 and 2.2 hold
    # it and reset it, 2.3 steps it down and repeats on every range.
    s.arrow(424, ay, 446, ay, th.fg, 2.0)
    s.rect(446, 168, 56, 44, th.panel, th.fg, rx=4, sw=2.0)
    s.arrow(456, 204, 492, 176, th.fg, 1.8)
    s.text(474, 232, "Attenuator", 12, th.fg, bold=True)
    s.text(474, 250, "ranges: 2.1 to 2.3", 12, th.muted)

    # Clause 2: the detector, specified only by what it reads.
    s.arrow(502, ay, 530, ay, th.fg, 2.0)
    s.rect(530, 144, 190, 94, th.panel, th.fg, rx=8, sw=2.2)
    s.text(625, 174, "Quasi-peak detector", 14, th.fg, bold=True)
    s.text(625, 200, "defined by its readings,", 12, th.muted)
    s.text(625, 220, "not by a time constant", 12, th.muted)
    s.text(625, 262, "clause 2, Tables 2 and 3", 12, th.muted)

    # Clauses 2.5, 2.6 and 3: the reading device and its scale. The green
    # tick is 80 % of full scale: where the steady tone would read in 2.1
    # and 2.2, and where the pulses read in 2.4.
    s.arrow(720, ay, 742, ay, th.fg, 2.0)
    s.rect(742, 140, 124, 100, th.panel, th.accent, rx=8, sw=2.2)
    s.text(804, 160, "Reading device", 13, th.fg, bold=True)
    cx, cy, r = 804.0, 228.0, 42.0

    def polar(deg: float, rad: float) -> tuple[float, float]:
        return (
            cx + rad * math.cos(math.radians(deg)),
            cy - rad * math.sin(math.radians(deg)),
        )

    xa, ya = polar(150.0, r)
    xb, yb = polar(30.0, r)
    s.path(
        f"M {xa:.1f} {ya:.1f} A {r} {r} 0 0 1 {xb:.1f} {yb:.1f}", stroke=th.fg, sw=1.8
    )
    for deg in (150.0, 90.0, 30.0):
        x0, y0 = polar(deg, r - 7)
        x1, y1 = polar(deg, r)
        s.line(x0, y0, x1, y1, th.fg, 1.6)
    x0, y0 = polar(54.0, r - 9)
    x1, y1 = polar(54.0, r + 1)
    s.line(x0, y0, x1, y1, th.accent, 2.4)
    xn, yn = polar(54.0, r - 10)
    s.line(cx, cy, xn, yn, th.fg, 2.2)
    s.circle(cx, cy, 3.5, th.fg)
    s.text(804, 258, "clause 3: dBqps", 12, th.muted)
    s.text(804, 276, "0.775 V reads 0 dB", 12, th.muted)

    # The calibration and the five methods of measurement.
    s.text(
        450,
        346,
        "The calibration and the five methods of measurement, and what each must read",
        15,
        th.fg,
        bold=True,
    )
    s.text(
        450,
        368,
        "2.1 and 2.2 set the level at which the steady tone would read 80 % "
        "of full scale",
        12,
        th.muted,
    )
    top0, row_h = 380.0, 56.0
    for i, (name, weighted, lines) in enumerate(_QP_TEST_ROWS):
        top = top0 + row_h * i
        if i:
            s.line(30, top, 870, top, th.muted, 0.8, dash="2,4")
        tag = th.primary if weighted else th.secondary
        s.text(36, top + 24, name, 13, th.fg, anchor="start", bold=True)
        s.text(
            36,
            top + 42,
            "through the network" if weighted else "unweighted mode",
            12,
            tag,
            anchor="start",
        )
        s.text(446, top + 18, lines[0], 13, th.fg, anchor="start")
        s.text(446, top + 34, lines[1], 12, th.muted, anchor="start")
        if lines[2]:
            s.text(446, top + 50, lines[2], 12, th.muted, anchor="start")
        _qp_stimulus(s, th, i, top + row_h / 2, tag)

    # What the percentages and the 0 dB are ratios of.
    box_y = top0 + row_h * 6 + 16
    s.rect(30, box_y, 840, 88, th.panel, th.fg, rx=6, sw=1.6)
    s.text(245, box_y + 30, "$20 lg(U/U_{ss})$", 17, th.primary)
    s.text(
        245,
        box_y + 54,
        "Tables 2 and 3 in dB: Table 2 prints 40 % as −8.0 dB",
        12,
        th.fg,
    )
    s.text(655, box_y + 30, "$20 lg(U/U_0)$, $U_0$ = 0.775 V", 17, th.accent)
    s.text(655, box_y + 54, "clauses 2.6 and 3: the level in dBqps", 12, th.fg)
    s.text(
        450,
        box_y + 76,
        "$U$ is the reading and $U_{ss}$ the steady reading of the same tone",
        12,
        th.muted,
    )
    s.text(
        450,
        box_y + 114,
        "clause 2 prints no time constant: the readings above are all it "
        "specifies about the dynamics",
        12,
        th.muted,
    )
    s.text(
        450,
        box_y + 134,
        "its Note offers one possible arrangement: full-wave rectification, "
        "then two peak rectifiers of different time constants in tandem",
        12,
        th.muted,
    )
    s.text(
        450,
        box_y + 154,
        "overload capacity more than 20 dB above the top of the scale, at "
        "every attenuator setting (2.3)",
        12,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Noise control at the source, along the path and at the receiver
# ---------------------------------------------------------------------------


def _d_noise_control(s: SVG, th: Theme) -> None:
    """The source-path-receiver triad with the guide's numbers: a lined
    machine enclosure (IL = R - C = 25 dB at 500 Hz), a duct run with the
    m = 4 expansion chamber (TL peak 6.5 dB at 286 Hz), a lined elbow
    (6 dB at 1 kHz), the open-end reflection (18 dB at 63 Hz) and an
    operator cabin rated by the same IL = R - C (31 dB at 1 kHz).
    """
    gy = 440.0
    s.ground(gy, 40.0, 860.0)
    for zx in (340.0, 660.0):
        s.line(zx, 80.0, zx, gy - 4, th.muted, 1.0, dash="7,7")
    s.text(185, 70, "1 · At the source", 16, th.fg, bold=True)
    s.text(480, 70, "2 · Along the path", 16, th.fg, bold=True)
    s.text(770, 70, "3 · At the receiver", 16, th.fg, bold=True)

    # --- source: machine inside a lined enclosure --------------------------
    s.rect(80, 306, 150, gy - 306, "none", th.primary, rx=6, sw=2.6)
    s.rect(90, 316, 130, gy - 320, "none", th.accent, rx=4, sw=1.3, dash="5,4")
    s.rect(100, 356, 110, 84, th.panel, th.fg, rx=6, sw=2)
    s.circle(130, 396, 14, th.primary)
    s.circle(130, 396, 5, th.bg)
    for r in (26, 42):
        s.path(
            f"M {130 + r * 0.3:.0f} {396 - r:.0f} "
            f"A {r} {r} 0 0 1 {130 + r:.0f} {396 - r * 0.3:.0f}",
            stroke=th.muted,
            sw=1.2,
        )
    s.text(155, 296, "Enclosure", 15, th.primary, bold=True)
    s.text(178, 428, "Machine", 13, th.fg)
    s.text(185, 482, "enclosure $IL = R − C$", 13, th.primary, bold=True)
    s.text(185, 504, "25 dB at 500 Hz", 12, th.fg)

    # --- path: duct with expansion chamber, lined elbow and open end -------
    dt, db = 350.0, 374.0  # duct walls (24 px = 113 mm bore)
    ch_l, ch_r, ct, cb = 390.0, 480.0, 338.0, 386.0  # 0.30 m chamber
    s.line(230.0, dt, ch_l, dt, th.fg, 2.0)
    s.line(230.0, db, ch_l, db, th.fg, 2.0)
    s.rect(ch_l, ct, ch_r - ch_l, cb - ct, th.panel, th.primary, sw=2)
    s.line(ch_r, dt, 590.0, dt, th.fg, 2.0)
    s.line(ch_r, db, 614.0, db, th.fg, 2.0)
    s.line(590.0, dt, 590.0, 224.0, th.fg, 2.0)  # elbow, inner wall
    s.line(614.0, db, 614.0, 224.0, th.fg, 2.0)  # elbow, outer wall
    s.line(592.5, 348.0, 592.5, 240.0, th.accent, 2.0, dash="4,4")  # lining
    s.line(611.5, 360.0, 611.5, 240.0, th.accent, 2.0, dash="4,4")
    for r in (16, 28, 40):
        s.path(
            f"M {602 - r:.0f} {220:.0f} A {r} {r} 0 0 1 {602 + r:.0f} {220:.0f}",
            stroke=th.muted,
            sw=1.3,
        )
    s.text(300, 338, "Ø 113 mm", 11, th.muted, mono=True)
    s.text(435, 326, "expansion chamber", 13, th.fg, bold=True)
    s.text(435, 424, "Ø 226 mm", 11, th.muted, mono=True)
    s.dim(ch_l, cb, ch_r, cb, "0.30 m", offset=18, size=12)
    s.text(560, 292, "lined elbow", 12, th.accent, anchor="end")
    s.line(566.0, 288.0, 590.0, 272.0, th.muted, 1.0)
    s.text(548, 170, "open end", 12, th.fg, anchor="end")
    s.line(554.0, 176.0, 572.0, 190.0, th.muted, 1.0)
    s.text(
        480,
        482,
        "silencer TL peak 6.5 dB at 286 Hz ($m = 4$)",
        12,
        th.primary,
        bold=True,
    )
    s.text(480, 504, "lined elbow 6 dB at 1 kHz; open end 18 dB at 63 Hz", 11, th.fg)

    # --- receiver: operator cabin ------------------------------------------
    s.rect(700, 300, 150, gy - 300, th.panel, th.fg, rx=4, sw=2.4)
    s.rect(716, 320, 54, 44, th.bg, th.muted, sw=1.5)
    s.person(806, gy, 92)
    s.text(775, 290, "Operator cabin", 15, th.fg, bold=True)
    s.text(770, 482, "cabin $IL = R − C$", 13, th.primary, bold=True)
    s.text(770, 504, "31 dB at 1 kHz", 12, th.fg)

    # --- captions ----------------------------------------------------------
    s.text(
        80,
        540,
        "the classic ranking: quiet the source first, treat the path next, shield the receiver last",
        15,
        th.fg,
        anchor="start",
    )
    # Both caption lines run the full width of the canvas; the smaller face is
    # what keeps the longest of them (the silencer one) off the right edge.
    s.text(
        80,
        568,
        "enclosure and cabin share $IL = R − C$, with "
        "$C = 10 log_{10}(0.3 + S_E/R_i)$ = 4.9 dB for a lined interior "
        "($ᾱ = 0.3$)",
        13,
        th.fg,
        anchor="start",
    )
    s.text(
        80,
        596,
        "reactive silencer: $TL = 10 log_{10}[1 + ¼ (m − 1/m)^2 "
        "sin^{2}(k·L)]$, peaking where the 0.3 m chamber is $λ/4$",
        13,
        th.muted,
        anchor="start",
    )


# ---------------------------------------------------------------------------
# IEC 60268-3 electrical distortion bench
# ---------------------------------------------------------------------------


def _d_duct_path(s: SVG, th: Theme) -> None:
    """Long's Table 14.9 installation as a place, not as a thirteen-row table.

    Every box carries the sheet code the snippet stamps on its
    ``DuctElement``, so the two paths of ``duct_path_cascade.svg`` become
    readable as positions in a building. The stamps under each box are the
    element's own two spectra at 63 Hz: what it takes out, and what its
    airflow puts back.
    """
    s.add('<g transform="translate(0,-28)">')
    plant_x, room_x = 60.0, 596.0
    ceil_y, floor_y = 300.0, 470.0

    # --- the two spaces ----------------------------------------------------
    s.ground(floor_y, 40.0, 860.0)
    s.rect(plant_x, 150.0, 250.0, floor_y - 150.0, th.panel, th.fg, sw=2.4)
    s.rect(room_x, ceil_y, 244.0, floor_y - ceil_y, th.panel, th.fg, sw=2.4)
    s.text(plant_x + 10, 172, "Plant room", 14, th.fg, bold=True, anchor="start")
    s.text(
        room_x + 12, 322, "Office, 20 × 20 × 8 ft", 14, th.fg, bold=True, anchor="start"
    )
    s.text(room_x + 12, 342, "drywall and carpet, NC 30", 11, th.muted, anchor="start")
    s.line(room_x, ceil_y, room_x + 244.0, ceil_y, th.fg, 2.4)

    # --- the fan, radiating both ways --------------------------------------
    s.rect(plant_x + 66, 356, 116, 94, th.bg, th.fg, rx=6, sw=2.4)
    s.circle(plant_x + 124, 403, 26, "none", th.primary, sw=2.6)
    s.circle(plant_x + 124, 403, 7, th.primary)
    s.text(
        plant_x + 124, 342, "1 · Fan, 5000 cfm, 2 in w.g.", 12, th.primary, bold=True
    )
    s.text(plant_x + 124, 466, "same $L_W$ into both runs", 11, th.muted)

    # --- the supply run, left to right, above the office ceiling -----------
    supply = (
        ("2", "elbow", "36×24 in", 246.0, 62.0),
        ("3", "silencer", "3 ft", 320.0, 66.0),
        ("4", "lined duct", "5 ft", 396.0, 70.0),
        ("5", "branch", "25 %", 478.0, 56.0),
        ("6", "lined duct", "18×12 in", 546.0, 74.0),
        ("7", "flex duct", "12 in, 6 ft", 632.0, 72.0),
    )
    y = 224.0
    s.line(plant_x + 182, 240.0, 246.0, 240.0, th.fg, 2.2)
    for code, name, size, x, w in supply:
        s.rect(x, y, w, 34.0, th.bg, th.primary, rx=3, sw=2.0)
        s.text(x + w / 2, y + 23, code, 13, th.primary, bold=True)
        s.text(x + w / 2, y - 8, name, 10, th.fg)
        s.text(x + w / 2, y + 50, size, 10, th.muted, mono=True)
    for a, b in (
        (308.0, 320.0),
        (386.0, 396.0),
        (466.0, 478.0),
        (534.0, 546.0),
        (620.0, 632.0),
    ):
        s.line(a, y + 17, b, y + 17, th.fg, 2.2)
    s.line(704.0, y + 17, 780.0, y + 17, th.fg, 2.2)
    s.line(780.0, y + 17, 780.0, ceil_y - 8, th.fg, 2.2)
    s.rect(760.0, ceil_y - 8, 40.0, 12.0, th.bg, th.primary, sw=2.0)
    s.text(752.0, 296.0, "8 · diffuser 24 × 24 in", 11, th.primary, anchor="end")

    # --- the return run, below the supply, back to the plant room ----------
    ret = (
        ("2", "elbow", 246.0, 62.0),
        ("3", "silencer", 320.0, 74.0),
        ("4", "elbow, lined", 404.0, 74.0),
        ("5", "plenum", 488.0, 82.0),
    )
    yr = 140.0
    for code, name, x, w in ret:
        s.rect(x, yr, w, 30.0, th.bg, th.secondary, rx=3, sw=2.0)
        s.text(x + w / 2, yr + 21, code, 12, th.secondary, bold=True)
        s.text(x + w / 2, yr - 8, name, 10, th.fg)
    for a, b in ((308.0, 320.0), (394.0, 404.0), (478.0, 488.0)):
        s.line(a, yr + 15, b, yr + 15, th.fg, 2.2)
    s.line(570.0, yr + 15, 806.0, yr + 15, th.fg, 2.2)
    s.line(806.0, yr + 15, 806.0, 196.0, th.fg, 2.2)
    s.text(824.0, yr + 20, "6 · grille", 11, th.secondary, anchor="start")
    s.line(plant_x + 182, yr + 15, 246.0, yr + 15, th.fg, 2.2)
    s.arrow(246.0, yr + 15, plant_x + 190, yr + 15, th.secondary, 2.0)

    # --- the receiver ------------------------------------------------------
    s.person(room_x + 214, floor_y, 82, seated=True)
    # Clear of the room's caption block, which in Spanish reaches x = 782.
    s.dim(788.0, ceil_y + 6, 788.0, floor_y - 68, "$r$ = 1.83 m", size=11)
    s.text(
        room_x + 12, 392, "$Q = 2$, flush in the ceiling", 11, th.muted, anchor="start"
    )

    # --- the legend --------------------------------------------------------
    s.text(
        60,
        520,
        "blue: the supply path; red: the return path; each box "
        "is one row of the sheet, stamped with its code",
        13,
        th.fg,
        anchor="start",
    )
    s.text(
        60,
        546,
        "attenuates only: 4, 5, 6 (supply) and 4, 5 (return); "
        "attenuates and regenerates: 2, 3; self-noise only: "
        "8 and the grille",
        12,
        th.muted,
        anchor="start",
    )
    s.text(
        60,
        574,
        "the return wins above 1 kHz: its silencer floors the room "
        "near 25 dB, and no amount of supply attenuation moves that",
        12,
        th.muted,
        anchor="start",
    )
    s.add("</g>")


def _d_silencer_iso7235(s: SVG, th: Theme) -> None:
    """The ISO 7235 substitution measurement, both series on one duct axis.

    Series I carries the test object, series II the substitution duct, and
    the insertion loss is the difference of the two spatially energy-averaged
    receiving-side levels. The annotations are the standard's own
    qualification numbers: the modal filter's >= 3 dB / >= 5 dB longitudinal
    attenuation (5.2.2.3), r <= 0.3 at both qualification planes (5.2.2.5,
    5.2.4.3), the 5 % linear tolerance on the substitution duct (5.2.3), the
    >= 6 dB and preferably >= 10 dB signal-to-background rule (5.2.2.2), and
    the three microphone positions of 6.2.1.
    """
    x_box, w_box = 60.0, 105.0
    x_mf, w_mf = 190.0, 80.0
    x_tr, w_tr = 285.0, 70.0
    x_ob, w_ob = 375.0, 150.0
    x_rd, w_rd = 545.0, 285.0
    duct_h = 56.0

    for row, (y, title, obj, colour) in enumerate(
        (
            (150.0, "Series I: test object installed", "test object", th.primary),
            (330.0, "Series II: substitution duct", "substitution duct", th.secondary),
        )
    ):
        ax = y + duct_h / 2
        s.text(60, y - 24, title, 15, colour, bold=True, anchor="start")

        s.rect(x_box, y - 16, w_box, duct_h + 32, th.panel, th.fg, rx=5, sw=2.2)
        s.rect(
            x_box + 6,
            y - 10,
            w_box - 12,
            duct_h + 20,
            "none",
            th.accent,
            rx=3,
            sw=1.2,
            dash="4,3",
        )
        s.circle(x_box + w_box / 2, ax, 15, th.fg)
        s.circle(x_box + w_box / 2, ax, 6, th.bg)

        s.rect(x_mf, y, w_mf, duct_h, th.panel, th.fg, sw=2.0)
        for k in range(3):
            s.line(
                x_mf + 14 + 26 * k,
                y + 4,
                x_mf + 14 + 26 * k,
                y + duct_h - 4,
                th.accent,
                3.0,
            )
        s.path(
            f"M {x_tr} {y - 6} L {x_tr + w_tr} {y + 6} "
            f"L {x_tr + w_tr} {y + duct_h - 6} L {x_tr} {y + duct_h + 6} Z",
            fill=th.panel,
            stroke=th.fg,
            sw=2.0,
        )
        s.rect(x_ob, y - 10, w_ob, duct_h + 20, th.panel, colour, rx=4, sw=2.6)
        if row == 0:
            for k in range(4):
                s.line(
                    x_ob + 18 + 32 * k,
                    y - 4,
                    x_ob + 18 + 32 * k,
                    y + duct_h + 4,
                    colour,
                    2.4,
                )
        s.text(x_ob + w_ob / 2, y + duct_h + 40, obj, 12, colour, bold=True)

        s.rect(x_rd, y, w_rd, duct_h, th.panel, th.fg, sw=2.0)
        for k in range(3):
            s.path(
                f"M {x_rd + w_rd - 10 - 24 * k} {y + 2} "
                f"L {x_rd + w_rd - 34 - 24 * k} {ax} "
                f"L {x_rd + w_rd - 10 - 24 * k} {y + duct_h - 2} Z",
                fill="none",
                stroke=th.muted,
                sw=1.3,
            )
        s.line(x_rd + 44, ax - 21, x_rd + 128, ax + 17, th.muted, 1.1, dash="4,3")
        for k in range(3):
            s.circle(x_rd + 50 + 36 * k, ax - 18 + 17 * k, 6, th.fg)

        s.arrow(x_box + w_box, ax, x_mf, ax, th.fg, 2.0)
        s.arrow(x_mf + w_mf, ax, x_tr, ax, th.fg, 2.0)
        s.arrow(x_ob + w_ob, ax, x_rd, ax, th.fg, 2.0)
        s.line(x_ob - 12, y - 24, x_ob - 12, y + duct_h + 24, th.muted, 1.2, dash="3,3")
        s.line(x_rd - 8, y - 24, x_rd - 8, y + duct_h + 24, th.muted, 1.2, dash="3,3")
        s.text(
            x_rd + w_rd,
            y - 10,
            "$L_{pI}$" if row == 0 else "$L_{pII}$",
            13,
            colour,
            anchor="end",
        )

    # --- what each element is ----------------------------------------------
    for x, label in (
        (x_box + w_box / 2, "sealed, lined loudspeaker box"),
        (x_mf + w_mf / 2, "modal filter"),
        (x_tr + w_tr / 2, "transition"),
        (x_rd + w_rd / 2, "test duct, anechoic termination"),
    ):
        s.text(x, 468, label, 10, th.muted)
    s.text(
        x_rd + w_rd / 2,
        488,
        "three positions on a line inclined to the axis, at mid-length",
        10,
        th.muted,
    )
    s.text(x_ob + w_ob / 2, 488, "$r ≤ 0.3$ planes", 10, th.muted)

    # --- the quantity and its qualification rules ---------------------------
    s.text(
        60,
        532,
        "$D_i = L_{pI} − L_{pII}$, one third octave at a time",
        15,
        th.fg,
        anchor="start",
    )
    left = (
        "modal filter: ≥ 3 dB on the fundamental at the low-frequency end,",
        "≥ 5 dB above the cut-on of higher-order modes (5.2.2.3)",
        "substitution duct: the empty housing where possible, otherwise",
        "matched within 5 % in every linear dimension (5.2.3)",
    )
    right = (
        "reflection coefficient $r ≤ 0.3$ at the source and receiving",
        "qualification planes (5.2.2.5, 5.2.4.3)",
        "signal ≥ 6 dB and preferably ≥ 10 dB above the background",
        "(5.2.2.2); IEC 61260 third octaves, class 1 chain (5.2.4.6)",
    )
    for k, line in enumerate(left):
        s.text(60, 562 + 20 * k, line, 10, th.muted, anchor="start")
    for k, line in enumerate(right):
        s.text(468, 562 + 20 * k, line, 10, th.muted, anchor="start")

    s.text(
        60,
        668,
        "the reported figure is an insertion loss against a "
        "substitution duct, not a transmission loss",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        60,
        692,
        "and the facility's own limiting insertion loss (flanking "
        "along the duct walls) caps what it can report at all",
        13,
        th.muted,
        anchor="start",
    )


def _d_room_to_room(s: SVG, th: Theme) -> None:
    """Section through Norton problem 4.18, drawn at 50 px per metre.

    Every symbol of Equation (4.101) is a piece of this drawing: the blower
    in the floor-wall intersection that makes Q = 4 worth 6.0 dB, the
    reverberant L_p1 that drives the whole partition, the 5 x 3 m separating
    wall, the receiving room whose absorption area overtakes that wall
    between 250 and 500 Hz, and the receiver against NC 45. The annotations
    sit outside the rooms because 3 m of room is 150 px of drawing.
    """
    cl, fl = 262.0, 412.0  # ceiling and floor: 3 m at 50 px/m
    xa, xb = 130.0, 530.0  # plant room, 8 m
    xc, xd = 542.0, 792.0  # operator room, 5 m

    # The scene is laid out on its own grid and lifted clear of the title.
    s.add('<g transform="translate(0,-44)">')
    s.ground(fl, 90.0, 830.0)
    for x0, x1 in ((xa, xb), (xc, xd)):
        s.rect(x0, cl, x1 - x0, fl - cl, th.panel, th.fg, sw=2.4)
        s.line(x0 + 4, cl + 7, x1 - 4, cl + 7, th.accent, 2.4, dash="6,4")
    s.rect(xb, cl, xc - xb, fl - cl, th.secondary, th.fg, sw=2.0)
    s.line(xc + 4, fl - 5, xd - 4, fl - 5, th.accent, 2.4, dash="2,4")

    s.text(
        xa + 10, 288, "Plant room 8 × 10 × 3 m", 14, th.fg, bold=True, anchor="start"
    )
    s.text(xa + 10, 306, "bare floor, absorbent ceiling", 11, th.muted, anchor="start")
    s.text(
        xd - 10, 288, "Operator room 5 × 5 × 3 m", 14, th.fg, bold=True, anchor="end"
    )
    s.text(xd - 10, 306, "carpet, same ceiling", 11, th.muted, anchor="end")
    s.text(xb + 6, 250, "$S_w$", 13, th.secondary, bold=True)

    # --- the blower in the floor-wall intersection: Q = 4 ------------------
    s.path(
        f"M {xa} {fl} L {xa + 104} {fl} A 104 104 0 0 0 {xa} {fl - 104} Z",
        fill=th.panel,
        stroke=th.primary,
        sw=1.4,
    )
    s.rect(xa + 2, fl - 42, 58, 42, th.bg, th.fg, rx=4, sw=2.2)
    s.circle(xa + 31, fl - 21, 11, th.primary)
    s.circle(xa + 31, fl - 21, 4, th.bg)
    for r in (58, 84):
        s.path(
            f"M {xa + 31 + r * 0.30:.0f} {fl - 21 - r:.0f} "
            f"A {r} {r} 0 0 1 {xa + 31 + r:.0f} {fl - 21 - r * 0.30:.0f}",
            stroke=th.muted,
            sw=1.1,
        )
    s.text(xa + 118, fl - 84, "$Q = 4$", 13, th.primary, anchor="start", bold=True)

    # --- the path across the partition -------------------------------------
    s.arrow(xa + 250, 350, xb - 6, 350, th.primary, 2.2)
    s.text(xa + 250, 340, "$L_{p1}$", 12, th.primary, anchor="start")
    s.arrow(xc + 6, 350, xd - 78, 350, th.primary, 2.2)
    s.text(xd - 86, 340, "$L_{p2}$", 12, th.primary, anchor="end")
    s.arrow(xc + 6, 380, xb - 6, 380, th.muted, 1.0)
    s.text(xc + 14, 376, "$τ S_w$", 10, th.muted, anchor="start")
    s.person(xd - 40, fl, 78)

    # --- the flanking route the equation does not price --------------------
    s.path(
        f"M {xb - 120} {cl - 4} Q {xb + 6} {186} {xc + 120} {cl - 4}",
        stroke=th.secondary,
        sw=2.0,
        dash="7,5",
    )
    s.text(
        xb + 6,
        172,
        "flanking over the ceiling void: an allowance, not a model",
        11,
        th.secondary,
    )

    # --- dimensions ---------------------------------------------------------
    s.dim(xa, fl + 30, xb, fl + 30, "8 m", size=13)
    s.dim(xc, fl + 30, xd, fl + 30, "5 m", size=13)
    s.dim(xa - 46, cl, xa - 46, fl, "3 m", size=13)

    # --- the numbers, outside the rooms -------------------------------------
    s.text(
        50,
        480,
        "source side, blower on the floor at a wall mid-point: "
        "$L_W$ = 105 dB at 125 Hz, $Q = 4$ adds 6.0 dB, "
        "$L_{p1}$ = 107.0 dB",
        12,
        th.fg,
        anchor="start",
    )
    s.text(
        50,
        502,
        "partition, 5 m × 3 m = 15 m², TL = 39 dB at 125 Hz; "
        "the $τ S_w$ returned to the source room is off by default",
        12,
        th.fg,
        anchor="start",
    )
    s.text(
        50,
        524,
        "receiving side, $S_{2}α_{2}$ = 5.5 m² at 125 Hz rising to "
        "39.2 m² at 4 kHz; $L_{p2}$ = 72.4 dB against 60 dB for "
        "NC 45",
        12,
        th.fg,
        anchor="start",
    )

    # --- the equation and where it turns over -------------------------------
    s.text(
        50,
        558,
        "$NR = TL − 10 log_{10}[S_w / (S_{2}α_{2} + τ S_w)]$",
        15,
        th.fg,
        anchor="start",
    )
    s.text(
        50,
        584,
        "$S_{2}α_{2}$ passes the 15 m² of the wall between 250 and "
        "500 Hz: below it the wall delivers less than its TL",
        13,
        th.primary,
        anchor="start",
    )
    s.text(
        50,
        608,
        "both levels are reverberant-field spatial averages; the "
        "balance says nothing below 163 Hz (Schroeder, 75 m³)",
        13,
        th.muted,
        anchor="start",
    )
    s.add("</g>")


def _d_machine_enclosure(s: SVG, th: Theme) -> None:
    """Section through the close-fitting enclosure of this page's own fiche.

    The fiche case is S_E = 24 m2 of exposed shell (a 3.0 x 2.0 x 1.8 m box,
    five faces), S_i = 30 m2 of interior surface and a mean interior
    absorption of 0.30, so R_i = 12.9 m2 and C = 3.4 dB. Every element the
    insertion loss actually depends on is drawn: the three wall layers, the
    isolated machine, the sealed door, the sleeved penetration, the lined
    cooling ducts, and the one unsealed gap that caps the result.
    """
    gy, yt = 470.0, 200.0
    x0, x1 = 230.0, 680.0  # 3.0 m of shell at 150 px/m
    t = 12.0  # drawn wall thickness

    s.ground(gy, 40.0, 700.0)
    s.text(
        455,
        92,
        "$S_E$ = 24 m² of exposed shell: a 3.0 × 2.0 × 1.8 m box, five faces",
        14,
        th.primary,
        bold=True,
    )

    # --- roof: the lined cooling outlet and the sleeved service entry ------
    s.rect(520, 128, 56, yt - 128, "none", th.fg, sw=2.2)
    s.line(530, 128, 530, yt, th.accent, 2.0, dash="5,4")
    s.line(566, 128, 566, yt, th.accent, 2.0, dash="5,4")
    s.arrow(548, yt - 10, 548, 136, th.primary, 2.0)
    s.text(592, 156, "lined cooling outlet", 12, th.fg, anchor="start")
    s.text(
        592, 176, "a short lined duct, never a bare hole", 10, th.muted, anchor="start"
    )
    s.line(310, yt, 310, 156, th.fg, 3.0)
    s.circle(310, yt - 6, 9, "none", th.accent, sw=2.0)
    s.text(310, 142, "cable and pipe entry, sealed sleeve", 11, th.fg)

    # --- the shell, drawn as its three layers ------------------------------
    s.rect(x0, yt, x1 - x0, gy - yt, "none", th.fg, sw=2.6)
    s.rect(
        x0 + t * 0.5,
        yt + t * 0.5,
        x1 - x0 - t,
        gy - yt - t * 0.5,
        "none",
        th.accent,
        sw=2.0,
        dash="6,4",
    )
    s.rect(
        x0 + t,
        yt + t,
        x1 - x0 - 2 * t,
        gy - yt - t,
        "none",
        th.muted,
        sw=1.4,
        dash="2,4",
    )
    s.text(455, 240, "$S_i$ = 30 m², $ᾱ_i = 0.30$  →  $R_i$ = 12.9 m²", 13, th.fg)
    s.text(
        455,
        262,
        "wall build-up: sheet-steel mass, absorbent lining, perforated facing",
        11,
        th.muted,
    )

    # --- the machine, isolated from the shell and from the slab ------------
    s.rect(330, 356, 260, 88, th.panel, th.fg, rx=6, sw=2.2)
    s.circle(460, 400, 17, th.primary)
    s.circle(460, 400, 6, th.bg)
    for mx in (352, 412, 508, 568):
        s.path(f"M {mx} 444 q 8 7 0 13 q -8 7 0 13", stroke=th.secondary, sw=2.0)
    s.text(460, 342, "machine on vibration isolators", 13, th.fg, bold=True)
    s.text(
        455, 496, "no rigid contact with the shell or with its slab", 12, th.secondary
    )

    # --- access door with its seal, and the gap at its foot ----------------
    s.rect(218, 262, 24, 190, th.panel, th.fg, sw=2.0)
    for dy in (268, 446):
        s.line(218, dy, 242, dy, th.accent, 2.6)
    s.rect(218, 452, 24, gy - 452, th.secondary, th.secondary, sw=1.0)
    s.text(206, 252, "access door", 13, th.fg, anchor="end")
    s.text(202, 272, "1.28 m², $R$ = 15 dB", 11, th.muted, anchor="end")
    s.text(206, 312, "compression seal", 11, th.accent, anchor="end")
    s.line(208, 308, 216, 274, th.muted, 1.0)
    s.text(206, 420, "unsealed gap at the foot", 11, th.secondary, anchor="end")
    s.text(206, 440, "0.24 m² = 1 % of $S_E$", 11, th.secondary, anchor="end")
    s.line(208, 446, 216, 460, th.muted, 1.0)

    # --- the lined cooling inlet -------------------------------------------
    s.rect(x1, 384, 96, 56, "none", th.fg, sw=2.2)
    s.line(x1, 394, x1 + 96, 394, th.accent, 2.0, dash="5,4")
    s.line(x1, 430, x1 + 96, 430, th.accent, 2.0, dash="5,4")
    s.arrow(x1 + 88, 412, x1 + 12, 412, th.primary, 2.0)
    s.text(700, 300, "lined cooling inlet", 12, th.fg, anchor="start")
    s.text(700, 320, "cooling air needs a path", 10, th.muted, anchor="start")

    # --- dimensions --------------------------------------------------------
    s.dim(x0, gy + 58, x1, gy + 58, "3.0 m", size=13)
    s.dim(858, yt, 858, gy, "1.8 m", size=13)

    # --- the equation and the two results ----------------------------------
    s.text(
        40,
        560,
        "$IL = R − C$,   $C = 10 log_{10}(0.3 + S_E/R_i)$ = 3.4 dB",
        15,
        th.fg,
        anchor="start",
    )
    s.text(
        40,
        586,
        "sealed shell (mean $R$ = 32.3 dB): mean IL = 28.9 dB",
        13,
        th.primary,
        anchor="start",
    )
    s.text(
        40,
        610,
        "with the door: 21.4 dB; with the 1 % gap as well: "
        "15.1 dB, against the $10 log_{10}(S_E/S_a)$ = 20 dB cap",
        13,
        th.secondary,
        anchor="start",
    )
    s.text(
        40,
        634,
        "an enclosure delivers its worst element, not its panels",
        13,
        th.muted,
        anchor="start",
    )


def _d_distortion_bench(s: SVG, th: Theme) -> None:
    """The bench every IEC 60268-3 distortion figure is defined on.

    Clause 3.1.2 fixes the chain (source e.m.f. through the rated source
    impedance, output terminals on the rated load impedance) and 3.1.3 the
    operating point (rated conditions with the drive dropped 10 dB). The
    lower band carries the three acceptance rules of 14.12.3.2 and 14.12.4.1,
    which decide whether a reading may be believed at all.
    """
    ay = 196.0  # signal axis

    def box(x: float, w: float, head: str, sub: str, col: str) -> None:
        s.rect(x, ay - 44, w, 88, th.panel, col, rx=10, sw=2.2)
        s.text(x + w / 2, ay - 8, head, 15, th.fg, bold=True)
        s.text(x + w / 2, ay + 18, sub, 13, th.muted, mono=True)

    # Generator -> rated source impedance -> amplifier under test.
    box(46, 186, "Signal generator", "1 kHz sine", th.primary)
    s.line(232, ay, 268, ay, th.fg, 2.0)
    s.rect(268, ay - 15, 66, 30, th.bg, th.fg, rx=3, sw=2.0)
    s.text(301, 154, "rated source", 12, th.muted)
    s.text(301, 170, "impedance", 12, th.muted)
    s.line(334, ay, 372, ay, th.fg, 2.0)
    box(372, 206, "Amplifier under test", "Class A / B / D", th.secondary)

    # Output terminals across the rated load, drawn to ground.
    s.line(578, ay, 640, ay, th.fg, 2.0)
    s.circle(640, ay, 5.0, th.bg, th.fg, 2.0)
    s.line(640, ay, 640, ay + 74, th.fg, 2.0)
    s.rect(618, ay + 74, 44, 62, th.bg, th.accent, rx=3, sw=2.2)
    s.line(640, ay + 136, 640, ay + 162, th.fg, 2.0)
    for k, hw in enumerate((22.0, 14.0, 7.0)):
        s.line(640 - hw, ay + 162 + k * 7, 640 + hw, ay + 162 + k * 7, th.fg, 2.0)
    s.text(
        676, ay + 96, "Rated load impedance", 13, th.accent, anchor="start", bold=True
    )
    s.text(676, ay + 116, "8 Ω non-inductive resistor,", 12, th.muted, anchor="start")
    s.text(676, ay + 134, "never a loudspeaker", 12, th.muted, anchor="start")

    # Class D branch: the IEC 61606-1 analogue low-pass before the analyser.
    s.line(640, ay, 700, ay, th.fg, 2.0)
    s.rect(700, ay - 34, 152, 68, th.bg, th.muted, rx=8, sw=1.8, dash="7,5")
    s.text(776, ay - 10, "Class D only:", 12, th.muted)
    s.text(776, ay + 10, "IEC 61606-1", 12, th.muted, mono=True)
    s.text(776, ay + 28, "analogue low-pass", 11, th.muted)

    # Analyser tap, above the load and after the optional Class D filter.
    s.line(776, ay - 34, 776, 116, th.fg, 2.0)
    s.rect(596, 46, 256, 70, th.panel, th.primary, rx=10, sw=2.2)
    s.text(724, 74, "Analyser / ADC", 15, th.fg, bold=True)
    s.text(724, 98, "≥ 10 dB headroom", 12, th.muted)

    # The operating point, called out on the generator side.
    s.rect(46, 46, 400, 62, th.panel, th.secondary, rx=10, sw=2.0)
    s.text(246, 70, "Standard measuring conditions (3.1.3)", 15, th.fg, bold=True)
    s.text(
        246, 94, "rated conditions (3.1.2) with the source e.m.f. −10 dB", 13, th.muted
    )
    s.line(246, 108, 246, ay - 44, th.muted, 1.4, dash="6,5")

    # Pre-conditioning and the reportable set.
    s.text(
        46,
        402,
        "Clause 9: hold the amplifier at that operating point for "
        "1 h before the first reading.",
        14,
        th.fg,
        anchor="start",
    )

    # The three acceptance rules the clauses make part of the method.
    s.rect(46, 424, 806, 132, th.panel, th.accent, rx=12, sw=2.0)
    s.text(
        66,
        452,
        "Three checks, from the method itself",
        15,
        th.fg,
        anchor="start",
        bold=True,
    )
    checks = (
        ("source THD ≥ 10 dB below the lowest distortion to be measured (14.12.3.2 a)"),
        (
            "generator muted: residual < 1/3 of the distortion voltage, or the "
            "result is discarded (14.12.3.2 d)"
        ),
        (
            "highest significant harmonic inside the band: $f_1 ≤ f_{limit} / n$ "
            "(14.12.4.1, 30 kHz and $n = 5$ give 6 kHz)"
        ),
    )
    for k, txt in enumerate(checks):
        s.circle(76, 476 + k * 24, 4.0, th.accent)
        s.text(92, 481 + k * 24, txt, 13, th.muted, anchor="start")
    s.text(
        852, 452, "AES17 band 20 Hz – 20 kHz", 13, th.primary, anchor="end", mono=True
    )


# ---------------------------------------------------------------------------
# Swept-sine distortion: the two benches and the time budget
# ---------------------------------------------------------------------------


def _d_sweep_bench(s: SVG, th: Theme) -> None:
    """What plays and records a sweep, electrically and acoustically.

    Panel (a) is the electrical case, where a loopback channel fixes t = 0;
    panel (b) the acoustic one, where the reflection-free time bounds what
    may be called a free-field response. The strip below is the same time
    axis the harmonic pre-arrivals live on, drawn for the page's own sweep.
    """
    # ---- panel (a): electrical, with the loopback reference ---------------
    s.rect(40, 56, 386, 214, th.panel, th.muted, rx=12, sw=1.6)
    s.text(233, 84, "(a) Electrical device under test", 15, th.fg, bold=True)

    s.rect(64, 112, 118, 60, th.bg, th.primary, rx=8, sw=2.0)
    s.text(123, 138, "Audio", 14, th.fg, bold=True)
    s.text(123, 158, "interface", 14, th.fg, bold=True)
    s.rect(268, 112, 132, 60, th.bg, th.secondary, rx=8, sw=2.0)
    s.text(334, 138, "Device", 14, th.fg, bold=True)
    s.text(334, 158, "under test", 14, th.fg, bold=True)
    s.arrow(182, 128, 268, 128, th.fg, 1.8)
    s.text(225, 120, "out", 11, th.muted)
    s.arrow(400, 156, 400, 200, th.fg, 1.8)
    s.line(400, 200, 123, 200, th.fg, 1.8)
    s.arrow(160, 200, 123, 200, th.fg, 1.8)
    s.text(262, 194, "in: channel 1", 11, th.muted)
    s.line(182, 148, 216, 148, th.accent, 1.8, dash="7,4")
    s.line(216, 148, 216, 232, th.accent, 1.8, dash="7,4")
    s.line(216, 232, 123, 232, th.accent, 1.8, dash="7,4")
    s.arrow(160, 232, 123, 232, th.accent, 1.8)
    s.text(233, 252, "loopback: channel 2 fixes $t = 0$", 12, th.accent)

    # ---- panel (b): acoustic, with the first reflection --------------------
    s.rect(444, 56, 416, 214, th.panel, th.muted, rx=12, sw=1.6)
    s.text(652, 82, "(b) Loudspeaker in a room", 15, th.fg, bold=True)
    s.text(652, 104, "source and microphone at 1.20 m over a hard floor", 12, th.muted)
    gy = 250.0
    s.ground(gy, 474.0, 834.0, hatch=18)

    sx, mx, hy = 546.0, 762.0, 178.0
    s.line(sx, hy + 24, sx, gy, th.fg, 2.0)
    s.rect(sx - 24, hy - 28, 48, 52, th.bg, th.primary, rx=5, sw=2.0)
    s.circle(sx, hy, 10, th.primary)
    s.line(mx, hy + 6, mx, gy, th.fg, 2.0)
    s.rect(mx - 20, hy - 6, 32, 12, th.primary, rx=4)
    s.rect(mx + 12, hy - 4, 10, 8, th.fg, rx=2)

    s.line(sx + 24, hy, mx - 20, hy, th.fg, 2.0)
    s.dim(sx, hy, mx, hy, "$d$ = 1.00 m", offset=-38, size=13)
    fx = (sx + mx) / 2
    s.line(sx, hy, fx, gy, th.secondary, 1.8, dash="8,5")
    s.line(fx, gy, mx, hy, th.secondary, 1.8, dash="8,5")
    # Inside the V of the reflected path, under the direct one, and 11 px in
    # Spanish to fit between the legs: set at the floor, both legs of the V
    # ran through it.
    reflected = "reflected path 2.60 m"
    s.text(fx, hy + 14, reflected, s.fit_size([reflected], [12, 11], 156), th.secondary)

    # ---- what the room costs, under both panels ---------------------------
    s.text(
        450,
        296,
        "Reflection-free time $t_g$ = (2.60 − 1.00) m / (343 "
        "m/s) = 4.7 ms: past that the record is the room, not "
        "the box.",
        14,
        th.fg,
    )

    # ---- the shared time budget of the harmonic arrivals -------------------
    x0, x1, ty = 90.0, 830.0, 412.0
    s.text(
        450,
        336,
        "Recording on the sweep's time axis: $f_1$ = 20 Hz, "
        "$f_2$ = 6 kHz, $T$ = 4 s, $L = T / ln(f_2/f_1)$ = "
        "0.70 s",
        15,
        th.fg,
        bold=True,
    )
    s.line(x0, ty, x1, ty, th.fg, 2.0)
    s.arrow(x1 - 30, ty, x1, ty, th.fg, 2.0)

    def tx(t: float) -> float:
        """Map an arrival time in seconds onto the strip (−1.0 s … +0.3 s)."""
        return x0 + (t + 1.0) / 1.3 * (x1 - 40 - x0)

    for t, lab, col, h in (
        (0.0, "$h_1$ (linear)", th.primary, 46.0),
        (-0.486, "$h_2$  −0.49 s", th.secondary, 34.0),
        (-0.770, "$h_3$  −0.77 s", th.accent, 26.0),
    ):
        s.line(tx(t), ty, tx(t), ty - h, col, 3.0)
        s.text(tx(t), ty - h - 9, lab, 13, col, bold=True)
    s.text(tx(0.0), ty + 22, "$t = 0$", 12, th.muted)

    # The per-order window against the closest spacing.
    s.rect(
        tx(-0.486),
        ty + 14,
        tx(-0.202) - tx(-0.486),
        26,
        th.panel,
        th.muted,
        rx=5,
        sw=1.4,
    )
    s.text(
        (tx(-0.486) + tx(-0.202)) / 2,
        ty + 62,
        "per-order window: 8192 samples = 0.17 s at 48 kHz",
        12,
        th.muted,
    )
    s.dim(
        tx(-0.770),
        ty + 104,
        tx(-0.486),
        ty + 104,
        "$L ln(3/2)$ = 0.28 s: the closest pair of arrivals",
        offset=0,
        size=13,
    )

    s.text(
        40,
        ty + 144,
        "Record until the decay has died, or the "
        "pre-arrivals wrap round the circular deconvolution "
        "into $h_1$.",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        40,
        ty + 168,
        "State the drive amplitude and the fade with the "
        "result, and pass the same fade to the analysis.",
        14,
        th.muted,
        anchor="start",
    )


# ---------------------------------------------------------------------------
# IEC 60268-5 polar measurement
# ---------------------------------------------------------------------------


def _d_loudspeaker_polar(s: SVG, th: Theme) -> None:
    """How a polar cut is taken (IEC 60268-5 23.1.2), in plan.

    The loudspeaker turns and the microphone does not: the reference point
    sits on the rotation axis so the measuring distance never changes, and
    the drive is retrimmed per band so that the on-axis pressure is held
    constant. The inset is the same cut on the IEC 60263 reference circle.
    """
    cx, cy, r = 292.0, 300.0, 176.0

    # Anechoic boundary.
    s.rect(40, 62, 512, 438, th.bg, th.fg, sw=2.4)
    for wx in range(44, 532, 40):
        s.path(
            f"M {wx} {62} L {wx + 40} {62} L {wx + 20} {88} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=1.0,
        )
        s.path(
            f"M {wx} {500} L {wx + 40} {500} L {wx + 20} {474} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=1.0,
        )
    for wy in range(90, 466, 40):
        s.path(
            f"M {40} {wy} L {40} {wy + 40} L {66} {wy + 20} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=1.0,
        )
        s.path(
            f"M {552} {wy} L {552} {wy + 40} L {526} {wy + 20} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=1.0,
        )
    # Clear of the wall's wedges, whose tips reach x = 66.
    s.text(72, 110, "Anechoic room, plan view", 13, th.muted, anchor="start")

    # The measuring arc the microphone is stepped along.
    s.path(
        f"M {cx + r:.1f} {cy:.1f} A {r} {r} 0 0 0 {cx - r:.1f} {cy:.1f}",
        stroke=th.accent,
        sw=1.8,
        dash="6,6",
    )
    for ang in (30, 60, 90, 120, 150):
        a = math.radians(ang)
        s.circle(cx + r * math.cos(a), cy - r * math.sin(a), 3.6, th.accent)
    # Outside the arc's end rather than on it, and the step inside the arc:
    # both labels sat where the arc ran through them.
    s.text(cx - r - 8, cy - 4, "180°", 12, th.accent, anchor="end")
    s.text(cx + 8, cy - r - 6, "90°", 12, th.accent, anchor="start")
    s.text(cx + 70, cy - 88, "$θ$ stepped by 10° or 15°", 12, th.accent)

    # Turntable, with the reference point over the rotation axis.
    s.ellipse(cx, cy, 70, 28, th.panel, th.muted, sw=1.8)
    s.circle(cx, cy, 4.0, th.fg)

    # Cabinet, seen from above, radiating along the reference axis.
    s.rect(cx - 32, cy - 24, 28, 48, th.panel, th.primary, rx=4, sw=2.0)
    s.line(cx - 4, cy - 24, cx - 4, cy + 24, th.primary, 2.4)

    # Reference axis at 0 degrees, out to the fixed microphone.
    s.line(cx, cy, cx + r + 40, cy, th.muted, 1.6, dash="8,5")
    # Both names under the axis, clear of the turntable and of the arc's end
    # (above the axis, the arc ran through the first) and inside the wall's
    # wedges (centred under the microphone, they ran through the second).
    s.text(cx + 80, cy + 22, "reference axis  0°", 13, th.muted, anchor="start")
    mx = cx + r
    s.rect(mx - 2, cy - 8, 38, 16, th.primary, rx=5)
    s.rect(mx - 16, cy - 5, 14, 10, th.fg, rx=3)
    s.text(mx + 52, cy + 44, "measuring microphone", 12, th.fg, anchor="end")

    # The two facts the geometry exists to guarantee.
    s.line(cx - 30, cy + 22, cx - 116, cy + 78, th.muted, 1.2, dash="4,4")
    # 11 px, so that the Spanish ends short of the witness line under the
    # rotation axis.
    s.text(
        72,
        cy + 116,
        "reference point on the rotation axis:",
        11,
        th.muted,
        anchor="start",
    )
    s.text(
        72, cy + 134, "$r$ never changes as $θ$ is swept", 11, th.muted, anchor="start"
    )
    # Witness lines from below the two names down to the dimension, so that
    # they do not run through them.
    s.dim(cx, cy + 150, mx - 16, cy + 150, "$r$ = 2 m", offset=0, size=14)
    for witness in (cx, mx - 16):
        s.line(witness, cy + 56, witness, cy + 150, th.muted, 0.9, dash="3,3")

    # The drive rule that makes the cut a pattern rather than a response.
    s.rect(596, 62, 264, 128, th.panel, th.secondary, rx=10, sw=2.0)
    s.text(728, 90, "Drive condition (23.1.2.3)", 14, th.fg, bold=True)
    s.text(728, 114, "input voltage retrimmed at each", 12, th.muted)
    s.text(728, 132, "frequency or band so that $L_p$ on", 12, th.muted)
    s.text(728, 150, "the reference axis stays constant", 12, th.muted)
    s.text(728, 176, "500 Hz · 1 k · 2 k · 4 k · 8 k", 13, th.secondary)

    # Inset: the same cut on the IEC 60263 25 dB reference circle.
    ix, iy, ir = 728.0, 344.0, 108.0
    s.text(728, 216, "The cut, on the IEC 60263 circle", 14, th.fg, bold=True)
    for k, frac in enumerate((1.0, 0.8, 0.6, 0.4, 0.2)):
        s.circle(ix, iy, ir * frac, "none", th.muted, 1.0)
        if k:
            # Just outside its ring: inside it, the small rings curve down
            # through their own labels.
            s.text(
                ix + 5, iy - ir * frac - 3, f"−{k * 5}", 10, th.muted, anchor="start"
            )
    s.line(ix - ir - 12, iy, ix + ir + 12, iy, th.muted, 1.0)
    s.line(ix, iy - ir - 12, ix, iy + ir + 12, th.muted, 1.0)
    pts = []
    for ang in range(-180, 181, 5):
        a = math.radians(ang)
        # A first-order cut, drawn on the clause-3 convention: the full
        # radius is 25 dB and the reference-axis level is the outer ring.
        mag = max(abs((1.0 + math.cos(a)) / 2.0), 1e-3)
        lev = max(-25.0, 20.0 * math.log10(mag))
        rad = ir * (25.0 + lev) / 25.0
        pts.append(f"{ix + rad * math.sin(a):.1f} {iy - rad * math.cos(a):.1f}")
    s.path("M " + " L ".join(pts) + " Z", stroke=th.primary, sw=2.2)
    s.text(728, iy + ir + 38, "outer ring = the reference-axis level,", 12, th.muted)
    s.text(728, iy + ir + 56, "full radius = 25 dB (clause 3)", 12, th.muted)

    s.text(
        450,
        542,
        "Directivity: free field on axis against a "
        "reverberation room, $D_i = L_{ax} − L_p + 10 lg(T/T_0) − "
        "10 lg(V/V_0)$ + 25 dB",
        14,
        th.fg,
    )
    s.text(
        450,
        566,
        "(23.3.2.1), or by integrating these polar curves over the sphere (23.3.2.2).",
        14,
        th.muted,
    )


# ---------------------------------------------------------------------------
# IEC 60268-4: the three fields a microphone sensitivity can be defined in
# ---------------------------------------------------------------------------


def _d_microphone_references(s: SVG, th: Theme) -> None:
    """Free field, diffuse field and pressure, on one capsule.

    The same capsule in three sound fields defines three different
    sensitivities (11.2.1, 11.2.2, 11.2.4). They agree while the capsule is
    small against the wavelength and separate once it is not, which is the
    whole reason the *type* has to be quoted with the number.
    """
    tops, w = (34.0, 320.0, 606.0), 260.0
    heads = ("Free field (11.2.1)", "Diffuse field (11.2.2)", "Pressure (11.2.4)")
    for x0, head in zip(tops, heads, strict=True):
        s.rect(x0, 54, w, 306, th.panel, th.muted, rx=12, sw=1.6)
        s.text(x0 + w / 2, 80, head, 15, th.fg, bold=True)

    def capsule(cx: float, cy: float) -> None:
        """One capsule glyph, diaphragm facing left along its reference axis."""
        s.rect(cx - 4, cy - 15, 54, 30, th.panel, th.primary, rx=6, sw=2.0)
        s.rect(cx - 18, cy - 12, 14, 24, th.fg, rx=3)
        s.line(cx - 18, cy - 12, cx - 18, cy + 12, th.secondary, 2.6)

    # --- 1: free field, plane wave on the reference axis --------------------
    x0 = tops[0]
    cx, cy = x0 + 168.0, 176.0
    for k in range(4):
        s.path(
            f"M {x0 + 40 + k * 22} {cy - 52} q 10 52 0 104", stroke=th.primary, sw=1.6
        )
    s.arrow(x0 + 118, cy, x0 + 140, cy, th.primary, 1.8)
    capsule(cx, cy)
    s.line(cx - 18, cy, x0 + 246, cy, th.muted, 1.2, dash="7,5")
    # The captions of all three panels start at yc, below the diffuse
    # field's lowest rays, which ran through its first line at 254.
    yc = 262.0
    s.text(x0 + w / 2, yc, "one source on the reference axis,", 12, th.muted)
    s.text(x0 + w / 2, yc + 18, "far enough that $r ≥ d$,", 12, th.muted)
    s.text(x0 + w / 2, yc + 36, "$r ≥ d^2/λ$ and $r$ ≥ 3 × the source", 12, th.muted)
    s.text(x0 + w / 2, yc + 64, "$M_{ff}$ : the undisturbed", 14, th.primary, bold=True)
    s.text(x0 + w / 2, yc + 83, "pressure of the plane wave", 13, th.muted)

    # --- 2: diffuse field, rays from every direction ------------------------
    x1 = tops[1]
    # The star a little higher and 78 px across rather than 96, so that its
    # lowest rays end above the captions.
    cx, cy = x1 + 130.0, 170.0
    for ang in range(0, 360, 30):
        a = math.radians(ang)
        s.arrow(
            cx + 78 * math.cos(a),
            cy + 78 * math.sin(a),
            cx + 40 * math.cos(a),
            cy + 40 * math.sin(a),
            th.accent,
            1.4,
        )
    capsule(cx - 22, cy)
    s.text(x1 + w / 2, yc, "sound from every direction,", 12, th.muted)
    s.text(x1 + w / 2, yc + 18, "with equal probability", 12, th.muted)
    s.text(x1 + w / 2, yc + 36, "(a reverberation room)", 12, th.muted)
    s.text(
        x1 + w / 2,
        yc + 64,
        "$M_{diff}$ : the r.m.s. of $M(θ)$",
        14,
        th.accent,
        bold=True,
    )
    s.text(x1 + w / 2, yc + 83, "$D = 20 lg(M_0 / M_{diff})$", 13, th.muted)

    # --- 3: pressure, the capsule closed into a coupler ---------------------
    x2 = tops[2]
    cx, cy = x2 + 150.0, 176.0
    s.rect(cx - 118, cy - 48, 122, 96, th.bg, th.secondary, rx=8, sw=2.2)
    s.circle(cx - 92, cy, 16, th.panel, th.muted, 1.6)
    s.arrow(cx - 92, cy + 30, cx - 92, cy - 30, th.secondary, 1.6)
    capsule(cx, cy)
    s.text(cx - 56, cy - 62, "cavity small against $λ$", 12, th.muted)
    s.text(x2 + w / 2, yc, "a coupler or a calibrator:", 12, th.muted)
    s.text(x2 + w / 2, yc + 18, "the pressure the capsule", 12, th.muted)
    s.text(x2 + w / 2, yc + 36, "itself replaces", 12, th.muted)
    s.text(x2 + w / 2, yc + 64, "$M_p$ : pressure at", 14, th.secondary, bold=True)
    s.text(x2 + w / 2, yc + 83, "the acoustic entry", 13, th.muted)

    # --- the bench the first two are realised on ----------------------------
    s.rect(34, 380, 832, 116, th.panel, th.primary, rx=12, sw=2.0)
    s.text(
        54,
        408,
        "The bench (clauses 5.5.2, 5.6.2, 5.7)",
        15,
        th.fg,
        anchor="start",
        bold=True,
    )
    rules = (
        (
            "anechoic room; the spherical wave counts as plane at least $λ/2$ "
            "from the centre of curvature at the lowest frequency"
        ),
        (
            "substitution: the microphone under test and a calibrated reference "
            "at the same point, in turn (highest accuracy)"
        ),
        (
            "simultaneous comparison at two nearby points only after showing it "
            "agrees with substitution within ± 1 dB"
        ),
    )
    for k, txt in enumerate(rules):
        s.circle(64, 432 + k * 22, 4.0, th.primary)
        s.text(80, 437 + k * 22, txt, 12, th.muted, anchor="start")
    s.text(
        846,
        408,
        "overall accuracy ± 2 dB or better",
        13,
        th.primary,
        anchor="end",
        mono=True,
    )

    s.text(
        450,
        528,
        "Polar cuts (13.1.2 a): distance, sound pressure and "
        "frequency held constant while $θ$ is stepped, by 10° or "
        "15°,",
        14,
        th.fg,
    )
    s.text(
        450,
        552,
        "at the octave centres 125 Hz to 16 kHz, with the "
        "reference axis as 0° of the polar diagram.",
        14,
        th.muted,
    )


def _d_vdi2081_sheet(s: SVG, th: Theme) -> None:
    """The VDI 2081 Part 2 worked sheet as a place, and where each number comes from.

    Table 1 is twenty numbered elements in a column; this is the same twenty
    as an installation, so a reader can see which of them takes level out,
    which puts it back, and which does both. The strip along the bottom names
    the equation or the measurement each row is obtained from, which is the
    part a table of results cannot show.
    """
    plant_x, room_x = 40.0, 552.0
    plant_top, ceil_y, floor_y = 108.0, 314.0, 452.0

    # --- the two spaces ----------------------------------------------------
    s.ground(floor_y, 24.0, 876.0)
    s.rect(plant_x, plant_top, 210.0, floor_y - plant_top, th.panel, th.fg, sw=2.4)
    s.rect(room_x, ceil_y, 312.0, floor_y - ceil_y, th.panel, th.fg, sw=2.4)
    s.text(
        plant_x + 10, plant_top + 22, "Plant room", 14, th.fg, bold=True, anchor="start"
    )
    s.line(room_x, ceil_y, room_x + 312.0, ceil_y, th.fg, 2.4)

    # --- element 1: the fan, at the head of the run ------------------------
    fan_cx, fan_cy = plant_x + 118.0, 232.0
    s.rect(fan_cx - 60, fan_cy - 46, 120, 92, th.bg, th.fg, rx=6, sw=2.4)
    s.circle(fan_cx, fan_cy, 27, "none", th.primary, sw=2.6)
    s.circle(fan_cx, fan_cy, 7, th.primary)
    s.text(fan_cx, fan_cy - 58, "1 · Supply fan", 12, th.primary, bold=True)
    s.text(fan_cx, fan_cy + 64, "16 000 m³/h, 600 Pa", 10, th.muted, mono=True)
    s.text(fan_cx, fan_cy + 82, "radial, backward blades", 10, th.muted)

    # --- the run, plant room to room 102 -----------------------------------
    run = (
        ("2", "splitter silencer", "5 baffles, 0.6 m", 268.0, 96.0, th.secondary),
        ("3", "branch", "0.30 of 1.08 m²", 390.0, 74.0, th.accent),
        ("5", "straight duct", "0.5 × 0.4 m, 4 m", 488.0, 82.0, th.primary),
        ("14", "bend", "160 mm round", 596.0, 66.0, th.accent),
        ("19", "two diffusers", "into the room", 686.0, 86.0, th.secondary),
    )
    y = fan_cy - 17.0
    s.line(fan_cx + 60, fan_cy, 268.0, fan_cy, th.fg, 2.2)
    for code, name, size, x, w, colour in run:
        s.rect(x, y, w, 34.0, th.bg, colour, rx=3, sw=2.0)
        s.text(x + w / 2, y + 23, code, 13, colour, bold=True)
        s.text(x + w / 2, y - 8, name, 10, th.fg)
        s.text(x + w / 2, y + 50, size, 10, th.muted, mono=True)
    for a, b in ((364.0, 390.0), (464.0, 488.0), (570.0, 596.0), (662.0, 686.0)):
        s.line(a, fan_cy, b, fan_cy, th.fg, 2.2)
    s.line(772.0, fan_cy, 838.0, fan_cy, th.fg, 2.2)
    s.line(838.0, fan_cy, 838.0, ceil_y - 8, th.fg, 2.2)
    s.rect(814.0, ceil_y - 8, 48.0, 12.0, th.bg, th.secondary, sw=2.0)

    # --- element 20: the room, and the listener 1,5 m from the outlet ------
    s.text(room_x + 14, ceil_y + 26, "Room 102", 14, th.fg, bold=True, anchor="start")
    s.text(room_x + 14, ceil_y + 46, "$A$ = 20 m²", 11, th.muted, anchor="start")
    s.text(
        room_x + 14,
        ceil_y + 66,
        "20 · $Q$ = 2.1 at 63 Hz",
        11,
        th.muted,
        anchor="start",
    )
    s.text(
        room_x + 14,
        ceil_y + 84,
        "to 7.2 at 8 kHz (Figure 30)",
        11,
        th.muted,
        anchor="start",
    )
    s.person(room_x + 190, floor_y, 84)
    s.dim(room_x + 190, ceil_y + 36, 838.0, ceil_y + 36, "$r$ = 1.5 m", size=11)

    # --- what each element does to the level -------------------------------
    s.text(
        40,
        floor_y + 46,
        "takes level out: 2, 3, 5 and 14; puts level back: 2 and 14 make "
        "their own flow noise, and 19 is a source in its own right",
        12,
        th.fg,
        anchor="start",
    )

    # --- where each number comes from --------------------------------------
    sources = (
        ("1", "Eq. (13) and (15), from the duty point and the assembly type"),
        ("2", "insertion loss from the maker; self-noise from Eq. (49)"),
        ("3", "Eq. (35), the branch's area ratio; flow noise from Eq. (18)"),
        ("5", "Table 5, dB per metre by duct size"),
        ("14", "Table 7 by bend size; flow noise from Eq. (18)"),
        ("20", "Eq. (36), from $A$ and the outlet's own $Q$"),
    )
    for index, (code, source) in enumerate(sources):
        row, column = divmod(index, 2)
        x = 40.0 + column * 436.0
        yy = floor_y + 76.0 + row * 22.0
        s.text(x, yy, code, 11, th.primary, bold=True, anchor="start")
        s.text(x + 26, yy, source, 11, th.muted, anchor="start")


def _d_enclosure_cabin_measurement(s: SVG, th: Theme) -> None:
    """The two runs of ISO 11546 and the one subtraction of ISO 11957.

    An enclosure keeps noise in and a cabin keeps it out, and the two are
    measured as mirror images of each other. The enclosure is a difference of
    two determinations of the same machine, one without the box and one with
    it, which is Equation (1) of both parts. The cabin is one subtraction
    between the level in the room and the level inside the empty cabin, which
    is Equation (1) of ISO 11957, with the loudspeaker positions of 7.2.1 read
    off the spread of the answer itself.
    """
    floor = 300.0

    s.text(
        232, 96, "ISO 11546: two runs of the same machine", 15, th.primary, bold=True
    )
    s.text(232, 128, "the measurement surface is the same in both", 13, th.muted)
    for x0, label, boxed in (
        (60.0, "without the enclosure", False),
        (270.0, "with the enclosure", True),
    ):
        s.ground(floor, x0 - 5, x0 + 176)
        s.rect(x0 + 55, floor - 56, 60, 56, th.panel, th.fg, rx=5, sw=2.2)
        s.circle(x0 + 85, floor - 28, 12, th.fg)
        s.circle(x0 + 85, floor - 28, 5, th.bg)
        if boxed:
            s.rect(x0 + 40, floor - 84, 90, 84, "none", th.primary, rx=4, sw=2.6)
        # The measurement surface stands outside whatever is being measured,
        # which is the whole point of the two runs having the same one.
        s.rect(
            x0 + 8, floor - 128, 154, 128, "none", th.muted, rx=6, sw=1.3, dash="6,4"
        )
        s.mic(x0 + 8, floor - 98, floor, scale=0.6)
        s.mic(x0 + 162, floor - 98, floor, scale=0.6)
        for j in range(2):
            s.circle(x0 + 52 + 60 * j, floor - 128, 5, th.fg)
        if boxed:
            s.text(x0 + 85, floor - 144, "the enclosure", 13, th.primary, bold=True)
        s.text(x0 + 85, floor + 30, label, 13, th.muted)
        s.text(
            x0 + 85,
            floor + 52,
            "$L_{W,without}$" if not boxed else "$L_{W,with}$",
            14,
            th.primary,
        )

    s.text(690, 96, "ISO 11957: one room, one cabin", 15, th.secondary, bold=True)
    s.ground(floor, 520, 860)
    s.rect(535, floor - 150, 310, 150, "none", th.fg, rx=4, sw=2.0)
    s.text(
        690,
        floor - 164,
        "the room, driven by a loudspeaker or by the work itself",
        13,
        th.muted,
    )
    s.rect(700, floor - 96, 130, 96, th.panel, th.secondary, rx=4, sw=2.6)
    s.text(765, floor + 30, "the cabin, empty", 13, th.secondary)
    for j in range(3):
        s.mic(560 + 44 * j, floor - 116, floor, scale=0.6)
    for j in range(2):
        s.mic(735 + 52 * j, floor - 78, floor, scale=0.6)
    s.text(620, floor + 30, "in the room", 13, th.muted)
    s.text(620, floor + 52, "$L_{p,room}$", 14, th.secondary)
    s.text(765, floor + 52, "$L_{p,cabin}$", 14, th.secondary)

    s.rect(70, 400, 760, 66, th.panel, th.fg, rx=6, sw=1.6)
    s.text(270, 428, "$D_W = L_{W,without} - L_{W,with}$", 17, th.primary)
    s.text(660, 428, "$D_p = L_{p,room} - L_{p,cabin}$", 17, th.secondary)
    s.text(
        450,
        452,
        "one quantity kept in, one kept out, and the same arithmetic both ways",
        13,
        th.muted,
    )

    s.text(
        450,
        500,
        "the machine that cannot be run twice has two substitutes: the reciprocity method and the artificial source of Annex A",
        13,
        th.muted,
    )
    s.text(
        450,
        524,
        "and in situ the number of loudspeaker positions is read off how much the answer moved between them",
        13,
        th.muted,
    )


def _d_silencer_in_situ(s: SVG, th: Theme) -> None:
    """The ISO 11820 measurement: one run, two measurement surfaces.

    The laboratory method of ISO 7235 substitutes a straight duct for the
    silencer and reads the difference of two runs. In situ there is nothing to
    substitute, so the quantity comes from the two sides of the one
    installation that exists: a mean level on each measurement surface, the
    ratio of the two areas, and the difference of the two field corrections.
    The distances are Equations (15) and (16), the areas are the rules clause 9
    attaches to each of the twenty installations of Figure 1, and the boxed
    line at the foot is Equation (19).
    """
    duct_y, duct_h = 210.0, 64.0
    axis = duct_y + duct_h / 2
    x_fan, w_fan = 45.0, 96.0
    x_sil, w_sil = 330.0, 150.0
    x_room, w_room = 610.0, 250.0

    s.text(450, 92, "One installation, two measurement surfaces", 17, th.fg, bold=True)

    # Source side: the machine and the duct that carries its sound.
    s.rect(x_fan, duct_y - 18, w_fan, duct_h + 36, th.panel, th.fg, rx=6, sw=2.2)
    s.circle(x_fan + w_fan / 2, axis, 17, th.fg)
    s.circle(x_fan + w_fan / 2, axis, 7, th.bg)
    s.text(x_fan + w_fan / 2, duct_y + duct_h + 46, "the machine", 13, th.muted)

    s.rect(
        x_fan + w_fan, duct_y, x_sil - x_fan - w_fan, duct_h, th.panel, th.fg, sw=2.0
    )
    s.rect(
        x_sil + w_sil, duct_y, x_room - x_sil - w_sil, duct_h, th.panel, th.fg, sw=2.0
    )

    # The silencer itself, splitters and all.
    s.rect(x_sil, duct_y - 12, w_sil, duct_h + 24, th.panel, th.primary, rx=5, sw=2.6)
    for k in range(4):
        s.line(
            x_sil + 20 + 32 * k,
            duct_y - 6,
            x_sil + 20 + 32 * k,
            duct_y + duct_h + 6,
            th.primary,
            2.4,
        )
    s.text(
        x_sil + w_sil / 2,
        duct_y - 26,
        "the silencer, as installed",
        13,
        th.primary,
        bold=True,
    )

    # The receiving room, drawn as a room because case 2 makes it one.
    s.rect(x_room, duct_y - 78, w_room, duct_h + 150, "none", th.fg, rx=4, sw=2.2)
    s.text(
        x_room + w_room / 2,
        duct_y + duct_h + 88,
        "the room it discharges into",
        13,
        th.muted,
    )

    # The two measurement surfaces and the distances that place them.
    s.line(
        265.0, duct_y - 42, 265.0, duct_y + duct_h + 42, th.secondary, 2.0, dash="6,4"
    )
    s.text(265.0, duct_y - 56, "$S_2$: the duct cross-section", 13, th.secondary)
    for k in range(3):
        s.circle(265.0, duct_y + 14 + 18 * k, 5, th.secondary)

    s.line(560.0, duct_y - 42, 560.0, duct_y + duct_h + 42, th.accent, 2.0, dash="6,4")
    s.text(700.0, duct_y - 96, "$S_1$: a quarter of the room absorption", 13, th.accent)
    for k in range(3):
        s.circle(x_room + 60 + 70 * k, duct_y - 30 + 34 * k, 5, th.accent)

    s.dim(
        x_fan + w_fan + 6,
        duct_y + duct_h + 78,
        265.0,
        duct_y + duct_h + 78,
        "$d_u$",
        size=14,
    )
    s.dim(
        x_sil + w_sil + 6,
        duct_y + duct_h + 78,
        560.0,
        duct_y + duct_h + 78,
        "$d_d$",
        size=14,
    )
    s.text(196, duct_y + duct_h + 104, "$d_u = 1,5 √(4S_u/π)$", 13, th.muted)
    s.text(523, duct_y + duct_h + 104, "$d_d = 12√S_d − 10√S_f$", 13, th.muted)

    s.arrow(x_fan + w_fan, axis, x_sil - 8, axis, th.fg, 2.0)
    s.arrow(x_sil + w_sil + 8, axis, x_room - 8, axis, th.fg, 2.0)

    # What the two surfaces are worth once they are read.
    s.rect(70, 420, 760, 66, th.panel, th.fg, rx=6, sw=1.6)
    s.text(450, 448, "$D_{ts} = D_{tps} + 10 lg(S_2/S_1) + K_2 − K_1$", 18, th.fg)
    s.text(
        450,
        472,
        "the level difference, the ratio of the two areas, and what the two sides do not share",
        13,
        th.muted,
    )

    s.text(
        450,
        516,
        "Figure 1 draws twenty installations: sixteen give a transmission loss and four an insertion loss",
        13,
        th.muted,
    )
    s.text(
        450,
        538,
        "the source side and the receiver side are each a duct, a diffuse room, a room without one, or open space",
        13,
        th.muted,
    )
    s.text(
        450,
        566,
        "and the flow is measured too: a silencer that is quiet and blocks the duct has not been measured",
        13,
        th.secondary,
    )


def _d_screen_in_situ(s: SVG, th: Theme) -> None:
    """The ISO 11821 measurement: two runs and four distances.

    A removable screen is the one device of the three that can be taken away,
    so the standard asks for the room with it and the room without it, and the
    attenuation is the difference. Where the microphones stand is 5.5.2: a
    quarter, a half, once and twice the screen height, floored at 1 m, which is
    why a low screen is measured at three distances rather than four.
    """
    floor = 430.0
    x_screen = 330.0
    h_screen = 200.0
    top = floor - h_screen

    s.text(
        450, 92, "Two runs, and four distances behind the screen", 17, th.fg, bold=True
    )
    s.ground(floor, 55, 860)

    # The source, which keeps running between the two campaigns.
    s.rect(110, floor - 84, 96, 84, th.panel, th.fg, rx=5, sw=2.2)
    s.circle(158, floor - 42, 15, th.fg)
    s.circle(158, floor - 42, 6, th.bg)
    s.text(158, floor + 30, "the machine, unchanged", 13, th.muted)

    # The screen, and the run without it drawn as its ghost.
    s.rect(x_screen - 9, top, 18, h_screen, th.panel, th.primary, rx=3, sw=2.6)
    s.text(
        x_screen,
        top - 18,
        "the screen: one run with it, one without",
        13,
        th.primary,
        bold=True,
    )
    s.dim(x_screen - 40, floor, x_screen - 40, top, "$h$", size=15, label_side="left")

    # The four microphone positions, with the floor the nearest is held out to.
    for label, x in (
        ("$h/4$", x_screen + 62),
        ("$h/2$", x_screen + 124),
        ("$h$", x_screen + 248),
        ("$2h$", x_screen + 430),
    ):
        s.mic(x, floor - 150, floor, scale=0.85)
        s.text(x, floor - 166, label, 14, th.accent, bold=True)
    s.dim(x_screen + 9, floor + 54, x_screen + 62, floor + 54, "≥ 1 m", size=13)

    # The operator the geometry is written for.
    s.person(x_screen + 248, floor, h=96)
    s.text(
        x_screen + 248, floor - 190, "operator height 1,55 m ± 0,075 m", 13, th.muted
    )

    s.rect(70, 496, 760, 62, th.panel, th.fg, rx=6, sw=1.6)
    s.text(
        450,
        522,
        "$D_p = L_{p1} - L_{p2}$, band by band and position by position",
        17,
        th.fg,
    )
    s.text(
        450,
        546,
        "the smallest attenuation is found at the most remote position and the largest at the nearest",
        13,
        th.muted,
    )
    s.text(
        450,
        588,
        "no microphone stands closer than 1 m, so a screen of 2 m or less is measured at three distances, not four",
        13,
        th.muted,
    )
    s.text(
        450,
        612,
        "an artificial source has to pass the twelve-position directivity test first, and may never give the A-weighted value",
        13,
        th.secondary,
    )


def _d_open_end_solid_angles(s: SVG, th: Theme) -> None:
    """The five mounting configurations of ISO 7235 Table B.1.

    The same five appear as Table 1 of ISO 5135, entry for entry, and they
    are the only thing in Equation (B.3) that a laboratory chooses rather
    than measures. The wedge drawn at each mouth is the solid angle read in
    section: a full circle for the 4 pi of an opening standing free, a half
    for the 2 pi of one flush with a surface, a quarter for the pi of one in
    the corner where two surfaces meet.
    """
    import math as _math

    cells = (
        ("A", "Flush in a wall", "2π", 270.0, 180.0, ("wall",)),
        ("B", "Wall and floor", "π", 270.0, 90.0, ("wall", "floor")),
        ("C", "Free in the room", "4π", 0.0, 360.0, ()),
        ("D", "On the floor", "2π", 180.0, 180.0, ("floor",)),
        ("E", "Duct in free space", "4π", 0.0, 360.0, ()),
    )
    left, cell_w, gap = 26.0, 160.0, 12.0
    top, box_h = 96.0, 178.0

    s.text(
        450,
        62,
        "The solid angle is the only term of Equation (B.3) a laboratory chooses",
        16,
        th.fg,
    )

    for index, (letter, name, omega, start, sweep, surfaces) in enumerate(cells):
        x0 = left + index * (cell_w + gap)
        cx, cy = x0 + cell_w / 2, top + box_h / 2 + 6
        radius = 46.0

        s.rect(x0, top, cell_w, box_h, th.panel, th.muted, rx=6, sw=1.4)

        # The wedge: the solid angle read in section, drawn before the
        # surfaces so a wall lies over its own edge rather than under it.
        if sweep >= 360.0:
            s.circle(cx, cy, radius, th.primary, th.primary, sw=1.2)
        else:
            a0, a1 = _math.radians(start), _math.radians(start + sweep)
            x1, y1 = cx + radius * _math.cos(a0), cy + radius * _math.sin(a0)
            x2, y2 = cx + radius * _math.cos(a1), cy + radius * _math.sin(a1)
            large = 1 if sweep > 180.0 else 0
            s.path(
                f"M {cx:.1f} {cy:.1f} L {x1:.1f} {y1:.1f} "
                f"A {radius:.1f} {radius:.1f} 0 {large} 1 {x2:.1f} {y2:.1f} Z",
                fill=th.primary,
                stroke=th.primary,
                sw=1.2,
            )

        # A surface stops where the wedge does, so the corner of B reads as a
        # corner and not as a cross.
        corner = len(surfaces) == 2
        if "wall" in surfaces:
            s.line(cx, top + 16, cx, cy if corner else top + box_h - 34, th.fg, 5.0)
        if "floor" in surfaces:
            s.line(cx if corner else x0 + 16, cy, x0 + cell_w - 16, cy, th.fg, 5.0)

        # The terminal itself, at the origin of the wedge.
        s.rect(cx - 11, cy - 11, 22, 22, th.bg, th.secondary, rx=3, sw=2.4)
        s.circle(cx, cy, 4.5, th.secondary)

        s.text(x0 + 12, top + 24, letter, 19, th.secondary, anchor="start", bold=True)
        s.text(cx, top + box_h - 14, name, 13, th.fg)
        s.text(cx, top + box_h + 24, f"Ω = {omega}", 17, th.primary, bold=True)

    s.text(
        450,
        326,
        "A full circle in section is 4π: the opening radiates into the whole room. "
        "Half of one is 2π, a quarter is π.",
        13,
        th.muted,
    )
    s.text(
        450,
        372,
        "D_td = 10 lg[1 + Ω / (4πf√S / c)²] dB, "
        "which ISO 5135 prints as ΔL_r = 10 lg[1 + (c / 4πf)² (Ω / S)]",
        16,
        th.fg,
    )
    s.text(
        450,
        400,
        "One formula, two names, and the same five values in ISO 7235 Table B.1 "
        "and ISO 5135 Table 1",
        13,
        th.muted,
    )
    s.text(
        450,
        434,
        "The bigger the solid angle, the more the mouth keeps in",
        15,
        th.accent,
        bold=True,
    )
    s.text(
        450,
        456,
        "a baffle is what makes an opening a good radiator",
        13,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Where the microphone goes at a work station (ISO 11201:2010, Clause 9)
# ---------------------------------------------------------------------------


def _cell(
    s: SVG, th: Theme, x: float, y: float, w: float, h: float, tag: str, name: str
) -> None:
    """One panel of the work-station plate: frame, clause number and name."""
    s.rect(x, y, w, h, th.panel, th.muted, rx=6, sw=1.4)
    s.text(x + 12, y + 22, tag, 15, th.secondary, anchor="start", bold=True)
    s.text(x + w / 2 + 20, y + 22, name, 13, th.fg)


def _height_dim(
    s: SVG, th: Theme, x: float, y_low: float, y_high: float, offset: float
) -> None:
    """A vertical dimension whose number is printed elsewhere.

    ``SVG.dim`` writes the label beside the line, which a three-across cell
    has no room for once the number carries a tolerance; these cells print
    it across the top instead and keep only the arrows here.
    """
    dx = x + offset
    s.line(x, y_low, dx, y_low, th.muted, 0.9, dash="3,3")
    s.line(x, y_high, dx, y_high, th.muted, 0.9, dash="3,3")
    mid = (y_low + y_high) / 2
    s.arrow(dx, mid - 4, dx, y_high, th.muted, 1.2)
    s.arrow(dx, mid + 4, dx, y_low, th.muted, 1.2)


def _d_workstation_microphone(s: SVG, th: Theme) -> None:
    """The five microphone positions of ISO 11201 Clause 9, drawn.

    The emission sound pressure level belongs to a position, and the
    standard spends a whole clause saying which one. Each cell here is one
    of its cases, with the distance the clause prints: beside a head, above
    a seat, above a footprint on the floor, along a path, and around a
    machine that nobody stands at.
    """
    s.text(
        450,
        60,
        "The emission level belongs to a position, and this is the position",
        16,
        th.fg,
    )

    left, gap = 26.0, 13.0
    top1, h1 = 84.0, 214.0
    w1 = (900.0 - 2 * left - 2 * gap) / 3.0

    # --- 9.1  Operator present: the head in plan ---------------------------
    x0 = left
    _cell(s, th, x0, top1, w1, h1, "9.1", "Operator present")
    cx, cy = x0 + w1 / 2 - 30.0, top1 + 108.0
    ydim = cy + 54.0
    s.text(x0 + w1 / 2, top1 + 46, "0.20 m ± 0.02 m", 12, th.fg)
    s.line(cx, top1 + 56, cx, ydim, th.muted, 1.1, dash="4,4")
    s.circle(cx, cy, 20.0, th.panel, th.fg, sw=2.0)
    s.path(
        f"M {cx - 7:.1f} {cy - 18:.1f} L {cx:.1f} {cy - 29:.1f} "
        f"L {cx + 7:.1f} {cy - 18:.1f} Z",
        fill=th.fg,
        stroke=th.fg,
        sw=1.0,
    )
    s.text(cx - 30, cy - 2, "centre plane", 11, th.muted, anchor="end")
    s.arrow(cx, cy - 36, cx, cy - 58, th.muted, 1.4)
    s.text(cx + 12, cy - 46, "line of vision", 11, th.muted, anchor="start")
    mx = cx + 64.0
    s.rect(mx - 5, cy - 15, 10, 24, th.primary, th.primary, rx=4, sw=1.0)
    s.line(mx, cy + 9, mx, ydim, th.muted, 1.1, dash="4,4")
    mid = (cx + mx) / 2
    s.arrow(mid - 4, ydim, cx, ydim, th.muted, 1.2)
    s.arrow(mid + 4, ydim, mx, ydim, th.muted, 1.2)
    s.text(x0 + w1 / 2, top1 + h1 - 34, "on a line with the eyes,", 12, th.fg)
    s.text(x0 + w1 / 2, top1 + h1 - 16, "on the louder side", 12, th.fg)

    # --- 9.2  Seated operator absent ---------------------------------------
    x0 = left + w1 + gap
    _cell(s, th, x0, top1, w1, h1, "9.2", "Seat, nobody in it")
    seat_y = top1 + 146.0
    scx = x0 + w1 / 2 + 8.0
    s.rect(scx - 44, seat_y, 88, 11, th.muted, th.fg, rx=3, sw=1.4)
    s.rect(scx + 33, seat_y - 48, 11, 48, th.muted, th.fg, rx=3, sw=1.4)
    s.line(scx, seat_y + 11, scx, seat_y + 26, th.fg, 2.0)
    s.line(scx - 20, seat_y + 26, scx + 20, seat_y + 26, th.fg, 2.0)
    s.line(scx - 62, seat_y, scx + 58, seat_y, th.primary, 1.1, dash="5,4")
    cap = top1 + 54.0
    s.rect(scx - 5, cap, 10, 24, th.primary, th.primary, rx=4, sw=1.0)
    _height_dim(s, th, scx, seat_y, cap + 24, -56.0)
    s.text(x0 + w1 / 2, top1 + 46, "0.80 m ± 0.05 m", 12, th.fg)
    s.text(x0 + w1 / 2, top1 + h1 - 16, "above the middle of the seat", 12, th.fg)

    # --- 9.3  Standing operator absent -------------------------------------
    x0 = left + 2 * (w1 + gap)
    _cell(s, th, x0, top1, w1, h1, "9.3", "Standing, nobody there")
    gy = top1 + 160.0
    s.ground(gy, x0 + 18, x0 + w1 - 18, hatch=20)
    # Left of centre so the label beside the floor point has the width its
    # longest translation needs before the cell border cuts it.
    gcx = x0 + w1 / 2 - 6.0
    s.circle(gcx, gy, 3.6, th.secondary)
    s.text(gcx + 12, gy - 12, "reference point", 11, th.muted, anchor="start")
    s.mic(gcx, top1 + 62.0, gy, scale=0.8)
    _height_dim(s, th, gcx, gy, top1 + 62.0, -58.0)
    s.text(x0 + w1 / 2, top1 + 46, "1.55 m ± 0.075 m", 12, th.fg)
    s.text(x0 + w1 / 2, top1 + h1 - 16, "the floor below the head", 12, th.fg)

    # --- 9.4  Operator moving along a path ---------------------------------
    top2, h2 = 322.0, 214.0
    w2 = (900.0 - 2 * left - gap) / 2.0
    x0 = left
    _cell(s, th, x0, top2, w2, h2, "9.4", "Operator on a path")
    gy = top2 + 148.0
    s.ground(gy, x0 + 18, x0 + w2 - 18, hatch=20)
    s.line(x0 + 44, gy - 4, x0 + w2 - 44, gy - 4, th.secondary, 2.0, dash="10,6")
    xs = [x0 + 78.0 + k * 84.0 for k in range(4)]
    for x in xs:
        s.mic(x, top2 + 58.0, gy, scale=0.7)
    s.dim(xs[1], top2 + 122, xs[2], top2 + 122, "≤ 2 m", offset=0, size=12)
    s.text(
        x0 + w2 / 2,
        top2 + h2 - 16,
        "same 1.55 m, and the levels are averaged over the path",
        12,
        th.fg,
    )

    # --- 9.5  Nobody at all: the reference box in plan ----------------------
    x0 = left + w2 + gap
    _cell(s, th, x0, top2, w2, h2, "9.5", "No work station")
    s.text(x0 + w2 / 2, top2 + 46, "reference box", 11, th.muted)
    bw, bh = 116.0, 40.0
    bx, by = x0 + w2 / 2 - bw / 2, top2 + 92.0
    bcx, bcy = bx + bw / 2, by + bh / 2
    s.rect(bx, by, bw, bh, "none", th.fg, rx=3, sw=1.6, dash="6,4")
    s.rect(bx + 26, by + 11, bw - 52, bh - 22, th.muted, th.fg, rx=3, sw=1.2)
    # One metre is one metre: the four positions stand the same distance off
    # the face they belong to, which is what the caption claims.
    out = 22.0
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        px = bcx + dx * (bw / 2 + out)
        py = bcy + dy * (bh / 2 + out)
        s.circle(px, py, 6.0, th.primary)
    s.dim(
        bcx,
        by + bh,
        bcx,
        bcy + bh / 2 + out,
        "1 m",
        offset=0,
        size=12,
        label_side="right",
    )
    s.text(
        x0 + w2 / 2,
        top2 + h2 - 34,
        "four or more, 1.55 m above the floor",
        12,
        th.fg,
    )
    s.text(x0 + w2 / 2, top2 + h2 - 16, "and the highest one is the answer", 12, th.fg)

    # --- what the number is, and is not ------------------------------------
    s.text(
        450,
        top2 + h2 + 34,
        "$L_{pA}$ at one of these positions is an emission level, not a sound "
        "power level: it says what the machine does to whoever is there.",
        13,
        th.muted,
    )
    s.text(
        450,
        top2 + h2 + 56,
        "The background correction $K_1$ and the environmental correction "
        "$K_2$ or $K_3$ come off it, and a peak level takes neither.",
        13,
        th.muted,
    )


def _d_in_duct_rig(s: SVG, th: Theme) -> None:
    """The ISO 5136 test arrangement of Figure 5: one fan, a test duct each side.

    The airway runs left to right as Figure 5 draws it: the bell mouth and
    the anechoic termination of the inlet test duct, a transition and an
    intermediate duct as long as the test duct is wide (l1 = d3), the fan,
    then the outlet intermediate duct carrying the star straightener two
    diameters long (5.2.9) with a straight run of d4 on each side of it, a
    transition, and the outlet test duct with its own termination and the
    throttle beyond it (5.2.8). That intermediate duct is the one section
    drawn to a printed limit, (d4/d2)^2 = 1.06, inside the 0.95 to 1.07 of
    Table 4; the test ducts and the transitions are foreshortened, and it
    is the dimensions of 5.2.6 that carry their lengths. Each test duct
    carries a microphone in a sampling tube on a stem through the wall,
    pointing back at the fan (6.1) at the radius of Table 7, and both
    lengths are dimensioned from the fan-side end of the duct. The
    measurement plane sits at 0.63 of the test duct from that end, which
    is 2.52 m of 4 m in a 0.63 m duct at its minimum lengths. Under the
    airway, the measurement plane seen along the duct (Table 7, 6.2.2),
    the sampling tube of Figure 1, and the three ways to the
    circumferential mean with their times (6.2.2, 7.2.2 to 7.2.4). The
    boxed lines are Equations (9) to (12).
    """
    ax = 214.0  # duct axis
    h = 20.0  # test-duct half-height: d is drawn 40 px
    top, bot = ax - h, ax + h
    hf = 16.0  # fan inlet and outlet
    h4 = 16.5  # outlet intermediate duct: (d4/d2)^2 = 1.06, Table 4
    d4 = 2 * h4  # the unit the chain inside l4 is drawn in

    x_bell, x_ti0 = 26.0, 50.0  # bell mouth, far end of the inlet termination
    x_d3a, x_d3b = 110.0, 310.0  # inlet test duct, l3
    x_t31 = x_d3b + 18.0  # transition l31 ends
    x_fan0 = x_t31 + 2 * h  # intermediate duct, l1 = d3
    x_fan1 = x_fan0 + 42.0  # the fan
    x_t24 = x_fan1 + 16.0  # transition l24 ends
    x_st0 = x_t24 + d4  # a straight d4, then the straightener
    x_st1 = x_st0 + 2 * d4  # the straightener is 2 d4 long
    x_t46a = x_st1 + d4  # a straight d4 before the transition
    x_t46b = x_t46a + 18.0  # transition l46 ends
    x_d6a, x_d6b = x_t46b, x_t46b + 200.0  # outlet test duct, l6
    x_to1 = x_d6b + 60.0  # far end of the outlet termination
    # l_m over l for a 0.63 m duct at its minimum lengths: 2.52 m of 4 m.
    lm_frac = 0.63
    x_p3 = x_d3b - lm_frac * (x_d3b - x_d3a)
    x_p6 = x_d6a + lm_frac * (x_d6b - x_d6a)
    r_px = 0.65 * h  # Table 7, sampling tube, d from 0.5 m

    s.text(
        450,
        70,
        "A test duct on each side, and a microphone that points back at the fan",
        16,
        th.fg,
        bold=True,
    )

    # The centre line of the whole airway.
    s.line(14, ax, 872, ax, th.muted, 0.9, dash="12,4,2,4")

    # Air comes in through the bell mouth at the far inlet end: the wall
    # leaves the duct horizontally and turns out into the mouth.
    s.arrow(4, ax, 22, ax, th.fg, 1.8)
    s.text(17, ax - 10, "flow", 11, th.muted)
    for y_wall, dy in ((top, -1.0), (bot, 1.0)):
        s.path(
            f"M {x_ti0} {y_wall} C {x_ti0 - 10} {y_wall} "
            f"{x_bell + 3} {y_wall + dy * 6} {x_bell} {y_wall + dy * 30}",
            stroke=th.fg,
            sw=2.2,
        )

    def termination(x_duct: float, x_far: float) -> None:
        # The anechoic termination as Figure 5 draws it, keys 2 and 5: the
        # passage runs straight through at the duct diameter, which is the
        # closing edge of each absorbent body, and the absorbent flares out
        # around it, square at the open end and tapered on the fan side.
        sign = 1.0 if x_far > x_duct else -1.0
        xm = x_duct + sign * 40
        xc = x_duct + sign * 20
        for y_wall, y_out in ((top, top - 36), (bot, bot + 36)):
            s.path(
                f"M {x_duct} {y_wall} C {xc} {y_wall} {xc + sign * 8} {y_out} "
                f"{xm} {y_out} L {x_far} {y_out} L {x_far} {y_wall} Z",
                fill=th.panel,
                stroke=th.fg,
                sw=2.0,
            )
            dy = -1 if y_out < y_wall else 1
            for k in range(3):
                xh = xm + sign * (3 + 6 * k) - sign * 10
                s.line(
                    xh, y_wall + dy * 3, xh + sign * 9, y_out - dy * 3, th.muted, 1.0
                )

    termination(x_d3a, x_ti0)
    termination(x_d6b, x_to1)

    # The two test ducts, in the colour of what is measured.
    for x0, x1 in ((x_d3a, x_d3b), (x_d6a, x_d6b)):
        s.rect(x0, top, x1 - x0, 2 * h, th.panel)
        s.line(x0, top, x1, top, th.primary, 2.6)
        s.line(x0, bot, x1, bot, th.primary, 2.6)

    # Transitions and intermediate ducts between the test ducts and the fan.
    for x0, h0, x1, h1 in (
        (x_d3b, h, x_t31, hf),
        (x_t31, hf, x_fan0, hf),
        (x_fan1, hf, x_t24, h4),
        (x_t24, h4, x_t46a, h4),
        (x_t46a, h4, x_t46b, h),
    ):
        s.line(x0, ax - h0, x1, ax - h1, th.fg, 2.0)
        s.line(x0, ax + h0, x1, ax + h1, th.fg, 2.0)

    # The star straightener: eight radial vanes, three of them seen edge on.
    s.line(x_st0, ax - h4, x_st0, ax + h4, th.fg, 1.4)
    s.line(x_st1, ax - h4, x_st1, ax + h4, th.fg, 1.4)
    for dy in (-10.0, 0.0, 10.0):
        s.line(x_st0, ax + dy, x_st1, ax + dy, th.fg, 1.6)

    # The fan.
    s.rect(x_fan0, ax - 40, x_fan1 - x_fan0, 80, th.panel, th.fg, rx=5, sw=2.2)
    s.circle((x_fan0 + x_fan1) / 2, ax, 14, th.fg)
    s.circle((x_fan0 + x_fan1) / 2, ax, 5, th.bg)

    # The throttle, at the end of the outlet termination remote from the fan.
    s.line(x_to1 + 8, ax - 16, x_to1 + 8, ax + 16, th.fg, 3.0)
    s.line(x_to1, ax, x_to1 + 22, ax, th.fg, 2.0)
    s.rect(x_to1 + 20, ax - 8, 6, 16, th.fg)
    s.line(x_to1 + 12, ax + 20, x_to1 + 12, bot + 44, th.muted, 0.9)

    # The microphones: a sampling tube on a stem through the wall, at
    # 2r/d = 0.65, nose towards the fan, and the measurement plane dashed.
    for xp, sign in ((x_p3, 1.0), (x_p6, -1.0)):
        y_t = ax - r_px
        xs = xp - sign * 8
        s.line(xs, top - 16, xs, y_t, th.fg, 2.0)
        x_rear = xp - sign * 10
        x_nose = xp + sign * 14
        s.rect(min(x_rear, x_nose), y_t - 3, abs(x_nose - x_rear), 6, th.primary, rx=2)
        s.path(
            f"M {x_nose} {y_t - 3} L {x_nose + sign * 7} {y_t} L {x_nose} {y_t + 3} Z",
            fill=th.fg,
        )
        s.line(xp, top - 4, xp, bot + 4, th.secondary, 1.4, dash="4,3")

    # What each part is.
    s.text(
        (x_d3a + x_d3b) / 2, 118, "inlet test duct, $U$ < 0", 13, th.primary, bold=True
    )
    s.text(
        (x_d6a + x_d6b) / 2, 118, "outlet test duct, $U$ > 0", 13, th.primary, bold=True
    )
    s.text(80, 146, "anechoic termination", 11, th.muted)
    s.text(x_to1 - 30, 146, "anechoic termination", 11, th.muted)
    s.text(x_p3 - 8, 170, "microphone", 11, th.fg)
    s.text(x_p6 + 8, 170, "microphone", 11, th.fg)
    s.text((x_fan0 + x_fan1) / 2, 166, "the fan", 13, th.fg, bold=True)
    # The straightener's own name runs wider than the piece it names, in
    # Spanish wide enough to reach over the fan, so it takes a leader.
    s.text(
        (x_st0 + x_st1) / 2,
        146,
        "star flow straightener, $2d_4$ long",
        11,
        th.muted,
    )
    s.line((x_st0 + x_st1) / 2, 152, (x_st0 + x_st1) / 2, ax - h4 - 4, th.muted, 0.9)
    s.text(
        (x_d3b + x_d6a) / 2,
        bot + 56,
        "transitions and intermediate ducts",
        11,
        th.muted,
    )
    s.text(x_to1 + 12, bot + 58, "throttle", 11, th.muted)

    # The two lengths of 5.2.6, from the fan-side end of each test duct.
    s.dim(x_p3, bot, x_d3b, bot, "$l_{m3}$ ≥ max(4$d_3$, 2 m)", offset=44, size=11)
    s.dim(x_d3a, bot, x_d3b, bot, "$l_3$ ≥ max(6$d_3$, 4 m)", offset=78, size=11)
    s.dim(x_d6a, bot, x_p6, bot, "$l_{m6}$ ≥ max(4$d_6$, 2 m)", offset=44, size=11)
    s.dim(x_d6a, bot, x_d6b, bot, "$l_6$ ≥ max(6$d_6$, 4 m)", offset=78, size=11)

    # The measurement plane seen along the duct: Table 7 and 6.2.2.
    cx, cy, big_r = 160.0, 454.0, 70.0
    rr = 0.65 * big_r
    s.text(cx, 364, "the measurement plane", 13, th.fg, bold=True)
    s.circle(cx, cy, big_r, th.panel, th.fg, sw=2.4)
    s.line(cx - big_r - 8, cy, cx + big_r + 8, cy, th.muted, 0.9, dash="8,3,2,3")
    # The vertical centre line breaks around the angle label it would cross.
    s.line(cx, cy - big_r - 8, cx, cy + 22, th.muted, 0.9, dash="8,3,2,3")
    s.line(cx, cy + 40, cx, cy + big_r + 4, th.muted, 0.9, dash="8,3,2,3")
    s.circle(cx, cy, rr, "none", th.primary, sw=1.4)
    spots = [
        (cx + rr * math.cos(math.radians(a)), cy + rr * math.sin(math.radians(a)))
        for a in (-90.0, 30.0, 150.0)
    ]
    for px, py in spots[1:]:
        s.line(cx, cy, px, py, th.secondary, 1.0)
    a0, a1, ra = math.radians(30.0), math.radians(150.0), 20.0
    s.path(
        f"M {cx + ra * math.cos(a0):.1f} {cy + ra * math.sin(a0):.1f} "
        f"A {ra} {ra} 0 0 1 {cx + ra * math.cos(a1):.1f} {cy + ra * math.sin(a1):.1f}",
        stroke=th.secondary,
        sw=1.4,
    )
    for px, py in spots:
        s.circle(px, py, 6.5, th.primary)
        s.circle(px, py, 2.4, th.bg)
    s.text(cx, cy + 36, "120°", 11, th.secondary)
    s.dim(cx + 3, cy, cx + 3, cy - rr + 7, "$r$", size=13, label_side="right")
    s.dim(
        cx - big_r,
        cy + big_r + 30,
        cx + big_r,
        cy + big_r + 30,
        "$d$ from 0.15 m to 2 m",
        size=12,
    )
    s.text(cx, 578, "$2r/d$ = 0.65 from $d$ = 0.5 m, 0.8 below it", 12, th.fg)
    s.text(cx, 596, "0.5 with a nose cone or a foam ball", 12, th.muted)
    s.text(cx, 616, "0.63 m duct: $r$ = 0.20 m, $l_m$ ≥ 2.52 m", 12, th.primary)

    # The sampling tube of Figure 1, on its support through the duct wall.
    bx = 462.0
    wall_y, tube_y = 394.0, 450.0
    s.text(bx, 364, "the sampling tube", 13, th.fg, bold=True)
    s.line(340, wall_y, 584, wall_y, th.fg, 2.4)
    s.text(584, wall_y - 8, "duct wall", 11, th.muted, anchor="end")
    s.rect(530, wall_y, 8, tube_y - 10 - wall_y, th.fg)
    s.rect(394, tube_y - 10, 170, 20, th.panel, th.fg, rx=4, sw=2.0)
    s.rect(414, tube_y - 4, 96, 8, th.accent, rx=2)
    s.path(f"M 394 {tube_y - 10} L 366 {tube_y} L 394 {tube_y + 10} Z", fill=th.fg)
    s.rect(540, tube_y - 7, 20, 14, th.primary, rx=3)
    s.arrow(358, tube_y, 336, tube_y, th.muted, 1.4)
    s.text(400, tube_y - 22, "nose cone, pointing at the fan", 11, th.muted)
    s.text(440, tube_y + 32, "slit under porous material", 11, th.accent)
    s.text(564, tube_y + 32, "microphone", 11, th.primary)
    s.text(bx, 520, "at most 22 mm across, within ± 5° of the axis", 12, th.fg)
    s.text(bx, 538, "$C_2$: its own response, measured to ± 0.5 dB", 12, th.fg)
    s.text(bx, 556, "$C_{3,4}$: the flow and the modes, from Annex A", 12, th.fg)
    s.text(bx, 578, "usable to 40 m/s; a nose cone to 20 m/s", 12, th.muted)
    s.text(bx, 596, "and a foam ball to 15 m/s", 12, th.muted)

    # The three ways to the circumferential mean, and how long each takes.
    kx = 624.0
    s.text(752, 364, "the mean around the duct", 13, th.fg, bold=True)
    for k, (tag, first, second) in enumerate(
        (
            (
                "a)",
                "one microphone moved round to three",
                "or more equally spaced positions",
            ),
            ("b)", "three or more fixed microphones,", "read in turn or multiplexed"),
            (
                "c)",
                "one microphone traversed once round",
                "at constant speed, in 30 s or more",
            ),
        )
    ):
        y = 400 + 50 * k
        s.text(kx, y, tag, 12, th.primary, anchor="start", bold=True)
        s.text(kx + 22, y, first, 12, th.fg, anchor="start")
        s.text(kx + 22, y + 18, second, 12, th.fg, anchor="start")
    s.text(
        kx, 578, "read in turn: at least 30 s a position", 12, th.muted, anchor="start"
    )
    s.text(kx, 596, "up to 160 Hz, 10 s from 200 Hz;", 12, th.muted, anchor="start")
    s.text(kx, 614, "multiplexed: 30 s a band", 12, th.muted, anchor="start")

    # Equations (9) to (12).
    box_y = 636.0
    s.rect(52, box_y, 796, 80, th.panel, th.primary, rx=6, sw=1.8)
    s.text(
        450,
        box_y + 22,
        "$L̄_p$ = energy mean of the $n$ ≥ 3 readings $L_{pi}$ + $C$,   "
        "$C = C_1 + C_2 + C_{3,4}$",
        15,
        th.fg,
    )
    s.text(
        450,
        box_y + 44,
        "with multiplexing or a traverse, it is $L̄_p = L_{pm} + C$ instead",
        15,
        th.fg,
    )
    s.text(
        450,
        box_y + 66,
        "$L_W = L̄_p + 10 lg(S/S_0) − 10 lg[ρc/(ρc)_0]$,   $S = πd^2/4$,   "
        "$S_0$ = 1 m²,   $(ρc)_0$ = 400 N·s/m³",
        15,
        th.primary,
    )

    s.text(
        450,
        744,
        "type 1 microphone and amplifier, IEC 61260 one-third octaves from 50 Hz "
        "to 10 kHz, class 1 calibrator before and after",
        12,
        th.muted,
    )
    s.text(
        450,
        764,
        "every band at least 6 dB over the background and over the turbulence; "
        "termination $r_a$ ≤ 0.4 at 50 Hz, ≤ 0.15 from 125 Hz",
        12,
        th.muted,
    )
    s.text(
        450,
        784,
        "throttle noise at least 10 dB under the fan; the outlet read with and "
        "without the straightener, the lower level kept",
        12,
        th.muted,
    )


def _d_valve_noise_place(s: SVG, th: Theme) -> None:
    """The place the printed level belongs to, and the path that gets it there.

    Almost nothing escapes through the valve body. The noise of interest is
    made at the vena contracta, travels downstream inside the pipe, and
    reaches the outside through the pipe wall, which is why the method
    spends a whole clause on the wall and none on the body. The number
    everybody quotes is measured a metre downstream of the body and a metre
    off the outer wall.
    """
    s.text(
        450,
        58,
        "Almost nothing comes out of the valve; the pipe wall is the way out",
        16,
        th.fg,
    )

    axis, bore, wall = 272.0, 36.0, 6.0
    x_in, x_out = 66.0, 706.0
    body_x0, body_x1 = 168.0, 248.0
    metre = 118.0
    top_wall = axis - bore - wall

    # --- The pipe, drawn as two walls with a bore between them --------------
    for sign in (-1.0, 1.0):
        y = axis + sign * bore if sign > 0 else axis - bore - wall
        s.rect(x_in, y, x_out - x_in, wall, th.muted, th.fg, rx=1.5, sw=1.2)
    s.text(x_in + 4, axis + 6, "flow", 12, th.muted, anchor="start")
    s.arrow(x_in + 38, axis, x_in + 82, axis, th.muted, 1.6)

    # --- The valve body: a plug closing on a seat, and the throat it leaves -
    s.rect(
        body_x0,
        axis - bore - 58,
        body_x1 - body_x0,
        2 * (bore + 58),
        th.panel,
        th.fg,
        rx=8,
        sw=2.0,
    )
    stem = (body_x0 + body_x1) / 2
    s.rect(stem - 13, axis - bore - 92, 26, 36, th.muted, th.fg, rx=3, sw=1.6)
    s.line(stem, axis - bore - 56, stem, axis - 14, th.fg, 3.0)
    s.rect(stem - 21, axis - 14, 42, 28, th.panel, th.fg, rx=3, sw=1.6)
    for sign in (-1.0, 1.0):
        y = axis + sign * bore
        s.path(
            f"M {body_x0 + 8:.1f} {y:.1f} L {stem + 26:.1f} {y:.1f} "
            f"L {stem + 26:.1f} {axis + sign * 12:.1f} Z",
            fill=th.muted,
            stroke=th.fg,
            sw=1.2,
        )
    s.text(stem, axis - bore - 106, "valve", 12, th.fg)

    # --- The jet, which is the source, and where it starts ------------------
    jet_x0, jet_x1 = stem + 26.0, stem + 232.0
    s.path(
        f"M {jet_x0:.1f} {axis - 12:.1f} L {jet_x1:.1f} {axis - bore + 5:.1f} "
        f"L {jet_x1:.1f} {axis + bore - 5:.1f} L {jet_x0:.1f} {axis + 12:.1f} Z",
        fill=th.primary,
        stroke="none",
        sw=0.0,
    )
    s.circle(jet_x0, axis, 5.0, th.secondary)
    s.line(jet_x0, axis + 16, jet_x0 + 30, axis + bore + 34, th.secondary, 1.2)
    s.text(
        jet_x0 + 34,
        axis + bore + 40,
        "the vena contracta is the source",
        11,
        th.secondary,
        anchor="start",
    )

    # --- Out through the wall, to the point the level is quoted ------------
    mic_x = body_x1 + metre
    mic_y = top_wall - metre
    s.arrow(mic_x, top_wall - 2, mic_x, mic_y + 30, th.secondary, 1.8)
    s.rect(mic_x - 5, mic_y, 10, 26, th.primary, th.primary, rx=4, sw=1.0)
    s.text(mic_x, mic_y - 14, "$L_{pAe,1m}$", 15, th.primary, bold=True)
    # Past the height dimension, low beside it: left of the arrow, the
    # Spanish ran back into the valve body and the witness line beside it.
    s.text(
        mic_x + 74,
        top_wall - 14,
        "through the wall",
        11,
        th.secondary,
        anchor="start",
    )
    s.line(body_x1, top_wall - 68, body_x1, top_wall, th.muted, 0.9, dash="3,3")
    s.dim(body_x1, top_wall - 58, mic_x, top_wall - 58, "1 m", offset=0, size=12)
    dim_x = mic_x + 64.0
    s.line(mic_x + 8, mic_y, dim_x, mic_y, th.muted, 0.9, dash="3,3")
    s.line(mic_x + 8, top_wall, dim_x, top_wall, th.muted, 0.9, dash="3,3")
    s.dim(dim_x, top_wall, dim_x, mic_y, "1 m", offset=0, size=12, label_side="right")

    # --- The second source, where the outlet lets the gas out fast ---------
    out_x = x_out - 60.0
    s.arrow(
        out_x, axis + bore + wall + 54, out_x, axis + bore + wall + 10, th.muted, 1.4
    )
    s.text(
        out_x,
        axis + bore + wall + 70,
        "a fast outlet is a second source,",
        11,
        th.muted,
    )
    s.text(out_x, axis + bore + wall + 86, "added to the first on energy", 11, th.muted)

    s.text(
        450,
        axis + bore + 152,
        "The body is not the path and the valve is not the source:",
        13,
        th.muted,
    )
    s.text(
        450,
        axis + bore + 172,
        "the noise is made where the stream chokes, and the wall decides how "
        "much of it is heard.",
        13,
        th.muted,
    )


# ---------------------------------------------------------------------------
# ISO 4871: declaring and verifying a sound power level
# ---------------------------------------------------------------------------


def _d_noise_declaration_chain(s: SVG, th: Theme) -> None:
    """What ISO 4871 adds to a measured sound power, and how it is checked.

    A calculation chain rather than an arrangement: the arrangements belong to
    the basic standards and are drawn on their own pages. The declaration is
    made for each operating mode (clause 4) by the manufacturer or supplier
    (3.13) from two inputs, the measured value, not rounded (3.12), and its
    uncertainty, K = 1,645 sigma_R, with the 2,5 dB and 4 dB of Annex A.2.2
    when no noise test code gives sigma_R. Both belong to a single machine:
    A.2.3 determines K another way for a batch, so the plate stays on the one
    machine 6.2 verifies. The noise test code picks the form (clause 4): the
    dual number of 3.16, each value rounded and both always stated together
    (clause 5), or the single number of 3.15, the sum rounded once. The
    verification value L_1 is measured under the same noise test code or,
    where there is none, a basic standard of the same or better grade, under
    the same operating conditions (6.1, with Note 20 for a lower grade), and
    6.2 gives the two verdicts, both of them held against the declared value.
    The values are the two operating modes of the declaration example, and
    the two L_1 are the ones the guide verifies.
    """
    s.text(
        450,
        76,
        "What is declared, and how it is verified on a single machine",
        17,
        th.fg,
        bold=True,
    )
    s.text(
        450,
        114,
        "the declaration, by the manufacturer or supplier, for each operating mode",
        13,
        th.muted,
    )

    # The two inputs: the measured value and its uncertainty.
    top1, h1, w = 128.0, 104.0, 380.0
    for x0, head, first, second, values in (
        (
            50.0,
            "1 · the measured value, $L_{WA}$",
            "from a basic standard, preferably grade 2 or better,",
            "on one machine, and not rounded",
            "mode 1: 88 dB · mode 2: 95 dB",
        ),
        (
            470.0,
            "2 · its uncertainty, $K_{WA}$",
            "from the reproducibility $σ_R$ in the noise test code;",
            "without a code, 2.5 dB at grade 2 and 4 dB at grade 3",
            "mode 1: 2 dB · mode 2: 2 dB",
        ),
    ):
        cx = x0 + w / 2
        s.rect(x0, top1, w, h1, th.panel, th.primary, rx=6, sw=1.8)
        s.text(cx, top1 + 26, head, 15, th.primary, bold=True)
        s.text(cx, top1 + 50, first, 12, th.fg)
        s.text(cx, top1 + 68, second, 12, th.fg)
        s.text(cx, top1 + 92, values, 13, th.primary, bold=True)

    # Both inputs feed both forms, and the noise test code chooses between them.
    bus1 = 254.0
    s.line(240, top1 + h1, 240, bus1, th.fg, 1.6)
    s.line(660, top1 + h1, 660, bus1, th.fg, 1.6)
    s.line(240, bus1, 660, bus1, th.fg, 1.6)
    s.arrow(240, bus1, 240, 284, th.fg, 1.6)
    s.arrow(660, bus1, 660, 284, th.fg, 1.6)
    s.text(450, 276, "the noise test code picks the form", 12, th.muted)

    # The two forms of clause 4, with the rounding of 3.16 and 3.15.
    top2, h2 = 286.0, 100.0
    for x0, head, first, second, values in (
        (
            50.0,
            "dual-number form",
            "$L_{WA}$ and $K_{WA}$, each rounded to the nearest",
            "decibel and always stated together",
            "88 dB and 2 dB · 95 dB and 2 dB",
        ),
        (
            470.0,
            "single-number form",
            "$L_{WAd}$, the unrounded sum rounded once: an upper",
            "limit repeated measurements are unlikely to exceed",
            "90 dB · 97 dB",
        ),
    ):
        cx = x0 + w / 2
        s.rect(x0, top2, w, h2, th.panel, th.fg, rx=6, sw=1.8)
        s.text(cx, top2 + 26, head, 15, th.fg, bold=True)
        s.text(cx, top2 + 50, first, 12, th.fg)
        s.text(cx, top2 + 68, second, 12, th.fg)
        s.text(cx, top2 + 90, values, 13, th.primary, bold=True)

    # Whichever form was declared is what the verification is held against, so
    # the bus carries it out to the rail on the right rather than into one box.
    bus2 = 402.0
    s.line(240, top2 + h2, 240, bus2, th.fg, 1.6)
    s.line(660, top2 + h2, 660, bus2, th.fg, 1.6)
    s.line(240, bus2, 845, bus2, th.fg, 1.6)

    # Above the line the maker declares; below it a new measurement checks.
    s.line(40, 420, 860, 420, th.muted, 1.2, dash="6,5")
    s.text(
        50,
        446,
        "the verification: a new measurement on one machine",
        13,
        th.muted,
        "start",
    )

    # The verification value and the conditions of 6.1 that admit it.
    top3 = 462.0
    s.rect(50, top3, 380, 130, th.panel, th.fg, rx=6, sw=1.8)
    s.text(240, top3 + 26, "3 · the verification value, $L_1$", 15, th.fg, bold=True)
    s.text(
        240, top3 + 52, "the same noise test code or, without one, a basic", 12, th.fg
    )
    s.text(
        240, top3 + 70, "standard of the same or better grade of accuracy,", 12, th.fg
    )
    s.text(240, top3 + 88, "and the same operating conditions", 12, th.fg)
    s.text(
        240,
        top3 + 114,
        "a lower grade only by agreement, allowing for it",
        12,
        th.muted,
    )

    # The declared value comes down the right-hand side into both verdicts.
    s.line(845, bus2, 845, 562, th.fg, 1.6)
    s.text(835, 452, "the declared value", 12, th.muted, "end")
    s.arrow(430, top3 + 52, 468, top3 + 34, th.fg, 1.6)
    s.arrow(430, top3 + 78, 468, top3 + 98, th.fg, 1.6)
    for y0, colour, verdict, reading in (
        (top3, th.accent, "declaration verified", "mode 1: $L_1$ = 89 dB ≤ 90 dB"),
        (
            top3 + 70,
            th.secondary,
            "declaration not verified",
            "mode 2: $L_1$ = 98 dB > 97 dB",
        ),
    ):
        s.rect(470, y0, 350, 60, th.panel, colour, rx=6, sw=2.2)
        s.text(645, y0 + 25, verdict, 15, colour, bold=True)
        s.text(645, y0 + 47, reading, 13, th.fg)
        s.arrow(845, y0 + 30, 822, y0 + 30, th.fg, 1.6)

    # The three relations the chain runs on.
    foot = 616.0
    s.rect(40, foot, 820, 74, th.panel, th.fg, rx=6, sw=1.6)
    for cx, relation, colour, source in (
        (145.0, "$K_{WA} = 1.645 σ_R$", th.primary, "one machine, Annex A.2.2"),
        (
            385.0,
            "$L_{WAd} = L_{WA} + K_{WA}$",
            th.fg,
            "clause 3.15, to the nearest decibel",
        ),
        (
            690.0,
            "$L_1 ≤ L_{WAd}$   or   $L_1 ≤ (L_{WA} + K_{WA})$",
            th.accent,
            "clause 6.2, whichever form was declared",
        ),
    ):
        s.text(cx, foot + 32, relation, 16, colour)
        s.text(cx, foot + 56, source, 12, th.muted)

    s.text(
        450,
        716,
        "$L_{pA}$ at the work station is declared the same way, "
        "with a $K_{pA}$ from ISO 11201 to ISO 11204",
        12,
        th.muted,
    )
