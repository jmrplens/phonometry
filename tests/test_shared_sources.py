#  Copyright (c) 2026. Jose Manuel Requena Plens
"""Tests for the shared-source check (``scripts/check_shared_sources.py``).

The gate's whole value is that it goes red on a misread page, so most of what
is here seeds a disagreement and watches it do that. The rest pins the two
decisions that make it useful rather than noisy: that a pair needs a shared
credit and not just a shared name, and that agreement is an overlap rather
than an equality.
"""

from __future__ import annotations

import dataclasses
import pathlib
import sys

import pytest

from phonometry.io import CatalogueRow

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_shared_sources as css

#: The study two of the books in this catalogue both take rows from.
_EMBLETON = "Embleton, Piercy and Daigle, 1983"


@dataclasses.dataclass(frozen=True, kw_only=True)
class _Surface(CatalogueRow):
    """A row with one quantity on it, standing in for a published class."""

    flow_resistivity_pa_s_m2: float | None = None
    porosity: float | None = None


def _row(
    table: str, name: str, credit: str | None = _EMBLETON, **fields: object
) -> _Surface:
    """One row of one book, crediting one study unless told otherwise."""
    return _Surface(
        name=name,
        table=table,
        source=f"{table} Table 1, PDF page 1 (printed p. 1)",
        attributed_to={"table": credit} if credit else {},
        **fields,  # type: ignore[arg-type]
    )


def _compare(
    *rows: _Surface, accepted: dict[str, str] | None = None
) -> tuple[list[str], list[str], int]:
    return css.compare("ground", rows, ("flow_resistivity_pa_s_m2",), accepted or {})


# ---------------------------------------------------------------------------
# What makes a pair
# ---------------------------------------------------------------------------
def test_two_books_crediting_one_study_are_a_pair() -> None:
    lines, failures, compared = _compare(
        _row("bies-2017-table-5-1", "Sugar snow", flow_resistivity_pa_s_m2=25_000.0),
        _row("cox-2017-table-6-7", "Sugar snow", flow_resistivity_pa_s_m2=25_000.0),
    )

    assert compared == 1
    assert not failures
    assert any("sugar snow" in line for line in lines)


def test_one_name_in_two_books_with_no_shared_credit_is_not_a_pair() -> None:
    """Two measurements of one material are free to disagree."""
    lines, failures, compared = _compare(
        _row(
            "bies-2017-table-5-1",
            "Grass",
            credit="Attenborough, 1982",
            flow_resistivity_pa_s_m2=100_000.0,
        ),
        _row(
            "cox-2017-table-6-7",
            "Grass",
            credit="Horoshenkov, 2006",
            flow_resistivity_pa_s_m2=900_000.0,
        ),
    )

    assert compared == 0
    assert not failures
    assert not lines


def test_two_rows_of_one_book_are_not_a_pair() -> None:
    """A book that prints a surface twice is fitting it twice, not copying."""
    _, failures, compared = _compare(
        _row("cox-2017-table-6-7", "Lawn", flow_resistivity_pa_s_m2=39_000.0),
        _row("cox-2017-table-6-7", "Lawn", flow_resistivity_pa_s_m2=750_000.0),
    )

    assert compared == 0
    assert not failures


# ---------------------------------------------------------------------------
# What counts as agreement
# ---------------------------------------------------------------------------
def test_a_value_inside_the_other_book_s_interval_agrees() -> None:
    """Bies gives a bare sandy plain 250 to 500 kPa s/m2 and Cox gives 370."""
    _, failures, compared = _compare(
        _row(
            "bies-2017-table-5-1",
            "Bare sandy plain",
            ranges={"flow_resistivity_pa_s_m2": (250_000.0, 500_000.0)},
        ),
        _row(
            "cox-2017-table-6-7",
            "Bare sandy plain",
            flow_resistivity_pa_s_m2=370_000.0,
        ),
    )

    assert compared == 1
    assert not failures


def test_two_intervals_that_touch_at_one_end_agree() -> None:
    _, failures, _ = _compare(
        _row(
            "bies-2017-table-5-1",
            "Snow",
            ranges={"flow_resistivity_pa_s_m2": (10_000.0, 30_000.0)},
        ),
        _row(
            "cox-2017-table-6-7",
            "Snow",
            ranges={"flow_resistivity_pa_s_m2": (30_000.0, 90_000.0)},
        ),
    )

    assert not failures


