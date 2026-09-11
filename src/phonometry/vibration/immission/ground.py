#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The elastic properties of the ground from its wave speeds (DIN 45672-1:2009-12).

DIN 45672-1 is the method of measuring vibration next to a railway line, and
nearly all of it is procedure: where to put the transducers, which directions,
which trains, what to write down. Its Clause 4.5 is the exception. The ground
the vibration travels through is described by the speeds of its compression
and shear waves, and from those two speeds and the density the clause gives
the shear modulus, Poisson's ratio and the elastic modulus, and the shear
strain a vibration puts into the soil.

**Why two speeds are enough.** An unbounded elastic continuum carries two
kinds of wave, and their speeds are fixed by two elastic constants and the
density: :math:`v_s = \sqrt{G/\rho}` for the shear wave (Formula (2)) and
:math:`v_p = \sqrt{2G(1-\nu)/(\rho(1-2\nu))}` for the compression wave. So
measuring both speeds fixes :math:`G` and :math:`\nu`, and with them every
other constant. :math:`v_p > v_s` always; the ratio decides Poisson's ratio
(Formula (3)).

**Why a small strain.** The shear modulus of a soil falls as the strain grows:
Figure 1 has it constant up to a shear strain of about :math:`10^{-4}` and
dropping below 20 % of that value further on. The experiments of the clause and
the vibration of rail traffic both strain the ground around :math:`10^{-6}`, so
the modulus measured is the small-strain maximum and the one that applies.
The strain itself is the velocity amplitude over the shear-wave speed
(Formula (4)).

