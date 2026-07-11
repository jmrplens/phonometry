#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Structure-borne sound power of building equipment (EN 15657:2018).

Building service equipment (pumps, fans, boilers, sanitary appliances) injects
**structure-borne sound power** into the building structure it is fixed to.
EN 15657 characterises a source by its *characteristic structure-borne sound
power level* ``L_Ws`` measured with the **reception-plate method**: the source
is mounted on a plate of known mass per unit area ``m`` and area ``S`` whose
structural loss factor ``eta`` is known, and the spatial-average vibratory
velocity level of the plate is measured.

The power a resonant plate dissipates equals ``P = omega * eta * (m S) *
<v**2>``, so the injected power level in one-third-octave bands is (Formula 14)::

    L_Ws = 10 lg(2 pi f eta m S / (f0 m0 S0)) + L_v - 60   [dB re 1 pW]

with the references ``f0 = 1 Hz``, ``m0 = 1 kg``, ``S0 = 1 m2``; the fixed
``-60 dB`` term is ``10 lg(v0**2 / P0)`` for the EN 15657 velocity reference
``v0 = 1e-9 m/s`` and ``P0 = 1 pW``. The spatial mean velocity level is the
energetic average over the ``N`` plate positions (Formula 12)::

    L_v = 10 lg( (1/N) sum 10^(L_v,i/10) )

and the plate loss factor follows from its structural reverberation time ``Ts``
(Formula 13, identical to the ISO 10848 total loss factor)::

    eta = 2.2 / (f Ts)

Two reception plates are used: a *low-mobility* plate (its point mobility and
loss factor are unchanged by the source) and a *high-mobility* plate (loaded by
the source). The characteristic power level plus the plate mobility feed the
installed structure-borne source model of EN 12354-5. The source-side free
velocity level of ISO 9611 (re ``5e-8 m/s``) is the direct-measurement
counterpart.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

from numpy.typing import ArrayLike

from ._validation import require_positive
from .flanking_transmission import total_loss_factor

#: EN 15657 vibratory velocity reference ``v0`` (= ISO 1683 10^-9 m/s), m/s.
REFERENCE_VELOCITY: float = 1.0e-9
#: Reference sound power ``P0``, W.
REFERENCE_SOUND_POWER: float = 1.0e-12


def spatial_mean_velocity_level(levels: ArrayLike) -> float:
    """Spatial-average velocity level over the plate (EN 15657, Formula 12).

    ``L_v = 10 lg( (1/N) sum 10^(L_v,i/10) )`` -- the energetic average of the
    per-position velocity levels.

    :param levels: Velocity levels ``L_v,i`` at the ``N`` positions, in dB.
    :return: The spatial mean velocity level, in dB.
    """
    lv = np.asarray(levels, dtype=np.float64)
    return float(10.0 * np.log10(np.mean(10.0 ** (0.1 * lv))))


def plate_loss_factor(
    frequency: ArrayLike, reverberation_time: ArrayLike
) -> np.ndarray:
    """Plate loss factor ``eta = 2.2 / (f Ts)`` (EN 15657, Formula 13).

    Estimated from the plate's structural reverberation time; identical to the
    ISO 10848 total loss factor.

    :param frequency: Band centre frequency ``f``, in hertz (per band).
    :param reverberation_time: Structural reverberation time ``Ts``, in s.
    :return: The loss factor ``eta`` (dimensionless) per band.
    """
    f = np.asarray(frequency, dtype=np.float64)
    ts = np.asarray(reverberation_time, dtype=np.float64)
    return total_loss_factor(f, ts)


def structure_borne_power_level(
    velocity_level: ArrayLike,
    frequency: ArrayLike,
    mass_per_area: float,
    area: float,
    loss_factor: ArrayLike,
    *,
    reference_velocity: float = REFERENCE_VELOCITY,
) -> np.ndarray:
    """Characteristic structure-borne sound power level (EN 15657, Formula 14).

    ``L_Ws = 10 lg(2 pi f eta m S / (f0 m0 S0)) + L_v + 10 lg(v0**2 / P0)`` --
    the power a resonant reception plate dissipates, expressed as a level re
    1 pW. With the EN 15657 reference ``v0 = 1e-9 m/s`` the last term is -60 dB.

    :param velocity_level: Spatial mean plate velocity level ``L_v`` (scalar or
        per band), in dB re ``v0``.
    :param frequency: Band centre frequency ``f``, in hertz.
    :param mass_per_area: Plate mass per unit area ``m``, in kg/m^2 (> 0).
    :param area: Plate area ``S``, in m^2 (> 0).
    :param loss_factor: Plate loss factor ``eta`` (scalar or per band).
    :param reference_velocity: Velocity reference ``v0`` (Default: 1e-9 m/s).
    :return: The structure-borne sound power level ``L_Ws``, in dB re 1 pW.
    :raises ValueError: for a non-positive mass, area, reference or frequency.
    """
    mass_per_area = require_positive(mass_per_area, "mass_per_area")
    area = require_positive(area, "area")
    reference_velocity = require_positive(reference_velocity, "reference_velocity")
    f = np.asarray(frequency, dtype=np.float64)
    if np.any(f <= 0.0):
        raise ValueError("'frequency' must be positive.")
    lv = np.asarray(velocity_level, dtype=np.float64)
    eta = np.asarray(loss_factor, dtype=np.float64)
    offset = 10.0 * np.log10(reference_velocity**2 / REFERENCE_SOUND_POWER)
    lw = (
        10.0 * np.log10(2.0 * np.pi * f * eta * mass_per_area * area)
        + lv
        + offset
    )
    return np.asarray(lw, dtype=np.float64)


