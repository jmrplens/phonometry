#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Airflow resistance of porous materials: ISO 9053-1 and ISO 9053-2.

Two standardised measurement methods share the same three quantities and units
(ISO 9053-1:2018, Clause 3; ISO 9053-2:2020, Clause 3):

- **Airflow resistance** ``R = dp / q_v`` in Pa*s/m3, with ``dp`` the air pressure
  difference across the specimen (Pa) and ``q_v`` the volumetric airflow rate
  through it (m3/s) (ISO 9053-1:2018, 3.1).
- **Specific airflow resistance** ``R_s = R * A`` in **Pa*s/m** (not Pa*s/m2),
  with ``A`` the cross-sectional area of the specimen perpendicular to the flow
  (m2) (ISO 9053-1:2018, 3.2). Equivalently ``R_s = dp / u`` with ``u`` the linear
  airflow velocity, since ``u = q_v / A``.
- **Airflow resistivity** ``sigma = R_s / d`` in Pa*s/m2, with ``d`` the specimen
  thickness in the flow direction (m), for homogeneous materials
  (ISO 9053-1:2018, 3.3). Equivalently ``sigma = R * A / d``.

The linear airflow velocity is ``u = q_v / A`` (ISO 9053-1:2018, 3.4).

**Static (DC) method, ISO 9053-1:2018.** A steady unidirectional flow in the
laminar regime is used. The recommended reference linear airflow velocity is
``u = 0.5e-3 m/s`` (0.5 mm/s, clause 7.5); if measured stepwise the highest
velocity shall not exceed ``15e-3 m/s`` (15 mm/s), beyond which the flow may be
non-linear. When measured stepwise the pressure difference is plotted against
``u`` and fitted with a regression of at least second order constrained through
the origin, ``dp = a*u + b*u**2``; ``dp`` and ``R_s`` are then evaluated at
``u = 0.5e-3 m/s`` (clause 7.5). Because ``R_s = dp / u = a + b*u``, the linear
coefficient ``a`` is the zero-velocity specific airflow resistance.

**Alternating (AC) method, ISO 9053-2:2020.** A sinusoidally moving piston
(frequency 1 Hz to 4 Hz, typically 2 Hz; clause 6.2) drives an alternating volume
flow into an air cavity terminated either by the specimen or by an airtight
termination. The airflow resistance follows from the sound-pressure-level
difference between the two terminations (ISO 9053-2:2020, Formula (2), 8.7)::

    R = kappa' * P_S / (2*pi*f*V) * (h_t/h_s) * 10**((L_ps - L_pt)/20)

with ``kappa'`` the effective ratio of specific heats for air (Annex A),
``P_S`` the static (atmospheric) pressure (Pa), ``f`` the piston frequency (Hz),
``V`` the cavity volume with the airtight termination (m3), ``h_t``/``h_s`` the
piston stroke amplitudes with the airtight termination / specimen cell, and
``L_ps``/``L_pt`` the cavity sound pressure levels with the specimen /
airtight termination (dB). Only the level *difference* enters, so the sound level
device needs no absolute calibration (clause 8.7). The RMS piston volume flow is
``q_v = 2*pi*f*h*A_P`` (ISO 9053-2:2020, 6.2), with ``h`` the stroke amplitude
and ``A_P`` the piston cross-sectional area.

Neither part defines a temperature/atmospheric normalisation of the result; the
adiabatic value ``kappa = 1.4`` is used as the default for ``kappa'``.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

#: Standard atmospheric (static) pressure ``P_S`` (Pa), ISO 9053-2:2020 Formula (2).
_STANDARD_STATIC_PRESSURE = 101325.0
#: Adiabatic ratio of specific heats for air; default for ``kappa'`` (ISO 9053-2 Annex A).
_ADIABATIC_KAPPA = 1.4
#: Reference linear airflow velocity, ISO 9053-1:2018 clause 7.5 (m/s).
_STATIC_REFERENCE_VELOCITY = 0.5e-3
#: Upper linear-velocity limit of the static method, ISO 9053-1:2018 clause 7.5 (m/s).
_STATIC_MAX_VELOCITY = 15.0e-3
#: Recommended specimen flow-velocity range, ISO 9053-2:2020 clause 6.2 (m/s).
_ALT_VELOCITY_RANGE = (0.5e-3, 4.0e-3)
#: Piston frequency range, ISO 9053-2:2020 clause 6.2 (Hz).
_ALT_FREQUENCY_RANGE = (1.0, 4.0)
#: Upper bound of the validity criterion, ISO 9053-2:2020 Formula (3).
_ALT_VALIDITY_LIMIT = 0.3
#: Required specimen-to-background level margin, ISO 9053-2:2020 Formula (4) (dB).
_ALT_BACKGROUND_MARGIN = 10.0


