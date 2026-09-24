#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Diagrams of the signals guides: levels, filters, spectra and metrology.

One module because these guides all draw the same thing from different
angles: a signal on its way through the library. The level and filter
diagrams follow it stage by stage (weighting, time weighting, the multirate
bank, block state, channels), the spectra diagrams open the estimators that
read it (Welch, coherence, cepstrum, synchronous averaging, correlation) and
the metrology diagrams close the loop back to physical units, uncertainty and
whether the record was fit to analyse at all.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from .canvas import signed

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from .canvas import SVG, Theme

# ---------------------------------------------------------------------------
# d1 - Calibration chain (IEC 60942)
# ---------------------------------------------------------------------------


def _d_calibration_chain(s: SVG, th: Theme) -> None:
    gy = 470.0
    s.ground(gy, 40, 860)

    # Calibrator on top of the microphone (left column)
    mx = 150.0
    cal_y = 110.0
    s.text(mx, cal_y - 22, "Sound calibrator", 19, th.fg, bold=True)
    s.rect(mx - 62, cal_y, 124, 86, th.panel, th.fg, rx=10, sw=2)
    s.text(mx, cal_y + 38, "94.0 dB", 22, th.secondary, bold=True, mono=True)
    s.text(mx, cal_y + 66, "1 kHz", 17, th.muted, mono=True)
    s.rect(mx - 15, cal_y + 86, 30, 12, th.fg, rx=3)  # coupler cavity
    s.mic(mx, cal_y + 98, gy, 1.3)

    # Signal chain
    boxes = [(400, "Microphone +", "preamplifier"), (650, "Audio interface", "(ADC)")]
    by, bw, bh = 176.0, 210.0, 78.0
    prev_x = mx + 62
    for bx, l1, l2 in boxes:
        s.rect(bx - bw / 2, by, bw, bh, th.panel, th.primary, rx=12, sw=2)
        s.text(bx, by + 33, l1, 19, th.fg, bold=True)
        s.text(bx, by + 60, l2, 19, th.fg, bold=True)
        s.arrow(prev_x, by + bh / 2, bx - bw / 2 - 6, by + bh / 2, th.fg, 2)
        prev_x = bx + bw / 2 + 6
    s.arrow(prev_x, by + bh / 2, 862, by + bh / 2, th.accent, 2.4)
    s.text(796, by + bh / 2 + 34, "Pa per", 17, th.accent, mono=True)
    s.text(796, by + bh / 2 + 58, "digital unit", 17, th.accent, mono=True)

    # Stability annotation, clearly separated below the chain. The box is
    # sized on the Spanish tolerance line, which sets six vertical bars, a
    # minus and a ≤ and so runs wider than its English twin.
    s.rect(220, 340, 620, 96, "none", th.secondary, rx=12, dash="6,5")
    s.text(
        530,
        376,
        "Stability: |max − mean| and |min − mean| ≤ 0.07 dB",
        19,
        th.secondary,
        bold=True,
    )
    s.text(
        530,
        408,
        "(IEC 60942:2017 Table 2, class 1); else CalibrationWarning",
        17,
        th.fg,
    )


# ---------------------------------------------------------------------------
# d1b - Coupling the calibrator on the capsule (IEC 60942 half-section)
# ---------------------------------------------------------------------------


def _d_calibration_coupling(s: SVG, th: Theme) -> None:
    """Half-section through the coupler with the capsule inserted.

    Drawn to the real proportions of a 1/2 inch measurement microphone
    (12.7 mm nominal capsule diameter, 6.35 mm for the 1/4 inch adaptor
    inset); the scale below is 14 drawing units per millimetre.
    """
    scale = 11.0  # drawing units per millimetre
    cx = 352.0  # axis of the assembly
    half = 12.7 / 2 * scale  # 1/2 inch capsule radius: 69.9 units
    wall = 24.0  # coupler wall thickness, drawn
    ref_y = 300.0  # reference plane: contact microphone/coupler
    dia_y = 236.0  # diaphragm, inside the cavity
    cav_top = 148.0  # cavity roof, under the driver

    # -- Coupler body, sectioned: two walls and a roof around the cavity ----
    for x0 in (cx - half - wall, cx + half):
        s.rect(x0, cav_top - 30, wall, ref_y - cav_top + 30, th.panel, th.fg, sw=2)
        y = cav_top - 24
        while y < ref_y - 8:
            s.line(x0 + 2, y + 12, x0 + wall - 2, y, th.muted, 0.9)
            y += 12
    s.rect(cx - half - wall, cav_top - 56, 2 * (half + wall), 26, th.panel, th.fg, sw=2)
    x = cx - half - wall + 6
    while x < cx + half + wall - 6:
        s.line(x, cav_top - 32, x + 12, cav_top - 54, th.muted, 0.9)
        x += 12
    s.text(cx, cav_top - 70, "Sound calibrator (class 1)", 17, th.fg, bold=True)

    # Driver radiating down into the cavity.
    s.rect(cx - 40, cav_top - 28, 80, 14, th.primary, th.fg, sw=1.4)
    for r in (22, 34, 46):
        s.path(
            f"M {cx - r:.0f} {cav_top + 4:.0f} Q {cx:.0f} "
            f"{cav_top + 4 + r * 0.42:.0f} {cx + r:.0f} {cav_top + 4:.0f}",
            stroke=th.accent,
            sw=1.4,
        )
    s.text(cx, cav_top + 56, "94.0 dB", 18, th.secondary, bold=True, mono=True)
    s.text(cx, cav_top + 80, "1 kHz", 15, th.muted, mono=True)

    # -- Effective load volume: cavity floor is the diaphragm ---------------
    s.add(
        f'<rect x="{cx - half}" y="{dia_y}" width="{2 * half}" '
        f'height="{ref_y - dia_y}" fill="{th.accent}" opacity="0.22"/>'
    )
    s.rect(
        cx - half, dia_y, 2 * half, ref_y - dia_y, "none", th.accent, sw=1.6, dash="5,4"
    )

    # -- Microphone, inserted to the reference plane ------------------------
    s.rect(cx - half, dia_y, 2 * half, 7, th.fg, rx=2)  # diaphragm
    s.rect(cx - half, ref_y, 2 * half, 132, th.panel, th.primary, rx=6, sw=2)
    s.line(cx - half - wall, ref_y, cx + half + wall, ref_y, th.secondary, 2.6)
    # Each line a size smaller where the capsule is narrower than it, as the
    # Spanish of both is at 16 px.
    capsule, preamp = "1/2 in capsule", "+ preamplifier"
    inner = 2 * half - 12
    s.text(
        cx,
        ref_y + 52,
        capsule,
        s.fit_size([capsule], [16, 15, 14, 13], inner, bold=True),
        th.fg,
        bold=True,
    )
    s.text(
        cx, ref_y + 76, preamp, s.fit_size([preamp], [16, 15, 14, 13], inner), th.muted
    )
    s.line(cx, ref_y + 132, cx, 470, th.fg, 2.2)
    s.dim(cx - half, ref_y + 104, cx + half, ref_y + 104, "12.7 mm", size=15)

    # Annotations on the left.
    s.line(cx - half - wall - 6, ref_y, 214, ref_y, th.secondary, 1.3, dash="7,4,2,4")
    s.text(
        210, ref_y - 28, "reference plane", 15, th.secondary, bold=True, anchor="end"
    )
    s.text(210, ref_y - 8, "(3.12)", 15, th.secondary, anchor="end")
    s.arrow(216, dia_y + 26, cx - half - 6, dia_y + 22, th.accent, 1.6)
    # Two lines each, and the two blocks stack in the same 212 px column:
    # the green one sits above its own arrow so the red one keeps the
    # baseline pair it needs. The Spanish "plano de referencia (3.12)" is
    # 220 px on one line, which is wider than the column, so both are set
    # broken and both need the room.
    s.text(212, dia_y - 10, "effective load", 15, th.accent, bold=True, anchor="end")
    s.text(212, dia_y + 12, "volume (3.13)", 15, th.accent, anchor="end")
    s.text(212, ref_y + 30, "the generated level shifts", 14, th.muted, anchor="end")
    s.text(212, ref_y + 50, "with that volume (6.3 k)", 14, th.muted, anchor="end")

    # -- Adaptor inset ------------------------------------------------------
    s.rect(468, 104, 160, 214, "none", th.fg, rx=10, sw=1.6, dash="6,5")
    s.text(548, 132, "1/4 in capsule", 15, th.fg, bold=True)
    ax0, aq = 548.0, 6.35 / 2 * scale
    s.rect(ax0 - 30, 150, 60, 24, th.panel, th.fg, sw=1.6)  # adaptor sleeve
    s.rect(ax0 - aq, 174, 2 * aq, 66, th.panel, th.primary, rx=3, sw=1.8)
    s.line(ax0 - 30, 150, ax0 + 30, 150, th.secondary, 2.2)
    adaptor = ("the adaptor is part of", "the calibrator (5.1.1)")
    size = s.fit_size(list(adaptor), [13, 12, 11], 148)
    s.text(548, 266, adaptor[0], size, th.fg)
    s.text(548, 288, adaptor[1], size, th.fg)

    # -- Windscreen, off to one side ---------------------------------------
    # Set left of the panel it would otherwise reach: "la verificación,
    # puesta al medir" is 201 px against the 176 of its English twin.
    s.circle(529, 386, 28, th.panel, th.muted, sw=2)
    for k in range(-2, 3):
        s.line(505, 386 + k * 10, 553, 386 + k * 10, th.muted, 0.9)
    s.text(529, 436, "windscreen: off for the", 13, th.muted)
    s.text(529, 456, "check, back on to measure", 13, th.muted)

    # -- Right panel: the background check ---------------------------------
    # 240 px wide on "leer ≥ 30 dB por debajo del", 216 px against the 185
    # of its English twin.
    s.rect(636, 104, 240, 340, "none", th.primary, rx=12, sw=1.8)
    s.text(756, 134, "Before switching it on", 16, th.primary, bold=True)
    s.rect(730, 158, 56, 52, th.panel, th.fg, rx=6, sw=1.8)
    s.rect(744, 210, 28, 62, th.panel, th.primary, rx=4, sw=1.8)
    s.text(758, 190, "OFF", 15, th.muted, bold=True, mono=True)
    for r in (26, 40):
        s.path(
            f"M {676 + r * 0.2:.0f} {224 - r * 0.5:.0f} A {r} {r} 0 0 1 "
            f"{676 + r * 0.5:.0f} {224 + r * 0.3:.0f}",
            stroke=th.secondary,
            sw=1.5,
        )
    s.arrow(694, 232, 724, 240, th.secondary, 1.6)
    s.text(698, 282, "source in use", 12, th.secondary)
    s.text(756, 324, "the coupled capsule must", 14, th.fg)
    s.text(756, 346, "read ≥ 30 dB below the", 14, th.fg, bold=True)
    s.text(756, 368, "calibrator level: under 64 dB", 14, th.fg)
    s.text(756, 390, "for a 94 dB calibrator", 14, th.fg)
    s.text(756, 418, "(B.4.2; 40 dB in A.5.3)", 14, th.muted)

    s.text(
        450,
        528,
        "The specified level is the level at the diaphragm of "
        "the inserted microphone (5.3.1.2), and holds for",
        15,
        th.fg,
    )
    s.text(
        450,
        552,
        "the microphone models and configurations listed in the "
        "manual (IEC 60942:2017, 5.3.1.3, 6.3 a)",
        15,
        th.muted,
    )


# ---------------------------------------------------------------------------
# d4 - Library signal chain
# ---------------------------------------------------------------------------


def _d_signal_chain(s: SVG, th: Theme) -> None:
    stages = [
        ("Signal", "$x$, $f_s$", th.fg),
        ("Calibrate", "→ Pa", th.primary),
        ("Weighting", "A/C/G/Z", th.primary),
        ("Octave", "bands $1/b$", th.primary),
        ("Ballistics", "F / S / I", th.primary),
        ("Metrics", "$L_{eq}$, $L_N$…", th.accent),
    ]
    bw, bh, gap = 136.0, 92.0, 12.0
    total = len(stages) * bw + (len(stages) - 1) * gap
    x = (900 - total) / 2
    y = 170.0
    for i, (title, sub, color) in enumerate(stages):
        s.rect(x, y, bw, bh, th.panel, color, rx=12, sw=2)
        s.text(x + bw / 2, y + 40, title, 19, th.fg, bold=True)
        # Mono is the code voice: it styles the literal stage tags, while a
        # sub carrying $...$ mathematics composes in the text face (mono
        # plus markup is refused by the canvas).
        s.text(x + bw / 2, y + 68, sub, 16, color, mono="$" not in sub)
        if i < len(stages) - 1:
            s.arrow(x + bw + 1, y + bh / 2, x + bw + gap - 2, y + bh / 2, th.fg, 2)
        x += bw + gap


# ---------------------------------------------------------------------------
# d5 - Multirate decimation inside the filter bank
# ---------------------------------------------------------------------------


def _d_multirate(s: SVG, th: Theme) -> None:
    # Input on the left
    s.rect(36, 150, 136, 70, th.panel, th.fg, rx=10, sw=2)
    s.text(104, 180, "Signal", 19, th.fg, bold=True)
    s.text(104, 205, "$f_s$ = 48 kHz", 15, th.muted)

    rows = [
        (120.0, "16 kHz band", "$f_s$", "no decimation", th.secondary),
        (230.0, "250 Hz band", "$f_s / 4$", "12 kHz", th.primary),
        (340.0, "63 Hz band", "$f_s / 16$", "3 kHz", th.accent),
    ]
    for y, band, rate, eff, color in rows:
        bx = 455.0
        if "no" not in eff:
            s.arrow(172, 185, 240, y + 35, th.fg, 1.6)
            s.rect(250, y, 150, 70, th.panel, th.muted, rx=10, sw=1.6)
            s.text(325, y + 30, "Anti-alias", 17, th.fg)
            s.text(325, y + 54, "LPF + \u2193$M$", 15, th.muted)
            s.arrow(400, y + 35, 448, y + 35, th.fg, 1.6)
        else:
            s.arrow(172, 185, 448, y + 35, th.fg, 1.6)
        s.rect(bx, y, 190, 70, th.panel, color, rx=10, sw=2)
        s.text(bx + 95, y + 30, band, 17, th.fg, bold=True)
        s.text(bx + 95, y + 54, f"SOS @ {rate}", 15, color)
        s.text(660, y + 40, eff, 15, th.muted, "start", mono=True)

    s.text(
        450, 480, "Low bands are filtered at a decimated rate: the relative", 17, th.fg
    )
    s.text(
        450,
        508,
        "bandwidth stays wide, so the SOS stays numerically healthy.",
        17,
        th.fg,
    )


def _d_uncertainty(s: SVG, th: Theme) -> None:
    """Two routes to measurement uncertainty (ISO/IEC Guide 98-3 and Suppl. 1).

    From a shared measurement model and its input estimates, two parallel
    lanes: the GUM law of propagation of uncertainty (clause 5) and the
    Monte Carlo propagation of distributions (Supplement 1, clause 7).
    """
    # --- Shared measurement model + inputs ----------------------------------
    cx = 450.0
    iw, ih = 560.0, 62.0
    s.rect(cx - iw / 2, 56, iw, ih, th.panel, th.fg, rx=10, sw=2)
    s.text(
        cx,
        84,
        "Measurement model  $y = f(x_1, …, x_N)$",
        17,
        th.fg,
        "middle",
        bold=True,
    )
    s.text(
        cx,
        106,
        "input estimates $x_i$ with standard uncertainties $u(x_i)$",
        13,
        th.muted,
        "middle",
    )

    lxc, rxc = 232.0, 668.0
    s.arrow(cx, 118, lxc, 158, th.fg, 1.8)
    s.arrow(cx, 118, rxc, 158, th.fg, 1.8)

    bw, bh = 372.0, 62.0

    def _step(cxx: float, y: float, l1: str, l2: str, color: str) -> None:
        s.rect(cxx - bw / 2, y, bw, bh, th.panel, color, rx=10, sw=2)
        s.text(cxx, y + 27, l1, 15, th.fg, "middle", bold=True)
        if l2:
            s.text(cxx, y + 48, l2, 12, th.muted, "middle")

    # --- Left lane: GUM law of propagation (clause 5) -----------------------
    _step(
        lxc,
        158,
        "Law of propagation  (GUM 5)",
        "sensitivity $c_i = ∂f / ∂x_i$",
        th.primary,
    )
    _step(
        lxc,
        250,
        "Combine in quadrature",
        "$u_c^2 = Σ c_i^2 u^{2}(x_i)$ + correlation",
        th.fg,
    )
    _step(
        lxc, 342, "Effective dof  (Annex G.4)", "$v_{eff}$: Welch–Satterthwaite", th.fg
    )
    s.arrow(lxc, 220, lxc, 250, th.fg, 1.8)
    s.arrow(lxc, 312, lxc, 342, th.fg, 1.8)
    s.arrow(lxc, 404, lxc, 434, th.fg, 1.8)
    s.rect(lxc - bw / 2, 434, bw, 58, "none", th.primary, rx=10, sw=2.4)
    s.text(lxc, 462, "$U = k · u_c$", 19, th.fg, "middle", bold=True)
    s.text(lxc, 482, "$k = t_{p}(v_{eff})$   (clause 6)", 12, th.muted, "middle")

    # --- Right lane: Monte Carlo (Supplement 1, clause 7) -------------------
    _step(
        rxc,
        158,
        "Monte Carlo  (Suppl. 1, 7)",
        "draw $x_i$ from its PDF $g(x_i)$",
        th.secondary,
    )
    _step(rxc, 250, "Propagate $M$ trials", "$y_r = f(x_{1r}, …, x_{Nr})$", th.fg)
    _step(
        rxc, 342, "Sort ${y_r}$, take fractiles", "prob.-symmetric 95 % interval", th.fg
    )
    s.arrow(rxc, 220, rxc, 250, th.fg, 1.8)
    s.arrow(rxc, 312, rxc, 342, th.fg, 1.8)
    s.arrow(rxc, 404, rxc, 434, th.fg, 1.8)
    s.rect(rxc - bw / 2, 434, bw, 58, "none", th.secondary, rx=10, sw=2.4)
    s.text(rxc, 462, "coverage interval", 19, th.fg, "middle", bold=True)
    s.text(rxc, 482, "$[y_{low}, y_{high}]$   (clause 7.7)", 12, th.muted, "middle")


def _d_uncertainty_sources(s: SVG, th: Theme) -> None:
    """Where each row of an acoustic budget comes from physically.

    One outdoor A-weighted level measurement drawn to scale at 60 units per
    metre (microphone 1.5 m above the ground and 4 m from the facade, three
    alternative positions 2 m apart), with a leader from each element to the
    budget row it feeds.
    """
    gy = 442.0
    s.ground(gy, 34, 520)
    scale = 60.0  # drawing units per metre

    # -- Facade at the right of the scene ----------------------------------
    s.rect(496, 168, 26, gy - 168, th.panel, th.fg, sw=2)
    s.text(490, 200, "facade", 13, th.muted, anchor="end")

    # -- Source ------------------------------------------------------------
    s.rect(44, 372, 42, 52, th.panel, th.primary, rx=6, sw=2)
    s.circle(65, 391, 9, th.primary)
    s.circle(65, 391, 3.5, th.bg)
    s.circle(65, 411, 5.5, th.primary)
    s.text(65, 362, "source", 13, th.fg, bold=True)
    for r in (20, 32, 44):
        s.path(
            f"M {90 + r * 0.30:.0f} {398 - r * 0.55:.0f} "
            f"A {r} {r} 0 0 1 {90 + r * 0.55:.0f} {398 + r * 0.30:.0f}",
            stroke=th.accent,
            sw=1.3,
        )

    # -- Meter on a tripod, microphone 1.5 m up and 4 m from the facade ----
    mic_x, mic_y = 256.0, gy - 1.5 * scale
    s.mic(mic_x, mic_y, gy, 1.1)
    s.rect(mic_x + 16, 372, 48, 64, th.panel, th.primary, rx=6, sw=1.8)
    s.text(mic_x + 40, 410, "SLM", 13, th.fg, bold=True, mono=True)
    s.dim(mic_x - 40, mic_y, mic_x - 40, gy, "1.5 m", size=13)
    s.line(mic_x - 40, mic_y, mic_x - 6, mic_y, th.muted, 0.9, dash="3,3")
    s.dim(mic_x, gy + 40, 496, gy + 40, "4 m", size=13)
    s.line(mic_x, gy, mic_x, gy + 44, th.muted, 0.9, dash="3,3")
    s.line(496, gy, 496, gy + 44, th.muted, 0.9, dash="3,3")

    # Two alternative microphone positions, 2 m either side.
    for dx in (-2.0 * scale, 2.0 * scale):
        s.circle(mic_x + dx, mic_y, 6.5, "none", th.secondary, 2.0)
        s.line(mic_x + dx, mic_y + 7, mic_x + dx, gy, th.secondary, 1.1, dash="5,4")
    s.dim(
        mic_x - 2 * scale,
        mic_y - 36,
        mic_x + 2 * scale,
        mic_y - 36,
        "3 positions, 2 m apart",
        size=13,
    )

    # -- Calibrator standing beside the meter ------------------------------
    # Past the right-hand position, named above itself: nearer the meter,
    # the leaders from the meter and from that position ran through its
    # name on their way to the budget.
    s.rect(410, gy - 52, 22, 48, th.panel, th.secondary, rx=5, sw=1.8)
    s.text(421, gy - 62, "calibrator", 13, th.secondary)

    # -- Weather station, high on the facade side --------------------------
    s.rect(300, 104, 154, 74, th.panel, th.fg, rx=8, sw=1.6)
    s.text(377, 128, "weather", 14, th.fg, bold=True)
    s.text(377, 150, "3 m/s  12 °C", 12, th.muted, mono=True)
    s.text(377, 170, "68 % RH", 12, th.muted, mono=True)

    # -- Budget table on the right, rows in the order the leaders run ------
    bx, by, bw = 552.0, 96.0, 322.0
    rows = (
        (
            "Meteorology and ground",
            "Type B - from the propagation clause",
            th.fg,
            (454.0, 140.0),
        ),
        (
            "Position scatter",
            "Type A - $s/√n$, $v = n − 1$",
            th.secondary,
            (mic_x + 2 * scale + 8, mic_y),
        ),
        (
            "Instrument class tolerance",
            "Type B - rectangular, $a$ = 0.3 dB",
            th.primary,
            (mic_x + 64, 400.0),
        ),
        (
            "Calibrator class tolerance",
            "Type B - rectangular, $a$ = 0.4 dB",
            th.secondary,
            (432.0, gy - 30),
        ),
    )
    s.rect(bx, by, bw, 252, "none", th.fg, rx=10, sw=1.8)
    s.text(bx + bw / 2, by - 14, "The budget it feeds", 16, th.fg, bold=True)
    for i, (name, kind, color, (from_x, from_y)) in enumerate(rows):
        ry = by + 26 + i * 60
        if i:
            s.line(bx + 12, ry - 18, bx + bw - 12, ry - 18, th.muted, 0.8)
        s.circle(bx + 20, ry + 4, 5, color)
        s.text(bx + 34, ry + 10, name, 15, th.fg, anchor="start", bold=True)
        s.text(bx + 34, ry + 32, kind, 12, th.muted, anchor="start")
        s.line(from_x, from_y, bx - 6, ry + 4, color, 1.0, dash="4,4")

    s.text(
        bx + bw / 2,
        by + 292,
        "one calibrator for two channels makes their",
        13,
        th.secondary,
    )
    s.text(
        bx + bw / 2,
        by + 312,
        "calibration terms correlated, not two rows",
        13,
        th.secondary,
    )

    s.text(
        450,
        552,
        "Budgets fail by omission, not arithmetic: every row is "
        "a piece of hardware or a decision about geometry",
        15,
        th.muted,
    )


