#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Lloyd's mirror: a source under the sea surface and its inverted image."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import numpy as np

from ..i18n import _fmt_minus
from ..media import _anim_figure, _render_clip, _translate_str
from ..schematics import _grid_axes
from ..theme import (
    CMAP_FIELD,
    COLOR_FG,
    COLOR_PRIMARY,
    COLOR_SECONDARY,
    COLOR_TERTIARY,
    FIELD_INK,
    FIELD_STROKE,
)
from ._core import _host

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.figure import Figure
    from matplotlib.gridspec import SubplotSpec
    from matplotlib.image import AxesImage
    from matplotlib.patheffects import AbstractPathEffect
    from numpy.typing import NDArray

    from phonometry.simulation import Compute

# The ship of the guide's own example (underwater/underwater-acoustics.mdx
# section 2): 6 m of mean draught, measured at the 100 m distance at the
# closest point of approach ISO 17208-1 5.4 gives a ship no longer than that.
# The nominal source depth, 0.7 of the draught (ISO 17208-2 Formula 1), and
# the three hydrophone depths are read from the library, not copied.
_LM_DRAUGHT = 6.0
_LM_CPA = 100.0
#: Sound speed of the water [m/s]: the default of
#: ``underwater.monopole_source_level``, and handed to it by name below so
#: the clip and the function cannot come to use two.
_LM_C = 1500.0
#: The two carriers [Hz], a decade apart and one on each side of the band
#: where the surface correction changes sign, k d_s = 1.03 (59 Hz for this
#: source depth). Both are decidecade centres of the guide's example:
#: k d_s = 0.55 at 31.5 Hz, where the correction is +5.15 dB, and 5.54 at
#: 315 Hz, past the first lobe.
_LM_FREQS = (31.5, 315.0)
# Mesh rule dx = min(smallest geometric dimension / 4, shortest wavelength
# / 8) = min(4.2 / 4, 4.762 / 8) m = 0.595 m. The grid runs 2.55 times
# finer, at 18 cells from the surface to the source (dx = 233 mm), for the
# timeline: the solver step is then dt = 0.6 dx / (c sqrt(2)) = 66.0 us,
# which puts 48.1 steps in one period of the 315 Hz carrier, so a frame per
# step meets the 48 frames per period the clips keep. The free surface is
# the plane through the top row of cell centres (stress imaging), so the
# source sits exactly 18 dx = 4.2 m under it.
_LM_CELLS_DEEP = 18
# The view [m], from the ship's side of the source to past the hydrophone
# string and down to past the deepest hydrophone (100 m). The strip above
# the surface is not simulated: it carries the mirror picture.
_LM_X0, _LM_X1 = -12.0, 110.0
_LM_Z1 = 110.0
_LM_AIR = 16.0
#: Depression angles the level is read over along the string [deg]: from
#: just under the surface to just past the deepest hydrophone.
_LM_ALPHA = (2.0, 47.0)
#: The sponge is this many wavelengths of the run's own carrier thick, and
#: never thinner than the cells below.
_LM_SPONGE_WAVELENGTHS = 2.0
_LM_SPONGE_MIN = 100
# Measured on the full-size run (NumPy, 2026-11-15). With these sponges the
# level along the string stays within 0.23 dB of the pair at 31.5 Hz (median
# 0.03 dB); at 315 Hz the median is 0.07 dB, with 0.24 dB at the 30 degree
# hydrophone, on the flank of the null, and 3 dB in the null itself, at
# 34.4 degrees. With one wavelength and 40 cells the same curves rode a
# ripple of 0.5 dB at 31.5 Hz and read 0.6 dB over the pair's own maximum at
# 315 Hz: the sponge, not the surface.
# Timeline. Flight: the farthest visible point is the bottom right corner,
# hypot(110, 110 - 4.2) = 152.6 m from the source, 101.7 ms at 1500 m/s, so
# the norm's 1.2 x flight is 122.1 ms. The level panel needs longer than
# that, because the slow carrier has to settle at the bottom of the string:
# 143.7 m away (95.8 ms), then the one-period onset ramp of the 31.5 Hz
# carrier (31.7 ms) and the one period its level is read over (31.7 ms),
# 159.3 ms in all. 180 ms are captured, so the settled curves stand for the
# last 20 ms; the verdicts come up at the settling time.
# Sampling: one frame per solver step, 66.0 us, 48.1 frames per period of
# the 315 Hz carrier and 481 of the 31.5 Hz one; 2 728 frames at 160 fps
# run 17.1 s, 10.6 ms of simulation per second of playback.
_LM_SPAN = 0.180
_LM_FPS = 160
#: Reading band of the level panel [dB re the source alone] and the axis
#: bottom under it: the strip below the floor is the legend's, and no curve
#: or marker enters it.
_LM_LEVEL_TOP = 10.0
_LM_LEVEL_FLOOR = -30.0
_LM_LEVEL_BOTTOM = -50.0


