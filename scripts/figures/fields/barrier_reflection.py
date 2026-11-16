#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The EN 1793-5 measurement: a pulse, a barrier and the window that reads it."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import numpy as np

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
from ._core import _host, _settle, _solid_in_field

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from matplotlib.gridspec import SubplotSpec
    from matplotlib.image import AxesImage
    from matplotlib.lines import Line2D
    from matplotlib.patheffects import AbstractPathEffect
    from matplotlib.text import Text
    from numpy.typing import NDArray

    from phonometry.simulation import FDTD2D, Compute

# The two samples: the 4 m of a qualification test (EN 1793-5, 5.5.7) and a
# lower one, inside the range of heights Figure 14 covers (2 m to 8 m). The
# loudspeaker stands at half the height of each (3.11), the distances to the
# reference plane are the library's (1.50 m and 0.25 m, 3.13 and 3.14), and
# the window of each sample and its low frequency limit are the ones
# ``reflection_low_frequency_limit`` returns for microphone 5.
_BR_HEIGHTS = (4.0, 2.5)
#: Speed of sound [m/s]: the 340 m/s NOTE 1 of 5.6.1 computes with, and the
#: guide's own comparison with Figure 14.
_BR_C = 340.0
#: Microphone 5, the centre of the grid, as the library indexes it.
_BR_MICROPHONE = 4
# The pulse. The source term is the derivative of a Gaussian, which a line
# source radiates as a single main peak between two shallow lobes of the
# other sign, 0.8 ms long in all: shorter than the 1.47 ms between the direct
# sound and the reflection, so the arrivals stand apart on the trace. (A
# loudspeaker's impulse response lasts up to 3 ms, 5.4.2, and overlaps the
# reflection: that is why the standard subtracts the free-field record, and
# the clip subtracts it too.)
_BR_F0 = 2000.0
# Mesh rule dx = min(smallest geometric dimension / 4, shortest wavelength
# / 8). The smallest dimension is the 0.25 m between the grid and the
# reference plane (62.5 mm); the pulse radiates most at 1.7 kHz (wavelength
# 0.20 m, 25 mm an eighth). dx = 6.25 mm sits four times finer, and puts
# every distance of the set-up on the grid: 240 cells from the loudspeaker
# to the plane, 40 from the microphone, 640 and 400 of height. The
# loudspeaker and the microphone are grid vertices, each the four cells
# around one, so their distances to the reference plane and to the ground,
# which are cell faces, are exact.
_BR_DX = 0.00625
#: Thickness of the sample [m]. Not an acoustic dimension of the scene: the
#: face reflects and the top edge diffracts whatever stands behind them.
_BR_THICKNESS = 0.15
# The view [m]: from behind the loudspeaker to behind the sample, and from
# the ground to over the top edge of the taller one.
_BR_VIEW_LEFT = 0.8
_BR_VIEW_BEHIND = 0.55
_BR_VIEW_TOP = 4.6
#: Every second cell is drawn: 16 stored cells per wavelength at 1.7 kHz.
_BR_STRIDE = 2
#: Sponge thickness [cells]. No sponge echo reaches the microphone inside
#: the clip (see ``_br_clearance``), so it only keeps the picture clean.
_BR_SPONGE = 100
# Timeline. The last arrival the clip names is the diffraction by the top
# edge of the 4 m sample, hypot(1.5, 2) + hypot(0.25, 2) = 4.516 m from the
# loudspeaker, 13.28 ms at 340 m/s; 15 ms let it pass the microphone, 1.13
# times its flight. Time runs from the instant the loudspeaker emits the
# peak of the pulse, read from the free-field record, so each arrival peaks
# at its path over the speed of sound.
# Sampling: one frame per solver step, dt = 0.6 dx / (c sqrt(2)) = 7.80 us,
# 74 frames per period at 1.7 kHz (64 at 2 kHz). 1 923 frames at 120 fps
# run 16.0 s, 0.94 ms of simulation per second of playback.
_BR_SPAN = 15.0e-3
_BR_FPS = 120


