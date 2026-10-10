#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Sound of rain on roofs, roof windows and rooflights, measured in the
laboratory with artificial rain (ISO 10140-1:2021 Annex K, ISO 10140-5:2021
Annexes H and I).

Rain is an impact source that falls on the roof rather than a noise that comes
through it, so ISO 10140-1 measures it as impact sound: a tank with a
perforated base drops water on the specimen at a controlled rate, and the
sound radiated into the test room below is reported as a **sound intensity
level** :math:`L_I`, the sound power per unit area of the specimen referred to
:math:`10^{-12}` W/m² (K.1). Per unit area, because only part of a large roof
is wetted and the power scales with the area the rain actually excites.

**The rain.** Real rain is classed by rate, drop size and fall velocity
(Table K.1, after IEC 60721-2-2:1988, :data:`RAINFALL_CLASSIFICATION`). The
laboratory reproduces two of the classes at their upper limits, "since larger
drops produce most of the sound generated": heavy rain, 40 mm/h of 5 mm drops
at 7 m/s, which is mandatory and the one products are compared with, and
intense rain, 15 mm/h of 2 mm drops at 4 m/s (ISO 10140-5:2021 Table H.1,
:data:`ARTIFICIAL_RAIN`). The generator is checked by its rainfall rate, which
has to stay within 2 mm/h of the nominal value (:func:`verify_rain_generator`,
:func:`rainfall_rate`).

**The level.** From the room-averaged sound pressure level :math:`L_\mathrm{pr}`,
the reverberation time :math:`T` and the volume :math:`V` of the test room and
the area :math:`S_\mathrm{e}` the rain excites,

.. math::

   L_I = L_\mathrm{pr} - 10 \log_{10}(T/T_0) + 10 \log_{10}(V/V_0) - 14
   - 10 \log_{10}(S_\mathrm{e}/S_0)

(Formula (K.1), :math:`T_0 = 1` s, :math:`V_0 = 1` m³, :math:`S_0 = 1` m²),
which is the diffuse-field sound power :math:`L_p + 10 \log_{10}(A/4)` with the
Sabine area :math:`A = 0.16\,V/T` written out and divided by the excited area.
With three positions of the generator on a large specimen the three levels are
added energetically and :math:`S_\mathrm{e}` is three times the perforated area
of the tank (K.4.2). The alternative of K.4.3 measures the intensity directly,
:math:`L_I = L_{I\mathrm{m}} + 10 \log_{10}(S_\mathrm{m}/S_\mathrm{e})`
(Formula (K.4)). The 18 bands 100 Hz to 5 000 Hz combine into the A-weighted
level :math:`L_{I\mathrm{A}} = 10 \log_{10} \sum 10^{0.1(L_{Ij} + C_j)}`
(Formula (K.2)) with the :math:`C_j` of Table K.2 (:data:`RAINFALL_A_WEIGHTING`),
and three bands into an octave by Formula (K.3).

**The reference specimen.** For comparison between laboratories, the levels
are normalized with the result for a 6 mm glass pane of 1,25 m by 1,5 m under
heavy rain (K.6, ISO 10140-5:2021 Annex I): its measured level is corrected to
the reference loss factor of Table I.1, :math:`L_{I,\mathrm{m,ref}} =
L_{I,\mathrm{ref}} + 10 \log_{10}(\eta/\eta_\mathrm{ref})` with
:math:`\eta = 2.2/(f T_\mathrm{s})` (Formulas (I.1) and (I.2)), and the
difference from the reference level of the same table is the correction
:math:`\Delta L_{I\mathrm{c}} = L_{I,\mathrm{m,ref}} - L_{I\mathrm{c,ref}}`
(Formula (I.3)) that every later specimen subtracts,
:math:`L_{I\mathrm{norm}} = L_I - \Delta L_{I\mathrm{c}}` (Formula (K.5)).

Citations are to ISO 10140-1:2021 and ISO 10140-5:2021. Both tables of the
reference specimen and the rain types are printed identically in
ISO 10140-5:2010/Amd 1:2014, where they first appeared.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

import numpy as np

from ..._internal.display import RichDisplay
from ..._internal.frozen import OwnsArrays
from ..._internal.levels_math import energy_sum
from ..._internal.validation import (
    require_choice,
    require_equal_shapes,
    require_finite_array,
    require_positive,
    require_positive_array,
    require_ranks,
    require_same_length,
)
from .lab_insulation import background_correction

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

__all__ = [
    "ARTIFICIAL_RAIN",
    "RAINFALL_A_WEIGHTING",
    "RAINFALL_CLASSIFICATION",
    "RAINFALL_REFERENCE_INTENSITY_DB",
    "RAINFALL_REFERENCE_LOSS_FACTOR_DB",
    "ArtificialRain",
    "RainGeneratorVerification",
    "RainfallReferenceCorrection",
    "RainfallSoundResult",
    "RainfallType",
    "rainfall_rate",
    "rainfall_reference_correction",
    "rainfall_sound",
    "rainfall_sound_from_intensity",
    "verify_rain_generator",
]


@dataclass(frozen=True)
class RainfallType(RichDisplay):
    """One class of natural rain (ISO 10140-1:2021 Table K.1).

    Each quantity is a ``(lower, upper)`` pair; ``None`` is an open end: the
    table prints the three lighter classes as "up to" a rate and cloudburst as
    "greater than" every quantity.

    :ivar rainfall_rate_mm_h: Rainfall rate, in mm/h.
    :ivar drop_diameter_mm: Typical drop diameter, in mm.
    :ivar fall_velocity_m_s: Fall velocity, in m/s.
    """

    rainfall_rate_mm_h: tuple[float | None, float | None]
    drop_diameter_mm: tuple[float | None, float | None]
    fall_velocity_m_s: tuple[float | None, float | None]


