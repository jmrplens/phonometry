#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Mechanical mobility and the frequency-response-function family (ISO 7626-1:2011).

Mechanical **mobility** is the complex ratio of a velocity response to the
excitation force that produces it, ``Y_ij = v_i / F_j`` (ISO 7626-1, 3.1). It is
one of a family of motion-per-force frequency-response functions (FRFs); which
member is used depends only on whether the motion is expressed as displacement,
velocity or acceleration, and each has a force-per-motion reciprocal
(ISO 7626-1, Table 1):

===============  =====================  ===========  =========================
Motion           FRF (motion / force)   Unit          Reciprocal (force / motion)
===============  =====================  ===========  =========================
displacement     dynamic compliance /   m/N           dynamic stiffness  (N/m)
                 receptance ``H``
velocity         mobility ``Y``         m/(N.s)        impedance          (N.s/m)
acceleration     accelerance ``A``      1/kg           apparent mass      (kg)
===============  =====================  ===========  =========================

For a harmonic motion ``x e^{j omega t}`` the velocity is ``j omega x`` and the
acceleration ``-omega**2 x``, so every FRF follows from the receptance ``H``::

    Y = j omega H          A = -omega**2 H
    Z (impedance)      = 1 / Y
    M (apparent mass)  = 1 / A
    K (dyn. stiffness) = 1 / H

:func:`convert_frf` moves between any two of the six FRFs through the receptance
pivot. A **driving-point** FRF has the response and force at the same point
(``i = j``); a **transfer** FRF has them at different points.

