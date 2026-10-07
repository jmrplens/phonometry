#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Sound reduction index of joints filled with fillers or seals (ISO 10140-1:2021 Annex J).

A joint is a line, not an area: a slit with or without a filler, a foam or
sealing tape, a gasket on the rebate of a door or window. Annex J therefore
normalizes the sound it lets through to a **metre** of joint rather than to a
square metre of element. With the joint mounted in a highly insulating
element, the level difference measured to ISO 10140-2 gives the sound
reduction index of joints per metre,

.. math::

   R_\mathrm{s} = L_1 - L_2 + 10 \lg \frac{S_\mathrm{n} l}{A l_\mathrm{n}}
   \tag{J.1}

with :math:`S_\mathrm{n} = 1` m², :math:`l_\mathrm{n} = 1` m, the joint length
:math:`l` and the equivalent absorption area :math:`A` of the receiving room
(:func:`joint_sound_reduction_index`).

**Flanking through the test element.** The element the joint sits in is part
of every measurement, so J.1 asks for the maximum the arrangement can show,
:math:`R_\mathrm{s,max}`, measured with the joint sealed on both sides. Unless
it lies 10 dB or more above the measured :math:`R_\mathrm{s}'`, the result is
corrected by the rules of ISO 10140-2:2021 A.3 (:func:`lab_joint_insulation`):

* a difference of 6 dB up to 10 dB: Formula (J.2),
  :math:`R_\mathrm{s} = -10 \lg(10^{-R_\mathrm{s}'/10} - 10^{-R_\mathrm{s,max}/10})`;
* less than 6 dB: a fixed correction of 1,3 dB, which is what Formula (J.2)
  gives at 6 dB, and the value is a minimum;
* :math:`R_\mathrm{s}'` above :math:`R_\mathrm{s,max} - 3` dB: the lower limit
  of :math:`R_\mathrm{s}` may be set to :math:`R_\mathrm{s,max}` itself,
  presented in brackets as a minimum value, e.g. :math:`(R_\mathrm{s} \ge
  50{,}4` dB).

**Single numbers.** :math:`R_\mathrm{s,w}` (:math:`C`; :math:`C_\mathrm{tr}`)
of ISO 717-1:2020 on the 16 bands 100 Hz to 3 150 Hz, with
:math:`C_{100\text{-}5000}` and :math:`C_\mathrm{tr,100\text{-}5000}` when the
bands reach 5 000 Hz, as the form of Figure J.7 prints them. Where a band is
above :math:`R_\mathrm{s,max} - 3` dB, J.1 rates the curve a second time with
those indicative bands taken as infinitely high; a difference of more than
1 dB between the two puts the single numbers in brackets too.

**The arrangement.** J.2.1 asks for a joint longer than 1 m and no wider
than 50 mm, J.2.2 for at least 5,0 m of a gap between the parts of a window or
door (:func:`check_joint_test_element`), whose width is read at four positions
or more that may not differ by more than 0,3 mm (:func:`check_gap_width`). A
variable slit is measured at its nominal gap width :math:`b_\mathrm{n}` (5 mm
when the manufacturer gives none), at the minimum width under a force of
normally 100 N/m, and at :math:`b_\mathrm{n} + 3` mm (J.4,
:func:`check_joint_gap_series`), and reported as single numbers against the
gap width (:func:`joint_gap_series`, Figures J.8 and J.9).

