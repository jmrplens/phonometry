#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Reference sound sources: the performance requirements and the calibration of
ISO 6926:2016.

A reference sound source is the yardstick of every comparison method of the
ISO 3740 family: ISO 3741 in a reverberation room, ISO 3747 in situ, ISO 9295
in the 16 kHz octave band. ISO 6926 says what a source must do to serve
(clause 5) and how its sound power levels are calibrated (clauses 8 to 10).

**Requirements (clause 5).** The sound power output is steady: the standard
deviation under repeatability conditions of three repeated sound power levels
or five repeated sound pressure levels,

.. math::

   \sigma_r = \sqrt{\frac{1}{N-1} \sum_{j=1}^{N}
   \left( L_{X,j} - \overline{L_X} \right)^2}
   \tag{Formula (1)}

with :math:`\overline{L_X}` the *energy* average of the :math:`N`
repetitions, does not exceed Table 1 (0,8 dB from 50 Hz to 80 Hz, 0,4 dB from
100 Hz to 160 Hz, 0,2 dB from 200 Hz to 20 kHz), and over the declared range
of its electrical or mechanical supply (the line voltage, say) no one-third
octave band varies by more than 0,3 dB either way. The spectrum is broadband: from
100 Hz to 10 000 Hz every one-third octave band lies within a range of 12 dB
and within 3 dB of its neighbours, and 16 dB and 4 dB over a range extended
beyond it (5.4). The directivity index :math:`D_{\mathrm{I}i} = L_{pi} -
\overline{L_p}` (3.9) does not exceed +6 dB in any band from 100 Hz to
10 000 Hz (5.5), unless the source is labelled for reverberation rooms only.
Recalibration is due when a band has moved by more than 2,83 times Table 1
between two checks (5.6).

**Calibration in a hemi-anechoic room (clause 8).** The room meets the
broadband qualification of ISO 3745 Annex A (8.1), the source stands on the
reflecting plane and the levels are measured over a hemisphere of radius 2 m
(8.2.1). The sound power level under the reference meteorological conditions
of clause 4 (23,0 degC, 101,325 kPa) is

.. math::

   L_W = \overline{L_p} + 10 \lg\frac{S}{S_0}\ \mathrm{dB}
   + C_1 + C_2 + C_3 \tag{Formula (2)}

with :math:`C_1 = -10 \lg(p_\mathrm{s}/p_{\mathrm{s},0}) + 5 \lg(\theta /
\theta_0)`, :math:`\theta_0` = 314 K, the radiation impedance correction
:math:`C_2` from the manufacturer or from Annex A, and the air absorption
:math:`C_3 = A_0 (1{,}005\,3 - 0{,}001\,2 A_0)^{1{,}6}` with :math:`A_0 = a(f)
r`. Annex A gives :math:`C_2 = -10 \lg(p_\mathrm{s}/p_{\mathrm{s},0}) + n \lg
(\theta/\theta_1)`, :math:`\theta_1` = 296 K, with :math:`n` = 15 for a
monopole below the knee frequency :math:`f_\mathrm{k} = c/(2\pi d_0)`, 5 for a
monopole at or above it, 25 for an aerodynamic dipole at or above it and 7,5
when the radiation is unknown. Annex B replaces the 50 Hz, 63 Hz and 80 Hz
bands by sound intensity levels when those agree with the pressure levels
within Table B.1 from 50 Hz to 315 Hz. Table 2 gives the reproducibility
standard deviation from which clause 11 builds the expanded uncertainty.

The calibration is consumed where a comparison method asks for
:math:`L_{W(\mathrm{RSS})}`: :func:`~phonometry.emission.sound_power_comparison`,
:func:`~phonometry.emission.sound_energy_comparison`,
:func:`~phonometry.emission.sound_power_in_situ`,
:func:`~phonometry.emission.sound_energy_in_situ` and
:func:`~phonometry.emission.high_frequency_sound_power_comparison` accept a
:class:`ReferenceSourceCalibration` where they accept the levels, and read the
bands they need from it. The calibration holds :math:`L_W` under the
reference meteorological conditions, where :math:`C_2` carried the power the
source radiated during the calibration (8.4). ISO 3741 wants
:math:`L_{W(\mathrm{RSS})}` "corrected to the meteorological conditions at
the time of test" (Formulae (21) and (31)), and ISO 9295 carries its levels
to the reference conditions as ISO 3741 does (10.1), so for those methods the
calibration is read as :math:`L_W - C_2`, with :math:`C_2` evaluated at the
test by the same formula the calibration used, as 8.4 asks
(:meth:`ReferenceSourceCalibration.sound_power_level_at` with the test's
temperature and pressure). ISO 3747 instead corrects the reference source's
measured pressure levels "for speed, temperature and static pressure
according to the manufacturer's specifications" (Equation (9)), which puts
the source back at its calibration, and reads the calibrated levels as they
are.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import KW_ONLY, dataclass
from typing import TYPE_CHECKING, Any, Literal, cast

import numpy as np

from .._internal.levels_math import energy_mean, energy_sum
from .._internal.validation import require_positive
from ._shared import (
    _PS0,
    _S0,
    _THETA1,
    SoundPowerWarning,
    _a_weighting_corrections,
    _c1_correction,
    _validate_meteorology,
)
from .free_field_qualification import FreeFieldCheck, _band_index, _nominal
from .sound_power_anechoic import sound_power_anechoic

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

    from .sound_power_anechoic import PrecisionSoundPowerResult

RadiationCharacter = Literal["monopole", "dipole", "unknown"]
MicrophoneArrangement = Literal["paths", "fixed"]
CalibrationEnvironment = Literal["hemi-anechoic", "reverberation-room"]
BandWidth = Literal["one-third-octave", "octave"]

#: 8.2.1: hemispherical measurement surface of radius 2 m.
_RADIUS_M = 2.0
#: Absolute zero offset of the kelvin temperature ISO 6926 prints as theta.
_KELVIN_OFFSET = 273.15
#: Annex A: exponents of lg(theta/theta_1) in Formulae (A.2) to (A.5).
_C2_MONOPOLE_LOW = 15.0
_C2_MONOPOLE_HIGH = 5.0
_C2_DIPOLE = 25.0
_C2_UNKNOWN = 7.5

#: One-third octave band indices (0 is 1 kHz) of the band edges ISO 6926 uses.
_K_50 = -13
_K_80 = -11
_K_100 = -10
_K_160 = -8
_K_315 = -5
_K_3150 = 5
_K_10000 = 10
_K_20000 = 13

