#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Atmospheric absorption of sound: ISO 9613-1:1993.

The attenuation of a pure tone propagating through the atmosphere is governed by
a pure-tone attenuation coefficient ``alpha`` (in dB/m) that depends on frequency,
temperature, humidity and pressure through the vibrational relaxation of the
oxygen and nitrogen molecules plus classical and rotational losses
(ISO 9613-1:1993, clause 6).

The attenuation coefficient (ISO 9613-1:1993, Eq. (5))::

    alpha = 8,686 * f^2 * {
              1,84e-11 * (pa/pr)^-1 * (T/T0)^(1/2)
            + (T/T0)^(-5/2) * [
                  0,012 75 * exp(-2239,1/T) * (frO + f^2/frO)^-1
                + 0,106 8  * exp(-3352,0/T) * (frN + f^2/frN)^-1
              ]
          }

in decibels per metre, with the oxygen and nitrogen relaxation frequencies
(ISO 9613-1:1993, Eq. (3) and Eq. (4))::

    frO = (pa/pr) * [24 + 4,04e4 * h * (0,02 + h)/(0,391 + h)]
    frN = (pa/pr) * (T/T0)^(-1/2)
          * [9 + 280 * h * exp{-4,170 * [(T/T0)^(-1/3) - 1]}]

Here ``T`` is the ambient temperature (K), ``T0 = 293,15 K`` and
``pr = 101,325 kPa`` are the reference conditions (ISO 9613-1:1993, clause 4.2),
``pa`` is the ambient pressure (kPa) and ``h`` is the molar concentration of
water vapour as a percentage, obtained from the relative humidity by the
psychrometric conversion (ISO 9613-1:1993, clause 6.4 / Annex B)::

    h = hr * (psat/pr) / (pa/pr)
    psat/pr = 10 ^ (-6,8346 * (T01/T)^1,261 + 4,6151),  T01 = 273,16 K

with ``hr`` the relative humidity (%) and ``T01`` the triple-point temperature of
water.

Table 1 of ISO 9613-1:1993 tabulates ``alpha`` (in dB/km) at the reference
pressure for a grid of temperature, relative humidity and one-third-octave
frequency; its rows are labelled with the ISO 266 preferred frequencies but the
coefficients are computed at the exact midband frequencies (Note 5)
``fm = 1000 * 10^(k/10)``, ``k`` integer. Pass ``exact_midband=True`` to snap the
requested frequencies onto that grid and reproduce Table 1 exactly.

