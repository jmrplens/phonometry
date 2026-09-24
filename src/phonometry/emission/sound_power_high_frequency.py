#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Sound power levels in the 16 kHz octave band: ISO 9295:2015.

Some machines emit most of what matters above the range the general methods
cover: the paper noise of a fast printer, the whine of a switched-mode power
supply, the tone of a display. ISO 3741 stops at the 10 kHz one-third octave
band and ISO 3744 at the same place, so ISO 9295 adds the octave band centred
on 16 kHz, from 11,2 kHz to 22,4 kHz (clause 1), and determines the unweighted
sound power level in its three one-third octave bands (12,5, 16 and 20 kHz)
or in the narrow bands that hold its discrete tones.

Four methods are specified. Three of them use a reverberation test room with
a microphone on a rotating boom pointed away from the source (clauses 5.4 and
5.5), and one uses a hemi-anechoic room (clause 9).

**Mean level.** The time-averaged band level over the four orientations of
the equipment (:math:`N = 4`), or over three revolutions of the boom
(:math:`N = 3`), is the energy mean of Formula (1):

.. math::

   \overline{L_p} = 10 \lg\!\left[ \frac{1}{N} \sum_{i=1}^{N} 10^{0{,}1 L_i}
   \right] \mathrm{dB} \tag{1}

A moving microphone spreads a discrete tone over sidebands. The analyser has
to be at least as wide as Formula (2), with :math:`v` the speed of the
microphone and :math:`c` the speed of sound; with a narrower FFT the
sidebands are summed on an energy basis, Formula (3):

.. math::

   \Delta f = 2 f \frac{v}{c} \tag{2}

   L_\mathrm{tot} = 10 \lg \sum_{i=1}^{N_\mathrm{sb}} 10^{0{,}1 L_i}\ \mathrm{dB}
   \tag{3}

**Method with the measured reverberation time** (clause 6). Above 10 kHz the
room absorption coefficient cannot be taken as small, so the Eyring relation
gives it from the measured reverberation time :math:`T`, and the room constant
:math:`R` follows from it (:math:`S` the total room surface, :math:`V` its
volume):

.. math::

   R = \frac{S \, \alpha_\mathrm{room}}{1 - \alpha_\mathrm{room}} \tag{4}

   \alpha_\mathrm{room} = 1 - \mathrm{e}^{-0{,}16 \, V / (S T)} \tag{5}

The sound power level in each band is then Formula (6):

.. math::

   L_W = \overline{L_{p(\mathrm{ST})}} - 10 \lg\frac{4}{R}\ \mathrm{dB} \tag{6}

**Method with the calculated air absorption** (clause 7). At 10 kHz and
above practically all of the absorption of a reverberation room is in the
air, so the room constant comes from the air absorption coefficient
:math:`\alpha` in nepers per metre, Formula (7), and Formula (6) is applied
unchanged:

.. math::

   R = \frac{8 \alpha V}{1 - \dfrac{8 \alpha V}{S}} \tag{7}

:math:`\alpha` is Annex A (normative), which is ISO 9613-1 written in nepers
rather than decibels and evaluated up to 22,4 kHz, where ISO 9613-1 stops at
10 kHz; :func:`air_absorption_np_per_m` evaluates it with the library's
ISO 9613-1 implementation. Tables 1 and 2 print it for 18 °C to 27 °C, 40 %
to 60 % relative humidity and 10 000 Hz to 22 400 Hz.

**Method with a reference sound source** (clause 8). The source under test
and a calibrated reference source are measured in turn with the same
bandwidth. For broadband noise the band level is Formula (8); for discrete
tones the reference source is calibrated as a power spectral density, per
unit bandwidth, and the noise bandwidth :math:`\Delta F` of the constant
bandwidth analyser puts it back into the band, Formula (9):

.. math::

   L_W = L_{W(\mathrm{FAR})} - \overline{L_{p(\mathrm{FAR})}}
   + \overline{L_{p(\mathrm{ST})}} \tag{8}

   L_W = L_{W(\mathrm{FAR})} - \overline{L_{p(\mathrm{FAR})}}
   + \overline{L_{p(\mathrm{ST})}} + 10 \lg(\Delta F / 1\ \mathrm{Hz})\ \mathrm{dB}
   \tag{9}

