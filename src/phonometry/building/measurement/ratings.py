#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Single-number weighted ratings of sound insulation and their spectrum
adaptation terms (ISO 717-1 airborne, ISO 717-2 impact).

ISO 717 rates a curve, not a room. Whatever produced the band values (a field
measurement to ISO 16283, a laboratory measurement to ISO 10140, a prediction
to ISO 12354), both parts of ISO 717 reduce them to a single number by the same
reference-curve method: one shift search, one pair of deviation bounds, one
rounding rule, run against the airborne reference curve of ISO 717-1 or the
impact reference curve of ISO 717-2, whose only structural difference is the
sign an unfavourable deviation has. That shared machinery, with the Table 3
reference curves and the Table 4 / Table B.1 spectra it reads, is the subject
of this module.

**Weighted rating (ISO 717-1).** The reference-curve method of Clause 4.4
shifts the reference curve of Table 3 in 1 dB steps towards the measured
curve until the sum of unfavourable deviations (measured below the
shifted reference) is as large as possible but not more than 32,0 dB for
the 16 one-third-octave bands (100 Hz to 3150 Hz) or 10,0 dB for the 5
octave bands (125 Hz to 2000 Hz). The weighted rating (``Rw``, ``R'w``,
``Dn,w``, ``DnT,w`` ...) is the shifted reference read at 500 Hz. The
spectrum adaptation terms are :math:`C = X_{\mathrm{A}1} - X_\mathrm{w}` and
:math:`C_\mathrm{tr} = X_{\mathrm{A}2} - X_\mathrm{w}`
with :math:`X_{\mathrm{A}j} = -10 \log_{10} \sum 10^{(L_{ij} - X_i)/10}` rounded to an
integer, using
the A-weighted spectra No. 1 (pink noise, ``C``) and No. 2 (urban traffic,
``Ctr``) of Table 4 (Clause 4.5, Formula (1) and (2)). Input levels are
reduced to one decimal place before use (Clause 4.4, footnote 1). The
reference values, spectra and shifting rule are identical in the 2013 and
2020 editions of ISO 717-1.

**Enlarged frequency ranges (ISO 717-1 Annex B; ISO 717-2 A.2.1 NOTE).**
When measurements cover an enlarged range, additional adaptation terms are
stated with the range as a subscript: ``C50-3150``, ``C50-5000``,
``C100-5000`` (and the ``Ctr`` counterparts) with the Table B.1 spectra, and
``CI,50-2500`` for impact. :func:`weighted_rating_extended` and
:func:`weighted_impact_rating_extended` compute them alongside the core
rating. Both accept ``one_decimal=True`` for the "1/10 dB for the expression
of uncertainty" variant of Clauses 4.4/4.5 (reference-curve shift in 0,1 dB
steps and one-decimal reductions), which ISO 12999-1:2020 Annex B requires
when stating the uncertainty of single-number values.

**Weighted impact rating (ISO 717-2).** The reference-curve method of
Clause 4.3 shifts the Table 3 impact reference curve towards the measured
curve until the sum of unfavourable deviations (here where the
**measurement exceeds** the reference, the sign opposite to airborne) is
as large as possible but not more than 32,0 dB (16 one-third-octave bands)
or 10,0 dB (5 octave bands). The rating (``Ln,w``, ``L'n,w``, ``L'nT,w``)
is the shifted reference read at 500 Hz, reduced by a further 5 dB for
octave bands (Clause 4.3.2). The spectrum adaptation term
:math:`C_\mathrm{I} = L_\mathrm{n,sum} - 15 - L_\mathrm{n,w}` uses the energetic sum ``Ln,sum``
over
100 Hz to 2500 Hz (one-third octave) or 125 Hz to 2000 Hz (octave),
rounded to an integer (Clause A.2.1, Formulae (A.1) to (A.3)). The Table 3
reference values, the shifting rule and CI are identical in the 2013 and
2020 editions of ISO 717-2 (the 2020 edition only adds Annex D for the
rubber-ball heavy/soft impactor, out of scope here).

**Improvements rated on a reference element (ISO 717-2:2020 Clauses 5 and 6,
ISO 717-1:2020 Annex D).** A floor covering and a lining are rated on a
standard element rather than on the floor or wall they were measured on, so
that the single number describes the product and not the laboratory. The
measured improvement is added to (subtracted from) the reference curve of the
element, the two curves are rated, and the improvement is the difference of
the two ratings: ``ΔLw`` on the heavyweight floor and ``ΔLt,w`` on the three
lightweight floors of Table 4 (:data:`IMPACT_REFERENCE_FLOORS`), and ``ΔRw``
with ``Δ(Rw + C)`` and ``Δ(Rw + Ctr)`` on the heavy wall, the heavy floor and
the lightweight wall of Table E.1 (:data:`LINING_REFERENCE_ELEMENTS`). Both
tables were printed in ISO 10140-5:2010 (Tables C.1 and B.1); its 2021
edition keeps the constructions and refers to ISO 717 for the curves.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, overload

import numpy as np

