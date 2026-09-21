#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The published diffusion coefficients, against a second reading of the pages.

The catalogue and the oracle in :mod:`tests.reference_data.diffusion` were
transcribed from the rendered pages by two readers who never saw each other's
work, and compared cell by cell before either was kept. These tests keep that
comparison alive, and add the shape: that a surface is three rows and not one,
that the random incidence row carries no angle and says why, and that the
section heading a row is short for travels with it.
"""

from __future__ import annotations

import pytest
import reference_data as ref

from phonometry.materials.diffusers import (
    DIFFUSION_BANDS_HZ,
    PUBLISHED_DIFFUSION,
    NormalizedDiffusionSpectrum,
    diffusion_named,
)

#: Cox Appendix B keyed the way the catalogue keys it.
COX = "cox-2017-appendix-b"

#: How the page heads each of the three lines it prints per surface, and the
#: variant the catalogue files it under.
ANGLES = {"0": "normal", "57": "57 degrees", "Random": "random"}


def _rows() -> list[NormalizedDiffusionSpectrum]:
    """Every row of the appendix, in catalogue order."""
    return [row for key, row in PUBLISHED_DIFFUSION.items() if key.startswith(COX)]


# ---------------------------------------------------------------------------
# The transcription against the second reading
# ---------------------------------------------------------------------------
def test_the_catalogue_holds_every_line_of_the_appendix() -> None:
    """Twenty-nine surfaces, three angles each, over four printed pages."""
    assert len(ref.COX_B_DIFFUSION) == 29
    assert len(_rows()) == 29 * 3 == 87


def test_the_bands_are_the_ones_the_appendix_prints() -> None:
    assert DIFFUSION_BANDS_HZ == ref.COX_B_BANDS_HZ


@pytest.mark.parametrize(
    ("section", "surface", "angles"),
    ref.COX_B_DIFFUSION,
    ids=[
        f"{section[:2]}-{surface[:34]}" for section, surface, _ in ref.COX_B_DIFFUSION
    ],
)
def test_each_surface_holds_what_the_second_reader_read(
    section: str,
    surface: str,
    angles: dict[str, tuple[float, ...]],
) -> None:
    """Three lines, eighteen cells each, under the heading they belong to.

    The appendix fills every cell, so a missing value here is a transcription
    error and not a page that left one out.
    """
    for printed_angle, values in angles.items():
        matches = [
            row
            for row in _rows()
            if row.name == surface
            and row.group == section
            and row.variant == ANGLES[printed_angle]
        ]
        assert len(matches) == 1, f"{surface!r} at {printed_angle}: {len(matches)} rows"
        row = matches[0]
        held = tuple(
            getattr(row, f"diffusion_coefficient_{band}") for band in ref.COX_B_BANDS_HZ
        )
        assert held == tuple(values)
        assert len(row.bands()) == 18


def test_every_section_heading_is_kept_whole() -> None:
    """The geometry a row is short for is in the heading, so it travels.

    ``"1 period, 0.61 cm wide"`` is a semicylinder of radius 0.3 m only
    because the heading above it says so, and the flat section between
    periods is printed there and nowhere else.
    """
    headings = {row.group for row in _rows()}
    assert len(headings) == 7
    first = next(h for h in headings if h.startswith("1."))
    assert first.endswith("(1 cm flat section between each period)")
    assert "radius 0.3 m" in first


# ---------------------------------------------------------------------------
# The shape of a row
# ---------------------------------------------------------------------------
def test_a_surface_is_three_rows_and_the_angle_says_which() -> None:
    rows = diffusion_named("12 periods, 7.32 m wide")
    assert [row.variant for row in rows] == ["normal", "57 degrees", "random"]
    assert [row.angle_of_incidence_deg for row in rows] == [0.0, 57.0, None]


def test_the_random_row_refuses_an_angle_and_says_what_the_page_had() -> None:
    """A mean over ten angles is not one of them, and zero would be a lie.

    Zero degrees is the normal incidence row, which this table also prints,
    so answering zero here would hand back a different row's meaning.
    """
    random = next(row for row in _rows() if row.variant == "random")
    assert random.angle_of_incidence_deg is None
    why = random.why_missing("angle_of_incidence_deg")
    assert "Random" in why
    assert "ten angles" in why
    with pytest.raises(ValueError, match="angle_of_incidence_deg"):
        random.printed("angle_of_incidence_deg")


def test_a_row_reads_back_as_a_spectrum_over_every_band() -> None:
    row = PUBLISHED_DIFFUSION[f"{COX}/1_1_period_0_61_cm_wide_normal"]
    assert row.bands() == DIFFUSION_BANDS_HZ
    assert row.spectrum()[5000] == 0.98
    assert row.diffusion_coefficient(5000) == 0.98


def test_a_frequency_no_table_prints_is_refused_as_such() -> None:
    row = PUBLISHED_DIFFUSION[f"{COX}/1_1_period_0_61_cm_wide_normal"]
    with pytest.raises(ValueError, match="not a one-third octave band"):
        row.diffusion_coefficient(700)


def test_every_value_is_a_normalized_diffusion_coefficient() -> None:
    """Between zero and one, which is what the coefficient is defined over."""
    for row in _rows():
        for band, value in row.spectrum().items():
            assert 0.0 <= value <= 1.0, f"{row.name} at {band} Hz: {value}"


# ---------------------------------------------------------------------------
# What the appendix is for
# ---------------------------------------------------------------------------
def test_one_diffuser_and_an_array_of_it_are_not_the_same_surface() -> None:
    """The argument the first section of the table exists to make.

    Semicylinders of the same radius, one period and then twelve, at random
    incidence: 0.77 against 0.22 at 1 kHz. A designer who reads a single
    device's polar response and scales it up gets this wrong by a factor of
    three, and no formula in the book says so.
    """
    one = PUBLISHED_DIFFUSION[f"{COX}/1_1_period_0_61_cm_wide_random"]
    twelve = PUBLISHED_DIFFUSION[f"{COX}/1_12_periods_7_32_m_wide_random"]
    assert one.group == twelve.group
    assert (one.spectrum()[1000], twelve.spectrum()[1000]) == (0.77, 0.22)


def test_depth_moves_the_coefficient_where_the_section_says_it_does() -> None:
    """Six semiellipses, 1 cm deep to 30 cm, at random incidence.

    The shallowest is flat as far as 5 kHz is concerned and the deepest is
    diffusing over most of the range, which is the second section's point.
    """
    shallow = PUBLISHED_DIFFUSION[f"{COX}/2_1_cm_deep_random"]
    deep = PUBLISHED_DIFFUSION[f"{COX}/2_30_cm_deep_semicylinders_random"]
    assert (shallow.spectrum()[5000], deep.spectrum()[5000]) == (0.02, 0.65)
    assert shallow.group == deep.group


def test_the_one_surface_the_appendix_lists_twice_is_kept_twice() -> None:
    """Two descriptions, one prediction, and the page prints both.

    "6 periods, 3.66 m wide" of section 1 and "30 cm deep (semicylinders)" of
    section 2 carry the same fifty-four values because they are the same six
    semicylinders read into two series. They are the only identical pair in
    the appendix, and collapsing them would drop a row from a section that
    needs it to make its own argument.
    """
    same = [
        row
        for row in _rows()
        if row.name in {"6 periods, 3.66 m wide", "30 cm deep (semicylinders)"}
    ]
    assert len(same) == 6
    by_angle: dict[str, list[dict[int, float]]] = {}
    for row in same:
        by_angle.setdefault(row.variant, []).append(row.spectrum())
    for variant, spectra in by_angle.items():
        assert spectra[0] == spectra[1], variant
    assert len({row.group for row in same}) == 2


def test_the_lookup_matches_the_heading_as_well_as_the_row() -> None:
    assert len(diffusion_named("Schroeder")) == 15
    assert len(diffusion_named("triangle")) == 12
    assert diffusion_named("QRD") == diffusion_named("qrd")
    assert diffusion_named("unobtainium") == ()


def test_the_catalogue_cannot_be_written_to() -> None:
    with pytest.raises(TypeError):
        PUBLISHED_DIFFUSION["x/y"] = NormalizedDiffusionSpectrum(  # type: ignore[index]
            name="x", source="nowhere"
        )
