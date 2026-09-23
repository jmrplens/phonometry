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
    # Left of the pedestal: centred on it, the pedestal, the arrow up it and
    # the person's shin all ran through the words.
    s.text(172, gy - 16, "vibration input", 15, th.secondary, "end", italic=True)
    s.person(178, gy, 176, seated=True)
    # Triaxial accelerometer at the seat/body interface with its x, y, z axes.
    ox, oy = 176.0, 420.0
    s.rect(ox - 9, oy - 8, 18, 16, th.secondary, th.fg, rx=2, sw=1.5)
    s.arrow(ox, oy - 8, ox, oy - 58, th.accent, 2.0)  # z (vertical)
    # Left of the axis and below the head, which it sat on at the top.
    s.text(ox - 8, oy - 30, "$z$", 15, th.accent, "end", bold=True)
    s.arrow(ox + 9, oy, ox + 62, oy, th.accent, 2.0)  # x (fore-aft)
    # Above the arrow's head, clear of the cushion's edge it sat on.
    s.text(ox + 62, oy - 8, "$x$", 15, th.accent, "start", bold=True)
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


def _d_meter_verification_bench(s: SVG, th: Theme) -> None:
    """ISO 8041-1 clause 12: one meter, fed two ways, and where each test sits.

    The top band is the mechanical frequency-response test of 12.11.2: the
    meter's own transducer and a calibrated laboratory reference on a
    vibration exciter, mounted to the ISO 16063-21 calibration procedure and
    stacked as Figure H.3 draws them, the input held constant on the
    reference while the meter's weighted reading is noted, which is
    Formula (9); the phase check of Annex H runs on an exciter of its own.
    The middle band is the electrical test of 12.11.3, the maker's substitute
    for the transducer (5.1) fed by a generator whose input signal value is
    adjusted to hold the reading, which is Formula (12), and the saw-tooth
    bursts of 12.13 with the Table 6 timing of Figure 3. The strip under them
    places every level those clauses name, each of them a band-limited
    indication at the reference frequency, inside the 60 dB linear operating
    range 5.7 asks for, and the box combines the two errors as 12.11.4 does,
    through Formula (10). The example is a whole-body meter: the 15,915 Hz
    reference frequency of Table 1, the Table 15 ranges, and the 100 Hz
    band-limiting corner of Table 3 behind the 2 ms fall time. Periodic
    verification is clause 14 and a different bench; this plate is the
    pattern evaluation, which is what its title says.
    """
    x_l = 40.0
    rx0, rw = 500.0, 210.0  # the column the meter's readings sit in

    # ------------------------------------------------------------------
    # 1. Mechanical: 12.11.2, with the phase check of Annex H beside it.
    # ------------------------------------------------------------------
    s.text(
        x_l,
        72,
        "Mechanical test: the whole meter on a vibration exciter (12.11.2)",
        15,
        th.primary,
        anchor="start",
        bold=True,
    )
    ex = 350.0
    s.text(
        ex + 40,
        102,
        "both transducers mounted as ISO 16063-21 describes",
        12,
        th.muted,
    )
    cab = 186.0
    s.rect(x_l, cab - 24, 100, 48, th.panel, th.fg, rx=6, sw=1.8)
    s.path(
        f"M {x_l + 18} {cab} C {x_l + 30} {cab - 22}, {x_l + 40} {cab - 22}, "
        f"{x_l + 50} {cab} S {x_l + 70} {cab + 22}, {x_l + 82} {cab}",
        stroke=th.primary,
        sw=2.0,
    )
    s.text(x_l + 50, cab + 44, "signal generator", 12, th.muted)
    s.arrow(x_l + 100, cab, 176, cab, th.fg, 1.8)
    # Annex H lists the exciter "with power amplifier" (H.2.3.3 d).
    s.path(
        f"M 178 {cab - 22} L 178 {cab + 22} L 214 {cab} Z",
        fill=th.panel,
        stroke=th.fg,
        sw=1.8,
    )
    s.text(196, cab + 44, "power", 12, th.muted)
    s.text(196, cab + 62, "amplifier", 12, th.muted)
    s.line(214, cab, 250, cab, th.fg, 1.8)
    s.line(250, cab, 250, 232, th.fg, 1.8)
    s.arrow(250, 232, 286, 232, th.fg, 1.8)

    # The exciter: body, base and the moving table.
    s.rect(ex - 62, 198, 124, 70, th.panel, th.primary, rx=8, sw=2.2)
    s.rect(ex - 76, 268, 152, 10, th.panel, th.fg, rx=2, sw=1.6)
    s.rect(ex - 34, 180, 68, 18, th.panel, th.fg, rx=2, sw=1.8)
    s.text(ex, 298, "vibration exciter", 12, th.muted)
    _motion_arrows(s, ex, 233, 17, th.secondary, 2.0)
    # Figure H.3 stacks them: the meter's transducer on the reference, and
    # 12.11.2 mounts both to the ISO 16063-21 calibration procedure.
    s.rect(ex - 15, 152, 30, 28, th.accent, th.fg, rx=2.5, sw=1.4)
    s.rect(ex - 12, 126, 24, 26, th.primary, th.fg, rx=2.5, sw=1.4)
    s.text(ex - 30, 136, "the meter's transducer", 12, th.primary, anchor="end")
    s.text(ex - 30, 162, "calibrated reference", 12, th.accent, anchor="end")
    s.line(ex - 26, 132, ex - 13, 139, th.muted, 0.9)
    s.line(ex - 26, 158, ex - 16, 164, th.muted, 0.9)

    # The two readings Formula (9) compares.
    s.line(ex + 12, 139, rx0, 139, th.primary, 1.6)
    s.line(ex + 15, 166, 466, 166, th.accent, 1.6)
    s.line(466, 166, 466, 220, th.accent, 1.6)
    s.line(466, 220, rx0, 220, th.accent, 1.6)
    s.rect(rx0, 112, rw, 56, th.panel, th.primary, rx=8, sw=2.0)
    s.text(rx0 + rw / 2, 135, "human-vibration meter", 13, th.fg, bold=True)
    s.text(rx0 + rw / 2, 156, "reads $a_{ind}$, weighted", 12, th.fg)
    s.rect(rx0, 192, rw, 56, th.panel, th.accent, rx=8, sw=2.0)
    s.text(rx0 + rw / 2, 215, "laboratory reference", 13, th.fg, bold=True)
    s.text(rx0 + rw / 2, 236, "measures $a_{in}$, unweighted", 12, th.fg)
    for k, line in enumerate(
        ("one weighting per", "application takes", "both tests", "(12.11.1)")
    ):
        s.text(790, 162 + 18 * k, line, 12, th.muted)

    s.text(
        x_l,
        328,
        "at $f_{ref}$ = 15.915 Hz, the band-limited reading 20 dB over the lower "
        "linearity limit fixes the input $a_{in}$",
        13,
        th.fg,
        anchor="start",
    )
    s.text(
        x_l,
        350,
        "in one-third-octave steps from 0.5 Hz to 160 Hz (Table 15, whole-body): "
        "$a_{in}$ held on the reference, $a_{ind}$ noted",
        13,
        th.fg,
        anchor="start",
    )
    s.text(
        x_l,
        372,
        "phase, where a peak, an MTVV or a VDV is read: on a vibration exciter, "
        "directly or by a tone and its third harmonic (Annex H)",
        12,
        th.muted,
        anchor="start",
    )
    s.line(x_l, 390, 860, 390, th.muted, 1.0, dash="6,6")

    # ------------------------------------------------------------------
    # 2. Electrical: 12.11.3, and the signal bursts of 12.13.
    # ------------------------------------------------------------------
    s.text(
        x_l,
        420,
        "Electrical test: a generator in place of the transducer (12.11.3, 12.13)",
        15,
        th.secondary,
        anchor="start",
        bold=True,
    )
    cab2 = 498.0
    # One generator, a sine for the sweep and a saw-tooth for the bursts.
    s.rect(x_l, cab2 - 24, 100, 48, th.panel, th.fg, rx=6, sw=1.8)
    s.path(
        f"M {x_l + 10} {cab2} C {x_l + 17} {cab2 - 16}, {x_l + 23} {cab2 - 16}, "
        f"{x_l + 28} {cab2} S {x_l + 40} {cab2 + 16}, {x_l + 46} {cab2}",
        stroke=th.primary,
        sw=1.8,
    )
    s.path(
        f"M {x_l + 54} {cab2} L {x_l + 62} {cab2 - 14} L {x_l + 62} {cab2 + 14} "
        f"L {x_l + 78} {cab2 - 14} L {x_l + 78} {cab2 + 14} L {x_l + 86} {cab2}",
        stroke=th.secondary,
        sw=1.8,
    )
    s.text(x_l + 50, cab2 + 44, "signal generator", 12, th.muted)
    s.arrow(x_l + 100, cab2, 184, cab2, th.fg, 1.8)
    # 12.13 puts the single-pole low-pass against the saw-tooth's switching
    # transients only, and prints its cut-off as an example.
    s.rect(186, cab2 - 22, 76, 44, th.panel, th.fg, rx=5, sw=1.6)
    s.path(
        f"M 198 {cab2 - 6} L 226 {cab2 - 6} Q 238 {cab2 - 6}, 250 {cab2 + 12}",
        stroke=th.fg,
        sw=1.6,
    )
    s.text(
        224,
        cab2 - 52,
        "single-pole low-pass for the saw-tooth, if needed",
        12,
        th.muted,
    )
    s.text(224, cab2 - 34, "e.g. 100 $f_2$ = 10 kHz", 12, th.muted)
    s.arrow(262, cab2, 294, cab2, th.fg, 1.8)
    # 5.1 NOTE: the three substitutes a maker may provide.
    s.rect(296, cab2 - 30, 160, 60, th.panel, th.secondary, rx=6, sw=2.0)
    s.text(376, cab2 - 10, "test point,", 12, th.fg)
    s.text(376, cab2 + 6, "dummy transducer", 12, th.fg)
    s.text(376, cab2 + 22, "or input adapter", 12, th.fg)
    s.text(376, cab2 + 48, "the maker's substitute (5.1)", 12, th.muted)
    s.arrow(456, cab2, rx0 - 2, cab2, th.fg, 1.8)
    s.text(478, cab2 - 10, "$u_{in}$", 13, th.secondary)
    s.rect(rx0, cab2 - 28, rw, 56, th.panel, th.primary, rx=8, sw=2.0)
    s.text(rx0 + rw / 2, cab2 - 5, "human-vibration meter", 13, th.fg, bold=True)
    s.text(rx0 + rw / 2, cab2 + 16, "shows $a_{ind}$ again", 12, th.fg)
    s.text(rx0 + rw / 2, cab2 - 38, "into its electrical input facility", 12, th.muted)
    s.line(rx0 + rw, cab2, 776, cab2, th.muted, 1.2, dash="4,3")
    s.rect(776, cab2 - 13, 26, 26, "none", th.muted, rx=2.5, sw=1.4, dash="4,3")
    s.text(789, cab2 + 38, "no transducer", 12, th.muted)

    # The saw-tooth bursts as Figure 3 draws them: two cycles, a linear rise
    # and a vertical fall, starting and ending on the baseline. Not to
    # scale, as Figure 3 is not.
    by = 614.0
    amp, per = 15.0, 20.0
    start = x_l + 40.0
    rep = 130.0

    def burst(x0: float) -> float:
        half = per / 2
        x = x0 + half + per
        s.path(
            f"M {x0} {by} L {x0 + half} {by - amp} L {x0 + half} {by + amp} "
            f"L {x} {by - amp} L {x} {by + amp} L {x + half} {by}",
            stroke=th.secondary,
            sw=1.8,
        )
        return x + half

    s.text(
        x_l,
        by - 30,
        "two-cycle bursts, as Figure 3 draws them",
        12,
        th.muted,
        anchor="start",
    )
    s.line(x_l, by, start, by, th.secondary, 1.8)
    e1 = burst(start)
    s.line(e1, by, start + rep, by, th.secondary, 1.8)
    e2 = burst(start + rep)
    s.line(e2, by, e2 + 22, by, th.secondary, 1.8)
    s.text(e2 + 34, by + 5, "//", 12, th.secondary)
    s.line(e2 + 46, by, e2 + 70, by, th.secondary, 1.8)
    e3 = burst(e2 + 70)
    s.line(e3, by, e3 + 14, by, th.secondary, 1.8)
    s.line(x_l, by - 22, x_l, by + 50, th.muted, 0.9, dash="3,3")
    s.line(e3 + 14, by - 22, e3 + 14, by + 50, th.muted, 0.9, dash="3,3")
    s.dim(x_l, by + 26, start, by + 26, "1 s", size=12)
    s.dim(start, by + 26, start + rep, by + 26, "10 s", size=12)
    s.dim(x_l, by + 50, e3 + 14, by + 50, "60 s", size=12)

    tx = 470.0
    s.text(
        tx,
        by - 26,
        "Table 6, whole-body: saw-tooth at 15.915 Hz",
        12,
        th.fg,
        anchor="start",
        bold=True,
    )
    s.text(tx, by - 6, "bursts of 1, 2, 4, 8 or 16 cycles", 12, th.fg, anchor="start")
    s.text(
        tx,
        by + 14,
        "the first at 1 s, one every 10 s, 60 s in all",
        12,
        th.fg,
        anchor="start",
    )
    s.text(
        tx,
        by + 34,
        "Table 8: what each weighting reads, within 10 % (VDV 12 %)",
        12,
        th.fg,
        anchor="start",
    )

    s.text(
        x_l,
        700,
        "at $f_{ref}$ the band-limited reading is again 20 dB over the lower limit, "
        "and the weighted one is $a_{ind}$",
        13,
        th.fg,
        anchor="start",
    )
    s.text(
        x_l,
        722,
        "in one-third-octave steps from 0.25 Hz to 160 Hz: $u_{in}$ set to show "
        "$a_{ind}$ again, signal plus noise at least 10 times the noise",
        13,
        th.fg,
        anchor="start",
    )
    s.text(
        x_l,
        744,
        "bursts on every time and frequency weighting after a steady sine at 50 % "
        "of the upper limit; fall time ≤ 1/(5 $f_2$) = 2 ms",
        13,
        th.fg,
        anchor="start",
    )
    s.line(x_l, 762, 860, 762, th.muted, 1.0, dash="6,6")

    # ------------------------------------------------------------------
    # 3. Where each level sits in the linear operating range (5.7, 12.11,
    #    12.13), drawn for the 60 dB that 5.7 sets as the least. Every
    #    marker is a band-limited indication at the reference frequency.
    # ------------------------------------------------------------------
    s.text(
        450,
        790,
        "Where each test sits in a linear operating range of 60 dB, "
        "the least 5.7 allows",
        14,
        th.fg,
        bold=True,
    )
    bar_y = 840.0
    x0db, px_db = 150.0, 10.0

    def at(db: float) -> float:
        return x0db + px_db * db

    s.rect(at(0), bar_y - 7, at(60) - at(0), 14, th.panel, th.fg, rx=3, sw=1.4)
    s.text(at(0) - 10, bar_y + 5, "lower limit", 12, th.muted, anchor="end")
    s.text(at(60) + 10, bar_y + 5, "upper limit", 12, th.muted, anchor="start")
    # Both frequency-response tests are set here, at the reference frequency.
    s.line(at(20), bar_y - 7, at(20), bar_y - 20, th.primary, 2.2)
    s.circle(at(20), bar_y, 5, th.primary)
    s.text(
        at(20),
        bar_y - 26,
        "at $f_{ref}$, 20 dB over the lower limit: both sweeps set",
        12,
        th.primary,
    )
    # The bursts: 50 % of the upper limit (-6.02 dB), then tenfold steps down
    # while the reading stays at least 3 times the lower limit (+9.54 dB):
    # 53.98, 33.98 and 13.98 dB, and the next, -6.02 dB, is out.
    first = 60.0 - 20.0 * 0.30103
    for k in range(3):
        s.circle(at(first - 20.0 * k), bar_y, 5, th.secondary)
    s.line(at(first), bar_y - 7, at(first), bar_y - 20, th.secondary, 2.2)
    s.text(
        at(first),
        bar_y - 26,
        "50 % of the upper limit: first bursts",
        12,
        th.secondary,
    )
    for k in range(2):
        xa, xb = at(first - 20.0 * k) - 8, at(first - 20.0 * (k + 1)) + 8
        s.arrow(xa, bar_y + 20, xb, bar_y + 20, th.secondary, 1.4)
        s.text((xa + xb) / 2, bar_y + 38, "÷ 10", 12, th.secondary)
    floor_db = 20.0 * 0.47712
    s.line(
        at(floor_db), bar_y - 7, at(floor_db), bar_y + 22, th.secondary, 1.4, dash="3,2"
    )
    s.text(at(floor_db), bar_y + 38, "3 × the lower limit", 12, th.secondary)
    # 12.13 raises the single-cycle bursts from that same level to overload.
    s.arrow(at(first) + 8, bar_y + 20, at(60) + 56, bar_y + 20, th.secondary, 1.4)
    s.text(
        860, bar_y + 38, "a single cycle up to overload", 12, th.secondary, anchor="end"
    )

    # ------------------------------------------------------------------
    # 4. Formulas (9) and (12), and how 12.11.4 joins them.
    # ------------------------------------------------------------------
    box = 896.0
    s.rect(x_l, box, 820, 94, th.panel, th.fg, rx=6, sw=1.6)
    s.text(
        x_l + 20,
        box + 26,
        "(9)  $ε(f) = [a_{ind}(f) − a_{in} w(f)] / [a_{in} w(f)] × 100 %$",
        14,
        th.primary,
        anchor="start",
    )
    s.text(x_l + 800, box + 26, "mechanical, $U$ ≤ 4.5 %", 12, th.muted, anchor="end")
    s.text(
        x_l + 20,
        box + 54,
        "(12)  $ε_{e}(f) = [u_{in}(f_{ref}) w(f_{ref}) / (u_{in}(f) w(f)) − 1] × 100 %$",
        14,
        th.secondary,
        anchor="start",
    )
    s.text(x_l + 800, box + 54, "electrical, $U$ ≤ 3 %", 12, th.muted, anchor="end")
    s.text(
        x_l + 20,
        box + 80,
        "(10)  $ε(f) = ε_{t}(f) + ε_{e}(f)$, with $ε_{t}$ taken from the weighting "
        "tested both ways: inside Table 5 with $U$ ≤ 5 % (12.11.4)",
        12,
        th.fg,
        anchor="start",
    )

    s.text(
        450,
        1012,
        "frequencies within ± 0.2 %, total distortion at most 5 % on the exciter "
        "and 0.1 % through the input (12.2)",
        12,
        th.muted,
    )
    s.text(
        450,
        1034,
        "one-off instrument (clause 13): frequency response on the exciter only, "
        "11 frequencies from 0.631 Hz to 125.9 Hz at 1.00 m/s², $U$ ≤ 4 %",
        12,
        th.muted,
    )


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