#: Table 1: largest standard deviation under repeatability conditions, dB.
_TABLE_1_DB = ((_K_80, 0.8), (_K_160, 0.4), (_K_20000, 0.2))
#: 5.6.2 and 5.6.3: a change beyond 2,83 times Table 1 calls for recalibration.
_DRIFT_FACTOR = 2.83
#: 5.4: range and step of the spectrum from 100 Hz to 10 000 Hz, and over a
#: range extended beyond it.
_CORE_RANGE_DB = 12.0
_CORE_STEP_DB = 3.0
_EXTENDED_RANGE_DB = 16.0
_EXTENDED_STEP_DB = 4.0
#: 5.5: the highest directivity index from 100 Hz to 10 000 Hz.
_MAX_DIRECTIVITY_DB = 6.0
#: 5.2: over the declared range of the supply, no one-third octave band varies
#: by more than +-0,3 dB.
_SUPPLY_VARIATION_DB = 0.3
#: 8.3.3 and 9.3.2: three repeated sound power levels or five sound pressure
#: levels.
_REPETITIONS = (3, 5)
#: Table B.1: tolerance on the difference between the pressure and intensity
#: sound power levels, dB, for 50 Hz to 80 Hz and 100 Hz to 315 Hz.
_TABLE_B1_DB = ((_K_80, 4.0), (_K_315, 1.0))
#: Formula (1) divides by N - 1, so two repetitions are the fewest it reads.
_MIN_REPETITIONS = 2
#: A level grid is (positions or repetitions, bands).
_GRID_RANK = 2
#: 11.2: the expanded uncertainty is +-1,96 sigma_R for 95 % coverage.
_COVERAGE_FACTOR = 1.96

#: Table 2, one-third octave rows: sigma_R in dB for the hemi-anechoic room
#: with meridional or spiral paths, with 20 discrete positions or coaxial
#: circular paths, and for the reverberation test room. Rows end at 80 Hz,
#: 160 Hz, 3 150 Hz, 10 000 Hz and 20 000 Hz.
_TABLE_2_THIRDS = (
    (_K_80, (2.0, 2.0, 2.5)),
    (_K_160, (0.8, 0.8, 1.0)),
    (_K_3150, (0.3, 0.5, 0.3)),
    (_K_10000, (0.3, 1.0, 0.3)),
    (_K_20000, (0.3, 1.0, 0.4)),
)
#: Table 2, octave rows: 63 Hz, 125 Hz, 250 Hz to 2 000 Hz, 4 000 Hz to
#: 8 000 Hz, 16 000 Hz (octave indices in one-third octave steps).
_TABLE_2_OCTAVES = (
    (-12, (2.0, 2.0, 2.5)),
    (-9, (0.8, 0.8, 1.0)),
    (3, (0.3, 0.5, 0.3)),
    (9, (0.3, 1.0, 0.3)),
    (12, (0.3, 1.0, 0.4)),
)
#: Table 2, A-weighted row.
_TABLE_2_A = (0.3, 0.5, 0.2)
#: Octave mid-band frequencies fall on every third one-third octave band
#: counted from 1 kHz.
_OCTAVE_STEP = 3


def _column(environment: str, arrangement: str | None) -> int:
    if environment == "reverberation-room":
        return 2
    if environment != "hemi-anechoic":
        msg = (
            "'environment' must be 'hemi-anechoic' or 'reverberation-room'; "
            f"got {environment!r}."
        )
        raise ValueError(msg)
    if arrangement not in ("paths", "fixed"):
        msg = (
            "'arrangement' must be 'paths' (meridional or spiral) or 'fixed' "
            "(20 discrete positions or coaxial circular paths) in a hemi-anechoic "
            f"room; got {arrangement!r}."
        )
        raise ValueError(msg)
    return 0 if arrangement == "paths" else 1


def _stepped[T](k: int, rows: tuple[tuple[int, T], ...], low: int, what: str) -> T:
    if k < low or k > rows[-1][0]:
        msg = f"{_nominal(k):g} Hz lies outside the bands of {what}."
        raise ValueError(msg)
    for upper, value in rows[:-1]:
        if k <= upper:
            return value
    return rows[-1][1]


def repeatability_standard_deviation(levels_db: ArrayLike) -> np.ndarray:
    r"""Standard deviation under repeatability conditions (ISO 6926 Formula (1)).

    :math:`\sigma_r = \sqrt{\sum_j (L_{X,j} - \overline{L_X})^2 / (N - 1)}` with
    :math:`\overline{L_X}` the energy average of the repetitions, as clause
    8.4 defines it, not their arithmetic mean.

    :param levels_db: ``(N, bands)`` repeated levels (sound power or sound
        pressure), or ``(N,)`` for one band, in dB.
    :return: :math:`\sigma_r` per band, in dB.
    :raises ValueError: for fewer than two repetitions or non-finite levels.
    """
    levels = np.asarray(levels_db, dtype=np.float64)
    if levels.ndim == 1:
        levels = levels[:, np.newaxis]
    if levels.ndim != _GRID_RANK or levels.shape[0] < _MIN_REPETITIONS:
        msg = "'levels_db' must hold at least two repetitions, one row each."
        raise ValueError(msg)
    if not np.all(np.isfinite(levels)):
        msg = "'levels_db' must be finite."
        raise ValueError(msg)
    mean = energy_mean(levels, axis=0)
    n = levels.shape[0]
    return np.asarray(
        np.sqrt(np.sum((levels - mean[np.newaxis, :]) ** 2, axis=0) / (n - 1)),
        dtype=np.float64,
    )


def knee_frequency(d0_m: float, *, speed_of_sound: float = 343.0) -> float:
    r"""Knee frequency of the radiation efficiency (ISO 6926 Formula (A.1)).

    :math:`f_\mathrm{k} = c / (2 \pi d_0)`: the frequency at which the
    radiation efficiency has dropped 3 dB from its high-frequency value.
    ISO 6926:2016 describes :math:`d_0` as "half the characteristic source
    dimension (see ISO 3745)", while ISO 3745:2012 3.14 defines the
    characteristic source dimension, with the same symbol, as the distance
    from the origin to the farthest corner of the reference box, already a
    half dimension (see docs/ERRATA.md). The value passed here is the
    :math:`d_0` that enters the formula, a radius-like length; the choice of
    which length that is stays with the caller.

    :param d0_m: :math:`d_0`, in metres.
    :param speed_of_sound: Speed of sound, in m/s (default 343).
    :return: :math:`f_\mathrm{k}`, in hertz.
    """
    d0 = require_positive(d0_m, "d0_m")
    c = require_positive(speed_of_sound, "speed_of_sound")
    return c / (2.0 * math.pi * d0)


