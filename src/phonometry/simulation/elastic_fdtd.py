#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""2D elastic finite-difference time-domain (P-SV) simulation.

A staggered-grid velocity-stress leapfrog solver for the 2D elastodynamic
equations in an isotropic linear medium, following the reference formulation
of Virieux, "P-SV wave propagation in heterogeneous media: velocity-stress
finite-difference method", *Geophysics* 51(4), 889-901 (1986):

* the governing first-order velocity-stress system in ``(vx, vy)`` and
  ``(txx, tyy, txy)`` (Eq. 2), which handles heterogeneous media without any
  explicit interface treatment;
* the fully staggered discretisation of Fig. 1 / Eq. 5, second order in
  space and time, arranged here so that the normal stresses share the cell
  centres of the acoustic solver (:class:`~phonometry.simulation.FDTD2D`)
  and the velocities live on the cell faces;
* the Courant stability condition
  :math:`c_\mathrm{P} \Delta t \sqrt{1/\Delta x^2 + 1/\Delta y^2} < 1`
  (Eqs. 6-7), which depends only on the P-wave speed, and the numerical
  dispersion relations of Eqs. 13-14 with the 10-cells-per-wavelength rule;
* liquids as the ``c_s = 0`` limit: shear-free cells propagate the acoustic
  wave equation and a fluid-solid contact needs no special treatment.

Heterogeneous media use the effective grid parameters of Moczo, Kristek,
Galis, Pazak & Balazovjech, "The finite-difference and finite-element
modeling of seismic wave propagation and earthquake motion", *Acta Physica
Slovaca* 57(2), 177-406 (2007): density arithmetically averaged onto the
faces and the shear modulus harmonically averaged onto the corners
(Eqs. 7.37-7.39), which is what makes internal interfaces (including
fluid-solid ones) converge to the physical traction continuity. Free
surfaces use the stress-imaging condition (Levander 1988; Moczo et al.
Eq. 9.9): zero normal stress on the surface plane and an antisymmetric
image of the shear stress above it.

Two API levels are exposed, mirroring the acoustic module.
:func:`elastic_fdtd_simulation` takes an :class:`ElasticRun`, the record of
a simulation that checks every argument when it is built, steps it
deterministically and returns a frozen :class:`ElasticFDTDResult` with
per-probe signal histories, optional field snapshots and a ``.plot()``
method.
:class:`ElasticFDTD2D` is the underlying stepping engine for callers that
need frame-by-frame access to the five field arrays.

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

Validated against analytic oracles: P- and S-wave times of flight
:math:`c_\mathrm{P} = \sqrt{(\lambda + 2\mu) / \rho}` and
:math:`c_\mathrm{S} = \sqrt{\mu / \rho}`, the
Rayleigh-wave speed from the exact characteristic equation (Cremer, Heckl &
Petersson 2005, Eq. 3.149), the Kirchhoff thin-plate flexural dispersion
:math:`c_\mathrm{B} = (B'/m'')^{1/4} \sqrt{\omega}` in its :math:`\lambda_\mathrm{B} \gg h`
domain
(Eqs. 3.83-3.89), the normal-incidence fluid-solid reflection coefficient
:math:`(Z_2 - Z_1)/(Z_2 + Z_1)`, the normal-incidence mass law of a thin
immersed
panel, and the exact reduction to the acoustic solver when ``c_s = 0``
everywhere. The fluid-solid coupling is further pinned to the oblique
plane-wave reflection coefficient of Brekhovskikh & Godin, *Acoustics of
Layered Media I* (Springer 1990), Eqs. 4.2.22-4.2.26 (with the shear-wave
mode conversion active), to the Scholte interface-wave speed from the exact
characteristic equation of Eq. 4.4.20 (see :func:`scholte_speed`), and to
the exact three-media transmission of an immersed plate (B&G Eqs. 2.4.10,
2.4.14) including its first thickness resonance :math:`f_1 = c_\mathrm{P} / (2 h)`
(Eq. 2.4.19), following the fluid-solid finite-difference benchmark of
van Vossen, Robertsson & Chapman, *Geophysics* 67(2), 618-624 (2002).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import KW_ONLY, dataclass
from functools import cached_property
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np
from scipy.optimize import brentq

