#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Atmospheric absorption of sound: ISO 9613-1:1993.

The attenuation of a pure tone propagating through the atmosphere is governed by
a pure-tone attenuation coefficient ``alpha`` (in dB/m) that depends on frequency,
temperature, humidity and pressure through the vibrational relaxation of the
oxygen and nitrogen molecules plus classical and rotational losses
(ISO 9613-1:1993, clause 6).

The attenuation coefficient, in decibels per metre (ISO 9613-1:1993):

.. math::

   \alpha = 8.686 f^2 \left\{ 1.84 \times 10^{-11}
   \left( \frac{p_\mathrm{a}}{p_\mathrm{r}} \right)^{-1}
   \left( \frac{T}{T_0} \right)^{1/2}
   + \left( \frac{T}{T_0} \right)^{-5/2}
   \left[ 0.01275 \, \mathrm{e}^{-2239.1/T}
   \left( f_\mathrm{rO} + \frac{f^2}{f_\mathrm{rO}} \right)^{-1}
   + 0.1068 \, \mathrm{e}^{-3352.0/T}
   \left( f_\mathrm{rN} + \frac{f^2}{f_\mathrm{rN}} \right)^{-1}
   \right] \right\} \tag{Eq. 5}

with the oxygen and nitrogen relaxation frequencies (ISO 9613-1:1993):

.. math::

   f_\mathrm{rO} = \frac{p_\mathrm{a}}{p_\mathrm{r}} \left[ 24 + 4.04 \times 10^{4} \, h \,
   \frac{0.02 + h}{0.391 + h} \right] \tag{Eq. 3}

   f_\mathrm{rN} = \frac{p_\mathrm{a}}{p_\mathrm{r}} \left( \frac{T}{T_0} \right)^{-1/2}
   \left\{ 9 + 280 \, h \exp\!\left[ -4.170 \left(
   \left( \frac{T}{T_0} \right)^{-1/3} - 1 \right) \right] \right\}
   \tag{Eq. 4}

Here ``T`` is the ambient temperature (K), :math:`T_0 = 293.15` K and
:math:`p_\mathrm{r} = 101.325` kPa are the reference conditions (ISO 9613-1:1993,
clause 4.2), ``pa`` is the ambient pressure (kPa) and ``h`` is the molar
concentration of water vapour as a percentage, obtained from the relative
humidity by the psychrometric conversion (ISO 9613-1:1993, clause 6.4 /
Annex B):

.. math::

   h = h_\mathrm{r} \, \frac{p_\mathrm{sat}/p_\mathrm{r}}{p_\mathrm{a}/p_\mathrm{r}}

   \frac{p_\mathrm{sat}}{p_\mathrm{r}} = 10^{-6.8346 \, (T_{01}/T)^{1.261} + 4.6151},
   \qquad T_{01} = 273.16~\text{K}

with ``hr`` the relative humidity (%) and ``T01`` the triple-point temperature of
water.

Table 1 of ISO 9613-1:1993 tabulates ``alpha`` (in dB/km) at the reference
pressure for a grid of temperature, relative humidity and one-third-octave
frequency; its rows are labelled with the ISO 266 preferred frequencies but
the coefficients are computed at the exact midband frequencies (Note 5)
:math:`f_\mathrm{m} = 1000 \cdot 10^{k/10}`, ``k`` integer. Pass
``exact_midband=True`` to snap the requested frequencies onto that grid and
reproduce Table 1 exactly.

This module closes the loop with :mod:`~phonometry.materials.absorbers.sound_absorption` (ISO 354),
whose air power-attenuation coefficient ``m`` (1/m) is defined only through
the ISO 9613-1 ``alpha`` via :math:`m = \alpha / (10 \log_{10} e)`.
:func:`air_power_attenuation_per_m` returns that ``m`` directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.air_absorption import (
    _EIGHT_686,
    _KELVIN,
    AtmosphericAbsorptionWarning,
    _exact_midband,
    _pure_tone_terms,
    _validate,
)
from ..._internal.frozen import OwnsArrays, read_only
from ..._internal.validation import (
    real_array,
    real_number,
    require_same_shape,
    require_scalar,
)
from ..._internal.warnings import advisories_held
from ...materials import power_attenuation_from_alpha

if TYPE_CHECKING:  # pragma: no cover - typing only
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

    from ..._i18n import Language

__all__ = [
    "AtmosphericAbsorptionWarning",
    "AtmosphericAttenuation",
    "air_attenuation",
    "air_power_attenuation_per_m",
    "atmospheric_attenuation",
]