@dataclass(frozen=True)
class StructureBornePowerResult:
    """Characteristic structure-borne sound power of a source (EN 15657).

    :ivar frequencies: Band centre frequencies, in hertz, or ``None``.
    :ivar power_level: Characteristic power level ``L_Ws`` per band, in dB re 1 pW.
    :ivar velocity_level: Spatial mean plate velocity level ``L_v`` per band, dB.
    :ivar loss_factor: Plate loss factor ``eta`` per band.
    :ivar mass_per_area: Plate mass per unit area ``m``, in kg/m^2.
    :ivar area: Plate area ``S``, in m^2.
    """

    power_level: np.ndarray
    velocity_level: np.ndarray
    loss_factor: np.ndarray
    mass_per_area: float
    area: float
    frequencies: np.ndarray | None = None

    @property
    def total_level(self) -> float:
        """Band-summed power level ``10 lg(sum 10^(0.1 L_Ws))``, in dB."""
        lw = np.asarray(self.power_level, dtype=np.float64)
        return float(10.0 * np.log10(np.sum(10.0 ** (0.1 * lw))))

    def plot(self, ax: "Axes | None" = None, **kwargs: Any) -> "Axes":
        """Plot the characteristic structure-borne power level per band.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ._plotting import plot_structure_borne_power

        return plot_structure_borne_power(self, ax=ax, **kwargs)


def reception_plate_power(
    velocity_level: ArrayLike,
    frequency: ArrayLike,
    mass_per_area: float,
    area: float,
    *,
    loss_factor: ArrayLike | None = None,
    reverberation_time: ArrayLike | None = None,
) -> StructureBornePowerResult:
    """Reception-plate structure-borne sound power (EN 15657, clause 7).

    Provide the plate loss factor directly, or its structural reverberation
    time ``Ts`` (from which ``eta = 2.2/(f Ts)`` is computed, Formula 13).

    :param velocity_level: Spatial mean plate velocity level ``L_v`` (per band),
        in dB re 1e-9 m/s (see :func:`spatial_mean_velocity_level`).
    :param frequency: Band centre frequencies ``f``, in hertz.
    :param mass_per_area: Plate mass per unit area ``m``, in kg/m^2 (> 0).
    :param area: Plate area ``S``, in m^2 (> 0).
    :param loss_factor: Plate loss factor ``eta`` (per band), or ``None`` to
        derive it from ``reverberation_time``.
    :param reverberation_time: Structural reverberation time ``Ts``, in s, used
        when ``loss_factor`` is ``None``.
    :return: The :class:`StructureBornePowerResult`.
    :raises ValueError: if neither ``loss_factor`` nor ``reverberation_time``
        is given.
    """
    freq = np.atleast_1d(np.asarray(frequency, dtype=np.float64))
    lv = np.broadcast_to(
        np.asarray(velocity_level, dtype=np.float64), freq.shape
    ).astype(np.float64)
    if loss_factor is not None:
        eta = np.broadcast_to(
            np.asarray(loss_factor, dtype=np.float64), freq.shape
        ).astype(np.float64)
    elif reverberation_time is not None:
        eta = np.asarray(plate_loss_factor(freq, reverberation_time), dtype=np.float64)
    else:
        raise ValueError(
            "provide either 'loss_factor' or 'reverberation_time'."
        )
    lw = structure_borne_power_level(lv, freq, mass_per_area, area, eta)
    return StructureBornePowerResult(
        power_level=np.asarray(lw, dtype=np.float64),
        velocity_level=lv,
        loss_factor=eta,
        mass_per_area=float(mass_per_area),
        area=float(area),
        frequencies=freq,
    )
