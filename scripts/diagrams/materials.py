#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Diagrams of the materials guides: absorbers, diffusers, surfaces and resilient layers.

One subject because every one of these is a specimen on a test rig: an
impedance tube, an airflow resistance bench, a reverberation room or
goniometer for scattering, an in-situ rig on a road surface, or a load plate
on a resilient layer. What is being characterised is the material, not the
building it will end up in.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .parts import _accel, _exciter, _motion_arrows, _rot_arrow, _spring_v

if TYPE_CHECKING:
    from .canvas import SVG, Theme


def _d_impedance_tube(s: SVG, th: Theme) -> None:
    """ISO 10534-2 two-microphone impedance tube (side view)."""
    tube_top, tube_bot, mid = 215.0, 335.0, 275.0
    tube_l, tube_r = 165.0, 778.0
    back_w, spec_w = 20.0, 48.0
    spec_l = tube_r - back_w - spec_w

    # Tube body.
    s.rect(tube_l, tube_top, tube_r - tube_l, tube_bot - tube_top, th.bg, th.fg, sw=3)

    # Loudspeaker sealed to the left end, cone opening into the tube.
    s.rect(72, mid - 46, 70, 92, th.panel, th.primary, rx=6, sw=2)
    s.path(
        f"M 142 {mid - 18} L 142 {mid + 18} L {tube_l} {tube_bot} "
        f"L {tube_l} {tube_top} Z",
        fill=th.panel,
        stroke=th.primary,
        sw=2,
    )
    s.circle(120, mid, 11, th.primary)
    s.text(118, tube_bot + 42, "Loudspeaker", 17, th.fg, bold=True)

    # Test specimen and rigid backing at the right end.
    s.rect(tube_r - back_w, tube_top, back_w, tube_bot - tube_top, th.fg)
    s.rect(spec_l, tube_top, spec_w, tube_bot - tube_top, th.panel, th.secondary, sw=2)
    for hx in range(int(spec_l) + 8, int(spec_l + spec_w), 11):
        s.line(hx, tube_bot - 4, hx - 16, tube_top + 4, th.secondary, 1.0)
    # Starting past the x1 dimension's witness line on the specimen's face,
    # which ran through the name centred on the specimen.
    s.text(
        spec_l + 8,
        tube_top - 14,
        "Test specimen",
        16,
        th.secondary,
        bold=True,
        anchor="start",
    )
    s.text(tube_r - back_w / 2, tube_bot + 42, "Rigid backing", 15, th.muted)

    # Two microphones flush in the top wall (mic 1 = farther from specimen).
    m1x, m2x = 460.0, 555.0
    # Each name beside its microphone, on the outer side of the pair: above
    # it, the x1 dimension's witness line ran through the first.
    for mx, lab, side in ((m1x, "Mic 1", -1.0), (m2x, "Mic 2", 1.0)):
        s.rect(mx - 7, tube_top - 20, 14, 20, th.fg, rx=3)
        s.circle(mx, tube_top, 5, th.primary)
        anchor = "end" if side < 0 else "start"
        s.text(mx + 13 * side, tube_top - 6, lab, 15, th.fg, bold=True, anchor=anchor)

    # Plane-wave arrows inside the tube.
    s.arrow(tube_l + 30, mid - 18, spec_l - 16, mid - 18, th.accent, 2.2)
    s.text((tube_l + spec_l) / 2 - 40, mid - 26, "incident", 15, th.accent)
    s.arrow(spec_l - 16, mid + 20, tube_l + 30, mid + 20, th.secondary, 2.2)
    s.text((tube_l + spec_l) / 2 - 40, mid + 38, "reflected", 15, th.secondary)

    # Dimensions: x1 (specimen face -> far mic) above, spacing s below.
    s.dim(spec_l, tube_top, m1x, tube_top, "$x_1$", offset=-58, size=16)
    s.dim(m1x, tube_bot, m2x, tube_bot, "$s$", offset=70, size=16)

    # Governing relations and range.
    for y, txt, col in (
        (
            438,
            (
                "$H_{12}$ → reflection factor $r$ (Eq. 17), "
                "absorption $α = 1 − |r|^2$ (Eq. 18), "
                "$Z/ρc_0 = (1+r)/(1−r)$ (Eq. 19)"
            ),
            th.fg,
        ),
        (
            466,
            (
                "Working range $f_l < f < f_u$ set by the microphone spacing "
                "$s$ and the tube diameter (Clause 6.1)"
            ),
            th.muted,
        ),
        (
            492,
            (
                "ASTM E2611: two further microphones behind the specimen also "
                "give the transmission loss"
            ),
            th.muted,
        ),
    ):
        s.text(450, y, txt, 15, col)


def _d_astm_tube(s: SVG, th: Theme) -> None:
    """ASTM E2611 four-microphone transmission-loss tube (side view)."""
    tube_top, tube_bot, mid = 225.0, 345.0, 285.0
    tube_l, tube_r = 140.0, 825.0
    spec_l, spec_r = 453.0, 497.0
    m1x, m2x, m3x, m4x = 250.0, 360.0, 590.0, 700.0

    # Tube body.
    s.rect(tube_l, tube_top, tube_r - tube_l, tube_bot - tube_top, th.bg, th.fg, sw=3)

    # Loudspeaker sealed to the left end.
    s.rect(56, mid - 42, 62, 84, th.panel, th.primary, rx=6, sw=2)
    s.path(
        f"M 118 {mid - 16} L 118 {mid + 16} L {tube_l} {tube_bot} "
        f"L {tube_l} {tube_top} Z",
        fill=th.panel,
        stroke=th.primary,
        sw=2,
    )
    s.circle(96, mid, 10, th.primary)
    s.text(96, tube_bot + 40, "Source", 16, th.fg, bold=True)

    # Adjustable termination (two loads) at the right end.
    s.rect(tube_r - 20, tube_top, 20, tube_bot - tube_top, th.fg)
    s.text(tube_r - 10, tube_bot + 40, "Termination", 15, th.muted)
    s.text(tube_r - 10, tube_bot + 60, "(2 loads)", 15, th.muted)

    # Test specimen at the centre.
    s.rect(
        spec_l,
        tube_top,
        spec_r - spec_l,
        tube_bot - tube_top,
        th.panel,
        th.secondary,
        sw=2,
    )
    for hx in range(int(spec_l) + 7, int(spec_r), 10):
        s.line(hx, tube_bot - 4, hx - 14, tube_top + 4, th.secondary, 1.0)
    s.text(
        (spec_l + spec_r) / 2,
        tube_bot + 40,
        "Test specimen",
        15,
        th.secondary,
        bold=True,
    )

    # Four microphones flush in the top wall (1,2 upstream; 3,4 downstream).
    # Each name beside its microphone: above them, the witness lines of l1
    # and l2 ran through the names of microphones 2 and 3.
    for mx, lab in ((m1x, "Mic 1"), (m2x, "Mic 2"), (m3x, "Mic 3"), (m4x, "Mic 4")):
        s.rect(mx - 6, tube_top - 18, 12, 18, th.fg, rx=3)
        s.circle(mx, tube_top, 5, th.primary)
        s.text(mx - 12, tube_top - 6, lab, 14, th.fg, bold=True, anchor="end")

    # Up- and downstream travelling waves.
    s.arrow(tube_l + 26, mid - 16, spec_l - 8, mid - 16, th.accent, 2.0)
    s.arrow(spec_l - 8, mid + 18, tube_l + 26, mid + 18, th.secondary, 2.0)
    s.arrow(spec_r + 8, mid - 16, tube_r - 26, mid - 16, th.accent, 2.0)
    s.arrow(tube_r - 26, mid + 18, spec_r + 8, mid + 18, th.secondary, 2.0)
    s.text(tube_l + 40, mid - 22, "$A$", 15, th.accent, bold=True)
    s.text(tube_l + 40, mid + 34, "$B$", 15, th.secondary, bold=True)
    s.text(tube_r - 40, mid - 22, "$C$", 15, th.accent, bold=True)
    s.text(tube_r - 40, mid + 34, "$D$", 15, th.secondary, bold=True)

    # Dimensions: spacings s1/s2 below; specimen offsets l1/l2 and thickness d above.
    s.dim(m1x, tube_bot, m2x, tube_bot, "$s_1$", offset=62, size=15)
    s.dim(m3x, tube_bot, m4x, tube_bot, "$s_2$", offset=62, size=15)
    # l1, l2 are both measured from the specimen FRONT face (x = 0), matching
    # wave_decomposition/transfer_matrix_two_load; l2 therefore spans the specimen.
    s.dim(m2x, tube_top, spec_l, tube_top, "$l_1$", offset=-42, size=15)
    s.dim(spec_l, tube_top, m3x, tube_top, "$l_2$", offset=-58, size=15)
    s.dim(spec_l, tube_top - 78, spec_r, tube_top - 78, "$d$", offset=0, size=15)
    s.line(spec_l, tube_top, spec_l, tube_top - 78, th.muted, 0.9, dash="3,3")
    s.line(spec_r, tube_top, spec_r, tube_top - 78, th.muted, 0.9, dash="3,3")

    # Governing relations.
    for y, txt, col in (
        (
            452,
            (
                "Decompose $A$, $B$ (upstream) and $C$, $D$ (downstream) → "
                "transfer matrix $T$ (Eq. 22)"
            ),
            th.fg,
        ),
        (
            480,
            "$TL = 20 log_{10} |(T_{11} + T_{12}/ρc + ρc·T_{21} + T_{22}) / 2|$   (Eq. 26)",
            th.muted,
        ),
        (
            506,
            (
                "Two-load method: repeat with two terminations; the one-load "
                "variant uses a single anechoic end"
            ),
            th.muted,
        ),
    ):
        s.text(450, y, txt, 15, col)


