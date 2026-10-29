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
entry point: it takes an :class:`FDTDRun`, the record of a simulation that
checks every argument when it is built, steps it deterministically and
returns a frozen :class:`FDTDResult` with per-probe pressure histories,
optional field snapshots and a ``.plot()`` method. :class:`FDTD2D` is the underlying
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

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from numbers import Real
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, Protocol

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .._internal.display import RichDisplay
from .._internal.frozen import (
    OwnsArrays,
    handed_over,
    read_only,
    read_only_copy,
    reduce_with_plain_rows,
)
from .._internal.validation import (
    require_choice,
    require_count,
    require_equal_counts,
    require_positive,
    require_ranks,
    require_same_length,
    require_scalar,
)
from . import _backends, _observer
from .compute import Compute, RunProvenance, _local_request, _requested
from .ntff import ContourPhasors

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable

    from matplotlib.axes import Axes

    from .._i18n import Language
    from ._remote.client import Expected

__all__ = [
    "FDTD2D",
    "CWSource",
    "ContourProbe",
    "FDTDBoundaries",
    "FDTDRecording",
    "FDTDResult",
    "FDTDRun",
    "GaussianPulse",
    "PlaneWaveSource",
    "SignalSource",
    "fdtd_simulation",
]

#: A real-valued map over the ``(ny, nx)`` grid. A map given as an array is
#: held as it was given, a float32 one included.
Field2D = NDArray[np.floating[Any]]

#: A grid shape ``(ny, nx)``: two whole numbers of cells, a NumPy integer
#: included, as any sequence of the two (a tuple, a list, an array's
#: ``shape``) or as a one-dimensional integer array of them.
GridShape = Sequence[int | np.integer[Any]] | NDArray[np.integer[Any]]

#: A side of the rectangular domain, by name.
Side = Literal["left", "right", "top", "bottom"]
#: How a side of the acoustic domain is terminated, by name.
AcousticBoundary = Literal["rigid", "absorbing"]

#: A direction a plane wave travels in, in the axes of ``FDTD2D.plot_geometry``.
Travel = Literal["down", "up", "left", "right"]

_SIDES: tuple[Side, ...] = ("left", "right", "top", "bottom")
#: Plane-wave travel directions accepted by ``FDTD2D.add_plane_wave``.
_SIDE_TRAVEL: tuple[Travel, ...] = ("down", "up", "left", "right")

#: Boundary-condition names accepted by :func:`fdtd_simulation`.
_BOUNDARY_NAMES: tuple[AcousticBoundary, ...] = ("rigid", "absorbing")

#: What a result's ``plot`` draws.
_PLOT_KINDS: tuple[Literal["probes", "snapshot"], ...] = ("probes", "snapshot")

#: The NumPy kinds of a real number an impedance may be given as: signed and
#: unsigned integers and floats, never a flag, a complex number or a text.
_REAL_KINDS = "iuf"

#: The target reflection of a sponge layer when the caller names none: the
#: default of both engines, which a run keeps.
_DEFAULT_SPONGE_REFLECTION = 1e-4


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


def _integer(name: str, value: object) -> int:
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

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            ix: int | np.integer[Any],
            iy: int | np.integer[Any],
            half_width_s: float,
            t0: float | None = None,
            amplitude: float = 1.0,
        ) -> None: ...

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

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            ix: int | np.integer[Any],
            iy: int | np.integer[Any],
            frequency: float,
            amplitude: float = 1.0,
            ramp_cycles: float = 3.0,
        ) -> None: ...

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

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            ix: int | np.integer[Any],
            iy: int | np.integer[Any],
            samples: ArrayLike,
            fs: float,
            amplitude: float = 1.0,
        ) -> None: ...

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

    direction: Travel
    waveform: Callable[[float], float]
    offset: int = 0
    amplitude: float = 1.0

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            direction: Travel,
            waveform: Callable[[float], float],
            offset: int | np.integer[Any] = 0,
            amplitude: float = 1.0,
        ) -> None: ...

    def __post_init__(self) -> None:
        """Require a known ``direction``, a callable ``waveform`` and a finite ``amplitude``.

        ``offset`` is held as the whole number of cells it names here, and
        checked against the grid in :meth:`FDTD2D.add_source`, which is the
        first place a grid exists.

        :raises TypeError: if ``direction`` is not a text, ``waveform`` is not
            callable, ``offset`` is not a number, or ``amplitude`` is not one
            number.
        :raises ValueError: if ``direction`` is not ``"down"``, ``"up"``,
            ``"left"`` or ``"right"``, ``offset`` is not whole or
            ``amplitude`` is not finite.
        """
        require_choice(self.direction, "direction", _SIDE_TRAVEL)
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
    sides: tuple[Side, ...],
    absorbing_layer_cells: int,
    absorbing_layer_reflection: float,
    damping: NDArray[np.float64],
    c_max: float,
    dx: float,
) -> Field2D:
    """Absorption-rate map sigma(x, y) [1/s]: sponge ramps plus damping."""
    ny, nx = shape
    cells = absorbing_layer_cells
    sigma_max = 0.0
    if cells > 0:
        # Quadratic-profile PML-style rate for a target reflection R:
        # exp(-2 * sigma_max * (w dx) / (3 c)) = R  (two-way transit).
        sigma_max = (
            -3.0
            * c_max
            * float(np.log(absorbing_layer_reflection))
            / (2.0 * cells * dx)
        )
    sig_x = _sponge_profile(nx, cells, ("left" in sides, "right" in sides), sigma_max)
    sig_y = _sponge_profile(ny, cells, ("top" in sides, "bottom" in sides), sigma_max)
    return sig_x[np.newaxis, :] + sig_y[:, np.newaxis] + damping


def _validate_sponge_damping(
    absorbing_layer_cells: int | np.integer[Any],
    absorbing_layer_reflection: float,
    damping: ArrayLike,
    ny: int,
    nx: int,
) -> tuple[int, NDArray[np.float64]]:
    """Validate the sponge/damping spec into ``(cells, damping map)``."""
    require_scalar(absorbing_layer_reflection, "absorbing_layer_reflection")
    require_scalar(absorbing_layer_cells, "absorbing_layer_cells")
    cells = _integer("absorbing_layer_cells", absorbing_layer_cells)
    if cells < 0:
        msg = "absorbing_layer_cells must be non-negative"
        raise ValueError(msg)
    if cells >= min(nx, ny):
        msg = (
            "absorbing_layer_cells must be fewer than the cells along the "
            "shortest grid side"
        )
        raise ValueError(msg)
    if not 0.0 < absorbing_layer_reflection < 1.0:
        msg = "absorbing_layer_reflection must lie strictly between 0 and 1"
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
    return cells, damping_map


class _PressureEngine(Protocol):
    """The stepping interface the shared ``run()`` driver relies on."""

    @property
    def _backend(self) -> _backends.Backend:
        """The backend the engine steps on, read to bring a frame to the host."""

    def step(self) -> None:
        """Advance the leapfrog scheme by one time step."""

    @property
    def p(self) -> _backends.DeviceArray:
        """Pressure at the cell centres, shape ``(ny, nx)``, on the device."""


