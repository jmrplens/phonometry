#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The practical and the one-third-octave absorption rows of a data sheet.

The oracles are the printed examples of EN ISO 11654:1997: Figures A.1 and
A.2 of Annex A (PDF p. 14, folio 4) give practical coefficients and the
weighted coefficient they rate to, and Annex C (PDF p. 16, folio 6) prints
eighteen one-third-octave coefficients, whose practical coefficients are
worked out below by hand from Clause 4.1 (PDF p. 12, folio 2).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from phonometry import io, materials

if TYPE_CHECKING:
    from collections.abc import Callable

_PRACTICAL = materials.PracticalAbsorptionSpectrum
_THIRDS = materials.ThirdOctaveAbsorptionSpectrum

#: Figure A.1: 125 Hz to 4 kHz, rated alpha_w = 0,60 with no indicator.
_FIGURE_A1 = (0.20, 0.35, 0.70, 0.65, 0.60, 0.55)
#: Figure A.2: the same with 1,00 at 500 Hz, rated 0,60(M).
_FIGURE_A2 = (0.20, 0.35, 1.00, 0.65, 0.60, 0.55)

#: Annex C: alpha_s from 100 Hz to 5 kHz.
_ANNEX_C = {
    100: 0.12,
    125: 0.15,
    160: 0.17,
    200: 0.21,
    250: 0.31,
    315: 0.51,
    400: 0.54,
    500: 0.80,
    630: 0.93,
    800: 1.05,
    1000: 1.10,
    1250: 1.19,
    1600: 1.20,
    2000: 1.13,
    2500: 1.02,
    3150: 0.99,
    4000: 0.94,
    5000: 0.81,
}
#: Clause 4.1 by hand on Annex C: the means 0,1467, 0,3433, 0,7567, 1,1133,
#: 1,1167 and 0,9133 to the second decimal are 0,15, 0,34, 0,76, 1,11, 1,12
#: and 0,91; in steps of 0,05 they are 0,15, 0,35, 0,75, 1,10, 1,10 and
#: 0,90; the two above 1,00 are set to 1,00.
_ANNEX_C_PRACTICAL = {
    125: 0.15,
    250: 0.35,
    500: 0.75,
    1000: 1.00,
    2000: 1.00,
    4000: 0.90,
}
#: Clause 4.2 by hand on those: in twentieths 7, 15, 20, 20, 18 against the
#: curve 16, 20, 20, 20, 18; shifted by 7 the unfavourable sum is 2 (0,10),
#: by 6 it is 3, so alpha_w = 0,65; the excess over the shifted curve is 7
#: at 1 kHz, 2 kHz and 4 kHz, so the indicators are M and H; class C.
_ANNEX_C_RATING = ("0.65(MH)", "C")


def _practical(
    values: tuple[float, ...], **extra: Any
) -> materials.PracticalAbsorptionSpectrum:
    bands = (125, 250, 500, 1000, 2000, 4000)
    cells = {
        f"practical_absorption_coefficient_{band}": value
        for band, value in zip(bands, values, strict=True)
    }
    return _PRACTICAL(name="Panel", source="A test", **cells, **extra)


def _annex_c(**extra: Any) -> materials.ThirdOctaveAbsorptionSpectrum:
    cells = {
        f"absorption_coefficient_{band}": value for band, value in _ANNEX_C.items()
    }
    return _THIRDS(name="Annex C", source="ISO 11654 Annex C", **cells, **extra)


@pytest.mark.parametrize(
    ("values", "label"),
    [(_FIGURE_A1, "0.60"), (_FIGURE_A2, "0.60(M)")],
    ids=["figure-a1", "figure-a2"],
)
def test_the_practical_row_rates_as_annex_a_prints(
    values: tuple[float, ...], label: str
) -> None:
    rating = _practical(values).rating()
    assert rating.rating_label == label
    assert rating.absorption_class == "C"


def test_the_125_hz_band_is_held_and_never_rated() -> None:
    """ISO 11654 Clause 1: the rating starts at 250 Hz."""
    low = _practical((0.95, *_FIGURE_A1[1:])).rating()
    high = _practical((0.05, *_FIGURE_A1[1:])).rating()
    assert low.rating_label == high.rating_label == "0.60"
    assert _practical(_FIGURE_A1).practical_absorption_coefficient(125) == 0.20


def test_a_missing_rating_band_is_refused_with_what_the_sheet_had() -> None:
    gap = _PRACTICAL(
        name="Panel",
        source="A test",
        practical_absorption_coefficient_250=0.35,
        practical_absorption_coefficient_500=0.70,
        practical_absorption_coefficient_1000=0.65,
        practical_absorption_coefficient_2000=0.60,
        unquantified={"practical_absorption_coefficient_4000": "n.m."},
    )
    with pytest.raises(ValueError, match="practical_absorption_coefficient_4000"):
        gap.rating()


def test_a_value_above_one_is_kept_and_rated_as_one() -> None:
    row = _practical((0.20, 0.35, 1.05, 0.65, 0.60, 0.55))
    assert row.practical_absorption_coefficient_500 == 1.05
    assert row.rating().rating_label == "0.60(M)"


def test_the_one_third_octave_row_gives_its_practical_coefficients() -> None:
    practical = _annex_c().practical()
    assert practical.spectrum() == pytest.approx(_ANNEX_C_PRACTICAL)
    assert set(practical.derived) == {
        f"practical_absorption_coefficient_{band}" for band in _ANNEX_C_PRACTICAL
    }
    assert (
        "100, 125 and 160 Hz"
        in practical.derived["practical_absorption_coefficient_125"]
    )
    assert all(practical.is_derived(name) for name in practical.derived)