def radiation_impedance_correction(
    *,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = _PS0,
    radiation: RadiationCharacter = "unknown",
    frequencies_hz: ArrayLike | None = None,
    knee_frequency_hz: float | None = None,
) -> np.ndarray:
    r"""The radiation impedance correction :math:`C_2` of ISO 6926 Annex A.

    :math:`C_2 = -10 \lg(p_\mathrm{s}/p_{\mathrm{s},0}) + n \lg(\theta/
    \theta_1)`, :math:`\theta_1` = 296 K and :math:`\theta` the air temperature
    in kelvin, with :math:`n` = 7,5 for a source whose radiation is unknown
    (A.5), 15 below and 5 at or above the knee frequency for a monopole
    (A.2, A.3), and 25 at or above it for an aerodynamic dipole (A.4). Annex A
    is informative: 8.4 prefers the manufacturer's value, and the formula the
    calibration used should be the one the user applies.

    :param temperature_c: Air temperature at the test, in degrees Celsius.
    :param static_pressure_kpa: Static pressure at the test, in kilopascals.
    :param radiation: ``"unknown"`` (default), ``"monopole"`` or ``"dipole"``.
    :param frequencies_hz: The band frequencies, in hertz; required for a
        monopole or a dipole, whose correction depends on the knee frequency.
    :param knee_frequency_hz: :math:`f_\mathrm{k}` (see
        :func:`knee_frequency`), required for a monopole or a dipole.
    :return: :math:`C_2` per band, in dB (one value without frequencies).
    :raises ValueError: for an unknown radiation character, a monopole or
        dipole without frequencies and knee frequency, or a dipole band below
        the knee frequency, for which Annex A gives no formula.
    """
    _validate_meteorology(temperature_c, static_pressure_kpa)
    theta = temperature_c + _KELVIN_OFFSET
    pressure_term = -10.0 * math.log10(static_pressure_kpa / _PS0)
    ratio = math.log10(theta / _THETA1)
    if radiation == "unknown":
        count = (
            1
            if frequencies_hz is None
            else np.atleast_1d(np.asarray(frequencies_hz)).size
        )
        return np.full(count, pressure_term + _C2_UNKNOWN * ratio, dtype=np.float64)
    if radiation not in ("monopole", "dipole"):
        msg = (
            f"'radiation' must be 'unknown', 'monopole' or 'dipole'; got {radiation!r}."
        )
        raise ValueError(msg)
    if frequencies_hz is None or knee_frequency_hz is None:
        msg = (
            f"a {radiation} needs 'frequencies_hz' and 'knee_frequency_hz': "
            "Annex A switches formula at the knee frequency."
        )
        raise ValueError(msg)
    freqs = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
    knee = require_positive(knee_frequency_hz, "knee_frequency_hz")
    above = freqs >= knee
    if radiation == "dipole":
        if not np.all(above):
            msg = (
                "Annex A gives C2 for an aerodynamic dipole only at or above the "
                "knee frequency (Formula (A.4)); a band lies below it."
            )
            raise ValueError(msg)
        return np.full(freqs.size, pressure_term + _C2_DIPOLE * ratio)
    n = np.where(above, _C2_MONOPOLE_HIGH, _C2_MONOPOLE_LOW)
    return np.asarray(pressure_term + n * ratio, dtype=np.float64)


def reference_source_reproducibility_db(
    frequencies_hz: ArrayLike,
    *,
    environment: CalibrationEnvironment,
    arrangement: MicrophoneArrangement | None = None,
    bandwidth: BandWidth = "one-third-octave",
) -> np.ndarray:
    r"""Standard deviation of reproducibility of a calibration (ISO 6926 Table 2).

    The one-third octave and octave columns of Table 2 are read separately,
    as printed: the 3 150 Hz one-third octave band sits in the 200 Hz to
    3 150 Hz row while the 4 000 Hz octave row begins at 4 000 Hz.

    :param frequencies_hz: Nominal mid-band frequencies, in hertz.
    :param environment: ``"hemi-anechoic"`` or ``"reverberation-room"``.
    :param arrangement: In a hemi-anechoic room, ``"paths"`` (meridional or
        spiral) or ``"fixed"`` (20 discrete positions or coaxial circular
        paths); ignored in a reverberation room.
    :param bandwidth: ``"one-third-octave"`` (default) or ``"octave"``.
    :return: :math:`\sigma_R` per band, in dB.
    :raises ValueError: for a band outside Table 2 or an unknown option.
    """
    column = _column(environment, arrangement)
    freqs = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
    if bandwidth == "one-third-octave":
        rows, low = _TABLE_2_THIRDS, _K_50
    elif bandwidth == "octave":
        rows, low = _TABLE_2_OCTAVES, -12
    else:
        msg = f"'bandwidth' must be 'one-third-octave' or 'octave'; got {bandwidth!r}."
        raise ValueError(msg)
    values = []
    for f in freqs:
        k = _band_index(float(f))
        if bandwidth == "octave" and k % _OCTAVE_STEP != 0:
            msg = f"{float(f):g} Hz is not an octave mid-band frequency."
            raise ValueError(msg)
        values.append(_stepped(k, rows, low, "ISO 6926 Table 2")[column])
    return np.array(values, dtype=np.float64)


def _repeatability_limit(k: int) -> float:
    return float(_stepped(k, _TABLE_1_DB, _K_50, "ISO 6926 Table 1"))


@dataclass(frozen=True)
class CalibrationConditions:
    r"""The air of a calibration on the 2 m hemisphere (ISO 6926 8.4).

    The three travel together because Formula (2) reads them from the same
    air: :math:`C_1` and the Annex A :math:`C_2` read its temperature and its
    static pressure, and :math:`C_3` reads the attenuation coefficient
    :math:`a(f)` that ISO 9613-1 gives for it. The defaults are the reference
    meteorological conditions of clause 4, 23,0 degC and 101,325 kPa, with no
    air absorption.

    :param temperature_c: Air temperature during the calibration, in degrees
        Celsius.
    :param static_pressure_kpa: Static pressure during the calibration, in
        kilopascals.
    :param air_absorption_db_per_m: :math:`a(f)` of ISO 9613-1 per band, or
        one value for every band, in dB/m, for :math:`C_3`; ``None`` leaves
        :math:`C_3 = 0`. It is held as a float64 copy.
    :raises ValueError: for a temperature that is not finite or not above
        absolute zero, a static pressure that is not finite and positive, or
        an air absorption that is not finite and non-negative.
    """

    _: KW_ONLY
    temperature_c: float = 23.0
    static_pressure_kpa: float = _PS0
    air_absorption_db_per_m: ArrayLike | None = None

    def __post_init__(self) -> None:
        """Refuse the conditions Formula (2) cannot read."""
        _validate_meteorology(self.temperature_c, self.static_pressure_kpa)
        if self.air_absorption_db_per_m is None:
            return
        absorption = np.array(self.air_absorption_db_per_m, dtype=np.float64)
        if not np.all(np.isfinite(absorption)) or np.any(absorption < 0.0):
            msg = "'air_absorption_db_per_m' must be finite and non-negative."
            raise ValueError(msg)
        object.__setattr__(self, "air_absorption_db_per_m", absorption)


