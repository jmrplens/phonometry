#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Sound power level of a small movable source in a special reverberation
test room: ISO 3743-2:2018 (engineering grade 2), the direct method and the
comparison method.

Part 1 of ISO 3743 asks little of the room and pays with a reference sound
source at every determination. Part 2 turns that round: the room is built to
a specification tight enough that the sound power can be read off the mean
room level alone. It is at least 70 m³ (and at most 300 m³ when the 4 kHz and
8 kHz octaves matter, 6.2), its floor reflects (absorption coefficient below
0,06) and its walls and ceiling absorb alike, each within 0,5 and 1,5 times
their mean (6.4), and above all its reverberation time follows a prescribed
curve (6.3): within 0,9 and 1,1 times :math:`R\,T_\mathrm{nom}` (0,8 and 1,2
above 6,3 kHz), with the reverberation parameter

.. math::

   R = 1 + \frac{257}{f V^{1/3}} \tag{Formula 1}

or, for a room that is not nearly cubical, :math:`R = 1 + cS/(8Vf)`, and a
nominal reverberation time :math:`T_\mathrm{nom}` between 0,5 s and 1,0 s.
The rise of :math:`R` at low frequencies is the Waterhouse correction built
into the room: the energy stored near the boundaries of a small room is
compensated by a longer reverberation time instead of a term in the
equation. So the direct method reduces to (10.2)

.. math::

   L_W = \overline{L_p} - 10 \log_{10}\frac{T_\mathrm{nom}}{T_0}
   + 10 \log_{10}\frac{V}{V_0} - 13\ \mathrm{dB} \tag{Formula 9}

for each octave band and for the A-weighted level measured as such, with
:math:`T_0` = 1 s and :math:`V_0` = 1 m³; the 13 dB instead of the 14 dB of
other standards, and the slope of the reverberation time, account for the
energy density near the surfaces and near the source (NOTE to 10.2). The
comparison method replaces the room by a reference sound source measured at
no fewer than six positions (10.3):

.. math::

   L_{W\mathrm{e}} = L_{p\mathrm{e}} + \left(L_{W\mathrm{r}} - L_{p\mathrm{r}}\right)
   \tag{Formula 10}

Both methods take the mean of the measured levels as the energy mean of all
of them (Formula 8) after correcting each one for background noise by the
stepped Table 4, 2 dB at a 4 dB or 5 dB margin, 1 dB from 6 dB to 8 dB,
0,5 dB at 9 dB and 10 dB and nothing above; a margin below 4 dB leaves the
level unreportable unless the report says the requirement of 6.5 was not met.
The table gives whole-decibel differences, and the library reads a measured
difference at the nearest whole decibel (a margin of 5,4 dB takes the 5 dB
row, one of 5,5 dB the 6 dB row), anything above 10 dB taking the last row.

Annex E carries the level to the reference meteorological conditions with the
radiation-impedance correction :math:`C_2` of ISO 3743-1:2010 Annex A, and
Annex F forms the A-weighted level from octave bands with Table F.1, which is
ISO 3743-1:2010 Table B.1. Clause 11 prints its own typical upper bounds of
:math:`\sigma_{R0}` (Table 5): 5,0 dB at 125 Hz, 3,0 dB at 250 Hz, 2,0 dB from
500 Hz to 4 kHz, 3,0 dB at 8 kHz and 2,0 dB A-weighted.

The room is qualified by :func:`check_special_room_reverberation` (6.2, 6.3
and the climate of 6.6), :func:`check_special_room_surfaces` (6.4) and
:func:`check_special_room_suitability` (6.7, the octave-band power of a
calibrated reference source determined in the room against its calibration,
Table 1). The number of source locations and microphone positions follows
from the survey of 9.4 by :func:`special_room_source_locations` (Table 3),
which also reads the spectral character of 9.5.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

    from .._report.metadata import ReportMetadata
    from .reference_sound_source import ReferenceSourceCalibration

from .._internal.levels_math import energy_mean, energy_sum
from .._internal.validation import (
    check_engine,
    require_choice,
    require_positive,
    require_ranks,
    require_same_length,
)
from ._shared import (
    SoundPowerWarning,
    _a_weighting_corrections,
    _c2_correction,
    _reference_power_levels,
    _settled,
    _validate_meteorology,
)
from .sound_power_hard_walled import (
    SourceLocationPlan,
    _check_uncertainty_inputs,
    _finite,
    _octave_frequencies,
)

#: The standard implemented here, as the warnings cite it.
_STANDARD = "ISO 3743-2:2018"
#: The two table references the frequency validator cites.
_TABLE_F1 = f"{_STANDARD}, Table F.1"
#: Reference quantities of Formula (9).
_T0_S = 1.0
_V0_M3 = 1.0
#: The constant of Formula (9), in decibels.
_DIRECT_CONSTANT_DB = 13.0
#: Formula (1): 257 in R = 1 + 257/(f V^(1/3)).
_R_CONSTANT = 257.0
#: The tolerance of 6.3 on T/(R Tnom), up to 6,3 kHz and above it.
_TOLERANCE = 0.1
_TOLERANCE_HIGH = 0.2
#: Bands above 6,3 kHz take the wider tolerance; the boundary is the upper
#: edge of the 6,3 kHz one-third-octave band, 6 300 x 2^(1/6) Hz, so that an
#: exact base-ten centre of that band still reads as 6,3 kHz.
_HIGH_TOLERANCE_ABOVE_HZ = 6300.0 * 2.0 ** (1.0 / 6.0)
#: 6.3: the nominal reverberation time lies between 0,5 s and 1,0 s.
_TNOM_MIN_S = 0.5
_TNOM_MAX_S = 1.0
#: 6.2: at least 70 m³, and at most 300 m³ when the 4 kHz and 8 kHz octaves
#: are within the frequency range of interest (direct method; the NOTE relaxes
#: it for the comparison method).
_MIN_VOLUME_M3 = 70.0
_MAX_VOLUME_HIGH_OCTAVES_M3 = 300.0
#: Clause 5: the volume of the noise source should not exceed 1 % of the
#: volume of the room (0,7 m³ in the smallest room of 70 m³).
_SOURCE_VOLUME_FRACTION = 0.01
#: The lower edge of the 8 kHz octave band, 8 000 / sqrt(2) Hz: a measurement
#: reaching it has the 8 kHz octave in its frequency range.
_EIGHT_KHZ_OCTAVE_LOWER_EDGE_HZ = 8000.0 / math.sqrt(2.0)
#: 6.6: the product H (theta + 5 degC) stays within +/-10 % of its value while
#: the reverberation time was measured.
_CLIMATE_OFFSET_C = 5.0
_CLIMATE_TOLERANCE = 0.10
#: 6.4: the floor absorbs less than 0,06, and each wall and the ceiling within
#: 0,5 and 1,5 times the mean of the walls and ceiling.
_FLOOR_MAX_ABSORPTION = 0.06
_SURFACE_RATIO_MIN = 0.5
_SURFACE_RATIO_MAX = 1.5
#: Table 1: maximum permitted difference between the octave-band power of a
#: broad-band reference source determined in the room and its calibration.
_TABLE1_DB: Mapping[int, float] = MappingProxyType(
    {125: 5.0, 250: 3.0, 500: 3.0, 1000: 3.0, 2000: 3.0, 4000: 3.0, 8000: 4.0}
)
#: Table 4: background margin (whole decibels) and the correction to subtract.
_TABLE4: Mapping[int, float] = MappingProxyType(
    {4: 2.0, 5: 2.0, 6: 1.0, 7: 1.0, 8: 1.0, 9: 0.5, 10: 0.5}
)
_TABLE4_MIN_DB = 4
_TABLE4_MAX_DB = 10
#: Table 5: typical upper bounds of sigma_R0 per octave band, and A-weighted.
_SIGMA_R0_DB: Mapping[int, float] = MappingProxyType(
    {125: 5.0, 250: 3.0, 500: 2.0, 1000: 2.0, 2000: 2.0, 4000: 2.0, 8000: 3.0}
)
_SIGMA_R0_A_DB = 2.0
#: Coverage factor of the two-sided 95 % interval (11.1).
_COVERAGE_TWO_SIDED = 2.0
#: The fewest microphone positions of Table 3, and the six of the survey (9.4)
#: and of the reference source in the comparison method (10.3).
_MIN_MICROPHONES = 3
_SURVEY_MICROPHONES = 6
#: 9.4: the survey switches from the arithmetic to the energy mean of the six
#: levels when their range exceeds 5 dB (Formula 5).
_ARITHMETIC_MEAN_RANGE_DB = 5.0
#: Table 3 and 9.5: the class limits of s_M, in decibels.
_SM_BROADBAND_BELOW_DB = 2.3
_SM_NARROW_BAND_UP_TO_DB = 4.0
#: Table 3: the columns of microphone positions.
_TABLE3_MICROPHONES: tuple[int, ...] = (3, 6, 12)
#: Table 3: minimum number of source locations for 3, 6 and 12 microphone
#: positions, by s_M class and by band group ('A' is the A-weighted row).
_TABLE3: Mapping[str, Mapping[str, tuple[int, int, int]]] = MappingProxyType(
    {
        "broadband": MappingProxyType(
            dict.fromkeys(("125", "250", "500", "high", "A"), (1, 1, 1))
        ),
        "narrow-band": MappingProxyType(
            {
                "125": (1, 1, 1),
                "250": (2, 2, 1),
                "500": (2, 2, 1),
                "A": (2, 2, 1),
                "high": (2, 1, 1),
            }
        ),
        "discrete tone": MappingProxyType(
            {
                "125": (3, 2, 2),
                "250": (4, 3, 2),
                "A": (4, 3, 2),
                "500": (4, 2, 2),
                "high": (3, 2, 1),
            }
        ),
    }
)