def _snapshot_options(
    snapshot_every: int | np.integer[Any] | None,
    snapshot_decimation: int | np.integer[Any],
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
    n_steps: int | np.integer[Any],
    snapshot_every: int | np.integer[Any] | None,
    snapshot_decimation: int | np.integer[Any],
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
    obstacle_mask: ArrayLike | None, ny: int, nx: int
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

    Any sequence of the two counts is read, and a one-dimensional array as
    the sequence of its items. A value that is not a sequence, a text, or a
    cell count that is not a number, is the wrong type; a sequence of another
    length, or a count that is not a whole number of one cell or more, is a
    wrong value. A whole float is kept as the count it names.

    :raises TypeError: for a value that is neither a sequence nor a
        one-dimensional array, a text, or a count that is not a number.
    :raises ValueError: for a sequence of another length than two, or a count
        that is not a whole number of at least one.
    """
    msg = f"shape must be a pair of positive integers (ny, nx); got {shape!r}"
    if isinstance(shape, np.ndarray) and shape.ndim == 1:
        shape = shape.tolist()
    if not isinstance(shape, Sequence) or isinstance(shape, str | bytes):
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


def _given_grid(shape: GridShape | None) -> tuple[int, int] | None:
    """The grid a given ``shape`` names, checked whether a map is given beside it or not.

    :raises TypeError: as :func:`_grid_shape`.
    :raises ValueError: as :func:`_grid_shape`.
    """
    return None if shape is None else _grid_shape(shape)


def _map_on_grid(name: str, field: Field2D, grid: tuple[int, int] | None) -> None:
    """Refuse a ``shape`` given beside a map that names another grid.

    :raises ValueError: when *grid* is given and the map has another shape.
    """
    if grid is not None and field.shape != grid:
        msg = (
            f"shape {grid} does not match the {name} map, whose shape is "
            f"{field.shape}; give shape only for a scalar {name}, or the map's own"
        )
        raise ValueError(msg)


def _resolve_c_map(c: ArrayLike, shape: GridShape | None) -> Field2D:
    """Broadcast/validate the sound-speed spec into a positive 2D map.

    A ``shape`` is read whenever it is given: it spreads a scalar ``c`` over
    the grid it names, and beside a map it must name the map's grid.
    """
    if np.iscomplexobj(c):
        msg = "c must be real; a complex sound speed is not supported"
        raise TypeError(msg)
    grid = _given_grid(shape)
    if np.isscalar(c):
        if grid is None:
            msg = "shape is required when c is a scalar"
            raise ValueError(msg)
        c_map = np.full(grid, float(np.real(c)), dtype=np.float64)
    else:
        c_map = np.asarray(c, dtype=np.float64)
    # The number is a count of array axes, not a quantity.
    if c_map.ndim != 2:  # noqa: PLR2004
        msg = "c must be a 2D (ny, nx) map"
        raise ValueError(msg)
    _map_on_grid("c", c_map, grid)
    _positive_map("c", c_map)
    return c_map


def _resolve_rho_map(rho: ArrayLike, ny: int, nx: int) -> Field2D:
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
    absorbing_sides: Side | Iterable[Side] | None,
) -> tuple[Side, ...]:
    """Normalise the sponge-side spec into a validated tuple of side names.

    :raises TypeError: for a side that is not a text.
    :raises ValueError: for a side that is not ``"left"``, ``"right"``,
        ``"top"`` or ``"bottom"``.
    """
    if absorbing_sides is None:
        return _SIDES
    # A bare string would iterate per character; treat it as one side.
    given = (absorbing_sides,) if isinstance(absorbing_sides, str) else absorbing_sides
    return tuple(require_choice(side, "absorbing_sides", _SIDES) for side in given)


def _impedance_numbers(side: str, value: object) -> NDArray[Any]:
    """One side's impedance read as numbers: a real scalar, or a profile of them.

    Read as NumPy reads it, so no number moves; only what is no real number
    is refused here, where ``np.asarray(value, float)`` would read a flag as
    an impedance of 1 Pa s/m and ``None`` as NaN. Real numbers NumPy keeps
    as objects (an int too large for 64 bits, a ``Fraction``) are read as
    floats, and one too large for a float is no finite impedance.

    :raises TypeError: for a flag, ``None``, a text, a complex number or
        anything else that is not a real number or an array of them.
    :raises ValueError: for a ragged profile, or a number too large for a
        float.
    """
    read = None
    if value is not None and not isinstance(value, str | bool | np.bool_):
        try:
            read = np.asarray(value)
        except ValueError:
            msg = f"impedance for side {side!r} must be a scalar or a 1D array"
            raise ValueError(msg) from None
    if read is not None and read.dtype == np.object_:
        read = _real_objects(side, read)
    elif read is not None and _holds_a_flag(value, read):
        # ``[True, 415.0]`` reads as the floats ``[1.0, 415.0]``.
        read = None
    if read is None or read.dtype.kind not in _REAL_KINDS:
        msg = (
            f"impedance for side {side!r} must be a real number [Pa s/m] or an "
            f"array of them; got {type(value).__name__}"
        )
        raise TypeError(msg)
    return read


def _holds_a_flag(value: object, read: NDArray[Any]) -> bool:
    """Whether a profile written as items holds a flag NumPy read as a number.

    NumPy reads ``[True, 415.0]`` as the floats ``[1.0, 415.0]``, so the
    items are read as they were written, before NumPy chose one type for
    them. An array holds one type, which :func:`_impedance_numbers` reads.
    """
    if isinstance(value, np.ndarray) or read.ndim == 0:
        return False
    items = np.asarray(value, dtype=object).ravel().tolist()
    return any(isinstance(item, bool | np.bool_) for item in items)


def _real_objects(side: str, read: NDArray[np.object_]) -> NDArray[np.float64] | None:
    """Real numbers NumPy holds as objects, as floats, or ``None`` when one is no real number.

    :raises ValueError: for a number too large for a float.
    """
    if not all(
        isinstance(item, Real) and not isinstance(item, bool | np.bool_)
        for item in read.ravel().tolist()
    ):
        return None
    try:
        return read.astype(np.float64)
    except OverflowError:
        msg = f"impedance for side {side!r} must be strictly positive and finite"
        raise ValueError(msg) from None


def _edge_impedance_profile(side: str, value: ArrayLike, n_edge: int) -> Field2D:
    """Broadcast/validate one side's impedance into a positive 1D profile.

    :raises TypeError: for an impedance that is not a real number or an
        array of them (:func:`_impedance_numbers`).
    """
    z = _impedance_numbers(side, value).astype(np.float64)
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
    edge_impedance: Mapping[Side, ArrayLike] | None,
    absorbing: tuple[Side, ...],
    ny: int,
    nx: int,
) -> list[tuple[str, Field2D]]:
    """Validate the per-side impedance spec into ``(side, profile)`` pairs.

    :param absorbing: The sides that carry a sponge layer, which cannot
        also be impedance boundaries.
    :return: One pair per impedance side, in the order of :data:`_SIDES`.
    :raises TypeError: for a side that is not a text.
    :raises ValueError: for a side that is not ``"left"``, ``"right"``,
        ``"top"`` or ``"bottom"``.
    """
    if not edge_impedance:
        return []
    for side in edge_impedance:
        require_choice(side, "edge_impedance", _SIDES)
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
    c: ArrayLike, shape: GridShape | None, cfl: float, dx: float
) -> tuple[Field2D, float, float]:
    """The sound-speed map, the grid spacing and the time step, checked on the host.

    :return: ``(c_map, dx, dt)``.
    """
    _require_courant(cfl)
    c_map = _resolve_c_map(c, shape)
    dx = _positive_finite("dx", dx)
    return c_map, dx, _time_step(cfl, dx, float(c_map.max()))


@dataclass(frozen=True)
class _AcousticMedium:
    """An acoustic medium checked on the host, before any device is asked for.

    What :class:`FDTD2D` builds its maps from, and what an
    :class:`FDTDRun` checks when it is built: the same function checks both,
    so a bad argument raises the same error on every route.
    """

    c_map: Field2D
    rho_map: Field2D
    dx: float
    dt: float
    absorbing_layer_cells: int
    sides: tuple[Side, ...]
    absorbing_sides: tuple[Side, ...]
    damping_map: NDArray[np.float64]
    impedances: list[tuple[str, Field2D]]
    obstacle: NDArray[np.bool_] | None


def _acoustic_medium(
    c: ArrayLike,
    dx: float,
    *,
    rho: ArrayLike,
    cfl: float,
    absorbing_layer_cells: int | np.integer[Any],
    absorbing_sides: Side | Iterable[Side] | None,
    absorbing_layer_reflection: float,
    damping: ArrayLike,
    shape: GridShape | None,
    edge_impedance: Mapping[Side, ArrayLike] | None,
    obstacle_mask: ArrayLike | None,
) -> _AcousticMedium:
    """Check every argument of :class:`FDTD2D` that describes the medium.

    In the order the constructor always checked them: the grid and the
    time step, the density, the sponge and the damping, the sponge sides,
    the impedance edges, the obstacle.
    """
    c_map, dx, dt = _acoustic_grid(c, shape, cfl, dx)
    ny, nx = c_map.shape
    rho_map = _resolve_rho_map(rho, ny, nx)
    cells, damping_map = _validate_sponge_damping(
        absorbing_layer_cells, absorbing_layer_reflection, damping, ny, nx
    )
    sides = _resolve_sponge_sides(absorbing_sides)
    cells = require_count(cells, "absorbing_layer_cells", at_least=None)
    used = sides if cells > 0 else ()
    return _AcousticMedium(
        c_map=c_map,
        rho_map=rho_map,
        dx=dx,
        dt=dt,
        absorbing_layer_cells=cells,
        sides=sides,
        absorbing_sides=used,
        damping_map=damping_map,
        impedances=_validated_impedances(edge_impedance, used, ny, nx),
        obstacle=_validated_obstacle(obstacle_mask, ny, nx),
    )


def _step_count(duration_s: float, dt: float) -> int:
    """The number of steps of *dt* that cover *duration_s*, at least one."""
    steps = round(duration_s / dt)
    if steps < 1:
        msg = f"duration_s must cover at least one time step (dt = {dt:.3e} s)"
        raise ValueError(msg)
    return steps


def _snapshot_shape(
    grid: tuple[int, int],
    steps: int,
    snapshot_every: int | None,
    snapshot_decimation: int,
) -> tuple[int, int, int] | None:
    """The shape of the snapshots a run of *steps* records on *grid*, or ``None``.

    One frame for the initial field and one every ``snapshot_every`` steps,
    each keeping every ``snapshot_decimation``-th cell along each axis. The
    checks of both runs read it here.
    """
    if snapshot_every is None:
        return None
    ny, nx = grid
    d = snapshot_decimation
    return (steps // snapshot_every + 1, -(-ny // d), -(-nx // d))


def _snapshot_times(
    steps: int, snapshot_every: int | None, dt: float
) -> NDArray[np.float64] | None:
    """The time of each snapshot a run of *steps* records [s], or ``None``.

    Read by both simulation functions, for the frames :func:`_snapshot_shape`
    counts.
    """
    if snapshot_every is None:
        return None
    return np.arange(0, steps + 1, snapshot_every, dtype=np.float64) * dt


def _check_source(
    source: AnySource, shape: tuple[int, ...], obstacle: NDArray[np.bool_] | None
) -> None:
    """Refuse a source off the grid ``(ny, nx)`` or inside the obstacle.

    Shared by :meth:`FDTD2D.add_source` and :class:`FDTDRun`, which checks
    its sources against the grid when the run is built.
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
    """Refuse a plane-wave injection line off the grid or across the obstacle.

    Its ``direction`` was checked when the source was built.
    """
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
    :raises TypeError: if ``ix0``, ``ix1``, ``iy0`` or ``iy1`` is a flag, a text or an
        array where a count goes.
    """

    def __init__(
        self,
        engine: FDTD2D,
        ix0: int | np.integer[Any],
        ix1: int | np.integer[Any],
        iy0: int | np.integer[Any],
        iy1: int | np.integer[Any],
        frequencies: ArrayLike,
    ) -> None:
        require_scalar(ix0, "ix0")
        require_scalar(ix1, "ix1")
        require_scalar(iy0, "iy0")
        require_scalar(iy1, "iy1")
        ny, nx = engine.p.shape
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
        if engine._obstacle is not None:
            # Every sampled face needs open cells on both of its sides:
            # the two cell columns flanking the vertical faces and the two
            # cell rows flanking the horizontal ones.
            blocked = bool(
                engine._obstacle[iy0 : iy1 + 1, [ix0 - 1, ix0, ix1, ix1 + 1]].any()
                or engine._obstacle[[iy0 - 1, iy0, iy1, iy1 + 1], ix0 : ix1 + 1].any()
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
        dx = engine.dx
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
        self._dt = engine.dt
        self._dx = dx
        b = engine._backend
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
        self._n_samples = 0

    @property
    def n_samples(self) -> int:
        """Number of DFT samples accumulated since the last reset, one per step."""
        return self._n_samples

    def reset(self) -> None:
        """Clear the running sums (call once the field is steady)."""
        with self._backend.context():
            self._sums[...] = 0.0
            if self._carry is not None:
                self._carry[...] = 0.0
        self._n_samples = 0

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
        self._n_samples += 1

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
        if self._n_samples == 0:
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
        scale = 2.0 / self._n_samples
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
    :param absorbing_layer_cells: Thickness of the absorbing (sponge) layer,
        in cells (default 0, no layer and no absorbing side).
    :param absorbing_sides: Which sides absorb: a single side name or an
        iterable drawn from ``{"left", "right", "top", "bottom"}``
        (default: all four when ``absorbing_layer_cells > 0``).
        ``left``/``right`` are the low/high column edges and
        ``top``/``bottom`` the low/high row edges (the default ``imshow``
        origin).
    :param absorbing_layer_reflection: Target round-trip amplitude reflection
        of the sponge layer; sets the peak absorption rate.
    :param damping: Bulk amplitude decay rate [1/s]: a scalar applied to
        the whole field (a simple stand-in for air/wall absorption;
        ``6.91 / T60`` gives a ``T60`` seconds reverberant decay) or an
        ``(ny, nx)`` map for locally lossy regions, e.g. an equivalent
        fluid modelling a porous sample (plane waves inside a uniform
        lossy region follow :math:`k = (\omega - j \sigma) / c` with the
        real characteristic impedance :math:`\rho c`).
    :param shape: Grid shape ``(ny, nx)``, required only when ``c`` is a
        scalar; beside a map it must be the map's own shape.
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
    :raises TypeError: if ``cfl``, ``dx`` or ``absorbing_layer_reflection`` is not
        a single number, ``absorbing_layer_cells`` is a flag, a text or an array
        where a count goes, ``shape`` is not a pair or holds a count that is
        not a number, a side of ``absorbing_sides`` or ``edge_impedance`` is
        not a text, an impedance of ``edge_impedance`` is not a real number or
        an array of them (a flag, ``None`` or a text among them), or
        ``compute`` is neither a :class:`Compute` nor ``None``.
    :raises ValueError: for an argument out of its range, a ``shape`` given
        beside a map of another shape, a side that is not ``"left"``,
        ``"right"``, ``"top"`` or ``"bottom"``, and for a ``compute`` that
        names a host: an engine steps in this process, and only
        :func:`fdtd_simulation` runs on a node.
    :raises ComputeImportError: when the library of the device ``compute``
        asks for is not installed or does not import.
    :raises ComputeDeviceError: when that device is not present, or fails a
        first small computation; with ``fallback=True`` the engine warns
        with :class:`ComputeFallbackWarning` and steps on NumPy instead.
    """

    def __init__(
        self,
        c: ArrayLike,
        dx: float,
        *,
        rho: ArrayLike = 1.2,
        cfl: float = 0.6,
        absorbing_layer_cells: int | np.integer[Any] = 0,
        absorbing_sides: Side | Iterable[Side] | None = None,
        absorbing_layer_reflection: float = _DEFAULT_SPONGE_REFLECTION,
        damping: ArrayLike = 0.0,
        shape: GridShape | None = None,
        edge_impedance: Mapping[Side, ArrayLike] | None = None,
        obstacle_mask: ArrayLike | None = None,
        compute: Compute | None = None,
    ) -> None:
        medium = _acoustic_medium(
            c,
            dx,
            rho=rho,
            cfl=cfl,
            absorbing_layer_cells=absorbing_layer_cells,
            absorbing_sides=absorbing_sides,
            absorbing_layer_reflection=absorbing_layer_reflection,
            damping=damping,
            shape=shape,
            edge_impedance=edge_impedance,
            obstacle_mask=obstacle_mask,
        )
        c_map, rho_map = medium.c_map, medium.rho_map
        self.dx, self.dt = medium.dx, medium.dt
        ny, nx = c_map.shape
        #: Thickness of the absorbing (sponge) layer, in cells.
        self.absorbing_layer_cells = medium.absorbing_layer_cells
        #: Sides carrying the absorbing layer; none when it has no cells.
        self.absorbing_sides: tuple[Side, ...] = medium.absorbing_sides
        self._obstacle: NDArray[np.bool_] | None = medium.obstacle

        # Every argument is checked on the host before the device is asked
        # for, so a bad one raises its own error, never a missing library's
        # or a fallback warning first. Then a host is refused: an engine
        # steps in this process.
        backend = _backends.backend_for(_local_request(compute, owner="FDTD2D"))
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
        #: Bulk modulus at the cell centres [Pa], a read-only NumPy copy.
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

        self._init_decay(
            medium.sides,
            medium.absorbing_layer_cells,
            absorbing_layer_reflection,
            medium.damping_map,
            c_max,
        )
        rho_edges = {
            "left": self.rho[:, 0],
            "right": self.rho[:, -1],
            "top": self.rho[0, :],
            "bottom": self.rho[-1, :],
        }
        self._edges = [
            _ImpedanceEdge(side, z, rho_edges[side], self.dt, self.dx, backend)
            for side, z in medium.impedances
        ]
        #: Per-side impedance boundaries as supplied (immutable record), read
        #: once the edges have validated them; an array profile is kept as a
        #: read-only copy of its own.
        self.edge_impedance: Mapping[Side, float | NDArray[np.float64]] = (
            MappingProxyType(
                {
                    side: float(np.asarray(value, dtype=np.float64))
                    if np.ndim(value) == 0
                    else read_only_copy(value, np.float64)
                    for side, value in (edge_impedance or {}).items()
                }
            )
        )
        self._init_obstacle()

    def _init_decay(
        self,
        sides: tuple[Side, ...],
        absorbing_layer_cells: int,
        absorbing_layer_reflection: float,
        damping: NDArray[np.float64],
        c_max: float,
    ) -> None:
        """Precompute the sponge/damping decay factors of every field."""
        sigma = _sigma_map(
            self.p.shape,
            sides,
            absorbing_layer_cells,
            absorbing_layer_reflection,
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
        direction: Travel,
        *,
        center_m: float,
        half_width_m: float,
        amplitude: float = 1.0,
        wavelength_m: float | None = None,
    ) -> None:
        r"""Superimpose a one-way plane wave packet as an initial condition.

        A Gaussian envelope (optionally carrying a sine at ``wavelength_m``)
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
        :param center_m: Envelope centre along the travel axis [m].
        :param half_width_m: Gaussian envelope half-width :math:`w` [m], the
            ``1/e`` point of :math:`\mathrm{e}^{-((x - x_0)/w)^2}`, as
            :attr:`GaussianPulse.half_width_s` is in time.
        :param amplitude: Peak pressure of the envelope [Pa].
        :param wavelength_m: Optional carrier wavelength [m]; ``None`` gives
            the pure Gaussian pulse.
        :raises ValueError: For an unknown direction, a non-positive or
            non-finite ``half_width_m``/``wavelength_m``, or a non-finite
            ``center_m``/``amplitude``.
        :raises TypeError: if ``direction`` is not a text, or ``amplitude``,
            ``center_m``, ``wavelength_m`` or ``half_width_m`` is not a single
            number.
        """
        require_choice(direction, "direction", _SIDE_TRAVEL)
        width = require_positive(half_width_m, "half_width_m")
        wavelength = (
            None
            if wavelength_m is None
            else require_positive(wavelength_m, "wavelength_m")
        )
        center = _finite("center_m", center_m)
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
        probes: Iterable[Sequence[int | np.integer[Any]]]
        | NDArray[np.integer[Any]]
        | None = None,
        language: Language = "en",
        **kwargs: Any,
    ) -> Axes:
        """Draw the configured domain before running it.

        Domain extent, obstacles, sponge layers, impedance and rigid edges
        and the added sources, with optional probe cells previewed; no
        time stepping happens. Requires matplotlib
        (``pip install "phonometry[plot]"``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param probes: Optional probe cells as ``(ix, iy)`` index pairs, the
            cells :class:`FDTDRecording` takes. Each is drawn at its cell
            centre ``((ix + 0.5) * dx, (iy + 0.5) * dx)``, where the run
            records it (:attr:`FDTDResult.probe_positions`).
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the obstacle ``imshow``.
        :raises TypeError: for a probe that is not a pair, or an index that is
            not a number, and for ``extent`` or ``origin`` in ``kwargs``, which
            the grid sets: the obstacles are drawn on the grid the sources and
            probes are on.
        :raises ValueError: for a probe of more or fewer than two indices, an
            index that is not whole, or a cell outside the grid or inside an
            obstacle, refused in the words a run uses.
        """
        from .._i18n import check_language
        from .._plot.geometry import plot_fdtd_domain

        check_language(language)
        positions = None
        if probes is not None:
            cells = _probe_indices(probes, self.c.shape, self._obstacle)
            if cells.shape[0]:
                positions = (cells.astype(np.float64) + 0.5) * self.dx
        return plot_fdtd_domain(
            self, ax=ax, probe_positions=positions, language=language, **kwargs
        )

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
        self,
        ix0: int | np.integer[Any],
        ix1: int | np.integer[Any],
        iy0: int | np.integer[Any],
        iy1: int | np.integer[Any],
        *,
        frequencies: ArrayLike,
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
        n_steps: int | np.integer[Any],
        *,
        snapshot_every: int | np.integer[Any] | None = None,
        snapshot_decimation: int | np.integer[Any] = 1,
    ) -> NDArray[np.floating]:
        """Advance ``n_steps`` steps, optionally recording pressure frames.

        With ``snapshot_every = k`` a NumPy copy of ``p`` is stored after
        every ``k``-th step (and one of the initial state), keeping every
        ``snapshot_decimation``-th cell along each axis; the stacked
        ``(n_frames, ny', nx')`` array plugs straight into a ``FuncAnimation``
        ``imshow`` update. Without ``snapshot_every`` an empty array is
        returned and only the final state is kept (read it with
        :meth:`numpy_field`). The two counts are taken by name, as
        :class:`FDTDRecording` takes them.

        :raises TypeError: if ``snapshot_decimation``, ``n_steps`` or
            ``snapshot_every`` is a flag, a text or an array where a count goes.
        :raises ValueError: if ``n_steps`` is not a whole number of 0 or more,
            or ``snapshot_every`` or ``snapshot_decimation`` is not a whole
            number of 1 or more.
        """
        return _run_recording(self, n_steps, snapshot_every, snapshot_decimation)

    #: The arrays the engine stores, the names :meth:`numpy_field` reads.
    _STORED: tuple[Literal["p", "vx", "vy"], ...] = ("p", "vx", "vy")

    def numpy_field(self, field: Literal["p", "vx", "vy"]) -> NDArray[np.floating]:
        """A NumPy copy of the stored *field*, in this process, whatever the device.

        :param field: ``"p"`` (cell centres), ``"vx"`` or ``"vy"`` (faces).
        :raises TypeError: if ``field`` is not a text.
        :raises ValueError: for a field the engine does not store.
        """
        require_choice(field, "field", self._STORED)
        return np.array(self._backend.to_host(getattr(self, field)), copy=True)

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
        :raises TypeError: for a ``kind`` that is not a text, or
            ``color_limit`` with ``kind="snapshot"``, which the field drawn
            sets (``vmin`` and ``vmax`` reach ``imshow``).
        :raises ValueError: for a ``kind`` other than ``"probes"`` and
            ``"snapshot"``, a ``language`` other than ``"en"`` and ``"es"``,
            or a snapshot asked of a result that holds none.
        """
        from .._i18n import check_language

        check_language(language)
        if require_choice(kind, "kind", _PLOT_KINDS) == "probes":
            from .._plot.simulation import plot_fdtd_probes

            return plot_fdtd_probes(self, ax=ax, language=language, **kwargs)
        from .._plot.simulation import plot_fdtd_snapshot

        return plot_fdtd_snapshot(self, ax=ax, frame=frame, language=language, **kwargs)


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

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            probes: Sequence[Sequence[int | np.integer[Any]]]
            | NDArray[np.integer[Any]] = (),
            snapshot_every: int | np.integer[Any] | None = None,
            snapshot_decimation: int | np.integer[Any] = 1,
        ) -> None: ...

    def __post_init__(self) -> None:
        """Refuse a malformed probe or count when the record is built.

        Whether a probe lies on the grid, and outside the obstacle, is checked
        by the :class:`FDTDRun` that holds the record, the first place a grid
        exists.
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