def air_attenuation(
    frequencies: ArrayLike,
    *,
    temperature_c: float = 20.0,
    relative_humidity_percent: float = 50.0,
    static_pressure_kpa: float = 101.325,
    exact_midband: bool = False,
) -> NDArray[np.float64]:
    r"""Pure-tone atmospheric attenuation coefficient (ISO 9613-1, Eq. (5)).

    Evaluates ``alpha`` in decibels per metre from the oxygen and nitrogen
    relaxation frequencies (Eq. (3)/(4)) and the classical, rotational and
    vibrational absorption terms (Eq. (5)). Fully vectorized over
    ``frequencies``; ``temperature_c``, ``relative_humidity_percent`` and
    ``static_pressure_kpa`` are scalars.

    :param frequencies: Frequency or frequencies ``f``, in hertz (array-like).
    :param temperature_c: Ambient air temperature, in degrees Celsius
        (default 20 degC, i.e. the reference ``T0``). A value outside the
        -20..+50 degC tabulated range emits an
        :class:`AtmosphericAbsorptionWarning`; a value at or below absolute zero
        raises ``ValueError``.
    :param relative_humidity_percent: Relative humidity, in percent, with respect to
        saturation over liquid water (default 50 %). Outside 10..100 % emits an
        :class:`AtmosphericAbsorptionWarning`; outside [0, 100] % raises
        ``ValueError``.
    :param static_pressure_kpa: Ambient atmospheric pressure ``pa``, in kilopascals
        (default 101.325 kPa = one standard atmosphere = ``pr``). Above 200 kPa
        emits an :class:`AtmosphericAbsorptionWarning`; non-positive raises
        ``ValueError``.
    :param exact_midband: When ``True``, each requested frequency is snapped to
        the nearest exact one-third-octave midband
        :math:`f_\mathrm{m} = 1000 \cdot 10^{k/10}` (Eq. (6)) before evaluation,
        reproducing the frequencies used for Table 1 (Note 5). Default
        ``False`` (use ``frequencies`` verbatim).
    :return: Attenuation coefficient ``alpha``, in dB/m, with the shape of
        ``frequencies``.
    :raises TypeError: if ``relative_humidity_percent``, ``static_pressure_kpa`` or
        ``temperature_c`` is not a single number, or ``frequencies`` holds a text or a
        value that is not a real number.

    .. note::
        ISO 354:2003 defers its air power-attenuation coefficient ``m`` (1/m)
        entirely to this ``alpha`` via :math:`m = \alpha / (10 \log_{10} e)`. Use
        :func:`air_power_attenuation_per_m` to obtain that ``m`` for
        :func:`~phonometry.materials.absorbers.sound_absorption.absorption_area` /
        :func:`~phonometry.materials.absorbers.sound_absorption.absorption_coefficient`.
    """
    freqs = real_array(frequencies, "frequencies")
    _validate(freqs, temperature_c, relative_humidity_percent, static_pressure_kpa)
    if exact_midband:
        freqs = _exact_midband(freqs)

    f2, bracket = _pure_tone_terms(
        freqs,
        temperature_c + _KELVIN,
        relative_humidity_percent,
        static_pressure_kpa,
    )
    alpha = _EIGHT_686 * f2 * bracket
    return np.asarray(alpha, dtype=np.float64)


def air_power_attenuation_per_m(
    frequencies: ArrayLike,
    *,
    temperature_c: float = 20.0,
    relative_humidity_percent: float = 50.0,
    static_pressure_kpa: float = 101.325,
    exact_midband: bool = False,
) -> NDArray[np.float64]:
    r"""ISO 354 air power-attenuation coefficient ``m`` (1/m) from conditions.

    Convenience composition of :func:`air_attenuation` (ISO 9613-1 ``alpha`` in
    dB/m) with the ISO 354:2003 (8.1.2.1) conversion
    :math:`m = \alpha / (10 \log_{10} e)`
    (via :func:`~phonometry.materials.absorbers.sound_absorption.power_attenuation_from_alpha`). It lets an
    ISO 354 caller feed real atmospheric conditions into
    :func:`~phonometry.materials.absorbers.sound_absorption.absorption_area` /
    :func:`~phonometry.materials.absorbers.sound_absorption.absorption_coefficient` instead of
    hand-entering ``m``.

    :param frequencies: Frequency or frequencies ``f``, in hertz (array-like).
    :param temperature_c: Ambient air temperature, in degrees Celsius (default 20).
    :param relative_humidity_percent: Relative humidity, in percent (default 50).
    :param static_pressure_kpa: Ambient atmospheric pressure, in kilopascals
        (default 101.325).
    :param exact_midband: Snap frequencies to exact midbands; see
        :func:`air_attenuation`.
    :return: Power attenuation coefficient ``m``, in 1/m, with the shape of
        ``frequencies``.
    """
    alpha = air_attenuation(
        frequencies,
        temperature_c=temperature_c,
        relative_humidity_percent=relative_humidity_percent,
        static_pressure_kpa=static_pressure_kpa,
        exact_midband=exact_midband,
    )
    return power_attenuation_from_alpha(alpha)


