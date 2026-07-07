#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Sound absorption in a reverberation room: BS EN ISO 354:2003.

The mean reverberation time of a reverberation room is measured empty and with
the test specimen installed. From those two reverberation times the equivalent
sound absorption area of the specimen is obtained via Sabine's equation, and for
a plane absorber the sound absorption coefficient follows by dividing by the
covered area (ISO 354:2003, Clauses 4 and 8.1).

Equivalent sound absorption area (ISO 354:2003, Eq. (5) empty room / Eq. (7) with
specimen; identical form)::

    A = 55,3 * V / (c * T) - 4 * V * m

with ``V`` the room volume (m3), ``c`` the speed of sound (m/s), ``T`` the
reverberation time (s) and ``m`` the power attenuation coefficient of air (1/m).
The speed of sound follows Eq. (6), valid for 15 degC to 30 degC::

    c = (331 + 0,6 * t/degC) m/s

The equivalent sound absorption area of the specimen and its absorption
coefficient (ISO 354:2003, Eq. (8) and Eq. (9))::

    AT = A2 - A1 = 55,3 * V * (1/(c2*T2) - 1/(c1*T1)) - 4 * V * (m2 - m1)
    alpha_s = AT / S

``alpha_s`` may exceed 1,0 (e.g. from diffraction/edge effects) and is not a
percentage (ISO 354:2003, Clause 3.7 NOTE 2); it is therefore never clamped.

The air attenuation coefficient ``m`` is defined by ISO 354 only through its
conversion from the ISO 9613-1 attenuation coefficient ``alpha`` (in dB/m)
(ISO 354:2003, 8.1.2.1)::

    m = alpha / (10 * lg e)

