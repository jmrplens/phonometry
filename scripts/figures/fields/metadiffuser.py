#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The slit-resonator metadiffuser: a panel a twentieth of a QRD deep.

Both the far-field polar levels the prediction figure is checked against and
the clip that shows the panel scattering are runs of the same meshed
Table-1 geometry, so they share its pitch, period count and design
frequency.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Any

import numpy as np

from ..materials import _METADIFFUSER_T1_ROWS
from ..media import _anim_figure, _render_clip, _translate_str
from ..theme import (
    CMAP_FIELD,
    COLOR_FG,
    FIELD_INK,
    FIELD_STROKE,
)
from ._core import _host, _solid_in_field

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.figure import Figure
    from matplotlib.gridspec import GridSpec
    from matplotlib.image import AxesImage
    from matplotlib.patheffects import AbstractPathEffect
    from matplotlib.text import Text
    from numpy.typing import NDArray

    from phonometry.simulation import Compute


@lru_cache(maxsize=1)
def _meshed_metadiffuser_ntff_levels() -> tuple[Any, Any]:
    """Far-field polar levels of the meshed Table-1 panel at 2 kHz.

    A dedicated continuous-wave FDTD run at dx = 0.5 mm (every slit, neck
    and cavity of the real panel resolved by at least four cells, unit-cell
    reflection phases within 2 degrees of a 0.25 mm run): a plane wave from
    just inside the top sponge drives the panel to steady state, a closed
    contour probe accumulates the 2 kHz pressure and normal-velocity
    phasors on the fly, and the 2D Kirchhoff-Helmholtz integral turns them
    into the far-field pattern. The incident wave extinguishes in the
    exterior integral, so no reference run is needed. Returns the polar
    angles [deg from the panel normal] and the levels re the peak [dB].
    """
    from phonometry.simulation import (
        FDTD2D,
        Compute,
        CWSource,
        PlaneWaveSource,
        far_field_from_contour,
    )

    dx, sponge, f0 = 0.0005, 60, _META_F0
    gap, marg, front = (round(m / dx) for m in (0.030, 0.010, 0.020))
    face_cells = round(5 * _META_PITCH / dx)
    lat = marg + gap + sponge
    nx = face_cells + 2 * lat
    r_face = sponge + gap + front
    slab = round(0.023 / dx)
    ny = r_face + slab + marg + gap + sponge
    mask = np.zeros((ny, nx), dtype=bool)
    mask[r_face : r_face + slab, lat : lat + face_cells] = True
    for n, (h, l_n, l_c, w_n, w_c) in enumerate(_METADIFFUSER_T1_ROWS):
        x_slit = (n + 0.12) * _META_PITCH
        c0s = lat + round(x_slit / dx)
        c1s = lat + round((x_slit + h * 1e-3) / dx)
        mask[r_face : r_face + round(0.02 / dx), c0s:c1s] = False
        for m in range(2):
            y_m = (m + 0.5) * 0.01
            x_neck = x_slit + h * 1e-3
            r0 = r_face + round((y_m - 0.5e-3 * w_n) / dx)
            r1 = r_face + round((y_m + 0.5e-3 * w_n) / dx)
            mask[r0:r1, c1s : lat + round((x_neck + l_n * 1e-3) / dx)] = False
            r0 = r_face + round((y_m - 0.5e-3 * w_c) / dx)
            r1 = r_face + round((y_m + 0.5e-3 * w_c) / dx)
            mask[
                r0:r1,
                lat + round((x_neck + l_n * 1e-3) / dx) : lat
                + round((x_neck + (l_n + l_c) * 1e-3) / dx),
            ] = False
    # cfl 0.9 trims the step count; at 340 cells per wavelength the
    # numerical dispersion is negligible at any stable Courant number.
    sim = FDTD2D(
        343.0,
        dx,
        shape=(ny, nx),
        absorbing_layer_cells=sponge,
        cfl=0.9,
        obstacle_mask=mask,
        compute=Compute(),
    )
    sim.add_source(
        PlaneWaveSource(
            direction="down",
            waveform=CWSource(ix=0, iy=0, frequency=f0).value,
            offset=sponge,
        )
    )
    probe = sim.add_contour_probe(
        lat - marg,
        lat + face_cells + marg - 1,
        r_face - front,
        r_face + slab + marg - 1,
        frequencies=[f0],
    )
    sim.run(round(8e-3 / sim.dt))  # transient out (ramp + ring-up)
    probe.reset()
    sim.run(round(10.0 / f0 / sim.dt))  # ten whole periods of DFT
    angles = np.arange(-90.0, 90.1, 5.0)
    pattern = far_field_from_contour(
        probe.phasors(f0),
        angles - 90.0,
        origin=((lat + face_cells / 2.0) * dx, r_face * dx),
    )
    magnitude = np.abs(pattern)
    levels = 20.0 * np.log10(np.maximum(magnitude / magnitude.max(), 1e-10))
    return angles, levels


