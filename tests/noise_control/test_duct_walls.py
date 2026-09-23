#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The duct walls of ASHRAE Chapter 49, against a second reading of the pages.

The catalogue and the oracle in :mod:`tests.reference_data.duct_walls` were
transcribed from the rendered pages by two readers who never saw each other's
work, and compared cell by cell before either was kept. These tests keep that
comparison alive, and add the things the transcription cannot say by itself:
that the two quantities are never mixed, that the six tables agree with each
other where the chapter says they should, that a mark the page prints instead
of a number is still a mark and not a zero, and that the censored cells are the
ones somebody counted on the paper.
"""

from __future__ import annotations

import json
import math

import pytest
import reference_data as ref

from phonometry import noise_control
from phonometry.noise_control import (
    DUCT_WALL_BANDS_HZ,
    PUBLISHED_DUCT_TRANSMISSION_LOSS,
    DuctWallSpectrum,
    duct_wall_named,
)

#: The data file this catalogue is read from, as the key spells it.
TABLE = "ashrae-2019-tables-29-to-34"

#: The three breakout tables and the three break-in ones.
BREAKOUT_TABLES = ("Table 29", "Table 30", "Table 31")
BREAK_IN_TABLES = ("Table 32", "Table 33", "Table 34")
#: The four tables whose titles do not say "Experimentally Measured": a
#: smooth rule rather than a measurement, and monotone band by band.
SMOOTH_TABLES = ("Table 29", "Table 31", "Table 33", "Table 34")


def _rows() -> list[DuctWallSpectrum]:
    """Every row of the catalogue, in the order the pages print them."""
    return list(PUBLISHED_DUCT_TRANSMISSION_LOSS.values())


def _of(printed_table: str) -> list[DuctWallSpectrum]:
    """The rows of one printed table, in printed order."""
    return [row for row in _rows() if row.printed_table == printed_table]


def _by_construction(
    printed_table: str,
) -> dict[tuple[float | None, float | None, str], DuctWallSpectrum]:
    """A table's rows keyed by the two sides and the gauge printed with them."""
    return {
        (row.first_side_mm, row.second_side_mm, row.sheet_metal_gauge): row
        for row in _of(printed_table)
    }


def _ids() -> list[str]:
    """One id per oracle row, and no two of them the same.

    Table 32 prints one diameter at two gauges and another at two, so the
    label and the gauge together do not identify a row. Ids that collide are
    suffixed 0 and 1 by pytest, which reads as if one row were tested twice;
    the printed position is what tells them apart, and it is what the test
    recovers the row by.
    """
    return [
        f"{index:02d}-{table.replace('Table ', 't')}-{label or 'blank'}-{gauge}"
        for index, (table, _group, label, gauge, _length, _values) in enumerate(
            ref.ASHRAE_49_DUCT_WALLS
        )
    ]


def _printed_millimetres(label: str) -> tuple[float, ...]:
    """The sizes a printed row label holds, in the order the page prints them.

    ``"305 × 1220"`` is two sides and ``"200"`` is a diameter, which is the
    whole of what tells a rectangular or flat oval row from a round one once
    the table heading is off the page.
    """
    return tuple(float(part) for part in label.split("×"))


def _assert_the_row_is_the_one_the_label_names(
    row: DuctWallSpectrum, index: int, label: str
) -> None:
    """The label, the name and the millimetres in the fields agree.

    A transcription that read every digit of a row correctly and hung them on
    the wrong size would pass a comparison of the band cells alone: the sizes
    live in their own columns and no cell comparison touches them. Both sides
    of a rectangular or flat oval row are read here, in the order the page
    prints them, and a round row's diameter, so a size written into the wrong
    field, or carried down from the row above, fails.
    """
    if not label:
        inherited = ref.ASHRAE_49_INHERITED_DIAMETERS[index]
        assert row.name == f"{inherited} mm"
        assert row.diameter_mm == float(inherited)
        assert "diameter_mm" in row.carried
        return
    assert row.name == f"{label} mm"
    printed = _printed_millimetres(label)
    if len(printed) == 2:
        assert (row.first_side_mm, row.second_side_mm) == printed
        assert row.diameter_mm is None
    else:
        assert row.diameter_mm == printed[0]
        assert (row.first_side_mm, row.second_side_mm) == (None, None)
    assert "diameter_mm" not in row.carried