from .._internal.catalogue import CatalogueRow
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
    require_ranks,
    require_same_length,
    require_scalar,
)
from . import _backends, _observer
from .compute import _local_request, _requested
from .fdtd import (
    _DEFAULT_SPONGE_REFLECTION,
    _SIDES,
    Field2D,
    Side,
    _cleared,
    _expected_arrays,
    _finite,
    _hold_cells,
    _integer,
    _placement_here,
    _positive_finite,
    _positive_map,
    _probe_indices,
    _probe_pairs,
    _recording_or_empty,
    _require_courant,
    _require_grid_axes,
    _require_provenance,
    _resolve_sponge_sides,
    _run_recording,
    _sigma_map,
    _snapshot_options,
    _snapshot_shape,
    _snapshot_times,
    _step_count,
    _time_step,
    _validate_sponge_damping,
    _validated_obstacle,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import NDArray

    from .._i18n import Language
    from ._backends import DeviceArray
    from ._remote.client import Expected
    from .compute import Compute, RunProvenance

Field = Literal["p", "vx", "vy"]

__all__ = [
    "AIR",
    "CONCRETE",
    "STEEL",
    "WATER",
    "ElasticBoundaries",
    "ElasticFDTD2D",
    "ElasticFDTDResult",
    "ElasticRecording",
    "ElasticRun",
    "ExplosionSource",
    "ForceSource",
    "Material",
    "elastic_fdtd_simulation",
    "scholte_speed",
    "ALUMINUM",
]

#: Boundary-condition names accepted by :func:`elastic_fdtd_simulation`.
#: How a side of the elastic domain is terminated, by name.
ElasticBoundary = Literal["rigid", "absorbing", "free"]
_BOUNDARY_NAMES: tuple[ElasticBoundary, ...] = ("rigid", "absorbing", "free")

#: Force directions accepted by :class:`ForceSource`.
_DIRECTIONS = ("x", "y")

#: Fields a probe or a snapshot can record.
_FIELD_NAMES: tuple[Field, ...] = ("p", "vx", "vy")

#: Smallest grid extent per axis (in cells) the staggered scheme supports:
#: an axis shorter than this has no interior faces or corners, so the velocity
#: field staggered across it and the shear stress txy would be empty arrays.
_MIN_GRID_CELLS = 2


@dataclass(frozen=True, kw_only=True)
class ExplosionSource(RichDisplay):
    r"""An isotropic (explosive) stress injection at one cell centre.

    Virieux (1986) drives an explosion with equal increments on both normal
    stresses at their shared node, which avoids the infinite amplitudes of a
    velocity-node source. The sign convention here is pressure-like: the
    waveform value is the injected compression, added as ``-s(t)`` to both
    ``txx`` and ``tyy`` so the synthetic pressure
    :math:`p = -(t_{xx} + t_{yy})/2` increases with a positive waveform (and
    a ``c_s = 0`` run reproduces the acoustic solver driven by the same
    waveform, sample by sample).

    ``waveform`` maps time in seconds to the injected pressure in pascals:
    any callable, typically the ``value`` method of a
    :class:`~phonometry.simulation.GaussianPulse`,
    :class:`~phonometry.simulation.CWSource` or
    :class:`~phonometry.simulation.SignalSource` (their own ``ix``/``iy``
    are not used here).

    :ivar ix: Source column (x) index; the cell centre is at
        :math:`x = (i_x + 0.5)\,\Delta x`.
    :ivar iy: Source row (y) index.
    :ivar waveform: Callable ``t -> s(t)`` in pascals.
    :ivar amplitude: Extra gain applied to ``waveform``.
    """

    ix: int
    iy: int
    waveform: Callable[[float], float]
    amplitude: float = 1.0

    def __post_init__(self) -> None:
        """Hold whole cell indices and reject a non-finite ``amplitude`` gain.

        :raises TypeError: if ``ix`` or ``iy`` is not a number.
        :raises ValueError: if ``ix`` or ``iy`` is not whole, or ``amplitude``
            is not finite.
        """
        _hold_cells(self, "ix", "iy")
        _finite("amplitude", self.amplitude)


@dataclass(frozen=True, kw_only=True)
class ForceSource(RichDisplay):
    """A directional body-force injection at one velocity node.

    The standard body-force term of the equation of motion (the ``f`` of the
    Moczo et al. 2007 formulation): each step the target velocity component
    receives ``dt * f(t) / (rho * dx**2)``, i.e. ``waveform`` is a line
    force per unit depth [N/m] spread over one cell. A vertical force just
    below a free surface reproduces Lamb's problem and launches the Rayleigh
    wave (Virieux 1986, Fig. 5).

    ``ix``/``iy`` index the staggered velocity array directly: for
    ``direction = "x"`` the x-face between cells ``ix`` and ``ix + 1``
    (position ``((ix + 1) * dx, (iy + 0.5) * dx)``), for
    ``direction = "y"`` the y-face between rows ``iy`` and ``iy + 1``
    (position ``((ix + 0.5) * dx, (iy + 1) * dx)``).

    :ivar ix: Source column index into the velocity array.
    :ivar iy: Source row index into the velocity array.
    :ivar direction: ``"x"`` (horizontal) or ``"y"`` (vertical, positive
        downward in the ``imshow`` axes).
    :ivar waveform: Callable ``t -> f(t)`` in newtons per metre of depth.
    :ivar amplitude: Extra gain applied to ``waveform``.
    """

    ix: int
    iy: int
    direction: Literal["x", "y"]
    waveform: Callable[[float], float]
    amplitude: float = 1.0

    def __post_init__(self) -> None:
        """Hold the cell indices as ints and check the gain and the direction.

        :raises TypeError: if ``ix`` or ``iy`` is not a number.
        :raises ValueError: if ``ix`` or ``iy`` is not whole, ``amplitude`` is
            not finite, or ``direction`` is not ``"x"`` or ``"y"``.
        """
        _hold_cells(self, "ix", "iy")
        _finite("amplitude", self.amplitude)
        if self.direction not in _DIRECTIONS:
            msg = "direction must be 'x' or 'y'"
            raise ValueError(msg)


ElasticSource = ExplosionSource | ForceSource


@dataclass(frozen=True, kw_only=True)
class Material(RichDisplay):
    r"""An isotropic elastic medium as measurable wave speeds and density.

    The three numbers the solver's material maps are built from: the
    compressional speed :math:`c_\mathrm{P} = \sqrt{(\lambda + 2\mu) / \rho}`,
    the shear
    speed :math:`c_\mathrm{S} = \sqrt{\mu / \rho}` and the density ``rho``.
    ``c_s = 0``
    marks a fluid (the acoustic ``mu = 0`` limit of the elastic scheme,
    Virieux 1986), so the same dataclass names both fluids and solids.
    Every material must satisfy :math:`c_\mathrm{P}^2 \ge 2 c_\mathrm{S}^2`
    (non-negative first
    Lame parameter), the constructor bound of :class:`ElasticFDTD2D`.

    The module constants :data:`AIR`, :data:`WATER`, :data:`STEEL`,
    :data:`ALUMINUM` and :data:`CONCRETE` carry the nominal round-number
    properties used throughout the documentation and the validation suite,
    mirroring the documented default media of the acoustic solver.

    Wherever a :class:`Material` is taken, a solid's catalogue row is taken
    too, one of :data:`~phonometry.solids.PUBLISHED_SOLIDS` or one read from
    a catalogue file of your own: its bulk longitudinal speed, its transverse
    speed and its density are read through
    :meth:`~phonometry.io.CatalogueRow.printed`, which refuses a cell the
    page does not print, in the page's own terms. The plate and bar speeds a
    table prints beside them are never read, because they are not the bulk
    speed this solver integrates.

    :ivar c_p: Compressional (P) wave speed [m/s], strictly positive.
    :ivar c_s: Shear (S) wave speed [m/s], non-negative; 0 marks a fluid.
    :ivar rho: Density [kg/m3], strictly positive.
    """

    c_p: float
    c_s: float
    rho: float

    def __post_init__(self) -> None:
        """Reject non-positive ``c_p``/``rho``, negative ``c_s`` and negative lambda."""
        c_p = _positive_finite("c_p", self.c_p)
        c_s = _finite("c_s", self.c_s)
        if c_s < 0.0:
            msg = "c_s must be non-negative (0 marks a fluid)"
            raise ValueError(msg)
        rho = _positive_finite("rho", self.rho)
        if c_p**2 < 2.0 * c_s**2 * (1.0 - 1e-9):
            msg = "c_p**2 must be at least 2 * c_s**2 (non-negative lambda)"
            raise ValueError(msg)
        object.__setattr__(self, "c_p", c_p)
        object.__setattr__(self, "c_s", c_s)
        object.__setattr__(self, "rho", rho)

    @property
    def is_fluid(self) -> bool:
        """``True`` when the material carries no shear (``c_s = 0``)."""
        return self.c_s <= 0.0


#: Air at room conditions (fluid), the acoustic solver's default medium.
AIR = Material(c_p=343.0, c_s=0.0, rho=1.2)

#: Fresh water at room temperature (fluid).
WATER = Material(c_p=1480.0, c_s=0.0, rho=1000.0)

# The three solids below carry **bulk** wave speeds, the quantities this solver
# integrates: c_p from (lambda + 2 mu) / rho and c_s from mu / rho, both in an
# unbounded medium. All three come from one page, Bies 5e Table C.1: the density
# is what it prints, and the two speeds follow from the modulus and the Poisson
# ratio printed beside that density, through the closed forms printed at the end
# of the same table. So the citation covers the values and the arithmetic that
# produced them, and no number here is a remembered one.
#
# They were nominal until that page was read, and their three densities were
# already the ones it prints, which is what made these rows the right ones to
# finish the job with. `test_each_material_is_the_row_it_cites` recomputes all
# six speeds from the catalogue on every run, so a constant here cannot drift
# away from the page it names.
#
# What the citation has to avoid is worth keeping written down, because the
# obvious candidate is the wrong one: EN 12354-1 Table B.3 tabulates the
# quasi-longitudinal phase velocity of a *plate*, sqrt(E / (rho (1 - nu^2))),
# which is a different quantity from the bulk c_p,
# sqrt(E (1 - nu) / (rho (1 + nu) (1 - 2 nu))). For steel the two are 5 291 and
# 5 856 m/s, an eleven per cent gap that grows to fifteen for aluminium; the
# table also lists neither steel nor aluminium at all. Reading c_L into c_p
# would put the wrong physics behind a citation.

#: Structural steel, from Bies 5e Table C.1 row "Steel (mild)", PDF page 747
#: (printed p. 718): rho = 7850 kg/m3 as printed, with the two speeds from the
#: E = 207 GPa and nu = 0,30 printed beside it.
STEEL = Material(c_p=5958.0, c_s=3184.7, rho=7850.0)

#: Aluminium, from Bies 5e Table C.1 row "Aluminum sheet", PDF page 747
#: (printed p. 718): rho = 2700 kg/m3 as printed, with the two speeds from the
#: E = 70 GPa and nu = 0,35 printed beside it.
ALUMINUM = Material(c_p=6450.5, c_s=3098.7, rho=2700.0)

#: Dense concrete, from Bies 5e Table C.1 row "Concrete (high strength)", PDF
#: page 748 (printed p. 719): rho = 2400 kg/m3 as printed, with the two speeds
#: from the E = 30 GPa and nu = 0,20 printed beside it.
CONCRETE = Material(c_p=3726.8, c_s=2282.2, rho=2400.0)


#: The three cells of a solid's catalogue row the solver reads: the bulk
#: longitudinal speed, the transverse speed and the density, in the order of
#: :class:`Material`'s fields. A row's plate speed, bar speed and the
#: longitudinal speed a page prints without saying which it is are not among
#: them, for the reason the comment above the three solids gives.
_ROW_CELLS = ("bulk_longitudinal_speed_m_s", "transverse_speed_m_s", "density_kg_m3")

#: Who wants the three cells, as a refusal names it.
_WANTED_BY = "the elastic FDTD"


def _material_of_row(name: str, row: CatalogueRow) -> Material:
    """The medium a solid's catalogue row describes.

    Any row class that has the three cells of :data:`_ROW_CELLS` is taken,
    :class:`~phonometry.solids.SolidMaterial` and a caller's subclass of it
    among them; the cells are read through
    :meth:`~phonometry.io.CatalogueRow.printed`, so a cell the page leaves
    empty, prints as a range or declares as a bound is refused with what the
    page has there. A row whose completion could work the bulk speed out of
    the cells its page prints (a modulus, a Poisson ratio and a density, or
    a plate speed with them) already holds it, marked as derived.

    :raises TypeError: for a row of a class that lacks any of those cells.
    :raises ValueError: for a cell the row does not hold a number in, or for
        speeds no isotropic solid has.
    """
    held = {item.name for item in dataclasses.fields(row)}
    missing = [cell for cell in _ROW_CELLS if cell not in held]
    if missing:
        msg = (
            f"{name} is a {type(row).__name__} row, which has no "
            f"{' or '.join(missing)}; the elastic FDTD reads the bulk "
            "longitudinal speed, the transverse speed and the density of a "
            "solid's row, such as a solids.SolidMaterial"
        )
        raise TypeError(msg)
    c_p, c_s, rho = (row.printed(cell, wanted_by=_WANTED_BY) for cell in _ROW_CELLS)
    try:
        return Material(c_p=c_p, c_s=c_s, rho=rho)
    except ValueError as error:
        msg = (
            f"{name}: {row.name!r} ({row.source}) is not a medium this solver "
            f"takes: {error}"
        )
        raise ValueError(msg) from error


def _as_material(name: str, value: object) -> Material:
    """Coerce a :class:`Material`, a solid's row or a ``(c_p, c_s, rho)`` triple."""
    if isinstance(value, Material):
        return value
    if isinstance(value, CatalogueRow):
        return _material_of_row(name, value)
    # The length of a fixed-size argument, not a quantity.
    if isinstance(value, Sequence) and not isinstance(value, str) and len(value) == 3:  # noqa: PLR2004
        c_p, c_s, rho = (float(np.real(v)) for v in value)
        return Material(c_p=c_p, c_s=c_s, rho=rho)
    msg = (
        f"{name} must be a Material, a solid's catalogue row or a "
        "(c_p, c_s, rho) triple"
    )
    raise TypeError(msg)


def scholte_speed(
    fluid: Material | CatalogueRow | tuple[float, float, float],
    solid: Material | CatalogueRow | tuple[float, float, float],
) -> float:
    r"""Exact Scholte-wave speed of a fluid over an elastic half-space [m/s].

    The Scholte wave is the true interface wave of a fluid-solid contact:
    evanescent on both sides, elliptical particle motion, no low-frequency
    cut-off, and non-dispersive over homogeneous half-spaces (Jensen,
    Kuperman, Porter & Schmidt, *Computational Ocean Acoustics* 2e,
    Sections 4.5.2 and 8.5.4). Its speed ``v`` lies below both the fluid
    sound speed and the solid shear speed, and solves the exact
    characteristic equation of Brekhovskikh & Godin, *Acoustics of Layered
    Media I* (1990), Eq. 4.4.20, written in the notation of Eq. 4.4.18
    (:math:`q = c_\mathrm{S}^2/c_\mathrm{P}^2`, :math:`r = c_\mathrm{S}^2/c^2`,
    :math:`s = v^2/c_\mathrm{S}^2`,
    :math:`m = \rho_{\mathrm{solid}}/\rho_{\mathrm{fluid}}`):

    .. math::

       4 \sqrt{1-s} \sqrt{1-qs} - (2-s)^2
       = \frac{s^2}{m} \sqrt{\frac{1-sq}{1-sr}}

    A root always exists (B&G Section 4.4.3); the :math:`m \to \infty`
    limit of the left side is the Rayleigh equation. For stiff beds the
    root hugs the fluid speed (water over steel: 1479.6 m/s, 0.027 % below
    ``c``) while for soft sediments it drops well below it, which is why
    measured seabed interface waves probe the sediment shear speed
    (:math:`v \approx 0.85 c_\mathrm{S}` rule, Jensen et al. Section 5.10.5).

    :param fluid: Fluid half-space: a :class:`Material` with ``c_s = 0``
        (or a ``(c_p, 0.0, rho)`` triple).
    :param solid: Elastic half-space: a :class:`Material` with ``c_s > 0``,
        a ``(c_p, c_s, rho)`` triple or a solid's catalogue row
        (:class:`~phonometry.solids.SolidMaterial`), whose bulk
        longitudinal speed, transverse speed and density are read through
        :meth:`~phonometry.io.CatalogueRow.printed`.
    :return: The Scholte-wave phase speed [m/s].
    :raises ValueError: If ``fluid`` carries shear or ``solid`` does not, or
        a row does not print one of the three numbers, in the row's terms.
    :raises TypeError: For a catalogue row of a class that lacks any of the
        bulk longitudinal speed, the transverse speed and the density.
    """
    flu = _as_material("fluid", fluid)
    sol = _as_material("solid", solid)
    if not flu.is_fluid:
        msg = "fluid must have c_s = 0"
        raise ValueError(msg)
    if sol.is_fluid:
        msg = "solid must have c_s > 0"
        raise ValueError(msg)
    q = sol.c_s**2 / sol.c_p**2
    r = sol.c_s**2 / flu.c_p**2
    m = sol.rho / flu.rho

    def characteristic(s: float) -> float:
        # B&G Eq. 4.4.20 rearranged to LHS - RHS; real and single-signed
        # branches over 0 < s < min(1, 1/r), where v < min(c, c_S).
        return float(
            4.0 * np.sqrt(1.0 - s) * np.sqrt(1.0 - q * s)
            - (2.0 - s) ** 2
            - (s**2 / m) * np.sqrt((1.0 - s * q) / (1.0 - s * r))
        )

    # The function is positive as s -> 0+ (expansion 2 s (1 - q) + O(s^2))
    # and diverges to -inf at the upper end, so a sign sweep brackets every
    # root; the largest one is the Scholte root.
    s_hi = min(1.0, 1.0 / r) * (1.0 - 1e-12)
    grid = np.linspace(1e-9, s_hi, 4001)
    values = np.array([characteristic(s) for s in grid])
    signs = np.sign(values)
    crossings = np.nonzero(np.diff(signs) != 0)[0]
    if crossings.size == 0:  # pragma: no cover - a root always exists
        msg = "no Scholte root found; check the material pair"
        raise ValueError(msg)
    k = int(crossings[-1])
    root = float(brentq(characteristic, grid[k], grid[k + 1], xtol=1e-15, rtol=8.9e-16))
    return sol.c_s * float(np.sqrt(root))


def _resolve_speed_map(
    name: str, value: float | Field2D, shape: tuple[int, int] | None
) -> Field2D:
    """Broadcast/validate a wave-speed spec into a finite 2D map."""
    if np.isscalar(value):
        if shape is None:
            msg = f"shape is required when {name} is a scalar"
            raise ValueError(msg)
        out = np.full(shape, float(np.real(value)), dtype=np.float64)
    else:
        out = np.asarray(value, dtype=np.float64)
    # The number is a count of array axes, not a quantity.
    if out.ndim != 2:  # noqa: PLR2004
        msg = f"{name} must be a 2D (ny, nx) map"
        raise ValueError(msg)
    return out


def _resolve_free_sides(
    free_sides: str | Iterable[str] | None,
) -> tuple[str, ...]:
    """Normalise the free-surface side spec into a validated tuple."""
    if free_sides is None:
        return ()
    if isinstance(free_sides, str):
        # A bare string would iterate per character; treat it as one side.
        sides: tuple[str, ...] = (free_sides,)
    else:
        sides = tuple(free_sides)
    unknown = set(sides) - set(_SIDES)
    if unknown:
        msg = f"unknown free sides: {sorted(unknown)}"
        raise ValueError(msg)
    return sides


def _elastic_grid(
    c_p: float | Field2D, shape: tuple[int, int] | None, cfl: float, dx: float
) -> tuple[Field2D, float, float]:
    """The P-wave speed map, the grid spacing and the time step, checked on the host.

    :return: ``(cp_map, dx, dt)``; the step is bounded by ``c_p`` alone.
    """
    _require_courant(cfl)
    cp_map = _resolve_speed_map("c_p", c_p, shape)
    _positive_map("c_p", cp_map)
    ny, nx = cp_map.shape
    if ny < _MIN_GRID_CELLS or nx < _MIN_GRID_CELLS:
        msg = "the grid must be at least 2 x 2 cells"
        raise ValueError(msg)
    dx = _positive_finite("dx", dx)
    return cp_map, dx, _time_step(cfl, dx, float(cp_map.max()))


def _checked_shear_speed(c_s: float | Field2D, cp_map: Field2D) -> Field2D:
    """The S-wave speed map on the grid of *cp_map*, checked against it."""
    ny, nx = cp_map.shape
    cs_map = _resolve_speed_map("c_s", c_s, (ny, nx))
    if cs_map.shape != (ny, nx):
        msg = "c_s map must match the shape of c_p"
        raise ValueError(msg)
    if not np.all(np.isfinite(cs_map)) or bool(np.any(cs_map < 0.0)):
        msg = "c_s must be non-negative and finite everywhere"
        raise ValueError(msg)
    # lambda >= 0 <=> c_p**2 >= 2 c_s**2 (a small relative tolerance
    # admits c_s = c_p / sqrt(2) given in rounded floats).
    if bool(np.any(cp_map**2 < 2.0 * cs_map**2 * (1.0 - 1e-9))):
        msg = (
            "c_p**2 must be at least 2 * c_s**2 in every "
            "cell (non-negative lambda); c_s = 0 marks a "
            "fluid cell"
        )
        raise ValueError(msg)
    return cs_map


def _checked_density(rho: float | Field2D, ny: int, nx: int) -> Field2D:
    """The density map on the ``(ny, nx)`` grid, strictly positive."""
    rho_map = (
        np.full((ny, nx), float(np.real(rho)), dtype=np.float64)
        if np.isscalar(rho)
        else np.asarray(rho, dtype=np.float64)
    )
    if rho_map.shape != (ny, nx):
        msg = "rho map must match the shape of c_p"
        raise ValueError(msg)
    _positive_map("rho", rho_map)
    return rho_map


@dataclass(frozen=True)
class _ElasticMedium:
    """An elastic medium checked on the host, before any device is asked for.

    What :class:`ElasticFDTD2D` builds its maps from, and what an
    :class:`ElasticRun` checks when it is built: the same function checks
    both, so a bad argument raises the same error on every route.
    """

    cp_map: Field2D
    cs_map: Field2D
    rho_map: Field2D
    dx: float
    dt: float
    sponge_width: int
    sides: tuple[Side, ...]
    sponge_sides: tuple[Side, ...]
    damping_map: NDArray[np.float64]
    free_sides: tuple[str, ...]
    obstacle: NDArray[np.bool_] | None


def _elastic_medium(
    c_p: float | Field2D,
    c_s: float | Field2D,
    dx: float,
    *,
    rho: float | Field2D,
    cfl: float,
    sponge_width: int,
    sponge_sides: Side | Iterable[Side] | None,
    sponge_reflection: float,
    damping: float | NDArray[np.float64],
    shape: tuple[int, int] | None,
    free_sides: str | Iterable[str] | None,
    obstacle_mask: NDArray[np.bool_] | None,
) -> _ElasticMedium:
    """Check every argument of :class:`ElasticFDTD2D` that describes the medium.

    In the order the constructor always checked them: the grid, ``c_s``
    against ``c_p``, the density, the sponge and the damping, the sides,
    the free surfaces against the sponge, the obstacle. An
    :class:`ElasticRun` calls it too, when it is built.
    """
    cp_map, dx, dt = _elastic_grid(c_p, shape, cfl, dx)
    ny, nx = cp_map.shape
    cs_map = _checked_shear_speed(c_s, cp_map)
    rho_map = _checked_density(rho, ny, nx)
    width, damping_map = _validate_sponge_damping(
        sponge_width, sponge_reflection, damping, ny, nx
    )
    sides = _resolve_sponge_sides(sponge_sides)
    width = require_count(width, "sponge_width", at_least=None)
    used = sides if width > 0 else ()
    free = _resolve_free_sides(free_sides)
    overlap = set(free) & set(used)
    if overlap:
        msg = f"sides {sorted(overlap)} cannot be both free and absorbing"
        raise ValueError(msg)
    return _ElasticMedium(
        cp_map=cp_map,
        cs_map=cs_map,
        rho_map=rho_map,
        dx=dx,
        dt=dt,
        sponge_width=width,
        sides=sides,
        sponge_sides=used,
        damping_map=damping_map,
        free_sides=free,
        obstacle=_validated_obstacle(obstacle_mask, ny, nx),
    )


def _check_elastic_source(
    source: ElasticSource,
    shape: tuple[int, ...],
    obstacle: NDArray[np.bool_] | None,
) -> None:
    """Refuse a source off the grid ``(ny, nx)`` or inside the obstacle.

    Shared by :meth:`ElasticFDTD2D.add_source` and :class:`ElasticRun`,
    which checks its sources against the grid when the run is built.
    """
    ix = _integer("source ix", source.ix)
    iy = _integer("source iy", source.iy)
    if isinstance(source, ExplosionSource):
        _check_explosion_cell(ix, iy, shape, obstacle)
    else:
        _check_force_node(source, ix, iy, shape, obstacle)


def _check_explosion_cell(
    ix: int, iy: int, shape: tuple[int, ...], obstacle: NDArray[np.bool_] | None
) -> None:
    """Check an explosion cell against the grid and the obstacle mask."""
    require_scalar(ix, "ix")
    require_scalar(iy, "iy")
    ny, nx = shape
    if not (0 <= ix < nx and 0 <= iy < ny):
        msg = "source position lies outside the grid"
        raise ValueError(msg)
    if obstacle is not None and obstacle[iy, ix]:
        msg = "source position lies inside an obstacle"
        raise ValueError(msg)


def _check_force_node(
    source: ForceSource,
    ix: int,
    iy: int,
    shape: tuple[int, ...],
    obstacle: NDArray[np.bool_] | None,
) -> None:
    """Check a force velocity node against the grid and the obstacle."""
    require_scalar(ix, "ix")
    require_scalar(iy, "iy")
    ny, nx = shape
    along_x = source.direction == "x"
    limit = (ny, nx - 1) if along_x else (ny - 1, nx)
    if not (0 <= ix < limit[1] and 0 <= iy < limit[0]):
        msg = "source position lies outside the grid"
        raise ValueError(msg)
    # The face is closed when either cell it separates is an obstacle cell,
    # the rule the open-face factors of the step are built from; it is read
    # from the host mask, not from those device factors.
    if obstacle is not None and (
        obstacle[iy, ix] or (obstacle[iy, ix + 1] if along_x else obstacle[iy + 1, ix])
    ):
        msg = "source position lies inside an obstacle"
        raise ValueError(msg)


class ElasticFDTD2D:
    r"""2D elastic (P-SV) FDTD stepping engine on a staggered grid.

    The Virieux (1986) cell is shifted half a cell so it lands on the layout
    of the acoustic :class:`~phonometry.simulation.FDTD2D`: the normal
    stresses ``txx`` and ``tyy`` share the cell centres, shape ``(ny, nx)``
    (row = y, column = x, the ``imshow`` convention; Virieux's downward z is
    the growing row here); ``vx`` lives at interior x-faces, shape
    ``(ny, nx - 1)``; ``vy`` at interior y-faces, shape ``(ny - 1, nx)``;
    the shear stress ``txy`` at interior corners, shape ``(ny - 1, nx - 1)``.
    Because only interior faces are stored, the domain boundary has zero
    normal velocity by construction and, with the corner shear stress taken
    as zero on the edge, is a shear-free rigid wall; ``free_sides`` turns
    selected sides into traction-free surfaces via stress imaging and sponge
    layers into absorbing ones. Material maps are given as the measurable
    wave speeds and converted internally to the Lame parameters
    :math:`\mu = \rho c_\mathrm{S}^2` and
    :math:`\lambda = \rho (c_\mathrm{P}^2 - 2 c_\mathrm{S}^2)`;
    density is
    arithmetically averaged onto the faces and ``mu`` harmonically averaged
    onto the corners (zero whenever any neighbour is a fluid), the Moczo
    et al. (2007) effective parameters (Eqs. 7.37-7.39) that make internal
    interfaces converge to the physical traction continuity.

    :param c_p: P-wave speed map [m/s], shape ``(ny, nx)``. A scalar with an
        explicit ``shape`` is also accepted.
    :param c_s: S-wave speed map [m/s]; scalar or ``(ny, nx)`` array.
        ``c_s = 0`` marks a fluid cell (the acoustic limit); every cell must
        satisfy :math:`c_\mathrm{P}^2 \ge 2 c_\mathrm{S}^2` (non-negative
        ``lambda``).
    :param dx: Grid spacing [m] (square cells).
    :param rho: Density map [kg/m3]; scalar or ``(ny, nx)`` array.
    :param cfl: Courant number
        :math:`C_\mathrm{N} = c_{\mathrm{p},\max}\, \Delta t \sqrt{2} / \Delta x`; the scheme
        is stable for :math:`C_\mathrm{N} < 1` (Virieux Eqs. 6-7, a bound on ``c_P``
        alone, independent of ``c_S`` and of the Poisson ratio) and values
        in ``(0, 1)`` are accepted. The default 0.6 keeps a wide stability
        margin with moderate numerical dispersion.
    :param sponge_width: Thickness of the absorbing layer in cells
        (0 = no absorbing sides).
    :param sponge_sides: Which sides absorb: a single side name or an
        iterable drawn from ``{"left", "right", "top", "bottom"}``
        (default: all four when ``sponge_width > 0``).
    :param sponge_reflection: Target round-trip amplitude reflection of the
        sponge layer; sets the peak absorption rate.
    :param damping: Bulk amplitude decay rate [1/s]: a scalar for the whole
        field or an ``(ny, nx)`` map for locally lossy regions.
    :param shape: Grid shape ``(ny, nx)``, required only when ``c_p`` is a
        scalar.
    :param free_sides: Sides carrying a traction-free surface (stress
        imaging, Moczo et al. Eq. 9.9): the surface plane runs through the
        boundary row/column of cell centres, the normal stress is pinned to
        zero there and the shear stress is imaged antisymmetrically above
        it. A side cannot be both free and absorbing.
    :param obstacle_mask: Boolean map, shape ``(ny, nx)``, of rigid cells:
        every face adjacent to a masked cell is closed (zero normal
        velocity) and every touching corner shear stress is zeroed, i.e. a
        shear-free rigid inclusion, rasterising arbitrary interior geometry.
    :param compute: Where the engine steps (:class:`Compute`); ``None``
        follows :func:`use`, then ``PHONOMETRY_COMPUTE``, then NumPy.
    :raises TypeError: if ``cfl`` is not a single number, ``sponge_width`` is a flag,
        a text or an array where a count goes, or ``compute`` is neither a
        :class:`Compute` nor ``None``.
    :raises ValueError: for an argument out of its range, and for a ``compute``
        that names a host: an engine steps in this process, and only
        :func:`elastic_fdtd_simulation` runs on a node.
    :raises ComputeImportError: when the library of the device ``compute``
        asks for is not installed or does not import.
    :raises ComputeDeviceError: when that device is not present, or fails a
        first small computation; with ``fallback=True`` the engine warns
        with :class:`ComputeFallbackWarning` and steps on NumPy instead.
    """

    def __init__(
        self,
        c_p: float | Field2D,
        c_s: float | Field2D,
        dx: float,
        *,
        rho: float | Field2D,
        cfl: float = 0.6,
        sponge_width: int = 0,
        sponge_sides: Side | Iterable[Side] | None = None,
        sponge_reflection: float = _DEFAULT_SPONGE_REFLECTION,
        damping: float | NDArray[np.float64] = 0.0,
        shape: tuple[int, int] | None = None,
        free_sides: str | Iterable[str] | None = None,
        obstacle_mask: NDArray[np.bool_] | None = None,
        compute: Compute | None = None,
    ) -> None:
        medium = _elastic_medium(
            c_p,
            c_s,
            dx,
            rho=rho,
            cfl=cfl,
            sponge_width=sponge_width,
            sponge_sides=sponge_sides,
            sponge_reflection=sponge_reflection,
            damping=damping,
            shape=shape,
            free_sides=free_sides,
            obstacle_mask=obstacle_mask,
        )
        cp_map, cs_map, rho_map = medium.cp_map, medium.cs_map, medium.rho_map
        self.dx, self.dt = medium.dx, medium.dt
        ny, nx = cp_map.shape
        #: Sponge-layer width in cells (read-only configuration record).
        self.sponge_width = medium.sponge_width
        #: Sides carrying a sponge layer when ``sponge_width > 0``.
        self.sponge_sides: tuple[str, ...] = medium.sponge_sides
        #: Sides carrying a traction-free surface (immutable record).
        self.free_sides: tuple[str, ...] = medium.free_sides
        self._obstacle: NDArray[np.bool_] | None = medium.obstacle

        # Every argument is checked on the host before the device is asked
        # for, so a bad one raises its own error, never a missing library's
        # or a fallback warning first. Then a host is refused: an engine
        # steps in this process.
        backend = _backends.backend_for(_local_request(compute, owner="ElasticFDTD2D"))
        self._backend = backend
        self._xp = backend.xp
        # Read-only copies of their own, so the maps the simulation reports
        # stay the ones mu, lam and dt were computed from.
        self.c_p = read_only_copy(cp_map)
        self.c_s = read_only_copy(cs_map)
        self.rho = read_only_copy(rho_map)
        c_max = float(cp_map.max())
        #: Shear modulus ``mu = rho c_s**2`` at cell centres, a read-only
        #: host copy.
        self.mu = read_only_copy(rho_map * cs_map**2)
        #: First Lame parameter ``lambda = rho (c_p**2 - 2 c_s**2)``, a
        #: read-only host copy.
        self.lam = read_only_copy(
            np.maximum(rho_map * (cp_map**2 - 2.0 * cs_map**2), 0.0)
        )
        mu2 = 2.0 * self.mu
        # Plane-strain surface modulus E' = 4 mu (lambda + mu) /
        # (lambda + 2 mu): on a free surface the zero normal stress ties
        # the normal strain rate to the tangential one, and the in-plane
        # stress evolves with E' times the tangential strain rate alone.
        e_surf = np.divide(
            4.0 * self.mu * (self.lam + self.mu),
            self.lam + mu2,
            out=np.zeros_like(self.mu),
            where=(self.lam + mu2) > 0.0,
        )
        # Density averaged onto the faces where each velocity lives
        # (arithmetic mean, Moczo et al. Eq. 7.39), kept on the host for the
        # force sources and on the device for the step.
        rho_x = 0.5 * (rho_map[:, 1:] + rho_map[:, :-1])
        rho_y = 0.5 * (rho_map[1:, :] + rho_map[:-1, :])
        self._rho_x_host, self._rho_y_host = rho_x, rho_y
        mu_c = self._corner_mu(self.mu)
        # The maps the step reads, each handed to the device once.
        self._lam = backend.asarray(self.lam)
        self._mu = backend.asarray(self.mu)
        self._mu2 = backend.asarray(mu2)
        self._e_surf = backend.asarray(e_surf)
        self._rho_x = backend.asarray(rho_x)
        self._rho_y = backend.asarray(rho_y)
        self._mu_c = backend.asarray(mu_c)

        self.txx = backend.zeros((ny, nx))
        self.tyy = backend.zeros((ny, nx))
        self.txy = backend.zeros((ny - 1, nx - 1))
        self.vx = backend.zeros((ny, nx - 1))
        self.vy = backend.zeros((ny - 1, nx))
        self._div = backend.zeros((ny, nx))
        self._dvx = backend.zeros((ny, nx))
        self._dvy = backend.zeros((ny, nx))
        self._dty = backend.zeros((ny, nx - 1))
        self._dtx = backend.zeros((ny - 1, nx))
        self._sources: list[ElasticSource] = []
        self.n = 0  # completed steps

        self._init_decay(
            medium.sides,
            medium.sponge_width,
            sponge_reflection,
            medium.damping_map,
            c_max,
        )
        self._init_obstacle()

    @classmethod
    def from_regions(
        cls,
        shape: tuple[int, int],
        dx: float,
        *,
        background: Material | CatalogueRow | tuple[float, float, float],
        regions: Iterable[
            tuple[Any, Material | CatalogueRow | tuple[float, float, float]]
        ] = (),
        **kwargs: Any,
    ) -> ElasticFDTD2D:
        """Build the engine from named materials painted over a background.

        Thin sugar over the map constructor for the common layered set-ups
        (fluid over a solid half-space, an immersed plate, an inclusion):
        the ``(ny, nx)`` maps of ``c_p``, ``c_s`` and ``rho`` start uniform
        at ``background`` and each ``(where, material)`` entry of
        ``regions`` is painted over them in order (later entries overwrite
        earlier ones), then everything is delegated to the normal
        constructor. No new physics: a fluid-solid contact still needs no
        explicit interface treatment, because the constructor's effective
        parameters (Moczo et al. 2007, Eqs. 7.37-7.39) handle it from the
        maps alone.

        ``where`` selects the painted cells: a boolean ``(ny, nx)`` mask,
        or any basic numpy index expression over the ``(row, column)``
        maps, e.g. ``(slice(120, None), slice(None))`` for the lower half
        or ``numpy.s_[120:, :]`` for the same thing spelled as a slice.

        :param shape: Grid shape ``(ny, nx)``.
        :param dx: Grid spacing [m] (square cells).
        :param background: The material filling the whole grid first: a
            :class:`Material`, a ``(c_p, c_s, rho)`` triple, e.g.
            :data:`WATER`, or a solid's catalogue row
            (:class:`~phonometry.solids.SolidMaterial`), whose bulk
            longitudinal speed, transverse speed and density are read
            through :meth:`~phonometry.io.CatalogueRow.printed`.
        :param regions: ``(where, material)`` pairs painted in order, each
            material taken in any of the forms ``background`` takes.
        :param kwargs: Forwarded to :class:`ElasticFDTD2D` (``cfl``,
            ``sponge_width``, ``sponge_sides``, ``sponge_reflection``,
            ``damping``, ``free_sides``, ``obstacle_mask``, ``compute``).
        :return: The configured stepping engine.
        :raises ValueError: If a mask does not match ``shape`` or a
            material spec is invalid, a catalogue row's refusal among them,
            or a ``compute`` keyword names a host: the engine steps in this
            process.
        :raises TypeError: For a mask array that is not boolean, a
            catalogue row of a class that lacks any of the bulk longitudinal
            speed, the transverse speed and the density, or a ``compute``
            keyword that is neither a :class:`Compute` nor ``None``.
        :raises ComputeImportError: When the library of the device a
            ``compute`` keyword asks for is not installed or does not import.
        :raises ComputeDeviceError: When that device is not present, or fails
            a first small computation; with ``fallback=True`` the engine warns
            with :class:`ComputeFallbackWarning`, pointing at the line that
            called this method, and steps on NumPy instead.
        """
        ny = _integer("shape[0]", shape[0])
        nx = _integer("shape[1]", shape[1])
        if ny < _MIN_GRID_CELLS or nx < _MIN_GRID_CELLS:
            msg = "the grid must be at least 2 x 2 cells"
            raise ValueError(msg)
        bg = _as_material("background", background)
        c_p = np.full((ny, nx), bg.c_p, dtype=np.float64)
        c_s = np.full((ny, nx), bg.c_s, dtype=np.float64)
        rho = np.full((ny, nx), bg.rho, dtype=np.float64)
        for k, (where, material) in enumerate(regions):
            mat = _as_material(f"regions[{k}]", material)
            index = where
            if isinstance(index, np.ndarray):
                msg = f"regions[{k}] mask must be a boolean array of shape {(ny, nx)}"
                if index.dtype != np.bool_:
                    raise TypeError(msg)
                if index.shape != (ny, nx):
                    raise ValueError(msg)
            c_p[index] = mat.c_p
            c_s[index] = mat.c_s
            rho[index] = mat.rho
        return cls(c_p, c_s, dx, rho=rho, **kwargs)

    @staticmethod
    def _corner_mu(mu: Field2D) -> Field2D:
        """Harmonic mean of ``mu`` over the 4 cells meeting at each corner.

        The Moczo et al. (2007) effective shear modulus (Eqs. 7.37-7.38):
        the harmonic mean enforces traction continuity across internal
        interfaces, and any fluid neighbour (``mu = 0``) zeroes the corner,
        which is exactly the shear-free wetted-wall condition of a
        fluid-solid contact (Virieux 1986).
        """
        quads = (mu[:-1, :-1], mu[:-1, 1:], mu[1:, :-1], mu[1:, 1:])
        all_solid = np.logical_and.reduce([q > 0.0 for q in quads])
        inv_sum = np.zeros_like(quads[0])
        for q in quads:
            inv_sum += np.divide(1.0, q, out=np.zeros_like(q), where=q > 0.0)
        return np.where(all_solid, 4.0 / np.where(inv_sum > 0.0, inv_sum, 1.0), 0.0)

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
            self.txx.shape,
            sides,
            sponge_width,
            sponge_reflection,
            damping,
            c_max,
            self.dx,
        )
        backend = self._backend
        self._decay_c = backend.asarray(np.exp(-sigma * self.dt))
        self._decay_vx = backend.asarray(
            np.exp(-(0.5 * (sigma[:, 1:] + sigma[:, :-1])) * self.dt)
        )
        self._decay_vy = backend.asarray(
            np.exp(-(0.5 * (sigma[1:, :] + sigma[:-1, :])) * self.dt)
        )
        self._decay_xy = backend.asarray(
            np.exp(
                -(
                    0.25
                    * (
                        sigma[1:, 1:]
                        + sigma[1:, :-1]
                        + sigma[:-1, 1:]
                        + sigma[:-1, :-1]
                    )
                )
                * self.dt
            )
        )

    def _init_obstacle(self) -> None:
        """Turn the validated obstacle mask into closed-face and corner factors on the device."""
        self._vx_open: DeviceArray | None = None
        self._vy_open: DeviceArray | None = None
        self._txy_open: DeviceArray | None = None
        if self._obstacle is not None:
            mask = self._obstacle
            backend = self._backend
            # A face between two cells is open only when both are open
            # (rigid obstacle boundary: zero normal velocity), and a corner
            # shear stress survives only when all four cells are open
            # (shear-free rigid inclusion, matching the domain edges).
            self._vx_open = backend.asarray(
                (~(mask[:, 1:] | mask[:, :-1])).astype(np.float64)
            )
            self._vy_open = backend.asarray(
                (~(mask[1:, :] | mask[:-1, :])).astype(np.float64)
            )
            self._txy_open = backend.asarray(
                (
                    ~(mask[1:, 1:] | mask[1:, :-1] | mask[:-1, 1:] | mask[:-1, :-1])
                ).astype(np.float64)
            )

    @property
    def time(self) -> float:
        """Elapsed simulated time [s]."""
        return self.n * self.dt

    @property
    # The array type is the backend's, and the Array API standard does not name one.
    def p(self) -> Any:  # noqa: ANN401
        """Synthetic pressure ``-(txx + tyy) / 2`` at cell centres [Pa].

        The mean compressive normal stress: in fluid (``c_s = 0``) regions
        it is exactly the acoustic pressure, and in solids it is the
        convenient scalar for probes and snapshots. It is computed on the
        engine's device, where the stresses live: a NumPy array by default,
        the backend's own array on another device; :meth:`host_field` gives
        host copies of the stresses it is built from.
        """
        with self._backend.context():
            return -0.5 * (self.txx + self.tyy)

    def add_source(self, source: ElasticSource) -> None:
        """Register an :class:`ExplosionSource` or a :class:`ForceSource`.

        Explosions inject additively at one cell centre; forces at one
        staggered velocity node. Positions are validated against the grid
        and the obstacle mask.
        """
        _check_elastic_source(source, self.c_p.shape, self._obstacle)
        self._sources.append(source)

    def step(self) -> None:
        """Advance the leapfrog scheme by one time step (Virieux Eq. 5)."""
        with self._backend.context():
            self._step()

    def _step(self) -> None:
        """One leapfrog step on the backend's arrays."""
        dt_dx = self.dt / self.dx
        txx, tyy = self.txx, self.tyy
        # Velocity half-step from the stress gradients; the one-sided txy
        # differences fold in the shear-free rigid edges and the imaged
        # free surfaces.
        self.vx += (
            dt_dx / self._rho_x * ((txx[:, 1:] - txx[:, :-1]) + self._shear_dty())
        )
        self.vy += (
            dt_dx / self._rho_y * ((tyy[1:, :] - tyy[:-1, :]) + self._shear_dtx())
        )
        if self._vx_open is not None and self._vy_open is not None:
            self.vx *= self._vx_open
            self.vy *= self._vy_open
        t_half = (self.n + 0.5) * self.dt
        for src in self._sources:
            if isinstance(src, ForceSource):
                self._inject_force(src, t_half)
        self.vx *= self._decay_vx
        self.vy *= self._decay_vy
        # Stress step from the velocity gradients (Hooke's law in rate
        # form): txx and tyy share the lambda * div(v) part, plus 2 mu
        # times their own normal strain rate; txy is driven by the shear
        # strain rate through the corner-averaged mu. Free surfaces stash
        # their E' in-plane stress first and rewrite it after the bulk
        # update.
        div, dvx, dvy = self._velocity_gradients()
        txx_surf, tyy_surf = self._stash_surface_stress(dt_dx, dvx, dvy)
        self.txx += self._lam * dt_dx * div + self._mu2 * dt_dx * dvx
        self.tyy += self._lam * dt_dx * div + self._mu2 * dt_dx * dvy
        self.txy += (
            self._mu_c
            * dt_dx
            * ((self.vx[1:, :] - self.vx[:-1, :]) + (self.vy[:, 1:] - self.vy[:, :-1]))
        )
        if self._txy_open is not None:
            self.txy *= self._txy_open
        # Pin the free surfaces before the sources, so a stress source on
        # the surface row acts as a boundary traction drive.
        self._apply_free_surfaces(txx_surf, tyy_surf)
        t_next = (self.n + 1) * self.dt
        for src in self._sources:
            if isinstance(src, ExplosionSource):
                inj = src.amplitude * src.waveform(t_next)
                self.txx[src.iy, src.ix] -= inj
                self.tyy[src.iy, src.ix] -= inj
        self.txx *= self._decay_c
        self.tyy *= self._decay_c
        self.txy *= self._decay_xy
        self.n += 1

    def _shear_dty(self) -> DeviceArray:
        r"""One-sided y-difference of txy, free surfaces imaged (Moczo 9.9).

        The shear stress is zero on the domain edge (shear-free rigid
        wall) except on free sides, where the antisymmetric image
        :math:`t_{xy}(-d) = -t_{xy}(+d)` about the surface plane doubles the
        one-sided difference.
        """
        txy, dty = self.txy, self._dty
        dty[0, :] = txy[0, :]
        dty[1:-1, :] = txy[1:, :] - txy[:-1, :]
        dty[-1, :] = -txy[-1, :]
        if "top" in self.free_sides:
            dty[0, :] *= 2.0
        if "bottom" in self.free_sides:
            dty[-1, :] *= 2.0
        return dty

    def _shear_dtx(self) -> DeviceArray:
        """One-sided x-difference of txy, free surfaces imaged (Moczo 9.9)."""
        txy, dtx = self.txy, self._dtx
        dtx[:, 0] = txy[:, 0]
        dtx[:, 1:-1] = txy[:, 1:] - txy[:, :-1]
        dtx[:, -1] = -txy[:, -1]
        if "left" in self.free_sides:
            dtx[:, 0] *= 2.0
        if "right" in self.free_sides:
            dtx[:, -1] *= 2.0
        return dtx

    def _velocity_gradients(
        self,
    ) -> tuple[DeviceArray, DeviceArray, DeviceArray]:
        """Velocity divergence and one-sided vx/vy differences at centres."""
        div = self._div
        div[...] = 0.0
        div[:, :-1] += self.vx
        div[:, 1:] -= self.vx
        div[:-1, :] += self.vy
        div[1:, :] -= self.vy
        dvx = self._dvx
        dvx[:, 0] = self.vx[:, 0]
        dvx[:, 1:-1] = self.vx[:, 1:] - self.vx[:, :-1]
        dvx[:, -1] = -self.vx[:, -1]
        dvy = self._dvy
        dvy[0, :] = self.vy[0, :]
        dvy[1:-1, :] = self.vy[1:, :] - self.vy[:-1, :]
        dvy[-1, :] = -self.vy[-1, :]
        return div, dvx, dvy

    def _surface_lines(
        self,
    ) -> tuple[tuple[tuple[bool, int], ...], tuple[tuple[bool, int], ...]]:
        """Free-surface (active, index) pairs for the rows and columns."""
        free = self.free_sides
        rows = (("top" in free, 0), ("bottom" in free, -1))
        cols = (("left" in free, 0), ("right" in free, -1))
        return rows, cols

    def _stash_surface_stress(
        self,
        dt_dx: float,
        dvx: DeviceArray,
        dvy: DeviceArray,
    ) -> tuple[list[DeviceArray], list[DeviceArray]]:
        """E'-updated in-plane stress of each free surface, pre-bulk-update.

        On a free-surface row/column the zero normal stress ties the
        normal strain rate to the tangential one, so the in-plane normal
        stress must evolve with E' times the tangential strain rate alone
        (the vy/vx value beyond the surface is vacuum, not the rigid
        edge).
        """
        surf_rows, surf_cols = self._surface_lines()
        txx_surf = [
            self.txx[k, :] + self._e_surf[k, :] * dt_dx * dvx[k, :]
            for on, k in surf_rows
            if on
        ]
        tyy_surf = [
            self.tyy[:, k] + self._e_surf[:, k] * dt_dx * dvy[:, k]
            for on, k in surf_cols
            if on
        ]
        return txx_surf, tyy_surf

    def _apply_free_surfaces(
        self,
        txx_surf: list[DeviceArray],
        tyy_surf: list[DeviceArray],
    ) -> None:
        """Pin the surface normal stress to zero and restore the E' update.

        Where two orthogonal free sides meet, the corner cell lies on both
        surface planes: pin both normal stresses to zero there (the
        sequential row/column passes would otherwise leave the later
        pass's E' value on the earlier pass's pinned stress).
        """
        surf_rows, surf_cols = self._surface_lines()
        it_rows = iter(txx_surf)
        for on, k in surf_rows:
            if on:
                self.tyy[k, :] = 0.0
                self.txx[k, :] = next(it_rows)
        it_cols = iter(tyy_surf)
        for on, k in surf_cols:
            if on:
                self.txx[:, k] = 0.0
                self.tyy[:, k] = next(it_cols)
        for on_r, r in surf_rows:
            for on_c, c in surf_cols:
                if on_r and on_c:
                    self.txx[r, c] = 0.0
                    self.tyy[r, c] = 0.0

    def _inject_force(self, src: ForceSource, t: float) -> None:
        """Add one body-force increment to the target velocity node.

        The face density is read from the host map as a Python float, which
        rounds as the float64 element it is read from, so the increment is
        the same IEEE double arithmetic on every device.
        """
        f = src.amplitude * src.waveform(t)
        if src.direction == "x":
            rho = float(self._rho_x_host[src.iy, src.ix])
            self.vx[src.iy, src.ix] += self.dt * f / (rho * self.dx**2)
        else:
            rho = float(self._rho_y_host[src.iy, src.ix])
            self.vy[src.iy, src.ix] += self.dt * f / (rho * self.dx**2)

    def energy(self) -> float:
        r"""Total elastic field energy [J per metre of depth].

        Kinetic energy plus the plane-strain elastic energy expressed in
        stresses by inverting the 2D stiffness (determinant
        :math:`4 \mu (\lambda + \mu)`); fluid cells (``mu = 0``) degenerate
        to the acoustic :math:`p^2 / (2 \lambda)` and shear-free corners
        contribute nothing.
        """
        xp, b = self._xp, self._backend
        with b.context():
            e_v = 0.5 * (
                b.scalar(xp.sum(self._rho_x * self.vx**2))
                + b.scalar(xp.sum(self._rho_y * self.vy**2))
            )
            lam, mu = self._lam, self._mu
            solid = mu > 0.0
            den = xp.where(solid, 8.0 * mu * (lam + mu), 1.0)
            e_solid = (
                (lam + 2.0 * mu) * (self.txx**2 + self.tyy**2)
                - 2.0 * lam * self.txx * self.tyy
            ) / den
            # Fluid cells always have lam = rho c_p**2 > 0; the solid cells
            # divide by one instead, so a lambda = 0 solid does not raise a
            # spurious warning, and their quotient is never read.
            safe = xp.where(solid, 1.0, 2.0 * lam)
            e_fluid = xp.where(solid, 0.0, self.p**2 / safe)
            e_n = b.scalar(xp.sum(xp.where(solid, e_solid, e_fluid)))
            mu_c = self._mu_c
            e_s = b.scalar(
                xp.sum(
                    xp.where(
                        mu_c > 0.0,
                        self.txy**2 / xp.where(mu_c > 0.0, 2.0 * mu_c, 1.0),
                        0.0,
                    )
                )
            )
        return (e_v + e_n + e_s) * self.dx**2

    # The array type is the backend's, and the Array API standard does not name one.
    def collocated(self, field: Field) -> Any:  # noqa: ANN401
        """One field interpolated to the cell centres, shape ``(ny, nx)``.

        ``"p"`` is the synthetic pressure; ``"vx"``/``"vy"`` average the two
        adjacent faces (domain-edge faces count as zero, their built-in
        value), so probes and snapshots of every field share the cell-centre
        positions. The result is on the engine's device, where the fields
        live: a NumPy array by default, the backend's own array on another
        device; :meth:`host_field` gives host copies of the stored fields.
        """
        if field == "p":
            return self.p
        if field not in _FIELD_NAMES:
            msg = f"field must be one of {_FIELD_NAMES}"
            raise ValueError(msg)
        ny, nx = self.txx.shape
        with self._backend.context():
            out = self._backend.zeros((ny, nx))
            if field == "vx":
                out[:, :-1] += self.vx
                out[:, 1:] += self.vx
            else:
                out[:-1, :] += self.vy
                out[1:, :] += self.vy
            out *= 0.5
        return out

    def run(
        self,
        n_steps: int,
        snapshot_every: int | None = None,
        snapshot_decimation: int = 1,
    ) -> NDArray[np.floating]:
        """Advance ``n_steps`` steps, optionally recording pressure frames.

        With ``snapshot_every = k`` a host copy of the synthetic pressure
        ``p`` is stored after every ``k``-th step (and one of the initial
        state), keeping every ``snapshot_decimation``-th cell along each
        axis; the stacked ``(n_frames, ny', nx')`` array plugs straight into
        a ``FuncAnimation`` ``imshow`` update. Without ``snapshot_every`` an
        empty array is returned and only the final state is kept (read it
        with :meth:`host_field`).

        :raises TypeError: if ``snapshot_decimation``, ``n_steps`` or
            ``snapshot_every`` is a flag, a text or an array where a count goes.
        :raises ValueError: if ``n_steps`` is not a whole number of 0 or more,
            or ``snapshot_every`` or ``snapshot_decimation`` is not a whole
            number of 1 or more.
        """
        return _run_recording(self, n_steps, snapshot_every, snapshot_decimation)

    #: The arrays the engine stores, the names :meth:`host_field` reads.
    _STORED: tuple[Literal["txx", "tyy", "txy", "vx", "vy"], ...] = (
        "txx",
        "tyy",
        "txy",
        "vx",
        "vy",
    )

    def host_field(
        self, name: Literal["txx", "tyy", "txy", "vx", "vy"]
    ) -> NDArray[np.floating]:
        """A NumPy copy of the stored field *name*, whatever the device.

        :param name: ``"txx"`` or ``"tyy"`` (cell centres), ``"txy"``
            (interior corners), ``"vx"`` or ``"vy"`` (faces).
        :raises TypeError: if ``name`` is not a text.
        :raises ValueError: for a field the engine does not store.
        """
        require_choice(name, "name", self._STORED)
        return np.array(self._backend.to_host(getattr(self, name)), copy=True)

    @property
    def provenance(self) -> RunProvenance:
        """Where this engine steps: device, dtype and library versions."""
        return self._backend.provenance


