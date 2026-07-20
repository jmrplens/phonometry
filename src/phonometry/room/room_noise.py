#  Copyright (c) 2026. Jose M. Requena-Plens
"""
Room-noise rating curves per ANSI/ASA S12.2-2019.

Implements the two spectrum-in rating methods of ANSI/ASA S12.2-2019, *Criteria
for Evaluating Room Noise*:

* **Noise Criteria (NC)** by the tangency method (Table 1). The NC rating is the
  value of the highest NC curve touched by the measured octave-band spectrum,
  reported together with the governing band.
* **Room Criteria Mark II (RC)** (Annex D, Table D.1). The numerical rating is
  the mid-frequency average ``LMF`` (500/1000/2000 Hz) rounded to the nearest
  decibel (clause D.4); the spectral tag ``N``/``R``/``H`` follows the
  deviation rules of clause D.3.

Both methods evaluate octave-band sound pressure levels over the 16 Hz to
8000 Hz bands tabulated by the standard. The RC Mark II curves are generated
from the -5 dB/octave rule of Annex D (16 Hz equal to 31.5 Hz, with the low
frequencies not dropping below 55 dB), which reproduces Table D.1 exactly.

The balanced noise criteria (NCB), the room noise criterion for fluctuating
low-frequency noise (RNC, Annex A) and the numeric quality-assessment index
(QAI, clause D.5 - deferred by the standard to external references) are not
implemented here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from matplotlib.axes import Axes

from numpy.typing import ArrayLike

# ---------------------------------------------------------------------------
# Normative constants - ANSI/ASA S12.2-2019.
# ---------------------------------------------------------------------------

#: Octave-band centre frequencies, in hertz (Table 1 / Table D.1).
OCTAVE_BANDS: np.ndarray = np.array(
    [16.0, 31.5, 63.0, 125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0, 8000.0],
    dtype=np.float64,
)

#: NC curve designations (value at 1000 Hz), Table 1.
NC_INDICES: np.ndarray = np.array(
    [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70], dtype=np.float64
)

#: NC curve octave-band sound pressure levels, in dB (Table 1), one row per
#: entry of :data:`NC_INDICES`, columns aligned with :data:`OCTAVE_BANDS`.
NC_CURVES: np.ndarray = np.array(
    [
        [78, 61, 47, 36, 28, 22, 18, 14, 12, 11],  # NC-15
        [79, 63, 50, 40, 33, 26, 22, 20, 17, 16],  # NC-20
        [80, 65, 54, 44, 37, 31, 27, 24, 22, 22],  # NC-25
        [81, 68, 57, 48, 41, 35, 32, 29, 28, 27],  # NC-30
        [82, 71, 60, 52, 45, 40, 36, 34, 33, 32],  # NC-35
        [84, 74, 64, 56, 50, 44, 41, 39, 38, 37],  # NC-40
        [85, 76, 67, 60, 54, 49, 46, 44, 43, 42],  # NC-45
        [87, 79, 71, 64, 58, 54, 51, 49, 48, 47],  # NC-50
        [89, 82, 74, 67, 62, 58, 56, 54, 53, 52],  # NC-55
        [90, 85, 77, 71, 66, 63, 60, 59, 58, 57],  # NC-60
        [90, 88, 80, 75, 71, 68, 65, 64, 63, 62],  # NC-65
        [90, 90, 84, 79, 75, 72, 71, 70, 68, 68],  # NC-70
    ],
    dtype=np.float64,
)

#: Integer octave steps of each band relative to 1000 Hz (Annex D generation).
_RC_OCTAVE_STEPS: np.ndarray = np.array(
    [-6, -5, -4, -3, -2, -1, 0, 1, 2, 3], dtype=np.float64
)
_RC_LOW_FREQUENCY_FLOOR = 55.0  # dB, the 31.5 Hz floor (Annex D).

_N_BANDS = OCTAVE_BANDS.size
_F1000_INDEX = 6  # index of the 1000 Hz band in OCTAVE_BANDS.


@dataclass(frozen=True)
class NCResult:
    """Result of a Noise Criteria (NC) rating (ANSI/ASA S12.2-2019, tangency).

    :ivar rating: The NC rating (value of the highest NC curve touched).
    :ivar governing_frequency: Band, in hertz, where the touch occurs.
    :ivar frequencies: Octave-band centre frequencies evaluated, in hertz.
    :ivar levels: Measured octave-band sound pressure levels, in dB.
    """

    rating: float
    governing_frequency: float
    frequencies: np.ndarray
    levels: np.ndarray

    def plot(self, ax: "Axes | None" = None, *, language: str = "en", **kwargs: Any) -> "Axes":
        """Plot the measured spectrum against the NC curves.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from .._i18n import check_language
        from .._plot.room import plot_noise_criterion

        check_language(language)
        return plot_noise_criterion(self, ax=ax, language=language, **kwargs)


