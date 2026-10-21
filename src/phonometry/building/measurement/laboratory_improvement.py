#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Improvement of sound insulation measured in the laboratory: a lining on a
basic element and a floor covering on a reference floor (ISO 10140-1:2021
Annexes G and H).

A lining and a floor covering are products that are never sold alone: each is
added to a wall or a floor, and what the laboratory measures is how much it
adds. ISO 10140-1 therefore measures the element twice, without and with the
product, and reports the difference band by band; the single number that
describes the product is then read on a *standard* element rather than on the
laboratory's own, so that two laboratories with different walls report the
same lining the same way.

**Linings, Annex G.** The sound reduction improvement index is
:math:`\Delta R = R_\mathrm{with} - R_\mathrm{without}` per one-third-octave
band (G.1). On one of the standard basic elements of ISO 10140-5:2021 Annex B
(the heavy wall of about 350 kg/m², the heavy concrete floor, the lightweight
wall of about 70 kg/m²), the single numbers are ``ΔRw``, ``Δ(Rw + C)`` and
``Δ(Rw + Ctr)`` of ISO 717-1:2020 Annex D, read on the element's reference curve
(G.5 c), :func:`~phonometry.building.weighted_reduction_improvement`). On any
other basic element they are the direct differences ``ΔRw,direct``,
``Δ(Rw + C)direct`` and ``Δ(Rw + Ctr)direct`` of Formula (D.2), which describe
the lining only on that element. G.4 adds one numeric condition, on the curing
of the basic element (:func:`check_lining_curing`).

**Floor coverings, Annex H.** The improvement of impact sound insulation is
:math:`\Delta L = L_\mathrm{n0} - L_\mathrm{n}` per band (Formula (H.1)), on the
heavyweight reference floor or on one of the three lightweight (timber)
reference floors of ISO 10140-5:2021 Annex C. The octave values follow from
Formula (H.2),
:math:`\Delta L_\mathrm{oct} = -10 \log_{10}[(1/3) \sum 10^{-\Delta L_j/10}]`,
and the single numbers ``ΔLw`` (heavyweight) or ``ΔLt,1,w``, ``ΔLt,2,w``,
``ΔLt,3,w`` (lightweight) with their adaptation terms from ISO 717-2:2020
Clauses 5 and 6 (:func:`~phonometry.building.weighted_impact_improvement`),
on the reference curves of its Table 4. H.6.1 adds the improvement for the
heavy/soft (rubber ball) source, :math:`\Delta L_\mathrm{r} =
L_\mathrm{i,Fmax,0} - L_\mathrm{i,Fmax}` (Formula (H.3)).

Citations are to ISO 10140-1:2021 (third edition) and, for the reference
curves, to ISO 717-1:2020 and ISO 717-2:2020, which since the 2021 edition of
ISO 10140-5 are where those curves are printed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from ..._internal.display import RichDisplay
from ..._internal.frozen import OwnsArrays
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
from .floor_covering_improvement import OctaveBandSpectrum, improvement_octave_bands
from .ratings import IMPACT_REFERENCE_FLOORS as _REFERENCE_FLOORS
from .ratings import LINING_REFERENCE_ELEMENTS as _BASIC_ELEMENTS
from .ratings import (
    ReductionImprovementRating,
    impact_improvement_adaptation_term,
    weighted_impact_improvement,
    weighted_impact_rating,
    weighted_rating,
    weighted_reduction_improvement,
)

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from numpy.typing import ArrayLike

    from ..._i18n import Language
    from ..._internal.types import ReportEngine
    from ..._report.metadata import ReportMetadata
    from .ratings import BasicElement, ImpactRatingResult, ReferenceFloor

__all__ = [
    "HeavyImpactImprovementResult",
    "LaboratoryFloorCoveringImprovementResult",
    "LaboratoryLiningImprovementResult",
    "LiningCuringCheck",
    "check_lining_curing",
    "heavy_impact_improvement",
    "laboratory_floor_covering_improvement",
    "laboratory_lining_improvement",
]

#: The 16 one-third-octave bands, 100 Hz to 3 150 Hz, on which ISO 717 rates a
#: single number, in Hz (the keys of every reference floor).
_RATING_BANDS_HZ: tuple[float, ...] = tuple(_REFERENCE_FLOORS["heavyweight"])

