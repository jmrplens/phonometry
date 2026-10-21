#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Impact-sound improvement of floor coverings on a small mock-up
(ISO 16251-1:2014).

Laboratory method for the **improvement of impact sound insulation** ``ΔL`` of a
soft, locally-reacting floor covering (carpet, PVC, linoleum; ISO 10140-1
Annex H category I) laid on a small concrete mock-up plate and excited by a
standard tapping machine. The two rooms of the ISO 10140 series are removed and
the floor is replaced by a softly-supported concrete plate; instead of the
receiving-room sound pressure level, the **structure-borne acceleration level**
on the underside of the plate is measured with and without the covering. For
locally-reacting coverings this acceleration-level difference equals the ISO
10140 impact sound reduction (Clause 4).

**Acceleration level (Formula (1)).**
:math:`L_a = 10 \log_{10}[(1/T_m) \int a(t)^2/a_0^2\,dt]` dB,
with the reference acceleration :math:`a_0 = 10^{-6}` m/s², i.e.
:math:`L_a = 10 \log_{10}(\overline{a^2}/a_0^2)`.

**Background correction (Formula (2)).** Each measured level ``L'`` is
corrected against the background ``Lb`` per accelerometer position, by the
margin :math:`L' - L_\mathrm{b}`: unchanged for :math:`\ge 15` dB; energy
subtraction :math:`10 \log_{10}(10^{L'/10} - 10^{L_\mathrm{b}/10})` for
:math:`6 \le \mathrm{margin} < 15` dB; and the fixed :math:`L' - 1.3` dB limit
for :math:`< 6` dB. Bands hitting the 1.3 dB limit are flagged as the *limit of
measurement* (reported as :math:`> \Delta L`). This differs from the ISO
10140-4 correction (:func:`phonometry.building.background_correction`) only at
exactly :math:`\mathrm{margin} = 6` dB.

**Improvement (Formulae (3)/(4)).** The per-position difference is
:math:`\Delta L_{t,a} = L_{0,t,a} - L_{1,t,a}` (0 = bare plate, 1 = specimen)
and the improvement is
their arithmetic mean over all tapping-machine (t) and accelerometer (a)
positions, :math:`\Delta L = (1/(t \cdot a)) \sum_t \sum_a \Delta L_{t,a}`.

**Octave bands (Formula (5)).**
:math:`\Delta L_\mathrm{oct} = -10 \log_{10}[(1/3) \sum 10^{-\Delta L_j/10}]` dB from
the three one-third-octave values in each octave.