from ..._internal.boundary import round_half_away_from_zero, round_half_up
from ..._internal.frozen import read_only_copy
from ..._internal.levels_math import energy_sum
from ..._internal.validation import (
    check_engine,
    require_choice,
    require_equal_shapes,
    require_ranks,
    require_same_length,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from matplotlib.axes import Axes

    from ..._report.metadata import ReportMetadata

# --- ISO 717-1 Table 3 reference values ----------------------------------

#: One-third-octave reference values, 100 Hz to 3150 Hz (Table 3).
_REF_THIRD_OCTAVE: tuple[int, ...] = (
    33,
    36,
    39,
    42,
    45,
    48,
    51,
    52,
    53,
    54,
    55,
    56,
    56,
    56,
    56,
    56,
)
#: Octave reference values, 125 Hz to 2000 Hz (Table 3).
_REF_OCTAVE: tuple[int, ...] = (36, 45, 52, 55, 56)

#: One-third-octave band centre frequencies, 100 Hz to 3150 Hz (16 bands).
_FREQ_THIRD_OCTAVE: tuple[float, ...] = (
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
#: Octave band centre frequencies, 125 Hz to 2000 Hz (5 bands).
_FREQ_OCTAVE: tuple[float, ...] = (125.0, 250.0, 500.0, 1000.0, 2000.0)

#: Number of bands in each ISO 717 band set, used to infer the band set
#: from the input length: 16 one-third-octave bands (100 Hz to 3150 Hz)
#: and 5 octave bands (125 Hz to 2000 Hz).
_N_THIRD_OCTAVE_BANDS = 16
_N_OCTAVE_BANDS = 5

#: Index of the 500 Hz band in each band set (the rating is read there).
_INDEX_500_THIRD = 7
_INDEX_500_OCTAVE = 2

#: Maximum sum of unfavourable deviations. These bounds are shared by both
#: rating paths: ISO 717-1 Clause 4.4 (airborne) and ISO 717-2 Clause 4.3
#: (impact) specify the identical 32,0 dB (16 one-third-octave bands) and
#: 10,0 dB (5 octave bands) limits.
_MAX_UNFAVOURABLE_THIRD = 32.0
_MAX_UNFAVOURABLE_OCTAVE = 10.0

#: The refusal of a band set the ratings do not read.
_BANDS_REFUSAL = "'bands' must be 'third-octave', 'octave' or None."

#: Tolerance absorbing floating-point noise when comparing the
#: unfavourable-deviation sum (a true multiple of 0,1 dB) to the bound.
_SHIFT_TOLERANCE = 1e-6

#: Tolerance for checking a stored unfavourable-deviation sum against the two
#: curves it summarises, so a caller who recomputed it along another
#: floating-point path is not refused over the last bit (the impact search
#: runs on negated curves and reaches the same tenths by a different route).
#: Distinct from _SHIFT_TOLERANCE, which guards the search's own comparison
#: to the bound rather than a field against its array.
_SUM_TOLERANCE = 1e-9

#: Tolerance for checking that ``scale * step`` reconstructs exactly 1,
#: i.e. that the reference-curve shift step divides 1 dB exactly (1.0 or
#: 0.1 dB per ISO 717 / ISO 12999-1:2020 Annex B.2), absorbing the
#: representation error of step values like 0.1. Distinct from
#: _SHIFT_TOLERANCE, which guards the deviation-sum comparison.
_STEP_DIVISOR_TOLERANCE = 1e-12

# --- ISO 717-2 Table 3 impact reference values ---------------------------

#: One-third-octave impact reference values, 100 Hz to 3150 Hz (Table 3).
_REF_IMPACT_THIRD_OCTAVE: tuple[int, ...] = (
    62,
    62,
    62,
    62,
    62,
    62,
    61,
    60,
    59,
    58,
    57,
    54,
    51,
    48,
    45,
    42,
)
#: Octave impact reference values, 125 Hz to 2000 Hz (Table 3).
_REF_IMPACT_OCTAVE: tuple[int, ...] = (67, 67, 65, 62, 49)

#: Octave-band single-number reduction applied to L'n,w / L'nT,w
#: (ISO 717-2 Clause 4.3.2): the shifted reference at 500 Hz minus 5 dB.
_IMPACT_OCTAVE_OFFSET = -5

#: One-third-octave band count for CI (100 Hz to 2500 Hz, excludes 3150 Hz).
_CI_THIRD_OCTAVE_BANDS = 15

# --- ISO 717-1 Table 4 spectra (A-weighted, normalized to 0 dB) ----------

#: Spectrum No. 1 (pink noise, for C), one-third octave 100-3150 Hz.
_SPECTRUM1_THIRD: tuple[int, ...] = (
    -29,
    -26,
    -23,
    -21,
    -19,
    -17,
    -15,
    -13,
    -12,
    -11,
    -10,
    -9,
    -9,
    -9,
    -9,
    -9,
)
#: Spectrum No. 2 (urban traffic, for Ctr), one-third octave 100-3150 Hz.
_SPECTRUM2_THIRD: tuple[int, ...] = (
    -20,
    -20,
    -18,
    -16,
    -15,
    -14,
    -13,
    -12,
    -11,
    -9,
    -8,
    -9,
    -10,
    -11,
    -13,
    -15,
)
#: Spectrum No. 1 (for C), octave 125-2000 Hz.
_SPECTRUM1_OCTAVE: tuple[int, ...] = (-21, -14, -8, -5, -4)
#: Spectrum No. 2 (for Ctr), octave 125-2000 Hz.
_SPECTRUM2_OCTAVE: tuple[int, ...] = (-14, -10, -7, -4, -6)

# --- ISO 717-1:2020 Table B.1 spectra for the enlarged frequency ranges ----
# One-third-octave sound levels, A-weighted and normalized to 0 dB over each
# range. Spectrum No. 1 has one column for C50-3150 and one shared column for
# C50-5000 and C100-5000; spectrum No. 2 has a single column valid for Ctr in
# any enlarged range.

#: One-third-octave band centre frequencies, 50 Hz to 5000 Hz (21 bands).
_FREQ_50_5000: tuple[float, ...] = (
    50.0,
    63.0,
    80.0,
    *_FREQ_THIRD_OCTAVE,
    4000.0,
    5000.0,
)
#: Spectrum No. 1 column for C50-3150 (19 bands, 50-3150 Hz).
_SPECTRUM1_50_3150: tuple[int, ...] = (
    -40,
    -36,
    -33,
    -29,
    -26,
    -23,
    -21,
    -19,
    -17,
    -15,
    -13,
    -12,
    -11,
    -10,
    -9,
    -9,
    -9,
    -9,
    -9,
)
#: Spectrum No. 1 column for C50-5000 and C100-5000 (21 bands, 50-5000 Hz;
#: the 100-5000 Hz range uses the same column restricted to its bands).
_SPECTRUM1_50_5000: tuple[int, ...] = (
    -41,
    -37,
    -34,
    -30,
    -27,
    -24,
    -22,
    -20,
    -18,
    -16,
    -14,
    -13,
    -12,
    -11,
    -10,
    -10,
    -10,
    -10,
    -10,
    -10,
    -10,
)
#: Spectrum No. 2 column for Ctr in any enlarged range (21 bands, 50-5000 Hz).
_SPECTRUM2_50_5000: tuple[int, ...] = (
    -25,
    -23,
    -21,
    -20,
    -20,
    -18,
    -16,
    -15,
    -14,
    -13,
    -12,
    -11,
    -9,
    -8,
    -9,
    -10,
    -11,
    -13,
    -15,
    -16,
    -18,
)

#: The enlarged one-third-octave adaptation ranges of ISO 717-1:2020 Annex B
#: (airborne): descriptor suffix -> (band frequencies, spectrum No. 1 levels,
#: spectrum No. 2 levels).
_EXTENDED_RANGES: dict[
    str, tuple[tuple[float, ...], tuple[int, ...], tuple[int, ...]]
] = {
    "50_3150": (_FREQ_50_5000[:19], _SPECTRUM1_50_3150, _SPECTRUM2_50_5000[:19]),
    "50_5000": (_FREQ_50_5000, _SPECTRUM1_50_5000, _SPECTRUM2_50_5000),
    "100_5000": (_FREQ_50_5000[3:], _SPECTRUM1_50_5000[3:], _SPECTRUM2_50_5000[3:]),
}

#: The enlarged CI summation range of ISO 717-2:2020 A.2.1 NOTE: 50-2500 Hz
#: (18 one-third-octave bands).
_CI_50_2500_FREQS: tuple[float, ...] = _FREQ_50_5000[:18]


_VALUES_1D_MSG = "'values_by_band' must be one-dimensional."
_VALUES_FINITE_MSG = "'values_by_band' must contain only finite values."

#: The one-third-octave bands of the ISO 717 rating that are not the centre
#: of an octave band: a mapping keyed by any of them holds one-third octaves.
_THIRD_OCTAVE_ONLY: frozenset[float] = frozenset(_FREQ_THIRD_OCTAVE) - frozenset(
    _FREQ_OCTAVE
)


def _by_band(
    values: Mapping[float, float] | Sequence[float] | np.ndarray,
    bands: str | None,
    name: str,
) -> tuple[np.ndarray, str | None]:
    """The values in rating order, read from a mapping by band when given one.

    A mapping is keyed by band centre frequency in hertz, as
    :meth:`~phonometry.io.BandedRow.spectrum` returns a row's bands: a
    mapping that holds any one-third-octave band that is not an octave
    centre is read as one-third octaves (100 Hz to 3150 Hz), any other as
    the five octaves 125 Hz to 2000 Hz, unless *bands* says which. Keys
    outside the rated range are not read. A band the rating needs and the
    mapping does not hold is refused, never filled from its neighbours, so
    a spectrum with a gap cannot be rated as if it had none.

    :return: The values as an array in the order of the rating bands, and
        the band set they were read as (*bands* itself for a sequence).
    :raises ValueError: for a mapping that lacks a rating band, naming each
        one missing.
    """
    if not isinstance(values, Mapping):
        return np.asarray(values, dtype=np.float64), bands
    if bands is None:
        third = any(centre in values for centre in _THIRD_OCTAVE_ONLY)
        bands = "third-octave" if third else "octave"
    if bands == "third-octave":
        centres = _FREQ_THIRD_OCTAVE
    elif bands == "octave":
        centres = _FREQ_OCTAVE
    else:
        msg = _BANDS_REFUSAL
        raise ValueError(msg)
    missing = [centre for centre in centres if centre not in values]
    if missing:
        named = ", ".join(f"{centre:g}" for centre in missing)
        msg = (
            f"{name!r} holds no value in the {bands} band of {named} Hz, and "
            f"ISO 717 rates the {bands} bands {centres[0]:g} Hz to "
            f"{centres[-1]:g} Hz; a missing band is never filled in"
        )
        raise ValueError(msg)
    return np.asarray([values[centre] for centre in centres], dtype=np.float64), bands


def _require_finite_curves(owner: object, *fields: str) -> None:
    """Require each named optional band curve of *owner* to be finite.

    The ``__post_init__`` companion of the entry points' own finiteness
    refusals: :func:`weighted_rating` and :func:`weighted_impact_rating`
    refuse non-finite input by name, so no constructor ever stores a
    non-finite band, and an instance carrying one can only have been
    assembled by hand or through :func:`dataclasses.replace`. ``None``
    fields (a rating built from the single numbers alone) are skipped.

    :param owner: The instance whose curve fields are checked.
    :param fields: Names of the optional per-band array fields.
    :raises ValueError: if a present curve carries a non-finite value.
    """
    for name in fields:
        value = getattr(owner, name)
        if value is not None and not np.all(
            np.isfinite(np.asarray(value, dtype=np.float64))
        ):
            msg = f"{type(owner).__name__}: '{name}' must contain only finite values."
            raise ValueError(msg)


def _require_unfavourable_sum(
    owner: WeightedRatingResult | ImpactRatingResult, *, impact: bool
) -> None:
    """Require ``unfavourable_sum`` to restate *owner*'s own two curves.

    The sum of unfavourable deviations is not a number kept beside the
    curves; it *is* those curves, added up. ISO 717-1 Clause 4.4 counts a
    band as unfavourable where the measurement falls below the shifted
    reference and ISO 717-2 Clause 4.3 where it rises above it -- the one
    structural difference between the two parts, which is why the sign
    arrives as *impact* rather than being read off a field. Neither part
    rounds the deviations any further: Table C.1 of each 2020 edition prints
    them in the tenths the measurement was already reduced to (Clause 4.4
    footnote 1) and adds those tenths straight up, reaching 31,8 dB and
    28,0 dB against bounds of 32,0 dB.

    A fiche prints the contradiction twice on one page. Its verbose Annex C
    table recomputes the deviation column from the two curves and closes it
    with a sum row, while the plot beside it titles itself from this field:
    a rating whose ``measured`` was swapped through
    :func:`dataclasses.replace` keeps the aggregate the old curve earned,
    and the page then reads a sum row of 0,0 dB under a column of em dashes
    next to a title claiming 31,8 dB.

    The em dash there is Table C.1's own mark for a band with no
    unfavourable deviation, not for one left undetermined: both curves are
    finite by the time this runs (:func:`_require_finite_curves` goes
    first), so the sum is always determined. A rating built from the single
    numbers alone carries no curves and is skipped.

    :param owner: The rating whose ``unfavourable_sum`` is checked.
    :param impact: ``True`` for the ISO 717-2 sign (measurement above the
        reference), ``False`` for the ISO 717-1 one.
    :raises ValueError: if ``unfavourable_sum`` is not the sum its own
        ``measured`` and ``shifted_reference`` state.
    """
    measured = owner.measured
    shifted = owner.shifted_reference
    if measured is None or shifted is None:
        return
    excess = np.asarray(measured, dtype=np.float64) - np.asarray(
        shifted, dtype=np.float64
    )
    expected = float(np.sum(np.maximum(excess if impact else -excess, 0.0)))
    if not math.isclose(
        owner.unfavourable_sum, expected, rel_tol=0.0, abs_tol=_SUM_TOLERANCE
    ):
        sense = (
            "'measured' above 'shifted_reference' (ISO 717-2 Clause 4.3)"
            if impact
            else "'measured' below 'shifted_reference' (ISO 717-1 Clause 4.4)"
        )
        msg = (
            f"{type(owner).__name__}: 'unfavourable_sum' must be the sum of "
            f"the unfavourable deviations of its own curves, {sense}; got "
            f"{owner.unfavourable_sum!r} where the curves sum to {expected!r}."
        )
        raise ValueError(msg)


@dataclass(frozen=True)
class WeightedRatingResult:
    """Single-number weighted rating and adaptation terms (ISO 717-1).

    :ivar rating: Weighted rating (``Rw``, ``R'w``, ``DnT,w`` ...), the
        shifted reference read at 500 Hz, in dB (Clause 4.4). Integer.
    :ivar c: Spectrum adaptation term ``C`` (spectrum No. 1), in dB
        (Clause 4.5). Integer.
    :ivar ctr: Spectrum adaptation term ``Ctr`` (spectrum No. 2), in dB
        (Clause 4.5). Integer.
    :ivar unfavourable_sum: Sum of unfavourable deviations at the final
        shift, in dB (Clause 4.4); at most 32,0 (16 bands) or 10,0 (5
        bands). Restates ``measured`` against ``shifted_reference`` and is
        checked against them when both are present.
    :ivar band_centers: Band centre frequencies of the measured curve, in
        Hz. Defaults to ``None`` for backward-compatible construction.
    :ivar measured: The measured band quantities used for the rating (after
        the one-decimal reduction of Clause 4.4), in dB. Defaults to
        ``None``.
    :ivar shifted_reference: Table 3 reference curve after the final shift,
        in dB. Defaults to ``None``.
    :ivar quantity: Always ``"airborne"``: this class carries the ISO 717-1
        airborne rating, and the renderers dispatch on this tag when handed
        the union with :class:`ImpactRatingResult`, which carries
        ``"impact"``. The field used to admit both values and promise that
        ``"impact"`` would select the impact labels; it never could, since
        the impact labels read ``ci`` off the result and this class does not
        have one, so the promise ended in the renderer's ``AttributeError``.
    """

    rating: int
    c: int
    ctr: int
    unfavourable_sum: float
    band_centers: np.ndarray | None = None
    measured: np.ndarray | None = None
    shifted_reference: np.ndarray | None = None
    quantity: Literal["airborne"] = "airborne"

    def __post_init__(self) -> None:
        """Reject a rating whose three band curves do not line up.

        The three arrays are the record of which bands the single number was
        rated over, and a fiche reads them as exactly that: ISO 717-1
        Clause 5.3 makes it declare whether the rating came from
        one-third-octave or octave bands, and it settles that from the length
        of ``band_centers`` alone. The renderers do compare the three, but
        only once a report is asked for, which can be long after the rating
        was built and passed on; :meth:`plot` compares nothing and hands the
        curves to matplotlib, whose complaint about first dimensions names
        neither the field nor the type it came from.

        The three arrays default to ``None`` on a rating built from the
        single numbers alone, and an absent curve is skipped rather than read
        as a disagreement.

        The curves must also be finite. No constructor can emit a non-finite
        band -- :func:`weighted_rating` refuses non-finite input, the centres
        come from the Table 1 band sets and the shifted reference is the
        Table 3 curve plus an integer shift -- and the fiche reads them raw:
        a NaN centre dies in a bare ``ValueError: cannot convert float NaN to
        integer`` from ``round`` inside the band table, while a NaN measured
        value prints a literal ``nan`` cell and, in the verbose Annex C
        table, an em dash in the deviation column whose defined meaning is
        "deviation below 0,05 dB" -- asserting no unfavourable deviation for
        a band that was never determined.

        Last, ``unfavourable_sum`` must be the sum those same two curves
        state, for the reasons set out on :func:`_require_unfavourable_sum`.

        :raises ValueError: if the band curves supplied disagree, one of them
            carries a non-finite value, or ``unfavourable_sum`` is not their
            own sum of unfavourable deviations.
        """
        require_ranks(self, band_centers=1, measured=1, shifted_reference=1)
        require_same_length(self, "band_centers", "measured", "shifted_reference")
        _require_finite_curves(self, "band_centers", "measured", "shifted_reference")
        _require_unfavourable_sum(self, impact=False)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the measured curve vs the shifted reference (ISO 717-1).

        Unfavourable deviations (reference above measurement) are shaded and
        ``Rw (C; Ctr)`` annotated. Requires matplotlib
        (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_weighted_rating

        check_language(language)
        return plot_weighted_rating(self, ax=ax, language=language, **kwargs)

    def report(
        self,
        path: str,
        *,
        metadata: ReportMetadata | None = None,
        engine: str = "reportlab",
        verbose: bool = False,
        language: str = "en",
        symbol: str | None = None,
    ) -> str:
        """Render an ISO 717-1 airborne sound-insulation fiche to a PDF.

        Writes a one-page accredited-laboratory report: the standard-basis
        line, an optional metadata header block, the band table beside the
        measured-versus-shifted-reference plot (the result's own
        :meth:`plot`), the boxed ``Rw (C; Ctr)`` result, an optional verdict
        row and a footer with the fixed disclaimer.

        :param path: Destination path of the PDF file.
        :param metadata: Optional
            :class:`~phonometry.ReportMetadata`; ``None`` produces a
            prediction fiche (body, result and disclaimer only).
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: When ``True``, the table uses the ISO 717 Annex C
            columns (frequency, measured value, shifted reference,
            unfavourable deviation) instead of the two-column ``f | value``
            table.
        :param language: Fiche language: ``"en"`` (default, English) or
            ``"es"`` (Spanish, with a comma decimal separator).
        :param symbol: The reported single-number quantity, as plain text:
            ``"Rw"`` (the default when ``None``), ``"R'w"``, ``"Dn,w"``,
            ``"DnT,w"`` ... per ISO 717-1 Tables 1-2, so a field measurement
            (e.g. a standardized level difference rated to ``DnT,w``) is not
            mislabelled with the laboratory descriptor.
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` is not ``"reportlab"``, ``symbol``
            is not a valid quantity-symbol shape, or the result was built
            without the per-band data (``band_centers``, ``measured``,
            ``shifted_reference``).
        :raises ImportError: If reportlab is not installed
            (``pip install phonometry[report]``), or matplotlib is missing for
            the embedded figure (``pip install phonometry[plot]``).
        """
        return _render_iso717(
            self,
            path,
            metadata=metadata,
            engine=engine,
            verbose=verbose,
            language=language,
            symbol=symbol,
        )


@dataclass(frozen=True)
class ImpactRatingResult:
    """Single-number weighted impact rating and CI (ISO 717-2).

    :ivar rating: Weighted impact rating (``Ln,w``, ``L'n,w``,
        ``L'nT,w``), the shifted reference read at 500 Hz, in dB
        (Clause 4.3; octave-band ratings include the -5 dB reduction of
        Clause 4.3.2). Integer.
    :ivar ci: Spectrum adaptation term ``CI`` (Clause A.2.1), in dB.
        Integer.
    :ivar unfavourable_sum: Sum of unfavourable deviations at the final
        shift, in dB (Clause 4.3); at most 32,0 (16 bands) or 10,0 (5
        bands). Restates ``measured`` against ``shifted_reference``, with the
        impact sign, and is checked against them when both are present.
    :ivar band_centers: Band centre frequencies of the measured curve, in
        Hz. Defaults to ``None`` for backward-compatible construction.
    :ivar measured: The measured impact levels used for the rating (after
        the one-decimal reduction of Clause 4.3.1), in dB. Defaults to
        ``None``.
    :ivar shifted_reference: Table 3 impact reference curve after the final
        shift, in dB. Defaults to ``None``.
    :ivar quantity: Always ``"impact"`` (ISO 717-2), selecting the impact
        labels of the ISO 717 Annex C report.
    """

    rating: int
    ci: int
    unfavourable_sum: float
    band_centers: np.ndarray | None = None
    measured: np.ndarray | None = None
    shifted_reference: np.ndarray | None = None
    quantity: Literal["impact"] = "impact"

    def __post_init__(self) -> None:
        """Reject a rating whose three band curves do not line up.

        Shading the bands where the measurement rises *above* the shifted
        reference -- the sign opposite to airborne -- is a comparison of one
        curve against the other, band for band, and :meth:`plot` makes it
        without first asking whether the two run over the same bands. The
        band centres carry as much: ISO 717-2 Clause 4.4 makes the fiche
        declare whether the rating came from one-third-octave or octave
        bands, and their length alone settles it. The renderers refuse a
        mismatch, but not until a report is asked for, and a rating is
        usually built long before that.

        The three arrays default to ``None`` on a rating built from the
        single numbers alone, and an absent curve is skipped rather than read
        as a disagreement.

        The curves must also be finite, for the reasons given on
        :class:`WeightedRatingResult` (no constructor can emit a non-finite
        band; the fiche prints them raw or crashes namelessly on them).

        Last, ``unfavourable_sum`` must be the sum those same two curves
        state, taken with the impact sign of Clause 4.3; see
        :func:`_require_unfavourable_sum`.

        :raises ValueError: if the band curves supplied disagree, one of them
            carries a non-finite value, or ``unfavourable_sum`` is not their
            own sum of unfavourable deviations.
        """
        require_ranks(self, band_centers=1, measured=1, shifted_reference=1)
        require_same_length(self, "band_centers", "measured", "shifted_reference")
        _require_finite_curves(self, "band_centers", "measured", "shifted_reference")
        _require_unfavourable_sum(self, impact=True)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the measured curve vs the shifted reference (ISO 717-2).

        Unfavourable deviations (measurement above the reference, the sign
        opposite to airborne) are shaded and ``Ln,w (CI)`` annotated.
        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_impact_rating

        check_language(language)
        return plot_impact_rating(self, ax=ax, language=language, **kwargs)

    def report(
        self,
        path: str,
        *,
        metadata: ReportMetadata | None = None,
        engine: str = "reportlab",
        verbose: bool = False,
        language: str = "en",
        symbol: str | None = None,
    ) -> str:
        """Render an ISO 717-2 impact-insulation fiche to a PDF.

        Writes a one-page accredited-laboratory report for impact sound: the
        standard-basis line, an optional metadata header block, the band
        table beside the measured-versus-shifted-reference plot (the
        result's own :meth:`plot`), the boxed ``Ln,w (CI)`` result, an
        optional verdict row and a footer with the fixed disclaimer.

        :param path: Destination path of the PDF file.
        :param metadata: Optional
            :class:`~phonometry.ReportMetadata`; ``None`` produces a
            prediction fiche (body, result and disclaimer only).
        :param engine: Rendering back end; only ``"reportlab"`` is supported.
        :param verbose: When ``True``, the table uses the ISO 717 Annex C
            columns (frequency, measured value, shifted reference,
            unfavourable deviation) instead of the two-column ``f | value``
            table.
        :param language: Fiche language: ``"en"`` (default, English) or
            ``"es"`` (Spanish, with a comma decimal separator).
        :param symbol: The reported single-number quantity, as plain text:
            ``"Ln,w"`` (the default when ``None``), ``"L'n,w"`` or
            ``"L'nT,w"`` per ISO 717-2 Table 1, so a field measurement is not
            mislabelled with the laboratory descriptor.
        :return: The written ``path`` as a :class:`str`.
        :raises ValueError: If ``engine`` is not ``"reportlab"``, ``symbol``
            is not a valid quantity-symbol shape, or the result was built
            without the per-band data (``band_centers``, ``measured``,
            ``shifted_reference``).
        :raises ImportError: If reportlab is not installed
            (``pip install phonometry[report]``), or matplotlib is missing for
            the embedded figure (``pip install phonometry[plot]``).
        """
        return _render_iso717(
            self,
            path,
            metadata=metadata,
            engine=engine,
            verbose=verbose,
            language=language,
            symbol=symbol,
        )


def _render_iso717(
    result: WeightedRatingResult | ImpactRatingResult,
    path: str,
    *,
    metadata: ReportMetadata | None,
    engine: str,
    verbose: bool,
    language: str,
    symbol: str | None = None,
) -> str:
    """Validate the report request and delegate to the reportlab renderer.

    Shared by :meth:`WeightedRatingResult.report` and
    :meth:`ImpactRatingResult.report`: it rejects unknown engines and results
    built without the per-band data, then calls the reportlab renderer (which
    raises a clear :class:`ImportError` when reportlab is absent).
    """
    from ..._i18n import check_language

    check_language(language)
    check_engine(engine)
    if (
        result.band_centers is None
        or result.measured is None
        or result.shifted_reference is None
    ):
        msg = (
            "report() needs the per-band data ('band_centers', 'measured', "
            "'shifted_reference'); build the rating with weighted_rating() or "
            "weighted_impact_rating() so they are populated."
        )
        raise ValueError(msg)
    from ..._report.iso717 import render_iso717_report

    return render_iso717_report(
        result,
        path,
        metadata=metadata,
        verbose=verbose,
        language=language,
        symbol=symbol,
    )


def _round_half_up_tenths(values: np.ndarray) -> np.ndarray:
    r"""Reduce levels to one decimal place (ISO 717-1 Clause 4.4, note 1).

    Rounds each value to the nearest tenth of a decibel, half away from
    zero (:math:`\lfloor x \cdot 10 + 0.5 \rfloor / 10` for non-negative
    values, mirrored for
    negative ones).

    .. note::
        This rounds negative halves *away from zero* (−0.05 → −0.1), which is
        Rule B of ISO 80000-1:2009 Annex B, whereas the adaptation-term
        reductions (:func:`_adaptation_term`, :func:`_impact_ci`) use the plain
        :math:`\lfloor x + 0.5 \rfloor`, which rounds them *towards* +∞
        (−0.5 → 0) and so follows neither printed rule there. The two
        conventions differ only for exactly-half negative values, which do
        not occur with realistic (positive-level) insulation data; the
        difference is documented here rather than unified so each function
        keeps the literal form of its clause.

    The scaled value is settled before the half is judged, so a level that is
    a half in decimal and a last bit under it in binary still rounds outwards.
    """
    return round_half_away_from_zero(values, 1)


def _resolve_band_set(
    n: int, bands: str | None
) -> tuple[tuple[int, ...], float, int, tuple[int, ...], tuple[int, ...]]:
    """Select the reference curve, bound and spectra for the band set.

    :return: ``(reference, max_unfavourable, index_500, spectrum1,
        spectrum2)``.
    """
    if bands == "third-octave" or (bands is None and n == _N_THIRD_OCTAVE_BANDS):
        if n != _N_THIRD_OCTAVE_BANDS:
            msg = f"One-third-octave rating needs 16 bands (100-3150 Hz), got {n}."
            raise ValueError(msg)
        return (
            _REF_THIRD_OCTAVE,
            _MAX_UNFAVOURABLE_THIRD,
            _INDEX_500_THIRD,
            _SPECTRUM1_THIRD,
            _SPECTRUM2_THIRD,
        )
    if bands == "octave" or (bands is None and n == _N_OCTAVE_BANDS):
        if n != _N_OCTAVE_BANDS:
            msg = f"Octave rating needs 5 bands (125-2000 Hz), got {n}."
            raise ValueError(msg)
        return (
            _REF_OCTAVE,
            _MAX_UNFAVOURABLE_OCTAVE,
            _INDEX_500_OCTAVE,
            _SPECTRUM1_OCTAVE,
            _SPECTRUM2_OCTAVE,
        )
    if bands is not None:
        msg = _BANDS_REFUSAL
        raise ValueError(msg)
    msg = (
        "Expected 16 one-third-octave (100-3150 Hz) or 5 octave "
        f"(125-2000 Hz) values, got {n}."
    )
    raise ValueError(msg)


def _best_shift(
    measured: np.ndarray,
    reference: np.ndarray,
    limit: float,
    step: float = 1.0,
) -> tuple[float, float]:
    r"""Largest ``step``-sized shift with unfavourable-deviation sum bounded.

    Shifts the reference by multiples of ``step`` and returns the largest
    shift for which
    :math:`\sum \max(0, \mathrm{reference} + \mathrm{shift}
    - \mathrm{measured}) \le \mathrm{limit}`
    (the sum is monotone non-decreasing in the shift), together with that
    sum. ``step`` is 1 dB for the standard rating (ISO 717-1 Clause 4.4 /
    ISO 717-2 Clause 4.3) or 0,1 dB for the one-decimal rating used in
    uncertainty statements (ISO 717 "1/10 dB for the expression of
    uncertainty"; ISO 12999-1:2020 Annex B.2 requires the 0,1 dB steps).

    Measured levels are multiples of 0,1 dB (Clause 4.4 footnote 1) and the
    reference is integer, so with both step sizes every deviation sum is a
    true multiple of 0,1 dB; a small tolerance absorbs floating-point noise
    so that a sum of exactly 32,0 (or 10,0) dB is not spuriously rejected.
    The shift is searched on an integer grid of ``step`` ticks to keep the
    0,1 dB steps exact.
    """
    scale = round(1.0 / step)
    if scale < 1 or abs(scale * step - 1.0) > _STEP_DIVISOR_TOLERANCE:
        msg = "'step' must divide 1 dB exactly (e.g. 1.0 or 0.1)."
        raise ValueError(msg)
    # Start below any feasible shift, then climb while the bound holds.
    n = (int(np.floor(np.min(measured - reference))) - 1) * scale
    while True:
        candidate = (n + 1) / scale
        next_sum = float(np.sum(np.maximum(0.0, reference + candidate - measured)))
        if next_sum > limit + _SHIFT_TOLERANCE:
            break
        n += 1
    shift = n / scale
    unfavourable = float(np.sum(np.maximum(0.0, reference + shift - measured)))
    return shift, unfavourable


def _adaptation_term(
    measured: np.ndarray, spectrum: tuple[int, ...], rating: int
) -> int:
    """Spectrum adaptation term ``Xaj - rating`` (Clause 4.5, Formula (2))."""
    x_aj = -energy_sum(np.asarray(spectrum, dtype=np.float64) - measured)
    return math.floor(x_aj + 0.5) - rating


def weighted_rating(
    values_by_band: Mapping[float, float] | Sequence[float] | np.ndarray,
    bands: str | None = None,
) -> WeightedRatingResult:
    """Single-number weighted rating and C / Ctr per ISO 717-1.

    Applies the reference-curve method of Clause 4.4: the Table 3
    reference curve is shifted in 1 dB steps towards the measured curve
    until the sum of unfavourable deviations is as large as possible but
    not more than 32,0 dB (16 one-third-octave bands, 100 Hz to 3150 Hz)
    or 10,0 dB (5 octave bands, 125 Hz to 2000 Hz). The rating is the
    shifted reference read at 500 Hz. The spectrum adaptation terms
    ``C`` and ``Ctr`` follow Clause 4.5 with the Table 4 spectra No. 1 and
    No. 2. Input values are first reduced to one decimal place
    (Clause 4.4, footnote 1).

    :param values_by_band: Measured band quantities (``R``, ``R'``,
        ``Dn``, ``DnT`` ...) in dB. 16 values are read as one-third-octave
        bands, 5 values as octave bands. A mapping of band centre frequency
        in hertz to value, such as a catalogue row's
        :meth:`~phonometry.io.BandedRow.spectrum`, is read band by band:
        one that holds any one-third-octave band that is not an octave
        centre as the 16 one-third octaves, any other as the 5 octaves, and
        a rating band it lacks is refused rather than filled.
    :param bands: ``"third-octave"``, ``"octave"`` or ``None`` to infer
        the band set from the number of values or the keys of the mapping.
    :return: :class:`WeightedRatingResult` with ``rating``, ``c``,
        ``ctr`` and ``unfavourable_sum``.
    :raises ValueError: If the number of values does not match the band
        set, if a mapping lacks a band of it, or if any value is
        non-finite.
    """
    data, bands = _by_band(values_by_band, bands, "values_by_band")
    if data.ndim != 1:
        raise ValueError(_VALUES_1D_MSG)
    if not np.all(np.isfinite(data)):
        raise ValueError(_VALUES_FINITE_MSG)

    reference, limit, index_500, spectrum1, spectrum2 = _resolve_band_set(
        int(data.size), bands
    )
    measured = _round_half_up_tenths(data)
    ref = np.asarray(reference, dtype=np.float64)

    shift, unfavourable = _best_shift(measured, ref, limit)
    rating = int(reference[index_500]) + round(shift)
    c = _adaptation_term(measured, spectrum1, rating)
    ctr = _adaptation_term(measured, spectrum2, rating)
    centers = _FREQ_THIRD_OCTAVE if data.size == _N_THIRD_OCTAVE_BANDS else _FREQ_OCTAVE
    return WeightedRatingResult(
        rating=rating,
        c=c,
        ctr=ctr,
        unfavourable_sum=unfavourable,
        band_centers=np.asarray(centers, dtype=np.float64),
        measured=measured,
        shifted_reference=ref + shift,
    )


def _resolve_impact_band_set(
    n: int, bands: str | None
) -> tuple[tuple[int, ...], float, int, int, int]:
    """Select the impact reference curve, bound, indices for the band set.

    :return: ``(reference, max_unfavourable, index_500, octave_offset,
        ci_band_count)``.
    """
    if bands == "third-octave" or (bands is None and n == _N_THIRD_OCTAVE_BANDS):
        if n != _N_THIRD_OCTAVE_BANDS:
            msg = (
                f"One-third-octave impact rating needs 16 bands (100-3150 Hz), got {n}."
            )
            raise ValueError(msg)
        return (
            _REF_IMPACT_THIRD_OCTAVE,
            _MAX_UNFAVOURABLE_THIRD,
            _INDEX_500_THIRD,
            0,
            _CI_THIRD_OCTAVE_BANDS,
        )
    if bands == "octave" or (bands is None and n == _N_OCTAVE_BANDS):
        if n != _N_OCTAVE_BANDS:
            msg = f"Octave impact rating needs 5 bands (125-2000 Hz), got {n}."
            raise ValueError(msg)
        return (
            _REF_IMPACT_OCTAVE,
            _MAX_UNFAVOURABLE_OCTAVE,
            _INDEX_500_OCTAVE,
            _IMPACT_OCTAVE_OFFSET,
            5,
        )
    if bands is not None:
        msg = _BANDS_REFUSAL
        raise ValueError(msg)
    msg = (
        "Expected 16 one-third-octave (100-3150 Hz) or 5 octave "
        f"(125-2000 Hz) values, got {n}."
    )
    raise ValueError(msg)


def _impact_ci(measured: np.ndarray, rating: int, n_bands: int) -> int:
    r"""Spectrum adaptation term ``CI`` (ISO 717-2 Clause A.2.1).

    :math:`C_\mathrm{I} = L_\mathrm{n,sum} - 15 - L_\mathrm{n,w}` with the energetic sum
    :math:`L_\mathrm{n,sum} = 10 \log_{10} \sum
    10^{L_i/10}` over the CI range (one-third octave 100-2500 Hz, i.e.
    the first 15 bands; octave 125-2000 Hz), rounded to an integer
    (round half up), Formulae (A.1) to (A.3).
    """
    l_sum = energy_sum(measured[:n_bands])
    return math.floor(l_sum + 0.5) - 15 - rating


def weighted_impact_rating(
    values_by_band: Mapping[float, float] | Sequence[float] | np.ndarray,
    bands: str | None = None,
) -> ImpactRatingResult:
    r"""Single-number weighted impact rating and CI per ISO 717-2.

    Applies the reference-curve method of Clause 4.3: the Table 3 impact
    reference curve is shifted in 1 dB steps towards the measured curve
    until the sum of unfavourable deviations is as large as possible but
    not more than 32,0 dB (16 one-third-octave bands, 100 Hz to 3150 Hz)
    or 10,0 dB (5 octave bands, 125 Hz to 2000 Hz). For impact sound an
    unfavourable deviation occurs where the **measurement exceeds** the
    reference (the sign opposite to ISO 717-1 airborne). The rating is the
    shifted reference read at 500 Hz; for octave bands it is then reduced
    by 5 dB (Clause 4.3.2). The spectrum adaptation term ``CI`` follows
    Clause A.2.1. Input values are first reduced to one decimal place
    (Clause 4.3.1, footnote 1).

    The shift search reuses the verified engine of :func:`weighted_rating`
    on the negated curves: minimising
    :math:`\sum \max(0, \text{measured} - (\text{ref} + k))` over ``k``
    equals maximising
    :math:`\sum \max(0, (-\text{ref}) + (-k) - (-\text{measured}))`, the
    airborne problem, so no separate search is duplicated.

    :param values_by_band: Measured impact levels (``Ln``, ``L'n``,
        ``L'nT``) in dB. 16 values are read as one-third-octave bands, 5
        values as octave bands. A mapping of band centre frequency in hertz
        to level is read band by band, as :func:`weighted_rating` reads
        one, and a rating band it lacks is refused rather than filled.
    :param bands: ``"third-octave"``, ``"octave"`` or ``None`` to infer
        the band set from the number of values or the keys of the mapping.
    :return: :class:`ImpactRatingResult` with ``rating``, ``ci`` and
        ``unfavourable_sum``.
    :raises ValueError: If the number of values does not match the band
        set, if a mapping lacks a band of it, or if any value is
        non-finite.
    """
    data, bands = _by_band(values_by_band, bands, "values_by_band")
    if data.ndim != 1:
        raise ValueError(_VALUES_1D_MSG)
    if not np.all(np.isfinite(data)):
        raise ValueError(_VALUES_FINITE_MSG)

    reference, limit, index_500, octave_offset, ci_bands = _resolve_impact_band_set(
        int(data.size), bands
    )
    measured = _round_half_up_tenths(data)
    ref = np.asarray(reference, dtype=np.float64)

    # Impact shift is the airborne search on the negated curves: the
    # returned shift m maximises Σ max(0, (-ref)+m-(-meas)); the impact
    # shift is k = -m, so the rating is ref_500 - m. The unfavourable sum
    # is identical under negation.
    shift, unfavourable = _best_shift(-measured, -ref, limit)
    rating = int(reference[index_500]) - round(shift) + octave_offset
    ci = _impact_ci(measured, rating, ci_bands)
    centers = _FREQ_THIRD_OCTAVE if data.size == _N_THIRD_OCTAVE_BANDS else _FREQ_OCTAVE
    return ImpactRatingResult(
        rating=rating,
        ci=ci,
        unfavourable_sum=unfavourable,
        band_centers=np.asarray(centers, dtype=np.float64),
        measured=measured,
        shifted_reference=ref - shift,
    )


@dataclass(frozen=True)
class ImpactImprovementRatingResult:
    r"""The weighted reduction of impact level of a covering, with its terms.

    ISO 717-2:2020 rates the reduction of impact sound pressure level
    :math:`\Delta L` of a floor covering against the heavyweight reference
    floor of its Table 4: :math:`\Delta L_\mathrm{w}` from Formulae (1) and
    (2), and the adaptation terms of Clause A.2.2, where
    :math:`C_{\mathrm{I},\Delta} = C_\mathrm{I,r,0} - C_\mathrm{I,r}`
    (Formula (A.4)) with :math:`C_\mathrm{I,r,0} = -11` dB. A data sheet of a
    covering or a resilient layer prints :math:`\Delta L_\mathrm{w}` and
    one of the two terms, so both are here.

    :ivar delta_lw: The weighted reduction of impact sound pressure level
        :math:`\Delta L_\mathrm{w}`, in dB, from
        :func:`weighted_impact_improvement`. Integer.
    :ivar ci_delta: The spectrum adaptation term
        :math:`C_{\mathrm{I},\Delta}`, in dB, from
        :func:`impact_improvement_adaptation_term`. Integer.
    :ivar ci_r: The spectrum adaptation term :math:`C_\mathrm{I,r}` of the
        reference floor with the covering, in dB, which is
        :math:`C_\mathrm{I,r,0} - C_{\mathrm{I},\Delta}`. Integer.
    :ivar band_centers: The 16 one-third-octave centre frequencies rated,
        100 Hz to 3150 Hz.
    :ivar improvement: :math:`\Delta L` in those bands, in dB, as given.
    """

    delta_lw: int
    ci_delta: int
    ci_r: int
    band_centers: np.ndarray
    improvement: np.ndarray

    def __post_init__(self) -> None:
        r"""Reject a rating whose terms or curves do not agree.

        :raises ValueError: if the band centres and the improvement differ in
            length or hold a value that is not finite, or if ``ci_r`` is not
            :math:`C_\mathrm{I,r,0} - C_{\mathrm{I},\Delta}`.
        """
        require_ranks(self, band_centers=1, improvement=1)
        require_same_length(self, "band_centers", "improvement")
        _require_finite_curves(self, "band_centers", "improvement")
        if self.ci_r != _IMPACT_REFERENCE_FLOOR_CI - self.ci_delta:
            msg = (
                f"{type(self).__name__}: 'ci_r' must be CI,r,0 - CI,Delta = "
                f"{_IMPACT_REFERENCE_FLOOR_CI} - ({self.ci_delta}) dB (ISO 717-2:2020 "
                f"Formula (A.4)); got {self.ci_r!r}."
            )
            raise ValueError(msg)

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the improvement spectrum with its rating (ISO 717-2).

        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_impact_improvement_rating

        check_language(language)
        return plot_impact_improvement_rating(self, ax=ax, language=language, **kwargs)


def _impact_improvement_rating(
    delta_l: Mapping[float, float] | Sequence[float] | np.ndarray,
) -> ImpactImprovementRatingResult:
    """``ΔLw``, ``CI,Δ`` and ``CI,r`` of one improvement spectrum."""
    dl, _ = _by_band(delta_l, "third-octave", "delta_l")
    ci_delta = impact_improvement_adaptation_term(dl)
    return ImpactImprovementRatingResult(
        delta_lw=weighted_impact_improvement(dl),
        ci_delta=ci_delta,
        ci_r=_IMPACT_REFERENCE_FLOOR_CI - ci_delta,
        band_centers=np.asarray(_FREQ_THIRD_OCTAVE, dtype=np.float64),
        improvement=np.array(dl, dtype=np.float64),
    )


# --- ISO 717 enlarged frequency ranges and one-decimal ratings ------------


@dataclass(frozen=True)
class ExtendedWeightedRatingResult:
    """Weighted rating with the enlarged-range adaptation terms (ISO 717-1 Annex B).

    All values are integers unless the result was computed with
    ``one_decimal=True`` (the "1/10 dB for the expression of uncertainty"
    variant of Clauses 4.4/4.5), in which case they carry one decimal place.
    An extended term is ``None`` when the supplied bands do not cover its
    frequency range.

    :ivar rating: Weighted rating (``Rw``, ``R'w``, ...) from the core
        100-3150 Hz bands, in dB.
    :ivar c: Core spectrum adaptation term ``C`` (100-3150 Hz), in dB.
    :ivar ctr: Core spectrum adaptation term ``Ctr`` (100-3150 Hz), in dB.
    :ivar c_50_3150: ``C50-3150``, in dB, or ``None``.
    :ivar c_50_5000: ``C50-5000``, in dB, or ``None``.
    :ivar c_100_5000: ``C100-5000``, in dB, or ``None``.
    :ivar ctr_50_3150: ``Ctr,50-3150``, in dB, or ``None``.
    :ivar ctr_50_5000: ``Ctr,50-5000``, in dB, or ``None``.
    :ivar ctr_100_5000: ``Ctr,100-5000``, in dB, or ``None``.
    :ivar core: The integer-mode :class:`WeightedRatingResult` of the core
        bands (independent of ``one_decimal``), for plotting and the
        unfavourable-deviation sum.
    :ivar band_centers: Band centre frequencies of the full (enlarged-range)
        measured curve, in Hz. Defaults to ``None`` for
        backward-compatible construction.
    :ivar measured: The measured band quantities over the full enlarged
        range (after the one-decimal reduction of Clause 4.4), in dB.
        Defaults to ``None``.
    """

    rating: float
    c: float
    ctr: float
    c_50_3150: float | None
    c_50_5000: float | None
    c_100_5000: float | None
    ctr_50_3150: float | None
    ctr_50_5000: float | None
    ctr_100_5000: float | None
    core: WeightedRatingResult
    band_centers: np.ndarray | None = None
    measured: np.ndarray | None = None

    def __post_init__(self) -> None:
        """Reject an enlarged-range rating whose curve and bands disagree.

        The Annex B plot shades from the ends of ``band_centers`` in to the
        ends of the core 100-3150 Hz axis, to mark which part of the curve is
        the enlarged range, and only afterwards draws ``measured`` against
        those same centres. The shading is therefore laid down before
        anything has compared the two lengths: centres that are not this
        curve's own axis put the enlarged-range mark where the curve does not
        reach, and what the caller is finally handed is matplotlib
        complaining about first dimensions.

        ``core`` is not compared here: it carries the 16 core bands whatever
        the enlarged range is, and checks its own three curves.

        :raises ValueError: if ``band_centers`` and ``measured`` disagree.
        """
        require_ranks(self, band_centers=1, measured=1)
        require_same_length(self, "band_centers", "measured")

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the enlarged-range curve vs the shifted reference (Annex B).

        The measured curve is drawn over the full enlarged range, the
        ISO 717-1 reference curve (after the final shift) over the 16 core
        bands 100-3150 Hz, with the unfavourable deviations shaded on the
        core bands and the bands outside the core range marked as the
        enlarged range; the title carries ``Rw (C; Ctr)`` and every Annex B
        adaptation term the input covered. Requires matplotlib
        (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_extended_weighted_rating

        check_language(language)
        return plot_extended_weighted_rating(self, ax=ax, language=language, **kwargs)


@dataclass(frozen=True)
class ExtendedImpactRatingResult:
    """Weighted impact rating with ``CI,50-2500`` (ISO 717-2:2020 A.2.1 NOTE).

    Values are integers unless computed with ``one_decimal=True``.

    :ivar rating: Weighted impact rating (``Ln,w``, ...) from the core
        100-3150 Hz bands, in dB.
    :ivar ci: Core spectrum adaptation term ``CI`` (100-2500 Hz), in dB.
    :ivar ci_50_2500: Enlarged-range term ``CI,50-2500``, in dB, or ``None``
        when the supplied bands do not cover 50-2500 Hz.
    :ivar core: The integer-mode :class:`ImpactRatingResult` of the core
        bands (independent of ``one_decimal``).
    :ivar band_centers: Band centre frequencies of the full (enlarged-range)
        measured curve, in Hz. Defaults to ``None`` for
        backward-compatible construction.
    :ivar measured: The measured impact levels over the full enlarged range
        (after the one-decimal reduction of Clause 4.3), in dB. Defaults to
        ``None``.
    """

    rating: float
    ci: float
    ci_50_2500: float | None
    core: ImpactRatingResult
    band_centers: np.ndarray | None = None
    measured: np.ndarray | None = None

    def __post_init__(self) -> None:
        """Reject an enlarged-range rating whose curve and bands disagree.

        The band centres are the record of which bands ``CI,50-2500`` was
        summed over, and the plot reads them a second time to mark which part
        of ``measured`` lies outside the core 100-3150 Hz set -- shading that
        span from the ends of the centres before it has looked at the curve
        at all. Centres that are not this curve's own axis therefore mis-mark
        the enlarged range first and fail second, in matplotlib's words
        rather than the library's.

        ``core`` is not compared here: it carries the 16 core bands whatever
        the enlarged range is, and checks its own three curves.

        :raises ValueError: if ``band_centers`` and ``measured`` disagree.
        """
        require_ranks(self, band_centers=1, measured=1)
        require_same_length(self, "band_centers", "measured")

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot the enlarged-range curve vs the shifted reference (ISO 717-2).

        The measured curve is drawn over the full enlarged range, the
        ISO 717-2 reference curve (after the final shift) over the 16 core
        bands 100-3150 Hz, with the unfavourable deviations (measurement
        above the reference) shaded on the core bands and the bands outside
        the core range marked as the enlarged range; the title carries the
        impact rating with ``CI`` and, when covered, ``CI,50-2500``.
        Requires matplotlib (``pip install phonometry[plot]``); returns the
        :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_extended_impact_rating

        check_language(language)
        return plot_extended_impact_rating(self, ax=ax, language=language, **kwargs)


def _reduce(value: float, *, one_decimal: bool) -> float:
    r"""Round half-up to an integer, or to one decimal.

    Half-up is Rule B of ISO 80000-1:2009 Annex B (normative), B.3, printed
    folio 36: of two equally near multiples, the greater in magnitude is the
    rounded number. :math:`\lfloor x + 0.5 \rfloor` is that rule only for a
    non-negative ``value``; it rounds a negative half towards positive infinity
    instead, where Rule B prints -12,25 as -12,3. The ratings this serves are
    levels and differences of levels that are positive in practice, so the two
    never part company here.
    """
    return float(round_half_up(value, 1 if one_decimal else 0))


def _match_bands(
    frequencies: np.ndarray, targets: tuple[float, ...]
) -> np.ndarray | None:
    """Indices of ``targets`` within ``frequencies`` (6 % tolerance), or None."""
    indices: list[int] = []
    for target in targets:
        hits = np.nonzero(np.abs(frequencies - target) <= 0.06 * target)[0]
        if hits.size != 1:
            return None
        indices.append(int(hits[0]))
    return np.asarray(indices, dtype=np.intp)


def _validated_extended_input(
    owner: str,
    values_by_band: Sequence[float] | np.ndarray,
    frequencies: Sequence[float] | np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Validate the extended-range input; return (measured, freqs, core_idx).

    *owner* is the entry point the caller typed, so that the message about
    the two spectra names it rather than this validator, which two entry
    points share.
    """
    data = np.asarray(values_by_band, dtype=np.float64)
    if data.ndim != 1:
        raise ValueError(_VALUES_1D_MSG)
    if not np.all(np.isfinite(data)):
        raise ValueError(_VALUES_FINITE_MSG)
    if frequencies is None:
        if data.size != len(_FREQ_THIRD_OCTAVE):
            msg = (
                "Without 'frequencies' the input must be the 16 core "
                "one-third-octave bands 100-3150 Hz; pass the band centre "
                "frequencies for an enlarged range."
            )
            raise ValueError(msg)
        freqs = np.asarray(_FREQ_THIRD_OCTAVE, dtype=np.float64)
    else:
        freqs = np.asarray(frequencies, dtype=np.float64)
        require_equal_shapes(
            owner,
            {"values_by_band": data.shape, "frequencies": freqs.shape},
            "band",
        )
        if not np.all(np.isfinite(freqs)) or np.any(freqs <= 0.0):
            msg = "'frequencies' must contain positive values."
            raise ValueError(msg)
    core_idx = _match_bands(freqs, _FREQ_THIRD_OCTAVE)
    if core_idx is None:
        msg = (
            "The input must contain the 16 core one-third-octave bands "
            "100-3150 Hz (ISO 717 rates the single number on that range)."
        )
        raise ValueError(msg)
    return _round_half_up_tenths(data), freqs, core_idx


def weighted_rating_extended(
    values_by_band: Sequence[float] | np.ndarray,
    frequencies: Sequence[float] | np.ndarray | None = None,
    *,
    one_decimal: bool = False,
) -> ExtendedWeightedRatingResult:
    r"""Weighted rating with enlarged-range adaptation terms (ISO 717-1 An. B).

    Computes the weighted rating from the core one-third-octave bands
    100-3150 Hz (Clause 4.4) and, for every enlarged frequency range covered
    by the input, the additional spectrum adaptation terms of Annex B
    (``C50-3150``, ``C50-5000``, ``C100-5000`` and the ``Ctr`` counterparts)
    with the Table B.1 spectra: :math:`C_j = X_{\mathrm{A}j} - X_\mathrm{w}` where ``XAj`` sums
    over the
    bands of the enlarged range (Clause 4.5 with Annex B).

    With ``one_decimal=True`` the reference-curve shift runs in 0,1 dB steps
    and every reduction keeps one decimal place; the variant Clauses 4.4/4.5
    prescribe "for the expression of uncertainty" and ISO 12999-1:2020
    Annex B requires for the uncertainty of single-number values.

    :param values_by_band: Measured band quantities (``R``, ``R'``, ``Dn``,
        ``DnT`` ...) in dB, one-third-octave bands.
    :param frequencies: Band centre frequencies, in Hz (one per value).
        ``None`` assumes exactly the 16 core bands 100-3150 Hz. The 16 core
        bands must always be present; extended terms are formed for each
        Annex B range whose bands are all present.
    :param one_decimal: Use the 0,1 dB shift and one-decimal reductions.
    :return: An :class:`ExtendedWeightedRatingResult`.
    :raises ValueError: If the input is not one-dimensional and finite, the
        band counts differ, or the core bands are missing.
    """
    measured, freqs, core_idx = _validated_extended_input(
        "weighted_rating_extended", values_by_band, frequencies
    )
    core_measured = measured[core_idx]
    ref = np.asarray(_REF_THIRD_OCTAVE, dtype=np.float64)
    step = 0.1 if one_decimal else 1.0
    shift, _ = _best_shift(core_measured, ref, _MAX_UNFAVOURABLE_THIRD, step)
    rating = float(_REF_THIRD_OCTAVE[_INDEX_500_THIRD]) + shift

    def _term(bands: np.ndarray, spectrum: Sequence[int]) -> float:
        x_aj = -energy_sum(np.asarray(spectrum, dtype=np.float64) - bands)
        return _reduce(value=float(x_aj), one_decimal=one_decimal) - rating

    c = _term(core_measured, _SPECTRUM1_THIRD)
    ctr = _term(core_measured, _SPECTRUM2_THIRD)
    extended: dict[str, float | None] = {}
    for suffix, (band_freqs, spectrum1, spectrum2) in _EXTENDED_RANGES.items():
        idx = _match_bands(freqs, band_freqs)
        if idx is None:
            extended[f"c_{suffix}"] = None
            extended[f"ctr_{suffix}"] = None
            continue
        for name, spectrum in (
            (f"c_{suffix}", spectrum1),
            (f"ctr_{suffix}", spectrum2),
        ):
            term = _term(measured[idx], spectrum)
            extended[name] = term if one_decimal else int(term)

    return ExtendedWeightedRatingResult(
        rating=rating if one_decimal else int(rating),
        c=c if one_decimal else int(c),
        ctr=ctr if one_decimal else int(ctr),
        c_50_3150=extended["c_50_3150"],
        c_50_5000=extended["c_50_5000"],
        c_100_5000=extended["c_100_5000"],
        ctr_50_3150=extended["ctr_50_3150"],
        ctr_50_5000=extended["ctr_50_5000"],
        ctr_100_5000=extended["ctr_100_5000"],
        core=weighted_rating(np.asarray(values_by_band, dtype=np.float64)[core_idx]),
        band_centers=read_only_copy(freqs),
        measured=measured,
    )


def weighted_impact_rating_extended(
    values_by_band: Sequence[float] | np.ndarray,
    frequencies: Sequence[float] | np.ndarray | None = None,
    *,
    one_decimal: bool = False,
) -> ExtendedImpactRatingResult:
    r"""Weighted impact rating with ``CI,50-2500`` (ISO 717-2:2020 A.2.1).

    Computes the weighted impact rating from the core one-third-octave bands
    100-3150 Hz (Clause 4.3) and, when the input covers 50-2500 Hz, the
    enlarged-range spectrum adaptation term ``CI,50-2500`` of the A.2.1 NOTE:
    the energetic sum runs over 50-2500 Hz instead of 100-2500 Hz in
    Formula (A.1), :math:`C_\mathrm{I} = L_\mathrm{n,sum} - 15 - L_\mathrm{n,w}`.

    With ``one_decimal=True`` the reference-curve shift runs in 0,1 dB steps
    and the sums keep one decimal place (Clauses 4.3.1/4.4; e.g. the
    reference floor yields :math:`L_\mathrm{n,r,0,w} = 77.6` dB and
    :math:`C_\mathrm{I,r,0} = -10.3` dB
    as printed in A.2.2).

    :param values_by_band: Measured impact levels (``Ln``, ``L'n``, ``L'nT``)
        in dB, one-third-octave bands.
    :param frequencies: Band centre frequencies, in Hz (one per value).
        ``None`` assumes exactly the 16 core bands 100-3150 Hz.
    :param one_decimal: Use the 0,1 dB shift and one-decimal reductions.
    :return: An :class:`ExtendedImpactRatingResult`.
    :raises ValueError: If the input is not one-dimensional and finite, the
        band counts differ, or the core bands are missing.
    """
    measured, freqs, core_idx = _validated_extended_input(
        "weighted_impact_rating_extended", values_by_band, frequencies
    )
    core_measured = measured[core_idx]
    ref = np.asarray(_REF_IMPACT_THIRD_OCTAVE, dtype=np.float64)
    step = 0.1 if one_decimal else 1.0
    # Impact shift = airborne search on the negated curves (see
    # weighted_impact_rating).
    shift, _ = _best_shift(-core_measured, -ref, _MAX_UNFAVOURABLE_THIRD, step)
    rating = float(_REF_IMPACT_THIRD_OCTAVE[_INDEX_500_THIRD]) - shift

    def _ci_over(bands: np.ndarray) -> float:
        l_sum = _reduce(value=float(energy_sum(bands)), one_decimal=one_decimal)
        return l_sum - 15.0 - rating

    ci = _ci_over(core_measured[:_CI_THIRD_OCTAVE_BANDS])
    idx = _match_bands(freqs, _CI_50_2500_FREQS)
    ci_50_2500: float | None = None
    if idx is not None:
        value = _ci_over(measured[idx])
        ci_50_2500 = value if one_decimal else int(value)

    return ExtendedImpactRatingResult(
        rating=rating if one_decimal else int(rating),
        ci=ci if one_decimal else int(ci),
        ci_50_2500=ci_50_2500,
        core=weighted_impact_rating(
            np.asarray(values_by_band, dtype=np.float64)[core_idx]
        ),
        band_centers=read_only_copy(freqs),
        measured=measured,
    )


# --- Reference floors and standard basic elements -------------------------


def _band_table(values: tuple[float, ...]) -> Mapping[float, float]:
    """A read-only ``{band centre in Hz: value}`` table over the 16 core bands."""
    return MappingProxyType(dict(zip(_FREQ_THIRD_OCTAVE, values, strict=True)))


#: The one curve ISO 717-2:2020 Table 4 prints for the lightweight reference
#: floors of type No 1 and No 2 (its column "for lightweight floors C1 and C2").
_LIGHTWEIGHT_C1_C2 = _band_table(
    (78.0, 78.0, 78.0, 78.0, 78.0, 78.0, 76.0, 74.0)
    + (72.0, 69.0, 66.0, 63.0, 60.0, 57.0, 54.0, 51.0)
)

#: Normalized impact sound pressure level of the four reference floors, in dB,
#: keyed by floor and then by one-third-octave band centre frequency in Hz,
#: 100 Hz to 3 150 Hz: ``Ln,r,0`` of the heavyweight concrete floor and
#: ``Ln,t,r,0`` of the three lightweight (timber) floors, as printed in
#: ISO 717-2:2020 Table 4 (PDF page 13, printed folio 7). The floors themselves
#: are built to ISO 10140-5:2021 Annex C; that edition no longer prints the
#: curves and refers to this table, which the 2010 edition printed with the
#: same numbers as its Table C.1. Floors No 1 and No 2 share one column, so
#: their two entries are the same curve; the weighted reduction they yield is
#: still designated apart, ``ΔLt,1,w`` and ``ΔLt,2,w`` (ISO 717-2:2020 6.2).
#: The single numbers the table prints under each curve (78, 72 and 75 dB,
#: with ``CI`` of -11, 0 and -3 dB) are what :func:`weighted_impact_rating`
#: returns for it, and they are not stored: Clause 5.3 obtains ``Ln,r,0,w``
#: from the curve "in accordance with 4.3.1".
IMPACT_REFERENCE_FLOORS: Mapping[str, Mapping[float, float]] = MappingProxyType(
    {
        "heavyweight": _band_table(
            (67.0, 67.5, 68.0, 68.5, 69.0, 69.5, 70.0, 70.5)
            + (71.0, 71.5, 72.0, 72.0, 72.0, 72.0, 72.0, 72.0)
        ),
        "lightweight_1": _LIGHTWEIGHT_C1_C2,
        "lightweight_2": _LIGHTWEIGHT_C1_C2,
        "lightweight_3": _band_table(
            (69.0, 72.0, 75.0, 78.0, 78.0, 78.0, 78.0, 78.0)
            + (78.0, 76.0, 74.0, 72.0, 69.0, 66.0, 63.0, 60.0)
        ),
    }
)

#: A reference floor of :data:`IMPACT_REFERENCE_FLOORS`.
ReferenceFloor = Literal[
    "heavyweight", "lightweight_1", "lightweight_2", "lightweight_3"
]

#: Sound reduction index of the three standard basic elements a lining is
#: rated on, in dB, keyed by element and then by one-third-octave band centre
#: frequency in Hz, 50 Hz to 5 000 Hz: ``Rref,without`` of the heavy wall, the
#: heavy floor and the lightweight wall, as printed in ISO 717-1:2020 Table E.1
#: (PDF pages 30 and 31, printed folios 24 and 25). The elements are built to
#: ISO 10140-5:2021 Annex B, B.2 to B.4; that edition no longer prints the
#: curves and refers to ISO 717-1, and the 2010 edition printed the same
#: numbers as its Table B.1. The single numbers under each curve (``Rw`` of 53,
#: 52 and 33 dB with every adaptation term of Annex B) are what
#: :func:`weighted_rating_extended` returns for it and are not stored.
LINING_REFERENCE_ELEMENTS: Mapping[str, Mapping[float, float]] = MappingProxyType(
    {
        name: MappingProxyType(dict(zip(_FREQ_50_5000, values, strict=True)))
        for name, values in (
            (
                "heavy_wall",
                (35.3, 37.3, 39.4, 40.0, 40.0, 40.0, 40.0, 41.0, 43.5, 46.1, 48.5)
                + (51.0, 53.6, 56.0, 58.4, 61.1, 63.6, 65.0, 65.0, 65.0, 65.0),
            ),
            (
                "heavy_floor",
                (34.0, 36.0, 38.1, 40.0, 40.0, 40.0, 40.0, 40.0, 41.8, 44.4, 46.8)
                + (49.3, 51.9, 54.4, 56.8, 59.5, 61.9, 64.3, 65.0, 65.0, 65.0),
            ),
            (
                "lightweight_wall",
                (21.3, 23.3, 25.3, 27.0, 27.0, 27.0, 27.0, 27.0, 27.0, 27.0, 27.0)
                + (28.0, 30.5, 32.8, 35.1, 37.6, 40.0, 42.3, 44.6, 47.1, 49.4),
            ),
        )
    }
)

#: A standard basic element of :data:`LINING_REFERENCE_ELEMENTS`.
BasicElement = Literal["heavy_wall", "heavy_floor", "lightweight_wall"]

#: The index ISO 717-1:2020 D.3 appends to a lining rating to name the basic
#: element it was rated on: "heavy" for the heavyweight wall and floor and
#: "light" for the lightweight wall.
_ELEMENT_INDEX: Mapping[str, str] = MappingProxyType(
    {"heavy_wall": "heavy", "heavy_floor": "heavy", "lightweight_wall": "light"}
)


def _reference_floor_curve(reference_floor: str) -> np.ndarray:
    """A fresh array of the 16 ``Ln,r,0`` values of one reference floor."""
    require_choice(reference_floor, "reference_floor", tuple(IMPACT_REFERENCE_FLOORS))
    return np.fromiter(
        IMPACT_REFERENCE_FLOORS[reference_floor].values(), dtype=np.float64
    )


def _validated_improvement(
    delta: Sequence[float] | np.ndarray, name: str
) -> np.ndarray:
    """The 16 core one-third-octave values of an improvement spectrum."""
    values = np.asarray(delta, dtype=np.float64)
    if values.shape != (_N_THIRD_OCTAVE_BANDS,):
        msg = f"'{name}' must give the 16 one-third-octave values 100-3150 Hz."
        raise ValueError(msg)
    if not np.all(np.isfinite(values)):
        msg = f"'{name}' must contain only finite values."
        raise ValueError(msg)
    return values


def _impact_improvement_ratings(
    delta_l: Mapping[float, float] | Sequence[float] | np.ndarray,
    reference_floor: str,
    *,
    one_decimal: bool,
) -> tuple[float, float]:
    """``(ΔLw, CI,Δ)`` of Formulas (1), (2) and (A.4)/(A.6), unrounded types."""
    dl, _ = _by_band(delta_l, "third-octave", "delta_l")
    bare = _reference_floor_curve(reference_floor)
    covered = bare - _validated_improvement(dl, "delta_l")  # Formula (1)
    rated_bare = weighted_impact_rating_extended(bare, one_decimal=one_decimal)
    rated_covered = weighted_impact_rating_extended(covered, one_decimal=one_decimal)
    delta_lw = _reduce(
        rated_bare.rating - rated_covered.rating, one_decimal=one_decimal
    )
    ci_delta = _reduce(rated_bare.ci - rated_covered.ci, one_decimal=one_decimal)
    return delta_lw, ci_delta


@overload
def weighted_impact_improvement(
    delta_l: Mapping[float, float] | Sequence[float] | np.ndarray,
    *,
    reference_floor: ReferenceFloor = ...,
    one_decimal: Literal[False] = ...,
) -> int: ...


@overload
def weighted_impact_improvement(
    delta_l: Mapping[float, float] | Sequence[float] | np.ndarray,
    *,
    reference_floor: ReferenceFloor = ...,
    one_decimal: Literal[True],
) -> float: ...


@overload
def weighted_impact_improvement(
    delta_l: Mapping[float, float] | Sequence[float] | np.ndarray,
    *,
    reference_floor: ReferenceFloor = ...,
    one_decimal: bool = ...,
) -> int | float: ...


def weighted_impact_improvement(
    delta_l: Mapping[float, float] | Sequence[float] | np.ndarray,
    *,
    reference_floor: ReferenceFloor = "heavyweight",
    one_decimal: bool = False,
) -> int | float:
    r"""Weighted reduction of impact level ``ΔLw`` or ``ΔLt,w`` (ISO 717-2:2020).

    Relates a measured improvement spectrum ``ΔL`` to a reference floor of
    Table 4 (:data:`IMPACT_REFERENCE_FLOORS`): the reference level with the
    covering is :math:`L_\mathrm{n,r} = L_\mathrm{n,r,0} - \Delta L`
    (Formula (1)) and the weighted improvement is
    :math:`\Delta L_\mathrm{w} = L_\mathrm{n,r,0,w} - L_\mathrm{n,r,w}`
    (Formula (2)), both weighted ratings taken with
    :func:`weighted_impact_rating`. On the heavyweight floor this is the
    ``ΔLw`` of Clause 5, :math:`78 - L_\mathrm{n,r,w}`; on a lightweight floor
    it is the ``ΔLt,w`` of Clause 6, which 6.3 computes "as specified in 5.3,
    substituting the heavy reference floor by a lightweight reference floor"
    and 6.2 designates ``ΔLt,1,w``, ``ΔLt,2,w`` or ``ΔLt,3,w`` by floor type.

    ``one_decimal=True`` rates both curves with the 0,1 dB shift and keeps one
    decimal place, the form 5.4 prescribes when the uncertainty of ``ΔLw`` is
    stated (its EXAMPLE, ``ΔLw = 18,9 ± 1,1``); ``Ln,r,0,w`` is then 77,6 dB for
    the heavyweight floor, as A.2.2 prints.

    :param delta_l: The reduction of impact sound pressure level ``ΔL`` per band,
        in dB; 16 one-third-octave values from 100 Hz to 3150 Hz (e.g. from a
        floor-covering measurement to ISO 10140-1:2021 Annex H or
        ISO 16251-1), or a mapping of band centre frequency in hertz to ``ΔL``
        that holds those 16 bands, other keys not read.
    :param reference_floor: ``"heavyweight"`` (default), ``"lightweight_1"``,
        ``"lightweight_2"`` or ``"lightweight_3"``.
    :param one_decimal: Use the 0,1 dB shift and one-decimal reductions.
    :return: The weighted reduction, in dB: an integer, or a value to one
        decimal place when ``one_decimal`` is set.
    :raises ValueError: If ``delta_l`` is not 16 finite one-third-octave values,
        a mapping lacks one of them, or ``reference_floor`` is not one of the
        four floors.
    """
    delta_lw, _ = _impact_improvement_ratings(
        delta_l, reference_floor, one_decimal=one_decimal
    )
    return delta_lw if one_decimal else int(delta_lw)


@overload
def impact_improvement_adaptation_term(
    delta_l: Mapping[float, float] | Sequence[float] | np.ndarray,
    *,
    reference_floor: ReferenceFloor = ...,
    one_decimal: Literal[False] = ...,
) -> int: ...


@overload
def impact_improvement_adaptation_term(
    delta_l: Mapping[float, float] | Sequence[float] | np.ndarray,
    *,
    reference_floor: ReferenceFloor = ...,
    one_decimal: Literal[True],
) -> float: ...


@overload
def impact_improvement_adaptation_term(
    delta_l: Mapping[float, float] | Sequence[float] | np.ndarray,
    *,
    reference_floor: ReferenceFloor = ...,
    one_decimal: bool = ...,
) -> int | float: ...


def impact_improvement_adaptation_term(
    delta_l: Mapping[float, float] | Sequence[float] | np.ndarray,
    *,
    reference_floor: ReferenceFloor = "heavyweight",
    one_decimal: bool = False,
) -> int | float:
    r"""Adaptation term ``CI,Δ`` or ``CIΔ,t`` of a floor covering (ISO 717-2:2020).

    :math:`C_{\mathrm{I},\Delta} = C_\mathrm{I,r,0} - C_\mathrm{I,r}`
    (Formula (A.4)) on the heavyweight floor, with :math:`C_\mathrm{I,r,0} = -11`
    dB, and :math:`C_{\mathrm{I}\Delta,\mathrm{t}} = C_\mathrm{I,t,r,0} -
    C_\mathrm{I,t,r}` (Formula (A.6)) on a lightweight one, with
    :math:`C_\mathrm{I,t,r,0}` of 0 dB for floors No 1 and No 2 and -3 dB for
    No 3. ``CI,r`` is the ISO 717-2 spectrum adaptation term of the reference
    floor with the covering under test,
    :math:`L_\mathrm{n,r} = L_\mathrm{n,r,0} - \Delta L` (Formula (1)). Together
    with :func:`weighted_impact_improvement` it yields the single-number
    reduction for a flat spectrum,
    :math:`\Delta L_\mathrm{lin} = \Delta L_\mathrm{w} + C_{\mathrm{I},\Delta}`
    (Formula (A.5), or (A.7) on a lightweight floor). ISO 16251-1 Clause 8 e)
    and ISO 10140-1:2021 H.5 h) require this term in the statement of results.

    With ``one_decimal=True`` both terms keep one decimal place, which gives
    ``CI,r,0 = -10,3`` dB and ``CI,t,r,0`` of 0,0 and -2,8 dB as A.2.2 and
    A.2.3 print.

    :param delta_l: The reduction of impact sound pressure level ``ΔL`` per
        band, in dB; 16 one-third-octave values from 100 Hz to 3150 Hz, or a
        mapping of band centre frequency in hertz to ``ΔL`` that holds those
        16 bands, other keys not read.
    :param reference_floor: ``"heavyweight"`` (default), ``"lightweight_1"``,
        ``"lightweight_2"`` or ``"lightweight_3"``.
    :param one_decimal: Use the 0,1 dB shift and one-decimal reductions.
    :return: The spectrum adaptation term, in dB: an integer, or a value to
        one decimal place when ``one_decimal`` is set.
    :raises ValueError: If ``delta_l`` is not 16 finite one-third-octave
        values, a mapping lacks one of them, or ``reference_floor`` is not one
        of the four floors.
    """
    _, ci_delta = _impact_improvement_ratings(
        delta_l, reference_floor, one_decimal=one_decimal
    )
    return ci_delta if one_decimal else int(ci_delta)


#: The spectrum adaptation term ``CI,r,0`` of the bare heavyweight reference
#: floor, -11 dB (ISO 717-2:2020 A.2.2), rated from its Table 4 curve as
#: Clause 5.3 rates the floor rather than stored beside it.
_IMPACT_REFERENCE_FLOOR_CI = weighted_impact_rating(
    IMPACT_REFERENCE_FLOORS["heavyweight"]
).ci


@dataclass(frozen=True)
class ReductionImprovementRating:
    r"""Single-number improvement of the sound reduction index by a lining.

    The rating of ISO 717-1:2020 Annex D: the measured ``ΔR`` is added to the
    reference curve of a standard basic element,
    :math:`R_\mathrm{ref,with} = R_\mathrm{ref,without} + \Delta R`
    (Formula (D.3)), both curves are rated, and each improvement is the
    difference of the two ratings (Formula (D.4)). Every value is an integer
    unless the rating was computed with ``one_decimal=True``. An enlarged-range
    term is ``None`` when ``ΔR`` did not cover its bands.

    :ivar basic_element: ``"heavy_wall"``, ``"heavy_floor"`` or
        ``"lightweight_wall"``.
    :ivar delta_rw: ``ΔRw``, in dB.
    :ivar delta_rw_c: ``Δ(Rw + C)``, in dB.
    :ivar delta_rw_ctr: ``Δ(Rw + Ctr)``, in dB.
    :ivar delta_rw_c_50_3150: ``Δ(Rw + C50-3150)``, in dB, or ``None``.
    :ivar delta_rw_c_50_5000: ``Δ(Rw + C50-5000)``, in dB, or ``None``.
    :ivar delta_rw_c_100_5000: ``Δ(Rw + C100-5000)``, in dB, or ``None``.
    :ivar delta_rw_ctr_50_3150: ``Δ(Rw + Ctr,50-3150)``, in dB, or ``None``.
    :ivar delta_rw_ctr_50_5000: ``Δ(Rw + Ctr,50-5000)``, in dB, or ``None``.
    :ivar delta_rw_ctr_100_5000: ``Δ(Rw + Ctr,100-5000)``, in dB, or ``None``.
    :ivar without_lining: The rating of ``Rref,without``, the bare reference
        curve over the bands ``ΔR`` was given in.
    :ivar with_lining: The rating of ``Rref,with``.
    """

    basic_element: str
    delta_rw: float
    delta_rw_c: float
    delta_rw_ctr: float
    delta_rw_c_50_3150: float | None
    delta_rw_c_50_5000: float | None
    delta_rw_c_100_5000: float | None
    delta_rw_ctr_50_3150: float | None
    delta_rw_ctr_50_5000: float | None
    delta_rw_ctr_100_5000: float | None
    without_lining: ExtendedWeightedRatingResult
    with_lining: ExtendedWeightedRatingResult

    def __post_init__(self) -> None:
        """Reject a basic element the reference table does not carry.

        The plot titles the rating with the index Annex D appends to it, read
        from the element name, so a name outside the three standard elements
        would reach the figure before anything had said which names there are.

        :raises ValueError: if ``basic_element`` is not a standard element.
        """
        require_choice(
            self.basic_element, "basic_element", tuple(LINING_REFERENCE_ELEMENTS)
        )

    @property
    def index(self) -> str:
        """The element index of ISO 717-1:2020 D.3: ``"heavy"`` or ``"light"``."""
        return _ELEMENT_INDEX[self.basic_element]

    def plot(
        self, ax: Axes | None = None, *, language: str = "en", **kwargs: Any
    ) -> Axes:
        """Plot ``Rref,without`` and ``Rref,with`` with the improvement ratings.

        Draws the reference curve of the basic element and the same curve
        raised by the measured ``ΔR``, the two curves Annex D rates; the title
        carries ``ΔRw``, ``Δ(Rw + C)`` and ``Δ(Rw + Ctr)`` with the element
        index. Requires matplotlib (``pip install phonometry[plot]``); returns
        the :class:`~matplotlib.axes.Axes`.
        """
        from ..._i18n import check_language
        from ..._plot.building import plot_reduction_improvement_rating

        check_language(language)
        return plot_reduction_improvement_rating(
            self, ax=ax, language=language, **kwargs
        )


def weighted_reduction_improvement(
    delta_r: Sequence[float] | np.ndarray,
    frequencies: Sequence[float] | np.ndarray | None = None,
    *,
    basic_element: BasicElement = "heavy_wall",
    one_decimal: bool = False,
) -> ReductionImprovementRating:
    r"""Weighted improvement of the sound reduction index by a lining (ISO 717-1).

    ISO 717-1:2020 Annex D rates a lining on a standard basic element rather
    than on the wall it was measured on, so that the number describes the
    lining and not the laboratory: the measured improvement ``ΔR`` is added
    to the reference curve of the element (:data:`LINING_REFERENCE_ELEMENTS`),
    :math:`R_\mathrm{ref,with} = R_\mathrm{ref,without} + \Delta R`
    (Formula (D.3)), both curves are rated with
    :func:`weighted_rating_extended`, and
    :math:`\Delta R_\mathrm{w} = R_\mathrm{w,ref,with} - R_\mathrm{w,ref,without}`
    (Formula (D.4)). ``Δ(Rw + C)`` and ``Δ(Rw + Ctr)`` are "calculated in an
    equivalent way", as differences of the sums, and so is every
    enlarged-range term of Annex B whose bands ``ΔR`` covers. The rating
    carries the element index of D.3, ``ΔRw,heavy`` or ``ΔRw,light``.

    For a basic element that is not one of the three standard ones, D.3 takes
    the ratings "directly from the single-number ratings for that basic
    element with and without the tested acoustical lining", the direct
    difference ``ΔRw,direct`` of Formula (D.2); that needs both measured
    curves and is what :func:`~phonometry.building.lab_lining_improvement`
    returns beside this rating.

    :param delta_r: The sound reduction improvement index ``ΔR`` per
        one-third-octave band, in dB (ISO 10140-1:2021 G.1).
    :param frequencies: Band centre frequencies of ``delta_r``, in Hz; ``None``
        assumes exactly the 16 core bands 100 Hz to 3 150 Hz. The 16 core
        bands must be present, and every band must be one Table E.1 prints
        (50 Hz to 5 000 Hz).
    :param basic_element: ``"heavy_wall"`` (default), ``"heavy_floor"`` or
        ``"lightweight_wall"``.
    :param one_decimal: Rate both curves with the 0,1 dB shift and one-decimal
        reductions, the form of Clause 4.4 for the expression of uncertainty.
    :return: A :class:`ReductionImprovementRating`.
    :raises ValueError: If ``delta_r`` is not one-dimensional and finite, the
        band counts differ, a band is not in Table E.1, the core bands are
        missing, or ``basic_element`` is not a standard element.
    """
    require_choice(basic_element, "basic_element", tuple(LINING_REFERENCE_ELEMENTS))
    delta = np.asarray(delta_r, dtype=np.float64)
    if delta.ndim != 1:
        msg = "'delta_r' must be one-dimensional (one value per band)."
        raise ValueError(msg)
    if not np.all(np.isfinite(delta)):
        msg = "'delta_r' must contain only finite values."
        raise ValueError(msg)
    if frequencies is None:
        freqs = np.asarray(_FREQ_THIRD_OCTAVE, dtype=np.float64)
    else:
        freqs = np.asarray(frequencies, dtype=np.float64)
    require_equal_shapes(
        "weighted_reduction_improvement",
        {"delta_r": delta.shape, "frequencies": freqs.shape},
        "band",
    )
    table = LINING_REFERENCE_ELEMENTS[basic_element]
    indices = _match_bands(np.asarray(tuple(table), dtype=np.float64), tuple(freqs))
    if indices is None or np.unique(indices).size != indices.size:
        msg = (
            "Every band of 'delta_r' must be a one-third-octave band of "
            "ISO 717-1:2020 Table E.1, 50 Hz to 5000 Hz, each given once."
        )
        raise ValueError(msg)
    without = np.asarray(tuple(table.values()), dtype=np.float64)[indices]
    rated_without = weighted_rating_extended(without, freqs, one_decimal=one_decimal)
    rated_with = weighted_rating_extended(
        without + delta, freqs, one_decimal=one_decimal
    )

    def _delta(before: float, after: float) -> float:
        value = _reduce(after - before, one_decimal=one_decimal)
        return value if one_decimal else int(value)

    def _extended(term: str) -> float | None:
        before, after = getattr(rated_without, term), getattr(rated_with, term)
        if before is None or after is None:
            return None
        return _delta(rated_without.rating + before, rated_with.rating + after)

    return ReductionImprovementRating(
        basic_element=basic_element,
        delta_rw=_delta(rated_without.rating, rated_with.rating),
        delta_rw_c=_delta(
            rated_without.rating + rated_without.c, rated_with.rating + rated_with.c
        ),
        delta_rw_ctr=_delta(
            rated_without.rating + rated_without.ctr,
            rated_with.rating + rated_with.ctr,
        ),
        delta_rw_c_50_3150=_extended("c_50_3150"),
        delta_rw_c_50_5000=_extended("c_50_5000"),
        delta_rw_c_100_5000=_extended("c_100_5000"),
        delta_rw_ctr_50_3150=_extended("ctr_50_3150"),
        delta_rw_ctr_50_5000=_extended("ctr_50_5000"),
        delta_rw_ctr_100_5000=_extended("ctr_100_5000"),
        without_lining=rated_without,
        with_lining=rated_with,
    )