_META_DX = 0.00025
_META_NY, _META_NX = 4800, 6400
_META_XL, _META_FACE = 0.45, 0.36
_META_PITCH, _META_PERIODS = 0.07, 2
_META_F0 = 2000.0


def _metadiffuser_panel_mask(rho: NDArray[np.float64]) -> None:
    """Carve the Table-1 metadiffuser (two periods) into a dense slab.

    The slab spans the panel depth L = 2 cm plus a 3 mm back wall under
    the face line; each well is a vertical slit from the face with its two
    resonators shelved sideways into the septum, the same layout the
    to-scale drawing uses (slit at 0.12 d into the cell, lattice a = L/2).
    """
    dx, y1 = _META_DX, _META_FACE
    rows = _METADIFFUSER_T1_ROWS
    depth, back = 0.02, 0.003
    rho[
        round((y1 - depth - back) / dx) : round(y1 / dx),
        round(_META_XL / dx) : round((_META_XL + _META_PERIODS * 5 * _META_PITCH) / dx),
    ] = 1.2e6
    lattice = depth / 2
    for period in range(_META_PERIODS):
        for n, (h, ln, lc, wn, wc) in enumerate(rows):
            x0 = _META_XL + (period * 5 + n) * _META_PITCH
            x_slit = x0 + 0.12 * _META_PITCH
            c0s, c1s = round(x_slit / dx), round((x_slit + h * 1e-3) / dx)
            rho[round((y1 - depth) / dx) : round(y1 / dx), c0s:c1s] = 1.2
            for m in range(2):
                y_m = y1 - depth + (2 - m - 0.5) * lattice
                x_neck = x_slit + h * 1e-3
                r0 = round((y_m - 0.5 * wn * 1e-3) / dx)
                r1 = round((y_m + 0.5 * wn * 1e-3) / dx)
                rho[r0:r1, c1s : round((x_neck + ln * 1e-3) / dx)] = 1.2
                r0 = round((y_m - 0.5 * wc * 1e-3) / dx)
                r1 = round((y_m + 0.5 * wc * 1e-3) / dx)
                rho[
                    r0:r1,
                    round((x_neck + ln * 1e-3) / dx) : round(
                        (x_neck + (ln + lc) * 1e-3) / dx
                    ),
                ] = 1.2


def _meta_qrd_wells() -> list[tuple[float, float, float]]:
    """QRD well openings (x0, x1, depth) matched to the metadiffuser.

    The same N = 5 residue order as the Table-1 metadiffuser
    (s = 1, 4, 4, 1, 0), designed at 500 Hz: depths s lambda0 / (2 N) up
    to 27.4 cm, 65 mm wells split by 5 mm fins on the 7 cm pitch.
    """
    unit = (343.0 / 500.0) / 10.0
    wells: list[tuple[float, float, float]] = []
    for period in range(_META_PERIODS):
        for n, s_n in enumerate((1, 4, 4, 1, 0)):
            x0 = _META_XL + (period * 5 + n) * _META_PITCH
            wells.append((x0 + 0.005, x0 + _META_PITCH, s_n * unit))
    return wells


def _meta_rho(kind: str) -> NDArray[np.float64]:
    """Density map of one run: ``flat``, ``qrd``, ``meta`` or ``ref``."""
    dx, ny, nx = _META_DX, _META_NY, _META_NX
    y1 = _META_FACE
    x_r = _META_XL + _META_PERIODS * 5 * _META_PITCH
    rho = np.full((ny, nx), 1.2)
    if kind == "qrd":
        rho[
            round(0.05 / dx) : round(y1 / dx), round(_META_XL / dx) : round(x_r / dx)
        ] = 1.2e6
        for wx0, wx1, d in _meta_qrd_wells():
            if d > 0.0:
                rho[
                    round((y1 - d) / dx) : round(y1 / dx),
                    round(wx0 / dx) : round(wx1 / dx),
                ] = 1.2
    elif kind == "meta":
        _metadiffuser_panel_mask(rho)
    elif kind == "flat":
        # A flat rigid slab with the metadiffuser's exact silhouette, so
        # the fans can only come from the slits, not from the outline.
        rho[
            round((y1 - 0.023) / dx) : round(y1 / dx),
            round(_META_XL / dx) : round(x_r / dx),
        ] = 1.2e6
    return rho


