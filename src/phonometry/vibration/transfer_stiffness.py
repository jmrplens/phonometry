#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Dynamic transfer stiffness of resilient elements (ISO 10846-1/-2/-3).

The vibro-acoustic transfer property of a resilient element (a vibration
isolator, mount, bellows or hose) is its **dynamic transfer stiffness** — the
frequency-dependent ratio of the *blocking force* phasor ``F2,b`` on the output
(receiver) side to the displacement phasor ``u1`` on the input (source) side,
with the output blocked (ISO 10846-1, 3.7)::

    k2,1 = F2,b / u1                                             [N/m]

For an isolator between two structures of large driving-point stiffness, the
force delivered to the receiver approximates this blocking force (ISO 10846-1,
Equation 7), so ``k2,1`` characterises the isolator's transmission. Results are
reported as a **level** re the reference stiffness ``k0 = 1 N/m`` (ISO 10846-2
and -3, 3.17)::

    L_k = 10 lg(|k2,1|**2 / k0**2) = 20 lg(|k2,1| / k0)          [dB]

and, in the low-frequency range where inertial forces in the element are
negligible, the **loss factor** is the tangent of the phase angle of ``k2,1``
(ISO 10846-1, 3.8): ``eta = Im(k2,1) / Re(k2,1)``.

Two laboratory methods determine ``k2,1``:

* **Direct method** (ISO 10846-2) — measure the blocked output force ``F2,b``
  and the input displacement ``u1`` directly: ``k2,1 = F2,b / u1``.
* **Indirect method** (ISO 10846-3) — load the output with a compact blocking
  mass ``m2`` and measure the vibration transmissibility ``T = u2/u1``; the
  blocking force is the mass's inertia force (ISO 10846-3, Equation 1)::

      k2,1 = -(2 pi f)**2 (m2 + mf) T          for  T << 1

  where ``mf`` is the mass of the output flange of the test element. The
  approximation is valid only where ``|T| <= 0.1`` (Inequality (2):
  ``DeltaL1,2 >= 20 dB``) and while the blocking mass still behaves rigidly,
  ``10 lg(m2,eff**2/m2**2) <= 1 dB`` (Inequality (3)); see
  :func:`transfer_stiffness_indirect`.

The dynamic transfer stiffness is a member of the frequency-response-function
family (ISO 10846-1, Annex A / Table A.2): ``k = j omega Z = -omega**2 m_eff``,
so it converts to mechanical impedance and effective mass through
:func:`phonometry.convert_frf` (``"dynamic_stiffness"`` <-> ``"impedance"`` <->
``"apparent_mass"``). This module feeds the structure-borne source and building
prediction standards (ISO 9611, EN 15657, EN 12354-5).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

from numpy.typing import ArrayLike, NDArray

from .._internal.validation import require_non_negative, require_positive
from .._internal.warnings import PhonometryWarning
from .mechanical_mobility import convert_frf

#: Reference dynamic stiffness for the level ``L_k`` (ISO 10846-2/-3, 3.17), N/m.
REFERENCE_STIFFNESS: float = 1.0

#: Validity limit on the vibration transmissibility magnitude for the indirect
#: method (ISO 10846-3:2002, 6.1, Inequality (2)): measurements are valid only
#: where ``DeltaL1,2 = La1 - La2 >= 20 dB``, i.e. ``|T| <= 0.1``, which keeps
#: the ``T << 1`` approximation of Formula (1) accurate within 1 dB (12 %).
TRANSMISSIBILITY_LIMIT: float = 0.1


def _omega(frequency: ArrayLike) -> NDArray[np.float64]:
    """Angular frequency ``omega = 2 pi f`` (rad/s); rejects non-positive f."""
    f = np.asarray(frequency, dtype=np.float64)
    if np.any(f <= 0.0):
        raise ValueError("'frequency' must be positive.")
    return 2.0 * np.pi * f


def transfer_stiffness_level(
    stiffness: ArrayLike, *, reference: float = REFERENCE_STIFFNESS
) -> np.ndarray:
    """Level of the dynamic transfer stiffness (ISO 10846-2/-3, 3.17).

    ``L_k = 20 lg(|k2,1| / k0)`` dB, with ``k0`` the reference stiffness.

    :param stiffness: Dynamic transfer stiffness ``k2,1`` (complex or real,
        scalar or array), in N/m.
    :param reference: Reference stiffness ``k0`` (Default: 1 N/m), in N/m.
    :return: The level ``L_k``, in dB re ``k0``.
    :raises ValueError: for a non-positive reference.
    """
    reference = require_positive(reference, "reference")
    magnitude = np.abs(np.asarray(stiffness, dtype=np.complex128))
    return np.asarray(20.0 * np.log10(magnitude / reference), dtype=np.float64)


