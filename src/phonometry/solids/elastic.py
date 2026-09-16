#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Three longitudinal wave speeds of a solid, and which one a table prints.

A solid carries more than one longitudinal wave, and which one a number belongs
to depends on the shape the wave travels in, not on the material. The three are

.. math::

   c_{\mathrm{L,b}} = \sqrt{\frac{E}{\rho}}
   \qquad\text{for a beam}

   c_{\mathrm{L,p}} = \sqrt{\frac{E}{\rho\,(1 - \nu^2)}}
   \qquad\text{for a plate}

   c'_{\mathrm{L}} = \sqrt{\frac{E\,(1 - \nu)}{\rho\,(1 + \nu)(1 - 2\nu)}}
   \qquad\text{in an unbounded solid}

and they are not interchangeable. Take the steel of Hopkins Table A2,
``rho = 7800`` kg/m3, ``nu = 0.28`` and a plate speed of 5 270 m/s, which is a
Young's modulus of 200 GPa: the beam speed is 5 059 m/s and the bulk speed is
5 720 m/s. Reading one into another is a four to nine per cent error in
whatever it feeds, and the gap grows with Poisson's ratio. The first two are
Hopkins (2007) Eqs. (2.20) and
(2.21), PDF page 144 (printed p. 117), which also records that the ``b`` and
``p`` subscripts are dropped later in that book and the plate value is then
called ``cL`` with no qualifier at all. The third is Norton & Karczub (2003)
2e Eq. (1.225), PDF page 94 (printed p. 74), the wave velocity of a *pure*
longitudinal wave, after Fahy.

Which one a printed table holds has to be read off its own page, and the
answer is not always the one the column heading suggests. EN 12354-1 Table B.3,
Hopkins Table A2 and Mechel Table 3 tabulate the plate value; a table of
*bulk* wave speeds, which is what an elastic solver integrates, is a different
table. This module exists so the conversion between them is written once,
named after the shape it belongs to, and never done in a caller's head.

Each speed has its inverse here as well, because a catalogue is built from
whatever its sources happened to print: Hopkins prints the plate speed and no
Young's modulus, Cremer and Mechel print the modulus and no speed, and the two
only meet through these six functions.
"""

from __future__ import annotations

import math

from .._internal.validation import require_finite, require_positive

#: Speed of sound in air at 20 degC, the reference the critical-frequency
#: tables of Hopkins, Long and Mechel are printed for.
DEFAULT_SPEED_OF_SOUND_M_S = 343.0

#: Poisson's ratio has to leave ``1 - nu**2`` positive for a plate, which is
#: every ratio a real material has and then some.
_PLATE_POISSON_LIMIT = 1.0

#: An unbounded solid also needs ``1 - 2 nu`` positive: at ``nu = 0.5`` the
#: material is incompressible and the pure longitudinal wave has no speed.
_BULK_POISSON_LIMIT = 0.5


def _require_plate_poisson(poisson_ratio: float) -> float:
    """Poisson's ratio for a plate, which needs ``1 - nu**2`` above zero."""
    value = require_finite(poisson_ratio, "poisson_ratio")
    if abs(value) >= _PLATE_POISSON_LIMIT:
        msg = (
            f"poisson_ratio must lie between -1 and 1 for a plate, got {value}: "
            "the plate wave speed divides by 1 - nu**2"
        )
        raise ValueError(msg)
    return value


def _require_bulk_poisson(poisson_ratio: float) -> float:
    """Poisson's ratio in an unbounded solid, which also needs ``1 - 2 nu``."""
    value = require_finite(poisson_ratio, "poisson_ratio")
    if not -_PLATE_POISSON_LIMIT < value < _BULK_POISSON_LIMIT:
        msg = (
            f"poisson_ratio must lie between -1 and 0.5 in an unbounded solid, "
            f"got {value}: at 0.5 the material is incompressible and the pure "
            "longitudinal wave has no speed"
        )
        raise ValueError(msg)
    return value


