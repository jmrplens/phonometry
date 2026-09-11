#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Figures for the vibration guides: exposure, mobility and structure-borne power.

Vibration as a measured quantity and as a transmission path: the human
exposure weightings and daily exposure, mechanical mobility and dynamic
stiffness, structure-borne sound power, the SEA coupling loss factors, and the
bearing-fault envelope that reads a machine's condition. Everything here is
embedded by a page under ``vibration/``.
"""

import math
from typing import TYPE_CHECKING, Literal


def _sci_math(value: float, digits: int = 2) -> str:
    r"""A scientific-notation reading composed as mathtext.

    ``f"{4.4e-3:.2e}"`` writes "4.40e-03", which a figure has no business
    showing; this returns ``$4.40\times10^{-3}$``, where mathtext sets the
    proper multiplication sign and a typographic minus in the exponent.
    """
    exponent = math.floor(math.log10(abs(value)))
    mantissa = value / 10.0**exponent
    return rf"${mantissa:.{digits}f}\times10^{{{exponent}}}$"


import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from phonometry._plot.common import format_frequency_axis, theme_fill

from .i18n import _LANG, _fmt_minus
from .theme import (
    COLOR_FG,
    COLOR_GRID,
    COLOR_MUTED,
    COLOR_PANEL,
    COLOR_PRIMARY,
    COLOR_QUATERNARY,
    COLOR_SECONDARY,
    COLOR_TERTIARY,
    COLOR_ZONE_A,
    COLOR_ZONE_B,
    COLOR_ZONE_C,
    COLOR_ZONE_D,
    LABEL_FREQ_HZ,
    _band_index_axis,
    save_figure,
)

if TYPE_CHECKING:
    from matplotlib.artist import Artist


def generate_junction_transmission(output_dir: str) -> None:
    """Hopkins 5.2.1.3 bending-wave transmission at a rigid X-junction."""
    print("Generating junction_transmission...")
    from phonometry import vibration

    # X-junction between a 100 mm and a 200 mm concrete plate (cL = 3200 m/s,
    # rho = 2400 kg/m^3 -> rho_s = 240 and 480 kg/m^2).
    res = vibration.junction_transmission("X", 0.1, 3200.0, 240.0, 0.2, 3200.0, 480.0)
    assert res.straight is not None
    assert res.straight_average is not None
    angles = res.angles_deg

    _fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.plot(
        angles,
        res.corner,
        color=COLOR_PRIMARY,
        linewidth=2.0,
        label=r"corner $\tau_{12}(\theta)$",
    )
    ax.plot(
        angles,
        res.straight,
        color=COLOR_SECONDARY,
        linewidth=2.0,
        label=r"straight $\tau_{13}(\theta)$",
    )
    ax.axhline(
        res.corner_average,
        color=COLOR_PRIMARY,
        linestyle="--",
        linewidth=1.3,
        label="corner average",
    )
    ax.axhline(
        res.straight_average,
        color=COLOR_SECONDARY,
        linestyle=":",
        linewidth=1.3,
        label="straight average",
    )

    # The cut-off: beyond arcsin(chi) the receiving plate has no propagating
    # bending wave to accept, so the corner path shuts completely.
    theta_co = math.degrees(math.asin(min(1.0, res.chi)))
    ax.axvspan(theta_co, 90.0, color=theme_fill(COLOR_SECONDARY, ax), zorder=0)
    ax.axvline(
        theta_co,
        color=COLOR_FG,
        linestyle="-.",
        linewidth=1.4,
        label=r"cut-off $\theta_\mathrm{co} = \arcsin\chi$",
    )
    ax.annotate(
        rf"$\theta_\mathrm{{co}} = {theta_co:.0f}°$: "
        r"$\tau_{12} = 0$ beyond it",
        xy=(theta_co, 0.5 * float(np.max(res.corner))),
        xytext=(theta_co + 6.0, 0.78 * float(np.max(res.corner))),
        fontsize=9.5,
        color=COLOR_FG,
        arrowprops={"arrowstyle": "->", "color": COLOR_MUTED},
    )

    ax.set_xlabel("Incidence angle [degrees]")
    ax.set_ylabel(r"Transmission coefficient $\tau$")
    ax.set_title(
        "Bending-wave transmission at a rigid X-junction (Hopkins 5.2.1.3)",
        pad=12,
    )
    ax.set_xlim(0.0, 90.0)
    ax.set_ylim(bottom=0.0)
    ax.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=9)

    info = [
        "X-junction: 100 mm / 200 mm concrete",
        rf"$\chi$ = {res.chi:.3f},  $\psi$ = {res.psi:.3f}",
        rf"$\theta_\mathrm{{co}} = \arcsin\chi$ = {theta_co:.1f}°",
        f"corner avg = {res.corner_average:.4f}",
        f"straight avg = {res.straight_average:.4f}",
    ]
    ax.text(
        0.015,
        0.60,
        "\n".join(info),
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    plt.tight_layout()
    save_figure(output_dir, "junction_transmission.svg")
    plt.close()


def generate_mechanical_mobility(output_dir: str) -> None:
    """ISO 7626-1 receptance/mobility/accelerance of a SDOF resonator."""
    print("Generating mechanical_mobility...")
    from phonometry import vibration

    m, k, c = 2.0, 8000.0, 5.0
    f0 = vibration.resonance_frequency(m, k)
    freq = np.logspace(np.log10(f0 / 20.0), np.log10(f0 * 20.0), 600)
    w0 = 2.0 * np.pi * f0
    h = vibration.sdof_receptance(freq, m, k, c)
    y = vibration.convert_frf(h, freq, "receptance", "mobility")
    a = vibration.convert_frf(h, freq, "receptance", "accelerance")
    # Normalise each FRF to O(1) near resonance so all three share one axis.
    curves = [
        (np.abs(h) * k, COLOR_PRIMARY, r"Receptance $|H|$ ($\times k$)"),
        (np.abs(y) * k / w0, COLOR_SECONDARY, r"Mobility $|Y|$ ($\times k/\omega_0$)"),
        (
            np.abs(a) * k / w0**2,
            COLOR_TERTIARY,
            r"Accelerance $|A|$ ($\times k/\omega_0^2$)",
        ),
    ]
    _fig, ax = plt.subplots(figsize=(10, 6.2))
    for mag, color, label in curves:
        ax.loglog(freq, mag, color=color, linewidth=2.0, label=label)
    ax.axvline(
        f0, color=COLOR_GRID, linestyle="--", linewidth=1.2, label="resonance $f_0$"
    )

    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Normalized FRF magnitude")
    ax.set_title("ISO 7626-1 Mechanical Mobility FRFs", pad=12)
    ax.set_xlim(freq[0], freq[-1])
    format_frequency_axis(ax, float(freq[0]), float(freq[-1]))
    ax.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.legend(loc="lower center", fontsize=9, ncol=2)

    info = [
        "SDOF: $m$ = 2 kg, $k$ = 8000 N/m, $c$ = 5 N·s/m",
        r"$H = 1/(k - \omega^2 m + \mathrm{j}\,\omega c)$",
        r"$Y = \mathrm{j}\,\omega H$,   $A = -\omega^2 H$  (Table 1)",
        rf"$f_0$ = {f0:.1f} Hz,  $|Y(f_0)| = 1/c$",
    ]
    ax.text(
        0.985,
        0.97,
        "\n".join(info),
        transform=ax.transAxes,
        va="top",
        ha="right",
        fontsize=10,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    plt.tight_layout()
    save_figure(output_dir, "mechanical_mobility.svg")
    plt.close()


def generate_transfer_stiffness(output_dir: str) -> None:
    """ISO 10846 dynamic transfer stiffness: true vs indirect-method recovery."""
    print("Generating transfer_stiffness...")
    from phonometry import vibration

    # Kelvin-Voigt isolator k + jwc, loaded by a blocking mass m2.
    k, c, m2 = 1.0e6, 120.0, 8.0
    f0 = np.sqrt(k / m2) / (2.0 * np.pi)
    freq = np.logspace(np.log10(f0 / 5.0), np.log10(f0 * 40.0), 600)
    w = 2.0 * np.pi * freq

    k_true = k + 1j * w * c  # exact transfer stiffness
    t = vibration.base_transmissibility(freq, m2, k, c)  # mass-loaded transmissibility
    k_indirect = vibration.transfer_stiffness_indirect(
        freq, t, m2
    )  # ISO 10846-3 Eq. (1)

    # Where the standard's own criterion starts holding: |T| <= 0.1
    # (Inequality 2), not the 3 f0 rule of thumb.
    magnitude_t = np.abs(np.asarray(t, dtype=np.complex128))
    valid = np.flatnonzero(magnitude_t <= 0.1)
    f_valid = float(freq[valid[0]]) if valid.size else float(freq[-1])
    level_error = vibration.transfer_stiffness_level(
        k_indirect
    ) - vibration.transfer_stiffness_level(k_true)
    eta = np.imag(k_true) / np.real(k_true)  # Kelvin-Voigt: w c / k

    fig, (ax, mid, low) = plt.subplots(
        3,
        1,
        figsize=(10, 10.2),
        sharex=True,
        gridspec_kw={"height_ratios": [1.5, 1.0, 0.85]},
    )
    ax.semilogx(
        freq,
        vibration.transfer_stiffness_level(k_true),
        color=COLOR_PRIMARY,
        linewidth=2.2,
        label=r"true $L_k$ of $k_{2,1}=k+\mathrm{j}\,\omega c$",
    )
    ax.semilogx(
        freq,
        vibration.transfer_stiffness_level(k_indirect),
        color=COLOR_SECONDARY,
        linewidth=2.0,
        linestyle="--",
        label=r"indirect method $-(2\pi f)^2 m_2 T$",
    )
    ax.axvline(
        f0, color=COLOR_GRID, linestyle=":", linewidth=1.2, label="resonance $f_0$"
    )
    for panel in (ax, mid, low):
        panel.axvspan(
            freq[0], f_valid, color=theme_fill(COLOR_SECONDARY, panel), zorder=0
        )
        panel.axvline(f_valid, color=COLOR_FG, linestyle="-.", linewidth=1.3)
        panel.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
        panel.set_axisbelow(True)

    ax.set_ylabel(r"$L_k$ [dB re 1 N/m]")
    ax.set_title("ISO 10846 Dynamic Transfer Stiffness", pad=12)
    ax.set_xlim(freq[0], freq[-1])
    ax.legend(loc="upper left", fontsize=9)
    info = [
        "Kelvin-Voigt: $k$ = 1 MN/m, $c$ = 120 N·s/m",
        rf"blocking mass $m_2$ = 8 kg,  $f_0$ = {f0:.1f} Hz",
        rf"$|T|$ falls to 0.1 at {f_valid:.0f} Hz",
        "shaded: Inequality (2) not met → no result",
    ]
    ax.text(
        0.985,
        0.05,
        "\n".join(info),
        transform=ax.transAxes,
        va="bottom",
        ha="right",
        fontsize=10,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    mid.loglog(
        freq,
        magnitude_t,
        color=COLOR_PRIMARY,
        linewidth=2.0,
        label=r"transmissibility $|T|$",
    )
    mid.axhline(
        0.1,
        color=COLOR_FG,
        linestyle="--",
        linewidth=1.4,
        label=r"TRANSMISSIBILITY_LIMIT = 0.1  ($\Delta L_{1,2}$ = 20 dB)",
    )
    mid.set_ylabel("$|T|$")
    mid.legend(loc="lower left", fontsize=9)
    twin = mid.twinx()
    # The primary axes must draw over the twin, or the shaded +-1 dB band
    # hides the |T| curve where the two cross.
    mid.set_zorder(twin.get_zorder() + 1)
    mid.patch.set_visible(False)
    twin.semilogx(freq, level_error, color=COLOR_TERTIARY, linewidth=1.8)
    twin.axhspan(-1.0, 1.0, color=theme_fill(COLOR_TERTIARY, twin), zorder=0)
    twin.set_ylim(-6.0, 6.0)
    twin.set_ylabel(
        r"$L_{k,\mathrm{ind}} - L_{k,\mathrm{true}}$ [dB]", color=COLOR_TERTIARY
    )
    twin.tick_params(axis="y", colors=COLOR_TERTIARY)
    # Drawn by the host, positioned by the twin. The host is deliberately
    # raised above the twin a few lines up, so the |T| curve is painted over
    # anything the twin draws, this label included; a zorder on a twin artist
    # cannot answer that, because an axes is drawn whole. Handing the label to
    # the host leaves it exactly where it was on the page and puts it above
    # the curve, and the chip then keeps the curve out of the letters.
    mid.text(
        0.985,
        0.06,
        "the ±1 dB the criterion buys",
        transform=twin.transAxes,
        va="bottom",
        ha="right",
        fontsize=9.5,
        color=COLOR_TERTIARY,
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    low.semilogx(
        freq,
        eta,
        color=COLOR_SECONDARY,
        linewidth=2.0,
        label=r"loss factor $\eta = \mathrm{Im}(k_{2,1})/"
        r"\mathrm{Re}(k_{2,1})$",
    )
    low.set_ylabel(r"$\eta$")
    low.set_xlabel(LABEL_FREQ_HZ)
    format_frequency_axis(low, float(freq[0]), float(freq[-1]))
    low.legend(loc="upper left", fontsize=9)
    low.text(
        0.985,
        0.90,
        "Kelvin-Voigt makes $\\eta$ rise with frequency; real\n"
        "elastomers are far flatter, so this is a model, not a material",
        transform=low.transAxes,
        va="top",
        ha="right",
        fontsize=9.5,
        color=COLOR_FG,
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    fig.align_ylabels()
    plt.tight_layout()
    save_figure(output_dir, "transfer_stiffness.svg")
    plt.close()


def generate_rigid_mass_calibration(output_dir: str) -> None:
    """ISO 7626-2 (7.5.2) operational rigid-mass calibration check."""
    print("Generating rigid_mass_calibration...")
    from phonometry import vibration

    # A 10 kg calibration block: the accelerance must be a flat |A| = 1/m over
    # frequency. The measured chain has a mild ripple and drifts above the
    # +/-5 % band towards a few kHz (a transducer/attachment-compliance error,
    # exactly what the check is meant to catch).
    m = 10.0
    freq = np.logspace(np.log10(20.0), np.log10(5000.0), 400)
    expected = 1.0 / m
    ripple = 0.015 * np.sin(2.0 * np.pi * np.log10(freq))
    drift = 0.05 * (freq / 2500.0) ** 2
    measured = expected * (1.0 + ripple + drift)
    res = vibration.rigid_mass_calibration_check(measured, freq, mass=m)
    within = res.within_tolerance
    tol = res.tolerance

    _fig, (ax_top, ax_bot) = plt.subplots(
        2,
        1,
        sharex=True,
        figsize=(10, 7.0),
        gridspec_kw={"height_ratios": [1.5, 1.0]},
    )
    # Upper panel: measured accelerance against the rigid-mass line + band.
    ax_top.fill_between(
        freq,
        res.expected * (1.0 - tol),
        res.expected * (1.0 + tol),
        color=COLOR_SECONDARY,
        alpha=0.15,
        label="±5 % tolerance band",
    )
    ax_top.semilogx(
        freq,
        res.expected,
        color=COLOR_SECONDARY,
        linestyle="--",
        linewidth=1.6,
        label=r"expected $|A| = 1/m$",
    )
    ax_top.semilogx(
        freq, res.measured, color=COLOR_PRIMARY, linewidth=2.0, label="within tolerance"
    )
    ax_top.semilogx(
        freq[~within],
        res.measured[~within],
        linestyle="none",
        marker="o",
        markersize=4,
        color=COLOR_SECONDARY,
        label="out of tolerance",
    )
    ax_top.set_ylabel("Accelerance $|A|$ [1/kg]")
    ax_top.set_title("ISO 7626-2 Rigid-Mass Calibration Check", pad=12)
    ax_top.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax_top.legend(loc="upper left", fontsize=9)

    # Lower panel: the relative deviation against the same +/-5 % band, where
    # the few-percent tolerance is actually readable.
    ax_bot.axhspan(-100.0 * tol, 100.0 * tol, color=COLOR_SECONDARY, alpha=0.15)
    ax_bot.axhline(0.0, color=COLOR_GRID, linestyle=":", linewidth=1.0)
    ax_bot.semilogx(freq, 100.0 * res.deviation, color=COLOR_PRIMARY, linewidth=2.0)
    ax_bot.semilogx(
        freq[~within],
        100.0 * res.deviation[~within],
        linestyle="none",
        marker="o",
        markersize=4,
        color=COLOR_SECONDARY,
    )
    ax_bot.set_xlabel(LABEL_FREQ_HZ)
    ax_bot.set_ylabel("Deviation [%]")
    ax_bot.set_xlim(freq[0], freq[-1])
    ax_bot.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)

    format_frequency_axis(ax_top, float(freq[0]), float(freq[-1]))
    format_frequency_axis(ax_bot, float(freq[0]), float(freq[-1]))

    info = [
        "calibration block $m$ = 10 kg",
        r"$|A| = 1/m$ = 0.100 1/kg  (7.5.2)",
        "criterion: agree within ±5 %",
        "high-f drift → attachment error",
    ]
    ax_top.text(
        0.985,
        0.05,
        "\n".join(info),
        transform=ax_top.transAxes,
        va="bottom",
        ha="right",
        fontsize=10,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    plt.tight_layout()
    save_figure(output_dir, "rigid_mass_calibration.svg")
    plt.close()


def generate_junction_plate_geometry(output_dir: str) -> None:
    """A T-junction of heavyweight plates to scale.

    A 140 mm concrete floor ending against a continuous 200 mm wall (the
    T-junction whose perpendicular plates are the identical pair), the
    incident bending wave marked. One concept: the junction the
    transmission coefficients describe.
    """
    print("Generating junction_plate_geometry...")
    from phonometry import building

    _fig, ax = plt.subplots(figsize=(9.0, 6.2))
    building.plot_junction_geometry("T2", 0.14, 0.2, ax=ax, language=_LANG)
    plt.tight_layout()
    save_figure(output_dir, "junction_plate_geometry.svg")
    plt.close()


def generate_vibration_weighting(output_dir: str) -> None:
    """ISO 8041-1: the whole-body vertical weighting Wk over its band."""
    print("Generating vibration_weighting.png...")
    from phonometry import vibration

    # A user evaluates the principal ISO 2631-1 weighting Wk on a fine
    # frequency grid across the whole-body band (0,4-100 Hz). The result is the
    # ISO 8041-1 cascade H(f): a gentle +0,5 dB peak near 6 Hz, a band-limiting
    # roll-off below 0,4 Hz and above ~16 Hz.
    freqs = np.geomspace(0.4, 100.0, 240)
    result = vibration.frequency_weighting("Wk", freqs)

    _fig, ax = plt.subplots(figsize=(10, 6.3))
    ax.semilogx(
        result.frequencies,
        result.magnitude_db,
        color=COLOR_PRIMARY,
        linewidth=1.9,
        zorder=3,
    )
    ax.axhline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.4, zorder=1)
    ax.set_title("Whole-body vertical weighting Wk (ISO 8041-1)", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Weighting factor [dB]")
    ax.set_xlim(0.4, 100.0)
    ax.set_ylim(-40.0, 5.0)
    from matplotlib.ticker import NullFormatter

    ax.set_xticks([0.5, 1, 2, 5, 10, 20, 50, 100])
    # Explicit string labels install a FixedFormatter so the Spanish pass can
    # apply the decimal comma (a log-axis ScalarFormatter would not be caught).
    ax.set_xticklabels(["0.5", "1", "2", "5", "10", "20", "50", "100"])
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.set_axisbelow(True)
    plt.tight_layout()
    save_figure(output_dir, "vibration_weighting.png")
    plt.close()


def generate_weighted_acceleration(output_dir: str) -> None:
    """ISO 2631-1: measured seat spectrum weighted to a_w (Eq. (9))."""
    print("Generating weighted_acceleration.png...")
    from phonometry import vibration

    # A measured vertical seat-pan acceleration spectrum (r.m.s. per one-third
    # octave, m/s^2) from a vehicle seat: energy concentrated in the 2-8 Hz
    # whole-body range. Weighting it with Wk gives the health-relevant a_w.
    freqs = np.array(
        [
            1.0,
            1.25,
            1.6,
            2.0,
            2.5,
            3.15,
            4.0,
            5.0,
            6.3,
            8.0,
            10.0,
            12.5,
            16.0,
            20.0,
            25.0,
            31.5,
            40.0,
            63.0,
            80.0,
        ]
    )
    accel = np.array(
        [
            0.18,
            0.24,
            0.33,
            0.46,
            0.52,
            0.55,
            0.48,
            0.39,
            0.31,
            0.26,
            0.21,
            0.17,
            0.13,
            0.10,
            0.078,
            0.060,
            0.045,
            0.028,
            0.020,
        ]
    )
    result = vibration.weighted_acceleration(accel, freqs, "Wk")

    positions = np.arange(freqs.size, dtype=float)
    width = 0.4
    _fig, ax = plt.subplots(figsize=(10.5, 6.3))
    ax.bar(
        positions - width / 2,
        result.band_accelerations,
        width,
        color="#9e9e9e",
        edgecolor=COLOR_FG,
        linewidth=0.5,
        label="Unweighted $a_i$",
        zorder=2,
    )
    ax.bar(
        positions + width / 2,
        result.weighted,
        width,
        color=COLOR_PRIMARY,
        edgecolor=COLOR_FG,
        linewidth=0.5,
        label="Weighted $W_i\\,a_i$ (Wk)",
        zorder=3,
    )
    ax.set_xticks(positions)
    ax.set_xticklabels([f"{f:g}" for f in freqs], rotation=45, ha="right")
    ax.set_title(
        rf"Weighted seat acceleration (ISO 2631-1)  $a_\mathrm{{w}}$ = "
        f"{result.overall:.3f} m/s²",
        pad=12,
    )
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("r.m.s. acceleration [m/s²]")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    save_figure(output_dir, "weighted_acceleration.png")
    plt.close()


def generate_daily_vibration_exposure(output_dir: str) -> None:
    """ISO 5349 + Directive 2002/44/EC: A(8) vs the EAV/ELV thresholds."""
    print("Generating daily_vibration_exposure.png...")
    from phonometry import vibration

    # A forestry worker's day across three chain-saw tasks (the ISO 5349-2
    # Annex E.3 worked example): each task's a_hv and duration give a partial
    # exposure A_i(8); they combine to A(8) = 3,6 m/s^2, assessed against the
    # hand-arm action (2,5) and limit (5,0) values of Directive 2002/44/EC.
    result = vibration.daily_vibration_exposure(
        [4.6, 6.0, 3.6],
        [2 * 3600.0, 1 * 3600.0, 2 * 3600.0],
        kind="hav",
        labels=["brush-saw", "felling", "stripping"],
    )

    labels = [*result.labels, "$A(8)$"]
    values = [*result.partials.tolist(), result.a8]
    positions = np.arange(len(values), dtype=float)
    colors = ["#9e9e9e"] * result.partials.size + [COLOR_PRIMARY]
    _fig, ax = plt.subplots(figsize=(9.5, 6.3))
    ax.bar(
        positions,
        values,
        width=0.62,
        color=colors,
        edgecolor=COLOR_FG,
        linewidth=0.6,
        zorder=3,
    )
    eav = result.assessment.action_value
    elv = result.assessment.limit_value
    ax.axhline(
        eav,
        color=COLOR_TERTIARY,
        linestyle="--",
        linewidth=1.6,
        label=f"EAV = {eav:g} m/s²",
        zorder=2,
    )
    ax.axhline(
        elv,
        color=COLOR_SECONDARY,
        linestyle="--",
        linewidth=1.6,
        label=f"ELV = {elv:g} m/s²",
        zorder=2,
    )
    ax.set_xticks(positions)
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_ylabel("Daily exposure $A(8)$ [m/s²]")
    ax.set_ylim(0.0, elv * 1.2)
    ax.set_title(
        f"Hand-arm daily exposure (ISO 5349 / 2002-44-EC)  $A(8)$ = "
        f"{result.a8:.2f} m/s²",
        pad=12,
    )
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    plt.tight_layout()
    save_figure(output_dir, "daily_vibration_exposure.png")
    plt.close()


def generate_multiple_shock(output_dir: str) -> None:
    """ISO 2631-5: seat-to-spine transmissibility and the injury probability."""
    print("Generating multiple_shock.png...")
    from phonometry import vibration
    from phonometry.vibration.human.multiple_shock import (
        MZ_MALE,
        RISK_THRESHOLDS_MALE,
    )

    _fig, (ax_h, ax_r) = plt.subplots(1, 2, figsize=(12.5, 5.4))

    # --- Left: seat-to-spine transmissibility |H(f)| (Formula 1). ---
    freq = np.logspace(np.log10(0.5), np.log10(80.0), 400)
    ax_h.plot(
        freq,
        np.abs(vibration.seat_to_spine_transfer(freq)),
        color=COLOR_PRIMARY,
        label=r"$|H(f)|$",
    )
    ax_h.axhline(1.0, color=COLOR_GRID, linestyle="--", alpha=0.7)
    ax_h.set_xscale("log")
    ax_h.set_xlabel("Frequency [Hz]")
    ax_h.set_ylabel("Transmissibility  seat → spine")
    ax_h.set_title("Seat-to-spine transfer function", pad=10)
    ax_h.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_h.set_axisbelow(True)
    format_frequency_axis(ax_h, float(freq[0]), float(freq[-1]))
    ax_h.legend(loc="upper right")

    # --- Right: injury probability Pi(R) with the Annex C male example. ---
    grid = np.linspace(0.0, 3.0, 300)
    sexes: tuple[tuple[Literal["male", "female"], str], ...] = (
        ("male", COLOR_PRIMARY),
        ("female", COLOR_SECONDARY),
    )
    for sex, colour in sexes:
        prob = 100.0 * vibration.injury_probability(grid, sex=sex)
        ax_r.plot(grid, prob, color=colour, label=f"{sex}")
    # The worked example: five 40 m/s2 peaks, 82 kg male -> R = 1.22.
    sd = vibration.compression_dose(vibration.dose_from_peaks([40.0] * 5), mz=MZ_MALE)
    r_male = vibration.injury_risk(
        sd, start_age=20, years=20, days_per_year=120, sex="male"
    )
    for level, r_val in zip((10, 50, 90), RISK_THRESHOLDS_MALE, strict=True):
        ax_r.axhline(level, color="#7f7f7f", linestyle=":", lw=0.8)
        ax_r.plot([r_val, r_val], [0.0, level], color="#7f7f7f", linestyle=":", lw=0.8)
    ax_r.scatter(
        [r_male],
        [100.0 * vibration.injury_probability(r_male, sex="male")],
        color=COLOR_TERTIARY,
        marker="*",
        s=160,
        zorder=4,
        label=f"Example  $R$ = {r_male:.2f}",
    )
    ax_r.set_xlabel("Stress variable $R$")
    ax_r.set_ylabel("Probability of lumbar injury [%]")
    ax_r.set_title("Injury probability (Annex C)", pad=10)
    ax_r.set_xlim(left=0.0)
    ax_r.set_ylim(0.0, 100.0)
    ax_r.grid(color=COLOR_GRID, linestyle="-", alpha=0.4)
    ax_r.set_axisbelow(True)
    ax_r.legend(loc="lower right")

    plt.tight_layout()
    save_figure(output_dir, "multiple_shock.png")
    plt.close()


def generate_vibration_weighting_family(output_dir: str) -> None:
    """ISO 8041-1: all nine human-vibration weightings on one frequency axis."""
    print("Generating vibration_weighting_family.png...")
    from phonometry import vibration

    # One evaluation per weighting over the band the *family* spans: Wf is a
    # sub-hertz weighting and Wh is still within 40 dB of its peak at 1 kHz,
    # so the axis has to run from 0,05 Hz to 1,5 kHz for the nine curves to be
    # comparable at all. Grouped by the part of the family each belongs to.
    freqs = np.geomspace(0.05, 1500.0, 900)
    curves = (
        ("Wk", "Wk — seat surface, vertical (ISO 2631-1)", COLOR_PRIMARY, "-", 2.4),
        ("Wd", "Wd — seat surface, horizontal", COLOR_PRIMARY, "--", 1.6),
        ("Wc", "Wc — backrest, x", COLOR_PRIMARY, (0, (1, 1, 3, 1)), 1.6),
        ("We", "We — rotational (per rad)", "#9467bd", "-.", 1.6),
        ("Wj", "Wj — recumbent, under the head", "#9467bd", ":", 1.8),
        ("Wm", "Wm — building occupants, all axes (ISO 2631-2)", "#ff7f0e", "-", 1.8),
        ("Wb", "Wb — rail ride comfort, vertical (ISO 2631-4)", "#ff7f0e", "--", 1.6),
        ("Wf", "Wf — motion sickness, vertical", COLOR_TERTIARY, "-", 2.0),
        (
            "Wh",
            "Wh — hand-transmitted, all three axes (ISO 5349-1)",
            COLOR_SECONDARY,
            "-",
            2.4,
        ),
    )

    _fig, ax = plt.subplots(figsize=(11, 6.8))
    for name, label, colour, style, width in curves:
        factors = np.asarray(vibration.weighting_factors(name, freqs))
        db = 20.0 * np.log10(np.maximum(factors, 1e-9))
        ax.semilogx(
            freqs,
            db,
            color=colour,
            linestyle=style,
            linewidth=width,
            label=label,
            zorder=3,
        )
    ax.axhline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.4, zorder=1)

    # The band each part of the family is tabulated over, drawn above the
    # curves: ISO 2631-1 Table 3 (0,5-80 Hz, band-limited 0,4/100 Hz),
    # its Wf column (0,1-0,5 Hz, band-limited 0,08/0,63 Hz) and ISO 5349-1
    # Table A.2 (6,3-1250 Hz, band-limited 6,31/1258,9 Hz). Each carries the
    # frequency its label is centred on, which is the middle of the band for
    # the first two and is not for the third: the hand-arm range begins under
    # the whole-body band drawn above it, so a chip centred on 6,3-1250 Hz
    # sits on the 80 Hz end of that bar and hides it, leaving the bar
    # apparently stopping in mid-air at the very frequency the label beside it
    # states. Centred over 80-1250 Hz -- the part of the range that is the
    # hand-arm band's alone -- the chip clears that end by a decade and still
    # stands over what it names.
    bands = (
        (0.1, 0.5, 11.0, COLOR_TERTIARY, "Wf: 0.1–0.5 Hz", np.sqrt(0.1 * 0.5)),
        (0.5, 80.0, 7.5, COLOR_PRIMARY, "whole body: 0.5–80 Hz", np.sqrt(0.5 * 80.0)),
        (
            6.3,
            1250.0,
            4.0,
            COLOR_SECONDARY,
            "hand-arm Wh: 6.3–1250 Hz",
            np.sqrt(80.0 * 1250.0),
        ),
    )
    for low, high, level, colour, label, centre in bands:
        ax.plot(
            [low, high],
            [level, level],
            color=colour,
            linewidth=3.0,
            solid_capstyle="butt",
            zorder=4,
        )
        for edge in (low, high):
            ax.plot(
                [edge, edge],
                [level - 1.1, level + 1.1],
                color=colour,
                linewidth=1.4,
                zorder=4,
            )
        ax.text(
            centre,
            level + 1.6,
            label,
            fontsize=8.5,
            color=colour,
            ha="center",
            va="bottom",
            zorder=6,
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": COLOR_PANEL,
                "edgecolor": COLOR_GRID,
            },
        )

    ax.annotate(
        "Wf peaks at 0.17 Hz:\nmotion sickness is sub-hertz",
        xy=(0.150, -1.6),
        xytext=(0.052, 2.6),
        fontsize=9,
        color=COLOR_TERTIARY,
        ha="left",
        arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_TERTIARY},
    )
    ax.annotate(
        "Wd peaks 2.5 octaves below Wk:\nthe body is more compliant\n"
        "horizontally at low frequency",
        xy=(1.09, 0.1),
        xytext=(2.1, -46.0),
        fontsize=9,
        color=COLOR_PRIMARY,
        ha="left",
        arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_PRIMARY},
    )

    ax.set_title("The nine human-vibration weightings (ISO 8041-1 Table 3)", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Weighting factor [dB]")
    ax.set_xlim(0.05, 1500.0)
    ax.set_ylim(-70.0, 16.0)
    from matplotlib.ticker import NullFormatter

    ax.set_xticks([0.05, 0.1, 0.5, 1, 5, 10, 50, 100, 500, 1250])
    ax.set_xticklabels(
        ["0.05", "0.1", "0.5", "1", "5", "10", "50", "100", "500", "1250"]
    )
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", fontsize=8.5, ncol=2, framealpha=0.9)
    plt.tight_layout()
    save_figure(output_dir, "vibration_weighting_family.png")
    plt.close()


def _shock_ride_record(fs: float, duration: float) -> np.ndarray:
    """A synthetic seated off-road record: 4.5 Hz ride plus five impacts.

    The record the dose-measure figure and the guide's snippet both run on.
    Its crest factor is above 9 and both ISO 2631-1 clause 6.3.3 ratios are
    exceeded, which is the case the basic r.m.s. method cannot describe.
    """
    time = np.arange(int(duration * fs)) / fs
    rng = np.random.default_rng(3)
    signal = 0.35 * np.sin(2.0 * np.pi * 4.5 * time) + 0.10 * rng.standard_normal(
        time.size
    )
    for start, amplitude in (
        (2.6, 9.0),
        (6.1, 14.0),
        (9.4, 6.0),
        (13.8, 18.0),
        (17.2, 11.0),
    ):
        mask = time >= start
        signal[mask] += (
            amplitude
            * np.exp(-28.0 * (time[mask] - start))
            * np.sin(2.0 * np.pi * 8.0 * (time[mask] - start))
        )
    return signal


def generate_shock_dose_measures(output_dir: str) -> None:
    """ISO 2631-1: one shock-laden record read by r.m.s., MTVV and VDV."""
    print("Generating shock_dose_measures.png...")
    from phonometry import vibration

    fs, duration = 200.0, 20.0
    time = np.arange(int(duration * fs)) / fs
    raw = _shock_ride_record(fs, duration)
    weighted = np.asarray(vibration.apply_weighting(raw, fs, name="Wk"))
    a_w = float(np.sqrt(np.mean(weighted**2)))
    running = np.asarray(vibration.running_rms(weighted, fs, integration_time=1.0))
    mtvv = float(vibration.mtvv(weighted, fs))
    vdv = float(vibration.vibration_dose_value(weighted, fs))
    # The running fourth-power accumulation whose end point is the VDV, drawn
    # against a_w t^(1/4), the value the basic method would predict for it.
    fourth = np.cumsum(weighted**4) / fs
    running_vdv = fourth**0.25
    basic_vdv = a_w * time**0.25

    _fig, (ax_t, ax_r, ax_v) = plt.subplots(
        3,
        1,
        sharex=True,
        figsize=(11, 9.2),
        gridspec_kw={"height_ratios": (1.15, 1.0, 1.0)},
    )

    ax_t.plot(
        time,
        raw,
        color=COLOR_MUTED,
        linewidth=0.7,
        label="$a_z(t)$, unweighted",
        zorder=2,
    )
    ax_t.plot(
        time,
        weighted,
        color=COLOR_PRIMARY,
        linewidth=1.0,
        label=r"$a_\mathrm{w}(t)$, Wk-weighted",
        zorder=3,
    )
    ax_t.set_ylabel("acceleration [m/s²]")
    ax_t.set_title(
        "(a)  A seated off-road record: 4.5 Hz ride plus five impacts",
        fontsize=10,
        loc="left",
        pad=6,
    )
    ax_t.legend(loc="upper right", fontsize=9)

    ax_r.plot(
        time,
        running,
        color=COLOR_PRIMARY,
        linewidth=1.4,
        label="running r.m.s., 1 s (Eq. (3))",
        zorder=3,
    )
    ax_r.axhline(
        a_w,
        color=COLOR_MUTED,
        linestyle="--",
        linewidth=1.6,
        label=rf"$a_\mathrm{{w}}$ = {a_w:.2f} m/s² (Eq. (1))",
        zorder=2,
    )
    peak_index = int(np.argmax(running))
    ax_r.plot(
        [time[peak_index]],
        [mtvv],
        marker="o",
        markersize=7,
        color=COLOR_SECONDARY,
        zorder=4,
        label=f"MTVV = {mtvv:.2f} m/s² (Eq. (4))",
    )
    ax_r.annotate(
        rf"$\mathrm{{MTVV}}/a_\mathrm{{w}}$ = {mtvv / a_w:.2f}"
        "   (> 1.5)",
        xy=(time[peak_index], mtvv),
        xytext=(time[peak_index] - 6.5, mtvv * 0.78),
        fontsize=9,
        color=COLOR_SECONDARY,
        arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_SECONDARY},
    )
    ax_r.set_ylabel("r.m.s. [m/s²]")
    ax_r.set_title(
        "(b)  The 1 s running r.m.s., whose maximum is the MTVV",
        fontsize=10,
        loc="left",
        pad=6,
    )
    ax_r.legend(loc="upper left", fontsize=9)

    ax_v.plot(
        time,
        running_vdv,
        color=COLOR_PRIMARY,
        linewidth=1.6,
        label=r"$\left(\int_0^t a_\mathrm{w}^4\,dt\right)^{1/4}$",
        zorder=3,
    )
    ax_v.plot(
        time,
        basic_vdv,
        color=COLOR_MUTED,
        linestyle="--",
        linewidth=1.6,
        label=r"$a_\mathrm{w}\,t^{1/4}$ (the basic method)",
        zorder=2,
    )
    ax_v.plot(
        [duration],
        [vdv],
        marker="o",
        markersize=7,
        color=COLOR_SECONDARY,
        zorder=4,
        label=f"VDV = {vdv:.2f} m/s$^{{1.75}}$ (Eq. (5))",
    )
    ax_v.annotate(
        rf"$\mathrm{{VDV}}/(a_\mathrm{{w}} T^{{1/4}})$ = "
        f"{vdv / (a_w * duration**0.25):.2f}   (> 1.75)",
        xy=(duration, vdv),
        xytext=(7.0, vdv * 0.55),
        fontsize=9,
        color=COLOR_SECONDARY,
        arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_SECONDARY},
    )
    ax_v.set_ylabel("dose [m/s$^{1.75}$]")
    ax_v.set_xlabel("Time [s]")
    ax_v.set_title(
        "(c)  The fourth-power accumulation, whose end point is the VDV",
        fontsize=10,
        loc="left",
        pad=6,
    )
    ax_v.legend(loc="upper left", fontsize=9)

    for axis in (ax_t, ax_r, ax_v):
        axis.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
        axis.set_axisbelow(True)
    ax_v.set_xlim(0.0, duration)
    plt.tight_layout()
    save_figure(output_dir, "shock_dose_measures.png")
    plt.close()


def generate_hav_vwf_lifetime(output_dir: str) -> None:
    """ISO 5349-1 Annex C: years to a 10 % prevalence of white finger."""
    print("Generating hav_vwf_lifetime.png...")
    from phonometry import vibration

    # Formula (C.1) over the exposure range a workplace assessment produces,
    # with the four tabulated points it interpolates between (Table C.1) and
    # the Directive's two thresholds read off the same curve.
    a8 = np.geomspace(1.0, 40.0, 400)
    years = np.array([vibration.hav_vwf_lifetime_years(float(v)) for v in a8])
    table_a8 = np.array([26.0, 14.0, 7.0, 3.7])
    table_years = np.array([1.0, 2.0, 4.0, 8.0])

    _fig, ax = plt.subplots(figsize=(10, 6.4))
    # Outside 1-8 years the curve is an extrapolation of Table C.1, not an
    # interpolation of it: shade what the table does not underwrite.
    wash = theme_fill(COLOR_MUTED, ax)
    ax.axhspan(0.3, 1.0, color=wash, zorder=0)
    ax.axhspan(8.0, 60.0, color=wash, zorder=0)
    ax.text(
        1.15,
        22.0,
        "extrapolation beyond Table C.1",
        fontsize=9,
        color=COLOR_FG,
        alpha=0.75,
        va="center",
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    # High in the band rather than through the middle of it: the two threshold
    # labels stand on the floor of the same band, just right of their rules,
    # and the Spanish note is long enough to be printed straight over the
    # first of them. The band is the note's to move inside; the labels are
    # pinned to their lines.
    ax.text(
        1.15,
        0.80,
        "extrapolation beyond Table C.1",
        fontsize=9,
        color=COLOR_FG,
        alpha=0.75,
        va="center",
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    ax.loglog(
        a8,
        years,
        color=COLOR_PRIMARY,
        linewidth=2.0,
        zorder=3,
        label=r"$D_\mathrm{y} = 31.8\,A(8)^{-1.06}$ (Eq. (C.1))",
    )
    ax.loglog(
        table_a8,
        table_years,
        linestyle="none",
        marker="o",
        markersize=8,
        color=COLOR_SECONDARY,
        zorder=4,
        label="Table C.1: 26 / 14 / 7 / 3.7 m/s²",
    )
    for value, label, colour in (
        (2.5, "EAV 2.5", COLOR_TERTIARY),
        (5.0, "ELV 5.0", COLOR_SECONDARY),
    ):
        ax.axvline(value, color=colour, linestyle="--", linewidth=1.5, zorder=2)
        ax.text(
            value * 1.04,
            0.36,
            f"{label} m/s²\n{vibration.hav_vwf_lifetime_years(value):.1f} years",
            fontsize=9,
            color=colour,
            va="bottom",
        )

    ax.set_title(
        "Group-mean years to a 10 % prevalence of vibration white "
        "finger (ISO 5349-1 Annex C)",
        pad=12,
    )
    ax.set_xlabel("Daily exposure $A(8)$ [m/s²]")
    ax.set_ylabel(r"Exposure duration $D_\mathrm{y}$ [years]")
    ax.set_xlim(1.0, 40.0)
    ax.set_ylim(0.3, 60.0)
    ax.set_xticks([1, 2, 2.5, 5, 10, 20, 40])
    ax.set_xticklabels(["1", "2", "2.5", "5", "10", "20", "40"])
    ax.set_yticks([0.5, 1, 2, 4, 8, 20, 50])
    ax.set_yticklabels(["0.5", "1", "2", "4", "8", "20", "50"])
    from matplotlib.ticker import NullFormatter

    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(which="major", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    save_figure(output_dir, "hav_vwf_lifetime.png")
    plt.close()


def _positive_peak_indices(response: np.ndarray) -> np.ndarray:
    """Index of the maximum of every positive run between zero crossings."""
    positive = response > 0.0
    edges = np.flatnonzero(np.diff(positive.astype(np.int8)))
    starts = np.r_[0, edges + 1]
    stops = np.r_[edges + 1, response.size]
    return np.array(
        [
            int(a + np.argmax(response[a:b]))
            for a, b in zip(starts, stops, strict=True)
            if positive[a]
        ]
    )


def generate_spinal_response_peaks(output_dir: str) -> None:
    """ISO 2631-5 clause 5: the spinal response in time and its counted peaks."""
    print("Generating spinal_response_peaks.png...")
    from phonometry import vibration

    # A synthetic off-road seat record: a 3.6 Hz ride oscillation, four
    # impacts of clearly different severity, and a 0.4 s free fall before the
    # largest one (the case clause 5.1.3 NOTE 2 sets the 0,01 Hz high pass
    # for). 256 samples per second is the rate clause 5.1.2 asks for.
    fs, duration = 256.0, 8.0
    time = np.arange(int(duration * fs)) / fs
    rng = np.random.default_rng(11)
    seat = 1.5 * np.sin(2.0 * np.pi * 3.6 * time) + 0.45 * rng.standard_normal(
        time.size
    )
    for start, amplitude in ((1.15, 26.0), (3.05, 8.0), (5.60, 55.0), (6.95, 15.0)):
        mask = time >= start
        seat[mask] += (
            amplitude
            * np.exp(-20.0 * (time[mask] - start))
            * np.sin(2.0 * np.pi * 5.5 * (time[mask] - start))
        )
    free_fall = (time >= 5.18) & (time < 5.58)
    seat[free_fall] = -9.81

    response = np.asarray(vibration.spinal_response(seat, fs))
    peaks = np.asarray(vibration.response_peaks(response))
    indices = _positive_peak_indices(response)
    shares = 100.0 * peaks**6 / float(np.sum(peaks**6))
    dose = float(vibration.dose_from_peaks(peaks))

    _fig, (ax_t, ax_p) = plt.subplots(2, 1, sharex=True, figsize=(11, 7.6))

    ax_t.plot(
        time,
        seat,
        color=COLOR_MUTED,
        linewidth=0.9,
        label=r"$a_\mathrm{z}(t)$, conditioned seat acceleration",
        zorder=2,
    )
    ax_t.plot(
        time,
        response,
        color=COLOR_PRIMARY,
        linewidth=1.5,
        label=r"$A_\mathrm{z}(t)$, spinal response (Formula 2)",
        zorder=3,
    )
    ax_t.axhline(-9.81, color=COLOR_SECONDARY, linestyle=":", linewidth=1.2, zorder=1)
    ax_t.annotate(
        "0.4 s of free fall at $-1\\,g$:\nthe 0.01 Hz high pass of 5.1.3 keeps it",
        xy=(5.30, -9.81),
        xytext=(2.25, 13.0),
        fontsize=9,
        color=COLOR_SECONDARY,
        arrowprops={"arrowstyle": "->", "lw": 0.9, "color": COLOR_SECONDARY},
    )
    ax_t.set_ylabel("acceleration [m/s²]")
    ax_t.set_title(
        "(a)  The seat-to-spine filter turns an impact into a ringing response",
        fontsize=10,
        loc="left",
        pad=6,
    )
    ax_t.legend(loc="upper left", fontsize=9)

    ax_p.plot(time, response, color=COLOR_PRIMARY, linewidth=1.2, zorder=2)
    ax_p.axhline(0.0, color=COLOR_FG, linewidth=0.9, alpha=0.6, zorder=1)
    ax_p.plot(
        time[indices],
        peaks,
        linestyle="none",
        marker="o",
        markersize=5,
        color=COLOR_SECONDARY,
        zorder=4,
        label=rf"{peaks.size} counted positive peaks $A_{{\mathrm{{z}},i}}$",
    )
    largest = int(np.argmax(peaks))
    ax_p.axhline(
        peaks[largest] / 3.0,
        color=COLOR_TERTIARY,
        linestyle="--",
        linewidth=1.4,
        zorder=3,
        label="a third of the largest peak: below this, no contribution",
    )
    for rank in np.argsort(peaks)[::-1][:3]:
        ax_p.annotate(
            f"{peaks[rank]:.1f}  ({shares[rank]:.1f} %)",
            xy=(time[indices[rank]], peaks[rank]),
            xytext=(time[indices[rank]] + 0.18, peaks[rank] + 1.6),
            fontsize=9,
            color=COLOR_FG,
        )
    ax_p.set_ylabel(r"$A_\mathrm{z}$ [m/s²]")
    ax_p.set_xlabel("Time [s]")
    ax_p.set_title(
        f"(b)  Each peak's share of $\\sum A_{{\\mathrm{{z}},i}}^6$ — "
        f"dose $D_\\mathrm{{z}}$ = "
        f"{dose:.1f} m/s²",
        fontsize=10,
        loc="left",
        pad=6,
    )
    ax_p.legend(loc="upper left", fontsize=9)

    for axis in (ax_t, ax_p):
        axis.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
        axis.set_axisbelow(True)
    ax_p.set_xlim(0.0, duration)
    plt.tight_layout()
    save_figure(output_dir, "spinal_response_peaks.png")
    plt.close()


def generate_junction_kij_thickness(output_dir: str) -> None:
    """Wave-approach Kij versus the plate thickness ratio (Hopkins Eq. 5.116)."""
    print("Generating junction_kij_thickness...")
    from phonometry import vibration

    # Concrete plates (cL = 3200 m/s, rho = 2400 kg/m3): plate 1 fixed at
    # 100 mm, plate 2 swept from 50 mm to 400 mm.
    h1, cl, rho = 0.1, 3200.0, 2400.0
    ratios = np.linspace(0.5, 4.0, 36)
    curves: dict[str, list[float]] = {
        "X corner": [],
        "X straight": [],
        "T-junction (1) corner": [],
        "L corner": [],
    }
    for ratio in ratios:
        h2 = h1 * float(ratio)
        res_x = vibration.junction_transmission("X", h1, cl, rho * h1, h2, cl, rho * h2)
        assert res_x.straight_average is not None
        curves["X corner"].append(res_x.corner_reduction_index)
        curves["X straight"].append(
            float(
                vibration.wave_vibration_reduction_index(
                    res_x.straight_average, res_x.critical_frequency2
                )
            )
        )
        res_t = vibration.junction_transmission(
            "T1", h1, cl, rho * h1, h2, cl, rho * h2
        )
        curves["T-junction (1) corner"].append(res_t.corner_reduction_index)
        res_l = vibration.junction_transmission("L", h1, cl, rho * h1, h2, cl, rho * h2)
        curves["L corner"].append(res_l.corner_reduction_index)

    _fig, ax = plt.subplots(figsize=(10, 6.2))
    styles = [
        ("-", COLOR_PRIMARY),
        ("--", COLOR_PRIMARY),
        ("-", COLOR_SECONDARY),
        ("-", COLOR_TERTIARY),
    ]
    for (label, values), (ls, color) in zip(curves.items(), styles, strict=True):
        ax.plot(ratios, values, ls, color=color, linewidth=2.0, label=label)
    # The identical-plate X-junction: Kij = 10 log10 12 + 5 log10(fc2/1000).
    res_eq = vibration.junction_transmission("X", h1, cl, rho * h1, h1, cl, rho * h1)
    ax.scatter(
        [1.0],
        [res_eq.corner_reduction_index],
        color=COLOR_FG,
        s=70,
        zorder=6,
        label=r"identical plates ($\tau = 1/12$)",
    )

    ax.set_xticks(np.arange(0.5, 4.01, 0.5))
    ax.set_xticklabels([f"{v:.1f}" for v in np.arange(0.5, 4.01, 0.5)])
    ax.set_xlabel("Thickness ratio $h_2/h_1$")
    ax.set_ylabel("Vibration reduction index $K_{ij}$ [dB]")
    ax.set_title("Wave-Approach Junction $K_{ij}$ (Hopkins Eq. 5.116)", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", fontsize=9)

    info = [
        r"$K_{ij} = 10\,\log_{10}(1/\bar{\tau}) + 5\,\log_{10}(f_{\mathrm{c}2}/1000)$",
        "concrete, plate 1 fixed at 100 mm",
    ]
    ax.text(
        0.985,
        0.03,
        "\n".join(info),
        transform=ax.transAxes,
        va="bottom",
        ha="right",
        fontsize=10,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    plt.tight_layout()
    save_figure(output_dir, "junction_kij_thickness.svg")
    plt.close()


def generate_bearing_fault_envelope(output_dir: str) -> None:
    """Predicted bearing fault lines over a measured envelope spectrum."""
    print("Generating bearing_fault_envelope...")
    from phonometry import signals, vibration

    # Norton problem 8.5 geometry: fifteen rollers, 34 mm pitch diameter,
    # 6 mm rollers, 12.96 deg contact angle, 2000 r/min.
    faults = vibration.bearing_fault_frequencies(
        2000.0, 15, 6.0, 34.0, contact_angle_deg=12.96
    )
    bpfo, fs_shaft = faults["BPFO"], faults.shaft_rate

    # A spalled outer race: one impact per BPFO period ringing a 3 kHz housing
    # resonance, load-modulated once per revolution, buried in broadband noise.
    fs, seconds = 20000.0, 2.0
    t = np.arange(int(fs * seconds)) / fs
    impacts = np.zeros_like(t)
    for k in range(int(seconds * bpfo)):
        idx = round(k / bpfo * fs)
        if idx < impacts.size:
            impacts[idx] = 1.0 + 0.35 * np.cos(2.0 * np.pi * fs_shaft * idx / fs)
    tau = np.arange(int(0.004 * fs)) / fs
    ring = np.exp(-tau / 6.0e-4) * np.sin(2.0 * np.pi * 3000.0 * tau)
    x = np.convolve(impacts, ring)[: t.size] * 0.6
    x += 0.35 * np.sin(2.0 * np.pi * fs_shaft * t)  # residual unbalance
    x += signals.noise_signal(fs, seconds, color="white", rms=0.25, seed=17)

    res = signals.envelope_spectrum(x, fs, band=(2000.0, 4000.0))
    keep = res.frequencies <= 4.6 * bpfo
    freq, amp = res.frequencies[keep], res.amplitude[keep]

    _fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.plot(
        freq,
        amp,
        color=COLOR_PRIMARY,
        linewidth=1.1,
        label="envelope spectrum of the 2-4 kHz band",
    )
    top = float(amp.max())
    for order in range(1, 5):
        line = order * bpfo
        ax.axvline(
            line,
            color=COLOR_SECONDARY,
            linestyle="--",
            linewidth=1.2,
            alpha=0.85,
            zorder=2,
            label="predicted BPFO and harmonics" if order == 1 else None,
        )
        ax.annotate(
            f"{order}×BPFO" if order > 1 else "BPFO",
            xy=(line, 1.02 * top),
            xytext=(3, 0),
            textcoords="offset points",
            rotation=90,
            fontsize=8.5,
            color=COLOR_SECONDARY,
            ha="left",
            va="bottom",
        )
    for name, colour in (("BPFI", COLOR_TERTIARY), ("BSF", "#9467bd")):
        ax.axvline(
            faults[name],
            color=colour,
            linestyle=":",
            linewidth=1.3,
            alpha=0.9,
            zorder=2,
            label=f"predicted {name}",
        )
    ax.axvline(
        fs_shaft,
        color=COLOR_FG,
        linestyle="-.",
        linewidth=1.0,
        alpha=0.6,
        zorder=2,
        label="shaft rate",
    )

    ax.set_xlim(0.0, 4.6 * bpfo)
    ax.set_ylim(0.0, 1.55 * top)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Envelope amplitude")
    ax.set_title("Bearing Fault Lines on a Measured Envelope Spectrum", pad=12)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=8, ncol=2)

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        r"15 rollers, $D$ = 34 mm, $d$ = 6 mm, $\varphi$ = 12.96°, 2000 r/min",
        f"BPFO = {bpfo:.0f} Hz, BPFI = {faults['BPFI']:.0f} Hz",
        "the envelope lines fall on BPFO, not on BPFI: outer-race spall",
    ]
    ax.text(
        0.985,
        0.47,
        "\n".join(info),
        transform=ax.transAxes,
        va="top",
        ha="right",
        fontsize=9,
        color=COLOR_FG,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": panel, "edgecolor": COLOR_GRID},
    )
    plt.tight_layout()
    save_figure(output_dir, "bearing_fault_envelope.svg")
    plt.close()


def generate_experimental_sea_clf(output_dir: str) -> None:
    """Measured and predicted coupling loss factors of a plate junction."""
    print("Generating experimental_sea_clf...")
    from phonometry import vibration
    from phonometry.vibration.structural.point_mobility import plate_bending_wave_speed

    rho, nu, young = 2700.0, 0.33, 7.1e10
    c_l = math.sqrt(young / (rho * (1.0 - nu**2)))
    bands = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0])

    # Two aluminium plates at right angles: 3 mm x 2.5 m x 1.2 m coupled to
    # 5.5 mm x 2.0 m x 1.2 m along the 1.2 m edge (Norton problem 6.13).
    h1, h2, area1, length = 0.003, 0.0055, 2.5 * 1.2, 1.2
    tau = vibration.right_angle_transmission_coefficient(
        h1, h2, density1=rho, density2=rho, wave_speed1=c_l, wave_speed2=c_l
    )
    c_b = plate_bending_wave_speed(
        bands, vibration.plate_bending_stiffness(young, h1, nu), rho * h1
    )
    welded = np.array(
        [
            float(vibration.coupling_loss_factor(tau, 2.0 * c, length, f, area1))
            for c, f in zip(c_b, bands, strict=True)
        ]
    )
    bolted = vibration.point_connection_coupling_loss_factor(
        bands,
        12,
        thickness1=h1,
        thickness2=h2,
        surface_density1=rho * h1,
        surface_density2=rho * h2,
        wave_speed1=c_l,
        wave_speed2=c_l,
        plate_area1=area1,
    )

    # The satellite platform and cylinder of Norton problem 6.10, inverted from
    # its measured energies in the 500 Hz octave.
    t_p, t_c, radius, cyl_len = 0.005, 0.003, 0.75, 2.0
    area_c = 2.0 * math.pi * radius * cyl_len
    area_p = 3.5 * 3.0 - math.pi * radius**2
    sea = vibration.power_injection_clf(
        500.0,
        rho * t_p * area_p * 0.0272**2,
        rho * t_c * area_c * 0.0132**2,
        4.4e-3,
        2.4e-3,
        vibration.flat_plate_modal_density(area_p, t_p, c_l),
        float(
            vibration.cylindrical_shell_modal_density(500.0, area_c, t_c, radius, c_l)[
                0
            ]
        ),
    )

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.6))
    ax = axes[0]
    x = _band_index_axis(ax, bands, fontsize=9)
    ax.semilogy(
        x,
        welded,
        "-o",
        color=COLOR_PRIMARY,
        linewidth=2.0,
        markersize=5,
        label=r"welded line junction $\eta_{12}$",
    )
    ax.semilogy(
        x,
        bolted,
        "-s",
        color=COLOR_SECONDARY,
        linewidth=2.0,
        markersize=5,
        label=r"12 bolts, point connections $\eta_{12}$",
    )
    ax.axhline(
        1.0e-2,
        color=COLOR_FG,
        linestyle="--",
        linewidth=1.2,
        alpha=0.7,
        label=r"internal loss factor $\eta_1$",
    )
    ax.set_ylabel("Coupling loss factor")
    ax.set_title("Predicted: Weld Against Bolts", pad=10)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, which="both")
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)

    ax = axes[1]
    labels = [r"$\eta_1$", r"$\eta_2$", r"$\eta_{12}$", r"$\eta_{21}$"]
    values = [
        4.4e-3,
        2.4e-3,
        float(sea.coupling_loss_factor12[0]),
        float(sea.coupling_loss_factor21[0]),
    ]
    # COLOR_MUTED, not COLOR_GRID: this is a de-emphasised *bar*, and the
    # grid colour is tuned to disappear into the page it is drawn on.
    colours = [COLOR_FG, COLOR_MUTED, COLOR_PRIMARY, COLOR_SECONDARY]
    ax.bar(labels, values, color=colours, edgecolor=COLOR_FG, linewidth=0.8)
    ax.set_yscale("log")
    # Headroom for the note that runs along the top: at a decade of it the
    # note reached down to the tallest bar and printed over the value written
    # above it, which in Spanish left the reader "4,40" and no exponent. The
    # note spans the full width of the panel and has nowhere else to go.
    ax.set_ylim(1.0e-4, 2.0e-2)
    ax.set_ylabel("Loss factor")
    ax.set_title("Measured: Power Injection, 500 Hz Octave", pad=10)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, axis="y", which="both")
    ax.set_axisbelow(True)
    for label, value in zip(labels, values, strict=True):
        ax.annotate(
            _sci_math(value),
            xy=(label, value),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            fontsize=8.5,
            color=COLOR_FG,
        )

    panel = "#f0f2f5" if COLOR_FG == "black" else "#1c2128"
    info = [
        "platform driven, cylinder driven only through the joints",
        f"input power = {float(sea.input_power[0]):.2f} W",
        r"coupling stays well below the damping: valid SEA",
    ]
    ax.text(
        0.98,
        0.97,
        "\n".join(info),
        transform=ax.transAxes,
        va="top",
        ha="right",
        fontsize=9,
        color=COLOR_FG,
        bbox={"boxstyle": "round,pad=0.5", "facecolor": panel, "edgecolor": COLOR_GRID},
    )
    fig.suptitle("Coupling Loss Factors: Prediction and Power Injection", fontsize=13)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    save_figure(output_dir, "experimental_sea_clf.svg")
    plt.close()


def generate_mobility_result_lines(output_dir: str) -> None:
    """ISO 7626 driving-point mobility with its stiffness and mass lines."""
    print("Generating mobility_result_lines...")
    from phonometry import vibration

    m, k, c = 2.0, 8000.0, 5.0
    f = np.logspace(np.log10(0.5), np.log10(200.0), 400)
    res = vibration.sdof_mobility_result(f, mass=m, stiffness=k, damping=c)
    w = 2.0 * np.pi * f
    f0 = float(res.frequencies[int(np.argmax(res.magnitude))])

    fig, (ax, low) = plt.subplots(
        2, 1, figsize=(10, 7.6), sharex=True, gridspec_kw={"height_ratios": [1.6, 1.0]}
    )
    ax.loglog(
        f,
        res.magnitude,
        color=COLOR_PRIMARY,
        linewidth=2.2,
        label="driving-point $|Y(f)|$",
    )
    ax.loglog(
        f,
        w / k,
        ":",
        color=COLOR_SECONDARY,
        linewidth=1.6,
        label=r"stiffness line $\omega/k$",
    )
    ax.loglog(
        f,
        1.0 / (w * m),
        ":",
        color=COLOR_TERTIARY,
        linewidth=1.6,
        label=r"mass line $1/(\omega m)$",
    )
    ax.axhline(1.0 / c, color=COLOR_GRID, linestyle="--", linewidth=1.2)
    ax.scatter(
        [f0],
        [1.0 / c],
        color=COLOR_FG,
        s=60,
        zorder=6,
        label="peak $|Y| = 1/c$ (damping)",
    )

    ax.set_xlim(float(f[0]), float(f[-1]))
    ax.set_ylim(2e-4, 0.6)
    ax.set_ylabel("Mobility $|Y|$ [m/(N·s)]")
    ax.set_title("Reading a Driving-Point Mobility (ISO 7626-1)", pad=12)
    ax.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", fontsize=9, ncol=2)

    info = [
        r"below $f_0$: stiffness-controlled, $|Y| \sim \omega/k$",
        r"above $f_0$: mass-controlled, $|Y| \sim 1/(\omega m)$",
        rf"$f_0$ = {f0:.1f} Hz,  $1/c$ = {1.0 / c:.2f} m/(N·s)",
    ]
    ax.text(
        0.015,
        0.97,
        "\n".join(info),
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=10,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    # The phase is the other half of the reading, and the one the +-90 deg
    # bound of ISO 7626-2 A.4 turns into a validity check on the setup.
    phase = np.degrees(np.asarray(res.phase, dtype=np.float64))
    low.axhspan(-90.0, 90.0, color=theme_fill(COLOR_PRIMARY, low), zorder=0)
    low.semilogx(f, phase, color=COLOR_PRIMARY, linewidth=2.2, label="phase of $Y(f)$")
    low.axhline(0.0, color=COLOR_GRID, linestyle="--", linewidth=1.2)
    low.scatter(
        [f0],
        [0.0],
        color=COLOR_FG,
        s=55,
        zorder=6,
        label="0° at the resonance: $Y$ is real, $|Y| = 1/c$",
    )
    low.set_ylim(-115.0, 115.0)
    low.set_yticks([-90, -45, 0, 45, 90])
    low.set_ylabel("Phase [degrees]")
    low.set_xlabel(LABEL_FREQ_HZ)
    format_frequency_axis(low, float(f[0]), float(f[-1]))
    low.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    low.set_axisbelow(True)
    low.legend(loc="lower left", fontsize=9)
    low.text(
        0.985,
        0.93,
        "a driving-point FRF never leaves ±90°\n(ISO 7626-2, A.4)",
        transform=low.transAxes,
        va="top",
        ha="right",
        fontsize=9.5,
        color=COLOR_FG,
    )
    fig.align_ylabels()
    plt.tight_layout()
    save_figure(output_dir, "mobility_result_lines.svg")


class _LineSpectrum:
    """A synthesised narrow-band spectrum for a ``FaultFrequencyResult`` overlay.

    ``FaultFrequencyResult.plot(spectrum=…)`` accepts anything exposing
    ``frequencies`` and ``amplitude``; the fault families of Norton Section 8.4
    are recognised by the *pattern* of their lines, so the panels below place
    Gaussian lines at the frequencies the library itself predicts and let the
    result draw its own prediction on top.
    """

    def __init__(self, freq: np.ndarray, floor: float = 0.004) -> None:
        self.frequencies = freq
        rng = np.random.default_rng(11)
        self.amplitude = floor * (0.6 + rng.random(freq.size))

    def add(self, centre: float, height: float, width: float = 2.2) -> None:
        self.amplitude = self.amplitude + height * np.exp(
            -0.5 * ((self.frequencies - centre) / width) ** 2
        )


#: One size for the four reading blocks of ``machine_fault_families``. Half a
#: point below the usual note size: every block stands in the room between two
#: of its panel's dashed lines, and the Spanish readings are the wide ones.
_NOTE_PT = 8.5


def _relabel_spectrum(ax: Axes, title: str) -> None:
    """Say what the drawn curve is: these panels are ordinary spectra.

    ``FaultFrequencyResult.plot`` labels its curve "envelope spectrum",
    which is true of the bearing route and false of the gear, motor and fan
    families drawn here, so the label, the y axis and the title are set to
    what the panel actually shows. The panel's own legend goes with them: the
    four panels draw the same curve and the same colour per family, so one key
    at the foot of the figure says all of it, and none of the four upper-right
    corners -- where the line names are -- has a box standing in it.
    """
    curve = ax.get_lines()[0]
    curve.set_label("vibration spectrum")
    ax.set_ylabel("Spectrum amplitude")
    ax.set_title(title, pad=10, fontsize=11)
    legend = ax.get_legend()
    if legend is not None:
        legend.remove()


def generate_machine_fault_families(output_dir: str) -> None:
    """The three fault families of Norton 8.4 as patterns, not as numbers."""
    print("Generating machine_fault_families...")
    from phonometry import vibration

    # Wide panels: the three gear clusters sit 100 Hz wide on a 2400 Hz axis
    # and the fan's four lines cut its axis into narrow columns, so the room
    # between them is what every annotation block has to fit in.
    fig, axes = plt.subplots(2, 2, figsize=(13.6, 8.8))

    # --- (a) and (b): the same gear pair with two different faults ----------
    gear = vibration.gear_mesh_frequencies(1500.0, 28, harmonics=3, sidebands=2)
    shaft = gear.shaft_rate  # 25 Hz
    gmf = gear["GMF"]  # 700 Hz
    cases = (
        (
            "Localised fault: one chipped tooth",
            (1.0, 0.40, 0.16),
            (0.13, 0.09),
            axes[0][0],
        ),
        ("Distributed wear: every tooth", (1.0, 0.78, 0.62), (0.46, 0.33), axes[0][1]),
    )
    for title, harm, side, ax in cases:
        freq = np.linspace(0.0, 2400.0, 4800)
        spec = _LineSpectrum(freq)
        for order in range(1, 4):  # shaft orders
            spec.add(order * shaft, 0.05 / order)
        for k, height in enumerate(harm, start=1):
            spec.add(k * gmf, height)
            for order, ratio in enumerate(side, start=1):
                spec.add(k * gmf - order * shaft, height * ratio)
                spec.add(k * gmf + order * shaft, height * ratio)
        gear.within(1.0, 2400.0).plot(spectrum=spec, ax=ax)
        _relabel_spectrum(ax, title)
        # The block goes below the shaft end of the axis, the only stretch
        # wide enough for it: the three mesh clusters carry their dashed
        # lines the full height of the panel, and the block used to be read
        # through the 2xGMF group's five of them.
        ax.annotate(
            "sidebands at\n$\\pm f_\\mathrm{s}$ = 25 Hz:\n"
            + (
                "low and flat"
                if "Localised" in title
                else "tall groups, and the\nhigher harmonics lift"
            ),
            xy=(gmf - 2.0 * shaft, 0.16 if "Localised" in title else 0.42),
            xytext=(0.025, 0.76),
            textcoords="axes fraction",
            va="top",
            ha="left",
            fontsize=_NOTE_PT,
            color=COLOR_FG,
            arrowprops={"arrowstyle": "->", "color": COLOR_MUTED},
        )

    # --- (c): the motor family, three decades of amplitude ------------------
    ax = axes[1][0]
    motor = vibration.induction_motor_frequencies(3600.0, 6, 60, slip=0.0)
    freq = np.linspace(0.0, 3900.0, 7800)
    spec = _LineSpectrum(freq, floor=2.0e-5)
    for name, height in (("1x", 1.0), ("2x", 0.30), ("2fe", 0.06)):
        spec.add(motor[name], height, width=3.0)
    spec.add(motor["fsh"], 1.6e-3, width=3.0)  # rotor slot
    for sign in (-1.0, 1.0):  # ± shaft rate
        spec.add(motor["fsh"] + sign * motor["1x"], 5.5e-4, width=3.0)
    motor.plot(spectrum=spec, ax=ax)
    _relabel_spectrum(ax, "Induction motor: 1x, 2x, 2fe and the rotor-slot family")
    ax.set_yscale("log")
    # Five decades and a little: the 1x line is the tallest thing in the panel
    # and the top of the axis is where its name is written.
    ax.set_ylim(1.0e-5, 5.0)
    ax.annotate(
        "rotor-slot harmonic\nwith $\\pm f_\\mathrm{s}$ sidebands:\n"
        "the spacing is the diagnosis",
        xy=(motor["fsh"], 1.6e-3),
        xytext=(1700.0, 0.02),
        fontsize=_NOTE_PT,
        color=COLOR_FG,
        arrowprops={"arrowstyle": "->", "color": COLOR_MUTED},
    )

    # --- (d): the ducted fan, blade rate against its lobe patterns ----------
    ax = axes[1][1]
    fan = vibration.blade_pass_frequencies(3500.0, 6, harmonics=1, n_vanes=4)
    freq = np.linspace(0.0, 420.0, 3200)
    spec = _LineSpectrum(freq, floor=0.006)
    spec.add(fan.shaft_rate, 0.10, width=0.8)
    spec.add(fan["BPF"], 1.0, width=0.8)
    spec.add(fan["lobe n=1 m=2"], 0.62, width=0.8)
    spec.add(fan["lobe n=1 m=10"], 0.07, width=0.8)
    fan.plot(spectrum=spec, ax=ax)
    _relabel_spectrum(ax, "Ducted fan: the blade rate and its rotating lobe patterns")
    # Each block is centred in the column between two of the fan's lines: the
    # first between the shaft and the two-lobe pattern, the second between that
    # and the blade rate, which the longer Spanish reading used to run over.
    ax.annotate(
        "$m_\\mathrm{L}$ = 10 turns at 35 Hz,\nbelow the shaft: weak",
        xy=(fan["lobe n=1 m=10"], 0.12),
        xytext=(66.0, 0.62),
        va="top",
        ha="left",
        fontsize=_NOTE_PT,
        color=COLOR_FG,
        arrowprops={"arrowstyle": "->", "color": COLOR_MUTED},
    )
    ax.annotate(
        "$m_\\mathrm{L}$ = 2 turns at 175 Hz,\n3x the shaft speed: strong",
        xy=(fan["lobe n=1 m=2"], 0.70),
        xytext=(189.0, 0.96),
        va="top",
        ha="left",
        fontsize=_NOTE_PT,
        color=COLOR_FG,
        arrowprops={"arrowstyle": "->", "color": COLOR_MUTED},
    )

    # One key for the four panels, at the foot of the figure: they draw the
    # same curve and give each family the same colour, so a box per panel
    # would only repeat itself in the corner where the line names are.
    keyed: dict[str, Artist] = {}
    for panel in axes.flat:
        handles, names = panel.get_legend_handles_labels()
        for name, handle in zip(names, handles, strict=True):
            keyed.setdefault(name, handle)
    fig.legend(
        list(keyed.values()),
        list(keyed),
        loc="lower center",
        ncol=len(keyed),
        fontsize=9.5,
        frameon=False,
    )

    fig.suptitle("Fault Families Are Recognised by Their Pattern", fontsize=13)
    plt.tight_layout(rect=(0.0, 0.035, 1.0, 0.96))
    save_figure(output_dir, "machine_fault_families.svg")
    plt.close()


def generate_envelope_chain_steps(output_dir: str) -> None:
    """The three steps of the envelope route, on one bearing record."""
    print("Generating envelope_chain_steps...")
    from scipy import signal as sp_signal

    from phonometry import signals, vibration

    faults = vibration.bearing_fault_frequencies(
        2000.0, 15, 6.0, 34.0, contact_angle_deg=12.96
    )
    bpfo, fs_shaft = faults["BPFO"], faults.shaft_rate

    # The record of the opening figure: impacts at BPFO ringing a 3 kHz
    # housing resonance, load-modulated once per revolution, under noise.
    fs, seconds = 20000.0, 2.0
    t = np.arange(int(fs * seconds)) / fs
    impacts = np.zeros_like(t)
    for k in range(int(seconds * bpfo)):
        idx = round(k / bpfo * fs)
        if idx < impacts.size:
            impacts[idx] = 1.0 + 0.35 * np.cos(2.0 * np.pi * fs_shaft * idx / fs)
    tau = np.arange(int(0.004 * fs)) / fs
    ring = np.exp(-tau / 6.0e-4) * np.sin(2.0 * np.pi * 3000.0 * tau)
    x = np.convolve(impacts, ring)[: t.size] * 0.6
    x += 0.35 * np.sin(2.0 * np.pi * fs_shaft * t)
    x += signals.noise_signal(fs, seconds, color="white", rms=0.25, seed=17)

    band = (2000.0, 4000.0)
    res = signals.envelope_spectrum(x, fs, band=band)
    sos = sp_signal.butter(4, band, btype="bandpass", fs=fs, output="sos")
    narrow = np.asarray(sp_signal.sosfiltfilt(sos, x), dtype=np.float64)

    window = slice(0, int(0.05 * fs))  # the first 50 ms
    fig, axes = plt.subplots(4, 1, figsize=(10.5, 10.4))

    axes[0].plot(t[window] * 1e3, x[window], color=COLOR_MUTED, linewidth=0.9)
    axes[0].set_ylabel("raw record")
    axes[0].set_title(
        "1. As recorded: noise and unbalance, no visible impacts", fontsize=11, pad=8
    )

    axes[1].plot(t[window] * 1e3, narrow[window], color=COLOR_PRIMARY, linewidth=0.9)
    axes[1].set_ylabel("2-4 kHz band")
    axes[1].set_title(
        "2. Band-passed on the 3 kHz housing resonance: the impact train",
        fontsize=11,
        pad=8,
    )
    top = float(np.max(np.abs(narrow[window])))
    axes[1].set_ylim(-1.35 * top, 1.35 * top)
    for k in range(11):  # one impact per BPFO period
        axes[1].axvline(
            1e3 * k / bpfo, color=COLOR_MUTED, linewidth=0.8, alpha=0.55, zorder=0
        )
    t0 = 1e3 / bpfo * 3.0
    axes[1].annotate(
        "",
        xy=(t0, 1.06 * top),
        xytext=(t0 + 1e3 / bpfo, 1.06 * top),
        arrowprops={"arrowstyle": "<->", "color": COLOR_SECONDARY},
    )
    axes[1].text(
        t0 + 0.5e3 / bpfo,
        1.14 * top,
        rf"$1/\mathrm{{BPFO}}$ = {1e3 / bpfo:.2f} ms",
        ha="center",
        fontsize=9,
        color=COLOR_SECONDARY,
    )

    axes[2].plot(
        res.times[window] * 1e3,
        res.envelope[window],
        color=COLOR_SECONDARY,
        linewidth=1.0,
    )
    axes[2].set_ylabel("envelope")
    axes[2].set_xlabel("Time [ms]")
    axes[2].set_title("3. Hilbert envelope: one pulse per impact", fontsize=11, pad=8)

    keep = res.frequencies <= 4.6 * bpfo
    axes[3].plot(
        res.frequencies[keep], res.amplitude[keep], color=COLOR_PRIMARY, linewidth=1.1
    )
    peak = float(np.max(res.amplitude[keep]))
    for order in range(1, 5):
        axes[3].axvline(
            order * bpfo,
            color=COLOR_SECONDARY,
            linestyle="--",
            linewidth=1.2,
            alpha=0.85,
            label="predicted BPFO and harmonics" if order == 1 else None,
        )
    for name, colour in (("BPFI", COLOR_TERTIARY), ("BSF", "#9467bd")):
        axes[3].axvline(
            faults[name],
            color=colour,
            linestyle=":",
            linewidth=1.3,
            alpha=0.9,
            label=f"predicted {name}",
        )
    axes[3].set_xlim(0.0, 4.6 * bpfo)
    axes[3].set_ylim(0.0, 1.35 * peak)
    axes[3].set_xlabel(LABEL_FREQ_HZ)
    axes[3].set_ylabel("envelope spectrum")
    axes[3].set_title(
        "4. Its spectrum: the period has become a line at BPFO", fontsize=11, pad=8
    )
    axes[3].legend(loc="upper right", fontsize=8.5)

    for ax in axes:
        ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
        ax.set_axisbelow(True)
    fig.suptitle("What Each Step of the Envelope Route Does to the Signal", fontsize=13)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.965))
    save_figure(output_dir, "envelope_chain_steps.svg")
    plt.close()


def generate_infinite_mobilities(output_dir: str) -> None:
    """The point mobilities a real structure has, beside the SDOF reference."""
    print("Generating infinite_mobilities...")
    from phonometry import vibration

    freq = np.logspace(np.log10(0.5), np.log10(2000.0), 600)

    # A 140 mm concrete slab (E = 30 GPa, nu = 0.2, rho = 2400 kg/m3), a
    # 100 x 200 mm steel beam, and a 2 cm2 steel strut in longitudinal motion.
    b_plate = vibration.plate_bending_stiffness(3.0e10, 0.14, 0.2)
    plate = vibration.infinite_plate_point_mobility(freq, b_plate, 336.0)
    b_beam = 2.1e11 * 0.1 * 0.2**3 / 12.0
    beam = vibration.infinite_beam_point_mobility(freq, b_beam, 7800.0 * 0.02)
    rod = vibration.longitudinal_rod_mobility(7800.0, 5100.0, 2.0e-4)
    sdof = vibration.sdof_mobility_result(freq, mass=2.0, stiffness=8000.0, damping=5.0)

    fig, (ax, low) = plt.subplots(
        2, 1, figsize=(10, 7.6), sharex=True, gridspec_kw={"height_ratios": [1.6, 1.0]}
    )
    curves = (
        (
            sdof.magnitude,
            np.degrees(np.asarray(sdof.phase)),
            COLOR_MUTED,
            "SDOF resonator (section 2)",
            "--",
        ),
        (
            plate.magnitude,
            np.degrees(np.asarray(plate.phase)),
            COLOR_PRIMARY,
            "infinite plate, 140 mm concrete",
            "-",
        ),
        (
            beam.magnitude,
            np.degrees(np.asarray(beam.phase)),
            COLOR_SECONDARY,
            "infinite beam, 100 × 200 mm steel",
            "-",
        ),
        (
            np.full_like(freq, rod),
            np.zeros_like(freq),
            COLOR_TERTIARY,
            "steel strut, longitudinal",
            ":",
        ),
    )
    for mag, phase, colour, label, style in curves:
        ax.loglog(freq, mag, style, color=colour, linewidth=2.0, label=label)
        low.semilogx(freq, phase, style, color=colour, linewidth=2.0)

    ax.set_ylim(5.0e-7, 0.6)
    ax.set_ylabel("Mobility $|Y|$ [m/(N·s)]")
    ax.set_title("Point Mobilities of Infinite Structures (Cremer Table 5.1)", pad=12)
    ax.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", fontsize=9)
    info = [
        r"plate:  $Y = 1/(8\sqrt{B^{\prime} m^{\prime\prime}})$, real and flat",
        r"beam:   $Y = (1-\mathrm{j})/(4 m^{\prime} c_\mathrm{B})$, $\propto f^{-1/2}$",
        r"rod:    $Y = 1/(\rho c_\mathrm{L} S)$, real and flat",
        f"plate $|Y|$ = {_sci_math(float(plate.magnitude[0]))} m/(N·s)",
    ]
    ax.text(
        0.985,
        0.97,
        "\n".join(info),
        transform=ax.transAxes,
        va="top",
        ha="right",
        fontsize=10,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    low.axhline(0.0, color=COLOR_GRID, linestyle="--", linewidth=1.1)
    low.axhline(-45.0, color=COLOR_GRID, linestyle=":", linewidth=1.1)
    low.set_ylim(-115.0, 115.0)
    low.set_yticks([-90, -45, 0, 45, 90])
    low.set_ylabel("Phase [degrees]")
    low.set_xlabel(LABEL_FREQ_HZ)
    low.set_xlim(float(freq[0]), float(freq[-1]))
    format_frequency_axis(low, float(freq[0]), float(freq[-1]))
    low.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    low.set_axisbelow(True)
    fig.align_ylabels()
    plt.tight_layout()
    save_figure(output_dir, "infinite_mobilities.svg")
    plt.close()


def generate_mobility_random_error(output_dir: str) -> None:
    """ISO 7626-2 Annex A: how many averages the 5 % criterion costs."""
    print("Generating mobility_random_error...")
    from phonometry import vibration

    averages = np.unique(np.round(np.logspace(np.log10(2.0), np.log10(1000.0), 260)))
    _fig, ax = plt.subplots(figsize=(10, 6.2))
    palette = (COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TERTIARY, COLOR_MUTED, COLOR_FG)
    for coherence, colour in zip((0.5, 0.7, 0.8, 0.9, 0.95), palette, strict=True):
        error = np.array(
            [
                float(vibration.random_error_percent(coherence, int(n)))
                for n in np.round(averages)
            ],
            dtype=np.float64,
        )
        ax.loglog(
            averages,
            error,
            color=colour,
            linewidth=2.0,
            label=rf"$\gamma^2 = {coherence}$",
        )
        needed = (1.0 - coherence) / (2.0 * coherence * 0.05**2)
        ax.scatter([needed], [5.0], color=colour, s=36, zorder=6)
        ax.annotate(
            f"{needed:.0f}",
            xy=(needed, 5.0),
            xytext=(0, -14),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            color=colour,
        )
    ax.axhline(
        5.0,
        color=COLOR_FG,
        linestyle="--",
        linewidth=1.4,
        label="the Annex A criterion, 5 %",
    )
    ax.scatter(
        [75.0],
        [float(vibration.random_error_percent(0.8, 75))],
        marker="*",
        s=190,
        color=COLOR_FG,
        zorder=7,
        label=r"the standard's own example: $\gamma^2 = 0.8$, "
        "$n$ = 75 → 4.08 %",
    )

    ax.set_xlabel("Number of averaged spectra $n$")
    ax.set_ylabel(r"Normalized random error $\varepsilon$ [%]")
    ax.set_title(
        "How Many Averages the 5 % Criterion Costs (ISO 7626-2, Annex A)", pad=12
    )
    ax.set_xlim(2.0, 1000.0)
    ax.set_ylim(1.0, 60.0)
    ax.grid(which="both", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=9)
    ax.text(
        0.015,
        0.05,
        "the marked $n$ is what each coherence needs to reach "
        "5 %: 11 averages at 0.95, 200 at 0.5.\nFixing the measurement is "
        "cheaper than averaging through it.",
        transform=ax.transAxes,
        va="bottom",
        ha="left",
        fontsize=9.5,
        color=COLOR_FG,
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    plt.tight_layout()
    save_figure(output_dir, "mobility_random_error.svg")
    plt.close()


def generate_seat_vibration_test(output_dir: str) -> None:
    """ISO 10326-1: the SEAT factor of one test, and the correction of 10.2.3."""
    print("Generating seat_vibration_test...")
    from phonometry import vibration

    platform_runs = (1.02, 1.00, 0.99)
    seat_runs = (0.72, 0.70, 0.71)
    intended = 1.10
    test = vibration.seat_transmission(seat_runs, platform_runs)

    fig, (ax_runs, ax_fix) = plt.subplots(1, 2, figsize=(12.2, 5.4))

    runs = np.arange(len(platform_runs)) + 1.0
    width = 0.36
    ax_runs.bar(
        runs - width / 2,
        platform_runs,
        width=width,
        color=COLOR_PRIMARY,
        label="platform $a_\\mathrm{wP}$",
    )
    ax_runs.bar(
        runs + width / 2,
        seat_runs,
        width=width,
        color=COLOR_TERTIARY,
        label="seat $a_\\mathrm{wS}$",
    )
    for value, colour, name in (
        (test.platform_acceleration, COLOR_PRIMARY, "mean at the platform"),
        (test.seat_acceleration, COLOR_TERTIARY, "mean at the seat"),
    ):
        ax_runs.axhline(value, color=colour, linestyle="--", linewidth=1.2, label=name)
    ax_runs.annotate(
        "",
        xy=(3.6, test.seat_acceleration),
        xytext=(3.6, test.platform_acceleration),
        arrowprops={"arrowstyle": "<->", "color": COLOR_FG, "linewidth": 1.2},
    )
    ax_runs.text(
        3.66,
        0.5 * (test.seat_acceleration + test.platform_acceleration),
        f"SEAT = {test.seat_factor:.2f}",
        va="center",
        ha="left",
        fontsize=10,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.3",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    ax_runs.set_xticks(runs)
    ax_runs.set_xlim(0.4, 4.5)
    ax_runs.set_ylim(0.0, 1.28)
    ax_runs.set_xlabel("Test run")
    ax_runs.set_ylabel("Weighted r.m.s. acceleration (m/s²)")
    ax_runs.set_title("Simulated Input Vibration Test", pad=10)
    ax_runs.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, axis="y")
    ax_runs.set_axisbelow(True)
    ax_runs.legend(loc="upper left", fontsize=8.5)

    # Right: the correction of 10.2.3. The simulator delivered a little more
    # than it meant to, so the magnitude on the seat is scaled to the input
    # that was intended rather than to the one that arrived.
    corrected = test.corrected_acceleration(intended)
    bars = (
        ("delivered\n$a_\\mathrm{wP}$", test.platform_acceleration, COLOR_PRIMARY),
        ("intended\n$a^{*}_\\mathrm{wP}$", intended, COLOR_QUATERNARY),
        ("measured\n$a_\\mathrm{wS}$", test.seat_acceleration, COLOR_TERTIARY),
        ("corrected\n$a^{*}_\\mathrm{wS}$", corrected, COLOR_SECONDARY),
    )
    positions = np.arange(len(bars))
    ax_fix.bar(
        positions,
        [value for _, value, _ in bars],
        width=0.6,
        color=[colour for _, _, colour in bars],
    )
    for x, (_, value, _) in zip(positions, bars, strict=True):
        ax_fix.text(
            x,
            value + 0.02,
            f"{value:.2f}",
            va="bottom",
            ha="center",
            fontsize=9,
            color=COLOR_FG,
        )
    ax_fix.set_xticks(positions)
    ax_fix.set_xticklabels([label for label, _, _ in bars], fontsize=9)
    ax_fix.set_ylim(0.0, 1.35)
    ax_fix.set_ylabel("Weighted r.m.s. acceleration (m/s²)")
    ax_fix.set_title("Correcting to the Input That Was Intended", pad=10)
    ax_fix.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, axis="y")
    ax_fix.set_axisbelow(True)
    ax_fix.text(
        0.5,
        0.94,
        "$a^{*}_\\mathrm{wS} = \\mathrm{SEAT} \\cdot a^{*}_\\mathrm{wP}$",
        transform=ax_fix.transAxes,
        va="top",
        ha="center",
        fontsize=11,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    fig.suptitle("What a Seat Does to the Vibration Under It", fontsize=13)
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    save_figure(output_dir, "seat_vibration_test.svg")
    plt.close()


def generate_machine_vibration_zones(output_dir: str) -> None:
    """The four evaluation zones as a frequency-shaped velocity criterion."""
    print("Generating machine_vibration_zones...")
    from phonometry import vibration

    # ISO 20816-1 Formula (C.1) drawn for one machine: flat between the two
    # corners, constant displacement below and constant acceleration above.
    # The specific parts of the series set the corners; 10 Hz and 1 kHz are
    # the pair the older ISO 10816-3 used for most machines.
    f_x, f_y = 10.0, 1000.0
    v_a = 1.12
    freq = np.logspace(np.log10(2.0), np.log10(3000.0), 600)
    curves = [
        ("A", vibration.ZONE_LIMIT_FACTORS["A"], COLOR_ZONE_A),
        ("B", vibration.ZONE_LIMIT_FACTORS["B"], COLOR_ZONE_B),
        ("C", vibration.ZONE_LIMIT_FACTORS["C"], COLOR_ZONE_C),
    ]

    _fig, ax = plt.subplots(figsize=(10, 6.2))
    limits = {}
    for zone, factor, colour in curves:
        v = np.asarray(
            vibration.allowable_velocity(
                freq,
                constant_velocity_mm_s=v_a,
                zone_factor=factor,
                corner_low_hz=f_x,
                corner_high_hz=f_y,
            )
        )
        limits[zone] = v
        ax.plot(
            freq,
            v,
            color=colour,
            linewidth=1.8,
            label=f"limit of zone {zone} ($Z$ = {factor:g})",
        )

    floor = np.full_like(freq, 1.0e-3)
    ceiling = np.full_like(freq, 1.0e3)
    bands = (
        (floor, limits["A"], COLOR_ZONE_A, "zone A: newly commissioned"),
        (limits["A"], limits["B"], COLOR_ZONE_B, "zone B: unrestricted operation"),
        (limits["B"], limits["C"], COLOR_ZONE_C, "zone C: limited operation"),
        (limits["C"], ceiling, COLOR_ZONE_D, "zone D: damage"),
    )
    for lower, upper, colour, label in bands:
        ax.fill_between(
            freq, lower, upper, color=theme_fill(colour, ax), zorder=0, label=label
        )

    for corner, name in ((f_x, "$f_x$"), (f_y, "$f_y$")):
        ax.axvline(corner, color=COLOR_FG, linestyle="--", linewidth=1.0, alpha=0.55)
        # Over the shaded zone D, so the label needs a chip to stay readable.
        ax.annotate(
            name,
            xy=(corner, 0.72),
            xycoords=("data", "axes fraction"),
            ha="center",
            va="center",
            fontsize=10,
            color=COLOR_FG,
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": COLOR_PANEL,
                "edgecolor": COLOR_GRID,
            },
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(2.0, 3000.0)
    ax.set_ylim(0.012, 60.0)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Allowable r.m.s. velocity (mm/s)")
    ax.set_title("Evaluation Zones as a Frequency-Shaped Velocity Criterion", pad=12)
    format_frequency_axis(ax)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, which="both")
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", fontsize=8, ncol=2)

    info = [
        r"$v_\mathrm{rms} = v_A Z (f_z/f_x)^k (f_y/f_w)^m$, "
        r"$v_A$ = 1.12 mm/s, $k = m = 1$",
        "flat between the corners; constant displacement below, "
        "constant acceleration above",
        "the B and C limits fall within 3 % of the 2.8 and 7.1 rungs of "
        "the Table C.1 ladder",
    ]
    ax.text(
        0.015,
        0.035,
        "\n".join(info),
        transform=ax.transAxes,
        va="bottom",
        ha="left",
        fontsize=9,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    plt.tight_layout()
    save_figure(output_dir, "machine_vibration_zones.svg")
    plt.close()


def generate_structural_damage_guidelines(output_dir: str) -> None:
    """DIN 4150-3: what a building is allowed to be shaken by."""
    print("Generating structural_damage_guidelines...")
    from phonometry import vibration

    classes = (
        ("commercial", "commercial and industrial", COLOR_PRIMARY),
        ("residential", "dwellings", COLOR_TERTIARY),
        ("sensitive", "especially sensitive", COLOR_SECONDARY),
    )
    # The bar rows carry the same names as the curves, broken over two lines
    # so the tick labels stay inside the column they belong to.
    row_labels = ("commercial\nand industrial", "dwellings", "especially\nsensitive")
    fig = plt.figure(figsize=(12.6, 6.0))
    grid = fig.add_gridspec(2, 2, width_ratios=[1.35, 1.0], hspace=0.55, wspace=0.3)
    ax_curve = fig.add_subplot(grid[:, 0])
    ax_top = fig.add_subplot(grid[0, 1])
    ax_pipe = fig.add_subplot(grid[1, 1])

    # Left: Bild 1. The guideline at the foundation is constant to 10 Hz and
    # then rises, so the same building takes more of a fast wiggle than a slow
    # one. Sampled densely rather than at the four corners, because the point
    # is that a value inside a band is defined at all.
    freq = np.linspace(1.0, 100.0, 400)
    for name, label, colour in classes:
        values = np.asarray(vibration.guideline_velocity(name, freq))
        ax_curve.plot(freq, values, color=colour, linewidth=1.9, label=label)
        corners = np.asarray(vibration.FOUNDATION_FREQUENCIES_HZ)
        ax_curve.plot(
            corners,
            np.asarray(vibration.guideline_velocity(name, corners)),
            linestyle="none",
            marker="o",
            markersize=4.5,
            color=colour,
        )
    for edge in (10.0, 50.0):
        ax_curve.axvline(
            edge, color=COLOR_MUTED, linestyle="--", linewidth=1.0, alpha=0.7
        )
    ax_curve.fill_between(
        freq,
        0.0,
        np.asarray(vibration.guideline_velocity("sensitive", freq)),
        color=theme_fill(COLOR_SECONDARY, ax_curve),
        zorder=0,
        label="below every guideline value",
    )
    ax_curve.set_xlim(0.0, 100.0)
    ax_curve.set_ylim(0.0, 55.0)
    ax_curve.set_xlabel(LABEL_FREQ_HZ)
    ax_curve.set_ylabel("Peak velocity $v_i$ (mm/s)")
    ax_curve.set_title("At the Foundation, Short-Term Vibration", pad=10)
    ax_curve.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax_curve.set_axisbelow(True)
    ax_curve.legend(loc="upper left", fontsize=9)

    # Top right: the topmost floor plane, where the guideline stops depending
    # on frequency and long-term vibration is judged instead.
    y = np.arange(len(classes))
    short = [
        float(vibration.guideline_velocity(name, location="top_floor"))
        for name, _, _ in classes
    ]
    long = [
        float(
            vibration.guideline_velocity(
                name, location="top_floor", duration="long_term"
            )
        )
        for name, _, _ in classes
    ]
    _paired_bars(
        ax_top,
        y,
        short,
        long,
        list(row_labels),
        ("short-term vibration", "long-term vibration"),
    )
    ax_top.set_xlabel("Peak velocity $v_i$ (mm/s)")
    ax_top.set_title("In the Topmost Floor Plane, Horizontal", pad=10)

    # Bottom right: buried pipelines, judged on the pipe by its material,
    # with the long-term half the standard allows without further evidence.
    materials = (
        ("welded_steel", "welded steel"),
        ("concrete_or_flanged_metal", "concrete,\nflanged metal"),
        ("masonry_or_plastic", "masonry,\nplastic"),
    )
    pipe_short = [vibration.pipeline_guideline_velocity(name) for name, _ in materials]
    pipe_long = [
        vibration.pipeline_guideline_velocity(name, duration="long_term")
        for name, _ in materials
    ]
    _paired_bars(
        ax_pipe,
        np.arange(len(materials)),
        pipe_short,
        pipe_long,
        [label for _, label in materials],
        ("short-term vibration", "long-term vibration"),
    )
    ax_pipe.set_xlabel("Peak velocity $v_i$ (mm/s)")
    ax_pipe.set_title("On a Buried Pipeline", pad=10)

    fig.suptitle(
        "Guideline Values for the Effect of Vibration on Structures", fontsize=13
    )
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.955))
    save_figure(output_dir, "structural_damage_guidelines.svg")
    plt.close()


def generate_building_frequency_prediction(output_dir: str) -> None:
    """ISO 4866 Annex D: four predictors of one frequency, and their spread."""
    print("Generating building_frequency_prediction...")
    from phonometry import vibration

    # A building of ordinary proportions: four times as tall as it is wide,
    # which is what makes the three code forms comparable on one axis.
    aspect = 4.0
    heights = np.logspace(np.log10(6.0), np.log10(250.0), 300)
    fit = np.asarray(vibration.height_fundamental_frequency(heights))

    fig, (ax_fit, ax_spread) = plt.subplots(
        1, 2, figsize=(12.4, 5.6), gridspec_kw={"width_ratios": [1.25, 1.0]}
    )

    ax_fit.fill_between(
        heights,
        fit * (1.0 - vibration.EMPIRICAL_FREQUENCY_TOLERANCE),
        fit * (1.0 + vibration.EMPIRICAL_FREQUENCY_TOLERANCE),
        color=theme_fill(COLOR_PRIMARY, ax_fit),
        zorder=0,
        label="$\\pm$50 %, which D.3 calls not uncommon",
    )
    ax_fit.plot(
        heights, fit, color=COLOR_PRIMARY, linewidth=2.0, label="$f = 46/h$ (D.3)"
    )
    # (model, curve label, short label for the bar rows, colour, dash)
    forms = (
        ("height", "$T = k_1 h$ (D.1)", "$T = k_1 h$", COLOR_TERTIARY, "--"),
        (
            "height_width",
            "$T = k_2 h/\\sqrt{b}$ (D.2)",
            "$T = k_2 h/\\sqrt{b}$",
            COLOR_QUATERNARY,
            "-.",
        ),
        (
            "slenderness",
            "$T = k_3 (h/\\sqrt{b})\\sqrt{h/(h+b)}$ (D.3)",
            "$T = k_3 (h/\\sqrt{b})\\sqrt{h/(h+b)}$",
            COLOR_SECONDARY,
            ":",
        ),
    )
    for model, label, _short, colour, style in forms:
        # The height form is written on the height alone and refuses a width,
        # so the width goes only to the two forms that use one.
        if model == "height":
            values = np.array(
                [
                    vibration.fundamental_frequency(model, height_m=float(h))
                    for h in heights
                ]
            )
        else:
            values = np.array(
                [
                    vibration.fundamental_frequency(
                        model, height_m=float(h), width_m=float(h) / aspect
                    )
                    for h in heights
                ]
            )
        ax_fit.plot(
            heights, values, color=colour, linewidth=1.6, linestyle=style, label=label
        )
    ax_fit.set_xscale("log")
    ax_fit.set_yscale("log")
    ax_fit.set_xlabel("Building height $h$ (m)")
    ax_fit.set_ylabel("Fundamental frequency $f$ (Hz)")
    ax_fit.set_title("Four Predictors of One Frequency", pad=10)
    ax_fit.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, which="both")
    ax_fit.set_axisbelow(True)
    ax_fit.legend(loc="lower left", fontsize=8.5)

    # Right: what the choice of code costs, on one 60 m building 15 m wide.
    tall, wide = 60.0, 15.0
    rows = []
    for model, _label, short, colour, _style in forms:
        low, high = vibration.PERIOD_COEFFICIENT_RANGES[model]
        if model == "height":
            span = [
                vibration.fundamental_frequency(model, height_m=tall, coefficient=k)
                for k in (low, high)
            ]
        else:
            span = [
                vibration.fundamental_frequency(
                    model, height_m=tall, width_m=wide, coefficient=k
                )
                for k in (low, high)
            ]
        rows.append((short, min(span), max(span), colour))
    fitted = float(vibration.height_fundamental_frequency(tall))
    for index, (label, low, high, colour) in enumerate(rows):
        ax_spread.barh(
            index, high - low, left=low, height=0.42, color=colour, label=label
        )
        # Over a gridline, so the reading carries a chip of its own.
        ax_spread.text(
            high + 0.012,
            index,
            f"{low:.2f} to {high:.2f} Hz",
            va="center",
            ha="left",
            fontsize=8.5,
            color=COLOR_FG,
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": COLOR_PANEL,
                "edgecolor": COLOR_GRID,
            },
        )
    ax_spread.axvline(
        fitted,
        color=COLOR_PRIMARY,
        linewidth=1.6,
        label=f"$f = 46/h$: {fitted:.2f} Hz",
    )
    ax_spread.set_yticks(range(len(rows)))
    ax_spread.set_yticklabels([label for label, _, _, _ in rows], fontsize=9)
    ax_spread.invert_yaxis()
    ax_spread.set_xlim(0.0, 1.62)
    ax_spread.set_xlabel("Fundamental frequency $f$ (Hz)")
    ax_spread.set_title("What the Choice of Code Costs, on One Building", pad=10)
    ax_spread.grid(visible=False)
    ax_spread.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, axis="x")
    ax_spread.set_axisbelow(True)
    ax_spread.legend(loc="lower left", fontsize=8.5)

    fig.suptitle(
        "Empirical Fundamental Frequency of a Building (ISO 4866 Annex D)",
        fontsize=13,
    )
    plt.tight_layout(rect=(0.0, 0.0, 1.0, 0.95))
    save_figure(output_dir, "building_frequency_prediction.svg")
    plt.close()


def _paired_bars(
    ax: Axes,
    y: np.ndarray,
    first: list[float],
    second: list[float],
    labels: list[str],
    names: tuple[str, str],
) -> None:
    """Two horizontal bars per row, with the value written at the tip."""
    height = 0.36
    for offset, values, colour, name in (
        (height / 2, first, COLOR_PRIMARY, names[0]),
        (-height / 2, second, COLOR_QUATERNARY, names[1]),
    ):
        ax.barh(y + offset, values, height=height, color=colour, label=name)
        for row, value in zip(y + offset, values, strict=True):
            ax.text(
                value + 0.02 * max(first),
                row,
                f"{value:g}",
                va="center",
                ha="left",
                fontsize=8.5,
                color=COLOR_FG,
            )
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    # Room to the right for the value beside the longest bar and for the
    # legend, which is wider in Spanish than in English.
    ax.set_xlim(0.0, max(first) * 1.52)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, axis="x")
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=8.5)


def generate_machine_vector_change(output_dir: str) -> None:
    """The Annex D vector change: a magnitude that falls while the vibration grows."""
    print("Generating machine_vector_change...")
    from phonometry import vibration

    # ISO 20816-1 Annex D, D.2: the worked case the annex prints.
    result = vibration.vibration_vector_change(3.0, 40.0, 2.5, 180.0)
    _fig, ax = plt.subplots(figsize=(7.6, 7.0), subplot_kw={"projection": "polar"})
    result.plot(ax=ax, language=_LANG, unit="mm/s")
    plt.tight_layout()
    save_figure(output_dir, "machine_vector_change.svg")
    plt.close()


def generate_industrial_machine_zones(output_dir: str) -> None:
    """Tables A.1 and A.2, and the rule that decides when the two disagree."""
    print("Generating industrial_machine_zones...")
    from phonometry import vibration

    classes = (
        ("group_1", "rigid", "group 1\nrigid"),
        ("group_1", "flexible", "group 1\nflexible"),
        ("group_2", "rigid", "group 2\nrigid"),
        ("group_2", "flexible", "group 2\nflexible"),
    )
    # ISO 10816-3:2009, 5.2.3: a machine measured in both quantities takes the
    # more restrictive of the two gradings. This pair is the case that makes
    # the clause matter, on a group 2 machine on a rigid support.
    measured_um, measured_mm_s = 50.0, 2.0
    marked = 2

    panels = (
        (
            "velocity_mm_s",
            "R.m.s. velocity (mm/s)",
            13.0,
            measured_mm_s,
            "%.1f",
            "the marked machine reads 2.0 mm/s, which is zone B",
        ),
        (
            "displacement_um",
            "R.m.s. displacement (µm)",
            165.0,
            measured_um,
            "%.0f",
            "the same machine reads 50 µm, which is zone C,\n"
            "and the more restrictive of the two gradings applies",
        ),
    )
    zones = (
        ("A", COLOR_ZONE_A, "zone A: newly commissioned"),
        ("B", COLOR_ZONE_B, "zone B: unrestricted operation"),
        ("C", COLOR_ZONE_C, "zone C: limited operation"),
        ("D", COLOR_ZONE_D, "zone D: damage"),
    )
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 6.6))
    positions = np.arange(len(classes), dtype=float)

    for ax, panel in zip(axes, panels, strict=True):
        attribute, ylabel, ceiling, measured, fmt, note = panel
        for index, (group, support, _label) in enumerate(classes):
            limits = vibration.INDUSTRIAL_MACHINE_ZONES[group, support]
            a_b, b_c, c_d = getattr(limits, attribute).as_tuple
            edges = (0.0, a_b, b_c, c_d, ceiling)
            for (letter, colour, legend), lower, upper in zip(
                zones, edges[:-1], edges[1:], strict=True
            ):
                ax.bar(
                    positions[index],
                    upper - lower,
                    bottom=lower,
                    width=0.66,
                    color=theme_fill(colour, ax),
                    edgecolor=colour,
                    linewidth=1.1,
                    zorder=2,
                    label=legend if index == 0 and ax is axes[0] else None,
                )
                if index == 0:
                    ax.text(
                        positions[index],
                        0.5 * (lower + min(upper, ceiling)),
                        letter,
                        ha="center",
                        va="center",
                        fontsize=11,
                        color=COLOR_FG,
                        zorder=4,
                    )
            for boundary in (a_b, b_c, c_d):
                ax.text(
                    positions[index] + 0.36,
                    boundary,
                    fmt % boundary,
                    ha="left",
                    va="center",
                    fontsize=8,
                    color=COLOR_FG,
                    zorder=4,
                )

        ax.plot(
            [positions[marked] - 0.42, positions[marked] + 0.42],
            [measured, measured],
            color=COLOR_FG,
            linewidth=1.6,
            linestyle="--",
            zorder=5,
        )
        ax.plot(
            positions[marked],
            measured,
            marker="o",
            markersize=7,
            color=COLOR_FG,
            zorder=6,
        )
        # Over the shaded zone D, so the note needs a chip to stay readable.
        ax.text(
            0.015,
            0.975,
            note,
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=8.5,
            color=COLOR_FG,
            bbox={
                "boxstyle": "round,pad=0.32",
                "facecolor": COLOR_PANEL,
                "edgecolor": COLOR_GRID,
            },
            zorder=7,
        )
        ax.set_xticks(positions)
        ax.set_xticklabels([label for _g, _s, label in classes], fontsize=9)
        ax.set_xlim(-0.6, len(classes) - 0.15)
        ax.set_ylim(0.0, ceiling)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5)
        ax.set_axisbelow(True)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=4,
        fontsize=9,
        frameon=False,
        bbox_to_anchor=(0.5, 0.005),
    )
    fig.suptitle("Zone Boundaries for Industrial Machines, Stated Twice", y=0.975)
    plt.tight_layout(rect=(0.0, 0.055, 1.0, 0.96))
    save_figure(output_dir, "industrial_machine_zones.svg")
    plt.close()


def generate_machine_alarm_trip(output_dir: str) -> None:
    """ALARM from the baseline, TRIP from the zone, and the cap on both."""
    print("Generating machine_alarm_trip...")
    from phonometry import vibration

    # A group 2 machine on a rigid support, judged in velocity: the class the
    # 15 kW to 300 kW plant is full of.
    limits = vibration.INDUSTRIAL_MACHINE_ZONES["group_2", "rigid"].velocity_mm_s
    a_b, b_c, c_d = limits.as_tuple
    ceiling = 8.0
    baselines = (0.9, 2.9)

    _fig, ax = plt.subplots(figsize=(9.6, 6.0))
    bands = (
        (0.0, a_b, COLOR_ZONE_A, "A", "zone A: newly commissioned"),
        (a_b, b_c, COLOR_ZONE_B, "B", "zone B: unrestricted operation"),
        (b_c, c_d, COLOR_ZONE_C, "C", "zone C: limited operation"),
        (c_d, ceiling, COLOR_ZONE_D, "D", "zone D: damage"),
    )
    for lower, upper, colour, letter, legend in bands:
        ax.axhspan(lower, upper, color=theme_fill(colour, ax), zorder=0, label=legend)
        ax.text(
            0.012,
            0.5 * (lower + upper),
            letter,
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=11,
            color=COLOR_FG,
        )

    cap = vibration.OPERATIONAL_LIMIT_HEADROOM * b_c
    ax.axhline(
        cap,
        color=COLOR_FG,
        linestyle=":",
        linewidth=1.4,
        label="the cap on an ALARM: 1.25 times the upper limit of zone B",
    )
    trip = vibration.trip_limit(c_d)
    ax.axhline(
        trip,
        color=COLOR_SECONDARY,
        linestyle="-.",
        linewidth=1.6,
        label="TRIP: 1.25 times the upper limit of zone C",
    )

    positions = np.arange(len(baselines), dtype=float)
    for index, baseline in enumerate(baselines):
        alarm = vibration.alarm_limit(baseline, b_c)
        x = positions[index]
        ax.bar(
            x,
            baseline,
            width=0.34,
            color=theme_fill(COLOR_QUATERNARY, ax),
            edgecolor=COLOR_QUATERNARY,
            linewidth=1.2,
            zorder=3,
        )
        ax.annotate(
            "",
            xy=(x, alarm),
            xytext=(x, baseline),
            arrowprops={"arrowstyle": "->", "color": COLOR_FG, "linewidth": 1.4},
            zorder=4,
        )
        ax.plot(
            [x - 0.24, x + 0.24],
            [alarm, alarm],
            color=COLOR_FG,
            linewidth=2.0,
            zorder=5,
        )
        capped = alarm >= cap - 1.0e-9
        note = "ALARM (capped)" if capped else "ALARM"
        ax.text(
            x + 0.28,
            alarm,
            f"{note}: {alarm:.3g} mm/s",
            ha="left",
            va="bottom",
            fontsize=9,
            color=COLOR_FG,
            zorder=5,
        )
        ax.text(
            x,
            0.5 * baseline,
            f"baseline\n{baseline:.3g} mm/s",
            ha="center",
            va="center",
            fontsize=8.5,
            color=COLOR_FG,
            zorder=6,
        )

    for level, name, colour, x_frac, align in (
        (cap, "the cap", COLOR_FG, 0.30, "left"),
        (trip, "TRIP", COLOR_SECONDARY, 0.988, "right"),
    ):
        ax.annotate(
            f"{name}: {level:.3g} mm/s",
            xy=(x_frac, level),
            xycoords=("axes fraction", "data"),
            ha=align,
            va="bottom",
            fontsize=9,
            color=colour,
        )
    ax.set_xticks(positions)
    ax.set_xticklabels(
        [
            "a machine settled in zone A",
            "a machine that has drifted into zone C",
        ],
        fontsize=9,
    )
    ax.set_xlim(-0.6, len(baselines) + 0.55)
    ax.set_ylim(0.0, ceiling)
    ax.set_ylabel("R.m.s. velocity (mm/s)")
    ax.set_title("Setting an ALARM from the Baseline, and a TRIP from the Zone", pad=12)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="lower right", fontsize=8)

    info = [
        "ALARM = baseline + 25 % of the upper limit of zone B,",
        "and never more than 1.25 times that limit",
        "TRIP guards against damage, so it comes from the machine",
    ]
    ax.text(
        0.015,
        0.965,
        "\n".join(info),
        transform=ax.transAxes,
        va="top",
        ha="left",
        fontsize=8.5,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    plt.tight_layout()
    save_figure(output_dir, "machine_alarm_trip.svg")
    plt.close()


def generate_gear_unit_rating_curves(output_dir: str) -> None:
    """The two rating curves of ISO 20816-9 Annex A, one family each."""
    print("Generating gear_unit_rating_curves...")
    from phonometry import vibration

    palette = (
        COLOR_PRIMARY,
        COLOR_SECONDARY,
        COLOR_TERTIARY,
        COLOR_QUATERNARY,
        COLOR_MUTED,
    )
    styles = ("-", "--", "-.", ":", "-")
    _fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.6, 5.8))

    freq = np.logspace(np.log10(1.0), np.log10(2000.0), 500)
    for rating, colour, style in zip(
        sorted(vibration.GEAR_UNIT_ZONES["displacement"]), palette, styles, strict=True
    ):
        ax.loglog(
            freq,
            np.asarray(vibration.gear_shaft_displacement_limit(freq, rating=rating)),
            style,
            color=colour,
            lw=1.8,
            label=f"DR = {rating:g} µm",
        )
    corner = vibration.GEAR_DISPLACEMENT_CORNER_HZ
    ax.axvline(corner, color=COLOR_FG, linestyle="--", linewidth=1.0, alpha=0.55)
    ax.annotate(
        "50 Hz",
        xy=(corner, 0.06),
        xycoords=("data", "axes fraction"),
        ha="center",
        va="bottom",
        fontsize=9,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Peak-to-peak displacement (µm)")
    ax.set_title("Shaft Displacement: Flat, Then 10 dB per Decade", pad=10)
    format_frequency_axis(ax)
    ax.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, which="both")
    ax.set_axisbelow(True)
    ax.legend(loc="lower left", fontsize=8)

    freq2 = np.logspace(np.log10(3.0), np.log10(20000.0), 600)
    for rating, colour, style in zip(
        sorted(vibration.GEAR_UNIT_ZONES["velocity"]), palette, styles, strict=True
    ):
        ax2.loglog(
            freq2,
            np.asarray(vibration.gear_housing_velocity_limit(freq2, rating=rating)),
            style,
            color=colour,
            lw=1.8,
            label=f"VR = {rating:g} mm/s",
        )
    for corner in vibration.GEAR_VELOCITY_CORNERS_HZ:
        ax2.axvline(corner, color=COLOR_FG, linestyle="--", linewidth=1.0, alpha=0.55)
        ax2.annotate(
            f"{corner:g} Hz",
            xy=(corner, 0.06),
            xycoords=("data", "axes fraction"),
            ha="center",
            va="bottom",
            fontsize=9,
            color=COLOR_FG,
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": COLOR_PANEL,
                "edgecolor": COLOR_GRID,
            },
        )
    ax2.set_xlabel(LABEL_FREQ_HZ)
    ax2.set_ylabel("R.m.s. velocity (mm/s)")
    ax2.set_title("Housing Velocity: Formula (C.1) With Part 9's Corners", pad=10)
    ax2.set_ylim(0.4, 46.0)
    format_frequency_axis(ax2)
    ax2.grid(color=COLOR_GRID, linestyle="--", alpha=0.5, which="both")
    ax2.set_axisbelow(True)
    ax2.legend(loc="lower left", fontsize=8)
    ax2.text(
        0.985,
        0.965,
        "14 dB per decade outside both corners,\n"
        "which is $k = m = 0.7$ in Formula (C.1)",
        transform=ax2.transAxes,
        va="top",
        ha="right",
        fontsize=8.5,
        color=COLOR_FG,
        bbox={
            "boxstyle": "round,pad=0.32",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    plt.tight_layout()
    save_figure(output_dir, "gear_unit_rating_curves.svg")
    plt.close()


def generate_machine_vibration_trend(output_dir: str) -> None:
    """A year of monthly readings, graded in one call, and what catches it first."""
    print("Generating machine_vibration_trend...")
    from phonometry import vibration

    limits = vibration.INDUSTRIAL_MACHINE_ZONES["group_2", "rigid"].velocity_mm_s
    a_b, b_c, c_d = limits.as_tuple
    ceiling = 6.0
    # A group 2 machine on a rigid support, read once a month for a year. It
    # sits in zone A, drifts through B and ends in D: the walk Criterion II
    # exists to see before Criterion I does.
    months = np.arange(1, 13, dtype=float)
    readings = np.array(
        [0.62, 0.66, 0.61, 0.70, 0.94, 1.32, 1.55, 1.84, 2.26, 2.95, 4.10, 5.20]
    )
    graded = vibration.industrial_machine_zone(
        "group_2", "rigid", velocity_mm_s=readings
    )
    baseline = float(readings[:4].mean())
    alarm = vibration.alarm_limit(baseline, b_c)
    # The first month whose change from the baseline is the one 5.3 asks to be
    # investigated. With a baseline this low it is also the first month past
    # the ALARM, because 5.4.1 sets the ALARM a change above the baseline.
    caught = int(
        np.argmax(
            np.abs(readings - baseline) > vibration.SIGNIFICANT_CHANGE_FRACTION * b_c
        )
    )

    _fig, ax = plt.subplots(figsize=(9.6, 6.0))
    for lower, upper, colour, letter in (
        (0.0, a_b, COLOR_ZONE_A, "A"),
        (a_b, b_c, COLOR_ZONE_B, "B"),
        (b_c, c_d, COLOR_ZONE_C, "C"),
        (c_d, ceiling, COLOR_ZONE_D, "D"),
    ):
        ax.axhspan(lower, upper, color=theme_fill(colour, ax), zorder=0)
        # Chipped, because the baseline crosses zone A where its letter sits.
        ax.text(
            0.014,
            0.5 * (lower + upper),
            letter,
            transform=ax.get_yaxis_transform(),
            ha="left",
            va="center",
            fontsize=12,
            color=COLOR_FG,
            bbox={
                "boxstyle": "round,pad=0.22",
                "facecolor": COLOR_PANEL,
                "edgecolor": COLOR_GRID,
            },
            zorder=3,
        )

    ax.axhline(
        baseline,
        color=COLOR_QUATERNARY,
        linestyle="--",
        linewidth=1.4,
        zorder=2,
        label=f"baseline: {baseline:.3g} mm/s, the first four months",
    )
    ax.axhline(
        alarm,
        color=COLOR_FG,
        linestyle=":",
        linewidth=1.5,
        zorder=2,
        label=f"ALARM: {alarm:.3g} mm/s, a change above the baseline",
    )

    ax.plot(
        months,
        readings,
        color=COLOR_FG,
        linewidth=1.8,
        marker="o",
        markersize=6,
        markerfacecolor=COLOR_PANEL,
        markeredgewidth=1.6,
        zorder=4,
        label="monthly r.m.s. velocity, with the zone it grades to",
    )
    for month, reading, zone in zip(months, readings, graded, strict=True):
        ax.annotate(
            str(zone),
            xy=(month, reading),
            xytext=(0, 11),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9.5,
            color=COLOR_FG,
            zorder=5,
        )

    ax.annotate(
        # The clause numbers stay in the prose: a "5.3" drawn in a figure comes
        # out of the Spanish pass as "5,3", which reads as a number.
        "month 7: the change from the baseline passes 25 % of the\n"
        "upper limit of zone B, and Criterion I still grades the machine B",
        xy=(months[caught], readings[caught]),
        xytext=(0.255, 0.50),
        textcoords="axes fraction",
        ha="left",
        va="bottom",
        fontsize=9,
        color=COLOR_FG,
        arrowprops={"arrowstyle": "->", "color": COLOR_FG, "linewidth": 1.2},
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
        zorder=6,
    )

    ax.set_xlim(0.4, 12.6)
    ax.set_ylim(0.0, ceiling)
    ax.set_xticks(months)
    ax.set_xlabel("Month of the survey")
    ax.set_ylabel("R.m.s. velocity (mm/s)")
    ax.set_title("A Year of Readings, Graded One by One", pad=12)
    ax.grid(axis="y", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", bbox_to_anchor=(0.045, 0.985), fontsize=8.5)

    plt.tight_layout()
    save_figure(output_dir, "machine_vibration_trend.svg")
    plt.close()


def _signed_percent(value: float) -> str:
    """A Table 5 percentage with the sign the figure is set in.

    ``format`` writes a negative number with an ASCII hyphen, which is a
    shorter, lower mark than the U+2212 the tick labels beside it carry, so
    negatives go through ``_fmt_minus``. Zero takes no sign at all.
    """
    if value > 0.0:
        return f"+{value:.0f}"
    if value < 0.0:
        return _fmt_minus(value, ".0f")
    return "0"


def _table_5_masks(
    frequencies: np.ndarray, transitions: tuple[float, float, float, float]
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The central, skirt and tail masks of ISO 8041-1 Table 5, in that order.

    Written with the inequalities the table itself prints: closed on the
    central region, open on the two skirts, so a frequency exactly at a corner
    takes the tighter limit rather than the wider one beside it.
    """
    ft1, ft2, ft3, ft4 = transitions
    central = (frequencies >= ft2) & (frequencies <= ft3)
    skirts = ((frequencies > ft1) & (frequencies < ft2)) | (
        (frequencies > ft3) & (frequencies < ft4)
    )
    tails = (frequencies <= ft1) | (frequencies >= ft4)
    return central, skirts, tails


