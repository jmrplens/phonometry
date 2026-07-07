#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Sound power level of a noise source from sound pressure measurements over an
enveloping measurement surface: ISO 3744:2010 (engineering, accuracy grade 2)
and ISO 3746:2010 (survey, accuracy grade 3).

The source stands on one (or more) reflecting plane(s). Sound pressure levels
are measured at an array of microphone positions on a hypothetical surface of
area ``S`` enveloping the source (a hemisphere or a right parallelepiped). The
sound power level follows from the surface-averaged pressure level and the
surface area (ISO 3744:2010 clause 8.2, equations (12), (16)-(18))::

    Lp_mean = 10*lg( (1/NM) * sum_i 10^(0,1*Lpi) )      (energy average, Eq. 12)
    K1      = -10*lg( 1 - 10^(-0,1*dLp) )               (background, Eq. 16)
    K2      = 10*lg( 1 + 4*S/A )                        (environment, Eq. A.2)
    Lp      = Lp_mean - K1 - K2                         (surface SPL, Eq. 17)
    LW      = Lp + 10*lg(S/S0)     S0 = 1 m^2           (Eq. 18)

The measurement surface area is a closed form of the source geometry: a full
hemisphere ``S = 2*pi*r^2`` (half ``pi*r^2``, quarter ``pi*r^2/2``) for one,
two or three reflecting planes (ISO 3744 clause 7.2.3); a parallelepiped
``S = 4(ab+bc+ca)`` with ``a = 0,5*l1+d``, ``b = 0,5*l2+d``, ``c = l3+d`` for
one plane (clause 7.2.4, equations (9)-(11)).

The A-weighted sound power level is combined from band levels with the
A-weighting band corrections ``Ck`` of ISO 3744 Annex E (Tables E.1/E.2)::

    LWA = 10*lg( sum_k 10^(0,1*(LWk + Ck)) )            (Eq. E.1)

ISO 3746:2010 shares the surfaces, the energy average and the LW/K1/K2 forms
but is coarser: fewer microphone positions (clause 8.2.1), a background
criterion of 3 dB instead of 6 dB (clause 8.4.1) and validity up to
``K2A <= 7 dB`` instead of ``4 dB`` (clause 4.3).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Literal, Tuple, cast

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

_S0 = 1.0  #: Reference area, in square metres (ISO 3744, 8.2.5).

Grade = Literal["engineering", "survey"]
Surface = Literal["hemisphere", "box"]


class SoundPowerWarning(UserWarning):
    """Non-fatal qualification issue in any of the sound-power methods.

    Emitted for ISO 3744/3746 background margin below the criterion and for
    ``K2`` beyond the method's validity limit (8.2.3, 4.3.2); for ISO 3741
    reverberation-room qualification (room volume vs Table 1, mean absorption)
    and microphone/source-position sampling; and for ISO 9614-2 negative total
    partial power and unmet field-indicator criteria. Where a lower criterion
    is only just met the returned levels represent upper bounds and must be
    reported as such."""


# --- ISO 3744:2010 Annex B, normative microphone coordinates (x/r,y/r,z/r) ---
#: Table B.1 - preferred positions for all sources (including tones).
_TABLE_B1: np.ndarray = np.array(
    [
        [0.16, -0.96, 0.22], [0.78, -0.60, 0.20], [0.78, 0.55, 0.31],
        [0.16, 0.90, 0.41], [-0.83, 0.32, 0.45], [-0.83, -0.40, 0.38],
        [-0.26, -0.65, 0.71], [0.74, -0.07, 0.67], [-0.26, 0.50, 0.83],
        [0.10, -0.10, 0.99], [0.91, -0.34, 0.22], [0.91, 0.38, 0.20],
        [-0.09, 0.95, 0.31], [-0.70, 0.59, 0.41], [-0.69, -0.56, 0.45],
        [-0.07, -0.92, 0.38], [0.43, -0.55, 0.71], [0.43, 0.61, 0.67],
        [-0.56, 0.02, 0.83], [0.14, 0.04, 0.99],
    ]
)
#: Table B.2 - positions for a broadband (tone-free) source.
_TABLE_B2: np.ndarray = np.array(
    [
        [-0.99, 0.0, 0.15], [0.50, -0.86, 0.15], [0.50, 0.86, 0.15],
        [-0.45, 0.77, 0.45], [-0.45, -0.77, 0.45], [0.89, 0.0, 0.45],
        [0.33, 0.57, 0.75], [-0.66, 0.0, 0.75], [0.33, -0.57, 0.75],
        [0.0, 0.0, 1.00], [0.99, 0.0, 0.15], [-0.50, 0.86, 0.15],
        [-0.50, -0.86, 0.15], [0.45, -0.77, 0.45], [0.45, 0.77, 0.45],
        [-0.89, 0.0, 0.45], [-0.33, -0.57, 0.75], [0.66, 0.0, 0.75],
        [-0.33, 0.57, 0.75], [0.0, 0.0, 1.00],
    ]
)
#: Table B.3 - source adjacent to three reflecting planes.
_TABLE_B3: np.ndarray = np.array(
    [
        [0.86, -0.50, 0.15], [0.45, -0.77, 0.45], [0.47, -0.47, 0.75],
        [0.50, -0.86, 0.15], [0.77, -0.45, 0.45], [0.47, -0.47, 0.75],
    ]
)