def beam_longitudinal_speed(youngs_modulus_pa: float, *, density_kg_m3: float) -> float:
    r"""Quasi-longitudinal wave speed along a beam (Hopkins Eq. 2.20).

    :math:`c_\mathrm{L,b} = \sqrt{E / \rho}`. A beam is unconstrained on its
    sides, so the lateral strains cost nothing and Poisson's ratio does not
    appear.

    :param youngs_modulus_pa: Young's modulus ``E``, in pascals (> 0).
    :param density_kg_m3: Density ``rho``, in kg/m3 (> 0).
    :return: The wave speed, in m/s.
    :raises ValueError: for a non-positive input.
    """
    modulus = require_positive(youngs_modulus_pa, "youngs_modulus_pa")
    density = require_positive(density_kg_m3, "density_kg_m3")
    return math.sqrt(modulus / density)


def plate_longitudinal_speed(
    youngs_modulus_pa: float, *, density_kg_m3: float, poisson_ratio: float
) -> float:
    r"""Quasi-longitudinal wave speed along a plate (Hopkins Eq. 2.21).

    :math:`c_\mathrm{L,p} = \sqrt{E / (\rho (1 - \nu^2))}`. The plate is
    constrained across its width, which stiffens it by :math:`1/(1 - \nu^2)`
    against the beam of :func:`beam_longitudinal_speed`.

    This is the value the building-acoustics tables print, and the one the
    critical frequency of a wall or floor is computed from.

    :param youngs_modulus_pa: Young's modulus ``E``, in pascals (> 0).
    :param density_kg_m3: Density ``rho``, in kg/m3 (> 0).
    :param poisson_ratio: Poisson's ratio ``nu``, between -1 and 1.
    :return: The wave speed, in m/s.
    :raises ValueError: for a non-positive input or a ratio out of range.
    """
    modulus = require_positive(youngs_modulus_pa, "youngs_modulus_pa")
    density = require_positive(density_kg_m3, "density_kg_m3")
    nu = _require_plate_poisson(poisson_ratio)
    return math.sqrt(modulus / (density * (1.0 - nu**2)))