**Weighted improvement.** ``ΔLw`` is the ISO 717-2 weighted reduction of impact
sound pressure level (Clause 6.5), computed with the heavyweight reference
floor via :func:`phonometry.building.weighted_impact_improvement` on the 16
rating bands 100 Hz to 3150 Hz; a wider clause 6.3 spectrum (18 bands 100-5000
Hz, optionally extended to 50 Hz) is rated on that sub-range. The statement of
results (Clause 8 e)) also carries the spectrum adaptation term ``CI,Δ`` (ISO
717-2:2020 Formula (A.4)) via
:func:`phonometry.building.impact_improvement_adaptation_term`.
"""

from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np

from ..._internal.boundary import settled
from ..._internal.frozen import OwnsArrays, read_only
from ..._internal.validation import (
    check_engine,
    require_choice,
    require_equal_shapes,
    require_ranks,
    require_same_length,
    require_scalar,
)
from ...metrology.reference_values import ISO1683_REFERENCE_VALUES
from .ratings import impact_improvement_adaptation_term, weighted_impact_improvement

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from matplotlib.axes import Axes
    from numpy.typing import NDArray

    from ..._report.metadata import ReportMetadata

__all__ = [
    "BackgroundCorrectedLevel",
    "FloorCoveringImprovementResult",
    "OctaveBandSpectrum",
    "acceleration_level",
    "background_corrected_level",
    "impact_improvement",
    "improvement_octave_bands",
]

#: Reference acceleration ``a0`` for the acceleration level (Formula (1)): 1e-6 m/s²,
#: the ISO 1683:2015 Table 3 value.
_ACCELERATION_REFERENCE = ISO1683_REFERENCE_VALUES["solid"]["acceleration"].value

#: Background-correction thresholds (Formula (2)), in dB.
_MARGIN_NEGLIGIBLE = 15.0
_MARGIN_LIMIT = 6.0
_LIMIT_CORRECTION = 1.3

#: The 16 one-third-octave centre frequencies rated by ISO 717-2 (100-3150 Hz).
_RATING_FREQS = (
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
)


def _finite(values: float | Sequence[float] | np.ndarray, name: str) -> np.ndarray:
    a = np.atleast_1d(np.asarray(values, dtype=np.float64))
    if not np.all(np.isfinite(a)):
        msg = f"'{name}' must contain only finite values."
        raise ValueError(msg)
    return a


def acceleration_level(
    acceleration: float | Sequence[float] | np.ndarray,
    *,
    reference: float = _ACCELERATION_REFERENCE,
) -> np.ndarray:
    r"""Vibratory acceleration level ``La`` (ISO 16251-1 Formula (1)).

    :math:`L_a = 10 \log_{10}(a_\mathrm{rms}^2 / a_0^2) = 20 \log_{10}(a_\mathrm{rms} / a_0)` dB.

    :param acceleration: RMS acceleration ``a_rms`` per band, in m/s² (> 0).
    :param reference: Reference acceleration ``a0``, in m/s² (default 1e-6).
    :return: The acceleration level ``La`` per band, in dB.
    :raises ValueError: Non-finite or non-positive acceleration, or a
        non-positive reference.
    :raises TypeError: if ``reference`` is not a single number.
    """
    require_scalar(reference, "reference")
    a = _finite(acceleration, "acceleration")
    if np.any(a <= 0.0):
        msg = "'acceleration' must be positive."
        raise ValueError(msg)
    if reference <= 0.0:
        msg = "'reference' must be positive."
        raise ValueError(msg)
    return 20.0 * np.log10(a / reference)


@dataclass(frozen=True)
class BackgroundCorrectedLevel(OwnsArrays):
    r"""A measured level corrected for background noise (ISO 16251-1 F. (2)).

    At a margin :math:`L' - L_\mathrm{b}` of 15 dB or more the level is used
    unchanged; between 6 dB and 15 dB the background is subtracted in energy;
    under 6 dB the correction is held at 1,3 dB, the limit of measurement,
    and the band is reported as :math:`> \Delta L`. The margins, the corrected
    levels and the bands at the limit are read from the two readings, so they
    are not fields: a record cannot be built to claim a band clear of the
    limit that its readings put on it.

    :ivar signal_and_background: Measured level ``L'`` (with background), in
        dB; one value per band, or a (positions, bands) array.
    :ivar background: Background-noise level ``Lb``, in dB, of the same shape.
    :ivar frequencies: The band centre frequencies, in Hz, one per band (the
        last axis of the readings), or ``None`` where the bands were not
        named; only the plot reads them.
    """

    signal_and_background: NDArray[np.float64]
    background: NDArray[np.float64]
    _: KW_ONLY
    frequencies: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        """Hold the readings read-only and reject readings that do not pair.

        :raises ValueError: For readings of different shapes, values that are
            not finite, or band frequencies that are not one positive value per
            band.
        """
        lp = _finite(self.signal_and_background, "signal_and_background")
        lb = _finite(self.background, "background")
        require_equal_shapes(
            type(self).__name__,
            {"signal_and_background": lp.shape, "background": lb.shape},
            "band",
        )
        object.__setattr__(self, "signal_and_background", read_only(lp))
        object.__setattr__(self, "background", read_only(lb))
        if self.frequencies is not None:
            freqs = _finite(self.frequencies, "frequencies")
            if freqs.ndim != 1 or freqs.size != lp.shape[-1] or np.any(freqs <= 0.0):
                msg = (
                    f"'frequencies' must be one positive centre frequency per "
                    f"band, {lp.shape[-1]} of them; got shape {freqs.shape}."
                )
                raise ValueError(msg)
            object.__setattr__(self, "frequencies", read_only(freqs))

    @property
    def margins_db(self) -> NDArray[np.float64]:
        r""":math:`L' - L_\mathrm{b}`, in dB, in the shape of the readings."""
        return np.asarray(
            self.signal_and_background - self.background, dtype=np.float64
        )

    @property
    def limited(self) -> NDArray[np.bool_]:
        """Where the margin is under 6 dB, so the band is at the limit of measurement.

        Judged settled: 32,3 - 26,3 dB is 5,999 999 999 999 996 in binary and
        still the 6 dB it is.
        """
        return np.asarray(settled(self.margins_db) < _MARGIN_LIMIT, dtype=np.bool_)

    @property
    def corrected_levels(self) -> NDArray[np.float64]:
        """The corrected levels ``L``, in dB, in the shape of the readings."""
        lp = np.asarray(self.signal_and_background, dtype=np.float64)
        lb = np.asarray(self.background, dtype=np.float64)
        diff = 10.0 ** (lp / 10.0) - 10.0 ** (lb / 10.0)
        with np.errstate(invalid="ignore", divide="ignore"):
            subtracted = 10.0 * np.log10(np.where(diff > 0.0, diff, 1.0))
        # >= 15: unchanged; 6 <= margin < 15: energy subtraction; < 6: 1,3 dB.
        judged = settled(self.margins_db)
        corrected = np.where(judged >= _MARGIN_NEGLIGIBLE, lp, subtracted)
        return np.asarray(
            np.where(self.limited, lp - _LIMIT_CORRECTION, corrected), dtype=np.float64
        )

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        r"""Plot the margin :math:`L' - L_\mathrm{b}` of each band against the criterion.

        The bands at 15 dB or more are used unchanged, those between 6 dB
        and 15 dB have the background subtracted in energy, and those under
        6 dB are held at the 1.3 dB limit of measurement; the two boundaries
        are drawn across the bands and the three regimes are told apart. A
        (positions, bands) record draws one line per position.

        Requires matplotlib (``pip install phonometry[plot]``).

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the margin bars, or to the line of each
            position.
        :return: The axes.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_background_corrected_level

        check_language(language)
        return plot_background_corrected_level(self, ax=ax, language=language, **kwargs)


