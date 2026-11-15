#  Copyright (c) 2026. Jose Manuel Requena Plens
"""One pulse in a box whose four sides are the four boundaries of the engine."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

import numpy as np

from ..media import _anim_figure, _render_clip, _translate_str
from ..theme import (
    CMAP_FIELD,
    COLOR_FG,
    COLOR_MUTED,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_TERTIARY,
    FIELD_INK,
    FIELD_STROKE,
)
from ._core import _host

if TYPE_CHECKING:
    from numpy.typing import NDArray

# The box of the FDTD guide's section on boundaries: air in a rectangle
# whose four sides carry the four things a side of the engine can be. The
# left side is left rigid, the top is a sponge, the right side carries the
# anechoic impedance rho c and the bottom the impedance the guide derives
# for a normal-incidence absorption of 0.9, 1.92 rho c.
_BND_C, _BND_RHO = 343.0, 1.2
_BND_W, _BND_H = 4.0, 2.25  # the box [m], 16:9
#: The normal-incidence absorption the bottom side is given.
_BND_ALPHA = 0.9
# The source sits 0.6 m from the bottom and from the right side, so both
# impedance sides are met from the normal out to oblique angles: the bottom
# out to 80 degrees at the far corner and the right side out to 70. The
# angle at which the bottom reflects nothing, 58.7 degrees, is met 0.99 m
# along it, well inside the box.
_BND_SRC = (3.4, 0.6)  # from the bottom-left corner [m]
# Mesh rule dx = min(smallest geometric dimension / 4, shortest wavelength
# / 8). The smallest dimension is the 0.6 m between the source and a side
# (0.15 m); the Gaussian pulse of half-width 0.2 ms is 20 dB down at
# 2 415 Hz, where the wavelength is 0.142 m and lambda / 8 = 17.8 mm. The
# grid runs at 10 mm.
_BND_DX = 0.01
_BND_HALF_WIDTH = 2.0e-4  # Gaussian half-width [s]
_BND_SPONGE = 40  # cells above the box
# Timeline per the animation norms. Flight: the deepest reflector is the
# rigid left side, 3.4 m from the source, and its mirror image of the pulse
# is followed back to the middle of the box, 2.0 m on: 5.4 m at 343 m/s is
# 15.7 ms, and the pulse leaves the source when it peaks, four half-widths
# in; so 0.8 + 1.2 x 15.7 = 19.7 ms is captured. Sampling: dt = 0.6 dx /
# (c sqrt(2)) = 12.37 us and every step is a frame, 72.8 frames per period
# of the 1 125 Hz the radiated pulse peaks at (>= the 48 the clips keep);
# 1 593 frames, played at 100 fps: 15.9 s, plus a 2 s hold.
_BND_FPS = 100.0
_BND_HOLD = round(2.0 * _BND_FPS)


def _bnd_impedance() -> float:
    """The bottom side's impedance over ``rho c``, from its normal absorption.

    ``|R| = sqrt(1 - alpha)`` and ``z = (1 + R) / (1 - R)``, the two steps
    the guide gives: 1.92 for an absorption of 0.9.
    """
    reflection = float(np.sqrt(1.0 - _BND_ALPHA))
    return (1.0 + reflection) / (1.0 - reflection)


def _bnd_reflection(z: float, angle_deg: NDArray[np.float64]) -> NDArray[np.float64]:
    """Reflection coefficient of a locally reacting side of impedance ``z rho c``.

    ``R = (z cos(theta) - 1) / (z cos(theta) + 1)``, the plane-wave
    reflection behind the oblique absorption of Mechel (2008), Sect. D.5,
    Eq. (6), ``4 z cos(theta) / (1 + z cos(theta))^2``, for a real ``z``.
    The solver's own test holds its impedance edge to it.
    """
    cosine = np.cos(np.radians(angle_deg))
    reflection: NDArray[np.float64] = (z * cosine - 1.0) / (z * cosine + 1.0)
    return reflection


@lru_cache(maxsize=1)
def _boundaries_fields() -> tuple[Any, Any]:
    """The pulse in the four-sided box, cached.

    Returns the pressure over the box, one sample every two cells, in units
    of the colour scale the frames are drawn on, and the frame times.
    """
    import clip_placement

    from phonometry.simulation import FDTD2D, GaussianPulse

    compute = clip_placement.compute_for("anim_fdtd_boundaries")
    dx = _BND_DX
    nx, rows = round(_BND_W / dx), round(_BND_H / dx)
    ny = _BND_SPONGE + rows
    rho_c = _BND_RHO * _BND_C
    sim = FDTD2D(
        c=_BND_C,
        dx=dx,
        rho=_BND_RHO,
        shape=(ny, nx),
        absorbing_layer_cells=_BND_SPONGE,
        absorbing_sides=("top",),
        edge_impedance={"right": rho_c, "bottom": _bnd_impedance() * rho_c},
        compute=compute,
    )
    sim.add_source(
        GaussianPulse(
            ix=round(_BND_SRC[0] / dx),
            iy=ny - round(_BND_SRC[1] / dx),
            half_width_s=_BND_HALF_WIDTH,
        )
    )
    flight = (_BND_SRC[0] + 0.5 * _BND_W) / _BND_C
    t_end = 4.0 * _BND_HALF_WIDTH + 1.2 * flight
    n_active = int(np.ceil(t_end / sim.dt))
    view = (slice(_BND_SPONGE, ny, 2), slice(0, nx, 2))
    frames: list[Any] = []
    ts: list[float] = []
    while len(frames) < n_active:
        sim.step()
        frames.append(_host(sim, sim.p[view]))
        ts.append(sim.time)
    stack = np.stack(frames)
    # The colour scale is set on the second half of the run, where what is
    # in the box is the reflections: the pulse at the source is far above
    # anything it leaves behind.
    scale = float(np.quantile(np.abs(stack[n_active // 2 :]), 0.999))
    return stack / scale, np.asarray(ts)


def animate_fdtd_boundaries(output_dir: str) -> None:
    """The four boundaries of the engine, met by one pulse (2D FDTD).

    A pulse leaves a source near the bottom-right corner of a box of air
    whose sides are the four things a side can be. The rigid side sends the
    whole pulse back at every angle. The sponge sends back next to nothing
    near its normal and a faint front from its far end, met beyond 60
    degrees, where a sponge is weaker. The two
    impedance sides are where a single number misleads: each reflects by
    ``(Z cos(theta) - rho c) / (Z cos(theta) + rho c)``, so the side matched
    to ``rho c`` is silent only along its normal and sends back more and
    more, inverted, as the pulse runs along it, while the side set for an
    absorption of 0.9 at normal incidence sends back a weak upright pulse
    near the normal, nothing at 58.7 degrees, and an inverted one beyond.
    The side panel draws those three laws; the dotted rays in the box mark
    the two directions in which an impedance side returns nothing.
    """
    from matplotlib import patheffects

    T = _translate_str
    frames, times = _boundaries_fields()
    n_active = int(times.size)
    z = _bnd_impedance()
    null_deg = float(np.degrees(np.arccos(1.0 / z)))
    outline = [patheffects.withStroke(linewidth=2.2, foreground=FIELD_STROKE)]

    fig = _anim_figure()
    fig.get_layout_engine().set(rect=(0.0, 0.05, 1.0, 0.95))  # type: ignore[union-attr, call-arg]  # _anim_figure: constrained engine, never None
    fig.suptitle(T("Four boundaries, one pulse (2D FDTD)"))
    grid = fig.add_gridspec(1, 2, width_ratios=(2.7, 1.0))
    ax = fig.add_subplot(grid[0, 0])
    ax.grid(visible=False)
    im = ax.imshow(
        frames[0],
        origin="upper",
        extent=(0.0, _BND_W, 0.0, _BND_H),
        cmap=CMAP_FIELD,
        vmin=-1.0,
        vmax=1.0,
        aspect="equal",
        interpolation="bilinear",
    )
    ax.set_xticks([])
    ax.set_yticks([])
    # The sponge is the one side that is not a wall: its spine is dashed.
    ax.spines["top"].set_linestyle((0, (4, 3)))
    for side in ("left", "right", "bottom", "top"):
        ax.spines[side].set_linewidth(1.6)
    sx, sy = _BND_SRC
    null_x = sx - sy * float(np.tan(np.radians(null_deg)))
    for end in ((null_x, 0.0), (_BND_W, sy)):
        ax.plot(
            [sx, end[0]],
            [sy, end[1]],
            ls=":",
            lw=1.0,
            color=FIELD_INK,
            zorder=4,
        )
    ax.plot(
        [sx],
        [sy],
        marker="*",
        ms=9,
        color=COLOR_SECONDARY,
        markeredgecolor=FIELD_STROKE,
        markeredgewidth=0.6,
        zorder=6,
    )
    label: dict[str, Any] = {
        "fontsize": 8,
        "color": FIELD_INK,
        "path_effects": outline,
        "zorder": 7,
    }
    ax.text(
        0.07,
        0.5 * _BND_H,
        T("rigid: $R = +1$ at every angle"),
        rotation=90,
        ha="left",
        va="center",
        **label,
    )
    ax.text(
        1.6,
        _BND_H - 0.07,
        T("sponge: the pulse leaves"),
        ha="center",
        va="top",
        **label,
    )
    ax.text(
        _BND_W - 0.07,
        0.66 * _BND_H,
        T("$Z = \\rho c$: nothing back at 0°"),
        rotation=90,
        ha="right",
        va="center",
        **label,
    )
    ax.text(
        1.15,
        0.07,
        T(f"$Z = {z:.2f}\\,\\rho c$: nothing back at {null_deg:.1f}°"),
        ha="center",
        va="bottom",
        **label,
    )

    law = fig.add_subplot(grid[0, 1])
    angles = np.linspace(0.0, 89.9, 300)
    law.axhline(0.0, color=COLOR_MUTED, lw=0.8, zorder=1)
    law.plot(
        angles, np.ones_like(angles), color=COLOR_FG, lw=1.4, label=T("rigid side")
    )
    law.plot(
        angles,
        _bnd_reflection(z, angles),
        color=COLOR_PRIMARY,
        lw=1.6,
        label=T(f"side at $Z = {z:.2f}\\,\\rho c$"),
    )
    law.plot(
        angles,
        _bnd_reflection(1.0, angles),
        color=COLOR_TERTIARY,
        lw=1.6,
        label=T("side at $Z = \\rho c$"),
    )
    law.plot([null_deg], [0.0], marker="o", ms=5, color=COLOR_PRIMARY, zorder=5)
    law.plot(
        [0.0], [0.0], marker="o", ms=5, color=COLOR_TERTIARY, zorder=5, clip_on=False
    )
    law.set_xlim(0.0, 90.0)
    law.set_ylim(-1.08, 1.12)
    law.set_xticks([0, 30, 60, 90])
    law.set_yticks([-1.0, -0.5, 0.0, 0.5, 1.0])
    law.tick_params(labelsize=7)
    law.set_xlabel(T("angle from the normal [°]"), fontsize=8)
    law.set_ylabel(T("reflection coefficient $R$"), fontsize=8)
    law.set_title(T("What each side sends back"), fontsize=8.5)
    law.legend(fontsize=6.5, loc="lower left", framealpha=0.85)

    fig.text(
        0.5,
        0.012,
        T(
            f"air in a {_BND_W:.2f} m by {_BND_H:.2f} m box; a locally reacting "
            "side reflects $R(\\theta) = (Z\\cos\\theta - \\rho c)/(Z\\cos\\theta "
            "+ \\rho c)$; dotted: the two rays that are not reflected"
        ),
        ha="center",
        va="bottom",
        fontsize=7.5,
        color=COLOR_FG,
    )
    t_txt = fig.text(
        0.012,
        0.935,
        "",
        ha="left",
        va="top",
        family="monospace",
        fontsize=9,
        color=COLOR_FG,
    )

    def update(k: int) -> tuple[Any, ...]:
        kf = min(k, n_active - 1)
        im.set_data(frames[kf])
        t_txt.set_text(T(f"$t$ = {float(times[kf]) * 1e3:5.2f} ms"))
        return im, t_txt

    _render_clip(
        fig,
        update,
        output_dir,
        "anim_fdtd_boundaries",
        frames=n_active + _BND_HOLD,
        fps=_BND_FPS,
        gif_fps=8,
    )