@dataclass(frozen=True)
class _LmFields:
    """What the two pairs of runs leave for the clip to draw.

    :ivar frames: The pressure frames of the two surface runs, low carrier
        first, each normalised to its own late-time colour scale.
    :ivar times: The frame times [s].
    :ivar alpha: The depression angles of the string cells [deg].
    :ivar levels: Per frame, the level along the string [dB re the same
        source with no surface], NaN below the reading floor.
    :ivar model: The same level from a line source and its inverted image.
    :ivar means: The power mean of the three hydrophone levels at the last
        frame, per carrier [dB].
    :ivar hydrophones: The three hydrophone depths [m].
    :ivar string_x: Horizontal distance of the string from the source [m].
    :ivar depth: The source depth [m].
    :ivar extent: The simulated view: left, right and bottom [m].
    :ivar reveal: The frame the slow carrier has settled at.
    """

    frames: tuple[NDArray[np.float32], NDArray[np.float32]]
    times: NDArray[np.float64]
    alpha: NDArray[np.float64]
    levels: tuple[NDArray[np.float32], NDArray[np.float32]]
    model: tuple[NDArray[np.float64], NDArray[np.float64]]
    means: tuple[float, float]
    hydrophones: NDArray[np.float64]
    string_x: float
    depth: float
    extent: tuple[float, float, float]
    reveal: int


def _lm_string_rows(dx: float) -> NDArray[np.intp]:
    """Rows of the hydrophone string, counted from the surface row."""
    x = round(_LM_CPA / dx) * dx
    first = math.ceil(x * math.tan(math.radians(_LM_ALPHA[0])) / dx)
    last = math.floor(x * math.tan(math.radians(_LM_ALPHA[1])) / dx)
    return np.arange(first, last + 1)


