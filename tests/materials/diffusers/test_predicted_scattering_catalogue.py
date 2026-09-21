#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The predicted scattering coefficients, against a second reading of the pages.

The catalogue and the oracle in :mod:`tests.reference_data.predicted_scattering`
were transcribed from the rendered pages by two readers who never saw each
other's work, and compared cell by cell before either was kept. These tests
keep that comparison alive, and add the shape: that a prediction is never
filed with a measurement, that the two three-dimensional tables print no band
below 250 Hz and say so, and that the summary row each group closes with is a
row and not a heading.
"""

from __future__ import annotations

import pytest
import reference_data as ref

from phonometry.materials.diffusers import (
    PUBLISHED_PREDICTED_SCATTERING,
    PUBLISHED_SCATTERING,
    PredictedScatteringSpectrum,
    ScatteringCoefficientSpectrum,
    predicted_scattering_named,
)

#: The three tables of the appendix, keyed the way the catalogue keys them.
C1, C2, C3 = "cox-2017-table-c1", "cox-2017-table-c2", "cox-2017-table-c3"

#: How the page heads each angle line of Table C.3, and the variant it is
#: filed under.
ANGLES = {
    "0": "normal",
    "56.9": "56.9 degrees",
    "Random": "random",
    "All/any": "any angle",
}


def _rows(table: str) -> list[PredictedScatteringSpectrum]:
    """Every row of one table, in catalogue order."""
    return [
        row
        for key, row in PUBLISHED_PREDICTED_SCATTERING.items()
        if key.startswith(table)
    ]


# ---------------------------------------------------------------------------
# The transcription against the second reading
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_every_line_of_all_three_tables() -> None:
    """Eighteen rows, twenty-two rows, and twenty-seven surfaces of three lines."""
    assert len(_rows(C1)) == len(ref.COX_C1_SCATTERING) == 18
    assert len(_rows(C2)) == len(ref.COX_C2_SCATTERING) == 22
    assert len(ref.COX_C3_SCATTERING) == 27
    assert len(_rows(C3)) == 79
    assert len(PUBLISHED_PREDICTED_SCATTERING) == 119


@pytest.mark.parametrize(
    ("table", "oracle"),
    [(C1, ref.COX_C1_SCATTERING), (C2, ref.COX_C2_SCATTERING)],
    ids=["C.1", "C.2"],
)
def test_the_three_dimensional_tables_hold_what_the_second_reader_read(
    table: str,
    oracle: tuple[tuple[str, str, tuple[float, ...]], ...],
) -> None:
    """Cell by cell, in printed order, under the heading of each group.

    Order is the check here rather than a lookup, because one row of Table C.2
    is printed twice on one page with the same description and the same
    values, and a lookup by name would not notice if one of them were dropped.
    """
    for (group, surface, values), row in zip(oracle, _rows(table), strict=True):
        assert (row.group, row.name) == (group, surface)
        held = tuple(
            getattr(row, f"scattering_coefficient_{band}")
            for band in ref.COX_C_FLAT_BANDS_HZ
        )
        assert held == tuple(values)


@pytest.mark.parametrize(
    ("section", "surface", "angles"),
    ref.COX_C3_SCATTERING,
    ids=[f"{surface[:38]}" for _s, surface, _a in ref.COX_C3_SCATTERING],
)
def test_the_two_dimensional_table_holds_what_the_second_reader_read(
    section: str,
    surface: str,
    angles: dict[str, tuple[float, ...]],
) -> None:
    for printed_angle, values in angles.items():
        matches = [
            row
            for row in _rows(C3)
            if row.name == surface
            and row.group == section
            and row.variant == ANGLES[printed_angle]
        ]
        assert len(matches) == 1, f"{surface!r} at {printed_angle}"
        held = tuple(
            getattr(matches[0], f"scattering_coefficient_{band}")
            for band in ref.COX_C_WIDE_BANDS_HZ
        )
        assert held == tuple(values)


# ---------------------------------------------------------------------------
# A prediction is not a measurement
# ---------------------------------------------------------------------------
def test_predicted_rows_are_never_filed_with_measured_ones() -> None:
    """Two catalogues, two classes, and no key in common.

    A row that reads 0.45 because a solver said so and a row that reads 0.45
    because a reverberation room said so are not interchangeable, and a caller
    who mixed them would have no way of telling afterwards.
    """
    assert not set(PUBLISHED_PREDICTED_SCATTERING) & set(PUBLISHED_SCATTERING)
    assert all(
        isinstance(row, PredictedScatteringSpectrum)
        for row in PUBLISHED_PREDICTED_SCATTERING.values()
    )
    assert not any(
        isinstance(row, PredictedScatteringSpectrum)
        for row in PUBLISHED_SCATTERING.values()
    )
    assert all(
        isinstance(row, ScatteringCoefficientSpectrum)
        for row in PUBLISHED_SCATTERING.values()
    )


def test_every_row_says_which_solver_produced_it() -> None:
    models = {row.model for row in PUBLISHED_PREDICTED_SCATTERING.values()}
    assert models == {
        "three-dimensional boundary element prediction",
        "two-dimensional boundary element prediction",
    }
    assert all(row.model.startswith("three") for row in _rows(C1))
    assert all(row.model.startswith("two") for row in _rows(C3))


def test_the_two_three_dimensional_tables_are_credited_to_their_paper() -> None:
    """A source line under the last group of each, resolved to the reference."""
    for table in (C1, C2):
        cited = {row.attributed_to["table"] for row in _rows(table)}
        assert len(cited) == 1
        assert cited.pop().startswith("H. Lee and T. Sakuma")
    assert not any(row.attributed_to for row in _rows(C3))


# ---------------------------------------------------------------------------
# The shape of a row
# ---------------------------------------------------------------------------
def test_the_three_dimensional_tables_print_no_band_below_250_hz() -> None:
    """The book says to take the coefficient as zero there and prints nothing.

    A catalogue that filled those five bands with zeros would be putting the
    book's advice into the data, where a reader could no longer tell it from a
    computed value.
    """
    row = _rows(C1)[0]
    assert row.bands() == ref.COX_C_FLAT_BANDS_HZ
    for band in (100, 125, 160, 200):
        assert getattr(row, f"scattering_coefficient_{band}") is None
        assert row.why_missing(f"scattering_coefficient_{band}")
        with pytest.raises(ValueError, match=f"{band} Hz band"):
            row.scattering_coefficient(band)


def test_the_two_dimensional_table_prints_every_band() -> None:
    row = _rows(C3)[1]
    assert len(row.bands()) == 18
    assert row.scattering_coefficient(100) == row.spectrum()[100]


def test_the_plane_surface_scatters_nothing_and_carries_no_angle() -> None:
    """One row, eighteen zeros, and "All/any" where the angle would be."""
    plane = _rows(C3)[0]
    assert plane.name.startswith("Plane surfaces")
    assert set(plane.spectrum().values()) == {0.0}
    assert plane.angle_of_incidence_deg is None
    assert "All/any" in plane.why_missing("angle_of_incidence_deg")


def test_the_random_row_carries_no_angle_either_but_for_another_reason() -> None:
    random = next(row for row in _rows(C3) if row.variant == "random")
    assert random.angle_of_incidence_deg is None
    why = random.why_missing("angle_of_incidence_deg")
    assert "Random" in why
    assert "All/any" not in why


def test_every_value_is_a_scattering_coefficient() -> None:
    for row in PUBLISHED_PREDICTED_SCATTERING.values():
        for band, value in row.spectrum().items():
            assert 0.0 <= value <= 1.0, f"{row.name} at {band} Hz: {value}"


# ---------------------------------------------------------------------------
# What the tables are for
# ---------------------------------------------------------------------------
def test_the_summary_row_of_a_group_is_a_row_and_carries_its_values() -> None:
    """``h/L = 20`` closes the sinusoidal group of Table C.1 with thirteen cells.

    It is not a heading, and read as a percentage it is the group's own
    4 cm surface: same thirteen values, and the page prints them without their
    trailing zeros, which is the only place in the table that happens.
    """
    summary = next(row for row in _rows(C1) if row.name == "h/L = 20")
    four = next(
        row
        for row in _rows(C1)
        if row.name == "h = 4 cm, L = 20 cm" and row.group == "Sinusoidal cross-section"
    )
    assert summary.group == four.group
    assert summary.spectrum() == four.spectrum()
    assert len(summary.bands()) == 13


def test_the_one_row_table_c2_prints_twice_stays_two_rows() -> None:
    """The reference surface of two comparisons, printed once for each."""
    keys = [
        key
        for key, row in PUBLISHED_PREDICTED_SCATTERING.items()
        if key.startswith(C2) and row.name == "h = 4 cm, L = 20 cm, w = 10 cm"
    ]
    assert len(keys) == 2
    first, second = (PUBLISHED_PREDICTED_SCATTERING[key] for key in keys)
    assert first.spectrum() == second.spectrum()
    assert keys[0] != keys[1]


def test_the_surface_listed_in_two_sections_of_c3_is_two_rows() -> None:
    same = [
        row
        for row in _rows(C3)
        if row.name in {"6 periods, 3.66 m wide", "30 cm deep (semicylinder)"}
        and row.variant == "random"
    ]
    assert len(same) == 2
    assert same[0].spectrum() == same[1].spectrum()
    assert same[0].group != same[1].group


def test_the_lookup_matches_the_heading_as_well_as_the_row() -> None:
    assert len(predicted_scattering_named("sinusoidal cross-section")) == 12
    assert len(predicted_scattering_named("batten")) == 16
    assert predicted_scattering_named("QRD") == predicted_scattering_named("qrd")
    assert predicted_scattering_named("unobtainium") == ()


def test_the_catalogue_cannot_be_written_to() -> None:
    with pytest.raises(TypeError):
        PUBLISHED_PREDICTED_SCATTERING["x/y"] = PredictedScatteringSpectrum(  # type: ignore[index]
            name="x", source="nowhere"
        )
