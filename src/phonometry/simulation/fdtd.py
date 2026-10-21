#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""2D acoustic finite-difference time-domain (FDTD) simulation.

A staggered-grid (Yee-style) pressure-velocity leapfrog solver for the
linear acoustic equations in a non-moving medium, following the reference
formulation of Attenborough & Van Renterghem, *Predicting Outdoor Sound*
(2nd ed., CRC Press 2021), chapter 4:

* the governing first-order system in ``p`` and ``v`` (Eqs. 4.3-4.4);
* the staggered-in-place, staggered-in-time discretisation (Eqs. 4.11-4.12),
  with pressure at cell centres and velocity components on cell faces;
* the Courant stability condition :math:`C_\mathrm{N} \le 1` with
  :math:`C_\mathrm{N} = c\,\Delta t \sqrt{1/\Delta x^2 + 1/\Delta y^2}`
  (Eqs. 4.13-4.14);
* rigid boundaries as zero normal face velocity (Eq. 4.32) and the
  frequency-independent real-impedance boundary update (Eqs. 4.33-4.35);
* absorbing edges as a graded sponge layer, the simple precursor of the
  perfectly-matched-layer treatment discussed in section 4.2.3.

Two API levels are exposed. :func:`fdtd_simulation` is the result-object
entry point: it builds the grid, runs a deterministic simulation and returns
a frozen :class:`FDTDResult` with per-probe pressure histories, optional
field snapshots and a ``.plot()`` method. :class:`FDTD2D` is the underlying
stepping engine (also used by the documentation animations) for callers that
need frame-by-frame access to the field.

The solver is deliberately deterministic: no random numbers, and every
operation in a fixed order. On NumPy in float64 identical inputs give
bit-identical outputs on the same platform. On CuPy in float64 the recorded
proof (``gpu-parity.lock``) found every field, snapshot and contour phasor
bit-identical to NumPy's over the scenarios of both engines, and the energy
within 1.79e-16 relative over them, because the GPU sums it in another
order; the guide on where a simulation runs names the hardware it was
measured on. Runs on torch's CPU device, and float32 runs on NumPy, agree
with NumPy in float64 within the tolerance that guide publishes for each
device and dtype. Each of these bounds is the worst over that scenario
matrix (grids of up to 64 by 48 cells, up to 120 steps), not a promise about
any run: float32 rounding grows with the number of steps. An acoustic run
of 8085 steps on a 200 by 300 cell grid, driven by a 1 kHz ``CWSource``,
differed by 8.0e-06 relative at its probe (4.0e-06 with a Gaussian pulse),
on NumPy and on torch's CPU device alike. A float32 run on CuPy, and any run
on torch's CUDA device, is not measured yet.

Validated against analytic oracles: the eigenfrequencies of a rigid
rectangular box and of an effectively 1D tube, the numerical dispersion
relation of the leapfrog scheme (the discrete counterpart of Eq. 4.15),
free-field pulse arrival times and cylindrical :math:`1/\sqrt{r}` amplitude
decay, the image-source echo of a rigid wall, the normal-incidence
reflection coefficient :math:`(Z - \rho c)/(Z + \rho c)` of an impedance
edge, and second-order convergence under grid refinement.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, Protocol

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .._internal.display import RichDisplay
from .._internal.frozen import OwnsArrays, handed_over, read_only_copy
from .._internal.validation import (
    require_choice,
    require_count,
    require_equal_counts,
    require_positive,
    require_ranks,
    require_same_length,
    require_scalar,
)
from . import _backends
from .compute import RunProvenance
from .ntff import ContourPhasors

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence

    from matplotlib.axes import Axes

    from .._i18n import Language
    from .compute import Compute

__all__ = [
    "FDTD2D",
    "CWSource",
    "ContourProbe",
    "FDTDRecording",
    "FDTDResult",
    "GaussianPulse",
    "PlaneWaveSource",
    "SignalSource",
    "fdtd_simulation",
]

Field2D = NDArray[np.float64]

#: A side of the rectangular domain, by name.
Side = Literal["left", "right", "top", "bottom"]
#: How a side of the acoustic domain is terminated, by name.
AcousticBoundary = Literal["rigid", "absorbing"]

_SIDES: tuple[Side, ...] = ("left", "right", "top", "bottom")
#: Plane-wave travel directions accepted by ``FDTD2D.add_plane_wave``.
_SIDE_TRAVEL = ("down", "up", "left", "right")

#: Boundary-condition names accepted by :func:`fdtd_simulation`.
_BOUNDARY_NAMES = ("rigid", "absorbing")


def _positive_finite(name: str, value: float) -> float:
    """Validate that *value* is a strictly positive finite scalar."""
    require_scalar(value, name)
    out = float(value)
    if not np.isfinite(out) or out <= 0.0:
        msg = f"{name} must be positive and finite"
        raise ValueError(msg)
    return out


def _finite(name: str, value: float) -> float:
    """Validate that *value* is a finite scalar."""
    require_scalar(value, name)
    out = float(value)
    if not np.isfinite(out):
        msg = f"{name} must be finite"
        raise ValueError(msg)
    return out


def _integer(name: str, value: int) -> int:
    """Validate that *value* is an integral scalar (bool is rejected).

    A count or a cell index of the grid, refused as
    :func:`~phonometry._internal.validation.require_count` refuses one: a
    :class:`TypeError` for anything that is not a number, a
    :class:`ValueError` for a number that is not whole. The bound each one
    has is checked where it is read.
    """
    return require_count(value, name, at_least=None)


def _hold_cells(record: object, *names: str) -> None:
    """Hold each named cell index of a source record as the int it names.

    ``ix=2.0`` names cell 2, and the engine indexes its arrays with the
    record's own fields, so a whole float is stored as an int and anything
    else is refused here, where the record is built, rather than at the
    first step.

    :param record: The frozen source record being built.
    :param names: Its cell-index fields.
    :raises TypeError: for an index that is not a number, or a flag.
    :raises ValueError: for an index that is not whole.
    """
    for name in names:
        object.__setattr__(record, name, _integer(name, getattr(record, name)))


def _positive_map(name: str, field: Field2D) -> None:
    """Validate that every cell of *field* is strictly positive and finite."""
    if not np.all(np.isfinite(field)) or bool(np.any(field <= 0.0)):
        msg = f"{name} must be strictly positive and finite everywhere"
        raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class GaussianPulse(RichDisplay):
    r"""A soft Gaussian pressure pulse injected at one cell.

    :math:`s(t) = \text{amplitude} \cdot \mathrm{e}^{-((t - t_0)/w)^2}`, with :math:`w`
    the half-width ``half_width_s`` and ``t0`` defaulting to
    ``4 * half_width_s`` so the pulse starts from (numerically) zero.

    :ivar ix: Source column (x) index; the cell centre is at
        :math:`x = (i_x + 0.5)\,\Delta x`.
    :ivar iy: Source row (y) index.
    :ivar half_width_s: Gaussian half-width :math:`w` [s]; it sets the pulse
        bandwidth. The name carries the unit because the perfectly matched
        layer of this same module measures its own width in cells.
    :ivar t0: Pulse centre time [s] (default ``4 * half_width_s``).
    :ivar amplitude: Peak source amplitude [Pa].
    """

    ix: int
    iy: int
    half_width_s: float
    t0: float | None = None
    amplitude: float = 1.0

    def __post_init__(self) -> None:
        """Hold the cell indices as ints and check the pulse parameters.

        ``half_width_s`` is positive, ``amplitude`` and ``t0`` finite.

        :raises TypeError: if ``ix`` or ``iy`` is not a number, or
            ``amplitude``, ``half_width_s`` or ``t0`` is not a single number.
        :raises ValueError: if ``ix`` or ``iy`` is not whole.
        """
        _hold_cells(self, "ix", "iy")
        _positive_finite("half_width_s", self.half_width_s)
        _finite("amplitude", self.amplitude)
        if self.t0 is not None:
            _finite("t0", self.t0)

    def value(self, t: float) -> float:
        """Source waveform at time ``t`` (seconds)."""
        t0 = 4.0 * self.half_width_s if self.t0 is None else self.t0
        return self.amplitude * float(np.exp(-(((t - t0) / self.half_width_s) ** 2)))


@dataclass(frozen=True, kw_only=True)
class CWSource(RichDisplay):
    """A continuous sine drive with a smooth cosine-ramped onset.

    The first ``ramp_cycles`` periods fade the amplitude in with a raised
    cosine so the start does not splash a broadband transient over the field.

    :ivar ix: Source column (x) index.
    :ivar iy: Source row (y) index.
    :ivar frequency: Drive frequency [Hz].
    :ivar amplitude: Steady-state source amplitude [Pa].
    :ivar ramp_cycles: Onset ramp length in periods of ``frequency``.
    """

    ix: int
    iy: int
    frequency: float
    amplitude: float = 1.0
    ramp_cycles: float = 3.0

    def __post_init__(self) -> None:
        """Hold the cell indices as ints and check the drive parameters.

        ``frequency`` is positive and ``ramp_cycles`` non-negative.

        :raises TypeError: if ``ix`` or ``iy`` is not a number, or
            ``amplitude``, ``frequency`` or ``ramp_cycles`` is not a single
            number.
        :raises ValueError: if ``ix`` or ``iy`` is not whole.
        """
        _hold_cells(self, "ix", "iy")
        require_scalar(self.ramp_cycles, "ramp_cycles")
        _positive_finite("frequency", self.frequency)
        _finite("amplitude", self.amplitude)
        if not np.isfinite(self.ramp_cycles) or self.ramp_cycles < 0.0:
            msg = "ramp_cycles must be non-negative and finite"
            raise ValueError(msg)

    def value(self, t: float) -> float:
        """Source waveform at time ``t`` (seconds)."""
        ramp_time = self.ramp_cycles / self.frequency
        if t < ramp_time and ramp_time > 0.0:
            envelope = 0.5 * (1.0 - float(np.cos(np.pi * t / ramp_time)))
        else:
            envelope = 1.0
        return (
            self.amplitude * envelope * float(np.sin(2.0 * np.pi * self.frequency * t))
        )