@dataclass(frozen=True)
class ReferenceSourceCalibration:
    r"""Calibrated sound power levels of a reference sound source (ISO 6926 8.4).

    :ivar frequencies_hz: Nominal one-third octave mid-band frequencies, in
        hertz, ascending.
    :ivar sound_power_level_db: :math:`L_W` under the reference meteorological
        conditions, per band, in dB re 1 pW; the 50 Hz to 80 Hz bands come
        from sound intensity where Annex B validated them.
    :ivar surface_pressure_level_db: :math:`\overline{L_p}` over the 2 m
        hemisphere after the background correction, per band.
    :ivar directivity_index_db: :math:`D_{\mathrm{I}i}` per position or
        traverse and band (3.9), ``(positions, bands)``.
    :ivar c1_db: :math:`C_1`, in dB.
    :ivar c2_db: :math:`C_2` per band, in dB.
    :ivar c3_db: :math:`C_3` per band, in dB.
    :ivar expanded_uncertainty_db: :math:`k \sigma_R` of Table 2 per band.
    :ivar coverage_factor: :math:`k`.
    :ivar arrangement: ``"paths"`` or ``"fixed"``.
    :ivar intensity_bands: Per band, whether the level came from the sound
        intensity of Annex B.
    :ivar intensity_agreement: Whether the pressure and intensity levels
        agree within Table B.1 from 50 Hz to 315 Hz, or ``None`` without
        intensity levels.
    :ivar room_qualified: Whether the room qualification given meets 8.1 for
        these bands at 2 m, or ``None`` when none was given.
    :ivar radiation: The radiation character whose Annex A :math:`C_2` the
        calibration used, or ``None`` when it used the manufacturer's value.
    :ivar knee_frequency_hz: The knee frequency of that :math:`C_2`, or
        ``None``.
    """

    frequencies_hz: np.ndarray
    sound_power_level_db: np.ndarray
    surface_pressure_level_db: np.ndarray
    directivity_index_db: np.ndarray
    c1_db: float
    c2_db: np.ndarray
    c3_db: np.ndarray
    expanded_uncertainty_db: np.ndarray
    coverage_factor: float
    arrangement: str
    intensity_bands: np.ndarray
    intensity_agreement: bool | None
    room_qualified: bool | None
    radiation: str | None
    knee_frequency_hz: float | None

    @property
    def maximum_directivity_index_db(self) -> np.ndarray:
        """The highest directivity index over the positions, per band (5.5).

        :return: One value per band, in dB.
        """
        return np.asarray(np.max(self.directivity_index_db, axis=0), dtype=np.float64)

    @property
    def a_weighted_expanded_uncertainty_db(self) -> float:
        r"""The expanded uncertainty of :attr:`sound_power_level_a_db` (Table 2).

        :return: :math:`k \sigma_R` of the A-weighted row, in dB.
        """
        return (
            self.coverage_factor
            * _TABLE_2_A[_column("hemi-anechoic", self.arrangement)]
        )

    @property
    def a_weighted_range_hz(self) -> tuple[float, float]:
        """The bands the A-weighted total covers: those of ISO 3744 Annex E.

        :return: ``(lowest, highest)`` nominal frequency, in hertz.
        """
        inside = self._a_weighted_bands()
        return float(self.frequencies_hz[inside][0]), float(
            self.frequencies_hz[inside][-1]
        )

    @property
    def sound_power_level_a_db(self) -> float:
        """A-weighted sound power level over :attr:`a_weighted_range_hz` (5.3).

        :return: :math:`L_{WA}`, in dB re 1 pW.
        """
        inside = self._a_weighted_bands()
        freqs = self.frequencies_hz[inside]
        return float(
            energy_sum(
                self.sound_power_level_db[inside] + _a_weighting_corrections(freqs)
            )
        )

    def _a_weighted_bands(self) -> np.ndarray:
        ks = np.array([_band_index(float(f)) for f in self.frequencies_hz])
        inside = (ks >= _K_50) & (ks <= _K_10000)
        if not np.any(inside):
            msg = "no band lies within the 50 Hz to 10 kHz of ISO 3744 Annex E."
            raise ValueError(msg)
        return inside

    def sound_power_level_at(
        self,
        frequencies_hz: ArrayLike,
        *,
        bandwidth: BandWidth = "one-third-octave",
        temperature_c: float | None = None,
        static_pressure_kpa: float | None = None,
    ) -> np.ndarray:
        r"""The calibrated level in the bands a comparison method asks for.

        Without meteorological conditions, :math:`L_W` under the reference
        conditions, as calibrated. With the temperature and the static
        pressure of a test, the power the source radiates there,
        :math:`L_W - C_2`, with :math:`C_2` evaluated at the test by the Annex A
        formula the calibration used (8.4: the formula of the calibration
        laboratory "should be the same as the one used by the user"); ISO 3741
        Formulae (21) and (31) ask for that level. An octave band is the energy
        sum of its three one-third octave bands, all of which must have been
        calibrated.

        :param frequencies_hz: Nominal mid-band frequencies, in hertz.
        :param bandwidth: ``"one-third-octave"`` (default) or ``"octave"``.
        :param temperature_c: Air temperature at the test, in degrees Celsius;
            ``None`` (default), with ``static_pressure_kpa``, reads the
            reference conditions.
        :param static_pressure_kpa: Static pressure at the test, in
            kilopascals, given together with ``temperature_c``.
        :return: The level per requested band, in dB re 1 pW.
        :raises ValueError: for a band the calibration does not cover, an
            octave asked at a frequency that is not an octave mid-band, only
            one of the two conditions, or conditions asked of a calibration
            that used the manufacturer's :math:`C_2`, whose value at the test
            only the manufacturer gives.
        """
        levels = np.asarray(self.sound_power_level_db, dtype=np.float64)
        if (temperature_c is None) != (static_pressure_kpa is None):
            msg = (
                "give 'temperature_c' and 'static_pressure_kpa' together, or "
                "neither for the reference conditions."
            )
            raise ValueError(msg)
        if temperature_c is not None and static_pressure_kpa is not None:
            if self.radiation is None:
                msg = (
                    "the calibration used the manufacturer's C2 ('c2_db'), whose "
                    "value at the test only the manufacturer gives (ISO 6926:2016, "
                    "8.4); subtract it from the calibrated levels and pass those."
                )
                raise ValueError(msg)
            levels = levels - radiation_impedance_correction(
                temperature_c=temperature_c,
                static_pressure_kpa=static_pressure_kpa,
                radiation=cast("RadiationCharacter", self.radiation),
                frequencies_hz=self.frequencies_hz,
                knee_frequency_hz=self.knee_frequency_hz,
            )
        known = {
            _band_index(float(f)): float(level)
            for f, level in zip(self.frequencies_hz, levels, strict=True)
        }
        out = []
        for f in np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64)):
            k = _band_index(float(f))
            if bandwidth == "one-third-octave":
                wanted = [k]
            elif bandwidth == "octave":
                if k % _OCTAVE_STEP != 0:
                    msg = f"{float(f):g} Hz is not an octave mid-band frequency."
                    raise ValueError(msg)
                wanted = [k - 1, k, k + 1]
            else:
                msg = (
                    "'bandwidth' must be 'one-third-octave' or 'octave'; "
                    f"got {bandwidth!r}."
                )
                raise ValueError(msg)
            missing = [w for w in wanted if w not in known]
            if missing:
                msg = (
                    f"the calibration does not cover the {_nominal(missing[0]):g} Hz "
                    f"one-third octave band needed for {float(f):g} Hz."
                )
                raise ValueError(msg)
            out.append(energy_sum([known[w] for w in wanted]))
        return np.array(out, dtype=np.float64)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the calibrated spectrum with its expanded uncertainty.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the level bars.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.free_field import plot_reference_source_calibration

        check_language(language)
        return plot_reference_source_calibration(
            self, ax=ax, language=language, **kwargs
        )


def _room_qualified(check: FreeFieldCheck, freqs: np.ndarray) -> bool:
    """8.1: hemi-anechoic, qualified over the pressure-calibrated bands out to 2 m.

    ``freqs`` are the bands whose level came from sound pressure: the bands
    Annex B replaced by sound intensity are the ones clause 10 lets a room
    not qualified at the lowest frequencies calibrate, so they are left out.
    """
    if check.room != "hemi-anechoic" or freqs.size == 0:
        return False
    if check.passes:
        low, high = float(check.frequencies_hz[0]), float(check.frequencies_hz[-1])
        radius = check.maximum_qualified_radius_m
    elif check.conforming_range_hz is not None and not check.not_judged:
        low, high = check.conforming_range_hz
        radius = check.conforming_radius_m
    else:
        return False
    within = bool(
        _band_index(float(freqs[0])) >= _band_index(low)
        and _band_index(float(freqs[-1])) <= _band_index(high)
    )
    return within and radius >= _RADIUS_M


