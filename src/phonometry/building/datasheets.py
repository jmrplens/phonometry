#  Copyright (c) 2026. Jose Manuel Requena Plens
r"""Sound insulation as a data sheet or a test report prints it.

The transmission loss tables of the books
(:mod:`~phonometry.building.catalogue`) print a field-incidence loss per
octave, rarely with a standard or a laboratory behind it. A product's data
sheet and a laboratory's test report print two quantities that are measured
to a standard and rated to another, and that are held here in a class each:

* the **sound reduction index** :math:`R` of an element measured in a
  laboratory to ISO 10140-2, one value per one-third octave band, rated to
  :math:`R_\mathrm{w}` with its spectrum adaptation terms :math:`C` and
  :math:`C_\mathrm{tr}` (ISO 717-1), and to the terms of the enlarged
  frequency ranges of its Annex B when the report prints the bands they
  need: :class:`SoundReductionSpectrum`;
* the **reduction of impact sound pressure level** :math:`\Delta L` of a
  floor covering or a floating floor measured to ISO 10140-3, one value per
  one-third octave band, rated to :math:`\Delta L_\mathrm{w}` against the
  heavyweight reference floor of ISO 717-2, with the adaptation terms
  :math:`C_{\mathrm{I},\Delta}` and :math:`C_\mathrm{I,r}` of its Clause A.2.2:
  :class:`ImpactImprovementSpectrum`.

A book's transmission loss is not a laboratory's :math:`R`, and a covering's
:math:`\Delta L_\mathrm{w}` is not the averaged improvement some handbooks
print (:attr:`~phonometry.building.ImpactInsulation.impact_sound_improvement_db`
is one): each quantity has its own class and its own field names, so the
mistake of taking one for the other shows at the call.

Each row carries the ratings the sheet prints beside the bands, as printed,
and works them out again from the bands with its ``rating()``. When a
catalogue file is read, :func:`phonometry.io.read_catalogue` compares the
two and notes any difference beside the catalogue; it never reconciles
them. A rating the sheet prints and no function of this library works out
(a flanking level difference, an STC or an IIC) has no field here: it goes
in the row's :attr:`~phonometry.io.CatalogueRow.note`.

Nothing here ships with data. A caller's own catalogue holds these rows,
read by :func:`phonometry.io.read_catalogue` from the file the caller typed
from the sheet.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar

from .._internal.catalogue import BandedRow
from .measurement.ratings import (
    _FREQ_THIRD_OCTAVE,
    ExtendedWeightedRatingResult,
    ImpactImprovementRatingResult,
    _impact_improvement_rating,
    weighted_rating_extended,
)

__all__ = ["ImpactImprovementSpectrum", "SoundReductionSpectrum"]

#: The one-third octave bands a laboratory report of ISO 10140 prints, in
#: hertz: the 100 Hz to 5 kHz of the standard and the three bands below it
#: that the enlarged ranges of ISO 717-1 Annex B and ISO 717-2 A.2.1 read.
_BANDS_HZ: tuple[int, ...] = (
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
)

#: The 16 one-third octaves 100 Hz to 3150 Hz every ISO 717 rating reads.
_RATING_BANDS_HZ: tuple[int, ...] = tuple(round(band) for band in _FREQ_THIRD_OCTAVE)


def _differs(printed: float, worked_out: float) -> bool:
    """Whether a printed rating is not the one worked out, on its digits."""
    return Decimal(repr(printed)) != Decimal(repr(worked_out))


def _disagreement(what: str, printed: float, worked_out: float, where: str) -> str:
    """The note for one printed rating the bands do not give."""
    return (
        f"{what} is printed as {printed!r} and the bands give {worked_out!r} "
        f"({where}); the printed value is kept as printed"
    )


@dataclass(frozen=True, kw_only=True)
class SoundReductionSpectrum(BandedRow):
    r"""One element of a laboratory report, with its sound reduction index.

    The sound reduction index :math:`R` of ISO 10140-2, measured between two
    rooms with the flanking paths suppressed, one value per one-third octave
    band from 50 Hz to 5 kHz as the report prints them, and the single
    numbers of ISO 717-1 printed beside them. :meth:`rating` rates the bands
    again; the printed numbers stay as printed.

    :ivar sound_reduction_index_50_db: :math:`R` in the 50 Hz one-third
        octave band, in decibels, as printed.
    :ivar sound_reduction_index_63_db: The same in the 63 Hz band.
    :ivar sound_reduction_index_80_db: The same in the 80 Hz band.
    :ivar sound_reduction_index_100_db: The same in the 100 Hz band.
    :ivar sound_reduction_index_125_db: The same in the 125 Hz band.
    :ivar sound_reduction_index_160_db: The same in the 160 Hz band.
    :ivar sound_reduction_index_200_db: The same in the 200 Hz band.
    :ivar sound_reduction_index_250_db: The same in the 250 Hz band.
    :ivar sound_reduction_index_315_db: The same in the 315 Hz band.
    :ivar sound_reduction_index_400_db: The same in the 400 Hz band.
    :ivar sound_reduction_index_500_db: The same in the 500 Hz band.
    :ivar sound_reduction_index_630_db: The same in the 630 Hz band.
    :ivar sound_reduction_index_800_db: The same in the 800 Hz band.
    :ivar sound_reduction_index_1000_db: The same in the 1 kHz band.
    :ivar sound_reduction_index_1250_db: The same in the 1.25 kHz band.
    :ivar sound_reduction_index_1600_db: The same in the 1.6 kHz band.
    :ivar sound_reduction_index_2000_db: The same in the 2 kHz band.
    :ivar sound_reduction_index_2500_db: The same in the 2.5 kHz band.
    :ivar sound_reduction_index_3150_db: The same in the 3.15 kHz band.
    :ivar sound_reduction_index_4000_db: The same in the 4 kHz band.
    :ivar sound_reduction_index_5000_db: The same in the 5 kHz band.
    :ivar weighted_sound_reduction_index_db: The weighted sound reduction
        index :math:`R_\mathrm{w}` the report prints, in decibels
        (ISO 717-1 Clause 4.4).
    :ivar spectrum_adaptation_term_db: :math:`C`, the adaptation term for
        spectrum No. 1 (pink noise), in decibels (Clause 4.5).
    :ivar traffic_spectrum_adaptation_term_db: :math:`C_\mathrm{tr}`, the
        adaptation term for spectrum No. 2 (urban traffic), in decibels.
    :ivar spectrum_adaptation_term_50_3150_db: :math:`C_{50-3150}` of
        ISO 717-1 Annex B, in decibels.
    :ivar spectrum_adaptation_term_50_5000_db: :math:`C_{50-5000}`.
    :ivar spectrum_adaptation_term_100_5000_db: :math:`C_{100-5000}`.
    :ivar traffic_spectrum_adaptation_term_50_3150_db:
        :math:`C_{\mathrm{tr},50-3150}`.
    :ivar traffic_spectrum_adaptation_term_50_5000_db:
        :math:`C_{\mathrm{tr},50-5000}`.
    :ivar traffic_spectrum_adaptation_term_100_5000_db:
        :math:`C_{\mathrm{tr},100-5000}`.
    :ivar surface_density_kg_m2: The mass per unit area of the element, in
        kilograms per square metre, as the report prints it.
    :ivar thickness_mm: The overall thickness of the element, in
        millimetres.
    :ivar construction: The build-up the report describes, as it describes
        it: the leaves, the studs, the cavity and what fills it.
    """

    sound_reduction_index_50_db: float | None = None
    sound_reduction_index_63_db: float | None = None
    sound_reduction_index_80_db: float | None = None
    sound_reduction_index_100_db: float | None = None
    sound_reduction_index_125_db: float | None = None
    sound_reduction_index_160_db: float | None = None
    sound_reduction_index_200_db: float | None = None
    sound_reduction_index_250_db: float | None = None
    sound_reduction_index_315_db: float | None = None
    sound_reduction_index_400_db: float | None = None
    sound_reduction_index_500_db: float | None = None
    sound_reduction_index_630_db: float | None = None
    sound_reduction_index_800_db: float | None = None
    sound_reduction_index_1000_db: float | None = None
    sound_reduction_index_1250_db: float | None = None
    sound_reduction_index_1600_db: float | None = None
    sound_reduction_index_2000_db: float | None = None
    sound_reduction_index_2500_db: float | None = None
    sound_reduction_index_3150_db: float | None = None
    sound_reduction_index_4000_db: float | None = None
    sound_reduction_index_5000_db: float | None = None
    weighted_sound_reduction_index_db: float | None = None
    spectrum_adaptation_term_db: float | None = None
    traffic_spectrum_adaptation_term_db: float | None = None
    spectrum_adaptation_term_50_3150_db: float | None = None
    spectrum_adaptation_term_50_5000_db: float | None = None
    spectrum_adaptation_term_100_5000_db: float | None = None
    traffic_spectrum_adaptation_term_50_3150_db: float | None = None
    traffic_spectrum_adaptation_term_50_5000_db: float | None = None
    traffic_spectrum_adaptation_term_100_5000_db: float | None = None
    surface_density_kg_m2: float | None = None
    thickness_mm: float | None = None
    construction: str = ""

    _bands_hz: ClassVar[tuple[int, ...]] = _BANDS_HZ
    _bands_per_octave: ClassVar[int] = 3
    _band_prefix: ClassVar[str] = "sound_reduction_index_"
    _band_suffix: ClassVar[str] = "_db"
    _band_kind: ClassVar[str] = "a one-third octave"
    _table_kind: ClassVar[str] = "sound reduction index"

    #: The printed single numbers :meth:`_catalogue_notes` compares, with
    #: the attribute of :class:`~phonometry.building.ExtendedWeightedRatingResult`
    #: each is worked out as and the clause that defines it.
    _RATINGS: ClassVar[tuple[tuple[str, str, str, str], ...]] = (
        ("weighted_sound_reduction_index_db", "rating", "Rw", "ISO 717-1 Clause 4.4"),
        ("spectrum_adaptation_term_db", "c", "C", "ISO 717-1 Clause 4.5"),
        ("traffic_spectrum_adaptation_term_db", "ctr", "Ctr", "ISO 717-1 Clause 4.5"),
        ("spectrum_adaptation_term_50_3150_db", "c_50_3150", "C50-3150", "Annex B"),
        ("spectrum_adaptation_term_50_5000_db", "c_50_5000", "C50-5000", "Annex B"),
        ("spectrum_adaptation_term_100_5000_db", "c_100_5000", "C100-5000", "Annex B"),
        (
            "traffic_spectrum_adaptation_term_50_3150_db",
            "ctr_50_3150",
            "Ctr,50-3150",
            "Annex B",
        ),
        (
            "traffic_spectrum_adaptation_term_50_5000_db",
            "ctr_50_5000",
            "Ctr,50-5000",
            "Annex B",
        ),
        (
            "traffic_spectrum_adaptation_term_100_5000_db",
            "ctr_100_5000",
            "Ctr,100-5000",
            "Annex B",
        ),
    )

    def sound_reduction_index_db(self, band_hz: int) -> float:
        """The sound reduction index in one band, or a refusal.

        :param band_hz: A one-third-octave centre frequency from 50 Hz to
            5 kHz.
        :return: The printed :math:`R`, in decibels.
        :raises ValueError: when the report has no number in that band,
            naming the row, the band and what the cell held instead; or when
            *band_hz* is not one of these bands.
        """
        return self._in_band(band_hz)

    def rating(self) -> ExtendedWeightedRatingResult:
        r"""The single numbers of ISO 717-1 worked out from the row's bands.

        :func:`~phonometry.building.weighted_rating_extended` on every band
        the row prints: :math:`R_\mathrm{w}`, :math:`C` and
        :math:`C_\mathrm{tr}` from the 16 one-third octaves 100 Hz to
        3150 Hz (Clauses 4.4 and 4.5), which the result also carries as the
        :func:`~phonometry.building.weighted_rating` of those bands in its
        ``core``, and each adaptation term of Annex B whose range the row
        prints every band of. A term whose range has a band the row does not
        print is ``None``: nothing is filled in to reach it.

        :return: The :class:`~phonometry.building.ExtendedWeightedRatingResult`.
        :raises ValueError: for a band from 100 Hz to 3150 Hz the row does
            not print, naming the row, the band and what the report had
            there.
        """
        self.values_at(_RATING_BANDS_HZ)
        bands = self.bands()
        values = [self.printed(self._band_field(band)) for band in bands]
        return weighted_rating_extended(values, bands)

    def _catalogue_notes(self) -> tuple[str, ...]:
        """Printed single numbers the bands do not give.

        When the row prints the 16 bands from 100 Hz to 3150 Hz, each single
        number it prints is compared with the one :meth:`rating` works out,
        on the digits the report prints, and every difference is noted.
        Nothing is changed.
        """
        if any(getattr(self, self._band_field(b)) is None for b in _RATING_BANDS_HZ):
            return ()
        rating = self.rating()
        notes: list[str] = []
        for field_name, attribute, symbol, where in self._RATINGS:
            printed = getattr(self, field_name)
            worked_out = getattr(rating, attribute)
            if printed is None or worked_out is None:
                continue
            if _differs(printed, worked_out):
                notes.append(_disagreement(symbol, printed, worked_out, where))
        return tuple(notes)


@dataclass(frozen=True, kw_only=True)
class ImpactImprovementSpectrum(BandedRow):
    r"""One covering or floating floor of a report, with its :math:`\Delta L`.

    The reduction of impact sound pressure level :math:`\Delta L` of
    ISO 10140-3, the difference a floor covering or a floating floor makes
    to the impact level of a heavyweight floor, one value per one-third
    octave band from 50 Hz to 5 kHz as the report prints them, and the
    single numbers of ISO 717-2 printed beside them. :meth:`rating` rates
    the bands again; the printed numbers stay as printed.

    :math:`\Delta L_\mathrm{w}` has a field of its own because it is a
    rating against the reference floor of ISO 717-2 Table 4, not a mean over
    frequency: a handbook's averaged improvement is another quantity, and
    this class never reads it.

    :ivar impact_improvement_50_db: :math:`\Delta L` in the 50 Hz one-third
        octave band, in decibels, as printed.
    :ivar impact_improvement_63_db: The same in the 63 Hz band.
    :ivar impact_improvement_80_db: The same in the 80 Hz band.
    :ivar impact_improvement_100_db: The same in the 100 Hz band.
    :ivar impact_improvement_125_db: The same in the 125 Hz band.
    :ivar impact_improvement_160_db: The same in the 160 Hz band.
    :ivar impact_improvement_200_db: The same in the 200 Hz band.
    :ivar impact_improvement_250_db: The same in the 250 Hz band.
    :ivar impact_improvement_315_db: The same in the 315 Hz band.
    :ivar impact_improvement_400_db: The same in the 400 Hz band.
    :ivar impact_improvement_500_db: The same in the 500 Hz band.
    :ivar impact_improvement_630_db: The same in the 630 Hz band.
    :ivar impact_improvement_800_db: The same in the 800 Hz band.
    :ivar impact_improvement_1000_db: The same in the 1 kHz band.
    :ivar impact_improvement_1250_db: The same in the 1.25 kHz band.
    :ivar impact_improvement_1600_db: The same in the 1.6 kHz band.
    :ivar impact_improvement_2000_db: The same in the 2 kHz band.
    :ivar impact_improvement_2500_db: The same in the 2.5 kHz band.
    :ivar impact_improvement_3150_db: The same in the 3.15 kHz band.
    :ivar impact_improvement_4000_db: The same in the 4 kHz band.
    :ivar impact_improvement_5000_db: The same in the 5 kHz band.
    :ivar weighted_impact_improvement_db: The weighted reduction of impact
        sound pressure level :math:`\Delta L_\mathrm{w}` the report prints,
        in decibels (ISO 717-2 Formulae (1) and (2)). It is what
        :func:`~phonometry.building.predicted_impact_insulation` takes as
        ``delta_l_w``, through
        :meth:`~phonometry.io.CatalogueRow.printed`.
    :ivar reference_floor_adaptation_term_db: :math:`C_\mathrm{I,r}`, the
        spectrum adaptation term of the reference floor with the covering
        (ISO 717-2 Clause A.2.2), in decibels, which data sheets of floating
        floor layers print beside :math:`\Delta L_\mathrm{w}`.
    :ivar impact_improvement_adaptation_term_db:
        :math:`C_{\mathrm{I},\Delta}`, the spectrum adaptation term of the
        covering (Clause A.2.2, Formula (A.4)), in decibels.
    """

    impact_improvement_50_db: float | None = None
    impact_improvement_63_db: float | None = None
    impact_improvement_80_db: float | None = None
    impact_improvement_100_db: float | None = None
    impact_improvement_125_db: float | None = None
    impact_improvement_160_db: float | None = None
    impact_improvement_200_db: float | None = None
    impact_improvement_250_db: float | None = None
    impact_improvement_315_db: float | None = None
    impact_improvement_400_db: float | None = None
    impact_improvement_500_db: float | None = None
    impact_improvement_630_db: float | None = None
    impact_improvement_800_db: float | None = None
    impact_improvement_1000_db: float | None = None
    impact_improvement_1250_db: float | None = None
    impact_improvement_1600_db: float | None = None
    impact_improvement_2000_db: float | None = None
    impact_improvement_2500_db: float | None = None
    impact_improvement_3150_db: float | None = None
    impact_improvement_4000_db: float | None = None
    impact_improvement_5000_db: float | None = None
    weighted_impact_improvement_db: float | None = None
    reference_floor_adaptation_term_db: float | None = None
    impact_improvement_adaptation_term_db: float | None = None

    _bands_hz: ClassVar[tuple[int, ...]] = _BANDS_HZ
    _bands_per_octave: ClassVar[int] = 3
    _band_prefix: ClassVar[str] = "impact_improvement_"
    _band_suffix: ClassVar[str] = "_db"
    _band_kind: ClassVar[str] = "a one-third octave"
    _table_kind: ClassVar[str] = "impact improvement"

    #: The printed single numbers :meth:`_catalogue_notes` compares, with
    #: the attribute of
    #: :class:`~phonometry.building.ImpactImprovementRatingResult` each is
    #: worked out as.
    _RATINGS: ClassVar[tuple[tuple[str, str, str, str], ...]] = (
        (
            "weighted_impact_improvement_db",
            "delta_lw",
            "ΔLw",
            "ISO 717-2 Formula (2)",
        ),
        (
            "impact_improvement_adaptation_term_db",
            "ci_delta",
            "CI,Δ",
            "ISO 717-2 Formula (A.4)",
        ),
        (
            "reference_floor_adaptation_term_db",
            "ci_r",
            "CI,r",
            "ISO 717-2 Clause A.2.2",
        ),
    )

    def impact_improvement_db(self, band_hz: int) -> float:
        r"""The reduction of impact level in one band, or a refusal.

        :param band_hz: A one-third-octave centre frequency from 50 Hz to
            5 kHz.
        :return: The printed :math:`\Delta L`, in decibels.
        :raises ValueError: when the report has no number in that band,
            naming the row, the band and what the cell held instead; or when
            *band_hz* is not one of these bands.
        """
        return self._in_band(band_hz)

    def rating(self) -> ImpactImprovementRatingResult:
        r"""The single numbers of ISO 717-2 worked out from the row's bands.

        :func:`~phonometry.building.weighted_impact_improvement` and
        :func:`~phonometry.building.impact_improvement_adaptation_term` on
        the 16 one-third octaves 100 Hz to 3150 Hz, and
        :math:`C_\mathrm{I,r} = C_\mathrm{I,r,0} - C_{\mathrm{I},\Delta}`
        with :math:`C_\mathrm{I,r,0} = -11` dB (Clause A.2.2).

        :return: The
            :class:`~phonometry.building.ImpactImprovementRatingResult`.
        :raises ValueError: for a band from 100 Hz to 3150 Hz the row does
            not print, naming the row, the band and what the report had
            there.
        """
        return _impact_improvement_rating(self.values_at(_RATING_BANDS_HZ))

    def _catalogue_notes(self) -> tuple[str, ...]:
        """Printed single numbers the bands do not give.

        When the row prints the 16 bands from 100 Hz to 3150 Hz, each single
        number it prints is compared with the one :meth:`rating` works out,
        on the digits the report prints, and every difference is noted.
        Nothing is changed.
        """
        if any(getattr(self, self._band_field(b)) is None for b in _RATING_BANDS_HZ):
            return ()
        rating = self.rating()
        return tuple(
            _disagreement(symbol, printed, getattr(rating, attribute), where)
            for field_name, attribute, symbol, where in self._RATINGS
            if (printed := getattr(self, field_name)) is not None
            and _differs(printed, getattr(rating, attribute))
        )