def _d_time_weighting(s: SVG, th: Theme) -> None:
    """Exponential-detector chain of the sound-level time weightings (IEC 61672-1)."""
    # The decibel stage spells out the logarithm and is the widest title of the
    # chain, so it takes a smaller face to keep the padding inside its box.
    stages = [
        ("$p(t)$", "band signal", th.fg, 18),
        ("$( · )^2$", "square", th.primary, 18),
        ("one-pole RC", "time constant $τ$", th.primary, 18),
        ("$10·log_{10}(·/p_0^2)$", "to decibels", th.accent, 15),
        ("$L_{τ}(t)$", "time-weighted level", th.secondary, 18),
    ]
    # Each box as wide as its longer line needs, 120 px at least: at a
    # common 150 px the Spanish of the last one ran out through both sides.
    widths = [
        max(
            120.0,
            s.text_width(title, size, bold=True) + 24,
            s.text_width(sub, 12) + 24,
        )
        for title, sub, _color, size in stages
    ]
    bh, gap = 90.0, 12.0
    total = sum(widths) + (len(stages) - 1) * gap
    x = (900 - total) / 2
    y = 108.0
    last = len(stages) - 1
    for i, (title, sub, color, size) in enumerate(stages):
        bw = widths[i]
        fill = "none" if i in (0, last) else th.panel
        s.rect(x, y, bw, bh, fill, color, rx=12, sw=2.2)
        s.text(x + bw / 2, y + 38, title, size, th.fg, "middle", bold=True)
        s.text(x + bw / 2, y + 64, sub, 12, color, "middle")
        if i < last:
            s.arrow(x + bw + 1, y + bh / 2, x + bw + gap - 2, y + bh / 2, th.fg, 2)
        x += bw + gap

    # Discrete realization of the detector. Parked: the exponent of
    # α = 1 − e^(−1/(fs·τ)) carries a subscript inside the superscript,
    # one script level more than the composer sets, so the whole line
    # stays plain until that family is adjudicated.
    s.rect(130, 246, 640, 70, th.panel, th.muted, rx=10, sw=1.6)
    s.text(
        450,
        275,
        "y[n] = α·x²[n] + (1 − α)·y[n−1],   α = 1 − e^(−1/(fs·τ))",
        15,
        th.fg,
        "middle",
        bold=True,
        mono=True,
    )
    s.text(
        450,
        299,
        "a first-order low-pass on the squared signal → the mean-square envelope",
        12,
        th.muted,
        "middle",
    )

    # The three standardized time constants.
    chips = [
        ("Fast (F)", "$τ$ = 125 ms", th.primary),
        ("Slow (S)", "$τ$ = 1000 ms", th.accent),
        ("Impulse (I)", "35 ms rise · 1500 ms fall", th.secondary),
    ]
    cw, cgap = 210.0, 15.0
    cx = (900 - (len(chips) * cw + (len(chips) - 1) * cgap)) / 2
    for title, sub, color in chips:
        s.rect(cx, 350, cw, 74, "none", color, rx=10, sw=2.2)
        s.text(cx + cw / 2, 380, title, 15, th.fg, "middle", bold=True)
        s.text(cx + cw / 2, 404, sub, 12, th.muted, "middle")
        cx += cw + cgap


# ---------------------------------------------------------------------------
# One calibrated record and every level the levels guide takes from it
# ---------------------------------------------------------------------------

#: The record drawn across the top of the plate and reduced in every branch:
#: 111 samples of background, one impulse (sample 27, the greatest excursion)
#: and one event centred on sample 68 (most of the energy). Offsets in px
#: from the strip's centre line, hard-coded so the plate is identical on every
#: platform.
_LEVELS_RECORD = (
    0, 2, -2, -5, -3, -5, 0, 7, -3, -3, 3, 2, 1, -5, 0, 4, -7, -3, -10, -7,
    -10, -1, -7, 1, 1, -1, -14, -34, 19, -9, -8, -3, -5, -5, 6, -4, 0, 5, -3,
    -1, 0, 0, -7, 0, 7, -12, 2, 6, -6, 6, 6, 3, -10, 1, -7, -15, 8, 3, 9, -15,
    9, -12, -2, -24, -26, 25, -6, 13, -8, -14, -7, 2, -9, -3, 7, 25, 9, 4, -9,
    -10, 9, 9, 1, 4, 5, -1, 5, -5, 13, -1, 2, 5, 0, 9, 2, 2, -9, 2, -10, -11,
    -1, -5, 1, 12, -5, -3, 1, 3, -1, -1, 4,
)  # fmt: skip


def _polyline(xs: Sequence[float], ys: Sequence[float]) -> str:
    """An open SVG path through the points, one decimal per coordinate."""
    return "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in zip(xs, ys, strict=True))


def _d_levels_from_a_record(s: SVG, th: Theme) -> None:
    """One calibrated record and the four reductions the levels guide makes.

    The frequency weighting of IEC 61672-1 5.5 comes first, and then the
    record splits four ways: the mean square over the stated interval (3.10,
    and the sound exposure level of 3.12 referred to 1 s), the exponential
    time weighting of 3.6 with its maximum (3.7) and the percentile levels the
    library reads off the same F track, the peak of 3.8 and 3.9 with C
    weighting (5.13), and the running integral of IEC 61252 3.1 normalized to
    8 h by 3.3. Each branch draws what it does to the same samples. The box
    at the foot is the one bridge between branches: the three energy
    quantities are one energy read over the stated interval, over the 1 s of
    3.12 and over the 8 h of IEC 61252 3.3, and the other three need the
    record itself.
    """
    rec = _LEVELS_RECORD
    n = len(rec)
    full = 34.0  # the greatest |offset|, the impulse

    # --- The record ---------------------------------------------------------
    x_a, x_b, mid = 220.0, 860.0, 112.0
    step = (x_b - x_a) / (n - 1)
    s.text(40, 94, "the calibrated record", 14, th.fg, anchor="start", bold=True)
    s.text(40, 116, "$p(t)$ in pascals", 13, th.fg, anchor="start")
    s.text(40, 138, "levels re $p_0$ = 20 µPa (3.2)", 12, th.muted, anchor="start")
    s.line(x_a, mid, x_b, mid, th.muted, 0.8, dash="3,3")
    s.path(
        _polyline([x_a + step * k for k in range(n)], [mid + v for v in rec]),
        stroke=th.fg,
        sw=1.4,
    )
    s.text(x_a + step * 27, 68, "an impulse", 12, th.secondary)
    s.text(x_a + step * 68, 68, "an event", 12, th.accent)
    s.text(x_a + step * 100, 68, "background", 12, th.muted)
    axis = 160.0
    s.line(x_a, axis, x_b, axis, th.fg, 1.2)
    for x, label in ((x_a, "$t_1$"), (x_b, "$t_2$")):
        s.line(x, axis - 5, x, axis + 5, th.fg, 1.2)
        s.text(x, axis + 22, label, 13, th.fg)
    s.text((x_a + x_b) / 2, axis + 22, "the stated time interval $T$", 13, th.fg)

    # --- Frequency weighting, 5.5 ---------------------------------------------
    bar_y, bar_h = 204.0, 44.0
    s.arrow(110, 150, 110, bar_y - 2, th.fg, 1.8)
    s.rect(30, bar_y, 840, bar_h, th.panel, th.fg, rx=8, sw=1.8)
    s.text(
        450,
        bar_y + 28,
        "frequency weighting A, C or Z, each 0 dB at 1 kHz (5.5)",
        14,
        th.fg,
        bold=True,
    )

    # --- Four branches ----------------------------------------------------------
    col_w, gap, top, height = 198.0, 16.0, 290.0, 336.0
    xs0 = [30.0 + k * (col_w + gap) for k in range(4)]
    colours = (th.primary, th.accent, th.secondary, th.primary)
    heads = (
        ("Average the square", "IEC 61672-1, 3.10 and 3.12", "A or Z"),
        ("Time-weight the square", "IEC 61672-1, 3.6, 3.7 and 5.8", "A"),
        ("Hold the greatest $|p|$", "IEC 61672-1, 3.8, 3.9 and 5.13", "C"),
        ("Integrate the square", "IEC 61252, 3.1 and 3.3", "A"),
    )
    # 13 px in English, where "Time-weight the square" runs 188 px at 14; the
    # Spanish heads all keep 14.
    head_size = s.fit_size(
        [h for h, _, _ in heads], (14, 13, 12), col_w - 16, bold=True
    )
    for x0, colour, (head, clause, weight) in zip(xs0, colours, heads, strict=True):
        cx = x0 + col_w / 2
        s.arrow(cx, bar_y + bar_h, cx, top - 2, colour, 1.8)
        s.text(
            cx + 8, bar_y + bar_h + 26, weight, 12, colour, anchor="start", bold=True
        )
        s.rect(x0, top, col_w, height, th.panel, colour, rx=10, sw=2.0)
        s.text(cx, top + 24, head, head_size, colour, bold=True)
        s.text(cx, top + 42, clause, 11, th.muted)

    sk_top, sk_h = top + 56, 94.0
    sk_bot = sk_top + sk_h
    leg_y = sk_bot + 22

    def sx(x0: float, k: float) -> float:
        return x0 + 10 + (col_w - 20) * k / (n - 1)

    def legend(x0: float, items: Sequence[tuple[str, str, str]]) -> None:
        widths = [22 + s.text_width(label, 11) for label, _, _ in items]
        x = x0 + (col_w - sum(widths) - 10 * (len(items) - 1)) / 2
        for (label, colour, dash), wd in zip(items, widths, strict=True):
            s.line(x, leg_y - 4, x + 16, leg_y - 4, colour, 2.0, dash=dash)
            s.text(x + 20, leg_y, label, 11, th.fg, anchor="start")
            x += wd + 10

    sq = [(v / full) ** 2 for v in rec]
    ks = range(n)

    # 1. The mean square over T (3.10): no time constant anywhere.
    x0 = xs0[0]
    top_sq = max(sq)
    s.line(x0 + 10, sk_bot, x0 + col_w - 10, sk_bot, th.muted, 1.0)
    s.path(
        _polyline(
            [sx(x0, k) for k in ks], [sk_bot - (sk_h - 6) * q / top_sq for q in sq]
        ),
        stroke=th.fg,
        sw=1.1,
    )
    y_mean = sk_bot - (sk_h - 6) * (sum(sq) / n) / top_sq
    s.line(x0 + 10, y_mean, x0 + col_w - 10, y_mean, th.primary, 2.4)
    legend(x0, (("$p^2$", th.fg, ""), ("its mean over $T$", th.primary, "")))

    # 2. The exponential time weighting (3.4, 3.6): a one-pole low-pass on the
    # square, fast for F and slow for S, then the maxima of 3.7 and the
    # percentiles of the F track once its first 5 tau are left out.
    x0 = xs0[1]

    def track(alpha: float) -> list[float]:
        out: list[float] = []
        y = sq[0] + 1e-3
        for q in sq:
            y += alpha * (q + 1e-3 - y)
            out.append(10 * math.log10(y))
        return out

    f_track, s_track = track(0.35), track(0.06)  # tau of 2.3 and 16 samples

    def ly(level: float) -> float:
        return sk_bot - sk_h * (min(max(level, -24.0), 0.0) + 24.0) / 24.0

    skip = 12  # 5 tau of the F track
    xb = sx(x0, skip)
    s.line(x0 + 10, sk_bot, x0 + col_w - 10, sk_bot, th.muted, 1.0)
    s.line(xb, sk_top, xb, sk_bot, th.muted, 1.0, dash="2,2")
    s.text((x0 + 10 + xb) / 2, sk_top + 10, "5$τ$", 10, th.muted)
    kept = sorted(f_track[skip:])
    for pct in (10, 50, 90):
        level = kept[round((100 - pct) / 100 * (len(kept) - 1))]
        s.line(xb, ly(level), x0 + col_w - 10, ly(level), th.muted, 1.0, dash="3,3")
    s.path(
        _polyline([sx(x0, k) for k in ks], [ly(v) for v in s_track]),
        stroke=th.fg,
        sw=1.3,
        dash="4,2",
    )
    s.path(
        _polyline([sx(x0, k) for k in ks], [ly(v) for v in f_track]),
        stroke=th.accent,
        sw=1.4,
    )
    k_f = max(ks, key=lambda k: f_track[k])
    k_s = max(ks, key=lambda k: s_track[k])
    s.circle(sx(x0, k_f), ly(f_track[k_f]), 3.6, th.accent)
    s.circle(sx(x0, k_s), ly(s_track[k_s]), 3.6, th.fg)
    legend(x0, (("F", th.accent, ""), ("S", th.fg, "4,2"), ("$L_N$", th.muted, "3,3")))

    # 3. The peak (3.8, 3.9): the greatest excursion of either sign, unaveraged.
    x0 = xs0[2]
    yc = sk_top + sk_h / 2
    scale = (sk_h / 2 - 4) / full
    s.line(x0 + 10, yc, x0 + col_w - 10, yc, th.muted, 0.8, dash="3,3")
    s.path(
        _polyline([sx(x0, k) for k in ks], [yc + v * scale for v in rec]),
        stroke=th.fg,
        sw=1.1,
    )
    k_p = max(ks, key=lambda k: abs(rec[k]))
    y_p = yc + rec[k_p] * scale
    for y in (y_p, 2 * yc - y_p):
        s.line(x0 + 10, y, x0 + col_w - 10, y, th.secondary, 1.3, dash="4,3")
    s.circle(sx(x0, k_p), y_p, 3.8, th.secondary)
    legend(x0, (("greatest $|p|$, either sign", th.secondary, "4,3"),))

    # 4. The sound exposure (IEC 61252, 3.1): the running integral of the
    # square, which the meter keeps until it is reset (4.1).
    x0 = xs0[3]
    running: list[float] = []
    total = 0.0
    for q in sq:
        total += q
        running.append(total)
    s.line(x0 + 10, sk_bot, x0 + col_w - 10, sk_bot, th.muted, 1.0)
    s.path(
        _polyline(
            [sx(x0, k) for k in ks], [sk_bot - (sk_h - 6) * r / total for r in running]
        ),
        stroke=th.primary,
        sw=2.2,
    )
    y_e = sk_bot - (sk_h - 6)
    s.circle(sx(x0, n - 1), y_e, 3.8, th.primary)
    s.text(sx(x0, n - 1) - 8, y_e + 16, "$E$", 13, th.primary, anchor="end")
    legend(x0, (("the running integral of $p^2$", th.primary, ""),))

    # --- What each branch yields ------------------------------------------------
    # Every line is measured against the column in both languages: the widest
    # is 182 px of the 198 px column ("SEL: the same energy in 1 s" at 13 px).
    rows = (
        (
            "$L_{eq}$, $L_{Aeq}$ over $T$",
            "the mean square, in dB",
            "SEL: the same energy in 1 s",
            "no time constant at all",
            "reference $E_0$ = $p_0^2$ · 1 s",
            "= 400 × $10^{−12}$ Pa²s (3.12)",
        ),
        (
            "$L_{AFmax}$, $L_{ASmax}$",
            "the top of the F and S tracks",
            "$L_{10}$, $L_{50}$, $L_{90}$ of the F track",
            "exceeded $N$ % of the time",
            "F: $τ$ = 0.125 s, S: $τ$ = 1 s",
            "its first 5$τ$ left out",
        ),
        (
            "$L_{Cpeak}$",
            "the squared peak, in dB",
            "no average and no $τ$",
            "held on the display (5.1.14)",
            "one cycle of 500 Hz: 3.5 dB",
            "over the steady $L_C$ (Table 5)",
        ),
        (
            "$E$ in Pa²h",
            "kept until reset (4.1)",
            "$L_{EX,8h}$: $E$ spread over 8 h",
            "the normalized 8 h level (3.3)",
            "3.2 Pa²h is exactly 90 dB",
            "1.01 Pa²h is 85 dB (Table A.1)",
        ),
    )
    styles = (
        (top + 196, 14, th.fg),
        (top + 216, 12, th.muted),
        (top + 246, 13, th.fg),
        (top + 266, 12, th.muted),
        (top + 298, 12, th.muted),
        (top + 316, 12, th.muted),
    )
    for x0, lines in zip(xs0, rows, strict=True):
        for label, (y, size, colour) in zip(lines, styles, strict=True):
            s.text(x0 + col_w / 2, y, label, size, colour)

    # --- The one bridge between branches -----------------------------------------
    box_y = 644.0
    s.rect(30, box_y, 840, 100, th.panel, th.primary, rx=8, sw=1.8)
    s.text(
        450,
        box_y + 30,
        "SEL = $L_{Aeq}$ + 10 lg($T$ / 1 s)        "
        "$L_{EX,8h}$ = $L_{Aeq}$ + 10 lg($T$ / 8 h)",
        16,
        th.fg,
    )
    s.text(
        450,
        box_y + 56,
        "$L_{EX,8h}$ = 10 lg[$E$ / ($p_0^2$ · 8 h)], with $E$ in Pa²h and "
        "$p_0$ = 20 µPa",
        14,
        th.fg,
    )
    s.text(
        450,
        box_y + 82,
        "one energy over $T$, 1 s and 8 h; the maxima, the percentiles "
        "and the peak need the record itself",
        12,
        th.muted,
    )


def _d_block_processing(s: SVG, th: Theme) -> None:
    """Streaming block processing: carrying the filter state versus resetting it."""
    import math

    x0, blk_w, nblk, amp = 150.0, 190.0, 3, 66.0

    def _lane(gy: float, *, reset: bool, color: str) -> None:
        s.line(x0, gy, x0 + nblk * blk_w, gy, th.muted, 1.4)
        for k in range(nblk + 1):
            bx = x0 + k * blk_w
            s.line(bx, gy - amp - 16, bx, gy + 12, th.muted, 1.0, dash="3,4")
        for k in range(nblk):
            pts = []
            for j in range(31):
                frac = j / 30.0
                t = frac if reset else (k + frac)
                v = 1.0 - math.exp(-t / 0.9)
                pts.append((x0 + (k + frac) * blk_w, gy - amp * v))
            d = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts)
            s.path(d, stroke=color, sw=2.6)
            s.text(
                x0 + (k + 0.5) * blk_w,
                gy + 30,
                f"block {k + 1}",
                11,
                th.muted,
                "middle",
            )
        if reset:
            # Mark the discontinuity where each block restarts from rest.
            v_end = 1.0 - math.exp(-1.0 / 0.9)
            for k in range(1, nblk):
                bx = x0 + k * blk_w
                s.line(bx, gy - amp * v_end, bx, gy, th.secondary, 1.6, dash="2,3")
        else:
            # A small tag shows the carried state seeding the next block.
            for k in range(1, nblk):
                bx = x0 + k * blk_w
                s.rect(bx - 27, gy - amp - 40, 54, 22, th.bg, color, rx=6, sw=1.4)
                s.text(bx, gy - amp - 25, "y[-1]", 10, th.fg, "middle", mono=True)

    s.text(
        450,
        62,
        "State carried across blocks: TimeWeighting.process()",
        16,
        th.fg,
        "middle",
        bold=True,
    )
    s.text(
        450,
        84,
        "y[-1] (or the sosfilt zi vector) seeds the next block → identical "
        "to one continuous call",
        11,
        th.muted,
        "middle",
    )
    _lane(200.0, reset=False, color=th.primary)

    s.text(
        450,
        300,
        "State reset each block: reset() or a fresh call",
        16,
        th.fg,
        "middle",
        bold=True,
    )
    s.text(
        450,
        322,
        "every block restarts from rest → spurious discontinuities at the seams",
        11,
        th.muted,
        "middle",
    )
    _lane(430.0, reset=True, color=th.secondary)


def _d_multichannel(s: SVG, th: Theme) -> None:
    """How array shapes flow through a per-channel operation (time axis last)."""
    cell = 22.0

    def _grid(gx: float, gy: float, rows: int, cols: int, color: str) -> None:
        for r in range(rows):
            for c in range(cols):
                s.rect(
                    gx + c * cell, gy + r * cell, cell, cell, th.panel, color, sw=1.3
                )

    # 1-D lane.
    _grid(64, 120, 1, 8, th.primary)
    s.text(64 + 4 * cell, 108, "1-D:  (samples,)", 13, th.fg, "middle", bold=True)
    s.rect(610, 120, cell, cell, "none", th.accent, sw=2)
    s.text(610 + cell / 2, 108, "scalar", 13, th.fg, "middle", bold=True)

    # 2-D lane.
    _grid(64, 250, 3, 8, th.primary)
    s.text(
        64 + 4 * cell, 238, "2-D:  (channels, samples)", 13, th.fg, "middle", bold=True
    )
    for r in range(3):
        s.rect(610, 250 + r * cell, cell, cell, "none", th.accent, sw=2)
    s.text(610 + cell / 2, 238, "(channels,)", 13, th.fg, "middle", bold=True)

    # Shared processing box.
    s.rect(360, 96, 190, 200, th.panel, th.fg, rx=12, sw=2)
    s.text(455, 178, "reduce along", 15, th.fg, "middle", bold=True)
    s.text(
        455, 202, "axis = −1  (time)", 15, th.primary, "middle", bold=True, mono=True
    )
    s.text(455, 236, "the channel axis 0", 12, th.muted, "middle")
    s.text(455, 256, "rides through untouched", 12, th.muted, "middle")

    s.arrow(64 + 8 * cell + 4, 131, 358, 150, th.fg, 1.6)
    s.arrow(64 + 8 * cell + 4, 283, 358, 244, th.fg, 1.6)
    s.arrow(552, 150, 606, 131, th.fg, 1.6)
    s.arrow(552, 244, 606, 283, th.fg, 1.6)

    s.text(
        450,
        350,
        "A mono call returns a scalar; a $C$-channel call returns $C$ results.",
        13,
        th.fg,
        "middle",
    )
    s.text(
        450,
        374,
        "Band metrics widen the reduced axis instead: (…, bands).",
        12,
        th.muted,
        "middle",
    )


