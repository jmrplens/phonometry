#  Copyright (c) 2026. Jose Manuel Requena Plens
"""A banded row read at an array of frequencies, one band per frequency.

``BandedRow.values_at`` is the adapter for the functions that take one value
per band by position: an array cannot say which band is missing, and a row
can. It answers exactly what the per-band accessor answers, for every
published banded row; it takes a nominal centre, an exact base-ten one and an
exact base-two one as the same band, within a sixth of the spacing between
bands and never as far as the next; and it refuses a band the row does not
print with what the page had there, rather than reading it as zero.
"""

from __future__ import annotations

import catalogue_fingerprint
import numpy as np
import pytest

from phonometry import io, materials, noise_control, room

_BIES = "bies-2017-table-6-2/unoccupied_heavily_upholstered_seats"
_SOURCE = "Example Acoustics Ltd, Panel 40 technical data sheet, Rev. 4, p. 2"


def _banded_rows() -> list[io.BandedRow]:
    """Every row of every published catalogue that prints one value per band."""
    return [
        row
        for mapping in catalogue_fingerprint.published_mappings().values()
        for row in mapping.values()
        if isinstance(row, io.BandedRow)
    ]


BANDED_ROWS = _banded_rows()


def test_every_published_banded_row_reads_the_same_as_band_by_band() -> None:
    """The array and the per-band accessor give one answer, row by row."""
    assert len(BANDED_ROWS) > 1000
    for row in BANDED_ROWS:
        bands = row.bands()
        values = row.values_at(bands)
        assert values.tolist() == [row._in_band(band) for band in bands], row.name
        assert values.tolist() == list(row.spectrum().values()), row.name


def test_the_published_accessor_and_the_array_agree() -> None:
    seats = materials.PUBLISHED_ABSORPTION[_BIES]
    bands = np.array([125, 500, 4000])
    assert seats.values_at(bands).tolist() == [
        seats.absorption_coefficient(125),
        seats.absorption_coefficient(500),
        seats.absorption_coefficient(4000),
    ]


def test_exact_centres_read_as_their_nominal_bands() -> None:
    """Base ten and base two, octave and one-third octave alike."""
    for row in BANDED_ROWS:
        bands = np.array(row.bands(), dtype=float)
        if not bands.size:
            continue
        per_octave = row._bands_per_octave
        steps = np.round(per_octave * np.log2(bands / 1000.0))
        base_ten = 1000.0 * 10.0 ** (3.0 * steps / (10.0 * per_octave))
        base_two = 1000.0 * 2.0 ** (steps / per_octave)
        nominal = row.values_at(bands)
        assert row.values_at(base_ten).tolist() == nominal.tolist(), row.name
        assert row.values_at(base_two).tolist() == nominal.tolist(), row.name


@pytest.mark.parametrize(
    ("row_key", "centre", "per_octave"),
    [
        ("absorption", 500.0, 1),
        ("scattering", 500.0, 3),
    ],
)
def test_a_frequency_matches_within_a_sixth_of_the_band_spacing(
    row_key: str, centre: float, per_octave: int
) -> None:
    row = _full_row(row_key)
    reach = 1.0 / (6.0 * per_octave)
    inside = centre * 2.0 ** (0.99 * reach)
    below = centre * 2.0 ** (-0.99 * reach)
    assert row.values_at([inside, below]).tolist() == [row._in_band(500)] * 2
    outside = centre * 2.0 ** (1.01 * reach)
    with pytest.raises(ValueError, match="the nearest is 500 Hz"):
        row.values_at([outside])


def _full_row(kind: str) -> io.BandedRow:
    """A published row that prints the 500 Hz band."""
    mapping = (
        materials.PUBLISHED_ABSORPTION
        if kind == "absorption"
        else materials.PUBLISHED_SCATTERING
    )
    return next(row for row in mapping.values() if 500 in row.bands())


def test_a_frequency_between_bands_is_refused_naming_the_nearest() -> None:
    seats = materials.PUBLISHED_ABSORPTION[_BIES]
    with pytest.raises(
        ValueError,
        match=r"600 Hz is not an octave band that absorption tables print: the "
        r"nearest is 500 Hz",
    ):
        seats.values_at([500.0, 600.0])