def _d_airflow(s: SVG, th: Theme) -> None:
    """ISO 9053-1 static and ISO 9053-2 alternating airflow-resistance rigs."""
    # --- Left panel: static (DC) method -----------------------------------
    s.rect(38, 70, 400, 560, th.panel, th.fg, rx=8, sw=2)
    s.text(238, 100, "Static method (ISO 9053-1)", 18, th.fg, bold=True)

    cx = 150.0
    holder_l, holder_r = cx - 45, cx + 45
    top_y, bot_y = 150.0, 440.0
    # Vertical measurement cell (Clause 5.2).
    s.line(holder_l, top_y, holder_l, bot_y, th.fg, 2.5)
    s.line(holder_r, top_y, holder_r, bot_y, th.fg, 2.5)
    # Specimen (hatched disc) with its edge seal.
    spec_y, spec_h = 262.0, 40.0
    s.rect(holder_l, spec_y, 90, spec_h, th.bg, th.secondary, sw=2)
    for hy in range(int(spec_y) + 10, int(spec_y + spec_h) + 8, 10):
        s.line(
            holder_l + 4,
            min(hy, spec_y + spec_h - 2),
            holder_r - 4,
            max(hy - 10, spec_y + 2),
            th.secondary,
            1.0,
        )
    s.rect(holder_l - 6, spec_y, 8, spec_h, th.accent)
    s.rect(holder_r - 2, spec_y, 8, spec_h, th.accent)
    s.text(holder_l - 12, spec_y + 26, "seal", 13, th.accent, bold=True, anchor="end")
    # Right of the thickness gauge: centred over the cell, both of its walls
    # and the gauge's stem ran through the name.
    s.text(
        holder_r + 38,
        spec_y - 30,
        "specimen  $A$, $d$",
        14,
        th.secondary,
        bold=True,
        anchor="start",
    )
    # Perforated support under the specimen.
    for gx in range(int(holder_l) + 8, int(holder_r) - 2, 12):
        s.line(gx, spec_y + spec_h + 22, gx, spec_y + spec_h + 34, th.fg, 2.0)
    s.line(holder_l, spec_y + spec_h + 22, holder_r, spec_y + spec_h + 22, th.fg, 1.6)
    s.text(holder_r + 10, spec_y + spec_h + 34, "grid", 13, th.muted, anchor="start")
    # Steady laminar flow up through the holder, from a controlled source.
    s.arrow(cx, bot_y - 6, cx, spec_y + spec_h + 46, th.accent, 2.4)
    s.arrow(cx, spec_y - 46, cx, top_y + 26, th.accent, 2.4)
    s.rect(cx - 44, bot_y + 8, 88, 36, th.bg, th.accent, rx=8, sw=2)
    s.text(cx, bot_y + 32, "$q_v$", 15, th.accent, bold=True)
    # 120 px wide, which holds the Spanish name that ran out through the
    # sides of the 88 px box.
    s.rect(cx - 60, bot_y + 56, 120, 34, th.bg, th.muted, rx=8, sw=1.6)
    s.text(cx, bot_y + 78, "flow source", 13, th.muted)
    # Differential manometer across the specimen (pressure taps).
    tap_x = holder_r + 34
    s.line(holder_r, spec_y + 2, tap_x, spec_y + 2, th.primary, 1.6)
    s.line(holder_r, spec_y + spec_h - 2, tap_x, spec_y + spec_h - 2, th.primary, 1.6)
    s.rect(tap_x, spec_y - 18, 82, spec_h + 34, th.bg, th.primary, rx=8, sw=2)
    s.text(tap_x + 41, spec_y + 24, "$Δp$", 19, th.primary, bold=True)
    # Thickness gauge resting on the specimen, in position (Clause 7.3).
    s.circle(cx + 62, top_y + 42, 14, th.bg, th.muted, 1.8)
    s.text(cx + 62, top_y + 48, "$d$", 14, th.muted, bold=True)
    s.line(cx + 62, top_y + 56, cx + 62, spec_y - 2, th.muted, 1.6, dash="4,3")
    s.line(cx + 30, spec_y - 2, cx + 70, spec_y - 2, th.muted, 1.8)
    # The free space Clause 5.2 asks for ahead of the specimen.
    # Its label over the top of the dimension: beside it, the panel's edge
    # ran through the label.
    s.dim(
        holder_l - 26,
        spec_y,
        holder_l - 26,
        top_y,
        "",
        offset=0,
        size=12,
        label_side="left",
    )
    s.text(holder_l - 26, top_y - 10, "≥ 1 bore", 12, th.fg)

    for yy, txt in (
        (546, "cell ≥ 29 mm bore, ≥ 1 bore of free space above"),
        (568, "$q_v$ and $Δp$ each to ±5 %, $Δp$ readable to 0.1 Pa"),
        (590, "grid ≥ 50 % open, $R < 1$ %; $d$ measured in position"),
    ):
        s.text(238, yy, txt, 12, th.muted)
    s.text(
        238,
        616,
        "$R = Δp / q_v$   (through-origin fit at 0.5 mm/s)",
        14,
        th.fg,
        bold=True,
    )

    # --- Right panel: alternating (AC) method -----------------------------
    s.rect(460, 70, 400, 560, th.panel, th.fg, rx=8, sw=2)
    s.text(660, 100, "Alternating method (ISO 9053-2)", 18, th.fg, bold=True)

    cav_l, cav_r = 590.0, 715.0
    cav_top, cav_bot = 210.0, 410.0
    # Cavity walls.
    s.rect(cav_l, cav_top, cav_r - cav_l, cav_bot - cav_top, th.bg, th.fg, sw=2.5)
    s.text((cav_l + cav_r) / 2, (cav_top + cav_bot) / 2 - 6, "cavity", 15, th.fg)
    s.text(
        (cav_l + cav_r) / 2, (cav_top + cav_bot) / 2 + 18, "$V$", 17, th.fg, bold=True
    )
    # Specimen cell, or the airtight termination that replaces it.
    s.rect(cav_l, cav_top - 26, cav_r - cav_l, 26, th.bg, th.secondary, sw=2)
    for hx in range(int(cav_l) + 8, int(cav_r), 11):
        s.line(hx, cav_top - 4, hx - 14, cav_top - 22, th.secondary, 1.0)
    s.text(
        (cav_l + cav_r) / 2,
        cav_top - 36,
        "measurement cell → $L_{p,s}$ ($h_s$)",
        13,
        th.secondary,
        bold=True,
    )
    s.text(
        (cav_l + cav_r) / 2,
        cav_top - 58,
        "airtight termination → $L_{p,t}$ ($h_t$)",
        13,
        th.muted,
    )
    # Piston at the bottom, oscillating.
    s.rect(cav_l, cav_bot, cav_r - cav_l, 26, th.panel, th.primary, sw=2)
    s.arrow(
        (cav_l + cav_r) / 2,
        cav_bot + 62,
        (cav_l + cav_r) / 2,
        cav_bot + 34,
        th.primary,
        2.2,
    )
    s.arrow(
        (cav_l + cav_r) / 2,
        cav_bot + 34,
        (cav_l + cav_r) / 2,
        cav_bot + 62,
        th.primary,
        2.2,
    )
    s.text(
        (cav_l + cav_r) / 2,
        cav_bot + 84,
        "piston  $f$ = 1–4 Hz",
        15,
        th.primary,
        bold=True,
    )
    s.text((cav_l + cav_r) / 2, cav_bot + 106, "$q_v = 2π f h A_P$", 13, th.muted)
    # Microphone in the cavity wall.
    s.circle(cav_r + 2, (cav_top + cav_bot) / 2, 6, th.fg)
    s.line(
        cav_r + 2,
        (cav_top + cav_bot) / 2,
        cav_r + 60,
        (cav_top + cav_bot) / 2,
        th.muted,
        1.4,
    )
    s.text(
        cav_r + 66,
        (cav_top + cav_bot) / 2 + 6,
        "$L_p$",
        17,
        th.fg,
        bold=True,
        anchor="start",
    )
    s.text(
        660,
        616,
        "$R$ from $L_{p,s} − L_{p,t}$   ($κ′$ per Annex A)",
        14,
        th.fg,
        bold=True,
    )


# ---------------------------------------------------------------------------
# d15 - ISO 17497-1 random-incidence scattering (reverberation room)
# ---------------------------------------------------------------------------


def _d_scattering_reverb(s: SVG, th: Theme) -> None:
    """ISO 17497-1 scattering coefficient in a reverberation room."""
    gy = 400.0
    # Reverberation room with non-parallel walls (skew quadrilateral).
    s.path("M 60 80 L 782 66 L 796 400 L 72 400 Z", fill=th.panel, stroke=th.fg, sw=3)
    s.text(80, 106, "Reverberation room", 17, th.fg, bold=True, anchor="start")

    # --- Turntable carrying the test sample (left, in perspective) --------
    tx, tyc = 285.0, 366.0
    s.ellipse(tx, tyc, 150, 26, th.panel, th.primary, 2.2)  # turntable
    s.ellipse(tx, tyc - 12, 82, 15, th.bg, th.secondary, 2.2)  # test sample
    for hx in range(int(tx) - 60, int(tx) + 60, 12):  # sample hatch
        s.line(hx, tyc - 10, hx + 10, tyc - 18, th.secondary, 1.0)
    s.text(tx, gy + 22, "Turntable and base plate", 15, th.fg, bold=True)
    _rot_arrow(s, tx, tyc, 150, 205, 340, th.accent, 2.2, ry=26)
    s.text(tx, tyc - 70, "the only thing that moves", 13, th.accent)
    s.text(tx, tyc - 46, "sample on the plate for $T_2$ and $T_4$", 13, th.muted)
    # Wall clearance of the turntable rim.
    s.line(78, 386, tx - 150, 386, th.muted, 1.4)
    s.line(78, 380, 78, 392, th.muted, 1.4)
    s.line(tx - 150, 380, tx - 150, 392, th.muted, 1.4)
    s.text(106, 376, "≥ 1.0 m", 12, th.muted)

    # --- Two fixed loudspeaker positions (right) --------------------------
    for sx, sy, lab in ((648.0, 262.0, "S1"), (752.0, 296.0, "S2")):
        s.rect(sx - 20, sy - 26, 40, 52, th.panel, th.primary, rx=6, sw=2)
        s.circle(sx, sy, 11, th.primary)
        s.circle(sx, sy, 4, th.bg)
        s.line(sx, sy + 26, sx, gy, th.fg, 2.2)
        s.line(sx - 14, gy, sx + 14, gy, th.fg, 2.2)
        s.text(sx, sy - 34, lab, 15, th.fg, bold=True)
    s.text(700, 196, "fixed sources (≥ 2)", 14, th.muted)

    # --- Three fixed microphone positions ---------------------------------
    for mx, my, lab in (
        (452.0, 262.0, "M1"),
        (520.0, 286.0, "M2"),
        (586.0, 310.0, "M3"),
    ):
        s.mic(mx, my, gy, 1.0)
        s.text(mx, my - 12, lab, 14, th.fg, bold=True)
    s.text(470, 226, "fixed microphones (≥ 3)", 14, th.muted)

    # --- Governing relations ----------------------------------------------
    for y, txt, col, bold in (
        (
            448,
            ("$T_1$ base plate, static  ·  $T_2$ sample, static  →  $α_s$ (Eq. 1)"),
            th.fg,
            True,
        ),
        (
            474,
            (
                "$T_3$ base plate, rotating  ·  $T_4$ sample, rotating  →  "
                "$α_{spec}$ (Eq. 4)"
            ),
            th.fg,
            True,
        ),
        (502, "$s = (α_{spec} − α_s) / (1 − α_s)$   (Eq. 5)", th.accent, True),
        (
            528,
            (
                "$α$ from $55.3·(V/S)·(1/(c T)) − 4(V/S)m$  ·  the base plate "
                "must pass the Table 1 ceiling"
            ),
            th.muted,
            False,
        ),
    ):
        s.text(450, y, txt, 16 if bold else 15, col, bold=bold)


# ---------------------------------------------------------------------------
# d16 - ISO 17497-2 free-field diffusion goniometer
# ---------------------------------------------------------------------------