def _meta_taper() -> NDArray[np.float64]:
    """Lateral cosine taper of the incident packet (free-field edges).

    The wavefront is flat over the panels and dies smoothly well before
    the lateral sponges, so the exterior boundaries only ever absorb
    outgoing scattered waves and the incident front stays plane: no edge
    arcs in the total field, and the reference run subtracts exactly.
    """
    x = (np.arange(_META_NX) + 0.5) * _META_DX
    x0, x1, x2, x3 = 0.10, 0.30, 1.30, 1.50
    w = np.zeros(_META_NX)
    rise = (x >= x0) & (x < x1)
    w[rise] = 0.5 - 0.5 * np.cos(np.pi * (x[rise] - x0) / (x1 - x0))
    w[(x >= x1) & (x <= x2)] = 1.0
    fall = (x > x2) & (x <= x3)
    w[fall] = 0.5 + 0.5 * np.cos(np.pi * (x[fall] - x2) / (x3 - x2))
    return w


_META_FRAMES = 600  # 6.13 ms / 10.2 us per frame (49 frames per period)


def _meta_pair(
    kind: str, n_frames: int, compute: Compute
) -> tuple[NDArray[np.float32], NDArray[np.float32], NDArray[np.float64]]:
    """One panel stepped in lockstep with its own free-field reference.

    The trail is ``|p_kind - p_ref|`` at the same step, above the panel face,
    kept as a running maximum that halves every 1.5 ms. It is computed on
    whichever device the pair steps on, every step, and only the captured
    frames come back to the host.
    """
    from phonometry.simulation import FDTD2D

    c0, dx = 343.0, _META_DX
    lam0 = c0 / _META_F0
    # Duration rule: full flight source -> deepest well bottom -> top of
    # the visible frame, (0.714 + 1.034) m / c * 1.2 = 6.12 ms, sampled at
    # four times the 12 frames-per-period visual floor (49/period at 2 kHz).
    every = 33
    sims = [
        FDTD2D(
            c0,
            dx,
            rho=rho,
            shape=(_META_NY, _META_NX),
            absorbing_layer_cells=200,
            compute=compute,
        )
        for rho in (_meta_rho(kind), _meta_rho("ref"))
    ]
    backend = sims[0]._backend
    xp = backend.xp
    # The two engines step on one device, so one copy of the taper serves both.
    lateral = backend.asarray(_meta_taper()[np.newaxis, :])
    for sim in sims:
        sim.add_plane_wave("up", center_m=0.80, half_width_m=0.05, wavelength_m=lam0)
        sim.p *= lateral
        sim.vy *= lateral
    decay = float(2.0 ** (-sims[0].dt / 0.0015))
    face_row = round(_META_FACE / dx)
    trail = backend.zeros(tuple(sims[0].p.shape))
    tot_frames: list[NDArray[np.float32]] = []
    trail_frames: list[NDArray[np.float32]] = []
    ts: list[float] = []
    for _ in range(every * n_frames):
        for sim in sims:
            sim.step()
        scat = sims[0].p - sims[1].p
        scat[:face_row, :] = 0.0
        xp.maximum(trail * decay, xp.abs(scat), out=trail)
        if sims[0].n % every == 0 and len(ts) < n_frames:
            tot_frames.append(_host(sims[0], sims[0].p[::20, ::20]))
            trail_frames.append(_host(sims[0], trail[::20, ::20]))
            ts.append(sims[0].time)
    return np.stack(tot_frames), np.stack(trail_frames), np.asarray(ts)


#: The RAM one float64 lockstep pair holds while it steps: 24 grids of
#: _META_NY x _META_NX doubles (ten per engine, the trail and three per-step
#: temporaries), the count the GPU node's memory measurement found, 5.9 GB.
_META_PAIR_BYTES = 24 * _META_NY * _META_NX * 8