@dataclass(frozen=True, kw_only=True)
class FDTDBoundaries(OwnsArrays):
    """How the four edges of the acoustic domain are terminated.

    The sponge thickness only means anything where a side is absorbing, which
    is why it travels with the sides rather than beside them.

    :param sides: ``"rigid"`` (default), ``"absorbing"``, or a mapping from
        side name (``left``/``right``/``top``/``bottom``) to ``"rigid"``,
        ``"absorbing"``, or a real specific impedance [Pa s/m] (scalar or
        per-edge-cell 1D array, Eqs. 4.33-4.35); a side the mapping leaves
        out is rigid. A mapping is held as a read-only copy, an impedance
        as the float a run reads, and a profile, given as a list or as an
        array of any real type, as a read-only float64 array of the
        record's own, so a change to the caller's dictionary, list or array
        afterwards does not reach the record.
    :param absorbing_layer_cells: Sponge-layer thickness for absorbing sides,
        in cells, held as the whole number it names.
    :raises TypeError: for ``sides`` that are neither a name nor a mapping,
        a side of ``sides`` that is not a text, a termination that is
        neither a name nor a real number or an array of them (a flag,
        ``None`` or a complex number among them), or an
        ``absorbing_layer_cells`` that is a flag, a text, an array or
        anything else that is not a number.
    :raises ValueError: for a side that is not ``"left"``, ``"right"``,
        ``"top"`` or ``"bottom"``, a termination name that is not
        ``"rigid"`` or ``"absorbing"``, a ragged impedance profile or an
        impedance too large for a float, or an ``absorbing_layer_cells`` that
        is not a whole number.
    """

    sides: AcousticBoundary | Mapping[Side, AcousticBoundary | float | Field2D] = (
        "rigid"
    )
    absorbing_layer_cells: int = 20

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            sides: AcousticBoundary
            | Mapping[
                Side,
                AcousticBoundary
                | float
                | np.floating[Any]
                | np.integer[Any]
                | Sequence[float]
                | NDArray[np.floating[Any] | np.integer[Any]],
            ] = "rigid",
            absorbing_layer_cells: int | np.integer[Any] = 20,
        ) -> None: ...

    def __post_init__(self) -> None:
        """Refuse an unknown side or termination, and hold the sides and the thickness.

        A mapping of sides is held as a read-only copy of its own, each
        impedance as the float or the float64 profile a run reads, and the
        thickness as the whole number of cells it names. Whether a profile
        fits its edge, an impedance is positive, and the thickness fits the
        grid, is checked where a run reads them, the first place a grid
        exists.
        """
        if isinstance(self.sides, Mapping):
            held: dict[Side, AcousticBoundary | float | Field2D] = {}
            for side, value in self.sides.items():
                require_choice(side, "sides", _SIDES)
                if isinstance(value, str):
                    held[side] = require_choice(
                        value, f"sides[{side!r}]", _BOUNDARY_NAMES
                    )
                    continue
                # An impedance, held as the float or the float64 profile a
                # run reads (_edge_impedance_profile), read once here.
                numbers = _impedance_numbers(side, value)
                held[side] = (
                    float(numbers)
                    if numbers.ndim == 0
                    else read_only_copy(numbers, np.float64)
                )
            object.__setattr__(self, "sides", MappingProxyType(held))
        else:
            require_choice(self.sides, "sides", _BOUNDARY_NAMES)
        require_scalar(self.absorbing_layer_cells, "absorbing_layer_cells")
        object.__setattr__(
            self,
            "absorbing_layer_cells",
            _integer("absorbing_layer_cells", self.absorbing_layer_cells),
        )

    def __reduce__(self) -> tuple[Any, tuple[type, dict[str, Any]]]:
        """Rebuild from the fields: a read-only mapping of sides does not pickle."""
        return reduce_with_plain_rows(self)