# ---------------------------------------------------------------------------
# The transcription against the second reading
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_every_row_of_the_six_tables() -> None:
    """Seven, nine, seven, nine, seven and seven, which is forty-six."""
    assert len(PUBLISHED_DUCT_TRANSMISSION_LOSS) == 46
    assert len(ref.ASHRAE_49_DUCT_WALLS) == 46
    counted = [len(_of(name)) for name in (*BREAKOUT_TABLES, *BREAK_IN_TABLES)]
    assert counted == [7, 9, 7, 9, 7, 7]


def test_the_rows_are_in_the_order_the_pages_print_them() -> None:
    held = [(row.printed_table, row.sheet_metal_gauge) for row in _rows()]
    read = [
        (table, gauge)
        for table, _group, _label, gauge, _length, _values in ref.ASHRAE_49_DUCT_WALLS
    ]
    assert held == read


@pytest.mark.parametrize(
    ("index", "printed_table", "group", "label", "gauge", "length", "values"),
    [(index, *entry) for index, entry in enumerate(ref.ASHRAE_49_DUCT_WALLS)],
    ids=_ids(),
)
def test_every_cell_is_the_mark_the_second_reader_read(
    index: int,
    printed_table: str,
    group: str,
    label: str,
    gauge: str,
    length: str,
    values: tuple[str, ...],
) -> None:
    """Cell by cell, and mark by mark rather than digit by digit.

    Four things can be in a cell of these tables and only one of them is a
    number, so a comparison that read every cell as a float would agree with
    the page on the digits and be wrong about three of the four. Each mark is
    checked for what it became: a value, a refused bound, a value the page put
    in parentheses, or a glyph the chapter never explains. What surrounds the
    cells is checked here too, because nothing else checks it: the row label
    and the millimetres read off it, the shape and the direction its table's
    own title gives it, the group heading, the gauge and the length.

    The row is recovered by its printed position and not by looking its own
    values up, so two rows that print the same marks stay two rows.
    """
    row = _rows()[index]
    assert row.printed_table == printed_table
    assert row.group == group
    assert row.sheet_metal_gauge == gauge
    shape, direction = ref.ASHRAE_49_TABLE_TITLES[printed_table]
    assert row.shape == shape
    assert row.direction == direction
    _assert_the_row_is_the_one_the_label_names(row, index, label)
    if length:
        # The attribute first, like every other comparison in this file, and
        # against the number rather than a rendering of it: formatting the
        # float to compare two strings put the only expected value on the left
        # in the whole module.
        assert row.duct_length_m == pytest.approx(float(length))
    else:
        assert row.duct_length_m is None

    for band, text in zip(ref.ASHRAE_49_BANDS_HZ[printed_table], values, strict=True):
        field = f"transmission_loss_{band}_db"
        held = getattr(row, field)
        printed_here = f"The {band} Hz cell is printed “{text}”"
        if text.startswith(">"):
            assert held is None
            assert field in row.bounded_below
            assert row.ranges[field] == (float(text[1:]), None)
            assert f"lower bound of {text[1:]}" in row.why_missing(field)
            assert printed_here in row.note
        elif text.startswith("("):
            assert held == float(text.strip("()"))
            assert not row.is_approximate(field)
            assert field not in row.ranges
            assert printed_here in row.note
            assert "greater uncertainty than usual" in row.note
        elif text == "—":
            assert held is None
            assert row.unquantified[field] == text
        else:
            assert held == float(text)
            assert not row.is_approximate(field)
            assert field not in row.ranges
            assert field not in row.unquantified
            assert f"The {band} Hz cell is printed" not in row.note