@dataclass(frozen=True)
class _BrSample:
    """One sample of the clip: its field, its records and its window.

    :ivar height: The height of the sample [m].
    :ivar source_height: The height of the loudspeaker and of microphone 5 [m].
    :ivar frames: The pressure frames, re the direct peak at the microphone.
    :ivar front: The record in front of the sample at each frame, re its
        direct peak.
    :ivar reflected: The same record with the free-field one subtracted.
    :ivar window: The Adrienne window of the reflected component on the frame
        clock, zero outside it.
    :ivar window_length: Its length [s].
    :ivar limit_hz: The low frequency limit of that window [Hz].
    :ivar arrivals: Geometric arrival times at the microphone [s]: direct,
        reflection, ground reflection, top-edge diffraction.
    :ivar closes: The frame at which the window has closed.
    """

    height: float
    source_height: float
    frames: NDArray[np.float32]
    front: NDArray[np.float64]
    reflected: NDArray[np.float64]
    window: NDArray[np.float64]
    window_length: float
    limit_hz: float
    arrivals: tuple[float, float, float, float]
    closes: int


@dataclass(frozen=True)
class _BrFields:
    """What the three runs leave for the clip to draw.

    :ivar samples: The tall sample and the low one.
    :ivar times: The frame times [s], from the emission of the pulse's peak.
    :ivar source_distance: Loudspeaker to reference plane [m].
    :ivar microphone_distance: Microphone to reference plane [m].
    :ivar extent: The view: left, right and top [m], the loudspeaker at x = 0.
    """

    samples: tuple[_BrSample, _BrSample]
    times: NDArray[np.float64]
    source_distance: float
    microphone_distance: float
    extent: tuple[float, float, float]


def _br_waveform(dt: float) -> tuple[NDArray[np.float64], float]:
    """The source term on the solver's own clock, and its sample rate [Hz].

    The derivative of a Gaussian of half-width ``1 / (pi f0)``, centred 1.5
    periods of ``f0`` after the start so it leaves from zero, with its sign
    chosen so the radiated pulse peaks upwards.
    """
    centre = 1.5 / _BR_F0
    t = np.arange(math.ceil(2.0 * centre / dt) + 1) * dt
    a = np.pi * _BR_F0 * (t - centre)
    return np.asarray(a * np.exp(-(a**2)), dtype=np.float64), 1.0 / dt


def _br_clearance(duration: float, direct: float) -> tuple[int, int, int]:
    """Cells of clear path a boundary needs so its echo misses the record.

    An echo of the pulse from a boundary reaches the microphone later than
    ``duration`` when the boundary lies this far from the loudspeaker: on
    the side away from the microphone, on the microphone's side, and across
    the line that joins them. The free-field run is a rigid box of this
    size, so its record holds the direct sound and nothing else, by
    causality and not by the quality of a sponge.
    """
    reach = _BR_C * duration
    away = (reach - direct) / 2.0
    towards = (reach + direct) / 2.0
    across = math.sqrt((reach / 2.0) ** 2 - (direct / 2.0) ** 2)
    return (
        math.ceil(away / _BR_DX) + 1,
        math.ceil(towards / _BR_DX) + 1,
        math.ceil(across / _BR_DX) + 1,
    )


def _br_vertex(nx: int, row: int, column: int) -> NDArray[np.intp]:
    """Flat indices of the four cells around the grid vertex (row, column)."""
    return np.array(
        [
            (row - 1) * nx + column - 1,
            (row - 1) * nx + column,
            row * nx + column - 1,
            row * nx + column,
        ]
    )


def _br_drive(sim: FDTD2D, row: int, column: int) -> None:
    """Put the pulse on the four cells around the vertex (row, column)."""
    from phonometry.simulation import SignalSource

    samples, rate = _br_waveform(sim.dt)
    for iy in (row - 1, row):
        for ix in (column - 1, column):
            sim.add_source(
                SignalSource(ix=ix, iy=iy, samples=samples, fs=rate, amplitude=0.25)
            )


