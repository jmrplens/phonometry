#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The open end of a duct: what comes back, and what gets out."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

import numpy as np

from ..media import (
    _ANIM_PILL_BOX,
    _FDTD_ANIM_FRAMES,
    _anim_figure,
    _render_clip,
    _translate_str,
)
from ..theme import (
    CMAP_FIELD,
    COLOR_FG,
    COLOR_GRID,
    COLOR_PANEL,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
)

if TYPE_CHECKING:
    from numpy.typing import NDArray

# A 0.20 m duct, flush in a rigid screen, radiating into the half space
# beyond it: the Omega = 2 pi of configuration A in ISO 7235 Table B.1. The
# first higher-order mode of a 2D duct that wide cuts on at c / 2a = 857 Hz,
# so both carriers below stay in the plane-wave band the whole of ISO 7235's
# duct arithmetic assumes.
_OPEN_BORE = 0.20
# Duct length. The envelope has to hold at least a half wavelength of the
# lower carrier for its maximum and minimum both to be in it, which at
# 100 Hz is 1.72 m; 3.0 m of duct leaves 2.4 m of that clear of the
# injection line's near field, so the standing-wave ratio read off it is a
# measurement rather than a fraction of a lobe.
_OPEN_DUCT_L = 3.0  # duct length simulated [m]
_OPEN_FREE_L = 1.3  # half space beyond the screen [m]
_OPEN_HEIGHT = 2.0  # domain height [m]
# Mesh rule dx = min(smallest dimension / 4, shortest wavelength / 8) =
# min(0.20 / 4 = 50 mm, 343 / 800 / 8 = 54 mm). The grid runs eight times
# finer so the mouth is 33 cells across and the near field around its lip
# renders as a curve rather than as a staircase.
_OPEN_DX = 0.006
# The two carriers, both below the 857 Hz cut-on. At 100 Hz the mouth is
# 0.18 radians across in ka and reflects nearly everything; at 800 Hz it is
# 1.47 and radiates freely. Nothing between them is needed: the point is the
# contrast.
_OPEN_FREQS = (100.0, 800.0)
_OPEN_EVERY = 10  # capture stride [solver steps]
_OPEN_SETTLE_S = 0.060  # settle before capture [s]


@lru_cache(maxsize=1)
def _open_end_fields(
    n_frames: int = _FDTD_ANIM_FRAMES,
) -> tuple[Any, Any, Any, Any, Any]:
    """Two CW runs down the same duct into the same half space, cached.

    Identical scenes but for the drive frequency. The duct walls and the
    screen the mouth is flush with are built from a 10^6:1 density contrast,
    so the sustained plane wave can be injected across the whole left edge;
    rho c edges on the other three sides make the half space anechoic and
    the source non-reflecting, so what stands in the duct is the mouth's own
    reflection and nothing else.

    The envelope is taken over one whole period after the field has settled,
    which is what makes the standing-wave ratio in it a measurement rather
    than a snapshot.

    :param n_frames: How many frames to capture per run.
    :return: The two masked frame stacks, the two settled centreline
        envelopes, and the frame times.
    """
    import fdtd2d

    dx = _OPEN_DX
    bore = round(_OPEN_BORE / dx)
    ny = round(_OPEN_HEIGHT / dx)
    nx = round((_OPEN_DUCT_L + _OPEN_FREE_L) / dx)
    mouth = round(_OPEN_DUCT_L / dx)
    y0 = (ny - bore) // 2

    air = np.zeros((ny, nx), dtype=bool)
    air[y0 : y0 + bore, :mouth] = True  # the duct
    air[:, mouth:] = True  # the half space beyond the screen
    rho_map = np.where(air, 1.2, 1.2e6)

    runs: list[tuple[Any, Any]] = []
    times = np.zeros(0)
    for frequency in _OPEN_FREQS:
        sim = fdtd2d.FDTD2D(
            343.0,
            dx,
            shape=(ny, nx),
            rho=rho_map,
            edge_impedance={
                "left": 1.2 * 343.0,
                "right": 1.2 * 343.0,
                "top": 1.2 * 343.0,
                "bottom": 1.2 * 343.0,
            },
        )
        tone = fdtd2d.CWSource(0, 0, frequency=frequency)
        sim.add_source(fdtd2d.PlaneWaveSource("right", tone.value, offset=2))
        axis = y0 + bore // 2
        period = round(1.0 / (frequency * sim.dt))
        settle = round(_OPEN_SETTLE_S / sim.dt)
        envelope = np.zeros(mouth, dtype=np.float32)
        for step in range(settle):
            sim.step()
            if step >= settle - period:
                np.maximum(envelope, np.abs(sim.p[axis, :mouth]), out=envelope)
        frames: list[Any] = []
        stamps: list[float] = []
        while len(frames) < n_frames:
            sim.step()
            if sim.n % _OPEN_EVERY == 0:
                # The dense cells ring with the injection line; blanking
                # them keeps the colour scale on the air path.
                frames.append(np.where(air, sim.p, np.nan)[::2, ::2].astype(np.float32))
                stamps.append(sim.time)
        runs.append((np.stack(frames), envelope))
        times = np.asarray(stamps)
    return runs[0][0], runs[0][1], runs[1][0], runs[1][1], times


