#  Copyright (c) 2026. Jose Manuel Requena Plens
"""The agreement gate between the books of the solids catalogue.

``scripts/check_solid_agreement.py`` puts the same material from several books
on one line and fails when two densities are too far apart to be anything but
a mistyped digit. Everything else it prints and never fails on, because moduli
really do disagree by thirty per cent across these tables.

Three decisions carry the whole design and each has a test that breaks it:

* the failing check is density and only density, because density is the one
  property a book cannot get very wrong without describing another material;
* it ignores rows a page marked as a specimen of its own, because expanded
  polystyrene foam and moulded polystyrene are not two books disagreeing;
* :data:`~check_solid_agreement.ACCEPTED` is a ratchet in both directions, so
  an entry whose books come to agree fails until somebody deletes it.

The last one is the reason the gate can be trusted a year from now: a silenced
disagreement that quietly stops being one would otherwise stay silenced.
"""

from __future__ import annotations

import dataclasses
import math
import pathlib
import sys

import pytest

from phonometry.solids import PUBLISHED_SOLIDS, SolidMaterial

_SCRIPTS = str(pathlib.Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import check_solid_agreement as csa

_SOURCE = "Somebody (2026), *A Book*, table 1."
_REASON = "the books really differ, and here is why"


def _row(table: str, **fields: object) -> SolidMaterial:
    """A catalogue row with only the fields a test cares about."""
    return SolidMaterial(name="Widgetium", source=_SOURCE, table=table, **fields)  # type: ignore[arg-type]


def _pair(first: float, second: float, **fields: object) -> list[SolidMaterial]:
    """The same material from two books, at two densities."""
    return [
        _row("first-book", density_kg_m3=first, **fields),
        _row("second-book", density_kg_m3=second, **fields),
    ]


def test_densities_that_agree_are_not_a_problem() -> None:
    """The ordinary case: two books, one material, a rounding apart."""
    assert csa.problems(_pair(7800.0, 7810.0), {}) == []


def test_a_density_that_disagrees_fails_the_gate() -> None:
    """The defect the gate exists for, with a digit typed wrong."""
    (found,) = csa.problems(_pair(7800.0, 1800.0), {})
    assert "widgetium" in found
    assert "333.3 per cent apart" in found
    assert "first 7800, second 1800" in found


def test_the_gate_fails_on_the_real_catalogue_with_one_digit_changed() -> None:
    """The gate proved against the catalogue it guards, not a fixture.

    A test that only ever sees invented rows cannot tell whether the gate is
    wired to the real thing. This one takes the published catalogue, moves one
    digit of one density, and requires the gate to name that material.
    """
    rows = list(PUBLISHED_SOLIDS.values())
    steel = next(
        index
        for index, row in enumerate(rows)
        if csa.normalised(row.name) == "steel" and not row.variant
    )
    assert csa.problems(rows) == []
    rows[steel] = dataclasses.replace(rows[steel], density_kg_m3=1800.0)
    (found,) = csa.problems(rows)
    assert found.startswith("steel: the densities are ")


def test_a_distinguished_row_never_fails_the_gate() -> None:
    """Bies prints lead annealed and rolled: two specimens, not two claims."""
    rows = [
        _row("first-book", density_kg_m3=7800.0),
        _row("second-book", density_kg_m3=1800.0, variant="expanded foam"),
    ]
    assert csa.problems(rows, {}) == []


def test_a_distinguished_row_is_still_reported() -> None:
    """What the failing check ignores the report still has to show."""
    rows = [
        _row("first-book", density_kg_m3=7800.0),
        _row("second-book", density_kg_m3=1800.0, variant="expanded foam"),
    ]
    printed = "\n".join(csa.report(rows, everything=True))
    assert "widgetium (2 rows, 2 books)" in printed
    assert "7800" in printed
    assert "1800" in printed


def test_one_book_alone_is_never_compared() -> None:
    """Two rows of one table are that table's business, not a disagreement."""
    rows = [
        _row("first-book", density_kg_m3=7800.0),
        _row("first-book", density_kg_m3=1800.0),
    ]
    assert csa.problems(rows, {}) == []
    assert csa.report(rows, everything=True) == []


def test_an_accepted_disagreement_is_silenced() -> None:
    """A disagreement somebody has read the pages for and written down."""
    assert csa.problems(_pair(7800.0, 1800.0), {"widgetium": _REASON}) == []


def test_an_accepted_disagreement_that_went_away_is_reported_as_stale() -> None:
    """The ratchet's other direction, which is what keeps the registry honest."""
    (found,) = csa.problems(_pair(7800.0, 7810.0), {"widgetium": _REASON})
    assert "its entry in ACCEPTED is stale" in found


def test_an_accepted_name_no_book_prints_is_reported_as_stale() -> None:
    """A material renamed out of the catalogue leaves its reason behind."""
    (found,) = csa.problems(_pair(7800.0, 7810.0), {"unobtainium": _REASON})
    assert found == (
        "unobtainium: is in ACCEPTED and no two books print a density for it"
    )


def test_an_accepted_name_two_books_print_but_never_compare_is_stale() -> None:
    """The hole the ratchet had, and the catalogue already occupies it.

    Two books print brick and fewer than two print a density for it, because
    Bies prints his as an interval. The material is therefore in the groups
    and never compared, so a registry keyed on the groups would hold a reason
    for a disagreement nothing can see. The ratchet is keyed on what was
    actually compared instead.
    """
    rows = [
        _row("first-book", density_kg_m3=7800.0),
        _row("second-book"),
        SolidMaterial(name="Steel", source=_SOURCE, table="a", density_kg_m3=7800.0),
        SolidMaterial(name="Steel", source=_SOURCE, table="b", density_kg_m3=7810.0),
    ]
    (found,) = csa.problems(rows, {"widgetium": _REASON})
    assert found == (
        "widgetium: is in ACCEPTED and no two books print a density for it"
    )


def test_a_quantity_at_zero_is_infinitely_apart_and_never_divides_by_it() -> None:
    """No compared quantity can reach zero, and if one does the gate says so."""
    assert csa.spread([("a", 0.0, False), ("b", 200.0, False)]) == math.inf


def test_the_registry_is_not_stale_against_the_published_catalogue() -> None:
    """Every entry in ACCEPTED still silences a disagreement that is there."""
    assert csa.problems(PUBLISHED_SOLIDS.values()) == []


def test_only_density_fails_however_far_apart_the_rest_are() -> None:
    """Moduli are literature spread. Tin is twelve times apart and passes."""
    rows = [
        _row("first-book", density_kg_m3=7280.0, youngs_modulus_pa=4.4e9),
        _row("second-book", density_kg_m3=7300.0, youngs_modulus_pa=54.0e9),
    ]
    assert csa.problems(rows, {}) == []


def test_a_notable_disagreement_is_printed_by_default() -> None:
    """Tin's shape: the densities agree and the moduli are an order apart."""
    rows = [
        _row("first-book", density_kg_m3=7280.0, youngs_modulus_pa=4.4e9),
        _row("second-book", density_kg_m3=7300.0, youngs_modulus_pa=54.0e9),
    ]
    printed = "\n".join(csa.report(rows, everything=False))
    assert "youngs_modulus_pa" in printed
    assert "first 4.4, second 54 GPa" in printed


def test_an_ordinary_disagreement_waits_for_the_full_report() -> None:
    """Nineteen per cent on a modulus is two books, not a thing to look at."""
    rows = [
        _row("first-book", density_kg_m3=2700.0, youngs_modulus_pa=62.0e9),
        _row("second-book", density_kg_m3=2700.0, youngs_modulus_pa=74.0e9),
    ]
    assert csa.report(rows, everything=False) == []
    assert "youngs_modulus_pa" in "\n".join(csa.report(rows, everything=True))


def test_a_variant_alone_never_makes_a_material_notable() -> None:
    """Expanded foam beside moulded polystyrene is not a disagreement.

    Measured over every row, this pair is six hundred per cent apart and would
    head the default run. The threshold is measured over the rows no page
    distinguished, so it is not there at all.
    """
    rows = [
        _row("first-book", density_kg_m3=1050.0, bar_longitudinal_speed_m_s=1750.0),
        _row(
            "second-book",
            density_kg_m3=1050.0,
            bar_longitudinal_speed_m_s=300.0,
            variant="expanded foam",
        ),
    ]
    assert csa.report(rows, everything=False) == []


def test_a_derived_value_is_marked_in_the_report() -> None:
    """A reader has to be able to tell a printed number from a computed one."""
    rows = [
        _row("first-book", density_kg_m3=7800.0, youngs_modulus_pa=200e9),
        _row(
            "second-book",
            density_kg_m3=7800.0,
            youngs_modulus_pa=200e9,
            derived={"youngs_modulus_pa": "from the printed speed and density"},
        ),
    ]
    printed = "\n".join(csa.report(rows, everything=True))
    assert "first 200, second* 200 GPa" in printed


@pytest.mark.parametrize(
    ("printed", "expected"),
    [
        ("Aluminium", "aluminium"),
        ("Glass, plate", "glass plate"),
        ("Perspex/Lucite", "perspex lucite"),
        ("Concrete (dense)", "concrete dense"),
    ],
)
def test_a_name_is_reduced_to_what_two_books_would_share(
    printed: str, expected: str
) -> None:
    """Case and punctuation, and nothing else: never the variant."""
    assert csa.normalised(printed) == expected


def test_the_spread_is_the_fraction_of_the_smaller() -> None:
    """A doubling reads as a hundred per cent, not fifty."""
    assert csa.spread([("a", 100.0, False), ("b", 200.0, False)]) == pytest.approx(1.0)


def test_the_tolerance_sits_between_the_real_spread_and_a_typed_digit() -> None:
    """The band the failing check lives in, stated as a test.

    The widest real density spread in the catalogue has to fit under the
    tolerance, and the tolerance has to fit well under what one wrong digit
    does, which is a factor of at least ten per cent and usually much more.
    """
    widest = max(
        csa.spread(readings)
        for rows in csa.groups(PUBLISHED_SOLIDS.values(), distinguished=False).values()
        for readings in [csa._readings(rows, "density_kg_m3")]
        if len({book for book, _, _ in readings}) >= 2
        and csa.normalised(rows[0].name) not in csa.ACCEPTED
    )
    assert widest < csa.DENSITY_TOLERANCE < 0.10
