#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Diagrams of the simulation guides: the FDTD wave solver.

The subject is the numerical scheme itself rather than any measurement: the
staggered grid of the finite-difference time-domain solver, the leapfrog
that alternates pressure and velocity updates on it, and the *virtual*
arrangements the two solver guides describe in prose -- the near-to-far-field
scattering scene, the fluid-solid contact at three incidences, and the
immersed plate with its probes and its time gate. A virtual measurement has
a geometry exactly as a bench measurement does, and it is as easy to get
wrong.
"""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .canvas import SVG, Theme


def _d_fdtd(s: SVG, th: Theme) -> None:
    """2D acoustic FDTD pipeline (Attenborough & Van Renterghem 2021, Ch. 4)."""
    cx = 450.0
    bw, bh = 700.0, 58.0
    x0 = cx - bw / 2

    # --- Inputs (two feeder boxes) -----------------------------------------
    # 340 px on the Spanish boundary subtitle, which is 315 px against the
    # 262 of its English twin.
    iw = 340.0
    s.rect(x0, 48, iw, bh, th.panel, th.fg, rx=10, sw=2)
    s.text(
        x0 + iw / 2,
        72,
        "Domain  $c(x, y)$, $ρ(x, y)$, $dx$",
        15,
        th.fg,
        "middle",
        bold=True,
    )
    s.text(
        x0 + iw / 2,
        92,
        "square cells; dt from the Courant number",
        11,
        th.muted,
        "middle",
    )
    s.rect(x0 + bw - iw, 48, iw, bh, th.panel, th.fg, rx=10, sw=2)
    s.text(
        x0 + bw - iw / 2, 72, "Geometry and boundaries", 15, th.fg, "middle", bold=True
    )
    s.text(
        x0 + bw - iw / 2,
        92,
        "rigid, impedance or absorbing edges; obstacles",
        11,
        th.muted,
        "middle",
    )
    s.arrow(x0 + iw / 2, 106, cx - 60, 150, th.fg, 1.8)
    s.arrow(x0 + bw - iw / 2, 106, cx + 60, 150, th.fg, 1.8)

    def _step(y: float, l1: str, l2: str, color: str) -> None:
        s.rect(x0, y, bw, bh, th.panel, color, rx=10, sw=2)
        s.text(cx, y + 25, l1, 15, th.fg, "middle", bold=True)
        s.text(cx, y + 45, l2, 11, th.muted, "middle")

    _step(
        150,
        "Sources  $s(t)$ injected at cells  (Eq. 4.11-4.12 grid)",
        "Gaussian pulse, ramped tone or arbitrary sampled signal",
        th.fg,
    )
    _step(
        238,
        "Staggered-grid leapfrog update  (Eqs. 4.11-4.12)",
        "$v ← v − (dt/ρ·dx)·grad p$,  then  $p ← p − (ρc^2·dt/dx)·div v$",
        th.primary,
    )
    _step(
        326,
        "stable while  $CN = c·dt·√2/dx ≤ 1$  (Eqs. 4.13-4.14)",
        "resolve ≥ 10 cells per wavelength to keep dispersion low",
        th.secondary,
    )
    for y0, y1 in ((208, 238), (296, 326), (384, 414)):
        s.arrow(cx, y0, cx, y1, th.fg, 1.8)

    # --- Output -------------------------------------------------------------
    s.rect(x0, 414, bw, bh, "none", th.primary, rx=10, sw=2.4)
    s.text(
        cx,
        439,
        "FDTDResult:  probe histories $p(t)$, field snapshots, .plot()",
        15,
        th.fg,
        "middle",
        bold=True,
    )
    s.text(
        cx,
        459,
        "deterministic: same inputs, bit-identical outputs",
        11,
        th.muted,
        "middle",
    )


def _hatch_band(
    s: SVG, th: Theme, x: float, y: float, w: float, h: float, step: float = 9.0
) -> None:
    """Diagonally hatched band: the drafting mark for an absorbing layer."""
    s.rect(x, y, w, h, th.panel, th.muted, sw=1.2)
    n = int((w + h) / step)
    for i in range(n + 1):
        x0 = x + i * step
        # 45-degree strokes clipped to the band by hand (no clipPath needed).
        xa, ya = x0, y
        xb, yb = x0 - h, y + h
        if xa > x + w:
            ya = y + (xa - (x + w))
            xa = x + w
        if xb < x:
            yb = y + h - (x - xb)
            xb = x
        if ya < y + h and xa > x:
            s.line(xa, ya, xb, yb, th.muted, 0.7)


def _d_ntff_contour(s: SVG, th: Theme) -> None:
    """Near-to-far-field scattering scene of the FDTD guide, to scale.

    The metadiffuser run of ``simulation/fdtd-simulation.mdx`` section 4:
    a 980 x 346 cell domain at dx = 0.5 mm (490 x 173 mm), 60-cell sponges
    on all four sides, the plane-wave injection line just inside the top
    sponge, the five-cell Table-1 panel, the closed contour that captures
    the phasors, and the angle convention of the far field the contour is
    transformed to. Drawn at the true proportions of the snippet the page
    runs, which is the point: the far-field arc is *outside* the box.
    """
    import math

    px = 1428.571  # pixels per metre (700 px = 0.49 m)
    cell = 0.0005 * px  # one grid cell, in pixels
    x0, y0 = 100.0, 360.0  # domain top-left corner

    def gx(col: float) -> float:
        return x0 + col * cell

    def gy(row: float) -> float:
        return y0 + row * cell

    sponge = 60

    # --- Domain, sponges and the injection line ---------------------------
    s.rect(x0, y0, gx(980) - x0, gy(346) - y0, th.bg, th.fg, sw=2)
    _hatch_band(s, th, x0, y0, gx(980) - x0, sponge * cell)
    _hatch_band(s, th, x0, gy(346 - sponge), gx(980) - x0, sponge * cell)
    _hatch_band(s, th, x0, gy(sponge), sponge * cell, (346 - 2 * sponge) * cell)
    _hatch_band(
        s, th, gx(980 - sponge), gy(sponge), sponge * cell, (346 - 2 * sponge) * cell
    )

    y_src = gy(sponge)
    s.line(gx(sponge), y_src, gx(980 - sponge), y_src, th.primary, 2.6)
    for arrow_col in (240, 400, 580, 740):
        s.arrow(gx(arrow_col), y_src + 4, gx(arrow_col), y_src + 26, th.primary, 1.6)
    s.text(
        gx(490),
        y_src + 34,
        'PlaneWaveSource(direction = "down", offset = 60)',
        13,
        th.primary,
        "middle",
        bold=True,
    )

    # --- The panel: five 70 mm cells, 20 mm slits on a 3 mm backing -------
    px_l, px_r = gx(140), gx(840)
    py_t, py_b = gy(160), gy(206)
    s.rect(px_l, py_t, px_r - px_l, py_b - py_t, th.muted, th.fg, sw=1.6)
    for k in range(1, 5):
        s.line(
            px_l + k * (px_r - px_l) / 5,
            py_t,
            px_l + k * (px_r - px_l) / 5,
            py_b,
            th.bg,
            1.2,
        )
    s.line(px_l, gy(200), px_r, gy(200), th.bg, 1.0, dash="4,3")

    # --- The capture contour and its outward normals ----------------------
    cx0, cx1 = gx(120), gx(860)
    cy0, cy1 = gy(120), gy(226)
    s.rect(cx0, cy0, cx1 - cx0, cy1 - cy0, "none", th.secondary, sw=2.4)
    for ax, ay, bx, by, lx, ly in (
        (gx(150), cy0, gx(150), cy0 - 22, gx(150), cy0 - 28),
        (gx(660), cy1, gx(660), cy1 + 22, gx(660), cy1 + 40),
        (cx0, gy(173), cx0 - 22, gy(173), cx0 - 34, gy(173) + 5),
        (cx1, gy(173), cx1 + 22, gy(173), cx1 + 34, gy(173) + 5),
    ):
        s.arrow(ax, ay, bx, by, th.secondary, 1.6)
        s.text(lx, ly, "$n$", 13, th.secondary, "middle", bold=True)

    # Two clearances worth drafting; the other two are in the notes.
    s.dim(gx(178), cy0, gx(178), py_t, "40", offset=0, label_side="left", size=13)
    # The label beside the witness line, just above the sponge: the span is
    # narrower than the "60", which sat on the sponge's hatching and edge.
    s.dim(gx(sponge), gy(300), cx0, gy(300), "", offset=0, size=13)
    s.text(cx0 + 8, gy(284), "60", 13, th.fg, "start")
    s.line(cx0, cy1, cx0, gy(304), th.muted, 0.9, dash="3,3")
    s.line(gx(sponge), gy(sponge), gx(sponge), gy(304), th.muted, 0.9, dash="3,3")

    # --- Far field: an arc that is deliberately outside the domain --------
    ox, oy = gx(490), py_t  # far-field origin
    s.circle(ox, oy, 5.0, th.accent)
    s.text(
        ox,
        gy(148),
        "far-field origin: the centre of the panel face",
        12,
        th.accent,
        "middle",
        bold=True,
    )
    r = 322.0
    pts = []
    for k in range(65):
        a = math.radians(-64.0 + 128.0 * k / 64.0)
        pts.append(f"{ox + r * math.sin(a):.1f} {oy - r * math.cos(a):.1f}")
    s.path("M " + " L ".join(pts), stroke=th.accent, sw=1.6, dash="7,5")
    for ang, lab, anc in (
        (-60.0, "$θ$ = −60°", "end"),
        (0.0, "$θ$ = 0", "middle"),
        (60.0, "$θ$ = +60°", "start"),
    ):
        a = math.radians(ang)
        s.arrow(
            ox + 0.62 * r * math.sin(a),
            oy - 0.62 * r * math.cos(a),
            ox + r * math.sin(a),
            oy - r * math.cos(a),
            th.accent,
            1.8,
        )
        if ang == 0.0:
            s.text(ox + 12, oy - r + 30, lab, 14, th.accent, "start", bold=True)
        else:
            s.text(
                ox + (r + 12) * math.sin(a),
                oy - r * math.cos(a) - 14,
                lab,
                14,
                th.accent,
                anc,
                bold=True,
            )
    # The normal through the origin starts above the two labels centred on
    # it, which it ran straight through from the panel face.
    s.line(ox, y_src + 20, ox, oy - 0.6 * r, th.accent, 1.0, dash="4,4")
    s.text(
        ox,
        oy - r - 40,
        "The far field is evaluated at $r → ∞$, and lives nowhere on the grid:",
        15,
        th.accent,
        "middle",
        bold=True,
    )
    s.text(
        ox,
        oy - r - 18,
        "far_field_from_contour propagates the captured phasors with the "
        "free-space Green function",
        13,
        th.muted,
        "middle",
    )

    # --- Legend and notes -------------------------------------------------
    ny = gy(346) + 30
    _hatch_band(s, th, x0, ny - 13, 26, 16)
    s.text(x0 + 34, ny, "sponge, 60 cells", 13, th.fg, "start")
    s.line(x0 + 168, ny - 5, x0 + 204, ny - 5, th.secondary, 2.4)
    s.text(x0 + 212, ny, "capture contour", 13, th.fg, "start")
    s.line(x0 + 350, ny - 5, x0 + 386, ny - 5, th.primary, 2.6)
    s.text(x0 + 394, ny, "plane-wave injection line", 13, th.fg, "start")

    notes = (
        (
            (
                "Domain 980 × 346 cells at dx = 0.5 mm (490 × 173 mm); at 2 kHz "
                "there are 343 cells per wavelength"
            ),
            th.fg,
        ),
        (
            (
                "Panel: five 70 mm cells, 20 mm slits on a 3 mm backing; the "
                "3.2 mm neck sets dx, not the wavelength"
            ),
            th.fg,
        ),
        (
            (
                "Clearances in cells: 40 ahead of the panel, 20 behind and to the "
                "sides, 60 to every sponge"
            ),
            th.fg,
        ),
        (
            (
                "Sources outside the contour integrate to zero (extinction): the "
                "total-field phasors give the scattered field"
            ),
            th.secondary,
        ),
        (
            (
                "Reference run: the same scene with no panel → "
                "ContourPhasors.subtract() removes the grid residual"
            ),
            th.muted,
        ),
    )
    for k, (txt, col) in enumerate(notes):
        s.text(x0, ny + 32 + 24 * k, txt, 13, col, "start")


def _d_elastic_fluid_solid(s: SVG, th: Theme) -> None:
    """The fluid-solid contact of the elastic guide, at three incidences.

    One interface line carried across three panels: normal incidence, where
    no shear is excited and the solid behaves as a liquid of its own rho and
    c_P; oblique incidence, where Snell refraction splits the transmitted
    wave into P and SV, each with its own critical angle; and the Scholte
    case of the van Vossen benchmark, where total reflection leaves an
    interface wave crawling along the contact. The inset says where the
    interface physically is on the staggered grid, which is what an
    off-by-one row error gets wrong.
    """
    import math

    y_if, top, bot = 320.0, 170.0, 450.0
    panels = ((40.0, 320.0), (330.0, 610.0), (620.0, 890.0))
    heads = (
        "(a) normal incidence",
        "(b) oblique: mode conversion",
        "(c) beyond both critical angles",
    )
    caps = (
        (
            ("$V = (Z_2−Z_1)/(Z_2+Z_1)$ = 0.939", th.fg, True),
            ("no shear is excited, so the steel", th.muted, False),
            ("acts as a liquid of its $ρ$ and $c_P$", th.muted, False),
        ),
        (
            ("critical angles 14.4° and 27.7°", th.fg, True),
            ("between them P is evanescent and", th.muted, False),
            ("the shear wave carries the power", th.muted, False),
        ),
        (
            ("over steel the deficit is 0.03 %", th.fg, True),
            ("the tail reaches ~7 $λ$ up, so no", th.muted, False),
            ("time of flight can separate it", th.muted, False),
        ),
    )

    for (x0, x1), head, cap in zip(panels, heads, caps, strict=True):
        s.rect(x0, top, x1 - x0, y_if - top, th.panel, th.fg, sw=1.6)
        s.rect(x0, y_if, x1 - x0, bot - y_if, th.bg, th.fg, sw=1.6)
        for hx in range(int(x0) + 6, int(x1) - 4, 14):
            s.line(hx, bot, hx + 12, bot - 12, th.muted, 0.8)
        s.line(x0, y_if, x1, y_if, th.primary, 2.6)
        s.text((x0 + x1) / 2, top - 16, head, 14, th.fg, "middle", bold=True)
        for k, (txt, col, bold) in enumerate(cap):
            s.text(
                (x0 + x1) / 2,
                482 + 22 * k,
                txt,
                13 if bold else 12,
                col,
                "middle",
                bold=bold,
            )

    # --- (a) normal incidence ---------------------------------------------
    ax = 180.0
    s.text(48, top + 18, "water 1480", 11, th.muted, "start")
    s.text(48, y_if + 20, "steel 5958 / 3185", 11, th.muted, "start")
    s.arrow(ax - 26, top + 30, ax - 26, y_if - 8, th.fg, 2.2)
    s.arrow(ax + 26, y_if - 8, ax + 26, top + 30, th.accent, 2.2)
    s.text(ax - 34, top + 74, "incident", 12, th.fg, "end")
    s.text(ax + 34, top + 74, "reflected", 12, th.accent, "start")
    s.arrow(ax, y_if + 8, ax, y_if + 72, th.primary, 2.0)
    s.text(ax + 10, y_if + 56, "P only", 12, th.primary, "start")

    # --- (b) oblique incidence with mode conversion -----------------------
    bx = 470.0
    s.line(bx, top + 30, bx, bot - 8, th.muted, 0.9, dash="4,4")
    th_i, r_in = math.radians(22.0), 122.0
    s.arrow(
        bx - r_in * math.sin(th_i),
        y_if - r_in * math.cos(th_i),
        bx - 6,
        y_if - 4,
        th.fg,
        2.2,
    )
    s.arrow(
        bx + 6,
        y_if - 4,
        bx + r_in * math.sin(th_i),
        y_if - r_in * math.cos(th_i),
        th.accent,
        2.2,
    )
    for ang, col, lab in ((62.0, th.primary, "P"), (30.0, th.secondary, "SV")):
        a = math.radians(ang)
        s.arrow(bx, y_if + 4, bx + 88 * math.sin(a), y_if + 88 * math.cos(a), col, 2.0)
        s.text(
            bx + 98 * math.sin(a) + 6,
            y_if + 88 * math.cos(a) + 5,
            lab,
            13,
            col,
            "start",
            bold=True,
        )
    s.text(bx - 12, y_if - 58, "$θ$", 14, th.fg, "end")
    s.circle(bx, y_if - 96, 5.5, th.primary)
    # One line across the top of the panel, above the normal and both rays:
    # beside the probe, the reflected ray ran through the second of its two
    # lines, and the incident ray would on the other side.
    s.text(bx, top + 20, "probe on the normal, 0.12 m up", 11, th.primary)

    # --- (c) the Scholte case ---------------------------------------------
    cx = 755.0
    s.text(628, top + 18, "water 1500", 11, th.muted, "start")
    s.text(628, y_if + 74, "sediment 3500 / 2000", 11, th.muted, "start")
    s.circle(cx - 78, y_if - 92, 6.0, th.secondary)
    s.text(cx - 68, y_if - 96, "shot, 10 m up", 11, th.secondary, "start")
    pts = [
        f"{cx - 46 + 2.7 * k:.1f} {y_if - 12 * math.sin(k * 0.9):.1f}"
        for k in range(41)
    ]
    s.path("M " + " L ".join(pts), stroke=th.accent, sw=2.2)
    for dy in (-34.0, 34.0):
        s.line(cx - 46, y_if + dy, cx + 62, y_if + dy, th.primary, 1.0, dash="3,4")
    s.text(cx + 6, y_if - 46, "evanescent both sides", 11, th.muted)
    s.arrow(cx + 68, y_if - 14, cx + 110, y_if - 14, th.accent, 1.8)
    s.text(cx + 89, y_if - 20, "1436 m/s", 11, th.accent)

    # --- Where the interface physically is --------------------------------
    ix0, iy0 = 190.0, 556.0
    # 640 px wide: the Spanish of the three lines beside the sketch ran out
    # through the right-hand side at 520.
    s.rect(ix0 - 40, iy0, 640, 96, th.panel, th.muted, rx=10, sw=1.4, dash="6,5")
    s.line(ix0 + 26, iy0 + 48, ix0 + 146, iy0 + 48, th.primary, 2.6)
    for k in range(4):
        s.line(
            ix0 + 26 + 40 * k,
            iy0 + 20,
            ix0 + 26 + 40 * k,
            iy0 + 76,
            th.muted,
            0.8,
            dash="3,3",
        )
    s.line(ix0 + 26, iy0 + 20, ix0 + 146, iy0 + 20, th.muted, 0.8, dash="3,3")
    s.line(ix0 + 26, iy0 + 76, ix0 + 146, iy0 + 76, th.muted, 0.8, dash="3,3")
    s.text(ix0 + 86, iy0 + 16, "last fluid row", 11, th.muted)
    s.text(ix0 + 86, iy0 + 90, "first solid row", 11, th.muted)
    s.text(
        ix0 + 164,
        iy0 + 30,
        "A region painted from row $i$ down puts the contact on the",
        12,
        th.fg,
        "start",
    )
    s.text(
        ix0 + 164,
        iy0 + 52,
        "face plane $y = i·dx$: density averaged arithmetically onto",
        12,
        th.fg,
        "start",
    )
    s.text(
        ix0 + 164,
        iy0 + 74,
        "the faces, shear modulus harmonically onto the corners",
        12,
        th.fg,
        "start",
    )

    s.text(
        450,
        686,
        "Sponge bands line the outer edges of every panel; no side is "
        "both free and absorbing",
        12,
        th.muted,
    )


def _d_immersed_plate_tl(s: SVG, th: Theme) -> None:
    """The immersed-plate transmission scene of the elastic guide, to scale.

    Left, the strip the run actually builds: 0.75 m of water at dx = 0.5 mm,
    three cells wide, with a 10 mm steel plate at 0.35 m, the one-way plane
    pulse and the two probes, all at their true heights. Right, what the two
    probes record and why the 65 us gate separates the incident pulse from
    its plate reflection exactly, plus the half-wave resonance that makes the
    plate transparent at 297.9 kHz.
    """
    import math

    y_top, y_bot = 108.0, 588.0  # 0.75 m of water column
    x_l, x_r = 250.0, 306.0  # the strip, widened to be legible

    def gy(metres: float) -> float:
        return y_top + metres / 0.75 * (y_bot - y_top)

    def leader(y_txt: float, y_feat: float, colour: str) -> None:
        s.arrow(238.0, y_txt - 5, x_l - 5, y_feat, colour, 1.1)

    s.rect(x_l, y_top, x_r - x_l, y_bot - y_top, th.panel, th.fg, sw=1.8)
    s.rect(x_l, gy(0.35), x_r - x_l, gy(0.36) - gy(0.35), th.muted, th.fg, sw=1.6)
    s.line(x_l + 6, gy(0.25), x_r - 6, gy(0.25), th.secondary, 2.6)
    for xx in (x_l + 16, (x_l + x_r) / 2, x_r - 16):
        s.arrow(xx, gy(0.25) + 4, xx, gy(0.29), th.secondary, 1.5)
    for y_m in (0.32, 0.41):
        s.circle((x_l + x_r) / 2, gy(y_m), 6.0, th.primary)

    for y_txt, y_feat, txt, colour, bold in (
        (170.0, gy(0.25), "1.5 mm plane pulse, 0.25 m", th.secondary, True),
        (192.0, gy(0.25), "one-way; usable to 340 kHz", th.muted, False),
        (300.0, gy(0.32), "probe A, 30 mm above", th.primary, True),
        (352.0, gy(0.355), "10 mm STEEL at $y$ = 0.35 m", th.fg, True),
        (374.0, gy(0.355), "painted into WATER", th.muted, False),
        (430.0, gy(0.41), "probe B, 50 mm below", th.primary, True),
    ):
        s.text(232.0, y_txt, txt, 12, colour, "end", bold=bold)
        if bold:
            leader(y_txt, y_feat, colour)

    s.dim(
        x_r + 42,
        y_top,
        x_r + 42,
        y_bot,
        "0.75 m",
        offset=0,
        label_side="right",
        size=13,
    )
    s.line(x_r, y_top, x_r + 42, y_top, th.muted, 0.9, dash="3,3")
    s.line(x_r, y_bot, x_r + 42, y_bot, th.muted, 0.9, dash="3,3")
    s.text((x_l + x_r) / 2, 616.0, "Three cells wide:", 12, th.muted)
    s.text(
        (x_l + x_r) / 2, 636.0, "a 1D problem in a 2D solver, dx = 0.5 mm", 12, th.muted
    )

    # --- What the two probes record ---------------------------------------
    # Starting 22 px further right, so that the probes' names end clear of
    # the 0.75 m dimension, whose line ran through their first letters.
    tx0, tw = 430.0, 398.0
    ta, tb = 192.0, 300.0

    def _pulse(cus: float, base: float, colour: str, amp: float) -> None:
        pts = []
        for k in range(49):
            us = cus - 12.0 + 0.5 * k
            xx = tx0 + tw * us / 160.0
            pts.append(
                f"{xx:.1f} {base - amp * math.exp(-(((us - cus) / 4.0) ** 2)):.1f}"
            )
        s.path("M " + " L ".join(pts), stroke=colour, sw=2.0)

    x_gate = tx0 + tw * 65.0 / 160.0
    s.rect(tx0, ta - 44, x_gate - tx0, 44, th.panel, th.accent, sw=1.4, dash="5,4")
    s.text(
        (tx0 + x_gate) / 2,
        ta - 52,
        "65 µs gate: the incident pulse alone",
        12,
        th.accent,
        bold=True,
    )
    for base, lab in ((ta, "probe A"), (tb, "probe B")):
        s.line(tx0, base, tx0 + tw, base, th.muted, 1.2)
        s.text(tx0 - 10, base + 5, lab, 12, th.primary, "end", bold=True)
    _pulse(47.0, ta, th.secondary, 30.0)
    _pulse(88.0, ta, th.fg, 18.0)
    s.text(tx0 + tw * 47.0 / 160.0, ta + 20, "incident, 47 µs", 11, th.secondary)
    s.text(tx0 + tw * 88.0 / 160.0, ta + 20, "reflection, 88 µs", 11, th.fg)
    _pulse(74.0, tb, th.primary, 13.0)
    s.text(tx0 + tw * 74.0 / 160.0, tb - 44, "transmitted ring-down;", 11, th.primary)
    s.text(tx0 + tw * 74.0 / 160.0, tb - 28, "no echo in the record", 11, th.muted)
    for tick in (0, 40, 80, 120, 160):
        xx = tx0 + tw * tick / 160.0
        s.line(xx, tb + 6, xx, tb + 13, th.muted, 1.0)
        s.text(xx, tb + 30, str(tick), 10, th.muted)
    s.text(tx0 + tw / 2, tb + 52, "time [µs]", 11, th.muted)

    s.text(618, 400, "$TL(f) = 20 log_{10} |I(f) / T(f)|$", 17, th.fg, bold=True)
    s.text(618, 424, "$I$ from the gated probe A, $T$ from probe B", 12, th.muted)

    # --- The half-wave resonance inside the plate -------------------------
    s.rect(408, 448, 420, 140, "none", th.muted, rx=10, sw=1.4, dash="6,5")
    s.text(618, 476, "Inside the plate, at half-wave thickness", 14, th.fg, bold=True)
    pl, pr, pmid = 528.0, 708.0, 508.0
    s.rect(pl, pmid - 16, pr - pl, 32, th.muted, th.fg, sw=1.4)
    pts = []
    for k in range(61):
        xx = pl + (pr - pl) * k / 60.0
        pts.append(f"{xx:.1f} {pmid - 22 * math.sin(math.pi * k / 60.0):.1f}")
    s.path("M " + " L ".join(pts), stroke=th.accent, sw=2.2)
    s.text(
        618,
        550,
        "$f_n = n c_P / (2h)$ = 297.9 kHz for 10 mm of steel",
        13,
        th.accent,
        bold=True,
    )
    s.text(
        618,
        572,
        "the plate goes transparent there, three decades above audio",
        11,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Where each field lives on the staggered grid of the two solvers
# ---------------------------------------------------------------------------


def _edge_hatch(s: SVG, th: Theme, x0: float, y0: float, length: float) -> None:
    """Hatch outside the top and the left side of a patch: the domain edge."""
    for k in range(int(length // 12) + 1):
        s.line(x0 + 12 * k, y0, x0 + 12 * k + 8, y0 - 8, th.muted, 0.9)
        s.line(x0, y0 + 12 * k, x0 - 8, y0 + 12 * k + 8, th.muted, 0.9)


def _staggered_patch(
    s: SVG, th: Theme, x0: float, y0: float, cell: float, n: int, *, elastic: bool
) -> None:
    """The top-left ``n`` by ``n`` cells of a domain, with every field marked.

    The layout of ``FDTD2D`` and ``ElasticFDTD2D``: a dot at each cell centre
    (``p``, or ``txx`` and ``tyy``), an arrow across each interior x-face
    (``vx``) and each interior y-face (``vy``) and, for the elastic solver, a
    diamond on each interior corner (``txy``). The top and the left side are
    the domain edge, drawn thick and hatched, and carry no mark: neither
    engine stores a face or a corner there. The right and the bottom side
    run on, so their faces and corners are interior ones.
    """
    size, tail = n * cell, 14.0
    s.rect(x0, y0, size, size, th.panel)
    for k in range(1, n + 1):
        s.line(x0 + k * cell, y0, x0 + k * cell, y0 + size + tail, th.muted, 1.0)
        s.line(x0, y0 + k * cell, x0 + size + tail, y0 + k * cell, th.muted, 1.0)
    _edge_hatch(s, th, x0, y0, size + tail)
    s.line(x0, y0, x0 + size + tail, y0, th.fg, 2.6)
    s.line(x0, y0, x0, y0 + size + tail, th.fg, 2.6)
    centres = [(k + 0.5) * cell for k in range(n)]
    faces = [k * cell for k in range(1, n + 1)]
    for cy in centres:
        for cx in centres:
            s.circle(x0 + cx, y0 + cy, 6.5, th.primary)
        for fx in faces:
            s.arrow(x0 + fx - 14, y0 + cy, x0 + fx + 14, y0 + cy, th.secondary, 2.2)
    for fy in faces:
        for cx in centres:
            s.arrow(x0 + cx, y0 + fy - 14, x0 + cx, y0 + fy + 14, th.accent, 2.2)
    if elastic:
        for fy in faces:
            for fx in faces:
                x, y = x0 + fx, y0 + fy
                s.path(
                    f"M {x - 7:.1f} {y:.1f} L {x:.1f} {y - 7:.1f} "
                    f"L {x + 7:.1f} {y:.1f} L {x:.1f} {y + 7:.1f} Z",
                    fill=th.fg,
                    stroke=th.bg,
                    sw=1.2,
                )
    for k, c in enumerate(centres):
        s.text(x0 + c, y0 - 20, f"ix = {k}" if k == 0 else str(k), 11, th.muted)
        s.text(
            x0 - 16, y0 + c + 4, f"iy = {k}" if k == 0 else str(k), 11, th.muted, "end"
        )


def _d_fdtd_staggered_cell(s: SVG, th: Theme) -> None:
    """Where ``FDTD2D`` keeps pressure and velocity, in space and in time.

    Left, the top-left cells of a domain as the engine stores them: ``p`` at
    the cell centres, shape ``(ny, nx)``; ``vx`` on the interior x-faces,
    shape ``(ny, nx - 1)``; ``vy`` on the interior y-faces, shape
    ``(ny - 1, nx)``; no face on the domain edge, which is what makes it a
    rigid wall (Attenborough & Van Renterghem 2021, Eq. 4.32, and the cell
    centres and faces of page 123). Right, the leapfrog of Eqs. 4.11-4.12,
    with the pressure at whole steps and the velocity half a step later, and
    the one face an impedance side adds: the wall-face velocity ``vb``, whose
    gradient is taken over half a cell and closed by the surface impedance
    (Eqs. 4.33-4.35).
    """
    x0, y0, cell, n = 80.0, 100.0, 116.0, 3
    size = n * cell
    _staggered_patch(s, th, x0, y0, cell, n, elastic=False)
    mid = 1.5 * cell
    s.text(x0 + mid, y0 + mid + 26, "p", 13, th.primary, bold=True, mono=True)
    # Each tag beside a mark of a cell of its own: three in one cell read as
    # one label.
    s.text(
        x0 + cell + 8,
        y0 + cell / 2 - 14,
        "vx",
        13,
        th.secondary,
        "start",
        bold=True,
        mono=True,
    )
    s.text(
        x0 + 2.5 * cell + 10,
        y0 + cell - 20,
        "vy",
        13,
        th.accent,
        "start",
        bold=True,
        mono=True,
    )
    # The dimension sits clear of the vy arrowheads on the bottom faces.
    s.dim(x0 + cell, y0 + size + 44, x0 + 2 * cell, y0 + size + 44, "$dx$", size=12)
    s.text(
        x0 + size / 2,
        y0 + size + 76,
        "rows grow downward, as an image is drawn",
        11,
        th.muted,
    )

    # --- What is stored, and where ----------------------------------------
    lx = 500.0
    s.text(lx, 90, "What is stored, and where", 14, th.fg, "start", bold=True)
    rows = (
        (
            "p at the cell centres, shape (ny, nx)",
            "centre of cell (ix, iy): ((ix + 1/2)·dx, (iy + 1/2)·dx)",
        ),
        (
            "vx on the interior x-faces, shape (ny, nx − 1)",
            "vx[iy, ix] lies between p[iy, ix] and p[iy, ix + 1]",
        ),
        (
            "vy on the interior y-faces, shape (ny − 1, nx)",
            "vy[iy, ix] lies between p[iy, ix] and p[iy + 1, ix]",
        ),
        (
            "no face is stored on the domain edge:",
            "zero normal velocity, a rigid wall (Eq. 4.32)",
        ),
    )
    for k, (head, tail) in enumerate(rows):
        y = 120.0 + 46 * k
        if k == 0:
            s.circle(lx + 10, y - 4, 6.5, th.primary)
        elif k == 1:
            s.arrow(lx - 2, y - 4, lx + 22, y - 4, th.secondary, 2.2)
        elif k == 2:
            s.arrow(lx + 10, y - 16, lx + 10, y + 8, th.accent, 2.2)
        else:
            s.line(lx - 2, y - 2, lx + 22, y - 2, th.fg, 2.6)
            for h in range(3):
                s.line(lx + 8 * h, y - 2, lx + 8 * h + 7, y - 9, th.muted, 0.9)
        s.text(lx + 34, y, head, 12, th.fg, "start")
        s.text(lx + 34, y + 17, tail, 11, th.muted, "start")

    # --- Half a step apart in time ----------------------------------------
    ty = 326.0
    s.text(
        lx,
        ty,
        "Half a step apart in time (Eqs. 4.11-4.12)",
        14,
        th.fg,
        "start",
        bold=True,
    )
    axis_y, mark_y = ty + 82, ty + 50
    ticks = (540.0, 640.0, 740.0, 840.0)
    s.line(510, axis_y, 870, axis_y, th.fg, 1.4)
    for x, label in zip(
        ticks, ("$n$", "$n$ + 1/2", "$n$ + 1", "$n$ + 3/2"), strict=True
    ):
        s.line(x, axis_y - 5, x, axis_y + 5, th.fg, 1.4)
        s.text(x, axis_y + 22, label, 12, th.fg)
    for k, x in enumerate(ticks):
        if k % 2 == 0:
            s.circle(x, mark_y, 6.5, th.primary)
            s.text(x, mark_y - 16, "p", 12, th.primary, bold=True, mono=True)
        else:
            s.arrow(x - 12, mark_y, x + 12, mark_y, th.secondary, 2.2)
            s.text(x, mark_y - 16, "vx, vy", 12, th.secondary, bold=True, mono=True)
    for (xa, xb), label in zip(
        itertools.pairwise(ticks), ("Eq. 4.11", "Eq. 4.12", "Eq. 4.11"), strict=True
    ):
        s.arrow(xa + 20, mark_y, xb - 20, mark_y, th.muted, 1.2)
        s.text((xa + xb) / 2, mark_y + 18, label, 10, th.muted)

    # --- The one face an impedance side adds ------------------------------
    by = 470.0
    s.text(
        lx, by, "An impedance side keeps one more face", 14, th.fg, "start", bold=True
    )
    bx, top, side = 520.0, by + 22, 70.0
    wall = bx + side
    s.rect(bx, top, side, side, th.panel, th.muted, sw=1.0)
    for k in range(6):
        s.line(wall, top + 12 * k + 8, wall + 8, top + 12 * k, th.muted, 0.9)
    s.line(wall, top - 6, wall, top + side + 6, th.fg, 2.6)
    s.circle(bx + side / 2, top + side / 2, 6.5, th.primary)
    s.arrow(wall - 14, top + side / 2, wall + 16, top + side / 2, th.secondary, 2.2)
    s.text(
        wall + 22,
        top + side / 2 + 4,
        "vb",
        13,
        th.secondary,
        "start",
        bold=True,
        mono=True,
    )
    s.dim(bx + side / 2, top + side + 22, wall, top + side + 22, "$dx$/2", size=11)
    notes = (
        "the wall face stores its own velocity vb;",
        "the pressure gradient is taken over half",
        "a cell, and $p_{surf} = Z·v_{out}$ closes it",
        "(Eqs. 4.33-4.35)",
    )
    note_size = s.fit_size(notes, (11, 10), 236.0, upright=("p_surf",))
    for k, line in enumerate(notes):
        s.text(
            648,
            top + 14 + 17 * k,
            line,
            note_size,
            th.fg,
            "start",
            upright=("p_surf",),
        )


def _d_elastic_staggered_cell(s: SVG, th: Theme) -> None:
    """The staggered cell of the acoustic solver beside that of the elastic one.

    (a) is the cell of ``FDTD2D`` and (b) that of ``ElasticFDTD2D``: the cell
    of Virieux (1986, Fig. 1) shifted half a cell, so that the normal stresses
    ``txx`` and ``tyy`` fall on the cell centres where the acoustic pressure
    lives, ``vx`` and ``vy`` on the same faces and the shear stress ``txy`` on
    the interior corners, shape ``(ny - 1, nx - 1)``. The notes under (b)
    are the effective parameters the engine builds its maps with: the
    density averaged arithmetically onto each face (Moczo et al. 2007,
    Eq. 7.39) and the shear modulus harmonically onto each corner, zero when
    any of the four cells is a fluid (Eq. 7.38). Both leapfrog alike,
    velocities half a step from the pressure or the stresses (Virieux's
    explicit scheme, Eq. 5).
    """
    y0, cell, n = 118.0, 120.0, 2
    size = n * cell
    panels = (
        (80.0, "(a) acoustic: p, vx, vy", False),
        (520.0, "(b) elastic: Virieux's cell, shifted half a cell", True),
    )
    for x0, head, elastic in panels:
        _staggered_patch(s, th, x0, y0, cell, n, elastic=elastic)
        s.text(x0 + size / 2, y0 - 48, head, 14, th.fg, bold=True)
        s.text(
            x0 + cell / 2,
            y0 + cell / 2 + 26,
            "txx, tyy" if elastic else "p",
            13,
            th.primary,
            bold=True,
            mono=True,
        )
        s.text(
            x0 + cell + 8,
            y0 + cell / 2 - 14,
            "vx",
            13,
            th.secondary,
            "start",
            bold=True,
            mono=True,
        )
        s.text(
            x0 + 1.5 * cell + 10,
            y0 + cell - 20,
            "vy",
            13,
            th.accent,
            "start",
            bold=True,
            mono=True,
        )
        if elastic:
            s.text(
                x0 + cell + 12,
                y0 + cell + 20,
                "txy",
                13,
                th.fg,
                "start",
                bold=True,
                mono=True,
            )

    ny = y0 + size + 56
    acoustic = (
        "p at the cell centres, shape (ny, nx)",
        "vx on the interior x-faces, shape (ny, nx − 1)",
        "vy on the interior y-faces, shape (ny − 1, nx)",
        "no face on the domain edge: a rigid wall",
    )
    elastic_notes = (
        "txx and tyy at the cell centres, where p lives",
        "vx and vy on the same faces as in (a)",
        "txy on the interior corners, shape (ny − 1, nx − 1)",
        "$ρ$ onto a face: arithmetic mean of its two cells",
        "(Moczo et al. 2007, Eq. 7.39)",
        "$μ$ onto a corner: harmonic mean of its four cells,",
        "zero when any of them is a fluid (Eq. 7.38)",
        "no txy on the domain edge: a shear-free rigid wall",
    )
    for k, line in enumerate(acoustic):
        s.text(40, ny + 20 * k, line, 12, th.fg, "start")
    size_b = s.fit_size(elastic_notes, (12, 11), 420.0)
    for k, line in enumerate(elastic_notes):
        s.text(456, ny + 20 * k, line, size_b, th.fg, "start")
    s.text(
        450,
        ny + 20 * len(elastic_notes) + 24,
        "Both leapfrog alike: vx and vy half a step from p or from the stresses "
        "(Virieux 1986, Eq. 5)",
        12,
        th.muted,
    )


def _d_compute_map(s: SVG, th: Theme) -> None:
    """Where a simulation steps and where its video is encoded, on one sheet.

    The map of ``simulation/where-it-runs.mdx``, and of section 1 of
    ``simulation/remote-node.mdx``, which walks the node branch in prose. No
    standard stands behind it: every box is the library's own behaviour, and
    each was read off the code before it was drawn.

    Upper lane. The run record (``FDTDRun`` or ``ElasticRun``) and the
    ``Compute`` record (``simulation/compute.py``: ``device``, ``dtype``,
    ``host``, ``fallback``) go into one of the four functions that take a
    host. With ``host=None`` the run steps here on one of the five devices
    of ``Compute.device``; with a host it goes to a node, in the five steps
    of the remote-node guide. Both end in ``result.provenance``
    (``RunProvenance``: ``device``, ``dtype``, ``host``, ``gpu``,
    ``package_sha256``), and ``fallback=True`` brings a failed device, node
    or connection back to NumPy here, with a ``ComputeFallbackWarning``.

    Lower lane. ``VideoOptions(encoder="auto")`` tries the kinds of encoder
    in the order of ``_internal/video_encoders.AUTO_ORDER``: NVENC, Quick
    Sync, VAAPI, VideoToolbox, then the CPU, each candidate with a trial
    encode of one frame, and the first that passes writes the video. The
    names under the boxes are the ``encoder=`` literals of that module.
    """
    left, right = 40.0, 860.0
    centre = (left + right) / 2

    def card(
        x0: float,
        y0: float,
        w: float,
        h: float,
        head: str,
        note: str,
        stroke: str,
        *,
        sw: float = 2.0,
    ) -> None:
        """A record or a function: its name as typed, and what it is."""
        s.rect(x0, y0, w, h, th.panel, stroke, rx=10, sw=sw)
        head_size = s.fit_size((head,), (14, 13, 12, 11), w - 24, bold=True, mono=True)
        s.text(x0 + w / 2, y0 + 26, head, head_size, th.fg, bold=True, mono=True)
        note_size = s.fit_size((note,), (12, 11), w - 24)
        s.text(x0 + w / 2, y0 + 47, note, note_size, th.muted)

    # === Upper lane: where a simulation steps =============================
    s.text(left, 68, "Where a simulation steps", 15, th.fg, "start", bold=True)

    in_y, in_h, in_w = 82.0, 62.0, 395.0
    card(
        left,
        in_y,
        in_w,
        in_h,
        "FDTDRun  |  ElasticRun",
        "the run: what to simulate, checked when it is built",
        th.fg,
    )
    card(
        right - in_w,
        in_y,
        in_w,
        in_h,
        "Compute(device, dtype, host)",
        "where it steps, passed as compute=",
        th.fg,
    )

    call_y, call_h = 176.0, 62.0
    card(
        left,
        call_y,
        right - left,
        call_h,
        "fdtd_simulation  |  elastic_fdtd_simulation  |  write_fdtd_animation"
        "  |  write_elastic_fdtd_animation",
        "the same call here and on a node; an engine built directly"
        " (FDTD2D, ElasticFDTD2D) steps in this process only",
        th.fg,
    )
    for x in (left + in_w / 2, right - in_w / 2):
        s.arrow(x, in_y + in_h, x, call_y - 2, th.fg, 1.8)

    # --- The fork: here, or on a node -------------------------------------
    fork_y, fork_h = 290.0, 196.0
    # The node's five steps are sentences and the devices are names: the
    # node takes the wider share, and both hold their Spanish at 11 px.
    here_w, node_w = 330.0, 470.0
    node_x = right - node_w
    here_mid, node_mid = left + here_w / 2, node_x + node_w / 2
    s.rect(left, fork_y, here_w, fork_h, th.panel, th.primary, rx=10, sw=2.2)
    s.rect(node_x, fork_y, node_w, fork_h, th.panel, th.accent, rx=10, sw=2.2)
    s.arrow(here_mid, call_y + call_h, here_mid, fork_y - 2, th.primary, 1.8)
    s.arrow(node_mid, call_y + call_h, node_mid, fork_y - 2, th.accent, 1.8)
    s.text(here_mid + 12, 270, "host=None", 12, th.primary, "start", mono=True)
    s.text(node_mid + 12, 270, 'host="nas"', 12, th.accent, "start", mono=True)

    s.text(here_mid, fork_y + 26, "Here, on the device asked for", 14, bold=True)
    device_size = s.fit_size(
        (
            "NumPy, the default",
            "an NVIDIA GPU, through CuPy",
            "PyTorch on the CPU",
            "PyTorch on an NVIDIA GPU",
            "Apple's GPU, in float32 only",
        ),
        (12, 11),
        here_w - 140,
    )
    for row, (literal, what) in enumerate(
        (
            ('"cpu"', "NumPy, the default"),
            ('"cupy"', "an NVIDIA GPU, through CuPy"),
            ('"torch:cpu"', "PyTorch on the CPU"),
            ('"torch:cuda"', "PyTorch on an NVIDIA GPU"),
            ('"torch:mps"', "Apple's GPU, in float32 only"),
        )
    ):
        y = fork_y + 58 + 29 * row
        s.text(left + 22, y, literal, 12, th.primary, "start", bold=True, mono=True)
        s.text(left + 126, y, what, device_size, th.fg, "start")

    s.text(node_mid, fork_y + 26, "On a node of your hosts file", 14, bold=True)
    steps = (
        "the hosts file says where the node is and how it runs a job",
        "one ssh process carries the run, as data and never as code",
        "phonometry is sent once per version and kept under a digest",
        "the node builds the run again and steps it on the device asked for",
        "back come the probes and the snapshots, or the bytes of a video",
    )
    step_size = s.fit_size(steps, (12, 11), node_w - 60)
    for row, step in enumerate(steps):
        y = fork_y + 58 + 29 * row
        s.circle(node_x + 26, y - 4, 9.5, th.bg, th.accent, 1.6)
        s.text(node_x + 26, y, str(row + 1), 11, th.accent, bold=True)
        s.text(node_x + 46, y, step, step_size, th.fg, "start")

    # --- Both end in the provenance; the fallback comes back here ---------
    fork_b = fork_y + fork_h
    prov_y, prov_h = 596.0, 62.0
    card(
        left,
        prov_y,
        right - left,
        prov_h,
        "result.provenance",
        "device, dtype and gpu say where the run stepped; host and"
        " package_sha256 name the node and the package it ran",
        th.fg,
        sw=2.4,
    )
    s.arrow(left + 60, fork_b, left + 60, prov_y - 2, th.primary, 1.8)
    s.arrow(right - 60, fork_b, right - 60, prov_y - 2, th.accent, 1.8)

    # A failed node, connection or device does not reach the provenance on
    # its own road: with fallback=True it comes back to NumPy, here.
    back_y = fork_b + 24
    s.line(node_mid, fork_b, node_mid, back_y, th.secondary, 1.8, dash="6,4")
    s.line(node_mid, back_y, here_mid, back_y, th.secondary, 1.8, dash="6,4")
    s.arrow(here_mid, back_y, here_mid, fork_b + 2, th.secondary, 1.8)
    s.text(centre, back_y + 22, "fallback=True", 12, th.secondary, bold=True, mono=True)
    back_notes = (
        "a device that cannot be used, or a node or a connection that fails,"
        " warns with ComputeFallbackWarning",
        "and the run steps on NumPy here, in the dtype asked for;"
        " its provenance then says cpu and no host",
    )
    back_size = s.fit_size(back_notes, (12, 11), right - left - 160)
    for row, note in enumerate(back_notes):
        s.text(centre, back_y + 42 + 18 * row, note, back_size, th.muted)

    # === Lower lane: where a video is encoded =============================
    lane_y = 690.0
    s.line(left, lane_y, right, lane_y, th.muted, 0.9, dash="3,4")
    s.text(left, lane_y + 30, "Where a video is encoded", 15, th.fg, "start", bold=True)
    s.text(
        right,
        lane_y + 30,
        "io.VideoOptions(encoder=...), passed as video=",
        12,
        th.muted,
        "end",
    )

    row_y, row_h = lane_y + 48, 58.0
    # 140 + 4 x (22 + 106) + 22 + 146 = 820: the row ends on the right margin.
    auto_w, kind_w, cpu_w, gap = 140.0, 106.0, 146.0, 22.0
    s.rect(left, row_y, auto_w, row_h, th.panel, th.fg, rx=10, sw=2.0)
    s.text(left + auto_w / 2, row_y + 25, '"auto"', 14, th.fg, bold=True, mono=True)
    s.text(left + auto_w / 2, row_y + 45, "the default", 12, th.muted)

    kinds = (
        ("NVENC", '"nvenc"'),
        ("Quick Sync", '"qsv"'),
        ("VAAPI", '"vaapi"'),
        ("VideoToolbox", '"videotoolbox"'),
    )
    kind_size = s.fit_size(
        [name for name, _ in kinds], (13, 12, 11), kind_w - 12, bold=True
    )
    x = left + auto_w + gap
    kind_x0 = x
    for name, literal in kinds:
        s.arrow(x - gap, row_y + row_h / 2, x - 2, row_y + row_h / 2, th.fg, 1.8)
        s.rect(x, row_y, kind_w, row_h, th.panel, th.primary, rx=10, sw=2.0)
        s.text(x + kind_w / 2, row_y + 25, name, kind_size, th.fg, bold=True)
        s.text(x + kind_w / 2, row_y + 45, literal, 11, th.primary, mono=True)
        x += kind_w + gap
    s.arrow(x - gap, row_y + row_h / 2, x - 2, row_y + row_h / 2, th.fg, 1.8)
    s.rect(x, row_y, cpu_w, row_h, th.panel, th.accent, rx=10, sw=2.0)
    s.text(x + cpu_w / 2, row_y + 25, "CPU", 13, th.fg, bold=True)
    s.text(x + cpu_w / 2, row_y + 45, '"cpu"', 11, th.accent, mono=True)

    # One bracket under the five candidates: what "tries" means. The CPU
    # encoder is given the same trial as the four before it.
    kind_x1 = x + cpu_w
    brace_y = row_y + row_h + 12
    s.path(
        f"M {kind_x0} {brace_y - 6} L {kind_x0} {brace_y} "
        f"L {kind_x1} {brace_y} L {kind_x1} {brace_y - 6}",
        stroke=th.primary,
        sw=1.4,
    )
    # Set on the sheet's centre, not on the bracket's: the Spanish runs 728
    # px, and centred under the bracket it passed the right margin.
    trial = (
        "tried in this order, each with a real encode of one frame;"
        " the first that passes writes the video"
    )
    trial_size = s.fit_size((trial,), (12, 11), right - left)
    s.text(centre, brace_y + 19, trial, trial_size, th.fg)
    foot = (
        "On the CPU: SVT-AV1 or, without it, VP9 in a WebM and x265 or x264"
        " in an MP4. A GIF is always written on the CPU.",
        "An animation you draw yourself is encoded here only; the two"
        " simulation writers also draw and encode on a node.",
    )
    foot_size = s.fit_size(foot, (12, 11), right - left)
    for row, note in enumerate(foot):
        s.text(centre, brace_y + 50 + 19 * row, note, foot_size, th.muted)