def background_corrected_level(
    signal_and_background: float | Sequence[float] | np.ndarray,
    background: float | Sequence[float] | np.ndarray,
    *,
    frequencies: Sequence[float] | np.ndarray | None = None,
) -> BackgroundCorrectedLevel:
    r"""Correct a measured level for background noise (ISO 16251-1 F. (2)).

    :param signal_and_background: Measured level ``L'`` (with background) per
        band, in dB; a (positions, bands) array is corrected position by
        position.
    :param background: Background-noise level ``Lb`` per band, in dB, of the
        same shape.
    :param frequencies: The band centre frequencies, in Hz, one per band, for
        the plot to name the bands by; ``None`` (the default) numbers them.
    :return: The correction, as a :class:`BackgroundCorrectedLevel`: the
        corrected levels ``L`` in its ``corrected_levels``, and in its
        ``limited`` the bands at the 1.3 dB limit of measurement (report as
        :math:`> \Delta L`).
    :raises ValueError: Mismatched shapes, non-finite values, or band
        frequencies that are not one positive value per band.
    """
    lp = _finite(signal_and_background, "signal_and_background")
    lb = _finite(background, "background")
    require_equal_shapes(
        "background_corrected_level",
        {"signal_and_background": lp.shape, "background": lb.shape},
        "band",
    )
    return BackgroundCorrectedLevel(
        lp,
        lb,
        frequencies=None
        if frequencies is None
        else np.asarray(frequencies, dtype=np.float64),
    )


