#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Diagrams of the fluids guides: the medium itself, computed.

One subject: the properties of the fluid a measurement is made in, as a
calculation rather than a place. Nothing here has a microphone in it. The
humid-air plate draws the model of IEC 61094-2:2009 Annex F as the chain it
is evaluated in, from the four conditions a caller supplies to the seven
quantities the library returns, marking which of them the annex prints a
value for and which it only writes an expression for.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .canvas import SVG, Theme


def _d_humid_air_chain(s: SVG, th: Theme) -> None:
    """IEC 61094-2:2009 Annex F as the chain it is evaluated in.

    Four conditions go in (the measured t, p_s and H of Clause F.1, and the
    carbon dioxide fraction Clause F.2 recommends in the absence of a
    measurement), and each reaches only the steps its own expression names:
    the temperature the saturation vapour pressure and the enhancement
    factor, the static pressure the enhancement factor and the mole
    fraction, the humidity the mole fraction alone. The water vapour comes
    first, from the saturation vapour pressure and the enhancement factor,
    and its mole fraction enters every quantity after it. The compressibility factor feeds the density alone;
    the speed of sound, the ratio of specific heats and the viscosity are
    polynomials of their own (Equations F.2 to F.4); and the thermal
    diffusivity is the one tabulated quantity that takes another tabulated
    quantity as an input, Equation F.5 forming it from the density and the
    two expressions of Clause F.6. The green values are the first condition
    set of Table F.1, and the coefficients are named by their Table F.2
    column rather than listed.
    """
    col_l, col_m, col_r, col_w = 40.0, 325.0, 610.0, 250.0
    mid_l, mid_m, mid_r = (x + col_w / 2 for x in (col_l, col_m, col_r))

    # --- The four inputs, each with the range Clause F.1 validates it over --
    in_y, in_h, in_w = 54.0, 84.0, 196.0
    for x0, symbol, name, note, assumed in (
        (40.0, "$t$", "temperature, °C", "valid from 15 °C to 27 °C", False),
        (248.0, "$p_s$", "static pressure, Pa", "valid from 60 kPa to 110 kPa", False),
        (456.0, "$H$", "relative humidity, %", "valid from 10 % to 90 %", False),
        (664.0, "$x_c$", "CO₂ mole fraction", "0.000 4 unless measured", True),
    ):
        s.rect(
            x0,
            in_y,
            in_w,
            in_h,
            th.panel,
            th.muted if assumed else th.fg,
            rx=8,
            sw=1.8,
            dash="6,4" if assumed else "",
        )
        cx = x0 + in_w / 2
        s.text(cx, in_y + 26, symbol, 18, th.fg, bold=True)
        s.text(cx, in_y + 50, name, 13, th.fg)
        s.text(cx, in_y + 72, note, 12, th.muted)

    # Each measured condition reaches the steps its own expression names and
    # no others: Clause F.2 writes the saturation vapour pressure in the
    # temperature alone, the enhancement factor in the static pressure and
    # the temperature, and the mole fraction in the relative humidity, the
    # static pressure and those two. One line per dependency is therefore
    # the drawing: a bus carrying all three would assert every one of the
    # nine pairings of three conditions with three steps, and the clause
    # prints five. The two lines that have to travel take a lane each, the
    # shorter above the longer so that the lower one passes under the turn
    # of the upper rather than through it, and they cross the drops between
    # them at a right angle: nothing in this band ever joins another line,
    # so a crossing is only a crossing. The carbon dioxide box keeps the
    # note it had, its three destinations being too far down the plate to
    # reach without cutting through the rest.
    row_b, h_b = 206.0, 96.0
    y_out, y_tip = in_y + in_h, row_b - 2
    s.text(762.0, 152.0, "$x_c$ enters $ρ$, $c_0$ and $κ$", 12, th.muted)
    # Straight down into the box underneath: the temperature into the
    # saturation vapour pressure, the static pressure and the humidity into
    # the mole fraction, each leaving and landing inside its own box.
    for cx in (mid_l, 380.0, 520.0):
        s.arrow(cx, y_out, cx, y_tip, th.muted, 1.4)
    # Across to the enhancement factor: the static pressure in the upper
    # lane, the temperature in the lower, landing either side of its centre.
    for x_out, lane, x_in in ((430.0, 164.0, 656.0), (210.0, 180.0, 626.0)):
        s.line(x_out, y_out, x_out, lane, th.muted, 1.4)
        s.line(x_out, lane, x_in, lane, th.muted, 1.4)
        s.arrow(x_in, lane, x_in, y_tip, th.muted, 1.4)

    # Every box names its quantity on the same line, so the row is set at the
    # one size the longest name allows (the Spanish speed of sound).
    name_size = s.fit_size(
        (
            "saturation vapour pressure",
            "water vapour mole fraction",
            "enhancement factor",
            "compressibility factor",
            "density, CIPM-2007",
            "zero-frequency speed of sound",
            "thermal conductivity",
            "thermal diffusivity",
            "ratio of specific heats",
            "specific heat capacity",
            "viscosity",
        ),
        (13, 12),
        col_w - 20,
    )
    styles = {
        "step": (th.primary, "", 2.0),
        "printed": (th.accent, "", 2.4),
        "f6": (th.secondary, "7,5", 2.0),
    }

    def stage(
        x0: float,
        y0: float,
        h: float,
        labels: tuple[str, str, str, str],
        kind: str,
    ) -> None:
        """One quantity: symbol, name, what it is computed in, and a foot line.

        The foot line of a printed quantity is its Table F.1 value, set in the
        colour of its border; the other two kinds carry a note instead.
        """
        stroke, dash, sw = styles[kind]
        symbol, name, inputs, foot = labels
        s.rect(x0, y0, col_w, h, th.panel, stroke, rx=10, sw=sw, dash=dash)
        cx = x0 + col_w / 2
        s.text(cx, y0 + 24, symbol, 16, stroke, bold=True)
        s.text(cx, y0 + 46, name, name_size, th.fg)
        s.text(cx, y0 + 67, inputs, 12, th.fg)
        if kind == "printed":
            s.text(cx, y0 + 88, foot, 13, stroke, bold=True)
        else:
            s.text(cx, y0 + 88, foot, 12, stroke if kind == "f6" else th.muted)

    # --- The water vapour: two factors meet in the mole fraction -----------
    stage(
        col_l,
        row_b,
        h_b,
        (
            "$p_{sv}$",
            "saturation vapour pressure",
            "$exp(a_0 T^2 + a_1 T + a_2 + a_3 T^{−1})$",
            "Table F.2, $a_0$ to $a_3$",
        ),
        "step",
    )
    stage(
        col_m,
        row_b,
        h_b,
        (
            "$x_w$",
            "water vapour mole fraction",
            "in $H$, $p_s$, $p_{sv}$ and $f$",
            "no coefficients of its own",
        ),
        "step",
    )
    stage(
        col_r,
        row_b,
        h_b,
        (
            "$f(p_s, t)$",
            "enhancement factor",
            "$a_0 + a_1 p_s + a_2 t^2$",
            "Table F.2, $a_0$ to $a_2$",
        ),
        "step",
    )
    y_mid = row_b + h_b / 2
    s.arrow(col_l + col_w + 2, y_mid, col_m - 3, y_mid, th.fg, 1.8)
    s.arrow(col_r - 2, y_mid, col_m + col_w + 3, y_mid, th.fg, 1.8)

    # --- x_w leaves the stage and enters everything but the diffusivity -----
    feed_y = row_b + h_b + 32
    h = 100.0
    row_c, row_d, row_e = feed_y + 20, feed_y + 146, feed_y + 272
    s.line(mid_m, row_b + h_b, mid_m, feed_y, th.fg, 1.8)
    s.line(mid_l, feed_y, mid_r, feed_y, th.fg, 1.8)
    for cx in (mid_l, mid_m, mid_r):
        s.arrow(cx, feed_y, cx, row_c - 2, th.fg, 1.8)
    s.text(
        mid_m + 12,
        feed_y - 10,
        "$x_w$ enters $Z$, $ρ$, $c_0$, $κ$, $η$, $k_a$ and $C_p$",
        12,
        th.muted,
        "start",
    )

    # --- Left column: the density through Z, and the conductivity ----------
    # --- Middle column: rho and the diffusivity it makes with k_a and C_p --
    # --- Right column: the three polynomials that need neither -------------
    stage(
        col_l,
        row_c,
        h,
        (
            "$Z$",
            "compressibility factor",
            "in $p_s$, $t$, $T$ and $x_w$",
            "Table F.2, $a_0$ to $a_8$",
        ),
        "step",
    )
    stage(
        col_m,
        row_c,
        h,
        (
            "$ρ$  (F.1)",
            "density, CIPM-2007",
            "in $x_c$, $p_s$, $Z$, $T$ and $x_w$",
            "1.186 084 8 kg/m³",
        ),
        "printed",
    )
    stage(
        col_r,
        row_c,
        h,
        (
            "$c_0$  (F.2)",
            "zero-frequency speed of sound",
            "in $t$, $x_w$, $p_s$, $x_c$; $a_0$ to $a_{15}$",
            "345.866 52 m/s",
        ),
        "printed",
    )
    stage(
        col_l,
        row_d,
        h,
        (
            "$k_a$",
            "thermal conductivity",
            "in $T$ and $x_w$; $a_0$ to $a_4$",
            "Clause F.6, no value printed",
        ),
        "f6",
    )
    stage(
        col_m,
        row_d,
        h,
        (
            "$α_t$  (F.5)",
            "thermal diffusivity",
            "in $k_a$, $ρ$ and $C_p$",
            "2.115 317 × 10⁻⁵ m²/s",
        ),
        "printed",
    )
    stage(
        col_r,
        row_d,
        h,
        (
            "$κ$  (F.3)",
            "ratio of specific heats",
            "in $t$, $x_w$, $p_s$, $x_c$; $a_0$ to $a_{15}$",
            "1.400 757 3",
        ),
        "printed",
    )
    stage(
        col_m,
        row_e,
        h,
        (
            "$C_p$",
            "specific heat capacity",
            "in $T$ and $x_w$; $a_0$ to $a_9$",
            "Clause F.6, no value printed",
        ),
        "f6",
    )
    stage(
        col_r,
        row_e,
        h,
        (
            "$η$  (F.4)",
            "viscosity",
            "in $T$ and $x_w$; $a_0$ to $a_5$",
            "1.826 566 × 10⁻⁵ Pa·s",
        ),
        "printed",
    )
    s.arrow(col_l + col_w + 2, row_c + h / 2, col_m - 3, row_c + h / 2, th.fg, 1.8)
    s.arrow(col_l + col_w + 2, row_d + h / 2, col_m - 3, row_d + h / 2, th.fg, 1.8)
    s.arrow(mid_m, row_c + h + 1, mid_m, row_d - 3, th.fg, 1.8)
    s.arrow(mid_m, row_e - 1, mid_m, row_d + h + 3, th.fg, 1.8)

    # --- The key, in the one cell the chain leaves free ---------------------
    key_y = row_e + 6
    key_labels = (
        "a property, value in Table F.1",
        "a property, only in Clause F.6",
        "a step on the way",
    )
    key_size = s.fit_size(key_labels, (12, 11), col_w - 54)
    for k, (stroke, dash) in enumerate(
        ((th.accent, ""), (th.secondary, "7,5"), (th.primary, ""))
    ):
        yy = key_y + 22 * k
        s.rect(col_l + 4, yy, 30, 16, th.panel, stroke, rx=4, sw=2.0, dash=dash)
        s.text(col_l + 46, yy + 13, key_labels[k], key_size, th.fg, "start")
    s.text(
        col_l + 4,
        key_y + 79,
        "values printed at 23 °C, 101 325 Pa, 50 %",
        12,
        th.muted,
        "start",
    )

    # --- The closed forms the boxes stand for -------------------------------
    box_y = row_e + h + 28
    s.rect(40, box_y, 820, 108, th.panel, th.fg, rx=8, sw=1.6)
    s.text(
        450,
        box_y + 30,
        "$ρ = [3.483 740 + 1.4446 (x_c − 0.000 4)] × 10^{−3} · p_s/(Z T) · "
        "(1 − 0.378 0 x_w)$",
        15,
        th.fg,
    )
    s.text(
        450,
        box_y + 60,
        "$Z = 1 − (p_s/T) [a_0 + a_1 t + a_2 t^2 + (a_3 + a_4 t) x_w + "
        "(a_5 + a_6 t) x_w^2] + (p_s^2/T^2) (a_7 + a_8 x_w^2)$",
        14,
        th.fg,
    )
    s.text(250, box_y + 90, "$x_w = (H/100) · (p_{sv}/p_s) · f(p_s, t)$", 14, th.fg)
    s.text(650, box_y + 90, "$α_t = k_a/(ρ C_p)$", 14, th.fg)

    foot = box_y + 108
    s.text(
        450,
        foot + 26,
        "$T = T_0 + t$ with $T_0$ = 273.15 K: a box that reads $t$ takes degrees "
        "Celsius, one that reads $T$ takes kelvin",
        12,
        th.muted,
    )
    s.text(
        450,
        foot + 48,
        "relative standard uncertainty of the equations: $ρ$ 22 × 10⁻⁶, "
        "$c_0$ 3 × 10⁻⁴, $κ$ 3.2 × 10⁻⁴, and none is quoted for the rest",
        12,
        th.muted,
    )
    s.text(
        450,
        foot + 70,
        "dispersion moves the speed of sound by less than the uncertainty of "
        "$c_0$ at the frequencies of a reciprocity calibration",
        12,
        th.muted,
    )
