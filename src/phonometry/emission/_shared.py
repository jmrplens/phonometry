#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""What every sound-power method has in common: the A-weighting band corrections
of ISO 3744:2010 Annex E, the reference area, the accuracy-grade vocabulary
and the qualification warning.

Each determination method carries its own standard and its own module (the
enveloping surface of ISO 3744/3746, the anechoic room of ISO 3745, the
reverberation room of ISO 3741, the intensity scanning of ISO 9614-2/-3), yet
they meet in the last step: the band sound power levels are combined into an
A-weighted total with the band corrections :math:`C_k` tabulated in ISO
3744:2010 Annex E (Tables E.1/E.2),

.. math::

   L_{W\mathrm{A}} = 10 \log_{10}\!\left[ \sum_k 10^{0.1 (L_{Wk} + C_k)} \right]
   \tag{Eq. E.1}

and the other standards adopt that same table by reference for their own
A-weighted totals (ISO 3741:2010 Annex F Eq. F.2, ISO 3745:2012 Annex C
Eq. C.1, ISO 9614-2:1996 clause 10.6 b). One table, transcribed once.

The radiation-impedance correction :math:`C_2` that carries a band level to
the reference meteorological conditions is shared the same way. ISO 3741:2010
clause 9.1.4 and ISO 3747:2010 Annex C print the same expression,

.. math::

   C_2 = -10 \log_{10}\frac{p_\mathrm{s}}{p_{\mathrm{s},0}}
   + 15 \log_{10}\frac{273{,}15 + \theta}{\theta_1},
   \qquad p_{\mathrm{s},0} = 101{,}325\ \mathrm{kPa},
   \quad \theta_1 = 296\ \mathrm{K}

digit for digit, so the guard on the two meteorological inputs and the
correction itself live here once. The reference-quantity correction
:math:`C_1` of ISO 3741:2010 clause 9.1.4 sits beside it for the same reason:
the ISO 3741 direct method and the two ISO 9295:2015 direct methods, whose
clause 10.1 refers to ISO 3741 for the reference conditions, both apply it.

The single event time-integrated levels of the sound energy determinations
meet here too: ISO 3744:2010 Eq. (19)/(20), ISO 3746:2010 Eq. (16)/(17) and
ISO 3741:2010 Eq. (22)/(23) are one pair of equations printed three times,
the energy mean of :math:`N_\mathrm{e}` events measured one at a time and
the :math:`-10 \log_{10} N_\mathrm{e}` of one measurement that encompasses
them all, so :func:`_single_event_mean` is transcribed once and the method
modules call it.

The reference area :math:`S_0 = 1` m^2 of the :math:`10 \log_{10}(S/S_0)`
surface term, the two accuracy grades the methods share (``'engineering'``,
grade 2 of ISO 3744 and ISO 9614-2, and ``'survey'``, grade 3 of ISO 3746 and
ISO 9614-2) and the warning class that every method raises when a
qualification limit is only just met are here for the same reason: the method
modules import them downward from a single definition, and none of them has to
import another method to get them.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, cast

import numpy as np

from .._internal.levels_math import energy_mean
from .._internal.validation import (
    real_array,
    require_choice,
    require_count,
    require_positive,
    require_scalar,
)
from .._internal.warnings import PhonometryWarning, published_by, warn_caller

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from .._internal.types import BandFraction, NumericArrayLike

_S0 = 1.0  #: Reference area, in square metres (ISO 3744, 8.2.5).
#: Reference static pressure of the ISO 3740 family, in kilopascals
#: (ISO 3741:2010 clause 4; ISO 3747:2010 Annex C prints 1,013 25 x 10^5 Pa).
_PS0 = 101.325
#: Reference temperature of the C1 reference-quantity correction, in kelvin
#: (ISO 3741:2010 clause 9.1.4).
_THETA0 = 314.0
#: Reference temperature of the C2 radiation-impedance correction, in kelvin
#: (ISO 3741:2010 clause 9.1.4, ISO 3747:2010 Annex C).
_THETA1 = 296.0
#: Temperature floor in degC: sqrt(273 + theta) of the speed-of-sound formula
#: c = 20.05*sqrt(273 + theta) is zero or complex at or below it (ISO 3741, 9.1.4).
_ROUNDED_ABS_ZERO_C = -273.0

#: Reference duration, in seconds, of the single event time-integrated sound
#: pressure level: L_E = L_p,T + 10 lg(T/T0) (ISO 3744:2010, 3.4 NOTE 1).
_T0 = 1.0
#: Fewest single sound emission events a sound energy determination rests
#: on, whether measured one at a time or in one measurement encompassing
#: them all (ISO 3744:2010 8.3.1, ISO 3746:2010 8.4.1, ISO 3741:2010 8.5.1).
_MIN_EVENTS = 5