@dataclass(frozen=True)
class _AcousticChecks:
    """What the checks of an :class:`FDTDRun` found, kept with the run.

    The grid and the counts the run is stepped and recorded with, so that
    the simulation function, here or on its way to a node, reads them
    without checking anything twice. No map is kept: an engine builds its
    own.
    """

    grid: tuple[int, int]
    dx: float
    dt: float
    obstacle: NDArray[np.bool_] | None
    absorbing_sides: tuple[Side, ...]
    edge_impedance: Mapping[Side, float | Field2D]
    absorbing_layer_cells: int
    probe_ix: NDArray[np.int_]
    steps: int
    snapshot_every: int | None
    snapshot_decimation: int

    def snapshot_shape(self) -> tuple[int, int, int] | None:
        """The shape of the snapshots the run records, or ``None`` when it records none."""
        return _snapshot_shape(
            self.grid, self.steps, self.snapshot_every, self.snapshot_decimation
        )


@dataclass(frozen=True, kw_only=True)
class FDTDRun(OwnsArrays):
    r"""One acoustic FDTD simulation: the domain, its sources and what it records.

    Every argument is checked when the run is built, the grid's included:
    the time step, the density, the sponge and the damping, the impedance
    edges, the obstacle, and the sources and the probes on the grid. A run
    that builds is one :func:`fdtd_simulation` can step, here or on a node,
    and a bad argument raises where the run is written, with the class and
    the words the function always raised. The sources are held as a tuple
    and each array as the run's own read-only copy, so nothing the caller
    changes afterwards reaches a checked run.

    :param c: Sound-speed map [m/s], shape ``(ny, nx)``, or a scalar with an
        explicit ``shape``.
    :param dx: Grid spacing [m] (square cells).
    :param duration_s: Physical time to simulate [s].
    :param sources: One or more of :class:`GaussianPulse`,
        :class:`CWSource`, :class:`SignalSource` or :class:`PlaneWaveSource`.
    :param shape: Grid shape ``(ny, nx)``, required when ``c`` is a scalar;
        beside a map it must be the map's own shape.
    :param rho: Density map [kg/m3]; scalar or ``(ny, nx)`` array.
    :param cfl: Courant number in ``(0, 1)`` (Eqs. 4.13-4.14); the time step
        is :math:`\Delta t = C_\mathrm{N}\, \Delta x / (c_{\max} \sqrt{2})`.
        Default 0.6.
    :param recording: What the run records (:class:`FDTDRecording`): the
        probe cells, and the snapshot cadence and decimation. ``None``
        records nothing but the time axis.
    :param boundaries: How the domain edges are terminated
        (:class:`FDTDBoundaries`): the rigid, absorbing and impedance sides,
        and the sponge thickness of the absorbing ones. ``None`` is rigid on
        all four sides.
    :param obstacle_mask: Boolean map, shape ``(ny, nx)``, of rigid cells
        (rasterised interior geometry).
    :param damping: Bulk amplitude decay rate [1/s]: a scalar for the whole
        field or an ``(ny, nx)`` map.
    :raises TypeError: If an argument is of the wrong type: a ``duration_s``,
        ``cfl`` or ``dx`` that is not one number, a ``recording`` that is
        neither an :class:`FDTDRecording` nor ``None``, ``boundaries`` that
        are neither an :class:`FDTDBoundaries` nor ``None``, a ``shape``
        that is not a pair or holds a count that is not a number, a complex
        medium, or an ``obstacle_mask`` that is not boolean.
    :raises ValueError: If an argument is out of its range, a ``shape`` is
        not two whole numbers of one cell or more or is given beside a map of
        another shape, or a source, a probe or the obstacle does not fit the
        grid.
    """

    c: float | Field2D
    dx: float
    duration_s: float
    sources: Sequence[AnySource]
    shape: tuple[int, int] | None = None
    rho: float | Field2D = 1.2
    cfl: float = 0.6
    recording: FDTDRecording | None = None
    boundaries: FDTDBoundaries | None = None
    obstacle_mask: NDArray[np.bool_] | None = None
    damping: float | Field2D = 0.0

    if TYPE_CHECKING:

        def __init__(
            self,
            *,
            c: ArrayLike,
            dx: float,
            duration_s: float,
            sources: Sequence[AnySource],
            shape: GridShape | None = None,
            rho: ArrayLike = 1.2,
            cfl: float = 0.6,
            recording: FDTDRecording | None = None,
            boundaries: FDTDBoundaries | None = None,
            obstacle_mask: ArrayLike | None = None,
            damping: ArrayLike = 0.0,
        ) -> None: ...

    def __post_init__(self) -> None:
        """Hold the containers and the maps so they cannot change, then check every argument.

        A ``shape`` is held as the pair of whole numbers it names: the grid a
        scalar ``c`` is spread over, or, beside a map, the map's own grid.
        """
        object.__setattr__(self, "sources", tuple(self.sources))
        if self.shape is not None:
            object.__setattr__(self, "shape", _grid_shape(self.shape))
        for name in ("c", "rho", "damping"):
            object.__setattr__(self, name, _held_map(getattr(self, name)))
        object.__setattr__(self, "obstacle_mask", _held_map(self.obstacle_mask, None))
        # Every argument is checked once, here, and what the checks found is kept.
        _ = self._checked

    @cached_property
    def _checked(self) -> _AcousticChecks:
        """Every argument checked, once, when the run is built."""
        return _acoustic_checks(self)

    def __reduce__(self) -> tuple[Any, tuple[type, dict[str, Any]]]:
        """Rebuild from the fields, so the run checks itself again where it arrives."""
        return reduce_with_plain_rows(self)