The canonical closed-form reference is the single-degree-of-freedom resonator
of mass ``m``, viscous damping ``c`` and stiffness ``k`` (ISO 7626-1, Annex A),
whose receptance is ``H(omega) = 1 / (k - omega**2 m + j omega c)``. At its
resonance ``omega0 = sqrt(k/m)`` the driving-point mobility is purely real and
equal to ``1/c`` -- the mobility peak measures the damping. This module is the
FRF backbone for the structure-borne source and transmission standards
(ISO 9611, ISO 10846, EN 15657, EN 12354-5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

from numpy.typing import ArrayLike, NDArray

from ._validation import require_non_negative, require_positive

# ---------------------------------------------------------------------------
# FRF taxonomy (ISO 7626-1 Table 1).
# ---------------------------------------------------------------------------

#: The six frequency-response functions, keyed by name. ``motion`` is the power
#: of ``j*omega`` relating the FRF to the receptance (0 displacement, 1 velocity,
#: 2 acceleration); ``inverse`` marks the force-per-motion reciprocals.
_FRF_TYPES: dict[str, tuple[int, bool]] = {
    "receptance": (0, False),        # dynamic compliance, x/F  [m/N]
    "mobility": (1, False),          # v/F                      [m/(N.s)]
    "accelerance": (2, False),       # a/F                      [1/kg]
    "dynamic_stiffness": (0, True),  # F/x                      [N/m]
    "impedance": (1, True),          # F/v                      [N.s/m]
    "apparent_mass": (2, True),      # F/a                      [kg]
}

#: SI unit strings for each FRF, for labelling.
FRF_UNITS: dict[str, str] = {
    "receptance": "m/N",
    "mobility": "m/(N·s)",
    "accelerance": "1/kg",
    "dynamic_stiffness": "N/m",
    "impedance": "N·s/m",
    "apparent_mass": "kg",
}


def _omega(frequency: ArrayLike) -> NDArray[np.float64]:
    """Angular frequency ``omega = 2 pi f`` (rad/s); rejects non-positive f."""
    f = np.asarray(frequency, dtype=np.float64)
    if np.any(f <= 0.0):
        raise ValueError("'frequency' must be positive (mobility conversions "
                         "divide by omega).")
    return 2.0 * np.pi * f


def _to_receptance(
    value: NDArray[np.complex128], omega: NDArray[np.float64], source: str
) -> NDArray[np.complex128]:
    """Reduce any FRF to the receptance ``H = x / F``."""
    power, inverse = _FRF_TYPES[source]
    # Undo the force-per-motion reciprocal, then the (j omega)**power factor.
    motion_per_force = 1.0 / value if inverse else value
    return motion_per_force / (1j * omega) ** power


def _from_receptance(
    receptance: NDArray[np.complex128], omega: NDArray[np.float64], target: str
) -> NDArray[np.complex128]:
    """Build any FRF from the receptance ``H``."""
    power, inverse = _FRF_TYPES[target]
    motion_per_force = receptance * (1j * omega) ** power
    result = 1.0 / motion_per_force if inverse else motion_per_force
    return np.asarray(result, dtype=np.complex128)


def convert_frf(
    value: ArrayLike,
    frequency: ArrayLike,
    source: str,
    target: str,
) -> np.ndarray:
    """Convert a frequency-response function between any two kinds (Table 1).

    :param value: The (complex) FRF value(s) of kind *source*.
    :param frequency: Frequency ``f``, in hertz (scalar or array, broadcast with
        *value*).
    :param source: The FRF kind of *value* -- one of ``"receptance"``,
        ``"mobility"``, ``"accelerance"``, ``"dynamic_stiffness"``,
        ``"impedance"`` or ``"apparent_mass"``.
    :param target: The FRF kind to convert to (same set).
    :return: The FRF value(s) of kind *target*, as a complex array.
    :raises ValueError: for an unknown FRF name or a non-positive frequency.
    """
    for name, role in ((source, "source"), (target, "target")):
        if name not in _FRF_TYPES:
            raise ValueError(
                f"unknown {role} FRF {name!r}; choose from {tuple(_FRF_TYPES)}."
            )
    omega = _omega(frequency)
    val = np.asarray(value, dtype=np.complex128)
    receptance = _to_receptance(val, omega, source)
    return np.asarray(_from_receptance(receptance, omega, target), dtype=np.complex128)


# ---------------------------------------------------------------------------
# Single-degree-of-freedom reference (ISO 7626-1 Annex A).
# ---------------------------------------------------------------------------


def sdof_receptance(
    frequency: ArrayLike, mass: float, stiffness: float, damping: float
) -> np.ndarray:
    """Receptance of a viscously damped SDOF resonator (ISO 7626-1, Annex A).

    ``H(omega) = 1 / (k - omega**2 m + j omega c)``.

    :param frequency: Frequency ``f``, in hertz (scalar or array).
    :param mass: Mass ``m``, in kg.
    :param stiffness: Stiffness ``k``, in N/m.
    :param damping: Viscous damping coefficient ``c``, in N.s/m (>= 0).
    :return: The complex receptance ``H``, in m/N.
    """
    mass = require_positive(mass, "mass")
    stiffness = require_positive(stiffness, "stiffness")
    damping = require_non_negative(damping, "damping")
    omega = _omega(frequency)
    denom = stiffness - omega**2 * mass + 1j * omega * damping
    return np.asarray(1.0 / denom, dtype=np.complex128)


def sdof_mobility(
    frequency: ArrayLike, mass: float, stiffness: float, damping: float
) -> np.ndarray:
    """Mobility of a viscously damped SDOF resonator: ``Y = j omega H``.

    :param frequency: Frequency ``f``, in hertz.
    :param mass: Mass ``m``, in kg. :param stiffness: Stiffness ``k``, N/m.
    :param damping: Viscous damping ``c``, N.s/m.
    :return: The complex mobility ``Y``, in m/(N.s).
    """
    h = sdof_receptance(frequency, mass, stiffness, damping)
    return convert_frf(h, frequency, "receptance", "mobility")


def sdof_accelerance(
    frequency: ArrayLike, mass: float, stiffness: float, damping: float
) -> np.ndarray:
    """Accelerance of a viscously damped SDOF resonator: ``A = -omega**2 H``.

    :param frequency: Frequency ``f``, in hertz.
    :param mass: Mass ``m``, in kg. :param stiffness: Stiffness ``k``, N/m.
    :param damping: Viscous damping ``c``, N.s/m.
    :return: The complex accelerance ``A``, in 1/kg.
    """
    h = sdof_receptance(frequency, mass, stiffness, damping)
    return convert_frf(h, frequency, "receptance", "accelerance")


def resonance_frequency(mass: float, stiffness: float) -> float:
    """Undamped natural frequency ``f0 = (1/2pi) sqrt(k/m)`` of the SDOF, in Hz.

    :param mass: Mass ``m``, in kg.
    :param stiffness: Stiffness ``k``, in N/m.
    :return: The natural frequency ``f0``, in hertz.
    """
    mass = require_positive(mass, "mass")
    stiffness = require_positive(stiffness, "stiffness")
    return float(np.sqrt(stiffness / mass) / (2.0 * np.pi))


# ---------------------------------------------------------------------------
# Bundled FRF result.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MobilityResult:
    """A measured or modelled mobility FRF over frequency.

    :ivar frequencies: Frequencies, in hertz.
    :ivar mobility: Complex mobility ``Y`` per frequency, in m/(N.s).
    :ivar driving_point: ``True`` if response and force are co-located (i = j).
    """

    frequencies: np.ndarray
    mobility: np.ndarray
    driving_point: bool = True

    @property
    def magnitude(self) -> np.ndarray:
        """Mobility magnitude ``|Y|``, in m/(N.s)."""
        return np.abs(self.mobility)

    @property
    def phase(self) -> np.ndarray:
        """Mobility phase, in radians."""
        return np.asarray(np.angle(self.mobility), dtype=np.float64)

    def to(self, target: str) -> np.ndarray:
        """Convert the mobility to another FRF kind (see :func:`convert_frf`)."""
        return convert_frf(self.mobility, self.frequencies, "mobility", target)

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the mobility magnitude ``|Y(f)|``.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ._plotting import plot_mobility

        return plot_mobility(self, ax=ax, **kwargs)


def sdof_mobility_result(
    frequency: ArrayLike, mass: float, stiffness: float, damping: float
) -> MobilityResult:
    """SDOF driving-point mobility bundled as a :class:`MobilityResult`.

    :param frequency: Frequencies ``f``, in hertz (array).
    :param mass: Mass ``m``, in kg. :param stiffness: Stiffness ``k``, N/m.
    :param damping: Viscous damping ``c``, N.s/m.
    :return: The :class:`MobilityResult` (driving point).
    """
    freq = np.asarray(frequency, dtype=np.float64)
    y = sdof_mobility(freq, mass, stiffness, damping)
    return MobilityResult(frequencies=freq, mobility=y, driving_point=True)