def _validate_event_count(n_events: object, owner: str) -> int | None:
    """A count of events as an ``int``, or ``None``, refused when it is not one.

    The entry points already refuse it, but a result can also be built
    directly or rebuilt with :func:`dataclasses.replace`, and a count of 2,5
    events describes no measurement the standard defines. The count goes
    through :func:`~phonometry._internal.validation.require_count`, so a bool,
    a text or an array is a :class:`TypeError` and a number that is not a
    whole one, or is below one, a :class:`ValueError`, both naming the owner.

    :return: The count as an ``int``, or ``None`` when none was given.
    """
    if n_events is None:
        return None
    try:
        return require_count(n_events, "n_events")
    except (TypeError, ValueError) as error:
        msg = f"{owner}: {error}"
        raise type(error)(msg) from None


Grade = Literal["engineering", "survey"]


@published_by("phonometry.emission")
class SoundPowerWarning(PhonometryWarning):
    """Non-fatal qualification issue in any of the sound-power methods.

    Emitted for ISO 3744/3746 background margin below the criterion and for
    ``K2`` beyond the method's validity limit (8.2.3, 4.3.2); for ISO 3741
    reverberation-room qualification (room volume vs Table 1, mean absorption)
    and microphone/source-position sampling; and for ISO 9614-2 negative total
    partial power and unmet field-indicator criteria. Where a lower criterion
    is only just met the returned levels represent upper bounds and must be
    reported as such.
    """


def _validate_meteorology(temperature_c: float, static_pressure_kpa: float) -> None:
    r"""Guard the meteorological inputs before the log10/sqrt of C1/C2 and c.

    A non-finite or :math:`\le -273` degC temperature makes
    :math:`\sqrt{273 + \theta}` complex/zero, and a non-finite or non-positive
    static pressure makes :math:`\log_{10}(p_\mathrm{s}/p_{\mathrm{s}0})` undefined; both are rejected
    with a clean ``ValueError``.
    """
    require_scalar(static_pressure_kpa, "static_pressure_kpa")
    require_scalar(temperature_c, "temperature_c")
    if not np.isfinite(temperature_c) or temperature_c <= _ROUNDED_ABS_ZERO_C:
        msg = "'temperature_c' must be finite and greater than -273 degC."
        raise ValueError(msg)
    if not np.isfinite(static_pressure_kpa) or static_pressure_kpa <= 0.0:
        msg = "'static_pressure_kpa' must be finite and positive."
        raise ValueError(msg)


def _c1_correction(temperature_c: float, static_pressure_kpa: float) -> float:
    """Reference-quantity correction ``C1`` (ISO 3741:2010 clause 9.1.4).

    Read by the ISO 3741 direct method and by the two ISO 9295:2015 direct
    methods, whose clause 10.1 carries their result to the reference
    meteorological conditions "de acuerdo con la Norma ISO 3741".
    """
    return float(
        -10.0 * np.log10(static_pressure_kpa / _PS0)
        + 5.0 * np.log10((273.15 + temperature_c) / _THETA0)
    )


def _c2_correction(temperature_c: float, static_pressure_kpa: float) -> float:
    """Radiation-impedance correction ``C2`` (ISO 3741:2010 clause 9.1.4,
    ISO 3747:2010 Annex C, Eq. C.1/C.3).
    """
    return float(
        -10.0 * np.log10(static_pressure_kpa / _PS0)
        + 15.0 * np.log10((273.15 + temperature_c) / _THETA1)
    )


def _check_grade(grade: object) -> Grade:
    require_choice(grade, "grade", ("engineering", "survey"))
    return cast("Grade", grade)


def _single_event_mean(
    levels: NumericArrayLike,
    n_events: int | np.integer[Any] | None,
    *,
    name: str,
    clause: str = "ISO 3744:2010 8.3.1, ISO 3741:2010 8.5.1",
) -> NDArray[np.float64]:
    r"""Mean single event time-integrated level of one event, per position.

    ISO 3744:2010 Eq. (19)/(20), printed again as ISO 3746:2010 Eq. (16)/(17)
    and ISO 3741:2010 Eq. (22)/(23). With ``n_events`` ``None`` the first axis
    of ``levels`` holds the :math:`N_\mathrm{e}` events measured one at a
    time and the mean is the energy average over that axis:

    .. math::

       L'_{Ei(\mathrm{ST})} = 10 \log_{10}\!\left[ \frac{1}{N_\mathrm{e}}
       \sum_{q=1}^{N_\mathrm{e}} 10^{0.1 L'_{Ei,q(\mathrm{ST})}} \right]
       \tag{Eq. 19}

    With ``n_events`` :math:`= N_\mathrm{e}` the whole of ``levels`` is one
    measurement that encompasses :math:`N_\mathrm{e}` successive events, and
    the level of one event is that measurement less :math:`10 \log_{10}
    N_\mathrm{e}`:

    .. math::

       L'_{Ei(\mathrm{ST})} = L'_{Ei,N_\mathrm{e}(\mathrm{ST})}
       - 10 \log_{10} N_\mathrm{e} \tag{Eq. 20}

    Both standards ask for at least five events in either mode; fewer is
    accepted with a :class:`SoundPowerWarning`, the determination then being
    below the count the method is written for.

    :param levels: Per-event levels with the events on the first axis
        (``n_events`` ``None``), or the one measurement of ``n_events`` events.
    :param n_events: ``None`` for one event per entry of the first axis, else
        the number of events one measurement encompasses.
    :param name: The caller's parameter name, for the error messages.
    :param clause: The clauses the warning cites for the five-event minimum,
        which each caller names for its own standard (ISO 3743-1:2010 prints
        it in 7.6).
    :return: The mean level of one event, one axis fewer than ``levels`` when
        ``n_events`` is ``None``, the same shape otherwise.
    :raises ValueError: for non-finite levels, an empty event axis or a
        non-positive ``n_events``.
    """
    arr = real_array(levels, name)
    if not np.all(np.isfinite(arr)):
        msg = f"'{name}' must contain only finite values."
        raise ValueError(msg)
    if n_events is None:
        if arr.ndim == 0 or arr.shape[0] == 0:
            msg = f"'{name}' must carry one entry per single event on its first axis."
            raise ValueError(msg)
        count = int(arr.shape[0])
        mean = energy_mean(arr, axis=0)
    else:
        count = require_count(n_events, "n_events")
        mean = arr - 10.0 * np.log10(count)
    if count < _MIN_EVENTS:
        warn_caller(
            f"Only {count} single event(s); the sound energy determination "
            f"requires at least {_MIN_EVENTS} ({clause}).",
            SoundPowerWarning,
        )
    return np.asarray(mean, dtype=np.float64)


