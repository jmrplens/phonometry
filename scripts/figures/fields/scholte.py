#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Water over the van Vossen seabed: the train the contact keeps while the fronts leave."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import numpy as np

from phonometry.simulation import Material, scholte_speed

from ..media import _ANIM_PILL_BOX, _anim_figure, _render_clip, _translate_str
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
    from matplotlib.figure import Figure
    from matplotlib.gridspec import SubplotSpec
    from matplotlib.image import AxesImage
    from matplotlib.lines import Line2D
    from matplotlib.text import Text
    from numpy.typing import NDArray

# The media of the still figure this clip sits under
# (simulation/elastic-waves.mdx section 6) and of the solver's own Scholte
# test: the benchmark of van Vossen, Robertsson & Chapman (2002), a fluid of
# 1500 m/s and 1000 kg/m3 over a solid of 3500 / 2000 m/s and 2500 kg/m3,
# with a line explosion 10 m above the contact that emits a 50 Hz Ricker
# wavelet (their METHOD section, folio 620).
_SCH_FLUID = Material(c_p=1500.0, c_s=0.0, rho=1000.0)
_SCH_SOLID = Material(c_p=3500.0, c_s=2000.0, rho=2500.0)
_SCH_F0 = 50.0  # Ricker peak frequency [Hz]
#: When the wavelet peaks [s]: the fronts the clip marks leave the shot then.
_SCH_T0 = 0.030
_SCH_SHOT_HEIGHT = 10.0  # the shot above the contact [m]
# Mesh rule dx = min(smallest geometric dimension / 4, shortest wavelength
# / 8). The smallest dimension is the 10 m between the shot and the contact
# (2.5 m); the Ricker spectrum is 20 dB down at 2.21 f0 = 110.6 Hz, where
# the slowest wave of the scene, the Scholte train at 1436 m/s, is 13.0 m
# long, so lambda / 8 = 1.6 m. The grid runs at 0.5 m, three times finer,
# because an interface wave is where the second-order scheme is slowest:
# at 1 m, 29 cells per Scholte wavelength at 50 Hz, the solver's own test
# times the train 1.5 % late, and over the 780 m this clip follows it that
# would leave the train 12 m behind the dot drawn at the exact speed, a
# third of the lead of the water front the clip is about. At 0.5 m (57
# cells) the error is a quarter of that.
_SCH_DX = 0.5
# Domain and view. The direct water front leaves the Scholte train behind
# at only 64 m/s, so it leads it by one Scholte wavelength at 50 Hz (28.7 m)
# only after the train has run 644 m: the finish line of the clip is 650 m
# from the shot. The view runs from 40 m behind the shot to 840 m ahead of
# it, and not to 650, for the reason clip-mates anim_fdtd_dispersion and
# anim_fdtd_critical_angle give: over a window scaled to the finish line the
# train runs a fifth as far again, to 780 m, and a view sized on the line
# would close the clip with the train already out of it. It shows 80 m to
# either side of the contact. A 60 m sponge closes every side, with 20 m of
# margin above and below so that the 1/e depth of the train (0.55
# wavelengths, 16 m at 50 Hz) never reaches one.
_SCH_BEHIND = 40.0
_SCH_AHEAD = 840.0
_SCH_FINISH = 650.0
_SCH_HALF = 80.0
_SCH_MARGIN = 20.0
_SCH_SPONGE = 60.0
#: Where the pressure is read [m ahead of the shot]: two cells on the
#: contact, the 300 m apart the solver's test times the train over, and one
#: 30 m up into the water above the second, as in that test.
_SCH_PROBES = (100.0, 400.0)
_SCH_PROBE_UP = 30.0
# Timeline per the animation norms. Flight: the slowest wave of interest,
# the Scholte train at 1436 m/s, takes 452.7 ms from the shot to the finish
# line, leaving when the wavelet peaks at 30 ms; so 30 + 1.2 x 452.7 =
# 573.2 ms is captured, and the last frame, which is also the poster, has
# the train 60 m inside the far edge with its verdict up. Sampling: dt =
# 0.6 dx / (c_P sqrt(2)) = 60.61 us, a stride of 6 gives a frame every
# 0.364 ms, i.e. 55.0 frames per period of the 50 Hz the wavelet peaks at
# (>= the 48 the clips keep), and 1 577 frames, played at 100 fps: 15.8 s,
# plus a 2 s hold.
_SCH_EVERY = 6
_SCH_FPS = 100.0
_SCH_HOLD = round(2.0 * _SCH_FPS)
#: The corner of the view the names of the media are written in: ranges
#: under the first and, in the water, depths above the second [m].
_SCH_NAME_CLEAR = (110.0, -58.0)
#: How far the Scholte root has to have run [m] before the two marks get
#: their symbols and the lead its readout: closer in, they sit on the shot.
_SCH_LABEL_FROM = 80.0