#: The four classes of natural rain of ISO 10140-1:2021 Table K.1 (PDF page 54,
#: printed folio 48), after IEC 60721-2-2:1988, keyed ``"moderate"``,
#: ``"intense"``, ``"heavy"`` and ``"cloudburst"``. They describe real rain;
#: the laboratory reproduces only the intense and heavy classes, at their upper
#: limits (:data:`ARTIFICIAL_RAIN`).
RAINFALL_CLASSIFICATION: Mapping[str, RainfallType] = MappingProxyType(
    {
        "moderate": RainfallType((None, 4.0), (0.5, 1.0), (1.0, 2.0)),
        "intense": RainfallType((None, 15.0), (1.0, 2.0), (2.0, 4.0)),
        "heavy": RainfallType((None, 40.0), (2.0, 5.0), (5.0, 7.0)),
        "cloudburst": RainfallType((100.0, None), (3.0, None), (6.0, None)),
    }
)


@dataclass(frozen=True)
class ArtificialRain(RichDisplay):
    """One type of artificial rain and the tank that makes it (ISO 10140-5 Annex H).

    :ivar rainfall_rate_mm_h: Rainfall rate, in mm/h: the depth of water the
        rain would leave on a horizontal surface in one hour (Table H.1).
    :ivar median_drop_diameter_mm: Volume median drop diameter, in mm: half of
        the water falls in drops larger than it (Table H.1).
    :ivar fall_velocity_m_s: Fall velocity at the specimen, in m/s (Table H.1).
    :ivar hole_diameter_mm: Diameter of the holes in the perforated base, as a
        ``(lower, upper)`` range, in mm (Table H.2, row 1).
    :ivar holes_per_m2: Approximate number of holes per square metre of the
        base (Table H.2, row 2).
    :ivar fall_height_m: Approximate fall height from the base to the
        specimen, in m (Table H.2, row 3).
    :ivar rainfall_rate_tolerance_mm_h: How far the rainfall rate may depart
        from its nominal value, in mm/h (H.1).
    :ivar drop_diameter_tolerance_mm: Half-width of the window around the
        median drop diameter that half the drops should fall in, in mm (H.1).
    :ivar fall_velocity_tolerance_m_s: Half-width of the window around the
        fall velocity that half the drops should fall in, in m/s (H.1).
    """

    rainfall_rate_mm_h: float
    median_drop_diameter_mm: float
    fall_velocity_m_s: float
    hole_diameter_mm: tuple[float, float]
    holes_per_m2: float
    fall_height_m: float
    _: KW_ONLY
    rainfall_rate_tolerance_mm_h: float = 2.0
    drop_diameter_tolerance_mm: float = 0.5
    fall_velocity_tolerance_m_s: float = 1.0


#: The two artificial rains of ISO 10140-5:2021 Table H.1 (PDF page 39, printed
#: folio 33), with the tank of Table H.2 and the tolerances of H.1, keyed
#: ``"intense"`` and ``"heavy"``. Heavy rain is the mandatory one and the
#: standard rain for comparing products (ISO 10140-1:2021 K.4.1); intense rain
#: is recommended only where a lower rate is needed. ISO 10140-5:2010/Amd 1:2014
#: printed the same two tables.
ARTIFICIAL_RAIN: Mapping[str, ArtificialRain] = MappingProxyType(
    {
        "intense": ArtificialRain(
            rainfall_rate_mm_h=15.0,
            median_drop_diameter_mm=2.0,
            fall_velocity_m_s=4.0,
            hole_diameter_mm=(0.3, 0.5),
            holes_per_m2=25.0,
            fall_height_m=1.0,
        ),
        "heavy": ArtificialRain(
            rainfall_rate_mm_h=40.0,
            median_drop_diameter_mm=5.0,
            fall_velocity_m_s=7.0,
            hole_diameter_mm=(1.0, 1.0),
            holes_per_m2=60.0,
            fall_height_m=3.5,
        ),
    }
)

#: The one-third-octave bands of the A-weighted intensity level, 100 Hz to
#: 5 000 Hz (the 18 bands :math:`j` of Formula (K.2)), in Hz.
_RAIN_BANDS_HZ: tuple[float, ...] = (
    100.0,
    125.0,
    160.0,
    200.0,
    250.0,
    315.0,
    400.0,
    500.0,
    630.0,
    800.0,
    1000.0,
    1250.0,
    1600.0,
    2000.0,
    2500.0,
    3150.0,
    4000.0,
    5000.0,
)


def _band_table(values: tuple[float, ...]) -> Mapping[float, float]:
    """A read-only ``{band centre in Hz: value}`` table over the 18 bands."""
    return MappingProxyType(dict(zip(_RAIN_BANDS_HZ, values, strict=True)))


