#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""The terms of ISO 9613-1:1993, the attenuation of sound by the atmosphere.

The pure-tone coefficient of Eq. (5), with the molar concentration of water
vapour of clause 6.4 and Annex B and the checks of its inputs, written once.
:func:`phonometry.environment.air_attenuation` is built on it, and the
aircraft noise of SAE ARP 866A and ARP 5534 and the sound power at high
frequencies of ISO 9295 read the same terms, without importing another
domain. The warning these checks give, :class:`AtmosphericAbsorptionWarning`,
is published by :mod:`phonometry.environment`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from .validation import require_above_absolute_zero, require_scalar
from .warnings import PhonometryWarning, published_by, warn_caller

if TYPE_CHECKING:
    from numpy.typing import NDArray

__all__ = ["AtmosphericAbsorptionWarning"]

#: Reference air temperature ``T0`` (ISO 9613-1:1993, clause 4.2), in kelvins.
_T0 = 293.15
#: Reference ambient pressure ``pr`` (ISO 9613-1:1993, clause 4.2), in kPa.
_PR = 101.325
#: Triple-point temperature of water ``T01`` (Annex B), in kelvins.
_T01 = 273.16
#: 0 degC in kelvins, for the Celsius -> kelvin conversion.
_KELVIN = 273.15
#: Np -> dB factor (20*lg e) ``20 lg e`` printed as 8,686 in Eq. (5).
_EIGHT_686 = 8.686
#: Full-scale relative humidity (saturation), in percent: hard upper validity
#: bound of the input (raises on violation), unlike the advisory tabulated
#: ``_HUMIDITY_RANGE`` checked alongside it.
_MAX_RELATIVE_HUMIDITY_PERCENT = 100.0

#: Tabulated ranges of ISO 9613-1:1993 (Scope / clause 1), used for advisories.
_FREQ_RANGE = (50.0, 10_000.0)
_TEMPERATURE_RANGE = (-20.0, 50.0)
_HUMIDITY_RANGE = (10.0, 100.0)
#: Pressure envelope of the accuracy clauses 7.1-7.3 (< 200 kPa), in kPa.
_PRESSURE_MAX = 200.0


@published_by("phonometry.environment")
class AtmosphericAbsorptionWarning(PhonometryWarning):
    """Advisory for ISO 9613-1 inputs outside the tabulated/validity ranges."""


def _exact_midband(frequencies: NDArray[np.float64]) -> NDArray[np.float64]:
    r"""Snap frequencies to the exact one-third-octave midbands, Eq. (6).

    :math:`f_\mathrm{m} = 1000 \cdot 10^{k/10}` with
    :math:`k = \operatorname{round}(10 \log_{10}(f/1000))` the nearest integer band
    index. Reproduces the frequencies used to compute Table 1
    (ISO 9613-1:1993, clause 6.4, Note 5).
    """
    k = np.round(10.0 * np.log10(frequencies / 1000.0))
    return 1000.0 * 10.0 ** (k / 10.0)


def _molar_water_vapour(
    temperature_k: float,
    relative_humidity_percent: float,
    static_pressure_kpa: float,
    saturation_ratio: float | None = None,
) -> float:
    r"""Molar concentration of water vapour ``h`` (%), ISO 9613-1 clause 6.4.

    :math:`p_\mathrm{sat}/p_\mathrm{r} = 10^{-6.8346 \, (T_{01}/T)^{1.261} + 4.6151}` and
    :math:`h = h_\mathrm{r} \, (p_\mathrm{sat}/p_\mathrm{r})/(p_\mathrm{a}/p_\mathrm{r})` (Annex B psychrometric
    conversion).

    :param saturation_ratio: :math:`p_\mathrm{sat}/p_\mathrm{r}` from another
        formula, for a document that keeps ISO 9613-1's Eq. (3)-(5) but writes
        its own saturation vapour pressure (SAE ARP 5534 Eq. 5-6 prints the
        longer form of ANSI S1.26). ``None`` takes the Annex B formula above.
    """
    psat_over_pr = (
        10.0 ** (-6.8346 * (_T01 / temperature_k) ** 1.261 + 4.6151)
        if saturation_ratio is None
        else saturation_ratio
    )
    return float(relative_humidity_percent * psat_over_pr / (static_pressure_kpa / _PR))