def test_a_reading_inside_one_of_several_listed_ones_agrees() -> None:
    """A listed cell is several readings, and matching one of them is enough."""
    _, failures, compared = _compare(
        _row(
            "bies-2017-table-5-1",
            "Gravel",
            ranges={"flow_resistivity_pa_s_m2": (200_000.0, 210_000.0)},
        ),
        _row(
            "cox-2017-table-6-7",
            "Gravel",
            reported={"flow_resistivity_pa_s_m2": (25_000.0, 207_000.0, 230_000.0)},
        ),
    )

    assert compared == 1
    assert not failures


def test_a_reading_in_the_gap_between_listed_ones_does_not_agree() -> None:
    """The failure an envelope would hide.

    A cell listing 25, 207 and 230 excludes 100 as firmly as it excludes 400:
    taking the envelope 25 to 230 would call that agreement.
    """
    _, failures, _ = _compare(
        _row(
            "bies-2017-table-5-1",
            "Gravel",
            flow_resistivity_pa_s_m2=100_000.0,
        ),
        _row(
            "cox-2017-table-6-7",
            "Gravel",
            reported={"flow_resistivity_pa_s_m2": (25_000.0, 207_000.0, 230_000.0)},
        ),
    )

    assert len(failures) == 1
    assert "do not overlap" in failures[0]


# ---------------------------------------------------------------------------
# The red light
# ---------------------------------------------------------------------------
def test_two_readings_of_one_study_that_exclude_each_other_fail() -> None:
    """The defect the gate exists for: a digit read off the wrong line."""
    _, failures, _ = _compare(
        _row(
            "bies-2017-table-5-1",
            "Sugar snow",
            ranges={"flow_resistivity_pa_s_m2": (25_000.0, 50_000.0)},
        ),
        _row(
            "cox-2017-table-6-7",
            "Sugar snow",
            ranges={"flow_resistivity_pa_s_m2": (250_000.0, 500_000.0)},
        ),
    )

    assert len(failures) == 1
    assert "do not overlap" in failures[0]
    assert _EMBLETON in failures[0]
    assert "bies-2017-table-5-1" in failures[0]


def test_a_disagreement_somebody_has_read_the_pages_for_is_accepted() -> None:
    _, failures, _ = _compare(
        _row(
            "bies-2017-table-5-1",
            "Sugar snow",
            ranges={"flow_resistivity_pa_s_m2": (25_000.0, 50_000.0)},
        ),
        _row(
            "cox-2017-table-6-7",
            "Sugar snow",
            ranges={"flow_resistivity_pa_s_m2": (250_000.0, 500_000.0)},
        ),
        accepted={
            "ground/sugar snow/flow_resistivity_pa_s_m2/"
            "bies-2017-table-5-1|cox-2017-table-6-7": "read the pages"
        },
    )

    assert not failures


def test_a_quantity_only_one_book_prints_is_not_compared() -> None:
    _, failures, compared = _compare(
        _row("bies-2017-table-5-1", "Snow", flow_resistivity_pa_s_m2=25_000.0),
        _row("cox-2017-table-6-7", "Snow"),
    )

    assert compared == 0
    assert not failures


# ---------------------------------------------------------------------------
# The catalogues as they stand
# ---------------------------------------------------------------------------
def test_every_published_pair_overlaps_today() -> None:
    """The same run CI makes, so a stale catalogue fails here first."""
    for label, catalogue, fields in css.CATALOGUES:
        _, failures, _ = css.compare(label, catalogue.values(), fields)
        assert failures == []


def test_the_published_catalogues_hold_pairs_at_all() -> None:
    """A gate that compares nothing passes for the wrong reason."""
    compared = sum(
        css.compare(label, catalogue.values(), fields)[2]
        for label, catalogue, fields in css.CATALOGUES
    )

    assert compared >= 8


def test_the_registry_holds_nothing_stale() -> None:
    """An accepted disagreement that no longer exists has to go."""
    assert css.ACCEPTED == {}


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        ((1.0, 2.0), (2.0, 3.0), True),
        ((1.0, 2.0), (2.5, 3.0), False),
        ((1.0, 5.0), (2.0, 3.0), True),
        ((2.0, 2.0), (1.0, 3.0), True),
    ],
)
def test_overlap_is_inclusive_at_the_ends(
    first: tuple[float, float], second: tuple[float, float], *, expected: bool
) -> None:
    one = css.Reading("a", "a-1", (first,))
    other = css.Reading("b", "b-1", (second,))

    assert css.overlap(one, other) is expected