def _held_map(
    value: ArrayLike | None, dtype: type[np.generic] | None = np.float64
) -> object:
    """A real-valued map given as nested sequences, as the run's own read-only array.

    A run copies the arrays it is given, not the lists: one built from
    ``[[343.0, ...], ...]`` would keep the caller's list, and an edit to it
    afterwards would change what the run steps here and what a node
    rebuilds. The list is read as the checks read it, so no number moves. A
    number, a text, an array or ``None`` is left as it is. So is a value the
    conversion refuses (an int too large for a float, a number whose float
    divides by zero), which the checks then refuse in their own words and in
    their own order, and a map that holds complex numbers, which the checks
    meet as they always did: :class:`FDTDRun`'s ``c`` and ``rho`` refuse it
    with ``TypeError``; elsewhere a map of Python complex numbers raises
    ``TypeError`` in the float conversion, and one of NumPy complex numbers
    loses its imaginary part with a ``ComplexWarning`` and stays the
    caller's list. Read here as float64, a map of NumPy complex numbers
    would warn a second time; read as complex, a map of Python complex
    numbers would turn its refusal into a warning. So only a real-valued map
    is held.

    :param dtype: What the checks read the map as: float64 for a medium,
        ``None`` for the obstacle, whose checks require booleans.
    """
    if value is None or np.isscalar(value) or isinstance(value, np.ndarray):
        return value
    try:
        held = None if np.iscomplexobj(value) else np.array(value, dtype=dtype)
    except (TypeError, ValueError, ArithmeticError):
        held = None
    return value if held is None else read_only(held)