def _background_exposure(
    background_levels: NumericArrayLike, integration_time: float | None
) -> NDArray[np.float64]:
    r"""The background's single event time-integrated level over ``T``.

    The correction Eq. (21) subtracts one energy from another, and the two
    must be referred to the same quantity: the event level is
    :math:`\int p^2\,\mathrm{d}t` re :math:`E_0 = p_0^2 \cdot 1` s, so the
    time-averaged background level the standard has measured over the same
    interval :math:`T` enters as its own exposure over :math:`T`,
    :math:`L_{p(\mathrm{B})} + 10 \log_{10}(T/T_0)` (clause 3.4 NOTE 1).

    :param background_levels: Time-averaged background levels, in decibels.
    :param integration_time: The interval ``T`` of the single event levels,
        in seconds; required.
    :return: The background exposure levels over ``T``, in decibels.
    :raises ValueError: if ``integration_time`` is missing or not positive.
    """
    if integration_time is None:
        msg = (
            "'integration_time' (the interval T of the single event levels, in "
            "seconds) is required with 'background_levels': the background is "
            "compared as its exposure over the same T (ISO 3744:2010 8.3.4, ISO 3741:2010 9.2.2)."
        )
        raise ValueError(msg)
    t = require_positive(integration_time, "integration_time")
    bg = real_array(background_levels, "background_levels")
    if not np.all(np.isfinite(bg)):
        msg = "'background_levels' must contain only finite values."
        raise ValueError(msg)
    return np.asarray(bg + 10.0 * np.log10(t / _T0), dtype=np.float64)


def _reference_power_levels(
    reference_sound_power_levels: object,
    frequencies: object,
    *,
    fraction: BandFraction,
    name: str = "reference_sound_power_levels",
    temperature_c: float | None = None,
    static_pressure_kpa: float | None = None,
) -> NDArray[np.float64]:
    r"""The calibrated sound power of a reference sound source, per band.

    A comparison method takes :math:`L_{W(\mathrm{RSS})}` either as the levels
    themselves or as the :class:`~phonometry.emission.ReferenceSourceCalibration`
    of ISO 6926, from which the bands at ``frequencies`` are read (an octave
    band is the energy sum of its three one-third octave bands). Given the
    meteorological conditions of the test, a calibration is read there, as
    :math:`L_W - C_2` (ISO 3741 Formulae (21) and (31)); without them, as
    calibrated, under the reference conditions (ISO 3747, whose Equation (9)
    corrects the measured levels of the reference source instead).

    :param reference_sound_power_levels: The levels, or a calibration.
    :param frequencies: The bands the method works in; required with a
        calibration.
    :param fraction: The bands of the method, 3 for one-third octaves or 1 for
        octaves.
    :param name: The parameter name for the error message.
    :param temperature_c: Air temperature at the test, in degrees Celsius, or
        ``None`` for the calibrated levels as they are.
    :param static_pressure_kpa: Static pressure at the test, in kilopascals,
        or ``None``.
    :return: The levels, in dB re 1 pW.
    :raises ValueError: for a calibration without ``frequencies`` or one that
        does not cover them.
    """
    from .reference_sound_source import ReferenceSourceCalibration

    if not isinstance(reference_sound_power_levels, ReferenceSourceCalibration):
        return real_array(cast("NumericArrayLike", reference_sound_power_levels), name)
    if frequencies is None:
        msg = (
            f"'frequencies' are required to read '{name}' from a "
            "ReferenceSourceCalibration."
        )
        raise ValueError(msg)
    return reference_sound_power_levels.sound_power_level_at(
        real_array(cast("NumericArrayLike", frequencies), "frequencies"),
        fraction=fraction,
        temperature_c=temperature_c,
        static_pressure_kpa=static_pressure_kpa,
    )