@dataclass(frozen=True)
class FloorCoveringImprovementResult(OwnsArrays):
    r"""Impact-sound improvement of a floor covering (ISO 16251-1).

    :ivar frequencies: One-third-octave band centre frequencies, in Hz.
    :ivar improvement: Improvement of impact sound insulation ``ΔL`` per
        band, in dB.
    :ivar delta_lw: Weighted improvement ``ΔLw`` (ISO 717-2), in dB, or ``None``
        when the spectrum does not contain the 16 one-third-octave rating
        bands 100-3150 Hz. A wider clause 6.3 spectrum (e.g. the 18 bands
        100-5000 Hz, optionally extended down to 50 Hz) is rated on its
        100-3150 Hz sub-range.
    :ivar ci_delta: Spectrum adaptation term ``CI,Δ`` (ISO 717-2:2020
        Formula (A.4); required in the ISO 16251-1 Clause 8 e) statement of
        results), in dB, or ``None`` when ``delta_lw`` is ``None``.
    :ivar background_margin_db: Per band, the smallest margin
        :math:`L' - L_\mathrm{b}` of a measured level over the background,
        over every position and both floors (Formula (2)), in dB; ``None`` when
        no background correction was applied. :attr:`limited` is read from it
        and the 6 dB of Formula (2), so it is not a field.
    """

    frequencies: np.ndarray
    improvement: np.ndarray
    delta_lw: int | None
    ci_delta: int | None = None
    background_margin_db: np.ndarray | None = None

    def __post_init__(self) -> None:
        """Reject an improvement spectrum whose columns cover different bands.

        The ISO 16251-1 fiche prints one row per band and prefixes ``>`` to the
        bands that only reached the 1,3 dB limit of measurement, which is the
        difference between a measured improvement and a lower bound on one.
        That prefix is taken from ``limited`` by position, so a mask of another
        length claims the limit for bands that were never near it and drops it
        from the bands that were. ``ΔLw`` is rated over the 100 Hz to 3150 Hz
        sub-range located inside ``frequencies``, so an axis of another length
        rates a different stretch of spectrum from the one tabulated beside it.

        The ratings are whole decibels by construction (ISO 717-2 rounds both
        ``ΔLw`` and ``CI,Δ`` to integers, and that is what
        :func:`~phonometry.building.weighted_impact_improvement` and
        :func:`~phonometry.building.impact_improvement_adaptation_term`
        return), and the fiche prints them as integers: a float smuggled in by
        a hand-built result would either crash the ``{ci_delta:+d}`` format
        with a message naming no field, or print an unlocalised decimal point
        on a comma-decimal sheet. Both are refused here by name instead.

        An adaptation term without the rating it adapts is refused as well.
        ``CI,Δ = CI,r,0 - CI,r`` (ISO 717-2:2020 Formula (A.4)) and ``ΔLw``
        are the two numbers the same weighted rating returns for the same
        reference floor with the covering, ``Ln,r = Ln,r,0 - ΔL`` over the same
        16 bands 100 Hz to 3150 Hz, so no spectrum can determine one and leave
        the other undetermined: ``delta_lw`` is ``None`` exactly when those
        bands are absent, and then ``CI,Δ`` has no derivation either. The
        opposite pairing is legitimate and stays allowed: a result that carries
        ``delta_lw`` without ``ci_delta`` is a rating quoted without the
        adaptation term, and the fiche then prints the bare ``ΔLw`` rather than
        an invented ``(+0)``. Left unguarded, the refused pairing printed a
        fiche that dropped the term in silence: the boxed statement of results
        fell through to the unrated characterisation headline (*Reduction of
        impact sound pressure level ΔL, 100 Hz to 3150 Hz*) with no ``CI,Δ``
        anywhere on the sheet, under a standard-basis line still promising that
        the statement of results carries it.

        :raises TypeError: if ``delta_lw`` / ``ci_delta`` is not an integer (or
            ``None``); a bool is not one.
        :raises ValueError: if the frequencies, the improvement and the
            limit-of-measurement mask do not agree on how many bands there
            are, or if ``ci_delta`` is given while ``delta_lw`` is ``None``.
        """
        require_ranks(self, frequencies=1, improvement=1, background_margin_db=1)
        require_same_length(self, "frequencies", "improvement", "background_margin_db")
        for name in ("delta_lw", "ci_delta"):
            value = getattr(self, name)
            # A bool is an int in Python, so it is excluded explicitly.
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int)
            ):
                msg = (
                    f"FloorCoveringImprovementResult: '{name}' must be an "
                    f"integer number of decibels (ISO 717-2 ratings are "
                    f"rounded to whole dB) or None; got {value!r}."
                )
                raise TypeError(msg)
        if self.delta_lw is None and self.ci_delta is not None:
            msg = (
                f"FloorCoveringImprovementResult: 'ci_delta' is the adaptation "
                f"term of 'delta_lw' (ISO 717-2:2020 Formula (A.4) rates the "
                f"same 100-3150 Hz bands), so it cannot be given while "
                f"'delta_lw' is None; got ci_delta={self.ci_delta!r}."
            )
            raise ValueError(msg)

    @property
    def limited(self) -> np.ndarray:
        r"""Per band, whether a position reached the 1.3 dB limit of measurement.

        ``True`` where the smallest margin over the background fell below the
        6 dB of Formula (2), so the band is reported as :math:`> \Delta L`; all
        ``False`` when no background correction was applied. The margin is
        judged settled, as Formula (2) itself is.
        """
        if self.background_margin_db is None:
            return np.zeros(np.shape(self.frequencies), dtype=bool)
        return np.asarray(
            settled(self.background_margin_db) < _MARGIN_LIMIT, dtype=bool
        )

    def octave_bands(self) -> OctaveBandSpectrum:
        """``ΔLoct`` in octave bands, via Formula (5) (needs whole octave triplets)."""
        return improvement_octave_bands(self.improvement, frequencies=self.frequencies)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the improvement spectrum ``ΔL`` (with ``ΔLw`` when available).

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_floor_covering_improvement

        check_language(language)
        return plot_floor_covering_improvement(self, ax=ax, language=language, **kwargs)

    def report(
        self,
        path: str,
        *,
        metadata: ReportMetadata | None = None,
        engine: str = "reportlab",
        verbose: bool = False,
        language: str = "en",
    ) -> str:
        r"""Render an ISO 16251-1 impact-improvement test-report fiche to PDF.

        Writes a one-page accredited report (BS EN ISO 16251-1:2014, the
        small-mock-up laboratory method for the reduction of transmitted impact
        sound by soft floor coverings): the standard-basis line, an optional
        metadata header block, a two-panel body with the per-band table
        (frequency and the reduction of impact sound pressure level ``ΔL``,
        bands at the 1,3 dB limit of measurement prefixed ``>``) beside the
        ``ΔL(f)`` improvement curve, a boxed single-number weighted improvement
        ``ΔLw (CI,Δ)`` (ISO 717-2, the Clause 8 e) statement of results; a
        characterisation headline replaces it when the spectrum lacks the 16
        rating bands 100-3150 Hz), an optional verdict row and a footer.

        :param path: Destination path of the PDF file.
        :param metadata: Optional :class:`~phonometry.ReportMetadata`; ``None``
            produces a body-and-disclaimer fiche whose header shows only the
            measured frequency range. The applicable descriptive fields are
            ``client``, ``manufacturer``, ``specimen`` (the floor covering under
            test), ``mounting``, ``mass_per_area``, ``test_room``,
            ``test_date``, ``temperature_c``, ``pressure``,
            ``measurement_standard``, ``laboratory``, ``operator``,
            ``report_id`` and ``notes``. The bare reference floor is the
            standardised heavyweight floor of ISO 717-2:2020 Table 4, fixed by
            the standard. When ``requirement`` is set the fiche adds a verdict
            row (a higher weighted improvement is better, so the result passes
            at or above the requirement).
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: When ``True``, the per-band table gains the
            reference-floor-with-covering column
            :math:`L_\mathrm{n,r} = L_\mathrm{n,r,0} - \Delta L`
            (ISO 717-2:2020 Formula (1)), the derivation basis of ``ΔLw``, when
            the spectrum is exactly the 16 rating bands 100-3150 Hz.
        :param language: Fiche language: ``"en"`` (default, English, decimal
            point) or ``"es"`` (Spanish, decimal comma).
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` is not ``"reportlab"``.
        :raises ImportError: If reportlab is not installed
            (``pip install phonometry[report]``), or matplotlib is missing for
            the embedded figure (``pip install phonometry[plot]``).
        """
        from ..._i18n import check_language

        check_language(language)
        check_engine(engine)
        from ..._report.iso16251 import render_iso16251_report

        return render_iso16251_report(
            self, path, metadata=metadata, verbose=verbose, language=language
        )