#: What a pair needs over its grids, as a factor: 1.45 times the grids is
#: 8.55 GB (8156 MiB) a pair. Measured on the node on 2026-10-22, the full
#: float64 run of 600 frames peaked at 7248 to 7250 MiB resident in each
#: pair's process: the grids, the frames it captures, the interpreter and its
#: libraries. The parent holds each pair's returned frames, two stacks of 600
#: float32 frames of 240 x 320, 2 x 600 x 240 x 320 x 4 B = 352 MiB, so a
#: pair side by side takes 7250 + 352 = 7602 MiB, 554 MiB under what it is
#: given (1.35 times the grids). One at a time in one process, the third pair
#: steps beside the first two pairs' frames, 7250 + 2 x 352 = 7954 MiB,
#: 202 MiB under. Side by side, the parent's own interpreter and libraries
#: are charged to no pair: they ride on the pairs' slack, which holds them
#: while they stay under 2 x 554 = 1108 MiB with two pairs, or under
#: 3 x 554 = 1662 MiB with three, at the least RAM that steps that many. The
#: parent's own peak, 3828 MiB once the pool had closed (the three pairs'
#: frames and their stacks), comes after the pairs' processes have given back
#: their 3 x 7250 MiB.
_META_PAIR_MARGIN = 1.45