#: The values :math:`C_j` of ISO 10140-1:2021 Table K.2 (PDF page 57, printed
#: folio 51), in dB, keyed by one-third-octave band centre frequency in Hz,
#: 100 Hz to 5 000 Hz: the corrections Formula (K.2) adds to each band before
#: the energetic sum. They are the A-weighting of IEC 61672-1 rounded to 0,1 dB
#: and evaluated, as IEC 61672-1 Table 3 is, at the exact base-ten midband
#: frequency of each nominal band; at the nominal 125 Hz, 160 Hz, 200 Hz,
#: 250 Hz and 5 000 Hz the rounded weighting would not be the printed value.
RAINFALL_A_WEIGHTING: Mapping[float, float] = _band_table(
    (-19.1, -16.1, -13.4, -10.9, -8.6, -6.6, -4.8, -3.2, -1.9)
    + (-0.8, 0.0, 0.6, 1.0, 1.2, 1.3, 1.2, 1.0, 0.5)
)

#: Reference loss factor of the small reference specimen in decibels, as the
#: table prints it, :math:`10 \log_{10}(\eta_\mathrm{ref}/\eta_0)` with
#: :math:`\eta_0 = 1`, keyed by one-third-octave band centre frequency in Hz,
#: 100 Hz to 5 000 Hz (ISO 10140-5:2021 Table I.1, PDF page 44, printed
#: folio 38). The linear :math:`\eta_\mathrm{ref}` is :math:`10^{x/10}` of the
#: value :math:`x` held here, and it is the linear value that
#: :attr:`RainfallReferenceCorrection.reference_loss_factor` carries.
RAINFALL_REFERENCE_LOSS_FACTOR_DB: Mapping[float, float] = _band_table(
    (-10.0, -11.0, -11.0, -12.0, -13.0, -13.0, -14.0, -14.0, -15.0)
    + (-15.0, -16.0, -17.0, -17.0, -18.0, -18.0, -19.0, -19.0, -20.0)
)

#: Reference sound intensity level :math:`L_{I\mathrm{c,ref}}` of the small
#: reference specimen under heavy rain, in dB re 1 pW/m², keyed by
#: one-third-octave band centre frequency in Hz, 100 Hz to 5 000 Hz
#: (ISO 10140-5:2021 Table I.1, PDF page 44, printed folio 38).
RAINFALL_REFERENCE_INTENSITY_DB: Mapping[float, float] = _band_table(
    (45.0, 45.0, 46.0, 46.0, 47.0, 47.0, 47.0, 47.0, 47.0)
    + (46.0, 44.0, 42.0, 43.0, 46.0, 51.0, 50.0, 46.0, 44.0)
)

#: The constant of Formula (K.1), in dB: :math:`10 \log_{10}(0.16/4)` rounded,
#: the diffuse-field power of the Sabine area :math:`A = 0.16\,V/T`.
_K1_CONSTANT_DB = 14.0

#: The constant of Formula (I.1): :math:`\eta = 2.2/(f T_\mathrm{s})`, the
#: loss factor of a decay of 60 dB in :math:`T_\mathrm{s}` seconds.
_LOSS_FACTOR_CONSTANT = 2.2

#: Share of the drops that "should" lie within the drop-diameter and velocity
#: windows of ISO 10140-5:2021 H.1: 50 %.
_DROP_SHARE = 0.5

#: Relative slack on the inclusive tolerances of H.1 ("within ±2 mm/h", "within
#: ±0,5 mm", "within ±1 m/s"). A rate on the bound must pass, but it rarely
#: reaches the comparison as the decimal it stands for: 3,8 L collected on
#: 0,1 m² in one hour is 38 mm/h, 2 mm/h below the nominal 40 mm/h, and the
#: division leaves it a few units in the last place lower. Nine orders of
#: magnitude below the tolerance is far above that arithmetic and far below
#: anything a rain gauge resolves.
_BOUND_SLACK = 1e-9

#: Relative window within which a given frequency is taken for a nominal
#: one-third-octave band centre (a third of the 26 % between neighbours).
_BAND_MATCH = 0.06


def _band_indices(
    frequencies_hz: np.ndarray, targets: tuple[float, ...]
) -> np.ndarray | None:
    """Indices of ``targets`` in ``frequencies_hz``, or ``None`` if one is absent."""
    indices: list[int] = []
    for target in targets:
        hits = np.nonzero(np.abs(frequencies_hz - target) <= _BAND_MATCH * target)[0]
        if hits.size != 1:
            return None
        indices.append(int(hits[0]))
    return np.asarray(indices, dtype=np.intp)


def _table_values(
    table: Mapping[float, float],
    frequencies_hz: np.ndarray,
    missing: Callable[[float, int], str],
) -> np.ndarray:
    """The values of a band table at every given band, or a ``ValueError``.

    ``missing(frequency_hz, matches)`` words the error for a band the table
    does not hold exactly once.
    """
    keys = np.asarray(tuple(table), dtype=np.float64)
    values = np.asarray(tuple(table.values()), dtype=np.float64)
    out = np.empty(frequencies_hz.shape, dtype=np.float64)
    for i, f in enumerate(frequencies_hz):
        hits = np.nonzero(np.abs(keys - f) <= _BAND_MATCH * f)[0]
        if hits.size != 1:
            raise ValueError(missing(float(f), int(hits.size)))
        out[i] = values[int(hits[0])]
    return out


def _is_rain_band(frequency_hz: float) -> bool:
    """Whether ``frequency_hz`` is one of the 18 bands 100 Hz to 5 000 Hz."""
    return any(
        abs(band - frequency_hz) <= _BAND_MATCH * frequency_hz
        for band in _RAIN_BANDS_HZ
    )


def _outside_table_i1(frequency_hz: float, _matches: int) -> str:
    """The error for a band that Table I.1 does not print."""
    return (
        "Table I.1 is defined only in the 18 one-third-octave bands "
        f"100 Hz to 5000 Hz; {frequency_hz:g} Hz is not one of them."
    )