**Method with a free field over a reflecting plane** (clause 9) is ISO 3744
(:func:`~phonometry.emission.sound_power.sound_power_pressure`) with the three
one-third octave bands of the 16 kHz octave; beyond a measurement radius of
2 m the surface level takes the absorption correction of Formula (10), with
:math:`\alpha` in decibels per metre:

.. math::

   K = r \cdot \alpha \tag{10}

**Reference meteorological conditions.** Clause 10.1 carries the levels of
the reverberation-room methods to 101,325 kPa and 23,0 °C "de acuerdo con la
Norma ISO 3741", which is the reference-quantity correction :math:`C_1` and
the radiation-impedance correction :math:`C_2` of ISO 3741:2010 clause 9.1.4
for a direct method and :math:`C_2` alone for the comparison with a reference
source, exactly as ISO 3741 Formulae (20) and (21) apply them.

Formulae (4) to (10) carry no worked example in the standard and are pinned
in closed form; Tables 1 and 2 are the numeric oracle of Annex A.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

from .._internal.levels_math import energy_mean, energy_sum
from .._internal.validation import (
    require_choice,
    require_finite_array,
    require_positive,
    require_positive_array,
    require_ranks,
    require_same_length,
)
from ..environment.propagation.air_absorption import (
    _EIGHT_686,
    _KELVIN,
    _pure_tone_terms,
    _validate,
)
from ._shared import (
    SoundPowerWarning,
    _c1_correction,
    _c2_correction,
    _validate_meteorology,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike, NDArray

#: The 16 kHz octave band the standard covers, in hertz (ISO 9295:2015,
#: clause 1: "frecuencias comprendidas entre 11,2 kHz y 22,4 kHz").
_OCTAVE_LOW_HZ = 11_200.0
_OCTAVE_HIGH_HZ = 22_400.0
#: The frequency from which the air absorbs practically all of the energy of
#: a reverberation room, the premise of Formula (7) (clause 7.2).
_AIR_ABSORPTION_FLOOR_HZ = 10_000.0
#: The lowest frequency of the ISO 9613-1 table, where the Annex A range of
#: this module begins.
_ISO_9613_LOW_HZ = 50.0
#: The Eyring constant of Formula (5), as printed (0,16 s/m).
_EYRING_CONSTANT = 0.16
#: The factor of Formula (7): the air absorption area is 8 alpha V when alpha
#: is the amplitude coefficient in nepers per metre (twice the energy one).
_AIR_ABSORPTION_FACTOR = 8.0
#: The 4 of the 10 lg(4/R) of Formula (6).
_DIFFUSE_FIELD_FOUR = 4.0
#: The widest FFT bandwidth Formula (9) admits, in hertz (clause 8.5.2).
_MAX_FFT_BANDWIDTH_HZ = 112.0
#: The measurement radius above which Formula (10) applies, in metres
#: (clause 9.8).
_ABSORPTION_CORRECTION_RADIUS_M = 2.0
#: How far below the highest tonal level a tone is still reported, in dB
#: (clause 13 c) and Table 3).
_TONE_REPORTING_RANGE_DB = 10.0

#: The rank of a levels array that holds the N orientations (or revolutions)
#: of Formula (1) as rows and the bands as columns.
_ORIENTATIONS_BY_BANDS = 2

_METHODS = ("direct", "comparison")


# --- Annex A: air absorption in nepers per metre -----------------------------


def air_absorption_np_per_m(
    frequencies_hz: ArrayLike,
    *,
    temperature_c: float,
    relative_humidity_percent: float,
    static_pressure_kpa: float = 101.325,
) -> NDArray[np.float64]:
    r"""Air absorption coefficient :math:`\alpha` in nepers per metre (ISO 9295 Annex A).

    Formulae (A.1) to (A.5) of ISO 9295:2015 are the ISO 9613-1:1993
    pure-tone attenuation written for the amplitude in nepers per metre, the
    unit Formula (7) takes, so this is the library's ISO 9613-1 evaluation
    without its factor 8,686 (Annex A: "multiplicando el valor de
    :math:`\alpha` en Np/m por 8,686 para obtener el valor de :math:`\alpha`
    en dB/m"). The difference from
    :func:`~phonometry.environment.propagation.air_absorption.air_attenuation`
    is the range: Annex A evaluates the same formula up to 22,4 kHz, the top
    of the 16 kHz octave band, so no advisory is raised between 10 kHz and
    22,4 kHz, where ISO 9613-1 stops tabulating.

    :param frequencies_hz: Frequency or frequencies ``f``, in hertz.
    :param temperature_c: Air temperature, in degrees Celsius. Outside
        -20 °C to +50 °C emits an
        :class:`~phonometry.environment.propagation.air_absorption.AtmosphericAbsorptionWarning`.
    :param relative_humidity_percent: Relative humidity ``h_r``, in percent.
    :param static_pressure_kpa: Static pressure ``p_s``, in kilopascals
        (default 101,325 kPa, the pressure Tables 1 and 2 are printed at).
    :return: :math:`\alpha` in Np/m, with the shape of ``frequencies_hz``.
    :raises ValueError: for a non-positive frequency, a temperature at or
        below absolute zero, a relative humidity outside [0, 100] % or a
        non-positive static pressure.
    """
    freqs = np.asarray(frequencies_hz, dtype=np.float64)
    _validate(
        freqs,
        temperature_c,
        relative_humidity_percent,
        static_pressure_kpa,
        frequency_scope=(
            _ISO_9613_LOW_HZ,
            _OCTAVE_HIGH_HZ,
            "range of ISO 9613-1:1993 as extended by ISO 9295:2015 Annex A",
        ),
    )
    f2, bracket = _pure_tone_terms(
        freqs, temperature_c + _KELVIN, relative_humidity_percent, static_pressure_kpa
    )
    return np.asarray(f2 * bracket, dtype=np.float64)


# --- Room constant: Formulae (4), (5) and (7) --------------------------------


def _room_geometry(volume_m3: float, surface_area_m2: float) -> tuple[float, float]:
    """The room volume and surface, each positive and finite."""
    return (
        require_positive(volume_m3, "volume_m3"),
        require_positive(surface_area_m2, "surface_area_m2"),
    )


def room_absorption_coefficient(
    reverberation_time_s: ArrayLike, *, volume_m3: float, surface_area_m2: float
) -> NDArray[np.float64]:
    r"""Room absorption coefficient from the reverberation time (ISO 9295 Formula (5)).

    :math:`\alpha_\mathrm{room} = 1 - \mathrm{e}^{-0{,}16 \, V / (S T)}`, the
    Eyring relation solved for the absorption coefficient. Clause 6.1 asks
    for it rather than the simpler Sabine one because above 10 kHz the room
    absorption coefficient cannot be taken as small compared with unity. The
    constant is the 0,16 the formula prints.

    :param reverberation_time_s: Mean measured reverberation time ``T`` per
        band, in seconds (scalar or one value per band); clause 6.2 averages
        three or four points of the microphone path.
    :param volume_m3: Room volume ``V``, in cubic metres.
    :param surface_area_m2: Total room surface ``S``, in square metres.
    :return: :math:`\alpha_\mathrm{room}` per band, in (0, 1).
    :raises ValueError: for a non-positive or non-finite time, volume or
        surface.
    """
    t = require_positive_array(reverberation_time_s, "reverberation_time_s")
    volume, surface = _room_geometry(volume_m3, surface_area_m2)
    return np.asarray(
        1.0 - np.exp(-_EYRING_CONSTANT * volume / (surface * t)), dtype=np.float64
    )


def room_constant_from_reverberation_time(
    reverberation_time_s: ArrayLike, *, volume_m3: float, surface_area_m2: float
) -> NDArray[np.float64]:
    r"""Room constant from the measured reverberation time (ISO 9295 Formulae (4), (5)).

    :math:`R = S \alpha_\mathrm{room} / (1 - \alpha_\mathrm{room})` with
    :math:`\alpha_\mathrm{room}` from :func:`room_absorption_coefficient`,
    the room constant of the method of clause 6. It goes into
    :func:`high_frequency_sound_power` as ``room_constant_m2``.

    :param reverberation_time_s: Mean measured reverberation time ``T`` per
        band, in seconds (scalar or one value per band).
    :param volume_m3: Room volume ``V``, in cubic metres.
    :param surface_area_m2: Total room surface ``S``, in square metres.
    :return: ``R`` per band, in square metres.
    :raises ValueError: for a non-positive or non-finite time, volume or
        surface.
    """
    alpha = room_absorption_coefficient(
        reverberation_time_s, volume_m3=volume_m3, surface_area_m2=surface_area_m2
    )
    return np.asarray(float(surface_area_m2) * alpha / (1.0 - alpha), dtype=np.float64)


def room_constant_from_air_absorption(
    frequencies_hz: ArrayLike,
    *,
    volume_m3: float,
    surface_area_m2: float,
    temperature_c: float,
    relative_humidity_percent: float,
    static_pressure_kpa: float = 101.325,
) -> NDArray[np.float64]:
    r"""Room constant from the calculated air absorption (ISO 9295 Formula (7)).

    :math:`R = 8 \alpha V / (1 - 8 \alpha V / S)`, the room constant of the
    method of clause 7, with :math:`\alpha` in nepers per metre from
    :func:`air_absorption_np_per_m` (Annex A). The method takes all of the
    room absorption to be in the air, which clause 7.2 holds at 10 kHz and
    above; a band below 10 kHz emits a
    :class:`~phonometry.emission.SoundPowerWarning`, since the walls are no
    longer negligible there and the measured reverberation time of
    :func:`room_constant_from_reverberation_time` is the method to use.

    :param frequencies_hz: Band centre or tone frequencies, in hertz.
    :param volume_m3: Room volume ``V``, in cubic metres.
    :param surface_area_m2: Total room surface ``S``, in square metres.
    :param temperature_c: Air temperature in the room, in degrees Celsius.
    :param relative_humidity_percent: Relative humidity in the room, in percent.
    :param static_pressure_kpa: Static pressure in the room, in kilopascals
        (default 101,325 kPa).
    :return: ``R`` per frequency, in square metres.
    :raises ValueError: for a non-positive or non-finite volume or surface,
        for the atmospheric inputs :func:`air_absorption_np_per_m` refuses, or
        where :math:`8 \alpha V / S \ge 1`: the air alone would then absorb more
        than the room surface can, and Formula (7) has no finite room constant.
    """
    volume, surface = _room_geometry(volume_m3, surface_area_m2)
    freqs = require_positive_array(frequencies_hz, "frequencies_hz")
    alpha = air_absorption_np_per_m(
        freqs,
        temperature_c=temperature_c,
        relative_humidity_percent=relative_humidity_percent,
        static_pressure_kpa=static_pressure_kpa,
    )
    if np.any(freqs < _AIR_ABSORPTION_FLOOR_HZ):
        warnings.warn(
            "One or more frequencies are below 10 kHz, where ISO 9295:2015 "
            "clause 7.2 no longer takes the air to hold practically all of the "
            "room absorption; the measured reverberation time of clause 6 is "
            "the method there.",
            SoundPowerWarning,
            stacklevel=2,
        )
    area = _AIR_ABSORPTION_FACTOR * alpha * volume
    mean_absorption = area / surface
    if np.any(mean_absorption >= 1.0):
        msg = (
            "8 alpha V / S reaches 1 at one or more frequencies: the air alone "
            "would absorb more than the room surface can, and Formula (7) of "
            "ISO 9295:2015 has no finite room constant there."
        )
        raise ValueError(msg)
    return np.asarray(area / (1.0 - mean_absorption), dtype=np.float64)


# --- Formulae (2) and (3): tones under a moving microphone -------------------


def minimum_analyzer_bandwidth_hz(
    tone_frequency_hz: ArrayLike,
    *,
    microphone_speed_m_s: float,
    speed_of_sound: float,
) -> NDArray[np.float64]:
    r"""Narrowest analyser bandwidth that holds a tone seen by a moving microphone.

    :math:`\Delta f = 2 f v / c`, ISO 9295:2015 Formula (2). The moving
    microphone spreads the energy of a discrete tone over sidebands either
    side of its frequency, and an analyser at least this wide collects the
    whole tone in one band; a narrower one (an FFT) needs its sidebands
    summed with :func:`tone_level_from_sidebands`.

    :param tone_frequency_hz: Centre frequency ``f`` of the tone, in hertz.
    :param microphone_speed_m_s: Speed ``v`` of the microphone along its
        path, in metres per second.
    :param speed_of_sound: Speed of sound ``c``, in metres per second.
    :return: The minimum bandwidth :math:`\Delta f`, in hertz.
    :raises ValueError: for a non-positive or non-finite input.
    """
    f = require_positive_array(tone_frequency_hz, "tone_frequency_hz")
    v = require_positive(microphone_speed_m_s, "microphone_speed_m_s")
    c = require_positive(speed_of_sound, "speed_of_sound")
    return np.asarray(2.0 * f * v / c, dtype=np.float64)


def tone_level_from_sidebands(sideband_levels_db: ArrayLike) -> float:
    r"""Total level of a tone from its sideband levels (ISO 9295 Formula (3)).

    :math:`L_\mathrm{tot} = 10 \lg \sum_{i=1}^{N_\mathrm{sb}} 10^{0{,}1 L_i}`,
    the energy sum of the bands adjacent to the tone frequency that carry
    its energy when the analyser is narrower than
    :func:`minimum_analyzer_bandwidth_hz`.

    :param sideband_levels_db: The :math:`N_\mathrm{sb}` sideband levels
        :math:`L_i`, in decibels re 20 µPa.
    :return: :math:`L_\mathrm{tot}`, in decibels re 20 µPa.
    :raises ValueError: for an empty or non-finite input.
    """
    levels = require_finite_array(sideband_levels_db, "sideband_levels_db")
    return energy_sum(levels)


# --- Formula (10): the free-field method beyond 2 m --------------------------


def free_field_absorption_correction(
    frequencies_hz: ArrayLike,
    *,
    radius_m: float,
    temperature_c: float,
    relative_humidity_percent: float,
    static_pressure_kpa: float = 101.325,
) -> NDArray[np.float64]:
    r"""Air absorption correction of the free-field method (ISO 9295 Formula (10)).

    :math:`K = r \cdot \alpha`, with :math:`\alpha` the air absorption in
    decibels per metre (Annex A times 8,686). Clause 9.8 adds it to the
    surface sound pressure level of ISO 3744 before the sound power is
    determined, and only when the measurement radius exceeds 2 m; at 2 m
    or less the clause asks for no correction and this returns zero. The
    surface level and the sound power level differ by the constant
    :math:`10 \lg(S/S_0)`, so adding ``K`` to the band levels
    :func:`~phonometry.emission.sound_power.sound_power_pressure` returns
    is the same thing.

    :param frequencies_hz: Band centre or tone frequencies, in hertz.
    :param radius_m: Radius ``r`` of the measurement hemisphere, in metres.
    :param temperature_c: Air temperature, in degrees Celsius.
    :param relative_humidity_percent: Relative humidity, in percent.
    :param static_pressure_kpa: Static pressure, in kilopascals (default
        101,325 kPa).
    :return: ``K`` per frequency, in decibels.
    :raises ValueError: for a non-positive radius or the atmospheric inputs
        :func:`air_absorption_np_per_m` refuses.
    """
    radius = require_positive(radius_m, "radius_m")
    alpha_db_per_m = _EIGHT_686 * air_absorption_np_per_m(
        frequencies_hz,
        temperature_c=temperature_c,
        relative_humidity_percent=relative_humidity_percent,
        static_pressure_kpa=static_pressure_kpa,
    )
    if radius <= _ABSORPTION_CORRECTION_RADIUS_M:
        return np.zeros_like(alpha_db_per_m)
    return np.asarray(radius * alpha_db_per_m, dtype=np.float64)


# --- Formulae (6), (8) and (9): the sound power level ------------------------


@dataclass(frozen=True)
class HighFrequencySoundPowerResult:
    r"""A sound power determination in the 16 kHz octave band (ISO 9295:2015).

    One value per band: a one-third octave band of the 16 kHz octave for
    broadband noise, or the narrow band of a discrete tone.

    :ivar frequencies: Band centre or tone frequencies, in hertz.
    :ivar sound_power_level: :math:`L_W` per band, in dB re 1 pW, at the
        reference meteorological conditions of clause 10.1 (Formula (6) plus
        :attr:`c1` and :attr:`c2` for the direct method, Formula (8) or (9)
        plus :attr:`c2` for the comparison).
    :ivar mean_pressure_level: :math:`\overline{L_{p(\mathrm{ST})}}` per
        band, in dB re 20 µPa, the energy mean of Formula (1) over the
        orientations or revolutions supplied.
    :ivar room_constant: The room constant ``R`` per band, in square metres,
        for the direct method (Formula (4) or (7)); ``None`` for the
        comparison.
    :ivar reference_sound_power_level: :math:`L_{W(\mathrm{FAR})}` per band,
        in dB re 1 pW (per hertz for the tonal comparison); ``None`` for the
        direct method.
    :ivar reference_pressure_level: :math:`\overline{L_{p(\mathrm{FAR})}}`
        per band, in dB re 20 µPa; ``None`` for the direct method.
    :ivar noise_bandwidth_hz: :math:`\Delta F` of Formula (9), in hertz, for
        the tonal comparison; ``None`` otherwise.
    :ivar c1: Reference-quantity correction ``C1`` of ISO 3741, in dB, for the
        direct method; ``NaN`` for the comparison, which does not apply it.
    :ivar c2: Radiation-impedance correction ``C2`` of ISO 3741, in dB.
    :ivar method: ``'direct'`` (clauses 6 and 7) or ``'comparison'``
        (clause 8).
    :ivar tonal: ``True`` when the bands are the narrow bands of discrete
        tones rather than one-third octave bands of broadband noise.
    """

    frequencies: NDArray[np.float64]
    sound_power_level: NDArray[np.float64]
    mean_pressure_level: NDArray[np.float64]
    room_constant: NDArray[np.float64] | None
    reference_sound_power_level: NDArray[np.float64] | None
    reference_pressure_level: NDArray[np.float64] | None
    noise_bandwidth_hz: float | None
    c1: float
    c2: float
    method: str
    tonal: bool

    def __post_init__(self) -> None:
        """Refuse a determination whose per-band quantities disagree.

        :raises ValueError: if ``method`` is neither ``'direct'`` nor
            ``'comparison'``, if a per-band field is not one-dimensional, or
            if two of them do not carry one value per band.
        """
        require_choice(self.method, "method", _METHODS)
        require_ranks(
            self,
            frequencies=1,
            sound_power_level=1,
            mean_pressure_level=1,
            room_constant=1,
            reference_sound_power_level=1,
            reference_pressure_level=1,
        )
        require_same_length(
            self,
            "frequencies",
            "sound_power_level",
            "mean_pressure_level",
            "room_constant",
            "reference_sound_power_level",
            "reference_pressure_level",
        )

    @property
    def within_10_db_of_maximum(self) -> NDArray[np.bool_]:
        """Bands whose level is within 10 dB of the highest one.

        Clause 13 c) and Table 3 ask for the level and the frequency of every
        tone that lies within 10 dB of the highest tonal level in the band, so
        for a tonal determination this marks the tones the report has to
        carry.
        """
        levels = np.asarray(self.sound_power_level, dtype=np.float64)
        return np.asarray(
            levels >= np.max(levels) - _TONE_REPORTING_RANGE_DB, dtype=np.bool_
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the band levels, with the mean room level they came from.

        Broadband bands are drawn as bars over the one-third octave bands; a
        tonal determination is drawn as one stem per tone on a frequency axis,
        with the line 10 dB below the highest tone that clause 13 c) reports
        down to. Requires matplotlib (``pip install phonometry[plot]``);
        returns the :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the bar or stem drawing of :math:`L_W`.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_high_frequency_sound_power

        check_language(language)
        return plot_high_frequency_sound_power(self, ax=ax, language=language, **kwargs)


def _mean_band_level(levels: ArrayLike, name: str) -> NDArray[np.float64]:
    """Formula (1): the energy mean over the rows of a 2-D input."""
    arr = np.asarray(levels, dtype=np.float64)
    if arr.ndim == _ORIENTATIONS_BY_BANDS:
        if arr.shape[0] == 0 or arr.shape[1] == 0 or not np.all(np.isfinite(arr)):
            msg = f"'{name}' must be a non-empty array of finite levels."
            raise ValueError(msg)
        return energy_mean(arr, axis=0)
    return require_finite_array(arr, name)


def _band_frequencies(frequencies_hz: ArrayLike, n_bands: int) -> NDArray[np.float64]:
    """One positive frequency per band, with an advisory outside the octave."""
    freqs = require_positive_array(frequencies_hz, "frequencies_hz")
    if freqs.shape != (n_bands,):
        msg = (
            f"'frequencies_hz' carries {freqs.size} value(s) for {n_bands} "
            "band(s); give one frequency per band."
        )
        raise ValueError(msg)
    if np.any(freqs < _OCTAVE_LOW_HZ) or np.any(freqs > _OCTAVE_HIGH_HZ):
        warnings.warn(
            "One or more frequencies are outside the 16 kHz octave band "
            "(11.2 kHz to 22.4 kHz) that ISO 9295:2015 covers; the methods of "
            "ISO 3741 and ISO 3744 are the ones below it.",
            SoundPowerWarning,
            stacklevel=3,
        )
    return freqs


def _per_band(value: ArrayLike, name: str, n_bands: int) -> NDArray[np.float64]:
    """A scalar or one value per band, as one value per band."""
    arr = np.atleast_1d(np.asarray(value, dtype=np.float64))
    if arr.ndim != 1 or arr.size not in (1, n_bands):
        msg = f"'{name}' must be a scalar or carry one value per band ({n_bands})."
        raise ValueError(msg)
    return np.broadcast_to(arr, (n_bands,)).astype(np.float64)


def high_frequency_sound_power(
    pressure_levels_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    room_constant_m2: ArrayLike,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    tonal: bool = False,
) -> HighFrequencySoundPowerResult:
    r"""Sound power level in the 16 kHz octave band, direct method (ISO 9295 Formula (6)).

    :math:`L_W = \overline{L_{p(\mathrm{ST})}} - 10 \lg(4/R) + C_1 + C_2`
    per band: Formula (6), carried to the reference meteorological conditions
    by the :math:`C_1` and :math:`C_2` of ISO 3741:2010 clause 9.1.4, which
    clause 10.1 points to. The same formula serves both direct methods; only
    the room constant differs, from the measured reverberation time
    (:func:`room_constant_from_reverberation_time`, clause 6) or from the
    calculated air absorption (:func:`room_constant_from_air_absorption`,
    clause 7).

    :param pressure_levels_db: :math:`\overline{L_{p(\mathrm{ST})}}` per band,
        in dB re 20 µPa, or an ``(N, bands)`` array of the time-averaged levels
        of the four orientations (:math:`N = 4`) or three boom revolutions
        (:math:`N = 3`), energy-averaged by Formula (1).
    :param frequencies_hz: Band centre or tone frequencies, in hertz, one per
        band. A frequency outside 11,2 kHz to 22,4 kHz emits a
        :class:`~phonometry.emission.SoundPowerWarning`.
    :param room_constant_m2: Room constant ``R``, in square metres, a scalar or
        one value per band.
    :param temperature_c: Air temperature in the room, in degrees Celsius
        (default 23,0 °C, the reference temperature).
    :param static_pressure_kpa: Static pressure in the room, in kilopascals
        (default 101,325 kPa, the reference pressure).
    :param tonal: ``True`` when the bands are the narrow bands of discrete
        tones (clause 6.5), which changes how the result is drawn and read.
    :return: A :class:`HighFrequencySoundPowerResult` with ``method='direct'``.
    :raises ValueError: for non-finite levels, a room constant that is not
        positive, frequencies that do not match the bands, or a temperature
        or static pressure ISO 3741 cannot correct from.
    """
    _validate_meteorology(temperature_c, static_pressure_kpa)
    mean_level = _mean_band_level(pressure_levels_db, "pressure_levels_db")
    n_bands = mean_level.size
    freqs = _band_frequencies(frequencies_hz, n_bands)
    room_constant = _per_band(room_constant_m2, "room_constant_m2", n_bands)
    if not np.all(np.isfinite(room_constant)) or np.any(room_constant <= 0.0):
        msg = "'room_constant_m2' must be positive and finite."
        raise ValueError(msg)
    c1 = _c1_correction(temperature_c, static_pressure_kpa)
    c2 = _c2_correction(temperature_c, static_pressure_kpa)
    level = mean_level - 10.0 * np.log10(_DIFFUSE_FIELD_FOUR / room_constant) + c1 + c2
    return HighFrequencySoundPowerResult(
        frequencies=freqs,
        sound_power_level=np.asarray(level, dtype=np.float64),
        mean_pressure_level=mean_level,
        room_constant=room_constant,
        reference_sound_power_level=None,
        reference_pressure_level=None,
        noise_bandwidth_hz=None,
        c1=c1,
        c2=c2,
        method="direct",
        tonal=bool(tonal),
    )


def high_frequency_sound_power_comparison(
    pressure_levels_db: ArrayLike,
    *,
    frequencies_hz: ArrayLike,
    reference_pressure_levels_db: ArrayLike,
    reference_sound_power_levels_db: ArrayLike,
    noise_bandwidth_hz: float | None = None,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
) -> HighFrequencySoundPowerResult:
    r"""Sound power level in the 16 kHz octave band against a reference source (ISO 9295 clause 8).

    For broadband noise, Formula (8):
    :math:`L_W = L_{W(\mathrm{FAR})} - \overline{L_{p(\mathrm{FAR})}}
    + \overline{L_{p(\mathrm{ST})}}`, per one-third octave band. For
    discrete tones, Formula (9) adds :math:`10 \lg(\Delta F / 1\ \mathrm{Hz})`,
    because the reference source is then calibrated per unit bandwidth
    (clause 8.1) and :math:`\Delta F` is the noise bandwidth of the constant
    bandwidth analyser. Clause 10.1 adds the radiation-impedance correction
    :math:`C_2` of ISO 3741, as ISO 3741 Formula (21) does for its own
    comparison method.

    :param pressure_levels_db: :math:`\overline{L_{p(\mathrm{ST})}}` per band,
        in dB re 20 µPa, or an ``(N, bands)`` array averaged by Formula (1).
    :param frequencies_hz: Band centre or tone frequencies, in hertz, one per
        band.
    :param reference_pressure_levels_db:
        :math:`\overline{L_{p(\mathrm{FAR})}}` per band, in dB re 20 µPa,
        measured with the same bandwidth at the same location (clauses 8.3,
        8.4); a 2-D input is averaged by Formula (1) as well.
    :param reference_sound_power_levels_db: :math:`L_{W(\mathrm{FAR})}` of the
        calibrated reference source, in dB re 1 pW, a scalar or one value per
        band: per band for broadband noise, per hertz for tones.
    :param noise_bandwidth_hz: :math:`\Delta F`, the noise bandwidth of the
        analyser, in hertz, which selects Formula (9); ``None`` (default)
        selects Formula (8). Clause 8.5.2 allows 1 Hz for a constant
        percentage analyser, and holds an FFT to 112 Hz or less: a wider one
        emits a :class:`~phonometry.emission.SoundPowerWarning`.
    :param temperature_c: Air temperature in the room, in degrees Celsius
        (default 23,0 °C).
    :param static_pressure_kpa: Static pressure in the room, in kilopascals
        (default 101,325 kPa).
    :return: A :class:`HighFrequencySoundPowerResult` with
        ``method='comparison'``, ``tonal`` set when ``noise_bandwidth_hz`` is
        given.
    :raises ValueError: for non-finite levels, reference levels that do not
        span the same bands, a non-positive bandwidth, or a temperature or
        static pressure ISO 3741 cannot correct from.
    """
    _validate_meteorology(temperature_c, static_pressure_kpa)
    mean_level = _mean_band_level(pressure_levels_db, "pressure_levels_db")
    n_bands = mean_level.size
    freqs = _band_frequencies(frequencies_hz, n_bands)
    reference_level = _mean_band_level(
        reference_pressure_levels_db, "reference_pressure_levels_db"
    )
    if reference_level.shape != (n_bands,):
        msg = (
            "'reference_pressure_levels_db' must span the same bands as "
            f"'pressure_levels_db' ({n_bands})."
        )
        raise ValueError(msg)
    reference_power = _per_band(
        reference_sound_power_levels_db, "reference_sound_power_levels_db", n_bands
    )
    if not np.all(np.isfinite(reference_power)):
        msg = "'reference_sound_power_levels_db' must be finite."
        raise ValueError(msg)
    bandwidth_term = 0.0
    bandwidth = None
    if noise_bandwidth_hz is not None:
        bandwidth = require_positive(noise_bandwidth_hz, "noise_bandwidth_hz")
        if bandwidth > _MAX_FFT_BANDWIDTH_HZ:
            warnings.warn(
                f"A noise bandwidth of {bandwidth:g} Hz is wider than the 112 Hz "
                "ISO 9295:2015 clause 8.5.2 allows an FFT analyser.",
                SoundPowerWarning,
                stacklevel=2,
            )
        bandwidth_term = 10.0 * np.log10(bandwidth)
    c2 = _c2_correction(temperature_c, static_pressure_kpa)
    level = reference_power - reference_level + mean_level + bandwidth_term + c2
    return HighFrequencySoundPowerResult(
        frequencies=freqs,
        sound_power_level=np.asarray(level, dtype=np.float64),
        mean_pressure_level=mean_level,
        room_constant=None,
        reference_sound_power_level=reference_power,
        reference_pressure_level=reference_level,
        noise_bandwidth_hz=bandwidth,
        c1=float("nan"),
        c2=c2,
        method="comparison",
        tonal=bandwidth is not None,
    )