def _table_5_row(region: str, limits: tuple[float, float, float]) -> str:
    """One row of ISO 8041-1 Table 5, named and written as the table prints it.

    Both graded columns, because the point of the legend is that they are one
    row: the magnitude pair and the characteristic phase deviation beside it.
    Every number comes from the library constants rather than from the label,
    so the key and the drawing cannot disagree.
    """
    upper, lower, phase = limits
    degrees = "±∞" if not math.isfinite(phase) else f"±{phase:.0f}°"
    return f"{region}: +{upper:.0f} %, {_fmt_minus(lower, '.0f')} %, {degrees}"


def generate_meter_tolerance_regions(output_dir: str) -> None:
    """ISO 8041-1: the five regions Tables 4 and 5 grade a meter in.

    The tolerance on the frequency weighting, and nothing else: no measurement
    and no verdict. Conformity also takes the indication, linearity, overload,
    burst and environmental clauses, which are hardware tests.
    """
    print("Generating meter_tolerance_regions...")
    from matplotlib.ticker import NullFormatter

    from phonometry import vibration

    # Wk carries the transition frequencies Table 4 gives six of the nine
    # weightings (Wb, Wc, Wd, We, Wj and Wk share one row), so the picture is
    # the common case rather than a special one.
    name = "Wk"
    transitions = vibration.TRANSITION_FREQUENCIES_HZ[name]
    ft1, ft2, ft3, ft4 = transitions
    fmin, fmax = 0.1, 400.0
    # The floor of the left panel. The two tails have no lower limit, so their
    # fill is drawn down to the axis instead of down to a value; the floor is
    # low enough for the upper limit of the right-hand tail, which is the half
    # of that row that does bind, to stay on the panel.
    floor = 8.0e-4

    # A pair of points either side of every transition frequency: all three
    # bands step there, and a grid carrying no point at the step draws it as a
    # ramp across whichever cell it falls in.
    edges = np.array(
        [f * scale for f in transitions for scale in (1.0 - 1e-9, 1.0 + 1e-9)]
    )
    # The left panel follows a curve, so it is sampled densely. The two on the
    # right draw limits that are constant between the corners, so they are
    # evaluated on the corners alone: the same staircase in ten points instead
    # of four hundred, which is most of the weight of the finished drawing.
    freqs = np.unique(np.concatenate((np.geomspace(fmin, fmax, 420), edges)))
    steps = np.unique(np.concatenate(([fmin, fmax], edges)))
    design = np.asarray(vibration.weighting_factors(name, freqs))
    upper, lower = vibration.weighting_tolerance_percent(name, freqs)
    step_upper, step_lower = vibration.weighting_tolerance_percent(name, steps)
    step_phase = vibration.phase_tolerance_degrees(name, steps)
    top = design * (1.0 + upper / 100.0)
    bottom = design * (1.0 + lower / 100.0)

    # Table 5's five rows are three distinct limit sets, and the colour of each
    # is the same on all three panels.
    rows = (
        (COLOR_PRIMARY, "the central region", vibration.CENTRAL_TOLERANCE_PERCENT),
        (COLOR_TERTIARY, "the two skirts", vibration.SKIRT_TOLERANCE_PERCENT),
        (COLOR_MUTED, "the two tails", vibration.TAIL_TOLERANCE_PERCENT),
    )
    band_masks = _table_5_masks(freqs, transitions)
    step_masks = _table_5_masks(steps, transitions)

    # The band on the left is the tall panel because it is the only one with a
    # curve in it; the two Table 5 columns stack beside it on the same axis.
    fig = plt.figure(figsize=(13.2, 7.0))
    grid_spec = fig.add_gridspec(
        2, 2, width_ratios=[1.18, 1.0], hspace=0.3, wspace=0.22
    )
    ax_band = fig.add_subplot(grid_spec[:, 0])
    ax_magnitude = fig.add_subplot(grid_spec[0, 1])
    ax_phase = fig.add_subplot(grid_spec[1, 1])

    # Left: the design goal and its sleeve. The lower edge of a tail is zero,
    # which a logarithmic axis cannot draw, so the fill runs to the floor and
    # the boundary line is simply not drawn there: an outline along the axis
    # would read as a limit, and the whole point of the region is that there
    # is none.
    fill_bottom = np.where(bottom > 0.0, bottom, floor)
    for (colour, region, limits), mask in zip(rows, band_masks, strict=True):
        ax_band.fill_between(
            freqs,
            fill_bottom,
            top,
            where=mask,
            color=theme_fill(colour, ax_band),
            zorder=0,
            label=_table_5_row(region, limits),
        )
    ax_band.plot(freqs, top, color=COLOR_FG, linewidth=1.0, alpha=0.55, zorder=2)
    ax_band.plot(
        freqs,
        np.where(bottom > 0.0, bottom, np.nan),
        color=COLOR_FG,
        linewidth=1.0,
        alpha=0.55,
        zorder=2,
    )
    ax_band.plot(
        freqs,
        design,
        color=COLOR_PRIMARY,
        linewidth=1.8,
        zorder=3,
        label=f"{name}, the design goal of Table 3",
    )

    # The four transition frequencies, marked on all three panels and named on
    # the left one, just above the upper edge of the band, which is empty on
    # both sides of every one of them.
    edge_design = np.asarray(vibration.weighting_factors(name, np.asarray(transitions)))
    edge_upper, _edge_lower = vibration.weighting_tolerance_percent(name, transitions)
    for index, (frequency, ceiling) in enumerate(
        zip(transitions, edge_design * (1.0 + edge_upper / 100.0), strict=True), start=1
    ):
        for panel in (ax_band, ax_magnitude, ax_phase):
            panel.axvline(
                frequency,
                color=COLOR_MUTED,
                linestyle="--",
                linewidth=1.0,
                alpha=0.8,
                zorder=1,
            )
        ax_band.text(
            frequency,
            ceiling * 1.9,
            f"$f_\\mathrm{{t{index}}}$",
            fontsize=9.5,
            color=COLOR_FG,
            ha="center",
            va="bottom",
            zorder=4,
            # Over its own dashed line, so the mark carries a chip: without
            # one the rule is drawn straight through the subscript.
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": COLOR_PANEL,
                "edgecolor": COLOR_GRID,
            },
        )

    # The other half of Table 4, which one weighting cannot draw: the five
    # regions are the standard's and the four frequencies are the weighting's.
    # Wh is the far end of that table, and every number here is printed to the
    # four significant figures Table 4 gives it.
    wh_first, _wh_second, _wh_third, wh_last = vibration.TRANSITION_FREQUENCIES_HZ["Wh"]
    ax_band.text(
        math.sqrt(ft2 * ft3),
        2.4e-3,
        "Table 4 gives every weighting its own four:\n"
        f"Wk's run from {ft1:.4g} Hz to {ft4:.4g} Hz,\n"
        f"and Wh's from {wh_first:.4g} Hz to {wh_last:.4g} Hz",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=5,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    ax_band.set_yscale("log")
    ax_band.set_ylim(floor, 3.0)
    ax_band.set_ylabel(f"{name} weighting factor")
    ax_band.set_title("The Band Around Wk, and Where It Changes Width", pad=10)

    # Right top: the same band with the design goal divided out. The two
    # boundary lines are drawn whole rather than region by region, so the step
    # at each transition frequency and the plunge off the bottom of the panel
    # are continuous strokes instead of four disconnected pieces.
    for (colour, _region, _limits), mask in zip(rows, step_masks, strict=True):
        ax_magnitude.fill_between(
            steps,
            step_lower,
            step_upper,
            where=mask,
            color=theme_fill(colour, ax_magnitude),
            zorder=0,
        )
    for limit in (step_upper, step_lower):
        ax_magnitude.plot(
            steps, limit, color=COLOR_FG, linewidth=1.2, alpha=0.75, zorder=2
        )
    ax_magnitude.axhline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.35, zorder=1)
    ax_magnitude.text(
        math.sqrt(ft2 * ft3),
        -31.0,
        f"{_fmt_minus(vibration.UNCONSTRAINED_BELOW, '.0f')} %: below "
        "$f_\\mathrm{t1}$ and\nabove $f_\\mathrm{t4}$ the standard sets\n"
        "no lower limit at all",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=5,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    central_upper, central_lower, central_phase = vibration.CENTRAL_TOLERANCE_PERCENT
    skirt_upper, skirt_lower, skirt_phase = vibration.SKIRT_TOLERANCE_PERCENT
    magnitude_ticks = (skirt_upper, central_upper, 0.0, central_lower, skirt_lower)
    # Room under the lower skirt limit for the note about the two tails, and
    # a little air over the upper one for the boundary line.
    ax_magnitude.set_ylim(skirt_lower - 20.0, skirt_upper + 8.0)
    ax_magnitude.set_yticks(list(magnitude_ticks))
    ax_magnitude.set_yticklabels([_signed_percent(value) for value in magnitude_ticks])
    ax_magnitude.set_ylabel("Magnitude tolerance on the factor (%)")
    ax_magnitude.set_title("The Magnitude Tolerance, to Scale", pad=8)

    # Right bottom: the other graded column of the same table. Formula (6) is
    # printed inside absolute-value bars, so its limit is a ceiling on a
    # modulus rather than a band about a line, and the fill runs from zero up
    # to it. In the two tails there is no ceiling, so the fill reaches the top
    # of the panel and the two cells are marked with what the table prints.
    ceiling_deg = 1.55 * skirt_phase
    phase_band = np.where(np.isfinite(step_phase), step_phase, ceiling_deg)
    for (colour, _region, _limits), mask in zip(rows, step_masks, strict=True):
        ax_phase.fill_between(
            steps,
            np.zeros_like(phase_band),
            phase_band,
            where=mask,
            color=theme_fill(colour, ax_phase),
            zorder=0,
        )
    ax_phase.plot(
        steps,
        np.where(np.isfinite(step_phase), step_phase, np.nan),
        color=COLOR_FG,
        linewidth=1.2,
        alpha=0.75,
        zorder=2,
    )
    for tail_centre in (math.sqrt(fmin * ft1), math.sqrt(ft4 * fmax)):
        # No chip: the mark sits on a flat fill, clear of every gridline.
        ax_phase.text(
            tail_centre,
            0.16 * ceiling_deg,
            "±∞",
            fontsize=10,
            color=COLOR_FG,
            ha="center",
            va="center",
            zorder=4,
        )
    ax_phase.text(
        math.sqrt(ft2 * ft3),
        0.76 * ceiling_deg,
        "footnote a: the phase column applies only\n"
        "to instruments whose measurement parameter\n"
        "is not based on r.m.s. values",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=5,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    ax_phase.set_ylim(0.0, ceiling_deg)
    ax_phase.set_yticks([0.0, central_phase, skirt_phase])
    ax_phase.set_yticklabels(
        [f"{value:.0f}" for value in (0.0, central_phase, skirt_phase)]
    )
    ax_phase.set_ylabel("Limit on $\\Delta\\varphi_0$ (degrees)")
    ax_phase.set_title("The Phase Tolerance, on the Same Corners", pad=8)

    # One frequency axis for all three panels, ticked at the four numbers of
    # Table 4 and at the decades that place them. The labels are formatted
    # from the same constants that place the ticks, so a number cannot be
    # written under a rule it no longer belongs to.
    ticks = (0.1, ft1, ft2, 10.0, ft3, ft4)
    tick_labels = [f"{value:.4g}" for value in ticks]
    for panel in (ax_band, ax_magnitude, ax_phase):
        panel.set_xscale("log")
        panel.set_xlim(fmin, fmax)
        panel.set_xticks(list(ticks))
        panel.set_xticklabels(tick_labels, fontsize=9)
        panel.xaxis.set_minor_formatter(NullFormatter())
        panel.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
        panel.set_axisbelow(True)
    for panel in (ax_band, ax_phase):
        panel.set_xlabel(LABEL_FREQ_HZ)
    # The two right-hand panels share one axis, so it is labelled once, under
    # the lower of them.
    ax_magnitude.tick_params(axis="x", labelbottom=False)

    # One key at the foot of the figure: the three regions are the same three
    # colours on all three panels, so a box per panel would say it three
    # times. One row of four, so that the three entries read as the three
    # distinct rows of Table 5 laid side by side, both graded columns each.
    handles, names = ax_band.get_legend_handles_labels()
    fig.legend(handles, names, loc="lower center", ncol=4, fontsize=8.5, frameon=False)
    fig.suptitle(
        "The Shape of the ISO 8041-1 Tolerance: Tables 4 and 5 on One Frequency Axis",
        fontsize=13,
    )
    # The margins are set by hand rather than by ``tight_layout``, which
    # declines a gridspec with a panel spanning two rows: it would warn, leave
    # the defaults in place and undo the ``hspace`` and ``wspace`` above. The
    # foot holds the key clear of the two frequency labels, and the head holds
    # the three panel titles clear of the suptitle.
    fig.subplots_adjust(left=0.068, right=0.985, top=0.875, bottom=0.145)
    save_figure(output_dir, "meter_tolerance_regions.svg")
    plt.close()


def _intercept_at_zero(
    lower_hz: float, upper_hz: float, lower_deg: float, upper_deg: float
) -> float:
    """Where the line through one pair of phase errors crosses ``f = 0``.

    ISO 8041-1 Formula (6) is this number inside absolute-value bars: its
    numerator is written with the two products exchanged, which flips the sign
    and leaves the modulus alone. Kept signed here because the drawing places
    a mark at the crossing, and a mark below the axis has to be drawn below
    the axis; the reading beside it takes the modulus the formula prints.
    """
    return (upper_hz * lower_deg - lower_hz * upper_deg) / (upper_hz - lower_hz)


def _draw_phase_series(
    ax: Axes,
    frequencies_hz: np.ndarray,
    values_deg: np.ndarray,
    colour: str,
    *,
    dashed: bool = False,
    hollow: bool = False,
    label: str = "_nolegend_",
) -> None:
    """One of the three phase errors, stroked the same way in every panel.

    Three panels draw the same three responses, so the stroke is written once:
    a reader who has learnt a colour on one of them has learnt it on all three.

    The delay-only response is the hollow one, and that is not decoration. Its
    characteristic phase deviation is zero at every pair, which is exactly
    where the response with the spare pole sits over most of the range; two
    filled markers there would leave only whichever was drawn last, and the
    reading the panel exists for is that both are on the axis.
    """
    ax.plot(
        frequencies_hz,
        values_deg,
        color=colour,
        linestyle="--" if dashed else "-",
        linewidth=1.7,
        marker="o",
        markersize=5.5 if hollow else 3.2,
        markerfacecolor="none" if hollow else colour,
        label=label,
        zorder=3,
    )


def generate_meter_phase_verification(output_dir: str) -> None:
    """ISO 8041-1 Formula (6): the phase criterion that grades an intercept.

    One instrument's phase error, three times over: against frequency, graded
    against the Table 5 band, and read as the intercept the formula actually
    takes. A constant error is graded at face value, a constant group delay as
    zero, and the spare pole is what the criterion catches.
    """
    print("Generating meter_phase_verification...")
    from matplotlib.ticker import NullFormatter

    from phonometry import vibration

    name = "Wk"
    transitions = vibration.TRANSITION_FREQUENCIES_HZ[name]
    ft3 = transitions[2]
    # The nominal frequency range of a whole-body meter, on the exact
    # one-third-octave centres of Formula (B.1). This is the grid the guide
    # grades its instrument on, so the drawing and the page report one run.
    freqs = 10.0 ** (np.arange(-3, 20) / 10.0)
    # The frame runs a little past ft1 and ft4 so that both tails, where
    # Table 5 sets no limit at all, are on the panel; the meter's own range
    # reaches neither of them.
    fmin, fmax = 0.16, 250.0

    # The guide's instrument and the two error shapes the criterion is built
    # around. Every reading in the drawing is formatted from these three.
    constant_deg = 4.0
    delay_s = 2.0e-3
    pole_hz = 100.0

    zero = np.zeros_like(freqs)
    design = vibration.verify_phase_response(name, freqs, zero).design_phase_deg
    delay_deg = -360.0 * freqs * delay_s
    pole_deg = -np.degrees(np.arctan(freqs / pole_hz))

    # Colour carries the response and the stroke carries the reading: dashed
    # for the constant, hollow for the one whose graded value is zero. The
    # three region colours are reserved for Table 5, so none of these three is
    # one of them, and red is the failing response, as it is in the library's
    # own verdict plot.
    responses = (
        (
            COLOR_QUATERNARY,
            True,
            False,
            f"a constant phase error of +{constant_deg:.0f}°",
            np.full(freqs.shape, constant_deg),
        ),
        (
            COLOR_FG,
            False,
            True,
            f"{delay_s * 1e3:.0f} ms of group delay on its own",
            delay_deg,
        ),
        (
            COLOR_SECONDARY,
            False,
            False,
            f"the same delay with a spare pole at {pole_hz:.0f} Hz",
            delay_deg + pole_deg,
        ),
    )
    checks = [
        vibration.verify_phase_response(name, freqs, design + error)
        for _colour, _dashed, _hollow, _label, error in responses
    ]
    constant_check, delay_check, pole_check = checks

    # Table 5's five rows are three distinct phase limits, in the colours
    # ``meter_tolerance_regions`` gives the same three rows.
    central_phase = vibration.CENTRAL_TOLERANCE_PERCENT[2]
    skirt_phase = vibration.SKIRT_TOLERANCE_PERCENT[2]
    tail_phase = vibration.TAIL_TOLERANCE_PERCENT[2]
    # The third row prints a limit that is the absence of one, and the glyph
    # is read off the constant rather than typed, the way ``_table_5_row``
    # reads the same cell for the figure beside this one on the page: three
    # rows, one convention, and no label that can outlive its constant.
    tail_limit = f"±{tail_phase:.0f}°" if math.isfinite(tail_phase) else "±∞"
    regions = (
        (
            COLOR_PRIMARY,
            f"the central region, where Table 5 allows ±{central_phase:.0f}°",
        ),
        (COLOR_TERTIARY, f"the two skirts, where it allows ±{skirt_phase:.0f}°"),
        (COLOR_MUTED, f"the two tails, where it allows {tail_limit}"),
    )
    # A pair of points either side of every transition frequency: the band
    # steps there, and a grid carrying no point at the step draws it as a ramp
    # across whichever cell it falls in. The limit is constant between the
    # corners, so ten points draw the whole staircase.
    edges = np.array(
        [f * scale for f in transitions for scale in (1.0 - 1e-9, 1.0 + 1e-9)]
    )
    steps = np.unique(np.concatenate(([fmin, fmax], edges)))
    step_masks = _table_5_masks(steps, transitions)
    step_limit = vibration.phase_tolerance_degrees(name, steps)
    # The two tails have no limit, so their fill runs to the top of the panel
    # instead of to a value.
    ceiling_deg = 1.55 * skirt_phase
    band = np.where(np.isfinite(step_limit), step_limit, ceiling_deg)

    fig = plt.figure(figsize=(13.4, 7.6))
    grid_spec = fig.add_gridspec(2, 2, width_ratios=[1.32, 1.0])
    ax_error = fig.add_subplot(grid_spec[0, 0])
    ax_cpd = fig.add_subplot(grid_spec[1, 0])
    ax_geom = fig.add_subplot(grid_spec[:, 1])
    chip = {
        "boxstyle": "round,pad=0.35",
        "facecolor": COLOR_PANEL,
        "edgecolor": COLOR_GRID,
    }

    # Top left: the quantity nobody grades. No band, because Table 5 sets none.
    for (colour, dashed, hollow, label, _error), check in zip(
        responses, checks, strict=True
    ):
        _draw_phase_series(
            ax_error,
            freqs,
            check.deviation_deg,
            colour,
            dashed=dashed,
            hollow=hollow,
            label=label,
        )
    ax_error.axhline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.35, zorder=1)
    # Low and to the left, where the three responses have not yet fallen:
    # the note is five lines and the two that fall reach its top edge only
    # past 44 Hz, which is well to the right of where it ends.
    ax_error.text(
        2.8,
        -74.0,
        "Table 5 sets no limit on this quantity: its phase column\n"
        "grades the characteristic phase deviation in the panel below,\n"
        "and footnote a applies that column only to instruments whose\n"
        "measurement parameter is not based on r.m.s. values. At "
        f"{freqs[-1]:.1f} Hz\nthe delay alone is "
        f"{_fmt_minus(delay_check.deviation_deg[-1], '.1f')}°, and with the "
        f"pole {_fmt_minus(pole_check.deviation_deg[-1], '.1f')}°",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=5,
        bbox=chip,
    )

    # Bottom left: the quantity Table 5 does grade, inside its band.
    for (colour, _label), mask in zip(regions, step_masks, strict=True):
        ax_cpd.fill_between(
            steps,
            np.zeros_like(band),
            band,
            where=mask,
            color=theme_fill(colour, ax_cpd),
            zorder=0,
            label=_label,
        )
    ax_cpd.plot(
        steps,
        np.where(np.isfinite(step_limit), step_limit, np.nan),
        color=COLOR_FG,
        linewidth=1.2,
        alpha=0.75,
        zorder=2,
    )
    for (colour, dashed, hollow, _label, _error), check in zip(
        responses, checks, strict=True
    ):
        _draw_phase_series(
            ax_cpd,
            check.characteristic_frequencies_hz,
            check.characteristic_deviation_deg,
            colour,
            dashed=dashed,
            hollow=hollow,
        )

    # The failing pair, and the whole of the attribution rule: a cross at the
    # frequency the value is attributed to, an open circle at the other end of
    # the same pair, and the step in the band between them.
    #
    # One index for the mark, the reading and the limit. They would agree
    # read from three ends here, because exactly one pair fails and it is the
    # last one, but nothing in the code says so: two failing pairs and the
    # cross would carry another pair's number and another pair's limit. A
    # response with no failing pair raises here instead, which is the right
    # noise for a drawing whose subject is the pair that fails.
    fail_index = int(np.flatnonzero(~pole_check.within_tolerance)[0])
    fail_hz = float(pole_check.characteristic_frequencies_hz[fail_index])
    fail_deg = float(pole_check.characteristic_deviation_deg[fail_index])
    fail_limit = float(pole_check.tolerance_deg[fail_index])
    # The other end of that very same pair, which is the whole of the
    # attribution rule: Formula (H.3) hands the value to the lower of the two.
    pair_hz = float(pole_check.frequencies_hz[fail_index + 1])
    upper_limit = float(vibration.phase_tolerance_degrees(name, [pair_hz])[0])
    ax_cpd.plot(
        [fail_hz, pair_hz],
        [fail_deg, fail_deg],
        color=COLOR_SECONDARY,
        linestyle=":",
        linewidth=1.2,
        zorder=4,
    )
    ax_cpd.plot(
        [pair_hz],
        [fail_deg],
        color=COLOR_SECONDARY,
        marker="o",
        markersize=6.5,
        markerfacecolor="none",
        linestyle="none",
        zorder=4,
    )
    # The cross lands on ft3 itself, which is where the band steps from one
    # colour to the next, so it is drawn with a halo of the panel colour:
    # without it the mark reads as half in the central region and half in the
    # skirt, and which side of that step it is on is the whole verdict.
    ax_cpd.plot(
        [fail_hz],
        [fail_deg],
        color=COLOR_SECONDARY,
        marker="X",
        markersize=11,
        markeredgecolor=COLOR_PANEL,
        markeredgewidth=1.4,
        linestyle="none",
        zorder=5,
    )
    # Both notes hang over the central region and above the ±12° line, which
    # is the one part of this panel where nothing is drawn: the staircase is
    # what the panel grades against, and a chip resting on it would hide the
    # step at the very frequency the verdict turns on. They share an anchor,
    # the geometric middle of the central region, so they stack.
    note_hz = math.sqrt(transitions[1] * ft3)
    ax_cpd.text(
        note_hz,
        15.4,
        f"{fail_deg:.2f}° against the ±{fail_limit:.0f}° of the central "
        "region: each value\nis attributed to the lower frequency of its "
        f"pair, so this one\nis graded at $f_\\mathrm{{t3}}$ = {fail_hz:.1f} Hz,"
        f" which Table 5 keeps\ninside the region, and not at {pair_hz:.1f} Hz,"
        f" where it allows ±{upper_limit:.0f}°",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=6,
        bbox=chip,
    )
    ax_cpd.text(
        note_hz,
        9.3,
        f"a constant +{constant_deg:.0f}° error is graded "
        f"{constant_check.characteristic_deviation_deg.max():.2f}° at every pair;\n"
        f"{delay_s * 1e3:.0f} ms of group delay is graded "
        f"{delay_check.characteristic_deviation_deg.max():.2f}° at every pair",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=6,
        bbox=chip,
    )

    # The four transition frequencies of Table 4, marked on both panels of the
    # shared axis and named on the upper one, where the panel is empty.
    for index, frequency in enumerate(transitions, start=1):
        for panel in (ax_error, ax_cpd):
            panel.axvline(
                frequency,
                color=COLOR_MUTED,
                linestyle="--",
                linewidth=1.0,
                alpha=0.8,
                zorder=1,
            )
        ax_error.text(
            frequency,
            7.0,
            f"$f_\\mathrm{{t{index}}}$",
            fontsize=9.5,
            color=COLOR_FG,
            ha="center",
            va="bottom",
            zorder=4,
            # Over its own dashed line, so the mark carries a chip: without
            # one the rule is drawn straight through the subscript.
            bbox={
                "boxstyle": "round,pad=0.2",
                "facecolor": COLOR_PANEL,
                "edgecolor": COLOR_GRID,
            },
        )

    # Right: the same three errors on a linear frequency axis, with the line
    # through the last pair carried back to where the formula reads it.
    for (colour, dashed, hollow, _label, _error), check in zip(
        responses, checks, strict=True
    ):
        _draw_phase_series(
            ax_geom, freqs, check.deviation_deg, colour, dashed=dashed, hollow=hollow
        )
        intercept = _intercept_at_zero(
            float(freqs[-2]),
            float(freqs[-1]),
            float(check.deviation_deg[-2]),
            float(check.deviation_deg[-1]),
        )
        # Grey rather than the foreground colour: two of the three lie exactly
        # on the response they were built from, which is the invariance, and a
        # construction line the same colour as the curve under it would be
        # invisible on the one response where that matters most.
        ax_geom.plot(
            [0.0, freqs[-1]],
            [intercept, check.deviation_deg[-1]],
            color=COLOR_MUTED,
            linestyle=":",
            linewidth=1.4,
            zorder=4,
        )
        ax_geom.plot(
            [0.0],
            [intercept],
            color=colour,
            marker="o",
            markersize=8,
            linestyle="none",
            zorder=5,
        )
        # The reading at the crossing, in the margin the axis was widened for.
        # Formula (6) takes this number without its sign, and the note below
        # says so; the mark is at a signed height, so the label beside it
        # carries the sign it is drawn at. Rounding before the sign is what
        # keeps the delay's crossing, which lands on the negative side of zero
        # by a fifteenth decimal place, from being written as a negative zero.
        ax_geom.text(
            -1.4,
            intercept,
            f"{_fmt_minus(round(intercept, 2) + 0.0, '+.2f')}°",
            fontsize=9,
            color=colour,
            ha="right",
            va="bottom",
            zorder=5,
        )
    ax_geom.axhline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.35, zorder=1)
    ax_geom.axvline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.35, zorder=1)
    for frequency in (freqs[-2], freqs[-1]):
        ax_geom.axvline(
            frequency,
            color=COLOR_MUTED,
            linestyle="--",
            linewidth=1.0,
            alpha=0.8,
            zorder=1,
        )
    # Right-aligned short of the left-hand rule of the pair, and two lines
    # rather than one: the single line of the draft ended on the right spine
    # in English and crossed it in Spanish, and a line long enough to reach
    # from the frame to the rules cannot avoid being drawn over them. Anchored
    # inside the frame, the whole note lives in the band above the constant
    # response, where nothing else is drawn.
    ax_geom.text(
        61.0,
        9.4,
        "the two dashed lines mark the pair\nthe dotted lines are drawn through",
        fontsize=9,
        color=COLOR_FG,
        ha="right",
        va="center",
        zorder=6,
        bbox=chip,
    )
    # Anchored on its right edge rather than centred: centred, the chip runs
    # past 63.1 Hz and covers the dashed rule of the failing pair, which is
    # the one thing the note above it points at.
    ax_geom.text(
        61.0,
        -84.0,
        "$\\Delta\\varphi_0$ is where the line through a pair of adjacent\n"
        "points crosses $f = 0$, taken without its sign. A line through\n"
        "the origin gives zero, and a horizontal one gives its own\n"
        "height: that is the whole of Formula (6)",
        fontsize=9,
        color=COLOR_FG,
        ha="right",
        va="center",
        zorder=6,
        bbox=chip,
    )

    error_label = "Phase error, measured minus design (degrees)"
    ax_error.set_ylabel(error_label)
    ax_error.set_title("The Phase Error Itself, Which Table 5 Never Grades", pad=8)
    ax_cpd.set_ylabel("Characteristic phase deviation $\\Delta\\varphi_0$ (degrees)")
    ax_cpd.set_title("The Characteristic Phase Deviation, Which It Grades", pad=8)
    ax_geom.set_ylabel(error_label)
    ax_geom.set_title(
        "The Same Errors on a Linear Frequency Axis, Read at $f = 0$", pad=8
    )
    # One scale for the two panels that draw the same quantity, with enough
    # headroom over the constant response for the note in the right-hand one
    # and for the four transition marks in the left-hand one, which are drawn
    # with a chip and would otherwise cross the frame.
    for panel in (ax_error, ax_geom):
        panel.set_ylim(-104.0, 15.0)
    ax_cpd.set_ylim(-1.0, ceiling_deg)
    ax_cpd.set_yticks([0.0, central_phase, skirt_phase])
    ax_cpd.set_yticklabels(
        [f"{value:.0f}" for value in (0.0, central_phase, skirt_phase)]
    )

    # One frequency axis for the two panels on the left, ticked at the four
    # numbers of Table 4 and at the two decades that place them. The labels
    # are formatted from the same constants that place the ticks.
    ticks = (transitions[0], transitions[1], 1.0, 10.0, ft3, transitions[3])
    for panel in (ax_error, ax_cpd):
        panel.set_xscale("log")
        panel.set_xlim(fmin, fmax)
        panel.set_xticks(list(ticks))
        panel.set_xticklabels([f"{value:.4g}" for value in ticks], fontsize=9)
        panel.xaxis.set_minor_formatter(NullFormatter())
    ax_error.tick_params(axis="x", labelbottom=False)
    # Room to the left of f = 0 for the three intercept readings: they are
    # the number Formula (6) takes, and the panel exists to show that it is
    # read off this axis rather than computed somewhere else. The automatic
    # locator would tick that margin with a negative frequency, so its choice
    # over the measured range is kept and nothing below zero is.
    # (``set_xticks`` widens the view to hold every tick it is given, so the
    # limit is set after it and not before.)
    ax_geom.set_xticks([tick for tick in ax_geom.get_xticks() if tick >= 0.0])
    ax_geom.set_xlim(-13.0, 84.0)
    for panel in (ax_error, ax_cpd, ax_geom):
        panel.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
        panel.set_axisbelow(True)
    for panel in (ax_cpd, ax_geom):
        panel.set_xlabel(LABEL_FREQ_HZ)

    # One key at the foot: the three responses on the upper row, the three
    # Table 5 rows they are graded against on the lower one. A legend fills
    # column by column, so the two are interleaved to come out as two rows.
    response_handles, response_labels = ax_error.get_legend_handles_labels()
    region_handles, region_labels = ax_cpd.get_legend_handles_labels()
    handles = [
        h for pair in zip(response_handles, region_handles, strict=True) for h in pair
    ]
    labels = [
        t for pair in zip(response_labels, region_labels, strict=True) for t in pair
    ]
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=8.5, frameon=False)
    fig.suptitle(
        "Grading a Phase Response: What ISO 8041-1 Formula (6) Ignores, "
        "and What It Catches",
        fontsize=13,
    )
    # No tight_layout: a gridspec with a panel spanning two rows is one of the
    # layouts it declines to honour, and it warns and reverts instead.
    fig.subplots_adjust(
        left=0.055, right=0.99, top=0.9, bottom=0.135, hspace=0.3, wspace=0.16
    )
    save_figure(output_dir, "meter_phase_verification.svg")
    plt.close()