class AirflowResistanceWarning(UserWarning):
    """Advisory for out-of-range or non-conforming ISO 9053 airflow inputs."""


@dataclass(frozen=True)
class StaticAirflowResult:
    """Result of an ISO 9053-1:2018 stepwise (static-method) determination.

    ``resistance`` (``R``, Pa*s/m3), ``specific_resistance`` (``R_s``, Pa*s/m) and
    ``resistivity`` (``sigma``, Pa*s/m2; ``None`` when no thickness is supplied)
    are evaluated at ``evaluation_velocity`` (m/s, the ISO 9053-1 clause 7.5
    reference 0.5 mm/s by default). ``linear_coefficient`` (``a``) and
    ``quadratic_coefficient`` (``b``) are the through-origin fit
    ``dp = a*u + b*u**2`` (clause 7.5); ``a`` is the zero-velocity specific
    airflow resistance (Pa*s/m). ``pressure_drop`` is the fitted ``dp`` at
    ``evaluation_velocity`` (Pa).
    """

    resistance: float
    specific_resistance: float
    resistivity: float | None
    evaluation_velocity: float
    pressure_drop: float
    linear_coefficient: float
    quadratic_coefficient: float


def linear_airflow_velocity(volume_flow_rate: float, area: float) -> float:
    """Linear airflow velocity ``u = q_v / A`` (ISO 9053-1:2018, 3.4).

    ``volume_flow_rate`` is ``q_v`` (m3/s) and ``area`` is ``A`` (m2); returns
    ``u`` in m/s.
    """
    if volume_flow_rate < 0.0:
        raise ValueError("'volume_flow_rate' must be non-negative.")
    if area <= 0.0:
        raise ValueError("'area' must be positive.")
    return volume_flow_rate / area


def airflow_resistance(pressure_drop: float, volume_flow_rate: float) -> float:
    """Airflow resistance ``R = dp / q_v`` (ISO 9053-1:2018, 3.1).

    ``pressure_drop`` is the pressure difference ``dp`` across the specimen (Pa)
    and ``volume_flow_rate`` is the volumetric airflow rate ``q_v`` (m3/s).
    Returns ``R`` in Pa*s/m3.
    """
    if pressure_drop < 0.0:
        raise ValueError("'pressure_drop' must be non-negative.")
    if volume_flow_rate <= 0.0:
        raise ValueError("'volume_flow_rate' must be positive.")
    return pressure_drop / volume_flow_rate


def specific_airflow_resistance(
    resistance: float | None = None,
    area: float | None = None,
    *,
    pressure_drop: float | None = None,
    velocity: float | None = None,
) -> float:
    """Specific airflow resistance ``R_s`` in Pa*s/m (ISO 9053-1:2018, 3.2).

    Two equivalent routes are accepted; supply exactly one:

    - ``resistance`` (``R``, Pa*s/m3) and ``area`` (``A``, m2): ``R_s = R * A``.
    - ``pressure_drop`` (``dp``, Pa) and ``velocity`` (``u``, m/s): ``R_s = dp/u``
      (from ``R_s = R*A`` with ``u = q_v/A``).

    The unit is pascal second per metre (Pa*s/m), not Pa*s/m2.
    """
    from_resistance = resistance is not None and area is not None
    from_pressure = pressure_drop is not None and velocity is not None
    if from_resistance == from_pressure:
        raise ValueError(
            "Provide exactly one route: ('resistance' and 'area') or "
            "('pressure_drop' and 'velocity')."
        )
    if resistance is not None and area is not None:
        if resistance < 0.0:
            raise ValueError("'resistance' must be non-negative.")
        if area <= 0.0:
            raise ValueError("'area' must be positive.")
        return resistance * area
    if pressure_drop is not None and velocity is not None:
        if pressure_drop < 0.0:
            raise ValueError("'pressure_drop' must be non-negative.")
        if velocity <= 0.0:
            raise ValueError("'velocity' must be positive.")
        return pressure_drop / velocity
    raise ValueError(  # pragma: no cover - unreachable, guarded above
        "Provide exactly one route: ('resistance' and 'area') or "
        "('pressure_drop' and 'velocity')."
    )