@dataclass(frozen=True)
class RCResult:
    """Result of a Room Criteria Mark II rating (ANSI/ASA S12.2-2019, Annex D).

    :ivar rating: Numerical RC designation ``LMF`` rounded to the nearest dB.
    :ivar lmf: Mid-frequency average (500/1000/2000 Hz), in dB (clause D.4).
    :ivar classification: Spectral tag, ``"N"`` (neutral), ``"R"`` (rumble),
        ``"H"`` (hiss) or ``"RH"`` (both) (clause D.3).
    :ivar reference_curve: The RC Mark II curve used for classification, in dB.
    :ivar frequencies: Octave-band centre frequencies evaluated, in hertz.
    :ivar levels: Measured octave-band sound pressure levels, in dB.
    """

    rating: int
    lmf: float
    classification: str
    reference_curve: np.ndarray
    frequencies: np.ndarray
    levels: np.ndarray

    @property
    def label(self) -> str:
        """The room-criterion label in the ``RC-NN(A)`` form (clause D.3.5)."""
        return f"RC-{self.rating}({self.classification})"

    def plot(self, ax: "Axes | None" = None, *, language: str = "en", **kwargs: Any) -> "Axes":
        """Plot the measured spectrum against the reference RC Mark II curve.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from .._i18n import check_language
        from .._plot.room import plot_room_criterion

        check_language(language)
        return plot_room_criterion(self, ax=ax, language=language, **kwargs)


def nc_curve(index: float) -> np.ndarray:
    """Octave-band levels of a Noise Criteria curve (ANSI/ASA S12.2-2019 Table 1).

    :param index: The NC designation. Integer designations from 15 to 70 in
        steps of five return the tabulated curve; intermediate values are
        linearly interpolated band by band.
    :return: The 10-band curve levels, in dB, aligned with :data:`OCTAVE_BANDS`.
    :raises ValueError: if ``index`` is outside the tabulated range.
    """
    if index < NC_INDICES[0] or index > NC_INDICES[-1]:
        raise ValueError(
            f"NC index {index} is outside the tabulated range "
            f"[{NC_INDICES[0]:.0f}, {NC_INDICES[-1]:.0f}]."
        )
    return np.array(
        [np.interp(index, NC_INDICES, NC_CURVES[:, k]) for k in range(_N_BANDS)]
    )


def rc_curve(index: float) -> np.ndarray:
    """Octave-band levels of a Room Criteria Mark II curve (Annex D, Table D.1).

    The curve has a constant slope of -5 dB/octave keyed to its value at
    1000 Hz; the 31.5 Hz level does not drop below 55 dB and the 16 Hz level
    equals the 31.5 Hz level.

    :param index: The RC designation (value at 1000 Hz).
    :return: The 10-band curve levels, in dB, aligned with :data:`OCTAVE_BANDS`.
    """
    curve = index - 5.0 * _RC_OCTAVE_STEPS
    low = max(index + 25.0, _RC_LOW_FREQUENCY_FLOOR)
    curve[1] = low  # 31.5 Hz floor
    curve[0] = low  # 16 Hz equals 31.5 Hz
    return curve


def _align_levels(levels: ArrayLike, frequencies: ArrayLike | None) -> np.ndarray:
    """Validate levels and align them to :data:`OCTAVE_BANDS`."""
    lv = np.atleast_1d(np.asarray(levels, dtype=np.float64))
    if lv.ndim != 1:
        raise ValueError("levels must be a 1-D vector of octave-band levels.")
    if frequencies is None:
        if lv.size != _N_BANDS:
            raise ValueError(
                f"levels must have {_N_BANDS} octave-band values (16 Hz - "
                f"8000 Hz) when frequencies are not given; got {lv.size}."
            )
        return lv
    fr = np.atleast_1d(np.asarray(frequencies, dtype=np.float64))
    if fr.shape != lv.shape:
        raise ValueError("levels and frequencies must have the same shape.")
    aligned = np.full(_N_BANDS, np.nan)
    for f, level in zip(fr, lv):
        matches = np.isclose(OCTAVE_BANDS, f, rtol=0.03)
        if not matches.any():
            raise ValueError(
                f"frequency {f} Hz is not one of the ANSI S12.2 octave bands "
                f"(16 Hz - 8000 Hz)."
            )
        aligned[np.argmax(matches)] = level
    return aligned


def noise_criterion(
    levels: ArrayLike, frequencies: ArrayLike | None = None
) -> NCResult:
    """Noise Criteria (NC) rating by the tangency method (ANSI/ASA S12.2-2019).

    The NC rating is the value of the highest NC curve touched by the measured
    octave-band spectrum. For each band the NC index whose curve passes through
    the measured level is found by interpolation; the rating is the maximum
    over bands and the governing band is where that maximum occurs.

    :param levels: Octave-band sound pressure levels, in dB. Without
        ``frequencies`` this must be the 10 bands from 16 Hz to 8000 Hz.
    :param frequencies: Optional band centre frequencies, in hertz, matching
        ``levels``; a subset of the ANSI S12.2 octave bands may be supplied.
    :return: An :class:`NCResult` with the rating and its ``.plot()``.
    :raises ValueError: for malformed inputs or unknown band frequencies.
    """
    aligned = _align_levels(levels, frequencies)
    valid = ~np.isnan(aligned)
    if not valid.any():
        raise ValueError("no valid octave-band levels were supplied.")
    per_band = np.full(_N_BANDS, -np.inf)
    for k in range(_N_BANDS):
        if valid[k]:
            per_band[k] = np.interp(
                aligned[k], NC_CURVES[:, k], NC_INDICES,
                left=NC_INDICES[0] - 1.0, right=NC_INDICES[-1] + 1.0,
            )
    governing = int(np.argmax(per_band))
    return NCResult(
        rating=float(per_band[governing]),
        governing_frequency=float(OCTAVE_BANDS[governing]),
        frequencies=OCTAVE_BANDS.copy(),
        levels=aligned,
    )


def room_criterion(
    levels: ArrayLike, frequencies: ArrayLike | None = None
) -> RCResult:
    """Room Criteria Mark II rating (ANSI/ASA S12.2-2019, Annex D).

    The numerical rating is the mid-frequency average ``LMF`` of the 500,
    1000 and 2000 Hz levels rounded to the nearest decibel (clause D.4). The
    spectral tag is neutral (``"N"``) when the levels at and below 500 Hz do
    not exceed the reference RC curve by more than 5 dB and the levels at and
    above 1000 Hz do not exceed it by more than 3 dB; rumble (``"R"``) when a
    low band exceeds by more than 5 dB; hiss (``"H"``) when a high band
    exceeds by more than 3 dB (clause D.3).

    :param levels: Octave-band sound pressure levels, in dB. Without
        ``frequencies`` this must be the 10 bands from 16 Hz to 8000 Hz.
    :param frequencies: Optional band centre frequencies, in hertz, matching
        ``levels``.
    :return: An :class:`RCResult` with the rating, tag and its ``.plot()``.
    :raises ValueError: if the 500/1000/2000 Hz mid-frequency bands are absent.
    """
    aligned = _align_levels(levels, frequencies)
    mid = aligned[5:8]  # 500, 1000, 2000 Hz.
    if np.isnan(mid).any():
        raise ValueError(
            "the 500, 1000 and 2000 Hz octave bands are required to compute "
            "the mid-frequency average (RC rating)."
        )
    lmf = float(np.mean(mid))
    rating = int(np.rint(lmf))
    reference = rc_curve(float(rating))
    deviation = aligned - reference

    low = slice(0, 6)   # 16 - 500 Hz (at and below 500 Hz).
    high = slice(6, _N_BANDS)  # 1000 - 8000 Hz (at and above 1000 Hz).
    low_dev = deviation[low][~np.isnan(deviation[low])]
    high_dev = deviation[high][~np.isnan(deviation[high])]
    rumble = low_dev.size > 0 and np.max(low_dev) > 5.0
    hiss = high_dev.size > 0 and np.max(high_dev) > 3.0
    tag = ("R" if rumble else "") + ("H" if hiss else "")
    classification = tag if tag else "N"

    return RCResult(
        rating=rating,
        lmf=lmf,
        classification=classification,
        reference_curve=reference,
        frequencies=OCTAVE_BANDS.copy(),
        levels=aligned,
    )