**Two formulas that are printed wrong.** Formula (1) writes the compression
speed as :math:`\sqrt{E/\rho}`, which is the speed in a thin rod, and as
:math:`\sqrt{G(1-\nu)/(\rho(1-2\nu))}`, which is short of a factor 2; Formula
(5) builds on the first and writes :math:`E = v_p^2 \rho`. Both contradict
Formula (3) of the same clause, which is right, and the two expressions of
Formula (1) only agree with each other at :math:`\nu = (\sqrt{17}-1)/8
\approx 0{,}39`. This module uses the relations of the continuum, which is
what Formula (3) is derived from, and the defect is registered in
``docs/ERRATA.md``.
"""

from __future__ import annotations

import math

from ..._internal.validation import require_positive

__all__ = [
    "GROUND_WAVE_SPEED_RANGES_M_S",
    "SHEAR_STRAIN_LINEAR_LIMIT",
    "compression_wave_speed",
    "poisson_ratio_from_wave_speeds",
    "shear_modulus_from_wave_speed",
    "shear_strain_amplitude",
    "youngs_modulus_from_wave_speeds",
]

#: The wave speeds Clause 4.5.1 gives for natural ground, in metres per
#: second, by the soil or rock it is: compression waves between 200 m/s and
#: 2000 m/s, shear waves between 10 m/s and 1000 m/s.
GROUND_WAVE_SPEED_RANGES_M_S: dict[str, tuple[float, float]] = {
    "compression": (200.0, 2000.0),
    "shear": (10.0, 1000.0),
}

#: The open interval Poisson's ratio of a stable isotropic continuum lies in:
#: at -1 the shear modulus would carry no bulk stiffness at all, and at 0,5
#: the medium would be incompressible and carry no compression wave.
_POISSON_LIMITS = (-1.0, 0.5)

#: The shear strain amplitude up to which Figure 1 has the shear modulus of a
#: soil about constant, in radians. Above it the modulus falls fast; the
#: strains of rail traffic and of the measurements are about a hundredth of it.
SHEAR_STRAIN_LINEAR_LIMIT: float = 1.0e-4


def _speeds(
    compression_wave_speed_m_s: float, shear_wave_speed_m_s: float
) -> tuple[float, float]:
    r"""Both speeds, positive, and a pair a stable continuum can carry.

    Clause 4.5.1 says only that the compression wave is the faster, and that
    is not enough: below :math:`2/\sqrt{3}` times the shear speed the bulk
    modulus :math:`\rho(v_p^2 - 4 v_s^2/3)` is negative, and Poisson's ratio
    below -1.
    """
    v_p = require_positive(compression_wave_speed_m_s, "compression_wave_speed_m_s")
    v_s = require_positive(shear_wave_speed_m_s, "shear_wave_speed_m_s")
    if 3.0 * v_p**2 <= 4.0 * v_s**2:
        msg = (
            "a stable continuum carries its compression wave faster than "
            f"2/sqrt(3) times its shear wave; got v_p = {v_p:g} m/s and "
            f"v_s = {v_s:g} m/s."
        )
        raise ValueError(msg)
    return v_p, v_s


def shear_modulus_from_wave_speed(
    shear_wave_speed_m_s: float, *, density_kg_m3: float
) -> float:
    r"""The shear modulus :math:`G = v_s^2 \rho`, Formula (5), in pascals.

    :param shear_wave_speed_m_s: :math:`v_s`, in metres per second.
    :param density_kg_m3: :math:`\rho`, in kilograms per cubic metre.
    :return: :math:`G`, in pascals.
    :raises ValueError: For a non-positive speed or density.
    """
    v_s = require_positive(shear_wave_speed_m_s, "shear_wave_speed_m_s")
    rho = require_positive(density_kg_m3, "density_kg_m3")
    return v_s**2 * rho


def poisson_ratio_from_wave_speeds(
    compression_wave_speed_m_s: float, shear_wave_speed_m_s: float
) -> float:
    r"""Poisson's ratio from the two wave speeds, Formula (3).

    :math:`\nu = (v_p^2 - 2 v_s^2) / (2 (v_p^2 - v_s^2))`, the inversion of
    the continuum relations and the formula of Clause 4.5.1 that is printed
    right.

    :param compression_wave_speed_m_s: :math:`v_p`, in metres per second.
    :param shear_wave_speed_m_s: :math:`v_s`, in metres per second.
    :return: :math:`\nu`, between -1 and 0,5. It is positive when :math:`v_p`
        exceeds :math:`\sqrt{2}\,v_s`, as it does in every soil; a pair
        between :math:`2/\sqrt{3}` and :math:`\sqrt{2}` gives the negative
        ratio a continuum allows and a soil does not show.
    :raises ValueError: For a non-positive speed, or a compression wave no
        faster than :math:`2/\sqrt{3}` times the shear wave, which no stable
        continuum carries.
    """
    v_p, v_s = _speeds(compression_wave_speed_m_s, shear_wave_speed_m_s)
    return (v_p**2 - 2.0 * v_s**2) / (2.0 * (v_p**2 - v_s**2))


def youngs_modulus_from_wave_speeds(
    compression_wave_speed_m_s: float,
    shear_wave_speed_m_s: float,
    *,
    density_kg_m3: float,
) -> float:
    r"""The elastic modulus from the two wave speeds, in pascals.

    :math:`E = 2G(1+\nu) = \rho v_s^2 (3 v_p^2 - 4 v_s^2)/(v_p^2 - v_s^2)`,
    which is what Formula (5) means. As printed it reads :math:`E = v_p^2
    \rho`, the thin-rod relation, and that overstates the modulus of a soil
    with :math:`\nu = 0{,}3` by 35 % and of one with :math:`\nu = 0{,}45` by a
    factor of 3,8.

    :param compression_wave_speed_m_s: :math:`v_p`, in metres per second.
    :param shear_wave_speed_m_s: :math:`v_s`, in metres per second.
    :param density_kg_m3: :math:`\rho`, in kilograms per cubic metre.
    :return: :math:`E`, in pascals.
    :raises ValueError: As :func:`poisson_ratio_from_wave_speeds`, or for a
        non-positive density.
    """
    nu = poisson_ratio_from_wave_speeds(
        compression_wave_speed_m_s, shear_wave_speed_m_s
    )
    g = shear_modulus_from_wave_speed(shear_wave_speed_m_s, density_kg_m3=density_kg_m3)
    return 2.0 * g * (1.0 + nu)


def compression_wave_speed(
    shear_modulus_pa: float, *, poisson_ratio: float, density_kg_m3: float
) -> float:
    r"""The compression-wave speed of a continuum, Formula (1) corrected, in m/s.

    :math:`v_p = \sqrt{2G(1-\nu)/(\rho(1-2\nu))}`, the speed of a P-wave in an
    unbounded medium, whose inverse is Formula (3). Formula (1) prints the
    radicand without the factor 2, which gives a speed :math:`\sqrt{2}` too
    slow at every Poisson's ratio.

    :param shear_modulus_pa: :math:`G`, in pascals.
    :param poisson_ratio: :math:`\nu`, above -1 and below 0,5.
    :param density_kg_m3: :math:`\rho`, in kilograms per cubic metre.
    :return: :math:`v_p`, in metres per second.
    :raises ValueError: For a non-positive modulus or density, or a ratio
        outside ``(-1, 0.5)``, where the continuum would not be stable.
    """
    g = require_positive(shear_modulus_pa, "shear_modulus_pa")
    rho = require_positive(density_kg_m3, "density_kg_m3")
    nu = float(poisson_ratio)
    if not _POISSON_LIMITS[0] < nu < _POISSON_LIMITS[1]:
        msg = f"'poisson_ratio' must lie in (-1, 0.5); got {poisson_ratio!r}."
        raise ValueError(msg)
    return math.sqrt(2.0 * g * (1.0 - nu) / (rho * (1.0 - 2.0 * nu)))


def shear_strain_amplitude(
    velocity_amplitude_m_s: float, *, shear_wave_speed_m_s: float
) -> float:
    r"""The shear strain amplitude :math:`\hat\gamma = \hat v / v_s`, Formula (4).

    Compare it with :data:`SHEAR_STRAIN_LINEAR_LIMIT` to know whether the
    small-strain modulus still applies.

    :param velocity_amplitude_m_s: :math:`\hat v`, the velocity amplitude, in
        metres per second (not millimetres: the strain is a ratio of the two
        speeds).
    :param shear_wave_speed_m_s: :math:`v_s`, in metres per second.
    :return: :math:`\hat\gamma`, in radians.
    :raises ValueError: For a negative amplitude or a non-positive speed.
    """
    v = float(velocity_amplitude_m_s)
    if not math.isfinite(v) or v < 0.0:
        msg = (
            "'velocity_amplitude_m_s' must be finite and non-negative; "
            f"got {velocity_amplitude_m_s!r}."
        )
        raise ValueError(msg)
    v_s = require_positive(shear_wave_speed_m_s, "shear_wave_speed_m_s")
    return v / v_s
