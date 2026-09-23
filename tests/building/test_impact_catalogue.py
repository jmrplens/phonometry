#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The published impact insulation, against a second reading of the pages.

The catalogue and the oracle in :mod:`tests.reference_data.impact_insulation`
were transcribed from the rendered pages by two readers who never saw each
other's work, and compared cell by cell before either was kept. These tests
keep that comparison alive, and add the things the transcription cannot say by
itself: that a rating and an improvement on a rating are never both on one row,
that every row which refers to another one refers to a row this file holds and
to a worse floor than itself, and that the row numbers the seven tables print
run through without a gap.
"""

from __future__ import annotations

import pytest
import reference_data as ref

from phonometry import building
from phonometry.building import (
    PUBLISHED_IMPACT_INSULATION,
    ImpactInsulation,
    impact_insulation_named,
)

#: Harris 3e Tables 32.1 to 32.8 keyed the way the catalogue keys it.
HARRIS = "harris-1995-tables-32-1-to-32-8"

#: The rows of those eight tables. The catalogue also holds three tables of
#: Harris (1977), which are tested in ``test_wave4_catalogues.py``; everything
#: here is about Chapter 32 and reads only its rows.
CHAPTER_32 = {
    key: row for key, row in PUBLISHED_IMPACT_INSULATION.items() if row.table == HARRIS
}


def _row(printed_row: str) -> ImpactInsulation:
    """The row the page numbers *printed_row*, which is also its key."""
    return PUBLISHED_IMPACT_INSULATION[f"{HARRIS}/{printed_row}"]


def _floors() -> tuple[ImpactInsulation, ...]:
    """The rows of Tables 32.1 to 32.7, in the order the pages print them."""
    return tuple(
        row for row in CHAPTER_32.values() if not row.group.startswith("TABLA 32.8.")
    )


def _treatments() -> tuple[ImpactInsulation, ...]:
    """The six rows of Table 32.8."""
    return tuple(
        row for row in CHAPTER_32.values() if row.group.startswith("TABLA 32.8.")
    )


# ---------------------------------------------------------------------------
# The transcription against the second reading
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_every_row_of_the_eight_tables() -> None:
    assert len(CHAPTER_32) == 48
    assert len(ref.HARRIS_32_FLOORS) == 42
    assert len(ref.HARRIS_32_8) == 6


@pytest.mark.parametrize(
    ("printed_row", "description", "rating"),
    ref.HARRIS_32_FLOORS,
    ids=[printed_row for printed_row, _d, _r in ref.HARRIS_32_FLOORS],
)
def test_each_floor_holds_what_the_second_reader_read(
    printed_row: str, description: str, rating: str
) -> None:
    """Cell by cell over Tables 32.1 to 32.7, description included.

    The description is half of what these tables publish, and it is where a
    transcription slips: a dropped clause changes the construction the rating
    belongs to without changing any digit.
    """
    row = _row(printed_row)
    assert row.name == description
    if rating:
        assert row.impact_insulation_class == float(rating)
    else:
        assert row.impact_insulation_class is None
    assert row.impact_insulation_class_improvement is None


@pytest.mark.parametrize(
    ("treatment", "improvement"),
    ref.HARRIS_32_8,
    ids=[treatment[:40] for treatment, _i in ref.HARRIS_32_8],
)
def test_each_surface_treatment_holds_what_the_second_reader_read(
    treatment: str, improvement: str
) -> None:
    row = next(candidate for candidate in _treatments() if candidate.name == treatment)
    if improvement.isdigit():
        assert row.impact_insulation_class_improvement == float(improvement)
    else:
        low, high = (float(part) for part in improvement.split(" a "))
        assert row.impact_insulation_class_improvement is None
        assert row.ranges["impact_insulation_class_improvement"] == (low, high)


def test_the_rows_are_in_the_order_the_pages_print_them() -> None:
    assert [row.name for row in _floors()] == [
        description for _row, description, _rating in ref.HARRIS_32_FLOORS
    ]
    assert [row.name for row in _treatments()] == [
        treatment for treatment, _improvement in ref.HARRIS_32_8
    ]


@pytest.mark.parametrize(
    ("printed_row", "designation"),
    ref.HARRIS_32_TABLE_OF_ROW,
    ids=[printed_row for printed_row, _t in ref.HARRIS_32_TABLE_OF_ROW],
)
def test_each_row_is_filed_under_the_table_that_prints_it(
    printed_row: str, designation: str
) -> None:
    assert _row(printed_row).group.startswith(f"{designation}. ")


# ---------------------------------------------------------------------------
# Two quantities, and never both
# ---------------------------------------------------------------------------
def test_no_row_holds_a_rating_and_an_improvement_at_once() -> None:
    """An improvement is not a rating, and the catalogue keeps them apart.

    A row carrying both would invite exactly the arithmetic this catalogue
    exists to prevent: adding a delta-IIC to an IIC that already includes a
    covering, or reading a difference between two floors as the rating of one.
    """
    both = [
        row
        for row in CHAPTER_32.values()
        if row.impact_insulation_class is not None
        and row.impact_insulation_class_improvement is not None
    ]
    assert both == []
    filled = [
        row
        for row in CHAPTER_32.values()
        if row.impact_insulation_class is not None
        or row.impact_insulation_class_improvement is not None
    ]
    assert len(filled) == 45


def test_the_improvements_of_table_32_8_are_not_ratings() -> None:
    """Table 32.8 prints a delta and no row of it carries an IIC.

    Its six treatments improve a hard massive floor by 16 to 30 points, which
    is the same order as a whole rating, so a row that carried the improvement
    in the rating field would read as a floor nobody would build and nothing in
    the number would give it away.
    """
    treatments = _treatments()
    assert len(treatments) == 6
    for row in treatments:
        assert row.impact_insulation_class is None
        with pytest.raises(ValueError, match="has no impact_insulation_class"):
            row.printed("impact_insulation_class")


def test_the_class_says_an_improvement_is_a_difference() -> None:
    written = " ".join((ImpactInsulation.__doc__ or "").split())
    assert "difference between two ratings and not a rating" in written


# ---------------------------------------------------------------------------
# What the transcription cannot say by itself
# ---------------------------------------------------------------------------
def test_every_reference_resolves_to_a_row_this_file_holds() -> None:
    """The twelve descriptions that refer to another row point somewhere real.

    Nothing in a transcription checks that "Igual que 1" was read as 1 and not
    as 7: the cell is prose. Resolving each reference against the keys is the
    only thing that would catch a misread row number or a row dropped from the
    file underneath one that refers to it.
    """
    referring = [row for row in _floors() if row.refers_to_row]
    assert len(referring) == len(ref.HARRIS_32_REFERS_TO) == 12
    for row, (printed_row, target) in zip(
        referring, ref.HARRIS_32_REFERS_TO, strict=True
    ):
        assert row.refers_to_row == target
        assert f"{row.table}/{target}" in PUBLISHED_IMPACT_INSULATION
        assert _row(printed_row) is row


def test_every_referring_row_rates_above_the_one_it_is_built_on() -> None:
    """Each of the twelve referring rows rates above the row it refers to.

    Every one of them is the construction it names with something added, made
    heavier or hung resiliently: a vinyl tile, a wood strip floor, a carpet, a
    layer of sand between the joists, a ceiling screwed to resilient channels.
    None of those is the kind of change that makes impact transmission worse,
    and on these pages every one of the twelve raises the rating, four of them
    by more than twenty points. A row that came out below its own reference
    would be a misread digit or a reference pointing at the wrong row, and
    neither shows up when the cells are checked one at a time.
    """
    checked = 0
    for row in _floors():
        if not row.refers_to_row:
            continue
        reference = PUBLISHED_IMPACT_INSULATION[f"{row.table}/{row.refers_to_row}"]
        held = row.printed("impact_insulation_class")
        assert held > reference.printed("impact_insulation_class"), row.refers_to_row
        checked += 1
    assert checked == 12


def test_the_row_numbers_run_from_one_to_thirty_eight_without_a_gap() -> None:
    """The seven tables number their rows straight through, and all 38 are here.

    The numbering does not restart per table, so a dropped row leaves a hole in
    a sequence rather than a short table, and a table read twice leaves a
    duplicate. Counting the rows would find neither.
    """
    printed = [row.split("/")[1] for row in CHAPTER_32]
    numbered = [entry for entry in printed if entry[0].isdigit()]
    stems = []
    for entry in numbered:
        stem = entry.rstrip("AB")
        if stem not in stems:
            stems.append(stem)
    assert stems == [str(number) for number in range(1, 39)]
    assert sorted(numbered) == sorted(set(numbered))
    assert len(numbered) == 42


def test_a_lettered_pair_is_two_rows_and_not_one_row_in_two_conditions() -> None:
    """34A and 34B are rows, so neither is a variant of the other.

    The contract keeps ``variant`` for the several specimens a page prints
    under one name. Here the page numbers each letter separately and gives it
    a description and a rating of its own, so filling ``variant`` would merge
    two measured floors into one.
    """
    lettered = [
        key.split("/")[1]
        for key in CHAPTER_32
        if key[-1] in "AB" and key.split("/")[1][:-1].isdigit()
    ]
    assert lettered == ["34A", "34B", "35A", "35B", "36A", "36B", "37A", "37B"]
    assert not [row for row in CHAPTER_32.values() if row.variant]


# ---------------------------------------------------------------------------
# The cells that are not numbers
# ---------------------------------------------------------------------------
def test_the_two_blank_ratings_say_the_page_left_them_blank() -> None:
    """Rows 30 and 38 print no rating, with no dash and no convention for it.

    Nothing is invented for them and no hedge is claimed either: the page is
    simply empty there, which is a different answer from a cell holding a word
    or an interval, and the refusal has to say so.
    """
    empty = [
        printed_row
        for printed_row, _description, rating in ref.HARRIS_32_FLOORS
        if not rating
    ]
    assert empty == ["30", "38"]
    blank = [row for row in _floors() if row.impact_insulation_class is None]
    assert blank == [_row(printed_row) for printed_row in empty]
    for row in blank:
        assert row.why_missing("impact_insulation_class") == (
            "the page does not give it, and it does not follow from the cells "
            "that it does"
        )


def test_the_one_interval_of_table_32_8_is_held_as_a_range() -> None:
    row = next(
        candidate
        for candidate in _treatments()
        if "impact_insulation_class_improvement" in candidate.ranges
    )
    assert row.impact_insulation_class_improvement is None
    assert row.why_missing("impact_insulation_class_improvement") == (
        "the page prints 25 to 30 and no value"
    )


def test_the_three_carried_references_say_where_they_come_from() -> None:
    """Three rows print "Parecido al anterior" and no row number.

    For them the row referred to follows from the position on the page and not
    from anything printed, so the row says so in ``carried`` rather than
    presenting the number as a reading. It is not a derivation: nothing is
    computed, and ``is_derived`` answers ``False``.
    """
    carried = [row for row in _floors() if "refers_to_row" in row.carried]
    assert [row.refers_to_row for row in carried] == ["28", "31", "34A"]
    for row in carried:
        assert "Parecido al anterior" in row.carried["refers_to_row"]
        assert not row.is_derived("refers_to_row")
    printed_reference = [
        row
        for row in _floors()
        if row.refers_to_row and "refers_to_row" not in row.carried
    ]
    assert len(printed_reference) == 9


# ---------------------------------------------------------------------------
# The pairs the page got wrong
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("printed_row", "pair"),
    ref.HARRIS_32_MISPRINTED_PAIRS,
    ids=[
        f"{printed_row}-{pair}" for printed_row, pair in ref.HARRIS_32_MISPRINTED_PAIRS
    ],
)
def test_each_pair_the_page_got_wrong_is_kept_and_marked(
    printed_row: str, pair: str
) -> None:
    """The printed pair stays in the description and the cell carries the mark.

    This is the shape the catalogue promises: a defect of the page is neither
    repaired nor dropped. The description keeps the pair exactly as it is set,
    so a reader reproducing the book finds what the book says, and the cell is
    marked so nobody downstream mistakes it for a reading this library stands
    behind.
    """
    row = _row(printed_row)
    assert pair in row.name
    reason = row.misprinted["name"]
    assert pair in reason
    assert "docs/ERRATA.md" in reason


def test_no_other_row_of_the_eight_tables_is_marked_misprinted() -> None:
    """Exactly the seventeen rows the second reading flagged, and no more.

    A mark added to a row whose pair converts would be an accusation against a
    page that is right, which costs the registry more than a missed one.
    """
    marked = sorted(
        {row for row, _pair in ref.HARRIS_32_MISPRINTED_PAIRS},
        key=lambda printed_row: (int(printed_row.rstrip("AB")), printed_row),
    )
    held = [key.split("/")[1] for key, row in CHAPTER_32.items() if row.misprinted]
    assert held == marked
    assert len(marked) == 17


def test_the_one_wrong_pair_that_is_a_quantity_serves_no_number() -> None:
    """Row 35A prints its board's density twice and the two disagree.

    Every other pair the page gets wrong is inside the running description,
    where nothing is served from it. This one is the cell the catalogue would
    lift into a field, so the field stays empty and the refusal hands back both
    printed halves rather than picking one.
    """
    row = _row("35A")
    assert row.layer_density_kg_m3 is None
    why = row.why_missing("layer_density_kg_m3")
    assert "410 kg/m3 (26,1 lb/ft3)" in why
    assert "418 kg/m3" in why
    assert "25,6 lb/ft3" in why
    with pytest.raises(ValueError, match="has no layer_density_kg_m3"):
        row.printed("layer_density_kg_m3")


# ---------------------------------------------------------------------------
# Who measured these floors
# ---------------------------------------------------------------------------
def test_every_row_carries_the_credit_of_the_table_that_prints_it() -> None:
    """Two credits, and a row read on its own has to say which one is its own.

    Tables 32.1 to 32.7 are the 1967 survey the National Bureau of Standards
    made for the Federal Housing Administration; Table 32.8 carries a printed
    credit line of its own to a 1963 German paper by Zeller. ``read_table``
    hands a row its ``source`` and nothing else, so a caller holding one row of
    Table 32.8 had no way to tell the two apart until the credit was on the
    row.
    """
    for row in _floors():
        credit = row.attributed_to["table"]
        assert "National Bureau of Standards" in credit
        assert "1967" in credit
        assert "Zeller" not in credit
    for row in _treatments():
        credit = row.attributed_to["table"]
        assert "Zeller" in credit
        assert "1963" in credit
        assert "Fuente: Referencia 6." in credit
    assert len({row.attributed_to["table"] for row in _floors()}) == 1
    assert len({row.attributed_to["table"] for row in _treatments()}) == 1


# ---------------------------------------------------------------------------
# The footnote, and the cells the page leaves blank
# ---------------------------------------------------------------------------
def test_every_row_of_table_32_8_carries_the_footnote_of_its_table() -> None:
    """The footnote is the brake on the whole of Table 32.8.

    It says the improvement may be substantially smaller over wood-joist
    floors, which is most of the floors anybody applies these treatments to, so
    a row of that table handed over without it is a number with its condition
    removed. Nothing else in this file fails if the note is deleted from the
    six rows, which is why this test exists.
    """
    treatments = _treatments()
    assert len(treatments) == 6
    for row in treatments:
        assert row.note.startswith("* Si estos tratamientos de superficies")
        assert "suelos de viguetas de madera" in row.note
        assert "sustancialmente inferior" in row.note
    assert len({row.note for row in treatments}) == 1
    assert not [row for row in _floors() if row.note.startswith("*")]


def test_the_two_blank_ratings_say_their_column_was_printed_for_them() -> None:
    """A blank cell in a column that exists is not a column that does not.

    :meth:`~phonometry._internal.catalogue.CatalogueRow.why_missing` answers the
    same sentence for both, because the contract has no hedge for "the column
    is there and this cell is blank": what distinguishes them is on the row's
    note, where the page's own silence can be described without inventing a
    reading of it.
    """
    for printed_row, table in (("30", "32.5"), ("38", "32.7")):
        row = _row(printed_row)
        assert row.impact_insulation_class is None
        assert f"column of Table {table} is printed for this row" in row.note
        assert "no number, no dash and no convention" in row.note


# ---------------------------------------------------------------------------
# The columns that are not a quantity
# ---------------------------------------------------------------------------
def test_the_section_drawings_are_recorded_and_nothing_else_is() -> None:
    drawn = [
        row.split("/")[1]
        for row, value in CHAPTER_32.items()
        if value.has_section_drawing
    ]
    assert drawn == list(ref.HARRIS_32_DRAWINGS)
    assert len(drawn) == 38
    for row in _treatments():
        assert not row.has_section_drawing


@pytest.mark.parametrize(
    ("printed_row", "material", "printed"),
    ref.HARRIS_32_DENSITIES,
    ids=[printed_row for printed_row, _m, _p in ref.HARRIS_32_DENSITIES],
)
def test_the_buried_densities_are_lifted_out_and_the_prose_stays_whole(
    printed_row: str, material: str, printed: str
) -> None:
    row = _row(printed_row)
    value, unit = printed.split(" ")
    assert unit == "kg/m3"
    assert material.casefold() in row.name.casefold()
    assert value in row.name
    if printed_row == "35A":
        # The one the page prints twice and inconsistently; the row below says
        # what it does instead.
        assert row.layer_density_kg_m3 is None
        return
    assert row.layer_density_kg_m3 == float(value.replace(",", "."))
    assert material in row.note


def test_the_density_field_says_layer_because_two_of_the_three_are_not_slabs() -> None:
    """Row 5 is a foam and row 35A a paper board; only 37A is a slab.

    The name of the field is the only thing a caller filtering the catalogue
    reads, and a caller after the density of a structural floor who filtered on
    a field called ``slab_density`` would be handed 35,2 kg/m3 of semi-rigid
    polyurethane foam.
    """
    assert hasattr(_row("5"), "layer_density_kg_m3")
    assert not hasattr(_row("5"), "slab_density_kg_m3")
    written = " ".join((ImpactInsulation.__doc__ or "").split())
    assert "which is why the field says layer and not slab" in written
    assert "never a density of the assembly" in written


def test_no_other_row_claims_a_density() -> None:
    with_density = [row for row in CHAPTER_32.values() if row.layer_density_kg_m3]
    assert len(ref.HARRIS_32_DENSITIES) == 3
    assert [row.name[:20] for row in with_density] == [
        _row("5").name[:20],
        _row("37A").name[:20],
    ]


# ---------------------------------------------------------------------------
# A single-number rating, and no spectrum anywhere
# ---------------------------------------------------------------------------
def test_the_catalogue_publishes_no_frequency_band() -> None:
    """The IIC is one number and these pages print no band at all.

    A band field added here would have to come from somewhere, and there is no
    somewhere: the chapter prints no impact sound pressure level per octave,
    none per third octave and no reference curve. This fails the moment anybody
    gives the row a spectrum the page cannot back.
    """
    row = _row("1")
    assert not hasattr(row, "spectrum")
    assert not hasattr(row, "bands")
    fields = vars(row)
    assert not [name for name in fields if name.endswith("_hz") or "_hz_" in name]


def test_the_module_says_there_is_no_spectrum_to_be_had() -> None:
    doc = building.impact_catalogue.__doc__ or ""
    assert "single-number rating" in doc
    assert "band-by-band impact level will not find one" in doc


# ---------------------------------------------------------------------------
# The shape of the catalogue
# ---------------------------------------------------------------------------
def test_every_row_says_which_pages_it_was_read_on() -> None:
    for row in CHAPTER_32.values():
        assert row.source == (
            "Harris 3e Tables 32.1 to 32.8, PDF pages 750-757 (printed pp. 32.8-32.15)"
        )
        assert row.table == HARRIS


def test_the_lookup_matches_a_fragment_of_the_printed_description() -> None:
    assert impact_insulation_named("baldosa de vinilo") == (_row("2"),)
    assert impact_insulation_named("LINÓLEO") == impact_insulation_named("linóleo")
    linoleum = impact_insulation_named("linóleo")
    treatments = _treatments()
    assert len(linoleum) == 9
    assert len([row for row in linoleum if row in treatments]) == 5
    assert impact_insulation_named("unobtainium") == ()


def test_the_catalogue_is_reachable_from_the_package() -> None:
    assert building.PUBLISHED_IMPACT_INSULATION is PUBLISHED_IMPACT_INSULATION
    assert all(key.startswith(f"{row.table}/") for key, row in CHAPTER_32.items())
    assert {row.table for row in PUBLISHED_IMPACT_INSULATION.values()} == {
        HARRIS,
        "harris-1977-table-19-2",
        "harris-1977-table-19-3",
        "harris-1977-table-19-4",
    }


def test_the_catalogue_cannot_be_written_to() -> None:
    with pytest.raises(TypeError):
        PUBLISHED_IMPACT_INSULATION["x/y"] = ImpactInsulation(  # type: ignore[index]
            name="x", source="nowhere"
        )