def test_a_diameter_the_page_leaves_blank_is_carried_and_never_served_as_read() -> None:
    """One printed 610 mm covers three rows, and two of them did not read it.

    The page prints the diameter once and leaves the cell empty on the two
    rows below it. A transcription that carried the blank into the catalogue
    would publish two duct walls of no diameter; one that stored the number as
    if the cell held it would be publishing a reading nobody made. The two
    rows keep it in ``carried``, which is what the row has for a value the
    page prints on another row, so the published table marks the cell as
    carried down rather than read. Nothing is computed, so ``is_derived``
    answers ``False``.
    """
    blanks = ref.ASHRAE_49_INHERITED_DIAMETERS
    assert len(blanks) == 2
    for index, diameter in blanks.items():
        row = _rows()[index]
        assert row.diameter_mm == float(diameter)
        assert not row.is_derived("diameter_mm")
        assert "carried down" in row.carried["diameter_mm"]
        assert "Table 30" in row.carried["diameter_mm"]
    printed_it = [
        row
        for row in _of("Table 30")
        if row.diameter_mm == 610 and "diameter_mm" not in row.carried
    ]
    assert len(printed_it) == 1
    assert len([row for row in _of("Table 30") if row.diameter_mm == 610]) == 3
    carried_elsewhere = [
        row for row in _rows() if row.carried and row.diameter_mm != 610
    ]
    assert carried_elsewhere == []
    assert [row for row in _rows() if row.derived] == []


def test_a_band_a_table_prints_no_column_for_is_not_a_band_it_left_empty() -> None:
    """Two different absences, and the row tells them apart.

    Table 31 stops at 4 kHz, so its 8 kHz field is empty because there is no
    column; its 2 kHz field is empty because the cell holds a rule. A
    catalogue that answered the same thing for both would lose the difference
    between a measurement the page never made and one it made and censored.
    """
    row = _of("Table 31")[0]
    assert row.transmission_loss_8000_db is None
    assert "does not give it" in row.why_missing("transmission_loss_8000_db")
    assert "transmission_loss_8000_db" not in row.unquantified
    dashed = _of("Table 31")[-1]
    assert "—" in dashed.why_missing("transmission_loss_250_db")


# ---------------------------------------------------------------------------
# What the six tables say about each other
# ---------------------------------------------------------------------------
def test_break_in_is_three_decibels_under_breakout_at_the_top_of_the_range() -> None:
    """The one place the six tables can be checked against each other.

    Above the frequency where the duct stops behaving as a plane-wave guide,
    break-in and breakout differ by a fixed 3 dB, and the chapter's tables hold
    it exactly: on all seven rectangular sizes at 1, 2, 4 and 8 kHz, and on all
    seven flat oval sizes in the highest band each of them prints. That is
    thirty-five pairs drawn from four tables that two readers transcribed
    separately, so a single digit misread in any of them breaks it, and a row
    filed under the wrong direction breaks all four of its bands at once. The
    tables agreeing is the evidence here; the chapter's own break-in equations
    are on the same folios and are not transcribed by this catalogue.
    """
    rectangular_out = _by_construction("Table 29")
    rectangular_in = _by_construction("Table 33")
    assert set(rectangular_out) == set(rectangular_in)
    pairs = 0
    for construction, breakout in rectangular_out.items():
        break_in = rectangular_in[construction]
        for band in (1000, 2000, 4000, 8000):
            escaping = breakout.transmission_loss_db(band)
            entering = break_in.transmission_loss_db(band)
            assert escaping - entering == 3.0, (construction, band)
            pairs += 1

    oval_out = _by_construction("Table 31")
    oval_in = _by_construction("Table 34")
    assert set(oval_out) == set(oval_in)
    for construction, breakout in oval_out.items():
        break_in = oval_in[construction]
        assert breakout.bands() == break_in.bands()
        top = max(break_in.bands())
        difference = breakout.transmission_loss_db(top) - break_in.transmission_loss_db(
            top
        )
        assert difference == 3.0, (construction, top)
        pairs += 1
    assert pairs == 35