def _acoustic_boundaries_or_rigid(boundaries: object) -> FDTDBoundaries:
    """A run's ``boundaries``, or rigid on all four sides for ``None``.

    :raises TypeError: for anything but ``None`` or an :class:`FDTDBoundaries`.
    """
    if boundaries is None:
        return FDTDBoundaries()
    if not isinstance(boundaries, FDTDBoundaries):
        msg = f"'boundaries' must be an FDTDBoundaries or None, got {type(boundaries).__name__}."
        raise TypeError(msg)
    return boundaries


def _acoustic_checks(run: FDTDRun) -> _AcousticChecks:
    """Check every argument of *run*, as :func:`fdtd_simulation` always did.

    The recording's type, the boundaries' type, the sources, the duration
    and the sponge thickness of absorbing sides, then the medium
    (:func:`_acoustic_medium`: the grid and the time step, the density, the
    sponge and the damping, the impedance edges, the obstacle), then the
    sources and the probes on the grid and the step count. The recording and
    the boundaries checked their own fields when they were built; here the
    probes and the impedances meet the grid.

    :raises TypeError: as :class:`FDTDRun` documents.
    :raises ValueError: as :class:`FDTDRun` documents.
    """
    recording = _recording_or_empty(run.recording, FDTDRecording)
    boundaries = _acoustic_boundaries_or_rigid(run.boundaries)
    if len(run.sources) == 0:
        msg = "at least one source is required"
        raise ValueError(msg)
    duration_s = _positive_finite("duration_s", run.duration_s)
    absorbing_sides, edge_impedance = _parse_boundaries(boundaries.sides)
    width = 0
    if absorbing_sides:
        width = boundaries.absorbing_layer_cells
        if width < 1:
            msg = "absorbing_layer_cells must be >= 1"
            raise ValueError(msg)
    medium = _acoustic_medium(
        run.c,
        run.dx,
        rho=run.rho,
        cfl=run.cfl,
        absorbing_layer_cells=width,
        absorbing_sides=absorbing_sides or None,
        absorbing_layer_reflection=_DEFAULT_SPONGE_REFLECTION,
        damping=run.damping,
        shape=run.shape,
        edge_impedance=edge_impedance or None,
        obstacle_mask=run.obstacle_mask,
    )
    ny, nx = medium.c_map.shape
    for source in run.sources:
        _check_source(source, (ny, nx), medium.obstacle)
    return _AcousticChecks(
        grid=(ny, nx),
        dx=medium.dx,
        dt=medium.dt,
        obstacle=None if medium.obstacle is None else read_only(medium.obstacle),
        absorbing_sides=absorbing_sides,
        edge_impedance=MappingProxyType(edge_impedance),
        absorbing_layer_cells=width,
        probe_ix=read_only(_probe_indices(recording.probes, (ny, nx), medium.obstacle)),
        steps=_step_count(duration_s, medium.dt),
        snapshot_every=recording.snapshot_every,
        snapshot_decimation=recording.snapshot_decimation,
    )