def _rating_slice(frequencies: np.ndarray) -> np.ndarray | None:
    """Indices of the 16 rating bands 100-3150 Hz within ``frequencies``.

    Clause 6.3 measures over 18 bands 100-5000 Hz (optionally extended down
    to 50 Hz); the ISO 717-2 rating of clause 6.5 uses the 100-3150 Hz
    sub-range. Returns ``None`` when the spectrum does not contain all 16
    rating bands (nominal centres matched within 6 %).
    """
    if frequencies.ndim != 1:
        return None
    indices: list[int] = []
    for target in _RATING_FREQS:
        candidates = np.nonzero(np.abs(frequencies - target) <= 0.06 * target)[0]
        if candidates.size != 1:
            return None
        indices.append(int(candidates[0]))
    return np.asarray(indices, dtype=np.intp)


def _rating(
    improvement: np.ndarray, frequencies: np.ndarray
) -> tuple[int | None, int | None]:
    """``(ΔLw, CI,Δ)`` over the 100-3150 Hz sub-range, or ``(None, None)``."""
    idx = _rating_slice(frequencies)
    if idx is None:
        return None, None
    rated = improvement[idx]
    return (
        weighted_impact_improvement(rated),
        impact_improvement_adaptation_term(rated),
    )


def impact_improvement(
    bare: float | Sequence[float] | np.ndarray,
    with_covering: float | Sequence[float] | np.ndarray,
    *,
    frequencies: float | Sequence[float] | np.ndarray,
    background: float | Sequence[float] | np.ndarray | None = None,
) -> FloorCoveringImprovementResult:
    r"""Improvement of impact sound insulation ``ΔL`` of a floor covering.

    ISO 16251-1. The acceleration levels without (``L0``) and with (``L1``)
    the specimen may be
    given either as one value per band (already averaged over the
    tapping-machine
    and accelerometer positions) or, for the raw measurement, as a
    ``(positions, bands)`` array. The standard's order of operations is
    followed:
    the background correction (Formula (2)) is applied **per position**, then
    the
    level difference :math:`\Delta L_{t,a} = L_0 - L_1` (Formula (3)), then
    the arithmetic mean
    over positions :math:`\Delta L = \mathrm{mean}(\Delta L_{t,a})`
    (Formula (4)), necessary because Formula
    (2) is non-linear, so correcting must precede averaging.

    :param bare: Bare-plate acceleration level ``L0``, in dB; ``(bands,)`` or
        ``(positions, bands)``.
    :param with_covering: Level with the specimen ``L1``, in dB; same shape as ``bare``.
    :param frequencies: One-third-octave band centre frequencies, in Hz (``(bands,)``).
    :param background: Optional background-noise level ``Lb``, in dB; ``(bands,)``
        (applied to every position) or ``(positions, bands)``. When given, ``L0``
        and ``L1`` are background-corrected (Formula (2)) per position before
        the difference, and bands where any position hits the 1.3 dB limit
        are flagged.
    :return: :class:`FloorCoveringImprovementResult` (``ΔL`` per band).
    :raises ValueError: Mismatched shapes or non-finite values.
    """
    l0 = _finite(bare, "bare")
    l1 = _finite(with_covering, "with_covering")
    freqs = _finite(frequencies, "frequencies")
    n_bands = freqs.shape[0]
    require_equal_shapes(
        "impact_improvement",
        {"bare": l0.shape, "with_covering": l1.shape},
        "position and band",
    )
    if l0.ndim not in (1, 2) or l0.shape[-1] != n_bands:
        msg = (
            "'bare'/'with_covering' must be (bands,) or (positions, bands) "
            "matching 'frequencies'."
        )
        raise ValueError(msg)

    margin: np.ndarray | None = None
    if background is not None:
        lb = _finite(background, "background")
        if lb.shape not in ((n_bands,), l0.shape):
            msg = (
                "'background' must be (bands,) or match the (positions, bands) "
                "shape of 'bare'/'with_covering'."
            )
            raise ValueError(msg)
        lb = np.broadcast_to(lb, l0.shape)
        # Formula (2) per position, then Formula (3), then Formula (4). A band
        # is at the limit of measurement where any position of either floor
        # is, so the smallest margin is the one the result keeps.
        margins = np.minimum(l0 - lb, l1 - lb)
        margin = margins.min(axis=0) if margins.ndim == 2 else margins  # noqa: PLR2004
        l0 = background_corrected_level(l0, lb).corrected_levels
        l1 = background_corrected_level(l1, lb).corrected_levels

    delta_per_position = l0 - l1  # Formula (3)
    if delta_per_position.ndim == 2:  # noqa: PLR2004
        improvement = delta_per_position.mean(axis=0)  # Formula (4)
    else:
        improvement = delta_per_position
    delta_lw, ci_delta = _rating(improvement, freqs)
    return FloorCoveringImprovementResult(
        frequencies=freqs,
        improvement=improvement,
        delta_lw=delta_lw,
        ci_delta=ci_delta,
        background_margin_db=margin,
    )