@dataclass(frozen=True)
class ElasticFDTDResult(OwnsArrays):
    r"""Frozen result of an :func:`elastic_fdtd_simulation` run.

    :ivar times: Time axis [s], length ``n_steps + 1`` (includes
        :math:`t = 0`).
    :ivar signals: Recorded histories, shape
        ``(n_probes, n_fields, n_steps + 1)``, one row per probe and one
        layer per entry of ``probe_fields`` (velocities are interpolated to
        the probe cell centre).
    :ivar probe_fields: The recorded fields, drawn from
        ``("p", "vx", "vy")``.
    :ivar probes: Probe cell indices ``(ix, iy)``, shape ``(n_probes, 2)``.
    :ivar probe_positions: Probe cell-centre positions ``(x, y)`` [m], shape
        ``(n_probes, 2)``.
    :ivar dx: Grid spacing [m].
    :ivar dt: Time step [s].
    :ivar shape: Grid shape ``(ny, nx)``.
    :ivar sources: The source definitions of the run.
    :ivar snapshots: Recorded cell-centre fields of ``snapshot_field``,
        shape ``(n_frames, ceil(ny / d), ceil(nx / d))`` with ``d`` the
        ``snapshot_decimation``, in the dtype the run stepped in, or ``None``
        when no snapshots were requested.
    :ivar snapshot_times: Time of each snapshot [s], or ``None``.
    :ivar snapshot_field: The field recorded in ``snapshots``.
    :ivar obstacle_mask: Boolean map of rigid cells, or ``None``.
    :ivar free_sides: Sides carrying a traction-free surface.
    :ivar snapshot_decimation: Every how many cells a snapshot keeps along
        each axis (1 keeps every cell).
    :ivar provenance: Where the run stepped (:class:`RunProvenance`).
    """

    times: NDArray[np.float64]
    signals: NDArray[np.float64]
    probe_fields: tuple[str, ...]
    probes: NDArray[np.int_]
    probe_positions: NDArray[np.float64]
    dx: float
    dt: float
    shape: tuple[int, int]
    sources: tuple[ElasticSource, ...]
    snapshots: NDArray[np.floating] | None
    snapshot_times: NDArray[np.float64] | None
    snapshot_field: Field
    obstacle_mask: NDArray[np.bool_] | None
    free_sides: tuple[str, ...]
    snapshot_decimation: int
    provenance: RunProvenance

    def __post_init__(self) -> None:
        """Reject a run whose probes, fields, time axis and grid disagree.

        ``signals`` is indexed one probe and one field at a time, and neither
        index carries a name of its own: the probe plot draws the trace at
        ``signals[k, j]`` under the position of probe ``k`` and the symbol of
        ``probe_fields[j]``. A field axis longer than ``probe_fields`` then
        leaves its surplus traces out of the picture without a word, and one
        shorter runs off the end of the array being drawn. The snapshot plot
        stamps its frame across an extent taken from ``shape``, which turns a
        frame recorded on a different grid into a plausible field over a
        domain it never covered.

        :raises TypeError: if ``snapshot_decimation`` is not a number, or
            ``provenance`` is not a :class:`RunProvenance`.
        :raises ValueError: if the probe, field, time-step, snapshot or grid
            axes disagree, or ``snapshot_decimation`` is not a whole number
            of 1 or more.
        """
        _require_provenance(type(self).__name__, self.provenance)
        require_ranks(
            self,
            times=1,
            signals=3,
            probes=2,
            probe_positions=2,
            snapshots=3,
            snapshot_times=1,
            obstacle_mask=2,
        )
        require_same_length(self, "signals", "probes", "probe_positions", axis="probe")
        require_same_length(
            self, ("probes", 1), ("probe_positions", 1), axis="coordinate"
        )
        require_same_length(self, "probe_fields", ("signals", 1), axis="recorded field")
        require_same_length(self, "times", ("signals", 2), axis="time step")
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
        :param kind: ``"probes"`` (default) draws the per-probe signal time
            histories; ``"snapshot"`` renders one recorded field with the
            geometry overlaid (``imshow`` raster).
        :param frame: Snapshot index for ``kind="snapshot"`` (default: the
            last recorded frame).
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the underlying ``plot``/``imshow``.
        :return: The axes.
        """
        from .._i18n import check_language

        check_language(language)
        if kind == "probes":
            from .._plot.simulation import plot_elastic_probes

            return plot_elastic_probes(self, ax=ax, language=language, **kwargs)
        if kind == "snapshot":
            from .._plot.simulation import plot_elastic_snapshot

            return plot_elastic_snapshot(
                self, ax=ax, frame=frame, language=language, **kwargs
            )
        msg = "kind must be 'probes' or 'snapshot'"
        raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class ElasticRecording(RichDisplay):
    """What an elastic run writes down: probe traces and field snapshots.

    The two ways out of a running simulation. Probes record a time history at
    named cells, one trace per field of ``probe_fields``; snapshots record the
    whole domain every ``snapshot_every`` steps for one field. Recording
    nothing (the default) runs the physics and keeps only the time axis.

    :param probes: Probe cells as ``(ix, iy)`` index pairs.
    :param probe_fields: Which fields each probe records, drawn from
        ``("p", "vx", "vy")`` (default ``("vy",)``, the component a surface
        accelerometer would see).
    :param snapshot_every: Record a full field snapshot every this many steps
        (and at :math:`t = 0`); ``None`` records none.
    :param snapshot_field: Field recorded in the snapshots
        (``"p"``/``"vx"``/``"vy"``, interpolated to cell centres).
    :param snapshot_decimation: Keep every this many cells along each axis
        in a snapshot (default 1, every cell); the result records it.
    :raises TypeError: for a probe that is not a pair or has an index that is
        not a number, a ``snapshot_every`` that is a flag, a text, an array or
        anything else that is neither a number nor ``None``, or a
        ``snapshot_decimation`` that is a flag, a text, an array or anything
        else that is not a number.
    :raises ValueError: for ``probe_fields`` that are empty, repeat a field or
        name one that is not ``"p"``, ``"vx"`` or ``"vy"``, a
        ``snapshot_field`` that is none of them, a probe of more or fewer than
        two indices or with an index that is not a whole number, or a
        ``snapshot_every`` or ``snapshot_decimation`` that is not a whole
        number of 1 or more.
    """

    probes: Sequence[tuple[int, int]] = ()
    probe_fields: Sequence[str] = ("vy",)
    snapshot_every: int | None = None
    snapshot_field: Field = "p"
    snapshot_decimation: int = 1

    def __post_init__(self) -> None:
        """Refuse a malformed probe, field or count when the record is built.

        Whether a probe lies on the grid, and outside the obstacle, is checked
        by the :class:`ElasticRun` that holds the record, the first place a
        grid exists.
        """
        fields = _resolve_probe_fields(self.probe_fields)
        if self.snapshot_field not in _FIELD_NAMES:
            msg = f"snapshot_field must be one of {_FIELD_NAMES}"
            raise ValueError(msg)
        every, decimation = _snapshot_options(
            self.snapshot_every, self.snapshot_decimation
        )
        # Held as tuples and plain ints, so a list handed in cannot change the
        # record after it is built, and a whole float or a NumPy integer reads
        # back as the count a slice takes.
        object.__setattr__(self, "probes", _probe_pairs(self.probes))
        object.__setattr__(self, "probe_fields", fields)
        object.__setattr__(self, "snapshot_every", every)
        object.__setattr__(self, "snapshot_decimation", decimation)


@dataclass(frozen=True, kw_only=True)
class ElasticBoundaries(RichDisplay):
    """How the four edges of the elastic domain are terminated.

    The sponge thickness only means anything where a side is absorbing, which
    is why it travels with the sides rather than beside them.

    :param sides: ``"rigid"`` (default), ``"absorbing"``, ``"free"``, or a
        mapping from side name (``left``/``right``/``top``/``bottom``) to one
        of those. A mapping is held as a read-only copy, so a change to the
        caller's dictionary afterwards does not reach the record.
    :param absorbing_layer_cells: Sponge-layer thickness for absorbing sides,
        in cells.
    """

    sides: ElasticBoundary | Mapping[Side, ElasticBoundary] = "rigid"
    absorbing_layer_cells: int = 20

    def __post_init__(self) -> None:
        """Hold a mapping of sides as a read-only copy of its own.

        The sides are checked where a run reads them, not here.
        """
        if isinstance(self.sides, Mapping):
            object.__setattr__(self, "sides", MappingProxyType(dict(self.sides)))

    def __reduce__(self) -> tuple[Any, tuple[type, dict[str, Any]]]:
        """Rebuild from the fields: a read-only mapping of sides does not pickle."""
        return reduce_with_plain_rows(self)


@dataclass(frozen=True)
class _ElasticChecks:
    """What the checks of an :class:`ElasticRun` found, kept with the run.

    As :class:`~phonometry.simulation.fdtd._AcousticChecks`, for the elastic
    engine: the grid, the free and the absorbing sides, the counts and the
    recorded fields.
    """

    grid: tuple[int, int]
    dx: float
    dt: float
    obstacle: NDArray[np.bool_] | None
    free_sides: tuple[str, ...]
    absorbing_sides: tuple[Side, ...]
    sponge_width: int
    probe_ix: NDArray[np.int_]
    fields: tuple[str, ...]
    steps: int
    snapshot_every: int | None
    snapshot_field: Field
    snapshot_decimation: int

    def snapshot_shape(self) -> tuple[int, int, int] | None:
        """The shape of the snapshots the run records, or ``None`` when it records none."""
        return _snapshot_shape(
            self.grid, self.steps, self.snapshot_every, self.snapshot_decimation
        )


@dataclass(frozen=True)
class ElasticRun(OwnsArrays):
    r"""One elastic (P-SV) FDTD simulation: the domain, its sources and what it records.

    As :class:`~phonometry.simulation.FDTDRun`, for
    :func:`elastic_fdtd_simulation`: every argument is checked when the run
    is built, the grid's included (the time step, the shear speed against
    the P-wave speed, the density, the sponge and the damping, the free and
    absorbing sides, the obstacle, and the sources and the probes on the
    grid), and nothing the caller changes afterwards reaches a checked run.

    :param c_p: P-wave speed map [m/s], shape ``(ny, nx)``, or a scalar with
        an explicit ``shape``.
    :param c_s: S-wave speed map [m/s]; ``c_s = 0`` marks fluid cells.
    :param dx: Grid spacing [m] (square cells).
    :param duration: Physical time to simulate [s].
    :param sources: One or more of :class:`ExplosionSource` or
        :class:`ForceSource`.
    :param rho: Density map [kg/m3]; scalar or ``(ny, nx)`` array.
    :param shape: Grid shape ``(ny, nx)``, required when ``c_p`` is scalar.
    :param cfl: Courant number in ``(0, 1)`` (Virieux Eqs. 6-7); the time
        step is :math:`\Delta t = C_\mathrm{N}\, \Delta x / (c_{\mathrm{p},\max} \sqrt{2})`.
        Default 0.6.
    :param recording: What the run records (:class:`ElasticRecording`): the
        probe cells and their fields, and the snapshot cadence and field.
        ``None`` records nothing but the time axis.
    :param boundaries: How the domain edges are terminated
        (:class:`ElasticBoundaries`); ``None`` is rigid on all four sides.
    :param obstacle_mask: Boolean map, shape ``(ny, nx)``, of rigid cells
        (rasterised interior geometry).
    :param damping: Uniform bulk amplitude decay rate [1/s].
    :raises TypeError: If an argument is of the wrong type, among them a
        ``cfl`` or ``dx`` that is not one number, a ``recording`` that is
        neither an :class:`ElasticRecording` nor ``None``, or ``boundaries``
        that are neither an :class:`ElasticBoundaries` nor ``None``.
    :raises ValueError: If an argument is out of its range, or a source, a
        probe or the obstacle does not fit the grid.
    """

    c_p: float | Field2D
    c_s: float | Field2D
    dx: float
    duration: float
    _: KW_ONLY
    sources: Sequence[ElasticSource]
    rho: float | Field2D
    shape: tuple[int, int] | None = None
    cfl: float = 0.6
    recording: ElasticRecording | None = None
    boundaries: ElasticBoundaries | None = None
    obstacle_mask: NDArray[np.bool_] | None = None
    damping: float = 0.0

    def __post_init__(self) -> None:
        """Hold the sources so they cannot change, then check every argument."""
        object.__setattr__(self, "sources", tuple(self.sources))
        checks = self._checked
        if self.shape is not None and np.isscalar(self.c_p):
            # Read only for a scalar c_p: held as the grid it was built on.
            object.__setattr__(self, "shape", checks.grid)

    @cached_property
    def _checked(self) -> _ElasticChecks:
        """Every argument checked, once, when the run is built."""
        return _elastic_checks(self)

    def __reduce__(self) -> tuple[Any, tuple[type, dict[str, Any]]]:
        """Rebuild from the fields, so the run checks itself again where it arrives."""
        return reduce_with_plain_rows(self)


def _boundaries_or_rigid(boundaries: object) -> ElasticBoundaries:
    """A run's ``boundaries``, or rigid on all four sides for ``None``.

    :raises TypeError: for anything but ``None`` or an :class:`ElasticBoundaries`.
    """
    if boundaries is None:
        return ElasticBoundaries()
    if not isinstance(boundaries, ElasticBoundaries):
        msg = f"'boundaries' must be an ElasticBoundaries or None, got {type(boundaries).__name__}."
        raise TypeError(msg)
    return boundaries


def _elastic_checks(run: ElasticRun) -> _ElasticChecks:
    """Check every argument of *run*, as :func:`elastic_fdtd_simulation` always did.

    The recording's type, the boundaries' type, the sources, the duration,
    the sides and the sponge thickness, then the medium
    (:func:`_elastic_medium`: the grid and the time step, the shear speed,
    the density, the sponge and the damping, the free sides, the obstacle),
    then the sources and the probes on the grid and the step count.

    :raises TypeError: as :class:`ElasticRun` documents.
    :raises ValueError: as :class:`ElasticRun` documents.
    """
    recording = _recording_or_empty(run.recording, ElasticRecording)
    boundaries = _boundaries_or_rigid(run.boundaries)
    if len(run.sources) == 0:
        msg = "at least one source is required"
        raise ValueError(msg)
    duration = _positive_finite("duration", run.duration)
    absorbing_sides, free_sides = _parse_elastic_boundaries(boundaries.sides)
    width = _validated_absorbing_layer(boundaries, absorbing_sides)
    medium = _elastic_medium(
        run.c_p,
        run.c_s,
        run.dx,
        rho=run.rho,
        cfl=run.cfl,
        sponge_width=width,
        sponge_sides=absorbing_sides or None,
        sponge_reflection=_DEFAULT_SPONGE_REFLECTION,
        damping=run.damping,
        shape=run.shape,
        free_sides=free_sides,
        obstacle_mask=run.obstacle_mask,
    )
    ny, nx = medium.cp_map.shape
    for source in run.sources:
        _check_elastic_source(source, (ny, nx), medium.obstacle)
    return _ElasticChecks(
        grid=(ny, nx),
        dx=medium.dx,
        dt=medium.dt,
        obstacle=None if medium.obstacle is None else read_only(medium.obstacle),
        free_sides=medium.free_sides,
        absorbing_sides=absorbing_sides,
        sponge_width=width,
        probe_ix=read_only(_probe_indices(recording.probes, (ny, nx), medium.obstacle)),
        fields=tuple(recording.probe_fields),
        steps=_step_count(duration, medium.dt),
        snapshot_every=recording.snapshot_every,
        snapshot_field=recording.snapshot_field,
        snapshot_decimation=recording.snapshot_decimation,
    )


def _elastic_engine(run: ElasticRun, compute: Compute | None) -> ElasticFDTD2D:
    """The engine that steps *run* on this machine, its sources added.

    It takes the sponge and the free sides the run's checks found, and
    checks its medium again in its constructor, as every engine does.
    """
    checks = run._checked
    sim = ElasticFDTD2D(
        run.c_p,
        run.c_s,
        run.dx,
        rho=run.rho,
        cfl=run.cfl,
        sponge_width=checks.sponge_width,
        sponge_sides=checks.absorbing_sides or None,
        damping=run.damping,
        shape=run.shape,
        free_sides=checks.free_sides,
        obstacle_mask=run.obstacle_mask,
        compute=compute,
    )
    for source in run.sources:
        sim.add_source(source)
    return sim


def _elastic_expected(run: ElasticRun, dtype: str) -> Expected:
    """The arrays a node must send back for *run*, in the order it sends them."""
    checks = run._checked
    signals = (checks.probe_ix.shape[0], len(checks.fields), checks.steps + 1)
    return _expected_arrays(("signals", signals), checks.snapshot_shape(), dtype)


def _parse_elastic_boundaries(
    boundaries: ElasticBoundary | Mapping[Side, ElasticBoundary],
) -> tuple[tuple[Side, ...], tuple[Side, ...]]:
    """Split the boundary spec into absorbing sides and free sides."""
    spec: dict[Side, str]
    if isinstance(boundaries, str):
        spec = dict.fromkeys(_SIDES, boundaries)
    else:
        unknown = set(boundaries) - set(_SIDES)
        if unknown:
            msg = f"unknown boundary sides: {sorted(unknown)}"
            raise ValueError(msg)
        spec = {side: boundaries.get(side, "rigid") for side in _SIDES}
    absorbing: list[Side] = []
    free: list[Side] = []
    for side in _SIDES:
        value = spec[side]
        if value not in _BOUNDARY_NAMES:
            msg = (
                f"boundary for side {side!r} must be one of "
                f"{_BOUNDARY_NAMES}, got {value!r}"
            )
            raise ValueError(msg)
        if value == "absorbing":
            absorbing.append(side)
        elif value == "free":
            free.append(side)
    return tuple(absorbing), tuple(free)


def _resolve_probe_fields(probe_fields: Sequence[str]) -> tuple[str, ...]:
    """Validate the probe-field spec into a non-empty unique tuple."""
    fields = tuple(probe_fields)
    if not fields:
        msg = "probe_fields must not be empty"
        raise ValueError(msg)
    unknown = set(fields) - set(_FIELD_NAMES)
    if unknown:
        msg = f"unknown probe fields: {sorted(unknown)}"
        raise ValueError(msg)
    if len(set(fields)) != len(fields):
        msg = "probe_fields must not repeat a field"
        raise ValueError(msg)
    return fields


def _device_mask(b: _backends.Backend, host: NDArray[np.bool_]) -> DeviceArray:
    """A host boolean array as a boolean array on the device.

    A backend hands over floating arrays, so the mask goes as exact zeros
    and ones and turns boolean again on the device.
    """
    return b.asarray(host.astype(np.float64)) > 0.0


def _probe_gathers(
    sim: ElasticFDTD2D, rows: NDArray[np.int_], cols: NDArray[np.int_]
) -> dict[str, DeviceArray]:
    """Flat indices and edge masks of the probe cells, on the device, once.

    The Array API standard indexes one axis with an integer array, not two
    at once, so each probe cell becomes one index into its field flattened
    row by row: ``row * width + column``, with the width of the field read.
    A face beyond the domain edge has no stored velocity; its index is
    clamped to a stored face and the mask zeroes what it reads.
    """
    b = sim._backend
    ny, nx = sim.txx.shape
    with b.context():
        return {
            "centre": b.index(rows * nx + cols),
            "vx_left": b.index(rows * (nx - 1) + np.maximum(cols - 1, 0)),
            "vx_right": b.index(rows * (nx - 1) + np.minimum(cols, nx - 2)),
            "vy_above": b.index(np.maximum(rows - 1, 0) * nx + cols),
            "vy_below": b.index(np.minimum(rows, ny - 2) * nx + cols),
            "has_left": _device_mask(b, cols > 0),
            "has_right": _device_mask(b, cols < nx - 1),
            "has_above": _device_mask(b, rows > 0),
            "has_below": _device_mask(b, rows < ny - 1),
        }


def _sample_probes(
    sim: ElasticFDTD2D, field: str, g: dict[str, DeviceArray]
) -> DeviceArray:
    """Sample one field at the probe cell centres (velocities averaged)."""
    xp = sim._xp

    def flat(a: DeviceArray) -> DeviceArray:
        return xp.reshape(a, (-1,))

    if field == "p":
        return -0.5 * (
            xp.take(flat(sim.txx), g["centre"]) + xp.take(flat(sim.tyy), g["centre"])
        )
    if field == "vx":
        left = xp.where(g["has_left"], xp.take(flat(sim.vx), g["vx_left"]), 0.0)
        right = xp.where(g["has_right"], xp.take(flat(sim.vx), g["vx_right"]), 0.0)
        return 0.5 * (left + right)
    above = xp.where(g["has_above"], xp.take(flat(sim.vy), g["vy_above"]), 0.0)
    below = xp.where(g["has_below"], xp.take(flat(sim.vy), g["vy_below"]), 0.0)
    return 0.5 * (above + below)


def _store_samples(
    sim: ElasticFDTD2D,
    probe_fields: tuple[str, ...],
    gathers: dict[str, DeviceArray],
    column: int,
    signals: NDArray[np.float64],
    buffer: DeviceArray | None,
) -> None:
    """Write this step's probe samples into column *column* of the record.

    Into ``signals`` itself when there is no device ``buffer`` (NumPy), into
    the buffer otherwise.
    """
    for k, field in enumerate(probe_fields):
        sample = _sample_probes(sim, field, gathers)
        if buffer is None:
            signals[:, k, column] = sample
        else:
            buffer[:, k, column] = sample


def _record_elastic_run(
    sim: ElasticFDTD2D,
    steps: int,
    probe_ix: NDArray[np.int_],
    probe_fields: tuple[str, ...],
    snapshot_every: int | None,
    snapshot_field: Field,
    snapshot_decimation: int,
    signals: NDArray[np.float64],
    snapshots: NDArray[np.floating] | None,
) -> None:
    """Step the engine, writing probe histories and field snapshots in place.

    ``signals`` takes one column per step after the first, one layer per
    entry of ``probe_fields``; ``snapshots`` takes the initial field and then
    one frame every ``snapshot_every`` steps, ``steps // snapshot_every + 1``
    of them. Both are allocated by the caller before the march, so that the
    run is never held twice, as a list of frames and their stack.

    On NumPy the probe samples are written straight into ``signals``; on a
    device they go into a buffer there, which comes to the host once, after
    the march. Each snapshot is cut to every ``snapshot_decimation``-th cell
    on the device and comes to the host as it is taken, so only the cells
    it keeps cross.

    After each step it tells a watcher, if one is set (:mod:`._observer`), how
    many steps are done; a node uses that to stop a run whose client went away.
    """
    b = sim._backend
    d = snapshot_decimation
    if snapshots is not None:
        snapshots[0] = b.to_host(sim.collocated(snapshot_field)[::d, ::d])
    n_probes = probe_ix.shape[0]
    gathers = _probe_gathers(sim, probe_ix[:, 1], probe_ix[:, 0]) if n_probes else {}
    buffer = (
        None if b.name == "numpy" else b.zeros((n_probes, len(probe_fields), steps + 1))
    )
    with b.context():
        for i in range(steps):
            sim.step()
            _observer.step_done(i + 1, steps)
            if n_probes:
                _store_samples(sim, probe_fields, gathers, i + 1, signals, buffer)
            if (
                snapshots is not None
                and snapshot_every is not None
                and (i + 1) % snapshot_every == 0
            ):
                snapshots[(i + 1) // snapshot_every] = b.to_host(
                    sim.collocated(snapshot_field)[::d, ::d]
                )
    if buffer is not None:
        signals[...] = b.to_host(buffer)


def _validated_absorbing_layer(
    boundaries: ElasticBoundaries,
    absorbing_sides: tuple[str, ...],
) -> int:
    """Validate the absorbing-layer thickness; 0 when no side absorbs."""
    if not absorbing_sides:
        return 0
    cells = _integer("absorbing_layer_cells", boundaries.absorbing_layer_cells)
    if cells < 1:
        msg = "absorbing_layer_cells must be >= 1"
        raise ValueError(msg)
    return cells


def elastic_fdtd_simulation(
    run: ElasticRun, *, compute: Compute | None = None
) -> ElasticFDTDResult:
    r"""Run a deterministic 2D elastic (P-SV) FDTD simulation.

    Builds the staggered velocity-stress grid (Virieux 1986, Eq. 5), applies
    the requested boundary conditions, injects the sources and integrates
    for ``duration`` seconds, recording the selected fields at every probe
    each time step and, optionally, full-field snapshots.

    The grid covers ``(nx * dx, ny * dx)`` metres; a cell index ``(ix, iy)``
    maps to the physical cell centre ``((ix + 0.5) * dx, (iy + 0.5) * dx)``.
    Resolve at least 10 cells per shortest wavelength
    (:math:`\Delta x \le c_{\mathrm{s},\min} / (10 f)` with ``c_s_min`` the smallest
    non-zero
    ``c_s`` over the solid cells, since the S wave is always the shortest;
    a wholly fluid map falls back to the acoustic rule on the smallest
    ``c_p``; Virieux's rule from the dispersion relations
    Eqs. 13-14), and 15-20 cells per wavelength when a Rayleigh wave along a
    free surface matters, the second-order stress-imaging surface being the
    most dispersive part of the scheme. The simulation is 2D (plane strain):
    a point source is physically a line source with cylindrical
    :math:`1/\sqrt{r}` amplitude spreading.

    :param run: The simulation (:class:`ElasticRun`): the domain, its
        sources and what it records, every argument checked when the run was
        built.
    :param compute: Where the run steps (:class:`Compute`); ``None`` follows
        :func:`use`, then ``PHONOMETRY_COMPUTE``, then NumPy. With a
        ``host`` the whole run goes to that node, named in the hosts file,
        and comes back as this function's record (see the guide on remote
        nodes).
    :return: An :class:`ElasticFDTDResult`.
    :raises TypeError: For a ``run`` that is not an :class:`ElasticRun`, a
        ``compute`` that is neither a :class:`Compute` nor ``None``, or,
        when ``compute`` names a host, a run that cannot travel to a node: an
        :class:`ExplosionSource` or a :class:`ForceSource` whose waveform is
        a callable other than the ``value`` of a
        :class:`~phonometry.simulation.GaussianPulse`,
        :class:`~phonometry.simulation.CWSource` or
        :class:`~phonometry.simulation.SignalSource`.
    :raises ValueError: For a ``PHONOMETRY_COMPUTE`` that does not parse, or
        a malformed hosts file.
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
    if not isinstance(run, ElasticRun):
        msg = f"'run' must be an ElasticRun, got {type(run).__name__}."
        raise TypeError(msg)
    checks = run._checked
    request = _requested(compute)
    # The record keeps these two as they are (handed_over): the snapshots are
    # most of the result, and a copy would hold them twice while it is built.
    # The probe histories are float64 whatever the run's dtype; the snapshots
    # keep it, a float32 run's being half the size. Either route fills them.
    signals = np.zeros(
        (checks.probe_ix.shape[0], len(checks.fields), checks.steps + 1),
        dtype=np.float64,
    )
    frames = checks.snapshot_shape()
    snapshots = (
        None if frames is None else np.zeros(frames, dtype=np.dtype(request.dtype))
    )
    provenance: RunProvenance | None = None
    if request.host is not None:
        # Called here, as in fdtd_simulation, not from a shared helper: the
        # record keeps these arrays without a copy, which holds only for
        # arrays that reach the code writing into them within three calls.
        from ._remote.client import run_remote

        expected = _elastic_expected(run, request.dtype)
        provenance = run_remote(
            "elastic_fdtd_simulation",
            request,
            {"run": run},
            expected,
            signals,
            snapshots,
        )
        if provenance is None:
            # The node failed and the request asked to run here instead.
            _cleared(signals, snapshots)
    if provenance is None:
        sim = _elastic_engine(run, _placement_here(request))
        _record_elastic_run(
            sim,
            checks.steps,
            checks.probe_ix,
            checks.fields,
            checks.snapshot_every,
            checks.snapshot_field,
            checks.snapshot_decimation,
            signals,
            snapshots,
        )
        provenance = sim.provenance
    return ElasticFDTDResult(
        times=np.arange(checks.steps + 1, dtype=np.float64) * checks.dt,
        signals=handed_over(signals),
        probe_fields=checks.fields,
        probes=checks.probe_ix,
        probe_positions=(checks.probe_ix.astype(np.float64) + 0.5) * checks.dx,
        dx=checks.dx,
        dt=checks.dt,
        shape=checks.grid,
        sources=tuple(run.sources),
        snapshots=handed_over(snapshots),
        snapshot_times=_snapshot_times(checks.steps, checks.snapshot_every, checks.dt),
        snapshot_field=checks.snapshot_field,
        obstacle_mask=checks.obstacle,
        free_sides=checks.free_sides,
        snapshot_decimation=checks.snapshot_decimation,
        provenance=provenance,
    )