def _br_step(
    sim: FDTD2D,
    microphone: NDArray[np.intp],
    *,
    steps: int,
    skip: int = 0,
    view: tuple[slice, slice] | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float32] | None]:
    """Step *sim* and bring back the microphone record and the frames.

    The record is the mean of the pressure over the four ``microphone``
    cells after every step; the frames are the pressure over ``view`` after
    each step past the first ``skip``. Both stay on the engine's device
    until the loop ends or a frame is captured.
    """
    backend = sim._backend
    xp = backend.xp
    cells = backend.index(microphone)
    record: list[Any] = []
    frames: list[NDArray[np.float32]] = []
    for step in range(steps):
        sim.step()
        p = sim.p
        record.append(xp.take(xp.reshape(p, (-1,)), cells))
        if view is not None and step >= skip:
            frames.append(_host(sim, p[view]))
    history = _host(sim, xp.stack(record), dtype=np.float64).mean(axis=1)
    return history, (np.stack(frames) if frames else None)


def _br_free_field(steps: int, direct: float, compute: Compute) -> NDArray[np.float64]:
    """The free-field record: the same pulse and microphone, nothing else.

    A rigid box large enough that no echo comes back inside the record
    (:func:`_br_clearance`), the loudspeaker and the microphone the same
    number of cells apart as in front of the sample.
    """
    from phonometry.simulation import FDTD2D

    sim = FDTD2D(c=_BR_C, dx=_BR_DX, shape=(2, 2), compute=compute)
    away, towards, across = _br_clearance(steps * sim.dt, direct)
    nx, ny = away + towards, 2 * across
    sim = FDTD2D(c=_BR_C, dx=_BR_DX, shape=(ny, nx), compute=compute)
    _br_drive(sim, across, away)
    microphone = _br_vertex(nx, across, away + round(direct / _BR_DX))
    record, _ = _br_step(sim, microphone, steps=steps)
    return record


def _br_in_front(
    height: float,
    source_height: float,
    *,
    steps: int,
    skip: int,
    source_distance: float,
    microphone_distance: float,
    compute: Compute,
) -> tuple[NDArray[np.float64], NDArray[np.float32]]:
    """The run in front of a sample: rigid ground, rigid sample, open sky.

    Row 0 is the ground, the rigid edge of the grid; the sample is a block
    of rigid cells standing on it, its face on the reference plane. The
    left side, the right side and the sky absorb, each far enough for the
    echo of its sponge to miss the record.
    """
    from phonometry.simulation import FDTD2D

    probe = FDTD2D(c=_BR_C, dx=_BR_DX, shape=(2, 2), compute=compute)
    direct = source_distance - microphone_distance
    away, _, across = _br_clearance(steps * probe.dt, direct)
    source = _BR_SPONGE + max(away, round(_BR_VIEW_LEFT / _BR_DX))
    face = source + round(source_distance / _BR_DX)
    thick = round(_BR_THICKNESS / _BR_DX)
    behind = round(_BR_VIEW_BEHIND / _BR_DX)
    nx = face + thick + behind + _BR_SPONGE
    row = round(source_height / _BR_DX)
    top = max(round(_BR_VIEW_TOP / _BR_DX), row + across)
    ny = top + _BR_SPONGE
    sample = np.zeros((ny, nx), dtype=bool)
    sample[: round(height / _BR_DX), face : face + thick] = True
    sim = FDTD2D(
        c=_BR_C,
        dx=_BR_DX,
        shape=(ny, nx),
        absorbing_layer_cells=_BR_SPONGE,
        # Row 0 is the ground ("top" in the engine's imshow naming), so the
        # sky is "bottom".
        absorbing_sides=("left", "right", "bottom"),
        obstacle_mask=sample,
        compute=compute,
    )
    _br_drive(sim, row, source)
    microphone = _br_vertex(nx, row, face - round(microphone_distance / _BR_DX))
    view = (
        slice(0, round(_BR_VIEW_TOP / _BR_DX), _BR_STRIDE),
        slice(
            source - round(_BR_VIEW_LEFT / _BR_DX), face + thick + behind, _BR_STRIDE
        ),
    )
    record, frames = _br_step(sim, microphone, steps=steps, skip=skip, view=view)
    if frames is None:
        msg = "the run in front of the sample was asked for frames and returned none"
        raise RuntimeError(msg)
    return record, frames