#: The quantities an :class:`OctaveBandSpectrum` can hold: the improvements
#: of ISO 16251-1 and ISO 10140-1 Annexes G and H, the sound reduction index
#: of a joint (ISO 10140-1 Annex J) and the rainfall intensity level, raw and
#: normalized (ISO 10140-1 Annex K).
_OCTAVE_BAND_QUANTITIES: tuple[str, ...] = ("ΔL", "ΔR", "Rs", "LI", "LI,norm")


@dataclass(frozen=True)
class OctaveBandSpectrum(OwnsArrays):
    """A one-third-octave result folded into octave bands, with what it holds.

    What :func:`improvement_octave_bands` returns, and what the
    ``octave_bands()`` methods of the floor-covering, laboratory lining,
    laboratory floor-covering, joint and rainfall results return: the octave
    centres and the octave values side by side, named, so that neither can be
    read as the other, and the quantity they are values of.

    :ivar frequencies: The octave centre frequencies, in hertz.
    :ivar values: The octave value of :attr:`quantity` in each band, in dB.
    :ivar quantity: Which quantity the values are: ``"ΔL"`` (an impact
        improvement), ``"ΔR"`` (a sound reduction improvement), ``"Rs"`` (the
        sound reduction index of a joint), ``"LI"`` or ``"LI,norm"`` (the
        rainfall sound intensity level, raw or normalized).
    """

    _display_units: ClassVar[Mapping[str, str]] = MappingProxyType({"values": "dB"})

    frequencies: np.ndarray
    values: np.ndarray
    quantity: str

    def __post_init__(self) -> None:
        """Reject an unknown quantity or columns of different lengths.

        :raises ValueError: if ``quantity`` is not one of the five above, or
            the two columns are not one-dimensional arrays of one value per
            octave.
        :raises TypeError: if ``quantity`` is not a text.
        """
        require_choice(self.quantity, "quantity", _OCTAVE_BAND_QUANTITIES)
        require_ranks(self, frequencies=1, values=1)
        require_same_length(self, "frequencies", "values")

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the octave values against their octave bands.

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.

        :param ax: Existing axes, or ``None`` to create a figure.
        :param language: Label language, ``"en"`` (default) or ``"es"``.
        :param kwargs: Forwarded to the octave curve ``plot`` call.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_octave_band_spectrum

        check_language(language)
        return plot_octave_band_spectrum(self, ax=ax, language=language, **kwargs)