def _lm_run(
    frequency: float,
    depth: float,
    *,
    surface: bool,
    stride: int | None,
    compute: Compute,
) -> tuple[NDArray[np.float32] | None, NDArray[np.float64], float]:
    """One CW run of the source in water, with the sea surface or without.

    With ``surface`` the top side is the solver's traction-free surface,
    which in a fluid (``c_s = 0``) is a pressure-release one: the pressure
    on the top row is zero at every step. Without it the grid grows upwards
    and all four sides absorb, so the same source radiates into open water:
    the run every level of the clip is referred to.

    Returns the decimated frames of the view (``None`` without a
    ``stride``), the pressure at the string cells at every step, and the
    solver step [s].
    """
    from phonometry import simulation

    dx = depth / _LM_CELLS_DEEP
    sponge = max(
        _LM_SPONGE_MIN, math.ceil(_LM_SPONGE_WAVELENGTHS * _LM_C / frequency / dx)
    )
    margin = round(-_LM_X0 / dx)
    right = round(_LM_X1 / dx)
    down = round(_LM_Z1 / dx)
    top = 0 if surface else sponge + margin
    ix0 = sponge + margin
    nx = ix0 + right + 1 + sponge
    ny = top + down + 1 + sponge
    sim = simulation.ElasticFDTD2D(
        c_p=_LM_C,
        c_s=0.0,
        dx=dx,
        rho=simulation.WATER.rho,
        shape=(ny, nx),
        absorbing_layer_cells=sponge,
        absorbing_sides=(
            ("left", "right", "bottom")
            if surface
            else ("left", "right", "top", "bottom")
        ),
        free_sides=("top",) if surface else None,
        compute=compute,
    )
    carrier = simulation.CWSource(
        ix=0, iy=0, frequency=frequency, ramp_cycles=1.0
    ).value
    sim.add_source(
        simulation.ExplosionSource(ix=ix0, iy=top + _LM_CELLS_DEEP, waveform=carrier)
    )
    steps = math.ceil(_LM_SPAN / sim.dt)
    backend = sim._backend
    xp = backend.xp
    col = ix0 + round(_LM_CPA / dx)
    cells = backend.index((top + _lm_string_rows(dx)) * nx + col)
    view = (
        None
        if stride is None
        else (
            slice(top, top + down + 1, stride),
            slice(ix0 - margin, ix0 + right + 1, stride),
        )
    )
    frames: list[NDArray[np.float32]] = []
    record: list[Any] = []
    for _ in range(steps):
        sim.step()
        p = sim.p
        record.append(xp.take(xp.reshape(p, (-1,)), cells))
        if view is not None:
            frames.append(_host(sim, p[view]))
    string = _host(sim, xp.stack(record), dtype=np.float64)
    return (np.stack(frames) if frames else None), string, float(sim.dt)


def _lm_levels(
    string: NDArray[np.float64], alone: NDArray[np.float64], window: int
) -> NDArray[np.float64]:
    """Level along the string at every step [dB re the source alone].

    The mean square over the last ``window`` steps, one period of the
    carrier, against the same mean square of the run with no surface, taken
    over its last period, when the whole string has settled.
    """
    energy = np.concatenate(
        [np.zeros((1, string.shape[1])), np.cumsum(string**2, axis=0)]
    )
    last = np.arange(1, string.shape[0] + 1)
    mean_square = (energy[last] - energy[np.maximum(last - window, 0)]) / window
    reference = np.mean(alone[-window:] ** 2, axis=0)
    with np.errstate(divide="ignore"):
        levels: NDArray[np.float64] = 10.0 * np.log10(mean_square / reference)
    return levels


def _lm_model(
    frequency: float, depth: float, x: float, z: NDArray[np.float64]
) -> NDArray[np.float64]:
    """Level of a line source and its inverted image [dB re the source alone].

    The exact two-dimensional field of the pair, ``H0(k r1) - H0(k r2)``
    with ``r1`` and ``r2`` the distances of ISO 17208-2 Figure A.1, against
    ``H0(k r1)``. It is the two-dimensional counterpart of Formula (A.6),
    not the fitted Formula (3), which averages the three-dimensional far
    field over the three hydrophones.
    """
    from scipy.special import hankel2

    k = 2.0 * np.pi * frequency / _LM_C
    direct = hankel2(0, k * np.hypot(x, z - depth))
    image = hankel2(0, k * np.hypot(x, z + depth))
    model: NDArray[np.float64] = 20.0 * np.log10(
        np.abs(direct - image) / np.abs(direct)
    )
    return model


def _power_mean(levels: NDArray[np.float64]) -> float:
    """The power average of *levels* [dB], as ISO 17208-1 Formula (8) takes it."""
    return float(10.0 * np.log10(np.mean(10.0 ** (levels / 10.0))))