def test_the_two_measured_tables_are_the_only_ones_that_fall_with_frequency() -> None:
    """A tabulated duct wall rises band by band; a measured one does not.

    Tables 29, 31, 33 and 34 never once go down from one band to the next:
    twenty-eight rows, a hundred and sixty-four printed values and a hundred
    and thirty-six steps between adjacent bands, every one of them upward,
    which is what a smooth rule looks like. Tables 30 and 32, the two whose titles say "Experimentally
    Measured", fall dozens of times, because a real duct has a ring frequency
    and a breathing mode and the background sound moves around. A monotone run
    appearing in the two measured tables, or a fall appearing in the four
    smooth ones, would be a row transcribed into the wrong table or a digit
    read from the line above.
    """
    falls = {}
    for name in (*BREAKOUT_TABLES, *BREAK_IN_TABLES):
        counted = 0
        for row in _of(name):
            printed = [row.spectrum()[band] for band in row.bands()]
            counted += sum(
                1 for low, high in zip(printed, printed[1:], strict=False) if high < low
            )
        falls[name] = counted
    assert falls["Table 29"] == falls["Table 31"] == 0
    assert falls["Table 33"] == falls["Table 34"] == 0
    # The figures the docstring quotes, so a later reader can check them
    # against the transcription rather than take the sentence on trust.
    smooth = [row for name in (*BREAKOUT_TABLES, *BREAK_IN_TABLES) for row in _of(name)]
    smooth = [row for row in smooth if row.printed_table in SMOOTH_TABLES]
    assert len(smooth) == 28
    assert sum(len(list(row.bands())) for row in smooth) == 164
    assert sum(len(list(row.bands())) - 1 for row in smooth) == 136
    assert falls["Table 30"] > 0
    assert falls["Table 32"] > 0


def test_the_censored_cells_are_the_ones_counted_on_the_paper() -> None:
    """The census two readers took by eye, against what the catalogue holds.

    A bound read as a value, a parenthesis dropped, a rule read as a zero:
    each of those changes a count here, and none of them changes a digit, so
    this is the check the cell-by-cell comparison cannot make on its own. The
    numbers are the ones counted on the pages: four bounds and two
    parenthesised values in Table 30, thirteen and two in Table 32, and
    twenty-three rules in each of Tables 31 and 34.

    A parenthesised cell is counted off the row's note, because it holds no
    hedge: the value is a measurement and the parentheses are a mark about
    how well it was measured, which no hedge of this library means.
    """
    bounds = dict.fromkeys((*BREAKOUT_TABLES, *BREAK_IN_TABLES), 0)
    flagged = dict.fromkeys(bounds, 0)
    rules = dict.fromkeys(bounds, 0)
    for row in _rows():
        bounds[row.printed_table] += len(row.bounded_below)
        flagged[row.printed_table] += row.note.count("Hz cell is printed “(")
        rules[row.printed_table] += len(row.unquantified)
    assert not any(row.approximate for row in _rows())
    assert (bounds["Table 30"], flagged["Table 30"]) == (4, 2)
    assert (bounds["Table 32"], flagged["Table 32"]) == (13, 2)
    assert bounds["Table 32"] + flagged["Table 32"] == 15
    assert rules["Table 31"] == rules["Table 34"] == 23
    assert sum(rules.values()) == 46
    assert bounds["Table 29"] == bounds["Table 31"] == 0
    assert rules["Table 30"] == rules["Table 32"] == 0