# --- ISO 3744:2010 Annex E, A-weighting band corrections Ck (dB) ------------
#: Table E.1 - one-third-octave mid-band frequencies.
_CK_THIRD: Dict[int, float] = {
    50: -30.2, 63: -26.2, 80: -22.5, 100: -19.1, 125: -16.1, 160: -13.4,
    200: -10.9, 250: -8.6, 315: -6.6, 400: -4.8, 500: -3.2, 630: -1.9,
    800: -0.8, 1000: 0.0, 1250: 0.6, 1600: 1.0, 2000: 1.2, 2500: 1.3,
    3150: 1.2, 4000: 1.0, 5000: 0.5, 6300: -0.1, 8000: -1.1, 10000: -2.5,
}
#: Table E.2 - octave mid-band frequencies (subset of E.1 values).
_CK_OCTAVE: Dict[int, float] = {
    63: -26.2, 125: -16.1, 250: -8.6, 500: -3.2,
    1000: 0.0, 2000: 1.2, 4000: 1.0, 8000: -1.1,
}

#: Background-noise criteria (low, high) in dB: below ``low`` the correction is
#: clamped (upper bound, warn); above ``high`` it is set to zero. ISO 3744
#: clause 8.2.3 (6, 15); ISO 3746 clause 8.4.1 (3, 10).
_K1_CRITERIA: Dict[str, Tuple[float, float]] = {
    "engineering": (6.0, 15.0),
    "survey": (3.0, 10.0),
}
#: Environmental-correction validity limit K2A, in dB. ISO 3744 clause 4.3.2
#: (4 dB); ISO 3746 clause 4.3 (7 dB).
_K2_LIMIT: Dict[str, float] = {"engineering": 4.0, "survey": 7.0}
#: Minimum microphone positions by grade and number of reflecting planes.
#: ISO 3744 clause 8.1.1 (10/5/3); ISO 3746 clause 8.2.1 (4/3/3).
_MIN_HEMI_POSITIONS: Dict[str, Dict[int, int]] = {
    "engineering": {1: 10, 2: 5, 3: 3},
    "survey": {1: 4, 2: 3, 3: 3},
}
#: Minimum microphone positions on a parallelepiped: ISO 3744 clause C.1 (9 key
#: positions for rectangular partial areas); ISO 3746 clause C.1, Figure C.7 (4
#: positions for a floor-standing source on one reflecting plane).
_MIN_BOX_POSITIONS: Dict[str, int] = {"engineering": 9, "survey": 4}
#: Typical A-weighted reproducibility standard deviation sigma_R0, in dB.
#: ISO 3744 Table 2 (1,5); ISO 3746 Table 1 (3,0, tone-free).
_SIGMA_R0: Dict[str, float] = {"engineering": 1.5, "survey": 3.0}