def _br_window(
    times: NDArray[np.float64], rate: float, reflection: float, length: float
) -> NDArray[np.float64]:
    """The library's Adrienne window laid on the frame clock.

    Its marker point, where the flat part begins, sits the 0.2 ms of 5.5.6
    before the geometric peak of the reflection, and its leading edge the
    0.5 ms of 5.5.5 before that; both leads are the library's own.
    """
    from phonometry.environment.propagation import barrier_reflection as library

    shape = library.adrienne_reflection_window(rate, window_length_s=length)
    begins = reflection - library._MARKER_LEAD_S - library._LEADING_EDGE_S
    first = int(np.searchsorted(times, begins))
    window = np.zeros(times.size)
    window[first : first + shape.size] = shape[: times.size - first]
    return window


@lru_cache(maxsize=1)
def _barrier_reflection_fields() -> _BrFields:
    """The pulse in front of a tall and a low sample, and in the free field.

    Three runs of the acoustic engine. The free-field one gives the direct
    sound at the microphone and, from its peak, the instant the loudspeaker
    emitted it; each run in front of a sample gives the frames and the
    record that holds the direct sound, the reflection and the arrivals the
    window has to shut out. The free-field record is subtracted from it
    sample by sample, as 5.5.4 does, the two runs being the same pulse on
    the same grid.
    """
    import clip_placement

    from phonometry import environment
    from phonometry.environment.propagation import barrier_reflection as library
    from phonometry.simulation import FDTD2D

    compute = clip_placement.compute_for("anim_fdtd_barrier_reflection")
    source_distance = environment.REFLECTION_SOURCE_DISTANCE_M
    microphone_distance = environment.REFLECTION_MICROPHONE_DISTANCE_M
    direct, specular = (
        float(d) for d in environment.reflection_grid_paths_m()[_BR_MICROPHONE]
    )
    dt = float(FDTD2D(c=_BR_C, dx=_BR_DX, shape=(2, 2), compute=compute).dt)
    n_frames = round(_BR_SPAN / dt)
    # Enough steps for the whole pulse to leave before the first frame.
    lead = math.ceil(3.0 / _BR_F0 / dt)
    steps = lead + n_frames
    free = _br_free_field(steps, direct, compute)
    peak = float(np.max(np.abs(free)))
    emitted = (int(np.argmax(np.abs(free))) + 1) * dt - direct / _BR_C
    skip = math.ceil(emitted / dt) - 1
    times = np.asarray((np.arange(skip, skip + n_frames) + 1) * dt - emitted)

    samples: list[_BrSample] = []
    for height in _BR_HEIGHTS:
        limit = environment.reflection_low_frequency_limit(height, speed_of_sound=_BR_C)
        source_height = float(limit.source_height_m)
        rise = height - source_height
        ground = math.hypot(direct, 2.0 * source_height)
        edge = math.hypot(source_distance, rise) + math.hypot(microphone_distance, rise)
        length = float(limit.window_length_s[_BR_MICROPHONE])
        # The window of the library ends with the first unwanted arrival; the
        # clip names both, so it holds its own geometry to the library's.
        first = (min(ground, edge) - specular) / _BR_C + library._LEADING_EDGE_S
        if abs(first - length) > 1.0e-9:
            msg = (
                f"the window of the {height:g} m sample is {length!r} s in the "
                f"library and {first!r} s by the geometry of the clip"
            )
            raise RuntimeError(msg)
        record, frames = _br_in_front(
            height,
            source_height,
            steps=steps,
            skip=skip,
            source_distance=source_distance,
            microphone_distance=microphone_distance,
            compute=compute,
        )
        chosen = slice(skip, skip + n_frames)
        window = _br_window(times, 1.0 / dt, specular / _BR_C, length)
        samples.append(
            _BrSample(
                height=height,
                source_height=source_height,
                frames=frames[:n_frames] / np.float32(peak),
                front=record[chosen] / peak,
                reflected=(record[chosen] - free[chosen]) / peak,
                window=window,
                window_length=length,
                limit_hz=float(limit.low_frequency_limit_hz[_BR_MICROPHONE]),
                arrivals=(
                    direct / _BR_C,
                    specular / _BR_C,
                    ground / _BR_C,
                    edge / _BR_C,
                ),
                closes=min(int(np.flatnonzero(window)[-1]) + 1, times.size - 1),
            )
        )
    return _BrFields(
        samples=(samples[0], samples[1]),
        times=times,
        source_distance=source_distance,
        microphone_distance=microphone_distance,
        extent=(
            -_BR_VIEW_LEFT,
            source_distance + _BR_THICKNESS + _BR_VIEW_BEHIND,
            _BR_VIEW_TOP,
        ),
    )