def _standing_wave_reflection(envelope: NDArray[np.float32]) -> float:
    """The reflection coefficient the standing wave in the duct implies.

    An incident wave and its echo add to ``|p| = p_i (1 + r)`` where they
    are in phase and ``p_i (1 - r)`` where they are not, so the ratio of the
    two gives ``r`` back. The first fifth of the duct is dropped: the
    injection line sits there and its near field is not the standing wave.
    """
    inner = np.asarray(envelope, dtype=np.float64)[len(envelope) // 5 :]
    top, bottom = float(np.max(inner)), float(np.min(inner))
    return float((top - bottom) / (top + bottom)) if top + bottom > 0.0 else 0.0


def animate_fdtd_open_end(output_dir: str) -> None:
    """What a duct mouth keeps in, at two frequencies (2D FDTD).

    One 0.20 m duct flush in a rigid screen, radiating into the half space
    beyond it, driven at 100 Hz and at 800 Hz. At 100 Hz the mouth is a
    fifth of a radian across in ``ka`` and is a poor radiator: most of what
    reaches it turns round, and the duct fills with a standing wave whose
    peaks and troughs are the incident wave and its echo adding and
    cancelling. At 800 Hz the mouth radiates freely, almost nothing comes
    back and the duct carries a travelling wave with a nearly flat envelope.

    That is the whole content of ISO 7235 Equation (B.3), and of ISO 5135
    Equation (2), which is the same formula: the mouth is a filter, and it
    is the reason a level measured in a room is not the level in the duct
    behind it.
    """
    T = _translate_str
    p_low, env_low, p_high, env_high, times = _open_end_fields()
    axis_x = np.arange(env_low.size) * _OPEN_DX

    fig = _anim_figure()
    # Reserve the bottom strip for the two-line footer: fig.text does not
    # claim space from the constrained layout on its own.
    fig.get_layout_engine().set(rect=(0.0, 0.085, 1.0, 0.915))  # type: ignore[union-attr, call-arg]  # _anim_figure: constrained engine, never None
    fig.suptitle(T("The open end of a duct: what comes back (2D FDTD)"))
    grid = fig.add_gridspec(2, 2, width_ratios=(1.0, 1.0), height_ratios=(1.0, 1.0))

    extent = (
        0.0,
        _OPEN_DUCT_L + _OPEN_FREE_L,
        0.0,
        _OPEN_HEIGHT,
    )
    ims: list[Any] = []
    for row, (frames, frequency) in enumerate(
        ((p_low, _OPEN_FREQS[0]), (p_high, _OPEN_FREQS[1]))
    ):
        ax = fig.add_subplot(grid[row, 0])
        ax.grid(visible=False)
        limit = 1.05 * float(np.nanquantile(np.abs(frames[-1]), 0.999))
        ims.append(
            ax.imshow(
                frames[0],
                origin="lower",
                extent=extent,
                cmap=CMAP_FIELD,
                vmin=-limit,
                vmax=limit,
            )
        )
        ax.axvline(_OPEN_DUCT_L, color=COLOR_FG, lw=1.4, ls="--")
        ax.set_title(T(f"{frequency:.0f} Hz"), fontsize=10, color=COLOR_FG, loc="left")
        ax.set_xticks([])
        ax.set_yticks([])

    for row, (envelope, colour) in enumerate(
        ((env_low, COLOR_PRIMARY), (env_high, COLOR_SECONDARY))
    ):
        ax = fig.add_subplot(grid[row, 1])
        ax.plot(axis_x, envelope / float(np.max(envelope)), color=colour, lw=1.8)
        ax.set_ylim(0.0, 1.15)
        ax.set_xlim(0.0, _OPEN_DUCT_L)
        ax.grid(color=COLOR_GRID, ls="--", alpha=0.4)
        ax.set_axisbelow(True)
        ax.set_ylabel(T("|p| along the duct"), fontsize=9)
        if row == 1:
            ax.set_xlabel(T("Distance from the source [m]"), fontsize=9)
        ax.text(
            0.03,
            0.10,
            T(f"standing-wave r = {_standing_wave_reflection(envelope):.2f}"),
            transform=ax.transAxes,
            fontsize=9,
            color=COLOR_FG,
            bbox={
                "boxstyle": _ANIM_PILL_BOX,
                "facecolor": COLOR_PANEL,
                "edgecolor": COLOR_GRID,
            },
        )

    fig.text(
        0.5,
        0.048,
        T("The mouth is a filter, and Equation (B.3) is how much of one"),
        ha="center",
        fontsize=10,
        color=COLOR_FG,
    )
    fig.text(
        0.5,
        0.014,
        T(
            "at 100 Hz it reflects most of what reaches it and the duct rings; "
            "at 800 Hz it radiates and the duct carries a travelling wave"
        ),
        ha="center",
        fontsize=9,
        color=COLOR_FG,
    )

    def update(index: int) -> tuple[Any, ...]:
        ims[0].set_data(p_low[index])
        ims[1].set_data(p_high[index])
        return (*ims,)

    _render_clip(
        fig,
        update,
        output_dir,
        "anim_fdtd_open_end",
        frames=int(times.size),
        gif_fps=8,
    )