def _d_diffusion_goniometer(s: SVG, th: Theme) -> None:
    """ISO 17497-2 directional diffusion coefficient (goniometer)."""
    gy, cx, R = 430.0, 450.0, 300.0
    s.ground(gy, 90, 810)

    # Semicircular receiver arc (0 deg right .. 180 deg left, zenith at top).
    s.path(f"M {cx - R} {gy} A {R} {R} 0 0 1 {cx + R} {gy}", stroke=th.muted, sw=1.8)
    ends = {0, 90, 180}
    for ang in range(0, 181, 15):
        a = math.radians(ang)
        px, py = cx + R * math.cos(a), gy - R * math.sin(a)
        s.circle(px, py, 6.5, th.primary)
        s.circle(px, py, 2.2, th.bg)
    # Label the two horizon receivers and the zenith one.
    # Raised clear of the ground line, which the subscripts touched.
    s.text(cx + R + 4, gy - 10, "$L_n$", 15, th.fg, anchor="start")
    s.text(cx - R - 4, gy - 10, "$L_1$", 15, th.fg, anchor="end")
    s.text(cx, gy - R - 14, "$L_i$", 15, th.fg)
    # Just outside the arc it names, which ran through it inside.
    s.text(cx + 176, gy - 250, "receiver arc (5° steps)", 14, th.muted, anchor="start")
    _ = ends

    # Polar (scattered) response lobe about the sample centre.
    pts = []
    for ang in range(0, 181, 6):
        a = math.radians(ang)
        rr = 92.0 + 42.0 * abs(math.sin(3.0 * a))
        pts.append((cx + rr * math.cos(a), gy - rr * math.sin(a)))
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    s.path(d, stroke=th.accent, sw=2.0)
    s.text(cx + 96, gy - 150, "polar response $L_i$", 14, th.accent)

    # Fixed source, off to the upper left, illuminating the sample.
    sa = math.radians(155.0)
    sxx, syy = cx + (R + 44) * math.cos(sa), gy - (R + 44) * math.sin(sa)
    s.rect(sxx - 26, syy - 22, 52, 44, th.panel, th.primary, rx=6, sw=2)
    s.circle(sxx + 20, syy, 10, th.primary)
    s.circle(sxx + 20, syy, 4, th.bg)
    s.text(sxx, syy - 32, "Fixed source", 15, th.fg, bold=True)
    s.arrow(sxx + 26, syy + 6, cx - 74, gy - 12, th.accent, 2.0)

    # Test sample on the turntable at the arc centre.
    s.rect(cx - 72, gy - 13, 144, 13, th.bg, th.secondary, sw=2)
    for hx in range(int(cx) - 64, int(cx) + 64, 12):
        s.line(hx, gy - 3, hx + 9, gy - 11, th.secondary, 1.0)
    s.text(cx, gy - 20, "Test sample", 14, th.secondary, bold=True)
    s.ellipse(cx, gy + 8, 88, 12, "none", th.primary, 1.8)
    _rot_arrow(s, cx, gy + 8, 88, 200, 340, th.primary, 1.8, ry=12)
    # Below the ground's hatching, which ran through the word at gy + 12.
    s.text(cx + 150, gy + 26, "Turntable", 14, th.fg, bold=True, anchor="start")

    # Governing relations. Formula 5 stays plain for now: its 10^(L_i/10)
    # terms put a subscript inside the exponent, one script level more than
    # the composer sets (the same energy-sum family the flanking and
    # reception-plate sums parked).
    s.text(
        450,
        476,
        "d = [(Σ10^(L_i/10))² − Σ(10^(L_i/10))²] / "
        "[(n−1)·Σ(10^(L_i/10))²]   (Formula 5)",
        15,
        th.fg,
        bold=True,
    )
    s.text(
        450,
        506,
        "$d_n = (d − d_{ref}) / (1 − d_{ref})$   (Formula 7)",
        15,
        th.accent,
        bold=True,
    )
    s.text(
        450,
        534,
        "5° receiver steps · turntable rotates the sample · source fixed",
        15,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Metadiffuser: from a Schroeder sequence to a diffusion coefficient
# (Jiménez, Cox, Romero-García and Groby 2017)
# ---------------------------------------------------------------------------


def _d_metadiffuser_chain(s: SVG, th: Theme) -> None:
    """From a Schroeder sequence to a diffusion coefficient, for a metadiffuser.

    The chain of Jiménez, Cox, Romero-García and Groby (Sci. Rep. 7, 5389,
    2017) drawn on the published quadratic-residue design. Band 1 is the
    target: the N = 5 quadratic residues set the well depths of a QRD designed
    for 500 Hz (27.4 cm deep, p. 3 of the paper; Cox and D'Antonio Eqs. (10.2)
    and (10.3)), and those depths set the reflection phase each well has to
    return at the 2 kHz evaluation frequency. The metadiffuser that replaces
    it is drawn beside it at the same scale, 35 cm by 2 cm, from Table 1.
    Band 2 is slit 1 of Table 1 enlarged, with the transfer-matrix chain of
    the paper's Methods set out along its depth: the radiation end correction
    at the mouth (Eq. (5)), a half lattice step either side of each resonator
    (Eq. (3)), the resonators as shunts (Eq. (4)), and the reflection of the
    rigidly backed slit (Eq. (6)). The loop back to band 1 is the design
    recipe: the geometry is tuned until each slit returns its target phase.
    Band 3 is the reduction the library runs: six periods, the Fraunhofer far
    field of Eq. (1), the grating directions of Cox and D'Antonio Eq. (10.9)
    with lobe lengths scaled by the aperture of one 70 mm strip, and the
    ISO 17497-2 coefficient of Formula (5) normalised by Formula (7).
    """
    mm_a = 0.6  # band 1: QRD and metadiffuser at one scale, px per mm
    mm_b = 7.0  # band 2: slit 1 enlarged, px per mm
    pitch = 70.0 * mm_a  # the 70 mm well pitch, 350 mm over five wells
    # Table 1 of the paper, slit by slit: h, neck length, cavity length,
    # neck width, cavity width, all in mm; two identical resonators per slit.
    table = (
        (14.7, 13.0, 16.4, 6.2, 9.0),
        (30.9, 9.1, 4.3, 3.5, 9.0),
        (30.9, 9.1, 4.3, 3.5, 9.0),
        (15.7, 13.3, 17.0, 6.3, 9.0),
        (20.3, 18.0, 20.7, 3.2, 9.0),
    )
    residues = (1, 4, 4, 1, 0)  # s_n = n² mod 5 for n = 1..5

    # ---- 1 · the target and the panel that replaces it, one scale --------
    s.text(
        30,
        64,
        "1 · Phases first: the sequence sets a target phase for each well",
        15,
        th.fg,
        "start",
        bold=True,
    )

    # The QRD of 500 Hz, drawn as its section profile: d_n = s_n λ0/(2N)
    # with λ0 = 686 mm, so 68.6 mm and 274.4 mm wells and one flat well.
    xq, yq, fin = 40.0, 106.0, 2.0
    depths = [sn * 68.6 * mm_a for sn in residues]
    body_h = max(depths) + 6.0
    s.text(xq + 2.5 * pitch, 92, "the target QRD, designed for 500 Hz", 12, th.muted)
    pts = [(xq, yq + body_h), (xq, yq)]
    for i, dpx in enumerate(depths):
        a, b = xq + i * pitch + fin, xq + (i + 1) * pitch - fin
        if dpx > 0:
            pts += [(a, yq), (a, yq + dpx), (b, yq + dpx), (b, yq)]
    pts += [(xq + 5 * pitch, yq), (xq + 5 * pitch, yq + body_h)]
    s.path(
        "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z",
        fill=th.panel,
        stroke=th.fg,
        sw=1.8,
    )
    s.ground(yq + body_h, xq - 4, xq + 5 * pitch + 4)
    s.dim(
        xq + 5 * pitch + 12,
        yq,
        xq + 5 * pitch + 12,
        yq + max(depths),
        "27.4 cm",
        size=12,
        label_side="right",
    )

    # The targets, well by well.
    cols = (350.0, 400.0, 462.0, 540.0)
    for x, head in zip(cols, ("$n$", "$s_n$", "$d_n$", "$φ_n$ at 2 kHz"), strict=True):
        s.text(x, 98, head, 13, th.fg)
    s.line(328, 106, 590, 106, th.muted, 1.0)
    depth_labels = ("6.9 cm", "27.4 cm", "27.4 cm", "6.9 cm", "0")
    phase_labels = ("+72°", "−72°", "−72°", "+72°", "0°")
    for i in range(5):
        y = 126 + 22 * i
        s.text(cols[0], y, str(i + 1), 13, th.fg)
        s.text(cols[1], y, str(residues[i]), 13, th.fg)
        s.text(cols[2], y, depth_labels[i], 13, th.fg)
        s.text(cols[3], y, phase_labels[i], 13, th.primary, bold=True)
    s.text(459, 238, "$s_n = n² mod N$,  $d_n = s_n λ_0/(2N)$", 13, th.fg)
    s.text(459, 260, "$φ_n = −2k d_n$, wrapped into ±180°", 12, th.muted)

    # The metadiffuser at the same scale: solid in muted, air in background,
    # the body outlined so the 350 mm by 20 mm strip reads as one panel rather
    # than as the blocks the slits cut it into, each mouth opened again at the
    # face the way band 2 opens the mouth it enlarges.
    xm, ym, depth_px = 640.0, 112.0, 20.0 * mm_a
    s.dim(xm, 92, xm + 5 * pitch, 92, "350 mm", size=12)
    s.rect(xm, ym, 5 * pitch, depth_px, th.muted, th.fg, sw=1.2)
    for i, (h, ln, lc, wn, wc) in enumerate(table):
        x0 = xm + (i + 0.12) * pitch
        s.rect(x0, ym, h * mm_a, depth_px, th.bg, "none")
        s.line(x0 + 0.5, ym, x0 + h * mm_a - 0.5, ym, th.bg, 2.0)
        for m in range(2):
            yc = ym + (m + 0.5) * 10.0 * mm_a
            s.rect(
                x0 + h * mm_a, yc - wn * mm_a / 2, ln * mm_a, wn * mm_a, th.bg, "none"
            )
            s.rect(
                x0 + (h + ln) * mm_a,
                yc - wc * mm_a / 2,
                lc * mm_a,
                wc * mm_a,
                th.bg,
                "none",
            )
        s.text(x0 + h * mm_a / 2, ym - 6, str(i + 1), 11, th.fg)
    # The backing sits just clear of the panel back, so its line is the wall
    # the lower cavities stop 0,5 mm short of rather than a stroke over them.
    s.ground(ym + depth_px + 1.2, xm - 4, xm + 5 * pitch + 4)
    s.text(xm + 5 * pitch + 8, ym + 10, "2 cm", 12, th.fg, "start")
    s.arrow(596, 170, 640, 132, th.primary, 1.6)
    x1 = xm + 0.12 * pitch
    s.rect(  # slit 1 with its resonators, the part band 2 enlarges
        x1 - 4,
        ym - 2,
        sum(table[0][:3]) * mm_a + 8,
        depth_px + 14,
        "none",
        th.muted,
        sw=1.0,
        dash="3,3",
    )
    s.line(x1 + 4.4, ym + depth_px + 12, x1 + 4.4, 346, th.muted, 1.0, dash="3,3")
    s.text(660, 158, "the metadiffuser at the same scale", 13, th.fg, "start")
    s.text(660, 178, "35 cm × 2 cm, five slits", 12, th.muted, "start")
    s.text(660, 196, "two resonators in each slit", 12, th.muted, "start")

    # ---- 2 · slit 1 and its transfer-matrix chain -------------------------
    s.text(
        30,
        334,
        "2 · Geometry second: one slit, one transfer-matrix chain",
        15,
        th.fg,
        "start",
        bold=True,
    )
    s.rect(446, 346, 444, 204, "none", th.muted, rx=6, sw=1.0, dash="5,4")
    face, back = 380.0, 380.0 + 20.0 * mm_b
    h, ln, lc, wn, wc = table[0]
    xs = 470.0
    xn, xc, xe = xs + h * mm_b, xs + (h + ln) * mm_b, xs + (h + ln + lc) * mm_b
    # The body takes the solid tone of band 1, so the enlargement keeps the
    # figure and ground of the overview it is drawn out of.
    s.rect(456, face, xe + 14 - 456, back - face, th.muted, th.fg, sw=1.6)
    s.rect(xs, face, h * mm_b, back - face, th.bg, th.fg, sw=1.6)
    s.line(xs + 1.2, face, xn - 1.2, face, th.bg, 3.0)  # the mouth is open
    for m in range(2):
        yc = face + (m + 0.5) * 10.0 * mm_b  # a/2 and 3a/2 below the face
        s.rect(xn, yc - wn * mm_b / 2, ln * mm_b, wn * mm_b, th.bg, th.fg, sw=1.4)
        s.rect(xc, yc - wc * mm_b / 2, lc * mm_b, wc * mm_b, th.bg, th.fg, sw=1.4)
        for x in (xn, xc):  # open the neck into the slit and into the cavity
            s.line(x, yc - wn * mm_b / 2 + 1.2, x, yc + wn * mm_b / 2 - 1.2, th.bg, 3.0)
    s.text((xn + xc) / 2, face + 5 * mm_b + 4, "neck", 11, th.fg)
    s.text((xc + xe) / 2, face + 5 * mm_b + 4, "cavity", 11, th.fg)
    s.text(xs + h * mm_b / 2 + 14, back - 16, "slit 1", 12, th.muted)
    s.ground(back, 452, xe + 18)
    s.dim(xs, face - 10, xn, face - 10, "$h_1$ = 14.7 mm", size=12)
    s.dim(
        xs + 14,
        face,
        xs + 14,
        face + 10 * mm_b,
        "$a$ = 10 mm",
        size=12,
        label_side="right",
    )
    s.dim(xe + 26, face, xe + 26, back, "$L$ = 20 mm", size=12, label_side="right")
    s.text(668, 544, "necks 13.0 mm × 6.2 mm, cavities 16.4 mm × 9.0 mm", 12, th.muted)

    # The chain along the depth, face at the top: M_Δl, then (M_s M_HR M_s)^M.
    lx0, lx1 = 380.0, 440.0
    s.rect(lx0, face - 26, lx1 - lx0, 22, th.panel, th.fg, rx=3, sw=1.4)
    s.text((lx0 + lx1) / 2, face - 10, "$M_{Δl}$", 13, th.fg)
    for k in range(4):
        y0 = face + k * 5 * mm_b
        s.rect(lx0, y0, lx1 - lx0, 5 * mm_b, th.panel, th.fg, sw=1.2)
        s.text((lx0 + lx1) / 2, y0 + 5 * mm_b / 2 + 5, "$M_s$", 13, th.fg)
    for m in range(2):
        yc = face + (m + 0.5) * 10.0 * mm_b
        s.line(lx0 - 6, yc, lx1 + 6, yc, th.primary, 3.2)
        s.line(lx1 + 6, yc, 456, yc, th.primary, 1.0, dash="3,3")
    s.line(lx0 - 6, back, lx1 + 6, back, th.fg, 3.2)
    for y_edge in (face, back):
        s.line(lx1 + 6, y_edge, 456, y_edge, th.muted, 0.9, dash="2,3")
    s.text(368, face - 11, "mouth: radiation end correction", 12, th.fg, "end")
    s.text(
        368,
        face + 5 * mm_b / 2 - 3,
        "half a lattice step of slit, $a$/2",
        12,
        th.fg,
        "end",
    )
    s.text(
        368,
        face + 5 * mm_b + 5,
        "resonator 1, a shunt $1/Z_{HR}$",
        12,
        th.primary,
        "end",
    )
    s.text(368, face + 15 * mm_b + 5, "resonator 2", 12, th.primary, "end")
    s.text(368, back + 5, "rigid backing", 12, th.fg, "end")

    s.rect(30, 540, 406, 66, th.panel, th.primary, rx=6, sw=1.6)
    s.text(233, 564, "$T_n = M_{Δl} · (M_s · M_{HR} · M_s)^M$", 14, th.fg, bold=True)
    s.text(
        233,
        592,
        "$R_n = (T_{11} − Z_0 T_{21}) / (T_{11} + Z_0 T_{21})$",
        14,
        th.primary,
        bold=True,
    )

    # The design loop: back from the phase of R_n to the target phases.
    s.path("M 30 578 L 14 578 L 14 300 L 459 300 L 459 272", stroke=th.primary, sw=1.6)
    s.arrow(459, 280, 459, 266, th.primary, 1.6)
    s.text(26, 452, "slit by slit: tune $h_n$, the necks and", 12, th.primary, "start")
    s.text(
        26,
        470,
        "the cavities until $arg R_n = φ_n$ at 2 kHz",
        12,
        th.primary,
        "start",
    )

    # ---- 3 · six periods, the far field and the coefficient ---------------
    s.text(
        30,
        640,
        "3 · Then the far field: six periods, five grating lobes, one coefficient",
        15,
        th.fg,
        "start",
        bold=True,
    )
    cx, cy, radius = 240.0, 856.0, 176.0
    s.path(
        f"M {cx - radius} {cy} A {radius} {radius} 0 0 1 {cx + radius} {cy}",
        stroke=th.muted,
        sw=1.2,
    )
    for ang in range(-90, 91, 5):  # the 37 receivers of the reduction
        a = math.radians(ang)
        s.circle(cx + radius * math.sin(a), cy - radius * math.cos(a), 2.2, th.primary)

    def polar(angle: float, r: float) -> tuple[float, float]:
        return cx + r * math.sin(angle), cy - r * math.cos(angle)

    # sin θ = mλ/(Nw) at 2 kHz, λ = 343/2000 m and Nw = 0.35 m; each lobe
    # scaled by the aperture of one 70 mm strip, sinc(πm/N).
    for m, half_width, label in (
        (0, 4.5, "$m$ = 0"),
        (1, 5.5, "+1"),
        (-1, 5.5, "−1"),
        (2, 11.0, "+2"),
        (-2, 11.0, "−2"),
    ):
        theta = math.asin(m * (343.0 / 2000.0) / 0.35)
        aperture = 1.0 if m == 0 else math.sin(math.pi * m / 5) / (math.pi * m / 5)
        rho, d = 158.0 * aperture, math.radians(half_width)
        c1, tip, c2 = (
            polar(theta - 1.6 * d, 0.92 * rho),
            polar(theta, rho),
            polar(theta + 1.6 * d, 0.92 * rho),
        )
        s.path(
            f"M {cx} {cy} Q {c1[0]:.1f} {c1[1]:.1f} {tip[0]:.1f} {tip[1]:.1f} "
            f"Q {c2[0]:.1f} {c2[1]:.1f} {cx} {cy} Z",
            fill=th.panel,
            stroke=th.accent,
            sw=2.0,
        )
        lx, ly = polar(theta, radius + 16)
        s.text(lx, ly + 4, label, 12, th.accent)

    # The 2.1 m panel: 30 strips of 70 mm, a longer tick every period.
    x_strip = cx - 210.0
    s.rect(x_strip, cy, 420, 7, th.panel, th.fg, sw=1.2)
    for j in range(31):
        x = x_strip + 14 * j
        period_edge = j % 5 == 0
        s.line(
            x,
            cy - 5 if period_edge else cy,
            x,
            cy + 7,
            th.fg if period_edge else th.muted,
            1.0,
        )
    s.ground(cy + 7, x_strip - 4, x_strip + 424)
    s.dim(x_strip, cy + 40, x_strip + 420, cy + 40, "six periods: 2.1 m", size=12)

    s.rect(474, 654, 416, 66, th.panel, th.fg, rx=6, sw=1.4)
    s.text(682, 680, "$p_{s}(θ) = ∫ R(x) exp(j k_0 x sin θ) dx$", 14, th.fg, bold=True)
    s.text(
        682,
        706,
        "$R(x)$ holds $R_n$ over each 70 mm strip, 30 strips in all",
        12,
        th.muted,
    )
    s.rect(474, 730, 416, 66, th.panel, th.accent, rx=6, sw=1.4)
    s.text(682, 756, "$sin θ = mλ/(N w)$,  $N w$ = 350 mm", 14, th.accent, bold=True)
    s.text(
        682,
        782,
        "at 2 kHz and 343 m/s the lobes stand near 0°, ±29° and ±78.5°",
        12,
        th.muted,
    )
    s.rect(474, 806, 416, 110, th.panel, th.primary, rx=6, sw=1.6)
    s.text(
        682,
        832,
        "$d = [(Σ I_{i})² − Σ I_{i}²] / [(37 − 1) Σ I_{i}²]$",
        14,
        th.primary,
        bold=True,
    )
    s.text(
        682,
        858,
        "$d_{norm} = (d − d_{ref}) / (1 − d_{ref})$",
        14,
        th.primary,
        bold=True,
    )
    s.text(682, 882, "$I_i = |p_{s}(θ_i)|²$ every 5° from −90° to +90°", 12, th.muted)
    s.text(682, 902, "$d_{ref}$: the same sums over a flat panel as wide", 12, th.muted)


# ---------------------------------------------------------------------------
# d17 - ISO 13472-1 in-situ road absorption, subtraction technique
# ---------------------------------------------------------------------------


def _d_insitu_subtraction(s: SVG, th: Theme) -> None:
    """ISO 13472-1 extended-surface (subtraction) in-situ absorption."""
    gy = 415.0
    # Road surface (the reference plane) under the main measurement.
    s.ground(gy, 55, 590)
    s.text(66, gy + 30, "Road surface", 14, th.muted, anchor="start")

    sx = 250.0
    src_y, mic_y = gy - 235.0, gy - 47.0  # ds : dm = 1.25 : 0.25 m
    s.line(sx, src_y, sx, gy, th.muted, 1.0, dash="4,4")  # normal axis

    # Loudspeaker (source) at ds above the surface.
    s.rect(sx - 30, src_y - 30, 60, 60, th.panel, th.primary, rx=6, sw=2)
    s.circle(sx, src_y, 12, th.primary)
    s.circle(sx, src_y, 5, th.bg)
    s.text(sx, src_y - 42, "Loudspeaker", 15, th.fg, bold=True)

    # Microphone at dm above the surface.
    s.rect(sx - 6, mic_y - 9, 12, 18, th.fg, rx=3)
    s.circle(sx, mic_y - 9, 5, th.primary)
    # Left of the microphone: on its right, the d_m witness line ran through
    # the word and the reflected ray's head into it.
    s.text(sx - 14, mic_y + 5, "Microphone", 13, th.fg, anchor="end")

    # Direct ray (source -> mic), drawn offset to the left of the axis.
    s.arrow(sx - 7, src_y + 22, sx - 7, mic_y - 12, th.accent, 2.0)
    # Against the arrow it names, clear of the d_s dimension, which moves
    # out to make room: at x = sx - 72 it ran through the label.
    s.text(
        sx - 14, (src_y + mic_y) / 2, "direct  $d_s−d_m$", 13, th.accent, anchor="end"
    )
    # Road-reflected ray: source -> surface point -> mic (shallow V, offset).
    gpx = sx + 74.0
    s.line(sx + 8, src_y + 24, gpx, gy, th.secondary, 2.0)
    s.arrow(gpx, gy, sx + 8, mic_y + 6, th.secondary, 2.0)
    s.text(gpx + 8, gy - 96, "reflected  $d_s+d_m$", 13, th.secondary, anchor="start")
    # Dashed continuation toward the image source below the plane.
    s.line(gpx, gy, sx + 34, gy + 66, th.muted, 1.2, dash="5,4")
    s.text(
        sx + 52, gy + 60, "to image source ($d_s$ below)", 12, th.muted, anchor="start"
    )

    # Height dimensions ds and dm.
    s.dim(
        sx - 150,
        gy,
        sx - 150,
        src_y,
        "$d_s$ = 1.25 m",
        offset=0,
        label_side="right",
        size=15,
    )
    s.line(sx - 150, gy, sx, gy, th.muted, 0.9, dash="3,3")
    s.line(sx - 150, src_y, sx - 30, src_y, th.muted, 0.9, dash="3,3")
    s.dim(
        sx + 122,
        gy,
        sx + 122,
        mic_y,
        "$d_m$ = 0.25 m",
        offset=0,
        label_side="right",
        size=15,
    )
    s.line(sx, mic_y, sx + 122, mic_y, th.muted, 0.9, dash="3,3")

    # --- Free-field reference (right): source + mic high, no ground -------
    s.line(615, 90, 615, gy + 40, th.muted, 1.2, dash="6,5")
    # Centred far enough right that its last caption, 11 px in Spanish,
    # stays clear of the divider it ran across at x = 730.
    fx = 760.0
    fs_y, fm_y = 150.0, 292.0
    s.rect(fx - 28, fs_y - 26, 56, 52, th.panel, th.primary, rx=6, sw=2)
    s.circle(fx, fs_y, 11, th.primary)
    s.circle(fx, fs_y, 4, th.bg)
    s.rect(fx - 6, fm_y - 9, 12, 18, th.fg, rx=3)
    s.circle(fx, fm_y - 9, 5, th.primary)
    s.arrow(fx, fs_y + 28, fx, fm_y - 14, th.accent, 2.0)
    s.text(fx, fs_y - 40, "Free-field reference", 15, th.fg, bold=True)
    window = "$H_i$: no ground reflection in the window"
    s.text(fx, fm_y + 34, window, s.fit_size([window], [12, 11], 266), th.muted)

    # Governing relations.
    s.text(
        450,
        502,
        "$K_r = (d_s − d_m)/(d_s + d_m) = 2/3$   (Clause 4.1)",
        15,
        th.fg,
        bold=True,
    )
    s.text(
        450,
        528,
        "$α(f) = 1 − (1/K_r^2)·|H_r/H_i|^2$   ·   $Δτ = 2 d_m / c$",
        15,
        th.accent,
        bold=True,
    )
    s.text(
        450,
        552,
        "Adrienne time window isolates the reflected response $H_r$",
        14,
        th.muted,
    )


# ---------------------------------------------------------------------------
# d18 - ISO 13472-2 in-situ road absorption, spot method
# ---------------------------------------------------------------------------


def _d_spot_tube(s: SVG, th: Theme) -> None:
    """ISO 13472-2 spot method: short tube sealed onto the road surface."""
    gy = 430.0
    cx, hw, y_top = 235.0, 72.0, 120.0

    # Road surface (the test sample) with the tube sealed onto it.
    s.ground(gy, 60, 430)
    s.text(72, gy + 30, "Road surface (test sample)", 13, th.muted, anchor="start")

    # Tube walls.
    s.line(cx - hw, y_top, cx - hw, gy, th.fg, 3)
    s.line(cx + hw, y_top, cx + hw, gy, th.fg, 3)
    # Sealing rings where the tube meets the road.
    s.rect(cx - hw - 7, gy - 9, 14, 18, th.muted, rx=2)
    s.rect(cx + hw - 7, gy - 9, 14, 18, th.muted, rx=2)

    # Loudspeaker cap at the top.
    s.rect(cx - hw, y_top - 40, 2 * hw, 40, th.panel, th.primary, sw=2)
    s.circle(cx, y_top - 20, 12, th.primary)
    s.circle(cx, y_top - 20, 5, th.bg)
    s.text(cx, y_top - 52, "Loudspeaker", 15, th.fg, bold=True)

    # Two microphones flush in the right wall, spacing s.
    m1y, m2y = gy - 158.0, gy - 82.0
    for my, lab in ((m1y, "Mic 1"), (m2y, "Mic 2")):
        s.rect(cx + hw - 4, my - 7, 12, 14, th.fg, rx=3)
        s.circle(cx + hw, my, 4, th.primary)
        # Above the witness line to the spacing dimension, which ran through
        # the name level with the microphone.
        s.text(cx + hw + 16, my - 6, lab, 13, th.fg, anchor="start")

    # Plane-wave travel down and reflection back up.
    s.arrow(cx - 34, y_top + 16, cx - 34, gy - 26, th.accent, 2.0)
    s.arrow(cx - 8, gy - 26, cx - 8, y_top + 16, th.secondary, 2.0)

    # Dimensions: tube diameter d (across) and mic spacing s (down).
    # Low enough for its label to clear the loudspeaker cap's edge.
    s.dim(cx - hw, y_top + 26, cx + hw, y_top + 26, "$d$", offset=0, size=15)
    # Far enough out for the microphones' names to end before its arrows.
    s.dim(
        cx + hw + 90,
        m1y,
        cx + hw + 90,
        m2y,
        "$s$",
        offset=0,
        label_side="right",
        size=15,
    )
    s.line(cx + hw + 10, m1y, cx + hw + 90, m1y, th.muted, 0.9, dash="3,3")
    s.line(cx + hw + 10, m2y, cx + hw + 90, m2y, th.muted, 0.9, dash="3,3")

    # Right panel: usable frequency range and DSP method.
    s.rect(430, 118, 430, 300, "none", th.muted, rx=12, dash="6,5")
    s.text(645, 152, "Spot method (ISO 13472-2)", 17, th.fg, bold=True)
    for y, txt, col in (
        (196, "$f_u = 0.58 c_0 / d$   (Clause 5.4.1)", th.accent),
        (232, "$0.05 c_0/f_{min} < s < 0.45 c_0/f_{max}$   (Clause 5.4.2)", th.accent),
        (268, "Working range: 250–1600 Hz (1/3-octave)", th.fg),
        (312, "Two-microphone transfer function $H_{12}$", th.fg),
        (344, "→ ISO 10534-2 decomposition → $α(f)$", th.primary),
    ):
        s.text(645, y, txt, 15, col, bold=(col is th.primary))
    # 12 px in Spanish, which at 13 ran out through the box's left edge.
    sealed = "Tube sealed onto the road; plane waves only below $f_u$"
    s.text(645, 396, sealed, s.fit_size([sealed], [13, 12], 410), th.muted)


def _d_iso11654(s: SVG, th: Theme) -> None:
    """ISO 11654 single-number absorption rating: from αs to the absorption class."""
    cx = 450.0
    bw, bh = 760.0, 54.0
    x0 = cx - bw / 2

    s.rect(x0, 46, bw, bh, th.panel, th.fg, rx=10, sw=2)
    s.text(
        cx,
        68,
        "Measured  $α_s$  at one-third octaves, 200 Hz to 5000 Hz",
        15,
        th.fg,
        "middle",
        bold=True,
    )
    s.text(cx, 88, "from a reverberation room (ISO 354)", 11, th.muted, "middle")
    s.arrow(cx, 100, cx, 128, th.fg, 1.8)

    def _step(y: float, l1: str, l2: str, color: str) -> None:
        s.rect(x0, y, bw, bh, th.panel, color, rx=10, sw=2)
        # "Desplazar la curva de referencia en pasos de 0,05 hasta el mejor
        # ajuste" is 735 px against the 522 of its English twin, and it is
        # the only line of the chart that has to drop a step.
        size = s.fit_size([l1], (15, 14), bw - 28, bold=True)
        s.text(cx, y + 23, l1, size, th.fg, "middle", bold=True)
        s.text(cx, y + 42, l2, 11, th.muted, "middle")

    _step(
        128,
        "Practical  $α_p$  per octave band, 250 Hz to 4000 Hz  (Clause 4.1)",
        "mean of the three one-third octaves, rounded to 0.05",
        th.primary,
    )
    _step(
        206,
        "Shift the reference curve in 0.05 steps to best fit  (Clause 4.2)",
        "sum of unfavourable deviations kept ≤ 0.10",
        th.fg,
    )
    _step(
        284,
        "Weighted coefficient  $α_w$ = shifted reference at 500 Hz",
        "read off the shifted curve, always a multiple of 0.05",
        th.fg,
    )
    _step(
        362,
        "Shape indicators (L, M, H) where  $α_p$ − reference ≥ 0.25",
        "appended to $α_w$ in parentheses, e.g. 0.60(M)",
        th.secondary,
    )
    for y0, y1 in ((100, 128), (182, 206), (260, 284), (338, 362)):
        s.arrow(cx, y0, cx, y1, th.fg, 1.8)
    s.arrow(cx, 416, cx, 444, th.fg, 1.8)

    s.rect(x0, 444, bw, 58, "none", th.primary, rx=10, sw=2.4)
    s.text(
        cx,
        469,
        "Sound absorption class  A to E   (Table B.1, Annex B)",
        15,
        th.fg,
        "middle",
        bold=True,
    )
    s.text(
        cx,
        489,
        "or “Not classified” when $α_w$ falls below the class-E band",
        11,
        th.muted,
        "middle",
    )


# ---------------------------------------------------------------------------
# Dynamic-stiffness resonance rig (ISO 9052-1 / EN 29052-1)
# ---------------------------------------------------------------------------


def _dsr_arrangement(
    s: SVG,
    th: Theme,
    cx: float,
    base_y: float,
    *,
    rigid: bool,
    drive_plate: bool,
    both: bool,
    title: str,
    note: str,
) -> None:
    """One EN 29052-1 excitation arrangement, drawn to a common baseline.

    ``rigid`` draws the hatched foundation of the first arrangement; the
    other two stand on a baseplate of at least 100 kg carried on soft
    mounts. ``drive_plate`` puts the exciter on the load plate rather than
    under the baseplate, and ``both`` adds the second accelerometer.
    """
    half = 72.0
    x0, x1 = cx - half, cx + half
    spec_h, plate_h = 38.0, 20.0
    spec_top = base_y - spec_h
    plate_top = spec_top - plate_h

    s.text(cx, 96, title, 14, th.fg, bold=True)
    s.text(cx, 116, note, 12, th.muted)

    if rigid:
        s.ground(base_y, x0 - 40, x1 + 40)
        s.text(cx, base_y + 34, "Rigid foundation", 12, th.muted)
    else:
        s.rect(x0 - 40, base_y, 2 * half + 80, 24, th.panel, th.fg, sw=1.8)
        s.text(cx, base_y + 17, "Baseplate ≥ 100 kg", 11, th.muted)
        for sx in (x0 - 16, x1 + 16):
            _spring_v(
                s, sx, base_y + 24, base_y + 96, th.muted, coils=3, width=9.0, sw=1.6
            )
        s.line(x0 - 40, base_y + 96, x1 + 40, base_y + 96, th.muted, 1.6)

    # Resilient specimen (soft diagonal hatching) and the load plate on it.
    s.rect(x0, spec_top, x1 - x0, spec_h, th.panel, th.accent, sw=1.8)
    for hx in range(int(x0) + 12, int(x1) + 1, 20):
        s.line(hx, spec_top, hx - 10, base_y, th.accent, 0.9)
    s.rect(x0 - 8, plate_top, x1 - x0 + 16, plate_h, th.panel, th.primary, rx=3, sw=2.0)

    # Excitation: on the load plate, or under the baseplate from below.
    if drive_plate:
        _exciter(s, cx - 30.0, plate_top, stinger=16.0, w=52.0, h=32.0)
        s.arrow(cx - 30.0, plate_top - 13, cx - 30.0, plate_top - 1, th.secondary, 2.0)
        s.text(cx - 30.0, plate_top - 58, "$F$", 14, th.secondary, bold=True)
    else:
        _exciter(s, cx, base_y + 24, stinger=18.0, w=52.0, h=32.0, up=True)
        s.arrow(cx, base_y + 38, cx, base_y + 26, th.secondary, 2.0)
        s.text(cx - 40, base_y + 52, "$F$", 14, th.secondary, anchor="end", bold=True)

    _accel(s, cx + 38.0, plate_top)
    if both:
        _accel(s, x1 + 24.0, base_y)


def _d_dynamic_stiffness_rig(s: SVG, th: Theme) -> None:
    """EN 29052-1 rig: the three excitation arrangements of Figures 1 to 3,
    the specimen preparation of Clauses 5 and 6, and the Formula 4 reading.
    """
    s.text(
        450,
        56,
        "The three excitation arrangements (Figures 1 to 3)",
        18,
        th.fg,
        bold=True,
    )

    base_y = 300.0
    _dsr_arrangement(
        s,
        th,
        158.0,
        base_y,
        rigid=True,
        drive_plate=True,
        both=False,
        title="Rigid base",
        note="load plate measured",
    )
    _dsr_arrangement(
        s,
        th,
        450.0,
        base_y,
        rigid=False,
        drive_plate=True,
        both=True,
        title="Isolated baseplate",
        note="load plate driven, both measured",
    )
    _dsr_arrangement(
        s,
        th,
        742.0,
        base_y,
        rigid=False,
        drive_plate=False,
        both=True,
        title="Isolated baseplate",
        note="baseplate driven, both measured",
    )
    s.text(
        450,
        440,
        "all three are equivalent; sinusoidal excitation is the reference "
        "method in case of dispute (7.1)",
        13,
        th.muted,
        italic=True,
    )

    # ===== The specimen under the plate, and what the standard fixes =====
    s.text(215, 502, "Specimen and load (Clauses 5 and 6)", 16, th.fg, bold=True)
    gy = 690.0
    s.ground(gy, 60, 320)
    x0, x1 = 110.0, 300.0
    spec_top, plate_h, bed_h = 626.0, 24.0, 9.0
    plate_top = spec_top - bed_h - plate_h
    s.rect(x0, spec_top, x1 - x0, gy - spec_top, th.panel, th.accent, sw=2)
    for hx in range(int(x0) + 14, int(x1) + 1, 22):
        s.line(hx, spec_top, hx - 12, gy, th.accent, 0.9)
    # Plaster bed on its foil, between the specimen and the load plate.
    s.rect(x0, spec_top - bed_h, x1 - x0, bed_h, th.panel, th.secondary, sw=1.4)
    s.rect(
        x0 - 10, plate_top, x1 - x0 + 20, plate_h, th.panel, th.primary, rx=3, sw=2.2
    )
    s.line(x1, spec_top - bed_h / 2, 312, 566, th.secondary, 1.1, dash="3,3")
    s.text(
        318,
        562,
        "plaster of Paris ≥ 5 mm on 0.02 mm foil",
        11,
        th.secondary,
        anchor="start",
    )
    s.text(318, 592, "Load plate, steel", 13, th.fg, anchor="start", bold=True)
    s.text(
        318, 611, "(200 ± 3) mm square, flat to 0.5 mm", 11, th.muted, anchor="start"
    )
    s.text(
        318, 629, "8 kg ± 0.5 kg with every device on it", 11, th.muted, anchor="start"
    )
    s.text(
        318,
        657,
        "Resilient specimen, 200 mm × 200 mm",
        13,
        th.fg,
        anchor="start",
        bold=True,
    )
    s.text(
        318, 676, "three of them; irregularities < 3 mm", 11, th.muted, anchor="start"
    )
    s.dim(x0, spec_top, x0, gy, "$d$", offset=-30, size=15)
    # Petroleum-jelly fillet, closed-cell materials only.
    s.path(
        f"M {x0} {gy} L {x0} {gy - 13} Q {x0 - 15} {gy - 5} {x0 - 17} {gy} Z",
        fill=th.secondary,
        stroke=th.secondary,
        sw=1.0,
    )
    s.line(x0 - 12, gy - 4, 96, 722, th.secondary, 1.1, dash="3,3")
    s.text(
        100,
        726,
        "petroleum-jelly fillet (closed-cell materials)",
        11,
        th.secondary,
        anchor="start",
    )

    # Headline relations, under the specimen half.
    s.text(
        258, 776, "$s′_t = 4π^2 m′_t f_r^2$   (Formula 4)", 17, th.primary, bold=True
    )
    s.text(258, 806, "$f_0 = (1/2π)·√(s′/m′)$   (Formula 2)", 14, th.muted)

    # ===== Right: the mass-spring reading and the response peak =====
    s.text(700, 502, "Mass-spring model", 16, th.fg, bold=True)
    mx = 700.0
    s.rect(mx - 52, 534, 104, 46, th.panel, th.primary, rx=8, sw=2.2)
    s.text(mx, 563, "$m′_t$", 17, th.fg, bold=True)
    _spring_v(s, mx, 580, 640, th.accent, coils=4)
    s.text(mx + 24, 618, "$s′_t$", 16, th.accent, anchor="start", bold=True)
    s.ground(640, mx - 62, mx + 62)
    _motion_arrows(s, mx - 78, 557, 20, th.secondary)

    ax0, ax1, base = 590.0, 862.0, 800.0
    s.line(ax0, base, ax1, base, th.muted, 1.4)
    s.line(ax0, base, ax0, 700.0, th.muted, 1.4)
    pk = 700.0
    s.path(
        f"M {ax0 + 6} {base - 10} C {pk - 56} {base - 14} {pk - 30} 712 "
        f"{pk} 710 C {pk + 30} 712 {pk + 64} {base - 7} {ax1 - 6} {base - 3}",
        stroke=th.primary,
        sw=2.4,
    )
    s.line(pk, base, pk, 712, th.muted, 1.2, dash="4,3")
    s.text(pk, base + 20, "$f_r$", 15, th.secondary, bold=True)
    s.text(
        (ax0 + ax1) / 2,
        base + 44,
        "read at the peak, extrapolated to zero force",
        12,
        th.muted,
        italic=True,
    )


# ---------------------------------------------------------------------------
# Porous absorber on a rigid wall (equivalent fluid, JCA parameters)
# ---------------------------------------------------------------------------


def _d_porous_layer(s: SVG, th: Theme) -> None:
    """Section of a 50 mm mineral-wool layer on a rigid backing under a
    normal-incidence plane wave, with a magnified microstructure detail and
    the JCA parameter set of the guide's material (sigma = 20 kPa.s/m2,
    phi = 0.98, alpha_inf = 1, Lambda = Lambda' = 87 um); the layered
    absorber solves alpha = 0.91 at 1 kHz.
    """
    lay_l, lay_r = 560.0, 700.0  # 140 px for 50 mm
    top, bot = 100.0, 430.0

    # Rigid backing and the porous layer with a deterministic fibre texture.
    s.rect(lay_r, top, 34, bot - top, th.fg)
    s.text(784, 458, "Rigid backing", 14, th.muted)
    s.rect(lay_l, top, lay_r - lay_l, bot - top, th.panel, th.secondary, sw=2)
    for i in range(80):
        h1 = math.sin(i * 12.9898) * 43758.5453
        h1 -= math.floor(h1)
        h2 = math.sin(i * 78.233) * 24634.6345
        h2 -= math.floor(h2)
        h3 = math.sin(i * 39.425) * 11369.535
        h3 -= math.floor(h3)
        cx = lay_l + 8 + h1 * (lay_r - lay_l - 16)
        cy = top + 10 + h2 * (bot - top - 20)
        ang = h3 * math.pi
        dx, dy = 7.0 * math.cos(ang), 7.0 * math.sin(ang)
        s.line(cx - dx, cy - dy, cx + dx, cy + dy, th.muted, 1.0)
    s.text(630, 88, "Porous layer (mineral wool)", 15, th.fg, bold=True)
    s.dim(lay_l, bot, lay_r, bot, "$d$ = 50 mm", offset=30, size=15)

    # Incident and reflected waves, and the decaying wave inside the layer.
    s.arrow(300.0, 240.0, lay_l - 8, 240.0, th.accent, 2.4)
    s.text(420, 268, "plane wave, normal incidence", 14, th.accent)
    s.arrow(lay_l - 8, 300.0, 445.0, 300.0, th.secondary, 1.6)
    s.text(438, 348, "reflected: $|R|^2 = 1 − α$ = 0.09", 13, th.secondary)
    d = f"M {lay_l + 2:.0f} 240"
    for i in range(1, 35):
        x = lay_l + 2 + i * 4.0
        amp = 26.0 * math.exp(-i / 12.0)
        d += f" L {x:.1f} {240 - amp * math.sin(i * 0.9):.1f}"
    s.path(d, stroke=th.primary, sw=1.8)

    # Magnified microstructure: sampled spot on the layer, blown-up circle.
    s.circle(610.0, 160.0, 16.0, "none", th.fg, 1.6)
    s.circle(170.0, 185.0, 92.0, th.panel, th.fg, 2.0)
    s.line(597.0, 150.0, 253.0, 148.0, th.muted, 1.0, dash="4,4")
    s.line(600.0, 173.0, 246.0, 232.0, th.muted, 1.0, dash="4,4")
    for i in range(11):
        h1 = math.sin(i * 21.9898) * 43758.5453
        h1 -= math.floor(h1)
        h2 = math.sin(i * 57.233) * 24634.6345
        h2 -= math.floor(h2)
        h3 = math.sin(i * 93.719) * 11369.535
        h3 -= math.floor(h3)
        ang0 = h3 * math.pi
        r0 = 12.0 + h2 * 62.0
        cx = 170.0 + (h1 - 0.5) * 2 * r0 * math.cos(ang0)
        cy = 185.0 + (h1 - 0.5) * 2 * r0 * math.sin(ang0)
        dx, dy = 34.0 * math.cos(ang0 + 1.1), 34.0 * math.sin(ang0 + 1.1)
        # Clip fibre ends into the circle by shortening long excursions.
        s.line(cx - dx, cy - dy, cx + dx, cy + dy, th.secondary, 3.0)
    s.text(170, 80, "microstructure (zoom)", 14, th.fg, bold=True)
    # Starting further left, so that the Spanish ends short of the leader
    # from the next label, which ran through its last word.
    s.text(64, 304, "fibre frame", 13, th.secondary, anchor="start")
    s.line(120.0, 292.0, 140.0, 252.0, th.muted, 1.0)
    s.text(190, 322, "air in the pores: $φ$ = 0.98", 13, th.fg, anchor="start")
    s.line(214.0, 314.0, 200.0, 262.0, th.muted, 1.0)

    # JCA parameter block (the guide's material).
    for yy, txt in (
        (368.0, "$σ$ = 20 kPa·s/m²  (flow resistivity)"),
        (392.0, "$φ$ = 0.98  (porosity)"),
        (416.0, "$α_∞$ = 1.0  (tortuosity)"),
        (440.0, "$Λ = Λ′$ = 87 µm  (viscous / thermal lengths)"),
    ):
        s.text(60, yy, txt, 14, th.fg, anchor="start")

    # --- captions ----------------------------------------------------------
    s.text(
        80,
        500,
        "JCA equivalent fluid: five parameters give $Z_c$ and $k$; a "
        "hard-backed layer has $Z_s = −j Z_c cot(k·d)$",
        15,
        th.fg,
        anchor="start",
    )
    s.text(
        80,
        528,
        "$α = 1 − |R|^2$ = 0.91 at 1 kHz for this 50 mm layer",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )
    s.text(
        80,
        556,
        "viscous friction in the pores and heat exchange with the frame dissipate the sound energy",
        15,
        th.muted,
        anchor="start",
    )


# ---------------------------------------------------------------------------
# d24 - ISO 354 reverberation-room sound absorption
# ---------------------------------------------------------------------------


def _d_iso354_room(s: SVG, th: Theme) -> None:
    """ISO 354 reverberation-room absorption measurement (plan + two states)."""
    # --- The room in plan, with non-parallel walls (Clause 6.1.2) ----------
    s.path("M 46 100 L 596 82 L 610 424 L 60 410 Z", fill=th.panel, stroke=th.fg, sw=3)
    s.text(60, 76, "Reverberation room · plan", 17, th.fg, bold=True, anchor="start")
    s.text(596, 76, "$V$ = 200 m³ (≥ 150 m³)", 15, th.muted, anchor="end")

    # Suspended diffusers near the ceiling (Annex A.1).
    for dx, dy, tilt in (
        (132.0, 164.0, 14.0),
        (232.0, 150.0, -20.0),
        (334.0, 166.0, 12.0),
        (436.0, 152.0, -14.0),
    ):
        s.path(
            f"M {dx - 32} {dy + tilt} Q {dx} {dy - 12} {dx + 32} {dy - tilt}",
            stroke=th.muted,
            sw=3.0,
        )
    s.text(284, 120, "diffusers  0.8–3 m² each, ≈ 5 kg/m² (Annex A)", 13, th.muted)

    # --- Test specimen on the floor, edges deliberately non-parallel ------
    ax_, ay = 122.0, 296.0  # corners, clockwise from top left
    bx, by = 316.0, 272.0
    cx_, cy = 330.0, 372.0
    dx_, dy = 136.0, 396.0
    s.path(
        f"M {ax_} {ay} L {bx} {by} L {cx_} {cy} L {dx_} {dy} Z",
        fill=th.bg,
        stroke=th.secondary,
        sw=2.4,
    )
    for i in range(1, 14):  # hatch parallel to the short edges
        t = i / 14.0
        s.line(
            ax_ + t * (bx - ax_),
            ay + t * (by - ay),
            dx_ + t * (cx_ - dx_),
            dy + t * (cy - dy),
            th.secondary,
            1.0,
        )
    s.text(226, 262, "Test specimen  $S$ = 10.8 m²", 15, th.secondary, bold=True)
    s.text(
        226,
        452,
        "10–12 m², width/length 0.7–1, no edge parallel to the room",
        13,
        th.muted,
    )
    # Clearance from the nearest room boundary (Clause 6.2.1.2).
    s.dim(66.0, 340.0, 122.0, 340.0, "≥ 0.75 m", offset=0, size=13)

    # --- Two source and three microphone positions (Clause 7.1) -----------
    for sx, sy, lab in ((470.0, 200.0, "S1"), (548.0, 344.0, "S2")):
        s.rect(sx - 19, sy - 25, 38, 50, th.panel, th.primary, rx=6, sw=2)
        s.circle(sx, sy, 10, th.primary)
        s.circle(sx, sy, 4, th.bg)
        s.text(sx + 26, sy + 5, lab, 14, th.fg, bold=True, anchor="start")
    s.line(470, 200, 548, 344, th.muted, 1.1, dash="4,4")
    s.text(478, 288, "≥ 3 m", 13, th.muted, anchor="end")

    for mx, my, lab in (
        (392.0, 186.0, "M1"),
        (392.0, 296.0, "M2"),
        (446.0, 386.0, "M3"),
    ):
        s.circle(mx, my, 7, th.fg)
        s.circle(mx, my, 2.6, th.bg)
        s.text(mx - 12, my + 5, lab, 14, th.fg, bold=True, anchor="end")
    s.line(392, 186, 392, 296, th.muted, 1.1, dash="4,4")
    s.text(400, 246, "≥ 1.5 m", 13, th.muted, anchor="start")
    s.text(
        400,
        480,
        "microphones ≥ 1.5 m apart, ≥ 2 m from a source, ≥ 1 m from any "
        "surface and from the specimen",
        13,
        th.muted,
    )

    # --- Right column: the two states the whole method rests on -----------
    # The panel and its title are sized on the English "The measurement is
    # a difference", 260 px against the 223 of its Spanish twin: here it is
    # the English that is the longer of the two.
    s.rect(618, 82, 264, 342, th.bg, th.muted, rx=8, sw=1.6)
    s.text(750, 114, "The measurement is a difference", 13, th.fg, bold=True)
    for top, title, note, col in (
        (146.0, "1 · empty room", "$T_1$  →  $A_1$", th.primary),
        (274.0, "2 · specimen installed", "$T_2$  →  $A_2$", th.secondary),
    ):
        s.text(750, top, title, 14, col, bold=True)
        s.path(
            f"M 656 {top + 14} L 842 {top + 8} L 848 {top + 78} L 660 {top + 84} Z",
            fill=th.panel,
            stroke=th.fg,
            sw=1.8,
        )
        if top > 200:
            s.rect(690, top + 34, 92, 26, th.bg, th.secondary, sw=1.8)
            for hx in range(696, 782, 12):
                s.line(hx, top + 57, hx + 14, top + 37, th.secondary, 0.9)
        s.text(750, top + 106, note, 16, col, bold=True)
    s.text(750, 412, "$α_s = (A_2 − A_1) / S$", 16, th.accent, bold=True)

    # --- Mounting strip: Type A on the floor, and a Type E air space ------
    s.text(
        60,
        524,
        "Annex B mounting (part of the result)",
        15,
        th.fg,
        bold=True,
        anchor="start",
    )
    for x0, lab, gap in (
        (80.0, "Type A: directly on the rigid floor", 0.0),
        (470.0, "Type E-400: 400 mm face to floor", 30.0),
    ):
        base = 590.0
        s.line(x0 - 14, base, x0 + 224, base, th.fg, 3.0)
        s.rect(x0 + 30, base - 16 - gap, 150, 16, th.bg, th.secondary, sw=1.8)
        for hx in range(int(x0) + 36, int(x0) + 176, 12):
            s.line(hx, base - 2 - gap, hx + 10, base - 15 - gap, th.secondary, 0.9)
        if gap:
            s.dim(
                x0 + 196,
                base,
                x0 + 196,
                base - 16 - gap,
                "400 mm",
                offset=26,
                size=12,
                label_side="right",
            )
        else:
            s.rect(x0 + 16, base - 16, 14, 16, th.fg)
            s.rect(x0 + 180, base - 16, 14, 16, th.fg)
            s.text(x0 + 105, base - 28, "perimeter frame, flush", 12, th.muted)
        s.text(x0 + 105, base + 24, lab, 13, th.fg)

    # --- Governing relations and acceptance checks ------------------------
    for y, txt, col, bold in (
        (
            646,
            "$A = 55.3 V/(c T) − 4 V m$   ·   $c = 331 + 0.6 t$  (15–30 °C)",
            th.fg,
            True,
        ),
        (
            672,
            (
                "≥ 12 spatially independent decays = ≥ 3 microphones × ≥ 2 sources "
                "· $T_{20}$ read from −5 dB over 20 dB"
            ),
            th.muted,
            False,
        ),
        (
            696,
            (
                "the empty-room $A_1$ must clear the Table 1 ceiling, and "
                "$T_1$ is measured without the specimen frame"
            ),
            th.muted,
            False,
        ),
    ):
        s.text(450, y, txt, 15 if bold else 13, col, bold=bold)


# ---------------------------------------------------------------------------
# EN 16487 suspended ceiling specimen in the ISO 354 room
# ---------------------------------------------------------------------------


def _d_suspended_ceiling_specimen(s: SVG, th: Theme) -> None:
    """The EN 16487 specimen: what the test code fixes before ISO 354 measures.

    Three views of one arrangement. In plan, the 10,80 m2 of 4.1.1.1.1 built
    from thirty 0,6 m test objects (4.1.1.1.2), five by six, butted with no
    seal and no grid over the joints (4.1.1.1.3, 4.1.1.2.3.3), turned at least
    10 degrees off the room walls together with its fixture (4.1.1.1.5), and
    no nearer a room edge than the 0,75 m of EN ISO 354, 6.2.1.2. In section,
    the type E mounting of 4.1.1.2.3 standing face up on the floor, which
    EN ISO 354, B.4 allows unless gravity changes the answer and 4.1.1.2.3.7
    then holds a loose porous backing to the tile with a wire grid: 200 mm
    from the floor to the exposed face and not sunk into the floor, which are
    both conditions of the data CE marking is compiled from rather than of
    every measurement, the 200 mm recommended by 4.1.1.2.3.1 and required of
    that data, the embedded arrangement ruled out by 4.1.1.2.3.2 for the
    purpose of CE marking; the face flush with a solid fixture of 20 kg/m2 or
    more whose joints are taped or sealed (4.1.1.1.4, 4.1.1.1.6, 4.1.1.1.7),
    the substructure of 4.1.1.2.3.4 on the supports of 4.1.1.2.3.6, each named
    by a leader because in every bay the profile stands on its support, and the
    deflection of 4.1.1.2.3.5; seen from below, which is Figure 5, the
    supports along each profile. Beside them the two runs the result is a
    difference of, with the climate of 4.2 and 5.2, and at the foot
    EN ISO 354 Formulae (8) and (9) with the cap 4.2.1 puts on the part of
    them that is the air.
    """
    # --- In plan: the room floor, and the specimen turned off its walls ----
    s.text(
        240, 70, "The specimen on the room floor, in plan", 15, th.primary, bold=True
    )
    s.rect(24, 88, 432, 242, "none", th.fg, sw=2.6)
    scale, cx, cy = 36.0, 140.0, 212.0  # px per metre, centre of the specimen
    tilt = math.radians(12.0)  # at least the 10 degrees 4.1.1.1.5 aims at

    def at(u: float, v: float) -> tuple[float, float]:
        """A point of the specimen, in metres along its 3.6 m and 3.0 m sides."""
        du, dv = u - 1.8, v - 1.5
        return (
            cx + scale * (du * math.cos(tilt) - dv * math.sin(tilt)),
            cy + scale * (du * math.sin(tilt) + dv * math.cos(tilt)),
        )

    def outline(u0: float, v0: float, u1: float, v1: float) -> str:
        corners = (at(u0, v0), at(u1, v0), at(u1, v1), at(u0, v1))
        return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in corners) + " Z"

    # The fixture round the perimeter, then the thirty test objects on it.
    s.path(outline(-0.1, -0.1, 3.7, 3.1), fill=th.fg)
    s.path(outline(0.0, 0.0, 3.6, 3.0), fill=th.panel, stroke=th.secondary, sw=1.8)
    for i in range(1, 6):
        (x0, y0), (x1, y1) = at(0.6 * i, 0.0), at(0.6 * i, 3.0)
        s.line(x0, y0, x1, y1, th.secondary, 1.0)
    for j in range(1, 5):
        (x0, y0), (x1, y1) = at(0.0, 0.6 * j), at(3.6, 0.6 * j)
        s.line(x0, y0, x1, y1, th.secondary, 1.0)

    # The angle to the wall and the clearance to it, read at the fixture corner.
    fx, fy = at(-0.1, -0.1)
    s.line(fx, fy, fx + 104, fy, th.muted, 1.1, dash="4,3")
    r = 80.0
    s.path(
        f"M {fx + r:.1f} {fy:.1f} A {r} {r} 0 0 1 "
        f"{fx + r * math.cos(tilt):.1f} {fy + r * math.sin(tilt):.1f}",
        stroke=th.fg,
        sw=1.6,
    )
    s.text(fx + 110, fy + 5, "≥ 10°", 13, th.fg, anchor="start")
    s.dim(fx, 88, fx, fy, "≥ 0.75 m", size=12, label_side="right")

    s.text(342, 152, "$S$ = 10.80 m²", 15, th.secondary, bold=True)
    for n, line in enumerate(
        (
            "30 test objects, 5 by 6,",
            "0.6 m × 0.6 m, butted together",
            "joints unsealed, no grid over them",
        )
    ):
        s.text(342, 178 + 18 * n, line, 12, th.fg)
    s.text(342, 248, "the fixture covers the perimeter,", 12, th.muted)
    s.text(342, 266, "its edges angled as well", 12, th.muted)
    s.text(
        240,
        352,
        "no part within 0.75 m of a room edge, and 1 m where possible",
        12,
        th.muted,
    )

    # --- The two runs the coefficient is a difference of --------------------
    s.rect(474, 52, 406, 314, th.bg, th.muted, rx=8, sw=1.4)
    s.text(677, 78, "The absorption is a difference of two runs", 14, th.fg, bold=True)
    for top, title, symbol, colour, fitted in (
        (
            96.0,
            "1 · empty room, fixture taken out",
            "$T_1$  →  $A_1$",
            th.primary,
            False,
        ),
        (184.0, "2 · specimen in its fixture", "$T_2$  →  $A_2$", th.secondary, True),
    ):
        s.path(
            f"M 494 {top + 8} L 578 {top + 4} L 582 {top + 68} L 498 {top + 72} Z",
            fill=th.panel,
            stroke=th.fg,
            sw=1.6,
        )
        if fitted:
            s.path(
                f"M 522 {top + 26} L 552 {top + 32} L 548 {top + 54} L 518 {top + 48} Z",
                fill=th.fg,
            )
            s.path(
                f"M 524 {top + 28} L 550 {top + 33} L 547 {top + 52} L 520 {top + 47} Z",
                fill=th.bg,
                stroke=th.secondary,
                sw=1.2,
            )
        s.text(600, top + 22, title, 14, colour, bold=True, anchor="start")
        s.text(
            600, top + 46, "temperature and humidity checked", 12, th.fg, anchor="start"
        )
        s.text(600, top + 70, symbol, 15, colour, anchor="start")
    for n, note in enumerate(
        (
            "relative humidity ≥ 50 %, humidifier off while measuring",
            "empty room at least once a day, in stable conditions,",
            "and again the same day if the air correction passes 0.05",
            "no microphone plane parallel to a room surface",
        )
    ):
        s.text(677, 284 + 20 * n, note, 12, th.muted)

    # --- In section: type E at 200 mm, face up on the floor -----------------
    # 0.36 px per mm across, 0.62 px per mm up: the 200 mm is drawn 124 px tall.
    floor, face = 612.0, 488.0
    back = face + 12  # the back of the test objects, where the profiles sit
    s.text(
        300, 398, "In section: type E, 200 mm deep, face up", 15, th.primary, bold=True
    )
    s.text(
        300, 418, "on the floor, not sunk into it, as CE marking requires", 12, th.muted
    )
    s.ground(floor, 40, 592)
    s.rect(70, face, 16, floor - face, th.fg)  # the fixture, solid
    s.rect(86, face, 486, 12, th.panel)
    s.line(86, face, 572, face, th.secondary, 1.8)
    s.line(86, back, 572, back, th.secondary, 1.8)
    for joint in (302.0, 518.0):
        s.line(joint, face, joint, back, th.secondary, 1.6)
    # Three profile shapes, as Figure 4 draws them: an angle on the fixture,
    # a box and a tee under the joints, each inside 30 mm by 50 mm.
    s.rect(86, back, 4, 31, th.primary)
    s.rect(86, back, 10, 4, th.primary)
    s.rect(297, back, 10, 31, th.primary)
    s.rect(299.5, back + 4, 5, 23, th.bg)
    s.rect(513, back, 10, 4, th.primary)
    s.rect(516, back + 4, 4, 27, th.primary)
    for post in (302.0, 518.0):
        s.rect(post - 9, back + 31, 18, floor - back - 31, th.panel, th.fg, sw=1.6)
    s.line(572, face - 16, 572, floor + 10, th.muted, 1.2, dash="12,4,2,4")
    # Tape over the joint at the face, lapping no further onto the specimen
    # than Detail A allows, and the fixture sealed where it meets the floor,
    # as Details A and B of Figure 2 draw them.
    s.line(70, face - 1.5, 90, face - 1.5, th.accent, 3.6)
    s.path(
        f"M 52 {floor - 2} L 68 {floor - 2} L 68 {floor - 14}", stroke=th.accent, sw=3.2
    )
    s.path(
        f"M 308 {back} Q 410 {back + 20} 512 {back}",
        stroke=th.secondary,
        sw=1.3,
        dash="5,4",
    )
    s.text(410, back + 34, "deflection ≤ 5 mm at any point", 12, th.secondary)
    s.text(410, floor - 18, "closed air space, no partitions", 12, th.muted)
    s.dim(150, floor, 150, face, "200 mm", size=13, label_side="right")
    # 11 px in Spanish, so that it ends short of the leader to the profile.
    depth = "overall depth"
    s.text(
        159,
        (floor + face) / 2 + 24,
        depth,
        s.fit_size([depth], [12, 11], 96),
        th.muted,
        anchor="start",
    )
    s.dim(86, face, 302, face, "≈ 0.6 m", offset=-24, size=12)
    s.dim(302, face, 518, face, "≈ 0.6 m", offset=-24, size=12)
    s.text(
        44,
        440,
        "joint taped or sealed, the face flush with the fixture top",
        12,
        th.accent,
        anchor="start",
    )
    s.line(60, 446, 72, face - 6, th.accent, 1.0)
    # Leaders to the two parts that stand one above the other in every bay:
    # the blue member is the substructure profile and the post under it the
    # support unit, in both bays, so neither heading can be read as naming
    # the column it sits under.
    s.path(
        f"M 234 {floor + 28} L 274 {floor - 56} L 296 {back + 20}",
        stroke=th.primary,
        sw=1.0,
    )
    s.line(562, floor + 28, 529, floor - 20, th.fg, 1.0)
    for x, head, notes, colour in (
        (78.0, "mounting fixture", ("solid, ≥ 20 kg/m²", "sealed to the floor"), th.fg),
        (302.0, "substructure profile", ("≤ 30 mm wide, ≤ 50 mm high",), th.primary),
        (518.0, "support unit", ("≤ 50 mm × 50 mm",), th.fg),
    ):
        s.text(x, floor + 32, head, 12, colour, bold=True)
        for n, note in enumerate(notes):
            s.text(x, floor + 50 + 18 * n, note, 12, th.muted)
    s.text(
        300,
        700,
        "face up only where gravity does not change the answer: a loose porous backing",
        12,
        th.muted,
    )
    s.text(
        300,
        718,
        "is held to the tile by a wire grid, ≤ 2 mm wire, ≈ 100 mm mesh",
        12,
        th.muted,
    )

    # --- Seen from below: the supports along each profile (Figure 5) --------
    s.text(752, 398, "Seen from below", 15, th.primary, bold=True)
    top, left = 418.0, 636.0  # 0.11 px per mm: 0.6 m is 66 px, 1.2 m is 132 px
    s.rect(left, top, 236, 10, th.fg)
    s.rect(left, top, 10, 200, th.fg)
    s.rect(left + 10, top + 10, 226, 4, th.primary)
    s.rect(left + 10, top + 10, 4, 190, th.primary)
    for profile in (712.0, 778.0):
        s.rect(profile - 3, top + 14, 6, 186, th.primary)
        # The support end is a symbol: 50 mm would be 5 px at this scale.
        s.rect(profile - 5, top + 139, 10, 10, th.panel, th.fg, sw=1.4)
    s.line(630, top + 206, 878, top + 206, th.muted, 1.2, dash="12,4,2,4")
    s.dim(822, top + 12, 822, top + 144, "≥ 1.2 m", size=12, label_side="right")
    s.dim(712, top + 178, 778, top + 178, "≈ 0.6 m", size=12)
    s.text(754, floor + 32, "profiles in one direction,", 12, th.fg)
    s.text(754, floor + 50, "supports ≥ 1.2 m apart", 12, th.muted)

    # --- What the two runs give, and the cap on the air's share of it -------
    box = 740.0
    s.rect(40, box, 820, 92, th.panel, th.fg, rx=6, sw=1.6)
    s.text(245, box + 32, "$α_s = (A_2 − A_1)/S$", 17, th.primary)
    s.text(650, box + 32, "$|Δα| = |4V(m_2 − m_1)/S|$ ≤ 0.05", 17, th.secondary)
    s.text(245, box + 58, "the specimen, with $S$ over the test objects", 12, th.fg)
    s.text(
        650, box + 58, "the change in air absorption, capped in every band", 12, th.fg
    )
    s.text(
        450,
        box + 80,
        "the uncertainty of Table 1 holds for this mounting alone: "
        "a plane absorber, type E, 200 mm",
        12,
        th.muted,
    )