#: The designation of the weighted reduction on each reference floor
#: (ISO 10140-1:2021 H.1, ISO 717-2:2020 6.2).
_FLOOR_DESIGNATIONS = {
    "heavyweight": "ΔLw",
    "lightweight_1": "ΔLt,1,w",
    "lightweight_2": "ΔLt,2,w",
    "lightweight_3": "ΔLt,3,w",
}

#: Curing period of a masonry or concrete basic element "not less than two
#: weeks, if not specified otherwise in the product specifications"
#: (ISO 10140-1:2021 G.4), in days.
_CURING_DAYS = 14.0

#: The alternative of G.4: the time lag between the two measurements "shall not
#: exceed one-third of the curing time elapsed before the first measurement",
#: held as the factor the lag is multiplied by to reach that curing time.
_LAG_FACTOR = 3.0

#: Relative slack on the two inclusive bounds of G.4 ("not less than two
#: weeks", "shall not exceed one-third"). A lag of 2,1 d after 6,3 d of curing
#: is exactly one third, but 3 x 2,1 is 6,300000000000001 in binary floating
#: point. Nine orders of magnitude below the curing time is far above that
#: arithmetic and far below a second of any day count.
_BOUND_SLACK = 1e-9


def _band_indices(
    frequencies: np.ndarray, targets: tuple[float, ...]
) -> np.ndarray | None:
    """Indices of ``targets`` in ``frequencies`` (6 % match), or ``None``.

    The 6 % window is the one the ISO 717 rating code matches nominal band
    centres with: wide enough for an exact midband frequency, narrower than
    the 26 % between neighbouring one-third-octave bands.
    """
    indices: list[int] = []
    for target in targets:
        hits = np.nonzero(np.abs(frequencies - target) <= 0.06 * target)[0]
        if hits.size != 1:
            return None
        indices.append(int(hits[0]))
    return np.asarray(indices, dtype=np.intp)


