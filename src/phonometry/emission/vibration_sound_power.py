#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Airborne sound power from surface vibration (ISO/TS 7849-1/-2:2009).

The airborne sound power a machine radiates through the structure-borne
vibration of its outer surface is estimated from the surface vibratory velocity
and a **radiation factor** ``epsilon`` (the radiation efficiency). The radiated
power, in watts, is (ISO/TS 7849-1, Equation 6):

.. math::

   P = Z_\mathrm{c} \, \langle v^2 \rangle \, S \, \epsilon

with :math:`Z_\mathrm{c}` the characteristic impedance of air and
:math:`\langle v^2 \rangle` the mean-square vibratory velocity averaged over
the radiating area :math:`S`. The vibratory velocity is reported as a
**level**, in decibels, re :math:`v_0 = 5 \times 10^{-8}` m/s (Equation 3):

.. math::

   L_v = 10 \log_{10}\frac{\langle v^2 \rangle}{v_0^2} = 20 \log_{10}\frac{v}{v_0}

so the A-weighted sound power level follows in logarithmic form, in decibels
(ISO/TS 7849-1, Equation 12; ISO/TS 7849-2, Equation 15):

.. math::

   L_W = L_v + 10 \log_{10}\frac{S}{S_0} + 10 \log_{10} \epsilon
   + 10 \log_{10}\frac{Z_\mathrm{c,n}}{Z_{\mathrm{c},0}}

where :math:`S_0 = 1~\text{m}^2`, the normalized characteristic impedance
:math:`Z_\mathrm{c,n} = 411~\text{N s/m}^3` (at 23 degC, 101.3 kPa) and the
reference acoustic impedance :math:`Z_{\mathrm{c},0} = 400~\text{N s/m}^3` give the
fixed :math:`10 \log_{10}(411/400) = 0.118` dB term.

The two parts differ only in ``epsilon``:

* **Part 1 (survey)** assumes :math:`\epsilon = 1` and yields the *upper
  limit* ``L_W,max`` of the radiated power, needing only
  :math:`\langle v^2 \rangle` and ``S``.
* **Part 2 (engineering)** applies a frequency-band radiation factor
  ``epsilon_j`` determined (per ISO 9614) as
  :math:`\epsilon_j = P_j / (Z_\mathrm{c,n} \langle v_j^2 \rangle S)` (Equation 8).