def _meta_workers(available: int | None) -> int:
    """How many pairs step side by side in *available* bytes of RAM: one to three.

    Each pair is given 8.55 GB (``_META_PAIR_BYTES * _META_PAIR_MARGIN``):
    25.7 GB or more steps the three side by side, 17.1 GB or more steps two
    and then the third, and less steps them one at a time; the fields are the
    same in every case, only the wall time changes. Where the RAM cannot be
    read (*available* is None, off Linux) the three step side by side, which
    asks the machine for those 25.7 GB.
    """
    if available is None:
        return 3
    return max(1, min(3, int(available // (_META_PAIR_BYTES * _META_PAIR_MARGIN))))


@lru_cache(maxsize=1)
def _metadiffuser_fields(
    n_frames: int = _META_FRAMES,
) -> tuple[Any, Any, Any]:
    """Plane-wave packet onto a deep QRD vs the 2 cm metadiffuser, cached.

    A 1.6 m x 1.2 m free-field box at dx = 0.25 mm, fine enough to mesh the
    real millimetre slits, necks and cavities of the Table-1 metadiffuser
    (density contrast 1e6:1 builds the panels). Each panel (flat control
    with the metadiffuser's silhouette, deep QRD, metadiffuser) advances in
    lockstep with a free-field reference, so ``total - incident`` is exact at
    every step: on NumPy the pairs run side by side in worker processes as
    far as the RAM holds them (5.9 GB of grids, 7.6 GB a process measured),
    else one after another, and on a GPU one after another; the fields are
    the same either way. A downgoing carrier packet at the 2 kHz evaluation
    frequency plays the goniometer source. Returns the total frame stacks,
    the fading scattered-envelope trails [dB] and the frame times. The
    quantitative far-field comparison lives in the companion polar figure;
    this clip shows the near fields of the meshed panels.
    """
    import clip_placement

    compute = clip_placement.compute_for("anim_fdtd_metadiffuser")
    kinds = ("flat", "qrd", "meta")
    workers = (
        _meta_workers(clip_placement.host_bytes()) if compute.device == "cpu" else 1
    )
    if workers > 1:
        import concurrent.futures as cf
        import multiprocessing as mp
        from concurrent.futures.process import BrokenProcessPool

        # Pairs side by side, one per process, as many as the RAM holds: with
        # three the wall time of the cached field is that of one pair, two
        # simulations instead of six, and with two that of two pairs, four. A
        # process the kernel kills for its memory breaks the pool, and the
        # wait for its pair ends in BrokenProcessPool instead of lasting for
        # ever: the pool notices the death at the latest when another pair
        # returns, since it may start watching the last process it started
        # only then. It is raised again in this field's own words, which name
        # the pairs and the remedy: in the standard library's it reads as the
        # render's own pool breaking. The results come back in the order of
        # the kinds.
        with cf.ProcessPoolExecutor(
            max_workers=workers, mp_context=mp.get_context("spawn")
        ) as pool:
            try:
                parts = list(
                    pool.map(
                        _meta_pair,
                        kinds,
                        [n_frames] * len(kinds),
                        [compute] * len(kinds),
                    )
                )
            except BrokenProcessPool as error:
                msg = (
                    f"the metadiffuser's pairs stepped {workers} at once and "
                    "the process of one of them died, most likely killed for "
                    "its memory (each pair is given "
                    f"{_META_PAIR_BYTES * _META_PAIR_MARGIN / 1e9:.2f} GB); set "
                    f"{clip_placement.HOST_BYTES_ENV} lower so that fewer pairs "
                    "step at once"
                )
                raise BrokenProcessPool(msg) from error
    else:
        # One pair at a time: on a GPU a pair is what the free memory holds,
        # and on NumPy where the RAM holds only one.
        parts = []
        for kind in kinds:
            parts.append(_meta_pair(kind, n_frames, compute))
            clip_placement.release_device()
    tot = np.stack([part[0] for part in parts])
    trail = np.stack([part[1] for part in parts])
    times = parts[0][2]
    ref = float(trail[:, trail.shape[1] // 3 :].max()) or 1.0
    with np.errstate(divide="ignore"):
        trail_db = 20.0 * np.log10(trail / ref)
    trail_db = np.clip(trail_db, -30.0, 0.0).astype(np.float32)
    return tot, trail_db, times


#: The right edge of the two periods of either panel [m].
_META_XR = _META_XL + _META_PERIODS * 5 * _META_PITCH


def _meta_qrd_outline() -> list[tuple[float, float]]:
    """The deep QRD drawn over the field: its slab with the wells cut down from the face."""
    y1, x_l, x_r = _META_FACE, _META_XL, _META_XR
    qrd_poly: list[tuple[float, float]] = [(x_l, 0.05), (x_l, y1)]
    for wx0, wx1, d in _meta_qrd_wells():
        qrd_poly += [(wx0, y1), (wx0, y1 - d), (wx1, y1 - d), (wx1, y1)]
    qrd_poly += [(x_r, y1), (x_r, 0.05)]
    return qrd_poly


def _meta_column(
    fig: Figure,
    gs: GridSpec,
    col: int,
    title: str,
    *,
    first: tuple[NDArray[np.float32], NDArray[np.float32]],
    vmax: float,
    outline: Sequence[AbstractPathEffect],
) -> tuple[AxesImage, AxesImage, Text]:
    """One column of the clip: the total field over the scattered trail of one panel.

    *first* is the column's first total frame and first trail frame. Returns
    the two images and the verdict line, empty until the frames write it.
    """
    from matplotlib.patches import Polygon, Rectangle

    T = _translate_str
    y1, x_l, x_r = _META_FACE, _META_XL, _META_XR
    xc = 0.5 * (x_l + x_r)
    ax_t = fig.add_subplot(gs[0, col])
    ax_s = fig.add_subplot(gs[1, col])
    im_t = ax_t.imshow(
        first[0],
        origin="lower",
        extent=(0.0, 1.6, 0.0, 1.2),
        cmap=CMAP_FIELD,
        vmin=-vmax,
        vmax=vmax,
        interpolation="bilinear",
    )
    im_s = ax_s.imshow(
        first[1],
        origin="lower",
        extent=(0.0, 1.6, 0.0, 1.2),
        cmap="magma",
        vmin=-30.0,
        vmax=0.0,
        interpolation="bilinear",
    )
    ax_t.set_title(title, fontsize=10)
    for ax in (ax_t, ax_s):
        ax.grid(visible=False)
        if col == 1:
            ax.add_patch(
                Polygon(
                    _meta_qrd_outline(),
                    closed=True,
                    facecolor=_solid_in_field(ax),
                    edgecolor=COLOR_FG,
                    lw=0.8,
                )
            )
        else:
            ax.add_patch(
                Rectangle(
                    (x_l, y1 - 0.023),
                    x_r - x_l,
                    0.023,
                    facecolor=_solid_in_field(ax),
                    edgecolor=COLOR_FG,
                    lw=0.8,
                )
            )
        ax.set_xlim(0.06, 1.54)
        ax.set_ylim(0.0, 1.12)
        ax.tick_params(labelsize=7)
    ax_t.tick_params(labelbottom=False)
    ax_s.set_xlabel("$x$ [m]", fontsize=8)
    if col == 1:
        ax_t.text(
            xc,
            0.97,
            T("incident plane wavefront"),
            ha="center",
            va="bottom",
            color=FIELD_INK,
            fontsize=7.5,
            path_effects=outline,
        )
        ax_t.annotate(
            "",
            xy=(xc, 0.83),
            xytext=(xc, 0.955),
            arrowprops={"arrowstyle": "-|>", "color": FIELD_INK, "lw": 1.2},
        )
    d_txt = ax_s.text(
        xc,
        1.03,
        "",
        ha="center",
        va="top",
        color="white",
        fontsize=7.5,
        fontweight="bold",
    )
    if col == 0:
        ax_t.set_ylabel(T("sound field $p$"), fontsize=9)
        ax_s.set_ylabel(T("scattered field (total − incident)"), fontsize=8)
    else:
        ax_t.tick_params(labelleft=False)
        ax_s.tick_params(labelleft=False)
    if col == 1:
        ax_t.annotate(
            "",
            xy=(x_r + 0.045, y1 - 0.274),
            xytext=(x_r + 0.045, y1),
            arrowprops={"arrowstyle": "-", "color": COLOR_FG, "lw": 1.6},
        )
        ax_t.text(
            x_r + 0.07,
            y1 - 0.14,
            "27 cm",
            ha="left",
            va="center",
            fontsize=7,
            color=COLOR_FG,
        )
    if col == 2:
        ax_t.text(
            xc,
            0.06,
            T("real slits and resonators meshed at 0.25 mm"),
            ha="center",
            va="bottom",
            color=FIELD_INK,
            fontsize=6.5,
            path_effects=outline,
        )
        # No dimension bar on this one: the panel is 2 cm deep against
        # the QRD's 27, and a bar drawn to that scale is four pixels of
        # a stroke 1.6 wide -- a full stop in front of the text, not a
        # measurement. The number sits against the end of the slab it
        # measures instead, which at this thickness is the slab's own
        # thickness anyway.
        ax_t.text(
            x_r + 0.02,
            y1 - 0.012,
            "2 cm",
            ha="left",
            va="center",
            fontsize=7,
            color=COLOR_FG,
        )
    return im_t, im_s, d_txt


def animate_fdtd_metadiffuser(output_dir: str) -> None:
    """The 27 cm deep Schroeder QRD vs the 2 cm metadiffuser that mimics
    it, next to a flat control slab (2D FDTD at 0.25 mm, real slits, necks
    and cavities meshed): the same 2 kHz wavefront leaves the same kind of
    scattered fan, from a panel 13.7 times thinner.
    """
    from matplotlib import patheffects

    T = _translate_str
    outline = [patheffects.withStroke(linewidth=2.0, foreground=FIELD_STROKE)]
    tot_all, trail_db, times = _metadiffuser_fields()
    vmax = float(np.quantile(np.abs(tot_all[:, 0]), 0.999))

    fig = _anim_figure()
    fig.suptitle(
        T("Schroeder diffuser vs metadiffuser (2D FDTD)"),
    )
    gs = fig.add_gridspec(2, 3)
    titles = [
        T("Flat rigid panel"),
        T("QRD, wells down to 27 cm"),
        T("Metadiffuser, 2 cm panel"),
    ]

    ims: list[Any] = []
    d_txts: list[Any] = []
    for col in range(3):
        im_t, im_s, d_txt = _meta_column(
            fig,
            gs,
            col,
            titles[col],
            first=(tot_all[col][0], trail_db[col][0]),
            vmax=vmax,
            outline=outline,
        )
        ims += [im_t, im_s]
        d_txts.append(d_txt)
    # Top-left margin, beside the centred suptitle: three columns of field
    # panels carry their x ticks and "$x$ [m]" all the way into the
    # bottom-right corner, and a readout parked there merged with the third
    # column's tick row -- the stem of the "t" reading as part of 1.00, the
    # "ms" as part of 1.50.
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
    reveal = int(0.8 * tot_all.shape[1])

    verdicts = [
        T("a collimated specular beam"),
        T("a wide scattered fan"),
        T("the same fan, from 2 cm"),
    ]

    def update(k: int) -> tuple[Any, ...]:
        for col in range(3):
            ims[2 * col].set_data(tot_all[col][k])
            ims[2 * col + 1].set_data(trail_db[col][k])
            d_txts[col].set_text(verdicts[col] if k >= reveal else "")
        t_txt.set_text(T(f"$t$ = {times[k] * 1000.0:4.2f} ms"))
        return (*ims, *d_txts, t_txt)

    _render_clip(
        fig,
        update,
        output_dir,
        "anim_fdtd_metadiffuser",
        frames=int(tot_all.shape[1]),
        gif_fps=8,
    )