#: Half-range of the colour ramp, re the direct peak at the microphone: the
#: fronts spread as a cylinder, so the ramp is set where the ground
#: reflection and the diffracted front, the faint ones, still show.
_BR_RAMP = 0.5
#: Depth of the ground strip under the field [m].
_BR_GROUND = 0.3
#: Vertical range of the traces, re the direct peak, and the three heights
#: the arrivals are named at.
_BR_TRACE = (-1.0, 1.95)
_BR_NAMES = (1.2, 1.45, 1.7)


def _br_field_panel(
    fig: Figure,
    cell: SubplotSpec,
    fields: _BrFields,
    index: int,
    *,
    outline: Sequence[AbstractPathEffect],
) -> AxesImage:
    """One sample in section: the field, the ground, the sample and the set-up."""
    from matplotlib.patches import Rectangle

    T = _translate_str
    sample = fields.samples[index]
    left, right, top = fields.extent
    ax = fig.add_subplot(cell)
    ax.grid(visible=False)
    im = ax.imshow(
        sample.frames[0],
        origin="lower",
        extent=(left, right, 0.0, top),
        cmap=CMAP_FIELD,
        vmin=-_BR_RAMP,
        vmax=_BR_RAMP,
        interpolation="bilinear",
    )
    ax.set_xlim(left, right)
    ax.set_ylim(-_BR_GROUND, top)
    ax.set_aspect("equal")
    solid = _solid_in_field(ax)
    ax.add_patch(
        Rectangle(
            (left, -_BR_GROUND),
            right - left,
            _BR_GROUND,
            facecolor=solid,
            edgecolor=COLOR_FG,
            lw=0.8,
            hatch="///",
        )
    )
    ax.add_patch(
        Rectangle(
            (fields.source_distance, 0.0),
            _BR_THICKNESS,
            sample.height,
            facecolor=solid,
            edgecolor=COLOR_FG,
            lw=0.8,
        )
    )
    ax.set_title(T(f"{sample.height:g} m sample"), fontsize=9.5)
    label: dict[str, Any] = {
        "ha": "center",
        "color": FIELD_INK,
        "fontsize": 6.5,
        "path_effects": outline,
    }
    ax.plot(
        [0.0],
        [sample.source_height],
        marker="o",
        ms=4,
        color=COLOR_TERTIARY,
        markeredgecolor=FIELD_STROKE,
        markeredgewidth=0.6,
    )
    ax.text(0.0, sample.source_height - 0.16, T("loudspeaker"), va="top", **label)
    microphone = fields.source_distance - fields.microphone_distance
    ax.plot(
        [microphone],
        [sample.source_height],
        marker="o",
        ms=4,
        color="white",
        markeredgecolor="black",
        markeredgewidth=0.8,
    )
    ax.text(
        microphone - 0.1,
        sample.source_height + 0.2,
        T("microphone 5"),
        va="bottom",
        **{**label, "ha": "right"},
    )
    ax.set_xticks([0.0, 1.0, 2.0])
    ax.set_yticks([0.0, 1.0, 2.0, 3.0, 4.0])
    ax.tick_params(labelsize=7)
    # Both panels carry the same labels, so the layout gives them the same
    # box: with the height named on one alone, the other comes out a tenth
    # larger and the two sections are no longer on one scale.
    ax.set_xlabel(T("from the loudspeaker [m]"), fontsize=8)
    ax.set_ylabel(T("height [m]"), fontsize=8)
    return im


