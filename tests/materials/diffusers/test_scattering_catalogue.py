#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The published scattering coefficients, against a second reading of the pages.

The catalogue and the oracle in :mod:`tests.reference_data.scattering` were
transcribed from the rendered pages by two readers who never saw each other's
work, and compared cell by cell before either was kept. These tests keep that
comparison alive, and add the shape: that a band the page leaves blank and a
band where it prints a dash are told apart, that the reference marker beside a
row becomes the paper it points at, and that a description the page prints
twice is two rows rather than one.
"""

from __future__ import annotations

import pytest
import reference_data as ref

from phonometry.materials.diffusers import (
    PUBLISHED_SCATTERING,
    SCATTERING_BANDS_HZ,
    ScatteringCoefficientSpectrum,
    scattering_named,
)

#: Cox Appendix D keyed the way the catalogue keys it.
COX = "cox-2017-appendix-d"

#: The reference markers the page prints on a row or on its group heading, and
#: which are stripped from the name once the paper they point at is spelled out.
MARKERS = (" [1]", " [2]", " [3]", " [4]", " [5]", " [6]", " [7]")


def _plain(text: str) -> str:
    """A label without the bracketed reference marker the page prints on it."""
    for marker in MARKERS:
        text = text.replace(marker, "")
    return text.strip()


def _rows() -> list[ScatteringCoefficientSpectrum]:
    """Every row of the appendix, in catalogue order."""
    return [row for key, row in PUBLISHED_SCATTERING.items() if key.startswith(COX)]


# ---------------------------------------------------------------------------
# The transcription against the second reading
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_every_row_of_the_appendix() -> None:
    """Forty-six surfaces over four printed pages."""
    assert len(_rows()) == len(ref.COX_D_SCATTERING) == 46


def test_the_bands_are_the_ones_the_appendix_prints() -> None:
    assert SCATTERING_BANDS_HZ == ref.COX_D_BANDS_HZ


@pytest.mark.parametrize(
    ("group", "name", "note", "values"),
    ref.COX_D_SCATTERING,
    ids=[f"{group[:22]}-{name[:26]}" for group, name, _, _ in ref.COX_D_SCATTERING],
)
def test_each_row_holds_what_the_second_reader_read(
    group: str,
    name: str,
    note: str,
    values: tuple[float | str | None, ...],
) -> None:
    """Cell by cell, under the heading the row sits below.

    Neither the description nor the heading identifies a row on its own: the
    page prints ``"h = w = 10 cm, L = 2h"`` under two different headings and
    twice under one of them. The pair does not always either, which is what
    the last assertion of this test is about.
    """
    matches = [
        row
        for row in _rows()
        if row.name == _plain(name) and row.group == _plain(group)
    ]
    held = [
        [
            "-"
            if row.unquantified.get(f"scattering_coefficient_{band}")
            else getattr(row, f"scattering_coefficient_{band}")
            for band in ref.COX_D_BANDS_HZ
        ]
        for row in matches
    ]
    assert list(values) in held, f"{name!r} under {group!r}: {values} not in {held}"
    assert matches[held.index(list(values))].variant == note


def _marker(group: str, name: str) -> str:
    """The reference number the page prints on a row, or on its heading."""
    for text in (name, group):
        for marker in MARKERS:
            if text.endswith(marker):
                return marker.strip(" []")
    msg = f"no reference marker on {name!r} or {group!r}"
    raise AssertionError(msg)


def test_every_row_is_credited_to_a_paper() -> None:
    """The bracketed marker is resolved, on the row or on its heading.

    Two headings carry no marker at all and their rows carry their own; two
    carry one and their rows do not. Either way the row ends up with the
    paper, because a superscript number is not a citation once the row leaves
    the page.
    """
    for row in _rows():
        credit = row.attributed_to["row"]
        assert credit.endswith(")"), credit
        assert "“" in credit
    papers = {row.attributed_to["row"] for row in _rows()}
    assert len(papers) == 7


def test_each_row_is_credited_to_the_paper_its_marker_points_at() -> None:
    """A credit that moved one row down would otherwise go unnoticed.

    The catalogue strips the ``[4]`` from the name, so nothing published
    carries the number any more and a swap between two rows leaves every
    other test green. The second reading kept the markers, which is what
    makes the check possible: a row's paper has to start with the author
    the appendix lists under that number, and two rows with different
    numbers cannot share a paper.
    """
    seen: dict[str, str] = {}
    for (group, name, _, _), row in zip(ref.COX_D_SCATTERING, _rows(), strict=True):
        marker = _marker(group, name)
        credit = row.attributed_to["row"]
        author = ref.COX_D_FIRST_AUTHORS[marker]
        first = credit.split(",")[0].split(" and ")[0]
        assert first.endswith(author), (
            f"{name!r} carries [{marker}] and is credited to {credit[:40]!r}"
        )
        assert seen.setdefault(marker, credit) == credit
    assert sorted(seen) == ["1", "2", "3", "4", "5", "6", "7"]


# ---------------------------------------------------------------------------
# The shape of a row
# ---------------------------------------------------------------------------
def test_a_row_reads_back_as_a_spectrum_over_the_bands_it_prints() -> None:
    row = PUBLISHED_SCATTERING[f"{COX}/sinusoidal_1d_corrugation_h_5_1_cm_l_17_7_cm"]
    assert row.bands() == SCATTERING_BANDS_HZ
    assert row.spectrum()[5000] == 0.89
    assert row.scattering_coefficient(5000) == 0.89


def test_a_dash_and_a_blank_are_different_refusals() -> None:
    """Ten rows print a dash at 5 kHz and twenty leave the column empty.

    Both answer ``None`` and neither answers zero, which for a scattering
    coefficient would say the surface reflects every ray back along the
    specular direction. What they say when asked why differs, because the
    page did two different things.
    """
    dashed = PUBLISHED_SCATTERING[f"{COX}/periodic_1d_battens_h_w_10_cm_l_2h_sakuma"]
    blank = PUBLISHED_SCATTERING[f"{COX}/wooden_hemispheres_covering_h_7_5_mm_p_14"]
    assert dashed.scattering_coefficient_5000 is None
    assert blank.scattering_coefficient_5000 is None
    assert "–" in dashed.why_missing("scattering_coefficient_5000")
    assert "does not give it" in blank.why_missing("scattering_coefficient_5000")
    with pytest.raises(ValueError, match="5000 Hz band"):
        dashed.scattering_coefficient(5000)


def test_the_two_kinds_of_empty_cell_are_counted_as_the_page_has_them() -> None:
    dashed = [
        row for row in _rows() if "scattering_coefficient_5000" in row.unquantified
    ]
    blank = [
        row
        for row in _rows()
        if row.scattering_coefficient_5000 is None
        and "scattering_coefficient_5000" not in row.unquantified
    ]
    assert len(dashed) == 10
    assert len(blank) == 20
    assert all(row.group == "Wooden hemispheres covering" for row in blank)


def test_a_frequency_no_table_prints_is_refused_as_such() -> None:
    row = PUBLISHED_SCATTERING[f"{COX}/sinusoidal_1d_corrugation_h_5_1_cm_l_17_7_cm"]
    with pytest.raises(ValueError, match="not a one-third octave band"):
        row.scattering_coefficient(700)


def test_the_one_coefficient_above_unity_is_kept(
    recwarn: pytest.WarningsRecorder,
) -> None:
    """ISO 17497-1 puts no ceiling on the result, so neither does the catalogue.

    The V-shaped grooves with seven grooves over 44% of the base plate are
    printed as 1.17 at 1250 Hz, between 0.85 at 1 kHz and 0.73 at 1.6 kHz. A
    catalogue that clipped it to 1 would be correcting the measurement rather
    than holding it, and the reader could no longer tell the spike from a row
    that genuinely reached the ceiling.
    """
    above = [
        (row.name, band, value)
        for row in _rows()
        for band, value in row.spectrum().items()
        if value > 1.0
    ]
    assert above == [("N = 7, P = 44%", 1250, 1.17)]
    assert not recwarn.list


def test_every_value_is_a_scattering_coefficient() -> None:
    """Never negative, and never far above one."""
    for row in _rows():
        for band, value in row.spectrum().items():
            assert 0.0 <= value <= 1.2, f"{row.name} at {band} Hz: {value}"


# ---------------------------------------------------------------------------
# What the appendix is for
# ---------------------------------------------------------------------------
def test_the_same_battens_measured_twice_are_two_rows() -> None:
    """How wide the method is, in the table's own numbers.

    Battens 10 cm high and 10 cm wide on a 20 cm period, measured by two
    teams under ISO 17497-1 and printed one under the other with the same
    description. They agree at 100 Hz and are a factor of two apart at
    800 Hz, which is the spread a caller is choosing a row out of.
    """
    sakuma = PUBLISHED_SCATTERING[f"{COX}/periodic_1d_battens_h_w_10_cm_l_2h_sakuma"]
    choi = PUBLISHED_SCATTERING[f"{COX}/periodic_1d_battens_h_w_10_cm_l_2h_choi"]
    assert sakuma.name == choi.name == "h = w = 10 cm, L = 2h"
    assert sakuma.group == choi.group
    assert sakuma.attributed_to["row"] != choi.attributed_to["row"]
    assert (sakuma.spectrum()[630], choi.spectrum()[630]) == (0.28, 0.44)
    assert (sakuma.spectrum()[800], choi.spectrum()[800]) == (0.25, 0.47)


def test_two_pyramid_rows_are_told_apart_only_by_the_page_they_sit_on() -> None:
    """The same description, the same continuation line, different numbers.

    The appendix prints ``"h = 30.5 cm, L = b = 2h"`` with ``"One in four
    pyramid corners raised from baseplate"`` under it on two of its pages,
    and the two spectra are not the same. Nothing printed beside either row
    distinguishes it, so the folio goes into the key and the fact goes into
    the ``about`` of the data file.
    """
    raised = [
        row
        for row in _rows()
        if row.group == "Pyramids" and row.variant.startswith("One in four")
    ]
    assert len(raised) == 2
    first, second = raised
    assert first.name == second.name == "h = 30.5 cm, L = b = 2h"
    assert first.spectrum()[1000] != second.spectrum()[1000]


def test_the_lookup_matches_the_heading_as_well_as_the_row() -> None:
    """A row of its own reads ``h = w = 10 cm, L = 2h`` and is not searchable.

    The words a reader has are in the group heading, so the lookup matches
    both. ``"hemisphere"`` finds the twenty rows of one heading and nothing
    else, and no row carries the word in its description.
    """
    hemispheres = scattering_named("hemisphere")
    assert len(hemispheres) == 20
    assert not any("hemisphere" in row.name.casefold() for row in hemispheres)
    assert len(scattering_named("groove")) == 7
    assert scattering_named("PYRAMID") == scattering_named("pyramid")
    assert scattering_named("unobtainium") == ()


def test_the_catalogue_cannot_be_written_to() -> None:
    with pytest.raises(TypeError):
        PUBLISHED_SCATTERING["x/y"] = ScatteringCoefficientSpectrum(  # type: ignore[index]
            name="x", source="nowhere"
        )