This module feeds the structure-borne source characterisation standards
(ISO 9611, EN 15657, EN 12354-5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, overload

import numpy as np

from .._internal.types import as_float_or_array

if TYPE_CHECKING:
    import os

    from matplotlib.axes import Axes
    from numpy.typing import NDArray

    from .._i18n import Language
    from .._internal.types import NumericArrayLike, RealScalar, RealValues, ReportEngine
    from .._report.metadata import ReportMetadata


from .._internal.frozen import OwnsArrays
from .._internal.validation import (
    check_engine,
    real_array,
    require_equal_shapes,
    require_positive,
    require_ranks,
    require_same_length,
    require_scalar,
)

__all__ = [
    "NORMALIZED_IMPEDANCE_PA_S_M",
    "REFERENCE_VELOCITY_M_S",
    "VibrationSoundPowerResult",
    "extraneous_velocity_correction",
    "mean_velocity_level",
    "radiated_sound_power_level",
    "radiation_factor",
    "sound_power_from_vibration",
    "velocity_level",
    "velocity_level_from_acceleration",
]

#: Reference vibratory velocity ``v0`` (ISO/TS 7849-1:2009, Equation 3), m/s:
#: the 50 nm/s ISO 1683:2015 keeps for structure-borne sound in note b of
#: Table 3, not its 1 nm/s.
REFERENCE_VELOCITY_M_S: float = 5.0e-8
#: Normalized characteristic impedance ``Z_c,n`` at 23 degC, 101.3 kPa, in Pa.s/m
#: (N.s/m3).
NORMALIZED_IMPEDANCE_PA_S_M: float = 411.0
#: Reference acoustic impedance of air ``Z_c,0``, N.s/m3.
_REFERENCE_IMPEDANCE: float = 400.0
#: Reference area ``S0``, m2.
_REFERENCE_AREA: float = 1.0

#: ISO/TS 7849-1 Table 2: correction K1A (dB) for extraneous vibratory velocity
#: keyed by the integer level difference dLv (dB). dLv >= 10 -> 0; dLv < 3 -> 3.
_K1A_TABLE: dict[int, float] = {
    3: 3.0,
    4: 2.0,
    5: 2.0,
    6: 1.0,
    7: 1.0,
    8: 1.0,
    9: 1.0,
    10: 0.0,
}
#: Table 2 top edge: Delta L_v (dB) at or above which the correction K1A is 0 dB.
_K1A_ZERO_ABOVE_DB: float = 10.0
#: Table 2 bottom edge: below this Delta L_v (dB) the table bottoms out, K1A is
#: clamped to the 3 dB floor value and the result becomes an upper boundary.
_K1A_CLAMPED_BELOW_DB: float = 3.0


@overload
def velocity_level[S: RealScalar](velocity: S, *, reference: float = ...) -> float: ...


@overload
def velocity_level[V: RealValues](
    velocity: V,
    *,
    reference: float = ...,
) -> NDArray[np.float64]: ...


@overload
def velocity_level[A: NumericArrayLike](
    velocity: A,
    *,
    reference: float = ...,
) -> float | NDArray[np.float64]: ...


def velocity_level(
    velocity: NumericArrayLike, *, reference: float = REFERENCE_VELOCITY_M_S
) -> float | NDArray[np.float64]:
    r"""Vibratory velocity level (ISO/TS 7849-1, Eq. 3).

    :math:`L_v = 20 \log_{10}(v/v_0)` with ``v0`` the reference velocity.

    :param velocity: R.m.s. vibratory velocity ``v`` (scalar or array), in m/s.
    :param reference: Reference velocity ``v0`` (Default: 5e-8 m/s).
    :return: The velocity level ``L_v``, in dB re ``v0``. A ``float`` for a number, an
        array for a sequence or an array, a zero-dimensional one included.
    :raises ValueError: for a non-positive reference.
    :raises TypeError: if ``reference`` is not a single number, or ``velocity`` holds a
        text or a value that is not a real number.
    """
    reference = require_positive(reference, "reference")
    v = real_array(velocity, "velocity")
    return as_float_or_array(20.0 * np.log10(np.abs(v) / reference), like=(velocity,))


@overload
def velocity_level_from_acceleration[S1: RealScalar, S2: RealScalar](
    peak_acceleration: S1,
    *,
    frequency: S2,
    reference: float = ...,
) -> float: ...


@overload
def velocity_level_from_acceleration[V: RealValues, A2: NumericArrayLike](
    peak_acceleration: V,
    *,
    frequency: A2,
    reference: float = ...,
) -> NDArray[np.float64]: ...


@overload
def velocity_level_from_acceleration[S1: RealScalar, V: RealValues](
    peak_acceleration: S1,
    *,
    frequency: V,
    reference: float = ...,
) -> NDArray[np.float64]: ...


@overload
def velocity_level_from_acceleration[A1: NumericArrayLike, A2: NumericArrayLike](
    peak_acceleration: A1,
    *,
    frequency: A2,
    reference: float = ...,
) -> float | NDArray[np.float64]: ...


def velocity_level_from_acceleration(
    peak_acceleration: NumericArrayLike,
    *,
    frequency: NumericArrayLike,
    reference: float = REFERENCE_VELOCITY_M_S,
) -> float | NDArray[np.float64]:
    r"""Velocity level from a sinusoidal acceleration (ISO/TS 7849-1, Eq. 8).

    :math:`L_v = 20 \log_{10}\!\left( \frac{a_{\text{peak}}}{2\pi f v_0 \sqrt{2}}
    \right)`, used to convert a calibration acceleration to the equivalent
    r.m.s. velocity level.

    :param peak_acceleration: Peak acceleration ``a_peak`` (scalar or array),
        in m/s^2.
    :param frequency: Frequency ``f``, in hertz (scalar or array).
    :param reference: Reference velocity ``v0`` (Default: 5e-8 m/s).
    :return: The velocity level ``L_v``, in dB re ``v0``. A ``float`` when
        ``peak_acceleration`` and ``frequency`` are both numbers, an array when either
        is a sequence or an array, a zero-dimensional one included.
    :raises ValueError: for a non-positive frequency or reference.
    :raises TypeError: if ``reference`` is not a single number, or ``frequency`` or
        ``peak_acceleration`` holds a text or a value that is not a real number.
    """
    reference = require_positive(reference, "reference")
    a = real_array(peak_acceleration, "peak_acceleration")
    f = real_array(frequency, "frequency")
    if np.any(f <= 0.0):
        msg = "'frequency' must be positive."
        raise ValueError(msg)
    v_rms = np.abs(a) / (2.0 * np.pi * f * np.sqrt(2.0))
    return as_float_or_array(
        20.0 * np.log10(v_rms / reference), like=(peak_acceleration, frequency)
    )


def mean_velocity_level(
    levels: NumericArrayLike, areas: NumericArrayLike | None = None
) -> float:
    """Mean vibratory velocity level over the surface (ISO/TS 7849-1, Eq. 10/11).

    With uniformly distributed positions (``areas`` is ``None``) this is the
    energetic average (Equation 10); with per-position partial areas it is the
    area-weighted average (Equation 11).

    :param levels: Velocity levels ``L_v,i`` at the positions, in dB.
    :param areas: Partial areas ``S_i`` (Equation 11), or ``None`` for the
        uniform energetic average (Equation 10).
    :return: The mean velocity level, in dB.
    :raises TypeError: if ``areas`` or ``levels`` holds a text or a value that is not a
        real number.
    """
    lv = real_array(levels, "levels")
    energy = 10.0 ** (0.1 * lv)
    if areas is None:
        mean_energy = float(np.mean(energy))
    else:
        s = real_array(areas, "areas")
        require_equal_shapes(
            "mean_velocity_level",
            {"levels": lv.shape, "areas": s.shape},
            "position",
        )
        mean_energy = float(np.sum(s * energy) / np.sum(s))
    return float(10.0 * np.log10(mean_energy))


@overload
def radiation_factor[S1: RealScalar, S2: RealScalar](
    sound_power: S1,
    area: float,
    mean_square_velocity: S2,
    *,
    impedance: float = ...,
) -> float: ...


@overload
def radiation_factor[V: RealValues, A2: NumericArrayLike](
    sound_power: V,
    area: float,
    mean_square_velocity: A2,
    *,
    impedance: float = ...,
) -> NDArray[np.float64]: ...


@overload
def radiation_factor[S1: RealScalar, V: RealValues](
    sound_power: S1,
    area: float,
    mean_square_velocity: V,
    *,
    impedance: float = ...,
) -> NDArray[np.float64]: ...


@overload
def radiation_factor[A1: NumericArrayLike, A2: NumericArrayLike](
    sound_power: A1,
    area: float,
    mean_square_velocity: A2,
    *,
    impedance: float = ...,
) -> float | NDArray[np.float64]: ...


def radiation_factor(
    sound_power: NumericArrayLike,
    area: float,
    mean_square_velocity: NumericArrayLike,
    *,
    impedance: float = NORMALIZED_IMPEDANCE_PA_S_M,
) -> float | NDArray[np.float64]:
    r"""A-weighted radiation factor ``epsilon`` (ISO/TS 7849-1 Eq. 4, -2 Eq. 8).

    :math:`\epsilon = P / (Z_\mathrm{c} \langle v^2 \rangle S)`, the sound-radiation
    efficiency, from an independently measured radiated power (ISO 9614), the
    surface area and the mean-square vibratory velocity.

    :param sound_power: Radiated airborne sound power ``P`` (scalar or array),
        in W.
    :param area: Radiating surface area ``S``, in m^2 (> 0).
    :param mean_square_velocity: Mean-square vibratory velocity
        :math:`\langle v^2 \rangle`, in (m/s)^2.
    :param impedance: Characteristic impedance ``Z_c`` (Default: 411 N.s/m^3).
    :return: The radiation factor ``epsilon`` (dimensionless). A ``float`` when
        ``sound_power`` and ``mean_square_velocity`` are both numbers, an array when
        either is a sequence or an array, a zero-dimensional one included.
    :raises ValueError: for a non-positive area or impedance.
    :raises TypeError: if ``area`` or ``impedance`` is not a single number, or
        ``mean_square_velocity`` or ``sound_power`` holds a text or a value that is not
        a real number.
    """
    area = require_positive(area, "area")
    impedance = require_positive(impedance, "impedance")
    p = real_array(sound_power, "sound_power")
    v2 = real_array(mean_square_velocity, "mean_square_velocity")
    return as_float_or_array(
        p / (impedance * v2 * area), like=(sound_power, mean_square_velocity)
    )


@overload
def radiated_sound_power_level[S1: RealScalar, S2: RealScalar](
    velocity_level: S1,
    area: float,
    *,
    radiation_factor: S2 = ...,
    reference_area: float = ...,
    normalized_impedance: float = ...,
    reference_impedance: float = ...,
) -> float: ...


@overload
def radiated_sound_power_level[V: RealValues, A2: NumericArrayLike](
    velocity_level: V,
    area: float,
    *,
    radiation_factor: A2 = ...,
    reference_area: float = ...,
    normalized_impedance: float = ...,
    reference_impedance: float = ...,
) -> NDArray[np.float64]: ...


@overload
def radiated_sound_power_level[S1: RealScalar, V: RealValues](
    velocity_level: S1,
    area: float,
    *,
    radiation_factor: V,
    reference_area: float = ...,
    normalized_impedance: float = ...,
    reference_impedance: float = ...,
) -> NDArray[np.float64]: ...


@overload
def radiated_sound_power_level[A1: NumericArrayLike, A2: NumericArrayLike](
    velocity_level: A1,
    area: float,
    *,
    radiation_factor: A2 = ...,
    reference_area: float = ...,
    normalized_impedance: float = ...,
    reference_impedance: float = ...,
) -> float | NDArray[np.float64]: ...


def radiated_sound_power_level(
    velocity_level: NumericArrayLike,
    area: float,
    *,
    radiation_factor: NumericArrayLike = 1.0,
    reference_area: float = _REFERENCE_AREA,
    normalized_impedance: float = NORMALIZED_IMPEDANCE_PA_S_M,
    reference_impedance: float = _REFERENCE_IMPEDANCE,
) -> float | NDArray[np.float64]:
    r"""Radiated sound power level (ISO/TS 7849-1 Eq. 12, -2 Eq. 15).

    .. math::

       L_W = L_v + 10 \log_{10}\frac{S}{S_0} + 10 \log_{10} \epsilon
       + 10 \log_{10}\frac{Z_\mathrm{c,n}}{Z_{\mathrm{c},0}}

    With the default ``radiation_factor = 1`` this is the Part 1 *upper limit*
    ``L_W,max``; pass a measured ``epsilon`` for the Part 2 engineering value.

    :param velocity_level: Mean vibratory velocity level ``L_v`` (scalar or
        array, e.g. per band), in dB re 5e-8 m/s.
    :param area: Radiating surface area ``S``, in m^2 (> 0).
    :param radiation_factor: Radiation factor ``epsilon`` (Default: 1.0).
    :param reference_area: Reference area ``S0`` (Default: 1 m^2).
    :param normalized_impedance: ``Z_c,n`` (Default: 411 N.s/m^3).
    :param reference_impedance: ``Z_c,0`` (Default: 400 N.s/m^3).
    :return: The sound power level ``L_W``, in dB re 1 pW. A ``float`` when
        ``velocity_level`` and ``radiation_factor`` are both numbers, an array when
        either is a sequence or an array, a zero-dimensional one included.
    :raises ValueError: for a non-positive area, reference area or impedance.
    :raises TypeError: if ``area``, ``normalized_impedance``, ``reference_area`` or
        ``reference_impedance`` is not a single number, or ``radiation_factor`` or
        ``velocity_level`` holds a text or a value that is not a real number.
    """
    area = require_positive(area, "area")
    reference_area = require_positive(reference_area, "reference_area")
    normalized_impedance = require_positive(
        normalized_impedance, "normalized_impedance"
    )
    reference_impedance = require_positive(reference_impedance, "reference_impedance")
    lv = real_array(velocity_level, "velocity_level")
    eps = real_array(radiation_factor, "radiation_factor")
    lw = (
        lv
        + 10.0 * np.log10(area / reference_area)
        + 10.0 * np.log10(eps)
        + 10.0 * np.log10(normalized_impedance / reference_impedance)
    )
    return as_float_or_array(lw, like=(velocity_level, radiation_factor))


def extraneous_velocity_correction(level_difference: float) -> float:
    r"""Correction K1A for extraneous vibration (ISO/TS 7849-1, Table 2).

    :math:`\Delta L_v` is the difference between the operating and the
    extraneous vibratory velocity levels. The correction is subtracted from
    the measured level; per the standard :math:`\Delta L_v \ge 10` dB gives
    0 dB, and :math:`\Delta L_v < 3` dB uses the 3 dB value (the result is
    then an upper boundary). The level difference is rounded to the nearest
    integer decibel to index the standard's table.

    :param level_difference: Level difference :math:`\Delta L_v`, in dB.
    :return: The correction ``K1A`` to subtract, in dB.
    :raises TypeError: if ``level_difference`` is not a single number.
    """
    require_scalar(level_difference, "level_difference")
    if level_difference >= _K1A_ZERO_ABOVE_DB:
        return 0.0
    if level_difference < _K1A_CLAMPED_BELOW_DB:
        return 3.0
    return _K1A_TABLE[round(level_difference)]


@dataclass(frozen=True)
class VibrationSoundPowerResult(OwnsArrays):
    """Sound power radiated by surface vibration (ISO/TS 7849).

    :ivar frequencies: Band centre frequencies, in hertz, or ``None`` for a
        single broadband value.
    :ivar velocity_level: Mean vibratory velocity level ``L_v`` per band, in dB.
    :ivar sound_power_level: Radiated sound power level ``L_W`` per band, in dB.
    :ivar radiation_factor: Radiation factor ``epsilon`` per band.
    :ivar area: Radiating surface area ``S``, in m^2.
    """

    velocity_level: NDArray[np.float64]
    sound_power_level: NDArray[np.float64]
    radiation_factor: NDArray[np.float64]
    area: float
    frequencies: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        """Reject a determination whose per-band quantities disagree.

        The fiche prints one row per band under a single header, taking the
        row count from ``sound_power_level`` and reading ``velocity_level``
        (and ``radiation_factor`` in the verbose table) at the same indices,
        so a short array cannot be read to the end of the sheet and a long one
        is dropped by it silently. ``frequencies`` are read there too, for the
        row labels, but they never mislabel a sheet: the fiche dies on the
        labels it runs out of, with a bare ``IndexError``. The quiet one is
        :attr:`sound_power_level_a`, which picks one A-weighting correction
        per band on its own: a single stray frequency broadcasts its one
        correction over every level and hands back an ``LWA`` that no band of
        the result supports, where any other mismatched length raises from
        numpy about two shapes that name neither field.

        Every quantity must also be finite, and the area positive. The one
        producer, :func:`sound_power_from_vibration`, computes finite levels
        from finite inputs and pins the area positive, so a non-finite value
        here is never the library's own output; letting one through changes
        what the fiche claims rather than crashing it. A single NaN band in
        ``sound_power_level`` turns :attr:`sound_power_level_a` into NaN, so
        the sheet silently swaps its boxed ``LWA`` for a partial unweighted
        total ``LW`` (the energy sum skips the NaN band) and compares *that*
        against the declared A-weighted limit, flipping the printed verdict;
        a NaN ``area`` prints ``S = nan m2`` beside the boxed result; and an
        all-NaN ``radiation_factor`` fails the ``epsilon = 1`` survey test,
        so the basis line asserts an engineering-method determination whose
        every epsilon cell is an em dash.

        The determination must also cover at least one band. Four length-0
        columns agree with each other, so every count and rank above is
        satisfied, and what comes out is a complete accredited sound-power
        test sheet: the basis line, an empty per-band table, a boxed
        "Sound power level LW = — dB re 1 pW" over the em dash the energy sum
        of no bands leaves behind, and the disclaimer under it. A single
        broadband determination is not that, and is not refused here: it
        carries one nought-dimensional level and no frequencies, which is one
        band's worth of data on no band axis.

        :raises ValueError: if any per-band quantity disagrees with the
            rest, the determination covers no band, any quantity carries a
            non-finite value, or the area is not a positive finite number.
        :raises TypeError: if ``area`` is not a single number.
        """
        require_ranks(
            self,
            velocity_level=1,
            sound_power_level=1,
            radiation_factor=1,
            frequencies=1,
        )
        require_same_length(
            self,
            "velocity_level",
            "sound_power_level",
            "radiation_factor",
            "frequencies",
        )
        if np.asarray(self.sound_power_level).size == 0:
            msg = (
                "VibrationSoundPowerResult: 'sound_power_level' must carry at "
                "least one band; the determination is empty."
            )
            raise ValueError(msg)
        for name in (
            "velocity_level",
            "sound_power_level",
            "radiation_factor",
            "frequencies",
        ):
            value = getattr(self, name)
            if value is not None and not np.all(np.isfinite(np.asarray(value))):
                msg = (
                    "VibrationSoundPowerResult: "
                    f"'{name}' must contain only finite values."
                )
                raise ValueError(msg)
        require_positive(self.area, "area")

    @property
    def total_level(self) -> float:
        r"""Band-summed sound power level, in dB:
        :math:`10 \log_{10} \sum_j 10^{0.1 L_{Wj}}`.
        """
        lw = np.asarray(self.sound_power_level, dtype=np.float64)
        return float(10.0 * np.log10(np.sum(10.0 ** (0.1 * lw))))

    @property
    def sound_power_level_a(self) -> float:
        """A-weighted sound power level ``L_WA``, in dB re 1 pW.

        Combines the band levels with the A-weighting band corrections of
        ISO 3744:2010 Annex E (the standard tabulation reused by the vibration
        method) when band centre frequencies are known. Without band
        frequencies the result is an unweighted broadband level that cannot be
        A-weighted, so ``L_WA`` is undefined and ``nan`` is returned (the
        report then boxes the unweighted total ``L_W`` instead of an ``L_WA``
        claim, and no A-weighted verdict is drawn).
        """
        if self.frequencies is None:
            return float("nan")
        from .._internal.sound_power import _a_weighting_corrections

        lw = np.asarray(self.sound_power_level, dtype=np.float64)
        ck = _a_weighting_corrections(np.asarray(self.frequencies, dtype=np.float64))
        return float(10.0 * np.log10(np.sum(10.0 ** (0.1 * (lw + ck)))))

    def plot(
        self, ax: Axes | None = None, *, language: Language = "en", **kwargs: Any
    ) -> Axes:
        """Plot the radiated sound power level per band.

        Requires matplotlib (the ``[plot]`` extra); returns the
        :class:`~matplotlib.axes.Axes`.

        :param language: The language of the labels: ``"en"`` or ``"es"``.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_vibration_sound_power

        check_language(language)
        return plot_vibration_sound_power(self, ax=ax, language=language, **kwargs)

    def report(
        self,
        path: str | os.PathLike[str],
        *,
        metadata: ReportMetadata | None = None,
        engine: ReportEngine = "reportlab",
        verbose: bool = False,
        language: Language = "en",
    ) -> str:
        r"""Render an ISO/TS 7849 sound-power-from-vibration determination fiche.

        Writes a one-page sound-power test sheet: the standard-basis line naming
        the vibration method (the ISO/TS 7849-1 survey method with a fixed
        radiation factor when every band uses ``epsilon = 1``, otherwise the
        ISO/TS 7849-2 engineering method with a determined radiation factor), an
        optional metadata header (client, machine/source, test environment,
        instrumentation, climate, date), a per-band table (nominal
        octave/one-third-octave frequency, the surface vibratory velocity level
        ``Lv`` and the radiated band sound-power level ``LW``), the sound-power
        spectrum ``LW(f)`` with a nominal band axis, the boxed A-weighted sound
        power level ``LWA`` (dB re 1 pW) with the total ``LW``, the radiating
        area ``S`` and the applied method, an optional verdict row against a
        declared limit, and a measurement-basis strip stating the sound-power
        relation :math:`L_W = L_v + 10 \log_{10}(S/S_0) + 10 \log_{10} \epsilon
        + 10 \log_{10}(Z_\mathrm{c,n}/Z_{\mathrm{c},0})`.

        :param path: Destination path of the PDF file.
        :param metadata: Optional :class:`~phonometry.ReportMetadata` supplying
            the header (``client``, ``specimen`` the machine/source, ``test_room``
            the test environment, ``instrumentation``, ``temperature_c``,
            ``relative_humidity_percent``, ``pressure``, ``test_date``), the footer
            identity (``laboratory``, ``operator``, ``report_id``, ``notes``)
            and, via ``requirement``, a declared A-weighted sound-power limit
            the fiche checks the result against (lower is better). The radiating
            area ``S`` comes from the result itself.
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: When ``True`` the per-band table adds the radiation
            factor ``epsilon`` column.
        :param language: Fiche language: ``"en"`` (default) or ``"es"``.
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` is not ``"reportlab"`` or ``language``
            is unknown.
        :raises ImportError: If reportlab (or, for the figure, matplotlib) is
            not installed (the ``[report]`` extra).
        """
        from .._i18n import check_language

        check_language(language)
        check_engine(engine)
        from .._report.iso7849 import render_vibration_power_report

        return render_vibration_power_report(
            self, path, metadata=metadata, verbose=verbose, language=language
        )


def sound_power_from_vibration(
    velocity_level: NumericArrayLike,
    area: float,
    *,
    radiation_factor: NumericArrayLike = 1.0,
    frequencies: NumericArrayLike | None = None,
) -> VibrationSoundPowerResult:
    """Bundle a sound-power-from-vibration determination (ISO/TS 7849).

    :param velocity_level: Mean vibratory velocity level ``L_v`` (per band), dB.
    :param area: Radiating surface area ``S``, in m^2 (> 0).
    :param radiation_factor: Radiation factor ``epsilon`` (Default: 1.0 -> the
        Part 1 upper limit); scalar or per band.
    :param frequencies: Band centre frequencies, in hertz, or ``None``.
    :return: The :class:`VibrationSoundPowerResult`.
    :raises TypeError: if ``frequencies``, ``radiation_factor`` or ``velocity_level``
        holds a text or a value that is not a real number.
    """
    lv = np.atleast_1d(real_array(velocity_level, "velocity_level"))
    eps = np.broadcast_to(
        real_array(radiation_factor, "radiation_factor"), lv.shape
    ).astype(np.float64)
    lw = radiated_sound_power_level(lv, area, radiation_factor=eps)
    freq = None
    if frequencies is not None:
        freq = np.atleast_1d(real_array(frequencies, "frequencies"))
        require_equal_shapes(
            "sound_power_from_vibration",
            {"velocity_level": lv.shape, "frequencies": freq.shape},
            "band",
        )
    return VibrationSoundPowerResult(
        velocity_level=lv,
        sound_power_level=np.asarray(lw, dtype=np.float64),
        radiation_factor=eps,
        area=float(area),
        frequencies=freq,
    )