Citations are to ISO 10140-1:2021 (third edition) Annex J and, for the
flanking rules it calls in, to ISO 10140-2:2021 A.3.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from ..._internal.frozen import OwnsArrays
from ..._internal.levels_math import energy_sum
from ..._internal.validation import (
    check_engine,
    require_choice,
    require_equal_shapes,
    require_finite_array,
    require_non_negative,
    require_positive,
    require_positive_array,
    require_ranks,
    require_same_length,
)
from .floor_covering_improvement import improvement_octave_bands
from .insulation import _as_band_levels
from .ratings import (
    _EXTENDED_RANGES,
    _FREQ_THIRD_OCTAVE,
    _INDEX_500_THIRD,
    _MAX_UNFAVOURABLE_THIRD,
    _REF_THIRD_OCTAVE,
    _SPECTRUM1_THIRD,
    _SPECTRUM2_THIRD,
    WeightedRatingResult,
    _best_shift,
    _match_bands,
    _round_half_up_tenths,
    weighted_rating,
    weighted_rating_extended,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

    from ..._report.metadata import ReportMetadata

__all__ = [
    "GapWidthCheck",
    "JointGapSeries",
    "JointGapSeriesCheck",
    "JointOpenBandRating",
    "JointTestElementCheck",
    "LabJointInsulationResult",
    "check_gap_width",
    "check_joint_gap_series",
    "check_joint_test_element",
    "joint_gap_series",
    "joint_sound_reduction_index",
    "lab_joint_insulation",
]

#: Reference area :math:`S_\mathrm{n}` of Formula (J.1), in m².
_REFERENCE_AREA_M2 = 1.0
#: Reference length :math:`l_\mathrm{n}` of Formula (J.1), in m.
_REFERENCE_LENGTH_M = 1.0

#: The margin of :math:`R_\mathrm{s,max}` over :math:`R_\mathrm{s}'` at and
#: above which no correction is needed: "Unless this value is 10 dB higher
#: than the measured value, the measurement results require correction" (J.1).
_NO_CORRECTION_DB = 10.0
#: The margin below which Formula (J.2) gives way to the fixed correction:
#: "If the difference ... is less than 6 dB in any of the frequency bands, the
#: correction shall be 1,3 dB" (J.1, ISO 10140-2:2021 A.3).
_FORMULA_MARGIN_DB = 6.0
#: The fixed correction at the limit of measurement, in dB; ISO 10140-2:2021
#: A.3: "this corresponds to a difference of 6 dB".
_LIMIT_CORRECTION_DB = 1.3
#: "If R's is larger than Rs,max - 3 dB, the lower limit of the sound reduction
#: index Rs may be set as Rs,max" (J.1).
_MAXIMUM_MARGIN_DB = 3.0
#: "If that result differs by more than 1 dB from that first directly
#: determined, the single number ratings shall also be presented in brackets"
#: (J.1).
_BRACKET_DB = 1.0

#: Slack on the inclusive margins above. Bands are read to 0,1 dB, and a
#: difference such as 36,3 - 30,3 is 5,999999999999996 in binary arithmetic:
#: nine orders of magnitude below a decibel is far above that error and far
#: below any reading.
_SLACK_DB = 1e-9

#: J.2.1: "The length of the joint shall be greater than 1 m", in m.
_MIN_JOINT_LENGTH_M = 1.0
#: J.2.1: "the width of the joint shall be no greater than 50 mm", in mm.
_MAX_JOINT_WIDTH_MM = 50.0
#: J.2.2: a gap between the parts of a window or door "shall have a length of
#: at least 5,0 m", in m.
_MIN_GAP_LENGTH_M = 5.0
#: J.2.2: "Determine the gap width at a minimum of four positions".
_MIN_GAP_READINGS = 4
#: J.2.2: "The results shall not deviate by more than 0,3 mm", in mm.
_MAX_GAP_SPREAD_MM = 0.3
#: Relative slack on the inclusive length and width bounds, for the same
#: reason as :data:`_SLACK_DB`.
_BOUND_SLACK = 1e-9

#: J.4 a): "if unknown bn = 5 mm is to be taken", in mm.
_DEFAULT_NOMINAL_GAP_MM = 5.0
#: J.4 c): the third gap width is "a gap width 3 mm more than nominal", in mm.
_WORKING_RANGE_MM = 3.0
#: How far a measured gap width may lie from a width J.4 asks for and still be
#: that width, in mm. J.4 gives no tolerance; the gap width ``b`` is itself the
#: average of readings J.2.2 lets spread over 0,3 mm, so a width within that
#: spread of the target is the target as far as the readings can tell.
_GAP_MATCH_MM = _MAX_GAP_SPREAD_MM

#: The three single numbers J.5.2 i) asks for as a function of gap width.
_SINGLE_NUMBERS = ("r_s_w", "r_s_w_c", "r_s_w_ctr")

#: Names of the four per-band regimes of the flanking correction.
_REGIMES = ("uncorrected", "corrected", "limit", "maximum")


def joint_sound_reduction_index(
    l1_db: ArrayLike,
    l2_db: ArrayLike,
    absorption_m2: ArrayLike,
    *,
    joint_length_m: float,
) -> np.ndarray:
    r"""Sound reduction index of joints per metre, Formula (J.1).

    .. math::

       R_\mathrm{s} = L_1 - L_2 + 10 \lg \frac{S_\mathrm{n} l}{A l_\mathrm{n}}

    with :math:`S_\mathrm{n} = 1` m² and :math:`l_\mathrm{n} = 1` m. A joint
    twice as long lets twice the power through, so the index of a metre is
    3 dB above the one a 2 m joint gives without the normalization.

    The same formula, with the joint sealed on both sides, gives the maximum
    of the test arrangement :math:`R_\mathrm{s,max}` that
    :func:`lab_joint_insulation` corrects against (J.1).

    :param l1_db: Energy average sound pressure level in the source room, in
        dB, one value per band, or a ``(positions, bands)`` array that is
        energy-averaged over the positions (ISO 10140-2).
    :param l2_db: The same in the receiving room, in dB.
    :param absorption_m2: Equivalent absorption area :math:`A` of the
        receiving room per band, in m².
    :param joint_length_m: Length :math:`l` of the joint under test, in m.
    :return: :math:`R_\mathrm{s}` per band, in dB.
    :raises ValueError: If the inputs disagree in band count, a level is not
        finite, an area is not positive, or the length is not positive.
    """
    l1 = _as_band_levels(np.asarray(l1_db, dtype=np.float64), "l1_db")
    l2 = _as_band_levels(np.asarray(l2_db, dtype=np.float64), "l2_db")
    area = require_positive_array(absorption_m2, "absorption_m2")
    require_equal_shapes(
        "joint_sound_reduction_index",
        {"l1_db": l1.shape, "l2_db": l2.shape, "absorption_m2": area.shape},
        "band",
    )
    length = require_positive(joint_length_m, "joint_length_m")
    ratio = (_REFERENCE_AREA_M2 * length) / (area * _REFERENCE_LENGTH_M)
    return np.asarray(l1 - l2 + 10.0 * np.log10(ratio), dtype=np.float64)


@dataclass(frozen=True)
class JointOpenBandRating:
    r"""The single numbers with the indicative bands taken as infinitely high (J.1).

    Where :math:`R_\mathrm{s}'` is above :math:`R_\mathrm{s,max} - 3` dB the
    band says only that the joint is better than the arrangement can show.
    J.1 rates the curve a second time with an infinitely high sound reduction
    index in those bands: they then add no unfavourable deviation and no
    transmitted energy. A term is ``None`` when it is unbounded, which happens
    when every band it sums is indicative, or when the bands do not reach its
    range.

    :ivar open_frequencies_hz: The indicative bands, in Hz.
    :ivar r_s_w_db: :math:`R_\mathrm{s,w}`, in dB, or ``None``.
    :ivar c_db: :math:`C`, in dB, or ``None``.
    :ivar ctr_db: :math:`C_\mathrm{tr}`, in dB, or ``None``.
    :ivar c_100_5000_db: :math:`C_{100\text{-}5000}`, in dB, or ``None``.
    :ivar ctr_100_5000_db: :math:`C_\mathrm{tr,100\text{-}5000}`, in dB, or
        ``None``.
    """

    open_frequencies_hz: tuple[float, ...]
    r_s_w_db: int | None
    c_db: int | None
    ctr_db: int | None
    c_100_5000_db: int | None
    ctr_100_5000_db: int | None

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the open-band single numbers beside the bands taken as open.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.joint_insulation import plot_joint_open_band_rating

        check_language(language)
        return plot_joint_open_band_rating(self, ax=ax, language=language, **kwargs)


def _sum_term(
    values: np.ndarray, spectrum: tuple[int, ...] | np.ndarray, rating: int
) -> int | None:
    """``XAj - Xw`` over *values*, or ``None`` when every band is open."""
    finite = np.isfinite(values)
    if not np.any(finite):
        return None
    spec = np.asarray(spectrum, dtype=np.float64)
    x_aj = -energy_sum(spec[finite] - values[finite])
    return math.floor(x_aj + 0.5) - rating


def _open_band_rating(
    r_s: np.ndarray, freqs: np.ndarray, core: np.ndarray, open_mask: np.ndarray
) -> JointOpenBandRating:
    """Rate *r_s* with the bands of *open_mask* set to an infinite index.

    The reference curve is shifted as ISO 717-1:2020 Clause 4.4 shifts it, but
    an infinite band never lies below it, so it adds no unfavourable
    deviation; and it transmits nothing, so it drops out of the sums of the
    adaptation terms (Clause 4.5 and Annex B).
    """
    values = _round_half_up_tenths(r_s).copy()
    values[open_mask] = np.inf
    opened = tuple(float(f) for f in freqs[open_mask])
    core_values = values[core]
    if not np.any(np.isfinite(core_values)):
        return JointOpenBandRating(opened, None, None, None, None, None)
    reference = np.asarray(_REF_THIRD_OCTAVE, dtype=np.float64)
    shift, _ = _best_shift(core_values, reference, _MAX_UNFAVOURABLE_THIRD)
    rating = int(_REF_THIRD_OCTAVE[_INDEX_500_THIRD]) + round(shift)
    band_freqs, spectrum1, spectrum2 = _EXTENDED_RANGES["100_5000"]
    wide = _match_bands(freqs, band_freqs)
    return JointOpenBandRating(
        open_frequencies_hz=opened,
        r_s_w_db=rating,
        c_db=_sum_term(core_values, _SPECTRUM1_THIRD, rating),
        ctr_db=_sum_term(core_values, _SPECTRUM2_THIRD, rating),
        c_100_5000_db=None
        if wide is None
        else _sum_term(values[wide], spectrum1, rating),
        ctr_100_5000_db=None
        if wide is None
        else _sum_term(values[wide], spectrum2, rating),
    )


def _single_numbers(
    rw: int | None,
    c: int | None,
    ctr: int | None,
    c_wide: int | None,
    ctr_wide: int | None,
) -> tuple[int | None, ...]:
    """``Rw``, ``Rw + C``, ``Rw + Ctr`` and the two enlarged-range sums."""

    def plus(term: int | None) -> int | None:
        return None if rw is None or term is None else rw + term

    return (rw, plus(c), plus(ctr), plus(c_wide), plus(ctr_wide))


@dataclass(frozen=True)
class LabJointInsulationResult(OwnsArrays):
    r"""Sound reduction index of a joint per metre (ISO 10140-1:2021 Annex J).

    :ivar frequencies_hz: One-third-octave band centre frequencies, in Hz.
    :ivar r_s_measured_db: :math:`R_\mathrm{s}'`, the index measured with the
        test element in the test opening, per band, in dB.
    :ivar r_s_max_db: :math:`R_\mathrm{s,max}`, the maximum of the test
        arrangement with the joint sealed on both sides, in dB.
    :ivar r_s_db: :math:`R_\mathrm{s}`, corrected for the flanking through the
        arrangement, in dB. In the ``"limit"`` and ``"maximum"`` bands it is a
        minimum value.
    :ivar regime: How each band was corrected: ``"uncorrected"``
        (:math:`R_\mathrm{s,max}` at least 10 dB above), ``"corrected"``
        (Formula (J.2), 6 dB to 10 dB), ``"limit"`` (the fixed 1,3 dB below
        6 dB) or ``"maximum"`` (above :math:`R_\mathrm{s,max} - 3` dB, set to
        :math:`R_\mathrm{s,max}`).
    :ivar joint_length_m: Length :math:`l` of the joint, in m, or ``None``
        when not given; the form of Figure J.7 prints it as the test length.
    :ivar rating: :math:`R_\mathrm{s,w}` (:math:`C`; :math:`C_\mathrm{tr}`) of
        ISO 717-1:2020, or ``None`` without the 16 bands 100 Hz to 3 150 Hz.
    :ivar c_100_5000_db: :math:`C_{100\text{-}5000}`, in dB, or ``None``
        without the bands 100 Hz to 5 000 Hz.
    :ivar ctr_100_5000_db: :math:`C_\mathrm{tr,100\text{-}5000}`, in dB, or
        ``None``.
    :ivar max_rating: The ISO 717-1 rating of :math:`R_\mathrm{s,max}`, the
        maximum sound insulation of the arrangement J.5.2 a) asks the report
        to state, or ``None``.
    :ivar open_band_rating: The single numbers with the indicative bands
        taken as infinitely high, or ``None`` when no band is indicative or
        there is no rating.
    """

    frequencies_hz: np.ndarray
    r_s_measured_db: np.ndarray
    r_s_max_db: np.ndarray
    r_s_db: np.ndarray
    regime: tuple[str, ...]
    joint_length_m: float | None
    rating: WeightedRatingResult | None
    c_100_5000_db: int | None
    ctr_100_5000_db: int | None
    max_rating: WeightedRatingResult | None
    open_band_rating: JointOpenBandRating | None

    def __post_init__(self) -> None:
        """Reject columns of different lengths and an unknown regime.

        The figure, the table of the form and the octave conversion read the
        four columns against ``frequencies_hz`` band by band, and the regime
        decides which bands the form prints as minimum values.

        :raises ValueError: if the per-band columns disagree, or a regime is
            not one of the four.
        """
        require_ranks(
            self,
            frequencies_hz=1,
            r_s_measured_db=1,
            r_s_max_db=1,
            r_s_db=1,
        )
        require_same_length(
            self, "frequencies_hz", "r_s_measured_db", "r_s_max_db", "r_s_db"
        )
        if len(self.regime) != np.size(self.frequencies_hz):
            msg = (
                "LabJointInsulationResult: 'regime' must carry one entry per "
                f"band; got {len(self.regime)} for {np.size(self.frequencies_hz)}."
            )
            raise ValueError(msg)
        for entry in self.regime:
            require_choice(entry, "regime", _REGIMES)

    @property
    def minimum_value(self) -> np.ndarray:
        r"""Bands whose :math:`R_\mathrm{s}` is a minimum value (``"limit"`` or ``"maximum"``)."""
        return np.asarray([r in {"limit", "maximum"} for r in self.regime], dtype=bool)

    @property
    def indicative(self) -> np.ndarray:
        r"""Bands where :math:`R_\mathrm{s}' > R_\mathrm{s,max} - 3` dB (J.1)."""
        return _indicative_bands(
            np.asarray(self.r_s_measured_db), np.asarray(self.r_s_max_db)
        )

    @property
    def bracketed(self) -> bool:
        r"""Whether the single numbers are presented in brackets (J.1).

        They are when rating the indicative bands as infinitely high moves any
        of :math:`R_\mathrm{s,w}`, :math:`R_\mathrm{s,w} + C`,
        :math:`R_\mathrm{s,w} + C_\mathrm{tr}` or their enlarged-range sums
        by more than 1 dB, or leaves one of them unbounded.
        """
        if self.rating is None or self.open_band_rating is None:
            return False
        direct = _single_numbers(
            self.rating.rating,
            self.rating.c,
            self.rating.ctr,
            self.c_100_5000_db,
            self.ctr_100_5000_db,
        )
        opened = self.open_band_rating
        other = _single_numbers(
            opened.r_s_w_db,
            opened.c_db,
            opened.ctr_db,
            opened.c_100_5000_db,
            opened.ctr_100_5000_db,
        )
        for first, second in zip(direct, other, strict=True):
            if first is None:
                continue
            if second is None or abs(second - first) > _BRACKET_DB:
                return True
        return False

    @property
    def r_s_w_db(self) -> int | None:
        r""":math:`R_\mathrm{s,w}`, in dB, or ``None`` without a rating."""
        return None if self.rating is None else self.rating.rating

    @property
    def r_s_w_c_db(self) -> int | None:
        r""":math:`R_\mathrm{s,w} + C`, in dB, or ``None`` without a rating."""
        return None if self.rating is None else self.rating.rating + self.rating.c

    @property
    def r_s_w_ctr_db(self) -> int | None:
        r""":math:`R_\mathrm{s,Atr} = R_\mathrm{s,w} + C_\mathrm{tr}`, in dB, or ``None``."""
        return None if self.rating is None else self.rating.rating + self.rating.ctr

    def octave_bands(self) -> tuple[np.ndarray, np.ndarray]:
        r"""``(octave centres in Hz, Rs,oct in dB)`` from the three thirds of each octave.

        :math:`R_\mathrm{oct} = -10 \lg[(1/3) \sum 10^{-R_j/10}]`: the
        transmitted power of the three thirds averaged, as Figure J.9 plots
        a joint at several gap widths in octave bands.
        """
        return improvement_octave_bands(self.r_s_db, self.frequencies_hz)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot :math:`R_\mathrm{s}` per band with the maximum of the arrangement.

        The test curve with its minimum values marked, :math:`R_\mathrm{s}'`
        and :math:`R_\mathrm{s,max}`, and the shifted ISO 717-1 reference
        curve over the rating range, as the diagram of Figure J.7. Requires
        matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.joint_insulation import plot_lab_joint_insulation

        check_language(language)
        return plot_lab_joint_insulation(self, ax=ax, language=language, **kwargs)

    def report(
        self,
        path: str,
        *,
        metadata: ReportMetadata | None = None,
        engine: str = "reportlab",
        verbose: bool = False,
        language: str = "en",
    ) -> str:
        r"""Render the form of Figure J.7 to a one-page PDF.

        The header of the form (client, specimen, date, test length,
        separation wall, test noise, room volumes, maximum joint sound
        reduction index, mounting and climate), the table of
        :math:`R_\mathrm{s}` from 100 Hz to 5 000 Hz beside its diagram, and
        the evaluation according to ISO 717-1:
        :math:`R_\mathrm{s,w}` (:math:`C`; :math:`C_\mathrm{tr}`),
        :math:`C_{100\text{-}5000}` and
        :math:`C_\mathrm{tr,100\text{-}5000}`, in brackets when J.1 puts
        them there. Minimum values are printed with ``≥``, those set to
        :math:`R_\mathrm{s,max}` in brackets.

        :param path: Destination path of the PDF file.
        :param metadata: Optional :class:`~phonometry.ReportMetadata`; its
            ``separating_element`` and ``test_signal`` fill the separation
            wall and test noise rows of the form.
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: When ``True``, the table also shows
            :math:`R_\mathrm{s}'` and :math:`R_\mathrm{s,max}`.
        :param language: ``"en"`` (default) or ``"es"``.
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` or ``language`` is unknown, or the
            result carries no rating (the 16 bands 100 Hz to 3 150 Hz are
            missing).
        :raises ImportError: If reportlab or matplotlib is not installed.
        """
        from ..._i18n import check_language
        from ..._report.iso10140_1 import render_joint_form

        check_engine(engine)
        check_language(language)
        if self.rating is None:
            msg = (
                "The Figure J.7 form needs the ISO 717-1 rating, formed on the 16 "
                "one-third-octave bands 100 Hz to 3150 Hz; this result has none."
            )
            raise ValueError(msg)
        return render_joint_form(
            self, path, metadata=metadata, verbose=verbose, language=language
        )


def _indicative_bands(measured: np.ndarray, maximum: np.ndarray) -> np.ndarray:
    r"""Bands where :math:`R_\mathrm{s}' > R_\mathrm{s,max} - 3` dB (J.1).

    The one reading of the rule: on the measured :math:`R_\mathrm{s}'`, the
    condition the bracketed lower limit is set by, whichever correction the
    band then received. :attr:`LabJointInsulationResult.indicative` and the
    open-band rating of :func:`lab_joint_insulation` both call it, so the two
    can never disagree on which bands are open.
    """
    margin = maximum - measured
    return np.asarray(margin < _MAXIMUM_MARGIN_DB - _SLACK_DB, dtype=bool)


def _correct(
    measured: np.ndarray, maximum: np.ndarray, *, limit_at_maximum: bool
) -> tuple[np.ndarray, tuple[str, ...]]:
    """The flanking correction of J.1 and ISO 10140-2:2021 A.3, band by band."""
    margin = maximum - measured
    corrected = np.empty_like(measured)
    regime: list[str] = []
    for k, d in enumerate(margin):
        if d >= _NO_CORRECTION_DB - _SLACK_DB:
            corrected[k] = measured[k]
            regime.append("uncorrected")
        elif d >= _FORMULA_MARGIN_DB - _SLACK_DB:
            # Formula (J.2); the argument is positive because d >= 6 dB here.
            corrected[k] = -10.0 * math.log10(
                10.0 ** (-measured[k] / 10.0) - 10.0 ** (-maximum[k] / 10.0)
            )
            regime.append("corrected")
        elif limit_at_maximum and d < _MAXIMUM_MARGIN_DB - _SLACK_DB:
            corrected[k] = maximum[k]
            regime.append("maximum")
        else:
            corrected[k] = measured[k] + _LIMIT_CORRECTION_DB
            regime.append("limit")
    return corrected, tuple(regime)


def lab_joint_insulation(
    r_s_measured_db: ArrayLike,
    r_s_max_db: ArrayLike,
    frequencies_hz: ArrayLike,
    *,
    joint_length_m: float | None = None,
    limit_at_maximum: bool = True,
) -> LabJointInsulationResult:
    r"""Sound reduction index of a joint, corrected for the test arrangement (J.1).

    :math:`R_\mathrm{s}'` and :math:`R_\mathrm{s,max}` are both Formula (J.1)
    (:func:`joint_sound_reduction_index`): the first with the joint as it is
    tested, the second with it sealed on both sides, "e.g. with elastic
    sealant". Band by band, with the difference
    :math:`d = R_\mathrm{s,max} - R_\mathrm{s}'`:

    * :math:`d \ge 10` dB: no correction, :math:`R_\mathrm{s} = R_\mathrm{s}'`;
    * :math:`6 \le d < 10` dB: Formula (J.2),
      :math:`R_\mathrm{s} = -10 \lg(10^{-R_\mathrm{s}'/10} - 10^{-R_\mathrm{s,max}/10})`;
    * :math:`d < 6` dB: :math:`R_\mathrm{s} = R_\mathrm{s}' + 1{,}3` dB, the
      correction Formula (J.2) gives at 6 dB, a minimum value
      (ISO 10140-2:2021 A.3);
    * :math:`d < 3` dB, with ``limit_at_maximum`` (the default): the lower
      limit set to :math:`R_\mathrm{s} = R_\mathrm{s,max}`, which J.1 allows
      ("may") and presents in brackets as a minimum value.

    The last rule is exact rather than conservative: the arrangement passes
    :math:`\tau_\mathrm{s,max}` alone and :math:`\tau_\mathrm{s} +
    \tau_\mathrm{s,max}` with the joint, so a measured index within 3 dB of
    the maximum means :math:`\tau_\mathrm{s} < \tau_\mathrm{s,max}`.

    With the 16 bands 100 Hz to 3 150 Hz the result carries
    :math:`R_\mathrm{s,w}` (:math:`C`; :math:`C_\mathrm{tr}`) of ISO 717-1, and
    with the 18 bands to 5 000 Hz :math:`C_{100\text{-}5000}` and
    :math:`C_\mathrm{tr,100\text{-}5000}`, the evaluation of Figure J.7. Bands
    with :math:`d < 3` dB are indicative: J.1 rates the curve again with them
    taken as infinitely high, and a change of more than 1 dB puts the single
    numbers in brackets (:attr:`LabJointInsulationResult.bracketed`). The
    indicative bands are read on :math:`R_\mathrm{s}'`, the same condition as
    the bracketed lower limit, whichever rule corrected them.

    :param r_s_measured_db: :math:`R_\mathrm{s}'` per one-third-octave band,
        in dB.
    :param r_s_max_db: :math:`R_\mathrm{s,max}` per band, in dB.
    :param frequencies_hz: Band centre frequencies, in Hz.
    :param joint_length_m: Length of the joint under test, in m, kept for the
        form of Figure J.7; ``None`` leaves that row empty.
    :param limit_at_maximum: Set the bands within 3 dB of the maximum to
        :math:`R_\mathrm{s,max}` (default), or give them the 1,3 dB correction
        like the other bands below 6 dB.
    :return: A :class:`LabJointInsulationResult`.
    :raises ValueError: If the three inputs disagree in length, a value is not
        finite, a frequency or the joint length is not positive.
    """
    freqs = require_positive_array(frequencies_hz, "frequencies_hz")
    measured = require_finite_array(r_s_measured_db, "r_s_measured_db")
    maximum = require_finite_array(r_s_max_db, "r_s_max_db")
    require_equal_shapes(
        "lab_joint_insulation",
        {
            "r_s_measured_db": measured.shape,
            "r_s_max_db": maximum.shape,
            "frequencies_hz": freqs.shape,
        },
        "band",
    )
    length = (
        None
        if joint_length_m is None
        else require_positive(joint_length_m, "joint_length_m")
    )
    r_s, regime = _correct(measured, maximum, limit_at_maximum=limit_at_maximum)

    core = _match_bands(freqs, _FREQ_THIRD_OCTAVE)
    rating: WeightedRatingResult | None = None
    max_rating: WeightedRatingResult | None = None
    c_wide: int | None = None
    ctr_wide: int | None = None
    opened: JointOpenBandRating | None = None
    if core is not None:
        rating = weighted_rating(r_s[core])
        max_rating = weighted_rating(maximum[core])
        extended = weighted_rating_extended(r_s, freqs)
        c_wide = None if extended.c_100_5000 is None else int(extended.c_100_5000)
        ctr_wide = None if extended.ctr_100_5000 is None else int(extended.ctr_100_5000)
        open_mask = _indicative_bands(measured, maximum)
        if bool(np.any(open_mask)):
            opened = _open_band_rating(r_s, freqs, core, open_mask)
    return LabJointInsulationResult(
        frequencies_hz=freqs,
        r_s_measured_db=measured,
        r_s_max_db=maximum,
        r_s_db=np.asarray(r_s, dtype=np.float64),
        regime=regime,
        joint_length_m=length,
        rating=rating,
        c_100_5000_db=c_wide,
        ctr_100_5000_db=ctr_wide,
        max_rating=max_rating,
        open_band_rating=opened,
    )


# --- J.2: the test element ---------------------------------------------------


@dataclass(frozen=True)
class JointTestElementCheck:
    """Whether a joint is long and narrow enough to be tested (J.2.1, J.2.2).

    The bounds are the clause's, so the verdicts are read from the length and
    the width and are not fields: a check cannot be built to pass a joint the
    clause fails.

    :ivar joint_length_m: Length of the joint, in m.
    :ivar joint_width_mm: Width of the joint, in mm.
    :ivar window_or_door_gap: Whether the joint is a gap between the parts of
        a window or door, which J.2.2 asks to be at least 5,0 m long.
    """

    joint_length_m: float
    joint_width_mm: float
    window_or_door_gap: bool

    @property
    def length_ok(self) -> bool:
        """Whether the length is greater than 1 m and, for a window or door gap, at least 5,0 m.

        The 1 m bound is exclusive and the 5,0 m bound inclusive, read with a
        relative slack so that a length on it is not failed by rounding.
        """
        length = self.joint_length_m
        if math.isnan(length) or length <= _MIN_JOINT_LENGTH_M:
            return False
        return not self.window_or_door_gap or length >= _MIN_GAP_LENGTH_M * (
            1.0 - _BOUND_SLACK
        )

    @property
    def width_ok(self) -> bool:
        """Whether the width is no greater than 50 mm."""
        return self.joint_width_mm <= _MAX_JOINT_WIDTH_MM * (1.0 + _BOUND_SLACK)

    @property
    def passes(self) -> bool:
        """Whether both the length and the width hold."""
        return self.length_ok and self.width_ok

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a JointTestElementCheck has no truth value; read its '.passes'"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the length and width of the joint against their bounds.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.joint_insulation import plot_joint_test_element_check

        check_language(language)
        return plot_joint_test_element_check(self, ax=ax, language=language, **kwargs)


def check_joint_test_element(
    joint_length_m: float,
    joint_width_mm: float,
    *,
    window_or_door_gap: bool = False,
) -> JointTestElementCheck:
    """Check the length and width of a joint before it is tested (J.2.1, J.2.2).

    J.2.1: "The length of the joint shall be greater than 1 m and the width of
    the joint shall be no greater than 50 mm." J.2.2 adds, for gaps between
    the parts of windows and doors, that the gap under test "shall have a
    length of at least 5,0 m with a uniform cross-section", which may be the
    sum of several gaps. The 1 m bound is exclusive, the others inclusive.

    The uniform cross-section, the shape of Figure J.1 and the design of the
    environment around the joint (J.2.1 "can only give advice") carry no
    number and are not judged here.

    :param joint_length_m: Total length of the joint under test, in m.
    :param joint_width_mm: Width of the joint, in mm (the gap width ``b``).
    :param window_or_door_gap: ``True`` for a gap between the parts of a
        window or door (J.2.2).
    :return: A :class:`JointTestElementCheck`.
    :raises ValueError: If the length is not positive or the width is
        negative or not finite.
    """
    length = require_positive(joint_length_m, "joint_length_m")
    width = require_non_negative(joint_width_mm, "joint_width_mm")
    return JointTestElementCheck(
        joint_length_m=length,
        joint_width_mm=width,
        window_or_door_gap=bool(window_or_door_gap),
    )


@dataclass(frozen=True)
class GapWidthCheck:
    """The gap width read along the joint, and whether the readings agree (J.2.2).

    Everything else is read from the readings, so a check cannot be built to
    pass readings the clause fails.

    :ivar readings_mm: The gap widths read along the joint, in mm.
    """

    readings_mm: tuple[float, ...]

    def __post_init__(self) -> None:
        """Hold the readings as a tuple of floats.

        :raises ValueError: If there is no reading.
        """
        readings = tuple(float(w) for w in self.readings_mm)
        if not readings:
            msg = "GapWidthCheck: 'readings_mm' must hold at least one reading."
            raise ValueError(msg)
        object.__setattr__(self, "readings_mm", readings)

    @property
    def gap_width_mm(self) -> float:
        """The average of the readings, the gap width ``b``, in mm."""
        return float(np.mean(self.readings_mm))

    @property
    def spread_mm(self) -> float:
        """The largest difference between two readings, in mm."""
        return max(self.readings_mm) - min(self.readings_mm)

    @property
    def enough_positions(self) -> bool:
        """Whether there are at least four readings."""
        return len(self.readings_mm) >= _MIN_GAP_READINGS

    @property
    def uniform(self) -> bool:
        """Whether no two readings differ by more than 0,3 mm."""
        return self.spread_mm <= _MAX_GAP_SPREAD_MM + _SLACK_DB

    @property
    def passes(self) -> bool:
        """Whether both hold; otherwise J.2.2 says to readjust the mounting."""
        return self.enough_positions and self.uniform

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a GapWidthCheck has no truth value; read its '.passes'"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the readings with their average and the 0,3 mm band.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.joint_insulation import plot_gap_width_check

        check_language(language)
        return plot_gap_width_check(self, ax=ax, language=language, **kwargs)


def check_gap_width(readings_mm: ArrayLike) -> GapWidthCheck:
    """Check the gap width read along the joint and average it (J.2.2).

    "Determine the gap width at a minimum of four positions, evenly
    distributed over the total length of sealing. The results shall not
    deviate by more than 0,3 mm, otherwise readjust the mounting. The average
    value is denoted as gap width, b." The deviation is read between the
    readings, the largest minus the smallest, which is the stricter of the
    two ways the sentence can be read: a deviation of each reading from the
    average would allow twice the spread. Whether the positions are evenly
    distributed is not judged, since only the widths are given.

    :param readings_mm: The gap widths read, in mm, in any order.
    :return: A :class:`GapWidthCheck`.
    :raises ValueError: If there is no reading, or a reading is negative or
        not finite.
    """
    widths = require_finite_array(readings_mm, "readings_mm")
    if np.any(widths < 0.0):
        msg = "'readings_mm' must be non-negative."
        raise ValueError(msg)
    return GapWidthCheck(readings_mm=tuple(float(w) for w in widths))


# --- J.4 and J.5: a variable slit at several gap widths ------------------------


@dataclass(frozen=True)
class JointGapSeries(OwnsArrays):
    r"""Single numbers of a variable slit against its gap width (J.4, J.5.2 h), i)).

    :ivar gap_widths_mm: The gap widths measured, ascending, in mm.
    :ivar results: The :class:`LabJointInsulationResult` at each width.
    :ivar nominal_gap_mm: The nominal gap width :math:`b_\mathrm{n}`, in mm.
    :ivar minimum_gap_mm: The minimal gap width :math:`b_\mathrm{min}` at the
        maximal pressure, in mm, or ``None`` when not given.
    :ivar r_s_w_db: :math:`R_\mathrm{s,w}` at each width, in dB.
    :ivar r_s_w_c_db: :math:`R_\mathrm{s,w} + C` at each width, in dB.
    :ivar r_s_w_ctr_db: :math:`R_\mathrm{s,Atr} = R_\mathrm{s,w} +
        C_\mathrm{tr}` at each width, in dB.
    """

    gap_widths_mm: np.ndarray
    results: tuple[LabJointInsulationResult, ...]
    nominal_gap_mm: float
    minimum_gap_mm: float | None
    r_s_w_db: np.ndarray
    r_s_w_c_db: np.ndarray
    r_s_w_ctr_db: np.ndarray

    def __post_init__(self) -> None:
        """Reject columns of different lengths.

        :raises ValueError: if the widths, results and single numbers disagree.
        """
        require_ranks(self, gap_widths_mm=1, r_s_w_db=1, r_s_w_c_db=1, r_s_w_ctr_db=1)
        require_same_length(
            self,
            "gap_widths_mm",
            "r_s_w_db",
            "r_s_w_c_db",
            "r_s_w_ctr_db",
            axis="width",
        )
        if len(self.results) != np.size(self.gap_widths_mm):
            msg = (
                "JointGapSeries: 'results' must carry one result per gap width; "
                f"got {len(self.results)} for {np.size(self.gap_widths_mm)}."
            )
            raise ValueError(msg)

    @property
    def working_range_mm(self) -> tuple[float, float]:
        r"""``(bn, bn + 3)``: the working range of Figure J.8, in mm.

        The figure draws it as :math:`\Delta b` and its key names it
        :math:`\Delta b_\mathrm{n}` (recorded in the errata registry); the plot
        uses the symbol of the drawing. The 3 mm is the one J.4 c) measures
        at; where J.5.2 h) lets "a gap range other than 3 mm" apply,
        :meth:`at_gap` reads the single numbers at any other measured width.
        """
        return (self.nominal_gap_mm, self.nominal_gap_mm + _WORKING_RANGE_MM)

    def single_number(
        self, quantity: Literal["r_s_w", "r_s_w_c", "r_s_w_ctr"] = "r_s_w_ctr"
    ) -> np.ndarray:
        """The single number at each width: ``"r_s_w"``, ``"r_s_w_c"`` or ``"r_s_w_ctr"``."""
        require_choice(quantity, "quantity", _SINGLE_NUMBERS)
        return np.asarray(getattr(self, f"{quantity}_db"), dtype=np.float64)

    def at_gap(
        self,
        gap_mm: float,
        quantity: Literal["r_s_w", "r_s_w_c", "r_s_w_ctr"] = "r_s_w_ctr",
    ) -> float:
        """The single number at a gap width, on the lines through the measurements.

        Figure J.8 plots "measurement results (open circles) and
        interpolations (lines plotted through measurement results)"; this
        reads the straight line between the two widths either side.

        :param gap_mm: The gap width, in mm, within the measured range.
        :param quantity: ``"r_s_w"``, ``"r_s_w_c"`` or ``"r_s_w_ctr"`` (default).
        :return: The single number, in dB.
        :raises ValueError: If the width lies outside the measured widths.
        """
        values = self.single_number(quantity)
        widths = np.asarray(self.gap_widths_mm, dtype=np.float64)
        gap = require_non_negative(gap_mm, "gap_mm")
        if gap < widths[0] - _SLACK_DB or gap > widths[-1] + _SLACK_DB:
            msg = (
                f"'gap_mm' {gap:g} mm lies outside the measured widths "
                f"{widths[0]:g} mm to {widths[-1]:g} mm; a single number is "
                "never extrapolated."
            )
            raise ValueError(msg)
        return float(np.interp(gap, widths, values))

    def plot(
        self,
        ax: Axes | None = None,
        *,
        language: str = "en",
        quantity: Literal["r_s_w", "r_s_w_c", "r_s_w_ctr"] = "r_s_w_ctr",
        **kwargs: Any,
    ) -> Axes:
        r"""Plot a single number against the gap width, as Figure J.8.

        The measured widths as open circles on the line through them, with
        :math:`b_\mathrm{min}`, :math:`b_\mathrm{n}` and
        :math:`b_\mathrm{n} + 3` marked. Requires matplotlib
        (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.joint_insulation import plot_joint_gap_series

        check_language(language)
        require_choice(quantity, "quantity", _SINGLE_NUMBERS)
        return plot_joint_gap_series(
            self, ax=ax, language=language, quantity=quantity, **kwargs
        )

    def plot_octave_bands(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot :math:`R_\mathrm{s}` in octave bands at every gap width, as Figure J.9.

        Every result must hold whole octaves of one-third-octave bands.
        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.joint_insulation import plot_joint_gap_octaves

        check_language(language)
        return plot_joint_gap_octaves(self, ax=ax, language=language, **kwargs)


def joint_gap_series(
    gap_widths_mm: ArrayLike,
    results: tuple[LabJointInsulationResult, ...] | list[LabJointInsulationResult],
    *,
    nominal_gap_mm: float = _DEFAULT_NOMINAL_GAP_MM,
    minimum_gap_mm: float | None = None,
) -> JointGapSeries:
    r"""Collect the results of a variable slit at several gap widths (J.4, J.5).

    "For variable slits, as with openable windows or doors, the test shall be
    repeated" at the nominal gap width :math:`b_\mathrm{n}` given by the
    manufacturer ("if unknown :math:`b_\mathrm{n}` = 5 mm is to be taken"),
    at the minimal gap width :math:`b_\mathrm{min}` under the maximal
    pressure (normally a force of 100 N per metre of sealing) and at
    :math:`b_\mathrm{n} + 3` mm (J.4); NOTE 1 suggests steps of 1 mm from
    maximum compression until a gap is present. The report gives each of
    :math:`R_\mathrm{s,w}`, :math:`R_\mathrm{s,w} + C` and
    :math:`R_\mathrm{s,w} + C_\mathrm{tr}` as a function of the gap width with
    the nominal width marked (J.5.2 i)), and the results at
    :math:`b_\mathrm{n}` and :math:`b_\mathrm{n} + 3` are the ones products are
    compared by (J.5.2 h)). Any set of widths is collected;
    :func:`check_joint_gap_series` judges whether the three of J.4 are among
    them.

    :param gap_widths_mm: The gap width ``b`` of each result, in mm (the
        average of :func:`check_gap_width`).
    :param results: The :class:`LabJointInsulationResult` at each width, each
        with its ISO 717-1 rating.
    :param nominal_gap_mm: :math:`b_\mathrm{n}`, in mm (default 5 mm).
    :param minimum_gap_mm: :math:`b_\mathrm{min}`, in mm, marked on the plot
        when given.
    :return: A :class:`JointGapSeries`, sorted by gap width.
    :raises ValueError: If the widths and results disagree in number, two
        widths coincide, a width is negative, or a result carries no rating.
    """
    widths = require_finite_array(gap_widths_mm, "gap_widths_mm")
    if np.any(widths < 0.0):
        msg = "'gap_widths_mm' must be non-negative."
        raise ValueError(msg)
    items = tuple(results)
    if len(items) != widths.size:
        msg = (
            "joint_gap_series: 'gap_widths_mm' and 'results' must have the same "
            f"length, one result per width; got {widths.size} and {len(items)}."
        )
        raise ValueError(msg)
    order = np.argsort(widths, kind="stable")
    widths = widths[order]
    items = tuple(items[k] for k in order)
    if np.any(np.diff(widths) <= _SLACK_DB):
        msg = "'gap_widths_mm' must not repeat a width."
        raise ValueError(msg)
    numbers: list[tuple[int, int, int]] = []
    for result in items:
        if result.rating is None:
            msg = (
                "joint_gap_series: every result needs its ISO 717-1 rating, "
                "formed on the 16 bands 100 Hz to 3150 Hz."
            )
            raise ValueError(msg)
        rating = result.rating
        numbers.append(
            (rating.rating, rating.rating + rating.c, rating.rating + rating.ctr)
        )
    nominal = require_non_negative(nominal_gap_mm, "nominal_gap_mm")
    minimum = (
        None
        if minimum_gap_mm is None
        else require_non_negative(minimum_gap_mm, "minimum_gap_mm")
    )
    table = np.asarray(numbers, dtype=np.float64)
    return JointGapSeries(
        gap_widths_mm=widths,
        results=items,
        nominal_gap_mm=nominal,
        minimum_gap_mm=minimum,
        r_s_w_db=table[:, 0],
        r_s_w_c_db=table[:, 1],
        r_s_w_ctr_db=table[:, 2],
    )


@dataclass(frozen=True)
class JointGapSeriesCheck:
    r"""Whether a variable slit was measured at the three gap widths of J.4.

    The three widths J.4 asks for are read from the nominal and the minimal
    gap width, so the verdicts are not fields: a check cannot be built to pass
    a series that misses one.

    :ivar gap_widths_mm: The gap widths measured, ascending, in mm.
    :ivar nominal_gap_mm: The nominal gap width :math:`b_\mathrm{n}`, in mm.
    :ivar minimum_gap_mm: The minimal gap width :math:`b_\mathrm{min}`, in mm,
        or ``None`` when the series does not name it.
    """

    gap_widths_mm: tuple[float, ...]
    nominal_gap_mm: float
    minimum_gap_mm: float | None

    @property
    def nominal_measured(self) -> bool:
        r"""Whether a measured width is :math:`b_\mathrm{n}` (J.4 a))."""
        return _measured_at(self.gap_widths_mm, self.nominal_gap_mm)

    @property
    def minimum_measured(self) -> bool:
        r"""Whether a measured width is :math:`b_\mathrm{min}` (J.4 b)).

        ``False`` when the series names no :math:`b_\mathrm{min}`, since
        nothing then shows it was measured.
        """
        return self.minimum_gap_mm is not None and _measured_at(
            self.gap_widths_mm, self.minimum_gap_mm
        )

    @property
    def working_range_measured(self) -> bool:
        r"""Whether a measured width is :math:`b_\mathrm{n} + 3` mm (J.4 c))."""
        return _measured_at(self.gap_widths_mm, self.nominal_gap_mm + _WORKING_RANGE_MM)

    @property
    def passes(self) -> bool:
        """Whether all three were measured."""
        return (
            self.nominal_measured
            and self.minimum_measured
            and self.working_range_measured
        )

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a JointGapSeriesCheck has no truth value; read its '.passes'"
        raise TypeError(msg)

    @property
    def tolerance_mm(self) -> float:
        """How far a measured width may lie from a required one, in mm (0,3 mm, J.2.2)."""
        return _GAP_MATCH_MM

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the measured gap widths against the three widths J.4 asks for.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.joint_insulation import plot_joint_gap_series_check

        check_language(language)
        return plot_joint_gap_series_check(self, ax=ax, language=language, **kwargs)


def _measured_at(widths: tuple[float, ...], target: float) -> bool:
    """Whether one of *widths* lies within the 0,3 mm of J.2.2 of *target*."""
    return any(abs(width - target) <= _GAP_MATCH_MM + _SLACK_DB for width in widths)


def check_joint_gap_series(series: JointGapSeries) -> JointGapSeriesCheck:
    r"""Check that a variable slit was measured at the three gap widths of J.4.

    "For variable slits, as with openable windows or doors, the test shall be
    repeated for the following gap width": a) the nominal gap width
    :math:`b_\mathrm{n}`, b) the minimal gap width :math:`b_\mathrm{min}` at
    maximal pressure, and c) :math:`b_\mathrm{n} + 3`, "a gap width 3 mm more
    than nominal". Each has to be among the widths of the series.

    J.4 gives no tolerance on how close a measured width must come. The gap
    width of a result is the average of readings that J.2.2 lets spread over
    0,3 mm, so a measured width within 0,3 mm of a required one counts as
    that width. A series that does not name :math:`b_\mathrm{min}` fails
    J.4 b), because nothing then shows which width it was; pass
    ``minimum_gap_mm`` to :func:`joint_gap_series`.

    :param series: The :class:`JointGapSeries` of the slit.
    :return: A :class:`JointGapSeriesCheck`.
    """
    widths = np.asarray(series.gap_widths_mm, dtype=np.float64)
    return JointGapSeriesCheck(
        gap_widths_mm=tuple(float(w) for w in widths),
        nominal_gap_mm=float(series.nominal_gap_mm),
        minimum_gap_mm=series.minimum_gap_mm,
    )