def test_the_table_printed_twice_is_held_once() -> None:
    """Folio 49.31 and folio 49.32 print Table 34 complete, and agree.

    Keeping both printings would double seven rows and make every count in
    this file wrong by seven; keeping neither would lose a table. One set is
    kept, and each of its rows says on the page why there is one.
    """
    flat_oval_break_in = _of("Table 34")
    assert len(flat_oval_break_in) == 7
    for row in flat_oval_break_in:
        assert "printed twice" in row.note
        assert "49.32" in row.note


# ---------------------------------------------------------------------------
# Two quantities, never one
# ---------------------------------------------------------------------------
def test_each_row_is_one_direction_and_says_which() -> None:
    for row in _rows():
        assert row.is_breakout != row.is_break_in
        assert row.direction in {"breakout", "break-in"}
    assert [row.direction for row in _of("Table 29")] == ["breakout"] * 7
    assert [row.direction for row in _of("Table 32")] == ["break-in"] * 9


def test_one_size_in_the_two_directions_is_two_rows() -> None:
    """The reason there are forty-six rows and not twenty-three.

    A 305 by 305 mm duct of 24 gauge is printed in Table 29 and again in
    Table 33, and the two are 21 and 16 dB at 63 Hz. A catalogue with one row
    per construction would have to pick one of them, or put them in two
    columns and claim the page had measured one specimen twice, which it never
    says it did.
    """
    both = duct_wall_named("305 × 305 mm")
    assert len(both) == 2
    breakout, break_in = both
    assert (breakout.direction, break_in.direction) == ("breakout", "break-in")
    assert breakout.first_side_mm == break_in.first_side_mm == 305
    assert breakout.sheet_metal_gauge == break_in.sheet_metal_gauge == "24"
    assert breakout.transmission_loss_db(63) == 21
    assert break_in.transmission_loss_db(63) == 16


def test_the_round_tables_cannot_be_paired_at_all() -> None:
    """Why the decision is the page's and not a preference.

    Breakout was measured on ducts of 200, 350, 560 and 810 mm at 4.6 m and
    break-in on ducts of 203, 356, 559 and 813 mm at 4.57 m, and the two
    spiral wound blocks share no diameter, length and gauge between them. A
    row carrying both quantities would have nothing to be a row of.
    """
    breakout = {(row.diameter_mm, row.duct_length_m) for row in _of("Table 30")}
    break_in = {(row.diameter_mm, row.duct_length_m) for row in _of("Table 32")}
    assert breakout & break_in == set()
    long_seam_out = [row for row in _of("Table 30") if row.group == "Long Seam Ducts"]
    long_seam_in = [row for row in _of("Table 32") if row.group == "Long Seam Ducts"]
    assert [row.diameter_mm for row in long_seam_out] == [200, 350, 560, 810]
    assert [row.diameter_mm for row in long_seam_in] == [203, 356, 559, 813]
    assert {row.duct_length_m for row in long_seam_out} == {4.6}
    assert {row.duct_length_m for row in long_seam_in} == {4.57}


# ---------------------------------------------------------------------------
# What the page could not say
# ---------------------------------------------------------------------------
def test_a_bound_is_refused_rather_than_served_as_a_value() -> None:
    """``>45`` is not 45 dB, and a caller who asks is told so.

    Answering 45 would under-report a wall the measurement could not see past;
    answering zero would say the wall transmits everything. The refusal names
    the band and quotes the bound instead.

    The open end of the range holds nothing. A transmission loss has no
    ceiling, so there is no number to put there: the first shape of this
    catalogue put an infinity, which is not a value the page gives, is not a
    token JSON has, and reached the published table as the high end of a
    two-sided interval.
    """
    row = _of("Table 30")[0]
    assert row.transmission_loss_63_db is None
    assert row.ranges["transmission_loss_63_db"] == (45.0, None)
    with pytest.raises(ValueError, match="lower bound of 45"):
        row.transmission_loss_db(63)
    ends = [end for row in _rows() for end in row.ranges.values() for end in end]
    assert not any(end is not None and math.isinf(end) for end in ends)