@dataclass(frozen=True, kw_only=True)
class SignalSource(OwnsArrays):
    """An arbitrary sampled waveform injected at one cell.

    The samples are interpreted as the source signal at ``fs`` and
    linearly interpolated onto the simulation time steps; outside the sampled
    span the source is zero. ``fs`` therefore does not need to match
    the simulation rate ``1/dt``, although a rate well above the highest
    frequency of interest avoids interpolation roll-off.

    :ivar ix: Source column (x) index.
    :ivar iy: Source row (y) index.
    :ivar samples: Source signal samples [Pa] (stored as a read-only 1D
        float64 array).
    :ivar fs: Sampling rate of ``samples`` [Hz].
    :ivar amplitude: Scale factor applied to the samples.
    """

    ix: int
    iy: int
    samples: NDArray[np.float64]
    fs: float
    amplitude: float = 1.0

    def __post_init__(self) -> None:
        """Hold the cell indices as ints, check ``fs`` and freeze the ``samples``.

        ``fs`` is positive and ``samples`` a finite, non-empty 1D array.

        :raises TypeError: if ``ix`` or ``iy`` is not a number, or
            ``amplitude`` or ``fs`` is not a single number.
        :raises ValueError: if ``ix`` or ``iy`` is not whole.
        """
        _hold_cells(self, "ix", "iy")
        _positive_finite("fs", self.fs)
        _finite("amplitude", self.amplitude)
        arr = np.asarray(self.samples, dtype=np.float64)
        if arr.ndim != 1:
            msg = "samples must be a 1D array"
            raise ValueError(msg)
        if arr.size == 0:
            msg = "samples must not be empty"
            raise ValueError(msg)
        if not np.all(np.isfinite(arr)):
            msg = "samples must be finite"
            raise ValueError(msg)
        arr.flags.writeable = False
        object.__setattr__(self, "samples", arr)

    def value(self, t: float) -> float:
        """Source waveform at time ``t`` (seconds), zero outside the span."""
        pos = t * self.fs
        last = self.samples.size - 1
        if pos < 0.0 or pos > last:
            return 0.0
        i = int(pos)
        if i >= last:
            return self.amplitude * float(self.samples[last])
        w = pos - i
        return self.amplitude * float(
            (1.0 - w) * self.samples[i] + w * self.samples[i + 1]
        )


@dataclass(frozen=True, kw_only=True)
class PlaneWaveSource(RichDisplay):
    """A sustained one-way plane wave injected on a line near one edge.

    A total-field/scattered-field style injection: each step the incident
    wave is added simultaneously to the pressure on the injection line and
    to the particle velocity on the adjacent face, so the wave launches
    only toward ``direction`` and anything scattered back crosses the line
    untouched (and can be absorbed by a sponge behind it).

    ``direction`` is the travel direction (``"down"``, ``"up"``,
    ``"left"``, ``"right"`` in the :meth:`FDTD2D.plot_geometry` axes) and
    the line sits ``offset`` cells in from the opposite edge (place it just
    inside the sponge layer when one is configured on that side).
    ``waveform`` maps time in seconds to the incident pressure in pascals
    (any callable, or reuse the ``value`` method of a point source).

    :ivar direction: Travel direction of the launched wave.
    :ivar waveform: Callable ``t -> p_inc(t)`` in pascals.
    :ivar offset: Line position, in cells from the launch edge.
    :ivar amplitude: Extra gain applied to ``waveform``.
    """

    direction: str
    waveform: Callable[[float], float]
    offset: int = 0
    amplitude: float = 1.0

    def __post_init__(self) -> None:
        """Require a callable ``waveform`` and a finite ``amplitude``.

        ``direction`` and ``offset`` are checked against the grid in
        :meth:`FDTD2D.add_source`, which is the first place a grid exists;
        ``offset`` is held as the whole number of cells it names here.

        :raises TypeError: if ``waveform`` is not callable, ``offset`` is not a
            number, or ``amplitude`` is not one number.
        :raises ValueError: if ``offset`` is not whole or ``amplitude`` is not
            finite.
        """
        _hold_cells(self, "offset")
        if not callable(self.waveform):
            msg = "waveform must be callable"
            raise TypeError(msg)
        _finite("amplitude", self.amplitude)


Source = GaussianPulse | CWSource | SignalSource

#: Everything :meth:`FDTD2D.add_source` accepts.
AnySource = Source | PlaneWaveSource


def _sponge_profile(
    n: int, width: int, sides: tuple[bool, bool], sigma_max: float
) -> Field2D:
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
        sigma[n - width :] = np.maximum(sigma[n - width :], ramp[::-1])
    return sigma


def _sigma_map(
    shape: tuple[int, int],
    sides: tuple[str, ...],
    sponge_width: int,
    sponge_reflection: float,
    damping: NDArray[np.float64],
    c_max: float,
    dx: float,
) -> Field2D:
    """Absorption-rate map sigma(x, y) [1/s]: sponge ramps plus damping."""
    ny, nx = shape
    sigma_max = 0.0
    if sponge_width > 0:
        # Quadratic-profile PML-style rate for a target reflection R:
        # exp(-2 * sigma_max * (w dx) / (3 c)) = R  (two-way transit).
        sigma_max = (
            -3.0 * c_max * float(np.log(sponge_reflection)) / (2.0 * sponge_width * dx)
        )
    sig_x = _sponge_profile(
        nx, sponge_width, ("left" in sides, "right" in sides), sigma_max
    )
    sig_y = _sponge_profile(
        ny, sponge_width, ("top" in sides, "bottom" in sides), sigma_max
    )
    return sig_x[np.newaxis, :] + sig_y[:, np.newaxis] + damping


def _validate_sponge_damping(
    sponge_width: int,
    sponge_reflection: float,
    damping: float | NDArray[np.float64],
    ny: int,
    nx: int,
) -> tuple[int, NDArray[np.float64]]:
    """Validate the sponge/damping spec into ``(width, damping map)``."""
    require_scalar(sponge_reflection, "sponge_reflection")
    require_scalar(sponge_width, "sponge_width")
    sponge_width = _integer("sponge_width", sponge_width)
    if sponge_width < 0:
        msg = "sponge_width must be non-negative"
        raise ValueError(msg)
    if sponge_width >= min(nx, ny):
        msg = "sponge_width must be narrower than the smallest grid side"
        raise ValueError(msg)
    if not 0.0 < sponge_reflection < 1.0:
        msg = "sponge_reflection must lie strictly between 0 and 1"
        raise ValueError(msg)
    damping_map = np.asarray(damping, dtype=np.float64)
    if damping_map.ndim not in (0, 2):
        msg = "damping must be a scalar or an (ny, nx) map"
        raise ValueError(msg)
    if not np.all(np.isfinite(damping_map)) or np.any(damping_map < 0.0):
        msg = "damping must be non-negative and finite"
        raise ValueError(msg)
    # The number is a count of array axes, not a quantity.
    if damping_map.ndim == 2 and damping_map.shape != (ny, nx):  # noqa: PLR2004
        msg = (
            f"damping map shape {damping_map.shape} does not match the grid {(ny, nx)}"
        )
        raise ValueError(msg)
    return sponge_width, damping_map


class _PressureEngine(Protocol):
    """The stepping interface the shared ``run()`` driver relies on."""

    _backend: _backends.Backend

    def step(self) -> None:
        """Advance the leapfrog scheme by one time step."""

    @property
    def p(self) -> _backends.DeviceArray:
        """Pressure at the cell centres, shape ``(ny, nx)``, on the device."""


def _snapshot_options(
    snapshot_every: int | None,
    snapshot_decimation: int,
) -> tuple[int | None, int]:
    """The snapshot cadence and decimation, validated alike on every route.

    The ``run()`` of both engines, :class:`FDTDRecording` and the elastic
    simulation function read the two counts here, so a bad value is refused
    with the same class and the same words whichever way it came in.

    :param snapshot_every: Steps between snapshots, or ``None`` for none.
    :param snapshot_decimation: Cells a snapshot steps over along each axis.
    :return: Both as ``int``, the cadence ``None`` when no snapshot is asked.
    :raises TypeError: for a flag, a text, an array or anything else that is
        not a number, ``None`` excepted for ``snapshot_every``.
    :raises ValueError: for a number that is not a whole number of 1 or more.
    """
    require_scalar(snapshot_every, "snapshot_every")
    require_scalar(snapshot_decimation, "snapshot_decimation")
    every = (
        None
        if snapshot_every is None
        else require_count(snapshot_every, "snapshot_every")
    )
    return every, require_count(snapshot_decimation, "snapshot_decimation")


