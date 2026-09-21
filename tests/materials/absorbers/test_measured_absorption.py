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
    if "per 1000 cubic feet" in name:
        factor /= THOUSAND_CUBIC_FEET_M3
    for band, printed in zip(ref.LONG_7_1_BANDS_HZ, values, strict=True):
        held = getattr(row, f"absorption_area_{band}_m2")
        if printed is None:
            assert held is None
            continue
        assert held == pytest.approx(printed * factor, rel=1e-12)
        assert row.is_derived(f"absorption_area_{band}_m2")
        assert str(printed) in row.derived[f"absorption_area_{band}_m2"]


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


def test_the_musician_is_an_area_per_person_in_square_metres_marked_derived() -> None:
    """The page prints sabins; the field says m2 and holds m2, and says so."""
    row = PUBLISHED_ABSORPTION_AREAS[f"{LONG}/musician_per_person_with_instrument"]
    assert row.per == "person"
    assert row.bands() == (125, 250, 500, 1000, 2000, 4000)
    assert row.spectrum()[125] == pytest.approx(4.0 * SQUARE_FOOT_M2)
    assert row.is_derived("absorption_area_125_m2")
    assert "4.0 sabins" in row.derived["absorption_area_125_m2"]
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
    assert "0.9 sabins per 1000 cubic feet" in row.derived["absorption_area_1000_m2"]
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
    """Four carpets in Bies and four in Long, and the caller reads the names."""
    carpets = absorption_named("carpet")
    assert [row.table for row in carpets].count(BIES) == 4
    assert [row.table for row in carpets].count(LONG) == 4
    assert len(carpets) == 8
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