def _sch_cells(length_m: float) -> int:
    """Whole cells in *length_m* metres of this grid."""
    return round(length_m / _SCH_DX)


def _sch_ricker(t: float) -> float:
    """The 50 Hz Ricker wavelet of the benchmark, peaking at ``_SCH_T0``."""
    a = (np.pi * _SCH_F0 * (t - _SCH_T0)) ** 2
    return float((1.0 - 2.0 * a) * np.exp(-a))


def _sch_peak(times: NDArray[np.float64], trace: NDArray[np.float64]) -> float:
    """When the envelope of *trace* peaks [s], between samples.

    The envelope is the magnitude of the analytic signal, as in the solver's
    own time-of-flight test; the three samples round its maximum fix a
    parabola whose vertex is the peak, so the reading is not held to the
    0.36 ms between captured frames.
    """
    from scipy.signal import hilbert

    env = np.abs(hilbert(trace))
    k = int(np.clip(env.argmax(), 1, env.size - 2))
    lo, mid, hi = env[k - 1], env[k], env[k + 1]
    curve = lo - 2.0 * mid + hi
    shift = 0.0 if curve >= 0.0 else 0.5 * (lo - hi) / curve
    return float(times[k] + shift * (times[k + 1] - times[k]))


@lru_cache(maxsize=1)
def _scholte_fields() -> tuple[Any, Any, Any, float, float]:
    """One shot over the water-seabed contact, cached.

    The benchmark scene of the still figure, run long and wide enough for
    what one frame cannot show: sponges on all four sides, the explosion
    10 m above the contact, and the run kept on until the water front leads
    the Scholte train by more than one of its wavelengths.

    The frames hold the vertical particle velocity over the view, one sample
    per metre. Three cells give the pressure, ``-(txx + tyy) / 2`` in the
    fluid: two on the contact, 100 m and 400 m from the shot, and one 30 m
    above the second. The train is the largest thing either contact cell
    ever sees, so its speed is the 300 m between them over the time between
    the peaks of the two envelopes, which is the measurement the solver's
    test makes.

    Returns the ``vy`` stack in units of the train's own peak, the three
    pressure traces in units of the first contact cell's peak, the frame
    times, the measured speed of the train and the fraction of the contact
    amplitude left 30 m up as the train passes.
    """
    import clip_placement

    from phonometry import simulation

    compute = clip_placement.compute_for("anim_elastic_scholte")
    dx = _SCH_DX
    sponge = _sch_cells(_SCH_SPONGE)
    top = sponge + _sch_cells(_SCH_MARGIN)
    half = _sch_cells(_SCH_HALF)
    iface = top + half
    ny = iface + half + top
    src_ix = sponge + _sch_cells(_SCH_BEHIND)
    nx = src_ix + _sch_cells(_SCH_AHEAD) + sponge
    sim = simulation.ElasticFDTD2D.from_regions(
        (ny, nx),
        dx,
        background=_SCH_FLUID,
        regions=[((slice(iface, None), slice(None)), _SCH_SOLID)],
        absorbing_layer_cells=sponge,
        compute=compute,
    )
    sim.add_source(
        simulation.ExplosionSource(
            ix=src_ix,
            iy=iface - _sch_cells(_SCH_SHOT_HEIGHT),
            waveform=_sch_ricker,
            amplitude=1e3,
        )
    )
    v_exact = scholte_speed(_SCH_FLUID, _SCH_SOLID)
    t_end = _SCH_T0 + 1.2 * _SCH_FINISH / v_exact
    n_active = int(np.ceil(t_end / (_SCH_EVERY * sim.dt)))
    # One sample per metre: the view is drawn 2 100 px wide for its 880 m.
    stride = max(1, _sch_cells(1.0))
    rows = slice(iface - half, iface + half, stride)
    cols = slice(sponge, nx - sponge, stride)
    xp = sim._backend.xp
    probe_cols = [src_ix + _sch_cells(x) for x in _SCH_PROBES]
    contact = sim._backend.index(np.asarray(probe_cols, dtype=np.int64))
    above = sim._backend.index(np.asarray(probe_cols[1:], dtype=np.int64))
    row_c = iface - 1
    row_u = row_c - _sch_cells(_SCH_PROBE_UP)
    frames: list[Any] = []
    on_contact: list[Any] = []
    up: list[Any] = []
    ts: list[float] = []
    while len(frames) < n_active:
        sim.step()
        if sim.n % _SCH_EVERY == 0:
            vy = sim.collocated("vy")
            frames.append(_host(sim, vy[rows, cols]))
            on_contact.append(xp.take(sim.txx[row_c] + sim.tyy[row_c], contact))
            up.append(xp.take(sim.txx[row_u] + sim.tyy[row_u], above))
            ts.append(sim.time)
    stack = np.stack(frames)
    times = np.asarray(ts)
    traces = -0.5 * np.concatenate(
        [
            _host(sim, xp.stack(on_contact), dtype=np.float64),
            _host(sim, xp.stack(up), dtype=np.float64),
        ],
        axis=1,
    )
    t_first = _sch_peak(times, traces[:, 0])
    t_second = _sch_peak(times, traces[:, 1])
    c_meas = float((_SCH_PROBES[1] - _SCH_PROBES[0]) / (t_second - t_first))
    # What is left 30 m up as the train passes below, as the solver's test
    # reads it: the two envelopes over the 20 ms round the contact peak.
    from scipy.signal import hilbert

    env = np.abs(hilbert(traces, axis=0))
    passing = np.abs(times - t_second) < 0.010
    ratio = float(env[passing, 2].max() / env[passing, 1].max())
    # The train in units of its own peak, taken off the second half of the
    # run: the shot is orders of magnitude above anything it launches.
    late = slice(n_active // 2, n_active)
    scale = float(np.abs(stack[late]).max())
    return (
        stack / scale,
        traces / float(np.abs(traces[:, 0]).max()),
        times,
        c_meas,
        ratio,
    )


@dataclass(frozen=True)
class _SchField:
    """The artists of the field panel that move.

    :ivar im: The field image.
    :ivar arc: The water front, dotted at ``c_w (t - t0)`` round the shot.
    :ivar dot: The Scholte root, at ``v_Sch (t - t0)`` along the contact.
    :ivar labels: The two symbols riding the arc and the dot.
    :ivar lead: The readout of how far the water front is ahead.
    """

    im: AxesImage
    arc: Line2D
    dot: Line2D
    labels: tuple[Text, Text]
    lead: Text


def _sch_field_panel(
    fig: Figure, cell: SubplotSpec, data: NDArray[np.float32], vmax: float
) -> _SchField:
    """The field panel: the two media, the shot, the probes and the two marks."""
    from matplotlib import patheffects

    T = _translate_str
    outline = [patheffects.withStroke(linewidth=2.0, foreground=FIELD_STROKE)]
    ax = fig.add_subplot(cell)
    ax.grid(visible=False)
    im = ax.imshow(
        data[0],
        origin="upper",
        extent=(-_SCH_BEHIND, _SCH_AHEAD, _SCH_HALF, -_SCH_HALF),
        cmap=CMAP_FIELD,
        vmin=-vmax,
        vmax=vmax,
        aspect="equal",
        interpolation="bilinear",
    )
    ax.axhline(0.0, color=FIELD_INK, ls=":", lw=0.8, alpha=0.75, zorder=3)
    ax.plot(
        [0.0],
        [-_SCH_SHOT_HEIGHT],
        marker="*",
        ms=8,
        color=COLOR_SECONDARY,
        markeredgecolor=FIELD_STROKE,
        markeredgewidth=0.6,
        zorder=6,
    )
    probes = (
        (_SCH_PROBES[0], 0.0, COLOR_PRIMARY),
        (_SCH_PROBES[1], 0.0, COLOR_SECONDARY),
        (_SCH_PROBES[1], -_SCH_PROBE_UP, COLOR_TERTIARY),
    )
    for x, y, color in probes:
        ax.plot(
            [x],
            [y],
            marker="o",
            ms=4.5,
            color=color,
            markeredgecolor=FIELD_STROKE,
            markeredgewidth=0.8,
            zorder=6,
        )
    media = (
        (-_SCH_HALF + 9.0, f"water {_SCH_FLUID.c_p:.0f} m/s"),
        (_SCH_HALF - 9.0, f"seabed {_SCH_SOLID.c_p:.0f} / {_SCH_SOLID.c_s:.0f} m/s"),
    )
    for y, medium in media:
        ax.text(
            -_SCH_BEHIND + 8.0,
            y,
            T(medium),
            fontsize=8,
            ha="left",
            va="center",
            color=FIELD_INK,
            path_effects=outline,
            zorder=5,
        )
    (arc,) = ax.plot([], [], ls=":", lw=1.0, color=FIELD_INK, zorder=4)
    (dot,) = ax.plot(
        [],
        [],
        marker="o",
        ms=5,
        ls="none",
        color=FIELD_INK,
        markeredgecolor=FIELD_STROKE,
        markeredgewidth=0.8,
        zorder=7,
    )
    labels = tuple(
        ax.text(
            0.0,
            0.0,
            symbol,
            fontsize=8.5,
            ha=ha,
            va="center",
            color=FIELD_INK,
            path_effects=outline,
            zorder=7,
            visible=False,
        )
        for symbol, ha in ((r"$c_\mathrm{w}$", "right"), (r"$v_\mathrm{Sch}$", "right"))
    )
    ax.set_ylabel(T("depth below the contact [m]"), fontsize=8)
    ax.set_xlabel(T("range from the shot [m]"), fontsize=8)
    ax.set_yticks([-50.0, 0.0, 50.0])
    ax.set_xticks(np.arange(0.0, _SCH_AHEAD + 1.0, 100.0))
    ax.tick_params(labelsize=7)
    lead = ax.text(
        _SCH_AHEAD - 8.0,
        _SCH_HALF - 6.0,
        "",
        ha="right",
        va="bottom",
        color="white",
        fontsize=7.5,
        zorder=8,
        linespacing=1.35,
        bbox={
            "boxstyle": _ANIM_PILL_BOX,
            "facecolor": "black",
            "alpha": 0.55,
            "edgecolor": "none",
        },
    )
    return _SchField(im=im, arc=arc, dot=dot, labels=(labels[0], labels[1]), lead=lead)


def _sch_water_arc(radius: float) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """The part of the water front that is in the water and in the view.

    A circle of *radius* round the shot, 10 m above the contact: the points
    of it at or above the contact, as ranges from the shot and depths below
    the contact (negative in the water).
    """
    angle = np.linspace(-0.5 * np.pi, 0.5 * np.pi, 721)
    x = radius * np.cos(angle)
    y = -_SCH_SHOT_HEIGHT + radius * np.sin(angle)
    keep = (y <= 0.0) & (y >= -_SCH_HALF) & (x <= _SCH_AHEAD)
    # The upper end of the front passes behind the name of the water in its
    # first 50 ms; it is not drawn through it.
    keep &= ~((x < _SCH_NAME_CLEAR[0]) & (y < _SCH_NAME_CLEAR[1]))
    return x[keep], y[keep]


def _sch_place_marks(
    panel: _SchField, since_peak: float, v_exact: float
) -> float | None:
    """Put the water front and the Scholte root where they are; return the lead [m].

    The front is the circle ``c_w (t - t0)`` round the shot and meets the
    contact ``sqrt(r^2 - h^2)`` ahead of it, the shot being ``h`` above the
    contact; the root is ``v_Sch (t - t0)`` along the contact. Before the
    wavelet peaks there is no front, and nothing is drawn; ``None`` until
    the two marks stand apart from the shot.
    """
    radius = _SCH_FLUID.c_p * since_peak
    root = v_exact * since_peak
    foot = float(np.sqrt(max(radius**2 - _SCH_SHOT_HEIGHT**2, 0.0)))
    if radius > _SCH_SHOT_HEIGHT:
        panel.arc.set_data(*_sch_water_arc(radius))
    else:
        panel.arc.set_data([], [])
    marked = _SCH_LABEL_FROM < root < _SCH_AHEAD
    panel.dot.set_data(([root] if marked else []), ([0.0] if marked else []))
    front, train = panel.labels
    # Both symbols ride behind their marks, so neither runs off the far
    # edge with the train still in the view: the front's 55 m up, where the
    # arc is 1.3 m at most behind its foot, and the root's below the
    # contact, clear of the dotted line.
    front.set_position((foot - 9.0, -55.0))
    front.set_visible(marked and foot < _SCH_AHEAD)
    train.set_position((root - 9.0, 24.0))
    train.set_visible(marked)
    return foot - root if marked else None


def animate_elastic_scholte(output_dir: str) -> None:
    """A Scholte train in motion, timed and left behind by the water front.

    An explosive 50 Hz shot 10 m above a water-seabed contact (the van
    Vossen benchmark media of the still figure this clip sits under) sends a
    front through the water at 1500 m/s, two faster ones through the seabed,
    and a train that stays on the contact at 1436 m/s, the root of the exact
    characteristic equation. One frame cannot show any of what makes it an
    interface wave. It is 4 % slower than the water front, so the two stand
    one Scholte wavelength apart only after 644 m: the dotted arc is the
    exact ``c_w (t - t0)`` front and the dot the exact root, and the readout
    is the gap between them on the contact. It keeps its amplitude while
    every body front thins as it spreads: two pressure probes on the contact,
    300 m apart, see the same pulse, and the delay between them is the speed
    the solver's test pins. And it lives within a fraction of a wavelength of
    the contact: a third probe 30 m up sees a small part of it.
    """
    T = _translate_str
    vy, traces, times, c_meas, ratio = _scholte_fields()
    v_exact = scholte_speed(_SCH_FLUID, _SCH_SOLID)
    n_active = int(times.size)
    t_ms = times * 1e3
    t_first = _sch_peak(times, traces[:, 0])
    t_second = _sch_peak(times, traces[:, 1])
    # The colour scale closes at half the train's peak: the train saturates,
    # and the body fronts, a tenth of it by mid-run, keep a readable tint.
    vmax = 0.5

    fig = _anim_figure()
    # The bottom strip holds the figure-level caption, which fig.text does
    # not claim from the constrained layout on its own.
    fig.get_layout_engine().set(rect=(0.0, 0.05, 1.0, 0.95))  # type: ignore[union-attr, call-arg]  # _anim_figure: constrained engine, never None
    fig.suptitle(
        T("Scholte wave: the train a water-seabed contact keeps (elastic 2D FDTD)")
    )
    grid = fig.add_gridspec(2, 1, height_ratios=(1.0, 1.05))
    panel = _sch_field_panel(fig, grid[0, 0], vy, vmax)

    tax = fig.add_subplot(grid[1, 0])
    tax.grid(visible=False)
    tax.set_xlim(0.0, float(t_ms[-1]))
    tax.set_ylim(-1.3, 2.1)
    tax.set_yticks([])
    tax.tick_params(labelsize=7)
    tax.set_xlabel(T("Time [ms]"), fontsize=8)
    tax.set_ylabel(T("pressure in the water"), fontsize=8)
    names = (
        T("on the contact, 100 m from the shot"),
        T("on the contact, 400 m"),
        T("30 m above the contact, 400 m"),
    )
    colors = (COLOR_PRIMARY, COLOR_SECONDARY, COLOR_TERTIARY)
    lines = [
        tax.plot([], [], color=color, lw=1.1, label=name)[0]
        for color, name in zip(colors, names, strict=True)
    ]
    # The legend is a row above the axes, where a title would be: inside
    # them every corner is either a pulse or the verdict.
    tax.legend(
        fontsize=7,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.0),
        ncol=3,
        frameon=False,
        handlelength=1.6,
        columnspacing=1.6,
    )
    # The time of flight, drawn once both peaks are in: a bar from one
    # envelope peak to the other, above the traces.
    (flight,) = tax.plot([], [], color=COLOR_FG, lw=0.9, marker="|", ms=7, zorder=4)
    flight_txt = tax.text(
        0.5 * (t_first + t_second) * 1e3,
        1.36,
        "",
        ha="center",
        va="bottom",
        fontsize=7.5,
        color=COLOR_FG,
    )
    v_txt = tax.text(
        float(t_ms[-1]) * 0.988,
        1.55,
        "",
        ha="right",
        va="center",
        color="white",
        fontsize=7.5,
        zorder=7,
        linespacing=1.35,
        bbox={
            "boxstyle": _ANIM_PILL_BOX,
            "facecolor": "black",
            "alpha": 0.55,
            "edgecolor": "none",
        },
    )
    distance = _SCH_PROBES[1] - _SCH_PROBES[0]
    flight_label = T(
        f"{distance:.0f} m between the contact probes in "
        f"{(t_second - t_first) * 1e3:.1f} ms"
    )
    verdict = (
        T(f"the train timed at {c_meas:.0f} m/s; the Scholte root is {v_exact:.0f} m/s")
        + "\n"
        + T(f"30 m above the contact: {ratio:.2f} of its amplitude")
    )
    marks_txt = fig.text(
        0.5,
        0.022,
        T(
            "dotted arc: the water front, $c_\\mathrm{w}(t - t_0)$ round the "
            "shot; dot: the Scholte root, $v_\\mathrm{Sch}(t - t_0)$ along the "
            f"contact, {v_exact:.0f} m/s (B&G Eq. 4.4.20)"
        ),
        ha="center",
        va="bottom",
        fontsize=7.5,
        color=COLOR_FG,
    )
    # The clock sits in the top left corner of the trace axes, above the
    # first probe's pulse and clear of the tick row: in the field panel it
    # would be under the water front as it leaves, and at the right end of
    # the axis label row it read as one with the last tick label.
    t_txt = tax.text(
        0.012,
        0.96,
        "",
        transform=tax.transAxes,
        ha="left",
        va="top",
        family="monospace",
        fontsize=9,
        color=COLOR_FG,
    )
    wavelength = "\n" + T(
        f"one Scholte wavelength at {_SCH_F0:.0f} Hz: {v_exact / _SCH_F0:.1f} m"
    )
    # The verdict waits for the second envelope peak and a little more, so
    # the pulse it is read from is whole on the trace when it appears.
    reveal = t_second + 0.015

    def update(k: int) -> tuple[Any, ...]:
        kf = min(k, n_active - 1)
        t = float(times[kf])
        panel.im.set_data(vy[kf])
        lead = _sch_place_marks(panel, max(t - _SCH_T0, 0.0), v_exact)
        panel.lead.set_text(
            ""
            if lead is None
            else T(f"water front ahead of the Scholte root: {lead:.1f} m") + wavelength
        )
        for i, line in enumerate(lines):
            line.set_data(t_ms[: kf + 1], traces[: kf + 1, i])
        timed = t >= reveal
        flight.set_data(
            ([t_first * 1e3, t_second * 1e3] if timed else []),
            ([1.3, 1.3] if timed else []),
        )
        flight_txt.set_text(flight_label if timed else "")
        v_txt.set_text(verdict if timed else "")
        t_txt.set_text(T(f"$t$ = {t * 1e3:5.1f} ms"))
        return (
            panel.im,
            panel.arc,
            panel.dot,
            *panel.labels,
            panel.lead,
            *lines,
            flight,
            flight_txt,
            v_txt,
            marks_txt,
            t_txt,
        )

    # No poster override: the last frame, which the hold repeats and the
    # default poster is cut from, has the train 60 m inside the far edge.
    _render_clip(
        fig,
        update,
        output_dir,
        "anim_elastic_scholte",
        frames=n_active + _SCH_HOLD,
        fps=_SCH_FPS,
        gif_fps=6,
    )