def airflow_resistivity(specific_resistance: float, thickness: float) -> float:
    """Airflow resistivity ``sigma = R_s / d`` in Pa*s/m2 (ISO 9053-1:2018, 3.3).

    ``specific_resistance`` is ``R_s`` (Pa*s/m) and ``thickness`` is ``d`` (m),
    the specimen thickness in the flow direction. Returns ``sigma`` in Pa*s/m2.
    """
    if specific_resistance < 0.0:
        raise ValueError("'specific_resistance' must be non-negative.")
    if thickness <= 0.0:
        raise ValueError("'thickness' must be positive.")
    return specific_resistance / thickness


def _warn_static_velocity_range(velocities: NDArray[np.float64], stacklevel: int) -> None:
    """Advise when a stepwise velocity exceeds the ISO 9053-1 clause 7.5 limit."""
    top = float(np.max(velocities))
    if top > _STATIC_MAX_VELOCITY:
        warnings.warn(
            f"Highest linear airflow velocity {top:g} m/s exceeds the "
            f"{_STATIC_MAX_VELOCITY:g} m/s limit of ISO 9053-1:2018 clause 7.5; "
            "the flow may be non-linear and the result is advisory.",
            AirflowResistanceWarning,
            stacklevel=stacklevel,
        )


def static_airflow_resistance(
    velocities: ArrayLike,
    pressure_drops: ArrayLike,
    area: float,
    thickness: float | None = None,
    *,
    evaluation_velocity: float = _STATIC_REFERENCE_VELOCITY,
) -> StaticAirflowResult:
    """Stepwise static-method airflow resistance (ISO 9053-1:2018, clause 7.5).

    Fits the measured pressure difference against the linear airflow velocity with
    a second-order regression constrained through the origin,
    ``dp = a*u + b*u**2``, and evaluates the resistances at
    ``evaluation_velocity`` (the clause 7.5 reference ``0.5e-3 m/s`` by default).

    ``velocities`` are the linear airflow velocities ``u`` (m/s) and
    ``pressure_drops`` the matching pressure differences ``dp`` (Pa) of at least
    two measurement steps; ``area`` is the cross-section ``A`` (m2) and
    ``thickness`` the specimen thickness ``d`` (m, optional, enabling ``sigma``).

    Because ``R_s = dp/u = a + b*u``, the returned ``linear_coefficient`` ``a`` is
    the zero-velocity specific airflow resistance. A velocity above the clause 7.5
    upper limit (15 mm/s) raises :class:`AirflowResistanceWarning`.
    """
    u = np.asarray(velocities, dtype=np.float64)
    dp = np.asarray(pressure_drops, dtype=np.float64)
    if u.ndim != 1 or dp.ndim != 1:
        raise ValueError("'velocities' and 'pressure_drops' must be 1-D.")
    if u.shape != dp.shape:
        raise ValueError("'velocities' and 'pressure_drops' must have equal length.")
    if u.size < 2:
        raise ValueError("At least two measurement steps are required.")
    if bool(np.any(u <= 0.0)):
        raise ValueError("All velocities must be positive.")
    if bool(np.any(dp < 0.0)):
        raise ValueError("All pressure drops must be non-negative.")
    if area <= 0.0:
        raise ValueError("'area' must be positive.")
    if thickness is not None and thickness <= 0.0:
        raise ValueError("'thickness' must be positive.")
    if evaluation_velocity <= 0.0:
        raise ValueError("'evaluation_velocity' must be positive.")

    _warn_static_velocity_range(u, stacklevel=2)

    # Through-origin second-order fit: dp = a*u + b*u**2 (no constant term).
    design = np.stack([u, u**2], axis=1)
    coeffs, _residuals, _rank, _sv = np.linalg.lstsq(design, dp, rcond=None)
    a = float(coeffs[0])
    b = float(coeffs[1])

    dp_eval = a * evaluation_velocity + b * evaluation_velocity**2
    specific = dp_eval / evaluation_velocity  # R_s = dp/u = a + b*u
    resistance = specific / area  # R = R_s / A
    resistivity = None if thickness is None else specific / thickness

    return StaticAirflowResult(
        resistance=resistance,
        specific_resistance=specific,
        resistivity=resistivity,
        evaluation_velocity=evaluation_velocity,
        pressure_drop=dp_eval,
        linear_coefficient=a,
        quadratic_coefficient=b,
    )


def piston_volume_flow_rate(
    frequency: float, stroke_amplitude: float, piston_area: float
) -> float:
    """RMS piston volume flow ``q_v = 2*pi*f*h*A_P`` (ISO 9053-2:2020, 6.2).

    ``frequency`` is the piston frequency ``f`` (Hz), ``stroke_amplitude`` the
    stroke amplitude ``h`` (m) and ``piston_area`` the piston cross-section
    ``A_P`` (m2). Returns ``q_v`` in m3/s.
    """
    if frequency <= 0.0:
        raise ValueError("'frequency' must be positive.")
    if stroke_amplitude < 0.0:
        raise ValueError("'stroke_amplitude' must be non-negative.")
    if piston_area <= 0.0:
        raise ValueError("'piston_area' must be positive.")
    return 2.0 * math.pi * frequency * stroke_amplitude * piston_area


