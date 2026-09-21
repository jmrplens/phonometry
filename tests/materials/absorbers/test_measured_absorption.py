#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The published absorption coefficients, against a second reading of the page.

The catalogue and the oracle in :mod:`tests.reference_data.absorption` were
transcribed from the rendered pages by two readers who never saw each other's
work, and compared cell by cell before either was kept. These tests keep that
comparison alive: an edit to the data file that the oracle does not share, or
the other way round, fails here.

The rest is the shape: that a band the page did not print stays empty and
says so, that the two rows the page prints as an area per person are areas
and not coefficients, and that a name lookup returns every row that matches
rather than choosing one.
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
    """The name the way the oracle writes it: heading and sub-row joined."""
    return f"{row.name} / {row.variant}" if row.variant else row.name


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
    over. A value of 2 or of 12 is a digit slipped, which is what this catches.
    """
    for key, row in PUBLISHED_ABSORPTION.items():
        for band, value in row.spectrum().items():
            assert 0.0 <= value <= 1.3, f"{key} at {band} Hz: {value}"


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
    """Four carpets, and the caller reads the names to pick one."""
    carpets = absorption_named("carpet")
    assert len(carpets) == 4
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