def _paired_spectra(
    owner: str,
    frequencies: ArrayLike,
    first: tuple[str, ArrayLike],
    second: tuple[str, ArrayLike],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Validate a band axis and the two spectra measured on it."""
    freqs = require_positive_array(frequencies, "frequencies")
    a = require_finite_array(first[1], first[0])
    b = require_finite_array(second[1], second[0])
    require_equal_shapes(
        owner,
        {"frequencies": freqs.shape, first[0]: a.shape, second[0]: b.shape},
        "band",
    )
    return freqs, a, b


# --- Annex G: linings -------------------------------------------------------


@dataclass(frozen=True)
class LaboratoryLiningImprovementResult(OwnsArrays):
    r"""Improvement of airborne sound insulation by a lining (ISO 10140-1 Annex G).

    :ivar frequencies: One-third-octave band centre frequencies, in Hz.
    :ivar r_without: Sound reduction index of the basic element without the
        lining, ``Rwithout``, in dB.
    :ivar r_with: Sound reduction index with the lining, ``Rwith``, in dB.
    :ivar delta_r: Sound reduction improvement index
        :math:`\Delta R = R_\mathrm{with} - R_\mathrm{without}`, in dB (G.1).
    :ivar basic_element: The standard basic element the lining was measured
        on (``"heavy_wall"``, ``"heavy_floor"``, ``"lightweight_wall"``), or
        ``None`` for another basic element.
    :ivar rating: The ISO 717-1:2020 Annex D rating on the reference curve of
        that element, or ``None`` for another basic element or a spectrum
        without the 16 rating bands 100 Hz to 3 150 Hz.
    :ivar delta_rw_direct: ``ΔRw,direct = Rw,with - Rw,without``
        (ISO 717-1:2020 Formula (D.2)), in dB, or ``None`` without the 16
        rating bands.
    :ivar delta_rw_c_direct: ``Δ(Rw + C)direct``, in dB, or ``None``.
    :ivar delta_rw_ctr_direct: ``Δ(Rw + Ctr)direct``, in dB, or ``None``.
    """

    frequencies: np.ndarray
    r_without: np.ndarray
    r_with: np.ndarray
    delta_r: np.ndarray
    basic_element: Literal["heavy_wall", "heavy_floor", "lightweight_wall"] | None
    rating: ReductionImprovementRating | None
    delta_rw_direct: int | None
    delta_rw_c_direct: int | None
    delta_rw_ctr_direct: int | None

    def __post_init__(self) -> None:
        """Reject spectra of different lengths and an unknown basic element.

        The figure draws ``delta_r`` against ``frequencies`` and the
        octave conversion regroups the same pair, so a column of another
        length would be matched to the wrong bands. The element name is
        looked up to title the figure with its ISO 717-1 index.

        :raises ValueError: if the per-band columns disagree, or
            ``basic_element`` is neither a standard element nor ``None``.
        :raises TypeError: if ``basic_element`` is not a text.
        """
        require_ranks(self, frequencies=1, r_without=1, r_with=1, delta_r=1)
        require_same_length(self, "frequencies", "r_without", "r_with", "delta_r")
        if self.basic_element is not None:
            require_choice(self.basic_element, "basic_element", tuple(_BASIC_ELEMENTS))

    def octave_bands(self) -> OctaveBandSpectrum:
        r""":math:`\Delta R_\mathrm{oct}` in octave bands (ISO 717-1:2020 Formula (D.1)).

        :math:`\Delta R_\mathrm{oct} = -10 \log_{10}[(1/3) \sum 10^{-\Delta R_j/10}]`
        over the three one-third-octave bands of each octave, for every octave
        whose three bands are present.
        """
        return improvement_octave_bands(
            self.delta_r, frequencies=self.frequencies, quantity="ΔR"
        )

    def plot(
        self, ax: Axes | None = None, *, language: Language = "en", **kwargs: Any
    ) -> Axes:
        """Plot the improvement ``ΔR`` per band with its single numbers.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_lab_lining_improvement

        check_language(language)
        return plot_lab_lining_improvement(self, ax=ax, language=language, **kwargs)


def laboratory_lining_improvement(
    r_without: ArrayLike,
    r_with: ArrayLike,
    *,
    frequencies: ArrayLike,
    basic_element: BasicElement | None = "heavy_wall",
) -> LaboratoryLiningImprovementResult:
    r"""Improvement of airborne sound insulation by a lining (ISO 10140-1:2021 G).

    The basic element is measured to ISO 10140-2 without and then with the
    lining, and the improvement is
    :math:`\Delta R = R_\mathrm{with} - R_\mathrm{without}` in each
    one-third-octave band (G.1). What it says about the lining depends on the
    element it was measured on (G.2):

    * on a standard basic element of ISO 10140-5:2021 Annex B the single
      numbers ``ΔRw``, ``Δ(Rw + C)`` and ``Δ(Rw + Ctr)`` are read on that
      element's reference curve, which generalises them beyond the
      laboratory (ISO 717-1:2020 Annex D; G.5 c));
    * on any other element (``basic_element=None``) only the direct
      differences of the measured single numbers are defined,
      ``ΔRw,direct = Rw,with - Rw,without`` (ISO 717-1:2020 Formula (D.2)),
      which "include the particular features of the laboratory and the basic
      element" (G.2 c)).

    The direct differences are returned in both cases, since they need only
    the two measured curves. The single numbers need the 16 rating bands
    100 Hz to 3 150 Hz; a spectrum without them keeps its per-band ``ΔR`` and
    reports no rating.

    NOTE 2 of G.1 leaves linings on flexible lightweight structures (timber
    frame floors, double-leaf gypsum board walls) outside the annex, and
    NOTE 1 limits the result to direct airborne transmission; neither can be
    read off the numbers, so neither is refused here.

    :param r_without: ``Rwithout`` per one-third-octave band, in dB
        (e.g. ``laboratory_airborne_insulation(...).r``).
    :param r_with: ``Rwith`` per band, in dB.
    :param frequencies: Band centre frequencies, in Hz.
    :param basic_element: ``"heavy_wall"`` (default), ``"heavy_floor"``,
        ``"lightweight_wall"`` or ``None`` for a basic element that is not one
        of the three standard ones.
    :return: A :class:`LaboratoryLiningImprovementResult`.
    :raises ValueError: If the three inputs disagree in length, a value is not
        finite, a frequency is not positive, or ``basic_element`` is unknown.
    :raises TypeError: if ``basic_element`` is not a text, or ``frequencies`` holds a
        text or a value that is not a real number.
    """
    freqs, without, with_ = _paired_spectra(
        "laboratory_lining_improvement",
        frequencies,
        ("r_without", r_without),
        ("r_with", r_with),
    )
    if basic_element is not None:
        require_choice(basic_element, "basic_element", tuple(_BASIC_ELEMENTS))
    delta = with_ - without
    core = _band_indices(freqs, _RATING_BANDS_HZ)
    rating: ReductionImprovementRating | None = None
    direct: tuple[int | None, int | None, int | None] = (None, None, None)
    if core is not None:
        rated_without = weighted_rating(without[core])
        rated_with = weighted_rating(with_[core])
        direct = (
            rated_with.rating - rated_without.rating,
            (rated_with.rating + rated_with.c)
            - (rated_without.rating + rated_without.c),
            (rated_with.rating + rated_with.ctr)
            - (rated_without.rating + rated_without.ctr),
        )
        if basic_element is not None:
            # Annex D rates the bands its reference curve prints (50 Hz to
            # 5000 Hz); a band beyond them has no Rref,without to add ΔR to.
            table = np.asarray(tuple(_BASIC_ELEMENTS[basic_element]), dtype=float)
            inside = np.array(
                [bool(np.any(np.abs(table - f) <= 0.06 * f)) for f in freqs]
            )
            rating = weighted_reduction_improvement(
                delta[inside], frequencies=freqs[inside], basic_element=basic_element
            )
    return LaboratoryLiningImprovementResult(
        frequencies=freqs,
        r_without=without,
        r_with=with_,
        delta_r=delta,
        basic_element=basic_element,
        rating=rating,
        delta_rw_direct=direct[0],
        delta_rw_c_direct=direct[1],
        delta_rw_ctr_direct=direct[2],
    )


@dataclass(frozen=True)
class LiningCuringCheck(RichDisplay):
    """Whether the basic element was stable across the two measurements (G.4).

    The verdicts are read from the three times and the third G.4 prints, so
    they are not fields: a check cannot be built to pass times the clause
    fails.

    :ivar curing_time_days: Time from the end of construction of the basic
        element to the first sound reduction measurement, in days.
    :ivar time_lag_days: Time between the measurement without and the
        measurement with the lining, in days.
    :ivar required_curing_days: The curing period that settles the element,
        14 days unless the product specification sets another.
    """

    curing_time_days: float
    time_lag_days: float
    required_curing_days: float

    @property
    def cured(self) -> bool:
        """Whether the curing time reaches ``required_curing_days``.

        Inclusive, and compared with a relative slack so that a time on the
        bound is not failed by the binary rounding of the product.
        """
        return self.curing_time_days >= self.required_curing_days * (1.0 - _BOUND_SLACK)

    @property
    def lag_within_third(self) -> bool:
        """Whether the time lag is at most a third of the curing time, the alternative G.4 allows.

        Inclusive, with the same slack: the printed 1 d and 3 d, or 2,1 d and
        6,3 d, are on the bound.
        """
        return self.time_lag_days * _LAG_FACTOR <= self.curing_time_days * (
            1.0 + _BOUND_SLACK
        )

    @property
    def passes(self) -> bool:
        """Whether either condition holds."""
        return self.cured or self.lag_within_third

    @property
    def earliest_start_days(self) -> float:
        """The curing time at which the lag condition is first met, in days.

        Three times the time lag: the G.4 example reads it the other way
        round, two measurements carried out within 1 d "can be started not
        less than 3 d after the end of construction".
        """
        return self.time_lag_days * _LAG_FACTOR

    def __bool__(self) -> bool:
        """Refuse to stand in for the verdict it carries.

        :raises TypeError: Always; the verdict is :attr:`passes`.
        """
        msg = "a LiningCuringCheck has no truth value; read its '.passes'"
        raise TypeError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: Language = "en", **kwargs: Any
    ) -> Axes:
        """Plot the admissible curing time and time lag with this measurement.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_lining_curing_check

        check_language(language)
        return plot_lining_curing_check(self, ax=ax, language=language, **kwargs)


def check_lining_curing(
    curing_time_days: float,
    time_lag_days: float,
    *,
    required_curing_days: float = _CURING_DAYS,
) -> LiningCuringCheck:
    """Is the basic element settled enough for the two measurements (G.4)?

    ``ΔR`` is the difference of two measurements of the same element, so the
    element must not change between them: "it shall either be at its final
    condition or the two measurements shall be carried out within a
    sufficiently short time interval". For masonry and concrete G.4 puts
    numbers on both ways out, and either one suffices:

    * a curing period of not less than two weeks (``required_curing_days``,
      unless the product specification sets another); or
    * a time lag between the two measurements of at most one third of the
      curing time elapsed before the first one. G.4's example: measurements
      carried out within 1 d can start 3 d after the end of construction.

    G.4 also asks the lining and its fixing to have reached their final
    condition before the second measurement, which has no number and is not
    judged here.

    :param curing_time_days: Days from the end of construction of the basic
        element to the first measurement.
    :param time_lag_days: Days between the two measurements (zero or more).
    :param required_curing_days: The curing period that settles the element
        without further condition, in days (default 14).
    :return: A :class:`LiningCuringCheck`.
    :raises ValueError: If a time is negative or not finite, or the required
        curing period is not positive.
    :raises TypeError: if ``curing_time_days``, ``required_curing_days`` or
        ``time_lag_days`` is not a single number.
    """
    curing = require_non_negative(curing_time_days, "curing_time_days")
    lag = require_non_negative(time_lag_days, "time_lag_days")
    required = require_positive(required_curing_days, "required_curing_days")
    return LiningCuringCheck(
        curing_time_days=curing,
        time_lag_days=lag,
        required_curing_days=required,
    )


# --- Annex H: floor coverings -----------------------------------------------


@dataclass(frozen=True)
class LaboratoryFloorCoveringImprovementResult(OwnsArrays):
    r"""Improvement of impact sound insulation by a floor covering (Annex H).

    :ivar frequencies: One-third-octave band centre frequencies, in Hz.
    :ivar l_n0: Normalized impact sound pressure level of the reference
        floor without the covering, ``Ln0``, in dB.
    :ivar l_n: Normalized impact sound pressure level with the covering,
        ``Ln``, in dB.
    :ivar improvement: :math:`\Delta L = L_\mathrm{n0} - L_\mathrm{n}`
        per band, in dB (Formula (H.1)).
    :ivar reference_floor: ``"heavyweight"``, ``"lightweight_1"``,
        ``"lightweight_2"`` or ``"lightweight_3"``.
    :ivar delta_lw: The weighted reduction on the reference curve of that
        floor (``ΔLw`` or ``ΔLt,n,w``, ISO 717-2:2020 Clauses 5 and 6), in
        dB, or ``None`` without the 16 rating bands 100 Hz to 3 150 Hz.
    :ivar ci_delta: Its spectrum adaptation term, ``CI,Δ`` on the
        heavyweight floor (Formula (A.4)) or ``CIΔ,t`` on a lightweight one
        (Formula (A.6)), designated ``CIΔ,t1`` to ``CIΔ,t3`` by floor type
        (ISO 717-2:2020 A.2.3), in dB, or ``None``.
    :ivar reference_rating: The ISO 717-2 rating of the reference curve with
        the covering, :math:`L_\mathrm{n,r} = L_\mathrm{n,r,0} - \Delta L`:
        ``Ln,r,w`` and ``CI,r`` of H.5 i), or ``None``.
    :ivar bare_rating: The ISO 717-2 rating of the measured bare floor,
        ``Ln,0,w`` and ``CI,0`` of H.5 i), or ``None``.
    """

    frequencies: np.ndarray
    l_n0: np.ndarray
    l_n: np.ndarray
    improvement: np.ndarray
    reference_floor: Literal[
        "heavyweight", "lightweight_1", "lightweight_2", "lightweight_3"
    ]
    delta_lw: int | None
    ci_delta: int | None
    reference_rating: ImpactRatingResult | None
    bare_rating: ImpactRatingResult | None

    def __post_init__(self) -> None:
        """Reject spectra of different lengths and an unknown reference floor.

        The figure and the octave conversion read ``improvement`` against
        ``frequencies`` band by band, and the designation of the rating is
        looked up from the floor name.

        :raises ValueError: if the per-band columns disagree, or the floor is
            not one of the four reference floors.
        :raises TypeError: if ``reference_floor`` is not a text.
        """
        require_ranks(self, frequencies=1, l_n0=1, l_n=1, improvement=1)
        require_same_length(self, "frequencies", "l_n0", "l_n", "improvement")
        require_choice(
            self.reference_floor, "reference_floor", tuple(_REFERENCE_FLOORS)
        )

    @property
    def designation(self) -> str:
        """``"ΔLw"`` on the heavyweight floor, ``"ΔLt,n,w"`` on floor No n (H.1)."""
        return _FLOOR_DESIGNATIONS[self.reference_floor]

    def octave_bands(self) -> OctaveBandSpectrum:
        r""":math:`\Delta L_\mathrm{oct}` in octave bands, by Formula (H.2).

        :math:`\Delta L_\mathrm{oct} = -10 \log_{10}[(1/3) \sum 10^{-\Delta L_j/10}]`
        over the three one-third-octave bands of each octave present.
        """
        return improvement_octave_bands(self.improvement, frequencies=self.frequencies)

    def plot(
        self,
        ax: Axes | None = None,
        *,
        language: Language = "en",
        rating_range: bool = False,
        **kwargs: Any,
    ) -> Axes:
        """Plot the improvement ``ΔL`` per band with its weighted reduction.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param rating_range: Mark the frequency range of the ISO 717-2 rating,
            100 Hz to 3 150 Hz, with two dashed lines, as the diagram of the
            form of Figure H.4 does (its key 1).
        :param kwargs: Forwarded to the ``ΔL`` curve.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_lab_floor_covering_improvement

        check_language(language)
        return plot_lab_floor_covering_improvement(
            self, ax=ax, language=language, rating_range=rating_range, **kwargs
        )

    def report(
        self,
        path: str,
        *,
        metadata: ReportMetadata | None = None,
        engine: ReportEngine = "reportlab",
        verbose: bool = False,
        language: Language = "en",
    ) -> str:
        r"""Render the form of ISO 10140-1:2021 Figure H.4 to a one-page PDF.

        "An example of the form for the expression of results ... is given in
        Figure H.4. The user is allowed to copy this form" (H.6.3). The sheet
        carries its fields: manufacturer and product, client, test room,
        who mounted the specimen, the date, the description of the facility
        and specimen, the type of reference floor, the mass per unit area,
        the curing time, the air temperature and humidity in the source room
        and the receiving room volume; the one-third-octave table of
        :math:`L_\mathrm{n,0}` and :math:`\Delta L` beside the :math:`\Delta L`
        diagram with the frequency range of the ISO 717-2 rating marked; the
        rating :math:`\Delta L_\mathrm{w}` (or :math:`\Delta L_\mathrm{t,n,w}`)
        and :math:`C_{\mathrm{I}\Delta}` with the two floor ratings of
        H.5 i); and the statement that the result comes from an artificial
        source on a specified reference floor. The form also asks for
        :math:`C_\mathrm{I,r,50\text{-}2500}`, which the reference floors of
        ISO 717-2:2020 Table 4 cannot give below 100 Hz; the sheet says so in
        its place.

        :param path: Destination path of the PDF file.
        :param metadata: Optional :class:`~phonometry.ReportMetadata`; its
            ``product`` and ``curing_time_hours`` fill the product identification
            and curing time rows, ``source_temperature_c`` and
            ``source_relative_humidity_percent`` (or the single
            ``temperature_c`` and ``relative_humidity_percent``) the climate
            of the source room, and ``requirement`` a verdict on the weighted
            reduction (passing at or above it).
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: When ``True``, the table also shows
            :math:`L_\mathrm{n}` with the covering.
        :param language: ``"en"`` (default) or ``"es"``.
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` or ``language`` is unknown, or the
            result carries no weighted reduction (the 16 bands 100 Hz to
            3 150 Hz are missing).
        :raises ImportError: If reportlab or matplotlib is not installed.
        """
        from ..._i18n import check_language
        from ..._report.iso10140_1 import render_floor_covering_form

        check_engine(engine)
        check_language(language)
        if self.delta_lw is None or self.ci_delta is None:
            msg = (
                "The Figure H.4 form needs the weighted reduction, formed on the "
                "16 one-third-octave bands 100 Hz to 3150 Hz; this result has none."
            )
            raise ValueError(msg)
        return render_floor_covering_form(
            self, path, metadata=metadata, verbose=verbose, language=language
        )