def test_a_rule_keeps_the_glyph_and_is_given_no_meaning() -> None:
    """The chapter prints the mark and no legend for it anywhere.

    Recording it as "not measured" or as "below the floor" would be writing a
    footnote the page does not have, so the cell holds the glyph and
    ``why_missing`` reads it back as what is printed there.
    """
    row = _of("Table 34")[-1]
    assert row.unquantified["transmission_loss_250_db"] == "—"
    with pytest.raises(ValueError, match="250 Hz band"):
        row.transmission_loss_db(250)


def test_a_value_in_parentheses_is_held_as_printed_and_the_mark_is_recorded() -> None:
    """The parentheses are about the measurement, not about the number.

    The only legend the chapter prints for them is the note under Table 32:
    "Parentheses indicate measurements in which background sound produced
    greater uncertainty than usual." That is not a number rounded on purpose,
    which is what ``approximate`` means and what the published table reads it
    back as ("the page prints it with a tilde"), and no tilde is printed
    anywhere on these folios. So the value is served exactly as printed and
    the mark is recorded in the row's note, in the page's own words.
    """
    marked = [row for row in _rows() if "greater uncertainty than usual" in row.note]
    assert len(marked) == 4
    assert [row.printed_table for row in marked] == [
        "Table 30",
        "Table 30",
        "Table 32",
        "Table 32",
    ]
    for row in marked:
        assert not row.approximate
        assert "Parentheses indicate measurements" in row.note
        assert "approximate" in row.note
    first = _of("Table 30")[0]
    assert first.transmission_loss_db(125) == 53
    assert not first.is_approximate("transmission_loss_125_db")
    assert "(53)" in first.note


def test_the_gauge_is_held_as_printed_and_no_thickness_is_offered() -> None:
    """The chapter never prints the gauge to thickness conversion.

    Bringing one in from outside would put a number in this catalogue that no
    page of the source has, and the asterisk on two of the gauges is the
    page's own marker for a lined duct, so it stays on the string.
    """
    gauges = {row.sheet_metal_gauge for row in _rows()}
    assert gauges == {"16", "18", "20", "22", "24", "24*", "26", "26*"}
    assert not hasattr(_rows()[0], "sheet_thickness_mm")
    lined = [row for row in _rows() if "*" in row.sheet_metal_gauge]
    assert len(lined) == 2
    for row in lined:
        assert "internally lined" in row.note


def test_every_row_credits_the_running_text_that_credits_it() -> None:
    """No table carries a source line, and all six are credited in prose.

    The credit is the only provenance these rows have beyond the citation of
    the file, so it is held to the sentence the second reader copied off the
    page: the quotation verbatim, the PDF page and the printed folio it is on,
    and the statement that the table itself carries no source line. Three
    substrings would pass an invented credit that happened to name Cummings.
    """
    seen = set()
    for row in _rows():
        credit = row.attributed_to["table"]
        page, folio, sentence = ref.ASHRAE_49_CREDITS[row.direction]
        assert sentence in credit
        assert f"PDF page {page}" in credit
        assert f"folio {folio}" in credit
        assert "carries no source line" in credit
        assert set(row.attributed_to) == {"table"}
        seen.add(credit)
    assert len(seen) == 2


def test_the_break_in_credit_quotes_a_sentence_the_chapter_got_wrong() -> None:
    """It is quoted as printed, and the defect is registered rather than fixed.

    The sentence on folio 49.31 says Table 32 is the rectangular one and
    Table 33 the round one; the printed titles over those tables, the columns
    under them (a diameter and a length against two sides) and the 8 kHz
    column only the rectangular tables print all say the opposite. Rewriting
    the quotation would be this library correcting a source inside a field
    whose whole job is to reproduce it, so the words stay and the row says
    where the defect is recorded.
    """
    _page, _folio, sentence = ref.ASHRAE_49_CREDITS["break-in"]
    assert "rectangular ducts are given in Table 32" in sentence
    assert "round ducts in Table 33" in sentence
    for row in _rows():
        if row.is_break_in:
            credit = row.attributed_to["table"]
            assert sentence in credit
            assert "the wrong way round" in credit
            assert "docs/ERRATA.md" in credit
    circular = _of("Table 32")[0]
    rectangular = _of("Table 33")[0]
    assert (circular.shape, circular.diameter_mm) == ("circular", 203)
    assert (rectangular.shape, rectangular.first_side_mm) == ("rectangular", 305)
    assert rectangular.transmission_loss_db(8000) == 42
    assert 8000 not in circular.bands()