# ISO 226:2023 Table 1 (p. 4): frequency Hz -> (alpha_f, L_U dB, T_f dB), the
# same parameters the library's ``equal_loudness_contour`` implements.
_ISO226_TABLE1: tuple[tuple[float, float, float, float], ...] = (
    (20.0, 0.635, -31.5, 78.1),
    (25.0, 0.602, -27.2, 68.7),
    (31.5, 0.569, -23.1, 59.5),
    (40.0, 0.537, -19.3, 51.1),
    (50.0, 0.509, -16.1, 44.0),
    (63.0, 0.482, -13.1, 37.5),
    (80.0, 0.456, -10.4, 31.5),
    (100.0, 0.433, -8.2, 26.5),
    (125.0, 0.412, -6.3, 22.1),
    (160.0, 0.391, -4.6, 17.9),
    (200.0, 0.373, -3.2, 14.4),
    (250.0, 0.357, -2.1, 11.4),
    (315.0, 0.343, -1.2, 8.6),
    (400.0, 0.330, -0.5, 6.2),
    (500.0, 0.320, 0.0, 4.4),
    (630.0, 0.311, 0.4, 3.0),
    (800.0, 0.303, 0.5, 2.2),
    (1000.0, 0.300, 0.0, 2.4),
    (1250.0, 0.295, -2.7, 3.5),
    (1600.0, 0.292, -4.2, 1.7),
    (2000.0, 0.290, -1.2, -1.3),
    (2500.0, 0.290, 1.4, -4.2),
    (3150.0, 0.289, 2.3, -6.0),
    (4000.0, 0.289, 1.0, -5.4),
    (5000.0, 0.289, -2.3, -1.5),
    (6300.0, 0.293, -7.2, 6.0),
    (8000.0, 0.303, -11.2, 12.6),
    (10000.0, 0.323, -10.9, 13.9),
    (12500.0, 0.354, -3.5, 12.3),
)


def _iso226_spl(alpha_f: float, l_u: float, t_f: float, phon: float) -> float:
    """ISO 226:2023 Formula (1): SPL of a pure tone at loudness level ``phon``."""
    import math

    term = (4.0e-10) ** (0.3 - alpha_f) * (10 ** (0.03 * phon) - 10**0.072) + 10 ** (
        alpha_f * (t_f + l_u) / 10
    )
    return 10 / alpha_f * math.log10(term) - l_u


def _a_weight_db(f: float) -> float:
    """IEC 61672-1 Annex E analytic A-weighting, normalized to 0 dB at 1 kHz."""
    import math

    def gain(x: float) -> float:
        f1, f2, f3, f4 = 20.599, 107.653, 737.862, 12194.217
        return (f4**2 * x**4) / (
            (x**2 + f1**2) * math.sqrt((x**2 + f2**2) * (x**2 + f3**2)) * (x**2 + f4**2)
        )

    return 20 * math.log10(gain(f) / gain(1000.0))


def _d_equal_loudness_weighting(s: SVG, th: Theme) -> None:
    """Equal-loudness contours (ISO 226) inverted into the A-curve (IEC 61672-1)."""
    import math

    f_lo, f_hi = 20.0, 12500.0

    def make_fx(px0: float, px1: float) -> Callable[[float], float]:
        span = math.log10(f_hi) - math.log10(f_lo)

        def fx(f: float) -> float:
            return px0 + (math.log10(f) - math.log10(f_lo)) / span * (px1 - px0)

        return fx

    def axes(
        bx0: float, by0: float, bx1: float, by1: float, fx: Callable[[float], float]
    ) -> None:
        s.rect(bx0, by0, bx1 - bx0, by1 - by0, "none", th.muted, sw=1.2)
        for f, lab in ((20.0, "20"), (100.0, "100"), (1000.0, "1k"), (10000.0, "10k")):
            x = fx(f)
            s.line(x, by1, x, by1 + 5, th.muted, 1.2)
            s.text(x, by1 + 21, lab, 11, th.muted, "middle")
        s.text((bx0 + bx1) / 2, by1 + 42, "Frequency [Hz]", 12, th.fg, "middle")

    # --- Left panel: the equal-loudness contours ----------------------------
    lx0, lx1, ly0, ly1 = 70.0, 390.0, 110.0, 430.0
    l_fx = make_fx(lx0, lx1)

    def l_fy(db: float) -> float:  # 0 dB at the bottom, 120 dB at the top
        return ly1 - db / 120.0 * (ly1 - ly0)

    s.text(
        (lx0 + lx1) / 2,
        92,
        "Equal-loudness contours (ISO 226)",
        15,
        th.fg,
        "middle",
        bold=True,
    )
    axes(lx0, ly0, lx1, ly1, l_fx)
    for db in (0, 40, 80, 120):
        y = l_fy(db)
        s.line(lx0 - 5, y, lx0, y, th.muted, 1.2)
        s.text(lx0 - 9, y + 5, str(db), 11, th.muted, "end")
    s.text(lx0 - 20, ly0 - 12, "dB SPL", 10, th.muted, "middle")

    for phon in (20, 40, 60, 80):
        main = phon == 40
        color = th.primary if main else th.muted
        pts = [
            (l_fx(f), l_fy(_iso226_spl(a, lu, tf, phon)))
            for f, a, lu, tf in _ISO226_TABLE1
        ]
        d = "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in pts)
        s.path(d, stroke=color, sw=2.8 if main else 1.5)
        # Label each contour above its 160 Hz point, where the curves spread.
        yl = l_fy(_iso226_spl(0.391, -4.6, 17.9, phon)) - 10
        if main:
            # Centred on 500 Hz, halfway between its own contour and the
            # 60 phon one, where both lie nearly flat: 10 px over the curve
            # at 160 Hz, the contour ran through the first letters where it
            # climbs to the left.
            y40 = l_fy(_iso226_spl(0.320, 0.0, 4.4, 40))
            y60 = l_fy(_iso226_spl(0.320, 0.0, 4.4, 60))
            s.text(
                l_fx(500.0),
                (y40 + y60) / 2 + 5,
                "40 phon",
                12,
                th.primary,
                "middle",
                bold=True,
            )
        else:
            s.text(l_fx(160.0), yl, str(phon), 10, th.muted, "middle")

    # --- Middle: the inversion step ------------------------------------------
    s.text(462, 226, "invert", 14, th.fg, "middle", bold=True)
    s.text(462, 248, "0 dB at 1 kHz", 11, th.muted, "middle")
    s.arrow(400, 272, 546, 272, th.fg, 2.2)

    # --- Right panel: inverted contour vs the A-curve ------------------------
    rx0, rx1 = 558.0, 872.0
    r_fx = make_fx(rx0, rx1)

    def r_fy(db: float) -> float:  # +10 dB at the top, -70 dB at the bottom
        return ly0 + (10.0 - db) / 80.0 * (ly1 - ly0)

    s.text(
        (rx0 + rx1) / 2, 92, "A-weighting (IEC 61672-1)", 15, th.fg, "middle", bold=True
    )
    axes(rx0, ly0, rx1, ly1, r_fx)
    for db in (0, -20, -40, -60):
        y = r_fy(db)
        s.line(rx0 - 5, y, rx0, y, th.muted, 1.2)
        s.text(rx0 - 9, y + 5, signed(db), 11, th.muted, "end")
    s.text(rx0 - 20, ly0 - 12, "dB", 10, th.muted, "middle")
    s.line(rx0, r_fy(0.0), rx1, r_fy(0.0), th.muted, 0.9, dash="3,4")

    # Inverted 40-phon contour, relative to its 1 kHz value (dashed reference).
    inv = [
        (r_fx(f), r_fy(-(_iso226_spl(a, lu, tf, 40.0) - 40.0)))
        for f, a, lu, tf in _ISO226_TABLE1
    ]
    s.path(
        "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in inv),
        stroke=th.secondary,
        sw=2.0,
        dash="6,5",
    )
    # The A-curve itself, sampled densely on the log axis.
    n = 60
    aw = [
        (r_fx(f), r_fy(_a_weight_db(f)))
        for f in (f_lo * (f_hi / f_lo) ** (i / (n - 1)) for i in range(n))
    ]
    s.path(
        "M " + " L ".join(f"{px:.1f} {py:.1f}" for px, py in aw),
        stroke=th.primary,
        sw=2.8,
    )

    # Legend, bottom right of the panel (the curves live top left).
    s.line(636, 386, 668, 386, th.primary, 2.8)
    s.text(676, 391, "A-weighting (IEC 61672-1)", 11, th.fg, "start")
    s.line(636, 408, 668, 408, th.secondary, 2.0, dash="6,5")
    s.text(676, 413, "inverted 40-phon contour", 11, th.fg, "start")

    # --- Footer ---------------------------------------------------------------
    s.text(
        450,
        507,
        "A is the 40-phon contour flipped into a realizable filter: "
        "quiet sounds, where the ear discards bass hardest.",
        12,
        th.fg,
        "middle",
    )
    s.text(
        450,
        529,
        "The match is deliberately loose (a 1930s convention, not a "
        "loudness model); C mirrors the flatter ~100-phon contour.",
        11,
        th.muted,
        "middle",
    )


# ---------------------------------------------------------------------------
# Sound level meter chain (IEC 61672-1)
# ---------------------------------------------------------------------------


def _d_slm_chain(s: SVG, th: Theme) -> None:
    """IEC 61672-1 sound level meter: the acoustic front end on the left
    (windscreen, microphone, coupled class 1 calibrator) feeding the
    four-stage level chain on the right.
    """
    gy = 508.0
    s.ground(gy, 40.0, 330.0)

    # --- Acoustic calibrator, coupled onto the capsule for the level check --
    mx = 165.0
    s.text(mx, 68.0, "Sound calibrator (class 1)", 17, th.fg, bold=True)
    s.rect(mx - 62, 82.0, 124, 84, th.panel, th.fg, rx=10, sw=2)
    s.text(mx, 118.0, "94.0 dB", 22, th.secondary, bold=True, mono=True)
    s.text(mx, 146.0, "1 kHz", 17, th.muted, mono=True)
    s.rect(mx - 15, 166.0, 30, 12, th.fg, rx=3)  # coupler cavity
    s.arrow(mx, 184.0, mx, 236.0, th.secondary, 2.0)
    s.text(mx - 16, 202.0, "coupled for", 13, th.muted, anchor="end", italic=True)
    s.text(mx - 16, 222.0, "the level check", 13, th.muted, anchor="end", italic=True)

    # --- Microphone on a stand; the windscreen is fitted for measurement ----
    cap_top = 248.0
    s.mic(mx, cap_top, gy, 1.25)
    s.ellipse(mx, cap_top + 18, 42, 42, "none", th.muted, 1.6, dash="5,4")
    s.line(mx - 30, cap_top + 49, mx - 65, cap_top + 76, th.muted, 1.0)
    s.text(mx - 79, cap_top + 94, "Windscreen", 15, th.fg)

    # --- The four-stage level chain (vertical) ------------------------------
    # 440 px wide, on the Spanish "Cuadrado + ponderación temporal  F / S",
    # which is the longest stage title of the chain in either language.
    cx, bw, bh = 610.0, 440.0, 78.0
    x0 = cx - bw / 2
    chain = [
        (96.0, "Microphone + preamplifier", "free-field capsule, high-impedance stage"),
        (
            208.0,
            "Frequency weighting  A / C / Z",
            "all three are 0 dB at 1 kHz; class 1: ±0.7 dB",
        ),
        (
            320.0,
            "Squaring + time weighting  F / S",
            "exponential detector: $τ_F$ = 125 ms, $τ_S$ = 1 s",
        ),
    ]
    for by, l1, l2 in chain:
        s.rect(x0, by, bw, bh, th.panel, th.primary, rx=12, sw=2)
        s.text(cx, by + 33, l1, 18, th.fg, bold=True)
        s.text(cx, by + 59, l2, 15, th.muted)
    s.rect(x0, 432.0, bw, bh, "none", th.accent, rx=12, sw=2.4)
    s.text(cx, 465.0, "Display", 18, th.fg, bold=True)
    s.text(cx, 491.0, "$L_{AF}(t)$, $L_{AS}(t)$ in dB re 20 µPa", 15, th.accent)
    for y0 in (174.0, 286.0, 398.0):
        s.arrow(cx, y0, cx, y0 + 32, th.fg, 2.0)
    # Sound pressure into the front end.
    s.arrow(226.0, 268.0, x0 - 8, 135.0, th.fg, 2.0)


# ---------------------------------------------------------------------------
# Two-channel FRF measurement: H1 estimator and coherence
# ---------------------------------------------------------------------------


def _d_system_measurement(s: SVG, th: Theme) -> None:
    """Classic dual-channel frequency-response measurement: generator into
    amplifier and loudspeaker, microphone back in, the electrical reference
    on channel 1, and Welch cross-spectra feeding H1 and coherence.
    """

    def box(
        x0: float, x1: float, y0: float, h: float, l1: str, l2: str, color: str
    ) -> None:
        s.rect(x0, y0, x1 - x0, h, th.panel, color, rx=10, sw=2)
        s.text((x0 + x1) / 2, y0 + 30.0, l1, 15, th.fg, bold=True)
        s.text((x0 + x1) / 2, y0 + 54.0, l2, 12, th.muted)

    # 222 px wide, not 190: "Generador de señal" over "broadband noise or a
    # sweep" is 199 px of heading over 198 px of caption, and the box has to
    # hold the wider of the two languages, not the narrower.
    box(60, 282, 68, 72.0, "Signal generator", "broadband noise or a sweep", th.fg)
    box(310, 460, 68, 72.0, "Power amplifier", "its gain is in H1", th.fg)
    s.arrow(282.0, 104.0, 306.0, 104.0, th.fg, 2.0)
    s.arrow(460.0, 104.0, 496.0, 104.0, th.fg, 2.0)

    # Loudspeaker under test and the measurement microphone.
    s.rect(500, 76, 44, 56, th.panel, th.primary, rx=6, sw=2)
    s.circle(522.0, 96.0, 10.0, th.primary)
    s.circle(522.0, 96.0, 4.0, th.bg)
    s.circle(522.0, 119.0, 5.5, th.primary)
    s.text(522.0, 60.0, "Loudspeaker under test", 13, th.fg, bold=True)
    for r in (22, 38, 54):
        s.path(
            f"M {548 + r * 0.30:.0f} {104 - r * 0.55:.0f} "
            f"A {r} {r} 0 0 1 {548 + r * 0.55:.0f} {104 + r * 0.30:.0f}",
            stroke=th.accent,
            sw=1.5,
        )
    s.rect(640, 99, 12, 10, th.fg, rx=2.5)  # capsule
    s.rect(652, 96, 30, 16, th.primary, rx=5)  # mic body
    s.text(680.0, 76.0, "measurement microphone", 13, th.fg, bold=True)
    s.line(682.0, 104.0, 706.0, 104.0, th.fg, 1.8)
    s.line(706.0, 104.0, 706.0, 176.0, th.fg, 1.8)

    # Reference tap after the generator.
    s.circle(278.0, 104.0, 3.5, th.fg)
    s.line(278.0, 104.0, 278.0, 176.0, th.fg, 1.8)

    box(
        150,
        420,
        208,
        60.0,
        "Channel 1: reference $x(t)$",
        "the electrical drive signal",
        th.primary,
    )
    box(
        470,
        750,
        208,
        60.0,
        "Channel 2: response $y(t)$",
        "acoustic output at the microphone",
        th.secondary,
    )
    s.arrow(278.0, 176.0, 278.0, 204.0, th.fg, 1.8)
    s.arrow(706.0, 176.0, 706.0, 204.0, th.fg, 1.8)

    box(
        150,
        750,
        300,
        72.0,
        "Dual-channel FFT analysis (Welch)",
        "Hann segments, 50 % overlap  →  $G_{xx}(f)$, $G_{yy}(f)$, $G_{xy}(f)$",
        th.fg,
    )
    s.arrow(285.0, 268.0, 285.0, 296.0, th.fg, 1.8)
    s.arrow(610.0, 268.0, 610.0, 296.0, th.fg, 1.8)

    box(
        60,
        440,
        404,
        72.0,
        "$H_{1}(f) = G_{xy} / G_{xx}$",
        "unbiased with output noise; $H_2 = G_{yy}/G_{yx}$ for input noise",
        th.primary,
    )
    box(
        460,
        840,
        404,
        72.0,
        "$γ^{2}(f) = |G_{xy}|^2 / (G_{xx}·G_{yy})$",
        "1 for a noiseless linear path; less with output noise",
        th.secondary,
    )
    s.arrow(280.0, 372.0, 264.0, 400.0, th.fg, 1.8)
    s.arrow(620.0, 372.0, 636.0, 400.0, th.fg, 1.8)

    s.text(
        450.0,
        528.0,
        "trust $|H_1|$ only where $γ^2$ is near 1: coherence dips flag "
        "noise, distortion or unresolved delay",
        15,
        th.fg,
        bold=True,
    )


# ---------------------------------------------------------------------------
# Test-signal family panel
# ---------------------------------------------------------------------------


def _d_test_signals(s: SVG, th: Theme) -> None:
    """Labelled miniature of each stimulus: white and pink noise with their
    PSD slopes, an MLS chip stream, linear versus exponential sweeps on a
    time-frequency sketch and an IEC 60268-1 tone burst.
    """
    import math

    def tile(x: float, y: float, w: float, title: str) -> None:
        s.rect(x, y, w, 240.0, th.panel, th.fg, rx=10, sw=1.8)
        s.text(x + w / 2, y + 26.0, title, 15, th.fg, bold=True)

    def spectrum_axes(x: float, y: float) -> None:
        s.line(x, y, x + 190.0, y, th.muted, 1.2)
        s.line(x, y, x, y - 58.0, th.muted, 1.2)
        # Over the end of the axis: under it, the MLS tile's caption ran
        # into the label.
        s.text(x + 190.0, y - 5.0, "$log_{10} f$", 10, th.muted, anchor="end")

    # --- white noise -------------------------------------------------------
    tile(55, 62, 250, "White noise")
    d = "M 75 140"
    for i in range(1, 36):
        r = math.sin(i * 12.9898) * 43758.5453
        r -= math.floor(r)
        d += f" L {75 + i * 6:.0f} {140 - (r - 0.5) * 62:.1f}"
    s.path(d, stroke=th.primary, sw=1.3)
    spectrum_axes(85.0, 268.0)
    s.line(90.0, 226.0, 270.0, 226.0, th.accent, 2.2)
    s.text(180.0, 250.0, "flat PSD: 0 dB/octave", 12, th.fg)
    s.text(180.0, 294.0, "equal power per hertz", 11, th.muted)

    # --- pink noise --------------------------------------------------------
    tile(325, 62, 250, "Pink noise")
    d = "M 345 146"
    for i in range(1, 36):
        v = (
            20.0 * math.sin(0.31 * i)
            + 10.0 * math.sin(0.83 * i + 1.7)
            + 6.0 * math.sin(2.2 * i + 0.5)
            + 3.0 * math.sin(5.1 * i)
        )
        d += f" L {345 + i * 6:.0f} {140 - v:.1f}"
    s.path(d, stroke=th.primary, sw=1.3)
    spectrum_axes(355.0, 268.0)
    s.line(360.0, 214.0, 540.0, 248.0, th.accent, 2.2)
    s.text(422.0, 204.0, "−3 dB/octave PSD", 12, th.fg)
    s.text(450.0, 294.0, "equal power per octave", 11, th.muted)

    # --- MLS ---------------------------------------------------------------
    tile(595, 62, 250, "MLS")
    bits = [0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1]
    d = ""
    for i, b in enumerate(bits):
        xa, xb = 620 + i * 12, 632 + i * 12
        yl = 140 - 26 if b else 140 + 26
        d += f"{'M' if i == 0 else 'L'} {xa} {yl} L {xb} {yl} "
    s.path(d, stroke=th.primary, sw=1.6)
    spectrum_axes(625.0, 268.0)
    s.line(630.0, 226.0, 810.0, 226.0, th.accent, 2.2)
    s.text(720.0, 250.0, "flat, line spectrum", 12, th.fg)
    s.text(720.0, 294.0, "binary ±1, period $2^m − 1$ samples", 11, th.muted)

    # --- sweeps: linear vs exponential (wide tile) -------------------------
    tile(55, 318, 520, "Sweeps: linear vs exponential")
    s.line(95.0, 520.0, 545.0, 520.0, th.muted, 1.2)
    s.arrow(95.0, 520.0, 95.0, 372.0, th.muted, 1.2)
    s.text(82.0, 372.0, "$f$", 11, th.muted)
    s.text(548.0, 534.0, "$t$", 11, th.muted)
    s.line(95.0, 516.0, 540.0, 380.0, th.primary, 2.2)
    s.text(268.0, 428.0, "linear", 12, th.primary)
    pts = [
        (95, 519),
        (206, 517),
        (295, 513),
        (362, 505),
        (410, 494),
        (451, 475),
        (473, 460),
        (495, 441),
        (518, 415),
        (540, 380),
    ]
    d = "M 95 519"
    for px_, py_ in pts[1:]:
        d += f" L {px_} {py_}"
    s.path(d, stroke=th.secondary, sw=2.2)
    s.text(438.0, 508.0, "exponential", 12, th.secondary)
    s.text(
        315.0,
        548.0,
        "exponential: equal time (and energy) per octave; linear: equal time per hertz",
        11,
        th.muted,
    )

    # --- tone burst --------------------------------------------------------
    tile(595, 318, 250, "Tone burst")
    s.line(615.0, 440.0, 825.0, 440.0, th.muted, 1.2)
    d = "M 665 440"
    for i in range(1, 111):
        d += f" L {665 + i:.0f} {440 - 42 * math.sin(2 * math.pi * i / 22):.1f}"
    s.path(d, stroke=th.primary, sw=1.6)
    s.rect(663, 394, 114, 92, "none", th.secondary, rx=4, sw=1.2, dash="5,4")
    s.text(720.0, 508.0, "whole periods, starting at", 11, th.muted)
    s.text(720.0, 526.0, "a zero crossing (IEC 60268-1)", 11, th.muted)
    s.text(720.0, 548.0, "25 periods of 5 kHz = 5 ms", 10, th.fg, mono=True)

    # --- captions ----------------------------------------------------------
    s.text(
        80.0,
        590.0,
        "every stimulus is deterministic and repeatable; synchronous "
        "averaging lowers uncorrelated noise",
        14,
        th.fg,
        anchor="start",
    )
    s.text(
        80.0,
        616.0,
        "sweeps separate harmonic distortion, MLS smears it across the period, bursts probe dynamics",
        14,
        th.muted,
        anchor="start",
    )