def _br_trace_panel(
    fig: Figure, cell: SubplotSpec, fields: _BrFields, index: int
) -> tuple[Axes, tuple[Line2D, Line2D, Line2D], Text]:
    """The record at microphone 5 of one sample, its arrivals named.

    Returns the axes, the three lines (the record, the record with the
    free-field one subtracted, the window) and the text that comes up when
    the window has closed: its length and its low frequency limit.
    """
    T = _translate_str
    sample = fields.samples[index]
    ax = fig.add_subplot(cell)
    _grid_axes(ax)
    ax.set_xlim(0.0, _BR_SPAN * 1.0e3)
    ax.set_xticks([0.0, 3.0, 6.0, 9.0, 12.0, 15.0])
    ax.set_ylim(*_BR_TRACE)
    ax.set_yticks([-1.0, 0.0, 1.0])
    ax.tick_params(labelsize=7)
    ax.set_title(
        T(f"Microphone 5 in front of the {sample.height:g} m sample"), fontsize=9
    )
    # Each arrival is named over its own line. The names of arrivals that
    # follow closely stand on different rows, so no name meets another or
    # the line of another arrival, whose line stops under its own name: the
    # reflection runs to the right of its line on the lowest row, and the
    # two unwanted arrivals run to the left of theirs on a row each, because
    # at the tall sample they come a millisecond apart and less than two
    # from the end of the record.
    names = (
        (T("direct"), 0, "center"),
        (T("reflection"), 0, "left"),
        (T("ground"), 1, "right"),
        (T("top edge"), 2, "right"),
    )
    for arrival, (name, row, align) in zip(sample.arrivals, names, strict=True):
        height = _BR_NAMES[row]
        at = arrival * 1.0e3
        ax.plot(
            [at, at],
            [_BR_TRACE[0] + 0.38, height - 0.09],
            color=COLOR_TERTIARY,
            ls=":",
            lw=1.0,
        )
        ax.text(
            at + {"left": -0.12, "center": 0.0, "right": 0.12}[align],
            height,
            name,
            ha=align,
            va="center",
            color=COLOR_FG,
            fontsize=6.5,
        )
    front = ax.plot([], [], color=COLOR_FG, lw=0.8)[0]
    reflected = ax.plot([], [], color=COLOR_PRIMARY, lw=1.7)[0]
    window = ax.plot([], [], color=COLOR_SECONDARY, lw=1.4)[0]
    verdict = ax.text(
        0.985,
        0.04,
        "",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        color=COLOR_FG,
        fontsize=6.5,
    )
    return ax, (front, reflected, window), verdict


