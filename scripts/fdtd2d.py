#  Copyright (c) 2026. Jose M. Requena-Plens
"""Minimal deterministic 2D acoustic FDTD engine for documentation animations.

A staggered-grid (Yee-style) pressure-velocity leapfrog scheme:

* pressure ``p`` at cell centres, shape ``(ny, nx)``;
* ``vx`` at interior x-faces, shape ``(ny, nx - 1)``;
* ``vy`` at interior y-faces, shape ``(ny - 1, nx)``.

Because only interior faces are stored, the domain boundary is perfectly
rigid (zero normal velocity) by construction; optional sponge layers turn
selected sides into absorbing boundaries. Heterogeneous sound-speed and
density maps are supported, sources are soft (additive) pressure injections
of either a Gaussian pulse or a ramped continuous wave, and ``run()`` can
subsample frames into a stacked array ready for ``FuncAnimation``/``imshow``.

The engine is deliberately deterministic so committed animation clips only
change when their code changes: float64 arithmetic throughout, no random
numbers, a fixed CFL number, and pure-numpy single-threaded execution (the
figure pipeline pins the BLAS/OpenMP pools to one thread before numpy is
imported).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Field2D = NDArray[np.float64]

_SIDES = ("left", "right", "top", "bottom")


def _positive_finite(name: str, value: float) -> float:
    """Validate that *value* is a strictly positive finite scalar."""
    out = float(value)
    if not np.isfinite(out) or out <= 0.0:
        raise ValueError(f"{name} must be positive and finite")
    return out


def _finite(name: str, value: float) -> float:
    """Validate that *value* is a finite scalar."""
    out = float(value)
    if not np.isfinite(out):
        raise ValueError(f"{name} must be finite")
    return out


def _positive_map(name: str, field: Field2D) -> None:
    """Validate that every cell of *field* is strictly positive and finite."""
    if not np.all(np.isfinite(field)) or bool(np.any(field <= 0.0)):
        raise ValueError(f"{name} must be strictly positive and finite "
                         "everywhere")


@dataclass(frozen=True)
class GaussianPulse:
    """A soft Gaussian pressure pulse injected at one cell.

    ``s(t) = amplitude * exp(-((t - t0) / width)**2)`` with ``t0`` defaulting
    to ``4 * width`` so the pulse starts from (numerically) zero.
    """

    ix: int
    iy: int
    width: float
    t0: float | None = None
    amplitude: float = 1.0

    def __post_init__(self) -> None:
        _positive_finite("width", self.width)
        _finite("amplitude", self.amplitude)
        if self.t0 is not None:
            _finite("t0", self.t0)

    def value(self, t: float) -> float:
        """Source waveform at time ``t`` (seconds)."""
        t0 = 4.0 * self.width if self.t0 is None else self.t0
        return self.amplitude * float(np.exp(-(((t - t0) / self.width) ** 2)))


@dataclass(frozen=True)
class CWSource:
    """A continuous sine drive with a smooth cosine-ramped onset.

    The first ``ramp_cycles`` periods fade the amplitude in with a raised
    cosine so the start does not splash a broadband transient over the field.
    """

    ix: int
    iy: int
    frequency: float
    amplitude: float = 1.0
    ramp_cycles: float = 3.0

    def __post_init__(self) -> None:
        _positive_finite("frequency", self.frequency)
        _finite("amplitude", self.amplitude)
        if not np.isfinite(self.ramp_cycles) or self.ramp_cycles < 0.0:
            raise ValueError("ramp_cycles must be non-negative and finite")

    def value(self, t: float) -> float:
        """Source waveform at time ``t`` (seconds)."""
        ramp_time = self.ramp_cycles / self.frequency
        if t < ramp_time and ramp_time > 0.0:
            envelope = 0.5 * (1.0 - float(np.cos(np.pi * t / ramp_time)))
        else:
            envelope = 1.0
        return (self.amplitude * envelope
                * float(np.sin(2.0 * np.pi * self.frequency * t)))


Source = GaussianPulse | CWSource


def _sponge_profile(n: int, width: int, sides: tuple[bool, bool],
                    sigma_max: float) -> Field2D:
    """1D absorption rate sigma(i) [1/s]: quadratic ramp into each sponge side.

    ``sides`` selects (low-index side, high-index side).
    """
    sigma = np.zeros(n, dtype=np.float64)
    if width <= 0:
        return sigma
    depth = (width - np.arange(width, dtype=np.float64)) / width
    ramp = sigma_max * depth**2
    if sides[0]:
        sigma[:width] = np.maximum(sigma[:width], ramp)
    if sides[1]:
        sigma[n - width:] = np.maximum(sigma[n - width:], ramp[::-1])
    return sigma


class FDTD2D:
    """2D acoustic FDTD simulation on a staggered grid.

    Parameters
    ----------
    c:
        Sound-speed map [m/s], shape ``(ny, nx)`` (row = y, column = x, the
        ``imshow`` convention). A scalar with an explicit ``shape`` is also
        accepted.
    dx:
        Grid spacing [m] (square cells).
    rho:
        Density map [kg/m3]; scalar or ``(ny, nx)`` array (default 1.2).
    cfl:
        Courant number; the scheme's 2D stability bound is ``1/sqrt(2)``,
        and only the deterministic 0.5-0.7 window is accepted.
    sponge_width:
        Thickness of the absorbing layer in cells (0 = all-rigid box).
    sponge_sides:
        Which sides absorb: a single side name or an iterable drawn from
        ``{"left", "right", "top", "bottom"}`` (default: all four when
        ``sponge_width > 0``).
        ``left``/``right`` are the low/high column edges and ``top``/
        ``bottom`` the low/high row edges (the default ``imshow`` origin).
    sponge_reflection:
        Target round-trip amplitude reflection of the sponge layer; sets the
        peak absorption rate.
    damping:
        Uniform bulk amplitude decay rate [1/s] applied to the whole field
        (a simple stand-in for air/wall absorption; ``6.91 / T60`` gives a
        ``T60`` seconds reverberant decay).
    shape:
        Grid shape ``(ny, nx)``, required only when ``c`` is a scalar.
    """

    def __init__(
        self,
        c: float | Field2D,
        dx: float,
        *,
        rho: float | Field2D = 1.2,
        cfl: float = 0.6,
        sponge_width: int = 0,
        sponge_sides: str | Iterable[str] | None = None,
        sponge_reflection: float = 1e-4,
        damping: float = 0.0,
        shape: tuple[int, int] | None = None,
    ) -> None:
        if np.isscalar(c):
            if shape is None:
                raise ValueError("shape is required when c is a scalar")
            c_map = np.full(shape, float(np.real(c)), dtype=np.float64)
        else:
            c_map = np.asarray(c, dtype=np.float64)
        if c_map.ndim != 2:
            raise ValueError("c must be a 2D (ny, nx) map")
        _positive_map("c", c_map)
        if not 0.5 <= cfl <= 0.7:
            raise ValueError("cfl must stay in the deterministic 0.5-0.7 window")
        ny, nx = c_map.shape
        rho_map = (np.full((ny, nx), float(np.real(rho)), dtype=np.float64)
                   if np.isscalar(rho) else np.asarray(rho, dtype=np.float64))
        if rho_map.shape != (ny, nx):
            raise ValueError("rho map must match the shape of c")
        _positive_map("rho", rho_map)
        if sponge_width < 0:
            raise ValueError("sponge_width must be non-negative")
        if sponge_width >= min(nx, ny):
            raise ValueError("sponge_width must be narrower than the "
                             "smallest grid side")
        if not 0.0 < sponge_reflection < 1.0:
            raise ValueError("sponge_reflection must lie strictly between "
                             "0 and 1")
        if not np.isfinite(damping) or damping < 0.0:
            raise ValueError("damping must be non-negative and finite")

        self.dx = _positive_finite("dx", dx)
        self.c = c_map
        self.rho = rho_map
        c_max = float(c_map.max())
        self.dt = cfl * self.dx / (c_max * float(np.sqrt(2.0)))
        self.kappa = rho_map * c_map**2          # bulk modulus at centres
        # Density averaged onto the faces where each velocity lives.
        self._rho_x = 0.5 * (rho_map[:, 1:] + rho_map[:, :-1])
        self._rho_y = 0.5 * (rho_map[1:, :] + rho_map[:-1, :])

        self.p: Field2D = np.zeros((ny, nx), dtype=np.float64)
        self.vx: Field2D = np.zeros((ny, nx - 1), dtype=np.float64)
        self.vy: Field2D = np.zeros((ny - 1, nx), dtype=np.float64)
        self._sources: list[Source] = []
        self.n = 0                                # completed steps

        if sponge_sides is None:
            sides: tuple[str, ...] = _SIDES
        elif isinstance(sponge_sides, str):
            # A bare string would iterate per character; treat it as one side.
            sides = (sponge_sides,)
        else:
            sides = tuple(sponge_sides)
        unknown = set(sides) - set(_SIDES)
        if unknown:
            raise ValueError(f"unknown sponge sides: {sorted(unknown)}")
        sigma_max = 0.0
        if sponge_width > 0:
            # Quadratic-profile PML-style rate for a target reflection R:
            # exp(-2 * sigma_max * (w dx) / (3 c)) = R  (two-way transit).
            sigma_max = (-3.0 * c_max * float(np.log(sponge_reflection))
                         / (2.0 * sponge_width * self.dx))
        sig_x = _sponge_profile(nx, sponge_width,
                                ("left" in sides, "right" in sides), sigma_max)
        sig_y = _sponge_profile(ny, sponge_width,
                                ("top" in sides, "bottom" in sides), sigma_max)
        sigma = sig_x[np.newaxis, :] + sig_y[:, np.newaxis] + damping
        self._decay_p: Field2D = np.exp(-sigma * self.dt)
        self._decay_vx: Field2D = np.exp(
            -(0.5 * (sigma[:, 1:] + sigma[:, :-1])) * self.dt)
        self._decay_vy: Field2D = np.exp(
            -(0.5 * (sigma[1:, :] + sigma[:-1, :])) * self.dt)

    @property
    def time(self) -> float:
        """Elapsed simulated time [s]."""
        return self.n * self.dt

    def add_source(self, source: Source) -> None:
        """Register a soft pressure source (additive injection at one cell)."""
        ny, nx = self.p.shape
        if not (0 <= source.ix < nx and 0 <= source.iy < ny):
            raise ValueError("source position lies outside the grid")
        self._sources.append(source)

    def step(self) -> None:
        """Advance the leapfrog scheme by one time step."""
        dt_dx = self.dt / self.dx
        # Velocity half-step from the pressure gradient (rigid walls are the
        # implicit zero normal velocity at the domain edge).
        self.vx -= dt_dx / self._rho_x * (self.p[:, 1:] - self.p[:, :-1])
        self.vy -= dt_dx / self._rho_y * (self.p[1:, :] - self.p[:-1, :])
        self.vx *= self._decay_vx
        self.vy *= self._decay_vy
        # Pressure step from the velocity divergence.
        div = np.zeros_like(self.p)
        div[:, :-1] += self.vx
        div[:, 1:] -= self.vx
        div[:-1, :] += self.vy
        div[1:, :] -= self.vy
        self.p -= self.kappa * dt_dx * div
        t_next = (self.n + 1) * self.dt
        for src in self._sources:
            self.p[src.iy, src.ix] += src.value(t_next)
        self.p *= self._decay_p
        self.n += 1

    def energy(self) -> float:
        """Total acoustic field energy [J per metre of depth]."""
        e_p = float(np.sum(self.p**2 / (2.0 * self.kappa)))
        e_v = 0.5 * (float(np.sum(self._rho_x * self.vx**2))
                     + float(np.sum(self._rho_y * self.vy**2)))
        return (e_p + e_v) * self.dx**2

    def run(
        self,
        steps: int,
        record_every: int | None = None,
        decimate: int = 1,
    ) -> NDArray[np.float64]:
        """Advance ``steps`` steps, optionally recording pressure frames.

        With ``record_every = k`` a snapshot of ``p`` is stored after every
        ``k``-th step (and one of the initial state), spatially subsampled by
        ``decimate``; the stacked ``(n_frames, ny', nx')`` array plugs
        straight into a ``FuncAnimation`` ``imshow`` update. Without
        ``record_every`` an empty array is returned and only the final state
        is kept (read it from ``self.p``).
        """
        if steps < 0:
            raise ValueError("steps must be non-negative")
        if record_every is not None and record_every < 1:
            raise ValueError("record_every must be >= 1")
        if decimate < 1:
            raise ValueError("decimate must be >= 1")
        frames: list[Field2D] = []
        if record_every is not None:
            frames.append(self.p[::decimate, ::decimate].copy())
        for i in range(steps):
            self.step()
            if record_every is not None and (i + 1) % record_every == 0:
                frames.append(self.p[::decimate, ::decimate].copy())
        if not frames:
            return np.zeros((0, 0, 0), dtype=np.float64)
        return np.stack(frames)