# ---------------------------------------------------------------------------
# Welch PSD pipeline (Bendat & Piersol)
# ---------------------------------------------------------------------------


def _d_spectral_analysis(s: SVG, th: Theme) -> None:
    """The Welch estimator as a chain, with the numbers of the guide's own
    example (fs = 48 kHz, 20 s of pink noise, nperseg = 4096): 467 raw
    segments, 442 effective averages, eps_r = 4.8 %.
    """
    cx, bw = 450.0, 680.0
    x0 = cx - bw / 2

    def step(y: float, l1: str, l2: str, color: str, h: float = 58.0) -> None:
        s.rect(x0, y, bw, h, th.panel, color, rx=10, sw=2)
        s.text(cx, y + 25, l1, 15, th.fg, bold=True)
        s.text(cx, y + 45, l2, 11, th.muted)

    step(
        52,
        "Record $x(t)$: $f_s$ = 48 kHz, 20 s of pink noise",
        "960 000 samples, calibrated end to end: pascals in, Pa²/Hz out",
        th.fg,
    )
    step(
        138,
        "Split into 50 %-overlapped segments: nperseg = 4096",
        "467 segments of 85.3 ms; bin spacing $Δf = f_s/4096$ = 11.7 Hz",
        th.primary,
    )
    step(
        224,
        "Hann taper on every segment",
        "ENBW = 1.5 bins → resolution bandwidth $B_e = 1.5·Δf$ = 17.6 Hz",
        th.primary,
    )
    step(
        310,
        "One-sided $|FFT|^2$ periodogram of each segment, then average",
        "overlap correlation (Welch 1967): 467 segments → $n_d$ = "
        "442 effective averages",
        th.fg,
    )
    s.rect(x0, 396, bw, 60, "none", th.accent, rx=10, sw=2.4)
    s.text(
        cx,
        421,
        "$G_{xx}(f)$ with its chi-square confidence interval",
        15,
        th.fg,
        bold=True,
    )
    s.text(
        cx,
        443,
        "random error $ε_r = 1/√n_d$ = 4.8 %;  $2·n_d ≈ 885$ degrees of freedom",
        11,
        th.muted,
    )
    for y0, y1 in ((110, 134), (196, 220), (282, 306), (368, 392), (456, 484)):
        s.arrow(cx, y0, cx, y1, th.fg, 1.8)

    s.rect(130, 488, 640, 72, "none", th.secondary, rx=10, sw=1.6, dash="6,5")
    s.text(
        cx,
        517,
        "The trade-off: segment length buys resolution or stability, never both",
        14,
        th.secondary,
        bold=True,
    )
    s.text(
        cx,
        543,
        "longer segments → finer $B_e$ but fewer averages (larger "
        "$ε_r$); shorter → the reverse",
        11,
        th.fg,
    )


# ---------------------------------------------------------------------------
# MISO coherence conditioning (Bendat & Piersol Chapter 7)
# ---------------------------------------------------------------------------


