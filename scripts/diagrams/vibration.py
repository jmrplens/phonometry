#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Diagrams of the vibration guides: structural paths and human exposure.

One subject: motion rather than pressure. The structural diagrams draw the
rigs that quantify how vibration enters, crosses and leaves a structure
(mobility, transfer stiffness, junctions), and the human diagrams draw the
measurement chains that judge the same motion as something a person is
exposed to.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .parts import (
    _accel,
    _accel_wall,
    _exciter,
    _motion_arrows,
    _plate_top,
    _plate_up,
    _rot_arrow,
    _spring_v,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .canvas import SVG, Theme


def _d_human_vibration(s: SVG, th: Theme) -> None:
    """Whole-body vibration measurement chain (ISO 2631-1 / ISO 8041-1)."""
    gy = 510.0
    # --- Left: a seated person on a vibrating seat, triaxial accelerometer ---
    s.ground(gy, 40, 350)
    # Seat: cushion, backrest and support leg.
    s.rect(118, 424, 132, 18, th.panel, th.fg, rx=4, sw=2)  # cushion
    s.rect(118, 336, 16, 90, th.panel, th.fg, rx=3, sw=2)  # backrest
    s.line(184, 442, 184, gy, th.fg, 2.4)  # pedestal
    # A wavy "vibration" arrow rising into the seat base.
    s.arrow(184, gy - 4, 184, 452, th.secondary, 2.4)
    s.text(184, gy - 12, "vibration input", 15, th.secondary, "middle", italic=True)
    s.person(178, gy, 176, seated=True)
    # Triaxial accelerometer at the seat/body interface with its x, y, z axes.
    ox, oy = 176.0, 420.0
    s.rect(ox - 9, oy - 8, 18, 16, th.secondary, th.fg, rx=2, sw=1.5)
    s.arrow(ox, oy - 8, ox, oy - 58, th.accent, 2.0)  # z (vertical)
    s.text(ox + 8, oy - 54, "$z$", 15, th.accent, "start", bold=True)
    s.arrow(ox + 9, oy, ox + 62, oy, th.accent, 2.0)  # x (fore-aft)
    s.text(ox + 66, oy + 5, "$x$", 15, th.accent, "start", bold=True)
    s.arrow(ox - 7, oy + 6, ox - 44, oy + 34, th.accent, 2.0)  # y (lateral)
    s.text(ox - 52, oy + 44, "$y$", 15, th.accent, "end", bold=True)
    s.text(150, gy + 34, "Seat/body interface", 15, th.fg, "middle")

    # --- Right: the vertical signal-processing chain ---
    # 348 px on "Limitación de banda + Wk / Wd", 317 px at the stage title
    # size against the 247 of its English twin.
    cx, bw, bh = 650.0, 348.0, 72.0
    x0 = cx - bw / 2
    chain = [
        (96.0, "Triaxial accelerometer", "$a_x , a_y , a_z$  (m/s²)"),
        (206.0, "Band limiting + Wk / Wd", "weighting (ISO 8041-1)"),
        (316.0, "Weighted r.m.s. $a_w$  &  VDV", "(ISO 2631-1)"),
    ]
    for by, l1, l2 in chain:
        s.rect(x0, by, bw, bh, th.panel, th.primary, rx=12, sw=2)
        s.text(cx, by + 31, l1, 18, th.fg, "middle", bold=True)
        s.text(cx, by + 56, l2, 15, th.muted, "middle")
    s.arrow(cx, 168, cx, 206, th.fg, 2.0)
    s.arrow(cx, 278, cx, 316, th.fg, 2.0)
    # Feed the setup into the chain.
    s.arrow(252, oy, x0 - 6, 132, th.fg, 2.0)

    # --- Bottom: dominant axis, daily exposure and the Directive assessment ---
    # The Directive's whole-body A(8) is based on the HIGHEST frequency-
    # weighted axis value (1,4 a_wx, 1,4 a_wy, a_wz), Annex Part B point 1 -
    # not on the ISO 2631-1 Eq. (10) vector total a_v.
    s.arrow(cx, 388, cx, 424, th.fg, 2.0)
    s.rect(400, 424, 470, 78, "none", th.secondary, rx=12, sw=2, dash="6,5")
    s.text(
        635,
        452,
        "$A(8) = max(1.4·a_{wx} , 1.4·a_{wy} , a_{wz})·√(T/T_0)$",
        17,
        th.fg,
        "middle",
        bold=True,
    )
    s.text(
        635,
        480,
        "assessed vs EAV / ELV (Directive 2002/44/EC)",
        15,
        th.secondary,
        "middle",
    )


def _d_multiple_shock(s: SVG, th: Theme) -> None:
    """Multiple-shock spinal-response dose and injury risk (ISO 2631-5:2018)."""
    cx = 450.0
    bw, bh = 660.0, 58.0
    x0 = cx - bw / 2

    # --- Input --------------------------------------------------------------
    s.rect(x0, 48, bw, bh, th.panel, th.fg, rx=10, sw=2)
    s.text(
        cx, 72, "Vertical seat acceleration  $a_{z}(t)$", 16, th.fg, "middle", bold=True
    )
    s.text(
        cx,
        92,
        "conditioned per 5.1.3:  HP 0.01 Hz (2nd order) / LP 80 Hz (4th order)",
        11,
        th.muted,
        "middle",
    )
    s.arrow(cx, 106, cx, 136, th.fg, 1.8)
    s.text(
        cx - 26,
        128,
        "not the ISO 2631-1 0.4 Hz / 100 Hz filters",
        10,
        th.secondary,
        "end",
    )

    def _step(y: float, l1: str, l2: str, color: str) -> None:
        s.rect(x0, y, bw, bh, th.panel, color, rx=10, sw=2)
        s.text(cx, y + 25, l1, 15, th.fg, "middle", bold=True)
        s.text(cx, y + 45, l2, 11, th.muted, "middle")

    _step(
        136,
        "Spinal response  $A_{z}(t)$  (clause 5.2, Formula 1/2)",
        "seat-to-spine transfer function $H(f)$: 1 zero, 6 poles",
        th.primary,
    )
    _step(
        224,
        "Acceleration dose  $D_z = 1.07·(Σ A_{z,i}^6)^{1/6}$  (Formula 3)",
        "$A_{z,i}$ = positive peaks;   daily dose $D_{zd} = D_z·(t_d/t_m)^{1/6}$",
        th.fg,
    )
    _step(
        312,
        "Compressive stress  $S_d = m_z·D_{zd}$  (Annex C, Formula C.1)",
        "$m_z$ = 0.029 (male) / 0.025 (female) MPa per m/s²",
        th.fg,
    )
    # PARKED (controller adjudication): ISO 2631-5:2018(E) prints the
    # descriptive subscripts of S_stat and S_age in roman (PDF page 24,
    # folio 18: S_stat,i and S_age beside italic indices), but "stat" and
    # "age" are not in _ROMAN_SCRIPTS and the sibling descriptors u/d of
    # S_u/S_d are single letters the list cannot take; composing part of
    # the pair would split one formula into two subscript styles.
    _step(
        400,
        "Stress variable  R = [Σ (Sd·N^(1/6) / (Su − Sstat))^6]^(1/6)",
        "Su = 6.75 − Sage·(b+i) MPa, cumulated over exposure years (C.3/C.4)",
        th.secondary,
    )
    for y0, y1 in ((196, 224), (284, 312), (372, 400), (460, 488)):
        s.arrow(cx, y0, cx, y1, th.fg, 1.8)

    # --- Output -------------------------------------------------------------
    s.rect(x0, 488, bw, 58, "none", th.primary, rx=10, sw=2.4)
    s.text(
        cx,
        513,
        "Injury probability  $P(R) = 1 − exp(−(R/α)^β)$  (Formula C.5)",
        15,
        th.fg,
        "middle",
        bold=True,
    )
    s.text(
        cx,
        533,
        "Weibull risk of lumbar injury, by sex (Table C.1/C.2)",
        11,
        th.muted,
        "middle",
    )


def _d_hand_arm_vibration(s: SVG, th: Theme) -> None:
    """Where the accelerometer goes on a tool, and what the reading becomes.

    ISO 5349-2 clause 6.1.3 (location), 6.1.4/6.1.5 (mounting and mass),
    6.2.3 (cable) and clause 8 (the daily exposure), on the chain-saw front
    handle the guide's worked example is measured at.
    """
    # --- Left: the tool handle, the hand and the transducer positions -------
    s.text(258, 74, "On the tool (ISO 5349-2, 6.1.3)", 15, th.fg, "middle", bold=True)
    bar_y, bar_h = 200.0, 26.0  # a Ø 30 mm handle tube
    bar_top, bar_bot = bar_y - bar_h / 2, bar_y + bar_h / 2
    s.rect(60, bar_top, 400, bar_h, th.panel, th.fg, rx=13, sw=2)

    # The hand: palm above the tube, four fingers curling under it.
    hand_x0, hand_x1 = 230.0, 330.0
    s.rect(hand_x0, 148, hand_x1 - hand_x0, bar_y - 148, th.muted, th.fg, rx=14, sw=1.6)
    for fx in (236.0, 259.0, 282.0, 305.0):
        s.rect(fx, bar_bot + 4, 19, 34, th.muted, th.fg, rx=9, sw=1.4)
    s.line(254, 156, 188, 92, th.muted, 15)
    s.dim(hand_x0, 272, hand_x1, 272, "gripping zone ≈ 100 mm", size=12)

    # The transducer positions of 6.1.3, in the order the clause prefers them.
    def _pos(x: float, *, under: bool, tag: str, cy: float) -> None:
        top = bar_bot if under else bar_top - 19
        s.rect(x - 12, top, 24, 19, th.secondary, th.fg, rx=3, sw=1.5)
        s.circle(x, cy, 12, th.secondary, th.bg, 2)
        s.text(x, cy + 5, tag, 14, th.bg, "middle", bold=True)

    _pos(x=280, under=True, tag="1", cy=174)
    _pos(x=196, under=False, tag="2", cy=148)
    _pos(x=372, under=False, tag="2", cy=148)
    _pos(x=372, under=True, tag="3", cy=253)

    s.text(520, 100, "chain-saw front handle,", 13, th.muted, "end")
    s.text(520, 118, "Ø 30 mm tube", 13, th.muted, "end")
    s.line(455, 126, 455, bar_top - 4, th.muted, 1.2, dash="4,4")

    # The cable, taped to the vibrating surface near the transducer (6.2.3).
    s.path(
        f"M 378 {bar_bot + 19} L 432 246 L 432 306 L 110 306", stroke=th.primary, sw=2.0
    )
    for tx in (170.0, 250.0):
        s.rect(tx, 300, 12, 12, th.primary, th.fg, rx=2, sw=1.0)
    s.text(
        110,
        330,
        "cable taped to the handle near the transducer (6.2.3)",
        12,
        th.primary,
        "start",
    )

    # Grip force: one of the two applied forces clause 9 asks the report for.
    s.arrow(306, 110, 306, 146, th.accent, 2.2)
    s.arrow(210, 250, 210, 218, th.accent, 2.2)
    s.text(306, 102, "grip force", 13, th.accent, "middle")

    s.text(
        45,
        366,
        "1  middle of the gripping zone, under the hand",
        13,
        th.fg,
        "start",
        bold=True,
    )
    s.text(
        62,
        385,
        "the most representative location; needs an adaptor",
        13,
        th.muted,
        "start",
    )
    s.text(
        45,
        410,
        "2  either side of the hand: usual practice",
        13,
        th.fg,
        "start",
        bold=True,
    )
    s.text(
        62, 429, "on a side handle, average the two positions", 13, th.muted, "start"
    )
    s.text(
        45,
        454,
        "3  underside of the handle, next to the hand",
        13,
        th.fg,
        "start",
        bold=True,
    )
    s.text(
        45,
        480,
        "grip and push force change the reading: report the",
        12,
        th.muted,
        "start",
    )
    s.text(
        45,
        497,
        "posture and the applied forces (7.1, clause 9 g))",
        12,
        th.muted,
        "start",
    )

    # The basicentric frame the three axes are reported in.
    # PARKED (controller adjudication): ISO 5349-1:2001(E) prints the h
    # subscript of the basicentric axes in roman (Figure 1 and its NOTE,
    # PDF page 10, folio 4: italic x/y/z with roman h, like the roman
    # hw/hv the curated list already carries), but a lone "h" cannot enter
    # _ROMAN_SCRIPTS without setting every legitimate h index upright, and
    # the italic default would put the same letter in two styles beside
    # the composed a_hv/a_hwx chain of this very diagram.
    ox, oy = 110.0, 578.0
    s.arrow(ox, oy, ox + 74, oy, th.primary, 2.2)
    s.text(ox + 80, oy + 5, "y_h", 15, th.primary, "start", bold=True)
    s.arrow(ox, oy, ox, oy - 46, th.primary, 2.2)
    s.text(ox, oy - 54, "z_h", 15, th.primary, "middle", bold=True)
    s.arrow(ox, oy, ox - 40, oy + 28, th.primary, 2.2)
    s.text(ox - 46, oy + 40, "x_h", 15, th.primary, "end", bold=True)
    s.text(236, 534, "basicentric frame (ISO 5349-1 Fig. 1):", 12, th.fg, "start")
    s.text(236, 552, "rotated so that y_h lies along the", 12, th.fg, "start")
    s.text(236, 570, "handle axis. All three axes are", 12, th.fg, "start")
    s.text(236, 588, "measured, and every $k = 1$.", 12, th.fg, "start")

    # --- Right: what the three axis magnitudes become -----------------------
    cx, bw, bh = 705.0, 320.0, 66.0
    x0 = cx - bw / 2
    chain = (
        (
            90.0,
            "$a_{hwx} , a_{hwy} , a_{hwz}$",
            "Wh-weighted, one per axis (ISO 5349-1 A.1)",
            th.primary,
        ),
        (
            176.0,
            "$a_{hv} = √(a_{hwx}^2 + a_{hwy}^2 + a_{hwz}^2)$",
            "vibration total value (Eq. (1))",
            th.fg,
        ),
        (
            262.0,
            "$A_{i}(8) = a_{hv,i} · √(T_i / T_0)$",
            "$T_i$ is total contact time per day (5.5)",
            th.fg,
        ),
        (
            348.0,
            "$A(8) = √(Σ A_{i}(8)^2)$",
            "one per hand, two significant figures (clause 8)",
            th.secondary,
        ),
    )
    for by, l1, l2, colour in chain:
        s.rect(x0, by, bw, bh, th.panel, colour, rx=12, sw=2)
        s.text(cx, by + 28, l1, 15, th.fg, "middle", bold=True)
        s.text(cx, by + 50, l2, 12, th.muted, "middle")
    for y0, y1 in ((156, 176), (242, 262), (328, 348), (414, 438)):
        s.arrow(cx, y0, cx, y1, th.fg, 1.8)
    s.rect(x0, 438, bw, 62, "none", th.secondary, rx=12, sw=2.4, dash="6,5")
    s.text(cx, 464, "EAV 2.5 m/s²   ·   ELV 5 m/s²", 16, th.fg, "middle", bold=True)
    s.text(cx, 486, "Directive 2002/44/EC, Article 3", 12, th.muted, "middle")

    # --- Bottom: the four acquisition rules that decide the reading ---------
    s.rect(524, 518, 336, 130, th.panel, th.muted, rx=12, sw=1.6)
    rules = (
        "transducer and mount below 5 % of the",
        "mass they are fixed to (6.1.5)",
        "linear averaging over complete work",
        "cycles (6.1.11)",
        "three samples per operation, a minute",
        "of record, none under 8 s (5.4.1)",
        "the lowest input range that does not",
        "overload, found by trial (6.1.10)",
    )
    for i, rule in enumerate(rules):
        if i % 2 == 0:
            s.circle(542, 540 + 14 * i - 5, 3.4, th.secondary)
        s.text(556, 540 + 14 * i, rule, 12, th.fg, "start")


def _d_iso2631_5_setup(s: SVG, th: Theme) -> None:
    """Getting the record ISO 2631-5 works on (clauses 5.1.2 and 5.1.4)."""
    import math

    # --- Left: the seat pan in section, with the ISO 10326-1 disc on it -----
    s.text(250, 78, "The seat pan, in section", 15, th.fg, "middle", bold=True)
    s.rect(200, 105, 92, 76, th.muted, th.fg, rx=26, sw=1.6)  # pelvis
    s.ellipse(224, 188, 24, 13, th.muted, th.fg, 1.6)  # tuberosity
    s.ellipse(268, 188, 24, 13, th.muted, th.fg, 1.6)  # tuberosity
    s.rect(150, 200, 220, 40, th.panel, th.fg, rx=9, sw=2)  # cushion
    s.rect(150, 240, 220, 12, th.panel, th.fg, sw=2)  # seat pan
    s.rect(150, 116, 16, 84, th.panel, th.fg, rx=4, sw=2)  # backrest
    _spring_v(s, 262, 252, 300, th.fg)
    s.ground(300, 130, 396)
    s.text(262, 322, "suspension travel", 12, th.muted, "middle")

    # The ISO 10326-1 mounting disc, edge on, taped to the cushion.
    s.rect(206, 191, 80, 9, th.secondary, th.fg, rx=4, sw=1.5)
    s.rect(234, 192.5, 24, 6, th.panel, th.fg, rx=1.5, sw=1.0)
    s.arrow(300, 190, 300, 128, th.accent, 2.4)
    s.text(308, 138, "$z$ +", 15, th.accent, "start", bold=True)
    s.rect(186, 190, 15, 11, th.primary, th.fg, rx=2, sw=1.2)
    s.line(186, 196, 128, 196, th.primary, 1.8)
    s.circle(124, 196, 4, th.primary)

    notes = (
        (True, "semi-rigid mounting disc Ø 250 ± 50 mm, height ≤ 12 mm,"),
        (False, "80-90 durometer (A), carrying a Ø 75 ± 5 mm × 1.5 mm"),
        (False, "metal disc for the accelerometers (ISO 10326-1, 5.2.3)"),
        (True, "taped to the cushion so the accelerometers sit midway"),
        (False, "between the ischial tuberosities (5.1.2)"),
        (True, "$z$ is positive to cranial: the method is about"),
        (False, "compressive spinal loading (5.1.3, first step)"),
        (True, "a contact switch or video detects loss of contact,"),
        (False, "which is reported and excluded from the exposure"),
    )
    for i, (bullet, line) in enumerate(notes):
        y = 356 + 17 * i
        if bullet:
            s.circle(50, y - 5, 3.4, th.secondary)
        s.text(64, y, line, 12, th.fg, "start")

    # --- Right: what the record then looks like -----------------------------
    ax0, ax1, base = 500.0, 862.0, 306.0
    s.text(
        681,
        78,
        "The record, split where contact is lost",
        15,
        th.fg,
        "middle",
        bold=True,
    )
    for i, line in enumerate(
        (
            "accelerations recorded while contact is lost",
            "shall not be counted as exposure, and the",
            "landing impact after a free fall shall be (5.1.2)",
        )
    ):
        s.text(681, 110 + 18 * i, line, 12, th.secondary, "middle")
    gaps = ((0.30, 0.40), (0.66, 0.72))
    for lo, hi in gaps:
        s.rect(
            ax0 + lo * (ax1 - ax0),
            base - 92,
            (hi - lo) * (ax1 - ax0),
            184,
            th.panel,
            th.secondary,
            sw=1.4,
            dash="5,4",
        )
    pts = []
    for i in range(0, 363, 2):
        u = i / 362.0
        v = 16.0 * math.sin(2.0 * math.pi * 5.0 * u) + 6.0 * math.sin(
            2.0 * math.pi * 13.0 * u + 1.0
        )
        for centre, amp in ((0.17, 62.0), (0.52, 44.0), (0.88, 78.0)):
            d = u - centre
            if 0.0 <= d < 0.2:
                v += amp * math.exp(-46.0 * d) * math.sin(2.0 * math.pi * 26.0 * d)
        for lo, hi in gaps:
            if lo <= u < hi:
                v = -34.0
        pts.append(f"{ax0 + u * (ax1 - ax0):.1f} {base - v:.1f}")
    s.path("M " + " L ".join(pts), stroke=th.primary, sw=1.8)
    s.line(ax0, base, ax1, base, th.fg, 1.4)
    s.text(ax0 - 8, base + 5, "0", 13, th.muted, "end")
    for lo, hi in gaps:
        s.text(
            ax0 + 0.5 * (lo + hi) * (ax1 - ax0),
            base - 100,
            "no contact",
            12,
            th.secondary,
            "middle",
        )
    s.text(ax0, base + 118, "$a_{z}(t)$, conditioned per 5.1.3", 12, th.muted, "start")
    segments = (
        (0.0, 0.30, "segment 1"),
        (0.40, 0.66, "segment 2"),
        (0.72, 1.0, "segment 3"),
    )
    for lo, hi, label in segments:
        xa, xb = ax0 + lo * (ax1 - ax0), ax0 + hi * (ax1 - ax0)
        s.line(xa, base + 138, xb, base + 138, th.accent, 3.0)
        s.text(0.5 * (xa + xb), base + 160, label, 12, th.accent, "middle")
    s.text(
        681,
        base + 186,
        "each segment is conditioned separately (5.1.3, second step)",
        12,
        th.fg,
        "middle",
    )

    # --- Bottom: the hardware and duration requirements ---------------------
    s.rect(40, 518, 820, 74, th.panel, th.muted, rx=12, sw=1.6)
    rules = (
        (
            "flat acceleration response from 0.01 Hz to at least 80 Hz, and "
            "256 samples per second or more (5.1.2)"
        ),
        (
            "equipment adequate for the highest amplitude anticipated; "
            "equipment and calibration method reported (5.1.2)"
        ),
        (
            "long enough to be representative: a complete work cycle for a "
            "repeatable task, longer where terrain varies (5.1.4)"
        ),
    )
    for i, rule in enumerate(rules):
        s.circle(62, 542 + 21 * i - 5, 3.4, th.secondary)
        s.text(76, 542 + 21 * i, rule, 12, th.fg, "start")


# ---------------------------------------------------------------------------
# Machine fault kinematics and the condition-monitoring rig (Norton 8.4)
# ---------------------------------------------------------------------------


def _d_fault_kinematics(s: SVG, th: Theme) -> None:
    """Where the fault frequencies come from: the bearing in end section and
    in axial half-section (where the contact angle lives), the gear pair and
    the ducted fan's rotating lobe pattern.
    """
    import math

    # ===== Panel 1: rolling-contact bearing, end section ====================
    cx, cy = 200.0, 262.0
    mm = 4.4  # 1 mm of the real bearing
    r_pitch, r_ball = 17.0 * mm, 3.0 * mm  # D = 34 mm, d = 6 mm
    r_out_i, r_out_o = r_pitch + r_ball, r_pitch + r_ball + 17.0
    r_in_o, r_in_bore = r_pitch - r_ball, r_pitch - r_ball - 26.0
    s.text(cx, 74, "1. Bearing: end section", 18, th.fg, bold=True)
    s.circle(cx, cy, r_out_o, th.panel, th.fg, 2.0)
    s.circle(cx, cy, r_out_i, "none", th.fg, 2.0)
    s.circle(cx, cy, r_in_o, th.panel, th.fg, 2.0)
    s.circle(cx, cy, r_in_bore, th.bg, th.fg, 2.0)
    s.circle(cx, cy, r_pitch, "none", th.muted, 1.1)
    for k in range(15):  # Z = 15 rolling elements
        a = math.radians(k * 24.0 - 90.0)
        s.circle(
            cx + r_pitch * math.cos(a),
            cy + r_pitch * math.sin(a),
            r_ball,
            th.bg,
            th.primary,
            1.8,
        )
    # The pitch diameter, dimensioned between two opposite element centres.
    s.arrow(cx - 6, cy, cx - r_pitch, cy, th.muted, 1.3)
    s.arrow(cx + 6, cy, cx + r_pitch, cy, th.muted, 1.3)
    # The halo is cut to the label it hides the raceway for, which in
    # Spanish is 147 px and in English 122; a fixed 148 fits one of them.
    halo = s.text_width("$D$ = 34 mm (pitch)", 13) + 16.0
    s.rect(cx - halo / 2, cy - 25, halo, 21, th.panel)
    s.text(cx, cy - 9, "$D$ = 34 mm (pitch)", 13, th.fg)
    # One element dimensioned, with a leader out of the drawing.
    bax = cx + r_pitch * math.cos(math.radians(38.0))
    bay = cy + r_pitch * math.sin(math.radians(38.0))
    s.line(bax + r_ball * 0.7, bay + r_ball * 0.7, 352, 352, th.muted, 1.0, dash="3,3")
    s.text(358, 358, "$d$ = 6 mm", 14, th.fg, anchor="start")
    # The spall on the stationary outer race, at the top of the load zone.
    for da in (-26.0, -13.0, 0.0, 13.0, 26.0):
        a = math.radians(-90.0 + da)
        s.line(
            cx + r_out_i * math.cos(a),
            cy + r_out_i * math.sin(a),
            cx + (r_out_i - 14.0) * math.cos(a),
            cy + (r_out_i - 14.0) * math.sin(a),
            th.secondary,
            2.2,
        )
    s.text(cx, 116, "spall on the outer race", 14, th.secondary)
    s.text(cx, 136, "BPFO = 207.0 Hz: one impact per pass", 12, th.secondary)
    # Which race turns, and the cage rate that follows from it.
    _rot_arrow(s, cx, cy, r_in_bore - 9.0, 20.0, 160.0, th.accent, 2.0)
    s.text(cx, cy + r_out_o + 34, "inner race turns at $f_s$ = 33.33 Hz,", 13, th.fg)
    s.text(cx, cy + r_out_o + 56, "outer race stationary", 13, th.fg)
    s.text(cx, cy + r_out_o + 82, "cage FTF = 13.8 Hz = 0.41 $f_s$", 13, th.accent)

    # ===== Panel 2: axial half-section, where the contact angle lives =======
    ax0, axy = 560.0, 250.0
    s.text(690, 74, "2. Bearing: axial half-section", 18, th.fg, bold=True)
    s.line(ax0 - 40, axy + 128, 880, axy + 128, th.muted, 1.4, dash="14,5,3,5")
    s.text(ax0 - 36, axy + 148, "bearing axis", 12, th.muted, anchor="start")
    # Outer ring, ball and inner ring in section, stacked off the axis.
    s.rect(ax0 + 40, axy - 92, 220, 44, th.panel, th.fg, sw=2.0)
    s.text(ax0 + 92, axy - 64, "outer ring", 13, th.fg)
    s.rect(ax0 + 40, axy + 48, 220, 44, th.panel, th.fg, sw=2.0)
    s.text(ax0 + 92, axy + 76, "inner ring", 13, th.fg)
    bx, by = ax0 + 168.0, axy
    s.circle(bx, by, 36, th.bg, th.primary, 2.0)
    # The radial plane (perpendicular to the axis) and the contact line.
    s.line(bx, by - 76, bx, by + 76, th.muted, 1.2, dash="5,4")
    s.text(bx - 10, by + 108, "radial plane", 12, th.muted, anchor="end")
    phi = math.radians(12.96)
    dx, dy = 74.0 * math.sin(phi), 74.0 * math.cos(phi)
    s.line(bx - dx, by + dy, bx + dx, by - dy, th.secondary, 2.4)
    s.text(690, 136, "contact line,  $φ$ = 12.96°", 14, th.secondary)
    s.path(
        f"M {bx:.1f} {by - 50:.1f} A 50 50 0 0 0 "
        f"{bx + 50 * math.sin(phi):.1f} {by - 50 * math.cos(phi):.1f}",
        stroke=th.secondary,
        sw=1.6,
    )
    s.text(
        690,
        axy + 186,
        "the contact angle exists only in this view: measured",
        13,
        th.muted,
    )
    s.text(
        690,
        axy + 206,
        "from the radial plane: $φ = 0$ for a deep-groove bearing",
        13,
        th.muted,
    )
    s.text(
        690,
        axy + 226,
        "and $φ > 0$ for angular-contact and tapered-roller types",
        13,
        th.muted,
    )

    # ===== Panel 3: gear pair in elevation ==================================
    gy = 596.0
    s.text(200, 500, "3. Gear pair", 18, th.fg, bold=True)
    for gcx, gr, teeth in ((110.0, 52.0, 28), (240.0, 78.0, 42)):
        s.circle(gcx, gy, gr, th.panel, th.fg, 2.0)
        s.circle(gcx, gy, gr * 0.22, th.bg, th.fg, 1.6)
        for k in range(teeth):
            a = 2.0 * math.pi * k / teeth
            s.line(
                gcx + gr * math.cos(a),
                gy + gr * math.sin(a),
                gcx + (gr + 8) * math.cos(a),
                gy + (gr + 8) * math.sin(a),
                th.fg,
                1.6,
            )
    # The chipped tooth, on the pinion, at the mesh line.
    s.circle(162.0, gy, 9.0, "none", th.secondary, 2.4)
    s.line(160, gy + 9, 108, 672, th.muted, 1.0, dash="3,3")
    s.text(64, 690, "chipped tooth", 13, th.secondary, anchor="start")
    s.text(336, 574, "28-tooth pinion on a", 13, th.fg, anchor="start")
    s.text(336, 594, "1500 r/min shaft:", 13, th.fg, anchor="start")
    s.text(336, 616, "$f_s$ = 25 Hz", 13, th.muted, anchor="start")

    # ===== Panel 4: ducted axial fan seen along the duct axis ===============
    fcx, fcy, fr = 690.0, 596.0, 80.0
    s.text(690, 500, "4. Ducted axial fan", 18, th.fg, bold=True)
    s.circle(fcx, fcy, fr, "none", th.fg, 2.4)
    s.circle(fcx, fcy, 20, th.panel, th.fg, 2.0)
    for k in range(4):  # V = 4 stator vanes, behind
        a = math.radians(45.0 + k * 90.0)
        s.line(
            fcx + 22 * math.cos(a),
            fcy + 22 * math.sin(a),
            fcx + fr * math.cos(a),
            fcy + fr * math.sin(a),
            th.muted,
            3.0,
            dash="7,5",
        )
    for k in range(6):  # N = 6 rotor blades, solid
        a = math.radians(k * 60.0)
        s.line(
            fcx + 20 * math.cos(a),
            fcy + 20 * math.sin(a),
            fcx + (fr - 6) * math.cos(a),
            fcy + (fr - 6) * math.sin(a),
            th.primary,
            4.4,
        )
    _rot_arrow(s, fcx, fcy, fr + 15.0, -62.0, 28.0, th.accent, 2.0)
    s.text(fcx + fr + 24, fcy + 6, "$N f_s$", 13, th.accent, anchor="start")
    s.text(690, fcy + 104, "6 blades (solid), 4 vanes (dashed)", 13, th.fg)

    # ===== What the two lower panels are for ================================
    s.text(
        450,
        730,
        "$GMF = N f_s = 28 × 25$ = 700 Hz, and a chipped tooth "
        "modulates it once per revolution: sidebands at $± f_s$",
        14,
        th.fg,
    )
    s.text(
        450,
        758,
        "$m_L = n·N ± k·V = 6 ± 4$ → 2 or 10 lobes, turning at "
        "$n·N·f_s/m_L$ = 175 or 35 Hz: the faster radiates much "
        "more",
        14,
        th.fg,
    )


def _d_machine_diagnostics(s: SVG, th: Theme) -> None:
    """Condition-monitoring measurement on a motor-gearbox train: where the
    accelerometers go, how they are mounted, and what the analyser records.
    """
    gy = 262.0  # top of the baseplate
    shaft_y = 222.0

    # --- The machine train on its baseplate ---------------------------------
    s.rect(110, gy, 460, 18, th.panel, th.fg, sw=2.0)
    s.ground(gy + 18, 110, 570)
    s.rect(130, 182, 136, 80, th.panel, th.fg, rx=6, sw=2.2)
    s.text(198, 228, "motor", 16, th.fg, bold=True)
    s.rect(390, 172, 148, 90, th.panel, th.fg, rx=6, sw=2.2)
    s.text(464, 224, "gearbox", 16, th.fg, bold=True)
    s.line(60, shaft_y, 130, shaft_y, th.fg, 3.0)  # non-drive end
    s.line(266, shaft_y, 390, shaft_y, th.fg, 3.0)  # drive shaft
    s.rect(316, shaft_y - 12, 26, 24, th.panel, th.fg, rx=3, sw=1.8)
    s.text(329, shaft_y + 34, "coupling", 12, th.muted)
    for hx in (282.0, 374.0):  # bearing housings
        s.rect(hx - 16, shaft_y - 18, 32, 36, th.bg, th.fg, rx=4, sw=1.8)

    # --- Where the accelerometers go ---------------------------------------
    for hx in (282.0, 374.0):
        _accel(s, hx, shaft_y - 18)
    s.rect(538, 196, 15, 16, th.secondary, th.fg, rx=2.5, sw=1.3)
    s.line(553, 204, 566, 204, th.fg, 1.3)
    s.text(572, 209, "axial", 13, th.secondary, anchor="start")
    s.text(
        328,
        322,
        "radial, in the load zone, on the housing itself: no "
        "joint between bearing and sensor",
        13,
        th.muted,
    )
    s.line(282, 300, 276, 262, th.muted, 1.0, dash="3,3")
    s.line(374, 300, 380, 262, th.muted, 1.0, dash="3,3")

    # --- The once-per-revolution pickup on the free shaft end ---------------
    s.rect(74, 146, 40, 28, th.panel, th.accent, rx=5, sw=2.0)
    s.arrow(94, 174, 94, 210, th.accent, 1.8)
    s.rect(86, shaft_y - 7, 16, 14, th.accent, th.fg, sw=1.0)
    s.text(122, 152, "once-per-revolution", 12, th.accent, anchor="start")
    s.text(122, 170, "pickup on a mark", 12, th.accent, anchor="start")

    # --- The cable bundle into the analyser --------------------------------
    s.line(94, 146, 94, 96, th.accent, 1.6)
    s.line(282, shaft_y - 40, 282, 96, th.secondary, 1.6)
    s.line(374, shaft_y - 40, 374, 96, th.secondary, 1.6)
    s.line(553, 204, 553, 96, th.secondary, 1.6)
    s.line(94, 96, 640, 96, th.fg, 1.8)
    s.arrow(640, 96, 690, 152, th.fg, 1.8)
    s.rect(628, 158, 246, 118, th.panel, th.primary, rx=12, sw=2.2)
    s.text(751, 190, "Analyser", 17, th.fg, bold=True)
    s.text(751, 218, "ch 1: acceleration", 14, th.fg)
    s.text(751, 242, "ch 2: tacho pulse", 14, th.fg)
    s.text(751, 264, "band-pass → envelope → spectrum", 11, th.muted)

    # --- Mounting: the usable upper frequency -------------------------------
    s.rect(48, 356, 396, 244, "none", th.fg, rx=10, sw=1.6)
    s.text(
        70,
        386,
        "Mounting sets the usable upper frequency",
        15,
        th.fg,
        anchor="start",
        bold=True,
    )
    rows = (
        (420.0, "stud into a prepared flat", "tens of kHz"),
        (450.0, "adhesive / thin cyanoacrylate", "~10 kHz"),
        (480.0, "magnet base", "a few kHz"),
        (510.0, "hand-held probe", "~1 kHz"),
    )
    for ry, what, limit in rows:
        s.text(70, ry, what, 14, th.fg, anchor="start")
        s.text(422, ry, limit, 14, th.muted, anchor="end")
    s.text(
        70,
        552,
        "this page band-passes 2-4 kHz, so a magnet base is",
        12,
        th.secondary,
        anchor="start",
    )
    s.text(
        70,
        572,
        "marginal there and a hand-held probe is useless",
        12,
        th.secondary,
        anchor="start",
    )

    # --- Acquisition: why 20 kHz and why 2 s --------------------------------
    s.rect(470, 356, 382, 244, "none", th.primary, rx=10, sw=1.6)
    s.text(492, 386, "Acquisition", 15, th.fg, anchor="start", bold=True)
    s.text(
        492,
        420,
        "20 kHz sample rate clears the 3 kHz resonance",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        492, 450, "$T$ = 2 s at 2000 r/min = 67 revolutions", 14, th.fg, anchor="start"
    )
    s.text(
        492,
        480,
        "$Δf = 1/T$ = 0.5 Hz, against $f_s$ = 33.3 Hz",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        492,
        522,
        "enough to resolve the $± f_s$ sidebands, which are",
        12,
        th.muted,
        anchor="start",
    )
    s.text(
        492,
        542,
        "what separates an inner-race defect from an",
        12,
        th.muted,
        anchor="start",
    )
    s.text(492, 562, "outer-race one", 12, th.muted, anchor="start")


# ---------------------------------------------------------------------------
# Mechanical-mobility rig (ISO 7626)
# ---------------------------------------------------------------------------


def _d_mobility_rig(s: SVG, th: Theme) -> None:
    """ISO 7626 rig: free-free beam, exciter + impedance head at the driving
    point, accelerometer at a transfer point, impact-hammer variant.
    """
    cy_top, beam_top, beam_h = 116.0, 286.0, 26.0
    beam_bot = beam_top + beam_h
    # Ceiling with soft suspension.
    s.line(150, cy_top, 730, cy_top, th.fg, 2.2)
    for hx in range(162, 730, 26):
        s.line(hx, cy_top, hx - 9, cy_top - 9, th.muted, 1.1)
    for sx in (168.0, 712.0):
        _spring_v(s, sx, cy_top, beam_top, th.muted, coils=3, width=8.0, sw=1.6)
    s.text(196, 142, "soft elastic suspension", 13, th.muted, anchor="start")

    # Beam under test.
    s.rect(150, beam_top, 580, beam_h, th.panel, th.fg, sw=2.2)
    s.text(
        470,
        beam_bot + 32,
        "Structure under test (free-free beam)",
        16,
        th.fg,
        bold=True,
    )

    # Driving point: exciter below the beam through an impedance head and a
    # drive rod (axially stiff, flexible in every other direction).
    dx = 248.0
    s.rect(dx - 14, beam_bot, 28, 16, th.secondary, th.fg, rx=3, sw=1.6)
    s.line(dx, beam_bot + 16, dx, 412, th.fg, 2.2)
    s.line(dx - 5, 352, dx + 5, 352, th.accent, 3.0)
    s.line(dx - 5, 392, dx + 5, 392, th.accent, 3.0)
    # The note sits in the 163 px between the sheet margin and the exciter
    # box, which is drawn over it; its leader leaves above the box's top
    # corner rather than through it, and joins the rod under the
    # impedance-head caption.
    s.text(44, 440, "drive rod: stiff axially,", 12, th.accent, anchor="start")
    s.text(44, 458, "flexible in every other", 12, th.accent, anchor="start")
    s.text(44, 476, "direction (6.4.4)", 12, th.accent, anchor="start")
    s.line(200, 416, dx - 8, 392, th.muted, 1.0, dash="3,3")
    s.rect(dx - 37, 412, 74, 48, th.panel, th.primary, rx=9, sw=2)
    s.text(dx, 486, "Exciter", 15, th.fg, bold=True)
    s.text(60, 380, "Impedance head", 14, th.fg, anchor="start", bold=True)
    s.text(60, 402, "$F$ and $a$ at the drive point", 12, th.muted, anchor="start")
    s.line(dx - 16, beam_bot + 8, 154, 362, th.muted, 1.1, dash="3,3")
    s.arrow(dx + 18, 396, dx + 18, 340, th.secondary, 2.2)
    s.text(dx + 28, 372, "$F_i$", 14, th.secondary, anchor="start")
    s.arrow(dx, beam_top - 4, dx, beam_top - 46, th.accent, 2.2)
    s.text(dx - 14, beam_top - 34, "$v_i$", 14, th.accent, anchor="end")
    s.text(210, 218, "driving point:  $Y_{ii} = v_i / F_i$", 14, th.fg, anchor="start")

    # Transfer point: accelerometer further along the beam.
    tx = 430.0
    _accel(s, tx, beam_top)
    s.arrow(tx, beam_top - 28, tx, beam_top - 56, th.accent, 2.2)
    s.text(tx + 12, beam_top - 40, "$v_j$", 14, th.accent, anchor="start")
    s.text(tx + 60, 192, "transfer:  $Y_{ji} = v_j / F_i$", 14, th.fg)

    # Impact-hammer variant striking the beam.
    hx2 = 600.0
    s.line(hx2 + 60, 172, hx2 + 6, 244, th.fg, 2.4)
    s.rect(hx2 - 16, 238, 32, 20, th.panel, th.fg, rx=4, sw=2)
    s.arrow(hx2, 262, hx2, beam_top - 6, th.secondary, 1.8)

    # FRF family footer.
    s.text(
        450,
        520,
        "$Y(f) = v/F$  [m/(N·s)] · attached exciter (Part 2) · impact hammer (Part 5)",
        15,
        th.fg,
    )
    s.text(
        450,
        546,
        "same measurement, three FRFs: $x/F$ receptance · $v/F$ mobility "
        "· $a/F$ accelerance",
        13,
        th.muted,
    )

    # ----- Where the two transducers go: the ISO 7626-2 Figure 4 decision ---
    s.text(
        450,
        600,
        "Where the accelerometer and the force transducer go (clause 6.4.4)",
        16,
        th.fg,
        bold=True,
    )
    verdicts = (
        (72.0, "a)", "accelerometer through the rod", "INVALID", th.secondary),
        (356.0, "b)", "force transducer at the structure", "VALID", th.accent),
        (640.0, "c)", "force transducer at the exciter", "WITH CAUTION", th.muted),
    )
    for px, tag, what, verdict, colour in verdicts:
        s.rect(px, 626, 224, 158, "none", colour, rx=10, sw=1.8)
        s.text(px + 14, 652, tag, 15, th.fg, anchor="start", bold=True)
        s.rect(px + 40, 668, 148, 12, th.panel, th.fg, sw=1.6)  # structure
        s.line(px + 114, 680, px + 114, 748, th.fg, 2.0)  # drive rod
        s.line(px + 108, 700, px + 120, 700, th.accent, 2.6)
        s.line(px + 108, 730, px + 120, 730, th.accent, 2.6)
        if tag == "a)":  # accelerometer on the rod
            s.rect(px + 122, 706, 16, 14, th.secondary, th.fg, rx=2, sw=1.2)
            s.rect(px + 100, 748, 28, 12, th.primary, th.fg, rx=2, sw=1.2)
        elif tag == "b)":  # both at the structure
            s.rect(px + 130, 656, 16, 14, th.secondary, th.fg, rx=2, sw=1.2)
            s.rect(px + 100, 680, 28, 12, th.primary, th.fg, rx=2, sw=1.2)
        else:  # force transducer at the exciter
            s.rect(px + 130, 656, 16, 14, th.secondary, th.fg, rx=2, sw=1.2)
            s.rect(px + 100, 736, 28, 12, th.primary, th.fg, rx=2, sw=1.2)
        s.text(px + 112, 776, what, 12, th.fg)
        s.text(px + 112, 646, verdict, 14, colour, bold=True)
    s.text(
        450,
        806,
        "the exciter attachment must be at least 10× more "
        "mobile, laterally and rotationally, than the structure (6.4.4)",
        14,
        th.fg,
    )
    s.text(
        450,
        830,
        "and the suspension at least 10× more mobile than the "
        "structure at each attachment point (5.3)",
        13,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Dynamic transfer stiffness of resilient elements (ISO 10846)
# ---------------------------------------------------------------------------


def _d_transfer_stiffness_rig(s: SVG, th: Theme) -> None:
    """ISO 10846: isolator between the driven input mass and a blocked output
    (direct, force transducer) or a blocking mass (indirect).
    """
    for cx, head in (
        (250.0, "Direct method (Part 2)"),
        (650.0, "Indirect method (Part 3)"),
    ):
        s.text(cx, 78, head, 19, th.fg, bold=True)
        _exciter(s, cx, 158.0, stinger=18.0)
        # Driven input mass with its input displacement u1.
        s.rect(cx - 80, 158, 160, 44, th.panel, th.fg, rx=6, sw=2.2)
        s.text(cx, 186, "excitation mass", 14, th.fg)
        _motion_arrows(s, cx - 96, 180, 24, th.secondary)
        s.text(cx - 110, 186, "$u_1$", 15, th.secondary, anchor="end")
        # The unidirectionality check: an accelerometer at the edge of the
        # excitation mass, in the plane of the input flange, sensing across
        # the excitation direction (Part 2, Inequality 3).
        s.rect(cx + 62, 190, 16, 14, th.secondary, th.fg, rx=2.5, sw=1.3)
        s.arrow(cx + 78, 197, cx + 104, 197, th.secondary, 1.6)
        # Isolator under test.
        _spring_v(s, cx, 202, 310, th.accent, coils=4)
        s.text(cx + 28, 260, "isolator under test", 14, th.accent, anchor="start")
    s.text(
        48, 296, "$a′_1$: unwanted transverse input,", 12, th.secondary, anchor="start"
    )
    s.text(
        48, 314, "≥ 15 dB below $a_1$ (Inequality 3)", 12, th.secondary, anchor="start"
    )
    s.line(150, 286, 310, 202, th.muted, 1.0, dash="3,3")

    # ===== Direct output: blocked, force transducer on a rigid foundation ===
    cx = 250.0
    s.rect(cx - 30, 310, 60, 18, th.secondary, th.fg, rx=3, sw=1.6)
    s.text(cx + 52, 326, "force transducer", 13, th.secondary, anchor="start")
    s.rect(cx - 105, 328, 210, 26, th.panel, th.fg, sw=2)
    s.ground(354, cx - 125, cx + 125)
    s.text(cx, 388, "Rigid foundation", 13, th.muted)
    s.text(cx, 470, "output blocked:  $u_2 ≈ 0$ → measure $F_{2,b}$", 14, th.fg)
    s.text(cx, 500, "$k_{2,1} = F_{2,b} / u_1$", 17, th.primary, bold=True)

    # ===== Indirect output: blocking mass on soft supports ==================
    cx = 650.0
    s.rect(cx - 85, 310, 170, 60, th.panel, th.fg, rx=6, sw=2.4)
    s.text(cx, 346, "blocking mass $m_2$", 15, th.fg)
    _accel(s, cx + 55, 310)
    s.text(cx + 72, 296, "$a_2$", 13, th.secondary, anchor="start")
    for sx in (cx - 50.0, cx + 50.0):
        _spring_v(s, sx, 370, 430, th.muted, coils=3, width=8.0, sw=1.6)
    s.ground(430, cx - 115, cx + 115)
    s.text(cx + 70, 408, "soft support", 12, th.muted, anchor="start")
    s.text(cx, 470, "measure $T = u_2 / u_1$  (small)", 14, th.fg)
    s.text(cx, 500, "$k_{2,1} = −(2πf)^2·(m_2+m_f)·T$", 17, th.primary, bold=True)

    # Validity footer (Part 3 clause 6, Part 1 Eq. 7).
    s.text(
        450,
        556,
        "valid where $ΔL_{1,2} = L_{a1} − L_{a2} ≥ 20$ dB, i.e. "
        "$|T| ≤ 0.1$   (Part 3, Inequality 2)",
        15,
        th.muted,
    )
    s.text(
        450,
        582,
        "the blocking force approximates the force delivered to a stiff receiver (Part 1, Eq. 7)",
        13,
        th.muted,
        italic=True,
    )

    # ===== How the static preload is applied (Part 1, clause 6.3.3.1) =======
    s.text(
        450,
        640,
        "The two ways the static preload is applied (ISO 10846-1, 6.3.3.1)",
        18,
        th.fg,
        bold=True,
    )
    # a) gravity loading. Both panels are sized on their own headings,
    # which are the widest lines they carry in either language.
    s.rect(44, 664, 400, 196, "none", th.fg, rx=10, sw=1.6)
    s.text(
        62,
        692,
        "a) gravity: the output-side mass is the preload",
        14,
        th.fg,
        anchor="start",
        bold=True,
    )
    s.rect(150, 712, 130, 30, th.panel, th.fg, rx=4, sw=2.0)
    _spring_v(s, 215, 742, 786, th.accent, coils=3, width=10.0, sw=2.0)
    s.rect(140, 786, 150, 34, th.panel, th.fg, rx=4, sw=2.2)
    s.text(215, 808, "load mass", 13, th.fg)
    s.ground(820, 120, 310)
    s.arrow(330, 760, 330, 800, th.secondary, 2.2)
    s.text(340, 784, "$W$ = load", 13, th.secondary, anchor="start")
    s.text(
        70,
        848,
        "simple, but unstable for large isolators at high loads",
        12,
        th.muted,
        anchor="start",
    )
    # b) frame + actuator + decoupling springs
    s.rect(456, 664, 400, 196, "none", th.primary, rx=10, sw=1.6)
    s.text(
        474,
        692,
        "b) frame, actuator and decoupling springs",
        14,
        th.fg,
        anchor="start",
        bold=True,
    )
    s.line(500, 706, 820, 706, th.fg, 2.6)  # frame traverse
    s.line(500, 706, 500, 822, th.fg, 2.2)
    s.line(820, 706, 820, 822, th.fg, 2.2)
    s.rect(628, 712, 64, 34, th.panel, th.secondary, rx=4, sw=2.0)
    s.arrow(660, 748, 660, 768, th.secondary, 2.2)
    # Right-aligned on the frame's own leg: set from the left, the Spanish
    # second line runs through it.
    s.text(812, 734, "actuator: 100 % of the", 12, th.secondary, anchor="end")
    s.text(812, 752, "permissible static load", 12, th.secondary, anchor="end")
    _spring_v(s, 660, 768, 800, th.accent, coils=3, width=10.0, sw=2.0)
    s.rect(600, 800, 120, 26, th.panel, th.fg, rx=4, sw=2.2)
    s.text(660, 818, "$m_2$", 13, th.fg)
    for sx in (556.0, 764.0):
        _spring_v(s, sx, 800, 840, th.muted, coils=2, width=7.0, sw=1.5)
    s.text(
        500,
        856,
        "auxiliary springs decouple $m_2$ from the frame",
        12,
        th.muted,
        anchor="start",
    )

    # ===== Transverse translations (Part 2, clause 5.2) =====================
    s.text(
        450,
        900,
        "Transverse translations are standardised too (ISO 10846-2, 5.2)",
        18,
        th.fg,
        bold=True,
    )
    s.rect(48, 924, 804, 132, "none", th.muted, rx=10, sw=1.4)
    s.rect(300, 950, 190, 30, th.panel, th.fg, rx=4, sw=2.2)
    s.text(395, 971, "force-distribution plate", 12, th.fg)
    _motion_arrows(s, 268, 965, 22, th.secondary)
    s.text(255, 940, "$a_{1x}$", 14, th.secondary, anchor="end")
    for rx in (330.0, 460.0):  # guiding roller bearings
        s.circle(rx, 940, 9, th.bg, th.fg, 1.6)
    s.text(
        508, 942, "roller bearings, or two symmetrical", 12, th.muted, anchor="start"
    )
    s.text(
        508, 962, "elements, suppress the unwanted input", 12, th.muted, anchor="start"
    )
    s.rect(320, 980, 150, 26, th.accent, th.fg, rx=4, sw=1.8)
    s.text(395, 999, "test element in shear", 11, th.bg)
    for fx in (348.0, 442.0):
        s.rect(fx - 22, 1006, 44, 16, th.panel, th.secondary, rx=3, sw=1.6)
    s.text(508, 1000, "output shear force summed from two", 12, th.fg, anchor="start")
    s.text(508, 1020, "transducers,  $F_2 = F_2′ + F_2″$", 12, th.fg, anchor="start")
    s.ground(1022, 300, 490)
    s.text(
        450,
        1082,
        "a mount is loaded in shear as well as in compression, "
        "and the transverse stiffness is usually the smaller of the two",
        13,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Junction vibration measurement, L- and T-junctions (ISO 10848)
# ---------------------------------------------------------------------------


def _d_junction_rig(s: SVG, th: Theme) -> None:
    """ISO 10848 junction rig: an L- and a T-junction of concrete plates,
    structure-borne excitation on element i, accelerometers on i and j and
    the junction length l_ij along the corner line.
    """
    gy = 430.0
    dp = 170.0
    dxo, dyo = dp * 0.72, dp * 0.55

    # ===== Left: L-junction (wall on the left end of the floor plate) =====
    s.text(280, 86, "L-junction", 18, th.fg, bold=True)
    _plate_top(s, th, 140, gy, 230, dp, 16)
    _plate_up(s, th, 140, gy, 16, 180, dp)
    # Junction line along the corner, highlighted, with its length label.
    s.line(156, gy, 156 + dxo, gy - dyo, th.accent, 2.6)
    s.text(58, 474, "$l_{ij} ≥ 2.3$ m", 15, th.fg, anchor="start")
    s.line(126, 466, 152, 438, th.muted, 1.0)

    # Exciter on the floor (element i), accelerometers on i and j.
    _exciter(s, 330, 396)
    _accel(s, 250, 410)
    _accel(s, 380, 380)
    _accel_wall(s, 205, 300)
    _accel_wall(s, 236, 262)
    s.text(196, 420, "$i$", 19, th.primary, bold=True)
    s.text(178, 200, "$j$", 19, th.secondary, bold=True)
    # Transmission path across the corner.
    s.path("M 300 402 Q 214 400 208 330", stroke=th.accent, sw=2.0)
    s.arrow(209.0, 344.0, 208.0, 322.0, th.accent, 2.0)
    s.text(194, 356, "$D_{v,ij}$", 14, th.accent, anchor="end")

    # ===== Right: T-junction (wall standing mid-way on the floor) =========
    s.text(690, 86, "T-junction", 18, th.fg, bold=True)
    _plate_top(s, th, 520, gy, 220, dp, 16)
    _plate_up(s, th, 620, gy, 16, 180, dp)
    s.line(636, gy, 636 + dxo, gy - dyo, th.accent, 2.6)
    _exciter(s, 566, 404)
    _accel(s, 588, 422)
    _accel_wall(s, 685, 290)
    _accel(s, 762, 384)
    s.text(533, 423, "$i$", 19, th.primary, bold=True)
    s.text(658, 200, "$j$", 19, th.secondary, bold=True)
    s.text(806, 400, "$j$", 19, th.secondary, bold=True)
    s.path("M 612 418 Q 690 434 756 400", stroke=th.accent, sw=2.0)
    s.arrow(742.0, 407.0, 760.0, 398.0, th.accent, 2.0)
    s.path("M 606 406 Q 646 394 654 330", stroke=th.accent, sw=2.0)
    s.arrow(655.0, 344.0, 654.0, 322.0, th.accent, 2.0)

    # Exciter label shared by both panels.
    s.text(450, 250, "Shaker or hammer on element $i$", 15, th.fg)
    s.line(376, 258, 348, 322, th.muted, 1.0)
    s.line(524, 258, 556, 348, th.muted, 1.0)

    # Plate thickness leader (the lines stop above the caption text).
    s.text(450, 496, "concrete plates 140 mm to 200 mm thick", 15, th.muted)
    s.line(322, 477, 300, 442, th.muted, 1.0)
    s.line(578, 477, 600, 442, th.muted, 1.0)

    # Normative relations.
    s.text(
        80,
        536,
        "$l_{ij} ≥ 2.3$ m along the junction; element sizes 3.0 m $≤ l_i <$ 6.0 m",
        15,
        th.fg,
        anchor="start",
    )
    s.text(
        80,
        564,
        "≥ 4 excitation positions on $i$; accelerometers "
        "≥ 0.25 m from edges, ≥ 0.5 m apart",
        15,
        th.fg,
        anchor="start",
    )
    s.text(
        80,
        596,
        "$K_{ij} = D̄_{v,ij} + 10 log_{10}( l_{ij} / √(a_i·a_j) "
        ")$,   $a_i$ = equivalent absorption length",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )


# ---------------------------------------------------------------------------
# Power injection: coupling loss factors from measured energies (Norton 6.6.4)
# ---------------------------------------------------------------------------


def _d_power_injection_rig(s: SVG, th: Theme) -> None:
    """The experimental-SEA rig: two plates joined along an edge, a shaker
    through an impedance head on one of them, accelerometers distributed over
    both, and the drive moved for the second run of the two-drive scheme.
    """
    gy = 380.0
    dp = 116.0
    dxo, dyo = dp * 0.72, dp * 0.55

    def _pair(x0: float, driven: int, head: str) -> None:
        """One state of the experiment: plate 1 horizontal, plate 2 upright."""
        s.text(x0 + 200, 80, head, 18, th.fg, bold=True)
        _plate_top(s, th, x0 + 40, gy, 240, dp, 12)
        _plate_up(s, th, x0 + 40, gy, 12, 168, dp)
        s.line(x0 + 52, gy, x0 + 52 + dxo, gy - dyo, th.accent, 2.6)
        s.line(x0 + 100, 250, x0 + 156, 156, th.muted, 1.0, dash="3,3")
        s.text(x0 + 160, 150, "subsystem 2", 15, th.secondary, anchor="start")
        s.text(x0 + 248, gy + 44, "subsystem 1", 15, th.primary)
        # Accelerometer positions: several per subsystem, off the edges and
        # off the drive point, because the band energy uses a space average.
        for ax in (108.0, 152.0, 216.0, 252.0):
            _accel(s, x0 + ax, gy)
        _accel(s, x0 + 178, gy - 34)
        for ay, axx in ((240.0, 20.0), (288.0, 48.0), (330.0, 26.0)):
            _accel_wall(s, x0 + 52 + axx, ay)
        # The drive: a shaker through an impedance head, on one subsystem.
        if driven == 1:
            s.rect(x0 + 120, gy + 2, 26, 13, th.secondary, th.fg, rx=3, sw=1.4)
            s.line(x0 + 133, gy + 15, x0 + 133, gy + 40, th.fg, 2.2)
            s.rect(x0 + 96, gy + 40, 74, 42, th.panel, th.primary, rx=9, sw=2)
            s.text(
                x0 + 176, gy + 20, "impedance head", 13, th.secondary, anchor="start"
            )
            s.text(x0 + 180, gy + 68, "shaker", 14, th.fg, anchor="start")
        else:
            s.rect(x0 + 58, 196, 26, 13, th.secondary, th.fg, rx=3, sw=1.4)
            s.line(x0 + 84, 202, x0 + 176, 202, th.fg, 2.2)
            s.rect(x0 + 176, 179, 74, 46, th.panel, th.primary, rx=9, sw=2)
            s.text(x0 + 213, 248, "shaker", 14, th.fg)
        s.text(
            x0 + 40,
            gy + 96,
            f"$Π_{'1' if driven == 1 else '2'}$ measured,  "
            f"$Π_{'2' if driven == 1 else '1'} = 0$",
            14,
            th.fg,
            anchor="start",
        )
        s.text(
            x0 + 40,
            gy + 122,
            "$E_1 = M_1⟨v_1^2⟩,   E_2 = M_2⟨v_2^2⟩$",
            14,
            th.fg,
            anchor="start",
        )

    _pair(10.0, 1, "Run 1: drive subsystem 1")
    _pair(460.0, 2, "Run 2: drive subsystem 2")
    s.line(450, 70, 450, 528, th.muted, 1.0, dash="6,6")

    # What is measured, and what each run buys.
    s.text(
        450,
        566,
        "$Π_{in} = ½ Re{F v*}$ at the drive point, from an "
        "impedance head, not the amplifier setting",
        15,
        th.fg,
    )
    s.text(
        450,
        592,
        "$⟨v^2⟩$ space-averaged over several positions per "
        "subsystem, away from the edges and from the drive point",
        15,
        th.fg,
    )
    s.text(
        450,
        618,
        "one run gives $η_{12}$ only if $η_1$ and $η_2$ come "
        "from a decay measurement; two runs solve all four",
        15,
        th.primary,
        bold=True,
    )
    s.text(
        450,
        644,
        "bands wide enough to hold several modes of each "
        "subsystem: the modal densities decide how wide",
        13,
        th.muted,
    )


def _d_machine_vibration_positions(s: SVG, th: Theme) -> None:
    """Where machine vibration is measured (ISO 20816-1, 4.4).

    Two kinds of measurement on one train. At the near bearing, the vibration
    of the non-rotating parts, taken on the housing in three mutually
    perpendicular directions. At the far bearing, the vibration of the shaft
    itself, taken by a pair of non-contacting probes in one transverse plane,
    with the cross-section that fixes the right angle between them and the
    chain the reading runs through.
    """
    import math

    gy = 508.0
    shaft_y = 372.0
    s.ground(gy, 96, 744)
    s.rect(118, gy - 24, 596, 24, th.panel, th.fg, rx=3, sw=2)  # common baseplate

    # --- The train: two pedestal bearings carrying a shaft between two bodies
    bearing_x = (196.0, 636.0)
    s.line(164, shaft_y, 672, shaft_y, th.fg, 5)  # shaft
    # The second label is the longer one in both languages, so it is set a
    # size down rather than pushed against the far bearing.
    for x, w, label, size in (
        (258.0, 128.0, "motor", 15),
        (448.0, 152.0, "driven machine", 13),
    ):
        s.rect(x, shaft_y - 52, w, 104, th.panel, th.primary, rx=8, sw=2.2)
        s.text(x + w / 2, shaft_y + 6, label, size)
    s.rect(402, shaft_y - 16, 38, 32, th.bg, th.accent, rx=3, sw=2)  # coupling
    s.text(421, shaft_y - 28, "coupling", 13, th.accent)
    for bx in bearing_x:
        s.rect(bx - 30, shaft_y - 26, 60, 26, th.secondary, th.fg, rx=4, sw=1.6)
        s.rect(bx - 22, shaft_y + 12, 44, gy - 24 - shaft_y - 12, th.panel, th.fg, 2)

    # --- Near bearing: the three perpendicular directions -------------------
    nx = bearing_x[0]
    _accel(s, nx, shaft_y - 26)
    s.arrow(nx, shaft_y - 48, nx, shaft_y - 96, th.accent, 2.4)
    s.text(nx, shaft_y - 106, "vertical", 14, th.accent)
    s.arrow(nx - 34, shaft_y - 18, nx - 84, shaft_y - 18, th.accent, 2.4)
    s.text(nx - 92, shaft_y - 14, "horizontal", 14, th.accent, anchor="end")
    # The axial direction leaves the elevation, so it is drawn as a
    # foreshortened diagonal rather than as a second horizontal arrow.
    s.arrow(nx - 24, shaft_y + 6, nx - 62, shaft_y + 36, th.muted, 2.4)
    s.text(nx - 70, shaft_y + 50, "axial", 14, th.muted, anchor="end")

    # --- Far bearing: the pair of non-contacting probes ---------------------
    fx = bearing_x[1]
    for sign in (-1.0, 1.0):
        tip_x, tip_y = fx + sign * 16.0, shaft_y - 16.0
        end_x, end_y = fx + sign * 52.0, shaft_y - 52.0
        s.line(tip_x, tip_y, end_x, end_y, th.fg, 2.4)
        s.circle(end_x, end_y, 7, th.secondary, th.fg, 1.5)
    s.text(fx, shaft_y - 76, "two probes", 14, th.secondary)

    # --- The cross-section that fixes the right angle -----------------------
    cx, cy, r = 744.0, 142.0, 48.0
    s.line(fx + 52, shaft_y - 52, cx - 30, cy + r + 4, th.muted, 1.2, dash="5 5")
    s.circle(cx, cy, r, th.panel, th.fg, 2)  # bearing bore
    s.circle(cx, cy, r * 0.58, th.bg, th.fg, 2.4)  # shaft section
    s.text(cx, cy + 5, "shaft", 13)
    for angle in (135.0, 45.0):
        rad = math.radians(angle)
        s.line(
            cx + r * 0.58 * math.cos(rad),
            cy - r * 0.58 * math.sin(rad),
            cx + (r + 20) * math.cos(rad),
            cy - (r + 20) * math.sin(rad),
            th.muted,
            1.6,
        )
        s.circle(
            cx + (r + 26) * math.cos(rad),
            cy - (r + 26) * math.sin(rad),
            7,
            th.secondary,
            th.fg,
            1.5,
        )
    s.path(
        f"M {cx - 30} {cy - 30} A 42 42 0 0 1 {cx + 30} {cy - 30}",
        "none",
        th.accent,
        sw=2.0,
    )
    s.text(cx, cy - 54, "90° ± 5°", 14, th.accent)

    # --- The chain a shaft reading runs through -----------------------------
    box_y = gy + 108.0
    for x, w, label in (
        (196.0, 150.0, "transducer"),
        (382.0, 166.0, "conditioning"),
        (584.0, 166.0, "processing"),
    ):
        s.rect(x, box_y, w, 40, th.panel, th.fg, rx=6, sw=1.8)
        s.text(x + w / 2, box_y + 26, label, 14)
    s.arrow(350, box_y + 20, 378, box_y + 20, th.muted, 2.2)
    s.arrow(552, box_y + 20, 580, box_y + 20, th.muted, 2.2)

    # --- The two captions ---------------------------------------------------
    s.text(250, gy + 54, "on non-rotating parts", 15, bold=True)
    s.text(250, gy + 76, "axial only on a thrust bearing", 13, th.muted)
    s.text(646, gy + 54, "on the rotating shaft", 15, bold=True)
    s.text(646, gy + 76, "both probes on one bearing half", 13, th.muted)


def _numbered(s: SVG, x: float, y: float, label: str, colour: str) -> None:
    """Small numbered marker tying a point on the section to its callout."""
    s.circle(x, y, 10, s.th.bg, colour, 1.6)
    s.text(x, y + 4.5, label, 12, colour, bold=True)


def _d_railway_monitoring(s: SVG, th: Theme) -> None:
    """Where E DIN 4150-2 measures a railway, and how the passages count.

    The upper half is Clause 5: the transducer on the floor of the room to
    be protected, vertical and two horizontals, where the vibration is
    strongest and for z mostly at mid-span (5.2); and the substitute point
    of 5.4 at the foundation, whose transfer to the room, a linear factor
    or a frequency-dependent function, can only ever show compliance. The
    lower half is 6.5.3.2: every passage one clock maximum however long it
    lasts, the passages grouped by category, and the chain of Formulae (5),
    (7), (8) and (6) that turns them into KB_Fmax and KB_FTr.
    """
    s.text(
        450,
        78,
        "The floor of the room, or a point at the foundation that stands in for it",
        15,
        th.fg,
        bold=True,
    )

    # --- The line: a tram on the surface and a metro in its tunnel ---------
    s.ground(300, 24, 256)
    s.rect(46, 250, 150, 40, th.panel, th.accent, rx=8, sw=2.2)
    for k in range(4):
        s.rect(60 + 34 * k, 258, 22, 12, th.bg, th.accent, rx=2, sw=1.0)
    for wx in (72.0, 98.0, 144.0, 170.0):
        s.circle(wx, 294, 5, th.fg)
    s.text(121, 238, "tram, on the surface", 13, th.accent)
    s.rect(30, 326, 182, 70, "none", th.fg, rx=30, sw=2.2)
    s.rect(50, 342, 142, 36, th.panel, th.primary, rx=8, sw=2.2)
    for wx in (72.0, 98.0, 144.0, 170.0):
        s.circle(wx, 382, 4.5, th.fg)
    s.line(42, 387, 200, 387, th.fg, 1.6)
    s.text(121, 418, "metro, underground", 13, th.primary)
    # Both paths run through the ground to the same basement wall.
    s.arrow(206, 318, 242, 330, th.muted, 1.8)
    s.arrow(214, 350, 242, 356, th.muted, 1.8)

    # --- The building: a basement and two storeys, the room on the upper --
    for y, h in ((112.0, 8.0), (200.0, 10.0), (300.0, 10.0)):
        s.rect(250, y, 350, h, th.panel, th.fg, sw=1.8)
    s.line(256, 120, 256, 372, th.fg, 3)
    s.line(596, 120, 596, 372, th.fg, 3)
    # The load-bearing interior wall fixes the floor span of the room:
    # x 256 to x 476, so mid-span is x 366.
    s.line(476, 120, 476, 200, th.fg, 2.6)
    s.line(476, 210, 476, 300, th.fg, 2.6)
    s.rect(244, 372, 360, 14, th.panel, th.fg, sw=2)
    s.ground(386, 244, 604)
    s.text(266, 134, "room to be protected", 12, th.primary, anchor="start", bold=True)

    # --- 1: the floor point at mid-span, with z and the two horizontals ----
    _accel(s, 366, 200, 16)
    s.arrow(366, 174, 366, 146, th.primary, 2.2)
    s.text(374, 153, "$z$", 14, th.primary, anchor="start")
    # The horizontal axis is drawn clear of the floor slab below it, whose
    # top edge runs at y = 200, so its label is never crossed by that line.
    s.arrow(378, 191, 420, 191, th.primary, 2.2)
    s.text(426, 187, "$x$", 14, th.primary, anchor="start")
    # y leaves the elevation, so it is drawn foreshortened.
    s.arrow(376, 186, 402, 164, th.primary, 2.2)
    s.text(407, 166, "$y$", 14, th.primary, anchor="start")
    _numbered(s, 334, 180, "1", th.primary)
    s.line(256, 224, 476, 224, th.muted, 1.0)
    for x, half in ((256.0, 5.0), (366.0, 7.0), (476.0, 5.0)):
        s.line(x, 224 - half, x, 224 + half, th.muted, 1.2)
    s.text(366, 242, "middle of the floor span", 11, th.fg)

    # --- 3: the substitute point on the foundation, 2: its transfer up ----
    _accel(s, 280, 372, 14)
    s.line(280, 346, 280, 222, th.secondary, 2.2, dash="7,5")
    s.arrow(280, 232, 280, 213, th.secondary, 2.2)
    _numbered(s, 302, 272, "2", th.secondary)
    _numbered(s, 312, 356, "3", th.secondary)

    # --- The three callouts -----------------------------------------------
    for top, colour, number, title, lines in (
        (
            112.0,
            th.primary,
            "1",
            "on the floor of the room",
            (
                "vertical $z$, horizontal $x$ and $y$ at 90°",
                "where it is expected to be strongest;",
                "for $z$, mostly the middle of the span",
            ),
        ),
        (
            216.0,
            th.secondary,
            "2",
            "the transfer to the room",
            (
                "a linear factor or a frequency-dependent",
                "transfer function, preferably measured,",
                "its uncertainty only as an upper bound",
            ),
        ),
        (
            320.0,
            th.secondary,
            "3",
            "a substitute measuring point",
            (
                "e.g. at the foundation, for",
                "monitoring over weeks or months,",
                "held to DIN 45669-2 like any point",
            ),
        ),
    ):
        s.rect(612, top, 276, 96, th.panel, colour, rx=6, sw=1.8)
        _numbered(s, 632, top + 20, number, colour)
        s.text(650, top + 25, title, 13, colour, anchor="start", bold=True)
        for k, line in enumerate(lines):
            s.text(624, top + 48 + 18 * k, line, 12, th.fg, anchor="start")

    s.text(
        450,
        446,
        "from a substitute point only $KB_{Fmax} < A_o$ and $KB_{FTr} < A_r$ can "
        "be shown; an exceedance cannot be reliably proven there",
        13,
        th.fg,
    )

    # --- The passages: one interval each, grouped by train category -------
    s.text(
        450,
        482,
        "One passage, one interval, however long it lasts",
        15,
        th.fg,
        bold=True,
    )
    x0, yb = 70.0, 590.0

    def at(t: float) -> float:
        return x0 + 2.0 * t

    s.arrow(x0, yb, x0, 506, th.fg, 1.6)
    s.text(80, 514, "$KB_{F}(t)$", 13, th.fg, anchor="start")
    s.arrow(x0, yb, 846, yb, th.fg, 1.6)
    s.text(852, 594, "t in s", 12, th.muted, anchor="start")
    for t in (0, 100, 200, 300, 380):
        s.line(at(t), yb, at(t), yb + 6, th.fg, 1.2)
        s.text(at(t), 610, f"{t}", 12, th.muted)
    s.text(24, 650, "per category", 12, th.muted, anchor="start")
    for t0, t1, hump, colour, name, z, ftm, fmax in (
        (49.0, 70.0, 8.0, th.primary, "metro north", "14", "0.037", "0.055"),
        (166.0, 185.0, 10.0, th.primary, "metro south", "14", "0.047", "0.070"),
        (258.0, 274.0, 48.0, th.accent, "tram east", "9", "0.406", "0.609"),
        (325.0, 351.0, 68.0, th.accent, "tram west", "10", "0.568", "0.851"),
    ):
        a, b = at(t0), at(t1)
        c = (a + b) / 2
        s.rect(a, 510, b - a, yb - 510, "none", colour, rx=2, sw=1.4, dash="5,4")
        s.path(f"M {a} {yb} Q {c} {yb - 2 * hump} {b} {yb}", "none", colour, sw=2.2)
        s.circle(c, yb - hump, 3.5, colour)
        s.text(c, 502, name, 12, colour)
        s.text(c, 632, f"$Z$ = {z} passages", 12, th.fg)
        s.text(c, 650, f"$KB_{{FTm,Zug}}$ = {ftm}", 12, th.fg)
        # The largest of the four is the one the railway is judged on.
        largest = fmax == "0.851"
        colour_max = th.accent if largest else th.fg
        s.text(c, 668, f"$KB_{{Fmax,Zug}}$ = {fmax}", 12, colour_max, bold=largest)
    s.text(778, 527, "$KB_{FTi,Zug}$", 13, th.fg, anchor="start")
    s.text(
        450,
        694,
        "each passage is recorded whole and gives one $KB_{FTi,Zug}$, even when "
        "it lasts longer than 30 s",
        12,
        th.muted,
    )
    s.text(
        450,
        716,
        "the railway takes the largest: $KB_{Fmax}$ = 0.851, from the trams "
        "running west",
        13,
        th.fg,
    )

    # --- The four formulae the strip feeds --------------------------------
    s.rect(40, 734, 820, 84, th.panel, th.fg, rx=6, sw=1.6)
    s.text(240, 766, "$KB_{FTm,Zug} = √((1/Z) · Σ KB_{FTi,Zug}^2)$", 15, th.primary)
    s.text(374, 766, "(5)", 12, th.muted, anchor="start")
    s.text(650, 766, "$KB_{Fmax,Zug} = 1.5 × KB_{FTm,Zug}$", 15, th.primary)
    s.text(766, 766, "(7)", 12, th.muted, anchor="start")
    s.text(240, 802, "$KB_{Fmax} = max{KB_{Fmax,Zug}}$", 15, th.primary)
    s.text(374, 802, "(8)", 12, th.muted, anchor="start")
    s.text(640, 802, "$KB_{FTr} = √(Σ (n_{Zug}/N_r) · (α_{Zug} · KB_{FTm,Zug})^2)$", 15)
    s.text(802, 802, "(6)", 12, th.muted, anchor="start")
    s.text(
        450,
        846,
        "$N_r$ = 1920 by day and 960 by night; a category whose $KB_{FTm,Zug}$ "
        "is at or below 0.1 enters $KB_{FTr}$ as zero",
        12,
        th.muted,
    )
    s.text(
        450,
        868,
        "a meter to DIN 45669-1, where a 4 Hz lower limit is usually enough at "
        "a railway, its transducers coupled to DIN 45669-2",
        12,
        th.muted,
    )


def _transducer_block(s: SVG, x: float, y_bottom: float, size: float = 13.0) -> None:
    """A transducer drawn as a block standing on (x, y_bottom)."""
    s.rect(
        x - size / 2,
        y_bottom - size,
        size,
        size,
        s.th.secondary,
        s.th.fg,
        rx=2.0,
        sw=1.3,
    )


def _label_block(
    s: SVG,
    x: float,
    y0: float,
    lines: Sequence[str],
    width: float,
    colour: str,
    anchor: str = "middle",
    step: float = 17.0,
) -> None:
    """Lines set one size for the whole block, the largest that fits *width*."""
    size = s.fit_size(list(lines), [12, 11, 10], width)
    for j, line in enumerate(lines):
        s.text(x, y0 + step * j, line, size, colour, anchor)


def _d_vibration_meter_coupling(s: SVG, th: Theme) -> None:
    """Where DIN 45669-2 puts the transducer, how it is coupled, what it feeds.

    The section is drawn at 30 px to the metre: two storeys of 3 m on strip
    footings, a manhole 1 m wide and 1,5 m deep, and a machine on its own
    foundation block as the source. The four points are the positions of
    5.1: the foundation on the source side no higher than 0,5 m above ground
    (5.1.2), the floor at mid-span for the vertical (5.1.3), the top floor
    ceiling beside the outer wall for the horizontal pair, the plane
    DIN 4150-3:1999-02, 5.4 asks for and where 5.1.3 puts a horizontal
    transducer too, near the load-bearing walls of an upper storey, and the
    ground near the source at a set distance, clear of a disturbing body by
    at least 1,5 times its largest dimension, which is where 5.1.4 measures
    what a source itself emits. The arrows are the directions of 5.2, where
    x points at the source by preference. The three insets are the couplings
    of 5.3: the device of Figure 1 b) with its rounded feet, the device of
    Figure 1 a) with its spikes, both drawn at 0,85 px to the millimetre,
    and the ground spike of the note to 5.3.4.2 a), which the standard
    describes and does not draw, at 0,25 px to the millimetre. The strip at
    the foot is the DIN 45669-1:2010-09 chain the cable feeds, and the box is
    Formula (2) with its counting rule.
    """
    gy = 330.0  # the ground surface

    # --- The building, in section --------------------------------------------
    s.ground(gy, 20, 880)
    for x0 in (40.0, 185.0, 330.0):  # strip footings under the three walls
        s.rect(x0, gy, 30, 24, th.panel, th.fg, sw=1.6)
    for x0 in (50.0, 195.0, 340.0):  # two outer walls, one load-bearing inner wall
        s.rect(x0, 150, 10, gy - 150, th.panel, th.fg, sw=1.8)
    s.rect(60, gy - 8, 280, 8, th.panel, th.fg, sw=1.6)  # ground slab
    s.rect(50, 240, 300, 8, th.panel, th.fg, sw=1.8)  # first floor, 3 m up
    s.rect(50, 150, 300, 8, th.panel, th.fg, sw=1.8)  # top floor ceiling, 6 m up

    # The top floor ceiling beside the outer wall: the horizontal pair that
    # DIN 4150-3:1999-02, 5.4 asks for, in or close to the outer masonry.
    hx = 329.0
    _transducer_block(s, hx, 150)
    s.arrow(hx + 7, 143.5, hx + 44, 143.5, th.accent, 2.0)
    s.text(hx + 50, 148, "$x$", 14, th.accent, "start")
    s.arrow(hx + 5, 137, hx + 22, 118, th.accent, 2.0)
    s.text(hx + 26, 118, "$y$", 14, th.accent, "start")
    s.text(190, 90, "top floor ceiling, in or next to the outer wall:", 12, th.fg)
    s.text(190, 108, "horizontal, $x$ and $y$ (DIN 4150-3, 5.4)", 12, th.fg)
    s.line(300, 114, hx - 6, 136, th.muted, 1.0)

    # The floor at mid-span, between the inner wall and the outer wall (5.1.3).
    mx = (205.0 + 340.0) / 2
    _transducer_block(s, mx, 240)
    s.arrow(mx, 227, mx, 190, th.accent, 2.0)
    s.text(mx + 7, 196, "$z$", 14, th.accent, "start")
    s.text(mx, 276, "floor mid-span:", 12, th.fg)
    s.text(mx, 294, "vertical, $z$ (5.1.3)", 12, th.fg)

    # The foundation on the source side, its top 0,47 m above ground (5.1.2).
    fx = 357.0
    _transducer_block(s, fx, gy - 1)
    s.arrow(fx + 7, gy - 7.5, fx + 44, gy - 7.5, th.accent, 2.0)
    s.text(fx + 50, gy - 3, "$x$", 14, th.accent, "start")
    s.arrow(fx, gy - 14, fx, gy - 50, th.accent, 2.0)
    s.text(fx + 6, gy - 42, "$z$", 14, th.accent, "start")
    s.arrow(fx + 5, gy - 13, fx + 22, gy - 32, th.accent, 2.0)
    s.text(fx + 26, gy - 32, "$y$", 14, th.accent, "start")
    _label_block(
        s,
        372,
        246,
        ("foundation, facing the source,", "≤ 0.5 m above ground (5.1.2)"),
        196,
        th.fg,
        "start",
        18,
    )

    # The source: a machine on its own foundation block.
    sc = 810.0
    s.rect(750, gy - 6, 120, 36, th.panel, th.fg, sw=1.6)
    s.rect(sc - 35, gy - 70, 70, 64, th.panel, th.fg, rx=4, sw=2.0)
    s.circle(sc - 15, gy - 44, 14, th.fg)
    s.circle(sc - 15, gy - 44, 5, th.bg)
    _label_block(
        s, sc, 232, ("the source,", "here a machine"), 110, th.fg, "middle", 18
    )

    # The ground near the source, on a spike driven fully in: 15 px is the
    # 0,5 m of the note to 5.3.4.2 a) at the section's own scale.
    gx = 560.0
    s.line(gx, gy, gx, gy + 15, th.fg, 3.0)
    s.rect(gx - 7, gy - 3, 14, 3, th.fg)
    _transducer_block(s, gx, gy - 3)
    s.arrow(gx + 7, gy - 10, gx + 40, gy - 10, th.accent, 2.0)
    s.text(gx + 46, gy - 6, "$x$", 14, th.accent, "start")
    s.arrow(gx, gy - 16, gx, gy - 50, th.accent, 2.0)
    s.text(gx - 6, gy - 44, "$z$", 14, th.accent, "end")
    s.arrow(gx + 5, gy - 16, gx + 22, gy - 35, th.accent, 2.0)
    s.text(gx + 26, gy - 35, "$y$", 14, th.accent, "start")
    _label_block(
        s,
        592,
        238,
        ("in the ground,", "near the source (5.1.4)"),
        160,
        th.fg,
        "start",
        18,
    )
    s.line(gx, 345, gx, 380, th.muted, 0.9, dash="3,3")
    s.line(sc, gy + 30, sc, 380, th.muted, 0.9, dash="3,3")
    s.dim(gx, 372, sc, 372, "a set distance", size=12)
    _label_block(
        s,
        572,
        402,
        ("by a railway, e.g. 8 m from the nearest track",),
        308,
        th.muted,
        "start",
    )

    # A manhole, the disturbing body 5.1.4 names, and the clearance from it.
    # The fill first: the ground hatch hangs two strokes into the open shaft.
    s.rect(431, gy + 1, 28, 43, th.bg)
    s.line(430, gy, 430, 375, th.fg, 2.0)
    s.line(460, gy, 460, 375, th.fg, 2.0)
    s.line(430, 375, 460, 375, th.fg, 2.0)
    s.line(426, gy - 2, 464, gy - 2, th.fg, 3.0)
    _label_block(s, 424, 372, ("manhole, largest dimension $a$",), 340, th.muted, "end")
    s.line(460, 375, 460, 404, th.muted, 0.9, dash="3,3")
    s.line(gx, 380, gx, 404, th.muted, 0.9, dash="3,3")
    s.dim(460, 398, gx, 398, "≥ 1.5 × $a$", size=12)

    # The directions of 5.2. The x label goes under its arrow: set after the
    # head it reads as the first word of the line beside it.
    s.rect(520, 52, 350, 132, th.panel, th.muted, rx=6, sw=1.2)
    ox, oy = 556.0, 150.0
    _transducer_block(s, ox, oy + 6)
    s.arrow(ox, oy - 7, ox, oy - 48, th.accent, 2.0)
    s.text(ox + 6, oy - 42, "$z$", 14, th.accent, "start")
    s.arrow(ox + 7, oy, ox + 42, oy, th.accent, 2.0)
    s.text(ox + 26, oy + 18, "$x$", 14, th.accent)
    s.arrow(ox + 5, oy - 6, ox + 24, oy - 26, th.accent, 2.0)
    s.text(ox + 27, oy - 26, "$y$", 14, th.accent, "start")
    s.text(616, 76, "Directions (5.2)", 13, th.fg, "start", bold=True)
    _label_block(
        s,
        616,
        100,
        (
            "$z$ vertical, $x$ and $y$ horizontal",
            "at right angles and parallel to",
            "the main axes of the building,",
            "$x$ preferably to the source",
            "(by a railway, DIN 45672-1 differs)",
        ),
        246,
        th.fg,
        "start",
        18,
    )

    # --- The three couplings of 5.3 ------------------------------------------
    iy, ih = 424.0, 244.0
    for x0, w in ((30.0, 260.0), (302.0, 260.0), (574.0, 296.0)):
        s.rect(x0, iy, w, ih, "none", th.muted, rx=6, sw=1.2)
    k = 0.85  # px per mm for Figure 1
    r_disc, t_disc, r_foot = 75 * k, 16 * k, 5 * k

    # Figure 1 b): the disc on three rounded feet, on a hard surface.
    ax = 160.0
    title = "On a hard surface (5.3.2)"
    s.text(
        ax,
        iy + 22,
        title,
        s.fit_size([title], [13, 12], 244, bold=True),
        th.primary,
        bold=True,
    )
    _label_block(
        s, ax, iy + 42, ("Figure 1 b): three feet ≈ R5 on Ø 130",), 244, th.muted
    )
    slab = 540.0
    s.rect(50, slab, 220, 16, th.panel, th.fg, sw=1.6)
    d_bot = slab - r_foot
    s.rect(ax - r_disc, d_bot - t_disc, 2 * r_disc, t_disc, th.bg, th.fg, sw=1.8)
    for off in (-65 * k, 65 * k):  # the feet sit on the 130 mm circle
        cx = ax + off
        s.path(
            f"M {cx - r_foot} {d_bot} A {r_foot} {r_foot} 0 0 0 {cx + r_foot} {d_bot} Z",
            th.fg,
        )
    s.rect(ax - 13, d_bot - t_disc - 26, 26, 26, th.secondary, th.fg, rx=2.5, sw=1.4)
    s.line(ax - r_disc, d_bot, ax - r_disc, 580, th.muted, 0.9, dash="3,3")
    s.line(ax + r_disc, d_bot, ax + r_disc, 580, th.muted, 0.9, dash="3,3")
    s.dim(ax - r_disc, 576, ax + r_disc, 576, "Ø 150 mm", size=12)
    _label_block(
        s,
        ax,
        600,
        (
            "set down loose, peaks ≤ 3 m/s²:",
            "$z$ to 100 Hz, $x$ and $y$ to 40 Hz",
            "beyond: glued, screwed or plastered",
            "wax on tiles or parquet: $x$, $y$ to 80 Hz",
        ),
        244,
        th.fg,
    )

    # Figure 1 a): the disc on three spikes, through a soft covering.
    bx = 432.0
    title = "On a soft covering (5.3.3)"
    s.text(
        bx,
        iy + 22,
        title,
        s.fit_size([title], [13, 12], 244, bold=True),
        th.primary,
        bold=True,
    )
    _label_block(
        s, bx, iy + 42, ("Figure 1 a): three spikes, 15 mm, 15°",), 244, th.muted
    )
    s.rect(352, slab, 148, 14, th.panel, th.fg, sw=1.6)
    s.rect(352, slab - 10, 148, 10, th.bg, th.muted, sw=1.2, dash="3,2")  # covering
    spike, nut = 15 * k, 4.0
    p_bot = slab - spike - nut
    s.rect(bx - r_disc, p_bot - t_disc, 2 * r_disc, t_disc, th.bg, th.fg, sw=1.8)
    for off in (-65 * k, 65 * k):
        cx = bx + off
        s.rect(cx - 4, p_bot, 8, nut, th.fg)
        s.path(
            f"M {cx - 2} {p_bot + nut} L {cx + 2} {p_bot + nut} L {cx} {slab} Z", th.fg
        )
    s.rect(bx - 13, p_bot - t_disc - 26, 26, 26, th.secondary, th.fg, rx=2.5, sw=1.4)
    xd = bx + r_disc + 14
    s.line(
        bx + r_disc, p_bot - t_disc, xd + 4, p_bot - t_disc, th.muted, 0.9, dash="3,3"
    )
    s.line(500, slab, xd + 4, slab, th.muted, 0.9, dash="3,3")
    s.dim(xd, p_bot - t_disc, xd, slab, "≈ 35", size=12, label_side="right")
    _label_block(
        s,
        bx,
        583,
        (
            "hardened steel, about 2.5 kg",
            "with the transducer, pressed and",
            "tapped through the covering",
            "set down loose, peaks ≤ 3 m/s²:",
            "$z$ to 100 Hz, $x$ and $y$ to 40 Hz",
        ),
        244,
        th.fg,
    )

    # The ground spike of the note to 5.3.4.2 a).
    cxx = 722.0
    s.text(cxx, iy + 22, "In the ground (5.3.4)", 13, th.primary, bold=True)
    _label_block(s, cxx, iy + 42, ("5.3.4.2 a): the ground spike",), 280, th.muted)
    g2 = 486.0
    s.ground(g2, 600, 680)
    q = 0.25  # px per mm for the spike
    sx = 640.0
    length, tip, half = 500 * q, 150 * q, 30 * q
    s.path(
        f"M {sx - half} {g2} L {sx + half} {g2} L {sx + half} {g2 + length - tip} "
        f"L {sx} {g2 + length} L {sx - half} {g2 + length - tip} Z",
        th.panel,
        th.fg,
        1.6,
    )
    s.line(sx, g2, sx, g2 + length - 4, th.fg, 1.2)
    s.rect(sx - 60 * q / 2, g2 - 10 * q, 60 * q, 10 * q, th.fg)  # the striking plate
    _transducer_block(s, sx, g2 - 10 * q, 12)
    s.dim(sx - half - 14, g2, sx - half - 14, g2 + length, "≈ 500", size=11)
    _label_block(
        s,
        674,
        508,
        (
            "X section of two",
            "30 × 30 × 4 angles",
            "pointed over ≈ 150 mm",
            "plate ≈ 60 × 60 × 10 mm",
            "driven fully in",
        ),
        186,
        th.fg,
        "start",
        18,
    )
    _label_block(
        s,
        cxx,
        636,
        ("couplings in practice: up to 15 dB (5.3.4.1)",),
        280,
        th.secondary,
    )
    _label_block(
        s, cxx, 655, ("or buried, in a borehole, on a plate (Table 2)",), 280, th.muted
    )

    # --- The DIN 45669-1 chain the cable feeds ---------------------------------
    s.text(
        450,
        694,
        "What the cable feeds: the DIN 45669-1 chain, working range 1 Hz to 80 Hz",
        13,
        th.fg,
        bold=True,
    )
    by, bh, gap = 706.0, 44.0, 16.0
    s.arrow(30, by + bh / 2, 64, by + bh / 2, th.fg, 1.6)
    s.text(46, by + bh / 2 - 8, "$v(t)$", 13, th.fg)
    bw = (870.0 - 70.0 - 4 * gap) / 5
    stages = (
        ("band limitation", "0.8 Hz and 100 Hz, (3)"),
        ("KB weighting", "5.6 Hz, (4)"),
        ("running r.m.s.", "$τ$ = 0.125 s, (1)"),
        ("30 s clock intervals", "one maximum each"),
        ("displayed", "$KB_{Fmax}$ and $KB_{FTm}$"),
    )
    size1 = s.fit_size([a for a, _ in stages], [12, 11], bw - 8, bold=True)
    size2 = s.fit_size([b for _, b in stages], [11, 10], bw - 8)
    for j, (head, detail) in enumerate(stages):
        x0 = 70 + j * (bw + gap)
        s.rect(x0, by, bw, bh, th.panel, th.primary, rx=6, sw=1.6)
        s.text(x0 + bw / 2, by + 18, head, size1, th.fg, bold=True)
        s.text(x0 + bw / 2, by + 36, detail, size2, th.muted)
        if j < len(stages) - 1:
            s.arrow(
                x0 + bw + 1, by + bh / 2, x0 + bw + gap - 1, by + bh / 2, th.fg, 1.6
            )

    s.rect(120, 764, 660, 56, th.panel, th.fg, rx=6, sw=1.6)
    s.text(450, 788, "$KB_{FTm} = √((1/N) · Σ KB_{FTi}^2)$", 16, th.fg)
    s.text(
        450,
        810,
        "a clock maximum ≤ 0.1 enters as 0 and still counts in $N$ (Formula (2))",
        12,
        th.muted,
    )


def _d_railway_cross_section(s: SVG, th: Theme) -> None:
    """Where vibration next to a railway is measured (DIN 45672-1, Clauses 6 to 8).

    One measuring cross-section at right angles to the track (6.1): the
    emission point on the ground 8 m from the track axis (6.2.1.2), the
    transmission points at twice the distance each time out to 128 m
    (6.2.2), and the immission points on the building that DIN 45669-2,
    DIN 4150-2 and DIN 4150-3 place (6.2.3), with the axes of 6.4.1 on the
    ground and the turned axes of 6.4.4 in the building. The insets are the
    rest of 6.2 and 6.3: the cross-sections along a straight test section,
    the projected distances on an embankment or in a cutting (6.2.1.3), and
    the tunnel points of 6.2.1.5 with the lateral surface point of 6.2.2,
    drawn at 12 px per metre. The strip is the record those points give, cut
    into the three stretches of DIN 45672-2 Clause 5, and the two boxes are
    the minimum test-track length of the note to 7.3.1 and the event value
    of Formula (8) of DIN 45672-2.
    """
    gy = 250.0  # the ground surface of the cross-section
    x_axis = 118.0  # the track axis

    def at(r: float) -> float:
        # One step per doubling, which is how 6.2.2 lays the points out.
        return 226.0 + 100.0 * math.log2(r / 8.0)

    s.text(
        450,
        62,
        "One measuring cross-section, from the track to the building",
        16,
        th.fg,
        bold=True,
    )

    # --- The track at ground level, with a train on it, end-on
    s.ground(gy, 24, 876)
    s.line(x_axis, 106, x_axis, gy + 12, th.muted, 1.2, dash="10,4,2,4")
    s.text(x_axis, 96, "the track, at ground level", 13, th.fg)
    s.path(
        f"M {x_axis - 58} {gy} L {x_axis - 38} {gy - 16} "
        f"L {x_axis + 38} {gy - 16} L {x_axis + 58} {gy} Z",
        th.panel,
        th.fg,
        1.6,
    )
    s.rect(x_axis - 44, gy - 22, 88, 6, th.muted)  # sleeper
    for dx in (-27.0, 19.0):
        s.rect(x_axis + dx, gy - 32, 8, 10, th.fg)  # rail
        s.rect(x_axis + dx - 1, gy - 46, 10, 14, th.fg, rx=2)  # wheel
    s.rect(x_axis - 44, gy - 132, 88, 84, th.panel, th.fg, rx=12, sw=2.0)
    s.rect(x_axis - 30, gy - 118, 60, 22, th.bg, th.fg, rx=4, sw=1.2)

    # --- The axes of 6.4.1: x along the track, out of the page
    ox, oy = 318.0, 122.0
    s.arrow(ox, oy, ox + 54, oy, th.fg, 1.8)
    s.text(ox + 62, oy + 5, "$y$ across the track", 13, th.fg, "start")
    s.arrow(ox, oy, ox, oy - 40, th.fg, 1.8)
    s.text(ox + 8, oy - 36, "$z$ vertical", 13, th.fg, "start")
    s.circle(ox, oy, 7, th.bg, th.fg, 1.6)
    s.circle(ox, oy, 2.4, th.fg)
    s.text(ox - 12, oy + 5, "$x$ along the track", 13, th.fg, "end")

    # --- Emission and transmission points on the ground (6.2.1.2, 6.2.2)
    for r in (8, 16, 32, 64, 128):
        x = at(r)
        _accel(s, x, gy)
        s.arrow(x + 14, gy - 4, x + 14, gy - 34, th.accent, 1.6)
        s.text(x + 14, gy - 40, "$z$", 12, th.accent)
        s.text(x, gy + 26, f"{r} m", 13, th.fg)
    s.text(x_axis, gy + 26, "track axis", 12, th.muted)
    s.text(at(8), gy - 60, "undisturbed ground", 12, th.primary)
    s.text(
        (at(16) + at(128)) / 2,
        gy - 60,
        "the distance doubles at each step",
        12,
        th.accent,
    )

    # --- The building and its immission points (6.2.3, 6.4.4)
    s.text(781, 84, "the building", 12, th.muted)
    s.rect(690, gy - 158, 182, 10, th.panel, th.fg, sw=1.6)  # roof
    s.rect(696, gy - 148, 10, 148, th.panel, th.fg, sw=1.6)  # wall facing the track
    s.rect(856, gy - 148, 10, 148, th.panel, th.fg, sw=1.6)  # far wall
    s.rect(706, gy - 84, 150, 9, th.panel, th.fg, sw=1.6)  # floor slab
    s.rect(706, gy - 8, 150, 8, th.panel, th.fg, sw=1.4)  # ground slab
    s.rect(686, gy, 30, 26, th.panel, th.fg, sw=1.6)  # strip foundations
    s.rect(846, gy, 30, 26, th.panel, th.fg, sw=1.6)
    _accel(s, 781, gy - 84)
    s.arrow(795, gy - 88, 795, gy - 116, th.secondary, 1.6)
    s.text(803, gy - 110, "$z′$", 13, th.secondary, "start")
    s.text(781, 120, "floor", 12, th.fg)
    # The foundation point rests on the ground slab: DIN 45669-2, 5.1.2, keeps
    # it within 0,5 m of the ground surface, on the outer foundation or the
    # rising wall nearest the source.
    _accel_wall(s, 713, gy - 14, 12)
    s.arrow(732, gy - 14, 762, gy - 14, th.secondary, 1.6)
    s.text(768, gy - 20, "$y′$", 13, th.secondary, "start")
    s.text(745, gy - 38, "foundation", 12, th.fg)

    # --- The three ranges, under the ground
    band = gy + 40
    for x0, x1, colour, label in (
        (at(8) - 46, at(8) + 46, th.primary, "emission"),
        (at(16) - 40, at(128) + 40, th.accent, "transmission"),
        (684.0, 878.0, th.secondary, "immission"),
    ):
        s.rect(x0, band, x1 - x0, 24, th.panel, colour, rx=4, sw=1.8)
        s.text((x0 + x1) / 2, band + 17, label, 13, colour)
    s.text(
        450,
        gy + 88,
        "emission 8 m from the track axis, transmission at 16 m, 32 m, 64 m "
        "and 128 m; three directions, or $z$ alone on the ground",
        12,
        th.muted,
    )
    s.text(
        450,
        gy + 106,
        "immission points on foundations and floors, chosen after DIN 45669-2, "
        "DIN 4150-2 and DIN 4150-3",
        12,
        th.muted,
    )

    # --- Three insets
    top, h = 382.0, 206.0
    for x0, w in ((28.0, 250.0), (290.0, 280.0), (582.0, 290.0)):
        s.rect(x0, top, w, h, "none", th.muted, rx=6, sw=1.2)

    # In plan: cross-sections along a straight test section (6.3), and a
    # building turned by alpha with x' along its nearest wall (6.4.4).
    s.text(38, top + 26, "In plan", 13, th.fg, "start", bold=True)
    s.line(58, 436, 58, 452, th.muted, 0.9, dash="3,3")
    s.line(248, 436, 248, 452, th.muted, 0.9, dash="3,3")
    s.dim(58, 440, 248, 440, "100 m to 200 m", size=12)
    s.rect(40, 452, 226, 10, th.panel, th.fg, sw=1.4)
    s.line(36, 457, 270, 457, th.muted, 1.0, dash="10,4,2,4")
    for x, sw in ((106.0, 1.4), (153.0, 2.2), (200.0, 1.4)):
        s.line(x, 462, x, 536, th.primary, sw, dash="5,4")
        for y in (478.0, 496.0, 520.0):
            s.circle(x, y, 3.4, th.primary)
    alpha = math.radians(20.0)
    cx, cy, hw, hh = 153.0, 562.0, 23.0, 11.0

    def turned(dx: float, dy: float) -> tuple[float, float]:
        return (
            cx + dx * math.cos(alpha) - dy * math.sin(alpha),
            cy + dx * math.sin(alpha) + dy * math.cos(alpha),
        )

    corners = [turned(-hw, -hh), turned(hw, -hh), turned(hw, hh), turned(-hw, hh)]
    s.path(
        "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in corners) + " Z",
        th.panel,
        th.fg,
        1.6,
    )
    c0, c1 = corners[0], corners[1]
    s.line(c0[0], c0[1], c0[0] + 58, c0[1], th.muted, 1.0, dash="4,3")
    arc = 40.0
    s.path(
        f"M {c0[0] + arc:.1f} {c0[1]:.1f} A {arc} {arc} 0 0 1 "
        f"{c0[0] + arc * math.cos(alpha):.1f} {c0[1] + arc * math.sin(alpha):.1f}",
        "none",
        th.secondary,
        1.4,
    )
    s.text(c0[0] + 62, c0[1] + 10, "$α$", 13, th.secondary, "start")
    ex, ey = c1[0] + 26 * math.cos(alpha), c1[1] + 26 * math.sin(alpha)
    s.arrow(c1[0], c1[1], ex, ey, th.secondary, 1.6)
    s.text(ex + 6, ey + 8, "$x′$", 13, th.secondary, "start")
    plan = (
        "cross-sections at right angles to the track,",
        "for a track form mid-way along the straight",
    )
    size = s.fit_size(plan, (12, 11), 246)
    s.text(153, 606, plan[0], size, th.muted)
    s.text(153, 622, plan[1], size, th.muted)

    # Embankment and cutting: projected distances (6.2.1.3).
    s.text(300, top + 26, "Embankment and cutting", 13, th.fg, "start", bold=True)
    s.ground(548, 298, 428, hatch=18)
    s.path("M 300 548 L 316 510 L 340 510 L 356 548 Z", th.panel, th.fg, 1.6)
    s.rect(320, 504, 5, 6, th.fg)
    s.rect(331, 504, 5, 6, th.fg)
    s.line(328, 478, 328, 560, th.muted, 1.0, dash="10,4,2,4")
    for x, label in ((364.0, "8"), (390.0, "16"), (416.0, "32")):
        s.circle(x, 544, 4, th.primary, th.fg, 1.0)
        s.text(x, 568, label, 11, th.fg)
    s.text(340, 584, "embankment", 11, th.muted)
    s.line(431, 424, 431, 580, th.muted, 0.9, dash="3,3")
    s.path(
        "M 436 510 L 446 510 L 460 548 L 480 548 L 494 510 L 566 510",
        "none",
        th.fg,
        1.8,
    )
    xh = 440.0
    while xh < 566:
        if not 446 < xh < 494:
            s.line(xh, 510, xh - 8, 519, th.muted, 1.1)
        xh += 18
    s.rect(462, 542, 5, 6, th.fg)
    s.rect(473, 542, 5, 6, th.fg)
    s.line(470, 478, 470, 560, th.muted, 1.0, dash="10,4,2,4")
    for x, label in ((504.0, "8"), (528.0, "16"), (552.0, "32")):
        s.circle(x, 506, 4, th.primary, th.fg, 1.0)
        s.text(x, 530, label, 11, th.fg)
    s.text(470, 584, "cutting", 11, th.muted)
    bank = ("points at projected distances", "of 8 m, 16 m and 32 m")
    size = s.fit_size(bank, (12, 11), 276)
    s.text(430, 606, bank[0], size, th.muted)
    s.text(430, 622, bank[1], size, th.muted)

    # Tunnel, 12 px per metre: a two-track box, 10 m wide inside, 2.5 m of
    # cover; the points of 6.2.1.5 and the lateral surface point of 6.2.2.
    s.text(592, top + 26, "Tunnel", 13, th.fg, "start", bold=True)
    surface = 446.0
    s.ground(surface, 590, 866, hatch=18)
    s.rect(640, 476, 132, 92, th.panel, th.fg, sw=1.8)
    s.rect(646, 482, 120, 80, th.bg, th.fg, sw=1.4)
    for track_x in (682.0, 730.0):  # track axes 4 m apart
        # Standard gauge at the inset's own 12 px to the metre, which leaves
        # the invert point of 6.2.1.5 room between the two rails.
        s.rect(track_x - 10.6, 556, 4, 6, th.fg)
        s.rect(track_x + 6.6, 556, 4, 6, th.fg)
    s.text(652, 542, "1.5 m above the rail", 10, th.fg, "start")
    # The cover runs beside the point column, so both arrowheads stay visible.
    s.dim(694, surface, 694, 476, "cover", size=11, label_side="left")
    s.line(730, 476, 730, 426, th.muted, 1.0, dash="10,4,2,4")
    s.dim(730, 432, 826, 432, "≥ 8 m", size=11)
    for px, py in (
        (682.0, 562.0),  # invert, at a track centre
        (706.0, 562.0),  # invert, between the two tracks
        (646.0, 538.0),  # wall, 1.5 m above the top of rail
        (706.0, 482.0),  # middle of the roof
        (706.0, surface),  # ground surface above the tunnel centre
        (826.0, surface),  # ground surface, 8 m from the track axis
    ):
        s.circle(px, py, 4, th.primary, th.fg, 1.0)
    tunnel = (
        "invert at a track centre and between two tracks;",
        "beside it ≈ 2/3 of the cover out, but ≥ 8 m",
    )
    size = s.fit_size(tunnel, (12, 11), 286)
    s.text(727, 606, tunnel[0], size, th.muted)
    s.text(727, 622, tunnel[1], size, th.muted)

    # --- One passage and its three stretches (DIN 45672-2, Clause 5)
    def tx(t: float) -> float:
        return 140.0 + 23.6 * t  # 0 s to 30 s

    s.text(
        450,
        656,
        "One passage and its three stretches (DIN 45672-2, Clause 5)",
        14,
        th.fg,
        bold=True,
    )
    y0, a0 = 752.0, 22.0
    # The envelope of the guide's own record: quiet to 6 s, up over 3 s,
    # a pulse per bogie, down from 21 s to 24 s; the largest spike at 15.5 s.
    k_peak = round(15.5 / 0.05)
    trace = []
    for k in range(601):
        t = k * 0.05
        env = min(max((t - 6.0) / 3.0, 0.0), 1.0) * min(max((24.0 - t) / 3.0, 0.0), 1.0)
        bogie = 1.0 + 0.5 * math.sin(2 * math.pi * 1.6 * t) ** 2
        jitter = (
            1.0
            if k == k_peak
            else 0.62 + 0.3 * abs(math.sin(1.7 * k) * math.cos(0.37 * k))
        )
        amp = a0 * (0.05 + env * bogie * jitter)
        trace.append(
            f"{'M' if k == 0 else 'L'} {tx(t):.1f} "
            f"{y0 - amp if k % 2 == 0 else y0 + amp:.1f}"
        )
    s.path(" ".join(trace), "none", th.muted, 0.9)
    for y, t0, t1, colour in (
        (680.0, 0.0, 30.0, th.fg),
        (696.0, 6.75, 23.25, th.primary),
        (712.0, 13.5, 17.5, th.secondary),
    ):
        mid = (tx(t0) + tx(t1)) / 2
        s.arrow(mid - 4, y, tx(t0), y, colour, 1.6)
        s.arrow(mid + 4, y, tx(t1), y, colour, 1.6)
    s.text(132, 684, "$T_3$ the whole event", 12, th.fg, "end")
    s.text(132, 700, "$T_2$ the passage", 12, th.primary, "end")
    s.text(132, 716, "$T_1$ ≈ 4 s", 12, th.secondary, "end")
    s.text(
        tx(17.5) + 8,
        716,
        "the largest values near its middle",
        12,
        th.secondary,
        "start",
    )
    for t in (6.75, 23.25):
        s.line(tx(t), y0 - 30, tx(t), y0 + 34, th.primary, 0.9, dash="3,3")
    quarter = a0 * 1.25 / 4
    for t0, t1 in ((4.6, 8.6), (21.4, 25.4)):
        s.line(tx(t0), y0 - quarter, tx(t1), y0 - quarter, th.primary, 1.2, dash="2,2")
    s.text(
        tx(4.6) - 4,
        y0 - quarter + 4,
        "≈ ¼ of the most frequent maxima",
        11,
        th.primary,
        "end",
    )
    s.line(tx(0), 790, tx(30), 790, th.muted, 1.2)
    for t in range(0, 31, 5):
        s.line(tx(t), 790, tx(t), 795, th.muted, 1.2)
    for t, label in ((0, "0"), (10, "10"), (20, "20"), (30, "30 s")):
        s.text(tx(t), 808, label, 11, th.muted)

    # --- The two boxed equations
    box_y = 824.0
    s.rect(52, box_y, 386, 80, th.panel, th.primary, rx=6, sw=1.8)
    s.text(245, box_y + 26, "$l_{MG} = l_Z + r · v_Z / v_R$", 15, th.primary, bold=True)
    track = (
        "minimum test-track length for a point $r$ from the track axis;",
        "$l_Z$ train length, $v_Z$ its speed, $v_R$ Rayleigh wave speed",
    )
    size = s.fit_size(track, (12, 11), 370)
    s.text(245, box_y + 48, track[0], size, th.fg)
    s.text(245, box_y + 68, track[1], size, th.fg)
    s.rect(462, box_y, 386, 80, th.panel, th.secondary, rx=6, sw=1.8)
    s.text(
        655, box_y + 26, "$v_E = ṽ_3 · √(T_3$ / 3600 s)", 15, th.secondary, bold=True
    )
    s.text(655, box_y + 48, "the r.m.s. over $T_3$ referred to one hour;", 12, th.fg)
    s.text(655, box_y + 68, "the passages of an hour add in square", 12, th.fg)

    s.text(
        450,
        928,
        "a meter to DIN 45669-1 from 4 Hz to 315 Hz, every point recorded at once "
        "where possible (8.3)",
        12,
        th.muted,
    )
    s.text(
        450,
        946,
        "and a record without a train at the same points, with the same chain, "
        "to show the background (8.4)",
        12,
        th.muted,
    )


def _d_people_in_buildings(s: SVG, th: Theme) -> None:
    """The DIN 4150-2 measurement, from the floor panel to the verdict.

    Left, the room the standard measures in (5.2): a section through the
    dwelling with the triaxial transducer at the middle of the floor panel,
    x towards the source, the alternative place for the horizontals in a
    window recess, and the fourth channel DIN 45669-1, 5.1.2 puts beside the
    source. Right, what the meter does with the record (3.4 to 3.6): band
    limit, KB weighting, running r.m.s., and ten 30 s clocks of a steady
    source whose maximum is 0,25 and whose clock maximum r.m.s. is 0,23, with
    the day cut into its two assessment periods and the rest hours (3.7.3,
    3.7.4, 5.4). Across the bottom, the order of Figure 2 walked with those
    numbers against the guide values of a residential area (Table 1, row 4),
    and at the foot Formulae (3) and (4b).
    """

    def diamond(cx: float, cy: float, w: float, h: float) -> None:
        s.path(
            f"M {cx} {cy - h / 2} L {cx + w / 2} {cy} L {cx} {cy + h / 2} "
            f"L {cx - w / 2} {cy} Z",
            th.panel,
            th.fg,
            sw=1.8,
        )

    # --- Left: the section through the dwelling ------------------------------
    s.text(235, 90, "Where the transducers go", 16, th.fg, bold=True)
    gy = 500.0
    s.ground(gy, 24, 446)
    s.rect(150, 150, 288, 14, th.panel, th.fg, sw=1.8)  # roof slab
    s.rect(150, 164, 14, 70, th.panel, th.fg, sw=1.8)  # outer wall above the recess
    s.rect(150, 290, 14, 210, th.panel, th.fg, sw=1.8)  # outer wall below it
    s.line(153, 234, 153, 290, th.muted, 1.4)  # glazing
    s.rect(424, 164, 14, 336, th.panel, th.fg, sw=1.8)  # far outer wall
    s.rect(164, 330, 260, 16, th.panel, th.primary, sw=2.2)  # the floor panel
    s.rect(144, gy, 26, 18, th.panel, th.fg, sw=1.6)  # footings
    s.rect(418, gy, 26, 18, th.panel, th.fg, sw=1.6)

    # The source, and the waves it sends into the ground. The quarter of curve
    # and the foreground colour keep them apart from the ground hatching, which
    # slants the same way in the muted colour.
    s.rect(34, 454, 60, 46, th.panel, th.fg, rx=4, sw=2.2)
    s.circle(64, 477, 11, th.fg)
    s.circle(64, 477, 4, th.bg)
    for r in (26.0, 40.0, 54.0):
        s.path(
            f"M {64 + r} {gy} A {r} {r} 0 0 1 64 {gy + r}",
            "none",
            th.fg,
            sw=1.4,
            dash="5,5",
        )
    s.text(64, 444, "the source", 13, th.muted)
    # The fourth channel that tells the source from other disturbances.
    _transducer_block(s, 110, gy - 1, 12.0)
    s.text(64, 390, "a 4th channel", 12, th.muted)
    s.text(64, 406, "by the source", 12, th.muted)
    s.line(100, 412, 110, 486, th.muted, 1.0)

    # The triaxial transducer on its base, at the middle of the panel.
    xm = 294.0
    s.rect(xm - 18, 322, 36, 6, th.panel, th.fg, rx=1, sw=1.3)
    for fx in (xm - 13, xm, xm + 13):
        s.circle(fx, 329, 2, th.fg)
    _transducer_block(s, xm, 322, 18.0)
    s.arrow(xm, 302, xm, 258, th.primary, 2.2)
    s.text(xm, 250, "$z$", 15, th.primary, bold=True)
    s.arrow(xm - 11, 313, xm - 54, 313, th.primary, 2.2)
    s.text(xm - 62, 318, "$x$", 15, th.primary, "end", bold=True)
    # y leaves the section, so it is a foreshortened diagonal.
    s.arrow(xm + 8, 306, xm + 36, 284, th.primary, 2.2)
    s.text(xm + 42, 282, "$y$", 15, th.primary, "start", bold=True)
    s.text(xm, 196, "middle of the floor panel", 13, th.fg, bold=True)
    s.text(xm, 214, "where the vertical is usually strongest", 12, th.muted)
    s.person(392, 330, h=92)
    s.line(xm, 346, xm, 380, th.muted, 0.9, dash="3,3")
    s.dim(164, 374, xm, 374, "½ span", size=12)
    s.dim(xm, 374, 424, 374, "½ span", size=12)

    # The horizontals may also be taken in a recess of a rising wall.
    _transducer_block(s, 160, 290, 12.0)
    s.text(84, 200, "or, for $x$ and $y$,", 12, th.muted)
    s.text(84, 216, "right by a wall,", 12, th.muted)
    s.text(84, 232, "or in a door or", 12, th.muted)
    s.text(84, 248, "window recess", 12, th.muted)
    s.line(110, 256, 152, 280, th.muted, 1.0)

    for k, line in enumerate(
        (
            "on the floor of the room itself, where it vibrates most",
            "$x$ and $y$ along the outer walls, $x$ towards the source if possible",
            "three channels at once, or one after another if steady",
            "set down loose while peaks stay ≤ 3 m/s², horizontals to 40 Hz",
            "on a carpet, the spiked device, about 2.5 kg with the transducer",
        )
    ):
        s.text(235, 566 + 17 * k, line, 12, th.muted)

    # --- Right: what the meter makes of the record ---------------------------
    s.text(673, 90, "What the meter makes of the record", 16, th.fg, bold=True)
    for x, w, top, bottom in (
        (466.0, 112.0, "band limit", "1 Hz to 80 Hz"),
        (594.0, 130.0, "KB weighting", "$f_0$ = 5.6 Hz"),
        (742.0, 138.0, "running r.m.s.", "$τ$ = 0.125 s"),
    ):
        s.rect(x, 108, w, 44, th.panel, th.fg, rx=5, sw=1.6)
        s.text(x + w / 2, 126, top, 13, th.fg)
        s.text(x + w / 2, 144, bottom, 12, th.muted)
    s.arrow(580, 130, 592, 130, th.muted, 1.8)
    s.arrow(726, 130, 740, 130, th.muted, 1.8)

    x0, cw, yb, k_px = 506.0, 36.0, 300.0, 320.0

    def yv(v: float) -> float:
        return yb - k_px * v

    s.text(
        686,
        178,
        "10 clocks of 30 s over 5 min, in $x$, the governing direction",
        12,
        th.muted,
    )
    s.line(x0, 196, x0, yb, th.fg, 1.4)
    s.line(x0, yb, x0 + 10 * cw, yb, th.fg, 1.4)
    s.text(x0 - 8, 206, "$KB_F$", 13, th.fg, "end")
    s.line(x0, yv(0.1), x0 + 10 * cw, yv(0.1), th.muted, 1.0, dash="4,4")
    s.text(x0 - 8, yv(0.1) + 4, "0.1", 11, th.muted, "end")
    # Drawn heights only: their r.m.s. is 0,23 and the tenth is the 0,25.
    maxima = (0.22, 0.23, 0.22, 0.24, 0.22, 0.23, 0.22, 0.23, 0.22, 0.25)
    pts = []
    for k, m in enumerate(maxima):
        if k:
            s.line(x0 + cw * k, 212, x0 + cw * k, yb, th.muted, 0.9, dash="2,3")
        s.text(x0 + cw * k + cw / 2, 316, f"$T_{{{k + 1}}}$", 11, th.muted)
        for j in range(12):
            v = m - 0.06 * ((7 * j + 3 * k) % 5) / 4
            pts.append((x0 + cw * k + 1.5 + 3 * j, yv(v)))
    s.path(
        "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in pts),
        "none",
        th.primary,
        sw=1.3,
    )
    for k, m in enumerate(maxima):
        s.line(x0 + cw * k + 2, yv(m), x0 + cw * (k + 1) - 2, yv(m), th.secondary, 2.4)
    s.dim(x0, 204, x0 + cw, 204, "30 s", size=11)
    s.text(x0 + 10 * cw, 208, "$KB_{Fmax}$ = 0.25", 12, th.secondary, "end")
    s.text(686, 336, "each 30 s clock keeps its maximum $KB_{FTi}$", 12, th.muted)
    s.text(
        686,
        352,
        "maxima of 0.1 or less count as 0, and still count in $N$",
        12,
        th.muted,
    )
    s.rect(506, 366, 170, 28, th.panel, th.secondary, rx=14, sw=1.8)
    s.text(591, 385, "$KB_{Fmax}$ = 0.25", 13, th.secondary)
    s.rect(696, 366, 170, 28, th.panel, th.primary, rx=14, sw=1.8)
    s.text(781, 385, "$KB_{FTm}$ = 0.23, $N$ = 10", 13, th.primary)

    # The day from 22:00 to 22:00, so the night reads as one block.
    s.text(686, 424, "by day and by night, each on its own", 12, th.fg)
    bx, hp, by, bh = 506.0, 15.0, 436.0, 22.0
    s.rect(bx, by, 8 * hp, bh, th.muted, th.fg, sw=1.2)
    s.rect(bx + 8 * hp, by, 16 * hp, bh, th.panel, th.fg, sw=1.2)
    s.rect(bx + 8 * hp, by, hp, bh, th.accent, th.fg, sw=1.2)
    s.rect(bx + 21 * hp, by, 3 * hp, bh, th.accent, th.fg, sw=1.2)
    s.text(bx + 4 * hp, by + 16, "night 8 h", 11, th.bg)
    s.text(bx + 15 * hp, by + 16, "day 16 h", 11, th.fg)
    for h, lab in ((0, "22"), (8, "6"), (9, "7"), (21, "19"), (24, "22 h")):
        s.text(bx + h * hp, by + bh + 14, lab, 11, th.muted)
    s.text(686, 492, "rest hours on working days, recorded apart", 11, th.accent)

    s.text(686, 530, "guide values of a residential area", 12, th.fg, bold=True)
    s.text(686, 550, "by day: $A_u$ = 0.15, $A_o$ = 3, $A_r$ = 0.07", 12, th.fg)
    s.text(686, 568, "by night: $A_u$ = 0.1, $A_o$ = 0.2, $A_r$ = 0.05", 12, th.muted)

    # --- Bottom: the order of Figure 2, walked with those numbers -------------
    cy, dw, dh = 712.0, 140.0, 56.0
    met_y, not_y = 650.0, 774.0
    cols = (100.0, 284.0, 468.0, 634.0, 800.0)
    half = {2: 75.0, 3: 56.0}
    diamond(cols[0], cy, dw, dh)
    s.text(cols[0], cy + 5, "$KB_{Fmax}$ ≤ $A_u$ ?", 13, th.fg)
    diamond(cols[1], cy, dw, dh)
    s.text(cols[1], cy + 5, "$KB_{Fmax}$ ≤ $A_o$ ?", 13, th.fg)
    diamond(cols[2], cy, 150.0, dh)
    s.text(cols[2], cy - 1, "rare, short", 12, th.fg)
    s.text(cols[2], cy + 14, "events?", 12, th.fg)
    s.rect(cols[3] - 56, cy - 17, 112, 34, th.panel, th.primary, rx=5, sw=1.8)
    s.text(cols[3], cy + 5, "form $KB_{FTr}$", 13, th.primary)
    diamond(cols[4], cy, dw, dh)
    s.text(cols[4], cy + 5, "$KB_{FTr}$ ≤ $A_r$ ?", 13, th.fg)
    for i_from, i_to in ((0, 1), (1, 2), (2, 3), (3, 4)):
        s.arrow(
            cols[i_from] + half.get(i_from, dw / 2),
            cy,
            cols[i_to] - half.get(i_to, dw / 2) - 1,
            cy,
            th.fg,
            1.6,
        )
    s.text(192, cy - 6, "no", 11, th.muted)
    s.text(376, cy - 6, "yes", 11, th.muted)
    s.text(558, cy - 6, "no", 11, th.muted)
    for c in (cols[0], cols[2], cols[4]):
        s.line(c, cy - dh / 2, c, met_y, th.accent, 1.8)
        s.text(c + 8, met_y + 22, "yes", 11, th.accent, "start")
    s.arrow(cols[0], met_y, 485, met_y, th.accent, 1.8)
    s.arrow(cols[4], met_y, 657, met_y, th.accent, 1.8)
    s.rect(486, met_y - 14, 170, 28, th.panel, th.accent, rx=14, sw=2)
    s.text(571, met_y + 5, "requirement met", 13, th.accent, bold=True)
    for c in (cols[1], cols[4]):
        s.line(c, cy + dh / 2, c, not_y, th.secondary, 1.8)
        s.text(c + 8, not_y - 16, "no", 11, th.secondary, "start")
    s.arrow(cols[1], not_y, 349, not_y, th.secondary, 1.8)
    s.arrow(cols[4], not_y, 491, not_y, th.secondary, 1.8)
    s.rect(350, not_y - 14, 140, 28, th.panel, th.secondary, rx=14, sw=2)
    s.text(420, not_y + 5, "not met", 13, th.secondary, bold=True)
    s.text(cols[0], 760, "0.25 > 0.15", 12, th.muted)
    s.text(cols[1] - 8, 676, "0.25 ≤ 3", 12, th.muted, "end")
    s.text(cols[2] - 8, 676, "up to 3 a day", 12, th.muted, "end")
    s.text(cols[3], 758, "from $KB_{FTm}$ and $T_e$", 12, th.muted)
    s.text(cols[4] - 8, 676, "if $T_e$ ≤ 1.5 h", 12, th.accent, "end")

    # --- Foot: Formulae (3) and (4b) -----------------------------------------
    s.rect(30, 806, 840, 56, th.panel, th.fg, rx=6, sw=1.6)
    s.text(245, 840, "$KB_{FTm} = √((1/N) · Σ KB_{FTi}^2)$", 16, th.primary)
    s.text(660, 840, "$KB_{FTr} = KB_{FTm} · √(T_e / T_r)$", 16, th.secondary)


def _d_structural_damage_points(s: SVG, th: Theme) -> None:
    """Where DIN 4150-3 puts the transducers, and what each of them is read for.

    Three places on the building and one on a pipe beside it, all from 5.4:
    the three components close together in the lowest storey, on the outside
    wall or its foundation, preferably on the side facing the source and, on
    a building without a basement, no more than 0,5 m above ground level; the
    two horizontal components in or close to the outside wall in the topmost
    floor plane; the vertical component at about mid-span on the floors
    expected to move most (5.2); and on a buried pipe the transducers on the
    pipe itself, bared only at that point, with the ground above it only an
    estimate (D.1). The pipe is drawn beyond 2 m from the building, because
    inside that distance a house connection is judged by the building's own
    foundation values (5.3). The boxes at the foot are the quantity 5.1
    judges at each building point, and the first line under them is the
    dwelling of D.2.
    """

    def tag(x: float, y: float, label: str, colour: str) -> None:
        s.circle(x, y, 11, colour)
        s.text(x, y + 5, label, 13, th.bg, bold=True)

    def block(x: float, y: float, colour: str, size: float = 12.0) -> None:
        s.rect(x - size / 2, y - size / 2, size, size, colour, th.fg, rx=2, sw=1.2)

    s.text(
        450,
        84,
        "Three places on the building, and one on a pipe beside it",
        17,
        th.fg,
        bold=True,
    )

    # The building: three storeys of 88 px (about 3 m each), no basement.
    top, storey = 128.0, 88.0
    gy = top + 3 * storey  # ground level, y = 392
    xl, xi, xr = 320.0, 532.0, 744.0  # left outside, interior and right outside wall

    # The ground, and the source on it: a piling rig with its pile driven in.
    s.ground(gy, 20, 880)
    s.rect(30, gy - 30, 100, 30, th.panel, th.fg, rx=5, sw=2.2)
    s.rect(134, 180, 8, gy - 180, th.panel, th.fg, sw=1.8)
    s.rect(142, 196, 22, 40, th.panel, th.fg, rx=3, sw=2.0)
    s.rect(150, 236, 6, gy + 30 - 236, th.muted)
    s.text(24, 150, "the source", 14, th.fg, "start", bold=True)
    s.text(24, 170, "piling, blasting, traffic", 12, th.muted, "start")
    cx, cy = 153.0, gy + 30
    a0, a1 = math.radians(-15), math.radians(25)
    for r in (35.0, 65.0, 95.0):
        s.path(
            f"M {cx + r * math.cos(a0):.1f} {cy + r * math.sin(a0):.1f} "
            f"A {r} {r} 0 0 1 {cx + r * math.cos(a1):.1f} {cy + r * math.sin(a1):.1f}",
            stroke=th.secondary,
            sw=1.8,
            dash="6,4",
        )

    for x in (xl, xr):
        s.rect(x, top, 16, gy - top, th.panel, th.fg, sw=2.0)
    s.rect(xi, top + 12, 12, gy - top - 20, th.panel, th.fg, sw=1.8)
    for k in range(3):
        s.rect(xl, top + k * storey, xr + 16 - xl, 12, th.panel, th.fg, sw=1.8)
    s.rect(xl + 16, gy - 8, xr - xl - 16, 8, th.panel, th.fg, sw=1.8)
    for x, w in ((xl - 12, 40.0), (xi - 8, 28.0), (xr - 12, 40.0)):
        s.rect(x, gy, w, 30, th.panel, th.fg, sw=1.8)
    s.text((xl + xr + 16) / 2, gy + 54, "a dwelling with no basement", 13, th.muted)

    # 1: the lowest storey, on the outside wall that faces the source.
    y1 = gy - 14
    block(xl + 22, y1, th.secondary)
    s.ellipse(xl + 20, y1, 26, 26, "none", th.secondary, 1.4, dash="4,3")
    tag(xl + 62, y1 - 24, "1", th.secondary)

    # 2: the topmost floor plane, on the outside wall just under the top slab.
    # x points at the source, which is the preference of DIN 45669-2 5.2.
    y2 = top + 21
    block(xl + 22, y2, th.primary)
    s.arrow(xl + 14, y2, xl - 22, y2, th.primary, 2.0)
    s.text(xl - 26, y2 + 5, "$x$", 14, th.primary, "end")
    s.arrow(xl + 28, y2 + 6, xl + 48, y2 + 26, th.primary, 2.0)
    s.text(xl + 52, y2 + 36, "$y$", 14, th.primary, "start")
    tag(xl + 110, y2 + 14, "2", th.primary)

    # 3: a floor at mid-span, vertical only.
    slab = top + storey
    mid = (xi + 12 + xr) / 2
    block(mid, slab - 7, th.accent, size=14)
    s.arrow(mid, slab - 16, mid, slab - 56, th.accent, 2.0)
    s.text(mid + 8, slab - 44, "$z$", 14, th.accent, "start")
    s.dim(xi + 12, slab + 34, mid, slab + 34, "$l/2$", size=12)
    s.dim(mid, slab + 34, xr, slab + 34, "$l/2$", size=12)
    tag(mid - 44, slab - 40, "3", th.accent)

    # 4: a buried pipe running past the building, in cross-section, bared at
    # one point. It is further from the building than the 2 m inside which a
    # house connection takes the building's own foundation values (5.3).
    px, py, pr = 846.0, 446.0, 15.0
    s.circle(px, py, pr, th.panel, th.fg, 2.0)
    s.line(818, gy + 2, px - pr + 2, py - 8, th.muted, 1.2, dash="4,3")
    s.line(874, gy + 2, px + pr - 2, py - 8, th.muted, 1.2, dash="4,3")
    s.rect(px - 5, py - pr - 10, 10, 10, th.fg)
    s.line(px - pr, py, px - pr, gy - 10, th.muted, 1.0, dash="3,3")
    s.dim(xr + 16, gy - 14, px - pr, gy - 14, "> 2 m", size=13)
    tag(804, py, "4", th.fg)

    # Detail 1: the foundation point at 100 px to the metre.
    ay, ah = 476.0, 160.0
    s.rect(20, ay, 420, ah, "none", th.secondary, rx=6, sw=1.4, dash="6,4")
    tag(42, ay + 22, "1", th.secondary)
    s.text(
        60,
        ay + 27,
        "the foundation, on the source side",
        14,
        th.secondary,
        "start",
        bold=True,
    )
    s.text(60, ay + 48, "$x$, $y$, $z$ close together", 12, th.fg, "start")
    ga = ay + 118  # the ground level outside
    wx = 300.0
    s.ground(ga, 36, wx)
    s.rect(wx, ay + 56, 40, ga - ay - 56, th.panel, th.fg, sw=2.0)
    s.rect(wx - 12, ga, 64, 34, th.panel, th.fg, sw=2.0)
    s.rect(wx + 40, ga - 10, 90, 20, th.panel, th.fg, sw=1.8)
    s.text(wx - 8, ay + 50, "outside wall", 12, th.muted, "end")
    s.text(wx - 20, ga + 26, "wall foundation", 12, th.muted, "end")
    # On the inner face, 0,3 m above the ground outside.
    tx, ty = wx + 49, ga - 30
    s.rect(tx - 9, ty - 9, 18, 18, th.secondary, th.fg, rx=2.5, sw=1.4)
    s.arrow(tx, ty - 11, tx, ty - 44, th.secondary, 2.0)
    s.text(tx + 6, ty - 36, "$z$", 14, th.secondary, "start")
    s.arrow(tx - 11, ty, tx - 50, ty, th.secondary, 2.0)
    s.text(tx - 54, ty + 5, "$x$", 14, th.secondary, "end")
    s.arrow(tx + 8, ty - 8, tx + 28, ty - 26, th.secondary, 2.0)
    s.text(tx + 32, ty - 24, "$y$", 14, th.secondary, "start")
    lim = ga - 50  # 0,5 m above the ground outside
    s.line(60, lim, 430, lim, th.muted, 1.0, dash="4,3")
    s.dim(80, lim, 80, ga, "≤ 0.5 m", size=13, label_side="right")
    s.text(40, ga + 24, "ground level", 12, th.muted, "start")

    # Detail 4: the pipe, along its axis.
    bx0 = 460.0
    s.rect(bx0, ay, 420, ah, "none", th.fg, rx=6, sw=1.4, dash="6,4")
    tag(bx0 + 22, ay + 22, "4", th.fg)
    s.text(bx0 + 40, ay + 27, "the pipe, enlarged", 14, th.fg, "start", bold=True)
    s.text(bx0 + 404, ay + 27, "Table 2 by pipe material", 12, th.muted, "end")
    # The ground line breaks over the excavation, because the pipe is bared
    # only at the measuring point (D.1).
    gb = ay + 80
    s.ground(gb, bx0 + 16, bx0 + 80)
    s.ground(gb, bx0 + 220, bx0 + 404)
    pipe_y = ay + 120
    s.rect(bx0 + 20, pipe_y, 380, 18, th.panel, th.fg, rx=9, sw=2.0)
    s.line(bx0 + 80, gb + 2, bx0 + 96, pipe_y - 2, th.muted, 1.2, dash="4,3")
    s.line(bx0 + 220, gb + 2, bx0 + 204, pipe_y - 2, th.muted, 1.2, dash="4,3")
    t4x = bx0 + 130
    s.rect(t4x - 8, pipe_y - 16, 16, 16, th.fg, th.fg, rx=2, sw=1.2)
    s.arrow(t4x + 10, pipe_y - 8, t4x + 94, pipe_y - 8, th.fg, 2.0)
    s.text(t4x + 100, pipe_y - 4, "$x$ along the pipe axis", 12, th.fg, "start")
    s.arrow(t4x, pipe_y - 18, t4x, pipe_y - 56, th.fg, 2.0)
    s.text(t4x - 6, pipe_y - 48, "$z$", 13, th.fg, "end")
    s.arrow(t4x - 8, pipe_y - 18, t4x - 26, pipe_y - 36, th.fg, 2.0)
    s.text(t4x - 30, pipe_y - 34, "$y$", 13, th.fg, "end")
    s.text(
        bx0 + 16, ay + 152, "on the pipe, bared at this point only", 12, th.fg, "start"
    )
    sx = bx0 + 386
    s.rect(sx - 8, gb - 16, 16, 16, "none", th.muted, rx=2, sw=1.4, dash="3,2")
    s.line(sx, gb + 2, sx, pipe_y - 2, th.muted, 1.0, dash="2,3")
    s.text(
        sx - 16,
        ay + 52,
        "on the ground above it: only an estimate,",
        12,
        th.muted,
        "end",
    )
    s.text(sx - 16, ay + 70, "usually larger than on the pipe", 12, th.muted, "end")

    # What 5.1 and 5.2 read at each of the three building points.
    by, bw, bh = 654.0, 276.0, 84.0
    for x0, colour, num, head, formula, note in (
        (
            20.0,
            th.secondary,
            "1",
            "foundation, lowest storey",
            "$|v_i|_{max}$,  $i = x, y, z$",
            "Table 1 at the frequency of that peak",
        ),
        (
            312.0,
            th.primary,
            "2",
            "topmost floor plane",
            "$|v_i|_{max}$,  $i = x, y$",
            "one value per class, Tables 1 and 3",
        ),
        (
            604.0,
            th.accent,
            "3",
            "a floor, at mid-span",
            "$v_z ≤ 20$ mm/s",
            "short-term vibration",
        ),
    ):
        s.rect(x0, by, bw, bh, th.panel, colour, rx=6, sw=1.8)
        tag(x0 + 20, by + 20, num, colour)
        s.text(x0 + 38, by + 25, head, 13, colour, "start", bold=True)
        s.text(x0 + bw / 2, by + 52, formula, 16, th.fg)
        s.text(x0 + bw / 2, by + 74, note, 12, th.muted)

    s.text(
        450,
        766,
        "at the foundation of a dwelling: $v_z$ = 5.1 mm/s at $f_z$ = 16.5 Hz, "
        "against 6.6 mm/s read off Bild 1",
        13,
        th.fg,
    )
    s.text(
        450,
        790,
        "a vibration meter to DIN 45669-1, function-checked and calibrated at a "
        "reference frequency and amplitude for the job",
        12,
        th.muted,
    )
    s.text(
        450,
        810,
        "on a hard surface loose only to 100 Hz vertical and 40 Hz horizontal at "
        "3 m/s² or less; otherwise glued, screwed or plastered",
        12,
        th.muted,
    )
    s.text(
        450,
        830,
        "one horizontal axis along a side wall; a large footprint takes several "
        "points at once, a higher mode several storeys at once",
        12,
        th.muted,
    )