def bulk_longitudinal_speed(
    youngs_modulus_pa: float, *, density_kg_m3: float, poisson_ratio: float
) -> float:
    r"""Pure longitudinal wave speed in an unbounded solid (Norton Eq. 1.225).

    :math:`c'_\mathrm{L} = \sqrt{B / \rho}` with the longitudinal modulus
    :math:`B = E (1 - \nu) / ((1 + \nu)(1 - 2\nu))`. Nothing is free to move
    sideways, which is why this is the fastest of the three and why it is the
    speed an elastic solver integrates.

    :param youngs_modulus_pa: Young's modulus ``E``, in pascals (> 0).
    :param density_kg_m3: Density ``rho``, in kg/m3 (> 0).
    :param poisson_ratio: Poisson's ratio ``nu``, between -1 and 0.5.
    :return: The wave speed, in m/s.
    :raises ValueError: for a non-positive input or a ratio out of range.
    """
    modulus = require_positive(youngs_modulus_pa, "youngs_modulus_pa")
    density = require_positive(density_kg_m3, "density_kg_m3")
    nu = _require_bulk_poisson(poisson_ratio)
    longitudinal = modulus * (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
    return math.sqrt(longitudinal / density)


def youngs_modulus_from_beam_speed(
    longitudinal_speed_m_s: float, *, density_kg_m3: float
) -> float:
    r"""Young's modulus from a beam wave speed, the inverse of Eq. 2.20.

    :math:`E = \rho\, c_\mathrm{L,b}^2`.

    :param longitudinal_speed_m_s: Beam wave speed ``cL,b``, in m/s (> 0).
    :param density_kg_m3: Density ``rho``, in kg/m3 (> 0).
    :return: Young's modulus ``E``, in pascals.
    :raises ValueError: for a non-positive input.
    """
    speed = require_positive(longitudinal_speed_m_s, "longitudinal_speed_m_s")
    density = require_positive(density_kg_m3, "density_kg_m3")
    return density * speed**2


def youngs_modulus_from_plate_speed(
    longitudinal_speed_m_s: float, *, density_kg_m3: float, poisson_ratio: float
) -> float:
    r"""Young's modulus from a plate wave speed, the inverse of Eq. 2.21.

    :math:`E = \rho\, c_\mathrm{L,p}^2 (1 - \nu^2)`. This is what turns a table
    that prints ``cL`` and ``nu`` and no modulus, such as Hopkins Table A2,
    into one that can be compared with a table that prints the modulus.

    :param longitudinal_speed_m_s: Plate wave speed ``cL,p``, in m/s (> 0).
    :param density_kg_m3: Density ``rho``, in kg/m3 (> 0).
    :param poisson_ratio: Poisson's ratio ``nu``, between -1 and 1.
    :return: Young's modulus ``E``, in pascals.
    :raises ValueError: for a non-positive input or a ratio out of range.
    """
    speed = require_positive(longitudinal_speed_m_s, "longitudinal_speed_m_s")
    density = require_positive(density_kg_m3, "density_kg_m3")
    nu = _require_plate_poisson(poisson_ratio)
    return density * speed**2 * (1.0 - nu**2)


def youngs_modulus_from_bulk_speed(
    longitudinal_speed_m_s: float, *, density_kg_m3: float, poisson_ratio: float
) -> float:
    r"""Young's modulus from a bulk wave speed, the inverse of Eq. 1.225.

    :math:`E = \rho\, c'^2_\mathrm{L} (1 + \nu)(1 - 2\nu) / (1 - \nu)`.

    :param longitudinal_speed_m_s: Bulk wave speed ``cL'``, in m/s (> 0).
    :param density_kg_m3: Density ``rho``, in kg/m3 (> 0).
    :param poisson_ratio: Poisson's ratio ``nu``, between -1 and 0.5.
    :return: Young's modulus ``E``, in pascals.
    :raises ValueError: for a non-positive input or a ratio out of range.
    """
    speed = require_positive(longitudinal_speed_m_s, "longitudinal_speed_m_s")
    density = require_positive(density_kg_m3, "density_kg_m3")
    nu = _require_bulk_poisson(poisson_ratio)
    return density * speed**2 * (1.0 + nu) * (1.0 - 2.0 * nu) / (1.0 - nu)


def thickness_critical_frequency_product(
    plate_speed_m_s: float,
    *,
    speed_of_sound_m_s: float = DEFAULT_SPEED_OF_SOUND_M_S,
) -> float:
    r"""The ``h f_c`` a materials table prints, from the plate wave speed.

    .. math::

       h f_\mathrm{c} = \frac{c_0^2 \sqrt{12}}{2 \pi\, c_\mathrm{L,p}}

    which is the critical frequency of a thin plate multiplied by the thickness
    it was computed for, so the product is a property of the material alone.
    Hopkins Table A2, Long Table 9.1 and Mechel Table 3 each print this column,
    which makes it the cheapest cross-check there is between three books that
    otherwise share no column at all.

    The constant here is the exact :math:`2\pi/\sqrt{12} = 1.8138` of the
    thin-plate dispersion relation, which is what
    :func:`phonometry.vibration.coincidence_frequency` computes and what
    reproduces the printed column: Hopkins states ``c0 = 343`` m/s in the
    heading of Table A2 and prints 12.3 m Hz for steel, which this returns and
    the rounded 1.8 of ISO 12354-1 misses by 0.8 per cent (12.40).
    :func:`phonometry.building.critical_frequency` keeps the rounded constant,
    because there it is the standard's own arithmetic and not the material's.

    :param plate_speed_m_s: Plate wave speed ``cL,p``, in m/s (> 0).
    :param speed_of_sound_m_s: Speed of sound in air ``c0``, in m/s (> 0).
    :return: The product ``h f_c``, in Hz m.
    :raises ValueError: for a non-positive input.
    """
    speed = require_positive(plate_speed_m_s, "plate_speed_m_s")
    air = require_positive(speed_of_sound_m_s, "speed_of_sound_m_s")
    return air**2 * math.sqrt(12.0) / (2.0 * math.pi * speed)