def _validate(
    freqs: NDArray[np.float64],
    temperature_c: float,
    relative_humidity_percent: float,
    static_pressure_kpa: float,
    *,
    frequency_scope: tuple[float, float, str] | None = None,
) -> None:
    """Raise on non-physical inputs; warn on out-of-tabulated-range inputs.

    ``frequency_scope`` is ``(low, high, description)`` of the frequency range
    the caller answers for, when it is wider than the ISO 9613-1 table: ISO
    9295:2015 Annex A evaluates the same Eq. (5) up to 22,4 kHz, the top of the
    16 kHz octave band, so its caller passes that range and its own name.
    """
    if np.any(freqs <= 0.0):
        msg = "'frequencies' must be positive."
        raise ValueError(msg)
    require_above_absolute_zero(temperature_c, "temperature_c")
    # The comparisons below would let a one-element array through, and the
    # psychrometric conversion would then read it as its element on numpy 2.0
    # to 2.3 and refuse it anonymously from 2.4 on.
    require_scalar(relative_humidity_percent, "relative_humidity_percent")
    require_scalar(static_pressure_kpa, "static_pressure_kpa")
    if not 0.0 <= relative_humidity_percent <= _MAX_RELATIVE_HUMIDITY_PERCENT:
        msg = "'relative_humidity_percent' must be within [0, 100] %."
        raise ValueError(msg)
    if static_pressure_kpa <= 0.0:
        msg = "'static_pressure_kpa' must be positive."
        raise ValueError(msg)

    lo_t, hi_t = _TEMPERATURE_RANGE
    if not lo_t <= temperature_c <= hi_t:
        warn_caller(
            f"Temperature {temperature_c:g} degC is outside the {lo_t:g}..{hi_t:g} "
            "degC tabulated range of ISO 9613-1:1993; the result is advisory.",
            AtmosphericAbsorptionWarning,
        )
    lo_h, hi_h = _HUMIDITY_RANGE
    if not lo_h <= relative_humidity_percent <= hi_h:
        warn_caller(
            f"Relative humidity {relative_humidity_percent:g} % is outside the "
            f"{lo_h:g}..{hi_h:g} % tabulated range of ISO 9613-1:1993; the "
            "result is advisory.",
            AtmosphericAbsorptionWarning,
        )
    lo_f, hi_f, scope = (
        (*_FREQ_RANGE, "tabulated range of ISO 9613-1:1993")
        if frequency_scope is None
        else frequency_scope
    )
    if np.any(freqs < lo_f) or np.any(freqs > hi_f):
        warn_caller(
            f"One or more frequencies are outside the {lo_f:g}..{hi_f:g} Hz "
            f"{scope}; the result is advisory.",
            AtmosphericAbsorptionWarning,
        )
    if static_pressure_kpa > _PRESSURE_MAX:
        warn_caller(
            f"Pressure {static_pressure_kpa:g} kPa exceeds the {_PRESSURE_MAX:g} kPa "
            "validity envelope of ISO 9613-1:1993 (clause 7); the result is "
            "advisory.",
            AtmosphericAbsorptionWarning,
        )


def _pure_tone_terms(
    freqs: NDArray[np.float64],
    temperature_k: float,
    relative_humidity_percent: float,
    static_pressure_kpa: float,
    *,
    saturation_ratio: float | None = None,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    r"""The two factors of Eq. (5) that do not carry the decibel.

    Returns :math:`f^2` and the braced sum of the classical, rotational and
    vibrational terms, so that :math:`\alpha = 8{,}686\, f^2\, \{\ldots\}` in
    decibels per metre (ISO 9613-1:1993, Eq. (5)) and :math:`f^2\, \{\ldots\}`
    is the same coefficient in nepers per metre, which is how ISO 9295:2015
    Annex A prints it (Formula (A.5)). The temperature is taken in kelvins,
    already converted, so the conversion from Celsius is written once, by the
    caller that owns it. Nothing is validated here. ``saturation_ratio`` is
    passed on to :func:`_molar_water_vapour`.
    """
    pa_over_pr = static_pressure_kpa / _PR
    t_ratio = temperature_k / _T0

    h = _molar_water_vapour(
        temperature_k,
        relative_humidity_percent,
        static_pressure_kpa,
        saturation_ratio,
    )
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
    return f2, np.asarray(classical + vibrational, dtype=np.float64)