def _annex_b(
    ks: np.ndarray, pressure: np.ndarray, intensity: np.ndarray
) -> tuple[np.ndarray, bool]:
    """Annex B: agreement from 50 Hz to 315 Hz and the bands it replaces."""
    compared = (ks >= _K_50) & (ks <= _K_315)
    if not np.any(compared):
        msg = "'intensity_sound_power_level_db' needs bands from 50 Hz to 315 Hz."
        raise ValueError(msg)
    agree = True
    for k, p, i in zip(
        ks[compared], pressure[compared], intensity[compared], strict=True
    ):
        if not math.isfinite(float(i)):
            msg = (
                "'intensity_sound_power_level_db' must be finite from 50 Hz to 315 Hz."
            )
            raise ValueError(msg)
        tolerance = float(_stepped(int(k), _TABLE_B1_DB, _K_50, "ISO 6926 Table B.1"))
        agree &= abs(float(i) - float(p)) <= tolerance + 1e-9
    replaced = (ks >= _K_50) & (ks <= _K_80) if agree else np.zeros(ks.size, dtype=bool)
    return replaced, agree


def _calibration_bands(frequencies_hz: ArrayLike) -> tuple[np.ndarray, np.ndarray]:
    """Ascending one-third octave mid-bands from 50 Hz to 20 kHz, and their indices."""
    freqs = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
    if freqs.ndim != 1 or freqs.size == 0:
        msg = "'frequencies_hz' must be a non-empty 1-D array of mid-band frequencies."
        raise ValueError(msg)
    ks = np.array([_band_index(float(f)) for f in freqs], dtype=np.int64)
    if np.any(np.diff(ks) <= 0) or ks[0] < _K_50 or ks[-1] > _K_20000:
        msg = (
            "'frequencies_hz' must be ascending one-third octave mid-bands from "
            "50 Hz to 20 kHz."
        )
        raise ValueError(msg)
    return freqs, ks


def _hemisphere_levels(
    levels_db: ArrayLike,
    freqs: np.ndarray,
    background_levels_db: ArrayLike | None,
    maximum_levels_db: ArrayLike | None,
) -> PrecisionSoundPowerResult:
    """The surface level over the 2 m hemisphere, refusing levels that are not finite.

    ISO 6926 8.3.1 measures "in accordance with ISO 3745", so the background
    criterion of ISO 3745 9.4.2 and its advisory come with the surface level.
    """
    levels = np.asarray(levels_db, dtype=np.float64)
    if levels.size == 0 or not np.all(np.isfinite(levels)):
        msg = "'levels_db' must hold the finite levels of at least one position."
        raise ValueError(msg)
    for name, extra in (
        ("background_levels_db", background_levels_db),
        ("maximum_levels_db", maximum_levels_db),
    ):
        if extra is not None and not np.all(
            np.isfinite(np.asarray(extra, dtype=np.float64))
        ):
            msg = f"'{name}' must be finite."
            raise ValueError(msg)
    if background_levels_db is None:
        return sound_power_anechoic(
            levels, "hemisphere", radius=_RADIUS_M, frequencies=freqs
        )
    return sound_power_anechoic(
        levels,
        "hemisphere",
        radius=_RADIUS_M,
        background_levels=np.asarray(background_levels_db, dtype=np.float64),
        frequencies=freqs,
    )


def _c3_correction(
    air_absorption_db_per_m: ArrayLike | None, freqs: np.ndarray
) -> np.ndarray:
    """:math:`C_3` of 8.4 over the 2 m path, zero without an air absorption.

    :class:`CalibrationConditions` has already refused an absorption that is
    not finite and non-negative.
    """
    if air_absorption_db_per_m is None:
        return np.zeros(freqs.size)
    a0 = (
        np.broadcast_to(
            np.asarray(air_absorption_db_per_m, dtype=np.float64), freqs.shape
        )
        * _RADIUS_M
    )
    return np.asarray(a0 * (1.0053 - 0.0012 * a0) ** 1.6, dtype=np.float64)


def _with_annex_b(
    lw: np.ndarray, ks: np.ndarray, intensity_sound_power_level_db: ArrayLike | None
) -> tuple[np.ndarray, np.ndarray, bool | None]:
    """The levels with Annex B applied, the bands it replaced and the agreement.

    :return: :math:`L_W` per band, the bands taken from sound intensity, and
        whether the two methods agree within Table B.1 (``None`` without
        intensity levels).
    """
    if intensity_sound_power_level_db is None:
        return lw, np.zeros(ks.size, dtype=bool), None
    intensity = np.asarray(intensity_sound_power_level_db, dtype=np.float64)
    if intensity.shape != ks.shape:
        msg = "'intensity_sound_power_level_db' needs one value per band."
        raise ValueError(msg)
    intensity_bands, agreement = _annex_b(ks, lw, intensity)
    return np.where(intensity_bands, intensity, lw), intensity_bands, agreement


def _calibration_directivity(
    precision: PrecisionSoundPowerResult, maximum_levels_db: ArrayLike | None
) -> np.ndarray:
    """The directivity index of each position, from the traverse maxima if given (8.3.2)."""
    if maximum_levels_db is None:
        return precision.directivity_index
    maxima = np.asarray(maximum_levels_db, dtype=np.float64)
    if maxima.shape != precision.directivity_index.shape:
        msg = "'maximum_levels_db' must have the shape of 'levels_db'."
        raise ValueError(msg)
    return np.asarray(
        maxima - precision.surface_pressure_level[np.newaxis, :], dtype=np.float64
    )


def _calibration_room_qualified(
    room_qualification: FreeFieldCheck | None, freqs: np.ndarray
) -> bool | None:
    """Whether the room qualification covers ``freqs`` at 2 m (8.1), with a warning if not."""
    if room_qualification is None:
        return None
    qualified = _room_qualified(room_qualification, freqs)
    if not qualified:
        warnings.warn(
            "The room qualification does not cover these bands at 2 m in a "
            "hemi-anechoic room (ISO 6926:2016, 8.1).",
            SoundPowerWarning,
            stacklevel=3,
        )
    return qualified