@lru_cache(maxsize=1)
def _lloyd_mirror_fields() -> _LmFields:
    """The two carriers under the surface and in open water, cached.

    Four runs of the library's P-SV engine in a fluid: each carrier once
    under a free top side and once with the surface taken away. The first
    gives the frames and the pressure along the hydrophone string; the
    second gives what the same source radiates alone at the same cells, so
    the level the clip plots is measured, not normalised by a model.
    """
    import clip_placement

    from phonometry import underwater

    compute = clip_placement.compute_for("anim_fdtd_lloyd_mirror")
    depth = float(
        underwater.monopole_source_level(
            0.0, _LM_DRAUGHT, frequency=_LM_FREQS[0], speed_of_sound=_LM_C
        ).source_depth
    )
    dx = depth / _LM_CELLS_DEEP
    rows = _lm_string_rows(dx)
    string_x = round(_LM_CPA / dx) * dx
    z = np.asarray(rows * dx, dtype=np.float64)
    hydrophones = underwater.hydrophone_depths(string_x)
    at = np.round(hydrophones / dx).astype(int) - int(rows[0])

    frames: list[NDArray[np.float32]] = []
    levels: list[NDArray[np.float32]] = []
    model: list[NDArray[np.float64]] = []
    means: list[float] = []
    times: NDArray[np.float64] = np.zeros(0)
    # The low carrier is drawn from every third cell and the high one from
    # every second: 68 and 10 stored cells per wavelength.
    for frequency, stride in zip(_LM_FREQS, (3, 2), strict=True):
        field, string, dt = _lm_run(
            frequency, depth, surface=True, stride=stride, compute=compute
        )
        _, alone, _ = _lm_run(
            frequency, depth, surface=False, stride=None, compute=compute
        )
        if field is None:
            msg = "the surface run was asked for frames and returned none"
            raise RuntimeError(msg)
        half = field.shape[0] // 2
        frames.append(field / float(np.quantile(np.abs(field[half:]), 0.995)))
        history = _lm_levels(string, alone, round(1.0 / (frequency * dt)))
        means.append(_power_mean(history[-1, at]))
        levels.append(
            np.where(history < _LM_LEVEL_FLOOR, np.nan, history).astype(np.float32)
        )
        model.append(_lm_model(frequency, depth, string_x, z))
        times = np.asarray((np.arange(string.shape[0]) + 1.0) * dt, dtype=np.float64)
    settle = float(np.hypot(string_x, z[-1] - depth)) / _LM_C + 2.0 / _LM_FREQS[0]
    return _LmFields(
        frames=(frames[0], frames[1]),
        times=times,
        alpha=np.degrees(np.arctan2(z, string_x)),
        levels=(levels[0], levels[1]),
        model=(model[0], model[1]),
        means=(means[0], means[1]),
        hydrophones=hydrophones,
        string_x=string_x,
        depth=depth,
        extent=(
            -round(-_LM_X0 / dx) * dx,
            round(_LM_X1 / dx) * dx,
            round(_LM_Z1 / dx) * dx,
        ),
        reveal=min(int(np.searchsorted(times, settle)), times.size - 1),
    )


def _lm_ghost(frame: NDArray[np.float32], rows: int) -> NDArray[np.float32]:
    """The strip above the surface: *frame* mirrored in it, with its sign turned."""
    return -frame[rows - 1 :: -1]