def _acoustic_engine(run: FDTDRun, compute: Compute | None) -> FDTD2D:
    """The engine that steps *run* on this machine, its sources added.

    It takes the sponge and the impedance edges the run's checks found, and
    checks its medium again in its constructor, as every engine does.
    """
    checks = run._checked
    sim = FDTD2D(
        run.c,
        run.dx,
        rho=run.rho,
        cfl=run.cfl,
        absorbing_layer_cells=checks.absorbing_layer_cells,
        absorbing_sides=checks.absorbing_sides or None,
        damping=run.damping,
        shape=run.shape,
        edge_impedance=checks.edge_impedance or None,
        obstacle_mask=run.obstacle_mask,
        compute=compute,
    )
    for source in run.sources:
        sim.add_source(source)
    return sim


def _expected_arrays(
    histories: tuple[str, tuple[int, ...]],
    frames: tuple[int, int, int] | None,
    dtype: str,
) -> Expected:
    """What a node sends back for a run, in the order it sends it.

    The probe histories, named and shaped as *histories* says and float64
    whatever the run's dtype, then the snapshots in the run's dtype when the
    run records them. Shared by both simulation functions, whose records
    differ only in the name and the shape of the histories.
    """
    from ._remote.client import ArraySpec, Expected

    name, shape = histories
    first = ArraySpec(name, "float64", shape)
    if frames is None:
        return Expected(arrays=(first,))
    return Expected(arrays=(first, ArraySpec("snapshots", dtype, frames)))


def _acoustic_expected(run: FDTDRun, dtype: str) -> Expected:
    """The arrays a node must send back for *run*, in the order it sends them."""
    checks = run._checked
    pressures = (checks.probe_ix.shape[0], checks.steps + 1)
    return _expected_arrays(("pressures", pressures), checks.snapshot_shape(), dtype)


def _placement_here(request: Compute) -> Compute:
    """Where a run steps on this machine, for either simulation function.

    As asked when the request names no host. When it names one, this is the
    fallback after the node failed: NumPy, in the dtype the request asked
    for.
    """
    return request if request.host is None else Compute(dtype=request.dtype)


def _cleared(first: NDArray[np.floating], second: NDArray[np.floating] | None) -> None:
    """Zero what a failed remote run may have half written, before the run here."""
    first[...] = 0.0
    if second is not None:
        second[...] = 0.0


def _parse_boundaries(
    boundaries: AcousticBoundary | Mapping[Side, AcousticBoundary | float | Field2D],
) -> tuple[tuple[Side, ...], dict[Side, float | Field2D]]:
    """Split the boundary spec into sponge sides and impedance sides.

    The :class:`FDTDBoundaries` the spec comes from checked its sides and
    their names when it was built.
    """
    spec: Mapping[Side, AcousticBoundary | float | Field2D] = (
        dict.fromkeys(_SIDES, boundaries) if isinstance(boundaries, str) else boundaries
    )
    absorbing: list[Side] = []
    impedance: dict[Side, float | Field2D] = {}
    for side in _SIDES:
        value = spec.get(side, "rigid")
        if not isinstance(value, str):
            impedance[side] = value
        elif value == "absorbing":
            absorbing.append(side)
    return tuple(absorbing), impedance