def reference_source_calibration(
    levels_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    arrangement: MicrophoneArrangement,
    background_levels_db: ArrayLike | None = None,
    maximum_levels_db: ArrayLike | None = None,
    conditions: CalibrationConditions | None = None,
    radiation: RadiationCharacter = "unknown",
    knee_frequency_hz: float | None = None,
    c2_db: ArrayLike | None = None,
    intensity_sound_power_level_db: ArrayLike | None = None,
    room_qualification: FreeFieldCheck | None = None,
    coverage_factor: float = _COVERAGE_FACTOR,
) -> ReferenceSourceCalibration:
    r"""Calibrate a reference sound source in a hemi-anechoic room (ISO 6926 clause 8).

    The one-third octave band levels over the 2 m hemisphere are corrected
    for background position by position and energy-averaged as ISO 3745
    prescribes (:func:`~phonometry.emission.sound_power_anechoic`), then
    Formula (2) carries them to the sound power level under the reference
    meteorological conditions with the :math:`C_1`, :math:`C_2` and
    :math:`C_3` of 8.4. The directivity index of each position (3.9) is its
    level less the surface level; for traversing microphones 8.3.2 takes the
    highest level seen on the traverse instead, which ``maximum_levels_db``
    carries. Annex B, the alternative at low frequencies, replaces the 50 Hz
    to 80 Hz bands by the intensity levels when both agree within Table B.1
    from 50 Hz to 315 Hz. B.2 asks for the directivity index of those three
    bands from the intensity measurements too; the result keeps the one
    from sound pressure, and :attr:`ReferenceSourceCalibration.intensity_bands`
    marks the bands whose level was replaced, as B.2 asks the report to.

    :param levels_db: ``(positions, bands)`` time-averaged levels at the fixed
        positions or along the traverses of 8.2, in dB.
    :param frequencies_hz: Nominal one-third octave mid-band frequencies, in
        hertz, ascending, from 50 Hz to 20 kHz.
    :param arrangement: ``"paths"`` (meridional or spiral paths) or
        ``"fixed"`` (the 20 fixed positions or coaxial circular paths), which
        selects the column of Table 2.
    :param background_levels_db: Background levels, per position or one
        spectrum, for the ISO 3745 correction; ``None`` applies none.
    :param maximum_levels_db: For traverses, the highest level recorded on
        each (8.3.2), same shape as ``levels_db``.
    :param conditions: The :class:`CalibrationConditions` of the air during
        the calibration, whose temperature and static pressure enter
        :math:`C_1` and the Annex A :math:`C_2` and whose :math:`a(f)` enters
        :math:`C_3`; ``None`` (default) takes the reference meteorological
        conditions of clause 4 with no air absorption.
    :param radiation: Radiation character for the Annex A :math:`C_2`.
    :param knee_frequency_hz: Knee frequency for a monopole or a dipole.
    :param c2_db: The manufacturer's :math:`C_2`, scalar or per band, which
        8.4 prefers to Annex A; overrides ``radiation``. A calibration made
        with it cannot be read at the conditions of a test, since only the
        manufacturer gives :math:`C_2` there (see
        :meth:`ReferenceSourceCalibration.sound_power_level_at`).
    :param intensity_sound_power_level_db: Sound power levels from sound
        intensity per band (ISO 9614-3, Annex B), ``nan`` outside 50 Hz to
        315 Hz; ``None`` applies no Annex B.
    :param room_qualification: The :func:`~phonometry.emission.check_free_field`
        verdict of the room; 8.1 asks for a hemi-anechoic room qualified over
        the frequency range of interest, here the bands calibrated from sound
        pressure at 2 m (the bands Annex B takes from sound intensity are the
        ones clause 10 lets an unqualified room calibrate, and are left out).
    :param coverage_factor: :math:`k` of the expanded uncertainty (1,96 in
        11.2 for 95 %).
    :return: :class:`ReferenceSourceCalibration`.
    :raises ValueError: for bands that are not ascending one-third octaves
        from 50 Hz to 20 kHz, no position, levels, background levels, maxima
        or a manufacturer's :math:`C_2` that are not finite, or inconsistent
        shapes.
    """
    freqs, ks = _calibration_bands(frequencies_hz)
    _column("hemi-anechoic", arrangement)
    air = CalibrationConditions() if conditions is None else conditions
    k = require_positive(coverage_factor, "coverage_factor")
    precision = _hemisphere_levels(
        levels_db, freqs, background_levels_db, maximum_levels_db
    )
    lp_bar = precision.surface_pressure_level
    area = 2.0 * math.pi * _RADIUS_M**2
    c1 = _c1_correction(air.temperature_c, air.static_pressure_kpa)
    if c2_db is not None:
        c2 = np.broadcast_to(np.asarray(c2_db, dtype=np.float64), freqs.shape).copy()
        if not np.all(np.isfinite(c2)):
            msg = "'c2_db' must be finite, one value or one per band."
            raise ValueError(msg)
    else:
        c2 = radiation_impedance_correction(
            temperature_c=air.temperature_c,
            static_pressure_kpa=air.static_pressure_kpa,
            radiation=radiation,
            frequencies_hz=freqs,
            knee_frequency_hz=knee_frequency_hz,
        )
    c3 = _c3_correction(air.air_absorption_db_per_m, freqs)
    lw, intensity_bands, agreement = _with_annex_b(
        lp_bar + 10.0 * math.log10(area / _S0) + c1 + c2 + c3,
        ks,
        intensity_sound_power_level_db,
    )
    directivity = _calibration_directivity(precision, maximum_levels_db)
    qualified = _calibration_room_qualified(room_qualification, freqs[~intensity_bands])
    uncertainty = k * reference_source_reproducibility_db(
        freqs, environment="hemi-anechoic", arrangement=arrangement
    )
    return ReferenceSourceCalibration(
        frequencies_hz=freqs,
        sound_power_level_db=np.asarray(lw, dtype=np.float64),
        surface_pressure_level_db=np.asarray(lp_bar, dtype=np.float64),
        directivity_index_db=np.asarray(directivity, dtype=np.float64),
        c1_db=float(c1),
        c2_db=np.asarray(c2, dtype=np.float64),
        c3_db=np.asarray(c3, dtype=np.float64),
        expanded_uncertainty_db=np.asarray(uncertainty, dtype=np.float64),
        coverage_factor=k,
        arrangement=arrangement,
        intensity_bands=intensity_bands,
        intensity_agreement=agreement,
        room_qualified=qualified,
        radiation=None if c2_db is not None else radiation,
        knee_frequency_hz=(
            None
            if c2_db is not None or knee_frequency_hz is None
            else float(knee_frequency_hz)
        ),
    )