def _lm_field_panel(
    fig: Figure,
    cell: SubplotSpec,
    fields: _LmFields,
    index: int,
    *,
    outline: Sequence[AbstractPathEffect],
) -> tuple[AxesImage, AxesImage, int]:
    """One carrier's field: the water, the mirror picture above it and the string."""
    T = _translate_str
    data = fields.frames[index]
    left, right, bottom = fields.extent
    air_rows = round(_LM_AIR / (bottom / (data.shape[1] - 1)))
    ax = fig.add_subplot(cell)
    ax.grid(visible=False)
    im = ax.imshow(
        data[0],
        origin="upper",
        extent=(left, right, bottom, 0.0),
        cmap=CMAP_FIELD,
        vmin=-1.0,
        vmax=1.0,
        interpolation="bilinear",
    )
    # The method of images, drawn: the field under the surface is the field
    # of the source and of an image of opposite sign in water without a
    # surface, and this is that picture's upper half.
    ghost = ax.imshow(
        _lm_ghost(data[0], air_rows),
        origin="upper",
        extent=(left, right, 0.0, -_LM_AIR),
        cmap=CMAP_FIELD,
        vmin=-1.0,
        vmax=1.0,
        alpha=0.4,
        interpolation="bilinear",
    )
    ax.set_xlim(left, right)
    ax.set_ylim(bottom, -_LM_AIR)
    ax.set_aspect("equal")
    ax.plot([left, right], [0.0, 0.0], color=COLOR_FG, lw=1.0)
    u = 2.0 * np.pi * _LM_FREQS[index] * fields.depth / _LM_C
    ax.set_title(
        T(f"{_LM_FREQS[index]:g} Hz: $k d_\\mathrm{{s}}$ = {u:.2f}"), fontsize=9.5
    )
    ax.plot(
        [0.0],
        [fields.depth],
        marker="o",
        ms=3.5,
        color=COLOR_TERTIARY,
        markeredgecolor=FIELD_STROKE,
        markeredgewidth=0.6,
    )
    ax.plot(
        [0.0], [-fields.depth], marker="o", ms=3.5, mfc="none", color=COLOR_TERTIARY
    )
    label: dict[str, Any] = {
        "ha": "left",
        "va": "center",
        "color": FIELD_INK,
        "fontsize": 6.5,
        "path_effects": outline,
    }
    ax.text(
        6.0,
        fields.depth + 8.0,
        T(f"source, $d_\\mathrm{{s}}$ = {fields.depth:.1f} m"),
        **label,
    )
    ax.text(6.0, -0.55 * _LM_AIR, T("image, inverted"), **label)
    ax.text(right - 3.0, -0.55 * _LM_AIR, T("surface"), **{**label, "ha": "right"})
    # The string of ISO 17208-1 Figure 1 and its three hydrophones.
    ax.plot(
        [fields.string_x, fields.string_x],
        [0.0, float(fields.hydrophones[-1]) + 6.0],
        ls=":",
        color=FIELD_INK,
        lw=0.9,
    )
    for angle, z in zip((15, 30, 45), fields.hydrophones, strict=True):
        ax.plot(
            [fields.string_x],
            [z],
            marker="o",
            ms=4,
            color="white",
            markeredgecolor="black",
            markeredgewidth=0.8,
        )
        ax.text(fields.string_x - 5.0, z, f"{angle}°", **{**label, "ha": "right"})
    ax.set_xticks([0.0, 50.0, 100.0])
    ax.set_yticks([0.0, 50.0, 100.0])
    ax.tick_params(labelsize=7)
    ax.set_xlabel(T("horizontal distance [m]"), fontsize=8)
    if index == 0:
        ax.set_ylabel(T("depth [m]"), fontsize=8)
    else:
        ax.tick_params(labelleft=False)
    return im, ghost, air_rows