def loss_factor(stiffness: ArrayLike) -> np.ndarray:
    """Loss factor ``eta = Im(k2,1) / Re(k2,1)`` (ISO 10846-1, 3.8).

    Valid in the low-frequency range where inertial forces in the element are
    negligible; it is the tangent of the phase angle of the transfer stiffness.

    :param stiffness: Dynamic transfer stiffness ``k2,1`` (complex, scalar or
        array), in N/m.
    :return: The loss factor ``eta`` (dimensionless).
    """
    k = np.asarray(stiffness, dtype=np.complex128)
    return np.asarray(k.imag / k.real, dtype=np.float64)


def transfer_stiffness_direct(
    blocking_force: ArrayLike, input_displacement: ArrayLike
) -> np.ndarray:
    """Dynamic transfer stiffness by the direct method (ISO 10846-2).

    ``k2,1 = F2,b / u1`` — the blocked output force phasor over the input
    displacement phasor.

    :param blocking_force: Blocked output force phasor ``F2,b`` (complex), in N.
    :param input_displacement: Input displacement phasor ``u1`` (complex), in m.
    :return: The dynamic transfer stiffness ``k2,1``, in N/m.
    """
    f2b = np.asarray(blocking_force, dtype=np.complex128)
    u1 = np.asarray(input_displacement, dtype=np.complex128)
    return np.asarray(f2b / u1, dtype=np.complex128)


def transfer_stiffness_indirect(
    frequency: ArrayLike,
    transmissibility: ArrayLike,
    blocking_mass: float,
    *,
    flange_mass: float = 0.0,
) -> np.ndarray:
    """Dynamic transfer stiffness by the indirect method (ISO 10846-3, Eq. 1).

    ``k2,1 = -(2 pi f)**2 (m2 + mf) T`` — the blocking force is the inertia
    force of a compact blocking mass ``m2`` (plus the output flange mass
    ``mf``), derived from the measured vibration transmissibility ``T = u2/u1``.
    Valid for ``T << 1`` (i.e. well above the mass/spring resonance).

    **Validity (ISO 10846-3, clause 6).** The ``T << 1`` approximation of
    Formula (1) is required accurate within 1 dB, i.e. within 12 % of the
    calculated stiffness magnitude. This holds only where Inequality (2) is
    met: ``DeltaL1,2 = La1 - La2 >= 20 dB``, i.e. ``|T| <= 0.1``
    (:data:`TRANSMISSIBILITY_LIMIT`). Bands with ``|T|`` above that limit —
    routine near or below the mass/spring resonance — trigger a
    :class:`~phonometry.PhonometryWarning`; treat those bands as outside the
    valid frequency range of the test arrangement. The upper frequency limit
    ``f3`` additionally requires the blocking mass to vibrate as a rigid
    body: results are valid only while its effective mass ``m2,eff``, measured
    per Formula (4) as ``m2,eff = 2 F2 / (a'1 + a''1)`` (two accelerometers
    spaced ``D = sqrt(S)`` across the contact area), stays within 1 dB of the
    rigid mass, ``10 lg(m2,eff**2 / m2**2) <= 1 dB`` (Inequality (3), 6.2.3).

    :param frequency: Frequency ``f``, in hertz (scalar or array).
    :param transmissibility: Vibration transmissibility ``T = u2/u1`` (complex,
        scalar or array; velocity and acceleration ratios have the same value).
    :param blocking_mass: Blocking mass ``m2``, in kg (> 0).
    :param flange_mass: Output-flange mass ``mf``, in kg (Default: 0.0).
    :return: The dynamic transfer stiffness ``k2,1``, in N/m.
    :raises ValueError: for a non-positive frequency or blocking mass.
    :warns PhonometryWarning: where any ``|T| > 0.1`` (Inequality (2) violated).
    """
    blocking_mass = require_positive(blocking_mass, "blocking_mass")
    flange_mass = require_non_negative(flange_mass, "flange_mass")
    omega = _omega(frequency)
    t = np.asarray(transmissibility, dtype=np.complex128)
    magnitude = np.abs(t)
    if np.any(magnitude > TRANSMISSIBILITY_LIMIT):
        worst = float(np.max(magnitude))
        warnings.warn(
            f"|T| up to {worst:.3g} exceeds {TRANSMISSIBILITY_LIMIT:g} "
            "(DeltaL1,2 < 20 dB): ISO 10846-3 Inequality (2) is violated and "
            "the T << 1 approximation of Formula (1) is no longer accurate "
            "within 1 dB (12 %); those bands lie outside the valid frequency "
            "range of the indirect method.",
            PhonometryWarning,
            stacklevel=2,
        )
    return np.asarray(
        -(omega**2) * (blocking_mass + flange_mass) * t, dtype=np.complex128
    )