def improvement_octave_bands(
    improvement: Sequence[float] | np.ndarray,
    *,
    frequencies: Sequence[float] | np.ndarray,
    quantity: str = "ΔL",
) -> OctaveBandSpectrum:
    r"""Convert a one-third-octave improvement spectrum to octaves (F. (5)).

    :math:`\Delta L_\mathrm{oct} = -10 \log_{10}[(1/3) \sum_{j=1}^{3} 10^{-\Delta L_j/10}]`
    dB over the three thirds of
    each octave.

    :param improvement: Improvement ``ΔL`` per one-third-octave band, in dB.
    :param frequencies: The matching one-third-octave centre frequencies, in Hz;
        must contain whole octave triplets (centre / centre·2^(±1/3)).
    :param quantity: What the values are, for the record and its plot:
        ``"ΔL"`` (Default), ``"ΔR"`` or ``"Rs"``, the three quantities folded
        into octaves by this average of transmitted power.
    :return: An :class:`OctaveBandSpectrum` with the octave centres
        (``.frequencies``) and the octave values (``.values``).
    :raises ValueError: The thirds do not group into complete octave triplets,
        or ``quantity`` is not one of the three.
    :raises TypeError: if ``quantity`` is not a text.
    """
    require_choice(quantity, "quantity", _OCTAVE_BAND_QUANTITIES[:3])
    dl = _finite(improvement, "improvement")
    freqs = _finite(frequencies, "frequencies")
    require_equal_shapes(
        "improvement_octave_bands",
        {"improvement": dl.shape, "frequencies": freqs.shape},
        "band",
    )
    octave_freqs: list[float] = []
    octave_values: list[float] = []
    by_freq = {round(float(f), 3): float(d) for f, d in zip(freqs, dl, strict=True)}
    for centre in _octave_centres(freqs):
        thirds = [centre * 2.0 ** (k / 3.0) for k in (-1, 0, 1)]
        try:
            vals = [by_freq[round(t, 3)] for t in _nearest(thirds, by_freq)]
        except KeyError:
            msg = (
                f"Octave {centre:g} Hz is missing one of its one-third-octave "
                "bands; provide complete triplets."
            )
            raise ValueError(msg) from None
        octave_freqs.append(centre)
        octave_values.append(
            -10.0 * np.log10(np.mean([10.0 ** (-v / 10.0) for v in vals]))
        )
    return OctaveBandSpectrum(
        frequencies=np.asarray(octave_freqs, dtype=np.float64),
        values=np.asarray(octave_values, dtype=np.float64),
        quantity=quantity,
    )


def _octave_centres(freqs: np.ndarray) -> list[float]:
    """The octave centres (…125, 250, 500…) present among one-third-octave freqs."""
    octaves = [
        31.5,
        63.0,
        125.0,
        250.0,
        500.0,
        1000.0,
        2000.0,
        4000.0,
        8000.0,
    ]
    lo, hi = float(np.min(freqs)), float(np.max(freqs))
    return [c for c in octaves if lo <= c <= hi]


def _nearest(targets: list[float], available: dict[float, float]) -> list[float]:
    """Snap each nominal third-octave frequency to the nearest available key."""
    keys = np.asarray(sorted(available))
    out = []
    for t in targets:
        idx = int(np.argmin(np.abs(keys - t)))
        if abs(keys[idx] - t) > t * 0.06:  # within ~6 % of the nominal ratio
            raise KeyError(t)
        out.append(float(keys[idx]))
    return out