Method = Literal["direct", "comparison"]


def _table4_correction(delta: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The Table 4 correction for each margin, and where it was at least 4 dB.

    The margin is read at the nearest whole decibel; any margin above 10 dB
    takes the last row (0 dB) and any below 4 dB takes the 4 dB row (2 dB),
    since the table has nothing lower and the level is then reported, if at
    all, as not meeting the requirement (9.8).
    """
    margin = _settled(delta)
    whole = np.clip(np.floor(margin + 0.5), _TABLE4_MIN_DB, _TABLE4_MAX_DB)
    table = np.vectorize(lambda d: _TABLE4[int(d)], otypes=[np.float64])(whole)
    correction = np.where(margin > _TABLE4_MAX_DB, 0.0, table)
    return np.asarray(correction, dtype=np.float64), np.asarray(
        margin >= _TABLE4_MIN_DB, dtype=bool
    )


def special_room_background_correction(
    levels: ArrayLike, background_levels: ArrayLike
) -> np.ndarray:
    r"""The background correction of ISO 3743-2:2018 Table 4 (9.8).

    The decibels to subtract from a level measured with the source operating
    to leave the level of the source alone, read from the difference between
    that level and the background level alone: 2 dB for a difference of 4 dB
    or 5 dB, 1 dB for 6 dB to 8 dB, 0,5 dB for 9 dB and 10 dB, and nothing
    for a difference above 10 dB.

    The table gives whole decibels, and the difference is read at the nearest
    whole decibel. A difference below 4 dB takes the 4 dB row and warns: the
    accuracy is then reduced, and 9.8 allows the level to be reported only
    with the statement that the background requirement was not fulfilled.
    The informative Annex D treats the table as a rounding of
    :math:`-10 \lg (1 - 10^{-0{,}1 \Delta L_p})`; the normative text is the
    table, and that is what is applied.

    :param levels: Levels measured with the source operating, in decibels.
    :param background_levels: Background levels alone, broadcasting against
        ``levels``, in decibels.
    :return: The correction to subtract, in decibels, of the broadcast shape.
    :raises ValueError: for non-finite or empty inputs, or shapes that do not
        broadcast.
    """
    signal = np.asarray(levels, dtype=np.float64)
    background = np.asarray(background_levels, dtype=np.float64)
    if signal.size == 0 or background.size == 0:
        msg = "'levels' and 'background_levels' must not be empty."
        raise ValueError(msg)
    if not np.all(np.isfinite(signal)) or not np.all(np.isfinite(background)):
        msg = "'levels' and 'background_levels' must be finite."
        raise ValueError(msg)
    try:
        delta = signal - background
    except ValueError as exc:
        msg = (
            "'background_levels' must broadcast against 'levels'; got shapes "
            f"{background.shape} and {signal.shape}."
        )
        raise ValueError(msg) from exc
    correction, met = _table4_correction(delta)
    if not np.all(met):
        warnings.warn(
            "A background margin is below 4 dB; Table 4 has no row for it, the "
            "4 dB row is applied and the level can be reported only as not "
            f"meeting the background requirement ({_STANDARD}, 9.8).",
            SoundPowerWarning,
            stacklevel=2,
        )
    return correction


def reverberation_parameter(
    frequencies: ArrayLike,
    volume_m3: float,
    *,
    surface_area_m2: float | None = None,
    speed_of_sound: float | None = None,
) -> np.ndarray:
    r"""The reverberation parameter :math:`R` of ISO 3743-2:2018, 6.3.

    .. math::

       R = 1 + \frac{257}{f V^{1/3}} \tag{Formula 1}

    for a room that is nearly cubical, or, by the NOTE to 6.3, the more robust

    .. math::

       R = 1 + \frac{c\,S}{8 V f}

    for any shape, which is the Waterhouse factor of ISO 3741 turned into a
    target for the reverberation time. The two agree for a cube when
    :math:`c = 257 \times 8/6 = 342{,}7` m/s, which is the speed of sound
    Formula (1) carries inside its constant. For 70 m³ the value at 1 kHz is
    the 1,06 of Formula (B.2).

    6.3 sends a 70 m³ room to Figure 1 instead, but the printed curve runs
    0,03 to 0,04 above Formula (1) from 100 Hz to 160 Hz and about 0,01 below
    it from 1 600 Hz up (see ``docs/ERRATA.md``), so Formula (1) is used for
    that volume too and nothing is read off the figure.

    :param frequencies: Band centre frequencies, in hertz.
    :param volume_m3: Volume of the test room, in cubic metres.
    :param surface_area_m2: Total surface area of the room, in square metres;
        with ``speed_of_sound`` it selects the NOTE form.
    :param speed_of_sound: Speed of sound, in metres per second, required
        with ``surface_area_m2`` and refused without it.
    :return: :math:`R` per frequency.
    :raises ValueError: for a non-positive frequency, volume, area or speed,
        or only one of the NOTE's two inputs.
    """
    freqs = np.asarray(frequencies, dtype=np.float64)
    if freqs.size == 0 or not np.all(np.isfinite(freqs)) or np.any(freqs <= 0.0):
        msg = "'frequencies' must be finite and positive."
        raise ValueError(msg)
    volume = require_positive(volume_m3, "volume_m3")
    if (surface_area_m2 is None) != (speed_of_sound is None):
        msg = (
            "'surface_area_m2' and 'speed_of_sound' select the NOTE form of "
            "6.3 together; give both or neither."
        )
        raise ValueError(msg)
    if surface_area_m2 is None or speed_of_sound is None:
        return np.asarray(1.0 + _R_CONSTANT / (freqs * volume ** (1.0 / 3.0)))
    area = require_positive(surface_area_m2, "surface_area_m2")
    speed = require_positive(speed_of_sound, "speed_of_sound")
    return np.asarray(1.0 + speed * area / (8.0 * volume * freqs))


def _tolerance(frequencies: np.ndarray) -> np.ndarray:
    """The half-width of the 6.3 tolerance per band: 0,1, or 0,2 above 6,3 kHz."""
    return np.where(frequencies > _HIGH_TOLERANCE_ABOVE_HZ, _TOLERANCE_HIGH, _TOLERANCE)


def _centred_scale(ratio: np.ndarray, half_width: np.ndarray) -> float:
    r"""The scale :math:`k = 1/T_\mathrm{nom}` that centres ``ratio`` = T/R.

    Centring is read as leaving the most margin: :math:`k` minimises the
    largest deviation :math:`|k q_f - 1| / w_f` of any band from the ideal
    curve, each measured against its own half-width. That function of
    :math:`k` is convex and piecewise linear, so its minimum sits where the
    rising deviation of one band meets the falling deviation of another,
    :math:`k = (w_i + w_j)/(q_i w_j + q_j w_i)`, or at the one band's own
    :math:`1/q` (the pair :math:`i = j`); every pair is evaluated and the
    best kept. With a single tolerance this is the scale that puts the
    largest and the smallest ratio equally far outside and inside,
    :math:`k = 2/(q_{\max} + q_{\min})`.
    """
    q_i, q_j = np.meshgrid(ratio, ratio, indexing="ij")
    w_i, w_j = np.meshgrid(half_width, half_width, indexing="ij")
    candidates = ((w_i + w_j) / (q_i * w_j + q_j * w_i)).ravel()
    deviation = np.max(
        np.abs(candidates[:, None] * ratio[None, :] - 1.0) / half_width[None, :],
        axis=1,
    )
    return float(candidates[int(np.argmin(deviation))])


@dataclass(frozen=True)
class SpecialRoomReverberationCheck:
    r"""Qualification of a special reverberation test room by its
    reverberation time, volume and climate (ISO 3743-2:2018, 6.2, 6.3, 6.6).

    ``reverberation_time_s`` is the measured :math:`T` per band and
    ``reverberation_parameter`` the :math:`R` of Formula (1) (or its NOTE);
    ``nominal_reverberation_time_s`` is :math:`T_\mathrm{nom}`, supplied or,
    with ``centred`` ``True``, found by centring the measured values within
    the limiting curves. ``lower_limit`` and ``upper_limit`` are the bounds on
    :math:`T/(R\,T_\mathrm{nom})`, 0,9 and 1,1, or 0,8 and 1,2 above 6,3 kHz.
    ``volume_m3`` is the room and ``method`` the determination it is being
    qualified for, which decides whether the 300 m³ ceiling applies.
    ``climate_product_change`` is the relative change of
    :math:`H(\theta + 5\ ^\circ\mathrm{C})` between the reverberation
    measurement and the test, ``NaN`` when the climates were not given.
    ``source_volume_m3`` is the volume of the noise source to be tested in
    the room, ``NaN`` when it was not given; clause 5 recommends at most 1 %
    of the room, which :attr:`source_size_recommended` reads and
    :attr:`passes` leaves out, the clause saying "should" where 6.2, 6.3 and
    6.6 say "shall".
    """

    frequencies: np.ndarray
    reverberation_time_s: np.ndarray
    reverberation_parameter: np.ndarray
    nominal_reverberation_time_s: float
    centred: bool
    lower_limit: np.ndarray
    upper_limit: np.ndarray
    volume_m3: float
    method: str
    climate_product_change: float = math.nan
    source_volume_m3: float = math.nan

    def __post_init__(self) -> None:
        """Reject a check whose per-band arrays disagree.

        :raises ValueError: if the per-band arrays differ in length or rank,
            the nominal reverberation time, the volume or a given source
            volume is not positive, or the method is unknown.
        """
        require_choice(self.method, "method", ("direct", "comparison"))
        require_positive(
            self.nominal_reverberation_time_s, "nominal_reverberation_time_s"
        )
        require_positive(self.volume_m3, "volume_m3")
        if not math.isnan(self.source_volume_m3):
            require_positive(self.source_volume_m3, "source_volume_m3")
        bands = (
            "frequencies",
            "reverberation_time_s",
            "reverberation_parameter",
            "lower_limit",
            "upper_limit",
        )
        require_ranks(self, **dict.fromkeys(bands, 1))
        require_same_length(self, *bands)

    @property
    def normalized_ratio(self) -> np.ndarray:
        r""":math:`T/(R\,T_\mathrm{nom})` per band, which 6.3 bounds."""
        return np.asarray(
            self.reverberation_time_s
            / (self.reverberation_parameter * self.nominal_reverberation_time_s),
            dtype=np.float64,
        )

    @property
    def ratio_to_nominal(self) -> np.ndarray:
        r""":math:`T/T_\mathrm{nom}` per band, the quantity Figure B.3 draws."""
        return np.asarray(
            self.reverberation_time_s / self.nominal_reverberation_time_s,
            dtype=np.float64,
        )

    @property
    def band_within(self) -> np.ndarray:
        """Per band, whether ``T`` lies within the limiting curves."""
        ratio = _settled(self.normalized_ratio)
        return np.asarray(
            (ratio >= self.lower_limit) & (ratio <= self.upper_limit), dtype=bool
        )

    @property
    def nominal_in_range(self) -> bool:
        r"""Whether :math:`T_\mathrm{nom}` is between 0,5 s and 1,0 s (6.3)."""
        nominal = float(_settled(self.nominal_reverberation_time_s))
        return _TNOM_MIN_S <= nominal <= _TNOM_MAX_S

    @property
    def volume_large_enough(self) -> bool:
        """Whether the room is at least 70 m³ (6.2)."""
        return self.volume_m3 >= _MIN_VOLUME_M3

    @property
    def volume_small_enough(self) -> bool:
        """Whether the 300 m³ ceiling of 6.2 is kept where it applies.

        It applies to the direct method when the 8 kHz octave, and with it the
        4 kHz one, is within the measured range; the NOTE lifts it for the
        comparison method.
        """
        applies = self.method == "direct" and bool(
            np.max(self.frequencies) >= _EIGHT_KHZ_OCTAVE_LOWER_EDGE_HZ
        )
        return not applies or self.volume_m3 <= _MAX_VOLUME_HIGH_OCTAVES_M3

    @property
    def climate_stable(self) -> bool | None:
        r"""Whether :math:`H(\theta + 5)` stayed within ±10 % (6.6); ``None``
        when the climates were not given.
        """
        if math.isnan(self.climate_product_change):
            return None
        return float(_settled(abs(self.climate_product_change))) <= _CLIMATE_TOLERANCE

    @property
    def source_size_recommended(self) -> bool | None:
        """Whether the source is at most 1 % of the room, as clause 5
        recommends; ``None`` when no source volume was given.
        """
        if math.isnan(self.source_volume_m3):
            return None
        ratio = float(_settled(self.source_volume_m3 / self.volume_m3))
        return ratio <= _SOURCE_VOLUME_FRACTION

    @property
    def passes(self) -> bool:
        """Whether the room qualifies on every requirement that was evaluated
        (6.2, 6.3 and 6.6); the recommendation of clause 5 on the size of the
        source is read by :attr:`source_size_recommended` and left out.
        """
        climate = self.climate_stable
        return (
            bool(np.all(self.band_within))
            and self.nominal_in_range
            and self.volume_large_enough
            and self.volume_small_enough
            and (climate is None or climate)
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a SpecialRoomReverberationCheck has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot :math:`T/T_\mathrm{nom}` within the limiting curves, laid out
        as Figure B.3 of the standard, with the limits widening above the
        6,3 kHz band as the text of 6.3 says (the figure widens them at
        6,3 kHz already; see ``docs/ERRATA.md``).

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the measured curve.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_special_room_reverberation

        return plot_special_room_reverberation(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _climate_change(
    test: tuple[float | None, float | None],
    reference: tuple[float | None, float | None],
) -> float:
    """The relative change of H (theta + 5) of 6.6, ``NaN`` when not given.

    :param test: ``(relative humidity %, temperature degC)`` of the test.
    :param reference: The same while the reverberation time was measured.
    :raises ValueError: for a climate given in part, a humidity outside
        (0, 100] or a temperature at or below -5 degC, where the product is
        not positive.
    """
    humidity, temperature = test
    humidity_ref, temperature_ref = reference
    if (
        humidity is None
        and temperature is None
        and humidity_ref is None
        and (temperature_ref is None)
    ):
        return math.nan
    if (
        humidity is None
        or temperature is None
        or humidity_ref is None
        or (temperature_ref is None)
    ):
        msg = (
            "The climate check of 6.6 needs the relative humidity and the "
            "temperature both of the test and of the reverberation measurement."
        )
        raise ValueError(msg)
    for rh in (humidity, humidity_ref):
        if not math.isfinite(rh) or rh <= 0.0 or rh > 100.0:  # noqa: PLR2004
            msg = "Relative humidities must be in (0, 100] per cent."
            raise ValueError(msg)
    for theta in (temperature, temperature_ref):
        if not math.isfinite(theta) or theta <= -_CLIMATE_OFFSET_C:
            msg = "Temperatures must be finite and above -5 degC for Formula (2)."
            raise ValueError(msg)
    product = humidity * (temperature + _CLIMATE_OFFSET_C)
    product_ref = humidity_ref * (temperature_ref + _CLIMATE_OFFSET_C)
    return product / product_ref - 1.0


def check_special_room_reverberation(
    reverberation_time_s: ArrayLike,
    frequencies: ArrayLike,
    *,
    volume_m3: float,
    nominal_reverberation_time_s: float | None = None,
    surface_area_m2: float | None = None,
    speed_of_sound: float | None = None,
    method: Method = "direct",
    relative_humidity_percent: float | None = None,
    temperature_c: float | None = None,
    reverberation_relative_humidity_percent: float | None = None,
    reverberation_temperature_c: float | None = None,
    source_volume_m3: float | None = None,
) -> SpecialRoomReverberationCheck:
    r"""Is this room's reverberation time the one ISO 3743-2:2018 prescribes?
    6.2, 6.3 and 6.6.

    The measured reverberation time shall lie between :math:`0{,}9\,R\,
    T_\mathrm{nom}` and :math:`1{,}1\,R\,T_\mathrm{nom}` in every band (0,8
    and 1,2 above 6,3 kHz), with :math:`R` from Formula (1) or its NOTE
    (:func:`reverberation_parameter`), and :math:`T_\mathrm{nom}` between
    0,5 s and 1,0 s. Annex B finds :math:`T_\mathrm{nom}` "by centring the
    measured values of T (normalized to the reverberation time at 1 000 Hz)
    within the limiting curves" (B.5) and prints no rule for it. The library
    takes the one whose verdict is the requirement of 6.3 itself: the
    :math:`T_\mathrm{nom}` that leaves the most margin, minimising the largest
    deviation of any band from the ideal curve measured against that band's
    own tolerance, so that a room passes whenever some :math:`T_\mathrm{nom}`
    puts every band within its curves. If the curve is followed exactly this
    gives Formula (B.2),
    :math:`T_\mathrm{nom} = T_{1\,000}/R(1\,000\ \mathrm{Hz})`.

    The EXAMPLE of B.5 departs from this rule. On the curve of Figure B.4 it
    reads :math:`T/T_\mathrm{nom}` = 1,09 at 1 kHz and
    :math:`T_\mathrm{nom}` = 0,8 s/1,09 = 0,73 s, where the rule gives 1,05
    and 0,76 s, 0,17 dB apart in the :math:`L_W` of Formula (9). The 1,09 is
    the midpoint of the extreme ratios taken against the 0,9 and 1,1 limits
    alone, the wider limits above 6,3 kHz left out, and it puts the 250 Hz
    band of Figure B.4 at 1,13 R, above the 1,1 R within which the NOTE to
    Figure B.3 says the data are centred; Figure B.3 draws that band, and
    those at 100 Hz and 10 kHz, where 1,09 does not put them (see
    ``docs/ERRATA.md``). A value supplied in ``nominal_reverberation_time_s``,
    the printed 0,73 s among them, is checked as given instead.

    6.2 adds the volume: at least 70 m³, and at most 300 m³ when the 4 kHz
    and 8 kHz octaves are within the frequency range, which the direct method
    needs and the comparison method does not (NOTE). 6.6 adds the climate:
    the product :math:`H(\theta + 5\ ^\circ\mathrm{C})` during the test shall
    stay within ±10 % of its value while the reverberation time was measured,
    checked when all four climate values are given. Clause 5 recommends a
    noise source of at most 1 % of the room's volume, 0,7 m³ in a room of
    70 m³; given ``source_volume_m3``, the check reads it, and warns above it,
    but keeps it out of the verdict, the clause saying "should".

    :param reverberation_time_s: Measured reverberation time per band, in
        seconds, in one-third-octave bands as Figure B.3 has them.
    :param frequencies: Band centre frequencies, in hertz.
    :param volume_m3: Volume of the test room, in cubic metres.
    :param nominal_reverberation_time_s: :math:`T_\mathrm{nom}` to check, in
        seconds; ``None`` centres it.
    :param surface_area_m2: Room surface area for the NOTE form of
        :math:`R`, in square metres, with ``speed_of_sound``.
    :param speed_of_sound: Speed of sound for the NOTE form, in metres per
        second.
    :param method: ``'direct'`` (default) or ``'comparison'``, for the
        300 m³ ceiling.
    :param relative_humidity_percent: Relative humidity during the test, in
        per cent.
    :param temperature_c: Temperature during the test, in degrees Celsius.
    :param reverberation_relative_humidity_percent: Relative humidity while
        the reverberation time was measured, in per cent.
    :param reverberation_temperature_c: Temperature while the reverberation
        time was measured, in degrees Celsius.
    :param source_volume_m3: Volume of the noise source to be tested, in
        cubic metres, for the recommendation of clause 5; ``None`` skips it.
    :return: The verdict, as a :class:`SpecialRoomReverberationCheck`.
    :raises ValueError: for reverberation times that are not positive and
        finite, a length mismatch, the refusals of
        :func:`reverberation_parameter`, an unknown method, a climate given
        in part or out of range, or a source volume that is not positive.
    """
    t = np.asarray(reverberation_time_s, dtype=np.float64)
    if t.ndim != 1 or t.size == 0 or not np.all(np.isfinite(t)) or np.any(t <= 0.0):
        msg = "'reverberation_time_s' must be a 1D array of positive, finite seconds."
        raise ValueError(msg)
    freqs = np.asarray(frequencies, dtype=np.float64)
    if freqs.shape != t.shape:
        msg = "'frequencies' must carry one value per reverberation time."
        raise ValueError(msg)
    chosen = require_choice(method, "method", ("direct", "comparison"))
    r = reverberation_parameter(
        freqs,
        volume_m3,
        surface_area_m2=surface_area_m2,
        speed_of_sound=speed_of_sound,
    )
    half_width = _tolerance(freqs)
    if nominal_reverberation_time_s is None:
        nominal = 1.0 / _centred_scale(t / r, half_width)
        centred = True
    else:
        nominal = require_positive(
            nominal_reverberation_time_s, "nominal_reverberation_time_s"
        )
        centred = False
    change = _climate_change(
        (relative_humidity_percent, temperature_c),
        (reverberation_relative_humidity_percent, reverberation_temperature_c),
    )
    source = (
        math.nan
        if source_volume_m3 is None
        else require_positive(source_volume_m3, "source_volume_m3")
    )
    check = SpecialRoomReverberationCheck(
        frequencies=freqs.copy(),
        reverberation_time_s=t.copy(),
        reverberation_parameter=np.asarray(r, dtype=np.float64),
        nominal_reverberation_time_s=float(nominal),
        centred=centred,
        lower_limit=np.asarray(1.0 - half_width, dtype=np.float64),
        upper_limit=np.asarray(1.0 + half_width, dtype=np.float64),
        volume_m3=float(volume_m3),
        method=chosen,
        climate_product_change=change,
        source_volume_m3=float(source),
    )
    if check.source_size_recommended is False:
        warnings.warn(
            f"The noise source is {source:g} m³ in a room of {volume_m3:g} m³; "
            f"clause 5 recommends at most {100.0 * _SOURCE_VOLUME_FRACTION:g} % of the "
            f"room, {_SOURCE_VOLUME_FRACTION * volume_m3:g} m³ ({_STANDARD}).",
            SoundPowerWarning,
            stacklevel=2,
        )
    return check


@dataclass(frozen=True)
class SpecialRoomSurfaceCheck:
    r"""Qualification of a special reverberation test room by its surfaces
    (ISO 3743-2:2018, 6.4).

    ``surface_absorption`` holds the mean absorption coefficient of each wall
    and of the ceiling per octave band, ``(surfaces, bands)``,
    ``floor_absorption`` that of the floor, and ``mean_absorption`` the mean of
    the walls and ceiling that each is compared with, weighted by their areas
    when those were given.
    """

    frequencies: np.ndarray
    surface_absorption: np.ndarray
    floor_absorption: np.ndarray
    mean_absorption: np.ndarray

    def __post_init__(self) -> None:
        """Reject a check whose arrays disagree.

        :raises ValueError: if the band counts or ranks differ.
        """
        require_ranks(
            self,
            frequencies=1,
            surface_absorption=2,
            floor_absorption=1,
            mean_absorption=1,
        )
        require_same_length(
            self,
            "frequencies",
            ("surface_absorption", 1),
            "floor_absorption",
            "mean_absorption",
        )

    @property
    def surface_ratio(self) -> np.ndarray:
        """Each wall's and the ceiling's coefficient over the mean, per band;
        1 where the mean is zero, since every surface then absorbs alike.
        """
        mean = np.broadcast_to(self.mean_absorption, self.surface_absorption.shape)
        return np.asarray(
            np.divide(
                self.surface_absorption,
                mean,
                out=np.ones_like(self.surface_absorption),
                where=mean > 0.0,
            ),
            dtype=np.float64,
        )

    @property
    def surface_within(self) -> np.ndarray:
        """Per wall or ceiling and band, ``(surfaces, bands)``, whether the
        coefficient lies within 0,5 and 1,5 times the mean.
        """
        ratio = _settled(self.surface_ratio)
        return np.asarray(
            (ratio >= _SURFACE_RATIO_MIN) & (ratio <= _SURFACE_RATIO_MAX), dtype=bool
        )

    @property
    def surfaces_uniform(self) -> np.ndarray:
        """Per band, whether every wall and the ceiling lie within 0,5 and 1,5
        times the mean.
        """
        return np.asarray(np.all(self.surface_within, axis=0), dtype=bool)

    @property
    def floor_reflective(self) -> np.ndarray:
        """Per band, whether the floor absorbs less than 0,06."""
        return np.asarray(
            _settled(self.floor_absorption) < _FLOOR_MAX_ABSORPTION, dtype=bool
        )

    @property
    def passes(self) -> bool:
        """Whether both criteria of 6.4 hold in every band."""
        return bool(np.all(self.surfaces_uniform) and np.all(self.floor_reflective))

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a SpecialRoomSurfaceCheck has no truth value; read its '.passes' "
            "for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot each surface's coefficient within the 0,5 to 1,5 band of the
        mean, and the floor against its 0,06, with every coefficient outside
        6.4 ringed and the verdict in the title.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the surface curves.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_special_room_surfaces

        return plot_special_room_surfaces(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _coefficients(value: ArrayLike, name: str, ndim: int) -> np.ndarray:
    """Absorption coefficients of the given rank, finite and in [0, 1]."""
    arr = np.asarray(value, dtype=np.float64)
    if (
        arr.ndim != ndim
        or arr.size == 0
        or not np.all(np.isfinite(arr))
        or np.any(arr < 0.0)
        or np.any(arr > 1.0)
    ):
        msg = f"'{name}' must be a {ndim}D array of absorption coefficients in [0, 1]."
        raise ValueError(msg)
    return arr


def check_special_room_surfaces(
    surface_absorption_coefficients: ArrayLike,
    floor_absorption_coefficients: ArrayLike,
    frequencies: ArrayLike,
    *,
    surface_areas_m2: ArrayLike | None = None,
) -> SpecialRoomSurfaceCheck:
    """Are the room's surfaces treated as ISO 3743-2:2018, 6.4 asks?

    The floor shall be reflective, its absorption coefficient below 0,06, and
    apart from the floor no surface may absorb significantly differently from
    the others: in each octave band the mean absorption coefficient of each
    wall and of the ceiling lies within 0,5 and 1,5 times the mean of the
    walls and ceiling. The clause does not say how that mean is formed; with
    ``surface_areas_m2`` it is weighted by area, which is the room's own mean,
    and without them it is the plain mean of the surfaces.

    :param surface_absorption_coefficients: Mean absorption coefficient of
        each wall and of the ceiling, ``(surfaces, bands)``, at least two
        surfaces.
    :param floor_absorption_coefficients: The floor's coefficient per band.
    :param frequencies: Octave-band centre frequencies, in hertz.
    :param surface_areas_m2: Area of each wall and of the ceiling, in square
        metres, for the area-weighted mean; ``None`` for the plain mean.
    :return: The verdict, as a :class:`SpecialRoomSurfaceCheck`.
    :raises ValueError: for coefficients outside [0, 1], fewer than two
        surfaces, mismatched bands, or areas that are not one positive value
        per surface.
    """
    surfaces = _coefficients(
        surface_absorption_coefficients, "surface_absorption_coefficients", 2
    )
    n_surfaces, n_bands = surfaces.shape
    if n_surfaces < 2:  # noqa: PLR2004
        msg = "'surface_absorption_coefficients' must hold at least two surfaces."
        raise ValueError(msg)
    floor = _coefficients(
        floor_absorption_coefficients, "floor_absorption_coefficients", 1
    )
    freqs = np.asarray(frequencies, dtype=np.float64)
    if floor.shape != (n_bands,) or freqs.shape != (n_bands,):
        msg = (
            "'floor_absorption_coefficients' and 'frequencies' must carry one "
            f"value per band ({n_bands})."
        )
        raise ValueError(msg)
    if surface_areas_m2 is None:
        mean = surfaces.mean(axis=0)
    else:
        areas = np.asarray(surface_areas_m2, dtype=np.float64)
        if (
            areas.shape != (n_surfaces,)
            or not np.all(np.isfinite(areas))
            or np.any(areas <= 0.0)
        ):
            msg = f"'surface_areas_m2' must be one positive area per surface ({n_surfaces})."
            raise ValueError(msg)
        mean = (areas[:, None] * surfaces).sum(axis=0) / areas.sum()
    return SpecialRoomSurfaceCheck(
        frequencies=freqs.copy(),
        surface_absorption=surfaces.copy(),
        floor_absorption=floor.copy(),
        mean_absorption=np.asarray(mean, dtype=np.float64),
    )


@dataclass(frozen=True)
class SpecialRoomSuitabilityCheck:
    """The suitability evaluation of ISO 3743-2:2018, 6.7 (Table 1).

    ``difference_db`` is, per octave band, the sound power level of a
    calibrated broad-band reference source determined in the room less its
    calibrated value, and ``limit_db`` the Table 1 bound on its magnitude.
    """

    frequencies: np.ndarray
    difference_db: np.ndarray
    limit_db: np.ndarray

    def __post_init__(self) -> None:
        """Reject a check whose per-band arrays disagree.

        :raises ValueError: if the arrays differ in length or rank.
        """
        require_ranks(self, frequencies=1, difference_db=1, limit_db=1)
        require_same_length(self, "frequencies", "difference_db", "limit_db")

    @property
    def band_within(self) -> np.ndarray:
        """Per band, whether the difference stays within Table 1."""
        return np.asarray(
            _settled(np.abs(self.difference_db)) <= self.limit_db, dtype=bool
        )

    @property
    def passes(self) -> bool:
        """Whether the room is suitable for broad-band sources (step 4 of 6.7)."""
        return bool(np.all(self.band_within))

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = (
            "a SpecialRoomSuitabilityCheck has no truth value; read its "
            "'.passes' for the verdict"
        )
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the difference per band within the ± Table 1 limits.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the difference bars.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_special_room_suitability

        return plot_special_room_suitability(
            self, ax=ax, language=check_language(language), **kwargs
        )


def _table_bands(frequencies: ArrayLike, n_bands: int, table: str) -> np.ndarray:
    """Octave centres from 125 Hz to 8 kHz, the bands Tables 1, 3 and 5 cover."""
    freqs = _octave_frequencies(frequencies, n_bands, _TABLE_F1)
    if any(round(float(f)) not in _TABLE1_DB for f in freqs):
        msg = f"'frequencies' must lie in 125 Hz to 8 kHz, the bands of {table}."
        raise ValueError(msg)
    return freqs


def check_special_room_suitability(
    measured_power_levels: ArrayLike,
    calibrated_power_levels: ArrayLike,
    frequencies: ArrayLike,
) -> SpecialRoomSuitabilityCheck:
    """Is the room suitable for broad-band sources? ISO 3743-2:2018, 6.7.

    A small broad-band reference sound source calibrated by ISO 3741, or by
    ISO 6926 and ISO 3745 (step 1), has its octave-band power levels
    determined in the room by this standard (step 2); the differences from
    the calibration (step 3) may not exceed Table 1 (step 4): ±5 dB at
    125 Hz, ±3 dB from 250 Hz to 4 kHz and ±4 dB at 8 kHz.

    :param measured_power_levels: The reference source's octave-band power
        levels determined in the room, in decibels.
    :param calibrated_power_levels: Its calibrated levels, in decibels.
    :param frequencies: Octave centres from 125 Hz to 8 kHz, ascending.
    :return: The verdict, as a :class:`SpecialRoomSuitabilityCheck`.
    :raises ValueError: for non-finite levels, mismatched lengths, or bands
        outside Table 1.
    """
    measured = _finite(measured_power_levels, "measured_power_levels", (1,))
    calibrated = _finite(calibrated_power_levels, "calibrated_power_levels", (1,))
    if calibrated.shape != measured.shape:
        msg = "'calibrated_power_levels' must carry one value per band."
        raise ValueError(msg)
    freqs = _table_bands(frequencies, measured.size, f"{_STANDARD}, Table 1")
    return SpecialRoomSuitabilityCheck(
        frequencies=freqs,
        difference_db=np.asarray(measured - calibrated, dtype=np.float64),
        limit_db=np.array([_TABLE1_DB[round(float(f))] for f in freqs]),
    )


def _band_group(frequency: float) -> str:
    """The row group of Table 3 a band belongs to."""
    nominal = round(frequency)
    return str(nominal) if nominal in (125, 250, 500) else "high"


def _sm_class(s_m: float) -> str:
    """The 9.5 reading of s_M, which is also the row block of Table 3."""
    settled = float(_settled(s_m))
    if settled < _SM_BROADBAND_BELOW_DB:
        return "broadband"
    if settled <= _SM_NARROW_BAND_UP_TO_DB:
        return "narrow-band"
    return "discrete tone"


def _survey_deviation(levels: np.ndarray) -> np.ndarray:
    r""":math:`s_\mathrm{M}` of Formula (4) about the mean 9.4 prescribes.

    The mean is arithmetic when the range of the levels is not greater than
    5 dB and the energy mean of Formula (5) otherwise; the range is settled
    first, so that levels 5,0 dB apart as read keep the arithmetic mean
    whatever their difference is in binary. The deviation is then taken
    about that mean with the divisor :math:`n - 1`, as printed.
    """
    arr = levels
    spread = _settled(np.ptp(arr, axis=0))
    mean = np.where(
        spread <= _ARITHMETIC_MEAN_RANGE_DB,
        arr.mean(axis=0),
        energy_mean(arr, axis=0),
    )
    n = arr.shape[0]
    return np.asarray(np.sqrt(np.sum((arr - mean) ** 2, axis=0) / (n - 1)))


def special_room_source_locations(
    levels: ArrayLike,
    frequencies: ArrayLike,
    *,
    microphone_positions: int = _SURVEY_MICROPHONES,
    a_weighted_levels: ArrayLike | None = None,
) -> SourceLocationPlan:
    r"""The number of source locations for a number of microphone positions,
    from the survey of ISO 3743-2:2018, 9.4 (Table 3), and the spectral
    character of 9.5.

    At one source location, six microphone positions record the sound
    pressure level (step 1), and per octave band and for A-weighting

    .. math::

       s_\mathrm{M} = (n - 1)^{-1/2} \left[ \sum_{i=1}^{n}
       \left(L_{pi} - \overline{L_p}\right)^2 \right]^{1/2}
       \tag{Formula 4}

    about the arithmetic mean when the six levels span no more than 5 dB and
    about their energy mean (Formula 5) when they span more (step 2). Table 3
    then gives the minimum number of source locations for 3, 6 or 12
    microphone positions (step 3), by :math:`s_\mathrm{M}` class (below
    2,3 dB, 2,3 dB to 4 dB, above 4 dB) and band. The same classes read the
    spectrum (9.5): broad-band below 2,3 dB, narrow-band components possible
    up to 4 dB, a discrete tone possible above; their suspected presence
    shall be reported.

    :param levels: Survey levels, ``(n, bands)``, six rows in 9.4, in
        decibels.
    :param frequencies: Octave centres from 125 Hz to 8 kHz, ascending.
    :param microphone_positions: The column of Table 3 to read, 3, 6
        (default) or 12.
    :param a_weighted_levels: The six A-weighted levels, ``(n,)``, for the
        A-weighted row; ``None`` leaves it unevaluated.
    :return: The :class:`SourceLocationPlan`.
    :raises ValueError: for levels that are not a finite 2D array of at least
        two positions, bands outside 125 Hz to 8 kHz, a column Table 3 does
        not have, or A-weighted levels not one per position.
    """
    arr = _finite(levels, "levels", (2,))
    n_positions, n_bands = arr.shape
    if n_positions < 2:  # noqa: PLR2004
        msg = "'levels' must hold at least two microphone positions for Formula (4)."
        raise ValueError(msg)
    if n_positions != _SURVEY_MICROPHONES:
        warnings.warn(
            f"{n_positions} microphone position(s) were surveyed; step 1 of 9.4 "
            f"uses {_SURVEY_MICROPHONES} ({_STANDARD}).",
            SoundPowerWarning,
            stacklevel=2,
        )
    if microphone_positions not in _TABLE3_MICROPHONES:
        msg = (
            "'microphone_positions' must be one of the columns of Table 3, "
            f"{_TABLE3_MICROPHONES}; got {microphone_positions!r}."
        )
        raise ValueError(msg)
    column = _TABLE3_MICROPHONES.index(microphone_positions)
    freqs = _table_bands(frequencies, n_bands, f"{_STANDARD}, Table 3")
    s_m = _survey_deviation(arr)
    classes = tuple(_sm_class(float(s)) for s in s_m)
    locations = np.array(
        [
            _TABLE3[cls][_band_group(float(f))][column]
            for cls, f in zip(classes, freqs, strict=True)
        ],
        dtype=np.int64,
    )
    s_a = math.nan
    n_a = 0
    class_a: str | None = None
    if a_weighted_levels is not None:
        a_levels = _finite(a_weighted_levels, "a_weighted_levels", (1,))
        if a_levels.shape != (n_positions,):
            msg = f"'a_weighted_levels' must carry one level per position ({n_positions})."
            raise ValueError(msg)
        s_a = float(_survey_deviation(a_levels[:, None])[0])
        class_a = _sm_class(s_a)
        n_a = _TABLE3[class_a]["A"][column]
    return SourceLocationPlan(
        standard=_STANDARD,
        frequencies=freqs,
        standard_deviation_db=np.asarray(s_m, dtype=np.float64),
        source_locations=locations,
        additional_room_locations=np.zeros(n_bands, dtype=np.int64),
        microphone_positions=int(microphone_positions),
        spectral_character=classes,
        a_weighted_standard_deviation_db=s_a,
        a_weighted_source_locations=n_a,
        a_weighted_spectral_character=class_a,
    )


@dataclass(frozen=True)
class SpecialRoomSoundPowerResult:
    r"""Result of an ISO 3743-2:2018 determination in a special reverberation
    test room.

    ``method`` is ``'direct'`` (Formula 9) or ``'comparison'`` (Formula 10).
    ``sound_power_level`` is the octave-band :math:`L_W` at the
    meteorological conditions of the test; the ``..._ref`` properties add the
    Annex E correction ``c2``, which 10.2 and 10.3 require above 500 m.

    ``mean_pressure_level`` is the mean background-corrected level of the
    source under test, :math:`\overline{L_p}` (Formula 8) or
    :math:`L_{p\mathrm{e}}`, and ``background_correction`` the per-band shift
    the Table 4 corrections made to it. ``background_requirement_met`` is
    ``True`` only where a background was measured and every margin, of the
    source and, for the comparison method, of the reference source, reached
    the 4 dB of 6.5 and 9.8. For the comparison method
    ``mean_reference_level`` is :math:`L_{p\mathrm{r}}` and
    ``reference_power_level`` :math:`L_{W\mathrm{r}}`; for the direct method
    both are ``NaN`` and ``volume_m3`` and ``nominal_reverberation_time_s``
    carry the room instead (``NaN`` for the comparison method).

    ``sound_power_level_a`` is the Annex F total of the octave bands;
    ``sound_power_level_a_direct`` is Formula (9) applied to the mean
    A-weighted level ``mean_a_weighted_level``, which is how clause 4 reads
    the A-weighted level of the direct method, both ``NaN`` where the
    A-weighted levels were not measured or the method is the comparison one;
    ``background_requirement_met_a`` is the 4 dB test of 6.5 on the
    A-weighted levels, ``False`` where there was nothing to test.
    ``sigma_r0`` is Table 5 per band (``NaN`` at 63 Hz) and ``sigma_r0_a`` its
    A-weighted row; the uncertainty properties follow Formulae (12) and (13).
    """

    frequencies: np.ndarray
    sound_power_level: np.ndarray
    mean_pressure_level: np.ndarray
    background_correction: np.ndarray
    background_requirement_met: np.ndarray
    mean_reference_level: np.ndarray
    reference_power_level: np.ndarray
    volume_m3: float
    nominal_reverberation_time_s: float
    c2: float
    sigma_r0: np.ndarray
    sigma_r0_a: float
    sigma_omc: float
    coverage_factor: float
    sound_power_level_a: float
    sound_power_level_a_direct: float
    mean_a_weighted_level: float
    background_requirement_met_a: bool
    method: str
    microphone_positions: int
    source_positions: int

    def __post_init__(self) -> None:
        """Reject a result whose per-band quantities disagree or whose tags
        are not the ones the standard has.

        :raises ValueError: if ``method`` is unknown, ``coverage_factor`` is not
            positive, a count is below one, or a per-band array disagrees with
            the rest.
        """
        require_choice(self.method, "method", ("direct", "comparison"))
        require_positive(self.coverage_factor, "coverage_factor")
        if self.microphone_positions < 1 or self.source_positions < 1:
            msg = (
                "SpecialRoomSoundPowerResult: 'microphone_positions' and "
                "'source_positions' must be at least 1."
            )
            raise ValueError(msg)
        bands = (
            "frequencies",
            "sound_power_level",
            "mean_pressure_level",
            "background_correction",
            "background_requirement_met",
            "mean_reference_level",
            "reference_power_level",
            "sigma_r0",
        )
        require_ranks(self, **dict.fromkeys(bands, 1))
        require_same_length(self, *bands)

    @property
    def sigma_tot(self) -> np.ndarray:
        """Formula (12) per band, in decibels; ``NaN`` without ``sigma_omc``."""
        return np.asarray(np.hypot(self.sigma_r0, self.sigma_omc), dtype=np.float64)

    @property
    def sigma_tot_a(self) -> float:
        """Formula (12) with the A-weighted row of Table 5, in decibels."""
        return float(math.hypot(self.sigma_r0_a, self.sigma_omc))

    @property
    def expanded_uncertainty(self) -> np.ndarray:
        """``U = k sigma_tot`` per band (Formula 13), in decibels."""
        return np.asarray(self.coverage_factor * self.sigma_tot, dtype=np.float64)

    @property
    def expanded_uncertainty_a(self) -> float:
        """``U`` of the A-weighted level (Formula 13), in decibels: 5,7 dB for
        ``sigma_omc`` = 2,0 dB and ``k`` = 2, the 11.5 EXAMPLE.
        """
        return float(self.coverage_factor * self.sigma_tot_a)

    @property
    def sound_power_level_ref(self) -> np.ndarray:
        """``LW + C2`` under the reference meteorological conditions (E.1)."""
        return np.asarray(self.sound_power_level + self.c2, dtype=np.float64)

    @property
    def sound_power_level_a_ref(self) -> float:
        """The Annex F total of :attr:`sound_power_level_ref`, ``LWA + C2``."""
        return float(self.sound_power_level_a + self.c2)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the octave-band spectrum with the A-weighted total annotated.

        A band whose background margin fell below 4 dB is hatched as not
        meeting 9.8, and the expanded uncertainty is drawn as an error bar
        where ``sigma_omc`` was given. Requires matplotlib
        (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the band bars.
        :return: The axes.
        """
        from .._i18n import check_language
        from .._plot.emission import plot_special_room_sound_power

        return plot_special_room_sound_power(
            self, ax=ax, language=check_language(language), **kwargs
        )

    def report(
        self,
        path: str,
        *,
        metadata: ReportMetadata | None = None,
        engine: str = "reportlab",
        verbose: bool = False,
        language: str = "en",
    ) -> str:
        """Render the ISO 3743-2 determination as a one-page test sheet.

        The sheet states the method and its accuracy grade (the direct or the
        comparison method in a special reverberation test room,
        ISO 3743-2:2018, grade 2), an optional metadata header, the per-band
        table of the mean level (and, for the comparison method, of the
        reference sound source) and the determined ``LW``, the spectrum, the
        boxed A-weighted level with the expanded uncertainty and its coverage
        factor, an optional verdict against a declared limit, and a basis strip
        with Formula 8 and Formula 9 or 10. The boxed level of the direct
        method is the one clause 4 describes, Formula (9) on the A-weighted
        sound pressure levels, where they were measured; the Annex F total of
        the octave bands is stated beside it. A band whose background
        requirement was not met is marked ``*`` and named beneath the table,
        as 9.8 asks.

        :param path: Destination path of the PDF file.
        :param metadata: Optional :class:`~phonometry.ReportMetadata` for the
            header, the footer identity and, via ``requirement``, a declared
            A-weighted limit the boxed level is checked against (lower is
            better).
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: When ``True`` the table adds the per-band shift of the
            Table 4 background corrections.
        :param language: Sheet language: ``"en"`` (default) or ``"es"``.
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` is not ``"reportlab"`` or ``language``
            is unknown.
        :raises ImportError: If reportlab (or, for the figure, matplotlib) is
            not installed (``pip install phonometry[report]``).
        """
        from .._i18n import check_language

        check_language(language)
        check_engine(engine)
        from .._report.iso3743 import render_special_room_power_report

        return render_special_room_power_report(
            self, path, metadata=metadata, verbose=verbose, language=language
        )


def _measurement_grid(value: ArrayLike, name: str) -> tuple[np.ndarray, bool]:
    """Levels as ``(NS, NM, NB)`` and whether they came from a traverse."""
    arr = _finite(value, name, (1, 2, 3))
    if arr.ndim == 1:
        return arr[None, None, :], True
    if arr.ndim == 2:  # noqa: PLR2004
        return arr[None, :, :], False
    return arr, False


def _background_grid(
    value: ArrayLike, name: str, n_positions: int, n_bands: int
) -> np.ndarray:
    """A background as ``(NM, NB)``: one spectrum for every position, or one
    per position.
    """
    arr = _finite(value, name, (1, 2))
    if arr.ndim == 1:
        if arr.shape != (n_bands,):
            msg = f"'{name}' must carry one value per band ({n_bands})."
            raise ValueError(msg)
        return np.broadcast_to(arr, (n_positions, n_bands)).copy()
    if arr.shape != (n_positions, n_bands):
        msg = (
            f"'{name}' must be one spectrum or one per microphone position "
            f"({n_positions} positions, {n_bands} bands)."
        )
        raise ValueError(msg)
    return arr


def _corrected_mean(
    grid: np.ndarray, background: np.ndarray | None
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Formula (8) over every measurement after the Table 4 correction.

    :param grid: Levels ``(NS, NM, NB)``.
    :param background: Background ``(NM, NB)`` read at each position, or
        ``None``.
    :return: ``(corrected mean, shift from the uncorrected mean, margin met per
        band)``; with no background the shift is zero and nothing is met.
    """
    flat = grid.reshape(-1, grid.shape[-1])
    raw = np.asarray(energy_mean(flat, axis=0), dtype=np.float64)
    if background is None:
        return raw, np.zeros_like(raw), np.zeros(raw.shape, dtype=bool)
    correction, met = _table4_correction(grid - background[None, :, :])
    corrected = np.asarray(
        energy_mean((grid - correction).reshape(-1, grid.shape[-1]), axis=0),
        dtype=np.float64,
    )
    return corrected, raw - corrected, np.all(met.reshape(-1, grid.shape[-1]), axis=0)


def _table5_sigma(frequencies: np.ndarray) -> np.ndarray:
    """Table 5 per band; ``NaN`` at 63 Hz, which the table does not reach."""
    return np.array(
        [_SIGMA_R0_DB.get(round(float(f)), math.nan) for f in frequencies],
        dtype=np.float64,
    )


def _background_advisory(
    requirement: np.ndarray, *, measured: bool, stacklevel: int
) -> None:
    """Warn when a band cannot be reported as meeting 6.5 and 9.8."""
    if not measured:
        warnings.warn(
            "No background levels were supplied; 6.5 checks the background at "
            f"each microphone position ({_STANDARD}), so no band can be reported "
            "as meeting it.",
            SoundPowerWarning,
            stacklevel=stacklevel,
        )
    elif not np.all(requirement):
        warnings.warn(
            "A background margin is below 4 dB in one or more bands; Table 4 "
            "has no row for it and those levels can be reported only as not "
            f"meeting the background requirement ({_STANDARD}, 9.8).",
            SoundPowerWarning,
            stacklevel=stacklevel,
        )


def _room_advisories(
    volume: float, nominal: float, freqs: np.ndarray, stacklevel: int
) -> None:
    """Warn when the room of a direct determination is outside 6.2 or 6.3."""
    if volume < _MIN_VOLUME_M3:
        warnings.warn(
            f"The room is {volume:g} m³; a special reverberation test room is "
            f"at least {_MIN_VOLUME_M3:g} m³ ({_STANDARD}, 6.2).",
            SoundPowerWarning,
            stacklevel=stacklevel,
        )
    if (
        volume > _MAX_VOLUME_HIGH_OCTAVES_M3
        and np.max(freqs) >= _EIGHT_KHZ_OCTAVE_LOWER_EDGE_HZ
    ):
        warnings.warn(
            f"The room is {volume:g} m³ and the 8 kHz octave is measured; the "
            f"direct method then needs at most {_MAX_VOLUME_HIGH_OCTAVES_M3:g} m³ "
            f"({_STANDARD}, 6.2).",
            SoundPowerWarning,
            stacklevel=stacklevel,
        )
    if not _TNOM_MIN_S <= nominal <= _TNOM_MAX_S:
        warnings.warn(
            f"The nominal reverberation time is {nominal:g} s; 6.3 puts it "
            f"between {_TNOM_MIN_S:g} s and {_TNOM_MAX_S:g} s ({_STANDARD}).",
            SoundPowerWarning,
            stacklevel=stacklevel,
        )


def _microphone_advisory(n_positions: int, *, traverse: bool, stacklevel: int) -> None:
    """Warn below the three microphone positions of the first Table 3 column."""
    if not traverse and n_positions < _MIN_MICROPHONES:
        warnings.warn(
            f"{n_positions} microphone position(s) were supplied; Table 3 starts "
            f"at {_MIN_MICROPHONES} and 9.4 generally needs 6 ({_STANDARD}).",
            SoundPowerWarning,
            stacklevel=stacklevel,
        )


def _a_weighted_mean(
    levels: ArrayLike, background: ArrayLike | None
) -> tuple[float, bool]:
    """Formula (8) over the A-weighted levels after Table 4, and whether every
    margin reached 4 dB (``False`` without a background).

    :param levels: One traverse level, one per position ``(NM,)`` or one per
        source location and position ``(NS, NM)``.
    :param background: One level for every position, one per position
        ``(NM,)``, or ``None``.
    """
    arr = _finite(levels, "a_weighted_levels", (0, 1, 2))
    if background is None:
        return float(energy_mean(arr.reshape(-1))), False
    bg = _finite(background, "a_weighted_background_levels", (0, 1))
    if bg.ndim == 1 and (arr.ndim == 0 or arr.shape[-1] != bg.shape[0]):
        msg = (
            "'a_weighted_background_levels' must be one level, or one per "
            "microphone position of 'a_weighted_levels'."
        )
        raise ValueError(msg)
    correction, met = _table4_correction(arr - bg)
    return float(energy_mean((arr - correction).reshape(-1))), bool(np.all(met))


def _annex_f_total(level: np.ndarray, freqs: np.ndarray) -> float:
    """The Annex F total of the octave bands (Formula F.1)."""
    return energy_sum(level + _a_weighting_corrections(freqs))


def sound_power_special_room(
    levels: ArrayLike,
    frequencies: ArrayLike,
    *,
    volume_m3: float,
    nominal_reverberation_time_s: float,
    background_levels: ArrayLike | None = None,
    a_weighted_levels: ArrayLike | None = None,
    a_weighted_background_levels: ArrayLike | None = None,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    sigma_omc_db: float | None = None,
    coverage_factor: float = _COVERAGE_TWO_SIDED,
) -> SpecialRoomSoundPowerResult:
    r"""Sound power level in a special reverberation test room, direct method
    (ISO 3743-2:2018, 10.2).

    Every measured level is corrected for background noise by Table 4 at its
    own microphone position (9.8), the corrected levels are energy-averaged
    over all positions and source locations (Formula 8), and

    .. math::

       L_W = \overline{L_p} - 10 \log_{10}\frac{T_\mathrm{nom}}{T_0}
       + 10 \log_{10}\frac{V}{V_0} - 13\ \mathrm{dB} \tag{Formula 9}

    in each octave band. Given the A-weighted levels as well, the same
    formula gives the A-weighted sound power level directly, which is how
    clause 4 describes the method; ``sound_power_level_a`` is in any case the
    Annex F total of the octave bands.

    :param levels: Measured octave-band levels, in decibels: ``(bands,)`` for
        a microphone traverse, ``(NM, bands)`` for fixed positions, or
        ``(NS, NM, bands)`` for several source locations (9.4).
    :param frequencies: Nominal octave centres from 63 Hz to 8 kHz, ascending
        (Table F.1; 63 Hz under its footnote).
    :param volume_m3: Volume of the test room, in cubic metres.
    :param nominal_reverberation_time_s: :math:`T_\mathrm{nom}` of the room
        (6.3), in seconds, as
        :func:`check_special_room_reverberation` finds it.
    :param background_levels: Background levels, ``(NM, bands)`` or one
        ``(bands,)`` spectrum for every position, in decibels; ``None``
        applies no correction, warns, and leaves
        ``background_requirement_met`` ``False``.
    :param a_weighted_levels: The A-weighted levels measured with the source,
        one per position (``(NM,)`` or ``(NS, NM)``) or one traverse level, in
        decibels; ``None`` leaves the direct A-weighted level ``NaN``.
    :param a_weighted_background_levels: The A-weighted background, one level
        or one per position, in decibels.
    :param temperature_c: Air temperature at the test, in degrees Celsius.
    :param static_pressure_kpa: Static pressure at the test, in kilopascals.
    :param sigma_omc_db: Operating-and-mounting standard deviation (11.2), in
        decibels; ``None`` leaves the total and expanded uncertainty ``NaN``.
    :param coverage_factor: ``k`` of Formula (13), 2 by default.
    :return: :class:`SpecialRoomSoundPowerResult` with ``method='direct'``.
    :raises ValueError: for levels or a background of an inadmissible shape or
        not finite, frequencies outside Table F.1, a non-positive volume or
        nominal reverberation time, a climate out of range, a negative
        ``sigma_omc_db`` or a coverage factor that is not positive.
    """
    grid, traverse = _measurement_grid(levels, "levels")
    n_sources, n_positions, n_bands = grid.shape
    freqs = _octave_frequencies(frequencies, n_bands, _TABLE_F1)
    volume = require_positive(volume_m3, "volume_m3")
    nominal = require_positive(
        nominal_reverberation_time_s, "nominal_reverberation_time_s"
    )
    omc = _check_uncertainty_inputs(sigma_omc_db, coverage_factor)
    _validate_meteorology(temperature_c, static_pressure_kpa)
    _microphone_advisory(n_positions, traverse=traverse, stacklevel=3)
    _room_advisories(volume, nominal, freqs, stacklevel=3)
    background = (
        None
        if background_levels is None
        else _background_grid(
            background_levels, "background_levels", n_positions, n_bands
        )
    )
    mean, shift, met = _corrected_mean(grid, background)
    _background_advisory(met, measured=background is not None, stacklevel=3)
    room_term = (
        -10.0 * math.log10(nominal / _T0_S)
        + 10.0 * math.log10(volume / _V0_M3)
        - _DIRECT_CONSTANT_DB
    )
    level = np.asarray(mean + room_term, dtype=np.float64)
    mean_a = math.nan
    level_a_direct = math.nan
    met_a = False
    if a_weighted_levels is not None:
        mean_a, met_a = _a_weighted_mean(
            a_weighted_levels, a_weighted_background_levels
        )
        level_a_direct = mean_a + room_term
    nan_band = np.full(n_bands, np.nan, dtype=np.float64)
    return SpecialRoomSoundPowerResult(
        frequencies=freqs,
        sound_power_level=level,
        mean_pressure_level=mean,
        background_correction=np.asarray(shift, dtype=np.float64),
        background_requirement_met=np.asarray(met, dtype=bool),
        mean_reference_level=nan_band.copy(),
        reference_power_level=nan_band.copy(),
        volume_m3=volume,
        nominal_reverberation_time_s=nominal,
        c2=_c2_correction(temperature_c, static_pressure_kpa),
        sigma_r0=_table5_sigma(freqs),
        sigma_r0_a=_SIGMA_R0_A_DB,
        sigma_omc=omc,
        coverage_factor=float(coverage_factor),
        sound_power_level_a=_annex_f_total(level, freqs),
        sound_power_level_a_direct=level_a_direct,
        mean_a_weighted_level=mean_a,
        background_requirement_met_a=met_a,
        method="direct",
        microphone_positions=n_positions,
        source_positions=n_sources,
    )


def sound_power_special_room_comparison(
    levels: ArrayLike,
    levels_ref: ArrayLike,
    lw_ref: ArrayLike | ReferenceSourceCalibration,
    frequencies: ArrayLike,
    *,
    background_levels: ArrayLike | None = None,
    background_levels_ref: ArrayLike | None = None,
    temperature_c: float = 23.0,
    static_pressure_kpa: float = 101.325,
    sigma_omc_db: float | None = None,
    coverage_factor: float = _COVERAGE_TWO_SIDED,
) -> SpecialRoomSoundPowerResult:
    r"""Sound power level in a special reverberation test room, comparison
    method (ISO 3743-2:2018, 10.3).

    A reference source meeting Annex A stands on the floor at least 1,5 m from
    any wall; its mean octave-band level :math:`L_{p\mathrm{r}}` is determined
    at no fewer than six microphone positions, and that of the source under
    test, :math:`L_{p\mathrm{e}}`, as for the direct method, both after the
    Table 4 background correction (9.8) and the mean of Formula (8). Then

    .. math::

       L_{W\mathrm{e}} = L_{p\mathrm{e}} + \left(L_{W\mathrm{r}}
       - L_{p\mathrm{r}}\right) \tag{Formula 10}

    and the A-weighted level follows from the octave bands by Annex F (10.4).
    The room drops out, so neither its volume nor its reverberation time is
    needed, and the 300 m³ ceiling of 6.2 does not apply (NOTE).

    :param levels: Levels of the source under test, ``(bands,)``, ``(NM,
        bands)`` or ``(NS, NM, bands)``, in decibels.
    :param levels_ref: Levels of the reference source, ``(NMr, bands)``, at
        least six positions (10.3), or one traverse level ``(bands,)``.
    :param lw_ref: The reference source's calibrated octave-band power level
        :math:`L_{W\mathrm{r}}`, ``(bands,)``, in decibels, under the
        meteorological conditions of the test, since Formula (10) gives
        :math:`L_{W\mathrm{e}}` there (Annex E); or the
        :class:`~phonometry.emission.ReferenceSourceCalibration` of ISO 6926,
        whose one-third octave bands are summed into the octaves at
        ``frequencies`` and carried from the reference conditions to those of
        the test by its own ``C2`` (ISO 6926:2016, 8.4).
    :param frequencies: Nominal octave centres from 63 Hz to 8 kHz.
    :param background_levels: Background for the source under test, as in
        :func:`sound_power_special_room`.
    :param background_levels_ref: Background at the reference source's
        positions; ``None`` reuses ``background_levels`` when it fits them.
    :param temperature_c: Air temperature at the test, in degrees Celsius.
    :param static_pressure_kpa: Static pressure at the test, in kilopascals.
    :param sigma_omc_db: Operating-and-mounting standard deviation, in
        decibels.
    :param coverage_factor: ``k`` of Formula (13), 2 by default.
    :return: :class:`SpecialRoomSoundPowerResult` with ``method='comparison'``.
    :raises ValueError: for levels of an inadmissible shape, a reference
        spectrum of other bands, a background that fits neither source,
        frequencies outside Table F.1, a climate out of range, a negative
        ``sigma_omc_db``, a coverage factor that is not positive, or a
        calibration that does not cover the bands or used the manufacturer's
        ``C2``, whose value at the test only the manufacturer gives.
    """
    grid, traverse = _measurement_grid(levels, "levels")
    n_sources, n_positions, n_bands = grid.shape
    freqs = _octave_frequencies(frequencies, n_bands, _TABLE_F1)
    omc = _check_uncertainty_inputs(sigma_omc_db, coverage_factor)
    _validate_meteorology(temperature_c, static_pressure_kpa)
    _microphone_advisory(n_positions, traverse=traverse, stacklevel=3)
    ref_grid, ref_traverse = _measurement_grid(levels_ref, "levels_ref")
    if ref_grid.shape[0] != 1 or ref_grid.shape[2] != n_bands:
        msg = (
            f"'levels_ref' must be (positions, {n_bands} bands) or one traverse "
            f"({n_bands} bands,) spectrum of the reference source."
        )
        raise ValueError(msg)
    n_ref_positions = ref_grid.shape[1]
    if not ref_traverse and n_ref_positions < _SURVEY_MICROPHONES:
        warnings.warn(
            f"The reference source was measured at {n_ref_positions} position(s); "
            f"10.3 asks for no fewer than {_SURVEY_MICROPHONES} ({_STANDARD}).",
            SoundPowerWarning,
            stacklevel=2,
        )
    # Formula (10) gives the level under the conditions of the test (Annex E),
    # so a calibration is read there, less its own C2.
    power = _finite(
        _reference_power_levels(
            lw_ref,
            freqs,
            bandwidth="octave",
            temperature_c=temperature_c,
            static_pressure_kpa=static_pressure_kpa,
        ),
        "lw_ref",
        (1,),
    )
    if power.shape != (n_bands,):
        msg = f"'lw_ref' must carry one value per band ({n_bands})."
        raise ValueError(msg)
    background = (
        None
        if background_levels is None
        else _background_grid(
            background_levels, "background_levels", n_positions, n_bands
        )
    )
    ref_background_input = (
        background_levels if background_levels_ref is None else background_levels_ref
    )
    ref_background = (
        None
        if ref_background_input is None
        else _background_grid(
            ref_background_input, "background_levels_ref", n_ref_positions, n_bands
        )
    )
    mean, shift, met = _corrected_mean(grid, background)
    mean_ref, _, met_ref = _corrected_mean(ref_grid, ref_background)
    requirement = met & met_ref
    _background_advisory(requirement, measured=background is not None, stacklevel=3)
    level = np.asarray(mean + (power - mean_ref), dtype=np.float64)
    return SpecialRoomSoundPowerResult(
        frequencies=freqs,
        sound_power_level=level,
        mean_pressure_level=mean,
        background_correction=np.asarray(shift, dtype=np.float64),
        background_requirement_met=np.asarray(requirement, dtype=bool),
        mean_reference_level=np.asarray(mean_ref, dtype=np.float64),
        reference_power_level=power.copy(),
        volume_m3=math.nan,
        nominal_reverberation_time_s=math.nan,
        c2=_c2_correction(temperature_c, static_pressure_kpa),
        sigma_r0=_table5_sigma(freqs),
        sigma_r0_a=_SIGMA_R0_A_DB,
        sigma_omc=omc,
        coverage_factor=float(coverage_factor),
        sound_power_level_a=_annex_f_total(level, freqs),
        sound_power_level_a_direct=math.nan,
        mean_a_weighted_level=math.nan,
        background_requirement_met_a=False,
        method="comparison",
        microphone_positions=n_positions,
        source_positions=n_sources,
    )