def animate_fdtd_barrier_reflection(output_dir: str) -> None:
    """The EN 1793-5 pulse in front of a 4 m sample and of a 2.5 m one.

    A vertical section through the loudspeaker and microphone 5: the pulse
    passes the microphone, comes back from the face of the sample, and is
    followed by what the method has to keep out, the reflection from the
    ground and the diffraction by the top edge (5.5.7). The record at the
    microphone fills in with the field; with the free-field record
    subtracted (5.5.4) what is left starts at the reflection, and the
    Adrienne window of the library is laid over it, its marker point 0.2 ms
    before the geometric peak (5.5.6). A lower sample brings both unwanted
    arrivals earlier, the window that ends before them is shorter, and a
    shorter window reaches less far down. Both the ground and the sample
    are rigid, and the section shows no side edge.
    """
    from matplotlib import patheffects
    from matplotlib.lines import Line2D

    T = _translate_str
    fields = _barrier_reflection_fields()
    outline = [patheffects.withStroke(linewidth=2.0, foreground=FIELD_STROKE)]
    ms = fields.times * 1.0e3

    fig = _anim_figure()
    sup = fig.suptitle(
        T("EN 1793-5 in situ: the reflection and what the window shuts out (2D FDTD)")
    )
    gs = fig.add_gridspec(2, 3, width_ratios=[1.0, 1.0, 1.5])
    images = [
        _br_field_panel(fig, gs[:, i], fields, i, outline=outline) for i in (0, 1)
    ]
    traces = [_br_trace_panel(fig, gs[i, 2], fields, i) for i in (0, 1)]
    traces[0][0].tick_params(labelbottom=False)
    traces[1][0].set_xlabel(
        T("time since the pulse left the loudspeaker [ms]"), fontsize=8
    )
    for ax, _, _ in traces:
        ax.set_ylabel(T("pressure re the direct peak"), fontsize=7.5)
    verdicts = [
        T(
            f"window {sample.window_length * 1.0e3:.1f} ms: "
            f"low frequency limit {sample.limit_hz:.0f} Hz"
        )
        for sample in fields.samples
    ]
    # One key for the two traces, under the whole figure: in the column of
    # the traces it is wider than they are, and the layout would narrow them
    # to make room for it.
    fig.legend(
        handles=[
            Line2D([], [], color=COLOR_FG, lw=0.8, label=T("in front of the sample")),
            Line2D(
                [],
                [],
                color=COLOR_PRIMARY,
                lw=1.7,
                label=T("free-field record subtracted"),
            ),
            Line2D([], [], color=COLOR_SECONDARY, lw=1.4, label=T("Adrienne window")),
        ],
        loc="outside lower center",
        ncol=3,
        fontsize=6.5,
        frameon=False,
        handlelength=1.6,
        columnspacing=1.2,
    )
    t_txt = fig.text(
        0.012,
        0.985,
        "",
        ha="left",
        va="top",
        family="monospace",
        fontsize=10,
        color=COLOR_FG,
    )
    spans = [np.flatnonzero(sample.window)[[0, -1]] for sample in fields.samples]

    def fit_title() -> None:
        # The title is centred on the canvas and the clock owns the top-left
        # corner: the clock is drawn at its widest, both are measured, and
        # the title steps down until 0.6 in of daylight separates them.
        t_txt.set_text(T(f"$t$ = {fields.times[-1] * 1000.0:4.1f} ms"))
        _settle(fig)
        # The ignores: ``get_fontsize`` is typed ``float | str`` for the
        # named sizes ("small"), which this title, set from rcParams, never
        # carries.
        while (
            sup.get_window_extent().x0 - t_txt.get_window_extent().x1 < 0.6 * fig.dpi
            and sup.get_fontsize() > 8.0  # type: ignore[operator]
        ):
            sup.set_fontsize(sup.get_fontsize() - 0.25)  # type: ignore[operator]
        t_txt.set_text("")

    def update(k: int) -> tuple[Any, ...]:
        artists: list[Any] = [t_txt]
        for i, sample in enumerate(fields.samples):
            images[i].set_data(sample.frames[k])
            front, reflected, window = traces[i][1]
            front.set_data(ms[: k + 1], sample.front[: k + 1])
            reflected.set_data(ms[: k + 1], sample.reflected[: k + 1])
            # The window is drawn as far as the record has got, and never
            # before it opens: a zero would lie on the axis like a record.
            first, last = (int(n) for n in spans[i])
            shown = slice(first, max(first, min(k, last) + 1))
            window.set_data(ms[shown], sample.window[shown])
            # The length and the limit come up when the window has closed,
            # so neither number is shown before what it measures.
            traces[i][2].set_text(verdicts[i] if k >= sample.closes else "")
            artists += [images[i], front, reflected, window, traces[i][2]]
        t_txt.set_text(T(f"$t$ = {fields.times[k] * 1000.0:4.1f} ms"))
        return tuple(artists)

    _render_clip(
        fig,
        update,
        output_dir,
        "anim_fdtd_barrier_reflection",
        frames=int(fields.times.size),
        fps=_BR_FPS,
        gif_fps=5,
        measure=fit_title,
    )