def test_a_band_the_row_does_not_print_is_refused_with_what_the_page_had() -> None:
    """Never a zero and never a neighbour: the refusal ``printed`` gives."""
    seats = materials.PUBLISHED_ABSORPTION[_BIES]
    assert 63 not in seats.bands()
    with pytest.raises(ValueError, match="has no absorption_coefficient_63"):
        seats.values_at([63.0, 125.0])


def test_the_refusal_is_the_one_the_per_band_accessor_gives() -> None:
    seats = materials.PUBLISHED_ABSORPTION[_BIES]
    with pytest.raises(ValueError, match="has no absorption_coefficient_63") as band:
        seats.absorption_coefficient(63)
    with pytest.raises(ValueError, match="has no absorption_coefficient_63") as array:
        seats.values_at([62.5])
    assert str(array.value) == str(band.value)


@pytest.mark.parametrize("bad", [0.0, -500.0, float("nan"), float("inf")])
def test_a_frequency_that_is_not_finite_and_positive_is_refused(bad: float) -> None:
    seats = materials.PUBLISHED_ABSORPTION[_BIES]
    with pytest.raises(ValueError, match="a finite frequency above zero"):
        seats.values_at([500.0, bad])


def test_the_shape_of_the_frequencies_is_the_shape_of_the_answer() -> None:
    seats = materials.PUBLISHED_ABSORPTION[_BIES]
    grid = np.array([[125.0, 250.0], [500.0, 1000.0]])
    values = seats.values_at(grid)
    assert values.shape == (2, 2)
    assert values.dtype == np.float64
    assert values[1, 0] == seats.absorption_coefficient(500)
    assert seats.values_at(500.0).shape == ()
    assert seats.values_at([]).shape == (0,)


def test_the_answer_is_a_new_array_the_caller_owns() -> None:
    seats = materials.PUBLISHED_ABSORPTION[_BIES]
    first = seats.values_at([500.0])
    first[0] = 9.0
    assert seats.values_at([500.0])[0] == seats.absorption_coefficient(500)


def test_the_per_band_refusal_reads_as_english() -> None:
    """The refusal of a band no table prints says "an octave band that"."""
    seats = materials.PUBLISHED_ABSORPTION[_BIES]
    with pytest.raises(
        ValueError, match="is not an octave band that absorption tables print"
    ):
        seats.absorption_coefficient(600)


# ---------------------------------------------------------------------------
# The consumers that take one value per band by position
# ---------------------------------------------------------------------------
def test_a_row_feeds_a_reverberation_formula_band_by_band() -> None:
    seats = materials.PUBLISHED_ABSORPTION[_BIES]
    bands = np.array([125.0, 250.0, 500.0, 1000.0, 2000.0, 4000.0])
    by_hand = np.array([seats.absorption_coefficient(int(band)) for band in bands])
    through_row = room.sabine_reverberation_time(
        500.0, [(120.0, seats.values_at(bands)), (300.0, 0.05)]
    )
    assert np.array_equal(
        through_row,
        room.sabine_reverberation_time(500.0, [(120.0, by_hand), (300.0, 0.05)]),
    )


def test_a_row_feeds_an_enclosure_as_its_transmission_loss_function() -> None:
    wall = next(
        row
        for row in noise_control.PUBLISHED_DUCT_TRANSMISSION_LOSS.values()
        if {125, 250, 500, 1000} <= set(row.bands())
    )
    bands = np.array([125.0, 250.0, 500.0, 1000.0])
    through_row = noise_control.enclosure_insertion_loss(
        wall.values_at,
        external_area=10.0,
        internal_area=12.0,
        internal_absorption=0.3,
        frequencies=bands,
    )
    by_array = noise_control.enclosure_insertion_loss(
        wall.values_at(bands),
        external_area=10.0,
        internal_area=12.0,
        internal_absorption=0.3,
        frequencies=bands,
    )
    assert np.array_equal(
        np.asarray(through_row.insertion_loss), np.asarray(by_array.insertion_loss)
    )


def test_a_row_of_the_caller_is_read_the_same_way() -> None:
    panel = materials.AbsorptionSpectrum(
        name="Panel 40",
        source=_SOURCE,
        absorption_coefficient_250=0.35,
        absorption_coefficient_500=0.8,
        unquantified={"absorption_coefficient_125": "n.m."},
    )
    assert panel.values_at([251.19, 501.19]).tolist() == [0.35, 0.8]
    with pytest.raises(ValueError, match="n.m."):
        panel.values_at([125.0])