@dataclass(frozen=True)
class ReferenceSoundSourceVerdict:
    r"""Whether a source meets the performance requirements of ISO 6926 clause 5.

    :ivar frequencies_hz: The one-third octave bands, ascending, in hertz.
    :ivar sound_power_level_db: The calibrated :math:`L_W` per band.
    :ivar repeatability_db: :math:`\sigma_r` of Formula (1) per band, or
        ``None`` when no repetitions were given.
    :ivar repeatability_limit_db: The Table 1 limit per band.
    :ivar supply_variation_db: The largest change of :math:`L_W` per band over
        the declared range of the electrical or mechanical supply (5.2), or
        ``None`` when not given.
    :ivar supply_limit_db: 0,3 dB either way (5.2).
    :ivar adjacent_step_db: The largest difference from a neighbouring band,
        per band (5.4).
    :ivar adjacent_limit_db: The step that band is held to: 3 dB from 100 Hz
        to 10 000 Hz, 4 dB where a neighbour lies in an extended range.
    :ivar core_range_db: The spread of :math:`L_W` from 100 Hz to 10 000 Hz.
    :ivar core_range_limit_db: 12 dB (5.4).
    :ivar extended_range_db: The spread over every band when the range is
        extended beyond 100 Hz to 10 000 Hz, else ``nan``.
    :ivar extended_range_limit_db: 16 dB (5.4).
    :ivar directivity_index_db: The highest directivity index per band, or
        ``None`` when not given.
    :ivar directivity_limit_db: +6 dB (5.5).
    :ivar reverberation_rooms_only: Whether the source is labelled "For use as
        a reference sound source in reverberation test rooms complying with
        ISO 3741", which lifts 5.5.
    :ivar frequency_range_met: Whether every band from 100 Hz to 10 000 Hz is
        present (5.4).
    :ivar not_judged: The requirements without data, by name.
    """

    frequencies_hz: np.ndarray
    sound_power_level_db: np.ndarray
    repeatability_db: np.ndarray | None
    repeatability_limit_db: np.ndarray
    supply_variation_db: np.ndarray | None
    supply_limit_db: float
    adjacent_step_db: np.ndarray
    adjacent_limit_db: np.ndarray
    core_range_db: float
    core_range_limit_db: float
    extended_range_db: float
    extended_range_limit_db: float
    directivity_index_db: np.ndarray | None
    directivity_limit_db: float
    reverberation_rooms_only: bool
    frequency_range_met: bool
    not_judged: tuple[str, ...]

    @property
    def stability_met(self) -> bool | None:
        r"""5.2: :math:`\sigma_r` within Table 1 in every band.

        :return: The verdict, or ``None`` when not judged.
        """
        if self.repeatability_db is None:
            return None
        return bool(np.all(self.repeatability_db <= self.repeatability_limit_db + 1e-9))

    @property
    def supply_met(self) -> bool | None:
        """5.2: no band moves by more than 0,3 dB over the declared supply range.

        :return: The verdict, or ``None`` when not judged.
        """
        if self.supply_variation_db is None:
            return None
        return bool(
            np.all(np.abs(self.supply_variation_db) <= self.supply_limit_db + 1e-9)
        )

    @property
    def spectrum_met(self) -> bool:
        """5.4: the 12 dB range and 3 dB steps, 16 dB and 4 dB when extended.

        :return: The verdict.
        """
        steps = bool(np.all(self.adjacent_step_db <= self.adjacent_limit_db + 1e-9))
        core = self.core_range_db <= self.core_range_limit_db + 1e-9
        extended = not math.isfinite(self.extended_range_db) or (
            self.extended_range_db <= self.extended_range_limit_db + 1e-9
        )
        return bool(self.frequency_range_met and steps and core and extended)

    @property
    def directivity_met(self) -> bool | None:
        """5.5: the directivity index at most +6 dB from 100 Hz to 10 000 Hz.

        :return: The verdict, ``True`` for a source labelled for reverberation
            rooms only, or ``None`` when not judged.
        """
        if self.reverberation_rooms_only:
            return True
        if self.directivity_index_db is None:
            return None
        ks = np.array([_band_index(float(f)) for f in self.frequencies_hz])
        core = (ks >= _K_100) & (ks <= _K_10000)
        return bool(
            np.all(self.directivity_index_db[core] <= self.directivity_limit_db + 1e-9)
        )

    @property
    def passes(self) -> bool:
        """Whether every requirement of clause 5 is judged and met (5.1).

        :return: ``True`` when the source may be declared in compliance.
        """
        return bool(
            not self.not_judged
            and self.stability_met
            and self.supply_met
            and self.spectrum_met
            and self.directivity_met
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a ReferenceSoundSourceVerdict has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw each requirement as a share of its limit, per band.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the step curve.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.free_field import plot_reference_sound_source

        check_language(language)
        return plot_reference_sound_source(self, ax=ax, language=language, **kwargs)


def _spectrum_steps(ks: np.ndarray, lw: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Largest step to a neighbour and the limit it is held to, per band."""
    n = ks.size
    step = np.zeros(n)
    limit = np.full(n, _CORE_STEP_DB)
    for i in range(n - 1):
        both_core = bool(
            _K_100 <= ks[i] <= _K_10000 and _K_100 <= ks[i + 1] <= _K_10000
        )
        pair_limit = _CORE_STEP_DB if both_core else _EXTENDED_STEP_DB
        diff = abs(float(lw[i + 1] - lw[i]))
        for j in (i, i + 1):
            if diff / pair_limit > step[j] / limit[j]:
                step[j], limit[j] = diff, pair_limit
    return step, limit


def _clause5_levels(
    calibration: ReferenceSourceCalibration | ArrayLike,
    frequencies_hz: ArrayLike | None,
    directivity_index_db: ArrayLike | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    """The bands, levels and directivity a clause 5 verdict reads.

    A calibration brings its bands and its directivity; plain levels need
    their bands.
    """
    fallback: np.ndarray | None
    if isinstance(calibration, ReferenceSourceCalibration):
        if frequencies_hz is not None:
            msg = "a calibration brings its own bands; omit 'frequencies_hz'."
            raise ValueError(msg)
        freqs = calibration.frequencies_hz
        lw = calibration.sound_power_level_db
        fallback = calibration.maximum_directivity_index_db
    else:
        if frequencies_hz is None:
            msg = "'frequencies_hz' is required with a plain level array."
            raise ValueError(msg)
        freqs = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
        lw = np.atleast_1d(np.asarray(calibration, dtype=np.float64))
        fallback = None
    directivity = (
        fallback
        if directivity_index_db is None
        else np.asarray(directivity_index_db, dtype=np.float64)
    )
    return freqs, lw, directivity


def _highest_directivity(
    directivity: np.ndarray | None, freqs: np.ndarray
) -> np.ndarray | None:
    """The highest directivity index per band, from one row per position or one row."""
    if directivity is None:
        return None
    if directivity.ndim == _GRID_RANK:
        directivity = directivity.max(axis=0)
    if directivity.shape != freqs.shape:
        msg = "'directivity_index_db' must span the same bands."
        raise ValueError(msg)
    return directivity


def _repeatability_of(
    repeated_levels_db: ArrayLike | None, n_bands: int
) -> np.ndarray | None:
    r""":math:`\sigma_r` of Formula (1) from three or five repetitions, if given."""
    if repeated_levels_db is None:
        return None
    repeated = np.asarray(repeated_levels_db, dtype=np.float64)
    if repeated.ndim == 1:
        repeated = repeated[:, np.newaxis]
    if repeated.shape[0] not in _REPETITIONS or repeated.shape[1] != n_bands:
        msg = (
            "'repeated_levels_db' must be (3, bands) sound power levels or "
            "(5, bands) sound pressure levels (8.3.3)."
        )
        raise ValueError(msg)
    return repeatability_standard_deviation(repeated)


def _supply_variation_of(
    supply_variation_db: ArrayLike | None, freqs: np.ndarray
) -> np.ndarray | None:
    """The change over the declared supply range per band (5.2), if given."""
    if supply_variation_db is None:
        return None
    supply = np.asarray(supply_variation_db, dtype=np.float64).reshape(-1)
    if supply.size == 1:
        supply = np.full(freqs.shape, float(supply[0]))
    if supply.shape != freqs.shape or not np.all(np.isfinite(supply)):
        msg = "'supply_variation_db' must be finite, one value or one per band."
        raise ValueError(msg)
    return supply


def verify_reference_sound_source(
    calibration: ReferenceSourceCalibration | ArrayLike,
    *,
    frequencies_hz: ArrayLike | None = None,
    repeated_levels_db: ArrayLike | None = None,
    supply_variation_db: ArrayLike | None = None,
    directivity_index_db: ArrayLike | None = None,
    reverberation_rooms_only: bool = False,
) -> ReferenceSoundSourceVerdict:
    """May this source be declared a reference sound source? (ISO 6926 clause 5).

    Judges the temporal steadiness (5.2, Table 1), the variation over the
    declared range of the supply (5.2), the spectrum (5.4) and the directivity
    (5.5). A calibration made here brings its bands, levels and
    directivity indices; a source calibrated elsewhere, for instance in a
    reverberation room by clause 9, passes its one-third octave levels and
    frequencies.

    :param calibration: A :class:`ReferenceSourceCalibration`, or the
        calibrated :math:`L_W` per band, in dB re 1 pW.
    :param frequencies_hz: The bands of a plain level array, ascending
        one-third octave mid-bands, in hertz; omitted with a calibration.
    :param repeated_levels_db: ``(3, bands)`` sound power levels or
        ``(5, bands)`` sound pressure levels measured in succession (8.3.3,
        9.3.2); ``None`` leaves the steadiness of 5.2 unjudged.
    :param supply_variation_db: The largest change of the sound power level
        in each band over the declared range of the electrical or mechanical
        supply, the line voltage for instance (5.2), per band or one value for
        every band, in dB; ``None`` leaves that requirement unjudged.
    :param directivity_index_db: The directivity index per position and band,
        or the highest per band, for a plain level array (a calibration brings
        its own).
    :param reverberation_rooms_only: The source is labelled for reverberation
        test rooms complying with ISO 3741 only, and 5.5 does not apply.
    :return: :class:`ReferenceSoundSourceVerdict`.
    :raises ValueError: for bands that are not ascending contiguous one-third
        octaves, repetitions other than three or five, or shapes that do not
        match.
    """
    freqs, lw, directivity = _clause5_levels(
        calibration, frequencies_hz, directivity_index_db
    )
    if lw.shape != freqs.shape or not np.all(np.isfinite(lw)):
        msg = "the sound power levels must be finite, one per band."
        raise ValueError(msg)
    ks = np.array([_band_index(float(f)) for f in freqs], dtype=np.int64)
    if np.any(np.diff(ks) != 1):
        msg = "the bands must be contiguous one-third octaves, ascending."
        raise ValueError(msg)
    directivity = _highest_directivity(directivity, freqs)
    repeat = _repeatability_of(repeated_levels_db, freqs.size)
    supply = _supply_variation_of(supply_variation_db, freqs)
    limits = np.array([_repeatability_limit(int(k)) for k in ks], dtype=np.float64)
    core = (ks >= _K_100) & (ks <= _K_10000)
    range_met = bool(np.sum(core) == _K_10000 - _K_100 + 1)
    core_levels = lw[core]
    core_range = float(np.ptp(core_levels)) if core_levels.size else float("nan")
    extended_range = float(np.ptp(lw)) if bool(np.any(~core)) else float("nan")
    step, step_limit = _spectrum_steps(ks, lw)
    unjudged = (
        ("temporal steadiness", repeat is None),
        ("supply variation", supply is None),
        ("directivity", directivity is None and not reverberation_rooms_only),
    )
    not_judged = [name for name, missing in unjudged if missing]
    return ReferenceSoundSourceVerdict(
        frequencies_hz=freqs,
        sound_power_level_db=lw,
        repeatability_db=repeat,
        repeatability_limit_db=limits,
        supply_variation_db=supply,
        supply_limit_db=_SUPPLY_VARIATION_DB,
        adjacent_step_db=step,
        adjacent_limit_db=step_limit,
        core_range_db=core_range,
        core_range_limit_db=_CORE_RANGE_DB,
        extended_range_db=extended_range,
        extended_range_limit_db=_EXTENDED_RANGE_DB,
        directivity_index_db=directivity,
        directivity_limit_db=_MAX_DIRECTIVITY_DB,
        reverberation_rooms_only=reverberation_rooms_only,
        frequency_range_met=range_met,
        not_judged=tuple(not_judged),
    )


@dataclass(frozen=True)
class ReferenceSourceDriftResult:
    """Whether a reference sound source has drifted enough to be recalibrated.

    :ivar frequencies_hz: The one-third octave bands, in hertz.
    :ivar change_db: The latest level less the reference one, per band.
    :ivar limit_db: 2,83 times the Table 1 value of each band (5.6).
    """

    frequencies_hz: np.ndarray
    change_db: np.ndarray
    limit_db: np.ndarray

    @property
    def passes(self) -> bool:
        """Whether every band stays within 2,83 times Table 1.

        :return: ``True`` when no recalibration is called for.
        """
        return bool(np.all(np.abs(self.change_db) <= self.limit_db + 1e-9))

    @property
    def recalibration_required(self) -> bool:
        """5.6.3: a band moved by more than 2,83 times Table 1.

        :return: The opposite of :attr:`passes`.
        """
        return not self.passes

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a ReferenceSourceDriftResult has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Draw the change of each band against its limit.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the change bars.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.free_field import plot_reference_source_drift

        check_language(language)
        return plot_reference_source_drift(self, ax=ax, language=language, **kwargs)


def verify_reference_source_drift(
    reference_levels_db: ArrayLike,
    latest_levels_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
) -> ReferenceSourceDriftResult:
    """Has the source drifted beyond what ISO 6926 5.6 allows?

    The same check serves 5.6.2 (two calibrations), 5.6.3 (the regular
    one-third octave band levels at fixed reference points) and 5.6.4 (the
    surface levels of a source kept in one place): a change larger than 2,83
    times Table 1 in any band calls for recalibration.

    :param reference_levels_db: The levels of the earlier check, per band, in
        dB.
    :param latest_levels_db: The levels of the latest check, same bands.
    :param frequencies_hz: Nominal one-third octave mid-bands, 50 Hz to
        20 kHz, in hertz.
    :return: :class:`ReferenceSourceDriftResult`.
    :raises ValueError: for levels that do not span the bands or are not
        finite.
    """
    freqs = np.atleast_1d(np.asarray(frequencies_hz, dtype=np.float64))
    reference = np.atleast_1d(np.asarray(reference_levels_db, dtype=np.float64))
    latest = np.atleast_1d(np.asarray(latest_levels_db, dtype=np.float64))
    if reference.shape != freqs.shape or latest.shape != freqs.shape:
        msg = "both level arrays must hold one value per band."
        raise ValueError(msg)
    if not (np.all(np.isfinite(reference)) and np.all(np.isfinite(latest))):
        msg = "the levels must be finite."
        raise ValueError(msg)
    limit = _DRIFT_FACTOR * np.array(
        [_repeatability_limit(_band_index(float(f))) for f in freqs], dtype=np.float64
    )
    return ReferenceSourceDriftResult(
        frequencies_hz=freqs, change_db=latest - reference, limit_db=limit
    )


__all__ = [
    "CalibrationConditions",
    "ReferenceSoundSourceVerdict",
    "ReferenceSourceCalibration",
    "ReferenceSourceDriftResult",
    "knee_frequency",
    "radiation_impedance_correction",
    "reference_source_calibration",
    "reference_source_reproducibility_db",
    "repeatability_standard_deviation",
    "verify_reference_sound_source",
    "verify_reference_source_drift",
]