# ---------------------------------------------------------------------------
# d25 - ISO 10534-1 standing-wave-ratio apparatus
# ---------------------------------------------------------------------------


def _d_standing_wave_tube(s: SVG, th: Theme) -> None:
    """ISO 10534-1 standing-wave apparatus: probe carriage and the minima."""
    tube_top, tube_bot, mid = 216.0, 346.0, 281.0
    tube_l, tube_r = 156.0, 838.0
    back_w, spec_w = 22.0, 46.0
    face = tube_r - back_w - spec_w  # the specimen face: x = 0

    # --- Tube, source and specimen ---------------------------------------
    s.rect(tube_l, tube_top, tube_r - tube_l, tube_bot - tube_top, th.bg, th.fg, sw=3)
    s.rect(58, mid - 44, 66, 88, th.panel, th.primary, rx=6, sw=2)
    s.path(
        f"M 124 {mid - 17} L 124 {mid + 17} L {tube_l} {tube_bot} "
        f"L {tube_l} {tube_top} Z",
        fill=th.panel,
        stroke=th.primary,
        sw=2,
    )
    s.circle(90, mid, 11, th.primary)
    s.text(92, 180, "Loudspeaker", 16, th.fg, bold=True)
    s.text(92, 202, "one pure tone at a time", 13, th.muted)

    s.rect(tube_r - back_w, tube_top, back_w, tube_bot - tube_top, th.fg)
    s.rect(face, tube_top, spec_w, tube_bot - tube_top, th.panel, th.secondary, sw=2)
    for hx in range(int(face) + 8, int(face + spec_w), 11):
        s.line(hx, tube_bot - 4, hx - 15, tube_top + 4, th.secondary, 1.0)
    s.text(
        tube_r,
        202,
        "Test specimen on the rigid backing",
        15,
        th.secondary,
        bold=True,
        anchor="end",
    )
    s.line(face, 208, face, tube_bot + 14, th.accent, 1.6, dash="5,4")
    s.text(face + 6, tube_bot + 26, "$x = 0$", 14, th.accent, bold=True, anchor="start")

    # --- Graduated rail and the probe carriage ----------------------------
    rail_y, car_x = 150.0, 430.0
    s.line(tube_l + 24, rail_y, face, rail_y, th.fg, 2.4)
    x_tick = face
    while x_tick > tube_l + 24:
        s.line(x_tick, rail_y, x_tick, rail_y - 8, th.muted, 1.0)
        x_tick -= 26.0
    s.rect(car_x - 34, rail_y - 2, 68, 24, th.panel, th.primary, rx=5, sw=2)
    s.line(car_x, rail_y + 22, car_x, mid, th.fg, 2.4)
    s.circle(car_x, mid, 5.5, th.fg)
    s.text(
        car_x,
        rail_y - 20,
        "probe microphone on a graduated carriage",
        14,
        th.fg,
        bold=True,
    )
    s.arrow(car_x + 42, rail_y + 10, car_x + 116, rail_y + 10, th.accent, 2.0)
    s.arrow(car_x - 42, rail_y + 10, car_x - 116, rail_y + 10, th.accent, 2.0)

    # --- The standing-wave envelope inside the tube, filling in leftwards -
    span = (tube_bot - tube_top) / 2.0 - 8.0
    wavelength = 214.0  # px per acoustic wavelength
    phi = math.radians(-54.1)

    def envelope(x: float) -> float:
        d = face - x
        r_eff = 0.5 * math.exp(-0.0014 * d)  # wall losses, exaggerated
        return math.sqrt(
            1.0
            + r_eff**2
            + 2.0 * r_eff * math.cos(2.0 * math.pi * d / wavelength - phi)
        )

    def y_of(env: float) -> float:
        return mid - (env - 1.0) * span / 0.62

    pts = [
        (x, y_of(envelope(x)))
        for x in [face - 3.0 * i for i in range(int((face - tube_l - 8) / 3))]
    ]
    s.path(
        "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts),
        stroke=th.primary,
        sw=2.4,
    )
    s.text(250, tube_top - 12, "$|p(x)|$ envelope", 14, th.primary)

    # The adjacent maximum and minimum the operator reads.
    x_min1 = face - wavelength * (phi + math.pi) / (2 * math.pi)
    x_max1 = x_min1 - wavelength / 2.0
    for px, lab in ((x_max1, "$L_{max}$"), (x_min1, "$L_{min}$")):
        py = y_of(envelope(px))
        s.circle(px, py, 5.5, th.secondary)
        s.text(px, py - 14, lab, 13, th.secondary, bold=True)
    # The label under the dimension's foot: level with its middle, the
    # envelope ran through it.
    s.dim(
        x_max1 - 46,
        y_of(envelope(x_max1)),
        x_max1 - 46,
        y_of(envelope(x_min1)),
        "",
        offset=0,
        size=14,
        label_side="left",
    )
    s.text(x_max1 - 54, y_of(envelope(x_min1)) + 16, "$ΔL$ = 9.54 dB", 14, th.fg, "end")
    s.line(
        x_max1 - 52,
        y_of(envelope(x_max1)),
        x_max1,
        y_of(envelope(x_max1)),
        th.muted,
        0.9,
        dash="3,3",
    )
    s.line(
        x_max1 - 52,
        y_of(envelope(x_min1)),
        x_min1,
        y_of(envelope(x_min1)),
        th.muted,
        0.9,
        dash="3,3",
    )
    # The label under the dimension, which is narrower than it: above, the
    # two witness lines ran through it.
    s.dim(x_min1, tube_bot + 14, face, tube_bot + 14, "", offset=46, size=14)
    s.text((x_min1 + face) / 2, tube_bot + 80, "$x_{min,1}$ = 12 cm", 14, th.fg)
    s.text(
        340,
        tube_bot + 104,
        "minima far from the specimen fill in (wall losses, exaggerated "
        "here): read the nearest one",
        13,
        th.muted,
    )

    # --- The reduction chain, verbatim from the guide ---------------------
    for i, txt in enumerate(
        (
            "$s = 10^{ΔL/20}$ = 3",
            "$|r| = (s − 1)/(s + 1)$ = 0.5",
            "$α = 1 − |r|^2$ = 0.75",
            "$Φ = 4π x_{min,1}/λ − π$ = −54.1°",
            "$Z/ρc_0 = (1 + r)/(1 − r)$ = 1.13 − 1.22j",
        )
    ):
        s.text(450, 490 + 24 * i, txt, 15, th.fg)
    s.text(
        450,
        622,
        "one channel: the microphone sensitivity cancels and there is no "
        "inter-channel phase error",
        15,
        th.accent,
        bold=True,
    )
    s.text(
        450,
        648,
        "magnitude from the ratio, phase from the position, which is why "
        "Part 1 is the arbitration method",
        13,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Slow-sound slit panel: the transfer-matrix chain (Jiménez et al. 2016, 2017)
# ---------------------------------------------------------------------------


def _d_slit_absorber_chain(s: SVG, th: Theme) -> None:
    """One period of the slow-sound slit panel as its transfer-matrix chain.

    The panel is the product of Appl. Sci. 2017, 7, 618, page 3: a radiation
    correction at the slit mouth (Eq. (3), with the length of Appl. Phys.
    Lett. 2016 Eq. (A27)), half a lattice step of visco-thermal slit
    (Eq. (2) with Eq. (6)) either side of the Helmholtz resonator, and the
    resonator itself as a shunt point scatterer (Eq. (3)) whose impedance is
    Eq. (A23) with the end corrections of Eqs. (A24) to (A26). The rigid
    backing closes the chain, Eq. (4) turns it into a reflection coefficient,
    and Eq. (9) is the critical-coupling condition in the boxes at the foot,
    written at the normal incidence the design is solved at. Below their own
    resonance the resonators soften the slit rather than stiffen it: Appl.
    Phys. Lett. Eq. (2) divides the slit bulk modulus by a bracket greater
    than one, while Eq. (3) leaves the effective density untouched, which is
    what makes the sound slow. The mouth term carries the added-mass sign the
    library uses (see the errata registry). The numbers are the guide's
    300 Hz design. Along the slit the drawing keeps 20 px per mm: the 30 mm
    step is 600 px, the neck 60 px, the cavity 540 px, the slit height and
    the neck length 20 px each; only the cavity length is drawn short.
    """
    x_face, x_back, x_mid = 180.0, 780.0, 480.0

    s.text(
        450,
        64,
        "One period, one resonator: every piece is a 2 × 2 matrix",
        17,
        th.fg,
        bold=True,
    )

    # Where each matrix acts: the slit, the resonator on its upper wall, the
    # mouth and the backing. The resonator is square in section, so its four
    # numbers are named side and length rather than set as a product.
    s.text(
        x_mid,
        94,
        "neck: 3 mm side, 1 mm long; cavity: 27 mm side, 44.7 mm long",
        13,
        th.accent,
    )
    s.rect(x_face, 104, x_back - x_face, 150, th.panel)
    s.path(f"M {x_face} 214 L {x_face} 104 L {x_back} 104", stroke=th.fg, sw=2.0)
    s.path(f"M {x_face} 234 L {x_face} 254 L {x_back} 254", stroke=th.fg, sw=2.0)
    s.rect(210, 122, 540, 72, th.bg, th.fg, sw=1.8)
    s.rect(x_face, 214, x_back - x_face, 20, th.bg)
    s.rect(451, 192, 58, 24, th.bg)
    s.line(x_face, 214, 450, 214, th.fg, 1.8)
    s.line(510, 214, x_back, 214, th.fg, 1.8)
    s.line(x_face, 234, x_back, 234, th.fg, 1.8)
    s.line(450, 194, 450, 214, th.fg, 1.8)
    s.line(510, 194, 510, 214, th.fg, 1.8)
    s.text(
        x_mid,
        164,
        "Helmholtz resonator, $M_{HR}$ at the middle of the step",
        14,
        th.accent,
        bold=True,
    )
    s.text(315, 229, "slit, $h$ = 0.978 mm", 12, th.primary)
    s.text(645, 229, "closed at the backing", 12, th.primary)
    s.rect(x_back, 96, 20, 166, th.fg)
    y = 100.0
    while y < 256:
        s.line(x_back + 20, y, x_back + 30, y + 8, th.muted, 1.1)
        y += 14
    s.arrow(40, 150, 170, 150, th.accent, 2.4)
    s.text(100, 138, "incident, angle $θ$", 13, th.accent)
    s.arrow(170, 186, 40, 186, th.secondary, 1.8)
    s.text(100, 206, "reflected, $R$", 13, th.secondary)
    s.text(100, 244, "$Z_0 = ρ_0 c_0 / S_0$", 13, th.muted)
    s.dim(x_face, 282, x_mid, 282, "$M_s$ over $a/2$ = 15 mm", size=13)
    s.dim(x_mid, 282, x_back, 282, "$M_s$ over $a/2$ = 15 mm", size=13)
    s.text(x_face, 308, "$M_{Δl}$ at $x_1 = 0$", 13, th.secondary, bold=True)
    s.text(x_mid, 308, "$L = N a$ = 30 mm, here $N$ = 1", 13, th.muted)
    s.text(790, 308, "$v = 0$ at $x_1 = L$", 13, th.fg, bold=True)

    def matrix(
        label: str,
        rows: list[tuple[str, str]],
        colour: str,
        ytop: float,
        x0: float = 112.0,
        x1: float = 322.0,
    ) -> None:
        hgt = 20 * len(rows) + 12
        s.path(
            f"M {x0 + 7} {ytop} L {x0} {ytop} L {x0} {ytop + hgt} "
            f"L {x0 + 7} {ytop + hgt}",
            stroke=colour,
            sw=1.6,
        )
        s.path(
            f"M {x1 - 7} {ytop} L {x1} {ytop} L {x1} {ytop + hgt} "
            f"L {x1 - 7} {ytop + hgt}",
            stroke=colour,
            sw=1.6,
        )
        cw = (x1 - x0) / 2
        for i, (left, right) in enumerate(rows):
            yy = ytop + 21 + 20 * i
            s.text(x0 + cw / 2, yy, left, 12, th.fg)
            s.text(x0 + 1.5 * cw, yy, right, 12, th.fg)
        s.text(x0 - 8, ytop + hgt / 2 + 5, label, 15, colour, "end", bold=True)

    def row(
        top: float,
        height: float,
        colour: str,
        lines: list[tuple[str, int, str, bool]],
    ) -> None:
        s.rect(36, top, 828, height, th.panel, colour, rx=6, sw=1.8)
        for k, (txt, size, fill, bold) in enumerate(lines):
            fitted = s.fit_size([txt], (size, size - 1), 514, bold=bold)
            s.text(338, top + 23 + 20 * k, txt, fitted, fill, "start", bold=bold)

    # The mouth: a series radiation mass (Eq. (3), Eq. (A27)).
    top = 326.0
    row(
        top,
        80,
        th.secondary,
        [
            ("The mouth of the slit radiates: a series mass", 14, th.secondary, True),
            (
                "$Z_{Δl} = jωρ_0 Δl_{slit} / (φ_t S_0)$,   "
                "$Δl_{slit} = h φ_t Σ sin²(nπφ_t) / (nπφ_t)³$",
                13,
                th.fg,
                False,
            ),
            (
                "$φ_t = h/d$ = 0.0196 with $d$ = 50 mm, $S_0 = d a$ = 1500 mm², "
                "so $Δl_{slit}$ = 1.12 mm",
                12,
                th.muted,
                False,
            ),
        ],
    )
    matrix("$M_{Δl}$ =", [("1", "$Z_{Δl}$"), ("0", "1")], th.secondary, top + 16)

    # Half a lattice step of lossy slit (Eq. (2), Eq. (6)).
    top = 414.0
    row(
        top,
        120,
        th.primary,
        [
            (
                "Half a lattice step of lossy slit, either side of the resonator",
                14,
                th.primary,
                True,
            ),
            (
                "$k_s = ω √(ρ_s / κ_s)$,   $Z_s = √(κ_s ρ_s) / S_s$,   $S_s = h a$",
                13,
                th.fg,
                False,
            ),
            (
                "$ρ_s = ρ_0 / [1 − tanh(h G_ρ/2) / (h G_ρ/2)]$,   $G_ρ = √(jωρ_0 / η)$",
                13,
                th.fg,
                False,
            ),
            (
                "$κ_s = κ_0 / [1 + (γ − 1) tanh(h G_κ/2) / (h G_κ/2)]$,   "
                "$G_κ = √(jω Pr ρ_0 / η)$",
                13,
                th.fg,
                False,
            ),
            (
                "at 300 Hz $ρ_s = 1.355 − 0.203j$ kg/m³, "
                "against 1.205 kg/m³ in free air",
                12,
                th.muted,
                False,
            ),
        ],
    )
    matrix(
        "$M_s$ =",
        [
            ("$cos(k_s a/2)$", "$j Z_s sin(k_s a/2)$"),
            ("$j sin(k_s a/2) / Z_s$", "$cos(k_s a/2)$"),
        ],
        th.primary,
        top + 37,
    )

    # The resonator as a shunt (Eq. (3), Eqs. (A23) to (A26)). Below its own
    # resonance it lowers the effective bulk modulus of the slit and leaves
    # the effective density alone (Appl. Phys. Lett. Eqs. (2) and (3)).
    top = 542.0
    row(
        top,
        120,
        th.accent,
        [
            (
                "The resonator in the middle of its step, as a shunt",
                14,
                th.accent,
                True,
            ),
            (
                "$Z_{HR}$ of a neck and a cavity, both square visco-thermal ducts, "
                "Eq. (A23)",
                13,
                th.fg,
                False,
            ),
            (
                "the 1 mm neck carries $Δl = Δl_1 + Δl_2$ = 2.08 mm of end correction:",
                13,
                th.fg,
                False,
            ),
            (
                "$Δl_1$ = 1.18 mm into the cavity (A24), "
                "$Δl_2$ = 0.90 mm into the slit (A25, A26)",
                13,
                th.fg,
                False,
            ),
            (
                "below its own resonance $Z_{HR}$ is a compliance: it softens the slit, "
                "adding no mass",
                12,
                th.muted,
                False,
            ),
        ],
    )
    matrix("$M_{HR}$ =", [("1", "0"), ("$1/Z_{HR}$", "1")], th.accent, top + 34)

    # The product, the backing and the reflection (Eq. (1), Eq. (4)).
    top = 676.0
    s.rect(36, top, 828, 88, "none", th.fg, rx=6, sw=1.8)
    s.text(
        450,
        top + 28,
        "$T = M_{Δl} · ∏ (M_s · M_{HR} · M_s)$ over the $N$ resonators",
        16,
        th.fg,
        bold=True,
    )
    s.text(
        450,
        top + 54,
        "$R(θ) = (T_{11} cos θ − Z_0 T_{21}) / (T_{11} cos θ + Z_0 T_{21})$,   "
        "$α = 1 − |R|^2$",
        15,
        th.fg,
    )
    s.text(
        450,
        top + 76,
        "the rigid backing holds $v = 0$ at $x_1 = L$, so the face sees "
        "$Z = T_{11} / T_{21}$",
        12,
        th.muted,
    )

    # Critical coupling (Eq. (9)) and the design that meets it. Eq. (9) is
    # written for any angle; the design is solved at normal incidence, where
    # the matched value is 1 + 0j, so the right-hand box says so.
    top = 778.0
    for x0, colour, lines in (
        (
            36.0,
            th.primary,
            (
                ("Critical coupling: loss equals leakage", 14, th.primary, True),
                ("$Re(Z) cos θ = Z_0$  and  $Im(Z) = 0$", 14, th.fg, False),
                ("the zero of $R$ lands on the real-frequency axis,", 12, th.fg, False),
                ("so $R = 0$ and $α = 1$ at that frequency", 12, th.fg, False),
            ),
        ),
        (
            460.0,
            th.fg,
            (
                ("The 300 Hz design at normal incidence", 14, th.fg, True),
                ("slit height $h$ = 0.978 mm sets the loss", 13, th.fg, False),
                ("cavity length 44.7 mm sets the resonance", 13, th.fg, False),
                (
                    "$Z/Z_0 = 1 + 0j$ and $α = 1$, in a panel $λ/38$ deep",
                    12,
                    th.fg,
                    False,
                ),
            ),
        ),
    ):
        s.rect(x0, top, 404, 104, th.panel, colour, rx=6, sw=1.8)
        for k, (txt, size, fill, bold) in enumerate(lines):
            fitted = s.fit_size([txt], (size, size - 1), 380, bold=bold)
            s.text(x0 + 202, top + 25 + 22 * k, txt, fitted, fill, bold=bold)