# ---------------------------------------------------------------------------
# What the credit covers
# ---------------------------------------------------------------------------
def test_a_credit_for_one_quantity_does_not_cover_another() -> None:
    """A study cited for a porosity says nothing about the resistivity.

    The rows pair, because they do share that porosity credit, but the
    resistivity beside it is credited to two different studies and is not
    compared: they are two measurements, free to disagree.
    """
    first = _Surface(
        name="Grass",
        table="bies-2017-table-5-1",
        source="Bies 5e Table 5.1, PDF page 1 (printed p. 1)",
        attributed_to={"porosity": _EMBLETON, "flow_resistivity_pa_s_m2": "Bies, 2017"},
        porosity=0.4,
        flow_resistivity_pa_s_m2=100_000.0,
    )
    second = _Surface(
        name="Grass",
        table="cox-2017-table-6-7",
        source="Cox & D'Antonio 3e Table 6.7, PDF page 1 (printed p. 1)",
        attributed_to={
            "porosity": _EMBLETON,
            "flow_resistivity_pa_s_m2": "Attenborough, 1982",
        },
        porosity=0.4,
        flow_resistivity_pa_s_m2=900_000.0,
    )

    _, failures, compared = css.compare(
        "ground", (first, second), ("porosity", "flow_resistivity_pa_s_m2"), {}
    )

    assert compared == 1
    assert not failures


def test_a_row_credit_covers_every_quantity_of_the_row() -> None:
    """Which is what a superscript on the material name means."""
    first = _Surface(
        name="Grass",
        table="bies-2017-table-5-1",
        source="Bies 5e Table 5.1, PDF page 1 (printed p. 1)",
        attributed_to={"row": _EMBLETON},
        flow_resistivity_pa_s_m2=100_000.0,
    )
    second = _Surface(
        name="Grass",
        table="cox-2017-table-6-7",
        source="Cox & D'Antonio 3e Table 6.7, PDF page 1 (printed p. 1)",
        attributed_to={"table": _EMBLETON},
        flow_resistivity_pa_s_m2=900_000.0,
    )

    _, failures, compared = css.compare(
        "ground", (first, second), ("flow_resistivity_pa_s_m2",), {}
    )

    assert compared == 1
    assert len(failures) == 1


def test_a_printed_uncertainty_widens_the_reading() -> None:
    """Cox prints (540 +/- 92) x 10^3, so 500 is inside what the page allows.

    A value with a plus-or-minus beside it is an interval the page stated, and
    comparing the centres alone would call two overlapping uncertainties a
    conflict.
    """
    _, failures, compared = _compare(
        _row(
            "bies-2017-table-5-1",
            "Bare sandy plain",
            flow_resistivity_pa_s_m2=500_000.0,
        ),
        _row(
            "cox-2017-table-6-7",
            "Bare sandy plain",
            flow_resistivity_pa_s_m2=540_000.0,
            uncertainty={"flow_resistivity_pa_s_m2": 92_000.0},
        ),
    )

    assert compared == 1
    assert not failures


def test_an_exception_written_for_one_pair_does_not_cover_another() -> None:
    """A material can be in three books and disagree with two of them.

    The registry key names both rows, so an exception somebody read the pages
    for covers those two rows and nothing else.
    """
    bies = _row(
        "bies-2017-table-5-1",
        "Sugar snow",
        ranges={"flow_resistivity_pa_s_m2": (25_000.0, 50_000.0)},
    )
    cox = _row(
        "cox-2017-table-6-7",
        "Sugar snow",
        ranges={"flow_resistivity_pa_s_m2": (250_000.0, 500_000.0)},
    )
    mechel = _row(
        "mechel-2008-section-g1-table-1",
        "Sugar snow",
        ranges={"flow_resistivity_pa_s_m2": (700_000.0, 900_000.0)},
    )
    excuse = {
        css.accepted_key(
            "ground", "sugar snow", "flow_resistivity_pa_s_m2", bies, cox
        ): "read the pages"
    }

    _, failures, _ = _compare(bies, cox, mechel, accepted=excuse)

    assert len(failures) == 2
    assert all("mechel" in failure for failure in failures)