def _d_miso_coherence(s: SVG, th: Theme) -> None:
    """Two correlated inputs through their paths into one output, then the
    Welch cross-spectral matrix, the conditioning and the per-source split,
    with the guide's measured numbers (ordinary 0.32 vs partial 0.00).
    """

    def box(
        x0: float,
        x1: float,
        y0: float,
        h: float,
        l1: str,
        l2: str,
        color: str,
        s1: int = 14,
        s2: int = 10,
    ) -> None:
        s.rect(x0, y0, x1 - x0, h, th.panel, color, rx=10, sw=2)
        s.text((x0 + x1) / 2, y0 + 24.0, l1, s1, th.fg, bold=True)
        s.text((x0 + x1) / 2, y0 + 44.0, l2, s2, th.muted)

    box(60, 280, 64, 56, "Input $x_1$", "white noise", th.primary)
    box(
        60,
        280,
        168,
        56,
        "Input $x_2 = 0.7·x_1$ + noise",
        "correlated with $x_1$",
        th.primary,
        s1=12,
    )
    s.line(110, 120, 110, 168, th.muted, 1.4, dash="5,4")

    box(340, 540, 64, 56, "Path $H_{1}(f)$", "low-pass, 400 Hz", th.fg)
    box(340, 540, 168, 56, "Path $H_{2}(f)$", "high-pass, 1.5 kHz", th.fg)
    s.arrow(280, 92, 336, 92, th.fg, 1.8)
    s.arrow(280, 196, 336, 196, th.fg, 1.8)

    s.circle(600, 144, 16, th.panel, th.fg, 2)
    s.text(600, 151, "+", 19, th.fg, bold=True)
    s.arrow(540, 92, 588, 134, th.fg, 1.8)
    s.arrow(540, 196, 588, 154, th.fg, 1.8)
    s.text(600, 74, "noise $n(t)$", 11, th.muted)
    s.arrow(600, 82, 600, 124, th.muted, 1.4)

    box(660, 850, 116, 56, "Output $y(t)$", "$G_{yy}(f)$", th.secondary)
    s.arrow(616, 144, 656, 144, th.fg, 1.8)

    s.arrow(755, 172, 755, 236, th.fg, 1.8)
    s.rect(90, 240, 720, 64, th.panel, th.fg, rx=10, sw=2)
    s.text(
        450,
        265,
        "Welch cross-spectral matrix: $G_{xx}$ (2×2) and $G_{xy}$, nperseg = 2048",
        14,
        th.fg,
        bold=True,
    )
    s.text(
        450,
        287,
        "conditioning: Schur steps $G_{ij·r!}$ (Eq. 7.94), inputs "
        "ordered by descending ordinary coherence",
        11,
        th.muted,
    )

    s.arrow(270, 304, 270, 340, th.fg, 1.8)
    s.arrow(630, 304, 630, 340, th.fg, 1.8)

    s.rect(70, 344, 370, 88, th.panel, th.primary, rx=10, sw=2)
    s.text(255, 370, "Multiple and partial coherence", 13, th.fg, bold=True)
    s.text(
        255,
        392,
        "input 2 in the 100-300 Hz band: ordinary 0.32 → partial 0.00",
        10,
        th.muted,
    )
    s.text(
        255,
        412,
        "multiple $γ^2_{y:x} = 1 − G_{nn}/G_{yy}$ ≈ 1.00 (100-300 Hz)",
        10,
        th.muted,
    )

    s.rect(460, 344, 370, 88, th.panel, th.accent, rx=10, sw=2)
    s.text(645, 370, "Contribution of each source", 13, th.fg, bold=True)
    s.text(645, 392, "$G_{vi} = γ^2_{iy·(i−1)!}·G_{yy}$ per input", 10, th.muted)
    s.text(645, 412, "$ΣG_{vi} + G_{nn} = G_{yy}$, band by band", 10, th.muted)

    s.text(
        450,
        482,
        "each conditioning step spends one average: the $i$-th "
        "ordered input carries $n_d − (i − 1)$; here $n_d$ = 242",
        12,
        th.fg,
    )
    s.text(
        450,
        506,
        "average generously before reading a small partial coherence as zero",
        11,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Time-frequency tiling trade-off (Bendat & Piersol 12.6.4.2)
# ---------------------------------------------------------------------------


def _d_time_frequency(s: SVG, th: Theme) -> None:
    """The same record tiled by a short and a long STFT window at
    fs = 16 kHz: nperseg = 256 (16 ms x 62.5 Hz cells) against 1024
    (64 ms x 15.6 Hz), with a tone and a click smeared to cell size.
    """
    panels = (
        (
            100.0,
            24.0,
            70.0,
            "Short window: nperseg = 256",
            "$T_B$ = 16 ms,  $B_e ≈ 1/T_B$ = 62.5 Hz",
            "sharp click, smeared tone",
            180.0,
            70.0,
            244.0,
            24.0,
        ),
        (
            512.0,
            96.0,
            17.5,
            "Long window: nperseg = 1024",
            "$T_B$ = 64 ms,  $B_e$ ≈ 15.6 Hz",
            "sharp tone, smeared click",
            215.0,
            17.5,
            608.0,
            96.0,
        ),
    )
    top, bot, w = 112.0, 392.0, 288.0
    for x0, cw, rh, header, res, verdict, ty, tth, cxx, cw2 in panels:
        s.text(x0 + w / 2, 74, header, 15, th.fg, bold=True)
        # tone band (frequency stripe) and click band (time stripe)
        s.rect(x0, ty, w, tth, th.primary)
        s.rect(cxx, top, cw2, bot - top, th.secondary)
        # grid over the highlighted cells
        x = x0
        while x <= x0 + w + 0.1:
            s.line(x, top, x, bot, th.muted, 0.7)
            x += cw
        y = top
        while y <= bot + 0.1:
            s.line(x0, y, x0 + w, y, th.muted, 0.7)
            y += rh
        # axes
        s.arrow(x0, bot, x0 + w + 24, bot, th.fg, 1.6)
        s.arrow(x0, bot, x0, top - 16, th.fg, 1.6)
        s.text(x0 + w + 30, bot + 16, "$t$", 12, th.muted)
        s.text(x0 - 14, top - 8, "$f$", 12, th.muted)
        s.text(x0 - 8, ty + tth / 2 + 5, "tone", 10, th.fg, anchor="end")
        s.text(cxx + cw2 / 2, 104, "click", 10, th.fg)
        s.text(x0 + w / 2, 426, res, 12, th.fg)
        s.text(x0 + w / 2, 450, verdict, 11, th.muted, italic=True)

    s.text(
        450,
        498,
        "each cell is one unaveraged estimate: $B_e·T_B ≈ 1$ and $ε_r = 1$ ($n_d = 1$)",
        13,
        th.fg,
        bold=True,
    )
    s.text(
        450,
        524,
        "the record fixes the product; nperseg only chooses how "
        "to spend it ($f_s$ = 16 kHz here)",
        12,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Cepstrum chain: echo to quefrency spike (Havelock Ch. 27)
# ---------------------------------------------------------------------------


def _d_cepstrum_echoes(s: SVG, th: Theme) -> None:
    """Signal with an 8 ms echo, rippled spectrum, log, inverse FFT, and the
    quefrency axis with the rahmonic spikes and the lifter split, using the
    guide's exact numbers (a = 0.5, 1/t0 = 125 Hz, +3.5/−6.0 dB).
    """

    def box(x0: float, x1: float, l1: str, l2: str, l3: str, color: str) -> None:
        s.rect(x0, 64, x1 - x0, 86, th.panel, color, rx=10, sw=2)
        s.text((x0 + x1) / 2, 90, l1, 13, th.fg, bold=True)
        s.text((x0 + x1) / 2, 112, l2, 10, th.muted)
        s.text((x0 + x1) / 2, 132, l3, 10, th.muted)

    # The four boxes are not equal: each is its own widest line plus the
    # same padding, so the ripply-spectrum box, which carries the longest
    # heading in Spanish, is the widest of the row and the inverse-FFT
    # box, whose Spanish caption is the longer one, is next.
    box(
        48,
        228,
        "Signal with one echo",
        "$x = s(t) + a·s(t − t_0)$",
        "$a$ = 0.5,  $t_0$ = 8 ms",
        th.fg,
    )
    box(
        252,
        458,
        "Ripply spectrum $|X(f)|$",
        "cosine ripple of period",
        "$1/t_0$ = 125 Hz",
        th.primary,
    )
    box(
        482,
        652,
        "Take the log: $ln |X|^2$",
        "the multiplicative echo",
        "becomes an additive ripple",
        th.primary,
    )
    box(
        676,
        860,
        "Inverse FFT",
        "quefrency axis, in seconds",
        "the cepstrum",
        th.secondary,
    )
    for xa in (228.0, 458.0, 652.0):
        s.arrow(xa + 2, 107, xa + 22, 107, th.fg, 1.8)
    s.arrow(768, 152, 768, 196, th.fg, 1.8)

    # Quefrency panel: source envelope, rahmonics, lifter split.
    s.rect(70, 200, 760, 240, th.panel, th.fg, rx=10, sw=1.8)
    base = 370.0
    px_ms = 34.0  # horizontal scale
    x_of = 110.0
    s.line(x_of, base, 790, base, th.fg, 1.6)
    s.arrow(790, base, 806, base, th.fg, 1.6)
    s.text(800, 390, "quefrency", 11, th.muted, anchor="end")
    # source wavelet envelope below 2 ms
    s.path(
        f"M {x_of:.0f} {base - 76:.0f} "
        f"Q {x_of + 22:.0f} {base - 10:.0f} {x_of + 68:.0f} {base:.0f}",
        stroke=th.muted,
        sw=2.0,
    )
    s.text(170, 244, "source wavelet,", 10, th.muted)
    s.text(170, 262, "below 2 ms", 10, th.muted)
    # first rahmonic at t0 = 8 ms, height a = 0.5 (scale 220 px per unit)
    x1 = x_of + 8 * px_ms
    s.line(x1, base, x1, base - 110, th.primary, 2.6)
    s.circle(x1, base - 110, 3.5, th.primary)
    s.text(x1, 246, "$a$ = 0.5 at $t_0$ = 8 ms", 12, th.primary, bold=True)
    # second rahmonic at 2 t0, height -a^2/2 = -0.125
    x2 = x_of + 16 * px_ms
    s.line(x2, base, x2, base + 27, th.secondary, 2.2)
    s.circle(x2, base + 27, 3.0, th.secondary)
    s.text(x2 + 14, base + 34, "$−a^2/2$ = −0.125", 10, th.secondary, anchor="start")
    # lifter cutoff
    xc = x_of + 4 * px_ms
    s.line(xc, 224, xc, 414, th.accent, 1.6, dash="6,5")
    s.text(xc, 432, "lifter cutoff 4 ms", 10, th.accent)
    s.text(176, 218, "lowpass: envelope", 10, th.fg)
    s.text(450, 218, "highpass: the echo ripple alone", 10, th.fg)
    # the 16 ms label sits lower to clear the downward second rahmonic
    for ms, lbl, dy in ((0.0, "0", 22.0), (8.0, "8 ms", 22.0), (16.0, "16 ms", 50.0)):
        xt = x_of + ms * px_ms
        s.line(xt, base, xt, base + 6, th.fg, 1.4)
        s.text(xt, base + dy, lbl, 10, th.muted)

    s.text(
        450,
        478,
        "rahmonics at $n·t_0$ with heights $a$, $−a^2/2$, $a^3/3$, …, "
        "whatever the source spectrum does",
        13,
        th.fg,
        bold=True,
    )
    s.text(
        450,
        504,
        "the highpass ripple swings between $20·log_{10}(1 ± a)$ = +3.5 "
        "and −6.0 dB; echo_detection reads $t_0$ and $a$ off the peak",
        11,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Time synchronous averaging (McFadden 1987)
# ---------------------------------------------------------------------------


def _d_echo_geometry(s: SVG, th: Theme) -> None:
    """Where the quefrency of an echo comes from, drawn to scale.

    Elevation at 150 units per metre: source and microphone 1.00 m apart at
    1.20 m over a hard floor, the floor-reflected path built through the image
    source, and a second panel for the side wall that gives the page's own
    8 ms example.
    """
    scale = 110.0
    c = 343.0

    # ---- Panel A: the floor reflection --------------------------------
    gy = 330.0
    s.ground(gy, 50, 470)
    sx = 130.0
    mx = sx + 1.0 * scale
    top = gy - 1.2 * scale
    s.rect(sx - 20, top - 22, 40, 44, th.panel, th.primary, rx=5, sw=2)
    s.circle(sx, top, 8, th.primary)
    s.text(sx, top - 34, "source", 15, th.fg, bold=True)
    s.mic(mx, top - 8, gy, 1.0)
    s.text(mx + 30, top - 6, "microphone", 15, th.fg, bold=True, anchor="start")
    s.line(sx + 22, top, mx - 8, top, th.primary, 2.4)
    s.text((sx + mx) / 2 + 28, top - 14, "$r_d$ = 1.00 m", 14, th.primary, bold=True)

    # Image source under the floor, and the reflected path through it.
    iy = gy + 1.2 * scale
    s.circle(sx, iy, 8, "none", th.muted, 1.6)
    s.text(sx, iy + 24, "image source", 14, th.muted)
    s.line(sx, top, sx, iy, th.muted, 1.0, dash="4,4")
    bounce_x = sx + (mx - sx) / 2.0
    s.line(sx, top, bounce_x, gy, th.secondary, 2.2)
    s.line(bounce_x, gy, mx, top - 8, th.secondary, 2.2)
    s.line(sx, iy, mx, top - 8, th.muted, 1.0, dash="4,4")
    s.circle(bounce_x, gy, 4, th.secondary)
    # Left of the image-source line, which ran through the label centred on it.
    s.text(sx - 8, gy - 46, "$r_r$ = 2.60 m", 14, th.secondary, bold=True, anchor="end")
    s.dim(mx + 46, top, mx + 46, gy, "1.20 m", size=14, label_side="right")
    s.line(mx, top - 8, mx + 46, top, th.muted, 0.9, dash="3,3")
    # The label past the dimension's end: over its middle, the unfolded
    # path from the image source ran through it.
    s.dim(sx, gy + 44, mx, gy + 44, "", size=14)
    s.text(mx + 10, gy + 49, "1.00 m", 14, th.fg, anchor="start")

    box_x = 500.0
    s.rect(box_x, 120, 356, 150, "none", th.fg, rx=10, sw=1.6)
    s.text(box_x + 178, 150, "Floor reflection", 17, th.fg, bold=True)
    dd = 2.6 - 1.0
    s.text(box_x + 178, 182, f"$Δd = r_r − r_d$ = {dd:.2f} m", 15, th.fg)
    s.text(
        box_x + 178,
        210,
        f"$t_0 = Δd / c$ = {1000 * dd / c:.1f} ms",
        15,
        th.secondary,
        bold=True,
    )
    s.text(box_x + 178, 240, "$a = R · r_d / r_r = 0.38 R$", 15, th.fg)

    # ---- Panel B: the side wall that gives 8 ms ------------------------
    s.rect(box_x, 292, 356, 168, "none", th.secondary, rx=10, sw=1.6)
    s.text(
        box_x + 178, 322, "The 8 ms example of this page", 17, th.secondary, bold=True
    )
    s.text(box_x + 178, 352, "$Δd = c · 8 ms$ = 2.74 m", 15, th.fg)
    s.text(box_x + 178, 380, "a side wall 1.37 m from the direct path", 15, th.fg)
    s.text(box_x + 178, 408, "$R = a · r_r / r_d = 3.74 a ≤ 1$", 15, th.fg)
    specular = "so $a > 0.27$ is not one specular reflection"
    s.text(
        box_x + 178,
        436,
        specular,
        s.fit_size([specular], [14, 13, 12], 336),
        th.muted,
    )

    s.text(
        450,
        512,
        "The reflection has to arrive before the record ends and "
        "at least 10 dB above its noise floor;",
        15,
        th.muted,
    )
    s.text(
        450,
        534,
        "$c$ moves about 0.6 m/s per kelvin, so convert the delay "
        "with the temperature you measured",
        15,
        th.muted,
    )


def _d_synchronous_averaging(s: SVG, th: Theme) -> None:
    """Trigger train, sliced recording, coherent average and residual, with
    the guide's numbers: T = 1/32 s at 8192 Hz, N = 40 averages, 16 dB of
    noise reduction, and McFadden's 32.05-order node example.
    """
    import math

    s.text(
        450, 64, "Tachometer: one trigger pulse per revolution", 14, th.fg, bold=True
    )
    s.line(80, 112, 840, 112, th.muted, 1.4)
    pulses = [120.0, 280.0, 440.0, 600.0, 760.0]
    for px_ in pulses:
        s.rect(px_ - 3, 86, 6, 26, th.accent, rx=1.5)
    s.dim(280, 133, 440, 133, "$T$ = 1/32 s = 256 samples", size=12)

    s.text(
        450,
        152,
        "Recording $y(t)$ at $f_s$ = 8192 Hz: the synchronous "
        "signature buried in noise",
        12,
        th.fg,
    )
    d = "M 80 196"
    for i in range(1, 191):
        x = 80 + i * 4
        v = (
            14.0 * math.sin(2 * math.pi * (x - 120.0) / 160.0)
            + 5.0 * math.sin(1.7 * i)
            + 3.5 * math.sin(4.3 * i + 1.2)
        )
        d += f" L {x:.0f} {196 - v:.1f}"
    s.path(d, stroke=th.primary, sw=1.2)
    for px_ in pulses:
        s.line(px_, 168, px_, 224, th.fg, 1.1, dash="4,4")
    s.text(450, 246, "slice at every trigger", 11, th.muted)

    # Stack of aligned one-period blocks
    for i in (2, 1, 0):
        s.rect(100 + 10 * i, 280 + 10 * i, 190, 54, th.panel, th.muted, rx=8, sw=1.4)
    s.text(205, 302, "$N$ aligned blocks", 12, th.fg, bold=True)
    s.text(205, 322, "one period $T$ each", 10, th.muted)
    s.arrow(190, 254, 195, 276, th.fg, 1.8)

    s.rect(360, 288, 220, 78, th.panel, th.primary, rx=10, sw=2)
    s.text(470, 312, "Coherent average", 14, th.fg, bold=True)
    s.text(470, 334, "$a(t) = (1/N) Σ y(t + n T)$", 11, th.primary)
    s.text(470, 354, "$N$ = 40 here", 10, th.muted)
    s.arrow(310, 322, 356, 322, th.fg, 1.8)

    s.rect(640, 288, 220, 78, th.panel, th.accent, rx=10, sw=2)
    s.text(750, 312, "The periodic part survives", 12, th.fg, bold=True)
    s.text(750, 334, "comb teeth of unit gain", 10, th.muted)
    s.text(750, 354, "at every order $k/T$", 10, th.muted)
    s.arrow(580, 327, 636, 327, th.fg, 1.8)

    s.rect(100, 420, 460, 64, "none", th.accent, rx=10, sw=1.6, dash="6,5")
    s.text(330, 446, "Asynchronous noise falls as $1/√N$", 13, th.accent, bold=True)
    s.text(
        330,
        470,
        "power $−10·log_{10} N$ = −16 dB for $N$ = 40;  amplitude gain $√N$ = 6.3",
        11,
        th.fg,
    )
    s.arrow(470, 366, 470, 416, th.fg, 1.6)

    s.rect(640, 420, 220, 64, th.panel, th.secondary, rx=10, sw=2)
    s.text(750, 442, "Residual", 12, th.fg, bold=True)
    s.text(750, 460, "record − tiled average:", 10, th.muted)
    s.text(750, 476, "everything not synchronous", 10, th.muted)
    s.arrow(750, 366, 750, 416, th.fg, 1.6)

    s.text(
        450,
        526,
        "a tone on a non-integer order is only attenuated: "
        "choose $N$ so a comb node lands on it",
        12,
        th.fg,
    )
    s.text(
        450,
        550,
        "McFadden's example: $N$ = 20 nulls the 32.05-order tone "
        "(20·32.05 = 641); the habitual $N$ = 32 does not",
        11,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Correlation-based time-delay estimation (Knapp & Carter)
# ---------------------------------------------------------------------------


def _d_miso_setup(s: SVG, th: Theme) -> None:
    """Instrumenting a two-source MISO measurement, plan view.

    A plant room drawn to scale at 55 units per metre: a fan and a compressor
    3 m apart, one reference sensor each, the receiver microphone 4 m from
    the fan, the airborne leakage that correlates the two references, and the
    single simultaneously sampling front end every channel has to share.
    """
    import math

    scale = 55.0  # drawing units per metre
    x0, y0 = 46.0, 92.0
    room_w, room_h = 9.2 * scale, 5.2 * scale
    s.rect(x0, y0, room_w, room_h, th.panel, th.fg, rx=4, sw=2.4)
    s.text(x0 + 12, y0 + 24, "Plant room: plan", 15, th.muted, anchor="start")

    # -- Machine A: a fan on resilient mounts ------------------------------
    ax, ay = x0 + 1.6 * scale, y0 + 3.4 * scale
    s.rect(ax - 40, ay - 40, 80, 80, th.bg, th.primary, rx=6, sw=2.2)
    s.circle(ax, ay, 24, "none", th.primary, 1.6)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        s.line(ax, ay, ax + 22 * math.cos(a), ay + 22 * math.sin(a), th.primary, 1.6)
    s.text(ax, ay - 52, "A: fan", 15, th.fg, bold=True)
    for k in (-1, 1):
        s.rect(ax + k * 26 - 8, ay + 40, 16, 9, th.muted, rx=2)
    s.rect(ax + 26 - 7, ay + 26, 14, 14, th.secondary, th.fg, rx=2, sw=1.2)
    # Under the sensor and clear of the 3.0 m dimension's arrowhead, which it
    # sat on.
    s.text(ax + 26, ay + 66, "ref 1", 14, th.secondary, bold=True)

    # -- Machine B: a compressor -------------------------------------------
    bx, by = ax + 3.0 * scale, ay
    s.rect(bx - 36, by - 36, 72, 72, th.bg, th.primary, rx=6, sw=2.2)
    s.rect(bx - 20, by - 16, 40, 32, th.panel, th.primary, rx=3, sw=1.4)
    # Its name is set further down, over the propagation paths that cross it.
    mic2_x = bx + 36 + 0.3 * scale
    s.circle(mic2_x, by, 7, th.bg, th.secondary, 2.0)
    # The label beside the short span, which it overran into the box's
    # corner and the witness line.
    s.dim(bx + 36, by + 52, mic2_x, by + 52, "", size=13)
    s.text(mic2_x + 8, by + 57, "0.3 m", 13, th.fg, "start")
    s.line(mic2_x, by + 10, mic2_x, by + 50, th.muted, 0.9, dash="3,3")
    s.text(mic2_x + 20, by + 6, "ref 2", 14, th.secondary, bold=True, anchor="start")
    s.dim(ax, y0 + room_h - 22, bx, y0 + room_h - 22, "3.0 m", size=14)

    # -- Receiver microphone at the operator position ----------------------
    rx_, ry = x0 + 7.6 * scale, y0 + 1.0 * scale
    s.circle(rx_, ry, 8, th.bg, th.accent, 2.4)
    s.text(rx_, ry - 18, "receiver", 15, th.accent, bold=True)
    s.text(rx_ - 16, ry + 6, "1.5 m high", 13, th.muted, anchor="end")
    s.line(ax, ay, rx_, ry, th.accent, 1.2, dash="6,5")
    s.line(bx, by, rx_, ry, th.accent, 1.2, dash="6,5")
    s.dim(ax, ay - 74, rx_, ry - 40, "4.0 m", size=13)
    # The compressor's name on a backing of the room's own colour, because
    # the path from the fan to the receiver runs through where it stands.
    name = "B: compressor"
    width = s.text_width(name, 15, bold=True)
    s.rect(bx - width / 2 - 3, by - 62, width + 6, 19, th.panel)
    s.text(bx, by - 48, name, 15, th.fg, bold=True)

    # -- The leakage that correlates the two references --------------------
    s.arrow(ax + 44, ay + 16, mic2_x - 11, by + 6, th.secondary, 1.8)
    # Under the leakage arrow, between the two machines: further right it
    # ran into the compressor's box.
    s.text(ax + 72, ay + 40, "leakage", 13, th.secondary, bold=True)

    # -- Legend under the room ---------------------------------------------
    ly = y0 + room_h + 26
    s.circle(x0 + 8, ly - 5, 5, th.secondary)
    s.text(
        x0 + 22,
        ly,
        "ref 1: accelerometer stud-mounted on the fan foot",
        14,
        th.fg,
        anchor="start",
    )
    s.circle(x0 + 8, ly + 21, 5, th.secondary)
    s.text(
        x0 + 22,
        ly + 26,
        "ref 2: microphone 0.3 m from the casing",
        14,
        th.fg,
        anchor="start",
    )
    s.circle(x0 + 8, ly + 47, 5, th.secondary)
    s.text(
        x0 + 22,
        ly + 52,
        "the leakage is what correlates the two inputs",
        14,
        th.secondary,
        anchor="start",
    )

    # -- Acquisition column -------------------------------------------------
    cx = x0 + room_w + 88
    s.rect(cx - 78, 100, 156, 172, "none", th.primary, rx=10, sw=1.8)
    s.text(cx, 126, "One front end", 15, th.primary, bold=True)
    for i, name in enumerate(("ref 1  $x_1$", "ref 2  $x_2$", "receiver  $y$")):
        s.rect(cx - 62, 140 + i * 32, 124, 24, th.panel, th.fg, rx=4, sw=1.2)
        s.text(cx, 157 + i * 32, name, 12, th.fg)
    s.text(cx, 258, "one clock, fixed gains", 12, th.muted)

    s.rect(cx - 78, 292, 156, 128, "none", th.secondary, rx=10, sw=1.8)
    s.text(cx, 318, "Before reading", 15, th.secondary, bold=True)
    s.text(cx, 338, "the split", 15, th.secondary, bold=True)
    s.text(cx, 364, "coherence between", 12, th.fg)
    s.text(cx, 382, "$x_1$ and $x_2$ > 0.9", 12, th.fg, bold=True)
    s.text(cx, 402, "⇒ do not attribute", 12, th.fg)

    s.text(
        450,
        552,
        "Conditioning separates only what the references "
        "separate: one sensor per source, all sampled together",
        15,
        th.muted,
    )


def _d_tsa_setup(s: SVG, th: Theme) -> None:
    """The two channels a time synchronous average needs, on a gearbox.

    A single-stage gearbox in elevation: the input shaft at 1800 r/min with
    one strip of reflective tape and an optical tacho head 20 mm away, a
    37-tooth pinion driving an 89-tooth wheel, and a stud-mounted
    accelerometer on the pedestal bearing of the input shaft.
    """
    import math

    # The housing starts 70 px in from the sheet's margin, which leaves the
    # accelerometer's labels room outside it: set against the margin, the
    # housing's wall ran through all three, and the bearing and the tacho
    # head were narrower than their own names.
    gy = 400.0
    x0 = 144.0
    s.ground(gy, 40, 530)
    s.rect(x0, 140, 380, gy - 140, th.panel, th.fg, rx=6, sw=2.2)
    s.text(x0, 128, "Gearbox: elevation", 15, th.muted, anchor="start")

    shaft_y = 252.0
    px, pr = 316.0, 38.0
    wx, wr = 432.0, 78.0
    for cx, r in ((px, pr), (wx, wr)):
        s.circle(cx, shaft_y, r, th.bg, th.primary, 2.2)
        s.circle(cx, shaft_y, 6, th.fg)
        for k in range(24):
            a = 2 * math.pi * k / 24
            s.line(
                cx + r * math.cos(a),
                shaft_y + r * math.sin(a),
                cx + (r + 7) * math.cos(a),
                shaft_y + (r + 7) * math.sin(a),
                th.primary,
                1.4,
            )
    # The pinion's caption drops past the wheel instead of stopping beside
    # it, and starts clear of the pedestal bearing.
    s.text(240, shaft_y + 128, "pinion, 37 teeth", 14, th.fg, bold=True, anchor="start")
    s.text(wx, shaft_y + wr + 26, "wheel, 89 teeth", 14, th.fg, bold=True)

    # Input shaft, the reflective tape and the optical tacho head, each
    # named where nothing else is drawn: the tacho above its head, the tape
    # under the shaft, clear of the tacho's arrow and of the 20 mm
    # dimension, which both ran through the tape's name above it.
    s.line(x0 + 8, shaft_y, px, shaft_y, th.fg, 4.0)
    s.rect(240, shaft_y - 9, 12, 18, th.secondary, rx=2)
    s.text(246, shaft_y + 26, "tape", 13, th.secondary, bold=True)
    s.rect(220, shaft_y - 86, 52, 32, th.panel, th.secondary, rx=5, sw=1.8)
    s.text(246, shaft_y - 94, "tacho", 13, th.secondary, bold=True)
    s.arrow(246, shaft_y - 52, 246, shaft_y - 16, th.secondary, 1.6)
    s.dim(208, shaft_y - 52, 208, shaft_y - 14, "20 mm", size=12, label_side="left")

    # Pedestal bearing on the input shaft, with the accelerometer on its face.
    s.rect(168, shaft_y + 10, 52, gy - shaft_y - 10, th.bg, th.fg, rx=3, sw=1.8)
    s.text(194, gy - 12, "bearing", 12, th.muted)
    s.rect(146, shaft_y + 46, 22, 26, th.primary, th.fg, rx=3, sw=1.4)
    s.arrow(144, shaft_y + 59, 116, shaft_y + 59, th.primary, 1.8)
    s.text(138, shaft_y + 96, "accel.", 13, th.fg, bold=True, anchor="end")
    s.text(138, shaft_y + 114, "(stud)", 12, th.muted, anchor="end")
    s.text(138, shaft_y + 44, "load direction", 13, th.primary, anchor="end")

    s.text(
        260, 442, "1800 r/min  →  $T$ = 33.3 ms per revolution", 15, th.fg, bold=True
    )
    s.text(
        260, 468, "mesh frequency 37 × 30 = 1110 Hz; five mesh harmonics", 14, th.muted
    )
    s.text(260, 490, "need $f_s ≥ 2.56 × 5550$ = 14.2 kHz", 14, th.muted)

    # -- Right column: the acquisition and the slicing --------------------
    cx = 700.0
    s.rect(cx - 160, 130, 320, 116, "none", th.primary, rx=10, sw=1.8)
    s.text(cx, 158, "One front end, one clock", 15, th.primary, bold=True)
    s.rect(cx - 140, 174, 130, 26, th.panel, th.fg, rx=4, sw=1.2)
    s.text(cx - 75, 192, "tacho", 13, th.fg, mono=True)
    s.rect(cx + 10, 174, 130, 26, th.panel, th.fg, rx=4, sw=1.2)
    s.text(cx + 75, 192, "vibration", 13, th.fg, mono=True)
    s.text(cx, 226, "$f_s$ = 25.6 kHz, gains fixed", 13, th.muted)

    base = 330.0
    s.line(cx - 160, base, cx + 160, base, th.fg, 1.4)
    for k in range(5):
        x = cx - 150 + k * 75
        s.line(x, base, x, base - 34, th.secondary, 2.2)
        s.line(x, base - 34, x + 8, base - 34, th.secondary, 2.2)
        s.line(x + 8, base - 34, x + 8, base, th.secondary, 2.2)
        if k < 4:
            s.line(x, base + 12, x, base + 96, th.muted, 1.0, dash="5,4")
    s.text(cx, base - 50, "one pulse per revolution", 14, th.secondary, bold=True)
    wave = "M " + " L ".join(
        f"{cx - 150 + i * 3:.0f} "
        f"{base + 56 + 22 * math.sin(i * 0.9) * math.cos(i * 0.21):.0f}"
        for i in range(101)
    )
    s.path(wave, stroke=th.primary, sw=1.2)
    s.text(cx, base + 122, "the pulse is the block boundary", 14, th.fg)
    s.text(cx, base + 146, "record $N + 1$ revolutions", 14, th.muted)

    s.text(
        450,
        552,
        "One tacho pulse per turn, an accelerometer in the load "
        "direction: the period is measured, not assumed",
        15,
        th.muted,
    )


def _d_correlation_delay(s: SVG, th: Theme) -> None:
    """Two microphones, the extra path c*tau, and the correlogram where the
    direct correlator smears while GCC-PHAT spikes at the guide's delay of
    20 samples at 8192 Hz (2.44 ms, 0.84 m at 343 m/s).
    """
    gy = 300.0
    s.ground(gy, 60, 840)

    # Source loudspeaker, top left
    s.rect(80, 64, 36, 44, th.panel, th.primary, rx=5, sw=2)
    s.circle(98, 80, 8, th.primary)
    s.circle(98, 80, 3, th.bg)
    s.circle(98, 98, 4.5, th.primary)
    s.text(98, 52, "source", 11, th.fg, bold=True)
    for r in (18, 30):
        s.path(
            f"M {120 + r * 0.30:.0f} {86 - r * 0.55:.0f} "
            f"A {r} {r} 0 0 1 {120 + r * 0.55:.0f} {86 + r * 0.30:.0f}",
            stroke=th.accent,
            sw=1.5,
        )

    # Rays to the two microphones (drawn first, mics overlay them)
    s.line(120, 90, 330, 188, th.muted, 1.2, dash="6,5")
    s.line(120, 90, 570, 188, th.muted, 1.2, dash="6,5")
    # Wavefront arc through mic 1 crossing the second ray at P
    s.path("M 330 188 A 232 232 0 0 0 346 139", stroke=th.fg, sw=1.6)
    s.line(346.4, 139.3, 570, 188, th.secondary, 2.6)
    s.text(
        470, 120, "$Δr = c·τ_0$ ≈ 0.84 m  ($c$ = 343 m/s)", 12, th.secondary, bold=True
    )

    s.mic(330, 190, gy, 1.0)
    s.mic(570, 190, gy, 1.0)
    s.text(314, 258, "mic 1: $x(t)$", 11, th.fg, bold=True, anchor="end")
    s.text(586, 258, "mic 2: $y(t)$", 11, th.fg, bold=True, anchor="start")
    s.dim(330, 272, 570, 272, "spacing $d$", size=12)
    s.text(450, 242, "$sin θ = c·τ_0 / d$", 12, th.fg)

    # Correlogram panel
    s.rect(70, 340, 760, 210, th.panel, th.fg, rx=10, sw=1.8)
    s.text(
        450,
        366,
        "cross-correlation against lag: $y(t) = α·x(t − τ_0) + n(t)$",
        13,
        th.fg,
        bold=True,
    )
    base = 505.0
    s.line(110, base, 770, base, th.fg, 1.6)
    s.arrow(770, base, 790, base, th.fg, 1.6)
    x_tau = 518.0
    s.path(
        f"M 388 {base:.0f} Q {x_tau:.0f} 415 648 {base:.0f}", stroke=th.muted, sw=2.0
    )
    s.text(688, 432, "direct correlator: broad peak", 11, th.muted)
    s.line(x_tau, base, x_tau, 400, th.primary, 2.6)
    s.circle(x_tau, 400, 3.5, th.primary)
    s.text(x_tau, 388, "GCC-PHAT: sharp spike", 11, th.primary, bold=True)
    s.text(150, 400, "$ψ(f) = 1/|G_{xy}|$", 11, th.fg, anchor="start")
    s.line(250, base - 5, 250, base + 5, th.fg, 1.4)
    s.text(250, base + 21, "0", 10, th.muted)
    s.text(x_tau, base + 21, "$τ_0$ = 20 samples / 8192 Hz = 2.44 ms", 11, th.fg)

    s.text(
        450,
        580,
        "parabolic peak interpolation + ×16 local upsampling → "
        "error below 0.002 samples",
        12,
        th.fg,
    )
    s.text(
        450,
        604,
        "the 'phase' route reads the same $τ_0$ from the slope of "
        "the unwrapped cross-spectrum phase",
        11,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Data qualification decision flow (Bendat & Piersol 10.3)
# ---------------------------------------------------------------------------


def _d_data_qualification(s: SVG, th: Theme) -> None:
    """Record to segment mean squares to the reverse arrangement count and
    the Table A.6 verdict, with the guide's numbers: N = 20 segments,
    acceptance (64, 125), A = 91 accepted and A = 7 rejected.
    """
    cx = 450.0
    x0, bw = 170.0, 560.0

    def step(y: float, l1: str, l2: str, color: str) -> None:
        s.rect(x0, y, bw, 54, th.panel, color, rx=10, sw=2)
        s.text(cx, y + 23, l1, 14, th.fg, bold=True)
        s.text(cx, y + 43, l2, 10, th.muted)

    step(52, "Time record $x(t)$", "before trusting any PSD, Leq or GUM average", th.fg)
    step(
        134,
        "Mean square per interval: $N$ = 20 equal segments",
        "each interval long against the record's lowest frequencies; also "
        "rms, mean or variance",
        th.primary,
    )
    step(
        216,
        "Reverse arrangement count $A$",
        "pairs $i < j$ with $x_i > x_j$; trend-free mean $μ_A = N(N−1)/4$ = 95",
        th.primary,
    )
    for y0, y1 in ((106, 130), (188, 212), (270, 294)):
        s.arrow(cx, y0, cx, y1, th.fg, 1.8)

    # Decision diamond
    s.path(
        f"M 240 340 L {cx:.0f} 296 L 660 340 L {cx:.0f} 384 Z",
        fill=th.panel,
        stroke=th.fg,
        sw=2,
    )
    s.text(cx, 336, "$64 < A ≤ 125$ ?", 15, th.fg, bold=True)
    s.text(cx, 358, "(Table A.6, $α = 0.05$)", 10, th.muted)

    s.arrow(390, 380, 250, 426, th.secondary, 1.8)
    s.text(298, 392, "no", 12, th.secondary, bold=True)
    s.arrow(510, 380, 650, 426, th.accent, 1.8)
    s.text(602, 392, "yes", 12, th.accent, bold=True)

    s.rect(60, 430, 360, 96, th.panel, th.secondary, rx=10, sw=2.2)
    s.text(240, 458, "Nonstationary: do not average", 13, th.fg, bold=True)
    s.text(240, 482, "+20 % gain ramp: $A = 7$ → rejected", 11, th.secondary)
    s.text(
        240, 504, "split at the change, or go short-time (spectrogram)", 10, th.muted
    )

    s.rect(480, 430, 360, 96, th.panel, th.accent, rx=10, sw=2.2)
    s.text(660, 458, "Stationary: analyse", 13, th.fg, bold=True)
    s.text(660, 482, "steady noise: $A = 91$ → accepted", 11, th.accent)
    s.text(660, 504, "the chi-square CIs and error formulas hold", 10, th.muted)

    s.text(
        cx,
        566,
        'the runs test (method="runs") is the two-sided '
        "companion: too many runs is as suspect as too few",
        12,
        th.fg,
    )
    s.text(
        cx,
        590,
        "a frequency glide can hide from the mean square: test "
        'statistic="mean" or band-filtered copies too',
        11,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Sound level meter pipeline: the library functions behind each IEC 61672-1
# stage, as assembled by the "Build a sound level meter" guide
# ---------------------------------------------------------------------------


def _d_slm_pipeline(s: SVG, th: Theme) -> None:
    """The guide's own pipeline: the two recordings that go in, the single
    sensitivity factor that makes them physical, and the three readout
    branches (display statistics, integrated levels, band spectrum) that a
    class 1 meter reports, closed by the class verifiers.
    """
    # --- The two recordings the meter needs, from the same input chain -----
    for x0, l1, l2 in (
        (40.0, "Calibrator tone", "94 dB at 1 kHz  (IEC 60942)"),
        (480.0, "Measurement recording", "same microphone, same gain"),
    ):
        s.rect(x0, 54, 380, 68, th.panel, th.primary, rx=12, sw=2)
        s.text(x0 + 190, 84, l1, 18, th.fg, bold=True)
        s.text(x0 + 190, 108, l2, 14, th.muted)

    # --- The sensitivity factor, derived from the calibrator tone ----------
    s.arrow(230, 122, 230, 150, th.fg, 2.0)
    s.rect(40, 150, 380, 78, th.panel, th.primary, rx=12, sw=2)
    s.text(
        230,
        182,
        "sensitivity(calibrator, target_spl=94.0, fs=fs)",
        11,
        th.fg,
        bold=True,
        mono=True,
    )
    s.text(230, 208, "the factor $S$ in pascals per digital unit", 13, th.muted)

    # --- Calibrated pressure: where both inputs meet -----------------------
    s.arrow(230, 228, 230, 266, th.fg, 2.0)
    s.arrow(670, 122, 670, 266, th.fg, 2.0)
    s.rect(120, 266, 660, 64, "none", th.accent, rx=12, sw=2.4)
    s.text(
        450,
        296,
        "Calibrated pressure   $p(t) = S · x(t)$   in pascals",
        18,
        th.fg,
        bold=True,
    )
    s.text(
        450, 320, "every level function takes $S$ as calibration_factor=", 14, th.accent
    )

    # --- Three readout branches, one guide section each --------------------
    branches = [
        (
            40.0,
            "Display and statistics",
            "weighting_filter(curve='A')",
            "time_weighting(mode='fast')",
            "exponential detector, $τ_F$ = 125 ms",
            "$L_{AF}(t)$   $L_{10} / L_{50} / L_{90}$",
        ),
        (
            320.0,
            "Integrated levels",
            "laeq · sel · lc_peak",
            "",
            "energy average, no ballistics",
            "$L_{Aeq}$   $L_{AE}$   $L_{Cpeak}$",
        ),
        (
            600.0,
            "Band spectrum",
            "octave_filter(fraction=3)",
            "OctaveFilterBank",
            "IEC 61260-1 band edges",
            "one-third-octave band levels",
        ),
    ]
    for x0, head, code1, code2, note, out in branches:
        cx = x0 + 130
        s.arrow(cx, 330, cx, 370, th.fg, 2.0)
        s.rect(x0, 370, 260, 104, th.panel, th.primary, rx=12, sw=2)
        s.text(cx, 400, head, 16, th.fg, bold=True)
        # A branch with a single call keeps its one line centred in the gap the
        # two-line branches use, rather than leaving a hole under the heading.
        s.text(cx, 426 if code2 else 437, code1, 12, th.fg, mono=True)
        if code2:
            s.text(cx, 448, code2, 12, th.fg, mono=True)
        s.text(cx, 468, note, 12, th.muted)
        s.arrow(cx, 474, cx, 510, th.fg, 2.0)
        s.rect(x0, 510, 260, 62, "none", th.accent, rx=12, sw=2.2)
        s.text(cx, 538, out, 13, th.accent, bold=True)
        s.text(cx, 560, "dB re 20 µPa", 12, th.muted)

    # --- Class verification closes the guide -------------------------------
    for cx in (170.0, 730.0):
        s.line(cx, 572, cx, 588, th.muted, 1.4, dash="5,4")
        s.arrow(cx, 588, cx, 596, th.muted, 1.4)
    s.rect(40, 596, 820, 62, "none", th.secondary, rx=12, sw=2, dash="7,5")
    s.text(
        450,
        624,
        "Class verification against the acceptance limits",
        15,
        th.secondary,
        bold=True,
    )
    s.text(
        450,
        648,
        "verify_weighting_class (IEC 61672-1 Table 3)  ·  "
        "verify_filter_class (IEC 61260-1 Table 1)",
        12,
        th.muted,
    )


# ---------------------------------------------------------------------------
# Calibration data flow: from the two recordings to levels in dB SPL
# ---------------------------------------------------------------------------


def _d_calibration_dataflow(s: SVG, th: Theme) -> None:
    """The data flow of the calibration guide: the calibrator recording
    yields one factor, the measurement recording carries the samples, and
    every level function takes the factor as ``calibration_factor``. The
    dBFS reference frame is the branch taken when no factor exists.
    """
    # --- The two recordings, which must come from the same untouched chain --
    for x0, l1, l2 in (
        (40.0, "Calibrator recording", "1 kHz tone through the chain"),
        (500.0, "Measurement recording", "the same chain, untouched"),
    ):
        s.rect(x0, 54, 360, 72, th.panel, th.primary, rx=12, sw=2)
        s.text(x0 + 180, 84, l1, 18, th.fg, bold=True)
        s.text(x0 + 180, 108, l2, 14, th.muted)
    s.line(400, 90, 500, 90, th.muted, 1.4, dash="6,5")
    s.text(
        450,
        152,
        "nothing in the chain may change between the two",
        13,
        th.muted,
        italic=True,
    )

    # --- sensitivity(): the equation of the guide, plus its stability check -
    s.arrow(220, 126, 220, 166, th.fg, 2.0)
    s.rect(40, 166, 360, 88, th.panel, th.primary, rx=12, sw=2)
    s.text(
        220,
        196,
        "sensitivity(calibrator, target_spl=94.0, fs=fs)",
        10,
        th.fg,
        bold=True,
        mono=True,
    )
    # Parked: the 10^(L_cal / 20) exponent carries a subscript inside
    # the superscript, one script level more than the composer sets, so
    # the formula stays plain until that family is adjudicated.
    s.text(220, 222, "S = p_ref · 10^(L_cal / 20) / x̃_ref", 14, th.fg)
    s.text(220, 244, "fs enables the IEC 60942 stability check", 12, th.muted)

    # --- The factor itself --------------------------------------------------
    s.arrow(220, 254, 220, 290, th.fg, 2.0)
    s.rect(40, 290, 360, 72, "none", th.accent, rx=12, sw=2.4)
    s.text(220, 320, "calibration_factor  S", 15, th.fg, bold=True, mono=True)
    s.text(220, 344, "pascals per digital unit", 14, th.accent)

    # --- Where the factor and the samples meet ------------------------------
    s.arrow(240, 362, 320, 400, th.fg, 2.0)
    s.arrow(680, 126, 680, 400, th.fg, 2.0)
    s.rect(60, 400, 780, 86, th.panel, th.fg, rx=12, sw=2)
    s.text(
        450,
        430,
        "octave_filter · leq · laeq · sel · ln_levels · lc_peak · OctaveFilterBank",
        12,
        th.fg,
        mono=True,
    )
    s.text(
        450,
        456,
        "every level function accepts calibration_factor=",
        15,
        th.fg,
        bold=True,
    )
    s.text(450, 478, "one factor for the whole library", 12, th.muted)

    # --- The physical result, and the dBFS branch beside it -----------------
    s.arrow(450, 486, 450, 522, th.fg, 2.0)
    s.rect(270, 522, 360, 64, "none", th.accent, rx=12, sw=2.4)
    s.text(450, 550, "Levels in dB SPL", 18, th.fg, bold=True)
    s.text(450, 574, "re 20 µPa", 14, th.accent, mono=True)
    s.rect(650, 514, 210, 80, "none", th.secondary, rx=12, sw=1.8, dash="7,5")
    s.text(755, 542, "No calibrator?", 14, th.secondary, bold=True)
    s.text(755, 564, "$S = 1$, samples read as Pa", 11, th.muted)
    s.text(755, 584, "use dbfs=True for dBFS", 11, th.fg)


# ---------------------------------------------------------------------------
# Filter bank data flow: the decimation decision and the band outputs
# ---------------------------------------------------------------------------


def _d_bank_dataflow(s: SVG, th: Theme) -> None:
    """The two numerical-stability strategies of the filter bank as one
    path: every band is a biquad cascade, and a low band takes the decimated
    branch first. Both branches end in the band level; ``sigbands=True``
    also brings the band signal back to the input rate.
    """
    # --- Input and the per-band decision ------------------------------------
    s.rect(290, 54, 320, 64, th.panel, th.fg, rx=12, sw=2)
    s.text(450, 84, "Input signal  $x(t)$", 18, th.fg, bold=True)
    s.text(450, 108, "sample rate $f_s$", 14, th.muted)
    s.arrow(450, 118, 450, 132, th.fg, 2.0)
    s.path("M 450 132 L 610 184 L 450 236 L 290 184 Z", th.panel, th.primary, sw=2)
    s.text(450, 180, "Room to decimate?", 17, th.fg, bold=True)
    s.text(450, 204, "$f_s / 2 ≥ 32 · f_{upper}$", 12, th.muted)

    s.line(290, 184, 190, 184, th.fg, 2.0)
    s.arrow(190, 184, 190, 244, th.fg, 2.0)
    s.text(240, 172, "yes", 13, th.accent, bold=True)
    s.line(610, 184, 710, 184, th.fg, 2.0)
    s.arrow(710, 184, 710, 360, th.fg, 2.0)
    s.text(660, 172, "no", 13, th.secondary, bold=True)

    # --- The decimated branch ----------------------------------------------
    s.rect(50, 244, 280, 80, th.panel, th.primary, rx=12, sw=2)
    s.text(190, 274, "resample_poly(1, M)", 13, th.fg, bold=True, mono=True)
    s.text(190, 298, "$M = floor[(f_s / 2) / (16 · f_{upper})]$", 11, th.muted)
    s.text(190, 318, "poles stay clear of $z = 1$", 12, th.muted)
    s.arrow(190, 324, 190, 360, th.fg, 2.0)

    # --- Both branches are the same biquad cascade at a different rate ------
    for x0, head in (
        (50.0, "SOS band filter at $f_s / M$"),
        (570.0, "SOS band filter at $f_s$"),
    ):
        s.rect(x0, 360, 280, 84, th.panel, th.primary, rx=12, sw=2)
        s.text(x0 + 140, 390, head, 15, th.fg, bold=True)
        s.text(x0 + 140, 414, "cascaded biquads", 13, th.muted)
        s.text(x0 + 140, 434, "designed on the IEC 61260-1 band edges", 10, th.muted)
    s.rect(340, 260, 220, 96, "none", th.secondary, rx=12, sw=1.8, dash="7,5")
    s.text(450, 288, "Every band filter", 12, th.secondary, bold=True)
    s.text(450, 308, "is a biquad cascade", 12, th.secondary, bold=True)
    s.text(450, 332, "not one high-order", 12, th.muted)
    s.text(450, 350, "(b, a) pair", 12, th.muted)

    # --- The band level, and the optional band signal -----------------------
    s.arrow(190, 444, 330, 496, th.fg, 2.0)
    s.arrow(710, 444, 570, 496, th.fg, 2.0)
    s.rect(270, 500, 360, 76, "none", th.accent, rx=12, sw=2.4)
    s.text(450, 530, "Band level", 18, th.fg, bold=True)
    s.text(450, 554, "RMS or peak, in dB re 20 µPa", 14, th.accent)
    s.rect(50, 604, 800, 62, "none", th.secondary, rx=12, sw=1.8, dash="7,5")
    s.text(
        450,
        632,
        "sigbands=True also returns the band signal at $f_s$",
        15,
        th.secondary,
        bold=True,
    )
    s.text(
        450,
        654,
        "the decimated branch is interpolated back with resample_poly(M, 1)",
        12,
        th.muted,
    )


# ---------------------------------------------------------------------------
# d27 - The infrasound measurement chain (ISO 7196 Annex A)
# ---------------------------------------------------------------------------

_G_POLES_HZ: tuple[tuple[float, float], ...] = (
    (-0.707, 0.707),
    (-0.707, -0.707),
    (-19.27, 5.16),
    (-19.27, -5.16),
    (-14.11, 14.11),
    (-14.11, -14.11),
    (-5.16, 19.27),
    (-5.16, -19.27),
)


def _g_weight_db(f: float) -> float:
    """ISO 7196:1995 G weighting from its Table 1 poles, 0 dB at 10 Hz."""
    import math

    def gain(x: float) -> float:
        jw = 2j * math.pi * x
        num = jw**4  # four zeros at the origin
        den = 1.0 + 0j
        for re, im in _G_POLES_HZ:
            den *= jw - 2 * math.pi * complex(re, im)
        return abs(num / den)

    return 20 * math.log10(gain(f) / gain(10.0))


def _d_infrasound_chain(s: SVG, th: Theme) -> None:
    """The chain that has to deliver 0,25 Hz, and where it usually does not.

    Left: section through the ground board with the capsule at its centre,
    the static-pressure equalisation vent called out, and the two windscreens.
    Middle: the three electrical stages. Right: the G curve against the
    chain's own high-pass corner, so the usable band is the overlap.
    Geometry after ISO 7196:1995 Annex A (A.2 microphone, A.5 integrator).
    """
    import math

    # -- Left: the capsule on the ground board ------------------------------
    gy = 372.0
    cx = 168.0
    s.ground(gy, 34, 300)
    s.rect(cx - 118, gy - 12, 236, 12, th.panel, th.fg, sw=2)  # hard board
    s.text(cx, gy + 40, "hard board on the ground", 15, th.fg, bold=True)
    s.text(cx, gy + 62, "capsule flush at its centre", 14, th.muted)

    # Capsule, drawn flush with the board, plus its equalisation vent.
    s.rect(cx - 26, gy - 40, 52, 28, th.panel, th.primary, rx=4, sw=2)
    s.rect(cx - 26, gy - 44, 52, 6, th.fg, rx=2)  # diaphragm
    s.circle(cx + 20, gy - 26, 4.5, th.secondary)  # vent
    s.arrow(120, 244, cx + 20, gy - 30, th.secondary, 1.4)
    s.text(
        38,
        190,
        "static-pressure equalisation",
        15,
        th.secondary,
        bold=True,
        anchor="start",
    )
    s.text(38, 212, "vent: a first-order high-pass,", 15, th.secondary, anchor="start")
    s.text(38, 234, "and the chain's real corner", 15, th.secondary, anchor="start")

    # Primary and secondary windscreens over it.
    s.path(
        f"M {cx - 62} {gy - 12} A 62 62 0 0 1 {cx + 62} {gy - 12}",
        stroke=th.muted,
        sw=2.2,
    )
    s.path(
        f"M {cx - 104} {gy - 12} A 104 104 0 0 1 {cx + 104} {gy - 12}",
        stroke=th.muted,
        sw=2.2,
        dash="8,5",
    )
    s.text(cx, gy + 88, "primary foam screen (solid)", 14, th.muted)
    s.text(cx, gy + 108, "secondary in wind (dashed),", 14, th.muted)
    s.text(cx, gy + 128, "with its loss corrected", 14, th.muted)
    s.text(cx, 92, "Below 20 Hz the wind is louder", 16, th.fg, bold=True)
    s.text(cx, 114, "than the source", 16, th.fg, bold=True)

    # -- Middle: the electrical chain ---------------------------------------
    # 264 px on "ponderación G + integrador", 267 px at the box title size
    # against the 239 of "G weighting + integrator"; the Spanish one drops a
    # step on top of that.
    bx, bw, bh = 320.0, 264.0, 92.0
    stages = (
        ("Preamplifier", "corner << 0,25 Hz", th.primary),
        ("Recorder", "low-cut switch OFF", th.primary),
        ("G weighting + integrator", "$T ≥ 10$ s (A.5)", th.accent),
    )
    y = 132.0
    for title, detail, color in stages:
        s.rect(bx, y, bw, bh, th.panel, color, rx=12, sw=2)
        tsize = 17 if s.text_width(title, 17, bold=True) <= bw - 24 else 15
        s.text(bx + bw / 2, y + 38, title, tsize, th.fg, bold=True)
        # Mono is the code voice of the literal switch settings; the
        # averaging-time detail carries $...$ mathematics and composes in
        # the text face (mono plus markup is refused by the canvas).
        s.text(bx + bw / 2, y + 66, detail, 15, th.muted, mono="$" not in detail)
        if y > 140:
            s.arrow(bx + bw / 2, y - 34, bx + bw / 2, y - 6, th.fg, 2)
        y += bh + 34
    s.arrow(cx + 120, gy - 6, bx - 8, 200, th.fg, 2)
    s.text(bx + bw / 2, y + 4, "report $L_{pG}$ with the chain corner,", 15, th.fg)
    s.text(bx + bw / 2, y + 26, "the screens and the averaging time", 15, th.fg)

    # -- Right: the G curve against the chain's own corner ------------------
    px, py, pw, ph = 604.0, 132.0, 268.0, 236.0
    s.rect(px, py, pw, ph, "none", th.fg, rx=10, sw=1.6)
    f_lo, f_hi, db_lo, db_hi = 0.1, 1000.0, -60.0, 10.0

    def fx(f: float) -> float:
        return px + pw * (math.log10(f) - math.log10(f_lo)) / (
            math.log10(f_hi) - math.log10(f_lo)
        )

    def fy(db: float) -> float:
        return py + ph * (db_hi - db) / (db_hi - db_lo)

    # The 0,25 Hz - 315 Hz span ISO 7196 Annex A asks the microphone to cover.
    s.add(
        f'<rect x="{fx(0.25):.1f}" y="{py + 2:.1f}" '
        f'width="{fx(315.0) - fx(0.25):.1f}" height="{ph - 4:.1f}" '
        f'fill="{th.accent}" opacity="0.14"/>'
    )
    # The G curve itself.
    pts = []
    f = f_lo
    while f <= f_hi:
        pts.append(f"{fx(f):.1f},{fy(max(db_lo, _g_weight_db(f))):.1f}")
        f *= 1.06
    s.add(
        f'<polyline points="{" ".join(pts)}" fill="none" '
        f'stroke="{th.accent}" stroke-width="2.4"/>'
    )
    # A chain whose vent corner sits at 2 Hz: first-order high-pass.
    corner = 2.0
    pts = []
    f = f_lo
    while f <= f_hi:
        db = 20 * math.log10(f / math.sqrt(f * f + corner * corner))
        pts.append(f"{fx(f):.1f},{fy(max(db_lo, db)):.1f}")
        f *= 1.06
    s.add(
        f'<polyline points="{" ".join(pts)}" fill="none" '
        f'stroke="{th.secondary}" stroke-width="2.2" stroke-dasharray="7,5"/>'
    )
    s.line(fx(corner), py + 2, fx(corner), py + ph - 2, th.secondary, 1.2, dash="3,4")
    s.text(px + pw / 2, py - 14, "What the chain lets through", 15, th.fg, bold=True)
    for f_tick, label in (
        (0.1, "0,1"),
        (1.0, "1"),
        (10.0, "10"),
        (100.0, "100"),
        (1000.0, "1k"),
    ):
        s.text(fx(f_tick), py + ph + 22, label, 13, th.muted, mono=True)
    s.text(px + pw / 2, py + ph + 46, "Frequency [Hz]", 14, th.muted)
    s.arrow(fx(0.45), fy(-33.0), fx(0.45), fy(-16.0), th.secondary, 1.5)
    s.text(fx(0.12), fy(-40.0), "lost", 13, th.secondary, bold=True, anchor="start")
    s.text(px + pw / 2, py + ph + 70, "green: the G weighting", 13, th.accent)
    s.text(
        px + pw / 2,
        py + ph + 90,
        "dashed: a chain with a 2 Hz vent corner",
        13,
        th.secondary,
    )
    s.text(
        px + pw / 2, py + ph + 116, "usable band = the overlap", 15, th.fg, bold=True
    )
    # The span of the shaded band, named with the captions: inside the plot
    # the G curve and the corner line ran through it wherever it went.
    s.text(px + pw / 2, py + ph + 138, "A.2: 0,25 - 315 Hz", 13, th.accent, bold=True)
    s.text(px + pw / 2, py + ph + 160, "ISO 7196:1995, Annex A", 14, th.muted)


# ---------------------------------------------------------------------------
# d28 - Capturing an array: one clock, locked gains, a written row map
# ---------------------------------------------------------------------------


def _d_multichannel_capture(s: SVG, th: Theme) -> None:
    """Four microphones, one converter, and the map from row to position.

    Room-survey spacing with the capsules at 1,2 m, the calibrator drawn
    coupled onto one capsule and moved along the row, and the single-clock
    requirement stated where it is decided: at the interface.
    """
    gy = 372.0
    s.ground(gy, 30, 312)
    s.text(172, 92, "Each position, its sensitivity", 16, th.fg, bold=True)

    xs = (66.0, 132.0, 198.0, 264.0)
    sens = ("11,8", "12,3", "11,9", "12,1")
    cap_y = gy - 120.0  # capsule height, 1,2 m to scale
    for i, (x, mv) in enumerate(zip(xs, sens, strict=True)):
        s.mic(x, cap_y, gy, 0.95)
        s.text(x, gy + 24, f"P{i + 1}", 15, th.fg, bold=True)
        s.text(x, gy + 44, mv, 12, th.muted, mono=True)
    s.text(172, gy + 66, "mV/Pa, one per capsule", 12, th.muted)
    # The label over the top of the dimension: beside it, the first stand
    # ran through it.
    s.dim(40, cap_y, 40, gy, "", size=13, label_side="right")
    s.text(40, cap_y - 10, "1,2 m", 13, th.fg)

    # Calibrator coupled onto P2 and moved along the row.
    s.rect(xs[1] - 22, cap_y - 56, 44, 56, th.panel, th.secondary, rx=6, sw=2)
    s.text(xs[1], cap_y - 30, "94,0", 13, th.secondary, bold=True, mono=True)
    s.text(xs[1], cap_y - 12, "dB", 11, th.muted, mono=True)
    s.path(
        f"M {xs[0]:.0f} {cap_y - 78:.0f} Q {xs[1] + 34:.0f} "
        f"{cap_y - 116:.0f} {xs[3]:.0f} {cap_y - 78:.0f}",
        stroke=th.secondary,
        sw=1.6,
        dash="7,5",
    )
    s.text(172, cap_y - 128, "one capsule at a time,", 13, th.secondary)
    s.text(172, cap_y - 110, "gains locked throughout", 13, th.secondary)

    # -- Middle: one preamplifier, one interface, one clock -----------------
    bx, bw = 352.0, 214.0
    s.rect(bx, 150, bw, 82, th.panel, th.primary, rx=10, sw=2)
    # A size smaller where the box would not hold it, as the Spanish at 16.
    preamp = "4-channel preamplifier"
    s.text(
        bx + bw / 2,
        196,
        preamp,
        s.fit_size([preamp], [16, 15, 14, 13], bw - 16, bold=True),
        th.fg,
        bold=True,
    )
    for i, x in enumerate(xs):
        s.arrow(x + 10, gy - 46, bx - 6, 168 + i * 16, th.muted, 1.2)

    s.rect(bx, 268, bw, 96, th.panel, th.primary, rx=10, sw=2)
    s.text(bx + bw / 2, 298, "audio interface", 16, th.fg, bold=True)
    # 40 px tall, which keeps the subscript off the box's lower edge.
    s.rect(bx + 14, 312, bw - 28, 40, th.panel, th.accent, rx=6, sw=2)
    s.text(bx + bw / 2, 328, "single sample clock", 14, th.accent, bold=True)
    s.text(bx + bw / 2, 343, "$f_s$ = 48 kHz", 13, th.accent)
    s.arrow(bx + bw / 2, 236, bx + bw / 2, 262, th.fg, 2)

    # The cross strikes out the arrangement and stops at its words, which it
    # ran through: each line sits on a backing of the box's own colour. The
    # box is as wide as the ones above, and its lines a size smaller where
    # they would not fit: the Spanish ran out through both sides.
    s.rect(bx + 4, 400, bw - 8, 60, th.panel, th.muted, rx=10, sw=2, dash="6,5")
    s.line(bx + 4, 400, bx + bw - 4, 460, th.secondary, 2.4)
    s.line(bx + 4, 460, bx + bw - 4, 400, th.secondary, 2.4)
    second = ("a second interface", "= two clocks, not one array")
    size = s.fit_size(list(second), [13, 12], bw - 20)
    for baseline, line in zip((428, 448), second, strict=True):
        width = s.text_width(line, size)
        s.rect(bx + bw / 2 - width / 2 - 3, baseline - 12, width + 6, 16, th.panel)
        s.text(bx + bw / 2, baseline, line, size, th.muted)

    # -- Right: the array, row by row --------------------------------------
    ax0, row_h = 620.0, 44.0
    s.text(748, 122, "$x$, the array you analyse", 16, th.fg, bold=True)
    for i in range(4):
        y = 150 + i * row_h
        s.rect(ax0, y, 232, row_h - 8, th.panel, th.primary, rx=6, sw=1.8)
        s.text(ax0 + 116, y + 24, f"ch{i} = P{i + 1}", 15, th.fg, mono=True)
    s.text(
        748, 150 + 4 * row_h + 12, "shape (4, N)", 15, th.accent, bold=True, mono=True
    )
    s.arrow(bx + bw + 6, 300, ax0 - 8, 240, th.fg, 2)

    s.rect(600, 372, 272, 96, "none", th.fg, rx=10, sw=1.8)
    s.text(736, 398, "Write down, with the file:", 14, th.fg, bold=True)
    s.text(736, 420, "one clock  |  locked gains", 13, th.fg)
    s.text(736, 442, "the row-to-position map", 13, th.fg)
    s.text(
        450,
        520,
        "A swapped pair gives perfectly valid levels attributed "
        "to the wrong positions,",
        15,
        th.fg,
    )
    s.text(450, 542, "and no later check can detect it", 15, th.muted)


# ---------------------------------------------------------------------------
# d29 - How a band is graded against Table 1 (IEC 61260-1:2014, 5.10)
# ---------------------------------------------------------------------------

#: IEC 61260-1:2014 Table 1, high side, as the exponent x of the octave
#: breakpoint G^x with the class 1 and class 2 limits the plate draws. In the
#: pass band the column is the maximum (the minimum is -0.4 dB for class 1 and
#: -0.6 dB for class 2 throughout); in the stop band it is the minimum (the
#: maximum is unbounded). The first stop-band row is the G^(1/2) + epsilon row.
_TABLE1_PASS_MAX: tuple[tuple[float, float, float], ...] = (
    (0.0, 0.4, 0.6),
    (1 / 8, 0.5, 0.7),
    (1 / 4, 0.7, 0.9),
    (3 / 8, 1.4, 1.7),
    (1 / 2, 5.3, 5.8),
)
_TABLE1_STOP_MIN: tuple[tuple[float, float, float], ...] = (
    (1 / 2, 1.2, 0.8),
    (1.0, 16.6, 15.6),
    (2.0, 40.5, 39.5),
    (3.0, 60.0, 54.0),
    (4.0, 70.0, 60.0),
)
_TABLE1_PASS_MIN = {1: -0.4, 2: -0.6}


def _third_octave_breakpoint(exponent: float) -> float:
    """IEC 61260-1:2014 Formula (9) for b = 3: octave breakpoint G^x on 1/3."""
    g = math.pow(10, 3 / 10)
    return 1 + (math.pow(g, 1 / 6) - 1) / (math.pow(g, 0.5) - 1) * (
        math.pow(g, exponent) - 1
    )


def _butterworth_third_octave_db(omega: float) -> float:
    """Relative attenuation of an order-6 Butterworth one-third-octave band.

    The analogue band-pass magnitude, 10 lg(1 + x^12) with x the band-pass
    frequency variable scaled to the band edges: 3.01 dB at both edges and the
    shape the library's digital design follows to within 0.1 dB up to G and
    2.2 dB at G^4, at 48 kHz without decimation.
    """
    g = 10 ** (3 / 10)
    x = (omega - 1 / omega) / (g ** (1 / 6) - g ** (-1 / 6))
    return 10 * math.log10(1 + x**12)


def _d_filter_class_check(s: SVG, th: Theme) -> None:
    """One band walked through the class check, and what the check leaves out.

    The chain across the top is clause 5.10 of IEC 61260-1:2014 in the order
    the library runs it: the designed band, its relative attenuation by
    Formula (8), the Table 1 mask carried to one-third octave by Formula (9)
    and mirrored by Formula (10), and the margin per class that decides the
    verdict. The two panels draw that mask on an axis stretched breakpoint by
    breakpoint, so every limit is a straight line between breakpoints, which
    is what Formula (11) says. The band is an order-6 Butterworth one-third
    octave at 1 kHz, which the default bank at 48 kHz walks to the end of the
    mask: its Nyquist frequency is 24 f_m, and a decimated band keeps its own
    at least sixteen times its upper edge. The solid box at the top right
    is what the verifier also computes on the design, the IEC 61260-2 tests
    that need no specimen (the Formula (1) grid, 5.12, 5.16 and the swept
    test of 5.14); the dashed column below it is IEC 61260-2 and IEC 61260-3
    as a laboratory runs them on a device, whose periodic results
    ``verify_filter_periodic`` grades.
    """
    pass_om = [_third_octave_breakpoint(row[0]) for row in _TABLE1_PASS_MAX]
    stop_om = [_third_octave_breakpoint(row[0]) for row in _TABLE1_STOP_MIN]
    pass_x = (62.0, 116.0, 170.0, 224.0, 278.0)
    stop_x = (354.0, 410.0, 466.0, 522.0, 578.0)
    stop_end = 614.0
    top, bottom = 210.0, 400.0

    def x_of(omega: float, oms: list[float], xs: tuple[float, ...]) -> float:
        # Linear in lg(omega) between adjacent breakpoints: Formula (11).
        for k in range(len(oms) - 1):
            if oms[k] <= omega <= oms[k + 1]:
                t = math.log10(omega / oms[k]) / math.log10(oms[k + 1] / oms[k])
                return xs[k] + t * (xs[k + 1] - xs[k])
        return xs[-1]

    def y_pass(db: float) -> float:
        return bottom - (db + 1.0) * (bottom - top) / 7.0  # -1 dB to +6 dB

    def y_stop(db: float) -> float:
        return bottom - db * (bottom - top) / 180.0  # 0 dB to 180 dB

    s.text(
        450,
        62,
        "The check runs on the design: every band, every breakpoint, "
        "one margin per class",
        15,
        th.fg,
        bold=True,
    )

    # -- The chain ---------------------------------------------------------
    boxes = (
        (
            "1 · the designed band",
            "$f_m$ = 1000 Hz, 1/3 octave",
            "order 6, sections at $f_s/M$",
            th.primary,
        ),
        (
            "2 · relative attenuation",
            "$ΔA(Ω) = A(Ω) − A_{ref}$",
            "$Ω = f/f_m$, $A_{ref}$ at $Ω$ = 1",
            th.primary,
        ),
        (
            "3 · the Table 1 mask",
            "octave breakpoints to $1/b$",
            "straight lines in lg Ω between",
            th.primary,
        ),
        (
            "4 · margin and class",
            "the worst distance to a limit",
            "strictest class with $m ≥ 0$",
            th.accent,
        ),
    )
    bw, gap, by, bh = 197.0, 24.0, 80.0, 78.0
    for i, (title, line1, line2, colour) in enumerate(boxes):
        x0 = 20.0 + i * (bw + gap)
        s.rect(x0, by, bw, bh, th.panel, colour, rx=8, sw=1.8)
        s.text(x0 + bw / 2, by + 24, title, 13, colour, bold=True)
        s.text(x0 + bw / 2, by + 46, line1, 12, th.fg)
        s.text(x0 + bw / 2, by + 66, line2, 12, th.muted)
        if i:
            s.arrow(x0 - gap + 2, by + bh / 2, x0 - 3, by + bh / 2, th.fg, 1.8)

    # -- The mask, pass band and stop band ---------------------------------
    s.text(170, 196, "pass band, both limits", 12, th.fg, bold=True)
    s.text(484, 196, "stop band, a minimum only", 12, th.fg, bold=True)
    s.rect(62, top, 216, bottom - top, "none", th.muted, sw=1.0)
    s.rect(354, top, stop_end - 354, bottom - top, "none", th.muted, sw=1.0)
    for db in (0, 2, 4, 6):
        s.line(57, y_pass(db), 62, y_pass(db), th.muted, 1.0)
        s.text(53, y_pass(db) + 4, str(db), 11, th.muted, anchor="end")
    for db in (0, 40, 80, 120, 160):
        s.line(349, y_stop(db), 354, y_stop(db), th.muted, 1.0)
        s.text(345, y_stop(db) + 4, str(db), 11, th.muted, anchor="end")
    s.text(30, 305, "dB", 11, th.muted)

    # Class 2 first, dashed, so class 1 is drawn over it.
    for col, colour, dash, sw in ((2, th.muted, "6,4", 1.6), (1, th.primary, "", 2.2)):
        pts = " L ".join(
            f"{x:.1f} {y_pass(row[col]):.1f}"
            for x, row in zip(pass_x, _TABLE1_PASS_MAX, strict=True)
        )
        s.path(f"M {pts}", stroke=colour, sw=sw, dash=dash)
        y_min = y_pass(_TABLE1_PASS_MIN[col])
        s.line(pass_x[0], y_min, pass_x[-1], y_min, colour, sw, dash=dash)
        pts = " L ".join(
            f"{x:.1f} {y_stop(row[col]):.1f}"
            for x, row in zip(stop_x, _TABLE1_STOP_MIN, strict=True)
        )
        y_last = y_stop(_TABLE1_STOP_MIN[-1][col])
        s.path(f"M {pts} L {stop_end} {y_last:.1f}", stroke=colour, sw=sw, dash=dash)

    # The band on the same stretched axis, and its value at every breakpoint.
    for oms, xs, y_of in ((pass_om, pass_x, y_pass), (stop_om, stop_x, y_stop)):
        band_pts: list[str] = []
        for k in range(len(oms) - 1):
            for j in range(33):
                om = oms[k] * (oms[k + 1] / oms[k]) ** (j / 32)
                band_db = _butterworth_third_octave_db(om)
                band_pts.append(f"{x_of(om, oms, xs):.1f} {y_of(band_db):.1f}")
        s.path("M " + " L ".join(band_pts), stroke=th.fg, sw=2.0)
        for om, x in zip(oms, xs, strict=True):
            s.circle(x, y_of(_butterworth_third_octave_db(om)), 4.2, th.fg)

    # The binding margin, drawn where it binds: 0.4 dB under the class 1 maximum.
    s.line(68, y_pass(0.0), 68, y_pass(0.4), th.secondary, 3.0)

    # Legend, in the empty top-left corner of the pass-band panel.
    s.line(67, 222, 83, 222, th.primary, 2.2)
    s.text(88, 226, "class 1", 11, th.fg, anchor="start")
    s.line(67, 238, 83, 238, th.muted, 1.6, dash="5,3")
    s.text(88, 242, "class 2", 11, th.fg, anchor="start")
    s.line(67, 254, 83, 254, th.fg, 2.0)
    s.text(88, 258, "$ΔA$ of the band", 11, th.fg, anchor="start")
    s.circle(75, 270, 4.2, th.fg)
    s.text(88, 274, "$ΔA$ at a breakpoint", 11, th.fg, anchor="start")

    # Column labels: the octave breakpoint, then its one-third-octave value.
    for xs, names, values in (
        (
            pass_x,
            ("1", "$G^{1/8}$", "$G^{1/4}$", "$G^{3/8}$", "$G^{1/2} − ε$"),
            ("1.000", "1.027", "1.056", "1.087", "1.122"),
        ),
        (
            stop_x,
            ("$G^{1/2} + ε$", "$G$", "$G^2$", "$G^3$", "$≥ G^4$"),
            ("1.122", "1.294", "1.882", "3.054", "5.392"),
        ),
    ):
        for x, name, value in zip(xs, names, values, strict=True):
            s.text(x, 420, name, 13, th.fg)
            s.text(x, 438, value, 11, th.muted)
    s.text(
        338,
        458,
        "top: octave breakpoints of Table 1; below: the same for one-third "
        "octave, Formula (9)",
        11,
        th.muted,
    )

    # The class 1 margin at every breakpoint, and the one that decides.
    s.text(338, 482, "class 1 margin at each breakpoint, in dB", 12, th.fg, bold=True)
    margins = (
        "+0.40", "+0.40", "+0.40", "+0.49", "+2.29",
        "+1.81", "+26", "+52", "+69", "+92",
    )  # fmt: skip
    for i, (x, label) in enumerate(zip(pass_x + stop_x, margins, strict=True)):
        s.text(x, 504, label, 12, th.secondary if i < 3 else th.fg, bold=True)
    s.rect(40, 489, 152, 22, "none", th.secondary, rx=4, sw=1.4)
    s.text(338, 526, "the smallest, +0.40 dB, is the band's margin", 11, th.secondary)

    s.text(
        338, 552, "edition '1995' adds class 0 on the same breakpoints:", 12, th.muted
    )
    s.text(
        338,
        570,
        "±0.15 dB at mid-band and 75 dB from $G^4$, with class 1 at ±0.3 dB",
        12,
        th.muted,
    )

    # -- The verdict -------------------------------------------------------
    s.rect(20, 588, 600, 104, th.panel, th.accent, rx=6, sw=1.8)
    s.text(
        320,
        614,
        "this band: $m_1$ = +0.40 dB, $m_2$ = +0.60 dB, so class 1",
        14,
        th.accent,
        bold=True,
    )
    s.text(
        320,
        638,
        "$m$ is the least distance to a limit over $2^{15}$ grid points and "
        "every breakpoint",
        12,
        th.fg,
    )
    s.text(
        320,
        658,
        "a bank takes the class of its worst band, and none if any band has none",
        12,
        th.fg,
    )
    s.text(
        320,
        678,
        "past a band's own Nyquist nothing is walked, and range_limited says so",
        12,
        th.muted,
    )

    # -- Computed on the design too: the IEC 61260-2 tests with no specimen -
    s.line(339.5, by + bh, 339.5, 176, th.primary, 1.4)
    s.line(339.5, 176, 758, 176, th.primary, 1.4)
    s.arrow(758, 176, 758, 190, th.primary, 1.4)
    s.rect(636, 192, 244, 180, th.panel, th.primary, rx=8, sw=1.6)
    s.text(758, 214, "Also computed on the design", 13, th.primary, bold=True)
    s.text(758, 231, "the IEC 61260-2 tests with no specimen", 11, th.muted)
    for y, line in (
        (252, "$S ≥ 24$ sines per bandwidth,"),
        (268, "at $Ω_i = G^{i/(bS)}$ (Formula 1)"),
        (288, "5.12: $ΔB$ by Formula (2),"),
        (304, "±0.4 dB class 1, ±0.6 dB class 2"),
        (324, "5.16: $ΔP_j$ by Formula (3),"),
        (340, "+0.8 dB to −1.8 dB class 1"),
        (360, "5.14: one sweep through the bank"),
    ):
        s.text(758, y, line, 11, th.fg)

    # -- Outside the check: what a laboratory does to an instrument ---------
    s.rect(636, 384, 244, 322, "none", th.muted, rx=8, sw=1.4, dash="7,5")
    s.text(758, 405, "Outside the check", 14, th.muted, bold=True)
    s.text(758, 424, "on a device, $A = L_{in} − L_{out}$ is measured", 11, th.fg)

    s.rect(644, 436, 228, 104, th.panel, th.muted, rx=6, sw=1.2)
    s.text(758, 456, "IEC 61260-2, on a specimen", 12, th.fg, bold=True)
    s.text(758, 472, "once per model", 11, th.muted)
    for y, line in (
        (490, "≥ 3 specimens in, ≥ 1 tested in full"),
        (506, "1 dB under the top of the linear range"),
        (522, "20 °C to 26 °C, 35 % to 65 % RH"),
    ):
        s.text(758, y, line, 11, th.fg)

    s.rect(644, 550, 228, 132, th.panel, th.muted, rx=6, sw=1.2)
    s.text(758, 570, "IEC 61260-3, periodic test", 12, th.fg, bold=True)
    s.text(758, 586, "each instrument, on a date", 11, th.muted)
    for y, line, colour in (
        (604, "every filter at mid-band, or one sweep", th.fg),
        (620, "three filters, low, middle and high,", th.fg),
        (636, "up to 15 sines each, $k$ = −7 … 7", th.fg),
        (656, "the results graded by", th.primary),
        (672, "verify_filter_periodic", th.primary),
    ):
        s.text(758, y, line, 11, colour)
    s.text(758, 698, "$U$ within Annex B: 0.20 to 0.50 dB", 11, th.muted)

    # -- The two formulas that carry Table 1 to any bandwidth --------------
    s.rect(20, 718, 860, 64, th.panel, th.fg, rx=6, sw=1.6)
    s.text(
        450,
        744,
        "$Ω_{h(1/b)} = 1 + (G^{1/(2b)} − 1) / (G^{1/2} − 1) · (Ω_{h(1/1)} − 1)$"
        "   (Formula 9)",
        15,
        th.fg,
    )
    s.text(
        450,
        770,
        "$ΔA_x = ΔA_a + (ΔA_b − ΔA_a) · lg(Ω_x/Ω_a) / lg(Ω_b/Ω_a)$   (Formula 11)",
        15,
        th.fg,
    )


# ---------------------------------------------------------------------------
# d30 - Verification regimes: the three parts of IEC 61672 and IEC 61260
# ---------------------------------------------------------------------------


def _d_verification_regimes(s: SVG, th: Theme) -> None:
    """The three parts of IEC 61672 and IEC 61260, and the line the library stops at.

    Both series split the same way. Part 1 fixes the design goals and the
    acceptance limits, Table 3 of IEC 61672-1 and Table 1 of IEC 61260-1, and
    it is the only part the design verifiers are held to; for the filters
    that is Table 1 with the effective bandwidth, the swept test and the
    summation of outputs (5.12, 5.14, 5.16), which ``verify_filter_class``
    and ``verify_time_invariance`` compute on the design the way Part 2
    tests them. Part 2 is pattern evaluation,
    and 4.1 of both parts sets minimums rather than counts: at least three
    specimens submitted, at least two selected and at least one of those
    tested in full against every mandatory specification, ending in a report
    that states whether the pattern is approved (10.3 of both). Part 3 is the
    periodic test of one working instrument on a deliberately limited set of
    key tests, and its verdict says nothing general about Part 1 unless that
    approval is public (clause 1 of IEC 61672-3, 1.5 of IEC 61260-3), which is
    the arrow down the left margin. The filter cell of Part 3 carries the
    condition 10.1.2 puts on the sweep, which stands in for the midband test
    of 10.2 only where the filters are time invariant; for any other filter
    set 10.2 is the only route. One condition the cell is too narrow to
    carry: the k range of 13.4 runs from -7 to 7 only while the test
    frequency stays above 0,5 times the lowest exact midband frequency of the
    set and below 1,5 times the highest, so fifteen is a ceiling. The box at
    the foot is the conformance criterion both series apply (5.1.21 of
    IEC 61672-1, 5.1.9 of IEC 61260-1), of which a computed response can show
    only the first half. The arrow down the right margin is
    ``verify_filter_periodic``, which grades a laboratory's Part 3 results
    for a band filter on both halves without running a test.
    """
    left, right, mid = 36.0, 864.0, 450.0
    xl, xr = 52.0, 466.0  # text start of the meter cell and of the filter cell

    def meter(x: float, y: float, colour: str, fill: str, dash: str = "") -> None:
        # A hand-held sound level meter: microphone on its stem, body, display.
        s.line(x, y + 2, x, y - 6, colour, 1.6)
        s.circle(x, y - 10, 4, th.panel, colour, 1.6)
        s.rect(x - 9, y + 2, 18, 32, fill, colour, rx=3, sw=1.6, dash=dash)
        s.rect(x - 6, y + 7, 12, 7, th.bg, colour, rx=1, sw=1.1)

    def filterset(x: float, y: float, colour: str, fill: str, dash: str = "") -> None:
        # A band analyser: a case with a band-level display in it.
        s.rect(x - 17, y - 2, 34, 36, fill, colour, rx=3, sw=1.6, dash=dash)
        s.rect(x - 14, y + 2, 28, 28, th.bg, "none", rx=2)
        for k, hgt in enumerate((7, 13, 18, 12, 6)):
            s.rect(x - 12 + 5 * k, y + 29 - hgt, 4, hgt, colour)

    def row(y0: float, h: float, colour: str, title: str) -> None:
        s.rect(left, y0, right - left, h, "none", colour, rx=8, sw=1.8)
        s.text(xl, y0 + 22, title, 14, colour, "start", bold=True)
        s.line(mid, y0 + 36, mid, y0 + h - 34, th.muted, 1.0)

    def lines(x: float, y0: float, texts: tuple[str, ...]) -> None:
        for k, label in enumerate(texts):
            s.text(x, y0 + 20 * k, label, 12, th.fg, "start")

    # -- The library, and the two verifiers that reach down into Part 1 ------
    s.rect(150, 50, 600, 60, th.panel, th.primary, rx=8, sw=2.0)
    s.text(
        mid,
        74,
        "phonometry: the transfer function you configured",
        15,
        th.primary,
        bold=True,
    )
    s.text(
        mid,
        97,
        "a computed design: no specimen, no air temperature, "
        "no uncertainty of measurement",
        12,
        th.muted,
    )
    for x, names, anchor, dx in (
        (239.0, ("verify_weighting_class",), "end", -8),
        (661.0, ("verify_filter_class", "verify_time_invariance"), "start", 8),
    ):
        s.arrow(x, 110, x, 168, th.primary, 1.8)
        for k, name in enumerate(names):
            s.text(x + dx, 134 + 18 * k, name, 12, th.primary, anchor, mono=True)

    # -- Part 1: the tables both verifiers read, and what a laboratory is held to
    y1 = 170.0
    row(
        y1,
        180,
        th.primary,
        "Part 1 · Specifications: design goals and acceptance limits",
    )
    s.text(
        xl, y1 + 48, "IEC 61672-1 · sound level meters", 13, th.fg, "start", bold=True
    )
    lines(
        xl,
        y1 + 70,
        (
            "Table 3: A, C and Z at 34 nominal frequencies,",
            "10 Hz to 20 kHz; ±0.7 dB at 1 kHz for class 1",
        ),
    )
    s.text(
        xl,
        y1 + 130,
        "the laboratory's $U$: at most 0.60 dB up to 4 kHz",
        12,
        th.muted,
        "start",
    )
    s.text(xr, y1 + 48, "IEC 61260-1 · band filters", 13, th.fg, "start", bold=True)
    lines(
        xr,
        y1 + 70,
        (
            "Table 1: a relative attenuation corridor",
            "round each mid-band; ±0.4 dB at $Ω = 1$ for class 1;",
            "5.12, 5.14, 5.16: bandwidth, sweep, summation",
        ),
    )
    s.text(
        xr,
        y1 + 130,
        "the laboratory's $U$: at most 0.20 dB while $ΔA ≤ 2$ dB",
        12,
        th.muted,
        "start",
    )
    s.text(
        mid,
        y1 + 166,
        "class 2 shares the design goals, with limits as wide or wider, "
        "and 0 °C to +40 °C against −10 °C to +50 °C for class 1",
        12,
        th.muted,
    )

    # -- The line the verifiers stop at --------------------------------------
    yb = 370.0
    s.line(16, yb, 884, yb, th.fg, 1.6, dash="8,5")
    chip = (
        "above: a design checked in software · below: a physical instrument "
        "in a laboratory"
    )
    wchip = s.text_width(chip, 12, bold=True) + 24
    s.rect(mid - wchip / 2, yb - 12, wchip, 24, th.bg, th.fg, rx=12, sw=1.2)
    s.text(mid, yb + 4, chip, 12, th.fg, bold=True)

    # -- Part 2: a model, once, on specimens, and every count a minimum ------
    y2 = 394.0
    row(
        y2,
        222,
        th.accent,
        "Part 2 · Pattern evaluation: a model, once, "
        "against every mandatory specification",
    )
    for x0, head, icon, pitch in (
        (xl, "IEC 61672-2", meter, 26.0),
        (xr, "IEC 61260-2", filterset, 42.0),
    ):
        s.text(x0, y2 + 48, head, 13, th.fg, "start", bold=True)
        cx = x0 + 18
        icon(cx, y2 + 70, th.accent, th.accent)  # the one tested in full
        icon(cx + pitch, y2 + 70, th.accent, th.panel)  # the second one selected
        icon(cx + 2 * pitch, y2 + 70, th.muted, th.panel, "3,2")  # submitted only
        tx = cx + 2 * pitch + 30
        s.text(
            tx, y2 + 80, "at least three submitted, at least two", 12, th.fg, "start"
        )
        s.text(
            tx, y2 + 100, "selected, at least one tested in full", 12, th.fg, "start"
        )
    lines(
        xl,
        y2 + 128,
        (
            "static pressure, temperature, humidity, ESD, RF fields",
            "weightings in a free field, 1/3 octave apart to 2 kHz,",
            "1/6 to 8 kHz and, for class 1, 1/12 to 20 kHz",
            "level linearity, tonebursts, overload, self-noise",
        ),
    )
    lines(
        xr,
        y2 + 128,
        (
            "every filter at 24 or more frequencies per bandwidth:",
            "relative attenuation, effective bandwidth, summation",
            "linearity on the lowest, a middle and the highest filter",
            "ESD, RF and four pairs of temperature and humidity",
        ),
    )
    s.text(
        mid,
        y2 + 212,
        "the report states whether the pattern is approved, "
        "and notice of an approval should be made public",
        12,
        th.accent,
        bold=True,
    )

    # -- Part 3: one working instrument, a deliberately limited set ----------
    y3 = 636.0
    row(
        y3,
        234,
        th.secondary,
        "Part 3 · Periodic tests: one working instrument, a limited set of key tests",
    )
    for x0, head, icon, env in (
        (
            xl,
            "IEC 61672-3",
            meter,
            "20 °C to 26 °C, 25 % to 70 % RH, 80 kPa to 105 kPa",
        ),
        (xr, "IEC 61260-3", filterset, "20 °C to 26 °C, 25 % to 70 % RH"),
    ):
        s.text(x0, y3 + 48, head, 13, th.fg, "start", bold=True)
        cx = x0 + 18
        icon(cx, y3 + 70, th.secondary, th.secondary)
        s.text(
            cx + 30,
            y3 + 80,
            "one instrument, its serial number visible",
            12,
            th.fg,
            "start",
        )
        s.text(cx + 30, y3 + 100, env, 12, th.fg, "start")
    lines(
        xl,
        y3 + 120,
        (
            "calibrator check, self-generated noise and weighting",
            "by sound at 125 Hz, 1 kHz, 8 kHz; electrically at",
            "octaves from 63 Hz to 16 kHz for class 1; linearity,",
            "tonebursts, C-weighted peak, overload",
        ),
    )
    lines(
        xr,
        y3 + 120,
        (
            "every filter at mid-band, ±0.4 dB for class 1, or one sweep",
            "across the set if the filters are time invariant",
            "three filters (31.5 Hz, 1 kHz, 16 kHz recommended): level",
            "linearity, and Table 1 at up to 15 frequencies, $k = −7$ to 7",
            "every filter's self-noise under the linear range",
        ),
    )
    s.text(
        mid,
        y3 + 224,
        "without that public approval, passing every test supports "
        "no general conclusion on Part 1",
        12,
        th.secondary,
        bold=True,
    )

    # The approval that Part 2 publishes is what the verdict of Part 3 leans on.
    s.path(
        f"M {left} {y2 + 208} H 22 V {y3 + 220} H {left - 10}",
        stroke=th.accent,
        sw=1.6,
    )
    s.arrow(left - 10, y3 + 220, left - 1, y3 + 220, th.accent, 1.6)

    # The periodic grader: a laboratory's Part 3 results, read on both halves.
    s.path(f"M 750 80 H 882 V {y3 + 44}", stroke=th.primary, sw=1.6)
    s.arrow(882, y3 + 44, right + 1, y3 + 44, th.primary, 1.6)
    s.text(
        right - 12,
        y3 + 48,
        "verify_filter_periodic",
        12,
        th.primary,
        "end",
        mono=True,
    )

    # -- The criterion both series apply, and the half software can see ------
    yf = 890.0
    s.rect(70, yf, 760, 102, th.panel, th.fg, rx=6, sw=1.6)
    s.text(
        mid,
        yf + 30,
        "$δ$ within the acceptance limits    and    $U ≤ U_{max}$",
        17,
        th.fg,
    )
    s.text(
        mid,
        yf + 54,
        "$δ$ the deviation from the design goal, "
        "$U$ the expanded uncertainty for 95 % coverage",
        12,
        th.fg,
    )
    s.text(
        mid,
        yf + 74,
        "a design verifier reads the first half off a computed response; "
        "a laboratory has to meet both,",
        12,
        th.muted,
    )
    s.text(
        mid,
        yf + 92,
        "and verify_filter_periodic grades both on a band filter's periodic results",
        12,
        th.muted,
    )
    s.text(
        mid,
        yf + 130,
        "IEC 61043 keeps all three in one document: requirements in clauses "
        "6 to 10, type tests in 11 to 13, periodic verification in Annex A",
        12,
        th.muted,
    )


# ---------------------------------------------------------------------------
# IEC 61183: the two calibrations of a sound level meter in a field from
# every direction (clauses 4 and 5, Annexes A and B)
# ---------------------------------------------------------------------------


def _wedge_walls(s: SVG, th: Theme, x0: float, y0: float, w: float, h: float) -> None:
    """A room in plan with absorbing wedges along its four walls."""
    s.rect(x0, y0, w, h, th.bg, th.fg, sw=2.2)
    tooth, depth = 24.0, 14.0
    x = x0
    while x + tooth <= x0 + w + 0.5:
        s.path(
            f"M {x} {y0} L {x + tooth} {y0} L {x + tooth / 2} {y0 + depth} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=0.9,
        )
        s.path(
            f"M {x} {y0 + h} L {x + tooth} {y0 + h} L {x + tooth / 2} {y0 + h - depth} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=0.9,
        )
        x += tooth
    y = y0 + depth
    while y + tooth <= y0 + h - depth + 0.5:
        s.path(
            f"M {x0} {y} L {x0} {y + tooth} L {x0 + depth} {y + tooth / 2} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=0.9,
        )
        s.path(
            f"M {x0 + w} {y} L {x0 + w} {y + tooth} L {x0 + w - depth} {y + tooth / 2} Z",
            fill=th.panel,
            stroke=th.muted,
            sw=0.9,
        )
        y += tooth


def _speaker(s: SVG, th: Theme, x: float, y: float, facing: float) -> None:
    """A loudspeaker in plan, its cone opening towards ``facing`` (+1 or -1)."""
    s.rect(x - 9, y - 13, 18, 26, th.panel, th.fg, rx=3, sw=1.6)
    tip = x + facing * 9
    mouth = x + facing * 23
    s.path(
        f"M {tip} {y - 6} L {mouth} {y - 15} L {mouth} {y + 15} L {tip} {y + 6} Z",
        fill=th.panel,
        stroke=th.fg,
        sw=1.6,
    )


def _meter_plan(
    s: SVG, th: Theme, cx: float, cy: float, heading_deg: float, length: float
) -> None:
    """A sound level meter in plan: microphone at (cx, cy), case behind it.

    ``heading_deg`` is the reference direction, measured from +x towards -y
    (counter-clockwise on the page); the case runs the opposite way.
    """
    a = math.radians(heading_deg)
    ux, uy = math.cos(a), -math.sin(a)
    px, py = -uy, ux
    back_x, back_y = cx - length * ux, cy - length * uy
    half = 11.0
    neck = 4.0
    s.path(
        f"M {cx - 6 * ux + neck * px:.1f} {cy - 6 * uy + neck * py:.1f} "
        f"L {cx - 26 * ux + half * px:.1f} {cy - 26 * uy + half * py:.1f} "
        f"L {back_x + half * px:.1f} {back_y + half * py:.1f} "
        f"L {back_x - half * px:.1f} {back_y - half * py:.1f} "
        f"L {cx - 26 * ux - half * px:.1f} {cy - 26 * uy - half * py:.1f} "
        f"L {cx - 6 * ux - neck * px:.1f} {cy - 6 * uy - neck * py:.1f} Z",
        fill=th.primary,
        stroke=th.fg,
        sw=1.4,
    )
    s.circle(cx, cy, 5.5, th.fg)


def _d_random_incidence_setup(s: SVG, th: Theme) -> None:
    """IEC 61183: the free-field method (Annex A) beside the diffuse-field
    method (Annex B), each with the readings it takes in order.
    """
    # ===== Free field: anechoic room, the meter on a turntable (A.2, A.4) ===
    s.text(222, 64, "Free field: anechoic room (4.10, Annex A)", 15, th.fg, bold=True)
    _wedge_walls(s, th, 22, 78, 400, 300)
    cx, cy = 262.0, 224.0
    sx = 58.0
    _speaker(s, th, sx, cy, 1.0)
    s.text(40, cy + 44, "source, fixed", 13, th.fg, anchor="start")

    # The X axis: from the microphone towards the source.
    s.line(sx + 28, cy, cx - 6, cy, th.muted, 1.4, dash="7,5")
    s.text(96, cy - 10, "X axis", 12, th.muted, anchor="start")

    # Turntable with the acoustical centre of the microphone on its axis.
    s.circle(cx, cy, 56, th.panel, th.muted, 1.4)
    phi = 34.0
    _meter_plan(s, th, cx, cy, 180.0 - phi, 88.0)
    # Above and to the right of the turntable, clear of its rim, with a leader
    # to the microphone at its centre.
    s.line(cx + 5, cy - 5, cx + 24, cy - 48, th.muted, 1.0, dash="3,3")
    s.text(cx + 30, cy - 66, "microphone on the", 11, th.fg, anchor="start")
    s.text(cx + 30, cy - 52, "axis of rotation", 11, th.fg, anchor="start")
    # The reference direction, phi from the X axis.
    a = math.radians(180.0 - phi)
    reach = 122.0
    s.line(
        cx,
        cy,
        cx + reach * math.cos(a),
        cy - reach * math.sin(a),
        th.secondary,
        1.6,
        dash="5,4",
    )
    s.text(
        cx + (reach + 8) * math.cos(a),
        cy - (reach + 8) * math.sin(a) - 4,
        "reference direction",
        12,
        th.secondary,
    )
    arc_r = 74.0
    s.path(
        f"M {cx - arc_r:.1f} {cy:.1f} A {arc_r} {arc_r} 0 0 1 "
        f"{cx + arc_r * math.cos(a):.1f} {cy - arc_r * math.sin(a):.1f}",
        stroke=th.secondary,
        sw=1.6,
    )
    mid = math.radians(180.0 - phi / 2)
    s.text(
        cx + (arc_r + 14) * math.cos(mid),
        cy - (arc_r + 14) * math.sin(mid) + 5,
        "$φ$",
        16,
        th.secondary,
    )
    # The rotation, in steps, drawn under the turntable.
    rot_r = 68.0
    start, end = math.radians(-160.0), math.radians(-20.0)
    s.path(
        f"M {cx + rot_r * math.cos(start):.1f} {cy - rot_r * math.sin(start):.1f} "
        f"A {rot_r} {rot_r} 0 0 0 {cx + rot_r * math.cos(end):.1f} "
        f"{cy - rot_r * math.sin(end):.1f}",
        stroke=th.accent,
        sw=2.0,
    )
    hx, hy = cx + rot_r * math.cos(end), cy - rot_r * math.sin(end)
    s.arrow(hx - 10, hy + 6, hx + 1, hy - 2, th.accent, 2.0)
    s.text(cx, cy + 100, "turned through 360° in steps of $Δφ$", 13, th.accent)

    # ===== Diffuse field: reverberation room, the two meters in turn ======
    s.text(
        672,
        64,
        "Diffuse field: reverberation room (5.6, Annex B)",
        15,
        th.fg,
        bold=True,
    )
    s.path("M 470 84 L 876 96 L 862 378 L 482 364 Z", fill=th.bg, stroke=th.fg, sw=2.2)
    _speaker(s, th, 506, 126, 1.0)
    _speaker(s, th, 834, 336, -1.0)
    s.text(540, 131, "two uncorrelated sources (B.1.4)", 12, th.muted, anchor="start")
    # The circular path the microphones are moved along (B.1.3).
    px, py = 666.0, 236.0
    s.ellipse(px, py, 96, 46, "none", th.accent, 2.0, dash="7,5")
    s.text(px, py - 58, "in turn, at the same positions (5.1)", 12, th.fg)
    _meter_plan(s, th, px - 96, py, 180.0, 64.0)
    s.text(px - 108, py - 4, "reference", 12, th.primary, anchor="end")
    s.text(px - 108, py + 16, "$L_{D,ref}$", 13, th.primary, anchor="end")
    _meter_plan(s, th, px + 96, py, 0.0, 64.0)
    s.text(px + 108, py - 4, "under test", 12, th.primary, anchor="start")
    s.text(px + 108, py + 16, "$L_D$", 13, th.primary, anchor="start")
    s.text(px, py + 72, "circular path, not parallel to any wall,", 12, th.accent)
    s.text(px, py + 88, "radius ≥ 1 m and ≥ 3 × the meter (B.1.3)", 12, th.accent)

    # ===== The readings, in the order they are taken =======================
    steps_free = (
        "1  reference microphone at the centre: $L_o$ (A.3.2)",
        "2  meter facing the source: $L_{rd}$; $G_F = L_{rd} − L_o$",
        "3  turn it through 360°: $L(φ, h)$ in the X-Y plane",
        "4  turn it 90° about its own axis, again: $L(φ, v)$",
        "5  weight each reading by $K(φ)$: $γ$; $G_{RI} = G_F − 10 lg γ$",
    )
    steps_diffuse = (
        "1  reference meter on the path: $L_{D,ref}$",
        "2  meter under test on the same path: $L_D$",
        "3  $ΔG_D = L_D − L_{D,ref}$, Formula (8)",
        "4  add $G_{D,ref}$ by how the reference was calibrated:",
        "Formula (9), (10) or (11)",
    )
    for k, text in enumerate(steps_free):
        s.text(26, 414 + 24 * k, text, 13, th.fg, anchor="start")
    for k, text in enumerate(steps_diffuse):
        s.text(
            474 + (22 if k == len(steps_diffuse) - 1 else 0),
            414 + 24 * k,
            text,
            13,
            th.fg,
            anchor="start",
        )


# ---------------------------------------------------------------------------
# IEC 62585: the substitution that gives a meter's correction on a source
# (Annexes D, E and F, Figures D.1, E.1 and F.1)
# ---------------------------------------------------------------------------


#: The first two readings of every method are taken in the free field.
_FREE_FIELD_READINGS = 2


def _meter_side(s: SVG, th: Theme, x: float, y: float) -> None:
    """A sound level meter from the side, its microphone at (x, y) facing left."""
    s.line(x + 5, y, x + 16, y, th.fg, 3.0)
    s.path(
        f"M {x + 16} {y - 4} L {x + 32} {y - 13} L {x + 104} {y - 13} "
        f"L {x + 104} {y + 13} L {x + 32} {y + 13} L {x + 16} {y + 4} Z",
        fill=th.primary,
        stroke=th.fg,
        sw=1.4,
    )
    s.circle(x, y, 5.5, th.fg)


def _reference_side(s: SVG, th: Theme, x: float, y: float, facing: float) -> None:
    """A laboratory standard microphone on its preamplifier, the diaphragm at
    (x, y), facing left (``facing`` = -1) or right (+1).
    """
    back = -facing
    capsule_end = x + back * 14
    body_end = x + back * 92
    s.rect(min(x, capsule_end), y - 7, 14, 14, th.secondary, th.fg, rx=2, sw=1.3)
    s.rect(min(capsule_end, body_end), y - 4.5, 78, 9, th.panel, th.fg, rx=2, sw=1.2)


def _wave_in(s: SVG, th: Theme, x: float, y: float) -> None:
    """A free progressive field arriving from the left: three parallel arrows."""
    for dy in (-9.0, 0.0, 9.0):
        s.arrow(x, y + dy, x + 36, y + dy, th.muted, 1.4)


def _calibrator_on(s: SVG, th: Theme, x: float, y: float) -> None:
    """A sound calibrator fitted over the microphone at (x, y)."""
    s.rect(x - 44, y - 17, 40, 34, th.panel, th.fg, rx=3, sw=1.5)
    s.rect(x - 8, y - 9, 8, 18, th.bg, th.fg, sw=1.2)


def _actuator_on(s: SVG, th: Theme, x: float, y: float) -> None:
    """An electrostatic actuator on the diaphragm at (x, y), with its lead."""
    s.rect(x - 9, y - 15, 5, 30, th.accent, th.fg, sw=1.2)
    s.path(
        f"M {x - 9} {y} C {x - 24} {y} {x - 22} {y + 16} {x - 38} {y + 16}",
        stroke=th.accent,
        sw=1.6,
    )


def _step(s: SVG, th: Theme, x: float, y: float, number: str) -> None:
    s.text(x, y + 5, number, 14, th.fg, bold=True)


def _d_free_field_corrections_setup(s: SVG, th: Theme) -> None:
    """IEC 62585: the readings of Annexes D, E and F, each by substitution.

    The meter and a type LS2P reference microphone read the same free field
    in turn, then the same source; the correction is the meter's free-field
    response relative to its response on the source, carried over from the
    reference's free-field correction.
    """
    columns = (
        ("Sound calibrator", "Annex D", 150.0),
        ("Comparison coupler", "Annex E", 450.0),
        ("Electrostatic actuator", "Annex F", 750.0),
    )
    for heading, annex, cx in columns:
        s.text(cx, 66, heading, 15, th.fg, bold=True)
        s.text(cx, 86, annex, 13, th.muted)
    for x in (300.0, 600.0):
        s.line(x, 54, x, 424, th.muted, 1.0, dash="4,4")

    rows_y = (126.0, 186.0, 246.0, 306.0)
    # ----- Annex D: free field for both, then the calibrator on both ------
    x0 = 14.0
    for k, (y, label) in enumerate(
        zip(
            rows_y,
            ("$L_{ind1}$", "$L_{ind2}$", "$L_{ind3}$", "$L_{ind4}$"),
            strict=True,
        )
    ):
        _step(s, th, x0 + 4, y, str(k + 1))
        mic = x0 + 76
        if k < _FREE_FIELD_READINGS:
            _wave_in(s, th, x0 + 20, y)
        else:
            _calibrator_on(s, th, mic, y)
        if k % 2 == 0:
            _meter_side(s, th, mic, y)
        else:
            _reference_side(s, th, mic, y, -1.0)
        s.text(x0 + 192, y + 5, label, 15, th.fg, anchor="start")

    # ----- Annex E: free field for both, then both in the coupler ---------
    x0 = 314.0
    for k, (y, label) in enumerate(
        zip(rows_y[:2], ("$L_{ind1}$", "$L_{ind2}$"), strict=True)
    ):
        _step(s, th, x0 + 4, y, str(k + 1))
        _wave_in(s, th, x0 + 20, y)
        mic = x0 + 76
        if k == 0:
            _meter_side(s, th, mic, y)
        else:
            _reference_side(s, th, mic, y, -1.0)
        s.text(x0 + 192, y + 5, label, 15, th.fg, anchor="start")
    y = 272.0
    _step(s, th, x0 + 4, y, "3")
    box_left, box_right = 426.0, 464.0
    s.rect(box_left, y - 18, box_right - box_left, 36, th.panel, th.fg, rx=3, sw=1.5)
    _reference_side(s, th, box_left - 2, y, 1.0)
    _meter_side(s, th, box_right + 2, y)
    s.text(372, y - 26, "$L_{ind3a}$", 15, th.fg)
    s.text(528, y - 26, "$L_{ind3b}$", 15, th.fg)
    s.text(450, y + 40, "face to face, read together or in turn", 12, th.muted)

    # ----- Annex F: free field for both, then the actuator on the meter ---
    x0 = 614.0
    for k, (y, label) in enumerate(
        zip(
            rows_y[:3],
            ("$L_{ind1}(f)$", "$L_{ind2}(f)$", "$L_{ind3}(f)$"),
            strict=True,
        )
    ):
        _step(s, th, x0 + 4, y, str(k + 1))
        mic = x0 + 76
        if k < _FREE_FIELD_READINGS:
            _wave_in(s, th, x0 + 20, y)
        else:
            _actuator_on(s, th, mic, y)
        if k == 1:
            _reference_side(s, th, mic, y, -1.0)
        else:
            _meter_side(s, th, mic, y)
        s.text(x0 + 192, y + 5, label, 15, th.fg, anchor="start")

    # ----- What each column gives ----------------------------------------
    # (D.7) and (E.6) as they stand with stable sources: the drift of the
    # free field and the difference of the levels on the source, the two
    # terms the NOTEs let be zero, are left out.
    s.text(150, 352, "Formula (D.7)", 13, th.fg, bold=True)
    s.text(150, 371, "$(L_{ind1} − L_{ind3}) − (L_{ind2} − L_{ind4})$", 13, th.fg)
    s.text(150, 390, "$+ C_{FF,RM}$", 13, th.fg)
    s.text(150, 408, "with stable sources (NOTEs 2, 3)", 12, th.muted)
    s.text(450, 352, "Formula (E.6)", 13, th.fg, bold=True)
    s.text(450, 371, "$(L_{ind1} − L_{ind3b}) − (L_{ind2} − L_{ind3a})$", 13, th.fg)
    s.text(450, 390, "$+ C_{FF,RM}$", 13, th.fg)
    s.text(450, 408, "with the labels of Figure E.1,", 12, th.muted)
    s.text(450, 424, "a stable source and equal coupler levels", 12, th.muted)
    s.text(750, 352, "Formula (F.13)", 13, th.fg, bold=True)
    s.text(750, 371, "every term referred to $f_0$,", 13, th.fg)
    s.text(750, 390, "where the correction is zero", 13, th.fg)

    # ----- Key -------------------------------------------------------------
    ky = 458.0
    _meter_side(s, th, 40, ky)
    s.text(156, ky + 5, "sound level meter", 13, th.fg, anchor="start")
    _reference_side(s, th, 330, ky, -1.0)
    s.text(432, ky + 5, "reference microphone, type LS2P", 13, th.fg, anchor="start")
    _wave_in(s, th, 690, ky)
    s.text(736, ky + 5, "free field", 13, th.fg, anchor="start")
    s.text(
        450,
        500,
        "Each free-field pair is read in turn at the same place (Annex G); "
        "$C_{FF,RM}$ comes from IEC/TS 61094-7.",
        13,
        th.muted,
    )