def _warn_alternating_validity(
    ratio_term: float,
    level_specimen: float,
    background_level: float | None,
    stacklevel: int,
) -> None:
    """Check the ISO 9053-2:2020 Formula (3)/(4) validity criteria."""
    if not ratio_term < _ALT_VALIDITY_LIMIT:
        warnings.warn(
            f"Validity term (h_t/h_s)*10**((L_ps-L_pt)/20) = {ratio_term:g} is not "
            f"below {_ALT_VALIDITY_LIMIT:g} (ISO 9053-2:2020 Formula (3)); adjust "
            "specimen size, cavity volume, piston frequency or stroke length.",
            AirflowResistanceWarning,
            stacklevel=stacklevel,
        )
    if background_level is not None and not (
        level_specimen - background_level > _ALT_BACKGROUND_MARGIN
    ):
        warnings.warn(
            f"Specimen-to-background margin {level_specimen - background_level:g} dB "
            f"is not above {_ALT_BACKGROUND_MARGIN:g} dB (ISO 9053-2:2020 "
            "Formula (4)); background noise may bias the result.",
            AirflowResistanceWarning,
            stacklevel=stacklevel,
        )


def alternating_airflow_resistance(
    level_specimen: float,
    level_termination: float,
    *,
    piston_stroke_specimen: float,
    piston_stroke_termination: float,
    frequency: float,
    cavity_volume: float,
    static_pressure: float = _STANDARD_STATIC_PRESSURE,
    kappa_prime: float = _ADIABATIC_KAPPA,
    background_level: float | None = None,
) -> float:
    """Alternating-method airflow resistance (ISO 9053-2:2020, Formula (2), 8.7).

    Implements::

        R = kappa' * P_S / (2*pi*f*V) * (h_t/h_s) * 10**((L_ps - L_pt)/20)

    ``level_specimen`` (``L_ps``) and ``level_termination`` (``L_pt``) are the
    cavity sound pressure levels (dB) with the specimen cell and the airtight
    termination; ``piston_stroke_specimen`` (``h_s``) and
    ``piston_stroke_termination`` (``h_t``) the corresponding stroke amplitudes
    (m); ``frequency`` the piston frequency ``f`` (Hz, 1-4 Hz); ``cavity_volume``
    the airtight-termination cavity volume ``V`` (m3); ``static_pressure`` the
    atmospheric pressure ``P_S`` (Pa, default 101325); ``kappa_prime`` the
    effective ratio of specific heats ``kappa'`` (Annex A, default 1.4);
    ``background_level`` the optional cavity background level ``L_pb`` (dB) for the
    Formula (4) check. Returns ``R`` in Pa*s/m3.

    Emits :class:`AirflowResistanceWarning` when the piston frequency is outside
    1-4 Hz or when the Formula (3)/(4) validity criteria are not met.
    """
    if frequency <= 0.0:
        raise ValueError("'frequency' must be positive.")
    if cavity_volume <= 0.0:
        raise ValueError("'cavity_volume' must be positive.")
    if piston_stroke_specimen <= 0.0:
        raise ValueError("'piston_stroke_specimen' must be positive.")
    if piston_stroke_termination <= 0.0:
        raise ValueError("'piston_stroke_termination' must be positive.")
    if static_pressure <= 0.0:
        raise ValueError("'static_pressure' must be positive.")
    if kappa_prime <= 0.0:
        raise ValueError("'kappa_prime' must be positive.")

    low, high = _ALT_FREQUENCY_RANGE
    if not low <= frequency <= high:
        warnings.warn(
            f"Piston frequency {frequency:g} Hz is outside the ISO 9053-2:2020 "
            f"clause 6.2 range [{low:g}, {high:g}] Hz; the result is advisory.",
            AirflowResistanceWarning,
            stacklevel=2,
        )

    stroke_ratio = piston_stroke_termination / piston_stroke_specimen
    level_factor = float(10.0 ** ((level_specimen - level_termination) / 20.0))
    ratio_term = stroke_ratio * level_factor
    _warn_alternating_validity(ratio_term, level_specimen, background_level, stacklevel=2)

    prefactor = kappa_prime * static_pressure / (2.0 * math.pi * frequency * cavity_volume)
    return prefactor * ratio_term