ISO 354 otherwise defers the calculation of ``alpha`` entirely to ISO 9613-1.
``m`` is therefore a user-supplied per-band parameter here (default 0, i.e. no air
correction); a caller holding ISO 9613-1 ``alpha`` values can convert them with
:func:`attenuation_from_alpha`.
"""

from __future__ import annotations

import math
import warnings

import numpy as np
from numpy.typing import ArrayLike, NDArray

#: Sabine constant of ISO 354:2003, Eq. (5)/(7) (55,3 exactly as printed).
_SABINE = 55.3
#: ``10 * lg e`` (ISO 354:2003, 8.1.2.1), lg = log10; ~= 4,342944819.
_TEN_LG_E = 10.0 * math.log10(math.e)
#: Validity range of the speed-of-sound Eq. (6), in degrees Celsius.
_EQ6_TEMPERATURE_RANGE = (15.0, 30.0)
#: Minimum reverberation-room volume, ISO 354:2003 clause 6.1.1 (m3).
_MIN_ROOM_VOLUME = 150.0
#: Plane-absorber sample-area limits, ISO 354:2003 clause 6.2.1.1 (m2).
_SAMPLE_AREA_MIN = 10.0
_SAMPLE_AREA_MAX = 12.0
#: Reference volume for scaling the upper sample-area limit, clause 6.2.1.1 (m3).
_SAMPLE_AREA_REF_VOLUME = 200.0


class AbsorptionWarning(UserWarning):
    """Advisory for out-of-range or non-physical ISO 354 absorption inputs."""


def _warn_small_room(volume: float, *, stacklevel: int) -> None:
    """Advise when the room is below the ISO 354 clause 6.1.1 minimum volume.

    Clause 6.1.1 requires ``V >= 150 m3`` (new rooms are recommended to be at
    least 200 m3). Below that the modal density is too low for a reliable diffuse
    field; the result is still returned.
    """
    if volume < _MIN_ROOM_VOLUME:
        warnings.warn(
            f"Room volume {volume:g} m3 is below the {_MIN_ROOM_VOLUME:g} m3 "
            "minimum of ISO 354:2003 clause 6.1.1 (new rooms recommended "
            ">= 200 m3); the result is advisory.",
            AbsorptionWarning,
            stacklevel=stacklevel,
        )


def _warn_sample_area(sample_area: float, volume: float, *, stacklevel: int) -> None:
    """Advise when ``S`` is outside the ISO 354 clause 6.2.1.1 range.

    Clause 6.2.1.1 requires a plane-absorber area ``10 m2 <= S <= 12 m2``; for
    ``V > 200 m3`` the upper limit is multiplied by ``(V/200)^(2/3)``. The result
    is still returned.
    """
    upper = _SAMPLE_AREA_MAX
    if volume > _SAMPLE_AREA_REF_VOLUME:
        upper *= (volume / _SAMPLE_AREA_REF_VOLUME) ** (2.0 / 3.0)
    if not _SAMPLE_AREA_MIN <= sample_area <= upper:
        warnings.warn(
            f"Sample area {sample_area:g} m2 is outside the ISO 354:2003 clause "
            f"6.2.1.1 range [{_SAMPLE_AREA_MIN:g}, {upper:g}] m2; the result is "
            "advisory.",
            AbsorptionWarning,
            stacklevel=stacklevel,
        )


def _speed_of_sound(temperature: float) -> float:
    """Speed of sound from air temperature (ISO 354:2003, Eq. (6)).

    :param temperature: Air temperature, in degrees Celsius (valid 15..30).
    :return: Propagation speed of sound, in metres per second.
    """
    return 331.0 + 0.6 * temperature


def _resolve_speed(temperature: float, speed_of_sound: float | None) -> float:
    """Return ``speed_of_sound`` if given, else Eq. (6) from ``temperature``.

    Warns when the speed is derived from a temperature outside the 15..30 degC
    validity range of Eq. (6). An explicit ``speed_of_sound`` bypasses the check.
    """
    if speed_of_sound is not None:
        if speed_of_sound <= 0.0:
            raise ValueError("'speed_of_sound' must be positive.")
        return float(speed_of_sound)
    lo, hi = _EQ6_TEMPERATURE_RANGE
    if not lo <= temperature <= hi:
        warnings.warn(
            f"Temperature {temperature} degC is outside the 15..30 degC validity "
            "range of ISO 354:2003 Eq. (6); speed of sound may be inaccurate.",
            AbsorptionWarning,
            stacklevel=3,
        )
    return _speed_of_sound(temperature)


def attenuation_from_alpha(alpha: ArrayLike) -> NDArray[np.float64]:
    """Air power attenuation coefficient ``m`` from ISO 9613-1 ``alpha``.

    Applies the ISO 354:2003 (8.1.2.1) conversion ``m = alpha / (10 * lg e)``,
    where ``alpha`` is the attenuation coefficient in decibels per metre used by
    ISO 9613-1 and ``m`` is the power attenuation coefficient in reciprocal
    metres entering Eq. (5)/(7)/(8). ISO 354 itself provides no ``alpha`` table
    or formula (it defers to ISO 9613-1); this helper only performs the unit
    conversion for a caller who already holds ``alpha`` values.

    :param alpha: Attenuation coefficient, in dB/m (scalar or per band).
    :return: Power attenuation coefficient ``m``, in 1/m.
    """
    a = np.asarray(alpha, dtype=np.float64)
    if np.any(a < 0.0):
        raise ValueError("'alpha' must be non-negative.")
    return a / _TEN_LG_E


def _validate_area_inputs(
    t: NDArray[np.float64], volume: float, m: NDArray[np.float64]
) -> None:
    if volume <= 0.0:
        raise ValueError("'volume' must be positive.")
    if np.any(t <= 0.0):
        raise ValueError("Reverberation times must be positive.")
    if np.any(m < 0.0):
        raise ValueError("Air attenuation coefficient 'm' must be non-negative.")


def absorption_area(
    t60: ArrayLike,
    volume: float,
    *,
    temperature: float = 20.0,
    speed_of_sound: float | None = None,
    m: ArrayLike = 0.0,
    _advise_volume: bool = True,
) -> NDArray[np.float64]:
    """Equivalent sound absorption area of a room (ISO 354:2003, Eq. (5)/(7)).

    ``A = 55,3 * V / (c * T) - 4 * V * m``. This is Sabine's equation with the
    air-absorption term; it gives the empty-room area ``A1`` from ``T1`` or the
    with-specimen area ``A2`` from ``T2`` (both equations have identical form).

    :param t60: Reverberation time(s) ``T``, in seconds (scalar or per band).
    :param volume: Room volume ``V``, in cubic metres.
    :param temperature: Air temperature, in degrees Celsius, used to compute the
        speed of sound via Eq. (6) when ``speed_of_sound`` is not given
        (default 20 degC, i.e. c = 343 m/s). A temperature outside 15..30 degC
        raises an :class:`AbsorptionWarning`. A room volume below the 150 m3
        minimum of clause 6.1.1 likewise raises an advisory :class:`AbsorptionWarning`.
    :param speed_of_sound: Explicit speed of sound ``c``, in m/s; overrides
        ``temperature`` and Eq. (6) when supplied.
    :param m: Power attenuation coefficient of air ``m``, in 1/m (scalar or per
        band; default 0, i.e. no air correction). Obtain it from an ISO 9613-1
        attenuation coefficient with :func:`attenuation_from_alpha`.
    :return: Equivalent sound absorption area ``A``, in square metres, with the
        shape of ``t60``.
    """
    t = np.asarray(t60, dtype=np.float64)
    m_arr = np.asarray(m, dtype=np.float64)
    _validate_area_inputs(t, volume, m_arr)
    if _advise_volume:
        _warn_small_room(volume, stacklevel=3)
    c = _resolve_speed(temperature, speed_of_sound)
    return _SABINE * volume / (c * t) - 4.0 * volume * m_arr


def absorption_coefficient(
    t1: ArrayLike,
    t2: ArrayLike,
    volume: float,
    sample_area: float,
    *,
    temperature1: float = 20.0,
    temperature2: float | None = None,
    speed_of_sound1: float | None = None,
    speed_of_sound2: float | None = None,
    m1: ArrayLike = 0.0,
    m2: ArrayLike = 0.0,
) -> NDArray[np.float64]:
    """Sound absorption coefficient of a plane absorber (ISO 354:2003, Eq. (9)).

    Builds the equivalent sound absorption area of the specimen from Eq. (8),
    ``AT = A2 - A1 = 55,3*V*(1/(c2*T2) - 1/(c1*T1)) - 4*V*(m2 - m1)``, using the
    empty-room reverberation time ``T1`` and the with-specimen time ``T2``, then
    returns ``alpha_s = AT / S`` (Eq. (9)).

    The two measurements may be at different temperatures; ``c1`` and ``c2`` are
    resolved independently. ``alpha_s`` is returned unclamped and may exceed 1,0
    (Clause 3.7 NOTE 2). Because adding an absorber must reduce the reverberation
    time, ``T2 >= T1`` (``alpha_s <= 0``) is non-physical and raises an
    :class:`AbsorptionWarning`. A room volume below the 150 m3 minimum of
    clause 6.1.1, or a sample area outside the clause 6.2.1.1 range
    (``10 m2 <= S <= 12 m2``, upper limit scaled by ``(V/200)^(2/3)`` when
    ``V > 200 m3``), each raise an advisory :class:`AbsorptionWarning`.

    :param t1: Empty-room reverberation time(s) ``T1``, in seconds.
    :param t2: With-specimen reverberation time(s) ``T2``, in seconds.
    :param volume: Room volume ``V``, in cubic metres.
    :param sample_area: Area ``S`` covered by the test specimen, in square metres
        (for both-sides-exposed absorbers, the area of the two sides;
        Clause 3.7 NOTE 1).
    :param temperature1: Empty-room air temperature, in degrees Celsius
        (default 20). Used for ``c1`` via Eq. (6) unless ``speed_of_sound1`` is
        given.
    :param temperature2: With-specimen air temperature, in degrees Celsius;
        defaults to ``temperature1``. Used for ``c2`` unless ``speed_of_sound2``
        is given.
    :param speed_of_sound1: Explicit ``c1`` in m/s; overrides ``temperature1``.
    :param speed_of_sound2: Explicit ``c2`` in m/s; overrides ``temperature2``.
    :param m1: Empty-room air attenuation coefficient ``m1``, in 1/m (default 0).
    :param m2: With-specimen air attenuation coefficient ``m2``, in 1/m
        (default 0).
    :return: Sound absorption coefficient ``alpha_s`` with the broadcast shape of
        ``t1`` and ``t2``.
    """
    if sample_area <= 0.0:
        raise ValueError("'sample_area' must be positive.")
    if volume <= 0.0:
        raise ValueError("'volume' must be positive.")
    if temperature2 is None:
        temperature2 = temperature1
    # Advisory setup checks (result still returned). Volume is advised here once
    # and suppressed in the internal absorption_area calls to avoid duplicates.
    _warn_small_room(volume, stacklevel=2)
    _warn_sample_area(sample_area, volume, stacklevel=2)
    a1 = absorption_area(
        t1, volume, temperature=temperature1, speed_of_sound=speed_of_sound1,
        m=m1, _advise_volume=False,
    )
    a2 = absorption_area(
        t2, volume, temperature=temperature2, speed_of_sound=speed_of_sound2,
        m=m2, _advise_volume=False,
    )
    area_specimen = a2 - a1
    alpha_s = area_specimen / sample_area
    if np.any(alpha_s <= 0.0):
        warnings.warn(
            "alpha_s <= 0 (T2 >= T1): adding the specimen did not reduce the "
            "reverberation time; check the measurement (ISO 354:2003, 8.1.2/8.1.3).",
            AbsorptionWarning,
            stacklevel=2,
        )
    return alpha_s