def _not_in_correction(frequency_hz: float, matches: int) -> str:
    """The error for a measured band the supplied correction does not carry."""
    if matches > 1:
        return (
            f"The reference correction carries {matches} values near "
            f"{frequency_hz:g} Hz; compute it once per band."
        )
    if _is_rain_band(frequency_hz):
        return (
            f"The reference correction carries no value at {frequency_hz:g} Hz; "
            "compute it over every band of the measurement."
        )
    return (
        f"The reference correction carries no value at {frequency_hz:g} Hz, "
        "and Table I.1 has none to give: it is defined only in the 18 "
        "one-third-octave bands 100 Hz to 5000 Hz."
    )


def _a_weighted(levels_db: np.ndarray, frequencies_hz: np.ndarray) -> float | None:
    r"""Formula (K.2) over the 18 bands, or ``None`` when one is missing."""
    idx = _band_indices(frequencies_hz, _RAIN_BANDS_HZ)
    if idx is None:
        return None
    weights = np.asarray(tuple(RAINFALL_A_WEIGHTING.values()), dtype=np.float64)
    return float(energy_sum(levels_db[idx] + weights))


# --- The rain ---------------------------------------------------------------


def rainfall_rate(
    collected_volume_litres: float,
    collection_area_m2: float,
    duration_s: float,
) -> float:
    """Rainfall rate from the water collected over an area and a time (H.2.3).

    The periodic check of a tank generator is "collecting the water over a
    given area over a precisely measured time period": the rate is the depth
    of that water, one litre per square metre being one millimetre, scaled to
    one hour (the definition under Table H.1).

    :param collected_volume_litres: Volume of water collected, in litres.
    :param collection_area_m2: Horizontal area it was collected over, in m².
    :param duration_s: Collection time, in seconds.
    :return: The rainfall rate, in mm/h.
    :raises ValueError: If an input is not positive and finite.
    """
    volume = require_positive(collected_volume_litres, "collected_volume_litres")
    area = require_positive(collection_area_m2, "collection_area_m2")
    duration = require_positive(duration_s, "duration_s")
    return volume / area * 3600.0 / duration