# --- plottable atmospheric-attenuation result (ISO 9613-1:1993) -----------


@dataclass(frozen=True)
class AtmosphericAttenuation(OwnsArrays):
    r"""A pure-tone atmospheric attenuation curve (ISO 9613-1:1993).

    Bundles the ISO 9613-1 attenuation coefficient ``alpha`` (Eq. (5)) over a
    frequency grid with the atmospheric conditions it was evaluated for, so the
    classic ``alpha`` versus frequency curve can be drawn with :meth:`plot`.
    Build it with :func:`atmospheric_attenuation`; the frozen instance is a thin,
    plottable wrapper and re-runs none of the maths.

    :ivar frequencies: Frequencies ``f`` the coefficient is evaluated at, in Hz
        (the exact one-third-octave midbands when ``exact_midband`` was used).
    :ivar attenuation_db_per_m: Pure-tone attenuation coefficient ``alpha``,
        per frequency, in decibels per metre (Table 1 prints dB/km, i.e.
        :math:`\times 1000`).
    :ivar temperature_c: Ambient air temperature, in degrees Celsius.
    :ivar relative_humidity_percent: Relative humidity, in percent.
    :ivar static_pressure_kpa: Ambient atmospheric pressure ``pa``, in kilopascals.
    :ivar distance: Propagation distance ``d``, in metres, or ``None`` when the
        result carries only the coefficient. When given, :attr:`total_attenuation`
        returns the total attenuation :math:`A = \alpha d` over that distance.
    """

    frequencies: NDArray[np.float64]
    attenuation_db_per_m: NDArray[np.float64]
    temperature_c: float
    relative_humidity_percent: float
    static_pressure_kpa: float
    distance: float | None = None

    if TYPE_CHECKING:

        def __init__(
            self,
            frequencies: ArrayLike,
            attenuation_db_per_m: ArrayLike,
            temperature_c: float,
            relative_humidity_percent: float,
            static_pressure_kpa: float,
            distance: float | None = None,
        ) -> None: ...

    def __post_init__(self) -> None:
        """Hold the curve read-only, and validate ``distance`` and the curve it belongs to.

        The frequencies and the coefficient are held as the read-only
        ``float64`` arrays :attr:`total_attenuation` and :meth:`plot` read
        them as, whatever sequence they were given as, so a list given by
        hand is arithmetic, not sequence repetition, wherever it is read.

        A propagation distance must be finite and non-negative; enforcing it
        here (rather than only in :func:`atmospheric_attenuation`) keeps direct
        construction of the frozen result and the factory consistent.

        The rest of the result is a single curve: every entry of
        :attr:`attenuation_db_per_m` is Eq. (5) evaluated at the frequency
        in the same position of :attr:`frequencies`, which is why the factory
        derives both from the one array the caller passed. :meth:`plot` reads
        them as that pair, in one ``semilogx`` call of alpha against the
        frequencies, and neither way of breaking the pairing is reported in
        those terms. Two different lengths are matplotlib's ``x and y must
        have same first dimension, but have shapes (6,) and (3,)``, raised
        from inside the plotter for a coefficient both shorter and longer than
        its frequencies, naming neither field, nor this result, nor which of
        the two shapes is the frequency axis. An extra axis is not reported at
        all: a coefficient of shape ``(6, 2)``, the shape a caller lands on
        by stacking the coefficients of two atmospheres, is drawn silently as
        two curves over the one frequency axis, with the single set of stored
        conditions printed twice in the legend, once per curve; a
        ``(6, 2)`` frequency array draws the same two curves just as quietly,
        over limits taken from the whole of it.

        A pair of nought-dimensional arrays is left alone: there is no axis
        there to disagree about. The factory never builds one (it stores a
        single frequency as a length-one array), but a direct construction
        from a scalar evaluation does, and a scalar paired with an array is
        still refused as a coefficient that carries no value per frequency.

        :raises ValueError: if ``distance`` is negative or non-finite, or if
            the coefficient and the frequency axis do not have one and the same
            shape: a different length either way, a scalar against an array,
            or an extra axis on one of the two.
        :raises TypeError: if ``distance`` is not a single number.
        """
        for name in ("frequencies", "attenuation_db_per_m"):
            curve = np.asarray(getattr(self, name), dtype=np.float64)
            object.__setattr__(self, name, read_only(curve))
        require_scalar(self.distance, "distance")
        if self.distance is not None and (
            not np.isfinite(self.distance) or self.distance < 0.0
        ):
            msg = "'distance' must be a finite, non-negative number of metres."
            raise ValueError(msg)
        require_same_shape(
            self, "frequencies", "attenuation_db_per_m", quantity="frequency"
        )

    @property
    def total_attenuation(self) -> NDArray[np.float64] | None:
        r"""Total attenuation :math:`A = \alpha d` over :attr:`distance`.

        The pure-tone attenuation ``alpha`` (dB/m) accumulated over the
        propagation distance ``d`` (m), per frequency, in decibels; this is the
        ISO 9613-2:1996 ``Aatm`` (Eq. (8)) form. ``None`` when no
        :attr:`distance` was supplied.
        """
        if self.distance is None:
            return None
        return np.asarray(self.attenuation_db_per_m * self.distance, dtype=np.float64)

    def plot(
        self, ax: Axes | None = None, *, language: Language = "en", **kwargs: Any
    ) -> Axes:
        """Plot the attenuation coefficient ``alpha`` versus frequency.

        Draws ``alpha`` (in dB/km, as Table 1 tabulates it) on a logarithmic
        frequency axis, the classic ISO 9613-1 curve for the stored atmospheric
        conditions. Requires matplotlib (the ``[plot]`` extra);
        returns the :class:`~matplotlib.axes.Axes` and never calls ``plt.show``.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the ``alpha`` curve ``plot`` call.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.environment import plot_atmospheric_attenuation

        check_language(language)
        return plot_atmospheric_attenuation(self, ax=ax, language=language, **kwargs)


def atmospheric_attenuation(
    frequencies: ArrayLike,
    *,
    temperature_c: float = 20.0,
    relative_humidity_percent: float = 50.0,
    static_pressure_kpa: float = 101.325,
    exact_midband: bool = False,
    distance: float | None = None,
) -> AtmosphericAttenuation:
    r"""Build a plottable ISO 9613-1 atmospheric-attenuation curve.

    Evaluates :func:`air_attenuation` at ``frequencies`` for the given
    atmospheric conditions and bundles the result into an
    :class:`AtmosphericAttenuation` that exposes ``.plot()``. The maths is
    unchanged; this is a thin, plottable wrapper around the existing function
    (the same warnings and the same ``ValueError`` cases apply).

    :param frequencies: Frequency or frequencies ``f``, in hertz (array-like).
    :param temperature_c: Ambient air temperature, in degrees Celsius (default 20).
    :param relative_humidity_percent: Relative humidity, in percent (default 50).
    :param static_pressure_kpa: Ambient atmospheric pressure, in kilopascals
        (default 101.325 kPa, one standard atmosphere).
    :param exact_midband: Snap the frequencies to the exact one-third-octave
        midbands :math:`f_\mathrm{m} = 1000 \cdot 10^{k/10}` (Eq. (6)) before
        evaluation; see :func:`air_attenuation`. When ``True`` the stored
        :attr:`frequencies` are the snapped midbands the coefficient was
        computed at.
    :param distance: Optional propagation distance ``d``, in metres. When given,
        the result's :attr:`~AtmosphericAttenuation.total_attenuation` returns
        the total attenuation :math:`A = \alpha d` over that distance
        (ISO 9613-2 Eq. (8)). Must be finite and non-negative.
    :return: A frozen :class:`AtmosphericAttenuation`.
    :raises ValueError: If ``distance`` is negative or non-finite (NaN/inf); the
        check lives on :class:`AtmosphericAttenuation` so it also guards direct
        construction.
    :raises TypeError: if ``frequencies`` holds a text or a value that is not a real
        number.
        ``distance`` is refused the same way when it is not one real number.
    """
    # Every advisory waits for the result: a refusal reached after one is
    # still what the caller meets under -W error.
    with advisories_held():
        freqs = real_array(frequencies, "frequencies")
        alpha = air_attenuation(
            frequencies,
            temperature_c=temperature_c,
            relative_humidity_percent=relative_humidity_percent,
            static_pressure_kpa=static_pressure_kpa,
            exact_midband=exact_midband,
        )
        if exact_midband:
            freqs = _exact_midband(freqs)
        return AtmosphericAttenuation(
            frequencies=np.atleast_1d(freqs),
            attenuation_db_per_m=np.atleast_1d(alpha),
            temperature_c=float(temperature_c),
            relative_humidity_percent=float(relative_humidity_percent),
            static_pressure_kpa=float(static_pressure_kpa),
            distance=None if distance is None else real_number(distance, "distance"),
        )
