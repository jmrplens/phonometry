#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Where a wave-field run is executed: the remote GPU, or this machine.

The clips of the documentation are FDTD simulations, and the expensive half
of each render is the stepping. ``fdtd_gpu_remote`` already knows how to
send a run to the CUDA box configured in ``.env`` and how to finish it here
when that box is not there; what it needs is the run *described* rather than
constructed, because a job archive can carry arrays and numbers but not the
live engine object a scene builds.

This module is that description. A :class:`Scene` holds exactly the
constructor arguments of the library engine plus the sustained sources as
data, and :func:`run` turns it into a job and submits it. The same scene
therefore runs on the GPU when one answers and on NumPy when none does, and
the two agree bit for bit (``tests/test_fdtd_gpu_parity.py``): the fallback
is the same engine on the other array module, not a second implementation.

The reductions are what make the round trip worth taking. A scene that
reads the field on every step -- a running mean square, an envelope along a
duct axis, the settled level over the last periods -- would otherwise have
to ship a frame per step, which costs more than the simulation. Ask for
them by name (``rms_beta``, ``envelopes``, ``mean_squares``) and they come
back computed on the device.

This file sits next to ``fdtd2d.py`` and outside the figures package on
purpose: like the engine itself, it decides *how* a field is computed and
not how it is drawn, so it stays out of the clip fingerprints
(:mod:`animation_fingerprint`).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import fdtd_gpu_remote

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from numpy.typing import NDArray

#: Frames come back at this dtype by default: half the bytes over the wire
#: and what every clip stack is stored as anyway.
FRAME_DTYPE = "float32"


def cw(
    frequency: float, amplitude: float = 1.0, ramp_cycles: float = 3.0
) -> dict[str, Any]:
    """The waveform dict of a cosine-ramped sine drive.

    The parameters and the defaults of the library's ``CWSource``, as data.
    """
    return {
        "type": "cw",
        "frequency": float(frequency),
        "amplitude": float(amplitude),
        "ramp_cycles": float(ramp_cycles),
    }


def gaussian(
    width: float, t0: float | None = None, amplitude: float = 1.0
) -> dict[str, Any]:
    """The waveform dict of a Gaussian pressure pulse.

    ``t0`` defaults to four widths, as the library's ``GaussianPulse`` does.
    """
    return {
        "type": "gaussian",
        "width": float(width),
        "t0": None if t0 is None else float(t0),
        "amplitude": float(amplitude),
    }


def point(ix: int, iy: int, waveform: Mapping[str, Any]) -> dict[str, Any]:
    """A sustained point drive on cell ``(iy, ix)``."""
    return {"kind": "point", "ix": int(ix), "iy": int(iy), "waveform": dict(waveform)}


def plane(
    direction: str,
    waveform: Mapping[str, Any],
    offset: int = 0,
    amplitude: float = 1.0,
) -> dict[str, Any]:
    """A sustained plane wave launched toward *direction*."""
    return {
        "kind": "plane",
        "direction": str(direction),
        "offset": int(offset),
        "amplitude": float(amplitude),
        "waveform": dict(waveform),
    }


@dataclass(frozen=True, eq=False)
class Scene:
    """One FDTD run, described rather than constructed.

    Every field is a constructor argument of the library engine under the
    same name, except :attr:`sources`, which lists the sustained drives as
    the dicts :func:`point` and :func:`plane` build. Equality is identity
    (the maps are arrays), and the dataclass is frozen so a scene can be
    described once and run more than once.
    """

    c: float | NDArray[np.float64]
    dx: float
    shape: tuple[int, int] | None = None
    rho: float | NDArray[np.float64] = 1.2
    cfl: float = 0.6
    sponge_width: int = 0
    sponge_sides: str | Iterable[str] | None = None
    sponge_reflection: float = 1e-4
    damping: float | NDArray[np.float64] = 0.0
    edge_impedance: dict[str, float | NDArray[np.float64]] | None = None
    obstacle_mask: NDArray[np.bool_] | None = None
    sources: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    @property
    def dt(self) -> float:
        """The leapfrog time step, the engine's own expression.

        Known before anything is allocated, so a caller can lay out a
        capture schedule (or a settle window) without building the run.
        """
        c_max = float(np.max(np.asarray(self.c, dtype=np.float64)))
        return self.cfl * float(self.dx) / (c_max * float(np.sqrt(2.0)))

    def with_sources(self, *sources: Mapping[str, Any]) -> Scene:
        """A copy of this scene driven by *sources* instead.

        The geometry of a scene is usually shared by the runs that differ
        only in what drives them (one frequency, then the next).
        """
        return Scene(
            c=self.c,
            dx=self.dx,
            shape=self.shape,
            rho=self.rho,
            cfl=self.cfl,
            sponge_width=self.sponge_width,
            sponge_sides=self.sponge_sides,
            sponge_reflection=self.sponge_reflection,
            damping=self.damping,
            edge_impedance=self.edge_impedance,
            obstacle_mask=self.obstacle_mask,
            sources=tuple(dict(s) for s in sources),
        )


def run(
    scene: Scene,
    *,
    steps: int,
    sample_steps: Sequence[int] | NDArray[np.int_] = (),
    sample_stride: int = 1,
    sample_dtype: str = FRAME_DTYPE,
    rms_beta: float = 0.0,
    envelopes: Sequence[Mapping[str, Any]] = (),
    mean_squares: Sequence[Mapping[str, Any]] = (),
    timeout: float = 1800.0,
) -> dict[str, Any]:
    """Step *scene* for *steps* and return what was asked for.

    Runs on the configured GPU when it answers and on this machine
    otherwise, with the same result either way. The keyword arguments are
    those of :func:`fdtd_gpu_remote.build_job`, and the returned dict is
    the runner's payload: ``frames`` on the ``sample_steps`` schedule,
    ``rms_frames``/``rms_final`` when ``rms_beta`` is positive, one
    ``envelope_<name>`` per envelope and one ``mean_square_<name>`` per
    window, plus ``backend`` and ``elapsed``.
    """
    job = fdtd_gpu_remote.build_job(
        scene.c,
        scene.dx,
        steps=int(steps),
        sample_steps=[int(s) for s in sample_steps],
        shape=scene.shape,
        rho=scene.rho,
        cfl=scene.cfl,
        sponge_width=scene.sponge_width,
        sponge_sides=scene.sponge_sides,
        sponge_reflection=scene.sponge_reflection,
        damping=scene.damping,
        edge_impedance=scene.edge_impedance,
        obstacle_mask=scene.obstacle_mask,
        sources=[dict(s) for s in scene.sources],
        rms_beta=float(rms_beta),
        envelopes=[dict(e) for e in envelopes],
        mean_squares=[dict(m) for m in mean_squares],
        sample_stride=int(sample_stride),
        sample_dtype=sample_dtype,
    )
    return fdtd_gpu_remote.submit(job, timeout=timeout)