def laboratory_floor_covering_improvement(
    l_n0: ArrayLike,
    l_n: ArrayLike,
    *,
    frequencies: ArrayLike,
    reference_floor: ReferenceFloor = "heavyweight",
) -> LaboratoryFloorCoveringImprovementResult:
    r"""Improvement of impact sound insulation by a floor covering (ISO 10140-1 H).

    The reference floor is measured to ISO 10140-3 with the tapping machine,
    without and then with the covering at the same positions, and the
    improvement is :math:`\Delta L = L_\mathrm{n0} - L_\mathrm{n}` in each
    one-third-octave band (Formula (H.1)). The weighted reduction is read on
    the reference curve of the floor it was measured on, ISO 717-2:2020
    Table 4: ``ΔLw`` on the heavyweight concrete floor (Clause 5) and
    ``ΔLt,1,w``, ``ΔLt,2,w`` or ``ΔLt,3,w`` on the lightweight floors of type
    No 1, 2 and 3 (Clause 6), each with its adaptation term (Formulas (A.4)
    and (A.6)). The result also carries the two ratings H.5 i) asks the report
    to state beside them: the reference floor with the covering (``Ln,r,w``,
    ``CI,r``) and the measured bare floor (``Ln,0,w``, ``CI,0``).

    ISO 717-2:2020 5.4 confines a ``ΔLw`` measured on the concrete slab to
    "similar types of massive floors"; a covering meant for a timber floor is
    measured on a lightweight reference floor. The wooden mock-up of
    ISO 10140-5:2021 Annex G is the alternative for a laboratory that cannot
    build one (H.6.2): Annex H names no reference curve for it, so its ``ΔL``
    describes the covering on a similar board and the rating it is given here
    is the one of the ``reference_floor`` the caller names.

    :param l_n0: ``Ln0`` per one-third-octave band, in dB: the
        energy-averaged normalized level of the bare floor (e.g.
        ``laboratory_impact_insulation(...).l_n``). For small category I specimens
        measured with the tapping machine beside each specimen, it is the
        arithmetic mean of the two positions either side (H.4.6.1.1).
    :param l_n: ``Ln`` with the covering, per band, in dB.
    :param frequencies: Band centre frequencies, in Hz; the ratings are
        formed on the 16 bands 100 Hz to 3 150 Hz when all are present.
    :param reference_floor: ``"heavyweight"`` (default), ``"lightweight_1"``,
        ``"lightweight_2"`` or ``"lightweight_3"``.
    :return: A :class:`LaboratoryFloorCoveringImprovementResult`.
    :raises ValueError: If the three inputs disagree in length, a value is not
        finite, a frequency is not positive, or ``reference_floor`` is not one
        of the four floors.
    :raises TypeError: if ``reference_floor`` is not a text, or ``frequencies`` holds a
        text or a value that is not a real number.
    """
    freqs, bare, covered = _paired_spectra(
        "laboratory_floor_covering_improvement",
        frequencies,
        ("l_n0", l_n0),
        ("l_n", l_n),
    )
    require_choice(reference_floor, "reference_floor", tuple(_REFERENCE_FLOORS))
    improvement = bare - covered  # Formula (H.1)
    core = _band_indices(freqs, _RATING_BANDS_HZ)
    delta_lw: int | None = None
    ci_delta: int | None = None
    reference_rating: ImpactRatingResult | None = None
    bare_rating: ImpactRatingResult | None = None
    if core is not None:
        rated = improvement[core]
        delta_lw = weighted_impact_improvement(rated, reference_floor=reference_floor)
        ci_delta = impact_improvement_adaptation_term(
            rated, reference_floor=reference_floor
        )
        curve = np.fromiter(_REFERENCE_FLOORS[reference_floor].values(), dtype=float)
        reference_rating = weighted_impact_rating(curve - rated)
        bare_rating = weighted_impact_rating(bare[core])
    return LaboratoryFloorCoveringImprovementResult(
        frequencies=freqs,
        l_n0=bare,
        l_n=covered,
        improvement=improvement,
        reference_floor=reference_floor,
        delta_lw=delta_lw,
        ci_delta=ci_delta,
        reference_rating=reference_rating,
        bare_rating=bare_rating,
    )


