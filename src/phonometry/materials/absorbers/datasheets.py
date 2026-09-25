#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Sound absorption as a data sheet or a test report prints it.

The absorption tables of the books (:mod:`~phonometry.materials.absorbers.measured`)
print one Sabine coefficient per octave and rarely say how it was measured. A
product's data sheet, its declaration of performance and the laboratory's
test report print something narrower and better defined, and they print it
in two shapes that are not the same quantity:

* the **sound absorption coefficient** :math:`\alpha_\mathrm{s}` of ISO 354,
  one value per one-third octave band as the reverberation room measured it,
  which can exceed 1 and carries every digit the laboratory reported; and
* the **practical sound absorption coefficient** :math:`\alpha_\mathrm{p}` of
  ISO 11654 Clause 4.1, one value per octave band from 125 Hz to 4 kHz, the
  mean of the three one-third octaves in it rounded in steps of 0,05 and
  capped at 1,00.

The two are two classes here, :class:`ThirdOctaveAbsorptionSpectrum` and
:class:`PracticalAbsorptionSpectrum`, because the band resolution and the
rounding are part of what the number is, and a row that held either under
one name would let an :math:`\alpha_\mathrm{p}` pass for a measurement it
was averaged and rounded from. The quantity lives in the class, never in a
flag, and a catalogue file says which one it holds by its ``row_type``.

Both carry the single-number rating the sheet prints beside the bands, the
weighted sound absorption coefficient :math:`\alpha_\mathrm{w}` of ISO 11654
Clause 4.2 with its shape indicators and its class, and both work it out
again from the bands with :meth:`PracticalAbsorptionSpectrum.rating` or
:meth:`ThirdOctaveAbsorptionSpectrum.rating`. The printed rating is kept as
printed; the one worked out is the library's, and when a catalogue file is
read the two are compared and any difference is noted beside the catalogue,
never reconciled.

The 125 Hz octave of :math:`\alpha_\mathrm{p}` is defined like the others
(ISO 11654 Clause 4.1 forms :math:`\alpha_\mathrm{p}` for each octave band,
and Clause 5.2 plots it from 125 Hz) and is not rated: the reference curve
starts at 250 Hz, and Clause 1 says the rating is not appropriate below it.
So a row holds it and :meth:`PracticalAbsorptionSpectrum.rating` never reads
it.

Nothing here ships with data. A caller's own catalogue holds these rows, read
by :func:`phonometry.io.read_catalogue` from the file the caller typed from
the sheet.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, ClassVar