This module closes the loop with :mod:`phonometry.sound_absorption` (ISO 354),
whose air power-attenuation coefficient ``m`` (1/m) is defined only through the
ISO 9613-1 ``alpha`` via ``m = alpha / (10 * lg e)``. :func:`air_attenuation_m`
returns that ``m`` directly.
"""

from __future__ import annotations

import warnings

import numpy as np
from numpy.typing import ArrayLike, NDArray

from .sound_absorption import attenuation_from_alpha

#: Reference air temperature ``T0`` (ISO 9613-1:1993, clause 4.2), in kelvins.
_T0 = 293.15
#: Reference ambient pressure ``pr`` (ISO 9613-1:1993, clause 4.2), in kPa.
_PR = 101.325
#: Triple-point temperature of water ``T01`` (Annex B), in kelvins.
_T01 = 273.16
#: 0 degC in kelvins, for the Celsius -> kelvin conversion.
_KELVIN = 273.15
#: dB/m -> Np/m factor ``20 lg e`` printed as 8,686 in Eq. (5).
_EIGHT_686 = 8.686

#: Tabulated ranges of ISO 9613-1:1993 (Scope / clause 1), used for advisories.
_FREQ_RANGE = (50.0, 10_000.0)
_TEMPERATURE_RANGE = (-20.0, 50.0)
_HUMIDITY_RANGE = (10.0, 100.0)
#: Pressure envelope of the accuracy clauses 7.1-7.3 (< 200 kPa), in kPa.
_PRESSURE_MAX = 200.0


class AtmosphericAbsorptionWarning(UserWarning):
    """Advisory for ISO 9613-1 inputs outside the tabulated/validity ranges."""


def _exact_midband(frequencies: NDArray[np.float64]) -> NDArray[np.float64]:
    """Snap frequencies to the exact one-third-octave midbands, Eq. (6).

    ``fm = 1000 * 10^(k/10)`` with ``k = round(10 * lg(f/1000))`` the nearest
    integer band index. Reproduces the frequencies used to compute Table 1
    (ISO 9613-1:1993, clause 6.4, Note 5).
    """
    k = np.round(10.0 * np.log10(frequencies / 1000.0))
    return 1000.0 * 10.0 ** (k / 10.0)


def _molar_water_vapour(
    temperature_k: float, relative_humidity: float, pressure: float
) -> float:
    """Molar concentration of water vapour ``h`` (%), ISO 9613-1 clause 6.4.

    ``psat/pr = 10^(-6,8346 (T01/T)^1,261 + 4,6151)`` and
    ``h = hr (psat/pr)/(pa/pr)`` (Annex B psychrometric conversion).
    """
    psat_over_pr = 10.0 ** (
        -6.8346 * (_T01 / temperature_k) ** 1.261 + 4.6151
    )
    return float(relative_humidity * psat_over_pr / (pressure / _PR))


def _validate(
    freqs: NDArray[np.float64],
    temperature: float,
    relative_humidity: float,
    pressure: float,
) -> None:
    """Raise on non-physical inputs; warn on out-of-tabulated-range inputs."""
    if np.any(freqs <= 0.0):
        raise ValueError("'frequencies' must be positive.")
    if temperature <= -_KELVIN:
        raise ValueError("'temperature' must be above absolute zero (-273,15 degC).")
    if not 0.0 <= relative_humidity <= 100.0:
        raise ValueError("'relative_humidity' must be within [0, 100] %.")
    if pressure <= 0.0:
        raise ValueError("'pressure' must be positive.")

    lo_t, hi_t = _TEMPERATURE_RANGE
    if not lo_t <= temperature <= hi_t:
        warnings.warn(
            f"Temperature {temperature:g} degC is outside the {lo_t:g}..{hi_t:g} "
            "degC tabulated range of ISO 9613-1:1993; the result is advisory.",
            AtmosphericAbsorptionWarning,
            stacklevel=3,
        )
    lo_h, hi_h = _HUMIDITY_RANGE
    if not lo_h <= relative_humidity <= hi_h:
        warnings.warn(
            f"Relative humidity {relative_humidity:g} % is outside the "
            f"{lo_h:g}..{hi_h:g} % tabulated range of ISO 9613-1:1993; the "
            "result is advisory.",
            AtmosphericAbsorptionWarning,
            stacklevel=3,
        )
    lo_f, hi_f = _FREQ_RANGE
    if np.any(freqs < lo_f) or np.any(freqs > hi_f):
        warnings.warn(
            f"One or more frequencies are outside the {lo_f:g}..{hi_f:g} Hz "
            "tabulated range of ISO 9613-1:1993; the result is advisory.",
            AtmosphericAbsorptionWarning,
            stacklevel=3,
        )
    if pressure > _PRESSURE_MAX:
        warnings.warn(
            f"Pressure {pressure:g} kPa exceeds the {_PRESSURE_MAX:g} kPa "
            "validity envelope of ISO 9613-1:1993 (clause 7); the result is "
            "advisory.",
            AtmosphericAbsorptionWarning,
            stacklevel=3,
        )


def air_attenuation(
    frequencies: ArrayLike,
    temperature: float = 20.0,
    relative_humidity: float = 50.0,
    pressure: float = 101.325,
    *,
    exact_midband: bool = False,
) -> NDArray[np.float64]:
    """Pure-tone atmospheric attenuation coefficient (ISO 9613-1:1993, Eq. (5)).

    Evaluates ``alpha`` in decibels per metre from the oxygen and nitrogen
    relaxation frequencies (Eq. (3)/(4)) and the classical, rotational and
    vibrational absorption terms (Eq. (5)). Fully vectorized over
    ``frequencies``; ``temperature``, ``relative_humidity`` and ``pressure`` are
    scalars.

    :param frequencies: Frequency or frequencies ``f``, in hertz (array-like).
    :param temperature: Ambient air temperature, in degrees Celsius
        (default 20 degC, i.e. the reference ``T0``). A value outside the
        -20..+50 degC tabulated range emits an
        :class:`AtmosphericAbsorptionWarning`; a value at or below absolute zero
        raises ``ValueError``.
    :param relative_humidity: Relative humidity, in percent, with respect to
        saturation over liquid water (default 50 %). Outside 10..100 % emits an
        :class:`AtmosphericAbsorptionWarning`; outside [0, 100] % raises
        ``ValueError``.
    :param pressure: Ambient atmospheric pressure ``pa``, in kilopascals
        (default 101,325 kPa = one standard atmosphere = ``pr``). Above 200 kPa
        emits an :class:`AtmosphericAbsorptionWarning`; non-positive raises
        ``ValueError``.
    :param exact_midband: When ``True``, each requested frequency is snapped to
        the nearest exact one-third-octave midband ``fm = 1000*10^(k/10)``
        (Eq. (6)) before evaluation, reproducing the frequencies used for
        Table 1 (Note 5). Default ``False`` (use ``frequencies`` verbatim).
    :return: Attenuation coefficient ``alpha``, in dB/m, with the shape of
        ``frequencies``.

    .. note::
        ISO 354:2003 defers its air power-attenuation coefficient ``m`` (1/m)
        entirely to this ``alpha`` via ``m = alpha / (10 * lg e)``. Use
        :func:`air_attenuation_m` to obtain that ``m`` for
        :func:`phonometry.sound_absorption.absorption_area` /
        :func:`~phonometry.sound_absorption.absorption_coefficient`.
    """
    freqs = np.asarray(frequencies, dtype=np.float64)
    _validate(freqs, temperature, relative_humidity, pressure)
    if exact_midband:
        freqs = _exact_midband(freqs)

    temperature_k = temperature + _KELVIN
    pa_over_pr = pressure / _PR
    t_ratio = temperature_k / _T0

    h = _molar_water_vapour(temperature_k, relative_humidity, pressure)
    fro = pa_over_pr * (24.0 + 4.04e4 * h * (0.02 + h) / (0.391 + h))
    frn = (
        pa_over_pr
        * t_ratio ** (-0.5)
        * (9.0 + 280.0 * h * np.exp(-4.170 * (t_ratio ** (-1.0 / 3.0) - 1.0)))
    )

    f2 = freqs**2
    classical = 1.84e-11 * (1.0 / pa_over_pr) * t_ratio**0.5
    vibrational = t_ratio ** (-2.5) * (
        0.01275 * np.exp(-2239.1 / temperature_k) / (fro + f2 / fro)
        + 0.1068 * np.exp(-3352.0 / temperature_k) / (frn + f2 / frn)
    )
    alpha = _EIGHT_686 * f2 * (classical + vibrational)
    return np.asarray(alpha, dtype=np.float64)


def air_attenuation_m(
    frequencies: ArrayLike,
    temperature: float = 20.0,
    relative_humidity: float = 50.0,
    pressure: float = 101.325,
    *,
    exact_midband: bool = False,
) -> NDArray[np.float64]:
    """ISO 354 air power-attenuation coefficient ``m`` (1/m) from conditions.

    Convenience composition of :func:`air_attenuation` (ISO 9613-1 ``alpha`` in
    dB/m) with the ISO 354:2003 (8.1.2.1) conversion ``m = alpha / (10 * lg e)``
    (via :func:`phonometry.sound_absorption.attenuation_from_alpha`). It lets an
    ISO 354 caller feed real atmospheric conditions into
    :func:`~phonometry.sound_absorption.absorption_area` /
    :func:`~phonometry.sound_absorption.absorption_coefficient` instead of
    hand-entering ``m``.

    :param frequencies: Frequency or frequencies ``f``, in hertz (array-like).
    :param temperature: Ambient air temperature, in degrees Celsius (default 20).
    :param relative_humidity: Relative humidity, in percent (default 50).
    :param pressure: Ambient atmospheric pressure, in kilopascals
        (default 101,325).
    :param exact_midband: Snap frequencies to exact midbands; see
        :func:`air_attenuation`.
    :return: Power attenuation coefficient ``m``, in 1/m, with the shape of
        ``frequencies``.
    """
    alpha = air_attenuation(
        frequencies,
        temperature,
        relative_humidity,
        pressure,
        exact_midband=exact_midband,
    )
    return attenuation_from_alpha(alpha)