@dataclass(frozen=True)
class HeavyImpactImprovementResult(OwnsArrays):
    r"""Improvement for the heavy/soft impact source (ISO 10140-1:2021 H.6.1).

    :ivar frequencies: Band centre frequencies, in Hz.
    :ivar l_i_fmax_0: Maximum impact sound pressure level of the reference
        floor without the covering, ``Li,Fmax,0``, in dB.
    :ivar l_i_fmax: The same with the covering, ``Li,Fmax``, in dB.
    :ivar improvement: :math:`\Delta L_\mathrm{r} = L_\mathrm{i,Fmax,0} -
        L_\mathrm{i,Fmax}` per band, in dB (Formula (H.3)).
    """

    frequencies: np.ndarray
    l_i_fmax_0: np.ndarray
    l_i_fmax: np.ndarray
    improvement: np.ndarray

    def __post_init__(self) -> None:
        """Reject columns of different lengths.

        :raises ValueError: if the per-band columns disagree.
        """
        require_ranks(
            self,
            frequencies=1,
            l_i_fmax_0=1,
            l_i_fmax=1,
            improvement=1,
        )
        require_same_length(
            self, "frequencies", "l_i_fmax_0", "l_i_fmax", "improvement"
        )

    def plot(
        self, ax: Axes | None = None, *, language: Language = "en", **kwargs: Any
    ) -> Axes:
        """Plot the improvement ``ΔLr`` per band.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_heavy_impact_improvement

        check_language(language)
        return plot_heavy_impact_improvement(self, ax=ax, language=language, **kwargs)


def heavy_impact_improvement(
    l_i_fmax_0: ArrayLike, l_i_fmax: ArrayLike, *, frequencies: ArrayLike
) -> HeavyImpactImprovementResult:
    r"""Improvement of a floor covering under the rubber ball (H.6.1).

    The floor covering is laid on a reference floor of ISO 10140-5:2021
    Annex C and the maximum impact sound pressure level ``Li,Fmax`` of the
    heavy/soft impact source (ISO 10140-3:2021 Annex A, the rubber ball of
    ISO 10140-5:2021 Annex F) is measured without and with it; the improvement
    is :math:`\Delta L_\mathrm{r} = L_\mathrm{i,Fmax,0} - L_\mathrm{i,Fmax}`
    in each band (Formula (H.3)). The source is characterised in octave
    bands from 31,5 Hz to 500 Hz, and the levels are usually taken in the
    octaves 63 Hz to 500 Hz or the matching one-third octaves
    (:func:`~phonometry.building.heavy_impact_octave_levels`).

    :param l_i_fmax_0: ``Li,Fmax,0`` per band, in dB.
    :param l_i_fmax: ``Li,Fmax`` per band, in dB.
    :param frequencies: Band centre frequencies, in Hz.
    :return: A :class:`HeavyImpactImprovementResult`.
    :raises ValueError: If the inputs disagree in length, a value is not finite
        or a frequency is not positive.
    :raises TypeError: if ``frequencies`` holds a text or a value that is not a real
        number.
    """
    freqs, bare, covered = _paired_spectra(
        "heavy_impact_improvement",
        frequencies,
        ("l_i_fmax_0", l_i_fmax_0),
        ("l_i_fmax", l_i_fmax),
    )
    return HeavyImpactImprovementResult(
        frequencies=freqs,
        l_i_fmax_0=bare,
        l_i_fmax=covered,
        improvement=bare - covered,
    )