def animate_fdtd_lloyd_mirror(output_dir: str) -> None:
    """A source 4.2 m under the sea surface at 31.5 Hz and at 315 Hz.

    The sea surface is a pressure-release mirror (ISO 17208-2 Annex A), so
    the water below holds the field of the source and of an image of
    opposite sign 2 d_s above it; the strip over the surface draws that
    image. Below the band where the surface correction changes sign the
    pair is closer than a wavelength and radiates as a vertical dipole:
    nothing along the surface, a single lobe downwards, and less at every
    hydrophone of the ISO 17208-1 string than the source would give alone.
    Above it one frequency shows lobes of up to twice the pressure and
    nulls between them. The level along the string is read against a run
    of the same source with the surface taken away, and lands on the field
    of the pair.
    """
    from matplotlib import patheffects

    T = _translate_str
    fields = _lloyd_mirror_fields()
    outline = [patheffects.withStroke(linewidth=2.0, foreground=FIELD_STROKE)]

    fig = _anim_figure()
    fig.suptitle(
        T(
            "Lloyd's mirror: a source under the sea surface "
            "and its inverted image (2D FDTD)"
        )
    )
    gs = fig.add_gridspec(
        2, 3, width_ratios=[1.0, 1.0, 0.86], height_ratios=[1.0, 0.16]
    )
    panels = [
        _lm_field_panel(fig, gs[0, i], fields, i, outline=outline) for i in (0, 1)
    ]
    verdicts = [
        T(
            "source and image nearly cancel:\npower mean of the three, "
            f"{_fmt_minus(fields.means[0], '+.1f')} dB"
        ),
        T(
            "lobes and nulls of a single frequency:\npower mean of the three, "
            f"{_fmt_minus(fields.means[1], '+.1f')} dB"
        ),
    ]
    v_txts = []
    for i in (0, 1):
        note = fig.add_subplot(gs[1, i])
        note.axis("off")
        v_txts.append(
            note.text(
                0.5,
                0.5,
                "",
                transform=note.transAxes,
                ha="center",
                va="center",
                color=COLOR_FG,
                fontsize=7,
            )
        )
        # Outside the layout: the panels must not move when the verdict comes up.
        v_txts[-1].set_in_layout(False)

    ax_l = fig.add_subplot(gs[:, 2])
    _grid_axes(ax_l)
    ax_l.set_title(T("Level at the hydrophones"), fontsize=10)
    ax_l.set_xlabel(T(r"depression angle $\alpha$ [°]"), fontsize=8)
    ax_l.set_ylabel(T("level re the source alone [dB]"), fontsize=8)
    ax_l.set_xlim(0.0, 48.0)
    ax_l.set_ylim(_LM_LEVEL_BOTTOM, _LM_LEVEL_TOP)
    ax_l.set_xticks([0.0, 15.0, 30.0, 45.0])
    ax_l.set_yticks([-30.0, -20.0, -10.0, 0.0, 10.0])
    ax_l.tick_params(labelsize=7)
    for i, angle in enumerate((15.0, 30.0, 45.0)):
        # Spanning the reading band, not the frame: the strip below it is
        # the legend's.
        ax_l.plot(
            [angle, angle],
            [_LM_LEVEL_FLOOR, _LM_LEVEL_TOP],
            color=COLOR_TERTIARY,
            ls=":",
            lw=1.2,
            label=T("hydrophones at 15°, 30° and 45°") if i == 0 else None,
        )
    ax_l.plot(
        [0.0, 48.0], [0.0, 0.0], color=COLOR_FG, lw=0.9, label=T("the source alone")
    )
    twice = 10.0 * math.log10(2.0)
    ax_l.plot(
        [0.0, 48.0],
        [twice, twice],
        color=COLOR_FG,
        lw=0.9,
        ls="-.",
        label=T("twice the power of one source"),
    )
    for i in (0, 1):
        ax_l.plot(
            fields.alpha,
            fields.model[i],
            ls="--",
            color=COLOR_FG,
            lw=1.2,
            alpha=0.75,
            label=T("source + inverted image") if i == 0 else None,
        )
    lines = [
        ax_l.plot([], [], color=color, lw=2.0, label=T(f"{_LM_FREQS[i]:g} Hz, FDTD"))[0]
        for i, color in enumerate((COLOR_PRIMARY, COLOR_SECONDARY))
    ]
    ax_l.legend(
        fontsize=6.5,
        loc="lower center",
        framealpha=0.92,
        borderpad=0.4,
        labelspacing=0.3,
        borderaxespad=0.4,
    )
    t_txt = fig.text(
        0.02,
        0.935,
        "",
        ha="left",
        va="top",
        family="monospace",
        fontsize=10,
        color=COLOR_FG,
    )

    def update(k: int) -> tuple[Any, ...]:
        for i, (im, ghost, air_rows) in enumerate(panels):
            frame = fields.frames[i][k]
            im.set_data(frame)
            ghost.set_data(_lm_ghost(frame, air_rows))
            lines[i].set_data(fields.alpha, fields.levels[i][k])
            v_txts[i].set_text(verdicts[i] if k >= fields.reveal else "")
        t_txt.set_text(T(f"$t$ = {fields.times[k] * 1000.0:5.1f} ms"))
        return (*lines, *v_txts, t_txt)

    _render_clip(
        fig,
        update,
        output_dir,
        "anim_fdtd_lloyd_mirror",
        frames=int(fields.times.size),
        fps=_LM_FPS,
        gif_fps=5,
    )