# ---------------------------------------------------------------------------
# The shape of the catalogue
# ---------------------------------------------------------------------------
def test_the_lookup_matches_a_part_of_a_printed_label() -> None:
    assert len(duct_wall_named("1220")) == 14
    assert duct_wall_named("305 × 152") == duct_wall_named("305 × 152 MM")
    assert duct_wall_named("unobtainium") == ()


def test_the_bands_these_tables_print_are_published() -> None:
    """A caller asks which bands a duct-wall table has without a private name.

    Every other banded catalogue of this library publishes its band tuple, and
    a caller who wants to lay two catalogues side by side needs this one to do
    the same. The rows themselves answer with the subset each of them fills.
    """
    assert DUCT_WALL_BANDS_HZ == (63, 125, 250, 500, 1000, 2000, 4000, 8000)
    assert noise_control.DUCT_WALL_BANDS_HZ is DUCT_WALL_BANDS_HZ
    for row in _rows():
        assert set(row.bands()) <= set(DUCT_WALL_BANDS_HZ)
    assert _of("Table 29")[0].bands() == DUCT_WALL_BANDS_HZ
    assert _of("Table 30")[0].bands() == DUCT_WALL_BANDS_HZ[1:7]


def test_the_data_file_is_json_that_anything_can_read() -> None:
    """The site reads these rows from JavaScript, not from Python.

    ``Infinity`` is an extension of CPython's ``json`` module: ``JSON.parse``
    refuses it on its first character. This file held seventeen of them, as
    the open end of every lower bound, and imported cleanly the whole time.
    """
    from importlib.resources import files

    def _not_a_json_constant(token: str) -> float:
        msg = f"{token} is a Python constant, not JSON"
        raise ValueError(msg)

    text = (files("phonometry.noise_control.data") / f"{TABLE}.json").read_text(
        encoding="utf-8"
    )
    document = json.loads(text, parse_constant=_not_a_json_constant)
    assert len(document["rows"]) == 46


def test_a_frequency_no_table_prints_is_refused_as_such() -> None:
    row = _rows()[0]
    with pytest.raises(ValueError, match="not an octave band"):
        row.transmission_loss_db(700)


def test_the_catalogue_is_reachable_from_the_package() -> None:
    assert (
        noise_control.PUBLISHED_DUCT_TRANSMISSION_LOSS
        is PUBLISHED_DUCT_TRANSMISSION_LOSS
    )
    assert all(key.startswith(f"{TABLE}/") for key in PUBLISHED_DUCT_TRANSMISSION_LOSS)


def test_the_catalogue_cannot_be_written_to() -> None:
    with pytest.raises(TypeError):
        PUBLISHED_DUCT_TRANSMISSION_LOSS["x/y"] = DuctWallSpectrum(  # type: ignore[index]
            name="x", source="nowhere"
        )


def test_every_value_is_a_plausible_duct_wall_transmission_loss() -> None:
    """Between ten and sixty decibels, which is what these tables print.

    The floor is the 1220 by 1220 mm rectangular duct at 63 Hz, printed 10 dB
    for break-in, and the ceiling is the 350 mm long seam duct at 125 Hz,
    printed 60. A value outside that is a digit slipped rather than a duct.
    """
    for row in _rows():
        for band, value in row.spectrum().items():
            assert 10 <= value <= 60, f"{row.name} at {band} Hz: {value}"