def _d_seat_test_rig(s: SVG, th: Theme) -> None:
    """The ISO 10326-1 laboratory test: two accelerometers and one ratio.

    The side view is the arrangement of Figures 1 and 3: the seat on the
    simulator platform, the test person on the semi-rigid disc of 5.2.3, the
    platform accelerometer inside the 200 mm circle 5.2.2 centres directly
    below the seat accelerometer, the backrest of 8.1.4 and the feet support
    of 8.2. The section is Figure 2. Both points go through the same weighted
    r.m.s. chain (5.1, 5.3), the seat runs have to agree within ± 5 % of their
    mean (10.2.1), and the boxed line is Formula (2) with the correction of
    Formula (4).
    """
    floor = 560.0
    plat_x, plat_w, plat_top, plat_h = 50.0, 316.0, 460.0, 26.0
    cushion_top = 346.0
    # The seat accelerometer sits midway between the ischial tuberosities, and
    # the platform one 36 px (90 mm at this scale) off the vertical through it.
    x_s, x_p = 244.0, 208.0

    s.text(
        450,
        92,
        "Where the vibration enters the seat, and where it reaches the person",
        17,
        th.fg,
        bold=True,
    )

    # --- Left: the rig from the side (Figures 1 and 3) ----------------------
    s.text(262, 136, "The seat on the simulator, from the side", 14, th.fg, bold=True)
    s.ground(floor, 40, 530)

    # The simulator under the platform, driving it along z.
    _exciter(s, 300, plat_top + plat_h, stinger=26, w=100, h=48, up=True)
    s.text(300, 541, "simulator", 12, th.muted)
    _motion_arrows(s, 88, 523, 22, th.secondary)
    s.text(100, 528, "$z$", 14, th.secondary, "start", bold=True)
    s.rect(plat_x, plat_top, plat_w, plat_h, th.panel, th.primary, rx=3, sw=2.2)
    s.text(plat_x + 12, plat_top + 18, "platform", 12, th.primary, "start")
    s.text(
        285,
        586,
        "$z$: the input and its $a_{wP}$ are set by the application standard (9.2)",
        12,
        th.muted,
    )

    # Seat base, suspension (a spring and a damper), pan and cushion.
    s.rect(222, 450, 116, 10, th.panel, th.fg, rx=2, sw=1.8)
    _spring_v(s, 258, 386, 450, th.fg, coils=4, width=10, sw=2.0)
    s.line(312, 386, 312, 414, th.fg, 2.0)
    s.rect(305, 410, 14, 34, th.panel, th.fg, rx=2, sw=1.6)
    s.line(312, 444, 312, 450, th.fg, 2.0)
    s.text(236, 414, "suspension", 12, th.muted, "end")
    s.rect(170, 374, 190, 12, th.panel, th.fg, sw=2.0)
    s.rect(170, cushion_top, 190, 28, th.panel, th.fg, rx=9, sw=2.0)

    # The backrest, 10° back from the vertical through its foot (8.1.4):
    # 148 px tall, so its top sits 148·tan 10° = 26 px further back.
    s.path(
        "M 170 346 L 188 346 L 162 198 L 144 198 Z", fill=th.panel, stroke=th.fg, sw=2.0
    )
    # The angle is marked at the top rear corner, the one place where a
    # vertical through a backrest edge stays clear of the outline.
    s.line(144, 198, 144, 300, th.muted, 1.0, dash="4,4")
    s.path("M 144 258 A 60 60 0 0 0 154.4 257.1", stroke=th.muted, sw=1.2)
    s.text(136, 262, "10° ± 5°", 12, th.muted, "end")

    # The feet support stands beside the platform, as Figure 3 draws it.
    s.rect(376, 492, 96, 8, th.panel, th.fg, rx=2, sw=1.6)
    s.line(388, 500, 388, floor, th.fg, 1.8)
    s.line(460, 500, 460, floor, th.fg, 1.8)

    # The test person, in the posture of Figure 3: the knee near 100°, the
    # ankle near 90°, the hand resting on the thigh, and the thigh clear of
    # the front of the cushion (8.2).
    s.ellipse(238, 326, 24, 9, th.muted)
    s.line(228, 318, 190, 226, th.muted, 3.4)
    s.circle(188, 216, 13, th.muted)
    s.line(200, 250, 242, 288, th.muted, 2.6)
    s.line(242, 288, 302, 324, th.muted, 2.6)
    s.line(230, 322, 362, 328, th.muted, 3.4)
    s.line(362, 328, 383, 490.5, th.muted, 3.0)
    s.line(383, 490.5, 428, 490.5, th.muted, 3.0)
    s.text(300, 232, "the test person", 12, th.muted, "start")

    # The semi-rigid disc on the cushion, its accelerometers at the centre.
    s.path(
        f"M 194 {cushion_top} L 194 342 C 222 342 228 336 {x_s} 336 "
        f"C 260 336 266 342 294 342 L 294 {cushion_top} Z",
        fill=th.secondary,
        stroke=th.fg,
        sw=1.4,
    )
    s.text(204, 334, "S", 14, th.secondary, bold=True)

    # The vertical through S, and P on the platform within 100 mm of it
    # (5.2.2 and the ≤ 100 of Figure 1).
    s.line(x_s, 336, x_s, plat_top, th.muted, 1.1, dash="9,3,2,3")
    s.rect(x_p - 7, plat_top - 14, 14, 14, th.primary, th.fg, rx=2.5, sw=1.3)
    s.line(x_p, plat_top - 14, x_p, plat_top - 22, th.fg, 1.3)
    s.text(x_p - 14, plat_top - 6, "P", 14, th.primary, "end", bold=True)
    y_dim = plat_top + plat_h + 22
    s.line(x_p, plat_top + plat_h, x_p, y_dim + 4, th.muted, 0.9, dash="3,3")
    s.line(x_s, plat_top + plat_h, x_s, y_dim + 4, th.muted, 0.9, dash="3,3")
    s.arrow(x_p + 18, y_dim, x_p, y_dim, th.muted, 1.2)
    s.arrow(x_s - 18, y_dim, x_s, y_dim, th.muted, 1.2)
    s.text(x_p - 8, y_dim + 5, "≤ 100 mm", 12, th.fg, "end")

    # --- Right, top: the disc in section (Figure 2) -------------------------
    # Across it is drawn at 1.1 px/mm and up at 4 px/mm, so the 12 mm can be
    # seen at all.
    s.text(715, 136, "The mounting disc, in section", 14, th.fg, bold=True)
    yb = 236.0
    s.path(
        f"M 578 {yb} L 578 224 C 650 224 670 188 715 188 "
        f"C 760 188 780 224 852 224 L 852 {yb} Z",
        fill=th.panel,
        stroke=th.secondary,
        sw=2.0,
    )
    s.rect(690, 204, 50, 26, th.bg, th.secondary, rx=8, sw=1.4)
    s.rect(706, 209, 18, 21, th.secondary, th.fg, rx=2, sw=1.3)
    s.rect(674, 230, 82, 6, th.fg, th.fg, sw=1.0)
    s.line(724, 210, 764, 176, th.muted, 1.0)
    s.text(770, 176, "accelerometers", 12, th.muted, "start")
    # The metal disc is 82 px across and its label 81, so the label goes
    # beside the dimension rather than between its witness lines.
    s.dim(674, yb, 756, yb, "", offset=26, size=12)
    s.text(764, 266, "Ø 75 ± 5 mm", 12, th.fg, "start")
    s.dim(578, yb, 852, yb, "Ø 250 ± 50 mm", offset=54, size=13)
    s.line(566, 188, 700, 188, th.muted, 0.9, dash="3,3")
    s.dim(566, 188, 566, yb, "≤ 12 mm", size=12)
    body = "metal disc 1.5 ± 0.2 mm thick, rim 3 ± 1 mm"
    material = "rubber or plastics, 80 to 90 durometer (A)"
    size = s.fit_size([body, material], (12, 11), 300)
    s.text(715, 312, body, size, th.muted)
    s.text(715, 330, material, size, th.muted)

    # --- Right, middle: the same chain at both points (5.1, 5.3, 10.2.1) ----
    s.text(715, 360, "The same chain at both points", 14, th.fg, bold=True)
    for cx, label, colour in (
        (637.0, "P: platform", th.primary),
        (795.0, "S: seat pan", th.secondary),
    ):
        s.rect(cx - 75, 376, 150, 34, th.panel, colour, rx=8, sw=1.8)
        s.text(cx, 398, label, 13, colour, bold=True)
        s.arrow(cx, 410, cx, 430, th.fg, 1.6)
        s.arrow(cx, 468, cx, 488, th.fg, 1.6)
    s.rect(562, 430, 308, 38, th.panel, th.fg, rx=8, sw=1.6)
    s.text(716, 454, "weighted r.m.s., to ISO 8041 (5.3)", 13, th.fg)
    for cx, symbol, first, second, colour in (
        (
            637.0,
            "$a_{wP}$",
            "mean of the same runs,",
            "input within tolerance",
            th.primary,
        ),
        (795.0, "$a_{wS}$", "mean of 3 runs, each", "within ± 5 % of it", th.secondary),
    ):
        s.rect(cx - 75, 488, 150, 72, th.panel, colour, rx=8, sw=1.8)
        s.text(cx, 512, symbol, 16, colour, bold=True)
        size = s.fit_size([first, second], (11, 10), 136)
        s.text(cx, 532, first, size, th.muted)
        s.text(cx, 548, second, size, th.muted)

    # --- Foot: the conditions, then the two formulae ------------------------
    notes = (
        "P on the platform, inside a 200 mm circle centred directly below S, "
        "aligned with the platform motion (5.2.2)",
        "S at the centre of the disc, the disc taped so S sits midway between "
        "the ischial tuberosities, axes within 15° (5.2.3)",
        "the seat run in first under a 75 kg inert mass; a warm-up of up to "
        "10 min before each series helps (8.1.2, 10.2.1)",
        "two test persons, weighed before each series; the feet support set so "
        "the thighs do not press the cushion front (8.2)",
    )
    for i, note in enumerate(notes):
        y = 616 + 20 * i
        s.circle(52, y - 5, 3.4, th.secondary)
        s.text(64, y, note, 12, th.fg, "start")

    s.rect(70, 700, 760, 72, th.panel, th.fg, rx=6, sw=1.6)
    s.text(290, 732, "$SEAT = a_{wS} / a_{wP}$", 18, th.fg)
    s.text(640, 732, "$a^*_{wS} = SEAT · a^*_{wP}$", 18, th.fg)
    s.text(
        450,
        758,
        "Formula (2), and Formula (4) for the magnitude corrected to the "
        "intended input (10.2.3)",
        13,
        th.muted,
    )


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
    # A size smaller where the box would not hold it, as the Spanish at 15.
    mounting = "Mounting sets the usable upper frequency"
    s.text(
        70,
        386,
        mounting,
        s.fit_size([mounting], [15, 14, 13], 360, bold=True),
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
    # The direct rig 30 px right of where it stood, so that the note on the
    # transverse check fits to its left: there, the spring and the force
    # transducer ran through the Spanish of both lines.
    for cx, head in (
        (280.0, "Direct method (Part 2)"),
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
    transverse = (
        "$a′_1$: unwanted transverse input,",
        "≥ 15 dB below $a_1$ (Inequality 3)",
    )
    size = s.fit_size(list(transverse), [12, 11], 240)
    s.text(24, 280, transverse[0], size, th.secondary, anchor="start")
    s.text(24, 297, transverse[1], size, th.secondary, anchor="start")
    s.line(150, 270, 340, 204, th.muted, 1.0, dash="3,3")

    # ===== Direct output: blocked, force transducer on a rigid foundation ===
    cx = 280.0
    s.rect(cx - 30, 310, 60, 18, th.secondary, th.fg, rx=3, sw=1.6)
    # Clear of the top of the foundation, which ran along the letters at 326.
    s.text(cx + 52, 321, "force transducer", 13, th.secondary, anchor="start")
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
    # The actuator a little left of the spring's axis and its note a size
    # smaller where needed, right-aligned on the frame's own leg: with the
    # box centred on the axis, the note ran into it in both languages.
    s.rect(604, 712, 64, 34, th.panel, th.secondary, rx=4, sw=2.0)
    s.arrow(660, 748, 660, 768, th.secondary, 2.2)
    actuator = ("actuator: 100 % of the", "permissible static load")
    size = s.fit_size(list(actuator), [12, 11], 136)
    s.text(812, 734, actuator[0], size, th.secondary, anchor="end")
    s.text(812, 752, actuator[1], size, th.secondary, anchor="end")
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
    # Both floor labels on the top face, between its edges and the paths:
    # the i sat on the face's slanted left edge and the j on its right end.
    s.text(556, 424, "$i$", 19, th.primary, bold=True)
    s.text(658, 200, "$j$", 19, th.secondary, bold=True)
    s.text(720, 396, "$j$", 19, th.secondary, bold=True)
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
        # Beyond the plate's right end, clear of the impedance head's name.
        s.text(x0 + 312, gy + 44, "subsystem 1", 15, th.primary, anchor="start")
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
            # Clear below the plate's front face, whose lower edge ran along
            # the top of the words at gy + 20.
            s.text(
                x0 + 176, gy + 28, "impedance head", 13, th.secondary, anchor="start"
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
    # Under the two bodies, above the baseplate: over the coupling, the name
    # ran across the corners of both bodies.
    s.text(421, shaft_y + 72, "coupling", 13, th.accent)
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
    # Level with the quarter line rather than dropped onto it: 4 px lower,
    # its descenders sat on the start of the trace.
    s.text(
        tx(4.6) - 4,
        y0 - quarter,
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


def _d_vibration_prediction_path(s: SVG, th: Theme) -> None:
    """The geometry DIN 4150-1 predicts along, from the source to the floor.

    Clause 4.2 splits the ground at the reference distance of Formula (1),
    counted from the centre of the source: nearer than it nothing the clause
    gives holds, beyond it the amplitude falls by Formula (2) with the exponent
    Figure 1 reads off three questions and the damping of the ground. Clause
    4.3 then takes the building as one mass on the ground's spring, Formula
    (3), passes the ground's amplitude through the foundation and up to the
    floors with a maximum transfer value for each, and gives the storey
    formula, Formula (4), for the lowest horizontal frequency. The drawing is
    not to scale; the numbers in the panels are the ones the clauses print.
    """
    gy = 320.0  # the ground surface
    xc = 120.0  # the centre of the source, where R and R_1 are counted from
    xa0, xa1 = 80.0, 160.0  # the extent a along the direction of propagation
    xr1 = 340.0  # the far-field boundary R_1
    xr = 560.0  # a point in the far field at distance R
    xb0, xb1 = 640.0, 800.0  # the walls of the building

    s.text(
        450,
        74,
        "Through the ground to the building, and up to its floors",
        17,
        th.fg,
        bold=True,
    )

    # The near field, shaded first so everything in it is drawn over it.
    s.rect(xc, 176, xr1 - xc, gy - 176, th.panel)
    s.text((xc + xr1) / 2, 196, "near field", 14, th.muted, bold=True)
    s.text((xc + xr1) / 2, 216, "$R < R_1$", 13, th.muted)
    s.text((xc + xr1) / 2, 236, "the approximations do not hold", 12, th.muted)

    # The ground, broken under the building, where it is drawn as a spring.
    s.ground(gy, 30, xb0 - 10)
    s.ground(gy, xb1 + 10, 870)

    # The source and its extent along the path.
    s.text(xc, 256, "the source", 13, th.fg)
    s.rect(xa0, gy - 32, xa1 - xa0, 32, th.panel, th.fg, rx=4, sw=2.2)
    s.circle(xc, gy - 16, 9, th.fg)
    s.circle(xc, gy - 16, 4, th.bg)
    s.dim(xa0, 282, xa1, 282, "$a$", size=14)

    # The boundary of Formula (1).
    s.line(xr1, 176, xr1, 392, th.secondary, 2.0, dash="7,5")
    s.text(xr1, 166, "$R_1$", 15, th.secondary, bold=True)

    # The far field and the decay of Formula (2), drawn to the plate's own
    # dimension chain: the geometric part is the exponent 1 counted from the
    # centre of the source, with a little material damping on top; the arrows
    # are velocity amplitudes.
    s.text(490, 196, "far field", 14, th.primary, bold=True)
    s.text(490, 216, "$R > R_1$, Formula (2)", 13, th.muted)
    s.text(490, 236, "a source near the surface", 12, th.muted)
    s.text(490, 252, "sends mostly a Rayleigh wave", 12, th.muted)
    x0, h0 = xr1 + 14, 50.0

    def height(x: float) -> float:
        return h0 * (x0 - xc) / (x - xc) * math.exp(-(x - x0) / 900.0)

    steps = int((xr - x0) / 4)
    envelope = [(x0 + 4.0 * k, gy - 4 - height(x0 + 4.0 * k)) for k in range(steps + 1)]
    s.path(
        "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in envelope),
        stroke=th.primary,
        sw=1.4,
        dash="5,4",
    )
    s.arrow(x0, gy - 2, x0, gy - 4 - height(x0), th.primary, 2.4)
    s.text(x0, gy - 12 - height(x0), "$v̄_1$", 15, th.primary)
    s.arrow(450.0, gy - 2, 450.0, gy - 4 - height(450.0), th.primary, 2.4)
    s.arrow(xr, gy - 2, xr, gy - 4 - height(xr), th.primary, 2.4)
    s.text(xr + 8, gy + 2 - height(xr), "$v̄$", 15, th.primary, "start")

    # Body waves under the surface, as fronts centred on the source and cut
    # at a common depth so they clear the dimension chain.
    for rx, sweep in ((290.0, 32.0), (360.0, 25.0), (430.0, 20.5)):
        front = [
            (
                xc + rx * math.cos(math.radians(sweep * k / 12)),
                gy + 2 + 0.45 * rx * math.sin(math.radians(sweep * k / 12)),
            )
            for k in range(13)
        ]
        s.path(
            "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in front),
            stroke=th.muted,
            sw=1.4,
            dash="4,4",
        )
    s.text(428, 408, "body waves: compression and shear", 12, th.muted)

    # Formula (1) as a chain of dimensions from the centre of the source.
    s.line(xc, gy - 32, xc, 448, th.muted, 0.9, dash="3,3")
    s.line(xa1, gy, xa1, 356, th.muted, 0.9, dash="3,3")
    s.line(xr, gy, xr, 448, th.muted, 0.9, dash="3,3")
    s.dim(xc, 350, xa1, 350, "$a/2$", size=13)
    s.dim(xa1, 350, xr1, 350, "$λ_R$", size=14)
    s.dim(xc, 384, xr1, 384, "$R_1 = a/2 + λ_R$", size=14)
    s.dim(xc, 440, xr, 440, "$R$", size=14)
    s.text(340, 464, "$R_1$ is counted from the centre of the source", 12, th.muted)

    # The building of 4.3: five storeys on a foundation, one floor bending.
    top, storey = 138.0, 34.0
    xm = (xb0 + xb1) / 2
    s.rect(xb0 - 10, 308, xb1 - xb0 + 20, 12, th.panel, th.fg, sw=2.0)
    s.line(xb0, top, xb0, 308, th.fg, 2.2)
    s.line(xb1, top, xb1, 308, th.fg, 2.2)
    for k in range(5):
        y = top + k * storey
        if k == 2:
            s.path(
                f"M {xb0} {y} Q {xm} {y + 14} {xb1} {y}", stroke=th.secondary, sw=2.6
            )
        else:
            s.line(xb0, y, xb1, y, th.fg, 2.6)
    s.arrow(xm, top + 2 * storey + 4, xm, top + 2 * storey + 22, th.secondary, 2.0)
    s.text(xb0 - 10, top + 2 * storey + 6, "$V_D$", 15, th.secondary, "end")
    s.text(xm, top + 3.5 * storey + 5, "$m_B$", 15, th.fg)
    s.text(xb0 - 18, 312, "$V_F$", 15, th.secondary, "end")

    # Formula (4): the lowest horizontal natural frequency, a sway at the roof.
    s.arrow(xb1 + 14, top, xb1 + 52, top, th.accent, 2.0)
    s.arrow(xb1 + 52, top, xb1 + 14, top, th.accent, 2.0)
    s.text(xb1 + 33, top - 10, "$f_1$", 15, th.accent)

    # Formula (3): the ground under the building as a spring with the system
    # damping of the building on it.
    base = 366.0
    s.ground(base, xb0 - 10, xb1 + 10)
    for xs in (xb0 + 25, xb1 - 25):
        _spring_v(s, xs, gy, base, th.accent, coils=3, width=8.0, sw=1.8)
    s.line(xm, gy, xm, 338, th.accent, 1.8)
    s.line(xm - 8, 338, xm + 8, 338, th.accent, 2.4)
    s.path(
        f"M {xm - 11} 330 L {xm - 11} 352 L {xm + 11} 352 L {xm + 11} 330",
        stroke=th.accent,
        sw=1.8,
    )
    s.line(xm, 352, xm, base, th.accent, 1.8)
    s.text(xb0 + 12, 348, "$k_B$", 14, th.accent, "end")
    s.text(xm + 18, 348, "$D_0$", 14, th.accent, "start")
    s.text(xm, 396, "five storeys, the ground a spring", 12, th.muted)
    s.text(xm, 414, "under a mass moving in phase", 12, th.muted)

    # Three panels: Figure 1, the attenuation of 4.2, and the building of 4.3.
    py, ph = 492.0, 196.0
    for x, pw, colour in (
        (30.0, 256.0, th.primary),
        (295.0, 270.0, th.accent),
        (574.0, 296.0, th.secondary),
    ):
        s.rect(x, py, pw, ph, th.panel, colour, rx=6, sw=1.8)

    x, pw = 30.0, 256.0
    s.text(x + pw / 2, py + 26, "the exponent $n$, Figure 1", 14, th.primary, bold=True)
    s.line(x + pw / 2, py + 40, x + pw / 2, py + 124, th.muted, 1.0)
    s.text(x + 64, py + 52, "adds 0", 12, th.muted)
    s.text(x + 192, py + 52, "adds 0.5", 12, th.muted)
    for k, (plain, more) in enumerate(
        (
            ("line source", "point source"),
            ("harmonic", "impulsive"),
            ("surface wave", "body wave"),
        )
    ):
        s.text(x + 64, py + 78 + 20 * k, plain, 13, th.fg)
        s.text(x + 192, py + 78 + 20 * k, more, 13, th.fg)
    s.text(x + pw / 2, py + 152, "$n$ = 0, 0.5, 1 or 1.5", 14, th.fg)
    s.text(x + pw / 2, py + 176, "a train of point sources: 0.3 to 0.5", 12, th.muted)

    x, pw = 295.0, 270.0
    s.text(
        x + pw / 2, py + 26, "the attenuation coefficient $α$", 14, th.accent, bold=True
    )
    s.text(x + pw / 2, py + 54, "$α ≈ 2πD/λ$, with $λ = c/f$", 14, th.fg)
    s.text(x + pw / 2, py + 80, "a first estimate on loose ground:", 12, th.fg)
    s.text(x + pw / 2, py + 98, "$D$ ≤ 0.01, more has to be proven", 12, th.fg)
    s.text(x + pw / 2, py + 124, "higher frequencies are damped more", 12, th.fg)
    s.text(x + pw / 2, py + 158, "$D$ = 0.01 and $λ$ = 12.5 m", 12, th.muted)
    s.text(x + pw / 2, py + 176, "give $α$ = 0.005 1/m", 12, th.muted)

    x, pw = 574.0, 296.0
    s.text(
        x + pw / 2, py + 26, "the building on its ground", 14, th.secondary, bold=True
    )
    for dy, row in (
        (48, "$f_B$: about 15 Hz for 1 to 2 storeys,"),
        (65, "8 Hz to 12 Hz for 2 to 6 storeys,"),
        (82, "under 8 Hz for more than 6,"),
        (99, "medium-stiff ground, $c_s$ = 150 m/s to 200 m/s"),
        (123, "$V_F$ at $f_B$: at most 2 on loose ground,"),
        (140, "a mean of 0.5 above $f_B$, no reduction on rock"),
        (164, "$V_D$: 10 to 25 at the floor resonance,"),
        (181, "with $0.02 < D_1 < 0.05$ in reinforced concrete"),
    ):
        s.text(x + pw / 2, py + dy, row, 12, th.fg)

    # The formulae the whole path is built from.
    by = 710.0
    s.rect(30, by, 405, 100, th.panel, th.primary, rx=6, sw=1.8)
    s.text(232, by + 30, "$R_1 = a/2 + λ_R$", 15, th.primary)
    s.text(232, by + 60, "$v̄ = v̄_1 · (R/R_1)^{−n} · exp[−α(R − R_1)]$", 15, th.primary)
    s.text(232, by + 86, "Formulae (1) and (2), for the far field", 12, th.muted)
    s.rect(465, by, 405, 100, th.panel, th.secondary, rx=6, sw=1.8)
    s.text(572, by + 30, "$f_B = √(k_B/m_B)/2π$", 15, th.secondary)
    s.text(770, by + 30, "$f_1 ≈ 10/n$ Hz, $n ≥ 5$", 15, th.secondary)
    s.text(572, by + 60, "$V_F = 1/(2D_0)$", 15, th.secondary)
    s.text(770, by + 60, "$V_D = 1/(2D_1)$", 15, th.secondary)
    s.text(
        667,
        by + 86,
        "Formulae (3) and (4), and the transfer values of 4.3",
        12,
        th.muted,
    )

    s.text(
        450,
        838,
        "the transfer values assume the whole building excited in phase by "
        "predominantly harmonic vibration;",
        12,
        th.muted,
    )
    s.text(
        450,
        858,
        "a source close by, moving or impulsive leaves them on the safe side",
        12,
        th.muted,
    )


# ---------------------------------------------------------------------------
# E DIN 45672-3: the prediction chain from the track to a floor
# ---------------------------------------------------------------------------


def _d_railway_prediction_chain(s: SVG, th: Theme) -> None:
    """E DIN 45672-3 Formula (1) drawn over the place it describes.

    The section is Figure 1 of the draft with the four points the terms of
    Formula (1) run between: the emission at a known distance from the track
    centre (5.2), a point of the ground in front of the building (5.3), the
    foundation (5.4.2) and the middle of a storey floor, vertical (3.3 and
    5.1). Those four points are the general case of 5.1 to 5.4, not the
    worked example, whose emission spectrum is taken at the foundation, so
    that its ground-to-foundation term drops out; what the example does give
    the plate are its numbers: 50 km/h, 7 m from the track centre to the
    building, concrete floors at 20 Hz, 0.7 as the weighting factor. The
    ground term is Formula (6) with the Annex B change of exponent for an
    exponent measured with a point excitation, the building terms are the
    six tables of Annex A, and the mitigation is the term 5.5 adds. The foot
    is Clause 7, the two quantities E DIN 4150-2 judges.
    """
    gy = 300.0  # the street surface, with the rails flush in it
    x_track = 150.0  # the track centre
    x_e = 280.0  # the emission point, at r_0
    x_b = 470.0  # the ground point in front of the building
    bx0, bx1 = 500.0, 860.0  # the building's outer walls
    storey = 72.0
    y_roof = gy - 2 * storey  # 156: basement, ground floor, first floor
    y_base = gy + storey  # 372: the basement floor
    mid = (bx0 + bx1) / 2  # 680: mid-span of the floors

    s.text(
        450,
        70,
        "One emission, and what the ground and the building do to it",
        17,
        th.fg,
        bold=True,
    )
    s.text(
        40,
        112,
        "$L_{v,E}$ at a tunnel floor or wall, a point in the ground or a foundation",
        12,
        th.muted,
        anchor="start",
    )
    s.text(
        40,
        132,
        "within 25 m of a tram line on the surface, Table 1 recommends a prediction",
        12,
        th.muted,
        anchor="start",
    )

    # The street, the track bed with its rails flush, and the tram on it. The
    # section is transverse, as Figure 1 is, so one wheel stands on each rail.
    s.ground(gy, 40, bx0)
    s.rect(x_track - 60, gy, 120, 22, th.panel, th.muted, sw=1.4)
    for dx in (-28.0, 28.0):
        s.rect(x_track + dx - 5, gy - 4, 10, 8, th.fg)
    s.rect(x_track - 72, gy - 70, 144, 52, th.panel, th.fg, rx=9, sw=2.0)
    s.rect(x_track - 60, gy - 60, 120, 18, th.bg, th.muted, rx=3, sw=1.2)
    for dx in (-28.0, 28.0):
        s.circle(x_track + dx, gy - 11, 7, th.fg)
    s.text(x_track - 10, gy - 80, "tram, 50 km/h", 13, th.fg, anchor="end")
    s.line(x_track, y_roof + 14, x_track, gy + 44, th.muted, 1.2, dash="12,4,3,4")

    # Where a mitigation would go: in the track, which 5.5 names first. The
    # top edge is the railhead, so the box holds the rails and the track bed
    # and leaves the vehicle above it out.
    s.rect(
        x_track - 70, gy - 4, 140, 36, "none", th.secondary, rx=4, sw=1.8, dash="6,4"
    )
    s.text(x_track, gy + 56, "$D_e$", 15, th.secondary, bold=True)

    # The building: a basement, a ground floor and a first floor.
    s.path(
        f"M {bx0 - 8} {y_roof} L {mid} {y_roof - 44} L {bx1 + 8} {y_roof} Z",
        fill=th.panel,
        stroke=th.fg,
        sw=2.0,
    )
    s.rect(bx0, y_roof, bx1 - bx0, y_base + 8 - y_roof, "none", th.fg, sw=2.2)
    for y in (y_roof, gy - storey, gy, y_base):
        s.rect(bx0, y, bx1 - bx0, 8, th.panel, th.fg, sw=1.4)
    # The first floor's own mode, which is what its natural frequency is.
    s.path(
        f"M {bx0} {gy - storey + 8} Q {mid} {gy - storey + 34} {bx1} {gy - storey + 8}",
        stroke=th.accent,
        sw=1.6,
        dash="6,4",
    )
    s.text(bx1 - 10, gy - 30, "concrete floors, $f_e$ = 20 Hz", 13, th.fg, anchor="end")
    s.text(
        bx1 - 10,
        gy - 12,
        "one prediction per $f_e$, never the envelope",
        12,
        th.muted,
        anchor="end",
    )
    s.text(bx1 - 10, y_base - 12, "basement", 12, th.muted, anchor="end")

    # The four points the levels of Formula (1) belong to.
    _accel(s, x_e, gy)
    _accel(s, x_b, gy)
    _accel(s, bx0 + 26, y_base)
    _accel(s, mid, gy - storey)
    _motion_arrows(s, mid + 26, gy - storey - 14, 12, th.primary)
    s.text(x_e + 14, gy - 34, "$L_{v,E}$", 15, th.primary, anchor="start", bold=True)
    s.text(x_e + 14, gy - 16, "Max Hold", 12, th.muted, anchor="start")
    s.text(x_b + 22, gy - 30, "in front of the building", 12, th.muted, anchor="end")
    s.text(bx0 + 42, y_base - 12, "foundation", 12, th.muted, anchor="start")
    s.text(mid, y_roof + 32, "$L_v$: mid-span, vertical", 15, th.primary, bold=True)

    # The two distances, both from the track centre.
    s.line(x_e, gy - 30, x_e, y_roof + 52, th.muted, 0.9, dash="3,3")
    s.dim(x_track, y_roof + 52, x_e, y_roof + 52, "$r_0$", size=14)
    s.dim(x_track, y_roof + 24, bx0, y_roof + 24, "7 m to the building", size=13)

    # The ground: Formula (6), and what Annex B takes off a point excitation.
    # The head continues the curve along its own end tangent, so the arc and
    # the arrow read as one stroke rather than as a line and a stub.
    s.path(
        f"M {x_e + 6} {gy + 6} Q {(x_e + x_b) / 2} {gy + 70} {x_b - 18} {gy + 16}",
        stroke=th.primary,
        sw=2.0,
    )
    s.arrow(x_b - 18, gy + 16, x_b - 6.5, gy + 8, th.primary, 2.0)
    s.text((x_e + x_b) / 2, gy + 64, "$ΔL_{v,BB}$", 15, th.primary, bold=True)
    s.text(300, gy + 90, "$v(r)/v(r_0) = (r/r_0)^{−n}$, $n$ per band", 13, th.fg)
    s.text(
        300,
        gy + 110,
        "from a point excitation: $n$ − 0.5 up to $R_0 ≈ L^2/λ$",
        12,
        th.muted,
    )

    # Into the foundation, then up to the middle of the floor.
    s.path(
        f"M {x_b + 6} {gy + 8} Q {bx0 - 10} {y_base - 6} {bx0 + 8} {y_base - 6}",
        stroke=th.accent,
        sw=2.0,
    )
    s.arrow(bx0 + 8, y_base - 6, bx0 + 19, y_base - 6, th.accent, 2.0)
    s.text(bx0 + 42, gy + 36, "$ΔL_{v,FB}$", 15, th.accent, anchor="start", bold=True)
    s.path(
        f"M {bx0 + 26} {y_base - 26} L {bx0 + 26} {gy - storey + 40} "
        f"Q {bx0 + 26} {gy - storey - 10} {mid - 30} {gy - storey - 10}",
        stroke=th.accent,
        sw=2.0,
    )
    s.arrow(mid - 38, gy - storey - 10, mid - 24, gy - storey - 10, th.accent, 2.0)
    s.text(bx0 + 40, gy - 30, "$ΔL_{v,DF}$", 15, th.accent, anchor="start", bold=True)

    # Formula (1), term by term, with where each term's numbers come from.
    eq_y = 490.0
    s.rect(40, eq_y - 66, 820, 144, th.panel, th.fg, rx=6, sw=1.6)
    for x, symbol, first, second, third in (
        (108.0, "$L_v$", "on the floor", "vertical, per band", ""),
        (
            232.0,
            "$L_{v,E}$",
            "Max Hold at $r_0$",
            "4 Hz to 250 Hz",
            "+ 20 lg($v_2/v_1$), up to 30 %",
        ),
        (372.0, "$ΔL_{v,BB}$", "the ground", "Formula (5) or (6)", ""),
        (
            512.0,
            "$ΔL_{v,FB}$",
            "into the foundation",
            "Table A.3 or A.4",
            "zero when $L_{v,E}$ is at a foundation",
        ),
        (652.0, "$ΔL_{v,DF}$", "up to the floor", "Table A.5 or A.6", ""),
        (786.0, "$D_e$", "mitigation", "DIN SPEC 45673-2, -3", ""),
    ):
        s.text(x, eq_y, symbol, 18, th.fg)
        s.text(x, eq_y + 24, first, 12, th.muted)
        s.text(x, eq_y + 42, second, 12, th.muted)
        if third:
            s.text(x, eq_y + 60, third, 12, th.muted)
    for x, sign in (
        (170.0, "="),
        (300.0, "+"),
        (442.0, "+"),
        (582.0, "+"),
        (718.0, "+"),
    ):
        s.text(x, eq_y, sign, 18, th.fg)
    # Formula (2): the two building terms in one, from Tables A.1 and A.2.
    s.line(458, eq_y - 32, 706, eq_y - 32, th.secondary, 1.4)
    s.line(458, eq_y - 32, 458, eq_y - 24, th.secondary, 1.4)
    s.line(706, eq_y - 32, 706, eq_y - 24, th.secondary, 1.4)
    s.text(
        582,
        eq_y - 42,
        "or in one step, $ΔL_{v,DB}$: Table A.1 or A.2, by $f_e$",
        12,
        th.secondary,
    )

    # Clause 7: the spectrum as the two quantities E DIN 4150-2 judges.
    box_y = 586.0
    s.rect(40, box_y, 400, 108, th.panel, th.primary, rx=6, sw=1.8)
    s.text(
        240,
        box_y + 26,
        "$KB_{FTm,Zug}$, one per category of train",
        14,
        th.primary,
        bold=True,
    )
    s.text(
        240, box_y + 50, "Table 2 weighting, energy sum from 4 Hz to 80 Hz,", 12, th.fg
    )
    s.text(240, box_y + 72, "$c_{T1}$ = 1, $v_0 = 5·10^{−5}$ mm/s", 12, th.fg)
    s.text(
        240,
        box_y + 94,
        "$KB_{Fmax,Zug} = 1.5 · KB_{FTm,Zug}$, $v_{max} = 3 · KB_{Fmax,Zug}$",
        12,
        th.fg,
    )

    s.rect(460, box_y, 400, 108, th.panel, th.secondary, rx=6, sw=1.8)
    s.text(
        660, box_y + 26, "$KB_{FTr}$, over the timetable", 14, th.secondary, bold=True
    )
    s.text(
        660,
        box_y + 52,
        "$KB_{FTr} = √(Σ n_{Zug}/N_r · (α_{Zug} · KB_{FTm,Zug})^2)$",
        13,
        th.fg,
    )
    s.text(660, box_y + 74, "$N_r$ = 1920 by day, 960 by night", 12, th.fg)
    s.text(660, box_y + 94, "$α_{Zug}$ = 0.7 for a tram on the surface", 12, th.fg)

    s.text(
        450,
        718,
        "E DIN 4150-2 holds $KB_{Fmax}$, the largest $KB_{Fmax,Zug}$, "
        "and $KB_{FTr}$ to its Table 1,",
        12,
        th.muted,
    )
    s.text(
        450,
        738,
        "with a category at or below 0.1 counting as zero in $KB_{FTr}$",
        12,
        th.muted,
    )


def _d_building_frequency_predictors(s: SVG, th: Theme) -> None:
    """What a building's own frequency is predicted from (ISO 4866 Annex D).

    One building drawn to scale, with the three things the predictors read
    off it (n, h, and b parallel to the force), and the four predictors of
    D.2 laid out from them with the coefficient range D.2 prints for each
    and what that range gives on this building. The two boxes at the foot
    are the fit of Figure D.1 with the ± 50 % D.2 calls not uncommon, and
    the damping of D.4, for which no proven method exists.
    """
    s.text(450, 92, "What each predictor reads off one building", 17, th.fg, bold=True)

    # --- The building, an elevation at 5 px per metre -----------------------
    ground_y, roof_y = 500.0, 200.0
    x_l, x_r = 200.0, 275.0
    storeys, sway = 18, 26.0
    s.rect(x_l, roof_y, x_r - x_l, ground_y - roof_y, th.panel, th.fg, sw=2.2)
    for k in range(1, storeys):
        y = ground_y - k * (ground_y - roof_y) / storeys
        s.line(x_l + 1.5, y, x_r - 1.5, y, th.muted, 1.0)
    # The mode the whole annex predicts: the same outline swayed, fixed at
    # the base, drawn dashed because it is what nobody here has measured.
    s.path(
        f"M {x_l} {ground_y} C {x_l} 380 {x_l + 8} 280 {x_l + sway} {roof_y} "
        f"L {x_r + sway} {roof_y} C {x_r + 8} 280 {x_r} 380 {x_r} {ground_y}",
        "none",
        th.primary,
        sw=1.8,
        dash="6,4",
    )
    s.text(252, 184, "the fundamental translation mode", 12, th.primary)
    for y in (250.0, 320.0, 390.0, 460.0):
        s.arrow(150, y, 194, y, th.secondary, 2.2)
    s.text(173, 236, "force", 13, th.secondary)
    # Both dimensions before the ground: the witness line of the height runs
    # along the ground line, and would read as a break in it if drawn over.
    s.dim(x_l, roof_y, x_l, ground_y, "$h$ = 60 m", offset=-60, size=14)
    s.dim(x_l, ground_y, x_r, ground_y, "$b$ = 15 m", offset=36, size=14)
    s.ground(ground_y, 90, 370)
    s.text(237, 562, "$n$ = 18 storeys, each about 3.3 m", 13, th.fg)
    s.text(237, 582, "$b$ is the width parallel to the force", 12, th.muted)
    s.text(237, 602, "$h/b$ = 4, so $√(h/(h + b))$ = 0.89", 12, th.muted)

    # --- One row per predictor: what it reads, its form, what it gives ------
    s.text(416, 138, "reads", 12, th.muted)
    s.text(476, 138, "the form, and its coefficient range", 12, th.muted, "start")
    s.text(860, 138, "this building, $f = 1/T$", 12, th.muted, "end")
    rows = (
        (
            th.fg,
            "$n$",
            "$f = 10/n$",
            "D.2: the simplest, no coefficient range",
            "0.56 Hz",
            "$T = 0.1 n$ = 1.8 s",
        ),
        (
            th.primary,
            "$h$",
            "$T = k_1 h$",
            "Formula (D.1): $k_1$ from 0.014 to 0.03",
            "0.56 to 1.19 Hz",
            "$T$ = 0.84 s to 1.80 s",
        ),
        (
            th.primary,
            "$h$, $b$",
            "$T = k_2 h/√b$",
            "Formula (D.2): $k_2$ from 0.087 to 0.109",
            "0.59 to 0.74 Hz",
            "$T$ = 1.35 s to 1.69 s",
        ),
        (
            th.primary,
            "$h$, $b$",
            "$T = (k_3 h/√b) √(h/(h + b))$",
            "Formula (D.3): $k_3$ from 0.06 to 0.08",
            "0.90 to 1.20 Hz",
            "$T$ = 0.83 s to 1.11 s",
        ),
    )
    for i, (colour, reads, form, rng, f_span, t_span) in enumerate(rows):
        top = 150.0 + 88.0 * i
        s.rect(384, top, 488, 76, th.panel, colour, rx=6, sw=1.6)
        s.rect(392, top + 23, 50, 30, th.bg, colour, rx=15, sw=1.4)
        s.text(417, top + 43, reads, 14, colour)
        s.arrow(446, top + 38, 468, top + 38, th.muted, 1.6)
        s.text(476, top + 33, form, 15, colour, "start")
        s.text(476, top + 57, rng, 12, th.muted, "start")
        s.text(860, top + 33, f_span, 14, colour, "end", bold=True)
        s.text(860, top + 57, t_span, 12, th.muted, "end")
    s.text(
        628,
        530,
        "on this building the four predictors span 0.56 Hz to 1.20 Hz",
        12,
    )
    s.text(628, 552, "and D.2 gives no rule for choosing inside a range", 12, th.muted)

    # --- What the annex closes with: the fit, and the damping it cannot -----
    box_y = 632.0
    fit_title = "$f = 46/h$: the fit of Figure D.1, 0.77 Hz here"
    damping_title = "D.4: no proven method predicts damping"
    size = s.fit_size([fit_title, damping_title], (14, 13), 380, bold=True)
    s.rect(40, box_y, 400, 84, th.panel, th.accent, rx=6, sw=1.8)
    s.text(240, box_y + 26, fit_title, size, th.accent, bold=True)
    s.text(240, box_y + 50, "$T = 0.022 h$ s, from 163 rectangular-plan buildings", 12)
    s.text(240, box_y + 70, "errors of ± 50 % are not uncommon: 0.38 Hz to 1.15 Hz", 12)
    s.rect(460, box_y, 400, 84, th.panel, th.secondary, rx=6, sw=1.8)
    s.text(660, box_y + 26, damping_title, size, th.secondary, bold=True)
    s.text(660, box_y + 50, "0.5 % to 2.1 % of critical can occur (Figure D.2)", 12)
    s.text(660, box_y + 70, "with large differences between orthogonal modes", 12)

    s.text(
        450,
        748,
        "D.1: for when a measurement cannot be made, or high damping "
        "or subcomponent resonances limit it",
        12,
        th.muted,
    )
    s.text(
        450,
        770,
        "D.3: a computer model correlates with measurement worse than "
        "$f = 46/h$, and an unproven one should not be assumed more accurate",
        12,
        th.muted,
    )
