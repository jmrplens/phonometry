#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The published transmission loss, against a second reading of the pages.

The catalogue and the oracle in :mod:`tests.reference_data.transmission_loss`
were transcribed from the rendered pages by two readers who never saw each
other's work, and compared cell by cell before either was kept. These tests
keep that comparison alive, and add the shape: that a band the page leaves
empty stays empty and says so, that the thickness and the surface density
travel with the row, and that two constructions of the same description are
two rows rather than one.
"""

from __future__ import annotations

import pytest
import reference_data as ref

from phonometry.building import (
    PUBLISHED_TRANSMISSION_LOSS,
    TRANSMISSION_LOSS_BANDS_HZ,
    TransmissionLossSpectrum,
    transmission_loss_named,
)

#: Bies 5e Table 7.6 keyed the way the catalogue keys it.
BIES = "bies-2017-table-7-6"


def _plain(text: str) -> str:
    """A description with the quotation marks the two readings spell apart.

    The page sets ``‘acoustic’`` and ``‘floating’`` with typographic quotes and
    ``50 mm × 100 mm`` with a multiplication sign; one reading typed those and
    the other their ASCII stand-ins, and neither is wrong about the paper.
    The catalogue keeps what the page prints; this is only for comparing the
    two readings.
    """
    return text.replace("‘", "'").replace("’", "'").replace("×", "x")


def _rows() -> list[TransmissionLossSpectrum]:
    """Every row of the table, in catalogue order."""
    return [
        row for key, row in PUBLISHED_TRANSMISSION_LOSS.items() if key.startswith(BIES)
    ]


# ---------------------------------------------------------------------------
# The transcription against the second reading
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_every_row_of_the_table() -> None:
    """Ninety-four constructions over six printed pages."""
    assert len(_rows()) == len(ref.BIES_7_6_TRANSMISSION_LOSS) == 94


@pytest.mark.parametrize(
    ("name", "thickness", "weight", "values"),
    ref.BIES_7_6_TRANSMISSION_LOSS,
    ids=[
        f"{name[:30]}-{thickness:g}"
        for name, thickness, _, _ in ref.BIES_7_6_TRANSMISSION_LOSS
    ],
)
def test_each_row_holds_what_the_second_reader_read(
    name: str,
    thickness: float,
    weight: float | None,
    values: tuple[float | None, ...],
) -> None:
    """Cell by cell, with the thickness and the surface weight beside them.

    The description alone does not identify a row: the page prints six
    windows called "Single glass in heavy frame" and three concrete floors
    called "Concrete, reinforced". The thickness tells them apart, which is
    why it is part of the key and part of this comparison.
    """
    matches = [
        row
        for row in _rows()
        if _plain(row.name) == _plain(name) and row.thickness_mm == thickness
    ]
    held = [
        [getattr(row, f"transmission_loss_{band}_db") for band in ref.BIES_7_6_BANDS_HZ]
        for row in matches
    ]
    assert list(values) in held, f"{name!r} at {thickness} mm: {values} not in {held}"
    row = matches[held.index(list(values))]
    assert row.surface_density_kg_m2 == weight


def test_every_row_prints_a_thickness() -> None:
    """The one column the page fills on all ninety-four rows."""
    assert all(row.thickness_mm is not None for row in _rows())


def test_the_two_rows_without_a_surface_weight_say_so() -> None:
    """A dash in that column, and a refusal rather than a guess.

    Neither row can be checked against the mass law, and neither pretends
    otherwise: the field is empty and ``why_missing`` says the page does not
    give it.
    """
    missing = [row for row in _rows() if row.surface_density_kg_m2 is None]
    assert len(missing) == 2
    assert "Typical proprietary" in missing[0].name
    assert "Gypsum ceiling" in missing[1].name
    assert missing[0].why_missing("surface_density_kg_m2")
    with pytest.raises(ValueError, match="surface_density_kg_m2"):
        missing[0].printed("surface_density_kg_m2")


# ---------------------------------------------------------------------------
# The shape of a row
# ---------------------------------------------------------------------------
def test_a_row_reads_back_as_a_spectrum_over_the_bands_it_prints() -> None:
    row = PUBLISHED_TRANSMISSION_LOSS[f"{BIES}/1_5_mm_lead_sheet_1.5mm"]
    assert row.bands() == TRANSMISSION_LOSS_BANDS_HZ
    assert row.spectrum()[500] == 33
    assert row.transmission_loss_db(500) == 33


def test_a_band_the_page_did_not_print_is_refused_by_name() -> None:
    """Thirty-eight rows leave 63 Hz empty, and none of them answers zero.

    A zero decibel transmission loss is a partition that transmits
    everything, so a caller who gets one instead of a refusal would be told
    the opposite of what the page says.
    """
    row = PUBLISHED_TRANSMISSION_LOSS[f"{BIES}/6_mm_steel_plate_6mm"]
    assert row.transmission_loss_63_db is None
    with pytest.raises(ValueError, match="63 Hz band"):
        row.transmission_loss_db(63)
    assert row.why_missing("transmission_loss_63_db")


def test_a_frequency_no_table_prints_is_refused_as_such() -> None:
    row = PUBLISHED_TRANSMISSION_LOSS[f"{BIES}/6_mm_steel_plate_6mm"]
    with pytest.raises(ValueError, match="not an octave band"):
        row.transmission_loss_db(700)


def test_every_value_is_a_plausible_transmission_loss() -> None:
    """Between zero and ninety decibels, which is what a partition does.

    The table's floor is the unplastered woodwork slab, which is printed as 0
    at 63 and 125 Hz, and its ceiling is 85 dB at 4 and 8 kHz for a double
    brick wall on expanded metal ties. A value outside that range would be a
    digit slipped rather than a partition.
    """
    for row in _rows():
        for band, value in row.spectrum().items():
            assert 0 <= value <= 90, f"{row.name} at {band} Hz: {value}"


# ---------------------------------------------------------------------------
# What the table is for
# ---------------------------------------------------------------------------
def test_the_same_wall_with_two_kinds_of_tie_is_two_rows() -> None:
    """The comparison the table exists to make.

    Two 280 mm brick walls, same thickness and same surface weight, one with
    strip ties and one with expanded metal ties: 40 and 55 dB at 500 Hz, 73
    and 77 at 2 kHz. A catalogue that kept one of them would lose the reason
    the distinction is made.
    """
    walls = [row for row in _rows() if row.name.startswith("280 mm brick")]
    assert len(walls) == 2
    assert {row.thickness_mm for row in walls} == {300}
    assert {row.surface_density_kg_m2 for row in walls} == {380}
    strip, expanded = walls
    assert "strip ties" in strip.name
    assert "expanded metal ties" in expanded.name
    assert (strip.spectrum()[500], expanded.spectrum()[500]) == (40, 55)


def test_a_fragment_answers_with_every_construction_that_carries_it() -> None:
    """Ten doors, and the caller reads the thickness to pick one.

    The page prints twelve rows under its Doors heading, and two of them, the
    hollow flush panel and the solid hardwood, are described without the
    word. A lookup over printed names finds the ten that carry it, and the
    group is what finds the other two.
    """
    doors = [row for row in transmission_loss_named("door") if row.table == BIES]
    assert len(doors) == 10
    assert all("door" in row.name.casefold() for row in doors)
    assert sorted({row.thickness_mm for row in doors}) == [
        35,
        44,
        54,
        66,
        100,
        180,
        250,
        270,
    ]
    in_the_group = [row for row in _rows() if row.group == "Doors"]
    assert len(in_the_group) == 12


def test_the_lookup_ignores_case_and_answers_with_nothing_for_nothing() -> None:
    assert transmission_loss_named("PLYWOOD") == transmission_loss_named("plywood")
    assert transmission_loss_named("unobtainium") == ()


def test_the_catalogue_cannot_be_written_to() -> None:
    with pytest.raises(TypeError):
        PUBLISHED_TRANSMISSION_LOSS["x/y"] = TransmissionLossSpectrum(  # type: ignore[index]
            name="x", source="nowhere"
        )


# ---------------------------------------------------------------------------
# The second table: the machine equipment room constructions of ASHRAE
# ---------------------------------------------------------------------------
#: ASHRAE Chapter 49 Table 40 keyed the way the catalogue keys it.
ASHRAE = "ashrae-2019-table-40"


def _ashrae() -> list[TransmissionLossSpectrum]:
    """The nine machine equipment room rows, in printed order."""
    return [
        row
        for key, row in PUBLISHED_TRANSMISSION_LOSS.items()
        if key.startswith(ASHRAE)
    ]


def test_the_catalogue_reads_every_one_of_its_tables() -> None:
    """Ninety-four constructions from Bies, nine from ASHRAE, and the rest.

    They are the same quantity measured the same way, which is why they are
    one catalogue, and the key names the table because a reader comparing two
    walls of the same description across two books has to know which is which.
    Rossing's table and the seven of Harris Chapter 31 are counted in
    ``test_wave4_catalogues.py``; this is the sum.
    """
    assert len(PUBLISHED_TRANSMISSION_LOSS) == 94 + 9 + 23 + 129
    assert len(_ashrae()) == len(ref.ASHRAE_49_TABLE_40) == 9
    assert {row.table for row in _ashrae()} == {ASHRAE}


@pytest.mark.parametrize(
    ("name", "rating", "values"),
    ref.ASHRAE_49_TABLE_40,
    ids=[name[:40] for name, _r, _v in ref.ASHRAE_49_TABLE_40],
)
def test_each_machine_room_row_holds_what_the_second_reader_read(
    name: str, rating: str, values: tuple[str, ...]
) -> None:
    """Cell by cell, the rating included, and the label reassembled in full.

    Four of the nine labels wrap over two lines in the narrow printed column,
    and a label reassembled short is the one defect a spectrum comparison
    would not catch, so the description is compared character for character
    beside the numbers.
    """
    row = next(row for row in _ashrae() if row.name == name)
    assert row.sound_transmission_class == float(rating)
    held = [
        getattr(row, f"transmission_loss_{band}_db")
        for band in ref.ASHRAE_49_TABLE_40_BANDS_HZ
    ]
    assert held == [float(text) for text in values]


def test_the_machine_room_rows_print_no_eight_kilohertz_band() -> None:
    """The table stops at 4 kHz, and the missing column is not a zero."""
    for row in _ashrae():
        assert row.bands() == ref.ASHRAE_49_TABLE_40_BANDS_HZ
        assert row.transmission_loss_8000_db is None
        with pytest.raises(ValueError, match="8000 Hz band"):
            row.transmission_loss_db(8000)


def test_the_rating_is_kept_because_the_bands_do_not_give_it_back() -> None:
    """An STC is computed from third octaves, so it is a reading of its own.

    The nine rows rise monotonically in rating and the 500 Hz band does not
    rise with them: the two concrete floors are 53 and 72 with 49 and 73 dB at
    500 Hz, and the double stud wall rates 64 on 62 dB. A catalogue that
    dropped the rating would be discarding a published number it cannot
    recompute, and one that rebuilt it from these seven bands would be
    inventing one.
    """
    ratings = [row.sound_transmission_class for row in _ashrae()]
    assert ratings == [50, 53, 38, 49, 56, 64, 53, 72, 84]
    assert [row.sound_transmission_class for row in _rows()[:3]] == [None] * 3
    best = max(_ashrae(), key=lambda row: row.sound_transmission_class or 0)
    assert "spring isolators" in best.name
    assert best.transmission_loss_db(500) == 84


def test_adding_a_leaf_never_makes_a_machine_room_wall_worse() -> None:
    """The comparison the nine rows are printed to make.

    The page walks one construction at a time: bare block, block with a lined
    leaf, one layer of board each side of studs, the same with insulation, two
    layers, and two rows of studs. Every step up is a better rating and a
    better 500 Hz band than the step before it, which is what makes the table
    a design argument rather than a list. A row read out of order, or a digit
    slipped in either column, breaks the chain.
    """
    studs = [row for row in _ashrae() if "metal studs" in row.name]
    assert len(studs) == 4
    ratings = [row.sound_transmission_class for row in studs]
    at_500 = [row.transmission_loss_db(500) for row in studs]
    assert ratings == sorted(ratings)
    assert at_500 == sorted(at_500)
    assert ratings[-1] - ratings[0] == 26


def test_the_machine_room_rows_say_nothing_about_thickness_or_mass() -> None:
    """The page prints neither, so the mass law has nothing to take here."""
    for row in _ashrae():
        assert row.thickness_mm is None
        assert row.surface_density_kg_m2 is None
        assert row.why_missing("surface_density_kg_m2")