@dataclass(frozen=True)
class RainGeneratorVerification(OwnsArrays):
    """Whether an artificial rain generator makes the rain it should (H.1, H.2.3).

    The windows are the rows of Table H.1 the rain type selects, so the
    shares and the verdicts are read from the measured samples and are not
    fields: a verification cannot be built to pass a rain the table fails.

    :ivar rain_type: ``"intense"`` or ``"heavy"``.
    :ivar rainfall_rate_mm_h: The measured rainfall rate, in mm/h.
    :ivar drop_diameters_mm: The measured drop diameters, in mm, or ``None``.
    :ivar fall_velocities_m_s: The measured fall velocities, in m/s, or
        ``None``.
    """

    rain_type: str
    rainfall_rate_mm_h: float
    drop_diameters_mm: np.ndarray | None
    fall_velocities_m_s: np.ndarray | None

    def __post_init__(self) -> None:
        """Reject a rain type the table does not print.

        :raises ValueError: if ``rain_type`` is not ``"intense"`` or
            ``"heavy"``.
        """
        require_choice(self.rain_type, "rain_type", tuple(ARTIFICIAL_RAIN))

    @property
    def nominal(self) -> ArtificialRain:
        """The row of :data:`ARTIFICIAL_RAIN` the generator was verified against."""
        return ARTIFICIAL_RAIN[self.rain_type]

    @property
    def rate_deviation_mm_h(self) -> float:
        """Measured minus nominal rate, in mm/h."""
        return self.rainfall_rate_mm_h - self.nominal.rainfall_rate_mm_h

    @property
    def rate_ok(self) -> bool:
        """Whether the rate is within the tolerance ("shall"), bounds included."""
        return abs(
            self.rate_deviation_mm_h
        ) <= self.nominal.rainfall_rate_tolerance_mm_h * (1.0 + _BOUND_SLACK)

    @property
    def drop_share(self) -> float | None:
        """Share of the measured drops within the diameter window, or ``None``."""
        if self.drop_diameters_mm is None:
            return None
        nominal = self.nominal
        return _share_of(
            self.drop_diameters_mm,
            nominal.median_drop_diameter_mm,
            nominal.drop_diameter_tolerance_mm,
        )

    @property
    def drops_ok(self) -> bool | None:
        """Whether at least half of the drops are within it ("should"), or ``None``."""
        share = self.drop_share
        return None if share is None else share >= _DROP_SHARE

    @property
    def velocity_share(self) -> float | None:
        """Share of the measured drops within the velocity window, or ``None``."""
        if self.fall_velocities_m_s is None:
            return None
        nominal = self.nominal
        return _share_of(
            self.fall_velocities_m_s,
            nominal.fall_velocity_m_s,
            nominal.fall_velocity_tolerance_m_s,
        )

    @property
    def velocities_ok(self) -> bool | None:
        """Whether at least half of the drops fall within it ("should"), or ``None``."""
        share = self.velocity_share
        return None if share is None else share >= _DROP_SHARE

    @property
    def passes(self) -> bool:
        """Whether every judged requirement holds."""
        return (
            self.rate_ok
            and self.drops_ok is not False
            and self.velocities_ok is not False
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a RainGeneratorVerification has no truth value; read its '.passes'"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot each measured quantity against its tolerance window.

        Every quantity is drawn as its deviation from the nominal value in
        units of its tolerance, so the three share one axis and the window is
        -1 to 1. Requires matplotlib (``pip install phonometry[plot]``);
        returns the :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_rain_generator_verification

        check_language(language)
        return plot_rain_generator_verification(
            self, ax=ax, language=language, **kwargs
        )


def _share_of(values: np.ndarray, centre: float, half_width: float) -> float:
    """The share of *values* within ``centre ± half_width``, bounds included."""
    within = np.abs(values - centre) <= half_width * (1.0 + _BOUND_SLACK)
    return float(np.mean(within))


def verify_rain_generator(
    rainfall_rate_mm_h: float,
    *,
    rain_type: str = "heavy",
    drop_diameters_mm: ArrayLike | None = None,
    fall_velocities_m_s: ArrayLike | None = None,
) -> RainGeneratorVerification:
    """Does the rain generator make the rain of Table H.1 (ISO 10140-5:2021)?

    H.1 sets three tolerances on the generated rain: the rainfall rate
    "shall be within ±2 mm/h" of the nominal rate, and half of the drops
    "should be within ±0,5 mm" of the volume median drop diameter and
    "within ±1 m/s" of the fall velocity. A tank built to Table H.2 needs only
    the rate checked (H.2.3), by collecting the water (:func:`rainfall_rate`);
    another generator needs the drops measured as well, and the drop criteria
    are judged when their samples are given. The three windows include their
    bounds: a rate exactly 2 mm/h from the nominal one passes, also when
    :func:`rainfall_rate` returns it a rounding error beyond.

    :param rainfall_rate_mm_h: The measured rainfall rate, in mm/h.
    :param rain_type: ``"heavy"`` (default) or ``"intense"``.
    :param drop_diameters_mm: Diameters of individual measured drops, in mm,
        or ``None`` to leave the drop size unjudged.
    :param fall_velocities_m_s: Fall velocities of individual measured drops,
        in m/s, or ``None`` to leave the velocity unjudged.
    :return: A :class:`RainGeneratorVerification`.
    :raises ValueError: If the rate or a sample is not positive and finite, or
        ``rain_type`` is unknown.
    """
    require_choice(rain_type, "rain_type", tuple(ARTIFICIAL_RAIN))
    rate = require_positive(rainfall_rate_mm_h, "rainfall_rate_mm_h")
    drops = (
        None
        if drop_diameters_mm is None
        else require_positive_array(drop_diameters_mm, "drop_diameters_mm")
    )
    velocities = (
        None
        if fall_velocities_m_s is None
        else require_positive_array(fall_velocities_m_s, "fall_velocities_m_s")
    )
    return RainGeneratorVerification(
        rain_type=rain_type,
        rainfall_rate_mm_h=rate,
        drop_diameters_mm=drops,
        fall_velocities_m_s=velocities,
    )


# --- The reference specimen -------------------------------------------------


@dataclass(frozen=True)
class RainfallReferenceCorrection(OwnsArrays):
    r"""The normalization correction from the reference glass pane (Annex I).

    :ivar frequencies_hz: One-third-octave band centre frequencies, in Hz.
    :ivar l_i_ref_db: Measured sound intensity level of the reference
        specimen, :math:`L_{I,\mathrm{ref}}`, in dB re 1 pW/m².
    :ivar structural_reverberation_time_s: Its structural reverberation time
        :math:`T_\mathrm{s}`, in s.
    :ivar loss_factor: Its total loss factor
        :math:`\eta = 2.2/(f T_\mathrm{s})` (Formula (I.1)), a linear ratio.
    :ivar reference_loss_factor: The reference loss factor
        :math:`\eta_\mathrm{ref}` of Table I.1 as a linear ratio, like
        ``loss_factor``: :math:`10^{x/10}` of the decibel value :math:`x` the
        table prints (:data:`RAINFALL_REFERENCE_LOSS_FACTOR_DB`).
    :ivar l_i_m_ref_db: The level corrected to the reference loss factor,
        :math:`L_{I,\mathrm{m,ref}}`, in dB (Formula (I.2)).
    :ivar l_ic_ref_db: The reference level :math:`L_{I\mathrm{c,ref}}` of
        Table I.1, in dB.
    :ivar correction_db: :math:`\Delta L_{I\mathrm{c}} = L_{I,\mathrm{m,ref}} -
        L_{I\mathrm{c,ref}}`, in dB (Formula (I.3)).
    """

    frequencies_hz: np.ndarray
    l_i_ref_db: np.ndarray
    structural_reverberation_time_s: np.ndarray
    loss_factor: np.ndarray
    reference_loss_factor: np.ndarray
    l_i_m_ref_db: np.ndarray
    l_ic_ref_db: np.ndarray
    correction_db: np.ndarray

    def __post_init__(self) -> None:
        """Reject columns of different lengths.

        :raises ValueError: if the per-band columns disagree.
        """
        fields = (
            "frequencies_hz",
            "l_i_ref_db",
            "structural_reverberation_time_s",
            "loss_factor",
            "reference_loss_factor",
            "l_i_m_ref_db",
            "l_ic_ref_db",
            "correction_db",
        )
        require_ranks(self, **dict.fromkeys(fields, 1))
        require_same_length(self, *fields)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the corrected reference level against Table I.1.

        The gap between the two curves is the correction every specimen of
        the laboratory is normalized by. Requires matplotlib
        (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_rainfall_reference_correction

        check_language(language)
        return plot_rainfall_reference_correction(
            self, ax=ax, language=language, **kwargs
        )


def rainfall_reference_correction(
    l_i_ref_db: ArrayLike,
    structural_reverberation_time_s: ArrayLike,
    frequencies_hz: ArrayLike | None = None,
) -> RainfallReferenceCorrection:
    r"""Correction :math:`\Delta L_{I\mathrm{c}}` of a laboratory (ISO 10140-5 I.2).

    The small reference specimen is a single 6 mm glass pane of 1,25 m by
    1,5 m, mounted as a window pane of ISO 10140-1:2021 Annex D and wetted by
    heavy rain centred on it. Its structural reverberation time gives its
    loss factor, :math:`\eta = 2.2/(f T_\mathrm{s})` (Formula (I.1)), and its
    measured intensity level is brought to the reference loss factor of
    Table I.1, :math:`L_{I,\mathrm{m,ref}} = L_{I,\mathrm{ref}} +
    10 \log_{10}(\eta/\eta_\mathrm{ref})` (Formula (I.2)): a pane mounted more
    lossily radiates less, and the correction removes that part of the
    difference, which belongs to the mounting and not to the laboratory's
    rain. What remains, :math:`\Delta L_{I\mathrm{c}} = L_{I,\mathrm{m,ref}} -
    L_{I\mathrm{c,ref}}` (Formula (I.3)), is subtracted from every specimen
    the laboratory measures (ISO 10140-1:2021 Formula (K.5)). No reference
    specimen is defined for large specimens (I.3).

    :math:`f` in Formula (I.1) is taken as the band centre frequency given.

    :param l_i_ref_db: :math:`L_{I,\mathrm{ref}}` of the reference specimen per
        band, in dB re 1 pW/m² (e.g. ``rainfall_sound(...).l_i_db``).
    :param structural_reverberation_time_s: Its structural reverberation time
        per band, measured to ISO 10140-4, in s.
    :param frequencies_hz: Band centre frequencies, in Hz, each one of the 18
        bands of Table I.1 (100 Hz to 5 000 Hz); ``None`` takes all 18.
    :return: A :class:`RainfallReferenceCorrection`.
    :raises ValueError: If the inputs disagree in length, a level is not
        finite, a time or frequency is not positive, or a band is not in
        Table I.1.
    """
    freqs = (
        np.asarray(_RAIN_BANDS_HZ, dtype=np.float64)
        if frequencies_hz is None
        else require_positive_array(frequencies_hz, "frequencies_hz")
    )
    level = require_finite_array(l_i_ref_db, "l_i_ref_db")
    t_s = require_positive_array(
        structural_reverberation_time_s, "structural_reverberation_time_s"
    )
    require_equal_shapes(
        "rainfall_reference_correction",
        {
            "frequencies_hz": freqs.shape,
            "l_i_ref_db": level.shape,
            "structural_reverberation_time_s": t_s.shape,
        },
        "band",
    )
    eta_ref_db = _table_values(
        RAINFALL_REFERENCE_LOSS_FACTOR_DB, freqs, _outside_table_i1
    )
    l_ic_ref = _table_values(RAINFALL_REFERENCE_INTENSITY_DB, freqs, _outside_table_i1)
    eta = _LOSS_FACTOR_CONSTANT / (freqs * t_s)  # Formula (I.1)
    eta_ref = 10.0 ** (eta_ref_db / 10.0)
    l_i_m_ref = level + 10.0 * np.log10(eta / eta_ref)  # Formula (I.2)
    return RainfallReferenceCorrection(
        frequencies_hz=freqs,
        l_i_ref_db=level,
        structural_reverberation_time_s=t_s,
        loss_factor=eta,
        reference_loss_factor=eta_ref,
        l_i_m_ref_db=l_i_m_ref,
        l_ic_ref_db=l_ic_ref,
        correction_db=l_i_m_ref - l_ic_ref,  # Formula (I.3)
    )


# --- The rain on the specimen -----------------------------------------------


@dataclass(frozen=True)
class RainfallSoundResult(OwnsArrays):
    r"""Sound intensity level radiated by a specimen under rain (Annex K).

    :ivar frequencies_hz: One-third-octave band centre frequencies, in Hz.
    :ivar l_i_db: Sound intensity level :math:`L_I` per band, in dB re
        1 pW/m² (Formula (K.1) or (K.4)).
    :ivar l_ia_db: A-weighted sound intensity level :math:`L_{I\mathrm{A}}`,
        in dB (Formula (K.2)), or ``None`` when the 18 bands 100 Hz to
        5 000 Hz are not all present.
    :ivar method: ``"pressure"`` (K.4.2) or ``"intensity"`` (K.4.3).
    :ivar correction_db: The laboratory correction
        :math:`\Delta L_{I\mathrm{c}}` per band, in dB, or ``None`` when the
        levels were not normalized.
    :ivar l_i_norm_db: Normalized level :math:`L_{I\mathrm{norm}} = L_I -
        \Delta L_{I\mathrm{c}}` per band, in dB (Formula (K.5)), or ``None``.
    :ivar l_ia_norm_db: Its A-weighted level :math:`L_{I\mathrm{Anorm}}`, in
        dB, or ``None``.
    """

    frequencies_hz: np.ndarray
    l_i_db: np.ndarray
    l_ia_db: float | None
    method: str
    correction_db: np.ndarray | None = None
    l_i_norm_db: np.ndarray | None = None
    l_ia_norm_db: float | None = None

    def __post_init__(self) -> None:
        """Reject columns of different lengths and an unknown method.

        :raises ValueError: if the per-band columns disagree, or ``method`` is
            neither ``"pressure"`` nor ``"intensity"``.
        """
        require_ranks(self, frequencies_hz=1, l_i_db=1, correction_db=1, l_i_norm_db=1)
        require_same_length(
            self, "frequencies_hz", "l_i_db", "correction_db", "l_i_norm_db"
        )
        require_choice(self.method, "method", ("pressure", "intensity"))

    def octave_bands(
        self, *, normalized: bool = False
    ) -> tuple[np.ndarray, np.ndarray]:
        r"""``(octave centres in Hz, LIoct in dB)`` by Formula (K.3).

        :math:`L_{I\mathrm{oct}} = 10 \log_{10} \sum_{j=1}^{3} 10^{0.1 L_{I,j}}`
        over the three one-third-octave bands of each octave present.

        :param normalized: Combine :math:`L_{I\mathrm{norm}}` instead of
            :math:`L_I`.
        :raises ValueError: If ``normalized`` is set on levels that were not
            normalized.
        """
        levels = self.l_i_db
        if normalized:
            if self.l_i_norm_db is None:
                msg = "These levels were not normalized; there is no LInorm to combine."
                raise ValueError(msg)
            levels = self.l_i_norm_db
        centres: list[float] = []
        values: list[float] = []
        for centre in (125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0):
            thirds = tuple(centre * 2.0 ** (k / 3.0) for k in (-1, 0, 1))
            idx = _band_indices(self.frequencies_hz, thirds)
            if idx is not None:
                centres.append(centre)
                values.append(float(energy_sum(levels[idx])))
        return np.asarray(centres), np.asarray(values)

    def sound_power_levels(self, specimen_area_m2: float) -> np.ndarray:
        r"""Sound power level radiated by the whole specimen, per band.

        :math:`L_W = L_I + 10 \log_{10}(S/S_0)` (the NOTE to Formula (K.2)),
        with :math:`S` the area of the whole specimen.

        :param specimen_area_m2: Area of the specimen, in m².
        :return: :math:`L_W` per band, in dB re 1 pW.
        :raises ValueError: If the area is not positive and finite.
        """
        area = require_positive(specimen_area_m2, "specimen_area_m2")
        return np.asarray(self.l_i_db + 10.0 * np.log10(area), dtype=np.float64)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the sound intensity level per band, normalized when available.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_rainfall_sound

        check_language(language)
        return plot_rainfall_sound(self, ax=ax, language=language, **kwargs)


def _normalized(
    frequencies_hz: np.ndarray,
    l_i: np.ndarray,
    reference: RainfallReferenceCorrection | ArrayLike | None,
) -> tuple[np.ndarray | None, np.ndarray | None, float | None]:
    """``(ΔLIc, LInorm, LIAnorm)`` by Formula (K.5), or three ``None``."""
    if reference is None:
        return None, None, None
    if isinstance(reference, RainfallReferenceCorrection):
        keys = MappingProxyType(
            dict(
                zip(
                    reference.frequencies_hz.tolist(),
                    reference.correction_db.tolist(),
                    strict=True,
                )
            )
        )
        correction = _table_values(keys, frequencies_hz, _not_in_correction)
    else:
        correction = require_finite_array(reference, "reference_correction")
        require_equal_shapes(
            "rainfall_sound",
            {
                "frequencies_hz": frequencies_hz.shape,
                "reference_correction": correction.shape,
            },
            "band",
        )
    l_i_norm = l_i - correction  # Formula (K.5)
    return correction, l_i_norm, _a_weighted(l_i_norm, frequencies_hz)


def rainfall_sound(
    l_pr_db: ArrayLike,
    reverberation_time_s: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    volume_m3: float,
    excited_area_m2: float,
    background_db: ArrayLike | None = None,
    reference_correction: RainfallReferenceCorrection | ArrayLike | None = None,
) -> RainfallSoundResult:
    r"""Sound intensity level of a specimen under artificial rain (K.4.2).

    While the rain falls steadily on the specimen, the room-averaged sound
    pressure level :math:`L_\mathrm{pr}` and the reverberation time :math:`T`
    of the test room are measured to ISO 10140-4, and each band gives

    .. math::

       L_I = L_\mathrm{pr} - 10 \log_{10}(T/T_0) + 10 \log_{10}(V/V_0) - 14
       - 10 \log_{10}(S_\mathrm{e}/S_0)

    (Formula (K.1)). A small specimen (a roof window or rooflight, about
    1,25 m by 1,5 m) is wetted from one position and :math:`S_\mathrm{e}` is
    its area; a large one (10 m² to 20 m²) from three, whose levels are added
    energetically, and :math:`S_\mathrm{e}` is three times the perforated
    area of the tank. The 18 bands 100 Hz to 5 000 Hz give the A-weighted
    level :math:`L_{I\mathrm{A}}` of Formula (K.2).

    With the correction of the laboratory's reference specimen
    (:func:`rainfall_reference_correction`), the levels are also normalized,
    :math:`L_{I\mathrm{norm}} = L_I - \Delta L_{I\mathrm{c}}` (Formula (K.5)),
    for comparison between laboratories.

    :param l_pr_db: Room-averaged sound pressure level per band, in dB:
        ``(bands,)`` for one position of the rain generator or
        ``(positions, bands)`` for several, which are added energetically.
    :param reverberation_time_s: Reverberation time of the test room per band,
        in s.
    :param frequencies_hz: Band centre frequencies, in Hz.
    :param volume_m3: Volume of the test room, in m³.
    :param excited_area_m2: Area of the specimen directly excited by the rain,
        :math:`S_\mathrm{e}`, in m².
    :param background_db: Background noise level per band, in dB, or ``None``.
        When given, each position's level is corrected by ISO 10140-4
        (:func:`~phonometry.building.background_correction`) before the sum.
    :param reference_correction: The laboratory correction: a
        :class:`RainfallReferenceCorrection` covering every band, or
        :math:`\Delta L_{I\mathrm{c}}` per band in dB, or ``None``.
    :return: A :class:`RainfallSoundResult`.
    :raises ValueError: If the shapes disagree, a level is not finite, a time,
        frequency, volume or area is not positive, or a band has no correction.
    """
    freqs = require_positive_array(frequencies_hz, "frequencies_hz")
    try:
        levels = np.asarray(l_pr_db, dtype=np.float64)
    except (TypeError, ValueError) as exc:
        msg = "'l_pr_db' must be numeric."
        raise ValueError(msg) from exc
    if levels.ndim == 1:
        levels = levels[np.newaxis, :]
    if levels.ndim != 2 or levels.shape[0] == 0:  # noqa: PLR2004
        msg = "'l_pr_db' must be (bands,) or (positions, bands)."
        raise ValueError(msg)
    if not np.all(np.isfinite(levels)):
        msg = "'l_pr_db' must contain only finite values."
        raise ValueError(msg)
    t = require_positive_array(reverberation_time_s, "reverberation_time_s")
    require_equal_shapes(
        "rainfall_sound",
        {
            "frequencies_hz": freqs.shape,
            "l_pr_db (bands)": levels.shape[1:],
            "reverberation_time_s": t.shape,
        },
        "band",
    )
    volume = require_positive(volume_m3, "volume_m3")
    area = require_positive(excited_area_m2, "excited_area_m2")
    if background_db is not None:
        background = require_finite_array(background_db, "background_db")
        require_equal_shapes(
            "rainfall_sound",
            {"frequencies_hz": freqs.shape, "background_db": background.shape},
            "band",
        )
        levels = np.vstack([background_correction(row, background) for row in levels])
    l_pr = energy_sum(levels, axis=0)
    l_i = (
        l_pr
        - 10.0 * np.log10(t)
        + 10.0 * np.log10(volume)
        - _K1_CONSTANT_DB
        - 10.0 * np.log10(area)
    )  # Formula (K.1)
    correction, l_i_norm, l_ia_norm = _normalized(freqs, l_i, reference_correction)
    return RainfallSoundResult(
        frequencies_hz=freqs,
        l_i_db=l_i,
        l_ia_db=_a_weighted(l_i, freqs),
        method="pressure",
        correction_db=correction,
        l_i_norm_db=l_i_norm,
        l_ia_norm_db=l_ia_norm,
    )


def rainfall_sound_from_intensity(
    l_im_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    measuring_area_m2: float,
    excited_area_m2: float,
    reference_correction: RainfallReferenceCorrection | ArrayLike | None = None,
) -> RainfallSoundResult:
    r"""Sound intensity level of a specimen under rain, measured directly (K.4.3).

    The alternative of K.4.3 measures the intensity with a probe over a
    surface :math:`S_\mathrm{m}` enclosing the specimen (ISO 15186-1, in any
    room meeting its field indicator and background requirements), and
    refers it to the excited area,
    :math:`L_I = L_{I\mathrm{m}} + 10 \log_{10}(S_\mathrm{m}/S_\mathrm{e})`
    (Formula (K.4)). The A-weighted level, the octaves and the normalization
    then follow as in K.4.2.

    :param l_im_db: Sound intensity level measured over the surface, per band,
        in dB re 1 pW/m².
    :param frequencies_hz: Band centre frequencies, in Hz.
    :param measuring_area_m2: Area of the measuring surface
        :math:`S_\mathrm{m}`, in m².
    :param excited_area_m2: Area of the specimen directly excited by the rain,
        :math:`S_\mathrm{e}`, in m².
    :param reference_correction: The laboratory correction, as for
        :func:`rainfall_sound`, or ``None``.
    :return: A :class:`RainfallSoundResult` with ``method="intensity"``.
    :raises ValueError: If the shapes disagree, a level is not finite, or a
        frequency or area is not positive.
    """
    freqs = require_positive_array(frequencies_hz, "frequencies_hz")
    l_im = require_finite_array(l_im_db, "l_im_db")
    require_equal_shapes(
        "rainfall_sound_from_intensity",
        {"frequencies_hz": freqs.shape, "l_im_db": l_im.shape},
        "band",
    )
    measuring = require_positive(measuring_area_m2, "measuring_area_m2")
    excited = require_positive(excited_area_m2, "excited_area_m2")
    l_i = l_im + 10.0 * np.log10(measuring / excited)  # Formula (K.4)
    correction, l_i_norm, l_ia_norm = _normalized(freqs, l_i, reference_correction)
    return RainfallSoundResult(
        frequencies_hz=freqs,
        l_i_db=l_i,
        l_ia_db=_a_weighted(l_i, freqs),
        method="intensity",
        correction_db=correction,
        l_i_norm_db=l_i_norm,
        l_ia_norm_db=l_ia_norm,
    )