def _verdict_clause(*, passes: bool) -> str:
    """The verdict of one sweep, as the clause the legend ends on.

    Taken from ``WeightingVerification.passes`` rather than typed, so a
    library change that moved either verdict would change the drawn label
    (and, since the label is an exact key of the Spanish table, would be
    caught by the language gate rather than shipped as a wrong caption).
    """
    return "and it conforms" if passes else "and it does not conform"


def generate_meter_weighting_verification(output_dir: str) -> None:
    """ISO 8041-1: one Wk bench sweep, refused, and the same shortfall accepted.

    The frequency weighting only. A sweep inside these limits has met one
    clause of the standard, and the indication, linearity, noise, overload,
    burst and environmental clauses are laboratory measurements no arithmetic
    can stand in for.
    """
    print("Generating meter_weighting_verification...")
    from matplotlib.ticker import NullFormatter

    from phonometry import vibration

    name = "Wk"
    ft1, ft2, ft3, ft4 = vibration.TRANSITION_FREQUENCIES_HZ[name]

    # The guide's own bench sweep, on the one-third-octave centres of Formula
    # (B.1) rather than on the printed decimals: 63.096 Hz rounds up past ft3
    # and would then be graded against the skirt rather than against the
    # central region it is the last band of.
    bands = np.array([-3, 0, 3, 6, 9, 12, 15, 18, 19])
    swept = 10.0 ** (bands / 10.0)
    as_read = np.array(
        [0.4314, 0.4969, 0.5466, 0.9937, 1.068, 0.7897, 0.3427, 0.1894, 0.1366]
    )
    moved = np.array(
        [0.4314, 0.4969, 0.5466, 0.9937, 1.068, 0.7897, 0.4112, 0.1894, 0.1138]
    )
    refused = vibration.verify_weighting(name, swept, as_read)
    accepted = vibration.verify_weighting(name, swept, moved)

    # Where each sweep reads low, read off the verdict rather than off the
    # index the array was typed at: the first is the frequency the standard
    # refuses, the second the deepest deviation of the sweep that conforms.
    outside = ~refused.within_tolerance
    refused_hz = float(refused.failing_frequencies_hz[0])
    moved_hz = float(swept[int(np.argmin(accepted.deviation_percent))])
    shortfall = _fmt_minus(refused.worst_deviation_percent, ".1f")

    central_upper, central_lower, _central_phase = vibration.CENTRAL_TOLERANCE_PERCENT
    skirt_upper, skirt_lower, _skirt_phase = vibration.SKIRT_TOLERANCE_PERCENT

    # The band, on a grid that opens just inside ft1 and closes just inside
    # ft4: Table 5 prints its first and last rows closed (f <= ft1, f >= ft4),
    # so a grid point exactly on a corner would take the tail's rule and drop
    # the lower edge of the sleeve to zero in one column of pixels. What is
    # drawn is therefore the open interval, one part in a thousand million
    # inside each corner, and the two extreme columns carry the skirt limit
    # that holds everywhere between the corners rather than the tail rule that
    # holds at the corner itself: that lapse is one frequency wide, and it is
    # section 3's subject rather than this figure's. A pair of points either
    # side of ft2 and ft3 makes the two steps vertical rather than a ramp
    # across whichever cell they fall in.
    inside_ft1, inside_ft4 = ft1 * (1.0 + 1e-9), ft4 * (1.0 - 1e-9)
    edges = np.array(
        [f * scale for f in (ft2, ft3) for scale in (1.0 - 1e-9, 1.0 + 1e-9)]
    )
    freqs = np.unique(
        np.concatenate((np.geomspace(inside_ft1, inside_ft4, 420), edges))
    )
    # The upper panel follows a curve, so it is sampled densely; the lower one
    # draws limits that are constant between the corners, so it is evaluated
    # on the corners alone, which is the same staircase in six points instead
    # of four hundred.
    steps = np.unique(np.concatenate(([inside_ft1, inside_ft4], edges)))
    design = np.asarray(vibration.weighting_factors(name, freqs))
    upper, lower = vibration.weighting_tolerance_percent(name, freqs)
    step_upper, step_lower = vibration.weighting_tolerance_percent(name, steps)

    # How far the refused point sits below the limit of its own region. The
    # upper panel cannot show a gap this small, so it is the number that panel
    # says out loud, and it is said in the quantity the lower panel is drawn
    # in: deviation from the design goal, so that the chip above and the two
    # lines below are one arithmetic (-15.0 against -11) and not two
    # percentages of two different denominators.
    swept_lower = vibration.weighting_tolerance_percent(name, swept)[1]
    below_limit = swept_lower - refused.deviation_percent
    failing = int(np.flatnonzero(outside)[np.argmax(below_limit[outside])])
    gap, failing_limit = float(below_limit[failing]), float(swept_lower[failing])

    fig = plt.figure(figsize=(11.6, 9.0))
    grid_spec = fig.add_gridspec(2, 1, height_ratios=[1.12, 0.86], hspace=0.24)
    ax_band = fig.add_subplot(grid_spec[0])
    ax_deviation = fig.add_subplot(grid_spec[1], sharex=ax_band)

    # Upper panel: the design goal and the sleeve Table 5 allows around it.
    # One wash rather than one per region: the regions are the previous
    # figure's subject, and the two saturated colours this drawing has are
    # spent on telling the two sweeps apart.
    band_label = (
        f"the Table 5 band: +{central_upper:.0f} % / "
        f"{_fmt_minus(central_lower, '.0f')} % centrally, +{skirt_upper:.0f} % / "
        f"{_fmt_minus(skirt_lower, '.0f')} % in a skirt"
    )
    ax_band.fill_between(
        freqs,
        design * (1.0 + lower / 100.0),
        design * (1.0 + upper / 100.0),
        color=theme_fill(COLOR_PRIMARY, ax_band),
        zorder=0,
        label=band_label,
    )
    for limit in (upper, lower):
        ax_band.plot(
            freqs,
            design * (1.0 + limit / 100.0),
            color=COLOR_FG,
            linewidth=1.0,
            alpha=0.55,
            zorder=2,
        )
    ax_band.plot(
        freqs,
        design,
        color=COLOR_PRIMARY,
        linewidth=1.8,
        zorder=3,
        label="the design goal the deviation is measured from",
    )

    # The two sweeps. The accepted one is drawn first and hollow, so that at
    # the seven bands where the two agree the reader sees one point wearing
    # both marks rather than one mark hiding the other.
    accepted_label = (
        f"the same shortfall moved to {moved_hz:.2f} Hz, "
        + _verdict_clause(passes=accepted.passes)
    )
    refused_label = (
        f"the sweep as read: {shortfall} % at {refused_hz:.2f} Hz, "
        + _verdict_clause(passes=refused.passes)
    )
    for panel, read_values, moved_values in (
        (ax_band, refused.measured, accepted.measured),
        (ax_deviation, refused.deviation_percent, accepted.deviation_percent),
    ):
        panel.plot(
            swept,
            read_values,
            marker="o",
            markersize=5.2,
            color=COLOR_SECONDARY,
            linestyle="none",
            zorder=5,
            label=refused_label if panel is ax_band else None,
        )
        panel.plot(
            swept,
            moved_values,
            marker="o",
            markersize=9.6,
            markerfacecolor="none",
            markeredgewidth=1.4,
            color=COLOR_TERTIARY,
            linestyle="none",
            zorder=4,
            label=accepted_label if panel is ax_band else None,
        )

    # What the upper panel cannot show, written on the upper panel. The chip
    # sits in the empty quarter under the roll-off and points at the marker.
    ax_band.annotate(
        f"{refused_hz:.2f} Hz falls in the central region, and the point sits\n"
        f"{gap:.1f} % of the design goal below the "
        f"{_fmt_minus(failing_limit, '.0f')} % limit",
        xy=(refused_hz, float(refused.measured[failing])),
        xytext=(9.2, 0.058),
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=6,
        arrowprops={
            "arrowstyle": "->",
            "color": COLOR_FG,
            "linewidth": 1.0,
            "shrinkB": 7.0,
        },
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    # The panel is scaled to the drawn band and no wider: the two sweeps part
    # by a fifth of a factor at the two bands where they differ, and on a taller
    # axis that difference closes to the width of the ink.
    ax_band.set_yscale("log")
    ax_band.set_ylim(0.020, 1.45)
    ax_band.set_ylabel(f"Weighting factor of the {name} channel")
    ax_band.set_title("The Bench Sweep Inside a Band That Narrows in the Middle", pad=8)

    # Lower panel: the same nine points as the quantity the acceptance test is
    # written in, against the limit of the region each one falls in.
    ax_deviation.fill_between(
        steps,
        step_lower,
        step_upper,
        color=theme_fill(COLOR_PRIMARY, ax_deviation),
        zorder=0,
    )
    for limit in (step_upper, step_lower):
        ax_deviation.plot(
            steps, limit, color=COLOR_FG, linewidth=1.2, alpha=0.75, zorder=2
        )
    ax_deviation.axhline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.35, zorder=1)

    # The flip itself: the same shortfall carried across the step the lower
    # limit takes at ft3, from below the line to above it.
    ax_deviation.annotate(
        "",
        xy=(moved_hz, float(np.min(accepted.deviation_percent))),
        xytext=(refused_hz, float(refused.worst_deviation_percent)),
        arrowprops={
            "arrowstyle": "->",
            "color": COLOR_FG,
            "linewidth": 1.4,
            "shrinkA": 9.0,
            "shrinkB": 9.0,
        },
        zorder=3,
    )
    ax_deviation.text(
        refused_hz,
        skirt_lower - 6.5,
        f"the same shortfall, {shortfall} %, twice: outside the "
        f"{_fmt_minus(central_lower, '.0f')} %\nof the central region, inside the "
        f"{_fmt_minus(skirt_lower, '.0f')} % of the upper skirt",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    magnitude_ticks = (skirt_upper, central_upper, 0.0, central_lower, skirt_lower)
    ax_deviation.set_ylim(skirt_lower - 13.5, skirt_upper + 5.0)
    ax_deviation.set_yticks(list(magnitude_ticks))
    ax_deviation.set_yticklabels([_signed_percent(value) for value in magnitude_ticks])
    ax_deviation.set_ylabel("Deviation from the design goal (%)")
    ax_deviation.set_title(
        "The Same Sweep in Per Cent, Where the Two Verdicts Part", pad=8
    )

    # One frequency axis for both panels, running from the first corner of
    # Table 4 to the last and ticked at all four of them, each label carrying
    # the number and the name the table gives it. The labels are formatted
    # from the same constants that place the ticks, so a corner cannot be
    # written under a rule it no longer belongs to.
    ticks = (ft1, ft2, 1.0, 10.0, ft3, ft4)
    corners = (
        "$f_\\mathrm{t1}$",
        "$f_\\mathrm{t2}$",
        "",
        "",
        "$f_\\mathrm{t3}$",
        "$f_\\mathrm{t4}$",
    )
    tick_labels = [
        f"{value:.4g}\n{corner}".rstrip()
        for value, corner in zip(ticks, corners, strict=True)
    ]
    for panel in (ax_band, ax_deviation):
        for corner in (ft2, ft3):
            panel.axvline(
                corner,
                color=COLOR_MUTED,
                linestyle="--",
                linewidth=1.0,
                alpha=0.8,
                zorder=1,
            )
        panel.set_xscale("log")
        panel.set_xlim(ft1, ft4)
        panel.set_xticks(list(ticks))
        panel.set_xticklabels(tick_labels, fontsize=9)
        panel.xaxis.set_minor_formatter(NullFormatter())
        panel.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
        panel.set_axisbelow(True)
    ax_deviation.set_xlabel(LABEL_FREQ_HZ)
    # The two panels share the axis, so it is labelled once, under the lower.
    ax_band.tick_params(axis="x", labelbottom=False)

    # One key at the foot of the figure, two entries to a row: the band and
    # the design goal it is drawn around, then the two sweeps and what the
    # standard says about each. The row clears the frequency labels above it
    # because ``subplots_adjust`` holds the panels off the foot of the figure.
    handles, names = ax_band.get_legend_handles_labels()
    fig.legend(handles, names, loc="lower center", ncol=2, fontsize=8.5, frameon=False)
    fig.suptitle(
        "The Same Shortfall, Refused in One Region and Accepted in the Next",
        fontsize=13,
    )
    fig.subplots_adjust(left=0.075, right=0.985, top=0.912, bottom=0.15)
    save_figure(output_dir, "meter_weighting_verification.svg")
    plt.close()


def generate_meter_uncertainty_allowance(output_dir: str) -> None:
    """ISO 8041-1: what the laboratory's own expanded uncertainty moves.

    5.6.6 keeps the Table 5 band where it is; 13.1 and 14.1 extend the
    measured deviation by the testing laboratory's actual expanded
    uncertainty. So a sweep that is inside the printed band can still be
    refused, and a bench that measures more carefully certifies more
    instruments.
    """
    print("Generating meter_uncertainty_allowance...")
    from matplotlib.ticker import NullFormatter

    from phonometry import vibration

    name = "Wk"
    # 12.11.2 is the mechanical frequency-response test, which is the test
    # this drawing grades, and 4.5 % is the most it lets a laboratory carry:
    # the general prohibition is 12.1 (folio 28), and the per-test maxima it
    # refers to are the table this key reads. The largest figure anywhere in
    # that table sets the abscissa of the right panel, so the wedges are drawn
    # over the whole range the standard permits rather than up to one clause's
    # share of it, and the dashed rule of that panel says whose share the
    # 4.5 % is so the rest of the axis is not read as available to this test.
    clause = "12.11.2"
    uncertainty = vibration.MAX_EXPANDED_UNCERTAINTY_PERCENT[clause]
    widest = max(vibration.MAX_EXPANDED_UNCERTAINTY_PERCENT.values())
    transitions = vibration.TRANSITION_FREQUENCIES_HZ[name]
    ft1, ft2, ft3, ft4 = transitions
    fmin, fmax = 0.1, 400.0
    # The same limits the panels are drawn against, unpacked once so no label
    # can write a number the drawing did not use.
    central_upper, central_lower = vibration.CENTRAL_TOLERANCE_PERCENT[:2]
    skirt_upper, skirt_lower = vibration.SKIRT_TOLERANCE_PERCENT[:2]

    # The bench sweep. 12.11.1 asks for steps of not more than one-third
    # octave, and the centres are built from Formula (B.1) rather than typed
    # as decimals: 63.096 written as the printed 63.1 rounds up past ft3 and
    # would be graded against the skirt instead of the central region. The
    # sweep runs past the nominal 0.5 Hz to 80 Hz of Table 1 at both ends,
    # because the two tails are where the exemption lives and nothing inside
    # the nominal range reaches them.
    bands = np.arange(-8, 25)
    freqs = 10.0 ** (bands / 10.0)
    # Table 4 gives Wk's four corners as the same powers of ten, so four of
    # those centres are a transition frequency and are set to the table's own
    # value rather than left as a second, arithmetically equal double.
    # ``pow`` is one of the libm entry points whose last bit is not the same
    # on every platform, and a centre landing one bit over ft1 would be
    # graded against the skirt instead of the tail: it would grow a second
    # arm and change verdict, on a figure that has to draw the same on every
    # machine. (The row is closed at ft1 and open above it, so it is the bit
    # above that crosses; the snap protects both directions either way.)
    for corner in transitions:
        freqs[np.isclose(freqs, corner, rtol=1e-9, atol=0.0)] = corner
    # The measurement, as deviations from the design goal in per cent. Every
    # one of them is inside the printed band of its region, so this is a
    # sweep that conforms on the bare comparison; the two that sit within
    # 4.5 % of a limit are the whole subject of the figure. The band at
    # 10**0.8 Hz reading 9 % high is the section's own worked example.
    deviations = np.array(
        [
            -27.0, -24.0, -21.0, -13.0, -9.0, -6.0, -4.0, -2.0, -0.5, 1.0,
            2.0, 2.5, 3.0, 3.5, 4.5, 6.5, 9.0, 6.0, 4.0, 2.5,
            1.5, 0.5, -0.5, -1.5, -3.0, -4.5, -6.0, -9.0, -13.0, -17.5,
            -22.0, -25.0, -28.0,
        ]
    )  # fmt: skip
    design = np.asarray(vibration.weighting_factors(name, freqs))
    measured = design * (1.0 + deviations / 100.0)
    # The verdict, and every reading the panel writes, come from here rather
    # than from the array above: the deviations are re-derived from the
    # measured factors exactly as a report would derive them.
    declared = vibration.verify_weighting(
        name, freqs, measured, expanded_uncertainty_percent=uncertainty
    )
    deviation = declared.deviation_percent
    kept = declared.within_tolerance
    refused = ~kept
    # The band the section's example lives in, found by its band index rather
    # than by its verdict, so the note keeps pointing at the same point.
    example = int(np.flatnonzero(bands == 8)[0])

    # The printed band, evaluated on the corners alone: the limits are
    # constant between the four transition frequencies, so a pair of points
    # either side of each of them draws the staircase exactly, and a grid
    # carrying no point at a step would draw it as a ramp.
    edges = np.array(
        [f * scale for f in transitions for scale in (1.0 - 1e-9, 1.0 + 1e-9)]
    )
    steps = np.unique(np.concatenate(([fmin, fmax], edges)))
    step_upper, step_lower = vibration.weighting_tolerance_percent(name, steps)
    step_masks = _table_5_masks(steps, transitions)

    # The three distinct rows of Table 5, in the colours the tolerance-regions
    # figure of the same guide gives them, so the two drawings name the same
    # region with the same ink. The pair is the magnitude column; the phase
    # column is that figure's subject and not this one's.
    regions = (
        (
            COLOR_PRIMARY,
            "the central region of Table 5",
            (central_upper, central_lower),
        ),
        (COLOR_TERTIARY, "the two skirts of Table 5", (skirt_upper, skirt_lower)),
        (
            COLOR_MUTED,
            "the two tails, with no lower limit",
            vibration.TAIL_TOLERANCE_PERCENT[:2],
        ),
    )

    fig = plt.figure(figsize=(13.2, 6.6))
    grid_spec = fig.add_gridspec(1, 2, width_ratios=[1.62, 1.0], wspace=0.06)
    ax_sweep = fig.add_subplot(grid_spec[0, 0])
    ax_window = fig.add_subplot(grid_spec[0, 1], sharey=ax_sweep)

    # Left: the band, unchanged by anything on this page. The lower edge of a
    # tail is -100 %, which is the absence of a limit rather than a value, so
    # the fill runs off the bottom of the panel and the boundary line is
    # simply not drawn there: an outline along some floor would read as a
    # limit that is not in the table.
    for (colour, region, _limits), mask in zip(regions, step_masks, strict=True):
        ax_sweep.fill_between(
            steps,
            step_lower,
            step_upper,
            where=mask,
            color=theme_fill(colour, ax_sweep),
            zorder=0,
            label=region,
        )
    ax_sweep.plot(
        steps, step_upper, color=COLOR_FG, linewidth=1.2, alpha=0.75, zorder=2
    )
    ax_sweep.plot(
        steps,
        np.where(step_lower > vibration.UNCONSTRAINED_BELOW, step_lower, np.nan),
        color=COLOR_FG,
        linewidth=1.2,
        alpha=0.75,
        zorder=2,
    )
    ax_sweep.axhline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.35, zorder=1)
    for frequency in transitions:
        ax_sweep.axvline(
            frequency,
            color=COLOR_MUTED,
            linestyle="--",
            linewidth=1.0,
            alpha=0.8,
            zorder=1,
        )

    # The bar 13.1 adds, and the one place it has only one arm. Where the
    # lower limit is -100 % the verification subtracts nothing, so drawing a
    # downward arm there would draw a comparison the library does not make.
    _point_upper, point_lower = vibration.weighting_tolerance_percent(name, freqs)
    unconstrained = point_lower <= vibration.UNCONSTRAINED_BELOW
    arms = np.vstack(
        (
            np.where(unconstrained, 0.0, uncertainty),
            np.full(freqs.shape, uncertainty),
        )
    )
    for mask, colour, marker, size, order, label in (
        (kept, COLOR_FG, "o", 4.5, 4, "the extended deviation conforms"),
        (refused, COLOR_SECONDARY, "X", 8.5, 5, "the extended deviation is refused"),
    ):
        ax_sweep.errorbar(
            freqs[mask],
            deviation[mask],
            yerr=arms[:, mask],
            color=colour,
            marker=marker,
            markersize=size,
            linestyle="none",
            elinewidth=1.2,
            capsize=2.5,
            zorder=order,
            label=label,
        )

    # The arithmetic of the refusal, over the point it refuses. Every number
    # in it is read back out of the arrays that placed the point and out of
    # the constants that drew the band.
    example_hz = float(freqs[example])
    example_deviation = float(deviation[example])
    ax_sweep.text(
        example_hz,
        20.5,
        f"at {example_hz:.3g} Hz the deviation is {example_deviation:.0f} %,\n"
        f"inside the +{central_upper:.0f} % of the central region;\n"
        f"{example_deviation:.0f} % + {uncertainty:.4g} % = "
        f"{example_deviation + uncertainty:.4g} % is not, and\n"
        "clause 13.1 grades the extended figure",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    # The exemption, in the empty band between the two tails: below the
    # central floor and above the deepest point of either tail.
    ax_sweep.text(
        math.sqrt(ft2 * ft3),
        -25.5,
        "in the two tails the bar has one arm:\n"
        "there is no lower limit to extend, so a\n"
        "channel reading nothing at all conforms",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    ax_sweep.set_xscale("log")
    ax_sweep.set_xlim(fmin, fmax)
    # The same six ticks as the tolerance-regions figure of this guide, and
    # for the same reason: the four numbers of Table 4 are read off the axis
    # rather than off a chip over the data, and every region edge lands on a
    # labelled tick. The labels are formatted from the values that place
    # them, so a number cannot be written under a rule it no longer marks.
    ticks = (0.1, ft1, ft2, 10.0, ft3, ft4)
    ax_sweep.set_xticks(list(ticks))
    ax_sweep.set_xticklabels([f"{value:.4g}" for value in ticks], fontsize=9)
    ax_sweep.xaxis.set_minor_formatter(NullFormatter())
    ax_sweep.set_xlabel(LABEL_FREQ_HZ)
    ax_sweep.set_ylabel("Deviation from the design goal (%)")
    # The panel is titled by what the bar is rather than by the clause that
    # adds it: the number belongs to the chip that spells the comparison out,
    # and the height of the bar comes from a clause of a different level of
    # testing, so the two numbers are best kept one to a place.
    ax_sweep.set_title(
        "What the Laboratory's Own Uncertainty Adds to Each Point", pad=8
    )

    # Right: the same comparison solved for the deviation instead. A region
    # whose limits are (upper, lower) certifies from lower + U to upper - U,
    # so each row of Table 5 is a wedge narrowing as U grows, and the two
    # limits are straight lines because the extension is a subtraction. Two
    # abscissae are enough for a straight line, and the wedges are drawn
    # widest first so the narrower ones sit on top.
    u_axis = np.array([0.0, widest])
    for colour, _region, (upper, lower) in reversed(regions):
        floor = (
            np.full(u_axis.shape, lower)
            if lower <= vibration.UNCONSTRAINED_BELOW
            else lower + u_axis
        )
        ax_window.fill_between(
            u_axis,
            floor,
            upper - u_axis,
            color=theme_fill(colour, ax_window),
            zorder=0,
        )
    for _colour, _region, (upper, lower) in regions:
        if lower <= vibration.UNCONSTRAINED_BELOW:
            # The tail shares its ceiling with the skirt and has no floor, so
            # it contributes no edge of its own.
            continue
        for limit in (upper - u_axis, lower + u_axis):
            ax_window.plot(
                u_axis, limit, color=COLOR_FG, linewidth=1.2, alpha=0.75, zorder=2
            )
    ax_window.axhline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.35, zorder=1)

    # What 12.11.2 costs, marked on the wedge it narrows.
    window_upper = central_upper - uncertainty
    window_lower = central_lower + uncertainty
    ax_window.axvline(
        uncertainty,
        color=COLOR_MUTED,
        linestyle="--",
        linewidth=1.0,
        alpha=0.8,
        zorder=1,
    )
    ax_window.plot(
        [uncertainty, uncertainty],
        [window_lower, window_upper],
        color=COLOR_FG,
        linewidth=1.6,
        marker="_",
        markersize=9,
        zorder=3,
    )
    # The rule is labelled with whose ceiling it is, not just with its
    # height: the abscissa runs to the largest figure the clause table permits
    # anywhere, and without this the half per cent beyond the rule reads as
    # available to the test the left panel grades, which may not carry it.
    # Right-aligned so the chip ends on the rule it names and clears the right
    # spine, and lifted above the skirt ceiling so it crosses no boundary.
    ax_window.text(
        uncertainty,
        27.0,
        f"{uncertainty:.4g} %, the most clause {clause} allows",
        fontsize=9,
        color=COLOR_FG,
        ha="right",
        va="bottom",
        zorder=6,
        # Over its own dashed rule, so the reading carries a chip.
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    ax_window.text(
        0.5 * widest,
        17.0,
        f"a bench carrying {uncertainty:.4g} % can certify\n"
        f"only {_fmt_minus(window_lower, '.4g')} % to "
        f"+{window_upper:.4g} %, where\n"
        f"Table 5 prints {_fmt_minus(central_lower, '.0f')} % to "
        f"+{central_upper:.0f} %",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    ax_window.set_xlim(0.0, widest)
    ax_window.set_xticks(np.arange(0.0, widest + 1.0, 1.0))
    ax_window.set_xlabel(
        "Expanded uncertainty $U$ of the laboratory (%), "
        f"$k$ = {vibration.ISO8041_COVERAGE_FACTOR:.0f}"
    )
    ax_window.set_title("What a Bench Carrying $U$ Can Certify", pad=8)
    ax_window.tick_params(axis="y", labelleft=False)

    # One deviation axis for both panels, ticked at the four graded limits of
    # Table 5 and at zero, and labelled from the same constants that place the
    # ticks. Sharing it is what lets the reader carry a height across: the
    # 9 % of the left panel is the height the right panel's central wedge has
    # already fallen below at 4.5 %.
    tolerance_ticks = (skirt_upper, central_upper, 0.0, central_lower, skirt_lower)
    ax_sweep.set_yticks(list(tolerance_ticks))
    ax_sweep.set_yticklabels([_signed_percent(value) for value in tolerance_ticks])
    ax_sweep.set_ylim(-33.0, 31.0)
    for panel in (ax_sweep, ax_window):
        panel.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
        panel.set_axisbelow(True)

    # One key at the foot of the figure: the three regions carry the same
    # colour on both panels, so a box per panel would say it twice, and the
    # two marker classes belong to the left one alone. The row clears the
    # frequency labels above it because the margins below hold the panels off
    # the foot of the figure.
    handles, names = ax_sweep.get_legend_handles_labels()
    fig.legend(handles, names, loc="lower center", ncol=5, fontsize=8.5, frameon=False)
    fig.suptitle(
        "The Band Does Not Move: ISO 8041-1 Extends the Measurement Instead",
        fontsize=13,
    )
    # The margins are set by hand, as the tolerance-regions figure of this
    # guide sets them and for the same reason: ``tight_layout`` declines a
    # gridspec whose subplot parameters were set on the gridspec itself, and
    # it would warn, leave the defaults in place and undo the ``wspace``
    # above. The foot holds the key clear of the frequency labels, and the
    # head holds the two panel titles clear of the suptitle.
    fig.subplots_adjust(left=0.062, right=0.988, top=0.875, bottom=0.155)
    save_figure(output_dir, "meter_uncertainty_allowance.svg")
    plt.close()


def _decay_criterion_fraction(decay_time_s: float, integration_time_s: float) -> float:
    """The 10 % of clause 5.13, read back out of the library's closed form.

    The clause times the fall down to a fraction of the initial indicated
    value, and that fraction is the one number of the test the library keeps
    private. It is recoverable exactly, because the exponential average's
    closed form is ``t = -2 tau ln(f)``: the fraction is ``exp(-t / 2 tau)`` of
    the time :func:`running_rms_decay_time` returns for that same average.
    Reading it back rather than typing it in is what keeps the rule the
    crossings are timed at, the per cent its label writes and the printed bands
    drawn around it from ever disagreeing.
    """
    return math.exp(-0.5 * decay_time_s / integration_time_s)


def _printed_decay_time(
    rows: tuple[tuple[float, float, float], ...], integration_time_s: float
) -> tuple[float, float]:
    """The printed decay time and its tolerance, for one time constant.

    Tables 10 and 11 are keyed by the averaging time rather than ordered, and
    ``verify_running_rms_decay`` reads them that way too, so the row is looked
    up rather than indexed: a row added between the printed three would then
    move nothing in the drawing.
    """
    matched = [
        (printed, tolerance)
        for constant, printed, tolerance in rows
        if math.isclose(constant, integration_time_s, rel_tol=1e-9, abs_tol=0.0)
    ]
    if len(matched) != 1:
        msg = f"{integration_time_s} s is not one printed row of the decay tables."
        raise ValueError(msg)
    return matched[0]


def _relative_level_db(relative: np.ndarray) -> np.ndarray:
    """A decay trace as a level below the indication it started from.

    The linear average empties: once its sliding window holds nothing but the
    zeros after the cut, the mean square in it is exactly zero and a level is
    not defined there. Those samples are dropped rather than floored, so the
    curve stops at the last sample that has a level instead of running along a
    horizontal line at whatever floor the panel happens to use, which is a
    reading the standard never drew.
    """
    level_db = np.full(relative.shape, np.nan)
    positive = relative > 0.0
    level_db[positive] = 20.0 * np.log10(relative[positive])
    return level_db


def generate_meter_running_rms_decay(output_dir: str) -> None:
    """ISO 8041-1 5.13: how long the running r.m.s. takes to forget.

    Both averages falling away from the cut, the printed bands of Tables 10
    and 11 their crossings have to land in, and the decay-rate column that is
    deliberately not the criterion. A stopwatch, not a certificate: conformity
    also takes the indication, linearity, overload, burst and environmental
    clauses, which are measurements on hardware.
    """
    print("Generating meter_running_rms_decay...")
    from phonometry import vibration

    name = "Wk"
    tau_s = 1.0
    fs_hz = 2000.0
    cut_s = 10.0
    # The width of the top panel, in seconds after the cut: past the printed
    # band of the slower average, with room on the right for the reading of
    # the criterion rule.
    view_s = 6.2

    # The test signal of 5.13: a steady sinusoid at the reference frequency of
    # the weighting under test, shut off at ``cut_s``. It is applied already
    # weighted, because the time weighting sits after the frequency weighting
    # in the chain. The amplitude is immaterial, since the test times a fall
    # to a fraction of whatever the indication was; root two puts the steady
    # indication at 1 m/s2. The fill before the cut is ten time constants,
    # which is twice the five the clause asks of the linear average; the
    # exponential average is asked for twenty, and at ten its transient is
    # 45 parts per million of the mean square, two orders of magnitude under
    # the ripple that actually sets where the initial value falls.
    excitation_hz = vibration.REFERENCE_FREQUENCY_HZ[name]
    sample_times = np.arange(round(2.0 * cut_s * fs_hz)) / fs_hz
    excitation = math.sqrt(2.0) * np.sin(2.0 * math.pi * excitation_hz * sample_times)
    excitation[sample_times >= cut_s] = 0.0
    cut_index = round(cut_s * fs_hz)
    # Time since the cut, counted in samples rather than by subtracting the
    # cut from the clock, so the axis starts at exactly zero.
    since_cut = np.arange(sample_times.size - cut_index) / fs_hz

    closed_form_s = {
        method: vibration.running_rms_decay_time(tau_s, method=method)
        for method in ("linear", "exponential")
    }
    fraction = _decay_criterion_fraction(closed_form_s["exponential"], tau_s)
    criterion_db = 20.0 * math.log10(fraction)

    # The two averages, measured. The crossing is timed the way the clause
    # words it, on the indication itself: the first sample whose value is less
    # than the fraction of the initial one, not the first sample of a level.
    measured_db: dict[str, np.ndarray] = {}
    crossing_s: dict[str, float] = {}
    for method in ("linear", "exponential"):
        trace = np.asarray(
            vibration.running_rms(
                excitation, fs_hz, integration_time=tau_s, method=method
            ),
            dtype=np.float64,
        )
        relative = trace[cut_index:] / float(trace[cut_index - 1])
        measured_db[method] = _relative_level_db(relative)
        crossing_s[method] = float(since_cut[np.flatnonzero(relative < fraction)[0]])

    # The same two falls in closed form, as 5.13 gives them: the linear
    # average keeps the last tau seconds of the record, so a time t after the
    # cut its window still holds (tau - t) / tau of the original mean square;
    # the exponential average decays in power as exp(-t / tau).
    closed_db = {
        "linear": _relative_level_db(
            np.sqrt(np.clip(1.0 - since_cut / tau_s, 0.0, None))
        ),
        "exponential": _relative_level_db(np.exp(-0.5 * since_cut / tau_s)),
    }

    # One colour per average, on both panels that draw one, and one colour per
    # printed column, on both panels that draw one.
    averages = (
        (
            "linear",
            COLOR_PRIMARY,
            f"the linear average of Table 10 ($\\tau$ = {tau_s:g} s)",
        ),
        (
            "exponential",
            COLOR_TERTIARY,
            f"the exponential average of Table 11 ($\\tau$ = {tau_s:g} s)",
        ),
    )
    # The band and the first bar of the third panel are the same printed
    # column drawn twice, in seconds and as a multiple, so both names carry
    # which of the two it is. Named only by what they are, they read as two
    # entries saying the same thing, which is what the first draft of the key
    # did.
    band_label = "the printed decay time and its tolerance, in seconds"
    time_column_label = "the time column of Table 11, as a multiple"
    rate_label = "the rate column of Table 11, read as a decay time"

    fig = plt.figure(figsize=(13.2, 7.6))
    grid_spec = fig.add_gridspec(
        2,
        2,
        height_ratios=[1.32, 1.0],
        width_ratios=[1.2, 1.0],
        hspace=0.36,
        wspace=0.16,
    )
    ax_decay = fig.add_subplot(grid_spec[0, :])
    ax_zoom = fig.add_subplot(grid_spec[1, 0])
    ax_columns = fig.add_subplot(grid_spec[1, 1])

    # --- Top: both falls, the criterion, and the two printed bands ----------
    #
    # The linear average lives for one time constant and the last hundredth of
    # it is the point of the figure, so it is drawn sample by sample and
    # stopped at its last defined sample. The exponential average is a
    # straight line on this axis for six seconds, so it is drawn every tenth
    # sample: 5 ms of drawn resolution, four points across the fastest ripple
    # the average can pass, and a tenth of the vertices.
    stride = {"linear": 1, "exponential": round(0.005 * fs_hz)}
    view_stop = round(view_s * fs_hz) + 1
    for method, colour, label in averages:
        defined = np.flatnonzero(np.isfinite(measured_db[method]))
        shown = slice(0, min(int(defined[-1]) + 1, view_stop), stride[method])
        ax_decay.plot(
            since_cut[shown],
            measured_db[method][shown],
            color=colour,
            linewidth=1.9,
            zorder=3,
            label=label,
        )
    for index, (method, _colour, _label) in enumerate(averages):
        defined = np.flatnonzero(np.isfinite(closed_db[method]))
        shown = slice(0, min(int(defined[-1]) + 1, view_stop), stride[method])
        ax_decay.plot(
            since_cut[shown],
            closed_db[method][shown],
            color=COLOR_MUTED,
            linewidth=1.1,
            linestyle="--",
            zorder=2,
            label="the closed form of each average" if index == 0 else "_nolegend_",
        )
    ax_decay.axhline(criterion_db, color=COLOR_FG, linewidth=1.0, alpha=0.55, zorder=1)
    # The printed bands, and the chip that reads each one against the trace
    # that has to land in it. Both chips sit in the empty quarter under the
    # exponential fall, with an arrow to the crossing they belong to, so
    # neither of them covers a stroke.
    chip = {
        "boxstyle": "round,pad=0.35",
        "facecolor": COLOR_PANEL,
        "edgecolor": COLOR_GRID,
    }
    chip_at = {"linear": (1.30, -23.5), "exponential": (2.45, -31.0)}
    printed_row = {
        method: _printed_decay_time(vibration.RUNNING_RMS_DECAY_TIME_S[method], tau_s)
        for method, _colour, _label in averages
    }
    for index, (method, colour, _label) in enumerate(averages):
        printed, tolerance = printed_row[method]
        ax_decay.axvspan(
            printed - tolerance,
            printed + tolerance,
            color=theme_fill(COLOR_SECONDARY, ax_decay),
            zorder=0,
            label=band_label if index == 1 else "_nolegend_",
        )
        ax_decay.plot(
            [crossing_s[method]],
            [criterion_db],
            marker="o",
            markersize=5.5,
            color=colour,
            zorder=4,
        )
        table = "Table 10" if method == "linear" else "Table 11"
        ax_decay.annotate(
            f"{table} prints {printed:g} ± {tolerance:g} s;\n"
            f"the trace crosses at {crossing_s[method]:.2f} s",
            xy=(crossing_s[method], criterion_db),
            xytext=chip_at[method],
            fontsize=9,
            color=colour,
            ha="left",
            va="center",
            zorder=5,
            bbox=chip,
            arrowprops={"arrowstyle": "->", "lw": 0.9, "color": colour},
        )
    # Three short lines rather than two long ones, and the clause named as
    # "clause 5.13" rather than as a bare "5.13". Both are the Spanish twin
    # talking: the translated sentence is a third longer, and at two lines it
    # reached back over the exponential fall; and the save-time decimal pass
    # rewrites a bare "5.13" as "5,13" unless one of the reference words it
    # knows ("apartado") stands in front of it, which is a clause number
    # printed as a number and a half.
    ax_decay.text(
        view_s - 0.1,
        criterion_db + 0.9,
        f"clause 5.13 times the fall to here:\n"
        f"{fraction * 100.0:.0f} % of the initial indication,\n"
        f"which is {_fmt_minus(criterion_db, '.0f')} dB",
        fontsize=9,
        color=COLOR_FG,
        ha="right",
        va="bottom",
        zorder=5,
        bbox=chip,
    )

    decay_ticks = (0.0, -10.0, criterion_db, -30.0)
    ax_decay.set_ylim(-34.0, 1.6)
    ax_decay.set_yticks(list(decay_ticks))
    ax_decay.set_yticklabels([_fmt_minus(value, ".0f") for value in decay_ticks])
    ax_decay.set_title("The Two Averages Falling Away From the Cut", pad=10)

    # --- Bottom left: the last tenth of a second of the linear fall ---------
    printed, tolerance = printed_row["linear"]
    ax_zoom.axvspan(
        printed - tolerance,
        printed + tolerance,
        color=theme_fill(COLOR_SECONDARY, ax_zoom),
        zorder=0,
    )
    ax_zoom.axhline(criterion_db, color=COLOR_FG, linewidth=1.0, alpha=0.55, zorder=1)
    ax_zoom.plot(
        since_cut,
        closed_db["linear"],
        color=COLOR_MUTED,
        linewidth=1.2,
        linestyle="--",
        zorder=2,
    )
    ax_zoom.plot(
        since_cut, measured_db["linear"], color=COLOR_PRIMARY, linewidth=1.9, zorder=3
    )
    # Two readings on one rule: where the closed form reaches the criterion,
    # which is the number Table 10 rounds and prints, and where the measured
    # trace does.
    ax_zoom.plot(
        [closed_form_s["linear"]],
        [criterion_db],
        marker="o",
        markersize=5.5,
        color=COLOR_MUTED,
        zorder=4,
    )
    ax_zoom.plot(
        [crossing_s["linear"]],
        [criterion_db],
        marker="o",
        markersize=5.5,
        color=COLOR_PRIMARY,
        zorder=4,
    )
    ax_zoom.text(
        printed + tolerance + 0.016,
        -6.6,
        "at the crossing the sliding window holds only\n"
        f"the last few samples of the {excitation_hz:g} Hz sinusoid,\n"
        "and their mean square depends on where in\n"
        "the cycle the signal was cut",
        fontsize=8.5,
        color=COLOR_FG,
        ha="right",
        va="top",
        zorder=5,
        bbox=chip,
    )
    # Which dot is which, and the two readings the panel exists to compare.
    # The chip above says why they differ, and said it without naming either
    # of them: the reader had to carry the colour code down from the top
    # panel to tell the measurement from the closed form. Each label sits
    # against its own marker, so proximity names it even where the colour
    # cannot: the measured one takes the colour of its trace, and the closed
    # form takes the foreground, because COLOR_MUTED is a neutral for
    # de-emphasised data and at 8.5 points on the chip it is not a readable
    # ink on either page.
    ax_zoom.text(
        crossing_s["linear"] - 0.005,
        criterion_db - 1.6,
        f"the measured crossing, {crossing_s['linear']:.2f} s",
        fontsize=8.5,
        color=COLOR_PRIMARY,
        ha="right",
        va="top",
        zorder=5,
        bbox=chip,
    )
    ax_zoom.text(
        closed_form_s["linear"] + 0.005,
        criterion_db + 1.2,
        f"the closed form, {closed_form_s['linear']:.2f} s",
        fontsize=8.5,
        color=COLOR_FG,
        ha="left",
        va="bottom",
        zorder=5,
        bbox=chip,
    )
    zoom_ticks = (printed - tolerance, printed, printed + tolerance)
    ax_zoom.set_xlim(0.90, printed + tolerance + 0.02)
    ax_zoom.set_xticks(list(zoom_ticks))
    ax_zoom.set_xticklabels([f"{value:.4g}" for value in zoom_ticks])
    ax_zoom.set_ylim(-32.0, -6.0)
    ax_zoom.set_yticks([-10.0, criterion_db, -30.0])
    ax_zoom.set_yticklabels(
        [_fmt_minus(value, ".0f") for value in (-10.0, criterion_db, -30.0)]
    )
    ax_zoom.set_title("The Linear Crossing, Sample by Sample", pad=8)

    # --- Bottom right: Table 11's two columns, against its own closed form --
    #
    # A decay rate is a time only once a distance is fixed, and the clause
    # fixes it: the criterion is the same 10 %, so a rate R reaches it in
    # (0 dB - criterion) / R seconds. Both columns then live on one axis, and
    # the axis is dimensionless because each row is divided by the closed form
    # of its own time constant.
    columns = (
        (COLOR_SECONDARY, time_column_label, 0.19),
        (COLOR_QUATERNARY, rate_label, -0.19),
    )
    constants = []
    for index, (constant, lower_rate, upper_rate) in enumerate(
        vibration.RUNNING_RMS_DECAY_RATE_DB_PER_S
    ):
        constants.append(constant)
        closed_s = vibration.running_rms_decay_time(constant, method="exponential")
        printed, tolerance = _printed_decay_time(
            vibration.RUNNING_RMS_DECAY_TIME_S["exponential"], constant
        )
        intervals = (
            ((printed - tolerance) / closed_s, (printed + tolerance) / closed_s),
            (
                -criterion_db / (upper_rate * closed_s),
                -criterion_db / (lower_rate * closed_s),
            ),
        )
        for (colour, label, offset), (low, high) in zip(
            columns, intervals, strict=True
        ):
            ax_columns.barh(
                index + offset,
                high - low,
                left=low,
                height=0.3,
                color=theme_fill(colour, ax_columns),
                edgecolor=colour,
                linewidth=1.3,
                zorder=2,
                label=label if index == 0 else "_nolegend_",
            )
    ax_columns.axvline(1.0, color=COLOR_FG, linewidth=1.0, alpha=0.55, zorder=1)
    # Hung off the top of the frame rather than off a row of the data. Placed
    # at a y in data units it stood a fixed number of points tall in a panel
    # whose data units are rows, so it ran over the top spine and cut it: the
    # spine is drawn, the chip is opaque, and the frame came out broken in all
    # four variants. Anchored in axes coordinates it cannot leave the panel,
    # and the head room that keeps it off the top bar is made by the ylim
    # below rather than by the placement.
    ax_columns.text(
        0.5,
        0.96,
        f"a decay rate of $R$ dB/s reaches the same {fraction * 100.0:.0f} % in "
        f"{-criterion_db:.0f}/$R$ s;\nin all three printed rows the time column "
        "is the narrower statement",
        transform=ax_columns.transAxes,
        fontsize=8.5,
        color=COLOR_FG,
        ha="center",
        va="top",
        zorder=5,
        bbox=chip,
    )
    column_ticks = np.arange(0.85, 1.16, 0.05)
    ax_columns.set_xlim(0.84, 1.18)
    ax_columns.set_xticks(list(column_ticks))
    ax_columns.set_xticklabels([f"{value:.2f}" for value in column_ticks])
    ax_columns.set_xlabel("Decay time, as a multiple of $2\\tau\\ln 10$")
    ax_columns.set_ylim(-0.62, len(constants) + 0.6)
    ax_columns.set_yticks(list(range(len(constants))))
    ax_columns.set_yticklabels([f"{value:g}" for value in constants])
    ax_columns.set_ylabel("Averaging time $\\tau$ [s]")
    ax_columns.set_title("Table 11's Two Columns, Against Its Own Closed Form", pad=8)

    for panel in (ax_decay, ax_zoom):
        panel.set_xlabel("Time since the signal was cut [s]")
        panel.set_ylabel("Indication, relative to its initial value [dB]")
    decay_x_ticks = np.arange(0.0, view_s, 1.0)
    ax_decay.set_xlim(0.0, view_s)
    ax_decay.set_xticks(list(decay_x_ticks))
    ax_decay.set_xticklabels([f"{value:g}" for value in decay_x_ticks])
    for panel in (ax_decay, ax_zoom, ax_columns):
        panel.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
        panel.set_axisbelow(True)

    # One key at the foot of the figure: the two averages and the closed form
    # are the same colours on the two panels that draw a fall, and the printed
    # decay time is the same colour on the two panels that draw it, so a box
    # per panel would say the same five things twice.
    handles, names = ax_decay.get_legend_handles_labels()
    extra_handles, extra_names = ax_columns.get_legend_handles_labels()
    fig.legend(
        handles + extra_handles,
        names + extra_names,
        loc="lower center",
        ncol=3,
        fontsize=8.5,
        frameon=False,
    )
    fig.suptitle(
        "The Running r.m.s. Decay of ISO 8041-1: Tables 10 and 11, Timed From the Cut",
        fontsize=13,
    )
    # The margins are set by hand rather than by ``tight_layout``, which
    # declines a gridspec with a panel spanning two columns: it would warn,
    # leave the defaults in place and undo the ``hspace`` and ``wspace`` above.
    # The foot holds the two-row key clear of the frequency-of-use labels, and
    # the head holds the three panel titles clear of the suptitle.
    fig.subplots_adjust(left=0.062, right=0.986, top=0.878, bottom=0.155)
    save_figure(output_dir, "meter_running_rms_decay.svg")
    plt.close()


def _burst_deviation(value: float) -> str:
    """One cell's deviation, written as the sentence beside it needs it.

    ``_signed_percent``, which the tolerance-region figure of this guide
    already carries, rounds to whole per cent for a tick label; a deviation
    read out inside a sentence keeps its tenth, and it keeps the U+2212 that
    ``format`` would write as an ASCII hyphen.
    """
    if value < 0.0:
        return f"{_fmt_minus(value, '.1f')} %"
    return f"+{value:.1f} %"


def _record_envelope(
    record: np.ndarray, fs: float, bins: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The record reduced to ``bins`` (centre, minimum, maximum) columns.

    A minute of record at any honest sampling rate is more vertices than a
    vector figure can carry, and drawing every n-th sample of a saw-tooth is
    the one reduction that lies: it reports whichever phase the stride lands
    on. The extremes of each bin are what the ink of the full trace would
    cover, so a stepped fill between them is the record at this scale.

    The bin that straddles the edge of a burst holds part signal and part
    silence, so it is drawn short: a notch of one bin, about a pixel at the
    size the page delivers, and the true extremes of that window rather than
    an artefact. No bin count removes it. At 200 samples per cycle a burst is
    exactly 3200 samples, but the bursts begin 31 831 samples apart and the
    first begins at sample 3184, whose greatest common divisor with the rest
    is 1: only a bin of one sample, which is the whole record and the reason
    this function exists, would start and end all six on a bin boundary.
    """
    block = record.size // bins
    frames = record[: block * bins].reshape(bins, block)
    return (
        (np.arange(bins) + 0.5) * block / fs,
        frames.min(axis=1),
        frames.max(axis=1),
    )


def generate_meter_signal_burst_response(output_dir: str) -> None:
    """ISO 8041-1 5.9: the saw-tooth burst, and a meter Table 8 catches.

    The signal of Table 6, and the deviations of one instrument against the
    printed cells of Table 8. A row inside the band says the time response of
    that weighting chain matches the printed table, and nothing else.
    """
    print("Generating meter_signal_burst_response...")
    from phonometry import vibration

    application = "whole-body"
    name = "Wk"
    test = vibration.SAWTOOTH_BURST_TESTS[application]
    longest = test.cycle_counts[-1]
    burst_span_s = longest / test.frequency_hz

    # The record, drawn at 200 samples per saw-tooth cycle. Not the rate the
    # indications are computed at: those run at the recommended 20 kHz, where
    # a minute of record is 1.2 million samples, and a vector figure cannot
    # carry a million vertices. A whole number of samples per cycle keeps
    # every tooth of the drawn burst identical, and the phase the sampling
    # lands on costs the peak 0.1 %.
    draw_fs = 200.0 * test.frequency_hz
    record = vibration.sawtooth_burst(application, longest, fs=draw_fs)
    record_times = np.arange(record.size) / draw_fs
    times, low, high = _record_envelope(record, draw_fs, 750)

    # The first burst, sliced with the inequality the library fills it by, so
    # the panel holds the samples that are in the burst and no others.
    inside = (record_times >= test.start_time_s) & (
        record_times < test.start_time_s + burst_span_s
    )
    burst_cycles = (record_times[inside] - test.start_time_s) * test.frequency_hz

    # The indications, once, and then two verdicts off the same numbers: the
    # chain as the library computes it, and the same chain with the
    # exponential MTVV reported in the linear column.
    rows = {
        cycles: vibration.signal_burst_indications(application, name, cycles)
        for cycles in (*test.cycle_counts, None)
    }
    honest = vibration.verify_signal_burst_response(application, name, rows)
    swapped = {
        cycles: {**row, "mtvv_linear": row["mtvv_exponential"]}
        for cycles, row in rows.items()
    }
    verdict = vibration.verify_signal_burst_response(application, name, swapped)

    fig = plt.figure(figsize=(13.4, 8.8))
    grid_spec = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.45])
    ax_record = fig.add_subplot(grid_spec[0, 0])
    ax_burst = fig.add_subplot(grid_spec[0, 1])
    ax_verdict = fig.add_subplot(grid_spec[1, :])

    # Top left: where the bursts sit. The x axis is ticked at the burst start
    # times themselves, so the start time and the repeat time of Table 6 are
    # read off the axis rather than off a chip.
    ax_record.fill_between(
        times,
        low,
        high,
        step="mid",
        color=COLOR_PRIMARY,
        linewidth=0.0,
        zorder=2,
    )
    starts = test.start_time_s + np.arange(test.burst_count) * test.repeat_time_s
    record_ticks = (*starts, test.duration_s)
    ax_record.set_xticks(list(record_ticks))
    ax_record.set_xticklabels([f"{value:g}" for value in record_ticks], fontsize=9)
    ax_record.set_xlim(0.0, test.duration_s)
    ax_record.set_ylim(-1.5, 2.1)
    ax_record.set_yticks([-1.0, 0.0, 1.0])
    ax_record.text(
        0.5 * test.duration_s,
        1.55,
        f"the whole-body row of Table 6: {test.burst_count} bursts of {longest}\n"
        f"cycles in a {test.duration_s:.0f} s record, the first at "
        f"{test.start_time_s:.0f} s and then one every "
        f"{test.repeat_time_s:.0f} s",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=5,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    ax_record.set_xlabel("Time [s]")
    ax_record.set_ylabel("acceleration [m/s²]")
    ax_record.set_title("Where the Bursts Sit in the Record", pad=8)

    # Top right: one burst, on an axis of saw-tooth cycles, so the five
    # printed burst lengths are ticks of the axis instead of marks over the
    # trace. Every shorter row is this same waveform stopped at one of them.
    ax_burst.plot(burst_cycles, record[inside], color=COLOR_PRIMARY, linewidth=1.0)
    crossings = np.array([0.0, *(float(count) for count in test.cycle_counts)])
    ax_burst.plot(
        crossings,
        np.zeros_like(crossings),
        marker="o",
        markersize=6,
        linestyle="none",
        color=COLOR_QUATERNARY,
        zorder=4,
    )
    ax_burst.set_xticks(list(crossings))
    ax_burst.set_xticklabels([f"{value:.0f}" for value in crossings], fontsize=9)
    ax_burst.set_xlim(-0.45, longest + 0.45)
    ax_burst.set_ylim(-1.5, 2.1)
    ax_burst.set_yticks([-1.0, 0.0, 1.0])
    ax_burst.text(
        0.5 * longest,
        1.55,
        "a linear rise and a vertical fall, and every printed length "
        f"starting\nand ending on an upward zero crossing: "
        f"{test.frequency_hz:.4f} Hz, {longest} cycles in {burst_span_s:.3f} s",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=5,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    ax_burst.set_xlabel("Saw-tooth cycles from the start of the burst")
    ax_burst.set_ylabel("acceleration [m/s²]")
    ax_burst.set_title("One Burst, and the Five Lengths the Tables Grade", pad=8)

    # Bottom: the verdict. The tolerance is per column, so the wider one is
    # drawn as a pair of edges over the same band rather than as a second
    # band under everything.
    positions = np.arange(len(verdict.cycle_counts), dtype=np.float64)
    # Bound here rather than at the ``set_xlim`` below, because the two
    # allowance stubs start at the left edge of the panel.
    x_left = -0.4
    x_right = positions[-1] + 0.42
    inner = float(np.min(verdict.tolerance_percent))
    outer = float(np.max(verdict.tolerance_percent))
    vdv_cells = sum(
        1 for cell in vibration.SIGNAL_BURST_RESPONSE.values() if "vdv" in cell
    )
    ax_verdict.axhspan(
        -inner,
        inner,
        color=theme_fill(COLOR_MUTED, ax_verdict),
        zorder=0,
        label=f"±{inner:.0f} %, the tolerance on every column but one",
    )
    # The wider allowance is one column's, so it is drawn as a pair of stubs
    # hanging off the axis beside their own ticks. Run across the panel, the
    # lower edge passes through the ring on the 8-cycle cell, and that cell is
    # graded on the narrower tolerance: the drawing would show a cell failing
    # against a limit that is not its own, which is the opposite of what the
    # legend says. Each stub ends half a step short of the first burst
    # length, where the panel draws nothing else.
    for index, edge in enumerate((-outer, outer)):
        ax_verdict.plot(
            (x_left, positions[0] + 0.5),
            (edge, edge),
            color=COLOR_MUTED,
            linestyle="--",
            linewidth=1.1,
            zorder=1,
            label=(
                f"±{outer:.0f} %, the one on the vibration dose value, in all "
                f"{vdv_cells} of its cells"
                if index == 0
                else None
            ),
        )
    ax_verdict.axhline(0.0, color=COLOR_FG, linewidth=0.8, alpha=0.4, zorder=1)
    ax_verdict.axvline(
        positions[-1] - 0.5,
        color=COLOR_MUTED,
        linestyle=":",
        linewidth=1.0,
        zorder=1,
    )

    # The column the defect lands in is drawn over the three that hug zero:
    # at the continuous row all four markers sit within a third of a per cent
    # of each other, and the one the panel is about has to be the visible one.
    styles = {
        # The panel title says what this meter does with the column, so the
        # legend row names it and stops there.
        "mtvv_linear": (COLOR_SECONDARY, "o", 2.0, "the linear MTVV column"),
        "vdv": (COLOR_TERTIARY, "s", 1.4, "the vibration dose value column"),
        "rms": (
            COLOR_PRIMARY,
            "^",
            1.2,
            "the r.m.s. and exponential MTVV columns, which the defect does not reach",
        ),
        "mtvv_exponential": (COLOR_PRIMARY, "v", 1.2, None),
    }
    for index, quantity in enumerate(verdict.quantities):
        colour, marker, width, label = styles[quantity]
        on_top = 3.5 if quantity == "mtvv_linear" else 3.0
        deviations = verdict.deviation_percent[:, index]
        # The burst rows carry a line between them because their abscissa is
        # ordered; the continuous row is not a burst length, so it is drawn
        # as a point of its own beyond the dotted rule.
        ax_verdict.plot(
            positions[:-1],
            deviations[:-1],
            color=colour,
            marker=marker,
            markersize=6,
            linewidth=width,
            zorder=on_top,
            label=label,
        )
        ax_verdict.plot(
            positions[-1:],
            deviations[-1:],
            color=colour,
            marker=marker,
            markersize=6,
            linestyle="none",
            zorder=on_top,
        )
    failed_rows, failed_columns = np.nonzero(~verdict.within_tolerance)
    ax_verdict.plot(
        positions[failed_rows],
        verdict.deviation_percent[failed_rows, failed_columns],
        marker="o",
        markersize=14,
        markerfacecolor="none",
        markeredgecolor=COLOR_SECONDARY,
        markeredgewidth=1.6,
        linestyle="none",
        zorder=4,
        label="the cells this meter fails",
    )

    linear = verdict.quantities.index("mtvv_linear")
    outside = [
        (cycles, deviation)
        for cycles, deviation, ok in zip(
            verdict.cycle_counts,
            verdict.deviation_percent[:, linear],
            verdict.within_tolerance[:, linear],
            strict=True,
        )
        if not ok
    ]
    lengths = " and ".join(f"{cycles}" for cycles, _ in outside)
    readings = " and ".join(_burst_deviation(value) for _, value in outside)
    ax_verdict.text(
        1.9,
        -17.5,
        f"only the {lengths} cycle rows leave the band, at\n{readings}: a test "
        "suite that ran only short\nbursts would have signed this meter off",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    ax_verdict.text(
        0.9,
        6.6,
        "read in the right column, the same chain reproduces\nall "
        f"{verdict.deviation_percent.size} of {name}'s printed cells to "
        f"{abs(honest.worst_deviation_percent):.2f} %",
        fontsize=9,
        color=COLOR_FG,
        ha="center",
        va="center",
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    ax_verdict.text(
        positions[-1] + 0.28,
        -9.0,
        "the continuous row passes too:\non a signal that never stops,\nthe two "
        "averages agree",
        fontsize=9,
        color=COLOR_FG,
        ha="right",
        va="center",
        zorder=6,
        bbox={
            "boxstyle": "round,pad=0.35",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )

    ax_verdict.set_xticks(list(positions))
    ax_verdict.set_xticklabels(
        [
            "continuous (no bursts)" if cycles is None else f"{cycles}"
            for cycles in verdict.cycle_counts
        ]
    )
    ax_verdict.set_xlim(x_left, x_right)
    ax_verdict.set_ylim(-24.0, 14.0)
    # The band edges and the two allowance edges, and one tick below them at
    # twice the printed tolerance. Without it the whole lower half of the
    # axis carries no number, and the deepest reading of the panel, which is
    # the headline of the section, could be read only off its chip.
    band_ticks = (-2.0 * inner, -outer, -inner, 0.0, inner, outer)
    ax_verdict.set_yticks(list(band_ticks))
    ax_verdict.set_yticklabels([_signed_percent(value) for value in band_ticks])
    ax_verdict.set_xlabel("Saw-tooth cycles per burst")
    ax_verdict.set_ylabel("Deviation from the printed cell [%]")
    ax_verdict.set_title(
        f"{name}: A Meter That Reports Its Exponential Average in the Linear Column",
        pad=8,
    )

    for panel in (ax_record, ax_burst):
        panel.grid(color=COLOR_GRID, linestyle="--", alpha=0.5)
        panel.set_axisbelow(True)
    # Vertical gridlines only on the verdict panel. A horizontal one lands on
    # a level the panel already draws at every tick but the lowest, and at
    # that one it would run through the ring on the 16-cycle cell. The first
    # call is the one that matters: ``axes.grid`` is on in the rcParams, so
    # the y gridlines have to be taken away rather than left unasked for.
    ax_verdict.grid(visible=False)
    ax_verdict.grid(visible=True, axis="x", color=COLOR_GRID, linestyle="--", alpha=0.5)
    ax_verdict.set_axisbelow(True)

    # One key for the whole drawing, in two rows of three: the column-major
    # fill puts the two tolerances together, then the two columns the defect
    # misses, then the column it lands in and the ring on its failing cells.
    # The labels are kept short enough for the key to stay narrower than the
    # drawing above it, and that is a constraint rather than taste:
    # ``savefig.bbox`` is "tight" for the whole corpus, so a key wider than
    # the panels grows the saved canvas instead of being clipped, and it grows
    # it by more in Spanish. Measured on this figure, the key is 812 pt in
    # English and 902 pt in Spanish against 939 pt of drawing, so both
    # editions save at the same width.
    handles, names = ax_verdict.get_legend_handles_labels()
    fig.legend(handles, names, loc="lower center", ncol=3, fontsize=8.5, frameon=False)
    total_cells = sum(len(cell) for cell in vibration.SIGNAL_BURST_RESPONSE.values())
    fig.suptitle(
        "The Saw-Tooth Burst of ISO 8041-1, and the "
        f"{total_cells} Numbers a Conforming Meter Has to Reproduce",
        fontsize=13,
    )
    fig.subplots_adjust(
        left=0.055, right=0.985, top=0.905, bottom=0.155, hspace=0.42, wspace=0.14
    )
    save_figure(output_dir, "meter_signal_burst_response.svg")
    plt.close()


def generate_kb_weighting(output_dir: str) -> None:
    """DIN 45669-1: the KB weighting over both working ranges (Formula (6))."""
    print("Generating kb_weighting...")
    from phonometry import vibration

    freqs = np.geomspace(0.2, 800.0, 600)
    building = np.abs(vibration.kb_weighting_response(freqs))
    railway = np.abs(vibration.kb_weighting_response(freqs, working_range="railway"))
    band = np.abs(vibration.band_limitation_response(freqs))

    _fig, ax = plt.subplots(figsize=(10, 6.2))
    ax.semilogx(
        freqs,
        20.0 * np.log10(band),
        color=COLOR_MUTED,
        linewidth=1.4,
        linestyle="--",
        label="band limitation alone, 1 Hz to 80 Hz",
    )
    ax.semilogx(
        freqs,
        20.0 * np.log10(building),
        color=COLOR_PRIMARY,
        linewidth=2.0,
        label="KB weighting, 1 Hz to 80 Hz",
    )
    ax.semilogx(
        freqs,
        20.0 * np.log10(railway),
        color=COLOR_TERTIARY,
        linewidth=2.0,
        label="KB weighting, 4 Hz to 315 Hz",
    )
    ax.axvline(vibration.KB_CORNER_HZ, color=COLOR_SECONDARY, linewidth=1.0, alpha=0.7)
    ax.plot(
        [vibration.KB_CORNER_HZ],
        [20.0 * math.log10(1.0 / math.sqrt(2.0))],
        color=COLOR_SECONDARY,
        marker="o",
        markersize=6,
        linestyle="none",
    )
    ax.text(
        6.6,
        -9.0,
        "5.6 Hz, the corner of Formula (4)",
        fontsize=10,
        color=COLOR_FG,
        ha="left",
        va="center",
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": COLOR_PANEL,
            "edgecolor": COLOR_GRID,
        },
    )
    ax.set_title("The KB weighting of a building vibration meter (DIN 45669-1)", pad=12)
    ax.set_xlabel(LABEL_FREQ_HZ)
    ax.set_ylabel("Weighting factor [dB]")
    ax.set_xlim(0.2, 800.0)
    ax.set_ylim(-40.0, 3.0)
    ax.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.5)
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", fontsize=10)
    format_frequency_axis(ax, 0.2, 800.0)
    plt.tight_layout()
    save_figure(output_dir, "kb_weighting.svg")
    plt.close()


def _immission_record(fs_hz: float) -> np.ndarray:
    """Ninety seconds of ground vibration with two events in it, in mm/s."""
    t = np.arange(int(90.0 * fs_hz)) / fs_hz
    record = 0.02 * np.sin(2.0 * np.pi * 11.0 * t)  # a machine running nearby
    for start, amplitude, frequency in ((22.0, 1.8, 17.0), (68.0, 0.9, 26.0)):
        window = (t >= start) & (t < start + 3.0)
        shape = np.hanning(int(window.sum()))
        record[window] += (
            amplitude * shape * np.sin(2.0 * np.pi * frequency * t[window])
        )
    return record


def generate_kb_time_response(output_dir: str) -> None:
    """DIN 45669-1: what a meter reduces a record to (Formulae (1) and (2))."""
    print("Generating kb_time_response...")
    from phonometry import vibration

    fs_hz = 2048.0
    record = _immission_record(fs_hz)
    reading = vibration.measure_vibration_immission(record, fs_hz)
    times = np.arange(record.size) / fs_hz

    _fig, axes = plt.subplots(2, 1, figsize=(10, 7.0), sharex=True)
    axes[0].plot(times, record, color=COLOR_MUTED, linewidth=0.6)
    axes[0].set_ylabel("Velocity $v$ [mm/s]")
    axes[0].set_title(
        "One record, and the four numbers a meter shows for it (DIN 45669-1)", pad=12
    )
    axes[0].grid(color=COLOR_GRID, linestyle="-", alpha=0.5)
    axes[0].set_axisbelow(True)

    axes[1].plot(
        times,
        reading.kbf,
        color=COLOR_PRIMARY,
        linewidth=1.2,
        label="$KB_F(t)$, running r.m.s. with $\\tau$ = 0.125 s",
    )
    axes[1].axhline(
        reading.kbf_max,
        color=COLOR_SECONDARY,
        linestyle="--",
        linewidth=1.4,
        label=f"$KB_{{F\\mathrm{{max}}}}$ = {reading.kbf_max:.3f}",
    )
    takt_s = vibration.TAKT_DURATION_S
    centres = (np.arange(reading.takt_maxima.size) + 0.5) * takt_s
    axes[1].plot(
        centres,
        reading.takt_maxima,
        color=COLOR_TERTIARY,
        marker="s",
        markersize=7,
        linestyle="none",
        label="clock maxima, one per 30 s",
    )
    axes[1].axhline(
        reading.kbf_takt_rms,
        color=COLOR_TERTIARY,
        linestyle=":",
        linewidth=1.4,
        label=f"$KB_{{FTm}}$ = {reading.kbf_takt_rms:.3f}",
    )
    for edge in np.arange(takt_s, 90.0, takt_s):
        axes[1].axvline(edge, color=COLOR_GRID, linewidth=0.8, alpha=0.8)
    axes[1].set_xlabel("Time [s]")
    axes[1].set_ylabel("Weighted vibration severity $KB_F$")
    axes[1].set_xlim(0.0, 90.0)
    axes[1].set_ylim(0.0, 1.55)
    axes[1].grid(color=COLOR_GRID, linestyle="-", alpha=0.5)
    axes[1].set_axisbelow(True)
    axes[1].legend(loc="upper right", fontsize=10)
    plt.tight_layout()
    save_figure(output_dir, "kb_time_response.svg")
    plt.close()


def generate_assessment_weighting(output_dir: str) -> None:
    """DIN 45669-1 Annex E: the three weightings and what they invert."""
    print("Generating assessment_weighting...")
    from phonometry import vibration

    freqs = np.geomspace(1.0, 315.0, 500)
    colors = {
        "commercial": COLOR_PRIMARY,
        "residential": COLOR_TERTIARY,
        "sensitive": COLOR_SECONDARY,
    }
    labels = {
        "commercial": "$v_{B1}$, commercial and industrial",
        "residential": "$v_{B2}$, dwellings",
        "sensitive": "$v_{B3}$, especially sensitive",
    }

    _fig, axes = plt.subplots(1, 2, figsize=(11.5, 5.4))
    for cls, color in colors.items():
        guideline = vibration.guideline_velocity(cls, freqs)
        axes[0].plot(freqs, guideline, color=color, linewidth=2.0, label=labels[cls])
        weighting = vibration.assessment_weighting_response(freqs, building_class=cls)
        axes[1].plot(freqs, weighting, color=color, linewidth=2.0, label=labels[cls])
    tolerance = vibration.ASSESSMENT_WEIGHTING_TOLERANCE
    residential = vibration.assessment_weighting_response(
        freqs, building_class="residential"
    )
    axes[1].fill_between(
        freqs,
        residential * (1.0 - tolerance),
        residential * (1.0 + tolerance),
        color=theme_fill(COLOR_TERTIARY, axes[1]),
        label="$\\pm$5 % of Table E.1",
    )
    axes[0].set_xscale("log")
    axes[0].set_title("What DIN 4150-3 Table 1 asks for", pad=10)
    axes[0].set_xlabel(LABEL_FREQ_HZ)
    axes[0].set_ylabel("Guideline peak velocity [mm/s]")
    axes[0].set_ylim(0.0, 55.0)
    axes[1].set_xscale("log")
    axes[1].set_title("The weighting that removes the frequency", pad=10)
    axes[1].set_xlabel(LABEL_FREQ_HZ)
    axes[1].set_ylabel("Weighting factor $H_{vB}$")
    axes[1].set_ylim(0.0, 1.15)
    for ax in axes:
        ax.set_xlim(1.0, 315.0)
        ax.grid(which="both", color=COLOR_GRID, linestyle="-", alpha=0.5)
        ax.set_axisbelow(True)
        ax.legend(loc="best", fontsize=9)
        format_frequency_axis(ax, 1.0, 315.0)
    plt.tight_layout()
    save_figure(output_dir, "assessment_weighting.svg")
    plt.close()
