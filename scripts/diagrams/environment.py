#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Diagrams of the environment guides: sources, propagation and assessment.

One subject: outdoor sound, from what emits it to what the law makes of it at
the receiver. The propagation diagrams draw the geometry the models work in
(barrier and ground, image source, refracted rays), the source diagram draws
a measurement geometry fixed by its own standard, and the assessment diagrams
draw what happens to the level once it has arrived.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .canvas import SVG, Theme

# ---------------------------------------------------------------------------
# d2 - Environmental noise microphone positions (ISO 1996-2)
# ---------------------------------------------------------------------------


def _d_env_positions(s: SVG, th: Theme) -> None:
    gy = 470.0
    s.ground(gy, 40, 860)

    # Building facade (right)
    fx = 700.0
    s.rect(fx, 120, 160, gy - 120, th.panel, th.fg, sw=2)
    for wy in range(158, int(gy) - 50, 78):
        s.rect(fx + 24, wy, 38, 46, th.bg, th.muted, rx=3, sw=1.2)
        s.rect(fx + 96, wy, 38, 46, th.bg, th.muted, rx=3, sw=1.2)
    s.text(fx + 80, 104, "Building façade", 19, th.fg, bold=True)

    # Source (left): car on a road
    s.rect(60, gy - 9, 140, 9, th.muted)
    s.path(
        f"M 88 {gy - 30} L 106 {gy - 48} L 146 {gy - 48} L 164 {gy - 30} Z",
        fill=th.secondary,
    )
    s.rect(80, gy - 32, 96, 14, th.secondary, rx=5)
    s.circle(102, gy - 13, 9, th.fg)
    s.circle(156, gy - 13, 9, th.fg)
    for r in (44, 76, 108):
        s.path(
            f"M {168 + r * 0.5} {gy - 34 - r * 0.55} "
            f"A {r} {r} 0 0 1 {168 + r * 0.87} {gy - 34 + r * 0.1}",
            stroke=th.accent,
            sw=1.6,
        )

    # Position A: free field, capsule 4 m above ground
    ax = 330.0
    a_cap = gy - 230.0
    s.mic(ax, a_cap, gy, 1.15)
    s.dim(ax, gy, ax, a_cap, "4.0 ± 0.2 m", offset=-60, size=17)
    s.text(ax - 20, a_cap - 58, "A: free field", 19, th.fg, bold=True)
    s.text(ax - 20, a_cap - 30, "0 dB", 19, th.accent, bold=True, mono=True)

    # Position B: 2 m in front of the facade, dimension at capsule height
    bx = fx - 108.0
    b_cap = gy - 230.0
    s.mic(bx, b_cap, gy, 1.15)
    s.dim(bx, b_cap + 6, fx, b_cap + 6, "2 m", offset=-14, size=17)
    s.text(bx - 30, b_cap - 58, "B: 2 m from façade", 19, th.fg, bold=True)
    s.text(bx - 30, b_cap - 30, "−3 dB", 19, th.secondary, bold=True, mono=True)

    # Position C: flush-mounted on the facade, below B's dimension zone
    cy = gy - 120.0
    s.circle(fx + 3, cy, 7, th.fg)
    # The leader crosses mic B's mast (plain line crossing, standard
    # drafting); the label itself sits in the clear zone between masts.
    s.line(fx - 2, cy + 5, 470, cy + 60, th.muted, 1.4)
    s.text(462, cy + 84, "C: flush-mounted", 19, th.fg, bold=True)
    s.text(462, cy + 110, "−6 dB", 19, th.secondary, bold=True, mono=True)


def _d_outdoor(s: SVG, th: Theme) -> None:
    c_diff = th.accent  # diffracted (over-the-top) ray
    c_direct = th.muted  # blocked direct ray
    gy = 430.0  # ground line
    s.ground(gy, 60.0, 840.0)
    # ISO 9613-2 names the source, middle and receiver regions by s, m and r,
    # and the receiver height h_r, all upright on the guide.
    s.text(
        66.0,
        gy + 26.0,
        "Ground ($G_s$, $G_m$, $G_r$)",
        15,
        th.muted,
        anchor="start",
        upright=("G_r",),
    )

    # --- source (loudspeaker) on the left, acoustic centre at (sx, sy) -------
    sx, sy = 150.0, 300.0
    for r in (26, 44, 62):
        s.path(
            f"M {sx + r * 0.22:.1f} {sy - r:.1f} "
            f"A {r} {r} 0 0 1 {sx + r:.1f} {sy - r * 0.22:.1f}",
            stroke=th.muted,
            sw=1.3,
        )
    s.rect(sx - 20, sy - 24, 40, 48, th.panel, th.fg, rx=5, sw=2)
    s.circle(sx, sy - 6, 9, th.fg)
    s.circle(sx, sy - 6, 3.5, th.bg)
    s.circle(sx, sy + 14, 6, th.fg)
    s.line(sx, sy + 24, sx, gy, th.fg, 2.0)  # mast to the ground
    s.text(sx, sy - 74, "Source", 17, th.fg, bold=True)

    # --- barrier in the middle, top edge at (ex, ey) -------------------------
    ex, ey = 450.0, 150.0
    bw = 16.0
    s.rect(ex - bw / 2, ey, bw, gy - ey, th.secondary, th.fg, sw=2)
    # Below the blocked direct path, which ran through the word at mid-height.
    s.text(
        ex + 16.0,
        (ey + gy) / 2 + 30.0,
        "Barrier",
        17,
        th.secondary,
        bold=True,
        anchor="start",
    )
    s.circle(ex, ey, 5.5, th.bg, th.fg, 2.0)  # diffraction edge node

    # --- receiver (microphone) on the right, capsule at (rx, ry) -------------
    rx, ry = 770.0, 288.0
    s.mic(rx, ry, gy, 1.0)
    s.text(rx, ry - 18.0, "Receiver", 17, th.fg, bold=True)

    # --- rays ---------------------------------------------------------------
    # Direct (blocked) ray straight through the barrier.
    s.line(sx + 14, sy - 6, rx, ry + 6, c_direct, 1.8, dash="7,6")
    s.text(
        285.0,
        sy + 40.0,
        "direct path (blocked)",
        14,
        c_direct,
        anchor="middle",
        italic=True,
    )
    # Diffracted ray up to the top edge, then down to the receiver. The
    # ss and sr of the two path lengths print upright in ISO 9613-2:1996,
    # Equation (16), p. 9.
    s.line(sx + 12, sy - 12, ex, ey, c_diff, 3.0)
    s.arrow(ex, ey, rx, ry + 2, c_diff, 3.0)
    s.text(300.0, 208.0, "$d_{ss}$", 15, c_diff, anchor="middle")
    s.text(610.0, 200.0, "$d_{sr}$", 15, c_diff, anchor="middle")
    s.text(ex, ey - 22.0, "diffracted path", 15, c_diff, bold=True)

    # --- heights (witness dimensions) ---------------------------------------
    s.dim(sx - 44, gy, sx - 44, sy - 6, "$h_s$", offset=0, label_side="left")
    s.line(sx - 44, gy, sx, gy, th.muted, 0.9, dash="3,3")
    s.line(sx - 44, sy - 6, sx, sy - 6, th.muted, 0.9, dash="3,3")
    s.dim(
        rx + 40,
        gy,
        rx + 40,
        ry + 6,
        "$h_r$",
        offset=0,
        label_side="right",
        upright=("h_r",),
    )
    s.line(rx, gy, rx + 40, gy, th.muted, 0.9, dash="3,3")
    s.line(rx, ry + 6, rx + 40, ry + 6, th.muted, 0.9, dash="3,3")

    # --- master relations ---------------------------------------------------
    # Equation (14) of ISO 9613-2:1996, p. 9, prints the met of K_met upright
    # and the z of D_z italic: z is the path difference the line above it
    # defines, not a word.
    s.text(
        450.0,
        gy + 58.0,
        "$z = d_{ss} + d_{sr} − d$   (path difference)",
        16,
        th.fg,
        bold=True,
    )
    s.text(
        450.0,
        gy + 84.0,
        "$D_z = 10 log10[ 3 + (C_2/λ) C_3 z K_{met} ]$   (Eq. 14)",
        15,
        th.muted,
    )


def _d_impulse_prominence(s: SVG, th: Theme) -> None:
    """Impulsive-sound prominence and the LAeq adjustment (NT ACOU 112:2002)."""
    cx = 450.0
    bw, bh = 640.0, 60.0
    x0 = cx - bw / 2

    # --- Input --------------------------------------------------------------
    s.rect(x0, 56, bw, bh, th.panel, th.fg, rx=10, sw=2)
    s.text(
        cx,
        82,
        "A-weighted level history  $L_{pAF}$  (time weighting F)",
        16,
        th.fg,
        "middle",
        bold=True,
    )
    s.text(
        cx,
        103,
        "an onset = a stretch where the gradient exceeds 10 dB/s (clauses 4.5-4.7)",
        11,
        th.muted,
        "middle",
    )
    s.arrow(cx, 116, cx, 150, th.fg, 1.8)

    def _step(y: float, l1: str, l2: str, color: str) -> None:
        s.rect(x0, y, bw, bh, th.panel, color, rx=10, sw=2)
        # The I of the impulse adjustment is upright on the guide.
        s.text(cx, y + 26, l1, 15, th.fg, "middle", bold=True, upright=("K_I",))
        s.text(cx, y + 47, l2, 11, th.muted, "middle", upright=("K_I",))

    _step(
        150,
        "Per impulse: onset rate OR and level difference LD",
        "OR = onset slope [dB/s],   $LD = L_e − L_s$ [dB]",
        th.primary,
    )
    _step(
        242,
        "Predicted prominence  $P$   (clause 7, Formula 1)",
        "$P = 3·log_{10}(OR) + 2·log_{10}(LD)$;   highest $P$ over 30 min governs",
        th.fg,
    )
    _step(
        334,
        "Adjustment  $K_I$   (clause 8, Formula 2)",
        "$K_I = 1.8·(P − 5)$ dB for $P > 5$, else 0",
        th.secondary,
    )
    s.arrow(cx, 210, cx, 242, th.fg, 1.8)
    s.arrow(cx, 302, cx, 334, th.fg, 1.8)
    s.arrow(cx, 394, cx, 426, th.fg, 1.8)

    # --- Output -------------------------------------------------------------
    # Note 1 to clause 8, as the guide writes it: the A-weighting, the rating
    # and the adjustment upright, the reference time T and the interval
    # index N italic.
    s.rect(x0, 426, bw, 60, "none", th.primary, rx=10, sw=2.4)
    s.text(
        cx,
        452,
        "Rating level  $L_{Ar,T} = 10 log_{10}((1/T) Σ_N Δt_N·"
        "10^{(L_{Aeq,N} + K_{I,N})/10})$",
        15,
        th.fg,
        "middle",
        bold=True,
        upright=("K_I",),
        sloped=("L_T",),
    )
    s.text(
        cx,
        473,
        "impulse-adjusted level over the reference time  (Note 1)",
        11,
        th.muted,
        "middle",
    )


# ---------------------------------------------------------------------------
# Wind-turbine noise measurement geometry (IEC 61400-11)
# ---------------------------------------------------------------------------


