#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The published absorption coefficients, against a second reading of the pages.

The catalogues and the oracles in :mod:`tests.reference_data.absorption` were
transcribed from the rendered pages by two readers who never saw each other's
work, and compared cell by cell before either was kept. These tests keep that
comparison alive: an edit to a data file that the oracle does not share, or
the other way round, fails here.

The rest is the shape: that a band the page did not print stays empty and
says so, that the rows a page prints as an area per person are areas and not
coefficients, that a mount the page prints stays with the row and a board
printed on two mounts is two rows, that sabins become square metres and say
so, and that a name lookup returns every row that matches rather than
choosing one.
"""

from __future__ import annotations

import re

import pytest
import reference_data as ref

from phonometry.materials.absorbers import (
    ABSORPTION_BANDS_HZ,
    PUBLISHED_ABSORPTION,
    PUBLISHED_ABSORPTION_AREAS,
    AbsorptionAreaSpectrum,
    AbsorptionSpectrum,
    absorption_named,
)

#: Bies 5e Table 6.2 keyed the way the catalogue keys it.
BIES = "bies-2017-table-6-2"

#: Long 2e Table 7.1 keyed the way the catalogue keys it.
LONG = "long-2014-table-7-1"

#: Cox & D'Antonio 3e Appendix A keyed the way the catalogue keys it.
COX = "cox-2017-appendix-a"

#: Arau-Puchades (1999) Table 6.1 keyed the way the catalogue keys it.
ARAU = "arau-1999-table-6-1"

#: Everest 4e's appendix keyed the way the catalogue keys it.
EVEREST = "everest-2001-appendix"

#: A square foot in square metres, which is what a sabin is in a table set in
#: inches, and a thousand cubic feet in cubic metres. Both exact, and both
#: written here again rather than imported so that the test does not check the
#: library's constant against itself.
SQUARE_FOOT_M2 = 0.3048**2
THOUSAND_CUBIC_FEET_M3 = 1000 * 0.3048**3


def _rows_of(table: str) -> list[AbsorptionSpectrum | AbsorptionAreaSpectrum]:
    """Every row of one table, coefficients and areas, in catalogue order."""
    mixed: list[tuple[str, AbsorptionSpectrum | AbsorptionAreaSpectrum]] = [
        *((key, row) for key, row in PUBLISHED_ABSORPTION.items()),
        *((key, row) for key, row in PUBLISHED_ABSORPTION_AREAS.items()),
    ]
    return [row for key, row in mixed if key.startswith(f"{table}/")]


def _plain(text: str) -> str:
    """A printed name with its list punctuation and line-fitting spaces dropped.

    The page prints a heading as "Plaster, gypsum or lime, smooth finish;" and
    its sub-rows as "on brick," and "on lath", and prints "kg/ m2" where a
    line was justified. The oracle keeps all of that, because it is what the
    page shows; the catalogue drops it, because a semicolon that closes a
    list is not part of a name. This is the rule that lets the two be
    compared, and it is all of it. A trailing parenthesis holding a year is
    the page's credit for the row, which the catalogue holds in
    ``attributed_to`` rather than in the name, and it is dropped the same way.
    """
    text = re.sub(r"\s*\([^()]*\d{4}\)$", "", text)
    parts = [part.strip().rstrip(";,") for part in text.split(" / ")]
    return " / ".join(parts).replace("/ ", "/")


def _printed_name(row: AbsorptionSpectrum | AbsorptionAreaSpectrum) -> str:
    """The name the way the Bies oracle writes it: heading and sub-row joined."""
    return f"{row.name} / {row.variant}" if row.variant else row.name


def _prints_as(row: AbsorptionSpectrum | AbsorptionAreaSpectrum, printed: str) -> bool:
    """Whether Long's page would print this row under *printed*.

    Long prints a thickness alone under a bold heading, "1/2″" under "Duct
    Liners", which the catalogue holds as the variant under the heading; and
    prints the first K-13 coating with its thickness in the name, "Acoustical
    coating K-13 1″", and the next two as "1.5″" and "2″". So a row prints as
    its name, as its variant, or as the two joined by a space.
    """
    candidates = {row.name, row.variant, f"{row.name} {row.variant}"}
    return printed in candidates


# ---------------------------------------------------------------------------
# The transcription against the second reading
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_every_row_of_the_table() -> None:
    """Fifty-nine rows, fifty-seven of them coefficients and two areas."""
    coefficients = [k for k in PUBLISHED_ABSORPTION if k.startswith(f"{BIES}/")]
    areas = [k for k in PUBLISHED_ABSORPTION_AREAS if k.startswith(f"{BIES}/")]
    kinds = [kind for _, _, kind, _ in ref.BIES_6_2_ABSORPTION]
    assert len(coefficients) == kinds.count(ref.COEF)
    assert len(areas) == kinds.count(ref.AREA)


@pytest.mark.parametrize(
    ("group", "name", "kind", "values"),
    ref.BIES_6_2_ABSORPTION,
    ids=[name[:40] for _, name, _, _ in ref.BIES_6_2_ABSORPTION],
)
def test_each_row_holds_what_the_second_reader_read(
    group: str, name: str, kind: str, values: tuple[float | None, ...]
) -> None:
    """Cell by cell, with the empty 63 Hz cells empty on both sides."""
    printed = _plain(name.split(" S ")[0] if kind == ref.AREA else name)
    matches = [row for row in _rows_of(BIES) if _plain(_printed_name(row)) == printed]
    assert len(matches) == 1, f"{printed!r} matched {len(matches)} rows"
    row = matches[0]
    assert row.group == group
    if kind == ref.AREA:
        assert isinstance(row, AbsorptionAreaSpectrum)
        fields = [f"absorption_area_{band}_m2" for band in ref.BIES_6_2_BANDS_HZ]
    else:
        assert isinstance(row, AbsorptionSpectrum)
        fields = [f"absorption_coefficient_{band}" for band in ref.BIES_6_2_BANDS_HZ]
    assert [getattr(row, field) for field in fields] == list(values)


def test_the_first_row_credits_the_study_the_page_prints_beside_it() -> None:
    """The one credit on the page, kept out of the name and into the credit."""
    row = PUBLISHED_ABSORPTION[f"{BIES}/unoccupied_heavily_upholstered_seats"]
    assert row.attributed_to == {"row": "Beranek and Hidaka (1998)"}
    assert "Beranek" not in row.name


def test_the_two_bands_of_63_hz_are_the_only_ones() -> None:
    """The page fills that column on two rows and leaves it empty elsewhere."""
    filled = [
        row.name
        for row in PUBLISHED_ABSORPTION.values()
        if row.table == BIES and row.absorption_coefficient_63 is not None
    ]
    assert filled == [
        "Unoccupied – average well-upholstered seating areas",
        "100% occupied audience (orchestra and chorus areas) – upholstered seats",
    ]


# ---------------------------------------------------------------------------
# Long's table against the second reading, mount included
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_every_row_of_long() -> None:
    """A hundred and two rows, a hundred coefficients and two areas."""
    coefficients = [k for k in PUBLISHED_ABSORPTION if k.startswith(f"{LONG}/")]
    areas = [k for k in PUBLISHED_ABSORPTION_AREAS if k.startswith(f"{LONG}/")]
    kinds = [kind for _, _, _, kind, _ in ref.LONG_7_1_ABSORPTION]
    assert len(coefficients) == kinds.count(ref.COEF) == 100
    assert len(areas) == kinds.count(ref.AREA) == 2


@pytest.mark.parametrize(
    ("group", "name", "mount", "kind", "values"),
    ref.LONG_7_1_ABSORPTION,
    ids=[
        f"{name[:32]}/{mount or 'none'}"
        for _, name, mount, _, _ in ref.LONG_7_1_ABSORPTION
    ],
)
def test_each_long_row_holds_what_the_second_reader_read(
    group: str, name: str, mount: str, kind: str, values: tuple[float | None, ...]
) -> None:
    """Cell by cell, the mount included, with the sabins converted on this side.

    The oracle keeps the sabins the page prints; the catalogue holds square
    metres. The conversion is redone here from the foot, so a wrong factor in
    the library and a wrong factor in this test would have to agree to pass.
    """
    matches = [
        row
        for row in _rows_of(LONG)
        if row.group == group
        and _prints_as(row, name)
        and getattr(row, "mounting", "") == mount
    ]
    assert len(matches) == 1, f"{name!r} on {mount!r} matched {len(matches)} rows"
    row = matches[0]
    if kind == ref.COEF:
        assert isinstance(row, AbsorptionSpectrum)
        held = [
            getattr(row, f"absorption_coefficient_{band}")
            for band in ref.LONG_7_1_BANDS_HZ
        ]
        assert held == list(values)
        return
    assert isinstance(row, AbsorptionAreaSpectrum)
    factor = SQUARE_FOOT_M2
    unit = "sabins"
    if "per 1000 cubic feet" in name:
        factor /= THOUSAND_CUBIC_FEET_M3
        unit = "sabins per 1000 ft3"
    for band, printed in zip(ref.LONG_7_1_BANDS_HZ, values, strict=True):
        held = getattr(row, f"absorption_area_{band}_m2")
        if printed is None:
            assert held is None
            continue
        assert held == pytest.approx(printed * factor, rel=1e-12)
        assert not row.is_derived(f"absorption_area_{band}_m2")
        assert row.converted[f"absorption_area_{band}_m2"] == (repr(printed), unit)


def test_the_mount_is_printed_on_sixty_two_rows_and_on_none_of_bies() -> None:
    long_rows = [row for row in PUBLISHED_ABSORPTION.values() if row.table == LONG]
    assert sum(1 for row in long_rows if row.mounting) == 62
    assert {row.mounting for row in long_rows} == {"", "A", "E400", "F"}
    assert all(
        not row.mounting for row in PUBLISHED_ABSORPTION.values() if row.table == BIES
    )


def test_the_same_board_on_two_mounts_is_two_rows_with_two_spectra() -> None:
    """Long prints the fibreglass board on the floor and over a 400 mm airspace."""
    floor = PUBLISHED_ABSORPTION[f"{LONG}/fb_3lb_ft3_1in_thick_a"]
    airspace = PUBLISHED_ABSORPTION[f"{LONG}/fb_3lb_ft3_1in_thick_e400"]
    assert floor.name == airspace.name == "FB, 3lb/ft³, 1″ thick"
    assert (floor.mounting, airspace.mounting) == ("A", "E400")
    assert floor.spectrum()[125] == 0.03
    assert airspace.spectrum()[125] == 0.65


def test_a_thickness_printed_alone_is_held_under_its_heading() -> None:
    liners = [
        row
        for row in PUBLISHED_ABSORPTION.values()
        if row.table == LONG and row.name == "Duct Liners"
    ]
    assert [row.variant for row in liners] == ["1/2″", "1″", "1 1/2″", "2″"]
    assert all(not row.mounting for row in liners)


def test_the_musician_is_an_area_per_person_in_square_metres_marked_converted() -> None:
    """The page prints sabins; the field says m2 and holds m2, and says so."""
    row = PUBLISHED_ABSORPTION_AREAS[f"{LONG}/musician_per_person_with_instrument"]
    assert row.per == "person"
    assert row.bands() == (125, 250, 500, 1000, 2000, 4000)
    assert row.spectrum()[125] == pytest.approx(4.0 * SQUARE_FOOT_M2)
    assert row.converted["absorption_area_125_m2"] == ("4.0", "sabins")
    assert not row.is_derived("absorption_area_125_m2")
    assert not hasattr(row, "absorption_area_125_ft2")


def test_the_air_is_an_area_per_cubic_metre_in_the_three_bands_the_page_fills() -> None:
    """Sabins per 1000 cubic feet, taken to square metres per cubic metre."""
    row = PUBLISHED_ABSORPTION_AREAS[
        f"{LONG}/air_sabins_per_1000_cubic_feet_at_50percent_rh"
    ]
    assert row.per == "cubic metre of air at 50% RH"
    assert row.bands() == (1000, 2000, 4000)
    assert row.spectrum()[1000] == pytest.approx(
        0.9 * SQUARE_FOOT_M2 / THOUSAND_CUBIC_FEET_M3
    )
    assert row.converted["absorption_area_1000_m2"] == ("0.9", "sabins per 1000 ft3")
    assert "does not give it" in row.why_missing("absorption_area_125_m2")


# ---------------------------------------------------------------------------
# The shape of a spectrum row
# ---------------------------------------------------------------------------
def test_a_row_reads_back_as_a_spectrum_over_the_bands_it_prints() -> None:
    row = PUBLISHED_ABSORPTION[f"{BIES}/carpet_heavy_on_concrete"]
    assert row.bands() == (125, 250, 500, 1000, 2000, 4000)
    assert row.spectrum() == {
        125: 0.02,
        250: 0.06,
        500: 0.14,
        1000: 0.37,
        2000: 0.60,
        4000: 0.65,
    }


def test_a_band_the_page_did_not_print_is_refused_by_name() -> None:
    """Not a zero and not a guess: a refusal that names the row and the band."""
    row = PUBLISHED_ABSORPTION[f"{BIES}/carpet_heavy_on_concrete"]
    with pytest.raises(ValueError, match="63 Hz band"):
        row.absorption_coefficient(63)
    assert row.why_missing("absorption_coefficient_63")


def test_a_frequency_no_table_prints_is_refused_as_such() -> None:
    row = PUBLISHED_ABSORPTION[f"{BIES}/carpet_heavy_on_concrete"]
    with pytest.raises(ValueError, match="not an octave band"):
        row.absorption_coefficient(700)


def test_every_row_prints_only_bands_the_catalogue_knows() -> None:
    for row in PUBLISHED_ABSORPTION.values():
        assert set(row.bands()) <= set(ABSORPTION_BANDS_HZ)


def test_every_coefficient_is_between_zero_and_one_or_a_little_above() -> None:
    """A Sabine coefficient above 1 is common; one far above it is a misread.

    The reverberation-room method can give more than 1 for an absorbent
    sample because of edge diffraction, and books print it as 1.0 or a little
    over; Long's highest is 1.33, for six inches of fibreglass at 250 Hz. A
    value of 2 or of 12 is a digit slipped, which is what this catches.
    """
    for key, row in PUBLISHED_ABSORPTION.items():
        for band, value in row.spectrum().items():
            assert 0.0 <= value <= 1.5, f"{key} at {band} Hz: {value}"


# ---------------------------------------------------------------------------
# Areas per person, kept apart
# ---------------------------------------------------------------------------
def test_the_areas_per_person_are_not_in_the_coefficient_catalogue() -> None:
    """A square metre behind a field named coefficient is the hazard."""
    assert f"{BIES}/audience_per_person_seated" in PUBLISHED_ABSORPTION_AREAS
    assert f"{BIES}/audience_per_person_seated" not in PUBLISHED_ABSORPTION


def test_an_area_row_says_what_it_is_per() -> None:
    row = PUBLISHED_ABSORPTION_AREAS[f"{BIES}/audience_per_person_standing"]
    assert row.per == "person"
    assert row.spectrum()[125] == 0.15
    assert row.bands() == (125, 250, 500, 1000, 2000, 4000)


# ---------------------------------------------------------------------------
# Looking a finish up
# ---------------------------------------------------------------------------
def test_a_fragment_answers_with_every_finish_that_contains_it() -> None:
    """Carpets from all three books at once, which is the point of the lookup.

    Four in Bies, four in Long and thirteen in Cox, whose appendix compiles
    carpets from six of its own sources. No book has them all and no two
    describe one the same way, so the caller gets every match and reads the
    names to pick theirs.
    """
    carpets = absorption_named("carpet")
    tables = [row.table for row in carpets]
    assert (tables.count(BIES), tables.count(LONG), tables.count(COX)) == (4, 4, 13)
    assert all("carpet" in row.name.casefold() for row in carpets)


def test_the_lookup_ignores_case() -> None:
    assert absorption_named("VELOUR") == absorption_named("velour")


def test_a_fragment_no_page_prints_answers_with_nothing() -> None:
    assert absorption_named("unobtainium") == ()


def test_a_sub_row_keeps_its_heading_as_the_name() -> None:
    """The page prints a heading and thirteen indented blankets under it."""
    blankets = [
        row
        for row in PUBLISHED_ABSORPTION.values()
        if row.table == BIES and row.name == "Fibreglass or rockwool blanket"
    ]
    assert len(blankets) == 13
    assert blankets[0].variant == "16 kg/m³, 25 mm thick"
    assert blankets[-1].variant == "60 kg/m³, 50 mm thick"


# ---------------------------------------------------------------------------
# The catalogue as an object
# ---------------------------------------------------------------------------
def test_the_catalogues_cannot_be_written_to() -> None:
    with pytest.raises(TypeError):
        PUBLISHED_ABSORPTION["x/y"] = AbsorptionSpectrum(  # type: ignore[index]
            name="x", source="nowhere"
        )
    with pytest.raises(TypeError):
        PUBLISHED_ABSORPTION_AREAS["x/y"] = AbsorptionAreaSpectrum(  # type: ignore[index]
            name="x", source="nowhere"
        )


# ---------------------------------------------------------------------------
# What the two books say about the same finish
# ---------------------------------------------------------------------------
#: ``(Bies row, Long row, the bands where the two disagree)``. Ten finishes
#: the two books describe in words that mean the same thing, found by reading
#: the names rather than by matching them, because no two books word one the
#: same way: Bies writes a velour in grams per square metre and Long the same
#: velour in ounces per square yard.
#:
#: Five of the ten agree in every band they share, digit for digit, which says
#: the two tables are compilations of the same older measurements rather than
#: two independent sets. The other five agree everywhere but one cell, and
#: that cell is what a catalogue keyed by table exists to show: a reader who
#: took either book alone would never learn that the other prints 0.57 where
#: this one prints 0.37. It is not an erratum in either. Neither page
#: contradicts itself, and a disagreement between two books is a disagreement
#: between two books.
CROSS_BOOK = (
    ("glass_heavy_plate", "glass_1_4in_heavy_plate", {1000: (0.03, 0.05)}),
    ("concrete_block_painted", "concrete_block_painted", {125: (0.01, 0.10)}),
    ("carpet_heavy_on_concrete", "carpet_heavy_on_concrete", {1000: (0.37, 0.57)}),
    ("ordinary_window", "glass_3_32in_ordinary_window", {125: (0.35, 0.55)}),
    ("concrete_or_terrazzo", "floors_concrete_or_terrazzo", {500: (0.01, 0.015)}),
    ("gypsum_board_on_50_100_mm_studs", "gypsum_board_1_2in_on_2_x_4_studs", {}),
    (
        "plaster_gypsum_or_lime_smooth_finish_on_brick",
        "plaster_7_8in_gypsum_or_lime_on_brick",
        {},
    ),
    ("unoccupied_metal_or_wood_seats", "chair_metal_or_wood_seat_unoccupied", {}),
    (
        "medium_velour_475_g_m2_draped_to_half_area",
        "medium_velour_14_oz_per_sq_yd_draped_to_half_area",
        {},
    ),
    (
        "heavy_velour_610_g_m2_draped_to_half_area",
        "heavy_velour_18_oz_per_sq_yd_draped_to_half_area",
        {},
    ),
)


@pytest.mark.parametrize(("bies", "long", "apart"), CROSS_BOOK)
def test_the_two_books_agree_about_a_finish_except_where_they_do_not(
    bies: str, long: str, apart: dict[int, tuple[float, float]]
) -> None:
    """Band by band, with the cells that differ named and their two values kept.

    This is the comparison neither book can make on its own, and it is also a
    check on both transcriptions: a digit slipped in either would show up here
    as a disagreement that is not in the list, or as an agreement that is.
    """
    left = PUBLISHED_ABSORPTION[f"{BIES}/{bies}"].spectrum()
    right = PUBLISHED_ABSORPTION[f"{LONG}/{long}"].spectrum()
    for band in sorted(set(left) & set(right)):
        if band not in apart:
            assert left[band] == right[band], f"{band} Hz: {left[band]}, {right[band]}"
            continue
        in_bies, in_long = apart[band]
        assert left[band] == in_bies
        assert right[band] == in_long


def test_the_pair_that_differs_most_is_the_carpet_at_one_kilohertz() -> None:
    """Not an erratum, and worth a reader's attention all the same.

    The heaviest disagreement of the ten is a heavy carpet on concrete, where
    one book prints 0.37 at 1 kHz and the other 0.57 and every other band of
    the row is identical. Nothing on either page says which is the typing
    mistake, so both are served, each keyed by the book it came off, and
    :func:`absorption_named` hands a caller both.
    """
    carpets = {
        row.table: row.spectrum()[1000]
        for row in absorption_named("carpet, heavy")
        if "concrete" in row.name.casefold()
    }
    assert carpets == {BIES: 0.37, LONG: 0.57}


# ---------------------------------------------------------------------------
# The compilation: Cox Appendix A against the second reading
# ---------------------------------------------------------------------------
def _cox_prints_as(row: AbsorptionSpectrum, printed: str) -> bool:
    """Whether Cox's page prints this catalogue row under *printed*.

    Five of the appendix's groups head a block of rows that are only a
    condition or a percentage, and the catalogue holds those with the heading
    as the name and the printed row as the variant, so a row prints as its
    name, as its variant, or as the two joined. The credit is checked
    separately, so the reference markers are dropped on both sides.
    """
    candidates = {row.name, row.variant, f"{row.name} {row.variant}".strip()}
    return printed in {_plain_cox(text) for text in candidates if text}


def _ascii(text: str) -> str:
    """A name with the characters two readers spell differently written out.

    One reading typed the superscript the page prints and the other its ASCII
    stand-in, and neither is wrong about the paper: "kg/m²" and "kg/m2" are
    the same square metre. The catalogue keeps the character the page uses;
    this is only for comparing the two readings.
    """
    return (
        text.replace("²", "2")
        .replace("³", "3")
        .replace("⁻¹", "-1")
        .replace("×", "x")
        .replace("–", "-")
        .replace("—", "-")
        .replace("”", '"')
        .replace("“", '"')
    )


def _plain_cox(text: str) -> str:
    """A name reduced to what the two readings can be compared on.

    The reference markers go, because the credit is checked on its own; the
    superscript two and three, the multiplication sign and the en dash are
    written out, because one reading typed the character the page prints and
    the other typed its ASCII stand-in, and neither is wrong about the paper.
    """
    text = re.sub(r"\(\d+(?:,\d+)*\)", "", text)
    text = (
        text.replace("²", "2")
        .replace("³", "3")
        .replace("×", "x")
        .replace("–", "-")
        .replace("—", "-")
    )
    return re.sub(r"\s+", " ", text).strip().rstrip(",")


def test_the_catalogue_holds_every_row_of_the_appendix() -> None:
    """A hundred and sixty-one rows, and the appendix has no area rows."""
    rows = [k for k in PUBLISHED_ABSORPTION if k.startswith(f"{COX}/")]
    assert len(rows) == len(ref.COX_A_ABSORPTION) == 161
    assert not [k for k in PUBLISHED_ABSORPTION_AREAS if k.startswith(f"{COX}/")]


def test_every_cell_of_the_appendix_is_a_number() -> None:
    """The one table of the three with no empty cell anywhere.

    Nine hundred and sixty-six cells, all filled. A row that lost a cell in
    transcription, or gained one, fails here rather than quietly answering
    ``None`` to a caller who asked for a band the page does print.
    """
    for key, row in PUBLISHED_ABSORPTION.items():
        if row.table != COX:
            continue
        assert row.bands() == ref.COX_A_BANDS_HZ, key
        assert len(row.spectrum()) == 6


@pytest.mark.parametrize(
    ("group", "name", "values"),
    ref.COX_A_ABSORPTION,
    ids=[f"{name[:36]}" for _, name, _ in ref.COX_A_ABSORPTION],
)
def test_each_appendix_row_holds_what_the_second_reader_read(
    group: str, name: str, values: tuple[float, ...]
) -> None:
    """Cell by cell, matched by the printed name rather than by position."""
    printed = _plain_cox(name)
    matches = [
        row
        for row in _rows_of(COX)
        if isinstance(row, AbsorptionSpectrum) and _cox_prints_as(row, printed)
    ]
    assert matches, f"{printed!r} is in the oracle and not in the catalogue"
    held = [
        [getattr(row, f"absorption_coefficient_{band}") for band in ref.COX_A_BANDS_HZ]
        for row in matches
    ]
    assert list(values) in held, f"{printed!r}: {values} not among {held}"
    # The credit too, on the row the values matched: the page prints it as a
    # superscript number, and a number that moved from one row to another is
    # as much a transcription error as a digit that did.
    row = matches[held.index(list(values))]
    numbers = re.findall(r"\((\d+(?:,\d+)*)\)", f"{group} {name}")
    printed_credit = "; ".join(
        ref.COX_A_REFERENCES[number]
        for group_of in numbers
        for number in group_of.split(",")
    )
    if printed_credit:
        assert row.attributed_to.get("row") == printed_credit


def test_a_credit_the_page_prints_as_a_number_is_held_as_the_reference() -> None:
    """Twenty-nine sources behind one appendix, and the row says which.

    A superscript 2 means nothing away from the page it is printed on, so the
    catalogue holds the reference the number points at. The reference list is
    on the page after the table.
    """
    row = PUBLISHED_ABSORPTION[f"{COX}/carpet_heavy_on_concrete"]
    assert row.attributed_to == {"row": "Harris (1991)"}
    two = PUBLISHED_ABSORPTION[f"{COX}/floors_concrete_or_terrazzo"]
    assert two.attributed_to == {
        "row": "Harris (1991); Physikalisch-Technische Bundesanstalt (accessed 2003)"
    }


def test_the_four_rows_the_page_credits_to_nobody_carry_no_credit() -> None:
    """Not a guess and not an empty string: the page prints no marker."""
    uncredited = sorted(
        row.name
        for row in PUBLISHED_ABSORPTION.values()
        if row.table == COX and not row.attributed_to
    )
    assert uncredited == [
        "25 mm cork on solid backing",
        "Anechoic chamber wall (wedges)",
        "Polyurethane foam, 2.5 cm thick",
        "Wood, 50 mm thick",
    ]


def test_a_row_printed_only_as_a_percentage_keeps_its_heading() -> None:
    """ "20%" is not a material, so the heading is the name and 20% the variant."""
    row = PUBLISHED_ABSORPTION[
        f"{COX}/top_soil_with_different_percentage_of_vegetative_cover_20percent"
    ]
    assert row.name == "Top soil with different percentage of vegetative cover"
    assert row.variant == "20%"
    assert row.attributed_to == {"row": "Yang, Kang and Cheal (2013)"}


def test_the_same_name_twice_is_two_rows_keyed_by_who_measured_it() -> None:
    """The appendix prints two swimming pools, from two sources, side by side."""
    pools = [
        row
        for row in PUBLISHED_ABSORPTION.values()
        if row.table == COX and row.name == "Water surface in swimming pool"
    ]
    assert len(pools) == 2
    assert {row.attributed_to["row"] for row in pools} == {
        "Knudsen and Harris (1953)",
        "Harris (1991)",
    }
    assert {row.spectrum()[125] for row in pools} == {0.01, 0.008}


# ---------------------------------------------------------------------------
# Arau's numbered list, in Spanish, with its intervals and its dashes
# ---------------------------------------------------------------------------
#: The rows of Arau's table that are the air attenuation coefficient m, in
#: reciprocal metres, rather than an absorption coefficient. The page prints
#: them inside the same table; the catalogue does not serve them.
ARAU_AIR_ROWS = (63, 64, 65)


def _arau_key(number: int) -> str:
    """The catalogue key of one printed row number, whatever its name is."""
    prefix = f"{ARAU}/{number:02d}_"
    keys = [key for key in PUBLISHED_ABSORPTION if key.startswith(prefix)]
    assert len(keys) == 1, f"row {number} matched {keys}"
    return keys[0]


def test_the_catalogue_holds_every_row_but_the_three_that_are_not_coefficients() -> (
    None
):
    """Ninety-nine printed rows, ninety-six served.

    The three the page prints as the air attenuation coefficient m are in the
    oracle, because the page prints them in this table, and out of the
    catalogue, because a value in reciprocal metres behind a dimensionless
    field is a unit error waiting to happen.
    """
    served = [k for k in PUBLISHED_ABSORPTION if k.startswith(f"{ARAU}/")]
    assert len(ref.ARAU_6_1_ABSORPTION) == 99
    assert len(served) == 99 - len(ARAU_AIR_ROWS)
    for number in ARAU_AIR_ROWS:
        assert not [k for k in served if k.startswith(f"{ARAU}/{number:02d}_")]


@pytest.mark.parametrize(
    ("number", "name", "values"),
    [row for row in ref.ARAU_6_1_ABSORPTION if row[0] not in ARAU_AIR_ROWS],
    ids=[
        f"{number:02d}"
        for number, _, _ in ref.ARAU_6_1_ABSORPTION
        if number not in ARAU_AIR_ROWS
    ],
)
def test_each_arau_row_holds_what_the_second_reader_read(
    number: int, name: str, values: tuple[object, ...]
) -> None:
    """Cell by cell, with an interval an interval and a dash an empty cell.

    Arau writes an interval as two lines with the word "a" between them, and
    the catalogue holds it in ``ranges`` with the field empty, which is what
    every other catalogue of this library does with a printed interval. A dash
    is a cell the page does not fill.
    """
    row = PUBLISHED_ABSORPTION[_arau_key(number)]
    printed = row.variant or row.name
    assert _ascii(printed) == _ascii(name)
    for band, value in zip(ref.ARAU_6_1_BANDS_HZ, values, strict=True):
        field = f"absorption_coefficient_{band}"
        if value is None:
            assert getattr(row, field) is None
        elif value == ref.RANGE_ACROSS_COLUMNS:
            assert getattr(row, field) is None
            assert row.unquantified[field] == ref.RANGE_ACROSS_COLUMNS
        elif isinstance(value, tuple):
            assert getattr(row, field) is None
            assert row.ranges[field] == value
        else:
            assert getattr(row, field) == value


def test_an_interval_says_so_rather_than_answering_with_a_midpoint() -> None:
    """Two rows print "0.01 a 0.02"; neither answers 0.015."""
    row = PUBLISHED_ABSORPTION[_arau_key(6)]
    assert row.absorption_coefficient_125 is None
    assert row.ranges["absorption_coefficient_125"] == (0.01, 0.02)
    assert "0.01 to 0.02" in row.why_missing("absorption_coefficient_125")
    with pytest.raises(ValueError, match="125 Hz band"):
        row.absorption_coefficient(125)


def test_the_grilles_say_what_the_page_prints_and_fill_no_band() -> None:
    """One interval, printed once, lying across the first two columns.

    Nothing on the page says which bands it is for, so no band gets it and
    all six say what is printed there instead.
    """
    row = PUBLISHED_ABSORPTION[_arau_key(96)]
    assert row.bands() == ()
    for band in ref.ARAU_6_1_BANDS_HZ:
        assert row.unquantified[f"absorption_coefficient_{band}"] == "0.15 – 0.50"
    assert "a caballo" in row.note


def test_a_row_that_says_idem_keeps_the_material_of_the_row_above() -> None:
    """ "Ídem 50 mm" is not a material, so the name is the one it refers to."""
    row = PUBLISHED_ABSORPTION[_arau_key(60)]
    assert row.name == "Fibra de vidrio 22 kg/m² 30 mm"
    assert row.variant == "Ídem 50 mm"
    assert PUBLISHED_ABSORPTION[_arau_key(20)].variant == (
        "Igual que 19, pero sin material absorbente"
    )


# ---------------------------------------------------------------------------
# Everest's appendix, where the credit is a column
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("group", "name", "values", "credit"),
    ref.EVEREST_ABSORPTION,
    ids=[f"{name[:34]}" for _, name, _, _ in ref.EVEREST_ABSORPTION],
)
def test_each_everest_row_holds_what_the_second_reader_read(
    group: str, name: str, values: tuple[float, ...], credit: str
) -> None:
    """Cell by cell, the credit column included.

    The page prints a label row and its variants underneath, so a row prints
    as its variant, as its name, or as the two joined; the catalogue holds the
    label as the name because "draped to 1/2 area" is three different drapes
    on one page.
    """
    printed = _ascii(name)
    matches = [
        row
        for row in _rows_of(EVEREST)
        if isinstance(row, AbsorptionSpectrum)
        and printed
        in {
            _ascii(row.name),
            _ascii(row.variant),
            _ascii(f"{row.name} {row.variant}".strip()),
            _ascii(f"{row.name}: {row.variant}".strip()),
        }
    ]
    held = [
        [getattr(row, f"absorption_coefficient_{b}") for b in ref.EVEREST_BANDS_HZ]
        for row in matches
    ]
    assert list(values) in held, f"{printed!r}: {values} not among {held}"
    row = matches[held.index(list(values))]
    assert row.group == group
    assert row.attributed_to.get("row", "") == credit


def test_the_two_rows_the_page_marks_with_a_dash_carry_no_credit() -> None:
    """Thirty-nine rows name a source; two print an em dash and nothing else.

    The page never says what the dash means, so the row says nothing either
    rather than inventing a source or borrowing the one above it.
    """
    uncredited = sorted(
        row.name
        for row in PUBLISHED_ABSORPTION.values()
        if row.table == EVEREST and not row.attributed_to
    )
    assert uncredited == [
        "Acoustical tile, ave, 1/2” thick",
        "Acoustical tile, ave, 3/4” thick",
    ]


def test_the_same_variant_under_three_drapes_is_three_rows() -> None:
    """ "draped to 1/2 area" is printed three times on one page, for three drapes."""
    halves = [
        row
        for row in PUBLISHED_ABSORPTION.values()
        if row.table == EVEREST and row.variant == "draped to 1/2 area"
    ]
    assert len(halves) == 3
    assert sorted(row.name for row in halves) == [
        "Drapes: cotton 14 oz/sq yd",
        "Drapes: heavy velour, 18 oz/sq yd",
        "Drapes: medium velour, 14 oz/sq yd",
    ]
    assert {row.spectrum()[125] for row in halves} == {0.07, 0.14}