def _probe_pairs(
    probes: Iterable[Sequence[int | np.integer[Any]]] | NDArray[np.integer[Any]],
) -> tuple[tuple[int, int], ...]:
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
    probes: Iterable[Sequence[int | np.integer[Any]]] | NDArray[np.integer[Any]],
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
    """A run's ``recording``, or an empty *record* for ``None``.

    Shared by :class:`FDTDRun` and :class:`ElasticRun`, so each takes its own
    record and nothing else, the other engine's included:
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


def _probe_setup(
    sim: FDTD2D, probe_ix: NDArray[np.int_], steps: int
) -> tuple[_backends.DeviceArray, _backends.DeviceArray | None]:
    """The probes' flat cell indices on the device, and a device buffer off NumPy.

    One flat index per cell, ``row * nx + column``, since the Array API
    standard indexes one axis with an integer array, not two at once.
    """
    b = sim._backend
    nx = sim.p.shape[1]
    centre = b.index(probe_ix[:, 1] * nx + probe_ix[:, 0])
    buffer = None if b.name == "numpy" else b.zeros((probe_ix.shape[0], steps + 1))
    return centre, buffer


def _store_pressures(
    sim: FDTD2D,
    centre: _backends.DeviceArray,
    column: int,
    pressures: NDArray[np.float64],
    buffer: _backends.DeviceArray | None,
) -> None:
    """Write this step's probe samples into column *column* of the record.

    Into ``pressures`` itself when there is no device ``buffer`` (NumPy),
    into the buffer otherwise.
    """
    xp = sim._xp
    sample = xp.take(xp.reshape(sim.p, (-1,)), centre)
    if buffer is None:
        pressures[:, column] = sample
    else:
        buffer[:, column] = sample


def _march(
    sim: FDTD2D,
    steps: int,
    probe_ix: NDArray[np.int_],
    snapshot_every: int | None,
    snapshot_decimation: int,
    pressures: NDArray[np.float64],
) -> Generator[_backends.DeviceArray, None, None]:
    """Step the engine *steps* times, recording the probes, yielding the field.

    With ``snapshot_every`` set, the pressure cut to every
    ``snapshot_decimation``-th cell is yielded at t = 0 and after every
    ``snapshot_every``-th step, still on the device and still the engine's
    own: the caller copies what it keeps before it asks for the next one.
    The steps after the last yield run when the generator is exhausted, so a
    caller drains it to the end, or closes it when it stops early (which
    leaves the device context it is suspended in). Each step is reported to
    the step hook, as :func:`_record_run` reports it, so a node stops a run
    whose client went away; a writer that finds its colour limit first
    marches twice, and the count goes from 1 to the step of its last frame
    the first time and from 1 to *steps* the second.

    It is :func:`_record_run`'s march with the field handed out instead of
    stored, for a writer that draws each frame and keeps none; the two share
    the probe helpers, so the probes record the same numbers either way.
    """
    b = sim._backend
    d = snapshot_decimation
    if snapshot_every is not None:
        yield sim.p[::d, ::d]
    n_probes = probe_ix.shape[0]
    centre, buffer = _probe_setup(sim, probe_ix, steps)
    with b.context():
        for i in range(steps):
            sim.step()
            _observer.step_done(i + 1, steps)
            if n_probes:
                _store_pressures(sim, centre, i + 1, pressures, buffer)
            if snapshot_every is not None and (i + 1) % snapshot_every == 0:
                yield sim.p[::d, ::d]
    if buffer is not None:
        pressures[...] = b.to_host(buffer)


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

    The probes are read through :func:`_probe_setup` and
    :func:`_store_pressures`. On NumPy the samples are written straight into
    ``pressures``; on a device they go into a buffer there, which comes to
    the host once, after the march. Each snapshot is cut to every
    ``snapshot_decimation``-th cell on the device and comes to the host as
    it is taken, so only the cells it keeps cross.

    After each step it tells a watcher, if one is set (:mod:`._observer`), how
    many steps are done; a node uses that to stop a run whose client went away.
    """
    b = sim._backend
    d = snapshot_decimation
    if snapshots is not None:
        snapshots[0] = b.to_host(sim.p[::d, ::d])
    n_probes = probe_ix.shape[0]
    centre, buffer = _probe_setup(sim, probe_ix, steps)
    with b.context():
        for i in range(steps):
            sim.step()
            _observer.step_done(i + 1, steps)
            if n_probes:
                _store_pressures(sim, centre, i + 1, pressures, buffer)
            if (
                snapshots is not None
                and snapshot_every is not None
                and (i + 1) % snapshot_every == 0
            ):
                snapshots[(i + 1) // snapshot_every] = b.to_host(sim.p[::d, ::d])
    if buffer is not None:
        pressures[...] = b.to_host(buffer)


def fdtd_simulation(run: FDTDRun, *, compute: Compute | None = None) -> FDTDResult:
    r"""Run a deterministic 2D acoustic FDTD simulation.

    Builds the staggered-grid domain (Attenborough & Van Renterghem 2021,
    Eqs. 4.11-4.12), applies the requested boundary conditions, injects the
    sources and integrates for ``duration_s`` seconds, recording the pressure
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

    :param run: The simulation (:class:`FDTDRun`): the domain, its sources
        and what it records, every argument checked when the run was built.
    :param compute: Where the run steps (:class:`Compute`); ``None`` follows
        :func:`use`, then ``PHONOMETRY_COMPUTE``, then NumPy. With a
        ``host`` the whole run goes to that node, named in the hosts file,
        and comes back as this function's record (see the guide on remote
        nodes).
    :return: A :class:`FDTDResult`.
    :raises TypeError: For a ``run`` that is not an :class:`FDTDRun`, a
        ``compute`` that is neither a :class:`Compute` nor ``None``, or,
        when ``compute`` names a host, a run that cannot travel to a node: a
        source whose waveform is a callable other than the ``value`` of a
        :class:`GaussianPulse`, :class:`CWSource` or :class:`SignalSource`,
        or a whole number outside the range of an int64.
    :raises ValueError: For a ``PHONOMETRY_COMPUTE`` that does not parse, or
        a hosts file that cannot be read or is malformed.
    :raises KeyError: For a ``host`` the hosts file does not name.
    :raises ComputeImportError: When the device's library is not installed
        or does not import.
    :raises ComputeDeviceError: When the device is not present, or fails a
        first small computation; with ``fallback=True`` the run warns with
        :class:`ComputeFallbackWarning` and steps on NumPy instead.
    :raises ComputeRemoteError: For a failure of the connection or of the
        node; with ``fallback=True`` the run warns with
        :class:`ComputeFallbackWarning` and steps on NumPy here instead.
    """
    if not isinstance(run, FDTDRun):
        msg = f"'run' must be an FDTDRun, got {type(run).__name__}."
        raise TypeError(msg)
    checks = run._checked
    request = _requested(compute)
    # The record keeps these two as they are (handed_over): the snapshots are
    # most of the result, and a copy would hold them twice while it is built.
    # The probe histories are float64 whatever the run's dtype; the snapshots
    # keep it, a float32 run's being half the size. Either route fills them.
    pressures = np.zeros((checks.probe_ix.shape[0], checks.steps + 1), dtype=np.float64)
    frames = checks.snapshot_shape()
    snapshots = (
        None if frames is None else np.zeros(frames, dtype=np.dtype(request.dtype))
    )
    provenance: RunProvenance | None = None
    if request.host is not None:
        # Called here, not from a helper the two functions share: the record
        # keeps these arrays without a copy, which holds only for arrays that
        # reach the code writing into them within three calls.
        from ._remote.client import run_remote

        expected = _acoustic_expected(run, request.dtype)
        provenance = run_remote(
            "fdtd_simulation", request, {"run": run}, expected, pressures, snapshots
        )
        if provenance is None:
            # The node failed and the request asked to run here instead.
            _cleared(pressures, snapshots)
    if provenance is None:
        sim = _acoustic_engine(run, _placement_here(request))
        _record_run(
            sim,
            checks.steps,
            checks.probe_ix,
            checks.snapshot_every,
            checks.snapshot_decimation,
            pressures,
            snapshots,
        )
        provenance = sim.provenance
    return FDTDResult(
        times=np.arange(checks.steps + 1, dtype=np.float64) * checks.dt,
        pressures=handed_over(pressures),
        probes=checks.probe_ix,
        probe_positions=(checks.probe_ix.astype(np.float64) + 0.5) * checks.dx,
        dx=checks.dx,
        dt=checks.dt,
        shape=checks.grid,
        sources=tuple(run.sources),
        snapshots=handed_over(snapshots),
        snapshot_times=_snapshot_times(checks.steps, checks.snapshot_every, checks.dt),
        obstacle_mask=checks.obstacle,
        snapshot_decimation=checks.snapshot_decimation,
        provenance=provenance,
    )