@dataclass(frozen=True)
class SoundPowerResult:
    """Result of a sound power determination from surface pressure levels.

    ``sound_power_level`` is the per-band ``LW`` (ISO 3744 Eq. 18);
    ``surface_pressure_level`` the surface SPL ``Lp`` after the K1/K2
    corrections (Eq. 17); ``mean_pressure_level`` the raw energy-averaged
    level ``Lp'(ST)`` (Eq. 12). ``background_correction`` (K1) and
    ``environmental_correction`` (K2) are per band. ``sound_power_level_a`` is
    the A-weighted total ``LWA`` (Eq. E.1), computed only when ``frequencies``
    are supplied; for a single band it equals ``LW``, and for several bands
    without ``frequencies`` it is ``NaN`` (A-weighting needs the band centres).
    ``directivity_index`` is the apparent directivity index ``DIi*`` per
    microphone position and frequency band, shape ``(NM, NB)`` (Eq. 7,
    evaluated per band per clause 8.6). ``uncertainty`` is the expanded
    uncertainty
    ``U = 2*sqrt(sigma_R0^2 + sigma_omc^2)`` (95 %, ISO 3744 clause 9.5)."""

    frequencies: np.ndarray | None
    sound_power_level: np.ndarray
    surface_pressure_level: np.ndarray
    mean_pressure_level: np.ndarray
    background_correction: np.ndarray
    environmental_correction: np.ndarray
    directivity_index: np.ndarray
    surface_area: float
    sound_power_level_a: float
    uncertainty: float
    grade: str

    def plot(self, ax: Axes | None = None, **kwargs: Any) -> Axes:
        """Plot the LW spectrum with the A-weighted total annotated.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ._plotting import plot_sound_power

        return plot_sound_power(self, ax=ax, **kwargs)


def _energy_average(levels: np.ndarray) -> np.ndarray:
    """Energy (mean-square) average of levels over axis 0 (ISO 3744 Eq. 12)."""
    n = levels.shape[0]
    return np.asarray(
        10.0 * np.log10(np.sum(10.0 ** (0.1 * levels), axis=0) / n),
        dtype=np.float64,
    )


def background_noise_correction(
    source_levels: np.ndarray,
    background_levels: np.ndarray,
    grade: Grade = "engineering",
) -> np.ndarray:
    """Background-noise correction ``K1`` per band (ISO 3744:2010 Eq. 16).

    ``K1 = -10*lg(1 - 10^(-0,1*dLp))`` with ``dLp = source - background``. For
    ``dLp`` above the upper criterion (15 dB engineering, 10 dB survey) the
    background is negligible and ``K1 = 0``. For ``dLp`` below the lower
    criterion (6 dB engineering, 3 dB survey) the accuracy is reduced: ``K1``
    is clamped to its value at that criterion and a :class:`SoundPowerWarning`
    is emitted, the result then being an upper bound (clause 8.2.3).

    :param source_levels: Levels with the source operating, in decibels.
    :param background_levels: Background-noise levels, in decibels.
    :param grade: ``'engineering'`` (ISO 3744) or ``'survey'`` (ISO 3746).
    :return: ``K1`` per band, in decibels.
    """
    low, high = _K1_CRITERIA[_check_grade(grade)]
    src = np.asarray(source_levels, dtype=np.float64)
    bg = np.asarray(background_levels, dtype=np.float64)
    delta = src - bg
    clamped = np.maximum(delta, low)
    k1 = -10.0 * np.log10(1.0 - 10.0 ** (-0.1 * clamped))
    k1 = np.where(delta >= high, 0.0, k1)
    if np.any(delta < low):
        warnings.warn(
            f"Background margin below {low:g} dB in one or more bands; K1 "
            "clamped to the criterion value and levels are upper bounds "
            "(ISO 3744:2010, 8.2.3).",
            SoundPowerWarning,
            stacklevel=2,
        )
    return np.asarray(k1, dtype=np.float64)


def environmental_correction(
    surface_area: float,
    *,
    absorption_area: float | np.ndarray | None = None,
    reverberation_time: float | np.ndarray | None = None,
    room_volume: float | None = None,
    mean_absorption_coefficient: float | np.ndarray | None = None,
    room_surface: float | None = None,
) -> float | np.ndarray:
    """Environmental correction ``K2`` (ISO 3744:2010 Eq. A.2).

    ``K2 = 10*lg(1 + 4*S/A)`` where ``A`` is the equivalent sound absorption
    area of the room. ``A`` is taken directly from ``absorption_area``, or from
    the Sabine reverberation time ``A = 0,16*V/T`` (Eq. A.3, ``reverberation_
    time`` + ``room_volume``), or from the mean absorption coefficient
    ``A = alpha*Sv`` (Eq. A.7, ``mean_absorption_coefficient`` + ``room_
    surface``). With no room data the field is treated as free and ``K2 = 0``;
    supplying only one member of a pair raises :class:`ValueError` rather than
    silently falling back to the free-field result.

    The room absorption is frequency dependent (``T``, ``alpha`` and hence ``A``
    vary with the band). Passing ``absorption_area``, ``reverberation_time`` or
    ``mean_absorption_coefficient`` as a per-band array returns ``K2`` per band
    with that shape; scalar inputs return a scalar, unchanged.

    :param surface_area: Measurement surface area ``S``, in square metres.
    :param absorption_area: Equivalent absorption area ``A`` (m^2), scalar or
        per band.
    :param reverberation_time: Sabine ``T`` (s), scalar or per band, with
        ``room_volume`` (Eq. A.3).
    :param room_volume: Room volume ``V`` (m^3), with ``reverberation_time``.
    :param mean_absorption_coefficient: ``alpha`` in (0, 1], scalar or per band,
        with ``room_surface`` (Eq. A.7).
    :param room_surface: Room boundary area ``Sv`` (m^2), with ``alpha``.
    :return: ``K2`` in decibels; a scalar for scalar inputs, otherwise an array
        per band.
    """
    if absorption_area is None:
        # A half-specified room pair must never be read as free field: naming
        # only one member of a pair is a mistake, not a K2 = 0 request.
        if (reverberation_time is None) != (room_volume is None):
            missing = "room_volume" if room_volume is None else "reverberation_time"
            raise ValueError(
                "reverberation_time and room_volume must be given together "
                f"(Eq. A.3); '{missing}' is missing."
            )
        if (mean_absorption_coefficient is None) != (room_surface is None):
            missing = (
                "room_surface"
                if room_surface is None
                else "mean_absorption_coefficient"
            )
            raise ValueError(
                "mean_absorption_coefficient and room_surface must be given "
                f"together (Eq. A.7); '{missing}' is missing."
            )
        if reverberation_time is not None and room_volume is not None:
            t = np.asarray(reverberation_time, dtype=np.float64)
            if room_volume <= 0 or np.any(t <= 0.0):
                raise ValueError("reverberation_time and room_volume must be > 0.")
            absorption_area = 0.16 * room_volume / t
        elif mean_absorption_coefficient is not None and room_surface is not None:
            alpha = np.asarray(mean_absorption_coefficient, dtype=np.float64)
            if room_surface <= 0 or np.any(alpha <= 0.0) or np.any(alpha > 1.0):
                raise ValueError(
                    "mean_absorption_coefficient must be in (0, 1] and "
                    "room_surface > 0."
                )
            absorption_area = alpha * room_surface
        else:
            return 0.0
    a = np.asarray(absorption_area, dtype=np.float64)
    if np.any(a <= 0.0):
        raise ValueError("absorption_area must be positive.")
    k2 = 10.0 * np.log10(1.0 + 4.0 * surface_area / a)
    return float(k2) if k2.ndim == 0 else np.asarray(k2, dtype=np.float64)


def measurement_positions(
    surface: Surface,
    *,
    radius: float | None = None,
    reflecting_planes: int = 1,
    tones: bool = True,
    grade: Grade = "engineering",
) -> np.ndarray:
    """Normative microphone coordinates on the measurement surface.

    For a ``'hemisphere'`` the coordinates come from ISO 3744:2010 Annex B:
    Table B.1 for sources that may emit discrete tones (``tones=True``) and
    Table B.2 for broadband sources. The engineering grade uses the 10 key
    positions for one reflecting plane (5 for two, 3 for three); the survey
    grade uses the reduced arrays of ISO 3746:2010 clause 8.2.1 (positions
    4, 5, 6, 10 for one plane). Coordinates are scaled by ``radius`` and
    returned as an ``(N, 3)`` array of Cartesian ``(x, y, z)`` in metres.

    :param surface: ``'hemisphere'`` (only shape with a coordinate table).
    :param radius: Hemisphere radius ``r``, in metres.
    :param reflecting_planes: Number of reflecting planes (1, 2 or 3).
    :param tones: If True use Table B.1, else Table B.2.
    :param grade: ``'engineering'`` or ``'survey'``.
    :return: ``(N, 3)`` microphone coordinates, in metres.
    """
    if surface != "hemisphere":
        raise ValueError(
            "measurement_positions provides coordinates for 'hemisphere' only; "
            "parallelepiped positions are defined by area subdivision "
            "(ISO 3744:2010 Annex C)."
        )
    if radius is None or radius <= 0:
        raise ValueError("A positive 'radius' is required for a hemisphere.")
    if reflecting_planes not in (1, 2, 3):
        raise ValueError("'reflecting_planes' must be 1, 2 or 3.")
    grade = _check_grade(grade)
    if grade == "engineering":  # ISO 3744 clause 8.1.1
        if reflecting_planes == 1:  # positions 1-10, Table B.1 (or B.2 broadband)
            table, index = (_TABLE_B1 if tones else _TABLE_B2), tuple(range(10))
        elif reflecting_planes == 2:  # positions 2,3,6,7,9 of Table B.2
            table, index = _TABLE_B2, (1, 2, 5, 6, 8)
        else:  # positions 1,2,3 of Table B.3
            table, index = _TABLE_B3, (0, 1, 2)
    else:  # survey, ISO 3746 clause 8.2.1
        if reflecting_planes == 1:  # positions 4,5,6,10 of Table B.1
            table, index = _TABLE_B1, (3, 4, 5, 9)
        elif reflecting_planes == 2:  # positions 14,15,18 of Table B.2
            table, index = _TABLE_B2, (13, 14, 17)
        else:  # positions 14,21,22 of Table B.2 (extended array not transcribed)
            raise NotImplementedError(
                "Survey coordinates for a source adjacent to three reflecting "
                "planes require the extended ISO 3746:2010 Table B.2 positions "
                "21 and 22 (see Figure B.4)."
            )
    return np.asarray(table[list(index)] * radius, dtype=np.float64)


def _hemisphere_area(radius: float, reflecting_planes: int) -> float:
    """Hemisphere/half/quarter area (ISO 3744:2010 clause 7.2.3)."""
    factor = {1: 2.0, 2: 1.0, 3: 0.5}[reflecting_planes]
    return factor * np.pi * radius**2


def _box_area(
    dimensions: Tuple[float, float, float], distance: float, reflecting_planes: int
) -> float:
    """Parallelepiped area (ISO 3744:2010 clause 7.2.4, equations (9)-(11))."""
    l1, l2, l3 = dimensions
    d = distance
    if reflecting_planes == 1:  # Eq. 9
        a, b, c = 0.5 * l1 + d, 0.5 * l2 + d, l3 + d
        return 4.0 * (a * b + b * c + c * a)
    if reflecting_planes == 2:  # Eq. 10 (against a wall)
        a, b, c = 0.5 * l2 + 0.5 * d, 0.5 * l1 + d, l3 + d
        return 2.0 * (2.0 * a * b + b * c + 2.0 * c * a)
    # Eq. 11 (in a corner)
    a, b, c = 0.5 * l1 + 0.5 * d, 0.5 * l2 + 0.5 * d, l3 + d
    return 2.0 * (2.0 * a * b + b * c + c * a)


def _a_weighting_corrections(frequencies: np.ndarray) -> np.ndarray:
    """A-weighting band corrections Ck for the given nominal mid-band
    frequencies (ISO 3744:2010 Annex E, Tables E.1/E.2). The octave-band
    values (Table E.2) coincide with the one-third-octave values (Table E.1)
    at the shared mid-band frequencies, so a single lookup serves both."""
    nominal = [int(round(f)) for f in frequencies]
    # Use the octave table (E.2) when every band is an octave mid-band centre,
    # otherwise the one-third-octave table (E.1); the two agree where they
    # overlap, so the result is identical either way.
    table = _CK_OCTAVE if set(nominal) <= set(_CK_OCTAVE) else _CK_THIRD
    ck = []
    for freq in nominal:
        if freq not in table:
            raise ValueError(
                f"No ISO 3744 Annex E A-weighting value for {freq} Hz; "
                "expected a nominal octave or one-third-octave mid-band "
                "frequency (50 Hz to 10 kHz)."
            )
        ck.append(table[freq])
    return np.asarray(ck, dtype=np.float64)


def _check_grade(grade: str) -> Grade:
    if grade not in ("engineering", "survey"):
        raise ValueError("'grade' must be 'engineering' or 'survey'.")
    return cast(Grade, grade)


def sound_power_pressure(
    levels_positions: np.ndarray,
    surface: Surface,
    *,
    radius: float | None = None,
    dimensions: Tuple[float, float, float] | None = None,
    distance: float | None = None,
    reflecting_planes: int = 1,
    background_levels: np.ndarray | None = None,
    frequencies: np.ndarray | None = None,
    absorption_area: float | None = None,
    reverberation_time: float | None = None,
    room_volume: float | None = None,
    mean_absorption_coefficient: float | None = None,
    room_surface: float | None = None,
    grade: Grade = "engineering",
    omc_uncertainty: float = 0.0,
) -> SoundPowerResult:
    """Sound power level from surface pressure levels (ISO 3744/3746:2010).

    ``levels_positions`` is an ``(NM, NB)`` array of time-averaged sound
    pressure levels: one row per microphone position, one column per frequency
    band (or a single column for a directly measured A-weighted level). The
    surface-averaged level is corrected for background noise (``K1``, from
    ``background_levels``) and for the test environment (``K2``, from the room
    absorption data) and combined with the measurement surface area::

        LW = 10*lg((1/NM) sum 10^(0,1*Lpi)) - K1 - K2 + 10*lg(S/S0)

    The surface area ``S`` is computed from the geometry: ``radius`` for a
    ``'hemisphere'`` (clause 7.2.3) or ``dimensions`` + ``distance`` for a
    ``'box'`` (clause 7.2.4). When ``frequencies`` are given the A-weighted
    sound power level is combined via ISO 3744 Annex E.

    :param levels_positions: ``(NM, NB)`` sound pressure levels, in decibels.
    :param surface: ``'hemisphere'`` or ``'box'``.
    :param radius: Hemisphere radius ``r`` (metres), for ``surface='hemisphere'``.
    :param dimensions: Reference box ``(l1, l2, l3)`` (metres), for ``'box'``.
    :param distance: Measurement distance ``d`` (metres), for ``'box'``.
    :param reflecting_planes: Number of reflecting planes (1, 2 or 3).
    :param background_levels: ``(NM, NB)`` background levels for ``K1``, or a
        single spectrum ``(NB,)`` / ``(1, NB)`` broadcast to every position.
    :param frequencies: Band mid-band frequencies (Hz) for the A-weighted total.
    :param absorption_area: Equivalent absorption area ``A`` (m^2) for ``K2``.
    :param reverberation_time: Sabine ``T`` (s), with ``room_volume``, for ``K2``.
    :param room_volume: Room volume ``V`` (m^3), with ``reverberation_time``.
    :param mean_absorption_coefficient: ``alpha``, with ``room_surface``, for ``K2``.
    :param room_surface: Room boundary area ``Sv`` (m^2), with ``alpha``.
    :param grade: ``'engineering'`` (ISO 3744) or ``'survey'`` (ISO 3746).
    :param omc_uncertainty: ``sigma_omc`` (dB), operating/mounting instability.
    :return: :class:`SoundPowerResult`.
    """
    grade = _check_grade(grade)
    levels = np.atleast_2d(np.asarray(levels_positions, dtype=np.float64))
    if levels.ndim != 2:
        raise ValueError("'levels_positions' must be a 2D (positions, bands) array.")
    n_positions = levels.shape[0]

    # --- measurement surface area -----------------------------------------
    if reflecting_planes not in (1, 2, 3):
        raise ValueError("'reflecting_planes' must be 1, 2 or 3.")
    if surface == "hemisphere":
        if radius is None or radius <= 0:
            raise ValueError("A positive 'radius' is required for a hemisphere.")
        area = _hemisphere_area(radius, reflecting_planes)
        min_positions = _MIN_HEMI_POSITIONS[grade][reflecting_planes]
    elif surface == "box":
        if dimensions is None or distance is None:
            raise ValueError("'dimensions' and 'distance' are required for a box.")
        if len(dimensions) != 3 or any(v <= 0 for v in dimensions) or distance <= 0:
            raise ValueError("'dimensions' must be 3 positive values and 'distance' > 0.")
        area = _box_area(dimensions, distance, reflecting_planes)
        min_positions = _MIN_BOX_POSITIONS[grade]
    else:
        raise ValueError("'surface' must be 'hemisphere' or 'box'.")

    if n_positions < min_positions:
        raise ValueError(
            f"{grade} {surface} with {reflecting_planes} reflecting plane(s) "
            f"requires at least {min_positions} microphone positions, got "
            f"{n_positions} (ISO 3744/3746:2010 clause 8)."
        )

    # --- energy average and background correction K1 ----------------------
    mean_level = _energy_average(levels)
    n_bands = mean_level.shape[0]
    if background_levels is not None:
        bg = np.atleast_2d(np.asarray(background_levels, dtype=np.float64))
        # A single background spectrum (shape (NB,) or (1, NB)) is broadcast to
        # every microphone position; a full (NM, NB) array is used as given.
        if bg.shape == (1, n_bands) and n_positions != 1:
            bg = np.broadcast_to(bg, (n_positions, n_bands))
        if bg.shape != levels.shape:
            raise ValueError(
                "'background_levels' must match 'levels_positions' shape, or be "
                "a single spectrum of shape (NB,) or (1, NB) broadcast to all "
                "positions."
            )
        k1 = background_noise_correction(mean_level, _energy_average(bg), grade)
    else:
        k1 = np.zeros(n_bands, dtype=np.float64)

    # --- environmental correction K2 (scalar or per band) -----------------
    k2_value = environmental_correction(
        area,
        absorption_area=absorption_area,
        reverberation_time=reverberation_time,
        room_volume=room_volume,
        mean_absorption_coefficient=mean_absorption_coefficient,
        room_surface=room_surface,
    )
    k2_arr = np.atleast_1d(np.asarray(k2_value, dtype=np.float64))
    if k2_arr.shape not in ((1,), (n_bands,)):
        raise ValueError(
            "per-band environmental inputs (absorption_area / reverberation_time"
            " / mean_absorption_coefficient) must match the number of bands."
        )
    if np.any(k2_arr > _K2_LIMIT[grade]):
        warnings.warn(
            f"K2 up to {float(np.max(k2_arr)):.1f} dB exceeds the {grade} "
            f"validity limit of {_K2_LIMIT[grade]:g} dB; the acoustic "
            "environment does not qualify for this method (ISO 3744:2010 "
            "clause 4.3.2).",
            SoundPowerWarning,
            stacklevel=2,
        )
    k2 = np.broadcast_to(k2_arr, (n_bands,)).astype(np.float64)

    # --- surface SPL, sound power level and A-weighted total ---------------
    surface_spl = mean_level - k1 - k2
    lw = surface_spl + 10.0 * np.log10(area / _S0)

    if frequencies is not None:
        freqs = np.asarray(frequencies, dtype=np.float64)
        if freqs.shape[0] != n_bands:
            raise ValueError("'frequencies' length must match the number of bands.")
        ck = _a_weighting_corrections(freqs)
        lwa = float(10.0 * np.log10(np.sum(10.0 ** (0.1 * (lw + ck)))))
    else:
        freqs = None
        # A-weighting needs the band centre frequencies; with several bands and
        # none supplied the A-weighted total is undefined (NaN). A single band
        # carries no weighting, so LWA = LW.
        lwa = float(lw[0]) if n_bands == 1 else float("nan")

    # --- apparent directivity index per position AND band (Eq. 7) ---------
    # ISO 3744:2010 clause 8.6 requires the directivity index to be evaluated
    # per frequency band, so DIi* is a (NM, NB) array. Per Eq. 7
    # DIi*(k) = Lpi(k) - (Lp'(k) - K1(k)): BOTH the per-position level Lpi(k)
    # and the surface energy mean Lp'(k) carry the same per-band background
    # correction K1(k), which cancels in the difference (3.24 DI definition).
    # The uniform per-band K1 therefore drops out and DIi*(k) reduces to the raw
    # per-band level minus the raw per-band surface mean (no residual +K1 bias).
    directivity = np.asarray(levels - mean_level[np.newaxis, :], dtype=np.float64)

    uncertainty = 2.0 * float(np.hypot(_SIGMA_R0[grade], omc_uncertainty))

    return SoundPowerResult(
        frequencies=freqs,
        sound_power_level=np.asarray(lw, dtype=np.float64),
        surface_pressure_level=np.asarray(surface_spl, dtype=np.float64),
        mean_pressure_level=mean_level,
        background_correction=k1,
        environmental_correction=k2,
        directivity_index=directivity,
        surface_area=float(area),
        sound_power_level_a=lwa,
        uncertainty=uncertainty,
        grade=grade,
    )
