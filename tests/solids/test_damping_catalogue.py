#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The commercial damping materials, against a second reading of the page.

The catalogue and the oracle in :mod:`tests.reference_data.damping` were
transcribed from the rendered page by two readers who never saw each other's
work, and compared cell by cell before either was kept. These tests keep that
comparison alive, and add the two things the transcription cannot say by
itself: that the conversion out of the page's degrees Fahrenheit and pounds
per square inch is the exact one and not the rounded factor the book's own
footnote offers, and that a loss factor here is never served without the
temperature and the frequency that locate it.
"""

from __future__ import annotations

import math

import pytest
import reference_data as ref

from phonometry import solids
from phonometry.solids import PUBLISHED_DAMPING, DampingMaterial, damping_named

#: The table this catalogue is read from, as the key spells it.
TABLE = "ver-beranek-2006-table-14-1"

#: Pascals in one pound-force per square inch, by definition.
PASCAL_PER_PSI = 6894.757293168361

#: How the oracle's columns map onto the fields of the row class.
FIELDS = {
    "ηmax": "max_loss_factor",
    "10 Hz": "peak_temperature_at_10_hz_c",
    "100 Hz": "peak_temperature_at_100_hz_c",
    "1000 Hz": "peak_temperature_at_1000_hz_c",
    "Emax": "youngs_modulus_max_pa",
    "Emin": "youngs_modulus_min_pa",
    "Etrans": "youngs_modulus_transition_pa",
    "EI,max": "loss_modulus_max_pa",
}


def _printed(text: str) -> float | None:
    """The oracle cell as a number, or ``None`` when the page corrupted it."""
    try:
        return float(text.replace("−", "-"))
    except ValueError:
        return None


def _row(name: str) -> DampingMaterial:
    return next(row for row in PUBLISHED_DAMPING.values() if row.name == name)


# ---------------------------------------------------------------------------
# The transcription against the second reading
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_every_row_of_the_table() -> None:
    assert len(PUBLISHED_DAMPING) == len(ref.VER_BERANEK_14_1) == 17


def test_the_rows_are_in_the_order_the_page_prints_them() -> None:
    names = [row.name for row in PUBLISHED_DAMPING.values()]
    assert names == [name for name, _values in ref.VER_BERANEK_14_1]


@pytest.mark.parametrize(
    ("name", "values"),
    ref.VER_BERANEK_14_1,
    ids=[name for name, _v in ref.VER_BERANEK_14_1],
)
def test_every_cell_is_the_printed_one_converted_exactly(
    name: str, values: tuple[str, ...]
) -> None:
    """Cell by cell, out of the page's own units and into the library's.

    The conversion is checked here rather than trusted, because it is the one
    step between the page and the catalogue that no second reader saw.
    """
    row = _row(name)
    for column, text in zip(ref.VER_BERANEK_14_1_COLUMNS, values, strict=True):
        field = FIELDS[column]
        printed = _printed(text)
        if printed is None:
            assert getattr(row, field) is None
            assert text in row.why_missing(field)
            continue
        held = getattr(row, field)
        if column.endswith("Hz"):
            assert held == pytest.approx((printed - 32.0) * 5.0 / 9.0, abs=1e-6)
        elif column.startswith("E"):
            assert held == pytest.approx(printed * PASCAL_PER_PSI, rel=1e-8)
        else:
            assert held == printed


#: Every field of this table whose value the library worked out of the units
#: the page prints, which is every field except the dimensionless loss factor.
CONVERTED_FIELDS = (
    "peak_temperature_at_10_hz_c",
    "peak_temperature_at_100_hz_c",
    "peak_temperature_at_1000_hz_c",
    "youngs_modulus_max_pa",
    "youngs_modulus_min_pa",
    "youngs_modulus_transition_pa",
    "loss_modulus_max_pa",
)


def test_the_converted_cells_keep_the_figure_the_page_prints() -> None:
    """A degree Celsius converted from the page is never served as a reading.

    Every cell of this table but the loss factor is a value converted out of
    degrees Fahrenheit or pounds per square inch, and ``converted`` is what
    stops it being read as a figure off the page: it keeps the printed figure
    and its unit beside the value, and the published table reads it as a
    conversion. It is not a derivation, because the number is the page's,
    so ``is_derived`` answers ``False``. The marker is asserted on every
    converted cell of every row rather than on a sample, and the figure it
    keeps is converted again here and compared with the value held, so a
    marker that drifted from its cell would fail too.
    """
    checked = 0
    for row in PUBLISHED_DAMPING.values():
        assert "max_loss_factor" not in row.converted, row.name
        for field in CONVERTED_FIELDS:
            if getattr(row, field) is None:
                # A cell the page corrupted is refused, not converted.
                assert row.why_missing(field), f"{row.name}.{field}"
                continue
            assert not row.is_derived(field), f"{row.name}.{field}"
            figure, unit = row.converted[field]
            printed = float(figure.replace("−", "-"))
            if field.endswith("_c"):
                assert unit == "°F", f"{row.name}.{field}"
                expected = (printed - 32.0) * 5.0 / 9.0
                assert getattr(row, field) == pytest.approx(expected, abs=1e-6)
            else:
                assert unit == "psi", f"{row.name}.{field}"
                expected = printed * PASCAL_PER_PSI
                assert getattr(row, field) == pytest.approx(expected, rel=1e-8)
            checked += 1
    assert checked == 116


def test_the_books_rounded_conversion_factor_is_not_the_one_used() -> None:
    """The footnote offers 7e3 Pa/psi, which is 1.5 per cent above the psi.

    Using it would put every modulus in this table 1.5 per cent high, which is
    larger than the last digit the page prints, so the difference is not
    academic.
    """
    rounded = 7e3
    assert rounded / PASCAL_PER_PSI == pytest.approx(1.0153, abs=5e-4)
    row = _row("Antiphon-13")
    printed_psi = 3e5
    assert row.youngs_modulus_max_pa == pytest.approx(
        printed_psi * PASCAL_PER_PSI, rel=1e-6
    )
    assert row.youngs_modulus_max_pa != pytest.approx(printed_psi * rounded, rel=1e-4)


# ---------------------------------------------------------------------------
# A loss factor here is never alone
# ---------------------------------------------------------------------------
def test_every_row_locates_its_peak_at_all_three_printed_frequencies() -> None:
    for row in PUBLISHED_DAMPING.values():
        assert row.max_loss_factor is not None
        for frequency in (10, 100, 1000):
            assert isinstance(row.peak_temperature_c(frequency), float)


def test_the_peak_temperature_rises_with_frequency_in_every_row() -> None:
    """The band where a polymer dissipates moves up as it is worked faster.

    Seventeen rows and no exception: a row that went the other way would be a
    transcription defect or a misprint, and this is the cheapest check on the
    table there is.
    """
    for row in PUBLISHED_DAMPING.values():
        at_10 = row.peak_temperature_c(10)
        at_100 = row.peak_temperature_c(100)
        at_1000 = row.peak_temperature_c(1000)
        assert at_10 < at_100 < at_1000, row.name


def test_a_frequency_the_table_does_not_print_is_refused() -> None:
    row = _row("Antiphon-13")
    with pytest.raises(ValueError, match="no peak temperature at 500 Hz"):
        row.peak_temperature_c(500)


@pytest.mark.parametrize("frequency", [float("inf"), float("-inf"), float("nan")])
def test_a_frequency_that_is_not_a_number_is_refused_the_same_way(
    frequency: float,
) -> None:
    """Infinity is refused by this catalogue, not by the integer conversion.

    The method documents ``ValueError`` and nothing else, and a caller who
    wraps it accordingly has to catch every refusal. Converting the frequency
    to an integer before looking at it raised ``OverflowError`` for infinity,
    which that caller does not catch, and for a NaN a ``ValueError`` whose
    message was about integer conversion rather than about the table.
    """
    row = _row("Antiphon-13")
    with pytest.raises(ValueError, match="has no peak temperature at"):
        row.peak_temperature_c(frequency)


def test_the_loss_modulus_is_about_the_product_of_the_other_two() -> None:
    """``E_I,max ~ eta_max E_trans``, which the chapter prints as a relation.

    It holds within a factor of two on every row that prints all three, which
    is what a table of values read off curves can be expected to do, and it is
    an independent check on three columns at once.
    """
    checked = 0
    for row in PUBLISHED_DAMPING.values():
        if row.loss_modulus_max_pa is None:
            continue
        expected = row.max_loss_factor * row.youngs_modulus_transition_pa
        assert 0.5 <= row.loss_modulus_max_pa / expected <= 2.0, row.name
        checked += 1
    assert checked == 16


def test_the_transition_modulus_lies_between_the_two_ends() -> None:
    """``E_min <= E_trans <= E_max``, which is the page's own definition.

    The paragraph under the table calls ``E_min`` "the smallest value of E"
    and puts ``E_trans`` in the range of the loss-factor peak, between the two
    ends. One row of the printing contradicts that: 3M ISD-113 prints
    ``E_trans`` below its own ``E_min``, and neither cell can be corrected
    from the page, so both are served as printed and the row carries a note.
    It is named here rather than skipped, so that the exception stays a
    documented one and a second row acquiring the same defect goes red.
    """
    contradicted = {"3M ISD-113"}
    seen = set()
    checked = 0
    for row in PUBLISHED_DAMPING.values():
        ends = (row.youngs_modulus_min_pa, row.youngs_modulus_max_pa)
        if row.youngs_modulus_transition_pa is None or None in ends:
            continue
        low, high = ends
        if not low <= row.youngs_modulus_transition_pa <= high:
            seen.add(row.name)
            continue
        checked += 1
    assert seen == contradicted
    assert checked == 14


# ---------------------------------------------------------------------------
# What the page could not say
# ---------------------------------------------------------------------------
def test_the_three_corrupted_cells_are_refused_and_named() -> None:
    """Three cells print glyphs that are not a number in the table's notation.

    They are held as misprinted, so the row keeps what the book says while
    refusing to serve it as a value.
    """
    corrupted = {
        row.name: field
        for row in PUBLISHED_DAMPING.values()
        for field in row.misprinted
    }
    assert corrupted == {
        "Antiphon-13": "loss_modulus_max_pa",
        "Soundcoat DYAD 606": "youngs_modulus_max_pa",
        "GE SMRD": "youngs_modulus_max_pa",
    }
    for name, field in corrupted.items():
        row = _row(name)
        assert getattr(row, field) is None
        with pytest.raises(ValueError, match="e-notation"):
            row.printed(field)


def test_the_table_says_the_values_were_read_off_curves() -> None:
    row = _row("Antiphon-13")
    assert "TABLE 14.1" in row.source
    assert "598" in row.source


# ---------------------------------------------------------------------------
# The shape of the catalogue
# ---------------------------------------------------------------------------
def test_the_lookup_matches_a_part_of_a_name() -> None:
    assert len(damping_named("3M")) == 5
    assert damping_named("EAR") == damping_named("ear")
    assert damping_named("unobtainium") == ()


def test_the_catalogue_is_reachable_from_the_package() -> None:
    assert solids.PUBLISHED_DAMPING is PUBLISHED_DAMPING
    assert all(key.startswith(f"{TABLE}/") for key in PUBLISHED_DAMPING)


def test_the_catalogue_cannot_be_written_to() -> None:
    with pytest.raises(TypeError):
        PUBLISHED_DAMPING["x/y"] = DampingMaterial(name="x", source="nowhere")  # type: ignore[index]


def test_no_temperature_is_a_nan() -> None:
    for row in PUBLISHED_DAMPING.values():
        for frequency in (10, 100, 1000):
            assert not math.isnan(row.peak_temperature_c(frequency))