def _run_recording(
    engine: _PressureEngine,
    n_steps: int,
    snapshot_every: int | None,
    snapshot_decimation: int,
) -> NDArray[np.floating]:
    """Validate the ``run()`` arguments and march, recording pressure frames.

    The frames are written into one host array allocated before the march
    (one for the initial state, then one every ``snapshot_every`` steps), so
    the recording is never held twice, as a list of frames and their stack.
    """
    every, d = _snapshot_options(snapshot_every, snapshot_decimation)
    require_scalar(n_steps, "n_steps")
    n_steps = _integer("n_steps", n_steps)
    if n_steps < 0:
        msg = "'n_steps' must be non-negative"
        raise ValueError(msg)
    backend = engine._backend
    if every is None:
        for _ in range(n_steps):
            engine.step()
        return np.zeros((0, 0, 0), dtype=backend.host_dtype)
    first = backend.to_host(engine.p[::d, ::d])
    frames = np.zeros((n_steps // every + 1, *first.shape), dtype=first.dtype)
    frames[0] = first
    for i in range(n_steps):
        engine.step()
        if (i + 1) % every == 0:
            frames[(i + 1) // every] = backend.to_host(engine.p[::d, ::d])
    return frames


def _validated_obstacle(
    obstacle_mask: NDArray[np.bool_] | None, ny: int, nx: int
) -> NDArray[np.bool_] | None:
    """Validate the obstacle mask; ``None`` when absent or all open."""
    if obstacle_mask is None:
        return None
    mask = np.asarray(obstacle_mask)
    if mask.shape != (ny, nx):
        msg = "obstacle_mask must match the grid shape"
        raise ValueError(msg)
    if mask.dtype != np.bool_:
        msg = "obstacle_mask must be a boolean array"
        raise TypeError(msg)
    if bool(mask.all()):
        msg = "obstacle_mask must leave open cells"
        raise ValueError(msg)
    return mask.copy() if bool(mask.any()) else None


def _grid_shape(shape: object) -> tuple[int, int]:
    """The ``(ny, nx)`` grid a scalar sound speed is spread over.

    A value that is not a pair, or a cell count that is not a number, is the
    wrong type; a pair of another length, or a count that is not a whole
    number of one cell or more, is a wrong value. A whole float is kept as
    the count it names.

    :raises TypeError: for a value that is not a tuple or a list, or a count
        that is not a number.
    :raises ValueError: for a sequence of another length than two, or a count
        that is not a whole number of at least one.
    """
    msg = f"shape must be a pair of positive integers (ny, nx); got {shape!r}"
    if not isinstance(shape, (tuple, list)):
        raise TypeError(msg)
    # The length of a fixed-size argument, not a quantity.
    if len(shape) != 2:  # noqa: PLR2004
        raise ValueError(msg)
    try:
        ny, nx = (require_count(n, "shape") for n in shape)
    except TypeError:
        raise TypeError(msg) from None
    except ValueError:
        raise ValueError(msg) from None
    return ny, nx


def _resolve_c_map(c: float | Field2D, shape: tuple[int, int] | None) -> Field2D:
    """Broadcast/validate the sound-speed spec into a positive 2D map."""
    if np.iscomplexobj(c):
        msg = "c must be real; a complex sound speed is not supported"
        raise TypeError(msg)
    if np.isscalar(c):
        if shape is None:
            msg = "shape is required when c is a scalar"
            raise ValueError(msg)
        c_map = np.full(_grid_shape(shape), float(np.real(c)), dtype=np.float64)
    else:
        c_map = np.asarray(c, dtype=np.float64)
    # The number is a count of array axes, not a quantity.
    if c_map.ndim != 2:  # noqa: PLR2004
        msg = "c must be a 2D (ny, nx) map"
        raise ValueError(msg)
    _positive_map("c", c_map)
    return c_map


def _resolve_rho_map(rho: float | Field2D, ny: int, nx: int) -> Field2D:
    """Broadcast/validate the density spec into a positive ``(ny, nx)`` map."""
    if np.iscomplexobj(rho):
        msg = "rho must be real; a complex density is not supported"
        raise TypeError(msg)
    rho_map = (
        np.full((ny, nx), float(np.real(rho)), dtype=np.float64)
        if np.isscalar(rho)
        else np.asarray(rho, dtype=np.float64)
    )
    if rho_map.shape != (ny, nx):
        msg = "rho map must match the shape of c"
        raise ValueError(msg)
    _positive_map("rho", rho_map)
    return rho_map


def _resolve_sponge_sides(
    sponge_sides: Side | Iterable[Side] | None,
) -> tuple[Side, ...]:
    """Normalise the sponge-side spec into a validated tuple of side names."""
    if sponge_sides is None:
        sides: tuple[Side, ...] = _SIDES
    elif isinstance(sponge_sides, str):
        # A bare string would iterate per character; treat it as one side.
        sides = (sponge_sides,)
    else:
        sides = tuple(sponge_sides)
    unknown = set(sides) - set(_SIDES)
    if unknown:
        msg = f"unknown sponge sides: {sorted(unknown)}"
        raise ValueError(msg)
    return sides


def _edge_impedance_profile(
    side: str, value: float | NDArray[np.float64], n_edge: int
) -> Field2D:
    """Broadcast/validate one side's impedance into a positive 1D profile."""
    z = np.asarray(value, dtype=np.float64)
    if z.ndim == 0:
        z = np.full(n_edge, float(z), dtype=np.float64)
    if z.shape != (n_edge,):
        msg = (
            f"impedance for side {side!r} must be a scalar or a 1D "
            f"array of length {n_edge}"
        )
        raise ValueError(msg)
    if not np.all(np.isfinite(z)) or bool(np.any(z <= 0.0)):
        msg = f"impedance for side {side!r} must be strictly positive and finite"
        raise ValueError(msg)
    return z


def _validated_impedances(
    edge_impedance: Mapping[Side, float | NDArray[np.float64]] | None,
    absorbing: tuple[str, ...],
    ny: int,
    nx: int,
) -> list[tuple[str, Field2D]]:
    """Validate the per-side impedance spec into ``(side, profile)`` pairs.

    :param absorbing: The sides that carry a sponge layer, which cannot
        also be impedance boundaries.
    :return: One pair per impedance side, in the order of :data:`_SIDES`.
    """
    if not edge_impedance:
        return []
    unknown = set(edge_impedance) - set(_SIDES)
    if unknown:
        msg = f"unknown impedance sides: {sorted(unknown)}"
        raise ValueError(msg)
    profiles: list[tuple[str, Field2D]] = []
    for side in _SIDES:  # deterministic order
        if side not in edge_impedance:
            continue
        if side in absorbing:
            msg = f"side {side!r} cannot be both absorbing and an impedance boundary"
            raise ValueError(msg)
        n_edge = ny if side in ("left", "right") else nx
        profiles.append(
            (side, _edge_impedance_profile(side, edge_impedance[side], n_edge))
        )
    return profiles


def _require_courant(cfl: float) -> None:
    """Refuse a Courant number outside ``(0, 1)``, where the leapfrog is unstable.

    :raises TypeError: if ``cfl`` is not a single number.
    """
    require_scalar(cfl, "cfl")
    if not np.isfinite(cfl) or not 0.0 < cfl < 1.0:
        msg = (
            "cfl must lie in (0, 1): the leapfrog scheme "
            "is unstable beyond the Courant bound CN = 1"
        )
        raise ValueError(msg)


def _time_step(cfl: float, dx: float, c_max: float) -> float:
    r"""The time step of Courant number *cfl*: Eq. 4.13 solved for :math:`\Delta t`.

    One formula for both engines and for the simulation functions, which
    count a run's steps before they build its engine.
    """
    return cfl * dx / (c_max * float(np.sqrt(2.0)))


def _acoustic_grid(
    c: float | Field2D, shape: tuple[int, int] | None, cfl: float, dx: float
) -> tuple[Field2D, float, float]:
    """The sound-speed map, the grid spacing and the time step, checked on the host.

    :return: ``(c_map, dx, dt)``.
    """
    _require_courant(cfl)
    c_map = _resolve_c_map(c, shape)
    dx = _positive_finite("dx", dx)
    return c_map, dx, _time_step(cfl, dx, float(c_map.max()))


def _step_count(duration: float, dt: float) -> int:
    """The number of steps of *dt* that cover *duration*, at least one."""
    steps = round(duration / dt)
    if steps < 1:
        msg = f"duration must cover at least one time step (dt = {dt:.3e} s)"
        raise ValueError(msg)
    return steps


def _check_source(
    source: AnySource, shape: tuple[int, ...], obstacle: NDArray[np.bool_] | None
) -> None:
    """Refuse a source off the grid ``(ny, nx)`` or inside the obstacle.

    Shared by :meth:`FDTD2D.add_source` and :func:`fdtd_simulation`, which
    checks its sources before it builds the engine.
    """
    if isinstance(source, PlaneWaveSource):
        _check_plane_source(source, shape, obstacle)
        return
    ny, nx = shape
    ix = _integer("source ix", source.ix)
    iy = _integer("source iy", source.iy)
    if not (0 <= ix < nx and 0 <= iy < ny):
        msg = "source position lies outside the grid"
        raise ValueError(msg)
    if obstacle is not None and obstacle[iy, ix]:
        msg = "source position lies inside an obstacle"
        raise ValueError(msg)


def _check_plane_source(
    source: PlaneWaveSource,
    shape: tuple[int, ...],
    obstacle: NDArray[np.bool_] | None,
) -> None:
    """Refuse a plane-wave injection line off the grid or across the obstacle."""
    if source.direction not in _SIDE_TRAVEL:
        msg = "'direction' must be 'down', 'up', 'left' or 'right'."
        raise ValueError(msg)
    offset = _integer("plane-wave offset", source.offset)
    ny, nx = shape
    limit = ny if source.direction in ("down", "up") else nx
    if not 0 <= offset < limit - 1:
        msg = "plane-wave offset lies outside the grid"
        raise ValueError(msg)
    if obstacle is not None:
        if source.direction == "down":
            line = obstacle[offset, :]
        elif source.direction == "up":
            line = obstacle[ny - 1 - offset, :]
        elif source.direction == "right":
            line = obstacle[:, offset]
        else:
            line = obstacle[:, nx - 1 - offset]
        if bool(np.any(line)):
            msg = "plane-wave injection line crosses an obstacle"
            raise ValueError(msg)


class _ImpedanceEdge:
    r"""One locally reacting boundary side with a real specific impedance.

    Implements the frequency-independent real-impedance velocity update of
    Attenborough & Van Renterghem Eqs. (4.33)-(4.35): the boundary-face
    normal velocity ``vb`` is stored on the wall, updated implicitly from the
    half-cell pressure gradient with the surface pressure eliminated through
    :math:`p_{\text{surf}} = Z v_{\text{out}}` (time-averaged over the two
    half steps), and its flux enters the divergence of the adjacent pressure
    cells.
    """

    __slots__ = ("c1", "c2", "side", "vb")

    def __init__(
        self,
        side: str,
        impedance: Field2D,
        rho_edge: Field2D,
        dt: float,
        dx: float,
        backend: _backends.Backend,
    ) -> None:
        self.side = side
        # a = dt Z / (rho dx): the dimensionless boundary Courant product,
        # on the host; the two coefficients go to the device once.
        a = dt * impedance / (rho_edge * dx)
        self.c1 = backend.asarray((1.0 - a) / (1.0 + a))
        self.c2 = backend.asarray((2.0 * dt / (rho_edge * dx)) / (1.0 + a))
        self.vb = backend.zeros(impedance.shape)

    def update(self, p: _backends.DeviceArray) -> None:
        """Advance the boundary-face velocity by one leapfrog step."""
        if self.side == "left":
            self.vb = self.c1 * self.vb - self.c2 * p[:, 0]
        elif self.side == "right":
            self.vb = self.c1 * self.vb + self.c2 * p[:, -1]
        elif self.side == "top":
            self.vb = self.c1 * self.vb - self.c2 * p[0, :]
        else:  # bottom
            self.vb = self.c1 * self.vb + self.c2 * p[-1, :]

    def add_flux(self, div: _backends.DeviceArray) -> None:
        """Add the boundary-face flux to the velocity divergence."""
        if self.side == "left":
            div[:, 0] -= self.vb
        elif self.side == "right":
            div[:, -1] += self.vb
        elif self.side == "top":
            div[0, :] -= self.vb
        else:  # bottom
            div[-1, :] += self.vb


class ContourProbe:
    r"""On-the-fly DFT of ``p`` and ``v_n`` on a closed rectangular contour.

    Created by :meth:`FDTD2D.add_contour_probe`. The contour is the closed
    rectangle of cell faces around the cell block ``ix0..ix1`` x
    ``iy0..iy1`` (inclusive); on each face the engine samples the outward
    normal velocity (which lives exactly there on the staggered grid) and
    the pressure averaged from the two adjacent cell centres, and folds
    them into running DFT sums at each requested frequency, so a
    continuous-wave run never stores full time histories.

    After every step the sums gain :math:`p\, \mathrm{e}^{-j \omega t}` with
    the fields' own leapfrog time stamps (:math:`t = n\,\Delta t` for
    pressure, :math:`t = (n - 1/2)\,\Delta t` for velocity, so the half-step
    stagger is handled
    exactly). :meth:`phasors` scales the sums by ``2 / n_samples`` into the
    steady-state complex amplitudes of the library's :math:`\mathrm{e}^{+j \omega t}`
    convention. Accumulate only over the steady state: run the transient
    out, call :meth:`reset`, then integrate a window as close as possible
    to a whole number of periods (the residual leakage falls as one over
    the number of periods).

    The sums are kept in float64 on every device that has it, also when the
    fields step in float32: the rounding of a sum grows with the number of
    steps, and in float32 it would soon outweigh the field's own. The
    exception is ``torch:mps``, which has no float64; there the sums are
    float32 with Neumaier's compensated summation.

    :ivar positions: Face-sample positions ``(x, y)`` [m], shape
        ``(n_points, 2)``, ordered left, right, top, bottom face.
    :ivar normals: Outward unit normals of each sample, same shape.
    :ivar frequencies: The tracked frequencies [Hz].
    :ivar samples: Number of steps accumulated since the last reset.
    :raises TypeError: if ``ix0``, ``ix1``, ``iy0`` or ``iy1`` is a flag, a text or an
        array where a count goes.
    """

    def __init__(
        self,
        sim: FDTD2D,
        ix0: int,
        ix1: int,
        iy0: int,
        iy1: int,
        frequencies: ArrayLike,
    ) -> None:
        require_scalar(ix0, "ix0")
        require_scalar(ix1, "ix1")
        require_scalar(iy0, "iy0")
        require_scalar(iy1, "iy1")
        ny, nx = sim.p.shape
        ix0 = _integer("ix0", ix0)
        ix1 = _integer("ix1", ix1)
        iy0 = _integer("iy0", iy0)
        iy1 = _integer("iy1", iy1)
        if not (1 <= ix0 <= ix1 <= nx - 2 and 1 <= iy0 <= iy1 <= ny - 2):
            msg = (
                "the contour block needs 1 <= ix0 <= ix1 <= nx - 2 and "
                "1 <= iy0 <= iy1 <= ny - 2, so every sampled face has an "
                "open cell on both sides"
            )
            raise ValueError(msg)
        freqs = np.atleast_1d(np.asarray(frequencies, dtype=np.float64))
        if (
            freqs.ndim != 1
            or freqs.size == 0
            or not np.all(np.isfinite(freqs))
            or bool(np.any(freqs <= 0.0))
        ):
            msg = (
                "frequencies must be a non-empty 1D sequence of positive finite values"
            )
            raise ValueError(msg)
        if sim._obstacle is not None:
            # Every sampled face needs open cells on both of its sides:
            # the two cell columns flanking the vertical faces and the two
            # cell rows flanking the horizontal ones.
            blocked = bool(
                sim._obstacle[iy0 : iy1 + 1, [ix0 - 1, ix0, ix1, ix1 + 1]].any()
                or sim._obstacle[[iy0 - 1, iy0, iy1, iy1 + 1], ix0 : ix1 + 1].any()
            )
            if blocked:
                msg = (
                    "the contour faces touch obstacle cells; the closed "
                    "rectangle must run through open air with the whole "
                    "scatterer strictly inside"
                )
                raise ValueError(msg)
        self._ix0, self._ix1 = ix0, ix1
        self._iy0, self._iy1 = iy0, iy1
        self._ys = slice(iy0, iy1 + 1)
        self._xs = slice(ix0, ix1 + 1)
        n_side = iy1 - iy0 + 1
        n_band = ix1 - ix0 + 1
        dx = sim.dx
        y_faces = (np.arange(iy0, iy1 + 1, dtype=np.float64) + 0.5) * dx
        x_faces = (np.arange(ix0, ix1 + 1, dtype=np.float64) + 0.5) * dx
        pos = np.empty((2 * (n_side + n_band), 2), dtype=np.float64)
        nrm = np.zeros_like(pos)
        s_left = slice(0, n_side)
        s_right = slice(n_side, 2 * n_side)
        s_top = slice(2 * n_side, 2 * n_side + n_band)
        s_bottom = slice(2 * n_side + n_band, 2 * (n_side + n_band))
        pos[s_left, 0], pos[s_left, 1] = ix0 * dx, y_faces
        pos[s_right, 0], pos[s_right, 1] = (ix1 + 1) * dx, y_faces
        pos[s_top, 0], pos[s_top, 1] = x_faces, iy0 * dx
        pos[s_bottom, 0], pos[s_bottom, 1] = x_faces, (iy1 + 1) * dx
        nrm[s_left, 0], nrm[s_right, 0] = -1.0, 1.0
        nrm[s_top, 1], nrm[s_bottom, 1] = -1.0, 1.0
        pos.flags.writeable = False
        nrm.flags.writeable = False
        self.positions: NDArray[np.float64] = pos
        self.normals: NDArray[np.float64] = nrm
        self.frequencies: tuple[float, ...] = tuple(float(f) for f in freqs)
        self._omega = 2.0 * np.pi * freqs
        self._dt = sim.dt
        self._dx = dx
        b = sim._backend
        self._backend = b
        self._segments = (s_left, s_right, s_top, s_bottom)
        n_points = pos.shape[0]
        # The running DFT sums, frequency first so that phasors() brings one
        # frequency to the host: then the quantity (p, v_n), the part (real,
        # imaginary) and the contour point.
        sums_shape = (freqs.size, 2, 2, n_points)
        acc = b.accumulator_dtype
        self._sums = b.zeros(sums_shape, dtype=acc)
        # What each float32 addition rounds away (Neumaier); float64 sums
        # need no compensation.
        self._carry = b.zeros(sums_shape, dtype=acc) if acc == "float32" else None
        # This step's face samples (p, v_n) in the field dtype, shaped to
        # broadcast over the parts and filled in place every step.
        self._now = b.zeros((2, 1, n_points))
        self.samples = 0

    def reset(self) -> None:
        """Clear the running sums (call once the field is steady)."""
        with self._backend.context():
            self._sums[...] = 0.0
            if self._carry is not None:
                self._carry[...] = 0.0
        self.samples = 0

    def _accumulate(
        self,
        p: _backends.DeviceArray,
        vx: _backends.DeviceArray,
        vy: _backends.DeviceArray,
        n: int,
    ) -> None:
        r"""Fold the current fields into the running DFT sums.

        The phases are computed on the host in float64 and moved to the
        device in one transfer; the products are summed there, real and
        imaginary parts apart. NumPy multiplies a complex phase
        :math:`a + jb` by a real sample :math:`x` as
        :math:`(a x - b \cdot 0) + j (a \cdot 0 + b x)`, which differs from
        :math:`a x` and :math:`b x` at most in the sign of a zero; the sums
        start at +0, and a sum that starts at +0 never turns -0, so the split
        sums equal the complex ones bit for bit.
        """
        b = self._backend
        ys, xs = self._ys, self._xs
        ix0, ix1 = self._ix0, self._ix1
        iy0, iy1 = self._iy0, self._iy1
        left, right, top, bottom = self._segments
        now = self._now
        now[0, 0, left] = 0.5 * (p[ys, ix0 - 1] + p[ys, ix0])
        now[0, 0, right] = 0.5 * (p[ys, ix1] + p[ys, ix1 + 1])
        now[0, 0, top] = 0.5 * (p[iy0 - 1, xs] + p[iy0, xs])
        now[0, 0, bottom] = 0.5 * (p[iy1, xs] + p[iy1 + 1, xs])
        now[1, 0, left] = -vx[ys, ix0 - 1]
        now[1, 0, right] = vx[ys, ix1]
        now[1, 0, top] = -vy[iy0 - 1, xs]
        now[1, 0, bottom] = vy[iy1, xs]
        # Leapfrog time stamps: p sits at n dt, v half a step earlier.
        phase_p = np.exp(self._omega * (-1j * (n * self._dt)))
        phase_v = np.exp(self._omega * (-1j * ((n - 0.5) * self._dt)))
        phases = np.empty((self._omega.size, 2, 2, 1))
        phases[:, 0, 0, 0], phases[:, 0, 1, 0] = phase_p.real, phase_p.imag
        phases[:, 1, 0, 0], phases[:, 1, 1, 0] = phase_v.real, phase_v.imag
        term = b.asarray(phases, dtype=b.accumulator_dtype) * now
        if self._carry is None:
            self._sums += term
        else:
            self._add_compensated(term)
        self.samples += 1

    def _add_compensated(self, term: _backends.DeviceArray) -> None:
        """Add *term* to float32 sums with Neumaier's compensated summation.

        Each addition rounds away low bits, and ``(s - t) + term`` (or
        ``(term - t) + s`` when the term is the larger) recovers them exactly
        into the carry, which :meth:`phasors` adds back. That difference is
        exact only when its first operand is the larger one, and Kahan's form
        always takes the sum first; Neumaier's picks the order, so a term
        larger than the sum, as at the start of a window or at a frequency
        the field does not carry, loses nothing either.
        """
        xp = self._backend.xp
        s = self._sums
        t = s + term
        larger = xp.abs(s) >= xp.abs(term)
        self._carry += xp.where(larger, (s - t) + term, (term - t) + s)
        self._sums = t

    def phasors(self, frequency: float) -> ContourPhasors:
        """The accumulated contour phasors at one tracked frequency.

        :param frequency: One of the frequencies the probe was created
            with, in hertz.
        :return: A :class:`~phonometry.simulation.ntff.ContourPhasors`
            ready for
            :func:`~phonometry.simulation.ntff.far_field_from_contour`.
        :raises ValueError: If the frequency is not tracked or nothing has
            been accumulated yet.
        """
        matches = [
            i for i, f in enumerate(self.frequencies) if np.isclose(f, float(frequency))
        ]
        if not matches:
            msg = (
                f"frequency {frequency!r} Hz is not tracked by this probe "
                f"(tracked: {self.frequencies})"
            )
            raise ValueError(msg)
        if self.samples == 0:
            msg = "no samples accumulated yet; step the simulation first"
            raise ValueError(msg)
        i = matches[0]
        b = self._backend
        # Only this frequency's sums come to the host, shape (2, 2, n_points).
        sums = b.to_host(self._sums[i, ...])
        if self._carry is not None:
            sums = sums.astype(np.float64) + b.to_host(self._carry[i, ...])
        # The complex sums are rebuilt by assignment alone, so no arithmetic
        # touches the float64 ones on the way.
        acc_p = np.empty(sums.shape[-1], dtype=np.complex128)
        acc_p.real, acc_p.imag = sums[0, 0], sums[0, 1]
        acc_v = np.empty_like(acc_p)
        acc_v.real, acc_v.imag = sums[1, 0], sums[1, 1]
        scale = 2.0 / self.samples
        return ContourPhasors(
            frequency=self.frequencies[i],
            positions=self.positions,
            normals=self.normals,
            pressure=np.asarray(scale * acc_p),
            normal_velocity=np.asarray(scale * acc_v),
            segment=self._dx,
        )


class FDTD2D:
    r"""2D acoustic FDTD stepping engine on a staggered grid.

    Pressure ``p`` lives at cell centres, shape ``(ny, nx)`` (row = y,
    column = x, the ``imshow`` convention); ``vx`` at interior x-faces,
    shape ``(ny, nx - 1)``; ``vy`` at interior y-faces, shape
    ``(ny - 1, nx)``. Because only interior faces are stored, the domain
    boundary is perfectly rigid (zero normal velocity, Eq. 4.32) by
    construction; sponge layers and per-cell real impedances turn selected
    sides into absorbing or locally reacting boundaries. Sources are soft
    (additive) pressure injections.

    :param c: Sound-speed map [m/s], shape ``(ny, nx)``. A scalar with an
        explicit ``shape`` is also accepted.
    :param dx: Grid spacing [m] (square cells).
    :param rho: Density map [kg/m3]; scalar or ``(ny, nx)`` array
        (default 1.2).
    :param cfl: Courant number
        :math:`C_\mathrm{N} = c_{\max}\, \Delta t \sqrt{2} / \Delta x` (Eq. 4.13);
        the explicit scheme is stable for :math:`C_\mathrm{N} \le 1` (Eq. 4.14) and
        values
        in ``(0, 1)`` are accepted. The default 0.6 keeps a wide stability
        margin with moderate numerical dispersion.
    :param sponge_width: Thickness of the absorbing layer in cells
        (0 = no absorbing sides).
    :param sponge_sides: Which sides absorb: a single side name or an
        iterable drawn from ``{"left", "right", "top", "bottom"}``
        (default: all four when ``sponge_width > 0``). ``left``/``right``
        are the low/high column edges and ``top``/``bottom`` the low/high
        row edges (the default ``imshow`` origin).
    :param sponge_reflection: Target round-trip amplitude reflection of the
        sponge layer; sets the peak absorption rate.
    :param damping: Bulk amplitude decay rate [1/s]: a scalar applied to
        the whole field (a simple stand-in for air/wall absorption;
        ``6.91 / T60`` gives a ``T60`` seconds reverberant decay) or an
        ``(ny, nx)`` map for locally lossy regions, e.g. an equivalent
        fluid modelling a porous sample (plane waves inside a uniform
        lossy region follow :math:`k = (\omega - j \sigma) / c` with the
        real characteristic impedance :math:`\rho c`).
    :param shape: Grid shape ``(ny, nx)``, required only when ``c`` is a
        scalar.
    :param edge_impedance: Locally reacting boundary sides: a mapping from
        side name to a real specific acoustic impedance [Pa s/m], either a
        scalar or a per-edge-cell 1D array (length ``ny`` for ``left``/
        ``right``, ``nx`` for ``top``/``bottom``). Implements Eqs.
        (4.33)-(4.35); :math:`Z = \rho c` is a normal-incidence matched
        (anechoic) edge. A side cannot be both a sponge and an impedance
        boundary.
    :param obstacle_mask: Boolean map, shape ``(ny, nx)``, of rigid cells:
        every face adjacent to a masked cell is closed (zero normal
        velocity, Eq. 4.32), rasterising arbitrary interior geometry.
    :param compute: Where the engine steps (:class:`Compute`); ``None``
        follows :func:`use`, then ``PHONOMETRY_COMPUTE``, then NumPy.
    :raises TypeError: if ``cfl``, ``dx`` or ``sponge_reflection`` is not a single
        number, ``sponge_width`` is a flag, a text or an array where a count goes,
        or ``compute`` is neither a :class:`Compute` nor ``None``.
    :raises ComputeImportError: when the library of the device ``compute``
        asks for is not installed or does not import.
    :raises ComputeDeviceError: when that device is not present, or fails a
        first small computation; with ``fallback=True`` the engine warns
        with :class:`ComputeFallbackWarning` and steps on NumPy instead.
    """

    def __init__(
        self,
        c: float | Field2D,
        dx: float,
        *,
        rho: float | Field2D = 1.2,
        cfl: float = 0.6,
        sponge_width: int = 0,
        sponge_sides: Side | Iterable[Side] | None = None,
        sponge_reflection: float = 1e-4,
        damping: float | NDArray[np.float64] = 0.0,
        shape: tuple[int, int] | None = None,
        edge_impedance: Mapping[Side, float | NDArray[np.float64]] | None = None,
        obstacle_mask: NDArray[np.bool_] | None = None,
        compute: Compute | None = None,
    ) -> None:
        c_map, self.dx, self.dt = _acoustic_grid(c, shape, cfl, dx)
        ny, nx = c_map.shape
        rho_map = _resolve_rho_map(rho, ny, nx)
        sponge_width, damping_map = _validate_sponge_damping(
            sponge_width, sponge_reflection, damping, ny, nx
        )
        sides = _resolve_sponge_sides(sponge_sides)
        #: Sponge-layer width in cells (read-only configuration record).
        self.sponge_width = require_count(sponge_width, "sponge_width", at_least=None)
        #: Sides carrying a sponge layer when ``sponge_width > 0``.
        self.sponge_sides: tuple[str, ...] = sides if sponge_width > 0 else ()
        impedances = _validated_impedances(edge_impedance, self.sponge_sides, ny, nx)
        self._obstacle: NDArray[np.bool_] | None = _validated_obstacle(
            obstacle_mask, ny, nx
        )

        # Every argument is checked on the host before the device is asked
        # for, so a bad one raises its own error, never a missing library's
        # or a fallback warning first.
        backend = _backends.backend_for(compute)
        self._backend = backend
        self._xp = backend.xp
        # The medium the simulation was built on, as read-only copies of its
        # own: an edit to the caller's maps cannot make them disagree with
        # dt and kappa, which were computed from them here.
        self.c = read_only_copy(c_map)
        self.rho = read_only_copy(rho_map)
        c_max = float(c_map.max())
        #: Mean sound speed, cached for the plane-wave machinery.
        self._c_ref = float(c_map.mean())
        #: Bulk modulus at the cell centres [Pa], a read-only host copy.
        self.kappa = read_only_copy(rho_map * c_map**2)
        self._kappa = backend.asarray(self.kappa)
        # Density averaged onto the faces where each velocity lives, kept on
        # the host for the plane-wave initial condition and on the device
        # for the step.
        rho_x = 0.5 * (rho_map[:, 1:] + rho_map[:, :-1])
        rho_y = 0.5 * (rho_map[1:, :] + rho_map[:-1, :])
        self._rho_x_host, self._rho_y_host = rho_x, rho_y
        self._rho_x = backend.asarray(rho_x)
        self._rho_y = backend.asarray(rho_y)

        self.p = backend.zeros((ny, nx))
        self.vx = backend.zeros((ny, nx - 1))
        self.vy = backend.zeros((ny - 1, nx))
        self._div = backend.zeros((ny, nx))
        self._sources: list[Source] = []
        self._plane_sources: list[PlaneWaveSource] = []
        self._contour_probes: list[ContourProbe] = []
        self.n = 0  # completed steps

        self._init_decay(sides, sponge_width, sponge_reflection, damping_map, c_max)
        rho_edges = {
            "left": self.rho[:, 0],
            "right": self.rho[:, -1],
            "top": self.rho[0, :],
            "bottom": self.rho[-1, :],
        }
        self._edges = [
            _ImpedanceEdge(side, z, rho_edges[side], self.dt, self.dx, backend)
            for side, z in impedances
        ]
        #: Per-side impedance boundaries as supplied (immutable record), read
        #: once the edges have validated them; an array profile is kept as a
        #: read-only copy of its own.
        self.edge_impedance: Mapping[str, float | NDArray[np.float64]] = (
            MappingProxyType(
                {
                    side: float(value)
                    if np.ndim(value) == 0
                    else read_only_copy(value, np.float64)
                    for side, value in (edge_impedance or {}).items()
                }
            )
        )
        self._init_obstacle()

    def _init_decay(
        self,
        sides: tuple[str, ...],
        sponge_width: int,
        sponge_reflection: float,
        damping: NDArray[np.float64],
        c_max: float,
    ) -> None:
        """Precompute the sponge/damping decay factors of every field."""
        sigma = _sigma_map(
            self.p.shape,
            sides,
            sponge_width,
            sponge_reflection,
            damping,
            c_max,
            self.dx,
        )
        backend = self._backend
        self._decay_p = backend.asarray(np.exp(-sigma * self.dt))
        self._decay_vx = backend.asarray(
            np.exp(-(0.5 * (sigma[:, 1:] + sigma[:, :-1])) * self.dt)
        )
        self._decay_vy = backend.asarray(
            np.exp(-(0.5 * (sigma[1:, :] + sigma[:-1, :])) * self.dt)
        )

    def _init_obstacle(self) -> None:
        """Turn the validated obstacle mask into closed-face velocity factors on the device."""
        self._vx_open: _backends.DeviceArray | None = None
        self._vy_open: _backends.DeviceArray | None = None
        if self._obstacle is not None:
            mask = self._obstacle
            # A face between two cells is open only when both are open
            # (rigid obstacle boundary: zero normal velocity, Eq. 4.32).
            self._vx_open = self._backend.asarray(
                (~(mask[:, 1:] | mask[:, :-1])).astype(np.float64)
            )
            self._vy_open = self._backend.asarray(
                (~(mask[1:, :] | mask[:-1, :])).astype(np.float64)
            )

    @property
    def time(self) -> float:
        """Elapsed simulated time [s]."""
        return self.n * self.dt

    def add_plane_wave(
        self,
        direction: Literal["down", "up", "left", "right"],
        *,
        center: float,
        width: float,
        amplitude: float = 1.0,
        wavelength: float | None = None,
    ) -> None:
        """Superimpose a one-way plane wave packet as an initial condition.

        A Gaussian envelope (optionally carrying a sine at ``wavelength``)
        is written onto the pressure field, and the leapfrog-consistent
        particle velocity is written a half time step back, so the packet
        propagates only toward ``direction`` (the axes of
        :meth:`plot_geometry`: ``"down"``/``"up"`` along y,
        ``"right"``/``"left"`` along x). The packet is uniform across the
        transverse direction and adds to whatever fields are present.

        Obstacles are not carved out of the initial condition: place the
        packet in free field (its envelope clear of ``obstacle_mask``
        cells), as a physical incident wave would be.

        :param direction: Travel direction, one of ``"down"``, ``"up"``,
            ``"left"``, ``"right"``.
        :param center: Envelope centre along the travel axis, in metres.
        :param width: Gaussian envelope width (the ``1/e`` half-width), in
            metres.
        :param amplitude: Peak pressure of the envelope, in pascals.
        :param wavelength: Optional carrier wavelength, in metres; ``None``
            gives the pure Gaussian pulse.
        :raises ValueError: For an unknown direction, a non-positive or
            non-finite ``width``/``wavelength``, or a non-finite
            ``center``/``amplitude``.
        :raises TypeError: if ``amplitude``, ``center``, ``wavelength`` or ``width`` is
            not a single number.
        """
        if direction not in _SIDE_TRAVEL:
            msg = "'direction' must be 'down', 'up', 'left' or 'right'."
            raise ValueError(msg)
        width = require_positive(width, "width")
        if wavelength is not None:
            wavelength = require_positive(wavelength, "wavelength")
        center = _finite("center", center)
        amplitude = _finite("amplitude", amplitude)

        def profile(coord: NDArray[np.floating]) -> NDArray[np.float64]:
            envelope = amplitude * np.exp(-(((coord - center) / width) ** 2))
            if wavelength is not None:
                envelope = envelope * np.sin(
                    2.0 * np.pi * (coord - center) / wavelength
                )
            return np.asarray(envelope, dtype=np.float64)

        ny, nx = self.p.shape
        axis_y = direction in ("down", "up")
        sign = 1.0 if direction in ("down", "right") else -1.0
        c_ref = self._c_ref
        # The increments are built on the host in float64, as the maps are,
        # and each goes to the device once.
        if axis_y:
            centres = (np.arange(ny) + 0.5) * self.dx
            faces = np.arange(1, ny) * self.dx
            dp = profile(centres)[:, np.newaxis]
            # v = sign * p / (rho c) for travel along +/- y, sampled on the
            # faces a half time step earlier: g(y -/+ c t) at t = -dt/2.
            v_prof = profile(faces + sign * 0.5 * c_ref * self.dt)
            dv = sign * v_prof[:, np.newaxis] / (self._rho_y_host * c_ref)
        else:
            centres = (np.arange(nx) + 0.5) * self.dx
            faces = np.arange(1, nx) * self.dx
            dp = profile(centres)[np.newaxis, :]
            v_prof = profile(faces + sign * 0.5 * c_ref * self.dt)
            dv = sign * v_prof[np.newaxis, :] / (self._rho_x_host * c_ref)
        backend = self._backend
        with backend.context():
            self.p += backend.asarray(dp)
            if axis_y:
                self.vy += backend.asarray(dv)
            else:
                self.vx += backend.asarray(dv)

    def plot_geometry(
        self,
        ax: Axes | None = None,
        *,
        probes: ArrayLike | None = None,
        language: Language = "en",
        **kwargs: Any,
    ) -> Axes:
        """Draw the configured domain before running it.

        Domain extent, obstacles, sponge layers, impedance and rigid edges
        and the added sources, with optional probe positions previewed; no
        time stepping happens. Requires matplotlib
        (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param probes: Optional probe positions ``(x, y)`` in metres, shape
            ``(N, 2)`` (the :func:`fdtd_simulation` convention).
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the obstacle ``imshow``.
        """
        from .._i18n import check_language
        from .._plot.geometry import plot_fdtd_domain

        check_language(language)
        return plot_fdtd_domain(self, ax=ax, probes=probes, language=language, **kwargs)

    def add_source(self, source: AnySource) -> None:
        """Register a source: a point injection or a plane-wave line.

        Point sources (:class:`GaussianPulse`, :class:`CWSource`,
        :class:`SignalSource`) inject additively at one cell. A
        :class:`PlaneWaveSource` injects a sustained one-way plane wave on
        a full line of cells near its launch edge.
        """
        _check_source(source, self.c.shape, self._obstacle)
        if isinstance(source, PlaneWaveSource):
            self._plane_sources.append(source)
        else:
            self._sources.append(source)

    def add_contour_probe(
        self, ix0: int, ix1: int, iy0: int, iy1: int, *, frequencies: ArrayLike
    ) -> ContourProbe:
        r"""Record ``p`` and ``v_n`` phasors on a closed rectangular contour.

        The contour is the rectangle of cell faces enclosing the cell
        block ``ix0..ix1`` x ``iy0..iy1`` (both ends inclusive): its sides
        lie on :math:`x = i_{x0}\,\Delta x`, :math:`x = (i_{x1}+1)\,\Delta x`,
        :math:`y = i_{y0}\,\Delta x` and :math:`y = (i_{y1}+1)\,\Delta x`. From
        the step after registration the engine
        folds the face pressures (averaged from the two adjacent cell
        centres) and the outward face normal velocities into running DFT
        sums at each requested frequency; see :class:`ContourProbe`
        for the steady-state protocol and
        :func:`~phonometry.simulation.ntff.far_field_from_contour` for the
        far-field transformation of the captured phasors.

        Place the contour in open air: strictly around the scatterer,
        clear of sponge layers and of any source (point sources and
        plane-wave injection lines must stay outside so the enclosed
        region is source-free in a scattering run, or inside when the
        radiated field itself is the quantity of interest).

        :param ix0: First cell column inside the contour.
        :param ix1: Last cell column inside the contour.
        :param iy0: First cell row inside the contour.
        :param iy1: Last cell row inside the contour.
        :param frequencies: Frequencies to track [Hz].
        :return: The registered :class:`ContourProbe`.
        :raises ValueError: For a block without open faces on all sides or
            invalid frequencies.
        """
        probe = ContourProbe(self, ix0, ix1, iy0, iy1, frequencies)
        self._contour_probes.append(probe)
        return probe

    def step(self) -> None:
        """Advance the leapfrog scheme by one time step."""
        with self._backend.context():
            self._step()

    def _step(self) -> None:
        """One leapfrog step on the backend's arrays."""
        dt_dx = self.dt / self.dx
        # Velocity half-step from the pressure gradient (rigid walls are the
        # implicit zero normal velocity at the domain edge).
        self.vx -= dt_dx / self._rho_x * (self.p[:, 1:] - self.p[:, :-1])
        self.vy -= dt_dx / self._rho_y * (self.p[1:, :] - self.p[:-1, :])
        if self._vx_open is not None and self._vy_open is not None:
            self.vx *= self._vx_open
            self.vy *= self._vy_open
        self.vx *= self._decay_vx
        self.vy *= self._decay_vy
        for edge in self._edges:
            edge.update(self.p)
        # Pressure step from the velocity divergence (reused buffer).
        div = self._div
        div[...] = 0.0
        div[:, :-1] += self.vx
        div[:, 1:] -= self.vx
        div[:-1, :] += self.vy
        div[1:, :] -= self.vy
        for edge in self._edges:
            edge.add_flux(div)
        self.p -= self._kappa * dt_dx * div
        t_next = (self.n + 1) * self.dt
        for src in self._sources:
            self.p[src.iy, src.ix] += src.value(t_next)
        for plane in self._plane_sources:
            self._inject_plane(plane, t_next)
        self.p *= self._decay_p
        self.n += 1
        for probe in self._contour_probes:
            probe._accumulate(self.p, self.vx, self.vy, self.n)

    def _inject_plane(self, plane: PlaneWaveSource, t_next: float) -> None:
        r"""Add the incident plane wave on the injection line (one-way).

        Simultaneous pressure and adjacent-face velocity increments carry
        the incident wave into the domain only along the travel direction;
        the increments are the discrete equivalent of superimposing
        :math:`p = s(t - d/c)` entering through the line each step.
        """
        c_ref = self._c_ref
        gain = plane.amplitude * self.dt / (self.dx / c_ref)
        value_p = plane.waveform(t_next)
        value_v = plane.waveform(t_next - 0.5 * self.dt + 0.5 * self.dx / c_ref)
        direction = plane.direction
        k = plane.offset
        if direction == "down":
            self.p[k, :] += gain * value_p
            self.vy[k, :] += gain * value_v / (self._rho_y[k, :] * c_ref)
        elif direction == "up":
            row = self.p.shape[0] - 1 - k
            self.p[row, :] += gain * value_p
            self.vy[row - 1, :] -= gain * value_v / (self._rho_y[row - 1, :] * c_ref)
        elif direction == "right":
            self.p[:, k] += gain * value_p
            self.vx[:, k] += gain * value_v / (self._rho_x[:, k] * c_ref)
        else:
            col = self.p.shape[1] - 1 - k
            self.p[:, col] += gain * value_p
            self.vx[:, col - 1] -= gain * value_v / (self._rho_x[:, col - 1] * c_ref)

    def energy(self) -> float:
        """Total acoustic field energy [J per metre of depth]."""
        xp, b = self._xp, self._backend
        with b.context():
            e_p = b.scalar(xp.sum(self.p**2 / (2.0 * self._kappa)))
            e_v = 0.5 * (
                b.scalar(xp.sum(self._rho_x * self.vx**2))
                + b.scalar(xp.sum(self._rho_y * self.vy**2))
            )
        return (e_p + e_v) * self.dx**2

    def run(
        self,
        n_steps: int,
        snapshot_every: int | None = None,
        snapshot_decimation: int = 1,
    ) -> NDArray[np.floating]:
        """Advance ``n_steps`` steps, optionally recording pressure frames.

        With ``snapshot_every = k`` a host copy of ``p`` is stored after
        every ``k``-th step (and one of the initial state), keeping every
        ``snapshot_decimation``-th cell along each axis; the stacked
        ``(n_frames, ny', nx')`` array plugs straight into a ``FuncAnimation``
        ``imshow`` update. Without ``snapshot_every`` an empty array is
        returned and only the final state is kept (read it with
        :meth:`host_field`).

        :raises TypeError: if ``snapshot_decimation``, ``n_steps`` or
            ``snapshot_every`` is a flag, a text or an array where a count goes.
        :raises ValueError: if ``n_steps`` is not a whole number of 0 or more,
            or ``snapshot_every`` or ``snapshot_decimation`` is not a whole
            number of 1 or more.
        """
        return _run_recording(self, n_steps, snapshot_every, snapshot_decimation)

    #: The arrays the engine stores, the names :meth:`host_field` reads.
    _STORED: tuple[Literal["p", "vx", "vy"], ...] = ("p", "vx", "vy")

    def host_field(self, name: Literal["p", "vx", "vy"]) -> NDArray[np.floating]:
        """A NumPy copy of the stored field *name*, whatever the device.

        :param name: ``"p"`` (cell centres), ``"vx"`` or ``"vy"`` (faces).
        :raises TypeError: if ``name`` is not a text.
        :raises ValueError: for a field the engine does not store.
        """
        require_choice(name, "name", self._STORED)
        return np.array(self._backend.to_host(getattr(self, name)), copy=True)

    @property
    def provenance(self) -> RunProvenance:
        """Where this engine steps: device, dtype and library versions."""
        return self._backend.provenance


def _require_grid_axes(
    owner: str,
    shape: tuple[int, int],
    snapshots: NDArray[np.floating] | None,
    obstacle_mask: NDArray[np.bool_] | None,
    snapshot_decimation: int,
) -> int:
    """Require every whole-domain raster to cover the grid ``shape`` names.

    Shared by the acoustic and the elastic result, which record different
    fields over the same domain and hand them to the same snapshot renderer.
    That renderer takes the physical extent of the picture from ``shape``
    alone and draws the obstacle map on top of it as a second image over the
    same extent, so a raster recorded on a different grid is stretched to fit
    a domain it never covered, with the geometry landing on cells that were
    never simulated. Neither imshow nor the eye objects: the frame is a
    perfectly ordinary field plot of the wrong thing.

    A snapshot keeps every ``snapshot_decimation``-th cell along each axis,
    starting with the first, so its axes are ``ceil(ny / d)`` by
    ``ceil(nx / d)``.

    :param owner: Name of the result type being checked, for the message.
    :param shape: The grid the run covered, ``(ny, nx)``.
    :param snapshots: Recorded frames, ``(n_frames, ceil(ny / d),
        ceil(nx / d))``, or ``None``.
    :param obstacle_mask: Rigid-cell map, ``(ny, nx)``, or ``None``.
    :param snapshot_decimation: The ``d`` the snapshots were taken with.
    :return: ``snapshot_decimation`` as an ``int``, for the result to hold.
    :raises TypeError: if ``snapshot_decimation`` is not a number.
    :raises ValueError: if a raster disagrees with ``shape``, or
        ``snapshot_decimation`` is not a whole number of 1 or more.
    """
    d = require_count(snapshot_decimation, "snapshot_decimation")
    ny, nx = shape
    rows = {"shape (rows)": ny}
    columns = {"shape (columns)": nx}
    if obstacle_mask is not None:
        rows["obstacle_mask"] = obstacle_mask.shape[0]
        columns["obstacle_mask (axis 1)"] = obstacle_mask.shape[1]
    require_equal_counts(owner, rows, "grid row")
    require_equal_counts(owner, columns, "grid column")
    if snapshots is not None:
        # Ceiling division: the decimated grid keeps the first cell of every block.
        require_equal_counts(
            owner,
            {"decimated rows": -(-ny // d), "snapshots (axis 1)": snapshots.shape[1]},
            "decimated grid row",
        )
        require_equal_counts(
            owner,
            {
                "decimated columns": -(-nx // d),
                "snapshots (axis 2)": snapshots.shape[2],
            },
            "decimated grid column",
        )
    return d


def _require_provenance(owner: str, provenance: object) -> None:
    """Refuse a result's ``provenance`` that is not a :class:`RunProvenance`.

    ``None`` included: a result that cannot say where it stepped could pass
    for a run on any device.

    :param owner: The result's class name, which the message names.
    :raises TypeError: for anything but a :class:`RunProvenance`.
    """
    if not isinstance(provenance, RunProvenance):
        msg = (
            f"{owner}: 'provenance' must be a RunProvenance, got "
            f"{type(provenance).__name__}."
        )
        raise TypeError(msg)


@dataclass(frozen=True)
class FDTDResult(OwnsArrays):
    r"""Frozen result of a :func:`fdtd_simulation` run.

    :ivar times: Time axis [s], length ``n_steps + 1`` (includes
        :math:`t = 0`).
    :ivar pressures: Pressure history at each probe [Pa], shape
        ``(n_probes, n_steps + 1)``.
    :ivar probes: Probe cell indices ``(ix, iy)``, shape ``(n_probes, 2)``.
    :ivar probe_positions: Probe cell-centre positions ``(x, y)`` [m], shape
        ``(n_probes, 2)``.
    :ivar dx: Grid spacing [m].
    :ivar dt: Time step [s].
    :ivar shape: Grid shape ``(ny, nx)``.
    :ivar sources: The source definitions of the run.
    :ivar snapshots: Recorded pressure fields, shape ``(n_frames,
        ceil(ny / d), ceil(nx / d))`` with ``d`` the ``snapshot_decimation``,
        in the dtype the run stepped in, or ``None`` when no snapshots were
        requested.
    :ivar snapshot_times: Time of each snapshot [s], or ``None``.
    :ivar obstacle_mask: Boolean map of rigid cells, or ``None``.
    :ivar snapshot_decimation: Every how many cells a snapshot keeps along
        each axis (1 keeps every cell).
    :ivar provenance: Where the run stepped (:class:`RunProvenance`).
    """

    times: NDArray[np.float64]
    pressures: NDArray[np.float64]
    probes: NDArray[np.int_]
    probe_positions: NDArray[np.float64]
    dx: float
    dt: float
    shape: tuple[int, int]
    sources: tuple[AnySource, ...]
    snapshots: NDArray[np.floating] | None
    snapshot_times: NDArray[np.float64] | None
    obstacle_mask: NDArray[np.bool_] | None
    snapshot_decimation: int
    provenance: RunProvenance

    def __post_init__(self) -> None:
        """Reject a run whose probes, time axis and grid do not line up.

        Every reader of a run is a picture, and neither picture can defend
        itself. The probe plot pairs each row of ``pressures`` with the label
        built from the matching row of ``probe_positions``, so a positions
        array of another length surfaces only at drawing time, as a zip that
        reports two lengths and names neither array, an entire run after the
        mistake was made. The snapshot plot does not surface it at all: it
        stamps the frame across an extent taken from ``shape``, which turns a
        frame recorded on a different grid into a plausible field over a
        domain it never covered.

        :raises TypeError: if ``snapshot_decimation`` is not a number, or
            ``provenance`` is not a :class:`RunProvenance`.
        :raises ValueError: if the probe, time-step, snapshot or grid axes
            disagree, or ``snapshot_decimation`` is not a whole number of 1
            or more.
        """
        _require_provenance(type(self).__name__, self.provenance)
        require_ranks(
            self,
            times=1,
            pressures=2,
            probes=2,
            probe_positions=2,
            snapshots=3,
            snapshot_times=1,
            obstacle_mask=2,
        )
        require_same_length(
            self, "pressures", "probes", "probe_positions", axis="probe"
        )
        require_same_length(
            self, ("probes", 1), ("probe_positions", 1), axis="coordinate"
        )
        require_same_length(self, "times", ("pressures", 1), axis="time step")
        require_same_length(self, "snapshots", "snapshot_times", axis="snapshot")
        decimation = _require_grid_axes(
            type(self).__name__,
            self.shape,
            self.snapshots,
            self.obstacle_mask,
            self.snapshot_decimation,
        )
        # Held as an int, so a whole float or a NumPy integer reads back as
        # the plain step a slice and the snapshot renderer take.
        object.__setattr__(self, "snapshot_decimation", decimation)

    @property
    def size(self) -> tuple[float, float]:
        """Domain size ``(lx, ly)`` [m]."""
        ny, nx = self.shape
        return nx * self.dx, ny * self.dx

    def plot(
        self,
        ax: Axes | None = None,
        *,
        kind: Literal["probes", "snapshot"] = "probes",
        frame: int = -1,
        language: Language = "en",
        **kwargs: Any,
    ) -> Axes:
        """Plot the probe histories or one recorded field snapshot.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param kind: ``"probes"`` (default) draws the per-probe pressure
            time histories; ``"snapshot"`` renders one recorded pressure
            field with the geometry overlaid (``imshow`` raster).
        :param frame: Snapshot index for ``kind="snapshot"`` (default: the
            last recorded frame).
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the underlying ``plot``/``imshow``.
        :return: The axes.
        """
        from .._i18n import check_language

        check_language(language)
        if kind == "probes":
            from .._plot.simulation import plot_fdtd_probes

            return plot_fdtd_probes(self, ax=ax, language=language, **kwargs)
        if kind == "snapshot":
            from .._plot.simulation import plot_fdtd_snapshot

            return plot_fdtd_snapshot(
                self, ax=ax, frame=frame, language=language, **kwargs
            )
        msg = "kind must be 'probes' or 'snapshot'"
        raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class FDTDRecording(RichDisplay):
    """What an acoustic run writes down: probe histories and field snapshots.

    The two ways out of a running simulation. Probes record the pressure
    history at named cells; snapshots record the whole pressure field every
    ``snapshot_every`` steps. Recording nothing (the default) runs the
    physics and keeps only the time axis.

    :param probes: Pressure-probe cells as ``(ix, iy)`` index pairs.
    :param snapshot_every: Record a full pressure-field snapshot every this
        many steps (and at :math:`t = 0`); ``None`` records none.
    :param snapshot_decimation: Keep every this many cells along each axis
        in a snapshot (default 1, every cell); the result records it.
    :raises TypeError: for a probe that is not a pair or has an index that is
        not a number, a ``snapshot_every`` that is a flag, a text, an array or
        anything else that is neither a number nor ``None``, or a
        ``snapshot_decimation`` that is a flag, a text, an array or anything
        else that is not a number.
    :raises ValueError: for a probe of more or fewer than two indices or with
        an index that is not a whole number, or a ``snapshot_every`` or
        ``snapshot_decimation`` that is not a whole number of 1 or more.
    """

    probes: Sequence[tuple[int, int]] = ()
    snapshot_every: int | None = None
    snapshot_decimation: int = 1

    def __post_init__(self) -> None:
        """Refuse a malformed probe or count when the record is built.

        Whether a probe lies on the grid, and outside the obstacle, is checked
        by :func:`fdtd_simulation`, the first place a grid exists.
        """
        every, decimation = _snapshot_options(
            self.snapshot_every, self.snapshot_decimation
        )
        # Held as a tuple of int pairs and plain ints, so a list handed in
        # cannot change the record after it is built, and a whole float or a
        # NumPy integer reads back as the count a slice takes.
        object.__setattr__(self, "probes", _probe_pairs(self.probes))
        object.__setattr__(self, "snapshot_every", every)
        object.__setattr__(self, "snapshot_decimation", decimation)


def _parse_boundaries(
    boundaries: AcousticBoundary
    | Mapping[Side, AcousticBoundary | float | NDArray[np.float64]],
) -> tuple[tuple[Side, ...], dict[Side, float | NDArray[np.float64]]]:
    """Split the boundary spec into sponge sides and impedance sides."""
    spec: dict[Side, str | float | NDArray[np.float64]]
    if isinstance(boundaries, str):
        spec = dict.fromkeys(_SIDES, boundaries)
    else:
        unknown = set(boundaries) - set(_SIDES)
        if unknown:
            msg = f"unknown boundary sides: {sorted(unknown)}"
            raise ValueError(msg)
        spec = {side: boundaries.get(side, "rigid") for side in _SIDES}
    absorbing: list[Side] = []
    impedance: dict[Side, float | NDArray[np.float64]] = {}
    for side in _SIDES:
        value = spec[side]
        if isinstance(value, str):
            if value not in _BOUNDARY_NAMES:
                msg = (
                    f"boundary for side {side!r} must be one of "
                    f"{_BOUNDARY_NAMES} or a real impedance, got {value!r}"
                )
                raise ValueError(msg)
            if value == "absorbing":
                absorbing.append(side)
        else:
            impedance[side] = value
    return tuple(absorbing), impedance


def _probe_pairs(probes: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """The probe cells as whole ``(ix, iy)`` pairs, read before any grid exists.

    :class:`FDTDRecording` reads them here when it is built, and
    :func:`_probe_indices` when a run checks them against its grid, so a
    malformed probe is refused with the same class and the same words on
    every route.

    :raises TypeError: for an entry that is not a pair, or an index that is
        not a number.
    :raises ValueError: for an entry of more or fewer than two indices, or an
        index that is not a whole number.
    """
    pairs: list[tuple[int, int]] = []
    for k, entry in enumerate(probes):
        try:
            ix, iy = entry
        except TypeError:
            msg = f"probes must hold (ix, iy) index pairs; entry {k} is {entry!r}"
            raise TypeError(msg) from None
        except ValueError:
            msg = f"probes must hold (ix, iy) index pairs; entry {k} is {entry!r}"
            raise ValueError(msg) from None
        pairs.append((_integer("probe ix", ix), _integer("probe iy", iy)))
    return tuple(pairs)


def _probe_indices(
    probes: Iterable[tuple[int, int]],
    shape: tuple[int, int],
    obstacle: NDArray[np.bool_] | None,
) -> NDArray[np.int_]:
    """Validate the probe cells into an ``(n_probes, 2)`` index array."""
    ny, nx = shape
    pairs = _probe_pairs(probes)
    probe_ix = np.zeros((len(pairs), 2), dtype=np.int_)
    for k, (ix, iy) in enumerate(pairs):
        if not (0 <= ix < nx and 0 <= iy < ny):
            msg = f"probe ({ix}, {iy}) lies outside the grid"
            raise ValueError(msg)
        if obstacle is not None and obstacle[iy, ix]:
            msg = f"probe ({ix}, {iy}) lies inside an obstacle"
            raise ValueError(msg)
        probe_ix[k] = (ix, iy)
    return probe_ix


def _recording_or_empty[R: RichDisplay](recording: object, record: type[R]) -> R:
    """A simulation function's ``recording``, or an empty *record* for ``None``.

    Shared by :func:`fdtd_simulation` and :func:`elastic_fdtd_simulation`, so
    each takes its own record and nothing else, the other engine's included:
    the elastic record has the acoustic one's fields, and would otherwise run
    with its probe fields and snapshot field silently ignored.

    :raises TypeError: for anything but ``None`` or a *record*.
    """
    if recording is None:
        return record()
    if not isinstance(recording, record):
        msg = (
            f"'recording' must be an {record.__name__} or None, got "
            f"{type(recording).__name__}."
        )
        raise TypeError(msg)
    return recording


def _record_run(
    sim: FDTD2D,
    steps: int,
    probe_ix: NDArray[np.int_],
    snapshot_every: int | None,
    snapshot_decimation: int,
    pressures: NDArray[np.float64],
    snapshots: NDArray[np.floating] | None,
) -> None:
    """Step the engine, writing probe histories and field snapshots in place.

    ``pressures`` takes one column per step after the first; ``snapshots``
    takes the initial field and then one frame every ``snapshot_every``
    steps, so it has ``steps // snapshot_every + 1`` of them. Both are
    allocated by the caller before the march, so that the run is never held
    twice, as a list of frames and their stack.

    The probes are read through one flat index per cell, ``row * nx +
    column``, since the Array API standard indexes one axis with an integer
    array, not two at once. On NumPy the samples are written straight into
    ``pressures``; on a device they go into a buffer there, which comes to
    the host once, after the march. Each snapshot is cut to every
    ``snapshot_decimation``-th cell on the device and comes to the host as
    it is taken, so only the cells it keeps cross.
    """
    b, xp = sim._backend, sim._xp
    d = snapshot_decimation
    if snapshots is not None:
        snapshots[0] = b.to_host(sim.p[::d, ::d])
    n_probes = probe_ix.shape[0]
    nx = sim.p.shape[1]
    centre = b.index(probe_ix[:, 1] * nx + probe_ix[:, 0])
    buffer = None if b.name == "numpy" else b.zeros((n_probes, steps + 1))
    with b.context():
        for i in range(steps):
            sim.step()
            if n_probes:
                sample = xp.take(xp.reshape(sim.p, (-1,)), centre)
                if buffer is None:
                    pressures[:, i + 1] = sample
                else:
                    buffer[:, i + 1] = sample
            if (
                snapshots is not None
                and snapshot_every is not None
                and (i + 1) % snapshot_every == 0
            ):
                snapshots[(i + 1) // snapshot_every] = b.to_host(sim.p[::d, ::d])
    if buffer is not None:
        pressures[...] = b.to_host(buffer)


def fdtd_simulation(
    c: float | Field2D,
    dx: float,
    duration: float,
    *,
    sources: Sequence[AnySource],
    shape: tuple[int, int] | None = None,
    rho: float | Field2D = 1.2,
    cfl: float = 0.6,
    recording: FDTDRecording | None = None,
    boundaries: AcousticBoundary
    | Mapping[Side, AcousticBoundary | float | NDArray[np.float64]] = "rigid",
    absorbing_layer_cells: int = 20,
    obstacle_mask: NDArray[np.bool_] | None = None,
    damping: float = 0.0,
    compute: Compute | None = None,
) -> FDTDResult:
    r"""Run a deterministic 2D acoustic FDTD simulation.

    Builds the staggered-grid domain (Attenborough & Van Renterghem 2021,
    Eqs. 4.11-4.12), applies the requested boundary conditions, injects the
    sources and integrates for ``duration`` seconds, recording the pressure
    at every probe each time step and, optionally, full-field snapshots.

    The grid covers ``(nx * dx, ny * dx)`` metres; a cell index ``(ix, iy)``
    maps to the physical cell centre ``((ix + 0.5) * dx, (iy + 0.5) * dx)``.
    Resolve at least 10 cells per shortest wavelength using the smallest
    sound speed of the domain (:math:`\Delta x \le c_{\min} / (10 f)`), the
    usual rule for
    this lowest-order scheme: the worst-case (on-axis) numerical dispersion
    error magnitude, :math:`(k \Delta x)^2 / 24` from the discrete counterpart
    of
    Eq. 4.15 (the modelled frequency under-reads, so the signed error is
    negative), is then about 1.6 % (about 1.4 % at the default ``cfl``;
    in a heterogeneous domain the slower cells run at a lower local Courant
    number and sit nearer the 1.6 % bound) and finer grids reduce it
    quadratically. The
    simulation is 2D, so a point source is
    physically a line source with cylindrical :math:`1/\sqrt{r}` amplitude
    spreading rather than the 3D spherical :math:`1/r`.

    :param c: Sound-speed map [m/s], shape ``(ny, nx)``, or a scalar with an
        explicit ``shape``.
    :param dx: Grid spacing [m] (square cells).
    :param duration: Physical time to simulate [s].
    :param sources: One or more of :class:`GaussianPulse`,
        :class:`CWSource`, :class:`SignalSource` or :class:`PlaneWaveSource`.
    :param shape: Grid shape ``(ny, nx)``, required when ``c`` is a scalar.
    :param rho: Density map [kg/m3]; scalar or ``(ny, nx)`` array.
    :param cfl: Courant number in ``(0, 1)`` (Eqs. 4.13-4.14); the time step
        is :math:`\Delta t = C_\mathrm{N}\, \Delta x / (c_{\max} \sqrt{2})`.
        Default 0.6.
    :param recording: What the run records (:class:`FDTDRecording`): the
        probe cells, and the snapshot cadence and decimation. ``None``
        records nothing but the time axis.
    :param boundaries: ``"rigid"`` (default), ``"absorbing"``, or a mapping
        from side name (``left``/``right``/``top``/``bottom``) to
        ``"rigid"``, ``"absorbing"``, or a real specific impedance
        [Pa s/m] (scalar or per-edge-cell 1D array, Eqs. 4.33-4.35).
    :param absorbing_layer_cells: Sponge-layer thickness for absorbing
        sides, in cells.
    :param obstacle_mask: Boolean map, shape ``(ny, nx)``, of rigid cells
        (rasterised interior geometry).
    :param damping: Uniform bulk amplitude decay rate [1/s].
    :param compute: Where the run steps (:class:`Compute`); ``None`` follows
        :func:`use`, then ``PHONOMETRY_COMPUTE``, then NumPy.
    :return: A :class:`FDTDResult`.
    :raises TypeError: If an input is of the wrong type: a ``duration``,
        ``cfl`` or ``dx`` that is not one number, a ``recording`` that is
        neither an :class:`FDTDRecording` nor ``None``, an
        ``absorbing_layer_cells`` that is not a number, a ``shape`` that is
        not a pair, a complex medium, an ``obstacle_mask`` that is not
        boolean, or a ``compute`` that is neither a :class:`Compute` nor
        ``None``.
    :raises ValueError: If the inputs are invalid.
    :raises ComputeImportError: When the device's library is not installed
        or does not import.
    :raises ComputeDeviceError: When the device is not present, or fails a
        first small computation; with ``fallback=True`` the run warns with
        :class:`ComputeFallbackWarning` and steps on NumPy instead.
    """
    recording = _recording_or_empty(recording, FDTDRecording)
    snapshot_every, d = recording.snapshot_every, recording.snapshot_decimation
    require_scalar(absorbing_layer_cells, "absorbing_layer_cells")
    if len(sources) == 0:
        msg = "at least one source is required"
        raise ValueError(msg)
    duration = _positive_finite("duration", duration)
    absorbing_sides, edge_impedance = _parse_boundaries(boundaries)
    if absorbing_sides:
        absorbing_layer_cells = _integer("absorbing_layer_cells", absorbing_layer_cells)
        if absorbing_layer_cells < 1:
            msg = "absorbing_layer_cells must be >= 1"
            raise ValueError(msg)

    # The grid, the obstacle, the sources, the probes and the step count are
    # checked on the host first, through the helpers the engine uses, so a
    # bad one raises its own error before the engine asks for its device.
    c_map, _, dt = _acoustic_grid(c, shape, cfl, dx)
    ny, nx = c_map.shape
    obstacle = _validated_obstacle(obstacle_mask, ny, nx)
    for source in sources:
        _check_source(source, (ny, nx), obstacle)
    probe_ix = _probe_indices(recording.probes, (ny, nx), obstacle)
    steps = _step_count(duration, dt)

    sim = FDTD2D(
        c,
        dx,
        rho=rho,
        cfl=cfl,
        sponge_width=absorbing_layer_cells if absorbing_sides else 0,
        sponge_sides=absorbing_sides or None,
        damping=damping,
        shape=shape,
        edge_impedance=edge_impedance or None,
        obstacle_mask=obstacle_mask,
        compute=compute,
    )
    for source in sources:
        sim.add_source(source)
    times = np.arange(steps + 1, dtype=np.float64) * sim.dt
    # The record keeps these two as they are (handed_over): the snapshots are
    # most of the result, and a copy would hold them twice while it is built.
    # The probe histories are float64 whatever the run's dtype; the snapshots
    # keep it, a float32 run's being half the size.
    pressures = np.zeros((probe_ix.shape[0], steps + 1), dtype=np.float64)
    snapshots = (
        None
        if snapshot_every is None
        else np.zeros(
            (steps // snapshot_every + 1, -(-ny // d), -(-nx // d)),
            dtype=sim._backend.host_dtype,
        )
    )
    _record_run(sim, steps, probe_ix, snapshot_every, d, pressures, snapshots)

    positions = (probe_ix.astype(np.float64) + 0.5) * sim.dx
    return FDTDResult(
        times=times,
        pressures=handed_over(pressures),
        probes=probe_ix,
        probe_positions=positions,
        dx=sim.dx,
        dt=sim.dt,
        shape=(ny, nx),
        sources=tuple(sources),
        snapshots=handed_over(snapshots),
        snapshot_times=(
            None
            if snapshot_every is None
            else np.arange(0, steps + 1, snapshot_every, dtype=np.float64) * sim.dt
        ),
        obstacle_mask=(sim._obstacle if sim._obstacle is not None else None),
        snapshot_decimation=d,
        provenance=sim.provenance,
    )