from ..._internal.catalogue import BandedRow, _bases_named
from .rating import (
    OCTAVE_BANDS,
    THIRD_OCTAVE_BANDS,
    AbsorptionRatingResult,
    _practical_round,
    weighted_absorption,
    weighted_absorption_from_third_octave,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

__all__ = ["PracticalAbsorptionSpectrum", "ThirdOctaveAbsorptionSpectrum"]

#: The octave bands of ISO 11654 Clause 5.2, in hertz: the five rating bands
#: and the 125 Hz band plotted with them.
_PRACTICAL_BANDS_HZ: tuple[int, ...] = (125, 250, 500, 1000, 2000, 4000)

#: The one-third octave bands an ISO 354 measurement can report, in hertz:
#: the 100 Hz to 5 kHz of the standard and the extensions a laboratory
#: prints down to 50 Hz and up to 10 kHz.
_THIRD_OCTAVE_BANDS_HZ: tuple[int, ...] = (
    50,
    63,
    80,
    100,
    125,
    160,
    200,
    250,
    315,
    400,
    500,
    630,
    800,
    1000,
    1250,
    1600,
    2000,
    2500,
    3150,
    4000,
    5000,
    6300,
    8000,
    10000,
)

#: The step and the ceiling of a practical coefficient and of the weighted
#: coefficient (ISO 11654 Clauses 4.1 and 4.2), in the digits the sheet
#: prints.
_STEP = Decimal("0.05")
_CEILING = Decimal(1)

#: The fields of every row that name and cite it, which a practical row
#: takes over from the one-third-octave row it is worked out from.
_ROW = ("name", "source", "table", "variant", "group", "note", "provenance")

#: The fields a practical row and a one-third-octave row share: what the
#: specimen is and the rating the sheet prints for it.
_SHARED = (
    "weighted_absorption_coefficient",
    "shape_indicator",
    "absorption_class",
    "noise_reduction_coefficient",
    "mounting",
    "thickness_mm",
    "construction_depth_mm",
)


def _digits(value: float) -> Decimal:
    """A number as the digits it was printed with.

    A float read from a file keeps the shortest digits that give it back,
    so ``repr`` returns the page's ``0.85`` rather than a binary expansion;
    the grid of ISO 11654 is checked on those digits, where a float would
    need a tolerance.
    """
    return Decimal(repr(value))


def _shown(value: float) -> str:
    """A coefficient as a sheet prints one: two decimals, or every digit it has.

    ISO 11654 Clause 5 gives the coefficients to two decimal places, so a
    0.6 read from a cell that said 0,60 is shown as 0.60; a value with more
    digits keeps all of them.
    """
    digits = _digits(value)
    hundredths = digits.quantize(Decimal("0.01"))
    return f"{hundredths}" if hundredths == digits else f"{digits}"


def _off_grid(value: float) -> str:
    """Why a printed coefficient is none ISO 11654 rounds to, or ``""``."""
    digits = _digits(value)
    if digits > _CEILING:
        return "above the 1.00 it is capped at"
    if digits % _STEP:
        return "off the steps of 0.05 it is rounded in"
    return ""


def _class_word(printed: str) -> str:
    """A printed absorption class as :func:`absorption_class` spells it."""
    word = printed.strip()
    if word.casefold().startswith("class "):
        word = word[len("class ") :].strip()
    return word.upper() if len(word) == 1 else word


@dataclass(frozen=True, kw_only=True)
class _RatedAbsorption(BandedRow):
    r"""What an absorption row of a data sheet prints beside its bands.

    :ivar weighted_absorption_coefficient: The weighted sound absorption
        coefficient :math:`\alpha_\mathrm{w}` the sheet prints (ISO 11654
        Clause 4.2), dimensionless: the shifted reference curve read at
        500 Hz, a multiple of 0,05 from 0 to 1.
    :ivar shape_indicator: The shape indicators printed after it, the
        letters only: ``"MH"`` for ``0,70(MH)`` (ISO 11654 Clause 4.3). Empty
        when the sheet prints none, which on a sheet that prints the rating
        is also what a curve without an excess looks like.
    :ivar absorption_class: The sound absorption class of ISO 11654 Annex B,
        ``"A"`` to ``"E"`` or ``"Not classified"``, as the sheet prints it.
    :ivar noise_reduction_coefficient: The NRC a sheet prints under ASTM
        C423, dimensionless: the mean of the Sabine coefficients at 250,
        500, 1000 and 2000 Hz rounded to 0,05. Held as printed; no function
        of this library works it out, so nothing compares it.
    :ivar mounting: The test mounting as the sheet prints it: ``"A"`` for a
        specimen laid against the room surface, ``"E-200"`` for one over an
        air space whose suffix is the distance in millimetres from its
        exposed face to the room surface behind it (ISO 354 Annex B). Empty
        for a sheet that prints none, which is not the same as mounting A.
    :ivar thickness_mm: The thickness of the specimen, in millimetres.
    :ivar construction_depth_mm: The depth of construction ISO 11654
        Clause 5.4 asks a result to state for a product mounted over an air
        space, in millimetres: from the room surface to the exposed face of
        the absorber (its Figure 2), which is what some sheets call the
        total construction height. It is not the air space alone: the
        absorber's thickness is part of it.
    """

    weighted_absorption_coefficient: float | None = None
    shape_indicator: str = ""
    absorption_class: str = ""
    noise_reduction_coefficient: float | None = None
    mounting: str = ""
    thickness_mm: float | None = None
    construction_depth_mm: float | None = None

    def _rating_notes(self) -> Iterator[str]:
        """Where the rating the sheet prints is not the one its bands give."""
        printed = self.weighted_absorption_coefficient
        if printed is not None and (why := _off_grid(printed)):
            yield (
                f"the weighted coefficient is printed as {_shown(printed)}, {why} "
                "(ISO 11654 Clause 4.2)"
            )
        rating = self._rating_if_printed()
        if rating is None:
            return
        if printed is not None and _digits(printed) != _digits(rating.alpha_w):
            yield (
                f"the weighted coefficient is printed as {_shown(printed)} and the "
                f"bands give {rating.alpha_w:.2f} (ISO 11654 Clause 4.2); the "
                "printed value is kept as printed"
            )
        shape = self.shape_indicator.strip().strip("()").upper()
        if shape and shape != rating.shape_indicator:
            given = rating.shape_indicator or "none"
            yield (
                f"the shape indicator is printed as {self.shape_indicator!r} "
                f"and the bands give {given} (ISO 11654 Clause 4.3); the "
                "printed one is kept as printed"
            )
        word = self.absorption_class.strip()
        if word and _class_word(word) != rating.absorption_class:
            yield (
                f"the absorption class is printed as {word!r} and the bands "
                f"give {rating.absorption_class!r} (ISO 11654 Annex B); the "
                "printed one is kept as printed"
            )

    def _rating_if_printed(self) -> AbsorptionRatingResult | None:
        """The rating when the row prints every band it needs, else ``None``."""
        raise NotImplementedError  # pragma: no cover - every subclass rates


@dataclass(frozen=True, kw_only=True)
class PracticalAbsorptionSpectrum(_RatedAbsorption):
    r"""One specimen of a data sheet, with its practical coefficient per octave.

    The practical sound absorption coefficient :math:`\alpha_\mathrm{p}` of
    ISO 11654 Clause 4.1 is the mean of the three one-third-octave
    coefficients of ISO 354 inside an octave, worked out to the second
    decimal, rounded in steps of 0,05 and set to 1,00 when it rounds above.
    A sheet that prints six values from 125 Hz to 4 kHz all ending in 0 or 5
    is printing these, and a row of this class holds them as printed, a
    value above 1,00 or off the steps included: the reader of a catalogue
    file notes such a value, and nothing here corrects it.

    A declaration under a product standard declares the coefficients as a
    level no result falls below (EN 13162 Clause 4.3.11 does, for mineral
    wool), so a sheet that says it declares them is recorded with
    :attr:`~phonometry.io.CatalogueRow.basis` ``"declared"``.

    :ivar practical_absorption_coefficient_125: :math:`\alpha_\mathrm{p}` in
        the 125 Hz octave band, dimensionless. Defined like the others and
        not rated (ISO 11654 Clause 1).
    :ivar practical_absorption_coefficient_250: The same in the 250 Hz band.
    :ivar practical_absorption_coefficient_500: The same in the 500 Hz band.
    :ivar practical_absorption_coefficient_1000: The same in the 1 kHz band.
    :ivar practical_absorption_coefficient_2000: The same in the 2 kHz band.
    :ivar practical_absorption_coefficient_4000: The same in the 4 kHz band.
    """

    practical_absorption_coefficient_125: float | None = None
    practical_absorption_coefficient_250: float | None = None
    practical_absorption_coefficient_500: float | None = None
    practical_absorption_coefficient_1000: float | None = None
    practical_absorption_coefficient_2000: float | None = None
    practical_absorption_coefficient_4000: float | None = None

    _bands_hz: ClassVar[tuple[int, ...]] = _PRACTICAL_BANDS_HZ
    _band_prefix: ClassVar[str] = "practical_absorption_coefficient_"
    _band_kind: ClassVar[str] = "an octave"
    _table_kind: ClassVar[str] = "practical absorption"

    def practical_absorption_coefficient(self, band_hz: int) -> float:
        r"""The practical coefficient in one octave, or a refusal.

        :param band_hz: An octave-band centre frequency from 125 Hz to
            4000 Hz.
        :return: The printed :math:`\alpha_\mathrm{p}`, as a float.
        :raises ValueError: when the sheet has no number in that band, naming
            the row, the band and what the cell held instead; or when
            *band_hz* is not one of the six octaves.
        """
        return self._in_band(band_hz)

    def rating(self) -> AbsorptionRatingResult:
        r"""The weighted sound absorption coefficient of the row's octaves.

        :func:`~phonometry.materials.weighted_absorption` on the five rating
        bands, 250 Hz to 4 kHz (ISO 11654 Clause 4.2), which snaps each
        value to the 0,05 grid and caps it at 1,00 as Clause 4.1 would have.
        The 125 Hz band is not read. The rating the sheet prints beside the
        bands is not consulted either: this is the one the bands give, and
        :func:`phonometry.io.read_catalogue` notes when the two differ.

        :return: The :class:`~phonometry.materials.AbsorptionRatingResult`,
            with :math:`\alpha_\mathrm{w}`, the shape indicators and the
            class.
        :raises ValueError: for a rating band the row does not print, naming
            the row, the band and what the sheet had there; nothing is filled
            in for it.
        """
        return weighted_absorption(self.values_at(OCTAVE_BANDS))

    def _rating_if_printed(self) -> AbsorptionRatingResult | None:
        values = [getattr(self, self._band_field(band)) for band in OCTAVE_BANDS]
        if any(value is None or value < 0 for value in values):
            return None
        return weighted_absorption(values)

    def _catalogue_notes(self) -> tuple[str, ...]:
        r"""Values off the steps ISO 11654 rounds to, and a rating that disagrees.

        A practical coefficient above 1,00 or off the steps of 0,05, and a
        printed :math:`\alpha_\mathrm{w}` off them, are noted on the digits
        the sheet prints; and when the row prints the five rating bands, the
        rating they give is compared with the one printed. Nothing is
        changed: the row keeps what the sheet prints.
        """
        notes = [
            (
                f"the practical coefficient at {band} Hz is printed as {_shown(value)}, "
                f"{why} (ISO 11654 Clause 4.1)"
            )
            for band in self._bands_hz
            if (value := getattr(self, self._band_field(band))) is not None
            and (why := _off_grid(value))
        ]
        notes += self._rating_notes()
        return tuple(notes)


@dataclass(frozen=True, kw_only=True)
class ThirdOctaveAbsorptionSpectrum(_RatedAbsorption):
    r"""One specimen of a test report, with its coefficient per one-third octave.

    The sound absorption coefficient :math:`\alpha_\mathrm{s}` of ISO 354,
    as the reverberation room measured it: one value per one-third octave
    band, 100 Hz to 5 kHz in the standard's range and from 50 Hz to 10 kHz
    where a laboratory reports more. A value above 1 is common and not an
    error, because :math:`\alpha_\mathrm{s}` is referred to the specimen's
    area and its edges absorb too; nothing here caps it.

    :meth:`practical` turns the row into its practical coefficients, and
    :meth:`rating` rates it; both leave out an octave the row cannot give
    all three of its one-third octaves for.

    :ivar absorption_coefficient_50: :math:`\alpha_\mathrm{s}` in the 50 Hz
        one-third octave band, dimensionless, as printed.
    :ivar absorption_coefficient_63: The same in the 63 Hz band.
    :ivar absorption_coefficient_80: The same in the 80 Hz band.
    :ivar absorption_coefficient_100: The same in the 100 Hz band.
    :ivar absorption_coefficient_125: The same in the 125 Hz band.
    :ivar absorption_coefficient_160: The same in the 160 Hz band.
    :ivar absorption_coefficient_200: The same in the 200 Hz band.
    :ivar absorption_coefficient_250: The same in the 250 Hz band.
    :ivar absorption_coefficient_315: The same in the 315 Hz band.
    :ivar absorption_coefficient_400: The same in the 400 Hz band.
    :ivar absorption_coefficient_500: The same in the 500 Hz band.
    :ivar absorption_coefficient_630: The same in the 630 Hz band.
    :ivar absorption_coefficient_800: The same in the 800 Hz band.
    :ivar absorption_coefficient_1000: The same in the 1 kHz band.
    :ivar absorption_coefficient_1250: The same in the 1.25 kHz band.
    :ivar absorption_coefficient_1600: The same in the 1.6 kHz band.
    :ivar absorption_coefficient_2000: The same in the 2 kHz band.
    :ivar absorption_coefficient_2500: The same in the 2.5 kHz band.
    :ivar absorption_coefficient_3150: The same in the 3.15 kHz band.
    :ivar absorption_coefficient_4000: The same in the 4 kHz band.
    :ivar absorption_coefficient_5000: The same in the 5 kHz band.
    :ivar absorption_coefficient_6300: The same in the 6.3 kHz band.
    :ivar absorption_coefficient_8000: The same in the 8 kHz band.
    :ivar absorption_coefficient_10000: The same in the 10 kHz band.
    """

    absorption_coefficient_50: float | None = None
    absorption_coefficient_63: float | None = None
    absorption_coefficient_80: float | None = None
    absorption_coefficient_100: float | None = None
    absorption_coefficient_125: float | None = None
    absorption_coefficient_160: float | None = None
    absorption_coefficient_200: float | None = None
    absorption_coefficient_250: float | None = None
    absorption_coefficient_315: float | None = None
    absorption_coefficient_400: float | None = None
    absorption_coefficient_500: float | None = None
    absorption_coefficient_630: float | None = None
    absorption_coefficient_800: float | None = None
    absorption_coefficient_1000: float | None = None
    absorption_coefficient_1250: float | None = None
    absorption_coefficient_1600: float | None = None
    absorption_coefficient_2000: float | None = None
    absorption_coefficient_2500: float | None = None
    absorption_coefficient_3150: float | None = None
    absorption_coefficient_4000: float | None = None
    absorption_coefficient_5000: float | None = None
    absorption_coefficient_6300: float | None = None
    absorption_coefficient_8000: float | None = None
    absorption_coefficient_10000: float | None = None

    _bands_hz: ClassVar[tuple[int, ...]] = _THIRD_OCTAVE_BANDS_HZ
    _bands_per_octave: ClassVar[int] = 3
    _band_prefix: ClassVar[str] = "absorption_coefficient_"
    _band_kind: ClassVar[str] = "a one-third octave"
    _table_kind: ClassVar[str] = "one-third-octave absorption"

    def absorption_coefficient(self, band_hz: int) -> float:
        r"""The coefficient in one one-third octave band, or a refusal.

        :param band_hz: A one-third-octave centre frequency from 50 Hz to
            10 kHz.
        :return: The printed :math:`\alpha_\mathrm{s}`, as a float.
        :raises ValueError: when the report has no number in that band,
            naming the row, the band and what the cell held instead; or when
            *band_hz* is not one of these bands.
        """
        return self._in_band(band_hz)

    def rating(self) -> AbsorptionRatingResult:
        """The weighted sound absorption coefficient of the row's bands.

        :func:`~phonometry.materials.weighted_absorption_from_third_octave` on
        the fifteen one-third octaves from 200 Hz to 5 kHz: the practical
        coefficients of the five rating octaves (ISO 11654 Clause 4.1), then
        the reference curve shifted over them (Clause 4.2). The result keeps
        the fifteen values it was formed from. The rating the report prints
        is not consulted: :func:`phonometry.io.read_catalogue` notes when it
        differs from this one.

        :return: The :class:`~phonometry.materials.AbsorptionRatingResult`.
        :raises ValueError: for a band from 200 Hz to 5 kHz the row does not
            print, naming the row, the band and what the report had there,
            or for a negative coefficient among them.
        """
        return weighted_absorption_from_third_octave(self.values_at(THIRD_OCTAVE_BANDS))

    def _rating_if_printed(self) -> AbsorptionRatingResult | None:
        values = [getattr(self, self._band_field(band)) for band in THIRD_OCTAVE_BANDS]
        if any(value is None or value < 0 for value in values):
            return None
        return weighted_absorption_from_third_octave(values)

    def practical(self) -> PracticalAbsorptionSpectrum:
        """The row's practical coefficients, octave by octave (ISO 11654 4.1).

        Each octave from 125 Hz to 4 kHz whose three one-third octaves the
        row prints is the mean of the three, worked out to the second decimal
        and rounded in steps of 0,05, capped at 1,00, and marked in
        :attr:`~phonometry.io.CatalogueRow.derived` with the bands it comes
        from; when those bands do not share one
        :attr:`~phonometry.io.CatalogueRow.basis`, the text names the basis
        of each. An octave with a one-third octave the row does not print
        as a number stays empty, and its
        :meth:`~phonometry.io.CatalogueRow.why_missing` says it does not
        follow from the cells the row has: nothing is borrowed from a
        neighbouring band.

        The name, the source, the provenance and what the report prints
        about the specimen (the mounting, the thickness, the depth of
        construction and the printed rating, with every hedge on them) pass
        to the practical row unchanged.

        :return: A new :class:`PracticalAbsorptionSpectrum`.
        """
        cells: dict[str, Any] = {
            name: getattr(self, name) for name in (*_ROW, *_SHARED)
        }
        for hedge in (*self._number_hedges, *self._value_hedges):
            held = getattr(self, hedge)
            kept = _keep(held, self._band_prefix)
            if kept is not None:
                cells[hedge] = kept
        derived: dict[str, str] = {}
        for octave in _PRACTICAL_BANDS_HZ:
            thirds = _octave_thirds(octave)
            values = [getattr(self, self._band_field(band)) for band in thirds]
            if any(value is None for value in values):
                continue
            field_name = PracticalAbsorptionSpectrum._band_field(octave)
            cells[field_name] = _practical_round(sum(values) / 3.0)
            derived[field_name] = self._how(thirds)
        cells["derived"] = {**cells.get("derived", {}), **derived}
        return PracticalAbsorptionSpectrum(**cells)

    def _how(self, thirds: tuple[int, int, int]) -> str:
        """The derived text of one practical octave, naming mixed bases."""
        low, centre, high = thirds
        how = (
            f"from the one-third-octave coefficients at {low}, {centre} and "
            f"{high} Hz, averaged, rounded in steps of 0.05 and capped at 1.00 "
            "(ISO 11654 Clause 4.1)"
        )
        fields = [self._band_field(band) for band in thirds]
        bases = [self.basis_of(name) for name in fields]
        if len(set(bases)) > 1:
            words = [f"the coefficient at {band} Hz" for band in thirds]
            how = f"{how}; {_bases_named(words, bases)}"
        return how

    def _catalogue_notes(self) -> tuple[str, ...]:
        r"""A printed rating that is off the grid or that the bands do not give.

        The one-third-octave coefficients themselves are measured values with
        no grid and no ceiling, so only the printed :math:`\alpha_\mathrm{w}`
        is checked against the 0,05 steps, and, when the row prints the
        fifteen bands from 200 Hz to 5 kHz, the printed rating against the
        one they give.
        """
        return tuple(self._rating_notes())


def _octave_thirds(octave: int) -> tuple[int, int, int]:
    """The three one-third octaves inside an octave, in hertz."""
    index = _THIRD_OCTAVE_BANDS_HZ.index(octave)
    return (
        _THIRD_OCTAVE_BANDS_HZ[index - 1],
        octave,
        _THIRD_OCTAVE_BANDS_HZ[index + 1],
    )


def _keep(held: object, prefix: str) -> object:
    """A hedge with its entries on one-third-octave bands left out, or ``None``.

    The practical row has no one-third-octave band, so a hedge on one of
    them has nothing to stand on there; a hedge on a field the two rows
    share, or on the row or the table, passes unchanged.
    """
    if not held:
        return None
    if isinstance(held, frozenset):
        return frozenset(name for name in held if not name.startswith(prefix))
    mapping: Mapping[str, Any] = held  # type: ignore[assignment]
    return {key: value for key, value in mapping.items() if not key.startswith(prefix)}