@pytest.mark.parametrize(
    "rate",
    [
        lambda row: row.rating(),
        lambda row: row.practical().rating(),
    ],
    ids=["from-thirds", "through-practical"],
)
def test_the_one_third_octave_row_rates_as_worked_by_hand(
    rate: Callable[
        [materials.ThirdOctaveAbsorptionSpectrum], materials.AbsorptionRatingResult
    ],
) -> None:
    rating = rate(_annex_c())
    assert (rating.rating_label, rating.absorption_class) == _ANNEX_C_RATING


def test_the_rating_keeps_the_fifteen_bands_it_was_formed_from() -> None:
    rating = _annex_c().rating()
    assert rating.third_octave_alpha_s is not None
    assert list(rating.third_octave_alpha_s) == [
        _ANNEX_C[band] for band in materials.THIRD_OCTAVE_BANDS
    ]


def test_an_octave_with_a_band_missing_stays_empty_and_says_why() -> None:
    cells = {f"absorption_coefficient_{b}": v for b, v in _ANNEX_C.items() if b != 160}
    row = _THIRDS(
        name="Gap",
        source="A test",
        unquantified={"absorption_coefficient_160": "n.m."},
        **cells,
    )
    practical = row.practical()
    assert practical.practical_absorption_coefficient_125 is None
    assert "practical_absorption_coefficient_125" not in practical.derived
    assert "does not follow" in practical.why_missing(
        "practical_absorption_coefficient_125"
    )
    assert practical.practical_absorption_coefficient_250 == pytest.approx(0.35)


def test_practical_carries_what_the_report_prints_about_the_specimen() -> None:
    provenance = io.Provenance(
        kind="test_report",
        document="Report 26-014",
        version=None,
        consulted="2026-09-25",
        laboratory="Example Lab",
    )
    row = _annex_c(
        variant="E-200",
        mounting="E-200",
        thickness_mm=40.0,
        construction_depth_mm=200.0,
        weighted_absorption_coefficient=0.65,
        shape_indicator="MH",
        absorption_class="C",
        approximate={"thickness_mm", "absorption_coefficient_500"},
        basis={"row": "measured", "absorption_coefficient_100": "estimated"},
        provenance=provenance,
        note="A note",
    )
    practical = row.practical()
    for name in (
        "name",
        "source",
        "variant",
        "mounting",
        "thickness_mm",
        "construction_depth_mm",
        "weighted_absorption_coefficient",
        "shape_indicator",
        "absorption_class",
        "note",
        "provenance",
    ):
        assert getattr(practical, name) == getattr(row, name), name
    assert practical.approximate == frozenset({"thickness_mm"})
    assert practical.basis == {"row": "measured"}
    assert "(estimated)" in practical.derived["practical_absorption_coefficient_125"]
    assert (
        "(estimated)" not in practical.derived["practical_absorption_coefficient_250"]
    )


def test_the_one_third_octave_row_reads_one_band_and_refuses_another() -> None:
    row = _annex_c()
    assert row.absorption_coefficient(1250) == 1.19
    assert row.values_at([158.49, 1000.0]).tolist() == [0.17, 1.10]
    with pytest.raises(ValueError, match="absorption_coefficient_50"):
        row.absorption_coefficient(50)
    with pytest.raises(ValueError, match="one-third octave band"):
        row.absorption_coefficient(900)


def test_notes_name_values_off_the_grid_and_a_rating_that_disagrees() -> None:
    """ISO 11654 Clause 4.1 steps of 0,05 and cap of 1,00, on printed digits."""
    row = _PRACTICAL(
        name="Panel 40",
        source="A test",
        practical_absorption_coefficient_250=0.25,
        practical_absorption_coefficient_500=0.83,
        practical_absorption_coefficient_1000=1.05,
        practical_absorption_coefficient_2000=1.00,
        practical_absorption_coefficient_4000=0.95,
        weighted_absorption_coefficient=0.85,
        shape_indicator="(MH)",
        absorption_class="Class B",
    )
    notes = row._catalogue_notes()
    assert len(notes) == 4
    assert "at 500 Hz is printed as 0.83, off the steps of 0.05" in notes[0]
    assert "at 1000 Hz is printed as 1.05, above the 1.00" in notes[1]
    assert "printed as 0.85 and the bands give 0.55" in notes[2]
    assert "printed as 'Class B' and the bands give 'D'" in notes[3]


def test_a_rating_that_agrees_and_a_grid_value_leave_no_note() -> None:
    row = _practical(
        _FIGURE_A2,
        weighted_absorption_coefficient=0.60,
        shape_indicator="M",
        absorption_class="C",
    )
    assert row._catalogue_notes() == ()
    assert _annex_c(weighted_absorption_coefficient=0.65)._catalogue_notes() == ()


def test_an_off_grid_weighted_coefficient_is_noted_without_the_bands() -> None:
    row = _PRACTICAL(
        name="Panel", source="A test", weighted_absorption_coefficient=0.83
    )
    (note,) = row._catalogue_notes()
    assert "weighted coefficient is printed as 0.83, off the steps" in note
    (third,) = _THIRDS(
        name="Panel", source="A test", weighted_absorption_coefficient=1.05
    )._catalogue_notes()
    assert "above the 1.00" in third


def test_a_one_third_octave_value_above_one_is_not_a_note() -> None:
    """ISO 354 alpha_s is referred to the specimen area and exceeds 1."""
    assert _annex_c()._catalogue_notes() == ()


def test_a_printed_shape_indicator_that_disagrees_is_noted() -> None:
    row = _practical(_FIGURE_A1, shape_indicator="L")
    (note,) = row._catalogue_notes()
    assert "shape indicator is printed as 'L' and the bands give none" in note