def base_transmissibility(
    frequency: ArrayLike, mass: float, stiffness: float, damping: float = 0.0
) -> np.ndarray:
    """Transmissibility of a mass on an ideal resilient element (model).

    The output mass ``m`` on a massless Kelvin-Voigt element (spring ``k`` in
    parallel with a viscous damper ``c``) driven at the input has the
    base-excitation transmissibility

    ``T = u2/u1 = (k + j omega c) / (k - omega**2 m + j omega c)``.

    This ideal-element model is the counterpart of the indirect-method test
    arrangement (ISO 10846-3): feeding ``T`` into :func:`transfer_stiffness_indirect`
    with the same mass recovers the element's transfer stiffness ``k + j omega c``
    in the high-frequency limit ``T << 1``.

    :param frequency: Frequency ``f``, in hertz (scalar or array).
    :param mass: Output mass ``m``, in kg.
    :param stiffness: Element stiffness ``k``, in N/m.
    :param damping: Viscous damping ``c``, in N.s/m (Default: 0.0).
    :return: The complex transmissibility ``T``.
    """
    mass = require_positive(mass, "mass")
    stiffness = require_positive(stiffness, "stiffness")
    damping = require_non_negative(damping, "damping")
    omega = _omega(frequency)
    numerator = stiffness + 1j * omega * damping
    denominator = stiffness - omega**2 * mass + 1j * omega * damping
    return np.asarray(numerator / denominator, dtype=np.complex128)


@dataclass(frozen=True)
class TransferStiffnessResult:
    """A dynamic transfer stiffness over frequency (ISO 10846).

    :ivar frequencies: Frequencies, in hertz.
    :ivar transfer_stiffness: Complex ``k2,1`` per frequency, in N/m.
    :ivar blocking_mass: Blocking mass ``m2`` used (indirect method), in kg, or
        ``None`` for the direct method.
    """

    frequencies: np.ndarray
    transfer_stiffness: np.ndarray
    blocking_mass: float | None = None

    @property
    def magnitude(self) -> np.ndarray:
        """Transfer-stiffness magnitude ``|k2,1|``, in N/m."""
        return np.abs(self.transfer_stiffness)

    @property
    def level(self) -> np.ndarray:
        """Transfer-stiffness level ``L_k`` re 1 N/m, in dB (3.17)."""
        return transfer_stiffness_level(self.transfer_stiffness)

    @property
    def loss_factor(self) -> np.ndarray:
        """Loss factor ``eta = Im/Re`` per frequency (3.8)."""
        return loss_factor(self.transfer_stiffness)

    def to(self, target: str) -> np.ndarray:
        """Convert ``k2,1`` to a related FRF (ISO 10846-1 Annex A / Table A.2).

        ``target`` is ``"impedance"`` (``Z = k/(j omega)``) or
        ``"apparent_mass"`` (``m_eff = -k/omega**2``); see
        :func:`phonometry.convert_frf`.
        """
        return convert_frf(
            self.transfer_stiffness, self.frequencies, "dynamic_stiffness", target
        )

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the transfer-stiffness level ``L_k(f)``.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from .._plot.vibration import plot_transfer_stiffness

        return plot_transfer_stiffness(self, ax=ax, **kwargs)


def indirect_transfer_stiffness_result(
    frequency: ArrayLike,
    transmissibility: ArrayLike,
    blocking_mass: float,
    *,
    flange_mass: float = 0.0,
) -> TransferStiffnessResult:
    """Indirect-method transfer stiffness bundled as a :class:`TransferStiffnessResult`.

    See :func:`transfer_stiffness_indirect` for the ISO 10846-3 validity
    conditions (Inequalities (2) and (3)); bands with ``|T| > 0.1`` trigger a
    :class:`~phonometry.PhonometryWarning`.

    :param frequency: Frequencies ``f``, in hertz (array).
    :param transmissibility: Vibration transmissibility ``T = u2/u1`` (complex).
    :param blocking_mass: Blocking mass ``m2``, in kg (> 0).
    :param flange_mass: Output-flange mass ``mf``, in kg (Default: 0.0).
    :return: The :class:`TransferStiffnessResult` (indirect method).
    :warns PhonometryWarning: where any ``|T| > 0.1`` (Inequality (2) violated).
    """
    freq = np.asarray(frequency, dtype=np.float64)
    k = transfer_stiffness_indirect(
        freq, transmissibility, blocking_mass, flange_mass=flange_mass
    )
    return TransferStiffnessResult(
        frequencies=freq, transfer_stiffness=k, blocking_mass=float(blocking_mass)
    )