def _d_wind_turbine(s: SVG, th: Theme) -> None:
    """IEC 61400-11 apparent-sound-power geometry: downwind ground-board
    microphone at R0 = H + D/2, slant distance R1 to the rotor centre and
    the Figure 3 plan-view position pattern.
    """
    import math

    gy = 470.0
    s.ground(gy, 40.0, 668.0)

    # Wind arrow on the upwind side.
    s.arrow(52.0, 108.0, 148.0, 108.0, th.accent, 2.6)
    s.text(100.0, 88.0, "Wind", 15, th.accent, bold=True)

    # --- met mast: anemometer cups + wind vane -----------------------------
    mmx = 108.0
    s.line(mmx, gy, mmx, gy - 96.0, th.fg, 2.2)
    s.line(mmx - 12, gy - 96.0, mmx + 12, gy - 96.0, th.fg, 1.8)
    s.circle(mmx - 12, gy - 102.0, 4.5, th.panel, th.fg, 1.4)  # cup
    s.circle(mmx + 12, gy - 102.0, 4.5, th.panel, th.fg, 1.4)  # cup
    s.line(mmx, gy - 82.0, mmx + 20, gy - 82.0, th.fg, 1.6)  # vane arm
    s.path(
        f"M {mmx + 20:.0f} {gy - 87:.0f} L {mmx + 34:.0f} {gy - 82:.0f} "
        f"L {mmx + 20:.0f} {gy - 77:.0f} Z",
        fill=th.secondary,
    )
    s.text(mmx, gy - 118.0, "Met mast", 14, th.fg, bold=True)
    s.text(mmx, gy + 30.0, "wind speed + direction", 12, th.muted)

    # --- turbine: tower, nacelle and the rotor edge-on ----------------------
    tx = 262.0  # tower vertical centreline
    hub_y = 168.0  # rotor centre => H = 302 px
    rr = 104.0  # rotor radius (D = 208 px)
    s.path(
        f"M {tx - 10:.0f} {gy:.0f} L {tx - 5:.0f} {hub_y + 12:.0f} "
        f"L {tx + 5:.0f} {hub_y + 12:.0f} L {tx + 10:.0f} {gy:.0f} Z",
        fill=th.panel,
        stroke=th.fg,
        sw=1.8,
    )
    s.rect(tx - 28, hub_y - 12, 56, 24, th.panel, th.fg, rx=6, sw=1.8)
    rx_ = tx - 34.0  # rotor plane (upwind of the tower)
    s.ellipse(rx_, hub_y, 9.0, rr, stroke=th.muted, sw=1.3, dash="6,5")
    s.line(rx_, hub_y - 8, rx_ - 4, hub_y - rr + 4, th.fg, 3.2)  # blade up
    s.line(rx_, hub_y + 8, rx_ + 3, hub_y + rr - 4, th.fg, 3.2)  # blade down
    s.circle(rx_, hub_y, 6.5, th.fg)
    s.text(tx + 36, hub_y - 26, "rotor centre", 13, th.fg, anchor="start")
    s.line(rx_ + 8, hub_y - 6, tx + 33, hub_y - 21, th.muted, 0.9)

    # Rotor diameter D across the swept ellipse.
    dx_ = rx_ - 58.0
    s.dim(dx_, hub_y - rr, dx_, hub_y + rr, "$D$", offset=0, label_side="left")
    s.line(rx_ - 8, hub_y - rr, dx_, hub_y - rr, th.muted, 0.9, dash="3,3")
    s.line(rx_ - 8, hub_y + rr, dx_, hub_y + rr, th.muted, 0.9, dash="3,3")

    # Hub height H, downwind of the tower.
    hx_ = tx + 56.0
    s.dim(hx_, gy, hx_, hub_y, "$H$", offset=0, label_side="right")
    s.line(tx + 10, gy, hx_, gy, th.muted, 0.9, dash="3,3")
    s.line(tx + 28, hub_y, hx_, hub_y, th.muted, 0.9, dash="3,3")

    # --- downwind microphone on a ground board ------------------------------
    mx = 640.0
    s.ellipse(mx, gy - 3.0, 36.0, 7.0, fill=th.panel, stroke=th.fg, sw=1.6)
    s.rect(mx - 16, gy - 10.0, 20, 6, th.fg, rx=2.5)  # capsule flat
    s.rect(mx + 4, gy - 11.0, 10, 8, th.primary, rx=2)  # body
    # Under the ground line and to the right of the R0 dimension: set above
    # the board, the label runs back across the hub-height dimension and
    # into the tower itself, and it is the longer of the two languages that
    # gets there first.
    s.text(740.0, gy + 62.0, "Microphone on a ground board", 14, th.fg, bold=True)

    # Slant distance R1 from the rotor centre to the microphone.
    s.line(rx_, hub_y, mx - 12, gy - 8.0, th.primary, 2.2, dash="9,6")
    s.text(430.0, 296.0, "$R_1$", 16, th.primary, bold=True)
    # Board-to-R1 inclination angle (25°..40°).
    ang = math.atan2(gy - 8.0 - hub_y, mx - 12 - rx_)  # slope of R1
    r_arc = 52.0
    axp = mx - 12 - r_arc * math.cos(ang)
    ayp = gy - 8.0 - r_arc * math.sin(ang)
    s.path(
        f"M {mx - 12 - r_arc:.1f} {gy - 8:.1f} "
        f"A {r_arc:.0f} {r_arc:.0f} 0 0 1 {axp:.1f} {ayp:.1f}",
        stroke=th.muted,
        sw=1.3,
    )
    s.text(mx - 74, gy - 22.0, "$φ$", 15, th.muted)

    # Horizontal reference distance R0.
    s.dim(tx, gy, mx, gy, "$R_0 = H + D/2$", offset=40)

    # --- plan-view inset: the Figure 3 position pattern ---------------------
    pcx, pcy, pr = 794.0, 218.0, 76.0
    s.text(pcx, 104.0, "Plan view (Figure 3)", 15, th.fg, bold=True)
    s.arrow(pcx - 60.0, 118.0, pcx - 60.0, 150.0, th.accent, 2.2)  # wind, from top
    s.circle(pcx, pcy, pr, "none", th.muted, 1.2)
    s.line(pcx - pr - 8, pcy, pcx + pr + 8, pcy, th.muted, 1.0, dash="4,4")
    s.line(pcx, pcy - pr - 8, pcx, pcy + pr + 8, th.muted, 1.0, dash="4,4")
    s.line(pcx - 16, pcy, pcx + 16, pcy, th.fg, 3.0)  # rotor, plan
    s.circle(pcx, pcy, 4.0, th.fg)
    # Reference position 1, downwind (diamond).
    p1x, p1y = pcx, pcy + pr
    s.path(
        f"M {p1x:.0f} {p1y - 7:.0f} L {p1x + 7:.0f} {p1y:.0f} "
        f"L {p1x:.0f} {p1y + 7:.0f} L {p1x - 7:.0f} {p1y:.0f} Z",
        fill=th.secondary,
    )
    # Positions 1 and 3 sit where the circle runs level, so their numbers go
    # just outside it: beside them, the circle ran through the digit.
    s.text(p1x + 12, p1y + 16, "1", 13, th.secondary, anchor="start", bold=True)
    # Optional positions 2 and 4 at ±60° from downwind, 3 upwind.
    for lbl, adeg, lx, ly, anch in (
        ("2", 150.0, -12.0, 4.0, "end"),
        ("3", 270.0, 12.0, -6.0, "start"),
        ("4", 30.0, 12.0, 4.0, "start"),
    ):
        pxx = pcx + pr * math.cos(math.radians(adeg))
        pyy = pcy + pr * math.sin(math.radians(adeg))
        s.circle(pxx, pyy, 5.5, th.bg, th.fg, 1.6)
        s.text(pxx + lx, pyy + ly, lbl, 13, th.muted, anchor=anch)
        s.line(pcx, pcy, pxx, pyy, th.muted, 0.9, dash="3,4")
    s.line(pcx, pcy, p1x, p1y, th.muted, 0.9, dash="3,4")
    s.text(pcx - 34, pcy + 52.0, "60°", 11, th.muted)
    s.text(pcx + 34, pcy + 52.0, "60°", 11, th.muted)
    s.text(pcx, pcy + pr + 30.0, "reference 1 (downwind)", 12, th.secondary)
    s.text(pcx, pcy + pr + 50.0, "optional positions 2–4", 12, th.muted)

    # --- governing relations -------------------------------------------------
    s.text(
        450.0,
        560.0,
        "$R_1 = √(H^2 + R_0^2)$   slant distance, rotor centre → microphone",
        16,
        th.fg,
        bold=True,
    )
    s.text(
        450.0,
        588.0,
        "$L_{WA,i} = L_{p,i} − 6 + 10 log_{10}(4π R_1^2 / S_0)$   (Formula 26, $S_0$ = 1 m²)",
        16,
        th.primary,
        bold=True,
    )
    s.text(
        450.0,
        614.0,
        "the −6 dB removes the board's pressure doubling; board-to-$R_1$ angle $φ$ = 25°–40°",
        14,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Ground reflection: direct ray, image source, path difference
# ---------------------------------------------------------------------------


def _d_ground_reflection(s: SVG, th: Theme) -> None:
    """Two-path ground interference: source, receiver, direct ray, the
    specular reflection unfolded through the image source, and the path
    difference that sets the interference phase (ISO 9613-2 ground effect,
    Chien-Soroka geometry).
    """
    gy = 372.0
    sx, sy = 170.0, 232.0  # source (hs = 140 px)
    rx, ry = 700.0, 282.0  # receiver capsule tip (hr = 90 px)
    ix, iy = sx, gy + (gy - sy)  # image source, mirrored below the ground
    # Specular point: equal angles, found by unfolding through the image.
    bx = sx + (rx - sx) * (gy - sy) / ((gy - sy) + (gy - ry))

    s.ground(gy, 60.0, 840.0)

    # Source: point with radiating arcs.
    for r in (22, 38, 54):
        s.path(
            f"M {sx + r * 0.30:.1f} {sy - r * 0.95:.1f} "
            f"A {r} {r} 0 0 1 {sx + r * 0.95:.1f} {sy - r * 0.30:.1f}",
            stroke=th.muted,
            sw=1.3,
        )
    s.circle(sx, sy, 8.0, th.fg)
    s.text(sx, sy - 66.0, "Source", 17, th.fg, bold=True)
    s.text(sx - 14, sy + 24, "$S$", 13, th.fg, anchor="end")
    s.line(sx, sy + 8, sx, gy, th.fg, 2.0)

    # Receiver: measurement microphone.
    s.mic(rx, ry, gy, 1.0)
    s.text(rx, ry - 18.0, "Receiver", 17, th.fg, bold=True)
    # Under the rays that arrive at the capsule, which ran through it level
    # with the tip.
    s.text(rx - 16, ry + 32.0, "$R$", 13, th.fg, anchor="end")

    # Direct ray r1.
    s.arrow(sx + 10, sy, rx - 8, ry - 2, th.primary, 2.6)
    s.text(430.0, 236.0, "direct ray  $r_1$", 15, th.primary, bold=True)

    # Reflected ray via the specular point (equal angles).
    s.line(sx + 6, sy + 7, bx, gy, th.accent, 2.6)
    s.arrow(bx, gy, rx - 6, ry + 4, th.accent, 2.6)
    s.text(330.0, gy - 34.0, "reflected ray", 15, th.accent, bold=True)
    # Equal grazing angles at the bounce.
    s.path(
        f"M {bx - 34:.1f} {gy:.1f} A 34 34 0 0 1 {bx - 26:.1f} {gy - 21:.1f}",
        stroke=th.muted,
        sw=1.2,
    )
    s.path(
        f"M {bx + 34:.1f} {gy:.1f} A 34 34 0 0 0 {bx + 26:.1f} {gy - 21:.1f}",
        stroke=th.muted,
        sw=1.2,
    )
    s.text(bx, gy - 40.0, "equal angles", 12, th.muted)

    # Image source: ghosted mirror of the source below the ground.
    s.circle(ix, iy, 8.0, "none", th.secondary, 1.8)
    s.line(sx, gy, ix, iy - 8, th.secondary, 1.2, dash="4,4")
    s.text(ix + 18, iy + 5, "image source", 14, th.secondary, anchor="start")
    s.text(ix - 16, iy + 5, "$S′$", 13, th.secondary, anchor="end")
    # The unfolded path S' -> R is straight through the bounce point: r2.
    s.line(ix, iy - 6, bx, gy, th.secondary, 1.6, dash="7,5")
    s.line(bx, gy, rx - 6, ry + 4, th.secondary, 1.2, dash="2,6")
    s.text(380.0, iy - 62.0, "$r_2 = |S′R|$", 14, th.secondary)

    # Heights.
    s.dim(sx - 46, gy, sx - 46, sy, "$h_s$", offset=0, label_side="left")
    s.line(sx - 46, gy, sx - 8, gy, th.muted, 0.9, dash="3,3")
    s.line(sx - 46, sy, sx - 8, sy, th.muted, 0.9, dash="3,3")
    s.dim(
        rx + 42,
        gy,
        rx + 42,
        ry,
        "$h_r$",
        offset=0,
        label_side="right",
        upright=("h_r",),
    )
    s.line(rx + 8, gy, rx + 42, gy, th.muted, 0.9, dash="3,3")
    s.line(rx + 8, ry, rx + 42, ry, th.muted, 0.9, dash="3,3")

    # Governing relations (top block, clear of the geometry).
    s.text(560.0, 88.0, "path difference  $δ = r_2 − r_1$", 17, th.fg, bold=True)
    s.text(560.0, 114.0, "phase difference  $Δφ = 2π δ / λ$  (+ $arg Q$)", 15, th.fg)
    # The two-ray sum of Salomons (2001), Equation (3.2), written as he
    # prints it, with exp() for the exponential and the italic i of the
    # imaginary unit, over the path lengths this plate labels r_1 and r_2.
    s.text(
        560.0,
        142.0,
        "$p ∝ exp(i\u2009k\u2009r_1)/r_1 + Q·exp(i\u2009k\u2009r_2)/r_2$   "
        "($Q$ = ground reflection coefficient)",
        14,
        th.muted,
    )
    s.text(
        560.0,
        168.0,
        "in phase ($δ ≈ nλ$): up to +6 dB    ·    out of phase ($δ ≈ λ/2$ on hard ground): a deep dip",
        13,
        th.muted,
    )


# Atmospheric refraction: downwind multipath and the upwind shadow zone
# ---------------------------------------------------------------------------


def _d_atmospheric_refraction(s: SVG, th: Theme) -> None:
    """Refracting surface layer (Salomons 2001; Attenborough & Van
    Renterghem 2021, Ch. 11): wind profile arrows, an effective-sound-speed
    inset, downward-curved rays with a ground bounce on the downwind side
    and upward-curved rays opening an acoustic shadow on the upwind side.
    Horizontal scale about 1 px per metre; heights exaggerated.
    """
    gy = 452.0
    sx, sy = 450.0, gy - 56.0  # source, hs = 2 m (schematic)
    mlx, mrx = 90.0, 795.0  # receivers, 350 m to each side

    # --- upwind side (left): rays curve upward -----------------------------
    # Limiting ray: grazes the ground at ~220 m upwind, then climbs; the
    # region under it is the acoustic shadow.
    s.path(
        f"M {sx:.0f} {sy:.0f} C 380 430 300 452 232 452", stroke=th.secondary, sw=1.8
    )
    shadow = "M 232 452 C 150 452 90 420 60 340 L 60 452 Z"
    s.path(shadow, fill=th.panel)
    s.path("M 232 452 C 150 452 90 420 60 340", stroke=th.secondary, sw=1.4, dash="6,5")
    # Fan of upwind rays, all refracted upward.
    s.path(
        f"M {sx:.0f} {sy:.0f} C 380 390 310 372 250 340", stroke=th.secondary, sw=1.8
    )
    s.arrow(250.0, 340.0, 214.0, 316.0, th.secondary, 1.8)
    s.path(
        f"M {sx:.0f} {sy:.0f} C 400 375 340 330 290 270", stroke=th.secondary, sw=1.8
    )
    s.arrow(290.0, 270.0, 264.0, 234.0, th.secondary, 1.8)
    s.path(
        f"M {sx:.0f} {sy:.0f} C 415 345 385 270 355 195", stroke=th.secondary, sw=1.8
    )
    s.arrow(355.0, 195.0, 340.0, 156.0, th.secondary, 1.8)
    s.text(
        188.0, 414.0, "acoustic shadow", 13, th.secondary, italic=True, anchor="start"
    )
    s.line(184.0, 410.0, 105.0, 395.0, th.muted, 1.0)
    # Shadow-boundary marker at the grazing point, broken around the label
    # it ran through.
    s.line(232.0, 452.0, 232.0, 422.0, th.muted, 1.1, dash="4,4")
    s.line(232.0, 400.0, 232.0, 386.0, th.muted, 1.1, dash="4,4")
    s.text(232.0, 370.0, "≈ 220 m", 12, th.muted)

    # --- downwind side (right): rays curve down, ground bounce -------------
    s.path(f"M {sx:.0f} {sy:.0f} Q 620 366 786 402", stroke=th.primary, sw=2.0)
    s.arrow(770.0, 399.0, 788.0, 403.0, th.primary, 2.0)
    s.path(f"M {sx:.0f} {sy:.0f} Q 590 300 726 452", stroke=th.accent, sw=2.0)
    s.path("M 726 452 Q 758 420 782 408", stroke=th.accent, sw=2.0)
    s.arrow(766.0, 415.0, 784.0, 407.0, th.accent, 2.0)

    # --- scene: ground, source, receivers ----------------------------------
    s.ground(gy, 40.0, 860.0)
    for r in (18, 30, 42):
        s.path(
            f"M {sx - r:.0f} {sy:.0f} A {r} {r} 0 0 1 {sx + r:.0f} {sy:.0f}",
            stroke=th.muted,
            sw=1.2,
        )
    s.circle(sx, sy, 7.0, th.fg)
    s.line(sx, sy + 7, sx, gy, th.fg, 2.0)
    s.text(sx, sy - 54.0, "Source", 15, th.fg, bold=True)
    s.dim(sx + 34, gy, sx + 34, sy, "2 m", offset=0, size=13, label_side="right")
    s.line(sx + 7, sy, sx + 34, sy, th.muted, 0.9, dash="3,3")
    s.mic(mlx, gy - 42.0, gy, 0.85)
    s.mic(mrx, gy - 46.0, gy, 1.0)
    s.text(mrx, gy - 66.0, "Receiver", 15, th.fg, bold=True)
    s.dim(
        mrx + 38,
        gy,
        mrx + 38,
        gy - 46.0,
        "1.5 m",
        offset=0,
        size=12,
        label_side="right",
    )
    s.line(mrx + 8, gy - 46.0, mrx + 38, gy - 46.0, th.muted, 0.9, dash="3,3")
    s.dim(mlx, gy, sx, gy, "350 m", offset=36, size=14)
    s.dim(sx, gy, mrx, gy, "350 m", offset=36, size=14)

    # --- wind profile arrows (blowing left to right) -----------------------
    for wy, wl in ((84.0, 116.0), (114.0, 82.0), (144.0, 52.0)):
        s.arrow(500.0, wy, 500.0 + wl, wy, th.accent, 2.2)
    s.text(548.0, 66.0, "wind $u(z)$", 14, th.accent, bold=True)

    # --- inset: effective-sound-speed profiles -----------------------------
    s.text(143.0, 52.0, "$c_{eff}(z) = c(z) + u(z)$", 13, th.fg, bold=True)
    s.rect(58, 64, 170, 170, th.panel, th.fg, rx=8, sw=1.5)
    s.arrow(76.0, 214.0, 76.0, 88.0, th.muted, 1.3)
    s.text(76.0, 80.0, "$z$", 11, th.muted)
    s.line(76.0, 214.0, 214.0, 214.0, th.muted, 1.3)
    s.path("M 143 214 Q 146 150 192 96", stroke=th.primary, sw=2.2)
    s.path("M 143 214 Q 140 150 100 96", stroke=th.secondary, sw=2.2)
    s.text(197.0, 92.0, "$+u$", 11, th.primary, anchor="start")
    s.text(96.0, 92.0, "$−u$", 11, th.secondary, anchor="end")
    s.text(143.0, 229.0, "340 m/s", 10, th.muted, mono=True)

    # --- physics captions --------------------------------------------------
    s.text(
        80.0,
        540.0,
        "Upwind: rays bend up; beyond ≈ 220 m a ground shadow opens and "
        "the level collapses over 20 dB",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        80.0,
        566.0,
        "Downwind: rays bend down; the receiver hears the direct and the ground-bounced arrival (multipath)",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        80.0,
        592.0,
        "a ±0.1 (m/s)/m gradient curves rays with $R_c = c_0/|g|$ ≈ "
        "3.4 km; source $h_s$ = 2 m, receiver $h_r$ = 1.5 m",
        14,
        th.muted,
        anchor="start",
        upright=("h_r",),
    )


# ---------------------------------------------------------------------------
# Barrier diffraction over ground (Fresnel number, Kurze-Anderson)
# ---------------------------------------------------------------------------


def _d_ground_barrier(s: SVG, th: Theme) -> None:
    """The guide's barrier geometry: a 1 m source, a 4 m thin screen at
    50 m and a 1.5 m receiver at 100 m. The diffracted segments A and B,
    the blocked direct path d and the barrier_insertion_loss values
    (N = 0.44 and 10.0 dB at 500 Hz, 15.5 dB at 2 kHz).
    """
    gy = 340.0  # ground; 7 px/m horizontal, 60 px/m vertical
    sx, sy = 110.0, gy - 60.0  # source, hs = 1 m
    ex, ey = 460.0, gy - 240.0  # barrier top edge, 4 m
    rx, ry = 810.0, gy - 90.0  # receiver, hr = 1.5 m

    s.ground(gy, 40.0, 860.0)

    # Source loudspeaker on its mast.
    for r in (22, 38, 54):
        s.path(
            f"M {sx + r * 0.22:.1f} {sy - r:.1f} "
            f"A {r} {r} 0 0 1 {sx + r:.1f} {sy - r * 0.22:.1f}",
            stroke=th.muted,
            sw=1.2,
        )
    s.rect(sx - 17, sy - 20, 34, 40, th.panel, th.fg, rx=5, sw=2)
    s.circle(sx, sy - 5, 8, th.fg)
    s.circle(sx, sy - 5, 3, th.bg)
    s.circle(sx, sy + 12, 5, th.fg)
    s.line(sx, sy + 20, sx, gy, th.fg, 2.0)
    s.text(sx, sy - 66, "Source", 16, th.fg, bold=True)

    # Thin screen with its diffraction edge.
    s.rect(ex - 8, ey, 16, gy - ey, th.secondary, th.fg, sw=2)
    s.text(ex + 18, ey + 74, "Barrier", 16, th.secondary, bold=True, anchor="start")

    # Receiver microphone.
    s.mic(rx, ry, gy, 1.0)
    s.text(rx, ry - 20, "Receiver", 16, th.fg, bold=True)

    # Blocked direct path and the diffracted path A + B.
    s.line(sx + 12, sy - 4, rx - 4, ry + 4, th.muted, 1.6, dash="7,6")
    s.text(268, 308, "direct $d$ = 100.00 m (blocked)", 13, th.muted)
    s.line(sx + 10, sy - 10, ex, ey, th.accent, 2.6)
    s.arrow(ex, ey, rx - 4, ry - 2, th.accent, 2.6)
    s.circle(ex, ey, 5.5, th.bg, th.fg, 2.0)
    s.text(258, 162, "$A$ = 50.09 m", 15, th.accent, bold=True)
    s.text(660, 152, "$B$ = 50.06 m", 15, th.accent, bold=True)

    # Height and distance dimensions.
    s.dim(64, gy, 64, sy - 4, "1.0 m", offset=0, size=13, label_side="left")
    s.line(64, sy - 4, sx - 17, sy - 4, th.muted, 0.9, dash="3,3")
    s.dim(430, gy, 430, ey, "4.0 m", offset=0, size=13, label_side="left")
    s.line(430, ey, ex - 8, ey, th.muted, 0.9, dash="3,3")
    s.dim(846, gy, 846, ry, "1.5 m", offset=0, size=12, label_side="right")
    s.line(rx + 6, ry, 846, ry, th.muted, 0.9, dash="3,3")
    s.dim(sx, gy, ex, gy, "50 m", offset=34, size=14)
    s.dim(ex, gy, rx, gy, "50 m", offset=34, size=14)

    # --- captions ----------------------------------------------------------
    s.text(
        80,
        420,
        "path difference $δ = A + B − d$ = 0.15 m; Fresnel number $N = 2δ/λ$ = 0.44 at 500 Hz",
        15,
        th.fg,
        anchor="start",
    )
    # The bar of the Kurze-Anderson attenuation names the barrier, as the
    # upright bar of A_bar does in ISO 9613-2:1996, Equation (12), p. 9.
    s.text(
        80,
        448,
        "Kurze–Anderson: $Δ_{bar}$ = 5 + 20 log10( √(2π$N$) / tanh √(2π$N$) ) = 10.0 dB, 500 Hz",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )
    s.text(
        80,
        476,
        "$N$ grows with frequency: the same screen gives 15.5 dB at 2 kHz (vertical scale exaggerated)",
        15,
        th.muted,
        anchor="start",
    )


# ---------------------------------------------------------------------------
# ISO 9613-2 ground regions and the ground factor G (7.3.1, Table 3 note 2)
# ---------------------------------------------------------------------------


def _d_ground_regions(s: SVG, th: Theme) -> None:
    gy = 250.0
    x0, x1 = 70.0, 830.0  # 0 m and 200 m of the path
    scale = (x1 - x0) / 200.0  # px per metre

    # The three regions, shaded along the ground.
    src_end = x0 + 45.0 * scale
    rec_start = x1 - 45.0 * scale
    band = 34.0
    s.rect(x0, gy - band, src_end - x0, band, th.panel, th.primary, sw=2.0)
    s.rect(src_end, gy - band, rec_start - src_end, band, th.panel, th.accent, sw=2.0)
    s.rect(rec_start, gy - band, x1 - rec_start, band, th.panel, th.primary, sw=2.0)

    # Mixed cover inside the middle region: 70 m grass then 40 m asphalt.
    grass_end = src_end + 70.0 * scale
    s.rect(
        grass_end, gy - band, rec_start - grass_end, band, th.muted, th.accent, sw=2.0
    )
    s.text((src_end + grass_end) / 2, gy - band - 12, "grass, $G = 1$", 15, th.fg)
    s.text((grass_end + rec_start) / 2, gy - band - 12, "asphalt, $G = 0$", 15, th.fg)

    s.ground(gy, 50.0, 850.0)

    # Source and receiver, both 1,5 m high (drawn out of scale for legibility).
    hs = 86.0
    s.circle(x0, gy - hs, 9, th.secondary)
    s.line(x0, gy - hs, x0, gy, th.fg, 2.0)
    s.text(x0 + 12, gy - hs - 40, "Source", 17, th.fg, anchor="start", bold=True)
    s.text(x0 + 12, gy - hs - 18, "$h_s$ = 1.5 m", 15, th.muted, anchor="start")
    s.mic(x1, gy - hs, gy, 1.0)
    s.text(x1 - 12, gy - hs - 40, "Receiver", 17, th.fg, anchor="end", bold=True)
    # The r of the receiver and the p of the projected distance d_p are
    # upright in ISO 9613-2 and on the guide.
    regions = ("h_r", "G_r", "d_p")
    s.text(
        x1 - 12,
        gy - hs - 18,
        "$h_r$ = 1.5 m",
        15,
        th.muted,
        anchor="end",
        upright=regions,
    )
    s.line(x0, gy - hs, x1, gy - hs, th.muted, 1.4, dash="7,5")

    # Region dimensions along the ground. The two end regions are narrower
    # than their names, which ran across the witness lines on one line, so
    # each name goes in two lines under its dimension.
    s.dim(x0, gy + 44, src_end, gy + 44, "", 0, 15)
    s.dim(src_end, gy + 80, rec_start, gy + 80, "middle region  110 m", 0, 15)
    s.dim(rec_start, gy + 44, x1, gy + 44, "", 0, 15)
    for left, right, name, extent in (
        (x0, src_end, "source region", "$30 h_s$ = 45 m"),
        (rec_start, x1, "receiver region", "$30 h_r$ = 45 m"),
    ):
        s.text((left + right) / 2, gy + 64, name, 15, th.fg)
        s.text((left + right) / 2, gy + 83, extent, 15, th.fg, upright=regions)
    for xv in (x0, src_end, rec_start, x1):
        s.line(xv, gy + 28, xv, gy + 92, th.muted, 0.9, dash="3,3")
    s.dim(x0, gy + 118, x1, gy + 118, "$d_p$ = 200 m", 0, 16, upright=regions)

    # Inset: the same path at 60 m, regions overlapping, no middle region.
    iy = gy + 190.0
    ix0, ix1 = 260.0, 640.0
    s.rect(ix0, iy - 26, ix1 - ix0, 26, th.panel, th.primary, sw=2.0)
    s.line(ix0 - 40, iy, ix1 + 40, iy, th.fg, 1.8)
    s.circle(ix0, iy - 46, 6, th.secondary)
    s.circle(ix1, iy - 46, 6, th.primary)
    s.dim(
        ix0,
        iy + 48,
        ix1,
        iy + 48,
        "$d_p$ = 60 m: the regions overlap, so there is no middle region",
        0,
        15,
        upright=regions,
    )

    # The two reading boxes, on one row under the drawing.
    by = 500.0
    s.rect(70.0, by, 380, 100, th.panel, th.muted, rx=8, sw=1.2)
    s.text(
        84.0,
        by + 28,
        "$G$ is the porous fraction of its region",
        16,
        th.fg,
        anchor="start",
        bold=True,
    )
    s.text(84.0, by + 54, "$G_s = 25/45$ = 0.56", 15, th.fg, anchor="start")
    s.text(
        84.0,
        by + 78,
        "$G_m = 70/110$ = 0.64   $G_r$ = 1.00",
        15,
        th.fg,
        anchor="start",
        upright=regions,
    )

    s.rect(470.0, by, 380, 100, th.panel, th.muted, rx=8, sw=1.2)
    s.text(
        484.0,
        by + 28,
        "$q = 1 − 30(h_s + h_r)/d_p$ = 0.55",
        16,
        th.fg,
        anchor="start",
        upright=regions,
    )
    s.text(
        484.0,
        by + 54,
        "below $30(h_s + h_r)$ = 90 m: $q = 0$, $A_m = 0$",
        15,
        th.secondary,
        anchor="start",
        upright=regions,
    )
    s.text(
        484.0,
        by + 78,
        "and ground_middle is ignored entirely",
        15,
        th.fg,
        anchor="start",
    )


# ---------------------------------------------------------------------------
# The four diffracted paths of a barrier on finite-impedance ground
# ---------------------------------------------------------------------------


def _d_barrier_in_situ(s: SVG, th: Theme) -> None:
    """The ISO 10847 measurement: the same two microphones, twice.

    A barrier cannot be wheeled away, so the two runs are two campaigns months
    apart, and the reference microphone is what makes them comparable: it
    stands above the top edge, hears the source and not the barrier, and
    whatever the source did differently on the second day it heard too. The
    direct method needs the site before the barrier was built; the indirect one
    borrows that campaign from an equivalent site and says so.
    """
    # The first title in two lines: in one, the Spanish ran on into the
    # reference microphone and its dimension.
    for row, (base, titles, built) in enumerate(
        (
            (250.0, ("Before: no barrier,", "or an equivalent site"), False),
            (500.0, ("After: the barrier as built",), True),
        )
    ):
        colour = th.secondary if row == 0 else th.primary
        for k, title in enumerate(titles):
            y = base - 150 + (k - (len(titles) - 1) / 2) * 20
            s.text(60, y, title, 15, colour, bold=True, anchor="start")
        s.ground(base, 55, 860)

        # The source region, which is a road or a yard rather than a point.
        s.rect(70, base - 52, 150, 52, th.panel, th.fg, rx=5, sw=2.0)
        s.circle(145, base - 26, 13, th.fg)
        s.circle(145, base - 26, 5, th.bg)
        s.text(145, base + 30, "the source region", 13, th.muted)

        top = base - 132.0
        if built:
            s.rect(430, top, 20, 132, th.panel, th.primary, rx=3, sw=2.6)
            s.text(440, top - 62, "the barrier", 13, th.primary, bold=True)
        else:
            s.rect(430, top, 20, 132, "none", th.muted, rx=3, sw=1.4, dash="5,4")
            s.text(440, top - 62, "where it will stand", 13, th.muted)

        # The reference microphone: 1,5 m clear of the top edge, on the plane
        # through it, so that it hears the source and not the barrier.
        s.mic(440, top - 46, top, scale=0.8)
        s.line(430, top, 450, top, th.muted, 1.2, dash="3,3")
        s.dim(470, top, 470, top - 46, "1.5 m", size=13, label_side="right")
        s.text(440, base + 30, "reference microphone", 13, th.accent)

        # The receiver, at 1,2 m or more, where somebody actually stands.
        s.mic(740, base - 86, base, scale=0.9)
        s.text(740, base + 30, "receiver position", 13, th.accent)
        s.dim(790, base, 790, base - 86, "≥ 1.2 m", size=13, label_side="right")

        s.arrow(225, base - 26, 415, top + 24, colour, 1.8)
        if built:
            s.path(
                f"M 440 {top} Q 590 {top - 34} 740 {base - 86}",
                stroke=colour,
                sw=1.8,
                dash="6,4",
            )
        else:
            s.arrow(225, base - 26, 725, base - 86, colour, 1.8)

    # The weather is part of the measurement, so it goes on the plate.
    s.rect(70, 620, 760, 92, th.panel, th.fg, rx=6, sw=1.6)
    # ISO 10847:1997, 8.2.1 (PDF page 15, folio 11), prints every subscript of
    # the insertion loss upright: IL, ref, r (receiver), A and B (after and
    # before).
    s.text(
        450,
        648,
        "$D_{IL} = (L_{ref,A} − L_{ref,B}) − (L_{r,A} − L_{r,B})$",
        18,
        th.fg,
        upright=("D_IL", "L_A", "L_B", "L_r"),
    )
    s.text(
        450,
        672,
        "the reference term normalises the source: a louder day cancels out of the answer",
        13,
        th.muted,
    )
    # 12 px where 13 would run out of the box, as the Spanish did.
    weather = (
        "both campaigns within 2 m/s on the wind component and 10 \u00b0C on the "
        "temperature, and never above 5 m/s"
    )
    s.text(450, 698, weather, s.fit_size([weather], [13, 12], 740), th.secondary)


def _d_barrier_reflection_setup(s: SVG, th: Theme) -> None:
    """The EN 1793-5 set-up: where everything stands and what is recorded.

    Three views of one rig. The side view is to scale for the 4 m device of
    5.3, so the two arrivals the window has to shut out (5.5.7) run where
    they really run: over the top edge to the top row, and off the ground to
    the bottom row. The front view is Figure 3 (b) laid on the minimum sample
    of Figure 7, with the rows told apart as 5.5.5 tells them apart. The third
    view is the free-field record of 3.16, and the list beside it names every
    record the method asks for with the clause that asks for it.

    The distances are the ones Table 1 defines (BS EN 1793-5:2016, PDF page
    15, folio 13): the 1.50 m of the loudspeaker to the reference plane and
    the 0.25 m of the plane to the grid. The Key of Figure 15 swaps their
    words (docs/ERRATA.md), so nothing here is read from it. The path lengths
    are those of Table 2 (PDF page 18) and the radius that of NOTE 1 of 5.6.1
    (PDF page 37). Table 1 prints every subscript of these lengths italic.
    """
    # --- (a) side view, 90 px to the metre --------------------------------
    scale = 90.0
    gy = 470.0
    xr = 330.0  # the reference plane
    top = gy - 4.0 * scale
    axis = gy - 2.0 * scale  # the reference height, half the device's
    xf = xr - 1.50 * scale  # the loudspeaker's front panel
    xg = xr - 0.25 * scale  # the measurement grid
    rows = [axis - 0.40 * scale, axis, axis + 0.40 * scale]

    s.text(
        40,
        72,
        "(a) Side view of a 4 m device, to scale",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )
    s.ground(gy, 40, 470)

    # The device, and the plane that touches its most protruding parts.
    s.rect(xr, top, 22, gy - top, th.panel, th.fg, sw=2.0)
    s.line(xr, top - 26, xr, top, th.primary, 1.4, dash="5,4")
    s.text(xr + 8, top - 14, "reference plane", 13, th.primary, anchor="start")
    s.text(xr + 34, top + 28, "the device", 13, th.fg, anchor="start")

    # The loudspeaker on its stand, front panel towards the device.
    s.rect(xf - 45, axis - 22, 45, 44, th.panel, th.fg, rx=4, sw=2.0)
    s.circle(xf - 17, axis, 11, th.fg)
    s.circle(xf - 17, axis, 4.5, th.bg)
    s.line(xf, axis - 22, xf, axis + 22, th.primary, 3.2)
    s.line(xf - 23, axis + 22, xf - 23, gy, th.fg, 2.2)
    s.line(xf - 39, gy, xf - 7, gy, th.fg, 2.2)
    s.text(xf, axis - 32, "loudspeaker", 13, th.fg, anchor="end", bold=True)

    # The grid seen edge on: one microphone of each row.
    s.line(xg, rows[0] - 10, xg, rows[2] + 10, th.fg, 1.6)
    s.line(xg, rows[2] + 10, xg, gy, th.muted, 1.4)
    s.text(xr + 38, rows[0] - 18, "microphones", 13, th.fg, anchor="start", bold=True)
    for y, numbers in zip(rows, ("1 · 2 · 3", "4 · 5 · 6", "7 · 8 · 9"), strict=True):
        s.line(xg + 8, y, xr + 32, y, th.muted, 0.9, dash="2,3")
        s.text(xr + 38, y + 4.5, numbers, 13, th.fg, anchor="start")

    # The reference height.
    s.line(70, axis, xf - 47, axis, th.muted, 0.9, dash="3,3")
    s.dim(70, gy, 70, axis, "$h_S = h_B/2$", size=13, label_side="right")

    # The two arrivals the window has to end before: over the top edge to the
    # top row, and off the ground (the loudspeaker's image below it) to the
    # bottom row.
    image_y = 2.0 * gy - axis
    ground_x = xf + (image_y - gy) / (image_y - rows[2]) * (xg - xf)
    s.path(
        f"M {xf + 2} {axis - 3} L {xr} {top} L {xg + 3.4:.1f} {rows[0] - 22}",
        stroke=th.secondary,
        sw=1.7,
        dash="6,4",
    )
    s.arrow(xg + 3.4, rows[0] - 22, xg + 1.2, rows[0] - 8, th.secondary, 1.7)
    s.path(
        f"M {xf + 2} {axis + 6} L {ground_x:.1f} {gy} L {xg - 6.2:.1f} {rows[2] + 18}",
        stroke=th.secondary,
        sw=1.7,
        dash="6,4",
    )
    s.arrow(xg - 6.2, rows[2] + 18, xg - 2.4, rows[2] + 7, th.secondary, 1.7)

    # The direct sound and the reflection, at microphone 5.
    s.arrow(xf + 3, axis - 5, xg - 7, axis - 1.5, th.accent, 2.0)
    s.line(xf + 3, axis + 5, xr - 1, axis + 9, th.primary, 2.0)
    s.arrow(xr - 1, axis + 9, xg + 6, axis + 3, th.primary, 2.0)
    for y in rows:
        s.circle(xg, y, 4.6, th.fg, th.bg, 1.2)

    # The two distances of Table 1, below the ground where nothing crosses
    # them.
    s.line(xf, axis + 22, xf, gy + 70, th.muted, 0.9, dash="3,3")
    s.line(xg, gy, xg, gy + 36, th.muted, 0.9, dash="3,3")
    s.line(xr, gy, xr, gy + 70, th.muted, 0.9, dash="3,3")
    s.arrow(xg - 24, gy + 30, xg, gy + 30, th.muted, 1.2)
    s.arrow(xr + 24, gy + 30, xr, gy + 30, th.muted, 1.2)
    s.text(xr + 30, gy + 35, "$d_M$ = 0.25 m", 14, th.fg, anchor="start")
    s.dim(xf, gy + 64, xr, gy + 64, "$d_S$ = 1.50 m", size=14)

    legend = (
        (th.accent, "", "direct sound: 1.25 m to microphone 5"),
        (th.primary, "", "reflection off the device: 1.75 m to microphone 5"),
        (
            th.secondary,
            "6,4",
            "diffraction over the top edge, reflection off the ground:",
        ),
        ("", "", "the time window has to end before either arrives (5.5.7)"),
    )
    size = s.fit_size([row[2] for row in legend], [13, 12], 410)
    for k, (colour, dash, label) in enumerate(legend):
        y = 574 + 20 * k
        if colour:
            s.line(40, y - 4.5, 64, y - 4.5, colour, 2.0, dash=dash)
        s.text(72, y, label, size, th.fg if colour else th.muted, anchor="start")

    # --- (b) front view, 75 px to the metre -------------------------------
    front = 75.0
    cx, cy = 700.0, gy - 2.0 * front
    half = 2.0 * front
    radius = 1.96 * front
    step = 0.40 * front

    s.text(
        500,
        72,
        "(b) The grid as the loudspeaker sees it",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )
    s.ground(gy, 520, 880)
    s.rect(cx - half, gy - 2 * half, 2 * half, 2 * half, th.panel, th.fg, sw=2.0)
    s.dim(cx - half, gy - 2 * half, cx + half, gy - 2 * half, "4 m", -18, 13)
    s.dim(cx - half, gy, cx - half, gy - 2 * half, "4 m", -18, 13)
    s.ellipse(cx, cy, radius, radius, stroke=th.muted, sw=1.4, dash="6,4")
    # The radius, drawn from clear of the grid out to the circle.
    ux, uy = -0.819, 0.574
    s.arrow(
        cx + 66 * ux, cy + 66 * uy, cx + radius * ux, cy + radius * uy, th.muted, 1.2
    )
    s.text(cx + 104 * ux - 6, cy + 104 * uy - 8, "$r$", 13, th.fg, anchor="end")
    # The spacing, between two columns of the top row.
    s.line(cx, cy - step - 22, cx + step, cy - step - 22, th.muted, 1.2)
    for x in (cx, cx + step):
        s.line(x, cy - step - 26, x, cy - step - 18, th.muted, 1.2)
    s.text(cx + step / 2, cy - step - 31, "$s$ = 0.40 m", 12, th.fg)
    for k in range(9):
        x = cx + (k % 3 - 1) * step
        y = cy + (k // 3 - 1) * step
        if k < 6:
            s.circle(x, y, 11, th.primary)
            s.text(x, y + 4.5, str(k + 1), 12, th.bg, bold=True)
        else:
            s.circle(x, y, 11, th.bg, th.primary, 1.8)
            s.text(x, y + 4.5, str(k + 1), 12, th.fg, bold=True)

    key = (
        (0, "1 to 6: every band, from 100 Hz"),
        (1, "7 to 9: from the 200 Hz band up (5.5.5)"),
        (2, "sampled area of microphone 5, $r$ = 1.96 m:"),
        (-1, "nothing else that reflects inside it (5.6.1, 5.6.3)"),
        (3, "4 m × 4 m: the smallest sample that is valid"),
        (-1, "from 200 Hz to 5 kHz (5.3)"),
    )
    size = s.fit_size([label for _, label in key], [13, 12], 352)
    y = 508.0
    for mark, label in key:
        if mark == 0:
            s.circle(510, y - 4.5, 8, th.primary)
        elif mark == 1:
            s.circle(510, y - 4.5, 8, th.bg, th.primary, 1.8)
        elif mark == 2:
            s.ellipse(510, y - 4.5, 8, 8, stroke=th.muted, sw=1.4, dash="4,3")
        elif mark == 3:
            s.rect(503, y - 11.5, 14, 14, th.panel, th.fg, sw=1.6)
        s.text(526, y, label, size, th.muted if mark < 0 else th.fg, anchor="start")
        y += 18 if mark in (2, 3) else 22

    # --- (c) the free-field record ------------------------------------------
    s.line(40, 646, 860, 646, th.muted, 1.0, dash="6,5")
    s.text(
        40, 680, "(c) The free-field record", 15, th.primary, anchor="start", bold=True
    )
    tilt = math.radians(20.0)
    ax_x, ax_y = math.cos(tilt), -math.sin(tilt)  # along the loudspeaker axis
    up_x, up_y = math.sin(tilt), math.cos(tilt)  # along the grid, downwards
    fx, fy = 112.0, 800.0
    box = [
        (fx + 22 * up_x, fy + 22 * up_y),
        (fx - 22 * up_x, fy - 22 * up_y),
        (fx - 45 * ax_x - 22 * up_x, fy - 45 * ax_y - 22 * up_y),
        (fx - 45 * ax_x + 22 * up_x, fy - 45 * ax_y + 22 * up_y),
    ]
    s.path(
        "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in box) + " Z",
        fill=th.panel,
        stroke=th.fg,
        sw=2.0,
    )
    s.circle(fx - 17 * ax_x, fy - 17 * ax_y, 11, th.fg)
    s.circle(fx - 17 * ax_x, fy - 17 * ax_y, 4.5, th.bg)
    s.line(box[0][0], box[0][1], box[1][0], box[1][1], th.primary, 3.2)
    reach = 1.25 * scale
    mx, my = fx + reach * ax_x, fy + reach * ax_y
    offset = 0.40 * scale
    s.line(
        mx - (offset + 10) * up_x,
        my - (offset + 10) * up_y,
        mx + (offset + 10) * up_x,
        my + (offset + 10) * up_y,
        th.fg,
        1.6,
    )
    s.arrow(fx + 3 * ax_x, fy + 3 * ax_y, mx - 7 * ax_x, my - 7 * ax_y, th.accent, 2.0)
    for k in (-1, 0, 1):
        s.circle(mx + k * offset * up_x, my + k * offset * up_y, 4.6, th.fg, th.bg, 1.2)
    s.text(fx + 34, fy + 36, "$d_{SM}$ = 1.25 m", 14, th.fg, anchor="start")
    notes = (
        "the same loudspeaker and grid, the same",
        "distance apart, facing nothing: neither an",
        "object nor the ground (3.16, 5.6.2.2)",
    )
    size = s.fit_size(notes, [13, 12], 292)
    for k, note in enumerate(notes):
        s.text(40, 866 + 18 * k, note, size, th.muted, anchor="start")

    # --- what is recorded -----------------------------------------------------
    s.text(
        372,
        680,
        "What is recorded, and the clause that asks for it",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )
    records = (
        (
            "Directivity, once per loudspeaker: at each microphone position",
            "and at the same distance on its specular path (Formula (3))",
        ),
        (
            "In front of the device: nine impulse responses per grid position",
            "(5.6.2.2); A, B and C if not flat, one per material if not",
            "homogeneous (5.6.2.3), four or more in two directions (5.6.2.4)",
        ),
        (
            "Free field: nine more per grid position, with the geometry",
            "unchanged (5.6.2.2)",
        ),
        (
            "Reflecting plate, 1.60 m × 1.60 m or larger: the path differences",
            "within 25 mm of Table 3 (5.6.2.5, 5.6.2.6)",
        ),
        (
            "Gain check, per grid position: the incident sound of both records,",
            "1.3 ms window, bands from 500 Hz to 2 kHz (Formula (4))",
        ),
    )
    size = s.fit_size([line for record in records for line in record], [13, 12], 478)
    y = 708.0
    for record in records:
        s.circle(378, y - 4.5, 3.2, th.primary)
        for k, line in enumerate(record):
            s.text(390, y, line, size, th.fg if k == 0 else th.muted, anchor="start")
            y += 18
        y += 8


def _d_barrier_four_paths(s: SVG, th: Theme) -> None:
    gy = 260.0
    x0, x1 = 110.0, 800.0
    sx, sy = x0, gy - 60.0  # source, 1 m high (out of scale)
    rx, ry = x1, gy - 90.0  # receiver, 1,5 m high
    ex = x0 + (x1 - x0) * 0.5  # barrier at 50 m of 100 m
    ey = gy - 200.0  # 4 m screen (out of scale)

    s.ground(gy, 60.0, 850.0)
    # Mirror images below the ground plane.
    sy_i = gy + (gy - sy)
    ry_i = gy + (gy - ry)

    # The screen.
    s.rect(ex - 7, ey, 14, gy - ey, th.panel, th.fg, sw=2)
    s.text(ex + 14, gy - 16, "4 m screen", 16, th.fg, anchor="start", bold=True)

    # Four routes, each one a source (or its image) over the edge to the
    # receiver (or its image).
    routes = (
        (sy, ry, th.primary, "0 bounces", "none"),
        (sy_i, ry, th.secondary, "1 bounce, source side", "6,4"),
        (sy, ry_i, th.accent, "1 bounce, receiver side", "2,4"),
        (sy_i, ry_i, "#9467bd", "2 bounces", "10,5"),
    )
    # Fanned by a few pixels at the edge so four coincident legs stay legible.
    for i, (y_src, y_rec, color, _label, dash) in enumerate(routes):
        eyy = ey + (i - 1.5) * 5.0
        s.path(
            f"M {sx:.1f} {y_src:.1f} L {ex:.1f} {eyy:.1f} L {rx:.1f} {y_rec:.1f}",
            stroke=color,
            sw=2.0,
            dash="" if dash == "none" else dash,
        )

    # Q at each ground reflection (the specular points of the image paths).
    for qx in (sx + (ex - sx) * 0.5, ex + (rx - ex) * 0.5):
        s.circle(qx, gy, 7, th.bg, th.fg, sw=1.8)
        s.text(qx, gy - 12, "$Q$", 15, th.fg, bold=True)

    # Source, receiver and their images.
    s.circle(sx, sy, 9, th.secondary)
    s.text(sx, sy - 20, "Source", 16, th.fg, bold=True)
    s.mic(rx, ry, gy, 0.9)
    s.text(rx, ry - 20, "Receiver", 16, th.fg, bold=True)
    s.circle(sx, sy_i, 8, th.secondary, th.bg, sw=1.4)
    s.text(sx, sy_i + 26, "image source", 15, th.muted)
    s.circle(rx, ry_i, 8, th.primary, th.bg, sw=1.4)
    s.text(rx, ry_i + 26, "image receiver", 15, th.muted)
    s.line(sx, sy, sx, sy_i, th.muted, 1.0, dash="3,3")
    s.line(rx, ry, rx, ry_i, th.muted, 1.0, dash="3,3")

    # Legend of the four routes.
    lx, ly = 96.0, 430.0
    s.rect(lx, ly, 430, 128, th.panel, th.muted, rx=8, sw=1.2)
    s.text(
        lx + 14,
        ly + 26,
        "Four coherent routes over one edge",
        16,
        th.fg,
        anchor="start",
        bold=True,
    )
    for i, (_, _, color, label, dash) in enumerate(routes):
        yy = ly + 52 + i * 24
        s.line(
            lx + 16,
            yy - 5,
            lx + 56,
            yy - 5,
            color,
            2.4,
            dash="" if dash == "none" else dash,
        )
        s.text(lx + 66, yy, label, 15, th.fg, anchor="start")

    # Inset: the two-edge (thick) case, 290 px wide, which holds the Spanish
    # heading that ran out through the right side of the 250 px box. The
    # drawing inside keeps its place in the middle of the box.
    tx, ty = 560.0, 430.0
    s.rect(tx, ty, 290, 128, th.panel, th.muted, rx=8, sw=1.2)
    s.text(
        tx + 14,
        ty + 26,
        "Thick barrier: two edges",
        16,
        th.fg,
        anchor="start",
        bold=True,
    )
    bx0, bx1, by0 = tx + 80, tx + 150, ty + 96
    s.rect(bx0, ty + 56, bx1 - bx0, by0 - ty - 56, th.bg, th.fg, sw=1.6)
    s.path(
        f"M {tx + 40} {ty + 84} L {bx0} {ty + 56} L {bx1} {ty + 56} "
        f"L {tx + 246} {ty + 88}",
        stroke=th.primary,
        sw=2.0,
    )
    s.dim(bx0, ty + 46, bx1, ty + 46, "$e$", 0, 15)


# ---------------------------------------------------------------------------
# CNOSSOS-EU road source line geometry (2.2)
# ---------------------------------------------------------------------------


def _d_cnossos_road(s: SVG, th: Theme) -> None:
    # --- plan ------------------------------------------------------------
    py = 150.0
    rx0, rx1 = 70.0, 700.0
    lane = 44.0
    # The heading takes the band right under the plate title and the
    # 60 m dimension takes the one under it: the Spanish heading runs to
    # x = 409, past the source the dimension starts from, so the two
    # cannot share a line.
    s.text(
        rx0,
        56.0,
        "Plan: two-lane urban arterial",
        17,
        th.fg,
        anchor="start",
        bold=True,
    )
    s.rect(rx0, py - lane, rx1 - rx0, 2 * lane, th.panel, th.muted, sw=1.2)
    s.line(rx0, py, rx1, py, th.muted, 1.6, dash="14,10")

    # A source line on each lane centre.
    for cy in (py - lane / 2, py + lane / 2):
        s.line(rx0, cy, rx1, cy, th.secondary, 2.2, dash="9,6")
    s.text(
        rx1 + 10, py - lane / 2 + 6, "source line,", 15, th.secondary, anchor="start"
    )
    s.text(
        rx1 + 10,
        py + lane / 2 + 6,
        "one per lane centre",
        15,
        th.secondary,
        anchor="start",
    )

    # dL = 20 m segments on the near lane, one with its point source.
    seg = (rx1 - rx0) / 12.0
    cy = py + lane / 2
    for i in range(13):
        s.line(rx0 + i * seg, cy - 9, rx0 + i * seg, cy + 9, th.muted, 1.2)
    hx = rx0 + 5.5 * seg
    s.circle(hx, cy, 8, th.secondary)
    # Far enough below the road for the label to clear its edge, which ran
    # along the top of the label at cy + 30.
    s.dim(rx0 + 5 * seg, cy + 44, rx0 + 6 * seg, cy + 44, "dL = 20 m", 0, 15)
    # The per-segment level is set as the guide that carries this plate
    # writes it, L'_{W,eq,line,i} with the eq and line upright and the W and
    # i italic.
    s.text(
        rx0,
        cy + 70,
        "each segment carries $L′_{W,eq,line,i}$ + 10 lg(dL)",
        15,
        th.fg,
        anchor="start",
        mono=False,
    )

    # The junction and its taper.
    jx = rx0 + 9.0 * seg
    s.line(jx, py - lane - 20, jx, py + lane + 20, th.primary, 2.4)
    s.text(
        jx + 8,
        py - lane - 26,
        "signal-controlled junction",
        15,
        th.primary,
        anchor="start",
    )
    s.dim(hx, py - lane - 23, jx, py - lane - 23, "$x$ = 60 m", 0, 15)
    s.line(hx, py - lane - 29, hx, py - lane - 4, th.muted, 0.9, dash="3,3")

    # A small inline graph of the taper, clear of the road, and high enough
    # to leave the receiver's label room under it: at gy0 = 300 its box sat
    # on the label.
    gx0, gx1, gy0 = 720.0, 850.0, 290.0
    s.rect(gx0 - 16, gy0 - 74, (gx1 - gx0) + 46, 106, th.panel, th.muted, rx=6, sw=1.1)
    s.line(gx0, gy0, gx1, gy0, th.muted, 1.4)
    s.line(gx0, gy0, gx0, gy0 - 48, th.muted, 1.4)
    s.path(f"M {gx0} {gy0 - 48} L {gx1} {gy0}", stroke=th.primary, sw=2.0)
    s.text(gx0 - 12, gy0 - 56, "$max(1 − |x|/100, 0)$", 13, th.fg, anchor="start")
    s.text(gx1, gy0 + 22, "100 m", 13, th.muted)

    # The receiving facade, in plan.
    fy = py + lane + 118.0
    s.rect(220.0, fy, 300.0, 30, th.panel, th.fg, sw=1.8)
    s.text(370.0, fy + 22, "dwelling façade", 15, th.fg)
    s.dim(560.0, cy, 560.0, fy, "25 m", 0, 15, label_side="right")
    s.line(520.0, fy + 15, 560.0, fy + 15, th.muted, 0.9, dash="3,3")
    s.line(rx0 + 6 * seg, cy, 560.0, cy, th.muted, 0.9, dash="3,3")

    # --- section ---------------------------------------------------------
    sy = 500.0
    s.text(70.0, 392.0, "Section", 17, th.fg, anchor="start", bold=True)
    s.ground(sy, 60.0, 860.0)
    s.rect(120.0, sy - 8, 300.0, 8, th.muted)
    s.text(240.0, sy + 34, "road surface", 15, th.muted)
    s.circle(300.0, sy - 22, 8, th.secondary)
    s.dim(300.0, sy, 300.0, sy - 22, "0,05 m", 40, 15, label_side="right")
    s.text(300.0, sy - 44, "equivalent point source", 15, th.fg, bold=True)

    # The gradient, with the two halves of a bidirectional flow.
    s.path(f"M 120 {sy - 6} L 420 {sy - 40}", stroke=th.primary, sw=2.2)
    s.arrow(150.0, sy - 66, 250.0, sy - 78, th.primary, 1.8)
    s.arrow(390.0, sy - 90, 290.0, sy - 78, th.secondary, 1.8)
    s.text(430.0, sy - 118, "gradient $s$: the flow is split", 15, th.primary)
    s.text(430.0, sy - 98, "and corrected uphill and downhill", 15, th.primary)

    rxr = 700.0
    s.rect(rxr - 40, sy - 150, 120, 150, th.panel, th.fg, sw=1.8)
    s.mic(rxr - 90, sy - 120, sy, 0.9)
    s.dim(rxr - 90, sy, rxr - 90, sy - 120, "4 m", -46, 15)
    s.text(rxr - 46, sy - 162, "receiver point", 15, th.fg, anchor="start", bold=True)


# ---------------------------------------------------------------------------
# CNOSSOS-EU railway source lines and directivity angles (2.3)
# ---------------------------------------------------------------------------


def _d_cnossos_rail(s: SVG, th: Theme) -> None:
    import math

    # --- section ---------------------------------------------------------
    gy = 400.0
    s.text(70.0, 74.0, "Section", 17, th.fg, anchor="start", bold=True)
    s.ground(gy, 190.0, 470.0)
    cx = 330.0  # track centre
    gauge = 92.0  # 1,435 m, out of scale
    s.path(
        f"M {cx - 130} {gy} L {cx - 96} {gy - 30} L {cx + 96} {gy - 30} "
        f"L {cx + 130} {gy} Z",
        fill=th.panel,
        stroke=th.muted,
        sw=1.4,
    )
    s.rect(cx - 86, gy - 42, 172, 12, th.muted)
    for dx in (-gauge / 2, gauge / 2):
        s.rect(cx + dx - 7, gy - 62, 14, 20, th.fg)
    datum = gy - 62.0
    s.line(cx - 120, datum, cx + 150, datum, th.secondary, 2.0, dash="9,5")
    # Both captions of the section end on the same right edge, clear of
    # the receiver's stand at x = 800: set from the left they run into it
    # in either language.
    s.text(
        782,
        datum + 26,
        "datum: the plane tangent to the two rail heads",
        15,
        th.secondary,
        anchor="end",
    )
    s.dim(cx - gauge / 2, gy - 76, cx + gauge / 2, gy - 76, "1,435 m", 0, 15)

    # Source A and source B on the track centre.
    ay = datum - 60.0
    by = datum - 250.0
    s.circle(cx, ay, 9, th.primary)
    s.circle(cx, by, 9, th.accent)
    s.dim(cx, datum, cx, ay, "0,5 m", 60, 15, label_side="right")
    s.dim(cx, datum, cx, by, "4,0 m", 120, 15, label_side="right")
    s.text(cx - 26, ay - 6, "A: rolling, impact, squeal,", 14, th.fg, anchor="end")
    s.text(cx - 26, ay + 16, "bridge, low traction", 14, th.fg, anchor="end")
    s.text(cx - 26, by + 16, "B: exhausts, roof apparatus,", 14, th.fg, anchor="end")
    s.text(cx - 26, by + 38, "pantograph recess", 14, th.fg, anchor="end")

    # The receiver, with the line of sight to each source and psi.
    rx = 800.0
    ry = gy - 150.0
    s.mic(rx, ry, gy, 0.9)
    s.line(cx, ay, rx, ry, th.primary, 1.8)
    s.line(cx, by, rx, ry, th.accent, 1.8)
    s.line(cx, ay, rx + 10, ay, th.muted, 1.2, dash="5,4")
    # Above the line of sight, which ran through the label set on it.
    s.text(cx + 250, ay - 30, "$ψ > 0$", 16, th.primary)
    s.text(
        782,
        ay + 34,
        "$ψ ≤ 0$: the vertical correction of A is zero",
        15,
        th.secondary,
        anchor="end",
    )
    s.text(rx, ry - 24, "receiver, 4 m", 15, th.fg, bold=True)

    s.circle(cx - 12, ay, 0.1, th.primary)

    # --- plan ------------------------------------------------------------
    py = 610.0
    s.text(70.0, 512.0, "Plan", 17, th.fg, anchor="start", bold=True)
    s.line(90.0, py, 520.0, py, th.muted, 2.0, dash="12,8")
    s.text(96.0, py - 14, "track axis", 15, th.muted, anchor="start")
    ox = 300.0
    s.circle(ox, py, 7, th.fg)
    pts = []
    for deg in range(0, 361, 4):
        a = math.radians(deg)
        lvl = 10.0 * math.log10(0.01 + 0.99 * math.sin(a) ** 2)
        r = max(76.0 * (1.0 + lvl / 24.0), 4.0)
        pts.append(f"{ox + r * math.cos(a):.1f} {py - r * math.sin(a):.1f}")
    s.path("M " + " L ".join(pts) + " Z", stroke=th.accent, sw=2.0)
    s.text(ox, py - 92, "0 dB broadside", 15, th.accent)
    s.text(ox - 96, py + 26, "−20 dB along the track", 15, th.accent, anchor="end")
    s.arrow(ox, py, ox + 140, py - 78, th.primary, 1.8)
    s.text(ox + 148, py - 82, "receiver bearing", 15, th.primary, anchor="start")
    s.text(ox + 56, py - 18, "$φ$", 17, th.primary, bold=True)
    # The note sits low, under the bearing's label: level with it, the box
    # ran through the end of the Spanish.
    s.rect(600.0, py - 40, 280, 112, th.panel, th.muted, rx=8, sw=1.2)
    s.text(614.0, py - 10, "Impact noise applies from 50 m", 14, th.fg, anchor="start")
    s.text(614.0, py + 10, "before a joint to 50 m after it", 14, th.fg, anchor="start")
    s.text(614.0, py + 40, "Curve squeal needs ≥ 50 m", 14, th.fg, anchor="start")
    s.text(614.0, py + 60, "of continuous curve", 14, th.fg, anchor="start")


# ---------------------------------------------------------------------------
# IEC 61400-11 ground-board microphone mounting (6.1.5, 7.1)
# ---------------------------------------------------------------------------


def _d_wind_turbine_board(s: SVG, th: Theme) -> None:
    # --- plan ------------------------------------------------------------
    cx, cy, r = 250.0, 210.0, 130.0
    s.circle(cx, cy, r, th.panel, th.fg, sw=2.2)
    s.dim(cx - r, cy + r + 34, cx + r, cy + r + 34, "diameter ≥ 1,0 m", 0, 15)
    s.circle(cx, cy, 9, th.fg)
    s.arrow(cx, cy, cx + r + 46, cy, th.secondary, 2.0)
    s.text(cx + r + 54, cy + 6, "to the turbine", 15, th.secondary, anchor="start")
    # The optional split, off the centre line and parallel to the axis.
    s.line(cx - r * 0.86, cy - 46, cx + r * 0.86, cy - 46, th.primary, 2.0, dash="8,5")
    # Beside the plate, level with the split it names: over the split, the
    # plate's edge ran through both ends of the line.
    s.text(
        cx + r + 12,
        cy - 41,
        "split (if any): off centre, parallel, gap < 1 mm",
        14,
        th.primary,
        anchor="start",
    )
    s.text(cx, cy - r - 24, "Plan", 17, th.fg, bold=True)

    # --- section ---------------------------------------------------------
    gy = 470.0
    bx0, bx1 = 470.0, 830.0
    s.ground(gy, 440.0, 860.0)
    s.rect(bx0, gy - 12, bx1 - bx0, 12, th.panel, th.fg, sw=2.0)
    s.text((bx0 + bx1) / 2, gy + 108, "plywood ≥ 12,0 mm  ·  metal ≥ 2,5 mm", 15, th.fg)
    # Soil fillet at the edges.
    s.path(f"M {bx0 - 34} {gy} L {bx0} {gy - 12} L {bx0} {gy} Z", fill=th.muted)
    s.path(f"M {bx1 + 34} {gy} L {bx1} {gy - 12} L {bx1} {gy} Z", fill=th.muted)
    s.text(bx0 + 6, gy + 30, "soil fillet", 14, th.muted, anchor="start")

    # Capsule with its diaphragm in the plane of the board.
    mcx = (bx0 + bx1) / 2
    s.rect(mcx - 22, gy - 12, 44, 10, th.fg, rx=3)
    s.text(mcx, gy + 82, "capsule diaphragm in the board plane, ≤ 13 mm", 14, th.fg)
    # Primary windscreen: a foam half-sphere ~90 mm across.
    s.path(
        f"M {mcx - 68} {gy - 12} A 68 68 0 0 1 {mcx + 68} {gy - 12} Z",
        fill=th.accent,
        stroke=th.fg,
        sw=1.6,
    )
    # Named under the board with the other parts: over the dome, the
    # secondary screen's outline ran through the name.
    s.text(mcx, gy + 56, "primary windscreen ≈ 90 mm", 15, th.fg)
    # Ghosted secondary windscreen.
    s.path(
        f"M {mcx - 116} {gy - 12} A 116 116 0 0 1 {mcx + 116} {gy - 12}",
        stroke=th.muted,
        sw=1.8,
        dash="8,6",
    )
    s.text(mcx, gy - 186, "secondary, for high wind only:", 14, th.muted)
    s.text(mcx, gy - 166, "document and correct its insertion loss", 14, th.muted)
    s.text(bx0 - 20, 330.0, "Section", 17, th.fg, anchor="start", bold=True)

    # Tolerance box, sized on its longest line in either language and set
    # against the sheet's own left margin, so it still stops short of the
    # ground the section stands on.
    s.rect(40.0, 400.0, 392.0, 156.0, th.panel, th.muted, rx=8, sw=1.2)
    s.text(56.0, 430.0, "Position (clause 7.1)", 16, th.fg, anchor="start", bold=True)
    for i, line in enumerate(
        (
            "within ±15° of downwind",
            "$R_0$ to ±20 %, max ±30 m, measured to ±2 %",
            "board inclination $φ$ between 25° and 40°",
            "reflections from structures < 0,2 dB",
        )
    ):
        s.text(56.0, 458.0 + i * 24.0, line, 15, th.fg, anchor="start")


# ---------------------------------------------------------------------------
# RD 1367/2007: phase to period to year, and the three criteria
# ---------------------------------------------------------------------------


def _d_rd1367_chain(s: SVG, th: Theme) -> None:
    # Stage 1: the 24 h clock.
    y0 = 90.0
    x0, x1 = 70.0, 830.0
    w = x1 - x0
    s.text(
        x0,
        y0 - 12,
        "1: the day, split into evaluation periods (Annex I A.1)",
        16,
        th.fg,
        anchor="start",
        bold=True,
    )
    bounds = (
        (0.0, 7.0, th.primary, "night 23-07"),
        (7.0, 19.0, th.accent, "day 07-19"),
        (19.0, 23.0, "#e8a838", "evening 19-23"),
        (23.0, 24.0, th.primary, ""),
    )
    for a, b, color, label in bounds:
        s.rect(x0 + w * a / 24.0, y0, w * (b - a) / 24.0, 42, th.panel, color, sw=2.0)
        if label:
            s.text(x0 + w * (a + b) / 48.0, y0 + 28, label, 15, th.fg)
    # The day, broken into the worked example's three phases.
    py = y0 + 62.0
    phases = (
        (7.0, 9.0, "2 h shut"),
        (9.0, 15.0, "6 h, machine"),
        (15.0, 19.0, "4 h, rest"),
    )
    for a, b, label in phases:
        cell = w * (b - a) / 24.0
        s.rect(x0 + w * a / 24.0, py, cell, 34, th.panel, th.muted, sw=1.2)
        # A name wider than its cell goes under it: the Spanish of the 2 h
        # phase ran out through both sides of its 63 px cell.
        inside = s.text_width(label, 14) <= cell - 12
        s.text(x0 + w * (a + b) / 48.0, py + (23 if inside else 52), label, 14, th.fg)
    s.text(
        x0,
        py + 76,
        "noise phases $T_i$ of uniformly perceived level",
        15,
        th.muted,
        anchor="start",
    )

    # Stage 2: the phase corrections.
    y1 = 250.0
    s.rect(x0, y1, 360, 108, th.panel, th.muted, rx=8, sw=1.2)
    s.text(
        x0 + 14,
        y1 + 28,
        "2: each phase, corrected",
        16,
        th.fg,
        anchor="start",
        bold=True,
    )
    # The corrected levels as the guide writes them: Keq upright beside the
    # Aeq it corrects, the phase duration Ti italic, the three penalties
    # upright, and the phase level inside the exponent of the period sum.
    s.text(
        x0 + 14,
        y1 + 56,
        "$L_{Keq,Ti} = L_{Aeq,Ti} + K_t + K_f + K_i$",
        15,
        th.fg,
        anchor="start",
        upright=("K_i",),
    )
    s.text(
        x0 + 14,
        y1 + 82,
        "$K_t + K_f + K_i ≤ 9$ dB (Annex IV A.3.3)",
        15,
        th.secondary,
        anchor="start",
        # The impulsive penalty beside the tonal and low-frequency ones.
        upright=("K_i",),
    )

    # Stage 3: the duration-weighted mean.
    s.arrow(x0 + 372, y1 + 54, x0 + 424, y1 + 54, th.muted, 1.8)
    s.rect(x0 + 436, y1, 324, 124, th.panel, th.muted, rx=8, sw=1.2)
    s.text(
        x0 + 450, y1 + 28, "3: the period level", 16, th.fg, anchor="start", bold=True
    )
    s.text(
        x0 + 450,
        y1 + 62,
        "$L_{Keq,x} = 10 lg[(1/T) Σ_i T_i·10^{L_{Keq,Ti}/10}]$",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        x0 + 450,
        y1 + 98,
        "round_reported_level → 57 dB",
        15,
        th.accent,
        anchor="start",
        mono=True,
    )

    # Stage 4: the annual mean.
    y2 = 400.0
    s.rect(x0, y2, 360, 96, th.panel, th.muted, rx=8, sw=1.2)
    s.text(
        x0 + 14, y2 + 28, "4: the annual value", 16, th.fg, anchor="start", bold=True
    )
    s.text(
        x0 + 14, y2 + 56, "$L_{K,x}$ over the operating days", 15, th.fg, anchor="start"
    )
    s.text(
        x0 + 14,
        y2 + 82,
        "303 open / 62 closed → 56 dB",
        15,
        th.accent,
        anchor="start",
        mono=True,
    )
    s.arrow(x0 + 180, y1 + 118, x0 + 180, y2 - 8, th.muted, 1.8)

    # The three criteria.
    s.arrow(x0 + 372, y2 + 46, x0 + 424, y2 + 46, th.muted, 1.8)
    cx = x0 + 436
    for i, (label, value) in enumerate(
        (
            ("worst phase ≤ limit + 5 dB", "59 ≤ 60 ✓"),
            ("daily $L_{Keq,x}$ ≤ limit + 3 dB", "57 ≤ 58 ✓"),
            ("annual $L_{K,x}$ ≤ limit", "56 > 55 ✗"),
        )
    ):
        yy = y2 + i * 40
        color = th.secondary if i == 2 else th.accent
        s.rect(cx, yy, 324, 32, th.bg, color, rx=6, sw=1.8)
        s.text(cx + 12, yy + 22, label, 14, th.fg, anchor="start")
        s.text(cx + 312, yy + 22, value, 14, color, anchor="end", mono=True)
    s.text(
        x0,
        y2 + 146,
        "Article 25.2 drops the third criterion for an activity already in operation",
        14,
        th.muted,
        anchor="start",
    )


# ---------------------------------------------------------------------------
# ISO 11819-1 statistical pass-by: the site and the microphone (6.1, 8.1)
# ---------------------------------------------------------------------------


def _d_rd1367_inspection(s: SVG, th: Theme) -> None:
    """Where the meter stands and what it reads when an activity is inspected.

    The chain plate beside this one starts at a phase level; this is how the
    level gets there. Every figure is the consolidated BOE text of RD
    1367/2007 (BOE-A-2007-18397): the indoor positions are Annex I A.3 b (PDF
    page 22) through Annex IV A.3.4 d (page 27), the series of a noise phase
    is A.3.4.2 b (page 28), the precautions are A.3.5 (page 29) and the
    instrument is Article 30 (page 16). A.3.4.2 gives the microphone of an
    activity no height outdoors (the 4 m of A.3.4.1 c belong to the quality
    objectives of an area), so the outdoor panel draws none.
    """
    # --- (a) indoors: one position of the receiving room, in section ------
    scale = 70.0
    x0, floor = 70.0, 300.0
    x1, ceiling = x0 + 4.2 * scale, floor - 2.5 * scale
    s.text(
        40,
        72,
        "(a) Indoors: the receiving room",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )
    s.rect(x0, ceiling, x1 - x0, floor - ceiling, th.panel, th.fg, sw=3.0)
    # The window in one wall and the door in the other, both shut.
    s.rect(x0 - 5, floor - 2.1 * scale, 10, 1.2 * scale, th.bg, th.primary, sw=2.0)
    s.rect(x1 - 5, floor - 2.0 * scale, 10, 2.0 * scale, th.bg, th.muted, sw=2.0)
    s.text(x0 + 2, ceiling - 12, "window, closed", 13, th.primary, anchor="start")
    s.text(x1 - 2, ceiling - 12, "door, closed", 13, th.muted, anchor="end")
    mic_x = x0 + 1.5 * scale
    mic_y = floor - 1.35 * scale
    s.mic(mic_x, mic_y, floor, scale=0.8)
    s.dim(x0 + 6, mic_y - 14, mic_x, mic_y - 14, "≈ 1.5 m", size=13)
    s.dim(mic_x, mic_y - 14, x1 - 6, mic_y - 14, "≥ 1 m", size=13)
    s.dim(
        mic_x + 34,
        floor,
        mic_x + 34,
        mic_y,
        "1.2 m to 1.5 m",
        size=13,
        label_side="right",
    )
    s.line(mic_x + 6, mic_y, mic_x + 34, mic_y, th.muted, 0.9, dash="3,3")
    indoor = (
        (th.fg, "doors and windows closed (A.3.4 d)"),
        (th.fg, "three positions or more, each like this one;"),
        (th.muted, "if they do not fit, the centre of the room (Annex I A.3 b)"),
    )
    size = s.fit_size([label for _, label in indoor], [13, 12], 400)
    for k, (colour, label) in enumerate(indoor):
        s.text(40, floor + 28 + 18 * k, label, size, colour, anchor="start")

    # --- (b) outdoors: incident sound at the point of highest level --------
    s.text(
        480,
        72,
        "(b) Outdoors: the evaluation point",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )
    s.ground(floor, 480, 862)
    s.rect(492, floor - 80, 80, 80, th.panel, th.fg, rx=3, sw=2.0)
    s.circle(532, floor - 40, 14, th.fg)
    s.circle(532, floor - 40, 5, th.bg)
    s.text(532, floor - 92, "the activity", 13, th.fg, bold=True)
    s.rect(806, floor - 180, 44, 180, th.panel, th.fg, sw=2.0)
    for y in (floor - 158, floor - 98):
        s.rect(815, y, 14, 28, th.bg, th.muted, sw=1.4)
    s.text(828, floor - 192, "façade", 13, th.fg)
    out_x, out_y = 700.0, floor - 53.0
    # The reflection off the façade, which the reading is corrected for. It
    # leaves the activity above the microphone, so the outgoing leg clears the
    # windscreen, and meets the façade where the image construction puts it:
    # on the line from the source to the mirror image, in the face x = 806, of
    # the point where it reaches the windscreen.
    wall = 806.0
    start_x, start_y = 575.0, floor - 78.0
    end_x, end_y = out_x + 9.0, out_y - 2.0
    image_x = 2.0 * wall - end_x
    bounce_y = start_y + (end_y - start_y) * (wall - start_x) / (image_x - start_x)
    s.path(
        f"M {start_x} {start_y} L {wall} {bounce_y:.2f} L {end_x} {end_y}",
        stroke=th.secondary,
        sw=1.7,
        dash="6,4",
    )
    back = (end_x - wall, end_y - bounce_y)
    reach = (back[0] ** 2 + back[1] ** 2) ** 0.5
    s.arrow(
        end_x - 12.0 * back[0] / reach,
        end_y - 12.0 * back[1] / reach,
        end_x,
        end_y,
        th.secondary,
        1.7,
    )
    s.arrow(575, floor - 40, out_x - 13, out_y + 5.5, th.primary, 2.0)
    s.mic(out_x, out_y, floor, scale=0.85)
    s.circle(out_x, out_y + 5, 11, th.panel, th.fg, 1.3)
    outdoor = (
        (th.primary, "", "incident sound: the one assessed (Annex I A.4)"),
        (th.secondary, "6,4", "reflection off a façade: corrected out (A.3.2)"),
        ("", "", "microphone, in its windscreen, where the"),
        ("", "", "level is highest (A.3.4.2 b, A.3.5 d)"),
    )
    size = s.fit_size([row[2] for row in outdoor], [13, 12], 350)
    for k, (colour, dash, label) in enumerate(outdoor):
        y = floor + 28 + 18 * k
        if colour:
            s.line(480, y - 4.5, 504, y - 4.5, colour, 2.0, dash=dash)
        s.text(512, y, label, size, th.fg if colour else th.muted, anchor="start")

    # --- (c) the series of one noise phase ---------------------------------
    s.line(40, 404, 860, 404, th.muted, 1.0, dash="6,5")
    s.text(
        40,
        436,
        "(c) One noise phase: the series of A.3.4.2 b",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )
    base = 550.0
    s.arrow(60, base, 452, base, th.fg, 1.6)
    tops = (base - 68, base - 60, base - 76)
    centres = (98.0, 218.0, 338.0)
    highest = min(tops)
    for x, top in zip(centres, tops, strict=True):
        fill = th.primary if top == highest else th.muted
        s.rect(x - 8, top, 16, base - top, fill, rx=2)
        s.text(x, base + 18, "≥ 5 s", 12, th.fg)
    s.dim(centres[0], base + 44, centres[1], base + 44, "≥ 3 min", size=13)
    s.dim(centres[1], base + 44, centres[2], base + 44, "≥ 3 min", size=13)
    # The spread the three readings have to keep within.
    for y in (highest, max(tops)):
        s.line(78, y, 372, y, th.secondary, 1.0, dash="4,3")
    s.line(372, highest, 372, max(tops), th.secondary, 1.6)
    s.text(
        380,
        (highest + max(tops)) / 2 + 4.5,
        "≤ 6 dBA",
        13,
        th.secondary,
        anchor="start",
    )
    s.text(centres[2], highest - 10, "the result", 13, th.primary, bold=True)
    rules = (
        (
            "three readings of $L_{Keq,Ti}$ or more in each phase,",
            "5 s or longer each and 3 min or more apart",
        ),
        ("valid within 6 dBA; beyond it, three more",),
        (
            "one reading far from the rest: find its source",
            "and repeat up to five times with it running",
        ),
        ("the result is the highest reading",),
        ("background: the same with the activity stopped",),
    )
    size = s.fit_size([line for rule in rules for line in rule], [13, 12], 348)
    y = 468.0
    for rule in rules:
        s.circle(500, y - 4.5, 3.2, th.primary)
        for line in rule:
            s.text(512, y, line, size, th.fg, anchor="start")
            y += 18
        y += 5

    # --- the instrument and the weather -------------------------------------
    s.rect(40, 630, 820, 84, th.panel, th.fg, rx=6, sw=1.6)
    kit = (
        "type 1/class 1 sound level meter and calibrator, class 1 one-third-octave filters (Article 30)",
        "calibrator check before and after every measurement: within 0.3 dB of the initial reference value (A.3.5 c)",
        "outdoors: windscreen always, no measurement in rain, none with wind above 5 m/s (A.3.5 b, d)",
    )
    size = s.fit_size(kit, [13, 12, 11], 790)
    for k, line in enumerate(kit):
        s.text(56, 654 + 22 * k, line, size, th.fg, anchor="start")


def _d_soundscape_study(s: SVG, th: Theme) -> None:
    """What a soundscape study collects, and what the analysis makes of it.

    The collection is ISO/TS 12913-2:2018: the soundwalk with predefined
    assessment sites of C.2.3 (PDF page 18), the instructions of Method B in
    C.3.2.2 (page 23), the questionnaires of C.3.1 and C.3.2.3 to C.3.2.5
    (pages 19 to 25) and the binaural measurement of Annex D (pages 30 and
    31): the microphones 1.6 m ± 0.1 m above the ground and at least 1 m from
    reflecting structures (D.2), 3 min or longer (D.3), equalized for the
    sound field (D.4), a wind shield outdoors (D.5), 44.1 kHz or more (D.6).
    The analysis is ISO/TS 12913-3:2019, Annexes A, B and D (PDF pages 11 to
    19). The head is drawn where the participants stand and facing where they
    look, which is what C.3.2.2.2 asks of it; nothing here says when it
    records, because the specification does not.
    """
    # --- (a) the soundwalk, in plan ----------------------------------------
    s.text(
        40, 72, "(a) The soundwalk (C.2.3)", 15, th.primary, anchor="start", bold=True
    )
    for x, y, w, h in (
        (48, 92, 96, 34),
        (236, 88, 84, 56),
        (120, 176, 104, 52),
        (330, 184, 90, 44),
        (404, 92, 56, 34),
    ):
        s.rect(x, y, w, h, th.panel, th.muted, rx=3, sw=1.0)
    route = ((52, 160), (112, 148), (196, 136), (286, 172), (368, 148), (456, 152))
    d = f"M {route[0][0]} {route[0][1]}"
    for k in range(len(route) - 1):
        before = route[max(k - 1, 0)]
        here, there = route[k], route[k + 1]
        after = route[min(k + 2, len(route) - 1)]
        c1 = (
            here[0] + (there[0] - before[0]) / 6,
            here[1] + (there[1] - before[1]) / 6,
        )
        c2 = (there[0] - (after[0] - here[0]) / 6, there[1] - (after[1] - here[1]) / 6)
        d += f" C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {there[0]} {there[1]}"
    s.path(d, stroke=th.primary, sw=2.2, dash="7,5")
    for number, (x, y) in enumerate(route[1:5], start=1):
        s.circle(x, y, 11, th.primary, th.bg, 1.6)
        s.text(x, y + 4.5, str(number), 13, th.bg, bold=True)
    walk = (
        "the area and the assessment sites (1 to 4) are set beforehand",
        "a moderator leads groups of up to five, who walk in silence",
        "and all fill in the questionnaire at every site",
        "20 or more independent observations of each site",
    )
    size = s.fit_size(walk, [13, 12], 424)
    for k, line in enumerate(walk):
        s.text(40, 258 + 18 * k, line, size, th.fg, anchor="start")

    # --- (b) one assessment site, in elevation ------------------------------
    s.text(
        500,
        72,
        "(b) At each site (C.3.2.2, D.2)",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )
    ground = 232.0
    s.ground(ground, 500, 860)
    for x in (522, 550, 578):
        s.person(x, ground, 78)
    s.arrow(512, 134, 598, 134, th.accent, 1.6)
    s.text(555, 126, "viewing direction", 12, th.accent)
    # The artificial head on its tripod, the ear canal entrance 1.6 m up.
    head_x, ear_y = 652.0, ground - 74.0
    for foot in (-17.0, 0.0, 17.0):
        s.line(head_x, ground - 40, head_x + foot, ground, th.fg, 2.0)
    s.line(head_x, ground - 40, head_x, ear_y + 22, th.fg, 2.4)
    s.rect(head_x - 13, ear_y + 15, 26, 8, th.muted, rx=3)
    s.ellipse(head_x, ear_y, 9.5, 11.5, th.panel, th.fg, 1.8)
    s.path(
        f"M {head_x + 9} {ear_y - 3} L {head_x + 14} {ear_y + 3} L {head_x + 9} {ear_y + 4}",
        stroke=th.fg,
        sw=1.8,
    )
    s.circle(head_x, ear_y, 3.2, th.primary)
    s.line(head_x + 4, ear_y, head_x + 34, ear_y, th.muted, 0.9, dash="3,3")
    s.dim(
        head_x + 34,
        ground,
        head_x + 34,
        ear_y,
        "1.6 m ± 0.1 m",
        size=13,
        label_side="right",
    )
    s.rect(814, ground - 126, 46, 126, th.panel, th.fg, sw=2.0)
    s.text(860, ground - 134, "reflecting structure", 12, th.muted, anchor="end")
    s.dim(head_x + 14, ground - 104, 814, ground - 104, "≥ 1 m", size=13)
    site = (
        "the participants listen in silence for a set time,",
        "e.g. 3 min, then answer without leaving the spot",
        "artificial head on a tripod, facing where they look",
        "and not moved while it measures (C.3.2.2.2)",
    )
    size = s.fit_size(site, [13, 12], 360)
    for k, line in enumerate(site):
        s.text(500, 258 + 18 * k, line, size, th.fg, anchor="start")

    # --- (c) to (e): what each record is, and what is made of it ------------
    s.line(40, 332, 860, 332, th.muted, 1.0, dash="6,5")
    lanes = (
        (
            "(c) Method A (C.3.1)",
            "four parts, five boxes each:",
            (
                "1  sources heard (Figures C.2, C.3)",
                "2  eight attributes (Figure C.4)",
                "3  overall quality (Figure C.5)",
                "4  appropriateness (Figure C.6)",
            ),
            "Annex A",
            (
                ("scale values of each part (Table A.1)", "method_a_scale_values"),
                ("median and range per site (A.2)", "method_a_summary"),
                ("$P$ and $E$ (Formulas A.1 and A.2)", "pleasantness_eventfulness"),
                ("Spearman against the levels (A.4)", "spearman_rank_correlation"),
                ("every scale is ordinal (A.2)", ""),
            ),
        ),
        (
            "(d) Method B (C.3.2)",
            "the soundwalk sheet, in this order:",
            (
                "1  continuous scales (Figure C.7)",
                "2  sources, by rank (Figure C.8):",
                "    up to eight, the most noticeable first",
                "3  free comments (Figure C.9)",
            ),
            "Annex B",
            (
                ("value 1 to 5, to one decimal (B.2)", "method_b_scale_values"),
                ("mean, deviation, 95 % interval (B.2)", "method_b_summary"),
                ("median rank of each source (B.2)", "method_b_source_ranking"),
                ("Pearson against the levels (B.3)", "pearson_correlation"),
                ("comments: qualitative analysis (B.2)", ""),
            ),
        ),
        (
            "(e) Binaural recording (Annex D)",
            "two channels, one for each ear:",
            (
                "3 min or longer (D.3)",
                "44.1 kHz or more, uncompressed (D.6)",
                "wind shield outdoors (D.5)",
                "equalized for the sound field (D.4)",
            ),
            "Annex D",
            (
                ("each metric of Table D.1 at each ear:", "binaural_indicators"),
                ("levels, loudness, sharpness, tonality,", ""),
                ("roughness and fluctuation strength", ""),
                ("the higher of the two ears' values", ""),
                ("is the representative value (D.2)", ""),
                ("a percentile ratio such as $N_5$/$N_{95}$", ""),
                ("tells the variation over time (D.2)", ""),
            ),
        ),
    )
    quiet_lines = (
        "every scale is ordinal (A.2)",
        "comments: qualitative analysis (B.2)",
    )
    width, top, mid, card = 260.0, 384.0, 532.0, 172.0
    heads = s.fit_size([lane[0] for lane in lanes], [15, 14, 13], width, bold=True)
    body = s.fit_size(
        [
            line
            for lane in lanes
            for line in (lane[1], *lane[2], *(item[0] for item in lane[4]))
        ],
        [13, 12, 11],
        width - 30,
    )
    for k, (head, lead, parts, annex, items) in enumerate(lanes):
        left = 40.0 + 280 * k
        s.text(left, 362, head, heads, th.primary, anchor="start", bold=True)
        s.rect(left, top, width, 108, th.panel, th.fg, rx=6, sw=1.4)
        s.text(left + 14, top + 22, lead, body, th.muted, anchor="start")
        for row, line in enumerate(parts):
            # A line indented under an item carries on that item.
            indent = 18 if line.startswith(" ") else 0
            s.text(
                left + 14 + indent,
                top + 42 + 18 * row,
                line.strip(),
                body,
                th.fg,
                anchor="start",
            )
        s.arrow(left + 30, top + 108, left + 30, mid - 2, th.fg, 1.6)
        s.text(
            left + 44,
            (top + 108 + mid) / 2 + 4.5,
            f"ISO/TS 12913-3, {annex}",
            12,
            th.muted,
            anchor="start",
        )
        s.rect(left, mid, width, card, th.bg, th.primary, rx=6, sw=1.6)
        line_y = mid + 22
        for label, function in items:
            quiet = label in quiet_lines
            s.text(
                left + 14,
                line_y,
                label,
                body,
                th.muted if quiet else th.fg,
                anchor="start",
            )
            if function:
                s.text(
                    left + 14,
                    line_y + 15,
                    function,
                    11,
                    th.primary,
                    anchor="start",
                    mono=True,
                )
            line_y += 33 if function else 18
    # The levels the answers are correlated with come from the recording.
    bus = mid + card + 22
    s.line(40 + 2 * 280 + 130, mid + card, 40 + 2 * 280 + 130, bus, th.accent, 1.8)
    s.line(170, bus, 40 + 2 * 280 + 130, bus, th.accent, 1.8)
    for foot in (170.0, 450.0):
        s.arrow(foot, bus, foot, mid + card + 2, th.accent, 1.8)
    s.text(
        450,
        bus + 20,
        "the acoustic data the answers are set against (A.4, B.3)",
        13,
        th.accent,
    )


def _d_statistical_pass_by_site(s: SVG, th: Theme) -> None:
    # --- plan, 12 px per metre -------------------------------------------
    # Figure 3's two-lane road: the measuring lane on the roadside of
    # right-hand traffic, the microphone 7,5 m from its centre (8.1), and
    # 30 m of level, straight road on each side of it (6.1).
    rx0, rx1 = 50.0, 850.0
    mx = 450.0
    per_m = 12.0
    s.text(rx0, 64.0, "Plan, right-hand traffic", 17, th.fg, anchor="start", bold=True)
    shoulder, lane = 1.5 * per_m, 3.5 * per_m
    top = 118.0
    y_opp = top + shoulder
    y_mid = y_opp + lane
    y_near = y_mid + lane
    y_edge = y_near + shoulder
    centre = y_mid + lane / 2
    s.rect(rx0, top, rx1 - rx0, shoulder, th.bg, th.muted, sw=1.0)
    s.rect(rx0, y_edge - shoulder, rx1 - rx0, shoulder, th.bg, th.muted, sw=1.0)
    s.rect(rx0, y_opp, rx1 - rx0, 2 * lane, th.panel, th.muted, sw=1.2)
    s.line(rx0, y_mid, rx1, y_mid, th.muted, 1.6, dash="14,10")
    s.text(rx0 + 10, top + 14, "shoulder", 13, th.muted, anchor="start")
    s.text(rx0 + 10, y_edge - 4, "shoulder", 13, th.muted, anchor="start")
    s.text(rx0 + 10, y_opp + 27, "opposing lane", 15, th.fg, anchor="start")
    s.text(rx0 + 10, y_mid + 27, "measuring lane", 15, th.fg, anchor="start", bold=True)
    s.text(mx + 16, y_edge + 20, "roadside area", 13, th.muted, anchor="start")

    # One vehicle on its own, driving towards the microphone.
    cx0, cx1 = 300.0, 354.0
    s.rect(cx0, centre - 11, cx1 - cx0, 22, th.secondary, rx=6)
    s.arrow(cx1 + 8, centre, cx1 + 48, centre, th.secondary, 2.0)

    # The two microphone positions, both 7,5 m from the measuring lane.
    mic1 = centre + 7.5 * per_m
    mic2 = centre - 7.5 * per_m
    for my in (mic1, mic2):
        s.circle(mx, my, 7, th.primary)
    s.line(mx, mic2 + 7, mx, mic1 - 7, th.muted, 0.9, dash="3,3")
    s.dim(mx - 22, centre, mx - 22, mic1, "7.5 m", 0, 15)
    s.dim(mx - 22, centre, mx - 22, mic2, "7.5 m", 0, 15)
    s.line(mx - 30, centre, mx + 30, centre, th.muted, 0.9, dash="3,3")
    s.text(
        mx + 16,
        mic1 + 6,
        "microphone position 1",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )
    s.text(
        mx + 16,
        mic2 + 5,
        "position 2, when the near shoulder is unsuitable",
        15,
        th.primary,
        anchor="start",
    )

    # The test section, 30 m each way (50 m on a high-speed road).
    half = 30.0 * per_m
    s.dim(mx - half, y_edge, mx, y_edge, "≥ 30 m (50 m on a high-speed road)", 92, 15)
    s.dim(mx, y_edge, mx + half, y_edge, "≥ 30 m", 92, 15)
    s.text(
        rx0,
        y_edge + 124,
        "test section: level and straight, the surface homogeneous over it (6.1)",
        15,
        th.fg,
        anchor="start",
    )

    # --- section at the microphone, 40 px per metre ------------------------
    gy = 540.0
    sec_m = 40.0
    s.text(
        rx0, 424.0, "Section at the microphone", 17, th.fg, anchor="start", bold=True
    )
    s.text(
        rx0,
        450.0,
        "per isolated pass-by: category, speed $v$ and $L_{AFmax}$",
        15,
        th.fg,
        anchor="start",
    )
    s.ground(gy, rx0, rx1)
    lane_x = 380.0
    road_x0 = lane_x - 1.5 * 3.5 * sec_m
    road_x1 = lane_x + (3.5 / 2 + 1.5) * sec_m
    s.rect(road_x0, gy - 8, road_x1 - road_x0, 8, th.muted)
    # A car on the measuring lane (its size is not to scale).
    s.rect(lane_x - 55, gy - 34, 110, 16, th.secondary, rx=5)
    s.path(
        f"M {lane_x - 40} {gy - 34} L {lane_x - 26} {gy - 52} "
        f"L {lane_x + 22} {gy - 52} L {lane_x + 38} {gy - 34} Z",
        fill=th.secondary,
    )
    s.circle(lane_x - 32, gy - 16, 9, th.fg)
    s.circle(lane_x + 32, gy - 16, 9, th.fg)
    s.line(lane_x, gy - 62, lane_x, gy, th.muted, 0.9, dash="3,3")
    s.text(lane_x, gy - 70, "lane centre", 13, th.muted)

    mic_x = lane_x + 7.5 * sec_m
    cap = gy - 1.2 * sec_m
    s.mic(mic_x, cap, gy, 0.8)
    s.arrow(mic_x - 10, cap + 5, mic_x - 70, cap + 5, th.primary, 1.8)
    s.text(
        mic_x - 40, cap - 24, "axis horizontal, towards the vehicles", 15, th.primary
    )
    s.dim(mic_x, gy, mic_x, cap, "1.2 m ± 0.1 m", 56, 15, label_side="right")
    s.dim(lane_x, gy, mic_x, gy, "7.5 m ± 0.1 m", 30, 15)


# ---------------------------------------------------------------------------
# ISO 3095 pass-by site: the microphones and the free area (6.1.1, 6.4.1)
# ---------------------------------------------------------------------------


def _d_rolling_stock_site(s: SVG, th: Theme) -> None:
    # --- section across the track, 23 px per metre -------------------------
    # Figure 6: A at 7,5 m and 1,2 m above the top of rail, B at 7,5 m and
    # 3,5 m (6.4.2), C at 25 m and 3,5 m (6.4.1, 200 km/h and above).
    per_m = 23.0
    x0 = 130.0  # track centreline
    rail = 300.0  # top of rail
    gy = rail + 1.3 * per_m  # the ground, 1,3 m below the top of rail
    s.text(
        50.0,
        70.0,
        "Section across the track (6.4.1, Figure 6)",
        17,
        th.fg,
        anchor="start",
        bold=True,
    )
    # The band 6.1.1 allows the ground to lie in, 0 m to -2 m.
    band = 2.0 * per_m
    s.rect(x0 + 60, rail, 700, band, th.panel, th.muted, sw=0.8, dash="4,3")
    s.ground(gy, x0 + 60, x0 + 760)
    # Ballast, sleeper and the two rails, the gauge out of scale.
    s.path(
        f"M {x0 - 70} {gy} L {x0 - 44} {rail + 8} L {x0 + 44} {rail + 8} "
        f"L {x0 + 70} {gy} Z",
        fill=th.panel,
        stroke=th.muted,
        sw=1.4,
    )
    s.rect(x0 - 40, rail + 4, 80, 6, th.muted)
    for dx in (-17.0, 17.0):
        s.rect(x0 + dx - 4, rail - 2, 8, 7, th.fg)
    # The unit under test, a car body on its wheels.
    s.rect(x0 - 36, rail - 4.2 * per_m, 72, 3.3 * per_m, th.panel, th.fg, rx=10, sw=1.6)
    s.rect(x0 - 26, rail - 3.6 * per_m, 52, 0.8 * per_m, th.bg, th.muted, rx=3, sw=1.0)
    for dx in (-17.0, 17.0):
        s.circle(x0 + dx, rail - 9, 9, th.fg)
    s.line(x0, rail - 4.6 * per_m, x0, gy + 16, th.muted, 0.9, dash="3,3")
    s.text(x0, gy + 34, "track centreline", 13, th.muted)
    # The datum every height is measured from; it and the label under the
    # band stop at the band's right edge, clear of the canvas edge.
    s.line(x0 + 40, rail, x0 + 760, rail, th.secondary, 1.6, dash="9,5")
    # Between A and C, where the line is clear of every stand and dimension.
    s.text(x0 + 16.25 * per_m, rail - 8, "top of rail", 14, th.secondary)
    s.text(
        x0 + 755,
        rail + band + 18,
        "ground 0 m to −2 m relative to the top of rail (6.1.1)",
        13,
        th.muted,
        anchor="end",
    )

    xa = x0 + 7.5 * per_m
    xc = x0 + 25.0 * per_m
    ya = rail - 1.2 * per_m
    yb = rail - 3.5 * per_m
    s.mic(xa, ya, gy, 0.55)
    s.circle(xa, yb, 7, th.bg, th.primary, sw=2.0)
    s.mic(xc, yb, gy, 0.55)
    s.dim(xa, rail, xa, ya, "1.2 m", 26, 14, label_side="right")
    s.dim(xa, rail, xa, yb, "3.5 m", -26, 14, label_side="left")
    s.dim(xc, rail, xc, yb, "3.5 m", 26, 14, label_side="right")
    s.dim(x0, gy + 62, xa, gy + 62, "7.5 m", 0, 14)
    s.dim(x0, gy + 90, xc, gy + 90, "25 m", 0, 14)
    s.text(xa + 16, ya - 16, "A", 16, th.primary, anchor="start", bold=True)
    s.text(xa + 14, yb - 12, "B", 16, th.primary, anchor="start", bold=True)
    s.text(xc - 16, yb - 16, "C", 16, th.primary, anchor="end", bold=True)
    s.text(
        x0 + 250,
        120.0,
        "A: the standard position, both sides of the unit",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        x0 + 250,
        140.0,
        "B: added when sources sit high on the unit (6.4.2)",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        x0 + 250,
        160.0,
        "C: allowed instead of A at 200 km/h and above",
        14,
        th.fg,
        anchor="start",
    )

    # --- plan, not to scale: d, 2d and 3d as 6.1.1 and 6.2.1 set them ------
    s.text(
        50.0,
        470.0,
        "Plan: the free area around a microphone at distance $d$",
        17,
        th.fg,
        anchor="start",
        bold=True,
    )
    s.text(50.0, 494.0, "(6.1.1 and 6.2.1)", 14, th.muted, anchor="start")
    d = 50.0
    mx, my = 450.0, 680.0
    ty = my - d
    s.circle(mx, my, 3 * d, "none", th.muted, sw=1.2)
    s.path(
        f"M {mx} {my} L {mx - 2 * d} {ty} L {mx + 2 * d} {ty} Z",
        fill=th.panel,
        stroke=th.primary,
        sw=1.4,
    )
    s.line(60.0, ty, 840.0, ty, th.fg, 2.4)
    s.line(60.0, ty - 8, 840.0, ty - 8, th.fg, 1.2)
    # A train running along the track towards the microphone section.
    s.rect(96.0, ty - 16, 150.0, 16.0, th.secondary, rx=4)
    s.arrow(254.0, ty - 8, 300.0, ty - 8, th.secondary, 2.0)
    s.circle(mx, my, 7, th.primary)
    # Left of the triangle, where the label is clear of its edge and of the
    # circle; on the right the edge ran through the letter.
    s.dim(mx, ty, mx, my, "$d$", -90, 15, label_side="left")
    s.dim(mx - 2 * d, ty, mx, ty, "$2d$", -30, 15)
    s.dim(mx, ty, mx + 2 * d, ty, "$2d$", -30, 15)
    s.line(mx, my, mx + 3 * d * 0.8, my + 3 * d * 0.6, th.muted, 1.0, dash="4,3")
    s.text(mx + 96, my + 56, "$3d$", 15, th.muted, anchor="start")
    s.text(
        mx + 3 * d + 24,
        my + 20,
        "within $3d$: no barriers, hills,",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        mx + 3 * d + 24,
        my + 40,
        "rocks, bridges or buildings",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        50.0,
        878.0,
        "shaded: free propagation, nobody inside, no other track, no snow or tall "
        "vegetation,",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        50.0,
        898.0,
        "no water, ice, tarmac or concrete; the reference track is the same over "
        "$2d$ either side",
        14,
        th.fg,
        anchor="start",
    )


# ---------------------------------------------------------------------------
# IEC TS 61400-11-2: wind turbine noise at a dwelling
# ---------------------------------------------------------------------------


def _small_turbine(
    s: SVG, th: Theme, x: float, gy: float, hub_y: float, rr: float
) -> None:
    """A wind turbine seen from the side: tower, nacelle and the rotor edge-on."""
    s.path(
        f"M {x - 7:.0f} {gy:.0f} L {x - 3:.0f} {hub_y + 8:.0f} "
        f"L {x + 3:.0f} {hub_y + 8:.0f} L {x + 7:.0f} {gy:.0f} Z",
        fill=th.panel,
        stroke=th.fg,
        sw=1.5,
    )
    s.rect(x - 18, hub_y - 8, 36, 16, th.panel, th.fg, rx=4, sw=1.5)
    rx = x - 22
    s.ellipse(rx, hub_y, 6.0, rr, stroke=th.muted, sw=1.1, dash="5,4")
    s.line(rx, hub_y - 6, rx - 3, hub_y - rr + 3, th.fg, 2.6)
    s.line(rx, hub_y + 6, rx + 2, hub_y + rr - 3, th.fg, 2.6)
    s.circle(rx, hub_y, 4.5, th.fg)


def _d_wind_turbine_receptor(s: SVG, th: Theme) -> None:
    """IEC TS 61400-11-2: the microphone at the dwelling and the wind it is binned by.

    Read in IEC TS 61400-11-2:2024. The microphone stands away from any large
    reflecting surface but the ground, ideally five wavelengths of the lowest
    frequency of interest, typically 15 m to 20 m (8.1.1, PDF page 25,
    printed p. 23), free-field and inside a two-stage or oversize wind screen
    on a tripod or a pole (8.1.3, same page). The façade alternative is plane
    within ±0,05 m within 1 m of the microphone, with the edges of the façade
    more than 1 m away, the relevant turbines within 45° of its normal, and no
    use for tonal audibility, amplitude modulation or impulsivity (8.1.3,
    PDF pages 25 and 26, pp. 23 and 24). Wind and the turbines' power are
    sampled at 1 Hz or faster and averaged over 10 s to 10 min (9.2, PDF page
    26, p. 24); the binning wind speed comes from the power curve and the
    nacelle anemometer, recalculated to 10 m (9.3.2.1, PDF page 28, p. 26),
    or from a mast or remote sensing device with one height within ±40 % of
    the hub height and a second at least 15 m from it (9.3.2.3, same page).
    Temperature and humidity are read 1 m to 1.5 m above ground between the
    farm and the receptor (9.6, PDF page 31, p. 29). The bins are 1 m/s wide
    and 30° sectors from north, the downwind sector ±45° of the line from
    the turbines (10.1, same page), and the amplitude modulation analysis
    takes 100 ms one-third-octave L_Aeq from 20 Hz to 10 kHz, 10 s blocks
    and 10 min periods, with integer-centred speed bins (13.6.1, PDF page
    51, p. 49). The section is not to scale: the standard fixes the
    distances by rule.
    """
    s.text(
        450, 62, "In section, from the turbines to the dwelling", 15, th.fg, bold=True
    )
    gy = 330.0
    s.ground(gy, 30, 870)
    for x, hub_y, rr in ((96.0, 140.0, 56.0), (196.0, 152.0, 52.0)):
        _small_turbine(s, th, x, gy, hub_y, rr)
    s.text(
        34, gy + 28, "binning wind: power curve or nacelle", 12, th.fg, anchor="start"
    )
    s.text(
        34,
        gy + 44,
        "anemometer, recalculated to 10 m (9.3.2.1)",
        12,
        th.fg,
        anchor="start",
    )
    s.text(
        34,
        gy + 60,
        "sampled at 1 Hz or faster, averaged over 10 s to 10 min (9.2)",
        12,
        th.muted,
        anchor="start",
    )

    # The mast: one height near the hub, another 15 m from it.
    mx = 296.0
    s.line(mx, gy, mx, 128, th.fg, 2.0)
    for y in (140.0, 214.0):
        s.line(mx - 10, y, mx + 10, y, th.fg, 1.6)
        s.circle(mx - 10, y - 5, 3.6, th.panel, th.fg, 1.2)
        s.circle(mx + 10, y - 5, 3.6, th.panel, th.fg, 1.2)
    s.dim(mx + 26, 140, mx + 26, 214, "≥ 15 m", size=11, label_side="right")
    s.text(mx, 104, "mast or remote sensing", 12, th.fg)
    s.text(mx, 120, "one height within ±40 % of the hub", 11, th.muted)

    # Temperature and humidity between the farm and the receptor.
    wx = 420.0
    s.line(wx, gy, wx, gy - 30, th.fg, 1.8)
    s.rect(wx - 8, gy - 42, 16, 12, th.panel, th.fg, sw=1.2)
    s.text(wx, gy - 70, "temperature, humidity", 11, th.fg)
    s.text(wx, gy - 55, "1 m to 1.5 m up (9.6)", 11, th.fg)

    # The dwelling and its façade.
    hx0, hx1 = 684.0, 820.0
    s.rect(hx0, 226, hx1 - hx0, gy - 226, th.panel, th.fg, sw=1.8)
    s.path(
        f"M {hx0 - 8:.0f} 226 L {(hx0 + hx1) / 2:.0f} 178 L {hx1 + 8:.0f} 226 Z",
        fill=th.panel,
        stroke=th.fg,
        sw=1.8,
    )
    s.rect(hx0 + 46, 270, 22, 60, th.bg, th.fg, sw=1.2)
    s.text((hx0 + hx1) / 2, 170, "dwelling", 12, th.fg, bold=True)
    # Façade microphone.
    s.rect(hx0 - 9, 262, 9, 7, th.secondary, th.fg, rx=1.5, sw=1.0)
    s.text(hx0 - 14, 296, "microphone", 11, th.secondary, anchor="end")
    s.text(hx0 - 14, 311, "on the façade", 11, th.secondary, anchor="end")

    # The free-field microphone, in its wind screen, on a tripod.
    fx = 520.0
    my = 270.0
    s.line(fx, my + 10, fx, gy, th.fg, 1.8)
    s.line(fx, gy - 22, fx - 12, gy, th.fg, 1.4)
    s.line(fx, gy - 22, fx + 12, gy, th.fg, 1.4)
    s.circle(fx, my, 18.0, th.panel, th.primary, 1.6)
    s.circle(fx, my, 11.0, "none", th.primary, 1.2)
    s.rect(fx - 2.5, my - 4, 5, 10, th.fg, rx=1.2)
    s.text(fx, 202, "free field, inside a", 12, th.primary)
    s.text(fx, 218, "two-stage or oversize", 12, th.primary)
    s.text(fx, 234, "wind screen (8.1.3)", 12, th.primary)
    s.dim(fx, gy + 26, hx0, gy + 26, "", size=11)
    s.text((fx + hx0) / 2, gy + 50, "5 $λ$ of the lowest frequency,", 12, th.fg)
    s.text((fx + hx0) / 2, gy + 66, "typically 15 m to 20 m (8.1.1)", 12, th.fg)

    # ----- What the façade has to be -------------------------------------------
    s.text(
        450,
        422,
        "A façade microphone (8.1.3) only where the signal needs it:",
        13,
        th.fg,
        bold=True,
    )
    s.text(
        450,
        442,
        "plane within ±0.05 m within 1 m, edges more than 1 m away, the turbines "
        "within 45° of its normal",
        12,
        th.muted,
    )
    s.text(
        450,
        460,
        "and never for tonal audibility, amplitude modulation or impulsivity; a "
        "proxy location is of limited use for them (8.1.2)",
        12,
        th.muted,
    )

    # ----- The bins ------------------------------------------------------------
    rcx, rcy, rr = 110.0, 578.0, 56.0
    s.text(
        40, 498, "Binned by wind (10.1, 13.6.1)", 14, th.fg, anchor="start", bold=True
    )
    for k in range(12):
        a = math.radians(-90.0 + 15.0 + 30.0 * k)
        s.line(rcx, rcy, rcx + rr * math.cos(a), rcy + rr * math.sin(a), th.muted, 1.0)
    s.circle(rcx, rcy, rr, "none", th.fg, 1.4)
    s.circle(rcx, rcy, rr * 0.5, "none", th.muted, 1.0)
    s.text(rcx, rcy - rr - 6, "N", 12, th.fg, bold=True)
    tx_ = 190.0
    s.text(tx_, 530, "12 sectors 30° wide, the first", 12, th.fg, anchor="start")
    s.text(tx_, 548, "from 345° to 15°", 12, th.fg, anchor="start")
    s.text(tx_, 572, "1 m/s wide, integer centred:", 12, th.fg, anchor="start")
    s.text(tx_, 590, "5 m/s is 4.5 m/s to 5.5 m/s", 12, th.fg, anchor="start")
    s.text(tx_, 614, "downwind: the line from the", 12, th.muted, anchor="start")
    s.text(tx_, 632, "turbines ±45°", 12, th.muted, anchor="start")

    # ----- Amplitude modulation --------------------------------------------------
    col, cw, top = 500.0, 370.0, 488.0
    s.rect(col, top, cw, 156, th.panel, th.fg, rx=6, sw=1.4)
    s.text(
        col + cw / 2, top + 24, "Amplitude modulation (13.6.1)", 14, th.fg, bold=True
    )
    rows = (
        "100 ms $L_{Aeq}$ in one-third octaves,",
        "20 Hz to 10 kHz at least",
        "10 s blocks, 60 of them to a 10 min period",
        "wind referenced to 10 min averages",
        "free field only, not on the façade",
    )
    size = s.fit_size(rows, (12, 11), cw - 28)
    for k, txt in enumerate(rows):
        s.text(col + 14, top + 52 + 21 * k, txt, size, th.fg, anchor="start")
